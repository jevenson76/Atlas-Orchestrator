"""
MCP Server Tests - Comprehensive Test Suite

Tests all MCP servers and components:
- Base server functionality
- Code review server (4 tools, 2 resources)
- Workflow orchestration server (5 tools, 2 resources)
- Validation server (3 tools, 1 resource)
- Agent registry server (4 tools, 2 resources)
- Server manager
- Error handling

Total: 25+ tests
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_servers.base_server import BaseMCPServer, ToolParameter
from mcp_servers.server_manager import ServerManager, ServerStatus, register_all_servers


# ==================== FIXTURES ====================

@pytest.fixture
def mock_code_review_server():
    """Mock code review server for testing."""
    from mcp_servers.code_review_server import CodeReviewServer

    with patch('mcp_servers.code_review_server.SpecializedRolesOrchestrator'):
        with patch('mcp_servers.code_review_server.ValidationOrchestrator'):
            server = CodeReviewServer(project_root=Path("/tmp"))
            return server


@pytest.fixture
def mock_workflow_server():
    """Mock workflow orchestration server for testing."""
    from mcp_servers.workflow_orchestration_server import WorkflowOrchestrationServer

    with patch('mcp_servers.workflow_orchestration_server.MasterOrchestrator'):
        with patch('mcp_servers.workflow_orchestration_server.ParallelDevelopmentOrchestrator'):
            with patch('mcp_servers.workflow_orchestration_server.ProgressiveEnhancementOrchestrator'):
                with patch('mcp_servers.workflow_orchestration_server.SpecializedRolesOrchestrator'):
                    server = WorkflowOrchestrationServer()
                    return server


@pytest.fixture
def mock_validation_server():
    """Mock validation server for testing."""
    from mcp_servers.validation_server import ValidationServer

    with patch('mcp_servers.validation_server.ValidationOrchestrator'):
        server = ValidationServer(project_root=Path("/tmp"))
        return server


@pytest.fixture
def mock_agent_registry_server():
    """Mock agent registry server for testing."""
    from mcp_servers.agent_registry_server import AgentRegistryServer

    with patch('mcp_servers.agent_registry_server.get_global_registry'):
        with patch('mcp_servers.agent_registry_server.AgentDiscovery'):
            with patch('mcp_servers.agent_registry_server.AgentAnalytics'):
                server = AgentRegistryServer()
                return server


@pytest.fixture
def server_manager():
    """Create server manager for testing."""
    return ServerManager()


# ==================== BASE SERVER TESTS ====================

def test_base_server_initialization():
    """Test 1: Base server can be initialized with metadata."""

    class TestServer(BaseMCPServer):
        async def _register_tools(self):
            pass

        async def _register_resources(self):
            pass

    server = TestServer(name="test-server", version="1.0.0", description="Test")

    assert server.name == "test-server"
    assert server.version == "1.0.0"
    assert server.description == "Test"
    assert server.server is not None
    assert isinstance(server.tools, dict)
    assert isinstance(server.resources, dict)


def test_base_server_tool_creation():
    """Test 2: Base server can create and register tools."""

    class TestServer(BaseMCPServer):
        async def _register_tools(self):
            pass

        async def _register_resources(self):
            pass

    server = TestServer(name="test-server")

    async def test_handler(message: str):
        return f"Handled: {message}"

    tool = server.create_tool(
        name="test_tool",
        description="A test tool",
        input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
        handler=test_handler
    )

    assert tool.name == "test_tool"
    assert "test_tool" in server.tools
    assert server.tools["test_tool"] == test_handler


def test_base_server_resource_creation():
    """Test 3: Base server can create and register resources."""

    class TestServer(BaseMCPServer):
        async def _register_tools(self):
            pass

        async def _register_resources(self):
            pass

    server = TestServer(name="test-server")

    async def test_handler():
        return {"data": "test"}

    resource = server.create_resource(
        uri="test://resource",
        name="Test Resource",
        description="A test resource",
        handler=test_handler
    )

    assert str(resource.uri) == "test://resource"
    assert "test://resource" in server.resources
    assert server.resources["test://resource"] == test_handler


# ==================== CODE REVIEW SERVER TESTS ====================

def test_code_review_server_initialization(mock_code_review_server):
    """Test 4: Code review server initializes correctly."""
    assert mock_code_review_server.name == "code-review"
    assert mock_code_review_server.version == "1.0.0"
    assert mock_code_review_server.project_root is not None


@pytest.mark.asyncio
async def test_code_review_server_tool_registration(mock_code_review_server):
    """Test 5: Code review server registers all tools."""
    await mock_code_review_server._register_tools()

    # Should have 4 tools
    assert len(mock_code_review_server.tools) == 4
    assert "review_code" in mock_code_review_server.tools
    assert "quick_review" in mock_code_review_server.tools
    assert "validate_code" in mock_code_review_server.tools
    assert "get_recommendations" in mock_code_review_server.tools


@pytest.mark.asyncio
async def test_code_review_server_resource_registration(mock_code_review_server):
    """Test 6: Code review server registers all resources."""
    await mock_code_review_server._register_resources()

    # Should have 2 resources
    assert len(mock_code_review_server.resources) == 2
    assert "review://history" in mock_code_review_server.resources
    assert "review://stats" in mock_code_review_server.resources


@pytest.mark.asyncio
async def test_code_review_quick_review_mock(mock_code_review_server):
    """Test 7: Code review quick_review tool (mocked)."""
    # Register tools first
    await mock_code_review_server._register_tools()

    # Mock the validator
    mock_code_review_server.validation_orchestrator.validate_code = AsyncMock(
        return_value={
            "code": {"score": 85, "passed": True, "findings": []},
            "documentation": {"score": 80, "passed": True, "findings": []},
            "tests": {"score": 90, "passed": True, "findings": []}
        }
    )

    # Call quick_review
    result = await mock_code_review_server._handle_quick_review(
        code="def hello(): return 'world'",
        language="python"
    )

    assert result["success"] is True
    assert "data" in result
    assert result["data"]["quality_score"] == 85


# ==================== WORKFLOW ORCHESTRATION SERVER TESTS ====================

def test_workflow_server_initialization(mock_workflow_server):
    """Test 8: Workflow orchestration server initializes correctly."""
    assert mock_workflow_server.name == "workflow-orchestration"
    assert mock_workflow_server.version == "1.0.0"


@pytest.mark.asyncio
async def test_workflow_server_tool_registration(mock_workflow_server):
    """Test 9: Workflow server registers all tools."""
    await mock_workflow_server._register_tools()

    # Should have 5 tools
    assert len(mock_workflow_server.tools) == 5
    assert "execute_workflow" in mock_workflow_server.tools
    assert "parallel_workflow" in mock_workflow_server.tools
    assert "progressive_workflow" in mock_workflow_server.tools
    assert "specialized_workflow" in mock_workflow_server.tools
    assert "get_workflow_recommendation" in mock_workflow_server.tools


@pytest.mark.asyncio
async def test_workflow_server_resource_registration(mock_workflow_server):
    """Test 10: Workflow server registers all resources."""
    await mock_workflow_server._register_resources()

    # Should have 2 resources
    assert len(mock_workflow_server.resources) == 2
    assert "workflows://available" in mock_workflow_server.resources
    assert "workflows://metrics" in mock_workflow_server.resources


@pytest.mark.asyncio
async def test_workflow_recommendation_handler(mock_workflow_server):
    """Test 11: Workflow recommendation handler works."""
    await mock_workflow_server._register_tools()

    result = await mock_workflow_server._handle_get_workflow_recommendation(
        task="Build a simple user authentication system",
        constraints=None
    )

    assert result["success"] is True
    assert "data" in result
    assert "recommendation" in result["data"]
    assert "workflow" in result["data"]["recommendation"]


@pytest.mark.asyncio
async def test_workflow_available_resources(mock_workflow_server):
    """Test 12: Workflow available resources handler works."""
    await mock_workflow_server._register_resources()

    result = await mock_workflow_server._handle_available_workflows()

    assert "workflows" in result
    assert len(result["workflows"]) == 4
    assert result["total_workflows"] == 4


# ==================== VALIDATION SERVER TESTS ====================

def test_validation_server_initialization(mock_validation_server):
    """Test 13: Validation server initializes correctly."""
    assert mock_validation_server.name == "validation"
    assert mock_validation_server.version == "1.0.0"
    assert mock_validation_server.thresholds is not None


@pytest.mark.asyncio
async def test_validation_server_tool_registration(mock_validation_server):
    """Test 14: Validation server registers all tools."""
    await mock_validation_server._register_tools()

    # Should have 3 tools
    assert len(mock_validation_server.tools) == 3
    assert "validate_code" in mock_validation_server.tools
    assert "validate_documentation" in mock_validation_server.tools
    assert "validate_tests" in mock_validation_server.tools


@pytest.mark.asyncio
async def test_validation_server_resource_registration(mock_validation_server):
    """Test 15: Validation server registers resource."""
    await mock_validation_server._register_resources()

    # Should have 1 resource
    assert len(mock_validation_server.resources) == 1
    assert "validation://thresholds" in mock_validation_server.resources


@pytest.mark.asyncio
async def test_validation_thresholds_resource(mock_validation_server):
    """Test 16: Validation thresholds resource returns correct data."""
    await mock_validation_server._register_resources()

    result = await mock_validation_server._handle_thresholds()

    assert "thresholds" in result
    assert "code" in result["thresholds"]
    assert "documentation" in result["thresholds"]
    assert "tests" in result["thresholds"]


# ==================== AGENT REGISTRY SERVER TESTS ====================

def test_agent_registry_server_initialization(mock_agent_registry_server):
    """Test 17: Agent registry server initializes correctly."""
    assert mock_agent_registry_server.name == "agent-registry"
    assert mock_agent_registry_server.version == "1.0.0"


@pytest.mark.asyncio
async def test_agent_registry_server_tool_registration(mock_agent_registry_server):
    """Test 18: Agent registry server registers all tools."""
    await mock_agent_registry_server._register_tools()

    # Should have 4 tools
    assert len(mock_agent_registry_server.tools) == 4
    assert "list_agents" in mock_agent_registry_server.tools
    assert "discover_agent" in mock_agent_registry_server.tools
    assert "get_agent_stats" in mock_agent_registry_server.tools
    assert "get_cost_analysis" in mock_agent_registry_server.tools


@pytest.mark.asyncio
async def test_agent_registry_server_resource_registration(mock_agent_registry_server):
    """Test 19: Agent registry server registers all resources."""
    await mock_agent_registry_server._register_resources()

    # Should have 2 resources
    assert len(mock_agent_registry_server.resources) == 2
    assert "agents://directory" in mock_agent_registry_server.resources
    assert "agents://analytics" in mock_agent_registry_server.resources


@pytest.mark.asyncio
async def test_agent_registry_list_agents_handler(mock_agent_registry_server):
    """Test 20: Agent registry list_agents handler works."""
    await mock_agent_registry_server._register_tools()

    # Mock the discovery
    mock_agent_registry_server.discovery.find_agents = Mock(return_value=[])

    result = await mock_agent_registry_server._handle_list_agents(
        category="all",
        model_tier="all"
    )

    assert result["success"] is True
    assert "data" in result
    assert "agents" in result["data"]


# ==================== SERVER MANAGER TESTS ====================

def test_server_manager_initialization(server_manager):
    """Test 21: Server manager initializes correctly."""
    assert server_manager.servers == {}
    assert server_manager.config == {}
    assert server_manager.config_path.name == "config.json"


def test_server_manager_register_server(server_manager, mock_code_review_server):
    """Test 22: Server manager can register servers."""
    info = server_manager.register_server(
        name="test-server",
        server_instance=mock_code_review_server
    )

    assert info.name == "test-server"
    assert info.status == ServerStatus.REGISTERED
    assert "test-server" in server_manager.servers


def test_server_manager_list_servers(server_manager, mock_code_review_server):
    """Test 23: Server manager can list servers."""
    server_manager.register_server("test-server-1", mock_code_review_server)
    server_manager.register_server("test-server-2", mock_code_review_server)

    servers = server_manager.list_servers()

    assert len(servers) == 2
    assert any(s.name == "test-server-1" for s in servers)
    assert any(s.name == "test-server-2" for s in servers)


def test_server_manager_get_summary(server_manager, mock_code_review_server):
    """Test 24: Server manager provides summary."""
    server_manager.register_server("test-server", mock_code_review_server)

    summary = server_manager.get_server_summary()

    assert summary["total_servers"] == 1
    assert "test-server" in summary["servers"]


# ==================== ERROR HANDLING TESTS ====================

def test_server_manager_duplicate_registration(server_manager, mock_code_review_server):
    """Test 25: Server manager rejects duplicate registration."""
    server_manager.register_server("test-server", mock_code_review_server)

    with pytest.raises(ValueError, match="already registered"):
        server_manager.register_server("test-server", mock_code_review_server)


@pytest.mark.asyncio
async def test_tool_parameter_helpers():
    """Test 26: ToolParameter helpers create correct schemas."""
    # String parameter
    string_param = ToolParameter.string("A string parameter", default="test")
    assert string_param["type"] == "string"
    assert string_param["default"] == "test"

    # Integer parameter
    int_param = ToolParameter.integer("An integer parameter", minimum=0, maximum=100)
    assert int_param["type"] == "integer"
    assert int_param["minimum"] == 0
    assert int_param["maximum"] == 100

    # Boolean parameter
    bool_param = ToolParameter.boolean("A boolean parameter", default=True)
    assert bool_param["type"] == "boolean"
    assert bool_param["default"] is True

    # Object parameter
    obj_param = ToolParameter.object(
        "An object parameter",
        properties={"key": {"type": "string"}},
        required=["key"]
    )
    assert obj_param["type"] == "object"
    assert "key" in obj_param["properties"]
    assert obj_param["required"] == ["key"]

    # Array parameter
    array_param = ToolParameter.array(
        "An array parameter",
        items={"type": "string"},
        min_items=1
    )
    assert array_param["type"] == "array"
    assert array_param["minItems"] == 1


def test_server_manager_validation(server_manager, mock_code_review_server):
    """Test 27: Server manager can validate server configuration."""
    server_manager.register_server("test-server", mock_code_review_server)

    # Without configuration
    result = server_manager.validate_server("test-server")
    assert "valid" in result
    assert "issues" in result
    # Should have issue about missing configuration
    assert any("configuration" in issue.lower() for issue in result["issues"])


@pytest.mark.asyncio
async def test_code_review_helper_methods(mock_code_review_server):
    """Test 28: Code review server helper methods work correctly."""
    # Test quality score calculation
    validation_result = {
        "code": {"score": 85},
        "documentation": {"score": 80},
        "tests": {"score": 90}
    }

    score = mock_code_review_server._calculate_quality_score(validation_result)
    assert score == 85  # Average

    # Test categorize_finding
    assert mock_code_review_server._categorize_finding("This is an error") == "errors"
    assert mock_code_review_server._categorize_finding("Security vulnerability") == "security"
    assert mock_code_review_server._categorize_finding("Performance issue") == "performance"
    assert mock_code_review_server._categorize_finding("Test coverage") == "testing"


# ==================== INTEGRATION TESTS ====================

def test_config_file_structure():
    """Test 29: Configuration file has correct structure."""
    config_path = Path.home() / ".claude" / "mcp_servers" / "config.json"

    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert "code-review" in config["mcpServers"]
        assert "workflow-orchestration" in config["mcpServers"]
        assert "validation" in config["mcpServers"]
        assert "agent-registry" in config["mcpServers"]

        # Check structure of each server
        for server_name, server_config in config["mcpServers"].items():
            assert "command" in server_config
            assert "args" in server_config
            assert server_config["command"] == "python3"
            assert len(server_config["args"]) > 0


def test_server_scripts_exist():
    """Test 30: All server scripts exist at expected paths."""
    lib_path = Path.home() / ".claude" / "lib" / "mcp_servers"

    assert (lib_path / "base_server.py").exists()
    assert (lib_path / "code_review_server.py").exists()
    assert (lib_path / "workflow_orchestration_server.py").exists()
    assert (lib_path / "validation_server.py").exists()
    assert (lib_path / "agent_registry_server.py").exists()
    assert (lib_path / "server_manager.py").exists()


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
