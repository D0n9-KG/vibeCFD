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
    if payload is None:
        raise ValueError(
            f"Scientific remediation handoff artifact is unreadable: {artifact_virtual_path}"
        )
    return payload


def build_scientific_remediation_handoff(
    *,
    snapshot: object | None,
    scientific_remediation_summary: object | None,
    artifact_virtual_paths: list[str] | None = None,
) -> dict[str, Any]:
    runtime_snapshot = _as_mapping(snapshot)
    remediation = _as_mapping(scientific_remediation_summary)
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
        if action_id == "execute-scientific-studies":
            tool_name = "submarine_solver_dispatch"
            tool_args = {
                "geometry_path": runtime_snapshot.get("geometry_virtual_path"),
                "task_description": runtime_snapshot.get("task_summary"),
                "task_type": runtime_snapshot.get("task_type"),
                "selected_case_id": runtime_snapshot.get("selected_case_id"),
                "execute_scientific_studies": True,
            }
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
            "reason": action.get("evidence_gap")
            or action.get("summary")
            or "An auto-executable remediation step is available.",
            "artifact_virtual_paths": artifact_virtual_paths or [],
            "manual_actions": manual_actions,
        }

    if manual_actions:
        return {
            "handoff_status": "manual_followup_required",
            "recommended_action_id": manual_actions[0].get("action_id"),
            "tool_name": None,
            "tool_args": None,
            "reason": manual_actions[0].get("evidence_gap")
            or "Manual remediation input is still required.",
            "artifact_virtual_paths": artifact_virtual_paths or [],
            "manual_actions": manual_actions,
        }

    return {
        "handoff_status": "manual_followup_required",
        "recommended_action_id": None,
        "tool_name": None,
        "tool_args": None,
        "reason": "Remediation review is still required before the next tool call.",
        "artifact_virtual_paths": artifact_virtual_paths or [],
        "manual_actions": [],
    }
