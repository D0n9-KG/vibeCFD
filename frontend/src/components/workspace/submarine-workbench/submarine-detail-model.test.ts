import assert from "node:assert/strict";
import test from "node:test";

const { buildSubmarineDetailModel } = await import(
  new URL("./submarine-detail-model.ts", import.meta.url).href
);

void test("keeps all trust-critical submarine evidence surfaces explicit", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      environment_parity_assessment: {
        parity_status: "aligned",
        profile_label: "OpenFOAM-12",
      },
    },
    finalReport: {
      provenance_manifest_virtual_path: "/artifacts/submarine/provenance.json",
      reproducibility_summary: {
        manifest_virtual_path: "/artifacts/submarine/repro.json",
        reproducibility_status: "reproducible",
      },
      experiment_summary: {
        baseline_run_id: "baseline-01",
        compare_count: 3,
      },
      scientific_remediation_summary: {
        plan_status: "needed",
      },
      scientific_followup_summary: {
        latest_outcome_status: "pending",
      },
    },
  });

  assert.deepEqual(
    model.trustPanels.map((panel) => panel.id),
    [
      "provenance",
      "reproducibility",
      "environment-parity",
      "scientific-gate",
      "experiment-compare",
      "remediation",
      "follow-up",
    ],
  );
  assert.equal(model.trustPanels[0]?.status, "available");
  assert.equal(model.trustPanels[1]?.status, "available");
  assert.equal(model.trustPanels[2]?.status, "available");
});

void test("builds experiment and operator boards from report contracts", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      execution_plan: [
        { role_id: "solver", owner: "worker-a", goal: "Run baseline" },
      ],
      activity_timeline: [{ actor: "worker-a", title: "Baseline solved" }],
    },
    finalReport: {
      experiment_summary: {
        baseline_run_id: "baseline-01",
        run_count: 4,
        compare_count: 2,
      },
      experiment_compare_summary: {
        compare_status_counts: { completed: 2 },
      },
      scientific_remediation_summary: {
        plan_status: "in_progress",
        actions: [{ action_id: "a1", title: "Refine mesh" }],
      },
      scientific_followup_summary: {
        latest_outcome_status: "manual_followup_required",
      },
      delivery_decision_summary: {
        decision_status: "needs_more_evidence",
      },
    },
  });

  assert.equal(model.experimentBoard.baselineRunId, "baseline-01");
  assert.equal(model.experimentBoard.compareCount, 2);
  assert.equal(model.operatorBoard.decisionStatus, "需要更多证据");
  assert.equal(model.operatorBoard.remediation.actionCount, 1);
  assert.deepEqual(model.operatorBoard.remediation.actions, ["细化网格"]);
  assert.equal(model.operatorBoard.timelineEntryCount, 1);
  assert.equal(model.operatorBoard.followup.latestOutcomeStatus, "需要人工跟进");
});

void test("preserves trust-critical cues across provenance, reproducibility, parity, and scientific gate", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      environment_parity_assessment: {
        parity_status: "drifted",
        drift_reasons: ["docker socket unavailable"],
        recovery_guidance: ["retry in containerized runner"],
      },
      scientific_gate_status: "blocked",
    },
    finalReport: {
      provenance_manifest_virtual_path: "/artifacts/submarine/provenance-manifest.json",
      evidence_index: [
        {
          group_id: "forces",
          group_title_zh: "Force coefficients",
        },
      ],
      reproducibility_summary: {
        reproducibility_status: "needs_review",
        parity_status: "drifted",
        drift_reasons: ["solver image mismatch"],
        recovery_guidance: ["pin OpenFOAM image"],
      },
      scientific_supervisor_gate: {
        gate_status: "blocked",
        blocking_reasons: ["missing independent validation"],
        advisory_notes: ["run additional benchmark"],
      },
      research_evidence_summary: {
        readiness_status: "partial",
        blocking_issues: ["no uncertainty bounds"],
      },
    },
  });

  const gatePanel = model.trustPanels.find((panel) => panel.id === "scientific-gate");
  assert.ok(gatePanel);
  assert.equal(gatePanel?.status, "available");
  assert.ok(gatePanel?.highlights.some((line) => line.includes("blocked")));
});

void test("preserves delivery decision, remediation handoff/manual actions, follow-up context, and study summary", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      activity_timeline: [
        { title: "Dispatch variant", actor: "worker-b" },
        { title: "Compare report", actor: "supervisor" },
      ],
    },
    finalReport: {
      experiment_summary: {
        baseline_run_id: "baseline",
        compare_count: 2,
        run_count: 3,
        compared_variant_run_ids: ["variant-a", "variant-b"],
      },
      experiment_compare_summary: {
        comparisons: [
          {
            candidate_run_id: "variant-a",
            compare_status: "completed",
            variant_label: "A",
            baseline_reference_run_id: "baseline",
          },
        ],
      },
      scientific_study_summary: {
        study_execution_status: "running",
        studies: [
          {
            summary_label: "AoA sweep",
            workflow_status: "in_progress",
          },
        ],
      },
      delivery_decision_summary: {
        decision_question_zh: "Can this be delivered for external review?",
        decision_status: "blocked",
        options: [{ option_id: "o1", label_zh: "Remediate first" }],
        blocking_reason_lines: ["validation gap"],
        advisory_note_lines: ["prioritize mesh refinement"],
      },
      scientific_remediation_summary: {
        plan_status: "needed",
        actions: [{ action_id: "r1", title: "Refine mesh near hull wake" }],
      },
      scientific_remediation_handoff: {
        handoff_status: "manual_followup_required",
        tool_name: "spawn_agent",
        manual_actions: [{ action_id: "m1", title: "Attach validation reference" }],
      },
      scientific_followup_summary: {
        latest_outcome_status: "manual_followup_required",
        latest_notes: ["Awaiting supervisor sign-off"],
        latest_tool_name: "spawn_agent",
      },
    },
  });

  assert.equal(model.operatorBoard.deliveryDecision.question?.length ? true : false, true);
  assert.equal(model.operatorBoard.deliveryDecision.optionCount, 1);
  assert.equal(model.operatorBoard.remediation.handoffStatus, "需要人工跟进");
  assert.equal(model.operatorBoard.remediation.manualActionCount, 1);
  assert.deepEqual(model.operatorBoard.remediation.manualActions, ["补充验证参考"]);
  assert.equal(model.operatorBoard.remediation.handoffToolName, "子代理协作");
  assert.equal(model.operatorBoard.followup.latestOutcomeStatus, "需要人工跟进");
  assert.equal(model.operatorBoard.followup.latestToolName, "子代理协作");
  assert.equal(model.experimentBoard.variantCount, 2);
  assert.equal(model.experimentBoard.comparisons.length, 1);
  assert.equal(model.experimentBoard.studyCount, 1);
});

void test("falls back to runtime delivery and follow-up signals when the final report is not ready", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      decision_status: "blocked_by_setup",
      delivery_decision_summary: {
        decision_status: "blocked_by_setup",
        decision_question_zh: "Ship current findings or request another run?",
        options: [{ option_id: "rerun", label_zh: "Request rerun" }],
      },
      scientific_followup_history_virtual_path: "/artifacts/submarine/followup.json",
      activity_timeline: [{ title: "Waiting for supervisor", actor: "lead-agent" }],
    },
    finalReport: null,
  });

  assert.equal(model.operatorBoard.decisionStatus, "受环境阻塞");
  assert.equal(
    model.operatorBoard.deliveryDecision.question,
    "Ship current findings or request another run?",
  );
  assert.equal(model.operatorBoard.deliveryDecision.optionCount, 1);
  assert.equal(
    model.operatorBoard.followup.historyVirtualPath,
    "/artifacts/submarine/followup.json",
  );
  assert.equal(model.operatorBoard.timelineEntryCount, 1);
});

void test("hides unmapped internal slugs behind generic user-facing fallbacks", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      iteration_mode: "custom_followup_mode",
      capability_gaps: [{ output_id: "wake_velocity_slice" }],
      unresolved_decisions: [{ decision_id: "confirm_tail_window" }],
      output_delivery_plan: [
        {
          output_id: "wake_velocity_slice",
          delivery_status: "queued_for_later",
        },
      ],
      delivery_decision_summary: {
        decision_question_zh: "Choose the next path.",
        options: [{ option_id: "request_additional_evidence" }],
      },
    },
    finalReport: null,
  });

  assert.equal(model.operatorBoard.contract.iterationModeLabel, "待同步迭代模式");
  assert.deepEqual(model.operatorBoard.contract.capabilityGapLabels, ["未命名研究项"]);
  assert.deepEqual(model.operatorBoard.contract.unresolvedDecisionLabels, ["未命名研究项"]);
  assert.deepEqual(model.operatorBoard.deliveryDecision.options, ["待确认路径"]);
  assert.deepEqual(model.operatorBoard.contract.deliveryItems, [
    {
      outputId: "wake_velocity_slice",
      label: "未命名输出项",
      statusLabel: "状态待同步",
      detail: null,
    },
  ]);
});

void test("surfaces iterative contract and lineage context in the operator board", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      contract_revision: 4,
      iteration_mode: "derive_variant",
      revision_summary: "Add wake-focused follow-up to the current baseline family.",
      capability_gaps: [{ output_id: "streamlines" }],
      unresolved_decisions: [
        { decision_id: "confirm-tail-window" },
        { decision_id: "confirm-wake-origin" },
      ],
      output_delivery_plan: [
        { output_id: "drag_coefficient", delivery_status: "delivered" },
        { output_id: "wake_velocity_slice", delivery_status: "planned" },
        { output_id: "streamlines", delivery_status: "not_yet_supported" },
      ],
    },
    finalReport: {
      scientific_remediation_handoff: {
        handoff_status: "ready_for_auto_followup",
        tool_name: "submarine_solver_dispatch",
        source_run_id: "mesh_independence:coarse",
        baseline_reference_run_id: "baseline",
        compare_target_run_id: "baseline",
        derived_run_ids: ["mesh_independence:coarse"],
      },
      scientific_followup_summary: {
        latest_outcome_status: "dispatch_refreshed_report",
        latest_tool_name: "submarine_solver_dispatch",
        latest_source_run_id: "mesh_independence:coarse",
        latest_baseline_reference_run_id: "baseline",
        latest_compare_target_run_id: "baseline",
        latest_derived_run_ids: ["mesh_independence:coarse:followup-1"],
      },
    },
  });

  assert.equal(model.operatorBoard.contract.revisionLabel, "r4");
  assert.equal(model.operatorBoard.contract.iterationModeLabel, "派生变体");
  assert.equal(
    model.operatorBoard.contract.revisionSummary,
    "Add wake-focused follow-up to the current baseline family.",
  );
  assert.equal(model.operatorBoard.contract.capabilityGapCount, 1);
  assert.equal(model.operatorBoard.contract.unresolvedDecisionCount, 2);
  assert.equal(model.operatorBoard.contract.deliveryDeliveredCount, 1);
  assert.equal(model.operatorBoard.contract.deliveryPlannedCount, 1);
  assert.equal(model.operatorBoard.contract.deliveryBlockedCount, 1);
  assert.equal(model.experimentBoard.lineageModeLabel, "派生变体");
  assert.deepEqual(model.experimentBoard.compareTargetRunIds, ["baseline"]);
  assert.equal(
    model.experimentBoard.followupSourceRunId,
    "网格无关性：粗",
  );
  assert.equal(
    model.operatorBoard.remediation.sourceRunId,
    "网格无关性：粗",
  );
  assert.equal(model.operatorBoard.remediation.handoffStatus, "可自动跟进");
  assert.equal(model.operatorBoard.remediation.handoffToolName, "求解派发");
  assert.equal(model.operatorBoard.remediation.compareTargetRunId, "基线");
  assert.deepEqual(model.operatorBoard.remediation.derivedRunIds, [
    "网格无关性：粗",
  ]);
  assert.equal(model.operatorBoard.followup.latestOutcomeStatus, "派发后已刷新报告");
  assert.equal(model.operatorBoard.followup.latestToolName, "求解派发");
  assert.equal(
    model.operatorBoard.followup.latestSourceRunId,
    "网格无关性：粗",
  );
  assert.deepEqual(model.operatorBoard.followup.latestDerivedRunIds, [
    "网格无关性：粗：跟进-1",
  ]);
});

void test("localizes known English revision-summary copy before it reaches the operator board", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      revision_summary: "Updated the structured CFD design brief.",
    },
    finalReport: null,
  });

  assert.equal(model.operatorBoard.contract.revisionSummary, "已更新结构化 CFD 设计简报。");
});

void test("falls back to design-brief contract truth before runtime and final-report artifacts arrive", () => {
  const model = buildSubmarineDetailModel({
    runtime: null,
    designBrief: {
      contract_revision: 2,
      iteration_mode: "revise_baseline",
      revision_summary: "Tighten the baseline setup before the first solver dispatch.",
      capability_gaps: [
        {
          output_id: "streamlines",
          requested_label: "流线图",
        },
      ],
      unresolved_decisions: [
        {
          decision_id: "confirm-reference-area",
          label_zh: "确认参考面积",
        },
      ],
      output_delivery_plan: [
        {
          output_id: "drag_coefficient",
          label: "阻力系数",
          delivery_status: "planned",
          detail: "等待首轮求解后生成。",
        },
      ],
    },
    finalReport: null,
  });

  assert.equal(model.operatorBoard.contract.revisionLabel, "r2");
  assert.equal(model.operatorBoard.contract.iterationModeLabel, "修订基线");
  assert.deepEqual(model.operatorBoard.contract.capabilityGapLabels, ["流线图"]);
  assert.deepEqual(model.operatorBoard.contract.unresolvedDecisionLabels, [
    "确认参考面积",
  ]);
  assert.deepEqual(model.operatorBoard.contract.deliveryItems, [
    {
      outputId: "drag_coefficient",
      label: "阻力系数",
      statusLabel: "待完成",
      detail: "等待首轮求解后生成。",
    },
  ]);
});
