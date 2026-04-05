from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    data_dir: Path
    cases_file: Path
    skills_file: Path
    runs_dir: Path
    uploads_dir: Path
    execution_delay_seconds: float
    dispatch_poll_interval_seconds: float
    execution_engine: str
    openfoam_command: str
    executor_base_url: str
    executor_timeout_seconds: float
    agent_provider_name: str
    agent_model_base_url: str
    agent_model_name: str
    agent_model_api_key: str
    agent_model_timeout_seconds: float
    agent_model_temperature: float
    agent_executor_display_name: str


def _first_non_empty(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _infer_agent_base_url() -> str:
    configured = os.getenv("SUBMARINE_AGENT_BASE_URL", "").strip()
    if configured:
        return configured
    if os.getenv("DASHSCOPE_API_KEY", "").strip():
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if os.getenv("DEEPSEEK_API_KEY", "").strip():
        return "https://api.deepseek.com"
    if os.getenv("GLM_API_KEY", "").strip():
        return "https://open.bigmodel.cn/api/paas/v4"
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        return "https://openrouter.ai/api/v1"
    return ""


def _infer_agent_model() -> str:
    configured = os.getenv("SUBMARINE_AGENT_MODEL", "").strip()
    if configured:
        return configured
    if os.getenv("DASHSCOPE_API_KEY", "").strip():
        return "qwen-plus"
    if os.getenv("DEEPSEEK_API_KEY", "").strip():
        return "deepseek-chat"
    if os.getenv("GLM_API_KEY", "").strip():
        return "glm-4.5-air"
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        return "deepseek/deepseek-chat"
    return ""


def get_settings() -> Settings:
    root_dir = Path(
        os.getenv("SUBMARINE_DEMO_ROOT", Path(__file__).resolve().parents[2])
    ).resolve()
    data_dir = root_dir / "data"

    return Settings(
        root_dir=root_dir,
        data_dir=data_dir,
        cases_file=data_dir / "cases" / "index.json",
        skills_file=data_dir / "skills" / "index.json",
        runs_dir=root_dir / "runs",
        uploads_dir=root_dir / "uploads",
        execution_delay_seconds=float(os.getenv("SUBMARINE_EXECUTION_DELAY", "0.05")),
        dispatch_poll_interval_seconds=float(
            os.getenv("SUBMARINE_DISPATCH_POLL_INTERVAL", "0.05")
        ),
        execution_engine=os.getenv("SUBMARINE_EXECUTION_ENGINE", "mock").strip().lower(),
        openfoam_command=os.getenv("SUBMARINE_OPENFOAM_COMMAND", "").strip(),
        executor_base_url=os.getenv("SUBMARINE_EXECUTOR_BASE_URL", "http://127.0.0.1:8020").strip(),
        executor_timeout_seconds=float(os.getenv("SUBMARINE_EXECUTOR_TIMEOUT", "120")),
        agent_provider_name=os.getenv("SUBMARINE_AGENT_PROVIDER", "compatible_api").strip().lower(),
        agent_model_base_url=_infer_agent_base_url(),
        agent_model_name=_infer_agent_model(),
        agent_model_api_key=_first_non_empty(
            "SUBMARINE_AGENT_API_KEY",
            "DASHSCOPE_API_KEY",
            "DEEPSEEK_API_KEY",
            "GLM_API_KEY",
            "OPENROUTER_API_KEY",
        ),
        agent_model_timeout_seconds=float(os.getenv("SUBMARINE_AGENT_TIMEOUT", "90")),
        agent_model_temperature=float(os.getenv("SUBMARINE_AGENT_TEMPERATURE", "0.2")),
        agent_executor_display_name=os.getenv(
            "SUBMARINE_AGENT_EXECUTOR_NAME",
            "Submarine Agent Executor",
        ).strip(),
    )
