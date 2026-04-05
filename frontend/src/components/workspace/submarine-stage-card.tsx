// src/components/workspace/submarine-stage-card.tsx
"use client";

import {
  AlertTriangleIcon,
  CheckIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  CircleDotIcon,
  XIcon,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export type StageCardState =
  | "done"
  | "active"
  | "pending"
  | "blocked"
  | "failed";

export interface StageCardProps {
  state: StageCardState;
  index: number;
  name: string;
  description?: string;
  timeLabel?: string;
  rightLabel?: ReactNode;
  children?: ReactNode;
  defaultExpanded?: boolean;
  className?: string;
  bodyClassName?: string;
}

export function StageCard({
  state,
  index,
  name,
  description,
  timeLabel,
  rightLabel,
  children,
  defaultExpanded,
  className,
  bodyClassName,
}: StageCardProps) {
  const [expanded, setExpanded] = useState(
    defaultExpanded ?? state !== "done",
  );

  const canToggle = state !== "active" && children != null;
  const showBody = (state === "active" || expanded) && children != null;

  return (
    <div
      className={cn(
        "flex h-full flex-col overflow-hidden rounded-xl border border-stone-200 bg-white",
        className,
      )}
    >
      <div
        className={cn(
          "flex shrink-0 items-center gap-3 px-4 py-3",
          state === "done" && "bg-green-50",
          state === "active" &&
            "border-l-[3px] border-l-blue-500 bg-blue-50",
          state === "pending" && "bg-stone-50",
          state === "blocked" &&
            "border-l-[3px] border-l-amber-500 bg-amber-50",
          state === "failed" &&
            "border-l-[3px] border-l-red-500 bg-red-50",
          canToggle && "cursor-pointer select-none",
        )}
        onClick={canToggle ? () => setExpanded((v) => !v) : undefined}
      >
        <StageIcon state={state} index={index} />

        <div className="min-w-0 flex-1">
          <div
            className={cn(
              "text-[13px] font-semibold",
              state === "pending" && "text-stone-400",
              state === "active" && "text-stone-900",
              state === "done" && "text-stone-900",
              state === "blocked" && "text-amber-900",
              state === "failed" && "text-red-900",
            )}
          >
            {name}
          </div>
          {description && (
            <div
              className={cn(
                "mt-0.5 truncate text-[11px]",
                state === "blocked" && "text-amber-700",
                state === "failed" && "text-red-700",
                state !== "blocked" &&
                  state !== "failed" &&
                  "text-stone-500",
              )}
            >
              {description}
            </div>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {rightLabel}
          {timeLabel && (
            <span className="text-[11px] text-stone-400">{timeLabel}</span>
          )}
          {canToggle && (
            <span className="text-stone-400">
              {expanded ? (
                <ChevronUpIcon className="size-3.5" />
              ) : (
                <ChevronDownIcon className="size-3.5" />
              )}
            </span>
          )}
        </div>
      </div>

      {showBody && (
        <div
          className={cn(
            "flex flex-1 flex-col border-t border-stone-200 bg-white px-4 py-3",
            bodyClassName,
          )}
        >
          {children}
        </div>
      )}
    </div>
  );
}

function StageIcon({
  state,
  index,
}: {
  state: StageCardState;
  index: number;
}) {
  if (state === "done") {
    return (
      <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-green-500 text-white">
        <CheckIcon className="size-3" />
      </div>
    );
  }

  if (state === "active") {
    return (
      <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-blue-500 text-white">
        <CircleDotIcon className="size-3 animate-pulse" />
      </div>
    );
  }

  if (state === "blocked") {
    return (
      <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-amber-500 text-white">
        <AlertTriangleIcon className="size-3" />
      </div>
    );
  }

  if (state === "failed") {
    return (
      <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-red-500 text-white">
        <XIcon className="size-3" />
      </div>
    );
  }

  return (
    <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-stone-200 text-[10px] font-bold text-stone-400">
      {index}
    </div>
  );
}
