#!/usr/bin/env python3
"""
Code Review MCP Server - Complete Code Review via MCP

Exposes comprehensive code review workflow through MCP tools:
- Complete multi-phase review (architect → developer → tester → reviewer)
- Quick validation for fast feedback
- Targeted validation by type
- Actionable recommendations

Resources:
- Review history
- Review statistics and trends

Usage:
    python3 code_review_server.py --project-root /path/to/project
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.base_server import BaseMCPServer, ToolParameter
from specialized_roles_orchestrator import SpecializedRolesOrchestrator
from validation_orchestrator import ValidationOrchestrator

logger = logging.getLogger(__name__)


class CodeReviewServer(BaseMCPServer):
    """
    MCP server providing complete code review capabilities.

    Tools:
    - review_code: Complete 4-phase review with validation
    - quick_review: Fast validation-only review
    - validate_code: Targeted validation by type
    - get_recommendations: Actionable improvement suggestions

    Resources:
    - review://history: Past code reviews
    - review://stats: Review statistics and trends
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize code review server.

        Args:
            project_root: Project root directory for context
        """
        super().__init__(
            name="code-review",
            version="1.0.0",
            description="Complete code review workflow via MCP"
        )

        self.project_root = project_root or Path.cwd()

        # Initialize orchestrators
        self.specialized_orchestrator = SpecializedRolesOrchestrator(
            project_root=str(self.project_root)
        )

        self.validation_orchestrator = ValidationOrchestrator(
            project_root=str(self.project_root)
        )

        # Review history storage
        self.review_history: List[Dict[str, Any]] = []
        self.review_stats = {
            "total_reviews": 0,
            "avg_quality_score": 0.0,
            "common_issues": {},
            "by_language": {}
        }

        logger.info(f"Initialized CodeReviewServer with project root: {self.project_root}")

    async def _register_tools(self):
        """Register all code review tools."""

        # Tool 1: Complete Review
        self.create_tool(
            name="review_code",
            description="Complete multi-phase code review with quality validation. "
                       "Runs 4-phase workflow (architect → developer → tester → reviewer) "
                       "followed by comprehensive validation. Returns detailed review with "
                       "quality score, findings, and recommendations. Time: 5-8 minutes.",
            input_schema={
                "type": "object",
                "properties": {
                    "code": ToolParameter.string(
                        "Source code to review (full content)"
                    ),
                    "language": ToolParameter.string(
                        "Programming language (python, javascript, typescript, etc.)"
                    ),
                    "context": ToolParameter.object(
                        "Optional context about the code",
                        properties={
                            "purpose": {"type": "string", "description": "What this code does"},
                            "requirements": {"type": "string", "description": "Requirements it should meet"},
                            "concerns": {"type": "string", "description": "Specific concerns to address"}
                        }
                    ),
                    "quality_threshold": ToolParameter.integer(
                        "Minimum quality score required (0-100)",
                        default=90,
                        minimum=0,
                        maximum=100
                    )
                },
                "required": ["code", "language"]
            },
            handler=self._handle_review_code
        )

        # Tool 2: Quick Review
        self.create_tool(
            name="quick_review",
            description="Fast validation-only review for immediate feedback. "
                       "Runs structural and quality validators without full multi-phase review. "
                       "Returns quality score and key findings. Time: 10-30 seconds.",
            input_schema={
                "type": "object",
                "properties": {
                    "code": ToolParameter.string(
                        "Source code to validate"
                    ),
                    "language": ToolParameter.string(
                        "Programming language"
                    )
                },
                "required": ["code", "language"]
            },
            handler=self._handle_quick_review
        )

        # Tool 3: Validate Code
        self.create_tool(
            name="validate_code",
            description="Targeted validation by type (code, documentation, or tests). "
                       "Focuses on specific validation concerns. Returns pass/fail with "
                       "detailed findings for the selected validation type.",
            input_schema={
                "type": "object",
                "properties": {
                    "code": ToolParameter.string(
                        "Source code to validate"
                    ),
                    "language": ToolParameter.string(
                        "Programming language"
                    ),
                    "validation_type": ToolParameter.string(
                        "Type of validation to perform",
                        enum=["code", "documentation", "tests", "all"],
                        default="all"
                    )
                },
                "required": ["code", "language"]
            },
            handler=self._handle_validate_code
        )

        # Tool 4: Get Recommendations
        self.create_tool(
            name="get_recommendations",
            description="Generate actionable improvement recommendations for code. "
                       "Analyzes code and provides prioritized list of improvements with "
                       "rationale and implementation guidance. Can focus on specific areas.",
            input_schema={
                "type": "object",
                "properties": {
                    "code": ToolParameter.string(
                        "Source code to analyze"
                    ),
                    "language": ToolParameter.string(
                        "Programming language"
                    ),
                    "focus_area": ToolParameter.string(
                        "Optional focus area (security, performance, maintainability, testing)",
                        enum=["security", "performance", "maintainability", "testing", "all"],
                        default="all"
                    )
                },
                "required": ["code", "language"]
            },
            handler=self._handle_get_recommendations
        )

    async def _register_resources(self):
        """Register all code review resources."""

        # Resource 1: Review History
        self.create_resource(
            uri="review://history",
            name="Review History",
            description="List of all past code reviews with timestamps and results",
            handler=self._handle_review_history
        )

        # Resource 2: Review Statistics
        self.create_resource(
            uri="review://stats",
            name="Review Statistics",
            description="Aggregate statistics: average quality, common issues, trends",
            handler=self._handle_review_stats
        )

    # ==================== TOOL HANDLERS ====================

    async def _handle_review_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        quality_threshold: int = 90
    ) -> Dict[str, Any]:
        """
        Handle complete code review.

        Runs:
        1. Specialized roles workflow (4 phases)
        2. Comprehensive validation
        3. Quality scoring
        """
        try:
            logger.info(f"Starting complete review for {language} code ({len(code)} chars)")

            # Prepare task
            task = f"Review this {language} code:\n\n{code}"
            if context:
                if context.get("purpose"):
                    task += f"\n\nPurpose: {context['purpose']}"
                if context.get("requirements"):
                    task += f"\nRequirements: {context['requirements']}"
                if context.get("concerns"):
                    task += f"\nConcerns: {context['concerns']}"

            # Run specialized roles workflow
            logger.info("Running 4-phase specialized roles workflow...")
            workflow_result = await self.specialized_orchestrator.execute_workflow(task)

            # Extract phase results
            phase_results = {
                "architect": workflow_result.phases.get("architect", {}).get("output", "N/A"),
                "developer": workflow_result.phases.get("developer", {}).get("output", "N/A"),
                "tester": workflow_result.phases.get("tester", {}).get("output", "N/A"),
                "reviewer": workflow_result.phases.get("reviewer", {}).get("output", "N/A")
            }

            # Run validation
            logger.info("Running comprehensive validation...")
            validation_result = await self.validation_orchestrator.validate_code(
                code=code,
                language=language,
                context={"workflow_review": phase_results}
            )

            # Calculate overall quality score
            quality_score = self._calculate_quality_score(validation_result)

            # Determine pass/fail
            passed = quality_score >= quality_threshold

            # Extract key findings
            findings = self._extract_findings(validation_result, phase_results)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                findings,
                phase_results,
                quality_score
            )

            # Store in history
            review_record = {
                "timestamp": datetime.now().isoformat(),
                "language": language,
                "code_length": len(code),
                "quality_score": quality_score,
                "passed": passed,
                "threshold": quality_threshold,
                "findings_count": len(findings)
            }
            self.review_history.append(review_record)
            self._update_stats(review_record, findings, language)

            result = {
                "success": True,
                "quality_score": quality_score,
                "passed": passed,
                "threshold": quality_threshold,
                "execution_time": workflow_result.total_time_seconds,
                "total_cost": workflow_result.total_cost,
                "phases": phase_results,
                "validation": {
                    "code": validation_result.get("code", {}),
                    "documentation": validation_result.get("documentation", {}),
                    "tests": validation_result.get("tests", {})
                },
                "findings": findings,
                "recommendations": recommendations
            }

            logger.info(f"Review complete: quality={quality_score}, passed={passed}")

            return self.format_success(result, f"Review complete with quality score: {quality_score}")

        except Exception as e:
            logger.error(f"Review failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_quick_review(
        self,
        code: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Handle quick validation-only review.

        Fast path: validators only, no multi-phase workflow.
        """
        try:
            logger.info(f"Starting quick review for {language} code ({len(code)} chars)")

            # Run validators only
            validation_result = await self.validation_orchestrator.validate_code(
                code=code,
                language=language
            )

            # Calculate quality score
            quality_score = self._calculate_quality_score(validation_result)

            # Extract key findings
            findings = []
            for validator_type, result in validation_result.items():
                if result.get("findings"):
                    findings.extend(result["findings"])

            result = {
                "success": True,
                "quality_score": quality_score,
                "validation": validation_result,
                "findings": findings[:10],  # Top 10 findings
                "findings_count": len(findings)
            }

            logger.info(f"Quick review complete: quality={quality_score}")

            return self.format_success(result, f"Quick review complete: {quality_score}/100")

        except Exception as e:
            logger.error(f"Quick review failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_validate_code(
        self,
        code: str,
        language: str,
        validation_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Handle targeted validation.

        Focuses on specific validation type.
        """
        try:
            logger.info(f"Starting validation ({validation_type}) for {language} code")

            # Run validation
            validation_result = await self.validation_orchestrator.validate_code(
                code=code,
                language=language
            )

            # Filter by validation type
            if validation_type != "all":
                validation_result = {
                    validation_type: validation_result.get(validation_type, {})
                }

            # Extract results
            passed = all(
                result.get("passed", False)
                for result in validation_result.values()
            )

            findings = []
            for result in validation_result.values():
                if result.get("findings"):
                    findings.extend(result["findings"])

            result = {
                "success": True,
                "passed": passed,
                "validation_type": validation_type,
                "validation": validation_result,
                "findings": findings,
                "findings_count": len(findings)
            }

            logger.info(f"Validation complete: passed={passed}")

            return self.format_success(result, f"Validation {'passed' if passed else 'failed'}")

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_get_recommendations(
        self,
        code: str,
        language: str,
        focus_area: str = "all"
    ) -> Dict[str, Any]:
        """
        Handle recommendation generation.

        Analyzes code and provides actionable recommendations.
        """
        try:
            logger.info(f"Generating recommendations ({focus_area}) for {language} code")

            # Run validation to get findings
            validation_result = await self.validation_orchestrator.validate_code(
                code=code,
                language=language
            )

            # Extract findings
            all_findings = []
            for result in validation_result.values():
                if result.get("findings"):
                    all_findings.extend(result["findings"])

            # Generate recommendations based on findings
            recommendations = self._generate_detailed_recommendations(
                all_findings,
                focus_area,
                language
            )

            result = {
                "success": True,
                "focus_area": focus_area,
                "recommendations": recommendations,
                "recommendation_count": len(recommendations),
                "priority_breakdown": {
                    "high": len([r for r in recommendations if r["priority"] == "high"]),
                    "medium": len([r for r in recommendations if r["priority"] == "medium"]),
                    "low": len([r for r in recommendations if r["priority"] == "low"])
                }
            }

            logger.info(f"Generated {len(recommendations)} recommendations")

            return self.format_success(result, f"Generated {len(recommendations)} recommendations")

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}", exc_info=True)
            return self.format_error(e)

    # ==================== RESOURCE HANDLERS ====================

    async def _handle_review_history(self) -> Dict[str, Any]:
        """Provide review history."""
        return {
            "reviews": self.review_history[-50:],  # Last 50 reviews
            "total_count": len(self.review_history)
        }

    async def _handle_review_stats(self) -> Dict[str, Any]:
        """Provide review statistics."""
        return self.review_stats

    # ==================== HELPER METHODS ====================

    def _calculate_quality_score(self, validation_result: Dict[str, Any]) -> int:
        """Calculate overall quality score from validation results."""
        scores = []

        for validator_type, result in validation_result.items():
            if "score" in result:
                scores.append(result["score"])

        if not scores:
            return 0

        return int(sum(scores) / len(scores))

    def _extract_findings(
        self,
        validation_result: Dict[str, Any],
        phase_results: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Extract all findings from validation and phases."""
        findings = []

        # From validation
        for validator_type, result in validation_result.items():
            if result.get("findings"):
                for finding in result["findings"]:
                    findings.append({
                        "source": f"validation:{validator_type}",
                        "severity": finding.get("severity", "info"),
                        "message": finding.get("message", ""),
                        "line": finding.get("line")
                    })

        # From phase reviews (extract key points)
        for phase, output in phase_results.items():
            if "issue" in output.lower() or "concern" in output.lower():
                findings.append({
                    "source": f"review:{phase}",
                    "severity": "info",
                    "message": f"{phase.capitalize()} noted concerns - see phase output"
                })

        return findings

    def _generate_recommendations(
        self,
        findings: List[Dict[str, Any]],
        phase_results: Dict[str, str],
        quality_score: int
    ) -> List[str]:
        """Generate high-level recommendations."""
        recommendations = []

        # Based on quality score
        if quality_score < 70:
            recommendations.append("Significant improvements needed - consider refactoring")
        elif quality_score < 85:
            recommendations.append("Good foundation, focus on addressing specific findings")
        else:
            recommendations.append("Code quality is good, minor refinements suggested")

        # Based on findings
        high_severity = [f for f in findings if f.get("severity") == "error"]
        if high_severity:
            recommendations.append(f"Address {len(high_severity)} critical issues first")

        # From phases
        if "test" in phase_results.get("tester", "").lower() and "missing" in phase_results.get("tester", "").lower():
            recommendations.append("Add comprehensive test coverage")

        if "documentation" in phase_results.get("reviewer", "").lower() and "missing" in phase_results.get("reviewer", "").lower():
            recommendations.append("Improve code documentation")

        return recommendations

    def _generate_detailed_recommendations(
        self,
        findings: List[Dict[str, Any]],
        focus_area: str,
        language: str
    ) -> List[Dict[str, Any]]:
        """Generate detailed actionable recommendations."""
        recommendations = []

        # Group findings by type
        finding_types = {}
        for finding in findings:
            msg = finding.get("message", "")
            finding_type = self._categorize_finding(msg)

            if finding_type not in finding_types:
                finding_types[finding_type] = []
            finding_types[finding_type].append(finding)

        # Generate recommendations per type
        for finding_type, type_findings in finding_types.items():
            # Filter by focus area if specified
            if focus_area != "all" and not self._matches_focus(finding_type, focus_area):
                continue

            priority = self._determine_priority(finding_type, len(type_findings))

            recommendations.append({
                "title": f"Address {finding_type} issues",
                "priority": priority,
                "issue_count": len(type_findings),
                "description": f"Found {len(type_findings)} {finding_type}-related issues",
                "action": self._get_action_for_type(finding_type, language),
                "examples": [f["message"] for f in type_findings[:3]]
            })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order[r["priority"]])

        return recommendations

    def _categorize_finding(self, message: str) -> str:
        """Categorize finding by message content."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["error", "exception", "fail"]):
            return "errors"
        elif any(word in message_lower for word in ["security", "vulnerability", "injection"]):
            return "security"
        elif any(word in message_lower for word in ["performance", "slow", "inefficient"]):
            return "performance"
        elif any(word in message_lower for word in ["test", "coverage"]):
            return "testing"
        elif any(word in message_lower for word in ["documentation", "docstring", "comment"]):
            return "documentation"
        else:
            return "code quality"

    def _matches_focus(self, finding_type: str, focus_area: str) -> bool:
        """Check if finding type matches focus area."""
        focus_map = {
            "security": ["security"],
            "performance": ["performance"],
            "maintainability": ["code quality", "documentation"],
            "testing": ["testing", "errors"]
        }

        return finding_type in focus_map.get(focus_area, [])

    def _determine_priority(self, finding_type: str, count: int) -> str:
        """Determine priority based on finding type and count."""
        if finding_type in ["errors", "security"]:
            return "high"
        elif finding_type in ["performance", "testing"]:
            return "medium" if count > 3 else "low"
        else:
            return "low"

    def _get_action_for_type(self, finding_type: str, language: str) -> str:
        """Get recommended action for finding type."""
        actions = {
            "errors": f"Fix all error-level issues in the {language} code",
            "security": f"Address security vulnerabilities using {language} best practices",
            "performance": f"Optimize performance bottlenecks in {language}",
            "testing": f"Add comprehensive unit tests using {language} testing framework",
            "documentation": f"Add docstrings and comments following {language} conventions",
            "code quality": f"Refactor code following {language} best practices"
        }

        return actions.get(finding_type, "Review and address the issues")

    def _update_stats(
        self,
        review_record: Dict[str, Any],
        findings: List[Dict[str, Any]],
        language: str
    ):
        """Update review statistics."""
        self.review_stats["total_reviews"] += 1

        # Update average quality
        total_quality = self.review_stats["avg_quality_score"] * (self.review_stats["total_reviews"] - 1)
        total_quality += review_record["quality_score"]
        self.review_stats["avg_quality_score"] = total_quality / self.review_stats["total_reviews"]

        # Update common issues
        for finding in findings:
            issue_type = self._categorize_finding(finding.get("message", ""))
            self.review_stats["common_issues"][issue_type] = \
                self.review_stats["common_issues"].get(issue_type, 0) + 1

        # Update by language
        if language not in self.review_stats["by_language"]:
            self.review_stats["by_language"][language] = {
                "count": 0,
                "avg_quality": 0.0
            }

        lang_stats = self.review_stats["by_language"][language]
        lang_stats["count"] += 1
        total_lang_quality = lang_stats["avg_quality"] * (lang_stats["count"] - 1)
        total_lang_quality += review_record["quality_score"]
        lang_stats["avg_quality"] = total_lang_quality / lang_stats["count"]


async def main():
    """Main entry point for code review server."""
    parser = argparse.ArgumentParser(
        description="Code Review MCP Server - Complete code review via MCP"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()

    # Create and run server
    project_root = Path(args.project_root) if args.project_root else None
    server = CodeReviewServer(project_root=project_root)

    await server.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
