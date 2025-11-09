"""
Master Orchestrator - Unified Router for All Workflow Types

Routes tasks to the optimal workflow orchestrator based on task characteristics:
- Specialized Roles: Sequential 4-phase workflow (ARCHITECT → DEVELOPER → TESTER → REVIEWER)
- Parallel Development: Distributed parallel execution for multi-component tasks
- Progressive Enhancement: Speed-optimized tier escalation (Haiku → Sonnet → Opus)

Auto-selects workflow or allows manual selection.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import logging
import re

# Import workflow orchestrators
try:
    from .specialized_roles_orchestrator import SpecializedRolesOrchestrator, WorkflowResult
    from .parallel_development_orchestrator import ParallelDevelopmentOrchestrator
    from .progressive_enhancement_orchestrator import ProgressiveEnhancementOrchestrator
    from .workflow_metrics import WorkflowMetricsTracker
except ImportError:
    from specialized_roles_orchestrator import SpecializedRolesOrchestrator, WorkflowResult
    from parallel_development_orchestrator import ParallelDevelopmentOrchestrator
    from progressive_enhancement_orchestrator import ProgressiveEnhancementOrchestrator
    from workflow_metrics import WorkflowMetricsTracker

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Available workflow types."""
    SPECIALIZED_ROLES = "specialized_roles"
    PARALLEL = "parallel"
    PROGRESSIVE = "progressive"
    AUTO = "auto"


@dataclass
class TaskCharacteristics:
    """Analyzed characteristics of a task."""
    complexity: str  # simple, moderate, complex
    component_count: int  # estimated number of independent components
    requires_architecture: bool
    requires_testing: bool
    requires_review: bool
    estimated_quality_target: int


class MasterOrchestrator:
    """
    Master Orchestrator - Routes to optimal workflow.

    Workflow Selection Logic:
    - **Simple tasks** (quality target < 80, single component):
      → Progressive Enhancement (Haiku→Sonnet, fast & cheap)

    - **Multi-component tasks** (2+ components, can parallelize):
      → Parallel Development (30-70% faster via distributed execution)

    - **Complex single tasks** (architecture/review needed, quality > 90):
      → Specialized Roles (4-phase workflow with validation gates)

    Usage:
        master = MasterOrchestrator()
        result = await master.execute(task, workflow='auto')  # Auto-select
        result = await master.execute(task, workflow='parallel')  # Manual selection
    """

    def __init__(self, project_root: str = "/mnt/d/Dev"):
        """
        Initialize master orchestrator with all workflow types.

        Args:
            project_root: Root directory for validation and metrics
        """
        self.project_root = project_root

        # Initialize all workflow orchestrators
        self.specialized_roles = SpecializedRolesOrchestrator(project_root=project_root)
        self.parallel = ParallelDevelopmentOrchestrator(
            project_root=project_root,
            num_parallel_agents=5,
            quality_threshold=85
        )
        self.progressive = ProgressiveEnhancementOrchestrator(
            project_root=project_root,
            quality_target=85,
            max_escalations=3
        )

        # Unified metrics tracker
        self.metrics = WorkflowMetricsTracker()

        logger.info("MasterOrchestrator initialized with 3 workflow types")

    async def execute(self,
                      task: str,
                      workflow: Literal["auto", "specialized_roles", "parallel", "progressive"] = "auto",
                      context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute task with specified or auto-selected workflow.

        Args:
            task: Development task description
            workflow: Workflow type ('auto', 'specialized_roles', 'parallel', 'progressive')
            context: Additional context (language, framework, requirements, etc.)

        Returns:
            WorkflowResult from the selected orchestrator
        """
        if context is None:
            context = {}

        # Auto-select workflow if requested
        if workflow == "auto":
            workflow = self._recommend_workflow(task, context)
            logger.info(f"Auto-selected workflow: {workflow}")

        # Add workflow selection metadata
        context["master_orchestrator"] = {
            "selected_workflow": workflow,
            "auto_selected": workflow == "auto",
            "timestamp": datetime.now().isoformat()
        }

        # Route to appropriate orchestrator
        logger.info(f"Executing with {workflow} workflow: {task[:100]}...")

        if workflow == "specialized_roles":
            # Specialized roles is synchronous (not async)
            result = self.specialized_roles.execute_workflow(task, context)
        elif workflow == "parallel":
            result = await self.parallel.execute_workflow(task, context)
        elif workflow == "progressive":
            result = await self.progressive.execute_workflow(task, context)
        else:
            raise ValueError(f"Unknown workflow type: {workflow}")

        # Add master orchestrator metadata to result context
        if "workflow_metadata" not in result.context:
            result.context["workflow_metadata"] = {}

        result.context["workflow_metadata"]["orchestrator"] = "master"
        result.context["workflow_metadata"]["selected_workflow"] = workflow

        return result

    def _recommend_workflow(self,
                           task: str,
                           context: Dict[str, Any]) -> str:
        """
        Recommend optimal workflow based on task characteristics.

        Decision Tree:
        1. Analyze task characteristics (complexity, components, requirements)
        2. Check context hints (quality_target, speed_priority, etc.)
        3. Apply heuristics to select workflow

        Returns:
            Workflow type ('specialized_roles', 'parallel', or 'progressive')
        """
        # Analyze task
        characteristics = self._analyze_task(task, context)

        logger.info(f"Task analysis: complexity={characteristics.complexity}, "
                   f"components={characteristics.component_count}, "
                   f"quality_target={characteristics.estimated_quality_target}")

        # Check context hints
        explicit_quality = context.get("quality_target")
        speed_priority = context.get("speed_priority", False)
        cost_priority = context.get("cost_priority", False)

        # Decision logic (REORDERED: Quality checks FIRST to prevent parallel workflow override)
        # 1. High quality requirements → Specialized Roles (quality >= 90)
        quality_target = explicit_quality if explicit_quality else characteristics.estimated_quality_target
        if quality_target >= 90:
            logger.info("→ Specialized Roles workflow (high quality requirement >= 90)")
            return "specialized_roles"

        # 2. Requires architecture/review → Specialized Roles
        if characteristics.requires_architecture or characteristics.requires_review:
            logger.info("→ Specialized Roles workflow (needs architecture/review)")
            return "specialized_roles"

        # 3. Complex task → Specialized Roles (default for complex)
        if characteristics.complexity == "complex":
            logger.info("→ Specialized Roles workflow (complex task)")
            return "specialized_roles"

        # 4. Multi-component CODE tasks → Parallel (if 2+ components AND quality < 90)
        if characteristics.component_count >= 2:
            logger.info("→ Parallel workflow (multi-component task with quality < 90)")
            return "parallel"

        # 5. Simple tasks → Progressive (quality < 85, simple complexity)
        if characteristics.complexity == "simple" and characteristics.estimated_quality_target < 85:
            logger.info("→ Progressive workflow (simple task, speed-optimized)")
            return "progressive"

        # 6. Speed priority → Progressive (tries fast models first)
        if speed_priority:
            logger.info("→ Progressive workflow (speed priority)")
            return "progressive"

        # Default: Progressive (good balance of speed and quality)
        logger.info("→ Progressive workflow (default)")
        return "progressive"

    def _analyze_task(self, task: str, context: Dict[str, Any]) -> TaskCharacteristics:
        """Analyze task to determine characteristics."""

        task_lower = task.lower()

        # Estimate complexity
        complexity_indicators = {
            "simple": ["simple", "basic", "add", "create a function", "write a function"],
            "complex": ["architecture", "system", "comprehensive", "full", "complete", "robust",
                       "scalable", "production", "enterprise"]
        }

        complexity = "moderate"  # default
        for level, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                complexity = level
                break

        # Count components (look for lists, multiple items, plural words)
        component_count = 1  # default
        list_patterns = [
            r'(\d+)\s+(endpoints?|functions?|classes?|components?|modules?)',
            r'(endpoints?|functions?|classes?)\s*:\s*\n',
            r'and\s+\d+',
        ]

        for pattern in list_patterns:
            matches = re.findall(pattern, task_lower)
            if matches:
                # Try to extract number
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    try:
                        num = int(match)
                        component_count = max(component_count, num)
                    except (ValueError, TypeError):
                        pass

        # Check if lists are present (bullets, numbered lists)
        if '\n-' in task or '\n*' in task or re.search(r'\n\d+\.', task):
            component_count = max(component_count, 2)  # At least 2 if listed items

        # Requirements detection
        requires_architecture = any(word in task_lower for word in
                                   ["architect", "design", "structure", "system design"])

        requires_testing = any(word in task_lower for word in
                              ["test", "testing", "validation", "verify"])

        requires_review = any(word in task_lower for word in
                             ["review", "audit", "check", "validate"])

        # Estimate quality target
        if "production" in task_lower or "critical" in task_lower:
            quality_target = 95
        elif "robust" in task_lower or "comprehensive" in task_lower:
            quality_target = 90
        elif complexity == "complex":
            quality_target = 88
        elif complexity == "simple":
            quality_target = 75
        else:
            quality_target = 85

        return TaskCharacteristics(
            complexity=complexity,
            component_count=component_count,
            requires_architecture=requires_architecture,
            requires_testing=requires_testing,
            requires_review=requires_review,
            estimated_quality_target=quality_target
        )

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get statistics across all workflows."""
        analytics = self.metrics.get_analytics()

        return {
            "total_workflows": len(self.metrics.workflows),
            "average_cost": analytics.get("average_cost_usd", 0),
            "average_quality": analytics.get("average_quality", 0),
            "average_duration_seconds": analytics.get("average_duration_seconds", 0),
            "cost_breakdown": analytics.get("cost_breakdown", {}),
            "quality_breakdown": analytics.get("quality_breakdown", {})
        }


# ================== DEMONSTRATION ==================

async def demonstrate_master_orchestrator():
    """Demonstrate master orchestrator with different task types."""
    print("=" * 70)
    print("🎯 MASTER ORCHESTRATOR DEMONSTRATION")
    print("=" * 70)

    master = MasterOrchestrator()

    print("\n📊 Initialized with 3 workflow types:")
    print("   • Specialized Roles (4-phase sequential)")
    print("   • Parallel Development (distributed execution)")
    print("   • Progressive Enhancement (tier escalation)")

    # Test 1: Simple task → Progressive
    print("\n" + "=" * 70)
    print("TEST 1: Simple Task (should select Progressive)")
    print("=" * 70)

    task1 = "Create a simple Python function to calculate fibonacci numbers"
    print(f"\nTask: {task1}")
    print("Executing with workflow='auto'...")

    result1 = await master.execute(task1, workflow="auto")

    metadata1 = result1.context.get("workflow_metadata", {})
    print(f"\n✅ Selected: {metadata1.get('selected_workflow', 'unknown')}")
    print(f"   Quality: {result1.overall_quality_score}/100")
    print(f"   Duration: {result1.total_execution_time_ms/1000:.2f}s")
    print(f"   Cost: ${result1.total_cost_usd:.4f}")

    # Test 2: Multi-component task → Parallel
    print("\n" + "=" * 70)
    print("TEST 2: Multi-Component Task (should select Parallel)")
    print("=" * 70)

    task2 = """Build REST API with endpoints:
    1. POST /users
    2. GET /users/{id}
    3. PUT /users/{id}
    4. DELETE /users/{id}"""

    print(f"\nTask: {task2[:50]}...")
    print("Executing with workflow='auto'...")

    result2 = await master.execute(task2, workflow="auto")

    metadata2 = result2.context.get("workflow_metadata", {})
    print(f"\n✅ Selected: {metadata2.get('selected_workflow', 'unknown')}")
    print(f"   Quality: {result2.overall_quality_score}/100")
    print(f"   Duration: {result2.total_execution_time_ms/1000:.2f}s")

    # Test 3: Manual selection
    print("\n" + "=" * 70)
    print("TEST 3: Manual Workflow Selection")
    print("=" * 70)

    task3 = "Create a calculator class"
    print(f"\nTask: {task3}")
    print("Manually selecting workflow='progressive'...")

    result3 = await master.execute(task3, workflow="progressive")

    metadata3 = result3.context.get("workflow_metadata", {})
    print(f"\n✅ Selected: {metadata3.get('selected_workflow', 'unknown')}")

    # Show overall stats
    print("\n" + "=" * 70)
    print("📊 OVERALL STATISTICS")
    print("=" * 70)

    stats = master.get_workflow_stats()
    print(f"   Total Workflows: {stats['total_workflows']}")
    print(f"   Average Quality: {stats['average_quality']:.1f}/100")
    print(f"   Average Duration: {stats['average_duration_seconds']:.2f}s")
    print(f"   Average Cost: ${stats['average_cost']:.4f}")

    print("\n" + "=" * 70)
    print("💡 KEY FEATURES:")
    print("=" * 70)
    print("""
    ✅ Automatic workflow selection based on task characteristics
    ✅ Manual workflow selection when needed
    ✅ Unified API across all workflow types
    ✅ Cross-workflow metrics and analytics
    ✅ Context-aware routing (quality targets, speed priority, etc.)

    Perfect for: Any development task - let the orchestrator choose the best approach!
    """)


if __name__ == "__main__":
    asyncio.run(demonstrate_master_orchestrator())
