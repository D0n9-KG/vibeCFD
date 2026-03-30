// src/components/workspace/submarine-pipeline-sidebar.tsx
"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { cn } from "@/lib/utils";

// RuntimeStage values in order
const STAGE_ORDER = [
  "task-intelligence",
  "geometry-preflight",
  "solver-dispatch",
  "result-reporting",
  "supervisor-review",
] as const;

const STAGE_LABELS: Record<string, string> = {
  "task-intelligence": "任务理解",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解执行",
  "result-reporting": "结果整理",
  "supervisor-review": "Supervisor 复核",
};

export interface SidebarRunItem {
  threadId: string;
  title: string;
  isRunning: boolean;
  isComplete: boolean;
}

interface SubmarinePipelineSidebarProps {
  currentThreadId: string;
  currentStage?: string | null;
  runs: SidebarRunItem[];
  onStageClick: (stageId: string) => void;
  onNewSimulation: () => void;
}

export function SubmarinePipelineSidebar({
  currentThreadId,
  currentStage,
  runs,
  onStageClick,
  onNewSimulation,
}: SubmarinePipelineSidebarProps) {
  const router = useRouter();

  const handleRunClick = useCallback(
    (threadId: string) => {
      router.push(`/workspace/submarine/${threadId}`);
    },
    [router],
  );

  const currentStageIndex = currentStage
    ? STAGE_ORDER.indexOf(currentStage as (typeof STAGE_ORDER)[number])
    : -1;

  return (
    <div className="flex h-full flex-col overflow-hidden bg-stone-50">
      {/* Brand header */}
      <div className="border-b border-stone-200 px-3 py-3">
        <div className="text-[14px] font-extrabold tracking-tight text-sky-500">
          VibeCFD{" "}
          <span className="text-[10px] font-normal text-stone-400">
            · DeerFlow
          </span>
        </div>
      </div>

      {/* Run list */}
      <div className="max-h-48 overflow-y-auto px-2.5 pb-1 pt-2">
        <div className="mb-1 px-1.5 text-[10px] font-semibold uppercase tracking-widest text-stone-400">
          仿真任务
        </div>
        {runs.length === 0 && (
          <div className="px-1.5 py-2 text-[11px] text-stone-400">
            暂无仿真任务
          </div>
        )}
        {runs.map((run) => (
          <div
            key={run.threadId}
            className={cn(
              "mx-0.5 my-0.5 cursor-pointer rounded-md px-2 py-1.5 text-[12px]",
              run.threadId === currentThreadId
                ? "bg-sky-100 font-semibold text-sky-700"
                : "text-stone-500 hover:bg-stone-100",
            )}
            onClick={() => handleRunClick(run.threadId)}
          >
            <div className="truncate">{run.title || run.threadId.slice(0, 8)}</div>
            <div
              className={cn(
                "mt-0.5 text-[10px]",
                run.threadId === currentThreadId
                  ? "text-sky-400"
                  : "text-stone-400",
              )}
            >
              {run.isRunning ? "● 运行中" : run.isComplete ? "✓ 已完成" : "○ 待运行"}
            </div>
          </div>
        ))}
      </div>

      {/* Stage mini-nav */}
      <div className="flex-1 overflow-y-auto px-2.5 pb-1 pt-2">
        <div className="mb-1 px-1.5 text-[10px] font-semibold uppercase tracking-widest text-stone-400">
          当前阶段
        </div>
        <div className="space-y-0.5 px-1">
          {STAGE_ORDER.map((stageId, idx) => {
            const isDone = currentStageIndex > idx;
            const isActive = currentStageIndex === idx;
            return (
              <button
                key={stageId}
                type="button"
                className={cn(
                  "flex w-full items-center gap-1.5 rounded px-1.5 py-1 text-[11px] text-left hover:bg-stone-100",
                  isActive && "bg-sky-100 font-semibold text-sky-700",
                )}
                onClick={() => onStageClick(stageId)}
              >
                <span
                  className={cn(
                    "inline-block size-[7px] shrink-0 rounded-full",
                    isDone && "bg-green-500",
                    isActive && "animate-pulse bg-sky-500",
                    !isDone && !isActive && "bg-stone-300",
                  )}
                />
                {STAGE_LABELS[stageId]}
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-stone-200 p-2.5">
        <button
          type="button"
          className="w-full rounded-md bg-sky-500 py-1.5 text-[12px] font-semibold text-white hover:bg-sky-600"
          onClick={onNewSimulation}
        >
          ＋ 新建仿真
        </button>
      </div>
    </div>
  );
}
