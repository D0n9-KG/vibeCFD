"use client";

import type { SkillStudioDetailModel } from "./skill-studio-detail-model";

type SkillStudioTestingEvidenceProps = {
  evaluate: SkillStudioDetailModel["evaluate"];
};

export function SkillStudioTestingEvidence({
  evaluate,
}: SkillStudioTestingEvidenceProps) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-700">
        验证与试跑证据
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <Metric label="场景数" value={String(evaluate.scenarioMatrix.scenarioCount)} />
        <Metric label="阻塞数" value={String(evaluate.scenarioMatrix.blockedCount)} />
        <Metric label="Dry-run" value={evaluate.dryRun.ready ? "已就绪" : "待修正"} />
      </div>
      <div className="mt-4 space-y-2">
        {evaluate.scenarioMatrix.scenarios.length > 0 ? (
          evaluate.scenarioMatrix.scenarios.slice(0, 4).map((scenario) => (
            <article
              key={scenario.id}
              className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-3 py-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-semibold text-slate-950">
                  {scenario.scenario}
                </div>
                <div className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
                  {scenario.status}
                </div>
              </div>
              <p className="mt-2 text-sm text-slate-700">
                预期结果：{scenario.expectedOutcome}
              </p>
              {scenario.blockingReasons.length > 0 ? (
                <p className="mt-2 text-xs text-amber-800">
                  阻塞原因：{scenario.blockingReasons.join(" ｜ ")}
                </p>
              ) : null}
            </article>
          ))
        ) : (
          <p className="text-sm text-slate-600">
            生成测试场景后，这里会展示验证矩阵与试跑证据。
          </p>
        )}
      </div>
      {evaluate.dryRun.nextActions.length > 0 ? (
        <p className="mt-3 text-xs text-slate-600">
          下一步：{evaluate.dryRun.nextActions[0]}
        </p>
      ) : null}
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
