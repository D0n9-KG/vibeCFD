"use client";

import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

import {
  getNegotiationRailRenderedSlotOrder,
  type NegotiationRailSlot,
} from "./negotiation-rail.contract";

export type NegotiationRailProps = {
  title: ReactNode;
  question: ReactNode;
  actions: ReactNode;
  body: ReactNode;
  footer?: ReactNode;
  className?: string;
};

export function NegotiationRail({
  title,
  question,
  actions,
  body,
  footer = null,
  className,
}: NegotiationRailProps) {
  const renderedSlots = getNegotiationRailRenderedSlotOrder({
    hasFooter: footer !== null,
  });
  const slotContent: Record<NegotiationRailSlot, ReactNode | null> = {
    title,
    question,
    actions,
    body,
    footer,
  };

  return (
    <section
      className={cn(
        "flex h-full min-h-0 flex-col gap-3 rounded-[26px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(246,249,252,0.98))] p-3",
        className,
      )}
    >
      {renderedSlots.map((slot) => (
        <section
          key={slot}
          data-negotiation-slot={slot}
          className={slot === "body" ? "min-h-0 flex-1" : undefined}
        >
          {slotContent[slot]}
        </section>
      ))}
    </section>
  );
}
