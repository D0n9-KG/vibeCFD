"use client";

import type { SubmarineResearchSlice } from "./submarine-session-model";

type SubmarineResearchSliceHistoryBannerProps = {
  slice: SubmarineResearchSlice;
  onReturnToCurrent?: () => void;
};

export function SubmarineResearchSliceHistoryBanner({
  slice,
  onReturnToCurrent,
}: SubmarineResearchSliceHistoryBannerProps) {
  return (
    <section
      data-history-inspection="submarine"
      className="rounded-[22px] border border-amber-200/80 bg-[linear-gradient(180deg,rgba(255,251,235,0.96),rgba(255,247,219,0.92))] px-4 py-3 shadow-[0_14px_30px_rgba(245,158,11,0.12)] motion-safe:transition-[transform,opacity,box-shadow] motion-safe:duration-300 motion-safe:ease-out motion-reduce:transition-none"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-700">
            历史切片查看中
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            你正在查看 <span className="font-semibold text-slate-950">{slice.title}</span>{" "}
            的历史快照。当前研究仍会沿着最新切片继续推进。
          </p>
        </div>

        <button
          type="button"
          onClick={onReturnToCurrent}
          className="inline-flex items-center rounded-full border border-amber-300/80 bg-white/90 px-3 py-2 text-sm font-medium text-amber-900 motion-safe:transition-[transform,border-color,background-color] motion-safe:duration-300 motion-safe:ease-out motion-safe:hover:-translate-y-0.5 motion-reduce:transition-none hover:border-amber-400 hover:bg-amber-50"
        >
          返回当前研究
        </button>
      </div>
    </section>
  );
}
