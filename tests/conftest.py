"""
Pytest Configuration for Validation Tests

This file configures pytest for the validation test suite.
"""

import sys
from pathlib import Path

# Add parent directory to Python path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests across multiple components"
    )
    config.addinivalue_line(
        "markers", "backward_compat: Backward compatibility tests"
    )
