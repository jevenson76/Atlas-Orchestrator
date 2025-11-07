"""
Shared constants used across the Claude library.

These constants eliminate hardcoding and ensure consistency
across all modules.
"""


class Models:
    """Claude model identifiers."""
    HAIKU = "claude-3-5-haiku-20241022"
    SONNET = "claude-3-5-sonnet-20241022"
    OPUS = "claude-3-opus-20240229"
    OPUS_4 = "claude-opus-4-20250514"  # Opus 4.1 - Extended thinking with ultrathink

    # Grok models (xAI)
    GROK_3 = "grok-3"  # Latest general model
    GROK_2 = "grok-2-1212"
    GROK_2_VISION = "grok-2-vision-1212"
    GROK_BETA = "grok-beta"  # Deprecated (kept for backwards compatibility)


class Limits:
    """System limits and thresholds."""
    MAX_RETRIES = 3
    CIRCUIT_BREAKER_THRESHOLD = 5
    DEFAULT_TIMEOUT = 60