# Protocol-Based Architecture Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Active (Phase 2B)

---

## Table of Contents

1. [Overview](#overview)
2. [Why Protocols?](#why-protocols)
3. [Protocol Definitions](#protocol-definitions)
4. [Dependency Injection Factory](#dependency-injection-factory)
5. [Architecture Benefits](#architecture-benefits)
6. [Usage Patterns](#usage-patterns)
7. [Testing Guide](#testing-guide)
8. [Migration Guide](#migration-guide)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [References](#references)

---

## Overview

The ZTE multi-agent system uses **Python Protocols (PEP 544)** for dependency inversion, breaking circular dependencies while maintaining type safety and clean architecture.

### The Problem We Solved

**Before Phase 2B**, we had circular imports:
- `validation_orchestrator` needed `critic_orchestrator`
- `critic_orchestrator` needed `validation_orchestrator`
- **Result:** Import errors and tight coupling

**After Phase 2B**, we use protocols:
- Both modules depend on abstract `Protocol` interfaces
- No circular dependencies in the import graph
- Clean, testable, flexible architecture

### Architecture at a Glance

```
        protocols/
       /          \
      ↓            ↓
validation    critic_orchestrator
      \            /
       ↓          ↓
    protocols/factory.py
    (runtime wiring)
```

---

## Why Protocols?

### The Circular Dependency Problem

**Classic Circular Import:**
```python
# validation_orchestrator.py
from critic_orchestrator import CriticOrchestrator  # ❌

class ValidationOrchestrator:
    def __init__(self):
        self.critic = CriticOrchestrator()

# critic_orchestrator.py
from validation_orchestrator import ValidationOrchestrator  # ❌

class CriticOrchestrator:
    def validate_critique(self, critique: str):
        validator = ValidationOrchestrator()
```

**Result:**
```
ImportError: cannot import name 'CriticOrchestrator' from partially initialized module
(most likely due to a circular import)
```

### The Protocol Solution

**Protocols break the circle by introducing abstraction:**

```python
# protocols/__init__.py (no concrete imports!)
from typing import Protocol

class CriticProtocol(Protocol):
    """Abstract critic interface."""
    def critique(self, data: Any) -> List[ValidationResult]: ...

class ValidationProtocol(Protocol):
    """Abstract validation interface."""
    def validate(self, data: Any) -> List[ValidationResult]: ...
```

**Now each module depends on protocols, not each other:**

```python
# validation/core.py
from protocols import CriticProtocol  # ✅ No circular import

class ValidationOrchestrator:
    def __init__(self, critic: Optional[CriticProtocol] = None):
        self._critic = critic

# critic_orchestrator.py
from protocols import ValidationProtocol  # ✅ No circular import

class CriticOrchestrator:
    def __init__(self, validator: Optional[ValidationProtocol] = None):
        self._validator = validator
```

### Why Not Other Solutions?

| Solution | Why Not? |
|----------|----------|
| **Lazy Imports** | Breaks type checking, hidden dependencies |
| **Merge Files** | Creates god file, violates SRP |
| **Abstract Base Classes** | Requires inheritance, less flexible |
| **Event Bus** | Over-engineered, debugging nightmare |
| **Service Locator** | Anti-pattern, hidden dependencies |

**Protocols win because:**
- ✅ No circular imports
- ✅ Type safety maintained
- ✅ No inheritance required (structural typing)
- ✅ Easy to test (simple mock objects)
- ✅ Pythonic (PEP 544 standard)

---

## Protocol Definitions

All protocols are defined in `protocols/__init__.py` with **zero concrete imports**.

### ValidationProtocol

```python
from typing import Protocol, runtime_checkable, Any, Optional, List

@runtime_checkable
class ValidationProtocol(Protocol):
    """
    Abstract interface for validation operations.

    Implementations must provide validation logic for code, documentation,
    and test files with configurable validation levels.

    Example implementations:
    - validation.ValidationOrchestrator
    - validation.ValidationEngine
    """

    def validate(
        self,
        data: Any,
        config: Optional[ValidationConfig] = None
    ) -> List[ValidationResult]:
        """
        Validate data and return results.

        Args:
            data: Data to validate (code, docs, tests)
            config: Optional validation configuration

        Returns:
            List of validation results
        """
        ...

    def aggregate_results(
        self,
        results: List[ValidationResult]
    ) -> AggregatedResult:
        """
        Aggregate multiple validation results.

        Args:
            results: List of validation results

        Returns:
            Aggregated summary
        """
        ...
```

**Implementations:**
- `validation.ValidationOrchestrator` - Main implementation
- `validation.ValidationEngine` - Core validation logic

### CriticProtocol

```python
@runtime_checkable
class CriticProtocol(Protocol):
    """
    Abstract interface for critic operations.

    Implementations must provide multi-perspective critique functionality
    with quality assessment and scoring.

    Example implementations:
    - critic_orchestrator.CriticOrchestrator
    """

    def critique(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """
        Generate critique from multiple perspectives.

        Args:
            data: Data to critique (code, docs, design)
            context: Optional context (file path, language, etc.)

        Returns:
            List of critique results
        """
        ...

    def assess_quality(
        self,
        critique: str,
        criteria: Optional[List[str]] = None
    ) -> QualityScore:
        """
        Assess quality of a critique.

        Args:
            critique: Critique text to assess
            criteria: Optional quality criteria

        Returns:
            Quality score (0.0-1.0)
        """
        ...
```

**Implementations:**
- `critic_orchestrator.CriticOrchestrator` - Main implementation

### OrchestratorProtocol

```python
@runtime_checkable
class OrchestratorProtocol(Protocol):
    """
    Abstract interface for orchestration operations.

    Implementations must provide workflow execution, agent coordination,
    and result aggregation with support for multiple execution modes.

    Example implementations:
    - orchestrator.Orchestrator (base class)
    - specialized_roles_orchestrator.SpecializedRolesOrchestrator
    - progressive_enhancement_orchestrator.ProgressiveEnhancementOrchestrator
    """

    def execute(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute orchestrated workflow.

        Args:
            input_data: Input data for orchestration

        Returns:
            Workflow results with metadata
        """
        ...

    async def execute_async(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute orchestrated workflow asynchronously.

        Args:
            input_data: Input data for orchestration

        Returns:
            Workflow results with metadata
        """
        ...

    def get_agent_results(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get results from all agents.

        Returns:
            Dictionary mapping agent names to their results
        """
        ...

    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics from all agents.

        Returns:
            Dictionary mapping agent names to their metrics
        """
        ...
```

**Implementations:**
- `orchestrator.Orchestrator` - Base orchestrator class
- `specialized_roles_orchestrator.SpecializedRolesOrchestrator`
- `progressive_enhancement_orchestrator.ProgressiveEnhancementOrchestrator`

**Execution Modes:**
```python
class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"    # Run tasks one by one
    PARALLEL = "parallel"        # Run all tasks simultaneously
    ADAPTIVE = "adaptive"        # Choose based on dependencies
    ITERATIVE = "iterative"      # Run with refinement loops
```

**Usage:**
```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Create agents
agents = [
    SubAgent(role="researcher", model="claude-sonnet-4-5-20250929"),
    SubAgent(role="analyst", model="claude-sonnet-4-5-20250929"),
]

# Create orchestrator via factory
orch = DependencyFactory.create_orchestrator(
    agents=agents,
    mode="sequential"
)

# Execute workflow
result = orch.execute({"task": "Research AI safety"})
```

**Complete System Integration:**
```python
# Create orchestrator with validator and critic
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="sequential",
    config={
        "validation_level": "thorough",
        "enable_critics": True
    }
)

# All components are wired together
result = orch.execute({"task": "Build feature"})
```

**See Also:**
- **ORCHESTRATOR_PROTOCOL_GUIDE.md** - Comprehensive orchestrator documentation
- `orchestrator.py` - Base implementation with SubAgent class
- `ExecutionMode` enum for workflow strategies

### Supporting Types

```python
from dataclasses import dataclass
from typing import TypedDict, Literal

@dataclass
class ValidationResult:
    """Single validation finding."""
    level: Literal["error", "warning", "info", "success"]
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class QualityScore:
    """Quality assessment score."""
    value: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    criteria_scores: Dict[str, float] = field(default_factory=dict)

class ValidationConfig(TypedDict, total=False):
    """Validation configuration."""
    level: Literal["quick", "standard", "thorough"]
    strict_mode: bool
    enable_critics: bool
    max_critics: int
```

---

## Dependency Injection Factory

The `DependencyFactory` encapsulates component creation and dependency wiring.

### Factory Class

```python
# protocols/factory.py
from typing import Optional, Tuple, Dict, Any
from protocols import ValidationProtocol, CriticProtocol

class DependencyFactory:
    """
    Factory for creating and wiring components with dependency injection.

    This factory handles:
    - Component instantiation
    - Bidirectional dependency wiring
    - Configuration management
    - Error handling
    """

    @staticmethod
    def create_validation_orchestrator(
        critic: Optional[CriticProtocol] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ValidationProtocol:
        """
        Create validation orchestrator with optional critic injection.

        Args:
            critic: Optional critic to inject
            config: Optional configuration

        Returns:
            Configured validation orchestrator
        """
        from validation.core import ValidationOrchestrator

        orchestrator = ValidationOrchestrator(config=config)

        if critic is not None:
            orchestrator.set_critic(critic)

        return orchestrator

    @staticmethod
    def create_critic_orchestrator(
        validator: Optional[ValidationProtocol] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> CriticProtocol:
        """
        Create critic orchestrator with optional validator injection.

        Args:
            validator: Optional validator to inject
            config: Optional configuration

        Returns:
            Configured critic orchestrator
        """
        from critic_orchestrator import CriticOrchestrator

        orchestrator = CriticOrchestrator(config=config)

        if validator is not None:
            orchestrator.set_validator(validator)

        return orchestrator

    @staticmethod
    def create_wired_system(
        config: Optional[Dict[str, Any]] = None
    ) -> Tuple[ValidationProtocol, CriticProtocol]:
        """
        Create fully wired validation system with bidirectional dependencies.

        This is the recommended way to create a validation system. It ensures
        both components are properly wired together.

        Args:
            config: Optional configuration for both components

        Returns:
            Tuple of (validator, critic) with dependencies wired

        Example:
            >>> validator, critic = DependencyFactory.create_wired_system()
            >>> results = validator.validate(code)
        """
        # Create both components without dependencies
        validator = DependencyFactory.create_validation_orchestrator(config=config)
        critic = DependencyFactory.create_critic_orchestrator(config=config)

        # Wire bidirectional dependencies
        validator.set_critic(critic)
        critic.set_validator(validator)

        return validator, critic

    @staticmethod
    def create_orchestrator(
        agents: List[SubAgent],
        mode: str = "sequential",
        validator: Optional[ValidationProtocol] = None,
        critic: Optional[CriticProtocol] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> OrchestratorProtocol:
        """
        Create orchestrator with optional validator/critic injection.

        Args:
            agents: List of SubAgent instances
            mode: Execution mode (sequential, parallel, adaptive, iterative)
            validator: Optional validator to inject
            critic: Optional critic to inject
            config: Optional configuration

        Returns:
            Configured orchestrator

        Example:
            >>> from orchestrator import SubAgent
            >>> agents = [SubAgent(role="test", model="claude-haiku-4-20250514")]
            >>> orch = DependencyFactory.create_orchestrator(agents=agents)
            >>> result = orch.execute({"task": "Process data"})
        """
        from orchestrator import Orchestrator, ExecutionMode

        orch = Orchestrator(
            name=config.get("name", "Orchestrator") if config else "Orchestrator",
            mode=ExecutionMode[mode.upper()],
            max_workers=config.get("max_workers", 5) if config else 5
        )

        for agent in agents:
            orch.add_agent(agent.role, agent)

        if validator is not None and hasattr(orch, 'set_validator'):
            orch.set_validator(validator)

        if critic is not None and hasattr(orch, 'set_critic'):
            orch.set_critic(critic)

        return orch

    @staticmethod
    def create_complete_system(
        agents: List[SubAgent],
        mode: str = "sequential",
        config: Optional[Dict[str, Any]] = None
    ) -> Tuple[OrchestratorProtocol, ValidationProtocol, CriticProtocol]:
        """
        Create complete orchestration system with validator and critic.

        This creates a fully integrated system with all components wired together.

        Args:
            agents: List of SubAgent instances
            mode: Execution mode
            config: Optional configuration for all components

        Returns:
            Tuple of (orchestrator, validator, critic) with dependencies wired

        Example:
            >>> from orchestrator import SubAgent
            >>> agents = [SubAgent(role="test", model="claude-haiku-4-20250514")]
            >>> orch, validator, critic = DependencyFactory.create_complete_system(agents)
            >>> result = orch.execute({"task": "Build feature"})
        """
        # Create all components
        validator = DependencyFactory.create_validation_orchestrator(config=config)
        critic = DependencyFactory.create_critic_orchestrator(config=config)
        orchestrator = DependencyFactory.create_orchestrator(
            agents=agents,
            mode=mode,
            validator=validator,
            critic=critic,
            config=config
        )

        # Wire bidirectional dependencies
        validator.set_critic(critic)
        critic.set_validator(validator)

        return orchestrator, validator, critic
```

### Configuration Options

```python
config = {
    # Validation settings
    "strict_mode": True,              # Fail on warnings
    "enable_critics": True,           # Enable critic integration
    "validation_level": "thorough",   # quick | standard | thorough

    # Critic settings
    "max_critics": 3,                 # Max parallel critics
    "critic_perspectives": [          # Which critics to use
        "security-critic",
        "performance-critic",
        "architecture-critic"
    ],

    # Quality settings
    "quality_threshold": 90,          # Min quality score (0-100)
    "confidence_threshold": 0.8,      # Min confidence (0.0-1.0)

    # Performance settings
    "timeout_seconds": 30,            # Max execution time
    "retry_on_failure": True,         # Auto-retry failed operations
    "max_retries": 3                  # Max retry attempts
}

validator, critic = DependencyFactory.create_wired_system(config=config)
```

---

## Architecture Benefits

### 1. No Circular Dependencies

**Import Graph is Now a DAG (Directed Acyclic Graph):**

```
protocols/__init__.py (pure types)
    ├─→ typing (stdlib)
    └─→ dataclasses (stdlib)

validation/core.py
    └─→ protocols (CriticProtocol)

critic_orchestrator.py
    └─→ protocols (ValidationProtocol)

protocols/factory.py (wiring only)
    ├─→ validation.core
    ├─→ critic_orchestrator
    └─→ protocols
```

**Verification:**
```bash
cd /home/jevenson/.claude/lib
python3 -c "from validation.core import ValidationOrchestrator; from critic_orchestrator import CriticOrchestrator; print('✅ No circular import')"
```

### 2. Type Safety Maintained

**Static Type Checking Works:**

```python
from protocols import ValidationProtocol

def process_data(validator: ValidationProtocol, data: str) -> List[ValidationResult]:
    """Type checker knows validator has validate() method."""
    return validator.validate(data)  # ✅ Type-checked
```

**Type Checkers Validate Protocol Conformance:**

```bash
$ mypy validation/ critic_orchestrator.py protocols/
Success: no issues found in 15 source files
```

### 3. Improved Testability

**No Mock Framework Needed:**

```python
class MockCritic:
    """Test double that satisfies CriticProtocol (no inheritance needed)."""

    def critique(self, data: Any, context=None) -> List[ValidationResult]:
        return [ValidationResult(
            level="info",
            message="Mock critique",
            suggestion="Use mock for testing"
        )]

    def assess_quality(self, critique: str, criteria=None) -> QualityScore:
        return QualityScore(value=0.9, confidence=1.0)

# Simple, fast tests
validator = DependencyFactory.create_validation_orchestrator(critic=MockCritic())
results = validator.validate(test_code)
assert len(results) > 0
```

### 4. Flexibility

**Easy to Swap Implementations:**

```python
# Production: Use full critic orchestrator
validator.set_critic(CriticOrchestrator())

# Performance: Use fast critic (reduced analysis)
validator.set_critic(FastCritic())

# Privacy: Use local LLM critic
validator.set_critic(LocalLLMCritic())

# A/B Testing: Compare implementations
validator_a.set_critic(CriticV1())
validator_b.set_critic(CriticV2())
```

### 5. Clear Contracts

**Protocols Document Exact Interface Requirements:**

```python
@runtime_checkable
class CriticProtocol(Protocol):
    """
    Interface for critique operations.

    Implementations must provide:
    - critique(): Create perspective-specific critique
    - assess_quality(): Score critique quality (0.0-1.0)

    All implementations must satisfy these exact method signatures.
    """
```

### 6. Runtime Validation

**Runtime Checks for Protocol Conformance:**

```python
from protocols import CriticProtocol

def set_critic(self, critic: CriticProtocol) -> None:
    """Set critic with runtime validation."""
    if not isinstance(critic, CriticProtocol):
        raise TypeError(
            f"Expected CriticProtocol, got {type(critic).__name__}. "
            f"Ensure implementation has critique() and assess_quality() methods."
        )
    self._critic = critic
```

---

## Usage Patterns

### Pattern 1: Basic Usage (Recommended)

```python
from protocols.factory import DependencyFactory

# Create fully wired system
validator, critic = DependencyFactory.create_wired_system()

# Use validation
results = validator.validate(code_string)
for result in results:
    print(f"{result.level}: {result.message}")

# Use critic
critiques = critic.critique(code_string, context={"file": "app.py"})
for critique in critiques:
    print(f"{critique.message}")
```

### Pattern 2: Custom Configuration

```python
config = {
    "strict_mode": True,
    "enable_critics": True,
    "max_critics": 5,
    "quality_threshold": 95
}

validator, critic = DependencyFactory.create_wired_system(config=config)
```

### Pattern 3: Independent Components

```python
# Create validator without critic
validator = DependencyFactory.create_validation_orchestrator()

# Use for basic validation
results = validator.validate(code)

# Add critic later if needed
critic = DependencyFactory.create_critic_orchestrator()
validator.set_critic(critic)
```

### Pattern 4: Custom Implementations

```python
class CustomCritic:
    """Custom critic implementation satisfying CriticProtocol."""

    def critique(self, data: Any, context=None) -> List[ValidationResult]:
        # Custom critique logic
        return [ValidationResult(level="info", message="Custom critique")]

    def assess_quality(self, critique: str, criteria=None) -> QualityScore:
        # Custom quality assessment
        return QualityScore(value=0.85, confidence=0.9)

# Use custom implementation
custom_critic = CustomCritic()
validator = DependencyFactory.create_validation_orchestrator(critic=custom_critic)
```

### Pattern 5: Multiple Validators

```python
# Create multiple validators with different configs
quick_validator, _ = DependencyFactory.create_wired_system({
    "validation_level": "quick"
})

thorough_validator, _ = DependencyFactory.create_wired_system({
    "validation_level": "thorough"
})

# Use appropriate validator based on context
if is_production:
    results = thorough_validator.validate(code)
else:
    results = quick_validator.validate(code)
```

---

## Testing Guide

### Unit Testing with Protocols

**Test validators independently:**

```python
def test_validator_basic_functionality():
    """Test validator without critic dependency."""
    validator = DependencyFactory.create_validation_orchestrator()

    code = "def hello(): print('world')"
    results = validator.validate(code)

    assert isinstance(results, list)
    assert all(isinstance(r, ValidationResult) for r in results)
```

**Test with mock critic:**

```python
class MockCritic:
    def critique(self, data, context=None):
        return [ValidationResult(level="info", message="mock")]

    def assess_quality(self, critique, criteria=None):
        return QualityScore(value=0.9, confidence=1.0)

def test_validator_with_mock_critic():
    """Test validator with mock critic."""
    mock_critic = MockCritic()
    validator = DependencyFactory.create_validation_orchestrator(critic=mock_critic)

    results = validator.validate("test code")
    assert len(results) > 0
```

### Integration Testing

**Test full system wiring:**

```python
def test_wired_system_integration():
    """Test that factory wires components correctly."""
    validator, critic = DependencyFactory.create_wired_system()

    # Validator should have critic
    assert hasattr(validator, '_critic')
    assert validator._critic is not None

    # Critic should have validator
    assert hasattr(critic, '_validator')
    assert critic._validator is not None
```

**Test bidirectional communication:**

```python
def test_bidirectional_communication():
    """Test validator and critic can communicate."""
    validator, critic = DependencyFactory.create_wired_system()

    code = "def test(): pass"

    # Validator uses critic
    validation_results = validator.validate(code)

    # Critic uses validator
    critique_results = critic.critique(code)

    assert validation_results is not None
    assert critique_results is not None
```

### Protocol Conformance Testing

**Test implementations satisfy protocols:**

```python
from protocols import ValidationProtocol, CriticProtocol

def test_validation_orchestrator_conforms():
    """Test ValidationOrchestrator satisfies ValidationProtocol."""
    from validation.core import ValidationOrchestrator

    validator = ValidationOrchestrator()
    assert isinstance(validator, ValidationProtocol)

def test_critic_orchestrator_conforms():
    """Test CriticOrchestrator satisfies CriticProtocol."""
    from critic_orchestrator import CriticOrchestrator

    critic = CriticOrchestrator()
    assert isinstance(critic, CriticProtocol)
```

---

## Migration Guide

### For Library Users

**Old Pattern (Still Works with Warnings):**

```python
from validation_orchestrator import ValidationOrchestrator
from critic_orchestrator import CriticOrchestrator

validation = ValidationOrchestrator()
critic = CriticOrchestrator()
# Manual wiring if needed
```

**New Pattern (Recommended):**

```python
from protocols.factory import DependencyFactory

validation, critic = DependencyFactory.create_wired_system()
```

**Benefits of Migration:**
- No manual wiring needed
- Guaranteed correct initialization
- Easier to test
- Better type hints
- No deprecation warnings

### For Library Developers

**Adding New Protocols:**

1. **Define protocol in `protocols/__init__.py`:**

```python
@runtime_checkable
class MyNewProtocol(Protocol):
    """Protocol for my new feature."""

    def my_method(self, data: Any) -> Result:
        """My method docstring."""
        ...
```

2. **Implement in your module:**

```python
from protocols import MyNewProtocol

class MyImplementation:
    """Implements MyNewProtocol."""

    def my_method(self, data: Any) -> Result:
        # Implementation here
        pass
```

3. **Add factory method:**

```python
# protocols/factory.py

@staticmethod
def create_my_component(
    config: Optional[Dict[str, Any]] = None
) -> MyNewProtocol:
    """Create my component."""
    from my_module import MyImplementation
    return MyImplementation(config=config)
```

4. **Add tests:**

```python
def test_my_implementation_conforms():
    """Test my implementation satisfies protocol."""
    from protocols import MyNewProtocol
    from my_module import MyImplementation

    instance = MyImplementation()
    assert isinstance(instance, MyNewProtocol)
```

**Using Protocols in Your Module:**

```python
from typing import Optional
from protocols import ValidationProtocol

class MyComponent:
    """My component that depends on validation."""

    def __init__(self, validator: Optional[ValidationProtocol] = None):
        """Initialize with optional validator injection."""
        self._validator = validator

    def set_validator(self, validator: ValidationProtocol) -> None:
        """Set validator (runtime injection)."""
        if not isinstance(validator, ValidationProtocol):
            raise TypeError(f"Expected ValidationProtocol, got {type(validator)}")
        self._validator = validator

    def do_something(self, data: Any) -> None:
        """Do something that requires validation."""
        if self._validator is None:
            raise RuntimeError("Validator not configured. Call set_validator() first.")

        results = self._validator.validate(data)
        # Process results...
```

---

## Best Practices

### 1. Always Use Protocols for Cross-Module Dependencies

❌ **Don't:**
```python
from other_module import ConcreteClass

class MyClass:
    def __init__(self):
        self.dependency = ConcreteClass()  # Tight coupling
```

✅ **Do:**
```python
from protocols import AbstractProtocol

class MyClass:
    def __init__(self, dependency: Optional[AbstractProtocol] = None):
        self._dependency = dependency  # Loose coupling
```

### 2. Use Factory for Component Creation

❌ **Don't:**
```python
validation = ValidationOrchestrator()
critic = CriticOrchestrator()
validation._critic = critic  # Manual, error-prone wiring
```

✅ **Do:**
```python
from protocols.factory import DependencyFactory

validation, critic = DependencyFactory.create_wired_system()  # Correct by construction
```

### 3. Support Both Constructor and Setter Injection

```python
class MyClass:
    def __init__(self, dependency: Optional[Protocol] = None):
        """Constructor injection (optional)."""
        self._dependency = dependency

    def set_dependency(self, dependency: Protocol) -> None:
        """Setter injection (for runtime wiring)."""
        if not isinstance(dependency, Protocol):
            raise TypeError(f"Expected Protocol, got {type(dependency)}")
        self._dependency = dependency
```

### 4. Document Protocol Requirements

```python
@runtime_checkable
class MyProtocol(Protocol):
    """
    Protocol for my component.

    Implementations must provide:
    - method_a(data: str) -> str: Process data and return result
    - method_b(config: Dict) -> None: Configure the component

    Example implementation: MyConcreteClass

    Usage:
        >>> impl = MyConcreteClass()
        >>> result = impl.method_a("test")
        >>> impl.method_b({"setting": "value"})
    """
    def method_a(self, data: str) -> str: ...
    def method_b(self, config: Dict) -> None: ...
```

### 5. Provide Clear Error Messages

```python
def set_dependency(self, dependency: Protocol) -> None:
    """Set dependency with clear error messages."""
    if not isinstance(dependency, Protocol):
        raise TypeError(
            f"Expected Protocol, got {type(dependency).__name__}. "
            f"Ensure the object implements required methods: "
            f"method_a(), method_b()"
        )
    self._dependency = dependency

def use_dependency(self) -> None:
    """Use dependency with helpful runtime errors."""
    if self._dependency is None:
        raise RuntimeError(
            "Dependency not configured. "
            "Call set_dependency() or use DependencyFactory.create_wired_system()"
        )

    result = self._dependency.method_a("data")
```

### 6. Use Type Hints Everywhere

```python
from typing import Optional, List, Dict, Any
from protocols import ValidationProtocol

def process(
    validator: ValidationProtocol,
    data: List[str],
    config: Optional[Dict[str, Any]] = None
) -> List[ValidationResult]:
    """
    Process data with validator.

    Type hints enable:
    - IDE autocomplete
    - Static type checking with mypy
    - Better documentation
    """
    results: List[ValidationResult] = []
    for item in data:
        results.extend(validator.validate(item, config))
    return results
```

---

## Troubleshooting

### Issue: "Module has no attribute 'Protocol'"

**Cause:** Using Python < 3.8

**Solution:** Import from `typing_extensions`:

```python
# Python 3.8+
from typing import Protocol

# Python 3.7
from typing_extensions import Protocol
```

### Issue: "Circular import still detected"

**Cause:** Modules importing from each other instead of from protocols

**Solution:** Check imports, ensure using protocols:

```python
# ❌ Wrong
from critic_orchestrator import CriticOrchestrator

# ✅ Correct
from protocols import CriticProtocol
```

### Issue: "Protocol not recognized by type checker"

**Cause:** Missing `@runtime_checkable` decorator

**Solution:** Add decorator for isinstance checks:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable  # Required for isinstance()
class MyProtocol(Protocol):
    def my_method(self) -> str: ...
```

### Issue: "Dependencies not wired"

**Cause:** Manual instantiation instead of using factory

**Solution:** Use `DependencyFactory.create_wired_system()`:

```python
# ❌ Wrong
validator = ValidationOrchestrator()
critic = CriticOrchestrator()
# Forgot to wire!

# ✅ Correct
validator, critic = DependencyFactory.create_wired_system()
```

### Issue: "RuntimeError: Critic not configured"

**Cause:** Trying to use critic before injection

**Solution:** Either use factory or inject manually:

```python
# Option 1: Use factory (recommended)
validator, critic = DependencyFactory.create_wired_system()

# Option 2: Manual injection
validator = DependencyFactory.create_validation_orchestrator()
critic = DependencyFactory.create_critic_orchestrator()
validator.set_critic(critic)
```

### Issue: "Type checker complains about protocol methods"

**Cause:** Implementation doesn't match protocol signature exactly

**Solution:** Ensure exact signature match:

```python
# Protocol definition
class ValidationProtocol(Protocol):
    def validate(self, data: Any, config: Optional[ValidationConfig] = None) -> List[ValidationResult]: ...

# ❌ Wrong implementation (missing config parameter)
class MyValidator:
    def validate(self, data: Any) -> List[ValidationResult]:
        pass

# ✅ Correct implementation (exact match)
class MyValidator:
    def validate(self, data: Any, config: Optional[ValidationConfig] = None) -> List[ValidationResult]:
        pass
```

---

## References

### Official Documentation

- **PEP 544** - Protocols: Structural Subtyping (Static Duck Typing)
  - https://www.python.org/dev/peps/pep-0544/

- **Python typing documentation**
  - https://docs.python.org/3/library/typing.html#typing.Protocol

### Related ADRs

- **ADR-004** - Protocol-Based Dependency Injection Strategy
  - `/home/jevenson/.claude/lib/docs/adr/ADR-004-protocol-based-dependency-injection.md`

- **ADR-001** - Decompose ValidationOrchestrator
  - `/home/jevenson/.claude/lib/docs/adr/ADR-001-decompose-validation-orchestrator.md`

### Migration Guides

- **Migration Guide Phase 2B**
  - `/home/jevenson/.claude/lib/docs/MIGRATION_GUIDE_PHASE_2B.md`

### Architecture Documentation

- **Current Architecture**
  - `/home/jevenson/.claude/lib/docs/CURRENT_ARCHITECTURE.md`

- **Phase 2A Completion Report**
  - `/home/jevenson/.claude/lib/PHASE_2A_COMPLETE.md`

### Design Patterns

- **Dependency Injection**
  - *Dependency Injection in .NET* by Mark Seemann

- **Factory Pattern**
  - *Design Patterns: Elements of Reusable Object-Oriented Software* by Gang of Four

- **Circular Dependency Solutions**
  - *Growing Object-Oriented Software, Guided by Tests* by Steve Freeman & Nat Pryce

---

## Version History

| Version | Date       | Changes                        | Author              |
|---------|------------|--------------------------------|---------------------|
| 1.0.0   | 2025-11-09 | Initial comprehensive guide    | Documentation Expert |

---

**Status:** ✅ Active (Phase 2B)
**Last Updated:** 2025-11-09
**Next Review:** After Phase 2B completion

---

**For Questions or Contributions:**
- Review ADR-004 for architectural rationale
- Check migration guide for upgrade path
- See examples in `tests/test_protocols.py`
- Consult current architecture documentation
