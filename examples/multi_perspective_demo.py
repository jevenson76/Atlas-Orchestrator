#!/usr/bin/env python3
"""
Multi-Perspective Dialogue System Demo

Demonstrates how multiple LLM models collaborate through constructive
dialogue to produce higher quality outputs for complex tasks.

Key Features:
- Sonnet proposes solutions (fast, FREE)
- Opus challenges and critiques (deep reasoning, FREE)
- Orchestrator manages dialogue flow (autonomous push-back)
- Bounded iterations prevent crippling back-and-forth
- Optional external perspective from Grok for diversity
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_perspective import (
    MultiPerspectiveDialogue,
    detect_task_complexity,
    ConsensusStatus,
    DialogueRole
)
from core.constants import Models
from agent_system import CostTracker


def print_dialogue_turn(turn, show_full=False):
    """Pretty print a dialogue turn."""
    role_icons = {
        DialogueRole.PROPOSER: "💡",
        DialogueRole.CHALLENGER: "🔍",
        DialogueRole.ORCHESTRATOR: "⚖️",
        DialogueRole.MEDIATOR: "🤝"
    }

    icon = role_icons.get(turn.role, "🔹")
    print(f"\n{icon} Turn {turn.turn_number}: {turn.agent_name} ({turn.model})")
    print(f"   Cost: ${turn.cost:.6f} | Tokens: {turn.tokens}")

    if show_full:
        print(f"\n   Prompt:\n   {turn.prompt[:200]}...\n")
        print(f"   Response:\n   {turn.response[:400]}...\n")
    else:
        print(f"   Response: {turn.response[:150]}...")


def example_1_simple_task():
    """Example 1: Simple task doesn't trigger multi-perspective."""

    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Task (No Multi-Perspective Needed)")
    print("="*80)

    task = "Write a Python function to calculate factorial"

    # Check complexity
    is_complex, reason = detect_task_complexity(task)

    print(f"\nTask: {task}")
    print(f"Complex: {is_complex}")
    print(f"Reason: {reason}")

    if is_complex:
        print("\n✅ Task is complex → Use multi-perspective dialogue")
    else:
        print("\n❌ Task is simple → Single model sufficient")
        print("   Recommendation: Use Sonnet 3.5 directly (FREE)")


def example_2_complex_task_dialogue():
    """Example 2: Complex task triggers multi-perspective dialogue."""

    print("\n" + "="*80)
    print("EXAMPLE 2: Complex Task with Multi-Perspective Dialogue")
    print("="*80)

    task = """Design a scalable REST API architecture for a real-time analytics system.
    Requirements:
    - Must handle 10k requests/second
    - Sub-100ms response time
    - Support both batch and streaming data
    - Ensure fault tolerance and horizontal scaling
    - Implement proper authentication and rate limiting"""

    # Check complexity
    is_complex, reason = detect_task_complexity(task)

    print(f"\nTask: {task[:150]}...")
    print(f"\nComplex: {is_complex}")
    print(f"Reason: {reason}")

    if not is_complex:
        print("❌ Task deemed simple, skipping multi-perspective")
        return

    print("\n✅ Task is complex → Initiating multi-perspective dialogue")
    print("\nDialogue Configuration:")
    print("  • Proposer: Sonnet 3.5 (FREE, fast solutions)")
    print("  • Challenger: Opus 4.1 (FREE, deep critique)")
    print("  • Orchestrator: Opus 4.1 (FREE, manages flow)")
    print("  • Max Iterations: 3 (prevents endless debate)")

    # Initialize dialogue system
    dialogue = MultiPerspectiveDialogue(
        proposer_model=Models.SONNET,
        challenger_model=Models.OPUS_4,
        orchestrator_model=Models.OPUS_4,
        max_iterations=3,
        min_quality_threshold=85.0,
        enable_external_perspective=False
    )

    # Execute dialogue
    print("\n" + "-"*80)
    print("Executing Dialogue...")
    print("-"*80)

    result = dialogue.execute(task)

    # Display results
    print("\n" + "="*80)
    print("DIALOGUE RESULTS")
    print("="*80)

    print(f"\n✅ Success: {result.success}")
    print(f"🎯 Consensus: {result.consensus_status.value}")
    print(f"🔄 Iterations: {result.iterations}")
    print(f"💰 Total Cost: ${result.total_cost:.6f} (FREE with Claude Max!)")
    print(f"⏱️  Duration: {result.duration_seconds:.2f}s")
    print(f"📊 Quality: {result.initial_quality:.1f} → {result.final_quality:.1f} (+{result.improvement_percentage:.1f}%)")
    print(f"🤖 Models: {', '.join(result.models_involved)}")

    print(f"\n{'='*80}")
    print("DIALOGUE TRANSCRIPT")
    print("="*80)

    for turn in result.turns:
        print_dialogue_turn(turn, show_full=False)

    print(f"\n{'='*80}")
    print("FINAL OUTPUT")
    print("="*80)
    print(result.final_output[:800] + "...")


def example_3_healthy_vs_crippling():
    """Example 3: Demonstrate healthy dialogue vs crippling back-and-forth."""

    print("\n" + "="*80)
    print("EXAMPLE 3: Healthy Dialogue vs Crippling Back-and-Forth")
    print("="*80)

    task = "Design a caching strategy for a high-traffic web application"

    print("\n🟢 HEALTHY DIALOGUE (Max 3 iterations):")
    print("-" * 80)

    dialogue_healthy = MultiPerspectiveDialogue(
        max_iterations=3,  # Bounded
        min_quality_threshold=85.0
    )

    result_healthy = dialogue_healthy.execute(task)

    print(f"\n   Iterations: {result_healthy.iterations}")
    print(f"   Duration: {result_healthy.duration_seconds:.2f}s")
    print(f"   Quality Improvement: +{result_healthy.improvement_percentage:.1f}%")
    print(f"   Consensus: {result_healthy.consensus_status.value}")
    print(f"   ✅ RESULT: Productive, converged to quality solution")

    print("\n🔴 CRIPPLING DIALOGUE (Unbounded, hypothetical):")
    print("-" * 80)
    print("   Iterations: 10+ (endless refinement)")
    print("   Duration: 120+ seconds")
    print("   Quality Improvement: +2% (diminishing returns)")
    print("   Consensus: Never reached")
    print("   ❌ RESULT: Wasted resources, minimal benefit")

    print("\n💡 KEY DIFFERENCE:")
    print("   • Healthy: Bounded iterations, orchestrator enforces consensus")
    print("   • Crippling: Endless debate, no convergence criteria")
    print("   • Solution: Max 3 iterations + quality threshold")


def example_4_orchestrator_autonomy():
    """Example 4: Show orchestrator pushing back and managing flow."""

    print("\n" + "="*80)
    print("EXAMPLE 4: Orchestrator Autonomy & Push-Back")
    print("="*80)

    task = "Implement a user authentication system with JWT tokens"

    print(f"\nTask: {task}")
    print("\nOrchestrator's Autonomous Decisions:")

    dialogue = MultiPerspectiveDialogue(
        max_iterations=3,
        min_quality_threshold=90.0  # High quality bar
    )

    result = dialogue.execute(task)

    print(f"\nDialogue Flow:")

    orchestrator_decisions = [
        t for t in result.turns
        if t.role == DialogueRole.ORCHESTRATOR
    ]

    for i, decision in enumerate(orchestrator_decisions, 1):
        print(f"\n{i}. Orchestrator Decision (Turn {decision.turn_number}):")
        print(f"   Context: After {i} round(s) of proposal/critique")

        decision_text = decision.response[:200]

        if "REFINE" in decision_text:
            print(f"   Decision: ✅ REFINE - Improvements still possible")
            print(f"   Autonomy: Orchestrator pushed back, requested refinement")
        elif "CONSENSUS" in decision_text:
            print(f"   Decision: ✅ CONSENSUS - Solution meets quality bar")
            print(f"   Autonomy: Orchestrator approved, stopped dialogue")
        else:
            print(f"   Decision: {decision_text[:100]}...")

    print(f"\n🎯 Final Consensus: {result.consensus_status.value}")
    print(f"💡 Key Insight: Orchestrator has full autonomy to:")
    print(f"   • Push back on inadequate solutions")
    print(f"   • Request specific improvements")
    print(f"   • Stop dialogue when quality threshold met")
    print(f"   • Prevent crippling endless refinement")


def example_5_external_perspective():
    """Example 5: Adding external perspective (Grok) for diversity."""

    print("\n" + "="*80)
    print("EXAMPLE 5: External Perspective from Grok (Diversity)")
    print("="*80)

    task = "Design a microservices architecture for an e-commerce platform"

    print(f"\nTask: {task}")
    print("\nDialogue Configuration:")
    print("  • Claude Models: Sonnet (propose) + Opus (challenge) - FREE")
    print("  • External Model: Grok 3 (fresh perspective) - $3/$15")
    print("  • Injection: Round 2 (after initial refinement)")

    dialogue = MultiPerspectiveDialogue(
        proposer_model=Models.SONNET,
        challenger_model=Models.OPUS_4,
        max_iterations=3,
        enable_external_perspective=True,  # Enable Grok
        external_model=Models.GROK_3
    )

    result = dialogue.execute(task)

    print(f"\n{'='*80}")
    print("DIALOGUE FLOW")
    print("="*80)

    for turn in result.turns:
        if "External" in turn.agent_name:
            print(f"\n🌟 {turn.agent_name} ({turn.model}):")
            print(f"   Turn: {turn.turn_number}")
            print(f"   Unique insights: {turn.response[:300]}...")
            print(f"   💰 Cost: ${turn.cost:.6f} (only paid model)")

    print(f"\n💡 Value of External Perspective:")
    print(f"   • Breaks Claude echo chamber")
    print(f"   • Brings unique insights (real-time search, different training)")
    print(f"   • Minimal cost: Only 1 call per dialogue (~$0.01)")
    print(f"   • Total cost: ${result.total_cost:.6f} (mostly FREE Claude)")


def example_6_cost_analysis():
    """Example 6: Cost analysis of multi-perspective vs single model."""

    print("\n" + "="*80)
    print("EXAMPLE 6: Cost Analysis - Multi-Perspective vs Single Model")
    print("="*80)

    task = "Design a distributed caching layer for a global application"

    # Single model approach (Opus only)
    print("\n🔹 Approach A: Single Model (Opus 4.1)")
    print("   Calls: 1 Opus call")
    print("   Cost: $0.00 (FREE with Claude Max)")
    print("   Quality: ~80/100 (one perspective)")

    # Multi-perspective approach (Sonnet + Opus dialogue)
    print("\n🔹 Approach B: Multi-Perspective (Sonnet + Opus)")

    dialogue = MultiPerspectiveDialogue(
        proposer_model=Models.SONNET,
        challenger_model=Models.OPUS_4,
        max_iterations=2
    )

    result = dialogue.execute(task)

    claude_calls = len([t for t in result.turns if "claude" in t.model.lower()])

    print(f"   Calls: {claude_calls} Claude calls (Sonnet + Opus)")
    print(f"   Cost: ${result.total_cost:.6f} (FREE with Claude Max)")
    print(f"   Quality: {result.final_quality:.1f}/100 (+{result.improvement_percentage:.1f}% improvement)")

    # With external perspective
    print("\n🔹 Approach C: Multi-Perspective + External (Sonnet + Opus + Grok)")

    dialogue_ext = MultiPerspectiveDialogue(
        proposer_model=Models.SONNET,
        challenger_model=Models.OPUS_4,
        max_iterations=2,
        enable_external_perspective=True,
        external_model=Models.GROK_3
    )

    result_ext = dialogue_ext.execute(task)

    grok_cost = sum(t.cost for t in result_ext.turns if "grok" in t.model.lower())

    print(f"   Calls: {len(result_ext.turns)} total (Claude FREE + 1 Grok)")
    print(f"   Cost: ${result_ext.total_cost:.6f} (mostly FREE, ~${grok_cost:.6f} for Grok)")
    print(f"   Quality: {result_ext.final_quality:.1f}/100 (diverse perspectives)")

    print("\n💰 COST SUMMARY:")
    print(f"   Approach A: $0.00 (single model)")
    print(f"   Approach B: $0.00 (multi-Claude)")
    print(f"   Approach C: ~${result_ext.total_cost:.6f} (multi-Claude + Grok)")

    print("\n💡 INSIGHT:")
    print(f"   With Claude Max, multi-perspective dialogue is FREE!")
    print(f"   Higher quality through debate at zero additional cost")
    print(f"   Optional Grok adds diversity for ~$0.01 per task")


def main():
    """Run all examples."""

    print("\n" + "="*80)
    print("🌐 ZEROTOUCH ATLAS - Multi-Perspective Dialogue System")
    print("="*80)
    print("\nDemonstrating collaborative dialogue between LLM models")
    print("for higher quality outputs on complex tasks.")

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--example", type=int, choices=range(1, 7),
                       help="Run specific example (1-6)")
    args = parser.parse_args()

    examples = {
        1: ("Simple Task Detection", example_1_simple_task),
        2: ("Complex Task Dialogue", example_2_complex_task_dialogue),
        3: ("Healthy vs Crippling", example_3_healthy_vs_crippling),
        4: ("Orchestrator Autonomy", example_4_orchestrator_autonomy),
        5: ("External Perspective", example_5_external_perspective),
        6: ("Cost Analysis", example_6_cost_analysis)
    }

    if args.example:
        name, func = examples[args.example]
        print(f"\nRunning: {name}")
        func()
    else:
        for num, (name, func) in examples.items():
            func()

    print("\n" + "="*80)
    print("✅ Demo Complete")
    print("="*80)

    print("\n💡 KEY TAKEAWAYS:")
    print("\n1. Complexity Detection:")
    print("   • Auto-detect when tasks need multiple perspectives")
    print("   • Simple tasks → Single model (Sonnet)")
    print("   • Complex tasks → Multi-perspective dialogue")

    print("\n2. Healthy Dialogue Pattern:")
    print("   • Sonnet proposes (fast, FREE)")
    print("   • Opus challenges (deep, FREE)")
    print("   • Orchestrator manages (autonomous, FREE)")
    print("   • Bounded iterations (max 3, prevents loops)")

    print("\n3. Orchestrator Autonomy:")
    print("   • Full authority to push back")
    print("   • Requests specific improvements")
    print("   • Enforces quality thresholds")
    print("   • Stops when consensus reached")

    print("\n4. Cost with Claude Max:")
    print("   • Multi-Claude dialogue: $0.00 (100% FREE)")
    print("   • Optional Grok perspective: ~$0.01/task")
    print("   • Higher quality at zero cost!")

    print("\n5. Preventing Crippling Loops:")
    print("   • Max iterations: 3 (configurable)")
    print("   • Quality threshold: Stop when met")
    print("   • Diminishing returns detection")
    print("   • Orchestrator consensus enforcement")


if __name__ == "__main__":
    main()
