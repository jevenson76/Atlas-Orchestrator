"""
Workflow Metrics Tracking - Cost & Performance Analytics

Tracks detailed metrics for specialized roles workflows:
- Cost breakdown by role and phase
- Performance analytics (execution time, token usage)
- Quality scores over time
- Self-correction statistics
- Export capabilities (JSON, CSV)

Usage:
    tracker = WorkflowMetricsTracker()

    # Record workflow
    tracker.record_workflow(workflow_result)

    # Get analytics
    analytics = tracker.get_analytics()

    # Export to file
    tracker.export_to_json("metrics.json")
    tracker.export_to_csv("metrics.csv")
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum


@dataclass
class WorkflowMetrics:
    """Metrics for a single workflow execution."""

    # Identification
    workflow_id: str
    task: str
    timestamp: str

    # Overall metrics
    success: bool
    overall_quality_score: Optional[int]
    total_execution_time_ms: float
    total_cost_usd: float
    total_tokens: int
    total_iterations: int

    # Phase metrics
    architect_cost_usd: float = 0.0
    architect_time_ms: float = 0.0
    architect_tokens: int = 0
    architect_score: Optional[int] = None

    developer_cost_usd: float = 0.0
    developer_time_ms: float = 0.0
    developer_tokens: int = 0
    developer_score: Optional[int] = None

    tester_cost_usd: float = 0.0
    tester_time_ms: float = 0.0
    tester_tokens: int = 0
    tester_score: Optional[int] = None

    reviewer_cost_usd: float = 0.0
    reviewer_time_ms: float = 0.0
    reviewer_tokens: int = 0
    reviewer_score: Optional[int] = None

    # Self-correction metrics
    phases_self_corrected: List[str] = field(default_factory=list)
    self_correction_cost_usd: float = 0.0

    # Context
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_workflow_result(cls, workflow_result) -> "WorkflowMetrics":
        """Create metrics from WorkflowResult."""
        workflow_id = f"wf_{int(datetime.now().timestamp() * 1000)}"

        metrics = cls(
            workflow_id=workflow_id,
            task=workflow_result.task,
            timestamp=workflow_result.started_at.isoformat(),
            success=workflow_result.success,
            overall_quality_score=workflow_result.overall_quality_score,
            total_execution_time_ms=workflow_result.total_execution_time_ms,
            total_cost_usd=workflow_result.total_cost_usd,
            total_tokens=workflow_result.total_tokens,
            total_iterations=workflow_result.total_iterations,
            phases_self_corrected=[p.value for p in workflow_result.phases_self_corrected],
            context=workflow_result.context
        )

        # Extract phase metrics
        if workflow_result.architect_result:
            metrics.architect_cost_usd = workflow_result.architect_result.cost_usd
            metrics.architect_time_ms = workflow_result.architect_result.execution_time_ms
            metrics.architect_tokens = workflow_result.architect_result.tokens_used
            metrics.architect_score = workflow_result.architect_result.quality_score

        if workflow_result.developer_result:
            metrics.developer_cost_usd = workflow_result.developer_result.cost_usd
            metrics.developer_time_ms = workflow_result.developer_result.execution_time_ms
            metrics.developer_tokens = workflow_result.developer_result.tokens_used
            metrics.developer_score = workflow_result.developer_result.quality_score

        if workflow_result.tester_result:
            metrics.tester_cost_usd = workflow_result.tester_result.cost_usd
            metrics.tester_time_ms = workflow_result.tester_result.execution_time_ms
            metrics.tester_tokens = workflow_result.tester_result.tokens_used
            metrics.tester_score = workflow_result.tester_result.quality_score

        if workflow_result.reviewer_result:
            metrics.reviewer_cost_usd = workflow_result.reviewer_result.cost_usd
            metrics.reviewer_time_ms = workflow_result.reviewer_result.execution_time_ms
            metrics.reviewer_tokens = workflow_result.reviewer_result.tokens_used
            metrics.reviewer_score = workflow_result.reviewer_result.quality_score

        # Calculate self-correction cost (estimate based on iterations)
        if workflow_result.total_iterations > len(workflow_result.completed_phases):
            extra_iterations = workflow_result.total_iterations - len(workflow_result.completed_phases)
            # Estimate self-correction cost as 20% of total cost per extra iteration
            metrics.self_correction_cost_usd = (metrics.total_cost_usd * 0.2) * extra_iterations

        return metrics


class WorkflowMetricsTracker:
    """
    Tracks and analyzes workflow metrics over time.

    Stores metrics for multiple workflow executions and provides
    analytics, trend analysis, and export capabilities.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize metrics tracker.

        Args:
            storage_path: Path to store metrics (default: ~/.claude/metrics/)
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / '.claude' / 'metrics'

        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.storage_path / 'workflow_metrics.json'
        self.workflows: List[WorkflowMetrics] = []

        # Load existing metrics if available
        self._load_metrics()

    def _load_metrics(self):
        """Load metrics from storage."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.workflows = [
                        WorkflowMetrics(**w) for w in data.get('workflows', [])
                    ]
                print(f"✅ Loaded {len(self.workflows)} existing workflow metrics")
            except Exception as e:
                print(f"⚠️  Could not load metrics: {e}")
                self.workflows = []
        else:
            self.workflows = []

    def _save_metrics(self):
        """Save metrics to storage."""
        try:
            data = {
                'workflows': [w.to_dict() for w in self.workflows],
                'last_updated': datetime.now().isoformat(),
                'total_workflows': len(self.workflows)
            }

            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"✅ Saved metrics to {self.metrics_file}")
        except Exception as e:
            print(f"❌ Failed to save metrics: {e}")

    def record_workflow(self, workflow_result) -> WorkflowMetrics:
        """
        Record metrics from a workflow execution.

        Args:
            workflow_result: WorkflowResult from SpecializedRolesOrchestrator

        Returns:
            WorkflowMetrics object
        """
        metrics = WorkflowMetrics.from_workflow_result(workflow_result)
        self.workflows.append(metrics)
        self._save_metrics()

        print(f"\n📊 Recorded workflow metrics:")
        print(f"   Workflow ID: {metrics.workflow_id}")
        print(f"   Total Cost: ${metrics.total_cost_usd:.6f}")
        print(f"   Total Time: {metrics.total_execution_time_ms/1000:.2f}s")
        print(f"   Quality Score: {metrics.overall_quality_score}/100")

        return metrics

    def get_analytics(self, last_n: Optional[int] = None) -> Dict[str, Any]:
        """
        Get analytics across all workflows.

        Args:
            last_n: Analyze only last N workflows (None = all)

        Returns:
            Dictionary with comprehensive analytics
        """
        workflows = self.workflows[-last_n:] if last_n else self.workflows

        if not workflows:
            return {'error': 'No workflows recorded'}

        total_workflows = len(workflows)
        successful_workflows = sum(1 for w in workflows if w.success)

        analytics = {
            'summary': {
                'total_workflows': total_workflows,
                'successful_workflows': successful_workflows,
                'success_rate': successful_workflows / total_workflows if total_workflows > 0 else 0,
                'date_range': {
                    'first': workflows[0].timestamp,
                    'last': workflows[-1].timestamp
                }
            },
            'cost_analytics': self._analyze_costs(workflows),
            'performance_analytics': self._analyze_performance(workflows),
            'quality_analytics': self._analyze_quality(workflows),
            'self_correction_analytics': self._analyze_self_correction(workflows),
            'phase_breakdown': self._analyze_phases(workflows)
        }

        return analytics

    def _analyze_costs(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze cost metrics."""
        total_cost = sum(w.total_cost_usd for w in workflows)
        avg_cost = total_cost / len(workflows) if workflows else 0

        # Cost by phase
        architect_cost = sum(w.architect_cost_usd for w in workflows)
        developer_cost = sum(w.developer_cost_usd for w in workflows)
        tester_cost = sum(w.tester_cost_usd for w in workflows)
        reviewer_cost = sum(w.reviewer_cost_usd for w in workflows)
        self_correction_cost = sum(w.self_correction_cost_usd for w in workflows)

        return {
            'total_cost_usd': round(total_cost, 6),
            'average_cost_per_workflow_usd': round(avg_cost, 6),
            'min_cost_usd': round(min(w.total_cost_usd for w in workflows), 6),
            'max_cost_usd': round(max(w.total_cost_usd for w in workflows), 6),
            'cost_by_phase': {
                'architect': round(architect_cost, 6),
                'developer': round(developer_cost, 6),
                'tester': round(tester_cost, 6),
                'reviewer': round(reviewer_cost, 6),
                'self_correction': round(self_correction_cost, 6)
            },
            'cost_distribution': {
                'architect_pct': round((architect_cost / total_cost * 100) if total_cost > 0 else 0, 2),
                'developer_pct': round((developer_cost / total_cost * 100) if total_cost > 0 else 0, 2),
                'tester_pct': round((tester_cost / total_cost * 100) if total_cost > 0 else 0, 2),
                'reviewer_pct': round((reviewer_cost / total_cost * 100) if total_cost > 0 else 0, 2),
                'self_correction_pct': round((self_correction_cost / total_cost * 100) if total_cost > 0 else 0, 2)
            }
        }

    def _analyze_performance(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze performance metrics."""
        total_time = sum(w.total_execution_time_ms for w in workflows)
        avg_time = total_time / len(workflows) if workflows else 0

        total_tokens = sum(w.total_tokens for w in workflows)
        avg_tokens = total_tokens / len(workflows) if workflows else 0

        return {
            'total_execution_time_ms': round(total_time, 2),
            'average_execution_time_ms': round(avg_time, 2),
            'average_execution_time_seconds': round(avg_time / 1000, 2),
            'min_execution_time_ms': round(min(w.total_execution_time_ms for w in workflows), 2),
            'max_execution_time_ms': round(max(w.total_execution_time_ms for w in workflows), 2),
            'total_tokens': total_tokens,
            'average_tokens_per_workflow': round(avg_tokens, 0),
            'tokens_per_second': round(total_tokens / (total_time / 1000) if total_time > 0 else 0, 2)
        }

    def _analyze_quality(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze quality metrics."""
        workflows_with_scores = [w for w in workflows if w.overall_quality_score is not None]

        if not workflows_with_scores:
            return {'error': 'No quality scores available'}

        scores = [w.overall_quality_score for w in workflows_with_scores]

        return {
            'average_quality_score': round(sum(scores) / len(scores), 2),
            'min_quality_score': min(scores),
            'max_quality_score': max(scores),
            'workflows_above_90': sum(1 for s in scores if s >= 90),
            'workflows_above_80': sum(1 for s in scores if s >= 80),
            'workflows_above_70': sum(1 for s in scores if s >= 70),
            'quality_distribution': {
                'excellent (90-100)': sum(1 for s in scores if s >= 90),
                'good (80-89)': sum(1 for s in scores if 80 <= s < 90),
                'fair (70-79)': sum(1 for s in scores if 70 <= s < 80),
                'poor (<70)': sum(1 for s in scores if s < 70)
            }
        }

    def _analyze_self_correction(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze self-correction metrics."""
        workflows_with_corrections = [w for w in workflows if w.total_iterations > 4]

        return {
            'total_workflows_with_corrections': len(workflows_with_corrections),
            'correction_rate': round(len(workflows_with_corrections) / len(workflows) * 100, 2) if workflows else 0,
            'average_iterations': round(sum(w.total_iterations for w in workflows) / len(workflows), 2) if workflows else 0,
            'total_self_correction_cost_usd': round(sum(w.self_correction_cost_usd for w in workflows), 6),
            'phases_most_corrected': self._get_most_corrected_phases(workflows)
        }

    def _get_most_corrected_phases(self, workflows: List[WorkflowMetrics]) -> Dict[str, int]:
        """Get count of corrections by phase."""
        phase_corrections = {}

        for workflow in workflows:
            for phase in workflow.phases_self_corrected:
                phase_corrections[phase] = phase_corrections.get(phase, 0) + 1

        return phase_corrections

    def _analyze_phases(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze metrics by phase."""
        phases = ['architect', 'developer', 'tester', 'reviewer']
        phase_analysis = {}

        for phase in phases:
            costs = [getattr(w, f'{phase}_cost_usd') for w in workflows]
            times = [getattr(w, f'{phase}_time_ms') for w in workflows]
            tokens = [getattr(w, f'{phase}_tokens') for w in workflows]
            scores = [getattr(w, f'{phase}_score') for w in workflows if getattr(w, f'{phase}_score') is not None]

            phase_analysis[phase] = {
                'total_cost_usd': round(sum(costs), 6),
                'average_cost_usd': round(sum(costs) / len(costs), 6) if costs else 0,
                'total_time_ms': round(sum(times), 2),
                'average_time_ms': round(sum(times) / len(times), 2) if times else 0,
                'total_tokens': sum(tokens),
                'average_tokens': round(sum(tokens) / len(tokens), 0) if tokens else 0,
                'average_quality_score': round(sum(scores) / len(scores), 2) if scores else None
            }

        return phase_analysis

    def export_to_json(self, filepath: Optional[str] = None):
        """Export metrics to JSON file."""
        if filepath is None:
            filepath = self.storage_path / f'metrics_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        filepath = Path(filepath)

        data = {
            'exported_at': datetime.now().isoformat(),
            'total_workflows': len(self.workflows),
            'analytics': self.get_analytics(),
            'workflows': [w.to_dict() for w in self.workflows]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Exported metrics to {filepath}")

    def export_to_csv(self, filepath: Optional[str] = None):
        """Export metrics to CSV file."""
        if filepath is None:
            filepath = self.storage_path / f'metrics_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        filepath = Path(filepath)

        if not self.workflows:
            print("⚠️  No workflows to export")
            return

        # Define CSV columns
        fieldnames = [
            'workflow_id', 'timestamp', 'task', 'success',
            'overall_quality_score', 'total_cost_usd', 'total_execution_time_ms',
            'total_tokens', 'total_iterations',
            'architect_cost_usd', 'developer_cost_usd', 'tester_cost_usd', 'reviewer_cost_usd',
            'architect_score', 'developer_score', 'tester_score', 'reviewer_score',
            'phases_self_corrected', 'self_correction_cost_usd'
        ]

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for workflow in self.workflows:
                row = {field: getattr(workflow, field, '') for field in fieldnames}
                # Convert list to string for CSV
                row['phases_self_corrected'] = ','.join(workflow.phases_self_corrected)
                writer.writerow(row)

        print(f"✅ Exported metrics to CSV: {filepath}")

    def print_summary(self, last_n: Optional[int] = None):
        """Print analytics summary."""
        analytics = self.get_analytics(last_n=last_n)

        if 'error' in analytics:
            print(f"❌ {analytics['error']}")
            return

        print("\n" + "=" * 80)
        print("WORKFLOW METRICS SUMMARY")
        print("=" * 80)

        # Summary
        summary = analytics['summary']
        print(f"\nTotal Workflows: {summary['total_workflows']}")
        print(f"Successful: {summary['successful_workflows']} ({summary['success_rate']*100:.1f}%)")

        # Cost Analytics
        cost = analytics['cost_analytics']
        print(f"\n💰 COST ANALYTICS:")
        print(f"  Total Cost: ${cost['total_cost_usd']:.6f}")
        print(f"  Average per Workflow: ${cost['average_cost_per_workflow_usd']:.6f}")
        print(f"  Range: ${cost['min_cost_usd']:.6f} - ${cost['max_cost_usd']:.6f}")
        print(f"\n  Cost by Phase:")
        for phase, phase_cost in cost['cost_by_phase'].items():
            pct = cost['cost_distribution'][f'{phase}_pct']
            print(f"    {phase.capitalize()}: ${phase_cost:.6f} ({pct:.1f}%)")

        # Performance Analytics
        perf = analytics['performance_analytics']
        print(f"\n⚡ PERFORMANCE ANALYTICS:")
        print(f"  Average Execution Time: {perf['average_execution_time_seconds']:.2f}s")
        print(f"  Average Tokens: {perf['average_tokens_per_workflow']:,.0f}")
        print(f"  Tokens per Second: {perf['tokens_per_second']:.0f}")

        # Quality Analytics
        quality = analytics['quality_analytics']
        if 'error' not in quality:
            print(f"\n✅ QUALITY ANALYTICS:")
            print(f"  Average Score: {quality['average_quality_score']:.1f}/100")
            print(f"  Range: {quality['min_quality_score']} - {quality['max_quality_score']}")
            print(f"  Above 90: {quality['workflows_above_90']} workflows")

        # Self-Correction Analytics
        correction = analytics['self_correction_analytics']
        print(f"\n🔄 SELF-CORRECTION ANALYTICS:")
        print(f"  Workflows with Corrections: {correction['total_workflows_with_corrections']}")
        print(f"  Correction Rate: {correction['correction_rate']:.1f}%")
        print(f"  Average Iterations: {correction['average_iterations']:.1f}")

        print("=" * 80)


# Example usage
if __name__ == "__main__":
    tracker = WorkflowMetricsTracker()

    # Print summary if metrics exist
    if tracker.workflows:
        tracker.print_summary()
        tracker.print_summary(last_n=10)  # Last 10 workflows
    else:
        print("No workflow metrics recorded yet.")
        print("Run workflows using SpecializedRolesOrchestrator to generate metrics.")
