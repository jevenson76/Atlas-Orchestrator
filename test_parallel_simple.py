"""
Simple Integration Tests for ParallelDevelopmentOrchestrator
(No pytest-asyncio required)
"""

import asyncio
import sys
from pathlib import Path

# Add library to path
sys.path.insert(0, str(Path(__file__).parent))

from parallel_development_orchestrator import ParallelDevelopmentOrchestrator
from specialized_roles_orchestrator import WorkflowResult


def test_orchestrator_initialization():
    """Test basic initialization."""
    print("\n✓ Test 1: Orchestrator Initialization")

    orchestrator = ParallelDevelopmentOrchestrator(
        project_root="/mnt/d/Dev",
        num_parallel_agents=3,
        quality_threshold=80
    )

    assert orchestrator.cluster is not None, "Cluster should be initialized"
    assert len(orchestrator.cluster.nodes) == 3, f"Expected 3 nodes, got {len(orchestrator.cluster.nodes)}"
    assert orchestrator.validator is not None, "Validator should be initialized"
    assert orchestrator.metrics is not None, "Metrics should be initialized"

    print(f"   - Cluster nodes: {len(orchestrator.cluster.nodes)}")
    print(f"   - Quality threshold: {orchestrator.quality_threshold}")
    print("   ✓ PASSED")


def test_cluster_status():
    """Test getting cluster status."""
    print("\n✓ Test 2: Cluster Status")

    orchestrator = ParallelDevelopmentOrchestrator(num_parallel_agents=3)
    status = orchestrator.get_cluster_status()

    assert "cluster_size" in status
    assert "online_nodes" in status
    assert status["cluster_size"] == 3

    print(f"   - Cluster size: {status['cluster_size']}")
    print(f"   - Online nodes: {status['online_nodes']}")
    print("   ✓ PASSED")


def test_code_detection():
    """Test code result detection."""
    print("\n✓ Test 3: Code Detection")

    orchestrator = ParallelDevelopmentOrchestrator(num_parallel_agents=2)

    # Should detect code
    assert orchestrator._is_code_result({"code": "def test(): pass"})
    assert orchestrator._is_code_result({"generated": "print('hello')"})
    assert orchestrator._is_code_result("x" * 51)

    # Should not detect code
    assert not orchestrator._is_code_result({"data": "123"})
    assert not orchestrator._is_code_result("short")

    print("   - Code detection working correctly")
    print("   ✓ PASSED")


def test_cost_estimation():
    """Test cost estimation."""
    print("\n✓ Test 4: Cost Estimation")

    orchestrator = ParallelDevelopmentOrchestrator(num_parallel_agents=2)

    cost_1k = orchestrator._estimate_cost(1000)
    cost_10k = orchestrator._estimate_cost(10000)

    assert cost_1k > 0, "Cost should be positive"
    assert cost_10k > cost_1k, "More tokens should cost more"

    print(f"   - Cost for 1k tokens: ${cost_1k:.6f}")
    print(f"   - Cost for 10k tokens: ${cost_10k:.6f}")
    print("   ✓ PASSED")


def test_simple_workflow():
    """Test executing a simple workflow."""
    print("\n✓ Test 5: Simple Workflow Execution")

    orchestrator = ParallelDevelopmentOrchestrator(
        num_parallel_agents=3,
        quality_threshold=75
    )

    task = "Create a simple calculator with add and subtract functions"

    # Run async workflow in sync context
    result = asyncio.run(orchestrator.execute_workflow(task))

    assert isinstance(result, WorkflowResult), "Should return WorkflowResult"
    assert result.task == task, "Task should match"
    assert result.total_execution_time_ms > 0, "Duration should be positive"
    assert result.context is not None, "Context should exist"
    assert result.context.get("workflow_metadata", {}).get("workflow_type") == "parallel_development"

    print(f"   - Task: {task[:50]}...")
    print(f"   - Duration: {result.total_execution_time_ms/1000:.2f}s")
    print(f"   - Quality: {result.overall_quality_score}/100")
    print(f"   - Has developer_result: {result.developer_result is not None}")
    print("   ✓ PASSED")


def test_workflow_metadata():
    """Test workflow metadata structure."""
    print("\n✓ Test 6: Workflow Metadata")

    orchestrator = ParallelDevelopmentOrchestrator(num_parallel_agents=3)
    task = "Simple task"

    result = asyncio.run(orchestrator.execute_workflow(task))

    # Check metadata fields (stored in context["workflow_metadata"])
    metadata = result.context.get("workflow_metadata", {})
    assert "workflow_type" in metadata
    assert "num_agents" in metadata
    assert "packages_executed" in metadata
    assert "parallel_speedup" in metadata
    assert "time_saved_seconds" in metadata
    assert "consensus_type" in metadata

    print(f"   - Workflow type: {metadata.get('workflow_type')}")
    print(f"   - Agents: {metadata.get('num_agents')}")
    print(f"   - Packages: {metadata.get('packages_executed')}")
    print(f"   - Speedup: {metadata.get('parallel_speedup', 0):.1f}x")
    print("   ✓ PASSED")


def test_scaling():
    """Test cluster scaling."""
    print("\n✓ Test 7: Cluster Scaling")

    orchestrator = ParallelDevelopmentOrchestrator(num_parallel_agents=3)

    initial_size = len(orchestrator.cluster.nodes)
    print(f"   - Initial size: {initial_size}")

    # Scale up
    asyncio.run(orchestrator.scale_agents(5))
    assert len(orchestrator.cluster.nodes) == 5
    print(f"   - After scale up: {len(orchestrator.cluster.nodes)}")

    # Scale down
    asyncio.run(orchestrator.scale_agents(2))
    assert len(orchestrator.cluster.nodes) == 2
    print(f"   - After scale down: {len(orchestrator.cluster.nodes)}")

    print("   ✓ PASSED")


def test_workflow_result_structure():
    """Test WorkflowResult structure."""
    print("\n✓ Test 8: WorkflowResult Structure")

    orchestrator = ParallelDevelopmentOrchestrator(num_parallel_agents=2)
    result = asyncio.run(orchestrator.execute_workflow("Test task"))

    # Check required attributes (matching specialized_roles_orchestrator.py structure)
    required_attrs = [
        "task", "context", "overall_quality_score", "total_execution_time_ms",
        "total_cost_usd", "success", "developer_result"
    ]

    for attr in required_attrs:
        assert hasattr(result, attr), f"Missing attribute: {attr}"
        print(f"   - {attr}: ✓")

    # Check developer_result phase
    if result.developer_result:
        phase = result.developer_result
        phase_attrs = ["phase", "role", "output", "quality_score", "tokens_used", "cost_usd", "execution_time_ms"]
        for attr in phase_attrs:
            assert hasattr(phase, attr), f"Phase missing attribute: {attr}"
    else:
        print("   - Warning: No developer_result")

    print("   ✓ PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("🧪 TESTING PARALLEL DEVELOPMENT ORCHESTRATOR")
    print("=" * 70)

    tests = [
        test_orchestrator_initialization,
        test_cluster_status,
        test_code_detection,
        test_cost_estimation,
        test_simple_workflow,
        test_workflow_metadata,
        test_scaling,
        test_workflow_result_structure,
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
