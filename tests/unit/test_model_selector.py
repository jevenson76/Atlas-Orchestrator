"""
Unit Tests for Centralized Model Selection

Tests the utils.ModelSelector class for model selection, temperature settings,
cost estimation, and budget-based recommendations.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import ModelSelector
from utils.model_selector import get_default_selector, reset_default_selector


class TestModelSelectorInit:
    """Test ModelSelector initialization."""

    def test_init_default(self):
        """Test default initialization."""
        selector = ModelSelector()

        assert selector is not None
        assert hasattr(selector, 'model_mappings')
        assert hasattr(selector, 'MODEL_MAPPINGS')
        assert hasattr(selector, 'TEMPERATURES')
        assert hasattr(selector, 'COST_PER_1M_TOKENS')

    def test_init_with_custom_mappings(self):
        """Test initialization with custom mappings."""
        custom = {
            "custom-task": {
                "quick": "custom-model",
                "standard": "custom-model",
                "thorough": "custom-model"
            }
        }

        selector = ModelSelector(custom_mappings=custom)

        assert "custom-task" in selector.model_mappings


class TestModelSelection:
    """Test model selection logic."""

    def test_select_model_code_validation_quick(self):
        """Test selecting model for code validation at quick level."""
        selector = ModelSelector()
        model = selector.select_model("code-validation", "quick")

        assert model == "claude-haiku-4-5-20250611"

    def test_select_model_code_validation_standard(self):
        """Test selecting model for code validation at standard level."""
        selector = ModelSelector()
        model = selector.select_model("code-validation", "standard")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_code_validation_thorough(self):
        """Test selecting model for code validation at thorough level."""
        selector = ModelSelector()
        model = selector.select_model("code-validation", "thorough")

        assert model == "claude-opus-4-20250514"

    def test_select_model_documentation(self):
        """Test that documentation always uses Sonnet."""
        selector = ModelSelector()

        for level in ["quick", "standard", "thorough"]:
            model = selector.select_model("documentation", level)
            assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_critique(self):
        """Test that critique always uses Opus (for unbiased analysis)."""
        selector = ModelSelector()

        for level in ["quick", "standard", "thorough"]:
            model = selector.select_model("critique", level)
            assert model == "claude-opus-4-20250514"

    def test_select_model_security_quick_uses_sonnet(self):
        """Test that security analysis uses Sonnet even at quick level."""
        selector = ModelSelector()
        model = selector.select_model("security-analysis", "quick")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_security_thorough_uses_opus(self):
        """Test that security analysis uses Opus at thorough level."""
        selector = ModelSelector()
        model = selector.select_model("security-analysis", "thorough")

        assert model == "claude-opus-4-20250514"

    def test_select_model_unknown_task_uses_general(self):
        """Test that unknown task type falls back to general."""
        selector = ModelSelector()
        model = selector.select_model("unknown-task", "standard")

        # Should fall back to general mapping
        assert model == "claude-sonnet-4-5-20250929"


class TestTemperatureSelection:
    """Test temperature selection logic."""

    def test_get_temperature_code_validation(self):
        """Test temperature for code validation."""
        selector = ModelSelector()
        temp = selector.get_temperature("code-validation")

        assert temp == 0.2

    def test_get_temperature_documentation(self):
        """Test temperature for documentation."""
        selector = ModelSelector()
        temp = selector.get_temperature("documentation")

        assert temp == 0.3

    def test_get_temperature_security(self):
        """Test temperature for security analysis (most deterministic)."""
        selector = ModelSelector()
        temp = selector.get_temperature("security-analysis")

        assert temp == 0.1

    def test_get_temperature_critique(self):
        """Test temperature for critique."""
        selector = ModelSelector()
        temp = selector.get_temperature("critique")

        assert temp == 0.2

    def test_get_temperature_unknown_defaults(self):
        """Test that unknown task types get default temperature."""
        selector = ModelSelector()
        temp = selector.get_temperature("unknown-task")

        assert temp == 0.2


class TestCostEstimation:
    """Test cost estimation logic."""

    def test_estimate_cost_haiku(self):
        """Test cost estimation for Haiku."""
        selector = ModelSelector()
        cost = selector.estimate_cost(
            "claude-haiku-4-5-20250611",
            input_tokens=1000,
            output_tokens=500
        )

        # Haiku: $0.25/1M input, $1.25/1M output
        expected = (1000 / 1_000_000) * 0.25 + (500 / 1_000_000) * 1.25
        assert abs(cost - expected) < 0.000001

    def test_estimate_cost_sonnet(self):
        """Test cost estimation for Sonnet."""
        selector = ModelSelector()
        cost = selector.estimate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=1000,
            output_tokens=500
        )

        # Sonnet: $3/1M input, $15/1M output
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.000001

    def test_estimate_cost_opus(self):
        """Test cost estimation for Opus."""
        selector = ModelSelector()
        cost = selector.estimate_cost(
            "claude-opus-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        # Opus: $15/1M input, $75/1M output
        expected = (1000 / 1_000_000) * 15.0 + (500 / 1_000_000) * 75.0
        assert abs(cost - expected) < 0.000001

    def test_estimate_cost_unknown_model_returns_zero(self):
        """Test that unknown model returns 0.0 cost."""
        selector = ModelSelector()
        cost = selector.estimate_cost(
            "unknown-model",
            input_tokens=1000,
            output_tokens=500
        )

        assert cost == 0.0

    def test_estimate_cost_opus_more_expensive_than_sonnet(self):
        """Test that Opus is more expensive than Sonnet."""
        selector = ModelSelector()

        opus_cost = selector.estimate_cost("claude-opus-4-20250514", 1000, 500)
        sonnet_cost = selector.estimate_cost("claude-sonnet-4-5-20250929", 1000, 500)

        assert opus_cost > sonnet_cost

    def test_estimate_cost_sonnet_more_expensive_than_haiku(self):
        """Test that Sonnet is more expensive than Haiku."""
        selector = ModelSelector()

        sonnet_cost = selector.estimate_cost("claude-sonnet-4-5-20250929", 1000, 500)
        haiku_cost = selector.estimate_cost("claude-haiku-4-5-20250611", 1000, 500)

        assert sonnet_cost > haiku_cost


class TestTokenEstimation:
    """Test token estimation logic."""

    def test_estimate_tokens_simple(self):
        """Test token estimation for simple text."""
        selector = ModelSelector()
        tokens = selector.estimate_tokens("Hello world!")

        # ~4 characters per token: 12 / 4 = 3
        assert tokens == 3

    def test_estimate_tokens_longer(self):
        """Test token estimation for longer text."""
        selector = ModelSelector()
        text = "This is a longer text that should have more tokens."
        tokens = selector.estimate_tokens(text)

        # Actual len(text) = 51, 51 // 4 = 12
        assert tokens == 12

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string."""
        selector = ModelSelector()
        tokens = selector.estimate_tokens("")

        assert tokens == 0


class TestModelInfo:
    """Test model information retrieval."""

    def test_get_model_info_haiku(self):
        """Test getting model info for Haiku."""
        selector = ModelSelector()
        info = selector.get_model_info("claude-haiku-4-5-20250611")

        assert info["model_name"] == "claude-haiku-4-5-20250611"
        assert info["input_cost_per_1m"] == 0.25
        assert info["output_cost_per_1m"] == 1.25
        assert info["available"] is True

    def test_get_model_info_sonnet(self):
        """Test getting model info for Sonnet."""
        selector = ModelSelector()
        info = selector.get_model_info("claude-sonnet-4-5-20250929")

        assert info["model_name"] == "claude-sonnet-4-5-20250929"
        assert info["input_cost_per_1m"] == 3.0
        assert info["output_cost_per_1m"] == 15.0
        assert info["available"] is True

    def test_get_model_info_unknown(self):
        """Test getting model info for unknown model."""
        selector = ModelSelector()
        info = selector.get_model_info("unknown-model")

        assert info["model_name"] == "unknown-model"
        assert info["input_cost_per_1m"] is None
        assert info["output_cost_per_1m"] is None
        assert info["available"] is False


class TestListModels:
    """Test listing available models."""

    def test_list_available_models(self):
        """Test listing available models."""
        selector = ModelSelector()
        models = selector.list_available_models()

        assert "claude-haiku-4-5-20250611" in models
        assert "claude-sonnet-4-5-20250929" in models
        assert "claude-opus-4-20250514" in models
        assert len(models) == 3


class TestCompareCosts:
    """Test cost comparison across models."""

    def test_compare_costs(self):
        """Test comparing costs across multiple models."""
        selector = ModelSelector()
        costs = selector.compare_costs(
            ["claude-haiku-4-5-20250611", "claude-sonnet-4-5-20250929"],
            input_tokens=1000,
            output_tokens=500
        )

        assert "claude-haiku-4-5-20250611" in costs
        assert "claude-sonnet-4-5-20250929" in costs
        assert costs["claude-haiku-4-5-20250611"] < costs["claude-sonnet-4-5-20250929"]

    def test_compare_costs_all_models(self):
        """Test comparing costs for all models."""
        selector = ModelSelector()
        models = selector.list_available_models()
        costs = selector.compare_costs(models, input_tokens=1000, output_tokens=500)

        # Verify ordering: Haiku < Sonnet < Opus
        assert costs["claude-haiku-4-5-20250611"] < costs["claude-sonnet-4-5-20250929"]
        assert costs["claude-sonnet-4-5-20250929"] < costs["claude-opus-4-20250514"]


class TestRecommendModel:
    """Test model recommendation based on budget."""

    def test_recommend_model_no_budget_uses_standard(self):
        """Test that no budget constraint recommends standard."""
        selector = ModelSelector()
        rec = selector.recommend_model("code-validation")

        assert rec["complexity"] == "standard"
        assert rec["recommended_model"] == "claude-sonnet-4-5-20250929"
        assert "No budget constraint" in rec["reason"]

    def test_recommend_model_high_budget_uses_thorough(self):
        """Test that high budget recommends thorough (Opus)."""
        selector = ModelSelector()
        rec = selector.recommend_model("code-validation", budget_usd=1.0)

        assert rec["complexity"] == "thorough"
        assert rec["recommended_model"] == "claude-opus-4-20250514"

    def test_recommend_model_medium_budget_uses_standard(self):
        """Test that medium budget recommends standard (Sonnet)."""
        selector = ModelSelector()
        # Sonnet with 1000 input + 1000 output ≈ $0.018, need higher budget
        rec = selector.recommend_model("code-validation", budget_usd=0.02)

        assert rec["complexity"] == "standard"
        assert rec["recommended_model"] == "claude-sonnet-4-5-20250929"

    def test_recommend_model_low_budget_uses_quick(self):
        """Test that low budget recommends quick (Haiku)."""
        selector = ModelSelector()
        rec = selector.recommend_model("code-validation", budget_usd=0.001)

        assert rec["complexity"] == "quick"
        assert rec["recommended_model"] == "claude-haiku-4-5-20250611"

    def test_recommend_model_very_low_budget_warns(self):
        """Test that very low budget returns warning."""
        selector = ModelSelector()
        rec = selector.recommend_model("code-validation", budget_usd=0.0001)

        assert rec["complexity"] == "quick"
        assert "WARNING" in rec["reason"]


class TestRepr:
    """Test string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        selector = ModelSelector()
        repr_str = repr(selector)

        assert "ModelSelector" in repr_str
        assert "tasks=" in repr_str
        assert "models=" in repr_str


class TestGlobalSelector:
    """Test global selector functions."""

    def test_get_default_selector_returns_selector(self):
        """Test get_default_selector returns ModelSelector."""
        reset_default_selector()  # Ensure clean state

        selector = get_default_selector()

        assert selector is not None
        assert isinstance(selector, ModelSelector)

    def test_get_default_selector_returns_singleton(self):
        """Test get_default_selector returns same instance."""
        reset_default_selector()  # Ensure clean state

        selector1 = get_default_selector()
        selector2 = get_default_selector()

        assert selector1 is selector2

    def test_reset_default_selector_creates_new_instance(self):
        """Test reset_default_selector creates new instance."""
        selector1 = get_default_selector()

        reset_default_selector()

        selector2 = get_default_selector()

        assert selector1 is not selector2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
