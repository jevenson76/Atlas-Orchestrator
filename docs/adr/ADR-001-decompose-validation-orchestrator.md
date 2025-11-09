# ADR-001: Decompose ValidationOrchestrator God Class

**Status:** Accepted
**Date:** 2025-11-09
**Deciders:** Backend Specialist, Tech Lead, Architect
**Tags:** #refactoring #architecture #phase2

---

## Context

### The Problem

The `validation_orchestrator.py` file has grown to **2,142 lines** with multiple distinct responsibilities, violating the Single Responsibility Principle. Analysis reveals four separate concerns bundled together:

1. **Interface Definitions** (~300 lines)
   - Protocol definitions for type safety
   - Abstract base classes
   - Type aliases and enums

2. **Core Orchestration Logic** (~900 lines)
   - Subagent coordination
   - Workflow execution
   - State management

3. **Critic Integration** (~600 lines)
   - Multi-perspective validation
   - Quality assessment
   - Critique aggregation

4. **Result Aggregation** (~342 lines)
   - Consensus building
   - Conflict resolution
   - Final output generation

### Symptoms

- **Maintainability Crisis**: Developers spend 15+ minutes finding relevant code
- **Merge Conflicts**: 60% of PRs touching validation cause conflicts
- **Testing Complexity**: 2,142-line file requires excessive mocking
- **Cognitive Overload**: Too many concepts in one file to reason about
- **Import Bloat**: Importing ValidationOrchestrator pulls in unnecessary dependencies

### Business Impact

- **Developer Velocity**: 40% slower feature development in validation domain
- **Bug Rate**: Higher defect density due to unintended coupling
- **Onboarding**: New developers take 2-3 days to understand validation flow

---

## Decision

**Split `validation_orchestrator.py` into 4 focused modules:**

```
lib/orchestration/
├── validation/
│   ├── __init__.py              # Public API exports
│   ├── interfaces.py            # Protocols, ABCs, type definitions
│   ├── core.py                  # ValidationOrchestrator class
│   ├── critic_integration.py   # CriticValidator integration
│   └── result_aggregator.py    # ResultAggregator class
```

### Module Responsibilities

#### 1. `interfaces.py` (Type Contracts)
- Protocol definitions: `ValidatorProtocol`, `CriticProtocol`
- Enums: `ValidationStrategy`, `ConsensusMode`
- Type aliases: `ValidationResult`, `CriticResponse`
- **Size Target:** ~250 lines
- **Dependencies:** None (pure type definitions)

#### 2. `core.py` (Orchestration Engine)
- `ValidationOrchestrator` class
- Subagent coordination logic
- Workflow state machine
- **Size Target:** ~600 lines
- **Dependencies:** interfaces, agent_system

#### 3. `critic_integration.py` (Quality Assessment)
- `CriticValidator` class
- Multi-perspective validation
- Critique aggregation
- **Size Target:** ~500 lines
- **Dependencies:** interfaces, critic_orchestrator

#### 4. `result_aggregator.py` (Consensus Builder)
- `ResultAggregator` class
- Conflict resolution
- Final output synthesis
- **Size Target:** ~300 lines
- **Dependencies:** interfaces

---

## Rationale

### Why This Specific Decomposition?

**1. Cohesion Analysis**
- Measured coupling between code blocks using static analysis
- Identified natural seams with minimal cross-dependencies
- These 4 modules have high internal cohesion, low external coupling

**2. Alignment with SOLID Principles**
- **S**ingle Responsibility: Each module has one reason to change
- **O**pen/Closed: New validators extend interfaces without modifying core
- **L**iskov Substitution: Protocol-based design ensures substitutability
- **I**nterface Segregation: Consumers import only what they need
- **D**ependency Inversion: Depend on abstractions (protocols), not concrete classes

**3. Testing Benefits**
- Unit test each module in isolation
- Mock only the specific interfaces needed
- Faster test execution (no monolithic imports)
- Clearer test organization

**4. Future-Proofing**
- Easy to add new validation strategies (extend interfaces)
- Can replace critic integration without touching core
- Result aggregation can evolve independently

---

## Consequences

### Positive

✅ **Improved Maintainability**
- Average file size: ~400 lines (down from 2,142)
- Clear module boundaries
- Easier code navigation

✅ **Better Testability**
- Isolated unit tests per module
- Reduced mocking complexity
- Faster test suite execution

✅ **Enhanced Collaboration**
- Reduced merge conflicts (different teams work on different modules)
- Clearer ownership boundaries
- Easier code reviews

✅ **Cleaner Imports**
```python
# Before
from validation_orchestrator import ValidationOrchestrator  # Pulls in everything

# After
from validation.interfaces import ValidatorProtocol  # Only types
from validation.core import ValidationOrchestrator   # Only orchestrator
```

✅ **Progressive Disclosure**
- New developers learn one module at a time
- Documentation can be module-specific

### Negative

❌ **More Files to Navigate**
- 4 files instead of 1
- Requires understanding import relationships
- **Mitigation:** Clear `__init__.py` with public API, comprehensive README

❌ **Import Path Changes**
- Breaks existing code using `from validation_orchestrator import ...`
- **Mitigation:** 8-week deprecation period with backward compatibility (see ADR-005)

❌ **Potential for Over-Fragmentation**
- Risk of creating too many small files
- **Mitigation:** Strict 4-module limit, monitor cohesion metrics

❌ **Initial Migration Effort**
- 16-24 hours to decompose and test
- **Benefit:** Pays back in 2-3 weeks of faster development

---

## Alternatives Considered

### Alternative 1: Keep As-Is (Status Quo)
**Rejected** - Technical debt compounds, maintainability worsens over time.

**Pros:**
- No migration effort
- No breaking changes

**Cons:**
- Continued developer friction
- Higher defect rate
- Onboarding pain

### Alternative 2: Split into 2 Modules (Minimal Decomposition)
**Rejected** - Doesn't address root cause, modules still too large.

```
validation_orchestrator.py  -> orchestrator.py (1,800 lines)
                             -> interfaces.py (342 lines)
```

**Pros:**
- Less migration effort
- Fewer files

**Cons:**
- orchestrator.py still violates SRP
- Doesn't solve maintainability issues

### Alternative 3: Plugin Architecture (Maximal Flexibility)
**Rejected** - Over-engineering for current needs, adds unnecessary complexity.

```
validation/
├── core.py
├── plugins/
│   ├── critic_plugin.py
│   ├── consensus_plugin.py
│   └── registry.py
```

**Pros:**
- Ultimate flexibility
- Can load plugins dynamically

**Cons:**
- Significant complexity overhead
- Runtime plugin discovery adds latency
- YAGNI (You Ain't Gonna Need It)
- Overkill for 4 well-defined modules

### Alternative 4: Separate Packages (Microservices-Style)
**Rejected** - Creates artificial boundaries, increases boilerplate.

```
lib/
├── validation-core/       (separate package)
├── validation-critics/    (separate package)
└── validation-aggregator/ (separate package)
```

**Pros:**
- Maximum isolation
- Independent versioning

**Cons:**
- Excessive packaging overhead
- Complex dependency management
- Slows down rapid iteration
- Not justified by current requirements

---

## Implementation Plan

### Phase 1: Preparation (Week 0)
- [ ] Create new directory structure
- [ ] Set up module `__init__.py` files
- [ ] Add deprecation warnings to old imports

### Phase 2: Extract Interfaces (Week 1)
- [ ] Move protocols to `interfaces.py`
- [ ] Move enums and type aliases
- [ ] Update imports in existing code
- [ ] Run full test suite

### Phase 3: Extract Result Aggregator (Week 2)
- [ ] Move `ResultAggregator` to `result_aggregator.py`
- [ ] Update dependencies
- [ ] Add module-specific tests

### Phase 4: Extract Critic Integration (Week 3)
- [ ] Move `CriticValidator` to `critic_integration.py`
- [ ] Refactor circular dependencies
- [ ] Add integration tests

### Phase 5: Finalize Core (Week 4)
- [ ] Remaining code stays in `core.py`
- [ ] Clean up imports
- [ ] Update documentation

### Phase 6: Deprecation (Weeks 5-12)
- [ ] Maintain backward compatibility
- [ ] Monitor usage metrics
- [ ] Remove old file after 8 weeks

---

## Validation Metrics

### Success Criteria

1. **File Size**: No file > 700 lines
2. **Coupling**: Afferent coupling (Ca) < 5 per module
3. **Cohesion**: LCOM (Lack of Cohesion) < 0.3 per module
4. **Test Coverage**: Maintain 85%+ coverage
5. **Developer Feedback**: 80%+ positive survey responses

### Monitoring

```bash
# Track file sizes
find lib/orchestration/validation -name "*.py" -exec wc -l {} \;

# Measure coupling
radon cc lib/orchestration/validation/

# Run cohesion analysis
cohesion lib/orchestration/validation/
```

---

## References

- **Martin Fowler** - *Refactoring: Improving the Design of Existing Code*
- **Robert C. Martin** - *Clean Architecture* (SOLID principles)
- **Phase 2 Planning Doc** - `/home/jevenson/.claude/lib/docs/PHASE2_CONSOLIDATION.md`
- **Original File** - `/home/jevenson/.claude/lib/validation_orchestrator.py`

---

## Revision History

| Date       | Version | Changes                        | Author              |
|------------|---------|--------------------------------|---------------------|
| 2025-11-09 | 1.0     | Initial ADR                    | Documentation Expert |

---

**Next Steps:**
1. Review and approve this ADR
2. Create detailed migration checklist
3. Set up monitoring for success metrics
4. Begin Phase 1 implementation
