"""Figure-delivery contracts for deterministic submarine postprocess exports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, Field


FigureRenderStatus = Literal["rendered", "skipped", "blocked"]


class SubmarineFigureItem(BaseModel):
    figure_id: str
    output_id: str
    title: str
    caption: str
    render_status: FigureRenderStatus
    field: str | None = None
    selector_summary: str | None = None
    axes: list[str] = Field(default_factory=list)
    color_metric: str | None = None
    sample_count: int | None = None
    value_range: dict[str, float] | None = None
    source_csv_virtual_path: str | None = None
    artifact_virtual_paths: list[str] = Field(default_factory=list)


class SubmarineFigureManifest(BaseModel):
    run_dir_name: str
    figure_count: int
    figures: list[SubmarineFigureItem] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)


def _as_mapping(value: object | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _as_string_list(value: object | None) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def build_figure_manifest(
    *,
    run_dir_name: str,
    figures: list[SubmarineFigureItem | Mapping[str, Any] | dict[str, Any]] | None,
) -> dict[str, Any]:
    normalized_figures = [
        SubmarineFigureItem.model_validate(item).model_dump(mode="json")
        for item in (figures or [])
    ]
    artifact_virtual_paths: list[str] = []
    for item in normalized_figures:
        for path in _as_string_list(_as_mapping(item).get("artifact_virtual_paths")):
            if path not in artifact_virtual_paths:
                artifact_virtual_paths.append(path)

    manifest = SubmarineFigureManifest(
        run_dir_name=run_dir_name,
        figure_count=len(normalized_figures),
        figures=normalized_figures,
        artifact_virtual_paths=artifact_virtual_paths,
    )
    return manifest.model_dump(mode="json")


def build_figure_delivery_summary(
    *,
    manifest: object | None,
    manifest_virtual_path: str | None,
) -> dict[str, Any] | None:
    manifest_mapping = _as_mapping(manifest)
    if not manifest_mapping:
        return None

    figures = [
        _as_mapping(item)
        for item in manifest_mapping.get("figures") or []
        if isinstance(item, Mapping) or hasattr(item, "model_dump")
    ]
    return {
        "figure_count": len(figures),
        "manifest_virtual_path": manifest_virtual_path,
        "artifact_virtual_paths": _as_string_list(
            manifest_mapping.get("artifact_virtual_paths")
        )
        or ([manifest_virtual_path] if manifest_virtual_path else []),
        "figures": [
            {
                "figure_id": str(item.get("figure_id") or "unknown"),
                "output_id": str(item.get("output_id") or "unknown"),
                "title": str(item.get("title") or "--"),
                "caption": str(item.get("caption") or "--"),
                "render_status": str(item.get("render_status") or "--"),
                "selector_summary": str(item.get("selector_summary") or "--"),
                "field": str(item.get("field") or "--"),
            }
            for item in figures
        ],
    }
