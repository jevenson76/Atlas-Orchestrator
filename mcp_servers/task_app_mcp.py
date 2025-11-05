#!/usr/bin/env python3
"""
Task Application MCP Server
Simplified MCP wrapper for single-user ZTE Task Management

Exposes high-level task execution and monitoring capabilities via MCP protocol.
Removes all distribution/collaboration features (no Slack, email, etc.).

Architecture:
- Wraps existing MCP servers (validation, workflow orchestration, analyst, RAG)
- Provides unified task execution interface
- Streams observability data for UI consumption

Exposed Prompts:
- /task/submit: Submit task for execution (writes to ADZ)
- /task/status: Get status of task by ID
- /task/results: Get results of completed task
- /events/stream: Get latest events from observability system

Author: ZTE Platform
Version: 1.0.0
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Directory paths
DROPZONE_ROOT = Path.home() / "dropzone"
TASKS_DIR = DROPZONE_ROOT / "tasks"
RESULTS_DIR = DROPZONE_ROOT / "results"
ARCHIVE_DIR = DROPZONE_ROOT / "archive"
EVENTS_DIR = Path.home() / ".claude" / "logs" / "events"
STREAM_FILE = EVENTS_DIR / "stream.jsonl"

# Ensure directories exist
TASKS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# TASK APP MCP SERVER
# ============================================================================

class TaskAppMCPServer:
    """
    Simplified MCP server for single-user task management.

    Provides unified interface for:
    1. Task submission to ADZ
    2. Task status monitoring
    3. Result retrieval
    4. Event stream access
    """

    def __init__(self):
        """Initialize Task App MCP Server."""
        self.server = Server("task-app-server")
        self._register_prompts()
        self._register_tools()

        logger.info("Task App MCP Server initialized (single-user mode)")

    def _register_prompts(self):
        """Register MCP prompts."""

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """List available prompts."""
            return [
                Prompt(
                    name="submit-task",
                    description=(
                        "Submit a task to the ZTE pipeline via Agentic Drop Zone. "
                        "Task will be automatically processed and results saved to ~/dropzone/results/."
                    ),
                    arguments=[
                        PromptArgument(
                            name="task",
                            description="Task description (what to build)",
                            required=True
                        ),
                        PromptArgument(
                            name="workflow",
                            description="Workflow strategy (auto, specialized_roles, parallel, progressive)",
                            required=False
                        ),
                        PromptArgument(
                            name="language",
                            description="Programming language (python, javascript, etc.)",
                            required=False
                        ),
                        PromptArgument(
                            name="quality_target",
                            description="Quality target score (70-100)",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="get-task-status",
                    description="Get status of a submitted task by task ID",
                    arguments=[
                        PromptArgument(
                            name="task_id",
                            description="Task ID to query",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="get-task-results",
                    description="Get results of a completed task",
                    arguments=[
                        PromptArgument(
                            name="task_id",
                            description="Task ID to retrieve results for",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="stream-events",
                    description="Get latest events from observability system",
                    arguments=[
                        PromptArgument(
                            name="max_events",
                            description="Maximum number of events to return",
                            required=False
                        ),
                        PromptArgument(
                            name="filter_component",
                            description="Filter by component name",
                            required=False
                        )
                    ]
                )
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> PromptMessage:
            """Get a specific prompt."""

            # PROMPT 1: Submit Task
            if name == "submit-task":
                task = arguments.get("task")
                if not task:
                    return self._error_response("task is required")

                workflow = arguments.get("workflow", "auto")
                language = arguments.get("language", "python")
                quality_target = int(arguments.get("quality_target", "85"))

                # Build task data
                task_data = {
                    "task": task,
                    "workflow": workflow,
                    "context": {
                        "language": language,
                        "quality_target": quality_target
                    },
                    "priority": "normal"
                }

                # Submit to ADZ
                try:
                    task_id = await self._submit_task(task_data)
                    response = self._format_submission_response(task_id, task_data)
                    return PromptMessage(
                        role="assistant",
                        content=TextContent(type="text", text=response)
                    )
                except Exception as e:
                    logger.error(f"Task submission failed: {e}", exc_info=True)
                    return self._error_response(f"Failed to submit task: {str(e)}")

            # PROMPT 2: Get Task Status
            elif name == "get-task-status":
                task_id = arguments.get("task_id")
                if not task_id:
                    return self._error_response("task_id is required")

                try:
                    status = await self._get_task_status(task_id)
                    response = self._format_status_response(task_id, status)
                    return PromptMessage(
                        role="assistant",
                        content=TextContent(type="text", text=response)
                    )
                except Exception as e:
                    return self._error_response(f"Failed to get status: {str(e)}")

            # PROMPT 3: Get Task Results
            elif name == "get-task-results":
                task_id = arguments.get("task_id")
                if not task_id:
                    return self._error_response("task_id is required")

                try:
                    results = await self._get_task_results(task_id)
                    response = self._format_results_response(task_id, results)
                    return PromptMessage(
                        role="assistant",
                        content=TextContent(type="text", text=response)
                    )
                except Exception as e:
                    return self._error_response(f"Failed to get results: {str(e)}")

            # PROMPT 4: Stream Events
            elif name == "stream-events":
                max_events = int(arguments.get("max_events", "50"))
                filter_component = arguments.get("filter_component")

                try:
                    events = await self._get_events(max_events, filter_component)
                    response = self._format_events_response(events)
                    return PromptMessage(
                        role="assistant",
                        content=TextContent(type="text", text=response)
                    )
                except Exception as e:
                    return self._error_response(f"Failed to get events: {str(e)}")

            else:
                return self._error_response(f"Unknown prompt: {name}")

    def _register_tools(self):
        """Register MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="submit_task",
                    description="Submit task to ZTE pipeline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "Task description"},
                            "workflow": {"type": "string", "description": "Workflow strategy"},
                            "context": {"type": "object", "description": "Task context"}
                        },
                        "required": ["task"]
                    }
                ),
                Tool(
                    name="get_task_status",
                    description="Get task status by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "Task ID"}
                        },
                        "required": ["task_id"]
                    }
                ),
                Tool(
                    name="get_events",
                    description="Get latest observability events",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_events": {"type": "integer", "description": "Max events to return"},
                            "filter_component": {"type": "string", "description": "Filter by component"}
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Call a tool."""

            if name == "submit_task":
                task_id = await self._submit_task(arguments)
                return [TextContent(
                    type="text",
                    text=json.dumps({"task_id": task_id, "status": "submitted"}, indent=2)
                )]

            elif name == "get_task_status":
                status = await self._get_task_status(arguments["task_id"])
                return [TextContent(type="text", text=json.dumps(status, indent=2))]

            elif name == "get_events":
                events = await self._get_events(
                    arguments.get("max_events", 50),
                    arguments.get("filter_component")
                )
                return [TextContent(type="text", text=json.dumps(events, indent=2))]

            else:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    # ========================================================================
    # CORE METHODS
    # ========================================================================

    async def _submit_task(self, task_data: Dict[str, Any]) -> str:
        """
        Submit task to ADZ by writing file.

        Args:
            task_data: Task definition

        Returns:
            task_id
        """
        # Generate task ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_id = f"task_{timestamp}"

        # Write task file
        task_file = TASKS_DIR / f"{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Task submitted: {task_id}")
        return task_id

    async def _get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of task.

        Args:
            task_id: Task ID

        Returns:
            Status dictionary
        """
        # Check if task file exists (pending)
        task_file = TASKS_DIR / f"{task_id}.json"
        if task_file.exists():
            return {"status": "pending", "message": "Task queued for execution"}

        # Check if result exists (completed)
        result_file = RESULTS_DIR / f"{task_id}_result.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                result = json.load(f)
                return {
                    "status": result.get("status", "unknown"),
                    "quality_score": result.get("quality_score"),
                    "cost_usd": result.get("cost_usd"),
                    "completed_at": result.get("completed_at")
                }

        # Check if archived (processing)
        archive_file = ARCHIVE_DIR / f"{task_id}.json"
        if archive_file.exists():
            return {"status": "processing", "message": "Task is being executed"}

        return {"status": "not_found", "message": "Task ID not found"}

    async def _get_task_results(self, task_id: str) -> Dict[str, Any]:
        """
        Get results of completed task.

        Args:
            task_id: Task ID

        Returns:
            Results dictionary
        """
        result_file = RESULTS_DIR / f"{task_id}_result.json"

        if not result_file.exists():
            return {"error": "Task results not found"}

        with open(result_file, 'r') as f:
            return json.load(f)

    async def _get_events(self, max_events: int, filter_component: Optional[str]) -> List[Dict]:
        """
        Get latest events from stream.

        Args:
            max_events: Maximum events to return
            filter_component: Optional component filter

        Returns:
            List of events
        """
        if not STREAM_FILE.exists():
            return []

        events = []
        with open(STREAM_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)

                    # Apply filter
                    if filter_component and event.get("component") != filter_component:
                        continue

                    events.append(event)

        # Return most recent events
        return list(reversed(events))[:max_events]

    # ========================================================================
    # RESPONSE FORMATTERS
    # ========================================================================

    def _format_submission_response(self, task_id: str, task_data: Dict) -> str:
        """Format task submission response."""
        return f"""✅ **Task Submitted Successfully**

**Task ID:** `{task_id}`
**Workflow:** {task_data['workflow']}
**Status:** Queued for execution

**Task Description:**
{task_data['task'][:200]}...

**Next Steps:**
1. Task written to `~/dropzone/tasks/{task_id}.json`
2. Agentic Drop Zone will detect and process automatically
3. Results will appear in `~/dropzone/results/{task_id}_result.json`
4. Monitor execution with `/task/status {task_id}` or the web UI

💡 **Tip:** Use the web UI for real-time monitoring of task execution events.
"""

    def _format_status_response(self, task_id: str, status: Dict) -> str:
        """Format task status response."""
        status_emoji = {
            "pending": "⏳",
            "processing": "⚙️",
            "success": "✅",
            "failed": "❌",
            "not_found": "❓"
        }
        emoji = status_emoji.get(status["status"], "•")

        response = f"""{emoji} **Task Status: {task_id}**

**Status:** {status['status']}
**Message:** {status.get('message', 'N/A')}
"""

        if status.get("quality_score"):
            response += f"**Quality Score:** {status['quality_score']}/100\n"
        if status.get("cost_usd"):
            response += f"**Cost:** ${status['cost_usd']:.4f}\n"
        if status.get("completed_at"):
            response += f"**Completed:** {status['completed_at']}\n"

        return response

    def _format_results_response(self, task_id: str, results: Dict) -> str:
        """Format task results response."""
        if "error" in results:
            return f"❌ **Error:** {results['error']}"

        output = results.get("output", "No output")
        quality = results.get("quality_score", 0)
        cost = results.get("cost_usd", 0.0)

        return f"""✅ **Task Results: {task_id}**

**Status:** {results.get('status', 'unknown')}
**Quality Score:** {quality}/100
**Cost:** ${cost:.4f}
**Duration:** {results.get('duration_seconds', 0):.1f}s

**Generated Output:**
```
{output[:500]}...
```

**Full results available at:** `~/dropzone/results/{task_id}_result.json`
"""

    def _format_events_response(self, events: List[Dict]) -> str:
        """Format events stream response."""
        if not events:
            return "No recent events"

        response = f"📊 **Latest {len(events)} Events**\n\n"

        for event in events[:20]:  # Show top 20
            timestamp = event.get("timestamp", "")[:19]
            component = event.get("component", "unknown")
            message = event.get("message", "")

            response += f"• **[{timestamp}]** `{component}` - {message}\n"

        return response

    def _error_response(self, message: str) -> PromptMessage:
        """Create error response message."""
        return PromptMessage(
            role="assistant",
            content=TextContent(
                type="text",
                text=f"❌ **Error:** {message}"
            )
        )

    # ========================================================================
    # SERVER LIFECYCLE
    # ========================================================================

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point."""
    server = TaskAppMCPServer()
    logger.info("Starting Task App MCP Server...")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
