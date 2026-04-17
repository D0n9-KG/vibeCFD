from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.model_availability import resolve_model_availability
from app.gateway.model_catalog import resolve_provider_label
from deerflow.config import get_app_config
from deerflow.config.runtime_config_overrides import (
    RuntimeConfigOverrides,
    RuntimeLeadAgentOverride,
    get_runtime_config_overrides,
    save_runtime_config_overrides,
)
from deerflow.config.runtime_models import (
    RuntimeModelDefinition,
    RuntimeModelRegistry,
    build_runtime_model_config,
    get_runtime_model_registry,
    get_runtime_model_secrets,
    save_runtime_model_registry,
    save_runtime_model_secrets,
)

router = APIRouter(prefix="/api", tags=["runtime-config"])


class RuntimeModelResponse(BaseModel):
    name: str
    display_name: str | None = None
    description: str | None = None
    provider_key: str
    provider_label: str
    model: str
    base_url: str | None = None
    has_api_key: bool = False
    supports_thinking: bool = False
    supports_reasoning_effort: bool = False
    supports_vision: bool = False
    is_available: bool = True
    availability_reason: str | None = None
    source: Literal["config", "runtime"]
    is_editable: bool


class RuntimeModelsListResponse(BaseModel):
    models: list[RuntimeModelResponse] = Field(default_factory=list)


class RuntimeModelCreateRequest(BaseModel):
    name: str = Field(pattern=RuntimeModelDefinition.model_fields["name"].metadata[0].pattern)
    display_name: str | None = None
    description: str | None = None
    provider_key: Literal["openai", "openai-compatible", "anthropic"]
    model: str
    base_url: str | None = None
    api_key: str | None = None
    supports_thinking: bool = False
    supports_reasoning_effort: bool = False
    supports_vision: bool = False


class RuntimeModelUpdateRequest(BaseModel):
    display_name: str | None = None
    description: str | None = None
    provider_key: Literal["openai", "openai-compatible", "anthropic"]
    model: str
    base_url: str | None = None
    api_key: str | None = None
    clear_api_key: bool = False
    supports_thinking: bool = False
    supports_reasoning_effort: bool = False
    supports_vision: bool = False


class RuntimeModelDeleteResponse(BaseModel):
    deleted: bool
    name: str


def _provider_label(provider_key: str) -> str:
    return resolve_provider_label(provider_key)


def _provider_key_from_use(provider_use: str) -> str:
    if provider_use.startswith("deerflow.models.claude_provider:") or provider_use.startswith(
        "langchain_anthropic:"
    ):
        return "anthropic"
    if provider_use.startswith("deerflow.models.openai_codex_provider:"):
        return "openai"
    if provider_use.startswith("langchain_openai:"):
        return "openai-compatible"
    return "openai"


def _resolve_base_url(model) -> str | None:
    for field_name in ("openai_api_base", "anthropic_api_url", "base_url", "api_base"):
        value = getattr(model, field_name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    extra = getattr(model, "model_extra", None)
    if isinstance(extra, dict):
        for field_name in ("openai_api_base", "anthropic_api_url", "base_url", "api_base"):
            value = extra.get(field_name)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _build_config_model_response(model) -> RuntimeModelResponse:
    provider_key = _provider_key_from_use(model.use)
    is_available, availability_reason = resolve_model_availability(model)
    return RuntimeModelResponse(
        name=model.name,
        display_name=getattr(model, "display_name", None),
        description=getattr(model, "description", None),
        provider_key=provider_key,
        provider_label=_provider_label(provider_key),
        model=model.model,
        base_url=_resolve_base_url(model),
        has_api_key=False,
        supports_thinking=getattr(model, "supports_thinking", False),
        supports_reasoning_effort=getattr(model, "supports_reasoning_effort", False),
        supports_vision=getattr(model, "supports_vision", False),
        is_available=is_available,
        availability_reason=availability_reason,
        source="config",
        is_editable=False,
    )


def _build_runtime_model_response(
    definition: RuntimeModelDefinition,
    *,
    has_api_key: bool,
) -> RuntimeModelResponse:
    model = build_runtime_model_config(
        definition,
        api_key=get_runtime_model_secrets().api_keys.get(definition.name),
    )
    is_available, availability_reason = resolve_model_availability(model)
    return RuntimeModelResponse(
        name=definition.name,
        display_name=definition.display_name,
        description=definition.description,
        provider_key=definition.provider_key,
        provider_label=_provider_label(definition.provider_key),
        model=definition.model,
        base_url=definition.base_url,
        has_api_key=has_api_key,
        supports_thinking=definition.supports_thinking,
        supports_reasoning_effort=definition.supports_reasoning_effort,
        supports_vision=definition.supports_vision,
        is_available=is_available,
        availability_reason=availability_reason,
        source="runtime",
        is_editable=True,
    )


def _find_runtime_model_definition(
    registry: RuntimeModelRegistry, name: str
) -> RuntimeModelDefinition | None:
    return next((model for model in registry.models if model.name == name), None)


def _remove_runtime_model_overrides(model_name: str) -> None:
    overrides = get_runtime_config_overrides()
    next_stage_roles = {
        role_id: override
        for role_id, override in overrides.stage_roles.items()
        if not (
            override.model_mode == "explicit" and override.model_name == model_name
        )
    }
    next_default_model = (
        None if overrides.lead_agent.default_model == model_name else overrides.lead_agent.default_model
    )

    if (
        next_default_model == overrides.lead_agent.default_model
        and next_stage_roles == overrides.stage_roles
    ):
        return

    save_runtime_config_overrides(
        RuntimeConfigOverrides(
            lead_agent=RuntimeLeadAgentOverride(default_model=next_default_model),
            stage_roles=next_stage_roles,
        )
    )


def _ensure_runtime_model_name_available(name: str) -> None:
    app_config = get_app_config()
    if any(model.name == name for model in app_config.models):
        raise HTTPException(
            status_code=409,
            detail=f"Model '{name}' already exists in config.yaml.",
        )


@router.get("/runtime-models", response_model=RuntimeModelsListResponse)
async def list_runtime_models() -> RuntimeModelsListResponse:
    config = get_app_config()
    registry = get_runtime_model_registry()
    secrets = get_runtime_model_secrets()

    models = [_build_config_model_response(model) for model in config.models]
    models.extend(
        _build_runtime_model_response(
            definition,
            has_api_key=bool(secrets.api_keys.get(definition.name, "").strip()),
        )
        for definition in registry.models
    )
    return RuntimeModelsListResponse(models=models)


@router.post("/runtime-models", response_model=RuntimeModelResponse)
async def create_runtime_model(
    request: RuntimeModelCreateRequest,
) -> RuntimeModelResponse:
    _ensure_runtime_model_name_available(request.name)
    registry = get_runtime_model_registry()
    secrets = get_runtime_model_secrets()
    if _find_runtime_model_definition(registry, request.name) is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Runtime model '{request.name}' already exists.",
        )

    definition = RuntimeModelDefinition(
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        provider_key=request.provider_key,
        model=request.model,
        base_url=request.base_url,
        supports_thinking=request.supports_thinking,
        supports_reasoning_effort=request.supports_reasoning_effort,
        supports_vision=request.supports_vision,
    )
    registry.models.append(definition)

    normalized_api_key = (request.api_key or "").strip()
    if normalized_api_key:
        secrets.api_keys[request.name] = normalized_api_key

    save_runtime_model_registry(registry)
    save_runtime_model_secrets(secrets)
    return _build_runtime_model_response(
        definition,
        has_api_key=bool(normalized_api_key),
    )


@router.put("/runtime-models/{model_name}", response_model=RuntimeModelResponse)
async def update_runtime_model(
    model_name: str,
    request: RuntimeModelUpdateRequest,
) -> RuntimeModelResponse:
    registry = get_runtime_model_registry()
    secrets = get_runtime_model_secrets()
    definition = _find_runtime_model_definition(registry, model_name)
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail=f"Runtime model '{model_name}' not found.",
        )

    updated_definition = definition.model_copy(
        update={
            "display_name": request.display_name,
            "description": request.description,
            "provider_key": request.provider_key,
            "model": request.model,
            "base_url": request.base_url,
            "supports_thinking": request.supports_thinking,
            "supports_reasoning_effort": request.supports_reasoning_effort,
            "supports_vision": request.supports_vision,
        }
    )

    registry.models = [
        updated_definition if model.name == model_name else model
        for model in registry.models
    ]

    normalized_api_key = (request.api_key or "").strip()
    if request.clear_api_key:
        secrets.api_keys.pop(model_name, None)
    elif normalized_api_key:
        secrets.api_keys[model_name] = normalized_api_key

    save_runtime_model_registry(registry)
    save_runtime_model_secrets(secrets)
    return _build_runtime_model_response(
        updated_definition,
        has_api_key=bool(secrets.api_keys.get(model_name, "").strip()),
    )


@router.delete(
    "/runtime-models/{model_name}",
    response_model=RuntimeModelDeleteResponse,
)
async def delete_runtime_model(model_name: str) -> RuntimeModelDeleteResponse:
    registry = get_runtime_model_registry()
    secrets = get_runtime_model_secrets()
    definition = _find_runtime_model_definition(registry, model_name)
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail=f"Runtime model '{model_name}' not found.",
        )

    registry.models = [model for model in registry.models if model.name != model_name]
    secrets.api_keys.pop(model_name, None)
    save_runtime_model_registry(registry)
    save_runtime_model_secrets(secrets)
    _remove_runtime_model_overrides(model_name)
    return RuntimeModelDeleteResponse(deleted=True, name=model_name)
