from urllib.parse import urlsplit
import time

from fastapi.testclient import TestClient

from app.agent_runtime.models import AgentPlan, AgentPlanStep, AgentReport
from app.agent_runtime.service import AgentExecutionService
from app.claude_executor_main import app as claude_executor_app
from app.main import app


def test_submit_task_and_confirm_run(temp_workspace) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/tasks",
        data={
            "task_description": "Compute pressure distribution for uploaded hull.",
            "task_type": "pressure_distribution",
            "geometry_family_hint": "DARPA SUBOFF",
            "operating_notes": "Deeply submerged at benchmark speed.",
        },
        files={"geometry_file": ("suboff.stl", b"solid hull", "model/stl")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "awaiting_confirmation"
    assert body["candidate_cases"]
    assert body["workflow_draft"]["stages"]

    confirm_response = client.post(
        f"/api/runs/{body['run_id']}/confirm",
        json={"confirmed": True, "reviewer_notes": "Proceed with recommended workflow."},
    )

    assert confirm_response.status_code == 202
    assert confirm_response.json()["status"] == "queued"

    for _ in range(40):
        detail = client.get(f"/api/runs/{body['run_id']}")
        assert detail.status_code == 200
        if detail.json()["status"] == "completed":
            break
        time.sleep(0.02)
    else:
        raise AssertionError("Queued run did not complete in time.")


def test_get_run_detail(temp_workspace) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/tasks",
        data={
            "task_description": "Analyze wake field.",
            "task_type": "wake_field",
            "geometry_family_hint": "Joubert BB2",
            "operating_notes": "Need wake plot only.",
        },
    )

    run_id = response.json()["run_id"]
    detail = client.get(f"/api/runs/{run_id}")

    assert detail.status_code == 200
    assert detail.json()["run_id"] == run_id
    assert detail.json()["workflow_draft"]["summary"]
    attempts = client.get(f"/api/runs/{run_id}/attempts")
    assert attempts.status_code == 200
    assert attempts.json() == []


def test_list_runs_returns_latest_runs_first(temp_workspace) -> None:
    client = TestClient(app)

    first = client.post(
        "/api/tasks",
        data={
            "task_description": "First run.",
            "task_type": "resistance",
            "geometry_family_hint": "Type 209",
            "operating_notes": "",
        },
    )
    second = client.post(
        "/api/tasks",
        data={
            "task_description": "Second run.",
            "task_type": "wake_field",
            "geometry_family_hint": "Joubert BB2",
            "operating_notes": "",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    listing = client.get("/api/runs")

    assert listing.status_code == 200
    body = listing.json()
    assert len(body) >= 2
    assert body[0]["run_id"] == second.json()["run_id"]
    assert body[1]["run_id"] == first.json()["run_id"]


def test_retry_run_creates_a_new_prepared_run(temp_workspace) -> None:
    client = TestClient(app)

    created = client.post(
        "/api/tasks",
        data={
            "task_description": "Retry this workflow.",
            "task_type": "pressure_distribution",
            "geometry_family_hint": "DARPA SUBOFF",
            "operating_notes": "Deeply submerged benchmark condition.",
        },
        files={"geometry_file": ("suboff.stl", b"solid hull", "model/stl")},
    )
    assert created.status_code == 201
    original = created.json()

    confirmed = client.post(
        f"/api/runs/{original['run_id']}/confirm",
        json={"confirmed": True, "reviewer_notes": "Run once before retry."},
    )
    assert confirmed.status_code == 202

    for _ in range(40):
        detail = client.get(f"/api/runs/{original['run_id']}")
        assert detail.status_code == 200
        if detail.json()["status"] == "completed":
            break
        time.sleep(0.02)
    else:
        raise AssertionError("Original run did not complete in time.")

    retried = client.post(f"/api/runs/{original['run_id']}/retry")

    assert retried.status_code == 201
    retry_body = retried.json()
    assert retry_body["run_id"] != original["run_id"]
    assert retry_body["status"] == "awaiting_confirmation"
    assert retry_body["request"]["task_description"] == original["request"]["task_description"]
    assert retry_body["candidate_cases"]


def test_cancel_queued_run_and_retry_it(temp_workspace, monkeypatch) -> None:
    monkeypatch.setenv("SUBMARINE_DISPATCH_POLL_INTERVAL", "0.5")
    client = TestClient(app)

    created = client.post(
        "/api/tasks",
        data={
            "task_description": "Queue then cancel this run.",
            "task_type": "pressure_distribution",
            "geometry_family_hint": "DARPA SUBOFF",
            "operating_notes": "Cancel before dispatch.",
        },
    )
    assert created.status_code == 201
    run_id = created.json()["run_id"]

    confirmed = client.post(
        f"/api/runs/{run_id}/confirm",
        json={"confirmed": True, "reviewer_notes": "Queue it first."},
    )
    assert confirmed.status_code == 202
    assert confirmed.json()["status"] == "queued"

    cancelled = client.post(
        f"/api/runs/{run_id}/cancel",
        json={"reason": "Stop this queued run."},
    )
    assert cancelled.status_code == 202
    assert cancelled.json()["status"] == "cancelled"

    events = client.get(f"/api/runs/{run_id}/events")
    assert events.status_code == 200
    assert any(item["event_type"] == "run_cancelled" for item in events.json())

    retried = client.post(f"/api/runs/{run_id}/retry")
    assert retried.status_code == 201
    assert retried.json()["status"] == "awaiting_confirmation"


def test_get_attempt_history_after_completed_run(temp_workspace) -> None:
    client = TestClient(app)

    created = client.post(
        "/api/tasks",
        data={
            "task_description": "Record attempts for this run.",
            "task_type": "pressure_distribution",
            "geometry_family_hint": "DARPA SUBOFF",
            "operating_notes": "Attempt history test.",
        },
    )
    assert created.status_code == 201
    run_id = created.json()["run_id"]

    confirmed = client.post(
        f"/api/runs/{run_id}/confirm",
        json={"confirmed": True, "reviewer_notes": "Run it once."},
    )
    assert confirmed.status_code == 202

    for _ in range(40):
        detail = client.get(f"/api/runs/{run_id}")
        assert detail.status_code == 200
        if detail.json()["status"] == "completed":
            break
        time.sleep(0.02)
    else:
        raise AssertionError("Completed run did not finish in time for attempts test.")

    attempts = client.get(f"/api/runs/{run_id}/attempts")
    assert attempts.status_code == 200
    body = attempts.json()
    assert len(body) == 1
    assert body[0]["attempt_number"] == 1
    assert body[0]["status"] == "completed"
    assert body[0]["summary"] == "Execution attempt completed successfully."
    assert body[0]["duration_seconds"] is not None
    assert body[0]["failure_category"] is None
    assert body[0]["failure_source"] is None


def test_submit_task_and_confirm_run_with_claude_executor(
    monkeypatch, temp_workspace
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "claude_executor")
    monkeypatch.setenv("SUBMARINE_EXECUTOR_BASE_URL", "http://claude-executor:8020")

    class FakeProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
            self.calls += 1
            if self.calls == 1:
                return AgentPlan(
                    mission_title="SUBOFF 压力分布演示任务",
                    plan_summary="先检查几何，再生成演示级求解结果，最后整理报告。",
                    selected_skills=["geometry-check", "solver-run", "report-generate"],
                    steps=[
                        AgentPlanStep(
                            skill_id="geometry-check",
                            goal="确认上传几何可用于模板化执行。",
                            expected_output="几何摘要",
                        ),
                        AgentPlanStep(
                            skill_id="solver-run",
                            goal="输出压力分布和阻力指标。",
                            expected_output="图表与结果 JSON",
                        ),
                    ],
                    report_focus=["压力分布", "阻力系数"],
                ).model_dump(mode="json")
            return AgentReport(
                report_title="SUBOFF 压力分布比赛报告",
                executive_summary="执行器完成了几何检查、演示级求解与报告整理。",
                key_findings=["生成了压力分布和结构化结果。"],
                verification_notes=["运行目录已回写完整产物。"],
                next_actions=["后续可接入真实 OpenFOAM。"],
            ).model_dump(mode="json")

    claude_executor_app.state.execution_service = AgentExecutionService(provider=FakeProvider())
    executor_client = TestClient(claude_executor_app)

    class FakeHttpxResponse:
        def __init__(self, response) -> None:
            self.response = response

        def raise_for_status(self) -> None:
            self.response.raise_for_status()

        def json(self):
            return self.response.json()

    def fake_post(url: str, json: dict, timeout: float):
        path = urlsplit(url).path
        response = executor_client.post(path, json=json)
        return FakeHttpxResponse(response)

    monkeypatch.setattr("app.execution.claude_executor_engine.httpx.post", fake_post)

    client = TestClient(app)

    response = client.post(
        "/api/tasks",
        data={
            "task_description": "Compute pressure distribution through claude executor.",
            "task_type": "pressure_distribution",
            "geometry_family_hint": "DARPA SUBOFF",
            "operating_notes": "Deeply submerged at benchmark speed.",
        },
        files={
            "geometry_file": (
                "suboff_solid.x_t",
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
                ).encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    run_id = response.json()["run_id"]

    confirm_response = client.post(
        f"/api/runs/{run_id}/confirm",
        json={"confirmed": True, "reviewer_notes": "Proceed with claude executor."},
    )

    assert confirm_response.status_code == 202
    body = confirm_response.json()
    assert body["status"] == "queued"

    for _ in range(40):
        detail = client.get(f"/api/runs/{run_id}")
        assert detail.status_code == 200
        if detail.json()["status"] == "completed":
            break
        time.sleep(0.02)
    else:
        raise AssertionError("claude_executor run did not complete in time.")

    assert detail.json()["artifacts"]
