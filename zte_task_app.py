#!/usr/bin/env python3
"""
ZTE Task Management Web UI
Full Application Pattern (Level 5) - Single-User Zero-Touch Engineering

Unified interface combining:
1. INTAKE: Task submission with form builder
2. OBSERVATION: Real-time monitoring of task execution via event stream
3. RESULTS: Task results viewer with quality metrics

Architecture:
- Streamlit-based single-page application
- Direct file writes to ADZ (~/dropzone/tasks/)
- Real-time event polling from observability stream
- No team collaboration features (single-user design)

Usage:
    streamlit run zte_task_app.py --server.port 8501

Author: ZTE Platform
Version: 1.0.0
"""

import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

# ============================================================================
# CONFIGURATION
# ============================================================================

# Directory paths
DROPZONE_ROOT = Path.home() / "dropzone"
TASKS_DIR = DROPZONE_ROOT / "tasks"
RESULTS_DIR = DROPZONE_ROOT / "results"
ARCHIVE_DIR = DROPZONE_ROOT / "archive"
EVENTS_DIR = Path.home() / ".claude" / "logs" / "events"
STREAM_FILE = EVENTS_DIR / "stream.jsonl"

# Ensure directories exist
TASKS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

# Auto-refresh interval (seconds)
REFRESH_INTERVAL = 2

# Workflow options
WORKFLOW_OPTIONS = {
    "auto": "Automatic (ZTE decides optimal workflow)",
    "specialized_roles": "Specialized Roles (4 phases: Architect → Developer → Tester → Reviewer)",
    "parallel": "Parallel Development (Multi-component concurrent execution)",
    "progressive": "Progressive Enhancement (Simple → Advanced iterative refinement)"
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "submitted_tasks" not in st.session_state:
    st.session_state.submitted_tasks = []

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if "filter_component" not in st.session_state:
    st.session_state.filter_component = "All"

if "filter_severity" not in st.session_state:
    st.session_state.filter_severity = "All"

if "auto_scroll" not in st.session_state:
    st.session_state.auto_scroll = True

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_task_id() -> str:
    """Generate unique task ID with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"task_{timestamp}"


def submit_task_to_adz(task_data: Dict[str, Any]) -> str:
    """
    Submit task to Agentic Drop Zone by writing JSON file.

    Args:
        task_data: Task definition dictionary

    Returns:
        task_id of submitted task
    """
    task_id = generate_task_id()
    task_file = TASKS_DIR / f"{task_id}.json"

    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)

    st.session_state.submitted_tasks.append({
        "task_id": task_id,
        "submitted_at": datetime.now().isoformat(),
        "task": task_data.get("task", "")[:100]
    })

    return task_id


def read_event_stream() -> List[Dict]:
    """
    Read latest events from observability stream.

    Returns:
        List of event dictionaries (most recent first)
    """
    if not STREAM_FILE.exists():
        return []

    try:
        events = []
        with open(STREAM_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return list(reversed(events))  # Most recent first
    except Exception as e:
        st.error(f"Failed to read event stream: {e}")
        return []


def read_task_results() -> List[Dict]:
    """
    Read all task results from results directory.

    Returns:
        List of result dictionaries sorted by completion time
    """
    results = []

    for result_file in RESULTS_DIR.glob("*_result.json"):
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
                result["result_file"] = result_file.name
                results.append(result)
        except Exception as e:
            st.warning(f"Failed to read {result_file.name}: {e}")

    # Sort by completion time (most recent first)
    results.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    return results


def get_statistics() -> Dict[str, Any]:
    """
    Calculate statistics from submitted tasks and results.

    Returns:
        Dict with counts, success rate, total cost, etc.
    """
    results = read_task_results()

    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r.get("status") == "success")
    total_cost = sum(r.get("cost_usd", 0.0) for r in results)
    avg_quality = sum(r.get("quality_score", 0) for r in results) / max(total_tasks, 1)

    return {
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "failed_tasks": total_tasks - successful_tasks,
        "success_rate": (successful_tasks / max(total_tasks, 1)) * 100,
        "total_cost_usd": total_cost,
        "avg_quality_score": avg_quality
    }


def format_event_for_display(event: Dict) -> str:
    """
    Format event as human-readable string for display.

    Args:
        event: Event dictionary

    Returns:
        Formatted string
    """
    # Extract key fields
    timestamp = event.get("timestamp", "")[:19]  # Cut off timezone
    component = event.get("component", "unknown")
    severity = event.get("severity", "INFO")
    message = event.get("message", "")

    # Emoji for severity
    emoji_map = {
        "DEBUG": "🐛",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨"
    }
    emoji = emoji_map.get(severity, "•")

    # Build display string
    display = f"{emoji} **[{timestamp}]** `{component}` - {message}"

    # Add metrics if present
    metrics = []
    if event.get("duration_ms"):
        metrics.append(f"{event['duration_ms']:.0f}ms")
    if event.get("cost_usd"):
        metrics.append(f"${event['cost_usd']:.4f}")
    if event.get("quality_score"):
        metrics.append(f"Q:{event['quality_score']:.0f}")

    if metrics:
        display += f" _({', '.join(metrics)})_"

    return display


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="ZTE Task Management",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="main-header">🚀 ZTE Task Management Platform</div>', unsafe_allow_html=True)
    st.markdown("**Zero-Touch Engineering** | Single-User Autonomous Development Environment")

    # ========================================================================
    # SIDEBAR: Status & Statistics
    # ========================================================================

    with st.sidebar:
        st.header("📊 Platform Status")

        # Statistics
        stats = get_statistics()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Tasks", stats["total_tasks"])
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
        with col2:
            st.metric("Successful", stats["successful_tasks"])
            st.metric("Failed", stats["failed_tasks"])

        st.metric("Total Cost", f"${stats['total_cost_usd']:.4f}")
        st.metric("Avg Quality", f"{stats['avg_quality_score']:.1f}/100")

        st.divider()

        # Recently submitted tasks
        st.subheader("🕒 Recent Submissions")
        if st.session_state.submitted_tasks:
            for task_info in reversed(st.session_state.submitted_tasks[-5:]):
                st.text(f"• {task_info['task_id']}")
                st.caption(task_info['task'][:50] + "...")
        else:
            st.info("No tasks submitted yet")

        st.divider()

        # Refresh controls
        st.subheader("🔄 Refresh Settings")
        if st.button("🔃 Manual Refresh", use_container_width=True):
            st.rerun()

        auto_refresh = st.checkbox("Auto-refresh (2s)", value=True)

        # Auto-refresh logic
        if auto_refresh:
            if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
                st.session_state.last_refresh = time.time()
                st.rerun()

    # ========================================================================
    # MAIN CONTENT: INTAKE + OBSERVATION
    # ========================================================================

    # Create two main sections with tabs
    tab1, tab2, tab3 = st.tabs(["📝 INTAKE (Submit Task)", "👁️ OBSERVATION (Live Events)", "📁 RESULTS (Task Outputs)"])

    # ========================================================================
    # TAB 1: INTAKE - Task Submission Form
    # ========================================================================

    with tab1:
        st.markdown('<div class="section-header">📝 Task Intake - Submit to ZTE Pipeline</div>', unsafe_allow_html=True)

        with st.form("task_submission_form"):
            st.markdown("**Define your task below. The Agentic Drop Zone (ADZ) will automatically process it.**")

            # Task description
            task_description = st.text_area(
                "Task Description*",
                height=150,
                placeholder="Example: Create a Python REST API for user authentication with JWT tokens, "
                           "including signup, login, and logout endpoints. Include comprehensive tests.",
                help="Describe what you want to build in natural language"
            )

            # Workflow selection
            workflow = st.selectbox(
                "Workflow Strategy",
                options=list(WORKFLOW_OPTIONS.keys()),
                format_func=lambda x: WORKFLOW_OPTIONS[x],
                help="Choose execution workflow (auto recommended)"
            )

            # Context inputs (collapsible)
            with st.expander("⚙️ Advanced Context Settings"):
                col1, col2 = st.columns(2)

                with col1:
                    language = st.selectbox(
                        "Programming Language",
                        ["python", "javascript", "typescript", "go", "rust", "java"],
                        help="Primary language for code generation"
                    )

                    include_tests = st.checkbox("Include Tests", value=True)
                    include_docs = st.checkbox("Include Documentation", value=True)

                with col2:
                    quality_target = st.slider(
                        "Quality Target",
                        min_value=70,
                        max_value=100,
                        value=85,
                        help="Minimum quality score (higher = more refinement iterations)"
                    )

                    priority = st.select_slider(
                        "Priority",
                        options=["low", "normal", "high"],
                        value="normal"
                    )

            # Submit button
            submitted = st.form_submit_button("🚀 Submit Task to ADZ", type="primary", use_container_width=True)

            if submitted:
                if not task_description.strip():
                    st.error("❌ Task description is required!")
                else:
                    # Build task data structure
                    task_data = {
                        "task": task_description.strip(),
                        "workflow": workflow,
                        "context": {
                            "language": language,
                            "quality_target": quality_target,
                            "include_tests": include_tests,
                            "include_docs": include_docs
                        },
                        "priority": priority
                    }

                    # Submit to ADZ
                    try:
                        task_id = submit_task_to_adz(task_data)
                        st.success(f"✅ Task submitted successfully! Task ID: **{task_id}**")
                        st.info("📂 Task file written to `~/dropzone/tasks/`. ADZ will process automatically.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Failed to submit task: {e}")

    # ========================================================================
    # TAB 2: OBSERVATION - Live Event Stream
    # ========================================================================

    with tab2:
        st.markdown('<div class="section-header">👁️ Live Observation - Real-Time Event Stream</div>', unsafe_allow_html=True)

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_component = st.selectbox(
                "Filter by Component",
                ["All", "orchestrator", "developer-agent", "architect-agent", "tester-agent", "reviewer-agent", "agentic-dropzone"],
                key="filter_component_select"
            )

        with col2:
            filter_severity = st.selectbox(
                "Filter by Severity",
                ["All", "INFO", "WARNING", "ERROR", "CRITICAL"],
                key="filter_severity_select"
            )

        with col3:
            max_events = st.number_input(
                "Max Events to Display",
                min_value=10,
                max_value=200,
                value=50,
                step=10
            )

        st.divider()

        # Read and filter events
        events = read_event_stream()

        # Apply filters
        if filter_component != "All":
            events = [e for e in events if e.get("component") == filter_component]

        if filter_severity != "All":
            events = [e for e in events if e.get("severity") == filter_severity]

        # Limit to max_events
        events = events[:max_events]

        # Display events
        if events:
            st.info(f"Showing **{len(events)}** most recent events (auto-refreshing every {REFRESH_INTERVAL}s)")

            for event in events:
                display_text = format_event_for_display(event)
                st.markdown(display_text)

                # Show expandable details for errors
                if event.get("severity") in ["ERROR", "CRITICAL"]:
                    with st.expander("🔍 Error Details"):
                        st.json(event)
        else:
            st.warning("No events found. Submit a task to see live execution events.")
            st.info("Events are written to `~/.claude/logs/events/stream.jsonl` by the observability system.")

    # ========================================================================
    # TAB 3: RESULTS - Task Results Viewer
    # ========================================================================

    with tab3:
        st.markdown('<div class="section-header">📁 Task Results - Completed Outputs</div>', unsafe_allow_html=True)

        # Read results
        results = read_task_results()

        if results:
            st.success(f"Found **{len(results)}** completed tasks")

            # Display results as cards
            for result in results:
                task_id = result.get("task_id", "unknown")
                status = result.get("status", "unknown")
                quality = result.get("quality_score", 0)
                cost = result.get("cost_usd", 0.0)
                duration = result.get("duration_seconds", 0)
                workflow = result.get("workflow_used", "unknown")

                # Status emoji
                status_emoji = "✅" if status == "success" else "❌"

                with st.expander(f"{status_emoji} **{task_id}** | Quality: {quality}/100 | Cost: ${cost:.4f}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Status", status.upper())
                        st.metric("Workflow", workflow)

                    with col2:
                        st.metric("Quality Score", f"{quality}/100")
                        st.metric("Duration", f"{duration:.1f}s")

                    with col3:
                        st.metric("Cost", f"${cost:.4f}")
                        st.metric("Completed", result.get("completed_at", "")[:10])

                    st.divider()

                    # Task description
                    st.markdown("**Task:**")
                    st.info(result.get("task", "No description"))

                    # Output
                    st.markdown("**Generated Output:**")
                    output = result.get("output", "No output")
                    st.code(output, language="text")

                    # Metadata
                    with st.expander("📊 Full Metadata"):
                        st.json(result)
        else:
            st.info("No completed tasks yet. Submit tasks in the INTAKE tab to see results here.")
            st.markdown("Results will appear in `~/dropzone/results/` after task execution completes.")

    # ========================================================================
    # FOOTER
    # ========================================================================

    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        🚀 <strong>ZTE Task Management Platform v1.0.0</strong> |
        Zero-Touch Engineering |
        Single-User Autonomous Development |
        <a href="https://github.com/anthropics/claude-code" target="_blank">Documentation</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
