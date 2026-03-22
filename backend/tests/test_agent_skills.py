from __future__ import annotations

import struct
from pathlib import Path

from app.agent_runtime.geometry import inspect_geometry_file


def test_inspect_geometry_file_parses_parasolid_text_header(tmp_path: Path) -> None:
    geometry_path = tmp_path / "suboff_solid.x_t"
    geometry_path.write_text(
        "\n".join(
            [
                "**PART1;",
                "APPL=unigraphics;",
                "FORMAT=text;",
                "KEY=suboff_solid;",
                "FILE=D:\\Cases\\suboff\\CAD-new\\suboff_solid.x_t;",
                "DATE=26-mar-2024;",
                "**PART2;",
                "SCH=SCH_2700178_26105;",
                "**PART3;",
            ]
        ),
        encoding="utf-8",
    )

    summary = inspect_geometry_file(geometry_path, geometry_family_hint="DARPA SUBOFF")

    assert summary.input_format == "x_t"
    assert summary.geometry_family == "DARPA SUBOFF"
    assert summary.parasolid_key == "suboff_solid"
    assert summary.source_application == "unigraphics"
    assert summary.file_size_bytes == geometry_path.stat().st_size


def test_inspect_geometry_file_normalizes_large_stl_dimensions_to_meters(tmp_path: Path) -> None:
    geometry_path = tmp_path / "suboff_solid.stl"
    header = b"DARPA SUBOFF STL".ljust(80, b" ")
    triangle_count = 1
    normal = (0.0, 0.0, 1.0)
    vertices = (
        0.0,
        0.0,
        0.0,
        4355.948,
        0.0,
        0.0,
        0.0,
        200.0,
        0.0,
    )
    payload = header + struct.pack("<I", triangle_count)
    payload += struct.pack("<fff", *normal)
    payload += struct.pack("<fffffffff", *vertices)
    payload += struct.pack("<H", 0)
    geometry_path.write_bytes(payload)

    summary = inspect_geometry_file(geometry_path, geometry_family_hint="DARPA SUBOFF")

    assert summary.input_format == "stl"
    assert summary.geometry_family == "DARPA SUBOFF"
    assert summary.triangle_count == 1
    assert summary.estimated_length_m == 4.356
