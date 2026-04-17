"""Shared contract models for official OpenFOAM case-seed inputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OfficialCaseInputSource = Literal["geometry_seed", "openfoam_case_seed"]


class OfficialCaseProfile(BaseModel):
    """Minimal runtime-visible profile for an imported official OpenFOAM case."""

    case_id: str
    source_commit: str
    source_kind: str | None = None
    source_paths: list[str] = Field(default_factory=list)
    command_chain: list[str] = Field(default_factory=list)
