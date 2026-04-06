"use client";

import { MessageSquareIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { SubmarineSessionModel } from "./submarine-session-model";

export function SubmarinePlanStage({
  session,
  onOpenChat,
}: {
  session: SubmarineSessionModel;
  onOpenChat: () => void;
}) {
  return (
    <section className="space-y-4">
      <article className="rounded-2xl border border-slate-200/80 bg-white/92 p-5 shadow-[0_14px_30px_rgba(15,23,42,0.04)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
          Plan Stage
        </div>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
          Define objective, constraints, and confirmation gates
        </h2>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          {session.summary.currentObjective}
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <PlanMetric
            label="Pending Approvals"
            value={String(session.negotiation.pendingApprovalCount)}
          />
          <PlanMetric label="Messages" value={String(session.summary.messageCount)} />
          <PlanMetric label="Artifacts" value={String(session.summary.artifactCount)} />
        </div>
        <Button className="mt-4" onClick={onOpenChat}>
          <MessageSquareIcon className="size-4" />
          Continue Negotiation
        </Button>
      </article>
    </section>
  );
}

function PlanMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
