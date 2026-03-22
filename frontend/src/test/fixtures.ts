import type { RunSummary } from "../lib/types";

export function createRunSummary(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: "run_20260321_0001",
    status: "awaiting_confirmation",
    current_stage: "awaiting_confirmation",
    stage_label: "待确认",
    created_at: "2026-03-21T09:00:00.000Z",
    updated_at: "2026-03-21T09:05:00.000Z",
    request: {
      task_description: "分析潜艇模型的压力分布",
      task_type: "pressure_distribution",
      geometry_family_hint: "DARPA SUBOFF",
      geometry_file_name: "suboff.stl",
      operating_notes: "深潜稳态工况"
    },
    run_directory: "C:/demo/runs/run_20260321_0001",
    geometry_check: "几何检查通过，可进入案例映射。",
    candidate_cases: [],
    selected_case: null,
    workflow_draft: null,
    confirmed_at: null,
    reviewer_notes: null,
    timeline: [],
    artifacts: [],
    report_markdown: null,
    metrics: {},
    ...overrides
  };
}
