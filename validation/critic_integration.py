"""
Validation Critic Integration - Critic Orchestration and Analysis

This module integrates validation with critic-based deep semantic analysis.

Architecture:
    Two-Stage Evaluation:
    1. VALIDATORS (fast, structural): Validation patterns and checks
    2. CRITICS (deep, semantic): Unbiased analysis with Opus

Philosophy: "Creator Cannot Be Judge"
    - Critics receive FRESH CONTEXT (code only, no task history)
    - Validators check "what's there", critics analyze "how well it works"
    - Complementary, not redundant

Usage:
    from validation.critic_integration import CriticIntegration

    integration = CriticIntegration(orchestrator)
    result = integration.validate_with_critics(code, level="standard")
"""

from typing import List, Dict, Optional, Literal, Any
import time

from validation.interfaces import ValidationLevel
from validation_types import ValidationFinding

# Observability
try:
    from observability.event_emitter import EventEmitter, EventType, EventSeverity
except ImportError:
    EventEmitter = None
    EventType = None
    EventSeverity = None


class CriticIntegration:
    """
    Integrates validation with critic-based deep semantic analysis.

    Combines fast validation with deep critic analysis for comprehensive evaluation.
    """

    def __init__(self, orchestrator):
        """
        Initialize CriticIntegration.

        Args:
            orchestrator: ValidationOrchestrator instance
        """
        self.orchestrator = orchestrator

    def validate_with_critics(
        self,
        code: str,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None,
        run_validators: bool = True,
        critics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive code evaluation combining validators and critics.

        Two-Stage Evaluation:
        1. VALIDATORS (fast, structural): Check for presence of security features,
           basic patterns, structural issues. Uses Haiku/Sonnet.
        2. CRITICS (deep, semantic): Unbiased analysis of actual vulnerabilities,
           performance issues, architectural problems. Uses Opus MANDATORY.

        Args:
            code: Source code to evaluate
            context: Optional context dictionary
            level: Validation level (quick/standard/thorough)
            run_validators: If True, run validators first (recommended)
            critics: Specific critics to run (overrides level-based selection)

        Returns:
            Dictionary with comprehensive evaluation results
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        level = level or self.orchestrator.default_level
        context = context or {}

        # Lazy import to avoid circular dependency
        from critic_orchestrator import CriticOrchestrator

        start_time = time.time()

        # Start workflow trace
        trace_id = None
        if self.orchestrator.emitter:
            trace_id = self.orchestrator.emitter.start_trace(
                workflow="validate_with_critics",
                context={
                    "level": level,
                    "file_path": context.get('file_path', 'unknown'),
                    "run_validators": run_validators,
                    "critics": critics or "auto"
                }
            )

        # Stage 1: Run validators (fast, structural checks)
        validator_result = None
        if run_validators:
            print("Stage 1: Running validators (fast structural checks)...")

            # Start validator span
            if self.orchestrator.emitter:
                self.orchestrator.emitter.start_span("validators")

            validator_result = self.orchestrator.validate_code(
                code=code,
                context=context,
                level=level
            )
            print(f"Validator result: {validator_result.status} (score: {validator_result.score}/100)")

            # End validator span
            if self.orchestrator.emitter:
                self.orchestrator.emitter.end_span()

        # Stage 2: Select critics based on level
        if critics is None:
            critics = self._select_critics_for_level(level)

        # Stage 3: Run critics (deep semantic analysis with FRESH CONTEXT)
        critic_results = {}
        critic_report = None
        if critics:
            print(f"\nStage 2: Running {len(critics)} critics (deep semantic analysis with Opus)...")
            print(f"Critics: {', '.join(critics)}")

            # Start critic span
            if self.orchestrator.emitter:
                self.orchestrator.emitter.start_span("critics")

            # Initialize CriticOrchestrator
            critic_orchestrator = CriticOrchestrator()

            # Run critics with FRESH CONTEXT (code only, no history)
            critic_results = critic_orchestrator.review_code(
                code_snippet=code,
                file_path=context.get('file_path'),
                critics=critics,
                language=context.get('language')
            )

            # Generate aggregated critic report
            critic_report = critic_orchestrator.generate_report(
                results=critic_results,
                code_snippet=code,
                file_path=context.get('file_path')
            )

            print(f"Critic report: {critic_report.worst_grade} (score: {critic_report.overall_score}/100)")
            print(f"Total findings: {critic_report.total_findings} "
                  f"(Critical: {critic_report.critical_findings}, High: {critic_report.high_findings})")

            # End critic span
            if self.orchestrator.emitter:
                self.orchestrator.emitter.end_span()

        # Calculate overall metrics
        total_time = time.time() - start_time

        # Overall score (weighted average: validators 30%, critics 70%)
        if validator_result and critic_report:
            overall_score = int(
                (validator_result.score * 0.3) + (critic_report.overall_score * 0.7)
            )
        elif validator_result:
            overall_score = validator_result.score
        elif critic_report:
            overall_score = critic_report.overall_score
        else:
            overall_score = 0

        # Worst grade
        grades = []
        if validator_result:
            # Map validator status to grade
            status_to_grade = {
                "PASS": "GOOD",
                "WARNING": "FAIR",
                "FAIL": "POOR"
            }
            grades.append(status_to_grade.get(validator_result.status, "UNKNOWN"))
        if critic_report:
            grades.append(critic_report.worst_grade)

        grade_priority = {
            "CRITICAL": 0,
            "POOR": 1,
            "FAIL": 1,
            "FAIR": 2,
            "WARNING": 2,
            "GOOD": 3,
            "PASS": 3,
            "EXCELLENT": 4,
            "UNKNOWN": -1
        }
        worst_grade = min(grades, key=lambda g: grade_priority.get(g, -1)) if grades else "UNKNOWN"

        # Total cost
        total_cost = 0.0
        if validator_result:
            total_cost += validator_result.cost_usd
        if critic_report:
            total_cost += critic_report.total_cost_usd

        # Recommendation logic
        critical_count = 0
        high_count = 0

        if validator_result:
            critical_count += sum(1 for f in validator_result.findings if f.severity == "CRITICAL")
            high_count += sum(1 for f in validator_result.findings if f.severity == "HIGH")

        if critic_report:
            critical_count += critic_report.critical_findings
            high_count += critic_report.high_findings

        # Recommendation decision tree
        if critical_count > 0:
            recommendation = "NO-GO"
        elif high_count >= 3:
            recommendation = "FIX-CRITICAL"
        elif high_count > 0:
            recommendation = "FIX-HIGH"
        elif overall_score >= 80:
            recommendation = "GO"
        else:
            recommendation = "REVIEW"

        # Build comprehensive result
        result = {
            "validator_result": validator_result,
            "critic_results": critic_results,
            "aggregated_report": critic_report,
            "overall_score": overall_score,
            "worst_grade": worst_grade,
            "total_cost_usd": round(total_cost, 6),
            "total_time_seconds": round(total_time, 2),
            "recommendation": recommendation,
            "metrics": {
                "validators_run": 1 if validator_result else 0,
                "critics_run": len(critic_results),
                "total_findings": (
                    len(validator_result.findings) if validator_result else 0
                ) + (
                    critic_report.total_findings if critic_report else 0
                ),
                "critical_findings": critical_count,
                "high_findings": high_count
            }
        }

        # End workflow trace
        if self.orchestrator.emitter:
            self.orchestrator.emitter.end_trace(
                success=True,
                result={
                    "overall_score": overall_score,
                    "recommendation": recommendation,
                    "total_cost": total_cost,
                    "validators_run": result["metrics"]["validators_run"],
                    "critics_run": result["metrics"]["critics_run"]
                }
            )

        return result

    def _select_critics_for_level(
        self,
        level: ValidationLevel
    ) -> List[str]:
        """
        Select critics based on validation level.

        Selection Strategy:
        - quick: No critics (validators only for speed)
        - standard: 2-3 key critics (security, performance, architecture)
        - thorough: All 5 critics (complete analysis)

        Args:
            level: Validation level

        Returns:
            List of critic IDs to run
        """
        if level == "quick":
            # No critics - validators only for speed
            return []

        elif level == "standard":
            # Key critics for typical issues
            return [
                "security-critic",      # Security vulnerabilities
                "performance-critic",   # Performance bottlenecks
                "architecture-critic"   # SOLID violations
            ]

        elif level == "thorough":
            # All critics for comprehensive analysis
            return [
                "security-critic",
                "performance-critic",
                "architecture-critic",
                "code-quality-critic",
                "documentation-critic"
            ]

        else:
            raise ValueError(f"Unknown level: {level}")

    def print_combined_report(self, result: Dict[str, Any]) -> None:
        """
        Print human-readable combined validator + critic report.

        Args:
            result: Result from validate_with_critics()
        """
        print("\n" + "=" * 80)
        print("COMPREHENSIVE CODE EVALUATION REPORT")
        print("=" * 80)

        # Overall assessment
        print(f"\n--- OVERALL ASSESSMENT ---")
        print(f"Score: {result['overall_score']}/100")
        print(f"Grade: {result['worst_grade']}")
        print(f"Recommendation: {result['recommendation']}")

        # Metrics
        metrics = result['metrics']
        print(f"\n--- EXECUTION METRICS ---")
        print(f"Validators Run: {metrics['validators_run']}")
        print(f"Critics Run: {metrics['critics_run']}")
        print(f"Total Findings: {metrics['total_findings']}")
        print(f"  - Critical: {metrics['critical_findings']}")
        print(f"  - High: {metrics['high_findings']}")
        print(f"Total Cost: ${result['total_cost_usd']:.4f}")
        print(f"Total Time: {result['total_time_seconds']:.2f}s")

        # Validator results
        if result['validator_result']:
            val_result = result['validator_result']
            print(f"\n--- VALIDATOR RESULTS ---")
            print(f"Status: {val_result.status}")
            print(f"Score: {val_result.score}/100")
            print(f"Findings: {len(val_result.findings)}")
            print(f"Cost: ${val_result.cost_usd:.6f}")

        # Critic results
        if result['critic_results']:
            print(f"\n--- CRITIC RESULTS ---")
            for critic_id, critic_result in result['critic_results'].items():
                print(f"\n{critic_id}:")
                print(f"  Score: {critic_result.overall_score}/100 ({critic_result.grade})")
                print(f"  Findings: {len(critic_result.findings)}")
                if critic_result.success:
                    stats = critic_result.statistics
                    print(f"    Critical: {stats.get('critical', 0)}, "
                          f"High: {stats.get('high', 0)}, "
                          f"Medium: {stats.get('medium', 0)}, "
                          f"Low: {stats.get('low', 0)}")
                else:
                    print(f"  Error: {critic_result.error}")

        # Recommendation explanation
        print(f"\n--- RECOMMENDATION: {result['recommendation']} ---")
        if result['recommendation'] == "NO-GO":
            print("⛔ Critical issues found. Do NOT proceed until fixed.")
        elif result['recommendation'] == "FIX-CRITICAL":
            print("⚠️  Multiple high-severity issues. Fix before proceeding.")
        elif result['recommendation'] == "FIX-HIGH":
            print("⚠️  High-severity issues found. Recommend fixing.")
        elif result['recommendation'] == "GO":
            print("✅ Code quality is good. Safe to proceed.")
        elif result['recommendation'] == "REVIEW":
            print("👀 Code needs review. Some issues present.")

        print("\n" + "=" * 80)
