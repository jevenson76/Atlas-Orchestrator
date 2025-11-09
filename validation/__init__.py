"""
Validation Package - Modular Validation System

This package provides a modular, extensible validation framework for code,
documentation, and tests. It integrates with Phase B infrastructure for
multi-provider LLM fallback and observability.

Architecture:
    validation/
    ├── interfaces.py         - Types, protocols, constants
    ├── core.py              - Core validation engine
    ├── critic_integration.py - Critic-based deep analysis
    ├── result_aggregator.py  - Result aggregation and reporting
    └── __init__.py          - Public API (this file)

Public API:
    # Primary class
    from validation import ValidationOrchestrator

    # Helper classes
    from validation import CriticIntegration, ResultAggregator

    # Types
    from validation import (
        ValidationResult,
        ValidationReport,
        ValidationFinding,
        ValidationLevel
    )

Usage:
    # Basic validation
    from validation import ValidationOrchestrator

    orchestrator = ValidationOrchestrator(project_root=".")
    result = orchestrator.validate_code(
        code=source_code,
        context={"file_path": "auth.py"},
        level="standard"
    )

    # With critics (comprehensive evaluation)
    critic_integration = CriticIntegration(orchestrator)
    comprehensive_result = critic_integration.validate_with_critics(
        code=source_code,
        level="thorough"
    )

    # Directory validation
    aggregator = ResultAggregator(orchestrator)
    report = aggregator.run_all_validators(
        target_path="src/",
        level="standard",
        recursive=True
    )
"""

# Core validation engine
from validation.core import ValidationOrchestrator

# Integration modules
from validation.critic_integration import CriticIntegration
from validation.result_aggregator import ResultAggregator

# Types and interfaces
from validation.interfaces import (
    # Type aliases
    ValidationLevel,
    ValidatorName,

    # Constants
    VALIDATION_MODELS,
    VALIDATION_TEMPERATURES,
    DEFAULT_VALIDATION_LEVEL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_MAX_TOKENS,
    DOC_PATTERNS,
    TEST_PATTERNS,
    CODE_EXTENSIONS,
    EXCLUDE_PATTERNS,
    INLINE_PROMPTS,
    LANGUAGE_EXTENSION_MAP,

    # Protocols
    ValidationEngineProtocol,
    ResultAggregatorProtocol,
    CriticIntegrationProtocol,
)

# Re-export types from validation_types for convenience
from validation_types import (
    ValidationFinding,
    ValidationResult,
    ValidationReport,
    SeverityLevel,
    Status,
    create_fail_result
)

# Package metadata
__version__ = "2.0.0"
__author__ = "Multi-Agent System"
__description__ = "Modular validation framework with Phase B integration"

# Public API
__all__ = [
    # Main classes
    "ValidationOrchestrator",
    "CriticIntegration",
    "ResultAggregator",

    # Types
    "ValidationFinding",
    "ValidationResult",
    "ValidationReport",
    "SeverityLevel",
    "Status",
    "ValidationLevel",
    "ValidatorName",

    # Constants
    "VALIDATION_MODELS",
    "VALIDATION_TEMPERATURES",
    "DEFAULT_VALIDATION_LEVEL",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_MAX_TOKENS",

    # Protocols
    "ValidationEngineProtocol",
    "ResultAggregatorProtocol",
    "CriticIntegrationProtocol",

    # Helper functions
    "create_fail_result",

    # Metadata
    "__version__",
]


# Convenience function for creating orchestrator with all integrations
def create_validation_system(
    project_root: str,
    validators=None,
    default_level: ValidationLevel = "standard"
):
    """
    Create a complete validation system with all integrations.

    This is a convenience function that creates a ValidationOrchestrator
    with CriticIntegration and ResultAggregator attached.

    Args:
        project_root: Root directory of project being validated
        validators: List of validator names (default: all three)
        default_level: Default validation level

    Returns:
        Dictionary with:
        - orchestrator: ValidationOrchestrator instance
        - critic_integration: CriticIntegration instance
        - result_aggregator: ResultAggregator instance

    Example:
        system = create_validation_system(project_root=".")

        # Use orchestrator directly
        result = system['orchestrator'].validate_code(code, level="standard")

        # Use critic integration
        comprehensive = system['critic_integration'].validate_with_critics(code)

        # Use result aggregator
        report = system['result_aggregator'].run_all_validators("src/")
    """
    orchestrator = ValidationOrchestrator(
        project_root=project_root,
        validators=validators,
        default_level=default_level
    )

    critic_integration = CriticIntegration(orchestrator)
    result_aggregator = ResultAggregator(orchestrator)

    return {
        "orchestrator": orchestrator,
        "critic_integration": critic_integration,
        "result_aggregator": result_aggregator
    }


# Add create_validation_system to __all__
__all__.append("create_validation_system")
