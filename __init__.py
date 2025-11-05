"""
Global Multi-Agent System Library - Phase B Implementation

Production-ready framework for orchestrating AI agents with:
- Multi-provider resilience (Anthropic, Gemini, OpenAI)
- Enhanced security (injection detection, input sanitization)
- Session management with GitHub autosave
- Context synchronization across LLMs
- Cost tracking with budget protection

Usage in any project:
    import sys
    sys.path.insert(0, '/home/jevenson/.claude/lib')

    # Phase B Components (Recommended)
    from resilient_agent import ResilientBaseAgent
    from session_management import EnhancedSessionManager
    from context_sync import ContextSyncEngine
    from resilience import EnhancedCircuitBreaker, ModelFallbackChain

    # Legacy Components (Still Available)
    from agent_system import BaseAgent, CircuitBreaker, CostTracker
    from orchestrator import Orchestrator, SubAgent

Author: Claude Code
Version: 2.1.0-beta (Phase B)
"""

# Try package-style imports first, fall back to direct imports
try:
    # Legacy core components
    from .agent_system import (
        BaseAgent,
        CircuitBreaker,
        CostTracker,
        ExponentialBackoff,
        ModelPricing,
        AgentMetrics
    )

    from .orchestrator import (
        Orchestrator,
        SubAgent,
        ExecutionMode
    )

    # Phase B - Priority 1: Resilience
    from .resilience import (
        EnhancedCircuitBreaker,
        ModelFallbackChain,
        SecurityValidator,
        CircuitState
    )

    from .resilient_agent import (
        ResilientBaseAgent,
        CallResult
    )

    # Phase B - Priority 2: Session Management
    from .session_management import (
        EnhancedSessionManager,
        ConversationTurn
    )

    # Phase B - Priority 3: Context Sync
    from .context_sync import (
        ContextSyncEngine,
        ContextEntry
    )

except ImportError:
    # Direct imports (not as package)
    from agent_system import (
        BaseAgent,
        CircuitBreaker,
        CostTracker,
        ExponentialBackoff,
        ModelPricing,
        AgentMetrics
    )

    from orchestrator import (
        Orchestrator,
        SubAgent,
        ExecutionMode
    )

    from resilience import (
        EnhancedCircuitBreaker,
        ModelFallbackChain,
        SecurityValidator,
        CircuitState
    )

    from resilient_agent import (
        ResilientBaseAgent,
        CallResult
    )

    from session_management import (
        EnhancedSessionManager,
        ConversationTurn
    )

    from context_sync import (
        ContextSyncEngine,
        ContextEntry
    )

__all__ = [
    # Phase B - Priority 1: Resilience
    'EnhancedCircuitBreaker',
    'ModelFallbackChain',
    'SecurityValidator',
    'CircuitState',
    'ResilientBaseAgent',
    'CallResult',

    # Phase B - Priority 2: Session Management
    'EnhancedSessionManager',
    'ConversationTurn',

    # Phase B - Priority 3: Context Sync
    'ContextSyncEngine',
    'ContextEntry',

    # Legacy Core
    'BaseAgent',
    'CircuitBreaker',
    'CostTracker',
    'ExponentialBackoff',
    'ModelPricing',
    'AgentMetrics',

    # Orchestration
    'Orchestrator',
    'SubAgent',
    'ExecutionMode',
]

__version__ = '2.1.0-beta'