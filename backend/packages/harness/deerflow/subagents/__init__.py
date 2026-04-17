from .config import SubagentConfig
from .registry import get_subagent_config, list_subagents

__all__ = [
    "SubagentConfig",
    "SubagentExecutor",
    "SubagentResult",
    "get_subagent_config",
    "list_subagents",
]


def __getattr__(name: str):
    if name == "SubagentExecutor":
        from .executor import SubagentExecutor

        return SubagentExecutor
    if name == "SubagentResult":
        from .executor import SubagentResult

        return SubagentResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
