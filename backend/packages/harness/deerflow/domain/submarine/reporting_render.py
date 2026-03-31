"""Markdown and HTML render helpers for submarine result reporting."""

from __future__ import annotations

from html import escape


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
        lines.extend(
            f"- `{gate.get('id')}` | `{gate.get('status')}` | {gate.get('detail')}"
            for gate in gates
        )

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
    gate_items = "".join(
        "<li>"
        f"<strong>{escape(str(gate.get('label')))}</strong> "
        f"({escape(str(gate.get('status')))})"
        f"<p>{escape(str(gate.get('detail')))}</p>"
        "</li>"
        for gate in gates
    ) or "<li>None</li>"

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
                for item in (acceptance_assessment.get('benchmark_comparisons') or [])
            )
            or "<li>None</li>"
        )
        + "</ul>"
        "</section>"
    )


def _render_output_delivery_html(output_delivery_plan: list[dict] | None) -> str:
    if not output_delivery_plan:
        return ""

    items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('label') or item.get('output_id')))}</strong> "
        f"(<code>{escape(str(item.get('delivery_status')))}</code>)"
        f"<p>{escape(str(item.get('detail') or 'No detail'))}</p>"
        "</li>"
        for item in output_delivery_plan
    ) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Requested Output Delivery</h2>"
        f"<ul>{items}</ul>"
        "</section>"
    )


def _render_figure_delivery_html(figure_delivery_summary: dict | None) -> str:
    if not figure_delivery_summary:
        return ""

    items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('title') or item.get('output_id')))}</strong> "
        f"(<code>{escape(str(item.get('render_status')))}</code>)"
        f"<p>{escape(str(item.get('caption') or 'No caption'))}</p>"
        f"<p>{escape(str(item.get('selector_summary') or 'No selector provenance'))}</p>"
        "</li>"
        for item in (figure_delivery_summary.get("figures") or [])
    ) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Figure Delivery</h2>"
        f"<p><strong>manifest:</strong> {escape(str(figure_delivery_summary.get('manifest_virtual_path') or '--'))}</p>"
        f"<p><strong>figure_count:</strong> {escape(str(figure_delivery_summary.get('figure_count') or 0))}</p>"
        f"<ul>{items}</ul>"
        "</section>"
    )


def _render_scientific_study_markdown(scientific_study_summary: dict | None) -> list[str]:
    if not scientific_study_summary:
        return []

    lines = [
        "",
        "## Scientific Studies",
        f"- execution_status: `{scientific_study_summary.get('study_execution_status')}`",
        f"- manifest: `{scientific_study_summary.get('manifest_virtual_path')}`",
    ]
    studies = scientific_study_summary.get("studies") or []
    if studies:
        lines.extend(["", "### Study Summary"])
        lines.extend(
            (
                "- "
                + " | ".join(
                    [
                        f"`{item.get('study_type')}`",
                        f"verification=`{item.get('verification_status')}`",
                        f"variants={item.get('variant_count')}",
                        str(item.get("verification_detail") or "No detail"),
                    ]
                )
            )
            for item in studies
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
        f"- baseline_run_id: `{experiment_summary.get('baseline_run_id')}`",
        f"- run_count: `{experiment_summary.get('run_count')}`",
        f"- linkage_status: `{experiment_summary.get('linkage_status')}`",
        f"- manifest: `{experiment_summary.get('manifest_virtual_path')}`",
    ]
    if experiment_summary.get("study_manifest_virtual_path"):
        lines.append(
            f"- study_manifest: `{experiment_summary.get('study_manifest_virtual_path')}`"
        )
    if experiment_summary.get("compare_virtual_path"):
        lines.append(
            f"- compare: `{experiment_summary.get('compare_virtual_path')}`"
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
        f"- compare: `{experiment_compare_summary.get('compare_virtual_path')}`",
    ]
    comparisons = experiment_compare_summary.get("comparisons") or []
    if comparisons:
        lines.extend(["", "### Compare Entries"])
        for item in comparisons:
            if not isinstance(item, dict):
                continue
            metric_lines = _format_compare_metric_delta_lines(item.get("metric_deltas"))
            detail = " | ".join(metric_lines) if metric_lines else str(item.get("notes") or "No metric delta")
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"`{item.get('candidate_run_id')}`",
                        f"`{item.get('compare_status')}`",
                        str(item.get("study_type") or "--"),
                        str(item.get("variant_id") or "--"),
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
        (
            f"- recommended_action_id: "
            f"`{scientific_remediation_handoff.get('recommended_action_id') or 'none'}`"
        ),
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
        (
            f"- latest_recommended_action_id: "
            f"`{scientific_followup_summary.get('latest_recommended_action_id') or 'none'}`"
        ),
        f"- latest_tool_name: `{scientific_followup_summary.get('latest_tool_name') or 'none'}`",
        (
            f"- latest_dispatch_stage_status: "
            f"`{scientific_followup_summary.get('latest_dispatch_stage_status') or 'none'}`"
        ),
        f"- report_refreshed: `{scientific_followup_summary.get('report_refreshed')}`",
        f"- history: `{scientific_followup_summary.get('history_virtual_path')}`",
    ]
    if scientific_followup_summary.get("latest_result_report_virtual_path"):
        lines.append(
            f"- latest_result_report: "
            f"`{scientific_followup_summary.get('latest_result_report_virtual_path')}`"
        )
    if scientific_followup_summary.get("latest_result_supervisor_handoff_virtual_path"):
        lines.append(
            f"- latest_result_handoff: "
            f"`{scientific_followup_summary.get('latest_result_supervisor_handoff_virtual_path')}`"
        )
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

    passed_requirements = (
        scientific_verification_assessment.get("passed_requirements") or []
    )
    if passed_requirements:
        lines.extend(["", "### Passed Requirements"])
        lines.extend(f"- {item}" for item in passed_requirements)

    return lines


def _render_scientific_study_html(scientific_study_summary: dict | None) -> str:
    if not scientific_study_summary:
        return ""

    study_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('summary_label') or item.get('study_type')))}</strong> "
        f"(<code>{escape(str(item.get('verification_status')))}</code>)"
        f"<p>{escape(str(item.get('verification_detail') or 'No detail'))}</p>"
        "</li>"
        for item in (scientific_study_summary.get("studies") or [])
    ) or "<li>None</li>"

    return (
        '<section class="panel">'
        "<h2>Scientific Studies</h2>"
        f"<p><strong>execution_status:</strong> {escape(str(scientific_study_summary.get('study_execution_status')))}</p>"
        f"<p><strong>manifest:</strong> {escape(str(scientific_study_summary.get('manifest_virtual_path')))}</p>"
        "<h3>Study Summary</h3>"
        f"<ul>{study_items}</ul>"
        "</section>"
    )


def _render_experiment_html(experiment_summary: dict | None) -> str:
    if not experiment_summary:
        return ""

    compare_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (experiment_summary.get("compare_notes") or [])
    ) or "<li>None</li>"
    linkage_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (experiment_summary.get("linkage_issues") or [])
    ) or "<li>None</li>"
    compare_html = (
        f"<p><strong>compare:</strong> {escape(str(experiment_summary.get('compare_virtual_path')))}</p>"
        if experiment_summary.get("compare_virtual_path")
        else ""
    )
    study_manifest_html = (
        f"<p><strong>study_manifest:</strong> {escape(str(experiment_summary.get('study_manifest_virtual_path')))}</p>"
        if experiment_summary.get("study_manifest_virtual_path")
        else ""
    )
    expected_variant_run_ids = [
        str(item)
        for item in (experiment_summary.get("expected_variant_run_ids") or [])
        if str(item)
    ]
    coverage_html = ""
    if expected_variant_run_ids:
        coverage_html = (
            "<h3>Planned Variant Coverage</h3>"
            f"<p><strong>expected_variant_run_ids:</strong> {escape(', '.join(expected_variant_run_ids))}</p>"
            f"<p><strong>recorded_variant_run_ids:</strong> {escape(', '.join(str(item) for item in (experiment_summary.get('recorded_variant_run_ids') or [])) or '--')}</p>"
            f"<p><strong>compared_variant_run_ids:</strong> {escape(', '.join(str(item) for item in (experiment_summary.get('compared_variant_run_ids') or [])) or '--')}</p>"
        )
    return (
        '<section class="panel">'
        "<h2>Experiment Registry</h2>"
        f"<p><strong>experiment_id:</strong> {escape(str(experiment_summary.get('experiment_id')))}</p>"
        f"<p><strong>experiment_status:</strong> {escape(str(experiment_summary.get('experiment_status')))}</p>"
        f"<p><strong>baseline_run_id:</strong> {escape(str(experiment_summary.get('baseline_run_id')))}</p>"
        f"<p><strong>run_count:</strong> {escape(str(experiment_summary.get('run_count')))}</p>"
        f"<p><strong>linkage_status:</strong> {escape(str(experiment_summary.get('linkage_status')))}</p>"
        f"<p><strong>manifest:</strong> {escape(str(experiment_summary.get('manifest_virtual_path')))}</p>"
        f"{study_manifest_html}"
        f"{compare_html}"
        f"{coverage_html}"
        "<h3>Compare Summary</h3>"
        f"<ul>{compare_items}</ul>"
        "<h3>Linkage Issues</h3>"
        f"<ul>{linkage_items}</ul>"
        "</section>"
    )


def _render_experiment_compare_html(experiment_compare_summary: dict | None) -> str:
    if not experiment_compare_summary:
        return ""

    items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('candidate_run_id') or '--'))}</strong> "
        f"(<code>{escape(str(item.get('compare_status') or '--'))}</code>)"
        f"<p>{escape(str(item.get('study_type') or '--'))} / {escape(str(item.get('variant_id') or '--'))}</p>"
        f"<p>{escape(' | '.join(_format_compare_metric_delta_lines(item.get('metric_deltas'))) or str(item.get('notes') or 'No metric delta'))}</p>"
        "</li>"
        for item in (experiment_compare_summary.get("comparisons") or [])
        if isinstance(item, dict)
    ) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Experiment Compare</h2>"
        f"<p><strong>baseline_run_id:</strong> {escape(str(experiment_compare_summary.get('baseline_run_id') or '--'))}</p>"
        f"<p><strong>compare_count:</strong> {escape(str(experiment_compare_summary.get('compare_count') or 0))}</p>"
        f"<p><strong>compare:</strong> {escape(str(experiment_compare_summary.get('compare_virtual_path') or '--'))}</p>"
        f"<ul>{items}</ul>"
        "</section>"
    )


def _render_research_evidence_html(research_evidence_summary: dict | None) -> str:
    if not research_evidence_summary:
        return ""

    passed_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (research_evidence_summary.get("passed_evidence") or [])
    ) or "<li>None</li>"
    gap_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (research_evidence_summary.get("evidence_gaps") or [])
    ) or "<li>None</li>"
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


def _render_scientific_gate_html(scientific_supervisor_gate: dict | None) -> str:
    if not scientific_supervisor_gate:
        return ""

    artifact_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (scientific_supervisor_gate.get("artifact_virtual_paths") or [])
    ) or "<li>None</li>"
    blocking_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (scientific_supervisor_gate.get("blocking_reasons") or [])
    ) or "<li>None</li>"
    advisory_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (scientific_supervisor_gate.get("advisory_notes") or [])
    ) or "<li>None</li>"
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

    artifact_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (scientific_remediation_summary.get("artifact_virtual_paths") or [])
    ) or "<li>None</li>"
    action_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('action_id') or '--'))}</strong> "
        f"(<code>{escape(str(item.get('owner_stage') or '--'))}</code> / <code>{escape(str(item.get('execution_mode') or '--'))}</code>)"
        f"<p>{escape(str(item.get('evidence_gap') or 'No evidence gap'))}</p>"
        "</li>"
        for item in (scientific_remediation_summary.get("actions") or [])
        if isinstance(item, dict)
    ) or "<li>None</li>"
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

    artifact_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (scientific_remediation_handoff.get("artifact_virtual_paths") or [])
    ) or "<li>None</li>"
    tool_args = scientific_remediation_handoff.get("tool_args") or {}
    tool_arg_items = "".join(
        f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>"
        for key, value in tool_args.items()
    ) or "<li>None</li>"
    manual_action_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('action_id') or '--'))}</strong> "
        f"(<code>{escape(str(item.get('owner_stage') or '--'))}</code>)"
        f"<p>{escape(str(item.get('evidence_gap') or 'Manual follow-up required'))}</p>"
        "</li>"
        for item in (scientific_remediation_handoff.get("manual_actions") or [])
        if isinstance(item, dict)
    ) or "<li>None</li>"
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

    requirement_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('label') or item.get('requirement_id')))}</strong> "
        f"(<code>{escape(str(item.get('status')))}</code>)"
        f"<p>{escape(str(item.get('detail') or 'No detail'))}</p>"
        "</li>"
        for item in (scientific_verification_assessment.get("requirements") or [])
    ) or "<li>None</li>"

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
            lines.append(
                f"- {field_name}: initial `{entry.get('initial_residual')}`, "
                f"final `{entry.get('final_residual')}`, iterations `{entry.get('iterations')}`"
            )
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
            patch_names = [
                str(item)
                for item in patches
                if isinstance(item, str) and item
            ] if isinstance(patches, list) else []
            parts.append(
                f"selector=patch[{','.join(patch_names)}]"
                if patch_names
                else "selector=patch"
            )
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
            if (
                isinstance(normal, list)
                and len(normal) == 3
                and all(isinstance(item, (int, float)) for item in normal)
            ):
                normal_summary = "; normal=(" + ", ".join(
                    _format_spec_number(item) for item in normal
                ) + ")"
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
        recommendations.append(
            f"回到 `{next_stage}` 补齐验证或整改项后，再刷新最终报告。"
        )
    if review_status == "ready_for_supervisor" and next_stage == "supervisor-review":
        recommendations.append(
            "进入 `supervisor-review` 审阅当前 claim level，并确认是否需要执行手动整改项。"
        )
    return recommendations


def render_markdown(payload: dict) -> str:
    source_artifacts = "\n".join(f"- `{path}`" for path in payload["source_artifact_virtual_paths"]) or "- 暂无"
    final_artifacts = "\n".join(f"- `{path}`" for path in payload["final_artifact_virtual_paths"])
    requested_outputs = "\n".join(
        (
            f"- `{item['output_id']}` | {item['label']} | "
            f"requested=`{item['requested_label']}` | support=`{item['support_level']}`"
            + (
                f" | spec=`{_summarize_postprocess_spec(item.get('postprocess_spec'))}`"
                if _summarize_postprocess_spec(item.get("postprocess_spec"))
                else ""
            )
        )
        for item in payload.get("requested_outputs") or []
    ) or "- 暂无"
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
        f"- 几何文件: `{payload['geometry_virtual_path']}`",
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
        (
            f"- supervisor_handoff_virtual_path: "
            f"`{payload.get('supervisor_handoff_virtual_path') or '当前阶段无'}`"
        ),
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
    lines.extend(_render_scientific_gate_markdown(payload.get("scientific_supervisor_gate")))
    lines.extend(
        _render_scientific_remediation_markdown(
            payload.get("scientific_remediation_summary")
        )
    )
    lines.extend(
        _render_scientific_remediation_handoff_markdown(
            payload.get("scientific_remediation_handoff")
        )
    )
    lines.extend(
        _render_scientific_followup_markdown(
            payload.get("scientific_followup_summary")
        )
    )
    lines.extend(_render_scientific_study_markdown(payload.get("scientific_study_summary")))
    lines.extend(_render_experiment_compare_markdown(payload.get("experiment_compare_summary")))
    lines.extend(_render_figure_delivery_markdown(payload.get("figure_delivery_summary")))
    lines.extend(
        _render_scientific_verification_markdown(
            payload.get("scientific_verification_assessment")
        )
    )
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
        (
            "<p><strong>后处理目录:</strong> "
            f"{escape(str(solver_metrics.get('workspace_postprocess_virtual_path')))}</p>"
        ),
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

    return "<section class=\"panel\"><h2>CFD 结果指标</h2>" + "".join(metric_lines) + "</section>"


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
        (
            "<p><strong>后处理目录:</strong> "
            f"{escape(str(solver_metrics.get('workspace_postprocess_virtual_path')))}</p>"
        ),
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
            metric_lines.append(
                "<p>"
                f"<strong>{escape(str(field_name))}:</strong> "
                f"initial {escape(str(entry.get('initial_residual')))}, "
                f"final {escape(str(entry.get('final_residual')))}, "
                f"iterations {escape(str(entry.get('iterations')))}"
                "</p>"
            )

    return "<section class=\"panel\"><h2>CFD 结果指标</h2>" + "".join(metric_lines) + "</section>"


def _render_scientific_followup_html(scientific_followup_summary: dict | None) -> str:
    if not scientific_followup_summary:
        return ""

    artifact_items = "".join(
        f"<li><code>{escape(str(path))}</code></li>"
        for path in (scientific_followup_summary.get("artifact_virtual_paths") or [])
    ) or "<li>None</li>"
    note_items = "".join(
        f"<li>{escape(str(note))}</li>"
        for note in (scientific_followup_summary.get("latest_notes") or [])
    ) or "<li>None</li>"
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
        + (
            f"<p><strong>latest_result_report:</strong> {escape(str(scientific_followup_summary.get('latest_result_report_virtual_path')))}</p>"
            if scientific_followup_summary.get("latest_result_report_virtual_path")
            else ""
        )
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
    dynamic_recommendations = [
        item.replace("`", "<code>", 1).replace("`", "</code>", 1)
        for item in _build_dynamic_report_recommendations(payload)
    ]
    items = "".join(
        f"<li>{item}</li>" for item in dynamic_recommendations
    ) + "".join(
        f"<li>{escape(item)}</li>" for item in _REPORT_RECOMMENDATIONS
    )
    return f'<section class="panel"><h2>建议</h2><ul>{items}</ul></section>'


def render_html(payload: dict) -> str:
    source_items = "".join(f"<li>{escape(path)}</li>" for path in payload["source_artifact_virtual_paths"]) or "<li>暂无</li>"
    final_items = "".join(f"<li>{escape(path)}</li>" for path in payload["final_artifact_virtual_paths"])
    metrics_section = _render_solver_metrics_html_enriched(payload.get("solver_metrics"))
    acceptance_section = _render_acceptance_html(payload.get("acceptance_assessment"))
    experiment_section = _render_experiment_html(payload.get("experiment_summary"))
    research_evidence_section = _render_research_evidence_html(
        payload.get("research_evidence_summary")
    )
    scientific_gate_section = _render_scientific_gate_html(
        payload.get("scientific_supervisor_gate")
    )
    scientific_remediation_section = _render_scientific_remediation_html(
        payload.get("scientific_remediation_summary")
    )
    scientific_remediation_handoff_section = _render_scientific_remediation_handoff_html(
        payload.get("scientific_remediation_handoff")
    )
    scientific_followup_section = _render_scientific_followup_html(
        payload.get("scientific_followup_summary")
    )
    scientific_study_section = _render_scientific_study_html(
        payload.get("scientific_study_summary")
    )
    experiment_compare_section = _render_experiment_compare_html(
        payload.get("experiment_compare_summary")
    )
    figure_delivery_section = _render_figure_delivery_html(
        payload.get("figure_delivery_summary")
    )
    scientific_verification_section = _render_scientific_verification_html(
        payload.get("scientific_verification_assessment")
    )
    requested_outputs_section = (
        '<section class="panel"><h2>Requested Outputs</h2><ul>'
        + (
            "".join(
                "<li>"
                f"<strong>{escape(str(item.get('label')))}</strong> "
                f"(<code>{escape(str(item.get('output_id')))}</code>)"
                f"<p>requested={escape(str(item.get('requested_label')))}, "
                f"support={escape(str(item.get('support_level')))}"
                + (
                    f", spec={escape(summary)}"
                    if (summary := _summarize_postprocess_spec(item.get("postprocess_spec")))
                    else ""
                )
                + "</p>"
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
    <title>{escape(payload['report_title'])}</title>
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
      <h1>{escape(payload['report_title'])}</h1>
      <p>{escape(payload['summary_zh'])}</p>
    </section>
    <section class="panel">
      <h2>运行上下文</h2>
      <p><strong>来源阶段:</strong> {escape(str(payload['source_runtime_stage']))}</p>
      <p><strong>任务摘要:</strong> {escape(str(payload.get('task_summary') or '待补充'))}</p>
      <p><strong>确认状态:</strong> {escape(str(payload.get('confirmation_status') or 'draft'))}</p>
      <p><strong>执行偏好:</strong> {escape(str(payload.get('execution_preference') or 'plan_only'))}</p>
      <p><strong>任务类型:</strong> {escape(str(payload['task_type']))}</p>
      <p><strong>几何文件:</strong> {escape(str(payload['geometry_virtual_path']))}</p>
      <p><strong>几何家族:</strong> {escape(str(payload.get('geometry_family') or '待确认'))}</p>
      <p><strong>执行就绪状态:</strong> {escape(str(payload.get('execution_readiness') or '待判定'))}</p>
      <p><strong>选定案例:</strong> {escape(str(payload.get('selected_case_id') or '未固定'))}</p>
      <p><strong>Workspace case:</strong> {escape(str(payload.get('workspace_case_dir_virtual_path') or '当前阶段无'))}</p>
      <p><strong>Run script:</strong> {escape(str(payload.get('run_script_virtual_path') or '当前阶段无'))}</p>
    </section>
    <section class="panel">
      <h2>当前阶段判断</h2>
      <p><strong>review_status:</strong> {escape(str(payload['review_status']))}</p>
      <p><strong>next_recommended_stage:</strong> {escape(str(payload['next_recommended_stage']))}</p>
      <p><strong>source_report_virtual_path:</strong> {escape(str(payload['source_report_virtual_path']))}</p>
      <p><strong>supervisor_handoff_virtual_path:</strong> {escape(str(payload.get('supervisor_handoff_virtual_path') or '当前阶段无'))}</p>
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

__all__ = ["render_delivery_readiness_markdown", "render_html", "render_markdown"]
