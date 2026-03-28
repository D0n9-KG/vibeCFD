from __future__ import annotations

import json
import math
from pathlib import Path

from ..models import ArtifactItem, TaskType
from .models import AgentPlan, AgentReport, GeometryInspection


def artifact_url(run_id: str, relative_path: str) -> str:
    return f"/api/runs/{run_id}/artifacts/{relative_path}"


def build_artifact(
    run_id: str,
    *,
    label: str,
    category: str,
    relative_path: str,
    mime_type: str,
) -> ArtifactItem:
    return ArtifactItem(
        label=label,
        category=category,
        relative_path=relative_path,
        mime_type=mime_type,
        url=artifact_url(run_id, relative_path),
    )


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _series_chart(title: str, subtitle: str, color: str, values: list[float], unit: str) -> str:
    width = 760
    height = 320
    margin_x = 60
    margin_y = 240
    span = max(max(values) - min(values), 1e-6)
    step = 600 / max(len(values) - 1, 1)
    points = []
    for index, value in enumerate(values):
        x = margin_x + index * step
        y = margin_y - ((value - min(values)) / span) * 140
        points.append((x, y))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    point_marks = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}" />' for x, y in points
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="20" fill="#0b1624" />
  <text x="32" y="38" fill="#f8fafc" font-size="22" font-family="Segoe UI, sans-serif">{title}</text>
  <text x="32" y="62" fill="#93c5fd" font-size="12" font-family="Segoe UI, sans-serif">{subtitle}</text>
  <g stroke="rgba(255,255,255,0.12)">
    <line x1="60" y1="240" x2="680" y2="240" />
    <line x1="60" y1="190" x2="680" y2="190" />
    <line x1="60" y1="140" x2="680" y2="140" />
    <line x1="60" y1="90" x2="680" y2="90" />
  </g>
  <text x="18" y="240" fill="#9ca3af" font-size="12" font-family="Segoe UI, sans-serif">{unit}</text>
  <polyline fill="none" stroke="{color}" stroke-width="4" points="{polyline}" />
  {point_marks}
</svg>
"""


def render_geometry_overview_svg(
    inspection: GeometryInspection,
    *,
    task_type: TaskType,
    selected_case_title: str | None,
) -> str:
    title = f"{inspection.geometry_family} 几何总览"
    case_label = selected_case_title or "尚未映射案例"
    detail_rows = [
        f"输入格式：{inspection.input_format}",
        f"任务类型：{task_type}",
        f"案例模板：{case_label}",
    ]
    if inspection.estimated_length_m is not None:
        detail_rows.append(f"估计尺度：{inspection.estimated_length_m:.3f} m")
    if inspection.parasolid_key:
        detail_rows.append(f"Parasolid KEY：{inspection.parasolid_key}")
    if inspection.triangle_count:
        detail_rows.append(f"三角面数量：{inspection.triangle_count}")

    detail_markup = "\n".join(
        f'<text x="420" y="{90 + index * 28}" fill="#dbeafe" font-size="16" font-family="Segoe UI, sans-serif">{row}</text>'
        for index, row in enumerate(detail_rows)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="760" height="320" viewBox="0 0 760 320">
  <rect width="760" height="320" rx="24" fill="#08131f" />
  <text x="28" y="38" fill="#f8fafc" font-size="22" font-family="Segoe UI, sans-serif">{title}</text>
  <text x="28" y="62" fill="#93c5fd" font-size="12" font-family="Segoe UI, sans-serif">主控执行器生成的几何检查摘要</text>
  <path d="M60 190 C120 180, 180 168, 250 164 C320 160, 390 160, 470 170 C540 178, 620 188, 700 190 L700 210 L60 210 Z"
    fill="rgba(56,189,248,0.18)" stroke="#38bdf8" stroke-width="3" />
  <rect x="392" y="74" width="330" height="174" rx="18" fill="rgba(15,23,42,0.72)" stroke="rgba(147,197,253,0.25)" />
  {detail_markup}
</svg>
"""


def render_pressure_chart(task_type: TaskType, pressure_peak_kpa: float) -> str:
    values = [
        pressure_peak_kpa * (0.74 + math.sin(index / 1.8) * 0.12 + index * 0.012)
        for index in range(10)
    ]
    return _series_chart("表面压力分布", f"任务类型：{task_type}", "#38bdf8", values, "kPa")


def render_wake_chart(wake_uniformity: float) -> str:
    values = [
        wake_uniformity * (0.9 + math.cos(index / 2.4) * 0.06)
        for index in range(10)
    ]
    return _series_chart("尾流均匀性切片", "基于演示级求解结果生成", "#f59e0b", values, "-")


def _metric_label(metric_key: str) -> str:
    labels = {
        "drag_coefficient": "阻力系数",
        "drag_newtons": "总阻力",
        "pressure_peak_kpa": "压力峰值",
        "pressure_mean_kpa": "平均压力",
        "wake_uniformity": "尾流均匀性",
        "reference_speed_ms": "参考航速",
        "wetted_area_m2": "湿表面积",
        "estimated_length_m": "估计艇长",
    }
    return labels.get(metric_key, metric_key)


def _metric_value(metric_key: str, value: float | str) -> str:
    units = {
        "drag_coefficient": "",
        "drag_newtons": "N",
        "pressure_peak_kpa": "kPa",
        "pressure_mean_kpa": "kPa",
        "wake_uniformity": "",
        "reference_speed_ms": "m/s",
        "wetted_area_m2": "m^2",
        "estimated_length_m": "m",
    }
    if isinstance(value, float):
        rendered = f"{value:.5f}" if metric_key == "drag_coefficient" else f"{value:.3f}".rstrip("0").rstrip(".")
    else:
        rendered = str(value)
    unit = units.get(metric_key, "")
    return f"{rendered} {unit}".strip()


def compose_final_report_markdown(
    *,
    run_id: str,
    request_goal: str,
    task_description: str,
    task_type: str,
    geometry: GeometryInspection,
    metrics: dict[str, float | str],
    plan: AgentPlan,
    report: AgentReport,
    selected_case_title: str | None,
    artifact_lines: list[str],
) -> str:
    lines = [
        f"# {report.report_title}",
        "",
        "## 执行摘要",
        report.executive_summary,
        "",
        "## 任务背景",
        f"- Run ID：`{run_id}`",
        f"- 执行目标：{request_goal}",
        f"- 任务描述：{task_description}",
        f"- 任务类型：`{task_type}`",
        f"- 几何家族：{geometry.geometry_family}",
        f"- 已选案例：{selected_case_title or '尚未映射案例'}",
        "",
        "## 主控执行方案",
        plan.plan_summary,
        "",
        "### 技能步骤",
        *[
            f"- `{step.skill_id}`：{step.goal}；预期输出：{step.expected_output}"
            for step in plan.steps
        ],
        "",
        "## 几何检查结论",
        f"- 输入文件：{geometry.file_name}",
        f"- 输入格式：{geometry.input_format}",
        *([f"- Parasolid KEY：{geometry.parasolid_key}"] if geometry.parasolid_key else []),
        *([f"- 估计尺度：{geometry.estimated_length_m:.3f} m"] if geometry.estimated_length_m else []),
        *[f"- {note}" for note in geometry.notes],
        "",
        "## 关键结果指标",
        *[
            f"- {_metric_label(key)}：{_metric_value(key, value)}"
            for key, value in metrics.items()
        ],
        "",
        "## 关键发现",
        *[f"- {item}" for item in report.key_findings],
        "",
        "## 可信性说明",
        *[f"- {item}" for item in report.verification_notes],
        "",
        "## 产物清单",
        *[f"- {line}" for line in artifact_lines],
        "",
        "## 后续建议",
        *[f"- {item}" for item in report.next_actions],
        "",
    ]
    return "\n".join(lines).strip() + "\n"
