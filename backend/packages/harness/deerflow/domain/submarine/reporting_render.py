"""Markdown and HTML render helpers for submarine result reporting."""

from __future__ import annotations

from html import escape
from typing import Any


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _format_float(value: object, digits: int = 1) -> str:
    if not _is_number(value):
        return "unknown"
    return f"{float(value):.{digits}f}"


def _format_percent(value: object, digits: int = 1) -> str:
    if not _is_number(value):
        return "unknown"
    return f"{float(value) * 100:.{digits}f}%"


def _render_acceptance_markdown(acceptance_assessment: dict | None) -> list[str]:
    if not acceptance_assessment:
        return []

    lines = [
        "",
        "## Delivery Readiness",
        f"- status: `{acceptance_assessment.get('status')}`",
        f"- confidence: `{acceptance_assessment.get('confidence')}`",
        f"- gate_count: `{acceptance_assessment.get('gate_count')}`",
    ]

    gates = acceptance_assessment.get("gates") or []
    if gates:
        lines.extend(["", "### Gates"])
        lines.extend(f"- `{gate.get('id')}` | `{gate.get('status')}` | {gate.get('detail')}" for gate in gates)

    blocking_issues = acceptance_assessment.get("blocking_issues") or []
    if blocking_issues:
        lines.extend(["", "### Blocking Issues"])
        lines.extend(f"- {item}" for item in blocking_issues)

    warnings = acceptance_assessment.get("warnings") or []
    if warnings:
        lines.extend(["", "### Warnings"])
        lines.extend(f"- {item}" for item in warnings)

    passed_checks = acceptance_assessment.get("passed_checks") or []
    if passed_checks:
        lines.extend(["", "### Passed Checks"])
        lines.extend(f"- {item}" for item in passed_checks)

    benchmark_comparisons = acceptance_assessment.get("benchmark_comparisons") or []
    if benchmark_comparisons:
        lines.extend(["", "### Benchmark Comparisons"])
        lines.extend(
            "- "
            + " | ".join(
                [
                    f"`{item.get('metric_id')}`",
                    f"`{item.get('status')}`",
                    f"observed={item.get('observed_value')}",
                    f"reference={item.get('reference_value')}",
                    f"rel_error={_format_percent(item.get('relative_error'))}",
                ]
            )
            for item in benchmark_comparisons
        )

    return lines


def render_delivery_readiness_markdown(
    report_title: str,
    acceptance_assessment: dict,
) -> str:
    lines = [
        f"# Delivery Readiness · {report_title}",
        "",
        "This artifact summarizes whether the current submarine CFD run is ready for supervisor review.",
    ]
    lines.extend(_render_acceptance_markdown(acceptance_assessment))
    lines.append("")
    return "\n".join(lines)


def _render_output_delivery_markdown(output_delivery_plan: list[dict] | None) -> list[str]:
    if not output_delivery_plan:
        return []

    lines = ["", "## Requested Output Delivery"]
    lines.extend(
        (
            "- "
            + " | ".join(
                [
                    f"`{item.get('output_id')}`",
                    f"`{item.get('delivery_status')}`",
                    str(item.get("detail") or "No detail"),
                ]
            )
        )
        for item in output_delivery_plan
    )
    return lines


def _render_figure_delivery_markdown(figure_delivery_summary: dict | None) -> list[str]:
    if not figure_delivery_summary:
        return []

    lines = [
        "",
        "## Figure Delivery",
        f"- figure_count: `{figure_delivery_summary.get('figure_count')}`",
        f"- manifest: `{figure_delivery_summary.get('manifest_virtual_path')}`",
    ]
    figures = figure_delivery_summary.get("figures") or []
    if figures:
        lines.extend(["", "### Figure Summary"])
        lines.extend(
            (
                "- "
                + " | ".join(
                    [
                        f"`{item.get('output_id')}`",
                        f"`{item.get('render_status')}`",
                        str(item.get("title") or "Untitled"),
                        str(item.get("selector_summary") or "No selector provenance"),
                        str(item.get("caption") or "No caption"),
                    ]
                )
            )
            for item in figures
        )
    return lines


def _render_acceptance_html(acceptance_assessment: dict | None) -> str:
    if not acceptance_assessment:
        return ""

    def render_items(items: list[str]) -> str:
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{escape(item)}</li>" for item in items)

    gates = acceptance_assessment.get("gates") or []
    gate_items = "".join(f"<li><strong>{escape(str(gate.get('label')))}</strong> ({escape(str(gate.get('status')))})<p>{escape(str(gate.get('detail')))}</p></li>" for gate in gates) or "<li>None</li>"

    return (
        '<section class="panel">'
        "<h2>Delivery Readiness</h2>"
        f"<p><strong>status:</strong> {escape(str(acceptance_assessment.get('status')))}</p>"
        f"<p><strong>confidence:</strong> {escape(str(acceptance_assessment.get('confidence')))}</p>"
        f"<p><strong>gate_count:</strong> {escape(str(acceptance_assessment.get('gate_count')))}</p>"
        "<h3>Gates</h3>"
        f"<ul>{gate_items}</ul>"
        "<h3>Blocking Issues</h3>"
        f"<ul>{render_items(acceptance_assessment.get('blocking_issues') or [])}</ul>"
        "<h3>Warnings</h3>"
        f"<ul>{render_items(acceptance_assessment.get('warnings') or [])}</ul>"
        "<h3>Passed Checks</h3>"
        f"<ul>{render_items(acceptance_assessment.get('passed_checks') or [])}</ul>"
        "<h3>Benchmark Comparisons</h3>"
        "<ul>"
        + (
            "".join(
                "<li>"
                f"<strong>{escape(str(item.get('metric_id')))}</strong> "
                f"({escape(str(item.get('status')))})"
                f"<p>observed={escape(str(item.get('observed_value')))}, "
                f"reference={escape(str(item.get('reference_value')))}, "
                f"relative_error={escape(_format_percent(item.get('relative_error')))}</p>"
                "</li>"
                for item in (acceptance_assessment.get("benchmark_comparisons") or [])
            )
            or "<li>None</li>"
        )
        + "</ul>"
        "</section>"
    )


def _render_output_delivery_html(output_delivery_plan: list[dict] | None) -> str:
    if not output_delivery_plan:
        return ""

    items = (
        "".join(
            f"<li><strong>{escape(str(item.get('label') or item.get('output_id')))}</strong> (<code>{escape(str(item.get('delivery_status')))}</code>)<p>{escape(str(item.get('detail') or 'No detail'))}</p></li>"
            for item in output_delivery_plan
        )
        or "<li>None</li>"
    )
    return f'<section class="panel"><h2>Requested Output Delivery</h2><ul>{items}</ul></section>'


def _render_figure_delivery_html(figure_delivery_summary: dict | None) -> str:
    if not figure_delivery_summary:
        return ""

    items = (
        "".join(
            "<li>"
            f"<strong>{escape(str(item.get('title') or item.get('output_id')))}</strong> "
            f"(<code>{escape(str(item.get('render_status')))}</code>)"
            f"<p>{escape(str(item.get('caption') or 'No caption'))}</p>"
            f"<p>{escape(str(item.get('selector_summary') or 'No selector provenance'))}</p>"
            "</li>"
            for item in (figure_delivery_summary.get("figures") or [])
        )
        or "<li>None</li>"
    )
    return (
        '<section class="panel">'
        "<h2>Figure Delivery</h2>"
        f"<p><strong>manifest:</strong> {escape(str(figure_delivery_summary.get('manifest_virtual_path') or '--'))}</p>"
        f"<p><strong>figure_count:</strong> {escape(str(figure_delivery_summary.get('figure_count') or 0))}</p>"
        f"<ul>{items}</ul>"
        "</section>"
    )


def _as_string_list(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item) for item in items if str(item)]


def _format_status_count_items(counts: object) -> list[str]:
    if not isinstance(counts, dict):
        return []
    items: list[str] = []
    for status, count in counts.items():
        if not _is_number(count):
            continue
        items.append(f"{status}: {int(count)}")
    return items


def _render_markdown_items(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return ["", f"### {title}", *(f"- {item}" for item in items)]


def _render_html_items(title: str, items: list[str]) -> str:
    rendered_items = "".join(f"<li>{escape(item)}</li>" for item in items) or "<li>None</li>"
    return f"<h3>{escape(title)}</h3><ul>{rendered_items}</ul>"


def _render_scientific_study_markdown(scientific_study_summary: dict | None) -> list[str]:
    if not scientific_study_summary:
        return []

    lines = [
        "",
        "## Scientific Studies",
        f"- execution_status: `{scientific_study_summary.get('study_execution_status')}`",
        f"- workflow_status: `{scientific_study_summary.get('workflow_status')}`",
        f"- manifest: `{scientific_study_summary.get('manifest_virtual_path')}`",
    ]
    lines.extend(
        _render_markdown_items(
            "Study Workflow Counts",
            _format_status_count_items(scientific_study_summary.get("study_status_counts")),
        )
    )
    studies = scientific_study_summary.get("studies") or []
    if studies:
        lines.extend(["", "### Study Summary"])
        for item in studies:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"`{item.get('study_type')}`",
                        f"execution=`{item.get('study_execution_status')}`",
                        f"workflow=`{item.get('workflow_status')}`",
                        f"verification=`{item.get('verification_status')}`",
                        f"variants={item.get('variant_count')}",
                        str(item.get("workflow_detail") or "No workflow detail"),
                    ]
                )
            )
            lines.extend(
                _render_markdown_items(
                    f"{item.get('study_type')} Variant Status Counts",
                    _format_status_count_items(item.get("variant_status_counts")),
                )
            )
            lines.extend(
                _render_markdown_items(
                    f"{item.get('study_type')} Compare Status Counts",
                    _format_status_count_items(item.get("compare_status_counts")),
                )
            )
            lines.extend(
                _render_markdown_items(
                    f"{item.get('study_type')} Expected Variant Runs",
                    _as_string_list(item.get("expected_variant_run_ids")),
                )
            )
            lines.extend(
                _render_markdown_items(
                    f"{item.get('study_type')} Planned Variant Runs",
                    _as_string_list(item.get("planned_variant_run_ids")),
                )
            )
            lines.extend(
                _render_markdown_items(
                    f"{item.get('study_type')} Blocked Variant Runs",
                    _as_string_list(item.get("blocked_variant_run_ids")),
                )
            )
            lines.extend(
                _render_markdown_items(
                    f"{item.get('study_type')} Pending Compare Coverage",
                    _as_string_list(item.get("planned_compare_variant_run_ids")),
                )
            )
            lines.extend(
                _render_markdown_items(
                    f"{item.get('study_type')} Missing Compare Metrics",
                    _as_string_list(item.get("missing_metrics_variant_run_ids")),
                )
            )
            verification_detail = str(item.get("verification_detail") or "").strip()
            if verification_detail:
                lines.extend(
                    [
                        "",
                        f"### {item.get('study_type')} Verification Detail",
                        f"- {verification_detail}",
                    ]
                )

    return lines


def _render_experiment_markdown(experiment_summary: dict | None) -> list[str]:
    if not experiment_summary:
        return []

    lines = [
        "",
        "## Experiment Registry",
        f"- experiment_id: `{experiment_summary.get('experiment_id')}`",
        f"- experiment_status: `{experiment_summary.get('experiment_status')}`",
        f"- workflow_status: `{experiment_summary.get('workflow_status')}`",
        f"- baseline_run_id: `{experiment_summary.get('baseline_run_id')}`",
        f"- run_count: `{experiment_summary.get('run_count')}`",
        f"- compare_count: `{experiment_summary.get('compare_count')}`",
        f"- linkage_status: `{experiment_summary.get('linkage_status')}`",
        f"- linkage_issue_count: `{experiment_summary.get('linkage_issue_count')}`",
        f"- manifest: `{experiment_summary.get('manifest_virtual_path')}`",
    ]
    if experiment_summary.get("study_manifest_virtual_path"):
        lines.append(f"- study_manifest: `{experiment_summary.get('study_manifest_virtual_path')}`")
    if experiment_summary.get("compare_virtual_path"):
        lines.append(f"- compare: `{experiment_summary.get('compare_virtual_path')}`")
    workflow_detail = str(experiment_summary.get("workflow_detail") or "").strip()
    if workflow_detail:
        lines.extend(["", "### Workflow Detail", f"- {workflow_detail}"])
    lines.extend(
        _render_markdown_items(
            "Run Status Counts",
            _format_status_count_items(experiment_summary.get("run_status_counts")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Compare Status Counts",
            _format_status_count_items(experiment_summary.get("compare_status_counts")),
        )
    )
    expected_variant_run_ids = experiment_summary.get("expected_variant_run_ids") or []
    if expected_variant_run_ids:
        lines.extend(
            [
                "",
                "### Planned Variant Coverage",
                f"- expected_variant_run_ids: `{', '.join(str(item) for item in expected_variant_run_ids)}`",
                f"- recorded_variant_run_ids: `{', '.join(str(item) for item in (experiment_summary.get('recorded_variant_run_ids') or [])) or '--'}`",
                f"- compared_variant_run_ids: `{', '.join(str(item) for item in (experiment_summary.get('compared_variant_run_ids') or [])) or '--'}`",
            ]
        )
    registered_custom_variant_run_ids = experiment_summary.get("registered_custom_variant_run_ids") or []
    if registered_custom_variant_run_ids:
        lines.extend(
            [
                "",
                "### Custom Variant Coverage",
                f"- registered_custom_variant_run_ids: `{', '.join(str(item) for item in registered_custom_variant_run_ids)}`",
                f"- planned_custom_variant_run_ids: `{', '.join(str(item) for item in (experiment_summary.get('planned_custom_variant_run_ids') or [])) or '--'}`",
                f"- completed_custom_variant_run_ids: `{', '.join(str(item) for item in (experiment_summary.get('completed_custom_variant_run_ids') or [])) or '--'}`",
                f"- missing_custom_compare_entry_ids: `{', '.join(str(item) for item in (experiment_summary.get('missing_custom_compare_entry_ids') or [])) or '--'}`",
            ]
        )
    lines.extend(
        _render_markdown_items(
            "Missing Variant Run Records",
            _as_string_list(experiment_summary.get("missing_variant_run_record_ids")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Missing Compare Entries",
            _as_string_list(experiment_summary.get("missing_compare_entry_ids")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Planned Variant Runs",
            _as_string_list(experiment_summary.get("planned_variant_run_ids")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Blocked Variant Runs",
            _as_string_list(experiment_summary.get("blocked_variant_run_ids")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Missing Compare Metrics",
            _as_string_list(experiment_summary.get("missing_metrics_variant_run_ids")),
        )
    )
    compare_notes = experiment_summary.get("compare_notes") or []
    if compare_notes:
        lines.extend(["", "### Compare Summary"])
        lines.extend(f"- {item}" for item in compare_notes)
    linkage_issues = experiment_summary.get("linkage_issues") or []
    if linkage_issues:
        lines.extend(["", "### Linkage Issues"])
        lines.extend(f"- {item}" for item in linkage_issues)
    return lines


def _format_compare_metric_delta_lines(metric_deltas: object) -> list[str]:
    if not isinstance(metric_deltas, dict):
        return []

    lines: list[str] = []
    for metric_name, payload in metric_deltas.items():
        if not isinstance(payload, dict):
            continue
        lines.append(
            " ".join(
                [
                    f"{metric_name}:",
                    f"baseline={payload.get('baseline_value')}",
                    f"candidate={payload.get('candidate_value')}",
                    f"delta={payload.get('absolute_delta')}",
                    f"relative={_format_percent(payload.get('relative_delta'))}",
                ]
            )
        )
    return lines


def _is_custom_compare_entry(item: dict[str, Any]) -> bool:
    run_role = str(item.get("run_role") or item.get("variant_origin") or "").strip()
    candidate_run_id = str(item.get("candidate_run_id") or "").strip()
    return run_role == "custom_variant" or candidate_run_id.startswith("custom:")


def _format_compare_entry_label(item: dict[str, Any]) -> str:
    variant_id = str(item.get("variant_id") or "unknown").strip() or "unknown"
    if _is_custom_compare_entry(item):
        return f"custom / {variant_id}"
    study_type = str(item.get("study_type") or "unknown").strip() or "unknown"
    return f"{study_type} / {variant_id}"


def _render_experiment_compare_markdown(
    experiment_compare_summary: dict | None,
) -> list[str]:
    if not experiment_compare_summary:
        return []

    lines = [
        "",
        "## Experiment Compare",
        f"- baseline_run_id: `{experiment_compare_summary.get('baseline_run_id')}`",
        f"- compare_count: `{experiment_compare_summary.get('compare_count')}`",
        f"- workflow_status: `{experiment_compare_summary.get('workflow_status')}`",
        f"- compare: `{experiment_compare_summary.get('compare_virtual_path')}`",
    ]
    lines.extend(
        _render_markdown_items(
            "Compare Status Counts",
            _format_status_count_items(experiment_compare_summary.get("compare_status_counts")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Planned Candidate Runs",
            _as_string_list(experiment_compare_summary.get("planned_candidate_run_ids")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Completed Candidate Runs",
            _as_string_list(experiment_compare_summary.get("completed_candidate_run_ids")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Blocked Candidate Runs",
            _as_string_list(experiment_compare_summary.get("blocked_candidate_run_ids")),
        )
    )
    lines.extend(
        _render_markdown_items(
            "Missing Compare Metrics",
            _as_string_list(experiment_compare_summary.get("missing_metrics_candidate_run_ids")),
        )
    )
    comparisons = experiment_compare_summary.get("comparisons") or []
    if comparisons:
        lines.extend(["", "### Compare Entries"])
        for item in comparisons:
            if not isinstance(item, dict):
                continue
            metric_lines = _format_compare_metric_delta_lines(item.get("metric_deltas"))
            detail = " | ".join(metric_lines) if metric_lines else str(item.get("notes") or "No metric delta")
            compare_target_run_id = str(item.get("compare_target_run_id") or item.get("baseline_run_id") or "baseline")
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"`{item.get('candidate_run_id')}`",
                        f"`{item.get('compare_status')}`",
                        f"execution=`{item.get('candidate_execution_status') or '--'}`",
                        _format_compare_entry_label(item),
                        f"compare_target=`{compare_target_run_id}`",
                        detail,
                    ]
                )
            )
    return lines


def _render_research_evidence_markdown(research_evidence_summary: dict | None) -> list[str]:
    if not research_evidence_summary:
        return []

    lines = [
        "",
        "## Research Evidence",
        f"- readiness_status: `{research_evidence_summary.get('readiness_status')}`",
        f"- verification_status: `{research_evidence_summary.get('verification_status')}`",
        f"- validation_status: `{research_evidence_summary.get('validation_status')}`",
        f"- provenance_status: `{research_evidence_summary.get('provenance_status')}`",
        f"- confidence: `{research_evidence_summary.get('confidence')}`",
    ]
    passed_evidence = research_evidence_summary.get("passed_evidence") or []
    evidence_gaps = research_evidence_summary.get("evidence_gaps") or []
    if passed_evidence:
        lines.extend(["", "### Passed Evidence"])
        lines.extend(f"- {item}" for item in passed_evidence)
    if evidence_gaps:
        lines.extend(["", "### Evidence Gaps"])
        lines.extend(f"- {item}" for item in evidence_gaps)
    return lines


def _render_reproducibility_markdown(
    reproducibility_summary: dict | None,
) -> list[str]:
    if not reproducibility_summary:
        return []

    lines = [
        "",
        "## Reproducibility",
        f"- manifest: `{reproducibility_summary.get('manifest_virtual_path') or '--'}`",
        f"- profile_id: `{reproducibility_summary.get('profile_id') or '--'}`",
        f"- parity_status: `{reproducibility_summary.get('parity_status') or '--'}`",
        (f"- reproducibility_status: `{reproducibility_summary.get('reproducibility_status') or '--'}`"),
    ]
    drift_reasons = reproducibility_summary.get("drift_reasons") or []
    if drift_reasons:
        lines.extend(["", "### Drift Reasons"])
        lines.extend(f"- {item}" for item in drift_reasons)
    recovery_guidance = reproducibility_summary.get("recovery_guidance") or []
    if recovery_guidance:
        lines.extend(["", "### Recovery Guidance"])
        lines.extend(f"- {item}" for item in recovery_guidance)
    return lines


def _render_scientific_gate_markdown(scientific_supervisor_gate: dict | None) -> list[str]:
    if not scientific_supervisor_gate:
        return []

    lines = [
        "",
        "## Scientific Supervisor Gate",
        f"- gate_status: `{scientific_supervisor_gate.get('gate_status')}`",
        f"- allowed_claim_level: `{scientific_supervisor_gate.get('allowed_claim_level')}`",
        f"- source_readiness_status: `{scientific_supervisor_gate.get('source_readiness_status')}`",
        f"- recommended_stage: `{scientific_supervisor_gate.get('recommended_stage')}`",
        f"- remediation_stage: `{scientific_supervisor_gate.get('remediation_stage') or 'none'}`",
    ]
    artifact_paths = scientific_supervisor_gate.get("artifact_virtual_paths") or []
    if artifact_paths:
        lines.extend(["", "### Gate Artifacts"])
        lines.extend(f"- `{path}`" for path in artifact_paths)
    blocking_reasons = scientific_supervisor_gate.get("blocking_reasons") or []
    if blocking_reasons:
        lines.extend(["", "### Blocking Reasons"])
        lines.extend(f"- {item}" for item in blocking_reasons)
    advisory_notes = scientific_supervisor_gate.get("advisory_notes") or []
    if advisory_notes:
        lines.extend(["", "### Advisory Notes"])
        lines.extend(f"- {item}" for item in advisory_notes)
    return lines


def _render_scientific_remediation_markdown(
    scientific_remediation_summary: dict | None,
) -> list[str]:
    if not scientific_remediation_summary:
        return []

    lines = [
        "",
        "## Scientific Remediation Plan",
        f"- plan_status: `{scientific_remediation_summary.get('plan_status')}`",
        f"- current_claim_level: `{scientific_remediation_summary.get('current_claim_level')}`",
        f"- target_claim_level: `{scientific_remediation_summary.get('target_claim_level')}`",
        f"- recommended_stage: `{scientific_remediation_summary.get('recommended_stage')}`",
    ]
    artifact_paths = scientific_remediation_summary.get("artifact_virtual_paths") or []
    if artifact_paths:
        lines.extend(["", "### Remediation Artifacts"])
        lines.extend(f"- `{path}`" for path in artifact_paths)
    actions = scientific_remediation_summary.get("actions") or []
    if actions:
        lines.extend(["", "### Remediation Actions"])
        for item in actions:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"`{item.get('action_id')}`",
                        f"`{item.get('owner_stage')}`",
                        f"`{item.get('execution_mode')}`",
                        str(item.get("evidence_gap") or "No evidence gap"),
                    ]
                )
            )
    return lines


def _render_scientific_remediation_handoff_markdown(
    scientific_remediation_handoff: dict | None,
) -> list[str]:
    if not scientific_remediation_handoff:
        return []

    lines = [
        "",
        "## Scientific Remediation Handoff",
        f"- handoff_status: `{scientific_remediation_handoff.get('handoff_status')}`",
        (f"- recommended_action_id: `{scientific_remediation_handoff.get('recommended_action_id') or 'none'}`"),
        f"- tool_name: `{scientific_remediation_handoff.get('tool_name') or 'manual_only'}`",
        f"- reason: {scientific_remediation_handoff.get('reason') or 'No detail'}",
    ]
    artifact_paths = scientific_remediation_handoff.get("artifact_virtual_paths") or []
    if artifact_paths:
        lines.extend(["", "### Handoff Artifacts"])
        lines.extend(f"- `{path}`" for path in artifact_paths)
    tool_args = scientific_remediation_handoff.get("tool_args") or {}
    if tool_args:
        lines.extend(["", "### Suggested Tool Args"])
        for key, value in tool_args.items():
            lines.append(f"- `{key}`: `{value}`")
    manual_actions = scientific_remediation_handoff.get("manual_actions") or []
    if manual_actions:
        lines.extend(["", "### Manual Actions"])
        for item in manual_actions:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"`{item.get('action_id')}`",
                        f"`{item.get('owner_stage')}`",
                        str(item.get("evidence_gap") or "Manual follow-up required"),
                    ]
                )
            )
    return lines


def _render_scientific_followup_markdown(
    scientific_followup_summary: dict | None,
) -> list[str]:
    if not scientific_followup_summary:
        return []

    lines = [
        "",
        "## Scientific Follow-Up History",
        f"- entry_count: `{scientific_followup_summary.get('entry_count')}`",
        f"- latest_outcome_status: `{scientific_followup_summary.get('latest_outcome_status')}`",
        f"- latest_handoff_status: `{scientific_followup_summary.get('latest_handoff_status')}`",
        (f"- latest_recommended_action_id: `{scientific_followup_summary.get('latest_recommended_action_id') or 'none'}`"),
        f"- latest_tool_name: `{scientific_followup_summary.get('latest_tool_name') or 'none'}`",
        (f"- latest_dispatch_stage_status: `{scientific_followup_summary.get('latest_dispatch_stage_status') or 'none'}`"),
        f"- report_refreshed: `{scientific_followup_summary.get('report_refreshed')}`",
        f"- history: `{scientific_followup_summary.get('history_virtual_path')}`",
    ]
    if scientific_followup_summary.get("latest_result_report_virtual_path"):
        lines.append(f"- latest_result_report: `{scientific_followup_summary.get('latest_result_report_virtual_path')}`")
    if scientific_followup_summary.get("latest_result_supervisor_handoff_virtual_path"):
        lines.append(f"- latest_result_handoff: `{scientific_followup_summary.get('latest_result_supervisor_handoff_virtual_path')}`")
    latest_notes = scientific_followup_summary.get("latest_notes") or []
    if latest_notes:
        lines.extend(["", "### Latest Follow-Up Notes"])
        lines.extend(f"- {item}" for item in latest_notes)
    artifact_paths = scientific_followup_summary.get("artifact_virtual_paths") or []
    if artifact_paths:
        lines.extend(["", "### Follow-Up Artifacts"])
        lines.extend(f"- `{path}`" for path in artifact_paths)
    return lines


def _render_scientific_verification_markdown(
    scientific_verification_assessment: dict | None,
) -> list[str]:
    if not scientific_verification_assessment:
        return []

    lines = [
        "",
        "## Scientific Verification",
        f"- status: `{scientific_verification_assessment.get('status')}`",
        f"- confidence: `{scientific_verification_assessment.get('confidence')}`",
        f"- requirement_count: `{scientific_verification_assessment.get('requirement_count')}`",
    ]
    requirements = scientific_verification_assessment.get("requirements") or []
    if requirements:
        lines.extend(["", "### Verification Requirements"])
        lines.extend(
            (
                "- "
                + " | ".join(
                    [
                        f"`{item.get('requirement_id')}`",
                        f"`{item.get('status')}`",
                        str(item.get("detail") or "No detail"),
                    ]
                )
            )
            for item in requirements
        )

    missing_evidence = scientific_verification_assessment.get("missing_evidence") or []
    if missing_evidence:
        lines.extend(["", "### Missing Evidence"])
        lines.extend(f"- {item}" for item in missing_evidence)

    blocking_issues = scientific_verification_assessment.get("blocking_issues") or []
    if blocking_issues:
        lines.extend(["", "### Blocking Issues"])
        lines.extend(f"- {item}" for item in blocking_issues)

    passed_requirements = scientific_verification_assessment.get("passed_requirements") or []
    if passed_requirements:
        lines.extend(["", "### Passed Requirements"])
        lines.extend(f"- {item}" for item in passed_requirements)

    return lines


def _render_scientific_study_html(scientific_study_summary: dict | None) -> str:
    if not scientific_study_summary:
        return ""

    study_counts_html = _render_html_items(
        "Study Workflow Counts",
        _format_status_count_items(scientific_study_summary.get("study_status_counts")),
    )
    study_sections: list[str] = []
    for item in scientific_study_summary.get("studies") or []:
        if not isinstance(item, dict):
            continue
        detail_sections = [
            _render_html_items(
                "Variant Status Counts",
                _format_status_count_items(item.get("variant_status_counts")),
            ),
            _render_html_items(
                "Compare Status Counts",
                _format_status_count_items(item.get("compare_status_counts")),
            ),
            _render_html_items(
                "Expected Variant Runs",
                _as_string_list(item.get("expected_variant_run_ids")),
            ),
            _render_html_items(
                "Planned Variant Runs",
                _as_string_list(item.get("planned_variant_run_ids")),
            ),
            _render_html_items(
                "Blocked Variant Runs",
                _as_string_list(item.get("blocked_variant_run_ids")),
            ),
            _render_html_items(
                "Pending Compare Coverage",
                _as_string_list(item.get("planned_compare_variant_run_ids")),
            ),
            _render_html_items(
                "Missing Compare Metrics",
                _as_string_list(item.get("missing_metrics_variant_run_ids")),
            ),
        ]
        study_sections.append(
            "<li>"
            f"<strong>{escape(str(item.get('summary_label') or item.get('study_type')))}</strong> "
            f"(<code>{escape(str(item.get('workflow_status') or '--'))}</code>)"
            f"<p>execution={escape(str(item.get('study_execution_status') or '--'))}, "
            f"verification={escape(str(item.get('verification_status') or '--'))}</p>"
            f"<p>{escape(str(item.get('workflow_detail') or 'No workflow detail'))}</p>"
            f"<p>{escape(str(item.get('verification_detail') or 'No detail'))}</p>" + "".join(detail_sections) + "</li>"
        )
    study_items = "".join(study_sections) or "<li>None</li>"

    return (
        '<section class="panel">'
        "<h2>Scientific Studies</h2>"
        f"<p><strong>execution_status:</strong> {escape(str(scientific_study_summary.get('study_execution_status')))}</p>"
        f"<p><strong>workflow_status:</strong> {escape(str(scientific_study_summary.get('workflow_status')))}</p>"
        f"<p><strong>manifest:</strong> {escape(str(scientific_study_summary.get('manifest_virtual_path')))}</p>"
        f"{study_counts_html}"
        "<h3>Study Summary</h3>"
        f"<ul>{study_items}</ul>"
        "</section>"
    )


def _render_experiment_html(experiment_summary: dict | None) -> str:
    if not experiment_summary:
        return ""

    compare_items = "".join(f"<li>{escape(str(item))}</li>" for item in (experiment_summary.get("compare_notes") or [])) or "<li>None</li>"
    linkage_items = "".join(f"<li>{escape(str(item))}</li>" for item in (experiment_summary.get("linkage_issues") or [])) or "<li>None</li>"
    compare_html = f"<p><strong>compare:</strong> {escape(str(experiment_summary.get('compare_virtual_path')))}</p>" if experiment_summary.get("compare_virtual_path") else ""
    study_manifest_html = f"<p><strong>study_manifest:</strong> {escape(str(experiment_summary.get('study_manifest_virtual_path')))}</p>" if experiment_summary.get("study_manifest_virtual_path") else ""
    expected_variant_run_ids = [str(item) for item in (experiment_summary.get("expected_variant_run_ids") or []) if str(item)]
    coverage_html = ""
    if expected_variant_run_ids:
        coverage_html = (
            "<h3>Planned Variant Coverage</h3>"
            f"<p><strong>expected_variant_run_ids:</strong> {escape(', '.join(expected_variant_run_ids))}</p>"
            f"<p><strong>recorded_variant_run_ids:</strong> {escape(', '.join(str(item) for item in (experiment_summary.get('recorded_variant_run_ids') or [])) or '--')}</p>"
            f"<p><strong>compared_variant_run_ids:</strong> {escape(', '.join(str(item) for item in (experiment_summary.get('compared_variant_run_ids') or [])) or '--')}</p>"
        )
    registered_custom_variant_run_ids = [str(item) for item in (experiment_summary.get("registered_custom_variant_run_ids") or []) if str(item)]
    custom_coverage_html = ""
    if registered_custom_variant_run_ids:
        custom_coverage_html = (
            "<h3>Custom Variant Coverage</h3>"
            f"<p><strong>registered_custom_variant_run_ids:</strong> {escape(', '.join(registered_custom_variant_run_ids))}</p>"
            f"<p><strong>planned_custom_variant_run_ids:</strong> {escape(', '.join(str(item) for item in (experiment_summary.get('planned_custom_variant_run_ids') or [])) or '--')}</p>"
            f"<p><strong>completed_custom_variant_run_ids:</strong> {escape(', '.join(str(item) for item in (experiment_summary.get('completed_custom_variant_run_ids') or [])) or '--')}</p>"
            f"<p><strong>missing_custom_compare_entry_ids:</strong> {escape(', '.join(str(item) for item in (experiment_summary.get('missing_custom_compare_entry_ids') or [])) or '--')}</p>"
        )
    return (
        '<section class="panel">'
        "<h2>Experiment Registry</h2>"
        f"<p><strong>experiment_id:</strong> {escape(str(experiment_summary.get('experiment_id')))}</p>"
        f"<p><strong>experiment_status:</strong> {escape(str(experiment_summary.get('experiment_status')))}</p>"
        f"<p><strong>workflow_status:</strong> {escape(str(experiment_summary.get('workflow_status')))}</p>"
        f"<p><strong>baseline_run_id:</strong> {escape(str(experiment_summary.get('baseline_run_id')))}</p>"
        f"<p><strong>run_count:</strong> {escape(str(experiment_summary.get('run_count')))}</p>"
        f"<p><strong>compare_count:</strong> {escape(str(experiment_summary.get('compare_count')))}</p>"
        f"<p><strong>linkage_status:</strong> {escape(str(experiment_summary.get('linkage_status')))}</p>"
        f"<p><strong>linkage_issue_count:</strong> {escape(str(experiment_summary.get('linkage_issue_count')))}</p>"
        f"<p><strong>manifest:</strong> {escape(str(experiment_summary.get('manifest_virtual_path')))}</p>"
        f"{study_manifest_html}"
        f"{compare_html}"
        f"<p><strong>workflow_detail:</strong> {escape(str(experiment_summary.get('workflow_detail') or '--'))}</p>"
        f"{_render_html_items('Run Status Counts', _format_status_count_items(experiment_summary.get('run_status_counts')))}"
        f"{_render_html_items('Compare Status Counts', _format_status_count_items(experiment_summary.get('compare_status_counts')))}"
        f"{coverage_html}"
        f"{custom_coverage_html}"
        f"{_render_html_items('Missing Variant Run Records', _as_string_list(experiment_summary.get('missing_variant_run_record_ids')))}"
        f"{_render_html_items('Missing Compare Entries', _as_string_list(experiment_summary.get('missing_compare_entry_ids')))}"
        f"{_render_html_items('Planned Variant Runs', _as_string_list(experiment_summary.get('planned_variant_run_ids')))}"
        f"{_render_html_items('Blocked Variant Runs', _as_string_list(experiment_summary.get('blocked_variant_run_ids')))}"
        f"{_render_html_items('Missing Compare Metrics', _as_string_list(experiment_summary.get('missing_metrics_variant_run_ids')))}"
        "<h3>Compare Summary</h3>"
        f"<ul>{compare_items}</ul>"
        "<h3>Linkage Issues</h3>"
        f"<ul>{linkage_items}</ul>"
        "</section>"
    )


def _render_experiment_compare_html(experiment_compare_summary: dict | None) -> str:
    if not experiment_compare_summary:
        return ""

    items = (
        "".join(
            "<li>"
            f"<strong>{escape(str(item.get('candidate_run_id') or '--'))}</strong> "
            f"(<code>{escape(str(item.get('compare_status') or '--'))}</code>)"
            f"<p>{escape(_format_compare_entry_label(item))}</p>"
            f"<p><strong>compare_target:</strong> {escape(str(item.get('compare_target_run_id') or item.get('baseline_run_id') or '--'))}</p>"
            f"<p>{escape(' | '.join(_format_compare_metric_delta_lines(item.get('metric_deltas'))) or str(item.get('notes') or 'No metric delta'))}</p>"
            "</li>"
            for item in (experiment_compare_summary.get("comparisons") or [])
            if isinstance(item, dict)
        )
        or "<li>None</li>"
    )
    return (
        '<section class="panel">'
        "<h2>Experiment Compare</h2>"
        f"<p><strong>baseline_run_id:</strong> {escape(str(experiment_compare_summary.get('baseline_run_id') or '--'))}</p>"
        f"<p><strong>compare_count:</strong> {escape(str(experiment_compare_summary.get('compare_count') or 0))}</p>"
        f"<p><strong>workflow_status:</strong> {escape(str(experiment_compare_summary.get('workflow_status') or '--'))}</p>"
        f"<p><strong>compare:</strong> {escape(str(experiment_compare_summary.get('compare_virtual_path') or '--'))}</p>"
        f"{_render_html_items('Compare Status Counts', _format_status_count_items(experiment_compare_summary.get('compare_status_counts')))}"
        f"{_render_html_items('Planned Candidate Runs', _as_string_list(experiment_compare_summary.get('planned_candidate_run_ids')))}"
        f"{_render_html_items('Completed Candidate Runs', _as_string_list(experiment_compare_summary.get('completed_candidate_run_ids')))}"
        f"{_render_html_items('Blocked Candidate Runs', _as_string_list(experiment_compare_summary.get('blocked_candidate_run_ids')))}"
        f"{_render_html_items('Missing Compare Metrics', _as_string_list(experiment_compare_summary.get('missing_metrics_candidate_run_ids')))}"
        f"<ul>{items}</ul>"
        "</section>"
    )


def _render_research_evidence_html(research_evidence_summary: dict | None) -> str:
    if not research_evidence_summary:
        return ""

    passed_items = "".join(f"<li>{escape(str(item))}</li>" for item in (research_evidence_summary.get("passed_evidence") or [])) or "<li>None</li>"
    gap_items = "".join(f"<li>{escape(str(item))}</li>" for item in (research_evidence_summary.get("evidence_gaps") or [])) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Research Evidence</h2>"
        f"<p><strong>readiness_status:</strong> {escape(str(research_evidence_summary.get('readiness_status')))}</p>"
        f"<p><strong>verification_status:</strong> {escape(str(research_evidence_summary.get('verification_status')))}</p>"
        f"<p><strong>validation_status:</strong> {escape(str(research_evidence_summary.get('validation_status')))}</p>"
        f"<p><strong>provenance_status:</strong> {escape(str(research_evidence_summary.get('provenance_status')))}</p>"
        f"<p><strong>confidence:</strong> {escape(str(research_evidence_summary.get('confidence')))}</p>"
        "<h3>Passed Evidence</h3>"
        f"<ul>{passed_items}</ul>"
        "<h3>Evidence Gaps</h3>"
        f"<ul>{gap_items}</ul>"
        "</section>"
    )


def _render_reproducibility_html(reproducibility_summary: dict | None) -> str:
    if not reproducibility_summary:
        return ""

    drift_items = "".join(f"<li>{escape(str(item))}</li>" for item in (reproducibility_summary.get("drift_reasons") or [])) or "<li>None</li>"
    guidance_items = "".join(f"<li>{escape(str(item))}</li>" for item in (reproducibility_summary.get("recovery_guidance") or [])) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Reproducibility</h2>"
        f"<p><strong>manifest:</strong> {escape(str(reproducibility_summary.get('manifest_virtual_path') or '--'))}</p>"
        f"<p><strong>profile_id:</strong> {escape(str(reproducibility_summary.get('profile_id') or '--'))}</p>"
        f"<p><strong>parity_status:</strong> {escape(str(reproducibility_summary.get('parity_status') or '--'))}</p>"
        f"<p><strong>reproducibility_status:</strong> {escape(str(reproducibility_summary.get('reproducibility_status') or '--'))}</p>"
        "<h3>Drift Reasons</h3>"
        f"<ul>{drift_items}</ul>"
        "<h3>Recovery Guidance</h3>"
        f"<ul>{guidance_items}</ul>"
        "</section>"
    )


def _render_scientific_gate_html(scientific_supervisor_gate: dict | None) -> str:
    if not scientific_supervisor_gate:
        return ""

    artifact_items = "".join(f"<li>{escape(str(item))}</li>" for item in (scientific_supervisor_gate.get("artifact_virtual_paths") or [])) or "<li>None</li>"
    blocking_items = "".join(f"<li>{escape(str(item))}</li>" for item in (scientific_supervisor_gate.get("blocking_reasons") or [])) or "<li>None</li>"
    advisory_items = "".join(f"<li>{escape(str(item))}</li>" for item in (scientific_supervisor_gate.get("advisory_notes") or [])) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Scientific Supervisor Gate</h2>"
        f"<p><strong>gate_status:</strong> {escape(str(scientific_supervisor_gate.get('gate_status')))}</p>"
        f"<p><strong>allowed_claim_level:</strong> {escape(str(scientific_supervisor_gate.get('allowed_claim_level')))}</p>"
        f"<p><strong>source_readiness_status:</strong> {escape(str(scientific_supervisor_gate.get('source_readiness_status')))}</p>"
        f"<p><strong>recommended_stage:</strong> {escape(str(scientific_supervisor_gate.get('recommended_stage')))}</p>"
        f"<p><strong>remediation_stage:</strong> {escape(str(scientific_supervisor_gate.get('remediation_stage') or 'none'))}</p>"
        "<h3>Gate Artifacts</h3>"
        f"<ul>{artifact_items}</ul>"
        "<h3>Blocking Reasons</h3>"
        f"<ul>{blocking_items}</ul>"
        "<h3>Advisory Notes</h3>"
        f"<ul>{advisory_items}</ul>"
        "</section>"
    )


def _render_scientific_remediation_html(scientific_remediation_summary: dict | None) -> str:
    if not scientific_remediation_summary:
        return ""

    artifact_items = "".join(f"<li>{escape(str(item))}</li>" for item in (scientific_remediation_summary.get("artifact_virtual_paths") or [])) or "<li>None</li>"
    action_items = (
        "".join(
            "<li>"
            f"<strong>{escape(str(item.get('action_id') or '--'))}</strong> "
            f"(<code>{escape(str(item.get('owner_stage') or '--'))}</code> / <code>{escape(str(item.get('execution_mode') or '--'))}</code>)"
            f"<p>{escape(str(item.get('evidence_gap') or 'No evidence gap'))}</p>"
            "</li>"
            for item in (scientific_remediation_summary.get("actions") or [])
            if isinstance(item, dict)
        )
        or "<li>None</li>"
    )
    return (
        '<section class="panel">'
        "<h2>Scientific Remediation Plan</h2>"
        f"<p><strong>plan_status:</strong> {escape(str(scientific_remediation_summary.get('plan_status') or '--'))}</p>"
        f"<p><strong>current_claim_level:</strong> {escape(str(scientific_remediation_summary.get('current_claim_level') or '--'))}</p>"
        f"<p><strong>target_claim_level:</strong> {escape(str(scientific_remediation_summary.get('target_claim_level') or '--'))}</p>"
        f"<p><strong>recommended_stage:</strong> {escape(str(scientific_remediation_summary.get('recommended_stage') or '--'))}</p>"
        "<h3>Remediation Artifacts</h3>"
        f"<ul>{artifact_items}</ul>"
        "<h3>Remediation Actions</h3>"
        f"<ul>{action_items}</ul>"
        "</section>"
    )


def _render_scientific_remediation_handoff_html(
    scientific_remediation_handoff: dict | None,
) -> str:
    if not scientific_remediation_handoff:
        return ""

    artifact_items = "".join(f"<li>{escape(str(item))}</li>" for item in (scientific_remediation_handoff.get("artifact_virtual_paths") or [])) or "<li>None</li>"
    tool_args = scientific_remediation_handoff.get("tool_args") or {}
    tool_arg_items = "".join(f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>" for key, value in tool_args.items()) or "<li>None</li>"
    manual_action_items = (
        "".join(
            f"<li><strong>{escape(str(item.get('action_id') or '--'))}</strong> (<code>{escape(str(item.get('owner_stage') or '--'))}</code>)<p>{escape(str(item.get('evidence_gap') or 'Manual follow-up required'))}</p></li>"
            for item in (scientific_remediation_handoff.get("manual_actions") or [])
            if isinstance(item, dict)
        )
        or "<li>None</li>"
    )
    return (
        '<section class="panel">'
        "<h2>Scientific Remediation Handoff</h2>"
        f"<p><strong>handoff_status:</strong> {escape(str(scientific_remediation_handoff.get('handoff_status') or '--'))}</p>"
        f"<p><strong>recommended_action_id:</strong> {escape(str(scientific_remediation_handoff.get('recommended_action_id') or 'none'))}</p>"
        f"<p><strong>tool_name:</strong> {escape(str(scientific_remediation_handoff.get('tool_name') or 'manual_only'))}</p>"
        f"<p><strong>reason:</strong> {escape(str(scientific_remediation_handoff.get('reason') or 'No detail'))}</p>"
        "<h3>Handoff Artifacts</h3>"
        f"<ul>{artifact_items}</ul>"
        "<h3>Suggested Tool Args</h3>"
        f"<ul>{tool_arg_items}</ul>"
        "<h3>Manual Actions</h3>"
        f"<ul>{manual_action_items}</ul>"
        "</section>"
    )


def _render_scientific_verification_html(
    scientific_verification_assessment: dict | None,
) -> str:
    if not scientific_verification_assessment:
        return ""

    def render_items(items: list[str]) -> str:
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{escape(item)}</li>" for item in items)

    requirement_items = (
        "".join(
            f"<li><strong>{escape(str(item.get('label') or item.get('requirement_id')))}</strong> (<code>{escape(str(item.get('status')))}</code>)<p>{escape(str(item.get('detail') or 'No detail'))}</p></li>"
            for item in (scientific_verification_assessment.get("requirements") or [])
        )
        or "<li>None</li>"
    )

    return (
        '<section class="panel">'
        "<h2>Scientific Verification</h2>"
        f"<p><strong>status:</strong> {escape(str(scientific_verification_assessment.get('status')))}</p>"
        f"<p><strong>confidence:</strong> {escape(str(scientific_verification_assessment.get('confidence')))}</p>"
        f"<p><strong>requirement_count:</strong> {escape(str(scientific_verification_assessment.get('requirement_count')))}</p>"
        "<h3>Verification Requirements</h3>"
        f"<ul>{requirement_items}</ul>"
        "<h3>Missing Evidence</h3>"
        f"<ul>{render_items(scientific_verification_assessment.get('missing_evidence') or [])}</ul>"
        "<h3>Blocking Issues</h3>"
        f"<ul>{render_items(scientific_verification_assessment.get('blocking_issues') or [])}</ul>"
        "<h3>Passed Requirements</h3>"
        f"<ul>{render_items(scientific_verification_assessment.get('passed_requirements') or [])}</ul>"
        "</section>"
    )


def _render_solver_metrics_markdown(solver_metrics: dict | None) -> list[str]:
    if not solver_metrics:
        return []

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    lines = [
        "",
        "## CFD 结果指标",
        f"- 求解完成: `{solver_metrics.get('solver_completed')}`",
        f"- 最终时间步: `{solver_metrics.get('final_time_seconds')}`",
        f"- 后处理目录: `{solver_metrics.get('workspace_postprocess_virtual_path')}`",
    ]
    if coefficient_metrics:
        lines.extend(
            [
                f"- Cd: `{coefficient_metrics.get('Cd')}`",
                f"- Cl: `{coefficient_metrics.get('Cl')}`",
                f"- Cs: `{coefficient_metrics.get('Cs')}`",
                f"- CmPitch: `{coefficient_metrics.get('CmPitch')}`",
            ]
        )
    if force_metrics:
        lines.extend(
            [
                f"- 总阻力向量 (N): `{force_metrics.get('total_force')}`",
                f"- 总力矩向量 (N·m): `{force_metrics.get('total_moment')}`",
            ]
        )
    if reference_values:
        lines.extend(
            [
                "",
                "## 参考量",
                f"- 参考长度: `{reference_values.get('reference_length_m')}` m",
                f"- 参考面积: `{reference_values.get('reference_area_m2')}` m^2",
                f"- 来流速度: `{reference_values.get('inlet_velocity_mps')}` m/s",
                f"- 流体密度: `{reference_values.get('fluid_density_kg_m3')}` kg/m^3",
            ]
        )
    return lines


def _render_solver_metrics_markdown_enriched(solver_metrics: dict | None) -> list[str]:
    if not solver_metrics:
        return []

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    simulation_requirements = solver_metrics.get("simulation_requirements") or {}
    mesh_summary = solver_metrics.get("mesh_summary") or {}
    residual_summary = solver_metrics.get("residual_summary") or {}

    lines = [
        "",
        "## CFD 结果指标",
        f"- 求解完成: `{solver_metrics.get('solver_completed')}`",
        f"- 最终时间步: `{solver_metrics.get('final_time_seconds')}`",
        f"- 后处理目录: `{solver_metrics.get('workspace_postprocess_virtual_path')}`",
    ]
    if coefficient_metrics:
        lines.extend(
            [
                f"- Cd: `{coefficient_metrics.get('Cd')}`",
                f"- Cl: `{coefficient_metrics.get('Cl')}`",
                f"- Cs: `{coefficient_metrics.get('Cs')}`",
                f"- CmPitch: `{coefficient_metrics.get('CmPitch')}`",
            ]
        )
    if force_metrics:
        lines.extend(
            [
                f"- 总阻力向量(N): `{force_metrics.get('total_force')}`",
                f"- 总力矩向量(N·m): `{force_metrics.get('total_moment')}`",
            ]
        )
    if reference_values:
        lines.extend(
            [
                "",
                "## 参考量",
                f"- 参考长度: `{reference_values.get('reference_length_m')}` m",
                f"- 参考面积: `{reference_values.get('reference_area_m2')}` m^2",
                f"- 来流速度: `{reference_values.get('inlet_velocity_mps')}` m/s",
                f"- 流体密度: `{reference_values.get('fluid_density_kg_m3')}` kg/m^3",
            ]
        )
    if simulation_requirements:
        lines.extend(
            [
                "",
                "## 计算要求",
                f"- inlet_velocity_mps: `{simulation_requirements.get('inlet_velocity_mps')}`",
                f"- fluid_density_kg_m3: `{simulation_requirements.get('fluid_density_kg_m3')}`",
                f"- kinematic_viscosity_m2ps: `{simulation_requirements.get('kinematic_viscosity_m2ps')}`",
                f"- end_time_seconds: `{simulation_requirements.get('end_time_seconds')}`",
                f"- delta_t_seconds: `{simulation_requirements.get('delta_t_seconds')}`",
                f"- write_interval_steps: `{simulation_requirements.get('write_interval_steps')}`",
            ]
        )
    if mesh_summary:
        lines.extend(
            [
                "",
                "## 网格质量摘要",
                f"- Mesh OK: `{mesh_summary.get('mesh_ok')}`",
                f"- cells: `{mesh_summary.get('cells')}`",
                f"- faces: `{mesh_summary.get('faces')}`",
                f"- internal faces: `{mesh_summary.get('internal_faces')}`",
                f"- points: `{mesh_summary.get('points')}`",
            ]
        )
    if residual_summary:
        lines.extend(
            [
                "",
                "## 残差收敛摘要",
                f"- 字段数: `{residual_summary.get('field_count')}`",
                f"- 最新时间: `{residual_summary.get('latest_time')}`",
                f"- 最大最终残差: `{residual_summary.get('max_final_residual')}`",
            ]
        )
        latest_by_field = residual_summary.get("latest_by_field") or {}
        for field_name, entry in latest_by_field.items():
            lines.append(f"- {field_name}: initial `{entry.get('initial_residual')}`, final `{entry.get('final_residual')}`, iterations `{entry.get('iterations')}`")
    return lines


def _format_spec_number(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "--"
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


def _summarize_postprocess_spec(spec: object) -> str | None:
    if not isinstance(spec, dict):
        return None

    parts: list[str] = []
    field = spec.get("field")
    if isinstance(field, str) and field:
        parts.append(f"field={field}")

    selector = spec.get("selector")
    if isinstance(selector, dict):
        selector_type = selector.get("type")
        if selector_type == "patch":
            patches = selector.get("patches")
            patch_names = [str(item) for item in patches if isinstance(item, str) and item] if isinstance(patches, list) else []
            parts.append(f"selector=patch[{','.join(patch_names)}]" if patch_names else "selector=patch")
        elif selector_type == "plane":
            origin_mode = selector.get("origin_mode")
            origin_value = selector.get("origin_value")
            if origin_mode == "x_by_lref" and isinstance(origin_value, (int, float)):
                origin_summary = f"x/Lref={_format_spec_number(origin_value)}"
            elif origin_mode == "x_absolute_m" and isinstance(origin_value, (int, float)):
                origin_summary = f"x={_format_spec_number(origin_value)}m"
            elif isinstance(origin_value, (int, float)):
                origin_summary = f"origin={_format_spec_number(origin_value)}"
            else:
                origin_summary = "origin=--"

            normal = selector.get("normal")
            normal_summary = ""
            if isinstance(normal, list) and len(normal) == 3 and all(isinstance(item, (int, float)) for item in normal):
                normal_summary = "; normal=(" + ", ".join(_format_spec_number(item) for item in normal) + ")"
            parts.append(f"selector=plane[{origin_summary}{normal_summary}]")

    time_mode = spec.get("time_mode")
    if isinstance(time_mode, str) and time_mode:
        parts.append(f"time={time_mode}")

    formats = spec.get("formats")
    if isinstance(formats, list):
        format_names = [str(item) for item in formats if isinstance(item, str) and item]
        if format_names:
            parts.append(f"formats={','.join(format_names)}")

    return "; ".join(parts) if parts else None


_REPORT_RECOMMENDATIONS: tuple[str, ...] = (
    "由 Claude Code Supervisor 审阅当前阶段结论，再决定是否进入下一次 DeerFlow run。",
    "若当前仅完成几何预检，请在继续前补全工况、案例和求解参数确认。",
    "若当前已完成求解派发或执行，请继续补齐结果整理与后处理展示。",
)


def _build_dynamic_report_recommendations(payload: dict) -> list[str]:
    review_status = str(payload.get("review_status") or "").strip()
    next_stage = str(payload.get("next_recommended_stage") or "").strip()
    recommendations: list[str] = []
    if review_status == "blocked" and next_stage:
        recommendations.append(f"回到 `{next_stage}` 补齐验证或整改项后，再刷新最终报告。")
    if review_status == "ready_for_supervisor" and next_stage == "supervisor-review":
        recommendations.append("进入 `supervisor-review` 审阅当前 claim level，并确认是否需要执行手动整改项。")
    return recommendations


def _legacy_render_markdown_v1(payload: dict) -> str:
    source_artifacts = "\n".join(f"- `{path}`" for path in payload["source_artifact_virtual_paths"]) or "- 暂无"
    final_artifacts = "\n".join(f"- `{path}`" for path in payload["final_artifact_virtual_paths"])
    requested_outputs = (
        "\n".join(
            (
                f"- `{item['output_id']}` | {item['label']} | "
                f"requested=`{item['requested_label']}` | support=`{item['support_level']}`" + (f" | spec=`{_summarize_postprocess_spec(item.get('postprocess_spec'))}`" if _summarize_postprocess_spec(item.get("postprocess_spec")) else "")
            )
            for item in payload.get("requested_outputs") or []
        )
        or "- 暂无"
    )
    lines = [
        f"# {payload['report_title']}",
        "",
        "## 中文摘要",
        payload["summary_zh"],
        "",
        "## 运行上下文",
        f"- 来源阶段: `{payload['source_runtime_stage']}`",
        f"- 任务摘要: `{payload.get('task_summary') or '待补充'}`",
        f"- 确认状态: `{payload.get('confirmation_status') or 'draft'}`",
        f"- 执行偏好: `{payload.get('execution_preference') or 'plan_only'}`",
        f"- 任务类型: `{payload['task_type']}`",
        f"- 输入来源: `{payload.get('input_source_type') or 'geometry_seed'}`",
        f"- 几何文件: `{payload['geometry_virtual_path']}`",
        f"- 官方案例: `{payload.get('official_case_id') or '未提供'}`",
        f"- 几何家族: `{payload.get('geometry_family') or '待确认'}`",
        f"- 执行就绪状态: `{payload.get('execution_readiness') or '待判定'}`",
        f"- 选定案例: `{payload.get('selected_case_id') or '未固定'}`",
        f"- Workspace case: `{payload.get('workspace_case_dir_virtual_path') or '当前阶段无'}`",
        f"- Run script: `{payload.get('run_script_virtual_path') or '当前阶段无'}`",
        "",
        "## 当前阶段判断",
        f"- review_status: `{payload['review_status']}`",
        f"- next_recommended_stage: `{payload['next_recommended_stage']}`",
        f"- source_report_virtual_path: `{payload['source_report_virtual_path']}`",
        (f"- supervisor_handoff_virtual_path: `{payload.get('supervisor_handoff_virtual_path') or '当前阶段无'}`"),
        "",
        "## 来源证据",
        source_artifacts,
    ]
    dynamic_recommendations = _build_dynamic_report_recommendations(payload)
    if dynamic_recommendations:
        lines.extend(
            [
                "",
                "### 行动提示",
                *(f"- {item}" for item in dynamic_recommendations),
            ]
        )
    lines.extend(
        [
            "",
            "## Requested Outputs",
            requested_outputs,
        ]
    )
    lines.extend(_render_solver_metrics_markdown_enriched(payload.get("solver_metrics")))
    lines.extend(_render_acceptance_markdown(payload.get("acceptance_assessment")))
    lines.extend(_render_experiment_markdown(payload.get("experiment_summary")))
    lines.extend(_render_research_evidence_markdown(payload.get("research_evidence_summary")))
    lines.extend(_render_reproducibility_markdown(payload.get("reproducibility_summary")))
    lines.extend(_render_scientific_gate_markdown(payload.get("scientific_supervisor_gate")))
    lines.extend(_render_scientific_remediation_markdown(payload.get("scientific_remediation_summary")))
    lines.extend(_render_scientific_remediation_handoff_markdown(payload.get("scientific_remediation_handoff")))
    lines.extend(_render_scientific_followup_markdown(payload.get("scientific_followup_summary")))
    lines.extend(_render_scientific_study_markdown(payload.get("scientific_study_summary")))
    lines.extend(_render_experiment_compare_markdown(payload.get("experiment_compare_summary")))
    lines.extend(_render_figure_delivery_markdown(payload.get("figure_delivery_summary")))
    lines.extend(_render_scientific_verification_markdown(payload.get("scientific_verification_assessment")))
    lines.extend(_render_output_delivery_markdown(payload.get("output_delivery_plan")))
    lines.extend(
        [
            "",
            "## 本阶段产物",
            final_artifacts,
            "",
            "## 建议",
            "- 由 Claude Code Supervisor 审阅当前阶段结论，再决定是否进入下一次 DeerFlow run。",
            "- 若当前仅完成几何预检，请在继续前补全工况、案例和求解参数确认。",
            "- 若当前已完成求解派发或执行，请继续补齐结果整理与后处理展示。",
            "",
        ]
    )
    return "\n".join(lines)


def _render_solver_metrics_html(solver_metrics: dict | None) -> str:
    if not solver_metrics:
        return ""

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    metric_lines = [
        f"<p><strong>求解完成:</strong> {escape(str(solver_metrics.get('solver_completed')))}</p>",
        f"<p><strong>最终时间步:</strong> {escape(str(solver_metrics.get('final_time_seconds')))}</p>",
        (f"<p><strong>后处理目录:</strong> {escape(str(solver_metrics.get('workspace_postprocess_virtual_path')))}</p>"),
    ]
    if coefficient_metrics:
        metric_lines.extend(
            [
                f"<p><strong>Cd:</strong> {escape(str(coefficient_metrics.get('Cd')))}</p>",
                f"<p><strong>Cl:</strong> {escape(str(coefficient_metrics.get('Cl')))}</p>",
                f"<p><strong>Cs:</strong> {escape(str(coefficient_metrics.get('Cs')))}</p>",
                f"<p><strong>CmPitch:</strong> {escape(str(coefficient_metrics.get('CmPitch')))}</p>",
            ]
        )
    if force_metrics:
        metric_lines.extend(
            [
                f"<p><strong>总阻力向量 (N):</strong> {escape(str(force_metrics.get('total_force')))}</p>",
                f"<p><strong>总力矩向量 (N·m):</strong> {escape(str(force_metrics.get('total_moment')))}</p>",
            ]
        )
    if reference_values:
        metric_lines.extend(
            [
                f"<p><strong>参考长度:</strong> {escape(str(reference_values.get('reference_length_m')))} m</p>",
                f"<p><strong>参考面积:</strong> {escape(str(reference_values.get('reference_area_m2')))} m^2</p>",
                f"<p><strong>来流速度:</strong> {escape(str(reference_values.get('inlet_velocity_mps')))} m/s</p>",
                f"<p><strong>流体密度:</strong> {escape(str(reference_values.get('fluid_density_kg_m3')))} kg/m^3</p>",
            ]
        )

    return '<section class="panel"><h2>CFD 结果指标</h2>' + "".join(metric_lines) + "</section>"


def _render_solver_metrics_html_enriched(solver_metrics: dict | None) -> str:
    if not solver_metrics:
        return ""

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    simulation_requirements = solver_metrics.get("simulation_requirements") or {}
    mesh_summary = solver_metrics.get("mesh_summary") or {}
    residual_summary = solver_metrics.get("residual_summary") or {}
    metric_lines = [
        f"<p><strong>求解完成:</strong> {escape(str(solver_metrics.get('solver_completed')))}</p>",
        f"<p><strong>最终时间步:</strong> {escape(str(solver_metrics.get('final_time_seconds')))}</p>",
        (f"<p><strong>后处理目录:</strong> {escape(str(solver_metrics.get('workspace_postprocess_virtual_path')))}</p>"),
    ]
    if coefficient_metrics:
        metric_lines.extend(
            [
                f"<p><strong>Cd:</strong> {escape(str(coefficient_metrics.get('Cd')))}</p>",
                f"<p><strong>Cl:</strong> {escape(str(coefficient_metrics.get('Cl')))}</p>",
                f"<p><strong>Cs:</strong> {escape(str(coefficient_metrics.get('Cs')))}</p>",
                f"<p><strong>CmPitch:</strong> {escape(str(coefficient_metrics.get('CmPitch')))}</p>",
            ]
        )
    if force_metrics:
        metric_lines.extend(
            [
                f"<p><strong>总阻力向量(N):</strong> {escape(str(force_metrics.get('total_force')))}</p>",
                f"<p><strong>总力矩向量(N·m):</strong> {escape(str(force_metrics.get('total_moment')))}</p>",
            ]
        )
    if reference_values:
        metric_lines.extend(
            [
                f"<p><strong>参考长度:</strong> {escape(str(reference_values.get('reference_length_m')))} m</p>",
                f"<p><strong>参考面积:</strong> {escape(str(reference_values.get('reference_area_m2')))} m^2</p>",
                f"<p><strong>来流速度:</strong> {escape(str(reference_values.get('inlet_velocity_mps')))} m/s</p>",
                f"<p><strong>流体密度:</strong> {escape(str(reference_values.get('fluid_density_kg_m3')))} kg/m^3</p>",
            ]
        )
    if simulation_requirements:
        metric_lines.extend(
            [
                "<h3>计算要求</h3>",
                f"<p><strong>inlet_velocity_mps:</strong> {escape(str(simulation_requirements.get('inlet_velocity_mps')))}</p>",
                f"<p><strong>fluid_density_kg_m3:</strong> {escape(str(simulation_requirements.get('fluid_density_kg_m3')))}</p>",
                f"<p><strong>kinematic_viscosity_m2ps:</strong> {escape(str(simulation_requirements.get('kinematic_viscosity_m2ps')))}</p>",
                f"<p><strong>end_time_seconds:</strong> {escape(str(simulation_requirements.get('end_time_seconds')))}</p>",
                f"<p><strong>delta_t_seconds:</strong> {escape(str(simulation_requirements.get('delta_t_seconds')))}</p>",
                f"<p><strong>write_interval_steps:</strong> {escape(str(simulation_requirements.get('write_interval_steps')))}</p>",
            ]
        )
    if mesh_summary:
        metric_lines.extend(
            [
                "<h3>网格质量摘要</h3>",
                f"<p><strong>Mesh OK:</strong> {escape(str(mesh_summary.get('mesh_ok')))}</p>",
                f"<p><strong>cells:</strong> {escape(str(mesh_summary.get('cells')))}</p>",
                f"<p><strong>faces:</strong> {escape(str(mesh_summary.get('faces')))}</p>",
                f"<p><strong>internal faces:</strong> {escape(str(mesh_summary.get('internal_faces')))}</p>",
                f"<p><strong>points:</strong> {escape(str(mesh_summary.get('points')))}</p>",
            ]
        )
    if residual_summary:
        metric_lines.extend(
            [
                "<h3>残差收敛摘要</h3>",
                f"<p><strong>字段数:</strong> {escape(str(residual_summary.get('field_count')))}</p>",
                f"<p><strong>最新时间:</strong> {escape(str(residual_summary.get('latest_time')))}</p>",
                f"<p><strong>最大最终残差:</strong> {escape(str(residual_summary.get('max_final_residual')))}</p>",
            ]
        )
        latest_by_field = residual_summary.get("latest_by_field") or {}
        for field_name, entry in latest_by_field.items():
            metric_lines.append(f"<p><strong>{escape(str(field_name))}:</strong> initial {escape(str(entry.get('initial_residual')))}, final {escape(str(entry.get('final_residual')))}, iterations {escape(str(entry.get('iterations')))}</p>")

    return '<section class="panel"><h2>CFD 结果指标</h2>' + "".join(metric_lines) + "</section>"


def _render_scientific_followup_html(scientific_followup_summary: dict | None) -> str:
    if not scientific_followup_summary:
        return ""

    artifact_items = "".join(f"<li><code>{escape(str(path))}</code></li>" for path in (scientific_followup_summary.get("artifact_virtual_paths") or [])) or "<li>None</li>"
    note_items = "".join(f"<li>{escape(str(note))}</li>" for note in (scientific_followup_summary.get("latest_notes") or [])) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Scientific Follow-Up History</h2>"
        f"<p><strong>entry_count:</strong> {escape(str(scientific_followup_summary.get('entry_count') or 0))}</p>"
        f"<p><strong>latest_outcome_status:</strong> {escape(str(scientific_followup_summary.get('latest_outcome_status') or '--'))}</p>"
        f"<p><strong>latest_handoff_status:</strong> {escape(str(scientific_followup_summary.get('latest_handoff_status') or '--'))}</p>"
        f"<p><strong>latest_recommended_action_id:</strong> {escape(str(scientific_followup_summary.get('latest_recommended_action_id') or 'none'))}</p>"
        f"<p><strong>latest_tool_name:</strong> {escape(str(scientific_followup_summary.get('latest_tool_name') or 'none'))}</p>"
        f"<p><strong>latest_dispatch_stage_status:</strong> {escape(str(scientific_followup_summary.get('latest_dispatch_stage_status') or 'none'))}</p>"
        f"<p><strong>report_refreshed:</strong> {escape(str(scientific_followup_summary.get('report_refreshed')))}</p>"
        f"<p><strong>history:</strong> {escape(str(scientific_followup_summary.get('history_virtual_path') or '--'))}</p>"
        + (f"<p><strong>latest_result_report:</strong> {escape(str(scientific_followup_summary.get('latest_result_report_virtual_path')))}</p>" if scientific_followup_summary.get("latest_result_report_virtual_path") else "")
        + (
            f"<p><strong>latest_result_handoff:</strong> {escape(str(scientific_followup_summary.get('latest_result_supervisor_handoff_virtual_path')))}</p>"
            if scientific_followup_summary.get("latest_result_supervisor_handoff_virtual_path")
            else ""
        )
        + "<h3>Latest Notes</h3>"
        + f"<ul>{note_items}</ul>"
        + "<h3>Follow-Up Artifacts</h3>"
        + f"<ul>{artifact_items}</ul>"
        + "</section>"
    )


def _render_recommendations_html(payload: dict) -> str:
    dynamic_recommendations = [item.replace("`", "<code>", 1).replace("`", "</code>", 1) for item in _build_dynamic_report_recommendations(payload)]
    items = "".join(f"<li>{item}</li>" for item in dynamic_recommendations) + "".join(f"<li>{escape(item)}</li>" for item in _REPORT_RECOMMENDATIONS)
    return f'<section class="panel"><h2>建议</h2><ul>{items}</ul></section>'


def _legacy_render_html_v1(payload: dict) -> str:
    source_items = "".join(f"<li>{escape(path)}</li>" for path in payload["source_artifact_virtual_paths"]) or "<li>暂无</li>"
    final_items = "".join(f"<li>{escape(path)}</li>" for path in payload["final_artifact_virtual_paths"])
    metrics_section = _render_solver_metrics_html_enriched(payload.get("solver_metrics"))
    acceptance_section = _render_acceptance_html(payload.get("acceptance_assessment"))
    experiment_section = _render_experiment_html(payload.get("experiment_summary"))
    research_evidence_section = _render_research_evidence_html(payload.get("research_evidence_summary"))
    reproducibility_section = _render_reproducibility_html(payload.get("reproducibility_summary"))
    scientific_gate_section = _render_scientific_gate_html(payload.get("scientific_supervisor_gate"))
    scientific_remediation_section = _render_scientific_remediation_html(payload.get("scientific_remediation_summary"))
    scientific_remediation_handoff_section = _render_scientific_remediation_handoff_html(payload.get("scientific_remediation_handoff"))
    scientific_followup_section = _render_scientific_followup_html(payload.get("scientific_followup_summary"))
    scientific_study_section = _render_scientific_study_html(payload.get("scientific_study_summary"))
    experiment_compare_section = _render_experiment_compare_html(payload.get("experiment_compare_summary"))
    figure_delivery_section = _render_figure_delivery_html(payload.get("figure_delivery_summary"))
    scientific_verification_section = _render_scientific_verification_html(payload.get("scientific_verification_assessment"))
    requested_outputs_section = (
        '<section class="panel"><h2>Requested Outputs</h2><ul>'
        + (
            "".join(
                "<li>"
                f"<strong>{escape(str(item.get('label')))}</strong> "
                f"(<code>{escape(str(item.get('output_id')))}</code>)"
                f"<p>requested={escape(str(item.get('requested_label')))}, "
                f"support={escape(str(item.get('support_level')))}" + (f", spec={escape(summary)}" if (summary := _summarize_postprocess_spec(item.get("postprocess_spec"))) else "") + "</p>"
                "</li>"
                for item in (payload.get("requested_outputs") or [])
            )
            or "<li>暂无</li>"
        )
        + "</ul></section>"
    )
    output_delivery_section = _render_output_delivery_html(payload.get("output_delivery_plan"))
    recommendations_section = _render_recommendations_html(payload)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(payload["report_title"])}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: #f7f8fa;
        color: #111827;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}
      h1, h2 {{ margin: 0 0 12px; }}
      p {{ line-height: 1.7; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li {{ margin-bottom: 8px; }}
      strong {{ color: #0f172a; }}
    </style>
  </head>
  <body>
    <section class="panel">
      <h1>{escape(payload["report_title"])}</h1>
      <p>{escape(payload["summary_zh"])}</p>
    </section>
    <section class="panel">
      <h2>运行上下文</h2>
      <p><strong>来源阶段:</strong> {escape(str(payload["source_runtime_stage"]))}</p>
      <p><strong>任务摘要:</strong> {escape(str(payload.get("task_summary") or "待补充"))}</p>
      <p><strong>确认状态:</strong> {escape(str(payload.get("confirmation_status") or "draft"))}</p>
      <p><strong>执行偏好:</strong> {escape(str(payload.get("execution_preference") or "plan_only"))}</p>
      <p><strong>任务类型:</strong> {escape(str(payload["task_type"]))}</p>
      <p><strong>输入来源:</strong> {escape(str(payload.get("input_source_type") or "geometry_seed"))}</p>
      <p><strong>几何文件:</strong> {escape(str(payload["geometry_virtual_path"]))}</p>
      <p><strong>官方案例:</strong> {escape(str(payload.get("official_case_id") or "未提供"))}</p>
      <p><strong>几何家族:</strong> {escape(str(payload.get("geometry_family") or "待确认"))}</p>
      <p><strong>执行就绪状态:</strong> {escape(str(payload.get("execution_readiness") or "待判定"))}</p>
      <p><strong>选定案例:</strong> {escape(str(payload.get("selected_case_id") or "未固定"))}</p>
      <p><strong>Workspace case:</strong> {escape(str(payload.get("workspace_case_dir_virtual_path") or "当前阶段无"))}</p>
      <p><strong>Run script:</strong> {escape(str(payload.get("run_script_virtual_path") or "当前阶段无"))}</p>
    </section>
    <section class="panel">
      <h2>当前阶段判断</h2>
      <p><strong>review_status:</strong> {escape(str(payload["review_status"]))}</p>
      <p><strong>next_recommended_stage:</strong> {escape(str(payload["next_recommended_stage"]))}</p>
      <p><strong>source_report_virtual_path:</strong> {escape(str(payload["source_report_virtual_path"]))}</p>
      <p><strong>supervisor_handoff_virtual_path:</strong> {escape(str(payload.get("supervisor_handoff_virtual_path") or "当前阶段无"))}</p>
    </section>
    <section class="panel">
      <h2>来源证据</h2>
      <ul>{source_items}</ul>
    </section>
    {requested_outputs_section}
    {metrics_section}
    {acceptance_section}
    {experiment_section}
    {research_evidence_section}
    {reproducibility_section}
    {scientific_gate_section}
    {scientific_remediation_section}
      {scientific_remediation_handoff_section}
      {scientific_followup_section}
      {scientific_study_section}
      {experiment_compare_section}
      {figure_delivery_section}
      {scientific_verification_section}
    {output_delivery_section}
    <section class="panel">
      <h2>本阶段产物</h2>
      <ul>{final_items}</ul>
    </section>
    {recommendations_section}
  </body>
</html>
"""


def _report_text(value: object, fallback: str = "--") -> str:
    text = str(value or "").strip()
    return text or fallback


def _report_string_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    deduped: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in deduped:
            deduped.append(text)
    return deduped


def _report_overview(payload: dict) -> dict[str, object]:
    overview = payload.get("report_overview")
    if isinstance(overview, dict):
        return overview

    reproducibility_summary = payload.get("reproducibility_summary")
    reproducibility_status = "--"
    if isinstance(reproducibility_summary, dict):
        reproducibility_status = _report_text(
            reproducibility_summary.get("reproducibility_status") or reproducibility_summary.get("parity_status"),
            fallback="unknown",
        )

    next_stage = _report_text(payload.get("next_recommended_stage"), fallback="")
    recommended_next_step = f"建议先进入 `{next_stage}` 阶段继续补齐证据链。" if next_stage else "回到聊天确认下一步研究动作。"
    return {
        "current_conclusion_zh": _report_text(
            payload.get("summary_zh"),
            fallback="当前暂无可交付结论摘要。",
        ),
        "allowed_claim_level": _report_text(
            payload.get("allowed_claim_level"),
            fallback="delivery_only",
        ),
        "review_status": _report_text(
            payload.get("review_status"),
            fallback="ready_for_supervisor",
        ),
        "reproducibility_status": reproducibility_status,
        "recommended_next_step_zh": recommended_next_step,
    }


def _delivery_highlights(payload: dict) -> dict[str, object]:
    highlights = payload.get("delivery_highlights")
    if isinstance(highlights, dict):
        return highlights

    solver_metrics = payload.get("solver_metrics") or {}
    overview = _report_overview(payload)
    figure_delivery_summary = payload.get("figure_delivery_summary") or {}
    metric_lines: list[str] = []

    if isinstance(solver_metrics, dict):
        coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
        if isinstance(coefficient_metrics, dict) and _is_number(coefficient_metrics.get("Cd")):
            metric_lines.append(f"阻力系数 Cd：{float(coefficient_metrics['Cd']):.6f}")

        if _is_number(solver_metrics.get("final_time_seconds")):
            metric_lines.append(f"最终时间步：{float(solver_metrics['final_time_seconds']):g} s")

        forces = solver_metrics.get("latest_forces") or {}
        total_force = forces.get("total_force") if isinstance(forces, dict) else None
        if isinstance(total_force, list) and total_force and _is_number(total_force[0]):
            metric_lines.append(f"总阻力 Fx：{float(total_force[0]):.4f} N")

    metric_lines.append("允许结论等级：" + _report_text(overview.get("allowed_claim_level"), fallback="delivery_only"))
    metric_lines.append("复核状态：" + _report_text(overview.get("review_status"), fallback="blocked"))
    metric_lines.append("可复现状态：" + _report_text(overview.get("reproducibility_status"), fallback="unknown"))

    figure_titles: list[str] = []
    if isinstance(figure_delivery_summary, dict):
        for item in figure_delivery_summary.get("figures") or []:
            if not isinstance(item, dict):
                continue
            figure_title = _report_text(
                item.get("title") or item.get("output_id"),
                fallback="",
            )
            if figure_title and figure_title not in figure_titles:
                figure_titles.append(figure_title)

    highlight_artifact_virtual_paths = _report_string_list(
        [
            payload.get("source_report_virtual_path"),
            payload.get("provenance_manifest_virtual_path"),
            payload.get("scientific_gate_virtual_path"),
            *(_report_string_list(payload.get("final_artifact_virtual_paths"))),
            *(_report_string_list(payload.get("source_artifact_virtual_paths"))),
        ]
    )[:8]

    return {
        "metric_lines": metric_lines,
        "figure_titles": figure_titles,
        "highlight_artifact_virtual_paths": highlight_artifact_virtual_paths,
    }


def _conclusion_sections(payload: dict) -> list[dict[str, object]]:
    sections = payload.get("conclusion_sections")
    if isinstance(sections, list):
        normalized: list[dict[str, object]] = []
        for item in sections:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "conclusion_id": _report_text(item.get("conclusion_id"), fallback="conclusion"),
                    "title_zh": _report_text(item.get("title_zh"), fallback="当前结论"),
                    "summary_zh": _report_text(item.get("summary_zh"), fallback="暂无结论说明。"),
                    "claim_level": _report_text(item.get("claim_level"), fallback="delivery_only"),
                    "confidence_label": _report_text(item.get("confidence_label"), fallback="--"),
                    "inline_source_refs": _report_string_list(item.get("inline_source_refs")),
                    "evidence_gap_notes": _report_string_list(item.get("evidence_gap_notes")),
                    "artifact_virtual_paths": _report_string_list(item.get("artifact_virtual_paths")),
                }
            )
        if normalized:
            return normalized

    overview = _report_overview(payload)
    research_summary = payload.get("research_evidence_summary") or {}
    evidence_gap_notes: list[str] = []
    if isinstance(research_summary, dict):
        evidence_gap_notes = _report_string_list(research_summary.get("evidence_gaps"))

    return [
        {
            "conclusion_id": "current_conclusion",
            "title_zh": "当前研究结论",
            "summary_zh": _report_text(
                overview.get("current_conclusion_zh"),
                fallback="暂无结论说明。",
            ),
            "claim_level": _report_text(
                overview.get("allowed_claim_level"),
                fallback="delivery_only",
            ),
            "confidence_label": _report_text(
                (research_summary.get("confidence") if isinstance(research_summary, dict) else None),
                fallback="--",
            ),
            "inline_source_refs": _report_string_list(
                [
                    payload.get("source_report_virtual_path"),
                    payload.get("scientific_gate_virtual_path"),
                    payload.get("provenance_manifest_virtual_path"),
                ]
            ),
            "evidence_gap_notes": evidence_gap_notes,
            "artifact_virtual_paths": _report_string_list(
                [
                    *(_report_string_list(payload.get("source_artifact_virtual_paths"))),
                    *(_report_string_list(payload.get("final_artifact_virtual_paths"))),
                ]
            )[:8],
        }
    ]


def _build_evidence_group(
    group_id: str,
    group_title_zh: str,
    artifact_virtual_paths: object,
    provenance_manifest_virtual_path: object,
) -> dict[str, object] | None:
    paths = _report_string_list(artifact_virtual_paths)
    provenance_path = _report_text(provenance_manifest_virtual_path, fallback="")
    if not paths and not provenance_path:
        return None
    return {
        "group_id": group_id,
        "group_title_zh": group_title_zh,
        "artifact_virtual_paths": paths,
        "provenance_manifest_virtual_path": provenance_path or None,
    }


def _evidence_index(payload: dict) -> list[dict[str, object]]:
    evidence_index = payload.get("evidence_index")
    if isinstance(evidence_index, list):
        normalized: list[dict[str, object]] = []
        for item in evidence_index:
            if not isinstance(item, dict):
                continue
            normalized_item = _build_evidence_group(
                _report_text(item.get("group_id"), fallback="evidence_group"),
                _report_text(item.get("group_title_zh"), fallback="证据分组"),
                item.get("artifact_virtual_paths"),
                item.get("provenance_manifest_virtual_path"),
            )
            if normalized_item:
                normalized.append(normalized_item)
        if normalized:
            return normalized

    groups: list[dict[str, object]] = []
    provenance_manifest_virtual_path = payload.get("provenance_manifest_virtual_path")
    figure_delivery_summary = payload.get("figure_delivery_summary") or {}
    research_evidence_summary = payload.get("research_evidence_summary") or {}
    scientific_followup_summary = payload.get("scientific_followup_summary") or {}

    for maybe_group in [
        _build_evidence_group(
            "research_evidence",
            "研究证据与科学判断",
            [
                *(_report_string_list(research_evidence_summary.get("artifact_virtual_paths") if isinstance(research_evidence_summary, dict) else [])),
                payload.get("scientific_gate_virtual_path"),
                payload.get("stability_evidence_virtual_path"),
            ],
            provenance_manifest_virtual_path,
        ),
        _build_evidence_group(
            "figures_and_delivery",
            "代表图表与交付产物",
            [
                *(_report_string_list(payload.get("final_artifact_virtual_paths"))),
                *(_report_string_list(figure_delivery_summary.get("artifact_virtual_paths") if isinstance(figure_delivery_summary, dict) else [])),
            ],
            provenance_manifest_virtual_path,
        ),
        _build_evidence_group(
            "runtime_and_lineage",
            "运行产物与追溯锚点",
            [
                payload.get("source_report_virtual_path"),
                payload.get("supervisor_handoff_virtual_path"),
                *(_report_string_list(payload.get("source_artifact_virtual_paths"))),
            ],
            provenance_manifest_virtual_path,
        ),
        _build_evidence_group(
            "followup_and_refresh",
            "后续动作与刷新链路",
            (scientific_followup_summary.get("artifact_virtual_paths") if isinstance(scientific_followup_summary, dict) else []),
            provenance_manifest_virtual_path,
        ),
    ]:
        if maybe_group:
            groups.append(maybe_group)

    return groups


def _markdown_inline_paths(paths: list[str]) -> str:
    if not paths:
        return "暂无"
    return "；".join(f"`{path}`" for path in paths)


def _render_conclusion_summary_markdown(overview: dict[str, object]) -> list[str]:
    return [
        "## 结论摘要",
        _report_text(overview.get("current_conclusion_zh"), fallback="暂无结论摘要。"),
        "",
        f"- 允许结论等级：`{_report_text(overview.get('allowed_claim_level'), fallback='delivery_only')}`",
        f"- 复核状态：`{_report_text(overview.get('review_status'), fallback='blocked')}`",
        f"- 可复现状态：`{_report_text(overview.get('reproducibility_status'), fallback='unknown')}`",
    ]


def _render_delivery_highlights_markdown(highlights: dict[str, object]) -> list[str]:
    metric_lines = _report_string_list(highlights.get("metric_lines"))
    figure_titles = _report_string_list(highlights.get("figure_titles"))
    highlight_paths = _report_string_list(highlights.get("highlight_artifact_virtual_paths"))

    lines = ["", "## 关键指标与代表图表"]
    lines.extend(["", "### 关键指标"])
    lines.extend(f"- {item}" for item in (metric_lines or ["暂无关键指标摘要。"]))
    lines.extend(["", "### 代表图表"])
    lines.extend(f"- {item}" for item in (figure_titles or ["暂无代表图表。"]))
    lines.extend(["", "### 高亮产物"])
    lines.extend(f"- `{path}`" for path in (highlight_paths or ["暂无高亮产物。"]))
    return lines


def _render_conclusion_sections_markdown(
    sections: list[dict[str, object]],
) -> list[str]:
    lines = ["", "## 结论与证据"]
    if not sections:
        lines.append("- 暂无结论条目。")
        return lines

    for section in sections:
        evidence_gap_notes = _report_string_list(section.get("evidence_gap_notes"))
        artifact_paths = _report_string_list(section.get("artifact_virtual_paths"))
        lines.extend(
            [
                "",
                f"### {_report_text(section.get('title_zh'), fallback='当前结论')}",
                _report_text(section.get("summary_zh"), fallback="暂无结论说明。"),
                f"- 来源：{_markdown_inline_paths(_report_string_list(section.get('inline_source_refs')))}",
                f"- Claim level：`{_report_text(section.get('claim_level'), fallback='delivery_only')}`",
                f"- 置信度：{_report_text(section.get('confidence_label'), fallback='--')}",
                f"- 证据缺口：{'; '.join(evidence_gap_notes) if evidence_gap_notes else '暂无'}",
                f"- 关联产物：{_markdown_inline_paths(artifact_paths)}",
            ]
        )
    return lines


def _render_evidence_index_markdown(
    evidence_index: list[dict[str, object]],
) -> list[str]:
    lines = ["", "## 证据索引"]
    if not evidence_index:
        lines.append("- 暂无证据索引。")
        return lines

    for group in evidence_index:
        artifact_paths = _report_string_list(group.get("artifact_virtual_paths"))
        provenance_manifest_virtual_path = _report_text(
            group.get("provenance_manifest_virtual_path"),
            fallback="",
        )
        lines.extend(
            [
                "",
                f"### {_report_text(group.get('group_title_zh'), fallback='证据分组')}",
            ]
        )
        lines.extend(f"- `{path}`" for path in (artifact_paths or ["暂无分组产物。"]))
        if provenance_manifest_virtual_path:
            lines.append(f"- provenance_manifest_virtual_path：`{provenance_manifest_virtual_path}`")
    return lines


def _render_next_steps_markdown(payload: dict, overview: dict[str, object]) -> list[str]:
    suggestions = [
        _report_text(
            overview.get("recommended_next_step_zh"),
            fallback="回到聊天确认下一步研究动作。",
        ),
        *_build_dynamic_report_recommendations(payload),
    ]
    deduped_suggestions = _report_string_list(suggestions)
    followup_summary = payload.get("scientific_followup_summary") or {}

    lines = ["", "## 建议下一步"]
    lines.extend(f"- {item}" for item in deduped_suggestions)

    next_stage = _report_text(payload.get("next_recommended_stage"), fallback="")
    if next_stage:
        lines.append(f"- next_recommended_stage：`{next_stage}`")

    source_report_virtual_path = _report_text(payload.get("source_report_virtual_path"), fallback="")
    if source_report_virtual_path:
        lines.append(f"- source_report_virtual_path：`{source_report_virtual_path}`")

    supervisor_handoff_virtual_path = _report_text(
        payload.get("supervisor_handoff_virtual_path"),
        fallback="",
    )
    if supervisor_handoff_virtual_path:
        lines.append(f"- supervisor_handoff_virtual_path：`{supervisor_handoff_virtual_path}`")

    if isinstance(followup_summary, dict):
        history_virtual_path = _report_text(followup_summary.get("history_virtual_path"), fallback="")
        if history_virtual_path:
            lines.append(f"- history_virtual_path：`{history_virtual_path}`")

    return lines


def _formal_render_artifact_manifest_markdown_compact(payload: dict) -> list[str]:
    """
    groups = _formal_artifact_group_summary(payload)
    lines = ["", "## 鏂囦欢娓呭崟涓庤矾寰勭储寮?"]
    for group in groups:
        lines.extend(["", f"### {group['title_zh']}"])
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            lines.append(summary)
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            lines.append("- 鏆傛棤鐩稿叧鏂囦欢銆?")
        else:
            for item in items:
                if not isinstance(item, dict):
                    continue
                lines.extend(
                    [
                        "",
                        f"#### `{_report_text(item.get('filename'), fallback='unknown')}`",
                        f"- 鏍囩锛歿_report_text(item.get('label'), fallback='鏈懡鍚嶆枃浠?)}",
                        f"- 鐢ㄩ€旓細{_report_text(item.get('description'), fallback='鏆傛棤璇存槑')}",
                    ]
                )
                file_type = _report_text(item.get("file_type"), fallback="")
                if file_type:
                    lines.append(f"- 绫诲瀷锛歚{file_type}`")
                location_kind = _report_text(item.get("location_kind"), fallback="")
                if location_kind:
                    lines.append(f"- 浣嶇疆鍒嗙被锛歚{location_kind}`")
                stage = _report_text(item.get("stage"), fallback="")
                if stage:
                    lines.append(f"- 鎵€灞為樁娈碉細`{stage}`")
                virtual_path = _report_text(item.get("virtual_path"), fallback="")
                if virtual_path:
                    lines.append(f"- 铏氭嫙璺緞锛歚{virtual_path}`")
                absolute_path = _report_text(item.get("absolute_path"), fallback="")
                if absolute_path:
                    lines.append(f"- 缁濆璺緞锛歚{absolute_path}`")
                if "is_final_deliverable" in item:
                    lines.append(
                        f"- 鏈€缁堜氦浠橈細`{'yes' if bool(item.get('is_final_deliverable')) else 'no'}`"
                    )
        notes = _report_string_list(group.get("notes"))
        if notes:
            lines.extend(["", "#### 璇存槑"])
            lines.extend(f"- {item}" for item in notes)
    return lines


    """
    return []


def _formal_render_artifact_manifest_html_compact(payload: dict) -> str:
    """
    groups = _formal_artifact_group_summary(payload)
    sections = ['<section class="panel">', "<h2>鏂囦欢娓呭崟涓庤矾寰勭储寮?/h2>"]
    for group in groups:
        sections.append(f"<h3>{escape(_report_text(group.get('title_zh'), fallback='文件分组'))}</h3>")
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            sections.append(f"<p>{escape(summary)}</p>")
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            sections.append("<p>鏆傛棤鐩稿叧鏂囦欢銆?/p>")
        else:
            cards = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                detail_items = [
                    f"<li>鏍囩锛歿escape(_report_text(item.get('label'), fallback='未命名文件'))}</li>",
                    f"<li>鐢ㄩ€旓細{escape(_report_text(item.get('description'), fallback='暂无说明'))}</li>",
                ]
                for label, key in [
                    ("绫诲瀷", "file_type"),
                    ("浣嶇疆鍒嗙被", "location_kind"),
                    ("鎵€灞為樁娈?", "stage"),
                    ("铏氭嫙璺緞", "virtual_path"),
                    ("缁濆璺緞", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        detail_items.append(
                            f"<li>{escape(label)}锛? <code>{escape(value)}</code></li>"
                        )
                if "is_final_deliverable" in item:
                    detail_items.append(
                        f"<li>鏈€缁堜氦浠橈細<code>{'yes' if bool(item.get('is_final_deliverable')) else 'no'}</code></li>"
                    )
                cards.append(
                    '<article class="detail-card">'
                    f"<h4><code>{escape(_report_text(item.get('filename'), fallback='unknown'))}</code></h4>"
                    f"<ul>{''.join(detail_items)}</ul>"
                    "</article>"
                )
            sections.append("".join(cards))
        notes = _report_string_list(group.get("notes"))
        if notes:
            sections.append("<h4>璇存槑</h4>")
            sections.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in notes) + "</ul>")
    sections.append("</section>")
    return "".join(sections)


    """
    return ""


def _formal_render_artifact_manifest_markdown_compact(payload: dict) -> list[str]:
    groups = _formal_artifact_group_summary(payload)
    lines = ["", "## 文件清单与路径索引"]
    for group in groups:
        lines.extend(["", f"### {_report_text(group.get('title_zh'), fallback='文件分组')}"])
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            lines.append(summary)
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            lines.append("- 暂无相关文件。")
        else:
            for item in items:
                if not isinstance(item, dict):
                    continue
                lines.extend(
                    [
                        "",
                        f"#### `{_report_text(item.get('filename'), fallback='unknown')}`",
                        f"- 标签：{_report_text(item.get('label'), fallback='未命名文件')}",
                        f"- 用途：{_report_text(item.get('description'), fallback='暂无说明')}",
                    ]
                )
                for label, key in [
                    ("类型", "file_type"),
                    ("位置分类", "location_kind"),
                    ("所属阶段", "stage"),
                    ("虚拟路径", "virtual_path"),
                    ("绝对路径", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        lines.append(f"- {label}：`{value}`")
                if "is_final_deliverable" in item:
                    lines.append(f"- 最终交付：`{'yes' if bool(item.get('is_final_deliverable')) else 'no'}`")
        notes = _report_string_list(group.get("notes"))
        if notes:
            lines.extend(["", "#### 说明"])
            lines.extend(f"- {item}" for item in notes)
    return lines


def _formal_render_artifact_manifest_html_compact(payload: dict) -> str:
    groups = _formal_artifact_group_summary(payload)
    sections = ['<section class="panel">', "<h2>文件清单与路径索引</h2>"]
    for group in groups:
        sections.append(f"<h3>{escape(_report_text(group.get('title_zh'), fallback='文件分组'))}</h3>")
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            sections.append(f"<p>{escape(summary)}</p>")
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            sections.append("<p>暂无相关文件。</p>")
        else:
            cards = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                detail_items = [
                    f"<li>标签：{escape(_report_text(item.get('label'), fallback='未命名文件'))}</li>",
                    f"<li>用途：{escape(_report_text(item.get('description'), fallback='暂无说明'))}</li>",
                ]
                for label, key in [
                    ("类型", "file_type"),
                    ("位置分类", "location_kind"),
                    ("所属阶段", "stage"),
                    ("虚拟路径", "virtual_path"),
                    ("绝对路径", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        detail_items.append(f"<li>{escape(label)}：<code>{escape(value)}</code></li>")
                if "is_final_deliverable" in item:
                    detail_items.append(f"<li>最终交付：<code>{'yes' if bool(item.get('is_final_deliverable')) else 'no'}</code></li>")
                cards.append(f'<article class="detail-card"><h4><code>{escape(_report_text(item.get("filename"), fallback="unknown"))}</code></h4><ul>{"".join(detail_items)}</ul></article>')
            sections.append("".join(cards))
        notes = _report_string_list(group.get("notes"))
        if notes:
            sections.append("<h4>说明</h4>")
            sections.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in notes) + "</ul>")
    sections.append("</section>")
    return "".join(sections)


def _legacy_render_markdown_v2(payload: dict) -> str:
    overview = _report_overview(payload)
    highlights = _delivery_highlights(payload)
    sections = _conclusion_sections(payload)
    evidence_index = _evidence_index(payload)

    lines = [
        f"# {_report_text(payload.get('report_title'), fallback='潜艇 CFD 阶段报告')}",
        "",
    ]
    lines.extend(_render_conclusion_summary_markdown(overview))
    lines.extend(_render_delivery_highlights_markdown(highlights))
    lines.extend(_render_conclusion_sections_markdown(sections))
    lines.extend(_render_evidence_index_markdown(evidence_index))
    lines.extend(_render_next_steps_markdown(payload, overview))
    lines.append("")
    return "\n".join(lines)


def _html_inline_paths(paths: list[str]) -> str:
    if not paths:
        return "暂无"
    return "；".join(f"<code>{escape(path)}</code>" for path in paths)


def _render_html_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f"<li>{escape(empty_text)}</li>"
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def _render_conclusion_summary_html(overview: dict[str, object]) -> str:
    return (
        '<section class="panel">'
        "<h2>结论摘要</h2>"
        f"<p>{escape(_report_text(overview.get('current_conclusion_zh'), fallback='暂无结论摘要。'))}</p>"
        f"<p><strong>允许结论等级：</strong> <code>{escape(_report_text(overview.get('allowed_claim_level'), fallback='delivery_only'))}</code></p>"
        f"<p><strong>复核状态：</strong> <code>{escape(_report_text(overview.get('review_status'), fallback='blocked'))}</code></p>"
        f"<p><strong>可复现状态：</strong> <code>{escape(_report_text(overview.get('reproducibility_status'), fallback='unknown'))}</code></p>"
        "</section>"
    )


def _render_delivery_highlights_html(highlights: dict[str, object]) -> str:
    metric_lines = _report_string_list(highlights.get("metric_lines"))
    figure_titles = _report_string_list(highlights.get("figure_titles"))
    highlight_paths = _report_string_list(highlights.get("highlight_artifact_virtual_paths"))
    return (
        '<section class="panel">'
        "<h2>关键指标与代表图表</h2>"
        "<h3>关键指标</h3>"
        f"<ul>{_render_html_list(metric_lines, '暂无关键指标摘要。')}</ul>"
        "<h3>代表图表</h3>"
        f"<ul>{_render_html_list(figure_titles, '暂无代表图表。')}</ul>"
        "<h3>高亮产物</h3>"
        "<ul>" + ("".join(f"<li><code>{escape(path)}</code></li>" for path in highlight_paths) or "<li>暂无高亮产物。</li>") + "</ul>"
        "</section>"
    )


def _render_conclusion_sections_html(
    sections: list[dict[str, object]],
) -> str:
    if not sections:
        return '<section class="panel"><h2>结论与证据</h2><p>暂无结论条目。</p></section>'

    rendered_sections = []
    for section in sections:
        evidence_gap_notes = _report_string_list(section.get("evidence_gap_notes"))
        artifact_paths = _report_string_list(section.get("artifact_virtual_paths"))
        rendered_sections.append(
            '<article class="conclusion-card">'
            f"<h3>{escape(_report_text(section.get('title_zh'), fallback='当前结论'))}</h3>"
            f"<p>{escape(_report_text(section.get('summary_zh'), fallback='暂无结论说明。'))}</p>"
            f"<p><strong>来源：</strong> {_html_inline_paths(_report_string_list(section.get('inline_source_refs')))}</p>"
            f"<p><strong>Claim level：</strong> <code>{escape(_report_text(section.get('claim_level'), fallback='delivery_only'))}</code></p>"
            f"<p><strong>置信度：</strong> {escape(_report_text(section.get('confidence_label'), fallback='--'))}</p>"
            f"<p><strong>证据缺口：</strong> {escape('; '.join(evidence_gap_notes) if evidence_gap_notes else '暂无')}</p>"
            f"<p><strong>关联产物：</strong> {_html_inline_paths(artifact_paths)}</p>"
            "</article>"
        )

    return '<section class="panel"><h2>结论与证据</h2>' + "".join(rendered_sections) + "</section>"


def _render_evidence_index_html(
    evidence_index: list[dict[str, object]],
) -> str:
    if not evidence_index:
        return '<section class="panel"><h2>证据索引</h2><p>暂无证据索引。</p></section>'

    rendered_groups = []
    for group in evidence_index:
        artifact_paths = _report_string_list(group.get("artifact_virtual_paths"))
        provenance_manifest_virtual_path = _report_text(
            group.get("provenance_manifest_virtual_path"),
            fallback="",
        )
        rendered_groups.append(
            '<div class="evidence-group">'
            f"<h3>{escape(_report_text(group.get('group_title_zh'), fallback='证据分组'))}</h3>"
            "<ul>"
            + ("".join(f"<li><code>{escape(path)}</code></li>" for path in artifact_paths) or "<li>暂无分组产物。</li>")
            + (f"<li><strong>provenance_manifest_virtual_path：</strong> <code>{escape(provenance_manifest_virtual_path)}</code></li>" if provenance_manifest_virtual_path else "")
            + "</ul>"
            "</div>"
        )

    return '<section class="panel"><h2>证据索引</h2>' + "".join(rendered_groups) + "</section>"


def _render_next_steps_html(payload: dict, overview: dict[str, object]) -> str:
    suggestions = _report_string_list(
        [
            _report_text(
                overview.get("recommended_next_step_zh"),
                fallback="回到聊天确认下一步研究动作。",
            ),
            *_build_dynamic_report_recommendations(payload),
        ]
    )
    followup_summary = payload.get("scientific_followup_summary") or {}

    detail_items = []
    for label, value in [
        ("next_recommended_stage", payload.get("next_recommended_stage")),
        ("source_report_virtual_path", payload.get("source_report_virtual_path")),
        (
            "supervisor_handoff_virtual_path",
            payload.get("supervisor_handoff_virtual_path"),
        ),
        (
            "history_virtual_path",
            followup_summary.get("history_virtual_path") if isinstance(followup_summary, dict) else None,
        ),
    ]:
        text = _report_text(value, fallback="")
        if text:
            detail_items.append(f"<li><strong>{escape(label)}：</strong> <code>{escape(text)}</code></li>")

    return f'<section class="panel"><h2>建议下一步</h2><ul>{_render_html_list(suggestions, "回到聊天确认下一步研究动作。")}</ul>' + (f"<ul>{''.join(detail_items)}</ul>" if detail_items else "") + "</section>"


def _legacy_render_html_v2(payload: dict) -> str:
    overview = _report_overview(payload)
    highlights = _delivery_highlights(payload)
    sections = _conclusion_sections(payload)
    evidence_index = _evidence_index(payload)

    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(_report_text(payload.get("report_title"), fallback="潜艇 CFD 阶段报告"))}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: #f7f8fa;
        color: #111827;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}
      .conclusion-card,
      .evidence-group {{
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        background: #f8fafc;
        margin-top: 12px;
      }}
      h1, h2, h3 {{ margin: 0 0 12px; }}
      p {{ line-height: 1.7; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li {{ margin-bottom: 8px; }}
      strong {{ color: #0f172a; }}
      code {{
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      }}
    </style>
  </head>
  <body>
    <section class="panel">
      <h1>{escape(_report_text(payload.get("report_title"), fallback="潜艇 CFD 阶段报告"))}</h1>
      <p>{escape(_report_text(payload.get("summary_zh"), fallback="暂无摘要。"))}</p>
    </section>
    {_render_conclusion_summary_html(overview)}
    {_render_delivery_highlights_html(highlights)}
    {_render_conclusion_sections_html(sections)}
    {_render_evidence_index_html(evidence_index)}
    {_render_next_steps_html(payload, overview)}
  </body>
</html>
"""


def _formal_render_artifact_manifest_markdown_compact(payload: dict) -> list[str]:
    groups = _formal_artifact_group_summary(payload)
    lines = ["", "## 文件清单与路径索引"]
    for group in groups:
        lines.extend(["", f"### {_report_text(group.get('title_zh'), fallback='文件分组')}"])
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            lines.append(summary)
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            lines.append("- 暂无相关文件。")
        else:
            for item in items:
                if not isinstance(item, dict):
                    continue
                lines.extend(
                    [
                        "",
                        f"#### `{_report_text(item.get('filename'), fallback='unknown')}`",
                        f"- 标签：{_report_text(item.get('label'), fallback='未命名文件')}",
                        f"- 用途：{_report_text(item.get('description'), fallback='暂无说明')}",
                    ]
                )
                for label, key in [
                    ("类型", "file_type"),
                    ("位置分类", "location_kind"),
                    ("所属阶段", "stage"),
                    ("虚拟路径", "virtual_path"),
                    ("绝对路径", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        lines.append(f"- {label}：`{value}`")
                if "is_final_deliverable" in item:
                    lines.append(f"- 最终交付：`{'yes' if bool(item.get('is_final_deliverable')) else 'no'}`")
        notes = _report_string_list(group.get("notes"))
        if notes:
            lines.extend(["", "#### 说明"])
            lines.extend(f"- {item}" for item in notes)
    return lines


def _formal_render_artifact_manifest_html_compact(payload: dict) -> str:
    groups = _formal_artifact_group_summary(payload)
    sections = ['<section class="panel">', "<h2>文件清单与路径索引</h2>"]
    for group in groups:
        sections.append(f"<h3>{escape(_report_text(group.get('title_zh'), fallback='文件分组'))}</h3>")
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            sections.append(f"<p>{escape(summary)}</p>")
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            sections.append("<p>暂无相关文件。</p>")
        else:
            cards = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                detail_items = [
                    f"<li>标签：{escape(_report_text(item.get('label'), fallback='未命名文件'))}</li>",
                    f"<li>用途：{escape(_report_text(item.get('description'), fallback='暂无说明'))}</li>",
                ]
                for label, key in [
                    ("类型", "file_type"),
                    ("位置分类", "location_kind"),
                    ("所属阶段", "stage"),
                    ("虚拟路径", "virtual_path"),
                    ("绝对路径", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        detail_items.append(f"<li>{escape(label)}：<code>{escape(value)}</code></li>")
                if "is_final_deliverable" in item:
                    detail_items.append(f"<li>最终交付：<code>{'yes' if bool(item.get('is_final_deliverable')) else 'no'}</code></li>")
                cards.append(f'<article class="detail-card"><h4><code>{escape(_report_text(item.get("filename"), fallback="unknown"))}</code></h4><ul>{"".join(detail_items)}</ul></article>')
            sections.append("".join(cards))
        notes = _report_string_list(group.get("notes"))
        if notes:
            sections.append("<h4>说明</h4>")
            sections.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in notes) + "</ul>")
    sections.append("</section>")
    return "".join(sections)


def _legacy_render_markdown_v3(payload: dict) -> str:
    overview = _report_overview(payload)
    lines = [
        f"# {_report_text(payload.get('report_title'), fallback='潜艇 CFD 最终报告')}",
        "",
    ]
    lines.extend(_formal_render_task_conditions_markdown(payload))
    lines.extend(_formal_render_geometry_settings_markdown(payload))
    lines.extend(_formal_render_results_validation_markdown(payload))
    lines.extend(_formal_render_traceability_markdown(payload))
    lines.extend(_formal_render_artifact_manifest_markdown_compact(payload))
    lines.extend(_formal_render_next_steps_markdown(payload, overview))
    lines.append("")
    return "\n".join(lines)


def _legacy_render_html_v3(payload: dict) -> str:
    overview = _report_overview(payload)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(_report_text(payload.get("report_title"), fallback="潜艇 CFD 最终报告"))}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: #f7f8fa;
        color: #111827;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}
      .detail-card {{
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        background: #f8fafc;
        margin-top: 12px;
      }}
      h1, h2, h3, h4 {{ margin: 0 0 12px; }}
      p {{ line-height: 1.7; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li {{ margin-bottom: 8px; }}
      strong {{ color: #0f172a; }}
      code {{
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      }}
    </style>
  </head>
  <body>
    <section class="panel">
      <h1>{escape(_report_text(payload.get("report_title"), fallback="潜艇 CFD 最终报告"))}</h1>
      <p>{escape(_report_text(payload.get("summary_zh"), fallback="暂无摘要。"))}</p>
    </section>
    {_formal_render_task_conditions_html(payload)}
    {_formal_render_geometry_settings_html(payload)}
    {_formal_render_results_validation_html(payload)}
    {_formal_render_traceability_html(payload)}
    {_formal_render_artifact_manifest_html_compact(payload)}
    {_formal_render_next_steps_html(payload, overview)}
  </body>
</html>
"""


def _formal_render_artifact_manifest_markdown_compact(payload: dict) -> list[str]:
    groups = _formal_artifact_group_summary(payload)
    lines = ["", "## 文件清单与路径索引"]
    for group in groups:
        lines.extend(["", f"### {_report_text(group.get('title_zh'), fallback='文件分组')}"])
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            lines.append(summary)
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            lines.append("- 暂无相关文件。")
        else:
            for item in items:
                if not isinstance(item, dict):
                    continue
                lines.extend(
                    [
                        "",
                        f"#### `{_report_text(item.get('filename'), fallback='unknown')}`",
                        f"- 标签：{_report_text(item.get('label'), fallback='未命名文件')}",
                        f"- 用途：{_report_text(item.get('description'), fallback='暂无说明')}",
                    ]
                )
                for label, key in [
                    ("类型", "file_type"),
                    ("位置分类", "location_kind"),
                    ("所属阶段", "stage"),
                    ("虚拟路径", "virtual_path"),
                    ("绝对路径", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        lines.append(f"- {label}：`{value}`")
                if "is_final_deliverable" in item:
                    lines.append(f"- 最终交付：`{'yes' if bool(item.get('is_final_deliverable')) else 'no'}`")
        notes = _report_string_list(group.get("notes"))
        if notes:
            lines.extend(["", "#### 说明"])
            lines.extend(f"- {item}" for item in notes)
    return lines


def _formal_render_artifact_manifest_html_compact(payload: dict) -> str:
    groups = _formal_artifact_group_summary(payload)
    sections = ['<section class="panel">', "<h2>文件清单与路径索引</h2>"]
    for group in groups:
        sections.append(f"<h3>{escape(_report_text(group.get('title_zh'), fallback='文件分组'))}</h3>")
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            sections.append(f"<p>{escape(summary)}</p>")
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            sections.append("<p>暂无相关文件。</p>")
        else:
            cards = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                detail_items = [
                    f"<li>标签：{escape(_report_text(item.get('label'), fallback='未命名文件'))}</li>",
                    f"<li>用途：{escape(_report_text(item.get('description'), fallback='暂无说明'))}</li>",
                ]
                for label, key in [
                    ("类型", "file_type"),
                    ("位置分类", "location_kind"),
                    ("所属阶段", "stage"),
                    ("虚拟路径", "virtual_path"),
                    ("绝对路径", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        detail_items.append(f"<li>{escape(label)}：<code>{escape(value)}</code></li>")
                if "is_final_deliverable" in item:
                    detail_items.append(f"<li>最终交付：<code>{'yes' if bool(item.get('is_final_deliverable')) else 'no'}</code></li>")
                cards.append(f'<article class="detail-card"><h4><code>{escape(_report_text(item.get("filename"), fallback="unknown"))}</code></h4><ul>{"".join(detail_items)}</ul></article>')
            sections.append("".join(cards))
        notes = _report_string_list(group.get("notes"))
        if notes:
            sections.append("<h4>说明</h4>")
            sections.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in notes) + "</ul>")
    sections.append("</section>")
    return "".join(sections)


def _legacy_render_markdown_v4(payload: dict) -> str:
    overview = _report_overview(payload)
    lines = [
        f"# {_report_text(payload.get('report_title'), fallback='潜艇 CFD 最终报告')}",
        "",
    ]
    lines.extend(_formal_render_task_conditions_markdown(payload))
    lines.extend(_formal_render_geometry_settings_markdown(payload))
    lines.extend(_formal_render_results_validation_markdown(payload))
    lines.extend(_formal_render_traceability_markdown(payload))
    lines.extend(_formal_render_artifact_manifest_markdown_compact(payload))
    lines.extend(_formal_render_next_steps_markdown(payload, overview))
    lines.append("")
    return "\n".join(lines)


def _legacy_render_html_v4(payload: dict) -> str:
    overview = _report_overview(payload)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(_report_text(payload.get("report_title"), fallback="潜艇 CFD 最终报告"))}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: #f7f8fa;
        color: #111827;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}
      .detail-card {{
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        background: #f8fafc;
        margin-top: 12px;
      }}
      h1, h2, h3, h4 {{ margin: 0 0 12px; }}
      p {{ line-height: 1.7; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li {{ margin-bottom: 8px; }}
      strong {{ color: #0f172a; }}
      code {{
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      }}
    </style>
  </head>
  <body>
    <section class="panel">
      <h1>{escape(_report_text(payload.get("report_title"), fallback="潜艇 CFD 最终报告"))}</h1>
      <p>{escape(_report_text(payload.get("summary_zh"), fallback="暂无摘要。"))}</p>
    </section>
    {_formal_render_task_conditions_html(payload)}
    {_formal_render_geometry_settings_html(payload)}
    {_formal_render_results_validation_html(payload)}
    {_formal_render_traceability_html(payload)}
    {_formal_render_artifact_manifest_html_compact(payload)}
    {_formal_render_next_steps_html(payload, overview)}
  </body>
</html>
"""


__all__ = ["render_delivery_readiness_markdown", "render_html", "render_markdown"]


def _formal_render_artifact_manifest_markdown(payload: dict) -> list[str]:
    manifest = _formal_artifact_manifest(payload)
    workspace_summary = _formal_workspace_storage_summary(payload)
    lines = [
        "",
        "## 文件清单与路径索引",
        "",
        "### 关键结果与交付文件",
    ]
    if not manifest:
        lines.append("- 暂无关键文件清单。")
    else:
        for item in manifest:
            lines.extend(
                [
                    "",
                    f"#### `{item['filename']}`",
                    f"- 标签：{item['label']}",
                    f"- 用途：{item['description']}",
                    f"- 类型：`{item['file_type']}`",
                    f"- 位置分类：`{item['location_kind']}`",
                    f"- 所属阶段：`{item['stage']}`",
                    f"- 虚拟路径：`{item['virtual_path']}`",
                    f"- 绝对路径：`{item['absolute_path']}`",
                    f"- 最终交付：`{'yes' if item['is_final_deliverable'] else 'no'}`",
                ]
            )

    lines.extend(
        [
            "",
            "### 中间文件位置说明",
            "<!-- \u6d93\ue162\u68ff\u93c2\u56e6\u6b22\u6d63\u5d87\u7586\u7487\u5b58\u69d1 -->",
        ]
    )
    if not workspace_summary:
        lines.append("- 暂无 workspace 位置摘要。")
        return lines

    for label, key in [
        ("workspace_run_root_virtual_path", "workspace_run_root_virtual_path"),
        ("workspace_run_root_absolute_path", "workspace_run_root_absolute_path"),
        ("workspace_case_dir_virtual_path", "workspace_case_dir_virtual_path"),
        ("workspace_case_dir_absolute_path", "workspace_case_dir_absolute_path"),
        ("run_script_virtual_path", "run_script_virtual_path"),
        ("run_script_absolute_path", "run_script_absolute_path"),
        ("workspace_postprocess_virtual_path", "workspace_postprocess_virtual_path"),
        ("workspace_postprocess_absolute_path", "workspace_postprocess_absolute_path"),
        ("study_workspace_root_virtual_path", "study_workspace_root_virtual_path"),
        ("study_workspace_root_absolute_path", "study_workspace_root_absolute_path"),
    ]:
        value = _report_text(workspace_summary.get(key), fallback="")
        if value:
            lines.append(f"- {label}：`{value}`")

    notes = _report_string_list(workspace_summary.get("directory_notes"))
    if notes:
        lines.extend(["", "#### 说明"])
        lines.extend(f"- {item}" for item in notes)
    return lines


def _formal_render_artifact_manifest_html(payload: dict) -> str:
    manifest = _formal_artifact_manifest(payload)
    workspace_summary = _formal_workspace_storage_summary(payload)
    cards = []
    if manifest:
        for item in manifest:
            cards.append(
                '<article class="detail-card">'
                f"<h3><code>{escape(str(item['filename']))}</code></h3>"
                "<ul>"
                f"<li>标签：{escape(str(item['label']))}</li>"
                f"<li>用途：{escape(str(item['description']))}</li>"
                f"<li>类型：<code>{escape(str(item['file_type']))}</code></li>"
                f"<li>位置分类：<code>{escape(str(item['location_kind']))}</code></li>"
                f"<li>所属阶段：<code>{escape(str(item['stage']))}</code></li>"
                f"<li>虚拟路径：<code>{escape(str(item['virtual_path']))}</code></li>"
                f"<li>绝对路径：<code>{escape(str(item['absolute_path']))}</code></li>"
                f"<li>最终交付：<code>{'yes' if item['is_final_deliverable'] else 'no'}</code></li>"
                "</ul>"
                "</article>"
            )

    summary_items = []
    if workspace_summary:
        for label, key in [
            ("workspace_run_root_virtual_path", "workspace_run_root_virtual_path"),
            ("workspace_run_root_absolute_path", "workspace_run_root_absolute_path"),
            ("workspace_case_dir_virtual_path", "workspace_case_dir_virtual_path"),
            ("workspace_case_dir_absolute_path", "workspace_case_dir_absolute_path"),
            ("run_script_virtual_path", "run_script_virtual_path"),
            ("run_script_absolute_path", "run_script_absolute_path"),
            ("workspace_postprocess_virtual_path", "workspace_postprocess_virtual_path"),
            ("workspace_postprocess_absolute_path", "workspace_postprocess_absolute_path"),
            ("study_workspace_root_virtual_path", "study_workspace_root_virtual_path"),
            ("study_workspace_root_absolute_path", "study_workspace_root_absolute_path"),
        ]:
            value = _report_text(workspace_summary.get(key), fallback="")
            if value:
                summary_items.append(f"<li><strong>{escape(label)}：</strong> <code>{escape(value)}</code></li>")
        for item in _report_string_list(workspace_summary.get("directory_notes")):
            summary_items.append(f"<li>{escape(item)}</li>")

    return (
        '<section class="panel">'
        "<h2>文件清单与路径索引</h2>"
        "<h3>关键结果与交付文件</h3>"
        + ("".join(cards) if cards else "<p>暂无关键文件清单。</p>")
        + "<h3>中间文件位置说明</h3>"
        + "<!-- \u6d93\ue162\u68ff\u93c2\u56e6\u6b22\u6d63\u5d87\u7586\u7487\u5b58\u69d1 -->"
        + (f"<ul>{''.join(summary_items)}</ul>" if summary_items else "<p>暂无 workspace 位置摘要。</p>")
        + "</section>"
    )


__all__ = ["render_delivery_readiness_markdown", "render_html", "render_markdown"]


def _formal_render_artifact_manifest_markdown(payload: dict) -> list[str]:
    manifest = _formal_artifact_manifest(payload)
    workspace_summary = _formal_workspace_storage_summary(payload)
    lines = [
        "",
        "## 文件清单与路径索引",
        "",
        "### 关键结果与交付文件",
    ]
    if not manifest:
        lines.append("- 暂无关键文件清单。")
    else:
        for item in manifest:
            lines.extend(
                [
                    "",
                    f"#### `{item['filename']}`",
                    f"- 标签：{item['label']}",
                    f"- 用途：{item['description']}",
                    f"- 类型：`{item['file_type']}`",
                    f"- 位置分类：`{item['location_kind']}`",
                    f"- 所属阶段：`{item['stage']}`",
                    f"- 虚拟路径：`{item['virtual_path']}`",
                    f"- 绝对路径：`{item['absolute_path']}`",
                    f"- 最终交付：`{'yes' if item['is_final_deliverable'] else 'no'}`",
                ]
            )

    lines.extend(
        [
            "",
            "### 中间文件位置说明",
            "<!-- \u6d93\ue162\u68ff\u93c2\u56e6\u6b22\u6d63\u5d87\u7586\u7487\u5b58\u69d1 -->",
        ]
    )
    if not workspace_summary:
        lines.append("- 暂无 workspace 位置摘要。")
        return lines

    for label, key in [
        ("workspace_run_root_virtual_path", "workspace_run_root_virtual_path"),
        ("workspace_run_root_absolute_path", "workspace_run_root_absolute_path"),
        ("workspace_case_dir_virtual_path", "workspace_case_dir_virtual_path"),
        ("workspace_case_dir_absolute_path", "workspace_case_dir_absolute_path"),
        ("run_script_virtual_path", "run_script_virtual_path"),
        ("run_script_absolute_path", "run_script_absolute_path"),
        ("workspace_postprocess_virtual_path", "workspace_postprocess_virtual_path"),
        ("workspace_postprocess_absolute_path", "workspace_postprocess_absolute_path"),
        ("study_workspace_root_virtual_path", "study_workspace_root_virtual_path"),
        ("study_workspace_root_absolute_path", "study_workspace_root_absolute_path"),
    ]:
        value = _report_text(workspace_summary.get(key), fallback="")
        if value:
            lines.append(f"- {label}：`{value}`")

    notes = _report_string_list(workspace_summary.get("directory_notes"))
    if notes:
        lines.extend(["", "#### 说明"])
        lines.extend(f"- {item}" for item in notes)
    return lines


def _formal_render_artifact_manifest_html(payload: dict) -> str:
    manifest = _formal_artifact_manifest(payload)
    workspace_summary = _formal_workspace_storage_summary(payload)
    cards = []
    if manifest:
        for item in manifest:
            cards.append(
                '<article class="detail-card">'
                f"<h3><code>{escape(str(item['filename']))}</code></h3>"
                "<ul>"
                f"<li>标签：{escape(str(item['label']))}</li>"
                f"<li>用途：{escape(str(item['description']))}</li>"
                f"<li>类型：<code>{escape(str(item['file_type']))}</code></li>"
                f"<li>位置分类：<code>{escape(str(item['location_kind']))}</code></li>"
                f"<li>所属阶段：<code>{escape(str(item['stage']))}</code></li>"
                f"<li>虚拟路径：<code>{escape(str(item['virtual_path']))}</code></li>"
                f"<li>绝对路径：<code>{escape(str(item['absolute_path']))}</code></li>"
                f"<li>最终交付：<code>{'yes' if item['is_final_deliverable'] else 'no'}</code></li>"
                "</ul>"
                "</article>"
            )

    summary_items = []
    if workspace_summary:
        for label, key in [
            ("workspace_run_root_virtual_path", "workspace_run_root_virtual_path"),
            ("workspace_run_root_absolute_path", "workspace_run_root_absolute_path"),
            ("workspace_case_dir_virtual_path", "workspace_case_dir_virtual_path"),
            ("workspace_case_dir_absolute_path", "workspace_case_dir_absolute_path"),
            ("run_script_virtual_path", "run_script_virtual_path"),
            ("run_script_absolute_path", "run_script_absolute_path"),
            ("workspace_postprocess_virtual_path", "workspace_postprocess_virtual_path"),
            ("workspace_postprocess_absolute_path", "workspace_postprocess_absolute_path"),
            ("study_workspace_root_virtual_path", "study_workspace_root_virtual_path"),
            ("study_workspace_root_absolute_path", "study_workspace_root_absolute_path"),
        ]:
            value = _report_text(workspace_summary.get(key), fallback="")
            if value:
                summary_items.append(f"<li><strong>{escape(label)}：</strong> <code>{escape(value)}</code></li>")
        for item in _report_string_list(workspace_summary.get("directory_notes")):
            summary_items.append(f"<li>{escape(item)}</li>")

    return (
        '<section class="panel">'
        "<h2>文件清单与路径索引</h2>"
        "<h3>关键结果与交付文件</h3>"
        + ("".join(cards) if cards else "<p>暂无关键文件清单。</p>")
        + "<h3>中间文件位置说明</h3>"
        + "<!-- \u6d93\ue162\u68ff\u93c2\u56e6\u6b22\u6d63\u5d87\u7586\u7487\u5b58\u69d1 -->"
        + (f"<ul>{''.join(summary_items)}</ul>" if summary_items else "<p>暂无 workspace 位置摘要。</p>")
        + "</section>"
    )


__all__ = ["render_delivery_readiness_markdown", "render_html", "render_markdown"]


def _formal_workspace_storage_summary(payload: dict) -> dict[str, object]:
    summary = payload.get("workspace_storage_summary")
    if not isinstance(summary, dict):
        return {}
    return {
        "workspace_run_root_virtual_path": _report_text(summary.get("workspace_run_root_virtual_path"), fallback=""),
        "workspace_run_root_absolute_path": _report_text(summary.get("workspace_run_root_absolute_path"), fallback=""),
        "workspace_case_dir_virtual_path": _report_text(summary.get("workspace_case_dir_virtual_path"), fallback=""),
        "workspace_case_dir_absolute_path": _report_text(summary.get("workspace_case_dir_absolute_path"), fallback=""),
        "run_script_virtual_path": _report_text(summary.get("run_script_virtual_path"), fallback=""),
        "run_script_absolute_path": _report_text(summary.get("run_script_absolute_path"), fallback=""),
        "workspace_postprocess_virtual_path": _report_text(summary.get("workspace_postprocess_virtual_path"), fallback=""),
        "workspace_postprocess_absolute_path": _report_text(summary.get("workspace_postprocess_absolute_path"), fallback=""),
        "study_workspace_root_virtual_path": _report_text(summary.get("study_workspace_root_virtual_path"), fallback=""),
        "study_workspace_root_absolute_path": _report_text(summary.get("study_workspace_root_absolute_path"), fallback=""),
        "directory_notes": _report_string_list(summary.get("directory_notes")),
    }


def _formal_render_artifact_manifest_markdown(payload: dict) -> list[str]:
    manifest = _formal_artifact_manifest(payload)
    workspace_summary = _formal_workspace_storage_summary(payload)
    lines = ["", "## 文件清单与路径索引", "", "### 关键结果与交付文件"]
    if not manifest:
        lines.append("- 暂无关键文件清单。")
    else:
        for item in manifest:
            lines.extend(
                [
                    "",
                    f"#### `{item['filename']}`",
                    f"- 标签：{item['label']}",
                    f"- 用途：{item['description']}",
                    f"- 类型：`{item['file_type']}`",
                    f"- 位置分类：`{item['location_kind']}`",
                    f"- 所属阶段：`{item['stage']}`",
                    f"- 虚拟路径：`{item['virtual_path']}`",
                    f"- 绝对路径：`{item['absolute_path']}`",
                    f"- 最终交付：`{'yes' if item['is_final_deliverable'] else 'no'}`",
                ]
            )

    lines.extend(["", "### 中间文件位置说明", "<!-- 娑擃參妫块弬鍥︽娴ｅ秶鐤嗙拠瀛樻 -->"])
    if not workspace_summary:
        lines.append("- 暂无 workspace 位置摘要。")
        return lines

    for label, key in [
        ("workspace_run_root_virtual_path", "workspace_run_root_virtual_path"),
        ("workspace_run_root_absolute_path", "workspace_run_root_absolute_path"),
        ("workspace_case_dir_virtual_path", "workspace_case_dir_virtual_path"),
        ("workspace_case_dir_absolute_path", "workspace_case_dir_absolute_path"),
        ("run_script_virtual_path", "run_script_virtual_path"),
        ("run_script_absolute_path", "run_script_absolute_path"),
        ("workspace_postprocess_virtual_path", "workspace_postprocess_virtual_path"),
        ("workspace_postprocess_absolute_path", "workspace_postprocess_absolute_path"),
        ("study_workspace_root_virtual_path", "study_workspace_root_virtual_path"),
        ("study_workspace_root_absolute_path", "study_workspace_root_absolute_path"),
    ]:
        value = _report_text(workspace_summary.get(key), fallback="")
        if value:
            lines.append(f"- {label}：`{value}`")

    notes = _report_string_list(workspace_summary.get("directory_notes"))
    if notes:
        lines.extend(["", "#### 说明"])
        lines.extend(f"- {item}" for item in notes)
    return lines


def _formal_render_artifact_manifest_html(payload: dict) -> str:
    manifest = _formal_artifact_manifest(payload)
    workspace_summary = _formal_workspace_storage_summary(payload)
    cards = []
    if manifest:
        for item in manifest:
            cards.append(
                '<article class="detail-card">'
                f"<h3><code>{escape(str(item['filename']))}</code></h3>"
                "<ul>"
                f"<li>标签：{escape(str(item['label']))}</li>"
                f"<li>用途：{escape(str(item['description']))}</li>"
                f"<li>类型：<code>{escape(str(item['file_type']))}</code></li>"
                f"<li>位置分类：<code>{escape(str(item['location_kind']))}</code></li>"
                f"<li>所属阶段：<code>{escape(str(item['stage']))}</code></li>"
                f"<li>虚拟路径：<code>{escape(str(item['virtual_path']))}</code></li>"
                f"<li>绝对路径：<code>{escape(str(item['absolute_path']))}</code></li>"
                f"<li>最终交付：<code>{'yes' if item['is_final_deliverable'] else 'no'}</code></li>"
                "</ul>"
                "</article>"
            )

    summary_items = []
    if workspace_summary:
        for label, key in [
            ("workspace_run_root_virtual_path", "workspace_run_root_virtual_path"),
            ("workspace_run_root_absolute_path", "workspace_run_root_absolute_path"),
            ("workspace_case_dir_virtual_path", "workspace_case_dir_virtual_path"),
            ("workspace_case_dir_absolute_path", "workspace_case_dir_absolute_path"),
            ("run_script_virtual_path", "run_script_virtual_path"),
            ("run_script_absolute_path", "run_script_absolute_path"),
            ("workspace_postprocess_virtual_path", "workspace_postprocess_virtual_path"),
            ("workspace_postprocess_absolute_path", "workspace_postprocess_absolute_path"),
            ("study_workspace_root_virtual_path", "study_workspace_root_virtual_path"),
            ("study_workspace_root_absolute_path", "study_workspace_root_absolute_path"),
        ]:
            value = _report_text(workspace_summary.get(key), fallback="")
            if value:
                summary_items.append(f"<li><strong>{escape(label)}：</strong> <code>{escape(value)}</code></li>")
        for item in _report_string_list(workspace_summary.get("directory_notes")):
            summary_items.append(f"<li>{escape(item)}</li>")

    return (
        '<section class="panel">'
        "<h2>文件清单与路径索引</h2>"
        "<h3>关键结果与交付文件</h3>"
        + ("".join(cards) if cards else "<p>暂无关键文件清单。</p>")
        + "<h3>中间文件位置说明</h3>"
        + "<!-- 娑擃參妫块弬鍥︽娴ｅ秶鐤嗙拠瀛樻 -->"
        + (f"<ul>{''.join(summary_items)}</ul>" if summary_items else "<p>暂无 workspace 位置摘要。</p>")
        + "</section>"
    )


__all__ = ["render_delivery_readiness_markdown", "render_html", "render_markdown"]


def _formal_markdown_inline_paths(paths: list[str]) -> str:
    if not paths:
        return "暂无"
    return "；".join(f"`{path}`" for path in paths)


def _formal_html_inline_paths(paths: list[str]) -> str:
    if not paths:
        return "暂无"
    return "；".join(f"<code>{escape(path)}</code>" for path in paths)


def _formal_normalized_simulation_requirements(payload: dict) -> dict[str, object]:
    simulation_requirements = payload.get("simulation_requirements")
    if isinstance(simulation_requirements, dict) and simulation_requirements:
        return simulation_requirements
    solver_metrics = payload.get("solver_metrics")
    if isinstance(solver_metrics, dict):
        nested_requirements = solver_metrics.get("simulation_requirements")
        if isinstance(nested_requirements, dict):
            return nested_requirements
    return {}


def _formal_normalized_mesh_summary(payload: dict) -> dict[str, object]:
    solver_metrics = payload.get("solver_metrics")
    if isinstance(solver_metrics, dict):
        mesh_summary = solver_metrics.get("mesh_summary")
        if isinstance(mesh_summary, dict):
            return mesh_summary
    return {}


def _formal_normalized_residual_summary(payload: dict) -> dict[str, object]:
    solver_metrics = payload.get("solver_metrics")
    if isinstance(solver_metrics, dict):
        residual_summary = solver_metrics.get("residual_summary")
        if isinstance(residual_summary, dict):
            return residual_summary
    return {}


def _formal_artifact_manifest(payload: dict) -> list[dict[str, object]]:
    manifest = payload.get("artifact_manifest")
    if not isinstance(manifest, list):
        return []
    normalized: list[dict[str, object]] = []
    for item in manifest:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "label": _report_text(item.get("label"), fallback="未命名产物"),
                "description": _report_text(item.get("description"), fallback="暂无说明"),
                "filename": _report_text(item.get("filename"), fallback="unknown"),
                "file_type": _report_text(item.get("file_type"), fallback="file"),
                "location_kind": _report_text(item.get("location_kind"), fallback="unknown"),
                "stage": _report_text(item.get("stage"), fallback="unknown"),
                "virtual_path": _report_text(item.get("virtual_path"), fallback=""),
                "absolute_path": _report_text(item.get("absolute_path"), fallback=""),
                "is_final_deliverable": bool(item.get("is_final_deliverable")),
            }
        )
    return normalized


def _formal_artifact_group_summary(payload: dict) -> list[dict[str, object]]:
    groups = payload.get("artifact_group_summary")
    normalized_groups: list[dict[str, object]] = []
    if isinstance(groups, list):
        for group in groups:
            if not isinstance(group, dict):
                continue
            raw_items = group.get("items")
            items: list[dict[str, object]] = []
            if isinstance(raw_items, list):
                for item in raw_items:
                    if not isinstance(item, dict):
                        continue
                    items.append(
                        {
                            "label": _report_text(item.get("label"), fallback="未命名文件"),
                            "description": _report_text(item.get("description"), fallback="暂无说明"),
                            "filename": _report_text(item.get("filename"), fallback="unknown"),
                            "file_type": _report_text(item.get("file_type"), fallback="file"),
                            "location_kind": _report_text(item.get("location_kind"), fallback="unknown"),
                            "stage": _report_text(item.get("stage"), fallback=""),
                            "virtual_path": _report_text(item.get("virtual_path"), fallback=""),
                            "absolute_path": _report_text(item.get("absolute_path"), fallback=""),
                            "is_final_deliverable": bool(item.get("is_final_deliverable")),
                        }
                    )
            normalized_groups.append(
                {
                    "group_id": _report_text(group.get("group_id"), fallback="artifact_group"),
                    "title_zh": _report_text(group.get("title_zh"), fallback="文件分组"),
                    "summary_zh": _report_text(group.get("summary_zh"), fallback=""),
                    "items": items,
                    "notes": _report_string_list(group.get("notes")),
                }
            )

    if normalized_groups:
        return normalized_groups

    manifest = _formal_artifact_manifest(payload)
    workspace_summary = _formal_workspace_storage_summary(payload)
    workspace_items: list[dict[str, object]] = []
    for filename, label, description, virtual_key, absolute_key in [
        (
            "workspace-run-root",
            "主工作目录",
            "该轮求解在工作区中的根目录。",
            "workspace_run_root_virtual_path",
            "workspace_run_root_absolute_path",
        ),
        (
            "openfoam-case",
            "主 OpenFOAM case",
            "主基线 case 目录。",
            "workspace_case_dir_virtual_path",
            "workspace_case_dir_absolute_path",
        ),
        (
            "Allrun",
            "执行脚本",
            "OpenFOAM 执行入口脚本。",
            "run_script_virtual_path",
            "run_script_absolute_path",
        ),
        (
            "postProcessing",
            "后处理目录",
            "后处理结果与曲线文件目录。",
            "workspace_postprocess_virtual_path",
            "workspace_postprocess_absolute_path",
        ),
        (
            "studies",
            "研究变体目录",
            "敏感性研究与变体目录。",
            "study_workspace_root_virtual_path",
            "study_workspace_root_absolute_path",
        ),
    ]:
        virtual_path = _report_text(workspace_summary.get(virtual_key), fallback="")
        absolute_path = _report_text(workspace_summary.get(absolute_key), fallback="")
        if not virtual_path and not absolute_path:
            continue
        workspace_items.append(
            {
                "label": label,
                "description": description,
                "filename": filename,
                "file_type": "directory",
                "location_kind": "workspace_intermediate",
                "stage": "solver-dispatch",
                "virtual_path": virtual_path,
                "absolute_path": absolute_path,
                "is_final_deliverable": False,
            }
        )

    return [
        {
            "group_id": "report_outputs",
            "title_zh": "报告交付文件",
            "summary_zh": "最终报告、交付门禁与研究结论说明相关文件。",
            "items": [item for item in manifest if item.get("location_kind") == "report_output"],
            "notes": [],
        },
        {
            "group_id": "solver_outputs",
            "title_zh": "求解与验证输出",
            "summary_zh": "OpenFOAM 主求解结果、稳定性证据与验证摘要。",
            "items": [item for item in manifest if item.get("location_kind") == "solver_output"],
            "notes": [],
        },
        {
            "group_id": "workspace_intermediate",
            "title_zh": "工作区与中间文件",
            "summary_zh": "用于复算与追溯的工作目录、中间文件位置及后处理目录。",
            "items": workspace_items,
            "notes": _report_string_list(workspace_summary.get("directory_notes")),
        },
    ]


def _formal_render_requested_outputs_markdown(payload: dict) -> list[str]:
    requested_outputs = payload.get("requested_outputs") or []
    if not requested_outputs:
        return ["- 预期交付：未显式声明。"]

    lines = ["", "### 预期交付"]
    for item in requested_outputs:
        if not isinstance(item, dict):
            continue
        label = _report_text(item.get("label") or item.get("output_id"), fallback="未命名输出")
        output_id = _report_text(item.get("output_id"), fallback="unknown")
        requested_label = _report_text(item.get("requested_label"), fallback="未说明")
        support_level = _report_text(item.get("support_level"), fallback="unknown")
        summary = _summarize_postprocess_spec(item.get("postprocess_spec"))
        line = f"- `{output_id}` | {label} | requested=`{requested_label}` | support=`{support_level}`"
        if summary:
            line += f" | spec=`{summary}`"
        lines.append(line)
    return lines


def _formal_render_requested_outputs_html(payload: dict) -> str:
    requested_outputs = payload.get("requested_outputs") or []
    if not requested_outputs:
        return "<p><strong>预期交付：</strong> 未显式声明。</p>"

    items = []
    for item in requested_outputs:
        if not isinstance(item, dict):
            continue
        label = _report_text(item.get("label") or item.get("output_id"), fallback="未命名输出")
        output_id = _report_text(item.get("output_id"), fallback="unknown")
        requested_label = _report_text(item.get("requested_label"), fallback="未说明")
        support_level = _report_text(item.get("support_level"), fallback="unknown")
        summary = _summarize_postprocess_spec(item.get("postprocess_spec"))
        detail = f"requested={requested_label} | support={support_level}" + (f" | spec={summary}" if summary else "")
        items.append(f"<li><strong>{escape(label)}</strong> (<code>{escape(output_id)}</code>)<p>{escape(detail)}</p></li>")
    return "<h3>预期交付</h3><ul>" + "".join(items) + "</ul>"


def _formal_render_task_conditions_markdown(payload: dict) -> list[str]:
    lines = [
        "## 计算目标与工况",
        _report_text(payload.get("summary_zh"), fallback="暂无正式 CFD 报告摘要。"),
        "",
        f"- 任务概述：{_report_text(payload.get('task_summary'), fallback='未提供任务说明。')}",
        f"- 几何族：`{_report_text(payload.get('geometry_family'), fallback='待确认')}`",
        f"- 选定案例：`{_report_text(payload.get('selected_case_id'), fallback='未固定')}`",
        f"- 任务类型：`{_report_text(payload.get('task_type'), fallback='unknown')}`",
        f"- 来源阶段：`{_report_text(payload.get('source_runtime_stage'), fallback='unknown')}`",
        f"- 复核状态：`{_report_text(payload.get('review_status'), fallback='unknown')}`",
    ]
    simulation_requirements = _formal_normalized_simulation_requirements(payload)
    if simulation_requirements:
        lines.extend(
            [
                "",
                "### 名义工况",
                f"- 来流速度：`{_report_text(simulation_requirements.get('inlet_velocity_mps'))}` m/s",
                f"- 流体密度：`{_report_text(simulation_requirements.get('fluid_density_kg_m3'))}` kg/m^3",
                (f"- 运动黏度：`{_report_text(simulation_requirements.get('kinematic_viscosity_m2ps'))}` m^2/s"),
                f"- 终止时间：`{_report_text(simulation_requirements.get('end_time_seconds'))}` s",
                f"- 时间步长：`{_report_text(simulation_requirements.get('delta_t_seconds'))}` s",
                f"- 写出间隔：`{_report_text(simulation_requirements.get('write_interval_steps'))}` steps",
            ]
        )
    lines.extend(_formal_render_requested_outputs_markdown(payload))
    return lines


def _formal_render_task_conditions_html(payload: dict) -> str:
    simulation_requirements = _formal_normalized_simulation_requirements(payload)
    simulation_block = ""
    if simulation_requirements:
        simulation_block = (
            "<h3>名义工况</h3>"
            "<ul>"
            f"<li>来流速度：<code>{escape(_report_text(simulation_requirements.get('inlet_velocity_mps')))}</code> m/s</li>"
            f"<li>流体密度：<code>{escape(_report_text(simulation_requirements.get('fluid_density_kg_m3')))}</code> kg/m^3</li>"
            f"<li>运动黏度：<code>{escape(_report_text(simulation_requirements.get('kinematic_viscosity_m2ps')))}</code> m^2/s</li>"
            f"<li>终止时间：<code>{escape(_report_text(simulation_requirements.get('end_time_seconds')))}</code> s</li>"
            f"<li>时间步长：<code>{escape(_report_text(simulation_requirements.get('delta_t_seconds')))}</code> s</li>"
            f"<li>写出间隔：<code>{escape(_report_text(simulation_requirements.get('write_interval_steps')))}</code> steps</li>"
            "</ul>"
        )
    return (
        '<section class="panel">'
        "<h2>计算目标与工况</h2>"
        f"<p>{escape(_report_text(payload.get('summary_zh'), fallback='暂无正式 CFD 报告摘要。'))}</p>"
        "<ul>"
        f"<li>任务概述：{escape(_report_text(payload.get('task_summary'), fallback='未提供任务说明。'))}</li>"
        f"<li>几何族：<code>{escape(_report_text(payload.get('geometry_family'), fallback='待确认'))}</code></li>"
        f"<li>选定案例：<code>{escape(_report_text(payload.get('selected_case_id'), fallback='未固定'))}</code></li>"
        f"<li>任务类型：<code>{escape(_report_text(payload.get('task_type'), fallback='unknown'))}</code></li>"
        f"<li>来源阶段：<code>{escape(_report_text(payload.get('source_runtime_stage'), fallback='unknown'))}</code></li>"
        f"<li>复核状态：<code>{escape(_report_text(payload.get('review_status'), fallback='unknown'))}</code></li>"
        "</ul>"
        f"{simulation_block}"
        f"{_formal_render_requested_outputs_html(payload)}"
        "</section>"
    )


def _formal_render_geometry_settings_markdown(payload: dict) -> list[str]:
    mesh_summary = _formal_normalized_mesh_summary(payload)
    residual_summary = _formal_normalized_residual_summary(payload)
    lines = [
        "",
        "## 几何、网格与计算设置",
        f"- 输入来源：`{_report_text(payload.get('input_source_type'), fallback='geometry_seed')}`",
        f"- 几何文件：`{_report_text(payload.get('geometry_virtual_path'), fallback='未提供')}`",
        f"- 官方案例：`{_report_text(payload.get('official_case_id'), fallback='未提供')}`",
        f"- 主 workspace case：`{_report_text(payload.get('workspace_case_dir_virtual_path'), fallback='当前阶段无')}`",
        f"- 运行脚本：`{_report_text(payload.get('run_script_virtual_path'), fallback='当前阶段无')}`",
    ]
    if payload.get("workspace_postprocess_virtual_path"):
        lines.append(f"- 后处理目录：`{_report_text(payload.get('workspace_postprocess_virtual_path'))}`")
    if mesh_summary:
        lines.extend(
            [
                "",
                "### 网格摘要",
                f"- mesh_ok：`{_report_text(mesh_summary.get('mesh_ok'))}`",
                f"- cells：`{_report_text(mesh_summary.get('cells'))}`",
                f"- faces：`{_report_text(mesh_summary.get('faces'))}`",
                f"- internal_faces：`{_report_text(mesh_summary.get('internal_faces'))}`",
                f"- points：`{_report_text(mesh_summary.get('points'))}`",
            ]
        )
    if residual_summary:
        lines.extend(
            [
                "",
                "### 收敛摘要",
                f"- latest_time：`{_report_text(residual_summary.get('latest_time'))}`",
                f"- max_final_residual：`{_report_text(residual_summary.get('max_final_residual'))}`",
            ]
        )
    return lines


def _formal_render_geometry_settings_html(payload: dict) -> str:
    mesh_summary = _formal_normalized_mesh_summary(payload)
    residual_summary = _formal_normalized_residual_summary(payload)
    mesh_block = ""
    if mesh_summary:
        mesh_block = (
            "<h3>网格摘要</h3><ul>"
            f"<li>mesh_ok：<code>{escape(_report_text(mesh_summary.get('mesh_ok')))}</code></li>"
            f"<li>cells：<code>{escape(_report_text(mesh_summary.get('cells')))}</code></li>"
            f"<li>faces：<code>{escape(_report_text(mesh_summary.get('faces')))}</code></li>"
            f"<li>internal_faces：<code>{escape(_report_text(mesh_summary.get('internal_faces')))}</code></li>"
            f"<li>points：<code>{escape(_report_text(mesh_summary.get('points')))}</code></li>"
            "</ul>"
        )
    residual_block = ""
    if residual_summary:
        residual_block = (
            "<h3>收敛摘要</h3><ul>"
            f"<li>latest_time：<code>{escape(_report_text(residual_summary.get('latest_time')))}</code></li>"
            f"<li>max_final_residual：<code>{escape(_report_text(residual_summary.get('max_final_residual')))}</code></li>"
            "</ul>"
        )
    postprocess_line = ""
    if payload.get("workspace_postprocess_virtual_path"):
        postprocess_line = f"<li>后处理目录： <code>{escape(_report_text(payload.get('workspace_postprocess_virtual_path')))}</code></li>"
    return (
        '<section class="panel">'
        "<h2>几何、网格与计算设置</h2>"
        "<ul>"
        f"<li>输入来源：<code>{escape(_report_text(payload.get('input_source_type'), fallback='geometry_seed'))}</code></li>"
        f"<li>几何文件：<code>{escape(_report_text(payload.get('geometry_virtual_path'), fallback='未提供'))}</code></li>"
        f"<li>官方案例：<code>{escape(_report_text(payload.get('official_case_id'), fallback='未提供'))}</code></li>"
        f"<li>主 workspace case：<code>{escape(_report_text(payload.get('workspace_case_dir_virtual_path'), fallback='当前阶段无'))}</code></li>"
        f"<li>运行脚本：<code>{escape(_report_text(payload.get('run_script_virtual_path'), fallback='当前阶段无'))}</code></li>"
        f"{postprocess_line}"
        "</ul>"
        f"{mesh_block}{residual_block}"
        "</section>"
    )


def _formal_render_official_case_traceability_markdown(payload: dict) -> list[str]:
    if _report_text(payload.get("input_source_type"), fallback="") != "openfoam_case_seed":
        return []

    profile = (
        payload.get("official_case_profile")
        if isinstance(payload.get("official_case_profile"), dict)
        else {}
    )
    provenance = (
        payload.get("provenance_summary")
        if isinstance(payload.get("provenance_summary"), dict)
        else {}
    )
    file_sources = (
        provenance.get("file_sources")
        if isinstance(provenance.get("file_sources"), dict)
        else {}
    )
    command_chain = (
        profile.get("command_chain")
        if isinstance(profile.get("command_chain"), list)
        else []
    )
    solver_metrics = payload.get("solver_metrics") if isinstance(payload.get("solver_metrics"), dict) else {}
    lines = [
        "",
        "### 官方案例追溯",
        f"- official_case_id：`{_report_text(payload.get('official_case_id'), fallback='未提供')}`",
        f"- source_commit：`{_report_text(profile.get('source_commit'), fallback='未提供')}`",
        f"- source_kind：`{_report_text(profile.get('source_kind'), fallback='未提供')}`",
    ]
    seed_paths = _report_string_list(payload.get("official_case_seed_virtual_paths"))
    if seed_paths:
        lines.extend(
            [
                "",
                "### Imported Seeds",
                *(f"- `{path}`" for path in seed_paths),
            ]
        )
    source_paths = _report_string_list(profile.get("source_paths"))
    if source_paths:
        lines.extend(
            [
                "",
                "### 官方基线路径",
                *(f"- `{path}`" for path in source_paths),
            ]
        )
    if command_chain:
        lines.extend(
            [
                "",
                "### Execution Profile",
                *(f"- `{command}`" for command in command_chain if isinstance(command, str)),
            ]
        )
    if file_sources:
        lines.extend(
            [
                "",
                "### 核心文件来源",
                *(
                    f"- `{relative_path}` | source_kind=`{_report_text(source.get('source_kind'), fallback='unknown')}`"
                    f" | source_path=`{_report_text(source.get('source_path'), fallback='未提供')}`"
                    f" | imported_virtual_path=`{_report_text(source.get('imported_virtual_path'), fallback='--')}`"
                    for relative_path, source in list(file_sources.items())[:6]
                    if isinstance(source, dict)
                ),
            ]
        )
    if solver_metrics:
        lines.extend(
            [
                "",
                "### Completion State",
                f"- solver_completed：`{_report_text(solver_metrics.get('solver_completed'), fallback='unknown')}`",
                f"- final_time_seconds：`{_report_text(solver_metrics.get('final_time_seconds'), fallback='未提供')}`",
            ]
        )
    return lines


def _formal_render_official_case_traceability_html(payload: dict) -> str:
    markdown_lines = _formal_render_official_case_traceability_markdown(payload)
    if not markdown_lines:
        return ""
    sections: list[str] = []
    current_heading = None
    current_items: list[str] = []
    for line in markdown_lines:
        if not line:
            continue
        if line.startswith("### "):
            if current_heading is not None:
                sections.append(
                    f"<h3>{escape(current_heading)}</h3><ul>{''.join(current_items)}</ul>"
                )
            current_heading = line.removeprefix("### ").strip()
            current_items = []
            continue
        if line.startswith("- "):
            current_items.append(f"<li>{escape(line.removeprefix('- ').strip())}</li>")
    if current_heading is not None:
        sections.append(
            f"<h3>{escape(current_heading)}</h3><ul>{''.join(current_items)}</ul>"
        )
    return "".join(sections)


def _formal_render_official_case_parity_markdown(payload: dict) -> list[str]:
    if _report_text(payload.get("input_source_type"), fallback="") != "openfoam_case_seed":
        return []

    parity = (
        payload.get("official_case_validation_assessment")
        if isinstance(payload.get("official_case_validation_assessment"), dict)
        else {}
    )
    if not parity:
        return []

    lines = [
        "",
        "### Official Case Parity",
        f"- parity_status: `{_report_text(parity.get('parity_status'), fallback='unknown')}`",
        f"- parity_artifact: `{_report_text(payload.get('official_case_validation_virtual_path'), fallback='not-recorded')}`",
    ]
    lines.extend(
        f"- passed_check: {item}"
        for item in _report_string_list(parity.get("passed_checks"))
    )
    lines.extend(
        f"- drift_reason: {item}"
        for item in _report_string_list(parity.get("drift_reasons"))
    )
    return lines


def _formal_render_official_case_parity_html(payload: dict) -> str:
    markdown_lines = _formal_render_official_case_parity_markdown(payload)
    if not markdown_lines:
        return ""

    items = [
        f"<li>{escape(line.removeprefix('- ').strip())}</li>"
        for line in markdown_lines
        if line.startswith("- ")
    ]
    if not items:
        return ""

    return "<h3>Official Case Parity</h3><ul>" + "".join(items) + "</ul>"


def _formal_render_results_validation_markdown(payload: dict) -> list[str]:
    overview = _report_overview(payload)
    highlights = _delivery_highlights(payload)
    sections = _conclusion_sections(payload)
    evidence_index = _evidence_index(payload)
    acceptance = payload.get("acceptance_assessment") or {}
    scientific_verification = payload.get("scientific_verification_assessment") or {}
    research_evidence = payload.get("research_evidence_summary") or {}
    scientific_gate = payload.get("scientific_supervisor_gate") or {}

    lines = [
        "",
        "## 结果、验证与结论边界",
        _report_text(overview.get("current_conclusion_zh"), fallback="暂无正式结论。"),
        "",
        "### 关键指标与代表图表",
    ]
    metric_lines = _report_string_list(highlights.get("metric_lines"))
    lines.extend(f"- {item}" for item in (metric_lines or ["暂无关键指标摘要。"]))
    figure_titles = _report_string_list(highlights.get("figure_titles"))
    lines.extend(
        [
            "",
            "#### 代表图表",
            *(f"- {item}" for item in (figure_titles or ["暂无代表图表。"])),
        ]
    )
    highlight_paths = _report_string_list(highlights.get("highlight_artifact_virtual_paths"))
    if highlight_paths:
        lines.extend(
            [
                "",
                "#### 高亮产物",
                *(f"- `{path}`" for path in highlight_paths),
            ]
        )

    lines.extend(["", "### 结论与证据"])
    for section in sections:
        evidence_gap_notes = _report_string_list(section.get("evidence_gap_notes"))
        artifact_paths = _report_string_list(section.get("artifact_virtual_paths"))
        lines.extend(
            [
                "",
                f"#### {_report_text(section.get('title_zh'), fallback='当前研究结论')}",
                _report_text(section.get("summary_zh"), fallback="暂无结论说明。"),
                f"- 来源：{_formal_markdown_inline_paths(_report_string_list(section.get('inline_source_refs')))}",
                f"- Claim level：`{_report_text(section.get('claim_level'), fallback='delivery_only')}`",
                f"- 置信度：{_report_text(section.get('confidence_label'), fallback='--')}",
                ("- 证据缺口：" + ("；".join(evidence_gap_notes) if evidence_gap_notes else "暂无")),
                f"- 关联产物：{_formal_markdown_inline_paths(artifact_paths)}",
            ]
        )

    lines.extend(
        [
            "",
            "### 验证与交付判定",
            f"- review_status：`{_report_text(overview.get('review_status'), fallback='unknown')}`",
            f"- allowed_claim_level：`{_report_text(overview.get('allowed_claim_level'), fallback='delivery_only')}`",
            f"- reproducibility_status：`{_report_text(overview.get('reproducibility_status'), fallback='unknown')}`",
        ]
    )
    if isinstance(acceptance, dict) and acceptance:
        lines.extend(
            [
                f"- acceptance_status：`{_report_text(acceptance.get('status'), fallback='unknown')}`",
                f"- acceptance_confidence：`{_report_text(acceptance.get('confidence'), fallback='unknown')}`",
            ]
        )
        lines.extend(f"- blocking_issue：{item}" for item in _report_string_list(acceptance.get("blocking_issues")))
        lines.extend(f"- warning：{item}" for item in _report_string_list(acceptance.get("warnings")))
    if isinstance(scientific_verification, dict) and scientific_verification:
        lines.extend(
            [
                f"- scientific_verification_status：`{_report_text(scientific_verification.get('status'), fallback='unknown')}`",
                f"- scientific_verification_confidence：`{_report_text(scientific_verification.get('confidence'), fallback='unknown')}`",
            ]
        )
        lines.extend(f"- missing_evidence：{item}" for item in _report_string_list(scientific_verification.get("missing_evidence")))
    if isinstance(research_evidence, dict) and research_evidence:
        lines.append(f"- research_readiness_status：`{_report_text(research_evidence.get('readiness_status'), fallback='unknown')}`")
        lines.extend(f"- evidence_gap：{item}" for item in _report_string_list(research_evidence.get("evidence_gaps")))
    if isinstance(scientific_gate, dict) and scientific_gate:
        lines.append(f"- scientific_gate_status：`{_report_text(scientific_gate.get('gate_status'), fallback='unknown')}`")

    lines.extend(["", "### 证据索引"])
    for group in evidence_index:
        lines.extend(
            [
                "",
                f"#### {_report_text(group.get('group_title_zh'), fallback='证据分组')}",
                *(f"- `{path}`" for path in (_report_string_list(group.get("artifact_virtual_paths")) or ["暂无分组产物。"])),
            ]
        )
        provenance_manifest_virtual_path = _report_text(
            group.get("provenance_manifest_virtual_path"),
            fallback="",
        )
        if provenance_manifest_virtual_path:
            lines.append(f"- provenance_manifest_virtual_path：`{provenance_manifest_virtual_path}`")
    return lines


def _formal_render_results_validation_html(payload: dict) -> str:
    overview = _report_overview(payload)
    highlights = _delivery_highlights(payload)
    sections = _conclusion_sections(payload)
    evidence_index = _evidence_index(payload)
    acceptance = payload.get("acceptance_assessment") or {}
    scientific_verification = payload.get("scientific_verification_assessment") or {}
    research_evidence = payload.get("research_evidence_summary") or {}
    scientific_gate = payload.get("scientific_supervisor_gate") or {}

    metric_lines = _report_string_list(highlights.get("metric_lines"))
    figure_titles = _report_string_list(highlights.get("figure_titles"))
    highlight_paths = _report_string_list(highlights.get("highlight_artifact_virtual_paths"))

    conclusion_cards = []
    for section in sections:
        evidence_gap_notes = _report_string_list(section.get("evidence_gap_notes"))
        artifact_paths = _report_string_list(section.get("artifact_virtual_paths"))
        conclusion_cards.append(
            '<article class="detail-card">'
            f"<h4>{escape(_report_text(section.get('title_zh'), fallback='当前研究结论'))}</h4>"
            f"<p>{escape(_report_text(section.get('summary_zh'), fallback='暂无结论说明。'))}</p>"
            f"<p><strong>来源：</strong> {_formal_html_inline_paths(_report_string_list(section.get('inline_source_refs')))}</p>"
            f"<p><strong>Claim level：</strong> <code>{escape(_report_text(section.get('claim_level'), fallback='delivery_only'))}</code></p>"
            f"<p><strong>置信度：</strong> {escape(_report_text(section.get('confidence_label'), fallback='--'))}</p>"
            f"<p><strong>证据缺口：</strong> {escape('；'.join(evidence_gap_notes) if evidence_gap_notes else '暂无')}</p>"
            f"<p><strong>关联产物：</strong> {_formal_html_inline_paths(artifact_paths)}</p>"
            "</article>"
        )

    validation_items = [
        f"<li>review_status：<code>{escape(_report_text(overview.get('review_status'), fallback='unknown'))}</code></li>",
        f"<li>allowed_claim_level：<code>{escape(_report_text(overview.get('allowed_claim_level'), fallback='delivery_only'))}</code></li>",
        f"<li>reproducibility_status：<code>{escape(_report_text(overview.get('reproducibility_status'), fallback='unknown'))}</code></li>",
    ]
    if isinstance(acceptance, dict) and acceptance:
        validation_items.extend(
            [
                f"<li>acceptance_status：<code>{escape(_report_text(acceptance.get('status'), fallback='unknown'))}</code></li>",
                f"<li>acceptance_confidence：<code>{escape(_report_text(acceptance.get('confidence'), fallback='unknown'))}</code></li>",
            ]
        )
        validation_items.extend(f"<li>blocking_issue：{escape(item)}</li>" for item in _report_string_list(acceptance.get("blocking_issues")))
        validation_items.extend(f"<li>warning：{escape(item)}</li>" for item in _report_string_list(acceptance.get("warnings")))
    if isinstance(scientific_verification, dict) and scientific_verification:
        validation_items.extend(
            [
                f"<li>scientific_verification_status：<code>{escape(_report_text(scientific_verification.get('status'), fallback='unknown'))}</code></li>",
                f"<li>scientific_verification_confidence：<code>{escape(_report_text(scientific_verification.get('confidence'), fallback='unknown'))}</code></li>",
            ]
        )
        validation_items.extend(f"<li>missing_evidence：{escape(item)}</li>" for item in _report_string_list(scientific_verification.get("missing_evidence")))
    if isinstance(research_evidence, dict) and research_evidence:
        validation_items.append(f"<li>research_readiness_status：<code>{escape(_report_text(research_evidence.get('readiness_status'), fallback='unknown'))}</code></li>")
        validation_items.extend(f"<li>evidence_gap：{escape(item)}</li>" for item in _report_string_list(research_evidence.get("evidence_gaps")))
    if isinstance(scientific_gate, dict) and scientific_gate:
        validation_items.append(f"<li>scientific_gate_status：<code>{escape(_report_text(scientific_gate.get('gate_status'), fallback='unknown'))}</code></li>")

    evidence_groups = []
    for group in evidence_index:
        artifact_paths = _report_string_list(group.get("artifact_virtual_paths"))
        provenance_manifest_virtual_path = _report_text(
            group.get("provenance_manifest_virtual_path"),
            fallback="",
        )
        group_items = "".join(f"<li><code>{escape(path)}</code></li>" for path in (artifact_paths or ["暂无分组产物。"]))
        if provenance_manifest_virtual_path:
            group_items += f"<li><strong>provenance_manifest_virtual_path：</strong> <code>{escape(provenance_manifest_virtual_path)}</code></li>"
        evidence_groups.append(f'<div class="detail-card"><h4>{escape(_report_text(group.get("group_title_zh"), fallback="证据分组"))}</h4><ul>{group_items}</ul></div>')

    highlight_block = ""
    if highlight_paths:
        highlight_block = "<h4>高亮产物</h4><ul>" + "".join(f"<li><code>{escape(path)}</code></li>" for path in highlight_paths) + "</ul>"

    return (
        '<section class="panel">'
        "<h2>结果、验证与结论边界</h2>"
        f"<p>{escape(_report_text(overview.get('current_conclusion_zh'), fallback='暂无正式结论。'))}</p>"
        "<h3>关键指标与代表图表</h3>"
        f"<ul>{_render_html_list(metric_lines, '暂无关键指标摘要。')}</ul>"
        "<h4>代表图表</h4>"
        f"<ul>{_render_html_list(figure_titles, '暂无代表图表。')}</ul>"
        f"{highlight_block}"
        "<h3>结论与证据</h3>"
        + ("".join(conclusion_cards) or "<p>暂无结论条目。</p>")
        + "<h3>验证与交付判定</h3>"
        + f"<ul>{''.join(validation_items)}</ul>"
        + "<h3>证据索引</h3>"
        + ("".join(evidence_groups) or "<p>暂无证据索引。</p>")
        + "</section>"
    )


def _formal_render_traceability_markdown(payload: dict) -> list[str]:
    reproducibility_summary = payload.get("reproducibility_summary") or {}
    followup_summary = payload.get("scientific_followup_summary") or {}
    lines = [
        "",
        "## 可复现性与追溯",
        f"- reproducibility_status：`{_report_text(reproducibility_summary.get('reproducibility_status') or reproducibility_summary.get('parity_status'), fallback='unknown')}`",
        f"- provenance_manifest_virtual_path：`{_report_text(payload.get('provenance_manifest_virtual_path'), fallback='')}`",
        f"- source_report_virtual_path：`{_report_text(payload.get('source_report_virtual_path'), fallback='')}`",
    ]
    lines.extend(_formal_render_official_case_traceability_markdown(payload))
    lines.extend(_formal_render_official_case_parity_markdown(payload))
    source_artifact_virtual_paths = _report_string_list(payload.get("source_artifact_virtual_paths"))
    if source_artifact_virtual_paths:
        lines.extend(
            [
                "",
                "### 来源产物",
                *(f"- `{path}`" for path in source_artifact_virtual_paths),
            ]
        )
    if isinstance(followup_summary, dict):
        history_virtual_path = _report_text(followup_summary.get("history_virtual_path"), fallback="")
        if history_virtual_path:
            lines.extend(
                [
                    "",
                    "### 跟进链路",
                    f"- history_virtual_path：`{history_virtual_path}`",
                ]
            )
        return lines
    return lines


def _formal_render_traceability_html(payload: dict) -> str:
    reproducibility_summary = payload.get("reproducibility_summary") or {}
    followup_summary = payload.get("scientific_followup_summary") or {}
    source_artifact_virtual_paths = _report_string_list(payload.get("source_artifact_virtual_paths"))
    source_block = ""
    if source_artifact_virtual_paths:
        source_block = "<h3>来源产物</h3><ul>" + "".join(f"<li><code>{escape(path)}</code></li>" for path in source_artifact_virtual_paths) + "</ul>"
    followup_block = ""
    if isinstance(followup_summary, dict):
        history_virtual_path = _report_text(followup_summary.get("history_virtual_path"), fallback="")
        if history_virtual_path:
            followup_block = f"<h3>跟进链路</h3><ul><li><strong>history_virtual_path：</strong> <code>{escape(history_virtual_path)}</code></li></ul>"
    return (
        '<section class="panel">'
        "<h2>可复现性与追溯</h2>"
        "<ul>"
        f"<li>reproducibility_status：<code>{escape(_report_text(reproducibility_summary.get('reproducibility_status') or reproducibility_summary.get('parity_status'), fallback='unknown'))}</code></li>"
        f"<li>provenance_manifest_virtual_path：<code>{escape(_report_text(payload.get('provenance_manifest_virtual_path'), fallback=''))}</code></li>"
        f"<li>source_report_virtual_path：<code>{escape(_report_text(payload.get('source_report_virtual_path'), fallback=''))}</code></li>"
        "</ul>"
        f"{_formal_render_official_case_traceability_html(payload)}{_formal_render_official_case_parity_html(payload)}{source_block}{followup_block}"
        "</section>"
    )


def _formal_render_artifact_manifest_markdown(payload: dict) -> list[str]:
    manifest = _formal_artifact_manifest(payload)
    lines = ["", "## 文件清单与路径索引"]
    if not manifest:
        lines.append("- 暂无文件清单。")
        return lines
    for item in manifest:
        lines.extend(
            [
                "",
                f"### `{item['filename']}`",
                f"- 标签：{item['label']}",
                f"- 用途：{item['description']}",
                f"- 类型：`{item['file_type']}`",
                f"- 位置分类：`{item['location_kind']}`",
                f"- 所属阶段：`{item['stage']}`",
                f"- 虚拟路径：`{item['virtual_path']}`",
                f"- 绝对路径：`{item['absolute_path']}`",
                f"- 最终交付：`{'yes' if item['is_final_deliverable'] else 'no'}`",
            ]
        )
    return lines


def _formal_render_artifact_manifest_html(payload: dict) -> str:
    manifest = _formal_artifact_manifest(payload)
    if not manifest:
        return '<section class="panel"><h2>文件清单与路径索引</h2><p>暂无文件清单。</p></section>'
    cards = []
    for item in manifest:
        cards.append(
            '<article class="detail-card">'
            f"<h3><code>{escape(str(item['filename']))}</code></h3>"
            "<ul>"
            f"<li>标签：{escape(str(item['label']))}</li>"
            f"<li>用途：{escape(str(item['description']))}</li>"
            f"<li>类型：<code>{escape(str(item['file_type']))}</code></li>"
            f"<li>位置分类：<code>{escape(str(item['location_kind']))}</code></li>"
            f"<li>所属阶段：<code>{escape(str(item['stage']))}</code></li>"
            f"<li>虚拟路径：<code>{escape(str(item['virtual_path']))}</code></li>"
            f"<li>绝对路径：<code>{escape(str(item['absolute_path']))}</code></li>"
            f"<li>最终交付：<code>{'yes' if item['is_final_deliverable'] else 'no'}</code></li>"
            "</ul>"
            "</article>"
        )
    return '<section class="panel"><h2>文件清单与路径索引</h2>' + "".join(cards) + "</section>"


def _formal_render_next_steps_markdown(payload: dict, overview: dict[str, object]) -> list[str]:
    suggestions = _report_string_list(
        [
            _report_text(
                overview.get("recommended_next_step_zh"),
                fallback="回到聊天中确认下一步研究动作。",
            ),
            *_build_dynamic_report_recommendations(payload),
        ]
    )
    followup_summary = payload.get("scientific_followup_summary") or {}
    lines = ["", "## 建议下一步"]
    lines.extend(f"- {item}" for item in suggestions)
    for label, value in [
        ("next_recommended_stage", payload.get("next_recommended_stage")),
        ("source_report_virtual_path", payload.get("source_report_virtual_path")),
        (
            "supervisor_handoff_virtual_path",
            payload.get("supervisor_handoff_virtual_path"),
        ),
        (
            "history_virtual_path",
            followup_summary.get("history_virtual_path") if isinstance(followup_summary, dict) else None,
        ),
    ]:
        text = _report_text(value, fallback="")
        if text:
            lines.append(f"- {label}：`{text}`")
    return lines


def _formal_render_next_steps_html(payload: dict, overview: dict[str, object]) -> str:
    suggestions = _report_string_list(
        [
            _report_text(
                overview.get("recommended_next_step_zh"),
                fallback="回到聊天中确认下一步研究动作。",
            ),
            *_build_dynamic_report_recommendations(payload),
        ]
    )
    followup_summary = payload.get("scientific_followup_summary") or {}
    detail_items = []
    for label, value in [
        ("next_recommended_stage", payload.get("next_recommended_stage")),
        ("source_report_virtual_path", payload.get("source_report_virtual_path")),
        (
            "supervisor_handoff_virtual_path",
            payload.get("supervisor_handoff_virtual_path"),
        ),
        (
            "history_virtual_path",
            followup_summary.get("history_virtual_path") if isinstance(followup_summary, dict) else None,
        ),
    ]:
        text = _report_text(value, fallback="")
        if text:
            detail_items.append(f"<li><strong>{escape(label)}：</strong> <code>{escape(text)}</code></li>")
    return f'<section class="panel"><h2>建议下一步</h2><ul>{_render_html_list(suggestions, "回到聊天中确认下一步研究动作。")}</ul>' + (f"<ul>{''.join(detail_items)}</ul>" if detail_items else "") + "</section>"


def _formal_render_artifact_manifest_markdown_compact(payload: dict) -> list[str]:
    groups = _formal_artifact_group_summary(payload)
    lines = ["", "## \u6587\u4ef6\u6e05\u5355\u4e0e\u8def\u5f84\u7d22\u5f15"]
    for group in groups:
        lines.extend(["", f"### {_report_text(group.get('title_zh'), fallback='\\u6587\\u4ef6\\u5206\\u7ec4')}"])
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            lines.append(summary)
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            lines.append("- \u6682\u65e0\u76f8\u5173\u6587\u4ef6\u3002")
        else:
            for item in items:
                if not isinstance(item, dict):
                    continue
                lines.extend(
                    [
                        "",
                        f"#### `{_report_text(item.get('filename'), fallback='unknown')}`",
                        f"- \u6807\u7b7e\uff1a{_report_text(item.get('label'), fallback='\\u672a\\u547d\\u540d\\u6587\\u4ef6')}",
                        f"- \u7528\u9014\uff1a{_report_text(item.get('description'), fallback='\\u6682\\u65e0\\u8bf4\\u660e')}",
                    ]
                )
                for label, key in [
                    ("\u7c7b\u578b", "file_type"),
                    ("\u4f4d\u7f6e\u5206\u7c7b", "location_kind"),
                    ("\u6240\u5c5e\u9636\u6bb5", "stage"),
                    ("\u865a\u62df\u8def\u5f84", "virtual_path"),
                    ("\u7edd\u5bf9\u8def\u5f84", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        lines.append(f"- {label}\uff1a`{value}`")
                if "is_final_deliverable" in item:
                    lines.append(f"- \u6700\u7ec8\u4ea4\u4ed8\uff1a`{'yes' if bool(item.get('is_final_deliverable')) else 'no'}`")
        notes = _report_string_list(group.get("notes"))
        if notes:
            lines.extend(["", "#### \u8bf4\u660e"])
            lines.extend(f"- {item}" for item in notes)
    return lines


def _formal_render_artifact_manifest_html_compact(payload: dict) -> str:
    groups = _formal_artifact_group_summary(payload)
    sections = ['<section class="panel">', "<h2>\u6587\u4ef6\u6e05\u5355\u4e0e\u8def\u5f84\u7d22\u5f15</h2>"]
    for group in groups:
        sections.append(f"<h3>{escape(_report_text(group.get('title_zh'), fallback='\\u6587\\u4ef6\\u5206\\u7ec4'))}</h3>")
        summary = _report_text(group.get("summary_zh"), fallback="")
        if summary:
            sections.append(f"<p>{escape(summary)}</p>")
        items = group.get("items") if isinstance(group, dict) else []
        if not items:
            sections.append("<p>\u6682\u65e0\u76f8\u5173\u6587\u4ef6\u3002</p>")
        else:
            cards = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                detail_items = [
                    f"<li>\u6807\u7b7e\uff1a{escape(_report_text(item.get('label'), fallback='\\u672a\\u547d\\u540d\\u6587\\u4ef6'))}</li>",
                    f"<li>\u7528\u9014\uff1a{escape(_report_text(item.get('description'), fallback='\\u6682\\u65e0\\u8bf4\\u660e'))}</li>",
                ]
                for label, key in [
                    ("\u7c7b\u578b", "file_type"),
                    ("\u4f4d\u7f6e\u5206\u7c7b", "location_kind"),
                    ("\u6240\u5c5e\u9636\u6bb5", "stage"),
                    ("\u865a\u62df\u8def\u5f84", "virtual_path"),
                    ("\u7edd\u5bf9\u8def\u5f84", "absolute_path"),
                ]:
                    value = _report_text(item.get(key), fallback="")
                    if value:
                        detail_items.append(f"<li>{escape(label)}\uff1a<code>{escape(value)}</code></li>")
                if "is_final_deliverable" in item:
                    detail_items.append(f"<li>\u6700\u7ec8\u4ea4\u4ed8\uff1a<code>{'yes' if bool(item.get('is_final_deliverable')) else 'no'}</code></li>")
                cards.append(f'<article class="detail-card"><h4><code>{escape(_report_text(item.get("filename"), fallback="unknown"))}</code></h4><ul>{"".join(detail_items)}</ul></article>')
            sections.append("".join(cards))
        notes = _report_string_list(group.get("notes"))
        if notes:
            sections.append("<h4>\u8bf4\u660e</h4>")
            sections.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in notes) + "</ul>")
    sections.append("</section>")
    return "".join(sections)


def render_markdown(payload: dict) -> str:
    overview = _report_overview(payload)
    lines = [
        f"# {_report_text(payload.get('report_title'), fallback='Submarine CFD Final Report')}",
        "",
    ]
    lines.extend(_formal_render_task_conditions_markdown(payload))
    lines.extend(_formal_render_geometry_settings_markdown(payload))
    lines.extend(_formal_render_results_validation_markdown(payload))
    lines.extend(_formal_render_traceability_markdown(payload))
    lines.extend(_formal_render_artifact_manifest_markdown_compact(payload))
    lines.extend(_formal_render_next_steps_markdown(payload, overview))
    lines.append("")
    return "\n".join(lines)


def render_html(payload: dict) -> str:
    overview = _report_overview(payload)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(_report_text(payload.get("report_title"), fallback="Submarine CFD Final Report"))}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: #f7f8fa;
        color: #111827;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}
      .detail-card {{
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        background: #f8fafc;
        margin-top: 12px;
      }}
      h1, h2, h3, h4 {{ margin: 0 0 12px; }}
      p {{ line-height: 1.7; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li {{ margin-bottom: 8px; }}
      strong {{ color: #0f172a; }}
      code {{
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      }}
    </style>
  </head>
  <body>
    <section class="panel">
      <h1>{escape(_report_text(payload.get("report_title"), fallback="Submarine CFD Final Report"))}</h1>
      <p>{escape(_report_text(payload.get("summary_zh"), fallback="No summary available."))}</p>
    </section>
    {_formal_render_task_conditions_html(payload)}
    {_formal_render_geometry_settings_html(payload)}
    {_formal_render_results_validation_html(payload)}
    {_formal_render_traceability_html(payload)}
    {_formal_render_artifact_manifest_html_compact(payload)}
    {_formal_render_next_steps_html(payload, overview)}
  </body>
</html>
"""


__all__ = ["render_delivery_readiness_markdown", "render_html", "render_markdown"]
