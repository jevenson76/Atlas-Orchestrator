"""
Base MCP Server - Abstract Foundation for All MCP Servers

Provides common functionality for creating MCP (Model Context Protocol) servers:
- Server initialization with metadata
- Tool registration with async handlers
- Resource registration with async handlers
- stdio transport support
- Error handling helpers
- Logging setup

All MCP servers should inherit from BaseMCPServer and override:
- _register_tools() - Register server-specific tools
- _register_resources() - Register server-specific resources
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional, List
from pathlib import Path

from mcp.server import Server
from mcp import Tool, Resource
from mcp.server.stdio import stdio_server

logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """
    Abstract base class for all MCP servers.

    Provides common infrastructure:
    - Server initialization
    - Tool and resource registration
    - stdio transport
    - Error handling

    Subclasses must implement:
    - _register_tools(): Register server-specific tools
    - _register_resources(): Register server-specific resources
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "MCP Server"
    ):
        """
        Initialize base MCP server.

        Args:
            name: Server name (lowercase, hyphens)
            version: Server version (semver)
            description: Human-readable description
        """
        self.name = name
        self.version = version
        self.description = description

        # Create MCP server instance
        self.server = Server(name)

        # Storage for registered tools and resources
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, Callable] = {}

        logger.info(f"Initialized {self.name} v{self.version}")

    def create_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable
    ) -> Tool:
        """
        Create and register a tool with the MCP server.

        Args:
            name: Tool name (lowercase_with_underscores)
            description: Clear description of what tool does
            input_schema: JSON schema for tool parameters
            handler: Async function to handle tool calls

        Returns:
            Tool instance
        """
        # Create tool
        tool = Tool(
            name=name,
            description=description,
            inputSchema=input_schema
        )

        # Store handler
        self.tools[name] = handler

        logger.debug(f"Registered tool: {name}")

        return tool

    def create_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str = "application/json",
        handler: Callable = None
    ) -> Resource:
        """
        Create and register a resource with the MCP server.

        Args:
            uri: Resource URI (e.g., "review://history")
            name: Human-readable name
            description: What this resource provides
            mime_type: MIME type of resource content
            handler: Async function to provide resource content

        Returns:
            Resource instance
        """
        # Create resource
        resource = Resource(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type
        )

        # Store handler if provided
        if handler:
            self.resources[uri] = handler

        logger.debug(f"Registered resource: {uri}")

        return resource

    @abstractmethod
    async def _register_tools(self):
        """
        Register server-specific tools.

        Subclasses must implement this to register their tools using
        self.create_tool().

        Example:
            self.create_tool(
                name="my_tool",
                description="Does something useful",
                input_schema={
                    "type": "object",
                    "properties": {
                        "param": {"type": "string"}
                    }
                },
                handler=self._handle_my_tool
            )
        """
        pass

    @abstractmethod
    async def _register_resources(self):
        """
        Register server-specific resources.

        Subclasses must implement this to register their resources using
        self.create_resource().

        Example:
            self.create_resource(
                uri="myserver://data",
                name="Server Data",
                description="Provides server data",
                handler=self._handle_data_resource
            )
        """
        pass

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Handle incoming tool call.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        handler = self.tools[name]

        try:
            logger.info(f"Executing tool: {name}")
            result = await handler(**arguments)
            logger.info(f"Tool {name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            raise

    async def handle_resource_read(self, uri: str) -> Dict[str, Any]:
        """
        Handle resource read request.

        Args:
            uri: Resource URI

        Returns:
            Resource content

        Raises:
            ValueError: If resource not found
            Exception: If resource read fails
        """
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")

        handler = self.resources[uri]

        try:
            logger.info(f"Reading resource: {uri}")
            content = await handler()
            logger.info(f"Resource {uri} read successfully")
            return content
        except Exception as e:
            logger.error(f"Resource {uri} read failed: {e}", exc_info=True)
            raise

    def format_error(self, error: Exception) -> Dict[str, Any]:
        """
        Format error for MCP response.

        Args:
            error: Exception to format

        Returns:
            Error dictionary with message and type
        """
        return {
            "error": {
                "type": type(error).__name__,
                "message": str(error)
            }
        }

    def format_success(self, data: Any, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Format success response for MCP.

        Args:
            data: Result data
            message: Optional success message

        Returns:
            Success dictionary
        """
        response = {
            "success": True,
            "data": data
        }

        if message:
            response["message"] = message

        return response

    async def initialize(self):
        """
        Initialize the server.

        Registers all tools and resources.
        Called before server starts.
        """
        logger.info(f"Initializing {self.name}...")

        # Register tools
        await self._register_tools()
        logger.info(f"Registered {len(self.tools)} tools")

        # Register resources
        await self._register_resources()
        logger.info(f"Registered {len(self.resources)} resources")

        logger.info(f"{self.name} initialization complete")

    async def run(self):
        """
        Run the MCP server using stdio transport.

        This is the main entry point for starting the server.
        Uses stdio (standard input/output) for communication, which is
        the standard transport for MCP servers.
        """
        logger.info(f"Starting {self.name} v{self.version}")

        # Initialize server
        await self.initialize()

        # Set up MCP handlers
        @self.server.list_tools()
        async def list_tools():
            """List all available tools."""
            return [
                Tool(
                    name=name,
                    description=handler.__doc__ or f"Tool: {name}",
                    inputSchema={"type": "object"}  # Simplified for now
                )
                for name, handler in self.tools.items()
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Handle tool call."""
            try:
                result = await self.handle_tool_call(name, arguments)
                return [{"type": "text", "text": str(result)}]
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return [{"type": "text", "text": f"Error: {str(e)}"}]

        @self.server.list_resources()
        async def list_resources():
            """List all available resources."""
            return [
                Resource(
                    uri=uri,
                    name=uri.split("://")[1] if "://" in uri else uri,
                    description=f"Resource: {uri}"
                )
                for uri in self.resources.keys()
            ]

        @self.server.read_resource()
        async def read_resource(uri: str):
            """Handle resource read."""
            try:
                content = await self.handle_resource_read(uri)
                return [{"uri": uri, "mimeType": "application/json", "text": str(content)}]
            except Exception as e:
                logger.error(f"Resource read failed: {e}")
                raise

        # Run server with stdio transport
        logger.info(f"{self.name} ready, starting stdio server...")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


class ToolParameter:
    """
    Helper class for defining tool parameters with JSON schema.

    Simplifies creation of parameter schemas.
    """

    @staticmethod
    def string(
        description: str,
        required: bool = False,
        default: Optional[str] = None,
        enum: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create string parameter schema."""
        schema = {
            "type": "string",
            "description": description
        }

        if default is not None:
            schema["default"] = default

        if enum is not None:
            schema["enum"] = enum

        return schema

    @staticmethod
    def integer(
        description: str,
        required: bool = False,
        default: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create integer parameter schema."""
        schema = {
            "type": "integer",
            "description": description
        }

        if default is not None:
            schema["default"] = default

        if minimum is not None:
            schema["minimum"] = minimum

        if maximum is not None:
            schema["maximum"] = maximum

        return schema

    @staticmethod
    def boolean(
        description: str,
        required: bool = False,
        default: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Create boolean parameter schema."""
        schema = {
            "type": "boolean",
            "description": description
        }

        if default is not None:
            schema["default"] = default

        return schema

    @staticmethod
    def object(
        description: str,
        properties: Dict[str, Any],
        required: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create object parameter schema."""
        schema = {
            "type": "object",
            "description": description,
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema

    @staticmethod
    def array(
        description: str,
        items: Dict[str, Any],
        min_items: Optional[int] = None,
        max_items: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create array parameter schema."""
        schema = {
            "type": "array",
            "description": description,
            "items": items
        }

        if min_items is not None:
            schema["minItems"] = min_items

        if max_items is not None:
            schema["maxItems"] = max_items

        return schema


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


if __name__ == "__main__":
    # Example usage - cannot run directly as it's abstract
    print("BaseMCPServer is an abstract base class.")
    print("Create a subclass that implements:")
    print("  - async def _register_tools(self)")
    print("  - async def _register_resources(self)")
    print("\nThen run: await server.run()")
