from __future__ import annotations

import struct
from pathlib import Path

from app.agent_runtime.skills import run_geometry_check
from app.agent_runtime.geometry import inspect_geometry_file
from app.executor_protocol import ExecutorTaskContext, ExecutorTaskRequest


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


def _create_request(run_directory: Path, input_relative_path: str) -> ExecutorTaskRequest:
    return ExecutorTaskRequest(
        job_id="job_geometry_preview",
        run_id="run_geometry_preview",
        stage="geometry_check",
        goal="生成几何预览",
        run_directory=str(run_directory),
        input_files=[input_relative_path],
        context=ExecutorTaskContext(
            task_description="分析潜艇外形",
            task_type="pressure_distribution",
            geometry_family="DARPA SUBOFF",
            selected_case_title="SUBOFF 压力分布基线案例",
        ),
    )


def test_run_geometry_check_exports_obj_preview_for_stl(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    upload_directory = run_directory / "request" / "uploaded_files"
    upload_directory.mkdir(parents=True)

    geometry_path = upload_directory / "suboff_solid.stl"
    header = b"DARPA SUBOFF STL".ljust(80, b" ")
    triangle_count = 1
    normal = (0.0, 0.0, 1.0)
    vertices = (
        0.0,
        0.0,
        0.0,
        4.356,
        0.0,
        0.0,
        0.0,
        0.2,
        0.0,
    )
    payload = header + struct.pack("<I", triangle_count)
    payload += struct.pack("<fff", *normal)
    payload += struct.pack("<fffffffff", *vertices)
    payload += struct.pack("<H", 0)
    geometry_path.write_bytes(payload)

    _, result = run_geometry_check(
        _create_request(run_directory, "request/uploaded_files/suboff_solid.stl")
    )

    preview_path = run_directory / "postprocess" / "models" / "geometry_preview.obj"

    assert preview_path.exists()
    assert any(
        artifact.category == "model" and artifact.relative_path == "postprocess/models/geometry_preview.obj"
        for artifact in result.artifacts
    )
    preview_content = preview_path.read_text(encoding="utf-8")
    assert "\nv " in f"\n{preview_content}"
    assert "\nf " in f"\n{preview_content}"


def test_run_geometry_check_exports_proxy_obj_preview_for_xt(tmp_path: Path) -> None:
    run_directory = tmp_path / "run"
    upload_directory = run_directory / "request" / "uploaded_files"
    upload_directory.mkdir(parents=True)

    geometry_path = upload_directory / "suboff_solid.x_t"
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

    geometry, result = run_geometry_check(
        _create_request(run_directory, "request/uploaded_files/suboff_solid.x_t")
    )

    preview_path = run_directory / "postprocess" / "models" / "geometry_preview.obj"

    assert geometry.input_format == "x_t"
    assert preview_path.exists()
    assert any(artifact.category == "model" for artifact in result.artifacts)
    assert "o submarine_preview" in preview_path.read_text(encoding="utf-8")
