"use client";

import type { SkillStudioDetailModel } from "./skill-studio-detail-model";

type SkillStudioGraphStageProps = {
  detail: SkillStudioDetailModel;
};

export function SkillStudioGraphStage({ detail }: SkillStudioGraphStageProps) {
  return (
    <section className="space-y-4">
      <section className="rounded-[28px] border border-slate-200/80 bg-white/95 p-5 shadow-[0_20px_48px_rgba(15,23,42,0.07)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-700">
          Graph
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Metric label="Related Skills" value={String(detail.graph.relationshipCount)} />
          <Metric label="High Impact" value={String(detail.graph.highImpactCount)} />
          <Metric label="Upstream" value={String(detail.graph.upstreamCount)} />
          <Metric label="Downstream" value={String(detail.graph.downstreamCount)} />
        </div>
      </section>

      <section className="rounded-[24px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <div className="text-sm font-semibold text-slate-950">Related Skills</div>
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          {detail.graph.relatedSkills.length > 0 ? (
            detail.graph.relatedSkills.map((item) => (
              <article
                key={item.skillAssetId}
                className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-950">
                      {item.skillName}
                    </div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {item.category}
                    </div>
                  </div>
                  <div className="text-xs font-medium text-slate-500">
                    score {item.strongestScore.toFixed(2)}
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {item.description}
                </p>
                {item.reasons.length > 0 ? (
                  <p className="mt-3 text-xs text-slate-600">
                    Why: {item.reasons[0]}
                  </p>
                ) : null}
              </article>
            ))
          ) : (
            <p className="text-sm text-slate-600">
              Relationship context will appear once the skill package is connected
              to the graph.
            </p>
          )}
        </div>
      </section>
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
