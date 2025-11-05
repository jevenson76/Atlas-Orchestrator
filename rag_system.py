"""
RAG-enhanced agent system with structured output enforcement and source tracking.

Phase B implementation focusing on RAG integrity:
- Structured outputs (answers + sources + confidence scores)
- Explicit "no relevant context found" handling
- Full source metadata tracking (page, doc name, author)
"""

import os
import time
import json
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError, APITimeoutError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    APIError = Exception
    APIConnectionError = Exception
    RateLimitError = Exception
    APITimeoutError = Exception
    ANTHROPIC_AVAILABLE = False
    logging.warning("anthropic package not installed. Install with: pip install anthropic")

# Import existing components
from agent_system import CircuitBreaker, CostTracker, ExponentialBackoff, ModelPricing
from core.models import ModelSelector
from core.constants import Models, Limits

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SourceMetadata:
    """Comprehensive source metadata for RAG outputs."""

    document_name: str
    page: Optional[int] = None
    author: Optional[str] = None
    url: Optional[str] = None
    date: Optional[str] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    relevance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'document_name': self.document_name,
            'page': self.page,
            'author': self.author,
            'url': self.url,
            'date': self.date,
            'section': self.section,
            'chunk_id': self.chunk_id,
            'relevance_score': round(self.relevance_score, 4)
        }

    def __str__(self) -> str:
        """Human-readable source citation."""
        parts = [self.document_name]
        if self.author:
            parts.append(f"by {self.author}")
        if self.page:
            parts.append(f"p. {self.page}")
        if self.section:
            parts.append(f"§ {self.section}")
        if self.url:
            parts.append(f"({self.url})")
        return ", ".join(parts)


@dataclass
class RAGOutput:
    """
    Structured output format for RAG operations.

    Enforces integrity by requiring all fields and providing
    clear indicators when context is insufficient.
    """

    answer: str
    sources: List[SourceMetadata] = field(default_factory=list)
    confidence: float = 0.0
    context_found: bool = False
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'answer': self.answer,
            'sources': [s.to_dict() for s in self.sources],
            'confidence': round(self.confidence, 4),
            'context_found': self.context_found,
            'reasoning': self.reasoning,
            'metadata': self.metadata
        }

    def is_valid(self) -> bool:
        """Check if output meets quality standards."""
        if not self.context_found:
            return self.answer == "I don't have relevant information to answer that question."

        return (
            self.confidence >= 0.5 and
            len(self.sources) > 0 and
            len(self.answer) > 0
        )

    def format_citation(self) -> str:
        """Format answer with inline citations."""
        if not self.sources:
            return self.answer

        citation_text = f"\n\nSources:\n"
        for i, source in enumerate(self.sources, 1):
            citation_text += f"[{i}] {source}\n"

        return self.answer + citation_text


class RAGBaseAgent:
    """
    RAG-enhanced base agent with enforced structured outputs.

    Features:
    - Mandatory structured output format (answer + sources + confidence)
    - Explicit handling of "no context found" scenarios
    - Full source metadata tracking
    - Built-in validation of RAG responses
    - Automatic retry with exponential backoff
    - Circuit breaker protection
    - Cost tracking
    """

    def __init__(self,
                 role: str,
                 model: str = Models.HAIKU,
                 api_key: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2048,
                 max_retries: int = Limits.MAX_RETRIES,
                 use_circuit_breaker: bool = True,
                 cost_tracker: Optional[CostTracker] = None,
                 system_prompt: Optional[str] = None,
                 enforce_citations: bool = True,
                 min_confidence: float = 0.5):
        """
        Initialize RAG-enhanced agent.

        Args:
            role: Agent's role/purpose
            model: Model to use
            api_key: API key (uses env var if not provided)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response tokens
            max_retries: Maximum retry attempts
            use_circuit_breaker: Enable circuit breaker
            cost_tracker: Optional shared cost tracker
            system_prompt: Optional custom system prompt
            enforce_citations: Require sources for all answers
            min_confidence: Minimum confidence threshold
        """
        self.role = role
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.system_prompt = system_prompt
        self.enforce_citations = enforce_citations
        self.min_confidence = min_confidence

        # Initialize client
        if ANTHROPIC_AVAILABLE:
            api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
            self.client = Anthropic(api_key=api_key) if api_key else None
        else:
            self.client = None
            logger.warning("Anthropic client not available - install with: pip install anthropic")

        # Initialize resilience components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=Limits.CIRCUIT_BREAKER_THRESHOLD,
            recovery_timeout=Limits.DEFAULT_TIMEOUT,
            expected_exception=Exception
        ) if use_circuit_breaker else None

        self.backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )

        # Initialize tracking
        self.cost_tracker = cost_tracker or CostTracker()
        self.agent_id = f"RAG_{role}_{model}_{id(self)}"

        logger.info(f"RAG Agent initialized: {self.agent_id} with model {model}")

    def query(self,
              question: str,
              retrieved_context: List[Dict[str, Any]],
              context_metadata: Optional[Dict[str, Any]] = None,
              require_sources: bool = True) -> RAGOutput:
        """
        Query agent with retrieved context and enforce structured output.

        Args:
            question: User's question
            retrieved_context: List of retrieved document chunks with metadata
            context_metadata: Optional additional context metadata
            require_sources: Whether to require source citations

        Returns:
            RAGOutput with answer, sources, and confidence score
        """
        # Check if context is empty
        if not retrieved_context:
            return self._no_context_response(question)

        # Build RAG prompt with structured output instructions
        prompt = self._build_rag_prompt(question, retrieved_context, require_sources)

        # Make API call with retry logic
        for attempt in range(self.max_retries):
            start_time = time.time()

            try:
                # Use circuit breaker if enabled
                if self.circuit_breaker:
                    response = self.circuit_breaker.call(
                        self._make_api_call,
                        prompt,
                        self._build_system_prompt(),
                        self.temperature,
                        self.max_tokens
                    )
                else:
                    response = self._make_api_call(
                        prompt,
                        self._build_system_prompt(),
                        self.temperature,
                        self.max_tokens
                    )

                # Calculate metrics
                latency = time.time() - start_time
                cost = ModelPricing.calculate_cost(
                    self.model,
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )

                # Track success
                self.cost_tracker.track(
                    self.agent_id,
                    self.model,
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    cost,
                    latency,
                    success=True
                )

                # Parse structured output
                rag_output = self._parse_response(
                    response.content[0].text,
                    retrieved_context,
                    {
                        'tokens_in': response.usage.input_tokens,
                        'tokens_out': response.usage.output_tokens,
                        'cost': cost,
                        'latency': latency,
                        'attempt': attempt + 1
                    }
                )

                # Validate output
                if not rag_output.is_valid():
                    logger.warning(f"RAG output failed validation (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        continue

                logger.info(f"RAG query successful: {self.agent_id} (confidence: {rag_output.confidence:.2f})")
                return rag_output

            except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                logger.warning(f"API error (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries - 1:
                    delay = self.backoff.get_delay(attempt)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    return self._error_response(question, str(e))

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return self._error_response(question, str(e))

        return self._error_response(question, "Max retries exceeded")

    def _build_rag_prompt(self,
                          question: str,
                          retrieved_context: List[Dict[str, Any]],
                          require_sources: bool) -> str:
        """Build prompt with structured output instructions."""

        # Format retrieved context with source markers
        context_parts = []
        for i, chunk in enumerate(retrieved_context):
            source_marker = f"[Source {i+1}]"
            content = chunk.get('content', chunk.get('text', ''))
            metadata = chunk.get('metadata', {})

            context_part = f"{source_marker}\n{content}\n"
            if metadata:
                context_part += f"Metadata: {json.dumps(metadata, indent=2)}\n"

            context_parts.append(context_part)

        context = "\n".join(context_parts)

        prompt = f"""Answer the following question based ONLY on the provided context.

Question: {question}

Context:
{context}

CRITICAL INSTRUCTIONS:
1. Only use information from the provided context
2. If the context doesn't contain relevant information, respond with EXACTLY: "I don't have relevant information to answer that question."
3. Cite specific sources using [Source N] notation
4. Provide your response in the following JSON format:

{{
    "answer": "Your answer here with [Source N] citations",
    "confidence": 0.0-1.0 (how confident you are in the answer),
    "context_found": true/false (whether relevant context was found),
    "reasoning": "Brief explanation of how you arrived at the answer",
    "source_ids": [list of source numbers used, e.g., [1, 2, 3]]
}}

Example response when context is found:
{{
    "answer": "The capital of France is Paris [Source 1]. It has been the capital since 987 CE [Source 2].",
    "confidence": 0.95,
    "context_found": true,
    "reasoning": "Both sources directly state Paris as the capital",
    "source_ids": [1, 2]
}}

Example response when NO relevant context is found:
{{
    "answer": "I don't have relevant information to answer that question.",
    "confidence": 0.0,
    "context_found": false,
    "reasoning": "The provided context does not contain information about this topic",
    "source_ids": []
}}

Provide ONLY the JSON response, no additional text."""

        return prompt

    def _build_system_prompt(self) -> str:
        """Build system prompt for RAG operations."""
        if self.system_prompt:
            return self.system_prompt

        return f"""You are {self.role}, a specialized RAG (Retrieval-Augmented Generation) assistant.

Your core responsibilities:
1. Answer questions ONLY based on provided context
2. Always cite sources using [Source N] notation
3. Be honest when context doesn't contain relevant information
4. Provide structured JSON responses
5. Include confidence scores and reasoning

NEVER make up information or use knowledge outside the provided context."""

    def _make_api_call(self, prompt: str, system: str,
                      temperature: float, max_tokens: int):
        """Make the actual API call."""
        return self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )

    def _parse_response(self,
                       response_text: str,
                       retrieved_context: List[Dict[str, Any]],
                       call_metadata: Dict[str, Any]) -> RAGOutput:
        """Parse structured response into RAGOutput."""

        try:
            # Try to parse JSON response
            # First, try to extract JSON if it's wrapped in other text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                parsed = json.loads(json_str)
            else:
                # If no JSON found, treat entire response as answer
                parsed = {
                    'answer': response_text,
                    'confidence': 0.5,
                    'context_found': True,
                    'reasoning': 'Fallback parsing',
                    'source_ids': list(range(1, len(retrieved_context) + 1))
                }

            # Extract source IDs
            source_ids = parsed.get('source_ids', [])

            # Build source metadata
            sources = []
            for source_id in source_ids:
                if 0 < source_id <= len(retrieved_context):
                    chunk = retrieved_context[source_id - 1]
                    metadata = chunk.get('metadata', {})

                    source = SourceMetadata(
                        document_name=metadata.get('title', metadata.get('document_name', f'Document {source_id}')),
                        page=metadata.get('page'),
                        author=metadata.get('author'),
                        url=metadata.get('url'),
                        date=metadata.get('date'),
                        section=metadata.get('section'),
                        chunk_id=metadata.get('chunk_id', str(source_id)),
                        relevance_score=chunk.get('score', metadata.get('relevance_score', 0.0))
                    )
                    sources.append(source)

            # Create RAGOutput
            return RAGOutput(
                answer=parsed.get('answer', ''),
                sources=sources,
                confidence=float(parsed.get('confidence', 0.0)),
                context_found=parsed.get('context_found', False),
                reasoning=parsed.get('reasoning'),
                metadata=call_metadata
            )

        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            logger.debug(f"Response text: {response_text}")

            # Return error response
            return RAGOutput(
                answer=f"Error parsing response: {str(e)}",
                sources=[],
                confidence=0.0,
                context_found=False,
                reasoning="Parse error",
                metadata=call_metadata
            )

    def _no_context_response(self, question: str) -> RAGOutput:
        """Generate response when no context is provided."""
        logger.warning(f"No context provided for question: {question[:50]}...")

        return RAGOutput(
            answer="I don't have relevant information to answer that question.",
            sources=[],
            confidence=0.0,
            context_found=False,
            reasoning="No retrieved context provided",
            metadata={'error': 'no_context'}
        )

    def _error_response(self, question: str, error: str) -> RAGOutput:
        """Generate response for errors."""
        logger.error(f"Error processing question '{question[:50]}...': {error}")

        return RAGOutput(
            answer=f"I encountered an error processing your question: {error}",
            sources=[],
            confidence=0.0,
            context_found=False,
            reasoning=f"Error: {error}",
            metadata={'error': error}
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent's performance metrics."""
        circuit_status = self.circuit_breaker.get_status() if self.circuit_breaker else None

        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'model': self.model,
            'enforce_citations': self.enforce_citations,
            'min_confidence': self.min_confidence,
            'circuit_breaker': circuit_status
        }


class SessionManager:
    """
    Manage multi-turn RAG sessions with conversation history.

    Features:
    - Track conversation history
    - Maintain context across turns
    - Session persistence
    - Memory management
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize session manager.

        Args:
            session_id: Unique session identifier (auto-generated if not provided)
        """
        self.session_id = session_id or f"session_{int(time.time())}_{os.getpid()}"
        self.history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

        logger.info(f"SessionManager created: {self.session_id}")

    def add_turn(self,
                 question: str,
                 answer: RAGOutput,
                 retrieved_context: List[Dict[str, Any]]) -> None:
        """
        Add a conversation turn to history.

        Args:
            question: User's question
            answer: RAG output
            retrieved_context: Context used for this turn
        """
        turn = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'answer': answer.to_dict(),
            'context_count': len(retrieved_context),
            'confidence': answer.confidence,
            'sources_count': len(answer.sources)
        }

        self.history.append(turn)
        self.last_activity = datetime.now()

        logger.debug(f"Turn added to session {self.session_id}: {len(self.history)} turns total")

    def get_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            last_n: Number of recent turns to retrieve (all if None)

        Returns:
            List of conversation turns
        """
        if last_n:
            return self.history[-last_n:]
        return self.history

    def set_context(self, key: str, value: Any) -> None:
        """Set session context variable."""
        self.context[key] = value
        self.last_activity = datetime.now()

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get session context variable."""
        return self.context.get(key, default)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history = []
        logger.info(f"History cleared for session {self.session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_turns = len(self.history)
        avg_confidence = sum(t['confidence'] for t in self.history) / max(total_turns, 1)

        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'total_turns': total_turns,
            'avg_confidence': round(avg_confidence, 4),
            'context_keys': list(self.context.keys())
        }

    def save(self, filepath: str) -> None:
        """Save session to file."""
        data = {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'history': self.history,
            'context': self.context
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Session saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'SessionManager':
        """Load session from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        session = cls(session_id=data['session_id'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_activity = datetime.fromisoformat(data['last_activity'])
        session.history = data['history']
        session.context = data['context']

        logger.info(f"Session loaded from {filepath}")
        return session


class ContextSyncEngine:
    """
    Synchronize and manage context across multiple agents and sessions.

    Features:
    - Share context between agents
    - Deduplicate retrieved documents
    - Track context usage
    - Optimize context window
    """

    def __init__(self, max_context_tokens: int = 150000):
        """
        Initialize context sync engine.

        Args:
            max_context_tokens: Maximum context window size
        """
        self.max_context_tokens = max_context_tokens
        self.shared_context: Dict[str, Any] = {}
        self.context_usage: Dict[str, int] = defaultdict(int)
        self.document_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"ContextSyncEngine initialized with max {max_context_tokens} tokens")

    def add_shared_context(self, key: str, value: Any) -> None:
        """Add context that can be shared across agents."""
        self.shared_context[key] = value
        logger.debug(f"Shared context added: {key}")

    def get_shared_context(self, key: str, default: Any = None) -> Any:
        """Get shared context."""
        self.context_usage[key] += 1
        return self.shared_context.get(key, default)

    def register_document(self, doc_id: str, document: Dict[str, Any]) -> None:
        """
        Register a document in the cache.

        Args:
            doc_id: Unique document identifier
            document: Document data
        """
        self.document_cache[doc_id] = {
            'content': document,
            'registered_at': datetime.now().isoformat(),
            'access_count': 0
        }
        logger.debug(f"Document registered: {doc_id}")

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached document."""
        if doc_id in self.document_cache:
            self.document_cache[doc_id]['access_count'] += 1
            return self.document_cache[doc_id]['content']
        return None

    def deduplicate_context(self,
                           retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate chunks from retrieved context.

        Args:
            retrieved_chunks: List of retrieved document chunks

        Returns:
            Deduplicated list of chunks
        """
        seen = set()
        deduped = []

        for chunk in retrieved_chunks:
            # Create hash of content
            content = chunk.get('content', chunk.get('text', ''))
            content_hash = hash(content[:200])  # Use first 200 chars for hash

            if content_hash not in seen:
                seen.add(content_hash)
                deduped.append(chunk)

        removed = len(retrieved_chunks) - len(deduped)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate chunks from context")

        return deduped

    def optimize_context_window(self,
                                chunks: List[Dict[str, Any]],
                                target_tokens: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Optimize context to fit within token limit.

        Args:
            chunks: List of document chunks
            target_tokens: Target token count (uses max if not specified)

        Returns:
            Optimized list of chunks
        """
        target = target_tokens or self.max_context_tokens

        # Sort by relevance score (highest first)
        sorted_chunks = sorted(
            chunks,
            key=lambda x: x.get('score', x.get('metadata', {}).get('relevance_score', 0.0)),
            reverse=True
        )

        # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
        current_tokens = 0
        optimized = []

        for chunk in sorted_chunks:
            content = chunk.get('content', chunk.get('text', ''))
            chunk_tokens = len(content) // 4

            if current_tokens + chunk_tokens <= target:
                optimized.append(chunk)
                current_tokens += chunk_tokens
            else:
                break

        if len(optimized) < len(sorted_chunks):
            logger.info(f"Context optimized: {len(sorted_chunks)} → {len(optimized)} chunks ({current_tokens} tokens)")

        return optimized

    def get_stats(self) -> Dict[str, Any]:
        """Get context sync statistics."""
        return {
            'shared_context_keys': len(self.shared_context),
            'cached_documents': len(self.document_cache),
            'most_used_context': sorted(
                self.context_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'total_context_accesses': sum(self.context_usage.values())
        }
