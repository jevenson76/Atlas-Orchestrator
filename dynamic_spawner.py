"""
Dynamic Agent Spawner for Intelligent Multi-Agent Systems

Automatically analyzes tasks and spawns the optimal team of agents
based on requirements, capabilities, and dependencies.
"""

import asyncio
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import core components
try:
    from .agent_system import BaseAgent, CostTracker
    from .orchestrator import Orchestrator, SubAgent, ExecutionMode
    from .expert_agents import (
        ExpertAgent, AgentRole, create_expert_agent,
        AgentTeamBuilder
    )
    from .message_bus import AgentMessageBus, get_message_bus
except ImportError:
    from agent_system import BaseAgent, CostTracker
    from orchestrator import Orchestrator, SubAgent, ExecutionMode
    from expert_agents import (
        ExpertAgent, AgentRole, create_expert_agent,
        AgentTeamBuilder
    )
    from message_bus import AgentMessageBus, get_message_bus

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"       # Single agent, < 5 min
    MODERATE = "moderate"   # 2-3 agents, < 30 min
    COMPLEX = "complex"     # 4-8 agents, < 2 hours
    ADVANCED = "advanced"   # 8+ agents, multi-phase


class TaskDomain(Enum):
    """Task domain categories."""
    WEB_DEVELOPMENT = "web_development"
    API_DEVELOPMENT = "api_development"
    DATA_PROCESSING = "data_processing"
    DEVOPS = "devops"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    GENERAL = "general"


@dataclass
class TaskAnalysis:
    """Results of task analysis."""
    complexity: TaskComplexity
    domains: List[TaskDomain]
    required_capabilities: Set[str]
    suggested_agents: List[AgentRole]
    estimated_time: float  # minutes
    estimated_cost: float  # dollars
    execution_mode: ExecutionMode
    confidence: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class AgentRequirement:
    """Requirements for an agent in the team."""
    role: AgentRole
    priority: int  # 1=critical, 2=important, 3=nice-to-have
    capabilities_needed: Set[str]
    dependencies: Set[AgentRole]
    estimated_workload: float  # 0.0 to 1.0
    model_recommendation: str


class TaskAnalyzer:
    """
    Analyzes tasks to determine agent requirements.
    """

    def __init__(self):
        # Keywords that indicate different domains and capabilities
        self.domain_keywords = {
            TaskDomain.WEB_DEVELOPMENT: [
                'frontend', 'ui', 'react', 'vue', 'angular', 'css', 'html',
                'responsive', 'component', 'webpage', 'website', 'user interface'
            ],
            TaskDomain.API_DEVELOPMENT: [
                'api', 'rest', 'graphql', 'endpoint', 'route', 'http',
                'request', 'response', 'swagger', 'openapi', 'webhook'
            ],
            TaskDomain.DATA_PROCESSING: [
                'database', 'sql', 'nosql', 'query', 'migration', 'schema',
                'etl', 'data', 'analytics', 'mongodb', 'postgresql'
            ],
            TaskDomain.DEVOPS: [
                'deploy', 'docker', 'kubernetes', 'ci/cd', 'pipeline',
                'aws', 'azure', 'gcp', 'terraform', 'ansible', 'helm'
            ],
            TaskDomain.SECURITY: [
                'security', 'vulnerability', 'authentication', 'authorization',
                'encryption', 'owasp', 'pentest', 'audit', 'compliance'
            ],
            TaskDomain.TESTING: [
                'test', 'unit test', 'integration', 'e2e', 'coverage',
                'pytest', 'jest', 'cypress', 'selenium', 'tdd', 'bdd'
            ],
            TaskDomain.PERFORMANCE: [
                'performance', 'optimize', 'speed', 'latency', 'cache',
                'load test', 'profile', 'benchmark', 'scalability'
            ],
            TaskDomain.ARCHITECTURE: [
                'architecture', 'design', 'pattern', 'microservice',
                'monolith', 'serverless', 'event-driven', 'system design'
            ]
        }

        # Agent capabilities mapping
        self.agent_capabilities = self._load_agent_capabilities()

    def _load_agent_capabilities(self) -> Dict[AgentRole, Set[str]]:
        """Load agent capabilities from registry."""
        registry_path = Path('/home/jevenson/.claude/agents/registry.yaml')

        if not registry_path.exists():
            # Return default capabilities
            return {
                AgentRole.ARCHITECT: {'system-design', 'architecture', 'patterns'},
                AgentRole.FRONTEND_SPECIALIST: {'react', 'vue', 'css', 'ui'},
                AgentRole.BACKEND_SPECIALIST: {'api', 'database', 'server'},
                AgentRole.DATA_SPECIALIST: {'sql', 'nosql', 'migrations'},
                AgentRole.SECURITY_AUDITOR: {'security', 'vulnerabilities'},
                AgentRole.TEST_SPECIALIST: {'testing', 'coverage', 'tdd'},
                AgentRole.DEVOPS_SPECIALIST: {'deployment', 'ci-cd', 'docker'},
                AgentRole.PERFORMANCE_ENGINEER: {'optimization', 'profiling'},
                AgentRole.DOCUMENTATION_SPECIALIST: {'documentation', 'writing'},
                AgentRole.API_DESIGNER: {'api-design', 'openapi', 'graphql'},
                AgentRole.UX_RESEARCHER: {'ux', 'usability', 'accessibility'},
                AgentRole.CODE_REVIEWER: {'review', 'quality', 'best-practices'}
            }

        with open(registry_path, 'r') as f:
            registry = yaml.safe_load(f)

        capabilities = {}
        for agent_data in registry.get('agents', {}).values():
            role_name = agent_data.get('role', '')
            # Find matching role
            for role in AgentRole:
                if role.value in agent_data.get('role', ''):
                    capabilities[role] = set(agent_data.get('capabilities', []))
                    break

        return capabilities

    def analyze(self, task_description: str,
               context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """
        Analyze a task and determine agent requirements.

        Args:
            task_description: Natural language task description
            context: Additional context (project type, constraints, etc.)

        Returns:
            TaskAnalysis with recommendations
        """
        task_lower = task_description.lower()
        context = context or {}

        # Detect domains
        domains = self._detect_domains(task_lower)

        # Detect required capabilities
        capabilities = self._detect_capabilities(task_lower, domains)

        # Determine complexity
        complexity = self._assess_complexity(task_lower, domains, capabilities)

        # Select agents
        agents = self._select_agents(domains, capabilities, complexity)

        # Determine execution mode
        exec_mode = self._determine_execution_mode(agents, complexity)

        # Estimate time and cost
        time_est = self._estimate_time(complexity, len(agents))
        cost_est = self._estimate_cost(agents, time_est)

        # Calculate confidence
        confidence = self._calculate_confidence(domains, agents)

        return TaskAnalysis(
            complexity=complexity,
            domains=domains,
            required_capabilities=capabilities,
            suggested_agents=agents,
            estimated_time=time_est,
            estimated_cost=cost_est,
            execution_mode=exec_mode,
            confidence=confidence,
            reasoning=self._generate_reasoning(task_lower, domains, agents)
        )

    def _detect_domains(self, task: str) -> List[TaskDomain]:
        """Detect task domains from description."""
        detected = []

        for domain, keywords in self.domain_keywords.items():
            if any(keyword in task for keyword in keywords):
                detected.append(domain)

        if not detected:
            detected.append(TaskDomain.GENERAL)

        return detected

    def _detect_capabilities(self, task: str,
                            domains: List[TaskDomain]) -> Set[str]:
        """Detect required capabilities from task."""
        capabilities = set()

        # Domain-specific capabilities
        domain_caps = {
            TaskDomain.WEB_DEVELOPMENT: {'frontend', 'ui', 'responsive-design'},
            TaskDomain.API_DEVELOPMENT: {'api-development', 'rest', 'graphql'},
            TaskDomain.DATA_PROCESSING: {'database', 'sql', 'data-modeling'},
            TaskDomain.DEVOPS: {'deployment', 'ci-cd', 'containerization'},
            TaskDomain.SECURITY: {'security', 'vulnerability-scanning'},
            TaskDomain.TESTING: {'testing', 'test-automation'},
            TaskDomain.PERFORMANCE: {'optimization', 'profiling'},
            TaskDomain.ARCHITECTURE: {'system-design', 'architectural-patterns'}
        }

        for domain in domains:
            capabilities.update(domain_caps.get(domain, set()))

        # Detect specific tech mentions
        tech_patterns = {
            r'\breact\b': 'react',
            r'\bvue\b': 'vue',
            r'\bangular\b': 'angular',
            r'\bpython\b': 'python',
            r'\bnode(js)?\b': 'nodejs',
            r'\bdocker\b': 'docker',
            r'\bkubernetes\b': 'kubernetes',
            r'\baws\b': 'aws',
            r'\bpostgres(ql)?\b': 'postgresql',
            r'\bmongo(db)?\b': 'mongodb'
        }

        for pattern, capability in tech_patterns.items():
            if re.search(pattern, task, re.IGNORECASE):
                capabilities.add(capability)

        return capabilities

    def _assess_complexity(self, task: str,
                          domains: List[TaskDomain],
                          capabilities: Set[str]) -> TaskComplexity:
        """Assess task complexity."""
        # Factors that increase complexity
        complexity_score = 0

        # Multiple domains increase complexity
        complexity_score += len(domains) * 10

        # Many capabilities needed
        complexity_score += len(capabilities) * 5

        # Keywords indicating complexity
        complex_keywords = [
            'integrate', 'migration', 'refactor', 'optimize',
            'scale', 'distributed', 'microservice', 'full-stack',
            'production', 'enterprise', 'compliance', 'multi-tenant'
        ]

        for keyword in complex_keywords:
            if keyword in task:
                complexity_score += 15

        # Simple keywords reduce complexity
        simple_keywords = [
            'simple', 'basic', 'prototype', 'poc', 'demo',
            'example', 'tutorial', 'test', 'fix', 'update'
        ]

        for keyword in simple_keywords:
            if keyword in task:
                complexity_score -= 10

        # Map score to complexity level
        if complexity_score < 20:
            return TaskComplexity.SIMPLE
        elif complexity_score < 50:
            return TaskComplexity.MODERATE
        elif complexity_score < 100:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ADVANCED

    def _select_agents(self, domains: List[TaskDomain],
                      capabilities: Set[str],
                      complexity: TaskComplexity) -> List[AgentRole]:
        """Select appropriate agents for the task."""
        selected = set()

        # Domain-specific agent mapping
        domain_agents = {
            TaskDomain.WEB_DEVELOPMENT: [
                AgentRole.FRONTEND_SPECIALIST,
                AgentRole.UX_RESEARCHER
            ],
            TaskDomain.API_DEVELOPMENT: [
                AgentRole.API_DESIGNER,
                AgentRole.BACKEND_SPECIALIST
            ],
            TaskDomain.DATA_PROCESSING: [
                AgentRole.DATA_SPECIALIST
            ],
            TaskDomain.DEVOPS: [
                AgentRole.DEVOPS_SPECIALIST
            ],
            TaskDomain.SECURITY: [
                AgentRole.SECURITY_AUDITOR
            ],
            TaskDomain.TESTING: [
                AgentRole.TEST_SPECIALIST
            ],
            TaskDomain.PERFORMANCE: [
                AgentRole.PERFORMANCE_ENGINEER
            ],
            TaskDomain.ARCHITECTURE: [
                AgentRole.ARCHITECT
            ]
        }

        # Add domain-specific agents
        for domain in domains:
            selected.update(domain_agents.get(domain, []))

        # Add agents based on capabilities
        for role, role_caps in self.agent_capabilities.items():
            if capabilities & role_caps:  # Intersection not empty
                selected.add(role)

        # Add essential agents for complex tasks
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED]:
            selected.add(AgentRole.ARCHITECT)  # Need architecture
            selected.add(AgentRole.TEST_SPECIALIST)  # Need testing
            selected.add(AgentRole.VALIDATOR)  # Need validation

        # Always include documentation for non-simple tasks
        if complexity != TaskComplexity.SIMPLE:
            selected.add(AgentRole.DOCUMENTATION_SPECIALIST)

        return list(selected)

    def _determine_execution_mode(self, agents: List[AgentRole],
                                 complexity: TaskComplexity) -> ExecutionMode:
        """Determine optimal execution mode."""
        # Simple tasks: sequential
        if complexity == TaskComplexity.SIMPLE:
            return ExecutionMode.SEQUENTIAL

        # Check for dependencies
        has_dependencies = False
        for agent in agents:
            if agent in [AgentRole.FRONTEND_SPECIALIST, AgentRole.BACKEND_SPECIALIST]:
                # These often depend on API design
                if AgentRole.API_DESIGNER in agents:
                    has_dependencies = True
                    break

        # Many agents without dependencies: parallel
        if len(agents) > 3 and not has_dependencies:
            return ExecutionMode.PARALLEL

        # Complex with dependencies: adaptive
        if has_dependencies:
            return ExecutionMode.ADAPTIVE

        # Default to adaptive for flexibility
        return ExecutionMode.ADAPTIVE

    def _estimate_time(self, complexity: TaskComplexity,
                      num_agents: int) -> float:
        """Estimate execution time in minutes."""
        base_times = {
            TaskComplexity.SIMPLE: 5,
            TaskComplexity.MODERATE: 30,
            TaskComplexity.COMPLEX: 120,
            TaskComplexity.ADVANCED: 300
        }

        base_time = base_times[complexity]

        # Parallel execution reduces time
        if num_agents > 1:
            # Assume 40% time reduction for parallel work
            base_time *= (1 - 0.4 * min(num_agents / 10, 1))

        return base_time

    def _estimate_cost(self, agents: List[AgentRole],
                      time_minutes: float) -> float:
        """Estimate cost in dollars."""
        # Model costs per agent type
        model_costs = {
            'haiku': 0.001,  # Per minute estimate
            'sonnet': 0.01,
            'opus': 0.05
        }

        # Agent to model mapping (simplified)
        agent_models = {
            AgentRole.ARCHITECT: 'sonnet',
            AgentRole.SECURITY_AUDITOR: 'sonnet',
            AgentRole.BACKEND_SPECIALIST: 'sonnet',
            AgentRole.FRONTEND_SPECIALIST: 'sonnet',
            AgentRole.DATA_SPECIALIST: 'sonnet',
            AgentRole.TEST_SPECIALIST: 'haiku',
            AgentRole.DOCUMENTATION_SPECIALIST: 'haiku',
            AgentRole.PERFORMANCE_ENGINEER: 'haiku',
            AgentRole.API_DESIGNER: 'haiku',
            AgentRole.UX_RESEARCHER: 'haiku',
            AgentRole.CODE_REVIEWER: 'haiku'
        }

        total_cost = 0.0
        for agent in agents:
            model = agent_models.get(agent, 'haiku')
            cost_per_min = model_costs[model]
            # Assume each agent works 20% of total time
            agent_time = time_minutes * 0.2
            total_cost += cost_per_min * agent_time

        return round(total_cost, 4)

    def _calculate_confidence(self, domains: List[TaskDomain],
                            agents: List[AgentRole]) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5  # Base confidence

        # More specific domains increase confidence
        if domains and TaskDomain.GENERAL not in domains:
            confidence += 0.2

        # Having appropriate agents increases confidence
        if len(agents) > 0:
            confidence += min(len(agents) * 0.05, 0.3)

        return min(confidence, 1.0)

    def _generate_reasoning(self, task: str,
                          domains: List[TaskDomain],
                          agents: List[AgentRole]) -> str:
        """Generate reasoning for the analysis."""
        domain_names = [d.value.replace('_', ' ') for d in domains]
        agent_names = [a.value.replace('-', ' ').title() for a in agents]

        reasoning = f"Task involves {', '.join(domain_names)}. "
        reasoning += f"Selected {len(agents)} specialized agents: {', '.join(agent_names[:3])}"
        if len(agents) > 3:
            reasoning += f" and {len(agents) - 3} others"
        reasoning += ". "

        if 'integrate' in task or 'full' in task:
            reasoning += "Task requires integration across multiple components. "

        if 'production' in task or 'deploy' in task:
            reasoning += "Production deployment considerations included. "

        return reasoning


class DynamicAgentSpawner:
    """
    Dynamically spawns and orchestrates agent teams based on task requirements.
    """

    def __init__(self,
                 cost_tracker: Optional[CostTracker] = None,
                 message_bus: Optional[AgentMessageBus] = None):
        """
        Initialize the dynamic spawner.

        Args:
            cost_tracker: Shared cost tracker
            message_bus: Message bus for agent communication
        """
        self.analyzer = TaskAnalyzer()
        self.cost_tracker = cost_tracker or CostTracker(daily_budget=50.0)
        self.message_bus = message_bus or get_message_bus()
        self.active_teams = {}
        self.team_counter = 0

        logger.info("Dynamic Agent Spawner initialized")

    def analyze_task(self, task_description: str,
                     context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """
        Analyze a task to determine agent requirements.

        Args:
            task_description: Task to analyze
            context: Additional context

        Returns:
            Task analysis with agent recommendations
        """
        return self.analyzer.analyze(task_description, context)

    def spawn_team(self, task_description: str,
                  context: Optional[Dict[str, Any]] = None,
                  auto_execute: bool = False) -> 'DynamicOrchestrator':
        """
        Spawn an agent team for a task.

        Args:
            task_description: Task to execute
            context: Additional context
            auto_execute: Automatically execute the task

        Returns:
            Orchestrator with spawned agent team
        """
        # Analyze task
        analysis = self.analyze_task(task_description, context)

        # Create team name
        self.team_counter += 1
        team_name = f"Team-{self.team_counter}-{analysis.complexity.value}"

        logger.info(f"Spawning {team_name} with {len(analysis.suggested_agents)} agents")

        # Create orchestrator
        orchestrator = DynamicOrchestrator(
            name=team_name,
            mode=analysis.execution_mode,
            cost_tracker=self.cost_tracker,
            task_analysis=analysis
        )

        # Add agents to orchestrator
        for agent_role in analysis.suggested_agents:
            agent = create_expert_agent(agent_role)

            # Register with message bus
            self.message_bus.register_agent(agent_role.value)

            # Add to orchestrator
            orchestrator.add_agent(agent_role.value, agent)

        # Store team reference
        self.active_teams[team_name] = orchestrator

        # Auto-execute if requested
        if auto_execute:
            asyncio.create_task(
                self._execute_team(orchestrator, task_description, context)
            )

        return orchestrator

    async def _execute_team(self, orchestrator: 'DynamicOrchestrator',
                           task_description: str,
                           context: Optional[Dict[str, Any]]):
        """Execute team asynchronously."""
        try:
            result = await orchestrator.execute_async({
                'task': task_description,
                'context': context
            })
            logger.info(f"Team {orchestrator.name} completed: {result.get('success')}")
        except Exception as e:
            logger.error(f"Team {orchestrator.name} failed: {e}")

    def spawn_from_template(self, template_name: str,
                          **kwargs) -> 'DynamicOrchestrator':
        """
        Spawn a team from a predefined template.

        Args:
            template_name: Name of team template
            **kwargs: Additional parameters

        Returns:
            Orchestrator with template-based team
        """
        builder = AgentTeamBuilder().with_name(f"Template-{template_name}")

        # Load team based on template
        if template_name == "fullstack_web":
            builder.add_fullstack_web_team()
        elif template_name == "api_service":
            builder.add_api_team()
        else:
            raise ValueError(f"Unknown template: {template_name}")

        agents = builder.build()

        # Create orchestrator
        orchestrator = DynamicOrchestrator(
            name=builder.team_name,
            mode=ExecutionMode.ADAPTIVE,
            cost_tracker=self.cost_tracker
        )

        # Add agents
        for agent in agents:
            orchestrator.add_agent(agent.agent_role.value, agent)

        return orchestrator

    def get_team_status(self, team_name: str) -> Dict[str, Any]:
        """Get status of an active team."""
        if team_name not in self.active_teams:
            return {'error': 'Team not found'}

        orchestrator = self.active_teams[team_name]
        return {
            'name': team_name,
            'agents': list(orchestrator.subagents.keys()),
            'mode': orchestrator.mode.value,
            'status': 'active',  # Could track actual status
            'metrics': orchestrator.get_agent_metrics()
        }

    def list_active_teams(self) -> List[str]:
        """List all active teams."""
        return list(self.active_teams.keys())

    def terminate_team(self, team_name: str):
        """Terminate and clean up a team."""
        if team_name in self.active_teams:
            orchestrator = self.active_teams[team_name]

            # Unregister agents from message bus
            for agent_name in orchestrator.subagents.keys():
                self.message_bus.unregister_agent(agent_name)

            # Remove team
            del self.active_teams[team_name]
            logger.info(f"Team {team_name} terminated")


class DynamicOrchestrator(Orchestrator):
    """
    Dynamic orchestrator that adapts based on task analysis.
    """

    def __init__(self,
                 task_analysis: Optional[TaskAnalysis] = None,
                 **kwargs):
        """
        Initialize dynamic orchestrator.

        Args:
            task_analysis: Task analysis results
            **kwargs: Additional Orchestrator parameters
        """
        super().__init__(**kwargs)
        self.task_analysis = task_analysis

    def prepare_prompt(self, agent_name: str,
                      initial_input: Dict[str, Any],
                      previous_results: Dict[str, Any]) -> str:
        """Prepare dynamic prompts based on task and agent role."""
        task = initial_input.get('task', '')
        context = initial_input.get('context', {})

        # Build context from previous results
        context_str = ""
        if previous_results:
            context_str = "\\n\\nPrevious agent results:"
            for prev_agent, result in previous_results.items():
                output = result.get('output', '')[:500]  # Limit length
                context_str += f"\\n{prev_agent}: {output}"

        # Create role-specific prompt
        prompt = f"""
        Task: {task}

        Your role: {agent_name}

        Context:
        {json.dumps(context, indent=2) if context else 'None'}
        {context_str}

        Please complete your part of this task according to your specialization.
        Provide structured output that other agents can use.
        """

        return prompt

    def process_result(self, agent_name: str,
                      result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure agent results."""
        # Add metadata
        result['agent'] = agent_name
        result['timestamp'] = asyncio.get_event_loop().time()

        # Parse structured output if present
        output = result.get('output', '')
        if isinstance(output, str):
            # Try to parse JSON output
            try:
                if output.strip().startswith('{') or output.strip().startswith('['):
                    result['structured_output'] = json.loads(output)
            except json.JSONDecodeError:
                pass

        return result