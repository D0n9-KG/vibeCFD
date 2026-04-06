"use client";

import { Button } from "@/components/ui/button";

import type { SkillStudioDetailModel } from "./skill-studio-detail-model";

type SkillStudioDefineStageProps = {
  detail: SkillStudioDetailModel;
  onOpenChat: () => void;
};

export function SkillStudioDefineStage({
  detail,
  onOpenChat,
}: SkillStudioDefineStageProps) {
  return (
    <section className="space-y-4">
      <section className="rounded-[28px] border border-slate-200/80 bg-white/95 p-5 shadow-[0_20px_48px_rgba(15,23,42,0.07)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-orange-700">
          Define
        </div>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
          {detail.define.skillTitle}
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
          {detail.define.skillGoal}
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <Metric label="Triggers" value={String(detail.define.triggerCount)} />
          <Metric label="Constraints" value={String(detail.define.constraintCount)} />
          <Metric
            label="Built-in Skills"
            value={String(detail.define.builtinSkills.length)}
          />
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]">
        <section className="rounded-[24px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Working Brief
          </div>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <ListCard
              title="Trigger Conditions"
              items={detail.define.triggerConditions}
              empty="Describe when the skill should activate."
            />
            <ListCard
              title="Expert Constraints"
              items={detail.define.constraints}
              empty="Capture non-negotiable constraints and failure boundaries."
            />
            <ListCard
              title="Acceptance Criteria"
              items={detail.define.acceptanceCriteria}
              empty="Spell out what counts as a successful skill output."
            />
            <ListCard
              title="Built-in Skills"
              items={detail.define.builtinSkills}
              empty="Select built-in skills once the package takes shape."
            />
          </div>
        </section>

        <section className="rounded-[24px] border border-orange-200/80 bg-orange-50/70 p-4 shadow-[0_18px_40px_rgba(249,115,22,0.08)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-orange-700">
            Prompting
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            Keep the right rail focused on collaboration. Use it to refine goals,
            define triggers, and negotiate the exact acceptance boundary before the
            draft locks in.
          </p>
          <Button className="mt-4 w-full" onClick={onOpenChat}>
            Continue Negotiation
          </Button>
        </section>
      </div>
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
