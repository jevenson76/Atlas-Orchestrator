"""
Shared constants used across the Claude library.

These constants eliminate hardcoding and ensure consistency
across all modules.
"""


class Models:
    """Model identifiers across providers."""
    # Claude models (Anthropic) - Available via Claude Code Max
    SONNET = "claude-3-5-sonnet-20241022"  # Balanced, high-quality
    OPUS = "claude-3-opus-20240229"  # Legacy Opus
    OPUS_4 = "claude-opus-4-20250514"  # Opus 4.1 with ULTRATHINK capability

    # Gemini models (Google)
    GEMINI_FLASH = "gemini-2.0-flash-exp"  # Fast, cheap model
    GEMINI_PRO = "gemini-1.5-pro"  # Balanced model
    GEMINI_EXP = "gemini-exp-1206"  # Experimental high-performance

    # Grok models (xAI)
    GROK_3 = "grok-3"  # Latest general model
    GROK_2 = "grok-2-1212"  # Balanced model
    GROK_2_VISION = "grok-2-vision-1212"  # Vision capabilities

    # Default model (Claude required per user)
    DEFAULT = SONNET  # Primary default (requires authentication)


class Limits:
    """System limits and thresholds."""
    MAX_RETRIES = 3
    CIRCUIT_BREAKER_THRESHOLD = 5
    DEFAULT_TIMEOUT = 60