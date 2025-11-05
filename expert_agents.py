"""
Specialized Expert Agents for Advanced Multi-Agent Systems

This module provides domain-specific expert agents that extend the base
SubAgent class with specialized capabilities and knowledge domains.
"""

import sys
import json
import yaml
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from pathlib import Path

# Import base classes
try:
    from .agent_system import BaseAgent, CostTracker
    from .orchestrator import SubAgent, Orchestrator, ExecutionMode
except ImportError:
    from agent_system import BaseAgent, CostTracker
    from orchestrator import SubAgent, Orchestrator, ExecutionMode


class AgentRole(Enum):
    """Enumeration of all available agent roles."""
    ARCHITECT = "architect-agent"
    API_DESIGNER = "api-designer"
    DATA_SPECIALIST = "data-specialist"
    PERFORMANCE_ENGINEER = "performance-engineer"
    FRONTEND_SPECIALIST = "frontend-specialist"
    BACKEND_SPECIALIST = "backend-specialist"
    SECURITY_AUDITOR = "security-auditor"
    TEST_SPECIALIST = "test-specialist"
    DEVOPS_SPECIALIST = "devops-specialist"
    DOCUMENTATION_SPECIALIST = "documentation-specialist"
    UX_RESEARCHER = "ux-researcher"
    CODE_REVIEWER = "code-reviewer"
    VALIDATOR = "validator-agent"
    INTEGRATION = "integration-agent"
    ORCHESTRATOR_MASTER = "orchestrator-master"


class ExpertAgent(SubAgent):
    """
    Enhanced SubAgent with domain-specific expertise and capabilities.
    """

    def __init__(self,
                 role: AgentRole,
                 capabilities: List[str] = None,
                 tools: List[str] = None,
                 communication_pattern: str = "async-queue",
                 priority: int = 2,
                 **kwargs):
        """
        Initialize an expert agent with specialized capabilities.

        Args:
            role: The agent's specialized role
            capabilities: List of domain capabilities
            tools: List of tools the agent can use
            communication_pattern: How this agent communicates
            priority: Execution priority (1=highest)
            **kwargs: Additional arguments for SubAgent
        """
        # Load agent configuration from registry
        config = self._load_agent_config(role.value)

        # Use config values with overrides from parameters
        model = kwargs.pop('model', config.get('model', 'claude-3-5-haiku-20241022'))
        dependencies = kwargs.pop('dependencies', set(config.get('dependencies', [])))

        super().__init__(
            role=config.get('role', role.value),
            model=model,
            dependencies=dependencies,
            **kwargs
        )

        self.agent_role = role
        self.capabilities = capabilities or config.get('capabilities', [])
        self.tools = tools or config.get('tools', [])
        self.communication_pattern = communication_pattern
        self.priority = priority or config.get('priority', 2)

        # Domain-specific knowledge base
        self.knowledge_base = {}
        self._load_domain_knowledge()

    def _load_agent_config(self, role_name: str) -> Dict[str, Any]:
        """Load agent configuration from registry."""
        registry_path = Path('/home/jevenson/.claude/agents/registry.yaml')

        if registry_path.exists():
            with open(registry_path, 'r') as f:
                registry = yaml.safe_load(f)
                return registry.get('agents', {}).get(role_name, {})
        return {}

    def _load_domain_knowledge(self):
        """Load domain-specific knowledge for the agent."""
        # This could load from files, databases, or other sources
        domain_knowledge = {
            AgentRole.ARCHITECT: {
                'patterns': ['mvc', 'mvvm', 'microservices', 'serverless', 'event-driven'],
                'principles': ['solid', 'dry', 'kiss', 'yagni'],
                'frameworks': ['django', 'fastapi', 'express', 'spring']
            },
            AgentRole.SECURITY_AUDITOR: {
                'vulnerabilities': ['sql-injection', 'xss', 'csrf', 'xxe', 'ssrf'],
                'standards': ['owasp-top-10', 'pci-dss', 'gdpr', 'hipaa'],
                'tools': ['zap', 'burp', 'nmap', 'metasploit']
            },
            AgentRole.PERFORMANCE_ENGINEER: {
                'metrics': ['latency', 'throughput', 'cpu', 'memory', 'disk-io'],
                'patterns': ['caching', 'cdn', 'load-balancing', 'database-indexing'],
                'tools': ['lighthouse', 'gtmetrix', 'jmeter', 'locust']
            }
        }

        self.knowledge_base = domain_knowledge.get(self.agent_role, {})

    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    def get_compatible_agents(self, agents: List['ExpertAgent']) -> List['ExpertAgent']:
        """Get agents this agent can work well with."""
        compatible = []
        for agent in agents:
            # Check for complementary capabilities
            if self._are_complementary(agent):
                compatible.append(agent)
        return compatible

    def _are_complementary(self, other: 'ExpertAgent') -> bool:
        """Check if two agents have complementary skills."""
        # Define complementary pairs
        complementary_pairs = {
            AgentRole.FRONTEND_SPECIALIST: [AgentRole.BACKEND_SPECIALIST, AgentRole.API_DESIGNER],
            AgentRole.BACKEND_SPECIALIST: [AgentRole.DATA_SPECIALIST, AgentRole.API_DESIGNER],
            AgentRole.ARCHITECT: [AgentRole.DEVOPS_SPECIALIST, AgentRole.SECURITY_AUDITOR],
            AgentRole.TEST_SPECIALIST: [AgentRole.CODE_REVIEWER, AgentRole.PERFORMANCE_ENGINEER]
        }

        return other.agent_role in complementary_pairs.get(self.agent_role, [])


class ArchitectAgent(ExpertAgent):
    """Specialized agent for system architecture and design."""

    def __init__(self, **kwargs):
        super().__init__(
            role=AgentRole.ARCHITECT,
            **kwargs
        )

    def design_system(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design a system architecture based on requirements."""
        prompt = f"""
        Design a system architecture for the following requirements:
        {json.dumps(requirements, indent=2)}

        Consider:
        - Scalability requirements
        - Performance constraints
        - Security needs
        - Technology stack preferences
        - Budget constraints

        Provide:
        1. High-level architecture diagram (mermaid syntax)
        2. Component breakdown
        3. Technology recommendations
        4. Deployment strategy
        """

        result = self.call(prompt)
        return self._parse_architecture_response(result)

    def _parse_architecture_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure architecture response."""
        # Parse the response and extract structured data
        return {
            'architecture': response.get('output', ''),
            'components': [],
            'technologies': [],
            'deployment': {},
            'cost_estimate': response.get('cost', 0)
        }


class SecurityAuditor(ExpertAgent):
    """Specialized agent for security auditing and vulnerability detection."""

    def __init__(self, **kwargs):
        super().__init__(
            role=AgentRole.SECURITY_AUDITOR,
            model="claude-3-5-sonnet-20241022",  # Use better model for security
            **kwargs
        )

    def audit_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Perform security audit on code."""
        prompt = f"""
        Perform a comprehensive security audit on this {language} code:

        ```{language}
        {code}
        ```

        Check for:
        1. OWASP Top 10 vulnerabilities
        2. Input validation issues
        3. Authentication/authorization problems
        4. Cryptographic weaknesses
        5. Dependency vulnerabilities
        6. Information disclosure
        7. Rate limiting issues

        Return findings with severity levels (critical, high, medium, low).
        """

        result = self.call(prompt)
        return self._parse_security_findings(result)

    def _parse_security_findings(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse security audit findings."""
        return {
            'vulnerabilities': [],
            'severity_summary': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'recommendations': [],
            'secure_code_snippets': [],
            'compliance': {}
        }


class DataSpecialist(ExpertAgent):
    """Specialized agent for database design and data modeling."""

    def __init__(self, **kwargs):
        super().__init__(
            role=AgentRole.DATA_SPECIALIST,
            **kwargs
        )

    def design_schema(self, entities: List[Dict[str, Any]],
                     database_type: str = "postgresql") -> Dict[str, Any]:
        """Design database schema from entity descriptions."""
        prompt = f"""
        Design a {database_type} database schema for these entities:
        {json.dumps(entities, indent=2)}

        Include:
        1. Table definitions with appropriate data types
        2. Primary and foreign keys
        3. Indexes for performance
        4. Constraints and validations
        5. Migration scripts
        6. Sample queries for common operations
        """

        result = self.call(prompt)
        return self._parse_schema_response(result)

    def optimize_query(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a database query for performance."""
        prompt = f"""
        Optimize this SQL query:
        {query}

        Given schema:
        {json.dumps(schema, indent=2)}

        Provide:
        1. Optimized query
        2. Explanation of optimizations
        3. Index recommendations
        4. Estimated performance improvement
        """

        result = self.call(prompt)
        return result

    def _parse_schema_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse schema design response."""
        return {
            'tables': [],
            'indexes': [],
            'constraints': [],
            'migrations': [],
            'sample_queries': []
        }


class PerformanceEngineer(ExpertAgent):
    """Specialized agent for performance optimization and testing."""

    def __init__(self, **kwargs):
        super().__init__(
            role=AgentRole.PERFORMANCE_ENGINEER,
            **kwargs
        )

    def analyze_performance(self, code: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code performance and suggest optimizations."""
        prompt = f"""
        Analyze the performance of this code:
        {code[:2000]}  # Truncate for token limits

        Current metrics:
        {json.dumps(metrics, indent=2)}

        Provide:
        1. Performance bottlenecks identified
        2. Optimization recommendations
        3. Caching strategies
        4. Algorithm improvements
        5. Estimated performance gains
        """

        result = self.call(prompt)
        return self._parse_performance_analysis(result)

    def create_load_test(self, api_spec: Dict[str, Any]) -> str:
        """Generate load testing scripts."""
        prompt = f"""
        Create a K6 load testing script for this API:
        {json.dumps(api_spec, indent=2)}

        Include:
        1. Ramp-up scenario
        2. Sustained load scenario
        3. Spike test scenario
        4. Performance thresholds
        5. Custom metrics
        """

        result = self.call(prompt)
        return result.get('output', '')

    def _parse_performance_analysis(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse performance analysis results."""
        return {
            'bottlenecks': [],
            'optimizations': [],
            'caching_strategy': {},
            'estimated_improvement': {},
            'recommendations': []
        }


class TestSpecialist(ExpertAgent):
    """Specialized agent for test strategy and implementation."""

    def __init__(self, **kwargs):
        super().__init__(
            role=AgentRole.TEST_SPECIALIST,
            **kwargs
        )

    def create_test_suite(self, code: str, framework: str = "pytest") -> str:
        """Generate comprehensive test suite for code."""
        prompt = f"""
        Create a comprehensive {framework} test suite for this code:
        {code}

        Include:
        1. Unit tests for all functions/methods
        2. Integration tests for components
        3. Edge case tests
        4. Error handling tests
        5. Performance tests
        6. Mock external dependencies

        Aim for 90%+ coverage.
        """

        result = self.call(prompt)
        return result.get('output', '')

    def generate_test_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test plan from requirements."""
        prompt = f"""
        Create a test plan for these requirements:
        {json.dumps(requirements, indent=2)}

        Include:
        1. Test strategy
        2. Test scenarios
        3. Test data requirements
        4. Environment setup
        5. Success criteria
        6. Risk assessment
        """

        result = self.call(prompt)
        return self._parse_test_plan(result)

    def _parse_test_plan(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse test plan response."""
        return {
            'strategy': '',
            'scenarios': [],
            'test_data': [],
            'environments': [],
            'criteria': {},
            'risks': []
        }


class DocumentationSpecialist(ExpertAgent):
    """Specialized agent for technical documentation."""

    def __init__(self, **kwargs):
        super().__init__(
            role=AgentRole.DOCUMENTATION_SPECIALIST,
            model="claude-3-5-haiku-20241022",  # Cheaper model for docs
            **kwargs
        )

    def create_readme(self, project_info: Dict[str, Any]) -> str:
        """Generate comprehensive README for project."""
        prompt = f"""
        Create a professional README.md for this project:
        {json.dumps(project_info, indent=2)}

        Include:
        1. Project overview and badges
        2. Features list
        3. Installation instructions
        4. Usage examples
        5. API documentation
        6. Contributing guidelines
        7. License information
        """

        result = self.call(prompt)
        return result.get('output', '')

    def generate_api_docs(self, api_spec: Dict[str, Any],
                         format: str = "openapi") -> str:
        """Generate API documentation."""
        prompt = f"""
        Generate {format} documentation for this API:
        {json.dumps(api_spec, indent=2)}

        Include:
        1. Endpoint descriptions
        2. Request/response schemas
        3. Authentication details
        4. Error responses
        5. Code examples in multiple languages
        """

        result = self.call(prompt)
        return result.get('output', '')


class UXResearcher(ExpertAgent):
    """Specialized agent for UX research and design."""

    def __init__(self, **kwargs):
        super().__init__(
            role=AgentRole.UX_RESEARCHER,
            **kwargs
        )

    def create_user_journey(self, user_persona: Dict[str, Any],
                           app_features: List[str]) -> Dict[str, Any]:
        """Create user journey map."""
        prompt = f"""
        Create a user journey map for this persona:
        {json.dumps(user_persona, indent=2)}

        Using these app features:
        {json.dumps(app_features, indent=2)}

        Include:
        1. Journey stages
        2. User actions
        3. Emotions/thoughts
        4. Pain points
        5. Opportunities
        6. Success metrics
        """

        result = self.call(prompt)
        return self._parse_journey_map(result)

    def accessibility_audit(self, ui_description: str) -> Dict[str, Any]:
        """Perform accessibility audit on UI."""
        prompt = f"""
        Perform WCAG 2.1 accessibility audit on this UI:
        {ui_description}

        Check for:
        1. Color contrast ratios
        2. Keyboard navigation
        3. Screen reader compatibility
        4. ARIA labels
        5. Focus indicators
        6. Alternative text

        Provide severity and fixes for each issue.
        """

        result = self.call(prompt)
        return self._parse_accessibility_audit(result)

    def _parse_journey_map(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user journey map."""
        return {
            'stages': [],
            'actions': [],
            'emotions': [],
            'pain_points': [],
            'opportunities': [],
            'metrics': []
        }

    def _parse_accessibility_audit(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse accessibility audit results."""
        return {
            'issues': [],
            'wcag_compliance': {},
            'recommendations': [],
            'priority_fixes': []
        }


# Factory function for creating expert agents
def create_expert_agent(role: AgentRole, **kwargs) -> ExpertAgent:
    """
    Factory function to create specialized expert agents.

    Args:
        role: The agent role to create
        **kwargs: Additional parameters for the agent

    Returns:
        Specialized expert agent instance
    """
    agent_classes = {
        AgentRole.ARCHITECT: ArchitectAgent,
        AgentRole.SECURITY_AUDITOR: SecurityAuditor,
        AgentRole.DATA_SPECIALIST: DataSpecialist,
        AgentRole.PERFORMANCE_ENGINEER: PerformanceEngineer,
        AgentRole.TEST_SPECIALIST: TestSpecialist,
        AgentRole.DOCUMENTATION_SPECIALIST: DocumentationSpecialist,
        AgentRole.UX_RESEARCHER: UXResearcher
    }

    agent_class = agent_classes.get(role, ExpertAgent)
    return agent_class(role=role, **kwargs)


# Agent team builder
class AgentTeamBuilder:
    """Builder for creating teams of expert agents."""

    def __init__(self):
        self.agents = []
        self.team_name = "Expert Team"

    def with_name(self, name: str) -> 'AgentTeamBuilder':
        """Set team name."""
        self.team_name = name
        return self

    def add_agent(self, role: AgentRole, **kwargs) -> 'AgentTeamBuilder':
        """Add an expert agent to the team."""
        agent = create_expert_agent(role, **kwargs)
        self.agents.append(agent)
        return self

    def add_fullstack_web_team(self) -> 'AgentTeamBuilder':
        """Add complete fullstack web development team."""
        web_roles = [
            AgentRole.ARCHITECT,
            AgentRole.FRONTEND_SPECIALIST,
            AgentRole.BACKEND_SPECIALIST,
            AgentRole.DATA_SPECIALIST,
            AgentRole.API_DESIGNER,
            AgentRole.TEST_SPECIALIST,
            AgentRole.SECURITY_AUDITOR,
            AgentRole.DEVOPS_SPECIALIST
        ]

        for role in web_roles:
            self.add_agent(role)

        return self

    def add_api_team(self) -> 'AgentTeamBuilder':
        """Add API development team."""
        api_roles = [
            AgentRole.ARCHITECT,
            AgentRole.API_DESIGNER,
            AgentRole.BACKEND_SPECIALIST,
            AgentRole.DATA_SPECIALIST,
            AgentRole.TEST_SPECIALIST,
            AgentRole.DOCUMENTATION_SPECIALIST
        ]

        for role in api_roles:
            self.add_agent(role)

        return self

    def build(self) -> List[ExpertAgent]:
        """Build and return the agent team."""
        return self.agents