"""Configuration and loaders for custom agents."""

import logging
import re
from typing import Any

import yaml
from pydantic import BaseModel

from deerflow.config.paths import get_paths

logger = logging.getLogger(__name__)

SOUL_FILENAME = "SOUL.md"
AGENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")


class AgentConfig(BaseModel):
    """Configuration for a custom agent."""

    name: str
    description: str = ""
    display_name: str | None = None
    model: str | None = None
    tool_groups: list[str] | None = None


BUILTIN_AGENT_CONFIGS: dict[str, dict[str, Any]] = {
    "codex-skill-creator": {
        "name": "codex-skill-creator",
        "description": "Dedicated Codex agent for Skill Studio authoring, validation, testing, and publishing workflows.",
        "display_name": "Codex · Skill Creator",
        "model": "gpt-5.4",
        "tool_groups": ["workspace", "skills"],
    },
    "claude-code-skill-creator": {
        "name": "claude-code-skill-creator",
        "description": "Dedicated Claude Code agent for Skill Studio authoring, validation, testing, and publishing workflows.",
        "display_name": "Claude Code · Skill Creator",
        "model": "claude-sonnet-4-6",
        "tool_groups": ["workspace", "skills"],
    },
}

BUILTIN_AGENT_SOULS: dict[str, str] = {
    "codex-skill-creator": "\n".join(
        [
            "You are Codex · Skill Creator, the dedicated agent for DeerFlow Skill Studio.",
            "",
            "Your job is to help domain experts turn raw rules, heuristics, workflows, and acceptance criteria into publishable DeerFlow/Codex skills.",
            "",
            "Operating rules:",
            "- Stay focused on skill authoring, validation, scenario testing, and publish readiness.",
            "- Treat the human as a domain expert collaborator. Ask for the missing domain judgment when a rule, threshold, or exception is unclear.",
            "- Always shape the work so it aligns with the skill-creator and writing-skills disciplines:",
            "  - concise trigger descriptions",
            "  - explicit workflow steps",
            "  - realistic validation scenarios",
            "  - reviewable artifacts",
            "- Prefer structured outputs over vague summaries. Surface what changed, what still blocks publishing, and what should be tested next.",
            "- Do not drift into general CFD execution unless it is directly necessary to author or validate a skill.",
        ],
    ),
    "claude-code-skill-creator": "\n".join(
        [
            "You are Claude Code · Skill Creator, the dedicated agent for DeerFlow Skill Studio.",
            "",
            "Your job is to help domain experts turn raw rules, heuristics, workflows, and acceptance criteria into publishable DeerFlow/Codex skills.",
            "",
            "Operating rules:",
            "- Stay focused on skill authoring, validation, scenario testing, and publish readiness.",
            "- Treat the human as a domain expert collaborator. Ask for the missing domain judgment when a rule, threshold, or exception is unclear.",
            "- Always shape the work so it aligns with the skill-creator and writing-skills disciplines:",
            "  - concise trigger descriptions",
            "  - explicit workflow steps",
            "  - realistic validation scenarios",
            "  - reviewable artifacts",
            "- Prefer structured outputs over vague summaries. Surface what changed, what still blocks publishing, and what should be tested next.",
            "- Do not drift into general CFD execution unless it is directly necessary to author or validate a skill.",
        ],
    ),
}


def _load_builtin_agent_config(name: str) -> AgentConfig | None:
    data = BUILTIN_AGENT_CONFIGS.get(name)
    if data is None:
        return None
    return AgentConfig(**data)


def load_agent_config(name: str | None) -> AgentConfig | None:
    """Load the custom or default agent's config from its directory.

    Args:
        name: The agent name.

    Returns:
        AgentConfig instance.

    Raises:
        FileNotFoundError: If the agent directory or config.yaml does not exist.
        ValueError: If config.yaml cannot be parsed.
    """

    if name is None:
        return None

    if not AGENT_NAME_PATTERN.match(name):
        raise ValueError(f"Invalid agent name '{name}'. Must match pattern: {AGENT_NAME_PATTERN.pattern}")

    builtin_config = _load_builtin_agent_config(name)
    if builtin_config is not None:
        return builtin_config

    agent_dir = get_paths().agent_dir(name)
    config_file = agent_dir / "config.yaml"

    if not agent_dir.exists():
        raise FileNotFoundError(f"Agent directory not found: {agent_dir}")

    if not config_file.exists():
        raise FileNotFoundError(f"Agent config not found: {config_file}")

    try:
        with open(config_file, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse agent config {config_file}: {e}") from e

    # Ensure name is set from directory name if not in file
    if "name" not in data:
        data["name"] = name

    # Strip unknown fields before passing to Pydantic (e.g. legacy prompt_file)
    known_fields = set(AgentConfig.model_fields.keys())
    data = {k: v for k, v in data.items() if k in known_fields}

    return AgentConfig(**data)


def load_agent_soul(agent_name: str | None) -> str | None:
    """Read the SOUL.md file for a custom agent, if it exists.

    SOUL.md defines the agent's personality, values, and behavioral guardrails.
    It is injected into the lead agent's system prompt as additional context.

    Args:
        agent_name: The name of the agent or None for the default agent.

    Returns:
        The SOUL.md content as a string, or None if the file does not exist.
    """
    if agent_name in BUILTIN_AGENT_SOULS:
        return BUILTIN_AGENT_SOULS[agent_name]

    agent_dir = get_paths().agent_dir(agent_name) if agent_name else get_paths().base_dir
    soul_path = agent_dir / SOUL_FILENAME
    if not soul_path.exists():
        return None
    content = soul_path.read_text(encoding="utf-8").strip()
    return content or None


def list_custom_agents() -> list[AgentConfig]:
    """Scan the agents directory and return all valid custom agents.

    Returns:
        List of AgentConfig for each valid agent directory found.
    """
    agents_dir = get_paths().agents_dir

    if not agents_dir.exists():
        return []

    agents: list[AgentConfig] = []

    for entry in sorted(agents_dir.iterdir()):
        if not entry.is_dir():
            continue

        config_file = entry / "config.yaml"
        if not config_file.exists():
            logger.debug(f"Skipping {entry.name}: no config.yaml")
            continue

        try:
            agent_cfg = load_agent_config(entry.name)
            agents.append(agent_cfg)
        except Exception as e:
            logger.warning(f"Skipping agent '{entry.name}': {e}")

    return agents
