#!/usr/bin/env python3
"""
ADZ System Verification Test
Quick verification that the Agentic Drop Zone system is properly configured.

Tests:
1. Directory structure exists
2. Core ADZ module can be imported
3. Task format parsing works
4. Documentation is present
5. Scripts are executable
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def test_directory_structure():
    """Test 1: Verify ADZ directory structure exists."""
    print("\n" + "=" * 80)
    print("TEST 1: Directory Structure Verification")
    print("=" * 80)

    dropzone_root = Path.home() / "dropzone"
    required_dirs = {
        "tasks": dropzone_root / "tasks",
        "results": dropzone_root / "results",
        "archive": dropzone_root / "archive",
        "errors": dropzone_root / "errors"
    }

    all_exist = True
    for name, dir_path in required_dirs.items():
        if dir_path.exists() and dir_path.is_dir():
            print(f"✓ {name.capitalize()} directory exists: {dir_path}")
        else:
            print(f"✗ {name.capitalize()} directory MISSING: {dir_path}")
            all_exist = False

    if all_exist:
        print("\n✅ TEST 1 PASSED: All required directories exist")
        return True
    else:
        print("\n❌ TEST 1 FAILED: Some directories are missing")
        return False


def test_module_import():
    """Test 2: Verify ADZ module can be imported."""
    print("\n" + "=" * 80)
    print("TEST 2: Module Import Verification")
    print("=" * 80)

    lib_path = Path.home() / ".claude" / "lib"
    if str(lib_path) not in sys.path:
        sys.path.insert(0, str(lib_path))

    try:
        # Try to import ADZ module
        import agentic_dropzone
        print(f"✓ agentic_dropzone module imported successfully")
        print(f"  - Module path: {agentic_dropzone.__file__}")

        # Check key classes exist
        if hasattr(agentic_dropzone, 'AgenticDropZone'):
            print(f"✓ AgenticDropZone class available")
        else:
            print(f"✗ AgenticDropZone class NOT FOUND")
            return False

        if hasattr(agentic_dropzone, 'TaskDefinition'):
            print(f"✓ TaskDefinition class available")
        else:
            print(f"✗ TaskDefinition class NOT FOUND")
            return False

        print("\n✅ TEST 2 PASSED: ADZ module imported successfully")
        return True

    except ImportError as e:
        print(f"✗ Failed to import agentic_dropzone: {e}")
        print("\n❌ TEST 2 FAILED: Module import failed")
        return False


def test_task_format():
    """Test 3: Verify task format parsing works."""
    print("\n" + "=" * 80)
    print("TEST 3: Task Format Parsing Verification")
    print("=" * 80)

    # Create test task in JSON format
    test_task = {
        "task_id": "test_verification",
        "task_type": "general",
        "description": "Verification test task for ADZ system",
        "requirements": {
            "complexity": "simple"
        },
        "context": {
            "purpose": "system_verification"
        }
    }

    # Save to temp file
    dropzone_root = Path.home() / "dropzone"
    test_file = dropzone_root / "tasks" / "test_verification.json"

    try:
        with open(test_file, 'w') as f:
            json.dump(test_task, f, indent=2)
        print(f"✓ Test task file created: {test_file}")

        # Try to parse it
        lib_path = Path.home() / ".claude" / "lib"
        if str(lib_path) not in sys.path:
            sys.path.insert(0, str(lib_path))

        from agentic_dropzone import TaskDefinition

        parsed_task = TaskDefinition.from_file(test_file)
        print(f"✓ Task parsed successfully")
        print(f"  - Task ID: {parsed_task.task_id}")
        print(f"  - Task Type: {parsed_task.task_type}")
        print(f"  - Description: {parsed_task.description[:50]}...")

        # Move to archive to avoid processing
        archive_path = dropzone_root / "archive" / f"test_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_file.rename(archive_path)
        print(f"✓ Test file archived: {archive_path}")

        print("\n✅ TEST 3 PASSED: Task format parsing works correctly")
        return True

    except Exception as e:
        print(f"✗ Task format test failed: {e}")
        print("\n❌ TEST 3 FAILED: Task parsing failed")

        # Cleanup
        if test_file.exists():
            test_file.unlink()

        return False


def test_documentation():
    """Test 4: Verify documentation exists."""
    print("\n" + "=" * 80)
    print("TEST 4: Documentation Verification")
    print("=" * 80)

    dropzone_root = Path.home() / "dropzone"
    docs = {
        "ADZ_GUIDE.md": "Main user guide",
        "TASK_SCHEMA.md": "Task format documentation",
        "SETUP_AND_TEST.md": "Setup instructions"
    }

    all_exist = True
    for doc_name, description in docs.items():
        doc_path = dropzone_root / doc_name
        if doc_path.exists():
            size_kb = doc_path.stat().st_size / 1024
            print(f"✓ {doc_name} exists ({size_kb:.1f} KB) - {description}")
        else:
            print(f"✗ {doc_name} MISSING - {description}")
            all_exist = False

    if all_exist:
        print("\n✅ TEST 4 PASSED: All documentation files exist")
        return True
    else:
        print("\n❌ TEST 4 FAILED: Some documentation is missing")
        return False


def test_scripts():
    """Test 5: Verify management scripts exist."""
    print("\n" + "=" * 80)
    print("TEST 5: Management Scripts Verification")
    print("=" * 80)

    claude_scripts = Path.home() / ".claude" / "scripts"
    scripts = {
        "adz-start.sh": "Start ADZ watcher",
        "adz-stop.sh": "Stop ADZ watcher",
        "adz-status.sh": "Check ADZ status"
    }

    all_exist = True
    for script_name, description in scripts.items():
        script_path = claude_scripts / script_name
        if script_path.exists():
            is_executable = script_path.stat().st_mode & 0o111 != 0
            status = "executable" if is_executable else "NOT executable"
            print(f"✓ {script_name} exists ({status}) - {description}")

            if not is_executable:
                print(f"  ⚠️  Hint: Make executable with: chmod +x {script_path}")
                all_exist = False
        else:
            print(f"✗ {script_name} MISSING - {description}")
            all_exist = False

    if all_exist:
        print("\n✅ TEST 5 PASSED: All management scripts exist and are executable")
        return True
    else:
        print("\n❌ TEST 5 FAILED: Some scripts are missing or not executable")
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 80)
    print("ADZ SYSTEM VERIFICATION SUMMARY")
    print("=" * 80)

    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")

    if failed_tests == 0:
        print("\n" + "=" * 80)
        print("✅ ADZ SYSTEM FULLY OPERATIONAL")
        print("=" * 80)
        print("\nThe Agentic Drop Zone is ready for Zero-Touch Engineering!")
        print("\nNext steps:")
        print("1. Start the watcher: ~/.claude/scripts/adz-start.sh")
        print("2. Drop a task file into: ~/dropzone/tasks/")
        print("3. Watch results appear in: ~/dropzone/results/")
        print("\nFor more info: ~/dropzone/ADZ_GUIDE.md")
    else:
        print("\n" + "=" * 80)
        print("⚠️  ADZ SYSTEM NEEDS ATTENTION")
        print("=" * 80)
        print(f"\n{failed_tests} test(s) failed. Please review the output above.")
        print("\nFor setup instructions: ~/dropzone/SETUP_AND_TEST.md")

    print("=" * 80)


def main():
    """Main entry point."""
    print("=" * 80)
    print("AGENTIC DROP ZONE - SYSTEM VERIFICATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Run all tests
    results = []
    results.append(test_directory_structure())
    results.append(test_module_import())
    results.append(test_task_format())
    results.append(test_documentation())
    results.append(test_scripts())

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
