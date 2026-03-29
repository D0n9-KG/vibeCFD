import importlib
import json
from types import SimpleNamespace

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

    message = result.update["messages"][0]
    assert "manual_followup_required" in message.content
    assert "attach-validation-reference" in message.content
    assert "No applicable benchmark target was available" in message.content
    assert "submarine_runtime" not in result.update


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

    message = result.update["messages"][0]
    assert "not_needed" in message.content
    assert "Scientific remediation is not needed" in message.content
    assert "submarine_runtime" not in result.update
