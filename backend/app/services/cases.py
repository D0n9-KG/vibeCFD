from __future__ import annotations

import json
import re
from pathlib import Path

from ..config import get_settings
from ..models import CaseCandidate, CaseSearchResult, SkillManifest, TaskSubmission


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


class CaseLibrary:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _load_cases(self) -> list[dict]:
        payload = json.loads(self.settings.cases_file.read_text(encoding="utf-8"))
        return payload["cases"]

    def _load_skills(self) -> dict[str, SkillManifest]:
        payload = json.loads(self.settings.skills_file.read_text(encoding="utf-8"))
        manifests = [SkillManifest.model_validate(item) for item in payload["skills"]]
        return {manifest.skill_id: manifest for manifest in manifests}

    def _tokenize(self, text: str) -> set[str]:
        return {token.lower() for token in TOKEN_PATTERN.findall(text)}

    def _score_case(self, task: TaskSubmission, case: dict) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        if task.task_type == case["task_type"]:
            score += 4.0
            reasons.append("任务类型完全匹配")

        if task.geometry_family_hint:
            hint = task.geometry_family_hint.lower()
            family = case["geometry_family"].lower()
            if hint == family or hint in family or family in hint:
                score += 3.0
                reasons.append("几何家族高度接近")

        task_tokens = self._tokenize(
            " ".join(
                filter(
                    None,
                    [
                        task.task_description,
                        task.operating_notes,
                        task.geometry_family_hint or "",
                    ],
                )
            )
        )
        case_tokens = self._tokenize(
            " ".join(
                [
                    case["title"],
                    case["geometry_description"],
                    case["task_type"],
                    " ".join(case.get("condition_tags", [])),
                    " ".join(case.get("expected_outputs", [])),
                ]
            )
        )
        overlap = task_tokens & case_tokens
        if overlap:
            token_score = min(len(overlap) * 0.35, 2.5)
            score += token_score
            reasons.append(f"描述关键词重合 {len(overlap)} 项")

        if task.geometry_file_name:
            suffix = Path(task.geometry_file_name).suffix.lower().lstrip(".")
            if any(suffix in item.lower() for item in case.get("input_requirements", [])):
                score += 0.5
                reasons.append("输入格式可复用现有模板")

        if "deep" in task.operating_notes.lower() and "deeply submerged" in {
            tag.lower() for tag in case.get("condition_tags", [])
        }:
            score += 0.75
            reasons.append("工况标签接近")

        if not reasons:
            reasons.append("作为兜底参考案例保留")

        return score, reasons

    def search(self, task: TaskSubmission) -> CaseSearchResult:
        skills = self._load_skills()
        raw_cases = self._load_cases()
        candidates: list[CaseCandidate] = []

        for raw_case in raw_cases:
            score, reasons = self._score_case(task, raw_case)
            candidate = CaseCandidate.model_validate(
                {
                    **raw_case,
                    "score": round(score, 3),
                    "rationale": "；".join(reasons),
                }
            )

            related_tools: list[str] = []
            for skill_id in candidate.linked_skills:
                manifest = skills.get(skill_id)
                if manifest:
                    related_tools.extend(manifest.required_tools)
            if related_tools:
                candidate.rationale = (
                    f"{candidate.rationale}；关联工具：{', '.join(sorted(set(related_tools)))}"
                )

            candidates.append(candidate)

        ranked = sorted(candidates, key=lambda item: item.score, reverse=True)[:5]
        if not ranked:
            raise RuntimeError("No cases found for the request.")

        return CaseSearchResult(candidates=ranked, recommended=ranked[0])
