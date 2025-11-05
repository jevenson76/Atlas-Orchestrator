"""
MCP Server Manager - Coordinate Multiple MCP Servers

Manages registration, configuration, and lifecycle of MCP servers:
- Register server instances
- List available servers with status
- Load configuration
- Provide server information

Note: For production use with multiple servers running simultaneously,
use process-based orchestration (e.g., supervisord, systemd).
This manager is primarily for configuration and information purposes.

Usage:
    from server_manager import ServerManager

    manager = ServerManager()
    manager.register_server("code-review", CodeReviewServer())
    manager.list_servers()
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServerStatus(str, Enum):
    """Server status states."""
    REGISTERED = "registered"
    CONFIGURED = "configured"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServerInfo:
    """Information about a registered server."""
    name: str
    server_instance: Any
    description: str
    version: str
    tools_count: int
    resources_count: int
    status: ServerStatus
    config: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ServerManager:
    """
    Manager for coordinating multiple MCP servers.

    Provides:
    - Server registration
    - Configuration management
    - Server information and status
    - Batch operations
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize server manager.

        Args:
            config_path: Path to configuration file (default: ~/.claude/mcp_servers/config.json)
        """
        self.config_path = config_path or Path.home() / ".claude" / "mcp_servers" / "config.json"

        # Registry of servers
        self.servers: Dict[str, ServerInfo] = {}

        # Configuration
        self.config: Dict[str, Any] = {}

        logger.info("Initialized ServerManager")

    def register_server(
        self,
        name: str,
        server_instance: Any,
        config: Optional[Dict[str, Any]] = None
    ) -> ServerInfo:
        """
        Register a server instance.

        Args:
            name: Server name (must be unique)
            server_instance: Server instance (subclass of BaseMCPServer)
            config: Optional server-specific configuration

        Returns:
            ServerInfo with registration details

        Raises:
            ValueError: If server name already registered
        """
        if name in self.servers:
            raise ValueError(f"Server already registered: {name}")

        # Create server info
        info = ServerInfo(
            name=name,
            server_instance=server_instance,
            description=getattr(server_instance, "description", "No description"),
            version=getattr(server_instance, "version", "unknown"),
            tools_count=len(getattr(server_instance, "tools", {})),
            resources_count=len(getattr(server_instance, "resources", {})),
            status=ServerStatus.REGISTERED,
            config=config
        )

        self.servers[name] = info

        logger.info(f"Registered server: {name} ({info.tools_count} tools, {info.resources_count} resources)")

        return info

    def unregister_server(self, name: str) -> bool:
        """
        Unregister a server.

        Args:
            name: Server name

        Returns:
            True if unregistered, False if not found
        """
        if name in self.servers:
            del self.servers[name]
            logger.info(f"Unregistered server: {name}")
            return True

        return False

    def get_server(self, name: str) -> Optional[ServerInfo]:
        """
        Get server information.

        Args:
            name: Server name

        Returns:
            ServerInfo if found, None otherwise
        """
        return self.servers.get(name)

    def list_servers(self, status_filter: Optional[ServerStatus] = None) -> List[ServerInfo]:
        """
        List all registered servers.

        Args:
            status_filter: Optional filter by status

        Returns:
            List of ServerInfo
        """
        servers = list(self.servers.values())

        if status_filter:
            servers = [s for s in servers if s.status == status_filter]

        return servers

    def get_server_summary(self) -> Dict[str, Any]:
        """
        Get summary of all servers.

        Returns:
            Dictionary with server statistics
        """
        total = len(self.servers)
        by_status = {}

        for status in ServerStatus:
            count = len([s for s in self.servers.values() if s.status == status])
            if count > 0:
                by_status[status.value] = count

        total_tools = sum(s.tools_count for s in self.servers.values())
        total_resources = sum(s.resources_count for s in self.servers.values())

        return {
            "total_servers": total,
            "by_status": by_status,
            "total_tools": total_tools,
            "total_resources": total_resources,
            "servers": {
                name: {
                    "description": info.description,
                    "version": info.version,
                    "tools": info.tools_count,
                    "resources": info.resources_count,
                    "status": info.status.value
                }
                for name, info in self.servers.items()
            }
        }

    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_path: Path to config file (default: use manager's config_path)

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file not found
        """
        import json

        path = config_path or self.config_path

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, 'r') as f:
            self.config = json.load(f)

        logger.info(f"Loaded configuration from {path}")

        return self.config

    def save_config(self, config: Dict[str, Any], config_path: Optional[Path] = None):
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary
            config_path: Path to save config (default: use manager's config_path)
        """
        import json

        path = config_path or self.config_path

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(config, f, indent=2)

        self.config = config

        logger.info(f"Saved configuration to {path}")

    def get_config_for_claude_desktop(self) -> Dict[str, Any]:
        """
        Get configuration formatted for Claude Desktop.

        Returns:
            Configuration dictionary in Claude Desktop format
        """
        return self.config.get("mcpServers", {})

    def validate_server(self, name: str) -> Dict[str, Any]:
        """
        Validate server configuration and state.

        Args:
            name: Server name

        Returns:
            Validation results with any issues
        """
        issues = []

        server = self.servers.get(name)

        if not server:
            return {
                "valid": False,
                "issues": [f"Server not found: {name}"]
            }

        # Check server instance
        if not server.server_instance:
            issues.append("No server instance")

        # Check tools
        if server.tools_count == 0:
            issues.append("No tools registered")

        # Check configuration
        if name in self.config.get("mcpServers", {}):
            server_config = self.config["mcpServers"][name]

            # Check command
            if "command" not in server_config:
                issues.append("Missing 'command' in configuration")

            # Check args
            if "args" not in server_config:
                issues.append("Missing 'args' in configuration")
            else:
                # Check if script path exists
                if server_config["args"]:
                    script_path = Path(server_config["args"][0])
                    if not script_path.exists():
                        issues.append(f"Script not found: {script_path}")
        else:
            issues.append(f"No configuration found for {name}")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def validate_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all registered servers.

        Returns:
            Dictionary mapping server names to validation results
        """
        results = {}

        for name in self.servers.keys():
            results[name] = self.validate_server(name)

        return results

    def print_summary(self):
        """Print summary of all servers to console."""
        summary = self.get_server_summary()

        print("=" * 70)
        print("MCP SERVER MANAGER SUMMARY")
        print("=" * 70)
        print(f"\nTotal Servers: {summary['total_servers']}")
        print(f"Total Tools: {summary['total_tools']}")
        print(f"Total Resources: {summary['total_resources']}")

        print("\nBy Status:")
        for status, count in summary['by_status'].items():
            print(f"  {status}: {count}")

        print("\nServers:")
        for name, info in summary['servers'].items():
            print(f"\n  {name} (v{info['version']}) - {info['status']}")
            print(f"    Description: {info['description']}")
            print(f"    Tools: {info['tools']}, Resources: {info['resources']}")

        print("\n" + "=" * 70)


# ==================== CONVENIENCE FUNCTIONS ====================

def create_manager() -> ServerManager:
    """
    Create a server manager instance.

    Returns:
        ServerManager instance
    """
    return ServerManager()


def register_all_servers(manager: ServerManager) -> Dict[str, ServerInfo]:
    """
    Register all available MCP servers.

    Args:
        manager: ServerManager instance

    Returns:
        Dictionary mapping server names to ServerInfo
    """
    import sys
    from pathlib import Path

    # Add lib directory to path
    lib_path = Path(__file__).parent.parent
    sys.path.insert(0, str(lib_path))

    registered = {}

    # Import and register code review server
    try:
        from mcp_servers.code_review_server import CodeReviewServer
        info = manager.register_server("code-review", CodeReviewServer())
        registered["code-review"] = info
        logger.info("Registered code-review server")
    except Exception as e:
        logger.error(f"Failed to register code-review server: {e}")

    # Import and register workflow orchestration server
    try:
        from mcp_servers.workflow_orchestration_server import WorkflowOrchestrationServer
        info = manager.register_server("workflow-orchestration", WorkflowOrchestrationServer())
        registered["workflow-orchestration"] = info
        logger.info("Registered workflow-orchestration server")
    except Exception as e:
        logger.error(f"Failed to register workflow-orchestration server: {e}")

    # Import and register validation server
    try:
        from mcp_servers.validation_server import ValidationServer
        info = manager.register_server("validation", ValidationServer())
        registered["validation"] = info
        logger.info("Registered validation server")
    except Exception as e:
        logger.error(f"Failed to register validation server: {e}")

    # Import and register agent registry server
    try:
        from mcp_servers.agent_registry_server import AgentRegistryServer
        info = manager.register_server("agent-registry", AgentRegistryServer())
        registered["agent-registry"] = info
        logger.info("Registered agent-registry server")
    except Exception as e:
        logger.error(f"Failed to register agent-registry server: {e}")

    return registered


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("\n" + "=" * 70)
    print("MCP SERVER MANAGER DEMO")
    print("=" * 70)

    # Create manager
    manager = create_manager()

    # Register all servers
    print("\nRegistering servers...")
    registered = register_all_servers(manager)

    print(f"\n✅ Registered {len(registered)} servers")

    # Print summary
    manager.print_summary()

    # Validate servers
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    validation_results = manager.validate_all_servers()

    for name, result in validation_results.items():
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"\n{name}: {status}")

        if result["issues"]:
            print("  Issues:")
            for issue in result["issues"]:
                print(f"    - {issue}")

    print("\n" + "=" * 70)
