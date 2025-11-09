"""
Validation Result Aggregator - Result Processing and Report Generation

This module handles aggregation of validation results and report generation.

Architecture:
    - Orchestrates multiple validators across files/directories
    - Aggregates results into comprehensive reports
    - Generates reports in multiple formats (markdown, JSON, text)

Usage:
    from validation.result_aggregator import ResultAggregator

    aggregator = ResultAggregator(orchestrator)
    report = aggregator.run_all_validators("src/", level="standard")
    markdown = aggregator.generate_report(report, format="markdown")
"""

from pathlib import Path
from typing import List, Dict, Optional, Literal
import time

from validation.interfaces import (
    ValidationResult,
    ValidationReport,
    ValidationFinding,
    ValidationLevel,
    EXCLUDE_PATTERNS
)


class ResultAggregator:
    """
    Aggregates validation results and generates reports.

    Coordinates running multiple validators across files and directories,
    then aggregates results into comprehensive reports.
    """

    def __init__(self, orchestrator):
        """
        Initialize ResultAggregator.

        Args:
            orchestrator: ValidationOrchestrator instance
        """
        self.orchestrator = orchestrator

    def run_all_validators(
        self,
        target_path: str,
        level: Optional[ValidationLevel] = None,
        recursive: bool = True,
        validators: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        Run all appropriate validators on a file or directory.

        Automatically detects file types and runs the appropriate validators:
        - .py/.js/.ts/etc → code-validator
        - .md/README/GUIDE → doc-validator
        - test_*.py/*_test.py → test-validator + code-validator

        Args:
            target_path: Path to file or directory to validate
            level: Validation level (defaults to orchestrator.default_level)
            recursive: If target is directory, recurse into subdirs
            validators: Override which validators to run

        Returns:
            ValidationReport aggregating all validation results

        Raises:
            FileNotFoundError: If target path not found
        """
        level = level or self.orchestrator.default_level
        target = Path(target_path)

        if not target.exists():
            raise FileNotFoundError(f"Target path not found: {target_path}")

        # Collect all validation results
        all_results: List[ValidationResult] = []
        start_time = time.time()

        if target.is_file():
            # Validate single file
            results = self._validate_single_file(
                file_path=target,
                level=level,
                validators=validators
            )
            all_results.extend(results)

        elif target.is_dir():
            # Validate directory
            results = self._validate_directory(
                directory=target,
                level=level,
                recursive=recursive,
                validators=validators
            )
            all_results.extend(results)

        else:
            raise ValueError(f"Invalid target: {target_path}")

        # Calculate execution time
        total_time_ms = int((time.time() - start_time) * 1000)

        # Aggregate results into report
        report = ValidationReport.from_results(
            results=all_results,
            total_time_ms=total_time_ms
        )

        return report

    def _validate_single_file(
        self,
        file_path: Path,
        level: str,
        validators: Optional[List[str]] = None
    ) -> List[ValidationResult]:
        """
        Validate a single file with appropriate validators.

        Args:
            file_path: Path to file
            level: Validation level
            validators: Override which validators to run

        Returns:
            List of ValidationResult objects (one per validator run)
        """
        results = []

        # Auto-detect which validators to use
        if validators is None:
            validators = self.orchestrator._detect_validators_for_file(file_path)

        if not validators:
            # No validators applicable for this file
            return results

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            # Can't read file, create FAIL result
            from validation_types import create_fail_result
            results.append(create_fail_result(
                validator_name="file-read",
                findings=[ValidationFinding(
                    id="ERR-READ",
                    severity="CRITICAL",
                    category="error",
                    subcategory="file_read",
                    location=str(file_path),
                    issue=f"Failed to read file: {e}",
                    recommendation="Check file permissions and encoding"
                )],
                model_used="none"
            ))
            return results

        # Prepare context
        context = {
            "file_path": str(file_path),
            "language": self.orchestrator._detect_language(file_path),
        }

        # Run each validator
        for validator_name in validators:
            if validator_name == "code-validator":
                result = self.orchestrator.validate_code(
                    code=content,
                    context=context,
                    level=level
                )
                results.append(result)

            elif validator_name == "doc-validator":
                context["doc_type"] = "README" if "README" in file_path.name else "GENERAL"
                result = self.orchestrator.validate_documentation(
                    documentation=content,
                    context=context,
                    level=level
                )
                results.append(result)

            elif validator_name == "test-validator":
                # For test files, try to find source code
                source_code = self.orchestrator._find_source_for_test(file_path)
                context["module_name"] = file_path.stem.replace("test_", "").replace("_test", "")

                result = self.orchestrator.validate_tests(
                    test_code=content,
                    source_code=source_code,
                    context=context,
                    level=level
                )
                results.append(result)

        return results

    def _validate_directory(
        self,
        directory: Path,
        level: str,
        recursive: bool,
        validators: Optional[List[str]] = None
    ) -> List[ValidationResult]:
        """
        Validate all files in a directory.

        Args:
            directory: Directory to validate
            level: Validation level
            recursive: Recurse into subdirectories
            validators: Override which validators to run

        Returns:
            List of all ValidationResult objects
        """
        all_results = []

        # Get all files
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")

        # Filter to only files (not directories)
        files = [f for f in files if f.is_file()]

        # Exclude common non-source files
        filtered_files = []
        for file_path in files:
            # Check if any exclude pattern matches
            skip = False
            for pattern in EXCLUDE_PATTERNS:
                if pattern in str(file_path):
                    skip = True
                    break
            if not skip:
                filtered_files.append(file_path)

        # Validate each file
        for file_path in filtered_files:
            try:
                file_results = self._validate_single_file(
                    file_path=file_path,
                    level=level,
                    validators=validators
                )
                all_results.extend(file_results)
            except Exception as e:
                # Log error but continue with other files
                print(f"Warning: Failed to validate {file_path}: {e}")
                continue

        return all_results

    def generate_report(
        self,
        report: ValidationReport,
        format: Literal["markdown", "json", "text"] = "markdown"
    ) -> str:
        """
        Generate formatted report from ValidationReport.

        Args:
            report: ValidationReport to format
            format: Output format (markdown, json, or text)

        Returns:
            Formatted report string

        Raises:
            ValueError: If unknown format specified
        """
        if format == "json":
            # Return JSON representation
            return report.to_json()

        elif format == "markdown":
            return self._generate_markdown_report(report)

        elif format == "text":
            # Simple text format
            lines = []
            lines.append("=" * 60)
            lines.append("VALIDATION REPORT")
            lines.append("=" * 60)
            lines.append(f"Status: {report.overall_status}")
            lines.append(f"Score: {report.average_score:.1f}/100")
            lines.append(f"Total Findings: {report.total_findings.get('total', 0)}")
            lines.append(f"  - Critical: {report.critical_count}")
            lines.append(f"  - High: {report.high_count}")
            lines.append(f"  - Medium: {report.medium_count}")
            lines.append(f"  - Low: {report.low_count}")
            lines.append(f"Execution Time: {report.total_execution_time_ms}ms")
            lines.append(f"Total Cost: ${report.total_cost_usd:.4f}")
            lines.append("=" * 60)
            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown format: {format}")

    def _generate_markdown_report(self, report: ValidationReport) -> str:
        """
        Generate detailed markdown report.

        Args:
            report: ValidationReport to format

        Returns:
            Markdown-formatted report
        """
        lines = []

        # Header
        lines.append("# Validation Report")
        lines.append("")
        lines.append(f"**Status:** {report.overall_status}")
        lines.append(f"**Score:** {report.average_score:.1f}/100")
        lines.append(f"**Total Findings:** {report.total_findings.get('total', 0)}")
        lines.append(f"**Execution Time:** {report.total_execution_time_ms}ms")
        lines.append(f"**Total Cost:** ${report.total_cost_usd:.4f}")
        lines.append("")

        # Summary by severity
        lines.append("## Findings by Severity")
        lines.append("")
        lines.append(f"- 🔴 **Critical:** {report.critical_count}")
        lines.append(f"- 🟠 **High:** {report.high_count}")
        lines.append(f"- 🟡 **Medium:** {report.medium_count}")
        lines.append(f"- 🔵 **Low:** {report.low_count}")
        lines.append(f"- ⚪ **Info:** {report.info_count}")
        lines.append("")

        # Results by validator
        lines.append("## Results by Validator")
        lines.append("")

        for result in report.results.values():
            lines.append(f"### {result.validator_name}")
            lines.append("")
            lines.append(f"- **Status:** {result.status}")
            lines.append(f"- **Score:** {result.score}/100")
            lines.append(f"- **Findings:** {len(result.findings)}")
            lines.append(f"- **Model:** {result.model_used}")
            lines.append(f"- **Time:** {result.execution_time_ms}ms")
            lines.append(f"- **Cost:** ${result.cost_usd:.6f}")
            lines.append("")

            # List findings
            if result.findings:
                lines.append("**Findings:**")
                lines.append("")
                for finding in result.findings:
                    severity_emoji = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MEDIUM": "🟡",
                        "LOW": "🔵",
                        "INFO": "⚪"
                    }.get(finding.severity, "⚪")

                    lines.append(f"{severity_emoji} **{finding.severity}** - {finding.issue}")
                    lines.append(f"  - **Location:** {finding.location}")
                    lines.append(f"  - **Category:** {finding.category}/{finding.subcategory}")
                    lines.append(f"  - **Recommendation:** {finding.recommendation}")
                    if finding.fix:
                        lines.append(f"  - **Fix:** `{finding.fix}`")
                    lines.append("")

        # Footer
        lines.append("---")
        lines.append(f"*Generated by ValidationOrchestrator - {len(report.results)} validators run*")

        return "\n".join(lines)
