"""Scientific follow-up history helpers for submarine runtime flows."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _as_string_list(values: object | None) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item) for item in values if isinstance(item, str) and item]


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
        "handoff_status": str(entry.get("handoff_status") or "unknown"),
        "recommended_action_id": (
            str(entry.get("recommended_action_id"))
            if entry.get("recommended_action_id") is not None
            else None
        ),
        "tool_name": (
            str(entry.get("tool_name")) if entry.get("tool_name") is not None else None
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
        "result_supervisor_handoff_virtual_path": (
            str(entry.get("result_supervisor_handoff_virtual_path"))
            if entry.get("result_supervisor_handoff_virtual_path")
            else None
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
