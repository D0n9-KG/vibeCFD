import importlib
import json
import zipfile
from types import SimpleNamespace

from deerflow.config.paths import Paths

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


def test_submarine_skill_studio_tool_generates_publish_ready_workspace_artifacts(
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
        skill_name="Submarine Result Acceptance",
        skill_purpose=("Define how Claude Code and reporting subagents should decide whether a submarine CFD run is trustworthy, needs review, or should be rerun."),
        trigger_conditions=[
            "the user asks whether the current CFD result is trustworthy",
            "Claude Code needs a final acceptance decision before delivery",
        ],
        workflow_steps=[
            "review mesh, residual, and force summaries from the current run",
            "decide whether the run is deliverable, risky, or should be rerun",
            "produce a Chinese acceptance conclusion with evidence and next-step advice",
        ],
        expert_rules=[
            "treat obviously drifting residual histories as risky unless the report explains why",
            "flag drag values that materially diverge from the baseline case family",
        ],
        acceptance_criteria=[
            "state an explicit delivery decision",
            "cite which CFD indicators support that decision",
        ],
        test_scenarios=[
            "baseline steady-state bare-hull case with stable Cd and residual decay",
            "report generated despite residuals staying high and force history oscillating",
        ],
        tool_call_id="tc-skill-studio-1",
    )

    artifacts = result.update["artifacts"]
    assert any(path.endswith("/skill-draft.json") for path in artifacts)
    assert any(path.endswith("/skill-lifecycle.json") for path in artifacts)
    assert any(path.endswith("/skill-package.json") for path in artifacts)
    assert any(path.endswith("/SKILL.md") for path in artifacts)
    assert any(path.endswith("/agents/openai.yaml") for path in artifacts)
    assert any(path.endswith("/test-matrix.json") for path in artifacts)
    assert any(path.endswith("/validation-report.json") for path in artifacts)
    assert any(path.endswith("/validation-report.md") for path in artifacts)
    assert any(path.endswith("/publish-readiness.json") for path in artifacts)
    assert any(path.endswith("/publish-readiness.md") for path in artifacts)
    assert any(path.endswith("/dry-run-evidence.json") for path in artifacts)
    assert any(path.endswith("/references/domain-rules.md") for path in artifacts)
    assert any(path.endswith("/submarine-result-acceptance.skill") for path in artifacts)

    draft_dir = outputs_dir / "submarine" / "skill-studio" / "submarine-result-acceptance"
    payload = json.loads((draft_dir / "skill-draft.json").read_text(encoding="utf-8"))
    package_payload = json.loads(
        (draft_dir / "skill-package.json").read_text(encoding="utf-8"),
    )
    lifecycle_payload = json.loads(
        (draft_dir / "skill-lifecycle.json").read_text(encoding="utf-8"),
    )
    test_matrix = json.loads(
        (draft_dir / "test-matrix.json").read_text(encoding="utf-8"),
    )
    validation = json.loads(
        (draft_dir / "validation-report.json").read_text(encoding="utf-8"),
    )
    publish_readiness = json.loads(
        (draft_dir / "publish-readiness.json").read_text(encoding="utf-8"),
    )
    dry_run_evidence = json.loads(
        (draft_dir / "dry-run-evidence.json").read_text(encoding="utf-8"),
    )
    skill_markdown = (draft_dir / "SKILL.md").read_text(encoding="utf-8")
    openai_yaml = (draft_dir / "agents" / "openai.yaml").read_text(
        encoding="utf-8",
    )
    archive_path = draft_dir / "submarine-result-acceptance.skill"

    assert payload["skill_name"] == "submarine-result-acceptance"
    assert payload["assistant_mode"] == "claude-code-skill-creator"
    assert payload["builtin_skills"] == ["skill-creator", "writing-skills"]
    assert payload["skill_asset_id"] == "submarine-result-acceptance"
    assert payload["source_thread_id"] == thread_id
    assert payload["test_status"] == "ready_for_dry_run"
    assert payload["publish_status"] == "ready_for_review"
    assert payload["lifecycle_virtual_path"].endswith("/skill-lifecycle.json")
    assert payload["version_note"] == ""
    assert payload["bindings"] == []

    assert lifecycle_payload["skill_asset_id"] == "submarine-result-acceptance"
    assert lifecycle_payload["draft_status"] == "draft_ready"
    assert lifecycle_payload["bindings"] == []
    assert lifecycle_payload["published_revisions"] == []
    assert lifecycle_payload["source_thread_id"] == thread_id

    assert package_payload["assistant_mode"] == "claude-code-skill-creator"
    assert package_payload["ui_metadata_virtual_path"].endswith("/agents/openai.yaml")

    assert test_matrix["status"] == "ready_for_dry_run"
    assert len(test_matrix["scenario_tests"]) == 2

    assert validation["status"] == "ready_for_review"
    assert validation["error_count"] == 0
    assert validation["checks"]["description_starts_with_use_when"] == "passed"

    assert publish_readiness["status"] == "ready_for_review"
    assert publish_readiness["publish_gate_count"] >= 4
    assert dry_run_evidence["status"] == "not_recorded"
    assert dry_run_evidence["thread_id"] == thread_id
    assert dry_run_evidence["scenario_id"] is None
    assert dry_run_evidence["message_ids"] == []
    assert archive_path.is_file() is True

    with zipfile.ZipFile(archive_path, "r") as archive:
        archive_entries = set(archive.namelist())

    assert "submarine-result-acceptance/dry-run-evidence.json" in archive_entries
    assert "submarine-result-acceptance/publish-readiness.json" in archive_entries

    assert skill_markdown.startswith("---\nname: submarine-result-acceptance\n")
    assert "description: Use when" in skill_markdown
    assert "## Workflow" in skill_markdown
    assert "## Acceptance Criteria" in skill_markdown
    assert "display_name: Submarine Result Acceptance" in openai_yaml

    studio_state = result.update["submarine_skill_studio"]
    assert studio_state["skill_name"] == "submarine-result-acceptance"
    assert studio_state["skill_asset_id"] == "submarine-result-acceptance"
    assert studio_state["assistant_mode"] == "claude-code-skill-creator"
    assert studio_state["builtin_skills"] == ["skill-creator", "writing-skills"]
    assert studio_state["validation_status"] == "ready_for_review"
    assert studio_state["test_status"] == "ready_for_dry_run"
    assert studio_state["publish_status"] == "ready_for_review"
    assert studio_state["error_count"] == 0
    assert studio_state["report_virtual_path"].endswith("/validation-report.md")
    assert studio_state["lifecycle_virtual_path"].endswith("/skill-lifecycle.json")
    assert studio_state["dry_run_evidence_status"] == "not_recorded"
    assert studio_state["dry_run_evidence_virtual_path"].endswith("/dry-run-evidence.json")
    assert studio_state["active_revision_id"] is None
    assert studio_state["published_revision_id"] is None
    assert studio_state["version_note"] == ""
    assert studio_state["bindings"] == []
    assert studio_state["artifact_virtual_paths"]


def test_submarine_skill_studio_tool_uses_selected_skill_creator_agent_profile(
    tmp_path,
    monkeypatch,
):
    from deerflow.config.agents_config import AgentConfig

    paths = Paths(tmp_path)
    thread_id = "thread-1"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(
        "deerflow.domain.submarine.skill_studio.load_agent_config",
        lambda name: AgentConfig(
            name=name or "codex-skill-creator",
            description="Dedicated Codex agent for Skill Studio.",
            display_name="Codex · Skill Creator",
            model="gpt-5.4",
        ),
    )

    runtime = _make_runtime(paths, thread_id)
    runtime.context["agent_name"] = "codex-skill-creator"

    result = tool_module.submarine_skill_studio_tool.func(
        runtime=runtime,
        skill_name="Submarine Result Acceptance",
        skill_purpose="Draft a reviewable submarine acceptance skill package.",
        tool_call_id="tc-skill-studio-codex",
    )

    draft_dir = outputs_dir / "submarine" / "skill-studio" / "submarine-result-acceptance"
    payload = json.loads((draft_dir / "skill-draft.json").read_text(encoding="utf-8"))
    package_payload = json.loads(
        (draft_dir / "skill-package.json").read_text(encoding="utf-8"),
    )
    studio_state = result.update["submarine_skill_studio"]

    assert payload["assistant_mode"] == "codex-skill-creator"
    assert payload["assistant_label"] == "Codex · Skill Creator"
    assert package_payload["assistant_mode"] == "codex-skill-creator"
    assert package_payload["assistant_label"] == "Codex · Skill Creator"
    assert studio_state["assistant_mode"] == "codex-skill-creator"
    assert studio_state["assistant_label"] == "Codex · Skill Creator"
