"""
Specialized Roles Project Planner with Quality-Focused Orchestration.

This module integrates the 4-role specialized workflow (Architect, Developer, Tester, Reviewer)
with comprehensive CSV project plan generation, ensuring 90% quality target.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Any
import json
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from role_definitions import (
    RoleType,
    ARCHITECT_ROLE,
    DEVELOPER_ROLE,
    TESTER_ROLE,
    REVIEWER_ROLE,
    get_role,
    estimate_workflow_cost
)

from csv_project_planner.src.models import (
    ProjectTask,
    ExtendedProjectTask,
    TaskType,
    Status,
    Priority,
    DependencyType
)
from csv_project_planner.src.planner import ProjectPlanner
from csv_project_planner.src.validation import TaskValidator
from csv_project_planner.src.critical_path import CriticalPathCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpecializedRolesProjectPlanner:
    """
    Advanced project planner that uses specialized AI roles to generate
    high-quality, comprehensive project plans with 90% quality target.
    """

    def __init__(self, project_name: str, project_description: str):
        """
        Initialize the specialized roles project planner.

        Args:
            project_name: Name of the project
            project_description: Detailed project description
        """
        self.project_name = project_name
        self.project_description = project_description
        self.planner = ProjectPlanner()
        self.quality_score = 0.0
        self.workflow_metrics = {}
        self.phase_tasks = {}

        # Quality thresholds
        self.MIN_QUALITY_SCORE = 90
        self.TASK_COMPLETION_TARGET = 95

        # Specialized role assignments
        self.role_assignments = {
            'architect': ARCHITECT_ROLE,
            'developer': DEVELOPER_ROLE,
            'tester': TESTER_ROLE,
            'reviewer': REVIEWER_ROLE
        }

    def generate_comprehensive_plan(
        self,
        start_date: datetime,
        target_end_date: Optional[datetime] = None,
        resource_pool: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive project plan using specialized roles workflow.

        Args:
            start_date: Project start date
            target_end_date: Optional target completion date
            resource_pool: Optional list of available resources

        Returns:
            Dictionary containing the complete project plan and metrics
        """
        logger.info(f"Starting comprehensive plan generation for: {self.project_name}")

        # Default resource pool with specialized roles
        if resource_pool is None:
            resource_pool = [
                "Project Manager",
                "Solution Architect",
                "Lead Developer",
                "Senior Developer",
                "Backend Developer",
                "Frontend Developer",
                "DevOps Engineer",
                "QA Lead",
                "Test Engineer",
                "Security Specialist",
                "Technical Writer",
                "Business Analyst"
            ]

        # Phase 1: Architecture and Planning (Architect Role)
        architecture_tasks = self._generate_architecture_phase(
            start_date,
            resource_pool
        )

        # Phase 2: Implementation Tasks (Developer Role)
        implementation_tasks = self._generate_implementation_phase(
            architecture_tasks,
            resource_pool
        )

        # Phase 3: Testing and QA (Tester Role)
        testing_tasks = self._generate_testing_phase(
            implementation_tasks,
            resource_pool
        )

        # Phase 4: Review and Deployment (Reviewer Role)
        deployment_tasks = self._generate_deployment_phase(
            testing_tasks,
            resource_pool
        )

        # Phase 5: Documentation
        documentation_tasks = self._generate_documentation_phase(
            deployment_tasks,
            resource_pool
        )

        # Phase 6: Maintenance Planning
        maintenance_tasks = self._generate_maintenance_phase(
            documentation_tasks,
            resource_pool,
            target_end_date
        )

        # Compile all tasks
        all_tasks = (
            architecture_tasks +
            implementation_tasks +
            testing_tasks +
            deployment_tasks +
            documentation_tasks +
            maintenance_tasks
        )

        # Add all tasks to planner
        self.planner.add_tasks(all_tasks)

        # Validate the plan
        is_valid, errors, warnings = self.planner.validate()

        if not is_valid:
            logger.error(f"Validation failed with errors: {errors}")
            raise ValueError(f"Project plan validation failed: {errors}")

        # Calculate critical path
        critical_path, metrics = self.planner.calculate_critical_path()

        # Analyze resources
        resource_analysis = self.planner.analyze_resources()

        # Get project statistics
        statistics = self.planner.get_project_statistics()

        # Calculate quality score
        self.quality_score = self._calculate_quality_score(
            all_tasks,
            critical_path,
            resource_analysis
        )

        # Prepare comprehensive result
        result = {
            'project_name': self.project_name,
            'project_description': self.project_description,
            'generation_timestamp': datetime.utcnow().isoformat(),
            'quality_score': self.quality_score,
            'quality_target_met': self.quality_score >= self.MIN_QUALITY_SCORE,
            'total_tasks': len(all_tasks),
            'phases': {
                'architecture': len(architecture_tasks),
                'implementation': len(implementation_tasks),
                'testing': len(testing_tasks),
                'deployment': len(deployment_tasks),
                'documentation': len(documentation_tasks),
                'maintenance': len(maintenance_tasks)
            },
            'critical_path': {
                'task_ids': critical_path,
                'length': len(critical_path),
                'metrics': metrics
            },
            'resource_analysis': resource_analysis,
            'statistics': statistics,
            'validation': {
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings
            },
            'estimated_cost': estimate_workflow_cost(
                architect_tokens=4000,
                developer_tokens=8000,
                tester_tokens=6000,
                reviewer_tokens=4000
            ),
            'tasks': [task.to_csv_row() for task in all_tasks]
        }

        logger.info(f"Plan generation complete. Quality score: {self.quality_score}%")

        return result

    def _generate_architecture_phase(
        self,
        start_date: datetime,
        resource_pool: List[str]
    ) -> List[ExtendedProjectTask]:
        """Generate architecture and planning phase tasks."""

        tasks = []
        current_date = start_date

        # Phase header task
        phase_task = ExtendedProjectTask(
            task_id="ARCH-000",
            task_name="Architecture & Planning Phase",
            wbs_code="1",
            task_type=TaskType.PHASE,
            description="High-level system architecture and project planning",
            start_date=current_date,
            end_date=current_date + timedelta(days=10),
            duration_days=Decimal("10"),
            priority=Priority.CRITICAL,
            owner="Solution Architect",
            assigned_to="Solution Architect",
            estimated_hours=Decimal("80"),
            quality_gate=True,
            risk_level=Priority.HIGH
        )
        tasks.append(phase_task)

        # Requirements analysis
        req_task = ExtendedProjectTask(
            task_id="ARCH-001",
            task_name="Requirements Analysis",
            wbs_code="1.1",
            task_type=TaskType.TASK,
            description="Analyze and document detailed project requirements",
            start_date=current_date,
            end_date=current_date + timedelta(days=2),
            duration_days=Decimal("2"),
            priority=Priority.CRITICAL,
            assigned_to="Business Analyst",
            predecessors=[],
            estimated_hours=Decimal("16"),
            quality_gate=True
        )
        tasks.append(req_task)

        # System design
        design_task = ExtendedProjectTask(
            task_id="ARCH-002",
            task_name="System Architecture Design",
            wbs_code="1.2",
            task_type=TaskType.TASK,
            description="Design comprehensive system architecture with component diagrams",
            start_date=current_date + timedelta(days=2),
            end_date=current_date + timedelta(days=5),
            duration_days=Decimal("3"),
            priority=Priority.CRITICAL,
            assigned_to="Solution Architect",
            predecessors=["ARCH-001"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(design_task)

        # Technical specifications
        spec_task = ExtendedProjectTask(
            task_id="ARCH-003",
            task_name="Technical Specifications",
            wbs_code="1.3",
            task_type=TaskType.DELIVERABLE,
            description="Create detailed technical specifications for all components",
            start_date=current_date + timedelta(days=5),
            end_date=current_date + timedelta(days=8),
            duration_days=Decimal("3"),
            priority=Priority.HIGH,
            assigned_to="Lead Developer",
            predecessors=["ARCH-002"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(spec_task)

        # Risk assessment
        risk_task = ExtendedProjectTask(
            task_id="ARCH-004",
            task_name="Risk Assessment & Mitigation Planning",
            wbs_code="1.4",
            task_type=TaskType.TASK,
            description="Identify project risks and create mitigation strategies",
            start_date=current_date + timedelta(days=3),
            end_date=current_date + timedelta(days=5),
            duration_days=Decimal("2"),
            priority=Priority.HIGH,
            assigned_to="Project Manager",
            predecessors=["ARCH-002"],
            estimated_hours=Decimal("16"),
            risk_level=Priority.HIGH
        )
        tasks.append(risk_task)

        # Architecture review milestone
        review_task = ExtendedProjectTask(
            task_id="ARCH-005",
            task_name="Architecture Review & Approval",
            wbs_code="1.5",
            task_type=TaskType.MILESTONE,
            description="Review and approve architecture before implementation",
            start_date=current_date + timedelta(days=8),
            end_date=current_date + timedelta(days=10),
            duration_days=Decimal("2"),
            priority=Priority.CRITICAL,
            assigned_to="Solution Architect",
            predecessors=["ARCH-003", "ARCH-004"],
            estimated_hours=Decimal("16"),
            quality_gate=True,
            is_critical=True
        )
        tasks.append(review_task)

        self.phase_tasks['architecture'] = [t.task_id for t in tasks]
        return tasks

    def _generate_implementation_phase(
        self,
        previous_phase_tasks: List[ExtendedProjectTask],
        resource_pool: List[str]
    ) -> List[ExtendedProjectTask]:
        """Generate implementation phase tasks."""

        tasks = []
        # Get the last task from previous phase
        last_task = previous_phase_tasks[-1]
        start_date = last_task.end_date + timedelta(days=1)

        # Phase header
        phase_task = ExtendedProjectTask(
            task_id="IMPL-000",
            task_name="Implementation Phase",
            wbs_code="2",
            task_type=TaskType.PHASE,
            description="Core system implementation and development",
            start_date=start_date,
            end_date=start_date + timedelta(days=30),
            duration_days=Decimal("30"),
            priority=Priority.CRITICAL,
            owner="Lead Developer",
            assigned_to="Lead Developer",
            predecessors=["ARCH-005"],
            estimated_hours=Decimal("240"),
            quality_gate=True
        )
        tasks.append(phase_task)

        # Backend development
        backend_task = ExtendedProjectTask(
            task_id="IMPL-001",
            task_name="Backend API Development",
            wbs_code="2.1",
            task_type=TaskType.TASK,
            description="Develop RESTful API endpoints and business logic",
            start_date=start_date,
            end_date=start_date + timedelta(days=10),
            duration_days=Decimal("10"),
            priority=Priority.CRITICAL,
            assigned_to="Backend Developer",
            predecessors=["ARCH-005"],
            estimated_hours=Decimal("80"),
            quality_gate=True
        )
        tasks.append(backend_task)

        # Database implementation
        db_task = ExtendedProjectTask(
            task_id="IMPL-002",
            task_name="Database Schema Implementation",
            wbs_code="2.2",
            task_type=TaskType.TASK,
            description="Create database schema, indexes, and stored procedures",
            start_date=start_date,
            end_date=start_date + timedelta(days=5),
            duration_days=Decimal("5"),
            priority=Priority.HIGH,
            assigned_to="Backend Developer",
            predecessors=["ARCH-005"],
            estimated_hours=Decimal("40"),
            quality_gate=True
        )
        tasks.append(db_task)

        # Frontend development
        frontend_task = ExtendedProjectTask(
            task_id="IMPL-003",
            task_name="Frontend UI Development",
            wbs_code="2.3",
            task_type=TaskType.TASK,
            description="Develop user interface components and interactions",
            start_date=start_date + timedelta(days=5),
            end_date=start_date + timedelta(days=15),
            duration_days=Decimal("10"),
            priority=Priority.HIGH,
            assigned_to="Frontend Developer",
            predecessors=["IMPL-001"],
            estimated_hours=Decimal("80"),
            quality_gate=True
        )
        tasks.append(frontend_task)

        # Integration layer
        integration_task = ExtendedProjectTask(
            task_id="IMPL-004",
            task_name="System Integration",
            wbs_code="2.4",
            task_type=TaskType.TASK,
            description="Integrate all components and external services",
            start_date=start_date + timedelta(days=15),
            end_date=start_date + timedelta(days=20),
            duration_days=Decimal("5"),
            priority=Priority.HIGH,
            assigned_to="Lead Developer",
            predecessors=["IMPL-003", "IMPL-002"],
            estimated_hours=Decimal("40"),
            quality_gate=True
        )
        tasks.append(integration_task)

        # Security implementation
        security_task = ExtendedProjectTask(
            task_id="IMPL-005",
            task_name="Security Features Implementation",
            wbs_code="2.5",
            task_type=TaskType.TASK,
            description="Implement authentication, authorization, and security features",
            start_date=start_date + timedelta(days=10),
            end_date=start_date + timedelta(days=15),
            duration_days=Decimal("5"),
            priority=Priority.CRITICAL,
            assigned_to="Security Specialist",
            predecessors=["IMPL-001"],
            estimated_hours=Decimal("40"),
            quality_gate=True,
            risk_level=Priority.HIGH
        )
        tasks.append(security_task)

        # Performance optimization
        perf_task = ExtendedProjectTask(
            task_id="IMPL-006",
            task_name="Performance Optimization",
            wbs_code="2.6",
            task_type=TaskType.TASK,
            description="Optimize system performance and resource usage",
            start_date=start_date + timedelta(days=20),
            end_date=start_date + timedelta(days=25),
            duration_days=Decimal("5"),
            priority=Priority.MEDIUM,
            assigned_to="Senior Developer",
            predecessors=["IMPL-004"],
            estimated_hours=Decimal("40"),
            quality_gate=True
        )
        tasks.append(perf_task)

        # Code review milestone
        code_review_task = ExtendedProjectTask(
            task_id="IMPL-007",
            task_name="Code Review & Quality Check",
            wbs_code="2.7",
            task_type=TaskType.MILESTONE,
            description="Comprehensive code review and quality assessment",
            start_date=start_date + timedelta(days=25),
            end_date=start_date + timedelta(days=30),
            duration_days=Decimal("5"),
            priority=Priority.CRITICAL,
            assigned_to="Lead Developer",
            predecessors=["IMPL-006", "IMPL-005"],
            estimated_hours=Decimal("40"),
            quality_gate=True,
            is_critical=True
        )
        tasks.append(code_review_task)

        self.phase_tasks['implementation'] = [t.task_id for t in tasks]
        return tasks

    def _generate_testing_phase(
        self,
        previous_phase_tasks: List[ExtendedProjectTask],
        resource_pool: List[str]
    ) -> List[ExtendedProjectTask]:
        """Generate testing and QA phase tasks."""

        tasks = []
        last_task = previous_phase_tasks[-1]
        start_date = last_task.end_date + timedelta(days=1)

        # Phase header
        phase_task = ExtendedProjectTask(
            task_id="TEST-000",
            task_name="Testing & Quality Assurance Phase",
            wbs_code="3",
            task_type=TaskType.PHASE,
            description="Comprehensive testing and quality assurance",
            start_date=start_date,
            end_date=start_date + timedelta(days=20),
            duration_days=Decimal("20"),
            priority=Priority.CRITICAL,
            owner="QA Lead",
            assigned_to="QA Lead",
            predecessors=["IMPL-007"],
            estimated_hours=Decimal("160"),
            quality_gate=True
        )
        tasks.append(phase_task)

        # Test planning
        test_plan_task = ExtendedProjectTask(
            task_id="TEST-001",
            task_name="Test Planning & Strategy",
            wbs_code="3.1",
            task_type=TaskType.TASK,
            description="Create comprehensive test plans and strategies",
            start_date=start_date,
            end_date=start_date + timedelta(days=2),
            duration_days=Decimal("2"),
            priority=Priority.HIGH,
            assigned_to="QA Lead",
            predecessors=["IMPL-007"],
            estimated_hours=Decimal("16"),
            quality_gate=True
        )
        tasks.append(test_plan_task)

        # Unit testing
        unit_test_task = ExtendedProjectTask(
            task_id="TEST-002",
            task_name="Unit Testing",
            wbs_code="3.2",
            task_type=TaskType.TASK,
            description="Execute comprehensive unit tests with 80% coverage",
            start_date=start_date + timedelta(days=2),
            end_date=start_date + timedelta(days=5),
            duration_days=Decimal("3"),
            priority=Priority.HIGH,
            assigned_to="Test Engineer",
            predecessors=["TEST-001"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(unit_test_task)

        # Integration testing
        integration_test_task = ExtendedProjectTask(
            task_id="TEST-003",
            task_name="Integration Testing",
            wbs_code="3.3",
            task_type=TaskType.TASK,
            description="Test component integrations and data flows",
            start_date=start_date + timedelta(days=5),
            end_date=start_date + timedelta(days=8),
            duration_days=Decimal("3"),
            priority=Priority.HIGH,
            assigned_to="Test Engineer",
            predecessors=["TEST-002"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(integration_test_task)

        # System testing
        system_test_task = ExtendedProjectTask(
            task_id="TEST-004",
            task_name="System Testing",
            wbs_code="3.4",
            task_type=TaskType.TASK,
            description="End-to-end system testing with all components",
            start_date=start_date + timedelta(days=8),
            end_date=start_date + timedelta(days=12),
            duration_days=Decimal("4"),
            priority=Priority.HIGH,
            assigned_to="QA Lead",
            predecessors=["TEST-003"],
            estimated_hours=Decimal("32"),
            quality_gate=True
        )
        tasks.append(system_test_task)

        # Performance testing
        perf_test_task = ExtendedProjectTask(
            task_id="TEST-005",
            task_name="Performance & Load Testing",
            wbs_code="3.5",
            task_type=TaskType.TASK,
            description="Performance, load, and stress testing",
            start_date=start_date + timedelta(days=8),
            end_date=start_date + timedelta(days=11),
            duration_days=Decimal("3"),
            priority=Priority.HIGH,
            assigned_to="DevOps Engineer",
            predecessors=["TEST-003"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(perf_test_task)

        # Security testing
        security_test_task = ExtendedProjectTask(
            task_id="TEST-006",
            task_name="Security Testing",
            wbs_code="3.6",
            task_type=TaskType.TASK,
            description="Security vulnerability assessment and penetration testing",
            start_date=start_date + timedelta(days=10),
            end_date=start_date + timedelta(days=13),
            duration_days=Decimal("3"),
            priority=Priority.CRITICAL,
            assigned_to="Security Specialist",
            predecessors=["TEST-003"],
            estimated_hours=Decimal("24"),
            quality_gate=True,
            risk_level=Priority.HIGH
        )
        tasks.append(security_test_task)

        # UAT
        uat_task = ExtendedProjectTask(
            task_id="TEST-007",
            task_name="User Acceptance Testing",
            wbs_code="3.7",
            task_type=TaskType.TASK,
            description="User acceptance testing with stakeholders",
            start_date=start_date + timedelta(days=12),
            end_date=start_date + timedelta(days=15),
            duration_days=Decimal("3"),
            priority=Priority.HIGH,
            assigned_to="Business Analyst",
            predecessors=["TEST-004"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(uat_task)

        # Bug fixing
        bug_fix_task = ExtendedProjectTask(
            task_id="TEST-008",
            task_name="Bug Fixing & Retesting",
            wbs_code="3.8",
            task_type=TaskType.TASK,
            description="Fix identified bugs and perform regression testing",
            start_date=start_date + timedelta(days=15),
            end_date=start_date + timedelta(days=18),
            duration_days=Decimal("3"),
            priority=Priority.HIGH,
            assigned_to="Lead Developer",
            predecessors=["TEST-007", "TEST-005", "TEST-006"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(bug_fix_task)

        # Test completion milestone
        test_complete_task = ExtendedProjectTask(
            task_id="TEST-009",
            task_name="Testing Sign-off",
            wbs_code="3.9",
            task_type=TaskType.MILESTONE,
            description="Final testing sign-off and quality certification",
            start_date=start_date + timedelta(days=18),
            end_date=start_date + timedelta(days=20),
            duration_days=Decimal("2"),
            priority=Priority.CRITICAL,
            assigned_to="QA Lead",
            predecessors=["TEST-008"],
            estimated_hours=Decimal("16"),
            quality_gate=True,
            is_critical=True
        )
        tasks.append(test_complete_task)

        self.phase_tasks['testing'] = [t.task_id for t in tasks]
        return tasks

    def _generate_deployment_phase(
        self,
        previous_phase_tasks: List[ExtendedProjectTask],
        resource_pool: List[str]
    ) -> List[ExtendedProjectTask]:
        """Generate deployment and go-live phase tasks."""

        tasks = []
        last_task = previous_phase_tasks[-1]
        start_date = last_task.end_date + timedelta(days=1)

        # Phase header
        phase_task = ExtendedProjectTask(
            task_id="DEPL-000",
            task_name="Deployment & Go-Live Phase",
            wbs_code="4",
            task_type=TaskType.PHASE,
            description="Production deployment and go-live activities",
            start_date=start_date,
            end_date=start_date + timedelta(days=10),
            duration_days=Decimal("10"),
            priority=Priority.CRITICAL,
            owner="DevOps Engineer",
            assigned_to="DevOps Engineer",
            predecessors=["TEST-009"],
            estimated_hours=Decimal("80"),
            quality_gate=True
        )
        tasks.append(phase_task)

        # Deployment preparation
        prep_task = ExtendedProjectTask(
            task_id="DEPL-001",
            task_name="Deployment Preparation",
            wbs_code="4.1",
            task_type=TaskType.TASK,
            description="Prepare production environment and deployment packages",
            start_date=start_date,
            end_date=start_date + timedelta(days=2),
            duration_days=Decimal("2"),
            priority=Priority.CRITICAL,
            assigned_to="DevOps Engineer",
            predecessors=["TEST-009"],
            estimated_hours=Decimal("16"),
            quality_gate=True
        )
        tasks.append(prep_task)

        # Infrastructure setup
        infra_task = ExtendedProjectTask(
            task_id="DEPL-002",
            task_name="Production Infrastructure Setup",
            wbs_code="4.2",
            task_type=TaskType.TASK,
            description="Configure production servers, databases, and services",
            start_date=start_date + timedelta(days=2),
            end_date=start_date + timedelta(days=4),
            duration_days=Decimal("2"),
            priority=Priority.CRITICAL,
            assigned_to="DevOps Engineer",
            predecessors=["DEPL-001"],
            estimated_hours=Decimal("16"),
            quality_gate=True,
            risk_level=Priority.HIGH
        )
        tasks.append(infra_task)

        # Data migration
        migration_task = ExtendedProjectTask(
            task_id="DEPL-003",
            task_name="Data Migration",
            wbs_code="4.3",
            task_type=TaskType.TASK,
            description="Migrate data to production environment",
            start_date=start_date + timedelta(days=4),
            end_date=start_date + timedelta(days=6),
            duration_days=Decimal("2"),
            priority=Priority.HIGH,
            assigned_to="Backend Developer",
            predecessors=["DEPL-002"],
            estimated_hours=Decimal("16"),
            quality_gate=True,
            risk_level=Priority.HIGH
        )
        tasks.append(migration_task)

        # Deployment execution
        deploy_task = ExtendedProjectTask(
            task_id="DEPL-004",
            task_name="Production Deployment",
            wbs_code="4.4",
            task_type=TaskType.TASK,
            description="Execute production deployment with rollback plan",
            start_date=start_date + timedelta(days=6),
            end_date=start_date + timedelta(days=7),
            duration_days=Decimal("1"),
            priority=Priority.CRITICAL,
            assigned_to="DevOps Engineer",
            predecessors=["DEPL-003"],
            estimated_hours=Decimal("8"),
            quality_gate=True,
            is_critical=True
        )
        tasks.append(deploy_task)

        # Smoke testing
        smoke_task = ExtendedProjectTask(
            task_id="DEPL-005",
            task_name="Production Smoke Testing",
            wbs_code="4.5",
            task_type=TaskType.TASK,
            description="Verify critical functionality in production",
            start_date=start_date + timedelta(days=7),
            end_date=start_date + timedelta(days=8),
            duration_days=Decimal("1"),
            priority=Priority.CRITICAL,
            assigned_to="QA Lead",
            predecessors=["DEPL-004"],
            estimated_hours=Decimal("8"),
            quality_gate=True
        )
        tasks.append(smoke_task)

        # Monitoring setup
        monitor_task = ExtendedProjectTask(
            task_id="DEPL-006",
            task_name="Monitoring & Alerting Setup",
            wbs_code="4.6",
            task_type=TaskType.TASK,
            description="Configure production monitoring and alerts",
            start_date=start_date + timedelta(days=7),
            end_date=start_date + timedelta(days=9),
            duration_days=Decimal("2"),
            priority=Priority.HIGH,
            assigned_to="DevOps Engineer",
            predecessors=["DEPL-004"],
            estimated_hours=Decimal("16"),
            quality_gate=True
        )
        tasks.append(monitor_task)

        # Go-live milestone
        golive_task = ExtendedProjectTask(
            task_id="DEPL-007",
            task_name="Go-Live",
            wbs_code="4.7",
            task_type=TaskType.MILESTONE,
            description="System go-live and production handover",
            start_date=start_date + timedelta(days=9),
            end_date=start_date + timedelta(days=10),
            duration_days=Decimal("1"),
            priority=Priority.CRITICAL,
            assigned_to="Project Manager",
            predecessors=["DEPL-005", "DEPL-006"],
            estimated_hours=Decimal("8"),
            quality_gate=True,
            is_critical=True
        )
        tasks.append(golive_task)

        self.phase_tasks['deployment'] = [t.task_id for t in tasks]
        return tasks

    def _generate_documentation_phase(
        self,
        previous_phase_tasks: List[ExtendedProjectTask],
        resource_pool: List[str]
    ) -> List[ExtendedProjectTask]:
        """Generate documentation phase tasks."""

        tasks = []
        last_task = previous_phase_tasks[-1]
        start_date = last_task.end_date + timedelta(days=1)

        # Phase header
        phase_task = ExtendedProjectTask(
            task_id="DOCS-000",
            task_name="Documentation Phase",
            wbs_code="5",
            task_type=TaskType.PHASE,
            description="Comprehensive project documentation",
            start_date=start_date,
            end_date=start_date + timedelta(days=10),
            duration_days=Decimal("10"),
            priority=Priority.MEDIUM,
            owner="Technical Writer",
            assigned_to="Technical Writer",
            predecessors=["DEPL-007"],
            estimated_hours=Decimal("80"),
            quality_gate=True
        )
        tasks.append(phase_task)

        # User documentation
        user_docs_task = ExtendedProjectTask(
            task_id="DOCS-001",
            task_name="User Documentation",
            wbs_code="5.1",
            task_type=TaskType.DELIVERABLE,
            description="Create end-user documentation and guides",
            start_date=start_date,
            end_date=start_date + timedelta(days=3),
            duration_days=Decimal("3"),
            priority=Priority.HIGH,
            assigned_to="Technical Writer",
            predecessors=["DEPL-007"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(user_docs_task)

        # Technical documentation
        tech_docs_task = ExtendedProjectTask(
            task_id="DOCS-002",
            task_name="Technical Documentation",
            wbs_code="5.2",
            task_type=TaskType.DELIVERABLE,
            description="Create API documentation and technical guides",
            start_date=start_date,
            end_date=start_date + timedelta(days=5),
            duration_days=Decimal("5"),
            priority=Priority.HIGH,
            assigned_to="Lead Developer",
            predecessors=["DEPL-007"],
            estimated_hours=Decimal("40"),
            quality_gate=True
        )
        tasks.append(tech_docs_task)

        # Operations manual
        ops_docs_task = ExtendedProjectTask(
            task_id="DOCS-003",
            task_name="Operations Manual",
            wbs_code="5.3",
            task_type=TaskType.DELIVERABLE,
            description="Create operations and maintenance manual",
            start_date=start_date + timedelta(days=3),
            end_date=start_date + timedelta(days=6),
            duration_days=Decimal("3"),
            priority=Priority.MEDIUM,
            assigned_to="DevOps Engineer",
            predecessors=["DOCS-001"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(ops_docs_task)

        # Training materials
        training_task = ExtendedProjectTask(
            task_id="DOCS-004",
            task_name="Training Materials",
            wbs_code="5.4",
            task_type=TaskType.DELIVERABLE,
            description="Create training materials and videos",
            start_date=start_date + timedelta(days=5),
            end_date=start_date + timedelta(days=8),
            duration_days=Decimal("3"),
            priority=Priority.MEDIUM,
            assigned_to="Business Analyst",
            predecessors=["DOCS-001"],
            estimated_hours=Decimal("24"),
            quality_gate=True
        )
        tasks.append(training_task)

        # Knowledge transfer
        kt_task = ExtendedProjectTask(
            task_id="DOCS-005",
            task_name="Knowledge Transfer Sessions",
            wbs_code="5.5",
            task_type=TaskType.TASK,
            description="Conduct knowledge transfer sessions with support team",
            start_date=start_date + timedelta(days=8),
            end_date=start_date + timedelta(days=10),
            duration_days=Decimal("2"),
            priority=Priority.HIGH,
            assigned_to="Lead Developer",
            predecessors=["DOCS-002", "DOCS-003", "DOCS-004"],
            estimated_hours=Decimal("16"),
            quality_gate=True
        )
        tasks.append(kt_task)

        self.phase_tasks['documentation'] = [t.task_id for t in tasks]
        return tasks

    def _generate_maintenance_phase(
        self,
        previous_phase_tasks: List[ExtendedProjectTask],
        resource_pool: List[str],
        target_end_date: Optional[datetime] = None
    ) -> List[ExtendedProjectTask]:
        """Generate maintenance and support phase tasks."""

        tasks = []
        last_task = previous_phase_tasks[-1]
        start_date = last_task.end_date + timedelta(days=1)

        # Default to 30-day maintenance period
        end_date = target_end_date or (start_date + timedelta(days=30))
        duration = (end_date - start_date).days

        # Phase header
        phase_task = ExtendedProjectTask(
            task_id="MAINT-000",
            task_name="Maintenance & Support Phase",
            wbs_code="6",
            task_type=TaskType.PHASE,
            description="Post-deployment maintenance and support",
            start_date=start_date,
            end_date=end_date,
            duration_days=Decimal(str(duration)),
            priority=Priority.MEDIUM,
            owner="Project Manager",
            assigned_to="Support Team",
            predecessors=["DOCS-005"],
            estimated_hours=Decimal("160"),
            quality_gate=False
        )
        tasks.append(phase_task)

        # Hypercare support
        hypercare_task = ExtendedProjectTask(
            task_id="MAINT-001",
            task_name="Hypercare Support",
            wbs_code="6.1",
            task_type=TaskType.TASK,
            description="Provide intensive support for first 2 weeks",
            start_date=start_date,
            end_date=start_date + timedelta(days=14),
            duration_days=Decimal("14"),
            priority=Priority.HIGH,
            assigned_to="Support Team",
            predecessors=["DOCS-005"],
            estimated_hours=Decimal("80"),
            quality_gate=False
        )
        tasks.append(hypercare_task)

        # Performance monitoring
        perf_monitor_task = ExtendedProjectTask(
            task_id="MAINT-002",
            task_name="Performance Monitoring",
            wbs_code="6.2",
            task_type=TaskType.TASK,
            description="Monitor system performance and optimize",
            start_date=start_date,
            end_date=start_date + timedelta(days=30),
            duration_days=Decimal("30"),
            priority=Priority.MEDIUM,
            assigned_to="DevOps Engineer",
            predecessors=["DOCS-005"],
            estimated_hours=Decimal("40"),
            quality_gate=False
        )
        tasks.append(perf_monitor_task)

        # Bug fixes
        bugfix_task = ExtendedProjectTask(
            task_id="MAINT-003",
            task_name="Production Bug Fixes",
            wbs_code="6.3",
            task_type=TaskType.TASK,
            description="Address production issues and bugs",
            start_date=start_date + timedelta(days=7),
            end_date=start_date + timedelta(days=21),
            duration_days=Decimal("14"),
            priority=Priority.HIGH,
            assigned_to="Senior Developer",
            predecessors=["MAINT-001"],
            estimated_hours=Decimal("40"),
            quality_gate=False
        )
        tasks.append(bugfix_task)

        # User feedback
        feedback_task = ExtendedProjectTask(
            task_id="MAINT-004",
            task_name="User Feedback Collection",
            wbs_code="6.4",
            task_type=TaskType.TASK,
            description="Collect and analyze user feedback",
            start_date=start_date + timedelta(days=14),
            end_date=start_date + timedelta(days=21),
            duration_days=Decimal("7"),
            priority=Priority.MEDIUM,
            assigned_to="Business Analyst",
            predecessors=["MAINT-001"],
            estimated_hours=Decimal("24"),
            quality_gate=False
        )
        tasks.append(feedback_task)

        # Lessons learned
        lessons_task = ExtendedProjectTask(
            task_id="MAINT-005",
            task_name="Lessons Learned & Project Closure",
            wbs_code="6.5",
            task_type=TaskType.MILESTONE,
            description="Document lessons learned and close project",
            start_date=start_date + timedelta(days=28),
            end_date=start_date + timedelta(days=30),
            duration_days=Decimal("2"),
            priority=Priority.LOW,
            assigned_to="Project Manager",
            predecessors=["MAINT-003", "MAINT-004"],
            estimated_hours=Decimal("16"),
            quality_gate=True
        )
        tasks.append(lessons_task)

        self.phase_tasks['maintenance'] = [t.task_id for t in tasks]
        return tasks

    def _calculate_quality_score(
        self,
        tasks: List[ExtendedProjectTask],
        critical_path: List[str],
        resource_analysis: Dict[str, Any]
    ) -> float:
        """
        Calculate overall project plan quality score.

        Args:
            tasks: All project tasks
            critical_path: Critical path task IDs
            resource_analysis: Resource allocation analysis

        Returns:
            Quality score as percentage (0-100)
        """
        scores = []

        # 1. Task completeness (20%)
        required_fields = ['description', 'assigned_to', 'predecessors']
        completeness_score = 0
        for task in tasks:
            field_count = sum(1 for field in required_fields if getattr(task, field))
            completeness_score += (field_count / len(required_fields)) * 100
        scores.append(completeness_score / len(tasks) * 0.2)

        # 2. Quality gates coverage (20%)
        quality_gate_count = sum(1 for t in tasks if t.quality_gate)
        quality_gate_score = (quality_gate_count / len(tasks)) * 100
        scores.append(quality_gate_score * 0.2)

        # 3. Critical path clarity (15%)
        critical_path_score = 100 if critical_path else 0
        scores.append(critical_path_score * 0.15)

        # 4. Resource allocation (15%)
        over_allocation_penalty = min(
            resource_analysis.get('over_allocation_count', 0) * 5, 50
        )
        resource_score = max(0, 100 - over_allocation_penalty)
        scores.append(resource_score * 0.15)

        # 5. Risk management (10%)
        risk_identified = sum(1 for t in tasks if hasattr(t, 'risk_level'))
        risk_score = min((risk_identified / len(tasks)) * 200, 100)
        scores.append(risk_score * 0.1)

        # 6. Phase balance (10%)
        phase_sizes = [len(phase) for phase in self.phase_tasks.values()]
        if phase_sizes:
            avg_size = sum(phase_sizes) / len(phase_sizes)
            variance = sum((s - avg_size) ** 2 for s in phase_sizes) / len(phase_sizes)
            balance_score = max(0, 100 - variance)
        else:
            balance_score = 0
        scores.append(balance_score * 0.1)

        # 7. Documentation tasks (10%)
        doc_tasks = sum(1 for t in tasks if 'DOCS' in t.task_id)
        doc_score = min((doc_tasks / len(tasks)) * 500, 100)
        scores.append(doc_score * 0.1)

        return round(sum(scores), 2)

    def export_to_csv(self, output_path: Path) -> str:
        """
        Export the project plan to CSV file.

        Args:
            output_path: Path to output CSV file

        Returns:
            Path to the generated CSV file
        """
        csv_content = self.planner.export_to_csv(
            output_path,
            use_pandas=True,
            include_extended=True
        )

        logger.info(f"Project plan exported to: {output_path}")
        return str(output_path)

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of the project plan.

        Returns:
            Dictionary containing project summary
        """
        stats = self.planner.get_project_statistics()
        dependency_analysis = self.planner.analyze_dependencies()
        gantt_data = self.planner.get_gantt_data()

        return {
            'project_name': self.project_name,
            'quality_score': self.quality_score,
            'statistics': stats,
            'dependencies': dependency_analysis,
            'phases': self.phase_tasks,
            'gantt_preview': gantt_data[:10],  # First 10 tasks for preview
            'workflow_cost': estimate_workflow_cost()
        }


# Example usage
if __name__ == "__main__":
    # Create planner instance
    planner = SpecializedRolesProjectPlanner(
        project_name="Enterprise E-Commerce Platform",
        project_description="Complete e-commerce platform with microservices architecture"
    )

    # Generate comprehensive plan
    plan = planner.generate_comprehensive_plan(
        start_date=datetime(2024, 1, 1),
        target_end_date=datetime(2024, 6, 30)
    )

    # Export to CSV
    csv_path = Path("enterprise_project_plan.csv")
    planner.export_to_csv(csv_path)

    # Generate summary
    summary = planner.generate_summary_report()

    # Print results
    print(f"Project Plan Generated:")
    print(f"  Quality Score: {plan['quality_score']}%")
    print(f"  Total Tasks: {plan['total_tasks']}")
    print(f"  Critical Path Length: {plan['critical_path']['length']}")
    print(f"  Validation: {'PASSED' if plan['validation']['is_valid'] else 'FAILED'}")
    print(f"  CSV Export: {csv_path}")