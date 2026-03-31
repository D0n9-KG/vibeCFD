"use client";

import { MoreHorizontal, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

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
  currentThreadRunLabel?: string;
  currentThreadTone?: "ready" | "streaming" | "error";
  runs: SidebarRunItem[];
  completedRunCount: number;
  isCleanupPending?: boolean;
  onStageClick: (stageId: string) => void;
  onDeleteRun: (threadId: string) => void;
  onCleanupCompletedRuns: () => void;
  onNewSimulation: () => void;
}

function renderRunStatus({
  run,
  currentThreadId,
  currentThreadRunLabel,
  currentThreadTone,
}: {
  run: SidebarRunItem;
  currentThreadId: string;
  currentThreadRunLabel?: string;
  currentThreadTone?: "ready" | "streaming" | "error";
}) {
  if (run.threadId === currentThreadId && currentThreadRunLabel) {
    if (currentThreadTone === "error") {
      return `● ${currentThreadRunLabel}`;
    }
    if (currentThreadRunLabel === "运行中") {
      return `● ${currentThreadRunLabel}`;
    }
    if (currentThreadRunLabel === "待命") {
      return "● 待命";
    }
    return currentThreadRunLabel;
  }

  if (run.isRunning) {
    return "● 运行中";
  }
  if (run.isComplete) {
    return "✓ 已完成";
  }
  return "● 待运行";
}

export function SubmarinePipelineSidebar({
  currentThreadId,
  currentStage,
  currentThreadRunLabel,
  currentThreadTone,
  runs,
  completedRunCount,
  isCleanupPending = false,
  onStageClick,
  onDeleteRun,
  onCleanupCompletedRuns,
  onNewSimulation,
}: SubmarinePipelineSidebarProps) {
  const router = useRouter();
  const [deleteTarget, setDeleteTarget] = useState<SidebarRunItem | null>(null);
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false);

  const handleRunClick = useCallback(
    (threadId: string) => {
      router.push(`/workspace/submarine/${threadId}`);
    },
    [router],
  );

  const currentStageIndex = currentStage
    ? STAGE_ORDER.indexOf(currentStage as (typeof STAGE_ORDER)[number])
    : -1;
  const currentRun = useMemo(
    () => runs.find((run) => run.threadId === currentThreadId) ?? null,
    [currentThreadId, runs],
  );

  return (
    <div className="flex h-full flex-col overflow-hidden bg-stone-50">
      <div className="border-b border-stone-200 px-3 py-3">
        <div className="text-[14px] font-extrabold tracking-tight text-sky-500">
          VibeCFD{" "}
          <span className="text-[10px] font-normal text-stone-400">
            · DeerFlow
          </span>
        </div>
      </div>

      <div className="px-2.5 pb-1 pt-2">
        <div className="mb-1 flex items-center justify-between gap-2 px-1.5">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-stone-400">
            仿真任务
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-[11px] font-medium text-stone-500 hover:text-stone-900"
            disabled={completedRunCount === 0 || isCleanupPending}
            onClick={() => setCleanupDialogOpen(true)}
          >
            清理已完成{completedRunCount > 0 ? ` (${completedRunCount})` : ""}
          </Button>
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
              "mx-0.5 my-0.5 flex items-start gap-1 rounded-md px-2 py-1.5 text-[12px]",
              run.threadId === currentThreadId
                ? "bg-sky-100 font-semibold text-sky-700"
                : "text-stone-500 hover:bg-stone-100",
            )}
          >
            <button
              type="button"
              className="min-w-0 flex-1 text-left"
              onClick={() => handleRunClick(run.threadId)}
            >
              <div className="truncate">
                {run.title || run.threadId.slice(0, 8)}
              </div>
              <div
                className={cn(
                  "mt-0.5 text-[10px]",
                  run.threadId === currentThreadId
                    ? "text-sky-400"
                    : "text-stone-400",
                  run.threadId === currentThreadId &&
                    currentThreadTone === "error" &&
                    "text-red-500",
                )}
              >
                {renderRunStatus({
                  run,
                  currentThreadId,
                  currentThreadRunLabel,
                  currentThreadTone,
                })}
              </div>
            </button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-md text-stone-400 transition hover:bg-white/70 hover:text-stone-700 disabled:pointer-events-none disabled:opacity-50"
                  disabled={isCleanupPending}
                  aria-label="More run actions"
                >
                  <MoreHorizontal className="size-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem
                  className="text-red-600 focus:text-red-700"
                  onSelect={() => setDeleteTarget(run)}
                >
                  <Trash2 className="size-4" />
                  删除仿真
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        ))}
      </div>

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

      <div className="border-t border-stone-200 p-2.5">
        <button
          type="button"
          className="w-full rounded-md bg-sky-500 py-1.5 text-[12px] font-semibold text-white hover:bg-sky-600"
          onClick={onNewSimulation}
        >
          ＋ 新建仿真
        </button>
      </div>

      <Dialog
        open={deleteTarget != null}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>删除这个仿真任务？</DialogTitle>
            <DialogDescription className="leading-6">
              {deleteTarget
                ? `删除“${deleteTarget.title || deleteTarget.threadId.slice(0, 8)}”后，其对话、上传几何、工作目录和生成产物会一并清理，且不可撤销。`
                : ""}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteTarget(null)}
              disabled={isCleanupPending}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (deleteTarget) {
                  onDeleteRun(deleteTarget.threadId);
                  setDeleteTarget(null);
                }
              }}
              disabled={isCleanupPending}
            >
              删除并清理
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={cleanupDialogOpen} onOpenChange={setCleanupDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>清理已完成的仿真任务？</DialogTitle>
            <DialogDescription className="leading-6">
              {completedRunCount > 0
                ? `这会删除 ${completedRunCount} 个已完成 run 的对话、上传文件、工作目录和计算产物，但保留运行中或待确认的任务。`
                : "当前没有可清理的已完成 run。"}
              {currentRun?.isComplete
                ? " 如果当前页面属于已完成 run，清理后会自动切换到剩余的 submarine 工作台。"
                : ""}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCleanupDialogOpen(false)}
              disabled={isCleanupPending}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                onCleanupCompletedRuns();
                setCleanupDialogOpen(false);
              }}
              disabled={completedRunCount === 0 || isCleanupPending}
            >
              清理已完成 run
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
