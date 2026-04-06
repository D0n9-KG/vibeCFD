"use client";

import { cn } from "@/lib/utils";

export type NarrativeStreamItem = {
  id: string;
  actor: string;
  message: string;
  tone?: "neutral" | "attention" | "critical";
};

export type NarrativeStreamProps = {
  items: readonly NarrativeStreamItem[];
  className?: string;
};

export function NarrativeStream({ items, className }: NarrativeStreamProps) {
  return (
    <ol
      className={cn(
        "space-y-2 overflow-y-auto rounded-[20px] border border-slate-200/80 bg-white/88 p-3",
        className,
      )}
    >
      {items.map((item) => (
        <li
          key={item.id}
          className={cn(
            "rounded-xl border px-3 py-2",
            item.tone === "critical"
              ? "border-rose-200/90 bg-rose-50/80"
              : item.tone === "attention"
                ? "border-amber-200/90 bg-amber-50/80"
                : "border-slate-200/80 bg-slate-50/70",
          )}
        >
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            {item.actor}
          </div>
          <p className="mt-1 text-sm leading-6 text-slate-700">{item.message}</p>
        </li>
      ))}
    </ol>
  );
}
