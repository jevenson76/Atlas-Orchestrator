#!/usr/bin/env python3
"""
MCP Bridge for Claude Code Max Subscription (Refactored)

Based on claude_max methodology - uses `claude --print` mode
with subscription authentication instead of API keys.

Key Insight: By unsetting ANTHROPIC_API_KEY and using --print mode,
Claude Code falls back to subscription (OAuth) authentication.

Architecture:
    Atlas App → This Bridge → `claude --print` → Max Subscription

Author: ZeroTouch Atlas Platform
Version: 2.0.0 (Refactored)
"""

import asyncio
import json
import subprocess
import logging
import os
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeCodeBridge:
    """
    Bridge to Claude Code using Max subscription (not API keys).

    Uses `claude --print` mode which supports subscription auth.
    """

    def __init__(self):
        self.claude_path = self._find_claude_code()
        logger.info(f"✅ Claude Code CLI found at: {self.claude_path}")

    def _find_claude_code(self) -> str:
        """Find Claude Code CLI executable."""
        try:
            result = subprocess.run(
                ["which", "claude"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                # Verify it works
                test = subprocess.run(
                    [path, "--help"],
                    capture_output=True,
                    timeout=5
                )
                if test.returncode == 0:
                    return path
        except:
            pass

        raise RuntimeError(
            "❌ Claude Code CLI not found.\n"
            "Install with: npm install -g @anthropics/claude-code\n"
            "Then authenticate: claude login"
        )

    async def call_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Call Claude model via Claude Code --print mode.

        This uses your Max subscription, NOT API keys.

        Args:
            model: Model name (e.g., "claude-3-5-sonnet-20241022")
            messages: List of message dicts
            system: Optional system prompt
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            Response dict
        """
        # Build prompt from messages
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(content)

        full_prompt = "\n\n".join(prompt_parts)

        # Map model name to Claude Code alias
        model_alias = self._map_model_name(model)

        # Build command
        cmd = [
            self.claude_path,
            "--print",  # Non-interactive mode!
            "--output-format", "json",
            "--model", model_alias
        ]

        if system:
            cmd.extend(["--system-prompt", system])

        cmd.append(full_prompt)

        # CRITICAL: Remove ANTHROPIC_API_KEY to force subscription auth
        env = os.environ.copy()
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
            logger.debug("Removed ANTHROPIC_API_KEY to use subscription")

        logger.info(f"🤖 Calling Claude Code: {model_alias} (subscription mode)")

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env  # Use modified environment
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"

                # Check for common auth issues
                if "not logged in" in error_msg.lower() or "login" in error_msg.lower():
                    raise RuntimeError(
                        "❌ Not logged into Claude Code with Max subscription.\n"
                        f"Run: {self.claude_path} login\n"
                        "Authenticate with your Max account (NOT Console/API)"
                    )

                logger.error(f"Claude Code error: {error_msg}")
                raise RuntimeError(f"Claude Code failed: {error_msg}")

            # Parse JSON response
            response_text = stdout.decode()

            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If not JSON, wrap in response format
                response_data = {
                    "content": response_text,
                    "model": model,
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 0
                    }
                }

            logger.info("✅ Claude Code response received (via subscription)")
            return response_data

        except asyncio.TimeoutError:
            raise RuntimeError("Claude Code call timed out")

    def _map_model_name(self, model: str) -> str:
        """
        Map API model names to Claude Code aliases.

        Args:
            model: API model name

        Returns:
            Claude Code alias
        """
        # Direct mappings
        mappings = {
            "claude-3-5-sonnet-20241022": "sonnet",
            "claude-3-5-sonnet-20250205": "sonnet",
            "claude-opus-4-20250514": "opus",
            "claude-3-opus-20240229": "opus-3",
        }

        if model in mappings:
            return mappings[model]

        # Fuzzy matching
        model_lower = model.lower()
        if "sonnet" in model_lower:
            return "sonnet"
        elif "opus-4" in model_lower or "opus4" in model_lower:
            return "opus"
        elif "opus" in model_lower:
            return "opus-3"

        # Default
        logger.warning(f"Unknown model '{model}', defaulting to 'sonnet'")
        return "sonnet"

    async def stream_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """
        Stream Claude model response.

        Args:
            model: Model name
            messages: Message list
            system: System prompt
            max_tokens: Max tokens
            temperature: Temperature

        Yields:
            Response chunks
        """
        # Build prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(content)

        full_prompt = "\n\n".join(prompt_parts)
        model_alias = self._map_model_name(model)

        cmd = [
            self.claude_path,
            "--print",
            "--output-format", "stream-json",
            "--model", model_alias
        ]

        if system:
            cmd.extend(["--system-prompt", system])

        cmd.append(full_prompt)

        # Remove API key for subscription auth
        env = os.environ.copy()
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]

        logger.info(f"🤖 Streaming from Claude Code: {model_alias}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        # Stream line by line
        async for line in process.stdout:
            chunk_text = line.decode().strip()
            if chunk_text:
                try:
                    chunk_data = json.loads(chunk_text)
                    yield chunk_data
                except json.JSONDecodeError:
                    # Plain text chunk
                    yield {"content": chunk_text, "type": "content_block_delta"}

        await process.wait()


# Singleton
_bridge_instance: Optional[ClaudeCodeBridge] = None


def get_bridge() -> ClaudeCodeBridge:
    """Get singleton bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ClaudeCodeBridge()
    return _bridge_instance


# Test
if __name__ == "__main__":
    async def test_bridge():
        """Test the refactored bridge."""
        bridge = get_bridge()

        response = await bridge.call_model(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "user", "content": "Say 'Hello from Claude Code Max subscription!' and confirm you're using my subscription, not an API key."}
            ],
            max_tokens=100
        )

        print("✅ Bridge Test Response:")
        print(json.dumps(response, indent=2))

    asyncio.run(test_bridge())
