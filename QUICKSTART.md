# Phase 2 Validation System - Quick Start Guide

## Installation

Add the library to your project:

```python
import sys
sys.path.insert(0, '/home/jevenson/.claude/lib')
```

---

## 1️⃣ Basic Usage (Simplest)

```python
from validation import ValidationOrchestrator

# Create orchestrator
orchestrator = ValidationOrchestrator(project_root=".")

# Validate code
result = orchestrator.validate_code(
    code="""
    def add(a, b):
        return a + b
    """,
    context={"file_path": "math_utils.py"},
    level="standard"  # Options: "quick", "standard", "thorough"
)

print(f"Overall score: {result.overall_score}")
print(f"Findings: {len(result.findings)}")
```

---

## 2️⃣ Recommended: Complete System Setup

```python
from validation import create_validation_system

# Create complete validation system
system = create_validation_system(
    project_root=".",
    validators=["code-validator", "doc-validator", "test-validator"],
    default_level="standard"
)

# Access components
orchestrator = system["orchestrator"]
critic_integration = system["critic_integration"]
result_aggregator = system["result_aggregator"]

# Validate code
result = orchestrator.validate_code(
    code=your_code,
    context={"file_path": "example.py"},
    level="standard"
)
```

---

## 3️⃣ Custom Configuration

```python
from validation import ValidationOrchestrator

# Custom validators and quality level
orchestrator = ValidationOrchestrator(
    project_root="/path/to/project",
    validators=["code-validator", "doc-validator"],
    default_level="thorough"  # Use highest quality models
)

# Validate with custom level
result = orchestrator.validate_code(
    code=code_snippet,
    context={
        "file_path": "auth.py",
        "language": "python"
    },
    level="quick"  # Override default for this validation
)
```

---

## 4️⃣ Using Model Selector Directly

```python
from utils import ModelSelector

selector = ModelSelector()

# Select model for specific task
model = selector.select_model(
    task_type="code-validation",
    complexity="standard"
)

# Get temperature for task
temperature = selector.get_temperature("code-validation")

# Estimate cost
cost = selector.estimate_cost(
    model_name="claude-sonnet-4-5-20250929",
    input_tokens=1000,
    output_tokens=500
)

print(f"Model: {model}")
print(f"Temperature: {temperature}")
print(f"Estimated cost: ${cost:.6f}")

# Get model recommendation based on budget
recommendation = selector.recommend_model(
    task_type="code-validation",
    budget_usd=0.01,
    estimated_tokens=2000
)

print(f"Recommended: {recommendation['model']} ({recommendation['complexity']})")
```

---

## 5️⃣ Dependency Injection (Testing/Mocking)

```python
from validation import ValidationOrchestrator, CriticIntegration
from protocols import DependencyFactory
from unittest.mock import Mock

# Create mock critic for testing
mock_critic = Mock()
mock_critic.review_code.return_value = {
    "overall_score": 95,
    "findings": [],
    "critics_used": ["test-critic"]
}

# Create custom factory with mock
factory = DependencyFactory(
    critic_impl=mock_critic,
    config={"api_key": "test-key"}
)

# Create orchestrator and integration
orchestrator = ValidationOrchestrator(project_root=".")
critic_integration = CriticIntegration(orchestrator, factory=factory)

# Use mocked critic
critic = critic_integration.factory.get_critic_orchestrator()
result = critic.review_code("test code")
print(result)  # Uses mock
```

---

## 6️⃣ Validation Levels Explained

```python
from validation import ValidationOrchestrator

orchestrator = ValidationOrchestrator(project_root=".")

# QUICK - Fast, cheap validation (uses Haiku)
# Best for: CI/CD, pre-commit hooks, rapid iteration
quick_result = orchestrator.validate_code(
    code=code,
    context={"file_path": "test.py"},
    level="quick"  # ~$0.0003 per validation
)

# STANDARD - Balanced quality/cost (uses Sonnet)
# Best for: Regular development, code reviews
standard_result = orchestrator.validate_code(
    code=code,
    context={"file_path": "test.py"},
    level="standard"  # ~$0.01 per validation (default)
)

# THOROUGH - Highest quality (uses Opus)
# Best for: Critical code, security reviews, production releases
thorough_result = orchestrator.validate_code(
    code=code,
    context={"file_path": "test.py"},
    level="thorough"  # ~$0.05 per validation
)
```

---

## 7️⃣ Available Task Types

```python
from utils import ModelSelector

selector = ModelSelector()

# All available task types:
task_types = [
    "code-validation",      # Code quality checks
    "documentation",        # Doc generation/review
    "test-validation",      # Test suite review
    "critique",             # Deep code critique (always Opus)
    "refactoring",          # Refactoring suggestions
    "security-analysis",    # Security vulnerability scan
    "general",              # General-purpose tasks
    "planning"              # Architecture/planning tasks
]

# Example: Security analysis always uses low temperature (0.1)
model = selector.select_model("security-analysis", "thorough")
temp = selector.get_temperature("security-analysis")

print(f"Security model: {model}")
print(f"Temperature: {temp}")  # 0.1 for deterministic results
```

---

## 8️⃣ Model Selection Summary

| Task Type | Quick | Standard | Thorough |
|-----------|-------|----------|----------|
| Code Validation | Haiku | Sonnet | Opus |
| Documentation | Sonnet | Sonnet | Sonnet |
| Test Validation | Haiku | Sonnet | Opus |
| Critique | **Opus** | **Opus** | **Opus** |
| Security Analysis | Haiku | Sonnet | Opus |

**Note:** Critique always uses Opus for unbiased, highest-quality analysis.

---

## 9️⃣ Cost Estimation Examples

```python
from utils import ModelSelector

selector = ModelSelector()

# Compare costs across models
comparison = selector.compare_costs(
    input_tokens=1000,
    output_tokens=500
)

for model, cost in comparison.items():
    print(f"{model}: ${cost:.6f}")

# Output:
# claude-haiku-4-5-20250611: $0.000875
# claude-sonnet-4-5-20250929: $0.010500
# claude-opus-4-20250514: $0.022500
```

---

## 🔟 Real-World Example

```python
from validation import create_validation_system
from pathlib import Path

# Initialize system
system = create_validation_system(
    project_root="./my_project",
    validators=["code-validator", "doc-validator", "test-validator"],
    default_level="standard"
)

orchestrator = system["orchestrator"]

# Read code file
code_file = Path("./my_project/auth.py")
code = code_file.read_text()

# Validate with context
result = orchestrator.validate_code(
    code=code,
    context={
        "file_path": str(code_file),
        "language": "python",
        "module": "authentication"
    },
    level="thorough"  # High-stakes security code
)

# Process results
print(f"Overall Score: {result.overall_score}/100")
print(f"Total Findings: {len(result.findings)}")

# Show findings
for finding in result.findings:
    print(f"\n{finding.severity.upper()}: {finding.message}")
    print(f"  Location: Line {finding.line_number}")
    if finding.suggestion:
        print(f"  Suggestion: {finding.suggestion}")

# Estimate cost
print(f"\nValidation Cost: ${result.cost_usd:.6f}")
```

---

## 📚 Additional Resources

- **Full Documentation:** `/home/jevenson/.claude/lib/PHASE_2_COMPLETE_VERIFIED.md`
- **Security Review:** `/home/jevenson/.claude/lib/PHASE_2_SECURITY_REVIEW.md`
- **Test Examples:** `/home/jevenson/.claude/lib/tests/integration/test_module_integration.py`
- **GitHub:** https://github.com/jevenson76/Atlas-Orchestrator

---

## 🆘 Troubleshooting

### Import Error: No module named 'validation'

```python
# Add library to path BEFORE importing
import sys
sys.path.insert(0, '/home/jevenson/.claude/lib')

# Then import
from validation import ValidationOrchestrator
```

### AttributeError: 'ValidationOrchestrator' object has no attribute...

```python
# Make sure you're using Phase 2 parameters
# ✅ Correct:
orchestrator = ValidationOrchestrator(
    project_root=".",
    validators=["code-validator"],
    default_level="standard"
)

# ❌ Incorrect (no session_id parameter):
orchestrator = ValidationOrchestrator(
    project_root=".",
    session_id="123"  # This parameter doesn't exist!
)
```

### Model selection not working

```python
# ModelSelector is automatically initialized by ValidationOrchestrator
# You don't need to pass it manually

# ✅ Correct:
orchestrator = ValidationOrchestrator(project_root=".")
# Model selector is already available as orchestrator.model_selector

# ❌ Don't do this:
from utils import ModelSelector
selector = ModelSelector()
orchestrator = ValidationOrchestrator(
    project_root=".",
    model_selector=selector  # Parameter doesn't exist!
)
```

---

**Version:** 2.0.0
**Last Updated:** 2025-11-09
**Status:** Production Ready ✅
