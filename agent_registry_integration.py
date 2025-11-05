"""
Agent Registry Integration - Helper for Orchestrators

Provides easy integration of agent registry usage tracking into existing orchestrators.

Usage in orchestrators:
    from agent_registry_integration import AgentUsageTracker

    class MyOrchestrator:
        def __init__(self):
            self.usage_tracker = AgentUsageTracker()

        async def execute_phase(self):
            start_time = time.time()

            # Execute agent
            result = await agent.execute(...)

            # Record usage
            self.usage_tracker.record(
                agent_name="developer",
                cost_usd=result.cost,
                execution_time_seconds=time.time() - start_time,
                quality_score=result.quality
            )
"""

import logging
import time
from typing import Optional
from contextlib import contextmanager

from agent_registry import get_global_registry, AgentRegistry

logger = logging.getLogger(__name__)


class AgentUsageTracker:
    """
    Helper class for tracking agent usage in orchestrators.

    Provides simple interface for recording agent invocations with
    cost, time, and quality metrics.
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        """
        Initialize usage tracker.

        Args:
            registry: Agent registry to use (default: global singleton)
        """
        self.registry = registry or get_global_registry()
        self.enabled = True

    def record(
        self,
        agent_name: str,
        cost_usd: float,
        execution_time_seconds: float,
        quality_score: Optional[int] = None
    ):
        """
        Record agent usage.

        Args:
            agent_name: Name of agent (must be in registry)
            cost_usd: Cost of this invocation
            execution_time_seconds: Execution time
            quality_score: Quality score if measured
        """
        if not self.enabled:
            return

        try:
            self.registry.record_usage(
                agent_name=agent_name,
                cost_usd=cost_usd,
                execution_time_seconds=execution_time_seconds,
                quality_score=quality_score
            )
            logger.debug(f"Recorded usage for {agent_name}: ${cost_usd:.4f}, {execution_time_seconds:.2f}s")
        except Exception as e:
            # Don't fail workflow if tracking fails
            logger.warning(f"Failed to record usage for {agent_name}: {e}")

    @contextmanager
    def track_agent(
        self,
        agent_name: str,
        cost_usd: Optional[float] = None,
        quality_score: Optional[int] = None
    ):
        """
        Context manager for automatic time tracking.

        Usage:
            with tracker.track_agent("developer", cost_usd=0.015, quality_score=85):
                result = await agent.execute(...)

        Args:
            agent_name: Agent name
            cost_usd: Cost (if known beforehand)
            quality_score: Quality score (if known beforehand)
        """
        start_time = time.time()

        try:
            yield
        finally:
            execution_time = time.time() - start_time

            if cost_usd is not None:
                self.record(
                    agent_name=agent_name,
                    cost_usd=cost_usd,
                    execution_time_seconds=execution_time,
                    quality_score=quality_score
                )

    def disable(self):
        """Disable usage tracking (for testing)."""
        self.enabled = False

    def enable(self):
        """Enable usage tracking."""
        self.enabled = True


# ================== INTEGRATION EXAMPLES ==================

# Example 1: Manual recording
def example_manual_recording():
    """Example of manual usage recording."""
    tracker = AgentUsageTracker()

    # Execute agent
    start_time = time.time()
    # result = await agent.execute(...)
    execution_time = time.time() - start_time

    # Record usage
    tracker.record(
        agent_name="developer",
        cost_usd=0.015,
        execution_time_seconds=execution_time,
        quality_score=88
    )


# Example 2: Context manager
async def example_context_manager():
    """Example using context manager for automatic time tracking."""
    tracker = AgentUsageTracker()

    with tracker.track_agent("developer", cost_usd=0.015, quality_score=88):
        # Execute agent - time tracked automatically
        # result = await agent.execute(...)
        pass


# Example 3: Integration in orchestrator
class ExampleOrchestrator:
    """Example orchestrator with registry integration."""

    def __init__(self):
        # Add usage tracker
        self.usage_tracker = AgentUsageTracker()

    async def execute_phase(self, phase_name: str):
        """Execute a phase and track usage."""
        start_time = time.time()

        # Execute agent
        # result = await self.agent.execute(...)

        # Simulate execution
        result_cost = 0.015
        result_quality = 88

        # Record usage
        self.usage_tracker.record(
            agent_name=phase_name,
            cost_usd=result_cost,
            execution_time_seconds=time.time() - start_time,
            quality_score=result_quality
        )

        logger.info(f"✅ Phase '{phase_name}' completed and usage recorded")


# ================== HELPER FUNCTIONS ==================

def create_usage_tracker() -> AgentUsageTracker:
    """
    Create a usage tracker instance.

    Convenience function for creating tracker in orchestrators.
    """
    return AgentUsageTracker()


def record_agent_usage(
    agent_name: str,
    cost_usd: float,
    execution_time_seconds: float,
    quality_score: Optional[int] = None
):
    """
    Convenience function to record agent usage.

    Args:
        agent_name: Agent name
        cost_usd: Cost in USD
        execution_time_seconds: Execution time
        quality_score: Quality score if available
    """
    tracker = AgentUsageTracker()
    tracker.record(
        agent_name=agent_name,
        cost_usd=cost_usd,
        execution_time_seconds=execution_time_seconds,
        quality_score=quality_score
    )


if __name__ == "__main__":
    # Demo usage tracking
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 70)
    print("📊 AGENT USAGE TRACKING DEMO")
    print("=" * 70)

    tracker = AgentUsageTracker()

    # Simulate some agent invocations
    print("\n✓ Recording usage for developer agent...")
    tracker.record(
        agent_name="developer",
        cost_usd=0.0145,
        execution_time_seconds=18.5,
        quality_score=89
    )

    print("✓ Recording usage for security-critic agent...")
    tracker.record(
        agent_name="security-critic",
        cost_usd=0.058,
        execution_time_seconds=32.3,
        quality_score=94
    )

    print("✓ Recording usage for tester agent...")
    tracker.record(
        agent_name="tester",
        cost_usd=0.011,
        execution_time_seconds=16.2,
        quality_score=91
    )

    # Get statistics
    print("\n📊 Agent Statistics:")

    registry = get_global_registry()
    stats = registry.get_all_stats()

    print(f"\nTotal invocations: {stats['total_invocations']}")
    print(f"Total cost: ${stats['total_cost_usd']:.4f}")

    print("\n✅ Most used agents:")
    for agent_info in stats['most_used_agents'][:5]:
        if agent_info['invocations'] > 0:
            agent_stats = registry.get_agent_stats(agent_info['name'])
            print(f"  • {agent_info['name']}: {agent_info['invocations']} calls, "
                  f"avg ${agent_stats['average_cost_per_call']:.4f}, "
                  f"quality {agent_stats['average_quality_score']:.1f}")

    print("\n" + "=" * 70)
