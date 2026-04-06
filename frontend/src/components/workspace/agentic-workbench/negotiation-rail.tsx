"use client";

import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

import { InterruptActionBar } from "./interrupt-action-bar";
import { NarrativeStream, type NarrativeStreamItem } from "./narrative-stream";
import { SessionSummaryBar } from "./session-summary-bar";

export type NegotiationRailProps = {
  pendingApprovals: number;
  interruptionVisible: boolean;
  narrative: readonly NarrativeStreamItem[];
  header?: ReactNode;
  footer?: ReactNode;
  onPause?: () => void;
  onResolve?: () => void;
  className?: string;
};

export function NegotiationRail({
  pendingApprovals,
  interruptionVisible,
  narrative,
  header = null,
  footer = null,
  onPause,
  onResolve,
  className,
}: NegotiationRailProps) {
  return (
    <section
      className={cn(
        "flex h-full min-h-0 flex-col gap-3 rounded-[26px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(246,249,252,0.98))] p-3",
        className,
      )}
    >
      {header}

      <SessionSummaryBar
        pendingApprovals={pendingApprovals}
        interruptionVisible={interruptionVisible}
      />

      <InterruptActionBar
        interruptionVisible={interruptionVisible}
        onPause={onPause}
        onResolve={onResolve}
      />

      <NarrativeStream items={narrative} className="min-h-0 flex-1" />

      {footer}
    </section>
  );
}
