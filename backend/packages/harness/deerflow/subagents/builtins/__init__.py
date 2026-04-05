"""Built-in subagent configurations."""

from .bash_agent import BASH_AGENT_CONFIG
from .general_purpose import GENERAL_PURPOSE_CONFIG
from .submarine_experiment_compare import SUBMARINE_EXPERIMENT_COMPARE_CONFIG
from .submarine_geometry_preflight import SUBMARINE_GEOMETRY_PREFLIGHT_CONFIG
from .submarine_result_reporting import SUBMARINE_RESULT_REPORTING_CONFIG
from .submarine_scientific_followup import SUBMARINE_SCIENTIFIC_FOLLOWUP_CONFIG
from .submarine_scientific_study import SUBMARINE_SCIENTIFIC_STUDY_CONFIG
from .submarine_scientific_verification import SUBMARINE_SCIENTIFIC_VERIFICATION_CONFIG
from .submarine_solver_dispatch import SUBMARINE_SOLVER_DISPATCH_CONFIG
from .submarine_task_intelligence import SUBMARINE_TASK_INTELLIGENCE_CONFIG

__all__ = [
    "GENERAL_PURPOSE_CONFIG",
    "BASH_AGENT_CONFIG",
    "SUBMARINE_TASK_INTELLIGENCE_CONFIG",
    "SUBMARINE_GEOMETRY_PREFLIGHT_CONFIG",
    "SUBMARINE_SOLVER_DISPATCH_CONFIG",
    "SUBMARINE_SCIENTIFIC_STUDY_CONFIG",
    "SUBMARINE_EXPERIMENT_COMPARE_CONFIG",
    "SUBMARINE_SCIENTIFIC_VERIFICATION_CONFIG",
    "SUBMARINE_RESULT_REPORTING_CONFIG",
    "SUBMARINE_SCIENTIFIC_FOLLOWUP_CONFIG",
]

# Registry of built-in subagents
BUILTIN_SUBAGENTS = {
    "general-purpose": GENERAL_PURPOSE_CONFIG,
    "bash": BASH_AGENT_CONFIG,
    "submarine-task-intelligence": SUBMARINE_TASK_INTELLIGENCE_CONFIG,
    "submarine-geometry-preflight": SUBMARINE_GEOMETRY_PREFLIGHT_CONFIG,
    "submarine-solver-dispatch": SUBMARINE_SOLVER_DISPATCH_CONFIG,
    "submarine-scientific-study": SUBMARINE_SCIENTIFIC_STUDY_CONFIG,
    "submarine-experiment-compare": SUBMARINE_EXPERIMENT_COMPARE_CONFIG,
    "submarine-scientific-verification": SUBMARINE_SCIENTIFIC_VERIFICATION_CONFIG,
    "submarine-result-reporting": SUBMARINE_RESULT_REPORTING_CONFIG,
    "submarine-scientific-followup": SUBMARINE_SCIENTIFIC_FOLLOWUP_CONFIG,
}
