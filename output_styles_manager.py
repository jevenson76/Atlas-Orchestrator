#!/usr/bin/env python3
"""
Output Styles Manager - Deterministic Output Control System (C5)

Enforces structured outputs for critics, validators, and refinement loops.
Integrates with ResilientBaseAgent to apply styles globally.

Architecture:
1. Load output style definitions from .md files
2. Parse YAML frontmatter (metadata)
3. Extract schema and validation rules
4. Apply style to prompts before LLM invocation
5. Validate LLM response against schema
6. Retry on parse errors (if enabled)

Usage:
    manager = OutputStylesManager()
    style = manager.get_style("critic_judge")

    # Apply to prompt
    enhanced_prompt = manager.apply_style(original_prompt, style)

    # Validate response
    is_valid, parsed, error = manager.validate_response(llm_response, style)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import yaml
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== CUSTOM EXCEPTIONS ====================

class OutputStyleError(Exception):
    """Base exception for output style errors."""
    pass


class OutputStyleNotFoundError(OutputStyleError):
    """Raised when output style definition file not found."""
    pass


class OutputStyleValidationError(OutputStyleError):
    """Raised when LLM response fails output style validation."""
    pass


class OutputStyleParseError(OutputStyleError):
    """Raised when output style definition file cannot be parsed."""
    pass


# ==================== DATA STRUCTURES ====================

@dataclass
class OutputStyle:
    """
    Represents a loaded output style definition.

    Contains metadata, schema, validation rules, and enforcement config.
    """
    name: str
    version: str
    model: Optional[str] = None
    enforcement: str = "strict"  # strict|lenient|advisory
    schema_type: str = "json"    # json|yaml|markdown
    schema_ref: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 4000
    retry_on_parse_error: bool = True
    retry_attempts: int = 3
    validation_mode: str = "schema_strict"

    # Content
    system_instructions: str = ""
    schema_definition: str = ""
    example_output: str = ""
    validation_rules: List[str] = field(default_factory=list)

    # Metadata
    loaded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    file_path: Optional[Path] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "model": self.model,
            "enforcement": self.enforcement,
            "schema_type": self.schema_type,
            "schema_ref": self.schema_ref,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "retry_on_parse_error": self.retry_on_parse_error,
            "retry_attempts": self.retry_attempts,
            "validation_mode": self.validation_mode,
            "loaded_at": self.loaded_at,
            "file_path": str(self.file_path) if self.file_path else None
        }


# ==================== MANAGER CLASS ====================

class OutputStylesManager:
    """
    Central manager for output styles.

    Responsibilities:
    - Load and cache output style definitions
    - Apply styles to prompts
    - Validate LLM responses
    - Handle parse errors and retries
    - Integrate with ResilientBaseAgent
    """

    def __init__(self, styles_dir: Optional[Path] = None):
        """
        Initialize output styles manager.

        Args:
            styles_dir: Directory containing .md output style files
                       (default: ~/.claude/lib/output_styles)
        """
        self.styles_dir = styles_dir or Path.home() / ".claude/lib/output_styles"
        self.styles_cache: Dict[str, OutputStyle] = {}

        # Create directory if it doesn't exist
        self.styles_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized OutputStylesManager (styles_dir: {self.styles_dir})")

        # Load all styles on initialization
        self.load_all_styles()

    def load_all_styles(self) -> int:
        """
        Load all .md output style files from styles directory.

        Returns:
            Number of styles loaded
        """
        loaded_count = 0

        if not self.styles_dir.exists():
            logger.warning(f"Styles directory does not exist: {self.styles_dir}")
            return 0

        for style_file in self.styles_dir.glob("*.md"):
            # Skip README and documentation files
            if style_file.name.upper() in ['README.MD', 'README.md', 'README.MD']:
                continue

            try:
                style = self._parse_markdown_file(style_file)
                self.styles_cache[style.name] = style
                loaded_count += 1
                logger.info(f"Loaded output style: {style.name} (v{style.version})")
            except Exception as e:
                logger.error(f"Failed to load style from {style_file}: {e}")

        logger.info(f"Loaded {loaded_count} output styles")
        return loaded_count

    def get_style(self, style_name: str, reload: bool = False) -> OutputStyle:
        """
        Get output style by name (from cache or load).

        Args:
            style_name: Name of the output style
            reload: Force reload from file (ignore cache)

        Returns:
            OutputStyle instance

        Raises:
            OutputStyleNotFoundError: If style not found
        """
        # Check cache first
        if not reload and style_name in self.styles_cache:
            return self.styles_cache[style_name]

        # Try to load from file
        style_file = self.styles_dir / f"{style_name}.md"

        if not style_file.exists():
            available = list(self.styles_cache.keys())
            raise OutputStyleNotFoundError(
                f"Output style '{style_name}' not found. "
                f"Available styles: {', '.join(available) if available else 'none'}"
            )

        try:
            style = self._parse_markdown_file(style_file)
            self.styles_cache[style.name] = style
            logger.info(f"Loaded output style: {style.name}")
            return style
        except Exception as e:
            raise OutputStyleParseError(f"Failed to parse {style_file}: {e}")

    def apply_style(self, base_prompt: str, style: OutputStyle) -> str:
        """
        Apply output style to base prompt.

        Appends style instructions to prompt to enforce structured output.

        Args:
            base_prompt: Original prompt
            style: OutputStyle to apply

        Returns:
            Enhanced prompt with style instructions
        """
        enhanced_parts = [
            "# TASK",
            base_prompt,
            "",
            "# OUTPUT STYLE REQUIREMENTS",
            "",
            style.system_instructions,
            "",
            "# SCHEMA",
            "",
            style.schema_definition,
            "",
            "# VALIDATION RULES",
            ""
        ]

        for rule in style.validation_rules:
            enhanced_parts.append(f"- {rule}")

        if style.example_output:
            enhanced_parts.extend([
                "",
                "# EXAMPLE OUTPUT",
                "",
                style.example_output
            ])

        enhanced_parts.extend([
            "",
            f"# CRITICAL: Output MUST be valid {style.schema_type.upper()} conforming to schema above.",
            f"# Start output immediately with {'{' if style.schema_type == 'json' else '---'}"
        ])

        enhanced_prompt = "\n".join(enhanced_parts)

        logger.debug(f"Applied output style '{style.name}' to prompt ({len(enhanced_prompt)} chars)")

        return enhanced_prompt

    def validate_response(
        self,
        response: str,
        style: OutputStyle
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Validate LLM response against output style schema.

        Args:
            response: Raw LLM response
            style: OutputStyle to validate against

        Returns:
            Tuple of (is_valid, parsed_data, error_message)
        """
        try:
            # Extract structured data based on schema type
            if style.schema_type == "json":
                parsed_data = self._extract_json_from_response(response)
                if parsed_data is None:
                    return False, None, "Could not extract valid JSON from response"

                # Validate JSON structure
                if style.validation_mode == "schema_strict":
                    is_valid, error = self._validate_json_schema(parsed_data, style)
                    if not is_valid:
                        return False, parsed_data, error

                return True, parsed_data, None

            elif style.schema_type == "yaml":
                parsed_data = self._extract_yaml_from_response(response)
                if parsed_data is None:
                    return False, None, "Could not extract valid YAML from response"

                # Validate YAML structure
                if style.validation_mode == "schema_strict":
                    is_valid, error = self._validate_yaml_schema(parsed_data, style)
                    if not is_valid:
                        return False, parsed_data, error

                return True, parsed_data, None

            elif style.schema_type == "markdown":
                # For markdown, just return the response as-is
                return True, response, None

            else:
                return False, None, f"Unsupported schema type: {style.schema_type}"

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return False, None, f"Validation exception: {str(e)}"

    def _parse_markdown_file(self, file_path: Path) -> OutputStyle:
        """
        Parse .md file with YAML frontmatter into OutputStyle.

        Expected format:
        ---
        name: critic_judge
        version: 1.0.0
        model: claude-opus-4-20250514
        ...
        ---
        # System Instructions
        ...

        Args:
            file_path: Path to .md file

        Returns:
            OutputStyle instance
        """
        content = file_path.read_text()

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)

        if not frontmatter_match:
            raise OutputStyleParseError(f"No YAML frontmatter found in {file_path}")

        frontmatter_yaml = frontmatter_match.group(1)
        markdown_content = frontmatter_match.group(2)

        # Parse frontmatter
        try:
            metadata = yaml.safe_load(frontmatter_yaml)
        except yaml.YAMLError as e:
            raise OutputStyleParseError(f"Invalid YAML frontmatter: {e}")

        # Extract sections from markdown content
        sections = self._extract_markdown_sections(markdown_content)

        # Build OutputStyle
        style = OutputStyle(
            name=metadata.get("name", file_path.stem),
            version=metadata.get("version", "1.0.0"),
            model=metadata.get("model"),
            enforcement=metadata.get("enforcement", "strict"),
            schema_type=metadata.get("schema_type", "json"),
            schema_ref=metadata.get("schema_ref"),
            temperature=float(metadata.get("temperature", 0.0)),
            max_tokens=int(metadata.get("max_tokens", 4000)),
            retry_on_parse_error=bool(metadata.get("retry_on_parse_error", True)),
            retry_attempts=int(metadata.get("retry_attempts", 3)),
            validation_mode=metadata.get("validation_mode", "schema_strict"),
            system_instructions=sections.get("system_instructions", ""),
            schema_definition=sections.get("schema", ""),
            example_output=sections.get("example_output", ""),
            validation_rules=sections.get("validation_rules", []),
            file_path=file_path
        )

        return style

    def _extract_markdown_sections(self, markdown: str) -> Dict[str, Any]:
        """
        Extract sections from markdown content.

        Looks for sections like:
        ## Output Schema
        ## Validation Rules
        ## Example Output

        Args:
            markdown: Markdown content

        Returns:
            Dict mapping section names to content
        """
        sections = {}

        # Extract system instructions (everything before first h2)
        first_h2_match = re.search(r'^##\s+', markdown, re.MULTILINE)
        if first_h2_match:
            sections["system_instructions"] = markdown[:first_h2_match.start()].strip()
        else:
            sections["system_instructions"] = markdown.strip()

        # Extract schema (look for "Output Schema" or "Schema" section)
        schema_match = re.search(
            r'##\s+(?:Output\s+)?Schema.*?\n(.*?)(?=\n##|\Z)',
            markdown,
            re.DOTALL | re.IGNORECASE
        )
        if schema_match:
            sections["schema"] = schema_match.group(1).strip()

        # Extract example output
        example_match = re.search(
            r'##\s+Example\s+Output.*?\n(.*?)(?=\n##|\Z)',
            markdown,
            re.DOTALL | re.IGNORECASE
        )
        if example_match:
            sections["example_output"] = example_match.group(1).strip()

        # Extract validation rules
        rules_match = re.search(
            r'##\s+Validation\s+Rules.*?\n(.*?)(?=\n##|\Z)',
            markdown,
            re.DOTALL | re.IGNORECASE
        )
        if rules_match:
            rules_text = rules_match.group(1).strip()
            # Extract bullet points
            rules = re.findall(r'^\s*[-*]\s+(.+)$', rules_text, re.MULTILINE)
            sections["validation_rules"] = rules

        return sections

    def _extract_json_from_response(self, response: str) -> Optional[dict]:
        """
        Extract JSON from response (handles markdown code blocks, extra text).

        Strategies:
        1. Try parsing entire response as JSON
        2. Extract JSON from ```json code block
        3. Find first { and last } and parse that

        Args:
            response: LLM response

        Returns:
            Parsed JSON dict or None
        """
        # Strategy 1: Parse entire response
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from code block
        code_block_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find JSON object boundaries
        first_brace = response.find('{')
        last_brace = response.rfind('}')

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(response[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass

        logger.warning("Could not extract valid JSON from response")
        return None

    def _extract_yaml_from_response(self, response: str) -> Optional[dict]:
        """
        Extract YAML from response.

        Args:
            response: LLM response

        Returns:
            Parsed YAML dict or None
        """
        # Try parsing entire response
        try:
            return yaml.safe_load(response.strip())
        except yaml.YAMLError:
            pass

        # Extract from code block
        code_block_match = re.search(r'```(?:yaml|yml)?\s*\n(.*?)\n```', response, re.DOTALL)
        if code_block_match:
            try:
                return yaml.safe_load(code_block_match.group(1).strip())
            except yaml.YAMLError:
                pass

        # Try extracting YAML between --- markers
        yaml_match = re.search(r'---\s*\n(.*?)\n(?:---|\.\.\.)?\s*$', response, re.DOTALL)
        if yaml_match:
            try:
                return yaml.safe_load(yaml_match.group(1).strip())
            except yaml.YAMLError:
                pass

        logger.warning("Could not extract valid YAML from response")
        return None

    def _validate_json_schema(self, data: dict, style: OutputStyle) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON against schema_ref (ValidationReport, etc.)

        Args:
            data: Parsed JSON data
            style: OutputStyle with schema_ref

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation - check for required keys based on schema_ref
        if style.schema_ref == "ValidationReport":
            required_keys = ["overall_status", "results", "total_findings"]
            for key in required_keys:
                if key not in data:
                    return False, f"Missing required key: {key}"

            # Validate overall_status values
            valid_statuses = ["PASS", "FAIL", "WARNING"]
            if data["overall_status"] not in valid_statuses:
                return False, f"Invalid overall_status: {data['overall_status']} (must be one of {valid_statuses})"

            # Validate results structure
            if not isinstance(data["results"], dict):
                return False, "results must be a dict"

            return True, None

        # If no schema_ref, just check it's a valid dict
        if not isinstance(data, dict):
            return False, "Response must be a JSON object (dict)"

        return True, None

    def _validate_yaml_schema(self, data: dict, style: OutputStyle) -> Tuple[bool, Optional[str]]:
        """
        Validate YAML against expected structure.

        Args:
            data: Parsed YAML data
            style: OutputStyle

        Returns:
            Tuple of (is_valid, error_message)
        """
        # For refinement_feedback style
        if style.name == "refinement_feedback":
            required_keys = ["iteration", "validation_status", "feedback", "regeneration_prompt"]
            for key in required_keys:
                if key not in data:
                    return False, f"Missing required key: {key}"

            # Validate feedback is a list
            if not isinstance(data["feedback"], list):
                return False, "feedback must be a list"

            # Validate each feedback item has required fields
            for item in data["feedback"]:
                if not isinstance(item, dict):
                    return False, "Each feedback item must be a dict"
                required_feedback_keys = ["priority", "location", "issue", "action"]
                for key in required_feedback_keys:
                    if key not in item:
                        return False, f"Feedback item missing required key: {key}"

            return True, None

        # Default validation
        if not isinstance(data, dict):
            return False, "Response must be a YAML object (dict)"

        return True, None

    def list_styles(self) -> List[str]:
        """
        List all available output style names.

        Returns:
            List of style names
        """
        return list(self.styles_cache.keys())

    def get_style_info(self, style_name: str) -> Dict[str, Any]:
        """
        Get metadata about an output style.

        Args:
            style_name: Name of style

        Returns:
            Dict with style metadata
        """
        style = self.get_style(style_name)
        return style.to_dict()

    def reload_styles(self) -> int:
        """
        Reload all styles from disk (clear cache and reload).

        Returns:
            Number of styles loaded
        """
        self.styles_cache.clear()
        return self.load_all_styles()


# ==================== CONVENIENCE FUNCTIONS ====================

def apply_output_style(prompt: str, style_name: str) -> str:
    """
    Convenience function to apply output style to prompt.

    Args:
        prompt: Base prompt
        style_name: Name of output style

    Returns:
        Enhanced prompt
    """
    manager = OutputStylesManager()
    style = manager.get_style(style_name)
    return manager.apply_style(prompt, style)


def validate_output_style(response: str, style_name: str) -> Tuple[bool, Any, Optional[str]]:
    """
    Convenience function to validate response against output style.

    Args:
        response: LLM response
        style_name: Name of output style

    Returns:
        Tuple of (is_valid, parsed_data, error_message)
    """
    manager = OutputStylesManager()
    style = manager.get_style(style_name)
    return manager.validate_response(response, style)
