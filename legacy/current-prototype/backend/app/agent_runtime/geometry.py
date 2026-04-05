from __future__ import annotations

import math
import struct
from pathlib import Path

from .models import GeometryInspection


GEOMETRY_FAMILY_DEFAULTS: dict[str, float] = {
    "DARPA SUBOFF": 4.356,
    "Joubert BB2": 70.0,
    "Type 209": 62.0,
}

MeshTriangle = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def _detect_geometry_family(text: str, hint: str | None) -> str:
    if hint:
        return hint
    lowered = text.lower()
    if "suboff" in lowered:
        return "DARPA SUBOFF"
    if "bb2" in lowered or "joubert" in lowered:
        return "Joubert BB2"
    if "209" in lowered:
        return "Type 209"
    return "Generic Submarine Hull"


def _parse_parasolid_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "=" not in line or not line.endswith(";"):
            continue
        key, value = line[:-1].split("=", 1)
        metadata[key.strip().upper()] = value.strip()
    return metadata


def _detect_binary_stl(raw: bytes) -> bool:
    if len(raw) < 84:
        return False
    triangle_count = struct.unpack("<I", raw[80:84])[0]
    expected_size = 84 + triangle_count * 50
    if expected_size == len(raw):
        return True
    return not raw[:5].lower().startswith(b"solid")


def _parse_binary_stl_triangles(raw: bytes) -> list[MeshTriangle]:
    triangle_count = struct.unpack("<I", raw[80:84])[0]
    triangles: list[MeshTriangle] = []
    for index in range(triangle_count):
        start = 84 + index * 50 + 12
        vertices = struct.unpack("<fffffffff", raw[start : start + 36])
        triangles.append(
            (
                (vertices[0], vertices[1], vertices[2]),
                (vertices[3], vertices[4], vertices[5]),
                (vertices[6], vertices[7], vertices[8]),
            )
        )
    return triangles


def _parse_ascii_stl_triangles(text: str) -> list[MeshTriangle]:
    triangles: list[MeshTriangle] = []
    current_vertices: list[tuple[float, float, float]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.lower().startswith("vertex "):
            continue
        parts = line.split()
        if len(parts) != 4:
            continue
        current_vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        if len(current_vertices) == 3:
            triangles.append((current_vertices[0], current_vertices[1], current_vertices[2]))
            current_vertices = []

    return triangles


def _read_stl_triangles(path: Path) -> list[MeshTriangle]:
    raw = path.read_bytes()
    if _detect_binary_stl(raw):
        return _parse_binary_stl_triangles(raw)
    return _parse_ascii_stl_triangles(raw.decode("utf-8", errors="ignore"))


def _compute_bounds_from_triangles(triangles: list[MeshTriangle]) -> dict[str, float]:
    if not triangles:
        return {
            "min_x": 0.0,
            "max_x": 0.0,
            "min_y": 0.0,
            "max_y": 0.0,
            "min_z": 0.0,
            "max_z": 0.0,
        }

    xs = [vertex[0] for triangle in triangles for vertex in triangle]
    ys = [vertex[1] for triangle in triangles for vertex in triangle]
    zs = [vertex[2] for triangle in triangles for vertex in triangle]
    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
    }


def _normalize_triangles(
    triangles: list[MeshTriangle],
    *,
    geometry_family: str,
    estimated_length_m: float | None,
) -> list[MeshTriangle]:
    if not triangles:
        return []

    bounds = _compute_bounds_from_triangles(triangles)
    span_x = bounds["max_x"] - bounds["min_x"]
    span_y = bounds["max_y"] - bounds["min_y"]
    span_z = bounds["max_z"] - bounds["min_z"]
    raw_length = max(span_x, span_y, span_z, 1e-6)
    target_length = estimated_length_m or _normalize_mesh_length(raw_length, geometry_family)

    center_x = (bounds["min_x"] + bounds["max_x"]) / 2.0
    center_y = (bounds["min_y"] + bounds["max_y"]) / 2.0
    center_z = (bounds["min_z"] + bounds["max_z"]) / 2.0
    scale = target_length / raw_length if raw_length > 0 else 1.0

    return [
        tuple(
            (
                round((vertex[0] - center_x) * scale, 6),
                round((vertex[1] - center_y) * scale, 6),
                round((vertex[2] - center_z) * scale, 6),
            )
            for vertex in triangle
        )
        for triangle in triangles
    ]


def _triangles_to_obj(triangles: list[MeshTriangle], object_name: str = "submarine_preview") -> str:
    lines = [f"o {object_name}"]
    vertex_index = 1

    for triangle in triangles:
        for vertex in triangle:
            lines.append(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}")
        lines.append(f"f {vertex_index} {vertex_index + 1} {vertex_index + 2}")
        vertex_index += 3

    return "\n".join(lines) + "\n"


def _submarine_radius_profile(geometry_family: str, length_m: float) -> list[tuple[float, float]]:
    radius_scale = {
        "DARPA SUBOFF": 0.061,
        "Joubert BB2": 0.067,
        "Type 209": 0.069,
    }.get(geometry_family, 0.064)
    max_radius = max(length_m * radius_scale, 0.12)
    return [
        (-length_m * 0.50, max_radius * 0.01),
        (-length_m * 0.44, max_radius * 0.38),
        (-length_m * 0.34, max_radius * 0.72),
        (-length_m * 0.12, max_radius * 0.94),
        (length_m * 0.16, max_radius),
        (length_m * 0.34, max_radius * 0.93),
        (length_m * 0.43, max_radius * 0.80),
        (length_m * 0.49, max_radius * 0.16),
    ]


def _generate_proxy_submarine_obj(geometry: GeometryInspection, segments: int = 28) -> str:
    length_m = geometry.estimated_length_m or GEOMETRY_FAMILY_DEFAULTS.get(geometry.geometry_family, 8.0)
    profile = _submarine_radius_profile(geometry.geometry_family, length_m)

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []

    for x_position, radius in profile:
        for segment in range(segments):
            angle = (math.tau * segment) / segments
            vertices.append(
                (
                    round(x_position, 6),
                    round(math.cos(angle) * radius, 6),
                    round(math.sin(angle) * radius, 6),
                )
            )

    for ring_index in range(len(profile) - 1):
        current_start = ring_index * segments
        next_start = (ring_index + 1) * segments
        for segment in range(segments):
            current = current_start + segment
            following = current_start + ((segment + 1) % segments)
            next_current = next_start + segment
            next_following = next_start + ((segment + 1) % segments)
            faces.append((current + 1, next_current + 1, next_following + 1))
            faces.append((current + 1, next_following + 1, following + 1))

    lines = ["o submarine_preview"]
    lines.extend(f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in vertices)
    lines.extend(f"f {a} {b} {c}" for a, b, c in faces)
    return "\n".join(lines) + "\n"


def build_geometry_preview_obj(path: Path | None, geometry: GeometryInspection) -> str:
    if path is not None and path.suffix.lower() == ".stl":
        triangles = _read_stl_triangles(path)
        normalized_triangles = _normalize_triangles(
            triangles,
            geometry_family=geometry.geometry_family,
            estimated_length_m=geometry.estimated_length_m,
        )
        if normalized_triangles:
            return _triangles_to_obj(normalized_triangles)
    return _generate_proxy_submarine_obj(geometry)


def _normalize_mesh_length(length_value: float, family: str) -> float:
    default_length = GEOMETRY_FAMILY_DEFAULTS.get(family)
    if length_value <= 0:
        return default_length or 0.0
    if length_value >= 100 and (default_length is None or length_value > default_length * 10):
        return round(length_value / 1000.0, 3)
    return round(length_value, 3)


def _scale_bounding_box(bounds: dict[str, float], scale_factor: float) -> dict[str, float]:
    return {key: round(value * scale_factor, 6) for key, value in bounds.items()}


def _inspect_parasolid(path: Path, geometry_family_hint: str | None) -> GeometryInspection:
    text = path.read_text(encoding="utf-8", errors="ignore")
    metadata = _parse_parasolid_metadata(text)
    family = _detect_geometry_family(f"{path.name}\n{text}", geometry_family_hint)
    return GeometryInspection(
        file_name=path.name,
        file_size_bytes=path.stat().st_size,
        input_format="x_t",
        geometry_family=family,
        source_application=metadata.get("APPL"),
        parasolid_key=metadata.get("KEY"),
        estimated_length_m=GEOMETRY_FAMILY_DEFAULTS.get(family),
        notes=[
            "检测到 Parasolid 文本格式几何。",
            "已提取头部元数据并映射到潜艇几何家族。",
        ],
        metadata={
            "format": metadata.get("FORMAT"),
            "date": metadata.get("DATE"),
            "source_file": metadata.get("FILE"),
        },
    )


def _inspect_binary_stl(path: Path, geometry_family_hint: str | None) -> GeometryInspection:
    triangles = _read_stl_triangles(path)
    triangle_count = len(triangles)
    bounds = _compute_bounds_from_triangles(triangles)

    family = _detect_geometry_family(path.name, geometry_family_hint)
    raw_length = max(
        bounds["max_x"] - bounds["min_x"],
        bounds["max_y"] - bounds["min_y"],
        bounds["max_z"] - bounds["min_z"],
    )
    estimated_length = _normalize_mesh_length(raw_length, family)
    scale_factor = estimated_length / raw_length if raw_length > 0 else 1.0
    normalized_bounds = _scale_bounding_box(bounds, scale_factor)

    notes = ["检测到 STL 网格文件。", "已统计三角面数量并计算包围盒。"]
    if scale_factor != 1.0:
        notes.append("检测到尺度更接近毫米单位，已自动折算为米。")

    return GeometryInspection(
        file_name=path.name,
        file_size_bytes=path.stat().st_size,
        input_format="stl",
        geometry_family=family,
        source_application="stl-mesh",
        estimated_length_m=estimated_length or GEOMETRY_FAMILY_DEFAULTS.get(family),
        triangle_count=triangle_count,
        bounding_box=normalized_bounds,
        notes=notes,
    )


def inspect_geometry_file(path: Path, geometry_family_hint: str | None = None) -> GeometryInspection:
    suffix = path.suffix.lower()
    if suffix == ".x_t":
        return _inspect_parasolid(path, geometry_family_hint)
    if suffix == ".stl":
        return _inspect_binary_stl(path, geometry_family_hint)

    family = _detect_geometry_family(path.name, geometry_family_hint)
    return GeometryInspection(
        file_name=path.name,
        file_size_bytes=path.stat().st_size,
        input_format=suffix.lstrip(".") or "unknown",
        geometry_family=family,
        estimated_length_m=GEOMETRY_FAMILY_DEFAULTS.get(family),
        notes=["检测到可接受的几何文件，但当前版本只做基础元数据提取。"],
    )
