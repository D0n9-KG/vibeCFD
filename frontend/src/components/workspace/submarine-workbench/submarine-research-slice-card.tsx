"use client";

import type { SubmarineResearchSliceFact } from "./submarine-research-canvas.model";
import type { SubmarineResearchSlice } from "./submarine-session-model";

type SubmarineResearchSliceCardProps = {
  slice: SubmarineResearchSlice;
  isHistoricalView: boolean;
  facts: readonly SubmarineResearchSliceFact[];
  evidenceBadges: readonly string[];
  contextNotes: readonly string[];
};

export function SubmarineResearchSliceCard({
  slice,
  isHistoricalView,
  facts,
  evidenceBadges,
  contextNotes,
}: SubmarineResearchSliceCardProps) {
  return (
    <section
      data-current-slice-card="submarine"
      data-historical-view={isHistoricalView ? "true" : "false"}
      className={[
        "rounded-[28px] border bg-white/96 px-5 py-5 motion-safe:transition-[transform,box-shadow,border-color,opacity] motion-safe:duration-300 motion-safe:ease-out motion-reduce:transition-none",
        isHistoricalView
          ? "border-amber-200/85 shadow-[0_24px_48px_rgba(245,158,11,0.10)]"
          : "border-slate-200/80 shadow-[0_24px_48px_rgba(15,23,42,0.08)]",
      ].join(" ")}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-700">
            {isHistoricalView ? "历史研究切片" : "当前研究切片"}
          </div>
          <h3 className="mt-2 text-[22px] font-semibold tracking-tight text-slate-950">
            {slice.title}
          </h3>
          <p className="mt-2 text-base leading-7 text-slate-700">{slice.summary}</p>
        </div>

        <div className="rounded-full border border-sky-200/80 bg-sky-50 px-3 py-2 text-sm font-medium text-sky-900">
          {slice.statusLabel}
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {facts.map((fact) => (
          <article
            key={fact.label}
            className="rounded-[20px] border border-slate-200/80 bg-slate-50/70 px-4 py-3"
          >
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              {fact.label}
            </div>
            <div className="mt-2 text-sm font-medium leading-6 text-slate-900">
              {fact.value}
            </div>
          </article>
        ))}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <article className="rounded-[22px] border border-slate-200/80 bg-slate-50/55 px-4 py-4">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            主智能体判断
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            {slice.agentInterpretation}
          </p>

          <div className="mt-5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            下一建议动作
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            {slice.nextRecommendedAction}
          </p>
        </article>

        <article className="rounded-[22px] border border-slate-200/80 bg-white px-4 py-4">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            关键证据
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            {slice.keyEvidenceSummary}
          </p>

          {evidenceBadges.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {evidenceBadges.map((badge) => (
                <span
                  key={badge}
                  className="rounded-full border border-slate-200/80 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700"
                >
                  {badge}
                </span>
              ))}
            </div>
          ) : null}
        </article>
      </div>

      {contextNotes.length > 0 ? (
        <article className="mt-5 rounded-[22px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(248,250,252,0.95),rgba(241,245,249,0.88))] px-4 py-4">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            切片上下文
          </div>
          <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-700">
            {contextNotes.map((note) => (
              <li key={note} className="flex gap-3">
                <span className="mt-[10px] h-1.5 w-1.5 shrink-0 rounded-full bg-sky-500" />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </section>
  );
}
