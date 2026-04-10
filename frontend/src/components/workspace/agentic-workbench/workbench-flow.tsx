"use client";

import type { ReactNode } from "react";

type FlowItem = {
  id: string;
  title: string;
  summary: string;
  status: string;
  expanded: boolean;
  content?: ReactNode;
};

export function WorkbenchFlow({ items }: { items: readonly FlowItem[] }) {
  return (
    <div className="flex min-h-0 flex-col gap-2.5">
      {items.map((item) => (
        <section
          key={item.id}
          data-flow-item={item.id}
          className={
            item.expanded
              ? "rounded-[28px] border border-sky-200/80 bg-white px-4 py-4"
              : "rounded-[20px] border border-slate-200/80 bg-slate-50/80 px-4 py-3"
          }
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-slate-950">
                {item.title}
              </div>
              {item.expanded ? (
                <div className="mt-1 text-sm leading-6 text-slate-600">
                  {item.summary}
                </div>
              ) : null}
            </div>
            <span className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-600">
              {item.status}
            </span>
          </div>
          {item.expanded ? <div className="mt-4">{item.content ?? null}</div> : null}
        </section>
      ))}
    </div>
  );
}
