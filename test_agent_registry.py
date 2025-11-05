"""
Comprehensive Tests for Agent Registry System

Tests coverage for:
- Agent registration with valid metadata
- Model discipline enforcement
- Usage tracking and statistics aggregation
- Agent discovery by various filters
- Model recommendation logic
- Registry persistence (save/load)
- Integration helpers
"""

import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent_registry import (
    AgentRegistry,
    AgentMetadata,
    AgentCategory,
    ModelTier,
    ModelDisciplineViolationError
)
from agent_discovery import AgentDiscovery
from agent_registry_integration import AgentUsageTracker


def test_registry_initialization():
    """Test 1: Registry initialization"""
    print("\n✓ Test 1: Registry Initialization")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        assert len(registry.agents) == 0
        assert registry.registry_dir == Path(tmpdir)
        assert registry.registry_file.parent == Path(tmpdir)

    print("   - Registry initialized correctly ✓")
    print("   ✓ PASSED")


def test_agent_registration():
    """Test 2: Agent registration with valid metadata"""
    print("\n✓ Test 2: Agent Registration")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register an agent
        metadata = registry.register_agent(
            name="test-developer",
            category=AgentCategory.CORE,
            model_tier=ModelTier.SONNET,
            description="Test developer agent",
            use_cases=["testing", "development"],
            estimated_cost_per_call=0.015,
            estimated_time_seconds=20.0,
            quality_range=(80, 95)
        )

        assert metadata.name == "test-developer"
        assert metadata.category == AgentCategory.CORE
        assert metadata.model_tier == ModelTier.SONNET
        assert len(registry.agents) == 1

    print("   - Agent registered with correct metadata ✓")
    print("   ✓ PASSED")


def test_model_discipline_critic_must_use_opus():
    """Test 3: Model discipline - critics MUST use Opus"""
    print("\n✓ Test 3: Model Discipline (Critic → Opus)")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Try to register critic with Haiku (should fail)
        try:
            registry.register_agent(
                name="bad-critic",
                category=AgentCategory.CRITIC,
                model_tier=ModelTier.HAIKU,  # WRONG!
                description="Bad critic",
                use_cases=["testing"],
                estimated_cost_per_call=0.001,
                estimated_time_seconds=5.0,
                quality_range=(70, 85)
            )
            assert False, "Should have raised ModelDisciplineViolationError"
        except ModelDisciplineViolationError as e:
            assert "CRITIC" in str(e)
            assert "MUST use Opus" in str(e)

    print("   - Rejected non-Opus critic ✓")
    print("   ✓ PASSED")


def test_model_discipline_critic_opus_accepted():
    """Test 4: Model discipline - critics with Opus accepted"""
    print("\n✓ Test 4: Model Discipline (Critic with Opus OK)")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register critic with Opus (should succeed)
        metadata = registry.register_agent(
            name="good-critic",
            category=AgentCategory.CRITIC,
            model_tier=ModelTier.OPUS,  # Correct
            description="Good critic",
            use_cases=["critique"],
            estimated_cost_per_call=0.05,
            estimated_time_seconds=30.0,
            quality_range=(90, 98)
        )

        assert metadata.name == "good-critic"
        assert metadata.model_tier == ModelTier.OPUS

    print("   - Accepted Opus critic ✓")
    print("   ✓ PASSED")


def test_usage_tracking():
    """Test 5: Usage tracking and statistics"""
    print("\n✓ Test 5: Usage Tracking")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agent
        registry.register_agent(
            name="test-agent",
            category=AgentCategory.CORE,
            model_tier=ModelTier.SONNET,
            description="Test",
            use_cases=["testing"],
            estimated_cost_per_call=0.01,
            estimated_time_seconds=10.0,
            quality_range=(80, 90)
        )

        # Record usage
        registry.record_usage("test-agent", cost_usd=0.012, execution_time_seconds=11.5, quality_score=85)
        registry.record_usage("test-agent", cost_usd=0.011, execution_time_seconds=10.2, quality_score=87)

        # Check statistics
        stats = registry.get_agent_stats("test-agent")
        assert stats['total_invocations'] == 2
        assert stats['total_cost_usd'] == 0.023
        assert stats['average_quality_score'] == 86.0  # (85 + 87) / 2

    print("   - Usage recorded correctly ✓")
    print("   - Statistics calculated correctly ✓")
    print("   ✓ PASSED")


def test_model_recommendation():
    """Test 6: Model tier recommendation logic"""
    print("\n✓ Test 6: Model Recommendation")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # High volume, simple → Haiku
        model1 = registry.recommend_model(
            task_complexity="simple",
            volume="high",
            requires_judgment=False
        )
        assert model1 == ModelTier.HAIKU

        # Complex, requires judgment → Opus
        model2 = registry.recommend_model(
            task_complexity="complex",
            volume="low",
            requires_judgment=True
        )
        assert model2 == ModelTier.OPUS

        # Moderate → Sonnet
        model3 = registry.recommend_model(
            task_complexity="moderate",
            volume="medium",
            requires_judgment=False
        )
        assert model3 == ModelTier.SONNET

    print("   - High volume/simple → Haiku ✓")
    print("   - Complex/judgment → Opus ✓")
    print("   - Moderate → Sonnet ✓")
    print("   ✓ PASSED")


def test_registry_persistence():
    """Test 7: Registry save and load"""
    print("\n✓ Test 7: Registry Persistence")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and populate registry
        registry1 = AgentRegistry(registry_dir=Path(tmpdir))

        registry1.register_agent(
            name="persist-test",
            category=AgentCategory.CORE,
            model_tier=ModelTier.SONNET,
            description="Persistence test",
            use_cases=["testing"],
            estimated_cost_per_call=0.01,
            estimated_time_seconds=10.0,
            quality_range=(80, 90)
        )

        # Record some usage
        registry1.record_usage("persist-test", cost_usd=0.012, execution_time_seconds=11.0, quality_score=85)

        # Create new registry instance (should load from file)
        registry2 = AgentRegistry(registry_dir=Path(tmpdir))

        assert len(registry2.agents) == 1
        assert "persist-test" in registry2.agents
        agent = registry2.get_agent("persist-test")
        assert agent.total_invocations == 1
        assert agent.total_cost_usd == 0.012

    print("   - Registry saved to file ✓")
    print("   - Registry loaded from file ✓")
    print("   - Usage statistics persisted ✓")
    print("   ✓ PASSED")


def test_list_agents_by_category():
    """Test 8: List agents by category"""
    print("\n✓ Test 8: List Agents by Category")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agents in different categories
        registry.register_agent("core-1", AgentCategory.CORE, ModelTier.SONNET, "Core agent 1", ["test"], 0.01, 10.0, (80, 90))
        registry.register_agent("core-2", AgentCategory.CORE, ModelTier.OPUS, "Core agent 2", ["test"], 0.05, 30.0, (85, 95))
        registry.register_agent("critic-1", AgentCategory.CRITIC, ModelTier.OPUS, "Critic 1", ["test"], 0.06, 35.0, (90, 98))

        # List core agents
        core_agents = registry.list_agents(category=AgentCategory.CORE)
        assert len(core_agents) == 2

        # List critics
        critics = registry.list_agents(category=AgentCategory.CRITIC)
        assert len(critics) == 1
        assert critics[0].name == "critic-1"

    print("   - Filtered by CORE category ✓")
    print("   - Filtered by CRITIC category ✓")
    print("   ✓ PASSED")


def test_list_agents_by_model_tier():
    """Test 9: List agents by model tier"""
    print("\n✓ Test 9: List Agents by Model Tier")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agents with different models
        registry.register_agent("haiku-agent", AgentCategory.CORE, ModelTier.HAIKU, "Haiku", ["test"], 0.001, 5.0, (70, 85))
        registry.register_agent("sonnet-agent", AgentCategory.CORE, ModelTier.SONNET, "Sonnet", ["test"], 0.01, 10.0, (80, 92))
        registry.register_agent("opus-agent", AgentCategory.CRITIC, ModelTier.OPUS, "Opus", ["test"], 0.05, 30.0, (90, 98))

        # List Opus agents
        opus_agents = registry.list_agents(model_tier=ModelTier.OPUS)
        assert len(opus_agents) == 1
        assert opus_agents[0].name == "opus-agent"

        # List Sonnet agents
        sonnet_agents = registry.list_agents(model_tier=ModelTier.SONNET)
        assert len(sonnet_agents) == 1

    print("   - Filtered by OPUS tier ✓")
    print("   - Filtered by SONNET tier ✓")
    print("   ✓ PASSED")


def test_agent_discovery_by_use_case():
    """Test 10: Agent discovery by use case"""
    print("\n✓ Test 10: Agent Discovery by Use Case")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))
        discovery = AgentDiscovery(registry=registry)

        # Register agents with different use cases
        registry.register_agent(
            "security-agent",
            AgentCategory.CRITIC,
            ModelTier.OPUS,
            "Security expert",
            ["security review", "vulnerability scanning"],
            0.06, 35.0, (90, 98)
        )
        registry.register_agent(
            "performance-agent",
            AgentCategory.CRITIC,
            ModelTier.OPUS,
            "Performance expert",
            ["performance analysis", "optimization"],
            0.055, 32.0, (88, 97)
        )

        # Search by use case
        security_agents = discovery.find_agents(use_case="security")
        assert len(security_agents) == 1
        assert security_agents[0].name == "security-agent"

        performance_agents = discovery.find_agents(use_case="performance")
        assert len(performance_agents) == 1
        assert performance_agents[0].name == "performance-agent"

    print("   - Found security-focused agent ✓")
    print("   - Found performance-focused agent ✓")
    print("   ✓ PASSED")


def test_agent_discovery_recommend():
    """Test 11: Agent recommendation for task"""
    print("\n✓ Test 11: Agent Recommendation")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))
        discovery = AgentDiscovery(registry=registry)

        # Register agents
        registry.register_agent(
            "security-agent",
            AgentCategory.CRITIC,
            ModelTier.OPUS,
            "Security expert",
            ["security", "vulnerability"],
            0.06, 35.0, (90, 98)
        )
        registry.register_agent(
            "developer-agent",
            AgentCategory.CORE,
            ModelTier.SONNET,
            "Developer",
            ["implementation", "coding"],
            0.015, 20.0, (80, 92)
        )

        # Recommend for security task
        security_task = "Review this code for SQL injection vulnerabilities"
        recommended = discovery.recommend_agent(security_task, quality_target=90)
        assert recommended is not None
        assert "security" in recommended.name.lower() or "security" in str(recommended.use_cases).lower()

    print("   - Recommended correct agent for security task ✓")
    print("   ✓ PASSED")


def test_agent_discovery_by_cost():
    """Test 12: Find agents by cost budget"""
    print("\n✓ Test 12: Find Agents by Cost")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))
        discovery = AgentDiscovery(registry=registry)

        # Register agents with different costs
        registry.register_agent("cheap", AgentCategory.CORE, ModelTier.HAIKU, "Cheap", ["test"], 0.001, 5.0, (70, 85))
        registry.register_agent("mid", AgentCategory.CORE, ModelTier.SONNET, "Mid", ["test"], 0.015, 10.0, (80, 92))
        registry.register_agent("expensive", AgentCategory.CRITIC, ModelTier.OPUS, "Expensive", ["test"], 0.06, 30.0, (90, 98))

        # Find agents under $0.02
        affordable = discovery.get_agents_by_cost(max_cost=0.02)
        assert len(affordable) == 2
        assert all(a.estimated_cost_per_call <= 0.02 for a in affordable)
        # Should be sorted by cost (cheapest first)
        assert affordable[0].estimated_cost_per_call <= affordable[1].estimated_cost_per_call

    print("   - Found agents within budget ✓")
    print("   - Sorted by cost (cheapest first) ✓")
    print("   ✓ PASSED")


def test_agent_discovery_by_quality():
    """Test 13: Find agents by quality threshold"""
    print("\n✓ Test 13: Find Agents by Quality")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))
        discovery = AgentDiscovery(registry=registry)

        # Register agents with different quality ranges
        registry.register_agent("low-q", AgentCategory.CORE, ModelTier.HAIKU, "Low Q", ["test"], 0.001, 5.0, (70, 85))
        registry.register_agent("mid-q", AgentCategory.CORE, ModelTier.SONNET, "Mid Q", ["test"], 0.015, 10.0, (80, 92))
        registry.register_agent("high-q", AgentCategory.CRITIC, ModelTier.OPUS, "High Q", ["test"], 0.06, 30.0, (90, 98))

        # Find agents with quality >= 90
        # Note: Finds agents where max quality >= threshold, so both high-q (98) and mid-q (92) qualify
        high_quality = discovery.get_agents_by_quality(min_quality=90)
        assert len(high_quality) >= 1
        # Should be sorted by quality (highest first)
        assert high_quality[0].quality_range[1] >= 90
        # Highest quality agent should be first
        assert high_quality[0].name == "high-q"

    print("   - Found high-quality agents ✓")
    print("   - Sorted by quality (highest first) ✓")
    print("   ✓ PASSED")


def test_agent_capabilities():
    """Test 14: Get agent capabilities"""
    print("\n✓ Test 14: Get Agent Capabilities")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))
        discovery = AgentDiscovery(registry=registry)

        # Register agent
        registry.register_agent(
            "test-agent",
            AgentCategory.CORE,
            ModelTier.SONNET,
            "Test agent",
            ["testing", "validation"],
            0.015, 20.0, (80, 92),
            version="2.0.0"
        )

        # Get capabilities
        caps = discovery.get_agent_capabilities("test-agent")
        assert caps is not None
        assert caps['name'] == "test-agent"
        assert caps['model'] == ModelTier.SONNET.value
        assert caps['category'] == AgentCategory.CORE.value
        assert len(caps['use_cases']) == 2
        assert caps['version'] == "2.0.0"

    print("   - Retrieved complete capabilities ✓")
    print("   - Included use cases and metadata ✓")
    print("   ✓ PASSED")


def test_usage_tracker_integration():
    """Test 15: AgentUsageTracker integration"""
    print("\n✓ Test 15: Usage Tracker Integration")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agent
        registry.register_agent(
            "tracker-test",
            AgentCategory.CORE,
            ModelTier.SONNET,
            "Test",
            ["testing"],
            0.01, 10.0, (80, 90)
        )

        # Use tracker
        tracker = AgentUsageTracker(registry=registry)
        tracker.record(
            agent_name="tracker-test",
            cost_usd=0.012,
            execution_time_seconds=11.0,
            quality_score=85
        )

        # Verify recorded
        stats = registry.get_agent_stats("tracker-test")
        assert stats['total_invocations'] == 1
        assert stats['total_cost_usd'] == 0.012

    print("   - Tracker recorded usage ✓")
    print("   - Statistics updated ✓")
    print("   ✓ PASSED")


def test_aggregate_statistics():
    """Test 16: Aggregate statistics across agents"""
    print("\n✓ Test 16: Aggregate Statistics")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register multiple agents
        registry.register_agent("agent1", AgentCategory.CORE, ModelTier.SONNET, "A1", ["test"], 0.01, 10.0, (80, 90))
        registry.register_agent("agent2", AgentCategory.CRITIC, ModelTier.OPUS, "A2", ["test"], 0.05, 30.0, (90, 98))

        # Record usage
        registry.record_usage("agent1", 0.012, 11.0, 85)
        registry.record_usage("agent2", 0.048, 29.0, 94)
        registry.record_usage("agent1", 0.011, 10.5, 87)

        # Get aggregate stats
        stats = registry.get_all_stats()
        assert stats['total_agents'] == 2
        assert stats['total_invocations'] == 3
        # Use tolerance for floating point comparison
        assert abs(stats['total_cost_usd'] - 0.071) < 0.0001  # 0.012 + 0.048 + 0.011

    print("   - Total agents count correct ✓")
    print("   - Total invocations correct ✓")
    print("   - Total cost aggregated correctly ✓")
    print("   ✓ PASSED")


def test_most_used_agents():
    """Test 17: Most used agents ranking"""
    print("\n✓ Test 17: Most Used Agents")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agents
        registry.register_agent("popular", AgentCategory.CORE, ModelTier.SONNET, "Pop", ["test"], 0.01, 10.0, (80, 90))
        registry.register_agent("rare", AgentCategory.CORE, ModelTier.SONNET, "Rare", ["test"], 0.01, 10.0, (80, 90))

        # Record usage (popular used 3x, rare used 1x)
        registry.record_usage("popular", 0.01, 10.0, 85)
        registry.record_usage("popular", 0.01, 10.0, 86)
        registry.record_usage("popular", 0.01, 10.0, 87)
        registry.record_usage("rare", 0.01, 10.0, 80)

        # Get stats
        stats = registry.get_all_stats()
        most_used = stats['most_used_agents']

        assert len(most_used) >= 2
        # Most used should be first
        assert most_used[0]['name'] == "popular"
        assert most_used[0]['invocations'] == 3

    print("   - Ranked agents by usage ✓")
    print("   - Most popular agent identified ✓")
    print("   ✓ PASSED")


def test_cost_by_model_tier():
    """Test 18: Cost breakdown by model tier"""
    print("\n✓ Test 18: Cost by Model Tier")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agents with different tiers
        registry.register_agent("sonnet-1", AgentCategory.CORE, ModelTier.SONNET, "S1", ["test"], 0.01, 10.0, (80, 90))
        registry.register_agent("opus-1", AgentCategory.CRITIC, ModelTier.OPUS, "O1", ["test"], 0.05, 30.0, (90, 98))

        # Record usage
        registry.record_usage("sonnet-1", 0.012, 11.0, 85)
        registry.record_usage("opus-1", 0.048, 29.0, 94)
        registry.record_usage("sonnet-1", 0.011, 10.5, 87)

        # Get cost breakdown
        stats = registry.get_all_stats()
        cost_by_tier = stats['cost_by_model_tier']

        assert ModelTier.SONNET.value in cost_by_tier
        assert ModelTier.OPUS.value in cost_by_tier
        assert cost_by_tier[ModelTier.SONNET.value] == 0.023  # 0.012 + 0.011
        assert cost_by_tier[ModelTier.OPUS.value] == 0.048

    print("   - Cost breakdown by tier calculated ✓")
    print("   - Sonnet costs aggregated ✓")
    print("   - Opus costs aggregated ✓")
    print("   ✓ PASSED")


def test_agents_by_category_count():
    """Test 19: Count agents by category"""
    print("\n✓ Test 19: Agents by Category Count")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agents in different categories
        registry.register_agent("core-1", AgentCategory.CORE, ModelTier.SONNET, "C1", ["test"], 0.01, 10.0, (80, 90))
        registry.register_agent("core-2", AgentCategory.CORE, ModelTier.OPUS, "C2", ["test"], 0.05, 30.0, (85, 95))
        registry.register_agent("critic-1", AgentCategory.CRITIC, ModelTier.OPUS, "Cr1", ["test"], 0.06, 35.0, (90, 98))
        registry.register_agent("specialized-1", AgentCategory.SPECIALIZED, ModelTier.SONNET, "S1", ["test"], 0.02, 15.0, (82, 92))

        # Get category counts
        stats = registry.get_all_stats()
        by_category = stats['agents_by_category']

        assert by_category[AgentCategory.CORE.value] == 2
        assert by_category[AgentCategory.CRITIC.value] == 1
        assert by_category[AgentCategory.SPECIALIZED.value] == 1

    print("   - Core agents counted ✓")
    print("   - Critic agents counted ✓")
    print("   - Specialized agents counted ✓")
    print("   ✓ PASSED")


def test_quality_score_averaging():
    """Test 20: Quality score running average"""
    print("\n✓ Test 20: Quality Score Averaging")

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir))

        # Register agent
        registry.register_agent("avg-test", AgentCategory.CORE, ModelTier.SONNET, "Test", ["test"], 0.01, 10.0, (80, 90))

        # Record usage with different quality scores
        registry.record_usage("avg-test", 0.01, 10.0, 80)
        registry.record_usage("avg-test", 0.01, 10.0, 90)
        registry.record_usage("avg-test", 0.01, 10.0, 85)

        # Check average
        stats = registry.get_agent_stats("avg-test")
        expected_avg = (80 + 90 + 85) / 3
        assert abs(stats['average_quality_score'] - expected_avg) < 0.01

    print("   - Running average calculated correctly ✓")
    print("   - Average = 85.0 as expected ✓")
    print("   ✓ PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("🧪 TESTING AGENT REGISTRY SYSTEM")
    print("=" * 70)

    tests = [
        test_registry_initialization,
        test_agent_registration,
        test_model_discipline_critic_must_use_opus,
        test_model_discipline_critic_opus_accepted,
        test_usage_tracking,
        test_model_recommendation,
        test_registry_persistence,
        test_list_agents_by_category,
        test_list_agents_by_model_tier,
        test_agent_discovery_by_use_case,
        test_agent_discovery_recommend,
        test_agent_discovery_by_cost,
        test_agent_discovery_by_quality,
        test_agent_capabilities,
        test_usage_tracker_integration,
        test_aggregate_statistics,
        test_most_used_agents,
        test_cost_by_model_tier,
        test_agents_by_category_count,
        test_quality_score_averaging,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
