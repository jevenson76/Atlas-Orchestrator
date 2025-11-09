"""
Orchestrator for coordinating multiple AI agents in complex workflows.

Provides base orchestrator class and utilities for building
multi-agent systems with parallel execution and error handling.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from .agent_system import BaseAgent, CostTracker
except ImportError:
    from agent_system import BaseAgent, CostTracker

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution modes for agent tasks."""
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


class SubAgent(BaseAgent):
    """
    Specialized agent with enhanced capabilities for orchestration.

    Extends BaseAgent with orchestration-specific features like
    dependencies, tools, and result processing.
    """

    def __init__(self,
                 role: str,
                 model: str = 'claude-3-5-sonnet-20241022',
                 tools: Optional[List[str]] = None,
                 dependencies: Optional[Set[str]] = None,
                 required: bool = True,
                 max_iterations: int = 1,
                 fallback_handler: Optional[Callable] = None,
                 **kwargs):
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
        super().__init__(role=role, model=model, **kwargs)

        self.tools = tools or []
        self.dependencies = dependencies or set()
        self.required = required
        self.max_iterations = max_iterations
        self.fallback_handler = fallback_handler

        # Task tracking
        self.status = TaskStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.iteration_count = 0

    def can_execute(self, completed_agents: Set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return self.dependencies.issubset(completed_agents)

    def get_duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    async def execute_async(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute agent asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.call, prompt, context)


class Orchestrator(ABC):
    """
    Base orchestrator for coordinating multiple agents.

    Provides framework for building complex multi-agent workflows
    with parallel execution, dependencies, and error handling.
    """

    def __init__(self,
                 name: str = "Orchestrator",
                 mode: ExecutionMode = ExecutionMode.ADAPTIVE,
                 max_workers: int = 5,
                 cost_tracker: Optional[CostTracker] = None,
                 enable_logging: bool = True):
        """
        Initialize orchestrator.

        Args:
            name: Name for this orchestrator
            mode: Execution mode
            max_workers: Max parallel workers
            cost_tracker: Shared cost tracker
            enable_logging: Enable execution logging
        """
        self.name = name
        self.mode = mode
        self.max_workers = max_workers
        self.cost_tracker = cost_tracker or CostTracker()
        self.enable_logging = enable_logging

        self.subagents: Dict[str, SubAgent] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.total_duration: float = 0.0

        if enable_logging:
            logger.info(f"Orchestrator '{name}' initialized with mode: {mode.value}")

    def add_agent(self, name: str, agent: SubAgent) -> 'Orchestrator':
        """
        Add a subagent to the orchestration.

        Args:
            name: Unique name for the agent
            agent: SubAgent instance

        Returns:
            Self for chaining
        """
        self.subagents[name] = agent
        logger.debug(f"Added agent '{name}' with dependencies: {agent.dependencies}")
        return self

    @abstractmethod
    def prepare_prompt(self, agent_name: str, initial_input: Dict[str, Any],
                      previous_results: Dict[str, Any]) -> str:
        """
        Prepare prompt for a specific agent based on inputs and previous results.

        Args:
            agent_name: Name of the agent
            initial_input: Original input to orchestrator
            previous_results: Results from completed agents

        Returns:
            Prepared prompt string
        """
        pass

    @abstractmethod
    def process_result(self, agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and transform agent result.

        Args:
            agent_name: Name of the agent
            result: Raw result from agent

        Returns:
            Processed result
        """
        pass

    async def execute_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute orchestration asynchronously.

        Args:
            input_data: Input data for orchestration

        Returns:
            Combined results from all agents
        """
        start_time = time.time()
        self._reset_execution_state()

        try:
            if self.mode == ExecutionMode.SEQUENTIAL:
                results = await self._execute_sequential_async(input_data)
            elif self.mode == ExecutionMode.PARALLEL:
                results = await self._execute_parallel_async(input_data)
            elif self.mode == ExecutionMode.ADAPTIVE:
                results = await self._execute_adaptive_async(input_data)
            elif self.mode == ExecutionMode.ITERATIVE:
                results = await self._execute_iterative_async(input_data)
            else:
                raise ValueError(f"Unknown execution mode: {self.mode}")

            self.total_duration = time.time() - start_time
            return self._compile_results(results, input_data)

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            self.total_duration = time.time() - start_time
            return {
                'error': str(e),
                'partial_results': {},
                'metadata': self._get_metadata()
            }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute orchestration synchronously.

        Args:
            input_data: Input data for orchestration

        Returns:
            Combined results from all agents
        """
        return asyncio.run(self.execute_async(input_data))

    async def _execute_sequential_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents sequentially."""
        results = {}
        completed = set()

        for name, agent in self.subagents.items():
            if not agent.can_execute(completed):
                logger.warning(f"Skipping {name}: dependencies not met")
                agent.status = TaskStatus.SKIPPED
                continue

            result = await self._run_agent_async(name, agent, input_data, results)
            if result:
                results[name] = result
                completed.add(name)
            elif agent.required:
                logger.error(f"Required agent {name} failed, stopping execution")
                break

        return results

    async def _execute_parallel_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all agents in parallel."""
        tasks = []
        for name, agent in self.subagents.items():
            task = asyncio.create_task(
                self._run_agent_async(name, agent, input_data, {})
            )
            tasks.append((name, task))

        results = {}
        for name, task in tasks:
            try:
                result = await task
                if result:
                    results[name] = result
            except Exception as e:
                logger.error(f"Agent {name} failed in parallel execution: {e}")
                if self.subagents[name].required:
                    # Cancel remaining tasks if required agent failed
                    for _, remaining_task in tasks:
                        if not remaining_task.done():
                            remaining_task.cancel()
                    break

        return results

    async def _execute_adaptive_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents adaptively based on dependencies."""
        results = {}
        completed = set()
        pending = set(self.subagents.keys())

        while pending:
            # Find ready agents
            ready = {
                name for name in pending
                if self.subagents[name].can_execute(completed)
            }

            if not ready:
                logger.error(f"Deadlock detected! Pending: {pending}, Completed: {completed}")
                break

            # Execute ready agents in parallel
            tasks = []
            for name in ready:
                agent = self.subagents[name]
                task = asyncio.create_task(
                    self._run_agent_async(name, agent, input_data, results)
                )
                tasks.append((name, task))
                pending.remove(name)

            # Wait for tasks to complete
            for name, task in tasks:
                try:
                    result = await task
                    if result:
                        results[name] = result
                        completed.add(name)
                except Exception as e:
                    logger.error(f"Agent {name} failed: {e}")
                    if self.subagents[name].required:
                        return results  # Stop if required agent failed

        return results

    async def _execute_iterative_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents with iterative refinement."""
        results = {}

        for name, agent in self.subagents.items():
            best_result = None

            for iteration in range(agent.max_iterations):
                agent.iteration_count = iteration + 1

                # Prepare context with previous iteration result
                context = {
                    'iteration': iteration + 1,
                    'previous_result': best_result,
                    'refinement_needed': iteration > 0
                }

                result = await self._run_agent_async(
                    name, agent, input_data, results, context
                )

                if result:
                    # Check if refinement improved the result
                    if self._should_refine(name, result, best_result):
                        best_result = result
                        logger.info(f"Agent {name} iteration {iteration + 1} improved result")
                    else:
                        logger.info(f"Agent {name} converged after {iteration + 1} iterations")
                        break
                else:
                    break

            if best_result:
                results[name] = best_result

        return results

    async def _run_agent_async(self, name: str, agent: SubAgent,
                               input_data: Dict[str, Any],
                               previous_results: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Run a single agent asynchronously."""
        agent.status = TaskStatus.RUNNING
        agent.start_time = datetime.now()

        try:
            # Prepare prompt
            prompt = self.prepare_prompt(name, input_data, previous_results)

            # Add iteration context if provided
            if context:
                prompt += f"\n\nIteration context: {context}"

            # Execute agent
            logger.info(f"Executing agent '{name}'")
            result = await agent.execute_async(prompt, context)

            if result.get('success'):
                agent.status = TaskStatus.COMPLETED
                agent.result = self.process_result(name, result)
                agent.end_time = datetime.now()

                self._log_execution(name, agent, success=True)
                return agent.result
            else:
                raise Exception(result.get('error', 'Unknown error'))

        except Exception as e:
            agent.status = TaskStatus.FAILED
            agent.error = str(e)
            agent.end_time = datetime.now()

            logger.error(f"Agent {name} failed: {e}")
            self._log_execution(name, agent, success=False)

            # Try fallback if available
            if agent.fallback_handler:
                try:
                    logger.info(f"Attempting fallback for {name}")
                    fallback_result = agent.fallback_handler(input_data, previous_results)
                    agent.result = fallback_result
                    return fallback_result
                except Exception as fb_error:
                    logger.error(f"Fallback also failed for {name}: {fb_error}")

            return None

    def _should_refine(self, agent_name: str, current_result: Dict[str, Any],
                      previous_result: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if refinement should continue.

        Override this method to implement custom refinement logic.
        """
        # Default: always refine until max iterations
        return True

    def _reset_execution_state(self):
        """Reset execution state for all agents."""
        for agent in self.subagents.values():
            agent.status = TaskStatus.PENDING
            agent.result = None
            agent.error = None
            agent.start_time = None
            agent.end_time = None
            agent.iteration_count = 0

        self.execution_log.clear()
        self.total_duration = 0.0

    def _log_execution(self, name: str, agent: SubAgent, success: bool):
        """Log execution details."""
        if self.enable_logging:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'agent': name,
                'status': agent.status.value,
                'success': success,
                'duration': agent.get_duration(),
                'model': agent.model,
                'cost': agent.cost_tracker.get_agent_cost(agent.agent_id),
                'error': agent.error,
                'iteration': agent.iteration_count if agent.iteration_count > 0 else None
            }
            self.execution_log.append(log_entry)

    def _compile_results(self, results: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile final results with metadata."""
        return {
            'input': input_data,
            'results': results,
            'metadata': self._get_metadata()
        }

    def _get_metadata(self) -> Dict[str, Any]:
        """Get execution metadata."""
        total_cost = sum(
            agent.cost_tracker.get_agent_cost(agent.agent_id)
            for agent in self.subagents.values()
        )

        successful_agents = [
            name for name, agent in self.subagents.items()
            if agent.status == TaskStatus.COMPLETED
        ]

        failed_agents = [
            name for name, agent in self.subagents.items()
            if agent.status == TaskStatus.FAILED
        ]

        return {
            'orchestrator': self.name,
            'mode': self.mode.value,
            'total_duration': round(self.total_duration, 2),
            'total_cost': round(total_cost, 6),
            'agents_run': len(successful_agents) + len(failed_agents),
            'agents_succeeded': len(successful_agents),
            'agents_failed': len(failed_agents),
            'successful_agents': successful_agents,
            'failed_agents': failed_agents,
            'execution_log': self.execution_log,
            'cost_report': self.cost_tracker.get_report()
        }

    def get_agent_results(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get results from all agents."""
        return {
            name: agent.result
            for name, agent in self.subagents.items()
        }

    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all agents."""
        return {
            name: agent.get_metrics()
            for name, agent in self.subagents.items()
        }