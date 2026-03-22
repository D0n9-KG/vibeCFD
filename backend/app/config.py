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
    )
