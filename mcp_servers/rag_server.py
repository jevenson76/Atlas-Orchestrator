#!/usr/bin/env python3
"""
Agentic RAG MCP Server
Exposes advanced RAG workflows with routing and self-reflection via MCP.

This MCP server provides access to the Agentic RAG Pipeline for complex
query answering with intelligent routing, multi-hop retrieval, and
self-reflective validation before synthesis.

Exposed Prompts:
- /rag/analyze-complex-query: Execute 4-step agentic RAG workflow

Architecture:
- Uses AgenticRAGPipeline orchestrator
- Coordinates Router (Haiku 4.5), Retriever (Haiku 4.5), Critic (Opus 4.1), Synthesizer (Sonnet 4.5)
- Enforces analyst output style for structured JSON reports
- Self-reflection validates context quality before synthesis
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

# Import AgenticRAGPipeline orchestrator
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_rag_pipeline import AgenticRAGPipeline, analyze_complex_query
from observability.event_emitter import EventEmitter

# RAG System (optional)
try:
    from rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAG system not available - will use agent fallback")

logger = logging.getLogger(__name__)


class AgenticRAGMCPServer:
    """
    Agentic RAG MCP Server.

    Exposes advanced RAG capabilities with routing and self-reflection via MCP.

    Workflow (triggered by /rag/analyze-complex-query prompt):
    1. Parse query and source_path from prompt arguments
    2. Initialize AgenticRAGPipeline orchestrator
    3. Execute 4-step workflow:
       - Routing: Analyze query and choose retrieval strategy (Haiku 4.5)
       - Retrieval: Execute retrieval based on routing (Haiku 4.5 + RAG)
       - Validation: Self-reflection on context quality (Opus 4.1)
       - Synthesis: Generate structured report (Sonnet 4.5 + analyst style)
    4. Return structured report with validation results

    MCP Integration:
    - Prompts: High-level natural language interface
    - Tools: Direct programmatic access
    - Resources: Query history access (future)
    """

    def __init__(
        self,
        rag_system: Optional['RAGSystem'] = None,
        max_retrieval_iterations: int = 2,
        min_confidence_threshold: float = 0.7,
        top_k: int = 10
    ):
        """
        Initialize Agentic RAG MCP Server.

        Args:
            rag_system: RAG system for vector retrieval (optional)
            max_retrieval_iterations: Max retrieval attempts if confidence low
            min_confidence_threshold: Minimum confidence to proceed (0.0-1.0)
            top_k: Number of chunks to retrieve per query
        """
        self.server = Server("agentic-rag-server")
        self.rag_system = rag_system
        self.max_retrieval_iterations = max_retrieval_iterations
        self.min_confidence_threshold = min_confidence_threshold
        self.top_k = top_k

        # Observability
        self.event_emitter = EventEmitter()

        # Initialize orchestrator
        self.pipeline = AgenticRAGPipeline(
            rag_system=self.rag_system,
            max_retrieval_iterations=self.max_retrieval_iterations,
            min_confidence_threshold=self.min_confidence_threshold,
            top_k=self.top_k
        )

        # Register handlers
        self._register_prompts()
        self._register_tools()

        logger.info(
            f"Agentic RAG MCP Server initialized (RAG available: {RAG_AVAILABLE}, "
            f"max_iterations: {max_retrieval_iterations}, min_confidence: {min_confidence_threshold})"
        )

    def _register_prompts(self):
        """Register MCP prompts."""

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """List available prompts."""
            return [
                Prompt(
                    name="analyze-complex-query",
                    description=(
                        "Execute the complete Agentic RAG workflow for complex query answering. "
                        "Uses intelligent routing (Haiku 4.5) to choose optimal retrieval strategy, "
                        "performs context retrieval (Haiku 4.5 + RAG), validates context quality "
                        "with self-reflection (Opus 4.1), and generates structured report "
                        "(Sonnet 4.5 + analyst output style)."
                    ),
                    arguments=[
                        PromptArgument(
                            name="query",
                            description="Complex query requiring analysis",
                            required=True
                        ),
                        PromptArgument(
                            name="source_path",
                            description="Path to data source (optional)",
                            required=False
                        )
                    ]
                )
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> PromptMessage:
            """Get a specific prompt."""
            if name != "analyze-complex-query":
                raise ValueError(f"Unknown prompt: {name}")

            # Extract arguments
            query = arguments.get("query")
            source_path = arguments.get("source_path")

            if not query:
                raise ValueError("query is a required argument")

            # Execute Agentic RAG workflow
            logger.info(f"Executing Agentic RAG workflow (query: {query[:50]}...)")

            try:
                result = await self.pipeline.analyze_query(
                    query=query,
                    source_path=source_path
                )

                # Format response message
                response_content = self._format_analysis_response(result)

                return PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=response_content
                    )
                )

            except Exception as e:
                logger.error(f"Agentic RAG workflow failed: {e}", exc_info=True)
                error_message = f"❌ **Agentic RAG Analysis Failed**\n\nError: {str(e)}"
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
                    name="analyze_complex_query",
                    description=(
                        "Execute the complete Agentic RAG workflow for complex query answering. "
                        "Includes routing, retrieval, self-reflection, and synthesis."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Complex query requiring analysis"
                            },
                            "source_path": {
                                "type": "string",
                                "description": "Path to data source (optional)"
                            },
                            "include_validation": {
                                "type": "boolean",
                                "description": "Include detailed validation results in response",
                                "default": False
                            },
                            "include_routing": {
                                "type": "boolean",
                                "description": "Include routing decision details in response",
                                "default": False
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Call a tool."""
            if name != "analyze_complex_query":
                raise ValueError(f"Unknown tool: {name}")

            # Extract arguments
            query = arguments["query"]
            source_path = arguments.get("source_path")
            include_validation = arguments.get("include_validation", False)
            include_routing = arguments.get("include_routing", False)

            # Execute workflow
            logger.info(f"Tool call: analyze_complex_query (query: {query[:50]}...)")

            try:
                result = await self.pipeline.analyze_query(
                    query=query,
                    source_path=source_path
                )

                # Build response
                response = {
                    "query_id": result["query_id"],
                    "status": result["status"],
                    "query": result["query"],
                    "report": result["report"],
                    "metadata": result["metadata"]
                }

                if include_validation:
                    response["validation_result"] = result["validation_result"]

                if include_routing:
                    response["routing_decision"] = result["routing_decision"]

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

    def _format_analysis_response(self, result: Dict[str, Any]) -> str:
        """
        Format analysis result as human-readable markdown response.

        Args:
            result: Analysis result

        Returns:
            Formatted markdown string
        """
        status_emoji = "✅" if result["status"] == "success" else "⚠️"

        # Extract key information
        routing = result["routing_decision"]
        retrieval = result["retrieved_context"]
        validation = result["validation_result"]
        report = result["report"]
        metadata = result["metadata"]

        # Build response
        lines = [
            f"{status_emoji} **Agentic RAG Analysis Complete**",
            "",
            f"**Query ID:** `{result['query_id']}`",
            f"**Status:** {result['status']}",
            f"**Confidence:** {validation['confidence_score']:.2f} ({validation['confidence_level']})",
            f"**Duration:** {metadata['duration_seconds']:.2f}s",
            ""
        ]

        # Add workflow execution details
        lines.extend([
            "## Workflow Execution",
            "",
            "### STEP 1: Query Routing",
            f"- **Model:** {metadata['router_model']}",
            f"- **Strategy:** {routing.get('recommended_strategy', 'unknown')}",
            f"- **Complexity:** {routing.get('query_complexity', 'unknown')}",
            f"- **Rationale:** {routing.get('rationale', 'N/A')}",
            ""
        ])

        if routing.get("key_concepts"):
            lines.append(f"- **Key Concepts:** {', '.join(routing['key_concepts'])}")
            lines.append("")

        lines.extend([
            "### STEP 2: Context Retrieval",
            f"- **Model:** {metadata['retriever_model']}",
            f"- **Method:** {retrieval['metadata'].get('method', 'unknown')}",
            f"- **Chunks Retrieved:** {retrieval['metadata'].get('total_chunks', 0)}",
            f"- **Iterations:** {retrieval['metadata'].get('iterations', 0)}",
            ""
        ])

        lines.extend([
            "### STEP 3: Self-Reflection (Validation)",
            f"- **Model:** {metadata['critic_model']} (Opus 4.1 - Critical Review)",
            f"- **Relevance Score:** {validation.get('relevance_score', 0):.2f}",
            f"- **Completeness Score:** {validation.get('completeness_score', 0):.2f}",
            f"- **Confidence Score:** {validation.get('confidence_score', 0):.2f}",
            f"- **Confidence Level:** {validation.get('confidence_level', 'UNKNOWN')}",
            f"- **Recommendation:** {validation.get('recommendation', 'UNKNOWN')}",
            ""
        ])

        if validation.get("has_contradictions"):
            lines.append(f"⚠️  **Contradictions Detected:** {validation.get('contradiction_details', 'See details')}")
            lines.append("")

        if validation.get("gaps_identified"):
            lines.append("**Gaps Identified:**")
            for gap in validation["gaps_identified"]:
                lines.append(f"- {gap}")
            lines.append("")

        # Add synthesis step if report generated
        if report:
            lines.extend([
                "### STEP 4: Synthesis",
                f"- **Model:** {metadata.get('synthesizer_model', 'N/A')}",
                f"- **Output Style:** analyst (structured JSON)",
                ""
            ])

            # Add executive summary if available
            if isinstance(report, dict) and "executive_summary" in report:
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
        else:
            lines.extend([
                "### STEP 4: Synthesis - SKIPPED",
                f"**Reason:** Insufficient confidence ({validation['confidence_score']:.2f} < {self.min_confidence_threshold:.2f})",
                "",
                "**Recommendation:** Retrieve additional context or refine query",
                ""
            ])

        # Add full report as JSON if available
        if report:
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

    parser = argparse.ArgumentParser(description="Agentic RAG MCP Server")
    parser.add_argument(
        "--rag-index",
        type=Path,
        help="Path to RAG index directory"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum retrieval iterations (default: 2)"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold (default: 0.7)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of chunks to retrieve (default: 10)"
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

    # Initialize RAG system if index provided
    rag_system = None
    if args.rag_index and RAG_AVAILABLE:
        try:
            rag_system = RAGSystem(index_dir=args.rag_index)
            logger.info(f"RAG system initialized from index: {args.rag_index}")
        except Exception as e:
            logger.warning(f"Failed to initialize RAG system: {e}")

    # Create and run server
    server = AgenticRAGMCPServer(
        rag_system=rag_system,
        max_retrieval_iterations=args.max_iterations,
        min_confidence_threshold=args.min_confidence,
        top_k=args.top_k
    )

    logger.info("Starting Agentic RAG MCP Server...")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
