"""Submarine geometry inspection, trust assessment, and artifact generation."""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from .contracts import build_supervisor_review_contract
from .library import rank_cases
from .models import (
    GeometryBoundingBox,
    GeometryFinding,
    GeometryInspection,
    GeometryReferenceValueSuggestion,
    GeometryScaleAssessment,
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


def _localize_case_title_for_summary(title: str) -> str:
    replacements = (
        (" Bare Hull Resistance Baseline", " 裸艇阻力基线"),
        (" Wake Field Baseline", " 尾流基线"),
        (" Pressure and Velocity Template", " 压力与速度模板"),
        (" Engineering Drag Workflow", " 工程阻力工作流"),
        (" Pressure and Velocity OpenFOAM Template", " 压力与速度 OpenFOAM 模板"),
        (" Drag and Pressure Combo", " 阻力与压力联合方案"),
    )
    localized = title.strip()
    for search, replacement in replacements:
        localized = localized.replace(search, replacement)
    return localized


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


def _read_stl_triangles(path: Path) -> tuple[list[MeshTriangle], str | None]:
    raw = path.read_bytes()
    try:
        if _detect_binary_stl(raw):
            return _parse_binary_stl_triangles(raw), None
        return _parse_ascii_stl_triangles(raw.decode("utf-8", errors="ignore")), None
    except (UnicodeDecodeError, ValueError, struct.error) as exc:
        return [], str(exc)


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


def _raw_length(bounds: GeometryBoundingBox | None) -> float:
    if bounds is None:
        return 0.0
    return max(
        bounds.max_x - bounds.min_x,
        bounds.max_y - bounds.min_y,
        bounds.max_z - bounds.min_z,
    )


def _normalize_mesh_length(length_value: float, family: str) -> float:
    default_length = GEOMETRY_FAMILY_DEFAULTS.get(family)
    if length_value <= 0:
        return default_length or 0.0
    if length_value >= 100 and (default_length is None or length_value > default_length * 10):
        return round(length_value / 1000.0, 3)
    return round(length_value, 3)


def _inspect_stl(path: Path, geometry_family_hint: str | None) -> GeometryInspection:
    triangles, parse_error = _read_stl_triangles(path)
    bounds = _compute_bounds_from_triangles(triangles)
    family = _detect_geometry_family(path.name, geometry_family_hint)
    raw_length = _raw_length(bounds)
    estimated_length = _normalize_mesh_length(raw_length, family)

    notes = [
        "检测到 STL 网格几何。",
        "已统计三角面数量并计算包围盒。",
    ]
    metadata: dict[str, str | None] = {
        "raw_length_value": f"{raw_length:.6f}",
        "normalized_length_m": (
            f"{estimated_length:.6f}" if estimated_length is not None else None
        ),
        "family_default_length_m": (
            f"{GEOMETRY_FAMILY_DEFAULTS.get(family):.6f}"
            if GEOMETRY_FAMILY_DEFAULTS.get(family) is not None
            else None
        ),
    }

    if parse_error:
        notes.append("STL 解析失败，当前结果只能作为阻断性预警。")
        metadata["parse_error"] = parse_error
    if raw_length >= 100:
        notes.append("几何尺度更接近毫米输入，已按除以 1000 的启发式归一到米制。")

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
        metadata=metadata,
    )


def inspect_geometry_file(path: Path, geometry_family_hint: str | None = None) -> GeometryInspection:
    suffix = path.suffix.lower()
    if suffix == ".stl":
        return _inspect_stl(path, geometry_family_hint)
    raise ValueError(f"Only STL (.stl) geometry files are supported in v1; received {suffix}")


def build_geometry_trust_contract(
    geometry: GeometryInspection,
) -> tuple[
    list[GeometryFinding],
    GeometryScaleAssessment,
    list[GeometryReferenceValueSuggestion],
    bool,
    bool,
]:
    findings: list[GeometryFinding] = []
    bounds = geometry.bounding_box
    raw_length = _raw_length(bounds)
    normalized_length = geometry.estimated_length_m
    family_default = GEOMETRY_FAMILY_DEFAULTS.get(geometry.geometry_family)
    parse_error = geometry.metadata.get("parse_error")
    scale_factor = (
        round((normalized_length or 0.0) / raw_length, 6)
        if raw_length > 0 and normalized_length is not None
        else None
    )
    relative_difference = (
        abs((normalized_length or 0.0) - family_default) / family_default
        if family_default and normalized_length is not None and family_default > 0
        else None
    )

    if parse_error:
        findings.append(
            GeometryFinding(
                finding_id="mesh-unreadable",
                category="integrity",
                severity="blocked",
                summary_zh="STL 网格内容无法可靠解析，当前几何不能进入后续求解。",
                evidence={
                    "parse_error": parse_error,
                    "triangle_count": geometry.triangle_count,
                },
            )
        )

    if (geometry.triangle_count or 0) <= 0:
        findings.append(
            GeometryFinding(
                finding_id="mesh-empty",
                category="integrity",
                severity="blocked",
                summary_zh="几何没有可用三角面，无法生成可信的尺度与参考值建议。",
                evidence={"triangle_count": geometry.triangle_count},
            )
        )

    if raw_length <= 0:
        findings.append(
            GeometryFinding(
                finding_id="zero-size-bounds",
                category="scale",
                severity="blocked",
                summary_zh="包围盒尺度为 0，几何尺寸无效，必须先修复源模型。",
                evidence={
                    "bounding_box": bounds.model_dump(mode="json") if bounds else None,
                },
            )
        )

    if raw_length >= 100 and scale_factor is not None and scale_factor <= 0.01:
        findings.append(
            GeometryFinding(
                finding_id="unit-scale-guess-mm-to-m",
                category="scale",
                severity="severe",
                summary_zh="当前长度使用了“除以 1000”的米制猜测，需要研究者确认单位解释。",
                evidence={
                    "raw_length_value": raw_length,
                    "normalized_length_m": normalized_length,
                    "applied_scale_factor": scale_factor,
                },
            )
        )

    mismatch_severity = "info"
    mismatch_summary = "几何尺度与家族默认长度基本一致。"
    if relative_difference is not None:
        if relative_difference >= 0.5:
            mismatch_severity = "severe"
            mismatch_summary = "归一化后的几何长度与该艇型默认长度强烈不一致，需要确认是否选错艇型或单位。"
        elif relative_difference >= 0.2:
            mismatch_severity = "warning"
            mismatch_summary = "归一化后的几何长度与该艇型默认长度存在明显偏差，建议在执行前复核。"

    if family_default is not None and normalized_length is not None:
        findings.append(
            GeometryFinding(
                finding_id="family-default-mismatch",
                category="reference",
                severity=mismatch_severity,
                summary_zh=mismatch_summary,
                evidence={
                    "geometry_family": geometry.geometry_family,
                    "family_default_length_m": family_default,
                    "normalized_length_m": normalized_length,
                    "relative_difference": relative_difference,
                },
            )
        )

    blocked = any(item.severity == "blocked" for item in findings)
    clarification_required = blocked or any(
        item.severity == "severe" for item in findings
    )
    warning_present = any(item.severity == "warning" for item in findings)

    if blocked:
        scale_severity = "blocked"
        scale_summary = "几何尺度存在阻断性问题。"
    elif clarification_required:
        scale_severity = "severe"
        scale_summary = "几何尺度存在高风险不确定性，需要立即确认。"
    elif warning_present:
        scale_severity = "warning"
        scale_summary = "几何尺度可作为草案建议，但建议在执行前复核。"
    else:
        scale_severity = "info"
        scale_summary = "几何尺度可以作为低风险草案建议进入后续确认。"

    scale_assessment = GeometryScaleAssessment(
        raw_length_value=raw_length or None,
        normalized_length_m=normalized_length,
        applied_scale_factor=scale_factor,
        heuristic=(
            "divide_by_1000_mm_to_m"
            if raw_length >= 100 and scale_factor is not None and scale_factor <= 0.01
            else "use_raw_extent_as_meters"
        ),
        severity=scale_severity,
        summary_zh=scale_summary,
        family_default_length_m=family_default,
        relative_difference=relative_difference,
        evidence={
            "triangle_count": geometry.triangle_count,
            "bounding_box": bounds.model_dump(mode="json") if bounds else None,
        },
    )

    reference_value_suggestions: list[GeometryReferenceValueSuggestion] = []
    if normalized_length is not None and raw_length > 0 and not blocked:
        confidence = (
            "low" if clarification_required else "medium" if warning_present else "high"
        )
        beam: float | None = None
        draft: float | None = None
        if bounds is not None and scale_factor is not None:
            beam = max(bounds.max_y - bounds.min_y, 0.0) * scale_factor
            draft = max(bounds.max_z - bounds.min_z, 0.0) * scale_factor
            reference_area = round(max((beam or 0.0) * (draft or 0.0), 1e-4), 6)
        else:
            reference_area = round(max(normalized_length * normalized_length * 0.01, 0.1), 6)

        reference_value_suggestions.extend(
            [
                GeometryReferenceValueSuggestion(
                    suggestion_id="geometry-reference-length",
                    quantity="reference_length_m",
                    value=round(max(normalized_length, 0.1), 6),
                    unit="m",
                    confidence=confidence,
                    source="geometry-preflight",
                    justification="Derived from STL bounding-box extent after unit normalization.",
                    summary_zh=(
                        "建议将归一化后的艇体长度作为参考长度。"
                        if not clarification_required
                        else "建议参考长度已生成，但当前尺度解释仍需研究者确认。"
                    ),
                    is_low_risk=not clarification_required,
                    requires_confirmation=clarification_required,
                    evidence={
                        "raw_length_value": raw_length,
                        "normalized_length_m": normalized_length,
                    },
                ),
                GeometryReferenceValueSuggestion(
                    suggestion_id="geometry-reference-area",
                    quantity="reference_area_m2",
                    value=reference_area,
                    unit="m^2",
                    confidence=confidence,
                    source="geometry-preflight",
                    justification="Derived from normalized beam and draft extents of the STL bounding box.",
                    summary_zh=(
                        "建议将归一化包围盒的横剖面积作为参考面积。"
                        if not clarification_required
                        else "建议参考面积已生成，但当前几何尺度仍需确认。"
                    ),
                    is_low_risk=not clarification_required,
                    requires_confirmation=clarification_required,
                    evidence={
                        "beam_m": beam,
                        "draft_m": draft,
                    },
                ),
            ]
        )

    return (
        findings,
        scale_assessment,
        reference_value_suggestions,
        clarification_required,
        blocked,
    )


def _compose_summary(result: SubmarineGeometryCheckResult) -> str:
    geometry = result.geometry
    candidate = result.candidate_cases[0] if result.candidate_cases else None
    case_text = (
        f"建议优先复用案例模板“{_localize_case_title_for_summary(candidate.title)}”。"
        if candidate
        else "当前没有命中明确案例模板，可先按通用潜艇外流场流程推进。"
    )
    length_text = (
        f"估计艇体长度约 {geometry.estimated_length_m:.3f} m。"
        if geometry.estimated_length_m is not None
        else "当前尚未得到可靠尺度估计。"
    )
    finding_text = (
        f"共记录 {len(result.geometry_findings)} 条几何信任发现。"
        if result.geometry_findings
        else "当前没有记录结构化几何发现。"
    )
    review_text = (
        "下一步需要研究者确认计算草案。"
        if result.review_status == "needs_user_confirmation"
        else "当前几何可以作为已确认草案继续进入求解准备。"
        if result.review_status == "ready_for_supervisor"
        else "当前几何存在阻断性问题，不能继续进入求解。"
    )
    return (
        f"已完成对 `{geometry.file_name}` 的几何检查，识别格式为 `{geometry.input_format}`，"
        f"几何家族倾向于 `{geometry.geometry_family}`。"
        f"{length_text}{finding_text}{case_text}{review_text}"
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
    finding_lines = [
        f"- `{item.finding_id}` | {item.category} | {item.severity} | {item.summary_zh}"
        for item in result.geometry_findings
    ] or ["- 当前没有结构化几何发现。"]
    suggestion_lines = [
        (
            f"- `{item.quantity}` | value={item.value} {item.unit} | "
            f"confidence={item.confidence} | immediate_confirmation={item.requires_confirmation}"
        )
        for item in result.reference_value_suggestions
    ] or ["- 当前没有生成参考值建议。"]

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
                "- 包围盒",
                f"  - x: [{bounds.min_x:.3f}, {bounds.max_x:.3f}]",
                f"  - y: [{bounds.min_y:.3f}, {bounds.max_y:.3f}]",
                f"  - z: [{bounds.min_z:.3f}, {bounds.max_z:.3f}]",
            ]
        )
    lines.extend(
        [
            "",
            "## 几何信任评估",
            f"- clarification_required: `{result.clarification_required}`",
            (
                f"- scale_assessment: `{result.scale_assessment.summary_zh}`"
                if result.scale_assessment
                else "- scale_assessment: `--`"
            ),
            "",
            "## 审核契约",
            f"- review_status: `{result.review_status}`",
            f"- next_recommended_stage: `{result.next_recommended_stage}`",
            f"- report_virtual_path: `{result.report_virtual_path}`",
            "",
            "## 几何发现",
            *finding_lines,
            "",
            "## 参考值建议",
            *suggestion_lines,
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
            "- 先确认案例模板与计算草案，再决定是否进入求解调度。",
            "- 当前产物已经进入 DeerFlow artifact/thread 体系，可直接在工作区查看。",
            "",
        ]
    )
    return "\n".join(lines)


def _render_html(result: SubmarineGeometryCheckResult) -> str:
    geometry = result.geometry
    candidate_items = "".join(
        f"<li><strong>{case.title}</strong><span> score={case.score:.2f}</span><p>{case.rationale}</p></li>"
        for case in result.candidate_cases
    ) or "<li><strong>暂无明确案例</strong><p>可先按通用外流场路径推进。</p></li>"
    role_items = "".join(
        f"<li><strong>{role.title}</strong><p>{role.responsibility}</p></li>"
        for role in result.suggested_roles
    )
    finding_items = "".join(
        f"<li><strong>{item.finding_id}</strong> ({item.severity})<p>{item.summary_zh}</p></li>"
        for item in result.geometry_findings
    ) or "<li><strong>无</strong><p>当前没有结构化几何发现。</p></li>"

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
        <h2>结构化几何发现</h2>
        <ul>{finding_items}</ul>
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
    (
        geometry_findings,
        scale_assessment,
        reference_value_suggestions,
        clarification_required,
        blocked,
    ) = build_geometry_trust_contract(inspection)
    candidate_cases = rank_cases(
        task_description=task_description,
        task_type=task_type,
        geometry_family_hint=inspection.geometry_family,
        geometry_file_name=geometry_path.name,
    )
    result = SubmarineGeometryCheckResult(
        geometry=inspection,
        candidate_cases=candidate_cases,
        geometry_findings=geometry_findings,
        scale_assessment=scale_assessment,
        reference_value_suggestions=reference_value_suggestions,
        clarification_required=clarification_required,
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
        next_recommended_stage=(
            "geometry-preflight"
            if blocked
            else "user-confirmation"
            if clarification_required or reference_value_suggestions
            else "solver-dispatch"
        ),
        report_virtual_path=artifacts[0],
        artifact_virtual_paths=artifacts,
        review_status=(
            "blocked"
            if blocked
            else "needs_user_confirmation"
            if clarification_required or reference_value_suggestions
            else "ready_for_supervisor"
        ),
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
