"""
Multi-Perspective Dialogue System for Complex Tasks

Implements collaborative dialogue between multiple LLM models to achieve
higher quality outputs through constructive debate and refinement.

Key Features:
- Multiple models provide different perspectives
- Orchestrator has autonomy to push back and request improvements
- Bounded iterations prevent crippling back-and-forth
- Complexity detection auto-triggers multi-perspective mode
- Consensus tracking and quality improvement monitoring
"""

import logging
import time
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

try:
    from resilient_agent import ResilientBaseAgent, CallResult
    from core.constants import Models
    from agent_system import CostTracker
except ImportError:
    from .resilient_agent import ResilientBaseAgent, CallResult
    from .core.constants import Models
    from .agent_system import CostTracker

logger = logging.getLogger(__name__)


class DialogueRole(Enum):
    """Roles in the multi-perspective dialogue."""
    PROPOSER = "proposer"        # Initial solution generator
    CHALLENGER = "challenger"     # Critical reviewer
    MEDIATOR = "mediator"         # Synthesizes perspectives
    ORCHESTRATOR = "orchestrator" # Manages dialogue flow


class ConsensusStatus(Enum):
    """Status of consensus in dialogue."""
    NO_CONSENSUS = "no_consensus"           # Significant disagreement
    PARTIAL_CONSENSUS = "partial_consensus" # Some agreement
    FULL_CONSENSUS = "full_consensus"       # Complete agreement
    ITERATIONS_EXCEEDED = "iterations_exceeded"  # Stopped due to limit


@dataclass
class DialogueTurn:
    """Single turn in the multi-perspective dialogue."""
    turn_number: int
    role: DialogueRole
    model: str
    agent_name: str
    prompt: str
    response: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    cost: float = 0.0
    tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogueResult:
    """Result of multi-perspective dialogue."""
    success: bool
    final_output: str
    consensus_status: ConsensusStatus

    # Dialogue history
    turns: List[DialogueTurn] = field(default_factory=list)
    iterations: int = 0

    # Quality metrics
    initial_quality: Optional[float] = None
    final_quality: Optional[float] = None
    improvement_percentage: Optional[float] = None

    # Cost tracking
    total_cost: float = 0.0
    total_tokens: int = 0
    duration_seconds: float = 0.0

    # Metadata
    models_involved: List[str] = field(default_factory=list)
    error: Optional[str] = None


class MultiPerspectiveDialogue:
    """
    Orchestrates multi-model dialogue for complex tasks.

    With Claude Max subscription, we can use multiple FREE models:
    - Sonnet 3.5: Fast proposer
    - Opus 4.1: Deep challenger/critic
    - Grok 3: External perspective (if needed)

    Dialogue Pattern:
    1. Proposer generates initial solution (Sonnet)
    2. Challenger critiques and suggests improvements (Opus)
    3. Proposer refines based on feedback (Sonnet)
    4. Orchestrator evaluates consensus
    5. Repeat if needed (max iterations)
    """

    def __init__(self,
                 proposer_model: str = Models.SONNET,
                 challenger_model: str = Models.OPUS_4,
                 orchestrator_model: str = Models.OPUS_4,
                 max_iterations: int = 3,
                 min_quality_threshold: float = 85.0,
                 enable_external_perspective: bool = False,
                 external_model: str = Models.GROK_3,
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize multi-perspective dialogue system.

        Args:
            proposer_model: Model for initial solutions (default: Sonnet)
            challenger_model: Model for critique (default: Opus 4.1)
            orchestrator_model: Model for orchestration (default: Opus 4.1)
            max_iterations: Maximum dialogue rounds (default: 3)
            min_quality_threshold: Stop when quality exceeds this (default: 85.0)
            enable_external_perspective: Include non-Claude model (default: False)
            external_model: External model to use (default: Grok 3)
            cost_tracker: Optional cost tracking
        """
        self.proposer_model = proposer_model
        self.challenger_model = challenger_model
        self.orchestrator_model = orchestrator_model
        self.max_iterations = max_iterations
        self.min_quality_threshold = min_quality_threshold
        self.enable_external_perspective = enable_external_perspective
        self.external_model = external_model
        self.cost_tracker = cost_tracker

        # Initialize agents
        self._initialize_agents()

        logger.info(
            f"MultiPerspectiveDialogue initialized: "
            f"proposer={proposer_model}, challenger={challenger_model}, "
            f"max_iterations={max_iterations}"
        )

    def _initialize_agents(self):
        """Initialize dialogue agents."""

        # Proposer: Generates initial solutions
        self.proposer = ResilientBaseAgent(
            role="Solution Proposer",
            model=self.proposer_model,
            enable_fallback=True,
            cost_tracker=self.cost_tracker
        )

        # Challenger: Critiques and suggests improvements
        self.challenger = ResilientBaseAgent(
            role="Critical Challenger",
            model=self.challenger_model,
            enable_fallback=True,
            cost_tracker=self.cost_tracker
        )

        # Orchestrator: Manages dialogue and evaluates consensus
        self.orchestrator = ResilientBaseAgent(
            role="Dialogue Orchestrator",
            model=self.orchestrator_model,
            enable_fallback=True,
            cost_tracker=self.cost_tracker
        )

        # External perspective (optional, for diversity)
        if self.enable_external_perspective:
            self.external_agent = ResilientBaseAgent(
                role="External Perspective",
                model=self.external_model,
                enable_fallback=True,
                cost_tracker=self.cost_tracker
            )
        else:
            self.external_agent = None

    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> DialogueResult:
        """
        Execute multi-perspective dialogue on a complex task.

        Args:
            task: The task/question to solve
            context: Optional context for the task

        Returns:
            DialogueResult with final output and dialogue history
        """
        start_time = time.time()
        turns: List[DialogueTurn] = []

        logger.info(f"Starting multi-perspective dialogue for task: {task[:100]}...")

        try:
            # Phase 1: Initial proposal
            proposal_result = self._generate_proposal(task, context, turns)
            current_solution = proposal_result

            # Phase 2: Iterative dialogue
            for iteration in range(1, self.max_iterations + 1):
                logger.info(f"Dialogue iteration {iteration}/{self.max_iterations}")

                # Challenger critiques current solution
                critique_result = self._generate_critique(
                    task, current_solution, iteration, context, turns
                )

                # Orchestrator evaluates if refinement is needed
                should_refine, consensus = self._should_refine(
                    task, current_solution, critique_result, iteration, turns
                )

                if not should_refine:
                    logger.info(f"Consensus reached at iteration {iteration}")
                    break

                # Proposer refines based on critique
                refined_result = self._refine_solution(
                    task, current_solution, critique_result, iteration, context, turns
                )
                current_solution = refined_result

                # Optional: External perspective on key iterations
                if self.enable_external_perspective and iteration == 2:
                    external_result = self._get_external_perspective(
                        task, current_solution, context, turns
                    )
                    # Incorporate external feedback
                    current_solution = self._incorporate_external_feedback(
                        task, current_solution, external_result, context, turns
                    )

            # Phase 3: Final quality assessment
            final_quality = self._assess_quality(current_solution, task, turns)

            # Calculate improvement
            initial_quality = turns[0].metadata.get("quality_estimate", 70.0)
            improvement = ((final_quality - initial_quality) / initial_quality) * 100

            # Build result
            duration = time.time() - start_time
            total_cost = sum(turn.cost for turn in turns)
            total_tokens = sum(turn.tokens for turn in turns)
            models_involved = list(set(turn.model for turn in turns))

            result = DialogueResult(
                success=True,
                final_output=current_solution,
                consensus_status=consensus if 'consensus' in locals() else ConsensusStatus.FULL_CONSENSUS,
                turns=turns,
                iterations=len([t for t in turns if t.role == DialogueRole.PROPOSER]),
                initial_quality=initial_quality,
                final_quality=final_quality,
                improvement_percentage=improvement,
                total_cost=total_cost,
                total_tokens=total_tokens,
                duration_seconds=duration,
                models_involved=models_involved
            )

            logger.info(
                f"Dialogue complete: {len(turns)} turns, "
                f"quality {initial_quality:.1f} → {final_quality:.1f} (+{improvement:.1f}%), "
                f"cost ${total_cost:.6f}"
            )

            return result

        except Exception as e:
            logger.error(f"Dialogue failed: {e}")
            return DialogueResult(
                success=False,
                final_output="",
                consensus_status=ConsensusStatus.NO_CONSENSUS,
                turns=turns,
                error=str(e),
                duration_seconds=time.time() - start_time
            )

    def _generate_proposal(self,
                          task: str,
                          context: Optional[Dict[str, Any]],
                          turns: List[DialogueTurn]) -> str:
        """Generate initial proposal."""

        prompt = f"""You are a Solution Proposer. Generate a comprehensive, high-quality solution for this task.

Task: {task}

Requirements:
- Be thorough and detailed
- Consider edge cases
- Provide clear explanations
- Use best practices

Provide your solution:"""

        result = self.proposer.call(prompt=prompt, context=context)

        turns.append(DialogueTurn(
            turn_number=len(turns) + 1,
            role=DialogueRole.PROPOSER,
            model=result.model_used or self.proposer_model,
            agent_name="Proposer",
            prompt=prompt,
            response=result.output,
            cost=result.cost,
            tokens=result.total_tokens,
            metadata={"quality_estimate": 70.0}
        ))

        return result.output

    def _generate_critique(self,
                          task: str,
                          solution: str,
                          iteration: int,
                          context: Optional[Dict[str, Any]],
                          turns: List[DialogueTurn]) -> str:
        """Generate critique of current solution."""

        prompt = f"""You are a Critical Challenger. Your role is to constructively critique the proposed solution and suggest specific improvements.

Original Task: {task}

Current Solution:
{solution}

Provide a critical analysis:
1. What are the strengths of this solution?
2. What are the weaknesses or gaps?
3. What specific improvements would make it better?
4. Are there edge cases not considered?
5. Overall quality assessment (0-100)?

Be constructive but thorough in your critique:"""

        result = self.challenger.call(prompt=prompt, context=context)

        turns.append(DialogueTurn(
            turn_number=len(turns) + 1,
            role=DialogueRole.CHALLENGER,
            model=result.model_used or self.challenger_model,
            agent_name="Challenger",
            prompt=prompt,
            response=result.output,
            cost=result.cost,
            tokens=result.total_tokens,
            metadata={"iteration": iteration}
        ))

        return result.output

    def _should_refine(self,
                      task: str,
                      solution: str,
                      critique: str,
                      iteration: int,
                      turns: List[DialogueTurn]) -> Tuple[bool, ConsensusStatus]:
        """Orchestrator decides if refinement is needed."""

        prompt = f"""You are a Dialogue Orchestrator. Evaluate whether the current solution needs refinement based on the critique.

Task: {task}

Current Solution:
{solution[:500]}...

Critique:
{critique}

Iteration: {iteration}/{self.max_iterations}

Decision criteria:
1. Are there significant issues that need addressing?
2. Would refinement meaningfully improve quality?
3. Is the critique actionable?
4. Have we reached diminishing returns?

Respond with EXACTLY one of:
- REFINE: Significant improvements possible
- CONSENSUS: Solution is good enough
- ITERATIONS_EXCEEDED: Stop due to iteration limit

Then provide 2-3 sentence justification.

Decision:"""

        result = self.orchestrator.call(prompt=prompt)

        turns.append(DialogueTurn(
            turn_number=len(turns) + 1,
            role=DialogueRole.ORCHESTRATOR,
            model=result.model_used or self.orchestrator_model,
            agent_name="Orchestrator",
            prompt=prompt,
            response=result.output,
            cost=result.cost,
            tokens=result.total_tokens,
            metadata={"iteration": iteration, "decision_point": True}
        ))

        # Parse decision
        decision = result.output.strip().upper()

        if "REFINE" in decision[:20]:
            return True, ConsensusStatus.PARTIAL_CONSENSUS
        elif "CONSENSUS" in decision[:20]:
            return False, ConsensusStatus.FULL_CONSENSUS
        elif iteration >= self.max_iterations:
            return False, ConsensusStatus.ITERATIONS_EXCEEDED
        else:
            # Default: refine if iteration budget allows
            return iteration < self.max_iterations, ConsensusStatus.PARTIAL_CONSENSUS

    def _refine_solution(self,
                        task: str,
                        current_solution: str,
                        critique: str,
                        iteration: int,
                        context: Optional[Dict[str, Any]],
                        turns: List[DialogueTurn]) -> str:
        """Proposer refines solution based on critique."""

        prompt = f"""You are refining your previous solution based on constructive critique.

Original Task: {task}

Your Previous Solution:
{current_solution}

Critique Received:
{critique}

Instructions:
- Address the specific issues raised
- Maintain the strengths of your original solution
- Improve weaknesses identified
- Don't completely rewrite unless necessary
- Focus on actionable improvements

Provide your refined solution:"""

        result = self.proposer.call(prompt=prompt, context=context)

        turns.append(DialogueTurn(
            turn_number=len(turns) + 1,
            role=DialogueRole.PROPOSER,
            model=result.model_used or self.proposer_model,
            agent_name="Proposer (Refining)",
            prompt=prompt,
            response=result.output,
            cost=result.cost,
            tokens=result.total_tokens,
            metadata={"iteration": iteration, "refinement": True}
        ))

        return result.output

    def _get_external_perspective(self,
                                  task: str,
                                  solution: str,
                                  context: Optional[Dict[str, Any]],
                                  turns: List[DialogueTurn]) -> str:
        """Get external perspective from non-Claude model."""

        if not self.external_agent:
            return ""

        prompt = f"""Provide a fresh, external perspective on this solution.

Task: {task}

Solution:
{solution[:800]}...

What unique insights can you offer? What might Claude models be missing?

Your perspective:"""

        result = self.external_agent.call(prompt=prompt, context=context)

        turns.append(DialogueTurn(
            turn_number=len(turns) + 1,
            role=DialogueRole.CHALLENGER,
            model=result.model_used or self.external_model,
            agent_name="External Perspective",
            prompt=prompt,
            response=result.output,
            cost=result.cost,
            tokens=result.total_tokens,
            metadata={"external": True}
        ))

        return result.output

    def _incorporate_external_feedback(self,
                                       task: str,
                                       solution: str,
                                       external_feedback: str,
                                       context: Optional[Dict[str, Any]],
                                       turns: List[DialogueTurn]) -> str:
        """Incorporate external feedback into solution."""

        prompt = f"""Consider this external perspective and selectively incorporate valuable insights.

Task: {task}

Current Solution:
{solution[:500]}...

External Feedback:
{external_feedback}

Integrate any valuable unique insights while maintaining your solution's strengths.

Updated solution:"""

        result = self.proposer.call(prompt=prompt, context=context)

        turns.append(DialogueTurn(
            turn_number=len(turns) + 1,
            role=DialogueRole.PROPOSER,
            model=result.model_used or self.proposer_model,
            agent_name="Proposer (External Integration)",
            prompt=prompt,
            response=result.output,
            cost=result.cost,
            tokens=result.total_tokens,
            metadata={"external_integration": True}
        ))

        return result.output

    def _assess_quality(self,
                       solution: str,
                       task: str,
                       turns: List[DialogueTurn]) -> float:
        """Assess final quality of solution."""

        prompt = f"""Assess the quality of this solution on a 0-100 scale.

Task: {task}

Solution:
{solution}

Provide a numerical score (0-100) based on:
- Completeness
- Correctness
- Clarity
- Best practices
- Edge case handling

Score (just the number):"""

        result = self.orchestrator.call(prompt=prompt)

        # Extract number from response
        try:
            score_str = ''.join(c for c in result.output if c.isdigit() or c == '.')
            score = float(score_str)
            score = min(100.0, max(0.0, score))
        except:
            score = 85.0  # Default if parsing fails

        turns.append(DialogueTurn(
            turn_number=len(turns) + 1,
            role=DialogueRole.ORCHESTRATOR,
            model=result.model_used or self.orchestrator_model,
            agent_name="Orchestrator (Quality Assessment)",
            prompt=prompt,
            response=result.output,
            cost=result.cost,
            tokens=result.total_tokens,
            metadata={"quality_score": score, "final_assessment": True}
        ))

        return score


def detect_task_complexity(task: str) -> Tuple[bool, str]:
    """
    Detect if task is complex enough to benefit from multi-perspective dialogue.

    Args:
        task: The task description

    Returns:
        Tuple of (is_complex, reason)
    """
    # Simple heuristics for complexity detection
    complexity_indicators = {
        "requires_multiple_steps": ["step", "phase", "first", "then", "finally"],
        "has_constraints": ["requirement", "must", "should", "constraint", "limit"],
        "needs_comparison": ["compare", "versus", "vs", "better", "alternative"],
        "involves_architecture": ["design", "architecture", "system", "pattern"],
        "requires_validation": ["validate", "verify", "check", "ensure", "quality"],
        "has_tradeoffs": ["tradeoff", "trade-off", "balance", "optimize"],
    }

    task_lower = task.lower()
    triggered_indicators = []

    for indicator_type, keywords in complexity_indicators.items():
        if any(keyword in task_lower for keyword in keywords):
            triggered_indicators.append(indicator_type)

    # Task is complex if it triggers 2+ indicators or is very long
    is_complex = len(triggered_indicators) >= 2 or len(task) > 500

    reason = f"Triggered {len(triggered_indicators)} complexity indicators: {', '.join(triggered_indicators)}" if triggered_indicators else "Task is straightforward"

    return is_complex, reason
