#!/usr/bin/env python3
"""
Validation MCP Server - Code Quality Validation via MCP

Exposes Priority 2 validators through MCP tools:
- Code validation (structural checks)
- Documentation validation (docstrings, comments)
- Test validation (test coverage and quality)

Resources:
- Validation thresholds and standards

Usage:
    python3 validation_server.py
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.base_server import BaseMCPServer, ToolParameter
from validation_orchestrator import ValidationOrchestrator
from validation_types import ValidationReport, ValidationResult, ValidationFinding
from observability.event_emitter import EventEmitter

logger = logging.getLogger(__name__)


class ValidationServer(BaseMCPServer):
    """
    MCP server providing code quality validation.

    Tools:
    - validate_code: Code structural validation
    - validate_documentation: Documentation quality validation
    - validate_tests: Test coverage and quality validation

    Resources:
    - validation://thresholds: Quality thresholds and standards
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize validation server.

        Args:
            project_root: Project root directory for context
        """
        super().__init__(
            name="validation",
            version="1.0.0",
            description="Code quality validation via MCP"
        )

        self.project_root = project_root or Path.cwd()

        # Initialize observability
        self.emitter = EventEmitter()

        # Initialize validation orchestrator
        self.validator = ValidationOrchestrator(
            project_root=str(self.project_root)
        )

        # Validation thresholds
        self.thresholds = {
            "code": {
                "min_score": 80,
                "checks": [
                    "Syntax validation",
                    "Import organization",
                    "Unused variables",
                    "Code complexity",
                    "Best practices"
                ]
            },
            "documentation": {
                "min_score": 75,
                "checks": [
                    "Docstring presence",
                    "Docstring quality",
                    "Comment clarity",
                    "README completeness",
                    "API documentation"
                ]
            },
            "tests": {
                "min_score": 85,
                "checks": [
                    "Test coverage (>80%)",
                    "Test quality",
                    "Edge case handling",
                    "Assertion quality",
                    "Test organization"
                ]
            }
        }

        logger.info(f"Initialized ValidationServer with project root: {self.project_root}")

    async def _register_tools(self):
        """Register all validation tools."""

        # Tool 1: Validate Code
        self.create_tool(
            name="validate_code",
            description="Validate code structural quality and best practices. "
                       "Checks syntax, imports, unused variables, complexity, and coding standards. "
                       "Returns score (0-100), pass/fail status, and detailed findings.",
            input_schema={
                "type": "object",
                "properties": {
                    "code": ToolParameter.string(
                        "Source code to validate"
                    ),
                    "language": ToolParameter.string(
                        "Programming language (python, javascript, typescript, etc.)"
                    ),
                    "context": ToolParameter.object(
                        "Optional validation context",
                        properties={
                            "file_path": {"type": "string", "description": "File path for context"},
                            "strict": {"type": "boolean", "description": "Enable strict validation"}
                        }
                    )
                },
                "required": ["code", "language"]
            },
            handler=self._handle_validate_code
        )

        # Tool 2: Validate Documentation
        self.create_tool(
            name="validate_documentation",
            description="Validate documentation quality and completeness. "
                       "Checks docstrings, comments, README, and API documentation. "
                       "Returns score (0-100), pass/fail status, and improvement suggestions.",
            input_schema={
                "type": "object",
                "properties": {
                    "code": ToolParameter.string(
                        "Source code with documentation to validate"
                    ),
                    "language": ToolParameter.string(
                        "Programming language"
                    ),
                    "doc_type": ToolParameter.string(
                        "Documentation type to focus on",
                        enum=["docstrings", "comments", "readme", "all"],
                        default="all"
                    )
                },
                "required": ["code", "language"]
            },
            handler=self._handle_validate_documentation
        )

        # Tool 3: Validate Tests
        self.create_tool(
            name="validate_tests",
            description="Validate test coverage and quality. "
                       "Checks test coverage percentage, test quality, edge cases, and assertions. "
                       "Returns score (0-100), coverage metrics, and quality findings.",
            input_schema={
                "type": "object",
                "properties": {
                    "test_code": ToolParameter.string(
                        "Test code to validate"
                    ),
                    "source_code": ToolParameter.string(
                        "Source code being tested (optional for coverage analysis)"
                    ),
                    "language": ToolParameter.string(
                        "Programming language"
                    )
                },
                "required": ["test_code", "language"]
            },
            handler=self._handle_validate_tests
        )

        # Tool 4: Run Quality Gate (NEW - Phase B)
        self.create_tool(
            name="run_quality_gate",
            description="Run comprehensive quality gate validation across code, docs, and tests. "
                       "Supports validation levels: 'quick' (Haiku, ~2s), 'standard' (Sonnet, ~15s), "
                       "'thorough' (Opus, ~45s). Returns aggregated ValidationReport with overall status, "
                       "findings by severity, and actionable recommendations.",
            input_schema={
                "type": "object",
                "properties": {
                    "target_path": ToolParameter.string(
                        "Path to file or directory to validate"
                    ),
                    "level": ToolParameter.string(
                        "Validation level (quick, standard, thorough)",
                        enum=["quick", "standard", "thorough"],
                        default="standard"
                    ),
                    "validators": ToolParameter.array(
                        "List of validators to run (default: all)",
                        items={"type": "string", "enum": ["code", "documentation", "tests"]},
                        default=["code", "documentation", "tests"]
                    ),
                    "context": ToolParameter.object(
                        "Additional validation context",
                        properties={
                            "language": {"type": "string", "description": "Programming language"},
                            "strict": {"type": "boolean", "description": "Enable strict mode"}
                        }
                    )
                },
                "required": ["target_path"]
            },
            handler=self._handle_run_quality_gate
        )

    async def _register_resources(self):
        """Register all validation resources."""

        # Resource 1: Validation Thresholds
        self.create_resource(
            uri="validation://thresholds",
            name="Validation Thresholds",
            description="Current quality thresholds and validation standards for each category",
            handler=self._handle_thresholds
        )

    # ==================== TOOL HANDLERS ====================

    async def _handle_validate_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle code validation.

        Validates code structure, quality, and best practices.
        """
        try:
            # Emit start event
            self.emitter.emit(
                event_type="validation.code.start",
                component="validation_server",
                message=f"Starting code validation for {language}",
                metadata={"language": language, "code_length": len(code)}
            )

            logger.info(f"Validating {language} code ({len(code)} chars)")

            # Prepare context
            validation_context = {
                "validation_type": "code",
                "language": language
            }

            if context:
                validation_context.update(context)

            # Run code validation
            result = await self.validator.validate_code(
                code=code,
                language=language,
                context=validation_context
            )

            # Extract code validation results
            code_result = result.get("code", {})

            # Format response
            response = {
                "success": True,
                "score": code_result.get("score", 0),
                "passed": code_result.get("passed", False),
                "threshold": self.thresholds["code"]["min_score"],
                "findings": code_result.get("findings", []),
                "summary": {
                    "total_checks": len(self.thresholds["code"]["checks"]),
                    "passed_checks": sum(1 for f in code_result.get("findings", []) if f.get("severity") != "error"),
                    "issues_found": len(code_result.get("findings", []))
                },
                "recommendations": self._generate_code_recommendations(code_result)
            }

            logger.info(f"Code validation complete: score={response['score']}, passed={response['passed']}")

            # Emit completion event
            self.emitter.emit(
                event_type="validation.code.complete",
                component="validation_server",
                severity="INFO" if response['passed'] else "WARNING",
                message=f"Code validation {'passed' if response['passed'] else 'failed'}",
                metadata={
                    "language": language,
                    "score": response['score'],
                    "passed": response['passed'],
                    "issues_found": response['summary']['issues_found']
                }
            )

            return self.format_success(
                response,
                f"Code validation {'passed' if response['passed'] else 'failed'} (score: {response['score']}/100)"
            )

        except Exception as e:
            # Emit error event
            self.emitter.emit(
                event_type="validation.code.error",
                component="validation_server",
                severity="ERROR",
                message=f"Code validation failed: {str(e)}",
                metadata={"language": language, "error": str(e)}
            )

            logger.error(f"Code validation failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_validate_documentation(
        self,
        code: str,
        language: str,
        doc_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Handle documentation validation.

        Validates documentation quality and completeness.
        """
        try:
            logger.info(f"Validating {language} documentation (type: {doc_type})")

            # Run documentation validation (C5: Uses critic_judge output style)
            result = await self.validator.validate_documentation(
                code=code,
                language=language,
                context={"doc_type": doc_type}
            )

            # Extract documentation validation results
            doc_result = result.get("documentation", {})

            # Format response
            response = {
                "success": True,
                "score": doc_result.get("score", 0),
                "passed": doc_result.get("passed", False),
                "threshold": self.thresholds["documentation"]["min_score"],
                "doc_type": doc_type,
                "findings": doc_result.get("findings", []),
                "coverage": {
                    "docstrings": self._count_docstrings(code, language),
                    "comments": self._count_comments(code, language),
                    "total_functions": self._count_functions(code, language)
                },
                "recommendations": self._generate_doc_recommendations(doc_result, doc_type)
            }

            logger.info(f"Documentation validation complete: score={response['score']}")

            return self.format_success(
                response,
                f"Documentation validation {'passed' if response['passed'] else 'failed'} (score: {response['score']}/100)"
            )

        except Exception as e:
            logger.error(f"Documentation validation failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_validate_tests(
        self,
        test_code: str,
        language: str,
        source_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle test validation.

        Validates test coverage and quality.
        """
        try:
            logger.info(f"Validating {language} tests ({len(test_code)} chars)")

            # Run test validation (C5: Uses critic_judge output style)
            result = await self.validator.validate_tests(
                test_code=test_code,
                source_code=source_code,
                language=language,
                context={}
            )

            # Extract test validation results
            test_result = result.get("tests", {})

            # Calculate coverage if source code provided
            coverage_pct = None
            if source_code:
                coverage_pct = self._estimate_coverage(test_code, source_code, language)

            # Format response
            response = {
                "success": True,
                "score": test_result.get("score", 0),
                "passed": test_result.get("passed", False),
                "threshold": self.thresholds["tests"]["min_score"],
                "findings": test_result.get("findings", []),
                "metrics": {
                    "test_count": self._count_tests(test_code, language),
                    "assertion_count": self._count_assertions(test_code, language),
                    "coverage_percent": coverage_pct
                },
                "quality_indicators": {
                    "has_setup_teardown": self._has_setup_teardown(test_code, language),
                    "tests_edge_cases": self._tests_edge_cases(test_code),
                    "uses_mocks": self._uses_mocks(test_code, language)
                },
                "recommendations": self._generate_test_recommendations(test_result, coverage_pct)
            }

            logger.info(f"Test validation complete: score={response['score']}")

            return self.format_success(
                response,
                f"Test validation {'passed' if response['passed'] else 'failed'} (score: {response['score']}/100)"
            )

        except Exception as e:
            logger.error(f"Test validation failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_run_quality_gate(
        self,
        target_path: str,
        level: str = "standard",
        validators: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle comprehensive quality gate validation.

        Runs all specified validators and returns aggregated ValidationReport.
        """
        import time

        try:
            start_time = time.time()

            # Emit start event
            self.emitter.emit(
                event_type="validation.quality_gate.start",
                component="validation_server",
                message=f"Starting quality gate validation (level: {level})",
                metadata={
                    "target_path": target_path,
                    "level": level,
                    "validators": validators or ["code", "documentation", "tests"]
                }
            )

            logger.info(f"Running quality gate on {target_path} (level: {level})")

            # Default to all validators
            validators = validators or ["code", "documentation", "tests"]

            # Read target file/directory
            target = Path(target_path)
            if not target.exists():
                raise FileNotFoundError(f"Target path not found: {target_path}")

            # Run all validators through ValidationOrchestrator
            report = await self.validator.run_all_validators(
                target_path=str(target),
                level=level,
                context=context or {}
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Emit completion event
            self.emitter.emit(
                event_type="validation.quality_gate.complete",
                component="validation_server",
                severity="INFO" if report.passed else "WARNING",
                message=f"Quality gate {'passed' if report.passed else 'failed'}",
                metadata={
                    "target_path": target_path,
                    "level": level,
                    "overall_status": report.overall_status,
                    "average_score": report.average_score,
                    "critical_findings": report.critical_count,
                    "high_findings": report.high_count,
                    "total_cost_usd": report.total_cost_usd,
                    "execution_time_ms": execution_time_ms
                }
            )

            logger.info(
                f"Quality gate complete: {report.overall_status} "
                f"(avg score: {report.average_score:.1f}, "
                f"critical: {report.critical_count}, "
                f"high: {report.high_count})"
            )

            # Format response with ValidationReport
            response = {
                "success": True,
                "report": report.to_dict(),
                "passed": report.passed,
                "overall_status": report.overall_status,
                "average_score": report.average_score,
                "total_findings": report.total_findings,
                "critical_findings": report.get_all_critical_findings(),
                "actionable_fixes": [f.to_dict() for f in report.get_actionable_fixes()],
                "recommendations": report.recommendations[:10],  # Top 10
                "execution_time_ms": execution_time_ms,
                "total_cost_usd": report.total_cost_usd
            }

            return self.format_success(
                response,
                f"Quality gate {'✅ PASSED' if report.passed else '❌ FAILED'} - "
                f"Score: {report.average_score:.1f}/100, "
                f"Critical: {report.critical_count}, High: {report.high_count}"
            )

        except Exception as e:
            # Emit error event
            self.emitter.emit(
                event_type="validation.quality_gate.error",
                component="validation_server",
                severity="ERROR",
                message=f"Quality gate failed: {str(e)}",
                metadata={"target_path": target_path, "level": level, "error": str(e)}
            )

            logger.error(f"Quality gate failed: {e}", exc_info=True)
            return self.format_error(e)

    # ==================== RESOURCE HANDLERS ====================

    async def _handle_thresholds(self) -> Dict[str, Any]:
        """Provide validation thresholds."""
        return {
            "thresholds": self.thresholds,
            "description": "Minimum scores and validation checks for each category"
        }

    # ==================== HELPER METHODS ====================

    def _generate_code_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate code validation recommendations."""
        recommendations = []

        findings = result.get("findings", [])
        errors = [f for f in findings if f.get("severity") == "error"]
        warnings = [f for f in findings if f.get("severity") == "warning"]

        if errors:
            recommendations.append(f"Fix {len(errors)} critical code issues")

        if warnings:
            recommendations.append(f"Address {len(warnings)} code warnings")

        if result.get("score", 0) < self.thresholds["code"]["min_score"]:
            recommendations.append("Refactor code to meet quality standards")

        if not recommendations:
            recommendations.append("Code quality is good, maintain current standards")

        return recommendations

    def _generate_doc_recommendations(self, result: Dict[str, Any], doc_type: str) -> List[str]:
        """Generate documentation recommendations."""
        recommendations = []

        findings = result.get("findings", [])
        missing_docs = [f for f in findings if "missing" in f.get("message", "").lower()]

        if missing_docs:
            recommendations.append(f"Add documentation for {len(missing_docs)} items")

        if doc_type in ["docstrings", "all"]:
            recommendations.append("Ensure all public functions have docstrings")

        if doc_type in ["comments", "all"]:
            recommendations.append("Add inline comments for complex logic")

        if result.get("score", 0) < self.thresholds["documentation"]["min_score"]:
            recommendations.append("Improve documentation completeness and clarity")

        if not recommendations:
            recommendations.append("Documentation is adequate")

        return recommendations

    def _generate_test_recommendations(
        self,
        result: Dict[str, Any],
        coverage_pct: Optional[float]
    ) -> List[str]:
        """Generate test validation recommendations."""
        recommendations = []

        if coverage_pct is not None and coverage_pct < 80:
            recommendations.append(f"Increase test coverage from {coverage_pct:.1f}% to >80%")

        findings = result.get("findings", [])
        if findings:
            recommendations.append(f"Address {len(findings)} test quality issues")

        if result.get("score", 0) < self.thresholds["tests"]["min_score"]:
            recommendations.append("Add more comprehensive test cases")
            recommendations.append("Include edge case and error handling tests")

        if not recommendations:
            recommendations.append("Test quality and coverage are good")

        return recommendations

    # Code analysis helpers

    def _count_docstrings(self, code: str, language: str) -> int:
        """Count docstrings in code."""
        if language == "python":
            import re
            # Simple heuristic: triple-quoted strings
            return len(re.findall(r'""".*?"""|\'\'\'.*?\'\'\'', code, re.DOTALL))
        return 0

    def _count_comments(self, code: str, language: str) -> int:
        """Count comments in code."""
        import re
        if language == "python":
            return len(re.findall(r'#.*$', code, re.MULTILINE))
        elif language in ["javascript", "typescript", "java", "c", "cpp"]:
            return len(re.findall(r'//.*$|/\*.*?\*/', code, re.MULTILINE | re.DOTALL))
        return 0

    def _count_functions(self, code: str, language: str) -> int:
        """Count functions in code."""
        import re
        if language == "python":
            return len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
        elif language in ["javascript", "typescript"]:
            return len(re.findall(r'function\s+\w+|const\s+\w+\s*=\s*\(.*?\)\s*=>', code))
        return 0

    def _count_tests(self, test_code: str, language: str) -> int:
        """Count test cases."""
        import re
        if language == "python":
            # pytest and unittest patterns
            return len(re.findall(r'^\s*def\s+test_\w+', test_code, re.MULTILINE))
        elif language in ["javascript", "typescript"]:
            # Jest/Mocha patterns
            return len(re.findall(r'it\s*\(|test\s*\(', test_code))
        return 0

    def _count_assertions(self, test_code: str, language: str) -> int:
        """Count assertions in tests."""
        import re
        if language == "python":
            return len(re.findall(r'assert\s+|self\.assert', test_code))
        elif language in ["javascript", "typescript"]:
            return len(re.findall(r'expect\s*\(|assert\s*\(', test_code))
        return 0

    def _estimate_coverage(self, test_code: str, source_code: str, language: str) -> float:
        """Estimate test coverage percentage (rough heuristic)."""
        source_functions = self._count_functions(source_code, language)
        test_count = self._count_tests(test_code, language)

        if source_functions == 0:
            return 0.0

        # Simple heuristic: assume each test covers 1-2 functions
        estimated_coverage = min(100.0, (test_count * 1.5 / source_functions) * 100)
        return round(estimated_coverage, 1)

    def _has_setup_teardown(self, test_code: str, language: str) -> bool:
        """Check if tests have setup/teardown."""
        import re
        if language == "python":
            return bool(re.search(r'setUp|tearDown|@pytest\.fixture', test_code))
        elif language in ["javascript", "typescript"]:
            return bool(re.search(r'beforeEach|afterEach|beforeAll|afterAll', test_code))
        return False

    def _tests_edge_cases(self, test_code: str) -> bool:
        """Check if tests cover edge cases."""
        edge_keywords = ["edge", "boundary", "limit", "empty", "null", "zero", "max", "min"]
        return any(keyword in test_code.lower() for keyword in edge_keywords)

    def _uses_mocks(self, test_code: str, language: str) -> bool:
        """Check if tests use mocking."""
        mock_keywords = ["mock", "stub", "spy", "patch"]
        return any(keyword in test_code.lower() for keyword in mock_keywords)


async def main():
    """Main entry point for validation server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validation MCP Server - Code quality validation via MCP"
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
    server = ValidationServer(project_root=project_root)

    await server.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
