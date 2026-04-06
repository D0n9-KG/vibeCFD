export type AgenticWorkbenchSurface = "submarine" | "skill-studio";

export type AgenticWorkbenchPrimaryStage = "workspace" | "review";

export type AgenticWorkbenchNegotiationState = {
  pendingApprovals: number;
  interruptionVisible: boolean;
};

export type AgenticWorkbenchSecondaryLayerId = "trust-critical";

export type AgenticWorkbenchSessionModel = {
  surface: AgenticWorkbenchSurface;
  isNewThread: boolean;
  chatOpen: boolean;
  primaryStage: AgenticWorkbenchPrimaryStage;
  negotiation: AgenticWorkbenchNegotiationState;
  secondaryLayers: {
    available: readonly AgenticWorkbenchSecondaryLayerId[];
    trustCriticalLayerId: AgenticWorkbenchSecondaryLayerId;
  };
  desktopNegotiationRailPersistent: true;
};

export type CreateAgenticWorkbenchSessionModelOptions = {
  surface: AgenticWorkbenchSurface;
  isNewThread: boolean;
  chatOpenOverride?: boolean;
};

export function createAgenticWorkbenchSessionModel({
  surface,
  isNewThread,
  chatOpenOverride,
}: CreateAgenticWorkbenchSessionModelOptions): AgenticWorkbenchSessionModel {
  return {
    surface,
    isNewThread,
    chatOpen: chatOpenOverride ?? isNewThread,
    primaryStage: "workspace",
    negotiation: {
      pendingApprovals: 0,
      interruptionVisible: false,
    },
    secondaryLayers: {
      available: ["trust-critical"],
      trustCriticalLayerId: "trust-critical",
    },
    desktopNegotiationRailPersistent: true,
  };
}

export function selectAgenticWorkbenchPrimaryStage(
  model: AgenticWorkbenchSessionModel,
  primaryStage: AgenticWorkbenchPrimaryStage,
): AgenticWorkbenchSessionModel {
  return {
    ...model,
    primaryStage,
  };
}

export function updateAgenticWorkbenchNegotiationState(
  model: AgenticWorkbenchSessionModel,
  negotiation: AgenticWorkbenchNegotiationState,
): AgenticWorkbenchSessionModel {
  return {
    ...model,
    negotiation,
  };
}

export function toggleAgenticWorkbenchChatOpen(
  model: AgenticWorkbenchSessionModel,
): AgenticWorkbenchSessionModel {
  return {
    ...model,
    chatOpen: !model.chatOpen,
  };
}
