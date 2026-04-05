from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .models import ArtifactItem, TaskType


ExecutorTaskStatus = Literal["completed", "failed"]


class ExecutorTaskContext(BaseModel):
    task_description: str
    task_type: TaskType
    geometry_family: str | None = None
    selected_case_id: str | None = None
    selected_case_title: str | None = None
    reviewer_notes: str = ""
    operating_notes: str = ""
    workflow_summary: str = ""
    workflow_assumptions: list[str] = Field(default_factory=list)
    linked_skills: list[str] = Field(default_factory=list)
    selected_case_geometry_description: str = ""
    selected_case_reuse_role: str = ""


class ExecutorTaskRequest(BaseModel):
    job_id: str
    run_id: str
    stage: str
    goal: str
    run_directory: str
    allowed_tools: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)
    input_files: list[str] = Field(default_factory=list)
    context: ExecutorTaskContext


class ExecutorTimelineEvent(BaseModel):
    stage: str
    message: str
    status: str


class ExecutorTaskResult(BaseModel):
    job_id: str
    run_id: str
    status: ExecutorTaskStatus
    summary: str
    executor_name: str
    used_tools: list[str] = Field(default_factory=list)
    metrics: dict[str, float | str] = Field(default_factory=dict)
    timeline: list[ExecutorTimelineEvent] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)
    report_markdown: str | None = None
    error_message: str | None = None
