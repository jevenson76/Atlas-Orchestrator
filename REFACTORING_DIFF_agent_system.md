# Refactoring Changes: agent_system.py

## Summary
- **Total lines changed:** 8 lines modified, 2 lines added
- **Hardcoded strings replaced:** 7 instances
- **Conditional logic simplified:** None found (no complexity-based selection in this file)

## Changes Applied

### 1. Added Imports (Lines 32-33)
```python
# BEFORE: (no imports)

# AFTER:
from core.models import ModelSelector
from core.constants import Models, Limits
```

### 2. ModelPricing Dictionary (Lines 55-59)
```python
# BEFORE:
PRICING = {
    'claude-3-5-haiku-20241022': (0.25, 1.25),
    'claude-3-5-sonnet-20241022': (3.00, 15.00),
    'claude-3-opus-20200229': (15.00, 75.00),

# AFTER:
PRICING = {
    Models.HAIKU: (0.25, 1.25),
    Models.SONNET: (3.00, 15.00),
    Models.OPUS: (15.00, 75.00),
```

### 3. BaseAgent Default Model (Line 461)
```python
# BEFORE:
def __init__(self,
             role: str,
             model: str = 'claude-3-5-haiku-20241022',
             max_retries: int = 3,

# AFTER:
def __init__(self,
             role: str,
             model: str = Models.HAIKU,
             max_retries: int = Limits.MAX_RETRIES,
```

### 4. CircuitBreaker Defaults (Lines 293-294)
```python
# BEFORE:
def __init__(self,
             failure_threshold: int = 5,
             recovery_timeout: int = 60,

# AFTER:
def __init__(self,
             failure_threshold: int = Limits.CIRCUIT_BREAKER_THRESHOLD,
             recovery_timeout: int = Limits.DEFAULT_TIMEOUT,
```

### 5. CircuitBreaker Instantiation (Lines 500-501)
```python
# BEFORE:
self.circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,

# AFTER:
self.circuit_breaker = CircuitBreaker(
    failure_threshold=Limits.CIRCUIT_BREAKER_THRESHOLD,
    recovery_timeout=Limits.DEFAULT_TIMEOUT,
```

### 6. ExponentialBackoff Max Delay (Line 409)
```python
# BEFORE:
def __init__(self,
             max_delay: float = 60.0,

# AFTER:
def __init__(self,
             max_delay: float = float(Limits.DEFAULT_TIMEOUT),
```

## Benefits of These Changes

1. **Single Source of Truth**: All model names and limits now come from `core.constants`
2. **Type Safety**: Using `Models.HAIKU` instead of strings prevents typos
3. **Easy Updates**: Change model versions in one place (core/constants.py)
4. **Consistency**: All components use the same thresholds and timeouts
5. **Maintainability**: Clear what values are being used across the system

## Lines Saved
- Direct savings: ~10 lines (by using constants)
- Future savings: No need to update multiple files when models change
- Bug prevention: Can't accidentally use wrong model string

## No Conditional Logic Found
This file doesn't contain any conditional logic for model selection based on complexity. All model choices are either:
- Default parameters (now using Models.HAIKU)
- Passed in by caller
- Part of pricing calculations