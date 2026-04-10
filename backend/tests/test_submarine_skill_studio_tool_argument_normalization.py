import importlib
import json
from types import SimpleNamespace

from deerflow.config.paths import Paths
from langchain.tools import ToolRuntime

tool_module = importlib.import_module(
    "deerflow.tools.builtins.submarine_skill_studio_tool",
)


def _make_runtime(paths: Paths, thread_id: str = "thread-1") -> SimpleNamespace:
    return SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(paths.sandbox_outputs_dir(thread_id)),
            },
        },
        context={"thread_id": thread_id},
    )


def test_submarine_skill_studio_tool_input_schema_accepts_stringified_list_fields(
    tmp_path,
):
    paths = Paths(tmp_path)
    runtime = ToolRuntime(
        state={
            "messages": [],
            "submarine_runtime": {},
            "artifacts": [],
            "viewed_images": {},
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir("thread-1")),
                "outputs_path": str(paths.sandbox_outputs_dir("thread-1")),
            },
        },
        context=None,
        config={},
        stream_writer=lambda _: None,
        tool_call_id="tc-stringified-lists",
        store=None,
    )

    payload = tool_module.submarine_skill_studio_tool.args_schema.model_validate(
        {
            "runtime": runtime,
            "skill_name": "Skill Workbench Ping",
            "skill_purpose": "Verify the Skill Studio pipeline is healthy.",
            "trigger_conditions": '["test skill", "ping skill studio"]',
            "workflow_steps": '["confirm trigger", "write output artifact"]',
            "expert_rules": '["artifact must land in outputs"]',
            "acceptance_criteria": '["tool invocation succeeds"]',
            "test_scenarios": '["normal smoke path"]',
            "tool_call_id": "tc-stringified-lists",
        }
    )

    assert payload.trigger_conditions == '["test skill", "ping skill studio"]'
    assert payload.workflow_steps == '["confirm trigger", "write output artifact"]'


def test_submarine_skill_studio_tool_normalizes_stringified_list_fields(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_skill_studio_tool.func(
        runtime=_make_runtime(paths, thread_id),
        skill_name="Skill Workbench Ping",
        skill_purpose="Verify the Skill Studio pipeline is healthy.",
        trigger_conditions='["test skill", "ping skill studio"]',
        workflow_steps='["confirm trigger", "write output artifact"]',
        expert_rules='["artifact must land in outputs"]',
        acceptance_criteria='["tool invocation succeeds"]',
        test_scenarios='["normal smoke path"]',
        tool_call_id="tc-stringified-lists",
    )

    draft_dir = outputs_dir / "submarine" / "skill-studio" / "skill-workbench-ping"
    payload = json.loads((draft_dir / "skill-draft.json").read_text(encoding="utf-8"))

    assert payload["trigger_conditions"] == [
        "test skill",
        "ping skill studio",
    ]
    assert payload["workflow_steps"] == [
        "confirm trigger",
        "write output artifact",
    ]
    assert payload["expert_rules"] == ["artifact must land in outputs"]
    assert payload["acceptance_criteria"] == ["tool invocation succeeds"]
    assert payload["test_scenarios"] == ["normal smoke path"]
    assert result.update["submarine_skill_studio"]["validation_status"] == "ready_for_review"


def test_normalize_string_list_preserves_single_entry_commas():
    assert tool_module._normalize_string_list("Keep Re < 1e6, use k-omega SST.") == [
        "Keep Re < 1e6, use k-omega SST."
    ]


def test_normalize_string_list_preserves_numeric_prefixes_in_newline_values():
    assert tool_module._normalize_string_list("1.2 m hull length\n2026-04-10 baseline review") == [
        "1.2 m hull length",
        "2026-04-10 baseline review",
    ]
