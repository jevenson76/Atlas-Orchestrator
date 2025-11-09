"""
Critical Path Method (CPM) calculator.

This module implements the Critical Path Method algorithm using
Forward Pass and Backward Pass to calculate project critical path,
earliest/latest start/finish times, and task slack.
"""

from typing import List, Dict, Set, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

import networkx as nx

from .models import ProjectTask, DependencyType


class CriticalPathCalculator:
    """
    Calculate project critical path using CPM algorithm.

    Uses Forward Pass and Backward Pass to determine:
    - Early Start (ES) and Early Finish (EF) for each task
    - Late Start (LS) and Late Finish (LF) for each task
    - Total Slack/Float for each task
    - Critical tasks (zero slack)
    """

    def __init__(self, tasks: List[ProjectTask]):
        """
        Initialize calculator with task list.

        Args:
            tasks: List of ProjectTask objects
        """
        self.tasks = tasks
        self.task_dict: Dict[str, ProjectTask] = {t.task_id: t for t in tasks}
        self.graph = self._build_graph()

        # Results storage
        self.early_start: Dict[str, datetime] = {}
        self.early_finish: Dict[str, datetime] = {}
        self.late_start: Dict[str, datetime] = {}
        self.late_finish: Dict[str, datetime] = {}
        self.slack: Dict[str, Decimal] = {}
        self.critical_tasks: Set[str] = set()

    def _build_graph(self) -> nx.DiGraph:
        """Build directed graph from task dependencies."""
        graph = nx.DiGraph()

        for task in self.tasks:
            graph.add_node(
                task.task_id,
                duration=float(task.duration_days),
                start=task.start_date,
                end=task.end_date
            )

            for pred_id in task.predecessors:
                if pred_id in self.task_dict:
                    graph.add_edge(pred_id, task.task_id)

        return graph

    def calculate(self) -> Tuple[List[str], Dict[str, Dict[str, any]]]:
        """
        Calculate critical path and return results.

        Returns:
            Tuple of (critical_path_task_ids, metrics_dict)
        """
        # Check for cycles first
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Cannot calculate critical path: circular dependencies detected")

        # Perform forward and backward passes
        self._forward_pass()
        self._backward_pass()
        self._calculate_slack()
        self._identify_critical_path()

        # Update task objects with calculated values
        self._update_tasks()

        # Build metrics dictionary
        metrics = self.get_metrics()

        return list(self.critical_tasks), metrics

    def _forward_pass(self) -> None:
        """
        Forward Pass: Calculate Early Start and Early Finish.

        ES = max(EF of all predecessors)
        EF = ES + Duration
        """
        # Topological sort ensures we process tasks in dependency order
        topo_order = list(nx.topological_sort(self.graph))

        for task_id in topo_order:
            task = self.task_dict[task_id]
            predecessors = list(self.graph.predecessors(task_id))

            if not predecessors:
                # Start task - use actual start date
                self.early_start[task_id] = task.start_date
            else:
                # ES = max(EF of all predecessors)
                max_pred_ef = max(
                    self.early_finish[pred_id] for pred_id in predecessors
                )
                self.early_start[task_id] = max_pred_ef

            # EF = ES + Duration
            duration_td = timedelta(days=float(task.duration_days))
            self.early_finish[task_id] = self.early_start[task_id] + duration_td

    def _backward_pass(self) -> None:
        """
        Backward Pass: Calculate Late Start and Late Finish.

        LF = min(LS of all successors)
        LS = LF - Duration
        """
        # Reverse topological sort for backward pass
        topo_order = list(reversed(list(nx.topological_sort(self.graph))))

        for task_id in topo_order:
            task = self.task_dict[task_id]
            successors = list(self.graph.successors(task_id))

            if not successors:
                # End task - LF = EF (project must finish at earliest possible time)
                self.late_finish[task_id] = self.early_finish[task_id]
            else:
                # LF = min(LS of all successors)
                min_succ_ls = min(
                    self.late_start[succ_id] for succ_id in successors
                )
                self.late_finish[task_id] = min_succ_ls

            # LS = LF - Duration
            duration_td = timedelta(days=float(task.duration_days))
            self.late_start[task_id] = self.late_finish[task_id] - duration_td

    def _calculate_slack(self) -> None:
        """
        Calculate total slack/float for each task.

        Total Slack = LS - ES = LF - EF
        """
        for task_id in self.task_dict.keys():
            # Calculate slack in days
            slack_td = self.late_start[task_id] - self.early_start[task_id]
            slack_days = Decimal(str(slack_td.days + slack_td.seconds / 86400))

            # Ensure non-negative (rounding errors)
            self.slack[task_id] = max(Decimal("0.00"), slack_days)

    def _identify_critical_path(self) -> None:
        """
        Identify critical path tasks (zero or near-zero slack).

        Critical tasks form the longest path through the project.
        """
        # Tasks with zero slack are on critical path
        tolerance = Decimal("0.01")  # Small tolerance for floating point errors

        for task_id, slack in self.slack.items():
            if slack <= tolerance:
                self.critical_tasks.add(task_id)

    def _update_tasks(self) -> None:
        """Update task objects with calculated critical path data."""
        for task_id, task in self.task_dict.items():
            task.is_critical = task_id in self.critical_tasks
            task.slack_days = self.slack[task_id]

    def get_metrics(self) -> Dict[str, Dict[str, any]]:
        """
        Get comprehensive metrics for all tasks.

        Returns:
            Dictionary mapping task_id to metrics dict
        """
        metrics = {}

        for task_id in self.task_dict.keys():
            metrics[task_id] = {
                'early_start': self.early_start[task_id].isoformat(),
                'early_finish': self.early_finish[task_id].isoformat(),
                'late_start': self.late_start[task_id].isoformat(),
                'late_finish': self.late_finish[task_id].isoformat(),
                'slack_days': float(self.slack[task_id]),
                'is_critical': task_id in self.critical_tasks
            }

        return metrics

    def get_project_duration(self) -> Decimal:
        """
        Calculate total project duration.

        Returns:
            Project duration in days
        """
        if not self.early_start or not self.early_finish:
            return Decimal("0.00")

        # Project duration = max(EF) - min(ES)
        min_start = min(self.early_start.values())
        max_finish = max(self.early_finish.values())

        duration_td = max_finish - min_start
        return Decimal(str(duration_td.days + duration_td.seconds / 86400))

    def get_critical_path_chain(self) -> List[str]:
        """
        Get ordered list of tasks on critical path.

        Returns:
            List of task IDs in dependency order along critical path
        """
        # Build subgraph with only critical tasks
        critical_graph = self.graph.subgraph(self.critical_tasks)

        try:
            # Get longest path through critical tasks
            return nx.dag_longest_path(critical_graph)
        except nx.NetworkXError:
            # If multiple paths, return topological sort of critical tasks
            return list(nx.topological_sort(critical_graph))

    def analyze_schedule_compression(
        self,
        target_duration: Decimal
    ) -> Dict[str, any]:
        """
        Analyze options for compressing schedule to meet target duration.

        Args:
            target_duration: Target project duration in days

        Returns:
            Dictionary with compression analysis
        """
        current_duration = self.get_project_duration()

        if current_duration <= target_duration:
            return {
                'compression_needed': False,
                'current_duration': float(current_duration),
                'target_duration': float(target_duration),
                'message': 'Project already meets target duration'
            }

        days_to_compress = current_duration - target_duration

        # Identify critical tasks that could be crashed
        critical_path = self.get_critical_path_chain()
        crash_candidates = []

        for task_id in critical_path:
            task = self.task_dict[task_id]

            # Tasks with duration > 1 day can potentially be crashed
            if task.duration_days > Decimal("1.0"):
                crash_candidates.append({
                    'task_id': task_id,
                    'task_name': task.task_name,
                    'current_duration': float(task.duration_days),
                    'potential_savings': min(
                        float(task.duration_days) * 0.3,  # Max 30% compression
                        float(days_to_compress)
                    )
                })

        return {
            'compression_needed': True,
            'current_duration': float(current_duration),
            'target_duration': float(target_duration),
            'days_to_compress': float(days_to_compress),
            'critical_path_tasks': critical_path,
            'crash_candidates': crash_candidates,
            'message': f'Need to compress schedule by {days_to_compress} days'
        }


class ResourceLeveling:
    """Analyze and optimize resource allocation across tasks."""

    def __init__(self, tasks: List[ProjectTask]):
        """
        Initialize resource leveling analyzer.

        Args:
            tasks: List of ProjectTask objects
        """
        self.tasks = tasks

    def detect_over_allocations(self) -> List[Dict[str, any]]:
        """
        Detect resource over-allocations.

        Returns:
            List of over-allocation instances
        """
        over_allocations = []

        # Group tasks by resource
        resource_tasks = defaultdict(list)
        for task in self.tasks:
            if task.assigned_to:
                resource_tasks[task.assigned_to].append(task)

        # Check each resource
        for resource, tasks in resource_tasks.items():
            # Sort by start date
            sorted_tasks = sorted(tasks, key=lambda t: t.start_date)

            # Check overlapping tasks
            for i, task1 in enumerate(sorted_tasks):
                for task2 in sorted_tasks[i + 1:]:
                    # Check date overlap
                    if task1.end_date >= task2.start_date:
                        # Get allocation percentages
                        alloc1 = getattr(task1, 'resource_allocation', Decimal("100.00"))
                        alloc2 = getattr(task2, 'resource_allocation', Decimal("100.00"))
                        total_alloc = alloc1 + alloc2

                        if total_alloc > Decimal("100.00"):
                            over_allocations.append({
                                'resource': resource,
                                'task1_id': task1.task_id,
                                'task2_id': task2.task_id,
                                'overlap_start': max(task1.start_date, task2.start_date).isoformat(),
                                'overlap_end': min(task1.end_date, task2.end_date).isoformat(),
                                'total_allocation': float(total_alloc),
                                'over_allocation': float(total_alloc - Decimal("100.00"))
                            })

        return over_allocations

    def suggest_leveling(self) -> List[Dict[str, any]]:
        """
        Suggest resource leveling adjustments.

        Returns:
            List of suggested adjustments
        """
        suggestions = []
        over_allocations = self.detect_over_allocations()

        for oa in over_allocations:
            # Find task with slack that could be delayed
            task1_id = oa['task1_id']
            task2_id = oa['task2_id']

            task1 = next(t for t in self.tasks if t.task_id == task1_id)
            task2 = next(t for t in self.tasks if t.task_id == task2_id)

            # Suggest delaying task with more slack
            if task1.slack_days > task2.slack_days:
                suggestions.append({
                    'type': 'delay_task',
                    'task_id': task1_id,
                    'delay_days': float((task2.end_date - task1.start_date).days + 1),
                    'reason': f'Resolve over-allocation with {task2_id}',
                    'impact': 'No critical path impact' if task1.slack_days > 0 else 'May delay project'
                })
            else:
                suggestions.append({
                    'type': 'delay_task',
                    'task_id': task2_id,
                    'delay_days': float((task1.end_date - task2.start_date).days + 1),
                    'reason': f'Resolve over-allocation with {task1_id}',
                    'impact': 'No critical path impact' if task2.slack_days > 0 else 'May delay project'
                })

        return suggestions
