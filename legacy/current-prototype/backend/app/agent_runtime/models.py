from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from ..models import ArtifactItem


class AgentPlanStep(BaseModel):
    skill_id: str
    goal: str
    expected_output: str


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = [value]

    normalized: list[str] = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, str):
            chunks = re.split(r"(?:\r?\n|[;,，；])+", item)
            for chunk in chunks:
                cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)、])\s*", "", chunk).strip()
                if cleaned:
                    normalized.append(cleaned)
            continue
        normalized.append(str(item).strip())
    return normalized


class AgentPlan(BaseModel):
    mission_title: str
    plan_summary: str
    selected_skills: list[str] = Field(default_factory=list)
    steps: list[AgentPlanStep] = Field(default_factory=list)
    report_focus: list[str] = Field(default_factory=list)

    @field_validator("selected_skills", "report_focus", mode="before")
    @classmethod
    def _normalize_string_lists(cls, value: Any) -> list[str]:
        return _normalize_text_list(value)

    @field_validator("steps", mode="before")
    @classmethod
    def _normalize_steps(cls, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


class AgentReport(BaseModel):
    report_title: str
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    verification_notes: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)

    @field_validator("key_findings", "verification_notes", "next_actions", mode="before")
    @classmethod
    def _normalize_report_lists(cls, value: Any) -> list[str]:
        return _normalize_text_list(value)


class GeometryInspection(BaseModel):
    file_name: str
    file_size_bytes: int
    input_format: str
    geometry_family: str
    source_application: str | None = None
    parasolid_key: str | None = None
    estimated_length_m: float | None = None
    triangle_count: int | None = None
    bounding_box: dict[str, float] | None = None
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillExecutionResult(BaseModel):
    skill_id: str
    stage: str
    summary: str
    used_tools: list[str] = Field(default_factory=list)
    metrics: dict[str, float | str] = Field(default_factory=dict)
    artifacts: list[ArtifactItem] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(default_factory=dict)
