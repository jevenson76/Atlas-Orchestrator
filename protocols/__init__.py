"""
Protocol Definitions for Dependency Injection

This module defines Protocol interfaces used throughout the validation system
to enable loose coupling and testability through dependency injection.

Key Protocols:
- CriticProtocol: Interface for critic orchestration
- SessionProtocol: Interface for session management
- ModelSelectionProtocol: Interface for model selection logic

Usage:
    from protocols import CriticProtocol, DependencyFactory

    factory = DependencyFactory()
    critic = factory.get_critic_orchestrator()
"""

from typing import Protocol, runtime_checkable, Optional, Dict, Any, List
from pathlib import Path

__version__ = "1.0.0"


@runtime_checkable
class SessionProtocol(Protocol):
    """Protocol for session management across agents."""

    def get_session_id(self) -> str:
        """Get current session ID."""
        ...

    def start_session(self, session_type: str, metadata: Optional[Dict] = None) -> str:
        """Start a new session."""
        ...

    def end_session(self, session_id: str, summary: Optional[str] = None) -> None:
        """End a session."""
        ...

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        ...


@runtime_checkable
class CriticProtocol(Protocol):
    """Protocol for critic orchestration."""

    def review_code(
        self,
        code_snippet: str,
        context: Optional[Dict[str, Any]] = None,
        critics: Optional[List[str]] = None,
        level: str = "standard",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review code using specified critics.

        Args:
            code_snippet: Code to review
            context: Additional context for review
            critics: List of critic names to use
            level: Review depth (quick/standard/thorough)
            session_id: Optional session ID for tracking

        Returns:
            Dict containing critic review results and overall score
        """
        ...

    def list_available_critics(self) -> List[str]:
        """List all available critic types."""
        ...

    def get_critic_description(self, critic_name: str) -> str:
        """Get description of a specific critic."""
        ...


@runtime_checkable
class ModelSelectionProtocol(Protocol):
    """Protocol for intelligent model selection."""

    def select_model(
        self,
        task_type: str,
        complexity_level: str = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Select appropriate model for a task.

        Args:
            task_type: Type of task (e.g., "code-validation", "documentation")
            complexity_level: quick/standard/thorough
            context: Additional context for selection

        Returns:
            Model name (e.g., "claude-sonnet-4-5-20250929")
        """
        ...

    def get_model_temperature(self, task_type: str) -> float:
        """Get recommended temperature for task type."""
        ...

    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost in USD for API call."""
        ...


@runtime_checkable
class PromptProtocol(Protocol):
    """Protocol for prompt management."""

    def get_prompt(self, prompt_name: str, version: Optional[str] = None) -> str:
        """Get prompt template by name."""
        ...

    def format_prompt(
        self,
        prompt_name: str,
        context: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """Format prompt template with context."""
        ...

    def list_prompts(self) -> List[str]:
        """List all available prompt templates."""
        ...


# Import factory components
from protocols.factory import (
    DependencyFactory,
    get_default_factory,
    set_default_factory,
    reset_default_factory
)

# Export all protocols and factory
__all__ = [
    # Protocols
    "SessionProtocol",
    "CriticProtocol",
    "ModelSelectionProtocol",
    "PromptProtocol",
    # Factory
    "DependencyFactory",
    "get_default_factory",
    "set_default_factory",
    "reset_default_factory",
    # Metadata
    "__version__"
]
