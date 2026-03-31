import type { AgentThread } from "@/core/threads";

import type { SidebarRunItem } from "./submarine-pipeline-sidebar";

type SubmarineRuntimeLike = {
  current_stage?: string | null;
  next_recommended_stage?: string | null;
  review_status?: string | null;
  stage_status?: string | null;
};

type SubmarineDesignBriefLike = {
  confirmation_status?: string | null;
  open_questions?: string[] | null;
};

type ThreadValuesLike = {
  title?: unknown;
  artifacts?: unknown;
  is_complete?: boolean;
  submarine_runtime?: SubmarineRuntimeLike | null;
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
  return runtime && typeof runtime === "object"
    ? (runtime as SubmarineRuntimeLike)
    : null;
}

function normalizeArtifacts(artifacts: unknown): string[] {
  return Array.isArray(artifacts)
    ? artifacts.filter((artifact): artifact is string => typeof artifact === "string")
    : [];
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
    return "task-intelligence";
  }

  return runtime.current_stage ?? null;
}

export function getSubmarineDisplayedNextStage(
  runtime: SubmarineRuntimeLike | null | undefined,
  designBrief?: SubmarineDesignBriefLike | null,
): string | null {
  if (needsUserConfirmation(runtime, designBrief)) {
    return "user-confirmation";
  }

  return runtime?.next_recommended_stage ?? null;
}

function needsUserConfirmation(
  runtime: SubmarineRuntimeLike | null | undefined,
  designBrief?: SubmarineDesignBriefLike | null,
): boolean {
  if (
    runtime?.review_status === "needs_user_confirmation" ||
    runtime?.next_recommended_stage === "user-confirmation"
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
