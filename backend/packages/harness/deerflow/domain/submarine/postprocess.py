"""Deterministic submarine CFD postprocess orchestration."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .figure_delivery import build_figure_manifest
from .postprocess_render import (
    build_figure_item,
    render_postprocess_export_markdown,
    render_requested_postprocess_png,
    summarize_delimited_file,
)
from .postprocess_specs import (
    render_requested_postprocess_function_objects,
    requested_output_formats,
    requested_output_ids,
)


_REQUESTED_POSTPROCESS_EXPORTS: dict[str, dict[str, str | tuple[str, ...]]] = {
    "surface_pressure_contour": {
        "object_name": "surfacePressure",
        "source_filenames": ("surfacePressure.csv",),
        "artifact_csv": "surface-pressure.csv",
        "artifact_png": "surface-pressure.png",
        "artifact_md": "surface-pressure.md",
        "title": "Surface Pressure Result",
        "summary": (
            "Exported surface pressure samples from OpenFOAM postProcessing. "
            "The CSV is kept for archive and the PNG is a deterministic preview."
        ),
    },
    "wake_velocity_slice": {
        "object_name": "wakeVelocitySlice",
        "source_filenames": ("wakeVelocitySlice.csv",),
        "artifact_csv": "wake-velocity-slice.csv",
        "artifact_png": "wake-velocity-slice.png",
        "artifact_md": "wake-velocity-slice.md",
        "title": "Wake Velocity Slice",
        "summary": (
            "Exported wake velocity slice samples from OpenFOAM postProcessing. "
            "The CSV is kept for archive and the PNG is a deterministic preview."
        ),
    },
}


def _requested_output_map(requested_outputs: list[dict] | None) -> dict[str, dict]:
    return {
        str(item.get("output_id")): item
        for item in (requested_outputs or [])
        if isinstance(item, dict) and item.get("output_id")
    }


def _find_latest_postprocess_file(case_dir: Path, object_name: str, filename: str) -> Path | None:
    root = case_dir / "postProcessing" / object_name
    if not root.exists():
        return None

    candidates: list[tuple[float, Path]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        target = child / filename
        if not target.exists():
            continue
        try:
            sort_key = float(child.name)
        except ValueError:
            sort_key = float("inf")
        candidates.append((sort_key, target))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def _find_latest_postprocess_candidate(
    case_dir: Path,
    object_name: str,
    filenames: list[str],
) -> Path | None:
    for filename in filenames:
        candidate = _find_latest_postprocess_file(case_dir, object_name, filename)
        if candidate is not None:
            return candidate
    return None


def collect_requested_postprocess_artifacts(
    *,
    case_dir: Path,
    artifact_dir: Path,
    run_dir_name: str,
    requested_outputs: list[dict] | None,
    artifact_virtual_path_builder,
    write_text,
) -> list[str]:
    requested_by_id = _requested_output_map(requested_outputs)
    exported_artifacts: list[str] = []
    figure_items: list[dict[str, Any]] = []

    for output_id, export_spec in _REQUESTED_POSTPROCESS_EXPORTS.items():
        requested_output = requested_by_id.get(output_id)
        if requested_output is None:
            continue

        source_path = _find_latest_postprocess_candidate(
            case_dir,
            str(export_spec["object_name"]),
            list(export_spec["source_filenames"]),
        )
        if source_path is None:
            continue

        csv_name = str(export_spec["artifact_csv"])
        markdown_name = str(export_spec["artifact_md"])
        csv_path = artifact_dir / csv_name
        markdown_path = artifact_dir / markdown_name
        shutil.copy2(source_path, csv_path)

        csv_virtual_path = artifact_virtual_path_builder(run_dir_name, csv_name)
        markdown_virtual_path = artifact_virtual_path_builder(run_dir_name, markdown_name)
        image_virtual_path: str | None = None
        render_status = "skipped"
        if "png" in requested_output_formats(output_id, requested_output):
            png_name = str(export_spec["artifact_png"])
            png_path = artifact_dir / png_name
            rendered = render_requested_postprocess_png(
                output_id=output_id,
                csv_path=csv_path,
                png_path=png_path,
                requested_output=requested_output,
            )
            if rendered:
                image_virtual_path = artifact_virtual_path_builder(run_dir_name, png_name)
                exported_artifacts.append(image_virtual_path)
                render_status = "rendered"
            else:
                render_status = "blocked"

        columns, data_row_count = summarize_delimited_file(csv_path)
        write_text(
            markdown_path,
            render_postprocess_export_markdown(
                export_spec=export_spec,
                header=columns,
                data_row_count=data_row_count,
                source_path=source_path,
                artifact_virtual_path=csv_virtual_path,
                png_virtual_path=image_virtual_path,
            ),
        )

        exported_artifacts.extend(
            [
                csv_virtual_path,
                markdown_virtual_path,
            ]
        )
        figure_items.append(
            build_figure_item(
                output_id=output_id,
                export_spec=export_spec,
                run_dir_name=run_dir_name,
                csv_path=csv_path,
                csv_virtual_path=csv_virtual_path,
                markdown_virtual_path=markdown_virtual_path,
                image_virtual_path=image_virtual_path,
                requested_output=requested_output,
                render_status=render_status,
            )
        )

    if figure_items:
        manifest_name = "figure-manifest.json"
        manifest_path = artifact_dir / manifest_name
        manifest_virtual_path = artifact_virtual_path_builder(run_dir_name, manifest_name)
        write_text(
            manifest_path,
            json.dumps(
                build_figure_manifest(
                    run_dir_name=run_dir_name,
                    figures=figure_items,
                ),
                ensure_ascii=False,
                indent=2,
            ),
        )
        exported_artifacts.append(manifest_virtual_path)

    return exported_artifacts


__all__ = [
    "collect_requested_postprocess_artifacts",
    "render_requested_postprocess_function_objects",
    "requested_output_ids",
]
