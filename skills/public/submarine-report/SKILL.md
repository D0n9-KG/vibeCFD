---
name: submarine-report
description: Turn submarine CFD artifacts into a Chinese delivery summary and report narrative. Use when geometry checks, solver outputs, or other evidence already exist and the user needs a traceable, presentation-ready result instead of raw logs.
---

# Submarine Report

Use this skill when the current thread already contains enough artifact-backed evidence to support a report. The primary agent should decide whether the task is ready for reporting.

## Workflow

1. Read `references/report-contract.md`.
2. Call the `submarine_result_report` tool once the current DeerFlow thread already contains `submarine_runtime`.
3. Organize the response into:
   - summary
   - key findings
   - next steps
   - review contract
4. Keep the final answer in Chinese unless the user requests another language.

## Goal

Artifacts and report content must stay first-class so the run can be shown, traced, and archived later.

## Reporting rules

- If runtime JSON already contains `review_status`, `next_recommended_stage`, `report_virtual_path`, or `artifact_virtual_paths`, preserve them in the final structured output.
- Prefer the thread-level `submarine_runtime` snapshot over reconstructing stage state from chat history.
- Preserve `contract_revision`, `revision_summary`, `requested_outputs`, and `output_delivery_plan` when they are available so the report keeps the active task contract visible.
- Keep requested-output support states explicit; if `support_level` or delivery state says an output is pending or unsupported, carry that truth into the report instead of flattening it into generic prose.
- If the source stage already produced `workspace_case_dir_virtual_path`, `run_script_virtual_path`, or `supervisor_handoff_virtual_path`, carry them into the final report context.
- Prefer report narratives that point back to artifact paths instead of retelling raw tool output.
- If only geometry preflight exists, say so clearly and keep the report bounded to preflight conclusions.
- Keep scientific-claim language proportional to the available evidence; do not imply a stronger conclusion just because a report was requested.
