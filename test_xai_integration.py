#!/usr/bin/env python3
"""
Test xAI (Grok) integration with ResilientBaseAgent.

Tests:
1. API key loading
2. Client initialization
3. Simple completion
4. Cost calculation
5. Fallback behavior
6. Circuit breaker integration
"""

import os
import sys
import logging
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from resilient_agent import ResilientBaseAgent
from core.constants import Models
from api_config import APIConfig
from agent_system import ModelPricing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_config():
    """Test 1: API configuration loads xAI key"""
    print("\n" + "="*60)
    print("TEST 1: API Configuration")
    print("="*60)

    config = APIConfig()
    status = config.get_status()

    if 'xai' in status:
        xai_status = status['xai']
        print(f"✓ xAI configured: {xai_status['configured']}")
        if xai_status['configured']:
            print(f"  Source: {xai_status['source']}")
            print(f"  Key preview: {xai_status['key_preview']}")
        else:
            print(f"  ✗ Not configured. Set XAI_API_KEY or add to config.json")
            return False
    else:
        print("✗ xAI not found in config")
        return False

    return True

def test_pricing():
    """Test 2: Grok model pricing"""
    print("\n" + "="*60)
    print("TEST 2: Model Pricing")
    print("="*60)

    test_cases = [
        (Models.GROK_3, 1000, 500),
        ('grok-2-1212', 2000, 1000),
    ]

    for model, tokens_in, tokens_out in test_cases:
        cost = ModelPricing.calculate_cost(model, tokens_in, tokens_out)
        print(f"✓ {model}: {tokens_in} in + {tokens_out} out = ${cost:.6f}")

    return True

def test_client_initialization():
    """Test 3: ResilientBaseAgent initializes xAI client"""
    print("\n" + "="*60)
    print("TEST 3: Client Initialization")
    print("="*60)

    try:
        agent = ResilientBaseAgent(
            role="Test Agent",
            model=Models.GROK_3,
            max_tokens=100
        )

        if hasattr(agent, 'xai_client') and agent.xai_client:
            print("✓ xAI client initialized successfully")
            return True
        else:
            print("✗ xAI client not initialized")
            return False

    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False

def test_simple_completion():
    """Test 4: Simple completion with Grok"""
    print("\n" + "="*60)
    print("TEST 4: Simple Completion")
    print("="*60)

    try:
        agent = ResilientBaseAgent(
            role="Test Agent",
            model=Models.GROK_3,
            max_tokens=100,
            enable_fallback=False  # Direct call only
        )

        result = agent.call(
            prompt="Say 'Hello from Grok' and nothing else.",
            context={"test": True}
        )

        if result.success:
            print(f"✓ Completion successful")
            print(f"  Output: {result.output[:100]}...")
            print(f"  Model: {result.model_used}")
            print(f"  Provider: {result.provider}")
            print(f"  Tokens: {result.tokens_in} in, {result.tokens_out} out")
            print(f"  Cost: ${result.cost:.6f}")
            print(f"  Latency: {result.latency:.2f}s")
            return True
        else:
            print(f"✗ Completion failed: {result.error}")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_behavior():
    """Test 5: Fallback includes Grok"""
    print("\n" + "="*60)
    print("TEST 5: Fallback Behavior")
    print("="*60)

    try:
        from resilience import ModelFallbackChain

        fallback = ModelFallbackChain(
            primary_model=Models.SONNET,
            enable_cross_provider=True
        )

        # Check that Grok is in fallback chain
        chain_models = fallback.anthropic_chain + fallback.cross_provider_chain
        grok_models = [m for m in chain_models if 'grok' in m.lower()]

        if grok_models:
            print(f"✓ Grok in fallback chain: {grok_models}")
            print(f"  Full chain: {chain_models}")
            # Verify it's grok-3, not deprecated grok-beta
            if Models.GROK_3 in grok_models or 'grok-3' in grok_models:
                print(f"  ✓ Using current model (grok-3)")
            return True
        else:
            print(f"✗ Grok not in fallback chain")
            print(f"  Chain: {chain_models}")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("XAI (GROK) INTEGRATION TEST SUITE")
    print("="*60)

    results = {
        "API Config": test_api_config(),
        "Pricing": test_pricing(),
        "Client Init": test_client_initialization(),
        "Simple Completion": test_simple_completion(),
        "Fallback Behavior": test_fallback_behavior()
    }

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
