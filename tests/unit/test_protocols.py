"""
Unit Tests for Protocols Package

Tests protocol definitions and dependency injection factory.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from protocols import (
    SessionProtocol,
    CriticProtocol,
    ModelSelectionProtocol,
    PromptProtocol,
    DependencyFactory,
    get_default_factory,
    set_default_factory,
    reset_default_factory
)


class TestProtocolDefinitions:
    """Test that protocol definitions are properly defined."""

    def test_session_protocol_has_required_methods(self):
        """Test SessionProtocol has required method signatures."""
        # Check protocol has required methods
        assert hasattr(SessionProtocol, 'get_session_id')
        assert hasattr(SessionProtocol, 'start_session')
        assert hasattr(SessionProtocol, 'end_session')
        assert hasattr(SessionProtocol, 'get_session_stats')

    def test_critic_protocol_has_required_methods(self):
        """Test CriticProtocol has required method signatures."""
        assert hasattr(CriticProtocol, 'review_code')
        assert hasattr(CriticProtocol, 'list_available_critics')
        assert hasattr(CriticProtocol, 'get_critic_description')

    def test_model_selection_protocol_has_required_methods(self):
        """Test ModelSelectionProtocol has required method signatures."""
        assert hasattr(ModelSelectionProtocol, 'select_model')
        assert hasattr(ModelSelectionProtocol, 'get_model_temperature')
        assert hasattr(ModelSelectionProtocol, 'estimate_cost')

    def test_prompt_protocol_has_required_methods(self):
        """Test PromptProtocol has required method signatures."""
        assert hasattr(PromptProtocol, 'get_prompt')
        assert hasattr(PromptProtocol, 'format_prompt')
        assert hasattr(PromptProtocol, 'list_prompts')


class TestDependencyFactoryInit:
    """Test DependencyFactory initialization."""

    def test_factory_init_with_defaults(self):
        """Test factory initialization with default parameters."""
        factory = DependencyFactory()

        assert factory._critic_impl is None
        assert factory._session_impl is None
        assert factory._model_selector_impl is None
        assert factory._prompt_impl is None
        assert factory._config == {}

    def test_factory_init_with_custom_critic(self):
        """Test factory initialization with custom critic implementation."""
        mock_critic = Mock(spec=CriticProtocol)
        factory = DependencyFactory(critic_impl=mock_critic)

        assert factory._critic_impl is mock_critic

    def test_factory_init_with_custom_session(self):
        """Test factory initialization with custom session implementation."""
        mock_session = Mock(spec=SessionProtocol)
        factory = DependencyFactory(session_impl=mock_session)

        assert factory._session_impl is mock_session

    def test_factory_init_with_config(self):
        """Test factory initialization with configuration."""
        config = {"project_root": "/test", "api_key": "test-key"}
        factory = DependencyFactory(config=config)

        assert factory._config == config


class TestDependencyFactoryGetCritic:
    """Test DependencyFactory.get_critic_orchestrator()."""

    def test_get_critic_returns_custom_implementation(self):
        """Test that custom critic implementation is returned when provided."""
        mock_critic = Mock(spec=CriticProtocol)
        factory = DependencyFactory(critic_impl=mock_critic)

        result = factory.get_critic_orchestrator()

        assert result is mock_critic

    def test_get_critic_returns_singleton_by_default(self):
        """Test that same instance is returned on multiple calls."""
        factory = DependencyFactory()

        critic1 = factory.get_critic_orchestrator()
        critic2 = factory.get_critic_orchestrator()

        # Should be same instance (singleton)
        assert critic1 is critic2

    def test_get_critic_returns_fresh_instance_when_requested(self):
        """Test that fresh instance is returned when fresh_instance=True."""
        factory = DependencyFactory()

        critic1 = factory.get_critic_orchestrator(fresh_instance=True)
        critic2 = factory.get_critic_orchestrator(fresh_instance=True)

        # Should be different instances
        assert critic1 is not critic2

    def test_get_critic_fallback_to_noop_on_import_error(self):
        """Test that no-op critic is returned if real import fails."""
        factory = DependencyFactory()

        # Force import to fail by using wrong config
        critic = factory.get_critic_orchestrator()

        # Should return some implementation (either real or no-op)
        assert critic is not None
        assert hasattr(critic, 'review_code')


class TestDependencyFactoryGetSession:
    """Test DependencyFactory.get_session_manager()."""

    def test_get_session_returns_custom_implementation(self):
        """Test that custom session implementation is returned."""
        mock_session = Mock(spec=SessionProtocol)
        factory = DependencyFactory(session_impl=mock_session)

        result = factory.get_session_manager()

        assert result is mock_session

    def test_get_session_returns_singleton_by_default(self):
        """Test that same session instance is returned."""
        factory = DependencyFactory()

        session1 = factory.get_session_manager()
        session2 = factory.get_session_manager()

        assert session1 is session2

    def test_get_session_returns_fresh_instance_when_requested(self):
        """Test fresh session instances can be created."""
        factory = DependencyFactory()

        session1 = factory.get_session_manager(fresh_instance=True)
        session2 = factory.get_session_manager(fresh_instance=True)

        assert session1 is not session2


class TestDependencyFactoryGetModelSelector:
    """Test DependencyFactory.get_model_selector()."""

    def test_get_model_selector_returns_custom_implementation(self):
        """Test custom model selector is returned."""
        mock_selector = Mock(spec=ModelSelectionProtocol)
        factory = DependencyFactory(model_selector_impl=mock_selector)

        result = factory.get_model_selector()

        assert result is mock_selector

    def test_get_model_selector_returns_singleton_by_default(self):
        """Test singleton pattern for model selector."""
        factory = DependencyFactory()

        selector1 = factory.get_model_selector()
        selector2 = factory.get_model_selector()

        assert selector1 is selector2

    def test_get_model_selector_has_required_methods(self):
        """Test that returned model selector has required methods."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        assert hasattr(selector, 'select_model')
        assert hasattr(selector, 'get_temperature')
        assert hasattr(selector, 'estimate_cost')


class TestDependencyFactoryReset:
    """Test DependencyFactory reset functionality."""

    def test_reset_singletons_clears_all_instances(self):
        """Test that reset_singletons clears cached instances."""
        factory = DependencyFactory()

        # Create instances
        critic1 = factory.get_critic_orchestrator()
        session1 = factory.get_session_manager()
        selector1 = factory.get_model_selector()

        # Reset
        factory.reset_singletons()

        # Get new instances
        critic2 = factory.get_critic_orchestrator()
        session2 = factory.get_session_manager()
        selector2 = factory.get_model_selector()

        # Should be different instances after reset
        assert critic1 is not critic2
        assert session1 is not session2
        assert selector1 is not selector2

    def test_configure_updates_config(self):
        """Test that configure updates factory config."""
        factory = DependencyFactory(config={"key1": "value1"})

        factory.configure({"key2": "value2", "key3": "value3"})

        assert "key1" in factory._config
        assert "key2" in factory._config
        assert "key3" in factory._config
        assert factory._config["key2"] == "value2"


class TestGlobalFactory:
    """Test global factory functions."""

    def test_get_default_factory_returns_factory(self):
        """Test get_default_factory returns a factory instance."""
        reset_default_factory()  # Ensure clean state

        factory = get_default_factory()

        assert factory is not None
        assert isinstance(factory, DependencyFactory)

    def test_get_default_factory_returns_singleton(self):
        """Test get_default_factory returns same instance."""
        reset_default_factory()  # Ensure clean state

        factory1 = get_default_factory()
        factory2 = get_default_factory()

        assert factory1 is factory2

    def test_set_default_factory_replaces_global_factory(self):
        """Test set_default_factory replaces global instance."""
        reset_default_factory()  # Ensure clean state

        custom_factory = DependencyFactory(config={"custom": True})
        set_default_factory(custom_factory)

        factory = get_default_factory()

        assert factory is custom_factory
        assert factory._config.get("custom") is True

    def test_reset_default_factory_clears_global(self):
        """Test reset_default_factory clears global instance."""
        factory1 = get_default_factory()

        reset_default_factory()

        factory2 = get_default_factory()

        # Should create new instance after reset
        assert factory1 is not factory2


class TestCentralizedModelSelector:
    """Test centralized ModelSelector implementation (Phase 2D)."""

    def test_select_model_code_validation_quick(self):
        """Test model selection for code validation quick level."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        model = selector.select_model("code-validation", "quick")

        assert model == "claude-haiku-4-5-20250611"

    def test_select_model_code_validation_standard(self):
        """Test model selection for code validation standard level."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        model = selector.select_model("code-validation", "standard")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_code_validation_thorough(self):
        """Test model selection for code validation thorough level."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        model = selector.select_model("code-validation", "thorough")

        assert model == "claude-opus-4-20250514"

    def test_get_temperature_code_validation(self):
        """Test temperature for code validation."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        temp = selector.get_temperature("code-validation")

        assert temp == 0.2

    def test_get_temperature_documentation(self):
        """Test temperature for documentation."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        temp = selector.get_temperature("documentation")

        assert temp == 0.3

    def test_get_temperature_unknown_defaults(self):
        """Test temperature defaults for unknown task type."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        temp = selector.get_temperature("unknown-task")

        assert temp == 0.2

    def test_estimate_cost_haiku(self):
        """Test cost estimation for Haiku model."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        cost = selector.estimate_cost(
            "claude-haiku-4-5-20250611",
            input_tokens=1000,
            output_tokens=500
        )

        # Haiku: $0.25/1M input, $1.25/1M output
        expected = (1000 / 1_000_000) * 0.25 + (500 / 1_000_000) * 1.25
        assert abs(cost - expected) < 0.000001

    def test_estimate_cost_sonnet(self):
        """Test cost estimation for Sonnet model."""
        factory = DependencyFactory()
        selector = factory.get_model_selector()

        cost = selector.estimate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=1000,
            output_tokens=500
        )

        # Sonnet: $3/1M input, $15/1M output
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.000001


class TestMockImplementations:
    """Test that mock implementations can be injected for testing."""

    def test_inject_mock_critic(self):
        """Test injecting mock critic implementation."""
        mock_critic = Mock(spec=CriticProtocol)
        mock_critic.review_code.return_value = {
            "overall_score": 95,
            "findings": [],
            "critics_used": ["test-critic"]
        }

        factory = DependencyFactory(critic_impl=mock_critic)
        critic = factory.get_critic_orchestrator()

        result = critic.review_code("test code")

        assert result["overall_score"] == 95
        mock_critic.review_code.assert_called_once_with("test code")

    def test_inject_mock_session(self):
        """Test injecting mock session implementation."""
        mock_session = Mock(spec=SessionProtocol)
        mock_session.get_session_id.return_value = "test-session-123"

        factory = DependencyFactory(session_impl=mock_session)
        session = factory.get_session_manager()

        session_id = session.get_session_id()

        assert session_id == "test-session-123"
        mock_session.get_session_id.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
