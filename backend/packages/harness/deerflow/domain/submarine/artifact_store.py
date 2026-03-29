"""Shared outputs-artifact resolution and JSON loading helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path


_OUTPUTS_PREFIX = "/mnt/user-data/outputs/"


def resolve_outputs_artifact(outputs_dir: Path, virtual_path: str) -> Path | None:
    if not virtual_path.startswith(_OUTPUTS_PREFIX):
        return None
    relative_parts = [
        part for part in virtual_path.removeprefix(_OUTPUTS_PREFIX).split("/") if part
    ]
    return outputs_dir.joinpath(*relative_parts)


def read_json_mapping(path: Path) -> dict | None:
    if not path.exists() or path.suffix.lower() != ".json":
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def load_json_outputs_artifact(outputs_dir: Path, virtual_path: str) -> dict | None:
    local_path = resolve_outputs_artifact(outputs_dir, virtual_path)
    if local_path is None:
        return None
    return read_json_mapping(local_path)


def load_json_payloads_from_artifacts(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: Sequence[str],
    suffixes: Sequence[str],
) -> list[tuple[str, dict]]:
    payloads: list[tuple[str, dict]] = []
    for artifact_virtual_path in artifact_virtual_paths:
        if not any(artifact_virtual_path.endswith(suffix) for suffix in suffixes):
            continue
        payload = load_json_outputs_artifact(outputs_dir, artifact_virtual_path)
        if payload is not None:
            payloads.append((artifact_virtual_path, payload))
    return payloads


def load_first_json_payload_from_artifacts(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: Sequence[str],
    suffixes: Sequence[str],
) -> tuple[str, dict] | None:
    payloads = load_json_payloads_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        suffixes=suffixes,
    )
    return payloads[0] if payloads else None


__all__ = [
    "load_first_json_payload_from_artifacts",
    "load_json_outputs_artifact",
    "load_json_payloads_from_artifacts",
    "read_json_mapping",
    "resolve_outputs_artifact",
]
