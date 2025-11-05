#!/usr/bin/env python3
"""
ZTE Task Management Web UI - ENHANCED (Phase D)
Full Application Pattern (Level 5) with:
- Polished drag-and-drop ADZ component with animations
- RAG Topic Management Panel for optimized queries
- Modern UI with micro-interactions
- UltraThink enforcement for Opus 4.1 validation

Architecture:
- Streamlit-based single-page application
- Drag-and-drop file upload with CSS animations
- Topic-based RAG filtering for routing optimization
- Real-time event streaming from observability system
- Zero-CLI, single-user design

Usage:
    streamlit run zte_task_app_enhanced.py --server.port 8501

Author: ZTE Platform - Phase D
Version: 2.0.0 (Enhanced)
"""

import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import base64

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

# RAG configuration
RAG_TOPICS = [
    "General Knowledge",
    "Medical & Health",
    "Automotive & Transportation",
    "Financial & Legal",
    "Technology & Software",
    "Education & Learning",
    "Business & Management",
    "Science & Research"
]

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

if "selected_rag_topics" not in st.session_state:
    st.session_state.selected_rag_topics = []

if "drag_drop_active" not in st.session_state:
    st.session_state.drag_drop_active = False

# ============================================================================
# CUSTOM CSS & ANIMATIONS
# ============================================================================

def inject_custom_css():
    """Inject custom CSS for modern UI with animations."""
    st.markdown("""
    <style>
    /* Main header styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        animation: fadeInDown 0.8s ease-out;
    }

    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
        animation: slideInLeft 0.6s ease-out;
    }

    /* Drag & Drop Zone */
    .drop-zone {
        border: 3px dashed #667eea;
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .drop-zone::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.3) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.5s ease;
    }

    .drop-zone:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }

    .drop-zone:hover::before {
        opacity: 1;
        animation: pulse 2s infinite;
    }

    .drop-zone-active {
        border-color: #4CAF50;
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(76, 175, 80, 0.1) 100%);
        animation: shake 0.5s ease-in-out;
    }

    /* Topic Pills */
    .topic-pill {
        display: inline-block;
        padding: 0.4rem 1rem;
        margin: 0.3rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .topic-pill:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }

    .topic-pill-selected {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        animation: bounceIn 0.5s ease-out;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: fadeIn 0.8s ease-out;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }

    /* Event Stream */
    .event-item {
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        background: rgba(102, 126, 234, 0.05);
        border-radius: 8px;
        transition: all 0.3s ease;
        animation: slideInRight 0.5s ease-out;
    }

    .event-item:hover {
        background: rgba(102, 126, 234, 0.1);
        transform: translateX(5px);
        border-left-width: 6px;
    }

    .event-error {
        border-left-color: #f44336;
        background: rgba(244, 67, 54, 0.05);
    }

    .event-warning {
        border-left-color: #ff9800;
        background: rgba(255, 152, 0, 0.05);
    }

    /* Animations */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    @keyframes pulse {
        0%, 100% {
            transform: scale(1) rotate(0deg);
        }
        50% {
            transform: scale(1.1) rotate(180deg);
        }
    }

    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }

    @keyframes bounceIn {
        0% {
            transform: scale(0.5);
            opacity: 0;
        }
        50% {
            transform: scale(1.1);
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }

    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }

    /* Progress indicator */
    .processing-indicator {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(102, 126, 234, 0.3);
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

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

    # Add RAG topic metadata if topics selected
    if st.session_state.selected_rag_topics:
        task_data["rag_topics"] = st.session_state.selected_rag_topics
        task_data["context"]["rag_filter"] = {
            "topics": st.session_state.selected_rag_topics,
            "routing_strategy": "topic_optimized"
        }

    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)

    st.session_state.submitted_tasks.append({
        "task_id": task_id,
        "submitted_at": datetime.now().isoformat(),
        "task": task_data.get("task", "")[:100],
        "rag_topics": st.session_state.selected_rag_topics.copy() if st.session_state.selected_rag_topics else []
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
        Formatted HTML string
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

    # CSS class based on severity
    css_class = "event-item"
    if severity in ["ERROR", "CRITICAL"]:
        css_class += " event-error"
    elif severity == "WARNING":
        css_class += " event-warning"

    # Build display HTML
    display = f"""
    <div class="{css_class}">
        {emoji} <strong>[{timestamp}]</strong> <code>{component}</code> - {message}
    """

    # Add metrics if present
    metrics = []
    if event.get("duration_ms"):
        metrics.append(f"{event['duration_ms']:.0f}ms")
    if event.get("cost_usd"):
        metrics.append(f"${event['cost_usd']:.4f}")
    if event.get("quality_score"):
        metrics.append(f"Q:{event['quality_score']:.0f}")

    if metrics:
        display += f"<br><small>({', '.join(metrics)})</small>"

    display += "</div>"

    return display


# ============================================================================
# DRAG & DROP ADZ COMPONENT
# ============================================================================

def render_adz_dropzone():
    """Render polished drag-and-drop zone for task submission."""
    st.markdown('<div class="section-header">📥 DRAG & DROP TASK SUBMISSION</div>', unsafe_allow_html=True)

    # Drag-and-drop zone HTML
    drop_zone_html = """
    <div class="drop-zone" id="dropZone">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📁</div>
        <h3>Drag & Drop Task File Here</h3>
        <p style="color: #666; margin-top: 0.5rem;">
            Or click to browse (.json, .txt, .md files)
        </p>
        <p style="color: #999; font-size: 0.9rem; margin-top: 1rem;">
            Task files will be automatically processed by the Agentic Drop Zone
        </p>
    </div>
    """

    st.markdown(drop_zone_html, unsafe_allow_html=True)

    # File uploader (hidden, triggered by drag-and-drop)
    uploaded_file = st.file_uploader(
        "Upload task file",
        type=["json", "txt", "md"],
        key="adz_uploader",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        st.success(f"✅ File received: {uploaded_file.name}")

        # Parse file content
        try:
            content = uploaded_file.read().decode("utf-8")

            # Try to parse as JSON
            if uploaded_file.name.endswith(".json"):
                task_data = json.loads(content)
            else:
                # Plain text - wrap in task structure
                task_data = {
                    "task": content,
                    "workflow": "auto",
                    "context": {
                        "language": "python",
                        "quality_target": 85
                    },
                    "priority": "normal"
                }

            # Submit to ADZ
            task_id = submit_task_to_adz(task_data)

            st.balloons()
            st.success(f"🚀 Task submitted successfully! Task ID: **{task_id}**")
            st.info("📂 Task file written to `~/dropzone/tasks/`. ADZ will process automatically.")

        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON format: {e}")
        except Exception as e:
            st.error(f"❌ Failed to process file: {e}")


# ============================================================================
# RAG TOPIC MANAGEMENT PANEL
# ============================================================================

def render_rag_topic_panel():
    """Render RAG topic management panel for query optimization."""
    st.markdown('<div class="section-header">🎯 RAG TOPIC MANAGEMENT</div>', unsafe_allow_html=True)

    st.markdown("""
    **Topic-Based Query Optimization**: Select relevant topics to optimize RAG retrieval routing.
    The Agentic RAG Pipeline will use these topics as metadata constraints for more accurate results.
    """)

    # Display topic pills
    st.markdown("**Available Topics:**")

    # Create columns for topic pills
    cols = st.columns(4)

    for idx, topic in enumerate(RAG_TOPICS):
        col_idx = idx % 4
        with cols[col_idx]:
            is_selected = topic in st.session_state.selected_rag_topics

            if st.button(
                topic,
                key=f"topic_{idx}",
                help=f"Click to {'remove' if is_selected else 'add'} {topic}",
                type="primary" if is_selected else "secondary"
            ):
                if is_selected:
                    st.session_state.selected_rag_topics.remove(topic)
                else:
                    st.session_state.selected_rag_topics.append(topic)
                st.rerun()

    # Display selected topics
    if st.session_state.selected_rag_topics:
        st.success(f"✅ **Selected Topics ({len(st.session_state.selected_rag_topics)})**: {', '.join(st.session_state.selected_rag_topics)}")

        # Clear button
        if st.button("🗑️ Clear All Topics"):
            st.session_state.selected_rag_topics = []
            st.rerun()
    else:
        st.info("ℹ️ No topics selected. Tasks will use general RAG retrieval without topic filtering.")

    # RAG optimization info
    with st.expander("📚 RAG Optimization Details"):
        st.markdown("""
        **How Topic Filtering Works:**

        1. **Routing Optimization**: Selected topics are passed as metadata to the Agentic RAG Pipeline's routing layer
        2. **Query Narrowing**: The Router (Haiku 4.5) uses topics to choose optimal retrieval strategy
        3. **Context Filtering**: Only relevant documents matching selected topics are retrieved
        4. **Quality Improvement**: Reduces noise, improves precision, and lowers latency

        **Best Practices:**
        - Select 1-3 topics for best results
        - Too many topics = wider search (may reduce precision)
        - No topics = general search (use for broad queries)

        **Example Use Cases:**
        - Medical query → Select "Medical & Health"
        - Car purchase advice → Select "Automotive & Transportation"
        - Investment analysis → Select "Financial & Legal"
        """)


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="ZTE Task Management - Enhanced",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject custom CSS
    inject_custom_css()

    # Header
    st.markdown('<div class="main-header">🚀 ZTE Task Management Platform</div>', unsafe_allow_html=True)
    st.markdown("**Zero-Touch Engineering (Phase D)** | Enhanced UI with Drag-and-Drop ADZ & RAG Topic Management")

    # ========================================================================
    # SIDEBAR: Status & Statistics
    # ========================================================================

    with st.sidebar:
        st.header("📊 Platform Status")

        # Statistics
        stats = get_statistics()

        # Create metric cards
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="margin: 0; color: #667eea;">{stats['total_tasks']}</h2>
            <p style="margin: 0; color: #666;">Total Tasks</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <h2 style="margin: 0; color: #4CAF50;">{stats['success_rate']:.1f}%</h2>
            <p style="margin: 0; color: #666;">Success Rate</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <h2 style="margin: 0; color: #ff9800;">${stats['total_cost_usd']:.4f}</h2>
            <p style="margin: 0; color: #666;">Total Cost</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <h2 style="margin: 0; color: #9c27b0;">{stats['avg_quality_score']:.1f}/100</h2>
            <p style="margin: 0; color: #666;">Avg Quality</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Recently submitted tasks
        st.subheader("🕒 Recent Submissions")
        if st.session_state.submitted_tasks:
            for task_info in reversed(st.session_state.submitted_tasks[-5:]):
                st.text(f"• {task_info['task_id']}")
                st.caption(task_info['task'][:50] + "...")
                if task_info.get('rag_topics'):
                    st.caption(f"📚 Topics: {', '.join(task_info['rag_topics'][:2])}")
        else:
            st.info("No tasks submitted yet")

        st.divider()

        # Refresh controls
        st.subheader("🔄 Refresh Settings")
        if st.button("🔃 Manual Refresh", use_container_width=True):
            st.rerun()

        auto_refresh = st.checkbox("Auto-refresh (2s)", value=True)

        # UltraThink status indicator
        st.divider()
        st.success("🧠 **UltraThink Active**\n\nOpus 4.1 validation uses extended reasoning")

        # Auto-refresh logic
        if auto_refresh:
            if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
                st.session_state.last_refresh = time.time()
                st.rerun()

    # ========================================================================
    # MAIN CONTENT: Enhanced Tabs
    # ========================================================================

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 DRAG & DROP ADZ",
        "🎯 RAG TOPICS",
        "👁️ OBSERVATION (Live Events)",
        "📁 RESULTS (Task Outputs)"
    ])

    # ========================================================================
    # TAB 1: Drag & Drop ADZ
    # ========================================================================

    with tab1:
        render_adz_dropzone()

        st.divider()

        # Traditional form (alternative method)
        st.markdown('<div class="section-header">📝 OR Use Traditional Form</div>', unsafe_allow_html=True)

        with st.form("task_submission_form"):
            task_description = st.text_area(
                "Task Description*",
                height=150,
                placeholder="Example: Create a Python REST API for user authentication...",
                help="Describe what you want to build in natural language"
            )

            col1, col2 = st.columns(2)

            with col1:
                workflow = st.selectbox(
                    "Workflow Strategy",
                    options=list(WORKFLOW_OPTIONS.keys()),
                    format_func=lambda x: WORKFLOW_OPTIONS[x],
                    help="Choose execution workflow (auto recommended)"
                )

                language = st.selectbox(
                    "Programming Language",
                    ["python", "javascript", "typescript", "go", "rust", "java"],
                    help="Primary language for code generation"
                )

            with col2:
                quality_target = st.slider(
                    "Quality Target",
                    min_value=70,
                    max_value=100,
                    value=85,
                    help="Minimum quality score"
                )

                priority = st.select_slider(
                    "Priority",
                    options=["low", "normal", "high"],
                    value="normal"
                )

            submitted = st.form_submit_button("🚀 Submit Task", type="primary", use_container_width=True)

            if submitted:
                if not task_description.strip():
                    st.error("❌ Task description is required!")
                else:
                    task_data = {
                        "task": task_description.strip(),
                        "workflow": workflow,
                        "context": {
                            "language": language,
                            "quality_target": quality_target
                        },
                        "priority": priority
                    }

                    try:
                        task_id = submit_task_to_adz(task_data)
                        st.success(f"✅ Task submitted successfully! Task ID: **{task_id}**")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Failed to submit task: {e}")

    # ========================================================================
    # TAB 2: RAG Topic Management
    # ========================================================================

    with tab2:
        render_rag_topic_panel()

    # ========================================================================
    # TAB 3: OBSERVATION - Live Event Stream
    # ========================================================================

    with tab3:
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
                display_html = format_event_for_display(event)
                st.markdown(display_html, unsafe_allow_html=True)

                # Show expandable details for errors
                if event.get("severity") in ["ERROR", "CRITICAL"]:
                    with st.expander("🔍 Error Details"):
                        st.json(event)
        else:
            st.warning("No events found. Submit a task to see live execution events.")

    # ========================================================================
    # TAB 4: RESULTS - Task Results Viewer
    # ========================================================================

    with tab4:
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

                    # RAG topics if present
                    if result.get("rag_topics"):
                        st.markdown("**RAG Topics Used:**")
                        topics_html = " ".join([
                            f'<span class="topic-pill topic-pill-selected">{topic}</span>'
                            for topic in result["rag_topics"]
                        ])
                        st.markdown(topics_html, unsafe_allow_html=True)

                    # Output
                    st.markdown("**Generated Output:**")
                    output = result.get("output", "No output")
                    st.code(output, language="text")

                    # Metadata
                    with st.expander("📊 Full Metadata"):
                        st.json(result)
        else:
            st.info("No completed tasks yet. Submit tasks to see results here.")

    # ========================================================================
    # FOOTER
    # ========================================================================

    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        🚀 <strong>ZTE Task Management Platform v2.0.0 (Enhanced)</strong> |
        Zero-Touch Engineering with UltraThink | Phase D Complete |
        <a href="https://github.com/anthropics/claude-code" target="_blank">Documentation</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
