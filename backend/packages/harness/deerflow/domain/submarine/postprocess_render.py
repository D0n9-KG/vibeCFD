"""Render helpers for deterministic submarine postprocess exports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .postprocess_specs import resolve_requested_postprocess_spec, selector_summary


def summarize_delimited_file(path: Path) -> tuple[list[str], int]:
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not lines:
        return [], 0

    header = (
        [token.strip() for token in lines[0].split(",")]
        if "," in lines[0]
        else lines[0].split()
    )
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

    def _lerp_color(
        start: tuple[int, int, int],
        end: tuple[int, int, int],
        fraction: float,
    ) -> tuple[int, int, int]:
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


def _render_surface_pressure_png(
    csv_path: Path,
    png_path: Path,
    requested_output: dict | None,
) -> bool:
    spec = resolve_requested_postprocess_spec(
        "surface_pressure_contour",
        requested_output,
    )
    rows = _read_delimited_rows(csv_path)
    field = str(spec.get("field") or "p")
    x_axis, y_axis = _extract_projection_axes(rows)
    x_values, y_values, color_values = _extract_numeric_points(
        rows,
        x_key=x_axis,
        y_key=y_axis,
        color_getter=lambda row: row.get(field, ""),
    )
    return _render_scatter_png(
        x_values=x_values,
        y_values=y_values,
        color_values=color_values,
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


def _vector3(
    value: object | None,
    default: tuple[float, float, float],
) -> tuple[float, float, float]:
    if (
        isinstance(value, list | tuple)
        and len(value) == 3
        and all(isinstance(component, (int, float)) for component in value)
    ):
        return (float(value[0]), float(value[1]), float(value[2]))
    return default


def _render_wake_velocity_slice_png(
    csv_path: Path,
    png_path: Path,
    requested_output: dict | None,
) -> bool:
    spec = resolve_requested_postprocess_spec("wake_velocity_slice", requested_output)
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


def render_requested_postprocess_png(
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


def _figure_metric_metadata(
    output_id: str,
    rows: list[dict[str, str]],
    requested_output: dict | None,
) -> tuple[list[str], str | None, str | None, list[float]]:
    spec = resolve_requested_postprocess_spec(output_id, requested_output)
    if output_id == "surface_pressure_contour":
        field = str(spec.get("field") or "p")
        x_axis, y_axis = _extract_projection_axes(rows)
        _, _, color_values = _extract_numeric_points(
            rows,
            x_key=x_axis,
            y_key=y_axis,
            color_getter=lambda row: row.get(field, ""),
        )
        return [x_axis, y_axis], field, field, color_values

    if output_id == "wake_velocity_slice":
        selector = spec.get("selector") or {}
        normal = _vector3(selector.get("normal"), (1.0, 0.0, 0.0))
        x_axis, y_axis = _wake_plane_axes(normal)
        field = str(spec.get("field") or "U")
        _, _, color_values = _extract_numeric_points(
            rows,
            x_key=x_axis,
            y_key=y_axis,
            color_getter=_wake_color_getter(field),
        )
        color_metric = "|U|" if field == "U" else field
        return [x_axis, y_axis], field, color_metric, color_values

    return [], None, None, []


def _value_range(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }


def _figure_caption(
    *,
    output_id: str,
    requested_output: dict | None,
    color_metric: str | None,
    sample_count: int,
) -> str:
    selector_text = selector_summary(output_id, requested_output)
    metric = color_metric or "scalar"
    if output_id == "surface_pressure_contour":
        return (
            "Surface pressure contour over the selected hull patches, "
            f"colored by {metric}. {selector_text}. Samples: {sample_count}."
        )
    if output_id == "wake_velocity_slice":
        return (
            "Wake velocity slice extracted from the requested cutting plane, "
            f"colored by {metric}. {selector_text}. Samples: {sample_count}."
        )
    return f"Deterministic figure export colored by {metric}. Samples: {sample_count}."


def build_figure_item(
    *,
    output_id: str,
    export_spec: dict[str, str | tuple[str, ...]],
    run_dir_name: str,
    csv_path: Path,
    csv_virtual_path: str,
    markdown_virtual_path: str,
    image_virtual_path: str | None,
    requested_output: dict | None,
    render_status: str,
) -> dict[str, Any]:
    rows = _read_delimited_rows(csv_path)
    axes, field, color_metric, color_values = _figure_metric_metadata(
        output_id,
        rows,
        requested_output,
    )
    artifact_virtual_paths = [csv_virtual_path, markdown_virtual_path]
    if image_virtual_path:
        artifact_virtual_paths.append(image_virtual_path)
    sample_count = len(color_values)
    return {
        "figure_id": f"{run_dir_name}:{output_id}",
        "output_id": output_id,
        "title": str(export_spec["title"]),
        "caption": _figure_caption(
            output_id=output_id,
            requested_output=requested_output,
            color_metric=color_metric,
            sample_count=sample_count,
        ),
        "render_status": render_status,
        "field": field,
        "selector_summary": selector_summary(output_id, requested_output),
        "axes": axes,
        "color_metric": color_metric,
        "sample_count": sample_count,
        "value_range": _value_range(color_values),
        "source_csv_virtual_path": csv_virtual_path,
        "artifact_virtual_paths": artifact_virtual_paths,
    }


def render_postprocess_export_markdown(
    *,
    export_spec: dict[str, str | tuple[str, ...]],
    header: list[str],
    data_row_count: int,
    source_path: Path | None = None,
    artifact_virtual_path: str | None = None,
    png_virtual_path: str | None = None,
) -> str:
    lines = [
        f"# {export_spec['title']}",
        "",
        str(export_spec["summary"]),
        "",
    ]
    if source_path is not None:
        lines.append(f"- Source postprocess file: `{source_path.as_posix()}`")
    if artifact_virtual_path:
        lines.append(f"- Stable CSV artifact: `{artifact_virtual_path}`")
    lines.append(f"- Data row count: `{data_row_count}`")
    if png_virtual_path:
        lines.append(f"- Preview PNG artifact: `{png_virtual_path}`")
    if header:
        lines.append(f"- Columns: `{', '.join(header)}`")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "build_figure_item",
    "render_postprocess_export_markdown",
    "render_requested_postprocess_png",
    "summarize_delimited_file",
]
