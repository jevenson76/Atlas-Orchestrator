"""
Unit Tests for Validation Core

Tests the core validation functionality including:
- ValidationOrchestrator initialization
- Import paths
- Model selection
- Prompt formatting
- Helper methods
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation import ValidationOrchestrator, ValidationResult, ValidationFinding
from validation.interfaces import (
    VALIDATION_MODELS,
    VALIDATION_TEMPERATURES,
    DEFAULT_VALIDATION_LEVEL
)


class TestValidationOrchestratorInit:
    """Test ValidationOrchestrator initialization."""

    def test_init_default_validators(self):
        """Test initialization with default validators."""
        orchestrator = ValidationOrchestrator(project_root=".")

        assert orchestrator.project_root.is_absolute()
        assert orchestrator.default_level == "standard"
        assert "code-validator" in orchestrator.validators
        assert "doc-validator" in orchestrator.validators
        assert "test-validator" in orchestrator.validators

    def test_init_custom_validators(self):
        """Test initialization with custom validators."""
        orchestrator = ValidationOrchestrator(
            project_root=".",
            validators=["code-validator"],
            default_level="quick"
        )

        assert orchestrator.validators == ["code-validator"]
        assert orchestrator.default_level == "quick"

    def test_init_custom_level(self):
        """Test initialization with custom default level."""
        orchestrator = ValidationOrchestrator(
            project_root=".",
            default_level="thorough"
        )

        assert orchestrator.default_level == "thorough"


class TestModelSelection:
    """Test model selection logic."""

    def test_select_model_code_validator_quick(self):
        """Test model selection for code-validator at quick level."""
        orchestrator = ValidationOrchestrator(project_root=".")
        model = orchestrator._select_model("code-validator", "quick")

        assert model == "claude-haiku-4-5-20250611"

    def test_select_model_code_validator_standard(self):
        """Test model selection for code-validator at standard level."""
        orchestrator = ValidationOrchestrator(project_root=".")
        model = orchestrator._select_model("code-validator", "standard")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_code_validator_thorough(self):
        """Test model selection for code-validator at thorough level."""
        orchestrator = ValidationOrchestrator(project_root=".")
        model = orchestrator._select_model("code-validator", "thorough")

        assert model == "claude-opus-4-20250514"

    def test_select_model_doc_validator(self):
        """Test model selection for doc-validator (always Sonnet)."""
        orchestrator = ValidationOrchestrator(project_root=".")

        for level in ["quick", "standard", "thorough"]:
            model = orchestrator._select_model("doc-validator", level)
            assert model == "claude-sonnet-4-5-20250929"


class TestLanguageDetection:
    """Test language detection from file extensions."""

    def test_detect_language_python(self):
        """Test Python file detection."""
        orchestrator = ValidationOrchestrator(project_root=".")

        lang = orchestrator._detect_language(Path("test.py"))
        assert lang == "python"

    def test_detect_language_javascript(self):
        """Test JavaScript file detection."""
        orchestrator = ValidationOrchestrator(project_root=".")

        lang = orchestrator._detect_language(Path("test.js"))
        assert lang == "javascript"

    def test_detect_language_typescript(self):
        """Test TypeScript file detection."""
        orchestrator = ValidationOrchestrator(project_root=".")

        lang = orchestrator._detect_language(Path("test.ts"))
        assert lang == "typescript"

    def test_detect_language_unknown(self):
        """Test unknown file extension."""
        orchestrator = ValidationOrchestrator(project_root=".")

        lang = orchestrator._detect_language(Path("test.xyz"))
        assert lang == "unknown"


class TestValidatorDetection:
    """Test automatic validator detection for files."""

    def test_detect_validators_python_file(self):
        """Test validator detection for Python source file."""
        orchestrator = ValidationOrchestrator(project_root=".")

        validators = orchestrator._detect_validators_for_file(Path("auth.py"))
        assert "code-validator" in validators
        assert "doc-validator" not in validators
        assert "test-validator" not in validators

    def test_detect_validators_test_file(self):
        """Test validator detection for test file."""
        orchestrator = ValidationOrchestrator(project_root=".")

        validators = orchestrator._detect_validators_for_file(Path("test_auth.py"))
        assert "code-validator" in validators
        assert "test-validator" in validators

    def test_detect_validators_markdown_file(self):
        """Test validator detection for markdown file."""
        orchestrator = ValidationOrchestrator(project_root=".")

        validators = orchestrator._detect_validators_for_file(Path("README.md"))
        assert "doc-validator" in validators
        assert "code-validator" not in validators

    def test_detect_validators_readme(self):
        """Test validator detection for README file."""
        orchestrator = ValidationOrchestrator(project_root=".")

        validators = orchestrator._detect_validators_for_file(Path("readme.txt"))
        assert "doc-validator" in validators


class TestExecutionStats:
    """Test execution statistics tracking."""

    def test_initial_stats(self):
        """Test initial stats are zero."""
        orchestrator = ValidationOrchestrator(project_root=".")
        stats = orchestrator.get_execution_stats()

        assert stats["total_validations"] == 0
        assert stats["total_cost_usd"] == 0.0
        assert stats["total_time_seconds"] == 0.0

    def test_reset_stats(self):
        """Test stats can be reset."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Manually set some stats
        orchestrator._execution_stats["total_validations"] = 5
        orchestrator._execution_stats["total_cost"] = 0.5

        # Reset
        orchestrator.reset_stats()
        stats = orchestrator.get_execution_stats()

        assert stats["total_validations"] == 0
        assert stats["total_cost_usd"] == 0.0


class TestPromptFormatting:
    """Test prompt template formatting."""

    def test_format_prompt_basic(self):
        """Test basic prompt formatting."""
        orchestrator = ValidationOrchestrator(project_root=".")

        template = "Validate {language} code in {file_path}"
        context = {"language": "python", "file_path": "auth.py"}

        result = orchestrator._format_prompt(
            prompt_template=template,
            validator_name="code-validator",
            target_content="code here",
            context=context,
            level="standard"
        )

        assert "python" in result
        assert "auth.py" in result

    def test_format_prompt_with_defaults(self):
        """Test prompt formatting with default values."""
        orchestrator = ValidationOrchestrator(project_root=".")

        template = "Language: {language}, Type: {project_type}"
        context = {}

        result = orchestrator._format_prompt(
            prompt_template=template,
            validator_name="code-validator",
            target_content="code",
            context=context,
            level="standard"
        )

        # Should use defaults
        assert "python" in result or "application" in result


class TestCostEstimation:
    """Test API cost estimation."""

    def test_estimate_cost_haiku(self):
        """Test cost estimation for Haiku model."""
        orchestrator = ValidationOrchestrator(project_root=".")

        response = "x" * 1000  # ~250 tokens
        cost = orchestrator._estimate_cost("claude-haiku-4-5-20250611", response)

        assert cost > 0
        assert cost < 0.01  # Haiku is cheap

    def test_estimate_cost_sonnet(self):
        """Test cost estimation for Sonnet model."""
        orchestrator = ValidationOrchestrator(project_root=".")

        response = "x" * 1000  # ~250 tokens
        cost = orchestrator._estimate_cost("claude-sonnet-4-5-20250929", response)

        assert cost > 0
        # Sonnet more expensive than Haiku
        haiku_cost = orchestrator._estimate_cost("claude-haiku-4-5-20250611", response)
        assert cost > haiku_cost

    def test_estimate_cost_opus(self):
        """Test cost estimation for Opus model."""
        orchestrator = ValidationOrchestrator(project_root=".")

        response = "x" * 1000  # ~250 tokens
        cost = orchestrator._estimate_cost("claude-opus-4-20250514", response)

        assert cost > 0
        # Opus most expensive
        sonnet_cost = orchestrator._estimate_cost("claude-sonnet-4-5-20250929", response)
        assert cost > sonnet_cost


class TestRepr:
    """Test string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        orchestrator = ValidationOrchestrator(project_root=".")

        repr_str = repr(orchestrator)
        assert "ValidationOrchestrator" in repr_str
        assert "validators=" in repr_str
        assert "default_level=" in repr_str


class TestConstants:
    """Test that constants are properly defined."""

    def test_validation_models_defined(self):
        """Test VALIDATION_MODELS constant."""
        assert "code-validator" in VALIDATION_MODELS
        assert "doc-validator" in VALIDATION_MODELS
        assert "test-validator" in VALIDATION_MODELS

        # Test code-validator has all levels
        assert "quick" in VALIDATION_MODELS["code-validator"]
        assert "standard" in VALIDATION_MODELS["code-validator"]
        assert "thorough" in VALIDATION_MODELS["code-validator"]

    def test_validation_temperatures_defined(self):
        """Test VALIDATION_TEMPERATURES constant."""
        assert "code-validator" in VALIDATION_TEMPERATURES
        assert "doc-validator" in VALIDATION_TEMPERATURES
        assert "test-validator" in VALIDATION_TEMPERATURES

    def test_default_level(self):
        """Test DEFAULT_VALIDATION_LEVEL constant."""
        assert DEFAULT_VALIDATION_LEVEL in ["quick", "standard", "thorough"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
