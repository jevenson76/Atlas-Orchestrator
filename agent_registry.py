"""
Agent Registry System - Global Agent Directory with Model Discipline

Manages all agents in a centralized registry with:
- Model discipline enforcement (Haiku for volume, Sonnet for standard, Opus for judgment)
- Usage tracking and analytics
- Agent discovery and recommendations
- Cost and performance monitoring

Architecture:
    AgentRegistry
    ├── Register agents with metadata
    ├── Enforce model discipline rules
    ├── Track usage statistics
    ├── Recommend models based on task
    └── Persist to JSON files

Usage:
    registry = AgentRegistry()

    # Register agent
    registry.register_agent(
        name="security-critic",
        category=AgentCategory.CRITIC,
        model_tier=ModelTier.OPUS,
        description="Security vulnerability analysis",
        use_cases=["security review", "vulnerability scanning"],
        estimated_cost_per_call=0.05,
        estimated_time_seconds=15.0,
        quality_range=(90, 98)
    )

    # Record usage
    registry.record_usage(
        agent_name="security-critic",
        cost_usd=0.048,
        execution_time_seconds=14.2,
        quality_score=95
    )

    # Get statistics
    stats = registry.get_agent_stats("security-critic")
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """
    Model tiers for agent execution.

    HAIKU: High-volume, fast operations (>1000 calls/day expected)
           - Scouting, summarization, quick checks
           - ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens

    SONNET: Standard development work
           - Implementation, analysis, standard tasks
           - ~$3 per 1M input tokens, ~$15 per 1M output tokens

    OPUS: Complex judgment and critique
           - Architecture, critique, complex decisions
           - ~$15 per 1M input tokens, ~$75 per 1M output tokens
    """
    HAIKU = "claude-3-5-haiku-20241022"
    SONNET = "claude-3-5-sonnet-20241022"
    OPUS = "claude-opus-4-20250514"  # Updated to Opus 4 for C3 critic system


class AgentCategory(str, Enum):
    """Agent categories for organization."""
    CORE = "core"              # Essential agents, always loaded
    SPECIALIZED = "specialized" # Domain-specific agents
    CRITIC = "critic"           # Critic agents (must use Opus)
    EXPERIMENTAL = "experimental" # Testing new agents


@dataclass
class AgentMetadata:
    """Metadata for a registered agent."""
    # Identity
    name: str
    category: AgentCategory
    model_tier: ModelTier

    # Description
    description: str
    use_cases: List[str]

    # Performance expectations
    estimated_cost_per_call: float  # USD
    estimated_time_seconds: float
    quality_range: Tuple[int, int]  # (min, max) expected quality scores

    # Output style (optional - system prompt control)
    output_style: Optional[str] = None

    # Registration metadata
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"

    # Usage statistics (tracked over time)
    total_invocations: int = 0
    total_cost_usd: float = 0.0
    total_execution_time_seconds: float = 0.0
    average_quality_score: Optional[float] = None
    last_used_at: Optional[str] = None

    # Output style usage tracking (style_name -> invocation_count)
    style_usage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['category'] = self.category.value
        data['model_tier'] = self.model_tier.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMetadata':
        """Create from dictionary."""
        # Convert strings to enums
        data['category'] = AgentCategory(data['category'])
        data['model_tier'] = ModelTier(data['model_tier'])
        return cls(**data)


class ModelDisciplineViolationError(Exception):
    """Raised when agent registration violates model discipline rules."""
    pass


class AgentRegistry:
    """
    Central registry for all agents with model discipline enforcement.

    Model Discipline Rules:
    1. CRITIC agents MUST use Opus (enforced strictly)
    2. High-volume agents (>1000 calls/day) SHOULD use Haiku (warning if not)
    3. Standard agents SHOULD use Sonnet (recommendation)
    4. Complex judgment agents SHOULD use Opus (recommendation)
    """

    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Initialize agent registry.

        Args:
            registry_dir: Directory for registry files (default: ~/.claude/agents/global/.registry)
        """
        self.registry_dir = registry_dir or Path.home() / ".claude" / "agents" / "global" / ".registry"
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        # Registry files
        self.registry_file = self.registry_dir / "agent_registry.json"
        self.usage_stats_file = self.registry_dir / "usage_stats.json"
        self.model_discipline_file = self.registry_dir / "model_discipline.json"

        # In-memory registry
        self.agents: Dict[str, AgentMetadata] = {}

        # Load existing registry
        self._load_registry()

        logger.info(f"AgentRegistry initialized with {len(self.agents)} agents")

    def register_agent(
        self,
        name: str,
        category: AgentCategory,
        model_tier: ModelTier,
        description: str,
        use_cases: List[str],
        estimated_cost_per_call: float,
        estimated_time_seconds: float,
        quality_range: Tuple[int, int],
        version: str = "1.0.0",
        output_style: Optional[str] = None,
        enforce_discipline: bool = True
    ) -> AgentMetadata:
        """
        Register an agent with the global registry.

        Args:
            name: Agent name (unique identifier)
            category: Agent category
            model_tier: Model tier to use
            description: What the agent does
            use_cases: List of use case descriptions
            estimated_cost_per_call: Estimated cost per invocation (USD)
            estimated_time_seconds: Estimated execution time
            quality_range: (min, max) expected quality scores
            version: Agent version
            output_style: Optional output style name (e.g., 'code', 'critic', 'architect')
            enforce_discipline: Whether to enforce model discipline (raises errors)

        Returns:
            AgentMetadata for the registered agent

        Raises:
            ModelDisciplineViolationError: If agent violates model discipline rules
        """
        # Validate model discipline
        if enforce_discipline:
            self._validate_model_discipline(name, category, model_tier)

        # Check if agent already registered
        if name in self.agents:
            logger.warning(f"Agent '{name}' already registered, updating metadata")

        # Create metadata
        metadata = AgentMetadata(
            name=name,
            category=category,
            model_tier=model_tier,
            description=description,
            use_cases=use_cases,
            estimated_cost_per_call=estimated_cost_per_call,
            estimated_time_seconds=estimated_time_seconds,
            quality_range=quality_range,
            output_style=output_style,
            version=version
        )

        # Add to registry
        self.agents[name] = metadata

        # Persist
        self._save_registry()

        logger.info(f"✅ Registered agent: {name} ({category.value}, {model_tier.value})")

        return metadata

    def _validate_model_discipline(
        self,
        name: str,
        category: AgentCategory,
        model_tier: ModelTier
    ):
        """
        Validate that agent follows model discipline rules.

        Rules:
        1. CRITIC agents MUST use Opus (strict)
        2. High-volume agents SHOULD use Haiku (warning)
        """
        # Rule 1: Critics MUST use Opus
        if category == AgentCategory.CRITIC and model_tier != ModelTier.OPUS:
            raise ModelDisciplineViolationError(
                f"CRITICAL: Agent '{name}' is a CRITIC but uses {model_tier.value}. "
                f"Critics MUST use Opus for reliable judgment. "
                f"This is a hard requirement for model discipline."
            )

        # Rule 2: High-volume agents should use Haiku (warning only)
        # TODO: Could add volume tracking and warn if agent with >1000 calls/day doesn't use Haiku

    def get_agent(self, name: str) -> Optional[AgentMetadata]:
        """Get agent metadata by name."""
        return self.agents.get(name)

    def list_agents(
        self,
        category: Optional[AgentCategory] = None,
        model_tier: Optional[ModelTier] = None
    ) -> List[AgentMetadata]:
        """
        List agents filtered by category and/or model tier.

        Args:
            category: Filter by category (optional)
            model_tier: Filter by model tier (optional)

        Returns:
            List of matching agents
        """
        agents = list(self.agents.values())

        if category:
            agents = [a for a in agents if a.category == category]

        if model_tier:
            agents = [a for a in agents if a.model_tier == model_tier]

        return agents

    def recommend_model(
        self,
        task_complexity: str,  # "simple", "moderate", "complex"
        volume: str,  # "low", "medium", "high"
        requires_judgment: bool = False
    ) -> ModelTier:
        """
        Recommend model tier based on task characteristics.

        Args:
            task_complexity: "simple", "moderate", or "complex"
            volume: "low" (<100 calls/day), "medium" (100-1000), "high" (>1000)
            requires_judgment: Whether task requires judgment/critique

        Returns:
            Recommended ModelTier
        """
        # Rule 1: Judgment tasks need Opus
        if requires_judgment or task_complexity == "complex":
            return ModelTier.OPUS

        # Rule 2: High volume needs Haiku
        if volume == "high":
            return ModelTier.HAIKU

        # Rule 3: Simple tasks can use Haiku
        if task_complexity == "simple":
            return ModelTier.HAIKU

        # Default: Sonnet for moderate complexity/volume
        return ModelTier.SONNET

    def record_usage(
        self,
        agent_name: str,
        cost_usd: float,
        execution_time_seconds: float,
        quality_score: Optional[int] = None,
        output_style_used: Optional[str] = None
    ):
        """
        Record usage statistics for an agent invocation.

        Args:
            agent_name: Name of agent that was invoked
            cost_usd: Actual cost of invocation
            execution_time_seconds: Actual execution time
            quality_score: Quality score (0-100) if measured
            output_style_used: Optional output style that was used in this invocation
        """
        agent = self.agents.get(agent_name)
        if not agent:
            logger.warning(f"Attempted to record usage for unregistered agent: {agent_name}")
            return

        # Update statistics
        agent.total_invocations += 1
        agent.total_cost_usd += cost_usd
        agent.total_execution_time_seconds += execution_time_seconds
        agent.last_used_at = datetime.now().isoformat()

        # Update average quality score
        if quality_score is not None:
            if agent.average_quality_score is None:
                agent.average_quality_score = quality_score
            else:
                # Running average
                n = agent.total_invocations
                agent.average_quality_score = (
                    (agent.average_quality_score * (n - 1) + quality_score) / n
                )

        # Track output style usage
        if output_style_used:
            if output_style_used not in agent.style_usage:
                agent.style_usage[output_style_used] = 0
            agent.style_usage[output_style_used] += 1

        # Persist updated statistics to both files
        self._save_registry()  # Save to agent_registry.json
        self._save_usage_stats()  # Also save to usage_stats.json for quick access

        logger.debug(
            f"Recorded usage for {agent_name}: ${cost_usd:.4f}, {execution_time_seconds:.2f}s"
            + (f", style={output_style_used}" if output_style_used else "")
        )

    def get_agent_stats(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get usage statistics for an agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return None

        return {
            "name": agent.name,
            "category": agent.category.value,
            "model_tier": agent.model_tier.value,
            "output_style": agent.output_style,
            "total_invocations": agent.total_invocations,
            "total_cost_usd": agent.total_cost_usd,
            "total_execution_time_seconds": agent.total_execution_time_seconds,
            "average_cost_per_call": (
                agent.total_cost_usd / agent.total_invocations
                if agent.total_invocations > 0 else 0
            ),
            "average_execution_time": (
                agent.total_execution_time_seconds / agent.total_invocations
                if agent.total_invocations > 0 else 0
            ),
            "average_quality_score": agent.average_quality_score,
            "last_used_at": agent.last_used_at,
            "quality_range": agent.quality_range,
            "style_usage": agent.style_usage
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics across all agents."""
        total_invocations = sum(a.total_invocations for a in self.agents.values())
        total_cost = sum(a.total_cost_usd for a in self.agents.values())

        # Cost by model tier
        cost_by_tier = {}
        for tier in ModelTier:
            agents_with_tier = [a for a in self.agents.values() if a.model_tier == tier]
            cost_by_tier[tier.value] = sum(a.total_cost_usd for a in agents_with_tier)

        # Most used agents
        most_used = sorted(
            self.agents.values(),
            key=lambda a: a.total_invocations,
            reverse=True
        )[:10]

        return {
            "total_agents": len(self.agents),
            "total_invocations": total_invocations,
            "total_cost_usd": total_cost,
            "cost_by_model_tier": cost_by_tier,
            "agents_by_category": {
                cat.value: len([a for a in self.agents.values() if a.category == cat])
                for cat in AgentCategory
            },
            "most_used_agents": [
                {"name": a.name, "invocations": a.total_invocations}
                for a in most_used
            ]
        }

    def _load_registry(self):
        """Load registry from JSON file."""
        if not self.registry_file.exists():
            logger.info("No existing registry found, starting fresh")
            return

        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)

            for agent_data in data.get('agents', []):
                metadata = AgentMetadata.from_dict(agent_data)
                self.agents[metadata.name] = metadata

            logger.info(f"Loaded {len(self.agents)} agents from registry")

        except Exception as e:
            logger.error(f"Failed to load registry: {e}")

    def _save_registry(self):
        """Save registry to JSON file."""
        try:
            data = {
                "version": "1.0.0",
                "updated_at": datetime.now().isoformat(),
                "agents": [agent.to_dict() for agent in self.agents.values()]
            }

            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved registry with {len(self.agents)} agents")

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def _save_usage_stats(self):
        """Save usage statistics to separate file for faster access."""
        try:
            stats = {
                "updated_at": datetime.now().isoformat(),
                "agents": {
                    name: self.get_agent_stats(name)
                    for name in self.agents.keys()
                }
            }

            with open(self.usage_stats_file, 'w') as f:
                json.dump(stats, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save usage stats: {e}")


# ================== CONVENIENCE FUNCTIONS ==================

def get_global_registry() -> AgentRegistry:
    """Get singleton instance of global agent registry."""
    if not hasattr(get_global_registry, '_instance'):
        get_global_registry._instance = AgentRegistry()
    return get_global_registry._instance


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)

    registry = AgentRegistry()

    # Register example agents
    registry.register_agent(
        name="architect",
        category=AgentCategory.CORE,
        model_tier=ModelTier.OPUS,
        description="System design and architecture planning",
        use_cases=["architecture design", "system planning"],
        estimated_cost_per_call=0.05,
        estimated_time_seconds=30.0,
        quality_range=(85, 98)
    )

    registry.register_agent(
        name="developer",
        category=AgentCategory.CORE,
        model_tier=ModelTier.SONNET,
        description="Code implementation",
        use_cases=["coding", "implementation"],
        estimated_cost_per_call=0.01,
        estimated_time_seconds=15.0,
        quality_range=(80, 95)
    )

    # Record some usage
    registry.record_usage("architect", cost_usd=0.048, execution_time_seconds=28.5, quality_score=92)
    registry.record_usage("developer", cost_usd=0.012, execution_time_seconds=14.2, quality_score=88)

    # Get statistics
    print("\n=== Agent Statistics ===")
    print(json.dumps(registry.get_all_stats(), indent=2))
