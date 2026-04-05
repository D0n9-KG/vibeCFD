"""Submarine CFD domain runtime for DeerFlow."""

from .assets import get_submarine_domain_root
from .contracts import (
    SubmarineRuntimeRequest,
    SubmarineRuntimeSnapshot,
    SupervisorReviewContract,
    build_runtime_snapshot,
    build_supervisor_review_contract,
)
from .geometry_check import inspect_geometry_file, run_geometry_check
from .library import load_case_library, load_skill_registry, rank_cases
from .reporting import run_result_report

__all__ = [
    "get_submarine_domain_root",
    "inspect_geometry_file",
    "load_case_library",
    "load_skill_registry",
    "rank_cases",
    "run_result_report",
    "run_geometry_check",
    "SubmarineRuntimeRequest",
    "SubmarineRuntimeSnapshot",
    "SupervisorReviewContract",
    "build_runtime_snapshot",
    "build_supervisor_review_contract",
]
