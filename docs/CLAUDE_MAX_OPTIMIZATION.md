# Optimal Model Selection with Claude Max Subscription

## Overview

With **Claude Max subscription**, all Anthropic models are **FREE** (no API costs). This fundamentally changes the optimization strategy from cost-focused to quality-focused.

---

## Updated Fallback Chain

### Primary Tier: Claude (FREE with Claude Max)
```
Opus 4.1 → Sonnet 3.5
```
**Haiku removed** - No longer used per user preference

### Cross-Provider Tier: Paid Models (Only When Claude Unavailable)
```
Grok 3 ($3/$15) → Gemini Pro (~$0.50/$1.50) → GPT-4 ($30/$60) → GPT-3.5 ($0.50/$1.50)
```

---

## Optimal Model Selection Strategy

### Decision Tree

```
Is task complex or requires validation?
  ├─ YES → Use Opus 4.1 (FREE, highest quality, UltraThink)
  └─ NO → Use Sonnet 3.5 (FREE, balanced, general-purpose)

Claude unavailable (rate limit, outage)?
  ├─ YES → Fallback to Grok 3 ($3/$15, balanced paid option)
  └─ NO → Stay with Claude (FREE)
```

### Task-to-Model Mapping

| Task Type | Model | Reason | Cost |
|-----------|-------|--------|------|
| **Quality Validation** | Opus 4.1 | UltraThink, highest accuracy | **FREE** |
| **Code Review** | Opus 4.1 | Deep reasoning, catches edge cases | **FREE** |
| **Critic/Judge** | Opus 4.1 | Auto UltraThink injection | **FREE** |
| **Self-Reflection** | Opus 4.1 | Complex reasoning required | **FREE** |
| **Complex Analysis** | Opus 4.1 | Maximum reasoning capability | **FREE** |
| **Code Generation** | Sonnet 3.5 | Balanced, fast, reliable | **FREE** |
| **Documentation** | Sonnet 3.5 | Clear, structured output | **FREE** |
| **General Tasks** | Sonnet 3.5 | Default choice | **FREE** |
| **Real-Time Search** | Grok 3 | Search capability (if Claude fails) | $3/$15 |
| **Budget Tasks** | Gemini Pro | Cheapest paid option | ~$0.50/$1.50 |

---

## Recommended Configurations

### Configuration 1: Quality-First (Recommended)

**Use Case**: Production workflows where quality matters

```python
from resilient_agent import ResilientBaseAgent
from core.constants import Models

# Validation/Critic: Always use Opus 4.1 (FREE + best quality)
critic_agent = ResilientBaseAgent(
    role="Quality Critic",
    model=Models.OPUS_4,          # FREE with Claude Max
    enable_fallback=True          # Fallback to Grok if needed
)

# General Tasks: Use Sonnet 3.5 (FREE + fast)
general_agent = ResilientBaseAgent(
    role="Task Processor",
    model=Models.SONNET,          # FREE with Claude Max
    enable_fallback=True          # Fallback to Grok if needed
)
```

**Workflow Example**:
1. Sonnet: Process task (FREE)
2. Opus 4.1: Validate output (FREE)
3. Opus 4.1: Generate final version (FREE)

**Total Cost**: $0.00 (all Claude)

---

### Configuration 2: Hybrid (Claude Primary, Grok Fallback)

**Use Case**: High-availability workflows

```python
# Primary: Claude (FREE)
# Fallback: Grok 3 (paid, only if Claude unavailable)

agent = ResilientBaseAgent(
    role="Resilient Processor",
    model=Models.SONNET,          # Try Sonnet first (FREE)
    enable_fallback=True          # Auto-fallback: Opus → Grok → Gemini → GPT
)
```

**Fallback Flow**:
```
Sonnet (FREE) → Opus (FREE) → Grok 3 ($3/$15) → Gemini (~$0.50) → GPT-4 ($30)
```

**Expected Cost**: $0.00 - $0.05 per task (Claude handles 99% of requests)

---

### Configuration 3: Multi-Agent Pipeline (All Claude)

**Use Case**: Complex multi-step workflows

```python
from orchestrator import Orchestrator, SubAgent, ExecutionMode

class OptimizedPipeline(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.SEQUENTIAL)

        # All agents use FREE Claude models
        self.agents = {
            "analyzer": SubAgent(
                role="Data Analyzer",
                model=Models.SONNET,      # FREE
                dependencies=set()
            ),
            "coder": SubAgent(
                role="Code Generator",
                model=Models.SONNET,      # FREE
                dependencies={"analyzer"}
            ),
            "validator": SubAgent(
                role="Quality Validator",
                model=Models.OPUS_4,      # FREE (UltraThink)
                dependencies={"coder"}
            ),
            "refiner": SubAgent(
                role="Output Refiner",
                model=Models.OPUS_4,      # FREE
                dependencies={"validator"}
            )
        }
```

**Pipeline Cost**: $0.00 (100% Claude)

---

## Anti-Patterns to Avoid

### ❌ DON'T: Use Haiku (Removed)

```python
# WRONG - Haiku removed per user preference
agent = ResilientBaseAgent(model=Models.HAIKU)
```

### ❌ DON'T: Use Paid Models When Claude Available

```python
# WRONG - Paying for Grok when Opus 4.1 is FREE
critic_agent = ResilientBaseAgent(
    model=Models.GROK_3,          # $3/$15 - UNNECESSARY
    enable_fallback=False
)

# RIGHT - Use FREE Opus 4.1
critic_agent = ResilientBaseAgent(
    model=Models.OPUS_4,          # FREE with Claude Max
    enable_fallback=True          # Fallback to Grok only if needed
)
```

### ❌ DON'T: Skip Opus for Quality Tasks

```python
# WRONG - Using paid Grok for validation when Opus is FREE
validator = ResilientBaseAgent(model=Models.GROK_3)  # Costs $3/$15

# RIGHT - Use FREE Opus 4.1 with UltraThink
validator = ResilientBaseAgent(model=Models.OPUS_4)  # FREE + better
```

---

## Cost Comparison: Before vs After Claude Max

### Before Claude Max (Pay-per-token)

**Workflow**: Security → Code → Validate
- Haiku (security): $0.25/$1.25 per 1M tokens
- Sonnet (code): $3/$15 per 1M tokens
- Opus (validate): $15/$75 per 1M tokens

**Strategy**: Use Haiku wherever possible to minimize cost

**Typical Cost**: $5-20 per 1000 tasks

---

### With Claude Max (FREE Claude)

**Workflow**: Process → Validate → Refine
- Sonnet (process): **FREE**
- Opus 4.1 (validate): **FREE**
- Opus 4.1 (refine): **FREE**

**Strategy**: Use Opus 4.1 liberally for maximum quality

**Typical Cost**: **$0.00** per 1000 tasks (100% Claude)

**Savings**: **100%** vs pay-per-token

---

## When to Use Paid Models (Grok/Gemini/GPT)

### Scenario 1: Claude Rate Limited

If you exceed Claude Max rate limits:
- Fallback automatically activates
- Grok 3 handles overflow ($3/$15)
- Maintains workflow continuity

### Scenario 2: Claude Outage

Rare, but possible:
- Circuit breaker detects repeated failures
- Switches to Grok 3 → Gemini → GPT
- Returns to Claude when available

### Scenario 3: Specialized Capabilities

**Real-time Search** (Grok advantage):
```python
# Grok has real-time search, Claude does not
search_agent = ResilientBaseAgent(
    model=Models.GROK_3,          # Intentional paid choice
    enable_fallback=False
)
```

**Vision Tasks** (if needed):
```python
# Grok 2 Vision for image analysis
vision_agent = ResilientBaseAgent(
    model=Models.GROK_2_VISION,   # $2/$10 per 1M
    enable_fallback=False
)
```

---

## Monitoring and Budget

### Track Paid Usage

```python
from agent_system import CostTracker

tracker = CostTracker(
    daily_budget=5.0,    # $5/day for paid models
    hourly_budget=1.0    # $1/hour limit
)

agent = ResilientBaseAgent(
    model=Models.SONNET,          # PRIMARY: FREE
    enable_fallback=True,         # FALLBACK: Paid models
    cost_tracker=tracker          # Track ONLY paid usage
)

# Check spending
report = tracker.get_report()
print(f"Paid model costs today: ${report['daily_spent']:.2f}")
```

**Expected Result**: $0.00 - $2.00/day (Claude handles 95-99% of load)

---

## Updated Model Recommendations

| Use Case | Model | Reason | Cost |
|----------|-------|--------|------|
| **Default Choice** | Sonnet 3.5 | Fast, reliable, FREE | **$0** |
| **Validation/QA** | Opus 4.1 | Highest quality, UltraThink | **$0** |
| **Code Review** | Opus 4.1 | Deep reasoning | **$0** |
| **Critic/Judge** | Opus 4.1 | Auto UltraThink | **$0** |
| **Documentation** | Sonnet 3.5 | Clear output | **$0** |
| **Complex Reasoning** | Opus 4.1 | Maximum capability | **$0** |
| **Fallback (Rate Limit)** | Grok 3 | Best paid option | $3/$15 |
| **Budget Fallback** | Gemini Pro | Cheapest paid | ~$0.50/$1.50 |
| **Emergency Only** | GPT-4 | Last resort | $30/$60 |

---

## Summary

### With Claude Max Subscription:

✅ **DO**:
- Use Opus 4.1 liberally (FREE + best quality)
- Use Sonnet 3.5 for general tasks (FREE)
- Enable fallback for resilience (Grok → Gemini → GPT)
- Monitor paid model usage (should be near $0)

❌ **DON'T**:
- Use Haiku (removed per preference)
- Choose paid models when Claude available
- Skip Opus for quality-critical tasks
- Disable fallback (loss of resilience)

### Expected Costs:

- **Claude usage**: $0.00 (100% FREE)
- **Fallback usage**: $0.00 - $2.00/day (rare)
- **Total**: ~$0.50/day average (99% FREE Claude, 1% paid fallback)

### Quality Improvement:

- **Before**: Used Haiku for cost → lower quality
- **After**: Use Opus 4.1 liberally → maximum quality
- **Result**: Better outputs at zero additional cost

---

**Last Updated**: November 7, 2025
**Version**: 2.0 (Claude Max Optimized)
**Maintained By**: ZeroTouch Atlas Team
