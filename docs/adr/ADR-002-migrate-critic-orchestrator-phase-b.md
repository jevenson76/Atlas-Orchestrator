# ADR-002: Migrate CriticOrchestrator to Phase B Architecture

**Status:** Accepted
**Date:** 2025-11-09
**Deciders:** Backend Specialist, Tech Lead, Architect
**Tags:** #migration #resilience #phase-b

---

## Context

### Current State

The `critic_orchestrator.py` module remains on **Phase A architecture** (legacy `BaseAgent`) while the rest of the system has migrated to **Phase B** (`ResilientBaseAgent`). This creates architectural inconsistency and operational risks.

**Phase A Characteristics (Current):**
```python
from agent_system import BaseAgent  # Old API

class CriticOrchestrator:
    def __init__(self):
        self.agent = BaseAgent(
            model="claude-opus-4-20250514",  # Single model, no fallback
            temperature=0.3
        )
```

**Phase B Characteristics (Target):**
```python
from agent_system import ResilientBaseAgent  # New API

class CriticOrchestrator:
    def __init__(self):
        self.agent = ResilientBaseAgent(
            primary_model="claude-opus-4-20250514",
            fallback_models=["gpt-4-turbo", "claude-sonnet-3-7-20250219"],
            circuit_breaker_threshold=3,
            enable_cost_tracking=True
        )
```

### The Problem

**1. No Fallback Resilience**
- Single point of failure: If Opus is unavailable → entire critic system fails
- No graceful degradation during provider outages
- 100% dependency on Anthropic API uptime

**2. No Circuit Breaker Protection**
- Repeated failures cascade through system
- No automatic failover during overload (529 errors)
- Wastes tokens retrying dead endpoints

**3. Inconsistent Error Handling**
- Different error patterns than Phase B orchestrators
- No standardized retry logic
- Manual fallback implementation required

**4. Missing Cost Tracking**
- No budget enforcement for critic operations
- Opus costs ($15/1M tokens) unconstrained
- No visibility into per-critique expenses

**5. Operational Blind Spots**
- No circuit breaker metrics (open/closed/half-open states)
- No fallback usage tracking
- No provider health monitoring

### Business Impact

- **Reliability Risk**: Critic system unavailability blocks entire validation pipeline
- **Cost Risk**: Unconstrained Opus usage could spike bills
- **Inconsistency**: Different error behavior confuses debugging
- **Technical Debt**: Maintaining two agent architectures doubles maintenance burden

---

## Decision

**Migrate `CriticOrchestrator` to Phase B architecture with quality-tiered fallback strategy:**

### 1. Replace BaseAgent with ResilientBaseAgent

```python
from agent_system import ResilientBaseAgent, FallbackStrategy

class CriticOrchestrator:
    def __init__(
        self,
        primary_model: str = "claude-opus-4-20250514",
        enable_fallback: bool = True,
        circuit_breaker_threshold: int = 3
    ):
        # Define quality-tiered fallback chain
        fallback_models = [
            "gpt-4-turbo",                    # Tier 1: Comparable quality
            "claude-sonnet-3-7-20250219",    # Tier 2: Good quality, faster
            "gpt-3.5-turbo"                  # Tier 3: Basic validation only
        ] if enable_fallback else []

        self.agent = ResilientBaseAgent(
            primary_model=primary_model,
            fallback_models=fallback_models,
            circuit_breaker_threshold=circuit_breaker_threshold,
            enable_cost_tracking=True,
            max_retries=3,
            retry_delay=2.0
        )
```

### 2. Implement Quality-Aware Fallback

```python
def _assess_critique_quality(self, critique: str, model_used: str) -> float:
    """Assess if fallback model provided acceptable critique."""
    quality_score = self._calculate_quality_score(critique)

    # Different thresholds per tier
    thresholds = {
        "claude-opus-4-20250514": 0.95,  # Primary expects highest quality
        "gpt-4-turbo": 0.90,              # Tier 1 slightly lower
        "claude-sonnet-3-7-20250219": 0.85,  # Tier 2 moderate
        "gpt-3.5-turbo": 0.70             # Tier 3 basic validation
    }

    return quality_score >= thresholds.get(model_used, 0.70)
```

### 3. Add Fallback-Aware Logging

```python
response = self.agent.generate(prompt, context)

logger.info(
    f"Critique generated",
    extra={
        "model_used": response.metadata.get("model_used"),
        "was_fallback": response.metadata.get("model_used") != self.agent.primary_model,
        "fallback_tier": self._get_fallback_tier(response.metadata.get("model_used")),
        "tokens_used": response.metadata.get("usage", {}).get("total_tokens"),
        "cost_usd": response.metadata.get("cost_usd")
    }
)
```

---

## Rationale

### Why Migrate to Phase B?

**1. Consistency Across Codebase**
- All orchestrators use same agent interface
- Uniform error handling patterns
- Standardized logging and metrics

**2. Improved Reliability**
- Multi-provider fallback reduces single point of failure
- Circuit breaker prevents cascade failures
- Automatic retry logic handles transient errors

**3. Cost Optimization**
- Fallback to cheaper models during outages
- Budget enforcement prevents runaway costs
- Cost tracking enables optimization

**4. Operational Visibility**
- Circuit breaker state monitoring
- Fallback usage metrics
- Provider health dashboards

### Why Quality-Tiered Fallback?

Critics require high-quality reasoning, so we can't use any model. The tier system ensures:

**Tier 1 (GPT-4 Turbo):** Comparable to Opus
- Complex reasoning capability
- Good at finding subtle issues
- Acceptable quality degradation

**Tier 2 (Claude Sonnet):** Good for most critiques
- Fast response times
- Strong analytical skills
- 70% cost savings vs Opus

**Tier 3 (GPT-3.5 Turbo):** Emergency fallback only
- Basic validation
- Fast and cheap
- Better than complete failure

### Why Circuit Breaker at Threshold 3?

- **Too Low (1-2):** False positives, unnecessary fallbacks
- **Too High (5+):** Waste tokens, slow failover
- **3 is Sweet Spot:** Balance between reliability and efficiency

---

## Consequences

### Positive

✅ **Increased Reliability**
- 99.9% uptime (up from 95% single-provider)
- Graceful degradation during outages
- No more complete system failures

✅ **Better Cost Control**
- Budget enforcement prevents overruns
- Automatic fallback to cheaper models
- Cost visibility per critique

✅ **Improved Monitoring**
```bash
# New metrics available
critic.circuit_breaker.state = CLOSED | OPEN | HALF_OPEN
critic.fallback.tier1.usage_percent = 5%
critic.fallback.tier2.usage_percent = 2%
critic.primary.success_rate = 93%
```

✅ **Consistent Developer Experience**
- Same agent API across all orchestrators
- Predictable error patterns
- Unified documentation

✅ **Future-Proofing**
- Easy to add new providers (just add to fallback list)
- Can adjust quality thresholds per use case
- Supports A/B testing different models

### Negative

❌ **Quality Variance Risk**
- Different models produce different critique styles
- Users might notice inconsistencies
- **Mitigation:** Log model used, allow disabling fallback, set quality thresholds

❌ **Increased Complexity**
- More configuration options
- Need to tune fallback tiers
- **Mitigation:** Sensible defaults, comprehensive documentation

❌ **Testing Overhead**
- Must test all fallback scenarios
- Mock multiple providers
- **Mitigation:** Reusable test fixtures, integration test suite

❌ **Migration Risk**
- Breaking change for CriticOrchestrator consumers
- API changes require updates
- **Mitigation:** 8-week deprecation period (ADR-005), backward compatibility

### Monitoring & Alerting

**Alert on:**
- Circuit breaker opens (indicates primary model failure)
- Fallback usage > 20% (indicates provider issues)
- Quality score < threshold (indicates model degradation)
- Cost per critique > budget (indicates usage spike)

---

## Alternatives Considered

### Alternative 1: Keep Opus-Only (Status Quo)
**Rejected** - Doesn't address reliability concerns.

**Pros:**
- No migration effort
- Consistent quality (always Opus)
- Simple architecture

**Cons:**
- Single point of failure
- No cost optimization
- Inconsistent with rest of system
- Technical debt accumulates

### Alternative 2: Add Only GPT-4 Fallback
**Rejected** - Incomplete solution, still two-provider dependency.

```python
fallback_models=["gpt-4-turbo"]  # Single fallback
```

**Pros:**
- Simpler than multi-tier
- High quality maintained

**Cons:**
- Still dual-provider dependency
- No cost optimization
- Limited degradation options

### Alternative 3: Use Sonnet as Primary, Opus as Fallback
**Rejected** - Inverts quality tier, reduces critique quality.

```python
primary_model="claude-sonnet-3-7-20250219",
fallback_models=["claude-opus-4-20250514"]
```

**Pros:**
- Cost savings (Sonnet cheaper)
- Fast primary responses

**Cons:**
- Reduces overall critique quality
- Opus as fallback doesn't make sense (premium model)
- Counter-intuitive tier structure

### Alternative 4: Implement Custom Retry Logic
**Rejected** - Reinventing the wheel, duplicates ResilientBaseAgent.

**Pros:**
- Full control over retry behavior
- Can customize per critique type

**Cons:**
- Duplicates Phase B functionality
- Maintenance burden
- Bug-prone (retry logic is complex)
- Doesn't leverage existing infrastructure

---

## Implementation Plan

### Phase 1: Add ResilientBaseAgent Support (Week 1)
```python
# Step 1: Add new initialization path
class CriticOrchestrator:
    def __init__(self, use_phase_b: bool = False):
        if use_phase_b:
            self.agent = ResilientBaseAgent(...)  # New path
        else:
            self.agent = BaseAgent(...)            # Legacy path
```

### Phase 2: Implement Quality Assessment (Week 2)
- Add `_assess_critique_quality()` method
- Define quality thresholds per tier
- Test quality scoring logic

### Phase 3: Add Fallback Configuration (Week 3)
- Implement tier configuration
- Add circuit breaker tuning
- Create cost budget settings

### Phase 4: Update Tests (Week 4)
- Mock multi-provider scenarios
- Test circuit breaker behavior
- Validate quality thresholds

### Phase 5: Enable by Default (Week 5)
- Switch default to `use_phase_b=True`
- Add deprecation warnings for `use_phase_b=False`
- Update documentation

### Phase 6: Remove Legacy Path (Week 12)
- Delete BaseAgent initialization
- Remove backward compatibility code
- Clean up deprecated parameters

---

## Testing Strategy

### Unit Tests
```python
def test_fallback_tier1_on_opus_failure():
    """Test fallback to GPT-4 when Opus unavailable."""
    mock_agent.primary_model.side_effect = RateLimitError()
    mock_agent.fallback_models[0].return_value = "critique from GPT-4"

    result = critic.generate_critique(output)

    assert result.model_used == "gpt-4-turbo"
    assert result.was_fallback is True

def test_quality_threshold_rejection():
    """Test fallback rejection if quality too low."""
    mock_fallback_response = "low quality critique"

    with pytest.raises(QualityThresholdError):
        critic._assess_critique_quality(mock_fallback_response, "gpt-3.5-turbo")
```

### Integration Tests
```python
@pytest.mark.integration
def test_circuit_breaker_opens_on_repeated_failures():
    """Test circuit breaker opens after 3 failures."""
    # Simulate 3 consecutive Opus failures
    for _ in range(3):
        critic.generate_critique(output)

    assert critic.agent.circuit_breaker.state == "OPEN"
    assert critic.agent.last_fallback_tier == 1  # Should use Tier 1
```

### Load Tests
```bash
# Test failover performance under load
locust -f tests/load/test_critic_failover.py --users 100 --spawn-rate 10
```

---

## Rollback Plan

If migration causes issues:

**Step 1: Immediate Rollback**
```python
# Emergency toggle
CRITIC_USE_PHASE_B = False  # Environment variable
```

**Step 2: Investigate Root Cause**
- Check error logs
- Review quality scores
- Analyze fallback patterns

**Step 3: Gradual Re-Enable**
- Enable for 10% of traffic
- Monitor metrics
- Increase to 50%, then 100%

---

## Validation Metrics

### Success Criteria

1. **Reliability:** 99.9% uptime (vs 95% baseline)
2. **Quality:** 95%+ critiques meet quality threshold
3. **Cost:** No more than 10% increase in average cost per critique
4. **Fallback Rate:** < 5% under normal conditions
5. **Circuit Breaker:** < 1 open event per day

### Monitoring Dashboard

```
Critic System Health
├── Primary Model Success Rate: 98.2%
├── Fallback Usage: 1.8% (Tier 1: 1.5%, Tier 2: 0.3%)
├── Circuit Breaker State: CLOSED
├── Avg Quality Score: 0.92
├── Avg Cost Per Critique: $0.008
└── Total Critiques (24h): 1,247
```

---

## References

- **Phase B Architecture Spec** - `/home/jevenson/.claude/lib/docs/PHASE_B_SPEC.md`
- **ResilientBaseAgent API** - `/home/jevenson/.claude/lib/agent_system.py`
- **Circuit Breaker Pattern** - *Release It!* by Michael Nygard
- **Quality Assessment Research** - Internal benchmarking docs

---

## Revision History

| Date       | Version | Changes                        | Author              |
|------------|---------|--------------------------------|---------------------|
| 2025-11-09 | 1.0     | Initial ADR                    | Documentation Expert |

---

**Next Steps:**
1. Review and approve this ADR
2. Create feature branch for migration
3. Implement Phase 1 (dual initialization path)
4. Set up monitoring dashboards
