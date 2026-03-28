"""Submarine geometry inspection and artifact generation."""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from .contracts import build_supervisor_review_contract
from .library import rank_cases
from .models import (
    GeometryBoundingBox,
    GeometryInspection,
    SubmarineGeometryCheckResult,
)
from .roles import get_subagent_role_boundaries

GEOMETRY_FAMILY_DEFAULTS: dict[str, float] = {
    "DARPA SUBOFF": 4.356,
    "Joubert BB2": 70.0,
    "Type 209": 62.0,
}

SUPPORTED_GEOMETRY_SUFFIXES = {".stl"}
MeshTriangle = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "geometry-check"


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


def _compute_bounds_from_triangles(triangles: list[MeshTriangle]) -> GeometryBoundingBox:
    if not triangles:
        return GeometryBoundingBox()

    xs = [vertex[0] for triangle in triangles for vertex in triangle]
    ys = [vertex[1] for triangle in triangles for vertex in triangle]
    zs = [vertex[2] for triangle in triangles for vertex in triangle]
    return GeometryBoundingBox(
        min_x=min(xs),
        max_x=max(xs),
        min_y=min(ys),
        max_y=max(ys),
        min_z=min(zs),
        max_z=max(zs),
    )


def _normalize_mesh_length(length_value: float, family: str) -> float:
    default_length = GEOMETRY_FAMILY_DEFAULTS.get(family)
    if length_value <= 0:
        return default_length or 0.0
    if length_value >= 100 and (default_length is None or length_value > default_length * 10):
        return round(length_value / 1000.0, 3)
    return round(length_value, 3)


def _inspect_stl(path: Path, geometry_family_hint: str | None) -> GeometryInspection:
    triangles = _read_stl_triangles(path)
    bounds = _compute_bounds_from_triangles(triangles)
    family = _detect_geometry_family(path.name, geometry_family_hint)
    raw_length = max(
        bounds.max_x - bounds.min_x,
        bounds.max_y - bounds.min_y,
        bounds.max_z - bounds.min_z,
    )
    estimated_length = _normalize_mesh_length(raw_length, family)

    notes = [
        "检测到 STL 网格几何。",
        "已统计三角面数量并计算包围盒。",
    ]
    if raw_length >= 100:
        notes.append("几何尺度看起来更接近毫米级输入，已按米级长度进行归一化估计。")

    return GeometryInspection(
        file_name=path.name,
        file_size_bytes=path.stat().st_size,
        input_format="stl",
        geometry_family=family,
        source_application="stl-mesh",
        estimated_length_m=estimated_length or GEOMETRY_FAMILY_DEFAULTS.get(family),
        triangle_count=len(triangles),
        bounding_box=bounds,
        notes=notes,
    )


def inspect_geometry_file(path: Path, geometry_family_hint: str | None = None) -> GeometryInspection:
    suffix = path.suffix.lower()
    if suffix == ".stl":
        return _inspect_stl(path, geometry_family_hint)
    raise ValueError(f"Only STL (.stl) geometry files are supported in v1; received {suffix}")


def _compose_summary(result: SubmarineGeometryCheckResult) -> str:
    geometry = result.geometry
    candidate = result.candidate_cases[0] if result.candidate_cases else None
    case_text = f"建议优先复用案例模板“{candidate.title}”。" if candidate else "当前没有命中明确案例模板，可先按通用潜艇外流场流程推进。"
    length_text = (
        f"估计艏体长度约 {geometry.estimated_length_m:.3f} m。"
        if geometry.estimated_length_m is not None
        else "当前尚未得到可靠尺度估计。"
    )
    return (
        f"已完成对 `{geometry.file_name}` 的几何检查，识别格式为 `{geometry.input_format}`，"
        f"几何家族倾向于 `{geometry.geometry_family}`。{length_text}{case_text}"
    )


def _render_markdown(result: SubmarineGeometryCheckResult) -> str:
    geometry = result.geometry
    case_lines = [
        f"- `{case.case_id}` | {case.title} | score={case.score:.2f} | {case.rationale}"
        for case in result.candidate_cases
    ] or ["- 当前没有匹配到明确案例。"]
    role_lines = [
        f"- `{role.role_id}` | {role.title} | {role.responsibility}"
        for role in result.suggested_roles
    ]

    lines = [
        "# 潜艇几何检查结果",
        "",
        "## 中文摘要",
        result.summary_zh,
        "",
        "## 几何信息",
        f"- 文件名: `{geometry.file_name}`",
        f"- 输入格式: `{geometry.input_format}`",
        f"- 几何家族: {geometry.geometry_family}",
        f"- 文件大小: {geometry.file_size_bytes} bytes",
    ]
    if geometry.parasolid_key:
        lines.append(f"- Parasolid KEY: `{geometry.parasolid_key}`")
    if geometry.estimated_length_m is not None:
        lines.append(f"- 估计长度: {geometry.estimated_length_m:.3f} m")
    if geometry.triangle_count is not None:
        lines.append(f"- 三角面数量: {geometry.triangle_count}")
    if geometry.bounding_box is not None:
        bounds = geometry.bounding_box
        lines.extend(
            [
                "- 包围盒:",
                f"  - x: [{bounds.min_x:.3f}, {bounds.max_x:.3f}]",
                f"  - y: [{bounds.min_y:.3f}, {bounds.max_y:.3f}]",
                f"  - z: [{bounds.min_z:.3f}, {bounds.max_z:.3f}]",
            ]
        )
    lines.extend(
        [
            "",
            "## 审核契约",
            f"- review_status: `{result.review_status}`",
            f"- next_recommended_stage: `{result.next_recommended_stage}`",
            f"- report_virtual_path: `{result.report_virtual_path}`",
            "",
            "## 几何检查备注",
            *[f"- {note}" for note in geometry.notes],
            "",
            "## 候选案例",
            *case_lines,
            "",
            "## 预留的后续 sub-agent 角色边界",
            *role_lines,
            "",
            "## 下一步建议",
            "- 先确认案例模板和工况，再进入求解调度。",
            "- 当前产物已经进入 DeerFlow artifact/thread 体系，可直接在工作区查看。",
            "",
        ]
    )
    return "\n".join(lines)


def _render_html(result: SubmarineGeometryCheckResult) -> str:
    geometry = result.geometry
    candidate_items = "".join(
        f"<li><strong>{case.title}</strong><span>score={case.score:.2f}</span><p>{case.rationale}</p></li>"
        for case in result.candidate_cases
    ) or "<li><strong>暂无明确案例</strong><p>可先按通用外流场流程推进。</p></li>"
    role_items = "".join(
        f"<li><strong>{role.title}</strong><p>{role.responsibility}</p></li>"
        for role in result.suggested_roles
    )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>潜艇几何检查结果</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: linear-gradient(135deg, #07131e 0%, #0f2740 55%, #153759 100%);
        color: #e8f1fb;
      }}
      .layout {{ display: grid; gap: 20px; }}
      .panel {{
        background: rgba(8, 20, 33, 0.78);
        border: 1px solid rgba(125, 179, 229, 0.22);
        border-radius: 20px;
        padding: 20px 24px;
        box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
      }}
      h1, h2 {{ margin: 0 0 12px; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li {{ margin-bottom: 10px; }}
      .summary {{ font-size: 18px; line-height: 1.7; }}
      .metrics {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
      }}
      .metric {{
        border-radius: 16px;
        background: rgba(20, 48, 76, 0.75);
        padding: 14px 16px;
      }}
      .metric small {{
        display: block;
        opacity: 0.7;
        margin-bottom: 6px;
      }}
    </style>
  </head>
  <body>
    <div class="layout">
      <section class="panel">
        <h1>潜艇几何检查结果</h1>
        <p class="summary">{result.summary_zh}</p>
      </section>
      <section class="panel">
        <h2>几何指标</h2>
        <div class="metrics">
          <div class="metric"><small>文件名</small>{geometry.file_name}</div>
          <div class="metric"><small>输入格式</small>{geometry.input_format}</div>
          <div class="metric"><small>几何家族</small>{geometry.geometry_family}</div>
          <div class="metric"><small>估计长度</small>{geometry.estimated_length_m or "N/A"}</div>
        </div>
      </section>
      <section class="panel">
        <h2>候选案例</h2>
        <ul>{candidate_items}</ul>
      </section>
      <section class="panel">
        <h2>预留角色边界</h2>
        <ul>{role_items}</ul>
      </section>
    </div>
  </body>
</html>
"""


def _artifact_virtual_path(run_dir_name: str, filename: str) -> str:
    return f"/mnt/user-data/outputs/submarine/geometry-check/{run_dir_name}/{filename}"


def run_geometry_check(
    *,
    geometry_path: Path,
    outputs_dir: Path,
    task_description: str,
    task_type: str,
    geometry_family_hint: str | None = None,
) -> tuple[SubmarineGeometryCheckResult, list[str]]:
    """Inspect geometry and persist DeerFlow-consumable artifacts."""
    inspection = inspect_geometry_file(geometry_path, geometry_family_hint)
    candidate_cases = rank_cases(
        task_description=task_description,
        task_type=task_type,
        geometry_family_hint=inspection.geometry_family,
        geometry_file_name=geometry_path.name,
    )
    result = SubmarineGeometryCheckResult(
        geometry=inspection,
        candidate_cases=candidate_cases,
        summary_zh="",
        suggested_roles=get_subagent_role_boundaries(),
    )
    run_dir_name = _slugify(geometry_path.stem)
    artifact_dir = outputs_dir / "submarine" / "geometry-check" / run_dir_name
    artifact_dir.mkdir(parents=True, exist_ok=True)

    payload_path = artifact_dir / "geometry-check.json"
    markdown_path = artifact_dir / "geometry-check.md"
    html_path = artifact_dir / "geometry-check.html"
    artifacts = [
        _artifact_virtual_path(run_dir_name, "geometry-check.md"),
        _artifact_virtual_path(run_dir_name, "geometry-check.html"),
        _artifact_virtual_path(run_dir_name, "geometry-check.json"),
    ]
    review = build_supervisor_review_contract(
        next_recommended_stage="geometry-preflight",
        report_virtual_path=artifacts[0],
        artifact_virtual_paths=artifacts,
    )
    result.review_status = review.review_status
    result.next_recommended_stage = review.next_recommended_stage
    result.report_virtual_path = review.report_virtual_path
    result.artifact_virtual_paths = review.artifact_virtual_paths
    result.summary_zh = _compose_summary(result)

    payload_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(result), encoding="utf-8")
    html_path.write_text(_render_html(result), encoding="utf-8")

    return result, artifacts
