"""Normalize user-requested submarine CFD outputs and track delivery status."""

from __future__ import annotations

import re
from typing import Literal

from .contracts import SubmarineOutputDeliveryItem, SubmarineRequestedOutput

SupportLevel = Literal["supported", "not_yet_supported", "needs_clarification"]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "custom_output"


_OUTPUT_CATALOG: tuple[dict, ...] = (
    {
        "output_id": "design_brief",
        "label": "设计简报",
        "aliases": ("设计简报", "cfd 设计简报", "cfd design brief", "design brief"),
        "inference_aliases": (
            "整理设计简报",
            "生成设计简报",
            "输出设计简报",
            "交付设计简报",
            "cfd design brief",
        ),
        "support_level": "supported",
        "notes": "当前运行时可交付结构化 CFD 设计简报。",
    },
    {
        "output_id": "assembled_openfoam_case",
        "label": "按默认设置组装的最小 OpenFOAM 案例",
        "aliases": (
            "按默认设置组装的最小 openfoam 案例",
            "默认组装后的 openfoam 最小案例",
            "默认组装后的 openfoam 最小 cavity 案例",
            "组装的最小 openfoam 案例",
            "最小 openfoam 案例",
            "案例组装摘要",
            "案例组装",
            "组装摘要",
            "assembled openfoam case",
            "assembled case",
        ),
        "support_level": "supported",
        "notes": "当前运行时可交付可直接查看和复跑的最小 OpenFOAM 案例骨架。",
    },
    {
        "output_id": "drag_coefficient",
        "label": "阻力系数 Cd",
        "aliases": ("阻力系数", "阻力系数 cd", "cd", "drag coefficient"),
        "support_level": "supported",
        "notes": "当前运行时可直接交付结构化阻力系数结果。",
    },
    {
        "output_id": "force_breakdown",
        "label": "受力分解",
        "aliases": ("受力分解", "力分解", "force breakdown", "drag breakdown"),
        "support_level": "supported",
        "notes": "当前运行时可交付压力力与黏性力等结构化受力分解结果。",
    },
    {
        "output_id": "mesh_quality_summary",
        "label": "网格质量摘要",
        "aliases": ("网格质量", "网格质量摘要", "mesh quality", "mesh quality summary"),
        "support_level": "supported",
        "notes": "当前运行时可交付网格质量摘要。",
    },
    {
        "output_id": "residual_history",
        "label": "残差收敛摘要",
        "aliases": ("残差", "残差历史", "残差收敛", "收敛历史", "residual history"),
        "support_level": "supported",
        "notes": "当前运行时可交付残差摘要与收敛信息。",
    },
    {
        "output_id": "benchmark_comparison",
        "label": "Benchmark 对比",
        "aliases": ("benchmark 对比", "benchmark comparison", "基准对比", "benchmark对比"),
        "support_level": "supported",
        "notes": "当前运行时在命中案例基准时可交付 benchmark 对比。",
    },
    {
        "output_id": "chinese_report",
        "label": "中文结果报告",
        "aliases": ("中文报告", "中文结果报告", "中文最终报告", "结果报告", "chinese report"),
        "support_level": "supported",
        "notes": "当前运行时可交付中文结构化最终报告。",
    },
    {
        "output_id": "solver_execution_summary",
        "label": "结果摘要",
        "aliases": (
            "结果摘要",
            "执行结果",
            "求解结果摘要",
            "求解执行结果摘要",
            "求解日志与关键收敛信息",
            "求解运行日志",
            "solver-results.json",
            "solver summary",
            "execution summary",
        ),
        "support_level": "supported",
        "notes": "当前运行时可交付求解执行摘要、关键收敛信息以及运行日志索引。",
    },
    {
        "output_id": "surface_pressure_contour",
        "label": "表面压力云图",
        "aliases": (
            "表面压力云图",
            "压力云图",
            "表面压力图",
            "pressure contour",
            "pressure distribution",
            "surface pressure map",
        ),
        "support_level": "supported",
        "default_postprocess_spec": {
            "field": "p",
            "time_mode": "latest",
            "selector": {
                "type": "patch",
                "patches": ["hull"],
            },
            "formats": ["csv", "png", "report"],
        },
        "notes": "当前运行时可在存在后处理文件时导出表面压力结果 artifact。",
    },
    {
        "output_id": "streamlines",
        "label": "流线图",
        "aliases": ("流线图", "流线", "streamlines", "streamline view"),
        "support_level": "not_yet_supported",
        "notes": "当前仓库尚未自动导出流线图 artifact。",
    },
    {
        "output_id": "wake_velocity_slice",
        "label": "尾流速度切片",
        "aliases": (
            "尾流速度切片",
            "尾流图",
            "流场信息",
            "速度切片",
            "wake field",
            "wake slice",
            "velocity slice",
            "flow visualization",
        ),
        "support_level": "supported",
        "default_postprocess_spec": {
            "field": "U",
            "time_mode": "latest",
            "selector": {
                "type": "plane",
                "origin_mode": "x_by_lref",
                "origin_value": 1.25,
                "normal": [1.0, 0.0, 0.0],
            },
            "formats": ["csv", "png", "report"],
        },
        "notes": "当前运行时可在存在后处理文件时导出尾流速度切片 artifact。",
    },
)


_OUTPUT_ARTIFACT_SUFFIXES: dict[str, tuple[str, ...]] = {
    "design_brief": (
        "/cfd-design-brief.md",
        "/cfd-design-brief.html",
        "/cfd-design-brief.json",
    ),
    "assembled_openfoam_case": (
        "/openfoam-case/Allrun",
        "/openfoam-case/system/blockMeshDict",
        "/openfoam-case/system/controlDict",
    ),
    "solver_execution_summary": (
        "/dispatch-summary.md",
        "/dispatch-summary.html",
        "/solver-results.md",
        "/solver-results.json",
        "/openfoam-run.log",
    ),
    "surface_pressure_contour": (
        "/surface-pressure.csv",
        "/surface-pressure.png",
        "/surface-pressure.md",
    ),
    "wake_velocity_slice": (
        "/wake-velocity-slice.csv",
        "/wake-velocity-slice.png",
        "/wake-velocity-slice.md",
    ),
    "chinese_report": ("/final-report.md", "/final-report.html", "/final-report.json"),
    "drag_coefficient": ("/solver-results.json",),
    "force_breakdown": ("/solver-results.json",),
    "mesh_quality_summary": ("/solver-results.json",),
    "residual_history": ("/solver-results.json",),
    "benchmark_comparison": ("/final-report.json", "/delivery-readiness.json"),
}


def _match_catalog_item(requested_label: str) -> dict | None:
    lowered = requested_label.lower()
    return next(
        (item for item in _OUTPUT_CATALOG if any(alias in lowered for alias in item["aliases"])),
        None,
    )


def _normalize_expected_outputs(expected_outputs: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for raw_item in expected_outputs or []:
        requested_label = raw_item.strip()
        if not requested_label or requested_label in normalized:
            continue
        normalized.append(requested_label)
    return normalized


def infer_expected_outputs_from_text(task_description: str | None) -> list[str]:
    """Infer structured output labels from free-form user task descriptions."""

    if not task_description or not task_description.strip():
        return []

    lowered = task_description.lower()
    matches: list[tuple[int, str]] = []
    seen_labels: set[str] = set()

    for item in _OUTPUT_CATALOG:
        aliases = item.get("inference_aliases", item["aliases"])
        positions = [lowered.find(alias.lower()) for alias in aliases if alias and lowered.find(alias.lower()) >= 0]
        if not positions:
            continue

        label = item["label"]
        if label in seen_labels:
            continue

        seen_labels.add(label)
        matches.append((min(positions), label))

    matches.sort(key=lambda pair: (pair[0], pair[1]))
    return [label for _, label in matches]


def resolve_effective_expected_outputs(
    *,
    existing_outputs: list[str] | None,
    explicit_outputs: list[str] | None,
    task_description: str | None,
) -> list[str]:
    """Resolve the effective expected-output list for a design-brief revision."""

    if explicit_outputs is not None:
        return _normalize_expected_outputs(explicit_outputs)

    merged = _normalize_expected_outputs(existing_outputs)
    for inferred in infer_expected_outputs_from_text(task_description):
        if inferred not in merged:
            merged.append(inferred)
    return merged


def resolve_requested_outputs(expected_outputs: list[str] | None) -> list[dict]:
    """Normalize free-form expected outputs into a structured requested-output list."""

    normalized: list[dict] = []
    seen_output_ids: set[str] = set()

    for requested_label in _normalize_expected_outputs(expected_outputs):
        matched = _match_catalog_item(requested_label)
        if matched is None:
            output_id = f"custom_{_slugify(requested_label)}"
            if output_id in seen_output_ids:
                continue
            seen_output_ids.add(output_id)
            normalized.append(
                SubmarineRequestedOutput(
                    output_id=output_id,
                    label=requested_label,
                    requested_label=requested_label,
                    support_level="needs_clarification",
                    notes=("当前版本尚未识别该输出类型，建议由 Claude Code 改写成受支持的结构化输出项。"),
                ).model_dump(mode="json")
            )
            continue

        output_id = matched["output_id"]
        if output_id in seen_output_ids:
            continue
        seen_output_ids.add(output_id)
        normalized.append(
            SubmarineRequestedOutput(
                output_id=output_id,
                label=matched["label"],
                requested_label=requested_label,
                support_level=matched["support_level"],
                postprocess_spec=matched.get("default_postprocess_spec"),
                notes=matched["notes"],
            ).model_dump(mode="json")
        )

    return normalized


def _matching_artifacts(artifact_virtual_paths: list[str], *suffixes: str) -> list[str]:
    return [path for path in artifact_virtual_paths if any(path.endswith(suffix) for suffix in suffixes)]


def build_output_delivery_plan(
    requested_outputs: list[SubmarineRequestedOutput | dict] | None,
    *,
    stage: str,
    solver_metrics: dict | None = None,
    artifact_virtual_paths: list[str] | None = None,
    acceptance_assessment: dict | None = None,
) -> list[dict]:
    """Map requested outputs to concrete delivery status for the current runtime stage."""

    artifacts = artifact_virtual_paths or []
    acceptance = acceptance_assessment or {}
    normalized = [SubmarineRequestedOutput.model_validate(item) for item in (requested_outputs or [])]
    delivery_items: list[dict] = []

    for item in normalized:
        if item.support_level != "supported":
            delivery_items.append(
                SubmarineOutputDeliveryItem(
                    output_id=item.output_id,
                    label=item.label,
                    delivery_status="not_yet_supported",
                    detail=item.notes or "当前仓库尚未自动交付该输出。",
                ).model_dump(mode="json")
            )
            continue

        delivery_status: str = "planned"
        detail = "该输出已纳入本次 run 的交付计划。"
        linked_artifacts: list[str] = []

        if item.output_id == "design_brief":
            linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["design_brief"])
            if linked_artifacts:
                delivery_status = "delivered"
                detail = "已生成结构化 CFD 设计简报。"
            elif stage in {"solver-dispatch", "result-reporting"}:
                delivery_status = "pending"
                detail = "设计简报应已生成，但当前 artifact 视图里还没有找到对应文件。"
        elif item.output_id == "assembled_openfoam_case":
            linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["assembled_openfoam_case"])
            if linked_artifacts:
                delivery_status = "delivered"
                detail = "已组装可复跑的最小 OpenFOAM 案例骨架。"
            elif stage == "result-reporting":
                delivery_status = "pending"
                detail = "结果报告阶段尚未在 artifact 视图中找到组装后的 OpenFOAM 案例入口。"
        elif item.output_id == "drag_coefficient":
            cd = ((solver_metrics or {}).get("latest_force_coefficients") or {}).get("Cd")
            if isinstance(cd, (int, float)):
                delivery_status = "delivered"
                detail = f"已提取 Cd = {float(cd):.5f}。"
                linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["drag_coefficient"])
            elif solver_metrics:
                delivery_status = "not_available_for_this_run"
                detail = "本次 run 已有 solver metrics，但未提取到 Cd。"
            elif stage == "result-reporting":
                delivery_status = "pending"
                detail = "结果报告阶段尚未拿到 solver metrics。"
        elif item.output_id == "force_breakdown":
            total_force = ((solver_metrics or {}).get("latest_forces") or {}).get("total_force")
            if total_force:
                delivery_status = "delivered"
                detail = "已提取压力力与黏性力等受力分解结果。"
                linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["force_breakdown"])
            elif solver_metrics:
                delivery_status = "not_available_for_this_run"
                detail = "本次 run 未提取到受力分解结果。"
            elif stage == "result-reporting":
                delivery_status = "pending"
                detail = "结果报告阶段尚未拿到 solver metrics。"
        elif item.output_id == "mesh_quality_summary":
            if (solver_metrics or {}).get("mesh_summary"):
                delivery_status = "delivered"
                detail = "已提取网格质量摘要。"
                linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["mesh_quality_summary"])
            elif solver_metrics:
                delivery_status = "not_available_for_this_run"
                detail = "本次 run 未提取到网格质量摘要。"
        elif item.output_id == "residual_history":
            if (solver_metrics or {}).get("residual_summary"):
                delivery_status = "delivered"
                detail = "已提取残差收敛摘要。"
                linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["residual_history"])
            elif solver_metrics:
                delivery_status = "not_available_for_this_run"
                detail = "本次 run 未提取到残差收敛摘要。"
        elif item.output_id == "benchmark_comparison":
            benchmark_comparisons = acceptance.get("benchmark_comparisons") or []
            if benchmark_comparisons:
                delivery_status = "delivered"
                detail = "已生成 benchmark comparison。"
                linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["benchmark_comparison"])
            elif solver_metrics:
                delivery_status = "not_available_for_this_run"
                detail = "当前 run 未命中可交付的 benchmark comparison。"
            elif stage == "result-reporting":
                delivery_status = "pending"
                detail = "结果报告阶段尚未拿到 solver metrics。"
        elif item.output_id == "chinese_report":
            linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["chinese_report"])
            if linked_artifacts:
                delivery_status = "delivered"
                detail = "已生成中文结果报告。"
            elif stage == "result-reporting":
                delivery_status = "pending"
                detail = "结果报告生成尚未完成。"
        elif item.output_id == "solver_execution_summary":
            linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["solver_execution_summary"])
            if linked_artifacts:
                delivery_status = "delivered"
                detail = "已生成求解执行摘要、关键收敛信息或运行日志索引。"
            elif stage in {"solver-dispatch", "result-reporting"}:
                delivery_status = "pending"
                detail = "求解阶段已启动，但当前 artifact 视图中还没有找到结果摘要或运行日志。"
        elif item.output_id == "surface_pressure_contour":
            linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["surface_pressure_contour"])
            if linked_artifacts:
                delivery_status = "delivered"
                detail = "已导出表面压力结果 artifact。"
            elif solver_metrics:
                delivery_status = "not_available_for_this_run"
                detail = "本次 run 未导出表面压力结果 artifact。"
            elif stage == "result-reporting":
                delivery_status = "pending"
                detail = "结果报告阶段尚未拿到 solver metrics。"
        elif item.output_id == "wake_velocity_slice":
            linked_artifacts = _matching_artifacts(artifacts, *_OUTPUT_ARTIFACT_SUFFIXES["wake_velocity_slice"])
            if linked_artifacts:
                delivery_status = "delivered"
                detail = "已导出尾流速度切片 artifact。"
            elif solver_metrics:
                delivery_status = "not_available_for_this_run"
                detail = "本次 run 未导出尾流速度切片 artifact。"
            elif stage == "result-reporting":
                delivery_status = "pending"
                detail = "结果报告阶段尚未拿到 solver metrics。"

        delivery_items.append(
            SubmarineOutputDeliveryItem(
                output_id=item.output_id,
                label=item.label,
                delivery_status=delivery_status,
                detail=detail,
                artifact_virtual_paths=linked_artifacts,
            ).model_dump(mode="json")
        )

    return delivery_items
