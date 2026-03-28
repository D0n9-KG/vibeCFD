"""Normalize and rank submarine domain assets for DeerFlow runtime use."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .assets import load_submarine_cases_payload, load_submarine_skills_payload
from .models import (
    SubmarineCase,
    SubmarineCaseLibrary,
    SubmarineCaseMatch,
    SubmarineSkillDefinition,
    SubmarineSkillRegistry,
)

TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def _family_matches(hint: str | None, family: str) -> bool:
    if not hint:
        return False
    normalized_hint = hint.strip().lower()
    normalized_family = family.strip().lower()
    return (
        normalized_hint == normalized_family
        or normalized_hint in normalized_family
        or normalized_family in normalized_hint
    )


def _suffix_matches(geometry_file_name: str | None, input_requirements: list[str]) -> bool:
    if not geometry_file_name:
        return False
    suffix = Path(geometry_file_name).suffix.lower().lstrip(".")
    if not suffix:
        return False
    normalized_requirements = " ".join(item.lower() for item in input_requirements)
    return suffix in normalized_requirements or suffix.replace("_", "") in normalized_requirements.replace(" ", "")


@lru_cache(maxsize=1)
def load_case_library() -> SubmarineCaseLibrary:
    """Load and normalize the submarine case library from source JSON."""
    cases = [
      SubmarineCase.model_validate(raw_case)
      for raw_case in load_submarine_cases_payload().get("cases", [])
    ]
    case_index = {case.case_id: case for case in cases}
    families = sorted({case.geometry_family for case in cases})
    task_types = sorted({case.task_type for case in cases})
    return SubmarineCaseLibrary(
      cases=cases,
      case_index=case_index,
      geometry_families=families,
      task_types=task_types,
    )


@lru_cache(maxsize=1)
def load_skill_registry() -> SubmarineSkillRegistry:
    """Load and normalize the submarine skill registry from source JSON."""
    skills = [
      SubmarineSkillDefinition.model_validate(raw_skill)
      for raw_skill in load_submarine_skills_payload().get("skills", [])
    ]
    return SubmarineSkillRegistry(
      skills=skills,
      skill_index={skill.skill_id: skill for skill in skills},
    )


def rank_cases(
    *,
    task_description: str,
    task_type: str,
    geometry_family_hint: str | None = None,
    geometry_file_name: str | None = None,
    limit: int = 3,
) -> list[SubmarineCaseMatch]:
    """Rank submarine benchmark or engineering cases for a task."""
    library = load_case_library()
    description_tokens = _tokenize(
        " ".join(
            part
            for part in [task_description, task_type, geometry_family_hint or "", geometry_file_name or ""]
            if part
        )
    )
    ranked: list[SubmarineCaseMatch] = []

    for case in library.cases:
        score = 0.0
        reasons: list[str] = []
        case_tokens = _tokenize(
            " ".join(
                [
                    case.title,
                    case.geometry_description,
                    case.task_type,
                    " ".join(case.condition_tags),
                    " ".join(case.expected_outputs),
                    case.reuse_role or "",
                ]
            )
        )

        if task_type == case.task_type:
            score += 4.0
            reasons.append("任务类型完全匹配")

        if _family_matches(geometry_family_hint, case.geometry_family):
            score += 3.0
            reasons.append("几何家族高度接近")

        overlap = description_tokens & case_tokens
        if overlap:
            overlap_score = min(len(overlap) * 0.35, 2.5)
            score += overlap_score
            reasons.append(f"任务描述关键词重合 {len(overlap)} 项")

        if _suffix_matches(geometry_file_name, case.input_requirements):
            score += 0.5
            reasons.append("输入格式可复用现有模板")

        if not reasons:
            reasons.append("可作为潜艇领域兜底参考案例")

        ranked.append(
            SubmarineCaseMatch(
                case_id=case.case_id,
                title=case.title,
                geometry_family=case.geometry_family,
                task_type=case.task_type,
                score=round(score, 3),
                rationale="；".join(reasons),
                recommended_solver=case.recommended_solver,
                expected_outputs=case.expected_outputs,
                linked_skills=case.linked_skills,
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]
