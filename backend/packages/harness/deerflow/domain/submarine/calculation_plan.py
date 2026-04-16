"""Helpers for building and validating the pre-compute calculation-plan draft."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .library import load_case_library
from .models import (
    CalculationPlanItem,
    GeometryReferenceValueSuggestion,
    SubmarineCase,
    SubmarineCaseMatch,
)


def normalize_calculation_plan(
    items: list[CalculationPlanItem | Mapping[str, Any]] | None,
) -> list[CalculationPlanItem]:
    normalized: list[CalculationPlanItem] = []
    for item in items or []:
        normalized.append(CalculationPlanItem.model_validate(item))
    return normalized


def calculation_plan_requires_confirmation(
    items: list[CalculationPlanItem | Mapping[str, Any]] | None,
) -> bool:
    return any(item.approval_state != "researcher_confirmed" for item in normalize_calculation_plan(items))


def calculation_plan_requires_immediate_confirmation(
    items: list[CalculationPlanItem | Mapping[str, Any]] | None,
) -> bool:
    return any(item.approval_state != "researcher_confirmed" and item.requires_immediate_confirmation for item in normalize_calculation_plan(items))


def confirm_calculation_plan(
    items: list[CalculationPlanItem | Mapping[str, Any]] | None,
) -> list[dict]:
    confirmed = []
    for item in normalize_calculation_plan(items):
        item.approval_state = "researcher_confirmed"
        confirmed.append(item.model_dump(mode="json"))
    return confirmed


def merge_calculation_plan(
    *,
    existing: list[CalculationPlanItem | Mapping[str, Any]] | None,
    updates: list[CalculationPlanItem | Mapping[str, Any]] | None,
) -> list[dict]:
    existing_items = normalize_calculation_plan(existing)
    existing_by_id = {item.item_id: item for item in existing_items}
    merged: list[CalculationPlanItem] = []
    seen: set[str] = set()

    for raw_update in updates or []:
        item = CalculationPlanItem.model_validate(raw_update)
        previous = existing_by_id.get(item.item_id)
        if previous is not None:
            if previous.researcher_note and not item.researcher_note:
                item.researcher_note = previous.researcher_note
            if _same_plan_payload(previous, item):
                item.approval_state = previous.approval_state
                if previous.origin in {"user_input", "researcher_edit"}:
                    item.origin = previous.origin
            elif previous.approval_state == "researcher_confirmed":
                item.origin = "researcher_edit"
        merged.append(item)
        seen.add(item.item_id)

    for item in existing_items:
        if item.item_id not in seen:
            merged.append(item)

    return [item.model_dump(mode="json") for item in merged]


def build_design_brief_calculation_plan(
    *,
    existing: list[CalculationPlanItem | Mapping[str, Any]] | None,
    confirmation_status: str,
    selected_case_id: str | None,
    simulation_requirements: Mapping[str, Any] | None,
) -> list[dict]:
    items: list[CalculationPlanItem] = []
    item_state = "researcher_confirmed" if confirmation_status == "confirmed" else "pending_researcher_confirmation"
    origin = "user_input" if confirmation_status == "confirmed" else "ai_suggestion"

    for field, label, unit in (
        ("inlet_velocity_mps", "入口速度", "m/s"),
        ("fluid_density_kg_m3", "流体密度", "kg/m^3"),
        ("kinematic_viscosity_m2ps", "运动黏度", "m^2/s"),
        ("end_time_seconds", "仿真时长", "s"),
        ("delta_t_seconds", "时间步长", "s"),
        ("write_interval_steps", "写出步数间隔", "steps"),
    ):
        value = None if simulation_requirements is None else simulation_requirements.get(field)
        if value is None:
            continue
        items.append(
            CalculationPlanItem(
                item_id=f"simulation.{field}",
                category="simulation",
                label=label,
                proposed_value=value,
                unit=unit,
                source_label="Research brief",
                confidence="high",
                origin=origin,
                approval_state=item_state,
            )
        )

    selected_case = _resolve_case(selected_case_id)
    if selected_case is not None:
        primary_source = _pick_primary_source(selected_case.reference_sources)
        items.append(
            CalculationPlanItem(
                item_id="case.selected_case_id",
                category="case",
                label="推荐案例模板",
                proposed_value=selected_case.case_id,
                source_label=(primary_source.source_label or primary_source.title) if primary_source else selected_case.title,
                source_url=primary_source.url if primary_source else None,
                confidence="medium" if primary_source and primary_source.is_placeholder else "high",
                applicability_conditions=_collect_applicability_conditions(selected_case),
                evidence_gap_note=primary_source.evidence_gap_note if primary_source else None,
                origin="ai_suggestion",
                approval_state=item_state,
            )
        )

    merged = merge_calculation_plan(existing=existing, updates=items)
    if confirmation_status == "confirmed":
        return confirm_calculation_plan(merged)
    return merged


def build_geometry_calculation_plan(
    *,
    existing: list[CalculationPlanItem | Mapping[str, Any]] | None,
    reference_value_suggestions: list[GeometryReferenceValueSuggestion | Mapping[str, Any]],
    selected_case: SubmarineCaseMatch | Mapping[str, Any] | None = None,
) -> list[dict]:
    items: list[CalculationPlanItem] = []
    for raw_suggestion in reference_value_suggestions:
        suggestion = GeometryReferenceValueSuggestion.model_validate(raw_suggestion)
        label = "参考长度" if suggestion.quantity == "reference_length_m" else "参考面积"
        items.append(
            CalculationPlanItem(
                item_id=f"geometry.{suggestion.quantity}",
                category="geometry",
                label=label,
                proposed_value=suggestion.value,
                unit=suggestion.unit,
                source_label=suggestion.source,
                confidence=suggestion.confidence,
                evidence_gap_note=(suggestion.summary_zh if suggestion.requires_confirmation else None),
                origin="ai_suggestion",
                approval_state="pending_researcher_confirmation",
                requires_immediate_confirmation=suggestion.requires_confirmation,
            )
        )

    if selected_case is not None:
        case_match = SubmarineCaseMatch.model_validate(selected_case)
        items.append(
            CalculationPlanItem(
                item_id="case.selected_case_id",
                category="case",
                label="推荐案例模板",
                proposed_value=case_match.case_id,
                source_label=case_match.source_label or case_match.title,
                source_url=case_match.source_url,
                confidence="medium" if case_match.is_placeholder else "high",
                applicability_conditions=case_match.applicability_conditions,
                evidence_gap_note=case_match.evidence_gap_note,
                origin="ai_suggestion",
                approval_state="pending_researcher_confirmation",
                requires_immediate_confirmation=False,
            )
        )

    return merge_calculation_plan(existing=existing, updates=items)


def extract_geometry_reference_inputs(
    items: list[CalculationPlanItem | Mapping[str, Any]] | None,
) -> dict[str, Any] | None:
    normalized = normalize_calculation_plan(items)
    reference_values: dict[str, Any] = {}
    justifications: list[str] = []
    approval_state = "researcher_confirmed"

    for item in normalized:
        if item.item_id == "geometry.reference_length_m":
            reference_values["reference_length_m"] = item.proposed_value
        elif item.item_id == "geometry.reference_area_m2":
            reference_values["reference_area_m2"] = item.proposed_value
        else:
            continue

        justifications.append(f"{item.label}: {item.source_label or 'calculation-plan draft'}")
        if item.approval_state != "researcher_confirmed":
            approval_state = item.approval_state

    if not reference_values:
        return None

    reference_values["approval_state"] = approval_state
    reference_values["justification"] = "; ".join(justifications)
    return reference_values


def _same_plan_payload(
    previous: CalculationPlanItem,
    current: CalculationPlanItem,
) -> bool:
    return (
        previous.proposed_value == current.proposed_value
        and previous.proposed_range == current.proposed_range
        and previous.unit == current.unit
        and previous.source_label == current.source_label
        and previous.source_url == current.source_url
        and previous.applicability_conditions == current.applicability_conditions
        and previous.evidence_gap_note == current.evidence_gap_note
        and previous.requires_immediate_confirmation == current.requires_immediate_confirmation
    )


def _resolve_case(selected_case_id: str | None) -> SubmarineCase | None:
    if not selected_case_id:
        return None
    return load_case_library().case_index.get(selected_case_id)


def _pick_primary_source(reference_sources):
    if not reference_sources:
        return None
    for source in reference_sources:
        if not source.is_placeholder:
            return source
    return reference_sources[0]


def _collect_applicability_conditions(selected_case: SubmarineCase) -> list[str]:
    conditions = [
        *selected_case.condition_tags,
        *(_pick_primary_source(selected_case.reference_sources).applicability_conditions if _pick_primary_source(selected_case.reference_sources) else []),
    ]
    deduped: list[str] = []
    for condition in conditions:
        normalized = condition.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped
