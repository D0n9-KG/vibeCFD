"""Built-in subagent configurations."""

from .bash_agent import BASH_AGENT_CONFIG
from .general_purpose import GENERAL_PURPOSE_CONFIG
from .submarine_geometry_preflight import SUBMARINE_GEOMETRY_PREFLIGHT_CONFIG
from .submarine_result_reporting import SUBMARINE_RESULT_REPORTING_CONFIG
from .submarine_solver_dispatch import SUBMARINE_SOLVER_DISPATCH_CONFIG
from .submarine_task_intelligence import SUBMARINE_TASK_INTELLIGENCE_CONFIG

__all__ = [
    "GENERAL_PURPOSE_CONFIG",
    "BASH_AGENT_CONFIG",
    "SUBMARINE_TASK_INTELLIGENCE_CONFIG",
    "SUBMARINE_GEOMETRY_PREFLIGHT_CONFIG",
    "SUBMARINE_SOLVER_DISPATCH_CONFIG",
    "SUBMARINE_RESULT_REPORTING_CONFIG",
]

# Registry of built-in subagents
BUILTIN_SUBAGENTS = {
    "general-purpose": GENERAL_PURPOSE_CONFIG,
    "bash": BASH_AGENT_CONFIG,
    "submarine-task-intelligence": SUBMARINE_TASK_INTELLIGENCE_CONFIG,
    "submarine-geometry-preflight": SUBMARINE_GEOMETRY_PREFLIGHT_CONFIG,
    "submarine-solver-dispatch": SUBMARINE_SOLVER_DISPATCH_CONFIG,
    "submarine-result-reporting": SUBMARINE_RESULT_REPORTING_CONFIG,
}
