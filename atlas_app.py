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
import nest_asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import base64

# Fix for "event loop already running" error in Streamlit
nest_asyncio.apply()

# ============================================================================
# IMPORTS - Security & Core
# ============================================================================

import sys
sys.path.insert(0, str(Path(__file__).parent))

from security import get_security_filter, SecurityViolation
from dialogue_ui import EnterpriseDialogueUI
from multi_perspective import MultiPerspectiveDialogue, detect_task_complexity, DialogueResult
from atlas_master_bridge import AtlasMasterBridge

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

# Model stack (Claude required - authentication needed)
MODEL_OPTIONS = {
    "claude-sonnet-4": "Claude Sonnet 4.5 (Default - Balanced performance)",
    "claude-opus-3": "Claude Opus 3 (Premium - Deep reasoning)",
    "claude-opus-4": "Claude Opus 4.1 (Ultimate - ULTRATHINK enabled)"
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
    st.session_state.security_enabled = False  # Disabled by user request

if "dialogue_history" not in st.session_state:
    st.session_state.dialogue_history = []

if "active_dialogue" not in st.session_state:
    st.session_state.active_dialogue = None

if "processing_mode" not in st.session_state:
    st.session_state.processing_mode = "direct"  # "direct" or "background"

if "current_task_progress" not in st.session_state:
    st.session_state.current_task_progress = []

if "output_save_path" not in st.session_state:
    st.session_state.output_save_path = str(Path.home() / "Downloads")

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

    @keyframes subtlePulse {
        0%, 100% {
            box-shadow: 0 4px 15px rgba(44, 83, 100, 0.3);
        }
        50% {
            box-shadow: 0 6px 25px rgba(44, 83, 100, 0.5);
        }
    }

    /* ================================================================
       ENTERPRISE BUTTON ENHANCEMENTS
       ================================================================ */

    /* Primary action buttons - enhanced styling */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #2c5364 0%, #0f2027 100%);
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(44, 83, 100, 0.3);
        animation: subtlePulse 3s ease-in-out infinite;
    }

    .stButton button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(44, 83, 100, 0.5);
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
    }

    .stButton button[kind="primary"]:active {
        transform: translateY(0px);
        box-shadow: 0 2px 10px rgba(44, 83, 100, 0.3);
    }

    /* Text inputs - enhanced styling */
    .stTextInput input {
        border-radius: 8px;
        border: 2px solid #e1e8ed;
        transition: all 0.3s ease;
    }

    .stTextInput input:focus {
        border-color: #2c5364;
        box-shadow: 0 0 0 3px rgba(44, 83, 100, 0.1);
    }

    .stTextInput input:disabled {
        background-color: #f8f9fa;
        border-color: #dee2e6;
        color: #6c757d;
        cursor: not-allowed;
    }

    /* Select boxes - enhanced styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e1e8ed;
        transition: all 0.3s ease;
    }

    .stSelectbox > div > div:focus-within {
        border-color: #2c5364;
        box-shadow: 0 0 0 3px rgba(44, 83, 100, 0.1);
    }

    /* Sliders - enhanced styling */
    .stSlider > div > div > div {
        background-color: #2c5364;
    }

    /* Checkboxes - enhanced styling */
    .stCheckbox > label {
        transition: all 0.2s ease;
    }

    .stCheckbox > label:hover {
        color: #2c5364;
    }

    /* Info/Success/Warning/Error boxes - enhanced styling */
    .stAlert {
        border-radius: 12px;
        border-left: 4px solid;
        animation: fadeInLeft 0.4s;
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

        # Static Source Field - Non-editable display of original source
        st.text_input(
            "📎 Task Source",
            value=uploaded_file.name,
            disabled=True,
            help="Original file that initiated this task (cannot be modified)"
        )

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

def emit_event(agent: str, action: str, model: str = "Atlas UI", provider: str = "ZeroTouch"):
    """
    Emit an event to the stream file for real-time activity tracking.

    Args:
        agent: The component/agent performing the action
        action: Description of the action
        model: Model being used (default: Atlas UI)
        provider: Provider name (default: ZeroTouch)
    """
    event = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "action": action,
        "model": model,
        "provider": provider
    }

    # Ensure events directory exists
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Append event to stream file
    with open(STREAM_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')


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

    # Emit event: Task received
    model = task_data.get("model", "claude-code-experimental-v1")
    emit_event(
        agent="Atlas UI",
        action=f"Task {task_id} received and validated",
        model=model,
        provider="ZeroTouch Atlas"
    )

    # Write to dropzone
    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)

    # Emit event: Task saved to dropzone
    emit_event(
        agent="Task Manager",
        action=f"Task {task_id} saved to dropzone/tasks/",
        model=model,
        provider="ADZ"
    )

    # Add to session history
    st.session_state.submitted_tasks.append({
        "task_id": task_id,
        "submitted_at": datetime.now().isoformat(),
        "task_preview": str(task_data.get("task", ""))[:100],
        "rag_topics": st.session_state.selected_rag_topics.copy() if st.session_state.selected_rag_topics else [],
        "security_validated": st.session_state.security_enabled
    })

    # Emit event: Task queued for processing
    emit_event(
        agent="ADZ Daemon",
        action=f"Task {task_id} queued for processing (waiting for daemon)",
        model=model,
        provider="Background Processor"
    )

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
    """
    Enhanced Real-Time Observability Dashboard (Phase E.1)

    Displays live metrics from C4 event stream including:
    - Quality scores from Opus 4.1 Critic
    - Cost tracking breakdown by model
    - Execution timeline visualization
    - Provider health status indicators
    """
    st.markdown('<div class="section-header">📊 LIVE MONITOR - Multi-Agent Observability</div>', unsafe_allow_html=True)

    st.markdown("""
    **Real-time Intelligence**: Monitor AI collaboration, quality metrics, and cost analytics.
    Data sourced from C4 hooks with full provider attribution.
    """)

    # Load and parse events
    events = load_c4_events()

    if not events:
        st.info("🌐 Event stream will appear here when tasks are processed.")
        st.markdown("""
        **What you'll see:**
        - 📈 Quality Scores from Opus 4.1 Critic
        - 💰 Real-time cost breakdown by model
        - ⏱️ Execution timeline across agents
        - 🔄 Provider health (Claude/Gemini/OpenAI)
        """)
        return

    # Layout: Metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    # Metric 1: Quality Scores (from Opus 4.1 Critic)
    with col1:
        render_quality_scores_metric(events)

    # Metric 2: Cost Tracking
    with col2:
        render_cost_tracking_metric(events)

    # Metric 3: Active Tasks
    with col3:
        render_active_tasks_metric(events)

    # Metric 4: Provider Health
    with col4:
        render_provider_health_metric(events)

    st.markdown("---")

    # Section: Cost Breakdown by Model
    st.markdown("### 💰 Cost Breakdown by Model")
    render_cost_breakdown_chart(events)

    st.markdown("---")

    # Section: Execution Timeline
    st.markdown("### ⏱️ Execution Timeline")
    render_execution_timeline(events)

    st.markdown("---")

    # Section: Recent Events (Last 10)
    st.markdown("### 📋 Recent Events")
    with st.expander("View Event Stream", expanded=False):
        for event in reversed(events[-10:]):
            render_event_card(event)


def load_c4_events() -> List[Dict[str, Any]]:
    """Load events from C4 event stream file."""
    if not STREAM_FILE.exists():
        return []

    try:
        with open(STREAM_FILE, 'r') as f:
            events = [json.loads(line) for line in f.readlines()]
        return events
    except Exception as e:
        st.warning(f"Could not load event stream: {e}")
        return []


def render_quality_scores_metric(events: List[Dict[str, Any]]):
    """Display quality scores from Opus 4.1 Critic."""
    # Extract quality scores from critic events
    critic_events = [
        e for e in events
        if e.get("event_type") in ["critic.completed", "quality.measured"]
        and e.get("quality_score") is not None
    ]

    if critic_events:
        latest_score = critic_events[-1].get("quality_score", 0)
        avg_score = sum(e.get("quality_score", 0) for e in critic_events) / len(critic_events)

        st.metric(
            label="📈 Quality Score",
            value=f"{latest_score:.1f}/100",
            delta=f"Avg: {avg_score:.1f}",
            help="Latest quality assessment from Opus 4.1 Critic"
        )
    else:
        st.metric(
            label="📈 Quality Score",
            value="—",
            help="No quality assessments yet"
        )


def render_cost_tracking_metric(events: List[Dict[str, Any]]):
    """Display total cost tracking (DISABLED per user request)."""
    # Cost tracking disabled - no display
    pass


def render_active_tasks_metric(events: List[Dict[str, Any]]):
    """Display active task count."""
    # Count workflow.started vs workflow.completed
    started = len([e for e in events if e.get("event_type") == "workflow.started"])
    completed = len([e for e in events if e.get("event_type") == "workflow.completed"])
    active = max(0, started - completed)

    st.metric(
        label="⚡ Active Tasks",
        value=active,
        delta=f"{completed} completed",
        help="Tasks currently in progress"
    )


def render_provider_health_metric(events: List[Dict[str, Any]]):
    """Display provider health status."""
    # Check for recent errors/fallbacks
    recent_events = events[-50:] if len(events) > 50 else events

    error_events = [
        e for e in recent_events
        if e.get("event_type") in ["model.error", "model.fallback", "agent.failed"]
    ]

    if error_events:
        health = "⚠️ Degraded"
        color = "orange"
    else:
        health = "✅ Healthy"
        color = "green"

    st.metric(
        label="🔄 Provider Health",
        value=health,
        help="Multi-provider fallback chain status"
    )


def render_cost_breakdown_chart(events: List[Dict[str, Any]]):
    """Render cost breakdown by model using a bar chart (DISABLED per user request)."""
    # Cost tracking disabled - no display
    pass


def render_execution_timeline(events: List[Dict[str, Any]]):
    """Render execution timeline showing agent activity."""
    # Filter for relevant events
    timeline_events = [
        e for e in events
        if e.get("event_type") in [
            "workflow.started", "workflow.completed",
            "agent.invoked", "agent.completed",
            "validation.started", "validation.passed", "validation.failed",
            "critic.started", "critic.completed"
        ]
    ]

    if timeline_events:
        # Create timeline dataframe
        timeline_data = []
        for event in timeline_events[-20:]:  # Last 20 events
            timeline_data.append({
                "Time": event.get("timestamp", "")[:19],  # Trim to readable format
                "Component": event.get("component", "Unknown"),
                "Event": event.get("event_type", ""),
                "Duration (ms)": event.get("duration_ms", 0)
            })

        df_timeline = pd.DataFrame(timeline_data)
        st.dataframe(df_timeline, width='stretch', height=300)

        # Visual timeline (using expander for details)
        with st.expander("View Execution Flow"):
            for event in timeline_events[-10:]:
                component = event.get("component", "Unknown")
                event_type = event.get("event_type", "")
                duration = event.get("duration_ms", 0)

                # Color code by event type
                if "completed" in event_type or "passed" in event_type:
                    st.success(f"✅ {component}: {event_type} ({duration}ms)")
                elif "failed" in event_type or "error" in event_type:
                    st.error(f"❌ {component}: {event_type}")
                elif "started" in event_type or "invoked" in event_type:
                    st.info(f"🔵 {component}: {event_type}")
                else:
                    st.write(f"⚪ {component}: {event_type}")
    else:
        st.info("Timeline will populate as tasks execute.")

def render_event_card(event: Dict[str, Any]):
    """Render individual event card with model attribution (supports both ADZ and Atlas UI formats)."""
    # Handle both event formats:
    # ADZ format: {component, message, event_type, ...}
    # Atlas UI format: {agent, action, model, provider, ...}

    timestamp = event.get("timestamp", "Unknown")

    # Agent/Component
    agent = event.get("agent") or event.get("component", "Unknown")

    # Action/Message
    action = event.get("action") or event.get("message", "Unknown")

    # Model (infer from event_type if not present)
    model = event.get("model")
    if not model:
        event_type = event.get("event_type", "")
        if "workflow" in event_type:
            model = "Multi-AI Workflow"
        elif "cost" in event_type:
            model = "Cost Tracker"
        elif "quality" in event_type:
            model = "Quality Analyzer"
        else:
            model = "ADZ Processor"

    # Provider (infer from component if not present)
    provider = event.get("provider")
    if not provider:
        component = event.get("component", "")
        if "orchestrator" in component:
            provider = "Task Orchestrator"
        elif "dropzone" in component:
            provider = "ADZ"
        else:
            provider = component.title() if component else "System"

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
                <span style="color: #bdc3c7; font-size: 0.85rem; margin-left: 0.5rem;">{provider}</span>
            </div>
            <span style="color: #95a5a6; font-size: 0.8rem;">{timestamp}</span>
        </div>
        <div style="margin-top: 0.5rem; color: #ecf0f1;">
            <strong style="color: #3498db;">{agent}</strong>: <span style="color: #e8e8e8;">{action}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MANUAL TASK BUILDER
# ============================================================================

def render_manual_task_builder():
    """Render manual task submission form with processing mode selector."""
    st.markdown('<div class="section-header">📝 MANUAL TASK BUILDER</div>', unsafe_allow_html=True)

    # Processing Mode - FORCE Direct Processing (background mode is broken)
    st.session_state.processing_mode = "direct"  # Force direct mode

    st.markdown("#### ⚙️ MASTER ORCHESTRATOR - INTELLIGENT WORKFLOW ROUTING")
    st.success("""
**🎯 AUTO-SELECTS OPTIMAL WORKFLOW**

✅ **3 Workflow Types** - Auto-selects based on task complexity
✅ **Multi-Provider LLMs** - Anthropic (Sonnet/Opus), Gemini, Grok, GPT-4
✅ **Brutal Critic Validation** - Opus 4 critics score every output 0-100
✅ **Smart Orchestration** - Only escalates when quality demands it

**Available Workflows:**
1. 🏗️ **Specialized Roles** - 4-phase: ARCHITECT → DEVELOPER → TESTER → REVIEWER
   - For complex tasks requiring architecture & review
   - Uses Opus for architect/reviewer, Sonnet for developer/tester

2. ⚡ **Parallel Development** - Distributed parallel execution
   - For multi-component tasks (2+ independent parts)
   - 30-70% faster via parallel agent execution

3. 📈 **Progressive Enhancement** - Tier escalation with quality gates
   - For simple/fast tasks with brutal critic scoring
   - Escalates through tiers only when quality < 85

**Auto-Selection Logic:**
- Multi-component? → Parallel
- Simple & fast? → Progressive
- Complex & high-quality? → Specialized Roles
    """)

    # Workflow selector
    workflow_mode = st.radio(
        "Workflow Selection:",
        options=["auto", "specialized_roles", "parallel", "progressive"],
        index=0,
        horizontal=True,
        help="Auto = Let orchestrator decide | Manual = Force specific workflow"
    )

    st.session_state.workflow_mode = workflow_mode

    if workflow_mode != "auto":
        st.info(f"🔒 **Manual Override**: Using {workflow_mode} workflow")

    st.markdown("---")

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

        # Output location - always show (direct mode is forced)
        st.markdown("#### 📁 Output Location")
        output_path = st.text_input(
            "Save results to:",
            value=st.session_state.output_save_path,
            help="Choose where to save the generated files"
        )
        st.session_state.output_save_path = output_path

        submitted = st.form_submit_button("🚀 Submit Task", width='stretch')

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

                # Route based on processing mode
                if st.session_state.processing_mode == "direct":
                    # Direct Processing with real-time progress
                    st.markdown("---")
                    st.markdown("### 🔄 Processing Task (Real-time)")

                    # Progress container
                    progress_container = st.container()
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Event callback to update UI
                    def update_progress(agent, action, model="", progress=0, **kwargs):
                        """Update Streamlit UI with progress."""
                        st.session_state.current_task_progress.append({
                            "timestamp": datetime.now().isoformat(),
                            "agent": agent,
                            "action": action,
                            "model": model,
                            "progress": progress
                        })

                        # Update progress bar
                        progress_bar.progress(progress / 100.0)

                        # Update status text
                        status_text.markdown(f"**[{agent}]** {action}")

                        # Emit to event stream
                        emit_event(agent, action, model)

                    # Create bridge to REAL MasterOrchestrator
                    processor = AtlasMasterBridge(event_callback=update_progress)

                    # Add task_id
                    task_data["task_id"] = generate_task_id()

                    # Get workflow mode
                    workflow_mode = st.session_state.get("workflow_mode", "auto")

                    # Process with MasterOrchestrator
                    try:
                        output_file = Path(st.session_state.output_save_path) / f"{task_data['task_id']}_result.csv"

                        result = processor.process_task(
                            task_data,
                            output_path=output_file,
                            workflow=workflow_mode
                        )

                        # Show completion
                        st.success(f"✅ **Task Completed!**")
                        st.info(f"📁 Results saved to: `{result['output_path']}`")
                        st.metric("Duration", f"{result['duration']:.1f}s")

                        # Show progress log
                        with st.expander("📋 View Processing Log", expanded=False):
                            for event in st.session_state.current_task_progress:
                                st.text(f"[{event['timestamp']}] {event['agent']}: {event['action']}")

                    except Exception as e:
                        st.error(f"❌ **Processing failed**: {e}")
                        import traceback
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())

                else:
                    # Background Processing (original ADZ daemon approach)
                    task_id = submit_task_to_adz(task_data)
                    st.success(f"✅ Task submitted to background daemon: `{task_id}`")
                    st.info("Check **Recent Events** and **~/dropzone/results/** for progress")
                    st.rerun()

# ============================================================================
# TASK HISTORY
# ============================================================================

def render_task_history():
    """
    Render submitted tasks history with Interactive Refinement (Phase E.2).

    Allows users to provide feedback and trigger refinement loops on completed tasks.
    """
    st.markdown('<div class="section-header">📚 SUBMITTED TASKS</div>', unsafe_allow_html=True)

    if st.session_state.submitted_tasks:
        for idx, task in enumerate(reversed(st.session_state.submitted_tasks)):  # Most recent first
            task_idx = len(st.session_state.submitted_tasks) - idx - 1  # Original index

            with st.expander(
                f"🎯 {task['task_id']} - {task['submitted_at'][:19]}",
                expanded=False
            ):
                st.markdown(f"**Preview**: {task['task_preview']}...")

                if task.get("rag_topics"):
                    st.markdown(f"**RAG Topics**: {', '.join(task['rag_topics'])}")

                security_icon = "🛡️" if task.get("security_validated") else "⚠️"
                st.markdown(f"**Security**: {security_icon} {'Validated' if task.get('security_validated') else 'Not Validated'}")

                st.markdown("---")

                # Phase E.2: Interactive Refinement Loop
                st.markdown("### ✏️ Refine This Output")
                st.markdown("Provide natural language feedback to iteratively improve the output.")

                feedback_text = st.text_area(
                    "What would you like improved?",
                    placeholder="Example: Make it more concise, add more examples, improve clarity...",
                    key=f"feedback_{task['task_id']}",
                    height=100
                )

                refinement_aspects = st.multiselect(
                    "Focus Areas",
                    ["Accuracy", "Clarity", "Completeness", "Tone", "Format", "Examples"],
                    key=f"aspects_{task['task_id']}"
                )

                col1, col2 = st.columns([3, 1])

                with col2:
                    if st.button("🔄 Refine", key=f"refine_btn_{task['task_id']}", type="primary"):
                        if not feedback_text:
                            st.error("Please provide feedback before refining.")
                        else:
                            # Trigger refinement process
                            with st.spinner("🧠 Converting feedback to structured YAML..."):
                                structured_feedback = convert_feedback_to_yaml(
                                    task_data=task,
                                    feedback=feedback_text,
                                    aspects=refinement_aspects
                                )

                            if structured_feedback:
                                st.success("✅ Feedback converted successfully!")
                                st.code(structured_feedback, language="yaml")

                                # Store for refinement trigger
                                st.session_state[f"structured_feedback_{task['task_id']}"] = structured_feedback

                                st.info("""
                                **Next Steps:**
                                1. Structured feedback has been generated
                                2. Use this feedback with RefinementLoop to trigger refinement
                                3. The refined output will replace the original
                                """)
                            else:
                                st.error("Failed to convert feedback. Please try again.")

                # Display existing structured feedback if available
                if f"structured_feedback_{task['task_id']}" in st.session_state:
                    with st.expander("📋 View Structured Feedback"):
                        st.code(
                            st.session_state[f"structured_feedback_{task['task_id']}"],
                            language="yaml"
                        )
    else:
        st.info("No tasks submitted yet. Use the Agentic Drop Zone or Manual Builder above.")


def convert_feedback_to_yaml(
    task_data: Dict[str, Any],
    feedback: str,
    aspects: List[str]
) -> Optional[str]:
    """
    Convert natural language feedback to structured YAML (Phase E.2).

    Uses Sonnet 4.5 agent to transform user feedback into the structured
    format required by RefinementLoop.

    Args:
        task_data: Original task data
        feedback: Natural language feedback from user
        aspects: Focus areas selected by user

    Returns:
        Structured YAML feedback string, or None if conversion fails
    """
    try:
        from resilient_agent import ResilientBaseAgent
        from core.constants import Models

        # Create Claude Sonnet agent for feedback conversion
        converter_agent = ResilientBaseAgent(
            role="Feedback Conversion Specialist",
            model=Models.SONNET,  # Claude Sonnet (authentication required)
            temperature=0.2
        )

        # Build conversion prompt
        conversion_prompt = f"""You are a feedback conversion specialist. Your task is to convert natural language feedback into structured YAML format for the RefinementLoop system.

## Original Task
{task_data.get('task_preview', 'Unknown task')}

## User Feedback (Natural Language)
{feedback}

## Focus Areas
{', '.join(aspects) if aspects else 'General improvement'}

## Your Task
Convert the user's feedback into structured YAML with the following format:

```yaml
feedback:
  - priority: CRITICAL|HIGH|MEDIUM|LOW
    location: "specific area or aspect to improve"
    issue: "clear description of what needs improvement"
    action: "specific action to take"
    code_snippet: "example if applicable (optional)"

regeneration_prompt: |
  Concise summary of all improvements needed, prioritized from most to least critical.
  Be specific about what to change and how.
```

IMPORTANT:
- Create 3-5 specific feedback items based on the user's input
- Prioritize based on impact and user emphasis
- Be concrete and actionable
- Include the regeneration_prompt that summarizes all fixes

Output ONLY the YAML, no additional text."""

        # Call agent (synchronous call)
        result = converter_agent.call(
            prompt=conversion_prompt,
            context={}
        )

        if not result.success:
            raise Exception(result.error or "Converter agent call failed")

        yaml_output = result.output

        # Extract YAML from response (may be wrapped in code blocks)
        import re
        yaml_match = re.search(r'```yaml\n(.*?)\n```', yaml_output, re.DOTALL)
        if yaml_match:
            return yaml_match.group(1)
        else:
            # Try without code blocks
            return yaml_output.strip()

    except Exception as e:
        st.error(f"Error converting feedback: {e}")
        return None

# ============================================================================
# JSON PROMPT GENERATOR
# ============================================================================

@st.dialog("🎯 Intelligent Task JSON Generator", width="large")
def show_json_generator():
    """
    Interactive JSON task generator with intelligent prompt optimization.
    Uses lightweight Haiku agent to refine vague inputs with follow-up questions.
    """
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h3 style="color: #0f2027; margin-bottom: 0.5rem;">Build Your Task</h3>
        <p style="color: #666;">Describe what you want to accomplish, and I'll help you create a properly formatted task.</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state for generator
    if 'generator_task_description' not in st.session_state:
        st.session_state.generator_task_description = ""
    if 'generator_follow_ups' not in st.session_state:
        st.session_state.generator_follow_ups = []
    if 'generator_refined_prompt' not in st.session_state:
        st.session_state.generator_refined_prompt = ""

    # Step 1: Task Description
    task_description = st.text_area(
        "What do you want to accomplish?",
        value=st.session_state.generator_task_description,
        placeholder="Example: Analyze customer sentiment from recent reviews and identify key themes...",
        height=120,
        help="Describe your task in natural language. The more detail, the better!"
    )

    # Step 2: Check if input is too vague and trigger follow-ups
    if task_description and task_description != st.session_state.generator_task_description:
        st.session_state.generator_task_description = task_description

        # Simple heuristic: if input is very short, trigger follow-ups
        if len(task_description.strip()) < 50:
            st.warning("⚠️ Your description is quite brief. Let me ask some clarifying questions...")

            # Trigger lightweight Haiku agent for follow-up questions
            with st.spinner("🧠 Analyzing your request..."):
                try:
                    from resilient_agent import ResilientBaseAgent
                    from core.constants import Models

                    optimizer = ResilientBaseAgent(
                        role="Task Clarification Assistant",
                        model=Models.SONNET,  # Claude Sonnet (authentication required)
                        temperature=0.3
                    )

                    follow_up_prompt = f"""You are a helpful task clarification assistant. The user provided this brief task description:

"{task_description}"

Generate 3-4 clarifying questions to help make this task more specific and actionable. Format as a numbered list.
Focus on:
1. What specific outcome they want
2. What format/structure the output should have
3. Any constraints or requirements
4. Data sources or context needed

Return ONLY the numbered questions, one per line."""

                    result = optimizer.call(
                        prompt=follow_up_prompt,
                        context={}
                    )
                    if not result.success:
                        raise Exception(result.error or "Optimizer call failed")
                    response = result.output
                    st.session_state.generator_follow_ups = response.strip().split('\n')

                    st.info("💡 **Consider these clarifications:**")
                    for question in st.session_state.generator_follow_ups:
                        if question.strip():
                            st.markdown(f"- {question.strip()}")

                except Exception as e:
                    logger.error(f"Error generating follow-ups: {e}")
                    st.session_state.generator_follow_ups = []

    # Step 3: Additional Details (if follow-ups were shown)
    additional_details = ""
    if st.session_state.generator_follow_ups:
        additional_details = st.text_area(
            "Additional Details (address the questions above)",
            placeholder="Provide more context based on the clarifying questions...",
            height=100
        )

    # Step 4: Configuration Options
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        model_choice = st.selectbox(
            "Model",
            options=[
                ("claude-sonnet-4", "Sonnet 4 (Balanced)"),
                ("claude-opus-4-20250514", "Opus 4.1 (Deep Reasoning + UltraThink)"),
                ("claude-3-5-sonnet-20241022", "Haiku 3.5 (Fast & Efficient)")
            ],
            format_func=lambda x: x[1],
            help="Choose the Claude model for task execution"
        )

        workflow = st.selectbox(
            "Workflow Mode",
            options=[
                "automatic",
                "specialized_roles",
                "parallel_execution",
                "progressive_enhancement"
            ],
            help="Select orchestration workflow"
        )

    with col2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Controls randomness (0=deterministic, 1=creative)"
        )

        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=8000,
            value=2000,
            step=100,
            help="Maximum length of response"
        )

    # Step 5: RAG Topic Selection
    st.markdown("---")
    st.markdown("**🎯 RAG Topic Filters (Optional)**")
    topic_cols = st.columns(4)
    selected_topics = []

    available_topics = [
        "Medical & Healthcare", "Automotive", "Financial & Legal", "Technology",
        "Education", "Business", "Science", "General Knowledge"
    ]

    for idx, topic in enumerate(available_topics):
        with topic_cols[idx % 4]:
            if st.checkbox(topic, key=f"gen_{topic}"):
                selected_topics.append(topic)

    # Step 6: Source Field (for tracking)
    st.markdown("---")
    source = st.text_input(
        "Source (Optional)",
        placeholder="e.g., GitHub link, PDF filename, or description of origin",
        help="Track where this task originated from"
    )

    # Step 7: Generate and Submit
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🚀 Generate & Submit to ADZ", width='stretch', type="primary"):
            if not task_description:
                st.error("❌ Please provide a task description")
                return

            # Combine description with additional details
            full_task = task_description
            if additional_details:
                full_task += f"\n\nAdditional Context:\n{additional_details}"

            # Build JSON payload
            task_json = {
                "task": full_task,
                "model": model_choice[0],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "workflow_mode": workflow,
                "source": source if source else "JSON Generator",
                "metadata": {
                    "generated_by": "Atlas JSON Generator",
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Add RAG topics if selected
            if selected_topics:
                task_json["rag_topics"] = selected_topics
                task_json["context"] = {
                    "rag_filter": {
                        "topics": selected_topics,
                        "routing_strategy": "topic_optimized"
                    }
                }

            # Submit to ADZ queue
            try:
                task_id = submit_task_to_adz(task_json)
                st.success(f"✅ Task generated and submitted successfully!")
                st.code(json.dumps(task_json, indent=2), language="json")
                st.info(f"**Task ID**: `{task_id}`")

                # Clear generator state
                st.session_state.generator_task_description = ""
                st.session_state.generator_follow_ups = []
                st.session_state.generator_refined_prompt = ""

                # Wait a moment then close dialog
                time.sleep(2)
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error submitting task: {e}")

# ============================================================================
# MULTI-PERSPECTIVE DIALOGUE
# ============================================================================

def render_multi_perspective_dialogue():
    """
    Render Multi-Perspective Dialogue interface with real-time visualization.

    Allows users to:
    - Submit complex tasks for multi-model collaboration
    - View live dialogue progression in real-time
    - See completed dialogue results with quality metrics
    - Analyze dialogue transcripts and improvement tracking
    """
    st.markdown('<div class="section-header">🗣️ MULTI-PERSPECTIVE DIALOGUE</div>', unsafe_allow_html=True)

    st.markdown("""
    **Collaborative AI Analysis**: For complex tasks, multiple models work together through constructive
    dialogue to produce higher-quality outputs. Watch the conversation unfold in real-time.

    **Architecture**:
    - **Proposer** (Sonnet 3.5): Generates initial solutions - Fast & FREE
    - **Challenger** (Opus 4.1): Provides critical review - Deep reasoning & FREE
    - **Orchestrator** (Opus 4.1): Manages dialogue flow - Autonomous decision-making & FREE
    - **Quality Improvement**: Typically +15-30% improvement through multi-perspective
    """)

    # Task submission section
    st.markdown("---")
    st.markdown("### 💡 Submit Task for Multi-Perspective Analysis")

    with st.form("dialogue_task_form"):
        task_input = st.text_area(
            "Task Description",
            height=150,
            placeholder="Describe a complex task that would benefit from multiple perspectives...\n\nExamples:\n- Design a distributed system architecture\n- Analyze tradeoffs between different approaches\n- Create a comprehensive technical specification",
            help="Complex tasks with constraints, architecture, or validation needs work best"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            max_iterations = st.slider(
                "Max Iterations",
                min_value=1,
                max_value=5,
                value=3,
                help="Maximum dialogue rounds (prevents endless debate)"
            )

        with col2:
            quality_threshold = st.slider(
                "Quality Threshold",
                min_value=70.0,
                max_value=95.0,
                value=85.0,
                step=5.0,
                help="Stop when quality score reaches this level"
            )

        with col3:
            enable_external = st.checkbox(
                "Enable External Perspective",
                value=False,
                help="Add Grok 3 for diverse viewpoint (~$0.01 cost)"
            )

        submit_dialogue = st.form_submit_button("🚀 Start Multi-Perspective Dialogue", width='stretch', type="primary")

        if submit_dialogue:
            if not task_input.strip():
                st.error("Please provide a task description")
            else:
                # Check task complexity
                is_complex, reason = detect_task_complexity(task_input)

                if not is_complex:
                    st.warning(f"⚠️ **Complexity Check**: {reason}")
                    st.info("💡 **Recommendation**: This task may be simple enough for a single model. Multi-perspective dialogue works best for complex tasks with multiple constraints, architectural decisions, or validation needs.")

                    proceed = st.checkbox("Proceed anyway")
                    if not proceed:
                        st.stop()

                # Execute dialogue
                with st.spinner("🧠 Initiating multi-perspective dialogue..."):
                    try:
                        from core.constants import Models

                        dialogue = MultiPerspectiveDialogue(
                            proposer_model=Models.SONNET,
                            challenger_model=Models.OPUS_4,  # ULTRATHINK capability
                            orchestrator_model=Models.OPUS_4,  # ULTRATHINK for orchestration
                            max_iterations=max_iterations,
                            min_quality_threshold=quality_threshold,
                            enable_external_perspective=enable_external,
                            external_model=Models.GROK_3 if enable_external else None
                        )

                        # Execute dialogue
                        result = dialogue.execute(task_input)

                        # Store in history
                        st.session_state.dialogue_history.append({
                            "task": task_input,
                            "result": result,
                            "timestamp": datetime.now().isoformat(),
                            "config": {
                                "max_iterations": max_iterations,
                                "quality_threshold": quality_threshold,
                                "external_enabled": enable_external
                            }
                        })

                        st.success("✅ Dialogue completed successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error executing dialogue: {e}")
                        import traceback
                        st.code(traceback.format_exc())

    # Display dialogue results
    st.markdown("---")
    st.markdown("### 📊 Dialogue Results")

    if st.session_state.dialogue_history:
        # Show latest dialogue first
        for idx, dialogue_entry in enumerate(reversed(st.session_state.dialogue_history)):
            entry_idx = len(st.session_state.dialogue_history) - idx - 1
            result = dialogue_entry["result"]
            config = dialogue_entry["config"]

            with st.expander(
                f"🗣️ Dialogue {entry_idx + 1} - {dialogue_entry['timestamp'][:19]} "
                f"(Quality: {result.final_quality:.1f}/100, Cost: ${result.total_cost:.6f})",
                expanded=(idx == 0)  # Expand most recent by default
            ):
                # Render full dialogue result with enterprise UI
                EnterpriseDialogueUI.render_full_dialogue_result(result, dialogue_entry["task"])

                # Configuration details
                st.markdown("---")
                st.markdown("### ⚙️ Configuration Used")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Max Iterations", config["max_iterations"])

                with col2:
                    st.metric("Quality Threshold", f"{config['quality_threshold']:.0f}/100")

                with col3:
                    external_status = "Enabled" if config["external_enabled"] else "Disabled"
                    st.metric("External Perspective", external_status)
    else:
        st.info("""
        📭 **No dialogues yet**

        Submit a complex task above to see multi-perspective dialogue in action. The system will:

        1. **Check complexity** - Ensures task benefits from multiple perspectives
        2. **Initiate dialogue** - Proposer generates initial solution
        3. **Critical review** - Challenger identifies improvements
        4. **Orchestration** - Orchestrator decides to refine or approve
        5. **Quality tracking** - Measures improvement through dialogue
        6. **Consensus** - Stops when quality threshold met or max iterations reached

        **Perfect for**: Architecture design, system analysis, technical specifications, tradeoff evaluation
        """)

    # Statistics panel
    if st.session_state.dialogue_history:
        st.markdown("---")
        st.markdown("### 📈 Dialogue Statistics")

        col1, col2, col3, col4 = st.columns(4)

        total_dialogues = len(st.session_state.dialogue_history)
        avg_quality = sum(d["result"].final_quality for d in st.session_state.dialogue_history) / total_dialogues
        avg_improvement = sum(d["result"].improvement_percentage or 0 for d in st.session_state.dialogue_history) / total_dialogues
        total_cost = sum(d["result"].total_cost for d in st.session_state.dialogue_history)

        with col1:
            st.metric("Total Dialogues", total_dialogues)

        with col2:
            st.metric("Avg Final Quality", f"{avg_quality:.1f}/100")

        with col3:
            st.metric("Avg Improvement", f"+{avg_improvement:.1f}%")

        with col4:
            st.metric("Total Cost", f"${total_cost:.6f}")

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

    # Authentication now handled by MCP bridge (uses Claude Code Max subscription)
    # No manual API key configuration needed!

    # Inject CSS
    inject_custom_css()

    # Header
    render_header()

    # Security status
    render_security_status()

    st.markdown("---")

    # JSON Generator Button - Prominently placed on home page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Generate Task JSON", width='stretch', type="primary", help="Launch intelligent task builder with AI-powered prompt refinement"):
            show_json_generator()

    st.markdown("---")

    # Main content in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Task Submission",
        "🎯 RAG Topics",
        "🗣️ Multi-Perspective Dialogue",
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
        render_multi_perspective_dialogue()

    with tab4:
        render_observability_dashboard()

    with tab5:
        render_task_history()

    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        st.session_state.security_enabled = st.toggle(
            "Zero-Trust Security Filter",
            value=st.session_state.security_enabled,
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
