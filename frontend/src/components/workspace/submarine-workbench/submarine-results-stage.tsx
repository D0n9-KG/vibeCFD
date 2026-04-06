"use client";

import type { SubmarineDetailModel } from "./submarine-detail-model";
import { SubmarineExperimentBoard } from "./submarine-experiment-board";
import { SubmarineOperatorBoard } from "./submarine-operator-board";
import type { SubmarineSessionModel } from "./submarine-session-model";
import { SubmarineTrustPanels } from "./submarine-trust-panels";

export function SubmarineResultsStage({
  session,
  detail,
}: {
  session: SubmarineSessionModel;
  detail: SubmarineDetailModel;
}) {
  return (
    <section className="space-y-4">
      <article className="rounded-2xl border border-slate-200/80 bg-white/92 p-5 shadow-[0_14px_30px_rgba(15,23,42,0.04)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
          Results Stage
        </div>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
          Trust-critical evidence and decision surface
        </h2>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          Preserve provenance, reproducibility, parity, compare, remediation, and
          follow-up before closing the session.
        </p>
        <p className="mt-2 text-xs text-slate-600">
          Evidence ready: {session.summary.evidenceReady ? "yes" : "no"}
        </p>
      </article>
      <SubmarineTrustPanels panels={detail.trustPanels} />
      <SubmarineExperimentBoard experimentBoard={detail.experimentBoard} />
      <SubmarineOperatorBoard operatorBoard={detail.operatorBoard} />
    </section>
  );
}
