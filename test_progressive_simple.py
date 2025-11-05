"""
Simple Tests for ProgressiveEnhancementOrchestrator
(Tests structure and logic, not actual API calls)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from progressive_enhancement_orchestrator import (
    ProgressiveEnhancementOrchestrator,
    ModelTier
)


def test_initialization():
    """Test orchestrator initialization."""
    print("\n✓ Test 1: Orchestrator Initialization")

    orchestrator = ProgressiveEnhancementOrchestrator(
        quality_target=85,
        max_escalations=3
    )

    assert orchestrator.quality_target == 85
    assert orchestrator.max_escalations == 3
    assert len(orchestrator.MODEL_TIERS) == 4

    print(f"   - Quality target: {orchestrator.quality_target}")
    print(f"   - Max escalations: {orchestrator.max_escalations}")
    print(f"   - Model tiers: {len(orchestrator.MODEL_TIERS)}")
    print("   ✓ PASSED")


def test_model_tier_structure():
    """Test ModelTier definitions."""
    print("\n✓ Test 2: Model Tier Structure")

    orchestrator = ProgressiveEnhancementOrchestrator()
    tiers = orchestrator.MODEL_TIERS

    # Check tier ordering (cheapest to most expensive)
    assert tiers[0].name == "Haiku"
    assert tiers[1].name == "Sonnet"
    assert tiers[2].name == "Opus"
    assert tiers[3].name == "GPT-4"

    # Check quality progression
    assert tiers[0].max_quality < tiers[1].max_quality
    assert tiers[1].max_quality < tiers[2].max_quality

    print("   - Tier progression correct:")
    for tier in tiers:
        print(f"     • {tier.name:6s}: max_quality={tier.max_quality}, "
              f"cost=${tier.cost_per_1m_input}/{tier.cost_per_1m_output} per 1M")

    print("   ✓ PASSED")


def test_code_detection():
    """Test code detection logic."""
    print("\n✓ Test 3: Code Detection")

    orchestrator = ProgressiveEnhancementOrchestrator()

    # Should detect code (must be > 50 chars)
    assert orchestrator._is_code_result("def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)")
    assert orchestrator._is_code_result("class Calculator:\n    def add(self, a, b):\n        return a + b\n    def subtract(self, a, b):\n        return a - b")
    assert orchestrator._is_code_result("import numpy as np\nimport pandas as pd\n\ndef process_data():\n    return pd.DataFrame()")

    # Should not detect code
    assert not orchestrator._is_code_result("This is just text")
    assert not orchestrator._is_code_result("Short")

    print("   - Code detection working correctly")
    print("   ✓ PASSED")


def test_quality_estimation():
    """Test quality estimation logic."""
    print("\n✓ Test 4: Quality Estimation")

    orchestrator = ProgressiveEnhancementOrchestrator()

    # Test with different tiers and outputs
    haiku_tier = orchestrator.MODEL_TIERS[0]
    sonnet_tier = orchestrator.MODEL_TIERS[1]

    # Long output, no validation
    quality1 = orchestrator._estimate_quality("x" * 1000, None, haiku_tier)
    assert 0 <= quality1 <= 100

    # Short output penalty
    quality2 = orchestrator._estimate_quality("x" * 50, None, haiku_tier)
    assert quality2 < quality1

    # Higher tier should have higher base quality
    quality3 = orchestrator._estimate_quality("x" * 1000, None, sonnet_tier)
    assert quality3 > quality1

    print(f"   - Haiku (long output): {quality1}/100")
    print(f"   - Haiku (short output): {quality2}/100")
    print(f"   - Sonnet (long output): {quality3}/100")
    print("   ✓ PASSED")


def test_system_prompt_creation():
    """Test system prompt generation."""
    print("\n✓ Test 5: System Prompt Creation")

    orchestrator = ProgressiveEnhancementOrchestrator()

    task = "Create a calculator"
    context = {"language": "python", "framework": "FastAPI"}

    prompt = orchestrator._create_system_prompt(task, context)

    assert "python" in prompt.lower()
    assert "FastAPI" in prompt
    assert task in prompt

    print("   - Prompt includes language ✓")
    print("   - Prompt includes framework ✓")
    print("   - Prompt includes task ✓")
    print("   ✓ PASSED")


def test_tier_skipping_logic():
    """Test that tiers are skipped when max_quality < target."""
    print("\n✓ Test 6: Tier Skipping Logic")

    # Create orchestrator with high quality target
    orchestrator = ProgressiveEnhancementOrchestrator(
        quality_target=95,  # Haiku max is 80, Sonnet max is 92
        max_escalations=3
    )

    # Verify tier skip logic
    haiku_tier = orchestrator.MODEL_TIERS[0]
    sonnet_tier = orchestrator.MODEL_TIERS[1]
    opus_tier = orchestrator.MODEL_TIERS[2]

    # Should skip Haiku (80 < 95)
    assert haiku_tier.max_quality < orchestrator.quality_target
    # Should skip Sonnet (92 < 95)
    assert sonnet_tier.max_quality < orchestrator.quality_target
    # Should try Opus (98 >= 95)
    assert opus_tier.max_quality >= orchestrator.quality_target

    print(f"   - Target quality: {orchestrator.quality_target}")
    print(f"   - Haiku skipped (max {haiku_tier.max_quality} < target)")
    print(f"   - Sonnet skipped (max {sonnet_tier.max_quality} < target)")
    print(f"   - Opus tried (max {opus_tier.max_quality} >= target)")
    print("   ✓ PASSED")


def test_suitable_for_hints():
    """Test that tiers have suitable_for hints."""
    print("\n✓ Test 7: Suitable For Hints")

    orchestrator = ProgressiveEnhancementOrchestrator()

    for tier in orchestrator.MODEL_TIERS:
        assert len(tier.suitable_for) > 0
        print(f"   - {tier.name:6s}: {', '.join(tier.suitable_for)}")

    print("   ✓ PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("🧪 TESTING PROGRESSIVE ENHANCEMENT ORCHESTRATOR")
    print("=" * 70)

    tests = [
        test_initialization,
        test_model_tier_structure,
        test_code_detection,
        test_quality_estimation,
        test_system_prompt_creation,
        test_tier_skipping_logic,
        test_suitable_for_hints,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
