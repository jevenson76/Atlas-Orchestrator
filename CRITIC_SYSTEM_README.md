# C3 Specialized Critic System

**Priority 4 Component C3: Unbiased Code Evaluation with Fresh Context**

## Table of Contents

1. [Philosophy](#philosophy)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Individual Critics](#individual-critics)
5. [Integration](#integration)
6. [Cost Analysis](#cost-analysis)
7. [Best Practices](#best-practices)
8. [API Reference](#api-reference)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Philosophy

### "Creator Cannot Be Judge"

The C3 Critic System implements a fundamental principle: **the agent that creates code cannot fairly evaluate it**. This separation ensures unbiased, objective analysis.

### Core Principles

1. **FRESH CONTEXT**: Critics receive ONLY the code to review, with zero knowledge of:
   - Who wrote the code
   - Why it was written
   - What task it was created for
   - What the intended behavior is

2. **OPUS MANDATORY**: All critics use `claude-opus-4-20250514` with `enable_fallback=False`
   - No fallback to cheaper models
   - Consistent, high-quality analysis
   - Predictable costs

3. **DOMAIN SPECIALIZATION**: Each critic focuses on ONE domain:
   - Security Critic → Vulnerabilities, OWASP compliance
   - Performance Critic → Bottlenecks, algorithm complexity
   - Architecture Critic → SOLID principles, design patterns
   - Code Quality Critic → Readability, maintainability
   - Documentation Critic → Completeness, clarity

4. **ACTIONABLE OUTPUT**: Every finding includes:
   - Specific location (file, line, function)
   - Severity (CRITICAL, HIGH, MEDIUM, LOW)
   - Impact (what breaks)
   - Concrete recommendation (how to fix)
   - Code examples (before/after)

5. **COMPLEMENT, DON'T REPLACE**: Critics enhance validators:
   - **Validators** (fast, structural): "Is this feature present?"
   - **Critics** (deep, semantic): "How well does this work?"

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    C3 CRITIC SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         CriticOrchestrator                             │    │
│  │  - Loads 5 specialized critics                         │    │
│  │  - Enforces FRESH CONTEXT (code only)                  │    │
│  │  - Enforces OPUS MANDATORY (no fallback)               │    │
│  │  - Aggregates results                                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ├──────────────────────┐               │
│                           │                      │               │
│  ┌──────────────────┐  ┌─▼──────────────┐  ┌───▼───────────┐  │
│  │  Security        │  │  Performance    │  │  Architecture │  │
│  │  Critic          │  │  Critic         │  │  Critic       │  │
│  │  (Opus 4)        │  │  (Opus 4)       │  │  (Opus 4)     │  │
│  └──────────────────┘  └─────────────────┘  └───────────────┘  │
│                                                                  │
│  ┌──────────────────┐  ┌─────────────────┐                     │
│  │  Code Quality    │  │  Documentation  │                     │
│  │  Critic          │  │  Critic         │                     │
│  │  (Opus 4)        │  │  (Opus 4)       │                     │
│  └──────────────────┘  └─────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Integrates with
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│            ValidationOrchestrator (Priority 2)                   │
│  - Runs validators first (fast, structural checks)              │
│  - Runs critics second (deep, semantic analysis)                │
│  - Combines results for comprehensive evaluation                │
└─────────────────────────────────────────────────────────────────┘
```

### Component Structure

```
~/.claude/
├── lib/
│   ├── critic_orchestrator.py      # Main orchestrator (600+ lines)
│   ├── validation_orchestrator.py  # Validator integration (350+ lines added)
│   ├── agent_registry.py           # Updated with Opus 4
│   ├── promote_agents.py           # Registers critics
│   ├── test_critic_system.py       # Comprehensive tests (24 tests)
│   ├── demo_critic_system.py       # Interactive demo (6 scenarios)
│   └── CRITIC_SYSTEM_README.md     # This file
│
└── agents/
    └── critics/
        ├── security-critic.md           # 7.8K
        ├── performance-critic.md        # 11K
        ├── architecture-critic.md       # 15K
        ├── code-quality-critic.md       # 17K
        └── documentation-critic.md      # 19K
```

---

## Quick Start

### Prerequisites

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key"

# Python 3.9+
pip install anthropic python-dotenv
```

### Basic Usage

```python
from critic_orchestrator import CriticOrchestrator

# Initialize orchestrator
orchestrator = CriticOrchestrator()

# Review code with security critic
results = orchestrator.review_code(
    code_snippet=your_code,
    critics=["security-critic"],
    file_path="auth.py"
)

# Get result
result = results["security-critic"]
print(f"Score: {result.overall_score}/100")
print(f"Grade: {result.grade}")
print(f"Findings: {len(result.findings)}")
```

### Complete Example

```python
from critic_orchestrator import CriticOrchestrator

code = '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
'''

# Initialize
orchestrator = CriticOrchestrator()

# Run all critics
results = orchestrator.review_code(
    code_snippet=code,
    file_path="auth.py",
    language="python"
)

# Generate aggregated report
report = orchestrator.generate_report(
    results=results,
    code_snippet=code,
    file_path="auth.py"
)

# Print results
orchestrator.print_report(report)
```

### Integration with Validators

```python
from validation_orchestrator import ValidationOrchestrator

# Initialize
orchestrator = ValidationOrchestrator(project_root=".")

# Two-stage evaluation (validators + critics)
result = orchestrator.validate_with_critics(
    code=your_code,
    context={"file_path": "auth.py", "criticality": "high"},
    level="standard"  # validators + 3 key critics
)

# Check recommendation
if result["recommendation"] == "NO-GO":
    print("Critical issues found!")
    print(f"Critical: {result['metrics']['critical_findings']}")
    print(f"High: {result['metrics']['high_findings']}")

# Print combined report
orchestrator.print_combined_report(result)
```

---

## Individual Critics

### Security Critic

**Focus**: Security vulnerabilities, OWASP compliance, attack vectors

**Detects**:
- SQL injection (CRITICAL)
- XSS vulnerabilities (CRITICAL)
- Authentication/authorization issues (CRITICAL)
- Sensitive data exposure (HIGH)
- CSRF vulnerabilities (HIGH)
- Insecure deserialization (HIGH)
- Missing input validation (MEDIUM)

**Example Output**:
```json
{
  "critic_type": "security",
  "overall_score": 25,
  "risk_level": "CRITICAL",
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "SQL Injection",
      "title": "Unsanitized user input in SQL query",
      "location": {"file": "auth.py", "line": 2},
      "impact": "Complete database compromise possible",
      "recommendation": "Use parameterized queries",
      "fixed_code": "query = 'SELECT * FROM users WHERE id = ?'"
    }
  ]
}
```

**Cost**: ~$0.06 per call, 35 seconds

---

### Performance Critic

**Focus**: Performance bottlenecks, algorithmic complexity, scalability

**Detects**:
- N+1 query patterns (CRITICAL)
- Missing database indexes (CRITICAL)
- Quadratic/exponential algorithms (HIGH)
- Memory leaks (CRITICAL)
- Blocking I/O in async contexts (HIGH)
- Inefficient data structures (MEDIUM)
- Missing caching (MEDIUM)

**Example Output**:
```json
{
  "critic_type": "performance",
  "overall_score": 30,
  "performance_grade": "CRITICAL",
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "Database",
      "title": "N+1 query pattern",
      "complexity": {"current": "O(n) queries", "optimal": "O(1) query"},
      "benchmark": {
        "current_performance": "2000ms for 100 users",
        "estimated_optimized": "50ms for 100 users",
        "scaling_impact": "At 1000 users: 20s vs 50ms (400x improvement)"
      },
      "recommendation": "Use JOIN or batch load with IN clause"
    }
  ]
}
```

**Cost**: ~$0.055 per call, 32 seconds

---

### Architecture Critic

**Focus**: SOLID principles, design patterns, coupling/cohesion

**Detects**:
- Single Responsibility Principle violations (CRITICAL)
- God objects (CRITICAL)
- Tight coupling (HIGH)
- Dependency Inversion violations (HIGH)
- Missing interfaces/abstractions (MEDIUM)
- Circular dependencies (CRITICAL)
- Anemic domain models (MEDIUM)

**Example Output**:
```json
{
  "critic_type": "architecture",
  "overall_score": 20,
  "architecture_grade": "CRITICAL",
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "SOLID",
      "principle_violated": "SRP",
      "title": "UserController violates Single Responsibility Principle",
      "impact": "Changes to any concern require modifying this class",
      "recommended_design": "Layered architecture: Controller → Service → Repository",
      "patterns_suggested": ["Repository", "Service Layer", "Dependency Injection"]
    }
  ]
}
```

**Cost**: ~$0.058 per call, 33 seconds

---

### Code Quality Critic

**Focus**: Readability, maintainability, code smells

**Detects**:
- Poor naming (HIGH)
- Deep nesting (HIGH)
- Magic numbers (MEDIUM)
- Code duplication (HIGH)
- Missing error handling (CRITICAL)
- Excessively long functions (HIGH)
- High cyclomatic complexity (HIGH)
- Missing type hints (MEDIUM)

**Example Output**:
```json
{
  "critic_type": "code_quality",
  "overall_score": 35,
  "quality_grade": "POOR",
  "findings": [
    {
      "severity": "HIGH",
      "category": "Readability",
      "title": "Unclear function and variable naming",
      "metrics": {
        "cyclomatic_complexity": 5,
        "function_length": 13,
        "nesting_depth": 4
      },
      "recommendation": "Rename function to describe purpose, add docstring",
      "improved_code": "def transform_sensor_readings(...):"
    }
  ]
}
```

**Cost**: ~$0.05 per call, 28 seconds

---

### Documentation Critic

**Focus**: Documentation completeness, clarity, examples

**Detects**:
- Missing docstrings (CRITICAL)
- Incomplete docstrings (HIGH)
- Missing type hints (HIGH)
- Missing examples (MEDIUM)
- Undocumented errors (HIGH)
- Missing README (CRITICAL)
- Outdated documentation (MEDIUM)

**Example Output**:
```json
{
  "critic_type": "documentation",
  "overall_score": 20,
  "documentation_grade": "CRITICAL",
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "Docstring",
      "title": "Public function missing docstring entirely",
      "impact": "Users don't know: what function does, parameters, return value, example usage",
      "recommendation": "Add comprehensive Google-style docstring with examples",
      "documented_code": "def calculate_score(...):\n    \"\"\"Calculate weighted average...\"\"\""
    }
  ]
}
```

**Cost**: ~$0.045 per call, 26 seconds

---

## Integration

### With Validators (Recommended)

```python
from validation_orchestrator import ValidationOrchestrator

orchestrator = ValidationOrchestrator(project_root=".")

# LEVEL: quick (validators only, no critics)
result = orchestrator.validate_with_critics(
    code=code,
    level="quick"
)
# Cost: ~$0.001-$0.005, Time: 2-5s

# LEVEL: standard (validators + 3 key critics)
result = orchestrator.validate_with_critics(
    code=code,
    level="standard"
)
# Cost: ~$0.15-$0.20, Time: 40-60s
# Critics: security, performance, architecture

# LEVEL: thorough (validators + all 5 critics)
result = orchestrator.validate_with_critics(
    code=code,
    level="thorough"
)
# Cost: ~$0.25-$0.35, Time: 90-120s
# Critics: all 5

# Custom critics
result = orchestrator.validate_with_critics(
    code=code,
    critics=["security-critic", "documentation-critic"],
    run_validators=True
)
```

### Standalone (Critics Only)

```python
from critic_orchestrator import CriticOrchestrator

orchestrator = CriticOrchestrator()

# Single critic
results = orchestrator.review_code(
    code_snippet=code,
    critics=["security-critic"]
)

# Multiple critics
results = orchestrator.review_code(
    code_snippet=code,
    critics=["security-critic", "performance-critic"]
)

# All critics (default)
results = orchestrator.review_code(
    code_snippet=code
)
```

---

## Cost Analysis

### Per-Critic Costs

| Critic | Model | Est. Cost | Est. Time | Use Case |
|--------|-------|-----------|-----------|----------|
| Security | Opus 4 | $0.06 | 35s | Pre-production auth code |
| Performance | Opus 4 | $0.055 | 32s | Database queries, algorithms |
| Architecture | Opus 4 | $0.058 | 33s | System design review |
| Code Quality | Opus 4 | $0.05 | 28s | PR review |
| Documentation | Opus 4 | $0.045 | 26s | Public API documentation |

### Level Costs

| Level | Validators | Critics | Total Cost | Total Time | Use Case |
|-------|------------|---------|------------|------------|----------|
| quick | 1 (Haiku) | 0 | $0.001-$0.005 | 2-5s | CI/CD quick check |
| standard | 1 (Sonnet) | 3 | $0.15-$0.20 | 40-60s | Pre-commit review |
| thorough | 1 (Opus) | 5 | $0.25-$0.35 | 90-120s | Pre-production gate |

### Cost Optimization

1. **Use validators first**: Filter out obvious issues before running critics
2. **Choose critics strategically**: Run only relevant critics for the code type
3. **Batch reviews**: Review multiple files together to amortize setup costs
4. **Use level appropriately**:
   - `quick`: CI/CD, every commit
   - `standard`: Pull requests
   - `thorough`: Production deployment gates

---

## Best Practices

### When to Use Critics

✅ **DO use critics for**:
- Security-critical code (auth, payments, data handling)
- Performance-sensitive code (database queries, hot paths)
- Public APIs (architecture, documentation)
- Production deployment gates
- Complex business logic

❌ **DON'T use critics for**:
- Every single file (use validators instead)
- Generated code
- Test files (unless testing test quality)
- Simple configuration files

### Choosing Critics

**Security-critical code**:
```python
critics=["security-critic", "architecture-critic"]
```

**Performance-sensitive code**:
```python
critics=["performance-critic", "code-quality-critic"]
```

**Public APIs**:
```python
critics=["architecture-critic", "documentation-critic", "code-quality-critic"]
```

**Pre-production**:
```python
critics=None  # All 5 critics
```

### Responding to Findings

**CRITICAL findings**: MUST fix before merging
- SQL injection
- Authentication bypass
- N+1 queries (high traffic)
- God objects
- Missing docstrings on public APIs

**HIGH findings**: SHOULD fix before production
- Missing input validation
- Inefficient algorithms
- SOLID violations
- Poor naming
- Incomplete documentation

**MEDIUM findings**: Consider fixing
- Suboptimal data structures
- Missing comments
- Magic numbers

**LOW findings**: Optional
- Micro-optimizations
- Minor style issues

---

## API Reference

### CriticOrchestrator

```python
class CriticOrchestrator:
    """Orchestrates specialized critic agents."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize orchestrator.

        Args:
            api_key: Anthropic API key (uses env var if not provided)
        """

    def review_code(
        self,
        code_snippet: str,
        file_path: Optional[str] = None,
        critics: Optional[List[str]] = None,
        language: Optional[str] = None
    ) -> Dict[str, CriticResult]:
        """Review code with specified critics.

        Args:
            code_snippet: Code to review
            file_path: Optional file path for context
            critics: List of critic IDs (None = all critics)
            language: Language hint (auto-detected if None)

        Returns:
            Dict mapping critic_id to CriticResult
        """

    def generate_report(
        self,
        results: Dict[str, CriticResult],
        code_snippet: str,
        file_path: Optional[str] = None
    ) -> AggregatedReport:
        """Generate aggregated report.

        Args:
            results: Critic results
            code_snippet: Code that was reviewed
            file_path: Optional file path

        Returns:
            AggregatedReport with combined findings
        """

    def print_report(self, report: AggregatedReport):
        """Print human-readable report."""
```

### ValidationOrchestrator Integration

```python
class ValidationOrchestrator:
    """Validation orchestrator with critic integration."""

    def validate_with_critics(
        self,
        code: str,
        context: Optional[Dict] = None,
        level: Optional[Literal["quick", "standard", "thorough"]] = None,
        run_validators: bool = True,
        critics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Comprehensive evaluation (validators + critics).

        Args:
            code: Source code
            context: Optional context
            level: Validation level
            run_validators: Run validators first
            critics: Override critic selection

        Returns:
            Dict with validator_result, critic_results, aggregated_report,
            overall_score, recommendation, etc.
        """

    def print_combined_report(self, result: Dict[str, Any]):
        """Print combined validator + critic report."""
```

---

## Testing

### Run Tests

```bash
# All tests
pytest test_critic_system.py -v

# Specific test suite
pytest test_critic_system.py::TestCriticInitialization -v

# Skip integration tests (require API key)
pytest test_critic_system.py -v -m "not integration"
```

### Test Coverage

- ✅ Critic initialization (3 tests)
- ✅ Fresh context enforcement (2 tests)
- ✅ JSON output parsing (4 tests)
- ✅ Individual critic functionality (3 tests)
- ✅ Aggregated reporting (2 tests)
- ✅ Validator-critic integration (3 tests)
- ✅ Cost tracking (1 test)
- ✅ Error handling (4 tests)
- ✅ Integration tests (2 tests)

**Total: 24 tests**

### Run Demo

```bash
python3 demo_critic_system.py
```

**6 interactive demos**:
1. Single critic analysis
2. Multiple critics in parallel
3. All 5 critics
4. Validator + critic integration
5. Good code analysis
6. Cost comparison

---

## Troubleshooting

### Issue: "Failed to load registry: 'claude-3-opus-20240229' is not a valid ModelTier"

**Cause**: Old registry file with Opus 3 model

**Solution**:
```bash
# Regenerate registry with Opus 4
cd ~/.claude/lib
python3 promote_agents.py
```

---

### Issue: "Critic definition not found"

**Cause**: Critic .md files not in expected location

**Solution**:
```bash
# Verify files exist
ls ~/.claude/agents/critics/

# Should show:
# security-critic.md
# performance-critic.md
# architecture-critic.md
# code-quality-critic.md
# documentation-critic.md
```

---

### Issue: High costs

**Cause**: Running all critics on every file

**Solution**:
- Use `level="quick"` for CI/CD (validators only)
- Use `level="standard"` for PRs (3 critics)
- Use `level="thorough"` only for production gates
- Run specific critics for specific code types
- Use validators first to filter obvious issues

---

### Issue: Slow performance

**Cause**: Critics use Opus 4 (30-35s each)

**Solution**:
- Run critics in parallel (handled automatically)
- Run only relevant critics
- Use validators first (2-5s with Haiku)
- Run critics async in background for large codebases

---

### Issue: "No API key"

**Cause**: ANTHROPIC_API_KEY not set

**Solution**:
```bash
export ANTHROPIC_API_KEY="your-api-key"

# Or add to ~/.bashrc
echo 'export ANTHROPIC_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

---

## Support

- **Documentation**: This file
- **Tests**: `test_critic_system.py`
- **Demo**: `demo_critic_system.py`
- **Source**: `critic_orchestrator.py`, `validation_orchestrator.py`

For issues or questions, see:
- Test suite for expected behavior
- Demo script for usage examples
- Critic definitions in `~/.claude/agents/critics/`

---

## License

This is part of the Priority 4 Component C3 implementation.

**Last Updated**: November 3, 2025
**Version**: 1.0.0
**Component**: C3 Specialized Critic System
