# Architecture Diagrams - Phase 2B: Protocol-Based Dependency Injection

**Version:** 1.0.0
**Date:** 2025-11-09
**Status:** Phase 2B Complete

---

## Table of Contents

1. [Before vs After Overview](#before-vs-after-overview)
2. [Detailed Import Graph](#detailed-import-graph)
3. [Component Interaction](#component-interaction)
4. [Factory Pattern Flow](#factory-pattern-flow)
5. [Testing Architecture](#testing-architecture)
6. [Migration Path](#migration-path)

---

## Before vs After Overview

### The Problem: Circular Dependency

**Before Phase 2B:**

```
┌─────────────────────────────────────────────────────────────┐
│                   CIRCULAR DEPENDENCY                        │
│                     (Import Error)                           │
└─────────────────────────────────────────────────────────────┘

  validation_orchestrator.py ←──────────┐
           │                             │
           │ imports                     │ imports
           ↓                             │
  critic_orchestrator.py  ───────────────┘

                  ❌ CIRCULAR!

  Result: ImportError at runtime
  "cannot import name 'CriticOrchestrator' from partially
   initialized module 'validation_orchestrator'"
```

### The Solution: Protocol-Based Dependency Inversion

**After Phase 2B:**

```
┌─────────────────────────────────────────────────────────────┐
│              PROTOCOL-BASED ARCHITECTURE                     │
│                  (No Circular Imports)                       │
└─────────────────────────────────────────────────────────────┘

                    protocols/
                   /          \
        (imports) ↓            ↓ (imports)
                /              \
    validation/           critic_orchestrator.py
    critic_integration.py
                \              /
                 ↓            ↓
              protocols/factory.py
              (runtime wiring)

                  ✅ ACYCLIC!

  Result: Clean import graph, dependency inversion achieved
```

---

## Detailed Import Graph

### Before Phase 2B: Circular Imports

```
┌────────────────────────────────────────────────────────────────┐
│                    IMPORT DEPENDENCY GRAPH                     │
│                        (BEFORE PHASE 2B)                       │
└────────────────────────────────────────────────────────────────┘

validation_orchestrator.py (2,142 lines)
    │
    ├─→ resilient_agent.ResilientBaseAgent
    ├─→ validation_types (ValidationResult, ValidationReport)
    ├─→ observability.event_emitter
    │
    └─→ critic_orchestrator.CriticOrchestrator ❌
            │
            ├─→ agent_system.BaseAgent
            ├─→ observability.event_emitter
            │
            └─→ validation_orchestrator.ValidationOrchestrator ❌
                    │
                    └─→ [CIRCULAR BACK TO TOP!]

⚠️ PROBLEM: Circular import causes:
   - Import errors at runtime
   - Fragile initialization order
   - Lazy imports required (hides dependency)
   - Difficult to test
   - Tight coupling
```

### After Phase 2B: Acyclic Import Graph (DAG)

```
┌────────────────────────────────────────────────────────────────┐
│                    IMPORT DEPENDENCY GRAPH                     │
│                        (AFTER PHASE 2B)                        │
│                  Directed Acyclic Graph (DAG)                  │
└────────────────────────────────────────────────────────────────┘

protocols/__init__.py (pure types - no concrete imports)
    ├─→ typing.Protocol
    ├─→ typing.runtime_checkable
    ├─→ dataclasses
    └─→ [NO CONCRETE IMPLEMENTATIONS]

        │ imported by            │ imported by
        ↓                        ↓

validation/critic_integration.py    critic_orchestrator.py
    │                                    │
    ├─→ protocols.CriticProtocol ✅      ├─→ protocols.ValidationProtocol ✅
    ├─→ validation_types                 ├─→ agent_system.BaseAgent
    └─→ resilient_agent                  └─→ observability.event_emitter

        │                                │
        │ imported by                    │ imported by
        ↓                                ↓

            protocols/factory.py
            (Runtime Wiring Only)
                │
                ├─→ validation.core.ValidationOrchestrator
                ├─→ critic_orchestrator.CriticOrchestrator
                └─→ protocols (type hints only)

✅ SOLUTION: Acyclic graph allows:
   - Clean imports (no errors)
   - Independent module development
   - Easy testing (inject mocks)
   - Loose coupling
   - Type-safe interfaces
```

---

## Component Interaction

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      LAYER ARCHITECTURE                         │
│                  (Dependency Inversion Principle)               │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  LAYER 1: ABSTRACT INTERFACES (protocols/)                    │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Validation   │  │   Critic     │  │  Orchestrator    │   │
│  │  Protocol    │  │   Protocol   │  │    Protocol      │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                                │
│  • Pure type definitions (Protocol classes)                   │
│  • No concrete implementations                                │
│  • No external dependencies (only stdlib)                     │
└───────────────────────────────────────────────────────────────┘
                            ↑ depends on (imports)
                            │
┌───────────────────────────────────────────────────────────────┐
│  LAYER 2: CONCRETE IMPLEMENTATIONS                            │
│                                                                │
│  ┌────────────────────────┐    ┌─────────────────────────┐   │
│  │  ValidationOrchestrator│    │  CriticOrchestrator     │   │
│  │  (validation/core.py)  │    │  (critic_orchestrator)  │   │
│  │                        │    │                         │   │
│  │  implements:           │    │  implements:            │   │
│  │  ValidationProtocol    │    │  CriticProtocol         │   │
│  │                        │    │                         │   │
│  │  depends on:           │    │  depends on:            │   │
│  │  - CriticProtocol ✅   │    │  - ValidationProtocol✅ │   │
│  └────────────────────────┘    └─────────────────────────┘   │
│                                                                │
│  • Concrete business logic                                    │
│  • Depend on protocols, not each other                        │
│  • Support dependency injection                               │
└───────────────────────────────────────────────────────────────┘
                            ↑ created by
                            │
┌───────────────────────────────────────────────────────────────┐
│  LAYER 3: DEPENDENCY INJECTION (protocols/factory.py)         │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           DependencyFactory                           │    │
│  │                                                       │    │
│  │  create_validation_orchestrator()                    │    │
│  │  create_critic_orchestrator()                        │    │
│  │  create_wired_system() ← RECOMMENDED                 │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                                │
│  • Knows about concrete implementations                       │
│  • Handles dependency wiring                                  │
│  • Provides clean API for consumers                           │
└───────────────────────────────────────────────────────────────┘
                            ↑ used by
                            │
┌───────────────────────────────────────────────────────────────┐
│  LAYER 4: APPLICATION CODE                                    │
│                                                                │
│  from protocols.factory import DependencyFactory              │
│                                                                │
│  validator, critic = DependencyFactory.create_wired_system()  │
│  results = validator.validate(code)                           │
│                                                                │
│  • Simple, clean API                                          │
│  • No knowledge of wiring details                             │
│  • Type-safe                                                  │
└───────────────────────────────────────────────────────────────┘
```

### Runtime Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│               RUNTIME COMPONENT INTERACTION                     │
│                  (Bidirectional Communication)                  │
└─────────────────────────────────────────────────────────────────┘

User Code
   │
   │ calls create_wired_system()
   ↓
DependencyFactory
   │
   ├─→ 1. Create ValidationOrchestrator (without critic)
   │       validator = ValidationOrchestrator()
   │
   ├─→ 2. Create CriticOrchestrator (without validator)
   │       critic = CriticOrchestrator()
   │
   ├─→ 3. Wire bidirectional dependencies
   │       validator.set_critic(critic)        ← inject critic
   │       critic.set_validator(validator)     ← inject validator
   │
   └─→ 4. Return wired system
           return (validator, critic)

Now both components can communicate:

ValidationOrchestrator                CriticOrchestrator
       │                                     │
       │ has reference to                   │ has reference to
       │ _critic: CriticProtocol             │ _validator: ValidationProtocol
       │                                     │
       │──────── validate_with_critics() ────→│
       │         (uses critic.critique())    │
       │                                     │
       │←─── validate_critique_quality() ────│
                (uses validator.validate())

✅ Benefits:
   - Both components can call each other
   - No circular import (wired at runtime)
   - Type-safe (protocol-based)
   - Easy to test (inject mocks)
```

---

## Factory Pattern Flow

### Component Creation and Wiring

```
┌─────────────────────────────────────────────────────────────────┐
│              FACTORY PATTERN: CREATION FLOW                     │
└─────────────────────────────────────────────────────────────────┘

Option 1: Create Wired System (RECOMMENDED)
───────────────────────────────────────────

from protocols.factory import DependencyFactory

validator, critic = DependencyFactory.create_wired_system()

                    │
                    ↓
        ┌───────────────────────┐
        │   DependencyFactory   │
        └───────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ↓                       ↓
┌──────────────┐        ┌──────────────┐
│ Validator    │        │   Critic     │
│ (created)    │        │  (created)   │
└──────────────┘        └──────────────┘
        │                       │
        │  validator.set_critic(critic)
        └──────────→ ⚡ ←────────┘
                    Wired!
        ┌──────────→ ⚡ ←────────┐
        │  critic.set_validator(validator)
        │                       │
        ↓                       ↓
┌──────────────┐        ┌──────────────┐
│ Validator    │◀──────▶│   Critic     │
│ (with critic)│        │(with validator)│
└──────────────┘        └──────────────┘
        │                       │
        └───────────┬───────────┘
                    │
                    ↓
        Returned to user as tuple
        (validator, critic)


Option 2: Independent Components
──────────────────────────────────

validator = DependencyFactory.create_validation_orchestrator()
# No critic injected, can add later

                    │
                    ↓
        ┌───────────────────────┐
        │ Validator (no critic) │
        └───────────────────────┘
                    │
        validator.set_critic(custom_critic)  ← Manual injection
                    │
                    ↓
        ┌───────────────────────┐
        │ Validator (with critic)│
        └───────────────────────┘


Option 3: Custom Implementations
───────────────────────────────────

class CustomCritic:
    def critique(self, data, context=None): ...
    def assess_quality(self, critique, criteria=None): ...

validator = DependencyFactory.create_validation_orchestrator(
    critic=CustomCritic()  ← Inject custom implementation
)

                    │
                    ↓
        ┌───────────────────────────┐
        │ Validator (custom critic) │
        └───────────────────────────┘
```

---

## Testing Architecture

### Test Doubles (No Mock Framework Needed)

```
┌─────────────────────────────────────────────────────────────────┐
│                   TESTING ARCHITECTURE                          │
│                  (Protocol-Based Test Doubles)                  │
└─────────────────────────────────────────────────────────────────┘

Production Code:
────────────────

┌────────────────┐         ┌────────────────┐
│  Validator     │◀───────▶│    Critic      │
│(production impl)│         │(production impl)│
└────────────────┘         └────────────────┘
        │                          │
        │ implements              │ implements
        ↓                          ↓
┌──────────────────┐      ┌──────────────────┐
│ValidationProtocol│      │  CriticProtocol  │
└──────────────────┘      └──────────────────┘


Test Code:
──────────

┌────────────────┐         ┌────────────────┐
│  Validator     │◀───────▶│   MockCritic   │ ← Simple test double
│(real impl)     │         │  (test impl)   │
└────────────────┘         └────────────────┘
        │                          │
        │ implements              │ implements
        ↓                          ↓
┌──────────────────┐      ┌──────────────────┐
│ValidationProtocol│      │  CriticProtocol  │
└──────────────────┘      └──────────────────┘


Test Implementation:
────────────────────

class MockCritic:
    """Simple test double - no inheritance needed!"""

    def critique(self, data, context=None):
        return [ValidationResult(level="info", message="test")]

    def assess_quality(self, critique, criteria=None):
        return QualityScore(value=0.9, confidence=1.0)

# Use in test
validator = DependencyFactory.create_validation_orchestrator(
    critic=MockCritic()  ← Inject test double
)

✅ Benefits:
   - No mock framework needed
   - Simple, readable test code
   - Fast test execution
   - Easy to create custom test scenarios
```

### Test Isolation

```
┌─────────────────────────────────────────────────────────────────┐
│                      TEST ISOLATION                             │
└─────────────────────────────────────────────────────────────────┘

Unit Test: Validator in Isolation
──────────────────────────────────

validator = DependencyFactory.create_validation_orchestrator()
# No critic - test validator logic alone

                    ┌───────────┐
                    │ Validator │  ← Test in isolation
                    └───────────┘
                         │
                         │ No external dependencies
                         ↓
                    ┌───────────┐
                    │   Tests   │
                    └───────────┘


Integration Test: Validator + Mock Critic
──────────────────────────────────────────

class MockCritic:
    def critique(self, data, context=None): ...

validator = DependencyFactory.create_validation_orchestrator(
    critic=MockCritic()
)

        ┌───────────┐         ┌──────────────┐
        │ Validator │◀───────▶│ MockCritic   │
        └───────────┘         └──────────────┘
             │                      │
             │ Integration test     │
             ↓                      ↓
        ┌──────────────────────────────┐
        │          Tests               │
        └──────────────────────────────┘


Full Integration Test: Real Components
───────────────────────────────────────

validator, critic = DependencyFactory.create_wired_system()

        ┌───────────┐         ┌──────────┐
        │ Validator │◀───────▶│  Critic  │
        │  (real)   │         │  (real)  │
        └───────────┘         └──────────┘
             │                      │
             │ Full integration     │
             ↓                      ↓
        ┌──────────────────────────────┐
        │          Tests               │
        └──────────────────────────────┘
```

---

## Migration Path

### Gradual Migration Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    MIGRATION TIMELINE                           │
│                  (8-Week Migration Period)                      │
└─────────────────────────────────────────────────────────────────┘

Week 0-2: Protocol Implementation
───────────────────────────────────
Status: ✅ COMPLETE

    Old Code              New Code
    ────────              ────────

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ validation   │─────▶│  protocols/  │◀─────│   critic     │
│ orchestrator │ ❌   │ (protocols)  │      │orchestrator  │
└──────────────┘      └──────────────┘      └──────────────┘
    Circular!             Acyclic! ✅


Week 2-8: Migration Period
────────────────────────────
Status: In Progress

Both patterns supported:

Old Pattern (Deprecated, with warnings):
    from validation_orchestrator import ValidationOrchestrator
    validator = ValidationOrchestrator()  ⚠️ Deprecation warning

New Pattern (Recommended):
    from protocols.factory import DependencyFactory
    validator, critic = DependencyFactory.create_wired_system() ✅


Week 8+: Completion
────────────────────
Status: Future

Only new pattern supported:
    - Old imports may stop working
    - Protocol pattern is standard
    - All code migrated


Migration Flow for Individual Modules:
───────────────────────────────────────

┌────────────┐
│ Old Module │
│ (circular  │
│  imports)  │
└─────┬──────┘
      │
      │ Step 1: Update imports
      ↓
┌────────────┐
│ Replace    │
│ concrete   │
│ imports    │
│ with       │
│ protocols  │
└─────┬──────┘
      │
      │ Step 2: Add DI support
      ↓
┌────────────┐
│ Add        │
│ __init__() │
│ with       │
│ optional   │
│ injection  │
└─────┬──────┘
      │
      │ Step 3: Add setter
      ↓
┌────────────┐
│ Add        │
│ set_dep()  │
│ method     │
└─────┬──────┘
      │
      │ Step 4: Use factory
      ↓
┌────────────┐
│ Update     │
│ consumers  │
│ to use     │
│ factory    │
└─────┬──────┘
      │
      │ Step 5: Test
      ↓
┌────────────┐
│ New Module │ ✅
│ (protocol- │
│  based)    │
└────────────┘
```

---

## Component Dependency Matrix

### Before Phase 2B

```
┌─────────────────────────────────────────────────────────────────┐
│              DEPENDENCY MATRIX (BEFORE)                         │
└─────────────────────────────────────────────────────────────────┘

                      Depends On
                  ┌───┬───┬───┬───┐
                  │Val│Cri│Pro│Fac│
              ────┼───┼───┼───┼───┤
       Validation │ - │ ✅ │ ❌ │ ❌ │  Depends on Critic ❌
              Crit│ ✅ │ - │ ❌ │ ❌ │  Depends on Validator ❌
         Protocols│ ❌ │ ❌ │ - │ ❌ │  (didn't exist)
           Factory│ ❌ │ ❌ │ ❌ │ - │  (didn't exist)
              ────└───┴───┴───┴───┘

❌ CIRCULAR: Validation ↔ Critic
```

### After Phase 2B

```
┌─────────────────────────────────────────────────────────────────┐
│              DEPENDENCY MATRIX (AFTER)                          │
└─────────────────────────────────────────────────────────────────┘

                      Depends On
                  ┌───┬───┬───┬───┐
                  │Val│Cri│Pro│Fac│
              ────┼───┼───┼───┼───┤
       Validation │ - │ ❌ │ ✅ │ ❌ │  Depends on Protocols ✅
              Crit│ ❌ │ - │ ✅ │ ❌ │  Depends on Protocols ✅
         Protocols│ ❌ │ ❌ │ - │ ❌ │  No dependencies (pure types)
           Factory│ ✅ │ ✅ │ ✅ │ - │  Coordinates all (runtime only)
              ────└───┴───┴───┴───┘

✅ ACYCLIC: Clean dependency graph
```

---

## Summary Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│          PHASE 2B: COMPLETE ARCHITECTURE OVERVIEW               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: Protocols (Abstract Interfaces)                       │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│ │ Validation   │  │   Critic     │  │  Orchestrator    │      │
│ │  Protocol    │  │   Protocol   │  │    Protocol      │      │
│ └──────────────┘  └──────────────┘  └──────────────────┘      │
│                                                                 │
│ • Pure type definitions                                        │
│ • No concrete imports                                          │
│ • Foundation for dependency inversion                          │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                    (imports protocols)
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: Implementations                                       │
│                                                                 │
│ ┌───────────────────────┐         ┌──────────────────────┐    │
│ │ ValidationOrchestrator│         │ CriticOrchestrator   │    │
│ │                       │         │                      │    │
│ │ + __init__(critic?)   │         │ + __init__(validator?)│   │
│ │ + set_critic()        │         │ + set_validator()    │    │
│ │ + validate()          │         │ + critique()         │    │
│ └───────────────────────┘         └──────────────────────┘    │
│                                                                 │
│ • Concrete business logic                                      │
│ • Depend on protocols, not each other                          │
│ • Support dependency injection                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                      (created/wired by)
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: Factory (Dependency Injection)                        │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │              DependencyFactory                           │   │
│ │                                                          │   │
│ │  + create_validation_orchestrator(critic?, config?)     │   │
│ │  + create_critic_orchestrator(validator?, config?)      │   │
│ │  + create_wired_system(config?) ← RECOMMENDED           │   │
│ │                                                          │   │
│ │  Handles:                                                │   │
│ │  - Component instantiation                               │   │
│ │  - Dependency wiring                                     │   │
│ │  - Configuration management                              │   │
│ └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                         (used by)
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: Application Code                                      │
│                                                                 │
│  from protocols.factory import DependencyFactory               │
│                                                                 │
│  validator, critic = DependencyFactory.create_wired_system()   │
│  results = validator.validate(code)                            │
│                                                                 │
│  • Simple, clean API                                           │
│  • No knowledge of wiring complexity                           │
│  • Type-safe, testable                                         │
└─────────────────────────────────────────────────────────────────┘

KEY BENEFITS:
✅ No circular dependencies (DAG)
✅ Type-safe (Protocol-based)
✅ Easy to test (inject mocks)
✅ Flexible (swap implementations)
✅ Backward compatible (8-week migration)
```

---

## Version History

| Version | Date       | Changes                      | Author              |
|---------|------------|------------------------------|---------------------|
| 1.0.0   | 2025-11-09 | Initial architecture diagrams| Documentation Expert |

---

**Status:** ✅ Complete (Phase 2B)
**Related Documents:**
- ADR-004: Protocol-Based Dependency Injection
- PROTOCOLS.md: Comprehensive protocol guide
- MIGRATION_GUIDE_PHASE_2B.md: Migration instructions
- CURRENT_ARCHITECTURE.md: Updated architecture documentation

---

**For More Information:**
- See PROTOCOLS.md for detailed protocol usage
- See MIGRATION_GUIDE_PHASE_2B.md for step-by-step migration
- See ADR-004 for architectural rationale
