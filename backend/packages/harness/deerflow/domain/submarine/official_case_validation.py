"""Parity checks for pinned official OpenFOAM tutorial cases."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .official_case_profiles import PINNED_OPENFOAM_13_COMMIT


def _stringify_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _coerce_number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


_OFFICIAL_CASE_VALIDATION_BASELINES: dict[str, dict[str, Any]] = {
    "cavity": {
        "required_files": {
            "system/controlDict": (
                "application     icoFoam;",
                "endTime         0.5;",
                "deltaT          0.005;",
            ),
            "system/fvSolution": (
                "pFinal",
                "PISO",
            ),
        },
        "expected_metrics": {
            "final_time_seconds": 0.5,
            "mesh_cells": 400,
        },
    },
    "pitzDaily": {
        "required_files": {
            "system/controlDict": (
                "solver          incompressibleFluid;",
                "endTime         2000;",
                "deltaT          1;",
                "writeInterval   100;",
                "cacheTemporaryObjects",
            ),
            "constant/momentumTransport": (
                "simulationType",
                "RAS;",
                "model           kEpsilon;",
            ),
            "system/fvSchemes": (
                "default         steadyState;",
                "div(phi,epsilon) bounded Gauss limitedLinear 1;",
            ),
            "system/fvSolution": (
                "SIMPLE",
                "residualControl",
            ),
            "system/functions": (
                "#includeFunc streamlinesLine",
                "#includeFunc writeObjects(kEpsilon:G)",
            ),
            "0/k": (
                "internalField   uniform 0.375;",
                "type kqRWallFunction;",
            ),
            "0/epsilon": (
                "internalField   uniform 14.855;",
                "type epsilonWallFunction;",
            ),
        },
        "expected_metrics": {
            "final_time_seconds": 285.0,
            "mesh_cells": 12225,
        },
    },
}


def _load_assembled_case_files(
    *,
    assembled_case_dir: Path | None,
    assembled_case_files: Mapping[str, str] | None,
    required_paths: tuple[str, ...],
) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if isinstance(assembled_case_files, Mapping):
        for path, text in assembled_case_files.items():
            normalized = str(path).replace("\\", "/")
            string_value = _stringify_text(text)
            if string_value is not None:
                loaded[normalized] = string_value

    if assembled_case_dir is None:
        return loaded

    for relative_path in required_paths:
        if relative_path in loaded:
            continue
        candidate = assembled_case_dir / Path(relative_path)
        if candidate.exists() and candidate.is_file():
            loaded[relative_path] = candidate.read_text(encoding="utf-8")

    return loaded


def build_official_case_validation_assessment(
    *,
    case_id: str,
    solver_results: Mapping[str, Any] | None,
    assembled_case_dir: Path | None = None,
    assembled_case_files: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    try:
        baseline = _OFFICIAL_CASE_VALIDATION_BASELINES[case_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported official case id: {case_id}") from exc

    required_files = baseline["required_files"]
    expected_metrics = baseline["expected_metrics"]
    assembled_files = _load_assembled_case_files(
        assembled_case_dir=assembled_case_dir,
        assembled_case_files=assembled_case_files,
        required_paths=tuple(required_files.keys()),
    )

    passed_checks: list[str] = []
    drift_reasons: list[str] = []

    for relative_path, required_snippets in required_files.items():
        text = assembled_files.get(relative_path)
        if text is None:
            drift_reasons.append(
                f"Assembled file `{relative_path}` is missing from the official-case workspace."
            )
            continue

        missing_snippets = [
            snippet for snippet in required_snippets if snippet not in text
        ]
        if missing_snippets:
            drift_reasons.append(
                f"Assembled file `{relative_path}` drifted from the pinned official defaults."
            )
            continue

        passed_checks.append(f"Assembly matched `{relative_path}`.")

    solver_results = solver_results or {}
    solver_completed = bool(solver_results.get("solver_completed"))
    observed_final_time = _coerce_number(solver_results.get("final_time_seconds"))
    observed_mesh_cells = _coerce_number(
        (solver_results.get("mesh_summary") or {}).get("cells")
    )

    if not solver_completed:
        if solver_results:
            drift_reasons.append(
                "The official-case solver run did not complete, so parity cannot be claimed."
            )
        parity_status = "pending_execution"
    else:
        expected_final_time = _coerce_number(expected_metrics.get("final_time_seconds"))
        expected_mesh_cells = _coerce_number(expected_metrics.get("mesh_cells"))

        if observed_final_time != expected_final_time:
            drift_reasons.append(
                "Observed final time drifted from the pinned official baseline."
            )
        else:
            passed_checks.append(
                f"Solver final time matched the pinned baseline (`{expected_final_time:g}`)."
            )

        if observed_mesh_cells != expected_mesh_cells:
            drift_reasons.append(
                "Observed mesh cell count drifted from the pinned official baseline."
            )
        else:
            passed_checks.append(
                f"Mesh cell count matched the pinned baseline (`{int(expected_mesh_cells)}`)."
            )

        parity_status = "matched" if not drift_reasons else "drifted"

    return {
        "case_id": case_id,
        "source_commit": PINNED_OPENFOAM_13_COMMIT,
        "parity_status": parity_status,
        "expected_metrics": expected_metrics,
        "observed_metrics": {
            "solver_completed": solver_completed,
            "final_time_seconds": observed_final_time,
            "mesh_cells": int(observed_mesh_cells)
            if observed_mesh_cells is not None
            else None,
        },
        "checked_file_count": len(required_files),
        "passed_checks": passed_checks,
        "drift_reasons": drift_reasons,
    }
