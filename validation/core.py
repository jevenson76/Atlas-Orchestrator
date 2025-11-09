"""
Validation Core - Core Validation Engine

This module contains the core ValidationOrchestrator class and validation logic.

Architecture:
    ValidationOrchestrator (inherits ResilientBaseAgent)
    ├── Loads validator agents from .md files
    ├── Formats prompts with user code/docs/tests
    ├── Invokes LLM via Phase B infrastructure
    ├── Parses structured JSON responses
    └── Returns ValidationResult objects

Integration:
    - Phase B: ResilientBaseAgent (multi-provider fallback)
    - Phase B: EnhancedSessionManager (session tracking)
    - validation.interfaces (types, protocols, constants)

Usage:
    from validation.core import ValidationOrchestrator

    orchestrator = ValidationOrchestrator(project_root=".")
    result = orchestrator.validate_code(code, context, level="standard")
"""

from pathlib import Path
from typing import List, Dict, Optional, Literal, Any
import json
import re
import time
from dataclasses import dataclass

# Phase B infrastructure
from resilient_agent import ResilientBaseAgent
from session_management import EnhancedSessionManager

# Centralized utilities
from utils import ModelSelector

# Validation types and interfaces
from validation.interfaces import (
    ValidationResult,
    ValidationFinding,
    ValidationLevel,
    ValidatorName,
    VALIDATION_MODELS,
    VALIDATION_TEMPERATURES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_VALIDATION_LEVEL,
    INLINE_PROMPTS,
    DOC_PATTERNS,
    TEST_PATTERNS,
    CODE_EXTENSIONS,
    LANGUAGE_EXTENSION_MAP
)

# Observability
try:
    from observability.event_emitter import EventEmitter, EventType, EventSeverity
except ImportError:
    EventEmitter = None
    EventType = None
    EventSeverity = None


class ValidationOrchestrator(ResilientBaseAgent):
    """
    Orchestrates validation across code, documentation, and tests.

    Integrates with Phase B infrastructure:
    - Inherits ResilientBaseAgent for LLM calls with multi-provider fallback
    - Uses EnhancedSessionManager for tracking
    - Leverages automatic error handling and retry logic

    Validators are loaded dynamically from ~/.claude/agents/*.md files
    and invoked programmatically with structured JSON outputs.

    Examples:
        # Initialize orchestrator
        orchestrator = ValidationOrchestrator(
            project_root="/home/user/project",
            validators=["code-validator", "doc-validator", "test-validator"]
        )

        # Validate code
        result = orchestrator.validate_code(
            code=source_code,
            context={"file_path": "auth.py"},
            level="standard"
        )
    """

    def __init__(
        self,
        project_root: str,
        validators: Optional[List[str]] = None,
        session_manager: Optional[EnhancedSessionManager] = None,
        default_level: ValidationLevel = DEFAULT_VALIDATION_LEVEL
    ):
        """
        Initialize ValidationOrchestrator with Phase B integration.

        Args:
            project_root: Root directory of project being validated
            validators: List of validator names to use (without .md extension)
                       Defaults to ["code-validator", "doc-validator", "test-validator"]
            session_manager: Optional EnhancedSessionManager instance
                           If not provided, creates a new one
            default_level: Default validation level for all validators

        Raises:
            FileNotFoundError: If validator .md files don't exist
            ValueError: If invalid validator names provided
        """
        # Initialize ResilientBaseAgent (Phase B)
        super().__init__(
            role="validation_orchestrator",
            model="claude-sonnet-4-5-20250929",  # Default to Sonnet 4.5
            temperature=0.2,  # Balanced for validation analysis
            enable_fallback=True  # Enable multi-provider fallback
        )

        # Project configuration
        self.project_root = Path(project_root).resolve()
        self.default_level = default_level

        # Validator configuration
        self.validators_dir = Path.home() / ".claude" / "agents"
        self.validators = validators or [
            "code-validator",
            "doc-validator",
            "test-validator"
        ]

        # Session management (Phase B integration)
        self.session_manager = session_manager or EnhancedSessionManager(
            project_root=str(self.project_root),
            auto_commit=True,
            commit_frequency=5
        )

        # Cache for loaded validator prompts
        self._validator_cache: Dict[str, str] = {}

        # Centralized model selection (Phase 2D)
        self.model_selector = ModelSelector()

        # Execution tracking
        self._execution_stats = {
            "total_validations": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        }

        # Initialize observability
        if EventEmitter is not None:
            self.emitter = EventEmitter(enable_console=False)
        else:
            self.emitter = None

        # Verify validators exist
        self._verify_validators()

    def _verify_validators(self) -> None:
        """
        Verify all specified validators exist in ~/.claude/agents/

        Raises:
            FileNotFoundError: If any validator file doesn't exist
        """
        missing = []
        for validator_name in self.validators:
            validator_path = self.validators_dir / f"{validator_name}.md"
            if not validator_path.exists():
                missing.append(str(validator_path))

        if missing:
            raise FileNotFoundError(
                f"Validator files not found:\n" + "\n".join(missing)
            )

    def generate_text(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> str:
        """
        Generate text using the ResilientBaseAgent.call() method.

        This is a convenience wrapper around the Phase B call() method.
        Temporarily changes the model/temperature/max_tokens for this call only.
        Disables fallback to ensure we use the exact model requested.

        Args:
            prompt: User prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            ValueError: If call fails or returns no output
        """
        # Save current settings
        original_model = self.model
        original_temperature = self.temperature
        original_max_tokens = self.max_tokens
        original_fallback = self.enable_fallback

        try:
            # Temporarily set new model/temperature/max_tokens
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            # Disable fallback - we want to use the exact model specified
            self.enable_fallback = False

            # Call ResilientBaseAgent.call() which uses self.model, self.temperature, etc.
            result = self.call(prompt=prompt)

            # Extract text from CallResult
            if isinstance(result, dict):
                # Dict format
                content = result.get("content", result.get("output", ""))
                if not content:
                    raise ValueError(f"No content in result dict. Keys: {result.keys()}")
                return content
            elif hasattr(result, "output"):
                # CallResult object with output attribute
                if not result.output:
                    error_msg = f"LLM call failed: {result.error}" if hasattr(result, 'error') and result.error else "No output generated"
                    raise ValueError(error_msg)
                return result.output
            elif hasattr(result, "content"):
                # Alternative content attribute
                if not result.content:
                    raise ValueError("No content in result")
                return result.content
            else:
                # Fallback to string conversion
                result_str = str(result)
                if not result_str or result_str == "None":
                    raise ValueError(f"Invalid result type: {type(result)}")
                return result_str

        finally:
            # Always restore original settings
            self.model = original_model
            self.temperature = original_temperature
            self.max_tokens = original_max_tokens
            self.enable_fallback = original_fallback

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _load_validator(self, validator_name: str) -> str:
        """
        Load validator .md file content.

        Uses caching to avoid re-reading files on subsequent calls.

        Args:
            validator_name: Name of validator (without .md extension)

        Returns:
            Full content of validator .md file as string

        Raises:
            FileNotFoundError: If validator file doesn't exist
        """
        # Check cache first
        if validator_name in self._validator_cache:
            return self._validator_cache[validator_name]

        # Load from file
        validator_path = self.validators_dir / f"{validator_name}.md"

        if not validator_path.exists():
            raise FileNotFoundError(
                f"Validator not found: {validator_path}\n"
                f"Available validators: {list(self.validators_dir.glob('*-validator.md'))}"
            )

        content = validator_path.read_text(encoding="utf-8")

        # Cache it
        self._validator_cache[validator_name] = content

        return content

    def _extract_system_prompt(self, validator_content: str) -> str:
        """
        Extract system prompt template from validator .md file.

        Tries multiple patterns to find the system prompt.

        Args:
            validator_content: Full validator .md file content

        Returns:
            System prompt template with {variable} placeholders

        Raises:
            ValueError: If no valid system prompt found
        """
        # Pattern 1: System Prompt Template in code fence
        patterns = [
            r'## System Prompt Template\s*\n\s*```(?:text|prompt|markdown)?\s*\n(.*?)\n\s*```',
            r'## System Prompt\s*\n\s*```(?:text|prompt|markdown)?\s*\n(.*?)\n\s*```',
            r'### System Prompt\s*\n\s*```(?:text|prompt|markdown)?\s*\n(.*?)\n\s*```',
        ]

        for pattern in patterns:
            match = re.search(pattern, validator_content, re.DOTALL)
            if match:
                prompt = match.group(1).strip()
                if len(prompt) > 100:  # Ensure it's substantial
                    return prompt

        # Pattern 2: System Prompt without code fence (fallback)
        pattern = r'## System Prompt(?:\s+Template)?\s*\n(.*?)(?=\n## |\Z)'
        match = re.search(pattern, validator_content, re.DOTALL)
        if match:
            prompt = match.group(1).strip()
            # Remove any markdown formatting
            prompt = re.sub(r'^```\w*\n?', '', prompt)
            prompt = re.sub(r'\n?```$', '', prompt)
            if len(prompt) > 100:
                return prompt.strip()

        # If still not found, raise error
        raise ValueError(
            f"Could not extract system prompt from validator.\n"
            f"Searched for: '## System Prompt Template', '## System Prompt', '### System Prompt'\n"
            f"Validator content length: {len(validator_content)} chars"
        )

    def _select_model(
        self,
        validator_name: str,
        level: ValidationLevel
    ) -> str:
        """
        Select appropriate model for validator and level.

        Uses centralized ModelSelector (Phase 2D) for consistent model selection.

        Args:
            validator_name: Name of validator
            level: Validation level

        Returns:
            Model identifier string for Anthropic API
        """
        # Map validator names to task types
        validator_to_task = {
            "code-validator": "code-validation",
            "doc-validator": "documentation",
            "test-validator": "test-validation"
        }

        task_type = validator_to_task.get(validator_name, "general")
        return self.model_selector.select_model(task_type, level)

    def _format_prompt(
        self,
        prompt_template: str,
        validator_name: str,
        target_content: str,
        context: Dict,
        level: str
    ) -> str:
        """
        Format prompt template with actual values.

        Args:
            prompt_template: System prompt with {variables}
            validator_name: Name of validator (for context)
            target_content: Code/docs/tests to validate
            context: Additional context
            level: Validation level

        Returns:
            Fully formatted prompt ready to send to LLM
        """
        # Prepare formatting variables with comprehensive defaults
        format_vars = {
            "validator_name": validator_name,
            "level": level,
            "target_content": target_content,
            "file_path": context.get("file_path", "unknown"),
            "module_purpose": context.get("module_purpose", ""),
            "language": context.get("language", "python"),
            "framework": context.get("framework", ""),
            "project_type": context.get("project_type", "application"),
            "criticality": context.get("criticality", "standard"),
            "project_name": context.get("project_name", Path(self.project_root).name),
            "version": context.get("version", "1.0.0"),
            "doc_type": context.get("doc_type", "GENERAL"),
            "primary_language": context.get("primary_language", "python"),
            "is_public": context.get("is_public", False),
            "test_framework": context.get("test_framework", "pytest"),
            "module_name": context.get("module_name", "unknown"),
            **context  # Include all context fields
        }

        # Format the prompt
        try:
            formatted_prompt = prompt_template.format(**format_vars)
        except KeyError as e:
            raise ValueError(
                f"Missing required template variable: {e}\n"
                f"Available variables: {list(format_vars.keys())}\n"
                f"Template requires: {re.findall(r'\{(\w+)\}', prompt_template)}"
            )

        return formatted_prompt

    def _parse_response(
        self,
        response: str,
        validator_name: str,
        execution_time: float,
        model_used: str
    ) -> ValidationResult:
        """
        Parse LLM JSON response into ValidationResult object.

        Args:
            response: Raw LLM response (should be JSON)
            validator_name: Which validator produced this response
            execution_time: How long validation took (seconds)
            model_used: Which model was used

        Returns:
            ValidationResult object with parsed findings

        Raises:
            ValueError: If response is not valid JSON or missing required fields
        """
        # Clean the response (remove markdown code fences if present)
        clean_response = response.strip()

        # Remove markdown code fences
        if clean_response.startswith("```"):
            clean_response = re.sub(r'^```(?:json)?\s*\n?', '', clean_response)
            clean_response = re.sub(r'\n?```\s*$', '', clean_response)
            clean_response = clean_response.strip()

        # Parse JSON
        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse validator response as JSON.\n"
                f"Validator: {validator_name}\n"
                f"Error: {e}\n"
                f"Response preview: {clean_response[:200]}..."
            )

        # Validate required fields
        required_fields = ["status", "score", "findings"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(
                f"Validator response missing required fields: {missing_fields}\n"
                f"Validator: {validator_name}\n"
                f"Response keys: {list(data.keys())}"
            )

        # Convert findings list to ValidationFinding objects
        findings = []
        for finding_data in data.get("findings", []):
            finding = ValidationFinding(
                id=finding_data.get("id", f"FIND-{len(findings)+1}"),
                severity=finding_data.get("severity", "INFO"),
                category=finding_data.get("category", "general"),
                subcategory=finding_data.get("subcategory", "general"),
                location=finding_data.get("location", ""),
                issue=finding_data.get("issue", ""),
                recommendation=finding_data.get("recommendation", finding_data.get("fix", "")),
                fix=finding_data.get("fix"),
                code_snippet=finding_data.get("code_snippet"),
                references=finding_data.get("references", []),
                impact=finding_data.get("impact"),
                confidence=finding_data.get("confidence", 0.9)
            )
            findings.append(finding)

        # Estimate cost based on model and response
        cost_estimate = self._estimate_cost(model_used, response)

        # Create ValidationResult
        result = ValidationResult(
            validator_name=validator_name,
            status=data["status"],
            score=data["score"],
            findings=findings,
            execution_time_ms=int(execution_time * 1000),
            model_used=model_used,
            cost_usd=cost_estimate,
            passed_checks=data.get("passed_checks", []),
            metrics=data.get("metrics", {}),
            target=data.get("target", "")
        )

        return result

    def _estimate_cost(self, model: str, response: str) -> float:
        """
        Estimate API cost based on model and response length.

        Uses centralized ModelSelector (Phase 2D) for accurate cost estimation.

        Args:
            model: Model identifier
            response: LLM response text

        Returns:
            Estimated cost in USD
        """
        # Estimate tokens using ModelSelector
        output_tokens = self.model_selector.estimate_tokens(response)
        input_tokens = 2000  # Typical prompt size

        # Use centralized cost estimation
        return self.model_selector.estimate_cost(
            model_name=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

    def _get_prompt_template(self, validator_name: str) -> str:
        """
        Get prompt template from .md file or fall back to inline prompt.

        Args:
            validator_name: Name of validator

        Returns:
            Prompt template string

        Raises:
            ValueError: If validator not found in either .md or inline
        """
        try:
            # First try to extract from .md file
            validator_content = self._load_validator(validator_name)
            return self._extract_system_prompt(validator_content)
        except (ValueError, FileNotFoundError) as e:
            # Fall back to inline prompt
            if validator_name in INLINE_PROMPTS:
                return INLINE_PROMPTS[validator_name]
            else:
                raise ValueError(
                    f"No prompt template found for {validator_name}.\n"
                    f"Not in .md file and not in INLINE_PROMPTS.\n"
                    f"Original error: {e}"
                )

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def validate_code(
        self,
        code: str,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None
    ) -> ValidationResult:
        """
        Validate code quality, security, and performance.

        Args:
            code: Source code to validate
            context: Optional context dictionary
            level: Validation level (defaults to self.default_level)

        Returns:
            ValidationResult with findings and recommendations

        Raises:
            ValueError: If code is empty or validation fails
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        level = level or self.default_level
        context = context or {}

        # Set defaults
        context.setdefault('language', 'python')
        context.setdefault('file_path', 'unknown.py')
        context.setdefault('module_purpose', 'Code validation')

        start_time = time.time()

        # Emit validation started event
        if self.emitter:
            self.emitter.emit(
                event_type=EventType.VALIDATION_STARTED,
                component="validation-orchestrator",
                message=f"Starting code validation (level: {level})",
                severity=EventSeverity.INFO,
                workflow="validation",
                data={
                    "validator": "code-validator",
                    "level": level,
                    "file_path": context.get('file_path', 'unknown')
                }
            )

        try:
            # Get prompt template
            prompt_template = self._get_prompt_template("code-validator")

            # Select model
            model = self._select_model("code-validator", level)

            # Format prompt
            formatted_prompt = self._format_prompt(
                prompt_template=prompt_template,
                validator_name="code-validator",
                target_content=code,
                context=context,
                level=level
            )

            # Invoke LLM
            response = self.generate_text(
                prompt=formatted_prompt,
                model=model,
                temperature=VALIDATION_TEMPERATURES.get("code-validator", {}).get(level, 0.1),
                max_tokens=DEFAULT_MAX_TOKENS
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Parse response
            result = self._parse_response(
                response=response,
                validator_name="code-validator",
                execution_time=execution_time,
                model_used=model
            )

            # Update stats
            self._execution_stats["total_validations"] += 1
            self._execution_stats["total_cost"] += result.cost_usd
            self._execution_stats["total_time"] += execution_time

            # Emit success event
            if self.emitter:
                event_type = EventType.VALIDATION_PASSED if result.status == "PASS" else EventType.VALIDATION_FAILED
                self.emitter.emit(
                    event_type=event_type,
                    component="validation-orchestrator",
                    message=f"Code validation {result.status.lower()}: score {result.score}/100",
                    severity=EventSeverity.INFO if result.status == "PASS" else EventSeverity.WARNING,
                    workflow="validation",
                    duration_ms=result.execution_time_ms
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            from validation_types import create_fail_result

            fail_result = create_fail_result(
                validator_name="code-validator",
                findings=[ValidationFinding(
                    id="ERR-001",
                    severity="CRITICAL",
                    category="error",
                    subcategory="validation_error",
                    location="orchestrator",
                    issue=f"Validation failed: {type(e).__name__}: {str(e)}",
                    recommendation="Check validator configuration and code syntax"
                )],
                model_used=model if 'model' in locals() else "unknown"
            )

            self._execution_stats["total_validations"] += 1
            self._execution_stats["total_time"] += execution_time

            return fail_result

    def validate_documentation(
        self,
        documentation: str,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None
    ) -> ValidationResult:
        """
        Validate documentation completeness, accuracy, and clarity.

        Args:
            documentation: Documentation content to validate
            context: Optional context dictionary
            level: Validation level (defaults to self.default_level)

        Returns:
            ValidationResult with documentation findings
        """
        if not documentation or not documentation.strip():
            raise ValueError("Documentation cannot be empty")

        level = level or self.default_level
        context = context or {}

        # Set defaults
        context.setdefault('doc_type', 'GENERAL')
        context.setdefault('project_type', 'application')

        start_time = time.time()

        try:
            prompt_template = self._get_prompt_template("doc-validator")
            model = self._select_model("doc-validator", level)

            formatted_prompt = self._format_prompt(
                prompt_template=prompt_template,
                validator_name="doc-validator",
                target_content=documentation,
                context=context,
                level=level
            )

            response = self.generate_text(
                prompt=formatted_prompt,
                model=model,
                temperature=VALIDATION_TEMPERATURES.get("doc-validator", {}).get(level, 0.2),
                max_tokens=DEFAULT_MAX_TOKENS
            )

            execution_time = time.time() - start_time
            result = self._parse_response(response, "doc-validator", execution_time, model)

            self._execution_stats["total_validations"] += 1
            self._execution_stats["total_cost"] += result.cost_usd
            self._execution_stats["total_time"] += execution_time

            return result

        except Exception as e:
            from validation_types import create_fail_result
            return create_fail_result(
                validator_name="doc-validator",
                findings=[ValidationFinding(
                    id="ERR-002",
                    severity="CRITICAL",
                    category="error",
                    subcategory="validation_error",
                    location="orchestrator",
                    issue=f"Documentation validation failed: {str(e)}",
                    recommendation="Check validator configuration"
                )],
                model_used=model if 'model' in locals() else "unknown"
            )

    def validate_tests(
        self,
        test_code: str,
        source_code: Optional[str] = None,
        context: Optional[Dict] = None,
        level: Optional[ValidationLevel] = None
    ) -> ValidationResult:
        """
        Validate test coverage, quality, and effectiveness.

        Args:
            test_code: Test code to validate
            source_code: Optional source code being tested
            context: Optional context dictionary
            level: Validation level (defaults to self.default_level)

        Returns:
            ValidationResult with test quality findings
        """
        if not test_code or not test_code.strip():
            raise ValueError("Test code cannot be empty")

        level = level or self.default_level
        context = context or {}

        # Set defaults
        context.setdefault('test_framework', 'pytest')
        context.setdefault('module_name', 'unknown')

        if source_code:
            context['source_code'] = source_code

        start_time = time.time()

        try:
            prompt_template = self._get_prompt_template("test-validator")
            model = self._select_model("test-validator", level)

            formatted_prompt = self._format_prompt(
                prompt_template=prompt_template,
                validator_name="test-validator",
                target_content=test_code,
                context=context,
                level=level
            )

            response = self.generate_text(
                prompt=formatted_prompt,
                model=model,
                temperature=VALIDATION_TEMPERATURES.get("test-validator", {}).get(level, 0.2),
                max_tokens=DEFAULT_MAX_TOKENS
            )

            execution_time = time.time() - start_time
            result = self._parse_response(response, "test-validator", execution_time, model)

            self._execution_stats["total_validations"] += 1
            self._execution_stats["total_cost"] += result.cost_usd
            self._execution_stats["total_time"] += execution_time

            return result

        except Exception as e:
            from validation_types import create_fail_result
            return create_fail_result(
                validator_name="test-validator",
                findings=[ValidationFinding(
                    id="ERR-003",
                    severity="CRITICAL",
                    category="error",
                    subcategory="validation_error",
                    location="orchestrator",
                    issue=f"Test validation failed: {str(e)}",
                    recommendation="Check validator configuration"
                )],
                model_used=model if 'model' in locals() else "unknown"
            )

    # ========================================================================
    # FILE HANDLING HELPERS
    # ========================================================================

    def _detect_validators_for_file(self, file_path: Path) -> List[str]:
        """Auto-detect which validators should run for this file."""
        validators = []
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Check for documentation
        if any(pattern in name or pattern == suffix for pattern in DOC_PATTERNS):
            validators.append("doc-validator")

        # Check for test files
        if any(pattern in name for pattern in TEST_PATTERNS):
            validators.append("test-validator")
            validators.append("code-validator")

        # Check for source code
        if suffix in CODE_EXTENSIONS and "test-validator" not in validators:
            validators.append("code-validator")

        return validators

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        return LANGUAGE_EXTENSION_MAP.get(suffix, "unknown")

    def _find_source_for_test(self, test_file: Path) -> Optional[str]:
        """Find the source code file that corresponds to a test file."""
        # Remove test prefix/suffix from filename
        name = test_file.stem
        name = name.replace("test_", "").replace("_test", "")
        source_filename = name + test_file.suffix

        # Common source directories
        search_dirs = [
            test_file.parent,
            test_file.parent.parent / "src",
            test_file.parent.parent / "lib",
            test_file.parent.parent / name,
        ]

        # Search for source file
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            source_path = search_dir / source_filename
            if source_path.exists():
                try:
                    return source_path.read_text(encoding="utf-8")
                except Exception:
                    continue

        return None

    def get_execution_stats(self) -> Dict:
        """Get execution statistics."""
        total = self._execution_stats["total_validations"]

        return {
            "total_validations": total,
            "total_cost_usd": round(self._execution_stats["total_cost"], 6),
            "total_time_seconds": round(self._execution_stats["total_time"], 2),
            "average_cost_usd": round(
                self._execution_stats["total_cost"] / total if total > 0 else 0,
                6
            ),
            "average_time_seconds": round(
                self._execution_stats["total_time"] / total if total > 0 else 0,
                2
            )
        }

    def reset_stats(self) -> None:
        """Reset execution statistics to zero."""
        self._execution_stats = {
            "total_validations": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        stats = self.get_execution_stats()
        return (
            f"ValidationOrchestrator("
            f"validators={self.validators}, "
            f"default_level='{self.default_level}', "
            f"validations_run={stats['total_validations']}, "
            f"total_cost=${stats['total_cost_usd']:.4f}"
            f")"
        )
