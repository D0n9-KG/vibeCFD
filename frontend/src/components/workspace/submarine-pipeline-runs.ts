import type { AgentThread } from "@/core/threads";

import type { SidebarRunItem } from "./submarine-pipeline-sidebar";

type SubmarineRuntimeLike = {
  current_stage?: string | null;
  next_recommended_stage?: string | null;
  approval_state?: string | null;
  review_status?: string | null;
  stage_hints?: Record<string, string | null> | null;
  calculation_plan?:
    | Array<{
        approval_state?: string | null;
        requires_immediate_confirmation?: boolean | null;
      }>
    | null;
  requires_immediate_confirmation?: boolean | null;
  stage_status?: string | null;
  runtime_status?: string | null;
};

type SubmarineDesignBriefLike = {
  confirmation_status?: string | null;
  approval_state?: string | null;
  open_questions?: string[] | null;
  stage_hints?: Record<string, string | null> | null;
  calculation_plan?:
    | Array<{
        approval_state?: string | null;
        requires_immediate_confirmation?: boolean | null;
      }>
    | null;
  requires_immediate_confirmation?: boolean | null;
};

type ThreadValuesLike = {
  title?: unknown;
  artifacts?: unknown;
  is_complete?: boolean;
  submarine_runtime?: SubmarineRuntimeLike | null;
};

type SubmarineRunLineageLike = {
  candidate_run_id?: string | null;
  compare_target_run_id?: string | null;
  run_role?: string | null;
  variant_origin?: string | null;
  variant_id?: string | null;
};

function normalizeValues(
  values: ThreadValuesLike | null | undefined,
): ThreadValuesLike {
  return values && typeof values === "object" ? values : {};
}

const ACTIVE_STAGE_STATUSES = new Set(["in_progress", "running", "streaming"]);
const TERMINAL_STAGE_STATUSES = new Set([
  "draft",
  "confirmed",
  "planned",
  "executed",
  "completed",
  "failed",
  "blocked",
  "ready",
  "waiting_user",
]);

function normalizeRuntime(
  runtime: ThreadValuesLike["submarine_runtime"],
): SubmarineRuntimeLike | null {
  return runtime && typeof runtime === "object" ? runtime : null;
}

function normalizeArtifacts(artifacts: unknown): string[] {
  return Array.isArray(artifacts)
    ? artifacts.filter((artifact): artifact is string => typeof artifact === "string")
    : [];
}

export function formatSubmarineRunLineage(
  entry: SubmarineRunLineageLike | null | undefined,
): string {
  const compareTargetRunId = entry?.compare_target_run_id ?? "baseline";
  const candidateRunId = entry?.candidate_run_id ?? "unknown";
  const variantId =
    entry?.variant_id ??
    (candidateRunId.startsWith("custom:")
      ? candidateRunId.slice("custom:".length)
      : candidateRunId);
  const isCustomVariant =
    entry?.run_role === "custom_variant" ||
    entry?.variant_origin === "custom_variant" ||
    candidateRunId.startsWith("custom:");
  const lineageLabel = isCustomVariant ? `custom / ${variantId}` : candidateRunId;
  return `${compareTargetRunId} -> ${candidateRunId} | ${lineageLabel}`;
}

export function isSubmarineThread(values: ThreadValuesLike | null | undefined): boolean {
  const normalizedValues = normalizeValues(values);
  const runtime = normalizeRuntime(normalizedValues.submarine_runtime);
  if (runtime) {
    return true;
  }

  return normalizeArtifacts(normalizedValues.artifacts).some(
    (path) =>
      path.includes("/submarine/") && !path.includes("/submarine/skill-studio/"),
  );
}

export function getSubmarineDisplayedStage(
  runtime: SubmarineRuntimeLike | null | undefined,
  designBrief?: SubmarineDesignBriefLike | null,
): string | null {
  if (!runtime) {
    return null;
  }

  if (needsUserConfirmation(runtime, designBrief)) {
    return runtime.stage_hints?.current ?? designBrief?.stage_hints?.current ?? "task-intelligence";
  }

  return runtime.stage_hints?.current ?? runtime.current_stage ?? null;
}

export function getSubmarineDisplayedNextStage(
  runtime: SubmarineRuntimeLike | null | undefined,
  designBrief?: SubmarineDesignBriefLike | null,
): string | null {
  if (needsUserConfirmation(runtime, designBrief)) {
    return (
      runtime?.stage_hints?.suggested_next ??
      designBrief?.stage_hints?.suggested_next ??
      "user-confirmation"
    );
  }

  return runtime?.stage_hints?.suggested_next ?? runtime?.next_recommended_stage ?? null;
}

function needsUserConfirmation(
  runtime: SubmarineRuntimeLike | null | undefined,
  designBrief?: SubmarineDesignBriefLike | null,
): boolean {
  const calculationPlan = runtime?.calculation_plan ?? designBrief?.calculation_plan ?? [];
  const hasImmediateCalculationPlanClarification =
    Boolean(
      runtime?.requires_immediate_confirmation ??
        designBrief?.requires_immediate_confirmation,
    ) ||
    calculationPlan.some(
      (item) =>
        Boolean(item?.requires_immediate_confirmation) &&
        item?.approval_state !== "researcher_confirmed",
    );
  const hasPendingCalculationPlanApproval = calculationPlan.some(
    (item) => item?.approval_state !== "researcher_confirmed",
  );
  const approvalState =
    runtime?.approval_state ?? designBrief?.approval_state ?? null;

  if (
    approvalState === "needs_confirmation" ||
    runtime?.review_status === "needs_user_confirmation" ||
    hasImmediateCalculationPlanClarification ||
    hasPendingCalculationPlanApproval
  ) {
    return true;
  }

  if (!designBrief) {
    return false;
  }

  const openQuestions = Array.isArray(designBrief.open_questions)
    ? designBrief.open_questions.filter(Boolean)
    : [];

  return (
    designBrief.confirmation_status === "draft" || openQuestions.length > 0
  );
}

function isActivelyRunning(runtime: SubmarineRuntimeLike | null): boolean {
  if (!runtime) {
    return false;
  }

  if (runtime.runtime_status === "running") {
    return true;
  }
  if (
    runtime.runtime_status === "ready" ||
    runtime.runtime_status === "completed" ||
    runtime.runtime_status === "blocked" ||
    runtime.runtime_status === "failed"
  ) {
    return false;
  }

  const stageStatus = runtime.stage_status?.trim().toLowerCase() ?? null;
  if (stageStatus && ACTIVE_STAGE_STATUSES.has(stageStatus)) {
    return true;
  }
  if (stageStatus && TERMINAL_STAGE_STATUSES.has(stageStatus)) {
    return false;
  }

  if (
    runtime.review_status === "needs_user_confirmation" ||
    runtime.review_status === "blocked"
  ) {
    return false;
  }

  return false;
}

function isComplete(
  values: ThreadValuesLike,
  artifacts: string[],
  runtime: SubmarineRuntimeLike | null,
): boolean {
  if (values.is_complete === true) {
    return true;
  }

  if (artifacts.some((path) => path.endsWith("/final-report.json"))) {
    return true;
  }

  return (
    runtime?.review_status === "ready_for_supervisor" &&
    runtime?.next_recommended_stage === "supervisor-review"
  );
}

export function deriveSubmarineSidebarRuns(
  threads: Array<Pick<AgentThread, "thread_id" | "values">>,
): SidebarRunItem[] {
  return threads
    .filter((thread) => isSubmarineThread(thread.values))
    .map((thread) => {
      const values = normalizeValues(thread.values);
      const artifacts = normalizeArtifacts(values.artifacts);
      const runtime = normalizeRuntime(values.submarine_runtime);
      const complete = isComplete(values, artifacts, runtime);

      return {
        threadId: thread.thread_id,
        title: (values.title as string | undefined) ?? "",
        isRunning: !complete && isActivelyRunning(runtime),
        isComplete: complete,
      };
    });
}

export function deriveCompletedSubmarineRunIds(runs: SidebarRunItem[]) {
  return runs
    .filter((run) => run.isComplete)
    .map((run) => run.threadId);
}

export function deriveSubmarineRunDeletionPath(
  threads: Array<Pick<AgentThread, "thread_id" | "values">>,
  deletedThreadIds: string[],
  currentThreadId: string,
) {
  const deletedIds = new Set(deletedThreadIds);
  if (!deletedIds.has(currentThreadId)) {
    return null;
  }

  const currentThreadIndex = threads.findIndex(
    (thread) => thread.thread_id === currentThreadId,
  );
  if (currentThreadIndex < 0) {
    return "/workspace/submarine/new";
  }

  const findCandidateAt = (index: number) => {
    const thread = threads[index];
    if (!thread) {
      return null;
    }
    if (deletedIds.has(thread.thread_id)) {
      return null;
    }
    return isSubmarineThread(thread.values)
      ? `/workspace/submarine/${thread.thread_id}`
      : null;
  };

  for (let offset = 1; offset < threads.length; offset += 1) {
    const rightCandidate = findCandidateAt(currentThreadIndex + offset);
    if (rightCandidate) {
      return rightCandidate;
    }

    const leftCandidate = findCandidateAt(currentThreadIndex - offset);
    if (leftCandidate) {
      return leftCandidate;
    }
  }

  return "/workspace/submarine/new";
}
