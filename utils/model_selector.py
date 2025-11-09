"""
Centralized Model Selection and Cost Estimation

This module provides centralized model selection logic used across all orchestrators.
It ensures consistent model selection, temperature settings, and cost estimation
throughout the multi-agent system.

Architecture:
    - Single source of truth for model mappings
    - Task-based model selection (code-validation, documentation, critique, etc.)
    - Complexity-based selection (quick/standard/thorough)
    - Accurate cost estimation based on latest pricing

Usage:
    from utils import ModelSelector

    selector = ModelSelector()

    # Select model based on task and complexity
    model = selector.select_model("code-validation", "thorough")
    # Returns: "claude-opus-4-20250514"

    # Get recommended temperature
    temp = selector.get_temperature("code-validation")
    # Returns: 0.2

    # Estimate cost
    cost = selector.estimate_cost(model, input_tokens=1000, output_tokens=500)
    # Returns: 0.0525 (in USD)
"""

from typing import Literal, Dict, Any, Optional
import warnings

# Type aliases
TaskType = Literal[
    "code-validation",
    "documentation",
    "test-validation",
    "critique",
    "security-analysis",
    "architecture-review",
    "performance-analysis",
    "general"
]

ComplexityLevel = Literal["quick", "standard", "thorough"]


class ModelSelector:
    """
    Centralized model selection and cost estimation.

    Provides consistent model selection across all orchestrators based on
    task type and complexity level.
    """

    # Model mappings per task type and complexity level
    # Structure: {task_type: {complexity_level: model_name}}
    MODEL_MAPPINGS: Dict[TaskType, Dict[ComplexityLevel, str]] = {
        "code-validation": {
            "quick": "claude-haiku-4-5-20250611",
            "standard": "claude-sonnet-4-5-20250929",
            "thorough": "claude-opus-4-20250514"
        },
        "documentation": {
            # Documentation benefits from Sonnet's balance across all levels
            "quick": "claude-sonnet-4-5-20250929",
            "standard": "claude-sonnet-4-5-20250929",
            "thorough": "claude-sonnet-4-5-20250929"
        },
        "test-validation": {
            "quick": "claude-haiku-4-5-20250611",
            "standard": "claude-sonnet-4-5-20250929",
            "thorough": "claude-opus-4-20250514"
        },
        "critique": {
            # Critics ALWAYS use Opus for unbiased deep analysis
            "quick": "claude-opus-4-20250514",
            "standard": "claude-opus-4-20250514",
            "thorough": "claude-opus-4-20250514"
        },
        "security-analysis": {
            # Security requires thoroughness even at quick level
            "quick": "claude-sonnet-4-5-20250929",
            "standard": "claude-opus-4-20250514",
            "thorough": "claude-opus-4-20250514"
        },
        "architecture-review": {
            "quick": "claude-sonnet-4-5-20250929",
            "standard": "claude-sonnet-4-5-20250929",
            "thorough": "claude-opus-4-20250514"
        },
        "performance-analysis": {
            "quick": "claude-haiku-4-5-20250611",
            "standard": "claude-sonnet-4-5-20250929",
            "thorough": "claude-opus-4-20250514"
        },
        "general": {
            "quick": "claude-haiku-4-5-20250611",
            "standard": "claude-sonnet-4-5-20250929",
            "thorough": "claude-opus-4-20250514"
        }
    }

    # Temperature settings per task type
    # Lower temperature = more deterministic, higher = more creative
    TEMPERATURES: Dict[TaskType, float] = {
        "code-validation": 0.2,      # Deterministic for validation
        "documentation": 0.3,         # Slightly creative for docs
        "test-validation": 0.2,       # Deterministic for test validation
        "critique": 0.2,              # Deterministic for objective critique
        "security-analysis": 0.1,     # Very deterministic for security
        "architecture-review": 0.3,   # Balanced for architecture
        "performance-analysis": 0.2,  # Deterministic for perf analysis
        "general": 0.2                # Default
    }

    # Cost per 1M tokens (as of 2025-01-09)
    # Source: https://www.anthropic.com/pricing
    COST_PER_1M_TOKENS: Dict[str, Dict[str, float]] = {
        "claude-haiku-4-5-20250611": {
            "input": 0.25,
            "output": 1.25
        },
        "claude-sonnet-4-5-20250929": {
            "input": 3.0,
            "output": 15.0
        },
        "claude-opus-4-20250514": {
            "input": 15.0,
            "output": 75.0
        }
    }

    # Default values
    DEFAULT_TASK_TYPE: TaskType = "general"
    DEFAULT_COMPLEXITY: ComplexityLevel = "standard"
    DEFAULT_TEMPERATURE: float = 0.2

    def __init__(self, custom_mappings: Optional[Dict] = None):
        """
        Initialize ModelSelector.

        Args:
            custom_mappings: Optional custom model mappings to override defaults
        """
        self.model_mappings = self.MODEL_MAPPINGS.copy()
        if custom_mappings:
            self.model_mappings.update(custom_mappings)

    def select_model(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Select appropriate model based on task type and complexity.

        Args:
            task_type: Type of task (e.g., "code-validation", "critique")
            complexity: Complexity level (quick/standard/thorough)
            context: Optional context for future smart selection

        Returns:
            Model name (e.g., "claude-sonnet-4-5-20250929")

        Examples:
            >>> selector = ModelSelector()
            >>> selector.select_model("code-validation", "quick")
            'claude-haiku-4-5-20250611'
            >>> selector.select_model("critique", "standard")
            'claude-opus-4-20250514'
        """
        # Get task mapping
        task_mapping = self.model_mappings.get(
            task_type,
            self.model_mappings[self.DEFAULT_TASK_TYPE]
        )

        # Get model for complexity level
        model = task_mapping.get(
            complexity,
            task_mapping[self.DEFAULT_COMPLEXITY]
        )

        return model

    def get_temperature(
        self,
        task_type: TaskType,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Get recommended temperature for task type.

        Args:
            task_type: Type of task
            context: Optional context for future smart temperature selection

        Returns:
            Temperature value (0.0-1.0)

        Examples:
            >>> selector = ModelSelector()
            >>> selector.get_temperature("code-validation")
            0.2
            >>> selector.get_temperature("documentation")
            0.3
        """
        return self.TEMPERATURES.get(task_type, self.DEFAULT_TEMPERATURE)

    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate API cost in USD for given model and token counts.

        Args:
            model_name: Model name (e.g., "claude-sonnet-4-5-20250929")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD

        Examples:
            >>> selector = ModelSelector()
            >>> selector.estimate_cost("claude-haiku-4-5-20250611", 1000, 500)
            0.000875
            >>> selector.estimate_cost("claude-opus-4-20250514", 1000, 500)
            0.0525
        """
        # Get cost structure for model
        costs = self.COST_PER_1M_TOKENS.get(model_name)

        if not costs:
            warnings.warn(
                f"Cost data not available for model '{model_name}'. Returning 0.0",
                RuntimeWarning
            )
            return 0.0

        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]

        return input_cost + output_cost

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).

        Uses the rule of thumb: ~4 characters per token for English text.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count

        Examples:
            >>> selector = ModelSelector()
            >>> selector.estimate_tokens("Hello world!")
            3
        """
        # Rough approximation: 4 characters per token
        return len(text) // 4

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Args:
            model_name: Model name

        Returns:
            Dictionary with model information

        Examples:
            >>> selector = ModelSelector()
            >>> info = selector.get_model_info("claude-sonnet-4-5-20250929")
            >>> info["input_cost_per_1m"]
            3.0
        """
        costs = self.COST_PER_1M_TOKENS.get(model_name)

        if not costs:
            return {
                "model_name": model_name,
                "input_cost_per_1m": None,
                "output_cost_per_1m": None,
                "available": False
            }

        return {
            "model_name": model_name,
            "input_cost_per_1m": costs["input"],
            "output_cost_per_1m": costs["output"],
            "available": True
        }

    def list_available_models(self) -> list[str]:
        """
        List all available models.

        Returns:
            List of model names

        Examples:
            >>> selector = ModelSelector()
            >>> models = selector.list_available_models()
            >>> "claude-sonnet-4-5-20250929" in models
            True
        """
        return list(self.COST_PER_1M_TOKENS.keys())

    def compare_costs(
        self,
        models: list[str],
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """
        Compare costs across multiple models.

        Args:
            models: List of model names to compare
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary mapping model name to estimated cost

        Examples:
            >>> selector = ModelSelector()
            >>> costs = selector.compare_costs(
            ...     ["claude-haiku-4-5-20250611", "claude-sonnet-4-5-20250929"],
            ...     1000, 500
            ... )
            >>> costs["claude-haiku-4-5-20250611"] < costs["claude-sonnet-4-5-20250929"]
            True
        """
        return {
            model: self.estimate_cost(model, input_tokens, output_tokens)
            for model in models
        }

    def recommend_model(
        self,
        task_type: TaskType,
        budget_usd: Optional[float] = None,
        estimated_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recommend best model based on budget and requirements.

        Args:
            task_type: Type of task
            budget_usd: Optional budget constraint in USD
            estimated_tokens: Optional estimated total tokens (input + output)

        Returns:
            Dictionary with recommendation

        Examples:
            >>> selector = ModelSelector()
            >>> rec = selector.recommend_model("code-validation", budget_usd=0.01)
            >>> rec["recommended_model"]
            'claude-haiku-4-5-20250611'
        """
        # Get all complexity levels for task
        task_mapping = self.model_mappings.get(task_type, {})
        models = {
            complexity: self.select_model(task_type, complexity)
            for complexity in ["quick", "standard", "thorough"]
        }

        # If no budget constraint, recommend standard
        if budget_usd is None:
            return {
                "recommended_model": models["standard"],
                "complexity": "standard",
                "reason": "No budget constraint - using standard complexity"
            }

        # Estimate costs for each complexity level
        # Assume 50/50 split between input and output tokens
        if estimated_tokens:
            input_tokens = estimated_tokens // 2
            output_tokens = estimated_tokens // 2
        else:
            # Default estimate: 2000 total tokens
            input_tokens = 1000
            output_tokens = 1000

        costs = {
            complexity: self.estimate_cost(model, input_tokens, output_tokens)
            for complexity, model in models.items()
        }

        # Find highest complexity that fits budget
        for complexity in ["thorough", "standard", "quick"]:
            if costs[complexity] <= budget_usd:
                return {
                    "recommended_model": models[complexity],
                    "complexity": complexity,
                    "estimated_cost": costs[complexity],
                    "budget": budget_usd,
                    "reason": f"Best quality within budget (${costs[complexity]:.6f} <= ${budget_usd})"
                }

        # If even quick exceeds budget, warn and return quick anyway
        return {
            "recommended_model": models["quick"],
            "complexity": "quick",
            "estimated_cost": costs["quick"],
            "budget": budget_usd,
            "reason": f"WARNING: Even quick exceeds budget (${costs['quick']:.6f} > ${budget_usd})"
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ModelSelector(tasks={len(self.model_mappings)}, "
            f"models={len(self.COST_PER_1M_TOKENS)})"
        )


# Singleton instance for convenience
_default_selector: Optional[ModelSelector] = None


def get_default_selector() -> ModelSelector:
    """Get global default ModelSelector instance."""
    global _default_selector
    if _default_selector is None:
        _default_selector = ModelSelector()
    return _default_selector


def reset_default_selector() -> None:
    """Reset global default ModelSelector (useful for testing)."""
    global _default_selector
    _default_selector = None
