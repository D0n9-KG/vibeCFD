"""Detection helpers for minimal official OpenFOAM case-seed uploads."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from deerflow.config.paths import VIRTUAL_PATH_PREFIX


@dataclass(slots=True)
class OfficialCaseSeedResolution:
    status: Literal["resolved", "partial"]
    case_id: str | None
    seed_virtual_paths: list[str]
    user_message: str | None = None


def _to_virtual_upload_path(uploads_dir: Path, actual_path: Path) -> str:
    relative = actual_path.resolve().relative_to(uploads_dir.resolve())
    return f"{VIRTUAL_PATH_PREFIX}/uploads/{relative.as_posix()}"


def _looks_like_openfoam_partial_seed(uploads_dir: Path) -> bool:
    for candidate in uploads_dir.rglob("*"):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(uploads_dir).as_posix()
        if relative.startswith(("0/", "constant/", "system/")):
            return True
    return False


def resolve_official_case_seed(
    *,
    uploads_dir: Path,
) -> OfficialCaseSeedResolution | None:
    if not uploads_dir.exists():
        return None

    cavity_seed_candidates = [
        candidate
        for candidate in uploads_dir.rglob("blockMeshDict")
        if candidate.is_file()
        and (
            candidate.relative_to(uploads_dir).as_posix()
            in {"blockMeshDict", "system/blockMeshDict"}
            or candidate.relative_to(uploads_dir).as_posix().endswith(
                "system/blockMeshDict"
            )
        )
    ]
    if cavity_seed_candidates:
        cavity_seed = sorted(cavity_seed_candidates)[0]
        return OfficialCaseSeedResolution(
            status="resolved",
            case_id="cavity",
            seed_virtual_paths=[_to_virtual_upload_path(uploads_dir, cavity_seed)],
        )

    pitzdaily_candidates = [
        candidate
        for candidate in uploads_dir.rglob("*")
        if candidate.is_file() and candidate.name in {"pitzDaily", "pitzDaily.blockMeshDict"}
    ]
    if pitzdaily_candidates:
        pitzdaily_seed = sorted(pitzdaily_candidates)[0]
        return OfficialCaseSeedResolution(
            status="resolved",
            case_id="pitzDaily",
            seed_virtual_paths=[_to_virtual_upload_path(uploads_dir, pitzdaily_seed)],
        )

    if _looks_like_openfoam_partial_seed(uploads_dir):
        return OfficialCaseSeedResolution(
            status="partial",
            case_id=None,
            seed_virtual_paths=[],
            user_message=(
                "Detected an incomplete OpenFOAM case-seed import. "
                "Upload the required seed file for a supported official case before assembly can continue."
            ),
        )

    return None
