from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


TaskType = Literal[
    "resistance",
    "pressure_distribution",
    "wake_field",
    "drift_angle_force",
    "near_free_surface",
    "self_propulsion",
]


class RunStatus(str, Enum):
    DRAFT = "draft"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskSubmission(BaseModel):
    task_description: str
    task_type: TaskType
    geometry_family_hint: str | None = None
    geometry_file_name: str | None = None
    operating_notes: str = ""


class CaseReference(BaseModel):
    title: str
    source: str
    url: str | None = None


class CaseCandidate(BaseModel):
    case_id: str
    title: str
    geometry_family: str
    geometry_description: str
    task_type: str
    condition_tags: list[str] = Field(default_factory=list)
    input_requirements: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    recommended_solver: str
    mesh_strategy: str
    bc_strategy: str
    postprocess_steps: list[str] = Field(default_factory=list)
    validation_targets: list[str] = Field(default_factory=list)
    reference_sources: list[CaseReference] = Field(default_factory=list)
    reuse_role: str
    linked_skills: list[str] = Field(default_factory=list)
    score: float = 0.0
    rationale: str = ""


class CaseSearchResult(BaseModel):
    candidates: list[CaseCandidate]
    recommended: CaseCandidate


class SkillManifest(BaseModel):
    skill_id: str
    name: str
    version: str
    category: str
    task_types: list[str]
    geometry_families: list[str]
    condition_tags: list[str] = Field(default_factory=list)
    input_schema: dict[str, str] = Field(default_factory=dict)
    output_schema: dict[str, str] = Field(default_factory=dict)
    required_tools: list[str]
    preconditions: list[str] = Field(default_factory=list)
    artifacts_out: list[str] = Field(default_factory=list)
    linked_cases: list[str] = Field(default_factory=list)
    validation_role: str
    owner: str


class WorkflowStage(BaseModel):
    stage_id: str
    title: str
    description: str


class WorkflowDraft(BaseModel):
    summary: str
    assumptions: list[str] = Field(default_factory=list)
    recommended_case_ids: list[str] = Field(default_factory=list)
    linked_skills: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)
    stages: list[WorkflowStage] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    timestamp: datetime
    stage: str
    message: str
    status: str


EventDetailValue = str | int | float | bool | None

ExecutionAttemptStatus = Literal["running", "completed", "failed"]
AttemptFailureCategory = Literal[
    "dispatch_launch_error",
    "executor_request_failed",
    "executor_reported_failure",
    "execution_failure",
    "service_restart_interruption",
]
AttemptFailureSource = Literal[
    "dispatcher",
    "claude_executor_client",
    "claude_executor",
    "execution_engine",
    "store_recovery",
]


class RunEvent(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: str
    stage: str
    status: str
    message: str
    details: dict[str, EventDetailValue] = Field(default_factory=dict)


class ExecutionAttempt(BaseModel):
    attempt_id: str
    attempt_number: int
    engine_name: str
    status: ExecutionAttemptStatus
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    summary: str | None = None
    error_message: str | None = None
    failure_category: AttemptFailureCategory | None = None
    failure_source: AttemptFailureSource | None = None


class ArtifactItem(BaseModel):
    label: str
    category: str
    relative_path: str
    mime_type: str
    url: str


class RunSummary(BaseModel):
    run_id: str
    status: RunStatus
    current_stage: str
    stage_label: str
    created_at: datetime
    updated_at: datetime
    request: TaskSubmission
    run_directory: str
    geometry_check: str = ""
    candidate_cases: list[CaseCandidate] = Field(default_factory=list)
    selected_case: CaseCandidate | None = None
    workflow_draft: WorkflowDraft | None = None
    confirmed_at: datetime | None = None
    reviewer_notes: str | None = None
    timeline: list[TimelineEvent] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)
    report_markdown: str | None = None
    metrics: dict[str, float | str] = Field(default_factory=dict)


class ConfirmRunRequest(BaseModel):
    confirmed: bool = True
    reviewer_notes: str = ""


class CancelRunRequest(BaseModel):
    reason: str = ""
