#!/usr/bin/env python3
"""
Register Core Output Styles

Registers all 8 core output styles with the OutputStyleManager.
Run this script after creating or updating style definitions.

Usage:
    python3 ~/.claude/lib/register_output_styles.py

    # Or with verbose output
    python3 ~/.claude/lib/register_output_styles.py --verbose

Core Styles:
1. code - Concise working code
2. detailed - Comprehensive explanations
3. json_strict - Pure JSON output
4. validator - Pass/fail validation
5. critic - Fresh context evaluation
6. architect - System design thinking
7. analyst - Research synthesis
8. orchestrator - Workflow coordination
"""

import sys
import argparse
import logging
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent
sys.path.insert(0, str(lib_path))

from output_style_manager import OutputStyleManager

logger = logging.getLogger(__name__)


def register_core_styles(manager: OutputStyleManager, verbose: bool = False) -> None:
    """
    Register all 8 core output styles.

    Args:
        manager: OutputStyleManager instance
        verbose: Whether to print verbose output
    """
    # Define core styles with metadata
    core_styles = [
        {
            "name": "code",
            "description": "Concise working code with minimal comments",
            "use_cases": ["coding", "implementation", "quick fixes"],
            "category": "practical",
            "version": "1.0.0"
        },
        {
            "name": "detailed",
            "description": "Comprehensive explanations with examples",
            "use_cases": ["learning", "documentation", "tutorials"],
            "category": "educational",
            "version": "1.0.0"
        },
        {
            "name": "json_strict",
            "description": "Pure JSON output only (no markdown)",
            "use_cases": ["API responses", "structured data", "parsing"],
            "category": "structured",
            "version": "1.0.0"
        },
        {
            "name": "validator",
            "description": "Objective pass/fail validation with JSON output",
            "use_cases": ["code validation", "quality checks", "compliance"],
            "category": "quality",
            "version": "1.0.0"
        },
        {
            "name": "critic",
            "description": "Unbiased evaluation with fresh context principle",
            "use_cases": [
                "security review",
                "performance analysis",
                "architecture critique",
                "code quality review",
                "documentation review"
            ],
            "category": "quality",
            "version": "1.0.0"
        },
        {
            "name": "architect",
            "description": "High-level system design and architectural thinking",
            "use_cases": [
                "system design",
                "architecture planning",
                "technology decisions",
                "scalability planning"
            ],
            "category": "design",
            "version": "1.0.0"
        },
        {
            "name": "analyst",
            "description": "Research synthesis from multiple sources",
            "use_cases": [
                "market research",
                "competitive analysis",
                "technical comparison",
                "data synthesis"
            ],
            "category": "research",
            "version": "1.0.0"
        },
        {
            "name": "orchestrator",
            "description": "Multi-agent workflow coordination",
            "use_cases": [
                "workflow management",
                "result aggregation",
                "quality metrics",
                "phase coordination"
            ],
            "category": "coordination",
            "version": "1.0.0"
        }
    ]

    styles_dir = Path.home() / ".claude" / "output_styles"

    registered_count = 0
    failed_count = 0

    print("=" * 80)
    print("OUTPUT STYLES REGISTRATION")
    print("=" * 80)
    print(f"\nStyles directory: {styles_dir}")
    print(f"Registering {len(core_styles)} core styles...\n")

    for style_info in core_styles:
        name = style_info["name"]
        file_path = styles_dir / f"{name}.md"

        try:
            # Check if file exists
            if not file_path.exists():
                print(f"❌ {name:<15} FAILED - File not found: {file_path}")
                failed_count += 1
                continue

            # Register style
            manager.register_style(
                style_name=name,
                file_path=str(file_path),
                metadata=style_info,
                version=style_info["version"]
            )

            print(f"✅ {name:<15} REGISTERED")

            if verbose:
                print(f"   Description: {style_info['description']}")
                print(f"   Use cases: {', '.join(style_info['use_cases'][:2])}")
                print(f"   File: {file_path}")
                print()

            registered_count += 1

        except Exception as e:
            print(f"❌ {name:<15} FAILED - {e}")
            failed_count += 1
            if verbose:
                import traceback
                traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("REGISTRATION SUMMARY")
    print("=" * 80)
    print(f"✅ Registered: {registered_count}/{len(core_styles)}")
    if failed_count > 0:
        print(f"❌ Failed:     {failed_count}/{len(core_styles)}")
    print()

    # Show registry stats
    print("=" * 80)
    print("REGISTRY STATISTICS")
    print("=" * 80)

    all_styles = manager.list_styles()
    print(f"Total styles in registry: {len(all_styles)}")
    print(f"Registered styles: {', '.join(sorted(all_styles))}")
    print()

    # Validation
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)

    validation_failures = []
    for style_name in all_styles:
        result = manager.validate_style(style_name)
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"{style_name:<15} {status}")

        if not result["valid"]:
            validation_failures.append((style_name, result["errors"]))
            for error in result["errors"]:
                print(f"   ERROR: {error}")

        if verbose and result["warnings"]:
            for warning in result["warnings"]:
                print(f"   WARNING: {warning}")

    print()

    # Final status
    if failed_count == 0 and len(validation_failures) == 0:
        print("=" * 80)
        print("✅ ALL STYLES REGISTERED AND VALIDATED SUCCESSFULLY")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("⚠️  REGISTRATION COMPLETED WITH ISSUES")
        print("=" * 80)
        if failed_count > 0:
            print(f"   - {failed_count} styles failed to register")
        if validation_failures:
            print(f"   - {len(validation_failures)} styles failed validation")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Register core output styles with OutputStyleManager"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize manager
    try:
        manager = OutputStyleManager()
    except Exception as e:
        print(f"❌ Failed to initialize OutputStyleManager: {e}")
        return 1

    # Register styles
    exit_code = register_core_styles(manager, verbose=args.verbose)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
