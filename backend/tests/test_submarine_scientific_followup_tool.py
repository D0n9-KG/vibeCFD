import importlib
import json
from types import SimpleNamespace

from deerflow.config.paths import Paths
from langchain_core.messages import ToolMessage
from langgraph.types import Command


def _make_runtime(
    paths: Paths,
    *,
    thread_id: str = "thread-followup",
    supervisor_handoff_virtual_path: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        state={
            "sandbox": {"sandbox_id": "local"},
            "thread_data": {
                "workspace_path": str(paths.sandbox_work_dir(thread_id)),
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(paths.sandbox_outputs_dir(thread_id)),
            },
            "submarine_runtime": {
                "current_stage": "result-reporting",
                "task_summary": "Continue the scientific CFD remediation flow",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "stage_status": "completed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "supervisor-review",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                "provenance_manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
                "artifact_virtual_paths": [],
                "activity_timeline": [],
                "supervisor_handoff_virtual_path": supervisor_handoff_virtual_path,
            },
        },
        context={"thread_id": thread_id},
    )


def _write_handoff_artifact(
    paths: Paths,
    *,
    thread_id: str,
    filename: str = "scientific-remediation-handoff.json",
    payload: dict,
) -> str:
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    artifact_dir = outputs_dir / "submarine" / "reports" / "demo"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / filename
    artifact_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return f"/mnt/user-data/outputs/submarine/reports/demo/{filename}"


def _read_report_artifact(paths: Paths, *, thread_id: str, filename: str) -> dict:
    artifact_path = (
        paths.sandbox_outputs_dir(thread_id)
        / "submarine"
        / "reports"
        / "demo"
        / filename
    )
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def test_submarine_scientific_followup_errors_without_handoff_pointer(tmp_path):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    runtime = _make_runtime(paths)

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-missing-handoff",
    )

    message = result.update["messages"][0]
    assert "Error:" in message.content
    assert "supervisor_handoff_virtual_path" in message.content


def test_submarine_scientific_followup_recovers_handoff_from_artifacts_when_runtime_pointer_is_missing(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-artifact-recovery"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "regenerate-research-report-linkage",
            "tool_name": "submarine_result_report",
            "tool_args": {
                "report_title": "Recovered scientific follow-up report",
            },
            "reason": "Use the latest remediation handoff artifact even if runtime lost the pointer.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=None,
    )
    runtime.state["artifacts"] = [handoff_virtual_path]

    captured: dict[str, object] = {}

    def fake_result_report_tool(**kwargs):
        captured.update(kwargs)
        return Command(
            update={
                "submarine_runtime": {
                    "current_stage": "result-reporting",
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                },
                "messages": [
                    ToolMessage(
                        "Recovered report regenerated",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_result_report_tool",
        SimpleNamespace(func=fake_result_report_tool),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-artifact-recovery",
    )

    assert captured["runtime"] is runtime
    assert captured["report_title"] == "Recovered scientific follow-up report"
    assert captured["tool_call_id"] == "tc-followup-artifact-recovery"
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json"
    )
    assert "Recovered report regenerated" in result.update["messages"][0].content


def test_submarine_scientific_followup_refuses_manual_handoff(tmp_path):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-manual"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "manual_followup_required",
            "recommended_action_id": "attach-validation-reference",
            "tool_name": None,
            "tool_args": None,
            "reason": "No applicable benchmark target was available for this run.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [
                {
                    "action_id": "attach-validation-reference",
                    "title": "Attach validation reference",
                    "owner_stage": "supervisor-review",
                    "evidence_gap": "No applicable benchmark target was available for this run.",
                }
            ],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-manual-handoff",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    message = result.update["messages"][0]
    assert "manual_followup_required" in message.content
    assert "attach-validation-reference" in message.content
    assert "No applicable benchmark target was available" in message.content
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json"
    )
    assert history["entry_count"] == 1
    assert history_entry["outcome_status"] == "manual_followup_required"
    assert history_entry["report_refreshed"] is False
    assert history_entry["recommended_action_id"] == "attach-validation-reference"
    assert history_entry["source_handoff_virtual_path"] == handoff_virtual_path


def test_submarine_scientific_followup_reports_not_needed_handoff(tmp_path):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-not-needed"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "not_needed",
            "recommended_action_id": None,
            "tool_name": None,
            "tool_args": None,
            "reason": "Scientific remediation is not needed for this run.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-not-needed",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    message = result.update["messages"][0]
    assert "not_needed" in message.content
    assert "Scientific remediation is not needed" in message.content
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json"
    )
    assert history["entry_count"] == 1
    assert history_entry["outcome_status"] == "not_needed"
    assert history_entry["report_refreshed"] is False
    assert history_entry["source_handoff_virtual_path"] == handoff_virtual_path


def test_submarine_scientific_followup_records_task_complete_without_rerun(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-task-complete"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "manual_followup_required",
            "recommended_action_id": "attach-validation-reference",
            "tool_name": None,
            "tool_args": None,
            "reason": "The user accepted the current evidence package as sufficient.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )

    dispatch_calls: list[dict[str, object]] = []
    report_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        tool_module,
        "submarine_solver_dispatch_tool",
        SimpleNamespace(func=lambda **kwargs: dispatch_calls.append(kwargs)),
        raising=False,
    )
    monkeypatch.setattr(
        tool_module,
        "submarine_result_report_tool",
        SimpleNamespace(func=lambda **kwargs: report_calls.append(kwargs)),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        followup_kind="task_complete",
        decision_summary_zh="接受当前结论作为任务终点。",
        source_conclusion_ids=["current_conclusion"],
        source_evidence_gap_ids=["missing_validation_reference"],
        tool_call_id="tc-followup-task-complete",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert dispatch_calls == []
    assert report_calls == []
    assert "task completion" in result.update["messages"][0].content
    assert history["entry_count"] == 1
    assert history_entry["followup_kind"] == "task_complete"
    assert history_entry["decision_summary_zh"] == "接受当前结论作为任务终点。"
    assert history_entry["source_conclusion_ids"] == ["current_conclusion"]
    assert history_entry["source_evidence_gap_ids"] == [
        "missing_validation_reference"
    ]
    assert history_entry["task_completion_status"] == "completed"
    assert history_entry["outcome_status"] == "task_complete"
    assert history_entry["report_refreshed"] is False
    assert (
        history_entry["result_report_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/final-report.md"
    )
    assert (
        history_entry["result_provenance_manifest_virtual_path"]
        == "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json"
    )


def test_submarine_scientific_followup_executes_solver_dispatch_handoff(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-dispatch"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": "Run the missing scientific studies",
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
            },
            "reason": "Scientific verification evidence is incomplete for this run.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )
    runtime.state["submarine_runtime"]["confirmation_status"] = "confirmed"
    runtime.state["submarine_runtime"]["execution_preference"] = (
        "preflight_then_execute"
    )

    captured: dict[str, object] = {}

    def fake_solver_dispatch_tool(**kwargs):
        captured.update(kwargs)
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json"
                ],
                "submarine_runtime": {
                    "current_stage": "solver-dispatch",
                    "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/supervisor-handoff.json",
                },
                "messages": [
                    ToolMessage(
                        "Scientific studies dispatched",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_solver_dispatch_tool",
        SimpleNamespace(func=fake_solver_dispatch_tool),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-dispatch",
    )

    assert captured["runtime"] is runtime
    assert captured["geometry_path"] == "/mnt/user-data/uploads/suboff-demo.stl"
    assert captured["task_description"] == "Run the missing scientific studies"
    assert captured["execute_scientific_studies"] is True
    assert captured["execute_now"] is True
    assert captured["tool_call_id"] == "tc-followup-dispatch"
    assert result.update["submarine_runtime"]["current_stage"] == "solver-dispatch"
    assert (
        result.update["submarine_runtime"]["task_summary"]
        == "Continue the scientific CFD remediation flow"
    )
    assert result.update["submarine_runtime"]["confirmation_status"] == "confirmed"
    assert (
        result.update["submarine_runtime"]["execution_preference"]
        == "preflight_then_execute"
    )
    assert "Scientific studies dispatched" in result.update["messages"][0].content


def test_submarine_scientific_followup_strips_runtime_only_dispatch_args(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-dispatch-sanitized"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": "Run the missing scientific studies",
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
                "confirmation_status": "confirmed",
                "execution_preference": "preflight_then_execute",
            },
            "reason": "Scientific verification evidence is incomplete for this run.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )
    runtime.state["submarine_runtime"]["confirmation_status"] = "confirmed"
    runtime.state["submarine_runtime"]["execution_preference"] = (
        "preflight_then_execute"
    )

    captured: dict[str, object] = {}

    def fake_solver_dispatch_tool(
        *,
        runtime,
        geometry_path,
        task_description,
        task_type="resistance",
        geometry_family_hint=None,
        selected_case_id=None,
        inlet_velocity_mps=None,
        fluid_density_kg_m3=None,
        kinematic_viscosity_m2ps=None,
        end_time_seconds=None,
        delta_t_seconds=None,
        write_interval_steps=None,
        execute_now=None,
        execute_scientific_studies=False,
        custom_variants=None,
        solver_command=None,
        tool_call_id="",
    ):
        captured.update(
            {
                "runtime": runtime,
                "geometry_path": geometry_path,
                "task_description": task_description,
                "task_type": task_type,
                "selected_case_id": selected_case_id,
                "execute_now": execute_now,
                "execute_scientific_studies": execute_scientific_studies,
                "tool_call_id": tool_call_id,
                "geometry_family_hint": geometry_family_hint,
                "inlet_velocity_mps": inlet_velocity_mps,
                "fluid_density_kg_m3": fluid_density_kg_m3,
                "kinematic_viscosity_m2ps": kinematic_viscosity_m2ps,
                "end_time_seconds": end_time_seconds,
                "delta_t_seconds": delta_t_seconds,
                "write_interval_steps": write_interval_steps,
                "custom_variants": custom_variants,
                "solver_command": solver_command,
            }
        )
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json"
                ],
                "submarine_runtime": {
                    "current_stage": "solver-dispatch",
                    "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/supervisor-handoff.json",
                },
                "messages": [
                    ToolMessage(
                        "Scientific studies dispatched",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_solver_dispatch_tool",
        SimpleNamespace(func=fake_solver_dispatch_tool),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-dispatch-sanitized",
    )

    assert captured["runtime"] is runtime
    assert captured["geometry_path"] == "/mnt/user-data/uploads/suboff-demo.stl"
    assert captured["task_description"] == "Run the missing scientific studies"
    assert captured["task_type"] == "resistance"
    assert captured["selected_case_id"] == "darpa_suboff_axisymmetric"
    assert captured["execute_scientific_studies"] is True
    assert captured["execute_now"] is True
    assert captured["tool_call_id"] == "tc-followup-dispatch-sanitized"
    assert "Scientific studies dispatched" in result.update["messages"][0].content


def test_submarine_scientific_followup_executes_result_report_handoff(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-report"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "regenerate-research-report-linkage",
            "tool_name": "submarine_result_report",
            "tool_args": {
                "report_title": "Regenerated research report",
            },
            "reason": "Research report packaging should be regenerated.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )

    captured: dict[str, object] = {}

    def fake_result_report_tool(**kwargs):
        captured.update(kwargs)
        return Command(
            update={
                "submarine_runtime": {
                    "current_stage": "result-reporting",
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                },
                "messages": [
                    ToolMessage(
                        "Research report regenerated",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_result_report_tool",
        SimpleNamespace(func=fake_result_report_tool),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-report",
    )

    assert captured["runtime"] is runtime
    assert captured["report_title"] == "Regenerated research report"
    assert captured["tool_call_id"] == "tc-followup-report"
    assert result.update["submarine_runtime"]["current_stage"] == "result-reporting"
    assert "Research report regenerated" in result.update["messages"][0].content


def test_submarine_scientific_followup_tool_is_registered_for_runtime_dispatch():
    tools_module = importlib.import_module("deerflow.tools.tools")

    builtin_tool_names = {tool.name for tool in tools_module.BUILTIN_TOOLS}

    assert "submarine_scientific_followup" in builtin_tool_names


def test_submarine_scientific_followup_refreshes_report_after_executed_dispatch(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-refresh"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": "Run the missing scientific studies",
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
            },
            "reason": "Scientific verification evidence is incomplete for this run.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )
    runtime.state["submarine_runtime"]["confirmation_status"] = "confirmed"
    runtime.state["submarine_runtime"]["execution_preference"] = (
        "preflight_then_execute"
    )

    dispatch_captured: dict[str, object] = {}
    report_captured: dict[str, object] = {}

    def fake_solver_dispatch_tool(**kwargs):
        dispatch_captured.update(kwargs)
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json"
                ],
                "submarine_runtime": {
                    "current_stage": "solver-dispatch",
                    "task_summary": "Run the missing scientific studies",
                    "task_type": "resistance",
                    "geometry_virtual_path": "/mnt/user-data/uploads/suboff-demo.stl",
                    "geometry_family": "DARPA SUBOFF",
                    "execution_readiness": "stl_ready",
                    "selected_case_id": "darpa_suboff_axisymmetric",
                    "stage_status": "executed",
                    "review_status": "ready_for_supervisor",
                    "next_recommended_stage": "result-reporting",
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                    "artifact_virtual_paths": [
                        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json"
                    ],
                    "activity_timeline": [],
                    "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/supervisor-handoff.json",
                },
                "messages": [
                    ToolMessage(
                        "Scientific studies dispatched",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    def fake_result_report_tool(**kwargs):
        report_captured.update(kwargs)
        chained_runtime = kwargs["runtime"]
        assert chained_runtime is not runtime
        assert (
            chained_runtime.state["submarine_runtime"]["stage_status"] == "executed"
        )
        assert (
            chained_runtime.state["submarine_runtime"]["current_stage"]
            == "solver-dispatch"
        )
        assert (
            chained_runtime.state["submarine_runtime"]["confirmation_status"]
            == "confirmed"
        )
        assert (
            chained_runtime.state["submarine_runtime"]["execution_preference"]
            == "preflight_then_execute"
        )
        assert chained_runtime.state["thread_data"] == runtime.state["thread_data"]
        assert chained_runtime.context == runtime.context
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/reports/demo/final-report.json"
                ],
                "submarine_runtime": {
                    "current_stage": "result-reporting",
                    "stage_status": "executed",
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                    "provenance_manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest-refreshed.json",
                    "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
                },
                "messages": [
                    ToolMessage(
                        "Research report regenerated after solver rerun",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_solver_dispatch_tool",
        SimpleNamespace(func=fake_solver_dispatch_tool),
        raising=False,
    )
    monkeypatch.setattr(
        tool_module,
        "submarine_result_report_tool",
        SimpleNamespace(func=fake_result_report_tool),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        followup_kind="evidence_supplement",
        decision_summary_zh="补齐外部验证证据后刷新报告。",
        source_conclusion_ids=["current_conclusion"],
        source_evidence_gap_ids=["missing_validation_reference"],
        tool_call_id="tc-followup-refresh",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert dispatch_captured["runtime"] is runtime
    assert dispatch_captured["execute_now"] is True
    assert report_captured["tool_call_id"] == "tc-followup-refresh"
    assert result.update["submarine_runtime"]["current_stage"] == "result-reporting"
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json"
    )
    assert "Research report regenerated after solver rerun" in result.update["messages"][
        0
    ].content
    assert history["entry_count"] == 1
    assert history_entry["outcome_status"] == "dispatch_refreshed_report"
    assert history_entry["followup_kind"] == "evidence_supplement"
    assert history_entry["decision_summary_zh"] == "补齐外部验证证据后刷新报告。"
    assert history_entry["source_conclusion_ids"] == ["current_conclusion"]
    assert history_entry["source_evidence_gap_ids"] == [
        "missing_validation_reference"
    ]
    assert history_entry["task_completion_status"] == "continued"
    assert history_entry["dispatch_stage_status"] == "executed"
    assert history_entry["report_refreshed"] is True
    assert (
        history_entry["result_report_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/final-report.md"
    )
    assert (
        history_entry["result_provenance_manifest_virtual_path"]
        == "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest-refreshed.json"
    )
    assert (
        history_entry["result_supervisor_handoff_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
    )


def test_submarine_scientific_followup_does_not_refresh_report_after_planned_dispatch(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-planned"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": "Prepare the scientific studies",
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
            },
            "reason": "Scientific verification evidence is incomplete for this run.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )

    report_calls: list[dict[str, object]] = []

    def fake_solver_dispatch_tool(**kwargs):
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json"
                ],
                "submarine_runtime": {
                    "current_stage": "solver-dispatch",
                    "stage_status": "planned",
                    "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/supervisor-handoff.json",
                },
                "messages": [
                    ToolMessage(
                        "Scientific studies prepared but not executed",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    def fake_result_report_tool(**kwargs):
        report_calls.append(kwargs)
        return Command(update={})

    monkeypatch.setattr(
        tool_module,
        "submarine_solver_dispatch_tool",
        SimpleNamespace(func=fake_solver_dispatch_tool),
        raising=False,
    )
    monkeypatch.setattr(
        tool_module,
        "submarine_result_report_tool",
        SimpleNamespace(func=fake_result_report_tool),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-planned",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert report_calls == []
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json"
    )
    assert result.update["submarine_runtime"]["stage_status"] == "planned"
    assert "prepared but not executed" in result.update["messages"][0].content
    assert history["entry_count"] == 1
    assert history_entry["outcome_status"] == "dispatch_planned"
    assert history_entry["dispatch_stage_status"] == "planned"
    assert history_entry["report_refreshed"] is False


def test_submarine_scientific_followup_does_not_refresh_report_after_failed_dispatch(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-failed"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": "Run the scientific studies",
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
            },
            "reason": "Scientific verification evidence is incomplete for this run.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=handoff_virtual_path,
    )

    report_calls: list[dict[str, object]] = []

    def fake_solver_dispatch_tool(**kwargs):
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json"
                ],
                "submarine_runtime": {
                    "current_stage": "solver-dispatch",
                    "stage_status": "failed",
                    "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/supervisor-handoff.json",
                },
                "messages": [
                    ToolMessage(
                        "Scientific studies failed to execute",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    def fake_result_report_tool(**kwargs):
        report_calls.append(kwargs)
        return Command(update={})

    monkeypatch.setattr(
        tool_module,
        "submarine_solver_dispatch_tool",
        SimpleNamespace(func=fake_solver_dispatch_tool),
        raising=False,
    )
    monkeypatch.setattr(
        tool_module,
        "submarine_result_report_tool",
        SimpleNamespace(func=fake_result_report_tool),
        raising=False,
    )

    result = tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-failed",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert report_calls == []
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        == "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json"
    )
    assert result.update["submarine_runtime"]["stage_status"] == "failed"
    assert "failed to execute" in result.update["messages"][0].content
    assert history["entry_count"] == 1
    assert history_entry["outcome_status"] == "dispatch_failed"
    assert history_entry["dispatch_stage_status"] == "failed"
    assert history_entry["report_refreshed"] is False
