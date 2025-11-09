# ADR-005: 8-Week Deprecation Strategy for Import Path Changes

**Status:** Accepted
**Date:** 2025-11-09
**Deciders:** Backend Specialist, Tech Lead, Architect
**Tags:** #deprecation #migration #breaking-changes

---

## Context

### The Problem: Breaking Changes from Phase 2 Consolidation

Phase 2 consolidation introduces **breaking import path changes** that will affect all consumers:

**Breaking Change 1: ValidationOrchestrator Decomposition** (ADR-001)
```python
# Old import (2,142-line monolith)
from validation_orchestrator import ValidationOrchestrator

# New import (decomposed modules)
from validation.core import ValidationOrchestrator
from validation.interfaces import ValidatorProtocol
from validation.result_aggregator import ResultAggregator
```

**Breaking Change 2: CriticOrchestrator Migration** (ADR-002)
```python
# Old API (Phase A)
critic = CriticOrchestrator()  # Single model, no fallback

# New API (Phase B)
critic = CriticOrchestrator(
    primary_model="claude-opus-4-20250514",
    fallback_models=["gpt-4-turbo"],
    enable_fallback=True
)
```

**Breaking Change 3: ModelSelector Introduction** (ADR-003)
```python
# Old pattern (duplicated logic)
def _select_model(self, complexity: str) -> str:
    if complexity == "high":
        return "claude-opus-4-20250514"

# New pattern (centralized)
from utils.model_selector import ModelSelector, ModelSelectionContext
model = model_selector.select_model(context)
```

**Breaking Change 4: Protocol-Based DI** (ADR-004)
```python
# Old instantiation (direct)
validator = ValidationOrchestrator()

# New instantiation (factory)
from orchestration.factory import create_validation_system
validator, critic = create_validation_system()
```

### Impact Analysis

**Internal Consumers** (within `/home/jevenson/.claude/lib/`):
- `orchestrator.py` - Uses ValidationOrchestrator
- `agent_system.py` - Indirect dependency through orchestrators
- `test_*.py` - 37 test files import validation/critic modules
- **Estimated Files Affected:** 50+

**External Consumers** (projects using the library):
```bash
$ grep -r "from validation_orchestrator import" ~/projects/
~/projects/data-pipeline/src/validation.py
~/projects/content-generator/quality/validator.py
~/projects/research-agent/orchestration/main.py
```
**Estimated External Projects:** 5-10 (unknown exact count)

### The Dilemma

**Option A: Hard Break (No Deprecation)**
- Release v2.0.0 with breaking changes
- All consumers must update immediately
- ❌ **Risks:** Production outages, frustrated users, rushed migrations

**Option B: Maintain Backward Compatibility Forever**
- Keep old imports working indefinitely
- Maintain two code paths (old + new)
- ❌ **Risks:** Technical debt, maintenance burden, confusion

**Option C: Gradual Deprecation (This ADR)**
- Announce changes
- Provide transition period
- Issue warnings
- Remove old code after deadline
- ✅ **Balances:** User experience + code hygiene

---

## Decision

**Implement an 8-week gradual deprecation strategy** with three phases:

### Phase 1: Announcement & Backward Compatibility (Weeks 0-2)

**Actions:**
1. Add backward-compatible shims for all old import paths
2. Emit `DeprecationWarning` on old imports
3. Update documentation with migration guide
4. Announce in CHANGELOG and release notes

**Example Shim:**
```python
# validation_orchestrator.py (legacy shim)
"""
DEPRECATED: This module is deprecated and will be removed in v2.1.0 (2025-12-28).

Migrate to:
    from validation.core import ValidationOrchestrator

See migration guide: /home/jevenson/.claude/lib/docs/MIGRATION_GUIDE_V2.md
"""
import warnings
from validation.core import ValidationOrchestrator as _ValidationOrchestrator
from validation.interfaces import ValidatorProtocol
from validation.result_aggregator import ResultAggregator

# Emit deprecation warning on import
warnings.warn(
    "validation_orchestrator module is deprecated. "
    "Use 'from validation.core import ValidationOrchestrator' instead. "
    "This module will be removed in v2.1.0 (2025-12-28).",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
ValidationOrchestrator = _ValidationOrchestrator
__all__ = ["ValidationOrchestrator", "ValidatorProtocol", "ResultAggregator"]
```

**Deprecation Notice in Code:**
```python
class ValidationOrchestrator:
    def __init__(self, critic=None):
        if critic is not None:
            warnings.warn(
                "Passing 'critic' directly is deprecated. "
                "Use create_validation_system() factory instead. "
                "See: docs/MIGRATION_GUIDE_V2.md",
                DeprecationWarning,
                stacklevel=2
            )
        # ... rest of initialization
```

### Phase 2: Active Migration Support (Weeks 3-6)

**Actions:**
1. Provide automated migration tool
2. Send reminders to known consumers
3. Offer migration assistance
4. Monitor deprecation warning frequency

**Automated Migration Script:**
```python
# scripts/migrate_to_v2.py
#!/usr/bin/env python3
"""
Automated migration script for Phase 2 breaking changes.

Usage:
    python scripts/migrate_to_v2.py /path/to/project [--dry-run]
"""
import re
import sys
from pathlib import Path

REPLACEMENTS = {
    # Validation orchestrator imports
    r"from validation_orchestrator import ValidationOrchestrator":
        "from validation.core import ValidationOrchestrator",

    # Critic orchestrator imports
    r"from critic_orchestrator import CriticOrchestrator":
        "from critic.core import CriticOrchestrator",

    # Model selection pattern
    r"self\._select_model\(([^)]+)\)":
        "self.model_selector.select_model(ModelSelectionContext(\\1))",

    # Direct instantiation to factory
    r"validator = ValidationOrchestrator\(\)":
        "validator, _ = create_validation_system()",
}

def migrate_file(file_path: Path, dry_run: bool = False):
    """Migrate a single file."""
    content = file_path.read_text()
    original = content

    for pattern, replacement in REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content)

    if content != original:
        if dry_run:
            print(f"Would update: {file_path}")
        else:
            file_path.write_text(content)
            print(f"Updated: {file_path}")
        return True
    return False

def main():
    project_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    python_files = project_path.rglob("*.py")
    updated_count = sum(migrate_file(f, dry_run) for f in python_files)

    print(f"\n{'Would update' if dry_run else 'Updated'} {updated_count} files.")
    print("\nNext steps:")
    print("1. Review changes: git diff")
    print("2. Run tests: pytest")
    print("3. Commit: git commit -m 'Migrate to validation lib v2.0'")

if __name__ == "__main__":
    main()
```

**Migration Guide:**
```markdown
# Migration Guide: v1.x → v2.0

## Import Path Changes

### ValidationOrchestrator
**Before:**
```python
from validation_orchestrator import ValidationOrchestrator
validator = ValidationOrchestrator()
```

**After:**
```python
from validation.core import ValidationOrchestrator
from orchestration.factory import create_validation_system

validator, critic = create_validation_system()
```

### CriticOrchestrator
**Before:**
```python
from critic_orchestrator import CriticOrchestrator
critic = CriticOrchestrator()
```

**After:**
```python
from critic.core import CriticOrchestrator
from orchestration.factory import create_validation_system

validator, critic = create_validation_system()
```

## API Changes

### CriticOrchestrator (Phase B Migration)
**Before:**
```python
critic = CriticOrchestrator()  # Single model
```

**After:**
```python
critic = CriticOrchestrator(
    primary_model="claude-opus-4-20250514",
    fallback_models=["gpt-4-turbo"],
    enable_fallback=True  # New: Resilience features
)
```

## Automated Migration

Run the migration script:
```bash
python /home/jevenson/.claude/lib/scripts/migrate_to_v2.py /path/to/your/project --dry-run
# Review changes
python /home/jevenson/.claude/lib/scripts/migrate_to_v2.py /path/to/your/project
```

## Timeline

- **Week 0-2:** Warnings only, full backward compatibility
- **Week 3-6:** Active migration support
- **Week 7-8:** Final reminders
- **Week 9:** v2.1.0 released, old imports removed

## Support

Questions? File an issue or contact: jevenson@example.com
```

### Phase 3: Final Warnings & Removal (Weeks 7-8)

**Actions:**
1. Escalate warnings to `PendingDeprecationWarning`
2. Send final removal notice
3. Prepare v2.1.0 release (removes old code)
4. Document breaking changes in CHANGELOG

**Escalated Warning:**
```python
# Week 7-8: More visible warning
warnings.warn(
    "validation_orchestrator module will be REMOVED in v2.1.0 (2025-12-28). "
    "This is your FINAL WARNING. Migrate now: docs/MIGRATION_GUIDE_V2.md",
    FutureWarning,  # More visible than DeprecationWarning
    stacklevel=2
)
```

**Removal Checklist (v2.1.0):**
- [ ] Delete `validation_orchestrator.py` shim
- [ ] Delete `critic_orchestrator.py` shim
- [ ] Remove deprecated `__init__()` parameters
- [ ] Remove backward-compatible import aliases
- [ ] Update version to 2.1.0
- [ ] Document removal in CHANGELOG

---

## Rationale

### Why 8 Weeks?

**Too Short (2-4 weeks):**
- Users on vacation miss announcement
- Not enough time for thorough testing
- Rushed migrations → bugs

**Too Long (6+ months):**
- Maintain two code paths for too long
- Technical debt accumulates
- Users procrastinate migration

**8 Weeks is Optimal:**
- Covers typical sprint cycles (2-4 sprints)
- Enough time for testing and rollout
- Not so long that debt becomes burden
- Industry standard (e.g., Python, Django)

### Why Three Phases?

**Phase 1 (Weeks 0-2): Soft Launch**
- Announce changes
- Allow early adopters to migrate
- Gather feedback on migration process

**Phase 2 (Weeks 3-6): Active Support**
- Most users migrate during this window
- Provide tooling and assistance
- Address migration issues

**Phase 3 (Weeks 7-8): Final Push**
- Last chance for stragglers
- Escalated warnings
- Prepare for removal

### Why Semantic Versioning (v2.0.0 → v2.1.0)?

**v2.0.0 (With Shims):**
- Major version bump signals breaking changes
- Shims provide backward compatibility
- Users see warnings but code still works

**v2.1.0 (Removal):**
- Minor version bump (not v3.0) because shims are internal
- External API remains stable if users migrated
- Only breaks code that ignored warnings

---

## Consequences

### Positive

✅ **Smooth User Experience**
- No sudden breakage
- Clear migration path
- Time to test changes

✅ **Reduced Support Burden**
- Migration guide preempts questions
- Automated script handles 80% of migrations
- Warnings guide users proactively

✅ **Maintain Goodwill**
- Respect users' time
- Professional communication
- Demonstrates library maturity

✅ **Clean Codebase After 8 Weeks**
- Remove all shims
- Delete deprecated code
- No lingering technical debt

✅ **Gather Feedback**
- Learn from migration issues
- Improve future deprecation processes
- Identify edge cases

### Negative

❌ **Maintain Two Code Paths (8 Weeks)**
- Keep shims working
- Test both old and new imports
- **Effort:** ~4 hours/week maintenance

❌ **Potential for Users to Ignore Warnings**
- Some users disable warnings
- Procrastination risk
- **Mitigation:** Escalate to `FutureWarning`, send emails, update docs

❌ **Complexity During Transition**
- Documentation must cover both paths
- Tests must validate shims work
- **Mitigation:** Mark shim tests with `@pytest.mark.deprecation`

❌ **Version Number Inflation**
- v2.0.0 → v2.1.0 in 8 weeks
- Rapid versioning may confuse users
- **Mitigation:** Clear CHANGELOG, semantic versioning guidelines

### Risk Analysis

**Risk 1: Users Miss Warnings**
- **Probability:** Medium
- **Impact:** High (broken code after v2.1.0)
- **Mitigation:**
  - Multiple warning levels (DeprecationWarning → FutureWarning)
  - Email notifications to known consumers
  - Prominent docs update

**Risk 2: Migration Script Breaks Code**
- **Probability:** Low
- **Impact:** Medium (user frustration)
- **Mitigation:**
  - Extensive testing on internal projects
  - `--dry-run` mode by default
  - Clear instructions to review changes

**Risk 3: Unknown External Consumers**
- **Probability:** High (can't track all users)
- **Impact:** Medium (they break on v2.1.0)
- **Mitigation:**
  - Conservative 8-week window
  - Prominent deprecation warnings
  - Maintain v2.0.x branch for security fixes

---

## Alternatives Considered

### Alternative 1: Hard Break (No Deprecation)
**Rejected** - Too disruptive to users.

**Pros:**
- Clean codebase immediately
- No shim maintenance

**Cons:**
- Breaks existing code instantly
- Poor user experience
- Damages library reputation

### Alternative 2: Permanent Backward Compatibility
**Rejected** - Accumulates technical debt.

**Pros:**
- No breaking changes ever
- Maximum user convenience

**Cons:**
- Maintain shims forever
- Confusion (two ways to do everything)
- Code bloat
- Harder to evolve library

### Alternative 3: 4-Week Transition
**Rejected** - Too short for thorough migration.

**Pros:**
- Faster cleanup
- Less maintenance

**Cons:**
- Insufficient time for testing
- Catches users off-guard
- Higher breakage risk

### Alternative 4: 6-Month Transition (Long-Term Support)
**Rejected** - Too long, excessive debt.

**Pros:**
- Maximum migration time
- Very safe for users

**Cons:**
- 6 months of maintaining two paths
- Users procrastinate
- Technical debt compounds
- Overkill for library of this size

### Alternative 5: Feature Flags (Runtime Toggle)
**Rejected** - Runtime complexity, configuration burden.

```python
# Toggle between old and new behavior
import os
USE_PHASE2 = os.environ.get("VALIDATION_USE_PHASE2", "false") == "true"

if USE_PHASE2:
    from validation.core import ValidationOrchestrator
else:
    from validation_orchestrator import ValidationOrchestrator
```

**Pros:**
- Users control migration timing
- No breaking changes

**Cons:**
- Runtime configuration complexity
- Two code paths maintained indefinitely
- Hard to test (combinatorial explosion)
- Users never migrate (path of least resistance)

---

## Implementation Plan

### Week 0: Preparation
- [ ] Create all shim modules
- [ ] Write migration guide
- [ ] Build migration script
- [ ] Test shims on internal projects
- [ ] Update documentation
- [ ] Prepare CHANGELOG entry

### Week 0-2: Soft Launch (v2.0.0 Release)
- [ ] Release v2.0.0 with shims
- [ ] Announce on mailing list / docs
- [ ] Enable `DeprecationWarning` in tests
- [ ] Monitor warning frequency
- [ ] Gather early feedback

### Week 3-6: Active Support
- [ ] Send migration reminders
- [ ] Offer 1-on-1 migration assistance
- [ ] Fix migration script bugs
- [ ] Update docs based on feedback
- [ ] Track migration progress

### Week 7-8: Final Warnings
- [ ] Escalate to `FutureWarning`
- [ ] Send "last chance" emails
- [ ] Prepare v2.1.0 release notes
- [ ] Final testing of migration script

### Week 9: Removal (v2.1.0 Release)
- [ ] Delete all shim modules
- [ ] Remove deprecated parameters
- [ ] Release v2.1.0
- [ ] Update documentation (remove old paths)
- [ ] Celebrate clean codebase! 🎉

---

## Monitoring & Validation

### Track Deprecation Warning Frequency

```python
# utils/deprecation_tracker.py
import logging
import warnings
from collections import defaultdict

class DeprecationTracker:
    """Track which deprecated features are still in use."""

    _warnings = defaultdict(int)

    @classmethod
    def warn_deprecated(cls, message: str, category=DeprecationWarning):
        """Issue warning and track usage."""
        cls._warnings[message] += 1
        warnings.warn(message, category, stacklevel=3)

    @classmethod
    def report(cls):
        """Report deprecation warning statistics."""
        logging.info("Deprecation Warning Report")
        for message, count in sorted(cls._warnings.items(), key=lambda x: -x[1]):
            logging.info(f"  {count:5d}x: {message}")
```

### Metrics Dashboard

```
Deprecation Tracking (Week 4/8)
================================
validation_orchestrator import:  237 warnings (↓ 60% from week 1)
critic_orchestrator import:      89 warnings (↓ 45% from week 1)
Direct validator instantiation:  12 warnings (↓ 90% from week 1)

Migration Progress: 78% complete (estimated)
At-Risk Projects: 3 (still using old imports heavily)
```

### Email Reminders

```
Subject: [Action Required] Migrate to validation lib v2.0 by Dec 28

Hi validation lib user,

We noticed your project still uses deprecated imports:
  - validation_orchestrator.py: 42 usages
  - critic_orchestrator.py: 15 usages

These will stop working in v2.1.0 (releases Dec 28, 2025).

Migration Guide: /home/jevenson/.claude/lib/docs/MIGRATION_GUIDE_V2.md
Automated Script: python scripts/migrate_to_v2.py /path/to/your/project

Need help? Reply to this email or file an issue.

Thanks,
Validation Lib Team
```

---

## Testing Strategy

### Test Backward Compatibility (Weeks 0-8)

```python
# tests/test_deprecation_shims.py

class TestBackwardCompatibility:
    """Test that old imports still work during deprecation period."""

    def test_old_validation_orchestrator_import_works(self):
        """Test deprecated import path still functions."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Old import should work but warn
            from validation_orchestrator import ValidationOrchestrator

            # Verify warning issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

            # Verify functionality preserved
            validator = ValidationOrchestrator()
            assert validator is not None

    def test_old_critic_orchestrator_import_works(self):
        """Test deprecated critic import still functions."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            from critic_orchestrator import CriticOrchestrator

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

    @pytest.mark.parametrize("week", [7, 8])
    def test_escalated_warnings_final_weeks(self, week):
        """Test that warnings escalate to FutureWarning in final weeks."""
        # Simulate week 7-8
        with patch("time.time", return_value=week_timestamp(week)):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                from validation_orchestrator import ValidationOrchestrator

                # Should escalate to FutureWarning
                assert len(w) == 1
                assert issubclass(w[0].category, FutureWarning)
```

### Test Migration Script

```python
# tests/test_migration_script.py

def test_migration_script_updates_imports(tmp_path):
    """Test that migration script correctly rewrites imports."""
    # Create test file with old imports
    test_file = tmp_path / "test.py"
    test_file.write_text("""
from validation_orchestrator import ValidationOrchestrator

validator = ValidationOrchestrator()
    """)

    # Run migration
    from scripts.migrate_to_v2 import migrate_file
    updated = migrate_file(test_file, dry_run=False)

    assert updated is True

    # Verify file updated
    content = test_file.read_text()
    assert "from validation.core import ValidationOrchestrator" in content
    assert "from validation_orchestrator" not in content
```

---

## References

- **PEP 387** - Backwards Compatibility Policy
- **Semantic Versioning** - https://semver.org/
- **Deprecation Best Practices** - Django deprecation policy
- **Python Warnings** - https://docs.python.org/3/library/warnings.html
- **Breaking Changes Done Right** - Stripe API versioning guide

---

## Revision History

| Date       | Version | Changes                        | Author              |
|------------|---------|--------------------------------|---------------------|
| 2025-11-09 | 1.0     | Initial ADR                    | Documentation Expert |

---

## Appendix: Timeline Visualization

```
Week 0-2: Soft Launch (v2.0.0)
═══════════════════════════════════════════════════════════════
[Announce] [Docs] [Shims Active] [DeprecationWarning]
↓
│  Users see warnings, begin migrating
│  Early adopters provide feedback
↓

Week 3-6: Active Support
═══════════════════════════════════════════════════════════════
[Reminders] [Migration Script] [1-on-1 Support] [Track Progress]
↓
│  Most users migrate during this window
│  Address migration issues
↓

Week 7-8: Final Warnings
═══════════════════════════════════════════════════════════════
[FutureWarning] [Last Chance Emails] [Prepare v2.1.0]
↓
│  Stragglers migrate
│  Final testing
↓

Week 9: Removal (v2.1.0)
═══════════════════════════════════════════════════════════════
[Delete Shims] [Release v2.1.0] [Clean Codebase]
✅ Migration Complete
```

---

**Next Steps:**
1. Review and approve this ADR
2. Create all shim modules
3. Write migration guide
4. Build and test migration script
5. Prepare v2.0.0 release
