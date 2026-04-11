import type {
  SubmarineNegotiationPendingItem,
  SubmarineSessionModel,
} from "./submarine-session-model.ts";

type SubmarineNegotiationState = SubmarineSessionModel["negotiation"];

export type SubmarineNegotiationPanelModel = {
  visible: boolean;
  title: string | null;
  summary: string | null;
  inputGuidance: string | null;
  items: readonly SubmarineNegotiationPendingItem[];
  ctaLabel: string | null;
};

export function buildSubmarineNegotiationPanelModel(
  negotiation: Pick<
    SubmarineNegotiationState,
    "pendingItems" | "summary" | "inputGuidance"
  >,
): SubmarineNegotiationPanelModel {
  if (negotiation.pendingItems.length === 0) {
    return {
      visible: false,
      title: null,
      summary: null,
      inputGuidance: null,
      items: [],
      ctaLabel: null,
    };
  }

  return {
    visible: true,
    title: "待确认事项",
    summary: negotiation.summary,
    inputGuidance: negotiation.inputGuidance,
    items: negotiation.pendingItems,
    ctaLabel: "前往输入框确认",
  };
}
