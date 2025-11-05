#!/usr/bin/env python3
"""
Analyst MCP Server
Exposes enterprise analyst report generation via Model Context Protocol.

This MCP server provides a high-level interface to the complete ZTE pipeline
for generating validated, structured enterprise analyst reports.

Exposed Prompts:
- /analyst/generate-report: Generate a validated analyst report from a data source

Architecture:
- Uses EnterpriseAnalyst orchestrator
- Coordinates Scout (Haiku 3.5), Master (Sonnet 4.5), Validation (Opus 4)
- Enforces analyst output style for structured JSON reports
- Applies critic_judge validation with automatic refinement
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
)

# Import EnterpriseAnalyst orchestrator
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from enterprise_analyst import EnterpriseAnalyst, generate_analyst_report
from observability.event_emitter import EventEmitter

logger = logging.getLogger(__name__)


class AnalystMCPServer:
    """
    Analyst MCP Server.

    Exposes enterprise analyst report generation capabilities via MCP.

    Workflow (triggered by /analyst/generate-report prompt):
    1. Parse source_path and query from prompt arguments
    2. Initialize EnterpriseAnalyst orchestrator
    3. Execute 5-step ZTE pipeline:
       - Retrieval: Scout Agent (Haiku 3.5) via RAG
       - Synthesis: Master Agent (Sonnet 4.5) with analyst output style
       - Validation: ValidationOrchestrator (Opus 4) with critic_judge
       - Refinement: RefinementLoop if validation fails
       - Finalization: Archive validated report
    4. Return structured report with validation results

    MCP Integration:
    - Prompts: High-level natural language interface
    - Tools: Direct programmatic access (future)
    - Resources: Report archive access (future)
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        enable_rag: bool = True,
        max_refinement_iterations: int = 3,
        min_validation_score: float = 85.0
    ):
        """
        Initialize Analyst MCP Server.

        Args:
            project_root: Root directory for validation context
            output_dir: Directory for archiving reports
            enable_rag: Whether to use RAG system for retrieval
            max_refinement_iterations: Maximum refinement attempts
            min_validation_score: Minimum score for validation pass
        """
        self.server = Server("analyst-server")
        self.project_root = Path(project_root or ".")
        self.output_dir = Path(output_dir or self.project_root / "reports")
        self.enable_rag = enable_rag
        self.max_refinement_iterations = max_refinement_iterations
        self.min_validation_score = min_validation_score

        # Observability
        self.event_emitter = EventEmitter()

        # Initialize orchestrator
        self.analyst = EnterpriseAnalyst(
            project_root=self.project_root,
            output_dir=self.output_dir,
            enable_rag=self.enable_rag,
            max_refinement_iterations=self.max_refinement_iterations,
            min_validation_score=self.min_validation_score
        )

        # Register handlers
        self._register_prompts()
        self._register_tools()

        logger.info(
            f"Analyst MCP Server initialized (project: {self.project_root}, "
            f"output: {self.output_dir}, RAG: {self.enable_rag})"
        )

    def _register_prompts(self):
        """Register MCP prompts."""

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """List available prompts."""
            return [
                Prompt(
                    name="generate-report",
                    description=(
                        "Generate a validated enterprise analyst report from a data source. "
                        "Uses the complete ZTE pipeline: Scout Agent (Haiku 3.5) for retrieval, "
                        "Master Agent (Sonnet 4.5) for generation with analyst output style, "
                        "ValidationOrchestrator (Opus 4) for validation with critic_judge, "
                        "and RefinementLoop for automatic correction if needed."
                    ),
                    arguments=[
                        PromptArgument(
                            name="source_path",
                            description="Path to data source (file, directory, or URL)",
                            required=True
                        ),
                        PromptArgument(
                            name="query",
                            description="Analysis query or objective",
                            required=True
                        ),
                        PromptArgument(
                            name="analyst_name",
                            description="Name of analyst for report metadata (optional)",
                            required=False
                        )
                    ]
                )
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> PromptMessage:
            """Get a specific prompt."""
            if name != "generate-report":
                raise ValueError(f"Unknown prompt: {name}")

            # Extract arguments
            source_path = arguments.get("source_path")
            query = arguments.get("query")
            analyst_name = arguments.get("analyst_name", "Claude Enterprise Analyst")

            if not source_path or not query:
                raise ValueError("source_path and query are required arguments")

            # Generate report using orchestrator
            logger.info(f"Generating analyst report (source: {source_path}, query: {query[:50]}...)")

            try:
                result = await self.analyst.generate_report(
                    source_path=source_path,
                    query=query,
                    analyst_name=analyst_name
                )

                # Format response message
                response_content = self._format_report_response(result)

                return PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=response_content
                    )
                )

            except Exception as e:
                logger.error(f"Report generation failed: {e}", exc_info=True)
                error_message = f"❌ **Report Generation Failed**\n\nError: {str(e)}"
                return PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=error_message
                    )
                )

    def _register_tools(self):
        """Register MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="generate_analyst_report",
                    description=(
                        "Generate a validated enterprise analyst report from a data source. "
                        "Executes the complete ZTE pipeline with automatic validation and refinement."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_path": {
                                "type": "string",
                                "description": "Path to data source (file, directory, or URL)"
                            },
                            "query": {
                                "type": "string",
                                "description": "Analysis query or objective"
                            },
                            "analyst_name": {
                                "type": "string",
                                "description": "Name of analyst for report metadata",
                                "default": "Claude Enterprise Analyst"
                            },
                            "include_validation": {
                                "type": "boolean",
                                "description": "Include full validation report in response",
                                "default": False
                            }
                        },
                        "required": ["source_path", "query"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Call a tool."""
            if name != "generate_analyst_report":
                raise ValueError(f"Unknown tool: {name}")

            # Extract arguments
            source_path = arguments["source_path"]
            query = arguments["query"]
            analyst_name = arguments.get("analyst_name", "Claude Enterprise Analyst")
            include_validation = arguments.get("include_validation", False)

            # Generate report
            logger.info(f"Tool call: generate_analyst_report (source: {source_path}, query: {query[:50]}...)")

            try:
                result = await self.analyst.generate_report(
                    source_path=source_path,
                    query=query,
                    analyst_name=analyst_name
                )

                # Build response
                response = {
                    "report_id": result["report_id"],
                    "status": result["status"],
                    "report": result["report"],
                    "metadata": result["metadata"]
                }

                if include_validation:
                    response["validation"] = result["validation_report"]

                if result.get("archive_path"):
                    response["archive_path"] = result["archive_path"]

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(response, indent=2)
                    )
                ]

            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": str(e),
                            "status": "failed"
                        }, indent=2)
                    )
                ]

    def _format_report_response(self, result: Dict[str, Any]) -> str:
        """
        Format report result as human-readable markdown response.

        Args:
            result: Report generation result

        Returns:
            Formatted markdown string
        """
        status_emoji = "✅" if result["status"] == "success" else "⚠️"

        # Extract key information
        report = result["report"]
        metadata = result["metadata"]
        validation_report = result["validation_report"]

        # Build response
        lines = [
            f"{status_emoji} **Enterprise Analyst Report Generated**",
            "",
            f"**Report ID:** `{result['report_id']}`",
            f"**Status:** {result['status']}",
            f"**Validation Score:** {validation_report['average_score']:.1f}/100",
            f"**Duration:** {metadata['duration_seconds']:.2f}s",
            ""
        ]

        # Add metadata
        lines.extend([
            "## Pipeline Execution",
            f"- **Retrieval Model:** {metadata['retrieval_model']}",
            f"- **Generation Model:** {metadata['generation_model']}",
            f"- **Validation Model:** {metadata['validation_model']}",
            f"- **Output Style:** {metadata['output_style']}",
            f"- **Refinement Iterations:** {metadata['refinement_iterations']}",
            ""
        ])

        # Add executive summary if available
        if "executive_summary" in report:
            exec_summary = report["executive_summary"]
            lines.extend([
                "## Executive Summary",
                "",
                f"**Overview:** {exec_summary.get('overview', 'N/A')}",
                "",
                f"**Risk Level:** {exec_summary.get('risk_level', 'UNKNOWN')}",
                f"**Compliance Status:** {exec_summary.get('compliance_status', 'UNKNOWN')}",
                ""
            ])

            if "key_findings" in exec_summary and exec_summary["key_findings"]:
                lines.append("**Key Findings:**")
                for finding in exec_summary["key_findings"]:
                    lines.append(f"- {finding}")
                lines.append("")

        # Add validation details
        if validation_report["overall_status"] != "PASS":
            lines.extend([
                "## Validation Issues",
                f"- **Critical Issues:** {validation_report['critical_count']}",
                f"- **High Issues:** {validation_report['high_count']}",
                ""
            ])

        # Add archive path if available
        if result.get("archive_path"):
            lines.extend([
                "## Archive",
                f"Report archived to: `{result['archive_path']}`",
                ""
            ])

        # Add full report as JSON
        lines.extend([
            "## Full Report (JSON)",
            "```json",
            json.dumps(report, indent=2),
            "```",
            ""
        ])

        return "\n".join(lines)

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyst MCP Server")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Root directory for validation context"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for archiving reports (default: {project_root}/reports)"
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG system for retrieval"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum refinement iterations (default: 3)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=85.0,
        help="Minimum validation score (default: 85.0)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run server
    server = AnalystMCPServer(
        project_root=args.project_root,
        output_dir=args.output_dir,
        enable_rag=not args.no_rag,
        max_refinement_iterations=args.max_iterations,
        min_validation_score=args.min_score
    )

    logger.info("Starting Analyst MCP Server...")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
