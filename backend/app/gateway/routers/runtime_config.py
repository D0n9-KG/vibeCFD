from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.model_availability import resolve_model_availability
from app.gateway.model_catalog import (
    get_effective_models,
    get_model_config_by_name,
    resolve_provider_key,
    resolve_provider_label,
)
from deerflow.config import get_app_config
from deerflow.config.app_config import AppConfig
from deerflow.config.extensions_config import ExtensionsConfig
from deerflow.config.runtime_config_overrides import (
    RuntimeConfigOverrides,
    RuntimeLeadAgentOverride,
    RuntimeStageRoleOverride,
    get_runtime_config_overrides,
    save_runtime_config_overrides,
)
from deerflow.domain.submarine.roles import get_subagent_role_boundaries
from deerflow.subagents.registry import get_subagent_config

router = APIRouter(prefix="/api", tags=["runtime-config"])


class RuntimeLeadAgentResponse(BaseModel):
    default_model: str | None = None
    config_source: str
    is_overridden: bool = False


class RuntimeModelSummaryResponse(BaseModel):
    name: str
    display_name: str | None = None
    description: str | None = None
    provider_key: str
    provider_label: str
    is_available: bool
    availability_reason: str | None = None
    supports_thinking: bool = False
    supports_reasoning_effort: bool = False


class RuntimeProviderSummaryResponse(BaseModel):
    provider_key: str
    label: str
    model_names: list[str] = Field(default_factory=list)
    is_available: bool
    availability_reason: str | None = None


class RuntimeStageRoleResponse(BaseModel):
    role_id: str
    subagent_name: str
    display_title: str
    model_mode: Literal["inherit", "explicit"]
    effective_model: str | None = None
    config_source: str
    timeout_seconds: int


class RuntimeProvenanceResponse(BaseModel):
    config_path: str | None = None
    extensions_config_path: str | None = None
    runtime_overrides_path: str | None = None
    langgraph_url: str | None = None


class RuntimeConfigSummaryResponse(BaseModel):
    lead_agent: RuntimeLeadAgentResponse
    models: list[RuntimeModelSummaryResponse] = Field(default_factory=list)
    providers: list[RuntimeProviderSummaryResponse] = Field(default_factory=list)
    stage_roles: list[RuntimeStageRoleResponse] = Field(default_factory=list)
    provenance: RuntimeProvenanceResponse


class RuntimeLeadAgentUpdateRequest(BaseModel):
    default_model: str | None = Field(
        default=None,
        description="Optional explicit default model override for the lead agent.",
    )


class RuntimeStageRoleUpdateRequest(BaseModel):
    role_id: str
    model_mode: Literal["inherit", "explicit"]
    model_name: str | None = None


class RuntimeConfigUpdateRequest(BaseModel):
    lead_agent: RuntimeLeadAgentUpdateRequest
    stage_roles: list[RuntimeStageRoleUpdateRequest] = Field(default_factory=list)


def _resolve_provider_details(model) -> tuple[str, str]:
    provider_key = resolve_provider_key(model)
    return provider_key, resolve_provider_label(provider_key)


def _resolve_langgraph_url(config) -> str | None:
    extra = getattr(config, "model_extra", None)
    if not isinstance(extra, dict):
        return None
    channels = extra.get("channels")
    if not isinstance(channels, dict):
        return None
    langgraph_url = channels.get("langgraph_url")
    if isinstance(langgraph_url, str) and langgraph_url.strip():
        return langgraph_url.strip()
    return None


def _resolve_optional_path(resolver) -> str | None:
    try:
        resolved = resolver()
    except Exception:
        return None
    if resolved is None:
        return None
    return str(resolved)


def _get_model_config(config, model_name: str):
    return get_model_config_by_name(config, model_name)


def _resolve_effective_default_model(
    config,
    runtime_overrides: RuntimeConfigOverrides,
) -> tuple[str | None, bool]:
    configured_default_model = config.models[0].name if config.models else None
    runtime_default_model = runtime_overrides.lead_agent.default_model

    if runtime_default_model and _get_model_config(config, runtime_default_model):
        return runtime_default_model, True

    return configured_default_model, False


def _build_runtime_config_summary(
    *,
    config=None,
    runtime_overrides: RuntimeConfigOverrides | None = None,
) -> RuntimeConfigSummaryResponse:
    config = config or get_app_config()
    runtime_overrides = runtime_overrides or get_runtime_config_overrides()
    runtime_overrides_path = _resolve_optional_path(
        RuntimeConfigOverrides.resolve_config_path
    )

    default_model, lead_is_overridden = _resolve_effective_default_model(
        config,
        runtime_overrides,
    )

    lead_agent = RuntimeLeadAgentResponse(
        default_model=default_model,
        config_source=(
            f"runtime-config:{runtime_overrides_path}"
            if lead_is_overridden and runtime_overrides_path
            else "runtime-config"
            if lead_is_overridden
            else "config.yaml:models[0]"
            if default_model is not None
            else "unconfigured"
        ),
        is_overridden=lead_is_overridden,
    )

    model_summaries: list[RuntimeModelSummaryResponse] = []
    provider_summaries: dict[str, RuntimeProviderSummaryResponse] = {}
    for model in get_effective_models(config):
        provider_key, provider_label = _resolve_provider_details(model)
        is_available, availability_reason = resolve_model_availability(model)
        model_summaries.append(
            RuntimeModelSummaryResponse(
                name=model.name,
                display_name=model.display_name,
                description=model.description,
                provider_key=provider_key,
                provider_label=provider_label,
                is_available=is_available,
                availability_reason=availability_reason,
                supports_thinking=model.supports_thinking,
                supports_reasoning_effort=model.supports_reasoning_effort,
            )
        )

        provider_summary = provider_summaries.get(provider_key)
        if provider_summary is None:
            provider_summary = RuntimeProviderSummaryResponse(
                provider_key=provider_key,
                label=provider_label,
                model_names=[],
                is_available=False,
                availability_reason=availability_reason,
            )
            provider_summaries[provider_key] = provider_summary

        provider_summary.model_names.append(model.name)
        provider_summary.is_available = provider_summary.is_available or is_available
        if provider_summary.is_available:
            provider_summary.availability_reason = None
        elif provider_summary.availability_reason is None:
            provider_summary.availability_reason = availability_reason

    stage_roles: list[RuntimeStageRoleResponse] = []
    for role in get_subagent_role_boundaries():
        subagent_name = f"submarine-{role.role_id}"
        subagent_config = get_subagent_config(subagent_name)
        role_override = runtime_overrides.stage_roles.get(role.role_id)
        override_model_name = (
            role_override.model_name
            if role_override is not None
            and role_override.model_mode == "explicit"
            and role_override.model_name
            and _get_model_config(config, role_override.model_name)
            else None
        )

        model_mode = "inherit"
        effective_model = default_model
        timeout_seconds = 0
        config_source = "builtin:subagent"

        if subagent_config is not None:
            timeout_seconds = subagent_config.timeout_seconds
            if override_model_name is not None:
                model_mode = "explicit"
                effective_model = override_model_name
                config_source = (
                    f"runtime-config:{runtime_overrides_path}"
                    if runtime_overrides_path
                    else "runtime-config"
                )
            elif subagent_config.model != "inherit":
                model_mode = "explicit"
                effective_model = subagent_config.model
        else:
            config_source = "missing:subagent"

        stage_roles.append(
            RuntimeStageRoleResponse(
                role_id=role.role_id,
                subagent_name=subagent_name,
                display_title=role.title,
                model_mode=model_mode,
                effective_model=effective_model,
                config_source=config_source,
                timeout_seconds=timeout_seconds,
            )
        )

    provenance = RuntimeProvenanceResponse(
        config_path=_resolve_optional_path(AppConfig.resolve_config_path),
        extensions_config_path=_resolve_optional_path(
            ExtensionsConfig.resolve_config_path
        ),
        runtime_overrides_path=runtime_overrides_path,
        langgraph_url=_resolve_langgraph_url(config),
    )

    return RuntimeConfigSummaryResponse(
        lead_agent=lead_agent,
        models=model_summaries,
        providers=list(provider_summaries.values()),
        stage_roles=stage_roles,
        provenance=provenance,
    )


def _ensure_model_exists(config, model_name: str, *, field_name: str) -> None:
    if _get_model_config(config, model_name):
        return

    raise HTTPException(
        status_code=422,
        detail=f"{field_name} references unknown model '{model_name}'.",
    )


def _validate_update_request(
    request: RuntimeConfigUpdateRequest,
    config,
) -> None:
    if request.lead_agent.default_model:
        _ensure_model_exists(
            config,
            request.lead_agent.default_model,
            field_name="lead_agent.default_model",
        )

    valid_role_ids = {role.role_id for role in get_subagent_role_boundaries()}
    for stage_role in request.stage_roles:
        if stage_role.role_id not in valid_role_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown stage role '{stage_role.role_id}'.",
            )

        if stage_role.model_mode == "explicit":
            if not stage_role.model_name:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"stage_roles[{stage_role.role_id}] requires model_name "
                        "when model_mode='explicit'."
                    ),
                )
            _ensure_model_exists(
                config,
                stage_role.model_name,
                field_name=f"stage_roles[{stage_role.role_id}].model_name",
            )


@router.get(
    "/runtime-config",
    response_model=RuntimeConfigSummaryResponse,
    summary="Get Runtime Configuration Summary",
    description=(
        "Summarize lead-agent defaults, stage-role effective models, "
        "provider availability, and config provenance without exposing secrets."
    ),
)
async def get_runtime_config_summary() -> RuntimeConfigSummaryResponse:
    return _build_runtime_config_summary()


@router.put(
    "/runtime-config",
    response_model=RuntimeConfigSummaryResponse,
    summary="Update Runtime Configuration Overrides",
    description=(
        "Persist canonical runtime overrides for the lead-agent default model "
        "and stage-role model routing without exposing secrets."
    ),
)
async def update_runtime_config(
    request: RuntimeConfigUpdateRequest,
) -> RuntimeConfigSummaryResponse:
    config = get_app_config()
    _validate_update_request(request, config)

    current_overrides = get_runtime_config_overrides()
    stage_role_overrides = dict(current_overrides.stage_roles)

    for stage_role in request.stage_roles:
        if stage_role.model_mode == "inherit":
            stage_role_overrides.pop(stage_role.role_id, None)
            continue

        stage_role_overrides[stage_role.role_id] = RuntimeStageRoleOverride(
            model_mode=stage_role.model_mode,
            model_name=stage_role.model_name,
        )

    overrides_to_save = RuntimeConfigOverrides(
        lead_agent=RuntimeLeadAgentOverride(
            default_model=request.lead_agent.default_model or None,
        ),
        stage_roles=stage_role_overrides,
    )

    saved_overrides = save_runtime_config_overrides(overrides_to_save)
    effective_overrides = saved_overrides or overrides_to_save
    return _build_runtime_config_summary(
        config=config,
        runtime_overrides=effective_overrides,
    )
