"""
A/B Testing Framework for Output Styles

Compare output styles empirically to determine which works best for specific tasks.

Features:
- Run same prompt with different output styles
- Collect quality metrics (user ratings, automated checks, cost, time)
- Statistical analysis of results
- Recommendation based on data
- Persistent test results

Usage:
    from style_ab_testing import StyleABTest, TestConfig

    # Create test
    test = StyleABTest(
        test_name="code-generation-comparison",
        prompt="Implement a binary search function",
        styles=["code", "detailed"],
        role="developer"
    )

    # Run test
    results = test.run(num_trials=5)

    # Analyze
    winner = test.get_winner()
    print(f"Winner: {winner}")

Architecture:
- StyleABTest: Main test orchestrator
- TestConfig: Configuration for a single test
- TestResult: Result from single trial
- ABTestReport: Aggregated results with statistics
"""

import json
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """Configuration for an A/B test."""
    test_name: str
    prompt: str
    styles: List[str]
    role: str = "developer"
    model: str = "claude-3-5-sonnet-20241022"
    num_trials: int = 3
    quality_metrics: List[str] = field(default_factory=lambda: ["speed", "cost", "quality"])
    context: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """Result from a single trial."""
    style: str
    trial_num: int
    success: bool
    output: Optional[str] = None
    duration_ms: float = 0.0
    cost_usd: float = 0.0
    tokens_used: int = 0
    quality_score: Optional[float] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class StyleMetrics:
    """Aggregated metrics for a style across multiple trials."""
    style: str
    total_trials: int
    successful_trials: int
    failed_trials: int
    success_rate: float
    avg_duration_ms: float
    avg_cost_usd: float
    avg_quality_score: Optional[float]
    total_cost_usd: float
    min_duration_ms: float
    max_duration_ms: float
    std_dev_duration: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ABTestReport:
    """Complete A/B test report with statistical analysis."""
    test_name: str
    test_config: TestConfig
    results_by_style: Dict[str, List[TestResult]]
    metrics_by_style: Dict[str, StyleMetrics]
    winner: Optional[str]
    winner_reason: str
    recommendations: List[str]
    test_duration_seconds: float
    total_cost_usd: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "test_config": asdict(self.test_config),
            "results_by_style": {
                style: [r.to_dict() for r in results]
                for style, results in self.results_by_style.items()
            },
            "metrics_by_style": {
                style: metrics.to_dict()
                for style, metrics in self.metrics_by_style.items()
            },
            "winner": self.winner,
            "winner_reason": self.winner_reason,
            "recommendations": self.recommendations,
            "test_duration_seconds": self.test_duration_seconds,
            "total_cost_usd": self.total_cost_usd,
            "timestamp": self.timestamp
        }


class StyleABTest:
    """
    A/B testing framework for comparing output styles.

    Example:
        test = StyleABTest(
            test_name="code-vs-detailed",
            prompt="Explain binary search",
            styles=["code", "detailed"],
            role="explainer"
        )

        results = test.run(num_trials=3)
        print(f"Winner: {test.get_winner()}")
    """

    def __init__(
        self,
        test_name: str,
        prompt: str,
        styles: List[str],
        role: str = "developer",
        model: str = "claude-3-5-sonnet-20241022",
        results_dir: Optional[Path] = None,
        agent_factory: Optional[Callable] = None
    ):
        """
        Initialize A/B test.

        Args:
            test_name: Name of this test (for tracking)
            prompt: The prompt to test with
            styles: List of output styles to compare (2-4 styles)
            role: Agent role
            model: Model to use for all tests
            results_dir: Directory to save results (default: ~/.claude/ab_tests/)
            agent_factory: Optional factory function to create agents
                         Signature: (role, model, output_style) -> agent
        """
        if len(styles) < 2:
            raise ValueError("Need at least 2 styles to compare")

        if len(styles) > 4:
            raise ValueError("Maximum 4 styles can be compared at once")

        self.test_name = test_name
        self.prompt = prompt
        self.styles = styles
        self.role = role
        self.model = model

        # Results directory
        if results_dir is None:
            results_dir = Path.home() / ".claude" / "ab_tests"
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Agent factory (for creating test agents)
        self.agent_factory = agent_factory

        # Test results
        self.results: Dict[str, List[TestResult]] = {style: [] for style in styles}
        self.report: Optional[ABTestReport] = None

    def run(
        self,
        num_trials: int = 3,
        context: Optional[Dict[str, Any]] = None,
        quality_evaluator: Optional[Callable[[str], float]] = None
    ) -> ABTestReport:
        """
        Run A/B test across all styles.

        Args:
            num_trials: Number of trials per style (default: 3)
            context: Optional context for prompts
            quality_evaluator: Optional function to evaluate output quality
                              Signature: (output: str) -> float (0-100)

        Returns:
            ABTestReport with aggregated results
        """
        logger.info(f"Starting A/B test '{self.test_name}' with {len(self.styles)} styles")

        start_time = time.time()

        # Run trials for each style
        for style in self.styles:
            logger.info(f"Testing style: {style} ({num_trials} trials)")

            for trial_num in range(1, num_trials + 1):
                result = self._run_single_trial(
                    style, trial_num, context, quality_evaluator
                )
                self.results[style].append(result)

                if result.success:
                    logger.info(
                        f"  Trial {trial_num}/{num_trials}: ✅ "
                        f"{result.duration_ms:.0f}ms, ${result.cost_usd:.4f}"
                    )
                else:
                    logger.warning(
                        f"  Trial {trial_num}/{num_trials}: ❌ {result.error}"
                    )

        # Calculate metrics
        test_duration = time.time() - start_time
        metrics_by_style = self._calculate_metrics()

        # Determine winner
        winner, winner_reason = self._determine_winner(metrics_by_style)

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics_by_style)

        # Calculate total cost
        total_cost = sum(
            sum(r.cost_usd for r in results)
            for results in self.results.values()
        )

        # Create report
        test_config = TestConfig(
            test_name=self.test_name,
            prompt=self.prompt,
            styles=self.styles,
            role=self.role,
            model=self.model,
            num_trials=num_trials,
            context=context
        )

        self.report = ABTestReport(
            test_name=self.test_name,
            test_config=test_config,
            results_by_style=self.results,
            metrics_by_style=metrics_by_style,
            winner=winner,
            winner_reason=winner_reason,
            recommendations=recommendations,
            test_duration_seconds=test_duration,
            total_cost_usd=total_cost
        )

        # Save report
        self._save_report()

        logger.info(f"Test complete. Winner: {winner}")

        return self.report

    def _run_single_trial(
        self,
        style: str,
        trial_num: int,
        context: Optional[Dict[str, Any]],
        quality_evaluator: Optional[Callable[[str], float]]
    ) -> TestResult:
        """Run a single trial with one style."""
        start_time = time.time()

        try:
            # Create agent (or use mock if no factory)
            if self.agent_factory:
                agent = self.agent_factory(self.role, self.model, style)
                call_result = agent.call(self.prompt, context)

                # Extract metrics from call result
                duration_ms = call_result.latency * 1000
                cost_usd = call_result.cost
                tokens_used = call_result.total_tokens
                output = call_result.output
                success = call_result.success
                error = call_result.error

            else:
                # Mock execution for testing
                duration_ms = (time.time() - start_time) * 1000
                cost_usd = 0.001  # Mock cost
                tokens_used = 100
                output = f"Mock output for style '{style}'"
                success = True
                error = None

            # Evaluate quality if evaluator provided
            quality_score = None
            if quality_evaluator and success and output:
                try:
                    quality_score = quality_evaluator(output)
                except Exception as e:
                    logger.warning(f"Quality evaluation failed: {e}")

            return TestResult(
                style=style,
                trial_num=trial_num,
                success=success,
                output=output,
                duration_ms=duration_ms,
                cost_usd=cost_usd,
                tokens_used=tokens_used,
                quality_score=quality_score,
                error=error
            )

        except Exception as e:
            logger.error(f"Trial failed: {e}")
            duration_ms = (time.time() - start_time) * 1000

            return TestResult(
                style=style,
                trial_num=trial_num,
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )

    def _calculate_metrics(self) -> Dict[str, StyleMetrics]:
        """Calculate aggregated metrics for each style."""
        metrics = {}

        for style, results in self.results.items():
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]

            # Durations (successful trials only)
            durations = [r.duration_ms for r in successful]

            # Costs
            total_cost = sum(r.cost_usd for r in results)
            avg_cost = sum(r.cost_usd for r in successful) / len(successful) if successful else 0.0

            # Quality scores
            quality_scores = [r.quality_score for r in successful if r.quality_score is not None]
            avg_quality = statistics.mean(quality_scores) if quality_scores else None

            metrics[style] = StyleMetrics(
                style=style,
                total_trials=len(results),
                successful_trials=len(successful),
                failed_trials=len(failed),
                success_rate=len(successful) / len(results) if results else 0.0,
                avg_duration_ms=statistics.mean(durations) if durations else 0.0,
                avg_cost_usd=avg_cost,
                avg_quality_score=avg_quality,
                total_cost_usd=total_cost,
                min_duration_ms=min(durations) if durations else 0.0,
                max_duration_ms=max(durations) if durations else 0.0,
                std_dev_duration=statistics.stdev(durations) if len(durations) > 1 else 0.0
            )

        return metrics

    def _determine_winner(
        self,
        metrics: Dict[str, StyleMetrics]
    ) -> tuple[Optional[str], str]:
        """
        Determine the winning style based on metrics.

        Priority:
        1. Success rate (must be > 50%)
        2. Quality score (if available)
        3. Cost efficiency (quality/cost ratio)
        4. Speed (duration)
        """
        # Filter styles with acceptable success rate
        acceptable = {
            style: m for style, m in metrics.items()
            if m.success_rate > 0.5
        }

        if not acceptable:
            return None, "No style had >50% success rate"

        # If quality scores available, use quality-cost ratio
        if any(m.avg_quality_score is not None for m in acceptable.values()):
            # Calculate quality/cost ratio
            quality_styles = {
                style: (m.avg_quality_score / max(m.avg_cost_usd, 0.0001))
                for style, m in acceptable.items()
                if m.avg_quality_score is not None
            }

            if quality_styles:
                winner = max(quality_styles, key=quality_styles.get)
                winner_metrics = metrics[winner]
                return (
                    winner,
                    f"Best quality/cost ratio: {winner_metrics.avg_quality_score:.1f} quality, "
                    f"${winner_metrics.avg_cost_usd:.4f} avg cost"
                )

        # Otherwise, use cost as primary factor
        winner = min(acceptable, key=lambda s: acceptable[s].avg_cost_usd)
        winner_metrics = metrics[winner]

        return (
            winner,
            f"Lowest cost: ${winner_metrics.avg_cost_usd:.4f} avg, "
            f"{winner_metrics.avg_duration_ms:.0f}ms avg duration"
        )

    def _generate_recommendations(
        self,
        metrics: Dict[str, StyleMetrics]
    ) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        # Check for styles with poor success rate
        for style, m in metrics.items():
            if m.success_rate < 0.5:
                recommendations.append(
                    f"❌ Avoid '{style}' style for this task ({m.success_rate*100:.0f}% success rate)"
                )

        # Identify fastest style
        successful_styles = {s: m for s, m in metrics.items() if m.success_rate > 0.5}
        if successful_styles:
            fastest = min(successful_styles, key=lambda s: successful_styles[s].avg_duration_ms)
            recommendations.append(
                f"⚡ '{fastest}' is fastest ({metrics[fastest].avg_duration_ms:.0f}ms avg)"
            )

            # Identify cheapest style
            cheapest = min(successful_styles, key=lambda s: successful_styles[s].avg_cost_usd)
            recommendations.append(
                f"💰 '{cheapest}' is cheapest (${metrics[cheapest].avg_cost_usd:.4f} avg)"
            )

            # Identify highest quality (if available)
            quality_styles = {
                s: m for s, m in successful_styles.items()
                if m.avg_quality_score is not None
            }
            if quality_styles:
                highest_quality = max(quality_styles, key=lambda s: quality_styles[s].avg_quality_score)
                recommendations.append(
                    f"⭐ '{highest_quality}' has highest quality ({metrics[highest_quality].avg_quality_score:.1f}/100)"
                )

        return recommendations

    def _save_report(self):
        """Save test report to JSON file."""
        if not self.report:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.test_name}_{timestamp}.json"
        filepath = self.results_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(self.report.to_dict(), f, indent=2)

            logger.info(f"Test report saved to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    def get_winner(self) -> Optional[str]:
        """Get the winning style (run test first)."""
        if self.report:
            return self.report.winner
        return None

    def get_report(self) -> Optional[ABTestReport]:
        """Get the full test report."""
        return self.report

    def print_summary(self):
        """Print a human-readable summary of results."""
        if not self.report:
            print("No results yet. Run test first.")
            return

        print("\n" + "=" * 80)
        print(f"A/B TEST REPORT: {self.test_name}")
        print("=" * 80)

        print(f"\nTest Configuration:")
        print(f"  Prompt: {self.prompt[:60]}...")
        print(f"  Styles tested: {', '.join(self.styles)}")
        print(f"  Trials per style: {len(self.results[self.styles[0]])}")
        print(f"  Total duration: {self.report.test_duration_seconds:.1f}s")
        print(f"  Total cost: ${self.report.total_cost_usd:.4f}")

        print(f"\nResults by Style:")
        for style, metrics in self.report.metrics_by_style.items():
            print(f"\n  {style}:")
            print(f"    Success rate: {metrics.success_rate*100:.0f}%")
            print(f"    Avg duration: {metrics.avg_duration_ms:.0f}ms")
            print(f"    Avg cost: ${metrics.avg_cost_usd:.4f}")
            if metrics.avg_quality_score is not None:
                print(f"    Avg quality: {metrics.avg_quality_score:.1f}/100")

        print(f"\nWinner: {self.report.winner}")
        print(f"Reason: {self.report.winner_reason}")

        print(f"\nRecommendations:")
        for rec in self.report.recommendations:
            print(f"  {rec}")

        print("\n" + "=" * 80)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_test_report(filepath: Path) -> ABTestReport:
    """
    Load a saved test report from JSON file.

    Args:
        filepath: Path to report JSON file

    Returns:
        ABTestReport instance
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Reconstruct objects from dictionaries
    # (This is simplified - in production you'd want proper deserialization)
    return ABTestReport(
        test_name=data["test_name"],
        test_config=TestConfig(**data["test_config"]),
        results_by_style={
            style: [TestResult(**r) for r in results]
            for style, results in data["results_by_style"].items()
        },
        metrics_by_style={
            style: StyleMetrics(**metrics)
            for style, metrics in data["metrics_by_style"].items()
        },
        winner=data["winner"],
        winner_reason=data["winner_reason"],
        recommendations=data["recommendations"],
        test_duration_seconds=data["test_duration_seconds"],
        total_cost_usd=data["total_cost_usd"],
        timestamp=data["timestamp"]
    )


if __name__ == "__main__":
    # Demo A/B test
    logging.basicConfig(level=logging.INFO)

    test = StyleABTest(
        test_name="code-vs-detailed-demo",
        prompt="Explain how binary search works",
        styles=["code", "detailed"],
        role="explainer"
    )

    # Run with mock (no actual agent calls)
    report = test.run(num_trials=3)

    # Print summary
    test.print_summary()
