from __future__ import annotations

import json
from pathlib import Path

from ..config import get_settings
from ..models import RunSummary, SkillManifest, WorkflowDraft, WorkflowStage
from ..store import RunStore
from .cases import CaseLibrary


class WorkflowService:
    def __init__(self, case_library: CaseLibrary, store: RunStore) -> None:
        self.case_library = case_library
        self.store = store
        self.settings = get_settings()

    def _load_skills(self) -> dict[str, SkillManifest]:
        payload = json.loads(self.settings.skills_file.read_text(encoding="utf-8"))
        manifests = [SkillManifest.model_validate(item) for item in payload["skills"]]
        return {manifest.skill_id: manifest for manifest in manifests}

    def _build_geometry_check(self, run: RunSummary) -> str:
        suffix = Path(run.request.geometry_file_name or "unknown").suffix.lower().lstrip(".")
        if not suffix:
            return "未上传几何文件，当前流程将按 benchmark 模板生成推荐案例与执行方案。"
        if suffix not in {"stl", "x_t", "step", "stp"}:
            return f"检测到 .{suffix} 文件，当前演示版优先支持 STL / x_t / STEP 几何。"
        return f"检测到 .{suffix} 几何文件，可进入案例映射、人工确认和受控执行流程。"

    def _build_workflow(self, run: RunSummary) -> WorkflowDraft:
        if run.selected_case is None:
            raise RuntimeError("Selected case is required before building a workflow.")

        skill_registry = self._load_skills()
        allowed_tools: list[str] = []
        required_artifacts = [
            "execution/logs/run.log",
            "postprocess/result.json",
            "report/final_report.md",
        ]

        for skill_id in run.selected_case.linked_skills:
            manifest = skill_registry.get(skill_id)
            if manifest:
                allowed_tools.extend(manifest.required_tools)
                required_artifacts.extend(manifest.artifacts_out)

        assumptions = [
            "采用演示版受控 benchmark 模板执行链路。",
            "默认工况按深潜稳态外流场处理。",
            "主控执行器会在固定 skill 边界内生成结果、图表和报告。",
        ]
        if run.request.geometry_family_hint:
            assumptions.append(f"上传几何优先映射到 {run.request.geometry_family_hint} 家族。")

        stages = [
            WorkflowStage(
                stage_id="retrieval",
                title="案例检索",
                description="从结构化案例库中检索候选 benchmark，并给出推荐映射。",
            ),
            WorkflowStage(
                stage_id="geometry_check",
                title="几何检查",
                description="确认上传几何格式、家族映射和模板化执行前提。",
            ),
            WorkflowStage(
                stage_id="execution",
                title="主控执行",
                description="由主控执行器在受控 skill 边界内推进求解与产物生成。",
            ),
            WorkflowStage(
                stage_id="postprocess",
                title="结果整理",
                description="输出几何概览、压力分布、尾流切片和结构化结果。",
            ),
            WorkflowStage(
                stage_id="report",
                title="报告生成",
                description="整理案例依据、关键指标、日志与结论，生成最终展示报告。",
            ),
        ]

        return WorkflowDraft(
            summary=(
                f"已基于 {run.selected_case.title} 生成 {run.request.task_type} 任务流程，"
                "待人工确认后由主控执行器完成几何检查、演示级求解、后处理与报告整理。"
            ),
            assumptions=assumptions,
            recommended_case_ids=[run.selected_case.case_id],
            linked_skills=run.selected_case.linked_skills,
            allowed_tools=sorted(set(allowed_tools)),
            required_artifacts=sorted(set(required_artifacts)),
            stages=stages,
        )

    def _workflow_markdown(self, run: RunSummary, draft: WorkflowDraft) -> str:
        lines = [
            f"# Workflow Draft for {run.run_id}",
            "",
            "## Summary",
            draft.summary,
            "",
            "## Assumptions",
            *[f"- {item}" for item in draft.assumptions],
            "",
            "## Selected Case",
            f"- {run.selected_case.title if run.selected_case else 'N/A'}",
            "",
            "## Allowed Tools",
            *[f"- `{tool}`" for tool in draft.allowed_tools],
            "",
            "## Required Artifacts",
            *[f"- `{item}`" for item in draft.required_artifacts],
        ]
        return "\n".join(lines).strip() + "\n"

    def prepare_run(self, run_id: str) -> RunSummary:
        run = self.store.get_run(run_id)
        result = self.case_library.search(run.request)
        prepared = self.store.prepare_run(
            run_id,
            geometry_check=self._build_geometry_check(run),
            candidate_cases=result.candidates,
            selected_case=result.recommended,
            workflow_draft=WorkflowDraft(summary="", stages=[]),
        )
        draft = self._build_workflow(prepared)
        prepared = self.store.update_run(run_id, workflow_draft=draft)

        run_path = Path(prepared.run_directory)
        (run_path / "retrieval" / "candidate_cases.json").write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in prepared.candidate_cases],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        if prepared.selected_case is None:
            raise RuntimeError("Selected case missing after preparation.")
        (run_path / "retrieval" / "selected_case.json").write_text(
            json.dumps(prepared.selected_case.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (run_path / "retrieval" / "workflow_draft.md").write_text(
            self._workflow_markdown(prepared, draft),
            encoding="utf-8",
        )
        self.store.append_timeline(
            run_id,
            "retrieval",
            f"已生成 {len(prepared.candidate_cases)} 个候选案例，并等待人工确认。",
            "ok",
        )
        return self.store.get_run(run_id)
