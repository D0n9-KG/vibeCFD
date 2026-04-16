"""Requested-output spec helpers for deterministic submarine postprocess exports."""

from __future__ import annotations

from typing import Any


def requested_output_ids(requested_outputs: list[dict] | None) -> set[str]:
    return {str(item.get("output_id")) for item in (requested_outputs or []) if isinstance(item, dict) and item.get("output_id")}


def _requested_output_map(requested_outputs: list[dict] | None) -> dict[str, dict]:
    return {str(item.get("output_id")): item for item in (requested_outputs or []) if isinstance(item, dict) and item.get("output_id")}


def _as_float(value: Any, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _vector3(
    value: Any,
    default: tuple[float, float, float],
) -> tuple[float, float, float]:
    if isinstance(value, list | tuple) and len(value) == 3 and all(isinstance(component, (int, float)) for component in value):
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
    resolved_patches = [str(patch) for patch in patches if isinstance(patch, str)] if isinstance(patches, list) and patches else ["hull"]
    return {
        "field": str(spec.get("field") or "p"),
        "time_mode": str(spec.get("time_mode") or "latest"),
        "selector": {
            "type": "patch",
            "patches": resolved_patches,
        },
        "formats": spec.get("formats") if isinstance(spec.get("formats"), list) else ["csv", "png", "report"],
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
        "formats": spec.get("formats") if isinstance(spec.get("formats"), list) else ["csv", "png", "report"],
    }


def resolve_requested_postprocess_spec(
    output_id: str,
    requested_output: dict | None,
) -> dict:
    if output_id == "surface_pressure_contour":
        return _surface_pressure_spec(requested_output)
    if output_id == "wake_velocity_slice":
        return _wake_velocity_slice_spec(requested_output)
    return {"formats": ["csv", "report"]}


def render_requested_postprocess_function_objects(
    *,
    requested_outputs: list[dict] | None,
    reference_length_m: float,
) -> str:
    requested_by_id = _requested_output_map(requested_outputs)
    blocks: list[str] = []

    if "surface_pressure_contour" in requested_by_id:
        spec = resolve_requested_postprocess_spec(
            "surface_pressure_contour",
            requested_by_id["surface_pressure_contour"],
        )
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
        spec = resolve_requested_postprocess_spec(
            "wake_velocity_slice",
            requested_by_id["wake_velocity_slice"],
        )
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


def requested_output_formats(
    output_id: str,
    requested_output: dict | None,
) -> set[str]:
    spec = resolve_requested_postprocess_spec(output_id, requested_output)
    return {str(item).strip().lower() for item in spec.get("formats", []) if isinstance(item, str) and item.strip()}


def _format_vector(values: tuple[float, float, float]) -> str:
    return f"({values[0]:.1f}, {values[1]:.1f}, {values[2]:.1f})"


def selector_summary(output_id: str, requested_output: dict | None) -> str:
    if output_id == "surface_pressure_contour":
        spec = resolve_requested_postprocess_spec(output_id, requested_output)
        patches = spec["selector"]["patches"]
        return f"Patch selection: {', '.join(str(patch) for patch in patches)}"

    if output_id == "wake_velocity_slice":
        spec = resolve_requested_postprocess_spec(output_id, requested_output)
        selector = spec["selector"]
        origin_value = float(selector["origin_value"])
        normal = _vector3(selector.get("normal"), (1.0, 0.0, 0.0))
        if selector.get("origin_mode") == "x_absolute_m":
            return f"Plane slice at x={origin_value:g} m with normal {_format_vector(normal)}"
        return f"Plane slice at x/Lref={origin_value:g} with normal {_format_vector(normal)}"

    return "Selector provenance unavailable"


__all__ = [
    "render_requested_postprocess_function_objects",
    "requested_output_formats",
    "requested_output_ids",
    "resolve_requested_postprocess_spec",
    "selector_summary",
]
