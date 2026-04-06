"use client";

import type { SubmarineDetailModel } from "./submarine-detail-model";

export function SubmarineOperatorBoard({
  operatorBoard,
}: {
  operatorBoard: SubmarineDetailModel["operatorBoard"];
}) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
        Operator Board
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Decision" value={operatorBoard.decisionStatus ?? "pending"} />
        <Metric
          label="Remediation Actions"
          value={String(operatorBoard.remediation.actionCount)}
        />
        <Metric
          label="Timeline Events"
          value={String(operatorBoard.timelineEntryCount)}
        />
        <Metric
          label="Follow-up"
          value={operatorBoard.followup.latestOutcomeStatus ?? "not set"}
        />
      </div>
      <div className="mt-3 space-y-2 text-sm text-slate-700">
        <p>
          Decision question:{" "}
          {operatorBoard.deliveryDecision.question ?? "Not yet declared."}
        </p>
        {operatorBoard.deliveryDecision.options.length > 0 ? (
          <p>Options: {operatorBoard.deliveryDecision.options.join(" | ")}</p>
        ) : null}
        {operatorBoard.deliveryDecision.blockingReasons.length > 0 ? (
          <p>
            Blocking reasons:{" "}
            {operatorBoard.deliveryDecision.blockingReasons.join(" | ")}
          </p>
        ) : null}
        {operatorBoard.deliveryDecision.advisoryNotes.length > 0 ? (
          <p>Advisory notes: {operatorBoard.deliveryDecision.advisoryNotes[0]}</p>
        ) : null}
      </div>
      <div className="mt-3 rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-3 text-xs text-slate-600">
        <div>Remediation handoff: {operatorBoard.remediation.handoffStatus ?? "n/a"}</div>
        <div>Tool: {operatorBoard.remediation.handoffToolName ?? "n/a"}</div>
        <div>
          Manual actions: {operatorBoard.remediation.manualActionCount}{" "}
          {operatorBoard.remediation.manualActions[0]
            ? `(${operatorBoard.remediation.manualActions[0]})`
            : ""}
        </div>
        <div>
          Follow-up tool: {operatorBoard.followup.latestToolName ?? "n/a"}{" "}
          {operatorBoard.followup.latestNotes[0]
            ? `- ${operatorBoard.followup.latestNotes[0]}`
            : ""}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/90 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
