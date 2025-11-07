"""
Enterprise-Grade Multi-Perspective Dialogue UI

Professional, clean visualization of multi-model dialogue with:
- Real-time streaming updates
- Professional color-coded role badges
- Progress indicators and metrics
- Timeline visualization
- Quality tracking charts
- Zero amateur elements (no emojis)
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from multi_perspective import DialogueTurn, DialogueResult, DialogueRole, ConsensusStatus


class EnterpriseDialogueUI:
    """
    Enterprise-grade UI for multi-perspective dialogue visualization.

    Design Principles:
    - Clean, professional aesthetics
    - Color-coded semantic roles
    - Real-time streaming updates
    - Data-driven metrics
    - Minimal, purposeful animations
    """

    # Professional Color Scheme (Enterprise palette)
    COLORS = {
        "proposer": "#1976D2",      # Primary Blue - Analysis/Proposal
        "challenger": "#F57C00",    # Amber - Critical Review
        "orchestrator": "#388E3C",  # Green - Decision/Approval
        "mediator": "#7B1FA2",      # Purple - Synthesis
        "neutral": "#616161",       # Gray - Informational
        "success": "#4CAF50",       # Green - Positive outcome
        "warning": "#FF9800",       # Orange - Attention needed
        "error": "#D32F2F",         # Red - Issue/Failure
        "background": "#F5F5F5",    # Light gray background
        "surface": "#FFFFFF",       # White surface
        "text_primary": "#212121",  # Dark gray text
        "text_secondary": "#757575" # Medium gray text
    }

    # Role Configuration
    ROLE_CONFIG = {
        DialogueRole.PROPOSER: {
            "label": "PROPOSER",
            "color": COLORS["proposer"],
            "description": "Solution Generation",
            "icon_class": "analysis"
        },
        DialogueRole.CHALLENGER: {
            "label": "CHALLENGER",
            "color": COLORS["challenger"],
            "description": "Critical Review",
            "icon_class": "review"
        },
        DialogueRole.ORCHESTRATOR: {
            "label": "ORCHESTRATOR",
            "color": COLORS["orchestrator"],
            "description": "Decision Management",
            "icon_class": "decision"
        },
        DialogueRole.MEDIATOR: {
            "label": "MEDIATOR",
            "color": COLORS["mediator"],
            "description": "Synthesis",
            "icon_class": "synthesis"
        }
    }

    @staticmethod
    def render_dialogue_header(task: str, status: str = "IN_PROGRESS"):
        """Render professional dialogue header."""

        st.markdown("""
        <style>
        .dialogue-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .dialogue-title {
            color: white;
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            letter-spacing: 0.5px;
        }
        .dialogue-task {
            color: rgba(255,255,255,0.9);
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 0.5rem;
        }
        .dialogue-status {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 1px;
            background: rgba(255,255,255,0.2);
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="dialogue-header">
            <div class="dialogue-title">Multi-Perspective Analysis</div>
            <div class="dialogue-task">{task[:200]}{'...' if len(task) > 200 else ''}</div>
            <div class="dialogue-status">{status}</div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_role_badge(role: DialogueRole, model: str, turn_number: int):
        """Render professional role badge."""

        config = EnterpriseDialogueUI.ROLE_CONFIG.get(role)
        if not config:
            return

        st.markdown(f"""
        <style>
        .role-badge {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-left: 4px solid {config['color']};
            background: white;
            border-radius: 4px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .role-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {config['color']};
            animation: pulse 2s ease-in-out infinite;
        }}
        .role-label {{
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: {config['color']};
        }}
        .role-description {{
            font-size: 0.8rem;
            color: #757575;
            margin-left: auto;
        }}
        .role-meta {{
            font-size: 0.7rem;
            color: #9E9E9E;
            font-family: 'Courier New', monospace;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        </style>

        <div class="role-badge">
            <div class="role-indicator"></div>
            <div class="role-label">{config['label']}</div>
            <div class="role-description">{config['description']}</div>
            <div class="role-meta">Turn {turn_number} • {model}</div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_progress_indicator(current: int, total: int, quality: Optional[float] = None):
        """Render professional progress indicator."""

        progress_pct = (current / total) * 100 if total > 0 else 0

        quality_display = ""
        if quality is not None:
            quality_color = EnterpriseDialogueUI._get_quality_color(quality)
            quality_display = f"""
            <div style="margin-top: 8px; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.75rem; color: #757575;">Quality Score:</span>
                <span style="font-size: 0.85rem; font-weight: 600; color: {quality_color};">{quality:.1f}/100</span>
            </div>
            """

        st.markdown(f"""
        <style>
        .progress-container {{
            background: white;
            padding: 16px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 16px;
        }}
        .progress-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }}
        .progress-label {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #212121;
        }}
        .progress-value {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #1976D2;
        }}
        .progress-bar-bg {{
            width: 100%;
            height: 8px;
            background: #E0E0E0;
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #1976D2 0%, #64B5F6 100%);
            border-radius: 4px;
            transition: width 0.5s ease-in-out;
            width: {progress_pct}%;
        }}
        </style>

        <div class="progress-container">
            <div class="progress-header">
                <span class="progress-label">Dialogue Progress</span>
                <span class="progress-value">Iteration {current}/{total}</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill"></div>
            </div>
            {quality_display}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_turn_card(turn: DialogueTurn, show_full: bool = False):
        """Render professional turn card."""

        config = EnterpriseDialogueUI.ROLE_CONFIG.get(turn.role)
        if not config:
            config = {
                "color": EnterpriseDialogueUI.COLORS["neutral"],
                "label": turn.role.value.upper()
            }

        # Truncate response for preview
        response_preview = turn.response[:300] if not show_full else turn.response
        show_more = len(turn.response) > 300 and not show_full

        st.markdown(f"""
        <style>
        .turn-card {{
            background: white;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 4px solid {config['color']};
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            transition: box-shadow 0.2s ease;
        }}
        .turn-card:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        }}
        .turn-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .turn-role {{
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: {config['color']};
        }}
        .turn-meta {{
            font-size: 0.65rem;
            color: #9E9E9E;
            font-family: 'Courier New', monospace;
        }}
        .turn-content {{
            font-size: 0.9rem;
            line-height: 1.6;
            color: #424242;
            white-space: pre-wrap;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        .turn-stats {{
            display: flex;
            gap: 16px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #EEEEEE;
        }}
        .turn-stat {{
            font-size: 0.7rem;
            color: #757575;
        }}
        .turn-stat-value {{
            font-weight: 600;
            color: #212121;
        }}
        </style>

        <div class="turn-card">
            <div class="turn-header">
                <span class="turn-role">{config['label']}</span>
                <span class="turn-meta">Turn {turn.turn_number} • {turn.model}</span>
            </div>
            <div class="turn-content">{response_preview}{'...' if show_more else ''}</div>
            <div class="turn-stats">
                <div class="turn-stat">
                    Tokens: <span class="turn-stat-value">{turn.tokens:,}</span>
                </div>
                <div class="turn-stat">
                    Cost: <span class="turn-stat-value">${turn.cost:.6f}</span>
                </div>
                <div class="turn-stat">
                    Time: <span class="turn-stat-value">{turn.timestamp[11:19]}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_consensus_status(status: ConsensusStatus, iterations: int):
        """Render consensus status indicator."""

        status_config = {
            ConsensusStatus.FULL_CONSENSUS: {
                "label": "CONSENSUS REACHED",
                "color": EnterpriseDialogueUI.COLORS["success"],
                "description": "All parties aligned on optimal solution"
            },
            ConsensusStatus.PARTIAL_CONSENSUS: {
                "label": "IN PROGRESS",
                "color": EnterpriseDialogueUI.COLORS["warning"],
                "description": "Refinement ongoing"
            },
            ConsensusStatus.NO_CONSENSUS: {
                "label": "NO CONSENSUS",
                "color": EnterpriseDialogueUI.COLORS["error"],
                "description": "Divergent perspectives remain"
            },
            ConsensusStatus.ITERATIONS_EXCEEDED: {
                "label": "MAX ITERATIONS",
                "color": EnterpriseDialogueUI.COLORS["neutral"],
                "description": "Stopped at iteration limit"
            }
        }

        config = status_config.get(status, status_config[ConsensusStatus.NO_CONSENSUS])

        st.markdown(f"""
        <style>
        .consensus-card {{
            background: {config['color']};
            color: white;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .consensus-label {{
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            margin-bottom: 4px;
        }}
        .consensus-description {{
            font-size: 0.85rem;
            opacity: 0.95;
        }}
        .consensus-iterations {{
            font-size: 0.7rem;
            opacity: 0.8;
            margin-top: 8px;
        }}
        </style>

        <div class="consensus-card">
            <div class="consensus-label">{config['label']}</div>
            <div class="consensus-description">{config['description']}</div>
            <div class="consensus-iterations">Completed in {iterations} iteration(s)</div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_quality_chart(initial_quality: float, final_quality: float, improvement: float):
        """Render quality improvement visualization."""

        improvement_color = EnterpriseDialogueUI._get_quality_color(final_quality)

        # Create DataFrame for chart
        df = pd.DataFrame({
            "Stage": ["Initial", "Final"],
            "Quality": [initial_quality, final_quality]
        })

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            <div style="font-size: 0.85rem; font-weight: 600; color: #212121; margin-bottom: 8px;">
                Quality Progression
            </div>
            """, unsafe_allow_html=True)
            st.bar_chart(df.set_index("Stage"), use_container_width=True, height=200)

        with col2:
            st.markdown(f"""
            <style>
            .quality-metric {{
                background: white;
                padding: 16px;
                border-radius: 6px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            }}
            .quality-label {{
                font-size: 0.7rem;
                color: #757575;
                margin-bottom: 4px;
                letter-spacing: 1px;
            }}
            .quality-value {{
                font-size: 1.5rem;
                font-weight: 700;
                color: {improvement_color};
            }}
            .quality-change {{
                font-size: 0.8rem;
                color: {improvement_color};
                margin-top: 4px;
            }}
            </style>

            <div class="quality-metric">
                <div class="quality-label">IMPROVEMENT</div>
                <div class="quality-value">+{improvement:.1f}%</div>
                <div class="quality-change">{initial_quality:.1f} → {final_quality:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def render_dialogue_timeline(turns: List[DialogueTurn]):
        """Render timeline visualization of dialogue flow."""

        st.markdown("""
        <div style="font-size: 0.85rem; font-weight: 600; color: #212121; margin-bottom: 12px;">
            Dialogue Timeline
        </div>
        """, unsafe_allow_html=True)

        # Create timeline data
        timeline_html = '<div style="position: relative; padding-left: 24px;">'

        for i, turn in enumerate(turns):
            config = EnterpriseDialogueUI.ROLE_CONFIG.get(turn.role, {
                "color": EnterpriseDialogueUI.COLORS["neutral"],
                "label": turn.role.value.upper()
            })

            # Timeline dot and connector
            connector = "" if i == len(turns) - 1 else f"""
            <div style="position: absolute; left: 7px; top: 24px; width: 2px; height: 40px; background: #E0E0E0;"></div>
            """

            timeline_html += f"""
            <div style="position: relative; margin-bottom: 32px;">
                <div style="position: absolute; left: -20px; top: 4px; width: 12px; height: 12px; border-radius: 50%; background: {config['color']}; border: 2px solid white; box-shadow: 0 0 0 2px {config['color']};"></div>
                {connector}
                <div style="font-size: 0.7rem; font-weight: 600; color: {config['color']}; letter-spacing: 1px;">
                    {config['label']}
                </div>
                <div style="font-size: 0.75rem; color: #757575; margin-top: 2px;">
                    {turn.response[:80]}...
                </div>
                <div style="font-size: 0.65rem; color: #9E9E9E; margin-top: 4px;">
                    {turn.timestamp[11:19]} • {turn.tokens} tokens
                </div>
            </div>
            """

        timeline_html += '</div>'
        st.markdown(timeline_html, unsafe_allow_html=True)

    @staticmethod
    def _get_quality_color(quality: float) -> str:
        """Get color based on quality score."""
        if quality >= 90:
            return EnterpriseDialogueUI.COLORS["success"]
        elif quality >= 75:
            return "#66BB6A"  # Light green
        elif quality >= 60:
            return EnterpriseDialogueUI.COLORS["warning"]
        else:
            return EnterpriseDialogueUI.COLORS["error"]

    @staticmethod
    def render_full_dialogue_result(result: DialogueResult, task: str):
        """Render complete dialogue result with all visualizations."""

        # Header
        status = "COMPLETED" if result.success else "FAILED"
        EnterpriseDialogueUI.render_dialogue_header(task, status)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Final Quality",
                value=f"{result.final_quality:.1f}/100",
                delta=f"+{result.improvement_percentage:.1f}%"
            )

        with col2:
            st.metric(
                label="Iterations",
                value=result.iterations,
                delta=f"of max {3}"  # Default max
            )

        with col3:
            st.metric(
                label="Total Cost",
                value=f"${result.total_cost:.6f}",
                delta="FREE" if result.total_cost == 0 else None
            )

        with col4:
            st.metric(
                label="Duration",
                value=f"{result.duration_seconds:.1f}s",
                delta=f"{len(result.turns)} turns"
            )

        st.markdown("---")

        # Consensus status
        EnterpriseDialogueUI.render_consensus_status(
            result.consensus_status,
            result.iterations
        )

        # Quality chart
        if result.initial_quality and result.final_quality:
            EnterpriseDialogueUI.render_quality_chart(
                result.initial_quality,
                result.final_quality,
                result.improvement_percentage or 0.0
            )

        st.markdown("---")

        # Dialogue turns
        st.markdown("""
        <div style="font-size: 1rem; font-weight: 600; color: #212121; margin-bottom: 16px;">
            Dialogue Transcript
        </div>
        """, unsafe_allow_html=True)

        for turn in result.turns:
            EnterpriseDialogueUI.render_turn_card(turn, show_full=False)

        st.markdown("---")

        # Timeline
        EnterpriseDialogueUI.render_dialogue_timeline(result.turns)

        # Final output
        st.markdown("""
        <div style="font-size: 1rem; font-weight: 600; color: #212121; margin-bottom: 16px;">
            Final Output
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 6px; border-left: 4px solid #1976D2; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
            <div style="font-size: 0.95rem; line-height: 1.7; color: #424242; white-space: pre-wrap;">
{result.final_output}
            </div>
        </div>
        """, unsafe_allow_html=True)
