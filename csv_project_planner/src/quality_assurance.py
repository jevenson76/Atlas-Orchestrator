"""
Quality Assurance Module for CSV Project Planning with Role-Based Validation.

This module implements comprehensive quality checks, validation rules,
and scoring mechanisms to ensure project plans meet 90% quality target.
"""

from typing import List, Dict, Tuple, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .models import ProjectTask, ExtendedProjectTask, Status, Priority, TaskType
from .validation import TaskValidator, DependencyAnalyzer
from .critical_path import CriticalPathCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityMetrics:
    """Define quality metrics and thresholds."""

    # Quality score weights
    WEIGHTS = {
        'completeness': 0.20,      # Task field completeness
        'dependencies': 0.15,       # Dependency clarity and validity
        'resources': 0.15,          # Resource allocation efficiency
        'scheduling': 0.15,         # Schedule realism and optimization
        'risk_management': 0.10,    # Risk identification and mitigation
        'documentation': 0.10,      # Documentation coverage
        'testing': 0.10,            # Testing coverage
        'milestones': 0.05         # Milestone definition
    }

    # Minimum thresholds
    MIN_THRESHOLDS = {
        'overall_quality': 90,      # Target quality score
        'task_completeness': 85,    # Minimum task field completion
        'test_coverage': 80,         # Minimum test task coverage
        'doc_coverage': 70,          # Minimum documentation coverage
        'resource_utilization': 60,  # Minimum resource utilization
        'critical_path_clarity': 95  # Critical path must be clear
    }

    # Risk thresholds
    RISK_THRESHOLDS = {
        'max_overallocation': 120,  # Max resource allocation %
        'max_task_duration': 30,     # Max single task duration (days)
        'min_buffer_time': 0.1,      # Min buffer as % of phase duration
        'max_dependency_depth': 10   # Max dependency chain depth
    }


class QualityAssuranceEngine:
    """
    Comprehensive quality assurance engine for project plans.

    Performs multi-dimensional quality analysis and provides
    actionable recommendations for improvement.
    """

    def __init__(self, tasks: List[ProjectTask]):
        """
        Initialize QA engine with project tasks.

        Args:
            tasks: List of project tasks to analyze
        """
        self.tasks = tasks
        self.validator = TaskValidator(tasks)
        self.analyzer = DependencyAnalyzer(tasks)
        self.metrics = QualityMetrics()
        self.quality_report = {}
        self.recommendations = []
        self.critical_issues = []

    def run_comprehensive_assessment(self) -> Dict[str, Any]:
        """
        Run comprehensive quality assessment on project plan.

        Returns:
            Dictionary containing quality assessment results
        """
        logger.info("Starting comprehensive quality assessment")

        # Run individual assessments
        completeness_score = self._assess_completeness()
        dependency_score = self._assess_dependencies()
        resource_score = self._assess_resources()
        scheduling_score = self._assess_scheduling()
        risk_score = self._assess_risk_management()
        documentation_score = self._assess_documentation()
        testing_score = self._assess_testing()
        milestone_score = self._assess_milestones()

        # Calculate weighted overall score
        scores = {
            'completeness': completeness_score,
            'dependencies': dependency_score,
            'resources': resource_score,
            'scheduling': scheduling_score,
            'risk_management': risk_score,
            'documentation': documentation_score,
            'testing': testing_score,
            'milestones': milestone_score
        }

        overall_score = sum(
            scores[metric] * weight
            for metric, weight in self.metrics.WEIGHTS.items()
        )

        # Determine quality status
        quality_status = self._determine_quality_status(overall_score)

        # Generate recommendations
        self._generate_recommendations(scores)

        # Compile report
        self.quality_report = {
            'assessment_timestamp': datetime.utcnow().isoformat(),
            'overall_score': round(overall_score, 2),
            'target_score': self.metrics.MIN_THRESHOLDS['overall_quality'],
            'quality_status': quality_status,
            'target_met': overall_score >= self.metrics.MIN_THRESHOLDS['overall_quality'],
            'detailed_scores': scores,
            'critical_issues': self.critical_issues,
            'recommendations': self.recommendations,
            'metrics': {
                'total_tasks': len(self.tasks),
                'phases_identified': len(self._identify_phases()),
                'resources_assigned': len(self._get_unique_resources()),
                'quality_gates': sum(1 for t in self.tasks if hasattr(t, 'quality_gate') and t.quality_gate),
                'risks_identified': sum(1 for t in self.tasks if hasattr(t, 'risk_level'))
            },
            'validation_summary': self._get_validation_summary()
        }

        logger.info(f"Quality assessment complete. Score: {overall_score}%")
        return self.quality_report

    def _assess_completeness(self) -> float:
        """Assess task field completeness."""
        total_score = 0
        required_fields = [
            'task_name', 'description', 'start_date', 'end_date',
            'assigned_to', 'priority', 'status'
        ]

        optional_fields = [
            'wbs_code', 'owner', 'estimated_cost', 'notes', 'tags'
        ]

        for task in self.tasks:
            # Check required fields (80% weight)
            required_complete = sum(
                1 for field in required_fields
                if hasattr(task, field) and getattr(task, field)
            ) / len(required_fields)

            # Check optional fields (20% weight)
            optional_complete = sum(
                1 for field in optional_fields
                if hasattr(task, field) and getattr(task, field)
            ) / len(optional_fields)

            task_score = (required_complete * 0.8 + optional_complete * 0.2) * 100
            total_score += task_score

        completeness_score = total_score / len(self.tasks) if self.tasks else 0

        if completeness_score < self.metrics.MIN_THRESHOLDS['task_completeness']:
            self.critical_issues.append(
                f"Task completeness ({completeness_score:.1f}%) below threshold "
                f"({self.metrics.MIN_THRESHOLDS['task_completeness']}%)"
            )

        return completeness_score

    def _assess_dependencies(self) -> float:
        """Assess dependency structure and validity."""
        issues = []

        # Check for circular dependencies
        has_circular = self.analyzer.detect_circular_dependencies()
        if has_circular:
            issues.append("Circular dependencies detected")
            self.critical_issues.append("CRITICAL: Circular dependencies found in project plan")

        # Check dependency depth
        max_depth = 0
        for task in self.tasks:
            depth = self.analyzer.get_dependency_depth(task.task_id)
            max_depth = max(max_depth, depth)

        if max_depth > self.metrics.RISK_THRESHOLDS['max_dependency_depth']:
            issues.append(f"Dependency depth ({max_depth}) exceeds threshold")

        # Check for orphaned tasks (no dependencies and no dependents)
        orphaned_count = 0
        for task in self.tasks:
            if not task.predecessors and not task.successors:
                # Exclude phase and milestone tasks
                if task.task_type not in [TaskType.PHASE, TaskType.MILESTONE]:
                    orphaned_count += 1

        if orphaned_count > len(self.tasks) * 0.1:  # More than 10% orphaned
            issues.append(f"{orphaned_count} orphaned tasks found")

        # Calculate score
        base_score = 100
        penalty = len(issues) * 20
        dependency_score = max(0, base_score - penalty)

        return dependency_score

    def _assess_resources(self) -> float:
        """Assess resource allocation and utilization."""
        resources = defaultdict(list)

        # Group tasks by resource
        for task in self.tasks:
            if hasattr(task, 'assigned_to') and task.assigned_to:
                resources[task.assigned_to].append(task)

        if not resources:
            return 50  # No resources assigned

        issues = []
        total_utilization = 0

        for resource, resource_tasks in resources.items():
            # Check for overlapping tasks
            overlaps = self._find_overlapping_tasks(resource_tasks)
            if overlaps:
                issues.append(f"{resource} has {len(overlaps)} overlapping tasks")

            # Calculate utilization
            if resource_tasks:
                working_days = self._calculate_working_days(resource_tasks)
                total_days = (
                    max(t.end_date for t in resource_tasks) -
                    min(t.start_date for t in resource_tasks)
                ).days + 1

                utilization = (working_days / total_days * 100) if total_days > 0 else 0
                total_utilization += utilization

        avg_utilization = total_utilization / len(resources) if resources else 0

        # Score based on utilization and issues
        base_score = min(100, avg_utilization * 1.2)  # Bonus for good utilization
        penalty = len(issues) * 10
        resource_score = max(0, base_score - penalty)

        if avg_utilization < self.metrics.MIN_THRESHOLDS['resource_utilization']:
            self.recommendations.append(
                f"Resource utilization ({avg_utilization:.1f}%) is below optimal. "
                "Consider consolidating tasks or reducing team size."
            )

        return resource_score

    def _assess_scheduling(self) -> float:
        """Assess schedule realism and optimization."""
        issues = []

        # Check for tasks with excessive duration
        long_tasks = [
            t for t in self.tasks
            if t.duration_days > self.metrics.RISK_THRESHOLDS['max_task_duration']
        ]
        if long_tasks:
            issues.append(f"{len(long_tasks)} tasks exceed maximum duration threshold")

        # Check for adequate buffers between phases
        phases = self._identify_phases()
        for i in range(len(phases) - 1):
            current_phase = phases[i]
            next_phase = phases[i + 1]

            buffer_days = (next_phase['start'] - current_phase['end']).days
            min_buffer = current_phase['duration'] * self.metrics.RISK_THRESHOLDS['min_buffer_time']

            if buffer_days < min_buffer:
                issues.append(f"Insufficient buffer between {current_phase['name']} and {next_phase['name']}")

        # Check for weekend/holiday work
        weekend_tasks = self._check_weekend_work()
        if weekend_tasks:
            issues.append(f"{len(weekend_tasks)} tasks scheduled on weekends")

        # Calculate score
        base_score = 100
        penalty = len(issues) * 15
        scheduling_score = max(0, base_score - penalty)

        return scheduling_score

    def _assess_risk_management(self) -> float:
        """Assess risk identification and mitigation."""
        risk_tasks = [
            t for t in self.tasks
            if hasattr(t, 'risk_level')
        ]

        critical_tasks = [
            t for t in self.tasks
            if t.priority == Priority.CRITICAL
        ]

        # Check risk coverage for critical tasks
        critical_with_risk = [
            t for t in critical_tasks
            if hasattr(t, 'risk_level')
        ]

        risk_coverage = (
            len(critical_with_risk) / len(critical_tasks) * 100
            if critical_tasks else 0
        )

        # Check for risk mitigation tasks
        mitigation_keywords = ['mitigation', 'contingency', 'backup', 'fallback']
        mitigation_tasks = [
            t for t in self.tasks
            if any(keyword in t.task_name.lower() for keyword in mitigation_keywords)
        ]

        # Calculate score
        base_score = risk_coverage
        if len(mitigation_tasks) > 0:
            base_score += 20  # Bonus for having mitigation tasks

        risk_score = min(100, base_score)

        if risk_coverage < 50:
            self.recommendations.append(
                "Increase risk assessment coverage for critical tasks"
            )

        return risk_score

    def _assess_documentation(self) -> float:
        """Assess documentation coverage."""
        doc_tasks = [
            t for t in self.tasks
            if any(keyword in t.task_name.lower() for keyword in
                   ['document', 'documentation', 'guide', 'manual', 'readme'])
        ]

        phases = self._identify_phases()
        doc_coverage = (len(doc_tasks) / len(phases) * 100) if phases else 0

        # Check for specific documentation types
        doc_types = {
            'user': ['user', 'end-user', 'customer'],
            'technical': ['technical', 'api', 'developer'],
            'operations': ['operations', 'ops', 'maintenance'],
            'training': ['training', 'tutorial', 'learning']
        }

        covered_types = set()
        for doc_type, keywords in doc_types.items():
            for task in doc_tasks:
                if any(kw in task.task_name.lower() for kw in keywords):
                    covered_types.add(doc_type)
                    break

        type_coverage = len(covered_types) / len(doc_types) * 100

        # Calculate score
        documentation_score = (doc_coverage * 0.5 + type_coverage * 0.5)

        if documentation_score < self.metrics.MIN_THRESHOLDS['doc_coverage']:
            self.recommendations.append(
                f"Documentation coverage ({documentation_score:.1f}%) is below threshold. "
                "Add more documentation tasks."
            )

        return documentation_score

    def _assess_testing(self) -> float:
        """Assess testing coverage and strategy."""
        test_tasks = [
            t for t in self.tasks
            if any(keyword in t.task_name.lower() for keyword in
                   ['test', 'testing', 'qa', 'quality'])
        ]

        # Check for different test types
        test_types = {
            'unit': ['unit test', 'unit testing'],
            'integration': ['integration test', 'integration testing'],
            'system': ['system test', 'end-to-end', 'e2e'],
            'performance': ['performance', 'load test', 'stress test'],
            'security': ['security test', 'penetration', 'vulnerability'],
            'uat': ['uat', 'user acceptance', 'acceptance testing']
        }

        covered_test_types = set()
        for test_type, keywords in test_types.items():
            for task in test_tasks:
                if any(kw in task.task_name.lower() for kw in keywords):
                    covered_test_types.add(test_type)
                    break

        # Calculate coverage
        test_coverage = len(covered_test_types) / len(test_types) * 100

        # Check for test tasks in relation to development tasks
        dev_tasks = [
            t for t in self.tasks
            if any(keyword in t.task_name.lower() for keyword in
                   ['develop', 'implement', 'code', 'build'])
        ]

        test_ratio = (len(test_tasks) / len(dev_tasks) * 100) if dev_tasks else 0

        # Calculate score
        testing_score = (test_coverage * 0.6 + min(test_ratio, 100) * 0.4)

        if testing_score < self.metrics.MIN_THRESHOLDS['test_coverage']:
            self.critical_issues.append(
                f"Testing coverage ({testing_score:.1f}%) below minimum threshold"
            )

        return testing_score

    def _assess_milestones(self) -> float:
        """Assess milestone definition and distribution."""
        milestones = [
            t for t in self.tasks
            if t.task_type == TaskType.MILESTONE
        ]

        phases = self._identify_phases()

        # Check milestone coverage (at least one per phase)
        milestone_coverage = (
            min(len(milestones) / len(phases), 1) * 100
            if phases else 0
        )

        # Check milestone distribution
        if milestones and len(milestones) > 1:
            milestone_gaps = []
            sorted_milestones = sorted(milestones, key=lambda t: t.start_date)

            for i in range(len(sorted_milestones) - 1):
                gap = (sorted_milestones[i + 1].start_date -
                       sorted_milestones[i].end_date).days
                milestone_gaps.append(gap)

            avg_gap = sum(milestone_gaps) / len(milestone_gaps)
            gap_variance = sum((g - avg_gap) ** 2 for g in milestone_gaps) / len(milestone_gaps)

            # Good distribution has low variance
            distribution_score = max(0, 100 - gap_variance)
        else:
            distribution_score = 50

        # Calculate score
        milestone_score = (milestone_coverage * 0.6 + distribution_score * 0.4)

        if len(milestones) < len(phases):
            self.recommendations.append(
                "Add milestones to mark completion of each project phase"
            )

        return milestone_score

    def _identify_phases(self) -> List[Dict[str, Any]]:
        """Identify project phases from tasks."""
        phases = []

        phase_tasks = [t for t in self.tasks if t.task_type == TaskType.PHASE]

        for phase in phase_tasks:
            phases.append({
                'name': phase.task_name,
                'start': phase.start_date,
                'end': phase.end_date,
                'duration': phase.duration_days
            })

        # If no explicit phases, try to identify by task grouping
        if not phases:
            # Group by WBS first level
            wbs_groups = defaultdict(list)
            for task in self.tasks:
                if hasattr(task, 'wbs_code') and task.wbs_code:
                    first_level = task.wbs_code.split('.')[0]
                    wbs_groups[first_level].append(task)

            for wbs, group_tasks in sorted(wbs_groups.items()):
                if group_tasks:
                    phases.append({
                        'name': f"Phase {wbs}",
                        'start': min(t.start_date for t in group_tasks),
                        'end': max(t.end_date for t in group_tasks),
                        'duration': Decimal(
                            (max(t.end_date for t in group_tasks) -
                             min(t.start_date for t in group_tasks)).days
                        )
                    })

        return sorted(phases, key=lambda p: p['start'])

    def _get_unique_resources(self) -> set:
        """Get unique resources from tasks."""
        resources = set()
        for task in self.tasks:
            if hasattr(task, 'assigned_to') and task.assigned_to:
                resources.add(task.assigned_to)
        return resources

    def _find_overlapping_tasks(self, tasks: List[ProjectTask]) -> List[Tuple]:
        """Find overlapping tasks for a resource."""
        overlaps = []
        sorted_tasks = sorted(tasks, key=lambda t: t.start_date)

        for i in range(len(sorted_tasks) - 1):
            for j in range(i + 1, len(sorted_tasks)):
                task1 = sorted_tasks[i]
                task2 = sorted_tasks[j]

                # Check for overlap
                if (task1.start_date <= task2.end_date and
                    task1.end_date >= task2.start_date):
                    overlaps.append((task1.task_id, task2.task_id))

        return overlaps

    def _calculate_working_days(self, tasks: List[ProjectTask]) -> int:
        """Calculate total working days for tasks."""
        working_days = set()

        for task in tasks:
            current = task.start_date
            while current <= task.end_date:
                working_days.add(current.date())
                current += timedelta(days=1)

        return len(working_days)

    def _check_weekend_work(self) -> List[ProjectTask]:
        """Check for tasks scheduled on weekends."""
        weekend_tasks = []

        for task in self.tasks:
            current = task.start_date
            while current <= task.end_date:
                if current.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
                    weekend_tasks.append(task)
                    break
                current += timedelta(days=1)

        return weekend_tasks

    def _determine_quality_status(self, score: float) -> str:
        """Determine quality status based on score."""
        if score >= 95:
            return "EXCELLENT"
        elif score >= 90:
            return "GOOD"
        elif score >= 80:
            return "ACCEPTABLE"
        elif score >= 70:
            return "NEEDS_IMPROVEMENT"
        else:
            return "POOR"

    def _generate_recommendations(self, scores: Dict[str, float]) -> None:
        """Generate recommendations based on scores."""
        # Find lowest scoring areas
        sorted_scores = sorted(scores.items(), key=lambda x: x[1])

        for metric, score in sorted_scores[:3]:  # Focus on 3 worst areas
            if score < 80:
                if metric == 'completeness':
                    self.recommendations.append(
                        "Improve task completeness by filling in missing descriptions, "
                        "assignments, and WBS codes"
                    )
                elif metric == 'dependencies':
                    self.recommendations.append(
                        "Review and clarify task dependencies. Ensure no circular "
                        "dependencies and reduce dependency depth"
                    )
                elif metric == 'resources':
                    self.recommendations.append(
                        "Optimize resource allocation. Balance workload and "
                        "resolve resource conflicts"
                    )
                elif metric == 'scheduling':
                    self.recommendations.append(
                        "Review schedule for realism. Add buffers between phases "
                        "and avoid excessively long tasks"
                    )

    def _get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary from task validator."""
        is_valid, errors, warnings = self.validator.validate_all()

        return {
            'is_valid': is_valid,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'errors': errors[:5],  # First 5 errors
            'warnings': warnings[:5]  # First 5 warnings
        }

    def generate_quality_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate detailed quality report.

        Args:
            output_path: Optional path to save report

        Returns:
            Formatted quality report as string
        """
        if not self.quality_report:
            self.run_comprehensive_assessment()

        report_lines = [
            "=" * 80,
            "PROJECT QUALITY ASSURANCE REPORT",
            "=" * 80,
            f"Generated: {self.quality_report['assessment_timestamp']}",
            "",
            f"Overall Quality Score: {self.quality_report['overall_score']}%",
            f"Target Score: {self.quality_report['target_score']}%",
            f"Status: {self.quality_report['quality_status']}",
            f"Target Met: {'YES' if self.quality_report['target_met'] else 'NO'}",
            "",
            "DETAILED SCORES",
            "-" * 40
        ]

        for metric, score in self.quality_report['detailed_scores'].items():
            status = "✓" if score >= 80 else "✗"
            report_lines.append(f"{status} {metric.title()}: {score:.1f}%")

        if self.critical_issues:
            report_lines.extend([
                "",
                "CRITICAL ISSUES",
                "-" * 40
            ])
            for issue in self.critical_issues:
                report_lines.append(f"• {issue}")

        if self.recommendations:
            report_lines.extend([
                "",
                "RECOMMENDATIONS",
                "-" * 40
            ])
            for rec in self.recommendations:
                report_lines.append(f"• {rec}")

        report_lines.extend([
            "",
            "PROJECT METRICS",
            "-" * 40
        ])
        for metric, value in self.quality_report['metrics'].items():
            report_lines.append(f"{metric.replace('_', ' ').title()}: {value}")

        report_lines.extend([
            "",
            "=" * 80
        ])

        report = "\n".join(report_lines)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)

        return report


# Example usage
if __name__ == "__main__":
    # This would typically be called with actual project tasks
    # qa_engine = QualityAssuranceEngine(tasks)
    # report = qa_engine.run_comprehensive_assessment()
    # print(qa_engine.generate_quality_report())
    pass