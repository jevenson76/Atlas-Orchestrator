#!/usr/bin/env python3
"""
Agent Registry MCP Server - Agent Discovery and Analytics via MCP

Exposes Component C1 Agent Registry through MCP tools:
- List and discover agents
- Get agent statistics and capabilities
- Analyze costs and performance
- Get recommendations for tasks

Resources:
- Agent directory catalog
- Usage analytics

Usage:
    python3 agent_registry_server.py
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from mcp_servers.base_server import BaseMCPServer, ToolParameter
from agent_registry import get_global_registry, AgentCategory, ModelTier
from agent_discovery import AgentDiscovery
from agent_analytics import AgentAnalytics

logger = logging.getLogger(__name__)


class AgentRegistryServer(BaseMCPServer):
    """
    MCP server providing agent registry access and analytics.

    Tools:
    - list_agents: List all registered agents with filters
    - discover_agent: Find optimal agent for specific task
    - get_agent_stats: Usage statistics for agent
    - get_cost_analysis: Cost breakdown and optimization opportunities

    Resources:
    - agents://directory: Full agent catalog
    - agents://analytics: Usage analytics and metrics
    """

    def __init__(self):
        """Initialize agent registry server."""
        super().__init__(
            name="agent-registry",
            version="1.0.0",
            description="Agent registry and analytics via MCP"
        )

        # Initialize registry components
        self.registry = get_global_registry()
        self.discovery = AgentDiscovery(registry=self.registry)
        self.analytics = AgentAnalytics(registry=self.registry)

        logger.info(f"Initialized AgentRegistryServer with {len(self.registry.agents)} agents")

    async def _register_tools(self):
        """Register all agent registry tools."""

        # Tool 1: List Agents
        self.create_tool(
            name="list_agents",
            description="List all registered agents with optional filtering by category, "
                       "model tier, or quality threshold. Returns agent metadata including "
                       "capabilities, costs, and usage statistics.",
            input_schema={
                "type": "object",
                "properties": {
                    "category": ToolParameter.string(
                        "Filter by category",
                        enum=["core", "specialized", "critic", "experimental", "all"],
                        default="all"
                    ),
                    "model_tier": ToolParameter.string(
                        "Filter by model tier",
                        enum=["haiku", "sonnet", "opus", "all"],
                        default="all"
                    ),
                    "min_quality": ToolParameter.integer(
                        "Minimum quality score (0-100)",
                        minimum=0,
                        maximum=100
                    ),
                    "include_stats": ToolParameter.boolean(
                        "Include usage statistics",
                        default=True
                    )
                },
                "required": []
            },
            handler=self._handle_list_agents
        )

        # Tool 2: Discover Agent
        self.create_tool(
            name="discover_agent",
            description="Find optimal agent for specific task. Analyzes task description "
                       "and recommends best agent based on use cases, quality requirements, "
                       "and cost constraints. Returns agent recommendation with reasoning.",
            input_schema={
                "type": "object",
                "properties": {
                    "task": ToolParameter.string(
                        "Task description to find agent for"
                    ),
                    "complexity": ToolParameter.string(
                        "Task complexity",
                        enum=["simple", "moderate", "complex"],
                        default="moderate"
                    ),
                    "quality_target": ToolParameter.integer(
                        "Target quality score (0-100)",
                        default=85,
                        minimum=0,
                        maximum=100
                    ),
                    "max_cost": ToolParameter.integer(
                        "Maximum cost per call in cents (e.g., 5 = $0.05)",
                        minimum=1
                    )
                },
                "required": ["task"]
            },
            handler=self._handle_discover_agent
        )

        # Tool 3: Get Agent Stats
        self.create_tool(
            name="get_agent_stats",
            description="Get detailed usage statistics for specific agent. "
                       "Returns invocation count, costs, execution times, quality scores, "
                       "and performance trends.",
            input_schema={
                "type": "object",
                "properties": {
                    "agent_name": ToolParameter.string(
                        "Agent name to get statistics for"
                    ),
                    "include_capabilities": ToolParameter.boolean(
                        "Include agent capabilities and metadata",
                        default=True
                    )
                },
                "required": ["agent_name"]
            },
            handler=self._handle_get_agent_stats
        )

        # Tool 4: Get Cost Analysis
        self.create_tool(
            name="get_cost_analysis",
            description="Analyze costs across all agents and identify optimization opportunities. "
                       "Shows cost breakdown by agent and model tier, identifies expensive agents "
                       "not outperforming cheaper alternatives, and provides savings recommendations.",
            input_schema={
                "type": "object",
                "properties": {
                    "category": ToolParameter.string(
                        "Focus analysis on specific category",
                        enum=["core", "specialized", "critic", "experimental", "all"],
                        default="all"
                    ),
                    "min_invocations": ToolParameter.integer(
                        "Only include agents with minimum invocations",
                        default=0,
                        minimum=0
                    )
                },
                "required": []
            },
            handler=self._handle_get_cost_analysis
        )

    async def _register_resources(self):
        """Register all agent registry resources."""

        # Resource 1: Agent Directory
        self.create_resource(
            uri="agents://directory",
            name="Agent Directory",
            description="Complete catalog of all registered agents with capabilities",
            handler=self._handle_agent_directory
        )

        # Resource 2: Agent Analytics
        self.create_resource(
            uri="agents://analytics",
            name="Agent Analytics",
            description="Usage analytics, performance metrics, and cost data",
            handler=self._handle_agent_analytics
        )

    # ==================== TOOL HANDLERS ====================

    async def _handle_list_agents(
        self,
        category: str = "all",
        model_tier: str = "all",
        min_quality: Optional[int] = None,
        include_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Handle agent listing with filters.
        """
        try:
            logger.info(f"Listing agents (category={category}, tier={model_tier})")

            # Convert filter values
            category_filter = None if category == "all" else AgentCategory(category)
            tier_filter = None if model_tier == "all" else ModelTier(self._get_model_tier_value(model_tier))

            # Find agents
            agents = self.discovery.find_agents(
                category=category_filter,
                model_tier=tier_filter,
                min_quality=min_quality
            )

            # Format response
            agent_list = []
            for agent in agents:
                agent_info = {
                    "name": agent.name,
                    "category": agent.category.value,
                    "model_tier": agent.model_tier.value,
                    "description": agent.description,
                    "use_cases": agent.use_cases,
                    "estimated_cost_per_call": agent.estimated_cost_per_call,
                    "estimated_time_seconds": agent.estimated_time_seconds,
                    "quality_range": list(agent.quality_range)
                }

                if include_stats:
                    stats = self.registry.get_agent_stats(agent.name)
                    if stats:
                        agent_info["stats"] = {
                            "total_invocations": stats["total_invocations"],
                            "total_cost_usd": stats["total_cost_usd"],
                            "average_quality_score": stats["average_quality_score"],
                            "last_used_at": stats["last_used_at"]
                        }

                agent_list.append(agent_info)

            response = {
                "success": True,
                "agents": agent_list,
                "count": len(agent_list),
                "filters_applied": {
                    "category": category,
                    "model_tier": model_tier,
                    "min_quality": min_quality
                }
            }

            logger.info(f"Found {len(agent_list)} agents matching filters")

            return self.format_success(response, f"Found {len(agent_list)} agents")

        except Exception as e:
            logger.error(f"List agents failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_discover_agent(
        self,
        task: str,
        complexity: str = "moderate",
        quality_target: int = 85,
        max_cost: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle agent discovery for task.
        """
        try:
            logger.info(f"Discovering agent for task: {task[:50]}...")

            # Convert max_cost from cents to dollars if provided
            max_cost_usd = max_cost / 100.0 if max_cost else None

            # Recommend agent
            recommended = self.discovery.recommend_agent(
                task=task,
                complexity=complexity,
                quality_target=quality_target,
                max_cost=max_cost_usd
            )

            if not recommended:
                return self.format_success(
                    {"success": False, "message": "No suitable agent found for task"},
                    "No agent matches requirements"
                )

            # Get detailed capabilities
            capabilities = self.discovery.get_agent_capabilities(recommended.name)

            # Generate reasoning
            reasoning = self._generate_discovery_reasoning(
                recommended,
                task,
                complexity,
                quality_target
            )

            response = {
                "success": True,
                "recommended_agent": {
                    "name": recommended.name,
                    "category": recommended.category.value,
                    "model_tier": recommended.model_tier.value,
                    "description": recommended.description,
                    "use_cases": recommended.use_cases,
                    "estimated_cost": recommended.estimated_cost_per_call,
                    "estimated_time": recommended.estimated_time_seconds,
                    "quality_range": list(recommended.quality_range)
                },
                "reasoning": reasoning,
                "matches_requirements": {
                    "complexity": complexity,
                    "quality_target": quality_target,
                    "within_budget": max_cost_usd is None or recommended.estimated_cost_per_call <= max_cost_usd
                },
                "capabilities": capabilities
            }

            logger.info(f"Recommended agent: {recommended.name}")

            return self.format_success(response, f"Recommended: {recommended.name}")

        except Exception as e:
            logger.error(f"Agent discovery failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_get_agent_stats(
        self,
        agent_name: str,
        include_capabilities: bool = True
    ) -> Dict[str, Any]:
        """
        Handle agent statistics retrieval.
        """
        try:
            logger.info(f"Getting statistics for agent: {agent_name}")

            # Get stats
            stats = self.registry.get_agent_stats(agent_name)

            if not stats:
                return self.format_success(
                    {"success": False, "message": f"Agent not found: {agent_name}"},
                    "Agent not found"
                )

            response = {
                "success": True,
                "agent_name": agent_name,
                "usage": {
                    "total_invocations": stats["total_invocations"],
                    "total_cost_usd": stats["total_cost_usd"],
                    "total_execution_time_seconds": stats["total_execution_time_seconds"],
                    "average_cost_per_call": stats["average_cost_per_call"],
                    "average_execution_time": stats["average_execution_time"],
                    "average_quality_score": stats["average_quality_score"],
                    "last_used_at": stats["last_used_at"]
                },
                "metadata": {
                    "category": stats["category"],
                    "model_tier": stats["model_tier"],
                    "quality_range": stats["quality_range"]
                }
            }

            if include_capabilities:
                capabilities = self.discovery.get_agent_capabilities(agent_name)
                if capabilities:
                    response["capabilities"] = {
                        "description": capabilities["description"],
                        "use_cases": capabilities["use_cases"],
                        "estimated_cost_per_call": capabilities["estimated_cost_per_call"],
                        "estimated_time_seconds": capabilities["estimated_time_seconds"]
                    }

            logger.info(f"Retrieved stats for {agent_name}: {stats['total_invocations']} invocations")

            return self.format_success(response, f"Stats for {agent_name}")

        except Exception as e:
            logger.error(f"Get agent stats failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_get_cost_analysis(
        self,
        category: str = "all",
        min_invocations: int = 0
    ) -> Dict[str, Any]:
        """
        Handle cost analysis and optimization.
        """
        try:
            logger.info(f"Generating cost analysis (category={category})")

            # Convert category filter
            category_filter = None if category == "all" else AgentCategory(category)

            # Generate analytics report
            report = self.analytics.generate_report(
                top_n=10,
                category_filter=category_filter,
                min_invocations=min_invocations
            )

            # Format response
            response = {
                "success": True,
                "summary": {
                    "total_agents": report["summary"]["total_agents"],
                    "total_invocations": report["summary"]["total_invocations"],
                    "total_cost_usd": report["summary"]["total_cost_usd"],
                    "cost_by_model_tier": report["summary"]["cost_by_model_tier"]
                },
                "highest_cost_agents": report["highest_cost_agents"],
                "optimization_opportunities": report["optimization_opportunities"],
                "recommendations": self._generate_cost_recommendations(report)
            }

            # Add underperforming agents if any
            if report.get("underperforming_agents"):
                response["underperforming_agents"] = report["underperforming_agents"]

            logger.info(f"Cost analysis complete: ${report['summary']['total_cost_usd']:.4f} total")

            return self.format_success(
                response,
                f"Found {len(report['optimization_opportunities'])} optimization opportunities"
            )

        except Exception as e:
            logger.error(f"Cost analysis failed: {e}", exc_info=True)
            return self.format_error(e)

    # ==================== RESOURCE HANDLERS ====================

    async def _handle_agent_directory(self) -> Dict[str, Any]:
        """Provide complete agent directory."""
        agents = []

        for agent_name, agent in self.registry.agents.items():
            capabilities = self.discovery.get_agent_capabilities(agent_name)
            if capabilities:
                agents.append(capabilities)

        return {
            "agents": agents,
            "total_count": len(agents),
            "by_category": {
                cat.value: len([a for a in self.registry.agents.values() if a.category == cat])
                for cat in AgentCategory
            },
            "by_tier": {
                tier.value: len([a for a in self.registry.agents.values() if a.model_tier == tier])
                for tier in ModelTier
            }
        }

    async def _handle_agent_analytics(self) -> Dict[str, Any]:
        """Provide agent analytics."""
        report = self.analytics.generate_report(top_n=10)

        return {
            "summary": report["summary"],
            "most_used_agents": report["most_used_agents"],
            "highest_cost_agents": report["highest_cost_agents"],
            "highest_quality_agents": report["highest_quality_agents"],
            "optimization_opportunities": report["optimization_opportunities"]
        }

    # ==================== HELPER METHODS ====================

    def _get_model_tier_value(self, tier: str) -> str:
        """Get model tier enum value from string."""
        tier_map = {
            "haiku": "claude-3-5-haiku-20241022",
            "sonnet": "claude-3-5-sonnet-20241022",
            "opus": "claude-3-opus-20240229"
        }
        return tier_map.get(tier.lower(), tier)

    def _generate_discovery_reasoning(
        self,
        agent: Any,
        task: str,
        complexity: str,
        quality_target: int
    ) -> str:
        """Generate reasoning for agent recommendation."""
        reasons = []

        # Match on use cases
        task_lower = task.lower()
        matched_use_cases = [uc for uc in agent.use_cases if any(word in task_lower for word in uc.lower().split())]

        if matched_use_cases:
            reasons.append(f"Matches use cases: {', '.join(matched_use_cases[:2])}")

        # Quality alignment
        if agent.quality_range[1] >= quality_target:
            reasons.append(f"Can achieve quality target ({agent.quality_range[1]} max vs {quality_target} required)")

        # Model tier appropriateness
        if complexity == "complex" and agent.category == AgentCategory.CRITIC:
            reasons.append("Complex task requires critic-level analysis (Opus)")
        elif complexity == "simple" and agent.model_tier == ModelTier.HAIKU:
            reasons.append("Simple task benefits from fast/cost-effective Haiku model")

        # Category alignment
        if agent.category == AgentCategory.CORE:
            reasons.append("Core agent with proven reliability")

        if not reasons:
            reasons.append("Best match based on overall capabilities")

        return " | ".join(reasons)

    def _generate_cost_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate cost optimization recommendations."""
        recommendations = []

        # From optimization opportunities
        opportunities = report.get("optimization_opportunities", [])
        if opportunities:
            for opp in opportunities[:3]:  # Top 3
                recommendations.append(opp["recommendation"])

        # High-cost agents
        high_cost = report.get("highest_cost_agents", [])
        if high_cost and high_cost[0]["total_cost"] > 1.0:
            recommendations.append(f"Monitor {high_cost[0]['name']} - highest cost agent")

        # Underperforming agents
        underperforming = report.get("underperforming_agents", [])
        if underperforming:
            recommendations.append(f"Review {len(underperforming)} underperforming agents")

        # General recommendations
        total_cost = report["summary"]["total_cost_usd"]
        if total_cost > 10.0:
            recommendations.append("Consider caching frequent operations to reduce costs")

        if not recommendations:
            recommendations.append("Cost optimization looks good")

        return recommendations


async def main():
    """Main entry point for agent registry server."""
    server = AgentRegistryServer()
    await server.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
