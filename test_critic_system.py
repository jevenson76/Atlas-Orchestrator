#!/usr/bin/env python3
"""
Comprehensive Test Suite for C3 Critic System

Tests cover:
- Critic loading and initialization
- FRESH CONTEXT enforcement
- OPUS MANDATORY enforcement
- JSON output parsing
- Individual critic functionality
- CriticOrchestrator coordination
- Validator-critic integration
- Error handling
- Cost tracking
- Aggregated reporting

Run with: pytest test_critic_system.py -v
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from critic_orchestrator import CriticOrchestrator, CriticResult, AggregatedReport
from validation_orchestrator import ValidationOrchestrator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_code():
    """Sample code with intentional issues for testing."""
    return '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
'''


@pytest.fixture
def good_code():
    """Sample of good quality code."""
    return '''
from typing import List

def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers.

    Args:
        numbers: List of numeric values

    Returns:
        Average value

    Raises:
        ValueError: If list is empty

    Example:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")

    return sum(numbers) / len(numbers)
'''


@pytest.fixture
def mock_api_response():
    """Mock Anthropic API response for testing."""
    return {
        "critic_type": "security",
        "model_used": "claude-opus-4-20250514",
        "analysis_timestamp": "2025-11-03T12:00:00Z",
        "overall_score": 25,
        "risk_level": "CRITICAL",
        "summary": "SQL injection vulnerability found",
        "findings": [
            {
                "severity": "CRITICAL",
                "category": "SQL Injection",
                "title": "Unsanitized user input in SQL query",
                "location": {"file": "test.py", "line": 2, "function": "get_user"},
                "description": "User ID directly interpolated into SQL query",
                "impact": "Complete database compromise possible",
                "recommendation": "Use parameterized queries",
                "code_snippet": 'query = f"SELECT * FROM users WHERE id = {user_id}"',
                "fixed_code": 'query = "SELECT * FROM users WHERE id = ?"',
                "references": ["OWASP A03:2021 - Injection"]
            }
        ],
        "statistics": {
            "total_findings": 1,
            "critical": 1,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "metrics": {}
    }


# ============================================================================
# TEST SUITE 1: CRITIC INITIALIZATION
# ============================================================================

class TestCriticInitialization:
    """Test critic loading and initialization."""

    def test_critic_files_exist(self):
        """Test 1: All 5 critic definition files exist."""
        critics_dir = Path.home() / ".claude" / "agents" / "critics"

        expected_critics = [
            "security-critic.md",
            "performance-critic.md",
            "architecture-critic.md",
            "code-quality-critic.md",
            "documentation-critic.md"
        ]

        for critic_file in expected_critics:
            critic_path = critics_dir / critic_file
            assert critic_path.exists(), f"Critic definition missing: {critic_file}"

            # Verify file is not empty
            content = critic_path.read_text()
            assert len(content) > 1000, f"{critic_file} seems incomplete (< 1000 chars)"

            # Verify contains key sections
            assert "FRESH CONTEXT" in content, f"{critic_file} missing FRESH CONTEXT principle"
            assert "OPUS MANDATORY" in content, f"{critic_file} missing OPUS MANDATORY principle"
            assert "JSON" in content or "json" in content, f"{critic_file} missing JSON output spec"

    def test_orchestrator_initialization(self):
        """Test 2: CriticOrchestrator initializes correctly."""
        orchestrator = CriticOrchestrator()

        # Should load 5 critics
        assert len(orchestrator._critic_agents) == 5, "Should load 5 critics"

        # Verify all expected critics are loaded
        expected_critics = [
            "security-critic",
            "performance-critic",
            "architecture-critic",
            "code-quality-critic",
            "documentation-critic"
        ]

        for critic_id in expected_critics:
            assert critic_id in orchestrator._critic_agents, f"{critic_id} not loaded"

    def test_opus_model_enforcement(self):
        """Test 3: All critics use Opus model (no fallback)."""
        orchestrator = CriticOrchestrator()

        # Verify OPUS_MODEL constant
        assert orchestrator.OPUS_MODEL == "claude-opus-4-20250514", \
            "Critic system must use Opus 4"

        # Verify each critic agent has correct model
        for critic_id, agent in orchestrator._critic_agents.items():
            assert agent.config.model == "claude-opus-4-20250514", \
                f"{critic_id} not using Opus 4"
            assert agent.config.enable_fallback is False, \
                f"{critic_id} should have fallback disabled"


# ============================================================================
# TEST SUITE 2: FRESH CONTEXT ENFORCEMENT
# ============================================================================

class TestFreshContextEnforcement:
    """Test that critics receive ONLY code, no history."""

    def test_fresh_context_prompt_structure(self, sample_code):
        """Test 4: Prompt contains only code and minimal context."""
        orchestrator = CriticOrchestrator()

        # Build fresh context prompt
        prompt = orchestrator._build_fresh_context_prompt(
            code_snippet=sample_code,
            file_path="test.py",
            language="python"
        )

        # Verify code is present
        assert sample_code in prompt, "Code snippet must be in prompt"

        # Verify NO task history or creation context
        forbidden_terms = [
            "task was",
            "user requested",
            "created by",
            "purpose of this code",
            "intended to",
            "implements the feature"
        ]

        for term in forbidden_terms:
            assert term.lower() not in prompt.lower(), \
                f"Prompt contains context about creation: '{term}'"

        # Verify minimal context only (file path, language)
        assert "test.py" in prompt or "File:" in prompt, \
            "File path context should be present"

    def test_fresh_context_no_history_leakage(self):
        """Test 5: Context dict does not leak task history."""
        orchestrator = CriticOrchestrator()

        # Attempt to pass task history in context
        code = "def foo(): pass"

        # This should be ignored by fresh context enforcement
        context_with_history = {
            "file_path": "foo.py",
            "task_description": "Implement authentication feature",
            "creation_reason": "User requested login system",
            "original_prompt": "Create a secure login function"
        }

        prompt = orchestrator._build_fresh_context_prompt(
            code_snippet=code,
            file_path=context_with_history.get("file_path"),
            language="python"
        )

        # Verify task history is NOT in prompt
        assert "authentication" not in prompt.lower(), \
            "Task description leaked into prompt"
        assert "User requested" not in prompt, \
            "Creation reason leaked into prompt"
        assert "login" not in prompt.lower(), \
            "Original prompt leaked into prompt"


# ============================================================================
# TEST SUITE 3: JSON OUTPUT PARSING
# ============================================================================

class TestJSONOutputParsing:
    """Test JSON response parsing from critics."""

    def test_parse_clean_json(self, mock_api_response):
        """Test 6: Parse clean JSON response."""
        orchestrator = CriticOrchestrator()

        json_str = json.dumps(mock_api_response)
        parsed = orchestrator._extract_json(json_str)

        assert parsed == mock_api_response
        assert parsed["overall_score"] == 25
        assert len(parsed["findings"]) == 1

    def test_parse_json_with_markdown(self, mock_api_response):
        """Test 7: Parse JSON wrapped in markdown code fence."""
        orchestrator = CriticOrchestrator()

        json_str = "```json\n" + json.dumps(mock_api_response) + "\n```"
        parsed = orchestrator._extract_json(json_str)

        assert parsed == mock_api_response
        assert parsed["risk_level"] == "CRITICAL"

    def test_parse_json_with_text(self, mock_api_response):
        """Test 8: Parse JSON from response with surrounding text."""
        orchestrator = CriticOrchestrator()

        json_str = "Here is the analysis:\n```json\n" + \
                   json.dumps(mock_api_response) + \
                   "\n```\nEnd of analysis."

        parsed = orchestrator._extract_json(json_str)

        assert parsed == mock_api_response

    def test_extract_grade_variants(self):
        """Test 9: Extract grade from various JSON field names."""
        orchestrator = CriticOrchestrator()

        test_cases = [
            ({"grade": "EXCELLENT"}, "EXCELLENT"),
            ({"quality_grade": "GOOD"}, "GOOD"),
            ({"performance_grade": "FAIR"}, "FAIR"),
            ({"risk_level": "CRITICAL"}, "CRITICAL"),
            ({"no_grade_field": "test"}, "UNKNOWN")
        ]

        for json_obj, expected_grade in test_cases:
            grade = orchestrator._extract_grade(json_obj)
            assert grade == expected_grade, \
                f"Failed to extract grade from {json_obj}"


# ============================================================================
# TEST SUITE 4: INDIVIDUAL CRITIC FUNCTIONALITY
# ============================================================================

class TestIndividualCritics:
    """Test individual critic execution (mocked)."""

    @patch('critic_orchestrator.BaseAgent.execute')
    def test_security_critic_execution(self, mock_execute, sample_code, mock_api_response):
        """Test 10: Security critic executes with correct parameters."""
        mock_execute.return_value = json.dumps(mock_api_response)

        orchestrator = CriticOrchestrator()
        results = orchestrator.review_code(
            code_snippet=sample_code,
            critics=["security-critic"],
            file_path="test.py"
        )

        assert "security-critic" in results
        result = results["security-critic"]

        assert result.critic_type == "security-critic"
        assert result.model_used == "claude-opus-4-20250514"
        assert result.success is True

    @patch('critic_orchestrator.BaseAgent.execute')
    def test_multiple_critics_execution(self, mock_execute, sample_code, mock_api_response):
        """Test 11: Multiple critics execute independently."""
        mock_execute.return_value = json.dumps(mock_api_response)

        orchestrator = CriticOrchestrator()
        results = orchestrator.review_code(
            code_snippet=sample_code,
            critics=["security-critic", "performance-critic", "architecture-critic"],
            file_path="test.py"
        )

        assert len(results) == 3
        assert all(r.success for r in results.values())

    @patch('critic_orchestrator.BaseAgent.execute')
    def test_critic_error_handling(self, mock_execute, sample_code):
        """Test 12: Critic handles API errors gracefully."""
        mock_execute.side_effect = Exception("API timeout")

        orchestrator = CriticOrchestrator()
        results = orchestrator.review_code(
            code_snippet=sample_code,
            critics=["security-critic"],
            file_path="test.py"
        )

        assert "security-critic" in results
        result = results["security-critic"]

        assert result.success is False
        assert "API timeout" in result.error
        assert result.grade == "ERROR"


# ============================================================================
# TEST SUITE 5: AGGREGATED REPORTING
# ============================================================================

class TestAggregatedReporting:
    """Test aggregated report generation."""

    def test_aggregated_report_generation(self, sample_code):
        """Test 13: Aggregated report combines all critic results."""
        # Create mock results
        results = {
            "security-critic": CriticResult(
                critic_type="security-critic",
                model_used="claude-opus-4-20250514",
                analysis_timestamp="2025-11-03T12:00:00Z",
                overall_score=30,
                grade="CRITICAL",
                summary="SQL injection found",
                findings=[
                    {"severity": "CRITICAL", "title": "SQL injection"}
                ],
                statistics={"total_findings": 1, "critical": 1, "high": 0, "medium": 0, "low": 0},
                metrics={},
                execution_time_seconds=10.0,
                cost_usd=0.05,
                success=True
            ),
            "performance-critic": CriticResult(
                critic_type="performance-critic",
                model_used="claude-opus-4-20250514",
                analysis_timestamp="2025-11-03T12:00:00Z",
                overall_score=60,
                grade="FAIR",
                summary="N+1 query issue",
                findings=[
                    {"severity": "HIGH", "title": "N+1 query"}
                ],
                statistics={"total_findings": 1, "critical": 0, "high": 1, "medium": 0, "low": 0},
                metrics={},
                execution_time_seconds=12.0,
                cost_usd=0.055,
                success=True
            )
        }

        orchestrator = CriticOrchestrator()
        report = orchestrator.generate_report(
            results=results,
            code_snippet=sample_code,
            file_path="test.py"
        )

        assert report.overall_score == 45  # (30 + 60) / 2
        assert report.worst_grade == "CRITICAL"
        assert report.total_findings == 2
        assert report.critical_findings == 1
        assert report.high_findings == 1
        assert report.total_cost_usd == 0.105  # 0.05 + 0.055
        assert report.success_count == 2
        assert report.failure_count == 0

    def test_worst_grade_calculation(self):
        """Test 14: Worst grade correctly identified."""
        results = {
            "critic1": CriticResult(
                critic_type="critic1", model_used="opus", analysis_timestamp="now",
                overall_score=90, grade="EXCELLENT", summary="good",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=1.0, cost_usd=0.01, success=True
            ),
            "critic2": CriticResult(
                critic_type="critic2", model_used="opus", analysis_timestamp="now",
                overall_score=50, grade="FAIR", summary="ok",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=1.0, cost_usd=0.01, success=True
            ),
            "critic3": CriticResult(
                critic_type="critic3", model_used="opus", analysis_timestamp="now",
                overall_score=20, grade="CRITICAL", summary="bad",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=1.0, cost_usd=0.01, success=True
            )
        }

        orchestrator = CriticOrchestrator()
        report = orchestrator.generate_report(
            results=results,
            code_snippet="code",
            file_path="test.py"
        )

        assert report.worst_grade == "CRITICAL"


# ============================================================================
# TEST SUITE 6: VALIDATOR-CRITIC INTEGRATION
# ============================================================================

class TestValidatorCriticIntegration:
    """Test integration between validators and critics."""

    @patch('validation_orchestrator.ValidationOrchestrator.validate_code')
    @patch('critic_orchestrator.CriticOrchestrator.review_code')
    def test_validate_with_critics_basic(self, mock_review, mock_validate, sample_code):
        """Test 15: validate_with_critics runs both validators and critics."""
        # Mock validator result
        from validation_types import ValidationResult, ValidationFinding
        mock_validate.return_value = ValidationResult(
            validator_name="code-validator",
            status="WARNING",
            score=75,
            findings=[],
            execution_time_ms=1000,
            model_used="sonnet",
            cost_usd=0.005
        )

        # Mock critic results
        mock_review.return_value = {
            "security-critic": CriticResult(
                critic_type="security", model_used="opus", analysis_timestamp="now",
                overall_score=60, grade="FAIR", summary="issues",
                findings=[], statistics={"total_findings": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
                metrics={}, execution_time_seconds=10.0, cost_usd=0.05, success=True
            )
        }

        orchestrator = ValidationOrchestrator(project_root=".")
        result = orchestrator.validate_with_critics(
            code=sample_code,
            level="standard"
        )

        assert "validator_result" in result
        assert "critic_results" in result
        assert "overall_score" in result
        assert "recommendation" in result

    def test_critic_selection_by_level(self):
        """Test 16: Correct critics selected based on level."""
        orchestrator = ValidationOrchestrator(project_root=".")

        # Quick: no critics
        critics = orchestrator._select_critics_for_level("quick")
        assert len(critics) == 0

        # Standard: 3 key critics
        critics = orchestrator._select_critics_for_level("standard")
        assert len(critics) == 3
        assert "security-critic" in critics
        assert "performance-critic" in critics
        assert "architecture-critic" in critics

        # Thorough: all 5 critics
        critics = orchestrator._select_critics_for_level("thorough")
        assert len(critics) == 5

    @patch('validation_orchestrator.ValidationOrchestrator.validate_code')
    @patch('critic_orchestrator.CriticOrchestrator.review_code')
    def test_recommendation_logic(self, mock_review, mock_validate, sample_code):
        """Test 17: Recommendation logic based on findings."""
        from validation_types import ValidationResult, ValidationFinding

        # Test NO-GO recommendation (critical findings)
        mock_validate.return_value = ValidationResult(
            validator_name="code", status="FAIL", score=30,
            findings=[ValidationFinding(
                id="1", severity="CRITICAL", category="security",
                subcategory="sql", location="line 1",
                issue="SQL injection", recommendation="Fix it"
            )],
            execution_time_ms=1000, model_used="sonnet", cost_usd=0.005
        )

        mock_review.return_value = {}

        orchestrator = ValidationOrchestrator(project_root=".")
        result = orchestrator.validate_with_critics(code=sample_code, run_validators=True)

        assert result["recommendation"] == "NO-GO"


# ============================================================================
# TEST SUITE 7: COST TRACKING
# ============================================================================

class TestCostTracking:
    """Test cost tracking and budget enforcement."""

    def test_cost_accumulation(self, sample_code):
        """Test 18: Costs accumulate correctly across critics."""
        results = {
            "critic1": CriticResult(
                critic_type="c1", model_used="opus", analysis_timestamp="now",
                overall_score=50, grade="FAIR", summary="ok",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=10.0, cost_usd=0.05, success=True
            ),
            "critic2": CriticResult(
                critic_type="c2", model_used="opus", analysis_timestamp="now",
                overall_score=50, grade="FAIR", summary="ok",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=12.0, cost_usd=0.055, success=True
            ),
            "critic3": CriticResult(
                critic_type="c3", model_used="opus", analysis_timestamp="now",
                overall_score=50, grade="FAIR", summary="ok",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=15.0, cost_usd=0.06, success=True
            )
        }

        orchestrator = CriticOrchestrator()
        report = orchestrator.generate_report(
            results=results,
            code_snippet=sample_code,
            file_path="test.py"
        )

        assert report.total_cost_usd == 0.165  # 0.05 + 0.055 + 0.06
        assert report.total_execution_time_seconds == 37.0  # 10 + 12 + 15


# ============================================================================
# TEST SUITE 8: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_code_rejection(self):
        """Test 19: Empty code is rejected."""
        orchestrator = CriticOrchestrator()

        with pytest.raises(ValueError, match="cannot be empty"):
            orchestrator.review_code(code_snippet="")

    def test_invalid_critic_id(self):
        """Test 20: Invalid critic ID raises error."""
        orchestrator = CriticOrchestrator()

        with pytest.raises(ValueError, match="Invalid critic IDs"):
            orchestrator.review_code(
                code_snippet="def foo(): pass",
                critics=["nonexistent-critic"]
            )

    def test_malformed_json_handling(self):
        """Test 21: Malformed JSON returns error structure."""
        orchestrator = CriticOrchestrator()

        malformed_json = "This is not JSON at all!"
        parsed = orchestrator._extract_json(malformed_json)

        assert "error" in parsed
        assert "Could not parse JSON" in parsed["error"]

    def test_partial_critic_failure(self):
        """Test 22: Partial critic failure doesn't stop aggregation."""
        results = {
            "critic1": CriticResult(
                critic_type="c1", model_used="opus", analysis_timestamp="now",
                overall_score=80, grade="GOOD", summary="ok",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=10.0, cost_usd=0.05, success=True
            ),
            "critic2": CriticResult(
                critic_type="c2", model_used="opus", analysis_timestamp="now",
                overall_score=0, grade="ERROR", summary="failed",
                findings=[], statistics={}, metrics={},
                execution_time_seconds=5.0, cost_usd=0.01, success=False,
                error="API timeout"
            )
        }

        orchestrator = CriticOrchestrator()
        report = orchestrator.generate_report(
            results=results,
            code_snippet="code",
            file_path="test.py"
        )

        # Should still generate report
        assert report.success_count == 1
        assert report.failure_count == 1
        assert len(report.failed_critics) == 1
        assert "critic2" in report.failed_critics


# ============================================================================
# TEST SUITE 9: INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests (require actual API calls - mark as integration)."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        "ANTHROPIC_API_KEY" not in __import__("os").environ,
        reason="Requires ANTHROPIC_API_KEY"
    )
    def test_real_security_critic(self, sample_code):
        """Test 23: Real security critic API call (integration test)."""
        orchestrator = CriticOrchestrator()

        results = orchestrator.review_code(
            code_snippet=sample_code,
            critics=["security-critic"],
            file_path="test.py",
            language="python"
        )

        assert "security-critic" in results
        result = results["security-critic"]

        # Should detect SQL injection
        assert result.success is True
        assert result.overall_score < 50  # Should score poorly
        assert any("injection" in f.get("title", "").lower() for f in result.findings)

    @pytest.mark.integration
    @pytest.mark.skipif(
        "ANTHROPIC_API_KEY" not in __import__("os").environ,
        reason="Requires ANTHROPIC_API_KEY"
    )
    def test_real_documentation_critic(self, good_code):
        """Test 24: Real documentation critic API call (integration test)."""
        orchestrator = CriticOrchestrator()

        results = orchestrator.review_code(
            code_snippet=good_code,
            critics=["documentation-critic"],
            file_path="test.py",
            language="python"
        )

        assert "documentation-critic" in results
        result = results["documentation-critic"]

        # Should score well (has docstring, type hints, examples)
        assert result.success is True
        assert result.overall_score > 70  # Should score well


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
