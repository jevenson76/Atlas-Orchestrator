#!/usr/bin/env python3
"""
Promote Existing Agents to Global Registry

Registers all existing agents from Priority 3 and Component C3 into the
global agent registry with proper model discipline and metadata.

Priority 3 Agents:
- Architect (CORE, OPUS)
- Developer (CORE, SONNET)
- Tester (CORE, SONNET)
- Reviewer (CORE, OPUS)

Component C3 Critics:
- Security Critic (CRITIC, OPUS)
- Performance Critic (CRITIC, OPUS)
- Architecture Critic (CRITIC, OPUS)
- Code Quality Critic (CRITIC, OPUS)
- Documentation Critic (CRITIC, OPUS)
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent_registry import AgentRegistry, AgentCategory, ModelTier

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def promote_all_agents():
    """Promote all existing agents to global registry."""
    registry = AgentRegistry()

    print("=" * 70)
    print("🚀 PROMOTING AGENTS TO GLOBAL REGISTRY")
    print("=" * 70)
    print()

    # ============ PRIORITY 3: SPECIALIZED ROLES ============
    print("📋 Registering Priority 3 Specialized Roles...")
    print()

    # 1. Architect (CORE, OPUS)
    registry.register_agent(
        name="architect",
        category=AgentCategory.CORE,
        model_tier=ModelTier.OPUS,
        description="System design and architecture planning. Creates high-level designs, technical specifications, and architectural diagrams.",
        use_cases=[
            "system architecture design",
            "technical specification creation",
            "design pattern selection",
            "scalability planning",
            "technology stack recommendations"
        ],
        estimated_cost_per_call=0.05,  # Opus, larger context
        estimated_time_seconds=30.0,
        quality_range=(85, 98)
    )
    print("  ✅ architect (CORE, OPUS)")

    # 2. Developer (CORE, SONNET)
    registry.register_agent(
        name="developer",
        category=AgentCategory.CORE,
        model_tier=ModelTier.SONNET,
        description="Code implementation and development. Writes production-quality code following best practices and design patterns.",
        use_cases=[
            "code implementation",
            "feature development",
            "bug fixes",
            "refactoring",
            "API development"
        ],
        estimated_cost_per_call=0.015,  # Sonnet, moderate context
        estimated_time_seconds=20.0,
        quality_range=(80, 95)
    )
    print("  ✅ developer (CORE, SONNET)")

    # 3. Tester (CORE, SONNET)
    registry.register_agent(
        name="tester",
        category=AgentCategory.CORE,
        model_tier=ModelTier.SONNET,
        description="Test generation and quality assurance. Creates comprehensive test suites with unit, integration, and edge case tests.",
        use_cases=[
            "test suite generation",
            "unit test creation",
            "integration test design",
            "edge case identification",
            "test coverage analysis"
        ],
        estimated_cost_per_call=0.012,  # Sonnet, focused context
        estimated_time_seconds=18.0,
        quality_range=(85, 95)
    )
    print("  ✅ tester (CORE, SONNET)")

    # 4. Reviewer (CORE, OPUS)
    registry.register_agent(
        name="reviewer",
        category=AgentCategory.CORE,
        model_tier=ModelTier.OPUS,
        description="Final code review and quality assessment. Provides comprehensive feedback on code quality, maintainability, and adherence to standards.",
        use_cases=[
            "code review",
            "quality assessment",
            "best practices validation",
            "maintainability analysis",
            "security review"
        ],
        estimated_cost_per_call=0.04,  # Opus, comprehensive review
        estimated_time_seconds=25.0,
        quality_range=(88, 98)
    )
    print("  ✅ reviewer (CORE, OPUS)")

    print()

    # ============ COMPONENT C3: CRITICS ============
    print("🔍 Registering Component C3 Critics...")
    print()

    # 5. Security Critic (CRITIC, OPUS)
    registry.register_agent(
        name="security-critic",
        category=AgentCategory.CRITIC,
        model_tier=ModelTier.OPUS,
        description="Deep security vulnerability analysis. Identifies security issues, compliance violations, and potential exploits.",
        use_cases=[
            "security vulnerability scanning",
            "SQL injection detection",
            "XSS vulnerability detection",
            "authentication/authorization review",
            "sensitive data exposure check",
            "OWASP Top 10 compliance"
        ],
        estimated_cost_per_call=0.06,  # Opus, thorough analysis
        estimated_time_seconds=35.0,
        quality_range=(90, 98)
    )
    print("  ✅ security-critic (CRITIC, OPUS)")

    # 6. Performance Critic (CRITIC, OPUS)
    registry.register_agent(
        name="performance-critic",
        category=AgentCategory.CRITIC,
        model_tier=ModelTier.OPUS,
        description="Performance analysis and optimization recommendations. Identifies bottlenecks, inefficient algorithms, and optimization opportunities.",
        use_cases=[
            "performance bottleneck identification",
            "algorithm complexity analysis",
            "database query optimization",
            "memory usage analysis",
            "caching strategy recommendations"
        ],
        estimated_cost_per_call=0.055,  # Opus, detailed analysis
        estimated_time_seconds=32.0,
        quality_range=(88, 97)
    )
    print("  ✅ performance-critic (CRITIC, OPUS)")

    # 7. Architecture Critic (CRITIC, OPUS)
    registry.register_agent(
        name="architecture-critic",
        category=AgentCategory.CRITIC,
        model_tier=ModelTier.OPUS,
        description="Architectural design review and pattern validation. Evaluates system design, scalability, and maintainability.",
        use_cases=[
            "architecture pattern validation",
            "scalability assessment",
            "coupling and cohesion analysis",
            "dependency management review",
            "design principle compliance"
        ],
        estimated_cost_per_call=0.058,  # Opus, high-level analysis
        estimated_time_seconds=33.0,
        quality_range=(90, 98)
    )
    print("  ✅ architecture-critic (CRITIC, OPUS)")

    # 8. Code Quality Critic (CRITIC, OPUS)
    registry.register_agent(
        name="code-quality-critic",
        category=AgentCategory.CRITIC,
        model_tier=ModelTier.OPUS,
        description="Code quality and maintainability assessment. Reviews code style, readability, and adherence to best practices.",
        use_cases=[
            "code style review",
            "naming convention validation",
            "code smell detection",
            "maintainability assessment",
            "technical debt identification"
        ],
        estimated_cost_per_call=0.05,  # Opus, focused review
        estimated_time_seconds=28.0,
        quality_range=(85, 96)
    )
    print("  ✅ code-quality-critic (CRITIC, OPUS)")

    # 9. Documentation Critic (CRITIC, OPUS)
    registry.register_agent(
        name="documentation-critic",
        category=AgentCategory.CRITIC,
        model_tier=ModelTier.OPUS,
        description="Documentation completeness and clarity review. Ensures documentation is comprehensive, accurate, and helpful.",
        use_cases=[
            "documentation completeness check",
            "docstring quality review",
            "API documentation validation",
            "README clarity assessment",
            "example code verification"
        ],
        estimated_cost_per_call=0.045,  # Opus, documentation focus
        estimated_time_seconds=26.0,
        quality_range=(82, 95)
    )
    print("  ✅ documentation-critic (CRITIC, OPUS)")

    print()

    # ============ ADDITIONAL AGENTS ============
    print("🔧 Registering Additional Specialized Agents...")
    print()

    # 10. Validation Orchestrator (SPECIALIZED, SONNET)
    registry.register_agent(
        name="validation-orchestrator",
        category=AgentCategory.SPECIALIZED,
        model_tier=ModelTier.SONNET,
        description="Code validation and quality gate enforcement. Runs multiple validators and aggregates results.",
        use_cases=[
            "code validation",
            "quality gate enforcement",
            "multi-validator aggregation",
            "validation result reporting"
        ],
        estimated_cost_per_call=0.02,  # Sonnet, orchestration
        estimated_time_seconds=22.0,
        quality_range=(80, 92)
    )
    print("  ✅ validation-orchestrator (SPECIALIZED, SONNET)")

    # 11. Master Orchestrator (SPECIALIZED, SONNET)
    registry.register_agent(
        name="master-orchestrator",
        category=AgentCategory.SPECIALIZED,
        model_tier=ModelTier.SONNET,
        description="Workflow routing and orchestration. Analyzes tasks and routes to optimal workflow.",
        use_cases=[
            "workflow selection",
            "task analysis",
            "workflow routing",
            "multi-workflow coordination"
        ],
        estimated_cost_per_call=0.01,  # Sonnet, routing logic
        estimated_time_seconds=8.0,
        quality_range=(85, 95)
    )
    print("  ✅ master-orchestrator (SPECIALIZED, SONNET)")

    print()

    # ============ SUMMARY ============
    print("=" * 70)
    print("📊 PROMOTION SUMMARY")
    print("=" * 70)

    stats = registry.get_all_stats()

    print(f"\n✅ Total Agents Registered: {stats['total_agents']}")
    print("\n📁 Agents by Category:")
    for category, count in stats['agents_by_category'].items():
        print(f"   - {category}: {count} agents")

    print("\n🤖 Agents by Model Tier:")
    agents_by_tier = {}
    for agent in registry.list_agents():
        tier = agent.model_tier.value
        if tier not in agents_by_tier:
            agents_by_tier[tier] = []
        agents_by_tier[tier].append(agent.name)

    for tier, agents in sorted(agents_by_tier.items()):
        print(f"   - {tier}: {len(agents)} agents")
        for agent_name in agents:
            print(f"      • {agent_name}")

    print("\n📍 Registry Location:")
    print(f"   {registry.registry_file}")

    print("\n✅ ALL AGENTS PROMOTED TO GLOBAL REGISTRY!")
    print("=" * 70)

    return registry


if __name__ == "__main__":
    promote_all_agents()
