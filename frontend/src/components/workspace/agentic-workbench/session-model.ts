export type AgenticWorkbenchSessionModel = {
  isNewThread: boolean;
  chatOpen: boolean;
  desktopNegotiationRailPersistent: true;
};

export type CreateAgenticWorkbenchSessionModelOptions = {
  isNewThread: boolean;
  chatOpenOverride?: boolean;
};

export function createAgenticWorkbenchSessionModel({
  isNewThread,
  chatOpenOverride,
}: CreateAgenticWorkbenchSessionModelOptions): AgenticWorkbenchSessionModel {
  return {
    isNewThread,
    chatOpen: chatOpenOverride ?? isNewThread,
    desktopNegotiationRailPersistent: true,
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
