"use client";

import type {
  SubmarineResearchSlice,
  SubmarineResearchSliceId,
} from "./submarine-session-model";

type SubmarineResearchSliceRibbonProps = {
  slices: readonly SubmarineResearchSlice[];
  activeSliceId: SubmarineResearchSliceId;
  viewedSliceId: SubmarineResearchSliceId;
  expanded: boolean;
  onSelectSlice?: (sliceId: SubmarineResearchSliceId) => void;
  onToggleExpanded?: () => void;
};

function buildVisibleSlices({
  slices,
  activeSliceId,
  expanded,
}: {
  slices: readonly SubmarineResearchSlice[];
  activeSliceId: SubmarineResearchSliceId;
  expanded: boolean;
}): readonly SubmarineResearchSlice[] {
  if (expanded || slices.length <= 3) {
    return slices;
  }

  const activeIndex = slices.findIndex((slice) => slice.id === activeSliceId);
  if (activeIndex === -1) {
    return slices.slice(0, 3);
  }

  const leftIndex = Math.max(activeIndex - 1, 0);
  const rightIndex = Math.min(activeIndex + 1, slices.length - 1);

  return slices.filter((_, index) => index >= leftIndex && index <= rightIndex);
}

export function SubmarineResearchSliceRibbon({
  slices,
  activeSliceId,
  viewedSliceId,
  expanded,
  onSelectSlice,
  onToggleExpanded,
}: SubmarineResearchSliceRibbonProps) {
  const visibleSlices = buildVisibleSlices({
    slices,
    activeSliceId,
    expanded,
  });

  return (
    <section
      data-research-ribbon="submarine"
      className="rounded-[24px] border border-sky-200/65 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(245,250,255,0.96))] px-4 py-4 shadow-[0_18px_40px_rgba(14,165,233,0.08)] motion-safe:transition-[box-shadow,border-color,background-color] motion-safe:duration-300 motion-safe:ease-out motion-reduce:transition-none"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-700">
            研究切片时间带
          </div>
          <h3 className="mt-2 text-lg font-semibold text-slate-950">
            主智能体正在把研究推进切成可回看的研究切片。
          </h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            当前只聚焦最新切片和邻近节点，需要时再展开完整历史。
          </p>
        </div>

        <button
          type="button"
          onClick={onToggleExpanded}
          className="inline-flex items-center rounded-full border border-sky-200/80 bg-white/90 px-3 py-2 text-sm font-medium text-sky-900 motion-safe:transition-[transform,border-color,background-color] motion-safe:duration-300 motion-safe:ease-out motion-safe:hover:-translate-y-0.5 motion-reduce:transition-none hover:border-sky-300 hover:bg-sky-50"
        >
          {expanded ? "收起完整历史" : "展开完整历史"}
        </button>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {visibleSlices.map((slice) => {
          const isActive = slice.id === activeSliceId;
          const isViewed = slice.id === viewedSliceId;

          return (
            <button
              key={slice.id}
              type="button"
              onClick={() => onSelectSlice?.(slice.id)}
              className={[
                "w-full rounded-[22px] border px-4 py-3 text-left sm:min-h-[150px] motion-safe:transition-[transform,box-shadow,border-color,background-color] motion-safe:duration-300 motion-safe:ease-out motion-safe:hover:-translate-y-0.5 motion-reduce:transition-none",
                isViewed
                  ? "border-sky-300 bg-sky-50/90 shadow-[0_12px_28px_rgba(14,165,233,0.10)]"
                  : "border-slate-200/80 bg-white/92 hover:border-sky-200 hover:bg-sky-50/70",
                isActive ? "ring-1 ring-slate-900/10" : "",
              ].join(" ")}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
                    {slice.statusLabel}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-slate-950">
                    {slice.title}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1 text-[10px] font-semibold uppercase tracking-[0.18em]">
                  {isActive ? (
                    <span className="rounded-full bg-slate-900 px-2 py-1 text-white">
                      当前
                    </span>
                  ) : null}
                  {isViewed ? (
                    <span className="rounded-full bg-sky-600 px-2 py-1 text-white">
                      查看中
                    </span>
                  ) : null}
                </div>
              </div>

              <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-600">
                {slice.summary}
              </p>
            </button>
          );
        })}
      </div>
    </section>
  );
}
