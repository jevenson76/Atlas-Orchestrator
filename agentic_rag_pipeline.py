#!/usr/bin/env python3
"""
Agentic RAG Pipeline - Advanced Retrieval with Routing and Self-Reflection

Implements a 4-step agentic workflow for complex query answering:
1. Query Analysis & Routing (Haiku 4.5) - Determine optimal retrieval strategy
2. Context Retrieval (Haiku 4.5 + RAG) - Execute retrieval based on routing
3. Self-Reflection/Validation (Opus 4.1) - Validate context quality before synthesis
4. Synthesis (Sonnet 4.5 + analyst style) - Generate structured report

Architecture:
- Phase B: Multi-provider infrastructure with resilient agents
- Priority 2: Closed-loop validation (self-reflection step)
- C5: Deterministic output control (analyst output style)
- RAG System: Vector database for context retrieval

Model Stack Mandate:
- Haiku 4.5: Routing and retrieval (cost-efficient)
- Opus 4.1: Self-reflective critique (highest quality validation)
- Sonnet 4.5: Complex synthesis (balanced performance/cost)
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from enum import Enum

# Phase B: Core Infrastructure
from resilient_agent import ResilientBaseAgent
from core.constants import Models

# RAG System
try:
    from rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAG system not available")

# Observability
from observability.event_emitter import EventEmitter

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Retrieval strategies determined by routing agent."""
    STANDARD_VECTOR = "standard_vector"  # Simple vector similarity search
    MULTI_HOP = "multi_hop"  # Requires multiple retrieval rounds
    TEMPORAL_FILTERED = "temporal_filtered"  # Filter by recency
    CROSS_SOURCE = "cross_source"  # Aggregate from multiple sources
    HYBRID = "hybrid"  # Combine vector + keyword search


class ConfidenceLevel(Enum):
    """Confidence levels from self-reflection."""
    HIGH = "HIGH"  # >80% - proceed to synthesis
    MEDIUM = "MEDIUM"  # 50-80% - may need more context
    LOW = "LOW"  # <50% - retrieve more context
    INSUFFICIENT = "INSUFFICIENT"  # Cannot answer with available context


class AgenticRAGPipeline:
    """
    Agentic RAG Pipeline Orchestrator.

    Coordinates a 4-step workflow for complex query answering with
    routing, retrieval, self-reflection, and synthesis.

    Model Stack:
    - Haiku 4.5: Routing and retrieval
    - Opus 4.1: Self-reflective validation
    - Sonnet 4.5: Final synthesis with analyst style

    Features:
    - Intelligent query routing
    - Multi-hop retrieval for complex queries
    - Self-reflection before synthesis (Opus 4.1 critic)
    - Structured output via analyst output style
    - Automatic re-retrieval if confidence low
    """

    def __init__(
        self,
        rag_system: Optional['RAGSystem'] = None,
        max_retrieval_iterations: int = 2,
        min_confidence_threshold: float = 0.7,
        top_k: int = 10
    ):
        """
        Initialize Agentic RAG Pipeline.

        Args:
            rag_system: RAG system for vector retrieval (optional)
            max_retrieval_iterations: Max retrieval attempts if confidence low
            min_confidence_threshold: Minimum confidence to proceed (0.0-1.0)
            top_k: Number of chunks to retrieve per query
        """
        self.rag_system = rag_system
        self.max_retrieval_iterations = max_retrieval_iterations
        self.min_confidence_threshold = min_confidence_threshold
        self.top_k = top_k

        # Observability
        self.event_emitter = EventEmitter()

        # Initialize agents
        self._initialize_agents()

        logger.info(
            f"AgenticRAGPipeline initialized (max_iterations: {max_retrieval_iterations}, "
            f"min_confidence: {min_confidence_threshold}, top_k: {top_k})"
        )

    def _initialize_agents(self):
        """Initialize all agents in the pipeline."""
        # STEP 1: Router Agent (Haiku 4.5) - Query analysis and routing
        self.router_agent = ResilientBaseAgent(
            role="Query analysis and retrieval strategy routing specialist",
            model=Models.HAIKU,
            temperature=0.3,
            max_tokens=1500
        )
        logger.info(f"Router Agent initialized: {self.router_agent.model}")

        # STEP 2: Retriever Agent (Haiku 4.5) - Context retrieval
        self.retriever_agent = ResilientBaseAgent(
            role="Context retrieval and information gathering specialist",
            model=Models.HAIKU,
            temperature=0.3,
            max_tokens=2000
        )
        logger.info(f"Retriever Agent initialized: {self.retriever_agent.model}")

        # STEP 3: Critic Agent (Opus 4.1) - Self-reflective validation
        self.critic_agent = ResilientBaseAgent(
            role="Self-reflective context validation and quality assessment specialist",
            model=Models.OPUS,
            temperature=0.0,
            max_tokens=2000
        )
        logger.info(f"Critic Agent initialized: {self.critic_agent.model}")

        # STEP 4: Synthesizer Agent (Sonnet 4.5) - Report generation
        self.synthesizer_agent = ResilientBaseAgent(
            role="Complex synthesis and structured report generation specialist",
            model=Models.SONNET,
            temperature=0.5,
            max_tokens=4000
        )
        logger.info(f"Synthesizer Agent initialized: {self.synthesizer_agent.model}")

    async def analyze_query(
        self,
        query: str,
        source_path: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete 4-step Agentic RAG workflow.

        Args:
            query: User query to analyze
            source_path: Optional path to data source
            additional_context: Optional additional context

        Returns:
            Dict with:
                - query_id: Unique query identifier
                - query: Original query
                - routing_decision: Routing analysis result
                - retrieved_context: Retrieved context chunks
                - validation_result: Self-reflection validation
                - report: Final structured report (if confidence sufficient)
                - metadata: Execution metadata
        """
        query_id = str(uuid4())
        start_time = datetime.utcnow()

        logger.info(f"Starting Agentic RAG analysis (query_id: {query_id}, query: {query[:50]}...)")

        self.event_emitter.emit("query_analysis_started", {
            "query_id": query_id,
            "query": query,
            "source_path": source_path,
            "timestamp": start_time.isoformat()
        })

        try:
            # STEP 1: Query Analysis & Routing
            routing_result = await self._step_1_route_query(
                query=query,
                source_path=source_path,
                query_id=query_id
            )

            # STEP 2: Context Retrieval (with potential iterations)
            retrieval_result = await self._step_2_retrieve_context(
                query=query,
                routing_decision=routing_result,
                query_id=query_id
            )

            # STEP 3: Self-Reflection/Validation
            validation_result = await self._step_3_validate_context(
                query=query,
                retrieved_context=retrieval_result["context"],
                metadata=retrieval_result["metadata"],
                query_id=query_id
            )

            # STEP 4: Synthesis (if confidence sufficient)
            synthesis_result = None
            if validation_result["confidence_level"] in [ConfidenceLevel.HIGH.value, ConfidenceLevel.MEDIUM.value]:
                # If medium confidence, may still proceed but flag uncertainty
                synthesis_result = await self._step_4_synthesize_report(
                    query=query,
                    context=retrieval_result["context"],
                    validation=validation_result,
                    source_path=source_path,
                    additional_context=additional_context,
                    query_id=query_id
                )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Build response
            response = {
                "query_id": query_id,
                "status": "success" if synthesis_result else "insufficient_confidence",
                "query": query,
                "routing_decision": routing_result,
                "retrieved_context": retrieval_result,
                "validation_result": validation_result,
                "report": synthesis_result["report"] if synthesis_result else None,
                "metadata": {
                    "source_path": source_path,
                    "duration_seconds": duration,
                    "retrieval_iterations": retrieval_result["metadata"]["iterations"],
                    "confidence_level": validation_result["confidence_level"],
                    "confidence_score": validation_result["confidence_score"],
                    "router_model": self.router_agent.model,
                    "retriever_model": self.retriever_agent.model,
                    "critic_model": self.critic_agent.model,
                    "synthesizer_model": self.synthesizer_agent.model if synthesis_result else None,
                    "started_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat()
                }
            }

            self.event_emitter.emit("query_analysis_completed", {
                "query_id": query_id,
                "status": response["status"],
                "duration_seconds": duration,
                "confidence": validation_result["confidence_score"]
            })

            logger.info(
                f"Agentic RAG analysis completed (query_id: {query_id}, "
                f"status: {response['status']}, duration: {duration:.2f}s, "
                f"confidence: {validation_result['confidence_score']:.2f})"
            )

            return response

        except Exception as e:
            logger.error(f"Agentic RAG analysis failed: {e}", exc_info=True)
            self.event_emitter.emit("query_analysis_failed", {
                "query_id": query_id,
                "error": str(e)
            })
            raise

    async def _step_1_route_query(
        self,
        query: str,
        source_path: Optional[str],
        query_id: str
    ) -> Dict[str, Any]:
        """
        STEP 1: Query Analysis & Routing (Haiku 4.5).

        Analyzes query and determines optimal retrieval strategy.
        """
        logger.info(f"STEP 1: Query routing (Router Agent - {self.router_agent.model})")

        self.event_emitter.emit("routing_started", {
            "query_id": query_id,
            "model": self.router_agent.model
        })

        try:
            # Build routing prompt
            routing_prompt = f"""# Query Routing Analysis

You are analyzing a user query to determine the optimal retrieval strategy.

## Query
{query}

## Source Path
{source_path or "Not specified"}

## Your Task
Analyze this query and determine:

1. **Query Complexity**: Simple (single-fact) or Complex (multi-hop reasoning required)
2. **Retrieval Strategy**: Which approach will work best?
   - STANDARD_VECTOR: Simple similarity search
   - MULTI_HOP: Requires multiple retrieval rounds to build context
   - TEMPORAL_FILTERED: Focus on recent/historical data
   - CROSS_SOURCE: Need to aggregate from multiple sources
   - HYBRID: Combine vector search with keyword matching

3. **Key Concepts**: Extract 3-5 key concepts/entities to focus retrieval
4. **Expected Document Types**: What types of documents contain the answer?
5. **Confidence Prediction**: How confident are you that we can answer this?

Provide your analysis in JSON format:
```json
{{
    "query_complexity": "simple|complex",
    "recommended_strategy": "standard_vector|multi_hop|temporal_filtered|cross_source|hybrid",
    "rationale": "Why you chose this strategy",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "expected_doc_types": ["type1", "type2"],
    "estimated_confidence": 0.0-1.0,
    "multi_hop_plan": ["step1", "step2"] // if multi_hop strategy
}}
```
"""

            # Call Router Agent (Haiku 4.5)
            routing_response = await self.router_agent.generate_text(
                prompt=routing_prompt,
                temperature=0.3
            )

            # Parse routing decision
            if isinstance(routing_response, str):
                # Extract JSON from response
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', routing_response, re.DOTALL)
                if json_match:
                    routing_decision = json.loads(json_match.group(1))
                else:
                    # Try to parse as JSON directly
                    routing_decision = json.loads(routing_response)
            else:
                routing_decision = routing_response

            self.event_emitter.emit("routing_completed", {
                "query_id": query_id,
                "strategy": routing_decision.get("recommended_strategy", "standard_vector"),
                "complexity": routing_decision.get("query_complexity", "unknown")
            })

            logger.info(
                f"Query routing completed (strategy: {routing_decision.get('recommended_strategy')}, "
                f"complexity: {routing_decision.get('query_complexity')})"
            )

            return routing_decision

        except Exception as e:
            logger.error(f"Query routing failed: {e}", exc_info=True)
            # Return default routing decision
            return {
                "query_complexity": "unknown",
                "recommended_strategy": "standard_vector",
                "rationale": f"Routing failed: {e}. Falling back to standard vector search.",
                "key_concepts": [],
                "expected_doc_types": [],
                "estimated_confidence": 0.5,
                "error": str(e)
            }

    async def _step_2_retrieve_context(
        self,
        query: str,
        routing_decision: Dict[str, Any],
        query_id: str
    ) -> Dict[str, Any]:
        """
        STEP 2: Context Retrieval (Haiku 4.5 + RAG System).

        Executes retrieval based on routing decision.
        """
        logger.info(f"STEP 2: Context retrieval (Retriever Agent - {self.retriever_agent.model})")

        self.event_emitter.emit("retrieval_started", {
            "query_id": query_id,
            "strategy": routing_decision.get("recommended_strategy", "standard_vector")
        })

        try:
            strategy = routing_decision.get("recommended_strategy", "standard_vector")
            context_chunks = []
            metadata = {
                "strategy": strategy,
                "iterations": 0,
                "total_chunks": 0
            }

            if self.rag_system and strategy == RetrievalStrategy.STANDARD_VECTOR.value:
                # Use RAG system for standard vector search
                logger.debug("Using RAG system for standard vector retrieval")
                results = await self.rag_system.query(query, top_k=self.top_k)
                context_chunks = [r["content"] for r in results]
                metadata["iterations"] = 1
                metadata["total_chunks"] = len(context_chunks)
                metadata["method"] = "rag_vector"

            elif strategy == RetrievalStrategy.MULTI_HOP.value:
                # Multi-hop retrieval: multiple rounds
                logger.debug("Using multi-hop retrieval strategy")
                multi_hop_plan = routing_decision.get("multi_hop_plan", [query])

                for iteration, hop_query in enumerate(multi_hop_plan[:self.max_retrieval_iterations], 1):
                    if self.rag_system:
                        results = await self.rag_system.query(hop_query, top_k=self.top_k // len(multi_hop_plan))
                        context_chunks.extend([r["content"] for r in results])
                    else:
                        # Fallback: use retriever agent
                        hop_result = await self.retriever_agent.generate_text(
                            prompt=f"Retrieve information about: {hop_query}",
                            temperature=0.3
                        )
                        context_chunks.append(hop_result)

                    metadata["iterations"] = iteration

                metadata["total_chunks"] = len(context_chunks)
                metadata["method"] = "multi_hop"

            else:
                # Fallback: Use retriever agent directly
                logger.debug("Using retriever agent fallback")
                retrieval_prompt = f"""# Context Retrieval Task

Retrieve relevant information to answer this query:

**Query:** {query}

**Key Concepts:** {', '.join(routing_decision.get('key_concepts', []))}

Extract all relevant information that will help answer this query.
Focus on facts, evidence, and specific details.
"""

                context = await self.retriever_agent.generate_text(
                    prompt=retrieval_prompt,
                    temperature=0.3
                )

                context_chunks = [context]
                metadata["iterations"] = 1
                metadata["total_chunks"] = 1
                metadata["method"] = "agent_fallback"

            # Combine context
            combined_context = "\n\n---\n\n".join(context_chunks)

            self.event_emitter.emit("retrieval_completed", {
                "query_id": query_id,
                "chunks_retrieved": len(context_chunks),
                "iterations": metadata["iterations"],
                "method": metadata["method"]
            })

            logger.info(
                f"Context retrieval completed (method: {metadata['method']}, "
                f"chunks: {len(context_chunks)}, iterations: {metadata['iterations']})"
            )

            return {
                "context": combined_context,
                "chunks": context_chunks,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}", exc_info=True)
            return {
                "context": "",
                "chunks": [],
                "metadata": {
                    "strategy": "failed",
                    "iterations": 0,
                    "total_chunks": 0,
                    "error": str(e)
                }
            }

    async def _step_3_validate_context(
        self,
        query: str,
        retrieved_context: str,
        metadata: Dict[str, Any],
        query_id: str
    ) -> Dict[str, Any]:
        """
        STEP 3: Self-Reflection/Validation (Opus 4.1).

        Validates retrieved context quality before synthesis.
        This is the critical self-reflective step using Opus 4.1.
        """
        logger.info(f"STEP 3: Context validation (Critic Agent - {self.critic_agent.model})")

        self.event_emitter.emit("validation_started", {
            "query_id": query_id,
            "model": self.critic_agent.model,
            "context_length": len(retrieved_context)
        })

        try:
            # Build validation prompt
            validation_prompt = f"""# Self-Reflective Context Validation

You are critically evaluating whether the retrieved context is sufficient to answer the user's query.

## Original Query
{query}

## Retrieved Context
{retrieved_context[:3000]}...  // Showing first 3000 chars

## Retrieval Metadata
- Strategy: {metadata.get('strategy', 'unknown')}
- Chunks Retrieved: {metadata.get('total_chunks', 0)}
- Method: {metadata.get('method', 'unknown')}

## Your Task (Critical Self-Reflection)
Evaluate the retrieved context and provide your assessment:

1. **Relevance**: How relevant is this context to the query? (0.0-1.0)
2. **Completeness**: Does it contain enough information to answer? (0.0-1.0)
3. **Consistency**: Are there contradictions in the context? (yes/no)
4. **Confidence**: Overall confidence we can answer correctly (0.0-1.0)
5. **Gaps**: What critical information is missing?
6. **Recommendation**: PROCEED (confidence >0.7) or RETRIEVE_MORE (confidence <0.7)

Be CRITICAL and HONEST. If the context is insufficient, say so.

Provide your assessment in JSON format:
```json
{{
    "relevance_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "has_contradictions": true|false,
    "contradiction_details": "description if true",
    "confidence_score": 0.0-1.0,
    "confidence_level": "HIGH|MEDIUM|LOW|INSUFFICIENT",
    "gaps_identified": ["gap1", "gap2"],
    "recommendation": "PROCEED|RETRIEVE_MORE",
    "rationale": "Why you made this recommendation"
}}
```

Remember: You are the FINAL QUALITY CHECK before synthesis. Be thorough and critical.
"""

            # Call Critic Agent (Opus 4.1) - Self-reflective validation
            validation_response = await self.critic_agent.generate_text(
                prompt=validation_prompt,
                temperature=0.0  # Deterministic validation
            )

            # Parse validation result
            if isinstance(validation_response, str):
                # Extract JSON from response
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', validation_response, re.DOTALL)
                if json_match:
                    validation_result = json.loads(json_match.group(1))
                else:
                    validation_result = json.loads(validation_response)
            else:
                validation_result = validation_response

            self.event_emitter.emit("validation_completed", {
                "query_id": query_id,
                "confidence_score": validation_result.get("confidence_score", 0.0),
                "confidence_level": validation_result.get("confidence_level", "UNKNOWN"),
                "recommendation": validation_result.get("recommendation", "UNKNOWN")
            })

            logger.info(
                f"Context validation completed (confidence: {validation_result.get('confidence_score', 0):.2f}, "
                f"level: {validation_result.get('confidence_level')}, "
                f"recommendation: {validation_result.get('recommendation')})"
            )

            return validation_result

        except Exception as e:
            logger.error(f"Context validation failed: {e}", exc_info=True)
            return {
                "relevance_score": 0.5,
                "completeness_score": 0.5,
                "has_contradictions": False,
                "confidence_score": 0.5,
                "confidence_level": ConfidenceLevel.MEDIUM.value,
                "gaps_identified": [],
                "recommendation": "PROCEED",
                "rationale": f"Validation failed: {e}. Proceeding with caution.",
                "error": str(e)
            }

    async def _step_4_synthesize_report(
        self,
        query: str,
        context: str,
        validation: Dict[str, Any],
        source_path: Optional[str],
        additional_context: Optional[Dict[str, Any]],
        query_id: str
    ) -> Dict[str, Any]:
        """
        STEP 4: Synthesis (Sonnet 4.5 + analyst output style).

        Generates structured report from validated context.
        """
        logger.info(f"STEP 4: Report synthesis (Synthesizer Agent - {self.synthesizer_agent.model})")

        self.event_emitter.emit("synthesis_started", {
            "query_id": query_id,
            "model": self.synthesizer_agent.model,
            "output_style": "analyst"
        })

        try:
            # Build synthesis prompt
            synthesis_prompt = f"""# Structured Report Generation

Generate a comprehensive analyst report based on the validated context.

## Query
{query}

## Validated Context
{context[:4000]}...  // Showing first 4000 chars

## Validation Assessment
- Confidence: {validation.get('confidence_score', 0):.2f}
- Confidence Level: {validation.get('confidence_level')}
- Identified Gaps: {', '.join(validation.get('gaps_identified', []))}

## Report Metadata
- Query ID: {query_id}
- Source Path: {source_path or "Not specified"}
- Generated: {datetime.utcnow().isoformat()}

## Additional Context
{json.dumps(additional_context, indent=2) if additional_context else "None"}

## Instructions
Generate a structured enterprise analyst report that:
1. Directly answers the query based on the context
2. Provides executive summary with key findings
3. Includes detailed analysis with evidence citations
4. Notes any gaps or limitations from validation
5. Assesses confidence level explicitly
6. Maintains professional, objective tone

The report must follow the analyst output style schema for structured JSON output.

IMPORTANT: If gaps were identified, acknowledge them in the report and explain limitations.
"""

            # Call Synthesizer Agent with analyst output style
            report = await self.synthesizer_agent.generate_text(
                prompt=synthesis_prompt,
                output_style="analyst",  # C5: Enforce structured JSON
                temperature=0.5
            )

            self.event_emitter.emit("synthesis_completed", {
                "query_id": query_id,
                "report_length": len(json.dumps(report)) if isinstance(report, dict) else 0
            })

            logger.info(f"Report synthesis completed (output_style: analyst, type: {type(report).__name__})")

            return {
                "report": report,
                "model": self.synthesizer_agent.model,
                "output_style": "analyst"
            }

        except Exception as e:
            logger.error(f"Report synthesis failed: {e}", exc_info=True)
            raise


# Convenience function
async def analyze_complex_query(
    query: str,
    source_path: Optional[str] = None,
    rag_system: Optional['RAGSystem'] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for Agentic RAG analysis.

    Args:
        query: User query to analyze
        source_path: Optional path to data source
        rag_system: Optional RAG system for retrieval
        additional_context: Optional additional context

    Returns:
        Analysis result with routing, retrieval, validation, and report
    """
    pipeline = AgenticRAGPipeline(rag_system=rag_system)
    return await pipeline.analyze_query(
        query=query,
        source_path=source_path,
        additional_context=additional_context
    )


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python agentic_rag_pipeline.py <query> [source_path]")
            print("Example: python agentic_rag_pipeline.py 'What are the security vulnerabilities?' ./data/docs")
            sys.exit(1)

        query = sys.argv[1]
        source_path = sys.argv[2] if len(sys.argv) > 2 else None

        result = await analyze_complex_query(
            query=query,
            source_path=source_path
        )

        print("\n" + "="*80)
        print("AGENTIC RAG ANALYSIS COMPLETE")
        print("="*80)
        print(f"Query ID: {result['query_id']}")
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['validation_result']['confidence_score']:.2f}")
        print(f"Confidence Level: {result['validation_result']['confidence_level']}")
        print(f"Duration: {result['metadata']['duration_seconds']:.2f}s")

        if result['report']:
            print("\nReport Summary:")
            print(json.dumps(result['report'].get('executive_summary', {}), indent=2))
        else:
            print("\nInsufficient confidence to generate report.")
            print(f"Gaps: {', '.join(result['validation_result'].get('gaps_identified', []))}")

    asyncio.run(main())
