# Model Selection Code Audit

## Summary
Found **45+ hardcoded model references** across 11 files that should use the centralized ModelSelector.

## Detailed Findings

| File | Line | Current Code | Suggested Replacement |
|------|------|--------------|----------------------|
| **agent_system.py** | | | |
| | 51-55 | Hardcoded model pricing dict | Use `from core.constants import Models` |
| | 457 | `model: str = 'claude-3-5-haiku-20241022'` | `model: str = Models.HAIKU` |
| **self_healing_chains.py** | | | |
| | 38 | `"model": "claude-3-5-haiku-20241022"` | `"model": Models.HAIKU` |
| | 80 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 141 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 198 | `"model": "claude-3-5-haiku-20241022"` | `"model": Models.HAIKU` |
| | 376 | `model="claude-3-5-haiku-20241022"` | `model=Models.HAIKU` |
| | 385 | `model="claude-3-5-sonnet-20241022"` | `model=Models.SONNET` |
| | 394 | `model="claude-3-5-sonnet-20241022"` | `model=Models.SONNET` |
| | 403 | `model="claude-3-5-haiku-20241022"` | `model=Models.HAIKU` |
| | 585-586 | Hardcoded model switch | Use ModelSelector |
| **cognitive_processing.py** | | | |
| | 46 | `"model": "claude-3-5-haiku-20241022"` | `"model": Models.HAIKU` |
| | 91 | `"model": "claude-3-5-haiku-20241022"` | `"model": Models.HAIKU` |
| | 152 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 226 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 306 | `"model": "claude-3-5-haiku-20241022"` | `"model": Models.HAIKU` |
| | 367 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 436 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 503 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 652, 657 | `model="claude-3-5-haiku-20241022"` | `model=Models.HAIKU` |
| | 831, 836 | `model="claude-3-5-sonnet-20241022"` | `model=Models.SONNET` |
| | 1125, 1130 | `model="claude-3-5-sonnet-20241022"` | `model=Models.SONNET` |
| **distributed_clusters.py** | | | |
| | 42 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 123 | `"model": "claude-3-5-haiku-20241022"` | `"model": Models.HAIKU` |
| | 190 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 278 | `"model": "claude-3-5-sonnet-20241022"` | `"model": Models.SONNET` |
| | 411 | `model: str = "claude-3-5-haiku-20241022"` | `model: str = Models.HAIKU` |
| | 437-439 | `if "haiku" in model:` logic | Use ModelSelector |
| | 447-449 | Hardcoded pricing dict | Import from core.constants |
| | 568 | `model="claude-3-5-sonnet-20241022"` | `model=Models.SONNET` |
| | 699 | `model="claude-3-5-sonnet-20241022"` | `model=Models.SONNET` |
| | 979-980 | Hardcoded model list | Use Models constants |
| | 1148 | `model = "claude-3-5-haiku-20241022"` | `model = Models.HAIKU` |
| **autonomous_ecosystem.py** | | | |
| | 390-392 | Hardcoded model list | Use Models constants |
| **dynamic_spawner.py** | | | |
| | 419-423 | Model costs dict with string keys | Should use ModelSelector |
| | 426-438 | Agent-to-model mapping | Should use ModelSelector.select() based on complexity |
| | 442 | `model = agent_models.get(agent, 'haiku')` | `model = ModelSelector.select(complexity)` |
| **orchestrator.py** | | | |
| | 53 | `model: str = 'claude-3-5-haiku-20241022'` | `model: str = Models.HAIKU` |
| **expert_agents.py** | | | |
| | 70 | `'claude-3-5-haiku-20241022'` | `Models.HAIKU` |
| | 199 | `model="claude-3-5-sonnet-20241022"` | `model=Models.SONNET` |
| | 423 | `model="claude-3-5-haiku-20241022"` | `model=Models.HAIKU` |
| **prompt_evolution.py** | | | |
| | 341 | `model="claude-3-5-haiku-20241022"` | `model=Models.HAIKU` |
| **test_library.py** | | | |
| | 25 | `model="claude-3-5-haiku-20241022"` | `model=Models.HAIKU` |
| | 35 | `"claude-3-5-haiku-20241022"` | `Models.HAIKU` |

## Model Selection Logic Patterns Found

### Pattern 1: Direct String Assignment
```python
# Current (45+ instances)
model = "claude-3-5-haiku-20241022"

# Should be:
from core.constants import Models
model = Models.HAIKU
```

### Pattern 2: Role-Based Selection
```python
# Current (dynamic_spawner.py)
agent_models = {
    AgentRole.ARCHITECT: 'sonnet',
    AgentRole.SECURITY_AUDITOR: 'sonnet',
    AgentRole.TEST_SPECIALIST: 'haiku',
}

# Should be:
from core.models import ModelSelector
model = ModelSelector.select('high' if critical_role else 'low')
```

### Pattern 3: Conditional Selection
```python
# Current (distributed_clusters.py:437)
if "haiku" in model:
    reliability = 0.95
elif "sonnet" in model:
    reliability = 0.97

# Should be:
from core.constants import Models
if model == Models.HAIKU:
    reliability = 0.95
elif model == Models.SONNET:
    reliability = 0.97
```

### Pattern 4: Cost-Based Selection
```python
# Current (multiple files)
# Comment: "Use cheap model for X"
model = "claude-3-5-haiku-20241022"

# Should be:
from core.models import ModelSelector
model = ModelSelector.select('low', cost_sensitive=True)
```

### Pattern 5: Intelligence-Based Selection
```python
# Current (self_healing_chains.py)
# Comment: "Need intelligence for healing"
model = "claude-3-5-sonnet-20241022"

# Should be:
from core.models import ModelSelector
model = ModelSelector.select('high')  # Complex healing task
```

## Statistics

- **Total hardcoded model strings:** 45+
- **Files affected:** 11
- **Duplicate model selection logic:** 5 distinct patterns
- **Potential lines saved:** ~300 lines after refactoring

## Validation

All 5 major model selection patterns identified:
✅ Direct hardcoded strings (45 instances)
✅ Role-based mapping (dynamic_spawner)
✅ Conditional selection (distributed_clusters)
✅ Cost-based comments (self_healing_chains)
✅ Intelligence-based comments (cognitive_processing)

## Recommended Refactoring Order

1. **Quick wins:** Replace all hardcoded strings with Models constants (5 minutes)
2. **Medium:** Update conditional logic to use ModelSelector (15 minutes)
3. **Complex:** Refactor role-based mappings to use complexity scoring (30 minutes)