"""
ValidationOrchestrator - Backward Compatibility Shim

⚠️  DEPRECATION WARNING ⚠️

This module is maintained for backward compatibility only.

The ValidationOrchestrator has been refactored into a modular package.
Please update your imports to use the new package structure:

OLD (deprecated):
    from validation_orchestrator import ValidationOrchestrator

NEW (recommended):
    from validation import ValidationOrchestrator

This backward compatibility shim will be removed in v3.0.0.
Update your code within the 8-week migration window.

Migration timeline:
- Week 0-8: Both import paths work (current)
- Week 8-16: Deprecation warnings (migration window)
- Week 16+: Old import path removed (v3.0.0)

For complete migration guide, see: docs/MIGRATION_GUIDE_PHASE_2A.md

---

All functionality has been moved to the `validation` package:
- validation.interfaces - Types, protocols, constants
- validation.core - Core validation engine
- validation.critic_integration - Critic-based analysis
- validation.result_aggregator - Result aggregation and reporting

The new modular structure provides:
✅ Better organization and maintainability
✅ Easier testing and mocking
✅ Protocol-based design for extensibility
✅ Smaller, focused modules
✅ Same public API (100% backward compatible)
"""

import warnings
from pathlib import Path

# Show deprecation warning when this module is imported
warnings.warn(
    "validation_orchestrator is deprecated and will be removed in v3.0.0. "
    "Please use 'from validation import ValidationOrchestrator' instead. "
    "See docs/MIGRATION_GUIDE_PHASE_2A.md for details.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new validation package
from validation import (
    ValidationOrchestrator,
    CriticIntegration,
    ResultAggregator,
    ValidationFinding,
    ValidationResult,
    ValidationReport,
    SeverityLevel,
    Status,
    ValidationLevel,
    ValidatorName,
    VALIDATION_MODELS,
    VALIDATION_TEMPERATURES,
    DEFAULT_VALIDATION_LEVEL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_MAX_TOKENS,
    create_fail_result,
    __version__
)

# Maintain module-level __version__ for backward compatibility
__version__ = __version__

# Public API (same as before, now imported from validation package)
__all__ = [
    "ValidationOrchestrator",
    "ValidationFinding",
    "ValidationResult",
    "ValidationReport",
    "SeverityLevel",
    "Status",
    "create_fail_result",
    "__version__"
]

# Backward compatibility note for module docstring
__doc__ += f"""

Current Version: {__version__}
New Package Location: validation/
Migration Guide: docs/MIGRATION_GUIDE_PHASE_2A.md

For new code, prefer direct import from validation package:
    from validation import ValidationOrchestrator
"""
