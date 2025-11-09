#!/usr/bin/env python3
"""
Anthropic API Adapter for Claude Code Bridge

Provides drop-in replacement for Anthropic Python SDK
that uses Claude Code Max subscription instead of API keys.

Usage:
    from mcp_bridge.anthropic_adapter import Anthropic

    client = Anthropic()  # No API key needed!
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello"}]
    )
"""

import asyncio
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass
from .claude_code_bridge import get_bridge

import logging
logger = logging.getLogger(__name__)


@dataclass
class Usage:
    """Token usage information."""
    input_tokens: int
    output_tokens: int


@dataclass
class Message:
    """Message response from Claude."""
    id: str
    type: str
    role: str
    content: List[Dict[str, Any]]
    model: str
    usage: Usage
    stop_reason: Optional[str] = None


class Messages:
    """
    Messages API compatible with Anthropic SDK.

    Routes calls through Claude Code bridge instead of API.
    """

    def __init__(self, bridge):
        self.bridge = bridge

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs
    ):
        """
        Create a message (synchronous).

        Args:
            model: Model name
            messages: List of message dicts
            max_tokens: Maximum tokens
            system: System prompt
            temperature: Sampling temperature
            stream: Whether to stream response

        Returns:
            Message object or stream iterator
        """
        # Run async call in event loop
        loop = asyncio.get_event_loop()

        if stream:
            # Return streaming iterator
            return self._create_stream_sync(
                model, messages, max_tokens, system, temperature
            )
        else:
            # Return complete message
            return loop.run_until_complete(
                self._create_async(model, messages, max_tokens, system, temperature)
            )

    async def _create_async(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        system: Optional[str],
        temperature: float
    ) -> Message:
        """Create message asynchronously."""
        response = await self.bridge.call_model(
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Extract content from response
        # Bridge returns {"type": "result", "result": "text", "usage": {...}}
        if response.get("type") == "result":
            content_text = response.get("result", "")
        else:
            content_text = response.get("content", "")

        return Message(
            id=f"msg_{hash(content_text)}",
            type="message",
            role="assistant",
            content=[{"type": "text", "text": content_text}],
            model=model,
            usage=Usage(
                input_tokens=response.get("usage", {}).get("input_tokens", 0),
                output_tokens=response.get("usage", {}).get("output_tokens", 0)
            ),
            stop_reason="end_turn"
        )

    def _create_stream_sync(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        system: Optional[str],
        temperature: float
    ) -> Iterator:
        """Create streaming response (synchronous iterator)."""
        loop = asyncio.get_event_loop()

        async def stream_generator():
            async for chunk in self.bridge.stream_model(
                model=model,
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature
            ):
                yield chunk

        # Convert async generator to sync iterator
        gen = stream_generator()

        while True:
            try:
                chunk = loop.run_until_complete(gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break


class Anthropic:
    """
    Drop-in replacement for Anthropic SDK client.

    Uses Claude Code Max subscription instead of API keys.

    Example:
        client = Anthropic()  # No api_key parameter needed!
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "Hello"}]
        )
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Anthropic client.

        Args:
            api_key: Ignored (uses Claude Code subscription)
            **kwargs: Ignored compatibility parameters
        """
        if api_key:
            logger.warning(
                "⚠️ API key provided but will be ignored. "
                "Using Claude Code Max subscription instead."
            )

        # Initialize bridge
        self.bridge = get_bridge()

        # Create messages API
        self.messages = Messages(self.bridge)

        logger.info("✅ Anthropic client initialized (via Claude Code bridge)")


# For compatibility with existing imports
APIError = Exception
APIConnectionError = ConnectionError
RateLimitError = Exception
APITimeoutError = TimeoutError


# Example usage
if __name__ == "__main__":
    # Test the adapter
    client = Anthropic()  # No API key needed!

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Hello! Confirm you're using Claude Code Max."}
        ]
    )

    print("✅ Adapter Test Response:")
    print(f"Role: {response.role}")
    print(f"Content: {response.content[0]['text']}")
    print(f"Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
