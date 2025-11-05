#!/usr/bin/env python3
"""
Refinement Loop - Closed-Loop Self-Correction System

Implements iterative refinement with validation feedback.
Enables agents to automatically improve their outputs based on
validation findings until quality thresholds are met.

Architecture:
1. Generate initial artifact
2. Run quality gate validation
3. Extract actionable feedback from findings
4. Regenerate based on feedback
5. Repeat until PASS or max iterations
6. Return final result with validation history

Usage:
    from refinement_loop import RefinementLoop

    loop = RefinementLoop(max_iterations=3)
    result = await loop.refine(
        generator_func=generate_code,
        validator_func=validate_code,
        initial_input={"task": "Create REST API"}
    )
"""

import logging
import time
from typing import Dict, Any, Callable, Optional, List, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from validation_types import ValidationReport, ValidationFinding, Status
from observability.event_emitter import EventEmitter

# C5 Integration: Import for structured feedback extraction
try:
    from resilient_agent import ResilientBaseAgent
except ImportError:
    ResilientBaseAgent = None

logger = logging.getLogger(__name__)


@dataclass
class RefinementIteration:
    """
    Record of a single refinement iteration.

    Tracks the artifact, validation result, feedback, and cost for one cycle.
    """
    iteration_number: int
    artifact: str
    validation_report: ValidationReport
    feedback: List[str]
    regeneration_prompt: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_time_ms: int = 0
    cost_usd: float = 0.0

    @property
    def passed(self) -> bool:
        """Check if this iteration passed validation."""
        return self.validation_report.passed

    @property
    def status(self) -> Status:
        """Get validation status."""
        return self.validation_report.overall_status

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "iteration_number": self.iteration_number,
            "artifact_preview": self.artifact[:200] + "..." if len(self.artifact) > 200 else self.artifact,
            "validation_report": self.validation_report.to_dict(),
            "feedback": self.feedback,
            "regeneration_prompt": self.regeneration_prompt,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
            "cost_usd": self.cost_usd,
            "passed": self.passed,
            "status": self.status
        }


@dataclass
class RefinementResult:
    """
    Final result from refinement loop.

    Contains the final artifact, all iterations, and summary metrics.
    """
    success: bool
    final_artifact: str
    final_validation: ValidationReport
    iterations: List[RefinementIteration]
    total_iterations: int
    converged: bool  # True if validation passed, False if max iterations hit
    total_execution_time_ms: int
    total_cost_usd: float
    error: Optional[str] = None

    @property
    def passed_validation(self) -> bool:
        """Check if final artifact passed validation."""
        return self.final_validation.passed

    @property
    def improvement_history(self) -> List[float]:
        """Get average score progression across iterations."""
        return [it.validation_report.average_score for it in self.iterations]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "final_artifact_preview": self.final_artifact[:500] + "..." if len(self.final_artifact) > 500 else self.final_artifact,
            "final_validation": self.final_validation.to_dict(),
            "iterations": [it.to_dict() for it in self.iterations],
            "total_iterations": self.total_iterations,
            "converged": self.converged,
            "passed_validation": self.passed_validation,
            "improvement_history": self.improvement_history,
            "total_execution_time_ms": self.total_execution_time_ms,
            "total_cost_usd": self.total_cost_usd,
            "error": self.error
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        status_emoji = "✅" if self.converged else "❌"
        output = [
            "=" * 60,
            f"{status_emoji} REFINEMENT RESULT",
            "=" * 60,
            f"Status: {'CONVERGED' if self.converged else 'MAX ITERATIONS REACHED'}",
            f"Final Validation: {'PASSED' if self.passed_validation else 'FAILED'}",
            f"Total Iterations: {self.total_iterations}",
            f"Total Time: {self.total_execution_time_ms}ms",
            f"Total Cost: ${self.total_cost_usd:.4f}",
            "",
            "IMPROVEMENT HISTORY:",
            f"  Scores: {' → '.join(f'{s:.1f}' for s in self.improvement_history)}",
            ""
        ]

        if self.converged:
            output.append("✅ Quality threshold met")
        else:
            output.append("⚠️  Max iterations reached without convergence")

        output.append("=" * 60)
        return "\n".join(output)


class RefinementLoop:
    """
    Closed-loop refinement system with validation feedback.

    Automatically iterates on generated artifacts using validation
    feedback until quality thresholds are met or max iterations reached.

    Attributes:
        max_iterations: Maximum refinement cycles (default: 3)
        min_score_threshold: Minimum average score to pass (default: 80)
        allow_partial: Accept WARNING status if critical issues fixed (default: False)
        save_history: Save all iterations to disk (default: False)
    """

    def __init__(
        self,
        max_iterations: int = 3,
        min_score_threshold: float = 80.0,
        allow_partial: bool = False,
        save_history: bool = False,
        history_dir: Optional[Path] = None,
        agent: Optional['ResilientBaseAgent'] = None
    ):
        """
        Initialize refinement loop.

        Args:
            max_iterations: Max refinement cycles (1-10)
            min_score_threshold: Min score to pass (0-100)
            allow_partial: Accept WARNING if no critical issues
            save_history: Save iteration history to disk
            history_dir: Directory for history files
            agent: Optional ResilientBaseAgent for structured feedback extraction (C5)
        """
        if not 1 <= max_iterations <= 10:
            raise ValueError(f"max_iterations must be 1-10, got {max_iterations}")

        if not 0 <= min_score_threshold <= 100:
            raise ValueError(f"min_score_threshold must be 0-100, got {min_score_threshold}")

        self.max_iterations = max_iterations
        self.min_score_threshold = min_score_threshold
        self.allow_partial = allow_partial
        self.save_history = save_history
        self.history_dir = history_dir or Path.home() / ".claude/logs/refinement"
        self.agent = agent  # C5: Optional agent for structured feedback extraction
        self._last_structured_feedback: Optional[Dict[str, Any]] = None  # C5: Cache for structured feedback

        if save_history:
            self.history_dir.mkdir(parents=True, exist_ok=True)

        self.emitter = EventEmitter()

        logger.info(
            f"Initialized RefinementLoop (max_iter={max_iterations}, "
            f"min_score={min_score_threshold}, "
            f"structured_feedback={'enabled' if agent else 'disabled'})"
        )

    async def refine(
        self,
        generator_func: Callable[[Dict[str, Any]], Awaitable[str]],
        validator_func: Callable[[str, Dict[str, Any]], Awaitable[ValidationReport]],
        initial_input: Dict[str, Any],
        validation_context: Optional[Dict[str, Any]] = None
    ) -> RefinementResult:
        """
        Execute refinement loop with validation feedback.

        Args:
            generator_func: Async function that generates artifact from input
            validator_func: Async function that validates artifact
            initial_input: Input dict for generator (task description, context, etc.)
            validation_context: Context for validation (language, file_path, etc.)

        Returns:
            RefinementResult with final artifact and iteration history
        """
        start_time = time.time()
        iterations: List[RefinementIteration] = []
        total_cost = 0.0

        self.emitter.emit(
            event_type="refinement.loop.start",
            component="refinement_loop",
            message=f"Starting refinement loop (max_iterations={self.max_iterations})",
            metadata={
                "max_iterations": self.max_iterations,
                "min_score_threshold": self.min_score_threshold,
                "allow_partial": self.allow_partial
            }
        )

        logger.info(f"Starting refinement loop (max {self.max_iterations} iterations)")

        current_input = initial_input.copy()
        artifact = None
        validation_report = None

        try:
            for iteration_num in range(1, self.max_iterations + 1):
                iter_start = time.time()

                # C5: Reset structured feedback cache for this iteration
                self._last_structured_feedback = None

                logger.info(f"Iteration {iteration_num}/{self.max_iterations}")

                self.emitter.emit(
                    event_type="refinement.iteration.start",
                    component="refinement_loop",
                    message=f"Starting iteration {iteration_num}",
                    metadata={"iteration": iteration_num}
                )

                # STEP 1: Generate artifact
                artifact = await generator_func(current_input)
                if not artifact:
                    raise ValueError(f"Generator returned empty artifact at iteration {iteration_num}")

                logger.info(f"Generated artifact ({len(artifact)} chars)")

                # STEP 2: Validate artifact
                validation_report = await validator_func(artifact, validation_context or {})

                logger.info(
                    f"Validation complete: {validation_report.overall_status}, "
                    f"score={validation_report.average_score:.1f}"
                )

                # STEP 3: Extract feedback
                feedback = self._extract_feedback(validation_report, iteration_num)

                # STEP 4: Build regeneration prompt
                regen_prompt = self._build_regeneration_prompt(
                    original_input=initial_input,
                    artifact=artifact,
                    validation_report=validation_report,
                    feedback=feedback
                )

                iter_time_ms = int((time.time() - iter_start) * 1000)
                iter_cost = validation_report.total_cost_usd
                total_cost += iter_cost

                # Record iteration
                iteration = RefinementIteration(
                    iteration_number=iteration_num,
                    artifact=artifact,
                    validation_report=validation_report,
                    feedback=feedback,
                    regeneration_prompt=regen_prompt,
                    execution_time_ms=iter_time_ms,
                    cost_usd=iter_cost
                )
                iterations.append(iteration)

                self.emitter.emit(
                    event_type="refinement.iteration.complete",
                    component="refinement_loop",
                    severity="INFO" if iteration.passed else "WARNING",
                    message=f"Iteration {iteration_num} {'passed' if iteration.passed else 'failed'}",
                    metadata={
                        "iteration": iteration_num,
                        "status": iteration.status,
                        "score": validation_report.average_score,
                        "critical_count": validation_report.critical_count,
                        "high_count": validation_report.high_count,
                        "execution_time_ms": iter_time_ms,
                        "cost_usd": iter_cost
                    }
                )

                # STEP 5: Check convergence
                if self._has_converged(validation_report):
                    logger.info(f"✅ Converged at iteration {iteration_num}")

                    total_time_ms = int((time.time() - start_time) * 1000)

                    result = RefinementResult(
                        success=True,
                        final_artifact=artifact,
                        final_validation=validation_report,
                        iterations=iterations,
                        total_iterations=iteration_num,
                        converged=True,
                        total_execution_time_ms=total_time_ms,
                        total_cost_usd=total_cost
                    )

                    self.emitter.emit(
                        event_type="refinement.loop.complete",
                        component="refinement_loop",
                        severity="INFO",
                        message=f"Refinement converged after {iteration_num} iterations",
                        metadata={
                            "iterations": iteration_num,
                            "final_score": validation_report.average_score,
                            "total_cost_usd": total_cost,
                            "total_time_ms": total_time_ms
                        }
                    )

                    if self.save_history:
                        self._save_history(result)

                    return result

                # STEP 6: Prepare next iteration input
                current_input = {
                    **initial_input,
                    "previous_attempt": artifact,
                    "validation_feedback": feedback,
                    "regeneration_prompt": regen_prompt
                }

            # Max iterations reached without convergence
            logger.warning(f"⚠️  Max iterations ({self.max_iterations}) reached without convergence")

            total_time_ms = int((time.time() - start_time) * 1000)

            result = RefinementResult(
                success=False,
                final_artifact=artifact or "",
                final_validation=validation_report,
                iterations=iterations,
                total_iterations=self.max_iterations,
                converged=False,
                total_execution_time_ms=total_time_ms,
                total_cost_usd=total_cost,
                error="Max iterations reached without meeting quality threshold"
            )

            self.emitter.emit(
                event_type="refinement.loop.max_iterations",
                component="refinement_loop",
                severity="WARNING",
                message=f"Max iterations reached without convergence",
                metadata={
                    "max_iterations": self.max_iterations,
                    "final_score": validation_report.average_score if validation_report else 0,
                    "total_cost_usd": total_cost,
                    "total_time_ms": total_time_ms
                }
            )

            if self.save_history:
                self._save_history(result)

            return result

        except Exception as e:
            logger.error(f"Refinement loop failed: {e}", exc_info=True)

            total_time_ms = int((time.time() - start_time) * 1000)

            result = RefinementResult(
                success=False,
                final_artifact=artifact or "",
                final_validation=validation_report,
                iterations=iterations,
                total_iterations=len(iterations),
                converged=False,
                total_execution_time_ms=total_time_ms,
                total_cost_usd=total_cost,
                error=str(e)
            )

            self.emitter.emit(
                event_type="refinement.loop.error",
                component="refinement_loop",
                severity="ERROR",
                message=f"Refinement loop failed: {str(e)}",
                metadata={"error": str(e), "iterations_completed": len(iterations)}
            )

            return result

    def _build_feedback_extraction_prompt(
        self,
        report: ValidationReport,
        iteration_num: int
    ) -> str:
        """
        Build prompt for LLM-based feedback extraction (C5).

        Creates a detailed prompt asking the LLM to extract structured,
        actionable feedback from the ValidationReport using the
        refinement_feedback output style.

        Args:
            report: ValidationReport to extract feedback from
            iteration_num: Current iteration number

        Returns:
            Prompt string for LLM
        """
        # Serialize validation report
        report_dict = report.to_dict()

        prompt = f"""# Feedback Extraction Task

You are analyzing a validation report from iteration {iteration_num} of a code refinement loop.
Your task is to extract the most critical, actionable feedback to guide the next iteration.

## Validation Report Summary

**Overall Status:** {report.overall_status}
**Average Score:** {report.average_score:.1f}/100
**Critical Issues:** {report.critical_count}
**High Issues:** {report.high_count}
**Medium Issues:** {report.medium_count}

## Detailed Findings

{self._format_findings_for_prompt(report)}

## Your Task

Extract up to 10 most critical feedback items that will drive code improvement.
Prioritize:
1. All CRITICAL findings (security, correctness)
2. HIGH findings with significant impact
3. MEDIUM findings if space permits

For each feedback item, provide:
- Exact location (file:line)
- Clear description of the issue
- Specific action to fix
- Code snippet showing the fix (when possible)

Also generate a concise regeneration_prompt that summarizes all fixes in priority order.

The output will be used to automatically regenerate the code with improvements.
"""
        return prompt

    def _format_findings_for_prompt(self, report: ValidationReport) -> str:
        """Format validation findings for inclusion in prompt."""
        lines = []

        # Group by category
        for category in ["code", "docs", "tests"]:
            category_report = getattr(report, f"{category}_validation", None)
            if not category_report or not category_report.findings:
                continue

            lines.append(f"\n### {category.upper()} Validation")
            for finding in category_report.findings:
                lines.append(f"\n**{finding.severity}** - {finding.location}")
                lines.append(f"Issue: {finding.issue}")
                lines.append(f"Recommendation: {finding.recommendation}")
                if finding.context:
                    lines.append(f"Context: {finding.context[:200]}...")

        return "\n".join(lines) if lines else "No specific findings available."

    def _extract_feedback(self, report: ValidationReport, iteration_num: int = 1) -> List[str]:
        """
        Extract actionable feedback from validation report.

        C5 Integration: Uses LLM with refinement_feedback output style for structured
        YAML feedback extraction when agent is available. Falls back to manual extraction.

        Args:
            report: ValidationReport to extract feedback from
            iteration_num: Current iteration number

        Returns:
            List of feedback strings (backward compatible)
        """
        # C5: Use structured feedback extraction if agent available
        if self.agent:
            try:
                logger.info("Using LLM-based structured feedback extraction (C5)")

                # Build prompt for feedback extraction
                prompt = self._build_feedback_extraction_prompt(report, iteration_num)

                # Call agent with refinement_feedback output style
                # This enforces Sonnet 4.5, temp=0.2, structured YAML
                structured_result = self.agent.generate_text(
                    prompt=prompt,
                    output_style="refinement_feedback"
                )

                # Store full structured result for later use
                self._last_structured_feedback = structured_result

                # Convert structured feedback to List[str] for backward compatibility
                feedback = []
                if isinstance(structured_result, dict) and "feedback" in structured_result:
                    for item in structured_result.get("feedback", []):
                        priority = item.get("priority", "UNKNOWN")
                        location = item.get("location", "unknown")
                        issue = item.get("issue", "")
                        action = item.get("action", "")
                        feedback.append(f"[{priority}] {location}: {issue} - {action}")

                logger.info(f"Extracted {len(feedback)} structured feedback items")
                return feedback or ["No specific issues found, but quality threshold not met"]

            except Exception as e:
                logger.warning(f"Structured feedback extraction failed: {e}, falling back to manual")
                # Fall through to manual extraction

        # Manual extraction (original logic)
        feedback = []

        # Critical findings first
        critical = report.get_all_critical_findings()
        for finding in critical:
            feedback.append(
                f"[CRITICAL] {finding.location}: {finding.issue} - "
                f"{finding.recommendation}"
            )

        # Then high severity (limit to top 5)
        high_findings = [
            f for f in report.get_all_findings()
            if f.severity == "HIGH"
        ]
        for finding in high_findings[:5]:
            feedback.append(
                f"[HIGH] {finding.location}: {finding.issue} - "
                f"{finding.recommendation}"
            )

        # If no critical/high, include medium (top 3)
        if not feedback:
            medium_findings = [
                f for f in report.get_all_findings()
                if f.severity == "MEDIUM"
            ]
            for finding in medium_findings[:3]:
                feedback.append(
                    f"[MEDIUM] {finding.location}: {finding.issue} - "
                    f"{finding.recommendation}"
                )

        return feedback or ["No specific issues found, but quality threshold not met"]

    def _build_regeneration_prompt(
        self,
        original_input: Dict[str, Any],
        artifact: str,
        validation_report: ValidationReport,
        feedback: List[str]
    ) -> str:
        """
        Build prompt for regenerating artifact based on feedback.

        C5 Integration: Uses pre-built regeneration_prompt from structured feedback
        when available (higher quality, LLM-generated). Falls back to manual construction.

        Returns structured prompt with original intent, validation feedback,
        and specific improvement instructions.
        """
        # C5: Use pre-built prompt from structured feedback if available
        if self._last_structured_feedback and isinstance(self._last_structured_feedback, dict):
            llm_prompt = self._last_structured_feedback.get("regeneration_prompt")
            if llm_prompt and isinstance(llm_prompt, str) and len(llm_prompt.strip()) > 0:
                logger.info("Using LLM-generated regeneration prompt (C5)")

                # Prepend context about original task
                full_prompt = f"""# Regeneration Request

## Original Task
{original_input.get("task", "Generate code based on requirements")}

## LLM-Extracted Feedback and Instructions

{llm_prompt.strip()}

## Additional Context
- Validation Score: {validation_report.average_score:.1f}/100
- Status: {validation_report.overall_status}

Generate the improved version now.
"""
                return full_prompt

        # Manual prompt construction (original logic)
        prompt_parts = [
            "# Regeneration Request",
            "",
            "## Original Task",
            original_input.get("task", "Generate code based on requirements"),
            "",
            "## Previous Attempt Issues",
            f"Validation Score: {validation_report.average_score:.1f}/100",
            f"Status: {validation_report.overall_status}",
            f"Critical Issues: {validation_report.critical_count}",
            f"High Issues: {validation_report.high_count}",
            "",
            "## Required Improvements",
        ]

        for i, feedback_item in enumerate(feedback, 1):
            prompt_parts.append(f"{i}. {feedback_item}")

        prompt_parts.extend([
            "",
            "## Instructions",
            "1. Address ALL critical and high severity issues",
            "2. Maintain the original intent and requirements",
            "3. Apply the recommended fixes exactly as specified",
            "4. Preserve any working functionality from the previous attempt",
            "5. Ensure code quality meets or exceeds threshold",
            "",
            "Generate the improved version now."
        ])

        return "\n".join(prompt_parts)

    def _has_converged(self, report: ValidationReport) -> bool:
        """
        Check if validation meets convergence criteria.

        Convergence occurs when:
        - Status is PASS, OR
        - Status is WARNING and no critical issues (if allow_partial=True), AND
        - Average score meets or exceeds threshold
        """
        score_meets_threshold = report.average_score >= self.min_score_threshold

        if report.overall_status == "PASS":
            return score_meets_threshold

        if self.allow_partial and report.overall_status == "WARNING":
            no_critical = not report.has_critical_issues
            return no_critical and score_meets_threshold

        return False

    def _save_history(self, result: RefinementResult):
        """Save refinement history to disk."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"refinement_{timestamp}.json"
            filepath = self.history_dir / filename

            import json
            with open(filepath, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)

            logger.info(f"Saved refinement history to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save history: {e}", exc_info=True)


# Convenience functions

async def refine_until_valid(
    generator_func: Callable[[Dict[str, Any]], Awaitable[str]],
    validator_func: Callable[[str, Dict[str, Any]], Awaitable[ValidationReport]],
    task: str,
    max_iterations: int = 3,
    **kwargs
) -> RefinementResult:
    """
    Simple wrapper for common use case: refine until validation passes.

    Args:
        generator_func: Generator function
        validator_func: Validator function
        task: Task description
        max_iterations: Max refinement cycles
        **kwargs: Additional context for generator/validator

    Returns:
        RefinementResult
    """
    loop = RefinementLoop(max_iterations=max_iterations)

    return await loop.refine(
        generator_func=generator_func,
        validator_func=validator_func,
        initial_input={"task": task, **kwargs},
        validation_context=kwargs
    )
