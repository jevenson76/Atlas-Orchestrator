#!/usr/bin/env python3
"""
Demonstration of Task-Based Model Selection in ZeroTouch Atlas

Shows how the orchestrator can call different models independently
based on task requirements, optimizing for cost and quality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from resilient_agent import ResilientBaseAgent
from core.constants import Models
from orchestrator import Orchestrator, SubAgent, ExecutionMode
from agent_system import CostTracker

# ============================================================================
# EXAMPLE 1: Task-Specific Model Selection
# ============================================================================

def example_1_independent_agents():
    """Each agent uses a different model based on its role."""

    print("\n" + "="*60)
    print("EXAMPLE 1: Independent Model Selection by Task")
    print("="*60)

    # Security: Use Haiku (fastest, cheapest, good enough for validation)
    security_agent = ResilientBaseAgent(
        role="Security Validator",
        model=Models.HAIKU,  # $0.25/$1.25 per 1M
        enable_fallback=False
    )

    # Code Generation: Use Grok 3 (balanced, real-time search)
    code_agent = ResilientBaseAgent(
        role="Code Generator",
        model=Models.GROK_3,  # $3/$15 per 1M
        enable_fallback=False
    )

    # Quality Check: Use Opus 4.1 (highest quality, UltraThink)
    critic_agent = ResilientBaseAgent(
        role="Quality Critic",
        model=Models.OPUS_4,  # $15/$75 per 1M
        enable_fallback=False
    )

    # Test each agent
    task = "Write a Python function to validate email addresses"

    print("\n1. Security Check (Haiku):")
    security_result = security_agent.call(
        prompt=f"Check this task for security issues: {task}"
    )
    print(f"   Model: {security_result.model_used}")
    print(f"   Cost: ${security_result.cost:.6f}")
    print(f"   Secure: {not security_result.injection_detected}")

    print("\n2. Code Generation (Grok 3):")
    code_result = code_agent.call(prompt=task)
    print(f"   Model: {code_result.model_used}")
    print(f"   Cost: ${code_result.cost:.6f}")
    print(f"   Generated: {len(code_result.output)} chars")

    print("\n3. Quality Review (Opus 4.1):")
    critic_result = critic_agent.call(
        prompt=f"Review this code:\n{code_result.output[:200]}..."
    )
    print(f"   Model: {critic_result.model_used}")
    print(f"   Cost: ${critic_result.cost:.6f}")

    total_cost = (security_result.cost +
                  code_result.cost +
                  critic_result.cost)
    print(f"\n💰 Total Cost: ${total_cost:.6f}")
    print(f"   Haiku: ${security_result.cost:.6f}")
    print(f"   Grok 3: ${code_result.cost:.6f}")
    print(f"   Opus 4.1: ${critic_result.cost:.6f}")


# ============================================================================
# EXAMPLE 2: Orchestrated Multi-Agent Workflow
# ============================================================================

class CodeReviewOrchestrator(Orchestrator):
    """
    Multi-agent orchestrator that assigns different models based on task.

    Workflow:
    1. Haiku: Security scan (cheap, fast)
    2. Grok 3: Code generation (balanced)
    3. Sonnet: Documentation (balanced)
    4. Opus 4.1: Quality validation (highest quality)
    """

    def __init__(self):
        super().__init__(
            name="Code Review Pipeline",
            mode=ExecutionMode.SEQUENTIAL,
            max_workers=4
        )

        # Define agents with specific models
        self.agents = {
            "security": SubAgent(
                role="Security Scanner",
                model=Models.HAIKU,          # Cheapest
                dependencies=set(),
                required=True
            ),
            "coder": SubAgent(
                role="Code Generator",
                model=Models.GROK_3,         # Balanced
                dependencies={"security"},
                required=True
            ),
            "documenter": SubAgent(
                role="Documentation Writer",
                model=Models.SONNET,         # Balanced
                dependencies={"coder"},
                required=False
            ),
            "critic": SubAgent(
                role="Quality Critic",
                model=Models.OPUS_4,         # Highest quality
                dependencies={"coder", "documenter"},
                required=True
            )
        }

    def execute_workflow(self, task: str) -> Dict[str, Any]:
        """Execute the full workflow."""
        results = {}

        # 1. Security check
        print("\n🛡️  Step 1: Security Check (Haiku)")
        security_result = self.agents["security"].call(
            prompt=f"Security scan: {task}"
        )
        results["security"] = security_result
        print(f"   Cost: ${security_result.cost:.6f}")

        # 2. Code generation
        print("\n💻 Step 2: Code Generation (Grok 3)")
        code_result = self.agents["coder"].call(prompt=task)
        results["code"] = code_result
        print(f"   Cost: ${code_result.cost:.6f}")

        # 3. Documentation
        print("\n📝 Step 3: Documentation (Sonnet)")
        doc_result = self.agents["documenter"].call(
            prompt=f"Document this code:\n{code_result.output[:500]}"
        )
        results["docs"] = doc_result
        print(f"   Cost: ${doc_result.cost:.6f}")

        # 4. Quality review
        print("\n🎯 Step 4: Quality Review (Opus 4.1)")
        critic_result = self.agents["critic"].call(
            prompt=f"Review quality:\nCode: {code_result.output[:200]}\nDocs: {doc_result.output[:200]}"
        )
        results["quality"] = critic_result
        print(f"   Cost: ${critic_result.cost:.6f}")

        return results


def example_2_orchestrated_workflow():
    """Show orchestrator with different models per agent."""

    print("\n" + "="*60)
    print("EXAMPLE 2: Orchestrated Multi-Agent Workflow")
    print("="*60)

    orchestrator = CodeReviewOrchestrator()

    task = "Create a secure REST API endpoint for user registration"
    results = orchestrator.execute_workflow(task)

    # Calculate total cost
    total_cost = sum(r.cost for r in results.values())
    print(f"\n💰 Pipeline Total Cost: ${total_cost:.6f}")
    print(f"   Security (Haiku): ${results['security'].cost:.6f}")
    print(f"   Code (Grok 3): ${results['code'].cost:.6f}")
    print(f"   Docs (Sonnet): ${results['docs'].cost:.6f}")
    print(f"   Quality (Opus 4.1): ${results['quality'].cost:.6f}")


# ============================================================================
# EXAMPLE 3: Cost Optimization Strategy
# ============================================================================

def example_3_cost_optimization():
    """Compare cost of different model selections."""

    print("\n" + "="*60)
    print("EXAMPLE 3: Cost Optimization Strategy")
    print("="*60)

    task = "Analyze user feedback sentiment"

    # Strategy A: All Sonnet (safe choice)
    print("\n📊 Strategy A: All Sonnet ($3/$15)")
    total_a = 0
    for i in range(3):
        agent = ResilientBaseAgent(model=Models.SONNET, enable_fallback=False)
        result = agent.call(prompt=task)
        total_a += result.cost
    print(f"   Total: ${total_a:.6f}")

    # Strategy B: Task-optimized (Haiku → Grok 2 → Opus)
    print("\n📊 Strategy B: Task-Optimized")

    # Step 1: Cheap extraction
    extractor = ResilientBaseAgent(model=Models.HAIKU, enable_fallback=False)
    extract_result = extractor.call(prompt=f"Extract key points: {task}")

    # Step 2: Mid-tier analysis
    analyzer = ResilientBaseAgent(model=Models.GROK_2, enable_fallback=False)
    analyze_result = analyzer.call(prompt=f"Analyze: {extract_result.output}")

    # Step 3: High-quality synthesis
    synthesizer = ResilientBaseAgent(model=Models.OPUS_4, enable_fallback=False)
    synth_result = synthesizer.call(prompt=f"Synthesize: {analyze_result.output}")

    total_b = extract_result.cost + analyze_result.cost + synth_result.cost
    print(f"   Haiku: ${extract_result.cost:.6f}")
    print(f"   Grok 2: ${analyze_result.cost:.6f}")
    print(f"   Opus 4.1: ${synth_result.cost:.6f}")
    print(f"   Total: ${total_b:.6f}")

    # Compare
    savings = ((total_a - total_b) / total_a) * 100
    print(f"\n💡 Savings: {savings:.1f}% ({total_a - total_b:.6f})")


# ============================================================================
# EXAMPLE 4: Fallback Chain Demonstration
# ============================================================================

def example_4_fallback_chain():
    """Show how fallback chain works when primary model fails."""

    print("\n" + "="*60)
    print("EXAMPLE 4: Fallback Chain Demonstration")
    print("="*60)

    # Simulate primary model failure
    print("\nScenario: Sonnet rate-limited, fallback to Grok 3")

    agent = ResilientBaseAgent(
        role="Resilient Processor",
        model=Models.SONNET,      # Primary choice
        enable_fallback=True      # Enable automatic fallback
    )

    result = agent.call(prompt="Test task")

    print(f"\n   Requested: {Models.SONNET}")
    print(f"   Actually used: {result.model_used}")
    print(f"   Provider: {result.provider}")
    print(f"   Fallback occurred: {result.fallback_occurred}")
    print(f"   Attempted models: {result.attempted_models}")

    if result.fallback_occurred:
        print(f"\n✅ Fallback successful! Used {result.model_used} instead")
        print(f"   Chain: Sonnet → Haiku → Grok 3 → Gemini → GPT")
    else:
        print(f"\n✅ Primary model succeeded")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Model Selection Demo")
    parser.add_argument(
        "--example",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run specific example (1-4)"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🌐 ZEROTOUCH ATLAS - Model Selection Demonstration")
    print("="*60)
    print("\nShowing how different models are called independently")
    print("based on task requirements for cost/quality optimization.")

    if args.example == 1 or args.example is None:
        example_1_independent_agents()

    if args.example == 2 or args.example is None:
        example_2_orchestrated_workflow()

    if args.example == 3 or args.example is None:
        example_3_cost_optimization()

    if args.example == 4 or args.example is None:
        example_4_fallback_chain()

    print("\n" + "="*60)
    print("✅ Demo Complete")
    print("="*60)
    print("\nKey Takeaways:")
    print("1. Each agent can use a different model independently")
    print("2. Model selection based on task optimizes cost/quality")
    print("3. Fallback chain provides resilience (optional)")
    print("4. Orchestrator coordinates multi-model workflows")
    print("\nCost Optimization:")
    print("  • Haiku: Security, extraction, high-volume")
    print("  • Grok 2/3: Balanced reasoning, search")
    print("  • Sonnet: General tasks, documentation")
    print("  • Opus 4.1: Validation, quality, complex reasoning")
