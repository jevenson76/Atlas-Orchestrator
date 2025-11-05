# Agent Registry System - Global Agent Directory

**Version:** 1.0.0
**Status:** Production Ready
**Last Updated:** November 3, 2025

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Model Discipline](#model-discipline)
4. [Quick Start](#quick-start)
5. [Agent Registration](#agent-registration)
6. [Agent Discovery](#agent-discovery)
7. [Usage Tracking](#usage-tracking)
8. [Analytics & Reporting](#analytics--reporting)
9. [Integration Guide](#integration-guide)
10. [Best Practices](#best-practices)
11. [API Reference](#api-reference)
12. [Migration Guide](#migration-guide)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The **Agent Registry System** is a centralized directory for managing all AI agents with enforced model discipline, usage tracking, and intelligent discovery capabilities.

### Key Features

- **Centralized Registry**: Single source of truth for all agents
- **Model Discipline Enforcement**: Strict rules ensuring optimal model selection
- **Usage Tracking**: Automatic recording of invocations, costs, and quality
- **Smart Discovery**: Find agents by use case, cost, quality, or category
- **Analytics**: Comprehensive reporting on usage, costs, and optimization opportunities
- **Integration Ready**: Easy integration with existing orchestrators

### Components

```
~/.claude/
├── agents/
│   └── global/
│       ├── core/           # Essential agents (always loaded)
│       ├── specialized/    # Domain-specific agents
│       ├── critics/        # Critic agents (Opus only)
│       ├── experimental/   # Testing new agents
│       └── .registry/      # Metadata and analytics
│           ├── agent_registry.json
│           ├── usage_stats.json
│           └── model_discipline.json
└── lib/
    ├── agent_registry.py            # Core registry system
    ├── agent_discovery.py           # Discovery and search
    ├── agent_registry_integration.py # Orchestrator helpers
    ├── promote_agents.py            # Agent promotion script
    └── test_agent_registry.py       # Test suite (20 tests)
```

---

## Architecture

### Core Classes

#### 1. AgentRegistry
Central registry managing all agents with persistence and model discipline.

```python
from agent_registry import AgentRegistry, AgentCategory, ModelTier

registry = AgentRegistry()  # Singleton pattern
```

#### 2. AgentMetadata
Comprehensive metadata for each agent.

```python
@dataclass
class AgentMetadata:
    # Identity
    name: str
    category: AgentCategory
    model_tier: ModelTier

    # Description
    description: str
    use_cases: List[str]

    # Performance expectations
    estimated_cost_per_call: float
    estimated_time_seconds: float
    quality_range: Tuple[int, int]  # (min, max)

    # Usage statistics (tracked over time)
    total_invocations: int = 0
    total_cost_usd: float = 0.0
    average_quality_score: Optional[float] = None
```

#### 3. AgentDiscovery
Search and recommendation engine for finding optimal agents.

```python
from agent_discovery import AgentDiscovery

discovery = AgentDiscovery()
```

#### 4. AgentUsageTracker
Helper for orchestrators to track agent usage.

```python
from agent_registry_integration import AgentUsageTracker

tracker = AgentUsageTracker()
```

### Data Flow

```
┌─────────────────┐
│ Orchestrator    │
│ or Script       │
└────────┬────────┘
         │
         │ 1. Find Agent
         ▼
┌─────────────────────────┐
│  AgentDiscovery         │
│  - Search by use case   │
│  - Recommend for task   │
│  - Load agent instance  │
└────────┬────────────────┘
         │
         │ 2. Query Registry
         ▼
┌─────────────────────────┐
│  AgentRegistry          │
│  - Store metadata       │
│  - Enforce discipline   │
│  - Track usage          │
└────────┬────────────────┘
         │
         │ 3. Persist
         ▼
┌─────────────────────────┐
│  JSON Files             │
│  - agent_registry.json  │
│  - usage_stats.json     │
└─────────────────────────┘
```

---

## Model Discipline

### Tier System

The registry enforces strict model discipline based on task characteristics:

| Model Tier | Model ID | Use Case | Cost | When to Use |
|-----------|----------|----------|------|-------------|
| **HAIKU** | `claude-3-5-haiku-20241022` | High-volume, fast operations | $0.25/$1.25 per 1M tokens | Scouting, summarization, >1000 calls/day |
| **SONNET** | `claude-3-5-sonnet-20241022` | Standard development work | $3/$15 per 1M tokens | Implementation, analysis, standard tasks |
| **OPUS** | `claude-3-opus-20240229` | Complex judgment and critique | $15/$75 per 1M tokens | Architecture, critique, complex decisions |

### Discipline Rules

#### Rule 1: Critics MUST Use Opus (STRICT)
```python
# This will RAISE ModelDisciplineViolationError
registry.register_agent(
    name="my-critic",
    category=AgentCategory.CRITIC,
    model_tier=ModelTier.SONNET  # ❌ REJECTED
)

# This will succeed
registry.register_agent(
    name="my-critic",
    category=AgentCategory.CRITIC,
    model_tier=ModelTier.OPUS  # ✅ ACCEPTED
)
```

**Rationale**: Critics provide judgment on code quality, security, performance, and architecture. These judgments require the most sophisticated reasoning to avoid false positives/negatives that could be costly.

#### Rule 2: High-Volume Agents Should Use Haiku (WARNING)
Agents expected to handle >1000 calls/day should use Haiku for cost efficiency.

#### Rule 3: Standard Tasks Should Use Sonnet (RECOMMENDATION)
Most development work (implementation, analysis, testing) works well with Sonnet.

#### Rule 4: Complex Judgment Should Use Opus (RECOMMENDATION)
Architecture decisions, design reviews, and complex planning benefit from Opus.

### Model Recommendation Algorithm

```python
def recommend_model(
    task_complexity: str,  # "simple", "moderate", "complex"
    volume: str,           # "low", "medium", "high"
    requires_judgment: bool = False
) -> ModelTier:
    # Judgment or complex tasks → Opus
    if requires_judgment or task_complexity == "complex":
        return ModelTier.OPUS

    # High volume → Haiku
    if volume == "high":
        return ModelTier.HAIKU

    # Simple tasks → Haiku
    if task_complexity == "simple":
        return ModelTier.HAIKU

    # Default: Sonnet
    return ModelTier.SONNET
```

---

## Quick Start

### 1. View Registered Agents

```bash
# Run promotion script to see all agents
python3 ~/.claude/lib/promote_agents.py

# Output:
# ✅ Registered 12 agents:
#   • architect (core, opus)
#   • developer (core, sonnet)
#   • tester (core, sonnet)
#   • reviewer (core, opus)
#   • security-critic (critic, opus)
#   • performance-critic (critic, opus)
#   ...
```

### 2. Find Agents Programmatically

```python
from agent_discovery import AgentDiscovery

discovery = AgentDiscovery()

# Find all security-focused agents
security_agents = discovery.find_agents(use_case="security")
# → [security-critic, reviewer]

# Find all critics
critics = discovery.find_agents(category=AgentCategory.CRITIC)
# → [security-critic, performance-critic, architecture-critic, ...]

# Find agents under budget
affordable = discovery.get_agents_by_cost(max_cost=0.02)
# → [developer, tester, validation-orchestrator]
```

### 3. Get Recommendations

```python
# Recommend agent for specific task
recommended = discovery.recommend_agent(
    task="Review authentication code for SQL injection vulnerabilities",
    complexity="high",
    quality_target=90
)
# → security-critic (quality: 90-98, cost: $0.06)

print(f"Recommended: {recommended.name}")
print(f"Model: {recommended.model_tier.value}")
print(f"Expected quality: {recommended.quality_range}")
```

### 4. View Analytics

```bash
# Full analytics report
python3 ~/.claude/scripts/agent_analytics.py

# Top 5 most used agents
python3 ~/.claude/scripts/agent_analytics.py --top 5

# Filter by category
python3 ~/.claude/scripts/agent_analytics.py --category critic

# JSON output
python3 ~/.claude/scripts/agent_analytics.py --format json
```

---

## Agent Registration

### Registering a New Agent

```python
from agent_registry import get_global_registry, AgentCategory, ModelTier

registry = get_global_registry()

registry.register_agent(
    name="my-new-agent",
    category=AgentCategory.SPECIALIZED,
    model_tier=ModelTier.SONNET,
    description="What this agent does (1-2 sentences)",
    use_cases=[
        "use case 1",
        "use case 2",
        "use case 3"
    ],
    estimated_cost_per_call=0.015,  # USD
    estimated_time_seconds=20.0,
    quality_range=(80, 92),  # (min, max) expected scores
    version="1.0.0"
)
```

### Registration Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | `str` | Unique identifier (kebab-case) | `"security-critic"` |
| `category` | `AgentCategory` | Core, Specialized, Critic, Experimental | `AgentCategory.CRITIC` |
| `model_tier` | `ModelTier` | Haiku, Sonnet, or Opus | `ModelTier.OPUS` |
| `description` | `str` | What the agent does (1-2 sentences) | `"Analyzes code for security vulnerabilities"` |
| `use_cases` | `List[str]` | Searchable use case descriptions | `["security review", "vulnerability scanning"]` |
| `estimated_cost_per_call` | `float` | Estimated cost in USD | `0.05` |
| `estimated_time_seconds` | `float` | Estimated execution time | `30.0` |
| `quality_range` | `Tuple[int, int]` | (min, max) expected quality scores (0-100) | `(85, 98)` |
| `version` | `str` | Agent version (semver) | `"1.0.0"` |

### Category Guidelines

#### CORE
Essential agents loaded by default. Examples:
- `architect`: System design and architecture
- `developer`: Code implementation
- `tester`: Test generation and validation
- `reviewer`: Code review

#### SPECIALIZED
Domain-specific agents for particular tasks. Examples:
- `validation-orchestrator`: Multi-agent validation workflows
- `master-orchestrator`: Complex multi-phase orchestration

#### CRITIC
Quality assurance agents (MUST use Opus). Examples:
- `security-critic`: Security vulnerability analysis
- `performance-critic`: Performance bottleneck identification
- `architecture-critic`: Design pattern review

#### EXPERIMENTAL
Agents in testing phase, not production-ready.

### Validation and Errors

```python
try:
    registry.register_agent(
        name="bad-critic",
        category=AgentCategory.CRITIC,
        model_tier=ModelTier.SONNET  # ❌ Wrong tier
    )
except ModelDisciplineViolationError as e:
    print(e)
    # "CRITICAL: Agent 'bad-critic' is a CRITIC but uses claude-3-5-sonnet-20241022.
    #  Critics MUST use Opus for reliable judgment."
```

---

## Agent Discovery

### Search by Use Case

```python
from agent_discovery import AgentDiscovery

discovery = AgentDiscovery()

# Substring search on use cases (case-insensitive)
agents = discovery.find_agents(use_case="security")
# Matches: security review, security vulnerability, security audit, etc.

for agent in agents:
    print(f"{agent.name}: {agent.description}")
```

### Filter by Criteria

```python
# Multiple filters
agents = discovery.find_agents(
    use_case="performance",
    model_tier=ModelTier.OPUS,
    category=AgentCategory.CRITIC,
    min_quality=90
)
# → [performance-critic]
```

### Get Agent Capabilities

```python
caps = discovery.get_agent_capabilities("security-critic")

print(f"Name: {caps['name']}")
print(f"Model: {caps['model']}")
print(f"Use cases: {caps['use_cases']}")
print(f"Cost per call: ${caps['estimated_cost_per_call']}")
print(f"Quality range: {caps['quality_range']}")
print(f"Stats: {caps['stats']}")
```

### Recommend Agent for Task

The discovery system uses keyword extraction to recommend optimal agents:

```python
# Security task
agent = discovery.recommend_agent(
    task="Review this authentication code for SQL injection vulnerabilities",
    complexity="high",
    quality_target=90
)
# → security-critic

# Implementation task
agent = discovery.recommend_agent(
    task="Implement JWT-based authentication with refresh tokens",
    complexity="moderate",
    quality_target=85
)
# → developer

# Architecture task
agent = discovery.recommend_agent(
    task="Design a microservices architecture for high-scale system",
    complexity="complex",
    quality_target=90
)
# → architect
```

#### Keyword Categories

| Category | Keywords |
|----------|----------|
| Security | security, vulnerability, exploit, injection, xss, authentication |
| Performance | performance, optimize, bottleneck, speed, efficiency, cache |
| Architecture | architecture, design, pattern, structure, scalability |
| Quality | quality, style, maintainability, readability, clean code |
| Documentation | documentation, docstring, readme, comments, api docs |
| Testing | test, testing, unit test, integration test, coverage |
| Implementation | implement, code, develop, build, create, write |
| Review | review, audit, check, validate, assess |

### Cost and Quality Filters

```python
# Find agents within budget
affordable = discovery.get_agents_by_cost(
    max_cost=0.02,
    category=AgentCategory.CORE
)

# Find high-quality agents
high_quality = discovery.get_agents_by_quality(
    min_quality=90,
    category=AgentCategory.CRITIC
)
```

---

## Usage Tracking

### Automatic Tracking

Every agent invocation should be tracked for analytics and cost monitoring.

### Manual Recording

```python
from agent_registry import get_global_registry
import time

registry = get_global_registry()

# Execute agent
start_time = time.time()
result = await agent.execute(...)
execution_time = time.time() - start_time

# Record usage
registry.record_usage(
    agent_name="developer",
    cost_usd=0.0145,
    execution_time_seconds=execution_time,
    quality_score=88  # Optional: 0-100 score
)
```

### Using AgentUsageTracker

```python
from agent_registry_integration import AgentUsageTracker

tracker = AgentUsageTracker()

# Method 1: Manual recording
start_time = time.time()
result = await agent.execute(...)
tracker.record(
    agent_name="developer",
    cost_usd=result.cost,
    execution_time_seconds=time.time() - start_time,
    quality_score=result.quality
)

# Method 2: Context manager (automatic time tracking)
with tracker.track_agent("developer", cost_usd=0.015, quality_score=88):
    result = await agent.execute(...)
    # Time tracked automatically
```

### Quality Scores

Quality scores (0-100) help track agent performance over time:

| Score Range | Interpretation |
|-------------|----------------|
| 90-100 | Excellent - exceeds expectations |
| 80-89 | Good - meets expectations |
| 70-79 | Acceptable - minor issues |
| 60-69 | Poor - significant issues |
| 0-59 | Failed - unacceptable quality |

Quality scores are subjective and can be based on:
- User feedback
- Automated validation results
- Code review scores
- Test pass rates
- Error rates

---

## Analytics & Reporting

### Command-Line Analytics

```bash
# Full report
python3 ~/.claude/scripts/agent_analytics.py

# Output sections:
# 1. Summary (total agents, invocations, costs)
# 2. Most used agents
# 3. Highest cost agents
# 4. Highest quality agents
# 5. Underperforming agents (quality < 80)
# 6. Cost optimization opportunities
```

### CLI Options

```bash
# Top N agents
python3 ~/.claude/scripts/agent_analytics.py --top 5

# Filter by category
python3 ~/.claude/scripts/agent_analytics.py --category critic

# Minimum invocations
python3 ~/.claude/scripts/agent_analytics.py --min-invocations 10

# JSON output
python3 ~/.claude/scripts/agent_analytics.py --format json > report.json
```

### Programmatic Analytics

```python
from agent_analytics import AgentAnalytics

analytics = AgentAnalytics()

# Generate report
report = analytics.generate_report(
    top_n=10,
    category_filter=AgentCategory.CRITIC,
    min_invocations=5
)

# Access report data
print(f"Total cost: ${report['summary']['total_cost_usd']:.4f}")
print(f"Total invocations: {report['summary']['total_invocations']}")

# Most used agents
for agent in report['most_used_agents']:
    print(f"{agent['name']}: {agent['invocations']} calls")

# Optimization opportunities
for opp in report['optimization_opportunities']:
    print(f"💡 {opp['recommendation']}")
    print(f"   Potential savings: ${opp['potential_savings']:.4f}")
```

### Cost Optimization

The analytics system identifies optimization opportunities by:

1. Grouping agents by category
2. Comparing expensive vs. cheaper agents
3. Analyzing quality differences
4. Flagging when:
   - Quality improvement < 5 points
   - Cost ratio > 2x
   - Significant savings possible

Example output:
```
💡 Consider using developer instead of architect
   Quality difference: +2.3 points
   Cost ratio: 3.3x more expensive
   Potential savings: $0.0245
```

---

## Integration Guide

### Integrating with Orchestrators

#### Step 1: Add Usage Tracker

```python
from agent_registry_integration import AgentUsageTracker

class MyOrchestrator:
    def __init__(self):
        # Add usage tracker
        self.usage_tracker = AgentUsageTracker()
        # ... existing initialization
```

#### Step 2: Record Usage in Phases

```python
async def execute_phase(self, phase_name: str, agent):
    """Execute a phase and track usage."""
    start_time = time.time()

    # Execute agent
    result = await agent.execute(
        system_prompt=self.system_prompts[phase_name],
        user_message=self.user_messages[phase_name]
    )

    # Record usage
    self.usage_tracker.record(
        agent_name=phase_name,
        cost_usd=result.cost,
        execution_time_seconds=time.time() - start_time,
        quality_score=result.quality_score if hasattr(result, 'quality_score') else None
    )

    return result
```

#### Step 3: Use Context Manager (Alternative)

```python
async def execute_phase(self, phase_name: str, agent):
    """Execute phase with automatic time tracking."""
    with self.usage_tracker.track_agent(phase_name, cost_usd=0.015):
        result = await agent.execute(...)
        # Time tracked automatically
    return result
```

### Example: Full Orchestrator Integration

```python
from agent_registry_integration import AgentUsageTracker
from agent_discovery import AgentDiscovery

class EnhancedOrchestrator:
    def __init__(self):
        self.usage_tracker = AgentUsageTracker()
        self.discovery = AgentDiscovery()

    async def run_workflow(self, task: str):
        """Run workflow with agent discovery and usage tracking."""

        # Step 1: Discover optimal agent
        agent_metadata = self.discovery.recommend_agent(
            task=task,
            complexity="moderate",
            quality_target=85
        )

        print(f"Using: {agent_metadata.name} ({agent_metadata.model_tier.value})")

        # Step 2: Load agent
        agent = self.discovery.load_agent(agent_metadata.name)

        # Step 3: Execute with tracking
        start_time = time.time()
        result = await agent.execute(
            system_prompt="You are a helpful assistant",
            user_message=task
        )

        # Step 4: Record usage
        self.usage_tracker.record(
            agent_name=agent_metadata.name,
            cost_usd=result.cost,
            execution_time_seconds=time.time() - start_time,
            quality_score=self._assess_quality(result)
        )

        return result

    def _assess_quality(self, result) -> int:
        """Assess result quality (0-100)."""
        # Implement your quality assessment logic
        return 85
```

---

## Best Practices

### Agent Design

#### 1. Clear Use Cases
Define specific, searchable use cases:
```python
# ✅ Good: Specific and searchable
use_cases=[
    "security vulnerability analysis",
    "OWASP Top 10 detection",
    "authentication security review"
]

# ❌ Bad: Too vague
use_cases=["security", "checking"]
```

#### 2. Accurate Cost Estimates
Base estimates on actual API costs:
```python
# Estimate based on expected token usage
# Example: 2000 input tokens + 500 output tokens with Sonnet
input_cost = (2000 / 1_000_000) * 3.00  # $3 per 1M input tokens
output_cost = (500 / 1_000_000) * 15.00  # $15 per 1M output tokens
estimated_cost_per_call = input_cost + output_cost  # ≈ $0.0135
```

#### 3. Realistic Quality Ranges
Set ranges based on expected performance:
```python
# Critics: High quality expected
quality_range=(90, 98)

# Developers: Good quality expected
quality_range=(80, 92)

# High-volume tasks: Acceptable quality
quality_range=(70, 85)
```

#### 4. Descriptive Names
Use kebab-case with clear purpose:
```python
# ✅ Good
name="security-critic"
name="jwt-auth-specialist"
name="react-component-generator"

# ❌ Bad
name="agent1"
name="SecurityAgent"
name="my_agent"
```

### Usage Tracking

#### 1. Always Record Usage
Track every invocation for accurate analytics:
```python
# ✅ Good: Always track
result = await agent.execute(...)
tracker.record(agent_name, cost, time, quality)

# ❌ Bad: Inconsistent tracking
result = await agent.execute(...)
# Forgot to track!
```

#### 2. Include Quality Scores When Possible
Quality data enables performance monitoring:
```python
# ✅ Good: Include quality when measurable
tracker.record(
    agent_name="developer",
    cost_usd=0.015,
    execution_time_seconds=18.3,
    quality_score=88  # Based on validation
)

# ⚠️ Acceptable: Omit if not measurable
tracker.record(
    agent_name="developer",
    cost_usd=0.015,
    execution_time_seconds=18.3
    # quality_score omitted
)
```

#### 3. Use Context Managers for Simplicity
Automatic time tracking reduces errors:
```python
# ✅ Best: Context manager
with tracker.track_agent("developer", cost_usd=0.015, quality_score=88):
    result = await agent.execute(...)

# ✅ Good: Manual tracking
start = time.time()
result = await agent.execute(...)
tracker.record("developer", 0.015, time.time() - start, 88)
```

### Model Selection

#### 1. Start with Recommendations
Use the registry's recommendation system:
```python
# Get recommendation
recommended_tier = registry.recommend_model(
    task_complexity="moderate",
    volume="medium",
    requires_judgment=False
)
# → SONNET
```

#### 2. Follow Model Discipline
Respect the tier guidelines:
```python
# ✅ Correct: Critic uses Opus
register_agent("security-critic", AgentCategory.CRITIC, ModelTier.OPUS)

# ✅ Correct: High-volume uses Haiku
register_agent("url-validator", AgentCategory.SPECIALIZED, ModelTier.HAIKU)

# ✅ Correct: Standard work uses Sonnet
register_agent("developer", AgentCategory.CORE, ModelTier.SONNET)
```

#### 3. Monitor and Optimize
Use analytics to identify optimization opportunities:
```bash
# Run analytics regularly
python3 ~/.claude/scripts/agent_analytics.py

# Look for:
# - Underperforming agents (quality < expected)
# - Cost optimization opportunities (expensive agents not outperforming)
# - Model tier mismatches
```

### Registry Management

#### 1. Version Agents
Use semantic versioning:
```python
# Initial release
register_agent(..., version="1.0.0")

# Bug fix
register_agent(..., version="1.0.1")

# New features
register_agent(..., version="1.1.0")

# Breaking changes
register_agent(..., version="2.0.0")
```

#### 2. Update Estimates Regularly
Refine estimates based on actual usage:
```python
# After collecting data
stats = registry.get_agent_stats("developer")
actual_avg_cost = stats['average_cost_per_call']
actual_avg_time = stats['average_execution_time']

# Update registration with actual values
registry.register_agent(
    ...,
    estimated_cost_per_call=actual_avg_cost,
    estimated_time_seconds=actual_avg_time
)
```

#### 3. Clean Up Experimental Agents
Move successful experiments to proper categories:
```python
# During experimentation
register_agent("new-feature", AgentCategory.EXPERIMENTAL, ...)

# After validation
register_agent("new-feature", AgentCategory.SPECIALIZED, ...)
```

---

## API Reference

### AgentRegistry

#### Methods

##### `register_agent()`
```python
def register_agent(
    name: str,
    category: AgentCategory,
    model_tier: ModelTier,
    description: str,
    use_cases: List[str],
    estimated_cost_per_call: float,
    estimated_time_seconds: float,
    quality_range: Tuple[int, int],
    version: str = "1.0.0",
    enforce_discipline: bool = True
) -> AgentMetadata
```
Register a new agent with the global registry.

**Raises**: `ModelDisciplineViolationError` if critic doesn't use Opus.

##### `get_agent()`
```python
def get_agent(name: str) -> Optional[AgentMetadata]
```
Get agent metadata by name.

##### `list_agents()`
```python
def list_agents(
    category: Optional[AgentCategory] = None,
    model_tier: Optional[ModelTier] = None
) -> List[AgentMetadata]
```
List agents filtered by category and/or model tier.

##### `record_usage()`
```python
def record_usage(
    agent_name: str,
    cost_usd: float,
    execution_time_seconds: float,
    quality_score: Optional[int] = None
)
```
Record usage statistics for an agent invocation.

##### `get_agent_stats()`
```python
def get_agent_stats(agent_name: str) -> Optional[Dict[str, Any]]
```
Get usage statistics for a specific agent.

##### `get_all_stats()`
```python
def get_all_stats() -> Dict[str, Any]
```
Get aggregate statistics across all agents.

##### `recommend_model()`
```python
def recommend_model(
    task_complexity: str,  # "simple", "moderate", "complex"
    volume: str,           # "low", "medium", "high"
    requires_judgment: bool = False
) -> ModelTier
```
Recommend model tier based on task characteristics.

### AgentDiscovery

#### Methods

##### `find_agents()`
```python
def find_agents(
    use_case: Optional[str] = None,
    model_tier: Optional[ModelTier] = None,
    category: Optional[AgentCategory] = None,
    min_quality: Optional[int] = None
) -> List[AgentMetadata]
```
Find agents matching criteria with substring search on use cases.

##### `recommend_agent()`
```python
def recommend_agent(
    task: str,
    complexity: str = "moderate",
    quality_target: int = 85,
    max_cost: Optional[float] = None
) -> Optional[AgentMetadata]
```
Recommend best agent for a given task using keyword extraction.

##### `load_agent()`
```python
def load_agent(name: str, **kwargs) -> Optional[ResilientBaseAgent]
```
Load and initialize agent as ResilientBaseAgent instance.

##### `get_agent_capabilities()`
```python
def get_agent_capabilities(name: str) -> Optional[Dict[str, Any]]
```
Get detailed capabilities for an agent including stats.

##### `get_agents_by_cost()`
```python
def get_agents_by_cost(
    max_cost: float,
    category: Optional[AgentCategory] = None
) -> List[AgentMetadata]
```
Find agents within cost budget, sorted by cost (cheapest first).

##### `get_agents_by_quality()`
```python
def get_agents_by_quality(
    min_quality: int,
    category: Optional[AgentCategory] = None
) -> List[AgentMetadata]
```
Find agents meeting quality threshold, sorted by quality (highest first).

### AgentUsageTracker

#### Methods

##### `record()`
```python
def record(
    agent_name: str,
    cost_usd: float,
    execution_time_seconds: float,
    quality_score: Optional[int] = None
)
```
Record agent usage to registry.

##### `track_agent()`
```python
@contextmanager
def track_agent(
    agent_name: str,
    cost_usd: Optional[float] = None,
    quality_score: Optional[int] = None
)
```
Context manager for automatic time tracking.

##### `disable()` / `enable()`
```python
def disable()
def enable()
```
Disable/enable usage tracking (useful for testing).

### AgentAnalytics

#### Methods

##### `generate_report()`
```python
def generate_report(
    top_n: int = 10,
    category_filter: Optional[AgentCategory] = None,
    min_invocations: int = 0
) -> Dict[str, Any]
```
Generate comprehensive analytics report.

##### `print_report()`
```python
def print_report(report: Dict[str, Any], format: str = "text")
```
Print report in specified format ("text" or "json").

---

## Migration Guide

### Migrating Existing Agents

#### Step 1: Identify Agents
List all agents currently in use:
```python
# agents.py (example)
class SecurityAgent:
    model = "claude-3-opus-20240229"
    ...

class DeveloperAgent:
    model = "claude-3-5-sonnet-20241022"
    ...
```

#### Step 2: Create Registration Script
```python
# migrate_agents.py
from agent_registry import get_global_registry, AgentCategory, ModelTier

registry = get_global_registry()

# Register each agent
registry.register_agent(
    name="security-agent",
    category=AgentCategory.CRITIC,
    model_tier=ModelTier.OPUS,
    description="Security vulnerability analysis",
    use_cases=["security review", "vulnerability scanning"],
    estimated_cost_per_call=0.06,
    estimated_time_seconds=35.0,
    quality_range=(90, 98)
)

registry.register_agent(
    name="developer-agent",
    category=AgentCategory.CORE,
    model_tier=ModelTier.SONNET,
    description="Code implementation",
    use_cases=["coding", "implementation"],
    estimated_cost_per_call=0.015,
    estimated_time_seconds=20.0,
    quality_range=(80, 92)
)
```

#### Step 3: Update Orchestrators
Add usage tracking to existing orchestrators:
```python
# Before migration
class MyOrchestrator:
    async def run(self):
        result = await self.agent.execute(...)
        return result

# After migration
from agent_registry_integration import AgentUsageTracker

class MyOrchestrator:
    def __init__(self):
        self.usage_tracker = AgentUsageTracker()

    async def run(self):
        start = time.time()
        result = await self.agent.execute(...)
        self.usage_tracker.record(
            agent_name="my-agent",
            cost_usd=result.cost,
            execution_time_seconds=time.time() - start
        )
        return result
```

#### Step 4: Replace Direct Agent Creation
Use discovery system instead of direct instantiation:
```python
# Before migration
from agents import SecurityAgent
agent = SecurityAgent()

# After migration
from agent_discovery import AgentDiscovery
discovery = AgentDiscovery()
agent = discovery.load_agent("security-agent")
```

#### Step 5: Verify Registration
```bash
# Run promotion script to verify
python3 ~/.claude/lib/promote_agents.py

# Check analytics
python3 ~/.claude/scripts/agent_analytics.py
```

---

## Troubleshooting

### Common Issues

#### Issue 1: ModelDisciplineViolationError
```
ModelDisciplineViolationError: Agent 'my-critic' is a CRITIC but uses claude-3-5-sonnet-20241022.
Critics MUST use Opus.
```

**Solution**: Change model tier to Opus for critic agents:
```python
registry.register_agent(
    name="my-critic",
    category=AgentCategory.CRITIC,
    model_tier=ModelTier.OPUS  # ✅ Fixed
)
```

#### Issue 2: Agent Not Found
```
WARNING: Attempted to record usage for unregistered agent: my-agent
```

**Solution**: Register the agent first:
```python
# Check if agent exists
agent = registry.get_agent("my-agent")
if not agent:
    # Register it
    registry.register_agent(...)
```

#### Issue 3: Usage Not Persisting
Usage statistics not appearing after restart.

**Solution**: Ensure `record_usage()` is being called (it auto-saves):
```python
# Verify recording is happening
registry.record_usage("my-agent", 0.015, 18.5, 88)

# Check persistence
stats = registry.get_agent_stats("my-agent")
print(stats['total_invocations'])  # Should be > 0
```

#### Issue 4: Discovery Returns No Results
```python
agents = discovery.find_agents(use_case="authentication")
# → []
```

**Solution**: Check use case spelling and ensure agents have matching use cases:
```python
# View agent use cases
agent = registry.get_agent("my-agent")
print(agent.use_cases)

# Add use case if missing
registry.register_agent(
    ...,
    use_cases=["authentication", "auth", "login"]  # More keywords
)
```

#### Issue 5: Analytics Shows Zero Cost
```bash
python3 ~/.claude/scripts/agent_analytics.py
# Total cost: $0.0000
```

**Solution**: Ensure usage is being recorded with actual costs:
```python
# ✅ Correct: Real cost
tracker.record("my-agent", cost_usd=0.0145, ...)

# ❌ Wrong: Zero cost
tracker.record("my-agent", cost_usd=0.0, ...)
```

### Debug Mode

Enable detailed logging:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

# Now registry operations will log details
registry = AgentRegistry()
# DEBUG: AgentRegistry initialized with 12 agents
```

### Registry File Locations

If issues persist, check registry files directly:
```bash
# Main registry
cat ~/.claude/agents/global/.registry/agent_registry.json

# Usage statistics
cat ~/.claude/agents/global/.registry/usage_stats.json

# Check file permissions
ls -la ~/.claude/agents/global/.registry/
```

### Reset Registry (Last Resort)

```bash
# Backup first
cp -r ~/.claude/agents/global/.registry ~/.claude/agents/global/.registry.backup

# Remove registry files
rm ~/.claude/agents/global/.registry/*.json

# Re-run promotion
python3 ~/.claude/lib/promote_agents.py
```

---

## Appendix

### Current Registered Agents (12 Total)

#### Core Agents (4)
1. **architect** - System design and architecture planning (Opus)
2. **developer** - Code implementation (Sonnet)
3. **tester** - Test generation and validation (Sonnet)
4. **reviewer** - Code review and quality assessment (Opus)

#### Critics (5)
5. **security-critic** - Security vulnerability analysis (Opus)
6. **performance-critic** - Performance bottleneck identification (Opus)
7. **architecture-critic** - Design pattern and architecture review (Opus)
8. **code-quality-critic** - Code quality and maintainability analysis (Opus)
9. **documentation-critic** - Documentation quality assessment (Opus)

#### Specialized (2)
10. **validation-orchestrator** - Multi-agent validation workflows (Sonnet)
11. **master-orchestrator** - Complex multi-phase orchestration (Sonnet)

#### Experimental (1)
12. **experiment-agent** - Testing new capabilities (Haiku)

### Cost Reference Table

| Model Tier | Input Cost | Output Cost | Typical Use Case | Example Cost |
|-----------|-----------|-------------|------------------|--------------|
| Haiku | $0.25/1M tokens | $1.25/1M tokens | 2000 in + 500 out | $0.0011 |
| Sonnet | $3.00/1M tokens | $15.00/1M tokens | 2000 in + 500 out | $0.0135 |
| Opus | $15.00/1M tokens | $75.00/1M tokens | 2000 in + 500 out | $0.0675 |

### File Structure Reference

```
~/.claude/
├── agents/
│   └── global/
│       ├── core/                    # Core agents
│       ├── specialized/             # Specialized agents
│       ├── critics/                 # Critics (Opus only)
│       ├── experimental/            # Experimental agents
│       └── .registry/               # Registry files
│           ├── agent_registry.json  # Main registry
│           ├── usage_stats.json     # Usage statistics
│           └── model_discipline.json # Discipline rules
├── lib/
│   ├── agent_registry.py            # Core registry (550 lines)
│   ├── agent_discovery.py           # Discovery system (350 lines)
│   ├── agent_registry_integration.py # Orchestrator helpers (250 lines)
│   ├── promote_agents.py            # Promotion script (350 lines)
│   ├── test_agent_registry.py       # Test suite (600 lines, 20 tests)
│   └── AGENT_REGISTRY_README.md     # This file
└── scripts/
    └── agent_analytics.py           # Analytics tool (400 lines)
```

---

## Contributing

### Adding New Agents

1. Create agent implementation
2. Register with appropriate metadata
3. Add comprehensive use cases
4. Set realistic cost/time estimates
5. Define quality range
6. Run tests
7. Update documentation

### Reporting Issues

Issues should be reported to the project maintainer with:
- Agent name and category
- Expected vs. actual behavior
- Registry file state (if relevant)
- Error messages and stack traces

### Testing

Run the test suite after changes:
```bash
cd ~/.claude/lib
python3 -m pytest test_agent_registry.py -v

# Should show: 20 passed
```

---

**Version History**

- **1.0.0** (Nov 3, 2025) - Initial release
  - 12 agents registered
  - Model discipline enforcement
  - Usage tracking and analytics
  - Discovery and recommendation system
  - 20 comprehensive tests

---

**Quick Links**

- [AgentRegistry API](#agentregistry)
- [AgentDiscovery API](#agentdiscovery)
- [Analytics Tool](#analytics--reporting)
- [Migration Guide](#migration-guide)
- [Troubleshooting](#troubleshooting)
