"""
Context Synchronization Engine for Multi-LLM Collaboration

PRIORITY 3: Multi-LLM Collaboration
- Filesystem-based context sync across Claude, Gemini, OpenAI
- Shared memory and knowledge base
- Conflict resolution and merging
- Real-time context updates
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import difflib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Single context entry that can be shared across LLMs."""

    key: str
    value: Any
    source_llm: str  # Which LLM created this
    timestamp: str
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'value': self.value,
            'source_llm': self.source_llm,
            'timestamp': self.timestamp,
            'version': self.version,
            'metadata': self.metadata
        }

    def get_hash(self) -> str:
        """Get content hash for change detection."""
        content = json.dumps(self.value, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()


class ContextSyncEngine:
    """
    Synchronize context across multiple LLM providers via filesystem.

    Features:
    - Shared context store accessible to all LLMs
    - Real-time file-based synchronization
    - Conflict detection and resolution
    - Version tracking
    - Provider-specific context isolation when needed
    """

    def __init__(self,
                 sync_dir: Optional[str] = None,
                 auto_sync: bool = True,
                 sync_interval_seconds: int = 5):
        """
        Initialize context sync engine.

        Args:
            sync_dir: Directory for shared context (auto-detect if None)
            auto_sync: Automatically sync changes
            sync_interval_seconds: How often to check for updates
        """
        self.sync_dir = Path(sync_dir) if sync_dir else self._get_default_sync_dir()
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval_seconds

        # Ensure sync directory exists
        self.sync_dir.mkdir(parents=True, exist_ok=True)

        # In-memory context store
        self.context: Dict[str, ContextEntry] = {}

        # Provider-specific contexts
        self.provider_contexts: Dict[str, Dict[str, Any]] = {
            'claude': {},
            'gemini': {},
            'openai': {}
        }

        # Sync metadata
        self.last_sync: Optional[datetime] = None
        self.sync_count = 0
        self.conflict_count = 0

        # File paths
        self.shared_context_file = self.sync_dir / 'shared_context.json'
        self.claude_context_file = self.sync_dir / 'claude_context.json'
        self.gemini_context_file = self.sync_dir / 'gemini_context.json'
        self.openai_context_file = self.sync_dir / 'openai_context.json'
        self.sync_log_file = self.sync_dir / 'sync_log.jsonl'

        # Load existing context
        self._load_from_disk()

        logger.info(f"ContextSyncEngine initialized at {self.sync_dir}")

    def _get_default_sync_dir(self) -> Path:
        """Get default sync directory."""
        # Look for project root
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current / '.context_sync'
            current = current.parent

        # Fallback to current directory
        return Path.cwd() / '.context_sync'

    def set_context(self,
                   key: str,
                   value: Any,
                   source_llm: str = 'claude',
                   metadata: Optional[Dict[str, Any]] = None):
        """
        Set shared context that syncs across all LLMs.

        Args:
            key: Context key
            value: Context value (must be JSON-serializable)
            source_llm: Which LLM is setting this
            metadata: Optional metadata
        """
        # Check if key exists
        if key in self.context:
            existing = self.context[key]

            # Check for conflicts
            if existing.get_hash() != self._get_value_hash(value):
                self.conflict_count += 1
                logger.warning(
                    f"Context conflict detected for '{key}': "
                    f"{existing.source_llm} vs {source_llm}"
                )

                # Resolve conflict (newest wins)
                existing.value = value
                existing.source_llm = source_llm
                existing.timestamp = datetime.now().isoformat()
                existing.version += 1
                existing.metadata = metadata or {}
            else:
                # Same value, just update timestamp
                existing.timestamp = datetime.now().isoformat()
        else:
            # New entry
            self.context[key] = ContextEntry(
                key=key,
                value=value,
                source_llm=source_llm,
                timestamp=datetime.now().isoformat(),
                metadata=metadata or {}
            )

        # Auto-sync if enabled
        if self.auto_sync:
            self._save_to_disk()

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get shared context value.

        Args:
            key: Context key
            default: Default value if not found

        Returns:
            Context value
        """
        # Sync first if auto-sync enabled
        if self.auto_sync and self._should_sync():
            self.sync_from_disk()

        entry = self.context.get(key)
        return entry.value if entry else default

    def set_provider_context(self,
                            provider: str,
                            key: str,
                            value: Any):
        """
        Set provider-specific context (not shared).

        Args:
            provider: LLM provider (claude, gemini, openai)
            key: Context key
            value: Context value
        """
        if provider not in self.provider_contexts:
            self.provider_contexts[provider] = {}

        self.provider_contexts[provider][key] = value

        # Save provider-specific context
        if self.auto_sync:
            self._save_provider_context(provider)

    def get_provider_context(self,
                            provider: str,
                            key: str,
                            default: Any = None) -> Any:
        """Get provider-specific context."""
        if provider not in self.provider_contexts:
            return default

        return self.provider_contexts[provider].get(key, default)

    def sync_from_disk(self):
        """Manually trigger sync from disk."""
        self._load_from_disk()
        self.last_sync = datetime.now()
        self.sync_count += 1

        logger.debug(f"Synced from disk (sync #{self.sync_count})")

    def sync_to_disk(self):
        """Manually trigger sync to disk."""
        self._save_to_disk()
        self.last_sync = datetime.now()
        self.sync_count += 1

        logger.debug(f"Synced to disk (sync #{self.sync_count})")

    def _should_sync(self) -> bool:
        """Check if it's time to sync."""
        if not self.last_sync:
            return True

        elapsed = (datetime.now() - self.last_sync).total_seconds()
        return elapsed >= self.sync_interval

    def _load_from_disk(self):
        """Load shared context from disk."""
        try:
            # Load shared context
            if self.shared_context_file.exists():
                with open(self.shared_context_file, 'r') as f:
                    data = json.load(f)

                for entry_data in data.get('entries', []):
                    entry = ContextEntry(**entry_data)
                    self.context[entry.key] = entry

                logger.debug(f"Loaded {len(self.context)} shared context entries")

            # Load provider-specific contexts
            for provider in ['claude', 'gemini', 'openai']:
                self._load_provider_context(provider)

        except Exception as e:
            logger.error(f"Failed to load context from disk: {e}")

    def _load_provider_context(self, provider: str):
        """Load provider-specific context."""
        file_map = {
            'claude': self.claude_context_file,
            'gemini': self.gemini_context_file,
            'openai': self.openai_context_file
        }

        context_file = file_map.get(provider)
        if not context_file or not context_file.exists():
            return

        try:
            with open(context_file, 'r') as f:
                self.provider_contexts[provider] = json.load(f)

            logger.debug(f"Loaded {provider} context ({len(self.provider_contexts[provider])} entries)")

        except Exception as e:
            logger.error(f"Failed to load {provider} context: {e}")

    def _save_to_disk(self):
        """Save shared context to disk."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'entries': [entry.to_dict() for entry in self.context.values()]
            }

            with open(self.shared_context_file, 'w') as f:
                json.dump(data, f, indent=2)

            # Log sync
            self._log_sync('save_shared', len(self.context))

            logger.debug(f"Saved {len(self.context)} shared context entries")

        except Exception as e:
            logger.error(f"Failed to save context to disk: {e}")

    def _save_provider_context(self, provider: str):
        """Save provider-specific context."""
        file_map = {
            'claude': self.claude_context_file,
            'gemini': self.gemini_context_file,
            'openai': self.openai_context_file
        }

        context_file = file_map.get(provider)
        if not context_file:
            return

        try:
            with open(context_file, 'w') as f:
                json.dump(self.provider_contexts[provider], f, indent=2)

            self._log_sync(f'save_{provider}', len(self.provider_contexts[provider]))

            logger.debug(f"Saved {provider} context ({len(self.provider_contexts[provider])} entries)")

        except Exception as e:
            logger.error(f"Failed to save {provider} context: {e}")

    def _log_sync(self, action: str, entry_count: int):
        """Log sync operation."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'entry_count': entry_count,
            'sync_count': self.sync_count,
            'conflict_count': self.conflict_count
        }

        try:
            with open(self.sync_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write sync log: {e}")

    def _get_value_hash(self, value: Any) -> str:
        """Get hash of value for change detection."""
        content = json.dumps(value, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def merge_contexts(self,
                      external_context: Dict[str, Any],
                      source_llm: str,
                      strategy: str = 'newest_wins') -> Dict[str, Any]:
        """
        Merge external context with current context.

        Args:
            external_context: Context from another LLM
            source_llm: Which LLM provided this context
            strategy: Merge strategy ('newest_wins', 'manual', 'preserve_both')

        Returns:
            Merge report with conflicts and resolutions
        """
        conflicts = []
        merged_count = 0

        for key, value in external_context.items():
            if key in self.context:
                existing = self.context[key]

                # Check for conflict
                if existing.get_hash() != self._get_value_hash(value):
                    conflicts.append({
                        'key': key,
                        'existing_source': existing.source_llm,
                        'new_source': source_llm,
                        'existing_value': existing.value,
                        'new_value': value
                    })

                    if strategy == 'newest_wins':
                        # Newest wins (external context is newer)
                        self.set_context(key, value, source_llm)
                        merged_count += 1

                    elif strategy == 'preserve_both':
                        # Keep both with suffixes
                        self.set_context(f"{key}_{existing.source_llm}", existing.value, existing.source_llm)
                        self.set_context(f"{key}_{source_llm}", value, source_llm)
                        merged_count += 2

                    # 'manual' strategy: do nothing, just report
            else:
                # No conflict, just add
                self.set_context(key, value, source_llm)
                merged_count += 1

        report = {
            'merged_count': merged_count,
            'conflict_count': len(conflicts),
            'conflicts': conflicts,
            'strategy': strategy
        }

        logger.info(f"Merged context: {merged_count} entries, {len(conflicts)} conflicts")

        return report

    def get_all_context(self) -> Dict[str, Any]:
        """Get all shared context as a dictionary."""
        return {
            key: entry.value
            for key, entry in self.context.items()
        }

    def get_context_by_source(self, source_llm: str) -> Dict[str, Any]:
        """Get all context entries from a specific LLM."""
        return {
            key: entry.value
            for key, entry in self.context.items()
            if entry.source_llm == source_llm
        }

    def clear_context(self, source_llm: Optional[str] = None):
        """
        Clear context.

        Args:
            source_llm: If provided, only clear context from this LLM
        """
        if source_llm:
            # Clear only entries from specific LLM
            keys_to_remove = [
                key for key, entry in self.context.items()
                if entry.source_llm == source_llm
            ]
            for key in keys_to_remove:
                del self.context[key]

            logger.info(f"Cleared {len(keys_to_remove)} entries from {source_llm}")
        else:
            # Clear all
            count = len(self.context)
            self.context.clear()
            logger.info(f"Cleared all {count} context entries")

        # Sync to disk
        if self.auto_sync:
            self._save_to_disk()

    def get_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics."""
        # Count entries by source
        source_counts = defaultdict(int)
        for entry in self.context.values():
            source_counts[entry.source_llm] += 1

        return {
            'total_entries': len(self.context),
            'source_counts': dict(source_counts),
            'sync_count': self.sync_count,
            'conflict_count': self.conflict_count,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_dir': str(self.sync_dir),
            'auto_sync': self.auto_sync,
            'provider_contexts': {
                provider: len(ctx)
                for provider, ctx in self.provider_contexts.items()
            }
        }

    def export_to_file(self, filepath: str):
        """Export all context to a single file."""
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'shared_context': [entry.to_dict() for entry in self.context.values()],
            'provider_contexts': self.provider_contexts,
            'stats': self.get_stats()
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Context exported to {filepath}")

    def import_from_file(self, filepath: str):
        """Import context from exported file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Import shared context
        for entry_data in data.get('shared_context', []):
            entry = ContextEntry(**entry_data)
            self.context[entry.key] = entry

        # Import provider contexts
        if 'provider_contexts' in data:
            for provider, ctx in data['provider_contexts'].items():
                self.provider_contexts[provider] = ctx

        logger.info(f"Context imported from {filepath}")

        # Sync to disk
        if self.auto_sync:
            self._save_to_disk()
            for provider in self.provider_contexts:
                self._save_provider_context(provider)
