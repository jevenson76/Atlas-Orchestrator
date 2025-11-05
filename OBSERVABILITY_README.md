# Multi-Agent Observability System

**Production-grade monitoring, tracing, and analytics for multi-agent workflows.**

## 🚀 Quick Start (5 Minutes)

### View Real-Time Events
```bash
# Simple terminal dashboard (updates every 2 seconds)
python3 ~/.claude/scripts/observability_dashboard.py
```

### Analyze History
```bash
# Analyze last 7 days
python3 ~/.claude/scripts/analyze_observability.py

# Analyze last 30 days
python3 ~/.claude/scripts/analyze_observability.py --days 30

# Filter by specific workflow
python3 ~/.claude/scripts/analyze_observability.py --workflow specialized_roles

# Detailed analysis with performance metrics
python3 ~/.claude/scripts/analyze_observability.py --detailed
```

### View Raw Logs
```bash
# Real-time event stream (latest 100 events)
tail -f ~/.claude/logs/events/stream.jsonl

# Today's complete event log
tail -f ~/.claude/logs/events/events-$(date +%Y%m%d).jsonl

# View specific event
cat ~/.claude/logs/events/events-20251103.jsonl | grep "workflow.completed" | tail -1 | jq '.'
```

---

## 📖 Overview

The observability system provides:

- **31 Event Types** - Comprehensive coverage of all workflow activities
- **Distributed Tracing** - Track execution across agents with trace_id/span_id
- **Real-Time Monitoring** - Live dashboard and alerts
- **Historical Analysis** - Trend analysis and cost optimization
- **Production-Ready** - Thread-safe, performant, non-invasive

---

## 🎯 Event Types (31 Total)

### Workflow Events
- `workflow.started` - Workflow execution begins
- `workflow.completed` - Workflow finishes successfully
- `workflow.failed` - Workflow encounters fatal error

### Agent Events
- `agent.invoked` - Agent starts execution
- `agent.completed` - Agent finishes successfully
- `agent.timeout` - Agent exceeds time limit

### Critic Events
- `critic.started` - Critic analysis begins
- `critic.completed` - Critic analysis finishes
- `critic.failed` - Critic analysis fails

### Validation Events
- `validation.started` - Validation begins
- `validation.passed` - Validation succeeds
- `validation.failed` - Validation fails
- `validation.skipped` - Validation bypassed

### Cost Events
- `cost.incurred` - Cost recorded for operation
- `budget.exceeded` - Daily budget limit reached

### Quality Events
- `quality.measured` - Quality score recorded
- `quality.threshold_passed` - Quality meets threshold
- `quality.threshold_failed` - Quality below threshold

### Model Events
- `model.rate_limited` - API rate limit hit
- `model.fallback` - Fallback to alternative model
- `model.overload` - Service overload (529 error)

### System Events
- `system.error` - System-level error occurred

---

## 🏗️ Architecture

### Data Flow
```
Orchestrator → EventEmitter → [Daily Log | Stream | Console | Alerts]
                                    ↓
                         events-YYYYMMDD.jsonl (persistent)
                         stream.jsonl (latest 100)
                         alerts.jsonl (triggered alerts)
```

### Instrumented Components
All major orchestrators emit events:

1. **CriticOrchestrator** - Code review events
2. **ValidationOrchestrator** - Validation events
3. **SpecializedRolesOrchestrator** - Phase-by-phase events (architect, dev, test, review)
4. **ParallelDevelopmentOrchestrator** - Parallel execution events
5. **ProgressiveEnhancementOrchestrator** - Tier escalation events
6. **AgenticDropzone** - Task processing events

### Distributed Tracing

Every event includes tracing context:

- `trace_id` - Unique workflow execution ID
- `span_id` - Component execution ID
- `parent_span_id` - Parent component ID (for nesting)

Example trace hierarchy:
```
workflow.started (trace_id: trace-abc123)
├─ architect (span_id: span-xyz001, parent: null)
├─ developer (span_id: span-xyz002, parent: null)
│  └─ validation (span_id: span-xyz003, parent: span-xyz002)
├─ tester (span_id: span-xyz004, parent: null)
└─ reviewer (span_id: span-xyz005, parent: null)
```

---

## 📊 Event Structure

Every event follows this schema:

```json
{
  "event_id": "uuid",
  "event_type": "workflow.completed",
  "timestamp": "2025-11-03T12:34:56.789",
  "severity": "info",

  "trace_id": "trace-abc123",
  "span_id": "span-xyz001",
  "parent_span_id": null,

  "component": "specialized-roles-orchestrator",
  "workflow": "specialized_roles",
  "agent": "developer",
  "model": "claude-sonnet-4-5-20250929",

  "message": "Workflow completed successfully",
  "data": {"quality_score": 95, "phases": 4},

  "duration_ms": 45200,
  "cost_usd": 0.0234,
  "quality_score": 95.0,

  "error": null,
  "stack_trace": null
}
```

**Required Fields**: `event_id`, `event_type`, `timestamp`, `severity`, `component`, `message`, `data`

**Optional Fields**: All tracing, metrics, and error fields

---

## 🚨 Alert Rules

### Configured Alerts (12 total)

#### Cost Alerts
- **High Cost Warning**: Single operation > $1 (severity: warning)
- **Critical Cost Alert**: Single operation > $5 (severity: critical)
- **Daily Budget Exceeded**: Budget limit reached (severity: critical)

#### Quality Alerts
- **Quality Failure**: Score < 70 (severity: error)
- **Critical Quality Failure**: Score < 50 (severity: critical)

#### Workflow Alerts
- **Workflow Failure**: Any workflow failure (severity: error)
- **Agent Timeout**: Agent execution timeout (severity: error)

#### Model Alerts
- **Model Rate Limit**: API rate limited (severity: warning)
- **Model Fallback**: Fallback to alternate model (severity: warning)

#### System Alerts
- **Critic Failure**: Critic analysis failed (severity: error)
- **Validation Failure**: Validation failed (severity: warning)
- **System Error**: System-level error (severity: critical)

### Custom Alert Rules

Edit `~/.claude/logs/events/alerts.json`:

```json
{
  "rules": [
    {
      "name": "Custom Cost Alert",
      "description": "Alert when cost exceeds $10",
      "event_types": ["cost.incurred"],
      "cost_threshold": 10.0,
      "severity": "critical",
      "enabled": true
    }
  ]
}
```

**Alert Rule Fields**:
- `name` - Rule name (required)
- `description` - Rule purpose (optional)
- `event_types` - List of event types to match (required)
- `cost_threshold` - Cost threshold (optional)
- `quality_threshold` - Quality threshold (optional)
- `min_severity` - Minimum event severity to trigger (optional)
- `severity` - Alert severity level (required)
- `enabled` - Whether rule is active (required)

---

## 🔧 Integration Guide

### Instrument a New Orchestrator

Follow this pattern (already applied to all 6 orchestrators):

#### 1. Add Imports
```python
import traceback

# Observability
try:
    from observability.event_emitter import EventEmitter, EventType, EventSeverity
except ImportError:
    EventEmitter = None
    EventType = None
    EventSeverity = None
```

#### 2. Initialize in `__init__`
```python
# Initialize observability
if EventEmitter is not None:
    self.emitter = EventEmitter(enable_console=False)
else:
    self.emitter = None
```

#### 3. Workflow-Level Tracing
```python
# At workflow start
if self.emitter:
    self.emitter.start_trace(
        workflow="my_workflow",
        context={"key": "value"}
    )

# At workflow end (success)
if self.emitter:
    self.emitter.end_trace(
        success=True,
        result={"quality": 95}
    )

# At workflow end (failure)
if self.emitter:
    self.emitter.emit(
        event_type=EventType.WORKFLOW_FAILED,
        component="my-orchestrator",
        message=f"Workflow failed: {error}",
        severity=EventSeverity.ERROR,
        error=str(e),
        stack_trace=traceback.format_exc()
    )
    self.emitter.end_trace(success=False, result={"error": str(e)})
```

#### 4. Component-Level Spans
```python
# Start component span
if self.emitter:
    self.emitter.start_span("component_name")

# ... component execution ...

# End component span
if self.emitter:
    self.emitter.end_span()
```

#### 5. Emit Key Events
```python
# Agent completed
if self.emitter:
    self.emitter.emit(
        event_type=EventType.AGENT_COMPLETED,
        component="agent-name",
        message="Agent completed successfully",
        severity=EventSeverity.INFO,
        duration_ms=duration * 1000,
        cost_usd=cost,
        model="claude-sonnet-4-5-20250929",
        data={"output_size": len(output)}
    )

# Quality measured
if self.emitter:
    self.emitter.emit(
        event_type=EventType.QUALITY_MEASURED,
        component="component-name",
        message=f"Quality score: {score}/100",
        severity=EventSeverity.INFO,
        quality_score=float(score),
        data={"criteria": "validation"}
    )

# Cost incurred
if self.emitter:
    self.emitter.emit(
        event_type=EventType.COST_INCURRED,
        component="component-name",
        message=f"Cost: ${cost:.4f}",
        severity=EventSeverity.INFO,
        cost_usd=cost,
        data={"operation": "llm_call"}
    )
```

---

## 📈 Usage Patterns

### Cost Analysis
```bash
# Find most expensive operations
cat ~/.claude/logs/events/events-*.jsonl | \
  jq 'select(.cost_usd != null) | {component, cost: .cost_usd, message}' | \
  sort -k2 -nr | head -10

# Total cost by component
cat ~/.claude/logs/events/events-*.jsonl | \
  jq -s 'group_by(.component) | map({component: .[0].component, total_cost: map(.cost_usd // 0) | add}) | sort_by(.total_cost) | reverse'
```

### Quality Tracking
```bash
# Average quality by workflow
cat ~/.claude/logs/events/events-*.jsonl | \
  jq 'select(.quality_score != null) | {workflow, quality_score}' | \
  jq -s 'group_by(.workflow) | map({workflow: .[0].workflow, avg_quality: (map(.quality_score) | add / length)})'
```

### Error Investigation
```bash
# Find all errors with stack traces
cat ~/.claude/logs/events/events-*.jsonl | \
  jq 'select(.severity == "error" or .severity == "critical") | {timestamp, component, message, error, stack_trace}'

# Count errors by component
cat ~/.claude/logs/events/events-*.jsonl | \
  jq 'select(.severity == "error" or .severity == "critical")' | \
  jq -s 'group_by(.component) | map({component: .[0].component, error_count: length}) | sort_by(.error_count) | reverse'
```

---

## 🛠️ Troubleshooting

### No Events Being Generated

**Check 1**: Is the orchestrator instrumented?
```python
# Should have emitter initialized
hasattr(orchestrator, 'emitter')  # Should be True
```

**Check 2**: Is observability module available?
```bash
# Should exist
ls ~/.claude/lib/observability/event_emitter.py
```

**Check 3**: Are log files being created?
```bash
# Should show recent files
ls -lh ~/.claude/logs/events/
```

### Dashboard Shows "No Events"

**Solution**: Generate some events by running a workflow:
```python
from specialized_roles_orchestrator import SpecializedRolesOrchestrator

orchestrator = SpecializedRolesOrchestrator(project_root=".")
result = orchestrator.execute_workflow(
    task="Create a hello world function",
    context={"language": "python"}
)
```

### High Performance Overhead

The observability system is designed for <5% overhead. If you experience performance issues:

**Solution 1**: Disable console output (already default)
```python
self.emitter = EventEmitter(enable_console=False)  # ✅ Good
```

**Solution 2**: Reduce stream buffer size
```python
# In event_emitter.py
max_stream_events = 50  # Default: 100
```

**Solution 3**: Disable streaming entirely
```python
self.emitter = EventEmitter(enable_streaming=False)
```

### Log Files Growing Too Large

Daily log files rotate automatically. To archive old logs:

```bash
# Archive logs older than 30 days
find ~/.claude/logs/events -name "events-*.jsonl" -mtime +30 -exec gzip {} \;

# Delete logs older than 90 days
find ~/.claude/logs/events -name "events-*.jsonl.gz" -mtime +90 -delete
```

---

## 📚 Advanced Features

### Custom Event Types

While the 31 built-in event types cover most use cases, you can emit custom events:

```python
if self.emitter:
    self.emitter.emit(
        event_type="custom.my_event",  # Custom type
        component="my-component",
        message="Custom event occurred",
        severity=EventSeverity.INFO,
        data={"custom_field": "value"}
    )
```

**Note**: Custom events won't trigger built-in alerts unless you add custom alert rules.

### Thread Safety

EventEmitter is thread-safe. Multiple agents can emit events concurrently:

```python
import threading

def agent_work(agent_id):
    if emitter:
        emitter.emit(
            event_type=EventType.AGENT_INVOKED,
            component=f"agent-{agent_id}",
            message="Starting work"
        )

threads = [threading.Thread(target=agent_work, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
```

### Performance Metrics

Track your own metrics:

```python
import time

start = time.time()
# ... do work ...
duration_ms = (time.time() - start) * 1000

if self.emitter:
    self.emitter.emit(
        event_type=EventType.AGENT_COMPLETED,
        component="my-agent",
        message="Work completed",
        duration_ms=duration_ms,
        data={"custom_metric": 123}
    )
```

---

## 🔍 Event Schema Reference

### Severity Levels

| Level | Usage | Color |
|-------|-------|-------|
| `DEBUG` | Development/debugging information | Gray |
| `INFO` | Normal operations | Green |
| `WARNING` | Issues that don't block execution | Yellow |
| `ERROR` | Failures that affect current operation | Red |
| `CRITICAL` | System-level failures | Bold Red |

### Common Patterns

**Workflow Execution**:
```
workflow.started → agent.invoked → agent.completed → workflow.completed
```

**With Validation**:
```
agent.completed → validation.started → validation.passed → quality.measured
```

**With Escalation**:
```
agent.completed → quality.threshold_failed → model.fallback → agent.invoked
```

**With Error**:
```
agent.invoked → agent.timeout → workflow.failed
```

---

## 📝 Best Practices

### DO ✅
- Emit events at key workflow milestones
- Include rich context in `data` field
- Use appropriate severity levels
- Track costs and quality metrics
- Enable observability in production

### DON'T ❌
- Emit events in tight loops (batch instead)
- Include sensitive data in events
- Block on event emission (it's async)
- Modify event schema without testing
- Disable observability "to save performance"

---

## 🎓 Examples

### Example 1: Track Custom Workflow
```python
from observability.event_emitter import EventEmitter, EventType, EventSeverity

emitter = EventEmitter()

# Start custom workflow
trace_id = emitter.start_trace("my_workflow", context={"task": "demo"})

# Execute with span
emitter.start_span("processing")
# ... do work ...
emitter.emit(
    event_type=EventType.AGENT_COMPLETED,
    component="processor",
    message="Processing complete",
    duration_ms=1500,
    cost_usd=0.005
)
emitter.end_span()

# End workflow
emitter.end_trace(success=True, result={"items_processed": 42})
```

### Example 2: Query Specific Workflow
```bash
# Get all events for a specific trace_id
TRACE_ID="trace-abc123"
cat ~/.claude/logs/events/events-*.jsonl | \
  jq "select(.trace_id == \"$TRACE_ID\")" | \
  jq -s 'sort_by(.timestamp)'
```

### Example 3: Cost by Day
```bash
# Total cost per day
for file in ~/.claude/logs/events/events-*.jsonl; do
  date=$(basename $file | sed 's/events-//;s/.jsonl//')
  cost=$(jq -s 'map(.cost_usd // 0) | add' $file)
  echo "$date: \$$cost"
done
```

---

## 🆘 Getting Help

### Documentation
- **Event Schema**: `/home/jevenson/.claude/lib/observability/event_schema.py`
- **Event Emitter**: `/home/jevenson/.claude/lib/observability/event_emitter.py`
- **Tests**: `/home/jevenson/.claude/lib/test_observability.py`
- **Implementation Summary**: `/home/jevenson/.claude/lib/observability/IMPLEMENTATION_SUMMARY.md`

### Quick Diagnostics
```bash
# Check installation
ls ~/.claude/lib/observability/*.py

# Check logs
ls -lh ~/.claude/logs/events/

# Test event emission
python3 -c "from observability.event_emitter import EventEmitter; e = EventEmitter(); print('✓ Observability working')"

# View latest events
tail -20 ~/.claude/logs/events/stream.jsonl | jq '.'
```

---

**Last Updated**: 2025-11-03
**Version**: 1.0.0
**Component**: Priority 4 Component C4 - Multi-Agent Observability
