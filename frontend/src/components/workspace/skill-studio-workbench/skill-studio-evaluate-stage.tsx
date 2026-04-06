"use client";

import type { SkillStudioDetailModel } from "./skill-studio-detail-model";
import { SkillStudioTestingEvidence } from "./skill-studio-testing-evidence";

type SkillStudioEvaluateStageProps = {
  detail: SkillStudioDetailModel;
};

export function SkillStudioEvaluateStage({
  detail,
}: SkillStudioEvaluateStageProps) {
  return (
    <section className="space-y-4">
      <section className="rounded-[28px] border border-slate-200/80 bg-white/95 p-5 shadow-[0_20px_48px_rgba(15,23,42,0.07)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-700">
          Evaluate
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Metric label="Validation" value={detail.evaluate.status} />
          <Metric label="Errors" value={String(detail.evaluate.errorCount)} />
          <Metric label="Warnings" value={String(detail.evaluate.warningCount)} />
          <Metric
            label="Passed Checks"
            value={String(detail.evaluate.passedChecks.length)}
          />
        </div>
        {(detail.evaluate.validationErrors.length > 0 ||
          detail.evaluate.validationWarnings.length > 0) ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <ListCard
              title="Validation Errors"
              items={detail.evaluate.validationErrors}
              empty="No blocking validation errors."
            />
            <ListCard
              title="Validation Warnings"
              items={detail.evaluate.validationWarnings}
              empty="No validation warnings."
            />
          </div>
        ) : null}
      </section>
      <SkillStudioTestingEvidence evaluate={detail.evaluate} />
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-3 py-3">
      <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-slate-950">{value}</div>
    </div>
  );
}

function ListCard({
  title,
  items,
  empty,
}: {
  title: string;
  items: string[];
  empty: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
      <div className="text-sm font-semibold text-slate-950">{title}</div>
      {items.length > 0 ? (
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-600">{empty}</p>
      )}
    </article>
  );
}
