#!/usr/bin/env python3
"""
Workflow Orchestration MCP Server - Multi-Agent Workflows via MCP

Exposes Priority 3 multi-agent workflows through MCP tools:
- Auto-routing to optimal workflow (MasterOrchestrator)
- Explicit workflow selection (Parallel, Progressive, Specialized)
- Workflow recommendations

Resources:
- Available workflows catalog
- Workflow performance metrics

Usage:
    python3 workflow_orchestration_server.py
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.base_server import BaseMCPServer, ToolParameter
from multi_ai_workflow import MasterOrchestrator
from parallel_development_orchestrator import ParallelDevelopmentOrchestrator
from progressive_enhancement_orchestrator import ProgressiveEnhancementOrchestrator
from specialized_roles_orchestrator import SpecializedRolesOrchestrator
from validation_orchestrator import ValidationOrchestrator
from refinement_loop import RefinementLoop

logger = logging.getLogger(__name__)


class WorkflowOrchestrationServer(BaseMCPServer):
    """
    MCP server providing multi-agent workflow orchestration.

    Tools:
    - execute_workflow: Auto-route to optimal workflow
    - parallel_workflow: Explicit parallel development
    - progressive_workflow: Explicit progressive enhancement
    - specialized_workflow: Explicit specialized roles
    - get_workflow_recommendation: Recommend workflow for task

    Resources:
    - workflows://available: Catalog of workflows
    - workflows://metrics: Performance metrics per workflow
    """

    def __init__(self):
        """Initialize workflow orchestration server."""
        super().__init__(
            name="workflow-orchestration",
            version="1.0.0",
            description="Multi-agent workflow orchestration via MCP"
        )

        # Initialize orchestrators
        self.master_orchestrator = MasterOrchestrator()
        self.parallel_orchestrator = ParallelDevelopmentOrchestrator()
        self.progressive_orchestrator = ProgressiveEnhancementOrchestrator()
        self.specialized_orchestrator = SpecializedRolesOrchestrator()

        # Initialize validation system (Phase B)
        self.validator = ValidationOrchestrator()
        self.refinement_loop = RefinementLoop(max_iterations=3, min_score_threshold=80.0)

        # Workflow metrics storage
        self.workflow_metrics = {
            "auto": {"count": 0, "avg_time": 0.0, "avg_cost": 0.0, "avg_quality": 0.0},
            "parallel": {"count": 0, "avg_time": 0.0, "avg_cost": 0.0, "avg_quality": 0.0},
            "progressive": {"count": 0, "avg_time": 0.0, "avg_cost": 0.0, "avg_quality": 0.0},
            "specialized": {"count": 0, "avg_time": 0.0, "avg_cost": 0.0, "avg_quality": 0.0}
        }

        logger.info("Initialized WorkflowOrchestrationServer")

    async def _register_tools(self):
        """Register all workflow orchestration tools."""

        # Tool 1: Execute Workflow (Auto-routing with Validation)
        self.create_tool(
            name="execute_workflow",
            description="Execute task using optimal workflow (auto-routing). "
                       "Master orchestrator analyzes task and routes to best workflow: "
                       "Progressive (simple tasks), Parallel (multi-component), "
                       "Specialized (complex single tasks). Returns workflow result with routing decision. "
                       "Optional validation: Enable quality gate validation after execution. "
                       "Optional refinement: Automatically refine if validation fails.",
            input_schema={
                "type": "object",
                "properties": {
                    "task": ToolParameter.string(
                        "Task description to execute"
                    ),
                    "workflow": ToolParameter.string(
                        "Workflow to use (default: auto-routing)",
                        enum=["auto", "parallel", "progressive", "specialized"],
                        default="auto"
                    ),
                    "enable_validation": ToolParameter.boolean(
                        "Run quality gate validation after execution",
                        default=False
                    ),
                    "validation_level": ToolParameter.string(
                        "Validation level (quick, standard, thorough)",
                        enum=["quick", "standard", "thorough"],
                        default="standard"
                    ),
                    "auto_refine": ToolParameter.boolean(
                        "Automatically refine if validation fails",
                        default=False
                    ),
                    "context": ToolParameter.object(
                        "Optional context for task execution",
                        properties={
                            "project_info": {"type": "string"},
                            "requirements": {"type": "string"},
                            "constraints": {"type": "string"}
                        }
                    )
                },
                "required": ["task"]
            },
            handler=self._handle_execute_workflow
        )

        # Tool 2: Parallel Workflow (Explicit)
        self.create_tool(
            name="parallel_workflow",
            description="Execute multi-component task using parallel development workflow. "
                       "Distributes work across multiple agents simultaneously for 30-70% time savings. "
                       "Best for tasks with independent components. Returns results with time savings metrics.",
            input_schema={
                "type": "object",
                "properties": {
                    "task": ToolParameter.string(
                        "Task description"
                    ),
                    "components": ToolParameter.array(
                        "List of independent components to develop in parallel",
                        items={"type": "string"},
                        min_items=2
                    ),
                    "context": ToolParameter.object(
                        "Optional context",
                        properties={
                            "shared_dependencies": {"type": "string"},
                            "integration_requirements": {"type": "string"}
                        }
                    )
                },
                "required": ["task", "components"]
            },
            handler=self._handle_parallel_workflow
        )

        # Tool 3: Progressive Workflow (Explicit)
        self.create_tool(
            name="progressive_workflow",
            description="Execute task using progressive enhancement workflow. "
                       "Starts with fast/cheap approach (Haiku), escalates if quality threshold not met. "
                       "Best for simple tasks with quality validation. Returns result with escalation history.",
            input_schema={
                "type": "object",
                "properties": {
                    "task": ToolParameter.string(
                        "Task description"
                    ),
                    "context": ToolParameter.object(
                        "Optional context",
                        properties={
                            "initial_attempt": {"type": "string"}
                        }
                    ),
                    "quality_threshold": ToolParameter.integer(
                        "Minimum quality score (0-100)",
                        default=90,
                        minimum=0,
                        maximum=100
                    )
                },
                "required": ["task"]
            },
            handler=self._handle_progressive_workflow
        )

        # Tool 4: Specialized Workflow (Explicit)
        self.create_tool(
            name="specialized_workflow",
            description="Execute task using specialized roles workflow (4 phases). "
                       "Runs through architect → developer → tester → reviewer pipeline. "
                       "Best for complex tasks requiring comprehensive review. Returns all phase outputs.",
            input_schema={
                "type": "object",
                "properties": {
                    "task": ToolParameter.string(
                        "Task description"
                    ),
                    "context": ToolParameter.object(
                        "Optional context",
                        properties={
                            "architecture_notes": {"type": "string"},
                            "test_requirements": {"type": "string"}
                        }
                    )
                },
                "required": ["task"]
            },
            handler=self._handle_specialized_workflow
        )

        # Tool 5: Get Workflow Recommendation
        self.create_tool(
            name="get_workflow_recommendation",
            description="Get recommendation for which workflow to use for a task. "
                       "Analyzes task characteristics and constraints to recommend optimal workflow. "
                       "Returns recommended workflow with reasoning and expected performance.",
            input_schema={
                "type": "object",
                "properties": {
                    "task": ToolParameter.string(
                        "Task description to analyze"
                    ),
                    "constraints": ToolParameter.object(
                        "Optional constraints",
                        properties={
                            "max_time": {"type": "number", "description": "Max time in seconds"},
                            "max_cost": {"type": "number", "description": "Max cost in USD"},
                            "min_quality": {"type": "integer", "description": "Min quality score (0-100)"}
                        }
                    )
                },
                "required": ["task"]
            },
            handler=self._handle_get_workflow_recommendation
        )

    async def _register_resources(self):
        """Register all workflow orchestration resources."""

        # Resource 1: Available Workflows
        self.create_resource(
            uri="workflows://available",
            name="Available Workflows",
            description="Catalog of all available workflows with descriptions and use cases",
            handler=self._handle_available_workflows
        )

        # Resource 2: Workflow Metrics
        self.create_resource(
            uri="workflows://metrics",
            name="Workflow Metrics",
            description="Performance metrics for each workflow type (time, cost, quality)",
            handler=self._handle_workflow_metrics
        )

    # ==================== TOOL HANDLERS ====================

    async def _handle_execute_workflow(
        self,
        task: str,
        workflow: str = "auto",
        enable_validation: bool = False,
        validation_level: str = "standard",
        auto_refine: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle workflow execution with auto-routing or explicit selection.

        Optionally runs quality gate validation after execution and can
        automatically refine the output if validation fails.
        """
        try:
            logger.info(f"Executing workflow: {workflow} for task: {task[:50]}... "
                       f"(validation={enable_validation}, auto_refine={auto_refine})")

            start_time = datetime.now()

            # Prepare enhanced task with context
            enhanced_task = task
            if context:
                if context.get("project_info"):
                    enhanced_task += f"\n\nProject: {context['project_info']}"
                if context.get("requirements"):
                    enhanced_task += f"\nRequirements: {context['requirements']}"
                if context.get("constraints"):
                    enhanced_task += f"\nConstraints: {context['constraints']}"

            # Execute based on workflow selection
            if workflow == "auto":
                # Use master orchestrator for routing
                result = await self.master_orchestrator.execute_workflow(enhanced_task)
                workflow_used = result.workflow_type
            elif workflow == "parallel":
                result = await self.parallel_orchestrator.execute_workflow(enhanced_task)
                workflow_used = "parallel"
            elif workflow == "progressive":
                result = await self.progressive_orchestrator.execute_workflow(enhanced_task)
                workflow_used = "progressive"
            elif workflow == "specialized":
                result = await self.specialized_orchestrator.execute_workflow(enhanced_task)
                workflow_used = "specialized"
            else:
                raise ValueError(f"Unknown workflow: {workflow}")

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Update metrics
            self._update_metrics(workflow_used, execution_time, result)

            # PHASE B: Optional Validation Step
            validation_report = None
            refinement_result = None

            if enable_validation:
                logger.info(f"Running validation (level: {validation_level})...")

                # Save output to temp file for validation
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(result.final_output)
                    temp_path = f.name

                try:
                    # Run quality gate validation
                    validation_report = await self.validator.run_all_validators(
                        target_path=temp_path,
                        level=validation_level,
                        context=context or {}
                    )

                    logger.info(
                        f"Validation complete: {validation_report.overall_status}, "
                        f"score={validation_report.average_score:.1f}"
                    )

                    # Optional: Auto-refinement if validation fails
                    if auto_refine and not validation_report.passed:
                        logger.info("Validation failed, triggering auto-refinement...")

                        # Define generator and validator functions for refinement loop
                        async def generator(input_dict):
                            """Regenerate based on feedback."""
                            # Re-run workflow with feedback context
                            feedback_context = {
                                **(input_dict.get("context", {})),
                                "validation_feedback": input_dict.get("validation_feedback", []),
                                "previous_attempt": input_dict.get("previous_attempt", "")
                            }
                            regen_result = await self.master_orchestrator.execute_workflow(
                                input_dict["task"],
                                context=feedback_context
                            )
                            return regen_result.final_output

                        async def validator(artifact, val_context):
                            """Validate regenerated artifact."""
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
                                f2.write(artifact)
                                path2 = f2.name
                            try:
                                report = await self.validator.run_all_validators(
                                    target_path=path2,
                                    level=validation_level,
                                    context=val_context
                                )
                                return report
                            finally:
                                Path(path2).unlink()

                        # Run refinement loop
                        refinement_result = await self.refinement_loop.refine(
                            generator_func=generator,
                            validator_func=validator,
                            initial_input={"task": task, "context": context or {}},
                            validation_context=context or {}
                        )

                        if refinement_result.success and refinement_result.converged:
                            logger.info("✅ Refinement converged - using refined output")
                            result.final_output = refinement_result.final_artifact
                            validation_report = refinement_result.final_validation
                        else:
                            logger.warning("⚠️  Refinement did not converge - using original output")

                finally:
                    # Cleanup temp file
                    Path(temp_path).unlink()

            # Format response
            response = {
                "success": True,
                "workflow_used": workflow_used,
                "execution_time": execution_time,
                "result": {
                    "output": result.final_output,
                    "quality_score": getattr(result, "quality_score", None),
                    "cost": getattr(result, "total_cost", 0.0),
                    "phases": getattr(result, "phases", {})
                },
                "metadata": {
                    "timestamp": end_time.isoformat(),
                    "task_length": len(task)
                }
            }

            # Add validation results if present
            if validation_report:
                response["validation"] = {
                    "enabled": True,
                    "level": validation_level,
                    "status": validation_report.overall_status,
                    "score": validation_report.average_score,
                    "critical_findings": validation_report.critical_count,
                    "high_findings": validation_report.high_count,
                    "passed": validation_report.passed,
                    "report": validation_report.to_dict()
                }

            # Add refinement results if present
            if refinement_result:
                response["refinement"] = {
                    "enabled": True,
                    "converged": refinement_result.converged,
                    "iterations": refinement_result.total_iterations,
                    "improvement_history": refinement_result.improvement_history,
                    "total_cost_usd": refinement_result.total_cost_usd
                }

            logger.info(f"Workflow {workflow_used} completed in {execution_time:.2f}s "
                       f"(validation={enable_validation}, refined={refinement_result is not None})")

            status_msg = f"Workflow completed using {workflow_used}"
            if validation_report:
                status_msg += f" | Validation: {validation_report.overall_status} ({validation_report.average_score:.1f}/100)"
            if refinement_result and refinement_result.converged:
                status_msg += f" | Refined in {refinement_result.total_iterations} iterations"

            return self.format_success(response, status_msg)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_parallel_workflow(
        self,
        task: str,
        components: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle explicit parallel workflow execution.
        """
        try:
            logger.info(f"Executing parallel workflow for {len(components)} components")

            start_time = datetime.now()

            # Prepare task with components
            enhanced_task = f"{task}\n\nComponents to develop in parallel:\n"
            for i, component in enumerate(components, 1):
                enhanced_task += f"{i}. {component}\n"

            if context:
                if context.get("shared_dependencies"):
                    enhanced_task += f"\nShared dependencies: {context['shared_dependencies']}"
                if context.get("integration_requirements"):
                    enhanced_task += f"\nIntegration: {context['integration_requirements']}"

            # Execute parallel workflow
            result = await self.parallel_orchestrator.execute_workflow(enhanced_task)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Calculate time savings (estimate vs parallel)
            estimated_sequential_time = execution_time * len(components) * 0.7
            time_savings_pct = ((estimated_sequential_time - execution_time) / estimated_sequential_time) * 100

            # Update metrics
            self._update_metrics("parallel", execution_time, result)

            response = {
                "success": True,
                "workflow": "parallel",
                "execution_time": execution_time,
                "components_count": len(components),
                "time_savings": {
                    "estimated_sequential": estimated_sequential_time,
                    "actual_parallel": execution_time,
                    "savings_percent": time_savings_pct
                },
                "result": {
                    "output": result.final_output,
                    "cost": getattr(result, "total_cost", 0.0),
                    "component_results": getattr(result, "phases", {})
                }
            }

            logger.info(f"Parallel workflow completed with {time_savings_pct:.1f}% time savings")

            return self.format_success(response, f"Parallel execution saved ~{time_savings_pct:.1f}% time")

        except Exception as e:
            logger.error(f"Parallel workflow failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_progressive_workflow(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        quality_threshold: int = 90
    ) -> Dict[str, Any]:
        """
        Handle explicit progressive enhancement workflow.
        """
        try:
            logger.info(f"Executing progressive workflow (threshold: {quality_threshold})")

            start_time = datetime.now()

            # Prepare task
            enhanced_task = task
            if context and context.get("initial_attempt"):
                enhanced_task += f"\n\nInitial attempt: {context['initial_attempt']}"

            # Execute progressive workflow
            result = await self.progressive_orchestrator.execute_workflow(
                enhanced_task,
                quality_threshold=quality_threshold
            )

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Track escalations
            escalated = getattr(result, "escalated", False)
            attempts = getattr(result, "attempts", 1)

            # Update metrics
            self._update_metrics("progressive", execution_time, result)

            response = {
                "success": True,
                "workflow": "progressive",
                "execution_time": execution_time,
                "quality_threshold": quality_threshold,
                "escalation": {
                    "escalated": escalated,
                    "attempts": attempts,
                    "final_quality": getattr(result, "quality_score", None)
                },
                "result": {
                    "output": result.final_output,
                    "cost": getattr(result, "total_cost", 0.0)
                }
            }

            logger.info(f"Progressive workflow completed ({'escalated' if escalated else 'no escalation'})")

            return self.format_success(response, f"Completed with {attempts} attempt(s)")

        except Exception as e:
            logger.error(f"Progressive workflow failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_specialized_workflow(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle explicit specialized roles workflow.
        """
        try:
            logger.info("Executing specialized roles workflow (4 phases)")

            start_time = datetime.now()

            # Prepare task
            enhanced_task = task
            if context:
                if context.get("architecture_notes"):
                    enhanced_task += f"\n\nArchitecture: {context['architecture_notes']}"
                if context.get("test_requirements"):
                    enhanced_task += f"\nTesting: {context['test_requirements']}"

            # Execute specialized workflow
            result = await self.specialized_orchestrator.execute_workflow(enhanced_task)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Extract phase results
            phases = getattr(result, "phases", {})
            phase_summary = {
                phase_name: {
                    "completed": phase_data.get("completed", False),
                    "time": phase_data.get("time", 0.0),
                    "output_length": len(str(phase_data.get("output", "")))
                }
                for phase_name, phase_data in phases.items()
            }

            # Update metrics
            self._update_metrics("specialized", execution_time, result)

            response = {
                "success": True,
                "workflow": "specialized",
                "execution_time": execution_time,
                "phases": {
                    "architect": phases.get("architect", {}).get("output", "N/A"),
                    "developer": phases.get("developer", {}).get("output", "N/A"),
                    "tester": phases.get("tester", {}).get("output", "N/A"),
                    "reviewer": phases.get("reviewer", {}).get("output", "N/A")
                },
                "phase_summary": phase_summary,
                "result": {
                    "output": result.final_output,
                    "cost": getattr(result, "total_cost", 0.0)
                }
            }

            logger.info(f"Specialized workflow completed all 4 phases")

            return self.format_success(response, "4-phase review complete")

        except Exception as e:
            logger.error(f"Specialized workflow failed: {e}", exc_info=True)
            return self.format_error(e)

    async def _handle_get_workflow_recommendation(
        self,
        task: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle workflow recommendation based on task analysis.
        """
        try:
            logger.info(f"Analyzing task for workflow recommendation: {task[:50]}...")

            # Analyze task characteristics
            analysis = self._analyze_task(task, constraints)

            # Recommend workflow
            recommendation = self._recommend_workflow(analysis, constraints)

            response = {
                "success": True,
                "task_analysis": analysis,
                "recommendation": recommendation,
                "reasoning": self._generate_reasoning(analysis, recommendation, constraints),
                "alternatives": self._get_alternatives(recommendation)
            }

            logger.info(f"Recommended workflow: {recommendation['workflow']}")

            return self.format_success(response, f"Recommended: {recommendation['workflow']}")

        except Exception as e:
            logger.error(f"Recommendation failed: {e}", exc_info=True)
            return self.format_error(e)

    # ==================== RESOURCE HANDLERS ====================

    async def _handle_available_workflows(self) -> Dict[str, Any]:
        """Provide catalog of available workflows."""
        return {
            "workflows": [
                {
                    "name": "auto",
                    "description": "Auto-routing to optimal workflow based on task analysis",
                    "use_cases": ["Any task where optimal workflow is unclear", "Let the system decide"],
                    "characteristics": "Intelligent routing, best overall choice"
                },
                {
                    "name": "parallel",
                    "description": "Parallel development for multi-component tasks",
                    "use_cases": ["Multiple independent components", "Time-critical projects", "Can parallelize work"],
                    "characteristics": "30-70% faster, requires independent components"
                },
                {
                    "name": "progressive",
                    "description": "Progressive enhancement with escalation",
                    "use_cases": ["Simple tasks", "Cost-sensitive projects", "Quality validation needed"],
                    "characteristics": "Start cheap (Haiku), escalate if needed"
                },
                {
                    "name": "specialized",
                    "description": "4-phase specialized roles workflow",
                    "use_cases": ["Complex single tasks", "Comprehensive review needed", "Architecture → implementation → testing → review"],
                    "characteristics": "Thorough, 4 distinct phases"
                }
            ],
            "total_workflows": 4
        }

    async def _handle_workflow_metrics(self) -> Dict[str, Any]:
        """Provide workflow performance metrics."""
        return self.workflow_metrics

    # ==================== HELPER METHODS ====================

    def _analyze_task(self, task: str, constraints: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze task characteristics."""
        task_lower = task.lower()

        return {
            "complexity": self._estimate_complexity(task),
            "component_count": self._count_components(task),
            "requires_architecture": any(word in task_lower for word in ["design", "architecture", "structure"]),
            "requires_testing": any(word in task_lower for word in ["test", "testing", "validation"]),
            "time_sensitive": constraints.get("max_time") is not None if constraints else False,
            "cost_sensitive": constraints.get("max_cost") is not None if constraints else False,
            "quality_critical": constraints.get("min_quality", 0) >= 90 if constraints else False
        }

    def _estimate_complexity(self, task: str) -> str:
        """Estimate task complexity."""
        # Simple heuristic based on task length and keywords
        complex_keywords = ["architecture", "design", "complex", "comprehensive", "system"]
        task_lower = task.lower()

        if len(task) > 500 or any(word in task_lower for word in complex_keywords):
            return "complex"
        elif len(task) > 200:
            return "moderate"
        else:
            return "simple"

    def _count_components(self, task: str) -> int:
        """Count number of components in task."""
        # Look for numbered lists or bullet points
        import re
        numbered = len(re.findall(r'\d+\.\s', task))
        bulleted = len(re.findall(r'[-*]\s', task))
        return max(numbered, bulleted, 1)

    def _recommend_workflow(
        self,
        analysis: Dict[str, Any],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Recommend optimal workflow based on analysis."""
        # Multi-component and time-sensitive → Parallel
        if analysis["component_count"] >= 2 and analysis["time_sensitive"]:
            return {
                "workflow": "parallel",
                "confidence": "high",
                "expected_time": "Fast (parallel execution)",
                "expected_cost": "Moderate",
                "expected_quality": "Good"
            }

        # Complex or requires architecture → Specialized
        if analysis["complexity"] == "complex" or analysis["requires_architecture"]:
            return {
                "workflow": "specialized",
                "confidence": "high",
                "expected_time": "Longer (4 phases)",
                "expected_cost": "Higher",
                "expected_quality": "Excellent"
            }

        # Simple and cost-sensitive → Progressive
        if analysis["complexity"] == "simple" and analysis["cost_sensitive"]:
            return {
                "workflow": "progressive",
                "confidence": "high",
                "expected_time": "Fast (may escalate)",
                "expected_cost": "Low (starts with Haiku)",
                "expected_quality": "Good (validated)"
            }

        # Default → Auto (let master decide)
        return {
            "workflow": "auto",
            "confidence": "medium",
            "expected_time": "Depends on routing",
            "expected_cost": "Depends on routing",
            "expected_quality": "Good"
        }

    def _generate_reasoning(
        self,
        analysis: Dict[str, Any],
        recommendation: Dict[str, Any],
        constraints: Optional[Dict[str, Any]]
    ) -> str:
        """Generate reasoning for recommendation."""
        workflow = recommendation["workflow"]

        reasons = []

        if workflow == "parallel":
            reasons.append(f"Task has {analysis['component_count']} components that can be developed in parallel")
            if analysis["time_sensitive"]:
                reasons.append("Time constraint makes parallel execution optimal")

        elif workflow == "specialized":
            if analysis["complexity"] == "complex":
                reasons.append("Task complexity requires comprehensive 4-phase review")
            if analysis["requires_architecture"]:
                reasons.append("Architecture phase needed for proper design")
            if analysis["requires_testing"]:
                reasons.append("Dedicated testing phase ensures quality")

        elif workflow == "progressive":
            reasons.append("Task is simple enough to start with fast/cheap approach")
            if analysis["cost_sensitive"]:
                reasons.append("Cost constraints favor progressive enhancement")

        else:  # auto
            reasons.append("Task characteristics suggest letting master orchestrator route optimally")

        return " ".join(reasons)

    def _get_alternatives(self, recommendation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get alternative workflows."""
        workflows = ["parallel", "progressive", "specialized", "auto"]
        current = recommendation["workflow"]

        alternatives = []
        for wf in workflows:
            if wf != current:
                alternatives.append({
                    "workflow": wf,
                    "when_to_use": self._get_when_to_use(wf)
                })

        return alternatives

    def _get_when_to_use(self, workflow: str) -> str:
        """Get use case description for workflow."""
        descriptions = {
            "parallel": "When task has multiple independent components",
            "progressive": "When task is simple and cost is a concern",
            "specialized": "When task is complex and requires comprehensive review",
            "auto": "When unsure which workflow is best"
        }
        return descriptions.get(workflow, "Unknown workflow")

    def _update_metrics(self, workflow: str, execution_time: float, result: Any):
        """Update workflow performance metrics."""
        metrics = self.workflow_metrics.get(workflow)
        if not metrics:
            return

        count = metrics["count"]
        new_count = count + 1

        # Update averages
        metrics["avg_time"] = (metrics["avg_time"] * count + execution_time) / new_count
        metrics["avg_cost"] = (metrics["avg_cost"] * count + getattr(result, "total_cost", 0.0)) / new_count

        quality = getattr(result, "quality_score", None)
        if quality:
            metrics["avg_quality"] = (metrics["avg_quality"] * count + quality) / new_count

        metrics["count"] = new_count


async def main():
    """Main entry point for workflow orchestration server."""
    server = WorkflowOrchestrationServer()
    await server.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
