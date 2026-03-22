from pathlib import Path

from app.agent_runtime.models import AgentPlan, AgentPlanStep, AgentReport
from app.agent_runtime.service import AgentExecutionService
from app.executor_protocol import ExecutorTaskContext, ExecutorTaskRequest


class EnglishProvider:
    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls += 1
        if self.calls == 1:
            return AgentPlan(
                mission_title="DARPA SUBOFF Pressure Distribution Study",
                plan_summary="Execute the submarine CFD workflow for pressure distribution and drag analysis.",
                selected_skills=["case-search", "geometry-check", "solver-run", "report-generate"],
                steps=[
                    AgentPlanStep(
                        skill_id="geometry-check",
                        goal="Verify geometry integrity and compatibility.",
                        expected_output="Validated geometry summary.",
                    ),
                    AgentPlanStep(
                        skill_id="solver-run",
                        goal="Run a deterministic CFD synthesis pipeline.",
                        expected_output="Pressure, wake and drag outputs.",
                    ),
                ],
                report_focus="Detailed pressure analysis and drag interpretation.",
            ).model_dump(mode="json")
        return AgentReport(
            report_title="DARPA SUBOFF Pressure Distribution Study Report",
            executive_summary="This report summarizes the CFD workflow and key findings.",
            key_findings="1. Pressure distribution exported\n2. Drag metrics computed",
            verification_notes="All artifacts were written to the run directory.",
            next_actions="Connect the real solver pipeline",
        ).model_dump(mode="json")


def test_agent_execution_service_localizes_english_model_output(
    temp_workspace: Path,
) -> None:
    run_id = "run_localized_demo"
    run_dir = temp_workspace / "runs" / run_id
    uploaded_dir = run_dir / "request" / "uploaded_files"
    uploaded_dir.mkdir(parents=True, exist_ok=True)
    (uploaded_dir / "suboff_solid.x_t").write_text(
        "\n".join(
            [
                "**PART1;",
                "APPL=unigraphics;",
                "FORMAT=text;",
                "KEY=suboff_solid;",
                "FILE=D:\\Cases\\suboff\\CAD-new\\suboff_solid.x_t;",
                "DATE=26-mar-2024;",
                "**PART2;",
                "**PART3;",
            ]
        ),
        encoding="utf-8",
    )

    request = ExecutorTaskRequest(
        job_id="job_localized_demo",
        run_id=run_id,
        stage="execution",
        goal="Execute the approved submarine CFD workflow in a controlled environment and return structured outputs.",
        run_directory=str(run_dir),
        allowed_tools=["geometry-check.inspect", "solver-openfoam.run_case"],
        required_artifacts=["postprocess/result.json", "report/final_report.md"],
        input_files=["request/uploaded_files/suboff_solid.x_t"],
        context=ExecutorTaskContext(
            task_description="Evaluate submarine pressure distribution and drag for a deeply submerged condition.",
            task_type="pressure_distribution",
            geometry_family="DARPA SUBOFF",
            selected_case_id="darpa_suboff_pressure_distribution",
            selected_case_title="DARPA SUBOFF Pressure Distribution Study",
            operating_notes="Deeply submerged steady-state benchmark-style run.",
            workflow_summary="根据 SUBOFF 案例模板执行几何检查、求解和报告生成。",
            workflow_assumptions=["默认按深潜稳态外流场处理。"],
            linked_skills=["case-search", "geometry-check", "solver-run", "report-generate"],
            selected_case_reuse_role="pressure template",
        ),
    )

    service = AgentExecutionService(provider=EnglishProvider())

    result = service.execute(request)

    assert result.status == "completed"
    assert "比赛展示报告" in (result.report_markdown or "")
    assert "## 执行摘要" in (result.report_markdown or "")
    assert "## 关键结果指标" in (result.report_markdown or "")
    assert "阻力系数" in (result.report_markdown or "")
    assert "压力分布图" in (result.report_markdown or "")
