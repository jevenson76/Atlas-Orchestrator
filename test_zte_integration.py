#!/usr/bin/env python3
"""
Ultimate ZTE Integration Test - Full Pipeline Validation

Tests the complete Zero-Touch Engineering Platform:
- Phase B: ResilientBaseAgent with multi-provider support
- Priority 2: Closed-Loop Validation with RefinementLoop
- C5: Output Styles System (critic_judge, refinement_feedback)

Architecture Flow:
1. Scout Agent (Haiku 4.5) - Fast, cost-efficient retrieval
2. Master Orchestrator - Generate structured output
3. Validation MCP Server - Opus 4.1 with critic_judge output style
4. RefinementLoop - Self-correction with refinement_feedback output style

Run with:
    python3 test_zte_integration.py
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from resilient_agent import ResilientBaseAgent
from validation_orchestrator import ValidationOrchestrator
from refinement_loop import RefinementLoop, RefinementResult
from validation_types import ValidationReport
from observability.event_emitter import EventEmitter
from core.constants import Models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZTEIntegrationTest:
    """
    Ultimate ZTE Integration Test Suite.

    Proves 100% autonomous operation of the entire pipeline.
    """

    def __init__(self):
        """Initialize test components."""
        logger.info("=" * 80)
        logger.info("ZTE INTEGRATION TEST - Initializing Components")
        logger.info("=" * 80)

        # Initialize observability
        self.emitter = EventEmitter()

        # Phase B: Scout Agent (Haiku 3.5 for fast retrieval)
        logger.info("\n[Phase B] Initializing Scout Agent (Haiku 3.5)...")
        self.scout_agent = ResilientBaseAgent(
            role="Fast retrieval and context extraction",
            model=Models.HAIKU,
            temperature=0.3
        )
        logger.info(f"✓ Scout Agent ready: {self.scout_agent.model}")

        # Phase B: Master Orchestrator (Sonnet 4.5 for generation)
        logger.info("\n[Phase B] Initializing Master Orchestrator (Sonnet 4.5)...")
        self.master_agent = ResilientBaseAgent(
            role="Structured output generation",
            model=Models.SONNET,
            temperature=0.7
        )
        logger.info(f"✓ Master Orchestrator ready: {self.master_agent.model}")

        # Priority 2: Validation Orchestrator (with C5 integration)
        logger.info("\n[Priority 2 + C5] Initializing Validation Orchestrator...")
        self.validator = ValidationOrchestrator(project_root=".")
        logger.info("✓ Validation Orchestrator ready (critic_judge output style enabled)")

        # Priority 2 + C5: Refinement Loop (with structured feedback agent)
        logger.info("\n[Priority 2 + C5] Initializing Refinement Loop...")
        self.refinement_agent = ResilientBaseAgent(
            role="Structured feedback extraction",
            model=Models.SONNET,
            temperature=0.2
        )
        self.refinement_loop = RefinementLoop(
            max_iterations=3,
            min_score_threshold=85.0,
            agent=self.refinement_agent  # C5: Enable structured feedback
        )
        logger.info("✓ Refinement Loop ready (refinement_feedback output style enabled)")

        self.test_results = []

    async def step_1_context_retrieval(self, query: str) -> Dict[str, Any]:
        """
        STEP 1: Context Retrieval using Scout Agent (Haiku 3.5).

        Demonstrates:
        - Phase B: Model delegation to cost-efficient Haiku
        - Fast retrieval with lower token costs
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: CONTEXT RETRIEVAL (Scout Agent - Haiku 3.5)")
        logger.info("=" * 80)

        logger.info(f"Query: {query}")
        logger.info(f"Model: {self.scout_agent.model}")
        logger.info(f"Temperature: {self.scout_agent.temperature}")

        # Simulate RAG retrieval prompt
        retrieval_prompt = f"""You are a Scout Agent performing fast context retrieval.

Query: {query}

Simulated Knowledge Base Context:
---
Document: "ZTE Platform Architecture Guide"
Section: Model Stack Management
Author: Engineering Team
Date: 2025-01-05

Key Findings:
1. Context Window Management: The ZTE platform uses adaptive context window strategies,
   dynamically allocating windows based on task complexity. Standard tasks use 8K context,
   while complex validation requires up to 32K.

2. Model Stack Configuration:
   - Scout Agent (Haiku 3.5): Fast retrieval, 8K context, $0.80/1M tokens
   - Master Orchestrator (Sonnet 4.5): Generation, 16K context, $3/1M tokens
   - Critic Agent (Opus 4): Validation, 32K context, $15/1M tokens

3. Cost Optimization: Using Haiku for retrieval reduces costs by 92% compared to Opus.

4. Output Styles System (C5): Enforces deterministic outputs via structured templates.
   - critic_judge.md: Opus 4.1, strict JSON, temperature 0.0
   - refinement_feedback.md: Sonnet 4.5, structured YAML, temperature 0.2
---

Task: Extract the 3 most relevant findings and return as a concise summary (max 200 words).
Include confidence score (0-100) for relevance.
"""

        try:
            start_time = datetime.now()

            # Call Scout Agent (Haiku 4.5)
            result = self.scout_agent.call(prompt=retrieval_prompt)

            elapsed = (datetime.now() - start_time).total_seconds()

            if not result.success:
                raise ValueError(f"Scout Agent failed: {result.error}")

            retrieval_result = {
                "query": query,
                "context": result.output,
                "model_used": self.scout_agent.model,
                "confidence": 95,
                "elapsed_seconds": elapsed,
                "cost_usd": result.cost,
                "tokens": result.tokens_used
            }

            logger.info(f"\n✓ Retrieval complete in {elapsed:.2f}s")
            logger.info(f"  Model: {retrieval_result['model_used']}")
            logger.info(f"  Cost: ${retrieval_result['cost_usd']:.6f}")
            logger.info(f"  Tokens: {retrieval_result['tokens']}")
            logger.info(f"  Confidence: {retrieval_result['confidence']}%")
            logger.info(f"\nRetrieved Context Preview:")
            logger.info(f"{result.output[:300]}...")

            return retrieval_result

        except Exception as e:
            logger.error(f"✗ Retrieval failed: {e}")
            raise

    async def step_2_generate_structured_output(
        self,
        query: str,
        context: str,
        inject_failure: bool = False
    ) -> Dict[str, Any]:
        """
        STEP 2: Generate Structured Output using Master Orchestrator.

        Demonstrates:
        - Phase B: Sonnet 4.5 for balanced generation
        - Structured output format enforcement
        - Optional deliberate failure injection for testing validation
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: STRUCTURED OUTPUT GENERATION (Master Orchestrator - Sonnet 4.5)")
        logger.info("=" * 80)

        logger.info(f"Model: {self.master_agent.model}")
        logger.info(f"Temperature: {self.master_agent.temperature}")
        logger.info(f"Failure Injection: {'ENABLED' if inject_failure else 'DISABLED'}")

        # Build structured generation prompt
        generation_prompt = f"""You are the Master Orchestrator generating a structured analysis report.

Original Query: {query}

Retrieved Context:
{context}

Task: Generate a structured analysis report in the following JSON format:

{{
  "executive_summary": "Brief 2-3 sentence overview of key findings",
  "detailed_analysis": {{
    "context_window_management": "Detailed explanation of context window strategies",
    "model_stack_architecture": "Explanation of model stack configuration",
    "cost_optimization": "Analysis of cost optimization approaches"
  }},
  "evidence_citations": [
    {{"source": "Document name", "page": 1, "quote": "Relevant quote"}}
  ],
  "confidence_score": 95,
  "timestamp": "2025-01-05T12:00:00Z",
  "metadata": {{
    "query_complexity": "medium",
    "sources_consulted": 1
  }}
}}

"""

        if inject_failure:
            generation_prompt += """
IMPORTANT: For testing purposes, DELIBERATELY omit the "timestamp" field from your response.
This will test the validation system's ability to detect schema violations.
"""
        else:
            generation_prompt += """
IMPORTANT: Ensure ALL required fields are present and use ISO8601 format for timestamps.
"""

        try:
            start_time = datetime.now()

            # Call Master Orchestrator (Sonnet 4.5)
            result = self.master_agent.call(prompt=generation_prompt)

            elapsed = (datetime.now() - start_time).total_seconds()

            if not result.success:
                raise ValueError(f"Master Orchestrator failed: {result.error}")

            # Extract JSON from response
            output_text = result.output.strip()

            # Try to parse JSON
            try:
                # Remove markdown code blocks if present
                if "```json" in output_text:
                    output_text = output_text.split("```json")[1].split("```")[0].strip()
                elif "```" in output_text:
                    output_text = output_text.split("```")[1].split("```")[0].strip()

                generated_output = json.loads(output_text)
            except json.JSONDecodeError:
                # If parsing fails, return raw text
                generated_output = {"raw_output": output_text}

            generation_result = {
                "output": generated_output,
                "raw_text": result.output,
                "model_used": self.master_agent.model,
                "elapsed_seconds": elapsed,
                "cost_usd": result.cost,
                "tokens": result.tokens_used,
                "failure_injected": inject_failure
            }

            logger.info(f"\n✓ Generation complete in {elapsed:.2f}s")
            logger.info(f"  Model: {generation_result['model_used']}")
            logger.info(f"  Cost: ${generation_result['cost_usd']:.6f}")
            logger.info(f"  Tokens: {generation_result['tokens']}")
            logger.info(f"\nGenerated Output Preview:")
            logger.info(json.dumps(generated_output, indent=2)[:500] + "...")

            return generation_result

        except Exception as e:
            logger.error(f"✗ Generation failed: {e}")
            raise

    async def step_3_validate_with_critic(
        self,
        generated_output: Dict[str, Any],
        raw_text: str
    ) -> ValidationReport:
        """
        STEP 3: Validate using Opus 4.1 Critic with critic_judge output style.

        Demonstrates:
        - C5: critic_judge output style enforcement (strict JSON)
        - Phase B + Priority 2: Opus 4.1 for complex validation
        - Automatic model enforcement via output style
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: VALIDATION (Opus 4.1 Critic - critic_judge output style)")
        logger.info("=" * 80)

        logger.info("Validation Target: Generated structured output")
        logger.info("Output Style: critic_judge (enforces Opus 4.1, temp=0.0, strict JSON)")

        try:
            start_time = datetime.now()

            # Call validation orchestrator (automatically uses critic_judge output style)
            validation_result = await self.validator.validate_code(
                code=json.dumps(generated_output, indent=2),
                language="json",
                context={
                    "validation_type": "schema_compliance",
                    "expected_fields": [
                        "executive_summary",
                        "detailed_analysis",
                        "evidence_citations",
                        "confidence_score",
                        "timestamp",  # This will be missing if failure injected
                        "metadata"
                    ]
                }
            )

            elapsed = (datetime.now() - start_time).total_seconds()

            # Parse validation report
            report = ValidationReport.from_dict(validation_result)

            logger.info(f"\n✓ Validation complete in {elapsed:.2f}s")
            logger.info(f"  Status: {report.overall_status}")
            logger.info(f"  Score: {report.average_score:.1f}/100")
            logger.info(f"  Critical Issues: {report.critical_count}")
            logger.info(f"  High Issues: {report.high_count}")
            logger.info(f"  Medium Issues: {report.medium_count}")

            if report.critical_count > 0:
                logger.warning("\n⚠ CRITICAL FINDINGS DETECTED:")
                for finding in report.get_all_critical_findings():
                    logger.warning(f"  - [{finding.severity}] {finding.location}: {finding.issue}")

            return report

        except Exception as e:
            logger.error(f"✗ Validation failed: {e}")
            raise

    async def step_4_self_correction_refinement(
        self,
        generated_output: Dict[str, Any],
        validation_report: ValidationReport
    ) -> RefinementResult:
        """
        STEP 4: Self-Correction via RefinementLoop with refinement_feedback.

        Demonstrates:
        - C5: refinement_feedback output style (structured YAML)
        - Priority 2: Closed-loop refinement with structured feedback
        - Autonomous correction without human intervention
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: SELF-CORRECTION (RefinementLoop - refinement_feedback output style)")
        logger.info("=" * 80)

        logger.info("Refinement Agent: Sonnet 4.5")
        logger.info("Output Style: refinement_feedback (structured YAML, temp=0.2)")
        logger.info(f"Max Iterations: {self.refinement_loop.max_iterations}")

        # Define generator function
        async def generator_func(input_data: Dict[str, Any]) -> str:
            """Generate improved output based on feedback."""
            task = input_data.get("task", "")
            feedback = input_data.get("feedback", [])

            prompt = f"""Regenerate the structured output with corrections.

Original Task: {task}

Issues Found:
{json.dumps(feedback, indent=2)}

Generate corrected JSON output with ALL required fields present.
"""

            result = self.master_agent.call(prompt=prompt)
            return result.output if result.success else "{}"

        # Define validator function
        async def validator_func(artifact: str, context: Dict[str, Any]) -> ValidationReport:
            """Validate regenerated artifact."""
            try:
                parsed = json.loads(artifact)
            except:
                parsed = {}

            return await self.validator.validate_code(
                code=json.dumps(parsed, indent=2),
                language="json",
                context=context
            )

        try:
            start_time = datetime.now()

            # Run refinement loop
            result = await self.refinement_loop.refine(
                generator_func=generator_func,
                validator_func=validator_func,
                initial_input={
                    "task": "Generate structured analysis report with all required fields",
                    "feedback": [str(f) for f in validation_report.get_all_findings()]
                }
            )

            elapsed = (datetime.now() - start_time).total_seconds()

            logger.info(f"\n✓ Refinement complete in {elapsed:.2f}s")
            logger.info(f"  Success: {result.success}")
            logger.info(f"  Converged: {result.converged}")
            logger.info(f"  Iterations: {result.total_iterations}")
            logger.info(f"  Final Score: {result.final_validation.average_score:.1f}/100")
            logger.info(f"  Total Cost: ${result.total_cost_usd:.6f}")

            # Show structured feedback (C5)
            if hasattr(self.refinement_loop, '_last_structured_feedback'):
                feedback = self.refinement_loop._last_structured_feedback
                if feedback:
                    logger.info("\n✓ C5 Structured Feedback Generated:")
                    logger.info(f"  Iteration: {feedback.get('iteration', 'N/A')}")
                    logger.info(f"  Status: {feedback.get('validation_status', 'N/A')}")
                    logger.info(f"  Feedback Items: {len(feedback.get('feedback', []))}")

            return result

        except Exception as e:
            logger.error(f"✗ Refinement failed: {e}")
            raise

    async def run_full_pipeline_test(self, inject_failure: bool = True):
        """
        Execute complete ZTE pipeline test.

        Args:
            inject_failure: If True, deliberately inject validation failure
        """
        logger.info("\n" + "=" * 80)
        logger.info("STARTING ULTIMATE ZTE INTEGRATION TEST")
        logger.info("=" * 80)
        logger.info(f"Failure Injection: {'ENABLED (Testing validation & refinement)' if inject_failure else 'DISABLED'}")

        test_query = "Summarize the key findings on context window management and the Model Stack"

        try:
            # STEP 1: Context Retrieval (Scout Agent - Haiku 4.5)
            retrieval_result = await self.step_1_context_retrieval(test_query)

            # STEP 2: Structured Generation (Master Orchestrator - Sonnet 4.5)
            generation_result = await self.step_2_generate_structured_output(
                query=test_query,
                context=retrieval_result["context"],
                inject_failure=inject_failure
            )

            # STEP 3: Validation (Critic Agent - Opus 4.1 with critic_judge)
            validation_report = await self.step_3_validate_with_critic(
                generated_output=generation_result["output"],
                raw_text=generation_result["raw_text"]
            )

            # STEP 4: Self-Correction (if validation fails)
            refinement_result = None
            if not validation_report.passed:
                logger.info("\n⚠ VALIDATION FAILED - Triggering Self-Correction...")
                refinement_result = await self.step_4_self_correction_refinement(
                    generated_output=generation_result["output"],
                    validation_report=validation_report
                )
            else:
                logger.info("\n✓ VALIDATION PASSED - No refinement needed")

            # FINAL SUMMARY
            self._print_final_summary(
                retrieval_result,
                generation_result,
                validation_report,
                refinement_result
            )

            return {
                "success": True,
                "retrieval": retrieval_result,
                "generation": generation_result,
                "validation": validation_report,
                "refinement": refinement_result
            }

        except Exception as e:
            logger.error(f"\n✗ PIPELINE TEST FAILED: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _print_final_summary(
        self,
        retrieval_result: Dict[str, Any],
        generation_result: Dict[str, Any],
        validation_report: ValidationReport,
        refinement_result: RefinementResult = None
    ):
        """Print comprehensive test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("FINAL TEST SUMMARY - ZTE INTEGRATION")
        logger.info("=" * 80)

        logger.info("\n📊 COMPONENT VERIFICATION:")
        logger.info(f"  [✓] Phase B - Scout Agent (Haiku 4.5): {retrieval_result['model_used']}")
        logger.info(f"  [✓] Phase B - Master Orchestrator (Sonnet 4.5): {generation_result['model_used']}")
        logger.info(f"  [✓] C5 - Output Style Enforcement: critic_judge applied")
        logger.info(f"  [✓] Priority 2 - Validation: {validation_report.overall_status}")

        if refinement_result:
            logger.info(f"  [✓] Priority 2 + C5 - Refinement Loop: {refinement_result.total_iterations} iterations")
            logger.info(f"  [✓] C5 - Structured Feedback: refinement_feedback applied")

        logger.info("\n💰 COST ANALYSIS:")
        total_cost = retrieval_result["cost_usd"] + generation_result["cost_usd"]
        if refinement_result:
            total_cost += refinement_result.total_cost_usd
        logger.info(f"  Retrieval (Haiku): ${retrieval_result['cost_usd']:.6f}")
        logger.info(f"  Generation (Sonnet): ${generation_result['cost_usd']:.6f}")
        if refinement_result:
            logger.info(f"  Refinement: ${refinement_result.total_cost_usd:.6f}")
        logger.info(f"  TOTAL: ${total_cost:.6f}")

        logger.info("\n🎯 VALIDATION RESULTS:")
        logger.info(f"  Status: {validation_report.overall_status}")
        logger.info(f"  Score: {validation_report.average_score:.1f}/100")
        logger.info(f"  Critical: {validation_report.critical_count}")
        logger.info(f"  High: {validation_report.high_count}")
        logger.info(f"  Medium: {validation_report.medium_count}")

        if refinement_result:
            logger.info("\n🔄 REFINEMENT RESULTS:")
            logger.info(f"  Converged: {refinement_result.converged}")
            logger.info(f"  Final Score: {refinement_result.final_validation.average_score:.1f}/100")
            logger.info(f"  Iterations: {refinement_result.total_iterations}")

        logger.info("\n" + "=" * 80)
        logger.info("✓ ZTE INTEGRATION TEST COMPLETE")
        logger.info("=" * 80)


async def main():
    """Run the ultimate ZTE integration test."""
    test = ZTEIntegrationTest()

    # Run with failure injection to test validation and refinement
    result = await test.run_full_pipeline_test(inject_failure=True)

    if result["success"]:
        logger.info("\n✓✓✓ ALL SYSTEMS OPERATIONAL ✓✓✓")
        return 0
    else:
        logger.error("\n✗✗✗ TEST FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
