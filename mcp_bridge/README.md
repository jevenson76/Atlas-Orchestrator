# MCP Bridge for Claude Code Max Subscription

This bridge allows Atlas to use your **Claude Code Max subscription** instead of requiring separate Anthropic API keys.

## Architecture

```
Atlas Streamlit App
    ↓
Anthropic SDK Adapter (drop-in replacement)
    ↓
Claude Code Bridge
    ↓
Claude Code CLI
    ↓
Your Max Subscription (OAuth authenticated)
```

## Setup

### 1. Install Claude Code CLI

```bash
npm install -g @anthropics/claude-code
```

### 2. Authenticate with Your Max Subscription

**IMPORTANT**: Use your subscription, NOT an API key!

```bash
# Logout first if you have an API key configured
claude logout

# Login with your Max subscription
claude login
```

When prompted, authenticate with your **Claude Max account** (NOT Console/API credentials).

### 3. Verify Authentication

```bash
claude auth status
```

Should show you're logged in with a subscription (not an API key).

### 4. Test the Bridge

```bash
cd /home/jevenson/.claude/lib/mcp_bridge
python3 claude_code_bridge.py
```

Should successfully call Claude via your subscription!

## Usage in Atlas

The bridge provides a drop-in replacement for the Anthropic SDK:

```python
# OLD WAY (requires API key):
from anthropic import Anthropic
client = Anthropic(api_key="sk-ant-...")

# NEW WAY (uses Max subscription):
from mcp_bridge import Anthropic
client = Anthropic()  # No API key needed!

# Same API calls work:
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## How It Works

1. **anthropic_adapter.py**: Provides drop-in replacement for Anthropic SDK
2. **claude_code_bridge.py**: Bridges to Claude Code CLI
3. **Claude Code CLI**: Authenticated with your Max subscription via OAuth
4. **Atlas gets responses** without needing separate API credits!

## Benefits

- ✅ Use your **existing Max subscription** (no extra API costs)
- ✅ Access to **Opus 4.1 ULTRATHINK** included in Max
- ✅ No code changes needed in Atlas (drop-in replacement)
- ✅ **200-800 prompts every 5 hours** (Max 20x plan)

## Troubleshooting

### "Claude Code CLI not found"

Install it:
```bash
npm install -g @anthropics/claude-code
```

### "Not authenticated"

Login with your subscription:
```bash
claude logout
claude login
```

### "Using API key instead of subscription"

You need to logout and re-login with subscription credentials:
```bash
claude logout
claude login
# Choose subscription authentication (NOT Console API)
```

### Check what you're using:

```bash
claude auth status
```

Should show "subscription" not "api_key".

## Model Names

The bridge automatically maps API model names to Claude Code names:

| API Model | Claude Code Name |
|-----------|------------------|
| `claude-3-5-sonnet-20241022` | `sonnet-4` |
| `claude-opus-4-20250514` | `opus-4` |
| `claude-3-opus-20240229` | `opus-3` |

## Rate Limits

Your Max subscription limits:
- **Max 5x ($100/month)**: ~50-200 prompts per 5 hours
- **Max 20x ($200/month)**: ~200-800 prompts per 5 hours

The bridge will use your subscription quota instead of API credits.

## License

Part of ZeroTouch Atlas Platform
