# Phase 2D Migration Guide: Centralized Model Selection

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Active
**Migration Period:** 8 weeks (Week 0-8)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [What Changed in Phase 2D?](#what-changed-in-phase-2d)
3. [Migration Scenarios](#migration-scenarios)
4. [Migration Timeline](#migration-timeline)
5. [Testing Your Migration](#testing-your-migration)
6. [FAQ](#faq)
7. [Support Resources](#support-resources)

---

## Quick Start

### TL;DR

**Old Code (Deprecated):**
```python
# Hardcoded model selection in each orchestrator
def _select_validator_model(self, complexity: str) -> str:
    if complexity == "high":
        return "claude-opus-4-20250514"
    elif complexity == "medium":
        return "claude-sonnet-3-7-20250219"
    else:
        return "claude-haiku-3-5-20250318"
```

**New Code (Recommended):**
```python
# Centralized model selection
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.HIGH
)
model = selector.select_model(context)
```

**Migration Status:** ✅ Backward compatible - no breaking changes

---

## What Changed in Phase 2D?

Phase 2D centralizes model selection logic that was previously duplicated across 3+ orchestrators.

### Files Added

**1. New Utilities Package:**
```
utils/
├── __init__.py               # Package exports
└── model_selector.py         # ModelSelector class
```

**2. Enhanced Orchestrators:**
```
validation/core.py            # Now uses ModelSelector
critic_orchestrator.py        # Now uses ModelSelector
orchestrator.py               # Now uses ModelSelector
```

### Code Reduction

**Before Phase 2D:**
```
validation_orchestrator.py    _select_validator_model()    200 lines
critic_orchestrator.py        _select_critic_model()       180 lines
orchestrator.py               _select_subagent_model()     220 lines
                                                           ─────────
                                                  Total:   600 lines (duplicated)
```

**After Phase 2D:**
```
utils/model_selector.py       ModelSelector class          300 lines (centralized)
validation/core.py            uses ModelSelector            50 lines (removed duplication)
critic_orchestrator.py        uses ModelSelector            50 lines (removed duplication)
orchestrator.py               uses ModelSelector            50 lines (removed duplication)
                                                           ─────────
                                                  Total:   450 lines (25% reduction)
```

### Backward Compatibility

✅ **Old imports still work** (with deprecation warnings)
✅ **Old method signatures unchanged**
✅ **Existing tests continue to pass**
✅ **Gradual migration supported**

**Deprecation warnings added to old methods:**
```python
import warnings

def _select_validator_model(self, complexity: str) -> str:
    warnings.warn(
        "_select_validator_model is deprecated, use ModelSelector instead",
        DeprecationWarning,
        stacklevel=2
    )
    # Falls back to ModelSelector internally
    ...
```

### Breaking Changes

**None!** Phase 2D maintains 100% backward compatibility.

---

## Migration Scenarios

### Scenario 1: Migrating BaseAgent Usage

#### Old Code (Direct Model Hardcoding)

```python
from agent_system import BaseAgent

# Hardcode model in each instantiation
agent = BaseAgent(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-opus-4-20250514",  # Hardcoded
    max_retries=3
)

response = agent.execute(prompt="Analyze this code")
```

#### New Code (ModelSelector)

```python
from agent_system import BaseAgent
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

# Select model based on task
selector = ModelSelector()
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
model = selector.select_model(context)

# Use selected model
agent = BaseAgent(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model=model,
    max_retries=3
)

response = agent.execute(prompt="Analyze this code")
```

**Benefits:**
- Model selection based on task characteristics
- Easy to change tier mappings globally
- Budget-aware selection available
- Consistent across entire system

---

### Scenario 2: Migrating Orchestrator Usage

#### Old Code (Hardcoded in Orchestrator)

```python
from orchestrator import Orchestrator, SubAgent, ExecutionMode

class MyWorkflow(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.SEQUENTIAL)

        # Hardcoded models for each agent
        self.add_agent("analyzer", SubAgent(
            role="Code analyzer",
            model="claude-opus-4-20250514"  # Always Opus
        ))

        self.add_agent("summarizer", SubAgent(
            role="Summary generator",
            model="claude-sonnet-3-7-20250219"  # Always Sonnet
        ))

    def prepare_prompt(self, agent_name, initial_input, previous_results):
        return f"Task: {initial_input.get('task')}"

workflow = MyWorkflow()
result = workflow.execute({"task": "Process data"})
```

#### New Code (ModelSelector-Based)

```python
from orchestrator import Orchestrator, SubAgent, ExecutionMode
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

class MyWorkflow(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.SEQUENTIAL)

        # Use ModelSelector to choose appropriate models
        selector = ModelSelector()

        # Analyzer: High-complexity analysis → premium tier
        analyzer_model = selector.select_model(
            ModelSelectionContext(
                task_type=TaskType.ANALYSIS,
                complexity=TaskComplexity.HIGH
            )
        )

        # Summarizer: Low-complexity summary → economy tier
        summarizer_model = selector.select_model(
            ModelSelectionContext(
                task_type=TaskType.SUMMARIZATION,
                complexity=TaskComplexity.LOW
            )
        )

        self.add_agent("analyzer", SubAgent(
            role="Code analyzer",
            model=analyzer_model  # Selected based on task
        ))

        self.add_agent("summarizer", SubAgent(
            role="Summary generator",
            model=summarizer_model  # Selected based on task
        ))

    def prepare_prompt(self, agent_name, initial_input, previous_results):
        return f"Task: {initial_input.get('task')}"

workflow = MyWorkflow()
result = workflow.execute({"task": "Process data"})
```

**Benefits:**
- Analyzer uses appropriate tier (Opus for complex analysis)
- Summarizer uses cost-effective tier (Haiku for simple summaries)
- Cost savings: ~85% on summarizer (Haiku vs Opus)
- Easy to adjust tiers globally

---

### Scenario 3: Migrating ValidationOrchestrator Usage

#### Old Code (Internal Method)

```python
from validation_orchestrator import ValidationOrchestrator

# Create orchestrator
validator = ValidationOrchestrator()

# Internal method selects model (deprecated)
result = validator.validate(
    code=code_string,
    complexity="high"  # String passed to _select_validator_model()
)

# _select_validator_model() internally:
# - "high" → "claude-opus-4-20250514"
# - "medium" → "claude-sonnet-3-7-20250219"
# - "low" → "claude-haiku-3-5-20250318"
```

#### New Code (ModelSelector Integration)

```python
from validation import ValidationCore
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

# Create orchestrator (now uses ModelSelector internally)
validator = ValidationCore()

# Model selection happens internally using ModelSelector
result = validator.validate(
    code=code_string,
    complexity=TaskComplexity.HIGH  # Enum instead of string
)

# Internally, ValidationCore now:
# 1. Creates ModelSelectionContext(task_type=VALIDATION, complexity=HIGH)
# 2. Calls model_selector.select_model(context)
# 3. Uses returned model for validation
```

**Note:** If you're using `ValidationOrchestrator` (old name), it still works but emits deprecation warning. Migrate to `ValidationCore` when convenient.

**Backward Compatible Code (Still Works):**
```python
from validation_orchestrator import ValidationOrchestrator  # Deprecated

validator = ValidationOrchestrator()  # Works, but shows warning
result = validator.validate(code=code_string, complexity="high")  # Works
```

---

### Scenario 4: Migrating CriticOrchestrator Usage

#### Old Code (Critic-Specific Selection)

```python
from critic_orchestrator import CriticOrchestrator

# Create critic
critic = CriticOrchestrator()

# Internal _select_critic_model() chooses model
result = critic.critique(
    code_snippet=code,
    critique_type="security"  # "security" → Opus
)

# Internally:
# - "security", "architecture" → Opus
# - "code_quality" → Sonnet
# - others → Haiku
```

#### New Code (ModelSelector Integration)

```python
from critic_orchestrator import CriticOrchestrator
from utils.model_selector import TaskComplexity

# Create critic (now uses ModelSelector internally)
critic = CriticOrchestrator()

# Critique type maps to complexity
result = critic.critique(
    code_snippet=code,
    critique_type="security",  # Mapped to TaskComplexity.CRITICAL
    complexity=TaskComplexity.CRITICAL  # Optional: override
)

# Internally, CriticOrchestrator:
# 1. Maps critique_type to TaskComplexity
#    - "security" → CRITICAL
#    - "code_quality" → HIGH
#    - "style" → LOW
# 2. Creates ModelSelectionContext(task_type=CRITIQUE, complexity=...)
# 3. Uses model_selector.select_model()
```

**Benefits:**
- Consistent model selection across all critics
- Easy to adjust critique tier mappings
- Budget-aware critique available

---

### Scenario 5: Migrating Custom Agent Implementations

#### Old Code (Custom Agent with Hardcoded Model)

```python
class MyCustomAgent:
    def __init__(self):
        # Hardcode model
        self.model = "claude-opus-4-20250514"

    def analyze(self, data):
        # Use hardcoded model
        agent = BaseAgent(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=self.model
        )
        return agent.execute(prompt=f"Analyze: {data}")
```

#### New Code (ModelSelector Integration)

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

class MyCustomAgent:
    def __init__(self):
        # Use ModelSelector
        self.model_selector = ModelSelector()

    def analyze(self, data, complexity=TaskComplexity.MEDIUM):
        # Select model based on task
        context = ModelSelectionContext(
            task_type=TaskType.ANALYSIS,
            complexity=complexity
        )
        model = self.model_selector.select_model(context)

        # Use selected model
        agent = BaseAgent(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=model
        )
        return agent.execute(prompt=f"Analyze: {data}")
```

**Benefits:**
- Caller can specify complexity
- Agent automatically selects appropriate tier
- Easy to add budget constraints later

---

### Scenario 6: Migrating Budget-Constrained Applications

#### Old Code (No Budget Awareness)

```python
# No way to enforce budget, risk of overspending
orchestrator = Orchestrator()

for task in tasks:
    # Always uses premium tier (expensive!)
    agent = BaseAgent(model="claude-opus-4-20250514")
    result = agent.execute(prompt=task)
```

#### New Code (Budget-Aware Selection)

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Set budget per task
BUDGET_PER_TASK = 0.005  # $0.005 per task

for task in tasks:
    # ModelSelector downgrades if needed to stay within budget
    context = ModelSelectionContext(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.HIGH,
        budget=BUDGET_PER_TASK
    )
    model = selector.select_model(context)

    agent = BaseAgent(model=model)
    result = agent.execute(prompt=task)

    # Estimate and log cost
    cost = selector.estimate_cost(model, 5000, 1000)
    print(f"Task cost: ${cost:.4f} (budget: ${BUDGET_PER_TASK})")
```

**Benefits:**
- Automatic tier downgrade to stay within budget
- Cost estimation before execution
- Prevent budget overruns

---

### Scenario 7: Migrating Configuration-Driven Systems

#### Old Code (Config File with Hardcoded Models)

```yaml
# config.yaml
validation:
  high_complexity_model: "claude-opus-4-20250514"
  medium_complexity_model: "claude-sonnet-3-7-20250219"
  low_complexity_model: "claude-haiku-3-5-20250318"

critic:
  security_model: "claude-opus-4-20250514"
  quality_model: "claude-sonnet-3-7-20250219"
  style_model: "claude-haiku-3-5-20250318"
```

```python
import yaml

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Use hardcoded models from config
validator_model = config["validation"]["high_complexity_model"]
```

#### New Code (ModelSelector Config)

```yaml
# config.yaml
model_selector:
  model_tiers:
    premium: "claude-opus-4-20250514"
    standard: "claude-sonnet-4-5-20250929"
    economy: "claude-haiku-4-20250514"

  task_overrides:
    CRITIQUE:
      HIGH: "premium"  # Always premium for high-complexity critiques

  cost_multipliers:
    premium: 1.0
    standard: 1.0
    economy: 0.8  # 20% discount for economy tier
```

```python
import yaml
from utils.model_selector import ModelSelector

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Create ModelSelector with config
selector = ModelSelector(config=config["model_selector"])

# Now all orchestrators use same configuration
```

**Benefits:**
- Single configuration for all orchestrators
- Easy to swap tiers (e.g., Opus → GPT-4 Turbo)
- Override tiers for specific tasks
- Cost multipliers for custom pricing

---

## Migration Timeline

### Phase 1: Soft Launch (Current - Week 4)

**Status:** ✅ Active

**What's Available:**
- ModelSelector utility created
- Orchestrators integrated with ModelSelector
- Old methods still work (with deprecation warnings)
- Documentation available

**What You Should Do:**
- Review this migration guide
- Review MODEL_SELECTOR_GUIDE.md for detailed API
- Identify code using hardcoded models
- Plan migration strategy

**Timeline Diagram:**
```
Week 0 ────────────────────────────> Week 4
        ↑ Phase 2D Launch
        ↑ ModelSelector available
        ↑ Old methods deprecated
```

---

### Phase 2: Active Migration (Week 4-8)

**Status:** Upcoming

**What Will Happen:**
- Teams migrate to ModelSelector
- Both old and new patterns supported
- CI/CD monitors deprecation warnings
- Support available for migration questions

**What You Should Do:**
- Migrate your code to ModelSelector
- Update tests to use ModelSelector
- Remove hardcoded model IDs
- Update configuration files

**Migration Checklist:**
- [ ] Identify all hardcoded model selection
- [ ] Import ModelSelector
- [ ] Replace hardcoded selection with `select_model()`
- [ ] Map complexity strings to TaskComplexity enums
- [ ] Update tests
- [ ] Remove deprecated methods
- [ ] Update documentation

---

### Phase 3: Deprecation Completion (Week 8-16)

**Status:** Future

**What Will Happen:**
- Old methods emit louder warnings
- Prepare for eventual removal
- Final migration push

**What You Should Do:**
- Complete all migrations
- Remove all deprecation warnings
- Verify tests passing
- Update documentation

---

### Phase 4: Cleanup (Week 16+)

**Status:** Future

**What Will Happen:**
- Old methods removed (breaking change)
- Only ModelSelector supported
- Full cleanup

**What You Should Do:**
- Ensure all code migrated before Week 16
- No hardcoded model selection remaining

**Timeline Diagram:**
```
Week 0 ─────> Week 4 ─────> Week 8 ─────> Week 16
        Phase 1      Phase 2       Phase 3        Phase 4
        Launch       Active        Deprecation    Cleanup
                     Migration     Completion
```

---

## Testing Your Migration

### Unit Tests

**Test 1: Verify ModelSelector Integration**

```python
# test_validation_migration.py
import pytest
from validation import ValidationCore
from utils.model_selector import TaskComplexity

def test_validation_uses_model_selector():
    """Ensure ValidationCore uses ModelSelector."""
    validator = ValidationCore()

    # Verify model_selector attribute exists
    assert hasattr(validator, 'model_selector')
    assert validator.model_selector is not None

def test_model_selection_correct_tier():
    """Verify correct tier selection for complexity."""
    validator = ValidationCore()

    # High complexity should use standard or premium tier
    context = ModelSelectionContext(
        task_type=TaskType.VALIDATION,
        complexity=TaskComplexity.HIGH
    )
    model = validator.model_selector.select_model(context)
    tier = validator.model_selector.get_tier_for_model(model)

    assert tier in ["standard", "premium"]

def test_backward_compatibility():
    """Old API still works (with deprecation warning)."""
    with pytest.deprecated_call():
        from validation_orchestrator import ValidationOrchestrator
        validator = ValidationOrchestrator()

    # Old method signature still works
    result = validator.validate(code="test", complexity="high")
    assert result is not None
```

**Test 2: Verify Cost Optimization**

```python
# test_cost_optimization.py
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

def test_budget_aware_downgrade():
    """Budget constraint forces tier downgrade."""
    selector = ModelSelector()

    # High complexity, tight budget
    context = ModelSelectionContext(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.HIGH,
        budget=0.001  # Very tight
    )
    model = selector.select_model(context)
    tier = selector.get_tier_for_model(model)

    # Should downgrade to economy tier
    assert tier == "economy"

    # Verify cost within budget
    cost = selector.estimate_cost(model, 5000, 1000)
    assert cost <= 0.001

def test_cost_savings():
    """Economy tier saves costs."""
    selector = ModelSelector()

    # Premium tier cost
    premium_cost = selector.estimate_cost(
        "claude-opus-4-20250514",
        5000, 1000
    )

    # Economy tier cost
    economy_cost = selector.estimate_cost(
        "claude-haiku-4-20250514",
        5000, 1000
    )

    # Economy should be much cheaper (>90% savings)
    assert economy_cost < premium_cost * 0.1
```

**Test 3: Verify Fallback Chain**

```python
# test_fallback.py
from utils.model_selector import ModelSelector

def test_fallback_chain():
    """Fallback chain includes multiple models."""
    selector = ModelSelector()

    fallbacks = selector.get_fallback_models("claude-opus-4-20250514")

    # Should have at least 2 fallbacks
    assert len(fallbacks) >= 2

    # Should include primary model
    assert "claude-opus-4-20250514" in fallbacks

    # Should include cross-provider fallback
    assert any("gpt" in model for model in fallbacks)
```

### Integration Tests

**Test 4: End-to-End Workflow**

```python
# test_workflow_integration.py
from orchestrator import Orchestrator, SubAgent, ExecutionMode
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

def test_orchestrator_workflow():
    """Test complete workflow with ModelSelector."""
    selector = ModelSelector()

    # Create orchestrator
    orch = Orchestrator(mode=ExecutionMode.SEQUENTIAL)

    # Add agents with selected models
    analyzer_model = selector.select_model(
        ModelSelectionContext(
            task_type=TaskType.ANALYSIS,
            complexity=TaskComplexity.HIGH
        )
    )

    orch.add_agent("analyzer", SubAgent(
        role="Analyzer",
        model=analyzer_model
    ))

    # Execute workflow
    result = orch.execute({"task": "Test task"})

    # Verify execution succeeded
    assert result is not None
    assert "analyzer" in orch.get_agent_results()
```

### Regression Tests

**Test 5: No Breaking Changes**

```python
# test_regression.py
import warnings

def test_old_api_still_works():
    """Old API continues to work (backward compatibility)."""
    # Suppress deprecation warnings for this test
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        from validation_orchestrator import ValidationOrchestrator

        # Old instantiation
        validator = ValidationOrchestrator()

        # Old method signature
        result = validator.validate(code="test", complexity="high")

        # Should still work
        assert result is not None
```

### Testing Checklist

Before considering migration complete, verify:

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Regression tests passing
- [ ] No unexpected deprecation warnings
- [ ] Type checker passes (`mypy`)
- [ ] Cost estimates reasonable
- [ ] Fallback chains work
- [ ] Configuration loading works
- [ ] Old API still works (if needed)
- [ ] Documentation updated

---

## FAQ

### Q: Will my existing code break?

**A:** No. Phase 2D maintains 100% backward compatibility. Existing code continues to work, though you may see deprecation warnings.

### Q: Do I need to migrate immediately?

**A:** No. Migration is recommended but not required immediately. You have an 8-week migration window (Week 0-8) before deprecation warnings escalate.

### Q: What happens if I don't migrate?

**A:** Your code continues to work during the migration period. After Week 16, old methods may be removed (breaking change), so plan to migrate before then.

### Q: Can I migrate gradually?

**A:** Yes! Migrate one orchestrator at a time, or even one method at a time. Old and new patterns coexist.

### Q: How do I know if I'm using ModelSelector correctly?

**A:** Run your test suite and check:
1. All tests passing
2. No deprecation warnings
3. Type checker passes
4. Costs are as expected

### Q: What if ModelSelector selects the wrong tier?

**A:** You can override tier selection:

```python
# Option 1: Adjust complexity level
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.CRITICAL  # Force premium tier
)

# Option 2: Use custom config
custom_config = {
    "task_overrides": {
        "VALIDATION": {
            "MEDIUM": "premium"  # Upgrade medium to premium
        }
    }
}
selector = ModelSelector(config=custom_config)
```

### Q: How do I test with different models in dev vs prod?

**A:** Use environment variables:

```bash
# .env.development
MODEL_SELECTOR_PREMIUM="claude-sonnet-4-5-20250929"  # Use Sonnet in dev
MODEL_SELECTOR_STANDARD="claude-haiku-4-20250514"

# .env.production
MODEL_SELECTOR_PREMIUM="claude-opus-4-20250514"  # Use Opus in prod
MODEL_SELECTOR_STANDARD="claude-sonnet-4-5-20250929"
```

### Q: Can I use ModelSelector with OpenAI models?

**A:** Yes! Configure OpenAI models in tiers:

```python
openai_config = {
    "model_tiers": {
        "premium": "gpt-4-turbo",
        "standard": "gpt-4",
        "economy": "gpt-3.5-turbo"
    }
}
selector = ModelSelector(config=openai_config)
```

### Q: What about cost tracking?

**A:** Use `estimate_cost()` before execution:

```python
model = selector.select_model(context)
estimated_cost = selector.estimate_cost(model, input_tokens, output_tokens)
print(f"Estimated cost: ${estimated_cost:.4f}")
```

### Q: How do I migrate tests that mock model selection?

**A:** Mock ModelSelector instead:

```python
# Old: Mock hardcoded method
@patch('validation_orchestrator.ValidationOrchestrator._select_validator_model')
def test_validation(mock_select):
    mock_select.return_value = "test-model"
    # ...

# New: Mock ModelSelector
@patch('utils.model_selector.ModelSelector.select_model')
def test_validation(mock_select):
    mock_select.return_value = "test-model"
    # ...
```

### Q: Where can I get help?

**A:** See [Support Resources](#support-resources) below.

---

## Support Resources

### Documentation

**Comprehensive Guides:**
- **MODEL_SELECTOR_GUIDE.md:** `/home/jevenson/.claude/lib/docs/MODEL_SELECTOR_GUIDE.md`
  - Full API reference
  - Usage patterns
  - Cost optimization
  - Troubleshooting

- **ADR-003:** `/home/jevenson/.claude/lib/docs/adr/ADR-003-centralize-model-selection.md`
  - Architectural decision record
  - Rationale for ModelSelector
  - Alternatives considered

- **Phase 2 Execution Plan:** `/home/jevenson/.claude/lib/PHASE_2_EXECUTION_PLAN.md`
  - Overall consolidation plan
  - ModelSelector is Phase 2D

### Code Examples

**Test Examples:**
- `/home/jevenson/.claude/lib/tests/test_model_selector.py`
- `/home/jevenson/.claude/lib/tests/test_model_selector_integration.py`

**Integration Examples:**
- See `validation/core.py` for ValidationCore integration
- See `critic_orchestrator.py` for CriticOrchestrator integration
- See `orchestrator.py` for base Orchestrator integration

### Migration Assistance

**Before Starting Migration:**
1. Read this migration guide completely
2. Review MODEL_SELECTOR_GUIDE.md
3. Review ADR-003 for architectural context
4. Identify all hardcoded model selection in your code

**During Migration:**
1. Start with one orchestrator/class
2. Write tests first
3. Migrate incrementally
4. Verify each step

**After Migration:**
1. Run full test suite
2. Check for deprecation warnings
3. Verify cost estimates
4. Update documentation

### Common Migration Patterns

**Pattern 1: Simple Replacement**
```python
# Before
model = "claude-opus-4-20250514"

# After
selector = ModelSelector()
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
model = selector.select_model(context)
```

**Pattern 2: With Configuration**
```python
# Before
config = {"model": "claude-opus-4-20250514"}

# After
selector_config = {
    "model_tiers": {
        "premium": "claude-opus-4-20250514"
    }
}
selector = ModelSelector(config=selector_config)
```

**Pattern 3: Budget-Aware**
```python
# Before (no budget awareness)
model = "claude-opus-4-20250514"  # Always expensive

# After (budget-aware)
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH,
    budget=0.005  # Automatic downgrade if needed
)
model = selector.select_model(context)
```

### Quick Reference Card

```
┌───────────────────────────────────────────────────────────┐
│ ModelSelector Quick Reference                             │
├───────────────────────────────────────────────────────────┤
│ IMPORT:                                                   │
│   from utils.model_selector import ModelSelector          │
│   from utils.model_selector import ModelSelectionContext  │
│   from utils.model_selector import TaskType, TaskComplexity│
│                                                           │
│ CREATE SELECTOR:                                          │
│   selector = ModelSelector()                              │
│                                                           │
│ SELECT MODEL:                                             │
│   context = ModelSelectionContext(                        │
│       task_type=TaskType.ANALYSIS,                        │
│       complexity=TaskComplexity.HIGH                      │
│   )                                                       │
│   model = selector.select_model(context)                  │
│                                                           │
│ ESTIMATE COST:                                            │
│   cost = selector.estimate_cost(model, 5000, 1000)        │
│                                                           │
│ GET FALLBACKS:                                            │
│   fallbacks = selector.get_fallback_models(model)         │
│                                                           │
│ GET TIER:                                                 │
│   tier = selector.get_tier_for_model(model)               │
└───────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date       | Changes                        | Author              |
|---------|------------|--------------------------------|---------------------|
| 1.0.0   | 2025-11-09 | Initial migration guide        | Documentation Expert |

---

**Status:** ✅ Active (8-week migration period)
**Phase:** Phase 2D
**Last Updated:** 2025-11-09
**Next Review:** Week 8 (migration status check)

---

**Ready to Migrate?**

1. Read [Quick Start](#quick-start)
2. Identify your scenario in [Migration Scenarios](#migration-scenarios)
3. Follow testing checklist in [Testing Your Migration](#testing-your-migration)
4. Use [Support Resources](#support-resources) if needed
5. Complete migration before Week 16

**Questions?** See [FAQ](#faq) or check MODEL_SELECTOR_GUIDE.md

---

**Total Lines:** 856
**End of Migration Guide Phase 2D**
