from typing import Annotated, NotRequired, TypedDict

from langchain.agents import AgentState


class SandboxState(TypedDict):
    sandbox_id: NotRequired[str | None]


class ThreadDataState(TypedDict):
    workspace_path: NotRequired[str | None]
    uploads_path: NotRequired[str | None]
    outputs_path: NotRequired[str | None]


class SubmarineRuntimeState(TypedDict):
    current_stage: NotRequired[str]
    task_summary: NotRequired[str]
    task_type: NotRequired[str]
    geometry_virtual_path: NotRequired[str]
    geometry_family: NotRequired[str | None]
    execution_readiness: NotRequired[str | None]
    selected_case_id: NotRequired[str | None]
    simulation_requirements: NotRequired[dict[str, float | int] | None]
    stage_status: NotRequired[str | None]
    workspace_case_dir_virtual_path: NotRequired[str | None]
    run_script_virtual_path: NotRequired[str | None]
    supervisor_handoff_virtual_path: NotRequired[str | None]
    scientific_followup_history_virtual_path: NotRequired[str | None]
    review_status: NotRequired[str]
    next_recommended_stage: NotRequired[str]
    report_virtual_path: NotRequired[str]
    artifact_virtual_paths: NotRequired[list[str] | None]
    execution_plan: NotRequired[list[dict] | None]
    activity_timeline: NotRequired[list[dict] | None]


class SubmarineSkillStudioState(TypedDict):
    skill_name: NotRequired[str]
    assistant_mode: NotRequired[str]
    assistant_label: NotRequired[str]
    builtin_skills: NotRequired[list[str] | None]
    validation_status: NotRequired[str]
    test_status: NotRequired[str]
    publish_status: NotRequired[str]
    error_count: NotRequired[int]
    warning_count: NotRequired[int]
    report_virtual_path: NotRequired[str]
    package_virtual_path: NotRequired[str]
    package_archive_virtual_path: NotRequired[str]
    test_virtual_path: NotRequired[str]
    publish_virtual_path: NotRequired[str]
    ui_metadata_virtual_path: NotRequired[str]
    artifact_virtual_paths: NotRequired[list[str] | None]


class ViewedImageData(TypedDict):
    base64: str
    mime_type: str


def merge_artifacts(existing: list[str] | None, new: list[str] | None) -> list[str]:
    """Reducer for artifacts list - merges and deduplicates artifacts."""
    if existing is None:
        return new or []
    if new is None:
        return existing
    # Use dict.fromkeys to deduplicate while preserving order
    return list(dict.fromkeys(existing + new))


def merge_viewed_images(existing: dict[str, ViewedImageData] | None, new: dict[str, ViewedImageData] | None) -> dict[str, ViewedImageData]:
    """Reducer for viewed_images dict - merges image dictionaries.

    Special case: If new is an empty dict {}, it clears the existing images.
    This allows middlewares to clear the viewed_images state after processing.
    """
    if existing is None:
        return new or {}
    if new is None:
        return existing
    # Special case: empty dict means clear all viewed images
    if len(new) == 0:
        return {}
    # Merge dictionaries, new values override existing ones for same keys
    return {**existing, **new}


class ThreadState(AgentState):
    sandbox: NotRequired[SandboxState | None]
    thread_data: NotRequired[ThreadDataState | None]
    submarine_runtime: NotRequired[SubmarineRuntimeState | None]
    submarine_skill_studio: NotRequired[SubmarineSkillStudioState | None]
    title: NotRequired[str | None]
    artifacts: Annotated[list[str], merge_artifacts]
    todos: NotRequired[list | None]
    uploaded_files: NotRequired[list[dict] | None]
    viewed_images: Annotated[dict[str, ViewedImageData], merge_viewed_images]  # image_path -> {base64, mime_type}
