"""Load source assets from the repository's submarine domain layer."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


def get_repo_root() -> Path:
    """Return the repository root for the current DeerFlow workspace."""
    return Path(__file__).resolve().parents[6]


def get_submarine_domain_root() -> Path:
    """Return the source-of-truth submarine domain asset root."""
    return get_repo_root() / "domain" / "submarine"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_submarine_cases_payload() -> dict:
    """Load the submarine case index from the domain layer."""
    return _load_json(get_submarine_domain_root() / "cases" / "index.json")


@lru_cache(maxsize=1)
def load_submarine_skills_payload() -> dict:
    """Load the submarine skill index from the domain layer."""
    return _load_json(get_submarine_domain_root() / "skills" / "index.json")
