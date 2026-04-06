"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type InterruptActionBarProps = {
  interruptionVisible: boolean;
  onPause?: () => void;
  onResolve?: () => void;
  activeDescription?: string;
  idleDescription?: string;
  pauseLabel?: string;
  resolveLabel?: string;
  className?: string;
};

export function InterruptActionBar({
  interruptionVisible,
  onPause,
  onResolve,
  activeDescription = "An interruption is active and requires operator intent.",
  idleDescription = "No interruption is active. Controls remain armed.",
  pauseLabel = "Pause",
  resolveLabel = "Resolve",
  className,
}: InterruptActionBarProps) {
  return (
    <section
      className={cn(
        "rounded-[20px] border border-slate-200/80 bg-white/88 p-3",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Interrupt Controls
          </div>
          <p className="mt-1 text-sm text-slate-700">
            {interruptionVisible ? activeDescription : idleDescription}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={onPause}>
            {pauseLabel}
          </Button>
          <Button onClick={onResolve}>{resolveLabel}</Button>
        </div>
      </div>
    </section>
  );
}
