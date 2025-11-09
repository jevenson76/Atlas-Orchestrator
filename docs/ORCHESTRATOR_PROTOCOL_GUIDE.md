# Orchestrator Protocol Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Active (Phase 2C)
**Phase:** 2C - Orchestrator Protocol Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [OrchestratorProtocol Definition](#orchestratorprotocol-definition)
3. [Orchestrator Base Class](#orchestrator-base-class)
4. [SubAgent Configuration](#subagent-configuration)
5. [Execution Modes](#execution-modes)
6. [Factory Pattern Integration](#factory-pattern-integration)
7. [Protocol-Based Dependency Injection](#protocol-based-dependency-injection)
8. [Usage Patterns](#usage-patterns)
9. [Complete System Integration](#complete-system-integration)
10. [Best Practices](#best-practices)
11. [Examples](#examples)
12. [Troubleshooting](#troubleshooting)
13. [References](#references)

---

## Overview

The Orchestrator uses **Protocol-based Dependency Injection** for managing multi-agent workflows with flexible execution strategies and optional validator/critic integration.

### The Multi-Agent Orchestration Problem

**Before Protocol-Based DI:**
- Complex dependencies between orchestrators, validators, and critics
- Tight coupling made testing difficult
- Circular imports between validation and critic systems
- Hard to compose different orchestration strategies

**After Protocol-Based DI:**
- Clean separation via protocols
- Easy dependency injection
- No circular dependencies
- Composable orchestration strategies

### Architecture at a Glance

```
        protocols/
       /    |    \
      ↓     ↓     ↓
  validator critic orchestrator
      \     |     /
       ↓    ↓    ↓
    protocols/factory.py
    (runtime wiring)
```

---

## OrchestratorProtocol Definition

The `OrchestratorProtocol` defines the contract for orchestration operations.

### Protocol Interface

```python
from typing import Protocol, runtime_checkable, Dict, Any, Optional

@runtime_checkable
class OrchestratorProtocol(Protocol):
    """
    Abstract interface for orchestration operations.

    Implementations must provide workflow execution, agent coordination,
    and result aggregation capabilities.

    Example implementations:
    - orchestrator.Orchestrator (base class)
    - specialized_roles_orchestrator.SpecializedRolesOrchestrator
    - progressive_enhancement_orchestrator.ProgressiveEnhancementOrchestrator
    """

    def execute(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute orchestrated workflow.

        Args:
            input_data: Input data for orchestration

        Returns:
            Workflow results with metadata
        """
        ...

    async def execute_async(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute orchestrated workflow asynchronously.

        Args:
            input_data: Input data for orchestration

        Returns:
            Workflow results with metadata
        """
        ...

    def get_agent_results(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get results from all agents.

        Returns:
            Dictionary mapping agent names to their results
        """
        ...

    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics from all agents.

        Returns:
            Dictionary mapping agent names to their metrics
        """
        ...
```

### Supporting Enums

```python
from enum import Enum

class ExecutionMode(Enum):
    """Execution modes for agent orchestration."""
    SEQUENTIAL = "sequential"    # Run tasks one by one
    PARALLEL = "parallel"        # Run all tasks simultaneously
    ADAPTIVE = "adaptive"        # Choose based on dependencies
    ITERATIVE = "iterative"      # Run with refinement loops

class TaskStatus(Enum):
    """Status of an agent task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
```

---

## Orchestrator Base Class

The `Orchestrator` abstract base class provides the foundation for all orchestrator implementations.

### Base Class Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from orchestrator import ExecutionMode

class Orchestrator(ABC):
    """
    Base orchestrator for coordinating multiple agents.

    Provides framework for building complex multi-agent workflows
    with parallel execution, dependencies, and error handling.
    """

    def __init__(
        self,
        name: str = "Orchestrator",
        mode: ExecutionMode = ExecutionMode.ADAPTIVE,
        max_workers: int = 5,
        cost_tracker: Optional[CostTracker] = None,
        enable_logging: bool = True
    ):
        """
        Initialize orchestrator.

        Args:
            name: Name for this orchestrator
            mode: Execution mode (sequential, parallel, adaptive, iterative)
            max_workers: Max parallel workers
            cost_tracker: Shared cost tracker
            enable_logging: Enable execution logging
        """
        ...

    def add_agent(self, name: str, agent: SubAgent) -> 'Orchestrator':
        """
        Add a subagent to the orchestration.

        Args:
            name: Unique name for the agent
            agent: SubAgent instance

        Returns:
            Self for chaining
        """
        ...

    @abstractmethod
    def prepare_prompt(
        self,
        agent_name: str,
        initial_input: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> str:
        """
        Prepare prompt for a specific agent based on inputs and previous results.

        Must be implemented by subclasses.

        Args:
            agent_name: Name of the agent
            initial_input: Original input to orchestrator
            previous_results: Results from completed agents

        Returns:
            Prepared prompt string
        """
        pass

    @abstractmethod
    def process_result(
        self,
        agent_name: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and transform agent result.

        Must be implemented by subclasses.

        Args:
            agent_name: Name of the agent
            result: Raw result from agent

        Returns:
            Processed result
        """
        pass
```

### Creating Custom Orchestrators

To create a custom orchestrator, inherit from `Orchestrator` and implement the abstract methods:

```python
from orchestrator import Orchestrator, SubAgent, ExecutionMode

class MyCustomOrchestrator(Orchestrator):
    """Custom orchestrator for my specific workflow."""

    def __init__(self):
        super().__init__(
            name="MyCustomOrchestrator",
            mode=ExecutionMode.SEQUENTIAL
        )

    def prepare_prompt(
        self,
        agent_name: str,
        initial_input: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> str:
        """Prepare agent-specific prompts."""
        task = initial_input.get("task", "")

        # Include previous results as context
        context = ""
        if previous_results:
            context = "\n\nPrevious results:\n"
            for name, result in previous_results.items():
                context += f"- {name}: {result.get('summary', '')}\n"

        return f"Task: {task}\n\nYour role: {agent_name}{context}"

    def process_result(
        self,
        agent_name: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and transform results."""
        # Extract key information
        return {
            "agent": agent_name,
            "summary": result.get("content", "")[:200],
            "full_result": result
        }
```

---

## SubAgent Configuration

`SubAgent` extends `BaseAgent` with orchestration-specific capabilities.

### SubAgent Class

```python
from orchestrator import SubAgent

class SubAgent(BaseAgent):
    """
    Specialized agent with enhanced capabilities for orchestration.

    Extends BaseAgent with orchestration-specific features like
    dependencies, tools, and result processing.
    """

    def __init__(
        self,
        role: str,
        model: str = 'claude-sonnet-4-5-20250929',
        tools: Optional[List[str]] = None,
        dependencies: Optional[Set[str]] = None,
        required: bool = True,
        max_iterations: int = 1,
        fallback_handler: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize subagent with orchestration capabilities.

        Args:
            role: Agent's role/purpose
            model: Model to use
            tools: List of tools available to this agent
            dependencies: Set of agent names that must complete first
            required: Whether failure should stop orchestration
            max_iterations: Maximum refinement iterations (for iterative mode)
            fallback_handler: Function to call if agent fails
            **kwargs: Additional arguments for BaseAgent
        """
```

### Basic SubAgent Creation

```python
from orchestrator import SubAgent

# Simple agent with no dependencies
agent = SubAgent(
    role="researcher",
    model="claude-sonnet-4-5-20250929"
)

# Agent with specific model and tools
coder = SubAgent(
    role="Write Python code",
    model="claude-sonnet-4-5-20250929",
    tools=["code_execution", "file_operations"]
)

# Agent with dependencies (runs after researcher)
analyst = SubAgent(
    role="Analyze research findings",
    model="claude-sonnet-4-5-20250929",
    dependencies={"researcher"}  # Waits for researcher to complete
)
```

### SubAgent Properties

```python
# Task tracking
agent.status          # TaskStatus enum (PENDING, RUNNING, COMPLETED, etc.)
agent.result          # Result dictionary (set after execution)
agent.error           # Error message (if failed)
agent.start_time      # Execution start timestamp
agent.end_time        # Execution end timestamp
agent.iteration_count # Current iteration (for iterative mode)

# Configuration
agent.tools           # List of available tools
agent.dependencies    # Set of agent name dependencies
agent.required        # Whether agent is required for workflow success
agent.max_iterations  # Max refinement iterations
agent.fallback_handler # Custom fallback function

# Methods
agent.can_execute(completed_agents: Set[str]) -> bool  # Check if dependencies met
agent.get_duration() -> Optional[float]                 # Get execution duration
await agent.execute_async(prompt: str, context: Dict)   # Execute asynchronously
```

### Advanced SubAgent Configuration

```python
# Agent with custom fallback handler
def fallback_handler(input_data, previous_results):
    """Called if agent fails."""
    return {
        "status": "fallback_used",
        "message": "Using cached result"
    }

agent = SubAgent(
    role="data_processor",
    model="claude-haiku-4-20250514",
    required=False,              # Optional agent (failure won't stop workflow)
    max_iterations=3,            # Allow up to 3 refinement iterations
    fallback_handler=fallback_handler
)

# Agent with multiple dependencies
reviewer = SubAgent(
    role="Review code and tests",
    model="claude-opus-4-20250514",
    dependencies={"coder", "tester"},  # Must wait for both
    tools=["static_analysis", "security_scan"]
)
```

---

## Execution Modes

The orchestrator supports four execution modes for different workflow patterns.

### 1. Sequential Execution

Agents run one after another in order.

**Use When:**
- Tasks must run in specific order
- Each task depends on previous results
- Simple linear workflow

**Example:**
```python
from orchestrator import Orchestrator, SubAgent, ExecutionMode

class SequentialWorkflow(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.SEQUENTIAL)

        # Add agents in order
        self.add_agent("step1", SubAgent(role="Step 1", model="claude-haiku-4-20250514"))
        self.add_agent("step2", SubAgent(role="Step 2", model="claude-haiku-4-20250514"))
        self.add_agent("step3", SubAgent(role="Step 3", model="claude-sonnet-4-5-20250929"))

    # Implement abstract methods...

# Execute
workflow = SequentialWorkflow()
result = workflow.execute({"task": "Process data"})
```

**Execution Flow:**
```
step1 → step2 → step3
  ↓       ↓       ↓
 res1   res2   res3
```

### 2. Parallel Execution

All agents run concurrently using asyncio.

**Use When:**
- Tasks are independent
- Want to minimize total execution time
- No dependencies between agents

**Example:**
```python
class ParallelWorkflow(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.PARALLEL)

        # Add independent agents
        self.add_agent("worker1", SubAgent(role="Process chunk 1", model="claude-haiku-4-20250514"))
        self.add_agent("worker2", SubAgent(role="Process chunk 2", model="claude-haiku-4-20250514"))
        self.add_agent("worker3", SubAgent(role="Process chunk 3", model="claude-haiku-4-20250514"))

    # Implement abstract methods...

# Execute all agents in parallel
workflow = ParallelWorkflow()
result = await workflow.execute_async({"data": chunks})
```

**Execution Flow:**
```
worker1 ──┐
worker2 ──┼── (all run concurrently)
worker3 ──┘
```

**Performance:**
- Sequential: 3 agents × 10s = 30s total
- Parallel: max(10s, 10s, 10s) = 10s total
- **3x speedup**

### 3. Adaptive Execution

Agents selected dynamically based on dependencies. Runs ready agents in parallel.

**Use When:**
- Complex dependency graph
- Want to maximize parallelism
- Some tasks depend on others, but not all

**Example:**
```python
class AdaptiveWorkflow(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.ADAPTIVE)

        # Agent with no dependencies (runs first)
        self.add_agent("fetcher", SubAgent(
            role="Fetch data",
            model="claude-haiku-4-20250514"
        ))

        # Two agents depend on fetcher (run in parallel after fetcher)
        self.add_agent("analyzer1", SubAgent(
            role="Analyze data (security)",
            model="claude-sonnet-4-5-20250929",
            dependencies={"fetcher"}
        ))
        self.add_agent("analyzer2", SubAgent(
            role="Analyze data (performance)",
            model="claude-sonnet-4-5-20250929",
            dependencies={"fetcher"}
        ))

        # Final agent depends on both analyzers
        self.add_agent("reporter", SubAgent(
            role="Generate report",
            model="claude-sonnet-4-5-20250929",
            dependencies={"analyzer1", "analyzer2"}
        ))

    # Implement abstract methods...
```

**Execution Flow:**
```
       fetcher
          ↓
    ┌─────┴─────┐
    ↓           ↓
analyzer1  analyzer2  (parallel)
    └─────┬─────┘
          ↓
       reporter
```

**Deadlock Detection:**
The adaptive mode includes automatic deadlock detection. If dependencies cannot be satisfied, it will log an error and stop.

### 4. Iterative Execution

Agents run in refinement loops until quality threshold met.

**Use When:**
- Quality matters more than speed
- Want iterative refinement
- Need to improve results progressively

**Example:**
```python
class IterativeWorkflow(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.ITERATIVE)

        # Agent with multiple iterations
        self.add_agent("drafter", SubAgent(
            role="Create draft",
            model="claude-haiku-4-20250514",
            max_iterations=5  # Up to 5 refinement rounds
        ))

        self.add_agent("reviewer", SubAgent(
            role="Review quality",
            model="claude-sonnet-4-5-20250929",
            max_iterations=3
        ))

    def _should_refine(self, agent_name, current_result, previous_result):
        """Override to implement custom refinement logic."""
        # Check quality score
        quality = current_result.get("quality_score", 0)
        return quality < 90  # Keep refining until 90% quality

    # Implement other abstract methods...
```

**Execution Flow:**
```
drafter iteration 1 → check quality → ❌ < 90%
drafter iteration 2 → check quality → ❌ < 90%
drafter iteration 3 → check quality → ✅ >= 90% (stop)

Result: Best result from iteration 3
```

**Cost Trade-off:**
- Iteration 1 (Haiku): $0.001
- Iteration 2 (Haiku): $0.001
- Iteration 3 (Haiku): $0.001
- **Total:** $0.003 (3x cost for 90% quality vs 70%)

---

## Factory Pattern Integration

The `DependencyFactory` provides methods for creating orchestrators with proper dependency injection.

### Factory Methods for Orchestrators

```python
from protocols.factory import DependencyFactory

class DependencyFactory:
    """Factory for creating and wiring components with dependency injection."""

    @staticmethod
    def create_orchestrator(
        agents: List[SubAgent],
        mode: str = "sequential",
        validator: Optional[ValidationProtocol] = None,
        critic: Optional[CriticProtocol] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> OrchestratorProtocol:
        """
        Create orchestrator with optional validator/critic injection.

        Args:
            agents: List of SubAgent instances
            mode: Execution mode (sequential, parallel, adaptive, iterative)
            validator: Optional validator to inject
            critic: Optional critic to inject
            config: Optional configuration

        Returns:
            Configured orchestrator
        """
        from orchestrator import Orchestrator

        # Create orchestrator
        orch = Orchestrator(
            name=config.get("name", "Orchestrator"),
            mode=ExecutionMode[mode.upper()],
            max_workers=config.get("max_workers", 5)
        )

        # Add agents
        for agent in agents:
            orch.add_agent(agent.role, agent)

        # Inject dependencies
        if validator is not None and hasattr(orch, 'set_validator'):
            orch.set_validator(validator)

        if critic is not None and hasattr(orch, 'set_critic'):
            orch.set_critic(critic)

        return orch

    @staticmethod
    def create_complete_system(
        agents: List[SubAgent],
        mode: str = "sequential",
        config: Optional[Dict[str, Any]] = None
    ) -> Tuple[OrchestratorProtocol, ValidationProtocol, CriticProtocol]:
        """
        Create complete orchestration system with validator and critic.

        This is the recommended way to create a full system. It ensures
        all components are properly wired together.

        Args:
            agents: List of SubAgent instances
            mode: Execution mode
            config: Optional configuration for all components

        Returns:
            Tuple of (orchestrator, validator, critic) with dependencies wired

        Example:
            >>> from orchestrator import SubAgent
            >>> agents = [SubAgent(role="test", model="claude-haiku-4-20250514")]
            >>> orch, validator, critic = DependencyFactory.create_complete_system(agents)
        """
        # Create all components
        validator = DependencyFactory.create_validation_orchestrator(config=config)
        critic = DependencyFactory.create_critic_orchestrator(config=config)
        orchestrator = DependencyFactory.create_orchestrator(
            agents=agents,
            mode=mode,
            validator=validator,
            critic=critic,
            config=config
        )

        # Wire bidirectional dependencies
        validator.set_critic(critic)
        critic.set_validator(validator)

        return orchestrator, validator, critic
```

---

## Protocol-Based Dependency Injection

Orchestrators support dependency injection for validators and critics.

### Constructor Injection

```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Create dependencies first
validator = DependencyFactory.create_validation_orchestrator()
critic = DependencyFactory.create_critic_orchestrator()

# Create orchestrator with injected dependencies
agents = [SubAgent(role="test", model="claude-haiku-4-20250514")]
orch = DependencyFactory.create_orchestrator(
    agents=agents,
    validator=validator,
    critic=critic
)
```

### Setter Injection

```python
from orchestrator import MyCustomOrchestrator

# Create orchestrator
orch = MyCustomOrchestrator()

# Inject dependencies later
if hasattr(orch, 'set_validator'):
    orch.set_validator(validator)

if hasattr(orch, 'set_critic'):
    orch.set_critic(critic)
```

### Using Injected Dependencies

```python
class ValidationAwareOrchestrator(Orchestrator):
    """Orchestrator that uses validator and critic."""

    def __init__(self):
        super().__init__(mode=ExecutionMode.SEQUENTIAL)
        self._validator = None
        self._critic = None

    def set_validator(self, validator: ValidationProtocol) -> None:
        """Inject validator dependency."""
        if not isinstance(validator, ValidationProtocol):
            raise TypeError("Expected ValidationProtocol")
        self._validator = validator

    def set_critic(self, critic: CriticProtocol) -> None:
        """Inject critic dependency."""
        if not isinstance(critic, CriticProtocol):
            raise TypeError("Expected CriticProtocol")
        self._critic = critic

    def process_result(self, agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process result with optional validation and critique."""
        processed = {"agent": agent_name, "result": result}

        # Validate if validator available
        if self._validator is not None:
            validation_results = self._validator.validate(
                data=result.get("output", ""),
                config={"level": "quick"}
            )
            processed["validation"] = validation_results

        # Critique if critic available
        if self._critic is not None:
            critique_results = self._critic.critique(
                data=result.get("output", ""),
                context={"agent": agent_name}
            )
            processed["critique"] = critique_results

        return processed
```

---

## Usage Patterns

### Pattern 1: Basic Orchestration (Direct Instantiation)

```python
from orchestrator import Orchestrator, SubAgent, ExecutionMode

class SimpleOrchestrator(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.SEQUENTIAL)

        self.add_agent("agent1", SubAgent(
            role="First task",
            model="claude-haiku-4-20250514"
        ))
        self.add_agent("agent2", SubAgent(
            role="Second task",
            model="claude-sonnet-4-5-20250929"
        ))

    def prepare_prompt(self, agent_name, initial_input, previous_results):
        return f"Task: {initial_input.get('task')}"

    def process_result(self, agent_name, result):
        return {"agent": agent_name, "output": result}

# Use
orch = SimpleOrchestrator()
result = orch.execute({"task": "Process data"})
```

### Pattern 2: Factory Pattern (Recommended)

```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Define agents
agents = [
    SubAgent(role="researcher", model="claude-sonnet-4-5-20250929"),
    SubAgent(role="analyst", model="claude-sonnet-4-5-20250929"),
]

# Create via factory
orch = DependencyFactory.create_orchestrator(
    agents=agents,
    mode="sequential"
)

# Execute
result = orch.execute({"task": "Research topic"})
```

### Pattern 3: Complete System with Validation

```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Define workflow
agents = [
    SubAgent(role="coder", model="claude-sonnet-4-5-20250929"),
    SubAgent(role="tester", model="claude-sonnet-4-5-20250929"),
]

# Create complete system (orchestrator + validator + critic)
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="sequential",
    config={
        "validation_level": "thorough",
        "enable_critics": True
    }
)

# Orchestrator automatically uses validator and critic
result = orch.execute({"task": "Build feature"})
```

### Pattern 4: Parallel Processing

```python
# Create independent workers
workers = [
    SubAgent(role=f"Worker {i}", model="claude-haiku-4-20250514")
    for i in range(5)
]

# Create parallel orchestrator
orch = DependencyFactory.create_orchestrator(
    agents=workers,
    mode="parallel"
)

# Execute all workers concurrently
result = await orch.execute_async({"data": large_dataset})
```

### Pattern 5: Dependency Graph

```python
# Create agents with dependencies
fetcher = SubAgent(role="Fetch data", model="claude-haiku-4-20250514")

# These depend on fetcher
analyzer1 = SubAgent(
    role="Security analysis",
    model="claude-sonnet-4-5-20250929",
    dependencies={"Fetch data"}
)
analyzer2 = SubAgent(
    role="Performance analysis",
    model="claude-sonnet-4-5-20250929",
    dependencies={"Fetch data"}
)

# This depends on both analyzers
reporter = SubAgent(
    role="Generate report",
    model="claude-opus-4-20250514",
    dependencies={"Security analysis", "Performance analysis"}
)

# Create adaptive orchestrator
orch = DependencyFactory.create_orchestrator(
    agents=[fetcher, analyzer1, analyzer2, reporter],
    mode="adaptive"
)

# Executes: fetcher → (analyzer1 || analyzer2) → reporter
result = await orch.execute_async({"target": "api.example.com"})
```

---

## Complete System Integration

### Orchestrator + Validator + Critic

The `create_complete_system` factory method creates a fully integrated system.

```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Define multi-stage workflow
agents = [
    SubAgent(role="designer", model="claude-opus-4-20250514"),
    SubAgent(role="implementer", model="claude-sonnet-4-5-20250929"),
    SubAgent(role="tester", model="claude-sonnet-4-5-20250929"),
]

# Create complete system
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="sequential",
    config={
        "validation_level": "thorough",
        "enable_critics": True,
        "max_critics": 3,
        "quality_threshold": 90
    }
)

# Execute workflow
result = orch.execute({
    "task": "Build user authentication system",
    "requirements": [
        "OAuth2 support",
        "Password hashing",
        "Session management"
    ]
})

# Result includes orchestration + validation + critique
print(result["results"])           # Agent results
print(result["metadata"])          # Execution metadata
print(result["validation"])        # Validation results (if validator used)
print(result["critique"])          # Critique results (if critic used)
```

### System Architecture

```
┌─────────────────────────────────────────────────┐
│            DependencyFactory                    │
│  (creates and wires all components)             │
└────────────┬──────────┬─────────────────────────┘
             ↓          ↓
    ┌────────────────────────┐
    │   Orchestrator         │
    │  - Coordinates agents  │
    │  - Manages execution   │
    └───┬────────────────┬───┘
        ↓                ↓
┌──────────────┐  ┌──────────────┐
│  Validator   │  │   Critic     │
│  - Validates │  │ - Critiques  │
│    outputs   │  │   quality    │
└──────────────┘  └──────────────┘
```

### Accessing Components Independently

```python
# Create complete system
orch, validator, critic = DependencyFactory.create_complete_system(agents=agents)

# Use orchestrator
orch_result = orch.execute({"task": "Build feature"})

# Use validator directly
validation_result = validator.validate(
    data=code_string,
    config={"level": "thorough"}
)

# Use critic directly
critique_result = critic.critique(
    data=code_string,
    context={"file": "app.py"}
)

# All components are wired together
assert orch._validator is validator  # Orchestrator has validator
assert orch._critic is critic        # Orchestrator has critic
assert validator._critic is critic   # Validator has critic
assert critic._validator is validator # Critic has validator
```

---

## Best Practices

### 1. Use Factory for Complex Systems

❌ **Don't:**
```python
orch = MyOrchestrator()
validator = ValidationOrchestrator()
critic = CriticOrchestrator()
# Manual wiring - error-prone, verbose
orch.validator = validator
orch.critic = critic
```

✅ **Do:**
```python
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="sequential"
)
# Factory handles wiring automatically
```

### 2. Choose Appropriate Execution Mode

| Mode | Use When | Example |
|------|----------|---------|
| **Sequential** | Tasks must run in order | Pipeline: fetch → process → store |
| **Parallel** | Independent tasks, time-sensitive | Batch processing, data parallel |
| **Adaptive** | Complex dependencies | DAG: fetch → (analyze1 ‖ analyze2) → merge |
| **Iterative** | Quality-focused, refinement | Draft → review → refine loop |

### 3. Set Proper Dependencies

❌ **Don't:**
```python
# Missing dependency - reviewer might run before coder
coder = SubAgent(role="coder", model="claude-sonnet-4-5-20250929")
reviewer = SubAgent(role="reviewer", model="claude-opus-4-20250514")
```

✅ **Do:**
```python
coder = SubAgent(role="coder", model="claude-sonnet-4-5-20250929")
reviewer = SubAgent(
    role="reviewer",
    model="claude-opus-4-20250514",
    dependencies={"coder"}  # Explicit dependency
)
```

### 4. Handle Failures Gracefully

```python
# Optional agents with fallback
agent = SubAgent(
    role="optional_task",
    model="claude-haiku-4-20250514",
    required=False,  # Failure won't stop workflow
    fallback_handler=lambda input, results: {"status": "skipped"}
)
```

### 5. Monitor Costs and Performance

```python
# Use shared cost tracker
from agent_system import CostTracker

tracker = CostTracker()
orch = Orchestrator(
    mode=ExecutionMode.PARALLEL,
    cost_tracker=tracker,
    enable_logging=True
)

# After execution
result = orch.execute(input_data)
print(f"Total cost: ${result['metadata']['total_cost']:.4f}")
print(f"Duration: {result['metadata']['total_duration']:.2f}s")
print(f"Agents run: {result['metadata']['agents_run']}")
```

### 6. Implement Custom Refinement Logic

```python
class QualityAwareOrchestrator(Orchestrator):
    def __init__(self):
        super().__init__(mode=ExecutionMode.ITERATIVE)

    def _should_refine(self, agent_name, current_result, previous_result):
        """Custom refinement logic."""
        # Get quality score
        quality = current_result.get("quality_score", 0)

        # Check improvement
        if previous_result:
            prev_quality = previous_result.get("quality_score", 0)
            improvement = quality - prev_quality

            # Stop if quality high enough or no improvement
            if quality >= 95 or improvement < 1:
                return False

        # Continue refining
        return quality < 95
```

### 7. Use Type Hints

```python
from typing import Dict, List, Any, Optional
from protocols import OrchestratorProtocol, ValidationProtocol

def process_with_orchestrator(
    orchestrator: OrchestratorProtocol,
    tasks: List[Dict[str, Any]],
    validator: Optional[ValidationProtocol] = None
) -> List[Dict[str, Any]]:
    """
    Process tasks with orchestrator.

    Type hints enable:
    - IDE autocomplete
    - Static type checking
    - Better documentation
    """
    results = []
    for task in tasks:
        result = orchestrator.execute(task)
        results.append(result)
    return results
```

---

## Examples

### Example 1: Research Pipeline

```python
from protocols.factory import DependencyFactory
from orchestrator import SubAgent

# Define research workflow
agents = [
    SubAgent(
        role="researcher",
        model="claude-sonnet-4-5-20250929"
    ),
    SubAgent(
        role="analyst",
        model="claude-sonnet-4-5-20250929",
        dependencies={"researcher"}
    ),
    SubAgent(
        role="writer",
        model="claude-sonnet-4-5-20250929",
        dependencies={"analyst"}
    )
]

# Create with validation
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="sequential"
)

# Execute research
result = orch.execute({
    "task": "Research AI safety best practices",
    "requirements": [
        "Focus on LLM-specific concerns",
        "Include recent developments",
        "Provide actionable recommendations"
    ]
})

# Access results
research = result["results"]["researcher"]
analysis = result["results"]["analyst"]
report = result["results"]["writer"]
```

### Example 2: Parallel Data Processing

```python
# Create data processing workers
workers = [
    SubAgent(
        role=f"Process chunk {i}",
        model="claude-haiku-4-20250514"
    )
    for i in range(10)
]

# Add merger that depends on all workers
merger = SubAgent(
    role="Merge results",
    model="claude-sonnet-4-5-20250929",
    dependencies={f"Process chunk {i}" for i in range(10)}
)

workers.append(merger)

# Create adaptive orchestrator (parallel workers → sequential merger)
orch = DependencyFactory.create_orchestrator(
    agents=workers,
    mode="adaptive"
)

# Process large dataset
result = await orch.execute_async({
    "data": large_dataset,
    "chunk_size": 1000
})

# Performance: 10 workers in parallel = 10x speedup
# Cost: 10 × Haiku + 1 × Sonnet = $0.0025 + $0.003 = $0.0055
```

### Example 3: Iterative Code Generation

```python
# Define iterative workflow
agents = [
    SubAgent(
        role="code_generator",
        model="claude-sonnet-4-5-20250929",
        max_iterations=5  # Up to 5 refinement rounds
    ),
    SubAgent(
        role="code_reviewer",
        model="claude-opus-4-20250514",
        max_iterations=3,
        dependencies={"code_generator"}
    )
]

# Create with validation
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="iterative",
    config={
        "quality_threshold": 95,
        "validation_level": "thorough"
    }
)

# Custom refinement logic
class CodeOrchestrator(Orchestrator):
    def _should_refine(self, agent_name, current_result, previous_result):
        """Refine until tests pass and quality high."""
        tests_pass = current_result.get("tests_pass", False)
        quality = current_result.get("quality_score", 0)

        return not tests_pass or quality < 95

# Generate code with iterative refinement
result = orch.execute({
    "task": "Implement binary search tree",
    "requirements": [
        "Include insert, delete, search methods",
        "Handle edge cases",
        "Include comprehensive tests"
    ]
})

# Iterations:
# Round 1: Basic implementation (quality 70%) → refine
# Round 2: Add edge cases (quality 85%) → refine
# Round 3: Optimize performance (quality 92%) → refine
# Round 4: Complete tests (quality 96%, tests pass) → accept
```

### Example 4: Multi-Stage Software Development

```python
# Define full development workflow
agents = [
    # Stage 1: Design
    SubAgent(
        role="architect",
        model="claude-opus-4-20250514",
        tools=["architecture_diagram", "api_design"]
    ),

    # Stage 2: Implementation (parallel)
    SubAgent(
        role="backend_dev",
        model="claude-sonnet-4-5-20250929",
        dependencies={"architect"},
        tools=["code_generation", "api_implementation"]
    ),
    SubAgent(
        role="frontend_dev",
        model="claude-sonnet-4-5-20250929",
        dependencies={"architect"},
        tools=["code_generation", "ui_implementation"]
    ),

    # Stage 3: Testing (parallel)
    SubAgent(
        role="backend_tester",
        model="claude-sonnet-4-5-20250929",
        dependencies={"backend_dev"},
        tools=["test_generation", "test_execution"]
    ),
    SubAgent(
        role="frontend_tester",
        model="claude-sonnet-4-5-20250929",
        dependencies={"frontend_dev"},
        tools=["test_generation", "test_execution"]
    ),

    # Stage 4: Review
    SubAgent(
        role="code_reviewer",
        model="claude-opus-4-20250514",
        dependencies={"backend_tester", "frontend_tester"},
        tools=["static_analysis", "security_scan"]
    )
]

# Create complete system
orch, validator, critic = DependencyFactory.create_complete_system(
    agents=agents,
    mode="adaptive",
    config={
        "validation_level": "thorough",
        "enable_critics": True,
        "max_critics": 5
    }
)

# Execute full workflow
result = orch.execute({
    "task": "Build e-commerce checkout system",
    "requirements": [
        "Payment processing",
        "Inventory management",
        "Order confirmation",
        "Email notifications"
    ]
})

# Execution flow:
# architect
#    ↓
# ┌──┴──┐
# backend frontend (parallel)
# ↓      ↓
# ┌──────┴──────┐
# backend_test frontend_test (parallel)
# └──────┬──────┘
#        ↓
#    reviewer
```

### Example 5: A/B Testing with Multiple Orchestrators

```python
# Create two different orchestration strategies
agents_fast = [
    SubAgent(role="worker", model="claude-haiku-4-20250514")
]

agents_quality = [
    SubAgent(role="drafter", model="claude-sonnet-4-5-20250929"),
    SubAgent(role="reviewer", model="claude-opus-4-20250514", dependencies={"drafter"})
]

# Strategy A: Fast (single Haiku agent)
orch_a = DependencyFactory.create_orchestrator(
    agents=agents_fast,
    mode="sequential"
)

# Strategy B: Quality (Sonnet + Opus review)
orch_b = DependencyFactory.create_orchestrator(
    agents=agents_quality,
    mode="sequential"
)

# Run both
task = {"task": "Summarize document"}

result_a = orch_a.execute(task)
result_b = orch_b.execute(task)

# Compare
print(f"Strategy A: ${result_a['metadata']['total_cost']:.4f}, {result_a['metadata']['total_duration']:.2f}s")
print(f"Strategy B: ${result_b['metadata']['total_cost']:.4f}, {result_b['metadata']['total_duration']:.2f}s")

# Typical results:
# Strategy A: $0.0001, 2.5s (fast, lower quality)
# Strategy B: $0.0200, 8.0s (slower, higher quality)
```

---

## Troubleshooting

### Issue: "Orchestrator has no attribute 'set_validator'"

**Cause:** Your orchestrator doesn't support dependency injection yet.

**Solution:** Use factory pattern or implement setter methods:

```python
# Option 1: Use factory (recommended)
orch = DependencyFactory.create_orchestrator(
    agents=agents,
    validator=validator
)

# Option 2: Implement setter in your orchestrator
class MyOrchestrator(Orchestrator):
    def set_validator(self, validator: ValidationProtocol) -> None:
        """Inject validator dependency."""
        if not isinstance(validator, ValidationProtocol):
            raise TypeError("Expected ValidationProtocol")
        self._validator = validator
```

### Issue: "ExecutionMode not found"

**Cause:** Missing import.

**Solution:** Import ExecutionMode enum:

```python
from orchestrator import ExecutionMode

orch = Orchestrator(mode=ExecutionMode.SEQUENTIAL)
```

### Issue: "Circular import detected"

**Cause:** Modules importing from each other instead of from protocols.

**Solution:** Use protocol imports:

```python
# ❌ Wrong
from critic_orchestrator import CriticOrchestrator

# ✅ Correct
from protocols import CriticProtocol
```

### Issue: "Deadlock detected! Pending agents cannot execute"

**Cause:** Circular dependencies or unsatisfiable dependency graph.

**Solution:** Check agent dependencies:

```python
# ❌ Wrong - circular dependency
agent_a = SubAgent(role="A", dependencies={"B"})
agent_b = SubAgent(role="B", dependencies={"A"})

# ✅ Correct - linear dependency
agent_a = SubAgent(role="A")
agent_b = SubAgent(role="B", dependencies={"A"})
```

### Issue: "Agent execution failed but workflow continued"

**Cause:** Agent marked as `required=False`.

**Solution:** Set `required=True` for critical agents:

```python
critical_agent = SubAgent(
    role="critical_task",
    model="claude-sonnet-4-5-20250929",
    required=True  # Workflow stops if this fails
)
```

### Issue: "Iterative mode never stops refining"

**Cause:** `_should_refine()` always returns True.

**Solution:** Implement proper termination logic:

```python
def _should_refine(self, agent_name, current_result, previous_result):
    """Stop after max iterations or quality threshold."""
    quality = current_result.get("quality_score", 0)
    iteration = current_result.get("iteration", 0)

    # Stop if quality good enough or max iterations reached
    return quality < 90 and iteration < 5
```

### Issue: "TypeError: Expected OrchestratorProtocol, got MyOrchestrator"

**Cause:** Your orchestrator doesn't implement required protocol methods.

**Solution:** Ensure your orchestrator implements all protocol methods:

```python
from protocols import OrchestratorProtocol

class MyOrchestrator:
    """Must implement all OrchestratorProtocol methods."""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Required by protocol."""
        ...

    async def execute_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Required by protocol."""
        ...

    def get_agent_results(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Required by protocol."""
        ...

    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Required by protocol."""
        ...

# Verify protocol conformance
assert isinstance(MyOrchestrator(), OrchestratorProtocol)
```

---

## References

### Related Documentation

- **ADR-004:** Protocol-Based Dependency Injection
  - `/home/jevenson/.claude/lib/docs/adr/ADR-004-protocol-based-dependency-injection.md`

- **PROTOCOLS.md:** Complete protocol guide
  - `/home/jevenson/.claude/lib/docs/PROTOCOLS.md`

- **MIGRATION_GUIDE_PHASE_2B.md:** Migration instructions
  - `/home/jevenson/.claude/lib/docs/MIGRATION_GUIDE_PHASE_2B.md`

- **CURRENT_ARCHITECTURE.md:** System architecture
  - `/home/jevenson/.claude/lib/docs/CURRENT_ARCHITECTURE.md`

### Source Files

- **orchestrator.py:** Base orchestrator implementation
  - `/home/jevenson/.claude/lib/orchestrator.py`

- **protocols/__init__.py:** Protocol definitions
  - `/home/jevenson/.claude/lib/protocols/__init__.py`

- **protocols/factory.py:** Dependency injection factory
  - `/home/jevenson/.claude/lib/protocols/factory.py`

### Examples

- **Test Suite:** Orchestrator tests
  - `/home/jevenson/.claude/lib/tests/test_orchestrator.py`

- **Integration Tests:** Complete system tests
  - `/home/jevenson/.claude/lib/tests/test_integration.py`

---

## Version History

| Version | Date       | Changes                              | Author                |
|---------|------------|--------------------------------------|-----------------------|
| 1.0.0   | 2025-11-09 | Initial orchestrator protocol guide  | Documentation Expert  |

---

**Status:** ✅ Complete (Phase 2C)
**Last Updated:** 2025-11-09
**Next Review:** After Phase 2C implementation

---

**For Questions or Contributions:**
- Review ADR-004 for architectural rationale
- Check PROTOCOLS.md for protocol details
- See MIGRATION_GUIDE for upgrade instructions
- Consult examples in tests directory
