"""Supervisor handoff helpers for remediation-aware submarine reporting."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .artifact_store import read_json_mapping, resolve_outputs_artifact


def _as_mapping(value: object | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _as_dict_list(value: object | None) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _as_string_list(value: object | None) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


_VALID_SCIENTIFIC_HANDOFF_STATUSES = frozenset(
    {
        "ready_for_auto_followup",
        "manual_followup_required",
        "not_needed",
    }
)


def _looks_like_scientific_remediation_handoff(payload: Mapping[str, Any]) -> bool:
    handoff_status = payload.get("handoff_status")
    if not isinstance(handoff_status, str):
        return False
    if handoff_status not in _VALID_SCIENTIFIC_HANDOFF_STATUSES:
        return False

    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        return False

    recommended_action_id = payload.get("recommended_action_id")
    if recommended_action_id is not None and not isinstance(
        recommended_action_id, str
    ):
        return False

    tool_name = payload.get("tool_name")
    if tool_name is not None and not isinstance(tool_name, str):
        return False

    tool_args = payload.get("tool_args")
    if tool_args is not None and not isinstance(tool_args, Mapping):
        return False

    manual_actions = payload.get("manual_actions")
    if not isinstance(manual_actions, list):
        return False

    artifact_virtual_paths = payload.get("artifact_virtual_paths")
    if not isinstance(artifact_virtual_paths, list):
        return False

    return True


def _resolve_lineage_context(
    *,
    runtime_snapshot: Mapping[str, Any],
    experiment_summary: Mapping[str, Any],
    experiment_compare_summary: Mapping[str, Any],
    recommended_action_id: str | None = None,
) -> dict[str, Any]:
    variant_policy = runtime_snapshot.get("variant_policy")
    if isinstance(variant_policy, Mapping):
        default_compare_target_run_id = variant_policy.get(
            "default_compare_target_run_id"
        )
    else:
        default_compare_target_run_id = None

    baseline_reference_run_id = (
        experiment_compare_summary.get("baseline_run_id")
        or experiment_summary.get("baseline_run_id")
        or default_compare_target_run_id
    )
    compare_target_run_id = default_compare_target_run_id or baseline_reference_run_id
    derived_run_ids = _as_string_list(experiment_summary.get("recorded_variant_run_ids"))
    if not derived_run_ids:
        derived_run_ids = [
            str(item.get("candidate_run_id"))
            for item in _as_dict_list(experiment_compare_summary.get("comparisons"))
            if item.get("candidate_run_id")
        ]
    if recommended_action_id == "rerun-current-baseline":
        source_run_id = baseline_reference_run_id
    else:
        source_run_id = derived_run_ids[-1] if derived_run_ids else compare_target_run_id
    return {
        "source_run_id": source_run_id,
        "baseline_reference_run_id": baseline_reference_run_id,
        "compare_target_run_id": compare_target_run_id,
        "derived_run_ids": derived_run_ids,
    }


def _build_solver_dispatch_tool_args(
    *,
    runtime_snapshot: Mapping[str, Any],
    execute_scientific_studies: bool,
) -> dict[str, Any]:
    tool_args = {
        "geometry_path": runtime_snapshot.get("geometry_virtual_path"),
        "task_description": runtime_snapshot.get("task_summary"),
        "task_type": runtime_snapshot.get("task_type"),
        "selected_case_id": runtime_snapshot.get("selected_case_id"),
        "execute_scientific_studies": execute_scientific_studies,
        "contract_revision": runtime_snapshot.get("contract_revision"),
        "iteration_mode": runtime_snapshot.get("iteration_mode"),
        "revision_summary": runtime_snapshot.get("revision_summary"),
    }
    confirmation_status = runtime_snapshot.get("confirmation_status")
    execution_preference = runtime_snapshot.get("execution_preference")
    if confirmation_status:
        tool_args["confirmation_status"] = confirmation_status
    if execution_preference:
        tool_args["execution_preference"] = execution_preference
    simulation_requirements = runtime_snapshot.get("simulation_requirements") or {}
    if isinstance(simulation_requirements, Mapping):
        tool_args.update(
            {
                "inlet_velocity_mps": simulation_requirements.get("inlet_velocity_mps"),
                "fluid_density_kg_m3": simulation_requirements.get(
                    "fluid_density_kg_m3"
                ),
                "kinematic_viscosity_m2ps": simulation_requirements.get(
                    "kinematic_viscosity_m2ps"
                ),
                "end_time_seconds": simulation_requirements.get("end_time_seconds"),
                "delta_t_seconds": simulation_requirements.get("delta_t_seconds"),
                "write_interval_steps": simulation_requirements.get(
                    "write_interval_steps"
                ),
            }
        )
    return tool_args


def load_scientific_remediation_handoff(
    *,
    outputs_dir: Path,
    artifact_virtual_path: str,
) -> dict[str, Any]:
    local_path = resolve_outputs_artifact(outputs_dir, artifact_virtual_path)
    if local_path is None:
        raise ValueError(
            f"Scientific remediation handoff path must stay inside outputs: {artifact_virtual_path}"
        )
    if not local_path.exists():
        raise ValueError(
            f"Scientific remediation handoff artifact was not found: {artifact_virtual_path}"
        )

    payload = read_json_mapping(local_path)
    if payload is None or not _looks_like_scientific_remediation_handoff(payload):
        raise ValueError(
            f"Scientific remediation handoff artifact is unreadable: {artifact_virtual_path}"
        )
    return payload


def build_scientific_remediation_handoff(
    *,
    snapshot: object | None,
    scientific_remediation_summary: object | None,
    experiment_summary: object | None = None,
    experiment_compare_summary: object | None = None,
    artifact_virtual_paths: list[str] | None = None,
) -> dict[str, Any]:
    runtime_snapshot = _as_mapping(snapshot)
    remediation = _as_mapping(scientific_remediation_summary)
    experiment_summary_mapping = _as_mapping(experiment_summary)
    experiment_compare_summary_mapping = _as_mapping(experiment_compare_summary)
    actions = _as_dict_list(remediation.get("actions"))
    auto_actions = [
        item for item in actions if str(item.get("execution_mode") or "") == "auto_executable"
    ]
    manual_actions = [
        item
        for item in actions
        if str(item.get("execution_mode") or "") == "manual_required"
    ]

    if str(remediation.get("plan_status") or "") == "not_needed":
        return {
            "handoff_status": "not_needed",
            "recommended_action_id": None,
            "tool_name": None,
            "tool_args": None,
            "reason": "Scientific remediation is not needed for this run.",
            "artifact_virtual_paths": artifact_virtual_paths or [],
            "manual_actions": [],
        }

    if auto_actions:
        action = auto_actions[0]
        action_id = str(action.get("action_id") or "")
        lineage_context = _resolve_lineage_context(
            runtime_snapshot=runtime_snapshot,
            experiment_summary=experiment_summary_mapping,
            experiment_compare_summary=experiment_compare_summary_mapping,
            recommended_action_id=action_id,
        )
        if action_id == "execute-scientific-studies":
            tool_name = "submarine_solver_dispatch"
            tool_args = _build_solver_dispatch_tool_args(
                runtime_snapshot=runtime_snapshot,
                execute_scientific_studies=True,
            )
        elif action_id == "rerun-current-baseline":
            tool_name = "submarine_solver_dispatch"
            tool_args = _build_solver_dispatch_tool_args(
                runtime_snapshot=runtime_snapshot,
                execute_scientific_studies=False,
            )
        elif action_id == "regenerate-research-report-linkage":
            tool_name = "submarine_result_report"
            tool_args = {}
        else:
            tool_name = None
            tool_args = None

        return {
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": action.get("action_id"),
            "tool_name": tool_name,
            "tool_args": tool_args,
            **lineage_context,
            "reason": action.get("evidence_gap")
            or action.get("summary")
            or "An auto-executable remediation step is available.",
            "artifact_virtual_paths": artifact_virtual_paths or [],
            "manual_actions": manual_actions,
        }

    if manual_actions:
        lineage_context = _resolve_lineage_context(
            runtime_snapshot=runtime_snapshot,
            experiment_summary=experiment_summary_mapping,
            experiment_compare_summary=experiment_compare_summary_mapping,
        )
        return {
            "handoff_status": "manual_followup_required",
            "recommended_action_id": manual_actions[0].get("action_id"),
            "tool_name": None,
            "tool_args": None,
            **lineage_context,
            "reason": manual_actions[0].get("evidence_gap")
            or "Manual remediation input is still required.",
            "artifact_virtual_paths": artifact_virtual_paths or [],
            "manual_actions": manual_actions,
        }

    lineage_context = _resolve_lineage_context(
        runtime_snapshot=runtime_snapshot,
        experiment_summary=experiment_summary_mapping,
        experiment_compare_summary=experiment_compare_summary_mapping,
    )
    return {
        "handoff_status": "manual_followup_required",
        "recommended_action_id": None,
        "tool_name": None,
        "tool_args": None,
        **lineage_context,
        "reason": "Remediation review is still required before the next tool call.",
        "artifact_virtual_paths": artifact_virtual_paths or [],
        "manual_actions": [],
    }
