# Setup Guide: Using Claude Code Max Subscription with Atlas

This guide shows how to configure Atlas to use your **Claude Code Max subscription** instead of requiring separate API keys.

## 🚨 CRITICAL: Two Authentication Methods Explained

**Before you start, understand this:** There are TWO completely separate ways to access Claude models, and people often confuse them!

### Method A: Console API (Pay-Per-Token) ❌ NOT WHAT WE WANT

| Aspect | Details |
|--------|---------|
| **What it is** | Developer API with pay-as-you-go pricing |
| **Where you get it** | https://console.anthropic.com → Get API Keys |
| **How you authenticate** | Set `ANTHROPIC_API_KEY` environment variable |
| **What it looks like** | `export ANTHROPIC_API_KEY="sk-ant-xxxxx..."` |
| **What it costs** | $3/1M tokens (Sonnet), $15/1M tokens (Opus) |
| **What it gives you** | Unlimited usage, but you pay per token |
| **Best for** | Production apps, server-side integrations |

### Method B: Subscription (OAuth Login) ✅ THIS IS WHAT WE WANT

| Aspect | Details |
|--------|---------|
| **What it is** | Claude Max subscription with quota-based access |
| **Where you get it** | https://claude.ai → Subscribe to Max ($100-$200/month) |
| **How you authenticate** | `claude login` (opens browser to claude.ai) |
| **What it looks like** | Browser OAuth flow with your claude.ai email/password |
| **What it costs** | $100-$200 fixed monthly fee |
| **What it gives you** | 50-800 prompts per 5 hours (depending on plan) |
| **Best for** | Personal use, Claude Code CLI, interactive development |

### Why This Bridge Uses Method B

**The entire point of this bridge is to give Atlas access to your EXISTING Max subscription!**

- You already pay $100-$200/month for Claude Max
- That subscription includes quota for programmatic access via Claude Code CLI
- This bridge tunnels that access into Atlas
- Result: No additional API costs, just use your existing subscription!

### Common Confusion Point

**Wrong assumption:** "OAuth login is wrong, I need to get an API key from Console"
- ❌ This would be Method A (pay-per-token)
- ❌ You'd be paying TWICE (subscription + API usage)
- ❌ You wouldn't be using your Max subscription quota

**Correct understanding:** "OAuth login IS the right way, it accesses my subscription"
- ✅ This is Method B (subscription quota)
- ✅ You only pay your monthly subscription fee
- ✅ You use your Max subscription quota for Atlas

## Prerequisites

- Claude Code Max subscription ($200/month for Max 20x with Opus 4 ULTRATHINK)
- Node.js 18+ and npm installed
- Atlas installed at `/home/jevenson/.claude/lib/`

## Step 1: Install Claude Code CLI

```bash
npm install -g @anthropics/claude-code
```

Verify installation:
```bash
claude --version
# Should show version 0.4.0 or higher
```

## Step 2: Authenticate with Your Max Subscription

### Understanding the Two Authentication Methods

**There are TWO completely separate ways to access Claude:**

| Method | What It Is | Where You Get It | What It Costs | Used For |
|--------|-----------|------------------|---------------|----------|
| **Method A: API Key** | Console API credentials | https://console.anthropic.com | Pay-per-token ($3-$15 per 1M tokens) | Programmatic API access |
| **Method B: Subscription** | OAuth login to claude.ai | https://claude.ai (your Max account) | Fixed monthly ($100-$200) + quota | Interactive Claude Code, Web UI |

**THIS BRIDGE USES METHOD B (Subscription)** - We access your Max subscription quota, NOT API credits!

### Why We Unset ANTHROPIC_API_KEY

The Claude Code CLI supports BOTH authentication methods:
- If `ANTHROPIC_API_KEY` environment variable exists → Uses Method A (pay-per-token API)
- If `ANTHROPIC_API_KEY` is NOT set → Uses Method B (subscription OAuth)

By unsetting the API key, we force Claude Code to use your subscription!

### Authenticate with Subscription (Method B)

```bash
# If you previously used an API key, logout first:
claude logout

# Ensure no API key in environment:
unset ANTHROPIC_API_KEY

# Login with your Max subscription:
claude login
```

**When the browser opens (OAuth flow):**
1. ✅ **DO**: Login with your **claude.ai account** (the one with Max subscription)
   - Example: `your-email@example.com` + password you use on claude.ai website
   - This is the account you pay $100-$200/month for
2. ❌ **DON'T**: Use Console API credentials from console.anthropic.com
3. ❌ **DON'T**: Enter an API key anywhere
4. ❌ **DON'T**: Look for "API Keys" section - you're logging in like you would to use the website

**Think of it this way:**
- Method A (API Key): Like using a prepaid debit card - you pay as you go
- Method B (Subscription): Like using a Netflix subscription - you already paid, just log in

**We're using Method B!** The OAuth login IS the correct path!

## Step 3: Verify Authentication

```bash
claude --print "test" --model sonnet
```

Should return a JSON response without errors. If you see authentication errors, repeat Step 2.

## Step 4: Test the MCP Bridge

```bash
cd /home/jevenson/.claude/lib/mcp_bridge
python3 claude_code_bridge.py
```

Expected output:
```
✅ Claude Code CLI found at: /usr/local/bin/claude (or similar)
🤖 Calling Claude Code: sonnet (subscription mode)
✅ Claude Code response received (via subscription)
```

The test will confirm:
- Claude Code CLI is installed and working
- Authentication is via subscription (not API key)
- Bridge successfully communicates with Claude models

## Step 5: Run Atlas

```bash
cd /home/jevenson/.claude/lib
streamlit run atlas_app.py
```

Atlas will now use your **Max subscription** for all Claude model calls (Sonnet, Opus 3, Opus 4 ULTRATHINK)!

## How It Works

The MCP bridge uses `claude --print` mode with a critical environment modification:

```
Atlas App
    ↓
Anthropic SDK Adapter (mcp_bridge.Anthropic - drop-in replacement)
    ↓
Claude Code Bridge (claude_code_bridge.py)
    ↓
`claude --print --output-format json` (with ANTHROPIC_API_KEY unset)
    ↓
Claude Code OAuth Authentication (Method B - Subscription)
    ↓
Your Max Subscription (200-800 prompts per 5 hours)
```

### The Critical Environment Variable Trick

**Normal API Usage (Method A):**
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"  # Console API key
claude --print "test" --model sonnet
# Result: Uses pay-per-token API, charges your API credits
```

**Subscription Usage (Method B - What We Want):**
```bash
unset ANTHROPIC_API_KEY  # Remove API key from environment
claude --print "test" --model sonnet
# Result: Uses OAuth subscription, charges your Max quota
```

**Key Insight**: By unsetting `ANTHROPIC_API_KEY` environment variable, Claude Code "falls back" to subscription (OAuth) authentication. But this isn't really a fallback - it's the PRIMARY method we want! We're explicitly choosing Method B (subscription) over Method A (API key).

**Why This Works:**
- You already logged in with `claude login` (OAuth to claude.ai)
- Claude Code CLI stores those OAuth credentials
- When no API key is present, it uses the stored OAuth credentials
- OAuth credentials = access to your Max subscription quota
- Therefore: We get programmatic access to your subscription!

## Usage Limits

Your subscription quota:

| Plan | Monthly Cost | Prompts per 5 hours | Estimated Usage |
|------|-------------|---------------------|-----------------|
| **Max 5x** | $100 | 50-200 | Light usage |
| **Max 20x** | $200 | 200-800 | Heavy usage |

The MCP bridge will consume from your subscription quota (not API credits).

## Troubleshooting

### Issue: "Claude Code CLI not found"

**Solution:**
```bash
npm install -g @anthropics/claude-code
```

### Issue: "Not authenticated with Claude Code"

**Solution:**
```bash
claude login
# Authenticate with your Max subscription
```

### Issue: "Using API key instead of subscription"

This means you're accidentally using **Method A (Console API)** instead of **Method B (Subscription)**.

**Common Causes:**
1. You have `ANTHROPIC_API_KEY` environment variable set
2. You logged in with console.anthropic.com credentials instead of claude.ai credentials
3. You're confusing the two authentication methods

**Solution:**
```bash
# Step 1: Completely logout and clear any cached credentials
claude logout

# Step 2: Make absolutely sure no API key is in environment
unset ANTHROPIC_API_KEY
echo $ANTHROPIC_API_KEY  # Should be empty

# Step 3: Login with subscription (OAuth flow)
claude login
```

**When browser opens:**
- ✅ **DO**: Use the SAME email/password you use to login to https://claude.ai
- ✅ **DO**: Think "I'm logging into the website where I chat with Claude"
- ❌ **DON'T**: Go to console.anthropic.com
- ❌ **DON'T**: Look for API keys
- ❌ **DON'T**: Use "Console" or "API" credentials

**Verify You're Using Method B:**
```bash
# Test in --print mode (this is what the bridge uses)
claude --print "test" --model sonnet

# Should return JSON response without authentication errors
# This confirms you're using subscription (Method B), not API (Method A)
```

**Still confused? Here's the test:**
```bash
# Set an API key and try
export ANTHROPIC_API_KEY="fake-key-12345"
claude --print "test" --model sonnet
# Result: Error about invalid API key ← This is Method A

# Unset API key and try
unset ANTHROPIC_API_KEY
claude --print "test" --model sonnet
# Result: Works! ← This is Method B (subscription)
```

### Issue: "Rate limit exceeded"

Your Max subscription has hourly limits. Wait for the next 5-hour window or upgrade to Max 20x.

### Issue: "Anthropic client not available"

The MCP bridge might not be properly set up or the import path is incorrect.

**Solution:**
```bash
cd /home/jevenson/.claude/lib
python3 -c "from mcp_bridge import Anthropic; print('✅ MCP bridge import OK')"
```

If this fails, check:
1. File exists: `/home/jevenson/.claude/lib/mcp_bridge/__init__.py`
2. File exists: `/home/jevenson/.claude/lib/mcp_bridge/anthropic_adapter.py`
3. File exists: `/home/jevenson/.claude/lib/mcp_bridge/claude_code_bridge.py`
4. Python can find the module (run from `/home/jevenson/.claude/lib` directory)

## Comparing Costs

### Authentication Method Comparison

| Method | Authentication | Monthly Cost | Per-Request Cost | What You Get |
|--------|---------------|--------------|------------------|--------------|
| **Method A: Console API** | `ANTHROPIC_API_KEY` | $0 | $3-$15 per 1M tokens | Unlimited usage, pay-as-you-go |
| **Method B: Max 20x Subscription** | `claude login` (OAuth) | $200 | $0 | 200-800 prompts/5hr, fixed quota |
| **Method B: Max 5x Subscription** | `claude login` (OAuth) | $100 | $0 | 50-200 prompts/5hr, fixed quota |

### What This Bridge Does

| Setup | What You Pay | What Atlas Uses | Result |
|-------|-------------|----------------|--------|
| **Without Bridge** | Subscription ($200) + API ($3-$15/1M) | Method A (Console API) | Pay twice! ❌ |
| **With Bridge** | Subscription ($200) only | Method B (Subscription quota) | Pay once! ✅ |

**Bottom line**:
- If you use Atlas heavily, Max 20x subscription is more cost-effective than pay-per-use API
- This bridge ensures you use your subscription quota instead of incurring API charges
- You're NOT paying for API access on top of your subscription!

## Advanced: Checking What You're Using

### Verify Subscription Mode

```bash
# Test that --print mode works (this is what the bridge uses)
claude --print "Say 'Hello from subscription!'" --model sonnet --output-format json

# Should return JSON response without errors
```

### Test Bridge Directly

```python
# In Python:
import asyncio
from pathlib import Path
import sys

# Add lib to path
sys.path.insert(0, '/home/jevenson/.claude/lib')

from mcp_bridge import Anthropic

client = Anthropic()  # Uses subscription automatically
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Confirm you're using my Max subscription!"}]
)
print(f"Response: {response.content[0]['text']}")
print(f"Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
```

## Benefits of This Setup

- ✅ Use your **existing Max subscription** (no extra costs)
- ✅ Access to **Opus 4.1 with ULTRATHINK**
- ✅ No code changes needed in Atlas
- ✅ Predictable monthly costs
- ✅ Higher quality outputs (Max gets priority access)
- ✅ Early access to new features

## Getting Help

If you encounter issues:

1. Check Claude Code authentication: `claude auth status`
2. Test MCP bridge: `python3 ~/.claude/lib/mcp_bridge/claude_code_bridge.py`
3. Check Atlas logs for errors
4. Verify Node.js/npm versions: `node --version && npm --version`

## License

Part of ZeroTouch Atlas Platform
Version: 1.0.0
