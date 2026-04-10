"use client";

import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

export type ThreadHeaderProps = {
  title: string;
  subtitle?: string;
  statusLabel?: string;
  actions?: ReactNode;
  className?: string;
};

export function ThreadHeader({
  title,
  subtitle,
  statusLabel,
  actions = null,
  className,
}: ThreadHeaderProps) {
  return (
    <header
      className={cn(
        "rounded-[24px] border border-slate-200/80 bg-white/92 px-4 py-3 shadow-[0_14px_32px_rgba(15,23,42,0.06)]",
        className,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold text-slate-950">{title}</h2>
          {subtitle ? (
            <p className="mt-1 text-sm leading-6 text-slate-600">{subtitle}</p>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          {statusLabel ? (
            <span className="rounded-full border border-cyan-200/90 bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700">
              {statusLabel}
            </span>
          ) : null}
          {actions}
        </div>
      </div>
    </header>
  );
}
