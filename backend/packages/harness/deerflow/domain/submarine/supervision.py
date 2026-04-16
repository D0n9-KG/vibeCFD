"""Scientific supervisor-gate helpers for submarine CFD reporting."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import SubmarineScientificSupervisorGate


def _as_mapping(value: object | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _as_string_list(value: object | None) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped


def _filter_benchmark_messages(values: list[str]) -> list[str]:
    return [value for value in values if "benchmark" in value.lower()]


def build_scientific_supervisor_gate(
    *,
    research_evidence_summary: object | None,
    artifact_virtual_paths: list[str] | None = None,
) -> dict[str, Any]:
    summary = _as_mapping(research_evidence_summary)
    readiness_status = str(summary.get("readiness_status") or "insufficient_evidence")
    validation_status = str(summary.get("validation_status") or "").strip()
    provenance_status = str(summary.get("provenance_status") or "").strip()
    blocking_reasons = _as_string_list(summary.get("blocking_issues"))
    evidence_gaps = _as_string_list(summary.get("evidence_gaps"))
    benchmark_highlights = _as_string_list(summary.get("benchmark_highlights"))
    benchmark_messages = _dedupe_strings(
        _filter_benchmark_messages(
            [
                *blocking_reasons,
                *evidence_gaps,
                *benchmark_highlights,
            ]
        )
    )

    gate_status = "blocked"
    allowed_claim_level = "delivery_only"
    recommended_stage = "solver-dispatch"
    remediation_stage: str | None = "solver-dispatch"
    advisory_notes: list[str] = []

    if readiness_status == "research_ready":
        gate_status = "ready_for_claim"
        allowed_claim_level = "research_ready"
        recommended_stage = "supervisor-review"
        remediation_stage = None
        if benchmark_highlights:
            advisory_notes.append("Benchmark validation, scientific verification, and provenance evidence are aligned for supervisor sign-off.")
    elif readiness_status == "verified_but_not_validated":
        gate_status = "claim_limited"
        allowed_claim_level = "verified_but_not_validated"
        recommended_stage = "supervisor-review"
        remediation_stage = "solver-dispatch"
        if benchmark_messages:
            advisory_notes.extend(benchmark_messages)
        elif validation_status == "missing_validation_reference":
            advisory_notes.append("External validation evidence is still missing for this run.")
    elif readiness_status == "validated_with_gaps":
        gate_status = "claim_limited"
        allowed_claim_level = "validated_with_gaps"
        recommended_stage = "supervisor-review"
        remediation_stage = "result-reporting"
        if benchmark_messages:
            advisory_notes.extend(benchmark_messages)
        if provenance_status in {"partial", "missing"} or evidence_gaps:
            advisory_notes.append("Scientific evidence is validated, but reporting and provenance gaps still limit the claim level.")
    elif readiness_status in {"blocked", "insufficient_evidence"}:
        if validation_status == "validation_failed":
            recommended_stage = "solver-dispatch"
            remediation_stage = "solver-dispatch"
            if benchmark_messages:
                blocking_reasons = _dedupe_strings([*blocking_reasons, *benchmark_messages])
            advisory_notes.append("Benchmark validation failed against the current CFD output. Revisit solver-dispatch before any research-grade claim is approved.")
        if provenance_status in {"partial", "missing"} and not blocking_reasons:
            recommended_stage = "result-reporting"
            remediation_stage = "result-reporting"

    blocking_reasons = _dedupe_strings(blocking_reasons)
    advisory_notes = _dedupe_strings(advisory_notes)

    gate = SubmarineScientificSupervisorGate(
        gate_status=gate_status,
        allowed_claim_level=allowed_claim_level,
        source_readiness_status=readiness_status,
        recommended_stage=recommended_stage,
        remediation_stage=remediation_stage,
        blocking_reasons=blocking_reasons,
        advisory_notes=advisory_notes,
        artifact_virtual_paths=artifact_virtual_paths or [],
    )
    return gate.model_dump(mode="json")
