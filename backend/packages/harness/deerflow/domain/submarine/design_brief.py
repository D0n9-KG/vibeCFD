"""Submarine CFD design brief generation for supervisor-facing planning."""

from __future__ import annotations

import hashlib
import json
import re
from html import escape
from pathlib import Path

from deerflow.domain.submarine.calculation_plan import (
    build_design_brief_calculation_plan,
)
from deerflow.domain.submarine.contracts import build_execution_plan
from deerflow.domain.submarine.library import load_case_library
from deerflow.domain.submarine.output_contract import (
    build_output_delivery_plan,
    resolve_requested_outputs,
)
from deerflow.domain.submarine.solver_dispatch import _resolve_simulation_requirements
from deerflow.domain.submarine.verification import (
    build_effective_scientific_verification_requirements,
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "submarine-design-brief"


def _artifact_virtual_path(run_dir_name: str, filename: str) -> str:
    return f"/mnt/user-data/outputs/submarine/design-brief/{run_dir_name}/{filename}"


_MAX_ARTIFACT_PATH_CHARS = 239
_MAX_RUN_DIR_NAME_CHARS = 80
_MIN_RUN_DIR_NAME_CHARS = 16
_RUN_DIR_HASH_CHARS = 10
_LONGEST_DESIGN_BRIEF_FILENAME = "cfd-design-brief.json"


def _resolve_run_dir_name_budget(outputs_dir: Path) -> int:
    artifact_root = outputs_dir / "submarine" / "design-brief"
    reserved_chars = len(_LONGEST_DESIGN_BRIEF_FILENAME) + 2
    available = _MAX_ARTIFACT_PATH_CHARS - len(str(artifact_root)) - reserved_chars
    return max(_MIN_RUN_DIR_NAME_CHARS, min(_MAX_RUN_DIR_NAME_CHARS, available))


def _build_run_dir_name(*, outputs_dir: Path, run_basis: str) -> str:
    slug = _slugify(run_basis)
    max_length = _resolve_run_dir_name_budget(outputs_dir)
    if len(slug) <= max_length:
        return slug

    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:_RUN_DIR_HASH_CHARS]
    prefix_length = max_length - len(digest) - 1
    if prefix_length <= 0:
        return digest[:max_length]

    prefix = slug[:prefix_length].rstrip("-_")
    if not prefix:
        return digest[:max_length]
    return f"{prefix}-{digest}"


def _maybe_resolve_simulation_requirements(
    *,
    inlet_velocity_mps: float | None,
    fluid_density_kg_m3: float | None,
    kinematic_viscosity_m2ps: float | None,
    end_time_seconds: float | None,
    delta_t_seconds: float | None,
    write_interval_steps: int | None,
) -> dict[str, float | int] | None:
    if all(
        value is None
        for value in (
            inlet_velocity_mps,
            fluid_density_kg_m3,
            kinematic_viscosity_m2ps,
            end_time_seconds,
            delta_t_seconds,
            write_interval_steps,
        )
    ):
        return None

    return _resolve_simulation_requirements(
        inlet_velocity_mps=inlet_velocity_mps,
        fluid_density_kg_m3=fluid_density_kg_m3,
        kinematic_viscosity_m2ps=kinematic_viscosity_m2ps,
        end_time_seconds=end_time_seconds,
        delta_t_seconds=delta_t_seconds,
        write_interval_steps=write_interval_steps,
    )


def _compose_summary(
    *,
    task_description: str,
    input_source_type: str,
    geometry_virtual_path: str | None,
    official_case_id: str | None,
    geometry_family_hint: str | None,
    confirmation_status: str,
    selected_case_id: str | None,
    expected_outputs: list[str],
    open_questions: list[str],
) -> str:
    if input_source_type == "openfoam_case_seed":
        geometry_text = (
            f"官方 OpenFOAM case `{official_case_id}`"
            if official_case_id
            else "当前已检测到官方 OpenFOAM case seed"
        )
    else:
        geometry_text = (
            f"几何文件 `{geometry_virtual_path}`"
            if geometry_virtual_path
            else "当前尚未绑定具体几何文件"
        )
    family_text = f"，潜艇家族线索为 `{geometry_family_hint}`" if geometry_family_hint else ""
    case_text = f"，建议基线案例为 `{selected_case_id}`" if selected_case_id else ""
    outputs_text = f"目标交付物包含 {len(expected_outputs)} 项" if expected_outputs else "交付物仍待进一步细化"
    confirmation_text = "方案已基本确认，可进入几何预检" if confirmation_status == "confirmed" else "方案仍在澄清中"
    open_questions_text = f"，还有 {len(open_questions)} 项待确认" if open_questions else ""
    return f"已整理 CFD 设计简报：{task_description}。{geometry_text}{family_text}{case_text}。{outputs_text}，{confirmation_text}{open_questions_text}。"


def _resolve_run_basis(
    *,
    geometry_virtual_path: str | None,
    official_case_id: str | None,
    task_description: str,
) -> str:
    if geometry_virtual_path:
        return geometry_virtual_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if official_case_id:
        return official_case_id
    return task_description


def _infer_iteration_mode(
    *,
    previous_contract_revision: int | None,
    existing_custom_variants: list[dict] | None,
) -> str:
    if existing_custom_variants:
        return "derive_variant"
    if isinstance(previous_contract_revision, int) and previous_contract_revision > 0:
        return "revise_baseline"
    return "baseline"


def _resolve_approval_state(
    *,
    confirmation_status: str,
    open_questions: list[str],
) -> str:
    if confirmation_status == "confirmed" and not open_questions:
        return "approved"
    return "needs_confirmation"


def _resolve_goal_status(*, approval_state: str) -> str:
    return "ready_for_execution" if approval_state == "approved" else "planning"


def _render_markdown(payload: dict) -> str:
    requested_outputs = "\n".join((f"- `{item['output_id']}` | {item['label']} | requested=`{item['requested_label']}` | support=`{item['support_level']}`") for item in payload.get("requested_outputs") or []) or "- 暂无"
    expected_outputs = "\n".join(f"- {item}" for item in payload["expected_outputs"]) or "- 暂无"
    user_constraints = "\n".join(f"- {item}" for item in payload["user_constraints"]) or "- 暂无"
    open_questions = "\n".join(f"- {item}" for item in payload["open_questions"]) or "- 暂无"
    execution_outline = "\n".join((f"- `{item['role_id']}` / {item['owner']} / `{item['status']}`：{item['goal']}") for item in payload["execution_outline"])
    lines = [
        f"# {payload['report_title']}",
        "",
        "## 中文摘要",
        payload["summary_zh"],
        "",
        "## 任务定义",
        f"- 任务目标：`{payload['task_description']}`",
        f"- 任务类型：`{payload['task_type']}`",
        f"- 确认状态：`{payload['confirmation_status']}`",
        f"- 输入来源：`{payload.get('input_source_type') or 'geometry_seed'}`",
        f"- 几何路径：`{payload.get('geometry_virtual_path') or '待上传 / 待绑定'}`",
        f"- 官方案例：`{payload.get('official_case_id') or '未提供'}`",
        f"- 几何家族线索：`{payload.get('geometry_family_hint') or '待确认'}`",
        f"- 选定案例：`{payload.get('selected_case_id') or '待确认'}`",
    ]

    simulation_requirements = payload.get("simulation_requirements") or {}
    if simulation_requirements:
        lines.extend(
            [
                "",
                "## 计算要求",
                f"- inlet_velocity_mps: `{simulation_requirements.get('inlet_velocity_mps')}`",
                f"- fluid_density_kg_m3: `{simulation_requirements.get('fluid_density_kg_m3')}`",
                f"- kinematic_viscosity_m2ps: `{simulation_requirements.get('kinematic_viscosity_m2ps')}`",
                f"- end_time_seconds: `{simulation_requirements.get('end_time_seconds')}`",
                f"- delta_t_seconds: `{simulation_requirements.get('delta_t_seconds')}`",
                f"- write_interval_steps: `{simulation_requirements.get('write_interval_steps')}`",
            ]
        )

    lines.extend(
        [
            "",
            "## 预期交付物",
            expected_outputs,
            "",
            "## 用户约束",
            user_constraints,
            "",
            "## 待确认项",
            open_questions,
            "",
            "## 执行分工",
            execution_outline,
            "",
            "## 下一步",
            f"- review_status: `{payload['review_status']}`",
            f"- next_recommended_stage: `{payload['next_recommended_stage']}`",
            f"- report_virtual_path: `{payload['report_virtual_path']}`",
            "",
        ]
    )
    insertion_index = next(
        (index for index, value in enumerate(lines) if value == user_constraints),
        None,
    )
    if insertion_index is not None:
        lines[insertion_index:insertion_index] = [
            "",
            "## Requested Outputs",
            requested_outputs,
        ]
    return "\n".join(lines)


def _render_html(payload: dict) -> str:
    requested_outputs = (
        "".join(
            (f"<li><strong>{escape(item['label'])}</strong> (<code>{escape(item['output_id'])}</code>)<br />requested: {escape(item['requested_label'])}<br />support: <code>{escape(item['support_level'])}</code></li>")
            for item in payload.get("requested_outputs") or []
        )
        or "<li>暂无</li>"
    )
    expected_outputs = "".join(f"<li>{escape(item)}</li>" for item in payload["expected_outputs"]) or "<li>暂无</li>"
    user_constraints = "".join(f"<li>{escape(item)}</li>" for item in payload["user_constraints"]) or "<li>暂无</li>"
    open_questions = "".join(f"<li>{escape(item)}</li>" for item in payload["open_questions"]) or "<li>暂无</li>"
    execution_outline = "".join((f"<li><strong>{escape(item['role_id'])}</strong> / {escape(item['owner'])} / <code>{escape(item['status'])}</code><br />{escape(item['goal'])}</li>") for item in payload["execution_outline"])

    requirements = payload.get("simulation_requirements") or {}
    requirements_html = ""
    if requirements:
        requirements_html = (
            '<section class="panel"><h2>计算要求</h2>'
            f"<p><strong>inlet_velocity_mps:</strong> {escape(str(requirements.get('inlet_velocity_mps')))}</p>"
            f"<p><strong>fluid_density_kg_m3:</strong> {escape(str(requirements.get('fluid_density_kg_m3')))}</p>"
            f"<p><strong>kinematic_viscosity_m2ps:</strong> {escape(str(requirements.get('kinematic_viscosity_m2ps')))}</p>"
            f"<p><strong>end_time_seconds:</strong> {escape(str(requirements.get('end_time_seconds')))}</p>"
            f"<p><strong>delta_t_seconds:</strong> {escape(str(requirements.get('delta_t_seconds')))}</p>"
            f"<p><strong>write_interval_steps:</strong> {escape(str(requirements.get('write_interval_steps')))}</p>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(payload["report_title"])}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Segoe UI", "PingFang SC", sans-serif;
        background: #f6f3ee;
        color: #1f1a15;
      }}
      main {{
        max-width: 960px;
        margin: 0 auto;
      }}
      .panel {{
        background: #fffdfa;
        border: 1px solid #e4d8c7;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 18px;
      }}
      h1, h2 {{
        margin-top: 0;
      }}
      ul {{
        margin: 0;
        padding-left: 18px;
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <h1>{escape(payload["report_title"])}</h1>
        <p>{escape(payload["summary_zh"])}</p>
      </section>
      <section class="panel">
        <h2>任务定义</h2>
        <p><strong>任务目标:</strong> {escape(payload["task_description"])}</p>
        <p><strong>任务类型:</strong> {escape(payload["task_type"])}</p>
        <p><strong>确认状态:</strong> {escape(payload["confirmation_status"])}</p>
        <p><strong>输入来源:</strong> {escape(str(payload.get("input_source_type") or "geometry_seed"))}</p>
        <p><strong>几何路径:</strong> {escape(str(payload.get("geometry_virtual_path") or "待上传 / 待绑定"))}</p>
        <p><strong>官方案例:</strong> {escape(str(payload.get("official_case_id") or "未提供"))}</p>
        <p><strong>几何家族线索:</strong> {escape(str(payload.get("geometry_family_hint") or "待确认"))}</p>
        <p><strong>选定案例:</strong> {escape(str(payload.get("selected_case_id") or "待确认"))}</p>
      </section>
      {requirements_html}
      <section class="panel">
        <h2>预期交付物</h2>
        <ul>{expected_outputs}</ul>
      </section>
      <section class="panel">
        <h2>Requested Outputs</h2>
        <ul>{requested_outputs}</ul>
      </section>
      <section class="panel">
        <h2>用户约束</h2>
        <ul>{user_constraints}</ul>
      </section>
      <section class="panel">
        <h2>待确认项</h2>
        <ul>{open_questions}</ul>
      </section>
      <section class="panel">
        <h2>执行分工</h2>
        <ul>{execution_outline}</ul>
      </section>
    </main>
  </body>
</html>
"""


def _render_markdown_v2(payload: dict) -> str:
    requested_outputs = "\n".join((f"- `{item['output_id']}` | {item['label']} | requested=`{item['requested_label']}` | support=`{item['support_level']}`") for item in payload.get("requested_outputs") or []) or "- 暂无"
    expected_outputs = "\n".join(f"- {item}" for item in payload.get("expected_outputs") or []) or "- 暂无"
    scientific_verification_requirements = "\n".join((f"- `{item['requirement_id']}` | {item['label']} | check=`{item['check_type']}`") for item in payload.get("scientific_verification_requirements") or []) or "- 暂无"
    user_constraints = "\n".join(f"- {item}" for item in payload.get("user_constraints") or []) or "- 暂无"
    open_questions = "\n".join(f"- {item}" for item in payload.get("open_questions") or []) or "- 暂无"
    execution_outline = "\n".join((f"- `{item['role_id']}` / {item['owner']} / `{item['status']}`: {item['goal']}") for item in payload.get("execution_outline") or []) or "- 暂无"

    lines = [
        f"# {payload['report_title']}",
        "",
        "## 中文摘要",
        payload["summary_zh"],
        "",
        "## 任务定义",
        f"- task_description: `{payload['task_description']}`",
        f"- task_type: `{payload['task_type']}`",
        f"- confirmation_status: `{payload['confirmation_status']}`",
        f"- input_source_type: `{payload.get('input_source_type') or 'geometry_seed'}`",
        f"- geometry_virtual_path: `{payload.get('geometry_virtual_path') or '待上传 / 待绑定'}`",
        f"- official_case_id: `{payload.get('official_case_id') or '未提供'}`",
        f"- geometry_family_hint: `{payload.get('geometry_family_hint') or '待确认'}`",
        f"- selected_case_id: `{payload.get('selected_case_id') or '待确认'}`",
    ]
    simulation_requirements = payload.get("simulation_requirements") or {}
    if simulation_requirements:
        lines.extend(
            [
                "",
                "## 计算要求",
                f"- inlet_velocity_mps: `{simulation_requirements.get('inlet_velocity_mps')}`",
                f"- fluid_density_kg_m3: `{simulation_requirements.get('fluid_density_kg_m3')}`",
                f"- kinematic_viscosity_m2ps: `{simulation_requirements.get('kinematic_viscosity_m2ps')}`",
                f"- end_time_seconds: `{simulation_requirements.get('end_time_seconds')}`",
                f"- delta_t_seconds: `{simulation_requirements.get('delta_t_seconds')}`",
                f"- write_interval_steps: `{simulation_requirements.get('write_interval_steps')}`",
            ]
        )

    lines.extend(
        [
            "",
            "## 预期交付物",
            expected_outputs,
            "",
            "## Requested Outputs",
            requested_outputs,
            "",
            "## 科研验证要求",
            scientific_verification_requirements,
            "",
            "## 用户约束",
            user_constraints,
            "",
            "## 待确认项",
            open_questions,
            "",
            "## 执行分工",
            execution_outline,
            "",
            "## 下一步",
            f"- review_status: `{payload['review_status']}`",
            f"- next_recommended_stage: `{payload['next_recommended_stage']}`",
            f"- report_virtual_path: `{payload['report_virtual_path']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _render_html_v2(payload: dict) -> str:
    requested_outputs = (
        "".join(
            (f"<li><strong>{escape(item['label'])}</strong> (<code>{escape(item['output_id'])}</code>)<br />requested: {escape(item['requested_label'])}<br />support: <code>{escape(item['support_level'])}</code></li>")
            for item in payload.get("requested_outputs") or []
        )
        or "<li>暂无</li>"
    )
    expected_outputs = "".join(f"<li>{escape(item)}</li>" for item in payload.get("expected_outputs") or []) or "<li>暂无</li>"
    scientific_verification_requirements = (
        "".join(
            (f"<li><strong>{escape(item['label'])}</strong> (<code>{escape(item['requirement_id'])}</code>)<br />check: <code>{escape(item['check_type'])}</code></li>") for item in payload.get("scientific_verification_requirements") or []
        )
        or "<li>暂无</li>"
    )
    user_constraints = "".join(f"<li>{escape(item)}</li>" for item in payload.get("user_constraints") or []) or "<li>暂无</li>"
    open_questions = "".join(f"<li>{escape(item)}</li>" for item in payload.get("open_questions") or []) or "<li>暂无</li>"
    execution_outline = (
        "".join((f"<li><strong>{escape(item['role_id'])}</strong> / {escape(item['owner'])} / <code>{escape(item['status'])}</code><br />{escape(item['goal'])}</li>") for item in payload.get("execution_outline") or []) or "<li>暂无</li>"
    )

    requirements = payload.get("simulation_requirements") or {}
    requirements_html = ""
    if requirements:
        requirements_html = (
            '<section class="panel"><h2>计算要求</h2>'
            f"<p><strong>inlet_velocity_mps:</strong> {escape(str(requirements.get('inlet_velocity_mps')))}</p>"
            f"<p><strong>fluid_density_kg_m3:</strong> {escape(str(requirements.get('fluid_density_kg_m3')))}</p>"
            f"<p><strong>kinematic_viscosity_m2ps:</strong> {escape(str(requirements.get('kinematic_viscosity_m2ps')))}</p>"
            f"<p><strong>end_time_seconds:</strong> {escape(str(requirements.get('end_time_seconds')))}</p>"
            f"<p><strong>delta_t_seconds:</strong> {escape(str(requirements.get('delta_t_seconds')))}</p>"
            f"<p><strong>write_interval_steps:</strong> {escape(str(requirements.get('write_interval_steps')))}</p>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(payload["report_title"])}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Segoe UI", "PingFang SC", sans-serif;
        background: #f6f3ee;
        color: #1f1a15;
      }}
      main {{
        max-width: 960px;
        margin: 0 auto;
      }}
      .panel {{
        background: #fffdfa;
        border: 1px solid #e4d8c7;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 18px;
      }}
      h1, h2 {{
        margin-top: 0;
      }}
      ul {{
        margin: 0;
        padding-left: 18px;
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <h1>{escape(payload["report_title"])}</h1>
        <p>{escape(payload["summary_zh"])}</p>
      </section>
      <section class="panel">
        <h2>任务定义</h2>
        <p><strong>task_description:</strong> {escape(payload["task_description"])}</p>
        <p><strong>task_type:</strong> {escape(payload["task_type"])}</p>
        <p><strong>confirmation_status:</strong> {escape(payload["confirmation_status"])}</p>
        <p><strong>input_source_type:</strong> {escape(str(payload.get("input_source_type") or "geometry_seed"))}</p>
        <p><strong>geometry_virtual_path:</strong> {escape(str(payload.get("geometry_virtual_path") or "待上传 / 待绑定"))}</p>
        <p><strong>official_case_id:</strong> {escape(str(payload.get("official_case_id") or "未提供"))}</p>
        <p><strong>geometry_family_hint:</strong> {escape(str(payload.get("geometry_family_hint") or "待确认"))}</p>
        <p><strong>selected_case_id:</strong> {escape(str(payload.get("selected_case_id") or "待确认"))}</p>
      </section>
      {requirements_html}
      <section class="panel">
        <h2>预期交付物</h2>
        <ul>{expected_outputs}</ul>
      </section>
      <section class="panel">
        <h2>Requested Outputs</h2>
        <ul>{requested_outputs}</ul>
      </section>
      <section class="panel">
        <h2>科研验证要求</h2>
        <ul>{scientific_verification_requirements}</ul>
      </section>
      <section class="panel">
        <h2>用户约束</h2>
        <ul>{user_constraints}</ul>
      </section>
      <section class="panel">
        <h2>待确认项</h2>
        <ul>{open_questions}</ul>
      </section>
      <section class="panel">
        <h2>执行分工</h2>
        <ul>{execution_outline}</ul>
      </section>
    </main>
  </body>
</html>
"""


def run_design_brief(
    *,
    outputs_dir: Path,
    task_description: str,
    task_type: str,
    confirmation_status: str,
    execution_preference: str,
    input_source_type: str = "geometry_seed",
    geometry_virtual_path: str | None,
    official_case_id: str | None = None,
    official_case_seed_virtual_paths: list[str] | None = None,
    official_case_profile: dict[str, object] | None = None,
    geometry_family_hint: str | None,
    selected_case_id: str | None,
    inlet_velocity_mps: float | None,
    fluid_density_kg_m3: float | None,
    kinematic_viscosity_m2ps: float | None,
    end_time_seconds: float | None,
    delta_t_seconds: float | None,
    write_interval_steps: int | None,
    expected_outputs: list[str] | None,
    user_constraints: list[str] | None,
    open_questions: list[str] | None,
    existing_calculation_plan: list[dict] | None = None,
    previous_contract_revision: int | None = None,
    existing_custom_variants: list[dict] | None = None,
    ready_stage_when_confirmed: str | None = None,
) -> tuple[dict, list[str]]:
    if confirmation_status not in {"draft", "confirmed"}:
        raise ValueError("confirmation_status must be either 'draft' or 'confirmed'")

    expected_outputs = [item.strip() for item in expected_outputs or [] if item and item.strip()]
    requested_outputs = resolve_requested_outputs(expected_outputs)
    output_delivery_plan = build_output_delivery_plan(
        requested_outputs,
        stage="task-intelligence",
    )
    capability_gaps = [item for item in requested_outputs if item.get("support_level") != "supported"]
    user_constraints = [item.strip() for item in user_constraints or [] if item and item.strip()]
    open_questions = [item.strip() for item in open_questions or [] if item and item.strip()]
    simulation_requirements = _maybe_resolve_simulation_requirements(
        inlet_velocity_mps=inlet_velocity_mps,
        fluid_density_kg_m3=fluid_density_kg_m3,
        kinematic_viscosity_m2ps=kinematic_viscosity_m2ps,
        end_time_seconds=end_time_seconds,
        delta_t_seconds=delta_t_seconds,
        write_interval_steps=write_interval_steps,
    )

    run_basis = _resolve_run_basis(
        geometry_virtual_path=geometry_virtual_path,
        official_case_id=official_case_id,
        task_description=task_description,
    )
    run_dir_name = _build_run_dir_name(outputs_dir=outputs_dir, run_basis=run_basis)
    report_title = "潜艇 CFD 设计简报"
    report_virtual_path = _artifact_virtual_path(run_dir_name, "cfd-design-brief.md")
    artifact_virtual_paths = [
        _artifact_virtual_path(run_dir_name, "cfd-design-brief.json"),
        report_virtual_path,
        _artifact_virtual_path(run_dir_name, "cfd-design-brief.html"),
    ]
    approval_state = _resolve_approval_state(
        confirmation_status=confirmation_status,
        open_questions=open_questions,
    )
    goal_status = _resolve_goal_status(approval_state=approval_state)
    review_status = "ready_for_supervisor" if confirmation_status == "confirmed" and not open_questions else "needs_user_confirmation"
    next_recommended_stage = "geometry-preflight" if review_status == "ready_for_supervisor" else "user-confirmation"
    execution_outline = build_execution_plan(confirmation_status=confirmation_status)
    selected_case = load_case_library().case_index.get(selected_case_id or "")
    scientific_verification_requirements = [
        item.model_dump(mode="json")
        for item in build_effective_scientific_verification_requirements(
            acceptance_profile=selected_case.acceptance_profile if selected_case else None,
            task_type=task_type,
        )
    ]
    contract_revision = previous_contract_revision + 1 if isinstance(previous_contract_revision, int) and previous_contract_revision > 0 else 1
    iteration_mode = _infer_iteration_mode(
        previous_contract_revision=previous_contract_revision,
        existing_custom_variants=existing_custom_variants,
    )
    revision_summary = "Updated the structured CFD design brief." if contract_revision > 1 else "Initialized the structured CFD design brief."
    unresolved_decisions = [
        {
            "decision_id": f"open-question-{index + 1}",
            "label": question,
            "source": "open_question",
            "status": "pending_user_confirmation",
        }
        for index, question in enumerate(open_questions)
    ]
    unresolved_decisions.extend(
        {
            "decision_id": f"capability-gap-{item['output_id']}",
            "label": (f"Confirm whether the current support boundary for {item.get('requested_label') or item.get('label') or item['output_id']} is acceptable."),
            "source": "capability_gap",
            "status": "pending_user_confirmation",
            "output_id": item["output_id"],
        }
        for item in capability_gaps
    )
    evidence_expectations = [
        {
            "expectation_id": item["requirement_id"],
            "kind": item["check_type"],
            "label": item["label"],
        }
        for item in scientific_verification_requirements
    ]
    variant_policy = {
        "default_compare_target_run_id": "baseline",
        "allow_custom_variants": True,
        "custom_variant_count": len(existing_custom_variants or []),
    }
    calculation_plan = build_design_brief_calculation_plan(
        existing=existing_calculation_plan,
        confirmation_status=confirmation_status,
        selected_case_id=selected_case_id,
        simulation_requirements=simulation_requirements,
    )
    summary_zh = _compose_summary(
        task_description=task_description,
        input_source_type=input_source_type,
        geometry_virtual_path=geometry_virtual_path,
        official_case_id=official_case_id,
        geometry_family_hint=geometry_family_hint,
        confirmation_status=confirmation_status,
        selected_case_id=selected_case_id,
        expected_outputs=expected_outputs,
        open_questions=open_questions,
    )
    payload = {
        "report_title": report_title,
        "summary_zh": summary_zh,
        "task_description": task_description,
        "task_type": task_type,
        "confirmation_status": confirmation_status,
        "approval_state": approval_state,
        "goal_status": goal_status,
        "execution_preference": execution_preference,
        "contract_revision": contract_revision,
        "iteration_mode": iteration_mode,
        "revision_summary": revision_summary,
        "input_source_type": input_source_type,
        "geometry_virtual_path": geometry_virtual_path,
        "official_case_id": official_case_id,
        "official_case_seed_virtual_paths": list(official_case_seed_virtual_paths or []),
        "official_case_profile": official_case_profile,
        "geometry_family_hint": geometry_family_hint,
        "selected_case_id": selected_case_id,
        "simulation_requirements": simulation_requirements,
        "expected_outputs": expected_outputs,
        "scientific_verification_requirements": scientific_verification_requirements,
        "requested_outputs": requested_outputs,
        "output_delivery_plan": output_delivery_plan,
        "capability_gaps": capability_gaps,
        "unresolved_decisions": unresolved_decisions,
        "evidence_expectations": evidence_expectations,
        "variant_policy": variant_policy,
        "user_constraints": user_constraints,
        "open_questions": open_questions,
        "calculation_plan": calculation_plan,
        "execution_outline": execution_outline,
        "review_status": review_status,
        "stage_hints": {
            "current": "task-intelligence",
            "suggested_next": (ready_stage_when_confirmed or next_recommended_stage if review_status == "ready_for_supervisor" else next_recommended_stage),
        },
        "next_recommended_stage": (ready_stage_when_confirmed or next_recommended_stage if review_status == "ready_for_supervisor" else next_recommended_stage),
        "report_virtual_path": report_virtual_path,
        "artifact_virtual_paths": artifact_virtual_paths,
    }

    run_dir = outputs_dir / "submarine" / "design-brief" / run_dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "cfd-design-brief.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "cfd-design-brief.md").write_text(
        _render_markdown_v2(payload),
        encoding="utf-8",
    )
    (run_dir / "cfd-design-brief.html").write_text(
        _render_html_v2(payload),
        encoding="utf-8",
    )

    return payload, artifact_virtual_paths
