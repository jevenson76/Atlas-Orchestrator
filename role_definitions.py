"""
Role Definitions for Specialized Multi-AI Orchestration

This module defines the 4 specialized roles used in the orchestrator:
- ARCHITECT: High-level design and planning
- DEVELOPER: Implementation and code generation
- TESTER: Test generation and validation
- REVIEWER: Final quality review and assessment

Each role is optimized for quality with appropriate model selection and fallback chains.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class RoleType(Enum):
    """Enum for role types."""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"


@dataclass
class Role:
    """
    Definition of a specialized AI role.

    Each role has specific responsibilities, model selection optimized for quality,
    and fallback chains for resilience.
    """
    name: str
    role_type: RoleType
    description: str
    responsibilities: List[str]

    # Model configuration (quality-optimized)
    primary_model: str
    fallback_models: List[str]

    # Generation parameters
    temperature: float
    max_tokens: int

    # Cost estimation (per 1M tokens: input, output)
    estimated_cost_per_1m: tuple[float, float]

    # System prompt
    system_prompt: str

    # Output format expectations
    output_format: str = "structured_json"

    # Quality requirements
    min_quality_score: int = 90

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            'name': self.name,
            'role_type': self.role_type.value,
            'description': self.description,
            'responsibilities': self.responsibilities,
            'primary_model': self.primary_model,
            'fallback_models': self.fallback_models,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'estimated_cost_per_1m': self.estimated_cost_per_1m,
            'system_prompt': self.system_prompt,
            'output_format': self.output_format,
            'min_quality_score': self.min_quality_score,
            'metadata': self.metadata
        }


# Define the 4 specialized roles

ARCHITECT_ROLE = Role(
    name="Architect",
    role_type=RoleType.ARCHITECT,
    description="High-level system architect responsible for design, planning, and architectural decisions",
    responsibilities=[
        "Analyze requirements and system context",
        "Design high-level architecture and component structure",
        "Create detailed implementation plans",
        "Identify potential risks and edge cases",
        "Define integration points and dependencies",
        "Provide design rationale and decision justification"
    ],
    primary_model="claude-3-opus-20240229",  # Opus for best planning
    fallback_models=[
        "claude-3-5-sonnet-20241022",  # Sonnet as first fallback
        "gpt-4"  # GPT-4 as last resort
    ],
    temperature=0.3,  # Lower temperature for more focused planning
    max_tokens=4096,  # Larger token budget for comprehensive plans
    estimated_cost_per_1m=(15.00, 75.00),  # Opus pricing
    system_prompt="""You are an expert software architect with deep expertise in system design,
software architecture patterns, and best practices.

Your role is to:
1. Analyze requirements thoroughly and identify key challenges
2. Design robust, scalable, and maintainable system architectures
3. Create detailed implementation plans with clear phases
4. Identify potential risks, edge cases, and failure modes
5. Define clear integration points and dependencies
6. Provide strong technical justification for all design decisions

Output Format:
Provide your analysis in structured JSON format:
{
    "analysis": {
        "requirements": ["list of key requirements"],
        "challenges": ["identified challenges"],
        "constraints": ["technical and business constraints"]
    },
    "architecture": {
        "overview": "high-level description",
        "components": [{"name": "...", "responsibility": "...", "interfaces": [...]}],
        "data_flow": "description of data flow",
        "integration_points": [...]
    },
    "implementation_plan": {
        "phases": [{"phase": 1, "tasks": [...], "dependencies": [...]}],
        "estimated_effort": "...",
        "risks": [{"risk": "...", "mitigation": "..."}]
    },
    "design_decisions": [
        {"decision": "...", "rationale": "...", "alternatives_considered": [...]}
    ]
}

Focus on production-grade quality, maintainability, and scalability.""",
    output_format="structured_json",
    min_quality_score=90,
    metadata={'role_priority': 'high', 'cost_tier': 'premium'}
)


DEVELOPER_ROLE = Role(
    name="Developer",
    role_type=RoleType.DEVELOPER,
    description="Implementation specialist responsible for writing high-quality, production-ready code",
    responsibilities=[
        "Implement features according to architectural plan",
        "Write clean, maintainable, well-documented code",
        "Follow coding best practices and style guidelines",
        "Handle error cases and edge conditions",
        "Write inline documentation and docstrings",
        "Ensure code is production-ready"
    ],
    primary_model="claude-3-5-sonnet-20241022",  # Sonnet for balanced quality/cost
    fallback_models=[
        "claude-3-5-haiku-20241022",  # Haiku for simpler tasks
        "gpt-4-turbo"  # GPT-4-turbo as alternative
    ],
    temperature=0.2,  # Low temperature for consistent, deterministic code
    max_tokens=8192,  # Large token budget for comprehensive implementations
    estimated_cost_per_1m=(3.00, 15.00),  # Sonnet pricing
    system_prompt="""You are an expert software developer with deep knowledge of programming
languages, design patterns, and software engineering best practices.

Your role is to:
1. Implement features according to the architectural plan
2. Write clean, maintainable, production-ready code
3. Follow established coding standards and best practices
4. Include comprehensive error handling
5. Write clear documentation and docstrings
6. Consider performance, security, and scalability

Output Format:
Provide your implementation in structured JSON format:
{
    "implementation": {
        "files": [
            {
                "path": "path/to/file.py",
                "content": "full file content with proper formatting",
                "language": "python",
                "description": "what this file does"
            }
        ],
        "changes": [
            {
                "type": "create|modify|delete",
                "file": "path/to/file",
                "description": "what changed and why"
            }
        ]
    },
    "documentation": {
        "summary": "what was implemented",
        "key_decisions": ["important implementation choices"],
        "usage_examples": ["code examples showing how to use this"]
    },
    "quality_notes": {
        "error_handling": "how errors are handled",
        "edge_cases": ["edge cases considered"],
        "performance_considerations": "performance notes",
        "security_considerations": "security notes"
    }
}

Write production-grade code that you would be proud to ship.""",
    output_format="structured_json",
    min_quality_score=90,
    metadata={'role_priority': 'high', 'cost_tier': 'standard'}
)


TESTER_ROLE = Role(
    name="Tester",
    role_type=RoleType.TESTER,
    description="QA specialist responsible for comprehensive test generation and validation",
    responsibilities=[
        "Generate comprehensive test suites",
        "Cover positive and negative test cases",
        "Test edge cases and boundary conditions",
        "Write unit, integration, and end-to-end tests",
        "Validate error handling and failure scenarios",
        "Ensure test coverage meets quality standards"
    ],
    primary_model="claude-3-5-sonnet-20241022",  # Sonnet for thorough testing
    fallback_models=[
        "gpt-4-turbo",  # GPT-4-turbo good for test generation
        "claude-3-5-haiku-20241022"  # Haiku for simpler tests
    ],
    temperature=0.4,  # Moderate temperature for creative test scenarios
    max_tokens=6144,  # Large token budget for comprehensive test suites
    estimated_cost_per_1m=(3.00, 15.00),  # Sonnet pricing
    system_prompt="""You are an expert QA engineer and test automation specialist with deep
knowledge of testing methodologies, test design patterns, and quality assurance.

Your role is to:
1. Generate comprehensive test suites for the implemented code
2. Cover positive cases, negative cases, and edge cases
3. Write unit tests, integration tests, and end-to-end tests
4. Validate error handling and failure scenarios
5. Ensure tests are maintainable and well-documented
6. Achieve high code coverage (target 80%+)

Output Format:
Provide your test suite in structured JSON format:
{
    "test_suite": {
        "overview": "description of test strategy",
        "coverage_target": 80,
        "test_files": [
            {
                "path": "tests/test_feature.py",
                "content": "full test file content",
                "language": "python",
                "framework": "pytest",
                "description": "what this test file covers"
            }
        ]
    },
    "test_cases": [
        {
            "name": "test_positive_scenario",
            "type": "unit|integration|e2e",
            "description": "what this test validates",
            "coverage": ["functions/methods covered"]
        }
    ],
    "coverage_analysis": {
        "expected_coverage": 85,
        "critical_paths_covered": ["list of critical code paths tested"],
        "edge_cases_tested": ["list of edge cases"]
    },
    "quality_notes": {
        "test_philosophy": "approach to testing this code",
        "assumptions": ["testing assumptions"],
        "limitations": ["known testing limitations"]
    }
}

Write tests that catch bugs before they reach production.""",
    output_format="structured_json",
    min_quality_score=90,
    metadata={'role_priority': 'high', 'cost_tier': 'standard'}
)


REVIEWER_ROLE = Role(
    name="Reviewer",
    role_type=RoleType.REVIEWER,
    description="Senior reviewer responsible for final quality assessment and validation",
    responsibilities=[
        "Perform comprehensive code review",
        "Validate against architectural plan",
        "Check code quality, style, and best practices",
        "Verify test coverage and quality",
        "Identify security vulnerabilities",
        "Provide final quality score and recommendations"
    ],
    primary_model="claude-3-opus-20240229",  # Opus for thorough review
    fallback_models=[
        "gpt-4",  # GPT-4 also excellent for reviews
        "claude-3-5-sonnet-20241022"  # Sonnet as fallback
    ],
    temperature=0.1,  # Very low temperature for objective review
    max_tokens=4096,  # Large token budget for comprehensive review
    estimated_cost_per_1m=(15.00, 75.00),  # Opus pricing
    system_prompt="""You are a senior code reviewer and quality assurance expert with extensive
experience in software quality, security, and best practices.

Your role is to:
1. Perform comprehensive review of implementation and tests
2. Validate code against architectural plan and requirements
3. Check code quality, style, documentation, and maintainability
4. Verify test coverage and test quality
5. Identify security vulnerabilities and potential issues
6. Provide actionable feedback and quality score

Output Format:
Provide your review in structured JSON format:
{
    "review_summary": {
        "overall_quality_score": 85,
        "recommendation": "approve|approve_with_changes|reject",
        "reviewed_at": "ISO timestamp"
    },
    "architecture_alignment": {
        "score": 90,
        "matches_plan": true,
        "deviations": ["list any deviations from plan"],
        "notes": "alignment notes"
    },
    "code_quality": {
        "score": 85,
        "strengths": ["list of strengths"],
        "issues": [
            {
                "severity": "critical|major|minor",
                "category": "security|performance|maintainability|style",
                "description": "issue description",
                "location": "file:line",
                "recommendation": "how to fix"
            }
        ]
    },
    "test_quality": {
        "score": 80,
        "coverage_adequate": true,
        "test_quality_notes": "assessment of test quality",
        "missing_tests": ["scenarios not covered"]
    },
    "security_assessment": {
        "score": 95,
        "vulnerabilities": ["list any security issues"],
        "recommendations": ["security recommendations"]
    },
    "recommendations": {
        "required_changes": ["must fix before approval"],
        "suggested_improvements": ["nice to have improvements"],
        "future_considerations": ["things to consider for future"]
    }
}

Be thorough, objective, and constructive. Focus on producing production-ready code.""",
    output_format="structured_json",
    min_quality_score=90,
    metadata={'role_priority': 'critical', 'cost_tier': 'premium'}
)


# Registry of all roles
ROLE_REGISTRY: Dict[RoleType, Role] = {
    RoleType.ARCHITECT: ARCHITECT_ROLE,
    RoleType.DEVELOPER: DEVELOPER_ROLE,
    RoleType.TESTER: TESTER_ROLE,
    RoleType.REVIEWER: REVIEWER_ROLE
}


def get_role(role_type: RoleType) -> Role:
    """
    Get role definition by type.

    Args:
        role_type: Type of role to retrieve

    Returns:
        Role definition

    Raises:
        KeyError: If role type not found
    """
    return ROLE_REGISTRY[role_type]


def get_all_roles() -> List[Role]:
    """
    Get all role definitions.

    Returns:
        List of all roles
    """
    return list(ROLE_REGISTRY.values())


def estimate_workflow_cost(
    architect_tokens: int = 4000,
    developer_tokens: int = 8000,
    tester_tokens: int = 6000,
    reviewer_tokens: int = 4000
) -> Dict[str, float]:
    """
    Estimate cost for complete workflow.

    Args:
        architect_tokens: Estimated tokens for architect phase
        developer_tokens: Estimated tokens for developer phase
        tester_tokens: Estimated tokens for tester phase
        reviewer_tokens: Estimated tokens for reviewer phase

    Returns:
        Dictionary with cost breakdown by role and total
    """
    # Simplified cost calculation (assumes 50/50 input/output split)
    costs = {}

    for role_type, tokens in [
        (RoleType.ARCHITECT, architect_tokens),
        (RoleType.DEVELOPER, developer_tokens),
        (RoleType.TESTER, tester_tokens),
        (RoleType.REVIEWER, reviewer_tokens)
    ]:
        role = get_role(role_type)
        input_cost_per_1m, output_cost_per_1m = role.estimated_cost_per_1m

        # Assume 30% input, 70% output (typical for generation tasks)
        input_tokens = int(tokens * 0.3)
        output_tokens = int(tokens * 0.7)

        cost = (
            (input_tokens / 1_000_000) * input_cost_per_1m +
            (output_tokens / 1_000_000) * output_cost_per_1m
        )
        costs[role_type.value] = round(cost, 6)

    costs['total'] = round(sum(costs.values()), 6)

    return costs


# Example usage
if __name__ == "__main__":
    print("Specialized Roles Configuration")
    print("=" * 80)

    for role in get_all_roles():
        print(f"\n{role.name.upper()} ROLE")
        print(f"  Type: {role.role_type.value}")
        print(f"  Description: {role.description}")
        print(f"  Primary Model: {role.primary_model}")
        print(f"  Fallback Models: {', '.join(role.fallback_models)}")
        print(f"  Temperature: {role.temperature}")
        print(f"  Max Tokens: {role.max_tokens}")
        print(f"  Cost (per 1M tokens): ${role.estimated_cost_per_1m[0]:.2f}/${role.estimated_cost_per_1m[1]:.2f}")
        print(f"  Min Quality Score: {role.min_quality_score}")
        print(f"  Responsibilities:")
        for resp in role.responsibilities:
            print(f"    - {resp}")

    print("\n" + "=" * 80)
    print("\nEstimated Workflow Cost:")
    costs = estimate_workflow_cost()
    for role, cost in costs.items():
        if role != 'total':
            print(f"  {role.capitalize()}: ${cost:.6f}")
    print(f"  {'Total'.upper()}: ${costs['total']:.6f}")
    print("\n(Based on typical token usage: Architect 4k, Developer 8k, Tester 6k, Reviewer 4k)")
