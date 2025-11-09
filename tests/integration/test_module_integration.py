"""
Integration Tests for Module Integration

Tests that all Phase 2 modules (validation, protocols, utils) work together correctly.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation import (
    ValidationOrchestrator,
    CriticIntegration,
    ResultAggregator,
    ValidationResult,
    ValidationFinding,
    create_validation_system
)
from protocols import (
    DependencyFactory,
    CriticProtocol,
    get_default_factory,
    reset_default_factory
)
from utils import ModelSelector


class TestValidationProtocolsIntegration:
    """Test integration between validation package and protocols package."""

    def test_validation_orchestrator_initializes_with_model_selector(self):
        """Test that ValidationOrchestrator initializes with centralized ModelSelector."""
        orchestrator = ValidationOrchestrator(project_root=".")

        assert orchestrator.model_selector is not None
        assert isinstance(orchestrator.model_selector, ModelSelector)

    def test_validation_uses_model_selector_for_model_selection(self):
        """Test that ValidationOrchestrator uses ModelSelector._select_model."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Test model selection through orchestrator
        model = orchestrator._select_model("code-validator", "quick")
        assert model == "claude-haiku-4-5-20250611"

        model = orchestrator._select_model("code-validator", "thorough")
        assert model == "claude-opus-4-20250514"

    def test_critic_integration_uses_dependency_factory(self):
        """Test that CriticIntegration uses DependencyFactory."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Create with default factory
        integration = CriticIntegration(orchestrator)

        assert integration.factory is not None
        assert isinstance(integration.factory, DependencyFactory)

    def test_critic_integration_accepts_custom_factory(self):
        """Test that CriticIntegration accepts custom DependencyFactory."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Create custom factory with mock critic
        mock_critic = Mock(spec=CriticProtocol)
        custom_factory = DependencyFactory(critic_impl=mock_critic)

        # Create integration with custom factory
        integration = CriticIntegration(orchestrator, factory=custom_factory)

        assert integration.factory is custom_factory

        # Verify it returns our mock
        critic = integration.factory.get_critic_orchestrator()
        assert critic is mock_critic


class TestValidationUtilsIntegration:
    """Test integration between validation package and utils package."""

    def test_validation_orchestrator_uses_centralized_model_selector(self):
        """Test that ValidationOrchestrator uses centralized ModelSelector."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Verify ModelSelector is used
        assert hasattr(orchestrator, 'model_selector')
        assert isinstance(orchestrator.model_selector, ModelSelector)

    def test_model_selection_consistency_across_validators(self):
        """Test that model selection is consistent across different validators."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # All validators should use same ModelSelector instance
        code_model = orchestrator._select_model("code-validator", "standard")
        doc_model = orchestrator._select_model("doc-validator", "standard")

        # Code uses Sonnet at standard
        assert code_model == "claude-sonnet-4-5-20250929"

        # Doc also uses Sonnet at standard
        assert doc_model == "claude-sonnet-4-5-20250929"

    def test_cost_estimation_uses_model_selector(self):
        """Test that cost estimation uses ModelSelector."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Estimate cost for a response
        cost = orchestrator._estimate_cost("claude-haiku-4-5-20250611", "x" * 1000)

        # Should be greater than 0 (actual cost calculation)
        assert cost > 0
        assert cost < 0.01  # Haiku is cheap


class TestProtocolsUtilsIntegration:
    """Test integration between protocols package and utils package."""

    def test_dependency_factory_returns_centralized_model_selector(self):
        """Test that DependencyFactory returns centralized ModelSelector."""
        factory = DependencyFactory()

        selector = factory.get_model_selector()

        assert selector is not None
        assert isinstance(selector, ModelSelector)

    def test_dependency_factory_model_selector_singleton(self):
        """Test that DependencyFactory returns same ModelSelector instance."""
        factory = DependencyFactory()

        selector1 = factory.get_model_selector()
        selector2 = factory.get_model_selector()

        # Should be same instance (singleton)
        assert selector1 is selector2

    def test_dependency_factory_custom_model_selector(self):
        """Test that DependencyFactory accepts custom ModelSelector."""
        custom_selector = ModelSelector(custom_mappings={
            "custom-task": {
                "quick": "custom-model",
                "standard": "custom-model",
                "thorough": "custom-model"
            }
        })

        factory = DependencyFactory(model_selector_impl=custom_selector)

        selector = factory.get_model_selector()

        assert selector is custom_selector
        assert "custom-task" in selector.model_mappings


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""

    def test_create_validation_system_convenience_function(self):
        """Test create_validation_system creates fully integrated system."""
        system = create_validation_system(project_root=".")

        # Verify all components created
        assert "orchestrator" in system
        assert "critic_integration" in system
        assert "result_aggregator" in system

        # Verify types
        assert isinstance(system["orchestrator"], ValidationOrchestrator)
        assert isinstance(system["critic_integration"], CriticIntegration)
        assert isinstance(system["result_aggregator"], ResultAggregator)

        # Verify integration
        assert system["critic_integration"].orchestrator is system["orchestrator"]
        assert system["result_aggregator"].orchestrator is system["orchestrator"]

    def test_validation_orchestrator_with_all_integrations(self):
        """Test ValidationOrchestrator with all Phase 2 integrations."""
        orchestrator = ValidationOrchestrator(
            project_root=".",
            validators=["code-validator", "doc-validator", "test-validator"],
            default_level="standard"
        )

        # Verify Phase 2A integration (modular structure)
        assert orchestrator is not None
        assert orchestrator.validators == ["code-validator", "doc-validator", "test-validator"]

        # Verify Phase 2D integration (centralized ModelSelector)
        assert orchestrator.model_selector is not None
        assert isinstance(orchestrator.model_selector, ModelSelector)

        # Test model selection works
        model = orchestrator._select_model("code-validator", "thorough")
        assert model == "claude-opus-4-20250514"

    def test_critic_integration_with_factory_and_model_selector(self):
        """Test CriticIntegration with both DependencyFactory and ModelSelector."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Create with default factory
        integration = CriticIntegration(orchestrator)

        # Verify factory integration
        assert integration.factory is not None

        # Verify orchestrator integration
        assert integration.orchestrator is orchestrator

        # Verify orchestrator has ModelSelector
        assert integration.orchestrator.model_selector is not None


class TestBackwardCompatibility:
    """Test that Phase 2 changes maintain backward compatibility."""

    def test_old_validation_orchestrator_import_still_works(self):
        """Test that old import path still works."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation_orchestrator import ValidationOrchestrator as OldOrch

            # Should work
            orchestrator = OldOrch(project_root=".")
            assert orchestrator is not None

    def test_old_and_new_imports_are_same_class(self):
        """Test that old and new imports point to same class."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation import ValidationOrchestrator as NewOrch
            from validation_orchestrator import ValidationOrchestrator as OldOrch

            assert NewOrch is OldOrch

    def test_old_import_validation_result_works(self):
        """Test that old ValidationResult import works."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            from validation_orchestrator import ValidationResult
            from validation import ValidationResult as NewResult

            assert ValidationResult is NewResult


class TestModuleImportOrder:
    """Test that modules can be imported in any order."""

    def test_import_validation_then_protocols_then_utils(self):
        """Test importing in order: validation → protocols → utils."""
        # This should work without circular import errors
        from validation import ValidationOrchestrator
        from protocols import DependencyFactory
        from utils import ModelSelector

        assert all([ValidationOrchestrator, DependencyFactory, ModelSelector])

    def test_import_utils_then_validation_then_protocols(self):
        """Test importing in order: utils → validation → protocols."""
        from utils import ModelSelector
        from validation import ValidationOrchestrator
        from protocols import DependencyFactory

        assert all([ModelSelector, ValidationOrchestrator, DependencyFactory])

    def test_import_protocols_then_utils_then_validation(self):
        """Test importing in order: protocols → utils → validation."""
        from protocols import DependencyFactory
        from utils import ModelSelector
        from validation import ValidationOrchestrator

        assert all([DependencyFactory, ModelSelector, ValidationOrchestrator])


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    def test_scenario_initialize_validation_system(self):
        """Test scenario: Initialize complete validation system."""
        # User wants to set up validation
        system = create_validation_system(
            project_root=".",
            validators=["code-validator", "doc-validator"],
            default_level="standard"
        )

        # Verify system is ready
        assert system["orchestrator"] is not None
        assert system["critic_integration"] is not None
        assert system["result_aggregator"] is not None

        # Verify orchestrator has ModelSelector
        assert system["orchestrator"].model_selector is not None

    def test_scenario_custom_factory_with_mock_critic(self):
        """Test scenario: Testing with mock critic via DependencyFactory."""
        # User wants to test with mock critic
        mock_critic = Mock(spec=CriticProtocol)
        mock_critic.review_code.return_value = {
            "overall_score": 95,
            "findings": [],
            "critics_used": ["mock-critic"]
        }

        # Create custom factory
        factory = DependencyFactory(critic_impl=mock_critic)

        # Create validation system with custom factory
        orchestrator = ValidationOrchestrator(project_root=".")
        integration = CriticIntegration(orchestrator, factory=factory)

        # Verify mock is used
        critic = integration.factory.get_critic_orchestrator()
        assert critic is mock_critic

    def test_scenario_model_selection_for_different_tasks(self):
        """Test scenario: Selecting models for different validation tasks."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Quick validation (uses Haiku)
        quick_model = orchestrator._select_model("code-validator", "quick")
        assert "haiku" in quick_model.lower()

        # Thorough validation (uses Opus)
        thorough_model = orchestrator._select_model("code-validator", "thorough")
        assert "opus" in thorough_model.lower()

        # Documentation (always Sonnet)
        doc_model = orchestrator._select_model("doc-validator", "quick")
        assert "sonnet" in doc_model.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
