"""
Resilient BaseAgent with Multi-Provider Support and Security Hardening

PRIORITY 1: Complete resilience implementation
- Circuit breaker integration
- Dynamic model fallback (Anthropic → Gemini → OpenAI)
- Security validation (injection detection, input sanitization)
- Cost tracking with budget protection
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field

try:
    from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError, APITimeoutError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
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

from resilience import EnhancedCircuitBreaker, ModelFallbackChain, SecurityValidator
from agent_system import CostTracker, ExponentialBackoff, ModelPricing
from core.constants import Models, Limits
from api_config import APIConfig
from output_styles_manager import OutputStylesManager, OutputStyleValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CallResult:
    """Structured result from agent call."""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None

    # Provider information
    model_used: Optional[str] = None
    provider: str = 'anthropic'
    fallback_occurred: bool = False
    attempted_models: List[str] = field(default_factory=list)

    # Performance metrics
    tokens_in: int = 0
    tokens_out: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency: float = 0.0
    attempt: int = 1

    # Security information
    injection_detected: bool = False
    detected_patterns: List[str] = field(default_factory=list)
    input_sanitized: bool = False

    # Output style information
    output_style: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'model_used': self.model_used,
            'provider': self.provider,
            'fallback_occurred': self.fallback_occurred,
            'attempted_models': self.attempted_models,
            'tokens_in': self.tokens_in,
            'tokens_out': self.tokens_out,
            'total_tokens': self.total_tokens,
            'cost': self.cost,
            'latency': round(self.latency, 3),
            'attempt': self.attempt,
            'injection_detected': self.injection_detected,
            'detected_patterns': self.detected_patterns,
            'input_sanitized': self.input_sanitized,
            'output_style': self.output_style
        }


class ResilientBaseAgent:
    """
    Production-ready agent with full resilience and security features.

    Features:
    - Output Styles: Deterministic behavior control via system prompts
    - Multi-provider support (Anthropic, Gemini, OpenAI)
    - Automatic fallback on rate limits or failures
    - Circuit breaker protection per model
    - Security validation (injection detection, sanitization)
    - Cost tracking with budget enforcement
    - Comprehensive metrics and logging

    Output Styles:
    - Explicit control over agent behavior through system prompts
    - 8 core styles: code, detailed, json_strict, validator, critic, architect, analyst, orchestrator
    - Auto-recommendation based on agent role
    - Usage tracking and analytics
    """

    def __init__(self,
                 role: str,
                 model: str = Models.SONNET,
                 temperature: float = 0.7,
                 max_tokens: int = 2048,
                 max_retries: int = 3,
                 enable_fallback: bool = True,
                 enable_security: bool = True,
                 cost_tracker: Optional[CostTracker] = None,
                 system_prompt: Optional[str] = None,
                 output_style: Optional[str] = None,
                 allowed_scopes: Optional[List[str]] = None):
        """
        Initialize resilient agent.

        Args:
            role: Agent's role/purpose
            model: Preferred model to use
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response tokens
            max_retries: Maximum retry attempts
            enable_fallback: Enable multi-provider fallback
            enable_security: Enable security validation
            cost_tracker: Optional shared cost tracker
            system_prompt: Optional custom system prompt (overrides output_style)
            output_style: Optional output style name (e.g., 'code', 'detailed', 'critic')
            allowed_scopes: List of allowed action scopes (for zero-trust)
        """
        self.role = role
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.enable_fallback = enable_fallback
        self.enable_security = enable_security
        self.system_prompt = system_prompt
        self.output_style = output_style
        self.allowed_scopes = allowed_scopes or ['*']

        # Get API configuration
        self.api_config = APIConfig()

        # Initialize OutputStyleManager
        self.style_manager = OutputStylesManager()

        # Initialize clients
        self._initialize_clients()

        # Initialize resilience components
        # Note: ModelFallbackChain will use APIConfig internally for provider availability
        self.fallback_chain = ModelFallbackChain(
            primary_model=model,
            enable_cross_provider=enable_fallback
        ) if enable_fallback else None

        self.backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )

        # Initialize tracking
        self.cost_tracker = cost_tracker or CostTracker()
        self.agent_id = f"Resilient_{role}_{model}_{id(self)}"

        # Security validator
        self.security = SecurityValidator()

        # Call history
        self.call_history: List[CallResult] = []

        logger.info(
            f"ResilientBaseAgent initialized: {self.agent_id} "
            f"(fallback={enable_fallback}, security={enable_security})"
        )

    def _initialize_clients(self):
        """Initialize API clients for available providers using APIConfig."""

        # Anthropic
        if ANTHROPIC_AVAILABLE:
            api_key = self.api_config.get_api_key('anthropic')
            if api_key:
                self.anthropic_client = Anthropic(api_key=api_key)
                logger.debug("Anthropic client initialized")
            else:
                self.anthropic_client = None
                logger.warning(
                    "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                    "or add to ~/.claude/config.json"
                )
        else:
            self.anthropic_client = None
            logger.warning("Anthropic SDK not installed. Install with: pip install anthropic")

        # OpenAI
        if OPENAI_AVAILABLE:
            api_key = self.api_config.get_api_key('openai')
            if api_key:
                openai.api_key = api_key
                self.openai_available = True
                logger.debug("OpenAI client initialized")
            else:
                self.openai_available = False
                logger.warning(
                    "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                    "or add to ~/.claude/config.json"
                )
        else:
            self.openai_available = False
            logger.warning("OpenAI SDK not installed. Install with: pip install openai")

        # Gemini
        if GEMINI_AVAILABLE:
            api_key = self.api_config.get_api_key('google')
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_available = True
                logger.debug("Gemini client initialized")
            else:
                self.gemini_available = False
                logger.warning(
                    "Google API key not found. Set GOOGLE_API_KEY environment variable "
                    "or add to ~/.claude/config.json"
                )
        else:
            self.gemini_available = False
            logger.warning("Gemini SDK not installed. Install with: pip install google-generativeai")

        # xAI (uses OpenAI SDK with custom base_url)
        if XAI_AVAILABLE:
            api_key = self.api_config.get_api_key('xai')
            if api_key:
                # Import OpenAI here to avoid namespace conflicts
                from openai import OpenAI
                self.xai_client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.x.ai/v1"
                )
                self.xai_available = True
                logger.debug("xAI client initialized")
            else:
                self.xai_client = None
                self.xai_available = False
                logger.warning(
                    "xAI API key not found. Set XAI_API_KEY environment variable "
                    "or add to ~/.claude/config.json"
                )
        else:
            self.xai_client = None
            self.xai_available = False
            logger.warning("xAI requires OpenAI SDK. Install with: pip install openai")

        # Log summary of available providers
        available_providers = self.api_config.get_available_providers()
        if available_providers:
            logger.info(f"Initialized providers: {', '.join(available_providers)}")
        else:
            logger.warning(
                "No API providers available! Configure at least one API key. "
                "See APIConfig documentation for setup instructions."
            )

    def call(self,
             prompt: str,
             context: Optional[Dict[str, Any]] = None,
             validate_scope: Optional[str] = None,
             strict_sanitize: bool = False) -> CallResult:
        """
        Make resilient API call with security validation.

        Args:
            prompt: User prompt
            context: Additional context
            validate_scope: Optional action scope to validate
            strict_sanitize: Use strict input sanitization

        Returns:
            CallResult with output and metadata
        """
        start_time = time.time()

        # SECURITY: Validate scope if provided (zero-trust delegation)
        if validate_scope:
            if not self.security.validate_scope(validate_scope, self.allowed_scopes):
                logger.error(f"Scope validation failed: {validate_scope}")
                return CallResult(
                    success=False,
                    error=f"Action '{validate_scope}' not in allowed scopes",
                    latency=time.time() - start_time
                )

        # SECURITY: Detect injection attempts
        injection_detected = False
        detected_patterns = []

        if self.enable_security:
            injection_detected, detected_patterns = self.security.detect_injection(prompt)

            if injection_detected:
                logger.warning(f"Potential injection detected: {detected_patterns}")
                # Continue but log the attempt

            # Sanitize input
            prompt = self.security.sanitize_input(prompt, strict=strict_sanitize)

        # Build system prompt
        system = self._build_system_prompt(context)

        # Try with fallback if enabled
        if self.enable_fallback and self.fallback_chain:
            return self._call_with_fallback(
                prompt, system, start_time,
                injection_detected, detected_patterns
            )
        else:
            # Determine provider from model
            provider = self._get_provider(self.model)
            return self._call_single_provider(
                prompt, system, self.model, provider, start_time,
                injection_detected, detected_patterns
            )

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        output_style: Optional[str] = None,
        _retry_count: int = 0
    ) -> Any:
        """
        Generate text using the agent's call() method with optional output style enforcement.

        This is a convenience wrapper that temporarily overrides model/temperature/max_tokens
        for a single call, then restores the original settings.

        With output_style specified, applies structured output requirements and validates
        response against schema. Returns parsed data instead of raw text.

        Args:
            prompt: User prompt
            model: Model to use (defaults to agent's model)
            temperature: Sampling temperature (defaults to agent's temperature)
            max_tokens: Maximum tokens to generate (defaults to agent's max_tokens)
            output_style: Optional output style name (e.g., "critic_judge", "refinement_feedback")
            _retry_count: Internal retry counter (do not set manually)

        Returns:
            Generated text response (str) or parsed data (dict) if output_style specified

        Raises:
            ValueError: If call fails or returns no output
            OutputStyleValidationError: If response fails output style validation (max retries exceeded)
        """
        # Save current settings
        original_model = self.model
        original_temperature = self.temperature
        original_max_tokens = self.max_tokens

        # Load and apply output style if specified
        style_manager = None
        style = None
        enhanced_prompt = prompt

        if output_style:
            try:
                style_manager = OutputStylesManager()
                style = style_manager.get_style(output_style)

                # Override model if style specifies one and enforcement is strict
                if style.model and style.enforcement == "strict":
                    model = style.model
                    logger.info(f"Output style '{output_style}' enforcing model: {model}")

                # Override temperature if style specifies
                if style.temperature is not None:
                    temperature = style.temperature
                    logger.debug(f"Output style '{output_style}' enforcing temperature: {temperature}")

                # Override max_tokens if style specifies
                if style.max_tokens:
                    max_tokens = style.max_tokens

                # Apply style to prompt
                enhanced_prompt = style_manager.apply_style(prompt, style)
                logger.debug(f"Applied output style '{output_style}' to prompt")

            except Exception as e:
                logger.error(f"Failed to apply output style '{output_style}': {e}")
                # Continue with original prompt if style application fails
                enhanced_prompt = prompt

        try:
            # Temporarily set new model/temperature/max_tokens if provided
            if model is not None:
                self.model = model
            if temperature is not None:
                self.temperature = temperature
            if max_tokens is not None:
                self.max_tokens = max_tokens

            # Call the agent with enhanced prompt
            result = self.call(prompt=enhanced_prompt)

            # Extract text from CallResult
            if not result.success:
                error_msg = result.error or "Call failed with no error message"
                raise ValueError(f"LLM call failed: {error_msg}")

            if not result.output:
                raise ValueError("No output generated from LLM call")

            raw_output = result.output

            # Validate response if output style was specified
            if output_style and style_manager and style:
                is_valid, parsed_data, error_msg = style_manager.validate_response(raw_output, style)

                if not is_valid:
                    logger.warning(f"Output style validation failed: {error_msg}")

                    # Retry if enabled and attempts remaining
                    if style.retry_on_parse_error and _retry_count < style.retry_attempts:
                        logger.info(f"Retrying with clearer instructions (attempt {_retry_count + 1}/{style.retry_attempts})")

                        # Build retry prompt with error feedback
                        retry_prompt = f"{prompt}\n\nIMPORTANT: Previous attempt failed validation with error: {error_msg}\n\nPlease ensure your response strictly follows the format requirements."

                        # Recursive retry
                        return self.generate_text(
                            prompt=retry_prompt,
                            model=model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            output_style=output_style,
                            _retry_count=_retry_count + 1
                        )
                    else:
                        # Max retries exceeded
                        error_detail = f"Response validation failed after {_retry_count + 1} attempts: {error_msg}"
                        logger.error(error_detail)
                        raise OutputStyleValidationError(error_detail)

                # Validation passed - return parsed data
                logger.info(f"Output style validation passed for '{output_style}'")
                return parsed_data

            # No output style - return raw text
            return raw_output

        finally:
            # Always restore original settings
            self.model = original_model
            self.temperature = original_temperature
            self.max_tokens = original_max_tokens

    def _call_with_fallback(self,
                           prompt: str,
                           system: str,
                           start_time: float,
                           injection_detected: bool,
                           detected_patterns: List[str]) -> CallResult:
        """Call with automatic fallback across providers."""

        def make_call(model: str) -> Dict[str, Any]:
            """Wrapper function for fallback chain."""
            provider = self._get_provider(model)
            return self._execute_call(model, provider, prompt, system)

        # Use fallback chain
        fallback_result = self.fallback_chain.call_with_fallback(
            make_call,
            self.model
        )

        if not fallback_result['success']:
            # All models failed
            return CallResult(
                success=False,
                error=fallback_result.get('error', 'All models failed'),
                attempted_models=fallback_result['attempted_models'],
                fallback_occurred=fallback_result['fallback_occurred'],
                latency=time.time() - start_time,
                injection_detected=injection_detected,
                detected_patterns=detected_patterns
            )

        # Success
        api_result = fallback_result['result']

        result = CallResult(
            success=True,
            output=api_result['output'],
            model_used=fallback_result['model_used'],
            provider=fallback_result['provider'],
            fallback_occurred=fallback_result['fallback_occurred'],
            attempted_models=fallback_result['attempted_models'],
            tokens_in=api_result['tokens_in'],
            tokens_out=api_result['tokens_out'],
            total_tokens=api_result['total_tokens'],
            cost=api_result['cost'],
            latency=time.time() - start_time,
            injection_detected=injection_detected,
            detected_patterns=detected_patterns,
            input_sanitized=self.enable_security,
            output_style=self.output_style
        )

        # Track metrics
        self._track_call(result)

        return result

    def _call_single_provider(self,
                             prompt: str,
                             system: str,
                             model: str,
                             provider: str,
                             start_time: float,
                             injection_detected: bool,
                             detected_patterns: List[str]) -> CallResult:
        """Call single provider with retries."""

        last_error = None

        for attempt in range(self.max_retries):
            try:
                api_result = self._execute_call(model, provider, prompt, system)

                result = CallResult(
                    success=True,
                    output=api_result['output'],
                    model_used=model,
                    provider=provider,
                    tokens_in=api_result['tokens_in'],
                    tokens_out=api_result['tokens_out'],
                    total_tokens=api_result['total_tokens'],
                    cost=api_result['cost'],
                    latency=time.time() - start_time,
                    attempt=attempt + 1,
                    injection_detected=injection_detected,
                    detected_patterns=detected_patterns,
                    input_sanitized=self.enable_security,
                    output_style=self.output_style
                )

                self._track_call(result)
                return result

            except Exception as e:
                logger.warning(f"Call failed (attempt {attempt + 1}): {e}")
                last_error = e

                if attempt < self.max_retries - 1:
                    delay = self.backoff.get_delay(attempt)
                    time.sleep(delay)

        # All retries failed
        return CallResult(
            success=False,
            error=str(last_error),
            model_used=model,
            provider=provider,
            attempt=self.max_retries,
            latency=time.time() - start_time,
            injection_detected=injection_detected,
            detected_patterns=detected_patterns
        )

    def _execute_call(self,
                     model: str,
                     provider: str,
                     prompt: str,
                     system: str) -> Dict[str, Any]:
        """Execute API call to specific provider."""

        if provider == 'anthropic':
            return self._call_anthropic(model, prompt, system)
        elif provider == 'openai':
            return self._call_openai(model, prompt, system)
        elif provider == 'gemini':
            return self._call_gemini(model, prompt, system)
        elif provider == 'xai':
            return self._call_xai(model, prompt, system)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _call_anthropic(self, model: str, prompt: str, system: str) -> Dict[str, Any]:
        """Call Anthropic API."""
        if not self.anthropic_client:
            raise Exception("Anthropic client not available")

        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )

        cost = ModelPricing.calculate_cost(
            model,
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        return {
            'output': response.content[0].text,
            'tokens_in': response.usage.input_tokens,
            'tokens_out': response.usage.output_tokens,
            'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
            'cost': cost
        }

    def _call_openai(self, model: str, prompt: str, system: str) -> Dict[str, Any]:
        """Call OpenAI API."""
        if not self.openai_available:
            raise Exception("OpenAI client not available")

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        # Estimate cost (approximate)
        cost = ModelPricing.calculate_cost(model, tokens_in, tokens_out)

        return {
            'output': response.choices[0].message.content,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'total_tokens': tokens_in + tokens_out,
            'cost': cost
        }

    def _call_gemini(self, model: str, prompt: str, system: str) -> Dict[str, Any]:
        """Call Gemini API."""
        if not self.gemini_available:
            raise Exception("Gemini client not available")

        gemini_model = genai.GenerativeModel(model)

        # Combine system and user prompt
        full_prompt = f"{system}\n\nUser: {prompt}"

        response = gemini_model.generate_content(full_prompt)

        # Gemini doesn't provide token counts easily, estimate
        tokens_in = len(full_prompt.split())
        tokens_out = len(response.text.split())

        # Rough cost estimate
        cost = (tokens_in + tokens_out) / 1000 * 0.0005

        return {
            'output': response.text,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'total_tokens': tokens_in + tokens_out,
            'cost': cost
        }

    def _call_xai(self, model: str, prompt: str, system: str) -> Dict[str, Any]:
        """Call xAI API (uses OpenAI SDK with custom base URL)."""
        if not self.xai_available or not self.xai_client:
            raise Exception("xAI client not available")

        response = self.xai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        # Calculate cost using ModelPricing
        cost = ModelPricing.calculate_cost(model, tokens_in, tokens_out)

        return {
            'output': response.choices[0].message.content,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'total_tokens': tokens_in + tokens_out,
            'cost': cost
        }

    def _get_provider(self, model: str) -> str:
        """Determine provider from model name."""
        if 'claude' in model.lower():
            return 'anthropic'
        elif 'gemini' in model.lower():
            return 'gemini'
        elif 'gpt' in model.lower():
            return 'openai'
        elif 'grok' in model.lower():
            return 'xai'
        else:
            return 'anthropic'  # default

    def _build_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """
        Build system prompt with role, output style, and context.

        Priority:
        1. Explicit system_prompt (if provided)
        2. Output style (if provided)
        3. Default role-based prompt

        CRITICAL: Automatically injects `ultrathink` for Opus 4.1 in validation/critic roles.
        """
        if self.system_prompt:
            # Explicit system prompt takes precedence
            system = self.system_prompt
        elif self.output_style:
            # Use output style
            try:
                style_data = self.style_manager.load_style(self.output_style, role=self.role)
                system = style_data['system_prompt']
                logger.debug(f"Loaded output style '{self.output_style}' for role '{self.role}'")
            except Exception as e:
                logger.warning(f"Failed to load output style '{self.output_style}': {e}. Using default.")
                system = f"You are {self.role}."
        else:
            # No output style specified - use default system prompt
            system = f"You are {self.role}."

        # ========================================================================
        # ULTRATHINK AUTO-INJECTION (Phase D Mandate)
        # ========================================================================
        # Automatically inject ultrathink keyword for Opus models when used in
        # validation, critic, judge, or self-reflection roles
        ultrathink_roles = ['critic', 'judge', 'validator', 'reviewer', 'validation', 'reflection']
        is_validation_role = any(keyword in self.role.lower() for keyword in ultrathink_roles)

        # Check for both Opus 3 and Opus 4 models
        is_opus = (
            'opus-4' in self.model.lower() or
            'claude-opus-4' in self.model.lower() or
            'claude-3-opus' in self.model.lower() or
            'opus-20240229' in self.model.lower()
        )

        if is_opus and is_validation_role:
            # Inject ultrathink at the beginning of system prompt
            system = f"ultrathink\n\n{system}"
            logger.info(f"🧠 ULTRATHINK auto-injected for {self.model} in {self.role} role")

        if context:
            context_str = json.dumps(context, indent=2) if isinstance(context, dict) else str(context)
            system += f"\n\nContext:\n{context_str}"

        return system

    def _track_call(self, result: CallResult):
        """Track call metrics and history."""
        # Add to history
        self.call_history.append(result)

        # Track cost
        if result.success:
            self.cost_tracker.track(
                self.agent_id,
                result.model_used or self.model,
                result.tokens_in,
                result.tokens_out,
                result.cost,
                result.latency,
                success=True
            )
        else:
            self.cost_tracker.track(
                self.agent_id,
                result.model_used or self.model,
                0, 0, 0, result.latency,
                success=False,
                error=result.error
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive agent metrics."""
        total_calls = len(self.call_history)
        successful_calls = sum(1 for r in self.call_history if r.success)
        fallback_calls = sum(1 for r in self.call_history if r.fallback_occurred)
        injection_attempts = sum(1 for r in self.call_history if r.injection_detected)

        metrics = {
            'agent_id': self.agent_id,
            'role': self.role,
            'primary_model': self.model,
            'output_style': self.output_style,
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'success_rate': round((successful_calls / max(total_calls, 1)) * 100, 2),
            'fallback_rate': round((fallback_calls / max(total_calls, 1)) * 100, 2),
            'injection_attempts': injection_attempts,
            'enable_fallback': self.enable_fallback,
            'enable_security': self.enable_security
        }

        if self.enable_fallback and self.fallback_chain:
            metrics['fallback_chain'] = self.fallback_chain.get_metrics()

        return metrics

    def get_recent_calls(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get recent call history."""
        recent = self.call_history[-n:]
        return [r.to_dict() for r in recent]
