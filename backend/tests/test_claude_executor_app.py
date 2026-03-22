from pathlib import Path

from fastapi.testclient import TestClient

from app.agent_runtime.models import AgentPlan, AgentPlanStep, AgentReport
from app.agent_runtime.service import AgentExecutionService
from app.claude_executor_main import app


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.system_prompts: list[str] = []
        self.user_prompts: list[str] = []

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls += 1
        self.system_prompts.append(system_prompt)
        self.user_prompts.append(user_prompt)
        if self.calls == 1:
            return AgentPlan(
                mission_title="SUBOFF 压力分布演示任务",
                plan_summary="先完成几何检查，再生成演示级求解结果，最后整理比赛展示报告。",
                selected_skills=["geometry-check", "solver-run", "report-generate"],
                steps=[
                    AgentPlanStep(
                        skill_id="geometry-check",
                        goal="确认 Parasolid 文件可以用于模板化执行。",
                        expected_output="几何摘要与映射结论",
                    ),
                    AgentPlanStep(
                        skill_id="solver-run",
                        goal="生成演示级压力分布与阻力结果。",
                        expected_output="结构化结果与图表",
                    ),
                    AgentPlanStep(
                        skill_id="report-generate",
                        goal="生成最终比赛展示报告。",
                        expected_output="Markdown 报告",
                    ),
                ],
                report_focus=["压力分布", "阻力系数", "案例映射"],
            ).model_dump(mode="json")
        return AgentReport(
            report_title="SUBOFF 压力分布比赛报告",
            executive_summary="主控执行器完成了案例映射、几何检查和演示级求解。",
            key_findings=[
                "几何文件已识别为 DARPA SUBOFF 家族。",
                "生成了压力分布、尾流切片和阻力表。",
            ],
            verification_notes=[
                "执行链路已完整回写到 run 目录。",
                "适合用于比赛演示与答辩展示。",
            ],
            next_actions=["可进一步替换为真实 OpenFOAM 求解器。"],
        ).model_dump(mode="json")


def test_agent_executor_returns_structured_completion_with_real_artifacts(
    temp_workspace: Path,
) -> None:
    provider = FakeProvider()
    app.state.execution_service = AgentExecutionService(provider=provider)
    client = TestClient(app)
    run_id = "run_agent_demo"
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

    response = client.post(
        "/api/execute",
        json={
            "job_id": "job_run_agent_demo",
            "run_id": run_id,
            "stage": "execution",
            "goal": "Run the recommended benchmark CFD workflow and write structured outputs.",
            "run_directory": str(run_dir),
            "allowed_tools": ["geometry-check.inspect", "solver-openfoam.run_case"],
            "required_artifacts": [
                "postprocess/result.json",
                "report/final_report.md",
            ],
            "input_files": ["request/uploaded_files/suboff_solid.x_t"],
            "context": {
                "task_description": "Compute pressure distribution for SUBOFF.",
                "task_type": "pressure_distribution",
                "geometry_family": "DARPA SUBOFF",
                "selected_case_id": "darpa_suboff_pressure_distribution",
                "selected_case_title": "DARPA SUBOFF pressure validation",
                "reviewer_notes": "Proceed with the recommended workflow.",
                "operating_notes": "Deeply submerged benchmark condition.",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["executor_name"] == "Submarine Agent Executor"
    assert body["timeline"]
    assert "潜艇 CFD 工作台" in provider.system_prompts[0]
    assert "比赛展示" in provider.system_prompts[1]
    assert "工作流摘要" in provider.user_prompts[0]
    assert any(
        artifact["relative_path"] == "postprocess/images/geometry_overview.svg"
        for artifact in body["artifacts"]
    )
    assert (run_dir / "execution" / "agent_executor" / "request.json").is_file()
    assert (run_dir / "execution" / "agent_executor" / "response.json").is_file()
    assert (run_dir / "postprocess" / "images" / "geometry_overview.svg").is_file()
    assert (run_dir / "postprocess" / "result.json").is_file()
    assert (run_dir / "report" / "final_report.md").is_file()
    report_markdown = (run_dir / "report" / "final_report.md").read_text(encoding="utf-8")
    assert "## 执行摘要" in report_markdown
    assert "## 关键结果指标" in report_markdown
    assert "## 产物清单" in report_markdown
