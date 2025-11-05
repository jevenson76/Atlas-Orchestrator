# MCP Server Wrappers - Complete Documentation

**Version:** 1.0.0
**Component:** Priority 4 Component C2
**Status:** Production Ready
**Last Updated:** November 3, 2025

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Available Servers](#available-servers)
4. [Tool Schemas](#tool-schemas)
5. [Setup Guide](#setup-guide)
6. [Usage Examples](#usage-examples)
7. [Development Guide](#development-guide)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [API Reference](#api-reference)

---

## Overview

### What Are MCP Servers?

MCP (Model Context Protocol) servers expose complex AI workflows through simple, standardized tool calls. Instead of manually coordinating multiple agents and workflows, users can simply call a tool like `review_code` and get comprehensive analysis instantly.

### Value Proposition

**Before MCP Servers:**
```python
# Complex orchestration
orchestrator = SpecializedRolesOrchestrator()
validator = ValidationOrchestrator()
result1 = await orchestrator.execute_workflow(task)
result2 = await validator.validate_code(code)
# ... merge results, calculate quality, format output ...
```

**With MCP Servers:**
```
User: "review_code" tool with code parameter
→ Complete 4-phase review + validation + recommendations
```

### Key Benefits

1. **Abstraction**: Hide workflow complexity behind simple interfaces
2. **Standardization**: MCP protocol works with Claude Desktop and other clients
3. **Discovery**: Tools advertise their capabilities automatically
4. **Error Handling**: Graceful error messages in standardized format
5. **Integration**: Easy to integrate with external tools and IDEs

### Components

```
Priority 4 Component C2: MCP Server Wrappers
├── Base Server (BaseMCPServer)
├── 4 Specialized Servers
│   ├── Code Review Server (4 tools, 2 resources)
│   ├── Workflow Orchestration Server (5 tools, 2 resources)
│   ├── Validation Server (3 tools, 1 resource)
│   └── Agent Registry Server (4 tools, 2 resources)
├── Server Manager (coordination)
├── Configuration (config.json)
├── Tests (30 tests, all passing)
└── Setup Script (setup_mcp_servers.py)
```

**Total**: 16 tools, 7 resources

---

## Architecture

### MCP Protocol Overview

```
┌─────────────────┐
│  Claude Desktop │
│  or MCP Client  │
└────────┬────────┘
         │ MCP Protocol (stdio)
         ▼
┌─────────────────────────┐
│   MCP Server            │
│   - Tools (16 total)    │
│   - Resources (7 total) │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Complex Workflows     │
│   - Orchestrators       │
│   - Validators          │
│   - Agent Registry      │
└─────────────────────────┘
```

### Server Hierarchy

```
BaseMCPServer (Abstract)
├── Tool registration helpers
├── Resource registration helpers
├── Error handling
├── stdio transport
└── Async handlers

↓ Inherited by ↓

CodeReviewServer
WorkflowOrchestrationServer
ValidationServer
AgentRegistryServer
```

### Communication Flow

1. **Tool Discovery**: Client requests list of available tools
2. **Tool Invocation**: Client calls tool with parameters
3. **Execution**: Server executes complex workflow
4. **Response**: Server returns formatted result
5. **Resource Access**: Client can access resources for additional context

---

## Available Servers

### 1. Code Review Server

**Purpose**: Complete code review with multi-phase analysis and validation

**Tools** (4):
- `review_code`: Complete 4-phase review (architect → developer → tester → reviewer) + validation
- `quick_review`: Fast validation-only review (10-30 seconds)
- `validate_code`: Targeted validation by type
- `get_recommendations`: Actionable improvement suggestions

**Resources** (2):
- `review://history`: Past code reviews
- `review://stats`: Review statistics and trends

**Time**: 5-8 minutes (complete review), 10-30 seconds (quick review)

**Use Cases**:
- Pre-commit code review
- Pull request review
- Code quality assessment
- Security analysis
- Performance review

### 2. Workflow Orchestration Server

**Purpose**: Multi-agent workflow execution with intelligent routing

**Tools** (5):
- `execute_workflow`: Auto-route to optimal workflow
- `parallel_workflow`: Explicit parallel execution (30-70% faster)
- `progressive_workflow`: Start cheap, escalate if needed
- `specialized_workflow`: 4-phase specialized roles
- `get_workflow_recommendation`: Which workflow to use

**Resources** (2):
- `workflows://available`: Catalog of workflows
- `workflows://metrics`: Performance metrics per workflow

**Time**: Varies by workflow (2-10 minutes)

**Use Cases**:
- Complex feature implementation
- Multi-component development
- Quality-critical tasks
- Time-sensitive projects
- Cost-sensitive projects

### 3. Validation Server

**Purpose**: Code quality validation (structure, docs, tests)

**Tools** (3):
- `validate_code`: Structural validation and best practices
- `validate_documentation`: Documentation quality checks
- `validate_tests`: Test coverage and quality

**Resources** (1):
- `validation://thresholds`: Quality standards

**Time**: 10-30 seconds per validation

**Use Cases**:
- Pre-commit validation
- CI/CD quality gates
- Documentation audits
- Test coverage checks
- Code style enforcement

### 4. Agent Registry Server

**Purpose**: Agent discovery and cost analytics

**Tools** (4):
- `list_agents`: List registered agents with filters
- `discover_agent`: Find optimal agent for task
- `get_agent_stats`: Usage statistics
- `get_cost_analysis`: Cost breakdown and optimization

**Resources** (2):
- `agents://directory`: Complete agent catalog
- `agents://analytics`: Usage analytics

**Time**: < 1 second

**Use Cases**:
- Agent discovery
- Cost monitoring
- Performance analysis
- Optimization opportunities
- Agent selection

---

## Tool Schemas

### Code Review Server Tools

#### `review_code`

**Description**: Complete multi-phase code review with quality validation

**Parameters**:
```json
{
  "code": "string (required) - Source code to review",
  "language": "string (required) - Programming language",
  "context": "object (optional) - Additional context",
  "quality_threshold": "integer (optional, default: 90) - Min quality score (0-100)"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "quality_score": 92,
    "passed": true,
    "execution_time": 360.5,
    "total_cost": 0.045,
    "phases": {
      "architect": "...",
      "developer": "...",
      "tester": "...",
      "reviewer": "..."
    },
    "validation": {
      "code": {"score": 90, "passed": true},
      "documentation": {"score": 85, "passed": true},
      "tests": {"score": 95, "passed": true}
    },
    "findings": [...],
    "recommendations": [...]
  }
}
```

#### `quick_review`

**Description**: Fast validation-only review

**Parameters**:
```json
{
  "code": "string (required)",
  "language": "string (required)"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "quality_score": 88,
    "validation": {...},
    "findings": [...],
    "findings_count": 5
  }
}
```

#### `validate_code`

**Description**: Targeted validation by type

**Parameters**:
```json
{
  "code": "string (required)",
  "language": "string (required)",
  "validation_type": "string (optional, default: 'all') - code|documentation|tests|all"
}
```

#### `get_recommendations`

**Description**: Generate actionable recommendations

**Parameters**:
```json
{
  "code": "string (required)",
  "language": "string (required)",
  "focus_area": "string (optional, default: 'all') - security|performance|maintainability|testing|all"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "focus_area": "all",
    "recommendations": [
      {
        "title": "Address security issues",
        "priority": "high",
        "issue_count": 3,
        "description": "...",
        "action": "...",
        "examples": [...]
      }
    ],
    "recommendation_count": 5,
    "priority_breakdown": {
      "high": 2,
      "medium": 2,
      "low": 1
    }
  }
}
```

### Workflow Orchestration Server Tools

#### `execute_workflow`

**Description**: Execute task using optimal workflow (auto-routing)

**Parameters**:
```json
{
  "task": "string (required) - Task to execute",
  "workflow": "string (optional, default: 'auto') - auto|parallel|progressive|specialized",
  "context": "object (optional)"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "workflow_used": "progressive",
    "execution_time": 45.2,
    "result": {
      "output": "...",
      "quality_score": 88,
      "cost": 0.012
    }
  }
}
```

#### `parallel_workflow`

**Description**: Execute multi-component task in parallel

**Parameters**:
```json
{
  "task": "string (required)",
  "components": "array (required, min 2) - List of components",
  "context": "object (optional)"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "workflow": "parallel",
    "execution_time": 120.5,
    "components_count": 3,
    "time_savings": {
      "estimated_sequential": 320.0,
      "actual_parallel": 120.5,
      "savings_percent": 62.3
    }
  }
}
```

#### `get_workflow_recommendation`

**Description**: Recommend optimal workflow for task

**Parameters**:
```json
{
  "task": "string (required)",
  "constraints": "object (optional) - max_time, max_cost, min_quality"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "task_analysis": {
      "complexity": "moderate",
      "component_count": 2,
      "requires_architecture": false
    },
    "recommendation": {
      "workflow": "parallel",
      "confidence": "high",
      "expected_time": "Fast (parallel execution)",
      "expected_cost": "Moderate",
      "expected_quality": "Good"
    },
    "reasoning": "Task has 2 components that can be developed in parallel",
    "alternatives": [...]
  }
}
```

### Validation Server Tools

#### `validate_code`

**Description**: Validate code structural quality

**Parameters**:
```json
{
  "code": "string (required)",
  "language": "string (required)",
  "context": "object (optional)"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "score": 88,
    "passed": true,
    "threshold": 80,
    "findings": [...],
    "summary": {
      "total_checks": 5,
      "passed_checks": 4,
      "issues_found": 3
    },
    "recommendations": [...]
  }
}
```

#### `validate_documentation`

**Description**: Validate documentation quality

**Parameters**:
```json
{
  "code": "string (required)",
  "language": "string (required)",
  "doc_type": "string (optional, default: 'all') - docstrings|comments|readme|all"
}
```

#### `validate_tests`

**Description**: Validate test coverage and quality

**Parameters**:
```json
{
  "test_code": "string (required)",
  "source_code": "string (optional) - For coverage analysis",
  "language": "string (required)"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "score": 85,
    "passed": true,
    "metrics": {
      "test_count": 12,
      "assertion_count": 24,
      "coverage_percent": 82.5
    },
    "quality_indicators": {
      "has_setup_teardown": true,
      "tests_edge_cases": true,
      "uses_mocks": true
    }
  }
}
```

### Agent Registry Server Tools

#### `list_agents`

**Description**: List all registered agents with filters

**Parameters**:
```json
{
  "category": "string (optional, default: 'all') - core|specialized|critic|experimental|all",
  "model_tier": "string (optional, default: 'all') - haiku|sonnet|opus|all",
  "min_quality": "integer (optional) - Minimum quality score",
  "include_stats": "boolean (optional, default: true)"
}
```

#### `discover_agent`

**Description**: Find optimal agent for task

**Parameters**:
```json
{
  "task": "string (required)",
  "complexity": "string (optional, default: 'moderate') - simple|moderate|complex",
  "quality_target": "integer (optional, default: 85)",
  "max_cost": "integer (optional) - Max cost in cents"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "recommended_agent": {
      "name": "security-critic",
      "category": "critic",
      "model_tier": "claude-3-opus-20240229",
      "estimated_cost": 0.06,
      "quality_range": [90, 98]
    },
    "reasoning": "Matches use cases: security review | Can achieve quality target",
    "matches_requirements": {
      "complexity": "complex",
      "quality_target": 90,
      "within_budget": true
    }
  }
}
```

#### `get_agent_stats`

**Description**: Get usage statistics for agent

**Parameters**:
```json
{
  "agent_name": "string (required)",
  "include_capabilities": "boolean (optional, default: true)"
}
```

#### `get_cost_analysis`

**Description**: Analyze costs and find optimization opportunities

**Parameters**:
```json
{
  "category": "string (optional, default: 'all')",
  "min_invocations": "integer (optional, default: 0)"
}
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_agents": 12,
      "total_invocations": 45,
      "total_cost_usd": 0.523,
      "cost_by_model_tier": {...}
    },
    "highest_cost_agents": [...],
    "optimization_opportunities": [
      {
        "expensive_agent": "agent-a",
        "cheaper_alternative": "agent-b",
        "quality_difference": 2.3,
        "cost_ratio": 3.5,
        "potential_savings": 0.045,
        "recommendation": "Consider using agent-b instead of agent-a"
      }
    ],
    "recommendations": [...]
  }
}
```

---

## Setup Guide

### Prerequisites

- Python 3.12+
- MCP package installed
- pytest and pytest-asyncio installed
- All workflow components (from Priority 3, Priority 2, Component C1)

### Quick Setup

```bash
# Run automated setup
python3 ~/.claude/scripts/setup_mcp_servers.py

# Or with custom project root
python3 ~/.claude/scripts/setup_mcp_servers.py --project-root /path/to/project

# Skip tests (faster)
python3 ~/.claude/scripts/setup_mcp_servers.py --skip-tests
```

### Manual Setup

#### 1. Install Dependencies

```bash
pip install mcp pytest pytest-asyncio --break-system-packages
```

#### 2. Verify Installation

```bash
cd ~/.claude/lib
python3 -m pytest test_mcp_servers.py -v
# Should show: 30 passed
```

#### 3. Generate Configuration

Configuration is auto-generated at: `~/.claude/mcp_servers/config.json`

#### 4. Add to Claude Desktop

Edit `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "code-review": {
      "command": "python3",
      "args": [
        "/home/jevenson/.claude/lib/mcp_servers/code_review_server.py",
        "--project-root",
        "/your/project/root"
      ]
    },
    "workflow-orchestration": {
      "command": "python3",
      "args": [
        "/home/jevenson/.claude/lib/mcp_servers/workflow_orchestration_server.py"
      ]
    },
    "validation": {
      "command": "python3",
      "args": [
        "/home/jevenson/.claude/lib/mcp_servers/validation_server.py",
        "--project-root",
        "/your/project/root"
      ]
    },
    "agent-registry": {
      "command": "python3",
      "args": [
        "/home/jevenson/.claude/lib/mcp_servers/agent_registry_server.py"
      ]
    }
  }
}
```

#### 5. Restart Claude Desktop

Restart Claude Desktop to load the MCP servers.

#### 6. Verify Tools Available

In Claude Desktop chat, MCP tools should be automatically available.

---

## Usage Examples

### Example 1: Complete Code Review

```
User: Use the review_code tool on this Python function:

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

Claude: [Calls review_code tool]

Result:
✅ Quality Score: 85/100 (PASSED)
⏱️ Time: 6m 23s
💰 Cost: $0.042

Phases:
- Architect: Function structure is acceptable but could be optimized
- Developer: Consider using list comprehension
- Tester: Needs edge case tests (empty list, negative numbers)
- Reviewer: Missing docstring and type hints

Recommendations:
1. Add docstring with parameter and return types
2. Add type hints: def process_data(data: List[int]) -> List[int]
3. Use list comprehension: return [item * 2 for item in data if item > 0]
4. Add unit tests for edge cases
```

### Example 2: Workflow Recommendation

```
User: Use get_workflow_recommendation tool for:
"Build a REST API with 3 endpoints: users, posts, and comments"

Claude: [Calls get_workflow_recommendation]

Result:
Recommended Workflow: parallel

Reasoning:
- Task has 3 components that can be developed in parallel
- Time-sensitive nature benefits from parallel execution
- Expected 60% time savings

Expected Performance:
- Time: Fast (parallel execution)
- Cost: Moderate
- Quality: Good

Alternatives:
- progressive: For cost-sensitive projects
- specialized: For comprehensive review needs
```

### Example 3: Agent Discovery

```
User: Use discover_agent tool to find the best agent for:
"Review this authentication code for security vulnerabilities"

Claude: [Calls discover_agent]

Result:
Recommended Agent: security-critic

Details:
- Category: critic
- Model: Claude Opus (highest quality)
- Estimated Cost: $0.06 per call
- Quality Range: 90-98

Reasoning:
- Matches use cases: security review, vulnerability scanning
- Can achieve quality target (98 max vs 90 required)
- Complex task requires critic-level analysis (Opus)
- Core agent with proven reliability

Capabilities:
- Security vulnerability analysis
- OWASP Top 10 detection
- Authentication security review
- Code injection detection
```

### Example 4: Fast Validation

```
User: Use validate_code tool on this function:

def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

Claude: [Calls validate_code]

Result:
✅ Score: 75/100 (PASSED threshold of 70)

Findings:
1. Missing error handling for KeyError
2. No type hints
3. Missing docstring
4. Could use more Pythonic sum() with generator

Recommendations:
1. Add try-except for KeyError
2. Add type hints: def calculate_total(items: List[Dict]) -> float
3. Add docstring
4. Consider: return sum(item['price'] for item in items)
```

### Example 5: Cost Analysis

```
User: Use get_cost_analysis tool

Claude: [Calls get_cost_analysis]

Result:
Total Cost: $0.523 (45 invocations across 12 agents)

Cost by Model Tier:
- Haiku: $0.045
- Sonnet: $0.328
- Opus: $0.150

Optimization Opportunities:
1. Consider using developer instead of architect
   - Quality difference: +2.3 points
   - Cost ratio: 3.5x more expensive
   - Potential savings: $0.045

2. Monitor security-critic - highest cost agent

Recommendations:
- Review 2 underperforming agents (quality < 80)
- Cache frequent operations to reduce costs
```

---

## Development Guide

### Creating a New MCP Server

#### 1. Inherit from BaseMCPServer

```python
from mcp_servers.base_server import BaseMCPServer, ToolParameter

class MyCustomServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            name="my-custom-server",
            version="1.0.0",
            description="My custom MCP server"
        )

    async def _register_tools(self):
        # Register tools here
        pass

    async def _register_resources(self):
        # Register resources here
        pass
```

#### 2. Register Tools

```python
async def _register_tools(self):
    self.create_tool(
        name="my_tool",
        description="Clear description of what this tool does",
        input_schema={
            "type": "object",
            "properties": {
                "param1": ToolParameter.string("Description of param1"),
                "param2": ToolParameter.integer("Description of param2", default=10)
            },
            "required": ["param1"]
        },
        handler=self._handle_my_tool
    )
```

#### 3. Implement Tool Handler

```python
async def _handle_my_tool(self, param1: str, param2: int = 10) -> Dict[str, Any]:
    """Handle my_tool invocation."""
    try:
        # Execute logic
        result = perform_operation(param1, param2)

        # Return formatted response
        return self.format_success(
            data={"result": result},
            message="Operation completed successfully"
        )

    except Exception as e:
        logger.error(f"my_tool failed: {e}")
        return self.format_error(e)
```

#### 4. Register Resources

```python
async def _register_resources(self):
    self.create_resource(
        uri="myserver://data",
        name="Server Data",
        description="Provides server data",
        handler=self._handle_data_resource
    )
```

#### 5. Implement Resource Handler

```python
async def _handle_data_resource(self) -> Dict[str, Any]:
    """Provide resource data."""
    return {
        "data": "resource content",
        "timestamp": datetime.now().isoformat()
    }
```

#### 6. Run Server

```python
async def main():
    server = MyCustomServer()
    await server.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Best Practices for MCP Server Development

#### Tool Design

1. **Clear Names**: Use descriptive, action-oriented names (`review_code`, not `do_review`)
2. **Rich Descriptions**: Users see these - make them helpful
3. **Complete Schemas**: Define all parameters with types and defaults
4. **Required vs Optional**: Mark parameters appropriately
5. **Validation**: Validate inputs before execution

#### Error Handling

1. **Try-Catch All**: Wrap tool handlers in try-except
2. **Specific Exceptions**: Catch specific errors when possible
3. **Helpful Messages**: Return clear error messages
4. **Log Errors**: Log full stack traces for debugging
5. **Format Errors**: Use `self.format_error(e)` for consistency

#### Response Format

1. **Success Format**: Use `self.format_success(data, message)`
2. **Consistent Structure**: Always include `success`, `data`, optional `message`
3. **Rich Data**: Include all relevant information in response
4. **Metadata**: Add timestamps, costs, execution times when relevant

#### Resource Design

1. **URI Scheme**: Use consistent URI scheme (`server://resource`)
2. **Caching**: Consider caching resource data if appropriate
3. **Update Notifications**: Implement update notifications if resources change
4. **Documentation**: Document what each resource provides

#### Testing

1. **Unit Tests**: Test each tool handler independently
2. **Mock External**: Mock external dependencies (orchestrators, APIs)
3. **Edge Cases**: Test error conditions and edge cases
4. **Integration Tests**: Test full server initialization
5. **Coverage**: Aim for 80%+ code coverage

---

## Troubleshooting

### Common Issues

#### Issue 1: "Module not found" errors

**Symptom**: ImportError when starting server

**Solution**:
```bash
# Check Python path
echo $PYTHONPATH

# Add lib directory to path (in server script)
sys.path.insert(0, str(Path(__file__).parent.parent))
```

#### Issue 2: Server doesn't appear in Claude Desktop

**Symptom**: MCP tools not available in Claude Desktop

**Solution**:
1. Check Claude Desktop config file exists
2. Verify absolute paths in configuration
3. Check server script is executable
4. Restart Claude Desktop
5. Check Claude Desktop logs for errors

#### Issue 3: Tool execution fails

**Symptom**: Tool returns error when called

**Solution**:
1. Check tool parameters match schema
2. Verify required dependencies are installed
3. Check logs for stack trace
4. Test tool handler independently
5. Verify external services (orchestrators) are available

#### Issue 4: Tests failing

**Symptom**: pytest shows failing tests

**Solution**:
```bash
# Install pytest-asyncio
pip install pytest-asyncio --break-system-packages

# Run tests with verbose output
cd ~/.claude/lib
python3 -m pytest test_mcp_servers.py -v --tb=short

# Fix import issues
# Check sys.path.insert statements in each server
```

#### Issue 5: Configuration validation fails

**Symptom**: setup_mcp_servers.py reports invalid config

**Solution**:
1. Check all script paths exist
2. Verify paths are absolute (not relative)
3. Check JSON syntax is valid
4. Ensure all required keys present (command, args)

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Checking Server Status

```python
from mcp_servers.server_manager import ServerManager

manager = ServerManager()
# ... register servers ...

# Print summary
manager.print_summary()

# Validate all servers
results = manager.validate_all_servers()
for name, result in results.items():
    print(f"{name}: {'✅' if result['valid'] else '❌'}")
    if result['issues']:
        for issue in result['issues']:
            print(f"  - {issue}")
```

---

## Best Practices

### For Users

1. **Start with Quick Tools**: Use `quick_review` before `review_code` for fast feedback
2. **Use Recommendations**: Let `get_workflow_recommendation` guide workflow choice
3. **Check Cost**: Use `get_cost_analysis` to monitor spending
4. **Discover Agents**: Use `discover_agent` to find optimal agents
5. **Validate Early**: Run `validate_code` before committing

### For Developers

1. **Tool Composition**: Design tools to compose well together
2. **Error Messages**: Make error messages actionable
3. **Documentation**: Keep tool descriptions updated
4. **Testing**: Test with real use cases
5. **Performance**: Monitor execution times
6. **Costs**: Track API costs per tool

### For System Administration

1. **Monitor Usage**: Track tool invocation counts
2. **Watch Costs**: Set up cost alerts
3. **Update Regularly**: Keep servers updated
4. **Backup Config**: Keep configuration backed up
5. **Security**: Protect API keys and credentials

---

## API Reference

### BaseMCPServer

#### Methods

##### `__init__(name: str, version: str, description: str)`
Initialize base server with metadata.

##### `create_tool(name, description, input_schema, handler) -> Tool`
Create and register a tool.

##### `create_resource(uri, name, description, handler) -> Resource`
Create and register a resource.

##### `handle_tool_call(name, arguments) -> Any`
Handle incoming tool call.

##### `handle_resource_read(uri) -> Dict`
Handle resource read request.

##### `format_error(error) -> Dict`
Format error for MCP response.

##### `format_success(data, message) -> Dict`
Format success response for MCP.

##### `async initialize()`
Initialize server (register tools and resources).

##### `async run()`
Run the MCP server using stdio transport.

### ToolParameter

Helper class for defining tool parameters.

#### Methods

##### `ToolParameter.string(description, default=None, enum=None) -> Dict`
Create string parameter schema.

##### `ToolParameter.integer(description, default=None, minimum=None, maximum=None) -> Dict`
Create integer parameter schema.

##### `ToolParameter.boolean(description, default=None) -> Dict`
Create boolean parameter schema.

##### `ToolParameter.object(description, properties, required=None) -> Dict`
Create object parameter schema.

##### `ToolParameter.array(description, items, min_items=None, max_items=None) -> Dict`
Create array parameter schema.

### ServerManager

#### Methods

##### `register_server(name, server_instance, config=None) -> ServerInfo`
Register a server instance.

##### `unregister_server(name) -> bool`
Unregister a server.

##### `list_servers(status_filter=None) -> List[ServerInfo]`
List all registered servers.

##### `get_server_summary() -> Dict`
Get summary of all servers.

##### `load_config(config_path=None) -> Dict`
Load configuration from file.

##### `save_config(config, config_path=None)`
Save configuration to file.

##### `validate_server(name) -> Dict`
Validate server configuration.

---

## Appendix

### File Structure

```
~/.claude/
├── lib/
│   ├── mcp_servers/
│   │   ├── __init__.py
│   │   ├── base_server.py              # Base class
│   │   ├── code_review_server.py       # Code review
│   │   ├── workflow_orchestration_server.py  # Workflows
│   │   ├── validation_server.py        # Validation
│   │   ├── agent_registry_server.py    # Agent registry
│   │   └── server_manager.py           # Manager
│   ├── test_mcp_servers.py            # Tests (30)
│   └── MCP_SERVERS_README.md          # This file
├── scripts/
│   └── setup_mcp_servers.py           # Setup script
└── mcp_servers/
    └── config.json                     # Configuration
```

### Tool Count by Server

| Server | Tools | Resources | Total |
|--------|-------|-----------|-------|
| Code Review | 4 | 2 | 6 |
| Workflow Orchestration | 5 | 2 | 7 |
| Validation | 3 | 1 | 4 |
| Agent Registry | 4 | 2 | 6 |
| **Total** | **16** | **7** | **23** |

### Dependencies

- **Runtime**:
  - Python 3.12+
  - mcp >= 1.12.2
  - anthropic (for API access)

- **Development**:
  - pytest >= 8.2
  - pytest-asyncio >= 1.2.0
  - pytest-cov (optional)

- **Components**:
  - Priority 3: Multi-agent workflows
  - Priority 2: Validation system
  - Component C1: Agent registry

---

**Version History**

- **1.0.0** (Nov 3, 2025) - Initial release
  - 4 MCP servers
  - 16 tools, 7 resources
  - 30 comprehensive tests (all passing)
  - Complete setup automation
  - Production-ready

---

**Quick Links**

- [Setup Guide](#setup-guide)
- [Tool Schemas](#tool-schemas)
- [Usage Examples](#usage-examples)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)
