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

import { getSubmarineMissionSidebarChrome } from "./workspace-sidebar-shell";

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
  "supervisor-review": "主管复核",
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
}: {
  run: SidebarRunItem;
  currentThreadId: string;
  currentThreadRunLabel?: string;
}) {
  if (run.threadId === currentThreadId && currentThreadRunLabel) {
    return currentThreadRunLabel;
  }

  if (run.isRunning) {
    return "运行中";
  }
  if (run.isComplete) {
    return "已完成";
  }
  return "待运行";
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
  const chrome = getSubmarineMissionSidebarChrome();
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
    <div className={chrome.rootClassName}>
      <div className={chrome.headerWrapClassName}>
        <div className={chrome.headerCardClassName}>
          <div className={chrome.headerEyebrowClassName}>任务看板</div>
          <div className={chrome.headerTitleClassName}>
            {currentRun?.title ?? "当前潜艇研究任务"}
          </div>
          <p className={chrome.headerMetaClassName}>
            聚焦当前任务、阶段推进与清理操作；左侧米色栏继续负责全局工作台导航和历史会话。
          </p>
        </div>
      </div>

      <div className={chrome.runsSectionClassName}>
        <div className="mb-1 flex items-center justify-between gap-2 px-1">
          <div className={chrome.sectionLabelClassName}>仿真任务</div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={chrome.secondaryActionClassName}
            disabled={completedRunCount === 0 || isCleanupPending}
            onClick={() => setCleanupDialogOpen(true)}
          >
            清理已完成
            {completedRunCount > 0 ? ` (${completedRunCount})` : ""}
          </Button>
        </div>

        <div className={chrome.sectionCardClassName}>
          {runs.length === 0 && (
            <div className="px-2.5 py-3 text-[11px] leading-5 text-stone-400">
              暂无潜艇仿真任务。
            </div>
          )}

          {runs.map((run) => {
            const isActive = run.threadId === currentThreadId;
            return (
              <div
                key={run.threadId}
                className={cn(
                  "mb-1 flex items-start gap-1.5 rounded-xl px-2.5 py-2",
                  isActive ? chrome.activeRunClassName : chrome.idleRunClassName,
                )}
              >
                <button
                  type="button"
                  className="min-w-0 flex-1 cursor-pointer text-left"
                  onClick={() => handleRunClick(run.threadId)}
                >
                  <div className="truncate text-[12px] font-medium">
                    {run.title ?? run.threadId.slice(0, 8)}
                  </div>
                  <div
                    className={cn(
                      "mt-1 text-[10px] font-medium",
                      isActive
                        ? chrome.statusTextActiveClassName
                        : chrome.statusTextIdleClassName,
                      isActive &&
                        currentThreadTone === "error" &&
                        "text-red-600",
                    )}
                  >
                    {renderRunStatus({
                      run,
                      currentThreadId,
                      currentThreadRunLabel,
                    })}
                  </div>
                </button>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      type="button"
                      className="mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-lg text-stone-400 transition-colors hover:bg-white/80 hover:text-stone-700 disabled:pointer-events-none disabled:opacity-50"
                      disabled={isCleanupPending}
                      aria-label="更多任务操作"
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
            );
          })}
        </div>
      </div>

      <div className={chrome.stageSectionClassName}>
        <div className={chrome.sectionLabelClassName}>当前阶段</div>
        <div className={chrome.sectionCardClassName}>
          {STAGE_ORDER.map((stageId, idx) => {
            const isDone = currentStageIndex > idx;
            const isActive = currentStageIndex === idx;
            return (
              <button
                key={stageId}
                type="button"
                className={cn(
                  chrome.stageButtonClassName,
                  isActive && chrome.stageButtonActiveClassName,
                )}
                onClick={() => onStageClick(stageId)}
              >
                <span
                  className={cn(
                    "inline-block size-2 shrink-0 rounded-full",
                    isDone && "bg-emerald-500",
                    isActive && "bg-sky-500",
                    !isDone && !isActive && "bg-stone-300",
                  )}
                />
                <span>{STAGE_LABELS[stageId]}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className={chrome.footerClassName}>
        <button
          type="button"
          className={chrome.primaryActionClassName}
          onClick={onNewSimulation}
        >
          + 新建仿真
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
