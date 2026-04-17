import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

import { localizeWorkspaceDisplayText } from "../../../core/i18n/workspace-display.ts";

export type SubmarineVisibleAction = {
  id: "execute" | "report" | "followup";
  label: string;
  description: string;
  message: string;
};

type BuildSubmarineVisibleActionsInput = {
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
};

function hasPendingConfirmation(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  designBrief: SubmarineDesignBriefPayload | null,
): boolean {
  if (
    runtime?.review_status === "needs_user_confirmation" ||
    runtime?.next_recommended_stage === "user-confirmation"
  ) {
    return true;
  }

  if (
    designBrief?.confirmation_status != null &&
    designBrief.confirmation_status !== "confirmed"
  ) {
    return true;
  }

  return (designBrief?.open_questions?.filter(Boolean).length ?? 0) > 0;
}

function hasPlannedDispatchReadyForExecution(
  runtime: SubmarineRuntimeSnapshotPayload | null,
): boolean {
  return Boolean(
    runtime?.current_stage === "solver-dispatch" &&
      runtime.stage_status === "planned" &&
      runtime.runtime_status === "ready" &&
      runtime.review_status === "ready_for_supervisor" &&
      runtime.execution_preference === "plan_only" &&
      !runtime.execution_log_virtual_path &&
      !runtime.solver_results_virtual_path &&
      !runtime.stability_evidence_virtual_path,
  );
}

function hasExecutionStarted(
  runtime: SubmarineRuntimeSnapshotPayload | null,
): boolean {
  if (hasPlannedDispatchReadyForExecution(runtime)) {
    return false;
  }

  return [
    runtime?.runtime_status === "running",
    runtime?.runtime_status === "completed",
    runtime?.runtime_status === "blocked",
    runtime?.current_stage === "result-reporting",
    runtime?.current_stage === "supervisor-review",
    runtime?.current_stage === "solver-dispatch" &&
      runtime?.stage_status !== "planned",
    runtime?.execution_log_virtual_path,
    runtime?.solver_results_virtual_path,
    runtime?.stability_evidence_virtual_path,
  ].some(Boolean);
}

function hasExecutionCompleted(
  runtime: SubmarineRuntimeSnapshotPayload | null,
): boolean {
  return [
    runtime?.runtime_status === "completed",
    runtime?.solver_results_virtual_path,
    runtime?.stability_evidence_virtual_path,
  ].some(Boolean);
}

function hasCompletedCurrentScientificFollowup(
  finalReport: SubmarineFinalReportPayload | null,
): boolean {
  const handoff = finalReport?.scientific_remediation_handoff;
  const followup = finalReport?.scientific_followup_summary;
  if (!handoff || !followup) {
    return false;
  }

  if (followup.latest_outcome_status === "task_complete") {
    return true;
  }

  if (followup.latest_outcome_status !== "dispatch_refreshed_report") {
    return false;
  }

  if (
    (followup.latest_recommended_action_id ?? null) !==
    (handoff.recommended_action_id ?? null)
  ) {
    return false;
  }

  return (followup.latest_source_run_id ?? null) === (handoff.source_run_id ?? null);
}

function hasReadyScientificFollowup(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  finalReport: SubmarineFinalReportPayload | null,
): boolean {
  const handoff = finalReport?.scientific_remediation_handoff;
  if (handoff?.handoff_status !== "ready_for_auto_followup") {
    return false;
  }

  if (hasCompletedCurrentScientificFollowup(finalReport)) {
    return false;
  }

  return Boolean(
    runtime?.runtime_status === "blocked" ||
      runtime?.blocker_detail != null ||
      finalReport?.scientific_supervisor_gate?.gate_status === "blocked",
  );
}

function hasReportReady(finalReport: SubmarineFinalReportPayload | null): boolean {
  return Boolean(finalReport);
}

function shouldOfferExecutionAction({
  runtime,
  designBrief,
}: Pick<BuildSubmarineVisibleActionsInput, "runtime" | "designBrief">): boolean {
  if (hasPendingConfirmation(runtime, designBrief)) {
    return false;
  }

  if (hasExecutionStarted(runtime)) {
    return false;
  }

  if (hasPlannedDispatchReadyForExecution(runtime)) {
    return true;
  }

  return designBrief?.confirmation_status === "confirmed";
}

function resolveScientificFollowupCopy(
  finalReport: SubmarineFinalReportPayload | null,
): Pick<SubmarineVisibleAction, "label" | "message"> & { summary: string | null } {
  const handoff = finalReport?.scientific_remediation_handoff;
  const actionId = handoff?.recommended_action_id ?? null;
  const summary =
    finalReport?.scientific_remediation_summary?.actions?.find(
      (item) => item?.action_id === actionId,
    )?.summary ??
    handoff?.reason ??
    null;

  switch (actionId) {
    case "rerun-current-baseline":
      return {
        label: "重跑当前基线并刷新报告",
        message:
          "请按当前修正交接说明继续推进：复用现有几何、案例和已确认设置，优先重跑当前基线，补齐缺失的求解指标，然后刷新结果报告。整个过程请保持在当前线程中可追踪。",
        summary,
      };
    case "regenerate-research-report-linkage":
      return {
        label: "刷新研究报告链路",
        message:
          "请不要重新求解。只基于当前已有产物刷新结果报告、科学审查和修正交接说明，并确保前端中的合同快照、阻塞项和交付状态与最新研究产物保持一致。",
        summary,
      };
    default:
      return {
        label: "继续建议修正并重跑",
        message:
          "请继续建议的修正流程：基于当前科学审查给出的修正交接说明，复用现有几何、案例和已确认设置，立即重跑当前求解，补齐缺失的求解指标，然后刷新结果报告。整个过程请保持在当前线程中可追踪。",
        summary,
      };
  }
}

function buildScientificFollowupAction({
  runtime,
  finalReport,
}: {
  runtime: SubmarineRuntimeSnapshotPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
}): SubmarineVisibleAction {
  const blocker = localizeWorkspaceDisplayText(
    runtime?.blocker_detail ??
      finalReport?.scientific_remediation_handoff?.reason ??
      finalReport?.scientific_supervisor_gate?.blocking_reasons?.find(Boolean) ??
      "当前科学审查仍要求补齐缺失证据。",
  );
  const actionCopy = resolveScientificFollowupCopy(finalReport);
  const actionSummary = actionCopy.summary
    ? `建议动作：${localizeWorkspaceDisplayText(actionCopy.summary)}。`
    : "";

  return {
    id: "followup",
    label: actionCopy.label,
    description: `当前阻塞：${blocker}。${actionSummary}这个按钮会把清晰的下一步请求发送到协商线程，并在聊天历史里留下完整记录。`,
    message: actionCopy.message,
  };
}

function resolveExecutionAction(
  runtime: SubmarineRuntimeSnapshotPayload | null,
): Pick<SubmarineVisibleAction, "description" | "message"> {
  if (
    runtime?.input_source_type === "openfoam_case_seed" &&
    runtime?.official_case_id
  ) {
    return {
      description: `把官方案例 ${runtime.official_case_id} 的执行请求发送到协商线程，消息会直接出现在聊天历史中，并明确沿用当前 case seed 与已组装的 OpenFOAM case。`,
      message: `请按当前已经确认或已规划好的官方 OpenFOAM 案例 ${runtime.official_case_id} 开始实际求解执行，并继续完成必要的后处理准备。优先复用已导入的 case seed、当前组装好的 OpenFOAM case 和现有设计简报；如果仍缺少执行前必要条件，请明确列出缺项。`,
    };
  }

  return {
    description:
      "把执行指令发送到协商线程，消息会直接出现在聊天历史中，不会绕过前端偷偷调用后台。",
    message:
      "请按当前已经确认或已规划好的潜艇 CFD 方案开始实际求解执行，并继续完成必要的后处理准备。优先复用当前设计简报、几何文件、参考尺度和已选基线设置；如果仍缺少执行前必要条件，请明确列出缺项。",
  };
}

export function buildSubmarineVisibleActions({
  runtime,
  designBrief,
  finalReport,
}: BuildSubmarineVisibleActionsInput): SubmarineVisibleAction[] {
  if (hasReadyScientificFollowup(runtime, finalReport)) {
    return [
      buildScientificFollowupAction({
        runtime,
        finalReport,
      }),
    ];
  }

  if (hasReportReady(finalReport)) {
    return [];
  }

  if (
    hasExecutionCompleted(runtime) &&
    runtime?.current_stage !== "result-reporting" &&
    runtime?.current_stage !== "supervisor-review"
  ) {
    return [
      {
        id: "report",
        label: "生成最终结果报告",
        description:
          "把最终报告请求发送到协商线程，消息会直接出现在聊天历史里，方便追踪交付过程。",
        message:
          "请基于当前已完成的潜艇 CFD 求解与后处理结果，生成最终结果报告，并明确给出关键结论、证据边界、交付产物路径与下一步建议。",
      },
    ];
  }

  if (shouldOfferExecutionAction({ runtime, designBrief })) {
    const executionAction = resolveExecutionAction(runtime);
    return [
      {
        id: "execute",
        label: "开始实际求解执行",
        description: executionAction.description,
        message: executionAction.message,
      },
    ];
  }

  return [];
}
