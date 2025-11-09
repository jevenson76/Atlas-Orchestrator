"""
Dependency Injection Factory

This module provides a factory for creating implementations of protocol interfaces.
It enables loose coupling by allowing different implementations to be injected
at runtime, and prevents circular dependencies.

Usage:
    from protocols.factory import DependencyFactory

    # Default factory with production implementations
    factory = DependencyFactory()
    critic = factory.get_critic_orchestrator()

    # Factory with custom implementations (for testing)
    factory = DependencyFactory(
        critic_impl=MockCriticOrchestrator(),
        session_impl=MockSessionManager()
    )
"""

from typing import Optional, Dict, Any, Callable
from pathlib import Path
import importlib
import warnings

from protocols import (
    CriticProtocol,
    SessionProtocol,
    ModelSelectionProtocol,
    PromptProtocol
)


class DependencyFactory:
    """
    Factory for creating protocol implementations with dependency injection.

    This factory provides lazy instantiation of dependencies to avoid circular
    imports and allows injection of custom implementations for testing.
    """

    def __init__(
        self,
        critic_impl: Optional[CriticProtocol] = None,
        session_impl: Optional[SessionProtocol] = None,
        model_selector_impl: Optional[ModelSelectionProtocol] = None,
        prompt_impl: Optional[PromptProtocol] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize dependency factory.

        Args:
            critic_impl: Custom critic implementation (for testing)
            session_impl: Custom session manager (for testing)
            model_selector_impl: Custom model selector (for testing)
            prompt_impl: Custom prompt manager (for testing)
            config: Configuration dictionary
        """
        self._critic_impl = critic_impl
        self._session_impl = session_impl
        self._model_selector_impl = model_selector_impl
        self._prompt_impl = prompt_impl
        self._config = config or {}

        # Lazy-loaded singletons
        self._critic_instance: Optional[CriticProtocol] = None
        self._session_instance: Optional[SessionProtocol] = None
        self._model_selector_instance: Optional[ModelSelectionProtocol] = None
        self._prompt_instance: Optional[PromptProtocol] = None

    def get_critic_orchestrator(
        self,
        fresh_instance: bool = False
    ) -> CriticProtocol:
        """
        Get critic orchestrator implementation.

        Args:
            fresh_instance: If True, create new instance instead of singleton

        Returns:
            CriticProtocol implementation
        """
        # Return custom implementation if provided
        if self._critic_impl is not None:
            return self._critic_impl

        # Return singleton unless fresh instance requested
        if not fresh_instance and self._critic_instance is not None:
            return self._critic_instance

        # Lazy import to avoid circular dependency
        try:
            from critic_orchestrator import CriticOrchestrator

            # CriticOrchestrator only accepts api_key parameter
            instance = CriticOrchestrator(
                api_key=self._config.get("api_key", None)
            )

            if not fresh_instance:
                self._critic_instance = instance

            return instance

        except (ImportError, TypeError) as e:
            warnings.warn(
                f"Could not import CriticOrchestrator: {e}. "
                "Returning no-op implementation.",
                RuntimeWarning
            )
            return NoOpCriticOrchestrator()

    def get_session_manager(
        self,
        fresh_instance: bool = False
    ) -> SessionProtocol:
        """
        Get session manager implementation.

        Args:
            fresh_instance: If True, create new instance instead of singleton

        Returns:
            SessionProtocol implementation
        """
        # Return custom implementation if provided
        if self._session_impl is not None:
            return self._session_impl

        # Return singleton unless fresh instance requested
        if not fresh_instance and self._session_instance is not None:
            return self._session_instance

        # Lazy import to avoid circular dependency
        try:
            from session_manager import EnhancedSessionManager

            instance = EnhancedSessionManager()

            if not fresh_instance:
                self._session_instance = instance

            return instance

        except ImportError as e:
            warnings.warn(
                f"Could not import EnhancedSessionManager: {e}. "
                "Returning no-op implementation.",
                RuntimeWarning
            )
            # Cache no-op instance for singleton behavior
            instance = NoOpSessionManager()
            if not fresh_instance:
                self._session_instance = instance
            return instance

    def get_model_selector(
        self,
        fresh_instance: bool = False
    ) -> ModelSelectionProtocol:
        """
        Get model selector implementation.

        Args:
            fresh_instance: If True, create new instance instead of singleton

        Returns:
            ModelSelectionProtocol implementation
        """
        # Return custom implementation if provided
        if self._model_selector_impl is not None:
            return self._model_selector_impl

        # Return singleton unless fresh instance requested
        if not fresh_instance and self._model_selector_instance is not None:
            return self._model_selector_instance

        # Use centralized ModelSelector (Phase 2D)
        from utils import ModelSelector
        instance = ModelSelector()

        if not fresh_instance:
            self._model_selector_instance = instance

        return instance

    def get_prompt_manager(
        self,
        fresh_instance: bool = False
    ) -> PromptProtocol:
        """
        Get prompt manager implementation.

        Args:
            fresh_instance: If True, create new instance instead of singleton

        Returns:
            PromptProtocol implementation
        """
        # Return custom implementation if provided
        if self._prompt_impl is not None:
            return self._prompt_impl

        # Return singleton unless fresh instance requested
        if not fresh_instance and self._prompt_instance is not None:
            return self._prompt_instance

        # Lazy import to avoid circular dependency
        try:
            from prompt_manager import PromptManager

            instance = PromptManager(
                prompts_dir=self._config.get("prompts_dir", "./prompts")
            )

            if not fresh_instance:
                self._prompt_instance = instance

            return instance

        except ImportError as e:
            warnings.warn(
                f"Could not import PromptManager: {e}. "
                "Returning no-op implementation.",
                RuntimeWarning
            )
            return NoOpPromptManager()

    def reset_singletons(self) -> None:
        """Reset all singleton instances (useful for testing)."""
        self._critic_instance = None
        self._session_instance = None
        self._model_selector_instance = None
        self._prompt_instance = None

    def configure(self, config: Dict[str, Any]) -> None:
        """Update factory configuration."""
        self._config.update(config)


# No-op implementations for graceful degradation


class NoOpCriticOrchestrator:
    """No-op critic implementation that returns empty results."""

    def review_code(self, code_snippet: str, **kwargs) -> Dict[str, Any]:
        """Return empty review."""
        warnings.warn("Using no-op critic orchestrator", RuntimeWarning)
        return {
            "critics_used": [],
            "overall_score": 50,
            "findings": [],
            "summary": "Critic orchestrator not available"
        }

    def list_available_critics(self) -> list:
        return []

    def get_critic_description(self, critic_name: str) -> str:
        return "No description available"


class NoOpSessionManager:
    """No-op session manager that provides minimal functionality."""

    def get_session_id(self) -> str:
        return "no-op-session"

    def start_session(self, session_type: str, metadata=None) -> str:
        return "no-op-session"

    def end_session(self, session_id: str, summary=None) -> None:
        pass

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        return {"total_calls": 0, "total_cost": 0.0}


# SimpleModelSelector removed in Phase 2D - now using centralized utils.ModelSelector


class NoOpPromptManager:
    """No-op prompt manager that returns empty prompts."""

    def get_prompt(self, prompt_name: str, version=None) -> str:
        return f"Prompt '{prompt_name}' not available"

    def format_prompt(
        self,
        prompt_name: str,
        context: Dict[str, Any],
        version=None
    ) -> str:
        return f"Formatted prompt '{prompt_name}' not available"

    def list_prompts(self) -> list:
        return []


# Global default factory instance
_default_factory: Optional[DependencyFactory] = None


def get_default_factory() -> DependencyFactory:
    """Get global default factory instance."""
    global _default_factory
    if _default_factory is None:
        _default_factory = DependencyFactory()
    return _default_factory


def set_default_factory(factory: DependencyFactory) -> None:
    """Set global default factory (useful for testing)."""
    global _default_factory
    _default_factory = factory


def reset_default_factory() -> None:
    """Reset global default factory."""
    global _default_factory
    _default_factory = None
