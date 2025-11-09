"""
Model selection logic for the Claude library.

Centralizes all model selection decisions to ensure consistency
and optimize for cost/performance across the entire system.
"""

from .constants import Models


class ModelSelector:
    """Intelligent model selection based on task requirements."""

    @staticmethod
    def select(complexity: str, cost_sensitive: bool = False) -> str:
        """
        Select the appropriate model based on task complexity.

        Args:
            complexity: Task complexity level ('high', 'medium', 'low')
            cost_sensitive: If True, prefer cheaper models when possible

        Returns:
            Model identifier string for the selected model
        """
        if cost_sensitive:
            return Models.GEMINI_FLASH  # Fast, cheap alternative

        model_map = {
            "high": Models.OPUS_4,  # High complexity - ULTRATHINK required
            "medium": Models.SONNET,  # Balanced tasks - Claude required
            "low": Models.GEMINI_FLASH  # Simple, fast tasks - can use Gemini
        }

        return model_map.get(complexity, Models.SONNET)