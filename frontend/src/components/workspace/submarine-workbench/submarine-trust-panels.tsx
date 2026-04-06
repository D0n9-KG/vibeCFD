"use client";

import { ShieldCheckIcon } from "lucide-react";

import type { SubmarineTrustPanelModel } from "./submarine-detail-model";

export function SubmarineTrustPanels({
  panels,
}: {
  panels: SubmarineTrustPanelModel[];
}) {
  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {panels.map((panel) => (
        <article
          key={panel.id}
          className="rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-[0_14px_30px_rgba(15,23,42,0.04)]"
        >
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className="size-4 text-sky-700" />
            <h4 className="text-sm font-semibold text-slate-950">{panel.title}</h4>
          </div>
          <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
            {panel.status === "available" ? "available" : "missing"}
          </p>
          {panel.highlights.length > 0 ? (
            <ul className="mt-3 space-y-1 text-sm text-slate-700">
              {panel.highlights.slice(0, 2).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : (
            <div className="mt-3 text-sm text-slate-700">
              No linked artifact captured yet.
            </div>
          )}
        </article>
      ))}
    </section>
  );
}
