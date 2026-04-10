export const NEGOTIATION_RAIL_REQUIRED_SLOT_ORDER = [
  "title",
  "question",
  "actions",
  "body",
] as const;

export const NEGOTIATION_RAIL_SLOT_ORDER = [
  ...NEGOTIATION_RAIL_REQUIRED_SLOT_ORDER,
  "footer",
] as const;

export type NegotiationRailSlot = (typeof NEGOTIATION_RAIL_SLOT_ORDER)[number];

export type GetNegotiationRailRenderedSlotOrderOptions = {
  hasFooter: boolean;
};

export function getNegotiationRailRenderedSlotOrder({
  hasFooter,
}: GetNegotiationRailRenderedSlotOrderOptions): NegotiationRailSlot[] {
  return hasFooter
    ? [...NEGOTIATION_RAIL_SLOT_ORDER]
    : [...NEGOTIATION_RAIL_REQUIRED_SLOT_ORDER];
}
