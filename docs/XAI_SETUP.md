# xAI (Grok) Setup Guide

## Overview

ZeroTouch Atlas now supports xAI's Grok models as a provider option. Grok offers competitive pricing ($3/$15 per 1M tokens, matching Claude Sonnet) with strong reasoning capabilities and real-time search integration.

## Getting Started

### 1. Obtain xAI API Key

1. Visit https://x.ai/api
2. Sign up for an account
3. Navigate to Developer Console
4. Generate a new API key (format: `xai-...`)

### 2. Configure API Key

**Option A: Environment Variable** (Recommended)
```bash
export XAI_API_KEY="xai-your-key-here"
```

**Option B: Config File**
```bash
mkdir -p ~/.claude
cat > ~/.claude/config.json << 'EOF'
{
  "api_keys": {
    "xai": "xai-your-key-here"
  },
  "fallback_order": ["anthropic", "xai", "google", "openai"]
}
EOF
```

### 3. Verify Installation

```bash
cd /home/jevenson/.claude/lib
python3 test_xai_integration.py
```

Expected output:
```
============================================================
XAI (GROK) INTEGRATION TEST SUITE
============================================================

TEST 1: API Configuration
============================================================
✓ xAI configured: True
  Source: config_file
  Key preview: xai-Kvo...puGM

TEST 2: Model Pricing
============================================================
✓ grok-beta: 1000 in + 500 out = $0.010500
✓ grok-2-1212: 2000 in + 1000 out = $0.014000

TEST 3: Client Initialization
============================================================
✓ xAI client initialized successfully

TEST 4: Simple Completion
============================================================
✓ Completion successful
  Output: Hello from Grok...
  Model: grok-beta
  Provider: xai
  Tokens: 45 in, 12 out
  Cost: $0.000315
  Latency: 1.23s

TEST 5: Fallback Behavior
============================================================
✓ Grok in fallback chain: ['grok-beta']
  Full chain: ['claude-3-opus-20240229', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'grok-beta', 'gemini-pro', 'gpt-4', 'gpt-3.5-turbo']

============================================================
TEST RESULTS
============================================================
API Config           ✓ PASS
Pricing              ✓ PASS
Client Init          ✓ PASS
Simple Completion    ✓ PASS
Fallback Behavior    ✓ PASS

Passed: 5/5

🎉 All tests passed!
```

## Available Models

| Model ID | Description | Pricing (per 1M tokens) | Best For |
|----------|-------------|------------------------|----------|
| `grok-beta` | General-purpose (recommended) | $3 in / $15 out | Default choice, balanced performance |
| `grok-2-1212` | Improved accuracy (Dec 2024) | $2 in / $10 out | Cost-sensitive tasks |
| `grok-2-vision-1212` | Multimodal with vision | $2 in / $10 out | Image analysis, OCR |

## Usage Examples

### Basic Agent

```python
from resilient_agent import ResilientBaseAgent
from core.constants import Models

agent = ResilientBaseAgent(
    role="Code Reviewer",
    model=Models.GROK_BETA,
    max_tokens=2048,
    temperature=0.7
)

result = agent.call(prompt="Review this Python code for security vulnerabilities...")
print(result.output)
```

### With Automatic Fallback

```python
agent = ResilientBaseAgent(
    role="Data Analyst",
    model=Models.SONNET,  # Primary: Claude Sonnet
    enable_fallback=True  # Will fallback to Grok if Claude fails
)

result = agent.call(prompt="Analyze this dataset...")
if result.fallback_occurred:
    print(f"Fallback to: {result.model_used} ({result.provider})")
```

**Fallback Order**: Claude → **Grok** → Gemini → GPT

### Cost Tracking

```python
from agent_system import CostTracker

tracker = CostTracker(daily_budget=5.0)

agent = ResilientBaseAgent(
    role="Assistant",
    model=Models.GROK_BETA,
    cost_tracker=tracker
)

# Make multiple calls...
for task in tasks:
    result = agent.call(prompt=task)
    print(f"Task cost: ${result.cost:.6f}")

# Get cost report
report = tracker.get_report()
print(f"Total spent today: ${report['daily_spent']:.2f}")
print(f"Budget remaining: ${report['daily_remaining']:.2f}")
```

### With Output Styles

```python
agent = ResilientBaseAgent(
    role="Code Generator",
    model=Models.GROK_2,
    output_style="code_generation",  # Structured output
    temperature=0.2
)

result = agent.call(
    prompt="Generate a Python function to calculate Fibonacci numbers",
    context={"language": "python", "style": "clean"}
)
```

## Pricing Comparison

| Provider | Model | Input ($/1M) | Output ($/1M) | Notes |
|----------|-------|-------------|---------------|-------|
| Anthropic | Haiku | $0.25 | $1.25 | Fastest, cheapest |
| **xAI** | **Grok Beta** | **$3.00** | **$15.00** | **Matches Sonnet pricing** |
| Anthropic | Sonnet | $3.00 | $15.00 | Balanced choice |
| **xAI** | **Grok 2** | **$2.00** | **$10.00** | **33% cheaper than Sonnet** |
| Google | Gemini Pro | ~$0.50 | ~$1.50 | Budget option |
| OpenAI | GPT-4 | $30.00 | $60.00 | Most expensive |
| OpenAI | GPT-3.5 Turbo | $0.50 | $1.50 | Legacy model |

**Cost Optimization Strategy**:
- Use **Grok 2** for cost-sensitive tasks (33% cheaper than Sonnet)
- Use **Grok Beta** as Sonnet alternative (same price, different capabilities)
- Enable fallback for resilience without cost penalty

## Free Credits

Eligible teams receive **$150/month** in free credits:
- Must spend $5 minimum
- Must opt into data sharing
- Country restrictions apply

See: https://docs.x.ai for eligibility details

## Troubleshooting

### Error: "xAI client not available"

**Cause**: OpenAI SDK not installed (xAI uses OpenAI-compatible API)

**Solution**:
```bash
pip install openai
```

### Error: "No API key found"

**Cause**: XAI_API_KEY not configured

**Solution**:
```bash
# Check environment variable
echo $XAI_API_KEY

# Or check config file
cat ~/.claude/config.json

# Set via environment
export XAI_API_KEY="xai-your-key"

# Or update config file
echo '{"api_keys": {"xai": "xai-your-key"}}' > ~/.claude/config.json
```

### Error: "Rate limit exceeded"

**Cause**: xAI rate limits vary by tier

**Free Tier Limits**:
- Lower request rate
- May encounter 429 errors during high usage

**Paid Tier Limits**:
- Higher request rate
- Better for production workloads

**Solution**:
```python
# Enable automatic fallback
agent = ResilientBaseAgent(
    model=Models.GROK_BETA,
    enable_fallback=True  # Auto-switch to Gemini/GPT on rate limit
)
```

### Error: "Connection timeout"

**Cause**: Network issues or API unavailability

**Solution**:
```python
# Increase timeout
agent = ResilientBaseAgent(
    model=Models.GROK_BETA,
    timeout=120  # 2 minutes instead of 60s
)
```

### Cost Tracking Shows $0.00

**Cause**: Model pricing not configured

**Solution**: Verify pricing is in `agent_system.py`:
```python
from agent_system import ModelPricing
print(ModelPricing.PRICING.get(Models.GROK_BETA))
# Should output: (3.0, 15.0)
```

## Advanced Configuration

### Custom Fallback Order

Place Grok before Gemini for better quality fallback:

```python
# In ~/.claude/config.json
{
  "fallback_order": ["anthropic", "xai", "google", "openai"]
}
```

### Circuit Breaker Tuning

Adjust circuit breaker sensitivity for Grok:

```python
from resilience import ModelFallbackChain

fallback = ModelFallbackChain(
    primary_model=Models.GROK_BETA,
    enable_cross_provider=True
)

# Access circuit breaker
breaker = fallback.circuit_breakers[Models.GROK_BETA]
print(f"State: {breaker.get_state()}")
print(f"Failures: {breaker.failure_count}")
```

### Multi-Provider Cost Comparison

```python
from agent_system import CostTracker

tracker = CostTracker()

# Track calls across providers
for provider, model in [
    ('anthropic', Models.SONNET),
    ('xai', Models.GROK_BETA),
    ('google', 'gemini-pro')
]:
    agent = ResilientBaseAgent(
        model=model,
        cost_tracker=tracker,
        enable_fallback=False
    )
    result = agent.call(prompt="Test prompt")
    print(f"{provider}: ${result.cost:.6f}")
```

## Integration with ZeroTouch Atlas UI

### Task Submission

Grok models appear automatically in the model dropdown:

1. Open **Manual Task Builder** tab
2. Select **Model**: `grok-beta` or `grok-2-1212`
3. Submit task

### Observability Dashboard

Monitor Grok usage in real-time:

1. Navigate to **📊 Live Monitor** tab
2. View **Cost Breakdown by Model** chart
3. Check **Provider Health** indicators
4. See **Execution Timeline** for Grok events

### Cost Tracking

View Grok costs in cost metrics:
- Total cost across all providers
- Per-model breakdown (bar chart)
- Provider-level aggregation

## API Reference

### Models Class

```python
from core.constants import Models

# Available Grok models
Models.GROK_BETA        # "grok-beta"
Models.GROK_2           # "grok-2-1212"
Models.GROK_2_VISION    # "grok-2-vision-1212"
```

### ResilientBaseAgent

```python
agent = ResilientBaseAgent(
    role: str,                          # Agent role
    model: str = Models.GROK_BETA,      # Model to use
    max_tokens: int = 2048,             # Max response length
    temperature: float = 0.7,           # Creativity (0-1)
    timeout: int = 60,                  # Request timeout (seconds)
    enable_fallback: bool = True,       # Auto-fallback on failure
    enable_security: bool = True,       # Input validation
    cost_tracker: CostTracker = None    # Budget tracking
)
```

### ModelPricing

```python
from agent_system import ModelPricing

cost = ModelPricing.calculate_cost(
    model=Models.GROK_BETA,
    input_tokens=1000,
    output_tokens=500
)
# Returns: 0.0105 ($3 * 0.001 + $15 * 0.0005)
```

## Best Practices

### 1. Use Grok 2 for Cost Savings

```python
# Instead of Sonnet ($3/$15)
agent = ResilientBaseAgent(model=Models.SONNET)

# Use Grok 2 ($2/$10) for 33% savings
agent = ResilientBaseAgent(model=Models.GROK_2)
```

### 2. Enable Fallback for Resilience

```python
# Production-ready configuration
agent = ResilientBaseAgent(
    model=Models.GROK_BETA,
    enable_fallback=True,  # Auto-switch on failure
    timeout=90,            # Generous timeout
    max_retries=3          # Retry transient failures
)
```

### 3. Monitor Costs

```python
tracker = CostTracker(
    daily_budget=10.0,   # $10/day limit
    hourly_budget=2.0    # $2/hour limit
)

agent = ResilientBaseAgent(
    model=Models.GROK_BETA,
    cost_tracker=tracker
)

# Check budget before expensive operations
if tracker.get_daily_spent() > 8.0:
    print("⚠️ Warning: Approaching daily budget limit")
```

### 4. Use Vision Models Appropriately

```python
# Only use vision models when needed
agent_text = ResilientBaseAgent(model=Models.GROK_BETA)  # Text-only
agent_vision = ResilientBaseAgent(model=Models.GROK_2_VISION)  # Multimodal

# Text task
result = agent_text.call(prompt="Summarize this article...")

# Vision task
result = agent_vision.call(
    prompt="Describe this image...",
    context={"image_url": "https://..."}
)
```

### 5. Log Provider Metrics

```python
result = agent.call(prompt="Task...")

# Log detailed metrics
logger.info(f"Task completed:")
logger.info(f"  Model: {result.model_used}")
logger.info(f"  Provider: {result.provider}")
logger.info(f"  Tokens: {result.total_tokens}")
logger.info(f"  Cost: ${result.cost:.6f}")
logger.info(f"  Latency: {result.latency:.2f}s")
logger.info(f"  Fallback: {result.fallback_occurred}")
```

## Support

- **xAI Documentation**: https://docs.x.ai
- **xAI API Reference**: https://docs.x.ai/docs/api-reference
- **GitHub Issues**: https://github.com/jevenson76/Atlas-Orchestrator/issues
- **Email**: support@zerotouch-atlas.com

## Changelog

### v1.1.0 (2025-11-07)
- ✅ Added xAI (Grok) provider integration
- ✅ Grok Beta, Grok 2, Grok 2 Vision support
- ✅ Automatic fallback chain inclusion
- ✅ Cost tracking for all Grok models
- ✅ Circuit breaker integration
- ✅ Comprehensive test suite
- ✅ Full documentation

---

**Last Updated**: November 7, 2025
**Version**: 1.1.0
**Maintained By**: ZeroTouch Atlas Team
