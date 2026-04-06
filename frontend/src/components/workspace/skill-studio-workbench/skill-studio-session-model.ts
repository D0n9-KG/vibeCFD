import {
  DEFAULT_SKILL_STUDIO_AGENT,
  labelOfSkillStudioAgentName,
} from "../skill-studio-agent-options.ts";

export type SkillStudioPrimaryStage =
  | "define"
  | "evaluate"
  | "publish"
  | "graph";

export type SkillStudioSessionModel = {
  primaryStage: SkillStudioPrimaryStage;
  stageOrder: readonly SkillStudioPrimaryStage[];
  assistant: {
    mode: string;
    label: string;
    locked: boolean;
  };
  summary: {
    hasDraftArtifact: boolean;
    validationStatus: string;
    testStatus: string;
    publishStatus: string;
    graphRelationshipCount: number;
  };
  negotiation: {
    pendingApprovalCount: number;
    interruptionVisible: boolean;
    question: string | null;
  };
};

export type BuildSkillStudioSessionModelInput = {
  isNewThread: boolean;
  persistedAssistantMode: string | null;
  hasDraftArtifact: boolean;
  validationStatus: string | null;
  testStatus: string | null;
  publishStatus: string | null;
  errorCount: number;
  warningCount: number;
  blockingCount: number;
  graphRelationshipCount: number;
};

const PUBLISH_READY_STATUSES = new Set([
  "draft_ready",
  "published",
  "ready_for_review",
  "rollback_available",
]);

function normalizeStatus(value: string | null | undefined, fallback = "draft_only") {
  const normalized = value?.trim();
  return normalized && normalized.length > 0 ? normalized : fallback;
}

function resolvePrimaryStage(
  input: BuildSkillStudioSessionModelInput,
  hasBlockingNegotiation: boolean,
): SkillStudioPrimaryStage {
  if (input.isNewThread || !input.hasDraftArtifact) {
    return "define";
  }

  if (hasBlockingNegotiation) {
    return "evaluate";
  }

  if (PUBLISH_READY_STATUSES.has(normalizeStatus(input.publishStatus))) {
    return "publish";
  }

  if (input.graphRelationshipCount > 0 && !input.hasDraftArtifact) {
    return "graph";
  }

  return "evaluate";
}

function buildNegotiationQuestion(
  input: BuildSkillStudioSessionModelInput,
  hasBlockingNegotiation: boolean,
) {
  if (!hasBlockingNegotiation) {
    return null;
  }

  if (input.errorCount > 0 || normalizeStatus(input.validationStatus) === "needs_revision") {
    return "Validation blockers need attention before dry-run or publish.";
  }

  if (normalizeStatus(input.testStatus) === "failed") {
    return "Scenario test failures are blocking the current lifecycle.";
  }

  if (normalizeStatus(input.publishStatus) === "blocked") {
    return "Publish readiness is blocked. Resolve the remaining gates first.";
  }

  return "The lifecycle has unresolved blockers that require operator review.";
}

export function buildSkillStudioSessionModel(
  input: BuildSkillStudioSessionModelInput,
): SkillStudioSessionModel {
  const assistantMode = input.persistedAssistantMode ?? DEFAULT_SKILL_STUDIO_AGENT;
  const hasBlockingNegotiation =
    input.blockingCount > 0 ||
    input.errorCount > 0 ||
    normalizeStatus(input.validationStatus) === "needs_revision" ||
    normalizeStatus(input.testStatus) === "failed" ||
    normalizeStatus(input.publishStatus) === "blocked";

  return {
    primaryStage: resolvePrimaryStage(input, hasBlockingNegotiation),
    stageOrder: ["define", "evaluate", "publish", "graph"],
    assistant: {
      mode: assistantMode,
      label: labelOfSkillStudioAgentName(assistantMode),
      locked: !input.isNewThread || Boolean(input.persistedAssistantMode),
    },
    summary: {
      hasDraftArtifact: input.hasDraftArtifact,
      validationStatus: normalizeStatus(input.validationStatus),
      testStatus: normalizeStatus(input.testStatus),
      publishStatus: normalizeStatus(input.publishStatus),
      graphRelationshipCount: input.graphRelationshipCount,
    },
    negotiation: {
      pendingApprovalCount: input.blockingCount,
      interruptionVisible: hasBlockingNegotiation,
      question: buildNegotiationQuestion(input, hasBlockingNegotiation),
    },
  };
}
