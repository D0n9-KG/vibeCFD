"""Deterministic submarine CFD postprocess helpers."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Any


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


def requested_output_ids(requested_outputs: list[dict] | None) -> set[str]:
    return {
        str(item.get("output_id"))
        for item in (requested_outputs or [])
        if isinstance(item, dict) and item.get("output_id")
    }


def _requested_output_map(requested_outputs: list[dict] | None) -> dict[str, dict]:
    return {
        str(item.get("output_id")): item
        for item in (requested_outputs or [])
        if isinstance(item, dict) and item.get("output_id")
    }


def _as_float(value: Any, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _vector3(value: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if (
        isinstance(value, list | tuple)
        and len(value) == 3
        and all(isinstance(component, (int, float)) for component in value)
    ):
        return (float(value[0]), float(value[1]), float(value[2]))
    return default


def _surface_pressure_spec(requested_output: dict | None) -> dict:
    base = {
        "field": "p",
        "time_mode": "latest",
        "selector": {
            "type": "patch",
            "patches": ["hull"],
        },
        "formats": ["csv", "png", "report"],
    }
    spec = requested_output.get("postprocess_spec") if isinstance(requested_output, dict) else None
    if not isinstance(spec, dict):
        return base

    selector = spec.get("selector") if isinstance(spec.get("selector"), dict) else {}
    patches = selector.get("patches")
    resolved_patches = (
        [str(patch) for patch in patches if isinstance(patch, str)]
        if isinstance(patches, list) and patches
        else ["hull"]
    )
    return {
        "field": str(spec.get("field") or "p"),
        "time_mode": str(spec.get("time_mode") or "latest"),
        "selector": {
            "type": "patch",
            "patches": resolved_patches,
        },
        "formats": spec.get("formats")
        if isinstance(spec.get("formats"), list)
        else ["csv", "png", "report"],
    }


def _wake_velocity_slice_spec(requested_output: dict | None) -> dict:
    base = {
        "field": "U",
        "time_mode": "latest",
        "selector": {
            "type": "plane",
            "origin_mode": "x_by_lref",
            "origin_value": 1.25,
            "normal": [1.0, 0.0, 0.0],
        },
        "formats": ["csv", "png", "report"],
    }
    spec = requested_output.get("postprocess_spec") if isinstance(requested_output, dict) else None
    if not isinstance(spec, dict):
        return base

    selector = spec.get("selector") if isinstance(spec.get("selector"), dict) else {}
    origin_mode = str(selector.get("origin_mode") or "x_by_lref")
    if origin_mode not in {"x_by_lref", "x_absolute_m"}:
        origin_mode = "x_by_lref"

    normal = _vector3(selector.get("normal"), (1.0, 0.0, 0.0))
    return {
        "field": str(spec.get("field") or "U"),
        "time_mode": str(spec.get("time_mode") or "latest"),
        "selector": {
            "type": "plane",
            "origin_mode": origin_mode,
            "origin_value": _as_float(selector.get("origin_value"), 1.25),
            "normal": [normal[0], normal[1], normal[2]],
        },
        "formats": spec.get("formats")
        if isinstance(spec.get("formats"), list)
        else ["csv", "png", "report"],
    }


def render_requested_postprocess_function_objects(
    *,
    requested_outputs: list[dict] | None,
    reference_length_m: float,
) -> str:
    requested_by_id = _requested_output_map(requested_outputs)
    blocks: list[str] = []

    if "surface_pressure_contour" in requested_by_id:
        spec = _surface_pressure_spec(requested_by_id["surface_pressure_contour"])
        patch_list = " ".join(spec["selector"]["patches"])
        blocks.append(
            f"""

    surfacePressure
    {{
        type            surfaces;
        libs            ("libsampling.so");
        writeControl    timeStep;
        writeInterval   10;
        surfaceFormat   raw;
        interpolationScheme cellPoint;
        fields          ({spec["field"]});
        surfaces
        (
            hullPressure
            {{
                type        patch;
                patches     ({patch_list});
                triangulate false;
            }}
        );
    }}""".rstrip()
        )

    if "wake_velocity_slice" in requested_by_id:
        spec = _wake_velocity_slice_spec(requested_by_id["wake_velocity_slice"])
        selector = spec["selector"]
        origin_value = float(selector["origin_value"])
        if selector["origin_mode"] == "x_absolute_m":
            wake_slice_x = origin_value
        else:
            wake_slice_x = round(reference_length_m * origin_value, 6)
        normal = selector["normal"]
        blocks.append(
            f"""

    wakeVelocitySlice
    {{
        type            surfaces;
        libs            ("libsampling.so");
        writeControl    timeStep;
        writeInterval   10;
        surfaceFormat   raw;
        interpolationScheme cellPoint;
        fields          ({spec["field"]});
        surfaces
        (
            wakePlane
            {{
                type        cuttingPlane;
                planeType   pointAndNormal;
                pointAndNormalDict
                {{
                    point   ({wake_slice_x} 0 0);
                    normal  ({normal[0]} {normal[1]} {normal[2]});
                }}
                interpolate true;
            }}
        );
    }}""".rstrip()
        )

    return "".join(blocks)


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


def _find_latest_postprocess_candidate(case_dir: Path, object_name: str, filenames: list[str]) -> Path | None:
    for filename in filenames:
        candidate = _find_latest_postprocess_file(case_dir, object_name, filename)
        if candidate is not None:
            return candidate
    return None


def _summarize_delimited_file(path: Path) -> tuple[list[str], int]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return [], 0

    header = [token.strip() for token in lines[0].split(",")] if "," in lines[0] else lines[0].split()
    data_row_count = max(len(lines) - 1, 0)
    return header, data_row_count


def _read_delimited_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            cleaned = {
                (key or "").strip(): (value or "").strip()
                for key, value in row.items()
                if key
            }
            if any(value for value in cleaned.values()):
                rows.append(cleaned)
        return rows


def _float_series(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(key)
        if raw is None or raw == "":
            continue
        try:
            values.append(float(raw))
        except ValueError:
            continue
    return values


def _extract_projection_axes(rows: list[dict[str, str]]) -> tuple[str, str]:
    spans: list[tuple[float, str]] = []
    for axis in ("x", "y", "z"):
        values = _float_series(rows, axis)
        if len(values) >= 2:
            spans.append((max(values) - min(values), axis))
    if len(spans) >= 2:
        spans.sort(reverse=True)
        return spans[0][1], spans[1][1]
    if len(spans) == 1:
        remaining = next(axis for axis in ("x", "y", "z") if axis != spans[0][1])
        return spans[0][1], remaining
    return "x", "y"


def _wake_plane_axes(normal: tuple[float, float, float]) -> tuple[str, str]:
    dominant = max(
        (
            (abs(normal[0]), "x"),
            (abs(normal[1]), "y"),
            (abs(normal[2]), "z"),
        ),
        key=lambda item: item[0],
    )[1]
    if dominant == "x":
        return "y", "z"
    if dominant == "y":
        return "x", "z"
    return "x", "y"


def _extract_numeric_points(
    rows: list[dict[str, str]],
    *,
    x_key: str,
    y_key: str,
    color_getter,
) -> tuple[list[float], list[float], list[float]]:
    x_values: list[float] = []
    y_values: list[float] = []
    colors: list[float] = []
    for row in rows:
        try:
            x_value = float(row[x_key])
            y_value = float(row[y_key])
            color_value = float(color_getter(row))
        except (KeyError, TypeError, ValueError):
            continue
        x_values.append(x_value)
        y_values.append(y_value)
        colors.append(color_value)
    return x_values, y_values, colors


def _render_scatter_png(
    *,
    x_values: list[float],
    y_values: list[float],
    color_values: list[float],
    x_label: str,
    y_label: str,
    color_label: str,
    title: str,
    png_path: Path,
) -> bool:
    if not x_values or not y_values or not color_values:
        return False

    from PIL import Image, ImageDraw, ImageFont

    width = 1200
    height = 720
    margin_left = 100
    margin_right = 140
    margin_top = 70
    margin_bottom = 90
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(y_values)
    y_max = max(y_values)
    c_min = min(color_values)
    c_max = max(color_values)

    if x_min == x_max:
        x_min -= 0.5
        x_max += 0.5
    if y_min == y_max:
        y_min -= 0.5
        y_max += 0.5
    if c_min == c_max:
        c_min -= 0.5
        c_max += 0.5

    def _normalize(value: float, lower: float, upper: float) -> float:
        return max(0.0, min(1.0, (value - lower) / (upper - lower)))

    def _lerp_color(start: tuple[int, int, int], end: tuple[int, int, int], fraction: float) -> tuple[int, int, int]:
        return tuple(
            int(round(start[index] + (end[index] - start[index]) * fraction))
            for index in range(3)
        )

    def _scalar_to_rgb(value: float) -> tuple[int, int, int]:
        palette = [
            (68, 1, 84),
            (59, 82, 139),
            (33, 145, 140),
            (94, 201, 97),
            (253, 231, 37),
        ]
        normalized = _normalize(value, c_min, c_max)
        scaled = normalized * (len(palette) - 1)
        lower_index = int(scaled)
        upper_index = min(lower_index + 1, len(palette) - 1)
        fraction = scaled - lower_index
        return _lerp_color(palette[lower_index], palette[upper_index], fraction)

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    plot_left = margin_left
    plot_top = margin_top
    plot_right = margin_left + plot_width
    plot_bottom = margin_top + plot_height

    draw.rectangle(
        (plot_left, plot_top, plot_right, plot_bottom),
        outline=(120, 120, 120),
        width=1,
    )

    for x_value, y_value, color_value in zip(x_values, y_values, color_values, strict=False):
        px = plot_left + int(round(_normalize(x_value, x_min, x_max) * plot_width))
        py = plot_bottom - int(round(_normalize(y_value, y_min, y_max) * plot_height))
        color = _scalar_to_rgb(color_value)
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=color, outline=color)

    draw.text((plot_left, 20), title, fill=(0, 0, 0), font=font)
    draw.text((plot_left, height - 30), x_label, fill=(0, 0, 0), font=font)
    draw.text((20, plot_top), y_label, fill=(0, 0, 0), font=font)

    draw.text((plot_left, plot_bottom + 12), f"{x_min:.3f}", fill=(80, 80, 80), font=font)
    draw.text((plot_right - 48, plot_bottom + 12), f"{x_max:.3f}", fill=(80, 80, 80), font=font)
    draw.text((36, plot_bottom - 6), f"{y_min:.3f}", fill=(80, 80, 80), font=font)
    draw.text((36, plot_top - 6), f"{y_max:.3f}", fill=(80, 80, 80), font=font)

    colorbar_left = plot_right + 36
    colorbar_right = colorbar_left + 28
    for offset in range(plot_height):
        fraction = 1.0 - (offset / max(plot_height - 1, 1))
        value = c_min + (c_max - c_min) * fraction
        draw.line(
            (colorbar_left, plot_top + offset, colorbar_right, plot_top + offset),
            fill=_scalar_to_rgb(value),
            width=1,
        )
    draw.rectangle(
        (colorbar_left, plot_top, colorbar_right, plot_bottom),
        outline=(120, 120, 120),
        width=1,
    )
    draw.text((colorbar_left - 6, plot_top - 18), color_label, fill=(0, 0, 0), font=font)
    draw.text((colorbar_right + 10, plot_top - 4), f"{c_max:.3f}", fill=(80, 80, 80), font=font)
    draw.text((colorbar_right + 10, plot_bottom - 10), f"{c_min:.3f}", fill=(80, 80, 80), font=font)

    image.save(png_path, format="PNG")
    return True


def _render_surface_pressure_png(csv_path: Path, png_path: Path, requested_output: dict | None) -> bool:
    spec = _surface_pressure_spec(requested_output)
    rows = _read_delimited_rows(csv_path)
    field = str(spec.get("field") or "p")
    x_axis, y_axis = _extract_projection_axes(rows)
    return _render_scatter_png(
        x_values=_extract_numeric_points(
            rows,
            x_key=x_axis,
            y_key=y_axis,
            color_getter=lambda row: row.get(field, ""),
        )[0],
        y_values=_extract_numeric_points(
            rows,
            x_key=x_axis,
            y_key=y_axis,
            color_getter=lambda row: row.get(field, ""),
        )[1],
        color_values=_extract_numeric_points(
            rows,
            x_key=x_axis,
            y_key=y_axis,
            color_getter=lambda row: row.get(field, ""),
        )[2],
        x_label=x_axis,
        y_label=y_axis,
        color_label=field,
        title="Surface Pressure Preview",
        png_path=png_path,
    )


def _wake_color_getter(field: str):
    if field == "U":
        return lambda row: (
            float(row.get("Ux", "nan")) ** 2
            + float(row.get("Uy", "nan")) ** 2
            + float(row.get("Uz", "nan")) ** 2
        ) ** 0.5
    return lambda row: row.get(field, "")


def _render_wake_velocity_slice_png(
    csv_path: Path,
    png_path: Path,
    requested_output: dict | None,
) -> bool:
    spec = _wake_velocity_slice_spec(requested_output)
    rows = _read_delimited_rows(csv_path)
    selector = spec.get("selector") or {}
    normal = _vector3(selector.get("normal"), (1.0, 0.0, 0.0))
    x_axis, y_axis = _wake_plane_axes(normal)
    field = str(spec.get("field") or "U")
    color_getter = _wake_color_getter(field)
    x_values, y_values, color_values = _extract_numeric_points(
        rows,
        x_key=x_axis,
        y_key=y_axis,
        color_getter=color_getter,
    )
    color_label = "|U|" if field == "U" else field
    return _render_scatter_png(
        x_values=x_values,
        y_values=y_values,
        color_values=color_values,
        x_label=x_axis,
        y_label=y_axis,
        color_label=color_label,
        title="Wake Velocity Slice Preview",
        png_path=png_path,
    )


def _requested_output_formats(output_id: str, requested_output: dict | None) -> set[str]:
    if output_id == "surface_pressure_contour":
        spec = _surface_pressure_spec(requested_output)
    elif output_id == "wake_velocity_slice":
        spec = _wake_velocity_slice_spec(requested_output)
    else:
        spec = {"formats": ["csv", "report"]}
    return {
        str(item).strip().lower()
        for item in spec.get("formats", [])
        if isinstance(item, str) and item.strip()
    }


def _render_requested_postprocess_png(
    *,
    output_id: str,
    csv_path: Path,
    png_path: Path,
    requested_output: dict | None,
) -> bool:
    try:
        if output_id == "surface_pressure_contour":
            return _render_surface_pressure_png(csv_path, png_path, requested_output)
        if output_id == "wake_velocity_slice":
            return _render_wake_velocity_slice_png(csv_path, png_path, requested_output)
    except Exception:
        return False
    return False


def _render_postprocess_export_markdown(
    *,
    title: str,
    summary: str,
    source_path: Path,
    artifact_virtual_path: str,
    image_virtual_path: str | None,
    columns: list[str],
    data_row_count: int,
) -> str:
    lines = [
        f"# {title}",
        "",
        summary,
        "",
        f"- Source postprocess file: `{source_path.as_posix()}`",
        f"- Stable CSV artifact: `{artifact_virtual_path}`",
        f"- Data row count: `{data_row_count}`",
    ]
    if image_virtual_path:
        lines.append(f"- Preview PNG artifact: `{image_virtual_path}`")
    if columns:
        lines.append(f"- Columns: `{', '.join(columns)}`")
    lines.append("")
    return "\n".join(lines)


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
        image_virtual_path: str | None = None
        if "png" in _requested_output_formats(output_id, requested_output):
            png_name = str(export_spec["artifact_png"])
            png_path = artifact_dir / png_name
            rendered = _render_requested_postprocess_png(
                output_id=output_id,
                csv_path=csv_path,
                png_path=png_path,
                requested_output=requested_output,
            )
            if rendered:
                image_virtual_path = artifact_virtual_path_builder(run_dir_name, png_name)
                exported_artifacts.append(image_virtual_path)

        columns, data_row_count = _summarize_delimited_file(csv_path)
        write_text(
            markdown_path,
            _render_postprocess_export_markdown(
                title=str(export_spec["title"]),
                summary=str(export_spec["summary"]),
                source_path=source_path,
                artifact_virtual_path=csv_virtual_path,
                image_virtual_path=image_virtual_path,
                columns=columns,
                data_row_count=data_row_count,
            ),
        )

        exported_artifacts.extend(
            [
                csv_virtual_path,
                artifact_virtual_path_builder(run_dir_name, markdown_name),
            ]
        )

    return exported_artifacts
