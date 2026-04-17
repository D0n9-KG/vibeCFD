"use client";

import { ArrowUpRightIcon, PencilIcon, Trash2Icon } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { useThreadDeletePreview } from "@/core/thread-management/hooks";
import { useDeleteThread, useRenameThread, useThreads } from "@/core/threads/hooks";
import {
  isManagedWorkbenchThread,
  pathOfThreadByState,
  titleOfThread,
} from "@/core/threads/utils";

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

export function ThreadsTab() {
  const { data: threads = [], isLoading, error } = useThreads();
  const deleteThread = useDeleteThread();
  const renameThread = useRenameThread();
  const [previewThreadId, setPreviewThreadId] = useState<string | null>(null);
  const [renameThreadId, setRenameThreadId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const deletePreviewQuery = useThreadDeletePreview({
    threadId: previewThreadId,
    enabled: Boolean(previewThreadId),
  });

  const sortedThreads = useMemo(
    () =>
      threads
        .filter((thread) => isManagedWorkbenchThread(thread))
        .sort((left, right) =>
        String(right.updated_at ?? "").localeCompare(String(left.updated_at ?? "")),
      ),
    [threads],
  );

  async function handleDelete(threadId: string) {
    try {
      const result = await deleteThread.mutateAsync({ threadId });
      toast.success(
        result.partial_success
          ? "线程清理已完成，但仍有后续步骤需要人工确认。"
          : "线程已删除。",
      );
    } catch (deleteError) {
      toast.error(
        deleteError instanceof Error ? deleteError.message : "删除线程失败。",
      );
    }
  }

  async function handleRename() {
    if (!renameThreadId || !renameValue.trim()) {
      return;
    }

    try {
      await renameThread.mutateAsync({
        threadId: renameThreadId,
        title: renameValue.trim(),
      });
      toast.success("线程标题已更新。");
      setRenameThreadId(null);
      setRenameValue("");
    } catch (renameError) {
      toast.error(
        renameError instanceof Error ? renameError.message : "重命名线程失败。",
      );
    }
  }

  if (error) {
    return (
      <WorkspaceStatePanel
        state="update-failed"
        label="线程与历史"
        title="读取线程清单失败"
        description={
          error instanceof Error
            ? error.message
            : "管理中心暂时无法读取线程与历史信息。"
        }
      />
    );
  }

  if (isLoading) {
    return (
      <WorkspaceStatePanel
        state="data-interrupted"
        label="线程与历史"
        title="正在读取线程与历史"
        description="正在同步规范线程清单、删除预览和标题信息。"
      />
    );
  }

  return (
    <>
      <div className="grid gap-5">
        <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="workspace-kicker text-rose-700 dark:text-rose-300">
                线程清单
              </div>
              <h3 className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                规范线程生命周期
              </h3>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                这里仅保留真实可管理的规范线程。你可以直接预览删除影响、重命名线程，并确认后端级联删除会清掉关联数据。
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-3 text-sm dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                活跃线程
              </div>
              <div className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                {sortedThreads.length}
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-3">
            {sortedThreads.map((thread) => (
              <div
                key={thread.thread_id}
                className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40"
              >
                <div className="flex items-start justify-between gap-4">
                  <Link
                    href={pathOfThreadByState(thread)}
                    className="min-w-0 flex-1 rounded-xl transition-colors hover:bg-slate-100/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 dark:hover:bg-slate-800/60 dark:focus-visible:ring-sky-700"
                  >
                    <div className="p-1">
                      <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                        {titleOfThread(thread)}
                      </div>
                      <div className="mt-1 break-all text-xs text-slate-500 dark:text-slate-400">
                        {thread.thread_id}
                      </div>
                      <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                        {pathOfThreadByState(thread)}
                      </div>
                    </div>
                  </Link>
                  <div className="flex flex-wrap justify-end gap-2">
                    <Button asChild variant="outline" size="sm">
                      <Link href={pathOfThreadByState(thread)}>
                        <ArrowUpRightIcon className="mr-1.5 size-4" />
                        打开线程
                      </Link>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setRenameThreadId(thread.thread_id);
                        setRenameValue(titleOfThread(thread));
                      }}
                    >
                      <PencilIcon className="mr-1.5 size-4" />
                      重命名
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPreviewThreadId(thread.thread_id)}
                    >
                      <Trash2Icon className="mr-1.5 size-4" />
                      删除预览
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <Dialog
        open={previewThreadId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setPreviewThreadId(null);
          }
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>删除预览</DialogTitle>
            <DialogDescription>
              线程删除会先调用后端级联清理接口，这里展示本地文件影响和 LangGraph 状态。
            </DialogDescription>
          </DialogHeader>

          {deletePreviewQuery.data ? (
            <div className="grid gap-4 text-sm">
              <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
                <div className="font-semibold text-slate-950 dark:text-slate-50">
                  {deletePreviewQuery.data.thread_id}
                </div>
                <div className="mt-2 text-slate-600 dark:text-slate-300">
                  线程目录：{deletePreviewQuery.data.local_storage.thread_dir}
                </div>
                <div className="mt-2 text-slate-600 dark:text-slate-300">
                  预计删除文件：{deletePreviewQuery.data.impact_summary.total_files} 个
                </div>
                <div className="mt-1 text-slate-600 dark:text-slate-300">
                  预计回收空间：{formatBytes(deletePreviewQuery.data.impact_summary.total_bytes)}
                </div>
                <div className="mt-1 text-slate-600 dark:text-slate-300">
                  LangGraph 状态：{deletePreviewQuery.data.langgraph_state.status}
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                {([
                  ["工作区", deletePreviewQuery.data.local_storage.workspace],
                  ["上传区", deletePreviewQuery.data.local_storage.uploads],
                  ["输出区", deletePreviewQuery.data.local_storage.outputs],
                ] as const).map(([label, slice]) => (
                  <div
                    key={label}
                    className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40"
                  >
                    <div className="font-semibold text-slate-950 dark:text-slate-50">
                      {label}
                    </div>
                    <div className="mt-2 text-slate-600 dark:text-slate-300">
                      {slice.file_count} 个文件
                    </div>
                    <div className="mt-1 text-slate-600 dark:text-slate-300">
                      {formatBytes(slice.total_bytes)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <WorkspaceStatePanel
              state="data-interrupted"
              label="线程与历史"
              title="正在读取删除预览"
              description="正在向后端请求线程删除影响详情。"
            />
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setPreviewThreadId(null)}>
              取消
            </Button>
            <Button
              variant="destructive"
              disabled={!previewThreadId || deleteThread.isPending}
              onClick={async () => {
                if (!previewThreadId) {
                  return;
                }
                await handleDelete(previewThreadId);
                setPreviewThreadId(null);
              }}
            >
              {deleteThread.isPending ? "删除中..." : "确认删除线程"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={renameThreadId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setRenameThreadId(null);
            setRenameValue("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>重命名线程</DialogTitle>
            <DialogDescription>
              更新后会同步影响工作区里所有展示这个线程标题的地方。
            </DialogDescription>
          </DialogHeader>
          <Input
            value={renameValue}
            onChange={(event) => setRenameValue(event.target.value)}
            placeholder="输入新的线程标题"
          />
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setRenameThreadId(null);
                setRenameValue("");
              }}
            >
              取消
            </Button>
            <Button
              onClick={() => void handleRename()}
              disabled={renameThread.isPending || renameValue.trim().length === 0}
            >
              {renameThread.isPending ? "保存中..." : "保存标题"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
