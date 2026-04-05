from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path

from .loader import load_skills

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "new",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "use",
    "used",
    "using",
    "when",
    "with",
    "your",
}

STAGE_KEYWORDS = {
    "creator": {"creator", "create", "draft", "publish", "validation", "studio", "writing"},
    "task": {"task", "intelligence", "case", "workflow", "plan", "planning"},
    "geometry": {"geometry", "stl", "mesh", "meshing", "preflight", "check", "checking"},
    "solver": {"solver", "dispatch", "openfoam", "run", "execution", "execute"},
    "report": {"report", "reporting", "summary", "acceptance", "review", "delivery"},
}

STAGE_TOKENS = {token for tokens in STAGE_KEYWORDS.values() for token in tokens}

SUBAGENT_STAGE_TARGETS: dict[str, set[str] | None] = {
    "general-purpose": None,
    "bash": set(),
    "submarine-task-intelligence": {"task"},
    "submarine-geometry-preflight": {"geometry"},
    "submarine-solver-dispatch": {"geometry", "solver"},
    "submarine-scientific-study": {"solver"},
    "submarine-experiment-compare": {"solver", "report"},
    "submarine-scientific-verification": {"report"},
    "submarine-result-reporting": {"report"},
    "submarine-scientific-followup": {"solver", "report"},
}


@dataclass
class SkillGraphNode:
    name: str
    description: str
    category: str
    enabled: bool
    related_count: int
    stage: str | None
    revision_count: int = 0
    active_revision_id: str | None = None
    rollback_target_id: str | None = None
    binding_count: int = 0
    last_published_at: str | None = None


@dataclass
class SkillRelationshipEdge:
    source: str
    target: str
    relationship_type: str
    score: float
    reason: str


@dataclass
class SkillGraphSummary:
    skill_count: int
    enabled_skill_count: int
    public_skill_count: int
    custom_skill_count: int
    edge_count: int
    relationship_counts: dict[str, int]


@dataclass
class SkillFocusItem:
    skill_name: str
    category: str
    enabled: bool
    description: str
    relationship_types: list[str]
    strongest_score: float
    reasons: list[str]
    revision_count: int = 0
    active_revision_id: str | None = None
    rollback_target_id: str | None = None
    binding_count: int = 0
    last_published_at: str | None = None


@dataclass
class SkillGraphFocus:
    skill_name: str
    related_skill_count: int
    related_skills: list[SkillFocusItem]


@dataclass
class SkillGraph:
    summary: SkillGraphSummary
    skills: list[SkillGraphNode]
    relationships: list[SkillRelationshipEdge]
    focus: SkillGraphFocus | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize_token(token: str) -> str:
    token = token.lower().strip()
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("s"):
        return token[:-1]
    return token


def _tokenize(*parts: str) -> set[str]:
    tokens: set[str] = set()
    for part in parts:
        for raw in re.split(r"[^a-zA-Z0-9]+", part.lower()):
            if not raw:
                continue
            token = _normalize_token(raw)
            if len(token) < 3 or token in STOPWORDS:
                continue
            tokens.add(token)
    return tokens


def _shared_domain_tokens(tokens_a: set[str], tokens_b: set[str]) -> set[str]:
    return {
        token
        for token in (tokens_a & tokens_b)
        if token not in STAGE_TOKENS
    }


def _infer_stage(tokens: set[str]) -> str | None:
    stage_scores = {
        stage: len(tokens & keywords)
        for stage, keywords in STAGE_KEYWORDS.items()
    }
    stage, score = max(stage_scores.items(), key=lambda item: item[1])
    return stage if score > 0 else None


def _contains_skill_reference(content: str, other_skill_name: str) -> bool:
    lower_content = content.lower()
    return (
        other_skill_name.lower() in lower_content
        or other_skill_name.lower().replace("-", " ") in lower_content
    )


def _build_skill_governance_metadata(
    skill,
    lifecycle_registry,
) -> dict[str, str | int | None]:
    from deerflow.domain.submarine.skill_lifecycle import (
        get_skill_lifecycle_binding_count,
        get_skill_lifecycle_revision_count,
        load_skill_lifecycle_record,
        merge_skill_lifecycle_record,
    )

    if skill.category != "custom":
        return {
            "revision_count": 0,
            "active_revision_id": None,
            "rollback_target_id": None,
            "binding_count": 0,
            "last_published_at": None,
        }

    record = merge_skill_lifecycle_record(
        skill_name=skill.name,
        lifecycle_payload=load_skill_lifecycle_record(
            skill.skill_dir / "skill-lifecycle.json",
        ),
        existing_record=lifecycle_registry.records.get(skill.name),
        enabled=skill.enabled,
        published_path=str(skill.skill_dir),
    )
    return {
        "revision_count": get_skill_lifecycle_revision_count(record),
        "active_revision_id": record.active_revision_id,
        "rollback_target_id": record.rollback_target_id,
        "binding_count": get_skill_lifecycle_binding_count(record),
        "last_published_at": record.last_published_at,
    }


def analyze_skill_relationships(
    *,
    skills_path: Path | None = None,
    focus_skill_name: str | None = None,
) -> SkillGraph:
    from deerflow.domain.submarine.skill_lifecycle import (
        load_skill_lifecycle_registry,
    )

    loaded_skills = load_skills(
        skills_path=skills_path,
        use_config=False,
        enabled_only=False,
    )
    loaded_skills.sort(key=lambda skill: skill.name)
    lifecycle_registry = load_skill_lifecycle_registry(skills_root=skills_path)

    token_map = {
        skill.name: _tokenize(skill.name, skill.description)
        for skill in loaded_skills
    }
    content_map = {
        skill.name: skill.skill_file.read_text(encoding="utf-8")
        for skill in loaded_skills
    }
    stage_map = {
        skill.name: _infer_stage(token_map[skill.name])
        for skill in loaded_skills
    }
    governance_map = {
        skill.name: _build_skill_governance_metadata(skill, lifecycle_registry)
        for skill in loaded_skills
    }

    relationships: list[SkillRelationshipEdge] = []
    related_counts: Counter[str] = Counter()

    for source, target in combinations(loaded_skills, 2):
        source_tokens = token_map[source.name]
        target_tokens = token_map[target.name]
        overlap = source_tokens & target_tokens
        shared_domain = _shared_domain_tokens(source_tokens, target_tokens)
        min_size = max(1, min(len(source_tokens), len(target_tokens)))
        overlap_score = len(overlap) / min_size

        if len(overlap) >= 2 and overlap_score >= 0.28:
            reason = (
                "Shared task language: "
                + ", ".join(sorted(overlap)[:5])
            )
            relationships.append(
                SkillRelationshipEdge(
                    source=source.name,
                    target=target.name,
                    relationship_type="similar_to",
                    score=round(overlap_score, 3),
                    reason=reason,
                )
            )
            related_counts[source.name] += 1
            related_counts[target.name] += 1

        source_stage = stage_map[source.name]
        target_stage = stage_map[target.name]
        if (
            source_stage
            and target_stage
            and source_stage != target_stage
            and len(shared_domain) >= 1
        ):
            reason = (
                f"Shared domain ({', '.join(sorted(shared_domain)[:4])}) with complementary stages "
                f"{source_stage} → {target_stage}"
            )
            relationships.append(
                SkillRelationshipEdge(
                    source=source.name,
                    target=target.name,
                    relationship_type="compose_with",
                    score=round(max(len(shared_domain) / 4, 0.25), 3),
                    reason=reason,
                )
            )
            related_counts[source.name] += 1
            related_counts[target.name] += 1

    for source in loaded_skills:
        source_content = content_map[source.name]
        for target in loaded_skills:
            if source.name == target.name:
                continue
            if _contains_skill_reference(source_content, target.name):
                relationships.append(
                    SkillRelationshipEdge(
                        source=source.name,
                        target=target.name,
                        relationship_type="depend_on",
                        score=1.0,
                        reason=f"Skill package explicitly references {target.name}.",
                    )
                )
                related_counts[source.name] += 1
                related_counts[target.name] += 1

    deduped: dict[tuple[str, str, str], SkillRelationshipEdge] = {}
    for edge in relationships:
        key = (edge.source, edge.target, edge.relationship_type)
        existing = deduped.get(key)
        if existing is None or edge.score > existing.score:
            deduped[key] = edge

    relationships = sorted(
        deduped.values(),
        key=lambda edge: (-edge.score, edge.relationship_type, edge.source, edge.target),
    )

    relationship_counts = Counter(edge.relationship_type for edge in relationships)

    nodes = [
        SkillGraphNode(
            name=skill.name,
            description=skill.description,
            category=skill.category,
            enabled=skill.enabled,
            related_count=related_counts[skill.name],
            stage=stage_map[skill.name],
            revision_count=governance_map[skill.name]["revision_count"],
            active_revision_id=governance_map[skill.name]["active_revision_id"],
            rollback_target_id=governance_map[skill.name]["rollback_target_id"],
            binding_count=governance_map[skill.name]["binding_count"],
            last_published_at=governance_map[skill.name]["last_published_at"],
        )
        for skill in loaded_skills
    ]

    focus: SkillGraphFocus | None = None
    if focus_skill_name:
        focus_skill = next(
            (skill for skill in loaded_skills if skill.name == focus_skill_name),
            None,
        )
        if focus_skill is not None:
            related_items: dict[str, SkillFocusItem] = {}
            skill_lookup = {skill.name: skill for skill in loaded_skills}
            for edge in relationships:
                if focus_skill_name not in {edge.source, edge.target}:
                    continue
                related_name = edge.target if edge.source == focus_skill_name else edge.source
                related_skill = skill_lookup[related_name]
                current = related_items.get(related_name)
                if current is None:
                    current = SkillFocusItem(
                        skill_name=related_name,
                        category=related_skill.category,
                        enabled=related_skill.enabled,
                        description=related_skill.description,
                        relationship_types=[],
                        strongest_score=edge.score,
                        reasons=[],
                        revision_count=governance_map[related_name]["revision_count"],
                        active_revision_id=governance_map[related_name]["active_revision_id"],
                        rollback_target_id=governance_map[related_name]["rollback_target_id"],
                        binding_count=governance_map[related_name]["binding_count"],
                        last_published_at=governance_map[related_name]["last_published_at"],
                    )
                    related_items[related_name] = current
                current.relationship_types.append(edge.relationship_type)
                current.strongest_score = max(current.strongest_score, edge.score)
                current.reasons.append(edge.reason)

            focus = SkillGraphFocus(
                skill_name=focus_skill_name,
                related_skill_count=len(related_items),
                related_skills=sorted(
                    related_items.values(),
                    key=lambda item: (-item.strongest_score, item.skill_name),
                ),
            )

    return SkillGraph(
        summary=SkillGraphSummary(
            skill_count=len(loaded_skills),
            enabled_skill_count=sum(1 for skill in loaded_skills if skill.enabled),
            public_skill_count=sum(1 for skill in loaded_skills if skill.category == "public"),
            custom_skill_count=sum(1 for skill in loaded_skills if skill.category == "custom"),
            edge_count=len(relationships),
            relationship_counts=dict(relationship_counts),
        ),
        skills=nodes,
        relationships=relationships,
        focus=focus,
    )


def recommend_skills_for_subagent(
    subagent_type: str,
    *,
    skills_path: Path | None = None,
) -> set[str] | None:
    target_stages = SUBAGENT_STAGE_TARGETS.get(subagent_type)
    loaded_skills = load_skills(
        skills_path=skills_path,
        use_config=False,
        enabled_only=True,
    )
    if not loaded_skills:
        return None

    if target_stages is None:
        return {skill.name for skill in loaded_skills}

    if len(target_stages) == 0:
        return None

    graph = analyze_skill_relationships(skills_path=skills_path)
    enabled_lookup = {
        skill.name: skill
        for skill in loaded_skills
    }
    node_lookup = {node.name: node for node in graph.skills if node.enabled}

    selected = {
        node.name
        for node in graph.skills
        if node.enabled and node.stage in target_stages
    }
    if not selected:
        return None

    expanded = set(selected)
    for edge in graph.relationships:
        if edge.source not in enabled_lookup or edge.target not in enabled_lookup:
            continue
        if edge.relationship_type not in {"compose_with", "depend_on", "similar_to"}:
            continue
        if edge.relationship_type == "similar_to" and edge.score < 0.35:
            continue

        if edge.source in selected:
            other_name = edge.target
        elif edge.target in selected:
            other_name = edge.source
        else:
            continue

        other_node = node_lookup.get(other_name)
        if other_node is None:
            continue
        if other_node.stage in target_stages or other_node.stage is None:
            expanded.add(other_name)

    return expanded
