#!/usr/bin/env python3
"""Test script to verify agent_system and orchestrator components."""

import sys
sys.path.insert(0, '/home/jevenson/.claude/lib')

# Test imports
from agent_system import BaseAgent, CircuitBreaker, CostTracker, ExponentialBackoff, ModelPricing, AgentMetrics
from orchestrator import Orchestrator, SubAgent, ExecutionMode, TaskStatus

# Test agent_system components
print("Testing agent_system.py components...")
print("=" * 50)

agent = BaseAgent('Test Agent')
print(f'✓ BaseAgent created: {agent.role}')

tracker = CostTracker(daily_budget=10.0)
print(f'✓ CostTracker created with budget: ${tracker.daily_budget}')

breaker = CircuitBreaker()
print(f'✓ CircuitBreaker created: state={breaker.state.value}')

backoff = ExponentialBackoff()
print(f'✓ ExponentialBackoff created: base_delay={backoff.base_delay}s')

metrics = AgentMetrics()
print(f'✓ AgentMetrics created: {metrics.total_calls} calls')

cost = ModelPricing.calculate_cost('claude-3-5-haiku-20241022', 1000, 500)
print(f'✓ ModelPricing calculated: ${cost} for 1500 tokens')

# Test orchestrator components
print("\nTesting orchestrator.py components...")
print("=" * 50)

subagent = SubAgent('Test SubAgent')
print(f'✓ SubAgent created: {subagent.role}')

print(f'✓ SubAgent status: {subagent.status.value}')
print(f'✓ SubAgent dependencies: {subagent.dependencies}')

print(f'✓ ExecutionMode values: {[m.value for m in ExecutionMode]}')
print(f'✓ TaskStatus values: {[s.value for s in TaskStatus]}')

# Test creating concrete orchestrator
class TestOrchestrator(Orchestrator):
    def prepare_prompt(self, agent_name, initial_input, previous_results):
        return f"Test prompt for {agent_name}"

    def process_result(self, agent_name, result):
        return result

orchestrator = TestOrchestrator(name="Test", mode=ExecutionMode.ADAPTIVE)
print(f'✓ Orchestrator created: {orchestrator.name} with mode {orchestrator.mode.value}')

print('\n✅ All components working correctly!')
print(f'✅ Total classes tested: 10')