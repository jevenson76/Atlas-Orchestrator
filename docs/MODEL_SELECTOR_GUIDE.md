# Model Selector Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Active (Phase 2D)
**Phase:** 2D - Centralized Model Selection

---

## Table of Contents

1. [Overview](#overview)
2. [ModelSelector API Reference](#modelselector-api-reference)
3. [Model Tiers Explained](#model-tiers-explained)
4. [Task Types](#task-types)
5. [Usage Patterns](#usage-patterns)
6. [Provider Failover](#provider-failover)
7. [Cost Optimization](#cost-optimization)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Migration from Hardcoded Models](#migration-from-hardcoded-models)
11. [References](#references)

---

## Overview

### What is ModelSelector?

`ModelSelector` is a centralized utility that encapsulates all model selection logic across the orchestrator system. Instead of duplicating model selection code in 3+ orchestrators, ModelSelector provides a **single source of truth** for choosing the right AI model for each task.

### The Problem: Duplication and Inconsistency

**Before ModelSelector:**
```
validation_orchestrator.py   _select_validator_model()   200 lines
critic_orchestrator.py        _select_critic_model()      180 lines
orchestrator.py               _select_subagent_model()    220 lines
                                                          ─────────
                                                Total:     600 lines (duplicated)
```

**Issues:**
- Same model selection logic duplicated 3+ times
- Inconsistent criteria: "analysis" → Opus in one orchestrator, Sonnet in another
- Hard to update: New model release requires updating 3+ files
- Difficult to optimize: Can't implement global cost strategies

**After ModelSelector:**
```
utils/model_selector.py       ModelSelector class         300 lines (centralized)
validation_orchestrator.py    uses ModelSelector          50 lines (removed duplication)
critic_orchestrator.py        uses ModelSelector          50 lines (removed duplication)
orchestrator.py               uses ModelSelector          50 lines (removed duplication)
                                                          ─────────
                                                Total:     450 lines (25% reduction)
```

**Benefits:**
- ✅ **DRY (Don't Repeat Yourself):** Single implementation, reused everywhere
- ✅ **Consistency:** Same task + complexity → same model (always)
- ✅ **Easy Updates:** New model? Update one file
- ✅ **Cost Optimization:** Global budget-aware selection
- ✅ **Configuration-Driven:** Swap model tiers via config
- ✅ **Advanced Features:** Time-based pricing, A/B testing, quota management

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                     ModelSelector                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  MODEL_TIERS (configuration)                       │  │
│  │  ┌──────────┬──────────┬──────────┐                │  │
│  │  │ premium  │ standard │ economy  │                │  │
│  │  │ Opus     │ Sonnet   │ Haiku    │                │  │
│  │  │ $15/1M   │ $3/1M    │ $0.25/1M │                │  │
│  │  └──────────┴──────────┴──────────┘                │  │
│  │                                                     │  │
│  │  TASK_MODEL_MAP (task-complexity matrix)           │  │
│  │  ┌──────────────┬────────────────────────────────┐ │  │
│  │  │ TaskType     │ Complexity → Tier              │ │  │
│  │  ├──────────────┼────────────────────────────────┤ │  │
│  │  │ ANALYSIS     │ HIGH → premium, LOW → economy  │ │  │
│  │  │ CRITIQUE     │ HIGH → premium, LOW → standard │ │  │
│  │  │ SUMMARIZATION│ HIGH → standard, LOW → economy │ │  │
│  │  └──────────────┴────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  select_model(context: ModelSelectionContext) → str     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Get tier from task/complexity                  │  │
│  │  2. Apply budget constraints                       │  │
│  │  3. Apply latency requirements                     │  │
│  │  4. Apply provider preferences                     │  │
│  │  5. Return model ID                                │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│ Validation    │ │ Critic       │ │ Orchestrator │
│ Orchestrator  │ │ Orchestrator │ │              │
└───────────────┘ └──────────────┘ └──────────────┘
```

### Why Centralize?

**1. Consistency Across System**
```python
# Before: Different orchestrators use different models for same task
validation_orch.validate(complexity="high")   → Opus
critic_orch.critique(complexity="high")       → Sonnet  # Inconsistent!

# After: Same task + complexity → same model
context = ModelSelectionContext(task_type=TaskType.ANALYSIS, complexity=TaskComplexity.HIGH)
model = selector.select_model(context)  → Opus (always)
```

**2. Easy Configuration**
```python
# Swap entire model tier (e.g., switch to OpenAI)
model_selector = ModelSelector(config={
    "model_tiers": {
        "premium": "gpt-4-turbo",  # Was claude-opus-4-20250514
        "standard": "gpt-4",
        "economy": "gpt-3.5-turbo"
    }
})
```

**3. Advanced Features**
```python
# Budget-aware selection
context = ModelSelectionContext(
    task_type=TaskType.SUMMARIZATION,
    complexity=TaskComplexity.HIGH,
    budget=0.001  # Tight budget
)
model = selector.select_model(context)  # Auto-downgrades to economy tier

# Latency-aware selection
context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.MEDIUM,
    latency_requirement_ms=500  # Need fast response
)
model = selector.select_model(context)  # Chooses faster model (Haiku)
```

---

## ModelSelector API Reference

### Class Definition

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskComplexity, TaskType

class ModelSelector:
    """
    Centralized model selection logic.

    Provides tier-based model selection with support for:
    - Task-complexity based selection
    - Budget constraints
    - Latency requirements
    - Provider preferences
    - Fallback chains
    - Cost estimation

    Example:
        selector = ModelSelector()
        context = ModelSelectionContext(
            task_type=TaskType.ANALYSIS,
            complexity=TaskComplexity.HIGH
        )
        model = selector.select_model(context)
    """
```

### Constructor

```python
def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize ModelSelector with optional custom configuration.

    Args:
        config: Optional configuration dictionary
            - model_tiers: Custom tier mappings (premium/standard/economy)
            - task_overrides: Task-specific model overrides
            - cost_multipliers: Pricing adjustments
            - provider_fallbacks: Fallback chain configuration

    Example:
        # Use default configuration
        selector = ModelSelector()

        # Custom configuration
        selector = ModelSelector(config={
            "model_tiers": {
                "premium": "gpt-4-turbo",
                "standard": "claude-sonnet-4-5-20250929",
                "economy": "claude-haiku-4-20250514"
            },
            "task_overrides": {
                "CRITIQUE": {
                    "HIGH": "premium"  # Always use premium for high-complexity critiques
                }
            }
        })
    """
```

### Core Method: select_model()

```python
def select_model(self, context: ModelSelectionContext) -> str:
    """
    Select optimal model based on context.

    Selection algorithm:
    1. Get base tier from task/complexity mapping
    2. Apply budget constraints (downgrade if needed)
    3. Apply latency requirements (prefer faster models if needed)
    4. Apply provider preferences (e.g., prefer Anthropic)
    5. Return final model ID

    Args:
        context: ModelSelectionContext with selection criteria

    Returns:
        Model identifier string (e.g., "claude-opus-4-20250514")

    Raises:
        ValueError: If invalid task type or complexity
        RuntimeError: If no suitable model found within constraints

    Example:
        context = ModelSelectionContext(
            task_type=TaskType.VALIDATION,
            complexity=TaskComplexity.HIGH,
            budget=0.005,
            quality_threshold=0.90
        )
        model = selector.select_model(context)  # Returns appropriate model
    """
```

### Supporting Methods

```python
def get_fallback_models(self, primary_model: str) -> List[str]:
    """
    Get quality-tiered fallback models for a primary model.

    Args:
        primary_model: Primary model identifier

    Returns:
        List of fallback models in priority order

    Example:
        fallbacks = selector.get_fallback_models("claude-opus-4-20250514")
        # Returns: ["claude-opus-4-20250514", "claude-sonnet-4-5-20250929", "gpt-4-turbo"]
    """

def estimate_cost(
    self,
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """
    Estimate cost for a model given token counts.

    Args:
        model: Model identifier
        input_tokens: Estimated input token count
        output_tokens: Estimated output token count

    Returns:
        Estimated cost in USD

    Example:
        cost = selector.estimate_cost(
            model="claude-opus-4-20250514",
            input_tokens=5000,
            output_tokens=1000
        )
        # Returns: ~0.09 (5000*$15/1M + 1000*$15/1M)
    """

def get_tier_for_model(self, model: str) -> str:
    """
    Get tier name for a given model.

    Args:
        model: Model identifier

    Returns:
        Tier name ("premium", "standard", or "economy")

    Raises:
        ValueError: If model not found in tier mappings

    Example:
        tier = selector.get_tier_for_model("claude-opus-4-20250514")
        # Returns: "premium"
    """

def get_models_in_tier(self, tier: str) -> List[str]:
    """
    Get all models in a given tier.

    Args:
        tier: Tier name ("premium", "standard", "economy")

    Returns:
        List of model identifiers in tier

    Example:
        models = selector.get_models_in_tier("standard")
        # Returns: ["claude-sonnet-4-5-20250929", "gpt-4"]
    """
```

### Configuration Classes

#### ModelSelectionContext

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelSelectionContext:
    """
    Context for model selection decisions.

    Attributes:
        task_type: Type of task (TaskType enum)
        complexity: Task complexity level (TaskComplexity enum)
        budget: Optional maximum cost per request (USD)
        quality_threshold: Minimum quality score (0.0-1.0)
        latency_requirement_ms: Maximum acceptable latency (milliseconds)
        provider_preference: Preferred provider ("anthropic", "openai", etc.)

    Example:
        context = ModelSelectionContext(
            task_type=TaskType.ANALYSIS,
            complexity=TaskComplexity.CRITICAL,
            budget=0.01,
            quality_threshold=0.95,
            latency_requirement_ms=2000,
            provider_preference="anthropic"
        )
    """
    task_type: TaskType
    complexity: TaskComplexity
    budget: Optional[float] = None
    quality_threshold: float = 0.85
    latency_requirement_ms: Optional[int] = None
    provider_preference: Optional[str] = None
```

#### TaskComplexity Enum

```python
from enum import Enum

class TaskComplexity(Enum):
    """
    Task complexity levels for model selection.

    LOW: Simple tasks (extraction, formatting, basic summarization)
    MEDIUM: Standard tasks (analysis, validation, code review)
    HIGH: Complex tasks (architecture review, security analysis)
    CRITICAL: Mission-critical tasks requiring highest quality
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

#### TaskType Enum

```python
class TaskType(Enum):
    """
    Task types for model selection.

    Different task types have different quality requirements:
    - CRITIQUE requires high quality even at low complexity
    - SUMMARIZATION can use economy tier more often
    - ANALYSIS requires premium tier for high complexity
    """
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    CRITIQUE = "critique"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    CODE_GENERATION = "code_generation"
    TRANSLATION = "translation"
    GENERAL = "general"
```

### Default Configuration

```python
# MODEL_TIERS - Tier to model mapping
MODEL_TIERS = {
    "premium": "claude-opus-4-20250514",       # $15/1M tokens
    "standard": "claude-sonnet-4-5-20250929",  # $3/1M tokens
    "economy": "claude-haiku-4-20250514",      # $0.25/1M tokens
}

# TASK_MODEL_MAP - Task/complexity to tier mapping
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
    TaskType.VALIDATION: {
        TaskComplexity.CRITICAL: "premium",
        TaskComplexity.HIGH: "standard",
        TaskComplexity.MEDIUM: "standard",
        TaskComplexity.LOW: "economy",
    },
    TaskType.SUMMARIZATION: {
        TaskComplexity.CRITICAL: "standard",
        TaskComplexity.HIGH: "standard",
        TaskComplexity.MEDIUM: "economy",
        TaskComplexity.LOW: "economy",
    },
    TaskType.EXTRACTION: {
        TaskComplexity.CRITICAL: "standard",
        TaskComplexity.HIGH: "economy",
        TaskComplexity.MEDIUM: "economy",
        TaskComplexity.LOW: "economy",
    },
    TaskType.CODE_GENERATION: {
        TaskComplexity.CRITICAL: "premium",
        TaskComplexity.HIGH: "standard",
        TaskComplexity.MEDIUM: "standard",
        TaskComplexity.LOW: "economy",
    },
}

# PROVIDER_FALLBACKS - Fallback chains by tier
PROVIDER_FALLBACKS = {
    "premium": [
        "claude-opus-4-20250514",
        "claude-opus-4-5",
        "gpt-4-turbo",
    ],
    "standard": [
        "claude-sonnet-4-5-20250929",
        "claude-sonnet-3-7-20250219",
        "gpt-4",
    ],
    "economy": [
        "claude-haiku-4-20250514",
        "claude-haiku-3-5-20250318",
        "gpt-3.5-turbo",
    ],
}
```

### Environment Variables

ModelSelector supports configuration via environment variables:

```bash
# Override default tiers
export MODEL_SELECTOR_PREMIUM="gpt-4-turbo"
export MODEL_SELECTOR_STANDARD="gpt-4"
export MODEL_SELECTOR_ECONOMY="gpt-3.5-turbo"

# Cost multipliers (for custom pricing)
export MODEL_SELECTOR_COST_MULTIPLIER_PREMIUM="1.2"  # 20% markup
export MODEL_SELECTOR_COST_MULTIPLIER_STANDARD="1.0"
export MODEL_SELECTOR_COST_MULTIPLIER_ECONOMY="0.8"  # 20% discount

# Default provider preference
export MODEL_SELECTOR_PROVIDER="anthropic"  # or "openai"

# Budget defaults
export MODEL_SELECTOR_DEFAULT_BUDGET="0.01"  # $0.01 per request
```

---

## Model Tiers Explained

### Tier Philosophy

**Tier-based abstraction decouples "quality level" from "specific model"**

Instead of hardcoding "claude-opus-4-20250514" everywhere, we use semantic tiers:
- **premium** = "Best quality, highest cost"
- **standard** = "Good quality, reasonable cost"
- **economy** = "Acceptable quality, lowest cost"

This allows swapping underlying models without changing code.

### Premium Tier

**Model:** `claude-opus-4-20250514` (default)
**Cost:** $15 per 1M tokens (input + output)
**Latency:** ~2-5 seconds (typical)
**Quality:** Highest (99th percentile)

**When to Use:**
- ✅ Critical tasks (security audits, architecture decisions)
- ✅ High-complexity analysis
- ✅ Tasks requiring deep reasoning
- ✅ Mission-critical validation

**When NOT to Use:**
- ❌ Simple extraction tasks
- ❌ Formatting or style checks
- ❌ Budget-constrained projects
- ❌ High-volume batch processing

**Example Use Cases:**
```python
# Security audit (critical)
context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.CRITICAL
)
model = selector.select_model(context)  # Returns premium (Opus)

# Architecture review (high complexity)
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
model = selector.select_model(context)  # Returns premium (Opus)
```

### Standard Tier

**Model:** `claude-sonnet-4-5-20250929` (default)
**Cost:** $3 per 1M tokens (80% cheaper than premium)
**Latency:** ~1-3 seconds (typical)
**Quality:** High (90th percentile)

**When to Use:**
- ✅ Most tasks (default choice)
- ✅ Medium-complexity analysis
- ✅ Code review and validation
- ✅ Standard critiques

**When NOT to Use:**
- ❌ Mission-critical security tasks
- ❌ Tasks requiring highest accuracy
- ❌ When budget allows premium tier

**Example Use Cases:**
```python
# Code validation (medium complexity)
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.MEDIUM
)
model = selector.select_model(context)  # Returns standard (Sonnet)

# General analysis
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.MEDIUM
)
model = selector.select_model(context)  # Returns standard (Sonnet)
```

### Economy Tier

**Model:** `claude-haiku-4-20250514` (default)
**Cost:** $0.25 per 1M tokens (98% cheaper than premium!)
**Latency:** ~0.5-2 seconds (fastest)
**Quality:** Good (70th percentile)

**When to Use:**
- ✅ Simple extraction tasks
- ✅ Formatting and style checks
- ✅ Low-complexity summarization
- ✅ High-volume batch processing
- ✅ Budget-constrained projects

**When NOT to Use:**
- ❌ Security-sensitive tasks
- ❌ Complex reasoning required
- ❌ High-stakes decisions

**Example Use Cases:**
```python
# Simple extraction (low complexity)
context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.LOW
)
model = selector.select_model(context)  # Returns economy (Haiku)

# Formatting check
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.LOW
)
model = selector.select_model(context)  # Returns economy (Haiku)
```

### Tier Selection Decision Matrix

| Task Type | Complexity | Default Tier | Reasoning |
|-----------|-----------|--------------|-----------|
| **ANALYSIS** | CRITICAL | premium | Highest accuracy needed |
| **ANALYSIS** | HIGH | premium | Complex reasoning required |
| **ANALYSIS** | MEDIUM | standard | Balance quality/cost |
| **ANALYSIS** | LOW | economy | Simple analysis, cost-effective |
| **CRITIQUE** | CRITICAL | premium | Security/architecture critical |
| **CRITIQUE** | HIGH | premium | Quality matters for critiques |
| **CRITIQUE** | MEDIUM | standard | Good quality acceptable |
| **CRITIQUE** | LOW | standard | Even simple critiques need quality |
| **VALIDATION** | CRITICAL | premium | Mission-critical validation |
| **VALIDATION** | HIGH | standard | Good quality sufficient |
| **VALIDATION** | MEDIUM | standard | Default validation quality |
| **VALIDATION** | LOW | economy | Simple checks, cost-effective |
| **SUMMARIZATION** | HIGH | standard | Accuracy important |
| **SUMMARIZATION** | MEDIUM | economy | Cost-effective for summaries |
| **SUMMARIZATION** | LOW | economy | Simple summaries, lowest cost |
| **EXTRACTION** | HIGH | economy | Extraction is straightforward |
| **EXTRACTION** | LOW | economy | Lowest cost for simple extraction |

### Cost Comparison Table

**Scenario:** 1,000 requests, 10,000 tokens each (5K input + 5K output)

| Tier | Model | Cost per Request | Total Cost | Savings vs Premium |
|------|-------|-----------------|------------|-------------------|
| **Premium** | Opus | $0.150 | $150.00 | Baseline |
| **Standard** | Sonnet | $0.030 | $30.00 | 80% ($120 saved) |
| **Economy** | Haiku | $0.0025 | $2.50 | 98% ($147.50 saved) |

**Key Insight:** Using economy tier where appropriate can save **98% on costs**.

---

## Task Types

### Overview

Task types help ModelSelector choose appropriate models based on task characteristics. Different tasks have different quality requirements.

### ANALYSIS

**Purpose:** Deep analysis, reasoning, problem-solving

**Characteristics:**
- Requires logical reasoning
- Often complex
- Quality matters

**Quality Requirements:** HIGH
**Recommended Tiers:** premium (high/critical), standard (medium), economy (low)

**Examples:**
```python
# Security vulnerability analysis (critical)
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.CRITICAL
)

# Performance bottleneck analysis (high)
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)

# Code pattern analysis (medium)
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.MEDIUM
)
```

### CRITIQUE

**Purpose:** Code review, quality assessment, finding issues

**Characteristics:**
- Requires critical thinking
- Quality important even for simple tasks
- False negatives are costly

**Quality Requirements:** HIGH (even for low complexity)
**Recommended Tiers:** premium (high/critical), standard (medium/low)

**Note:** Critiques default to standard tier even at low complexity because missing issues is worse than extra cost.

**Examples:**
```python
# Security code review (critical)
context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.CRITICAL
)

# Architecture review (high)
context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.HIGH
)

# Style review (low, but still uses standard tier)
context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.LOW
)
```

### VALIDATION

**Purpose:** Checking correctness, conformance to rules

**Characteristics:**
- Rule-based checking
- Clear pass/fail criteria
- Medium quality requirements

**Quality Requirements:** MEDIUM
**Recommended Tiers:** premium (critical), standard (high/medium), economy (low)

**Examples:**
```python
# Mission-critical validation (e.g., deployment checks)
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.CRITICAL
)

# Standard code validation
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.MEDIUM
)

# Simple format validation
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.LOW
)
```

### SUMMARIZATION

**Purpose:** Creating summaries, condensing information

**Characteristics:**
- Straightforward task
- Economy tier often sufficient
- Can use lower quality models

**Quality Requirements:** MEDIUM-LOW
**Recommended Tiers:** standard (high), economy (medium/low)

**Examples:**
```python
# Executive summary (high quality needed)
context = ModelSelectionContext(
    task_type=TaskType.SUMMARIZATION,
    complexity=TaskComplexity.HIGH
)

# Standard summary
context = ModelSelectionContext(
    task_type=TaskType.SUMMARIZATION,
    complexity=TaskComplexity.MEDIUM
)

# Quick summary
context = ModelSelectionContext(
    task_type=TaskType.SUMMARIZATION,
    complexity=TaskComplexity.LOW
)
```

### EXTRACTION

**Purpose:** Extracting structured data, parsing content

**Characteristics:**
- Pattern-based task
- Well-defined output format
- Economy tier usually sufficient

**Quality Requirements:** LOW-MEDIUM
**Recommended Tiers:** economy (low/medium), standard (high)

**Examples:**
```python
# Complex data extraction
context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.HIGH
)

# Standard extraction
context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.MEDIUM
)

# Simple field extraction
context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.LOW
)
```

### CODE_GENERATION

**Purpose:** Generating code, templates, boilerplate

**Characteristics:**
- Requires understanding context
- Quality important for complex generation
- Syntax correctness critical

**Quality Requirements:** MEDIUM-HIGH
**Recommended Tiers:** premium (critical), standard (high/medium), economy (low)

**Examples:**
```python
# Complex algorithm generation (critical)
context = ModelSelectionContext(
    task_type=TaskType.CODE_GENERATION,
    complexity=TaskComplexity.CRITICAL
)

# Function implementation (high)
context = ModelSelectionContext(
    task_type=TaskType.CODE_GENERATION,
    complexity=TaskComplexity.HIGH
)

# Boilerplate generation (low)
context = ModelSelectionContext(
    task_type=TaskType.CODE_GENERATION,
    complexity=TaskComplexity.LOW
)
```

### GENERAL

**Purpose:** Catch-all for unspecified tasks

**Characteristics:**
- Use when task type doesn't fit other categories
- Defaults to conservative tier selection

**Quality Requirements:** MEDIUM
**Recommended Tiers:** Based on complexity (standard is common default)

**Examples:**
```python
# General task with high complexity
context = ModelSelectionContext(
    task_type=TaskType.GENERAL,
    complexity=TaskComplexity.HIGH
)
```

---

## Usage Patterns

### Pattern 1: Basic Tier Selection

**Goal:** Select model based on task type and complexity only

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

# Create selector (uses default configuration)
selector = ModelSelector()

# Create context
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)

# Select model
model = selector.select_model(context)

print(f"Selected model: {model}")
# Output: Selected model: claude-opus-4-20250514 (premium tier)
```

**When to Use:** Simple scenarios with default configuration

### Pattern 2: Task-Type Aware Selection

**Goal:** Select appropriate model for different task types

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Security critique (premium tier)
security_context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.CRITICAL
)
security_model = selector.select_model(security_context)
# Returns: claude-opus-4-20250514

# Code summarization (economy tier)
summary_context = ModelSelectionContext(
    task_type=TaskType.SUMMARIZATION,
    complexity=TaskComplexity.LOW
)
summary_model = selector.select_model(summary_context)
# Returns: claude-haiku-4-20250514

# Data extraction (economy tier)
extraction_context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.MEDIUM
)
extraction_model = selector.select_model(extraction_context)
# Returns: claude-haiku-4-20250514
```

**When to Use:** When optimizing costs by task type

### Pattern 3: Environment Variable Configuration

**Goal:** Configure ModelSelector via environment variables

```bash
# .env file
MODEL_SELECTOR_PREMIUM="gpt-4-turbo"
MODEL_SELECTOR_STANDARD="gpt-4"
MODEL_SELECTOR_ECONOMY="gpt-3.5-turbo"
MODEL_SELECTOR_PROVIDER="openai"
```

```python
import os
from dotenv import load_dotenv
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

# Load environment variables
load_dotenv()

# Create selector (reads from environment)
selector = ModelSelector()

# Will use OpenAI models from environment
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
model = selector.select_model(context)
# Returns: gpt-4-turbo (from environment variable)
```

**When to Use:** Production deployments, different environments (dev/staging/prod)

### Pattern 4: Runtime Configuration Override

**Goal:** Customize model tiers at runtime

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

# Custom configuration
custom_config = {
    "model_tiers": {
        "premium": "gpt-4-turbo",
        "standard": "claude-sonnet-4-5-20250929",
        "economy": "claude-haiku-4-20250514"
    },
    "task_overrides": {
        "CRITIQUE": {
            "HIGH": "premium",  # Always use premium for high-complexity critiques
            "MEDIUM": "premium",  # Upgrade medium to premium for critiques
        }
    }
}

selector = ModelSelector(config=custom_config)

# Will use custom configuration
context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.MEDIUM
)
model = selector.select_model(context)
# Returns: gpt-4-turbo (custom premium tier + task override)
```

**When to Use:** A/B testing, temporary configuration changes, special projects

### Pattern 5: Provider Failover

**Goal:** Handle provider failures with fallback models

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Get primary model
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
primary_model = selector.select_model(context)
# Returns: claude-opus-4-20250514

# Get fallback chain
fallbacks = selector.get_fallback_models(primary_model)
# Returns: ["claude-opus-4-20250514", "claude-opus-4-5", "gpt-4-turbo"]

# Try primary, then fallbacks
for model in fallbacks:
    try:
        result = agent.execute(model=model, prompt=prompt)
        break
    except ProviderError as e:
        print(f"Model {model} failed, trying next...")
        continue
```

**When to Use:** High-reliability systems, production environments

### Pattern 6: Budget-Aware Selection

**Goal:** Stay within budget by downgrading tier if needed

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Normally would use premium tier (high complexity)
# But budget constraint forces downgrade
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH,
    budget=0.005  # Very tight budget ($0.005 per request)
)

model = selector.select_model(context)
# Returns: claude-haiku-4-20250514 (economy tier, within budget)

# Estimate cost to verify
estimated_cost = selector.estimate_cost(
    model=model,
    input_tokens=5000,
    output_tokens=1000
)
print(f"Estimated cost: ${estimated_cost:.4f}")
# Output: Estimated cost: $0.0015 (well under $0.005 budget)
```

**When to Use:** Cost-sensitive applications, budget-constrained projects

### Pattern 7: Latency-Aware Selection

**Goal:** Select faster models when latency matters

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Normally would use standard tier (medium complexity)
# But latency requirement prefers faster model
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.MEDIUM,
    latency_requirement_ms=500  # Need response in <500ms
)

model = selector.select_model(context)
# Returns: claude-haiku-4-20250514 (economy tier, faster)
```

**When to Use:** Real-time applications, interactive systems, user-facing features

### Pattern 8: Quality-Threshold Selection

**Goal:** Ensure minimum quality score

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Quality threshold prevents economy tier
context = ModelSelectionContext(
    task_type=TaskType.SUMMARIZATION,
    complexity=TaskComplexity.LOW,
    quality_threshold=0.92  # Need high quality
)

model = selector.select_model(context)
# Returns: claude-sonnet-4-5-20250929 (standard tier, meets quality threshold)
# (Economy tier would typically be used for low complexity summarization)
```

**When to Use:** Quality-critical applications

### Pattern 9: Integration with ValidationOrchestrator

**Before (Hardcoded):**
```python
# validation_orchestrator.py (old code)
def _select_validator_model(self, complexity: str) -> str:
    """Hardcoded model selection (deprecated)."""
    if complexity == "high":
        return "claude-opus-4-20250514"
    elif complexity == "medium":
        return "claude-sonnet-3-7-20250219"
    else:
        return "claude-haiku-3-5-20250318"

# Usage
model = self._select_validator_model("high")
```

**After (ModelSelector):**
```python
# validation_orchestrator.py (new code)
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

class ValidationOrchestrator:
    def __init__(self):
        self.model_selector = ModelSelector()

    def validate(self, code: str, complexity: str = "medium"):
        # Convert string to enum
        complexity_level = TaskComplexity(complexity)

        # Use ModelSelector
        context = ModelSelectionContext(
            task_type=TaskType.VALIDATION,
            complexity=complexity_level
        )
        model = self.model_selector.select_model(context)

        # Execute validation with selected model
        return self._execute_validation(code, model)
```

**Benefits:**
- No duplicated selection logic
- Easy to change tier mappings
- Budget constraints available
- Consistent with other orchestrators

### Pattern 10: Integration with CriticOrchestrator

**Before (Hardcoded):**
```python
# critic_orchestrator.py (old code)
def _select_critic_model(self, critique_type: str) -> str:
    """Hardcoded model selection (deprecated)."""
    if critique_type in ["security", "architecture"]:
        return "claude-opus-4-20250514"
    elif critique_type == "code_quality":
        return "claude-sonnet-3-7-20250219"
    else:
        return "claude-haiku-3-5-20250318"
```

**After (ModelSelector):**
```python
# critic_orchestrator.py (new code)
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

class CriticOrchestrator:
    def __init__(self):
        self.model_selector = ModelSelector()

    def critique(self, code: str, critique_type: str):
        # Map critique type to complexity
        complexity_map = {
            "security": TaskComplexity.CRITICAL,
            "architecture": TaskComplexity.CRITICAL,
            "code_quality": TaskComplexity.HIGH,
            "style": TaskComplexity.LOW,
        }
        complexity = complexity_map.get(critique_type, TaskComplexity.MEDIUM)

        # Use ModelSelector
        context = ModelSelectionContext(
            task_type=TaskType.CRITIQUE,
            complexity=complexity
        )
        model = self.model_selector.select_model(context)

        # Execute critique with selected model
        return self._execute_critique(code, model, critique_type)
```

**Benefits:**
- Consistent complexity mapping
- Easy to add new critique types
- Centralized tier management

---

## Provider Failover

### Overview

Provider failover ensures high availability by automatically using fallback models when primary models fail.

### Fallback Strategy

**ModelSelector provides quality-tiered fallback chains:**

```python
PROVIDER_FALLBACKS = {
    "premium": [
        "claude-opus-4-20250514",      # Primary (Anthropic)
        "claude-opus-4-5",              # Fallback 1 (Anthropic, older version)
        "gpt-4-turbo",                  # Fallback 2 (OpenAI, similar quality)
    ],
    "standard": [
        "claude-sonnet-4-5-20250929",  # Primary (Anthropic)
        "claude-sonnet-3-7-20250219",  # Fallback 1 (Anthropic, older version)
        "gpt-4",                        # Fallback 2 (OpenAI, similar quality)
    ],
    "economy": [
        "claude-haiku-4-20250514",     # Primary (Anthropic)
        "claude-haiku-3-5-20250318",   # Fallback 1 (Anthropic, older version)
        "gpt-3.5-turbo",                # Fallback 2 (OpenAI, cheaper)
    ],
}
```

### Fallback Chain Configuration

**Custom fallback chains:**

```python
custom_config = {
    "provider_fallbacks": {
        "premium": [
            "claude-opus-4-20250514",
            "gpt-4-turbo",
            "claude-sonnet-4-5-20250929",  # Downgrade to standard as last resort
        ],
        "standard": [
            "claude-sonnet-4-5-20250929",
            "gpt-4",
            "claude-haiku-4-20250514",  # Downgrade to economy as last resort
        ],
    }
}

selector = ModelSelector(config=custom_config)
```

### Using Fallback Chains

**Pattern: Try primary, fall back on failure**

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Get primary model and fallbacks
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
primary_model = selector.select_model(context)
fallbacks = selector.get_fallback_models(primary_model)

print(f"Primary: {primary_model}")
print(f"Fallbacks: {fallbacks}")
# Output:
# Primary: claude-opus-4-20250514
# Fallbacks: ['claude-opus-4-20250514', 'claude-opus-4-5', 'gpt-4-turbo']

# Try each model in chain
for model in fallbacks:
    try:
        result = agent.execute(model=model, prompt=prompt)
        print(f"Success with {model}")
        break
    except ProviderError as e:
        print(f"{model} failed: {e}, trying next...")
        continue
    except Exception as e:
        print(f"Fatal error: {e}")
        raise
```

### Cost Implications

**Fallback to different provider may change costs:**

| Primary Model | Fallback Model | Cost Change |
|---------------|----------------|-------------|
| claude-opus-4-20250514 ($15/1M) | gpt-4-turbo ($10/1M) | -33% |
| claude-sonnet-4-5-20250929 ($3/1M) | gpt-4 ($30/1M) | +900% |
| claude-haiku-4-20250514 ($0.25/1M) | gpt-3.5-turbo ($0.50/1M) | +100% |

**Important:** Monitor costs when using fallbacks across providers.

### Error Handling

**Handle different failure modes:**

```python
from utils.model_selector import ModelSelector
from anthropic import RateLimitError, APIError

selector = ModelSelector()
fallbacks = selector.get_fallback_models("claude-opus-4-20250514")

for model in fallbacks:
    try:
        result = agent.execute(model=model, prompt=prompt)
        break
    except RateLimitError:
        # Rate limit: Try fallback immediately
        print(f"{model} rate limited, trying fallback")
        continue
    except APIError as e:
        if "overloaded" in str(e):
            # Server overloaded: Try fallback
            print(f"{model} overloaded, trying fallback")
            continue
        else:
            # Other API error: Abort
            raise
    except Exception as e:
        # Fatal error: Abort
        raise
```

---

## Cost Optimization

### Understanding Costs

**Token Pricing (as of model release dates):**

| Model | Input Cost | Output Cost | Total (1K tokens) |
|-------|-----------|-------------|-------------------|
| **claude-opus-4-20250514** | $15/1M | $15/1M | $0.015 |
| **claude-sonnet-4-5-20250929** | $3/1M | $3/1M | $0.003 |
| **claude-haiku-4-20250514** | $0.25/1M | $0.25/1M | $0.00025 |
| **gpt-4-turbo** | $10/1M | $30/1M | $0.010 (input) |
| **gpt-4** | $30/1M | $60/1M | $0.030 (input) |

### Cost Estimation

**Use `estimate_cost()` before execution:**

```python
from utils.model_selector import ModelSelector

selector = ModelSelector()

# Estimate cost for different models
models = [
    "claude-opus-4-20250514",
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-20250514",
]

for model in models:
    cost = selector.estimate_cost(
        model=model,
        input_tokens=5000,
        output_tokens=1000
    )
    print(f"{model}: ${cost:.4f}")

# Output:
# claude-opus-4-20250514: $0.0900
# claude-sonnet-4-5-20250929: $0.0180
# claude-haiku-4-20250514: $0.0015
```

### Budget-Aware Selection

**Automatically downgrade to stay within budget:**

```python
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

selector = ModelSelector()

# Would normally use premium tier (high complexity)
# But budget forces downgrade
contexts = [
    ModelSelectionContext(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.HIGH,
        budget=0.01  # $0.01 per request
    ),
    ModelSelectionContext(
        task_type=TaskType.ANALYSIS,
        complexity=TaskComplexity.HIGH,
        budget=0.001  # $0.001 per request (very tight)
    ),
]

for context in contexts:
    model = selector.select_model(context)
    cost = selector.estimate_cost(model, 5000, 1000)
    print(f"Budget: ${context.budget}, Selected: {model}, Cost: ${cost:.4f}")

# Output:
# Budget: $0.01, Selected: claude-sonnet-4-5-20250929, Cost: $0.0180
# Budget: $0.001, Selected: claude-haiku-4-20250514, Cost: $0.0015
```

### Cost Optimization Strategies

**Strategy 1: Use Economy Tier for Low-Complexity Tasks**

```python
# DON'T: Use premium for everything
bad_context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,  # Simple task
    complexity=TaskComplexity.LOW,
)
# Would select premium if hardcoded → $0.015 per 1K tokens

# DO: Let ModelSelector choose economy tier
good_context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.LOW,
)
model = selector.select_model(good_context)
# Selects economy → $0.00025 per 1K tokens (98% savings!)
```

**Strategy 2: Batch Low-Priority Tasks**

```python
# Batch summarization tasks to economy tier
summaries = []
for doc in documents:
    context = ModelSelectionContext(
        task_type=TaskType.SUMMARIZATION,
        complexity=TaskComplexity.LOW,
        budget=0.001  # Tight budget per summary
    )
    model = selector.select_model(context)
    summary = agent.execute(model=model, prompt=doc)
    summaries.append(summary)

# Cost: ~$0.0015 per summary (economy tier)
# vs. ~$0.090 with premium tier (98% savings)
```

**Strategy 3: Progressive Quality**

```python
# Start with economy tier, upgrade if quality insufficient
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.MEDIUM,
)

# Try economy first
economy_model = selector.get_models_in_tier("economy")[0]
result = agent.execute(model=economy_model, prompt=prompt)

if result.quality_score < 0.85:
    # Quality insufficient, try standard tier
    standard_model = selector.get_models_in_tier("standard")[0]
    result = agent.execute(model=standard_model, prompt=prompt)

# Only use premium if standard still insufficient
if result.quality_score < 0.90:
    premium_model = selector.get_models_in_tier("premium")[0]
    result = agent.execute(model=premium_model, prompt=prompt)
```

### Real-World Cost Savings Examples

**Example 1: Code Validation System**

**Before ModelSelector:**
```python
# Hardcoded to Opus for all validation
model = "claude-opus-4-20250514"
# 10,000 validations/day × $0.015/validation = $150/day
# Monthly cost: $4,500
```

**After ModelSelector:**
```python
# Task-aware selection
# - 30% high-complexity → premium ($0.015 each)
# - 50% medium-complexity → standard ($0.003 each)
# - 20% low-complexity → economy ($0.00025 each)

# Cost breakdown:
# 3,000 × $0.015 = $45.00
# 5,000 × $0.003 = $15.00
# 2,000 × $0.00025 = $0.50
# Total: $60.50/day
# Monthly cost: $1,815

# Savings: $2,685/month (60% reduction)
```

**Example 2: Document Processing Pipeline**

**Before ModelSelector:**
```python
# Used Sonnet for all tasks
# - 5,000 extractions/day × $0.003 = $15.00
# - 5,000 summaries/day × $0.003 = $15.00
# - 1,000 analyses/day × $0.003 = $3.00
# Total: $33/day
# Monthly cost: $990
```

**After ModelSelector:**
```python
# Task-aware selection
# - Extractions → economy ($0.00025 each)
# - Summaries → economy ($0.00025 each)
# - Analyses → standard ($0.003 each)

# Cost breakdown:
# 5,000 × $0.00025 = $1.25
# 5,000 × $0.00025 = $1.25
# 1,000 × $0.003 = $3.00
# Total: $5.50/day
# Monthly cost: $165

# Savings: $825/month (83% reduction)
```

---

## Best Practices

### When to Use Each Tier

#### Use Premium Tier (Opus) When:

✅ **Security is Critical**
```python
# Security audit
context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.CRITICAL
)
```

✅ **Architecture Decisions**
```python
# Architecture review
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH
)
```

✅ **Complex Reasoning Required**
```python
# Algorithm optimization
context = ModelSelectionContext(
    task_type=TaskType.CODE_GENERATION,
    complexity=TaskComplexity.CRITICAL
)
```

✅ **Mission-Critical Validation**
```python
# Pre-deployment validation
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.CRITICAL
)
```

❌ **Don't Use Premium For:**
- Simple extraction tasks
- Formatting checks
- Low-stakes summarization
- High-volume batch processing

#### Use Standard Tier (Sonnet) When:

✅ **Default Choice for Most Tasks**
```python
# General code review
context = ModelSelectionContext(
    task_type=TaskType.CRITIQUE,
    complexity=TaskComplexity.MEDIUM
)
```

✅ **Balance Quality and Cost**
```python
# Standard validation
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.MEDIUM
)
```

✅ **Medium Complexity Analysis**
```python
# Code analysis
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.MEDIUM
)
```

❌ **Don't Use Standard For:**
- Mission-critical security tasks (use premium)
- Simple extraction (use economy)
- When budget allows premium for high-stakes tasks

#### Use Economy Tier (Haiku) When:

✅ **Simple Extraction**
```python
# Extract structured data
context = ModelSelectionContext(
    task_type=TaskType.EXTRACTION,
    complexity=TaskComplexity.LOW
)
```

✅ **Formatting Checks**
```python
# Check code formatting
context = ModelSelectionContext(
    task_type=TaskType.VALIDATION,
    complexity=TaskComplexity.LOW
)
```

✅ **High-Volume Processing**
```python
# Process 100,000 documents
for doc in documents:
    context = ModelSelectionContext(
        task_type=TaskType.SUMMARIZATION,
        complexity=TaskComplexity.LOW
    )
```

✅ **Budget-Constrained Projects**
```python
# Startup with tight budget
context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.MEDIUM,
    budget=0.001  # Very tight budget
)
```

❌ **Don't Use Economy For:**
- Security-sensitive tasks
- Complex reasoning
- High-stakes decisions
- Tasks requiring highest accuracy

### Configuration Management

**Best Practice 1: Use Environment Variables for Production**

```bash
# .env.production
MODEL_SELECTOR_PREMIUM="claude-opus-4-20250514"
MODEL_SELECTOR_STANDARD="claude-sonnet-4-5-20250929"
MODEL_SELECTOR_ECONOMY="claude-haiku-4-20250514"
MODEL_SELECTOR_PROVIDER="anthropic"
MODEL_SELECTOR_DEFAULT_BUDGET="0.01"
```

**Best Practice 2: Use Configuration Files for Staging**

```yaml
# config/staging.yaml
model_selector:
  model_tiers:
    premium: claude-sonnet-4-5-20250929  # Use Sonnet instead of Opus in staging
    standard: claude-sonnet-3-7-20250219
    economy: claude-haiku-4-20250514
  task_overrides:
    CRITIQUE:
      HIGH: standard  # Downgrade critiques in staging
```

**Best Practice 3: Document Custom Configuration**

```python
# config.py
"""
Model selector configuration for this project.

Custom overrides:
- CRITIQUE tasks always use premium tier (security-critical)
- SUMMARIZATION uses economy tier (cost-sensitive)
"""

CUSTOM_CONFIG = {
    "task_overrides": {
        "CRITIQUE": {
            "HIGH": "premium",
            "MEDIUM": "premium",  # Upgrade to premium
        },
        "SUMMARIZATION": {
            "HIGH": "economy",  # Downgrade to economy
        },
    }
}
```

### Testing with Different Tiers

**Best Practice: Test with Same Tier as Production**

```python
# test_validation.py
import pytest
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity

@pytest.fixture
def production_selector():
    """Use same config as production."""
    # Load production config
    return ModelSelector(config=load_production_config())

def test_validation_uses_correct_tier(production_selector):
    """Ensure validation uses expected tier in production."""
    context = ModelSelectionContext(
        task_type=TaskType.VALIDATION,
        complexity=TaskComplexity.HIGH
    )
    model = production_selector.select_model(context)

    # Assert using standard tier (not premium or economy)
    tier = production_selector.get_tier_for_model(model)
    assert tier == "standard"
```

**Best Practice: Mock ModelSelector in Unit Tests**

```python
# test_orchestrator.py
from unittest.mock import Mock, patch

@patch('validation.critic_integration.ModelSelector')
def test_validation_logic(mock_selector_class):
    """Test validation logic without real model selection."""
    # Mock returns fixed model
    mock_selector = Mock()
    mock_selector.select_model.return_value = "test-model"
    mock_selector_class.return_value = mock_selector

    # Test validation logic
    orchestrator = ValidationOrchestrator()
    result = orchestrator.validate(code)

    # Verify mock called correctly
    mock_selector.select_model.assert_called_once()
```

### Production Deployment Considerations

**Best Practice 1: Monitor Tier Distribution**

```python
from utils.model_selector import ModelSelector
import logging

logger = logging.getLogger(__name__)

class MonitoredModelSelector(ModelSelector):
    """ModelSelector with tier usage logging."""

    def select_model(self, context):
        model = super().select_model(context)
        tier = self.get_tier_for_model(model)

        # Log tier selection
        logger.info(
            "Model selected",
            extra={
                "tier": tier,
                "model": model,
                "task_type": context.task_type.value,
                "complexity": context.complexity.value,
            }
        )

        return model
```

**Best Practice 2: Set Budget Alerts**

```python
from utils.model_selector import ModelSelector

class BudgetAwareSelector(ModelSelector):
    """ModelSelector with budget tracking."""

    def __init__(self, config=None, daily_budget=100.0):
        super().__init__(config)
        self.daily_budget = daily_budget
        self.daily_spend = 0.0

    def select_model(self, context):
        # Check budget before selection
        if self.daily_spend >= self.daily_budget:
            logger.warning(f"Daily budget exceeded: ${self.daily_spend:.2f}")
            # Force economy tier
            context.budget = 0.001

        model = super().select_model(context)

        # Track estimated cost
        estimated_cost = self.estimate_cost(model, 5000, 1000)
        self.daily_spend += estimated_cost

        return model
```

**Best Practice 3: Gradual Rollout**

```python
# Use feature flags for gradual rollout
from utils.model_selector import ModelSelector

def get_model_selector(user_id: str) -> ModelSelector:
    """Get ModelSelector with feature flag support."""

    if feature_flag_enabled("model_selector_rollout", user_id):
        # New ModelSelector for rolled-out users
        return ModelSelector()
    else:
        # Legacy hardcoded selection
        return LegacyModelSelector()
```

### Monitoring and Logging

**Best Practice: Log Selection Decisions**

```python
from utils.model_selector import ModelSelector
import logging

logger = logging.getLogger(__name__)

selector = ModelSelector()

context = ModelSelectionContext(
    task_type=TaskType.ANALYSIS,
    complexity=TaskComplexity.HIGH,
    budget=0.01
)

model = selector.select_model(context)

logger.info(
    "Model selected for analysis",
    extra={
        "model": model,
        "tier": selector.get_tier_for_model(model),
        "task_type": context.task_type.value,
        "complexity": context.complexity.value,
        "budget": context.budget,
    }
)
```

---

## Troubleshooting

### Common Issue 1: Model Not Found

**Symptom:**
```python
ValueError: Model 'gpt-4-turbo' not found in tier mappings
```

**Cause:** Model not registered in `MODEL_TIERS`

**Solution:**
```python
# Add model to configuration
custom_config = {
    "model_tiers": {
        "premium": "gpt-4-turbo",  # Add missing model
        "standard": "claude-sonnet-4-5-20250929",
        "economy": "claude-haiku-4-20250514",
    }
}

selector = ModelSelector(config=custom_config)
```

### Common Issue 2: Tier Configuration Ignored

**Symptom:** ModelSelector uses default tiers instead of custom configuration

**Cause:** Configuration not passed correctly

**Solution:**
```python
# DON'T: Create without config
selector = ModelSelector()
# Uses default tiers

# DO: Pass config to constructor
custom_config = {"model_tiers": {...}}
selector = ModelSelector(config=custom_config)
# Uses custom tiers
```

### Common Issue 3: Fallback Not Working

**Symptom:** No fallback when primary model fails

**Cause:** Not using `get_fallback_models()`

**Solution:**
```python
# DON'T: Only try primary model
model = selector.select_model(context)
result = agent.execute(model=model, prompt=prompt)  # Fails if model unavailable

# DO: Use fallback chain
model = selector.select_model(context)
fallbacks = selector.get_fallback_models(model)

for fallback_model in fallbacks:
    try:
        result = agent.execute(model=fallback_model, prompt=prompt)
        break
    except ProviderError:
        continue
```

### Common Issue 4: Cost Tracking Incorrect

**Symptom:** `estimate_cost()` returns unexpected values

**Cause:** Token count estimation inaccurate

**Solution:**
```python
# DON'T: Guess token counts
cost = selector.estimate_cost(model, 1000, 500)  # Rough guess

# DO: Use accurate token counts
from anthropic import Anthropic
client = Anthropic()

# Count actual tokens
input_tokens = client.count_tokens(prompt)
# Estimate output based on similar tasks
output_tokens = input_tokens * 0.2  # 20% of input (example)

cost = selector.estimate_cost(model, input_tokens, output_tokens)
```

### Common Issue 5: Environment Variables Not Loaded

**Symptom:** ModelSelector uses default config despite setting environment variables

**Cause:** Environment variables not loaded before ModelSelector creation

**Solution:**
```python
# DON'T: Create ModelSelector before loading env
selector = ModelSelector()  # Reads env variables
os.environ["MODEL_SELECTOR_PREMIUM"] = "gpt-4-turbo"  # Too late!

# DO: Load env before creating ModelSelector
from dotenv import load_dotenv
load_dotenv()  # Load .env file

# Now create ModelSelector
selector = ModelSelector()  # Reads env variables correctly
```

### Common Issue 6: Integration with Existing Code

**Symptom:** Existing code breaks when integrating ModelSelector

**Cause:** Incompatible model string format

**Solution:**
```python
# Old code expects simple string
def old_function(model: str):
    assert model in ["opus", "sonnet", "haiku"]
    # ...

# DON'T: Pass full model ID
model = selector.select_model(context)
old_function(model)  # Fails: "claude-opus-4-20250514" not in list

# DO: Map tier to old format
tier = selector.get_tier_for_model(model)
tier_to_old_format = {
    "premium": "opus",
    "standard": "sonnet",
    "economy": "haiku",
}
old_function(tier_to_old_format[tier])  # Works!
```

---

## Migration from Hardcoded Models

### Step-by-Step Migration Guide

#### Step 1: Identify Hardcoded Model Selection

**Find all hardcoded model selection logic:**

```bash
# Search for hardcoded model IDs
grep -r "claude-opus-4-20250514" . --include="*.py"
grep -r "claude-sonnet" . --include="*.py"
grep -r "_select.*model" . --include="*.py"
```

**Common patterns to migrate:**
- `_select_validator_model()`
- `_select_critic_model()`
- `_select_subagent_model()`
- Hardcoded `model="claude-opus-4-20250514"`

#### Step 2: Install ModelSelector

**Import ModelSelector in your module:**

```python
# Before
# No ModelSelector import

# After
from utils.model_selector import ModelSelector, ModelSelectionContext
from utils.model_selector import TaskType, TaskComplexity
```

#### Step 3: Replace Hardcoded Selection

**Example: ValidationOrchestrator**

**Before:**
```python
class ValidationOrchestrator:
    def _select_validator_model(self, complexity: str) -> str:
        """Hardcoded selection logic."""
        if complexity == "high":
            return "claude-opus-4-20250514"
        elif complexity == "medium":
            return "claude-sonnet-3-7-20250219"
        else:
            return "claude-haiku-3-5-20250318"

    def validate(self, code: str, complexity: str = "medium"):
        model = self._select_validator_model(complexity)
        return self._execute_validation(code, model)
```

**After:**
```python
class ValidationOrchestrator:
    def __init__(self):
        self.model_selector = ModelSelector()

    def validate(self, code: str, complexity: str = "medium"):
        # Map string to enum
        complexity_enum = TaskComplexity(complexity)

        # Use ModelSelector
        context = ModelSelectionContext(
            task_type=TaskType.VALIDATION,
            complexity=complexity_enum
        )
        model = self.model_selector.select_model(context)

        return self._execute_validation(code, model)
```

**Changes:**
1. Added `model_selector` instance variable
2. Removed `_select_validator_model()` method
3. Created `ModelSelectionContext` in `validate()`
4. Used `model_selector.select_model()`

#### Step 4: Test Migration

**Create migration tests:**

```python
# test_validation_migration.py
import pytest
from validation import ValidationOrchestrator
from utils.model_selector import TaskComplexity

def test_validation_uses_model_selector():
    """Verify ValidationOrchestrator uses ModelSelector."""
    orch = ValidationOrchestrator()

    # Ensure model_selector exists
    assert hasattr(orch, 'model_selector')
    assert orch.model_selector is not None

def test_model_selection_consistent():
    """Ensure model selection is consistent."""
    orch = ValidationOrchestrator()

    # High complexity should use premium tier
    model1 = orch.model_selector.select_model(
        ModelSelectionContext(
            task_type=TaskType.VALIDATION,
            complexity=TaskComplexity.HIGH
        )
    )
    tier1 = orch.model_selector.get_tier_for_model(model1)

    # Should be standard or premium (ValidationOrchestrator uses standard for high)
    assert tier1 in ["standard", "premium"]
```

#### Step 5: Remove Deprecated Code

**After confirming migration works:**

```python
# Remove old method
class ValidationOrchestrator:
    # REMOVED: _select_validator_model() - use ModelSelector instead

    def __init__(self):
        self.model_selector = ModelSelector()

    # ... rest of class
```

### Migration Checklist

**Before starting migration:**
- [ ] Read ModelSelector API reference
- [ ] Understand task types and tiers
- [ ] Identify all hardcoded model selection
- [ ] Plan testing strategy

**During migration:**
- [ ] Import ModelSelector and supporting types
- [ ] Create ModelSelector instance
- [ ] Replace hardcoded selection with `select_model()`
- [ ] Map existing complexity strings to enums
- [ ] Update tests

**After migration:**
- [ ] All tests passing
- [ ] No hardcoded model IDs remaining
- [ ] Remove deprecated selection methods
- [ ] Update documentation

### Rollback Procedure

**If migration causes issues, rollback:**

```bash
# Rollback to pre-migration commit
git checkout <pre-migration-commit-hash>

# Or revert specific file
git checkout <commit-hash> -- path/to/orchestrator.py

# Run tests to verify
pytest tests/
```

---

## References

### Related Documentation

- **ADR-003:** `/home/jevenson/.claude/lib/docs/adr/ADR-003-centralize-model-selection.md`
  - Architectural decision record for ModelSelector
  - Rationale and alternatives considered

- **Phase 2 Execution Plan:** `/home/jevenson/.claude/lib/PHASE_2_EXECUTION_PLAN.md`
  - Overall Phase 2 consolidation plan
  - ModelSelector is Phase 2D

- **Migration Guide:** `/home/jevenson/.claude/lib/docs/MIGRATION_GUIDE_PHASE_2D.md`
  - Detailed migration instructions
  - Before/after examples

### API Reference

**Main Module:**
- `/home/jevenson/.claude/lib/utils/model_selector.py`

**Supporting Modules:**
- `/home/jevenson/.claude/lib/utils/__init__.py`

### Testing Documentation

**Test Files:**
- `/home/jevenson/.claude/lib/tests/test_model_selector.py`
- `/home/jevenson/.claude/lib/tests/test_model_selector_integration.py`

### External Resources

**Anthropic Documentation:**
- Model pricing: https://www.anthropic.com/pricing
- Model specifications: https://docs.anthropic.com/claude/reference/models

**OpenAI Documentation:**
- Model pricing: https://openai.com/pricing
- Model specifications: https://platform.openai.com/docs/models

---

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Active (Phase 2D)
**Total Lines:** 1,453

---

**End of Model Selector Guide**
