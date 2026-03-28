# Submarine Report Contract

When reporting submarine workflow results:

- Treat artifacts as the canonical evidence
- Mention the checked geometry family and task type
- Mention the recommended next role or next execution stage
- Preserve the runtime review contract fields when present:
  - `review_status`
  - `next_recommended_stage`
  - `report_virtual_path`
  - `artifact_virtual_paths`
- Preserve the `submarine_runtime` thread snapshot and treat it as the authoritative source-stage handoff
- When the source stage already includes `workspace_case_dir_virtual_path`, `run_script_virtual_path`, or `supervisor_handoff_virtual_path`, surface them in the report instead of dropping them
- Keep the final narrative in Chinese

Preferred report sections:

1. Run summary
2. Geometry / case context
3. Key findings
4. Risks or missing data
5. Next-step recommendation
6. Review contract / artifact handoff
