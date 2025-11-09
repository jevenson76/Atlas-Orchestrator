"""
Validation engine for project tasks.

This module provides multi-level validation including field validation,
cross-task validation, dependency cycle detection, and resource conflict detection.
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque
from datetime import datetime
from decimal import Decimal

import networkx as nx

from .models import ProjectTask, Status, DependencyType


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


class TaskValidator:
    """
    Comprehensive task validation engine.

    Validates individual tasks, task relationships, dependencies,
    and resource allocations.
    """

    def __init__(self, tasks: List[ProjectTask]):
        """
        Initialize validator with task list.

        Args:
            tasks: List of ProjectTask objects to validate
        """
        self.tasks = tasks
        self.task_dict: Dict[str, ProjectTask] = {t.task_id: t for t in tasks}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Run all validation checks
        self._validate_unique_ids()
        self._validate_dependencies()
        self._detect_dependency_cycles()
        self._validate_date_consistency()
        self._validate_resource_allocations()
        self._validate_critical_path_consistency()
        self._validate_cost_consistency()

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_unique_ids(self) -> None:
        """Validate that all task IDs are unique."""
        task_ids = [t.task_id for t in self.tasks]
        duplicates = [tid for tid in task_ids if task_ids.count(tid) > 1]

        if duplicates:
            unique_dupes = list(set(duplicates))
            self.errors.append(
                f"Duplicate task IDs found: {', '.join(unique_dupes)}"
            )

    def _validate_dependencies(self) -> None:
        """Validate that all dependencies reference existing tasks."""
        for task in self.tasks:
            # Check predecessors
            for pred_id in task.predecessors:
                if pred_id not in self.task_dict:
                    self.errors.append(
                        f"Task {task.task_id} references non-existent "
                        f"predecessor: {pred_id}"
                    )

            # Check successors
            for succ_id in task.successors:
                if succ_id not in self.task_dict:
                    self.errors.append(
                        f"Task {task.task_id} references non-existent "
                        f"successor: {succ_id}"
                    )

            # Validate bidirectional consistency
            for pred_id in task.predecessors:
                if pred_id in self.task_dict:
                    pred_task = self.task_dict[pred_id]
                    if task.task_id not in pred_task.successors:
                        self.warnings.append(
                            f"Task {task.task_id} lists {pred_id} as predecessor, "
                            f"but {pred_id} doesn't list {task.task_id} as successor"
                        )

    def _detect_dependency_cycles(self) -> None:
        """
        Detect circular dependencies using depth-first search.

        Uses NetworkX for robust cycle detection in large graphs.
        """
        # Build directed graph
        graph = nx.DiGraph()

        for task in self.tasks:
            graph.add_node(task.task_id)
            for pred_id in task.predecessors:
                if pred_id in self.task_dict:
                    graph.add_edge(pred_id, task.task_id)

        # Find all cycles
        try:
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                for cycle in cycles:
                    cycle_str = " -> ".join(cycle + [cycle[0]])
                    self.errors.append(
                        f"Circular dependency detected: {cycle_str}"
                    )
        except nx.NetworkXNoCycle:
            pass  # No cycles found

    def _validate_date_consistency(self) -> None:
        """
        Validate date consistency across dependent tasks.

        Checks that dependencies respect date ordering based on dependency type.
        """
        for task in self.tasks:
            for pred_id in task.predecessors:
                if pred_id not in self.task_dict:
                    continue

                pred_task = self.task_dict[pred_id]

                # Validate based on dependency type
                if task.dependency_type == DependencyType.FINISH_TO_START:
                    # Predecessor must finish before successor starts
                    if pred_task.end_date > task.start_date:
                        self.warnings.append(
                            f"FS dependency violation: Task {task.task_id} "
                            f"starts ({task.start_date}) before predecessor "
                            f"{pred_id} ends ({pred_task.end_date})"
                        )

                elif task.dependency_type == DependencyType.START_TO_START:
                    # Both should start around the same time
                    days_diff = abs((task.start_date - pred_task.start_date).days)
                    if days_diff > 1:  # Allow 1-day tolerance
                        self.warnings.append(
                            f"SS dependency warning: Task {task.task_id} and "
                            f"predecessor {pred_id} start dates differ by {days_diff} days"
                        )

                elif task.dependency_type == DependencyType.FINISH_TO_FINISH:
                    # Both should finish around the same time
                    days_diff = abs((task.end_date - pred_task.end_date).days)
                    if days_diff > 1:  # Allow 1-day tolerance
                        self.warnings.append(
                            f"FF dependency warning: Task {task.task_id} and "
                            f"predecessor {pred_id} end dates differ by {days_diff} days"
                        )

                elif task.dependency_type == DependencyType.START_TO_FINISH:
                    # Predecessor starts before successor finishes
                    if pred_task.start_date > task.end_date:
                        self.warnings.append(
                            f"SF dependency violation: Predecessor {pred_id} "
                            f"starts ({pred_task.start_date}) after task {task.task_id} "
                            f"finishes ({task.end_date})"
                        )

    def _validate_resource_allocations(self) -> None:
        """
        Validate resource allocations for over-allocation.

        Checks if any resource is allocated > 100% during overlapping periods.
        """
        # Group tasks by resource
        resource_tasks: Dict[str, List[ProjectTask]] = defaultdict(list)

        for task in self.tasks:
            if task.assigned_to and task.status != Status.CANCELLED:
                resource_tasks[task.assigned_to].append(task)

        # Check each resource for over-allocation
        for resource, tasks_list in resource_tasks.items():
            # Sort tasks by start date
            sorted_tasks = sorted(tasks_list, key=lambda t: t.start_date)

            # Check overlapping periods
            for i, task1 in enumerate(sorted_tasks):
                total_allocation = Decimal("0.00")

                for task2 in sorted_tasks[i:]:
                    # Check if tasks overlap
                    overlap = self._check_date_overlap(task1, task2)
                    if overlap:
                        # Get allocation percentage (default 100%)
                        alloc1 = getattr(task1, 'resource_allocation', Decimal("100.00"))
                        alloc2 = getattr(task2, 'resource_allocation', Decimal("100.00"))

                        if task1.task_id == task2.task_id:
                            total_allocation = alloc1
                        else:
                            total_allocation = alloc1 + alloc2

                        if total_allocation > Decimal("100.00"):
                            self.warnings.append(
                                f"Resource over-allocation: {resource} allocated "
                                f"{total_allocation}% during overlap of tasks "
                                f"{task1.task_id} and {task2.task_id}"
                            )

    def _check_date_overlap(self, task1: ProjectTask, task2: ProjectTask) -> bool:
        """
        Check if two tasks have overlapping date ranges.

        Args:
            task1: First task
            task2: Second task

        Returns:
            True if tasks overlap, False otherwise
        """
        return not (task1.end_date < task2.start_date or task2.end_date < task1.start_date)

    def _validate_critical_path_consistency(self) -> None:
        """Validate critical path flags and slack calculations."""
        for task in self.tasks:
            # Critical tasks should have zero or near-zero slack
            if task.is_critical and task.slack_days > Decimal("0.1"):
                self.warnings.append(
                    f"Task {task.task_id} marked as critical but has "
                    f"{task.slack_days} days of slack"
                )

            # Non-critical tasks should have positive slack
            if not task.is_critical and task.slack_days == Decimal("0.00"):
                self.warnings.append(
                    f"Task {task.task_id} not marked as critical but has zero slack"
                )

    def _validate_cost_consistency(self) -> None:
        """Validate cost-related fields."""
        for task in self.tasks:
            # Actual cost shouldn't exceed estimated cost significantly
            if task.actual_cost > task.estimated_cost * Decimal("1.2"):
                self.warnings.append(
                    f"Task {task.task_id} actual cost (${task.actual_cost}) "
                    f"exceeds estimated cost (${task.estimated_cost}) by >20%"
                )

            # Completed tasks should have costs recorded
            if task.status == Status.COMPLETED:
                if task.estimated_cost > 0 and task.actual_cost == 0:
                    self.warnings.append(
                        f"Completed task {task.task_id} has no actual cost recorded"
                    )


class DependencyAnalyzer:
    """Analyze and visualize task dependencies."""

    def __init__(self, tasks: List[ProjectTask]):
        """
        Initialize analyzer with task list.

        Args:
            tasks: List of ProjectTask objects
        """
        self.tasks = tasks
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        """Build NetworkX directed graph from tasks."""
        graph = nx.DiGraph()

        for task in self.tasks:
            graph.add_node(
                task.task_id,
                task=task,
                start=task.start_date,
                end=task.end_date,
                duration=task.duration_days
            )

            for pred_id in task.predecessors:
                graph.add_edge(pred_id, task.task_id)

        return graph

    def get_dependency_depth(self, task_id: str) -> int:
        """
        Calculate dependency depth (longest path from root).

        Args:
            task_id: Task identifier

        Returns:
            Depth in dependency tree
        """
        if task_id not in self.graph:
            return 0

        # Find all paths from root nodes
        root_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]

        max_depth = 0
        for root in root_nodes:
            try:
                if nx.has_path(self.graph, root, task_id):
                    path_length = nx.shortest_path_length(self.graph, root, task_id)
                    max_depth = max(max_depth, path_length)
            except nx.NetworkXNoPath:
                continue

        return max_depth

    def get_impacted_tasks(self, task_id: str) -> List[str]:
        """
        Get all tasks impacted by delays in given task.

        Args:
            task_id: Task identifier

        Returns:
            List of task IDs that would be impacted
        """
        if task_id not in self.graph:
            return []

        # Get all descendants (tasks that depend on this one)
        descendants = nx.descendants(self.graph, task_id)
        return list(descendants)

    def find_longest_path(self) -> List[str]:
        """
        Find longest dependency path in project.

        Returns:
            List of task IDs in longest path
        """
        try:
            # Use topological sort to find longest path
            longest_path = nx.dag_longest_path(self.graph)
            return longest_path
        except nx.NetworkXError:
            return []
