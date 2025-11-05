"""
Simple Tests for AgenticDropZone
(Tests structure and logic, not actual workflow execution)
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent))

from agentic_dropzone import AgenticDropZone
from specialized_roles_orchestrator import WorkflowResult, PhaseResult, WorkflowPhase
from role_definitions import Role, RoleType


def test_initialization():
    """Test ADZ initialization with custom dropzone root."""
    print("\n✓ Test 1: ADZ Initialization")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Check directories created
        assert adz.tasks_dir.exists()
        assert adz.results_dir.exists()
        assert adz.archive_dir.exists()

        # Check paths
        assert adz.tasks_dir == Path(tmpdir) / "tasks"
        assert adz.results_dir == Path(tmpdir) / "results"
        assert adz.archive_dir == Path(tmpdir) / "archive"

        # Check components initialized
        assert adz.master is not None
        assert adz.metrics is not None

        print(f"   - Tasks dir: {adz.tasks_dir} ✓")
        print(f"   - Results dir: {adz.results_dir} ✓")
        print(f"   - Archive dir: {adz.archive_dir} ✓")
        print("   ✓ PASSED")


def test_task_file_parsing():
    """Test task file parsing and validation."""
    print("\n✓ Test 2: Task File Parsing")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Create valid task file
        task_file = adz.tasks_dir / "test_task.json"
        task_data = {
            "task": "Create a calculator",
            "workflow": "progressive",
            "context": {"language": "python"},
            "priority": "normal"
        }

        with open(task_file, 'w') as f:
            json.dump(task_data, f)

        # Parse task
        parsed = adz._read_task_file(task_file)

        assert parsed["task"] == "Create a calculator"
        assert parsed["workflow"] == "progressive"
        assert parsed["context"]["language"] == "python"
        assert parsed["priority"] == "normal"

        print("   - Valid task parsed correctly ✓")
        print("   ✓ PASSED")


def test_task_file_defaults():
    """Test that defaults are applied to task files."""
    print("\n✓ Test 3: Task File Defaults")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Create minimal task file (only required 'task' field)
        task_file = adz.tasks_dir / "minimal_task.json"
        task_data = {
            "task": "Simple task"
        }

        with open(task_file, 'w') as f:
            json.dump(task_data, f)

        # Parse task
        parsed = adz._read_task_file(task_file)

        # Check defaults applied
        assert parsed["workflow"] == "auto"
        assert parsed["context"] == {}
        assert parsed["priority"] == "normal"

        print("   - Default workflow: auto ✓")
        print("   - Default context: {} ✓")
        print("   - Default priority: normal ✓")
        print("   ✓ PASSED")


def test_invalid_json():
    """Test error handling for invalid JSON."""
    print("\n✓ Test 4: Invalid JSON Handling")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Create invalid JSON file
        task_file = adz.tasks_dir / "invalid.json"
        with open(task_file, 'w') as f:
            f.write("{ this is not valid json }")

        # Should raise ValueError
        try:
            adz._read_task_file(task_file)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid JSON" in str(e)
            print(f"   - Caught error: {e} ✓")

        print("   ✓ PASSED")


def test_missing_task_field():
    """Test error handling for missing required field."""
    print("\n✓ Test 5: Missing Required Field")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Create task file without 'task' field
        task_file = adz.tasks_dir / "no_task.json"
        task_data = {
            "workflow": "auto",
            "context": {}
        }

        with open(task_file, 'w') as f:
            json.dump(task_data, f)

        # Should raise ValueError
        try:
            adz._read_task_file(task_file)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Missing required field: 'task'" in str(e)
            print(f"   - Caught error: {e} ✓")

        print("   ✓ PASSED")


def test_result_saving():
    """Test result file creation."""
    print("\n✓ Test 6: Result Saving")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Create mock Role
        mock_role = Role(
            name="Developer",
            role_type=RoleType.DEVELOPER,
            description="Mock developer",
            responsibilities=["coding"],
            primary_model="claude-3-5-sonnet-20241022",
            fallback_models=[],
            temperature=0.7,
            max_tokens=4096,
            estimated_cost_per_1m=(3.0, 15.0),
            system_prompt="You are a developer",
            output_format="code"
        )

        # Create mock WorkflowResult
        result = WorkflowResult(
            task="Test task",
            context={"workflow_metadata": {"selected_workflow": "progressive"}},
            developer_result=PhaseResult(
                phase=WorkflowPhase.DEVELOPER,
                role=mock_role,
                output="def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
                success=True,
                execution_time_ms=1000,
                tokens_used=500,
                cost_usd=0.001,
                model_used="claude-3-5-sonnet-20241022",
                quality_score=85
            ),
            overall_quality_score=85,
            total_execution_time_ms=1500,
            total_cost_usd=0.002,
            success=True  # Set WorkflowResult.success to True
        )

        task_data = {
            "task": "Test task",
            "workflow": "progressive"
        }

        # Save results
        adz._save_results("test_task", result, task_data)

        # Check result file created
        result_file = adz.results_dir / "test_task_result.json"
        assert result_file.exists()

        # Check result contents
        with open(result_file, 'r') as f:
            saved = json.load(f)

        assert saved["task_id"] == "test_task"
        assert saved["status"] == "success"
        assert saved["quality_score"] == 85
        assert saved["workflow_used"] == "progressive"
        assert "def factorial" in saved["output"]

        print("   - Result file created ✓")
        print("   - All fields present ✓")
        print("   ✓ PASSED")


def test_error_saving():
    """Test error file creation."""
    print("\n✓ Test 7: Error Saving")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        task_data = {
            "task": "Test task",
            "workflow": "auto"
        }

        # Save error
        adz._save_error("test_error", "Something went wrong", task_data)

        # Check error file created
        error_file = adz.results_dir / "test_error_error.json"
        assert error_file.exists()

        # Check error contents
        with open(error_file, 'r') as f:
            saved = json.load(f)

        assert saved["task_id"] == "test_error"
        assert saved["status"] == "failed"
        assert saved["error"] == "Something went wrong"
        assert saved["task"] == "Test task"

        print("   - Error file created ✓")
        print("   - All fields present ✓")
        print("   ✓ PASSED")


def test_task_archiving():
    """Test task file archiving."""
    print("\n✓ Test 8: Task Archiving")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Create task file
        task_file = adz.tasks_dir / "archive_test.json"
        task_file.write_text('{"task": "Test"}')

        assert task_file.exists()

        # Archive it
        adz._archive_task(task_file)

        # Check moved to archive
        assert not task_file.exists()
        archived = adz.archive_dir / "archive_test.json"
        assert archived.exists()
        assert archived.read_text() == '{"task": "Test"}'

        print("   - Task moved to archive ✓")
        print("   - Original removed ✓")
        print("   ✓ PASSED")


def test_status_reporting():
    """Test ADZ status reporting."""
    print("\n✓ Test 9: Status Reporting")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Initial status
        status = adz.status()

        assert status["running"] is False
        assert status["tasks_processed"] == 0
        assert status["tasks_failed"] == 0
        assert status["success_rate"] == 0.0

        # Simulate processing
        adz.tasks_processed = 8
        adz.tasks_failed = 2

        status = adz.status()
        assert status["tasks_processed"] == 8
        assert status["tasks_failed"] == 2
        assert status["success_rate"] == 80.0  # 8 / (8 + 2) * 100

        print("   - Initial status correct ✓")
        print("   - Success rate calculation correct ✓")
        print("   ✓ PASSED")


def test_output_extraction():
    """Test output extraction from WorkflowResult."""
    print("\n✓ Test 10: Output Extraction")

    with tempfile.TemporaryDirectory() as tmpdir:
        adz = AgenticDropZone(dropzone_root=Path(tmpdir))

        # Create mock Role
        mock_role = Role(
            name="Developer",
            role_type=RoleType.DEVELOPER,
            description="Mock",
            responsibilities=["coding"],
            primary_model="claude-3-5-sonnet-20241022",
            fallback_models=[],
            temperature=0.7,
            max_tokens=4096,
            estimated_cost_per_1m=(3.0, 15.0),
            system_prompt="You are a developer",
            output_format="code"
        )

        # Test with developer_result
        result1 = WorkflowResult(
            task="Test",
            context={},
            developer_result=PhaseResult(
                phase=WorkflowPhase.DEVELOPER,
                role=mock_role,
                output="code from developer",
                success=True,
                execution_time_ms=1000,
                tokens_used=500,
                cost_usd=0.001,
                model_used="claude-3-5-sonnet-20241022",
                quality_score=85
            )
        )

        output1 = adz._extract_output(result1)
        assert output1 == "code from developer"

        # Test with architect_result fallback
        mock_architect_role = Role(
            name="Architect",
            role_type=RoleType.ARCHITECT,
            description="Mock",
            responsibilities=["design"],
            primary_model="claude-3-opus-20240229",
            fallback_models=[],
            temperature=0.7,
            max_tokens=4096,
            estimated_cost_per_1m=(15.0, 75.0),
            system_prompt="You are an architect",
            output_format="structured"
        )

        result2 = WorkflowResult(
            task="Test",
            context={},
            architect_result=PhaseResult(
                phase=WorkflowPhase.ARCHITECT,
                role=mock_architect_role,
                output="design from architect",
                success=True,
                execution_time_ms=1000,
                tokens_used=500,
                cost_usd=0.001,
                model_used="claude-3-opus-20240229",
                quality_score=90
            )
        )

        output2 = adz._extract_output(result2)
        assert output2 == "design from architect"

        # Test with no results
        result3 = WorkflowResult(task="Test", context={})
        output3 = adz._extract_output(result3)
        assert output3 == "No output generated"

        print("   - Developer output extraction ✓")
        print("   - Architect fallback ✓")
        print("   - No output handling ✓")
        print("   ✓ PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("🧪 TESTING AGENTIC DROP ZONE")
    print("=" * 70)

    tests = [
        test_initialization,
        test_task_file_parsing,
        test_task_file_defaults,
        test_invalid_json,
        test_missing_task_field,
        test_result_saving,
        test_error_saving,
        test_task_archiving,
        test_status_reporting,
        test_output_extraction,
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
