"""Auto-load credentials from Claude Code CLI and Codex CLI.

Implements two credential strategies:
  1. Claude Code OAuth token from explicit env vars or an exported credentials file
     - Uses Authorization: Bearer header (NOT x-api-key)
     - Requires anthropic-beta: oauth-2025-04-20,claude-code-20250219
     - Supports $CLAUDE_CODE_OAUTH_TOKEN, $CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR, and $ANTHROPIC_AUTH_TOKEN
     - Override path with $CLAUDE_CODE_CREDENTIALS_PATH
     - Falls back to ~/.claude/settings.json env handoff when available
  2. Codex CLI token from ~/.codex/auth.json
     - Uses chatgpt.com/backend-api/codex/responses endpoint
     - Supports both legacy top-level tokens and current nested tokens shape
     - Override path with $CODEX_AUTH_PATH
"""

import json
import logging
import os
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Required beta headers for Claude Code OAuth tokens
OAUTH_ANTHROPIC_BETAS = "oauth-2025-04-20,claude-code-20250219,interleaved-thinking-2025-05-14"


def is_oauth_token(token: str) -> bool:
    """Check if a token is a Claude Code OAuth token (not a standard API key)."""
    return isinstance(token, str) and "sk-ant-oat" in token


@dataclass
class ClaudeCodeCredential:
    """Claude Code CLI OAuth credential."""

    access_token: str
    refresh_token: str = ""
    expires_at: int = 0
    base_url: str = ""
    source: str = ""

    @property
    def is_expired(self) -> bool:
        if self.expires_at <= 0:
            return False
        return time.time() * 1000 > self.expires_at - 60_000  # 1 min buffer


@dataclass
class CodexCliCredential:
    """Codex CLI credential."""

    access_token: str
    account_id: str = ""
    source: str = ""


@dataclass
class OpenAIApiCredential:
    """OpenAI API credential loaded from env or Codex auth handoff."""

    api_key: str
    base_url: str = ""
    source: str = ""


def _resolve_credential_path(env_var: str, default_relative_path: str) -> Path:
    configured_path = os.getenv(env_var)
    if configured_path:
        return Path(configured_path).expanduser()
    return _home_dir() / default_relative_path


def _home_dir() -> Path:
    """Resolve the current user's home directory with explicit HOME support.

    Python's Path.home() ignores HOME on Windows, but our tests and shell-based
    launch flows often set HOME explicitly. Prefer that when available so the
    credential lookup behaves consistently across platforms.
    """
    if home := os.getenv("HOME"):
        return Path(home).expanduser()
    return Path.home()


def _load_json_file(path: Path, label: str) -> dict[str, Any] | None:
    if not path.exists():
        logger.debug(f"{label} not found: {path}")
        return None
    if path.is_dir():
        logger.warning(f"{label} path is a directory, expected a file: {path}")
        return None

    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to read {label}: {e}")
        return None


def _read_secret_from_file_descriptor(env_var: str) -> str | None:
    fd_value = os.getenv(env_var)
    if not fd_value:
        return None

    try:
        fd = int(fd_value)
    except ValueError:
        logger.warning(f"{env_var} must be an integer file descriptor, got: {fd_value}")
        return None

    try:
        with os.fdopen(os.dup(fd), "r", encoding="utf-8") as fh:
            secret = fh.read().strip()
    except OSError as e:
        logger.warning(f"Failed to read {env_var}: {e}")
        return None

    return secret or None


def _credential_from_direct_token(access_token: str, source: str) -> ClaudeCodeCredential | None:
    token = access_token.strip()
    if not token:
        return None
    return ClaudeCodeCredential(access_token=token, source=source)


def _iter_claude_code_credential_paths() -> list[Path]:
    paths: list[Path] = []
    override_path = os.getenv("CLAUDE_CODE_CREDENTIALS_PATH")
    if override_path:
        paths.append(Path(override_path).expanduser())

    default_path = _home_dir() / ".claude/.credentials.json"
    if not paths or paths[-1] != default_path:
        paths.append(default_path)

    return paths


def _load_claude_settings_env_credential() -> ClaudeCodeCredential | None:
    settings_path = _home_dir() / ".claude/settings.json"
    data = _load_json_file(settings_path, "Claude Code settings")
    if data is None:
        return None

    env = data.get("env", {})
    if not isinstance(env, dict):
        logger.debug("Claude Code settings exist but env block is not a JSON object")
        return None

    token = str(env.get("CLAUDE_CODE_OAUTH_TOKEN") or env.get("ANTHROPIC_AUTH_TOKEN") or "").strip()
    if not token:
        logger.debug("Claude Code settings exist but no Claude auth token found in env block")
        return None

    base_url = str(env.get("ANTHROPIC_API_URL") or env.get("ANTHROPIC_BASE_URL") or "").strip()
    return ClaudeCodeCredential(
        access_token=token,
        base_url=base_url,
        source="claude-cli-settings",
    )


def _extract_claude_code_credential(data: dict[str, Any], source: str) -> ClaudeCodeCredential | None:
    oauth = data.get("claudeAiOauth", {})
    access_token = oauth.get("accessToken", "")
    if not access_token:
        logger.debug("Claude Code credentials container exists but no accessToken found")
        return None

    cred = ClaudeCodeCredential(
        access_token=access_token,
        refresh_token=oauth.get("refreshToken", ""),
        expires_at=oauth.get("expiresAt", 0),
        source=source,
    )

    if cred.is_expired:
        logger.warning("Claude Code OAuth token is expired. Run 'claude' to refresh.")
        return None

    return cred


def load_claude_code_credential() -> ClaudeCodeCredential | None:
    """Load OAuth credential from explicit Claude Code handoff sources.

    Lookup order:
      1. $CLAUDE_CODE_OAUTH_TOKEN or $ANTHROPIC_AUTH_TOKEN
      2. $CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR
      3. $CLAUDE_CODE_CREDENTIALS_PATH
      4. ~/.claude/.credentials.json
      5. ~/.claude/settings.json env handoff

    Exported credentials files contain:
    {
      "claudeAiOauth": {
        "accessToken": "sk-ant-oat01-...",
        "refreshToken": "sk-ant-ort01-...",
        "expiresAt": 1773430695128,
        "scopes": ["user:inference", ...],
        ...
      }
    }
    """
    direct_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("ANTHROPIC_AUTH_TOKEN")
    if direct_token:
        cred = _credential_from_direct_token(direct_token, "claude-cli-env")
        if cred:
            logger.info("Loaded Claude Code OAuth credential from environment")
        return cred

    fd_token = _read_secret_from_file_descriptor("CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR")
    if fd_token:
        cred = _credential_from_direct_token(fd_token, "claude-cli-fd")
        if cred:
            logger.info("Loaded Claude Code OAuth credential from file descriptor")
        return cred

    override_path = os.getenv("CLAUDE_CODE_CREDENTIALS_PATH")
    override_path_obj = Path(override_path).expanduser() if override_path else None
    for cred_path in _iter_claude_code_credential_paths():
        data = _load_json_file(cred_path, "Claude Code credentials")
        if data is None:
            continue
        cred = _extract_claude_code_credential(data, "claude-cli-file")
        if cred:
            source_label = "override path" if override_path_obj is not None and cred_path == override_path_obj else "plaintext file"
            logger.info(f"Loaded Claude Code OAuth credential from {source_label} (expires_at={cred.expires_at})")
            return cred

    settings_cred = _load_claude_settings_env_credential()
    if settings_cred:
        logger.info("Loaded Claude Code credential from ~/.claude/settings.json env block")
        return settings_cred

    return None


def load_codex_cli_credential() -> CodexCliCredential | None:
    """Load credential from Codex CLI (~/.codex/auth.json)."""
    cred_path = _resolve_credential_path("CODEX_AUTH_PATH", ".codex/auth.json")
    data = _load_json_file(cred_path, "Codex CLI credentials")
    if data is None:
        return None
    tokens = data.get("tokens", {})
    if not isinstance(tokens, dict):
        tokens = {}

    access_token = data.get("access_token") or data.get("token") or tokens.get("access_token", "")
    account_id = data.get("account_id") or tokens.get("account_id", "")
    if not access_token:
        logger.debug("Codex CLI credentials file exists but no token found")
        return None

    logger.info("Loaded Codex CLI credential")
    return CodexCliCredential(
        access_token=access_token,
        account_id=account_id,
        source="codex-cli",
    )


def load_openai_api_credential() -> OpenAIApiCredential | None:
    """Load OpenAI API key from env or the local Codex auth handoff file."""
    direct_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
    direct_base_url = str(os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "").strip()
    if direct_key:
        logger.info("Loaded OpenAI API credential from environment")
        return OpenAIApiCredential(
            api_key=direct_key,
            base_url=direct_base_url,
            source="openai-api-env",
        )

    cred_path = _resolve_credential_path("CODEX_AUTH_PATH", ".codex/auth.json")
    data = _load_json_file(cred_path, "Codex CLI credentials")
    if data is None:
        return None

    api_key = str(
        data.get("OPENAI_API_KEY")
        or data.get("openai_api_key")
        or "",
    ).strip()
    if not api_key:
        logger.debug("Codex auth file exists but no OpenAI API key was found")
        return None

    logger.info("Loaded OpenAI API credential from Codex auth file")
    return OpenAIApiCredential(
        api_key=api_key,
        base_url=_load_codex_openai_base_url(),
        source="codex-auth-file",
    )


def _load_codex_openai_base_url() -> str:
    config_path = _resolve_credential_path("CODEX_CONFIG_PATH", ".codex/config.toml")
    if not config_path.exists() or config_path.is_dir():
        return ""

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as e:
        logger.warning(f"Failed to read Codex config: {e}")
        return ""

    model_providers = data.get("model_providers", {})
    if not isinstance(model_providers, dict):
        return ""

    provider_name = data.get("model_provider")
    provider_config: dict[str, Any] | None = None
    if isinstance(provider_name, str):
        maybe_provider = model_providers.get(provider_name)
        if isinstance(maybe_provider, dict):
            provider_config = maybe_provider

    if provider_config is None:
        for candidate in model_providers.values():
            if isinstance(candidate, dict) and candidate.get("requires_openai_auth"):
                provider_config = candidate
                break

    if provider_config is None:
        return ""

    return str(provider_config.get("base_url") or "").strip()
