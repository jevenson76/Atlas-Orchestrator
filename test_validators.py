#!/usr/bin/env python3
"""
Comprehensive Test Suite for Validator System

Tests all components:
- validation_types.py (data structures)
- validation_orchestrator.py (orchestration)
- Integration with Phase B infrastructure
- All three validators (code, doc, test)
- Report generation
- Error handling

Run with:
    pytest test_validators.py -v
    pytest test_validators.py -v --tb=short  # Less verbose
    pytest test_validators.py::test_name -v  # Single test
"""

import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock
import sys

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from validation_types import (
    ValidationFinding,
    ValidationResult,
    ValidationReport
)
from validation_orchestrator import ValidationOrchestrator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory"""
    return tmp_path

@pytest.fixture
def orchestrator(temp_project):
    """Create ValidationOrchestrator instance"""
    return ValidationOrchestrator(
        project_root=str(temp_project),
        validators=["code-validator", "doc-validator", "test-validator"]
    )

@pytest.fixture
def sample_code():
    """Sample Python code for testing"""
    return '''
def authenticate(username, password):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}'"
    return execute_query(query)
'''

@pytest.fixture
def sample_docs():
    """Sample documentation for testing"""
    return '''
# My Project

This is a minimal README.

## Installation
pip install it
'''

@pytest.fixture
def sample_tests():
    """Sample test code for testing"""
    return '''
def test_authenticate():
    assert True  # Weak assertion

def test_login():
    pass  # Empty test
'''

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return json.dumps({
        "status": "FAIL",
        "score": 70,
        "findings": [
            {
                "id": "SEC-001",
                "severity": "CRITICAL",
                "category": "security",
                "subcategory": "sql-injection",
                "location": "auth.py:3",
                "issue": "SQL injection vulnerability",
                "recommendation": "Use parameterized queries",
                "confidence": 0.95
            }
        ],
        "passed_checks": ["Code compiles", "No syntax errors"],
        "metrics": {"complexity": 5, "maintainability": 70},
        "target": "auth.py"
    })


# ============================================================================
# VALIDATION TYPES TESTS
# ============================================================================

class TestValidationTypes:
    """Test validation_types.py data structures"""

    def test_validation_finding_creation(self):
        """Test creating ValidationFinding"""
        finding = ValidationFinding(
            id="FIND-001",
            severity="CRITICAL",
            category="security",
            subcategory="sql-injection",
            location="auth.py:42",
            issue="SQL injection",
            recommendation="Use parameterized queries"
        )

        assert finding.severity == "CRITICAL"
        assert finding.category == "security"
        assert "auth.py:42" in finding.location

    def test_validation_result_creation(self):
        """Test creating ValidationResult"""
        result = ValidationResult(
            validator_name="code-validator",
            status="FAIL",
            score=70,
            findings=[],
            execution_time_ms=5000,
            model_used="claude-sonnet-4-5-20250929",
            cost_usd=0.005
        )

        assert result.validator_name == "code-validator"
        assert result.status == "FAIL"
        assert result.score == 70

    def test_validation_report_from_results(self):
        """Test creating ValidationReport from results"""
        result1 = ValidationResult(
            validator_name="code-validator",
            status="PASS",
            score=95,
            findings=[],
            execution_time_ms=2000,
            model_used="claude-haiku-4-5-20250611",
            cost_usd=0.002
        )

        result2 = ValidationResult(
            validator_name="doc-validator",
            status="FAIL",
            score=60,
            findings=[
                ValidationFinding(
                    id="DOC-001",
                    severity="HIGH",
                    category="completeness",
                    subcategory="missing-section",
                    location="README.md",
                    issue="Missing installation section",
                    recommendation="Add installation instructions"
                )
            ],
            execution_time_ms=3000,
            model_used="claude-sonnet-4-5-20250929",
            cost_usd=0.005
        )

        report = ValidationReport.from_results(
            results=[result1, result2],
            total_time_ms=5000
        )

        assert isinstance(report, ValidationReport)
        assert report.overall_status == "FAIL"  # One fail = overall fail
        assert len(report.results) == 2
        assert report.total_findings["total"] == 1  # total_findings is now a dict
        assert report.high_count == 1


# ============================================================================
# ORCHESTRATOR INITIALIZATION TESTS
# ============================================================================

class TestOrchestratorInit:
    """Test ValidationOrchestrator initialization"""

    def test_initialization_success(self, temp_project):
        """Test successful orchestrator initialization"""
        orchestrator = ValidationOrchestrator(
            project_root=str(temp_project)
        )

        assert orchestrator.project_root == temp_project
        assert len(orchestrator.validators) == 3
        assert "code-validator" in orchestrator.validators

    def test_initialization_with_custom_validators(self, temp_project):
        """Test initialization with custom validator list"""
        orchestrator = ValidationOrchestrator(
            project_root=str(temp_project),
            validators=["code-validator"]
        )

        assert len(orchestrator.validators) == 1
        assert orchestrator.validators[0] == "code-validator"

    def test_default_level(self, orchestrator):
        """Test default validation level is set"""
        assert orchestrator.default_level == "standard"

    def test_stats_initialization(self, orchestrator):
        """Test execution stats are initialized to zero"""
        stats = orchestrator.get_execution_stats()
        assert stats["total_validations"] == 0
        assert stats["total_cost_usd"] == 0.0
        assert stats["total_time_seconds"] == 0.0


# ============================================================================
# INLINE PROMPT TESTS
# ============================================================================

class TestInlinePrompts:
    """Test inline prompt fallback system"""

    def test_inline_prompts_exist(self, orchestrator):
        """Test inline prompts are defined"""
        assert hasattr(orchestrator, '_INLINE_PROMPTS')
        assert "code-validator" in orchestrator._INLINE_PROMPTS
        assert "doc-validator" in orchestrator._INLINE_PROMPTS
        assert "test-validator" in orchestrator._INLINE_PROMPTS

    def test_get_prompt_template_fallback(self, orchestrator):
        """Test _get_prompt_template falls back to inline"""
        # This will use inline prompts since .md extraction likely fails
        prompt = orchestrator._get_prompt_template("code-validator")

        assert len(prompt) > 100
        assert "{target_content}" in prompt
        assert "{level}" in prompt

    def test_inline_prompt_has_required_variables(self, orchestrator):
        """Test inline prompts have required template variables"""
        # Test code validator inline prompt directly
        code_prompt = orchestrator._INLINE_PROMPTS["code-validator"]
        assert "{target_content}" in code_prompt
        assert "{level}" in code_prompt

        # Test that all validators have prompts available
        for validator_name in ["code-validator", "doc-validator", "test-validator"]:
            prompt = orchestrator._get_prompt_template(validator_name)
            assert len(prompt) > 100  # Substantial prompt


# ============================================================================
# VALIDATION METHOD TESTS (with mocked LLM)
# ============================================================================

class TestValidationMethods:
    """Test individual validation methods"""

    @patch('resilient_agent.ResilientBaseAgent.generate_text')
    def test_validate_code_success(self, mock_generate, orchestrator, sample_code, mock_llm_response):
        """Test code validation with mocked LLM"""
        mock_generate.return_value = mock_llm_response

        result = orchestrator.validate_code(
            code=sample_code,
            context={"file_path": "auth.py"},
            level="quick"
        )

        assert isinstance(result, ValidationResult)
        assert result.validator_name == "code-validator"
        assert result.status in ["PASS", "FAIL", "WARNING"]

        # Verify LLM was called
        mock_generate.assert_called_once()

    def test_validate_code_empty_input(self, orchestrator):
        """Test code validation rejects empty input"""
        with pytest.raises(ValueError, match="Code cannot be empty"):
            orchestrator.validate_code(code="", context={}, level="quick")

    @patch('resilient_agent.ResilientBaseAgent.generate_text')
    def test_validate_documentation_success(self, mock_generate, orchestrator, sample_docs, mock_llm_response):
        """Test documentation validation with mocked LLM"""
        mock_generate.return_value = mock_llm_response

        result = orchestrator.validate_documentation(
            documentation=sample_docs,
            context={"doc_type": "README"},
            level="quick"
        )

        assert isinstance(result, ValidationResult)
        assert result.validator_name == "doc-validator"

    @patch('resilient_agent.ResilientBaseAgent.generate_text')
    def test_validate_tests_success(self, mock_generate, orchestrator, sample_tests, mock_llm_response):
        """Test test validation with mocked LLM"""
        mock_generate.return_value = mock_llm_response

        result = orchestrator.validate_tests(
            test_code=sample_tests,
            context={"module_name": "auth"},
            level="quick"
        )

        assert isinstance(result, ValidationResult)
        assert result.validator_name == "test-validator"

    @pytest.mark.parametrize("level", ["quick", "standard", "thorough"])
    @patch('resilient_agent.ResilientBaseAgent.generate_text')
    def test_validation_levels(self, mock_generate, orchestrator, sample_code, mock_llm_response, level):
        """Test all validation levels work"""
        mock_generate.return_value = mock_llm_response

        result = orchestrator.validate_code(
            code=sample_code,
            context={"file_path": "test.py"},
            level=level
        )

        assert result is not None


# ============================================================================
# MODEL SELECTION TESTS
# ============================================================================

class TestModelSelection:
    """Test model selection logic"""

    def test_code_validator_model_stack(self, orchestrator):
        """Test code validator uses different models by level"""
        quick_model = orchestrator._select_model("code-validator", "quick")
        standard_model = orchestrator._select_model("code-validator", "standard")
        thorough_model = orchestrator._select_model("code-validator", "thorough")

        assert "haiku" in quick_model.lower()
        assert "sonnet" in standard_model.lower()
        assert "opus" in thorough_model.lower()

    def test_doc_validator_uses_sonnet(self, orchestrator):
        """Test doc validator uses Sonnet for all levels"""
        for level in ["quick", "standard", "thorough"]:
            model = orchestrator._select_model("doc-validator", level)
            assert "sonnet" in model.lower()

    def test_test_validator_uses_sonnet(self, orchestrator):
        """Test test validator uses Sonnet for all levels"""
        for level in ["quick", "standard", "thorough"]:
            model = orchestrator._select_model("test-validator", level)
            assert "sonnet" in model.lower()


# ============================================================================
# HELPER METHOD TESTS
# ============================================================================

class TestHelperMethods:
    """Test orchestrator helper methods"""

    def test_language_detection(self, orchestrator):
        """Test programming language detection"""
        assert orchestrator._detect_language(Path("test.py")) == "python"
        assert orchestrator._detect_language(Path("test.js")) == "javascript"
        assert orchestrator._detect_language(Path("test.ts")) == "typescript"
        assert orchestrator._detect_language(Path("test.go")) == "go"
        assert orchestrator._detect_language(Path("test.rs")) == "rust"

    def test_detect_validators_for_python_file(self, orchestrator):
        """Test validator detection for Python source file"""
        validators = orchestrator._detect_validators_for_file(Path("auth.py"))
        assert "code-validator" in validators
        assert "doc-validator" not in validators

    def test_detect_validators_for_test_file(self, orchestrator):
        """Test validator detection for test file"""
        validators = orchestrator._detect_validators_for_file(Path("test_auth.py"))
        assert "test-validator" in validators
        assert "code-validator" in validators  # Also validate test code quality

    def test_detect_validators_for_doc_file(self, orchestrator):
        """Test validator detection for documentation"""
        validators = orchestrator._detect_validators_for_file(Path("README.md"))
        assert "doc-validator" in validators
        assert "code-validator" not in validators

    def test_format_prompt(self, orchestrator):
        """Test prompt formatting with variables"""
        template = "Validate {language} code at {file_path}. Level: {level}"

        formatted = orchestrator._format_prompt(
            prompt_template=template,
            validator_name="code-validator",
            target_content="def foo(): pass",
            context={"file_path": "test.py", "language": "python"},
            level="quick"
        )

        assert "python" in formatted
        assert "test.py" in formatted
        assert "quick" in formatted


# ============================================================================
# ORCHESTRATION TESTS
# ============================================================================

class TestOrchestration:
    """Test run_all_validators() and orchestration"""

    @patch.object(ValidationOrchestrator, 'validate_code')
    def test_validate_single_file(self, mock_validate, orchestrator, temp_project):
        """Test validating a single Python file"""
        # Create test file
        test_file = temp_project / "test.py"
        test_file.write_text("def foo(): pass")

        # Mock validation result
        mock_validate.return_value = ValidationResult(
            validator_name="code-validator",
            status="PASS",
            score=95,
            findings=[],
            execution_time_ms=2000,
            model_used="claude-haiku-4-5-20250611",
            cost_usd=0.002
        )

        report = orchestrator.run_all_validators(
            target_path=str(test_file),
            level="quick"
        )

        assert isinstance(report, ValidationReport)
        assert len(report.results) > 0

    @patch.object(ValidationOrchestrator, 'validate_code')
    @patch.object(ValidationOrchestrator, 'validate_documentation')
    def test_validate_directory(self, mock_validate_doc, mock_validate_code, orchestrator, temp_project):
        """Test validating an entire directory"""
        # Create test files
        (temp_project / "auth.py").write_text("def authenticate(): pass")
        (temp_project / "README.md").write_text("# Project")

        # Mock results
        mock_validate_code.return_value = ValidationResult(
            validator_name="code-validator",
            status="PASS",
            score=95,
            findings=[],
            execution_time_ms=2000,
            model_used="claude-haiku-4-5-20250611",
            cost_usd=0.002
        )

        mock_validate_doc.return_value = ValidationResult(
            validator_name="doc-validator",
            status="PASS",
            score=90,
            findings=[],
            execution_time_ms=3000,
            model_used="claude-sonnet-4-5-20250929",
            cost_usd=0.005
        )

        report = orchestrator.run_all_validators(
            target_path=str(temp_project),
            level="quick",
            recursive=True
        )

        assert isinstance(report, ValidationReport)

    def test_run_validators_nonexistent_path(self, orchestrator):
        """Test error when path doesn't exist"""
        with pytest.raises(FileNotFoundError):
            orchestrator.run_all_validators(
                target_path="/nonexistent/path",
                level="quick"
            )


# ============================================================================
# REPORT GENERATION TESTS
# ============================================================================

class TestReportGeneration:
    """Test report generation in different formats"""

    def test_generate_markdown_report(self, orchestrator):
        """Test markdown report generation"""
        # Create sample report
        result1 = ValidationResult(
            validator_name="code-validator",
            status="PASS",
            score=95,
            findings=[],
            execution_time_ms=2000,
            model_used="claude-haiku-4-5-20250611",
            cost_usd=0.002
        )

        result2 = ValidationResult(
            validator_name="doc-validator",
            status="FAIL",
            score=60,
            findings=[
                ValidationFinding(
                    id="DOC-001",
                    severity="HIGH",
                    category="completeness",
                    subcategory="missing-section",
                    location="README.md",
                    issue="Missing installation section",
                    recommendation="Add installation instructions"
                )
            ],
            execution_time_ms=3000,
            model_used="claude-sonnet-4-5-20250929",
            cost_usd=0.005
        )

        report = ValidationReport.from_results(
            results=[result1, result2],
            total_time_ms=5000
        )

        markdown = orchestrator.generate_report(report, format="markdown")

        assert "# Validation Report" in markdown
        assert "code-validator" in markdown
        assert "doc-validator" in markdown
        assert "PASS" in markdown
        assert "FAIL" in markdown

    def test_generate_json_report(self, orchestrator):
        """Test JSON report generation"""
        result = ValidationResult(
            validator_name="code-validator",
            status="PASS",
            score=95,
            findings=[],
            execution_time_ms=2000,
            model_used="claude-haiku-4-5-20250611",
            cost_usd=0.002
        )

        report = ValidationReport.from_results(
            results=[result],
            total_time_ms=2000
        )

        json_report = orchestrator.generate_report(report, format="json")

        # Should be valid JSON
        parsed = json.loads(json_report)
        assert "overall_status" in parsed
        assert "results" in parsed

    def test_generate_text_report(self, orchestrator):
        """Test text report generation"""
        result = ValidationResult(
            validator_name="code-validator",
            status="PASS",
            score=95,
            findings=[],
            execution_time_ms=2000,
            model_used="claude-haiku-4-5-20250611",
            cost_usd=0.002
        )

        report = ValidationReport.from_results(
            results=[result],
            total_time_ms=2000
        )

        text = orchestrator.generate_report(report, format="text")

        assert len(text) > 0
        assert isinstance(text, str)
        assert "VALIDATION REPORT" in text


# ============================================================================
# STATS TRACKING TESTS
# ============================================================================

class TestStatsTracking:
    """Test execution statistics tracking"""

    @patch('resilient_agent.ResilientBaseAgent.generate_text')
    def test_stats_updated_after_validation(self, mock_generate, orchestrator, sample_code, mock_llm_response):
        """Test stats are updated after validation"""
        mock_generate.return_value = mock_llm_response

        # Get initial stats
        initial_stats = orchestrator.get_execution_stats()
        assert initial_stats["total_validations"] == 0

        # Run validation
        orchestrator.validate_code(
            code=sample_code,
            context={"file_path": "test.py"},
            level="quick"
        )

        # Check stats updated
        updated_stats = orchestrator.get_execution_stats()
        assert updated_stats["total_validations"] == 1
        assert updated_stats["total_cost_usd"] > 0
        assert updated_stats["total_time_seconds"] > 0

    def test_reset_stats(self, orchestrator):
        """Test resetting statistics"""
        # Manually set some stats
        orchestrator._execution_stats["total_validations"] = 10
        orchestrator._execution_stats["total_cost"] = 1.5

        # Reset
        orchestrator.reset_stats()

        # Verify reset
        stats = orchestrator.get_execution_stats()
        assert stats["total_validations"] == 0
        assert stats["total_cost_usd"] == 0.0

    def test_average_calculations(self, orchestrator):
        """Test average cost and time calculations"""
        orchestrator._execution_stats["total_validations"] = 5
        orchestrator._execution_stats["total_cost"] = 0.025
        orchestrator._execution_stats["total_time"] = 50.0

        stats = orchestrator.get_execution_stats()

        assert stats["average_cost_usd"] == 0.005
        assert stats["average_time_seconds"] == 10.0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and recovery"""

    @patch('resilient_agent.ResilientBaseAgent.generate_text')
    def test_handles_llm_error_gracefully(self, mock_generate, orchestrator, sample_code):
        """Test graceful handling when LLM fails"""
        mock_generate.side_effect = Exception("API Error")

        # Should not raise, should return FAIL result
        result = orchestrator.validate_code(
            code=sample_code,
            context={"file_path": "test.py"},
            level="quick"
        )

        assert result.status == "FAIL"
        assert len(result.findings) > 0

    @patch('resilient_agent.ResilientBaseAgent.generate_text')
    def test_handles_invalid_json_response(self, mock_generate, orchestrator, sample_code):
        """Test handling of non-JSON LLM response"""
        mock_generate.return_value = "This is not JSON"

        result = orchestrator.validate_code(
            code=sample_code,
            context={"file_path": "test.py"},
            level="quick"
        )

        assert result.status == "FAIL"

    def test_validate_code_with_none_context(self, orchestrator, sample_code):
        """Test validation with None context (should use defaults)"""
        with patch.object(orchestrator, 'generate_text') as mock_generate:
            mock_generate.return_value = json.dumps({
                "status": "PASS",
                "score": 95,
                "findings": [],
                "passed_checks": [],
                "metrics": {},
                "target": "unknown"
            })

            result = orchestrator.validate_code(
                code=sample_code,
                context=None,
                level="quick"
            )

            assert result is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhaseBIntegration:
    """Test integration with Phase B infrastructure"""

    def test_inherits_from_resilient_agent(self, orchestrator):
        """Test orchestrator inherits from ResilientBaseAgent"""
        from resilient_agent import ResilientBaseAgent
        assert isinstance(orchestrator, ResilientBaseAgent)

    def test_has_generate_text_method(self):
        """Test orchestrator has generate_text from ResilientBaseAgent"""
        from resilient_agent import ResilientBaseAgent
        assert hasattr(ResilientBaseAgent, 'generate_text')
        assert callable(getattr(ResilientBaseAgent, 'generate_text'))

    def test_session_manager_integration(self, orchestrator):
        """Test session manager is integrated"""
        assert orchestrator.session_manager is not None
        assert hasattr(orchestrator.session_manager, 'add_turn')  # Check for actual method

    def test_repr_method(self, orchestrator):
        """Test string representation"""
        repr_str = repr(orchestrator)

        assert "ValidationOrchestrator" in repr_str
        assert "validators=" in repr_str
        assert "default_level=" in repr_str


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
