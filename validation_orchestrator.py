"""
ValidationOrchestrator - Programmatic Validation Coordination

Coordinates code, documentation, and test validators to enable
Zero-Touch Engineering (ZTE) through automated quality validation.

Architecture:
    ValidationOrchestrator (inherits ResilientBaseAgent)
    ├── Loads validator agents from .md files
    ├── Formats prompts with user code/docs/tests
    ├── Invokes LLM via Phase B infrastructure
    ├── Parses structured JSON responses
    └── Aggregates results into ValidationReport

Integration:
    - Phase B: ResilientBaseAgent (multi-provider fallback)
    - Phase B: EnhancedSessionManager (session tracking)
    - validation_types.py (structured outputs)
    - Validator agents: code-validator.md, doc-validator.md, test-validator.md

Usage:
    from validation_orchestrator import ValidationOrchestrator

    orchestrator = ValidationOrchestrator(project_root=".")
    result = orchestrator.validate_code(code, context, level="standard")

See ValidationOrchestrator class docstring for complete examples.
"""

from pathlib import Path
from typing import List, Dict, Optional, Literal, Any
import json
import re
import time
import traceback
from dataclasses import dataclass

# Phase B infrastructure
from resilient_agent import ResilientBaseAgent
from session_management import EnhancedSessionManager

# Validator types
from validation_types import (
    ValidationFinding,
    ValidationResult,
    ValidationReport,
    SeverityLevel,
    Status
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

        # Run all validators
        report = orchestrator.run_all_validators(
            target_path="src/",
            level="standard"
        )
    """

    # Inline prompts as fallback when .md extraction fails
    _INLINE_PROMPTS = {
        "code-validator": """You are a code quality validator. Analyze the provided code for quality, security, and performance issues.

VALIDATION LEVEL: {level}
LANGUAGE: {language}
FILE: {file_path}

CODE TO VALIDATE:
{target_content}

Analyze for:
- Code quality (naming, structure, complexity)
- Security vulnerabilities (OWASP Top 10)
- Performance issues
- Best practices adherence
- Error handling

Return JSON with this exact structure:
{{
    "status": "PASS|FAIL|WARNING",
    "score": 0-100,
    "findings": [
        {{
            "id": "FIND-001",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
            "category": "security|performance|quality|style",
            "subcategory": "specific-issue",
            "location": "line 42, function foo()",
            "issue": "Description of the issue",
            "recommendation": "How to fix it",
            "fix": "Optional code fix",
            "code_snippet": "Optional problematic code",
            "references": ["Optional reference links"],
            "impact": "Optional impact description",
            "confidence": 0.0-1.0
        }}
    ],
    "passed_checks": ["List of passed validations"],
    "metrics": {{"complexity": 5, "maintainability": 85}},
    "target": "{file_path}"
}}""",

        "doc-validator": """You are a documentation validator. Analyze the provided documentation for completeness, accuracy, and clarity.

VALIDATION LEVEL: {level}
DOC TYPE: {doc_type}
PROJECT TYPE: {project_type}

DOCUMENTATION TO VALIDATE:
{target_content}

Analyze for:
- Completeness (all necessary sections present)
- Accuracy (technically correct information)
- Clarity (easy to understand)
- User perspective (helpful for target audience)
- Examples and code samples

Return JSON with this exact structure:
{{
    "status": "PASS|FAIL|WARNING",
    "score": 0-100,
    "findings": [
        {{
            "id": "DOC-001",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
            "category": "completeness|accuracy|clarity|examples",
            "subcategory": "specific-issue",
            "location": "Section: Installation",
            "issue": "Description of the issue",
            "recommendation": "How to improve",
            "fix": "Optional improved text",
            "references": ["Optional reference links"],
            "confidence": 0.0-1.0
        }}
    ],
    "passed_checks": ["List of passed validations"],
    "metrics": {{"readability": 85, "completeness": 90}},
    "target": "documentation"
}}""",

        "test-validator": """You are a test quality validator. Analyze the provided test code for coverage, quality, and effectiveness.

VALIDATION LEVEL: {level}
TEST FRAMEWORK: {test_framework}
MODULE: {module_name}

TEST CODE TO VALIDATE:
{target_content}

Analyze for:
- Test coverage (edge cases, error paths)
- Test quality (clear, maintainable, isolated)
- Assertions (meaningful, comprehensive)
- Test smells (anti-patterns)
- Effectiveness (do tests catch bugs?)

Return JSON with this exact structure:
{{
    "status": "PASS|FAIL|WARNING",
    "score": 0-100,
    "findings": [
        {{
            "id": "TEST-001",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
            "category": "coverage|quality|effectiveness|smells",
            "subcategory": "specific-issue",
            "location": "test_foo() line 15",
            "issue": "Description of the issue",
            "recommendation": "How to improve",
            "fix": "Optional improved test",
            "references": ["Optional reference links"],
            "confidence": 0.0-1.0
        }}
    ],
    "passed_checks": ["List of passed validations"],
    "metrics": {{"coverage_estimate": 75, "test_quality": 80}},
    "target": "{module_name}"
}}"""
    }

    def __init__(
        self,
        project_root: str,
        validators: Optional[List[str]] = None,
        session_manager: Optional[EnhancedSessionManager] = None,
        default_level: Literal["quick", "standard", "thorough"] = "standard"
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
        max_tokens: int = 4000
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
    # PART 2: HELPER METHODS
    # ========================================================================

    def _load_validator(self, validator_name: str) -> str:
        """
        Load validator .md file content.

        Uses caching to avoid re-reading files on subsequent calls.

        Args:
            validator_name: Name of validator (without .md extension)
                           e.g., "code-validator"

        Returns:
            Full content of validator .md file as string

        Raises:
            FileNotFoundError: If validator file doesn't exist

        Example:
            validator_content = self._load_validator("code-validator")
            # Returns full code-validator.md content
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

        Tries multiple patterns to find the system prompt:
        1. ## System Prompt Template section in code fence
        2. ## System Prompt section in code fence
        3. Large text block after System Prompt heading

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

        # If still not found, use inline prompt as last resort
        # This ensures validators work even if .md format varies
        raise ValueError(
            f"Could not extract system prompt from validator.\n"
            f"Searched for: '## System Prompt Template', '## System Prompt', '### System Prompt'\n"
            f"Validator content length: {len(validator_content)} chars\n"
            f"Tip: Ensure validator .md has a '## System Prompt Template' section"
        )

    def _select_model(
        self,
        validator_name: str,
        level: Literal["quick", "standard", "thorough"]
    ) -> str:
        """
        Select appropriate model for validator and level.

        Model Selection Strategy:
        - code-validator: Uses Haiku/Sonnet/Opus stack (3-tier)
        - doc-validator: Uses Sonnet only (temperature variation)
        - test-validator: Uses Sonnet only (temperature variation)

        Args:
            validator_name: Name of validator
            level: Validation level

        Returns:
            Model identifier string for Anthropic API

        Example:
            model = self._select_model("code-validator", "quick")
            # Returns: "claude-haiku-4-5-20250611"
        """
        # Code validator uses 3-tier model stack
        if validator_name == "code-validator":
            model_map = {
                "quick": "claude-haiku-4-5-20250611",      # Fast, cheap
                "standard": "claude-sonnet-4-5-20250929",    # Balanced
                "thorough": "claude-opus-4-20250514"     # Deep analysis
            }
            return model_map[level]

        # Doc and test validators use Sonnet only
        # (Temperature variation handled in _format_prompt)
        elif validator_name in ["doc-validator", "test-validator"]:
            return "claude-sonnet-4-5-20250929"

        else:
            # Default to Sonnet for unknown validators
            return "claude-sonnet-4-5-20250929"

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

        Replaces template variables like {target_content}, {level}, etc.
        with actual values from the validation request.

        Args:
            prompt_template: System prompt with {variables}
            validator_name: Name of validator (for context)
            target_content: Code/docs/tests to validate
            context: Additional context (file_path, module_purpose, etc.)
            level: Validation level (quick/standard/thorough)

        Returns:
            Fully formatted prompt ready to send to LLM

        Example:
            prompt = self._format_prompt(
                prompt_template=template,
                validator_name="code-validator",
                target_content="def foo(): pass",
                context={"file_path": "auth.py"},
                level="standard"
            )
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
            # Additional variables for doc-validator and other templates
            "project_name": context.get("project_name", Path(self.project_root).name),
            "version": context.get("version", "1.0.0"),
            "doc_type": context.get("doc_type", "GENERAL"),
            "primary_language": context.get("primary_language", "python"),
            "is_public": context.get("is_public", False),
            **context  # Include all context fields (overrides defaults if provided)
        }

        # Format the prompt
        try:
            formatted_prompt = prompt_template.format(**format_vars)
        except KeyError as e:
            # If a required variable is missing, provide helpful error
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

        Handles both clean JSON and JSON wrapped in markdown code fences.
        Provides detailed error messages if parsing fails.

        Args:
            response: Raw LLM response (should be JSON)
            validator_name: Which validator produced this response
            execution_time: How long validation took (seconds)
            model_used: Which model was used

        Returns:
            ValidationResult object with parsed findings

        Raises:
            ValueError: If response is not valid JSON or missing required fields

        Example:
            result = self._parse_response(
                response='{"status": "PASS", "score": 95, ...}',
                validator_name="code-validator",
                execution_time=12.5,
                model_used="claude-sonnet-4-5-20250929"
            )
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

        Rough estimates based on Anthropic pricing:
        - Haiku: $0.25 / 1M input tokens, $1.25 / 1M output tokens
        - Sonnet: $3.00 / 1M input tokens, $15.00 / 1M output tokens
        - Opus: $15.00 / 1M input tokens, $75.00 / 1M output tokens

        Args:
            model: Model identifier
            response: LLM response text

        Returns:
            Estimated cost in USD
        """
        # Rough token estimation (1 token ≈ 4 characters)
        output_tokens = len(response) / 4
        input_tokens = 2000  # Typical prompt size

        # Cost per million tokens
        if "haiku" in model.lower():
            input_cost = 0.25
            output_cost = 1.25
        elif "opus" in model.lower():
            input_cost = 15.0
            output_cost = 75.0
        else:  # Sonnet
            input_cost = 3.0
            output_cost = 15.0

        # Calculate total cost
        cost = (input_tokens * input_cost / 1_000_000) + \
               (output_tokens * output_cost / 1_000_000)

        return round(cost, 6)

    def _get_prompt_template(self, validator_name: str) -> str:
        """
        Get prompt template from .md file or fall back to inline prompt.

        This method provides resilience against varying .md file formats
        by attempting extraction first, then falling back to inline prompts.

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
            if validator_name in self._INLINE_PROMPTS:
                return self._INLINE_PROMPTS[validator_name]
            else:
                raise ValueError(
                    f"No prompt template found for {validator_name}.\n"
                    f"Not in .md file and not in _INLINE_PROMPTS.\n"
                    f"Original error: {e}"
                )

    # ========================================================================
    # PART 3: VALIDATION METHODS
    # ========================================================================

    def validate_code(
        self,
        code: str,
        context: Optional[Dict] = None,
        level: Optional[Literal["quick", "standard", "thorough"]] = None
    ) -> ValidationResult:
        """
        Validate code quality, security, and performance.

        Uses code-validator.md with multi-model stack:
        - Quick: Haiku 4.5 (~2s, $0.001)
        - Standard: Sonnet 4.5 (~12s, $0.005)
        - Thorough: Opus 4.1 (~45s, $0.020)

        Args:
            code: Source code to validate
            context: Optional context dictionary with:
                - file_path: Path to the file being validated
                - module_purpose: What this module does
                - language: Programming language (default: python)
                - dependencies: List of dependencies
                - criticality: high|medium|low (default: medium)
            level: Validation level (defaults to self.default_level)

        Returns:
            ValidationResult with findings and recommendations

        Raises:
            ValueError: If code is empty or validation fails
            FileNotFoundError: If code-validator.md not found

        Example:
            result = orchestrator.validate_code(
                code='def authenticate(user, pwd): ...',
                context={'file_path': 'auth.py', 'criticality': 'high'},
                level='standard'
            )
            print(f"Status: {result.status}, Score: {result.score}")
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        level = level or self.default_level
        context = context or {}

        # Set defaults for code validation
        context.setdefault('language', 'python')
        context.setdefault('file_path', 'unknown.py')
        context.setdefault('module_purpose', 'Code validation')

        # Track start time
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
                    "file_path": context.get('file_path', 'unknown'),
                    "language": context.get('language', 'python')
                }
            )

        try:
            # Get prompt template (tries .md extraction, falls back to inline)
            prompt_template = self._get_prompt_template("code-validator")

            # Select model for this level
            model = self._select_model("code-validator", level)

            # Format prompt with code and context
            formatted_prompt = self._format_prompt(
                prompt_template=prompt_template,
                validator_name="code-validator",
                target_content=code,
                context=context,
                level=level
            )

            # Invoke LLM via ResilientBaseAgent (Phase B integration)
            # This automatically handles multi-provider fallback
            # Apply critic_judge output style for structured ValidationReport JSON
            response = self.generate_text(
                prompt=formatted_prompt,
                model=model,
                temperature=0.1,  # Low temp for consistent code analysis
                max_tokens=4000,
                output_style="critic_judge"  # C5: Enforce strict JSON ValidationReport
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Parse response into ValidationResult
            result = self._parse_response(
                response=response,
                validator_name="code-validator",
                execution_time=execution_time,
                model_used=model
            )

            # Update execution stats
            self._execution_stats["total_validations"] += 1
            self._execution_stats["total_cost"] += result.cost_usd
            self._execution_stats["total_time"] += execution_time

            # Emit validation passed/failed event based on status
            if self.emitter:
                event_type = EventType.VALIDATION_PASSED if result.status == "PASS" else EventType.VALIDATION_FAILED
                severity = EventSeverity.INFO if result.status == "PASS" else EventSeverity.WARNING

                self.emitter.emit(
                    event_type=event_type,
                    component="validation-orchestrator",
                    message=f"Code validation {result.status.lower()}: score {result.score}/100",
                    severity=severity,
                    workflow="validation",
                    duration_ms=result.execution_time_ms,
                    cost_usd=result.cost_usd,
                    quality_score=float(result.score),
                    data={
                        "validator": "code-validator",
                        "status": result.status,
                        "score": result.score,
                        "findings_count": len(result.findings),
                        "model": model
                    }
                )

                # Emit quality measured event
                self.emitter.emit(
                    event_type=EventType.QUALITY_MEASURED,
                    component="code-validator",
                    message=f"Code quality score: {result.score}/100",
                    severity=EventSeverity.INFO,
                    quality_score=float(result.score),
                    data={
                        "status": result.status,
                        "findings": len(result.findings)
                    }
                )

                # Emit cost incurred event
                self.emitter.emit(
                    event_type=EventType.COST_INCURRED,
                    component="code-validator",
                    message=f"Validation cost: ${result.cost_usd:.6f}",
                    severity=EventSeverity.INFO,
                    cost_usd=result.cost_usd,
                    data={
                        "model": model,
                        "operation": "code_validation"
                    }
                )

            return result

        except Exception as e:
            # Create a FAIL result for the error
            error_details = f"{type(e).__name__}: {str(e)}"
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
                    issue=f"Validation failed: {error_details}",
                    recommendation="Check validator configuration and code syntax"
                )],
                model_used=model if 'model' in locals() else "unknown"
            )

            # Update stats even for failed validations
            self._execution_stats["total_validations"] += 1
            self._execution_stats["total_time"] += execution_time

            # Emit validation failed event
            if self.emitter:
                self.emitter.emit(
                    event_type=EventType.VALIDATION_FAILED,
                    component="validation-orchestrator",
                    message=f"Code validation failed: {error_details}",
                    severity=EventSeverity.ERROR,
                    workflow="validation",
                    duration_ms=int(execution_time * 1000),
                    error=error_details,
                    data={
                        "validator": "code-validator",
                        "status": "FAIL",
                        "error": error_details
                    }
                )

            return fail_result

    def validate_documentation(
        self,
        documentation: str,
        context: Optional[Dict] = None,
        level: Optional[Literal["quick", "standard", "thorough"]] = None
    ) -> ValidationResult:
        """
        Validate documentation completeness, accuracy, and clarity.

        Uses doc-validator.md with Sonnet at varying temperatures:
        - Quick: Temperature 0.1 (~5s, $0.003)
        - Standard: Temperature 0.2 (~12s, $0.005)
        - Thorough: Temperature 0.3 (~20s, $0.007)

        Args:
            documentation: Documentation content to validate
                          Can be README, docstrings, API docs, etc.
            context: Optional context dictionary with:
                - project_root: Root directory of project
                - doc_type: README|API|GUIDE|INLINE
                - project_type: library|application|framework
                - primary_language: python|javascript|etc
                - is_public: True for public OSS, False for internal
            level: Validation level (defaults to self.default_level)

        Returns:
            ValidationResult with documentation findings

        Example:
            result = orchestrator.validate_documentation(
                documentation=readme_content,
                context={'doc_type': 'README', 'is_public': True},
                level='standard'
            )
        """
        if not documentation or not documentation.strip():
            raise ValueError("Documentation cannot be empty")

        level = level or self.default_level
        context = context or {}

        # Set defaults for documentation validation
        context.setdefault('doc_type', 'GENERAL')
        context.setdefault('project_type', 'application')
        context.setdefault('primary_language', 'python')
        context.setdefault('is_public', False)

        # Temperature varies by level for doc validation
        temperature_map = {
            "quick": 0.1,
            "standard": 0.2,
            "thorough": 0.3
        }
        temperature = temperature_map[level]

        start_time = time.time()

        try:
            # Get prompt template (tries .md extraction, falls back to inline)
            prompt_template = self._get_prompt_template("doc-validator")

            # Doc validator always uses Sonnet
            model = self._select_model("doc-validator", level)

            # Format prompt
            formatted_prompt = self._format_prompt(
                prompt_template=prompt_template,
                validator_name="doc-validator",
                target_content=documentation,
                context=context,
                level=level
            )

            # Invoke LLM with appropriate temperature
            # Apply critic_judge output style for structured ValidationReport JSON
            response = self.generate_text(
                prompt=formatted_prompt,
                model=model,
                temperature=temperature,
                max_tokens=4000,
                output_style="critic_judge"  # C5: Enforce strict JSON ValidationReport
            )

            execution_time = time.time() - start_time

            # Parse response
            result = self._parse_response(
                response=response,
                validator_name="doc-validator",
                execution_time=execution_time,
                model_used=model
            )

            # Update stats
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
                    recommendation="Check validator configuration and documentation format"
                )],
                model_used=model if 'model' in locals() else "unknown"
            )

    def validate_tests(
        self,
        test_code: str,
        source_code: Optional[str] = None,
        context: Optional[Dict] = None,
        level: Optional[Literal["quick", "standard", "thorough"]] = None
    ) -> ValidationResult:
        """
        Validate test coverage, quality, and effectiveness.

        Uses test-validator.md with Sonnet at varying temperatures:
        - Quick: Temperature 0.1 (~5s, $0.003)
        - Standard: Temperature 0.2 (~15s, $0.006)
        - Thorough: Temperature 0.3 (~25s, $0.008)

        Args:
            test_code: Test code to validate
            source_code: Optional source code being tested
                        (helps validator assess coverage)
            context: Optional context dictionary with:
                - module_name: Name of module being tested
                - test_framework: pytest|unittest|jest|etc
                - coverage_data: Coverage percentage and uncovered lines
                - language: python|javascript|typescript|etc
                - project_type: library|application|framework
            level: Validation level (defaults to self.default_level)

        Returns:
            ValidationResult with test quality findings

        Example:
            result = orchestrator.validate_tests(
                test_code=test_content,
                source_code=source_content,
                context={
                    'module_name': 'auth',
                    'test_framework': 'pytest',
                    'coverage_data': {'percentage': 85.5}
                },
                level='standard'
            )
        """
        if not test_code or not test_code.strip():
            raise ValueError("Test code cannot be empty")

        level = level or self.default_level
        context = context or {}

        # Set defaults for test validation
        context.setdefault('test_framework', 'pytest')
        context.setdefault('language', 'python')
        context.setdefault('module_name', 'unknown')

        # Include source code if provided
        if source_code:
            context['source_code'] = source_code

        # Temperature varies by level
        temperature_map = {
            "quick": 0.1,
            "standard": 0.2,
            "thorough": 0.3
        }
        temperature = temperature_map[level]

        start_time = time.time()

        try:
            # Get prompt template (tries .md extraction, falls back to inline)
            prompt_template = self._get_prompt_template("test-validator")

            # Test validator always uses Sonnet
            model = self._select_model("test-validator", level)

            # Format prompt with test code
            formatted_prompt = self._format_prompt(
                prompt_template=prompt_template,
                validator_name="test-validator",
                target_content=test_code,
                context=context,
                level=level
            )

            # Invoke LLM
            # Apply critic_judge output style for structured ValidationReport JSON
            response = self.generate_text(
                prompt=formatted_prompt,
                model=model,
                temperature=temperature,
                max_tokens=4000,
                output_style="critic_judge"  # C5: Enforce strict JSON ValidationReport
            )

            execution_time = time.time() - start_time

            # Parse response
            result = self._parse_response(
                response=response,
                validator_name="test-validator",
                execution_time=execution_time,
                model_used=model
            )

            # Update stats
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
                    recommendation="Check validator configuration and test code syntax"
                )],
                model_used=model if 'model' in locals() else "unknown"
            )

    # ========================================================================
    # PART 4: ORCHESTRATION & REPORTS
    # ========================================================================

    def run_all_validators(
        self,
        target_path: str,
        level: Optional[Literal["quick", "standard", "thorough"]] = None,
        recursive: bool = True,
        validators: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        Run all appropriate validators on a file or directory.

        Automatically detects file types and runs the appropriate validators:
        - .py/.js/.ts/etc → code-validator
        - .md/README/GUIDE → doc-validator
        - test_*.py/*_test.py → test-validator + code-validator

        Args:
            target_path: Path to file or directory to validate
            level: Validation level (defaults to self.default_level)
            recursive: If target is directory, recurse into subdirs
            validators: Override which validators to run
                       If None, auto-detects based on file type

        Returns:
            ValidationReport aggregating all validation results

        Example:
            # Validate entire src/ directory
            report = orchestrator.run_all_validators(
                target_path="src/",
                level="standard",
                recursive=True
            )
            print(f"Overall Status: {report.overall_status}")
            print(f"Total Cost: ${report.total_cost_usd:.4f}")

            # Validate single file
            report = orchestrator.run_all_validators(
                target_path="auth.py",
                level="quick"
            )
        """
        level = level or self.default_level
        target = Path(target_path)

        if not target.exists():
            raise FileNotFoundError(f"Target path not found: {target_path}")

        # Collect all validation results
        all_results: List[ValidationResult] = []
        start_time = time.time()

        if target.is_file():
            # Validate single file
            results = self._validate_single_file(
                file_path=target,
                level=level,
                validators=validators
            )
            all_results.extend(results)

        elif target.is_dir():
            # Validate directory
            results = self._validate_directory(
                directory=target,
                level=level,
                recursive=recursive,
                validators=validators
            )
            all_results.extend(results)

        else:
            raise ValueError(f"Invalid target: {target_path}")

        # Calculate execution time
        total_time_ms = int((time.time() - start_time) * 1000)

        # Aggregate results into report
        report = ValidationReport.from_results(
            results=all_results,
            total_time_ms=total_time_ms
        )

        return report

    def _validate_single_file(
        self,
        file_path: Path,
        level: str,
        validators: Optional[List[str]] = None
    ) -> List[ValidationResult]:
        """
        Validate a single file with appropriate validators.

        Args:
            file_path: Path to file
            level: Validation level
            validators: Override which validators to run

        Returns:
            List of ValidationResult objects (one per validator run)
        """
        results = []

        # Auto-detect which validators to use
        if validators is None:
            validators = self._detect_validators_for_file(file_path)

        if not validators:
            # No validators applicable for this file
            return results

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            # Can't read file, create FAIL result
            from validation_types import create_fail_result
            results.append(create_fail_result(
                validator_name="file-read",
                findings=[ValidationFinding(
                    id="ERR-READ",
                    severity="CRITICAL",
                    category="error",
                    subcategory="file_read",
                    location=str(file_path),
                    issue=f"Failed to read file: {e}",
                    recommendation="Check file permissions and encoding"
                )],
                model_used="none"
            ))
            return results

        # Prepare context
        context = {
            "file_path": str(file_path),
            "language": self._detect_language(file_path),
        }

        # Run each validator
        for validator_name in validators:
            if validator_name == "code-validator":
                result = self.validate_code(
                    code=content,
                    context=context,
                    level=level
                )
                results.append(result)

            elif validator_name == "doc-validator":
                context["doc_type"] = "README" if "README" in file_path.name else "GENERAL"
                result = self.validate_documentation(
                    documentation=content,
                    context=context,
                    level=level
                )
                results.append(result)

            elif validator_name == "test-validator":
                # For test files, try to find source code
                source_code = self._find_source_for_test(file_path)
                context["module_name"] = file_path.stem.replace("test_", "").replace("_test", "")

                result = self.validate_tests(
                    test_code=content,
                    source_code=source_code,
                    context=context,
                    level=level
                )
                results.append(result)

        return results

    def _validate_directory(
        self,
        directory: Path,
        level: str,
        recursive: bool,
        validators: Optional[List[str]] = None
    ) -> List[ValidationResult]:
        """
        Validate all files in a directory.

        Args:
            directory: Directory to validate
            level: Validation level
            recursive: Recurse into subdirectories
            validators: Override which validators to run

        Returns:
            List of all ValidationResult objects
        """
        all_results = []

        # Get all files
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")

        # Filter to only files (not directories)
        files = [f for f in files if f.is_file()]

        # Exclude common non-source files
        exclude_patterns = [
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            ".pytest_cache",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".DS_Store"
        ]

        filtered_files = []
        for file_path in files:
            # Check if any exclude pattern matches
            skip = False
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    skip = True
                    break
            if not skip:
                filtered_files.append(file_path)

        # Validate each file
        for file_path in filtered_files:
            try:
                file_results = self._validate_single_file(
                    file_path=file_path,
                    level=level,
                    validators=validators
                )
                all_results.extend(file_results)
            except Exception as e:
                # Log error but continue with other files
                print(f"Warning: Failed to validate {file_path}: {e}")
                continue

        return all_results

    def _detect_validators_for_file(self, file_path: Path) -> List[str]:
        """
        Auto-detect which validators should run for this file.

        Detection logic:
        - Documentation files (.md, README, GUIDE) → doc-validator
        - Test files (test_*.py, *_test.py, *.test.js) → test-validator + code-validator
        - Source code (.py, .js, .ts, etc.) → code-validator

        Args:
            file_path: Path to file

        Returns:
            List of validator names to run
        """
        validators = []
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Check for documentation
        doc_patterns = [".md", "readme", "guide", "docs", ".rst", ".txt"]
        if any(pattern in name or pattern == suffix for pattern in doc_patterns):
            validators.append("doc-validator")

        # Check for test files
        test_patterns = ["test_", "_test.", ".test.", "spec_", "_spec.", ".spec."]
        if any(pattern in name for pattern in test_patterns):
            validators.append("test-validator")
            validators.append("code-validator")  # Also validate test code quality

        # Check for source code
        code_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".rb", ".php"]
        if suffix in code_extensions and "test-validator" not in validators:
            validators.append("code-validator")

        return validators

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to file

        Returns:
            Language identifier (python, javascript, etc.)
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript-react",
            ".tsx": "typescript-react",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "c++",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
            ".md": "markdown",
            ".rst": "restructuredtext"
        }

        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, "unknown")

    def _find_source_for_test(self, test_file: Path) -> Optional[str]:
        """
        Find the source code file that corresponds to a test file.

        Attempts to locate the source file by:
        1. Removing test_ prefix or _test suffix
        2. Looking in ../src/ or ../lib/ directories
        3. Looking in same directory

        Args:
            test_file: Path to test file

        Returns:
            Source code content if found, None otherwise
        """
        # Remove test prefix/suffix from filename
        name = test_file.stem
        name = name.replace("test_", "").replace("_test", "")
        source_filename = name + test_file.suffix

        # Common source directories
        search_dirs = [
            test_file.parent,  # Same directory
            test_file.parent.parent / "src",  # ../src/
            test_file.parent.parent / "lib",  # ../lib/
            test_file.parent.parent / name,  # ../module_name/
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

        # Not found
        return None

    def generate_report(
        self,
        report: ValidationReport,
        format: Literal["markdown", "json", "text"] = "markdown"
    ) -> str:
        """
        Generate formatted report from ValidationReport.

        Args:
            report: ValidationReport to format
            format: Output format (markdown, json, or text)

        Returns:
            Formatted report string

        Example:
            report = orchestrator.run_all_validators("src/")
            markdown = orchestrator.generate_report(report, format="markdown")
            print(markdown)
        """
        if format == "json":
            # Return JSON representation
            return report.to_json()

        elif format == "markdown":
            return self._generate_markdown_report(report)

        elif format == "text":
            # Simple text format
            lines = []
            lines.append("=" * 60)
            lines.append("VALIDATION REPORT")
            lines.append("=" * 60)
            lines.append(f"Status: {report.overall_status}")
            lines.append(f"Score: {report.average_score:.1f}/100")
            lines.append(f"Total Findings: {report.total_findings.get('total', 0)}")
            lines.append(f"  - Critical: {report.critical_count}")
            lines.append(f"  - High: {report.high_count}")
            lines.append(f"  - Medium: {report.medium_count}")
            lines.append(f"  - Low: {report.low_count}")
            lines.append(f"Execution Time: {report.total_execution_time_ms}ms")
            lines.append(f"Total Cost: ${report.total_cost_usd:.4f}")
            lines.append("=" * 60)
            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown format: {format}")

    def _generate_markdown_report(self, report: ValidationReport) -> str:
        """
        Generate detailed markdown report.

        Args:
            report: ValidationReport to format

        Returns:
            Markdown-formatted report
        """
        lines = []

        # Header
        lines.append("# Validation Report")
        lines.append("")
        lines.append(f"**Status:** {report.overall_status}")
        lines.append(f"**Score:** {report.average_score:.1f}/100")
        lines.append(f"**Total Findings:** {report.total_findings.get('total', 0)}")
        lines.append(f"**Execution Time:** {report.total_execution_time_ms}ms")
        lines.append(f"**Total Cost:** ${report.total_cost_usd:.4f}")
        lines.append("")

        # Summary by severity
        lines.append("## Findings by Severity")
        lines.append("")
        lines.append(f"- 🔴 **Critical:** {report.critical_count}")
        lines.append(f"- 🟠 **High:** {report.high_count}")
        lines.append(f"- 🟡 **Medium:** {report.medium_count}")
        lines.append(f"- 🔵 **Low:** {report.low_count}")
        lines.append(f"- ⚪ **Info:** {report.info_count}")
        lines.append("")

        # Results by validator
        lines.append("## Results by Validator")
        lines.append("")

        for result in report.results.values():
            lines.append(f"### {result.validator_name}")
            lines.append("")
            lines.append(f"- **Status:** {result.status}")
            lines.append(f"- **Score:** {result.score}/100")
            lines.append(f"- **Findings:** {len(result.findings)}")
            lines.append(f"- **Model:** {result.model_used}")
            lines.append(f"- **Time:** {result.execution_time_ms}ms")
            lines.append(f"- **Cost:** ${result.cost_usd:.6f}")
            lines.append("")

            # List findings
            if result.findings:
                lines.append("**Findings:**")
                lines.append("")
                for finding in result.findings:
                    severity_emoji = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MEDIUM": "🟡",
                        "LOW": "🔵",
                        "INFO": "⚪"
                    }.get(finding.severity, "⚪")

                    lines.append(f"{severity_emoji} **{finding.severity}** - {finding.issue}")
                    lines.append(f"  - **Location:** {finding.location}")
                    lines.append(f"  - **Category:** {finding.category}/{finding.subcategory}")
                    lines.append(f"  - **Recommendation:** {finding.recommendation}")
                    if finding.fix:
                        lines.append(f"  - **Fix:** `{finding.fix}`")
                    lines.append("")

        # Footer
        lines.append("---")
        lines.append(f"*Generated by ValidationOrchestrator - {len(report.results)} validators run*")

        return "\n".join(lines)

    def get_execution_stats(self) -> Dict:
        """
        Get execution statistics.

        Returns:
            Dictionary with execution stats:
            - total_validations: Number of validations run
            - total_cost: Total cost in USD
            - total_time: Total time in seconds
            - average_cost: Average cost per validation
            - average_time: Average time per validation
        """
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
        """
        Reset execution statistics to zero.

        Useful for tracking stats for a specific session or batch.
        """
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

    # ========================================================================
    # PART 5: CRITIC INTEGRATION
    # ========================================================================

    def validate_with_critics(
        self,
        code: str,
        context: Optional[Dict] = None,
        level: Optional[Literal["quick", "standard", "thorough"]] = None,
        run_validators: bool = True,
        critics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive code evaluation combining validators and critics.

        Two-Stage Evaluation:
        1. VALIDATORS (fast, structural): Check for presence of security features,
           basic patterns, structural issues. Uses Haiku/Sonnet.
        2. CRITICS (deep, semantic): Unbiased analysis of actual vulnerabilities,
           performance issues, architectural problems. Uses Opus MANDATORY.

        Philosophy: "Creator Cannot Be Judge"
        - Critics receive FRESH CONTEXT (code only, no task history)
        - Validators check "what's there", critics analyze "how well it works"
        - Complementary, not redundant

        Args:
            code: Source code to evaluate
            context: Optional context dictionary (same as validate_code)
            level: Validation level (quick/standard/thorough)
                  - quick: Validators only, no critics
                  - standard: Validators + 2-3 critics (security, performance)
                  - thorough: Validators + all 5 critics
            run_validators: If True, run validators first (recommended)
            critics: Specific critics to run (overrides level-based selection)
                    Options: security-critic, performance-critic,
                            architecture-critic, code-quality-critic,
                            documentation-critic

        Returns:
            Dictionary with:
            {
                "validator_result": ValidationResult,  # Fast structural checks
                "critic_results": {critic_id: CriticResult},  # Deep analysis
                "aggregated_report": AggregatedReport,  # Combined report
                "overall_score": int,  # 0-100 average
                "worst_grade": str,  # CRITICAL, POOR, FAIR, GOOD, EXCELLENT
                "total_cost_usd": float,
                "total_time_seconds": float,
                "recommendation": str  # GO|NO-GO|FIX-CRITICAL|FIX-HIGH
            }

        Example:
            # Standard evaluation (validators + key critics)
            result = orchestrator.validate_with_critics(
                code=source_code,
                context={'file_path': 'auth.py', 'criticality': 'high'},
                level='standard'
            )

            if result['recommendation'] == 'NO-GO':
                print("Critical issues found:")
                for finding in result['aggregated_report'].critical_findings:
                    print(f"  - {finding}")

            # Thorough evaluation (validators + all critics)
            result = orchestrator.validate_with_critics(
                code=source_code,
                level='thorough'
            )

            # Custom critics only
            result = orchestrator.validate_with_critics(
                code=source_code,
                critics=['security-critic', 'performance-critic'],
                run_validators=False
            )
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        level = level or self.default_level
        context = context or {}

        # Lazy import to avoid circular dependency
        from critic_orchestrator import CriticOrchestrator

        start_time = time.time()

        # Start workflow trace
        trace_id = None
        if self.emitter:
            trace_id = self.emitter.start_trace(
                workflow="validate_with_critics",
                context={
                    "level": level,
                    "file_path": context.get('file_path', 'unknown'),
                    "run_validators": run_validators,
                    "critics": critics or "auto"
                }
            )

        # Stage 1: Run validators (fast, structural checks)
        validator_result = None
        if run_validators:
            print("Stage 1: Running validators (fast structural checks)...")

            # Start validator span
            if self.emitter:
                self.emitter.start_span("validators")
            validator_result = self.validate_code(
                code=code,
                context=context,
                level=level
            )
            print(f"Validator result: {validator_result.status} (score: {validator_result.score}/100)")

            # End validator span
            if self.emitter:
                self.emitter.end_span()

        # Stage 2: Select critics based on level
        if critics is None:
            critics = self._select_critics_for_level(level)

        # Stage 3: Run critics (deep semantic analysis with FRESH CONTEXT)
        critic_results = {}
        critic_report = None
        if critics:
            print(f"\nStage 2: Running {len(critics)} critics (deep semantic analysis with Opus)...")
            print(f"Critics: {', '.join(critics)}")

            # Start critic span
            if self.emitter:
                self.emitter.start_span("critics")

            # Initialize CriticOrchestrator
            critic_orchestrator = CriticOrchestrator()

            # Run critics with FRESH CONTEXT (code only, no history)
            critic_results = critic_orchestrator.review_code(
                code_snippet=code,
                file_path=context.get('file_path'),
                critics=critics,
                language=context.get('language')
            )

            # Generate aggregated critic report
            critic_report = critic_orchestrator.generate_report(
                results=critic_results,
                code_snippet=code,
                file_path=context.get('file_path')
            )

            print(f"Critic report: {critic_report.worst_grade} (score: {critic_report.overall_score}/100)")
            print(f"Total findings: {critic_report.total_findings} "
                  f"(Critical: {critic_report.critical_findings}, High: {critic_report.high_findings})")

            # End critic span
            if self.emitter:
                self.emitter.end_span()

        # Calculate overall metrics
        total_time = time.time() - start_time

        # Overall score (weighted average: validators 30%, critics 70%)
        if validator_result and critic_report:
            overall_score = int(
                (validator_result.score * 0.3) + (critic_report.overall_score * 0.7)
            )
        elif validator_result:
            overall_score = validator_result.score
        elif critic_report:
            overall_score = critic_report.overall_score
        else:
            overall_score = 0

        # Worst grade
        grades = []
        if validator_result:
            # Map validator status to grade
            status_to_grade = {
                "PASS": "GOOD",
                "WARNING": "FAIR",
                "FAIL": "POOR"
            }
            grades.append(status_to_grade.get(validator_result.status, "UNKNOWN"))
        if critic_report:
            grades.append(critic_report.worst_grade)

        grade_priority = {
            "CRITICAL": 0,
            "POOR": 1,
            "FAIL": 1,
            "FAIR": 2,
            "WARNING": 2,
            "GOOD": 3,
            "PASS": 3,
            "EXCELLENT": 4,
            "UNKNOWN": -1
        }
        worst_grade = min(grades, key=lambda g: grade_priority.get(g, -1)) if grades else "UNKNOWN"

        # Total cost
        total_cost = 0.0
        if validator_result:
            total_cost += validator_result.cost_usd
        if critic_report:
            total_cost += critic_report.total_cost_usd

        # Recommendation logic
        critical_count = 0
        high_count = 0

        if validator_result:
            critical_count += sum(1 for f in validator_result.findings if f.severity == "CRITICAL")
            high_count += sum(1 for f in validator_result.findings if f.severity == "HIGH")

        if critic_report:
            critical_count += critic_report.critical_findings
            high_count += critic_report.high_findings

        # Recommendation decision tree
        if critical_count > 0:
            recommendation = "NO-GO"
        elif high_count >= 3:
            recommendation = "FIX-CRITICAL"
        elif high_count > 0:
            recommendation = "FIX-HIGH"
        elif overall_score >= 80:
            recommendation = "GO"
        else:
            recommendation = "REVIEW"

        # Build comprehensive result
        result = {
            "validator_result": validator_result,
            "critic_results": critic_results,
            "aggregated_report": critic_report,
            "overall_score": overall_score,
            "worst_grade": worst_grade,
            "total_cost_usd": round(total_cost, 6),
            "total_time_seconds": round(total_time, 2),
            "recommendation": recommendation,
            "metrics": {
                "validators_run": 1 if validator_result else 0,
                "critics_run": len(critic_results),
                "total_findings": (
                    len(validator_result.findings) if validator_result else 0
                ) + (
                    critic_report.total_findings if critic_report else 0
                ),
                "critical_findings": critical_count,
                "high_findings": high_count
            }
        }

        # End workflow trace
        if self.emitter:
            self.emitter.end_trace(
                success=True,
                result={
                    "overall_score": overall_score,
                    "recommendation": recommendation,
                    "total_cost": total_cost,
                    "validators_run": result["metrics"]["validators_run"],
                    "critics_run": result["metrics"]["critics_run"]
                }
            )

            # Emit aggregated quality score
            self.emitter.emit(
                event_type=EventType.QUALITY_MEASURED,
                component="validation-orchestrator",
                message=f"Combined validation score: {overall_score}/100 ({worst_grade})",
                severity=EventSeverity.INFO,
                quality_score=float(overall_score),
                data={
                    "recommendation": recommendation,
                    "validators": result["metrics"]["validators_run"],
                    "critics": result["metrics"]["critics_run"],
                    "findings": result["metrics"]["total_findings"]
                }
            )

            # Emit total cost
            self.emitter.emit(
                event_type=EventType.COST_INCURRED,
                component="validation-orchestrator",
                message=f"Total validation cost: ${total_cost:.6f}",
                severity=EventSeverity.INFO,
                cost_usd=total_cost,
                data={
                    "operation": "validate_with_critics",
                    "validators_cost": validator_result.cost_usd if validator_result else 0,
                    "critics_cost": critic_report.total_cost_usd if critic_report else 0
                }
            )

        return result

    def _select_critics_for_level(
        self,
        level: Literal["quick", "standard", "thorough"]
    ) -> List[str]:
        """
        Select critics based on validation level.

        Selection Strategy:
        - quick: No critics (validators only for speed)
        - standard: 2-3 key critics (security, performance, architecture)
        - thorough: All 5 critics (complete analysis)

        Args:
            level: Validation level

        Returns:
            List of critic IDs to run
        """
        if level == "quick":
            # No critics - validators only for speed
            return []

        elif level == "standard":
            # Key critics for typical issues
            return [
                "security-critic",      # Security vulnerabilities
                "performance-critic",   # Performance bottlenecks
                "architecture-critic"   # SOLID violations
            ]

        elif level == "thorough":
            # All critics for comprehensive analysis
            return [
                "security-critic",
                "performance-critic",
                "architecture-critic",
                "code-quality-critic",
                "documentation-critic"
            ]

        else:
            raise ValueError(f"Unknown level: {level}")

    def print_combined_report(self, result: Dict[str, Any]) -> None:
        """
        Print human-readable combined validator + critic report.

        Args:
            result: Result from validate_with_critics()
        """
        print("\n" + "=" * 80)
        print("COMPREHENSIVE CODE EVALUATION REPORT")
        print("=" * 80)

        # Overall assessment
        print(f"\n--- OVERALL ASSESSMENT ---")
        print(f"Score: {result['overall_score']}/100")
        print(f"Grade: {result['worst_grade']}")
        print(f"Recommendation: {result['recommendation']}")

        # Metrics
        metrics = result['metrics']
        print(f"\n--- EXECUTION METRICS ---")
        print(f"Validators Run: {metrics['validators_run']}")
        print(f"Critics Run: {metrics['critics_run']}")
        print(f"Total Findings: {metrics['total_findings']}")
        print(f"  - Critical: {metrics['critical_findings']}")
        print(f"  - High: {metrics['high_findings']}")
        print(f"Total Cost: ${result['total_cost_usd']:.4f}")
        print(f"Total Time: {result['total_time_seconds']:.2f}s")

        # Validator results
        if result['validator_result']:
            val_result = result['validator_result']
            print(f"\n--- VALIDATOR RESULTS ---")
            print(f"Status: {val_result.status}")
            print(f"Score: {val_result.score}/100")
            print(f"Findings: {len(val_result.findings)}")
            print(f"Cost: ${val_result.cost_usd:.6f}")

        # Critic results
        if result['critic_results']:
            print(f"\n--- CRITIC RESULTS ---")
            for critic_id, critic_result in result['critic_results'].items():
                print(f"\n{critic_id}:")
                print(f"  Score: {critic_result.overall_score}/100 ({critic_result.grade})")
                print(f"  Findings: {len(critic_result.findings)}")
                if critic_result.success:
                    stats = critic_result.statistics
                    print(f"    Critical: {stats.get('critical', 0)}, "
                          f"High: {stats.get('high', 0)}, "
                          f"Medium: {stats.get('medium', 0)}, "
                          f"Low: {stats.get('low', 0)}")
                else:
                    print(f"  Error: {critic_result.error}")

        # Recommendation explanation
        print(f"\n--- RECOMMENDATION: {result['recommendation']} ---")
        if result['recommendation'] == "NO-GO":
            print("⛔ Critical issues found. Do NOT proceed until fixed.")
        elif result['recommendation'] == "FIX-CRITICAL":
            print("⚠️  Multiple high-severity issues. Fix before proceeding.")
        elif result['recommendation'] == "FIX-HIGH":
            print("⚠️  High-severity issues found. Recommend fixing.")
        elif result['recommendation'] == "GO":
            print("✅ Code quality is good. Safe to proceed.")
        elif result['recommendation'] == "REVIEW":
            print("👀 Code needs review. Some issues present.")

        print("\n" + "=" * 80)
