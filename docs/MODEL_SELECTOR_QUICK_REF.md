# ModelSelector Quick Reference

**Version:** 1.0.0
**Last Updated:** 2025-11-09

---

## One-Page Cheat Sheet

### Import Statements

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity
```

---

## Basic Usage

### 1. Simple Selection

```python
selector = ModelSelector()

context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)

model = selector.select_model(context)
# Returns: "claude-opus-4-20250514" (premium tier)
```

### 2. Budget-Aware Selection

```python
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH,
    budget=0.005  # Max $0.005 per request
)

model = selector.select_model(context)
# Returns: economy tier if needed to stay within budget
```

### 3. Latency-Aware Selection

```python
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.MEDIUM,
    latency_requirement_ms=500  # Need fast response
)

model = selector.select_model(context)
# Returns: faster model (Haiku)
```

---

## Task Types & Complexity

### Task Types

```python
TaskType.ANALYSIS        # Deep analysis, reasoning
TaskType.CRITIQUE        # Code review, quality assessment
TaskType.VALIDATION      # Checking correctness
TaskType.SUMMARIZATION   # Creating summaries
TaskType.EXTRACTION      # Extracting structured data
TaskType.CODE_GENERATION # Generating code
TaskType.GENERAL         # Catch-all
```

### Complexity Levels

```python
TaskComplexity.LOW       # Simple tasks
TaskComplexity.MEDIUM    # Standard tasks
TaskComplexity.HIGH      # Complex tasks
TaskComplexity.CRITICAL  # Mission-critical tasks
```

---

## Tier Selection Matrix

| Task Type | Complexity | Default Tier | Cost/1K tokens |
|-----------|-----------|--------------|----------------|
| ANALYSIS | CRITICAL | premium | $0.015 |
| ANALYSIS | HIGH | premium | $0.015 |
| ANALYSIS | MEDIUM | standard | $0.003 |
| ANALYSIS | LOW | economy | $0.00025 |
| CRITIQUE | CRITICAL | premium | $0.015 |
| CRITIQUE | HIGH | premium | $0.015 |
| CRITIQUE | MEDIUM | standard | $0.003 |
| CRITIQUE | LOW | standard | $0.003 |
| VALIDATION | CRITICAL | premium | $0.015 |
| VALIDATION | HIGH | standard | $0.003 |
| VALIDATION | MEDIUM | standard | $0.003 |
| VALIDATION | LOW | economy | $0.00025 |
| SUMMARIZATION | HIGH | standard | $0.003 |
| SUMMARIZATION | MEDIUM | economy | $0.00025 |
| SUMMARIZATION | LOW | economy | $0.00025 |
| EXTRACTION | * | economy | $0.00025 |

---

## Common Patterns

### Pattern 1: ValidationOrchestrator Integration

```python
from validation import ValidationCore
from utils.model_selector import TaskComplexity

validator = ValidationCore()

# Internally uses ModelSelector
result = validator.validate(
    code=code_string,
    complexity=TaskComplexity.HIGH
)
```

### Pattern 2: CriticOrchestrator Integration

```python
from critic_orchestrator import CriticOrchestrator

critic = CriticOrchestrator()

# Internally maps critique_type to complexity
result = critic.critique(
    code_snippet=code,
    critique_type="security"  # Maps to CRITICAL
)
```

### Pattern 3: Orchestrator Workflow

```python
from orchestrator import Orchestrator, SubAgent
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Select models for agents
analyzer_model = selector.select_model(
    ModelSelectionContext(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.HIGH
    )
)

summarizer_model = selector.select_model(
    ModelSelectionContext(
        task_type=TaskType.SUMMARIZATION,
        complexity=TaskComplexity.LOW
    )
)

orch = Orchestrator()
orch.add_agent("analyzer", SubAgent(role="Analyzer", model=analyzer_model))
orch.add_agent("summarizer", SubAgent(role="Summarizer", model=summarizer_model))
```

### Pattern 4: Fallback Chain

```python
primary_model = selector.select_model(context)
fallbacks = selector.get_fallback_models(primary_model)

for model in fallbacks:
    try:
        result = agent.execute(model=model, prompt=prompt)
        break
    except ProviderError:
        continue
```

---

## Cost Estimation

```python
model = selector.select_model(context)

cost = selector.estimate_cost(
    model=model,
    input_tokens=5000,
    output_tokens=1000
)

print(f"Estimated cost: ${cost:.4f}")
```

---

## Custom Configuration

### Environment Variables

```bash
# .env
MODEL_SELECTOR_PREMIUM="gpt-4-turbo"
MODEL_SELECTOR_STANDARD="claude-sonnet-4-5-20250929"
MODEL_SELECTOR_ECONOMY="claude-haiku-4-20250514"
MODEL_SELECTOR_PROVIDER="anthropic"
```

### Runtime Configuration

```python
custom_config = {
    "model_tiers": {
        "premium": "gpt-4-turbo",
        "standard": "claude-sonnet-4-5-20250929",
        "economy": "claude-haiku-4-20250514"
    },
    "task_overrides": {
        "CRITIQUE": {
            "MEDIUM": "premium"  # Upgrade medium critiques
        }
    }
}

selector = ModelSelector(config=custom_config)
```

---

## Helper Methods

```python
# Get tier for model
tier = selector.get_tier_for_model("claude-opus-4-20250514")
# Returns: "premium"

# Get all models in tier
models = selector.get_models_in_tier("standard")
# Returns: ["claude-sonnet-4-5-20250929", ...]

# Get fallback chain
fallbacks = selector.get_fallback_models("claude-opus-4-20250514")
# Returns: ["claude-opus-4-20250514", "claude-opus-4-5", "gpt-4-turbo"]
```

---

## Troubleshooting Quick Fixes

### Issue: Model not found
```python
# Add to custom config
custom_config = {
    "model_tiers": {
        "premium": "your-model-id"
    }
}
selector = ModelSelector(config=custom_config)
```

### Issue: Wrong tier selected
```python
# Override complexity or use task_overrides
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.CRITICAL  # Force premium
)
```

### Issue: Environment variables not loading
```python
# Load before creating ModelSelector
from dotenv import load_dotenv
load_dotenv()

selector = ModelSelector()
```

---

## Model Tiers

### Premium Tier (Opus)
- **Model:** `claude-opus-4-20250514`
- **Cost:** $15/1M tokens
- **Use For:** Critical tasks, security, complex reasoning
- **Don't Use For:** Simple tasks, high-volume batch processing

### Standard Tier (Sonnet)
- **Model:** `claude-sonnet-4-5-20250929`
- **Cost:** $3/1M tokens (80% cheaper than premium)
- **Use For:** Most tasks (default choice)
- **Don't Use For:** Mission-critical security, simple extraction

### Economy Tier (Haiku)
- **Model:** `claude-haiku-4-20250514`
- **Cost:** $0.25/1M tokens (98% cheaper than premium!)
- **Use For:** Simple extraction, formatting, high-volume tasks
- **Don't Use For:** Security-sensitive, complex reasoning

---

## Migration Quick Guide

### Before (Hardcoded)
```python
model = "claude-opus-4-20250514"
```

### After (ModelSelector)
```python
selector = ModelSelector()
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
model = selector.select_model(context)
```

---

## Cost Savings Examples

### Example 1: Using Economy for Extraction
```python
# Before: Opus for everything
# 10,000 extractions × $0.015 = $150/day

# After: Economy for extraction
# 10,000 extractions × $0.00025 = $2.50/day
# Savings: 98% ($147.50/day)
```

### Example 2: Budget-Aware Selection
```python
# Tight budget forces downgrade
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH,
    budget=0.001
)
model = selector.select_model(context)
# Auto-downgrades to economy tier
```

---

## Full API Reference

See `/home/jevenson/.claude/lib/docs/MODEL_SELECTOR_GUIDE.md` for:
- Complete API reference
- Detailed usage patterns
- Cost optimization strategies
- Advanced features
- Troubleshooting guide

---

## Migration Guide

See `/home/jevenson/.claude/lib/docs/MIGRATION_GUIDE_PHASE_2D.md` for:
- Step-by-step migration instructions
- Before/after code examples
- Migration timeline
- Testing checklist

---

**Quick Access:**
- **Full Guide:** `docs/MODEL_SELECTOR_GUIDE.md`
- **Migration Guide:** `docs/MIGRATION_GUIDE_PHASE_2D.md`
- **ADR-003:** `docs/adr/ADR-003-centralize-model-selection.md`
- **Tests:** `tests/test_model_selector.py`

---

**Total Lines:** 317
