"""
Enhanced Session Management with GitHub Autosave

PRIORITY 2: Session Management ("Autosave" Mechanism)
- Update ALL context files (CLAUDE.md, gemini.md, Agents.md)
- Commit to GitHub with semantic summaries
- Create NEXT_STEPS.md for continuity
- Track conversation history across multiple LLMs
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single conversation turn across any LLM."""

    timestamp: str
    llm_provider: str  # anthropic, gemini, openai
    model: str
    role: str  # user, assistant, system
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'llm_provider': self.llm_provider,
            'model': self.model,
            'role': self.role,
            'content': self.content,
            'metadata': self.metadata
        }


class EnhancedSessionManager:
    """
    Session manager with automatic context file updates and GitHub commits.

    The "Autosave" mechanism that ensures continuity across sessions and LLMs.

    Features:
    - Track conversation history across multiple LLMs
    - Auto-update context files (CLAUDE.md, gemini.md, Agents.md)
    - Commit to GitHub with semantic summaries
    - Generate NEXT_STEPS.md for continuity
    - Session persistence and recovery
    """

    def __init__(self,
                 session_id: Optional[str] = None,
                 project_root: Optional[str] = None,
                 auto_commit: bool = True,
                 commit_frequency: int = 5):
        """
        Initialize enhanced session manager.

        Args:
            session_id: Unique session identifier
            project_root: Project root directory (auto-detect if None)
            auto_commit: Automatically commit changes to Git
            commit_frequency: Commit every N significant updates
        """
        self.session_id = session_id or f"session_{int(datetime.now().timestamp())}"
        self.project_root = Path(project_root) if project_root else self._detect_project_root()
        self.auto_commit = auto_commit
        self.commit_frequency = commit_frequency

        # Conversation history
        self.history: List[ConversationTurn] = []
        self.context: Dict[str, Any] = {}

        # Session metadata
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.last_commit_at: Optional[datetime] = None
        self.updates_since_commit = 0

        # Context file paths
        self.context_files = {
            'claude': self.project_root / 'CLAUDE.md',
            'gemini': self.project_root / 'gemini.md',
            'agents': self.project_root / 'Agents.md',
            'next_steps': self.project_root / 'NEXT_STEPS.md',
            'progress': self.project_root / 'PROGRESS.md',
            'decisions': self.project_root / 'DECISIONS.md'
        }

        logger.info(f"EnhancedSessionManager created: {self.session_id} at {self.project_root}")

    def _detect_project_root(self) -> Path:
        """Auto-detect project root by looking for .git directory."""
        current = Path.cwd()

        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent

        # No git repo found, use current directory
        return Path.cwd()

    def add_turn(self,
                 role: str,
                 content: str,
                 llm_provider: str = 'anthropic',
                 model: str = 'claude-3-5-sonnet-20241022',
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add conversation turn and trigger autosave.

        Args:
            role: Speaker role (user, assistant, system)
            content: Turn content
            llm_provider: LLM provider used
            model: Specific model used
            metadata: Optional additional metadata
        """
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            llm_provider=llm_provider,
            model=model,
            role=role,
            content=content,
            metadata=metadata or {}
        )

        self.history.append(turn)
        self.last_activity = datetime.now()
        self.updates_since_commit += 1

        logger.debug(f"Turn added: {role} ({llm_provider}/{model})")

        # Check if autosave should trigger
        if self.updates_since_commit >= self.commit_frequency:
            self.autosave()

    def autosave(self):
        """
        Autosave: Update context files and commit to GitHub.

        This is the critical continuity mechanism.
        """
        logger.info(f"Autosave triggered for session {self.session_id}")

        try:
            # 1. Update all context files
            self._update_context_files()

            # 2. Generate NEXT_STEPS.md
            self._generate_next_steps()

            # 3. Commit to GitHub if enabled
            if self.auto_commit and self._is_git_repo():
                self._commit_to_github()

            self.last_commit_at = datetime.now()
            self.updates_since_commit = 0

            logger.info("Autosave completed successfully")

        except Exception as e:
            logger.error(f"Autosave failed: {e}")

    def _update_context_files(self):
        """Update all context markdown files with session data."""

        # Update CLAUDE.md
        self._update_claude_md()

        # Update gemini.md
        self._update_gemini_md()

        # Update Agents.md
        self._update_agents_md()

        # Update PROGRESS.md
        self._update_progress_md()

    def _update_claude_md(self):
        """Update CLAUDE.md with current session context."""
        claude_file = self.context_files['claude']

        if not claude_file.exists():
            logger.warning(f"CLAUDE.md not found at {claude_file}")
            return

        # Read existing content
        content = claude_file.read_text()

        # Add session summary section
        session_summary = self._generate_session_summary()

        # Check if session summary section exists
        marker = "<!-- SESSION_SUMMARY -->"
        if marker in content:
            # Replace existing section
            parts = content.split(marker)
            content = f"{parts[0]}{marker}\n{session_summary}\n{marker}{parts[2] if len(parts) > 2 else ''}"
        else:
            # Append to end
            content += f"\n\n{marker}\n{session_summary}\n{marker}\n"

        # Write back
        claude_file.write_text(content)
        logger.info("CLAUDE.md updated")

    def _update_gemini_md(self):
        """Update gemini.md with current session context."""
        gemini_file = self.context_files['gemini']

        # Create if doesn't exist
        if not gemini_file.exists():
            gemini_file.write_text("# Gemini Context\n\n")

        content = gemini_file.read_text()

        # Add session summary
        session_summary = self._generate_session_summary()

        marker = "<!-- SESSION_SUMMARY -->"
        if marker in content:
            parts = content.split(marker)
            content = f"{parts[0]}{marker}\n{session_summary}\n{marker}{parts[2] if len(parts) > 2 else ''}"
        else:
            content += f"\n\n{marker}\n{session_summary}\n{marker}\n"

        gemini_file.write_text(content)
        logger.info("gemini.md updated")

    def _update_agents_md(self):
        """Update Agents.md with agent collaboration notes."""
        agents_file = self.context_files['agents']

        if not agents_file.exists():
            agents_file.write_text("# Agent Collaboration\n\n")

        content = agents_file.read_text()

        # Extract agent interactions from history
        agent_summary = self._generate_agent_summary()

        marker = "<!-- AGENT_ACTIVITY -->"
        if marker in content:
            parts = content.split(marker)
            content = f"{parts[0]}{marker}\n{agent_summary}\n{marker}{parts[2] if len(parts) > 2 else ''}"
        else:
            content += f"\n\n{marker}\n{agent_summary}\n{marker}\n"

        agents_file.write_text(content)
        logger.info("Agents.md updated")

    def _update_progress_md(self):
        """Update PROGRESS.md with completed work."""
        progress_file = self.context_files['progress']

        if not progress_file.exists():
            progress_file.write_text("# Progress Log\n\n")

        content = progress_file.read_text()

        # Add progress entry
        progress_entry = self._generate_progress_entry()

        content += f"\n{progress_entry}\n"

        progress_file.write_text(content)
        logger.info("PROGRESS.md updated")

    def _generate_next_steps(self):
        """Generate NEXT_STEPS.md for continuity."""
        next_steps_file = self.context_files['next_steps']

        # Analyze conversation to determine next steps
        next_steps = self._analyze_next_steps()

        content = f"""# Next Steps
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Session: {self.session_id}*

## Immediate Actions

{next_steps['immediate']}

## Pending Tasks

{next_steps['pending']}

## Context for Next Session

{next_steps['context']}

## Recent Activity Summary

{self._generate_recent_activity_summary()}
"""

        next_steps_file.write_text(content)
        logger.info("NEXT_STEPS.md generated")

    def _generate_session_summary(self) -> str:
        """Generate summary of current session."""
        turn_count = len(self.history)

        # Count by provider
        provider_counts = {}
        for turn in self.history:
            provider = turn.llm_provider
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        summary = f"""## Session Summary
- **Session ID**: {self.session_id}
- **Created**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Last Activity**: {self.last_activity.strftime('%Y-%m-%d %H:%M:%S')}
- **Total Turns**: {turn_count}
- **Providers Used**: {', '.join(f'{k} ({v})' for k, v in provider_counts.items())}

"""
        return summary

    def _generate_agent_summary(self) -> str:
        """Generate summary of agent activities."""
        # Extract agent-related turns
        agent_turns = [t for t in self.history if t.metadata.get('agent_id')]

        if not agent_turns:
            return "*No agent activity in this session*"

        summary = f"### Recent Agent Activity ({len(agent_turns)} interactions)\n\n"

        for turn in agent_turns[-5:]:  # Last 5
            agent_id = turn.metadata.get('agent_id', 'Unknown')
            timestamp = datetime.fromisoformat(turn.timestamp).strftime('%H:%M:%S')
            summary += f"- **{timestamp}** - {agent_id}: {turn.content[:80]}...\n"

        return summary

    def _generate_progress_entry(self) -> str:
        """Generate progress entry."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Get recent significant actions
        recent_actions = [
            t for t in self.history[-10:]
            if t.role == 'assistant' and len(t.content) > 50
        ]

        entry = f"## {now}\n"
        if recent_actions:
            entry += "**Completed:**\n"
            for action in recent_actions:
                entry += f"- {action.content[:100]}...\n"

        return entry

    def _analyze_next_steps(self) -> Dict[str, str]:
        """Analyze conversation to determine next steps."""

        # Simple heuristic-based analysis
        # In production, use LLM to analyze conversation

        immediate = []
        pending = []
        context_notes = []

        # Look for unfinished tasks in conversation
        for turn in reversed(self.history[-20:]):
            if turn.role == 'user':
                content_lower = turn.content.lower()

                if any(word in content_lower for word in ['todo', 'next', 'should', 'need to']):
                    immediate.append(f"- {turn.content[:100]}")

                if any(word in content_lower for word in ['later', 'eventually', 'maybe']):
                    pending.append(f"- {turn.content[:100]}")

        # Generate context
        if self.history:
            last_turn = self.history[-1]
            context_notes.append(f"Last activity: {last_turn.content[:150]}...")

        return {
            'immediate': '\n'.join(immediate) if immediate else "*No immediate actions identified*",
            'pending': '\n'.join(pending) if pending else "*No pending tasks*",
            'context': '\n'.join(context_notes) if context_notes else "*No additional context*"
        }

    def _generate_recent_activity_summary(self) -> str:
        """Generate summary of recent activity."""
        recent = self.history[-10:]

        summary = ""
        for turn in recent:
            timestamp = datetime.fromisoformat(turn.timestamp).strftime('%H:%M')
            role_emoji = "👤" if turn.role == "user" else "🤖"
            provider = turn.llm_provider[:3].upper()

            summary += f"{role_emoji} **{timestamp}** [{provider}] {turn.content[:80]}...\n\n"

        return summary

    def _is_git_repo(self) -> bool:
        """Check if project root is a git repository."""
        return (self.project_root / '.git').exists()

    def _commit_to_github(self):
        """Commit changes to GitHub with semantic summary."""
        try:
            os.chdir(self.project_root)

            # Stage context files
            files_to_commit = [
                'CLAUDE.md', 'gemini.md', 'Agents.md',
                'NEXT_STEPS.md', 'PROGRESS.md'
            ]

            for file in files_to_commit:
                if (self.project_root / file).exists():
                    subprocess.run(['git', 'add', file], check=True)

            # Generate commit message
            commit_msg = self._generate_commit_message()

            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info(f"Committed to Git: {commit_msg}")

                # Optionally push (commented out for safety)
                # subprocess.run(['git', 'push'], check=True)
            else:
                if 'nothing to commit' not in result.stdout:
                    logger.warning(f"Git commit returned non-zero: {result.stderr}")

        except Exception as e:
            logger.error(f"Git commit failed: {e}")

    def _generate_commit_message(self) -> str:
        """Generate semantic commit message."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Analyze recent activity
        recent_user_turns = [
            t for t in self.history[-5:]
            if t.role == 'user'
        ]

        if recent_user_turns:
            last_topic = recent_user_turns[-1].content[:50]
            return f"docs: Update context - {last_topic}... [{timestamp}]"
        else:
            return f"docs: Update session context [{timestamp}]"

    def get_history(self, last_n: Optional[int] = None, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history with optional filtering.

        Args:
            last_n: Return only last N turns
            provider: Filter by LLM provider

        Returns:
            List of conversation turns
        """
        history = self.history

        if provider:
            history = [t for t in history if t.llm_provider == provider]

        if last_n:
            history = history[-last_n:]

        return [t.to_dict() for t in history]

    def set_context(self, key: str, value: Any):
        """Set session context variable."""
        self.context[key] = value
        self.last_activity = datetime.now()

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get session context variable."""
        return self.context.get(key, default)

    def save_to_file(self, filepath: Optional[str] = None):
        """Save session to JSON file."""
        if filepath is None:
            filepath = self.project_root / f".sessions/{self.session_id}.json"

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'history': [t.to_dict() for t in self.history],
            'context': self.context,
            'project_root': str(self.project_root)
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Session saved to {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str) -> 'EnhancedSessionManager':
        """Load session from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        session = cls(
            session_id=data['session_id'],
            project_root=data.get('project_root')
        )

        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_activity = datetime.fromisoformat(data['last_activity'])
        session.context = data['context']

        # Reconstruct history
        session.history = [
            ConversationTurn(**turn_data)
            for turn_data in data['history']
        ]

        logger.info(f"Session loaded from {filepath}")
        return session

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        provider_counts = {}
        for turn in self.history:
            provider = turn.llm_provider
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'duration_minutes': (self.last_activity - self.created_at).total_seconds() / 60,
            'total_turns': len(self.history),
            'provider_counts': provider_counts,
            'updates_since_commit': self.updates_since_commit,
            'last_commit': self.last_commit_at.isoformat() if self.last_commit_at else None
        }
