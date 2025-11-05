"""
Output Style Manager - Manages system prompt styles for agents.

Provides deterministic control over agent behavior through explicit style definitions.

Architecture Principle: "The system prompt builds the agent"
- Explicit > Implicit
- Reusable > One-off
- Observable > Hidden
- Testable > Assumed
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OutputStyleManager:
    """
    Manages output styles (system prompts) for agents.

    Provides:
    - Loading style definitions from markdown files
    - Style versioning and metadata tracking
    - Usage statistics
    - Style recommendations based on agent roles
    - A/B testing support
    - Extensibility for custom styles

    Directory Structure:
        ~/.claude/output_styles/
            code.md
            detailed.md
            json_strict.md
            validator.md
            critic.md
            architect.md
            analyst.md
            orchestrator.md
            .registry/
                style_registry.json
                usage_stats.json
    """

    def __init__(self, styles_dir: Optional[str] = None):
        """
        Initialize the OutputStyleManager.

        Args:
            styles_dir: Path to styles directory. Defaults to ~/.claude/output_styles/
        """
        if styles_dir is None:
            home = Path.home()
            self.styles_dir = home / ".claude" / "output_styles"
        else:
            self.styles_dir = Path(styles_dir)

        self.registry_dir = self.styles_dir / ".registry"
        self.registry_file = self.registry_dir / "style_registry.json"
        self.stats_file = self.registry_dir / "usage_stats.json"

        # Ensure directories exist
        self.styles_dir.mkdir(parents=True, exist_ok=True)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        # Initialize registry and stats
        self._initialize_registry()
        self._initialize_stats()

        # Role to style mappings (default recommendations)
        self.role_mappings = {
            "code-generator": "code",
            "explainer": "detailed",
            "api-client": "json_strict",
            "validator": "validator",
            "security-critic": "critic",
            "performance-critic": "critic",
            "architecture-critic": "critic",
            "code-quality-critic": "critic",
            "documentation-critic": "critic",
            "architect": "architect",
            "researcher": "analyst",
            "analyst": "analyst",
            "orchestrator": "orchestrator",
            "project-manager": "orchestrator",
            "default": "code"
        }

    def _initialize_registry(self) -> None:
        """Initialize the style registry if it doesn't exist."""
        if not self.registry_file.exists():
            registry = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "styles": {}
            }
            self._save_registry(registry)

    def _initialize_stats(self) -> None:
        """Initialize usage statistics if they don't exist."""
        if not self.stats_file.exists():
            stats = {
                "total_loads": 0,
                "style_usage": {},
                "role_usage": {},
                "last_updated": datetime.utcnow().isoformat()
            }
            self._save_stats(stats)

    def _load_registry(self) -> Dict[str, Any]:
        """Load the style registry."""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            return {"version": "1.0", "styles": {}}

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        """Save the style registry."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")

    def _load_stats(self) -> Dict[str, Any]:
        """Load usage statistics."""
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            return {"total_loads": 0, "style_usage": {}, "role_usage": {}}

    def _save_stats(self, stats: Dict[str, Any]) -> None:
        """Save usage statistics."""
        try:
            stats["last_updated"] = datetime.utcnow().isoformat()
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

    def _update_usage_stats(self, style_name: str, role: Optional[str] = None) -> None:
        """Update usage statistics when a style is loaded."""
        stats = self._load_stats()

        # Update total loads
        stats["total_loads"] = stats.get("total_loads", 0) + 1

        # Update style usage
        if "style_usage" not in stats:
            stats["style_usage"] = {}
        stats["style_usage"][style_name] = stats["style_usage"].get(style_name, 0) + 1

        # Update role usage if provided
        if role:
            if "role_usage" not in stats:
                stats["role_usage"] = {}
            stats["role_usage"][role] = stats["role_usage"].get(role, 0) + 1

        self._save_stats(stats)

    def load_style(self, style_name: str, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a style definition from markdown file.

        Args:
            style_name: Name of the style (e.g., 'code', 'detailed', 'critic')
            role: Optional role name for usage tracking

        Returns:
            Dict containing:
                - name: Style name
                - content: Full markdown content
                - system_prompt: Extracted system prompt text
                - version: Style version
                - metadata: Additional metadata

        Raises:
            FileNotFoundError: If style file doesn't exist
            ValueError: If style is not registered
        """
        # Check if style is registered
        registry = self._load_registry()
        if style_name not in registry.get("styles", {}):
            # Try to auto-register if file exists
            style_file = self.styles_dir / f"{style_name}.md"
            if style_file.exists():
                self.register_style(style_name, str(style_file), {})
            else:
                raise FileNotFoundError(
                    f"Style '{style_name}' not found at {style_file}"
                )

        # Load style file
        style_info = registry["styles"][style_name]
        style_path = Path(style_info["file_path"])

        if not style_path.exists():
            raise FileNotFoundError(f"Style file not found: {style_path}")

        # Read style content
        with open(style_path, 'r') as f:
            content = f.read()

        # Update usage statistics
        self._update_usage_stats(style_name, role)

        # Return style data
        return {
            "name": style_name,
            "content": content,
            "system_prompt": content,  # Full markdown is the system prompt
            "version": style_info.get("version", "1.0"),
            "metadata": style_info.get("metadata", {}),
            "file_path": str(style_path)
        }

    def list_styles(self) -> List[str]:
        """
        List all registered styles.

        Returns:
            List of style names
        """
        registry = self._load_registry()
        return list(registry.get("styles", {}).keys())

    def get_style_metadata(self, style_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific style.

        Args:
            style_name: Name of the style

        Returns:
            Dict containing style metadata

        Raises:
            ValueError: If style doesn't exist
        """
        registry = self._load_registry()

        if style_name not in registry.get("styles", {}):
            raise ValueError(f"Style '{style_name}' not registered")

        style_info = registry["styles"][style_name]

        # Get usage stats
        stats = self._load_stats()
        usage_count = stats.get("style_usage", {}).get(style_name, 0)

        return {
            "name": style_name,
            "file_path": style_info["file_path"],
            "version": style_info.get("version", "1.0"),
            "registered_at": style_info.get("registered_at"),
            "metadata": style_info.get("metadata", {}),
            "usage_count": usage_count
        }

    def recommend_style_for_role(self, role: str) -> str:
        """
        Recommend a style based on agent role.

        Args:
            role: Agent role (e.g., 'validator', 'architect', 'code-generator')

        Returns:
            Recommended style name
        """
        # Check direct mapping
        if role in self.role_mappings:
            return self.role_mappings[role]

        # Check partial matches (e.g., 'security-critic' matches 'critic')
        for role_key, style in self.role_mappings.items():
            if role_key in role or role in role_key:
                return style

        # Default to 'code' style
        return self.role_mappings["default"]

    def register_style(
        self,
        style_name: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0"
    ) -> None:
        """
        Register a new style in the registry.

        Args:
            style_name: Name of the style
            file_path: Path to the markdown file
            metadata: Optional metadata dict
            version: Style version (default: "1.0")
        """
        registry = self._load_registry()

        if "styles" not in registry:
            registry["styles"] = {}

        # Check if file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Style file not found: {file_path}")

        # Register or update style
        registry["styles"][style_name] = {
            "file_path": file_path,
            "version": version,
            "registered_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        self._save_registry(registry)
        logger.info(f"Registered style: {style_name} (v{version})")

    def get_style_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for all styles.

        Returns:
            Dict containing:
                - total_loads: Total number of style loads
                - style_usage: Dict mapping style names to usage counts
                - role_usage: Dict mapping roles to usage counts
                - most_used_style: Most frequently used style
                - last_updated: Timestamp of last update
        """
        stats = self._load_stats()

        # Find most used style
        style_usage = stats.get("style_usage", {})
        most_used_style = None
        if style_usage:
            most_used_style = max(style_usage.items(), key=lambda x: x[1])[0]

        return {
            "total_loads": stats.get("total_loads", 0),
            "style_usage": style_usage,
            "role_usage": stats.get("role_usage", {}),
            "most_used_style": most_used_style,
            "last_updated": stats.get("last_updated")
        }

    def add_role_mapping(self, role: str, style_name: str) -> None:
        """
        Add or update a role-to-style mapping.

        Args:
            role: Role name
            style_name: Style to map to this role
        """
        self.role_mappings[role] = style_name
        logger.info(f"Added role mapping: {role} -> {style_name}")

    def get_all_role_mappings(self) -> Dict[str, str]:
        """
        Get all current role-to-style mappings.

        Returns:
            Dict mapping roles to style names
        """
        return self.role_mappings.copy()

    def validate_style(self, style_name: str) -> Dict[str, Any]:
        """
        Validate a style definition.

        Args:
            style_name: Name of the style to validate

        Returns:
            Dict containing:
                - valid: Boolean indicating if style is valid
                - errors: List of validation errors
                - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        try:
            # Check if registered
            registry = self._load_registry()
            if style_name not in registry.get("styles", {}):
                errors.append(f"Style '{style_name}' not registered")
                return {"valid": False, "errors": errors, "warnings": warnings}

            # Check if file exists
            style_info = registry["styles"][style_name]
            style_path = Path(style_info["file_path"])

            if not style_path.exists():
                errors.append(f"Style file not found: {style_path}")
            else:
                # Check file is readable and not empty
                with open(style_path, 'r') as f:
                    content = f.read()

                if not content.strip():
                    errors.append("Style file is empty")

                # Check for basic structure
                if "# " not in content:
                    warnings.append("Style file has no main heading")

                if "## Behavior" not in content:
                    warnings.append("Style file missing '## Behavior' section")

                if "## Output Format" not in content:
                    warnings.append("Style file missing '## Output Format' section")

                if "## Constraints" not in content:
                    warnings.append("Style file missing '## Constraints' section")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Singleton instance for convenience
_manager_instance = None


def get_style_manager() -> OutputStyleManager:
    """
    Get the singleton OutputStyleManager instance.

    Returns:
        OutputStyleManager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = OutputStyleManager()
    return _manager_instance
