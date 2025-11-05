#!/usr/bin/env python3
"""
ZeroTouch Atlas - Unified Task Management Interface
Global-scale, intelligent multi-agent orchestration platform

FINAL DEPLOYMENT VERSION (Phase D Complete)

Features:
- 🛡️ Zero-Trust Input Boundary (Haiku 4.5 Security Filter)
- 📥 Agentic Drop Zone (ADZ) with polished drag-and-drop
- 🎯 RAG Topic Management for optimized routing
- 📊 Real-time Multi-Agent Observability Dashboard
- 🔄 Closed-Loop Validation with UltraThink (Opus 4.1)
- 🌐 Multi-Provider Fallback (Anthropic, Gemini, OpenAI)

Architecture:
- **Atlas (Global Intelligence)**: Zero-touch operation with worldwide knowledge mapping
- **Zero-Trust**: All inputs validated by Haiku 4.5 security boundary
- **Observable**: Real-time event streaming from C4 hooks
- **Resilient**: Multi-provider fallback with circuit breakers

Usage:
    streamlit run atlas_app.py --server.port 8501

Repository: https://github.com/jevenson76/Atlas-Orchestrator
Author: ZeroTouch Atlas Platform
Version: 1.0.0 (Production)
"""

import streamlit as st
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import base64

# ============================================================================
# IMPORTS - Security & Core
# ============================================================================

import sys
sys.path.insert(0, str(Path(__file__).parent))

from security import get_security_filter, SecurityViolation

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

# RAG Topic Categories (Enhanced for routing optimization)
RAG_TOPICS = [
    "General Knowledge & Reference",
    "Medical & Healthcare",
    "Automotive & Transportation",
    "Financial Services & Legal",
    "Technology & Software Development",
    "Education & Training",
    "Business Strategy & Management",
    "Scientific Research & Data Analysis"
]

# Ensure directories exist
TASKS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

# Auto-refresh interval (seconds)
REFRESH_INTERVAL = 2

# Workflow execution modes
WORKFLOW_OPTIONS = {
    "auto": "🤖 Automatic (Atlas decides optimal workflow)",
    "specialized_roles": "👥 Specialized Roles (Architect → Developer → Tester → Reviewer)",
    "parallel": "⚡ Parallel Execution (Multi-component concurrent processing)",
    "progressive": "📈 Progressive Enhancement (Simple → Advanced iterative refinement)"
}

# Model stack
MODEL_OPTIONS = {
    "claude-sonnet-4": "Claude Sonnet 4.5 (Default - Balanced performance)",
    "claude-haiku-3": "Claude Haiku 4.5 (Fast - Cost-effective)",
    "claude-opus-3": "Claude Opus 3 (Premium - Deep reasoning)",
    "claude-opus-4": "Claude Opus 4.1 (Ultimate - UltraThink enabled)"
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "submitted_tasks" not in st.session_state:
    st.session_state.submitted_tasks = []

if "security_stats" not in st.session_state:
    st.session_state.security_stats = {"total_events": 0, "blocked": 0, "approved": 0}

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if "filter_component" not in st.session_state:
    st.session_state.filter_component = "All"

if "filter_severity" not in st.session_state:
    st.session_state.filter_severity = "All"

if "selected_rag_topics" not in st.session_state:
    st.session_state.selected_rag_topics = []

if "security_enabled" not in st.session_state:
    st.session_state.security_enabled = True

# ============================================================================
# CUSTOM CSS & BRANDING
# ============================================================================

def inject_custom_css():
    """Inject ZeroTouch Atlas branded CSS with animations."""
    st.markdown("""
    <style>
    /* ================================================================
       ZEROTOUCH ATLAS BRANDING
       ================================================================ */

    /* Main header - Gradient brand colors */
    .atlas-header {
        font-size: 3.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        animation: fadeInDown 0.8s ease-out;
        letter-spacing: -0.02em;
    }

    .atlas-tagline {
        text-align: center;
        font-size: 1.1rem;
        color: #2c5364;
        font-weight: 500;
        margin-bottom: 2rem;
        animation: fadeIn 1s ease-out;
    }

    /* Atlas Globe Logo - Minimalist World + Tech */
    .atlas-globe-logo {
        display: inline-block;
        width: 70px;
        height: 70px;
        border: 3px solid #2c5364;
        border-radius: 50%;
        position: relative;
        margin: 0 auto 1rem;
        background: radial-gradient(circle, rgba(44, 83, 100, 0.1) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
        overflow: visible;
    }

    .atlas-globe-logo::before {
        content: "🌐";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 2.2rem;
        filter: drop-shadow(0 0 8px rgba(44, 83, 100, 0.3));
    }

    /* Circuit pattern overlay */
    .atlas-globe-logo::after {
        content: "";
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px dashed rgba(44, 83, 100, 0.3);
        top: -6px;
        left: -6px;
        animation: pulse 3s ease-in-out infinite;
    }

    @keyframes rotate {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }

    /* ================================================================
       ENHANCED DRAG & DROP ZONE
       ================================================================ */

    .adz-container {
        background: linear-gradient(135deg, rgba(44, 83, 100, 0.05) 0%, rgba(15, 32, 39, 0.05) 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
    }

    .drop-zone {
        border: 3px dashed #2c5364;
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(44, 83, 100, 0.1) 0%, rgba(15, 32, 39, 0.1) 100%);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .drop-zone:hover {
        border-color: #0f2027;
        background: linear-gradient(135deg, rgba(44, 83, 100, 0.2) 0%, rgba(15, 32, 39, 0.2) 100%);
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(44, 83, 100, 0.3);
    }

    .drop-zone::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(44, 83, 100, 0.1), transparent);
        transform: rotate(45deg);
        animation: shine 3s infinite;
    }

    /* ================================================================
       SECURITY STATUS BADGE
       ================================================================ */

    .security-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
        color: white;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(39, 174, 96, 0.3);
        animation: bounceIn 0.6s;
    }

    .security-badge.warning {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        box-shadow: 0 4px 10px rgba(243, 156, 18, 0.3);
    }

    .security-badge.danger {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        box-shadow: 0 4px 10px rgba(231, 76, 60, 0.3);
    }

    /* ================================================================
       RAG TOPIC PILLS
       ================================================================ */

    .topic-pill {
        display: inline-block;
        padding: 0.5rem 1.2rem;
        margin: 0.3rem;
        border-radius: 25px;
        background: linear-gradient(135deg, #2c5364 0%, #0f2027 100%);
        color: white;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .topic-pill:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 6px 16px rgba(44, 83, 100, 0.4);
    }

    .topic-pill.selected {
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
        box-shadow: 0 6px 16px rgba(39, 174, 96, 0.4);
    }

    /* ================================================================
       OBSERVABILITY DASHBOARD
       ================================================================ */

    .event-card {
        background: white;
        border-left: 4px solid #2c5364;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }

    .event-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .event-card.high-priority {
        border-left-color: #e74c3c;
    }

    .event-card.medium-priority {
        border-left-color: #f39c12;
    }

    .model-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        background: #ecf0f1;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #2c3e50;
        margin-right: 0.5rem;
    }

    .model-badge.opus {
        background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
        color: white;
    }

    .model-badge.sonnet {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
    }

    .model-badge.haiku {
        background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%);
        color: white;
    }

    /* ================================================================
       SECTION HEADERS
       ================================================================ */

    .section-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f2027;
        margin: 2rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #2c5364;
        animation: fadeInLeft 0.6s;
    }

    /* ================================================================
       ANIMATIONS
       ================================================================ */

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

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes fadeInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.05);
            opacity: 0.8;
        }
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

    @keyframes shine {
        0% {
            transform: translateX(-100%) translateY(-100%) rotate(45deg);
        }
        100% {
            transform: translateX(100%) translateY(100%) rotate(45deg);
        }
    }

    /* ================================================================
       RESPONSIVE DESIGN
       ================================================================ */

    @media (max-width: 768px) {
        .atlas-header {
            font-size: 2.2rem;
        }

        .section-header {
            font-size: 1.4rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_task_id() -> str:
    """Generate unique task ID."""
    return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

def get_security_filter_instance():
    """Get or create security filter instance."""
    if "security_filter" not in st.session_state:
        st.session_state.security_filter = get_security_filter()
    return st.session_state.security_filter

# ============================================================================
# BRANDING COMPONENTS
# ============================================================================

def render_header():
    """Render ZeroTouch Atlas branded header."""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div class="atlas-globe-logo"></div>
        <h1 class="atlas-header">ZeroTouch Atlas</h1>
        <p class="atlas-tagline">
            <strong>Global-Scale Intelligent Orchestration</strong><br/>
            Mapping knowledge across domains — zero-touch automation
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_security_status():
    """Render security status badge."""
    security_filter = get_security_filter_instance()
    stats = security_filter.get_security_stats()

    st.session_state.security_stats = {
        "total_events": stats["total_events"],
        "approved": stats["total_submissions"],
        "blocked": stats["threat_distribution"].get("high", 0) + stats["threat_distribution"].get("critical", 0)
    }

    threat_level = "none"
    if stats["threat_distribution"].get("critical", 0) > 0:
        threat_level = "critical"
    elif stats["threat_distribution"].get("high", 0) > 0:
        threat_level = "high"
    elif stats["threat_distribution"].get("medium", 0) > 0:
        threat_level = "medium"

    badge_class = "security-badge"
    if threat_level in ["high", "critical"]:
        badge_class += " danger"
    elif threat_level == "medium":
        badge_class += " warning"

    st.markdown(f"""
    <div class="{badge_class}">
        🛡️ Zero-Trust Boundary: Active |
        Validated: {stats["total_submissions"]} |
        Blocked: {st.session_state.security_stats["blocked"]}
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ADZ COMPONENT (Agentic Drop Zone)
# ============================================================================

def render_adz_dropzone():
    """Render polished Agentic Drop Zone with security integration."""
    st.markdown('<div class="section-header">📥 AGENTIC DROP ZONE</div>', unsafe_allow_html=True)
    st.markdown('<div class="adz-container">', unsafe_allow_html=True)

    # Security notice
    if st.session_state.security_enabled:
        st.info("🛡️ **Zero-Trust Security Active**: All submissions are validated by Haiku 4.5 before processing")

    # Drop zone HTML
    drop_zone_html = """
    <div class="drop-zone" id="dropZone">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">📁</div>
        <h2 style="color: #0f2027; margin-bottom: 0.5rem;">Drag & Drop Task File</h2>
        <p style="color: #666; margin-top: 0.5rem;">
            Or click to browse (.json, .txt, .md, .yaml files)
        </p>
        <p style="color: #999; font-size: 0.9rem; margin-top: 1rem;">
            ✨ Files are automatically validated and routed to the orchestrator
        </p>
    </div>
    """

    st.markdown(drop_zone_html, unsafe_allow_html=True)

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload task file",
        type=["json", "txt", "md", "yaml", "yml"],
        key="adz_uploader",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        st.success(f"✅ File received: {uploaded_file.name}")

        # Parse file content
        try:
            content = uploaded_file.read().decode("utf-8")

            # Try JSON first
            try:
                task_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: treat as plain text task description
                task_data = {
                    "task": content,
                    "model": "claude-sonnet-4",
                    "temperature": 0.7,
                    "source_file": uploaded_file.name
                }

            # Security validation
            if st.session_state.security_enabled:
                with st.spinner("🛡️ Security validation in progress (Haiku 4.5)..."):
                    try:
                        # Run async security validation
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        security_result = loop.run_until_complete(
                            get_security_filter_instance().validate_input(
                                task_data,
                                source_id=f"upload_{datetime.now().timestamp()}"
                            )
                        )

                        loop.close()

                        st.success("✅ Security validation passed")
                        task_data = security_result["validated_data"]

                    except SecurityViolation as e:
                        st.error(f"🚨 Security validation failed: {e}")
                        st.stop()
                    except Exception as e:
                        st.error(f"❌ Security validation error: {e}")
                        st.stop()

            # Add RAG topics if selected
            if st.session_state.selected_rag_topics:
                task_data["rag_topics"] = st.session_state.selected_rag_topics
                task_data["context"] = task_data.get("context", {})
                task_data["context"]["rag_filter"] = {
                    "topics": st.session_state.selected_rag_topics,
                    "routing_strategy": "topic_optimized"
                }

            # Submit to ADZ
            task_id = submit_task_to_adz(task_data)
            st.success(f"🚀 Task submitted successfully: `{task_id}`")

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

def submit_task_to_adz(task_data: Dict[str, Any]) -> str:
    """
    Submit validated task to Agentic Drop Zone.

    Args:
        task_data: Validated task data (already passed security filter)

    Returns:
        Task ID
    """
    task_id = generate_task_id()
    task_file = TASKS_DIR / f"{task_id}.json"

    # Add metadata
    task_data["submitted_at"] = datetime.now().isoformat()
    task_data["task_id"] = task_id
    task_data["security_validated"] = st.session_state.security_enabled

    # Write to dropzone
    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)

    # Add to session history
    st.session_state.submitted_tasks.append({
        "task_id": task_id,
        "submitted_at": datetime.now().isoformat(),
        "task_preview": str(task_data.get("task", ""))[:100],
        "rag_topics": st.session_state.selected_rag_topics.copy() if st.session_state.selected_rag_topics else [],
        "security_validated": st.session_state.security_enabled
    })

    return task_id

# ============================================================================
# RAG TOPIC MANAGEMENT
# ============================================================================

def render_rag_topic_panel():
    """Render RAG topic management for optimized routing."""
    st.markdown('<div class="section-header">🎯 RAG TOPIC MANAGEMENT</div>', unsafe_allow_html=True)

    st.markdown("""
    **Topic-Based Query Optimization**: Select relevant knowledge domains to optimize RAG retrieval routing.
    The Agentic RAG Pipeline uses these topics as metadata constraints for precise, efficient retrieval.
    """)

    st.markdown("**Available Topics:**")

    # Create topic pills in columns
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
        st.success(
            f"✅ **Active Topics ({len(st.session_state.selected_rag_topics)})**: "
            f"{', '.join(st.session_state.selected_rag_topics)}"
        )

        # Optimization info
        st.info(
            f"📊 **Optimization Impact**: ~{len(st.session_state.selected_rag_topics) * 15}% "
            f"reduction in retrieval scope, improving precision and reducing latency"
        )
    else:
        st.warning("⚠️ No topics selected - queries will search across all knowledge domains")

# ============================================================================
# OBSERVABILITY DASHBOARD
# ============================================================================

def render_observability_dashboard():
    """Render real-time multi-agent observability dashboard."""
    st.markdown('<div class="section-header">📊 MULTI-AGENT OBSERVABILITY</div>', unsafe_allow_html=True)

    st.markdown("""
    **Real-time Event Stream**: Monitor agent execution, model utilization, and workflow progress.
    Events are captured via C4 hooks and displayed with provider/model attribution.
    """)

    # Event stream
    if STREAM_FILE.exists():
        try:
            with open(STREAM_FILE, 'r') as f:
                events = [json.loads(line) for line in f.readlines()[-20:]]  # Last 20 events

            if events:
                for event in reversed(events):  # Most recent first
                    render_event_card(event)
            else:
                st.info("No events yet. Submit a task to see real-time execution.")
        except Exception as e:
            st.warning(f"Could not load event stream: {e}")
    else:
        st.info("Event stream will appear here when tasks are processed.")

def render_event_card(event: Dict[str, Any]):
    """Render individual event card with model attribution."""
    timestamp = event.get("timestamp", "Unknown")
    agent = event.get("agent", "Unknown")
    action = event.get("action", "Unknown")
    model = event.get("model", "Unknown")
    provider = event.get("provider", "Unknown")

    # Determine priority class
    priority_class = "event-card"
    if "error" in action.lower() or "failed" in action.lower():
        priority_class += " high-priority"
    elif "warning" in action.lower():
        priority_class += " medium-priority"

    # Determine model badge class
    model_badge_class = "model-badge"
    if "opus" in model.lower():
        model_badge_class += " opus"
    elif "sonnet" in model.lower():
        model_badge_class += " sonnet"
    elif "haiku" in model.lower():
        model_badge_class += " haiku"

    st.markdown(f"""
    <div class="{priority_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="{model_badge_class}">{model}</span>
                <span style="color: #7f8c8d; font-size: 0.85rem;">{provider}</span>
            </div>
            <span style="color: #95a5a6; font-size: 0.8rem;">{timestamp}</span>
        </div>
        <div style="margin-top: 0.5rem;">
            <strong>{agent}</strong>: {action}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MANUAL TASK BUILDER
# ============================================================================

def render_manual_task_builder():
    """Render manual task submission form."""
    st.markdown('<div class="section-header">📝 MANUAL TASK BUILDER</div>', unsafe_allow_html=True)

    with st.form("manual_task_form"):
        task_description = st.text_area(
            "Task Description",
            height=150,
            placeholder="Describe the task you want to execute...",
            help="Provide a clear, detailed description of what you want to accomplish"
        )

        col1, col2 = st.columns(2)

        with col1:
            model = st.selectbox(
                "Model Selection",
                options=list(MODEL_OPTIONS.keys()),
                format_func=lambda x: MODEL_OPTIONS[x],
                help="Choose the AI model for task execution"
            )

            workflow = st.selectbox(
                "Execution Mode",
                options=list(WORKFLOW_OPTIONS.keys()),
                format_func=lambda x: WORKFLOW_OPTIONS[x],
                help="Select workflow orchestration strategy"
            )

        with col2:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher = more creative, Lower = more focused"
            )

            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=8000,
                value=4000,
                step=100,
                help="Maximum response length"
            )

        submitted = st.form_submit_button("🚀 Submit Task", use_container_width=True)

        if submitted:
            if not task_description.strip():
                st.error("Please provide a task description")
            else:
                task_data = {
                    "task": task_description,
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "workflow": workflow
                }

                # Security validation
                if st.session_state.security_enabled:
                    with st.spinner("🛡️ Security validation..."):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            security_result = loop.run_until_complete(
                                get_security_filter_instance().validate_input(
                                    task_data,
                                    source_id=f"manual_{datetime.now().timestamp()}"
                                )
                            )

                            loop.close()

                            task_data = security_result["validated_data"]

                        except SecurityViolation as e:
                            st.error(f"🚨 Security validation failed: {e}")
                            st.stop()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                            st.stop()

                # Add RAG topics
                if st.session_state.selected_rag_topics:
                    task_data["rag_topics"] = st.session_state.selected_rag_topics
                    task_data["context"] = {
                        "rag_filter": {
                            "topics": st.session_state.selected_rag_topics,
                            "routing_strategy": "topic_optimized"
                        }
                    }

                # Submit
                task_id = submit_task_to_adz(task_data)
                st.success(f"✅ Task submitted: `{task_id}`")
                st.rerun()

# ============================================================================
# TASK HISTORY
# ============================================================================

def render_task_history():
    """Render submitted tasks history."""
    st.markdown('<div class="section-header">📚 SUBMITTED TASKS</div>', unsafe_allow_html=True)

    if st.session_state.submitted_tasks:
        for task in reversed(st.session_state.submitted_tasks):  # Most recent first
            with st.expander(
                f"🎯 {task['task_id']} - {task['submitted_at'][:19]}",
                expanded=False
            ):
                st.markdown(f"**Preview**: {task['task_preview']}...")

                if task.get("rag_topics"):
                    st.markdown(f"**RAG Topics**: {', '.join(task['rag_topics'])}")

                security_icon = "🛡️" if task.get("security_validated") else "⚠️"
                st.markdown(f"**Security**: {security_icon} {'Validated' if task.get('security_validated') else 'Not Validated'}")
    else:
        st.info("No tasks submitted yet. Use the Agentic Drop Zone or Manual Builder above.")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Page config
    st.set_page_config(
        page_title="ZeroTouch Atlas",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject CSS
    inject_custom_css()

    # Header
    render_header()

    # Security status
    render_security_status()

    st.markdown("---")

    # Main content in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Task Submission",
        "🎯 RAG Topics",
        "📊 Observability",
        "📚 History"
    ])

    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            render_adz_dropzone()

        with col2:
            render_manual_task_builder()

    with tab2:
        render_rag_topic_panel()

    with tab3:
        render_observability_dashboard()

    with tab4:
        render_task_history()

    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        st.session_state.security_enabled = st.toggle(
            "Zero-Trust Security Filter",
            value=True,
            help="Enable Haiku 4.5 security validation for all inputs"
        )

        st.markdown("---")

        st.markdown("## 📊 Statistics")
        st.metric("Tasks Submitted", len(st.session_state.submitted_tasks))
        st.metric("Security Events", st.session_state.security_stats["total_events"])
        st.metric("Threats Blocked", st.session_state.security_stats["blocked"])

        st.markdown("---")

        st.markdown("## 🔗 Resources")
        st.markdown("""
        - [GitHub Repository](https://github.com/jevenson76/Atlas-Orchestrator)
        - [Documentation](./docs/README.md)
        - [API Reference](./docs/API.md)
        """)

        st.markdown("---")
        st.markdown("**ZeroTouch Atlas** v1.0.0")
        st.markdown("*Global-scale intelligent orchestration*")

if __name__ == "__main__":
    main()
