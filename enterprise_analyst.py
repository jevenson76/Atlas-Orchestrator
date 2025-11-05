#!/usr/bin/env python3
"""
Enterprise Analyst Orchestrator
Coordinates full ZTE pipeline for validated enterprise report generation.

Architecture:
- Phase B: Multi-provider infrastructure with resilient agents
- Priority 2: Closed-loop validation and refinement
- C5: Deterministic output control via analyst output style

Workflow:
1. Delegation/Retrieval: Scout Agent (Haiku 3.5) retrieves context via RAG
2. Synthesis: Master Orchestrator (Sonnet 4.5) generates report with analyst style
3. Validation: ValidationOrchestrator (Opus 4) validates with critic_judge style
4. Refinement: RefinementLoop corrects if validation fails
5. Finalization: Archive validated report
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

# Phase B: Core Infrastructure
from resilient_agent import ResilientBaseAgent
from core.constants import Models

# Priority 2: Validation and Refinement
from validation_orchestrator import ValidationOrchestrator
from refinement_loop import RefinementLoop
from validation_types import ValidationReport, Status

# RAG System (if available)
try:
    from rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAG system not available - will use basic file reading")

# Observability
from observability.event_emitter import EventEmitter

logger = logging.getLogger(__name__)


class EnterpriseAnalyst:
    """
    Enterprise Analyst Orchestrator.

    Coordinates the complete ZTE pipeline to generate validated,
    structured enterprise analyst reports from external data sources.

    Model Stack:
    - Haiku 3.5: Scout/retrieval phase (cost-efficient)
    - Sonnet 4.5: Master orchestrator + refinement
    - Opus 4: Validation/critic with strict enforcement

    Output Styles:
    - analyst: Structured JSON report (Sonnet 4.5, temp=0.5)
    - critic_judge: Strict JSON validation (Opus 4, temp=0.0)
    - refinement_feedback: Structured YAML feedback (Sonnet 4.5, temp=0.2)
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        enable_rag: bool = True,
        max_refinement_iterations: int = 3,
        min_validation_score: float = 85.0,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize Enterprise Analyst orchestrator.

        Args:
            project_root: Root directory for validation context
            enable_rag: Whether to use RAG system for retrieval
            max_refinement_iterations: Maximum refinement attempts
            min_validation_score: Minimum score for validation pass
            output_dir: Directory for archiving final reports
        """
        self.project_root = Path(project_root or ".")
        self.enable_rag = enable_rag and RAG_AVAILABLE
        self.max_refinement_iterations = max_refinement_iterations
        self.min_validation_score = min_validation_score
        self.output_dir = Path(output_dir or self.project_root / "reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Observability
        self.event_emitter = EventEmitter()

        # Initialize agents
        self._initialize_agents()

        # Initialize RAG system if enabled
        self.rag_system = None
        if self.enable_rag:
            try:
                self.rag_system = RAGSystem()
                logger.info("RAG system initialized for context retrieval")
            except Exception as e:
                logger.warning(f"Failed to initialize RAG system: {e}")
                self.rag_system = None

        logger.info(
            f"EnterpriseAnalyst initialized (RAG: {self.enable_rag}, "
            f"max_iterations: {max_refinement_iterations}, "
            f"min_score: {min_validation_score})"
        )

    def _initialize_agents(self):
        """Initialize all agents in the pipeline."""
        # STEP 1: Scout Agent (Haiku 3.5) - Fast retrieval
        self.scout_agent = ResilientBaseAgent(
            role="Enterprise data scout and context retrieval specialist",
            model=Models.HAIKU,
            temperature=0.3,
            max_tokens=2000
        )
        logger.info(f"Scout Agent initialized: {self.scout_agent.model}")

        # STEP 2: Master Orchestrator (Sonnet 4.5) - Report generation
        self.master_agent = ResilientBaseAgent(
            role="Enterprise analyst report generation specialist",
            model=Models.SONNET,
            temperature=0.5,
            max_tokens=4000
        )
        logger.info(f"Master Agent initialized: {self.master_agent.model}")

        # STEP 3: Validation Orchestrator (Opus 4 + critic_judge)
        self.validator = ValidationOrchestrator(
            project_root=str(self.project_root)
        )
        logger.info("Validation Orchestrator initialized (critic_judge enabled)")

        # STEP 4: Refinement Loop (with structured feedback)
        self.refinement_agent = ResilientBaseAgent(
            role="Structured feedback extraction and refinement specialist",
            model=Models.SONNET,
            temperature=0.2,
            max_tokens=3000
        )
        self.refinement_loop = RefinementLoop(
            max_iterations=self.max_refinement_iterations,
            min_score_threshold=self.min_validation_score,
            agent=self.refinement_agent
        )
        logger.info(
            f"Refinement Loop initialized (max_iterations: {self.max_refinement_iterations}, "
            f"refinement_feedback enabled)"
        )

    async def generate_report(
        self,
        source_path: str,
        query: str,
        analyst_name: str = "Claude Enterprise Analyst",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a validated enterprise analyst report.

        Executes the complete 5-step ZTE pipeline:
        1. Retrieval: Scout Agent gathers context from source
        2. Synthesis: Master Agent generates report with analyst output style
        3. Validation: ValidationOrchestrator validates with critic_judge
        4. Refinement: RefinementLoop corrects if validation fails
        5. Finalization: Archive validated report

        Args:
            source_path: Path to data source (file, directory, or URL)
            query: Analysis query/objective
            analyst_name: Name of analyst for report metadata
            additional_context: Optional additional context

        Returns:
            Dict with:
                - report_id: Unique report identifier
                - report: Validated analyst report (JSON)
                - validation_report: Final validation results
                - metadata: Execution metadata (timing, iterations, etc.)
                - archive_path: Path to archived report
        """
        report_id = str(uuid4())
        start_time = datetime.utcnow()

        logger.info(
            f"Starting report generation (report_id: {report_id}, "
            f"query: {query[:50]}..., source: {source_path})"
        )

        self.event_emitter.emit("report_generation_started", {
            "report_id": report_id,
            "query": query,
            "source_path": source_path,
            "timestamp": start_time.isoformat()
        })

        try:
            # STEP 1: Retrieval (Scout Agent - Haiku 3.5)
            retrieval_result = await self._step_1_retrieve_context(
                source_path=source_path,
                query=query,
                report_id=report_id
            )

            # STEP 2: Synthesis (Master Agent - analyst output style)
            generation_result = await self._step_2_generate_report(
                query=query,
                context=retrieval_result["context"],
                source_path=source_path,
                analyst_name=analyst_name,
                report_id=report_id,
                additional_context=additional_context
            )

            # STEP 3: Validation (Opus 4 - critic_judge output style)
            validation_report = await self._step_3_validate_report(
                report=generation_result["report"],
                report_id=report_id
            )

            # STEP 4: Refinement (if validation fails)
            refinement_result = None
            if not validation_report.passed:
                logger.info(
                    f"Report validation failed (score: {validation_report.average_score:.1f}), "
                    f"triggering refinement loop"
                )
                refinement_result = await self._step_4_refine_report(
                    initial_report=generation_result["report"],
                    validation_report=validation_report,
                    query=query,
                    context=retrieval_result["context"],
                    source_path=source_path,
                    analyst_name=analyst_name,
                    report_id=report_id
                )

                # Use refined report and validation
                generation_result = refinement_result["generation_result"]
                validation_report = refinement_result["validation_report"]

            # STEP 5: Finalization (archive if passed)
            archive_path = None
            if validation_report.passed:
                archive_path = await self._step_5_finalize_report(
                    report=generation_result["report"],
                    validation_report=validation_report,
                    report_id=report_id
                )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Build response
            response = {
                "report_id": report_id,
                "status": "success" if validation_report.passed else "failed_validation",
                "report": generation_result["report"],
                "validation_report": validation_report.to_dict(),
                "metadata": {
                    "query": query,
                    "source_path": source_path,
                    "analyst_name": analyst_name,
                    "duration_seconds": duration,
                    "retrieval_model": self.scout_agent.model,
                    "generation_model": self.master_agent.model,
                    "validation_model": Models.OPUS,
                    "output_style": "analyst",
                    "refinement_iterations": refinement_result["iterations"] if refinement_result else 0,
                    "final_validation_score": validation_report.average_score,
                    "started_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat()
                },
                "archive_path": str(archive_path) if archive_path else None
            }

            self.event_emitter.emit("report_generation_completed", {
                "report_id": report_id,
                "status": response["status"],
                "duration_seconds": duration,
                "validation_score": validation_report.average_score
            })

            logger.info(
                f"Report generation completed (report_id: {report_id}, "
                f"status: {response['status']}, duration: {duration:.2f}s, "
                f"score: {validation_report.average_score:.1f})"
            )

            return response

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            self.event_emitter.emit("report_generation_failed", {
                "report_id": report_id,
                "error": str(e)
            })
            raise

    async def _step_1_retrieve_context(
        self,
        source_path: str,
        query: str,
        report_id: str
    ) -> Dict[str, Any]:
        """
        STEP 1: Retrieve context using Scout Agent (Haiku 3.5).

        Uses RAG system if available, otherwise reads files directly.
        """
        logger.info(f"STEP 1: Context retrieval (Scout Agent - {self.scout_agent.model})")

        self.event_emitter.emit("retrieval_started", {
            "report_id": report_id,
            "source_path": source_path
        })

        try:
            # If RAG system available, use it
            if self.rag_system:
                logger.debug("Using RAG system for context retrieval")
                # Query RAG system for relevant context
                rag_results = await self.rag_system.query(query, top_k=10)
                context_chunks = [result["content"] for result in rag_results]
                context = "\n\n---\n\n".join(context_chunks)

                retrieval_result = {
                    "context": context,
                    "source_count": len(rag_results),
                    "retrieval_method": "rag",
                    "metadata": {
                        "top_k": 10,
                        "sources": [r.get("metadata", {}) for r in rag_results]
                    }
                }
            else:
                # Fallback: Read files directly using Scout Agent
                logger.debug("RAG unavailable, using direct file reading")

                # Build retrieval prompt
                retrieval_prompt = f"""# Context Retrieval Task

You are a data scout retrieving relevant information from the specified source.

**Source Path:** {source_path}
**Analysis Query:** {query}

**Your Task:**
1. Read the source path (file or directory)
2. Extract all relevant information related to the query
3. Organize the information into clear, structured sections
4. Preserve important details, quotes, and evidence
5. Return the organized context

Focus on retrieving comprehensive, relevant information that will support a detailed enterprise analyst report.
"""

                # Call Scout Agent (Haiku 3.5) - no output style for retrieval
                context = await self.scout_agent.generate_text(
                    prompt=retrieval_prompt,
                    temperature=0.3
                )

                retrieval_result = {
                    "context": context,
                    "source_count": 1,
                    "retrieval_method": "direct",
                    "metadata": {
                        "source_path": source_path
                    }
                }

            self.event_emitter.emit("retrieval_completed", {
                "report_id": report_id,
                "context_length": len(retrieval_result["context"]),
                "source_count": retrieval_result["source_count"],
                "method": retrieval_result["retrieval_method"]
            })

            logger.info(
                f"Context retrieval completed (method: {retrieval_result['retrieval_method']}, "
                f"sources: {retrieval_result['source_count']}, "
                f"context_length: {len(retrieval_result['context'])} chars)"
            )

            return retrieval_result

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}", exc_info=True)
            raise

    async def _step_2_generate_report(
        self,
        query: str,
        context: str,
        source_path: str,
        analyst_name: str,
        report_id: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        STEP 2: Generate report using Master Agent (Sonnet 4.5) with analyst output style.
        """
        logger.info(f"STEP 2: Report generation (Master Agent - {self.master_agent.model})")

        self.event_emitter.emit("generation_started", {
            "report_id": report_id,
            "model": self.master_agent.model,
            "output_style": "analyst"
        })

        try:
            # Build generation prompt
            generation_prompt = f"""# Enterprise Analyst Report Generation

You are generating a comprehensive enterprise analyst report based on retrieved context.

## Query/Objective
{query}

## Source Path
{source_path}

## Retrieved Context
{context}

## Report Metadata
- Report ID: {report_id}
- Analyst: {analyst_name}
- Generated: {datetime.utcnow().isoformat()}

## Additional Context
{json.dumps(additional_context, indent=2) if additional_context else "None"}

## Instructions
Generate a comprehensive enterprise analyst report that:
1. Provides an executive summary with key findings
2. Includes detailed analysis organized by categories
3. Cites evidence from the retrieved context
4. Offers actionable recommendations with implementation details
5. Assesses risk levels and compliance status
6. Maintains professional, objective tone

The report must follow the analyst output style schema for structured JSON output.
"""

            # Call Master Agent with analyst output style
            report = await self.master_agent.generate_text(
                prompt=generation_prompt,
                output_style="analyst",  # C5: Enforce structured JSON
                temperature=0.5
            )

            self.event_emitter.emit("generation_completed", {
                "report_id": report_id,
                "report_length": len(json.dumps(report)) if isinstance(report, dict) else 0
            })

            logger.info(
                f"Report generation completed (output_style: analyst, "
                f"type: {type(report).__name__})"
            )

            return {
                "report": report,
                "model": self.master_agent.model,
                "output_style": "analyst"
            }

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            raise

    async def _step_3_validate_report(
        self,
        report: Dict[str, Any],
        report_id: str
    ) -> ValidationReport:
        """
        STEP 3: Validate report using ValidationOrchestrator (Opus 4 + critic_judge).
        """
        logger.info("STEP 3: Report validation (Opus 4 - critic_judge output style)")

        self.event_emitter.emit("validation_started", {
            "report_id": report_id,
            "validator": "ValidationOrchestrator",
            "output_style": "critic_judge"
        })

        try:
            # Convert report to JSON string for validation
            report_json = json.dumps(report, indent=2)

            # Validate using code validator (treats JSON as code)
            validation_report = await self.validator.validate_code(
                code=report_json,
                language="json",
                context={
                    "report_id": report_id,
                    "validation_type": "analyst_report",
                    "schema": "analyst_output_style"
                }
            )

            self.event_emitter.emit("validation_completed", {
                "report_id": report_id,
                "status": validation_report.overall_status,
                "score": validation_report.average_score,
                "critical_issues": validation_report.critical_count
            })

            logger.info(
                f"Report validation completed (status: {validation_report.overall_status}, "
                f"score: {validation_report.average_score:.1f}, "
                f"critical: {validation_report.critical_count}, "
                f"high: {validation_report.high_count})"
            )

            return validation_report

        except Exception as e:
            logger.error(f"Report validation failed: {e}", exc_info=True)
            raise

    async def _step_4_refine_report(
        self,
        initial_report: Dict[str, Any],
        validation_report: ValidationReport,
        query: str,
        context: str,
        source_path: str,
        analyst_name: str,
        report_id: str
    ) -> Dict[str, Any]:
        """
        STEP 4: Refine report using RefinementLoop (refinement_feedback output style).
        """
        logger.info(
            f"STEP 4: Report refinement (RefinementLoop - refinement_feedback output style, "
            f"max_iterations: {self.max_refinement_iterations})"
        )

        self.event_emitter.emit("refinement_started", {
            "report_id": report_id,
            "initial_score": validation_report.average_score,
            "max_iterations": self.max_refinement_iterations
        })

        try:
            # Prepare input for refinement loop
            refinement_input = {
                "task": f"Generate enterprise analyst report for: {query}",
                "source_path": source_path,
                "analyst_name": analyst_name,
                "report_id": report_id,
                "context": context
            }

            # Define generation function for refinement loop
            async def generate_fn(input_data: Dict[str, Any]) -> Any:
                """Generation function called by refinement loop."""
                return await self._step_2_generate_report(
                    query=input_data["task"],
                    context=input_data["context"],
                    source_path=input_data["source_path"],
                    analyst_name=input_data["analyst_name"],
                    report_id=input_data["report_id"]
                )

            # Define validation function for refinement loop
            async def validate_fn(output: Any) -> ValidationReport:
                """Validation function called by refinement loop."""
                report_data = output["report"] if isinstance(output, dict) and "report" in output else output
                return await self._step_3_validate_report(
                    report=report_data,
                    report_id=report_id
                )

            # Execute refinement loop
            refinement_result = await self.refinement_loop.refine(
                generate_fn=generate_fn,
                validate_fn=validate_fn,
                initial_input=refinement_input,
                initial_output={"report": initial_report},
                initial_validation=validation_report
            )

            self.event_emitter.emit("refinement_completed", {
                "report_id": report_id,
                "iterations": refinement_result["iterations"],
                "final_score": refinement_result["final_validation"].average_score,
                "success": refinement_result["final_validation"].passed
            })

            logger.info(
                f"Report refinement completed (iterations: {refinement_result['iterations']}, "
                f"final_score: {refinement_result['final_validation'].average_score:.1f}, "
                f"success: {refinement_result['final_validation'].passed})"
            )

            return {
                "generation_result": refinement_result["final_output"],
                "validation_report": refinement_result["final_validation"],
                "iterations": refinement_result["iterations"],
                "history": refinement_result.get("history", [])
            }

        except Exception as e:
            logger.error(f"Report refinement failed: {e}", exc_info=True)
            raise

    async def _step_5_finalize_report(
        self,
        report: Dict[str, Any],
        validation_report: ValidationReport,
        report_id: str
    ) -> Path:
        """
        STEP 5: Finalize and archive validated report.
        """
        logger.info("STEP 5: Report finalization and archiving")

        self.event_emitter.emit("finalization_started", {
            "report_id": report_id
        })

        try:
            # Create archive filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archive_filename = f"analyst_report_{report_id}_{timestamp}.json"
            archive_path = self.output_dir / archive_filename

            # Build archive package
            archive_data = {
                "report_id": report_id,
                "report": report,
                "validation": validation_report.to_dict(),
                "metadata": {
                    "archived_at": datetime.utcnow().isoformat(),
                    "validation_passed": validation_report.passed,
                    "validation_score": validation_report.average_score
                }
            }

            # Write to file
            with open(archive_path, 'w') as f:
                json.dump(archive_data, f, indent=2)

            self.event_emitter.emit("finalization_completed", {
                "report_id": report_id,
                "archive_path": str(archive_path),
                "file_size": archive_path.stat().st_size
            })

            logger.info(f"Report archived successfully: {archive_path}")

            return archive_path

        except Exception as e:
            logger.error(f"Report finalization failed: {e}", exc_info=True)
            raise


# Convenience function
async def generate_analyst_report(
    source_path: str,
    query: str,
    analyst_name: str = "Claude Enterprise Analyst",
    project_root: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate an analyst report.

    Args:
        source_path: Path to data source
        query: Analysis query/objective
        analyst_name: Name of analyst for report metadata
        project_root: Root directory for validation context
        output_dir: Directory for archiving reports

    Returns:
        Report generation result with report, validation, and metadata
    """
    analyst = EnterpriseAnalyst(
        project_root=project_root,
        output_dir=output_dir
    )

    return await analyst.generate_report(
        source_path=source_path,
        query=query,
        analyst_name=analyst_name
    )


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        if len(sys.argv) < 3:
            print("Usage: python enterprise_analyst.py <source_path> <query>")
            print("Example: python enterprise_analyst.py ./data/docs 'Analyze security compliance'")
            sys.exit(1)

        source_path = sys.argv[1]
        query = sys.argv[2]

        result = await generate_analyst_report(
            source_path=source_path,
            query=query
        )

        print("\n" + "="*80)
        print("ANALYST REPORT GENERATION COMPLETE")
        print("="*80)
        print(f"Report ID: {result['report_id']}")
        print(f"Status: {result['status']}")
        print(f"Validation Score: {result['validation_report']['average_score']:.1f}/100")
        print(f"Duration: {result['metadata']['duration_seconds']:.2f}s")
        if result['archive_path']:
            print(f"Archive: {result['archive_path']}")
        print("\nReport Summary:")
        print(json.dumps(result['report'].get('executive_summary', {}), indent=2))

    asyncio.run(main())
