#!/usr/bin/env python3
"""
Output Styles System Demonstrations

Showcases all features of the Output Styles system (C5):
1. OutputStyleManager - Loading and managing styles
2. Style Recommendations - Auto-recommend based on role
3. ResilientBaseAgent Integration - Using styles with agents
4. Agent Registry Integration - Tracking style usage
5. Observability Integration - Style in events
6. A/B Testing - Empirical style comparison

Usage:
    python3 demo_output_styles.py

Or run specific demos:
    python3 demo_output_styles.py --demo 1
    python3 demo_output_styles.py --demo 2,3
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add lib to path
lib_path = Path(__file__).parent
sys.path.insert(0, str(lib_path))

from output_style_manager import OutputStyleManager, get_style_manager
from style_ab_testing import StyleABTest


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def demo_1_style_manager():
    """
    Demo 1: OutputStyleManager - Loading and Managing Styles

    Demonstrates:
    - Initializing manager
    - Registering styles
    - Loading style definitions
    - Listing available styles
    - Getting metadata
    """
    print_section("DEMO 1: OutputStyleManager - Loading and Managing Styles")

    # Initialize manager
    manager = get_style_manager()
    print(f"✅ Initialized OutputStyleManager")
    print(f"   Styles directory: {manager.styles_dir}")
    print(f"   Registry directory: {manager.registry_dir}")

    # List available styles
    print(f"\n📋 Available Styles:")
    styles = manager.list_styles()
    if styles:
        for style in sorted(styles):
            print(f"   - {style}")
    else:
        print("   (No styles registered yet)")
        print("   Run: python3 ~/.claude/lib/register_output_styles.py")

    # If styles exist, show detailed info
    if styles and "code" in styles:
        print(f"\n📄 Style Metadata Example (code):")
        metadata = manager.get_style_metadata("code")
        print(f"   Name: {metadata['name']}")
        print(f"   File: {metadata['file_path']}")
        print(f"   Version: {metadata['version']}")
        print(f"   Registered: {metadata['registered_at']}")
        print(f"   Usage count: {metadata['usage_count']}")

        # Load style content (preview)
        print(f"\n📖 Style Content Preview (code):")
        style_data = manager.load_style("code")
        content_preview = style_data['content'][:200].replace('\n', ' ')
        print(f"   {content_preview}...")

    # Show usage stats
    print(f"\n📊 Usage Statistics:")
    stats = manager.get_style_stats()
    print(f"   Total loads: {stats['total_loads']}")
    print(f"   Most used style: {stats['most_used_style']}")

    if stats['style_usage']:
        print(f"\n   Style usage breakdown:")
        for style, count in sorted(stats['style_usage'].items(), key=lambda x: x[1], reverse=True):
            print(f"     {style}: {count} loads")

    if stats['role_usage']:
        print(f"\n   Role usage breakdown:")
        for role, count in sorted(stats['role_usage'].items(), key=lambda x: x[1], reverse=True):
            print(f"     {role}: {count} loads")

    print("\n✅ Demo 1 complete!")


def demo_2_style_recommendations():
    """
    Demo 2: Style Recommendations - Auto-recommend based on Role

    Demonstrates:
    - Role-to-style mappings
    - Automatic recommendations
    - Custom role mapping
    - Recommendation logic
    """
    print_section("DEMO 2: Style Recommendations - Auto-recommend based on Role")

    manager = get_style_manager()

    print("🎯 Built-in Role Recommendations:\n")

    # Test various roles
    test_roles = [
        ("code-generator", "Simple coding tasks"),
        ("explainer", "Educational content"),
        ("validator", "Code validation"),
        ("security-critic", "Security review"),
        ("performance-critic", "Performance analysis"),
        ("architect", "System design"),
        ("analyst", "Research and analysis"),
        ("orchestrator", "Workflow coordination"),
        ("unknown-role", "Fallback behavior")
    ]

    for role, description in test_roles:
        recommended = manager.recommend_style_for_role(role)
        print(f"   Role: {role:<20} → Style: {recommended:<15} ({description})")

    # Add custom role mapping
    print(f"\n🔧 Adding Custom Role Mapping:")
    manager.add_role_mapping("data-scientist", "analyst")
    print(f"   Added: data-scientist → analyst")

    recommended = manager.recommend_style_for_role("data-scientist")
    print(f"   Verification: {recommended}")

    # Show all mappings
    print(f"\n📋 All Role Mappings:")
    mappings = manager.get_all_role_mappings()
    print(f"   Total mappings: {len(mappings)}")
    print(f"   Sample mappings:")
    for role, style in list(mappings.items())[:5]:
        print(f"     {role} → {style}")

    print("\n✅ Demo 2 complete!")


def demo_3_agent_integration():
    """
    Demo 3: ResilientBaseAgent Integration - Using styles with agents

    Demonstrates:
    - Creating agent with output_style
    - Auto-recommendation
    - Style loading
    - System prompt construction
    """
    print_section("DEMO 3: ResilientBaseAgent Integration - Using styles with agents")

    print("🤖 Agent Creation with Output Styles:\n")

    print("Scenario 1: Explicit output_style")
    print("   Creating agent with role='developer', output_style='code'")
    print("   → Agent will use the 'code' style system prompt")

    print("\nScenario 2: Auto-recommendation")
    print("   Creating agent with role='security-critic', no explicit style")
    print("   → System recommends 'critic' style for security-critic role")
    print("   → Agent uses recommended 'critic' style system prompt")

    print("\nScenario 3: Explicit system_prompt (highest priority)")
    print("   Creating agent with system_prompt='Custom prompt', output_style='code'")
    print("   → Explicit system_prompt takes precedence")
    print("   → output_style is ignored")

    print("\n📝 System Prompt Priority:")
    print("   1. Explicit system_prompt (if provided)")
    print("   2. Output style (if provided)")
    print("   3. Auto-recommended style (based on role)")
    print("   4. Default role-based prompt (fallback)")

    print("\n🔍 Example Integration Code:")
    print("""
    from resilient_agent import ResilientBaseAgent
    from core.constants import Models

    # Method 1: Explicit style
    agent = ResilientBaseAgent(
        role="developer",
        model=Models.SONNET,
        output_style="code"  # ← Uses 'code' style
    )

    # Method 2: Auto-recommendation
    agent = ResilientBaseAgent(
        role="security-critic",  # ← Auto-selects 'critic' style
        model=Models.OPUS
    )

    # Make call (style tracked automatically)
    result = agent.call("Implement binary search")
    print(f"Used style: {result.output_style}")
    """)

    print("\n✅ Demo 3 complete!")


def demo_4_registry_integration():
    """
    Demo 4: Agent Registry Integration - Tracking style usage

    Demonstrates:
    - Registering agents with output_style
    - Recording usage with style tracking
    - Viewing style usage statistics
    - Analyzing style effectiveness
    """
    print_section("DEMO 4: Agent Registry Integration - Tracking style usage")

    from agent_registry import AgentRegistry, AgentCategory, ModelTier
    import tempfile

    # Use temporary registry for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = AgentRegistry(registry_dir=Path(tmpdir) / ".registry")

        print("📝 Registering Agents with Output Styles:\n")

        # Register agents with different styles
        agents_config = [
            ("developer", AgentCategory.CORE, ModelTier.SONNET, "code"),
            ("security-critic", AgentCategory.CRITIC, ModelTier.OPUS, "critic"),
            ("architect", AgentCategory.SPECIALIZED, ModelTier.OPUS, "architect"),
        ]

        for name, category, tier, style in agents_config:
            registry.register_agent(
                name=name,
                category=category,
                model_tier=tier,
                description=f"{name} agent",
                use_cases=["demo"],
                estimated_cost_per_call=0.01,
                estimated_time_seconds=10.0,
                quality_range=(80, 95),
                output_style=style
            )
            print(f"   ✅ {name:<20} → style: {style}")

        # Record usage with different styles
        print(f"\n📊 Recording Usage (with style tracking):\n")

        usage_records = [
            ("developer", "code", 3),
            ("developer", "detailed", 1),
            ("security-critic", "critic", 5),
            ("architect", "architect", 2),
        ]

        for agent_name, style_used, count in usage_records:
            for _ in range(count):
                registry.record_usage(
                    agent_name=agent_name,
                    cost_usd=0.01,
                    execution_time_seconds=10.0,
                    output_style_used=style_used
                )
            print(f"   Recorded {count} calls for {agent_name} using '{style_used}' style")

        # Show statistics
        print(f"\n📈 Agent Statistics with Style Usage:\n")

        for agent_name, _, _, default_style in agents_config:
            stats = registry.get_agent_stats(agent_name)
            print(f"   Agent: {agent_name}")
            print(f"     Default style: {stats['output_style']}")
            print(f"     Total invocations: {stats['total_invocations']}")
            print(f"     Style usage breakdown:")
            for style, count in stats['style_usage'].items():
                print(f"       {style}: {count} calls")
            print()

    print("✅ Demo 4 complete!")


def demo_5_observability_integration():
    """
    Demo 5: Observability Integration - Style in events

    Demonstrates:
    - Creating events with output_style
    - Style tracking in observability
    - Event serialization with style
    - Distributed tracing with styles
    """
    print_section("DEMO 5: Observability Integration - Style in events")

    from observability.event_schema import ObservabilityEvent, EventType, EventSeverity

    print("📡 Creating Events with Output Style Tracking:\n")

    # Create various events with output_style
    events = [
        ObservabilityEvent(
            event_type=EventType.AGENT_INVOKED,
            component="developer-agent",
            message="Starting code implementation",
            severity=EventSeverity.INFO,
            agent="developer",
            model="claude-3-5-sonnet-20241022",
            output_style="code"
        ),
        ObservabilityEvent(
            event_type=EventType.AGENT_COMPLETED,
            component="security-critic",
            message="Security review completed",
            severity=EventSeverity.INFO,
            agent="security-critic",
            model="claude-opus-4-20250514",
            output_style="critic",
            duration_ms=15000.0,
            cost_usd=0.025,
            quality_score=95.0
        ),
        ObservabilityEvent(
            event_type=EventType.AGENT_COMPLETED,
            component="architect",
            message="System design completed",
            severity=EventSeverity.INFO,
            agent="architect",
            model="claude-opus-4-20250514",
            output_style="architect",
            duration_ms=30000.0,
            cost_usd=0.045,
            quality_score=92.0
        )
    ]

    for i, event in enumerate(events, 1):
        print(f"Event {i}:")
        print(f"   Component: {event.component}")
        print(f"   Agent: {event.agent}")
        print(f"   Output Style: {event.output_style}")
        print(f"   Message: {event.message}")
        if event.duration_ms:
            print(f"   Duration: {event.duration_ms:.0f}ms")
        if event.cost_usd:
            print(f"   Cost: ${event.cost_usd:.4f}")
        print()

    # Serialize event with style
    print("📄 Event Serialization (JSON):\n")
    event_dict = events[1].to_dict()
    print(f"   Keys: {list(event_dict.keys())}")
    print(f"   output_style present: {'output_style' in event_dict}")
    print(f"   output_style value: {event_dict.get('output_style')}")

    print("\n💾 Example JSON:")
    example_json = json.dumps(event_dict, indent=2, default=str)
    print(example_json[:400] + "...")

    print("\n✅ Demo 5 complete!")


def demo_6_ab_testing():
    """
    Demo 6: A/B Testing - Empirical style comparison

    Demonstrates:
    - Setting up A/B tests
    - Running tests across styles
    - Analyzing results
    - Determining winner
    - Generating recommendations
    """
    print_section("DEMO 6: A/B Testing - Empirical style comparison")

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        print("🧪 Setting up A/B Test:\n")

        test = StyleABTest(
            test_name="code-vs-detailed-demo",
            prompt="Explain how binary search works",
            styles=["code", "detailed"],
            role="explainer",
            results_dir=Path(tmpdir)
        )

        print(f"   Test name: {test.test_name}")
        print(f"   Prompt: {test.prompt}")
        print(f"   Styles: {', '.join(test.styles)}")
        print(f"   Role: {test.role}")

        # Run test (using mock - no actual API calls)
        print(f"\n▶️  Running Test (3 trials per style)...")
        print(f"   Using mock execution (no actual API calls)\n")

        report = test.run(num_trials=3)

        # Show results
        print("📊 Test Results:\n")

        for style, metrics in report.metrics_by_style.items():
            print(f"   {style}:")
            print(f"     Success rate: {metrics.success_rate*100:.0f}%")
            print(f"     Avg duration: {metrics.avg_duration_ms:.0f}ms")
            print(f"     Avg cost: ${metrics.avg_cost_usd:.4f}")
            if metrics.avg_quality_score:
                print(f"     Avg quality: {metrics.avg_quality_score:.1f}/100")
            print()

        # Winner
        print(f"🏆 Winner: {report.winner}")
        print(f"   Reason: {report.winner_reason}")

        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"   {rec}")

        # Test metadata
        print(f"\n📋 Test Metadata:")
        print(f"   Total duration: {report.test_duration_seconds:.2f}s")
        print(f"   Total cost: ${report.total_cost_usd:.4f}")
        print(f"   Timestamp: {report.timestamp}")

        # Report saved
        print(f"\n💾 Report saved to: {test.results_dir}")

    print("\n✅ Demo 6 complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Output Styles System Demonstrations"
    )
    parser.add_argument(
        "--demo",
        type=str,
        help="Run specific demos (e.g., '1' or '1,3,5'). Default: all demos"
    )

    args = parser.parse_args()

    # Determine which demos to run
    if args.demo:
        demo_numbers = [int(n.strip()) for n in args.demo.split(',')]
    else:
        demo_numbers = [1, 2, 3, 4, 5, 6]

    # Map demo numbers to functions
    demos = {
        1: ("OutputStyleManager", demo_1_style_manager),
        2: ("Style Recommendations", demo_2_style_recommendations),
        3: ("ResilientBaseAgent Integration", demo_3_agent_integration),
        4: ("Agent Registry Integration", demo_4_registry_integration),
        5: ("Observability Integration", demo_5_observability_integration),
        6: ("A/B Testing", demo_6_ab_testing)
    }

    # Run selected demos
    print("\n" + "=" * 80)
    print(" OUTPUT STYLES SYSTEM DEMONSTRATIONS (C5)")
    print("=" * 80)
    print(f"\nRunning {len(demo_numbers)} of {len(demos)} demos...\n")

    for demo_num in demo_numbers:
        if demo_num in demos:
            name, func = demos[demo_num]
            try:
                func()
            except Exception as e:
                print(f"\n❌ Demo {demo_num} failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n❌ Demo {demo_num} not found. Valid demos: 1-6")

    # Summary
    print("\n" + "=" * 80)
    print(" DEMONSTRATIONS COMPLETE")
    print("=" * 80)
    print(f"\n✅ Completed {len(demo_numbers)} demonstrations")
    print(f"\nTo run specific demos: python3 {__file__} --demo 1,3,5")
    print()


if __name__ == "__main__":
    main()
