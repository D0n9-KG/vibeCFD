"""Typed models for the submarine CFD domain layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SubmarineScientificStudyType = Literal[
    "mesh_independence",
    "domain_sensitivity",
    "time_step_sensitivity",
]


class ReferenceSource(BaseModel):
    title: str
    source: str
    url: str


class SubmarineBenchmarkTarget(BaseModel):
    metric_id: str
    quantity: str
    summary_zh: str
    reference_value: float
    relative_tolerance: float
    inlet_velocity_mps: float | None = None
    velocity_tolerance_mps: float = 0.05
    on_miss_status: Literal["warning", "blocked"] = "blocked"
    source_label: str | None = None
    source_url: str | None = None


class SubmarineScientificVerificationRequirement(BaseModel):
    requirement_id: str
    label: str
    summary_zh: str
    check_type: Literal[
        "artifact_presence",
        "max_final_residual",
        "force_coefficient_tail_stability",
    ]
    required_artifacts: list[str] = Field(default_factory=list)
    force_coefficient: str | None = None
    minimum_history_samples: int | None = None
    max_tail_relative_spread: float | None = None
    max_value: float | None = None


class SubmarineScientificStudyVariant(BaseModel):
    study_type: SubmarineScientificStudyType
    variant_id: str
    variant_label: str
    parameter_overrides: dict[str, float | int | str] = Field(default_factory=dict)
    rationale: str


class SubmarineScientificStudyDefinition(BaseModel):
    study_type: SubmarineScientificStudyType
    summary_label: str
    monitored_quantity: str
    pass_fail_tolerance: float
    variants: list[SubmarineScientificStudyVariant] = Field(default_factory=list)


class SubmarineScientificStudyManifest(BaseModel):
    selected_case_id: str
    baseline_configuration_snapshot: dict[str, object] = Field(default_factory=dict)
    study_definitions: list[SubmarineScientificStudyDefinition] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)
    study_execution_status: Literal["planned", "in_progress", "completed", "blocked"] = "planned"


class SubmarineScientificStudyResult(BaseModel):
    study_type: SubmarineScientificStudyType
    monitored_quantity: str
    baseline_value: float | None = None
    compared_values: list[dict[str, object]] = Field(default_factory=list)
    relative_spread: float | None = None
    status: Literal["passed", "blocked", "missing_evidence"]
    summary_zh: str


class SubmarineCaseAcceptanceProfile(BaseModel):
    profile_id: str
    summary_zh: str
    require_solver_completed: bool = True
    require_mesh_ok: bool = True
    require_force_coefficients: bool = True
    minimum_completed_fraction_of_planned_time: float | None = None
    max_final_residual: float | None = None
    required_artifacts: list[str] = Field(default_factory=list)
    benchmark_targets: list[SubmarineBenchmarkTarget] = Field(default_factory=list)
    scientific_verification_requirements: list[
        SubmarineScientificVerificationRequirement
    ] = Field(default_factory=list)


class SubmarineCase(BaseModel):
    case_id: str
    title: str
    geometry_family: str
    geometry_description: str
    task_type: str
    condition_tags: list[str] = Field(default_factory=list)
    input_requirements: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    recommended_solver: str | None = None
    mesh_strategy: str | None = None
    bc_strategy: str | None = None
    postprocess_steps: list[str] = Field(default_factory=list)
    validation_targets: list[str] = Field(default_factory=list)
    reference_sources: list[ReferenceSource] = Field(default_factory=list)
    reuse_role: str | None = None
    linked_skills: list[str] = Field(default_factory=list)
    acceptance_profile: SubmarineCaseAcceptanceProfile | None = None


class SubmarineSkillDefinition(BaseModel):
    skill_id: str
    name: str
    version: str
    category: str
    task_types: list[str] = Field(default_factory=list)
    geometry_families: list[str] = Field(default_factory=list)
    condition_tags: list[str] = Field(default_factory=list)
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    required_tools: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    artifacts_out: list[str] = Field(default_factory=list)
    linked_cases: list[str] = Field(default_factory=list)
    validation_role: str | None = None
    owner: str | None = None


class SubmarineCaseLibrary(BaseModel):
    cases: list[SubmarineCase]
    case_index: dict[str, SubmarineCase]
    geometry_families: list[str]
    task_types: list[str]


class SubmarineSkillRegistry(BaseModel):
    skills: list[SubmarineSkillDefinition]
    skill_index: dict[str, SubmarineSkillDefinition]


class SubmarineCaseMatch(BaseModel):
    case_id: str
    title: str
    geometry_family: str
    task_type: str
    score: float
    rationale: str
    recommended_solver: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    linked_skills: list[str] = Field(default_factory=list)


class GeometryBoundingBox(BaseModel):
    min_x: float = 0.0
    max_x: float = 0.0
    min_y: float = 0.0
    max_y: float = 0.0
    min_z: float = 0.0
    max_z: float = 0.0


class GeometryInspection(BaseModel):
    file_name: str
    file_size_bytes: int
    input_format: str
    geometry_family: str
    source_application: str | None = None
    parasolid_key: str | None = None
    estimated_length_m: float | None = None
    triangle_count: int | None = None
    bounding_box: GeometryBoundingBox | None = None
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, str | None] = Field(default_factory=dict)


class SubmarineRoleBoundary(BaseModel):
    role_id: str
    title: str
    responsibility: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)


class SubmarineGeometryCheckResult(BaseModel):
    geometry: GeometryInspection
    candidate_cases: list[SubmarineCaseMatch] = Field(default_factory=list)
    summary_zh: str
    suggested_roles: list[SubmarineRoleBoundary] = Field(default_factory=list)
    review_status: Literal["ready_for_supervisor", "needs_user_confirmation", "blocked"] = "ready_for_supervisor"
    next_recommended_stage: str = "geometry-preflight"
    report_virtual_path: str = ""
    artifact_virtual_paths: list[str] = Field(default_factory=list)
