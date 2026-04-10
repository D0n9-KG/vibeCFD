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
  mobileNegotiationRailVisible: boolean;
  pendingApprovals: number;
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
  mobileNegotiationRailVisibleOverride?: boolean;
};

export function createAgenticWorkbenchSessionModel({
  surface,
  isNewThread,
  mobileNegotiationRailVisibleOverride,
}: CreateAgenticWorkbenchSessionModelOptions): AgenticWorkbenchSessionModel {
  return {
    surface,
    isNewThread,
    mobileNegotiationRailVisible:
      mobileNegotiationRailVisibleOverride ?? isNewThread,
    pendingApprovals: 0,
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
    pendingApprovals: negotiation.pendingApprovals,
    negotiation,
  };
}

export function setAgenticWorkbenchMobileNegotiationRailVisible(
  model: AgenticWorkbenchSessionModel,
  mobileNegotiationRailVisible: boolean,
): AgenticWorkbenchSessionModel {
  return {
    ...model,
    mobileNegotiationRailVisible,
  };
}

export function toggleAgenticWorkbenchMobileNegotiationRailVisible(
  model: AgenticWorkbenchSessionModel,
): AgenticWorkbenchSessionModel {
  return {
    ...model,
    mobileNegotiationRailVisible: !model.mobileNegotiationRailVisible,
  };
}
