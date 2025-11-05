"""
Validation Result Data Structures

Defines standardized output formats for all validators in the ZTE system.
These classes enable:
- Structured validator output
- JSON serialization for agent communication
- Aggregated validation reports
- Auto-fix workflows

Python 3.12+ features used:
- type statement for type aliases
- dataclass with slots
- Pattern matching for severity levels
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List
from datetime import datetime
from enum import Enum


# Type aliases for clarity
type Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
type Status = Literal["PASS", "FAIL", "WARNING"]


class SeverityLevel(str, Enum):
    """Severity levels for validation findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def priority(self) -> int:
        """Get numeric priority (higher = more severe)."""
        return {
            "CRITICAL": 5,
            "HIGH": 4,
            "MEDIUM": 3,
            "LOW": 2,
            "INFO": 1
        }[self.value]

    @property
    def emoji(self) -> str:
        """Get emoji representation."""
        return {
            "CRITICAL": "🚨",
            "HIGH": "❗",
            "MEDIUM": "⚠️",
            "LOW": "ℹ️",
            "INFO": "💡"
        }[self.value]


@dataclass(slots=True)
class ValidationFinding:
    """
    A single validation finding from a validator.

    Represents an issue discovered during code/doc/test validation.
    Includes location, severity, and actionable fix recommendation.

    Attributes:
        id: Unique identifier for this finding (e.g., "SEC-001")
        severity: Severity level of the issue
        category: High-level category (e.g., "security", "performance")
        subcategory: Specific issue type (e.g., "sql_injection")
        location: File path and line number (e.g., "auth.py:42-45")
        issue: Description of the problem
        recommendation: Actionable fix recommendation
        fix: Optional code fix that can be auto-applied
        code_snippet: Optional code showing the issue
        references: Links to documentation or standards
        impact: Optional description of impact if not fixed

    Example:
        >>> finding = ValidationFinding(
        ...     id="SEC-001",
        ...     severity="CRITICAL",
        ...     category="security",
        ...     subcategory="sql_injection",
        ...     location="auth.py:42",
        ...     issue="SQL query uses string interpolation",
        ...     recommendation="Use parameterized queries",
        ...     fix='cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))'
        ... )
    """

    id: str
    severity: Severity
    category: str
    subcategory: str
    location: str
    issue: str
    recommendation: str
    fix: Optional[str] = None
    code_snippet: Optional[str] = None
    references: list[str] = field(default_factory=list)
    impact: Optional[str] = None
    confidence: float = 1.0  # 0.0 to 1.0, how confident is the validator

    def __post_init__(self):
        """Validate severity level."""
        if self.severity not in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            raise ValueError(f"Invalid severity: {self.severity}")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

    @property
    def severity_level(self) -> SeverityLevel:
        """Get severity as enum."""
        return SeverityLevel(self.severity)

    @property
    def is_critical(self) -> bool:
        """Check if finding is critical severity."""
        return self.severity == "CRITICAL"

    @property
    def is_actionable(self) -> bool:
        """Check if finding has an auto-fixable recommendation."""
        return self.fix is not None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "subcategory": self.subcategory,
            "location": self.location,
            "issue": self.issue,
            "recommendation": self.recommendation,
            "fix": self.fix,
            "code_snippet": self.code_snippet,
            "references": self.references,
            "impact": self.impact,
            "confidence": self.confidence
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationFinding":
        """Create from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        """Human-readable representation."""
        emoji = self.severity_level.emoji
        output = [
            f"{emoji} [{self.severity}] {self.id}",
            f"Location: {self.location}",
            f"Category: {self.category}/{self.subcategory}",
            f"Issue: {self.issue}",
            f"Recommendation: {self.recommendation}"
        ]

        if self.impact:
            output.append(f"Impact: {self.impact}")

        if self.code_snippet:
            output.append(f"Code:\n{self.code_snippet}")

        if self.fix:
            output.append(f"Fix:\n{self.fix}")

        if self.references:
            output.append(f"References: {', '.join(self.references)}")

        if self.confidence < 1.0:
            output.append(f"Confidence: {self.confidence:.0%}")

        return "\n".join(output)


@dataclass(slots=True)
class ValidationResult:
    """
    Result from a single validator execution.

    Represents the output of one validator (code/doc/test) running
    against a target. Contains findings, metrics, and execution metadata.

    Attributes:
        validator_name: Name of the validator that produced this result
        status: Overall status (PASS/FAIL/WARNING)
        score: Numeric score 0-100 (100 = perfect)
        findings: List of issues discovered
        execution_time_ms: How long validation took in milliseconds
        model_used: Which LLM model was used
        cost_usd: Estimated API cost in USD
        timestamp: When validation was performed
        passed_checks: List of checks that passed
        metrics: Additional metrics (LOC, complexity, etc.)
        target: What was validated (file path, directory, etc.)

    Example:
        >>> result = ValidationResult(
        ...     validator_name="code-validator",
        ...     status="FAIL",
        ...     score=65,
        ...     findings=[finding1, finding2],
        ...     execution_time_ms=8420,
        ...     model_used="claude-sonnet-4-5-20250929",
        ...     cost_usd=0.0042
        ... )
    """

    validator_name: str
    status: Status
    score: float  # 0-100
    findings: list[ValidationFinding] = field(default_factory=list)
    execution_time_ms: int = 0
    model_used: str = ""
    cost_usd: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    passed_checks: list[str] = field(default_factory=list)
    metrics: dict[str, any] = field(default_factory=dict)
    target: str = ""

    def __post_init__(self):
        """Validate status and score."""
        if self.status not in ["PASS", "FAIL", "WARNING"]:
            raise ValueError(f"Invalid status: {self.status}")

        if not 0 <= self.score <= 100:
            raise ValueError(f"Score must be 0-100, got {self.score}")

    @property
    def has_critical_findings(self) -> bool:
        """Check if result contains critical findings."""
        return any(f.is_critical for f in self.findings)

    @property
    def has_actionable_fixes(self) -> bool:
        """Check if result has auto-fixable findings."""
        return any(f.is_actionable for f in self.findings)

    @property
    def finding_summary(self) -> dict[str, int]:
        """Get count of findings by severity."""
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }

        for finding in self.findings:
            summary[finding.severity.lower()] += 1

        return summary

    @property
    def total_findings(self) -> int:
        """Get total number of findings."""
        return len(self.findings)

    def get_findings_by_severity(self, severity: Severity) -> list[ValidationFinding]:
        """Get all findings of a specific severity."""
        return [f for f in self.findings if f.severity == severity]

    def get_critical_findings(self) -> list[ValidationFinding]:
        """Get all critical findings."""
        return self.get_findings_by_severity("CRITICAL")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "validator_name": self.validator_name,
            "status": self.status,
            "score": self.score,
            "findings": [f.to_dict() for f in self.findings],
            "execution_time_ms": self.execution_time_ms,
            "model_used": self.model_used,
            "cost_usd": self.cost_usd,
            "timestamp": self.timestamp,
            "passed_checks": self.passed_checks,
            "metrics": self.metrics,
            "target": self.target,
            "summary": self.finding_summary
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationResult":
        """Create from dictionary."""
        # Convert findings back to objects
        findings_data = data.pop("findings", [])
        findings = [ValidationFinding.from_dict(f) for f in findings_data]

        # Remove summary if present (it's computed)
        data.pop("summary", None)

        return cls(findings=findings, **data)

    def __str__(self) -> str:
        """Human-readable representation."""
        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARNING": "⚠️"
        }[self.status]

        summary = self.finding_summary

        output = [
            f"{status_emoji} {self.validator_name.upper()} - {self.status}",
            f"Score: {self.score:.1f}/100",
            f"Target: {self.target or 'Not specified'}",
            f"Model: {self.model_used}",
            f"Time: {self.execution_time_ms}ms",
            f"Cost: ${self.cost_usd:.4f}",
            "",
            "Findings:",
            f"  🚨 Critical: {summary['critical']}",
            f"  ❗ High: {summary['high']}",
            f"  ⚠️  Medium: {summary['medium']}",
            f"  ℹ️  Low: {summary['low']}",
            f"  💡 Info: {summary['info']}",
            "",
            f"Passed Checks: {len(self.passed_checks)}"
        ]

        if self.findings:
            output.append("\nTop Issues:")
            # Show top 3 most severe findings
            sorted_findings = sorted(
                self.findings,
                key=lambda f: f.severity_level.priority,
                reverse=True
            )
            for finding in sorted_findings[:3]:
                output.append(f"\n{finding}")

        return "\n".join(output)


@dataclass(slots=True)
class ValidationReport:
    """
    Aggregated validation report from multiple validators.

    Combines results from code-validator, test-validator, and
    doc-validator into a single comprehensive report.

    Attributes:
        overall_status: Aggregated status across all validators
        results: Map of validator names to their results
        summary: Human-readable summary of validation
        total_findings: Count of findings by severity across all validators
        total_cost_usd: Sum of all validation costs
        total_execution_time_ms: Sum of execution times
        recommendations: Prioritized list of actions to take
        timestamp: When report was generated
        metadata: Additional report metadata

    Example:
        >>> report = ValidationReport(
        ...     overall_status="FAIL",
        ...     results={
        ...         "code-validator": code_result,
        ...         "test-validator": test_result
        ...     }
        ... )
        >>> report.get_all_critical_findings()
        [finding1, finding2, finding3]
    """

    overall_status: Status
    results: dict[str, ValidationResult] = field(default_factory=dict)
    summary: str = ""
    total_findings: dict[str, int] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    total_execution_time_ms: int = 0
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Compute aggregated metrics."""
        if self.results:
            self._compute_aggregates()

    def _compute_aggregates(self):
        """Compute aggregated metrics from all results."""
        # Aggregate findings by severity
        self.total_findings = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }

        self.total_cost_usd = 0.0
        self.total_execution_time_ms = 0

        for result in self.results.values():
            summary = result.finding_summary
            for severity, count in summary.items():
                self.total_findings[severity] += count

            self.total_cost_usd += result.cost_usd
            self.total_execution_time_ms += result.execution_time_ms

        # Generate recommendations
        self._generate_recommendations()

    def _generate_recommendations(self):
        """Generate prioritized recommendations."""
        self.recommendations = []

        # Critical findings first
        for validator_name, result in self.results.items():
            critical = result.get_critical_findings()
            for finding in critical:
                self.recommendations.append(
                    f"[CRITICAL] {validator_name}: {finding.issue} ({finding.location})"
                )

        # Then high severity
        for validator_name, result in self.results.items():
            high = result.get_findings_by_severity("HIGH")
            for finding in high[:3]:  # Top 3 per validator
                self.recommendations.append(
                    f"[HIGH] {validator_name}: {finding.issue} ({finding.location})"
                )

    @property
    def passed(self) -> bool:
        """Check if overall validation passed."""
        return self.overall_status == "PASS"

    @property
    def has_critical_issues(self) -> bool:
        """Check if report contains critical findings."""
        return self.total_findings.get("critical", 0) > 0

    @property
    def average_score(self) -> float:
        """Get average score across all validators."""
        if not self.results:
            return 0.0

        return sum(r.score for r in self.results.values()) / len(self.results)

    @property
    def critical_count(self) -> int:
        """Get count of critical findings."""
        return self.total_findings.get("critical", 0)

    @property
    def high_count(self) -> int:
        """Get count of high severity findings."""
        return self.total_findings.get("high", 0)

    @property
    def medium_count(self) -> int:
        """Get count of medium severity findings."""
        return self.total_findings.get("medium", 0)

    @property
    def low_count(self) -> int:
        """Get count of low severity findings."""
        return self.total_findings.get("low", 0)

    @property
    def info_count(self) -> int:
        """Get count of info findings."""
        return self.total_findings.get("info", 0)

    def get_all_findings(self) -> list[ValidationFinding]:
        """Get all findings from all validators."""
        all_findings = []
        for result in self.results.values():
            all_findings.extend(result.findings)

        return all_findings

    def get_all_critical_findings(self) -> list[ValidationFinding]:
        """Get all critical findings from all validators."""
        return [f for f in self.get_all_findings() if f.is_critical]

    def get_actionable_fixes(self) -> list[ValidationFinding]:
        """Get all findings that have auto-fixable recommendations."""
        return [f for f in self.get_all_findings() if f.is_actionable]

    def get_validator_result(self, validator_name: str) -> Optional[ValidationResult]:
        """Get result from a specific validator."""
        return self.results.get(validator_name)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_status": self.overall_status,
            "results": {name: result.to_dict() for name, result in self.results.items()},
            "summary": self.summary,
            "total_findings": self.total_findings,
            "total_cost_usd": self.total_cost_usd,
            "total_execution_time_ms": self.total_execution_time_ms,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "average_score": self.average_score
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationReport":
        """Create from dictionary."""
        # Convert results back to objects
        results_data = data.pop("results", {})
        results = {
            name: ValidationResult.from_dict(result)
            for name, result in results_data.items()
        }

        # Remove computed fields
        data.pop("average_score", None)

        return cls(results=results, **data)

    @classmethod
    def from_results(
        cls,
        results: List[ValidationResult],
        total_time_ms: int = 0
    ) -> "ValidationReport":
        """
        Create ValidationReport from list of ValidationResult objects.

        Aggregates multiple validation results into a single report.

        Args:
            results: List of ValidationResult objects
            total_time_ms: Total execution time in milliseconds

        Returns:
            ValidationReport with aggregated data
        """
        from datetime import datetime

        # Convert list to dictionary
        results_dict = {result.validator_name: result for result in results}

        # Determine overall status
        statuses = [r.status for r in results]
        if "FAIL" in statuses:
            overall_status = "FAIL"
        elif "WARNING" in statuses:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        # Count findings by severity
        total_findings_count = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        info_count = 0

        for result in results:
            total_findings_count += len(result.findings)
            for finding in result.findings:
                if finding.severity == "CRITICAL":
                    critical_count += 1
                elif finding.severity == "HIGH":
                    high_count += 1
                elif finding.severity == "MEDIUM":
                    medium_count += 1
                elif finding.severity == "LOW":
                    low_count += 1
                elif finding.severity == "INFO":
                    info_count += 1

        # Calculate total cost
        total_cost = sum(r.cost_usd for r in results)

        # Build summary
        summary = f"{len(results)} validators run. "
        if overall_status == "PASS":
            summary += "All checks passed."
        elif overall_status == "FAIL":
            summary += f"{total_findings_count} issues found."
        else:
            summary += f"{total_findings_count} warnings found."

        # Collect recommendations
        recommendations = []
        for result in results:
            for finding in result.findings:
                if finding.severity in ["CRITICAL", "HIGH"]:
                    recommendations.append(finding.recommendation)

        return cls(
            overall_status=overall_status,
            results=results_dict,
            summary=summary,
            total_findings={
                "total": total_findings_count,
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
                "info": info_count
            },
            total_cost_usd=total_cost,
            total_execution_time_ms=total_time_ms,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
            metadata={}
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARNING": "⚠️"
        }[self.overall_status]

        output = [
            "=" * 60,
            f"{status_emoji} VALIDATION REPORT - {self.overall_status}",
            "=" * 60,
            f"Generated: {self.timestamp}",
            f"Average Score: {self.average_score:.1f}/100",
            f"Total Cost: ${self.total_cost_usd:.4f}",
            f"Total Time: {self.total_execution_time_ms}ms",
            "",
            "VALIDATORS RUN:",
        ]

        for validator_name, result in self.results.items():
            status_icon = "✅" if result.status == "PASS" else "❌"
            output.append(f"  {status_icon} {validator_name}: {result.status} (Score: {result.score:.1f})")

        output.extend([
            "",
            "FINDINGS SUMMARY:",
            f"  🚨 Critical: {self.total_findings.get('critical', 0)}",
            f"  ❗ High: {self.total_findings.get('high', 0)}",
            f"  ⚠️  Medium: {self.total_findings.get('medium', 0)}",
            f"  ℹ️  Low: {self.total_findings.get('low', 0)}",
            f"  💡 Info: {self.total_findings.get('info', 0)}",
            ""
        ])

        if self.summary:
            output.extend([
                "SUMMARY:",
                self.summary,
                ""
            ])

        if self.recommendations:
            output.extend([
                "PRIORITY RECOMMENDATIONS:",
                ""
            ])
            for i, rec in enumerate(self.recommendations[:10], 1):
                output.append(f"{i}. {rec}")

        output.append("=" * 60)

        return "\n".join(output)


# Convenience functions for creating common validation objects

def create_pass_result(
    validator_name: str,
    target: str = "",
    model_used: str = "",
    execution_time_ms: int = 0,
    cost_usd: float = 0.0
) -> ValidationResult:
    """Create a passing validation result with no findings."""
    return ValidationResult(
        validator_name=validator_name,
        status="PASS",
        score=100.0,
        target=target,
        model_used=model_used,
        execution_time_ms=execution_time_ms,
        cost_usd=cost_usd
    )


def create_fail_result(
    validator_name: str,
    findings: list[ValidationFinding],
    target: str = "",
    model_used: str = "",
    execution_time_ms: int = 0,
    cost_usd: float = 0.0
) -> ValidationResult:
    """Create a failing validation result with findings."""
    # Calculate score based on severity of findings
    severity_weights = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": 1}
    penalty = sum(severity_weights.get(f.severity, 0) for f in findings)
    score = max(0, 100 - penalty)

    return ValidationResult(
        validator_name=validator_name,
        status="FAIL",
        score=score,
        findings=findings,
        target=target,
        model_used=model_used,
        execution_time_ms=execution_time_ms,
        cost_usd=cost_usd
    )


def aggregate_results(
    results: dict[str, ValidationResult],
    summary: str = ""
) -> ValidationReport:
    """
    Aggregate multiple validation results into a report.

    Args:
        results: Map of validator names to their results
        summary: Optional summary text

    Returns:
        Aggregated validation report
    """
    # Determine overall status
    if all(r.status == "PASS" for r in results.values()):
        overall_status = "PASS"
    elif any(r.has_critical_findings for r in results.values()):
        overall_status = "FAIL"
    else:
        overall_status = "WARNING"

    return ValidationReport(
        overall_status=overall_status,
        results=results,
        summary=summary
    )
