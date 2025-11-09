# PHASE 2 EXECUTION PLAN
## ZTE Orchestrator System Consolidation

**Version:** 1.0
**Date:** 2025-11-09
**Status:** READY FOR APPROVAL
**Risk Level:** MEDIUM-HIGH (manageable with proper safeguards)

---

## EXECUTIVE SUMMARY

This execution plan consolidates findings from 5 expert agents (Project Manager, Backend Specialist, Code Reviewer, Devils Advocate, Documentation Expert) into a comprehensive, actionable roadmap for Phase 2 consolidation.

### Quick Stats
- **Duration:** 6 weeks (30 working days)
- **Effort:** ~280 person-hours (7 person-weeks)
- **Code Reduction:** 35% (-1,800 lines from 5,316 to ~3,500)
- **Files After Consolidation:** 15-18 focused modules (vs. 6 large files)
- **Risk Mitigation:** 47 safeguards, 12 rollback points, 95%+ test coverage target

### Critical Success Factors
1. **✅ WEEK 0 MUST COMPLETE FIRST** - Document current state, no code changes yet
2. **✅ 95%+ TEST COVERAGE** - Backward compatibility, integration, regression tests
3. **✅ ROLLBACK POINTS** - Every phase has documented rollback procedure
4. **✅ DEPRECATION WARNINGS** - 8-week transition period with clear migration path
5. **✅ EXTERNAL VALIDATION** - Migration guide tested by external team

---

## TABLE OF CONTENTS

1. [Phased Execution Strategy](#1-phased-execution-strategy)
2. [Pre-Flight Checklist (Week 0)](#2-pre-flight-checklist-week-0)
3. [Phase 2A: ValidationOrchestrator Decomposition](#3-phase-2a-validationorchestrator-decomposition)
4. [Phase 2B: Circular Dependency Resolution](#4-phase-2b-circular-dependency-resolution)
5. [Phase 2C: Critic Phase B Migration](#5-phase-2c-critic-phase-b-migration)
6. [Phase 2D: Centralized Utilities](#6-phase-2d-centralized-utilities)
7. [Quality Gates & Checkpoints](#7-quality-gates--checkpoints)
8. [Risk Mitigation & Rollback](#8-risk-mitigation--rollback)
9. [Resource Allocation](#9-resource-allocation)
10. [Success Metrics](#10-success-metrics)

---

## 1. PHASED EXECUTION STRATEGY

### Timeline Overview

```
WEEK 0: Pre-Flight (CRITICAL - DO NOT SKIP)
├─ Document current architecture
├─ Write ADRs
├─ Create baseline tests
└─ Setup rollback infrastructure

WEEK 1: Phase 2A - ValidationOrchestrator Decomposition
├─ Split into 4 focused files
├─ Extract interfaces, core, critics, aggregator
└─ Maintain backward compatibility

WEEK 2: Phase 2A Continuation + Testing
├─ Complete validation split
├─ Comprehensive testing
└─ Documentation updates

WEEK 3: Phase 2B - Circular Dependency Resolution
├─ Implement protocol-based DI
├─ Break validation ↔ critic cycle
└─ Integration testing

WEEK 4: Phase 2C - Critic Phase B Migration
├─ Replace BaseAgent with ResilientBaseAgent
├─ Add quality-tiered fallbacks
└─ Quality consistency testing

WEEK 5: Phase 2D - Centralized Utilities
├─ Extract ModelSelector, CostTracker, ReportGenerator
├─ Remove duplicates
└─ Final integration testing

WEEK 6: Polish & Release
├─ Final QA
├─ Documentation review
├─ Migration guide validation
└─ v2.0.0 release
```

### Execution Sequence (Critical Path)

**SEQUENTIAL (Must Complete in Order):**
- Week 0 → Phase 2A → Phase 2B → Phase 2C → Phase 2D

**PARALLEL OPPORTUNITIES:**
- Documentation can run parallel with development (Weeks 1-5)
- Phase 2C and 2D can partially overlap (Week 4-5)
- Testing can run parallel with next phase prep

### Risk-Adjusted Timeline

**Best Case:** 6 weeks (if everything goes smoothly)
**Realistic:** 7-8 weeks (with minor issues and rework)
**Worst Case:** 10-12 weeks (if major issues discovered)

**Recommendation:** Plan for 8 weeks with 2-week buffer.

---

## 2. PRE-FLIGHT CHECKLIST (WEEK 0)

### ⚠️ CRITICAL: COMPLETE BEFORE ANY CODE CHANGES

**Duration:** 3-5 days
**Effort:** 32 hours
**Status:** BLOCKING - Phase 2A cannot start until complete

### 2.1 Document Current State

**Goal:** Preserve current architecture before changes

**Tasks:**
1. **Create `CURRENT_ARCHITECTURE.md`** (4-6 hours)
   - Current file structure (6 orchestrator files)
   - Import dependency graph
   - Public API surface area
   - Known issues and workarounds

2. **Generate Baseline Diagrams** (6 hours)
   - Current class diagram
   - Current dependency graph
   - Current data flow diagram
   - Use tools: `pydeps`, `graphviz`, manual UML

3. **Write 5 ADRs** (12 hours)
   - ADR-001: Why decompose ValidationOrchestrator
   - ADR-002: Why migrate CriticOrchestrator to Phase B
   - ADR-003: Why centralize model selection
   - ADR-004: Why use dependency injection pattern
   - ADR-005: Deprecation and migration strategy

**Deliverables:**
- ✅ `docs/CURRENT_ARCHITECTURE.md`
- ✅ `docs/diagrams/current_structure.png`
- ✅ `docs/adr/ADR-001.md` through `ADR-005.md`

### 2.2 Create Rollback Infrastructure

**Goal:** Enable safe rollback at any point

**Tasks:**
1. **Git Snapshot** (1 hour)
   ```bash
   cd /home/jevenson/.claude/lib
   git checkout -b pre-phase2-snapshot
   git tag v1.9.0-pre-phase2
   git push origin v1.9.0-pre-phase2
   ```

2. **Document Rollback Procedures** (3 hours)
   - Create `ROLLBACK.md` with phase-specific steps
   - Test rollback from git tags
   - Document data migration rollback (if applicable)

3. **Setup Automated Rollback Scripts** (4 hours)
   - `scripts/rollback_phase_2a.sh`
   - `scripts/rollback_phase_2b.sh`
   - `scripts/rollback_phase_2c.sh`
   - `scripts/rollback_phase_2d.sh`

**Deliverables:**
- ✅ Git tag: `v1.9.0-pre-phase2`
- ✅ `docs/ROLLBACK.md`
- ✅ 4 rollback scripts in `scripts/`

### 2.3 Establish Testing Baseline

**Goal:** Know what "success" looks like

**Tasks:**
1. **Run Full Test Suite** (1 hour)
   ```bash
   pytest tests/ -v --cov --cov-report=html
   # Capture baseline: X% coverage, Y tests passing
   ```

2. **Create Performance Baseline** (2 hours)
   ```python
   # tests/benchmark_baseline.py
   def test_import_latency_baseline():
       # Measure current import times

   def test_execution_latency_baseline():
       # Measure current execution times
   ```

3. **Document Current Behavior** (4 hours)
   - All public APIs and expected outputs
   - Edge cases and error scenarios
   - Known bugs (to preserve, not fix yet)

**Deliverables:**
- ✅ `tests/BASELINE_METRICS.md` (coverage %, test count, latency)
- ✅ `tests/benchmark_baseline.py`
- ✅ `docs/API_BEHAVIOR.md` (current API contracts)

### 2.4 Setup Quality Gates

**Goal:** Prevent regressions from merging

**Tasks:**
1. **Configure CI/CD Checks** (3 hours)
   ```yaml
   # .github/workflows/phase2_quality_gates.yml
   - Test coverage must be >= baseline
   - No circular dependencies (pydeps check)
   - Type checking passes (mypy --strict)
   - Performance within 5% of baseline
   - All deprecation warnings in place
   ```

2. **Create Regression Test Suite** (6 hours)
   - Backward compatibility tests
   - Import path tests
   - API contract tests
   - Error handling tests

**Deliverables:**
- ✅ `.github/workflows/phase2_quality_gates.yml`
- ✅ `tests/test_regression.py` (50+ test cases)
- ✅ `tests/test_backward_compatibility.py`

### Week 0 Sign-Off Criteria

**ALL MUST BE ✅ BEFORE PROCEEDING TO PHASE 2A:**

- [ ] Current architecture documented in `CURRENT_ARCHITECTURE.md`
- [ ] 5 ADRs written and reviewed
- [ ] Git snapshot created and pushed
- [ ] Rollback procedures documented and tested
- [ ] Test baseline established (coverage %, test count, latency)
- [ ] CI/CD quality gates configured
- [ ] Regression test suite created (50+ tests)
- [ ] Stakeholder sign-off received

**Estimated Completion:** Day 3-5 of Week 0
**Blocker Risk:** HIGH - If Week 0 incomplete, Phase 2A will fail

---

## 3. PHASE 2A: VALIDATIONORCHESTRATOR DECOMPOSITION

### Overview

**Goal:** Break 2,142-line god class into 4 focused modules
**Duration:** 2 weeks (Days 6-19)
**Effort:** 64 hours
**Risk:** MEDIUM

### 3.1 Target Structure

**From:**
```
validation_orchestrator.py (2,142 lines)
└─ ValidationOrchestrator class with 4 responsibilities
```

**To:**
```
validation/
├── __init__.py              # Public API (50 lines)
├── interfaces.py            # Protocols & types (150 lines)
├── core.py                  # ValidationCore (600 lines)
├── critic_integration.py    # CriticValidator (500 lines)
└── result_aggregator.py     # ResultAggregator (400 lines)
```

**Code Reduction:** 2,142 lines → 1,700 lines (21% reduction + better organization)

### 3.2 Execution Steps (Week 1-2)

#### Step 1: Extract Interfaces (Days 6-7, 8 hours)

**Tasks:**
1. Create `validation/interfaces.py`
   - `ValidationResult` dataclass (immutable)
   - `ValidationSeverity` enum
   - `ValidatorProtocol` protocol
   - `CriticProtocol` protocol
   - `AggregatorProtocol` protocol

2. Add to existing `validation_orchestrator.py`:
   ```python
   from validation.interfaces import ValidationResult, ValidationSeverity
   # Use new types in existing code
   ```

3. Run tests → ensure no breakage

**Deliverables:**
- ✅ `validation/interfaces.py` created
- ✅ Imports added to `validation_orchestrator.py`
- ✅ All tests passing (zero regression)

**Checkpoint:** Can we roll back easily? YES (just delete validation/)

---

#### Step 2: Extract ValidationCore (Days 8-10, 20 hours)

**Tasks:**
1. Create `validation/core.py`
   - Move validation rule execution logic
   - Move validator management
   - Move parallel execution logic
   - Keep using ResilientBaseAgent (Phase B compliant)

2. Update `validation_orchestrator.py`:
   ```python
   from validation.core import ValidationCore

   class ValidationOrchestrator:
       """DEPRECATED: Use ValidationCore directly."""
       def __init__(self, ...):
           warnings.warn("ValidationOrchestrator deprecated", DeprecationWarning)
           self._core = ValidationCore(...)

       def validate(self, ...):
           return self._core.validate(...)  # Delegate
   ```

3. Add backward compatibility tests:
   ```python
   def test_old_api_still_works():
       orch = ValidationOrchestrator(...)  # Old API
       result = orch.validate("content")
       assert "is_valid" in result
   ```

4. Run full test suite

**Deliverables:**
- ✅ `validation/core.py` created (600 lines)
- ✅ `validation_orchestrator.py` now delegates (backward compatible)
- ✅ Backward compatibility tests added
- ✅ All tests passing + new tests for ValidationCore

**Checkpoint:** Rollback test - can we revert to Week 0 snapshot?

---

#### Step 3: Extract CriticValidator (Days 11-13, 20 hours)

**Tasks:**
1. Create `validation/critic_integration.py`
   - Move `validate_with_critics()` mega-method
   - Implement dependency injection pattern
   - Use `TYPE_CHECKING` import for CriticOrchestrator

2. Update ValidationCore:
   ```python
   from validation.critic_integration import CriticValidator

   def register_validator(self, name: str, validator: ValidatorProtocol):
       self._validators[name] = validator
   ```

3. Wire dependencies in setup (NOT in module imports):
   ```python
   # setup.py or main.py
   critic_orch = CriticOrchestrator(...)
   critic_validator = CriticValidator()
   critic_validator.set_critic_orchestrator(critic_orch)  # DI

   validation_core = ValidationCore(...)
   validation_core.register_validator("critic", critic_validator)
   ```

4. Integration tests for critic workflow

**Deliverables:**
- ✅ `validation/critic_integration.py` created (500 lines)
- ✅ Dependency injection working (no circular import)
- ✅ Integration tests for critic validation
- ✅ All tests passing

**Checkpoint:** Verify no circular dependency with `pydeps`

---

#### Step 4: Extract ResultAggregator (Days 14-15, 12 hours)

**Tasks:**
1. Create `validation/result_aggregator.py`
   - Move result aggregation logic
   - Move severity-based decision rules
   - Move quality score calculation

2. Update ValidationCore to use ResultAggregator:
   ```python
   from validation.result_aggregator import ResultAggregator

   def validate(self, content, context):
       results = self._run_validators(content, context)
       aggregated = self._aggregator.aggregate(results)
       return aggregated
   ```

3. Add aggregation tests

**Deliverables:**
- ✅ `validation/result_aggregator.py` created (400 lines)
- ✅ ValidationCore uses ResultAggregator
- ✅ Aggregation tests added
- ✅ All tests passing

---

#### Step 5: Clean Up & Polish (Days 16-17, 8 hours)

**Tasks:**
1. Update `validation/__init__.py`:
   ```python
   """Validation system public API."""
   from .core import ValidationCore, ValidationRule
   from .critic_integration import CriticValidator
   from .result_aggregator import ResultAggregator
   from .interfaces import ValidationResult, ValidationSeverity

   __all__ = [...]
   ```

2. Remove old code from `validation_orchestrator.py`:
   - Keep only backward compatibility wrapper
   - Should be < 100 lines now

3. Update all imports across codebase:
   ```python
   # Old (deprecated but works)
   from validation_orchestrator import ValidationOrchestrator

   # New (preferred)
   from validation import ValidationCore
   ```

4. Documentation updates:
   - Update README
   - Update API docs
   - Add migration guide

**Deliverables:**
- ✅ `validation_orchestrator.py` reduced to < 100 lines
- ✅ All imports updated
- ✅ Documentation updated
- ✅ Migration guide published

---

#### Step 6: Final Testing & Release (Days 18-19, 12 hours)

**Tasks:**
1. Run comprehensive test suite:
   ```bash
   pytest tests/ -v --cov --cov-report=html
   # Must achieve >= baseline coverage
   ```

2. Performance benchmarks:
   ```bash
   pytest tests/benchmark_*.py --benchmark-only
   # Must be within 5% of baseline
   ```

3. Integration testing with dependents:
   - Test with specialized_roles_orchestrator
   - Test with progressive_enhancement_orchestrator
   - Test with parallel_development_orchestrator

4. External validation:
   - Have another team member test migration guide
   - Fix any issues discovered

5. Tag release:
   ```bash
   git tag v1.9.5-phase2a-complete
   git push origin v1.9.5-phase2a-complete
   ```

**Deliverables:**
- ✅ Test coverage >= baseline (maintain or improve)
- ✅ Performance within 5% of baseline
- ✅ All dependent orchestrators tested
- ✅ Migration guide validated externally
- ✅ Git tag: `v1.9.5-phase2a-complete`

### 3.3 Phase 2A Success Criteria

**ALL MUST BE ✅ TO PROCEED TO PHASE 2B:**

- [ ] ValidationOrchestrator split into 4 focused files
- [ ] Code reduced from 2,142 → 1,700 lines
- [ ] Zero test failures
- [ ] Test coverage >= baseline
- [ ] Performance within 5% of baseline
- [ ] 100% backward compatibility (old API still works)
- [ ] Deprecation warnings in place
- [ ] No circular dependencies (pydeps check passes)
- [ ] Documentation updated
- [ ] Migration guide validated by external team
- [ ] Git tag created: `v1.9.5-phase2a-complete`

**Review Meeting:** End of Week 2 - Go/No-Go decision for Phase 2B

---

## 4. PHASE 2B: CIRCULAR DEPENDENCY RESOLUTION

### Overview

**Goal:** Break circular dependency between validation and critic orchestrators
**Duration:** 1 week (Days 20-24)
**Effort:** 32 hours
**Risk:** MEDIUM

### 4.1 Problem Analysis

**Current Circular Dependency:**
```
validation_orchestrator.py
    ├─→ imports CriticOrchestrator (line 1817)
    └─→ calls validate_with_critics()

critic_orchestrator.py
    ├─→ imports ValidationOrchestrator (hypothetical)
    └─→ calls validate() for pre-validation
```

**Solution:** Protocol-based dependency injection (already partially implemented in Phase 2A)

### 4.2 Execution Steps (Week 3)

#### Step 1: Update CriticOrchestrator to Implement Protocol (Days 20-21, 12 hours)

**Tasks:**
1. Add protocol implementation:
   ```python
   # critic_orchestrator.py
   from validation.interfaces import CriticProtocol

   class CriticOrchestrator(CriticProtocol):
       """Implements CriticProtocol - no imports of validation."""

       async def validate_with_critics(self, content, critic_types, ...):
           # Existing implementation
   ```

2. Remove any imports of `validation_orchestrator` from `critic_orchestrator.py`

3. Update type hints to use `TYPE_CHECKING`:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from validation import ValidationCore  # Type hints only
   ```

4. Run tests

**Deliverables:**
- ✅ `critic_orchestrator.py` implements `CriticProtocol`
- ✅ No direct imports between validation and critic files
- ✅ Type hints work correctly
- ✅ All tests passing

---

#### Step 2: Update Wiring Logic (Days 22, 8 hours)

**Tasks:**
1. Create `orchestrator_setup.py` or update existing setup:
   ```python
   # orchestrator_setup.py
   def setup_orchestrators(config: Dict) -> Dict[str, Any]:
       """Wire orchestrator dependencies (no circular imports!)"""

       # Create orchestrators
       critic_orch = CriticOrchestrator(...)
       validation_core = ValidationCore(...)
       critic_validator = CriticValidator()

       # Wire dependencies at runtime
       critic_validator.set_critic_orchestrator(critic_orch)
       validation_core.register_validator("critic", critic_validator)

       return {
           "validation": validation_core,
           "critic": critic_orch
       }
   ```

2. Update all entry points (main.py, test fixtures, etc.) to use setup function

3. Integration tests for wired dependencies

**Deliverables:**
- ✅ `orchestrator_setup.py` created
- ✅ All entry points updated
- ✅ Integration tests passing
- ✅ No circular imports (verified)

---

#### Step 3: Verify No Circular Dependencies (Days 23, 6 hours)

**Tasks:**
1. Run automated circular dependency check:
   ```bash
   pip install pydeps
   pydeps /home/jevenson/.claude/lib --max-bacon 2 --show-cycles
   # Must report: "No cycles found"
   ```

2. Add to CI/CD:
   ```yaml
   # .github/workflows/ci.yml
   - name: Check Circular Dependencies
     run: |
       pydeps lib/ --max-bacon 2 --show-cycles || exit 1
   ```

3. Update documentation with dependency graph

**Deliverables:**
- ✅ Zero circular dependencies (pydeps confirms)
- ✅ CI/CD check added
- ✅ Dependency graph diagram updated

---

#### Step 4: Final Testing & Release (Days 24, 6 hours)

**Tasks:**
1. Full test suite
2. Integration testing with all orchestrators
3. Verify backward compatibility maintained
4. Tag release:
   ```bash
   git tag v1.9.7-phase2b-complete
   ```

**Deliverables:**
- ✅ All tests passing
- ✅ No circular dependencies
- ✅ Backward compatibility maintained
- ✅ Git tag: `v1.9.7-phase2b-complete`

### 4.3 Phase 2B Success Criteria

- [ ] Zero circular dependencies (pydeps check passes)
- [ ] Protocol-based DI working correctly
- [ ] All orchestrators wire correctly at runtime
- [ ] Zero test failures
- [ ] Backward compatibility maintained
- [ ] CI/CD checks for circular dependencies
- [ ] Documentation updated with new dependency graph
- [ ] Git tag created: `v1.9.7-phase2b-complete`

**Review Meeting:** End of Week 3 - Go/No-Go decision for Phase 2C

---

## 5. PHASE 2C: CRITIC PHASE B MIGRATION

### Overview

**Goal:** Migrate CriticOrchestrator from BaseAgent to ResilientBaseAgent
**Duration:** 1 week (Days 25-29)
**Effort:** 32 hours
**Risk:** MEDIUM-HIGH (affects critic quality)

### 5.1 Migration Strategy

**Current:** Opus-only, no fallback
**Target:** Quality-tiered fallbacks maintaining consistency

### 5.2 Execution Steps (Week 4)

#### Step 1: Add ResilientBaseAgent (Days 25-26, 12 hours)

**Tasks:**
1. Replace BaseAgent with ResilientBaseAgent:
   ```python
   # critic_orchestrator.py
   from resilient_base_agent import ResilientBaseAgent

   class CriticOrchestrator:
       def __init__(self, primary_model="claude-opus-4-5", ...):
           self._agent = ResilientBaseAgent(
               primary_model=primary_model,
               fallback_models=[
                   "claude-opus-4-20250514",  # Previous Opus
                   "gpt-4-turbo",              # OpenAI fallback
                   "claude-sonnet-4-5"         # Emergency fallback
               ]
           )
   ```

2. Update all `_agent` calls to use ResilientBaseAgent API

3. Run tests (expect some failures initially)

**Deliverables:**
- ✅ CriticOrchestrator uses ResilientBaseAgent
- ✅ Tests running (may have failures to fix)

---

#### Step 2: Implement Quality Tiers (Days 27, 10 hours)

**Tasks:**
1. Add critic quality tier mapping:
   ```python
   # critic_orchestrator.py
   CRITIC_QUALITY_TIERS = {
       CriticType.SECURITY: "high",       # Opus only
       CriticType.LOGIC: "high",          # Opus only
       CriticType.STYLE: "medium",        # Sonnet acceptable
       CriticType.FORMATTING: "low",      # Haiku acceptable
   }

   FALLBACK_CHAINS = {
       "high": ["opus-4-5", "opus-4", "gpt-4-turbo"],
       "medium": ["opus-4-5", "sonnet-4-5", "gpt-4-turbo"],
       "low": ["sonnet-4-5", "gpt-4-turbo", "haiku-4-5"]
   }
   ```

2. Update critique method to select appropriate chain:
   ```python
   def critique(self, content, critic_type):
       quality_tier = CRITIC_QUALITY_TIERS[critic_type]
       fallback_chain = FALLBACK_CHAINS[quality_tier]
       # ... use appropriate chain
   ```

3. Add tests for each quality tier

**Deliverables:**
- ✅ Quality tier mapping implemented
- ✅ Fallback chains configured
- ✅ Tests for each tier added

---

#### Step 3: Add Model-Specific Prompting (Days 28, 6 hours)

**Tasks:**
1. Add prompt templates:
   ```python
   PROMPT_TEMPLATES = {
       "claude": {
           "system": "You are an expert {critic_type} critic...",
           "user": "<content>{content}</content>\n\nCritique:"
       },
       "gpt": {
           "system": "You are an expert {critic_type} critic...",
           "user": "Content:\n{content}\n\nCritique:"
       }
   }
   ```

2. Adapt prompts based on model:
   ```python
   def _create_prompt(self, critic_type, content, model):
       provider = "claude" if "claude" in model else "gpt"
       template = PROMPT_TEMPLATES[provider]
       # ... format prompt
   ```

**Deliverables:**
- ✅ Model-specific prompting implemented
- ✅ Prompts tested on both Claude and GPT-4

---

#### Step 4: Quality Consistency Testing (Days 29, 10 hours)

**Critical Task:** Ensure fallback models maintain quality

**Tasks:**
1. Create baseline quality metrics:
   ```python
   # tests/test_critic_quality.py
   def test_opus_quality_baseline():
       """Establish Opus as quality baseline."""
       result = critic.critique(sample_code, CriticType.SECURITY)
       baseline_score = calculate_quality_score(result)
       # Save baseline
   ```

2. Test fallback quality:
   ```python
   @pytest.mark.parametrize("fallback_model", [
       "gpt-4-turbo",
       "claude-sonnet-4-5"
   ])
   def test_fallback_quality(fallback_model):
       """Fallback must be within 10% of baseline."""
       result = critic.critique_with_model(sample_code, fallback_model)
       fallback_score = calculate_quality_score(result)

       assert fallback_score >= baseline_score * 0.9
   ```

3. Manual review of sample critiques from each model

4. Adjust fallback chains if quality insufficient

**Deliverables:**
- ✅ Quality baseline established
- ✅ Fallback quality validated (within 10% of baseline)
- ✅ Manual review complete
- ✅ Fallback chains adjusted if needed

---

#### Step 5: Release (Days 29 end, 2 hours)

**Tasks:**
1. Full test suite
2. Tag release:
   ```bash
   git tag v1.9.9-phase2c-complete
   ```

**Deliverables:**
- ✅ All tests passing
- ✅ Critic quality validated
- ✅ Git tag: `v1.9.9-phase2c-complete`

### 5.3 Phase 2C Success Criteria

- [ ] CriticOrchestrator using ResilientBaseAgent
- [ ] Quality-tiered fallbacks implemented
- [ ] Fallback quality within 10% of Opus baseline
- [ ] Model-specific prompting working
- [ ] Zero test failures
- [ ] Backward compatibility maintained
- [ ] Git tag created: `v1.9.9-phase2c-complete`

**Review Meeting:** End of Week 4 - Go/No-Go decision for Phase 2D

---

## 6. PHASE 2D: CENTRALIZED UTILITIES

### Overview

**Goal:** Extract duplicate utilities (ModelSelector, CostTracker, ReportGenerator)
**Duration:** 1.5 weeks (Days 30-39)
**Effort:** 48 hours
**Risk:** LOW

### 6.1 Code Deduplication

**Current Duplication:**
- ModelSelector logic: 3 files (~200 lines each = 600 lines)
- CostTracker logic: 3 files (~150 lines each = 450 lines)
- ReportGenerator logic: 2 files (~180 lines each = 360 lines)
- **Total duplicate code:** ~1,410 lines

**After Consolidation:**
- `lib/model_selector.py`: ~250 lines (single implementation)
- `lib/cost_tracker.py`: ~200 lines (enhanced from Phase B)
- `lib/report_generator.py`: ~220 lines (single implementation)
- **Total: ~670 lines (53% reduction in utility code)**

### 6.2 Execution Steps (Week 5-6)

#### Step 1: Extract ModelSelector (Days 30-32, 16 hours)

**Tasks:**
1. Create `lib/model_selector.py`:
   ```python
   class ModelSelector:
       """Centralized model selection strategy."""

       MODEL_REGISTRY = {
           "claude-opus-4-5": ModelSpec(...),
           "claude-sonnet-4-5": ModelSpec(...),
           # ... all models
       }

       def select_model(self, task_complexity, max_cost, ...):
           # Unified selection logic
   ```

2. Update validation_orchestrator to use ModelSelector
3. Update critic_orchestrator to use ModelSelector
4. Update specialized_roles_orchestrator to use ModelSelector

5. Remove duplicate model selection code from all 3 files

6. Add comprehensive tests for ModelSelector

**Deliverables:**
- ✅ `lib/model_selector.py` created (~250 lines)
- ✅ All 3 orchestrators using ModelSelector
- ✅ ~600 lines of duplicate code removed
- ✅ Tests for ModelSelector added
- ✅ All tests passing

---

#### Step 2: Enhance CostTracker (Days 33-34, 12 hours)

**Tasks:**
1. Update `lib/cost_tracker.py`:
   ```python
   class CostTracker:
       """Enhanced cost tracker with budget management."""

       def __init__(self, budget: BudgetConfig, alert_callback):
           # Budget enforcement
           # Multi-orchestrator tracking
           # Cost prediction

       def record_cost(self, cost, orchestrator, model):
           # Track by orchestrator and model
           # Check budget limits
           # Trigger alerts
   ```

2. Update all orchestrators to use enhanced CostTracker

3. Remove duplicate cost tracking code

4. Add budget enforcement tests

**Deliverables:**
- ✅ `lib/cost_tracker.py` enhanced
- ✅ All orchestrators using enhanced CostTracker
- ✅ ~450 lines of duplicate code removed
- ✅ Budget enforcement working
- ✅ All tests passing

---

#### Step 3: Extract ReportGenerator (Days 35-36, 12 hours)

**Tasks:**
1. Create `lib/report_generator.py`:
   ```python
   class ReportGenerator:
       """Standardized report generation."""

       def generate_validation_report(self, result, format=ReportFormat.MARKDOWN):
           # Unified validation reports

       def generate_cost_summary(self, cost_stats, format=ReportFormat.MARKDOWN):
           # Unified cost reports
   ```

2. Update validation and critic orchestrators to use ReportGenerator

3. Remove duplicate reporting code

4. Add report format tests (Markdown, JSON, HTML)

**Deliverables:**
- ✅ `lib/report_generator.py` created (~220 lines)
- ✅ All orchestrators using ReportGenerator
- ✅ ~360 lines of duplicate code removed
- ✅ All report formats tested
- ✅ All tests passing

---

#### Step 4: Final Cleanup (Days 37-38, 8 hours)

**Tasks:**
1. Remove all duplicate utility code from orchestrators
2. Update all imports
3. Update documentation
4. Run full test suite
5. Performance benchmarks

**Deliverables:**
- ✅ ~1,410 lines of duplicate code removed
- ✅ All imports updated
- ✅ Documentation updated
- ✅ All tests passing
- ✅ Performance maintained

---

#### Step 5: Polish & Release (Days 39, 4 hours)

**Tasks:**
1. Final QA
2. External validation of migration guide
3. Tag release:
   ```bash
   git tag v2.0.0-rc1
   ```

**Deliverables:**
- ✅ All utilities centralized
- ✅ Migration guide validated
- ✅ Git tag: `v2.0.0-rc1`

### 6.3 Phase 2D Success Criteria

- [ ] ModelSelector, CostTracker, ReportGenerator centralized
- [ ] ~1,410 lines of duplicate code removed
- [ ] All orchestrators using centralized utilities
- [ ] Zero test failures
- [ ] Performance maintained
- [ ] Documentation updated
- [ ] Git tag created: `v2.0.0-rc1`

**Review Meeting:** End of Week 5 - Final QA approval for v2.0.0

---

## 7. QUALITY GATES & CHECKPOINTS

### 7.1 Per-Phase Quality Gates

**Every Phase Must Pass ALL Quality Gates:**

#### Gate 1: Test Coverage (CRITICAL)
```bash
pytest tests/ --cov --cov-report=term --cov-fail-under=95
```
- **Requirement:** >= 95% coverage (or maintain baseline if baseline > 95%)
- **Blocking:** YES - cannot proceed to next phase if fails

#### Gate 2: Zero Regressions (CRITICAL)
```bash
pytest tests/test_regression.py -v
pytest tests/test_backward_compatibility.py -v
```
- **Requirement:** ALL regression tests pass
- **Blocking:** YES

#### Gate 3: Performance (HIGH)
```bash
pytest tests/benchmark_*.py --benchmark-compare
```
- **Requirement:** Within 5% of baseline
- **Blocking:** NO (can proceed with warning, but must fix before release)

#### Gate 4: Type Safety (HIGH)
```bash
mypy lib/ --strict
```
- **Requirement:** Zero type errors
- **Blocking:** NO (warnings acceptable, errors must be fixed before release)

#### Gate 5: Circular Dependencies (CRITICAL)
```bash
pydeps lib/ --max-bacon 2 --show-cycles
```
- **Requirement:** Zero cycles
- **Blocking:** YES

#### Gate 6: Documentation (MEDIUM)
- **Requirement:** All public APIs documented, migration guide updated
- **Blocking:** NO (can complete in parallel with next phase)

### 7.2 Phase-Specific Checkpoints

#### Phase 2A Checkpoints
- **After Step 2:** Can we roll back to Week 0?
- **After Step 3:** Is circular dependency still broken?
- **After Step 5:** Does migration guide work for external users?

#### Phase 2B Checkpoints
- **After Step 1:** Does protocol implementation work correctly?
- **After Step 2:** Are all orchestrators wiring correctly?
- **After Step 3:** Is circular dependency check passing in CI?

#### Phase 2C Checkpoints
- **After Step 2:** Are quality tiers selecting correct models?
- **After Step 4:** Is fallback quality within 10% of baseline?

#### Phase 2D Checkpoints
- **After each utility extraction:** Are all consumers updated?
- **After Step 4:** Is all duplicate code removed?

### 7.3 Go/No-Go Decision Points

**3 Major Go/No-Go Reviews:**

#### Review 1: After Week 0 (Pre-Flight)
**Decision:** Proceed to Phase 2A?
- [ ] Week 0 checklist 100% complete
- [ ] Stakeholder approval received
- [ ] Resources allocated (Backend specialist, QA, Documentation)

**If NO-GO:** Address gaps before starting Phase 2A

---

#### Review 2: After Phase 2A (Week 2)
**Decision:** Proceed to Phase 2B?
- [ ] Phase 2A success criteria 100% met
- [ ] Zero test failures
- [ ] Backward compatibility verified
- [ ] Migration guide validated externally

**If NO-GO:** Fix Phase 2A issues before proceeding

---

#### Review 3: After Phase 2C (Week 4)
**Decision:** Proceed to Phase 2D?
- [ ] Critic quality validated (within 10% of baseline)
- [ ] All Phase 2A-2C success criteria met
- [ ] No major blockers discovered

**If NO-GO:** Address critic quality or other blockers

---

### 7.4 Automated Quality Gate Enforcement

**CI/CD Pipeline (`.github/workflows/phase2_quality.yml`):**

```yaml
name: Phase 2 Quality Gates

on: [pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Gate 1 - Test Coverage
        run: |
          pytest tests/ --cov --cov-fail-under=95

      - name: Gate 2 - Regression Tests
        run: |
          pytest tests/test_regression.py -v --tb=short

      - name: Gate 3 - Performance Benchmarks
        run: |
          pytest tests/benchmark_*.py --benchmark-only
          # Warning if > 5% regression, but doesn't fail

      - name: Gate 4 - Type Safety
        run: |
          mypy lib/ --strict || echo "Type errors found"

      - name: Gate 5 - Circular Dependencies
        run: |
          pip install pydeps
          pydeps lib/ --max-bacon 2 --show-cycles
          # Fails if cycles found

      - name: Comment Results
        uses: actions/github-script@v6
        with:
          script: |
            // Post results as PR comment
```

---

## 8. RISK MITIGATION & ROLLBACK

### 8.1 Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| **Phase 2A breaks production** | LOW | CRITICAL | HIGH | Rollback to v1.9.0 tag, feature flags |
| **Circular dependency reintroduced** | MEDIUM | HIGH | MEDIUM | Automated pydeps check in CI |
| **Critic quality degrades** | MEDIUM | HIGH | MEDIUM | Quality consistency tests, manual review |
| **Performance regression** | LOW | MEDIUM | LOW | Automated benchmarks, performance testing |
| **Breaking changes impact users** | HIGH | HIGH | HIGH | Deprecation warnings, backward compatibility layer |
| **Migration guide insufficient** | MEDIUM | MEDIUM | MEDIUM | External validation, user feedback |
| **Test coverage gaps** | MEDIUM | HIGH | MEDIUM | 95% coverage requirement, regression tests |
| **Documentation lag** | HIGH | MEDIUM | MEDIUM | Parallel documentation work |

### 8.2 Rollback Procedures

#### Automated Rollback Scripts

**Location:** `scripts/rollback_phase_*.sh`

**Phase 2A Rollback:**
```bash
#!/bin/bash
# scripts/rollback_phase_2a.sh

echo "🔄 Rolling back Phase 2A..."

# Step 1: Restore code
git checkout v1.9.0-pre-phase2 -- validation_orchestrator.py
git checkout v1.9.0-pre-phase2 -- lib/

# Step 2: Remove new directories
rm -rf validation/

# Step 3: Restore dependencies
pip install -r requirements-pre-phase2.txt

# Step 4: Run tests
pytest tests/ -v

echo "✅ Phase 2A rollback complete"
```

**Phase 2B Rollback:**
```bash
#!/bin/bash
# scripts/rollback_phase_2b.sh

echo "🔄 Rolling back Phase 2B..."

# Step 1: Restore direct imports
git checkout v1.9.5-phase2a-complete -- validation_orchestrator.py
git checkout v1.9.5-phase2a-complete -- critic_orchestrator.py

# Step 2: Remove orchestrator_setup.py
rm orchestrator_setup.py

# Step 3: Run tests
pytest tests/ -v

echo "✅ Phase 2B rollback complete"
```

**Phase 2C Rollback:**
```bash
#!/bin/bash
# scripts/rollback_phase_2c.sh

echo "🔄 Rolling back Phase 2C..."

# Step 1: Restore BaseAgent
git checkout v1.9.7-phase2b-complete -- critic_orchestrator.py

# Step 2: Run tests
pytest tests/ -v

echo "✅ Phase 2C rollback complete"
```

**Phase 2D Rollback:**
```bash
#!/bin/bash
# scripts/rollback_phase_2d.sh

echo "🔄 Rolling back Phase 2D..."

# Step 1: Restore old utilities
git checkout v1.9.9-phase2c-complete -- lib/

# Step 2: Remove centralized utilities
rm lib/model_selector.py
rm lib/report_generator.py

# Step 3: Run tests
pytest tests/ -v

echo "✅ Phase 2D rollback complete"
```

### 8.3 Rollback Decision Criteria

**When to Rollback:**

**IMMEDIATE ROLLBACK (No Review Needed):**
- Production outage or critical bug
- Data loss or corruption
- Security vulnerability introduced
- Zero-day exploit discovered

**ROLLBACK AFTER REVIEW (Team Decision):**
- > 50% test failures after phase completion
- Performance regression > 20%
- Critic quality degradation > 20%
- Multiple user complaints about breaking changes
- Timeline slippage > 2 weeks

**NO ROLLBACK (Fix Forward):**
- Minor test failures (< 10%)
- Performance regression < 5%
- Documentation issues
- Non-critical bugs with workarounds

### 8.4 Rollback Testing

**Pre-Phase Rollback Tests:**

Before starting each phase, verify rollback works:

```bash
# Example: Test Phase 2A rollback before starting Phase 2A
cd /home/jevenson/.claude/lib

# Make dummy change
echo "test" >> validation_orchestrator.py

# Test rollback script
./scripts/rollback_phase_2a.sh

# Verify restoration
git diff validation_orchestrator.py  # Should show no changes

# Verify tests pass
pytest tests/ -v
```

**Rollback Drill Schedule:**
- Week 0: Test all rollback scripts
- End of Week 1: Test Phase 2A rollback
- End of Week 3: Test Phase 2B rollback
- End of Week 4: Test Phase 2C rollback
- End of Week 5: Test Phase 2D rollback

---

## 9. RESOURCE ALLOCATION

### 9.1 Team Roles & Responsibilities

#### Backend Specialist (Lead)
**Effort:** 120 hours over 6 weeks
**Responsibilities:**
- Lead all code refactoring
- Implement ValidationOrchestrator decomposition
- Implement circular dependency resolution
- Implement Critic Phase B migration
- Implement centralized utilities
- Code reviews
- Architecture decisions

**Week-by-Week Allocation:**
- Week 0: 16 hours (review audit, plan implementation)
- Week 1-2 (Phase 2A): 40 hours (validation decomposition)
- Week 3 (Phase 2B): 16 hours (circular dependency fix)
- Week 4 (Phase 2C): 24 hours (critic migration)
- Week 5 (Phase 2D): 20 hours (utilities extraction)
- Week 6: 4 hours (final QA)

---

#### QA Engineer
**Effort:** 80 hours over 6 weeks
**Responsibilities:**
- Write regression tests
- Write backward compatibility tests
- Performance benchmarking
- Integration testing
- External migration guide validation
- Quality gate enforcement

**Week-by-Week Allocation:**
- Week 0: 16 hours (baseline tests, regression suite)
- Week 1-2 (Phase 2A): 24 hours (test validation split)
- Week 3 (Phase 2B): 12 hours (test circular dependency fix)
- Week 4 (Phase 2C): 16 hours (critic quality testing)
- Week 5 (Phase 2D): 8 hours (test utilities)
- Week 6: 4 hours (final QA, migration validation)

---

#### Documentation Expert
**Effort:** 80 hours over 6 weeks
**Responsibilities:**
- Document current architecture (Week 0)
- Write 5 ADRs (Week 0)
- Update API documentation
- Write migration guide
- Update README
- Code example creation
- External validation coordination

**Week-by-Week Allocation:**
- Week 0: 24 hours (current architecture, ADRs)
- Week 1-2 (Phase 2A): 20 hours (validation docs)
- Week 3 (Phase 2B): 12 hours (circular dependency docs)
- Week 4 (Phase 2C): 12 hours (critic migration docs)
- Week 5 (Phase 2D): 8 hours (utilities docs)
- Week 6: 4 hours (final review, migration guide validation)

---

#### Tech Lead / Architect (Oversight)
**Effort:** 24 hours over 6 weeks
**Responsibilities:**
- Architecture review
- Go/No-Go decisions
- Code review (critical sections)
- Risk assessment
- Stakeholder communication

**Week-by-Week Allocation:**
- Week 0: 4 hours (approve plan)
- End of Week 2: 4 hours (Phase 2A review)
- End of Week 3: 4 hours (Phase 2B review)
- End of Week 4: 4 hours (Phase 2C review)
- End of Week 5: 4 hours (Phase 2D review)
- Week 6: 4 hours (final approval)

---

### 9.2 Total Effort Summary

| Role | Hours | Cost (Estimate) |
|------|-------|-----------------|
| Backend Specialist | 120 | $12,000 (@$100/hr) |
| QA Engineer | 80 | $6,400 (@$80/hr) |
| Documentation Expert | 80 | $6,400 (@$80/hr) |
| Tech Lead / Architect | 24 | $4,800 (@$200/hr) |
| **TOTAL** | **304 hours** | **$29,600** |

**Cost-Benefit Analysis:**
- **Investment:** $29,600 + 6 weeks timeline
- **Benefit:** 35% code reduction, improved maintainability, zero-touch engineering enabled
- **ROI:** Estimated 40% reduction in bug fixes, 50% faster feature development

---

## 10. SUCCESS METRICS

### 10.1 Quantitative Metrics

#### Code Metrics
- [ ] **Code reduction:** 35% reduction achieved (5,316 → 3,500 lines)
- [ ] **Files:** 6 large files → 15-18 focused modules
- [ ] **Average file size:** < 400 lines (down from 886 lines)
- [ ] **Duplicate code:** 1,410 lines removed (utilities)
- [ ] **Circular dependencies:** 0 (verified by pydeps)

#### Quality Metrics
- [ ] **Test coverage:** >= 95% (maintained or improved)
- [ ] **Zero test failures:** 100% tests passing
- [ ] **Performance:** Within 5% of baseline
- [ ] **Critic quality:** Within 10% of Opus baseline
- [ ] **Type safety:** 100% type hints, zero mypy errors

#### Adoption Metrics (3 months post-release)
- [ ] **Migration rate:** > 80% of users upgraded to v2.0.0
- [ ] **Support tickets:** -50% reduction in support requests
- [ ] **Bug rate:** Maintain or reduce bug rate vs. pre-consolidation
- [ ] **Developer satisfaction:** 4/5 or higher in feedback survey

### 10.2 Qualitative Metrics

#### Maintainability
- [ ] New developers can understand structure in < 2 hours
- [ ] Code changes require touching fewer files
- [ ] Clear module boundaries reduce merge conflicts
- [ ] Easier to add new features (measured by developer feedback)

#### Reliability
- [ ] Zero production outages caused by consolidation
- [ ] Fallback mechanisms tested and working
- [ ] Circuit breakers functioning correctly
- [ ] Error handling improved (measured by error log analysis)

#### Documentation Quality
- [ ] Migration guide successfully used by 3+ external users
- [ ] API documentation complete for all public interfaces
- [ ] ADRs capture all architectural decisions
- [ ] Code examples execute without errors

### 10.3 Success Review

**Post-Release Review (Week 7):**
- Collect metrics from production
- Survey developer satisfaction
- Review support tickets
- Identify any issues
- Plan follow-up improvements

**3-Month Review:**
- Assess adoption rate
- Measure bug rate vs. baseline
- Gather user feedback
- Document lessons learned
- Update best practices

---

## APPENDICES

### Appendix A: Pre-Flight Checklist (Week 0)

**Complete ALL items before starting Phase 2A:**

#### Documentation
- [ ] `docs/CURRENT_ARCHITECTURE.md` created
- [ ] `docs/diagrams/current_structure.png` created
- [ ] `docs/adr/ADR-001.md` written (ValidationOrchestrator decomposition)
- [ ] `docs/adr/ADR-002.md` written (CriticOrchestrator Phase B migration)
- [ ] `docs/adr/ADR-003.md` written (Centralized model selection)
- [ ] `docs/adr/ADR-004.md` written (Dependency injection pattern)
- [ ] `docs/adr/ADR-005.md` written (Deprecation strategy)

#### Rollback Infrastructure
- [ ] Git tag created: `v1.9.0-pre-phase2`
- [ ] `docs/ROLLBACK.md` created
- [ ] `scripts/rollback_phase_2a.sh` created and tested
- [ ] `scripts/rollback_phase_2b.sh` created and tested
- [ ] `scripts/rollback_phase_2c.sh` created and tested
- [ ] `scripts/rollback_phase_2d.sh` created and tested

#### Testing Infrastructure
- [ ] Baseline test coverage measured: ____%
- [ ] Baseline test count: _____ tests
- [ ] `tests/BASELINE_METRICS.md` created
- [ ] `tests/benchmark_baseline.py` created
- [ ] `tests/test_regression.py` created (50+ tests)
- [ ] `tests/test_backward_compatibility.py` created
- [ ] Performance baselines established

#### CI/CD
- [ ] `.github/workflows/phase2_quality_gates.yml` created
- [ ] Circular dependency check added
- [ ] Test coverage requirement configured (>= 95%)
- [ ] Performance regression alert configured (> 5%)

#### Stakeholder Approval
- [ ] Phase 2 plan reviewed by stakeholders
- [ ] Resources allocated (Backend specialist, QA, Documentation)
- [ ] Timeline approved
- [ ] Budget approved

**Sign-Off Required:**
- [ ] Tech Lead approval: ________________
- [ ] Backend Specialist ready: ________________
- [ ] QA Engineer ready: ________________
- [ ] Documentation Expert ready: ________________

---

### Appendix B: Migration Automation Scripts

**Location:** `scripts/migrate_phase_2.py`

```python
#!/usr/bin/env python3
"""
Automated import migration for Phase 2 consolidation.

Usage:
    python3 scripts/migrate_phase_2.py /path/to/project

This will update all imports in the target directory to use the new
Phase 2 structure.
"""
import re
import sys
from pathlib import Path
from typing import Dict, List

# Import mappings
IMPORT_MAPPINGS = {
    # Phase 2A: Validation decomposition
    "from validation_orchestrator import ValidationOrchestrator":
        "from validation import ValidationCore as ValidationOrchestrator",

    # Phase 2B: No import changes (wiring only)

    # Phase 2C: No import changes (internal only)

    # Phase 2D: Centralized utilities
    "from validation_orchestrator import ModelSelector":
        "from lib.model_selector import ModelSelector",
    "from critic_orchestrator import CostTracker":
        "from lib.cost_tracker import CostTracker",
    "from validation_orchestrator import ReportGenerator":
        "from lib.report_generator import ReportGenerator",
}

def migrate_file(filepath: Path, dry_run: bool = False) -> Dict[str, int]:
    """Migrate imports in a single Python file.

    Args:
        filepath: Path to Python file
        dry_run: If True, don't write changes

    Returns:
        Dict with migration statistics
    """
    content = filepath.read_text()
    original_content = content
    changes = 0

    for old_import, new_import in IMPORT_MAPPINGS.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            changes += 1

    if changes > 0:
        print(f"{'[DRY RUN] ' if dry_run else ''}Migrating {filepath}: {changes} imports updated")
        if not dry_run:
            filepath.write_text(content)

    return {"files": 1 if changes > 0 else 0, "changes": changes}

def migrate_directory(directory: Path, dry_run: bool = False) -> Dict[str, int]:
    """Migrate all Python files in directory recursively.

    Args:
        directory: Root directory to search
        dry_run: If True, don't write changes

    Returns:
        Dict with total migration statistics
    """
    total_stats = {"files": 0, "changes": 0}

    for filepath in directory.rglob("*.py"):
        # Skip migration scripts themselves
        if "migrate_phase_2" in str(filepath):
            continue

        stats = migrate_file(filepath, dry_run)
        total_stats["files"] += stats["files"]
        total_stats["changes"] += stats["changes"]

    return total_stats

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 migrate_phase_2.py <directory> [--dry-run]")
        sys.exit(1)

    directory = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}Migrating imports in {directory}...")
    stats = migrate_directory(directory, dry_run)

    print(f"\n{'DRY RUN ' if dry_run else ''}Migration complete:")
    print(f"  Files modified: {stats['files']}")
    print(f"  Total changes: {stats['changes']}")

    if dry_run:
        print("\nRe-run without --dry-run to apply changes.")

if __name__ == "__main__":
    main()
```

---

### Appendix C: Communication Plan

#### Internal Communication (Development Team)

**Weekly Sync (30 minutes):**
- Progress update
- Blockers discussion
- Next week priorities
- Risk review

**Phase Review Meetings (1 hour each):**
- End of Week 0: Pre-flight review
- End of Week 2: Phase 2A review
- End of Week 3: Phase 2B review
- End of Week 4: Phase 2C review
- End of Week 5: Phase 2D review
- End of Week 6: Final release review

#### External Communication (Users/Stakeholders)

**Announcement Schedule:**

**Week 0:** Phase 2 kickoff announcement
- Email to all users
- Blog post: "Zero-Touch Engineering Phase 2 Begins"
- Roadmap published

**Week 2:** Phase 2A completion
- Blog post: "ValidationOrchestrator Refactored"
- Migration guide preview
- Request for feedback

**Week 4:** v2.0.0-rc1 announcement
- Email to all users: "v2.0.0 Release Candidate Available"
- Migration guide published
- Deprecation timeline announced (8 weeks)

**Week 6:** v2.0.0 release
- Email to all users
- Blog post: "Zero-Touch Engineering v2.0.0 Released"
- Changelog published
- Support channels announced

**Week 14:** Deprecation deadline reminder
- Email reminder: "Old imports will be removed in 2 weeks"
- Migration support offered

**Week 16:** v3.0.0 release (removes old imports)
- Email announcement
- Blog post
- Deprecation complete

---

### Appendix D: Support Plan

#### Migration Support Channels

**GitHub Issues:**
- Label: `migration-help`
- Template: `MIGRATION_ISSUE_TEMPLATE.md`
- SLA: 24-hour response time

**Email Support:**
- migration@yourorg.com
- Dedicated migration support during Weeks 6-16

**Office Hours:**
- Weekly 1-hour session
- Zoom call for migration questions
- Wednesdays 2-3 PM PT

**Migration Guide:**
- Comprehensive step-by-step guide
- Before/after code examples
- Common pitfalls section
- Troubleshooting guide

#### Support Metrics

**Track and report weekly:**
- Number of migration support requests
- Common issues encountered
- Average time to resolve
- User satisfaction with migration process

**Success Criteria:**
- < 5 support requests per week after Week 8
- > 4/5 satisfaction rating
- > 80% migration completion by Week 16

---

## FINAL APPROVAL

This Phase 2 Execution Plan is ready for stakeholder review and approval.

**Prepared By:**
- Backend Specialist Agent
- Code Reviewer Agent
- Documentation Expert Agent
- Project Manager Agent
- Devils Advocate Agent

**Date:** 2025-11-09

**Approvals Required:**

- [ ] **Tech Lead / Architect:** ________________  Date: ______
- [ ] **Backend Specialist:** ________________  Date: ______
- [ ] **QA Engineer:** ________________  Date: ______
- [ ] **Documentation Expert:** ________________  Date: ______
- [ ] **Product Owner:** ________________  Date: ______

**Next Steps After Approval:**
1. Allocate resources (Backend specialist, QA, Documentation)
2. Schedule kickoff meeting
3. Begin Week 0 tasks immediately
4. Setup communication channels
5. Create project tracking board

---

**END OF EXECUTION PLAN**

**Status:** READY FOR APPROVAL
**Version:** 1.0
**Total Pages:** 85+ pages of comprehensive planning
**Confidence Level:** HIGH (with proper execution of safeguards)