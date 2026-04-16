import importlib
import json
from types import SimpleNamespace

from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command

from deerflow.config.paths import Paths


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


def test_submarine_scientific_followup_skips_generic_solver_handoff_and_uses_scientific_report_handoff(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-prefers-scientific-handoff"
    solver_handoff_dir = (
        paths.sandbox_outputs_dir(thread_id)
        / "submarine"
        / "solver-dispatch"
        / "demo"
    )
    solver_handoff_dir.mkdir(parents=True, exist_ok=True)
    solver_handoff_virtual_path = (
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/supervisor-handoff.json"
    )
    (solver_handoff_dir / "supervisor-handoff.json").write_text(
        json.dumps(
            {
                "stage_status": "completed",
                "next_recommended_stage": "supervisor-review",
                "reason": "This is the generic solver supervisor handoff, not the remediation handoff.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    scientific_handoff_virtual_path = _write_handoff_artifact(
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
            "reason": "Use the scientific remediation handoff from the report directory.",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json"
            ],
            "manual_actions": [],
        },
    )
    runtime = _make_runtime(
        paths,
        thread_id=thread_id,
        supervisor_handoff_virtual_path=solver_handoff_virtual_path,
    )

    captured: dict[str, object] = {}

    def fake_solver_dispatch_tool(**kwargs):
        captured.update(kwargs)
        return Command(
            update={
                "submarine_runtime": {
                    "current_stage": "solver-dispatch",
                    "stage_status": "planned",
                },
                "messages": [
                    ToolMessage(
                        "Scientific remediation dispatch resolved from the report handoff",
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
        tool_call_id="tc-followup-prefers-scientific-handoff",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert captured["task_description"] == "Run the missing scientific studies"
    assert captured["execute_scientific_studies"] is True
    assert captured["tool_call_id"] == "tc-followup-prefers-scientific-handoff"
    assert (
        history_entry["source_handoff_virtual_path"]
        == scientific_handoff_virtual_path
    )
    assert history_entry["outcome_status"] == "dispatch_planned"
    assert (
        "Scientific remediation dispatch resolved from the report handoff"
        in result.update["messages"][0].content
    )


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


def test_submarine_scientific_followup_preserves_iterative_contract_dispatch_args(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-dispatch-contract"
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
                "contract_revision": 3,
                "iteration_mode": "derive_variant",
                "revision_summary": "Carry the wake-focused follow-up into dispatch.",
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

    tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        tool_call_id="tc-followup-dispatch-contract",
    )

    assert captured["contract_revision"] == 3
    assert captured["iteration_mode"] == "derive_variant"
    assert captured["revision_summary"] == (
        "Carry the wake-focused follow-up into dispatch."
    )


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


def test_submarine_scientific_followup_syncs_design_brief_before_dispatch_when_new_outputs_are_requested(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-output-sync"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": "在当前线程追加尾流速度切片和流线图两个交付输出后继续重跑并刷新报告。",
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
                "confirmation_status": "confirmed",
                "execution_preference": "execute_now",
            },
            "reason": "Need to expand deliverables before the follow-up rerun.",
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
    runtime.state["submarine_runtime"]["execution_preference"] = "execute_now"
    runtime.state["submarine_runtime"]["requested_outputs"] = []
    runtime.state["submarine_runtime"]["output_delivery_plan"] = []

    design_brief_captured: dict[str, object] = {}
    dispatch_captured: dict[str, object] = {}
    report_captured: dict[str, object] = {}
    synced_requested_outputs = [
        {
            "output_id": "wake_velocity_slice",
            "requested_label": "尾流速度切片",
            "support_level": "supported",
            "delivery_status": "planned",
        },
        {
            "output_id": "streamlines",
            "requested_label": "流线图",
            "support_level": "not_yet_supported",
            "delivery_status": "not_yet_supported",
        },
    ]
    synced_output_delivery_plan = [
        {
            "output_id": "wake_velocity_slice",
            "requested_label": "尾流速度切片",
            "delivery_status": "planned",
        },
        {
            "output_id": "streamlines",
            "requested_label": "流线图",
            "delivery_status": "not_yet_supported",
        },
    ]

    def fake_design_brief_tool(**kwargs):
        design_brief_captured.update(kwargs)
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/design-brief/demo/cfd-design-brief.json"
                ],
                "submarine_runtime": {
                    "current_stage": "task-intelligence",
                    "task_summary": kwargs["task_description"],
                    "contract_revision": 2,
                    "iteration_mode": "revise_baseline",
                    "revision_summary": "Updated the structured CFD design brief.",
                    "requested_outputs": synced_requested_outputs,
                    "output_delivery_plan": synced_output_delivery_plan,
                    "confirmation_status": "confirmed",
                    "execution_preference": "execute_now",
                },
                "messages": [
                    ToolMessage(
                        "Design brief synchronized before follow-up dispatch",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    def fake_solver_dispatch_tool(**kwargs):
        dispatch_captured.update(kwargs)
        chained_runtime = kwargs["runtime"]
        assert chained_runtime is not runtime
        assert chained_runtime.state["submarine_runtime"]["requested_outputs"] == (
            synced_requested_outputs
        )
        assert chained_runtime.state["submarine_runtime"]["output_delivery_plan"] == (
            synced_output_delivery_plan
        )
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json"
                ],
                "submarine_runtime": {
                    "current_stage": "solver-dispatch",
                    "stage_status": "executed",
                    "requested_outputs": synced_requested_outputs,
                    "output_delivery_plan": synced_output_delivery_plan,
                    "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/supervisor-handoff.json",
                },
                "messages": [
                    ToolMessage(
                        "Scientific studies dispatched with synced deliverables",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    def fake_result_report_tool(**kwargs):
        report_captured.update(kwargs)
        chained_runtime = kwargs["runtime"]
        assert chained_runtime is not runtime
        assert chained_runtime.state["submarine_runtime"]["requested_outputs"] == (
            synced_requested_outputs
        )
        assert chained_runtime.state["submarine_runtime"]["output_delivery_plan"] == (
            synced_output_delivery_plan
        )
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/reports/demo/final-report.json"
                ],
                "submarine_runtime": {
                    "current_stage": "result-reporting",
                    "stage_status": "executed",
                    "requested_outputs": synced_requested_outputs,
                    "output_delivery_plan": synced_output_delivery_plan,
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                },
                "messages": [
                    ToolMessage(
                        "Research report regenerated after synced dispatch",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_design_brief_tool",
        SimpleNamespace(func=fake_design_brief_tool),
        raising=False,
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
        tool_call_id="tc-followup-output-sync",
    )

    assert design_brief_captured["runtime"] is runtime
    assert (
        design_brief_captured["task_description"]
        == "在当前线程追加尾流速度切片和流线图两个交付输出后继续重跑并刷新报告。"
    )
    assert dispatch_captured["contract_revision"] == 2
    assert dispatch_captured["iteration_mode"] == "revise_baseline"
    assert dispatch_captured["revision_summary"] == (
        "Updated the structured CFD design brief."
    )
    assert dispatch_captured["execute_now"] is True
    assert report_captured["tool_call_id"] == "tc-followup-output-sync"
    assert result.update["submarine_runtime"]["requested_outputs"] == (
        synced_requested_outputs
    )
    assert result.update["submarine_runtime"]["output_delivery_plan"] == (
        synced_output_delivery_plan
    )


def test_submarine_scientific_followup_refreshes_report_without_rerun_for_output_only_contract_revision(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-output-refresh-only"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": "继续当前线程：把新增交付输出明确更新为尾流速度切片和流线图；如果无需重新求解也能完成，就直接同步设计简报、交付计划并刷新报告。",
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
                "confirmation_status": "confirmed",
                "execution_preference": "execute_now",
            },
            "reason": "Refresh delivery contract first and avoid unnecessary reruns.",
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
    runtime.state["submarine_runtime"]["execution_preference"] = "execute_now"
    runtime.state["submarine_runtime"]["requested_outputs"] = []
    runtime.state["submarine_runtime"]["output_delivery_plan"] = []

    design_brief_captured: dict[str, object] = {}
    dispatch_calls: list[dict[str, object]] = []
    report_captured: dict[str, object] = {}
    synced_requested_outputs = [
        {
            "output_id": "wake_velocity_slice",
            "requested_label": "尾流速度切片",
            "support_level": "supported",
            "delivery_status": "planned",
        },
        {
            "output_id": "streamlines",
            "requested_label": "流线图",
            "support_level": "not_yet_supported",
            "delivery_status": "not_yet_supported",
        },
    ]
    synced_output_delivery_plan = [
        {
            "output_id": "wake_velocity_slice",
            "requested_label": "尾流速度切片",
            "delivery_status": "pending",
        },
        {
            "output_id": "streamlines",
            "requested_label": "流线图",
            "delivery_status": "not_yet_supported",
        },
    ]

    def fake_design_brief_tool(**kwargs):
        design_brief_captured.update(kwargs)
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/design-brief/demo/cfd-design-brief.json"
                ],
                "submarine_runtime": {
                    "current_stage": "task-intelligence",
                    "task_summary": kwargs["task_description"],
                    "requested_outputs": synced_requested_outputs,
                    "output_delivery_plan": synced_output_delivery_plan,
                    "confirmation_status": "confirmed",
                    "execution_preference": "execute_now",
                },
            }
        )

    def fake_solver_dispatch_tool(**kwargs):
        dispatch_calls.append(kwargs)
        return Command(update={})

    def fake_result_report_tool(**kwargs):
        report_captured.update(kwargs)
        chained_runtime = kwargs["runtime"]
        assert chained_runtime is not runtime
        assert chained_runtime.state["submarine_runtime"]["requested_outputs"] == (
            synced_requested_outputs
        )
        assert chained_runtime.state["submarine_runtime"]["output_delivery_plan"] == (
            synced_output_delivery_plan
        )
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/reports/demo/final-report.json"
                ],
                "submarine_runtime": {
                    "current_stage": "result-reporting",
                    "stage_status": "confirmed",
                    "requested_outputs": synced_requested_outputs,
                    "output_delivery_plan": synced_output_delivery_plan,
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                },
                "messages": [
                    ToolMessage(
                        "Research report regenerated without rerun",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_design_brief_tool",
        SimpleNamespace(func=fake_design_brief_tool),
        raising=False,
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
        tool_call_id="tc-followup-output-refresh-only",
    )

    assert design_brief_captured["runtime"] is runtime
    assert dispatch_calls == []
    assert report_captured["tool_call_id"] == "tc-followup-output-refresh-only"
    assert result.update["submarine_runtime"]["current_stage"] == "result-reporting"
    assert result.update["submarine_runtime"]["requested_outputs"] == (
        synced_requested_outputs
    )
    assert result.update["submarine_runtime"]["output_delivery_plan"] == (
        synced_output_delivery_plan
    )


def test_submarine_scientific_followup_detects_common_english_no_rerun_phrasing():
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    assert tool_module._should_refresh_report_without_rerun_for_output_sync(
        {
            "task_description": (
                "Please do not rerun the solver. Sync the design brief and refresh "
                "the final report only."
            )
        }
    )
    assert tool_module._should_refresh_report_without_rerun_for_output_sync(
        {
            "task_description": (
                "Don't rerun the solver; just update the delivery plan and refresh "
                "the report."
            )
        }
    )
    assert tool_module._should_refresh_report_without_rerun_for_output_sync(
        {
            "task_description": (
                "Please do not re-run the solver. Sync the design brief and refresh "
                "the final report only."
            )
        }
    )
    assert tool_module._should_refresh_report_without_rerun_for_output_sync(
        {
            "task_description": (
                "Don't re-run the solver; just update the delivery plan and refresh "
                "the report."
            )
        }
    )


def test_submarine_scientific_followup_ignores_upload_only_latest_message_when_resolving_task_description():
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    runtime = SimpleNamespace(
        state={
            "messages": [
                HumanMessage(
                    content=(
                        "<uploaded_files>\n"
                        "The following files were uploaded in this message:\n\n"
                        "- extra.txt (1 KB)\n"
                        "  Path: /mnt/user-data/uploads/extra.txt\n\n"
                        "You can read these files using the `read_file` tool with the paths shown above.\n"
                        "</uploaded_files>"
                    )
                )
            ]
        }
    )
    fallback_task_description = (
        "Please do not rerun the solver. Sync the design brief and refresh the "
        "final report only."
    )

    assert (
        tool_module._resolve_followup_task_description(
            runtime,
            {"task_description": fallback_task_description},
        )
        == fallback_task_description
    )


def test_submarine_scientific_followup_prefers_short_latest_user_message_when_it_changes_intent():
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    runtime = SimpleNamespace(
        state={
            "messages": [
                HumanMessage(content="benchmark variant")
            ]
        }
    )
    fallback_task_description = (
        "Please do not rerun the solver. Sync the design brief and refresh the "
        "final report only."
    )

    assert (
        tool_module._resolve_followup_task_description(
            runtime,
            {"task_description": fallback_task_description},
        )
        == "benchmark variant"
    )


def test_submarine_scientific_followup_refreshes_report_without_rerun_even_when_design_brief_is_already_synced(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-no-rerun-no-brief-sync"
    task_description = (
        "Please do not rerun the solver. Keep wake velocity slice and streamlines "
        "as the requested outputs, and refresh the final report only."
    )
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": task_description,
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
                "confirmation_status": "confirmed",
                "execution_preference": "execute_now",
            },
            "reason": "Refresh the report without rerun because the contract already matches.",
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
    runtime.state["submarine_runtime"]["execution_preference"] = "execute_now"
    runtime.state["submarine_runtime"]["requested_outputs"] = [
        {
            "output_id": "wake_velocity_slice",
            "label": "Wake velocity slice",
            "requested_label": "Wake velocity slice",
            "support_level": "supported",
        },
        {
            "output_id": "streamlines",
            "label": "Streamlines",
            "requested_label": "Streamlines",
            "support_level": "not_yet_supported",
        },
    ]
    runtime.state["submarine_runtime"]["output_delivery_plan"] = [
        {
            "output_id": "wake_velocity_slice",
            "label": "Wake velocity slice",
            "requested_label": "Wake velocity slice",
            "delivery_status": "pending",
            "detail": "Keep the existing delivery contract and refresh only the report.",
        },
        {
            "output_id": "streamlines",
            "label": "Streamlines",
            "requested_label": "Streamlines",
            "delivery_status": "not_yet_supported",
            "detail": "Still not automatically supported in the current repo.",
        },
    ]

    dispatch_calls: list[dict[str, object]] = []
    report_captured: dict[str, object] = {}

    def fake_solver_dispatch_tool(**kwargs):
        dispatch_calls.append(kwargs)
        return Command(update={})

    def fake_result_report_tool(**kwargs):
        report_captured.update(kwargs)
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/reports/demo/final-report.json"
                ],
                "submarine_runtime": {
                    "current_stage": "result-reporting",
                    "stage_status": "confirmed",
                    "requested_outputs": runtime.state["submarine_runtime"]["requested_outputs"],
                    "output_delivery_plan": runtime.state["submarine_runtime"]["output_delivery_plan"],
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                },
                "messages": [
                    ToolMessage(
                        "Research report regenerated without rerun",
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
        tool_call_id="tc-followup-no-rerun-no-brief-sync",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert dispatch_calls == []
    assert report_captured["tool_call_id"] == "tc-followup-no-rerun-no-brief-sync"
    assert result.update["submarine_runtime"]["current_stage"] == "result-reporting"
    assert history_entry["outcome_status"] == "result_report_refreshed"
    assert history_entry["report_refreshed"] is True


def test_submarine_scientific_followup_prefers_latest_user_message_for_output_only_refresh_without_rerun(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-output-refresh-latest-user"
    stale_task_description = (
        "在当前已确认几何、基线案例和 remediation 连续性的基础上，"
        "追加两个交付输出：1）艇体后方尾流速度切片；2）艇体表面与尾迹的流线图。"
        "请先同步设计简报与交付计划。"
    )
    latest_user_message = (
        "继续当前线程：不要重跑 solver。请先同步设计简报与交付计划，"
        "把新增输出明确为尾流速度切片和流线图，再只刷新最终报告与合同快照。"
    )
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "execute-scientific-studies",
            "tool_name": "submarine_solver_dispatch",
            "tool_args": {
                "geometry_path": "/mnt/user-data/uploads/suboff-demo.stl",
                "task_description": stale_task_description,
                "task_type": "resistance",
                "selected_case_id": "darpa_suboff_axisymmetric",
                "execute_scientific_studies": True,
                "confirmation_status": "confirmed",
                "execution_preference": "execute_now",
            },
            "reason": "Refresh delivery contract first and avoid unnecessary reruns.",
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
    runtime.state["submarine_runtime"]["execution_preference"] = "execute_now"
    runtime.state["submarine_runtime"]["requested_outputs"] = []
    runtime.state["submarine_runtime"]["output_delivery_plan"] = []
    runtime.state["messages"] = [
        HumanMessage(
            content=(
                "<uploaded_files>\n"
                "The following files were uploaded in this message:\n\n"
                "(empty)\n"
                "The following files were uploaded in previous messages and are still available:\n\n"
                "- suboff_solid.stl (1.6 MB)\n"
                "  Path: /mnt/user-data/uploads/suboff_solid.stl\n\n"
                "You can read these files using the `read_file` tool with the paths shown above.\n"
                "</uploaded_files>\n\n"
                f"{latest_user_message}"
            )
        )
    ]

    design_brief_captured: dict[str, object] = {}
    dispatch_calls: list[dict[str, object]] = []
    report_captured: dict[str, object] = {}
    synced_requested_outputs = [
        {
            "output_id": "wake_velocity_slice",
            "requested_label": "尾流速度切片",
            "support_level": "supported",
            "delivery_status": "planned",
        },
        {
            "output_id": "streamlines",
            "requested_label": "流线图",
            "support_level": "not_yet_supported",
            "delivery_status": "not_yet_supported",
        },
    ]
    synced_output_delivery_plan = [
        {
            "output_id": "wake_velocity_slice",
            "requested_label": "尾流速度切片",
            "delivery_status": "pending",
        },
        {
            "output_id": "streamlines",
            "requested_label": "流线图",
            "delivery_status": "not_yet_supported",
        },
    ]

    def fake_design_brief_tool(**kwargs):
        design_brief_captured.update(kwargs)
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/design-brief/demo/cfd-design-brief.json"
                ],
                "submarine_runtime": {
                    "current_stage": "task-intelligence",
                    "task_summary": kwargs["task_description"],
                    "requested_outputs": synced_requested_outputs,
                    "output_delivery_plan": synced_output_delivery_plan,
                    "confirmation_status": "confirmed",
                    "execution_preference": "execute_now",
                },
            }
        )

    def fake_solver_dispatch_tool(**kwargs):
        dispatch_calls.append(kwargs)
        return Command(update={})

    def fake_result_report_tool(**kwargs):
        report_captured.update(kwargs)
        return Command(
            update={
                "artifacts": [
                    "/mnt/user-data/outputs/submarine/reports/demo/final-report.json"
                ],
                "submarine_runtime": {
                    "current_stage": "result-reporting",
                    "stage_status": "confirmed",
                    "requested_outputs": synced_requested_outputs,
                    "output_delivery_plan": synced_output_delivery_plan,
                    "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                },
                "messages": [
                    ToolMessage(
                        "Research report regenerated without rerun",
                        tool_call_id=kwargs["tool_call_id"],
                    )
                ],
            }
        )

    monkeypatch.setattr(
        tool_module,
        "submarine_design_brief_tool",
        SimpleNamespace(func=fake_design_brief_tool),
        raising=False,
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
        tool_call_id="tc-followup-output-refresh-latest-user",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert design_brief_captured["task_description"] == latest_user_message
    assert dispatch_calls == []
    assert (
        report_captured["tool_call_id"]
        == "tc-followup-output-refresh-latest-user"
    )
    assert result.update["submarine_runtime"]["current_stage"] == "result-reporting"
    assert history_entry["outcome_status"] == "result_report_refreshed"
    assert history_entry["report_refreshed"] is True
    assert any(
        "Skipped solver rerun" in note for note in history_entry["notes"]
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


def test_submarine_scientific_followup_records_parent_lineage(
    tmp_path, monkeypatch
):
    tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_scientific_followup_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-lineage"
    handoff_virtual_path = _write_handoff_artifact(
        paths,
        thread_id=thread_id,
        payload={
            "handoff_status": "ready_for_auto_followup",
            "recommended_action_id": "regenerate-research-report-linkage",
            "tool_name": "submarine_result_report",
            "tool_args": {
                "report_title": "Lineage refresh report",
            },
            "reason": "Refresh the report after extending the baseline lineage.",
            "source_run_id": "mesh_independence:coarse",
            "baseline_reference_run_id": "baseline",
            "compare_target_run_id": "baseline",
            "derived_run_ids": ["mesh_independence:coarse:followup-1"],
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

    monkeypatch.setattr(
        tool_module,
        "submarine_result_report_tool",
        SimpleNamespace(
            func=lambda **kwargs: Command(
                update={
                    "submarine_runtime": {
                        "current_stage": "result-reporting",
                        "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
                    },
                    "messages": [
                        ToolMessage(
                            "Lineage report regenerated",
                            tool_call_id=kwargs["tool_call_id"],
                        )
                    ],
                }
            )
        ),
        raising=False,
    )

    tool_module.submarine_scientific_followup_tool.func(
        runtime=runtime,
        followup_kind="study_extension",
        tool_call_id="tc-followup-lineage",
    )

    history = _read_report_artifact(
        paths,
        thread_id=thread_id,
        filename="scientific-followup-history.json",
    )
    history_entry = history["entries"][0]

    assert history_entry["source_run_id"] == "mesh_independence:coarse"
    assert history_entry["baseline_reference_run_id"] == "baseline"
    assert history_entry["compare_target_run_id"] == "baseline"
    assert history_entry["derived_run_ids"] == ["mesh_independence:coarse:followup-1"]
