"use client";

import type { SubmarineDetailModel } from "./submarine-detail-model";

export function SubmarineExperimentBoard({
  experimentBoard,
}: {
  experimentBoard: SubmarineDetailModel["experimentBoard"];
}) {
  const leadingStudy = experimentBoard.studies[0];

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
      {experimentBoard.variantRunIds.length > 0 ? (
        <p className="mt-3 text-sm text-slate-700">
          Variants: {experimentBoard.variantRunIds.join(", ")}
        </p>
      ) : null}
      {experimentBoard.comparisons.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {experimentBoard.comparisons.slice(0, 3).map((comparison) => (
            <li
              key={`${comparison.candidateRunId}-${comparison.variantLabel}`}
              className="rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-2 text-sm text-slate-700"
            >
              {comparison.variantLabel} ({comparison.candidateRunId}) -{" "}
              {comparison.status}
            </li>
          ))}
        </ul>
      ) : null}
      {experimentBoard.lineageNotes.length > 0 ? (
        <p className="mt-3 text-xs text-slate-600">
          Lineage: {experimentBoard.lineageNotes[0]}
        </p>
      ) : null}
      {leadingStudy ? (
        <p className="mt-2 text-xs text-slate-600">
          Study: {leadingStudy.label} ({leadingStudy.workflowStatus})
        </p>
      ) : null}
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
