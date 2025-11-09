"""
Data models for CSV Project Plan Generator.

This module defines Pydantic models for project tasks with comprehensive
validation, including field-level constraints and business rule validation.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class TaskType(str, Enum):
    """Task type enumeration."""
    MILESTONE = "Milestone"
    TASK = "Task"
    PHASE = "Phase"
    DELIVERABLE = "Deliverable"
    REVIEW = "Review"
    APPROVAL = "Approval"


class Status(str, Enum):
    """Task status enumeration."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    BLOCKED = "Blocked"


class Priority(str, Enum):
    """Task priority enumeration."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DependencyType(str, Enum):
    """Dependency relationship types."""
    FINISH_TO_START = "FS"  # Predecessor must finish before successor starts
    START_TO_START = "SS"   # Both tasks start together
    FINISH_TO_FINISH = "FF"  # Both tasks finish together
    START_TO_FINISH = "SF"   # Predecessor starts before successor finishes


class ProjectTask(BaseModel):
    """
    Core project task model with essential fields.

    This model represents a single task in a project plan with validation
    for all required fields and business rules.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False
    )

    # Core identifiers
    task_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique task identifier"
    )
    task_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task name/title"
    )
    wbs_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Work Breakdown Structure code (e.g., 1.2.3)"
    )

    # Task details
    task_type: TaskType = Field(
        default=TaskType.TASK,
        description="Type of task"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed task description"
    )

    # Scheduling
    start_date: datetime = Field(
        ...,
        description="Planned start date (ISO 8601)"
    )
    end_date: datetime = Field(
        ...,
        description="Planned end date (ISO 8601)"
    )
    duration_days: Decimal = Field(
        ...,
        ge=0,
        description="Task duration in days"
    )

    # Progress tracking
    status: Status = Field(
        default=Status.NOT_STARTED,
        description="Current task status"
    )
    percent_complete: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Completion percentage (0-100)"
    )

    # Priority and assignment
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Task priority level"
    )
    assigned_to: Optional[str] = Field(
        None,
        max_length=100,
        description="Resource/person assigned to task"
    )
    owner: Optional[str] = Field(
        None,
        max_length=100,
        description="Task owner/responsible party"
    )

    # Dependencies
    predecessors: List[str] = Field(
        default_factory=list,
        description="List of predecessor task IDs"
    )
    successors: List[str] = Field(
        default_factory=list,
        description="List of successor task IDs"
    )
    dependency_type: DependencyType = Field(
        default=DependencyType.FINISH_TO_START,
        description="Type of dependency relationship"
    )

    # Cost tracking
    estimated_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Estimated task cost"
    )
    actual_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Actual task cost"
    )

    # Critical path
    is_critical: bool = Field(
        default=False,
        description="Whether task is on critical path"
    )
    slack_days: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Total slack/float in days"
    )

    # Metadata
    created_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Task creation timestamp"
    )
    modified_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last modification timestamp"
    )
    notes: Optional[str] = Field(
        None,
        max_length=5000,
        description="Additional notes"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Task tags/labels"
    )

    @field_validator('wbs_code')
    @classmethod
    def validate_wbs_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate WBS code format (e.g., 1.2.3)."""
        if v is None:
            return v

        # WBS should be dot-separated numbers
        parts = v.split('.')
        if not all(part.isdigit() for part in parts):
            raise ValueError(
                f"WBS code must be dot-separated numbers (e.g., 1.2.3), got: {v}"
            )
        return v

    @model_validator(mode='after')
    def validate_dates(self) -> 'ProjectTask':
        """Validate date relationships and duration."""
        # End date must be >= start date
        if self.end_date < self.start_date:
            raise ValueError(
                f"End date ({self.end_date}) cannot be before start date ({self.start_date})"
            )

        # Calculate actual duration
        actual_duration = (self.end_date - self.start_date).days

        # Allow small tolerance for decimal precision
        if abs(float(self.duration_days) - actual_duration) > 0.1:
            raise ValueError(
                f"Duration ({self.duration_days} days) doesn't match date range "
                f"({actual_duration} days from {self.start_date} to {self.end_date})"
            )

        return self

    @model_validator(mode='after')
    def validate_completion(self) -> 'ProjectTask':
        """Validate status and completion percentage consistency."""
        if self.status == Status.COMPLETED and self.percent_complete != 100:
            raise ValueError(
                f"Completed task must have 100% completion, got {self.percent_complete}%"
            )

        if self.status == Status.NOT_STARTED and self.percent_complete > 0:
            raise ValueError(
                f"Not started task cannot have completion > 0%, got {self.percent_complete}%"
            )

        return self

    @model_validator(mode='after')
    def validate_costs(self) -> 'ProjectTask':
        """Validate cost relationships."""
        if self.actual_cost > 0 and self.status == Status.NOT_STARTED:
            raise ValueError(
                "Task not started cannot have actual costs"
            )

        return self

    def to_csv_row(self) -> Dict[str, Any]:
        """
        Convert task to CSV row dictionary.

        Returns:
            Dictionary with string keys suitable for CSV writing
        """
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'wbs_code': self.wbs_code or '',
            'task_type': self.task_type.value,
            'description': self.description or '',
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'duration_days': str(self.duration_days),
            'status': self.status.value,
            'percent_complete': self.percent_complete,
            'priority': self.priority.value,
            'assigned_to': self.assigned_to or '',
            'owner': self.owner or '',
            'predecessors': ';'.join(self.predecessors),
            'successors': ';'.join(self.successors),
            'dependency_type': self.dependency_type.value,
            'estimated_cost': str(self.estimated_cost),
            'actual_cost': str(self.actual_cost),
            'is_critical': str(self.is_critical),
            'slack_days': str(self.slack_days),
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat(),
            'notes': self.notes or '',
            'tags': ';'.join(self.tags)
        }


class ExtendedProjectTask(ProjectTask):
    """
    Extended task model with additional fields for advanced project management.

    Adds fields for resource management, risk tracking, and integration
    with external PM tools.
    """

    # Resource management
    estimated_hours: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Estimated work hours"
    )
    actual_hours: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Actual work hours spent"
    )
    resource_allocation: Decimal = Field(
        default=Decimal("100.00"),
        ge=0,
        le=100,
        description="Resource allocation percentage"
    )

    # Risk and quality
    risk_level: Priority = Field(
        default=Priority.LOW,
        description="Risk level (reuses Priority enum)"
    )
    quality_gate: bool = Field(
        default=False,
        description="Whether task includes quality gate"
    )

    # External tool integration
    jira_key: Optional[str] = Field(
        None,
        max_length=50,
        description="Jira issue key"
    )
    asana_gid: Optional[str] = Field(
        None,
        max_length=50,
        description="Asana task GID"
    )
    ms_project_id: Optional[int] = Field(
        None,
        description="MS Project unique ID"
    )

    # Custom fields (extensible)
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom field values"
    )

    @field_validator('custom_fields')
    @classmethod
    def validate_custom_fields(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate custom fields are JSON-serializable."""
        try:
            import json
            json.dumps(v)
            return v
        except (TypeError, ValueError) as e:
            raise ValueError(f"Custom fields must be JSON-serializable: {e}")

    def to_csv_row(self) -> Dict[str, Any]:
        """
        Convert extended task to CSV row dictionary.

        Returns:
            Dictionary with all fields including extended ones
        """
        base_row = super().to_csv_row()

        extended_fields = {
            'estimated_hours': str(self.estimated_hours),
            'actual_hours': str(self.actual_hours),
            'resource_allocation': str(self.resource_allocation),
            'risk_level': self.risk_level.value,
            'quality_gate': str(self.quality_gate),
            'jira_key': self.jira_key or '',
            'asana_gid': self.asana_gid or '',
            'ms_project_id': str(self.ms_project_id) if self.ms_project_id else '',
            'custom_fields': str(self.custom_fields) if self.custom_fields else ''
        }

        base_row.update(extended_fields)
        return base_row
