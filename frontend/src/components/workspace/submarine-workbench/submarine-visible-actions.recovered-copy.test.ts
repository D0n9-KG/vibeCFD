import assert from "node:assert/strict";
import test from "node:test";

import { buildSubmarineVisibleActions } from "./submarine-visible-actions.ts";

void test("localizes scientific-study rerun summaries before they become visible follow-up descriptions", () => {
  const actions = buildSubmarineVisibleActions({
    runtime: {
      current_stage: "result-reporting",
      runtime_status: "blocked",
      blocker_detail:
        "Time-step sensitivity study: Some scientific-study variants are missing solver results: coarse, fine.",
      supervisor_handoff_virtual_path:
        "/artifacts/submarine/scientific-remediation-handoff.json",
    },
    designBrief: {
      confirmation_status: "confirmed",
      task_description: "Refresh the blocked SUBOFF baseline thread.",
      selected_case_id: "darpa_suboff_bare_hull_resistance",
    },
    finalReport: {
      summary_zh: "The report was refreshed, but follow-up evidence is still incomplete.",
      scientific_supervisor_gate: {
        gate_status: "blocked",
        blocking_reasons: [
          "Time-step sensitivity study: Some scientific-study variants are missing solver results: coarse, fine.",
        ],
      },
      scientific_remediation_summary: {
        actions: [
          {
            action_id: "execute-scientific-studies",
            summary:
              "Run the planned scientific study variants and regenerate the missing verification artifacts for domain_sensitivity, time_step_sensitivity.",
          },
        ],
      },
      scientific_remediation_handoff: {
        handoff_status: "ready_for_auto_followup",
        recommended_action_id: "execute-scientific-studies",
        tool_name: "submarine_solver_dispatch",
        reason:
          "Time-step sensitivity study: Some scientific-study variants are missing solver results: coarse, fine.",
      },
    },
  });

  assert.equal(actions.length, 1);
  assert.equal(actions[0]?.id, "followup");
  assert.doesNotMatch(
    actions[0]?.description ?? "",
    /Run the planned|verification artifacts|domain_sensitivity|time_step_sensitivity/i,
  );
});
