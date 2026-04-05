from __future__ import annotations

import json
from pathlib import Path

from ..config import get_settings
from ..executor_protocol import ExecutorTaskRequest, ExecutorTaskResult, ExecutorTimelineEvent
from .artifacts import write_json
from .models import AgentPlan, AgentPlanStep, AgentReport, GeometryInspection
from .provider import CompatibleAgentProvider
from .skills import run_geometry_check, run_report_generation, run_solver_pipeline


TASK_TYPE_LABELS = {
    "pressure_distribution": "压力分布",
    "resistance": "阻力评估",
    "wake_field": "尾流分析",
    "drift_angle_force": "漂角受力分析",
    "near_free_surface": "近自由液面分析",
    "self_propulsion": "自航性能分析",
}

SKILL_STEP_TEMPLATES: dict[str, tuple[str, str]] = {
    "case-search": ("复核案例映射并锁定参考模板。", "案例确认结论"),
    "geometry-check": ("检查几何完整性与家族映射关系。", "几何摘要与格式校验结果"),
    "mesh-prep": ("准备演示级求解案例结构与网格模板。", "案例目录与网格准备说明"),
    "solver-openfoam": ("执行受控求解流程并生成核心数值结果。", "压力、阻力与尾流相关结果"),
    "solver-run": ("执行受控求解流程并生成核心数值结果。", "压力、阻力与尾流相关结果"),
    "postprocess": ("导出图表、结构化结果和展示素材。", "图像、数据表与结果 JSON"),
    "report": ("整理比赛展示版报告与证据链。", "Markdown 报告与摘要清单"),
    "report-generate": ("整理比赛展示版报告与证据链。", "Markdown 报告与摘要清单"),
}


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _task_label(task_type: str) -> str:
    return TASK_TYPE_LABELS.get(task_type, task_type)


def _looks_fragmented(items: list[str]) -> bool:
    if not items:
        return True
    average_length = sum(len(item.strip()) for item in items) / len(items)
    return len(items) > 5 or average_length < 18


class AgentExecutionService:
    def __init__(self, provider: CompatibleAgentProvider | None = None) -> None:
        self.settings = get_settings()
        self.provider = provider or CompatibleAgentProvider(
            base_url=self.settings.agent_model_base_url,
            model=self.settings.agent_model_name,
            api_key=self.settings.agent_model_api_key,
            timeout_seconds=self.settings.agent_model_timeout_seconds,
            temperature=self.settings.agent_model_temperature,
        )

    def _ensure_layout(self, run_path: Path) -> None:
        for relative in (
            "execution/agent_executor",
            "execution/logs",
            "execution/raw_outputs",
            "execution/solver_case",
            "postprocess/images",
            "postprocess/tables",
            "report",
        ):
            (run_path / relative).mkdir(parents=True, exist_ok=True)

    def _plan_system_prompt(self) -> str:
        return (
            "你是潜艇 CFD 工作台中的主控执行器。"
            "你不是通用聊天助手，而是一个面向仿真任务的受控执行代理。"
            "你只能在给定 skill 范围内规划步骤，并且必须输出单个 JSON 对象。"
            "所有自然语言字段尽量使用简体中文。"
            "不要输出 markdown、解释性前言或额外文本。"
        )

    def _plan_user_prompt(self, request: ExecutorTaskRequest) -> str:
        skill_list = ", ".join(
            request.context.linked_skills or ["geometry-check", "solver-run", "report-generate"]
        )
        assumptions = "；".join(request.context.workflow_assumptions) or "无"
        return (
            "请为当前 run 生成比赛展示版执行规划，并严格输出 JSON 对象。\n"
            f"任务描述：{request.context.task_description}\n"
            f"任务类型：{request.context.task_type}\n"
            f"几何家族：{request.context.geometry_family or '未知'}\n"
            f"已选案例：{request.context.selected_case_title or '未知'}\n"
            f"执行目标：{request.goal}\n"
            f"工作流摘要：{request.context.workflow_summary or '待生成'}\n"
            f"工作流假设：{assumptions}\n"
            f"工况说明：{request.context.operating_notes or '未提供'}\n"
            f"允许 skill：{skill_list}\n"
            "输出字段必须包含 mission_title、plan_summary、selected_skills、steps、report_focus。\n"
            "steps 数组中的每个对象必须包含 skill_id、goal、expected_output。"
        )

    def _report_system_prompt(self) -> str:
        return (
            "你是潜艇仿真项目的比赛展示技术报告助手。"
            "请根据几何摘要、执行计划和结果指标生成结构化报告素材。"
            "所有自然语言字段尽量使用简体中文。"
            "必须输出单个 JSON 对象，不要输出 markdown 或额外说明。"
        )

    def _report_user_prompt(
        self,
        request: ExecutorTaskRequest,
        *,
        plan: AgentPlan,
        geometry_summary: dict,
        metrics: dict[str, float | str],
    ) -> str:
        return (
            "请为比赛展示生成报告素材，并严格输出 JSON 对象。\n"
            f"任务描述：{request.context.task_description}\n"
            f"任务类型：{request.context.task_type}\n"
            f"已选案例：{request.context.selected_case_title or '未知'}\n"
            f"执行计划：{json.dumps(plan.model_dump(mode='json'), ensure_ascii=False)}\n"
            f"几何摘要：{geometry_summary}\n"
            f"结果指标：{metrics}\n"
            "输出字段必须包含 report_title、executive_summary、key_findings、verification_notes、next_actions。"
        )

    def _localize_plan(self, request: ExecutorTaskRequest, plan: AgentPlan) -> AgentPlan:
        task_label = _task_label(request.context.task_type)
        selected_case = request.context.selected_case_title or request.context.geometry_family or "当前艇型"
        mission_title = (
            plan.mission_title
            if _contains_chinese(plan.mission_title)
            else f"{selected_case} {task_label}演示任务"
        )
        plan_summary = (
            plan.plan_summary
            if _contains_chinese(plan.plan_summary)
            else (
                f"围绕 {selected_case} 开展{task_label}任务，依次完成案例确认、几何检查、"
                "演示级求解、后处理与比赛展示报告整理。"
            )
        )

        selected_skills = plan.selected_skills or request.context.linked_skills
        localized_steps: list[AgentPlanStep] = []
        source_steps = plan.steps or [AgentPlanStep(skill_id=skill_id, goal="", expected_output="") for skill_id in selected_skills]
        for step in source_steps:
            template_goal, template_output = SKILL_STEP_TEMPLATES.get(
                step.skill_id,
                ("按受控方式推进该阶段任务。", "阶段性结构化结果"),
            )
            localized_steps.append(
                AgentPlanStep(
                    skill_id=step.skill_id,
                    goal=step.goal if _contains_chinese(step.goal) else template_goal,
                    expected_output=(
                        step.expected_output
                        if _contains_chinese(step.expected_output)
                        else template_output
                    ),
                )
            )

        report_focus = [item for item in plan.report_focus if _contains_chinese(item)]
        if not report_focus:
            report_focus = [f"{task_label}结论", "关键指标解释", "证据链归档"]

        return plan.model_copy(
            update={
                "mission_title": mission_title,
                "plan_summary": plan_summary,
                "selected_skills": selected_skills,
                "steps": localized_steps,
                "report_focus": report_focus,
            },
            deep=True,
        )

    def _localize_report(
        self,
        request: ExecutorTaskRequest,
        *,
        plan: AgentPlan,
        report: AgentReport,
        geometry: GeometryInspection,
        metrics: dict[str, float | str],
    ) -> AgentReport:
        task_label = _task_label(request.context.task_type)
        case_title = request.context.selected_case_title or geometry.geometry_family
        drag = metrics.get("drag_newtons", "N/A")
        peak = metrics.get("pressure_peak_kpa", "N/A")
        wake = metrics.get("wake_uniformity", "N/A")

        report_title = (
            report.report_title
            if _contains_chinese(report.report_title)
            else f"{geometry.geometry_family} {task_label}比赛展示报告"
        )
        executive_summary = (
            report.executive_summary
            if _contains_chinese(report.executive_summary)
            else (
                f"本次演示围绕 {case_title} 完成了{task_label}任务。"
                f"主控执行器已依据案例模板组织几何检查、演示级求解与报告归档，"
                f"当前结果显示阻力约为 {drag} N、压力峰值约为 {peak} kPa、尾流均匀性约为 {wake}。"
            )
        )

        key_findings = [item for item in report.key_findings if _contains_chinese(item)]
        if not key_findings or _looks_fragmented(key_findings):
            key_findings = [
                f"已识别上传几何属于 {geometry.geometry_family} 家族，并完成格式与尺度检查。",
                f"已生成 {task_label}核心结果，阻力约为 {drag} N，压力峰值约为 {peak} kPa。",
                f"后处理阶段已输出几何总览图、压力分布图、尾流切片图和阻力表。",
            ]

        verification_notes = [
            item for item in report.verification_notes if _contains_chinese(item)
        ]
        if not verification_notes or _looks_fragmented(verification_notes):
            verification_notes = [
                "主控执行规划、执行日志、结构化结果和最终报告均已回写到 run 目录。",
                "本次展示采用受控 skill 链路，避免了自由发挥式黑盒执行。",
                "图像、数据表和结果 JSON 可作为答辩时的证据链材料。",
            ]

        next_actions = [item for item in report.next_actions if _contains_chinese(item)]
        if not next_actions or _looks_fragmented(next_actions):
            next_actions = [
                "后续可替换为真实 OpenFOAM 求解器与专业后处理脚本。",
                "可补充更多 benchmark 案例与领域校核口径，提升结果可信度。",
            ]

        return report.model_copy(
            update={
                "report_title": report_title,
                "executive_summary": executive_summary,
                "key_findings": key_findings,
                "verification_notes": verification_notes,
                "next_actions": next_actions,
            },
            deep=True,
        )

    def _write_response(self, run_path: Path, result: ExecutorTaskResult) -> None:
        write_json(
            run_path / "execution" / "agent_executor" / "response.json",
            result.model_dump(mode="json"),
        )

    def execute(self, request: ExecutorTaskRequest) -> ExecutorTaskResult:
        run_path = Path(request.run_directory)
        self._ensure_layout(run_path)
        write_json(
            run_path / "execution" / "agent_executor" / "request.json",
            request.model_dump(mode="json"),
        )

        timeline: list[ExecutorTimelineEvent] = [
            ExecutorTimelineEvent(
                stage="execution",
                message="主控执行器已接收结构化执行请求，开始生成执行规划。",
                status="running",
            )
        ]

        try:
            plan_payload = self.provider.complete_json(
                system_prompt=self._plan_system_prompt(),
                user_prompt=self._plan_user_prompt(request),
            )
            plan = self._localize_plan(request, AgentPlan.model_validate(plan_payload))
            write_json(
                run_path / "execution" / "agent_executor" / "plan.json",
                plan.model_dump(mode="json"),
            )
            timeline.append(
                ExecutorTimelineEvent(
                    stage="planning",
                    message=plan.plan_summary,
                    status="running",
                )
            )

            geometry, geometry_result = run_geometry_check(request)
            timeline.append(
                ExecutorTimelineEvent(
                    stage=geometry_result.stage,
                    message=geometry_result.summary,
                    status="running",
                )
            )

            solver_result = run_solver_pipeline(request, geometry=geometry, plan=plan)
            timeline.append(
                ExecutorTimelineEvent(
                    stage=solver_result.stage,
                    message=solver_result.summary,
                    status="running",
                )
            )

            report_payload = self.provider.complete_json(
                system_prompt=self._report_system_prompt(),
                user_prompt=self._report_user_prompt(
                    request,
                    plan=plan,
                    geometry_summary=geometry.model_dump(mode="json"),
                    metrics=solver_result.metrics,
                ),
            )
            report = self._localize_report(
                request,
                plan=plan,
                report=AgentReport.model_validate(report_payload),
                geometry=geometry,
                metrics=solver_result.metrics,
            )
            report_result = run_report_generation(
                request,
                geometry=geometry,
                plan=plan,
                report=report,
                metrics=solver_result.metrics,
            )
            timeline.append(
                ExecutorTimelineEvent(
                    stage=report_result.stage,
                    message=report_result.summary,
                    status="ok",
                )
            )

            result = ExecutorTaskResult(
                job_id=request.job_id,
                run_id=request.run_id,
                status="completed",
                summary="主控执行器已完成几何检查、演示级求解和比赛报告生成。",
                executor_name=self.settings.agent_executor_display_name,
                used_tools=list(
                    dict.fromkeys(
                        [
                            *geometry_result.used_tools,
                            *solver_result.used_tools,
                            *report_result.used_tools,
                        ]
                    )
                ),
                metrics=solver_result.metrics,
                timeline=timeline,
                artifacts=[
                    *geometry_result.artifacts,
                    *solver_result.artifacts,
                    *report_result.artifacts,
                ],
                report_markdown=report_result.outputs["report_markdown"],
            )
            self._write_response(run_path, result)
            return result
        except Exception as exc:
            result = ExecutorTaskResult(
                job_id=request.job_id,
                run_id=request.run_id,
                status="failed",
                summary="主控执行器未能完成本次执行。",
                executor_name=self.settings.agent_executor_display_name,
                timeline=[
                    *timeline,
                    ExecutorTimelineEvent(
                        stage="failed",
                        message=str(exc),
                        status="error",
                    ),
                ],
                error_message=str(exc),
            )
            self._write_response(run_path, result)
            return result
