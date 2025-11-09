"""
Specialized Roles Orchestrator - Production-Grade Multi-AI Workflow

Coordinates 4 specialized AI roles for high-quality software development:
- ARCHITECT: System design and planning (Claude Opus)
- DEVELOPER: Implementation (Claude Sonnet)
- TESTER: Test generation (Claude Sonnet)
- REVIEWER: Quality review (Claude Opus)

Features:
- Integration with Phase B infrastructure (ResilientBaseAgent)
- Integration with Priority 2 validators (ValidationOrchestrator)
- Self-correction loops (max 3 iterations)
- Cost tracking per role
- Quality threshold enforcement (90+ score)
- Production-grade error handling

Architecture:
    SpecializedRolesOrchestrator
    ├── Architect Phase (design & planning)
    ├── Developer Phase (implementation)
    │   └── Validator integration (code quality check)
    ├── Tester Phase (test generation)
    │   └── Validator integration (test quality check)
    ├── Reviewer Phase (final review)
    │   └── Validator integration (overall quality check)
    └── Self-Correction Loop (if quality < 90)

Usage:
    orchestrator = SpecializedRolesOrchestrator(project_root="/path/to/project")
    result = orchestrator.execute_workflow(
        task="Implement user authentication",
        context={"framework": "FastAPI", "database": "PostgreSQL"},
        quality_threshold=90
    )
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import traceback

# Observability
try:
    from observability.event_emitter import EventEmitter, EventType, EventSeverity
except ImportError:
    EventEmitter = None
    EventType = None
    EventSeverity = None

# Phase B infrastructure
from resilient_agent import ResilientBaseAgent, CallResult

# Priority 2 validators
from validation_orchestrator import ValidationOrchestrator
from validation_types import ValidationResult, Status

# Priority 3 - Role definitions
from role_definitions import (
    Role,
    RoleType,
    get_role,
    get_all_roles,
    ARCHITECT_ROLE,
    DEVELOPER_ROLE,
    TESTER_ROLE,
    REVIEWER_ROLE
)


class WorkflowPhase(str, Enum):
    """Enum for workflow phases."""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"


@dataclass
class PhaseResult:
    """Result from a single workflow phase."""
    phase: WorkflowPhase
    role: Role
    output: str
    success: bool

    # Execution metrics
    execution_time_ms: float
    tokens_used: int
    cost_usd: float
    model_used: str

    # Validation results
    validation_result: Optional[ValidationResult] = None
    quality_score: Optional[int] = None

    # Self-correction tracking
    iteration: int = 1
    self_corrected: bool = False

    # Error information
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'phase': self.phase.value,
            'role_name': self.role.name,
            'success': self.success,
            'execution_time_ms': self.execution_time_ms,
            'tokens_used': self.tokens_used,
            'cost_usd': self.cost_usd,
            'model_used': self.model_used,
            'quality_score': self.quality_score,
            'iteration': self.iteration,
            'self_corrected': self.self_corrected,
            'error': self.error,
            'output_length': len(self.output) if self.output else 0
        }


@dataclass
class WorkflowResult:
    """Complete workflow result with all phases."""
    task: str
    context: Dict[str, Any]

    # Phase results
    architect_result: Optional[PhaseResult] = None
    developer_result: Optional[PhaseResult] = None
    tester_result: Optional[PhaseResult] = None
    reviewer_result: Optional[PhaseResult] = None

    # Overall metrics
    overall_quality_score: Optional[int] = None
    total_execution_time_ms: float = 0.0
    total_cost_usd: float = 0.0
    total_tokens: int = 0

    # Status
    success: bool = False
    completed_phases: List[WorkflowPhase] = field(default_factory=list)

    # Self-correction tracking
    total_iterations: int = 0
    phases_self_corrected: List[WorkflowPhase] = field(default_factory=list)

    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'task': self.task,
            'context': self.context,
            'success': self.success,
            'overall_quality_score': self.overall_quality_score,
            'total_execution_time_ms': self.total_execution_time_ms,
            'total_cost_usd': self.total_cost_usd,
            'total_tokens': self.total_tokens,
            'total_iterations': self.total_iterations,
            'completed_phases': [p.value for p in self.completed_phases],
            'phases_self_corrected': [p.value for p in self.phases_self_corrected],
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

        # Add phase results
        for phase_name in ['architect', 'developer', 'tester', 'reviewer']:
            phase_result = getattr(self, f'{phase_name}_result')
            if phase_result:
                result[f'{phase_name}_phase'] = phase_result.to_dict()

        return result

    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            "=" * 80,
            "SPECIALIZED ROLES WORKFLOW SUMMARY",
            "=" * 80,
            f"Task: {self.task}",
            f"Status: {'✅ SUCCESS' if self.success else '❌ FAILED'}",
            f"Overall Quality Score: {self.overall_quality_score}/100" if self.overall_quality_score else "Overall Quality Score: N/A",
            "",
            "EXECUTION METRICS:",
            f"  Total Time: {self.total_execution_time_ms/1000:.2f}s",
            f"  Total Cost: ${self.total_cost_usd:.6f}",
            f"  Total Tokens: {self.total_tokens:,}",
            f"  Total Iterations: {self.total_iterations}",
            "",
            "PHASES COMPLETED:",
        ]

        for phase in self.completed_phases:
            phase_result = getattr(self, f'{phase.value}_result')
            if phase_result:
                status_icon = "✅" if phase_result.success else "❌"
                corrected = " (self-corrected)" if phase_result.self_corrected else ""
                lines.append(f"  {status_icon} {phase.value.upper()}: {phase_result.quality_score}/100{corrected}")

        lines.append("=" * 80)
        return "\n".join(lines)


class SpecializedRolesOrchestrator:
    """
    Orchestrates specialized AI roles for production-grade software development.

    Workflow:
    1. ARCHITECT analyzes task and creates design plan
    2. DEVELOPER implements based on plan
    3. TESTER generates comprehensive tests
    4. REVIEWER performs final quality check
    5. Validators ensure quality thresholds are met
    6. Self-correction if quality < threshold

    Example:
        orchestrator = SpecializedRolesOrchestrator(
            project_root="/path/to/project",
            quality_threshold=90
        )

        result = orchestrator.execute_workflow(
            task="Implement user authentication with JWT",
            context={
                "framework": "FastAPI",
                "database": "PostgreSQL",
                "requirements": ["email/password login", "refresh tokens", "rate limiting"]
            }
        )

        if result.success:
            print(f"Quality Score: {result.overall_quality_score}/100")
            print(f"Cost: ${result.total_cost_usd:.6f}")
    """

    def __init__(self,
                 project_root: str,
                 quality_threshold: int = 90,
                 max_self_correction_iterations: int = 3,
                 enable_validation: bool = True,
                 enable_self_correction: bool = True):
        """
        Initialize specialized roles orchestrator.

        Args:
            project_root: Root directory of the project
            quality_threshold: Minimum quality score required (0-100)
            max_self_correction_iterations: Max times to retry with self-correction
            enable_validation: Enable validator integration
            enable_self_correction: Enable self-correction loops
        """
        self.project_root = Path(project_root)
        self.quality_threshold = quality_threshold
        self.max_self_correction_iterations = max_self_correction_iterations
        self.enable_validation = enable_validation
        self.enable_self_correction = enable_self_correction

        # Initialize validator orchestrator (Priority 2)
        if self.enable_validation:
            self.validator = ValidationOrchestrator(
                project_root=str(self.project_root),
                validators=["code-validator", "test-validator"]
            )
        else:
            self.validator = None

        # Initialize observability
        if EventEmitter is not None:
            self.emitter = EventEmitter(enable_console=False)
        else:
            self.emitter = None

        # Initialize role agents (using ResilientBaseAgent from Phase B)
        self.agents: Dict[RoleType, ResilientBaseAgent] = {}
        self._initialize_agents()

        print(f"✅ SpecializedRolesOrchestrator initialized")
        print(f"   Project Root: {self.project_root}")
        print(f"   Quality Threshold: {self.quality_threshold}/100")
        print(f"   Max Self-Correction Iterations: {self.max_self_correction_iterations}")
        print(f"   Validation Enabled: {self.enable_validation}")
        print(f"   Self-Correction Enabled: {self.enable_self_correction}")

    def _initialize_agents(self):
        """Initialize ResilientBaseAgent for each role."""
        for role_type in RoleType:
            role = get_role(role_type)

            # Create agent with role-specific configuration
            agent = ResilientBaseAgent(
                role=role.name,
                model=role.primary_model,
                temperature=role.temperature,
                max_tokens=role.max_tokens,
                max_retries=3,
                enable_fallback=True,  # Enable multi-provider fallback
                enable_security=True,  # Enable security validation
                system_prompt=role.system_prompt
            )

            self.agents[role_type] = agent
            print(f"   ✅ Initialized {role.name} agent ({role.primary_model})")

    def execute_workflow(self,
                        task: str,
                        context: Dict[str, Any],
                        quality_threshold: Optional[int] = None) -> WorkflowResult:
        """
        Execute complete specialized roles workflow.

        Args:
            task: Task description
            context: Task context and requirements
            quality_threshold: Override default quality threshold

        Returns:
            WorkflowResult with all phase results and metrics
        """
        threshold = quality_threshold if quality_threshold is not None else self.quality_threshold

        print(f"\n{'='*80}")
        print(f"STARTING SPECIALIZED ROLES WORKFLOW")
        print(f"{'='*80}")
        print(f"Task: {task}")
        print(f"Quality Threshold: {threshold}/100")
        print(f"{'='*80}\n")

        result = WorkflowResult(
            task=task,
            context=context,
            started_at=datetime.now()
        )

        # Start workflow trace
        if self.emitter:
            self.emitter.start_trace(
                workflow="specialized_roles",
                context={
                    "quality_threshold": threshold,
                    "validation_enabled": self.enable_validation,
                    "self_correction_enabled": self.enable_self_correction
                }
            )

        try:
            # Phase 1: ARCHITECT
            print(f"\n📐 PHASE 1: ARCHITECT - Analyzing and Designing")
            print("-" * 80)
            if self.emitter:
                self.emitter.start_span("architect")

            result.architect_result = self._execute_phase(
                phase=WorkflowPhase.ARCHITECT,
                task=task,
                context=context,
                previous_results={}
            )
            if not result.architect_result.success:
                raise Exception(f"Architect phase failed: {result.architect_result.error}")
            result.completed_phases.append(WorkflowPhase.ARCHITECT)

            if self.emitter:
                self.emitter.emit(
                    event_type=EventType.AGENT_COMPLETED,
                    component="architect",
                    message="Architect phase completed",
                    severity=EventSeverity.INFO,
                    duration_ms=result.architect_result.execution_time_ms,
                    cost_usd=result.architect_result.cost_usd,
                    model=result.architect_result.model_used,
                    data={"quality_score": result.architect_result.quality_score}
                )
                self.emitter.end_span()

            # Phase 2: DEVELOPER
            print(f"\n💻 PHASE 2: DEVELOPER - Implementing")
            print("-" * 80)
            if self.emitter:
                self.emitter.start_span("developer")

            result.developer_result = self._execute_phase(
                phase=WorkflowPhase.DEVELOPER,
                task=task,
                context=context,
                previous_results={'architect': result.architect_result.output}
            )
            if not result.developer_result.success:
                raise Exception(f"Developer phase failed: {result.developer_result.error}")
            result.completed_phases.append(WorkflowPhase.DEVELOPER)

            if self.emitter:
                self.emitter.emit(
                    event_type=EventType.AGENT_COMPLETED,
                    component="developer",
                    message="Developer phase completed",
                    severity=EventSeverity.INFO,
                    duration_ms=result.developer_result.execution_time_ms,
                    cost_usd=result.developer_result.cost_usd,
                    model=result.developer_result.model_used,
                    data={"quality_score": result.developer_result.quality_score}
                )
                self.emitter.end_span()

            # Validate code quality
            if self.enable_validation:
                result.developer_result = self._validate_and_correct(
                    phase_result=result.developer_result,
                    validation_type="code",
                    threshold=threshold,
                    context=context
                )

            # Phase 3: TESTER
            print(f"\n🧪 PHASE 3: TESTER - Generating Tests")
            print("-" * 80)
            if self.emitter:
                self.emitter.start_span("tester")

            result.tester_result = self._execute_phase(
                phase=WorkflowPhase.TESTER,
                task=task,
                context=context,
                previous_results={
                    'architect': result.architect_result.output,
                    'developer': result.developer_result.output
                }
            )
            if not result.tester_result.success:
                raise Exception(f"Tester phase failed: {result.tester_result.error}")
            result.completed_phases.append(WorkflowPhase.TESTER)

            if self.emitter:
                self.emitter.emit(
                    event_type=EventType.AGENT_COMPLETED,
                    component="tester",
                    message="Tester phase completed",
                    severity=EventSeverity.INFO,
                    duration_ms=result.tester_result.execution_time_ms,
                    cost_usd=result.tester_result.cost_usd,
                    model=result.tester_result.model_used,
                    data={"quality_score": result.tester_result.quality_score}
                )
                self.emitter.end_span()

            # Validate test quality
            if self.enable_validation:
                result.tester_result = self._validate_and_correct(
                    phase_result=result.tester_result,
                    validation_type="test",
                    threshold=threshold,
                    context=context
                )

            # Phase 4: REVIEWER
            print(f"\n✅ PHASE 4: REVIEWER - Final Quality Check")
            print("-" * 80)
            if self.emitter:
                self.emitter.start_span("reviewer")

            result.reviewer_result = self._execute_phase(
                phase=WorkflowPhase.REVIEWER,
                task=task,
                context=context,
                previous_results={
                    'architect': result.architect_result.output,
                    'developer': result.developer_result.output,
                    'tester': result.tester_result.output
                }
            )
            if not result.reviewer_result.success:
                raise Exception(f"Reviewer phase failed: {result.reviewer_result.error}")
            result.completed_phases.append(WorkflowPhase.REVIEWER)

            if self.emitter:
                self.emitter.emit(
                    event_type=EventType.AGENT_COMPLETED,
                    component="reviewer",
                    message="Reviewer phase completed",
                    severity=EventSeverity.INFO,
                    duration_ms=result.reviewer_result.execution_time_ms,
                    cost_usd=result.reviewer_result.cost_usd,
                    model=result.reviewer_result.model_used,
                    data={"quality_score": result.reviewer_result.quality_score}
                )
                self.emitter.end_span()

            # Extract overall quality score from reviewer
            result.overall_quality_score = self._extract_quality_score(result.reviewer_result.output)

            # Check if quality threshold met
            if result.overall_quality_score and result.overall_quality_score < threshold:
                print(f"\n⚠️  Quality score ({result.overall_quality_score}) below threshold ({threshold})")

                if self.enable_self_correction:
                    print(f"🔄 Initiating self-correction workflow...")
                    result = self._full_workflow_self_correction(result, threshold)
                else:
                    print(f"❌ Self-correction disabled. Workflow failed to meet quality threshold.")
                    result.success = False
            else:
                print(f"\n✅ Quality threshold met: {result.overall_quality_score}/{threshold}")
                result.success = True

            # Calculate total metrics
            result.total_execution_time_ms = sum([
                r.execution_time_ms for r in [
                    result.architect_result,
                    result.developer_result,
                    result.tester_result,
                    result.reviewer_result
                ] if r
            ])

            result.total_cost_usd = sum([
                r.cost_usd for r in [
                    result.architect_result,
                    result.developer_result,
                    result.tester_result,
                    result.reviewer_result
                ] if r
            ])

            result.total_tokens = sum([
                r.tokens_used for r in [
                    result.architect_result,
                    result.developer_result,
                    result.tester_result,
                    result.reviewer_result
                ] if r
            ])

        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            result.success = False

            # Emit workflow failure
            if self.emitter:
                self.emitter.emit(
                    event_type=EventType.WORKFLOW_FAILED,
                    component="specialized-roles-orchestrator",
                    message=f"Workflow failed: {str(e)}",
                    severity=EventSeverity.ERROR,
                    workflow="specialized_roles",
                    error=str(e),
                    stack_trace=traceback.format_exc()
                )

        finally:
            result.completed_at = datetime.now()

        # Print summary
        print(f"\n{result.get_summary()}")

        # End workflow trace and emit final metrics
        if self.emitter:
            self.emitter.end_trace(
                success=result.success,
                result={
                    "overall_quality_score": result.overall_quality_score,
                    "total_cost": result.total_cost_usd,
                    "phases_completed": [p.value for p in result.completed_phases]
                }
            )

            # Emit aggregated cost
            if result.total_cost_usd:
                self.emitter.emit(
                    event_type=EventType.COST_INCURRED,
                    component="specialized-roles-orchestrator",
                    message=f"Total workflow cost: ${result.total_cost_usd:.4f}",
                    severity=EventSeverity.INFO,
                    cost_usd=result.total_cost_usd,
                    data={"phases": len(result.completed_phases)}
                )

            # Emit final quality score
            if result.overall_quality_score:
                self.emitter.emit(
                    event_type=EventType.QUALITY_MEASURED,
                    component="specialized-roles-orchestrator",
                    message=f"Final quality score: {result.overall_quality_score}/100",
                    severity=EventSeverity.INFO,
                    quality_score=float(result.overall_quality_score),
                    data={
                        "threshold": threshold,
                        "success": result.success
                    }
                )

        return result

    def _execute_phase(self,
                      phase: WorkflowPhase,
                      task: str,
                      context: Dict[str, Any],
                      previous_results: Dict[str, str]) -> PhaseResult:
        """Execute a single workflow phase."""
        role_type = RoleType(phase.value)
        role = get_role(role_type)
        agent = self.agents[role_type]

        # Build prompt for this phase
        prompt = self._build_phase_prompt(phase, task, context, previous_results)

        print(f"Executing {role.name} phase...")
        print(f"Model: {role.primary_model}")
        print(f"Temperature: {role.temperature}")

        start_time = time.time()

        try:
            # Call agent (uses ResilientBaseAgent with automatic fallback)
            call_result: CallResult = agent.call(prompt)

            execution_time_ms = (time.time() - start_time) * 1000

            if call_result.success:
                print(f"✅ {role.name} phase completed successfully")
                print(f"   Model used: {call_result.model_used}")
                print(f"   Execution time: {execution_time_ms/1000:.2f}s")
                print(f"   Cost: ${call_result.cost:.6f}")

                return PhaseResult(
                    phase=phase,
                    role=role,
                    output=call_result.output,
                    success=True,
                    execution_time_ms=execution_time_ms,
                    tokens_used=call_result.total_tokens,
                    cost_usd=call_result.cost,
                    model_used=call_result.model_used,
                    iteration=1
                )
            else:
                print(f"❌ {role.name} phase failed: {call_result.error}")
                return PhaseResult(
                    phase=phase,
                    role=role,
                    output="",
                    success=False,
                    execution_time_ms=execution_time_ms,
                    tokens_used=0,
                    cost_usd=0.0,
                    model_used=call_result.model_used or "unknown",
                    error=call_result.error,
                    iteration=1
                )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            print(f"❌ {role.name} phase exception: {e}")
            return PhaseResult(
                phase=phase,
                role=role,
                output="",
                success=False,
                execution_time_ms=execution_time_ms,
                tokens_used=0,
                cost_usd=0.0,
                model_used="unknown",
                error=str(e),
                iteration=1
            )

    def _build_phase_prompt(self,
                           phase: WorkflowPhase,
                           task: str,
                           context: Dict[str, Any],
                           previous_results: Dict[str, str]) -> str:
        """Build prompt for a specific phase."""
        role = get_role(RoleType(phase.value))

        prompt_parts = [
            f"TASK: {task}",
            f"\nCONTEXT:",
            json.dumps(context, indent=2),
        ]

        if previous_results:
            prompt_parts.append("\nPREVIOUS PHASE RESULTS:")
            for phase_name, output in previous_results.items():
                prompt_parts.append(f"\n{phase_name.upper()} OUTPUT:")
                prompt_parts.append(output[:5000])  # Limit context size

        prompt_parts.append(f"\n{role.system_prompt}")

        return "\n".join(prompt_parts)

    def _validate_and_correct(self,
                             phase_result: PhaseResult,
                             validation_type: str,
                             threshold: int,
                             context: Dict[str, Any]) -> PhaseResult:
        """Validate phase output and self-correct if needed."""
        if not self.validator:
            return phase_result

        print(f"\n🔍 Validating {phase_result.phase.value} output...")

        # Run appropriate validator
        if validation_type == "code":
            validation_result = self.validator.validate_code(
                code=phase_result.output,
                context=context,
                level="standard"
            )
        elif validation_type == "test":
            validation_result = self.validator.validate_tests(
                tests=phase_result.output,
                context=context,
                level="standard"
            )
        else:
            print(f"⚠️  Unknown validation type: {validation_type}")
            return phase_result

        phase_result.validation_result = validation_result
        phase_result.quality_score = validation_result.score

        print(f"   Quality Score: {validation_result.score}/100")
        print(f"   Status: {validation_result.status}")

        # Check if self-correction needed
        if validation_result.score < threshold and self.enable_self_correction:
            print(f"   ⚠️  Score below threshold ({threshold}). Initiating self-correction...")
            phase_result = self._self_correct_phase(
                phase_result=phase_result,
                validation_result=validation_result,
                threshold=threshold,
                context=context
            )

        return phase_result

    def _self_correct_phase(self,
                           phase_result: PhaseResult,
                           validation_result: ValidationResult,
                           threshold: int,
                           context: Dict[str, Any]) -> PhaseResult:
        """Self-correct a phase output based on validation feedback."""
        iteration = 1

        while iteration <= self.max_self_correction_iterations:
            print(f"\n🔄 Self-correction iteration {iteration}/{self.max_self_correction_iterations}")

            # Build self-correction prompt with validation feedback
            correction_prompt = self._build_correction_prompt(
                phase_result=phase_result,
                validation_result=validation_result,
                threshold=threshold
            )

            # Re-execute with better model (escalate to Opus if not already using it)
            role_type = RoleType(phase_result.phase.value)
            role = get_role(role_type)

            # Escalate model if needed
            escalated_model = self._escalate_model(role.primary_model)
            print(f"   Escalating to model: {escalated_model}")

            # Create temporary agent with escalated model
            corrected_agent = ResilientBaseAgent(
                role=role.name,
                model=escalated_model,
                temperature=role.temperature * 0.8,  # Slightly lower temperature for correction
                max_tokens=role.max_tokens,
                system_prompt=role.system_prompt
            )

            start_time = time.time()
            call_result = corrected_agent.call(correction_prompt)
            execution_time_ms = (time.time() - start_time) * 1000

            if not call_result.success:
                print(f"   ❌ Self-correction failed: {call_result.error}")
                iteration += 1
                continue

            # Validate corrected output
            if phase_result.phase == WorkflowPhase.DEVELOPER:
                new_validation = self.validator.validate_code(
                    code=call_result.output,
                    context=context,
                    level="standard"
                )
            elif phase_result.phase == WorkflowPhase.TESTER:
                new_validation = self.validator.validate_tests(
                    tests=call_result.output,
                    context=context,
                    level="standard"
                )
            else:
                # No validation for other phases
                break

            print(f"   New Quality Score: {new_validation.score}/100")

            if new_validation.score >= threshold:
                print(f"   ✅ Self-correction successful!")

                # Update phase result
                phase_result.output = call_result.output
                phase_result.validation_result = new_validation
                phase_result.quality_score = new_validation.score
                phase_result.iteration = iteration + 1
                phase_result.self_corrected = True
                phase_result.execution_time_ms += execution_time_ms
                phase_result.tokens_used += call_result.total_tokens
                phase_result.cost_usd += call_result.cost

                return phase_result
            else:
                print(f"   ⚠️  Still below threshold. Trying again...")
                validation_result = new_validation
                iteration += 1

        print(f"   ❌ Self-correction failed after {self.max_self_correction_iterations} iterations")
        return phase_result

    def _build_correction_prompt(self,
                                phase_result: PhaseResult,
                                validation_result: ValidationResult,
                                threshold: int) -> str:
        """Build prompt for self-correction."""
        prompt = f"""SELF-CORRECTION REQUIRED

Previous output received quality score of {validation_result.score}/100, below threshold of {threshold}/100.

VALIDATION FINDINGS:
{self._format_validation_findings(validation_result)}

PREVIOUS OUTPUT:
{phase_result.output}

INSTRUCTIONS:
Please revise the output to address all validation findings and achieve a quality score of at least {threshold}/100.

Focus on:
1. Fixing all CRITICAL and HIGH severity issues
2. Addressing MEDIUM severity issues where possible
3. Ensuring output meets all quality criteria
4. Maintaining the same output format (JSON structure)

Provide the COMPLETE revised output (not just the changes).
"""
        return prompt

    def _format_validation_findings(self, validation_result: ValidationResult) -> str:
        """Format validation findings for prompt."""
        lines = []
        for finding in validation_result.findings:
            lines.append(f"- [{finding.severity}] {finding.category}/{finding.subcategory}")
            lines.append(f"  Issue: {finding.issue}")
            lines.append(f"  Recommendation: {finding.recommendation}")
            lines.append("")
        return "\n".join(lines)

    def _escalate_model(self, current_model: str) -> str:
        """Escalate to a better model for self-correction."""
        # Model escalation hierarchy
        if "haiku" in current_model.lower():
            return "claude-3-5-sonnet-20241022"
        elif "sonnet" in current_model.lower():
            return "claude-opus-4-20250514"  # Escalate to Opus 4.1
        elif "opus" in current_model.lower():
            return "gpt-4"  # Try GPT-4 if Opus already used
        else:
            return "claude-opus-4-20250514"  # Default to Opus 4.1

    def _extract_quality_score(self, reviewer_output: str) -> Optional[int]:
        """Extract overall quality score from reviewer output."""
        try:
            # Try to parse as JSON first
            data = json.loads(reviewer_output)
            if 'review_summary' in data and 'overall_quality_score' in data['review_summary']:
                return int(data['review_summary']['overall_quality_score'])

            # Fallback: search for score in text
            import re
            match = re.search(r'"overall_quality_score":\s*(\d+)', reviewer_output)
            if match:
                return int(match.group(1))

            return None
        except Exception as e:
            print(f"⚠️  Could not extract quality score: {e}")
            return None

    def _full_workflow_self_correction(self,
                                      workflow_result: WorkflowResult,
                                      threshold: int) -> WorkflowResult:
        """Self-correct entire workflow if overall quality is low."""
        print(f"\n{'='*80}")
        print(f"FULL WORKFLOW SELF-CORRECTION")
        print(f"{'='*80}")

        # For now, just return the result as-is
        # Full workflow self-correction would involve re-running phases with feedback
        # This is a simplified implementation

        print(f"⚠️  Full workflow self-correction not yet implemented")
        print(f"   Current quality: {workflow_result.overall_quality_score}/100")
        print(f"   Threshold: {threshold}/100")

        return workflow_result


# Example usage
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = SpecializedRolesOrchestrator(
        project_root="/mnt/d/Dev",
        quality_threshold=90,
        enable_validation=True,
        enable_self_correction=True
    )

    # Example workflow
    result = orchestrator.execute_workflow(
        task="Implement a simple user registration API endpoint",
        context={
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "requirements": [
                "Accept email and password",
                "Validate email format",
                "Hash password with bcrypt",
                "Return JWT token on success"
            ]
        }
    )

    print(f"\n{'='*80}")
    print(f"WORKFLOW RESULT")
    print(f"{'='*80}")
    print(f"Success: {result.success}")
    print(f"Quality Score: {result.overall_quality_score}/100")
    print(f"Total Cost: ${result.total_cost_usd:.6f}")
    print(f"Total Time: {result.total_execution_time_ms/1000:.2f}s")
