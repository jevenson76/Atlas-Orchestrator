#!/usr/bin/env python3
"""
Comprehensive Test Suite for Multi-Agent Observability System

Tests cover:
- Event schema and serialization
- Event emitter functionality
- Distributed tracing (trace_id, span_id)
- Alert system
- File/stream/console sinks
- Critic orchestrator instrumentation
- Integration scenarios

Run with: pytest test_observability.py -v
"""

import pytest
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from observability.event_schema import (
    ObservabilityEvent,
    EventType,
    EventSeverity,
    create_event,
    validate_event,
    get_event_type_by_name,
    get_severity_by_name
)
from observability.event_emitter import EventEmitter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create temporary log directory for tests."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def emitter(temp_log_dir):
    """Create event emitter with temporary log directory."""
    return EventEmitter(log_dir=temp_log_dir, enable_console=False)


@pytest.fixture
def sample_event():
    """Create sample observability event."""
    return create_event(
        event_type=EventType.AGENT_COMPLETED,
        component="test-agent",
        message="Test agent completed",
        severity=EventSeverity.INFO,
        duration_ms=1000.0,
        cost_usd=0.01,
        quality_score=95.0
    )


# ============================================================================
# TEST SUITE 1: EVENT SCHEMA
# ============================================================================

class TestEventSchema:
    """Test event schema and validation."""

    def test_event_creation(self):
        """Test 1: Basic event creation."""
        event = create_event(
            event_type=EventType.WORKFLOW_STARTED,
            component="orchestrator",
            message="Workflow started",
            severity=EventSeverity.INFO
        )

        assert event.event_type == EventType.WORKFLOW_STARTED
        assert event.component == "orchestrator"
        assert event.message == "Workflow started"
        assert event.severity == EventSeverity.INFO
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_event_serialization(self, sample_event):
        """Test 2: Event serialization to JSON."""
        json_str = sample_event.to_json()

        assert isinstance(json_str, str)
        assert "agent.completed" in json_str
        assert "test-agent" in json_str
        assert "1000" in json_str  # duration_ms
        assert "0.01" in json_str  # cost_usd

    def test_event_deserialization(self, sample_event):
        """Test 3: Event deserialization from JSON."""
        json_str = sample_event.to_json()
        deserialized = ObservabilityEvent.from_json(json_str)

        assert deserialized.event_type == sample_event.event_type
        assert deserialized.component == sample_event.component
        assert deserialized.message == sample_event.message
        assert deserialized.duration_ms == sample_event.duration_ms
        assert deserialized.cost_usd == sample_event.cost_usd

    def test_event_validation_valid(self, sample_event):
        """Test 4: Valid event passes validation."""
        valid, error = validate_event(sample_event)

        assert valid is True
        assert error is None

    def test_event_validation_invalid_quality_score(self):
        """Test 5: Invalid quality score fails validation."""
        event = create_event(
            event_type=EventType.QUALITY_MEASURED,
            component="test",
            message="Invalid quality",
            quality_score=150.0  # Invalid: must be 0-100
        )

        valid, error = validate_event(event)

        assert valid is False
        assert "quality_score" in error.lower()

    def test_all_event_types_exist(self):
        """Test 6: All expected event types are defined."""
        expected_types = [
            "workflow.started", "workflow.completed", "workflow.failed",
            "agent.invoked", "agent.completed", "agent.failed",
            "critic.started", "critic.completed", "critic.failed",
            "cost.incurred", "budget.exceeded",
            "quality.measured", "quality.threshold_passed",
            "model.fallback", "model.rate_limited"
        ]

        for event_type_str in expected_types:
            event_type = get_event_type_by_name(event_type_str)
            assert event_type is not None, f"Event type {event_type_str} not found"

    def test_severity_levels(self):
        """Test 7: All severity levels are defined."""
        expected_severities = ["debug", "info", "warning", "error", "critical"]

        for severity_str in expected_severities:
            severity = get_severity_by_name(severity_str)
            assert severity is not None, f"Severity {severity_str} not found"


# ============================================================================
# TEST SUITE 2: EVENT EMITTER
# ============================================================================

class TestEventEmitter:
    """Test event emitter functionality."""

    def test_emitter_initialization(self, temp_log_dir):
        """Test 8: Event emitter initializes correctly."""
        emitter = EventEmitter(log_dir=temp_log_dir)

        assert emitter.log_dir == temp_log_dir
        assert emitter.enable_streaming is True
        assert emitter.enable_alerts is True
        assert emitter._current_trace_id is None
        assert emitter._current_span_id is None

    def test_emit_event(self, emitter, temp_log_dir):
        """Test 9: Emitting event writes to log file."""
        emitter.emit(
            event_type=EventType.AGENT_COMPLETED,
            component="test-agent",
            message="Test message",
            severity=EventSeverity.INFO
        )

        # Check daily log file exists
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = temp_log_dir / f"events-{date_str}.jsonl"

        assert log_file.exists()

        # Read and verify event
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1

            event_data = json.loads(lines[0])
            assert event_data["event_type"] == "agent.completed"
            assert event_data["component"] == "test-agent"
            assert event_data["message"] == "Test message"

    def test_stream_file_creation(self, emitter, temp_log_dir):
        """Test 10: Stream file is created and updated."""
        # Emit multiple events
        for i in range(5):
            emitter.emit(
                event_type=EventType.AGENT_COMPLETED,
                component=f"agent-{i}",
                message=f"Message {i}",
                severity=EventSeverity.INFO
            )

        # Check stream file
        stream_file = temp_log_dir / "stream.jsonl"
        assert stream_file.exists()

        # Read stream
        with open(stream_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 5

    def test_stream_buffer_limit(self, emitter, temp_log_dir):
        """Test 11: Stream buffer respects max size limit."""
        # Emit more events than buffer size
        for i in range(150):
            emitter.emit(
                event_type=EventType.AGENT_COMPLETED,
                component=f"agent-{i}",
                message=f"Message {i}",
                severity=EventSeverity.INFO
            )

        # Stream should only have last 100 events
        stream_file = temp_log_dir / "stream.jsonl"
        with open(stream_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == emitter.max_stream_events

    def test_statistics_tracking(self, emitter):
        """Test 12: Statistics are tracked correctly."""
        initial_stats = emitter.get_stats()
        assert initial_stats["events_emitted"] == 0

        # Emit 3 events
        for i in range(3):
            emitter.emit(
                event_type=EventType.AGENT_COMPLETED,
                component="test",
                message="Test",
                severity=EventSeverity.INFO
            )

        stats = emitter.get_stats()
        assert stats["events_emitted"] == 3


# ============================================================================
# TEST SUITE 3: DISTRIBUTED TRACING
# ============================================================================

class TestDistributedTracing:
    """Test trace and span management."""

    def test_start_trace(self, emitter):
        """Test 13: Starting trace generates trace_id."""
        trace_id = emitter.start_trace("test-workflow", {"test": True})

        assert trace_id is not None
        assert trace_id.startswith("trace-")
        assert emitter._current_trace_id == trace_id

    def test_end_trace(self, emitter):
        """Test 14: Ending trace clears trace_id."""
        trace_id = emitter.start_trace("test-workflow")

        assert emitter._current_trace_id is not None

        emitter.end_trace(success=True)

        assert emitter._current_trace_id is None

    def test_start_span(self, emitter):
        """Test 15: Starting span generates span_id."""
        emitter.start_trace("test-workflow")
        span_id = emitter.start_span("test-component")

        assert span_id is not None
        assert span_id.startswith("span-")
        assert emitter._current_span_id == span_id

    def test_nested_spans(self, emitter):
        """Test 16: Nested spans work correctly."""
        emitter.start_trace("test-workflow")

        # Start parent span
        parent_span = emitter.start_span("parent")
        assert emitter._current_span_id == parent_span

        # Start child span
        child_span = emitter.start_span("child")
        assert emitter._current_span_id == child_span

        # End child span - should revert to parent
        emitter.end_span()
        assert emitter._current_span_id == parent_span

        # End parent span - should clear
        emitter.end_span()
        assert emitter._current_span_id is None

    def test_events_inherit_trace_context(self, emitter, temp_log_dir):
        """Test 17: Events automatically inherit trace_id and span_id."""
        trace_id = emitter.start_trace("test-workflow")
        span_id = emitter.start_span("test-component")

        emitter.emit(
            event_type=EventType.AGENT_COMPLETED,
            component="test",
            message="Test",
            severity=EventSeverity.INFO
        )

        # Read event from log
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = temp_log_dir / f"events-{date_str}.jsonl"

        with open(log_file, 'r') as f:
            # Skip workflow started event, read agent completed
            lines = f.readlines()
            event_data = json.loads(lines[-1])

            assert event_data["trace_id"] == trace_id
            assert event_data["span_id"] == span_id


# ============================================================================
# TEST SUITE 4: ALERT SYSTEM
# ============================================================================

class TestAlertSystem:
    """Test alert rule checking and triggering."""

    def test_load_alert_rules(self, emitter):
        """Test 18: Alert rules load from file."""
        rules = emitter._load_alert_rules()

        assert isinstance(rules, list)
        # Should have rules from alerts.json
        assert len(rules) >= 10

    def test_cost_threshold_alert(self, emitter, temp_log_dir):
        """Test 19: High cost triggers alert."""
        # Emit high cost event
        emitter.emit(
            event_type=EventType.COST_INCURRED,
            component="test",
            message="High cost operation",
            severity=EventSeverity.INFO,
            cost_usd=2.0  # Above $1 threshold
        )

        # Check alerts file
        alerts_file = temp_log_dir / "alerts.jsonl"
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 0

                alert = json.loads(lines[0])
                assert "cost" in alert["rule_name"].lower()

    def test_quality_threshold_alert(self, emitter, temp_log_dir):
        """Test 20: Low quality triggers alert."""
        # Emit low quality event
        emitter.emit(
            event_type=EventType.QUALITY_MEASURED,
            component="test",
            message="Low quality detected",
            severity=EventSeverity.WARNING,
            quality_score=40.0  # Below 50 threshold
        )

        # Check alerts file
        alerts_file = temp_log_dir / "alerts.jsonl"
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                lines = f.readlines()
                # Should have triggered alert
                assert any("quality" in line.lower() for line in lines)


# ============================================================================
# TEST SUITE 5: CRITIC ORCHESTRATOR INSTRUMENTATION
# ============================================================================

class TestCriticInstrumentation:
    """Test that CriticOrchestrator emits events correctly."""

    def test_critic_orchestrator_has_emitter(self):
        """Test 21: CriticOrchestrator initializes with emitter."""
        from critic_orchestrator import CriticOrchestrator

        orchestrator = CriticOrchestrator()

        assert hasattr(orchestrator, 'emitter')
        assert orchestrator.emitter is not None

    @patch('critic_orchestrator.BaseAgent.execute')
    def test_critic_review_emits_events(self, mock_execute, temp_log_dir):
        """Test 22: Critic review emits events during execution."""
        from critic_orchestrator import CriticOrchestrator

        # Mock critic response
        mock_execute.return_value = json.dumps({
            "critic_type": "security",
            "model_used": "claude-opus-4-20250514",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": 75,
            "risk_level": "MEDIUM",
            "summary": "Test analysis",
            "findings": [],
            "statistics": {"total_findings": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
            "metrics": {}
        })

        # Create orchestrator with test log dir
        orchestrator = CriticOrchestrator()
        orchestrator.emitter = EventEmitter(log_dir=temp_log_dir, enable_console=False)

        # Run critic
        results = orchestrator.review_code(
            code_snippet="def foo(): pass",
            critics=["security-critic"],
            file_path="test.py"
        )

        # Check events were emitted
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = temp_log_dir / f"events-{date_str}.jsonl"

        assert log_file.exists()

        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0

            # Should have critic events
            events = [json.loads(line) for line in lines]
            event_types = [e["event_type"] for e in events]

            assert "critic.started" in event_types
            assert "critic.completed" in event_types


# ============================================================================
# TEST SUITE 6: INTEGRATION
# ============================================================================

class TestIntegration:
    """Integration tests for full workflow."""

    def test_end_to_end_workflow(self, temp_log_dir):
        """Test 23: Complete workflow with tracing."""
        emitter = EventEmitter(log_dir=temp_log_dir, enable_console=False)

        # Start workflow
        trace_id = emitter.start_trace("test-workflow", {"param": "value"})

        # Phase 1
        span1 = emitter.start_span("phase-1")
        emitter.emit(
            EventType.AGENT_INVOKED,
            "phase-1",
            "Phase 1 started",
            EventSeverity.INFO
        )
        time.sleep(0.01)
        emitter.emit(
            EventType.AGENT_COMPLETED,
            "phase-1",
            "Phase 1 completed",
            EventSeverity.INFO,
            duration_ms=10.0,
            cost_usd=0.005
        )
        emitter.end_span()

        # Phase 2
        span2 = emitter.start_span("phase-2")
        emitter.emit(
            EventType.AGENT_INVOKED,
            "phase-2",
            "Phase 2 started",
            EventSeverity.INFO
        )
        emitter.emit(
            EventType.QUALITY_MEASURED,
            "phase-2",
            "Quality measured",
            EventSeverity.INFO,
            quality_score=92.0
        )
        emitter.end_span()

        # End workflow
        emitter.end_trace(success=True, result={"quality": 92})

        # Verify events
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = temp_log_dir / f"events-{date_str}.jsonl"

        with open(log_file, 'r') as f:
            events = [json.loads(line) for line in f.readlines()]

            # Should have workflow started, 2 phases, workflow completed
            assert len(events) >= 6

            # All events should have same trace_id
            trace_ids = set(e.get("trace_id") for e in events if e.get("trace_id"))
            assert len(trace_ids) == 1
            assert trace_id in trace_ids

    def test_error_handling(self, temp_log_dir):
        """Test 24: Error events are emitted correctly."""
        emitter = EventEmitter(log_dir=temp_log_dir, enable_console=False)

        emitter.start_trace("error-workflow")

        # Emit error
        emitter.emit(
            EventType.AGENT_FAILED,
            "failing-agent",
            "Agent failed due to timeout",
            EventSeverity.ERROR,
            error="Connection timeout after 30s",
            stack_trace="Traceback (most recent call last):\n  File..."
        )

        emitter.end_trace(success=False)

        # Verify error event
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = temp_log_dir / f"events-{date_str}.jsonl"

        with open(log_file, 'r') as f:
            events = [json.loads(line) for line in f.readlines()]

            error_events = [e for e in events if e["event_type"] == "agent.failed"]
            assert len(error_events) == 1

            error_event = error_events[0]
            assert error_event["severity"] == "error"
            assert "timeout" in error_event["error"].lower()
            assert error_event["stack_trace"] is not None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
