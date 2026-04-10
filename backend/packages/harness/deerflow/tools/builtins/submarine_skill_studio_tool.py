"""Built-in DeerFlow tool for Skill Studio drafting and validation."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.config.paths import get_paths
from deerflow.domain.submarine.skill_studio import run_skill_studio

_LIST_ITEM_PREFIX_RE = re.compile(r"^(?:[-*]\s+|\d+[.)]\s+)")


def _get_thread_id(runtime: ToolRuntime[ContextT, ThreadState]) -> str:
    thread_id = runtime.context.get("thread_id") if runtime.context else None
    if not thread_id:
        raise ValueError("Thread ID is not available in runtime context")
    return thread_id


def _get_thread_dir(runtime: ToolRuntime[ContextT, ThreadState], key: str) -> Path:
    thread_data = (runtime.state or {}).get("thread_data") or {}
    raw_path = thread_data.get(key)
    if raw_path:
        return Path(raw_path).resolve()

    thread_id = _get_thread_id(runtime)
    paths = get_paths()
    fallback_dirs = {
        "uploads_path": paths.sandbox_uploads_dir(thread_id),
        "outputs_path": paths.sandbox_outputs_dir(thread_id),
    }
    fallback = fallback_dirs.get(key)
    if fallback is None:
        raise ValueError(f"Thread data missing required path: {key}")
    return fallback.resolve()


def _normalize_string_list(value: str | list[str] | None) -> list[str] | None:
    if value is None:
        return None

    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            candidate = item.strip() if isinstance(item, str) else str(item).strip()
            if candidate:
                normalized.append(candidate)
        return normalized

    candidate = value.strip()
    if not candidate:
        return []

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        return _normalize_string_list(parsed)

    if "\n" in candidate:
        normalized_lines: list[str] = []
        for line in candidate.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            normalized = _LIST_ITEM_PREFIX_RE.sub("", stripped, count=1).strip()
            if normalized:
                normalized_lines.append(normalized)
        return normalized_lines

    return [candidate]


@tool("submarine_skill_studio", parse_docstring=True)
def submarine_skill_studio_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    skill_name: str,
    skill_purpose: str,
    trigger_conditions: str | list[str] | None = None,
    workflow_steps: str | list[str] | None = None,
    expert_rules: str | list[str] | None = None,
    acceptance_criteria: str | list[str] | None = None,
    test_scenarios: str | list[str] | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Create and validate a publish-ready Skill Studio package for a reusable DeerFlow skill.

    Args:
        skill_name: Human-readable title for the skill. The tool will normalize it into a slug-safe skill name.
        skill_purpose: What the skill should help Codex, Claude Code, or subagents accomplish.
        trigger_conditions: Phrases that describe when the skill should trigger.
        workflow_steps: Ordered workflow steps the skill should teach.
        expert_rules: Domain rules, thresholds, or heuristics provided by the expert.
        acceptance_criteria: What outputs or decisions the skill must reliably produce.
        test_scenarios: Realistic scenarios used to validate the drafted skill before publishing.
    """
    try:
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        payload, artifacts = run_skill_studio(
            outputs_dir=outputs_dir,
            skill_name=skill_name,
            skill_purpose=skill_purpose,
            trigger_conditions=_normalize_string_list(trigger_conditions),
            workflow_steps=_normalize_string_list(workflow_steps),
            expert_rules=_normalize_string_list(expert_rules),
            acceptance_criteria=_normalize_string_list(acceptance_criteria),
            test_scenarios=_normalize_string_list(test_scenarios),
            assistant_mode=runtime.context.get("agent_name") if runtime.context else None,
            source_thread_id=_get_thread_id(runtime),
        )
    except ValueError as exc:
        return Command(
            update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]},
        )

    skill_studio_state = {
        "skill_name": payload["skill_name"],
        "skill_asset_id": payload["skill_asset_id"],
        "assistant_mode": payload["assistant_mode"],
        "assistant_label": payload["assistant_label"],
        "builtin_skills": payload["builtin_skills"],
        "validation_status": payload["validation_status"],
        "test_status": payload["test_status"],
        "publish_status": payload["publish_status"],
        "error_count": payload["error_count"],
        "warning_count": payload["warning_count"],
        "report_virtual_path": payload["report_virtual_path"],
        "package_virtual_path": payload["package_virtual_path"],
        "package_archive_virtual_path": payload["package_archive_virtual_path"],
        "draft_virtual_path": payload["draft_virtual_path"],
        "lifecycle_virtual_path": payload["lifecycle_virtual_path"],
        "test_virtual_path": payload["test_virtual_path"],
        "publish_virtual_path": payload["publish_virtual_path"],
        "dry_run_evidence_status": payload["dry_run_evidence_status"],
        "dry_run_evidence_virtual_path": payload["dry_run_evidence_virtual_path"],
        "ui_metadata_virtual_path": payload["ui_metadata_virtual_path"],
        "active_revision_id": payload["active_revision_id"],
        "published_revision_id": payload["published_revision_id"],
        "version_note": payload["version_note"],
        "bindings": payload["bindings"],
        "artifact_virtual_paths": artifacts,
    }
    detail_lines = "\n".join(f"- {artifact}" for artifact in artifacts)
    message = (
        f"Generated Skill Studio package `{payload['skill_name']}` and completed the initial validation pass.\n"
        f"Current validation status: `{payload['validation_status']}`.\n"
        f"Registered {len(artifacts)} Skill Studio artifacts for review:\n{detail_lines}"
    )
    return Command(
        update={
            "artifacts": artifacts,
            "submarine_skill_studio": skill_studio_state,
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
        },
    )
