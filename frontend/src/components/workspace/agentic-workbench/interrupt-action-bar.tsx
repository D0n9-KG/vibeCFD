"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type InterruptActionBarProps = {
  interruptionVisible: boolean;
  onPause?: () => void;
  onResolve?: () => void;
  className?: string;
};

export function InterruptActionBar({
  interruptionVisible,
  onPause,
  onResolve,
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
            {interruptionVisible
              ? "An interruption is active and requires operator intent."
              : "No interruption is active. Controls remain armed."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={onPause}>
            Pause
          </Button>
          <Button onClick={onResolve}>Resolve</Button>
        </div>
      </div>
    </section>
  );
}
