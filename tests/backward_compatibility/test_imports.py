"""
Backward Compatibility Tests

Tests that old import paths still work and deprecation warnings are shown.
"""

import pytest
import warnings
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBackwardCompatibleImports:
    """Test backward compatible import paths."""

    def test_old_import_shows_deprecation_warning(self):
        """Test that old import path shows deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import using old path
            import validation_orchestrator

            # Should have deprecation warning
            assert len(w) > 0
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("validation_orchestrator is deprecated" in str(warning.message) for warning in w)

    def test_old_import_validation_orchestrator_class(self):
        """Test importing ValidationOrchestrator from old module."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation_orchestrator import ValidationOrchestrator

            assert ValidationOrchestrator is not None
            assert ValidationOrchestrator.__name__ == "ValidationOrchestrator"

    def test_old_import_validation_result_class(self):
        """Test importing ValidationResult from old module."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation_orchestrator import ValidationResult

            assert ValidationResult is not None

    def test_old_import_validation_finding_class(self):
        """Test importing ValidationFinding from old module."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation_orchestrator import ValidationFinding

            assert ValidationFinding is not None


class TestNewImports:
    """Test new import paths from validation package."""

    def test_new_import_validation_orchestrator(self):
        """Test importing ValidationOrchestrator from new package."""
        from validation import ValidationOrchestrator

        assert ValidationOrchestrator is not None
        assert ValidationOrchestrator.__name__ == "ValidationOrchestrator"

    def test_new_import_validation_result(self):
        """Test importing ValidationResult from new package."""
        from validation import ValidationResult

        assert ValidationResult is not None

    def test_new_import_validation_finding(self):
        """Test importing ValidationFinding from new package."""
        from validation import ValidationFinding

        assert ValidationFinding is not None

    def test_new_import_critic_integration(self):
        """Test importing CriticIntegration from new package."""
        from validation import CriticIntegration

        assert CriticIntegration is not None

    def test_new_import_result_aggregator(self):
        """Test importing ResultAggregator from new package."""
        from validation import ResultAggregator

        assert ResultAggregator is not None


class TestImportEquivalence:
    """Test that old and new imports point to the same classes."""

    def test_validation_orchestrator_same_class(self):
        """Test that old and new imports give same ValidationOrchestrator class."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation import ValidationOrchestrator as NewOrchestrator
            from validation_orchestrator import ValidationOrchestrator as OldOrchestrator

            # Should be the exact same class
            assert NewOrchestrator is OldOrchestrator

    def test_validation_result_same_class(self):
        """Test that old and new imports give same ValidationResult class."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation import ValidationResult as NewResult
            from validation_orchestrator import ValidationResult as OldResult

            # Should be the exact same class
            assert NewResult is OldResult

    def test_validation_finding_same_class(self):
        """Test that old and new imports give same ValidationFinding class."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation import ValidationFinding as NewFinding
            from validation_orchestrator import ValidationFinding as OldFinding

            # Should be the exact same class
            assert NewFinding is OldFinding


class TestModuleLocations:
    """Test that classes are in correct modules."""

    def test_validation_orchestrator_module(self):
        """Test ValidationOrchestrator is in validation.core module."""
        from validation import ValidationOrchestrator

        assert ValidationOrchestrator.__module__ == "validation.core"

    def test_critic_integration_module(self):
        """Test CriticIntegration is in validation.critic_integration module."""
        from validation import CriticIntegration

        assert CriticIntegration.__module__ == "validation.critic_integration"

    def test_result_aggregator_module(self):
        """Test ResultAggregator is in validation.result_aggregator module."""
        from validation import ResultAggregator

        assert ResultAggregator.__module__ == "validation.result_aggregator"


class TestVersionInformation:
    """Test version information is accessible."""

    def test_validation_package_version(self):
        """Test validation package has __version__."""
        from validation import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)
        assert __version__ == "2.0.0"

    def test_old_module_version(self):
        """Test old module has __version__."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation_orchestrator import __version__

            assert __version__ is not None
            assert isinstance(__version__, str)
            assert __version__ == "2.0.0"

    def test_versions_match(self):
        """Test that old and new module versions match."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation import __version__ as new_version
            from validation_orchestrator import __version__ as old_version

            assert new_version == old_version


class TestInstantiation:
    """Test that classes can be instantiated from both import paths."""

    def test_instantiate_from_new_import(self):
        """Test creating ValidationOrchestrator from new import."""
        from validation import ValidationOrchestrator

        orchestrator = ValidationOrchestrator(project_root=".")
        assert orchestrator is not None
        assert isinstance(orchestrator, ValidationOrchestrator)

    def test_instantiate_from_old_import(self):
        """Test creating ValidationOrchestrator from old import."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation_orchestrator import ValidationOrchestrator

            orchestrator = ValidationOrchestrator(project_root=".")
            assert orchestrator is not None
            assert isinstance(orchestrator, ValidationOrchestrator)

    def test_instances_are_compatible(self):
        """Test that instances from old and new imports are compatible."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation import ValidationOrchestrator as NewOrchestrator
            from validation_orchestrator import ValidationOrchestrator as OldOrchestrator

            new_instance = NewOrchestrator(project_root=".")
            old_instance = OldOrchestrator(project_root=".")

            # Both should be instances of the same class
            assert type(new_instance) is type(old_instance)
            assert isinstance(new_instance, OldOrchestrator)
            assert isinstance(old_instance, NewOrchestrator)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
