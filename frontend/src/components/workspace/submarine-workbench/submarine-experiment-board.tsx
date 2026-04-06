"use client";

import type { SubmarineDetailModel } from "./submarine-detail-model";

export function SubmarineExperimentBoard({
  experimentBoard,
}: {
  experimentBoard: SubmarineDetailModel["experimentBoard"];
}) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
        Experiment / Compare
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Baseline Run" value={experimentBoard.baselineRunId ?? "none"} />
        <Metric label="Run Count" value={String(experimentBoard.runCount)} />
        <Metric label="Compare Count" value={String(experimentBoard.compareCount)} />
        <Metric
          label="Compared Complete"
          value={String(experimentBoard.compareCompletedCount)}
        />
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
