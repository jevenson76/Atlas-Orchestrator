# ADR-003: Centralize Model Selection Logic

**Status:** Accepted
**Date:** 2025-11-09
**Deciders:** Backend Specialist, Tech Lead, Architect
**Tags:** #refactoring #dry #architecture

---

## Context

### The Problem: Model Selection Logic Duplication

Model selection logic is **duplicated across 3 orchestrators**, totaling ~600 lines of repetitive code:

**1. ValidationOrchestrator** (~200 lines)
```python
def _select_validator_model(self, complexity: str) -> str:
    """Select model based on validation complexity."""
    if complexity == "high":
        return "claude-opus-4-20250514"
    elif complexity == "medium":
        return "claude-sonnet-3-7-20250219"
    else:
        return "claude-haiku-3-5-20250318"
```

**2. CriticOrchestrator** (~180 lines)
```python
def _select_critic_model(self, critique_type: str) -> str:
    """Select model for critique generation."""
    if critique_type in ["security", "architecture"]:
        return "claude-opus-4-20250514"
    elif critique_type == "code_quality":
        return "claude-sonnet-3-7-20250219"
    else:
        return "claude-haiku-3-5-20250318"
```

**3. Orchestrator** (~220 lines)
```python
def _select_subagent_model(self, task_type: str, budget: float) -> str:
    """Select model for subagent task."""
    if task_type == "analysis" and budget > 0.01:
        return "claude-opus-4-20250514"
    elif task_type in ["summarization", "extraction"]:
        return "claude-sonnet-3-7-20250219"
    else:
        return "claude-haiku-3-5-20250318"
```

### The Cost of Duplication

**1. Inconsistent Model Selection**
- Different orchestrators use different criteria for same task
- Example: "analysis" → Opus in Orchestrator, Sonnet in ValidationOrchestrator
- No unified strategy

**2. Maintenance Burden**
- New model added → update 3+ locations
- Cost optimization → change 3+ files
- Bug fix → replicate across orchestrators

**3. Testing Complexity**
- Same logic tested 3 times
- Test drift: Tests diverge, miss edge cases
- 180+ lines of duplicated test code

**4. Configuration Fragmentation**
- Model mappings hardcoded in each orchestrator
- No central configuration
- Difficult to A/B test model strategies

**5. Inability to Optimize Globally**
- Can't easily implement:
  - Time-of-day pricing (use cheaper models off-peak)
  - Provider quota management
  - Cross-orchestrator cost budgets

### Real-World Impact

**Scenario 1: New Model Release**
```
Claude Sonnet 4.0 released → Must update:
- validation_orchestrator.py
- critic_orchestrator.py
- orchestrator.py
- All corresponding tests
= 4-6 hours of work
```

**Scenario 2: Cost Optimization**
```
Need to reduce costs by 30% → Must:
- Analyze usage patterns in 3 orchestrators
- Change model mappings in 3 places
- Update thresholds inconsistently
- Risk breaking changes due to drift
= 8-12 hours + potential bugs
```

---

## Decision

**Create a centralized `ModelSelector` utility in `lib/utils/model_selector.py`** that encapsulates all model selection logic.

### Architecture

```python
# lib/utils/model_selector.py

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass

class TaskComplexity(Enum):
    """Task complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskType(Enum):
    """Task types for model selection."""
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    CRITIQUE = "critique"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    CODE_GENERATION = "code_generation"

@dataclass
class ModelSelectionContext:
    """Context for model selection decisions."""
    task_type: TaskType
    complexity: TaskComplexity
    budget: Optional[float] = None
    quality_threshold: float = 0.85
    latency_requirement_ms: Optional[int] = None
    provider_preference: Optional[str] = None

class ModelSelector:
    """Centralized model selection logic."""

    # Default model tier mappings
    MODEL_TIERS = {
        "premium": "claude-opus-4-20250514",       # $15/1M tokens
        "standard": "claude-sonnet-3-7-20250219",  # $3/1M tokens
        "economy": "claude-haiku-3-5-20250318",    # $0.25/1M tokens
    }

    # Task-specific overrides
    TASK_MODEL_MAP = {
        TaskType.ANALYSIS: {
            TaskComplexity.CRITICAL: "premium",
            TaskComplexity.HIGH: "premium",
            TaskComplexity.MEDIUM: "standard",
            TaskComplexity.LOW: "economy",
        },
        TaskType.CRITIQUE: {
            TaskComplexity.CRITICAL: "premium",
            TaskComplexity.HIGH: "premium",
            TaskComplexity.MEDIUM: "standard",
            TaskComplexity.LOW: "standard",  # Critiques need quality
        },
        TaskType.SUMMARIZATION: {
            TaskComplexity.CRITICAL: "standard",
            TaskComplexity.HIGH: "standard",
            TaskComplexity.MEDIUM: "economy",
            TaskComplexity.LOW: "economy",
        },
    }

    def __init__(self, config: Optional[Dict] = None):
        """Initialize with optional custom configuration."""
        self.config = config or {}
        self._load_model_tiers()

    def select_model(self, context: ModelSelectionContext) -> str:
        """
        Select optimal model based on context.

        Args:
            context: Selection context (task type, complexity, budget, etc.)

        Returns:
            Model identifier string

        Raises:
            ValueError: If invalid context provided
        """
        # Get base tier from task/complexity mapping
        tier = self._get_tier_for_task(context.task_type, context.complexity)

        # Apply budget constraints
        if context.budget is not None:
            tier = self._adjust_for_budget(tier, context.budget)

        # Apply latency requirements
        if context.latency_requirement_ms is not None:
            tier = self._adjust_for_latency(tier, context.latency_requirement_ms)

        # Apply provider preferences
        if context.provider_preference:
            return self._get_model_for_provider(tier, context.provider_preference)

        return self.MODEL_TIERS[tier]

    def get_fallback_models(self, primary_model: str) -> list[str]:
        """Get quality-tiered fallback models for a primary model."""
        # Implementation returns appropriate fallbacks
        pass

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a model given token counts."""
        # Implementation calculates cost
        pass
```

### Usage in Orchestrators

**Before:**
```python
# validation_orchestrator.py
def _select_validator_model(self, complexity: str) -> str:
    if complexity == "high":
        return "claude-opus-4-20250514"
    elif complexity == "medium":
        return "claude-sonnet-3-7-20250219"
    else:
        return "claude-haiku-3-5-20250318"

model = self._select_validator_model(task_complexity)
```

**After:**
```python
# validation_orchestrator.py
from utils.model_selector import ModelSelector, ModelSelectionContext, TaskType, TaskComplexity

model_selector = ModelSelector()

context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity(task_complexity),
    budget=self.budget_per_task
)

model = model_selector.select_model(context)
```

---

## Rationale

### Why Centralize?

**1. DRY Principle (Don't Repeat Yourself)**
- Single source of truth for model selection
- Change once, apply everywhere
- Eliminates drift between orchestrators

**2. Consistency**
- Uniform model selection across entire system
- Same task + complexity → same model (always)
- Predictable cost and quality

**3. Configurability**
```python
# Easy to swap model tiers via configuration
model_selector = ModelSelector(config={
    "model_tiers": {
        "premium": "gpt-4-turbo",  # Switch to OpenAI
        "standard": "claude-sonnet-3-7-20250219",
        "economy": "claude-haiku-3-5-20250318"
    }
})
```

**4. Testability**
- Test model selection logic once, comprehensively
- Mock ModelSelector in orchestrator tests
- Clear separation of concerns

**5. Advanced Features Unlocked**
```python
# Time-based pricing
model_selector.select_model(context, current_hour=3)  # Use cheaper models at 3 AM

# Provider quota management
model_selector.track_quota("anthropic", tokens_used=1500)

# A/B testing
model_selector.select_model(context, experiment_group="variant_b")
```

### Why This Design?

**Enum-Based Task Types**
- Type-safe task categorization
- IDE autocomplete support
- Prevents typos ("anlaysis" vs "analysis")

**Context Object Pattern**
- Extensible (add new selection criteria without breaking API)
- Explicit (all factors visible at call site)
- Testable (easy to construct test contexts)

**Tier-Based Abstraction**
- Decouple "quality level" from "specific model"
- Easy to swap underlying models
- Clear cost implications (premium > standard > economy)

---

## Consequences

### Positive

✅ **Reduced Code Duplication**
- 600 lines → 300 lines (50% reduction)
- Single implementation, reused everywhere

✅ **Improved Maintainability**
```bash
# Before: Update 3 files
vim validation_orchestrator.py critic_orchestrator.py orchestrator.py

# After: Update 1 file
vim utils/model_selector.py
```

✅ **Consistent Model Selection**
- Same task → same model
- No more "analysis uses Opus here, Sonnet there"

✅ **Enhanced Testing**
```python
# Test ModelSelector comprehensively once
def test_premium_tier_for_critical_analysis():
    context = ModelSelectionContext(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.CRITICAL
    )
    assert model_selector.select_model(context) == "claude-opus-4-20250514"

# Mock in orchestrator tests
@patch('utils.model_selector.ModelSelector')
def test_orchestrator(mock_selector):
    mock_selector.select_model.return_value = "test-model"
    # Test orchestrator logic without caring about actual model
```

✅ **Cost Optimization Opportunities**
```python
# Implement budget-aware selection
context = ModelSelectionContext(
    task_type=TaskType.SUMMARIZATION,
    complexity=TaskComplexity.MEDIUM,
    budget=0.001  # Tight budget
)
model = selector.select_model(context)  # Automatically downgrades to economy
```

✅ **Configuration-Driven**
```yaml
# config/models.yaml
model_tiers:
  premium: claude-opus-4-20250514
  standard: claude-sonnet-3-7-20250219
  economy: claude-haiku-3-5-20250318

task_overrides:
  critique:
    high: premium  # Always use premium for high-complexity critiques
```

### Negative

❌ **All Orchestrators Depend on ModelSelector**
- Tight coupling to single utility
- Changes to ModelSelector affect everyone
- **Mitigation:** Comprehensive tests, semantic versioning, deprecation warnings

❌ **Increased Abstraction**
- Developers must understand ModelSelector API
- Less obvious which model is selected
- **Mitigation:** Clear documentation, logging, `explain_selection()` method

❌ **Potential Performance Overhead**
- Enum conversions, context object creation
- **Reality Check:** Negligible (<0.1ms), API latency dominates (500-2000ms)

❌ **Risk of Over-Engineering**
- Could add too many features to ModelSelector
- **Mitigation:** Start simple, add features only when needed (YAGNI)

### Migration Impact

**Breaking Changes:**
- Orchestrators can't use `_select_model()` methods directly
- Must import and use ModelSelector

**Backward Compatibility:**
```python
# Temporary shim during migration
def _select_validator_model(self, complexity: str) -> str:
    warnings.warn("Use ModelSelector instead", DeprecationWarning)
    context = ModelSelectionContext(
        task_type=TaskType.VALIDATION,
        complexity=TaskComplexity(complexity)
    )
    return self.model_selector.select_model(context)
```

---

## Alternatives Considered

### Alternative 1: Keep Duplicated Logic
**Rejected** - Technical debt compounds, inconsistencies grow.

**Pros:**
- No migration effort
- Each orchestrator fully independent

**Cons:**
- Maintenance nightmare
- Inconsistent behavior
- Difficult to optimize globally

### Alternative 2: Configuration File Only
**Rejected** - No logic for dynamic selection.

```yaml
# config/models.yaml
validation:
  high: claude-opus-4-20250514
  medium: claude-sonnet-3-7-20250219
  low: claude-haiku-3-5-20250318
```

**Pros:**
- Simple, declarative
- Easy to modify

**Cons:**
- No budget-aware selection
- No latency-based adjustment
- No advanced features (time-based pricing, A/B testing)
- Still requires duplication (each orchestrator reads config)

### Alternative 3: Strategy Pattern with Plugins
**Rejected** - Over-engineered for current needs.

```python
class ModelSelectionStrategy(ABC):
    @abstractmethod
    def select(self, context: ModelSelectionContext) -> str:
        pass

class CostOptimizedStrategy(ModelSelectionStrategy):
    def select(self, context):
        return "claude-haiku-3-5-20250318"  # Always cheapest

class QualityOptimizedStrategy(ModelSelectionStrategy):
    def select(self, context):
        return "claude-opus-4-20250514"  # Always best
```

**Pros:**
- Maximum flexibility
- Easy to add new strategies

**Cons:**
- Too complex for simple mappings
- Adds indirection
- YAGNI (no current need for pluggable strategies)

### Alternative 4: Hardcode in ResilientBaseAgent
**Rejected** - Violates separation of concerns.

```python
# agent_system.py
class ResilientBaseAgent:
    def __init__(self, task_type: str, complexity: str):
        # Agent itself decides which model to use
        self.model = self._select_model(task_type, complexity)
```

**Pros:**
- Selection logic close to execution

**Cons:**
- Agent shouldn't know about task semantics
- Violates single responsibility
- Makes agent harder to test
- Less flexible (can't override per orchestrator)

---

## Implementation Plan

### Phase 1: Create ModelSelector (Week 1)
- [ ] Create `utils/model_selector.py`
- [ ] Implement core selection logic
- [ ] Add comprehensive unit tests
- [ ] Document API

### Phase 2: Migrate ValidationOrchestrator (Week 2)
- [ ] Add ModelSelector dependency
- [ ] Replace `_select_validator_model()`
- [ ] Add deprecation warnings
- [ ] Update tests

### Phase 3: Migrate CriticOrchestrator (Week 3)
- [ ] Add ModelSelector dependency
- [ ] Replace `_select_critic_model()`
- [ ] Update tests

### Phase 4: Migrate Orchestrator (Week 4)
- [ ] Add ModelSelector dependency
- [ ] Replace `_select_subagent_model()`
- [ ] Update tests

### Phase 5: Cleanup (Week 5-12)
- [ ] Remove deprecated methods after 8 weeks
- [ ] Remove backward compatibility shims
- [ ] Update documentation

---

## Testing Strategy

### Unit Tests for ModelSelector

```python
class TestModelSelector:
    def test_premium_tier_for_critical_tasks(self):
        context = ModelSelectionContext(
            task_type=TaskType.ANALYSIS,
            complexity=TaskComplexity.CRITICAL
        )
        assert selector.select_model(context) == "claude-opus-4-20250514"

    def test_budget_constraint_downgrade(self):
        context = ModelSelectionContext(
            task_type=TaskType.SUMMARIZATION,
            complexity=TaskComplexity.HIGH,
            budget=0.0005  # Very tight budget
        )
        # Should downgrade to economy despite high complexity
        assert selector.select_model(context) == "claude-haiku-3-5-20250318"

    def test_latency_requirement_selection(self):
        context = ModelSelectionContext(
            task_type=TaskType.EXTRACTION,
            complexity=TaskComplexity.MEDIUM,
            latency_requirement_ms=500  # Need fast response
        )
        # Should prefer Haiku for low latency
        assert selector.select_model(context) == "claude-haiku-3-5-20250318"
```

### Integration Tests

```python
def test_orchestrator_uses_model_selector():
    """Test that orchestrators actually use ModelSelector."""
    orchestrator = Orchestrator()
    with patch.object(orchestrator.model_selector, 'select_model') as mock:
        mock.return_value = "test-model"
        orchestrator.run_subagent(task_type="analysis")
        mock.assert_called_once()
```

---

## Monitoring & Metrics

### Track Model Selection Decisions

```python
logger.info(
    "Model selected",
    extra={
        "task_type": context.task_type.value,
        "complexity": context.complexity.value,
        "selected_model": model,
        "tier": tier,
        "budget_constraint": context.budget,
        "selection_time_ms": elapsed_ms
    }
)
```

### Dashboard Metrics

```
Model Selection Analytics (24h)
├── Total Selections: 5,432
├── Tier Distribution:
│   ├── Premium: 18% (978 selections)
│   ├── Standard: 56% (3,042 selections)
│   └── Economy: 26% (1,412 selections)
├── Budget Downgrades: 142 (2.6%)
├── Provider Overrides: 23 (0.4%)
└── Avg Selection Time: 0.08ms
```

---

## References

- **DRY Principle** - *The Pragmatic Programmer* by Hunt & Thomas
- **Strategy Pattern** - *Design Patterns* by Gang of Four
- **Configuration Management** - *The Twelve-Factor App*
- **Model Pricing** - Anthropic/OpenAI pricing pages

---

## Implementation Details

**Status:** ⏳ In Progress (Phase 2D)

### Files Created

```
utils/
├── __init__.py               # Package initialization, exports
└── model_selector.py         # ModelSelector class (TBD: actual line count)
```

### Actual Code Reduction

**Estimated:**
- Before: 600 lines (duplicated across 3 orchestrators)
- After: 300 lines (centralized) + 150 lines (integration) = 450 lines
- **Reduction:** 25% (150 lines eliminated)

**Actual:** (To be updated after implementation)
- Before: TBD lines
- After: TBD lines
- **Reduction:** TBD%

### Integration Points

**Where ModelSelector is Used:**

1. **validation/core.py** - ValidationCore uses ModelSelector
   - Replaces `_select_validator_model()`
   - Complexity → TaskComplexity enum mapping

2. **critic_orchestrator.py** - CriticOrchestrator uses ModelSelector
   - Replaces `_select_critic_model()`
   - Critique type → TaskComplexity mapping

3. **orchestrator.py** - Base Orchestrator uses ModelSelector
   - Replaces `_select_subagent_model()`
   - SubAgent model selection centralized

### Lessons Learned

**What Worked:**
- (To be filled in after implementation)

**What Didn't Work:**
- (To be filled in after implementation)

**Challenges:**
- (To be filled in after implementation)

**Surprises:**
- (To be filled in after implementation)

---

## Future Enhancements

**Potential Improvements:**

1. **Time-Based Pricing**
   - Use economy tier during off-peak hours (e.g., 12am-6am)
   - Reduce costs by 30-50% for non-urgent tasks

2. **Provider Quota Management**
   - Track API usage across providers
   - Auto-switch to alternate provider when quota nearing limit

3. **A/B Testing Support**
   - Experiment with different model tiers
   - Measure quality/cost trade-offs

4. **Quality-Based Auto-Tuning**
   - Monitor output quality scores
   - Automatically adjust tier mappings for optimal quality/cost

5. **Multi-Model Ensembles**
   - Run same task with multiple models
   - Aggregate results for higher confidence

6. **Cost Prediction Dashboard**
   - Real-time cost tracking
   - Budget alerts and recommendations

---

## Revision History

| Date       | Version | Changes                        | Author              |
|------------|---------|--------------------------------|---------------------|
| 2025-11-09 | 1.0     | Initial ADR                    | Documentation Expert |
| 2025-11-09 | 1.1     | Added implementation tracking  | Documentation Expert |

---

**Next Steps:**
1. ✅ ADR approved
2. ⏳ Backend Specialist creates `utils/model_selector.py`
3. ⏳ Test Specialist writes comprehensive test suite
4. ⏳ Backend Specialist migrates orchestrators
5. ⏳ Documentation Expert updates with actual metrics
