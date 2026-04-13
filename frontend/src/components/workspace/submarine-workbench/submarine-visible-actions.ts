import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

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
    runtime &&
      runtime.current_stage === "solver-dispatch" &&
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

function hasReadyScientificFollowup(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  finalReport: SubmarineFinalReportPayload | null,
): boolean {
  const handoff = finalReport?.scientific_remediation_handoff;
  if (handoff?.handoff_status !== "ready_for_auto_followup") {
    return false;
  }

  const latestOutcome = finalReport?.scientific_followup_summary?.latest_outcome_status;
  if (
    latestOutcome != null &&
    ["dispatch_refreshed_report", "result_report_refreshed", "task_complete"].includes(
      latestOutcome,
    )
  ) {
    return false;
  }

  return Boolean(
    runtime?.runtime_status === "blocked" ||
      runtime?.blocker_detail ||
      finalReport?.scientific_supervisor_gate?.gate_status === "blocked",
  );
}

function hasReportReady(finalReport: SubmarineFinalReportPayload | null): boolean {
  return Boolean(finalReport);
}

function shouldOfferExecutionAction({
  runtime,
  designBrief,
}: Pick<
  BuildSubmarineVisibleActionsInput,
  "runtime" | "designBrief"
>): boolean {
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

function buildScientificFollowupAction({
  runtime,
  finalReport,
}: {
  runtime: SubmarineRuntimeSnapshotPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
}): SubmarineVisibleAction {
  const blocker =
    runtime?.blocker_detail ??
    finalReport?.scientific_remediation_handoff?.reason ??
    finalReport?.scientific_supervisor_gate?.blocking_reasons?.find(Boolean) ??
    "当前科学审查仍要求补齐缺失证据。";

  return {
    id: "followup",
    label: "继续建议修正并重跑",
    description: `当前阻塞：${blocker}。这个按钮会把续跑和刷新报告的请求发送到协商线程，并在聊天历史中留下完整记录。`,
    message:
      "请继续建议的修正流程：基于当前科学审查给出的 remediation handoff，复用现有几何、案例和已确认设置，立即重跑当前求解并补齐缺失的 solver metrics，然后刷新结果报告。整个过程请保持在当前线程中可追踪。",
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
    return [
      {
        id: "execute",
        label: "开始实际求解执行",
        description:
          "把执行指令发送到协商线程，消息会直接出现在聊天历史中，不会绕过前端偷偷调用后台。",
        message:
          "请按当前已经确认或已规划好的潜艇 CFD 方案开始实际求解执行，并继续完成必要的后处理准备。优先复用当前设计简报、几何文件、参考尺度和已选基线设置；如果仍缺少执行前必要条件，请明确列出缺项。",
      },
    ];
  }

  return [];
}
