import json
from collections.abc import Mapping
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


_EXECUTION_PLAN_STATUS_ORDER = {
    "pending": 0,
    "ready": 1,
    "in_progress": 2,
    "completed": 3,
    "blocked": 4,
}


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


def _merge_string_list(existing: list[str] | None, new: list[str] | None) -> list[str]:
    merged: list[str] = []
    for value in (existing or []) + (new or []):
        if isinstance(value, str) and value not in merged:
            merged.append(value)
    return merged


def _merge_unique_dict_list(existing: list[dict] | None, new: list[dict] | None) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for item in (existing or []) + (new or []):
        if not isinstance(item, dict):
            continue
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False, default=str)
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(dict(item))
    if all(isinstance(item.get("timestamp"), str) for item in merged):
        merged.sort(key=lambda item: str(item.get("timestamp")))
    return merged


def _prefer_execution_plan_status(existing: object, new: object) -> object:
    if not isinstance(existing, str):
        return new
    if not isinstance(new, str):
        return existing
    existing_rank = _EXECUTION_PLAN_STATUS_ORDER.get(existing, -1)
    new_rank = _EXECUTION_PLAN_STATUS_ORDER.get(new, -1)
    return existing if existing_rank >= new_rank else new


def _merge_keyed_dict_list(
    existing: list[dict] | None,
    new: list[dict] | None,
    *,
    id_key: str,
) -> list[dict]:
    merged: list[dict] = []
    index_by_id: dict[str, int] = {}

    for item in (existing or []) + (new or []):
        if not isinstance(item, Mapping):
            continue
        identifier = item.get(id_key)
        if not isinstance(identifier, str) or not identifier:
            merged.append(dict(item))
            continue

        item_dict = dict(item)
        existing_index = index_by_id.get(identifier)
        if existing_index is None:
            index_by_id[identifier] = len(merged)
            merged.append(item_dict)
            continue

        prior = merged[existing_index]
        combined = {**prior, **item_dict}
        if "status" in prior or "status" in item_dict:
            combined["status"] = _prefer_execution_plan_status(
                prior.get("status"),
                item_dict.get("status"),
            )
        if "target_skills" in prior or "target_skills" in item_dict:
            combined["target_skills"] = _merge_string_list(
                prior.get("target_skills") if isinstance(prior.get("target_skills"), list) else None,
                item_dict.get("target_skills") if isinstance(item_dict.get("target_skills"), list) else None,
            )
        merged[existing_index] = combined

    return merged


def merge_submarine_runtime(
    existing: SubmarineRuntimeState | None,
    new: SubmarineRuntimeState | None,
) -> SubmarineRuntimeState:
    """Reducer for submarine_runtime that safely merges concurrent graph updates."""
    if existing is None:
        return dict(new or {})
    if new is None:
        return dict(existing)

    merged: SubmarineRuntimeState = dict(existing)

    for key, value in new.items():
        if key == "artifact_virtual_paths":
            merged[key] = merge_artifacts(
                merged.get(key) if isinstance(merged.get(key), list) else None,
                value if isinstance(value, list) else None,
            )
        elif key == "activity_timeline":
            merged[key] = _merge_unique_dict_list(
                merged.get(key) if isinstance(merged.get(key), list) else None,
                value if isinstance(value, list) else None,
            )
        elif key == "execution_plan":
            merged[key] = _merge_keyed_dict_list(
                merged.get(key) if isinstance(merged.get(key), list) else None,
                value if isinstance(value, list) else None,
                id_key="role_id",
            )
        elif key == "simulation_requirements" and isinstance(value, dict):
            prior_value = merged.get(key)
            merged[key] = {
                **(prior_value if isinstance(prior_value, dict) else {}),
                **value,
            }
        else:
            merged[key] = value

    return merged


class ThreadState(AgentState):
    sandbox: NotRequired[SandboxState | None]
    thread_data: NotRequired[ThreadDataState | None]
    submarine_runtime: Annotated[SubmarineRuntimeState | None, merge_submarine_runtime]
    submarine_skill_studio: NotRequired[SubmarineSkillStudioState | None]
    title: NotRequired[str | None]
    artifacts: Annotated[list[str], merge_artifacts]
    todos: NotRequired[list | None]
    uploaded_files: NotRequired[list[dict] | None]
    viewed_images: Annotated[dict[str, ViewedImageData], merge_viewed_images]  # image_path -> {base64, mime_type}
