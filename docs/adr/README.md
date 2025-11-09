# Architecture Decision Records (ADRs)

## Overview

This directory contains Architecture Decision Records (ADRs) documenting significant architectural decisions made during the Phase 2 consolidation of the multi-agent orchestration library.

ADRs capture the **context, decision, rationale, and consequences** of important choices, preserving institutional knowledge for future developers.

---

## Active ADRs

### [ADR-001: Decompose ValidationOrchestrator God Class](./ADR-001-decompose-validation-orchestrator.md)
**Status:** Accepted | **Date:** 2025-11-09

**Problem:** `validation_orchestrator.py` grew to 2,142 lines with 4 distinct responsibilities, violating Single Responsibility Principle.

**Decision:** Split into 4 focused modules:
- `interfaces.py` - Type contracts (protocols, enums)
- `core.py` - Core orchestration logic
- `critic_integration.py` - Critic validation integration
- `result_aggregator.py` - Consensus building

**Impact:** Better maintainability (400 lines/file vs 2,142), clearer boundaries, easier testing.

**Key Trade-offs:** More files to navigate vs improved modularity.

---

### [ADR-002: Migrate CriticOrchestrator to Phase B Architecture](./ADR-002-migrate-critic-orchestrator-phase-b.md)
**Status:** Accepted | **Date:** 2025-11-09

**Problem:** `CriticOrchestrator` remains on Phase A architecture (legacy `BaseAgent`) while rest of system uses Phase B (`ResilientBaseAgent`), creating architectural inconsistency and missing fallback resilience.

**Decision:** Migrate to `ResilientBaseAgent` with quality-tiered fallback:
- **Tier 1:** GPT-4 Turbo (comparable quality)
- **Tier 2:** Claude Sonnet (good quality, faster)
- **Tier 3:** GPT-3.5 Turbo (emergency fallback)

**Impact:** 99.9% uptime (vs 95%), cost visibility, consistent error handling across system.

**Key Trade-offs:** Quality variance across models vs improved reliability.

---

### [ADR-003: Centralize Model Selection Logic](./ADR-003-centralize-model-selection.md)
**Status:** Accepted | **Date:** 2025-11-09

**Problem:** Model selection logic duplicated across 3 orchestrators (~600 lines), creating inconsistency and maintenance burden.

**Decision:** Create centralized `ModelSelector` utility with:
- Tier-based abstraction (premium/standard/economy)
- Context-driven selection (task type, complexity, budget, latency)
- Unified configuration

**Impact:** 50% code reduction (600 → 300 lines), consistent model selection, easy A/B testing.

**Key Trade-offs:** All orchestrators depend on ModelSelector vs reduced duplication.

---

### [ADR-004: Use Protocol-Based Dependency Injection](./ADR-004-protocol-based-dependency-injection.md)
**Status:** Accepted | **Date:** 2025-11-09

**Problem:** Circular dependency between `ValidationOrchestrator` and `CriticOrchestrator` causes import errors.

**Decision:** Use Python Protocols (PEP 544) with runtime dependency injection:
- Define `ValidatorProtocol` and `CriticProtocol` interfaces
- Implement setter-based dependency injection
- Use factory pattern to wire dependencies

**Impact:** Breaks circular import, maintains type safety, improves testability.

**Key Trade-offs:** Requires runtime wiring vs clean import graph.

---

### [ADR-005: 8-Week Deprecation Strategy for Import Path Changes](./ADR-005-eight-week-deprecation-strategy.md)
**Status:** Accepted | **Date:** 2025-11-09

**Problem:** Phase 2 consolidation introduces breaking import path changes affecting all consumers.

**Decision:** Implement 8-week gradual deprecation:
- **Weeks 0-2:** Soft launch with `DeprecationWarning` and backward-compatible shims
- **Weeks 3-6:** Active migration support with automated script
- **Weeks 7-8:** Final warnings with `FutureWarning`
- **Week 9:** Remove old code in v2.1.0

**Impact:** Smooth user experience, reduced support burden, clean codebase after 8 weeks.

**Key Trade-offs:** Maintain two code paths temporarily vs respectful user migration.

---

## ADR Index by Topic

### Code Organization
- [ADR-001: Decompose ValidationOrchestrator](./ADR-001-decompose-validation-orchestrator.md)

### Reliability & Resilience
- [ADR-002: Migrate CriticOrchestrator to Phase B](./ADR-002-migrate-critic-orchestrator-phase-b.md)

### Code Quality
- [ADR-003: Centralize Model Selection Logic](./ADR-003-centralize-model-selection.md)
- [ADR-004: Use Protocol-Based Dependency Injection](./ADR-004-protocol-based-dependency-injection.md)

### Migration & Compatibility
- [ADR-005: 8-Week Deprecation Strategy](./ADR-005-eight-week-deprecation-strategy.md)

---

## ADR Template

When creating new ADRs, use this structure:

```markdown
# ADR-XXX: Title

**Status:** Proposed | Accepted | Deprecated | Superseded
**Date:** YYYY-MM-DD
**Deciders:** List of decision makers
**Tags:** #tag1 #tag2

---

## Context
What is the issue we're facing? What constraints exist?

## Decision
What did we decide to do?

## Rationale
Why did we make this decision?

## Consequences
What are the positive and negative consequences?

## Alternatives Considered
What other options did we evaluate and why were they rejected?

## Implementation Plan
How will this be implemented?

## Testing Strategy
How will we validate this decision?

## References
Related documents, patterns, or research

## Revision History
Track changes to this ADR over time
```

---

## How to Use ADRs

### When to Create an ADR

Create an ADR when:
- Making significant architectural changes
- Choosing between multiple viable approaches
- Establishing patterns others should follow
- Making decisions with long-term consequences
- Rejecting a popular approach (document why)

### When NOT to Create an ADR

Skip ADRs for:
- Trivial implementation details
- Obvious bug fixes
- Routine refactoring
- Temporary workarounds

### ADR Lifecycle

1. **Proposed** - Decision under consideration
2. **Accepted** - Decision approved and being implemented
3. **Deprecated** - Decision no longer recommended
4. **Superseded** - Decision replaced by newer ADR (link to replacement)

### Updating ADRs

ADRs should be **immutable** once accepted. If a decision changes:
1. Don't edit the original ADR
2. Create a new ADR that supersedes it
3. Update the status of the old ADR to "Superseded by ADR-XXX"
4. Link between old and new ADRs

**Exception:** Fix typos, clarify wording, or add implementation notes without changing the core decision.

---

## Phase 2 Consolidation Context

These ADRs document decisions made during **Phase 2: Consolidation & Standardization** of the multi-agent orchestration library.

**Goals:**
- Reduce code duplication (~2,000 lines)
- Standardize architecture patterns
- Improve maintainability
- Enable easier testing

**Scope:**
- ValidationOrchestrator decomposition
- CriticOrchestrator Phase B migration
- Model selection centralization
- Dependency injection patterns
- Deprecation strategy

**Timeline:** November 2025 (8-week execution, 8-week deprecation)

For full context, see:
- [Phase 2 Planning Document](../PHASE2_CONSOLIDATION.md)
- [Multi-Agent Framework README](../../README.md)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)

---

## Related Documentation

- **[Multi-Agent Framework](../../README.md)** - Overall library documentation
- **[Deployment Guide](../DEPLOYMENT_GUIDE.md)** - Production deployment patterns
- **[Phase 2 Plan](../PHASE2_CONSOLIDATION.md)** - Consolidation project plan
- **[Migration Guide](../MIGRATION_GUIDE_V2.md)** - How to migrate to v2.0

---

## Questions or Feedback

If you have questions about these ADRs or want to propose changes:

1. **Review Process:** Open an issue with tag `adr-review`
2. **New ADR:** Submit PR with new ADR file
3. **Discussion:** Use issue tracker for architectural discussions

**Contact:** jevenson@example.com

---

## Statistics

- **Total ADRs:** 5
- **Accepted:** 5
- **Proposed:** 0
- **Deprecated:** 0
- **Superseded:** 0
- **Total Lines of Documentation:** ~7,500
- **Average ADR Length:** ~1,500 lines

---

**Last Updated:** 2025-11-09
**Maintained By:** Documentation Expert
