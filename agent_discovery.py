"""
Agent Discovery System - Find and Load Agents from Global Registry

Provides high-level interface for:
- Searching agents by use case, model tier, or category
- Loading agents as initialized ResilientBaseAgent instances
- Recommending optimal agents for tasks
- Querying agent capabilities

Architecture:
    AgentDiscovery
    ├── Search registry by criteria
    ├── Load agents from global directory
    ├── Initialize with ResilientBaseAgent
    ├── Recommend agents for tasks
    └── Query capabilities

Usage:
    discovery = AgentDiscovery()

    # Find agents by use case
    agents = discovery.find_agents(use_case="security review")
    # → [security-critic, reviewer]

    # Load and initialize agent
    agent = discovery.load_agent("security-critic")
    # → ResilientBaseAgent ready to use

    # Recommend agent for task
    recommended = discovery.recommend_agent(
        task="Review code for SQL injection vulnerabilities",
        complexity="high"
    )
    # → security-critic (best match)

    # Get agent capabilities
    caps = discovery.get_agent_capabilities("security-critic")
    # → {use_cases, model, estimated_cost, quality_range}
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from agent_registry import (
    AgentRegistry,
    AgentMetadata,
    AgentCategory,
    ModelTier,
    get_global_registry
)

# Import ResilientBaseAgent from Phase B
try:
    from resilient_agent import ResilientBaseAgent
except ImportError:
    # Fallback if not available
    ResilientBaseAgent = None
    logging.warning("ResilientBaseAgent not available, load_agent() will not work")

logger = logging.getLogger(__name__)


class AgentDiscovery:
    """
    Agent Discovery System - Find and load agents from registry.

    Provides high-level interface for agent search, loading, and recommendations.
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        """
        Initialize agent discovery system.

        Args:
            registry: Agent registry to use (default: global singleton)
        """
        self.registry = registry or get_global_registry()
        logger.info(f"AgentDiscovery initialized with {len(self.registry.agents)} agents")

    def find_agents(
        self,
        use_case: Optional[str] = None,
        model_tier: Optional[ModelTier] = None,
        category: Optional[AgentCategory] = None,
        min_quality: Optional[int] = None
    ) -> List[AgentMetadata]:
        """
        Find agents matching criteria.

        Args:
            use_case: Search use cases (substring match)
            model_tier: Filter by model tier
            category: Filter by category
            min_quality: Minimum expected quality score

        Returns:
            List of matching agents, sorted by relevance

        Examples:
            # Find all security-focused agents
            agents = discovery.find_agents(use_case="security")

            # Find high-quality Opus agents
            agents = discovery.find_agents(model_tier=ModelTier.OPUS, min_quality=90)

            # Find all critics
            agents = discovery.find_agents(category=AgentCategory.CRITIC)
        """
        # Start with all agents
        agents = list(self.registry.agents.values())

        # Filter by category
        if category:
            agents = [a for a in agents if a.category == category]

        # Filter by model tier
        if model_tier:
            agents = [a for a in agents if a.model_tier == model_tier]

        # Filter by minimum quality
        if min_quality:
            agents = [a for a in agents if a.quality_range[1] >= min_quality]

        # Search use cases (substring match, case-insensitive)
        if use_case:
            use_case_lower = use_case.lower()
            matched_agents = []

            for agent in agents:
                # Check if use_case appears in any of agent's use cases
                for agent_use_case in agent.use_cases:
                    if use_case_lower in agent_use_case.lower():
                        matched_agents.append(agent)
                        break  # Don't add same agent twice

            agents = matched_agents

        # Sort by quality (highest first)
        agents.sort(key=lambda a: a.quality_range[1], reverse=True)

        logger.debug(f"Found {len(agents)} agents matching criteria")

        return agents

    def load_agent(
        self,
        name: str,
        **kwargs
    ) -> Optional[Any]:
        """
        Load and initialize agent as ResilientBaseAgent.

        Args:
            name: Agent name from registry
            **kwargs: Additional arguments for ResilientBaseAgent initialization

        Returns:
            Initialized ResilientBaseAgent, or None if agent not found

        Example:
            agent = discovery.load_agent("security-critic")
            result = await agent.execute(
                system_prompt="You are a security expert...",
                user_message="Review this code for vulnerabilities..."
            )
        """
        if ResilientBaseAgent is None:
            logger.error("ResilientBaseAgent not available, cannot load agents")
            return None

        # Get agent metadata
        metadata = self.registry.get_agent(name)
        if not metadata:
            logger.error(f"Agent '{name}' not found in registry")
            return None

        # Initialize ResilientBaseAgent with model from registry
        try:
            agent = ResilientBaseAgent(
                name=f"Agent_{name}",
                primary_model=metadata.model_tier.value,
                **kwargs
            )

            logger.info(f"Loaded agent '{name}' with model {metadata.model_tier.value}")

            return agent

        except Exception as e:
            logger.error(f"Failed to load agent '{name}': {e}")
            return None

    def recommend_agent(
        self,
        task: str,
        complexity: str = "moderate",
        quality_target: int = 85,
        max_cost: Optional[float] = None
    ) -> Optional[AgentMetadata]:
        """
        Recommend best agent for a given task.

        Args:
            task: Task description
            complexity: "simple", "moderate", or "complex"
            quality_target: Target quality score (0-100)
            max_cost: Maximum acceptable cost per call (USD)

        Returns:
            Recommended agent, or None if no suitable agent found

        Algorithm:
        1. Extract keywords from task (security, performance, architecture, etc.)
        2. Find agents whose use cases match keywords
        3. Filter by quality target and cost constraints
        4. Rank by relevance and quality
        5. Return best match

        Examples:
            # Security task
            agent = discovery.recommend_agent(
                task="Review code for SQL injection vulnerabilities",
                complexity="high",
                quality_target=95
            )
            # → security-critic

            # Implementation task
            agent = discovery.recommend_agent(
                task="Implement user authentication with JWT",
                complexity="moderate",
                quality_target=85
            )
            # → developer
        """
        task_lower = task.lower()

        # Extract keywords for matching
        keywords = {
            "security": ["security", "vulnerability", "exploit", "injection", "xss", "authentication"],
            "performance": ["performance", "optimize", "bottleneck", "speed", "efficiency", "cache"],
            "architecture": ["architecture", "design", "pattern", "structure", "scalability"],
            "quality": ["quality", "style", "maintainability", "readability", "clean code"],
            "documentation": ["documentation", "docstring", "readme", "comments", "api docs"],
            "testing": ["test", "testing", "unit test", "integration test", "coverage"],
            "implementation": ["implement", "code", "develop", "build", "create", "write"],
            "review": ["review", "audit", "check", "validate", "assess"]
        }

        # Detect task type
        task_types = []
        for task_type, words in keywords.items():
            if any(word in task_lower for word in words):
                task_types.append(task_type)

        logger.debug(f"Detected task types: {task_types}")

        # Find matching agents
        candidates = []

        for task_type in task_types:
            # Map task type to use case search terms
            use_case_term = task_type

            # Find agents for this task type
            agents = self.find_agents(use_case=use_case_term)
            candidates.extend(agents)

        # Remove duplicates
        seen_names = set()
        unique_candidates = []
        for agent in candidates:
            if agent.name not in seen_names:
                seen_names.add(agent.name)
                unique_candidates.append(agent)

        candidates = unique_candidates

        # Filter by quality target
        candidates = [
            a for a in candidates
            if a.quality_range[1] >= quality_target
        ]

        # Filter by max cost if specified
        if max_cost is not None:
            candidates = [
                a for a in candidates
                if a.estimated_cost_per_call <= max_cost
            ]

        if not candidates:
            logger.warning(f"No suitable agents found for task: {task[:50]}...")
            return None

        # Rank by quality and select best
        # Prefer higher quality, then lower cost
        candidates.sort(
            key=lambda a: (a.quality_range[1], -a.estimated_cost_per_call),
            reverse=True
        )

        recommended = candidates[0]

        logger.info(f"Recommended agent '{recommended.name}' for task (quality: {recommended.quality_range[1]})")

        return recommended

    def get_agent_capabilities(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed capabilities for an agent.

        Args:
            name: Agent name

        Returns:
            Dictionary with agent capabilities, or None if not found

        Example:
            caps = discovery.get_agent_capabilities("security-critic")
            # → {
            #     "name": "security-critic",
            #     "category": "critic",
            #     "model": "claude-3-opus-20240229",
            #     "use_cases": [...],
            #     "estimated_cost_per_call": 0.06,
            #     "estimated_time_seconds": 35.0,
            #     "quality_range": (90, 98),
            #     "description": "...",
            #     "stats": {...}
            # }
        """
        metadata = self.registry.get_agent(name)
        if not metadata:
            return None

        # Get usage statistics
        stats = self.registry.get_agent_stats(name)

        return {
            "name": metadata.name,
            "category": metadata.category.value,
            "model": metadata.model_tier.value,
            "use_cases": metadata.use_cases,
            "estimated_cost_per_call": metadata.estimated_cost_per_call,
            "estimated_time_seconds": metadata.estimated_time_seconds,
            "quality_range": metadata.quality_range,
            "description": metadata.description,
            "version": metadata.version,
            "registered_at": metadata.registered_at,
            "stats": stats
        }

    def list_all_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents with their capabilities.

        Returns:
            List of agent capability dictionaries
        """
        return [
            self.get_agent_capabilities(name)
            for name in self.registry.agents.keys()
        ]

    def get_agents_by_cost(
        self,
        max_cost: float,
        category: Optional[AgentCategory] = None
    ) -> List[AgentMetadata]:
        """
        Find agents within cost budget.

        Args:
            max_cost: Maximum acceptable cost per call (USD)
            category: Optional category filter

        Returns:
            Agents sorted by cost (cheapest first)
        """
        agents = list(self.registry.agents.values())

        # Filter by category if specified
        if category:
            agents = [a for a in agents if a.category == category]

        # Filter by cost
        agents = [a for a in agents if a.estimated_cost_per_call <= max_cost]

        # Sort by cost (cheapest first)
        agents.sort(key=lambda a: a.estimated_cost_per_call)

        return agents

    def get_agents_by_quality(
        self,
        min_quality: int,
        category: Optional[AgentCategory] = None
    ) -> List[AgentMetadata]:
        """
        Find agents meeting quality threshold.

        Args:
            min_quality: Minimum expected quality score
            category: Optional category filter

        Returns:
            Agents sorted by quality (highest first)
        """
        agents = list(self.registry.agents.values())

        # Filter by category if specified
        if category:
            agents = [a for a in agents if a.category == category]

        # Filter by quality
        agents = [a for a in agents if a.quality_range[1] >= min_quality]

        # Sort by quality (highest first)
        agents.sort(key=lambda a: a.quality_range[1], reverse=True)

        return agents


# ================== CONVENIENCE FUNCTIONS ==================

def find_agent_for_task(task: str, **kwargs) -> Optional[AgentMetadata]:
    """
    Convenience function to find best agent for a task.

    Args:
        task: Task description
        **kwargs: Additional arguments for recommend_agent()

    Returns:
        Recommended agent metadata
    """
    discovery = AgentDiscovery()
    return discovery.recommend_agent(task, **kwargs)


def get_all_critics() -> List[AgentMetadata]:
    """Get all critic agents (all use Opus by model discipline)."""
    discovery = AgentDiscovery()
    return discovery.find_agents(category=AgentCategory.CRITIC)


def get_core_agents() -> List[AgentMetadata]:
    """Get all core agents."""
    discovery = AgentDiscovery()
    return discovery.find_agents(category=AgentCategory.CORE)


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    discovery = AgentDiscovery()

    print("=" * 70)
    print("🔍 AGENT DISCOVERY SYSTEM DEMO")
    print("=" * 70)

    # Example 1: Find agents by use case
    print("\n📋 Example 1: Find security-focused agents")
    agents = discovery.find_agents(use_case="security")
    print(f"Found {len(agents)} agents:")
    for agent in agents:
        print(f"  • {agent.name} ({agent.category.value}, {agent.model_tier.value})")

    # Example 2: Recommend agent for task
    print("\n📋 Example 2: Recommend agent for security review task")
    recommended = discovery.recommend_agent(
        task="Review this authentication code for security vulnerabilities",
        complexity="high",
        quality_target=90
    )
    if recommended:
        print(f"  Recommended: {recommended.name}")
        print(f"  Model: {recommended.model_tier.value}")
        print(f"  Est. cost: ${recommended.estimated_cost_per_call}")
        print(f"  Quality range: {recommended.quality_range}")

    # Example 3: Get agent capabilities
    print("\n📋 Example 3: Get capabilities for security-critic")
    caps = discovery.get_agent_capabilities("security-critic")
    if caps:
        print(f"  Name: {caps['name']}")
        print(f"  Model: {caps['model']}")
        print(f"  Use cases: {len(caps['use_cases'])} defined")
        print(f"  Cost: ${caps['estimated_cost_per_call']}")
        print(f"  Quality: {caps['quality_range']}")

    # Example 4: Find all critics
    print("\n📋 Example 4: List all critic agents")
    critics = get_all_critics()
    print(f"Found {len(critics)} critics:")
    for critic in critics:
        print(f"  • {critic.name} - {critic.description[:50]}...")

    # Example 5: Find agents by cost
    print("\n📋 Example 5: Find agents under $0.02 per call")
    affordable = discovery.get_agents_by_cost(max_cost=0.02)
    print(f"Found {len(affordable)} agents:")
    for agent in affordable:
        print(f"  • {agent.name}: ${agent.estimated_cost_per_call}")

    print("\n" + "=" * 70)
