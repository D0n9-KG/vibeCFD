from __future__ import annotations

import struct
from pathlib import Path

from .models import GeometryInspection


GEOMETRY_FAMILY_DEFAULTS: dict[str, float] = {
    "DARPA SUBOFF": 4.356,
    "Joubert BB2": 70.0,
    "Type 209": 62.0,
}


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
    raw = path.read_bytes()
    triangle_count = struct.unpack("<I", raw[80:84])[0]
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for index in range(triangle_count):
        start = 84 + index * 50 + 12
        vertices = struct.unpack("<fffffffff", raw[start : start + 36])
        for vertex_index in range(0, 9, 3):
            x = vertices[vertex_index]
            y = vertices[vertex_index + 1]
            z = vertices[vertex_index + 2]
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            min_z = min(min_z, z)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            max_z = max(max_z, z)

    family = _detect_geometry_family(path.name, geometry_family_hint)
    bounds = {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "min_z": min_z,
        "max_z": max_z,
    }
    raw_length = max(max_x - min_x, max_y - min_y, max_z - min_z)
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
