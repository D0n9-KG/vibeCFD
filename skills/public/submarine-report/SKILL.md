---
name: submarine-report
description: Turn submarine CFD run artifacts into a Chinese delivery summary and report narrative. Use when geometry checks or solver outputs already exist and the user needs a traceable, presentation-ready result instead of raw logs.
---

# Submarine Report

Use this skill after geometry preflight or later solver/postprocess steps have already produced artifacts.

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
- If the source stage already produced `workspace_case_dir_virtual_path`, `run_script_virtual_path`, or `supervisor_handoff_virtual_path`, carry them into the final report context.
- Prefer report narratives that point back to artifact paths instead of retelling raw tool output.
- If only geometry preflight exists, say so clearly and keep the report bounded to preflight conclusions.
