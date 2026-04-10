from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import override

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelCallResult, ModelRequest, ModelResponse
from langchain_core.messages import SystemMessage
from langgraph.config import get_config
from langgraph.runtime import Runtime

from deerflow.agents.lead_agent.prompt import apply_prompt_template
from deerflow.agents.thread_state import SkillRuntimeSnapshotState, ThreadState
from deerflow.domain.submarine.skill_lifecycle import (
    get_skill_lifecycle_registry_path,
    load_skill_lifecycle_registry,
    utc_timestamp,
)
from deerflow.skills.loader import get_skills_root_path, load_skills as load_skills_from_path


def _resolve_skills_root() -> Path:
    try:
        from deerflow.config import get_app_config

        return get_app_config().skills.get_skills_path()
    except Exception:
        return get_skills_root_path()


def _get_container_base_path() -> str:
    try:
        from deerflow.config import get_app_config

        return get_app_config().skills.container_path
    except Exception:
        return "/mnt/skills"


def _resolve_binding_targets(
    *,
    registry,
    enabled_skill_names: list[str],
) -> tuple[list[str], list[dict[str, object]]]:
    enabled_name_set = set(enabled_skill_names)
    resolved_targets: dict[str, list[str]] = {}

    for record in registry.records.values():
        if not record.enabled:
            continue

        for binding in record.binding_targets:
            if binding.mode != "explicit":
                continue

            targets = sorted(
                target
                for target in (binding.target_skills or [record.skill_name])
                if target in enabled_name_set
            )
            if not targets:
                continue

            existing_targets = resolved_targets.setdefault(binding.role_id, [])
            for target in targets:
                if target not in existing_targets:
                    existing_targets.append(target)

    applied_roles = sorted(resolved_targets)
    resolved_entries = [
        {"role_id": role_id, "target_skills": sorted(targets)}
        for role_id, targets in sorted(resolved_targets.items())
    ]
    return applied_roles, resolved_entries


def capture_skill_runtime_snapshot() -> SkillRuntimeSnapshotState:
    skills_root = _resolve_skills_root()
    registry_path = get_skill_lifecycle_registry_path(skills_root)
    registry = load_skill_lifecycle_registry(registry_path=registry_path)
    fresh_enabled_skills = sorted(
        load_skills_from_path(
            skills_path=skills_root,
            use_config=True,
            enabled_only=True,
        ),
        key=lambda skill: skill.name,
    )
    enabled_skill_names = [skill.name for skill in fresh_enabled_skills]
    binding_targets_applied, resolved_binding_targets = _resolve_binding_targets(
        registry=registry,
        enabled_skill_names=enabled_skill_names,
    )
    container_base_path = _get_container_base_path()

    return {
        "runtime_revision": registry.runtime_revision,
        "captured_at": utc_timestamp(),
        "enabled_skill_names": enabled_skill_names,
        "binding_targets_applied": binding_targets_applied,
        "source_registry_path": str(registry_path),
        "skill_prompt_entries": [
            {
                "name": skill.name,
                "description": skill.description,
                "location": skill.get_container_file_path(container_base_path),
            }
            for skill in fresh_enabled_skills
        ],
        "resolved_binding_targets": resolved_binding_targets,
    }


def _get_runtime_configurable() -> dict:
    try:
        return get_config().get("configurable", {})
    except RuntimeError:
        return {}


def _backfill_legacy_snapshot(
    snapshot: SkillRuntimeSnapshotState,
) -> SkillRuntimeSnapshotState:
    if snapshot.get("skill_prompt_entries"):
        return snapshot

    snapshot_skill_names = [
        name
        for name in snapshot.get("enabled_skill_names", [])
        if isinstance(name, str) and name
    ]
    if not snapshot_skill_names:
        return snapshot

    skills_root = _resolve_skills_root()
    all_skills = load_skills_from_path(
        skills_path=skills_root,
        use_config=False,
        enabled_only=False,
    )
    skills_by_name = {
        skill.name: skill
        for skill in all_skills
        if skill.name in set(snapshot_skill_names)
    }
    container_base_path = _get_container_base_path()
    prompt_entries = [
        {
            "name": skill_name,
            "description": skills_by_name[skill_name].description,
            "location": skills_by_name[skill_name].get_container_file_path(
                container_base_path
            ),
        }
        for skill_name in snapshot_skill_names
        if skill_name in skills_by_name
    ]
    if not prompt_entries:
        return snapshot

    return {
        **snapshot,
        "skill_prompt_entries": prompt_entries,
    }


class SkillRuntimeSnapshotMiddleware(AgentMiddleware[ThreadState]):
    state_schema = ThreadState

    def _override_skill_snapshot(
        self,
        request: ModelRequest,
        snapshot: SkillRuntimeSnapshotState,
    ) -> ModelRequest:
        snapshot = _backfill_legacy_snapshot(snapshot)
        configurable = _get_runtime_configurable()
        system_prompt = apply_prompt_template(
            subagent_enabled=configurable.get("subagent_enabled", False),
            max_concurrent_subagents=configurable.get(
                "max_concurrent_subagents",
                3,
            ),
            agent_name=configurable.get("agent_name"),
            available_skills=set(snapshot.get("enabled_skill_names", [])),
            skill_snapshot=snapshot,
        )
        return request.override(
            system_message=SystemMessage(content=system_prompt),
        )

    @override
    def before_model(self, state: ThreadState, runtime: Runtime) -> dict | None:
        snapshot = state.get("skill_runtime_snapshot")
        if snapshot:
            upgraded_snapshot = _backfill_legacy_snapshot(snapshot)
            if upgraded_snapshot != snapshot:
                return {"skill_runtime_snapshot": upgraded_snapshot}
            return None
        return {"skill_runtime_snapshot": capture_skill_runtime_snapshot()}

    @override
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        snapshot = request.state.get("skill_runtime_snapshot")
        if snapshot is None:
            snapshot = capture_skill_runtime_snapshot()
            request = request.override(
                state={
                    **dict(request.state or {}),
                    "skill_runtime_snapshot": snapshot,
                },
            )
        else:
            upgraded_snapshot = _backfill_legacy_snapshot(snapshot)
            if upgraded_snapshot != snapshot:
                snapshot = upgraded_snapshot
                request = request.override(
                    state={
                        **dict(request.state or {}),
                        "skill_runtime_snapshot": snapshot,
                    },
                )
        return handler(self._override_skill_snapshot(request, snapshot))

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        snapshot = request.state.get("skill_runtime_snapshot")
        if snapshot is None:
            snapshot = capture_skill_runtime_snapshot()
            request = request.override(
                state={
                    **dict(request.state or {}),
                    "skill_runtime_snapshot": snapshot,
                },
            )
        else:
            upgraded_snapshot = _backfill_legacy_snapshot(snapshot)
            if upgraded_snapshot != snapshot:
                snapshot = upgraded_snapshot
                request = request.override(
                    state={
                        **dict(request.state or {}),
                        "skill_runtime_snapshot": snapshot,
                    },
                )
        return await handler(self._override_skill_snapshot(request, snapshot))
