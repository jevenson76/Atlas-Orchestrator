"""
Main project planner module that coordinates all components.

This module provides the high-level API for creating, validating,
and exporting comprehensive project plans.
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
from decimal import Decimal

from .models import ProjectTask, ExtendedProjectTask
from .validation import TaskValidator, DependencyAnalyzer
from .critical_path import CriticalPathCalculator, ResourceLeveling
from .csv_generator import CSVGenerator, CSVImporter


class ProjectPlanner:
    """
    Main project planning coordinator.

    Provides high-level API for:
    - Creating and validating project plans
    - Calculating critical paths
    - Detecting resource conflicts
    - Generating CSV exports
    - Integration with PM tools
    """

    def __init__(self, tasks: List[ProjectTask] = None):
        """
        Initialize project planner.

        Args:
            tasks: Optional initial list of tasks
        """
        self.tasks: List[ProjectTask] = tasks or []
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
        self.critical_path: List[str] = []
        self.metrics: Dict[str, Dict[str, any]] = {}

    def add_task(self, task: ProjectTask) -> None:
        """
        Add a task to the project plan.

        Args:
            task: ProjectTask object to add
        """
        self.tasks.append(task)

    def add_tasks(self, tasks: List[ProjectTask]) -> None:
        """
        Add multiple tasks to the project plan.

        Args:
            tasks: List of ProjectTask objects
        """
        self.tasks.extend(tasks)

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all tasks and dependencies.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        validator = TaskValidator(self.tasks)
        is_valid, errors, warnings = validator.validate_all()

        self.validation_errors = errors
        self.validation_warnings = warnings

        return is_valid, errors, warnings

    def calculate_critical_path(self) -> Tuple[List[str], Dict[str, Dict[str, any]]]:
        """
        Calculate project critical path.

        Returns:
            Tuple of (critical_path_task_ids, metrics_dict)

        Raises:
            ValueError: If validation fails or circular dependencies exist
        """
        # Validate first
        is_valid, errors, _ = self.validate()
        if not is_valid:
            raise ValueError(f"Cannot calculate critical path: validation errors: {errors}")

        # Calculate critical path
        calculator = CriticalPathCalculator(self.tasks)
        self.critical_path, self.metrics = calculator.calculate()

        return self.critical_path, self.metrics

    def analyze_resources(self) -> Dict[str, any]:
        """
        Analyze resource allocations and detect conflicts.

        Returns:
            Dictionary with resource analysis results
        """
        leveling = ResourceLeveling(self.tasks)

        over_allocations = leveling.detect_over_allocations()
        suggestions = leveling.suggest_leveling()

        return {
            'over_allocations': over_allocations,
            'over_allocation_count': len(over_allocations),
            'leveling_suggestions': suggestions,
            'resources_affected': len(set(oa['resource'] for oa in over_allocations))
        }

    def get_project_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive project statistics.

        Returns:
            Dictionary with project stats
        """
        if not self.tasks:
            return {}

        # Calculate critical path if not done
        if not self.critical_path:
            try:
                self.calculate_critical_path()
            except ValueError:
                pass  # Continue without critical path if validation fails

        # Basic statistics
        total_tasks = len(self.tasks)
        critical_tasks = sum(1 for t in self.tasks if t.is_critical)
        completed_tasks = sum(1 for t in self.tasks if t.status.value == "Completed")

        # Cost statistics
        total_estimated = sum(t.estimated_cost for t in self.tasks)
        total_actual = sum(t.actual_cost for t in self.tasks)

        # Duration statistics
        total_duration = sum(t.duration_days for t in self.tasks)
        if self.tasks:
            min_start = min(t.start_date for t in self.tasks)
            max_end = max(t.end_date for t in self.tasks)
            project_span = (max_end - min_start).days
        else:
            project_span = 0

        # Progress
        avg_completion = sum(t.percent_complete for t in self.tasks) / total_tasks if total_tasks > 0 else 0

        # Resource statistics
        resources = set(t.assigned_to for t in self.tasks if t.assigned_to)

        return {
            'total_tasks': total_tasks,
            'critical_tasks': critical_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': sum(1 for t in self.tasks if t.status.value == "In Progress"),
            'not_started_tasks': sum(1 for t in self.tasks if t.status.value == "Not Started"),
            'total_estimated_cost': float(total_estimated),
            'total_actual_cost': float(total_actual),
            'cost_variance': float(total_actual - total_estimated),
            'avg_completion_percent': float(avg_completion),
            'total_duration_days': float(total_duration),
            'project_span_days': project_span,
            'total_resources': len(resources),
            'critical_path_length': len(self.critical_path)
        }

    def export_to_csv(
        self,
        output_path: Path,
        use_pandas: bool = True,
        include_extended: bool = True
    ) -> str:
        """
        Export project plan to CSV file.

        Args:
            output_path: Output file path
            use_pandas: Use pandas for better performance
            include_extended: Include extended fields

        Returns:
            CSV content as string
        """
        generator = CSVGenerator(self.tasks, include_extended_fields=include_extended)

        if use_pandas:
            generator.generate_with_pandas(output_path)
            # Read back to return content
            with open(output_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return generator.generate(output_path)

    def export_to_ms_project(self, output_path: Path) -> None:
        """
        Export to Microsoft Project compatible format.

        Args:
            output_path: Output file path
        """
        generator = CSVGenerator(self.tasks)
        generator.export_to_ms_project(output_path)

    def export_summary_report(self, output_path: Path) -> None:
        """
        Export summary report with statistics.

        Args:
            output_path: Output file path
        """
        generator = CSVGenerator(self.tasks)
        generator.export_summary_report(output_path)

    def import_from_csv(
        self,
        file_path: Path,
        task_class: type = ProjectTask,
        replace: bool = True
    ) -> int:
        """
        Import tasks from CSV file.

        Args:
            file_path: Path to CSV file
            task_class: Task class to use for import
            replace: Replace existing tasks (True) or append (False)

        Returns:
            Number of tasks imported
        """
        importer = CSVImporter(use_pandas=True)
        imported_tasks = importer.import_from_csv(file_path, task_class)

        if replace:
            self.tasks = imported_tasks
        else:
            self.tasks.extend(imported_tasks)

        return len(imported_tasks)

    def analyze_dependencies(self) -> Dict[str, any]:
        """
        Analyze task dependencies.

        Returns:
            Dictionary with dependency analysis
        """
        analyzer = DependencyAnalyzer(self.tasks)

        # Find longest path
        longest_path = analyzer.find_longest_path()

        # Analyze each task's impact
        impact_analysis = {}
        for task in self.tasks:
            impacted_tasks = analyzer.get_impacted_tasks(task.task_id)
            depth = analyzer.get_dependency_depth(task.task_id)

            impact_analysis[task.task_id] = {
                'dependency_depth': depth,
                'impacted_task_count': len(impacted_tasks),
                'impacted_tasks': impacted_tasks[:10]  # Limit for readability
            }

        return {
            'longest_path': longest_path,
            'longest_path_length': len(longest_path),
            'impact_analysis': impact_analysis
        }

    def get_gantt_data(self) -> List[Dict[str, any]]:
        """
        Get data formatted for Gantt chart visualization.

        Returns:
            List of task dictionaries with Gantt chart data
        """
        gantt_data = []

        for task in sorted(self.tasks, key=lambda t: t.start_date):
            gantt_data.append({
                'task_id': task.task_id,
                'task_name': task.task_name,
                'start': task.start_date.isoformat(),
                'end': task.end_date.isoformat(),
                'duration': float(task.duration_days),
                'progress': task.percent_complete,
                'dependencies': task.predecessors,
                'is_critical': task.is_critical,
                'assigned_to': task.assigned_to or 'Unassigned',
                'status': task.status.value
            })

        return gantt_data

    def optimize_schedule(
        self,
        target_duration: Optional[Decimal] = None
    ) -> Dict[str, any]:
        """
        Analyze schedule optimization opportunities.

        Args:
            target_duration: Target project duration in days

        Returns:
            Dictionary with optimization analysis
        """
        # Calculate critical path first
        if not self.critical_path:
            self.calculate_critical_path()

        calculator = CriticalPathCalculator(self.tasks)

        if target_duration:
            compression_analysis = calculator.analyze_schedule_compression(target_duration)
        else:
            compression_analysis = None

        # Identify tasks with high slack
        high_slack_tasks = [
            {
                'task_id': t.task_id,
                'task_name': t.task_name,
                'slack_days': float(t.slack_days)
            }
            for t in self.tasks
            if t.slack_days > Decimal("5.0")
        ]

        # Identify parallel opportunities
        parallel_opportunities = self._identify_parallel_opportunities()

        return {
            'current_duration': float(calculator.get_project_duration()),
            'target_duration': float(target_duration) if target_duration else None,
            'compression_analysis': compression_analysis,
            'high_slack_tasks': high_slack_tasks,
            'parallel_opportunities': parallel_opportunities
        }

    def _identify_parallel_opportunities(self) -> List[Dict[str, any]]:
        """
        Identify tasks that could potentially be parallelized.

        Returns:
            List of parallelization opportunities
        """
        opportunities = []
        analyzer = DependencyAnalyzer(self.tasks)

        # Group tasks by dependency depth
        depth_groups = {}
        for task in self.tasks:
            depth = analyzer.get_dependency_depth(task.task_id)
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(task)

        # Find levels with multiple tasks
        for depth, tasks in depth_groups.items():
            if len(tasks) > 1:
                # Check if tasks have same resource
                resources = [t.assigned_to for t in tasks if t.assigned_to]
                if len(set(resources)) > 1:  # Different resources
                    opportunities.append({
                        'depth_level': depth,
                        'task_count': len(tasks),
                        'task_ids': [t.task_id for t in tasks],
                        'potential_savings': 'Tasks could run in parallel with different resources'
                    })

        return opportunities
