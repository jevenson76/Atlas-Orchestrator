"""
Core agent system components for multi-agent orchestration.

Provides base classes and utilities for building robust AI agent systems
with cost tracking, error handling, and retry logic.
"""

import os
import time
import random
import logging
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

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
    logging.warning("anthropic package not installed. Install with: pip install anthropic")

# Import centralized model selection
from core.models import ModelSelector
from core.constants import Models, Limits

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states for API protection."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class ModelPricing:
    """Model pricing information per 1M tokens."""

    PRICING = {
        # Claude models (input, output per 1M tokens)
        Models.HAIKU: (0.25, 1.25),
        Models.SONNET: (3.00, 15.00),
        Models.OPUS: (15.00, 75.00),
        'claude-3-haiku-20240307': (0.25, 1.25),  # Legacy model
        'claude-3-sonnet-20240229': (3.00, 15.00),  # Legacy model

        # Shorthand aliases
        'haiku': (0.25, 1.25),
        'sonnet': (3.00, 15.00),
        'opus': (15.00, 75.00),

        # Grok models (xAI)
        Models.GROK_3: (3.00, 15.00),
        Models.GROK_2: (2.00, 10.00),
        Models.GROK_2_VISION: (2.00, 10.00),
        'grok-3': (3.00, 15.00),
        'grok-beta': (3.00, 15.00),  # Deprecated
        'grok-2-1212': (2.00, 10.00),
        'grok-2-vision-1212': (2.00, 10.00),

        # GPT models for reference
        'gpt-4': (30.00, 60.00),
        'gpt-4-turbo': (10.00, 30.00),
        'gpt-3.5-turbo': (0.50, 1.50),
    }

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for token usage.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pricing = cls.PRICING.get(model, (0, 0))
        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        return round(input_cost + output_cost, 6)


@dataclass
class AgentMetrics:
    """Metrics tracking for an individual agent."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost: float = 0.0
    total_latency: float = 0.0

    calls_by_model: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    costs_by_model: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    last_call_time: Optional[datetime] = None
    last_error: Optional[str] = None

    def record_call(self, model: str, tokens_in: int, tokens_out: int,
                   cost: float, latency: float, success: bool = True,
                   error: Optional[str] = None):
        """Record metrics for a call."""
        self.total_calls += 1

        if success:
            self.successful_calls += 1
            self.total_tokens_in += tokens_in
            self.total_tokens_out += tokens_out
            self.total_cost += cost
            self.total_latency += latency
            self.calls_by_model[model] += 1
            self.costs_by_model[model] += cost
        else:
            self.failed_calls += 1
            if error:
                error_type = type(error).__name__ if not isinstance(error, str) else error
                self.errors_by_type[error_type] += 1
                self.last_error = str(error)

        self.last_call_time = datetime.now()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of metrics."""
        success_rate = (self.successful_calls / max(self.total_calls, 1)) * 100
        avg_latency = self.total_latency / max(self.successful_calls, 1)

        return {
            'total_calls': self.total_calls,
            'success_rate': round(success_rate, 2),
            'total_tokens': self.total_tokens_in + self.total_tokens_out,
            'total_cost': round(self.total_cost, 6),
            'avg_cost_per_call': round(self.total_cost / max(self.successful_calls, 1), 6),
            'avg_latency': round(avg_latency, 2),
            'models_used': list(self.calls_by_model.keys()),
            'error_rate': round((self.failed_calls / max(self.total_calls, 1)) * 100, 2),
            'last_call': self.last_call_time.isoformat() if self.last_call_time else None
        }


class CostTracker:
    """
    Track costs across multiple agents with budgets and alerts.

    Features:
    - Per-agent cost tracking
    - Daily/hourly budget limits
    - Alert thresholds
    - Cost breakdown by model
    """

    def __init__(self,
                 daily_budget: float = 10.0,
                 hourly_budget: Optional[float] = None,
                 alert_threshold: float = 0.8):
        """
        Initialize cost tracker.

        Args:
            daily_budget: Maximum daily spend in USD
            hourly_budget: Optional hourly spend limit
            alert_threshold: Alert when this fraction of budget used (0.8 = 80%)
        """
        self.daily_budget = daily_budget
        self.hourly_budget = hourly_budget
        self.alert_threshold = alert_threshold

        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.start_of_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

        self.alerts_sent = {
            'daily': False,
            'hourly': False
        }

        logger.info(f"CostTracker initialized with daily budget: ${daily_budget:.2f}")

    def track(self, agent_id: str, model: str, tokens_in: int, tokens_out: int,
             cost: float, latency: float = 0.0, success: bool = True,
             error: Optional[str] = None):
        """
        Track a new API call.

        Args:
            agent_id: Unique identifier for the agent
            model: Model used
            tokens_in: Input tokens consumed
            tokens_out: Output tokens generated
            cost: Cost in USD
            latency: Call latency in seconds
            success: Whether call succeeded
            error: Error message if failed
        """
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics()

        self.agent_metrics[agent_id].record_call(
            model, tokens_in, tokens_out, cost, latency, success, error
        )

        # Check budgets
        self._check_budgets()

    def _check_budgets(self):
        """Check budget limits and send alerts."""
        now = datetime.now()

        # Reset daily tracking if new day
        if now.date() > self.start_of_day.date():
            self.start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.alerts_sent['daily'] = False

        # Reset hourly tracking if new hour
        if now.hour > self.start_of_hour.hour or now.date() > self.start_of_hour.date():
            self.start_of_hour = now.replace(minute=0, second=0, microsecond=0)
            self.alerts_sent['hourly'] = False

        # Check daily budget
        daily_cost = self.get_period_cost(self.start_of_day)

        if daily_cost > self.daily_budget:
            logger.error(f"💸 DAILY BUDGET EXCEEDED! Spent: ${daily_cost:.2f} / ${self.daily_budget:.2f}")
        elif daily_cost > self.daily_budget * self.alert_threshold and not self.alerts_sent['daily']:
            logger.warning(f"⚠️ Approaching daily budget: ${daily_cost:.2f} / ${self.daily_budget:.2f}")
            self.alerts_sent['daily'] = True

        # Check hourly budget if set
        if self.hourly_budget:
            hourly_cost = self.get_period_cost(self.start_of_hour)

            if hourly_cost > self.hourly_budget:
                logger.error(f"💸 HOURLY BUDGET EXCEEDED! Spent: ${hourly_cost:.2f} / ${self.hourly_budget:.2f}")
            elif hourly_cost > self.hourly_budget * self.alert_threshold and not self.alerts_sent['hourly']:
                logger.warning(f"⚠️ Approaching hourly budget: ${hourly_cost:.2f} / ${self.hourly_budget:.2f}")
                self.alerts_sent['hourly'] = True

    def get_period_cost(self, start_time: datetime) -> float:
        """Get total cost since a given time."""
        total = 0.0
        for metrics in self.agent_metrics.values():
            # This is simplified - for production, track individual calls
            if metrics.last_call_time and metrics.last_call_time >= start_time:
                # Approximate cost for the period
                total += metrics.total_cost
        return total

    def get_agent_cost(self, agent_id: str) -> float:
        """Get total cost for a specific agent."""
        if agent_id in self.agent_metrics:
            return self.agent_metrics[agent_id].total_cost
        return 0.0

    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive cost report."""
        daily_cost = self.get_period_cost(self.start_of_day)
        hourly_cost = self.get_period_cost(self.start_of_hour) if self.hourly_budget else 0

        return {
            'daily_budget': self.daily_budget,
            'daily_spent': round(daily_cost, 2),
            'daily_remaining': round(self.daily_budget - daily_cost, 2),
            'hourly_budget': self.hourly_budget,
            'hourly_spent': round(hourly_cost, 2) if self.hourly_budget else None,
            'agents': {
                agent_id: metrics.get_summary()
                for agent_id, metrics in self.agent_metrics.items()
            },
            'total_agents': len(self.agent_metrics),
            'alert_threshold': self.alert_threshold
        }


class CircuitBreaker:
    """
    Prevent cascading failures during API overload.

    Implements the circuit breaker pattern to fail fast when
    the API is experiencing issues, preventing unnecessary retries.
    """

    def __init__(self,
                 failure_threshold: int = Limits.CIRCUIT_BREAKER_THRESHOLD,
                 recovery_timeout: int = Limits.DEFAULT_TIMEOUT,
                 expected_exception: type = Exception):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            expected_exception: Exception type to catch (default: all)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.success_count = 0

        logger.info(f"CircuitBreaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")

    def call(self, func, *args, **kwargs):
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
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: HALF_OPEN - Testing recovery")
            else:
                time_remaining = self.recovery_timeout - (datetime.now() - self.last_failure_time).total_seconds()
                raise Exception(f"Circuit breaker OPEN - service unavailable (retry in {time_remaining:.0f}s)")

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        return (
            self.last_failure_time and
            (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout
        )

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # Require 2 successes to fully close
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker: CLOSED - Service recovered")
        else:
            self.failure_count = max(0, self.failure_count - 1)  # Decay failures on success

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.error("Circuit breaker: OPEN - Recovery test failed")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker: OPEN - Threshold reached ({self.failure_count} failures)")

    def reset(self):
        """Manually reset the circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker: Manually reset to CLOSED")

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'threshold': self.failure_threshold,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class ExponentialBackoff:
    """
    Exponential backoff with jitter for retry logic.

    Implements exponential backoff with optional jitter to prevent
    thundering herd problem during API recovery.
    """

    def __init__(self,
                 base_delay: float = 1.0,
                 max_delay: float = float(Limits.DEFAULT_TIMEOUT),
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        """
        Initialize backoff strategy.

        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Exponential growth factor
            jitter: Add random jitter to prevent thundering herd
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        Get delay for given attempt number.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Calculate exponential delay
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)  # Ensure non-negative


class BaseAgent:
    """
    Base class for all AI agents with built-in resilience and monitoring.

    Features:
    - Automatic retries with exponential backoff
    - Circuit breaker for API protection
    - Cost tracking and budget enforcement
    - Comprehensive logging and metrics
    - Support for multiple models
    """

    def __init__(self,
                 role: str,
                 model: str = Models.HAIKU,
                 api_key: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2048,
                 max_retries: int = Limits.MAX_RETRIES,
                 use_circuit_breaker: bool = True,
                 cost_tracker: Optional[CostTracker] = None,
                 system_prompt: Optional[str] = None):
        """
        Initialize base agent.

        Args:
            role: Agent's role/purpose
            model: Model to use
            api_key: API key (uses env var if not provided)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response tokens
            max_retries: Maximum retry attempts
            use_circuit_breaker: Enable circuit breaker
            cost_tracker: Optional shared cost tracker
            system_prompt: Optional custom system prompt
        """
        self.role = role
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.system_prompt = system_prompt

        # Initialize client
        if ANTHROPIC_AVAILABLE:
            api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
            self.client = Anthropic(api_key=api_key) if api_key else None
        else:
            self.client = None
            logger.warning("Anthropic client not available - install with: pip install anthropic")

        # Initialize resilience components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=Limits.CIRCUIT_BREAKER_THRESHOLD,
            recovery_timeout=Limits.DEFAULT_TIMEOUT,
            expected_exception=Exception
        ) if use_circuit_breaker else None

        self.backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )

        # Initialize tracking
        self.cost_tracker = cost_tracker or CostTracker()
        self.agent_id = f"{role}_{model}_{id(self)}"
        self.local_metrics = AgentMetrics()

        logger.info(f"Agent initialized: {self.agent_id} with model {model}")

    def call(self,
             prompt: str,
             context: Optional[Dict[str, Any]] = None,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Make API call with full resilience and tracking.

        Args:
            prompt: User prompt
            context: Additional context
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Dictionary with output, tokens, cost, and metadata
        """
        if not self.client:
            error_msg = "Anthropic client not available. Set ANTHROPIC_API_KEY or install anthropic package."
            logger.error(error_msg)
            return {'output': None, 'error': error_msg, 'success': False}

        # Build system prompt
        system = self._build_system_prompt(context)

        # Override defaults if provided
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        # Retry loop with backoff
        for attempt in range(self.max_retries):
            start_time = time.time()

            try:
                # Use circuit breaker if enabled
                if self.circuit_breaker:
                    response = self.circuit_breaker.call(
                        self._make_api_call,
                        prompt, system, temperature, max_tokens
                    )
                else:
                    response = self._make_api_call(
                        prompt, system, temperature, max_tokens
                    )

                # Calculate metrics
                latency = time.time() - start_time
                cost = ModelPricing.calculate_cost(
                    self.model,
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )

                # Track success
                self.cost_tracker.track(
                    self.agent_id,
                    self.model,
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    cost,
                    latency,
                    success=True
                )

                self.local_metrics.record_call(
                    self.model,
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    cost,
                    latency,
                    success=True
                )

                logger.info(f"API call successful: {self.agent_id} (attempt {attempt + 1}, cost: ${cost:.6f})")

                return {
                    'output': response.content[0].text,
                    'tokens_in': response.usage.input_tokens,
                    'tokens_out': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                    'cost': cost,
                    'model': self.model,
                    'attempt': attempt + 1,
                    'latency': round(latency, 2),
                    'success': True
                }

            except RateLimitError as e:
                logger.warning(f"Rate limit hit (attempt {attempt + 1}): {e}")
                error_type = "RateLimitError"

            except APITimeoutError as e:
                logger.warning(f"API timeout (attempt {attempt + 1}): {e}")
                error_type = "APITimeoutError"

            except APIConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                error_type = "APIConnectionError"

            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                error_type = type(e).__name__

            # Track failure
            latency = time.time() - start_time
            self.local_metrics.record_call(
                self.model, 0, 0, 0, latency,
                success=False,
                error=error_type
            )

            # Retry logic
            if attempt < self.max_retries - 1:
                delay = self.backoff.get_delay(attempt)
                logger.info(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {self.max_retries} attempts failed for {self.agent_id}")
                return {
                    'output': None,
                    'error': error_type,
                    'attempts': self.max_retries,
                    'success': False
                }

    def _build_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Build system prompt with role and context."""
        if self.system_prompt:
            system = self.system_prompt
        else:
            system = f"You are {self.role}."

        if context:
            context_str = json.dumps(context, indent=2) if isinstance(context, dict) else str(context)
            system += f"\n\nContext:\n{context_str}"

        return system

    def _make_api_call(self, prompt: str, system: str,
                      temperature: float, max_tokens: int):
        """Make the actual API call."""
        return self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent's performance metrics."""
        circuit_status = self.circuit_breaker.get_status() if self.circuit_breaker else None

        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'model': self.model,
            'metrics': self.local_metrics.get_summary(),
            'circuit_breaker': circuit_status
        }

    def reset(self):
        """Reset agent state and metrics."""
        self.local_metrics = AgentMetrics()
        if self.circuit_breaker:
            self.circuit_breaker.reset()
        logger.info(f"Agent reset: {self.agent_id}")