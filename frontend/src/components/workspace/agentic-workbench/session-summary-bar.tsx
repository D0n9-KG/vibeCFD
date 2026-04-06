"use client";

import { cn } from "@/lib/utils";

export type SessionSummaryBarProps = {
  pendingApprovals: number;
  interruptionVisible: boolean;
  summary?: string;
  className?: string;
};

export function SessionSummaryBar({
  pendingApprovals,
  interruptionVisible,
  summary = "协商区始终在线，所有修改意见、确认动作与临时打断都通过聊天完成。",
  className,
}: SessionSummaryBarProps) {
  return (
    <section
      className={cn(
        "rounded-[20px] border border-slate-200/80 bg-slate-50/80 p-3",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-cyan-200/90 bg-cyan-50 px-2.5 py-1 text-xs font-semibold text-cyan-700">
          待确认事项：{pendingApprovals}
        </span>
        <span
          className={cn(
            "rounded-full border px-2.5 py-1 text-xs font-semibold",
            interruptionVisible
              ? "border-rose-200/90 bg-rose-50 text-rose-700"
              : "border-slate-200/80 bg-white text-slate-600",
          )}
        >
          {interruptionVisible ? "需继续协商" : "协商区待命"}
        </span>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-600">{summary}</p>
    </section>
  );
}
