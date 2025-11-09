"""
Utilities Package - Shared Utilities for Multi-Agent System

This package provides shared utilities used across all orchestrators.

Modules:
    model_selector - Centralized model selection and cost estimation

Usage:
    from utils import ModelSelector

    selector = ModelSelector()
    model = selector.select_model("code-validation", "thorough")
    temp = selector.get_temperature("code-validation")
    cost = selector.estimate_cost(model, input_tokens=1000, output_tokens=500)
"""

from utils.model_selector import ModelSelector

__version__ = "1.0.0"

__all__ = [
    "ModelSelector",
    "__version__"
]
