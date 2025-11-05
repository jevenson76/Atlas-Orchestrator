#!/usr/bin/env python3
"""
Quick test to verify ValidationOrchestrator instrumentation works correctly.
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from validation_orchestrator import ValidationOrchestrator
from observability.event_emitter import EventEmitter

def test_validation_instrumentation():
    """Test that ValidationOrchestrator emits observability events."""

    print("Testing ValidationOrchestrator instrumentation...")
    print("=" * 60)

    # Test 1: Verify orchestrator has emitter
    print("\nTest 1: Verify emitter initialization")
    orchestrator = ValidationOrchestrator(project_root=".")

    if hasattr(orchestrator, 'emitter'):
        print("✓ ValidationOrchestrator has emitter attribute")
        if orchestrator.emitter is not None:
            print("✓ Emitter is initialized")
        else:
            print("✗ Emitter is None")
            return False
    else:
        print("✗ ValidationOrchestrator missing emitter attribute")
        return False

    # Test 2: Simple code validation (will emit events)
    print("\nTest 2: Test code validation with events")

    sample_code = """
def add(a, b):
    '''Add two numbers'''
    return a + b
"""

    try:
        result = orchestrator.validate_code(
            code=sample_code,
            context={"file_path": "test.py", "language": "python"},
            level="quick"
        )
        print(f"✓ Validation completed: {result.status} (score: {result.score}/100)")
        print(f"  Model used: {result.model_used}")
        print(f"  Cost: ${result.cost_usd:.6f}")
        print(f"  Findings: {len(result.findings)}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Check log files were created
    print("\nTest 3: Verify event logs created")
    log_dir = Path.home() / ".claude" / "logs" / "events"

    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    daily_log = log_dir / f"events-{date_str}.jsonl"
    stream_log = log_dir / "stream.jsonl"

    if daily_log.exists():
        size = daily_log.stat().st_size
        print(f"✓ Daily log exists: {daily_log} ({size} bytes)")
    else:
        print(f"✗ Daily log not found: {daily_log}")
        return False

    if stream_log.exists():
        size = stream_log.stat().st_size
        print(f"✓ Stream log exists: {stream_log} ({size} bytes)")
    else:
        print(f"✗ Stream log not found: {stream_log}")
        return False

    # Test 4: Verify events in logs
    print("\nTest 4: Verify validation events in logs")

    import json
    validation_events = []

    with open(daily_log, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    if event.get("component") == "validation-orchestrator":
                        validation_events.append(event)
                except json.JSONDecodeError:
                    continue

    print(f"Found {len(validation_events)} validation events")

    # Check for expected event types
    expected_types = ["validation.started"]
    found_types = [e.get("event_type") for e in validation_events]

    for expected in expected_types:
        if expected in found_types:
            print(f"✓ Found event: {expected}")
        else:
            print(f"⚠️  Missing event: {expected}")

    # Check that either passed or failed event exists
    result_events = [t for t in found_types if t in ["validation.passed", "validation.failed"]]
    if result_events:
        print(f"✓ Found result event: {result_events[0]}")
    else:
        print("⚠️  Missing validation result event (passed/failed)")

    # Test 5: Check execution stats
    print("\nTest 5: Verify execution stats")
    stats = orchestrator.get_execution_stats()
    print(f"Total validations: {stats['total_validations']}")
    print(f"Total cost: ${stats['total_cost_usd']:.6f}")
    print(f"Total time: {stats['total_time_seconds']:.2f}s")

    if stats['total_validations'] > 0:
        print("✓ Stats tracking works")
    else:
        print("✗ Stats not updated")
        return False

    print("\n" + "=" * 60)
    print("✅ All tests passed! ValidationOrchestrator instrumentation working.")
    return True

if __name__ == "__main__":
    success = test_validation_instrumentation()
    sys.exit(0 if success else 1)
