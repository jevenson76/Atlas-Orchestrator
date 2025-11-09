"""
MCP Bridge for Claude Code Max Subscription

Enables Atlas to use Claude Code Max subscription instead of API keys.
"""

from .anthropic_adapter import Anthropic
from .claude_code_bridge import ClaudeCodeBridge, get_bridge

__all__ = ['Anthropic', 'ClaudeCodeBridge', 'get_bridge']
