#!/usr/bin/env python3
"""
Test script to verify the multi-agent library works correctly.
"""

import sys
import os
sys.path.insert(0, '/home/jevenson/.claude/lib')

# Test imports
print("Testing imports...")
try:
    from agent_system import BaseAgent, CircuitBreaker, CostTracker, ExponentialBackoff
    from orchestrator import Orchestrator, ExecutionMode, SubAgent
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test BaseAgent creation
print("\nTesting BaseAgent...")
try:
    agent = BaseAgent(
        role="Test Agent",
        model="claude-3-5-sonnet-20241022"
    )
    print(f"✅ BaseAgent created: {agent.role}")
except Exception as e:
    print(f"❌ BaseAgent creation failed: {e}")

# Test CostTracker
print("\nTesting CostTracker...")
try:
    tracker = CostTracker(daily_budget=10.0)
    tracker.track("test_agent", "claude-3-5-sonnet-20241022", 1000, 500, 0.001)
    report = tracker.get_report()
    print(f"✅ CostTracker working: ${report['spent_today']:.6f} spent")
except Exception as e:
    print(f"❌ CostTracker failed: {e}")

# Test CircuitBreaker
print("\nTesting CircuitBreaker...")
try:
    breaker = CircuitBreaker(failure_threshold=3, timeout=5)

    def test_function():
        return "success"

    result = breaker.call(test_function)
    print(f"✅ CircuitBreaker working: {result}")
except Exception as e:
    print(f"❌ CircuitBreaker failed: {e}")

# Test ExponentialBackoff
print("\nTesting ExponentialBackoff...")
try:
    backoff = ExponentialBackoff(base_delay=1.0, max_delay=10.0)
    delays = [backoff.get_delay(i) for i in range(3)]
    print(f"✅ ExponentialBackoff working: delays = {[f'{d:.1f}s' for d in delays]}")
except Exception as e:
    print(f"❌ ExponentialBackoff failed: {e}")

# Test Orchestrator
print("\nTesting Orchestrator...")
try:
    class TestOrchestrator(Orchestrator):
        def prepare_input(self, agent_name, initial_input):
            return {"prompt": f"Test prompt for {agent_name}"}

        def process_output(self, agent_name, output):
            return output

    orchestrator = TestOrchestrator(
        name="Test Orchestrator",
        mode=ExecutionMode.SEQUENTIAL
    )
    print(f"✅ Orchestrator created: {orchestrator.name}")
except Exception as e:
    print(f"❌ Orchestrator creation failed: {e}")

# Test with mock execution (no actual API calls)
print("\nTesting mock agent execution...")
try:
    # Create mock agent
    mock_agent = BaseAgent(role="Mock Agent")

    # Override call method to return mock data
    def mock_call(prompt, context=None, temperature=0.7, max_tokens=2048):
        return {
            'output': f'Mock response to: {prompt[:50]}...',
            'tokens_in': 100,
            'tokens_out': 50,
            'total_tokens': 150,
            'cost': 0.0001,
            'model': 'mock',
            'attempt': 1
        }

    mock_agent.call = mock_call

    # Test the mock agent
    result = mock_agent.call("Test prompt")
    print(f"✅ Mock agent execution: {result['output'][:50]}...")
except Exception as e:
    print(f"❌ Mock execution failed: {e}")

print("\n" + "="*50)
print("Library test complete!")
print("="*50)
print("\nTo use in your projects, add this to the top of your Python files:")
print("```python")
print("import sys")
print("sys.path.insert(0, '/home/jevenson/.claude/lib')")
print("from agent_system import BaseAgent, CostTracker")
print("from orchestrator import Orchestrator, ExecutionMode")
print("```")