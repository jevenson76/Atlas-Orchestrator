# Phase 2B Migration Guide: Protocol-Based Architecture

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Active
**Migration Period:** 8 weeks (Week 0-8)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [What Changed?](#what-changed)
3. [Do I Need to Migrate?](#do-i-need-to-migrate)
4. [Migration Scenarios](#migration-scenarios)
5. [Step-by-Step Migration](#step-by-step-migration)
6. [Timeline](#timeline)
7. [FAQ](#faq)
8. [Support](#support)

---

## Quick Start

### TL;DR

**Old Code (Still Works):**
```python
from validation_orchestrator import ValidationOrchestrator
orchestrator = ValidationOrchestrator()
```

**New Code (Recommended):**
```python
from protocols.factory import DependencyFactory
validator, critic = DependencyFactory.create_wired_system()
```

**Migration Status:** ✅ Backward compatible - no breaking changes

---

## What Changed?

Phase 2B introduces protocol-based dependency injection to resolve circular dependencies between `validation_orchestrator` and `critic_orchestrator`.

### Technical Changes

**1. New Modules Added:**
- `protocols/__init__.py` - Protocol definitions (ValidationProtocol, CriticProtocol, OrchestratorProtocol)
- `protocols/factory.py` - Dependency injection factory

**2. Import Paths Updated:**
- Validation components moved to `validation/` package
- Critic integration uses protocols instead of direct imports

**3. Dependency Injection:**
- Components now support optional dependency injection
- Factory pattern recommended for component creation
- Manual wiring still possible but not recommended

### Architecture Changes

**Before (Circular Dependency):**
```
validation_orchestrator.py ←→ critic_orchestrator.py
        ↓                              ↓
    [CIRCULAR IMPORT ERROR]
```

**After (Protocol-Based DI):**
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

## Do I Need to Migrate?

### No - Backward Compatibility Maintained

Your existing code will continue to work without changes. We've maintained 100% backward compatibility.

**If you have code like this, it still works:**
```python
from validation_orchestrator import ValidationOrchestrator, ValidationResult
orchestrator = ValidationOrchestrator()
results = orchestrator.validate(code)
```

### Yes - Migration is Recommended

While not required, migrating provides benefits:

✅ **No deprecation warnings**
✅ **Better type safety**
✅ **Easier testing**
✅ **Clearer dependencies**
✅ **Future-proof code**

**Migrate when:**
- Creating new code
- Refactoring existing code
- Adding test coverage
- Experiencing import issues

---

## Migration Scenarios

### Scenario 1: Using ValidationOrchestrator

#### Old Code (Still Works)

```python
from validation_orchestrator import ValidationOrchestrator

# Create validator
orchestrator = ValidationOrchestrator(
    project_root="/path/to/project",
    default_level="standard"
)

# Use validator
results = orchestrator.validate_code(
    code=code_string,
    context={"file": "app.py"},
    level="thorough"
)
```

#### New Code (Recommended)

```python
from protocols.factory import DependencyFactory

# Create validator (factory handles configuration)
validator, critic = DependencyFactory.create_wired_system(config={
    "project_root": "/path/to/project",
    "validation_level": "standard"
})

# Use validator (same API)
results = validator.validate_code(
    code=code_string,
    context={"file": "app.py"},
    level="thorough"
)
```

**Migration Steps:**
1. Replace import: `from validation_orchestrator import ...` → `from protocols.factory import DependencyFactory`
2. Replace instantiation: `ValidationOrchestrator()` → `DependencyFactory.create_wired_system()`
3. Destructure result: `validator, critic = ...`
4. Use `validator` where you used `orchestrator` before

---

### Scenario 2: Using CriticOrchestrator

#### Old Code

```python
from critic_orchestrator import CriticOrchestrator

# Create critic
critic = CriticOrchestrator()

# Use critic
results = critic.review_code(
    code_snippet=code,
    file_path="src/app.py",
    critics=["security-critic", "performance-critic"]
)
```

#### New Code

```python
from protocols.factory import DependencyFactory

# Create critic
validator, critic = DependencyFactory.create_wired_system()

# Use critic (same API)
results = critic.review_code(
    code_snippet=code,
    file_path="src/app.py",
    critics=["security-critic", "performance-critic"]
)
```

**Migration Steps:**
1. Use factory to create both validator and critic
2. Use `critic` from destructured tuple
3. No API changes needed

---

### Scenario 3: Using Both Together

#### Old Code

```python
from validation_orchestrator import ValidationOrchestrator
from critic_orchestrator import CriticOrchestrator

# Create both
validation = ValidationOrchestrator()
critic = CriticOrchestrator()

# Manual wiring (if needed)
# validation.critic = critic
# critic.validator = validation
```

#### New Code

```python
from protocols.factory import DependencyFactory

# Factory handles wiring automatically
validation, critic = DependencyFactory.create_wired_system()

# No manual wiring needed - already connected!
```

**Benefits:**
- No manual wiring code
- Guaranteed correct initialization
- Both components ready to use immediately

---

### Scenario 4: Custom Implementations

#### Old Code

```python
class MyValidator:
    def validate(self, data):
        # Custom validation logic
        return results

validator = MyValidator()
```

#### New Code

```python
from protocols import ValidationProtocol

class MyValidator:
    """Implements ValidationProtocol."""

    def validate(self, data, config=None):
        # Custom validation logic
        return results

# Can be used anywhere ValidationProtocol is expected
validator = MyValidator()

# Or inject into factory
critic = DependencyFactory.create_critic_orchestrator(validator=validator)
```

**Migration Steps:**
1. Import protocol: `from protocols import ValidationProtocol`
2. Update method signatures to match protocol
3. Optionally add type hints: `class MyValidator(ValidationProtocol):`

---

### Scenario 5: Using Orchestrator

#### Old Code (Direct Instantiation)

```python
from orchestrator import Orchestrator, SubAgent, ExecutionMode

class MyWorkflow(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.SEQUENTIAL)

        self.add_agent("agent1", SubAgent(
            role="First task",
            model="claude-haiku-4-20250514"
        ))
        self.add_agent("agent2", SubAgent(
            role="Second task",
            model="claude-sonnet-4-5-20250929"
        ))

    def prepare_prompt(self, agent_name, initial_input, previous_results):
        return f"Task: {initial_input.get('task')}"

    def process_result(self, agent_name, result):
        return {"agent": agent_name, "output": result}

# Use
workflow = MyWorkflow()
result = workflow.execute({"task": "Process data"})
```

#### New Code (Factory Pattern - Recommended)

```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Define agents
agents = [
    SubAgent(role="First task", model="claude-haiku-4-20250514"),
    SubAgent(role="Second task", model="claude-sonnet-4-5-20250929"),
]

# Create via factory
orch = DependencyFactory.create_orchestrator(
    agents=agents,
    mode="sequential"
)

# Execute
result = orch.execute({"task": "Process data"})
```

**Migration Steps:**
1. Replace custom Orchestrator subclass with agent configuration
2. Use `DependencyFactory.create_orchestrator()` instead of direct instantiation
3. Pass agents list and execution mode to factory
4. Execute with same API

**Benefits:**
- No need to subclass Orchestrator
- Simpler agent configuration
- Factory handles initialization
- Easier to test and modify

---

### Scenario 6: Orchestrator with Validation

#### Old Code

```python
from orchestrator import Orchestrator, SubAgent
from validation_orchestrator import ValidationOrchestrator
from critic_orchestrator import CriticOrchestrator

# Create components separately
orch = MyOrchestrator()
validator = ValidationOrchestrator()
critic = CriticOrchestrator()

# Manual wiring (error-prone)
orch.validator = validator
orch.critic = critic
validator.critic = critic
critic.validator = validator
```

#### New Code (Complete System)

```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Define workflow
agents = [
    SubAgent(role="coder", model="claude-sonnet-4-5-20250929"),
    SubAgent(role="tester", model="claude-sonnet-4-5-20250929"),
]

# Create complete system (orchestrator + validator + critic)
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="sequential",
    config={
        "validation_level": "thorough",
        "enable_critics": True
    }
)

# All components wired automatically
result = orch.execute({"task": "Build feature"})
```

**Migration Steps:**
1. Define agents list
2. Use `DependencyFactory.create_complete_system()` instead of manual creation
3. Destructure result: `orch, validator, critic = ...`
4. Remove manual wiring code
5. Use orchestrator as before

**Benefits:**
- All components wired automatically
- No risk of forgetting to wire dependencies
- Consistent initialization
- Single factory call

---

### Scenario 7: Testing

#### Old Code

```python
import unittest
from unittest.mock import Mock
from validation_orchestrator import ValidationOrchestrator

class TestValidation(unittest.TestCase):
    def test_validation(self):
        # Complex mocking setup
        mock_critic = Mock()
        validator = ValidationOrchestrator()
        validator.critic = mock_critic

        results = validator.validate(code)
        self.assertIsNotNone(results)
```

#### New Code

```python
import pytest
from protocols.factory import DependencyFactory

class MockCritic:
    """Simple test double (no mock framework needed)."""
    def critique(self, data, context=None):
        return [ValidationResult(level="info", message="test")]

    def assess_quality(self, critique, criteria=None):
        return QualityScore(value=0.9, confidence=1.0)

def test_validation():
    """Clean, simple test."""
    # Easy dependency injection
    validator = DependencyFactory.create_validation_orchestrator(
        critic=MockCritic()
    )

    results = validator.validate(code)
    assert results is not None
```

**Benefits:**
- No mock framework needed
- Simpler test setup
- Clearer test intent
- Faster test execution

---

## Step-by-Step Migration

### Step 1: Update Imports

**Find and replace:**

```python
# Before
from validation_orchestrator import ValidationOrchestrator, ValidationResult
from critic_orchestrator import CriticOrchestrator

# After
from validation import ValidationOrchestrator, ValidationResult
from critic_orchestrator import CriticOrchestrator
from protocols.factory import DependencyFactory
```

**Quick migration command:**
```bash
# Find all files using old imports
grep -r "from validation_orchestrator import" . --include="*.py"

# Recommended: Use search-and-replace in your IDE
```

### Step 2: Update Component Creation

**Replace direct instantiation with factory:**

```python
# Before
validation = ValidationOrchestrator()
critic = CriticOrchestrator()

# After
validation, critic = DependencyFactory.create_wired_system()
```

**With configuration:**

```python
# Before
validation = ValidationOrchestrator(
    project_root="/path",
    default_level="thorough"
)

# After
validation, critic = DependencyFactory.create_wired_system(config={
    "project_root": "/path",
    "validation_level": "thorough"
})
```

### Step 3: Remove Manual Wiring

**Delete manual dependency wiring:**

```python
# Before (delete this)
validation.critic = critic
critic.validator = validation

# After (factory handles this automatically)
# No wiring code needed!
```

### Step 4: Update Type Hints (Optional but Recommended)

**Use protocols for type hints:**

```python
# Before
from validation_orchestrator import ValidationOrchestrator

def process(validator: ValidationOrchestrator):
    return validator.validate(data)

# After (more flexible)
from protocols import ValidationProtocol

def process(validator: ValidationProtocol):
    return validator.validate(data)
```

**Benefits:**
- Accepts any ValidationProtocol implementation
- Better for testing (easy to inject mocks)
- More flexible architecture

### Step 5: Update Tests

**Simplify test setup:**

```python
# Before
def test_validation():
    mock_critic = Mock()
    validator = ValidationOrchestrator()
    validator.critic = mock_critic
    # Complex setup...

# After
def test_validation():
    class SimpleCritic:
        def critique(self, data, context=None):
            return [ValidationResult(...)]

    validator = DependencyFactory.create_validation_orchestrator(
        critic=SimpleCritic()
    )
    # Clean, simple setup!
```

### Step 6: Run Tests

**Verify migration:**

```bash
# Run your test suite
pytest tests/

# Check for deprecation warnings
pytest tests/ -W all

# Run type checker
mypy src/
```

### Step 7: Commit Changes

**Commit with conventional message:**

```bash
git add .
git commit -m "refactor: migrate to protocol-based dependency injection

- Update imports to use protocols.factory
- Replace direct instantiation with DependencyFactory
- Remove manual dependency wiring
- Update type hints to use protocols

Refs: Phase 2B, ADR-004"
```

---

## Timeline

### Phase 1: Deprecation (Current - Week 8)

**Status:** ✅ Active

**What's Available:**
- Old imports work with deprecation warnings
- New protocol-based pattern available
- Documentation updated
- Migration guide available (this document)

**What You Should Do:**
- Review this migration guide
- Plan migration for your codebase
- Test new pattern in non-critical code
- Ask questions if unclear

### Phase 2: Migration Period (Week 8 - Week 16)

**Status:** Upcoming

**What's Happening:**
- Teams migrate to new pattern
- Both patterns fully supported
- CI/CD monitors deprecation warnings
- Support team available for questions

**What You Should Do:**
- Migrate your code to new pattern
- Update tests
- Remove manual wiring code
- Update documentation

### Phase 3: Completion (Week 16+)

**Status:** Future

**What Will Happen:**
- Old pattern may be deprecated
- Protocol pattern is standard
- Full ecosystem support
- Old imports may stop working

**What You Should Do:**
- Ensure migration completed
- Verify all tests passing
- No deprecation warnings remain

---

## FAQ

### Q: Will my existing code break?

**A:** No, backward compatibility is maintained. Existing code continues to work without changes.

### Q: Do I need to migrate immediately?

**A:** No, but migrating is recommended for new code and when refactoring existing code.

### Q: What if I have a custom validator?

**A:** Implement the ValidationProtocol interface and it will work with the DI system. See Scenario 4 above.

### Q: Can I mix old and new patterns?

**A:** Yes, they're fully compatible. You can gradually migrate over time.

### Q: How do I test with the new pattern?

**A:** Use DependencyFactory to inject test doubles. No mock framework needed. See Scenario 5 above.

### Q: What if I get "RuntimeError: Critic not configured"?

**A:** Use `DependencyFactory.create_wired_system()` instead of direct instantiation, or manually inject dependencies.

### Q: Are there performance implications?

**A:** No, the factory pattern has negligible performance overhead. Runtime wiring happens once at initialization.

### Q: What about type checking?

**A:** Type checking is fully supported. Use protocols for type hints to get better flexibility.

### Q: How do I know if I've migrated correctly?

**A:** Run your test suite and check for:
- ✅ All tests passing
- ✅ No deprecation warnings
- ✅ Type checker passes (`mypy`)
- ✅ No circular import errors

### Q: Where can I get help?

**A:** See [Support](#support) section below for resources and contacts.

---

## Support

### Documentation

**Protocol Guide:**
- `/home/jevenson/.claude/lib/docs/PROTOCOLS.md`
- Comprehensive guide to protocol-based architecture

**ADR-004:**
- `/home/jevenson/.claude/lib/docs/adr/ADR-004-protocol-based-dependency-injection.md`
- Architectural rationale and decision record

**Current Architecture:**
- `/home/jevenson/.claude/lib/docs/CURRENT_ARCHITECTURE.md`
- Updated architecture documentation

### Examples

**Test Examples:**
- `/home/jevenson/.claude/lib/tests/test_protocols.py`
- Working examples of protocol usage

**Integration Examples:**
- See `specialized_roles_orchestrator.py` for protocol usage
- See `progressive_enhancement_orchestrator.py` for factory usage

### Code Review

**Migration Checklist:**

Before submitting PR, verify:

- [ ] Imports updated to use protocols
- [ ] Using DependencyFactory for component creation
- [ ] Manual wiring code removed
- [ ] Type hints use protocols where appropriate
- [ ] All tests passing
- [ ] No deprecation warnings
- [ ] No circular import errors
- [ ] Documentation updated (if public API)

**PR Template:**

```markdown
## Migration to Protocol-Based DI

**Type:** Refactoring
**Related:** Phase 2B, ADR-004

### Changes

- Updated imports to use `protocols.factory`
- Replaced direct instantiation with `DependencyFactory`
- Removed manual dependency wiring
- Updated type hints to use protocols

### Testing

- [ ] All unit tests passing
- [ ] No deprecation warnings
- [ ] Type checker passes
- [ ] Integration tests passing

### Checklist

- [ ] Followed migration guide
- [ ] Removed manual wiring code
- [ ] Updated type hints
- [ ] Documentation updated
```

### Contacts

**Questions about migration:**
- Review this guide first
- Check PROTOCOLS.md for detailed usage
- See ADR-004 for architectural rationale
- Check test examples

**Issues or bugs:**
- Create issue in project repository
- Include code snippets showing problem
- Include error messages
- Note which migration step you're on

### Common Migration Patterns

**Pattern 1: Simple Migration**
```python
# Before
from validation_orchestrator import ValidationOrchestrator
validator = ValidationOrchestrator()

# After
from protocols.factory import DependencyFactory
validator, _ = DependencyFactory.create_wired_system()
```

**Pattern 2: With Configuration**
```python
# Before
validator = ValidationOrchestrator(project_root="/path", default_level="thorough")

# After
validator, _ = DependencyFactory.create_wired_system({
    "project_root": "/path",
    "validation_level": "thorough"
})
```

**Pattern 3: Independent Components**
```python
# Before
validator = ValidationOrchestrator()

# After
validator = DependencyFactory.create_validation_orchestrator()
# Note: No critic, can add later with validator.set_critic()
```

**Pattern 4: Testing**
```python
# Before
mock = Mock()
validator = ValidationOrchestrator()
validator.critic = mock

# After
class TestCritic:
    def critique(self, data, context=None): return []
    def assess_quality(self, critique, criteria=None): return QualityScore(0.9, 1.0)

validator = DependencyFactory.create_validation_orchestrator(critic=TestCritic())
```

---

## Migration Examples by File Type

### Python Scripts

```python
# script.py - Before
from validation_orchestrator import ValidationOrchestrator

def main():
    validator = ValidationOrchestrator()
    results = validator.validate(code)
    print(results)

if __name__ == "__main__":
    main()
```

```python
# script.py - After
from protocols.factory import DependencyFactory

def main():
    validator, _ = DependencyFactory.create_wired_system()
    results = validator.validate(code)
    print(results)

if __name__ == "__main__":
    main()
```

### Web Applications

```python
# app.py - Before
from flask import Flask
from validation_orchestrator import ValidationOrchestrator

app = Flask(__name__)
validator = ValidationOrchestrator()

@app.route("/validate", methods=["POST"])
def validate():
    code = request.json["code"]
    results = validator.validate(code)
    return jsonify(results)
```

```python
# app.py - After
from flask import Flask
from protocols.factory import DependencyFactory

app = Flask(__name__)

# Create at app startup
validator, critic = DependencyFactory.create_wired_system()

@app.route("/validate", methods=["POST"])
def validate():
    code = request.json["code"]
    results = validator.validate(code)
    return jsonify(results)
```

### CLI Applications

```python
# cli.py - Before
import click
from validation_orchestrator import ValidationOrchestrator

@click.command()
@click.argument("file")
def validate(file):
    validator = ValidationOrchestrator()
    with open(file) as f:
        code = f.read()
    results = validator.validate(code)
    click.echo(results)
```

```python
# cli.py - After
import click
from protocols.factory import DependencyFactory

@click.command()
@click.argument("file")
def validate(file):
    validator, _ = DependencyFactory.create_wired_system()
    with open(file) as f:
        code = f.read()
    results = validator.validate(code)
    click.echo(results)
```

### Test Files

```python
# test_app.py - Before
import unittest
from unittest.mock import Mock
from validation_orchestrator import ValidationOrchestrator

class TestApp(unittest.TestCase):
    def setUp(self):
        self.validator = ValidationOrchestrator()
        self.validator.critic = Mock()

    def test_validation(self):
        results = self.validator.validate("code")
        self.assertIsNotNone(results)
```

```python
# test_app.py - After
import pytest
from protocols.factory import DependencyFactory

class TestCritic:
    def critique(self, data, context=None):
        return []
    def assess_quality(self, critique, criteria=None):
        return QualityScore(0.9, 1.0)

@pytest.fixture
def validator():
    return DependencyFactory.create_validation_orchestrator(critic=TestCritic())

def test_validation(validator):
    results = validator.validate("code")
    assert results is not None
```

---

## Version History

| Version | Date       | Changes                        | Author              |
|---------|------------|--------------------------------|---------------------|
| 1.0.0   | 2025-11-09 | Initial migration guide        | Documentation Expert |

---

**Status:** ✅ Active (8-week migration period)
**Phase:** Phase 2B
**Last Updated:** 2025-11-09
**Next Review:** Week 8 (migration status check)

---

**Ready to Migrate?**

1. Read [Quick Start](#quick-start)
2. Identify your scenario in [Migration Scenarios](#migration-scenarios)
3. Follow [Step-by-Step Migration](#step-by-step-migration)
4. Use [Support](#support) resources if needed
5. Submit PR using checklist

**Questions?** See [FAQ](#faq) or check [PROTOCOLS.md](/home/jevenson/.claude/lib/docs/PROTOCOLS.md)
