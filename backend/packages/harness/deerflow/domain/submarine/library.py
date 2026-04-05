"""Normalize and rank submarine domain assets for DeerFlow runtime use."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .assets import load_submarine_cases_payload, load_submarine_skills_payload
from .models import (
    ReferenceSource,
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


def _pick_primary_reference(case: SubmarineCase) -> ReferenceSource | None:
    if not case.reference_sources:
        return None
    for source in case.reference_sources:
        if not source.is_placeholder:
            return source
    return case.reference_sources[0]


def _collect_applicability_conditions(case: SubmarineCase) -> list[str]:
    values = [*case.condition_tags]
    primary = _pick_primary_reference(case)
    if primary is not None:
        values.extend(primary.applicability_conditions)

    deduped: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped


def _build_confidence_note(case: SubmarineCase) -> str:
    if case.evidence_tier == "benchmark_validated":
        return "Case is benchmark-backed and suitable as a stronger scientific anchor."
    if case.evidence_tier == "advisory_placeholder":
        return "Case is advisory only until stronger provenance is curated."
    primary = _pick_primary_reference(case)
    if primary is not None and primary.confidence_note:
        return primary.confidence_note
    if case.acceptance_profile and case.acceptance_profile.benchmark_targets:
        return "Case includes an explicit benchmark-backed acceptance target."
    if primary is not None and primary.is_placeholder:
        return "Case is advisory only until stronger provenance is curated."
    return "Case is matched by task and geometry metadata."


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
        primary_reference = _pick_primary_reference(case)
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
            reasons.append("Task type matches exactly")

        if _family_matches(geometry_family_hint, case.geometry_family):
            score += 3.0
            reasons.append("Geometry family is closely aligned")

        overlap = description_tokens & case_tokens
        if overlap:
            overlap_score = min(len(overlap) * 0.35, 2.5)
            score += overlap_score
            reasons.append(f"Description overlaps with {len(overlap)} case tokens")

        if _suffix_matches(geometry_file_name, case.input_requirements):
            score += 0.5
            reasons.append("Input format can reuse the existing workflow")

        if case.acceptance_profile and case.acceptance_profile.benchmark_targets:
            score += 0.8
            reasons.append("Benchmark-backed acceptance targets are available")
        elif case.acceptance_profile is not None:
            score += 0.2
            reasons.append("Acceptance profile is defined for this workflow")

        if case.evidence_tier == "benchmark_validated":
            score += 1.0
            reasons.append("Evidence tier is benchmark validated")
        elif case.evidence_tier == "advisory_placeholder":
            score -= 1.25
            reasons.append("Evidence tier is advisory placeholder only")

        if primary_reference is not None:
            if primary_reference.is_placeholder:
                score -= 0.75
                reasons.append("Reference provenance is placeholder-backed and disclosed")
            else:
                score += 0.6
                reasons.append("Reference provenance includes a concrete cited source")

        if not reasons:
            reasons.append("Can serve as a domain fallback template")

        ranked.append(
            SubmarineCaseMatch(
                case_id=case.case_id,
                title=case.title,
                evidence_tier=case.evidence_tier,
                geometry_family=case.geometry_family,
                task_type=case.task_type,
                score=round(score, 3),
                rationale="; ".join(reasons),
                recommended_solver=case.recommended_solver,
                expected_outputs=case.expected_outputs,
                linked_skills=case.linked_skills,
                reference_sources=case.reference_sources,
                source_label=(
                    primary_reference.source_label or primary_reference.title
                    if primary_reference
                    else None
                ),
                source_url=primary_reference.url if primary_reference else None,
                source_type=primary_reference.source_type if primary_reference else None,
                applicability_conditions=_collect_applicability_conditions(case),
                confidence_note=_build_confidence_note(case),
                is_placeholder=primary_reference.is_placeholder if primary_reference else False,
                evidence_gap_note=(
                    primary_reference.evidence_gap_note if primary_reference else None
                ),
                acceptance_profile_summary_zh=(
                    case.acceptance_profile.summary_zh
                    if case.acceptance_profile is not None
                    else None
                ),
                benchmark_metric_ids=(
                    [
                        target.metric_id
                        for target in case.acceptance_profile.benchmark_targets
                    ]
                    if case.acceptance_profile is not None
                    else []
                ),
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]
