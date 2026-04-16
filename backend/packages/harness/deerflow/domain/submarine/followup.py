"""Scientific follow-up history helpers for submarine runtime flows."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_FOLLOWUP_KINDS = {
    "evidence_supplement",
    "parameter_correction",
    "study_extension",
    "task_complete",
}


def _as_string_list(values: object | None) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item) for item in values if isinstance(item, str) and item]


def _optional_string(value: object | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    return value or None


def _normalize_followup_kind(value: object | None) -> str | None:
    candidate = _optional_string(value)
    if candidate in _FOLLOWUP_KINDS:
        return candidate
    return None


def _normalize_task_completion_status(
    value: object | None,
    *,
    followup_kind: str | None,
) -> str:
    candidate = _optional_string(value)
    if candidate:
        return candidate
    if followup_kind == "task_complete":
        return "completed"
    if followup_kind:
        return "continued"
    return "unknown"


def _merge_string_lists(*values: object) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _as_string_list(value):
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
    return merged


def resolve_scientific_followup_history_virtual_path(
    *virtual_paths: str | None,
) -> str | None:
    prefix = "/mnt/user-data/outputs/submarine/reports/"
    for virtual_path in virtual_paths:
        if not virtual_path or not isinstance(virtual_path, str):
            continue
        if not virtual_path.startswith(prefix):
            continue
        relative_parts = [
            part for part in virtual_path.removeprefix(prefix).split("/") if part
        ]
        if len(relative_parts) < 2:
            continue
        return f"{prefix}{relative_parts[0]}/scientific-followup-history.json"
    return None


def load_scientific_followup_history(
    *,
    artifact_path: Path,
    artifact_virtual_path: str,
) -> dict[str, Any]:
    if not artifact_path.exists():
        raise ValueError(
            f"Scientific follow-up history artifact was not found: {artifact_virtual_path}"
        )

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Scientific follow-up history artifact is unreadable: {artifact_virtual_path}"
        ) from exc

    if not isinstance(payload, Mapping):
        raise ValueError(
            f"Scientific follow-up history artifact must contain a JSON object: {artifact_virtual_path}"
        )
    return dict(payload)


def append_scientific_followup_history(
    *,
    artifact_path: Path,
    artifact_virtual_path: str,
    entry: Mapping[str, Any],
) -> dict[str, Any]:
    if artifact_path.exists():
        existing_payload = load_scientific_followup_history(
            artifact_path=artifact_path,
            artifact_virtual_path=artifact_virtual_path,
        )
        existing_entries = existing_payload.get("entries")
        if isinstance(existing_entries, list):
            entries = [
                dict(item) for item in existing_entries if isinstance(item, Mapping)
            ]
        else:
            entries = []
    else:
        entries = []

    sequence_index = len(entries) + 1
    followup_kind = _normalize_followup_kind(entry.get("followup_kind"))
    normalized_entry = {
        "entry_id": f"scientific-followup-{sequence_index:04d}",
        "sequence_index": sequence_index,
        "source_handoff_virtual_path": (
            str(entry.get("source_handoff_virtual_path"))
            if entry.get("source_handoff_virtual_path")
            else None
        ),
        "source_report_virtual_path": (
            str(entry.get("source_report_virtual_path"))
            if entry.get("source_report_virtual_path")
            else None
        ),
        "source_run_id": _optional_string(entry.get("source_run_id")),
        "baseline_reference_run_id": _optional_string(
            entry.get("baseline_reference_run_id")
        ),
        "compare_target_run_id": _optional_string(
            entry.get("compare_target_run_id")
        ),
        "derived_run_ids": _as_string_list(entry.get("derived_run_ids")),
        "handoff_status": str(entry.get("handoff_status") or "unknown"),
        "recommended_action_id": (
            str(entry.get("recommended_action_id"))
            if entry.get("recommended_action_id") is not None
            else None
        ),
        "tool_name": (
            str(entry.get("tool_name")) if entry.get("tool_name") is not None else None
        ),
        "followup_kind": followup_kind,
        "decision_summary_zh": _optional_string(entry.get("decision_summary_zh")),
        "source_conclusion_ids": _as_string_list(entry.get("source_conclusion_ids")),
        "source_evidence_gap_ids": _as_string_list(
            entry.get("source_evidence_gap_ids")
        ),
        "outcome_status": str(entry.get("outcome_status") or "unknown"),
        "dispatch_stage_status": (
            str(entry.get("dispatch_stage_status"))
            if entry.get("dispatch_stage_status") is not None
            else None
        ),
        "report_refreshed": bool(entry.get("report_refreshed")),
        "result_report_virtual_path": (
            str(entry.get("result_report_virtual_path"))
            if entry.get("result_report_virtual_path")
            else None
        ),
        "result_provenance_manifest_virtual_path": (
            str(entry.get("result_provenance_manifest_virtual_path"))
            if entry.get("result_provenance_manifest_virtual_path")
            else None
        ),
        "result_supervisor_handoff_virtual_path": (
            str(entry.get("result_supervisor_handoff_virtual_path"))
            if entry.get("result_supervisor_handoff_virtual_path")
            else None
        ),
        "task_completion_status": _normalize_task_completion_status(
            entry.get("task_completion_status"),
            followup_kind=followup_kind,
        ),
        "artifact_virtual_paths": _as_string_list(entry.get("artifact_virtual_paths")),
        "notes": _as_string_list(entry.get("notes")),
    }
    entries.append(normalized_entry)

    payload = {
        "history_version": "v1",
        "entry_count": len(entries),
        "latest_entry_id": normalized_entry["entry_id"],
        "artifact_virtual_paths": [artifact_virtual_path],
        "entries": entries,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def build_scientific_followup_summary(
    *,
    history: Mapping[str, Any],
    history_virtual_path: str,
) -> dict[str, Any] | None:
    entries = [
        dict(item) for item in history.get("entries", []) if isinstance(item, Mapping)
    ]
    if not entries:
        return None

    latest_entry = entries[-1]
    return {
        "history_virtual_path": history_virtual_path,
        "entry_count": len(entries),
        "latest_entry_id": latest_entry.get("entry_id"),
        "latest_outcome_status": latest_entry.get("outcome_status"),
        "latest_handoff_status": latest_entry.get("handoff_status"),
        "latest_source_run_id": latest_entry.get("source_run_id"),
        "latest_baseline_reference_run_id": latest_entry.get(
            "baseline_reference_run_id"
        ),
        "latest_compare_target_run_id": latest_entry.get("compare_target_run_id"),
        "latest_derived_run_ids": _as_string_list(latest_entry.get("derived_run_ids")),
        "latest_recommended_action_id": latest_entry.get("recommended_action_id"),
        "latest_tool_name": latest_entry.get("tool_name"),
        "latest_followup_kind": latest_entry.get("followup_kind"),
        "latest_decision_summary_zh": latest_entry.get("decision_summary_zh"),
        "latest_source_conclusion_ids": _as_string_list(
            latest_entry.get("source_conclusion_ids")
        ),
        "latest_source_evidence_gap_ids": _as_string_list(
            latest_entry.get("source_evidence_gap_ids")
        ),
        "latest_dispatch_stage_status": latest_entry.get("dispatch_stage_status"),
        "report_refreshed": bool(latest_entry.get("report_refreshed")),
        "latest_result_report_virtual_path": latest_entry.get(
            "result_report_virtual_path"
        ),
        "latest_result_provenance_manifest_virtual_path": latest_entry.get(
            "result_provenance_manifest_virtual_path"
        ),
        "latest_result_supervisor_handoff_virtual_path": latest_entry.get(
            "result_supervisor_handoff_virtual_path"
        ),
        "latest_notes": _as_string_list(latest_entry.get("notes")),
        "artifact_virtual_paths": _merge_string_lists(
            history.get("artifact_virtual_paths"),
            latest_entry.get("artifact_virtual_paths"),
            [latest_entry.get("result_provenance_manifest_virtual_path")],
            [history_virtual_path],
        ),
    }
