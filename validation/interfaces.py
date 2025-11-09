"""
Validation Interfaces - Type Definitions, Protocols, and Constants

This module defines the core interfaces and types used throughout the validation system.
It re-exports types from validation_types.py and adds validation-specific protocols.

Architecture:
    - Pure type definitions (no implementation)
    - Protocol-based design for dependency inversion
    - Shared constants for configuration

Usage:
    from validation.interfaces import (
        ValidationResult,
        ValidationReport,
        ValidationLevel,
        VALIDATION_MODELS
    )
"""

from typing import Protocol, List, Dict, Optional, Literal, Any, runtime_checkable
from pathlib import Path

# Re-export core types from validation_types
from validation_types import (
    ValidationFinding,
    ValidationResult,
    ValidationReport,
    SeverityLevel,
    Status
)

# Type aliases
ValidationLevel = Literal["quick", "standard", "thorough"]
ValidatorName = Literal["code-validator", "doc-validator", "test-validator"]

# ============================================================================
# CONSTANTS
# ============================================================================

# Model selection by validator and level
VALIDATION_MODELS = {
    "code-validator": {
        "quick": "claude-haiku-4-5-20250611",
        "standard": "claude-sonnet-4-5-20250929",
        "thorough": "claude-opus-4-20250514"
    },
    "doc-validator": {
        "quick": "claude-sonnet-4-5-20250929",
        "standard": "claude-sonnet-4-5-20250929",
        "thorough": "claude-sonnet-4-5-20250929"
    },
    "test-validator": {
        "quick": "claude-sonnet-4-5-20250929",
        "standard": "claude-sonnet-4-5-20250929",
        "thorough": "claude-sonnet-4-5-20250929"
    }
}

# Temperature settings by validator and level
VALIDATION_TEMPERATURES = {
    "code-validator": {
        "quick": 0.1,
        "standard": 0.1,
        "thorough": 0.1
    },
    "doc-validator": {
        "quick": 0.1,
        "standard": 0.2,
        "thorough": 0.3
    },
    "test-validator": {
        "quick": 0.1,
        "standard": 0.2,
        "thorough": 0.3
    }
}

# Default configuration values
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_TOKENS = 4000
DEFAULT_VALIDATION_LEVEL: ValidationLevel = "standard"

# File patterns for auto-detection
DOC_PATTERNS = [".md", "readme", "guide", "docs", ".rst", ".txt"]
TEST_PATTERNS = ["test_", "_test.", ".test.", "spec_", "_spec.", ".spec."]
CODE_EXTENSIONS = [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".rb", ".php"]

# Exclusion patterns for directory validation
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".pytest_cache",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store"
]

# ============================================================================
# PROTOCOLS
# ============================================================================

@runtime_checkable
class ValidationEngineProtocol(Protocol):
    """Protocol for validation engines."""

    def validate_code(
        self,
        code: str,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None
    ) -> ValidationResult:
        """Validate code quality, security, and performance."""
        ...

    def validate_documentation(
        self,
        documentation: str,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None
    ) -> ValidationResult:
        """Validate documentation completeness and clarity."""
        ...

    def validate_tests(
        self,
        test_code: str,
        source_code: Optional[str] = None,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None
    ) -> ValidationResult:
        """Validate test coverage and quality."""
        ...


@runtime_checkable
class ResultAggregatorProtocol(Protocol):
    """Protocol for result aggregation and reporting."""

    def run_all_validators(
        self,
        target_path: str,
        level: Optional[ValidationLevel] = None,
        recursive: bool = True,
        validators: Optional[List[str]] = None
    ) -> ValidationReport:
        """Run all appropriate validators on a file or directory."""
        ...

    def generate_report(
        self,
        report: ValidationReport,
        format: Literal["markdown", "json", "text"] = "markdown"
    ) -> str:
        """Generate formatted report from ValidationReport."""
        ...


@runtime_checkable
class CriticIntegrationProtocol(Protocol):
    """Protocol for critic integration."""

    def validate_with_critics(
        self,
        code: str,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None,
        run_validators: bool = True,
        critics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Comprehensive code evaluation combining validators and critics."""
        ...


# ============================================================================
# INLINE PROMPTS (Fallback when .md extraction fails)
# ============================================================================

INLINE_PROMPTS = {
    "code-validator": """You are a code quality validator. Analyze the provided code for quality, security, and performance issues.

VALIDATION LEVEL: {level}
LANGUAGE: {language}
FILE: {file_path}

CODE TO VALIDATE:
{target_content}

Analyze for:
- Code quality (naming, structure, complexity)
- Security vulnerabilities (OWASP Top 10)
- Performance issues
- Best practices adherence
- Error handling

Return JSON with this exact structure:
{{
    "status": "PASS|FAIL|WARNING",
    "score": 0-100,
    "findings": [
        {{
            "id": "FIND-001",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
            "category": "security|performance|quality|style",
            "subcategory": "specific-issue",
            "location": "line 42, function foo()",
            "issue": "Description of the issue",
            "recommendation": "How to fix it",
            "fix": "Optional code fix",
            "code_snippet": "Optional problematic code",
            "references": ["Optional reference links"],
            "impact": "Optional impact description",
            "confidence": 0.0-1.0
        }}
    ],
    "passed_checks": ["List of passed validations"],
    "metrics": {{"complexity": 5, "maintainability": 85}},
    "target": "{file_path}"
}}""",

    "doc-validator": """You are a documentation validator. Analyze the provided documentation for completeness, accuracy, and clarity.

VALIDATION LEVEL: {level}
DOC TYPE: {doc_type}
PROJECT TYPE: {project_type}

DOCUMENTATION TO VALIDATE:
{target_content}

Analyze for:
- Completeness (all necessary sections present)
- Accuracy (technically correct information)
- Clarity (easy to understand)
- User perspective (helpful for target audience)
- Examples and code samples

Return JSON with this exact structure:
{{
    "status": "PASS|FAIL|WARNING",
    "score": 0-100,
    "findings": [
        {{
            "id": "DOC-001",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
            "category": "completeness|accuracy|clarity|examples",
            "subcategory": "specific-issue",
            "location": "Section: Installation",
            "issue": "Description of the issue",
            "recommendation": "How to improve",
            "fix": "Optional improved text",
            "references": ["Optional reference links"],
            "confidence": 0.0-1.0
        }}
    ],
    "passed_checks": ["List of passed validations"],
    "metrics": {{"readability": 85, "completeness": 90}},
    "target": "documentation"
}}""",

    "test-validator": """You are a test quality validator. Analyze the provided test code for coverage, quality, and effectiveness.

VALIDATION LEVEL: {level}
TEST FRAMEWORK: {test_framework}
MODULE: {module_name}

TEST CODE TO VALIDATE:
{target_content}

Analyze for:
- Test coverage (edge cases, error paths)
- Test quality (clear, maintainable, isolated)
- Assertions (meaningful, comprehensive)
- Test smells (anti-patterns)
- Effectiveness (do tests catch bugs?)

Return JSON with this exact structure:
{{
    "status": "PASS|FAIL|WARNING",
    "score": 0-100,
    "findings": [
        {{
            "id": "TEST-001",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
            "category": "coverage|quality|effectiveness|smells",
            "subcategory": "specific-issue",
            "location": "test_foo() line 15",
            "issue": "Description of the issue",
            "recommendation": "How to improve",
            "fix": "Optional improved test",
            "references": ["Optional reference links"],
            "confidence": 0.0-1.0
        }}
    ],
    "passed_checks": ["List of passed validations"],
    "metrics": {{"coverage_estimate": 75, "test_quality": 80}},
    "target": "{module_name}"
}}"""
}

# ============================================================================
# LANGUAGE DETECTION
# ============================================================================

LANGUAGE_EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript-react",
    ".tsx": "typescript-react",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "c++",
    ".c": "c",
    ".rb": "ruby",
    ".php": "php",
    ".md": "markdown",
    ".rst": "restructuredtext"
}

# ============================================================================
# VERSION
# ============================================================================

__version__ = "2.0.0"
