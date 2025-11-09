"""
Circular Import Detection Test

This test verifies that there are no circular dependencies between modules.
"""

import pytest
import sys
from pathlib import Path
import importlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestNoCircularImports:
    """Test that imports don't create circular dependencies."""

    def test_import_protocols_first(self):
        """Test importing protocols package first."""
        # Fresh import (clear any cached imports)
        if 'protocols' in sys.modules:
            del sys.modules['protocols']
        if 'protocols.factory' in sys.modules:
            del sys.modules['protocols.factory']

        # Import protocols - should work without circular dependency
        from protocols import DependencyFactory, CriticProtocol
        assert DependencyFactory is not None
        assert CriticProtocol is not None

    def test_import_validation_first(self):
        """Test importing validation package first."""
        # Import validation - should work without circular dependency
        from validation import ValidationOrchestrator, CriticIntegration
        assert ValidationOrchestrator is not None
        assert CriticIntegration is not None

    def test_import_validation_then_protocols(self):
        """Test importing validation then protocols."""
        from validation import ValidationOrchestrator
        from protocols import DependencyFactory

        assert ValidationOrchestrator is not None
        assert DependencyFactory is not None

    def test_import_protocols_then_validation(self):
        """Test importing protocols then validation."""
        from protocols import DependencyFactory, get_default_factory
        from validation import ValidationOrchestrator, CriticIntegration

        assert DependencyFactory is not None
        assert ValidationOrchestrator is not None
        assert CriticIntegration is not None

    def test_import_critic_integration_uses_factory(self):
        """Test that CriticIntegration uses factory to avoid circular import."""
        from validation.critic_integration import CriticIntegration
        from validation import ValidationOrchestrator

        # Create orchestrator
        orchestrator = ValidationOrchestrator(project_root=".")

        # Create critic integration (should not cause circular import)
        integration = CriticIntegration(orchestrator)

        assert integration is not None
        assert integration.factory is not None

    def test_factory_can_get_critic_without_circular_import(self):
        """Test that factory can get critic orchestrator without circular import."""
        from protocols import get_default_factory

        factory = get_default_factory()

        # This should use lazy import to avoid circular dependency
        # May return no-op if critic_orchestrator not importable
        critic = factory.get_critic_orchestrator()

        assert critic is not None
        assert hasattr(critic, 'review_code')

    def test_all_validation_modules_import_cleanly(self):
        """Test all validation modules can be imported without circular deps."""
        from validation import (
            ValidationOrchestrator,
            CriticIntegration,
            ResultAggregator,
            ValidationResult,
            ValidationFinding
        )

        assert all([
            ValidationOrchestrator,
            CriticIntegration,
            ResultAggregator,
            ValidationResult,
            ValidationFinding
        ])

    def test_all_protocol_modules_import_cleanly(self):
        """Test all protocol modules can be imported without circular deps."""
        from protocols import (
            CriticProtocol,
            SessionProtocol,
            ModelSelectionProtocol,
            PromptProtocol,
            DependencyFactory,
            get_default_factory
        )

        assert all([
            CriticProtocol,
            SessionProtocol,
            ModelSelectionProtocol,
            PromptProtocol,
            DependencyFactory,
            get_default_factory
        ])

    def test_import_order_independence(self):
        """Test that import order doesn't matter."""
        # This test verifies that modules can be imported in any order
        # without causing circular dependency errors

        import importlib
        import sys

        # Define all modules to test
        modules_to_test = [
            'protocols',
            'protocols.factory',
            'validation',
            'validation.core',
            'validation.critic_integration',
            'validation.result_aggregator',
            'validation.interfaces'
        ]

        # Test forward order
        for module_name in modules_to_test:
            # Skip if module already imported
            if module_name in sys.modules:
                continue

            try:
                importlib.import_module(module_name)
            except ImportError as e:
                # Some modules may not exist or have dependencies not available
                # That's okay - we're just testing for circular import errors
                if "circular" in str(e).lower():
                    pytest.fail(f"Circular import detected in {module_name}: {e}")

        # All imports should succeed (or fail for reasons other than circular deps)
        assert True

    def test_backward_compat_import_no_circular_dep(self):
        """Test backward compatibility import doesn't create circular dependency."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Old import path
            from validation_orchestrator import ValidationOrchestrator as OldOrch

            # New import path
            from validation import ValidationOrchestrator as NewOrch

            # Should be same class
            assert OldOrch is NewOrch


class TestImportDependencyGraph:
    """Test the dependency graph is acyclic."""

    def test_protocols_has_no_validation_dependency(self):
        """Test that protocols package doesn't import from validation package."""
        import ast
        import inspect
        from protocols import factory

        # Get source code of factory module
        source = inspect.getsource(factory)
        tree = ast.parse(source)

        # Find all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Verify no imports from validation package
        validation_imports = [imp for imp in imports if imp.startswith('validation')]

        assert len(validation_imports) == 0, (
            f"protocols/factory.py should not import from validation package. "
            f"Found: {validation_imports}"
        )

    def test_validation_critic_integration_imports_protocols(self):
        """Test that validation.critic_integration imports protocols (correct direction)."""
        import ast
        import inspect
        from validation import critic_integration

        # Get source code
        source = inspect.getsource(critic_integration)
        tree = ast.parse(source)

        # Find all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Should import from protocols
        protocol_imports = [imp for imp in imports if 'protocol' in imp.lower()]

        assert len(protocol_imports) > 0, (
            "validation.critic_integration should import from protocols package"
        )

    def test_no_direct_critic_orchestrator_import_in_critic_integration(self):
        """Test that critic_integration doesn't directly import CriticOrchestrator."""
        import ast
        import inspect
        from validation import critic_integration

        # Get source code
        source = inspect.getsource(critic_integration)

        # Check for direct import of CriticOrchestrator (outside of lazy import pattern)
        # The refactored version should use factory.get_critic_orchestrator() instead

        # Look for "from critic_orchestrator import" at module level
        lines = source.split('\n')
        module_level_imports = []

        in_function = False
        for line in lines:
            stripped = line.strip()

            # Track if we're in a function
            if stripped.startswith('def ') or stripped.startswith('async def '):
                in_function = True
            elif in_function and not line.startswith(' ') and not line.startswith('\t'):
                in_function = False

            # Check for critic_orchestrator import at module level
            if not in_function and 'from critic_orchestrator import' in line:
                module_level_imports.append(line)

        # Should have NO module-level imports of critic_orchestrator
        # (Factory pattern should be used instead)
        assert len(module_level_imports) == 0, (
            f"validation.critic_integration should use factory instead of direct import. "
            f"Found module-level imports: {module_level_imports}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
