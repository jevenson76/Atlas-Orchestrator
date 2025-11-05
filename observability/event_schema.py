#!/usr/bin/env python3
"""
Event Schema for Multi-Agent Observability System

Defines comprehensive event types, severity levels, and event structure
for tracking all multi-agent workflow operations.

Architecture Principles:
1. STRUCTURED EVENTS - Consistent schema across all components
2. DISTRIBUTED TRACING - trace_id + span_id for execution tracking
3. CONTEXTUAL LOGGING - Rich debugging context in every event
4. TYPE SAFETY - Enum-based event types prevent typos
5. EXTENSIBILITY - Easy to add new event types and fields

Usage:
    from observability.event_schema import ObservabilityEvent, EventType, EventSeverity

    event = ObservabilityEvent(
        event_id="uuid-here",
        event_type=EventType.WORKFLOW_STARTED,
        timestamp="2025-11-03T12:00:00Z",
        severity=EventSeverity.INFO,
        trace_id="workflow-trace-123",
        component="specialized-roles-orchestrator",
        message="Workflow started with 4 phases"
    )

    json_str = event.to_json()
"""

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


# ============================================================================
# EVENT TYPE DEFINITIONS
# ============================================================================

class EventType(str, Enum):
    """
    Comprehensive event types for multi-agent observability.

    Organized by category for easy navigation and filtering.
    """

    # ========== WORKFLOW EVENTS ==========
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"

    # ========== AGENT EVENTS ==========
    AGENT_INVOKED = "agent.invoked"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_TIMEOUT = "agent.timeout"
    AGENT_RETRYING = "agent.retrying"

    # ========== VALIDATION EVENTS ==========
    VALIDATION_STARTED = "validation.started"
    VALIDATION_PASSED = "validation.passed"
    VALIDATION_FAILED = "validation.failed"
    VALIDATION_SKIPPED = "validation.skipped"

    # ========== CRITIC EVENTS ==========
    CRITIC_STARTED = "critic.started"
    CRITIC_COMPLETED = "critic.completed"
    CRITIC_FAILED = "critic.failed"

    # ========== COST EVENTS ==========
    COST_INCURRED = "cost.incurred"
    BUDGET_WARNING = "budget.warning"
    BUDGET_EXCEEDED = "budget.exceeded"
    COST_ANOMALY = "cost.anomaly"

    # ========== QUALITY EVENTS ==========
    QUALITY_MEASURED = "quality.measured"
    QUALITY_THRESHOLD_PASSED = "quality.threshold_passed"
    QUALITY_THRESHOLD_FAILED = "quality.threshold_failed"
    QUALITY_REGRESSION = "quality.regression"

    # ========== MODEL EVENTS ==========
    MODEL_FALLBACK = "model.fallback"
    MODEL_RATE_LIMITED = "model.rate_limited"
    MODEL_ERROR = "model.error"
    MODEL_UNAVAILABLE = "model.unavailable"

    # ========== SYSTEM EVENTS ==========
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"


# ============================================================================
# EVENT SEVERITY LEVELS
# ============================================================================

class EventSeverity(str, Enum):
    """
    Event severity levels for filtering and alerting.

    Levels:
    - DEBUG: Detailed diagnostic info (verbose, development only)
    - INFO: Normal operations (successful completions, routine events)
    - WARNING: Potential issues (rate limits, fallbacks, budget warnings)
    - ERROR: Failures requiring attention (agent failures, validation failures)
    - CRITICAL: System-level failures (workflow failures, budget exceeded)
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# OBSERVABILITY EVENT DATACLASS
# ============================================================================

@dataclass
class ObservabilityEvent:
    """
    Comprehensive event structure for multi-agent observability.

    This dataclass represents a single observable event in the system,
    with complete context for debugging, tracing, and analysis.

    Core Design:
    - Immutable once created (use frozen=True in production)
    - Serializable to JSON for persistence
    - Deserializable from JSON for analysis
    - Rich context for debugging
    - Distributed tracing support (trace_id, span_id)

    Example:
        event = ObservabilityEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AGENT_COMPLETED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=EventSeverity.INFO,
            trace_id="workflow-abc-123",
            span_id="agent-span-456",
            component="developer-agent",
            workflow="specialized-roles",
            agent="developer",
            model="claude-sonnet-4-5-20250929",
            message="Developer agent completed code implementation",
            data={"files_created": 3, "lines_of_code": 250},
            duration_ms=15000.0,
            cost_usd=0.015,
            quality_score=92.0
        )
    """

    # ========== CORE FIELDS (Required) ==========

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this event (UUID)"""

    event_type: EventType = EventType.SYSTEM_STARTED
    """Type of event (from EventType enum)"""

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    """ISO 8601 timestamp with timezone (UTC)"""

    severity: EventSeverity = EventSeverity.INFO
    """Event severity level (from EventSeverity enum)"""

    # ========== DISTRIBUTED TRACING FIELDS ==========

    trace_id: Optional[str] = None
    """Workflow execution ID - same for all events in a workflow"""

    span_id: Optional[str] = None
    """Component execution ID - unique for each component invocation"""

    parent_span_id: Optional[str] = None
    """Parent component's span_id for nested execution tracking"""

    # ========== COMPONENT CONTEXT ==========

    component: str = "unknown"
    """Which component emitted this event (e.g., 'developer-agent', 'security-critic')"""

    workflow: Optional[str] = None
    """Workflow name if applicable (e.g., 'specialized-roles', 'parallel-development')"""

    agent: Optional[str] = None
    """Agent name if applicable (e.g., 'architect', 'developer', 'tester')"""

    model: Optional[str] = None
    """Model used if applicable (e.g., 'claude-sonnet-4-5-20250929')"""

    output_style: Optional[str] = None
    """Output style used if applicable (e.g., 'code', 'detailed', 'critic', 'architect')"""

    # ========== EVENT DATA ==========

    message: str = ""
    """Human-readable description of what happened"""

    data: Dict[str, Any] = field(default_factory=dict)
    """Structured event-specific data (arbitrary key-value pairs)"""

    # ========== PERFORMANCE METRICS ==========

    duration_ms: Optional[float] = None
    """Operation duration in milliseconds"""

    cost_usd: Optional[float] = None
    """Cost incurred in USD (for API calls)"""

    tokens_used: Optional[int] = None
    """Tokens consumed (input + output)"""

    # ========== QUALITY METRICS ==========

    quality_score: Optional[float] = None
    """Quality score (0-100 scale)"""

    # ========== ERROR CONTEXT ==========

    error: Optional[str] = None
    """Error message if event represents a failure"""

    stack_trace: Optional[str] = None
    """Full stack trace if error occurred"""

    # ========== TAGS (for filtering/searching) ==========

    tags: Dict[str, str] = field(default_factory=dict)
    """Custom key-value tags for categorization and filtering"""

    # ========== METHODS ==========

    def to_json(self) -> str:
        """
        Serialize event to JSON string.

        Returns:
            JSON string representation of event

        Example:
            json_str = event.to_json()
            # '{"event_id": "...", "event_type": "workflow.started", ...}'
        """
        return json.dumps(self.to_dict(), default=str)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary.

        Converts enums to their string values for JSON serialization.
        Excludes None values to reduce payload size.

        Returns:
            Dictionary representation of event

        Example:
            event_dict = event.to_dict()
            # {'event_id': '...', 'event_type': 'workflow.started', ...}
        """
        # Convert dataclass to dict
        event_dict = asdict(self)

        # Convert enums to string values
        if isinstance(self.event_type, EventType):
            event_dict['event_type'] = self.event_type.value
        if isinstance(self.severity, EventSeverity):
            event_dict['severity'] = self.severity.value

        # Remove None values to reduce payload size
        return {k: v for k, v in event_dict.items() if v is not None}

    @classmethod
    def from_json(cls, json_str: str) -> 'ObservabilityEvent':
        """
        Deserialize event from JSON string.

        Args:
            json_str: JSON string representation of event

        Returns:
            ObservabilityEvent instance

        Raises:
            ValueError: If JSON is invalid or missing required fields

        Example:
            event = ObservabilityEvent.from_json('{"event_id": "..."}')
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObservabilityEvent':
        """
        Create event from dictionary.

        Handles enum conversion and provides defaults for missing fields.

        Args:
            data: Dictionary with event fields

        Returns:
            ObservabilityEvent instance

        Example:
            event = ObservabilityEvent.from_dict({
                'event_type': 'workflow.started',
                'severity': 'info',
                'component': 'orchestrator'
            })
        """
        # Convert string event_type to enum
        if 'event_type' in data and isinstance(data['event_type'], str):
            try:
                data['event_type'] = EventType(data['event_type'])
            except ValueError:
                # Keep as string if not a valid EventType
                pass

        # Convert string severity to enum
        if 'severity' in data and isinstance(data['severity'], str):
            try:
                data['severity'] = EventSeverity(data['severity'])
            except ValueError:
                # Default to INFO if invalid
                data['severity'] = EventSeverity.INFO

        # Ensure required fields have defaults
        data.setdefault('event_id', str(uuid.uuid4()))
        data.setdefault('timestamp', datetime.now(timezone.utc).isoformat())
        data.setdefault('component', 'unknown')
        data.setdefault('message', '')
        data.setdefault('data', {})
        data.setdefault('tags', {})

        # Create instance with available fields
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            Formatted string with key event details

        Example:
            print(event)
            # [2025-11-03T12:00:00Z] INFO workflow.started [orchestrator] Workflow started
        """
        return (
            f"[{self.timestamp}] {self.severity.value.upper()} {self.event_type.value} "
            f"[{self.component}] {self.message}"
        )

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            Full representation with all fields
        """
        return (
            f"ObservabilityEvent(event_id={self.event_id!r}, "
            f"event_type={self.event_type.value!r}, "
            f"severity={self.severity.value!r}, "
            f"component={self.component!r}, "
            f"message={self.message!r})"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_event(
    event_type: EventType,
    component: str,
    message: str,
    severity: EventSeverity = EventSeverity.INFO,
    **kwargs
) -> ObservabilityEvent:
    """
    Convenience function to create an event.

    Args:
        event_type: Type of event
        component: Component emitting the event
        message: Human-readable description
        severity: Event severity (default: INFO)
        **kwargs: Additional event fields

    Returns:
        ObservabilityEvent instance

    Example:
        event = create_event(
            event_type=EventType.AGENT_COMPLETED,
            component="developer-agent",
            message="Code implementation completed",
            severity=EventSeverity.INFO,
            duration_ms=15000.0,
            cost_usd=0.015,
            quality_score=92.0
        )
    """
    return ObservabilityEvent(
        event_type=event_type,
        component=component,
        message=message,
        severity=severity,
        **kwargs
    )


def get_event_type_by_name(name: str) -> Optional[EventType]:
    """
    Get EventType enum by string name.

    Args:
        name: Event type name (e.g., 'workflow.started')

    Returns:
        EventType enum or None if not found

    Example:
        event_type = get_event_type_by_name('workflow.started')
        # EventType.WORKFLOW_STARTED
    """
    try:
        return EventType(name)
    except ValueError:
        return None


def get_severity_by_name(name: str) -> Optional[EventSeverity]:
    """
    Get EventSeverity enum by string name.

    Args:
        name: Severity name (e.g., 'info', 'error')

    Returns:
        EventSeverity enum or None if not found

    Example:
        severity = get_severity_by_name('warning')
        # EventSeverity.WARNING
    """
    try:
        return EventSeverity(name.lower())
    except ValueError:
        return None


# ============================================================================
# VALIDATION
# ============================================================================

def validate_event(event: ObservabilityEvent) -> tuple[bool, Optional[str]]:
    """
    Validate that event has all required fields and correct types.

    Args:
        event: Event to validate

    Returns:
        (is_valid, error_message)

    Example:
        valid, error = validate_event(event)
        if not valid:
            print(f"Invalid event: {error}")
    """
    # Check required fields
    if not event.event_id:
        return False, "Missing event_id"

    if not isinstance(event.event_type, EventType):
        return False, f"Invalid event_type: {event.event_type}"

    if not event.timestamp:
        return False, "Missing timestamp"

    if not isinstance(event.severity, EventSeverity):
        return False, f"Invalid severity: {event.severity}"

    if not event.component:
        return False, "Missing component"

    # Validate timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
    except ValueError:
        return False, f"Invalid timestamp format: {event.timestamp}"

    # Validate optional numeric fields
    if event.duration_ms is not None and event.duration_ms < 0:
        return False, f"Invalid duration_ms: {event.duration_ms} (must be >= 0)"

    if event.cost_usd is not None and event.cost_usd < 0:
        return False, f"Invalid cost_usd: {event.cost_usd} (must be >= 0)"

    if event.tokens_used is not None and event.tokens_used < 0:
        return False, f"Invalid tokens_used: {event.tokens_used} (must be >= 0)"

    if event.quality_score is not None and not (0 <= event.quality_score <= 100):
        return False, f"Invalid quality_score: {event.quality_score} (must be 0-100)"

    return True, None


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    # Demo event creation
    print("=" * 80)
    print("OBSERVABILITY EVENT SCHEMA DEMO")
    print("=" * 80)

    # Example 1: Workflow started event
    workflow_event = create_event(
        event_type=EventType.WORKFLOW_STARTED,
        component="specialized-roles-orchestrator",
        message="Starting specialized roles workflow with 4 phases",
        severity=EventSeverity.INFO,
        trace_id="workflow-123-abc",
        workflow="specialized-roles",
        data={"phases": 4, "task": "Implement authentication"}
    )

    print("\n1. WORKFLOW STARTED EVENT:")
    print(f"   {workflow_event}")
    print(f"   JSON: {workflow_event.to_json()[:100]}...")

    # Example 2: Agent completed event
    agent_event = create_event(
        event_type=EventType.AGENT_COMPLETED,
        component="developer-agent",
        message="Developer agent completed code implementation",
        severity=EventSeverity.INFO,
        trace_id="workflow-123-abc",
        span_id="span-dev-456",
        agent="developer",
        model="claude-sonnet-4-5-20250929",
        duration_ms=15000.0,
        cost_usd=0.015,
        tokens_used=5000,
        quality_score=92.0,
        data={"files_created": 3, "lines_of_code": 250}
    )

    print("\n2. AGENT COMPLETED EVENT:")
    print(f"   {agent_event}")

    # Example 3: Error event
    error_event = create_event(
        event_type=EventType.AGENT_FAILED,
        component="tester-agent",
        message="Test generation failed due to API timeout",
        severity=EventSeverity.ERROR,
        trace_id="workflow-123-abc",
        span_id="span-test-789",
        error="API timeout after 30 seconds",
        stack_trace="Traceback (most recent call last):\n  File..."
    )

    print("\n3. ERROR EVENT:")
    print(f"   {error_event}")

    # Example 4: Serialization/deserialization
    print("\n4. SERIALIZATION TEST:")
    json_str = agent_event.to_json()
    print(f"   Serialized: {len(json_str)} bytes")

    deserialized = ObservabilityEvent.from_json(json_str)
    print(f"   Deserialized: {deserialized.event_type.value}")

    # Example 5: Validation
    print("\n5. VALIDATION TEST:")
    valid, error = validate_event(agent_event)
    print(f"   Valid: {valid}, Error: {error}")

    # Example 6: All event types
    print("\n6. ALL EVENT TYPES:")
    for event_type in EventType:
        print(f"   - {event_type.value}")

    print("\n" + "=" * 80)
    print("✅ Event schema ready for use!")
