"""
Enhanced Resilience Components for Multi-LLM Agent Systems

PRIORITY 1: Resilience Against Rate Limits
- CircuitBreaker with full state machine (CLOSED→OPEN→HALF_OPEN)
- Dynamic Model Fallback (Opus/Sonnet → Haiku → Gemini → OpenAI)
- BaseAgent with diversification interfaces

Security Focus:
- Zero-trust delegation
- Input sanitization
- Scope restriction enforcement
"""

import os
import time
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json

try:
    from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError, APITimeoutError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    APIError = Exception
    APIConnectionError = Exception
    RateLimitError = Exception
    APITimeoutError = Exception
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

# xAI support via OpenAI SDK (OpenAI-compatible API)
XAI_AVAILABLE = OPENAI_AVAILABLE  # xAI uses OpenAI SDK with custom base_url

from core.constants import Models, Limits

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states with full state machine."""
    CLOSED = "closed"          # Normal operation, requests pass through
    OPEN = "open"              # Failing, reject all requests immediately
    HALF_OPEN = "half_open"    # Testing recovery, allow limited requests


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0  # Rejected while circuit is OPEN

    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    failure_times: List[datetime] = field(default_factory=list)
    recovery_attempts: int = 0

    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    time_in_open_state: float = 0.0

    def record_call(self, success: bool, state: CircuitState):
        """Record a call result."""
        self.total_calls += 1

        if success:
            self.successful_calls += 1
            self.last_success_time = datetime.now()
        else:
            self.failed_calls += 1
            self.last_failure_time = datetime.now()
            self.failure_times.append(datetime.now())

    def record_state_change(self, from_state: CircuitState, to_state: CircuitState, reason: str):
        """Record state transition."""
        self.state_changes.append({
            'timestamp': datetime.now().isoformat(),
            'from': from_state.value,
            'to': to_state.value,
            'reason': reason
        })

    def record_rejection(self):
        """Record a rejected call."""
        self.rejected_calls += 1

    def get_failure_rate(self, window_seconds: int = 60) -> float:
        """Calculate failure rate within time window."""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        recent_failures = [f for f in self.failure_times if f >= cutoff]

        total_recent = len([f for f in self.failure_times if f >= cutoff])
        if total_recent == 0:
            return 0.0

        return len(recent_failures) / total_recent

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        success_rate = (self.successful_calls / max(self.total_calls, 1)) * 100

        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'rejected_calls': self.rejected_calls,
            'success_rate': round(success_rate, 2),
            'state_changes': len(self.state_changes),
            'recovery_attempts': self.recovery_attempts,
            'time_in_open_state': round(self.time_in_open_state, 2),
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success': self.last_success_time.isoformat() if self.last_success_time else None
        }


class EnhancedCircuitBreaker:
    """
    Enhanced circuit breaker with full state machine for API resilience.

    State Transitions:
    - CLOSED → OPEN: When failure threshold is exceeded
    - OPEN → HALF_OPEN: After recovery timeout expires
    - HALF_OPEN → CLOSED: When test requests succeed
    - HALF_OPEN → OPEN: When test requests fail

    Features:
    - Configurable failure threshold and recovery timeout
    - Automatic state transitions
    - Detailed metrics tracking
    - Support for partial failures (degraded mode)
    - Integration with model fallback system
    """

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 half_open_max_calls: int = 3,
                 success_threshold: int = 2,
                 expected_exception: type = Exception):
        """
        Initialize enhanced circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            half_open_max_calls: Max requests allowed in HALF_OPEN state
            success_threshold: Successes needed in HALF_OPEN to close circuit
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0

        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()

        self.metrics = CircuitBreakerMetrics()

        logger.info(f"Enhanced CircuitBreaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: Circuit breaker OPEN or function failed
        """
        # Check circuit state before attempting call
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self.metrics.record_rejection()
                time_remaining = self._time_until_retry()
                raise Exception(
                    f"Circuit breaker OPEN - service unavailable "
                    f"(retry in {time_remaining:.0f}s, failures: {self.failure_count}/{self.failure_threshold})"
                )

        # HALF_OPEN state: limit number of test calls
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                self.metrics.record_rejection()
                raise Exception(
                    f"Circuit breaker HALF_OPEN - max test calls reached "
                    f"({self.half_open_calls}/{self.half_open_max_calls})"
                )
            self.half_open_calls += 1

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            self.metrics.record_call(success=True, state=self.state)
            return result

        except self.expected_exception as e:
            self._on_failure()
            self.metrics.record_call(success=False, state=self.state)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if not self.last_failure_time:
            return False

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _time_until_retry(self) -> float:
        """Calculate time remaining until retry attempt."""
        if not self.last_failure_time:
            return 0.0

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0.0, self.recovery_timeout - elapsed)

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state for recovery testing."""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        self.last_state_change = datetime.now()

        self.metrics.record_state_change(old_state, self.state, "Recovery timeout expired")
        self.metrics.recovery_attempts += 1

        logger.info(f"Circuit breaker: {old_state.value} → HALF_OPEN (testing recovery)")

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.success_threshold:
                # Enough successes to close circuit
                self._transition_to_closed()

        elif self.state == CircuitState.CLOSED:
            # Decay failure count on success
            self.failure_count = max(0, self.failure_count - 1)

    def _transition_to_closed(self):
        """Transition to CLOSED state (normal operation)."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_state_change = datetime.now()

        self.metrics.record_state_change(old_state, self.state, "Service recovered")

        logger.info(f"Circuit breaker: {old_state.value} → CLOSED (service recovered)")

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Recovery test failed, reopen circuit
            self._transition_to_open("Recovery test failed")

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open("Failure threshold reached")

    def _transition_to_open(self, reason: str):
        """Transition to OPEN state (reject all requests)."""
        old_state = self.state

        # Track time spent in OPEN state
        if old_state != CircuitState.OPEN:
            self.last_state_change = datetime.now()

        self.state = CircuitState.OPEN
        self.success_count = 0
        self.half_open_calls = 0

        self.metrics.record_state_change(old_state, self.state, reason)

        logger.error(
            f"Circuit breaker: {old_state.value} → OPEN ({reason}, "
            f"failures: {self.failure_count}/{self.failure_threshold})"
        )

    def force_open(self, reason: str = "Manual override"):
        """Manually open the circuit."""
        self._transition_to_open(reason)

    def force_close(self, reason: str = "Manual override"):
        """Manually close the circuit."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None

        self.metrics.record_state_change(old_state, self.state, reason)

        logger.info(f"Circuit breaker: {old_state.value} → CLOSED (manual reset)")

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive circuit breaker status."""
        status = {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'success_count': self.success_count,
            'success_threshold': self.success_threshold,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'time_until_retry': round(self._time_until_retry(), 1) if self.state == CircuitState.OPEN else 0,
            'metrics': self.metrics.get_summary()
        }

        if self.state == CircuitState.HALF_OPEN:
            status['half_open_calls'] = self.half_open_calls
            status['half_open_max_calls'] = self.half_open_max_calls

        return status


class ModelFallbackChain:
    """
    Dynamic model fallback system for resilience.

    Fallback order: Opus/Sonnet → Haiku → Gemini → OpenAI

    Features:
    - Automatic fallback on rate limits or failures
    - Per-model circuit breakers
    - Cost tracking across providers
    - Performance metrics
    """

    def __init__(self,
                 primary_model: str = Models.SONNET,
                 enable_cross_provider: bool = True):
        """
        Initialize fallback chain.

        Args:
            primary_model: Preferred model to use
            enable_cross_provider: Allow fallback to other providers
        """
        self.primary_model = primary_model
        self.enable_cross_provider = enable_cross_provider

        # Primary fallback chain (Claude models - authentication required)
        self.anthropic_chain = [Models.OPUS_4, Models.SONNET, Models.OPUS]

        # Cross-provider fallbacks (if enabled and auth fails)
        self.cross_provider_chain = []
        if enable_cross_provider:
            # Add Gemini, xAI, and OpenAI as fallbacks
            if GEMINI_AVAILABLE:
                self.cross_provider_chain.extend([Models.GEMINI_PRO, Models.GEMINI_EXP, Models.GEMINI_FLASH])
            if XAI_AVAILABLE:
                self.cross_provider_chain.extend([Models.GROK_3, Models.GROK_2])
            if OPENAI_AVAILABLE:
                self.cross_provider_chain.extend(['gpt-4o', 'gpt-4-turbo'])

        # Per-model circuit breakers
        self.circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}
        self._initialize_circuit_breakers()

        # Fallback metrics
        self.fallback_counts: Dict[str, int] = defaultdict(int)
        self.successful_calls: Dict[str, int] = defaultdict(int)

        logger.info(
            f"ModelFallbackChain initialized: primary={primary_model}, "
            f"cross_provider={enable_cross_provider}"
        )

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each model."""
        all_models = self.anthropic_chain + self.cross_provider_chain

        for model in all_models:
            self.circuit_breakers[model] = EnhancedCircuitBreaker(
                failure_threshold=3,  # More aggressive for fallback
                recovery_timeout=30,   # Faster recovery attempts
                half_open_max_calls=2,
                success_threshold=2
            )

    def get_available_model(self) -> Tuple[str, str]:
        """
        Get the next available model to use.

        Returns:
            Tuple of (model_name, provider)

        Raises:
            Exception: No available models
        """
        # Try Anthropic chain first (authentication required)
        for model in self.anthropic_chain:
            breaker = self.circuit_breakers[model]
            if breaker.get_state() != CircuitState.OPEN:
                return (model, 'anthropic')

        # Try cross-provider fallbacks if enabled
        if self.enable_cross_provider:
            for model in self.cross_provider_chain:
                breaker = self.circuit_breakers[model]
                if breaker.get_state() != CircuitState.OPEN:
                    # Determine provider from model name
                    if 'grok' in model.lower():
                        provider = 'xai'
                    elif 'gemini' in model.lower():
                        provider = 'gemini'
                    elif 'gpt' in model.lower():
                        provider = 'openai'
                    else:
                        provider = 'openai'  # default
                    return (model, provider)

        raise Exception(
            "No available models - all circuit breakers are OPEN. "
            "Service temporarily unavailable."
        )

    def call_with_fallback(self,
                          func: Callable,
                          model: str,
                          *args,
                          **kwargs) -> Dict[str, Any]:
        """
        Call function with automatic fallback on failure.

        Args:
            func: Function to call (must accept model parameter)
            model: Preferred model
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Dict with result and metadata
        """
        attempted_models = []
        last_error = None

        # Start with requested model
        current_model = model
        provider = 'anthropic'

        while True:
            attempted_models.append(current_model)
            breaker = self.circuit_breakers[current_model]

            try:
                # Try with circuit breaker protection
                result = breaker.call(func, current_model, *args, **kwargs)

                self.successful_calls[current_model] += 1

                return {
                    'result': result,
                    'model_used': current_model,
                    'provider': provider,
                    'attempted_models': attempted_models,
                    'fallback_occurred': current_model != model,
                    'success': True
                }

            except RateLimitError as e:
                logger.warning(f"Rate limit hit on {current_model}: {e}")
                last_error = e
                self.fallback_counts[current_model] += 1

            except Exception as e:
                logger.error(f"Error with {current_model}: {e}")
                last_error = e
                self.fallback_counts[current_model] += 1

            # Try next model in chain
            try:
                current_model, provider = self.get_available_model()

                if current_model in attempted_models:
                    # Already tried this model, all models exhausted
                    break

                logger.info(f"Falling back to {current_model} ({provider})")

            except Exception as e:
                logger.error(f"No available fallback models: {e}")
                break

        # All models failed
        return {
            'result': None,
            'model_used': None,
            'provider': None,
            'attempted_models': attempted_models,
            'fallback_occurred': True,
            'success': False,
            'error': str(last_error)
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get fallback chain metrics."""
        return {
            'primary_model': self.primary_model,
            'cross_provider_enabled': self.enable_cross_provider,
            'fallback_counts': dict(self.fallback_counts),
            'successful_calls': dict(self.successful_calls),
            'circuit_breakers': {
                model: breaker.get_status()
                for model, breaker in self.circuit_breakers.items()
            }
        }

    def reset_all_breakers(self):
        """Reset all circuit breakers."""
        for model, breaker in self.circuit_breakers.items():
            breaker.force_close("Manual reset all")

        logger.info("All circuit breakers reset")


class SecurityValidator:
    """
    Security validation for inputs and prompts.

    SECURITY MANDATES:
    - Prevent markdown/meta character confusion
    - Implement zero-trust delegation
    - Detect prompt injection attempts
    """

    # Suspicious patterns that might indicate injection
    SUSPICIOUS_PATTERNS = [
        'ignore previous instructions',
        'ignore all previous',
        'disregard previous',
        'forget everything',
        'new instructions',
        'system:',
        'assistant:',
        'user:',
        '```python',
        '```bash',
        'exec(',
        'eval(',
        '__import__',
        'subprocess',
    ]

    # Dangerous characters for markdown confusion
    DANGEROUS_CHARS = ['`', '```', '<', '>', '|', '&', ';', '$']

    @classmethod
    def sanitize_input(cls, text: str, strict: bool = False) -> str:
        """
        Sanitize user input to prevent injection attacks.

        Args:
            text: Input text to sanitize
            strict: If True, escape more aggressively

        Returns:
            Sanitized text
        """
        if not text:
            return text

        # Remove null bytes
        text = text.replace('\x00', '')

        if strict:
            # Escape markdown special characters
            for char in cls.DANGEROUS_CHARS:
                text = text.replace(char, f'\\{char}')

        return text

    @classmethod
    def detect_injection(cls, text: str) -> Tuple[bool, List[str]]:
        """
        Detect potential prompt injection attempts.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (is_suspicious, detected_patterns)
        """
        if not text:
            return (False, [])

        text_lower = text.lower()
        detected = []

        for pattern in cls.SUSPICIOUS_PATTERNS:
            if pattern in text_lower:
                detected.append(pattern)

        return (len(detected) > 0, detected)

    @classmethod
    def validate_scope(cls,
                      action: str,
                      allowed_scopes: List[str]) -> bool:
        """
        Validate that action is within allowed scope.

        Zero-trust delegation: always verify permissions.

        Args:
            action: Action to validate
            allowed_scopes: List of allowed action patterns

        Returns:
            True if action is allowed
        """
        for scope in allowed_scopes:
            if scope == '*':
                return True

            if scope.endswith('*'):
                # Wildcard match
                prefix = scope[:-1]
                if action.startswith(prefix):
                    return True
            elif action == scope:
                return True

        return False
