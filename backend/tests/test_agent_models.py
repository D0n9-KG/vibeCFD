from app.agent_runtime.models import AgentPlan, AgentReport


def test_agent_plan_normalizes_string_fields_from_real_model_output() -> None:
    plan = AgentPlan.model_validate(
        {
            "mission_title": "SUBOFF 演示任务",
            "plan_summary": "先检查几何，再生成结果与报告。",
            "selected_skills": "geometry-check, solver-run, report-generate",
            "steps": {
                "skill_id": "geometry-check",
                "goal": "检查几何",
                "expected_output": "几何摘要",
            },
            "report_focus": "压力分布；阻力系数；报告归档",
        }
    )

    assert plan.selected_skills == ["geometry-check", "solver-run", "report-generate"]
    assert len(plan.steps) == 1
    assert plan.steps[0].skill_id == "geometry-check"
    assert plan.report_focus == ["压力分布", "阻力系数", "报告归档"]


def test_agent_report_normalizes_bullet_like_strings() -> None:
    report = AgentReport.model_validate(
        {
            "report_title": "SUBOFF 比赛报告",
            "executive_summary": "执行完成。",
            "key_findings": "1. 生成压力分布图\n2. 生成阻力表",
            "verification_notes": "日志已落盘；报告已生成",
            "next_actions": "接入真实求解器",
        }
    )

    assert report.key_findings == ["生成压力分布图", "生成阻力表"]
    assert report.verification_notes == ["日志已落盘", "报告已生成"]
    assert report.next_actions == ["接入真实求解器"]
