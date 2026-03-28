import { useEffect, useMemo, useState } from "react";

import {
  cancelRun,
  confirmRun,
  getRun,
  listRunAttempts,
  listRunEvents,
  listRuns,
  retryRun,
  submitTask,
  type TaskFormInput
} from "./lib/api";
import { DockPanel } from "./components/DockPanel";
import { GraphicsWorkspace } from "./components/GraphicsWorkspace";
import { LeftWorkbenchSidebar, type LeftWorkspaceView } from "./components/LeftWorkbenchSidebar";
import { WorkbenchHeader } from "./components/WorkbenchHeader";
import { WorkflowDraft } from "./components/WorkflowDraft";
import type { ExecutionAttempt, RunEvent, RunSummary } from "./lib/types";

function shouldPoll(run: RunSummary | null): boolean {
  return run?.status === "queued" || run?.status === "running";
}

function pickWorkspaceViewForRun(run: RunSummary | null): LeftWorkspaceView {
  if (run?.candidate_cases.length) {
    return "cases";
  }
  return run ? "history" : "task";
}

function describeError(error: unknown, fallback: string): string {
  if (error instanceof Error) {
    if (error.message === "Failed to fetch") {
      return "无法连接后端服务，请确认 8010 端口的 API 已启动。";
    }
    return error.message;
  }
  return fallback;
}

export default function App() {
  const [run, setRun] = useState<RunSummary | null>(null);
  const [runEvents, setRunEvents] = useState<RunEvent[]>([]);
  const [runAttempts, setRunAttempts] = useState<ExecutionAttempt[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [leftView, setLeftView] = useState<LeftWorkspaceView>("task");
  const [submitting, setSubmitting] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [retryingRunId, setRetryingRunId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshRuns() {
    try {
      setHistoryLoading(true);
      const items = await listRuns();
      setRuns(items);
    } catch (historyError) {
      setError(describeError(historyError, "读取历史运行失败。"));
    } finally {
      setHistoryLoading(false);
    }
  }

  async function loadRunDetails(runId: string) {
    const [nextRun, nextEvents, nextAttempts] = await Promise.all([
      getRun(runId),
      listRunEvents(runId),
      listRunAttempts(runId)
    ]);
    setRun(nextRun);
    setRunEvents(nextEvents);
    setRunAttempts(nextAttempts);
    return nextRun;
  }

  useEffect(() => {
    void refreshRuns();
  }, []);

  useEffect(() => {
    const activeRunId = run?.run_id;
    if (!activeRunId || !shouldPoll(run)) {
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const nextRun = await loadRunDetails(activeRunId);
        if (!shouldPoll(nextRun)) {
          void refreshRuns();
        }
      } catch (pollError) {
        setError(describeError(pollError, "轮询运行状态失败。"));
      }
    }, 1200);

    return () => window.clearInterval(timer);
  }, [run]);

  const completionRatio = useMemo(() => {
    if (!run?.workflow_draft) {
      return 0;
    }
    const total = run.workflow_draft.stages.length;
    if (total === 0) {
      return 0;
    }
    const completed = run.status === "completed" ? total : Math.min(run.timeline.length, total);
    return Math.round((completed / total) * 100);
  }, [run]);

  async function handleSubmit(payload: TaskFormInput) {
    try {
      setSubmitting(true);
      setError(null);
      const createdRun = await submitTask(payload);
      setRun(createdRun);
      setLeftView(pickWorkspaceViewForRun(createdRun));
      const [events, attempts] = await Promise.all([
        listRunEvents(createdRun.run_id),
        listRunAttempts(createdRun.run_id)
      ]);
      setRunEvents(events);
      setRunAttempts(attempts);
      await refreshRuns();
    } catch (submitError) {
      setError(describeError(submitError, "任务提交失败。"));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConfirm() {
    if (!run) {
      return;
    }

    try {
      setConfirming(true);
      setError(null);
      await confirmRun(run.run_id, "操作员确认按照推荐流程继续执行。");
      await loadRunDetails(run.run_id);
      await refreshRuns();
    } catch (confirmError) {
      setError(describeError(confirmError, "确认执行失败。"));
    } finally {
      setConfirming(false);
    }
  }

  async function handleCancel() {
    if (!run) {
      return;
    }

    try {
      setCancelling(true);
      setError(null);
      await cancelRun(run.run_id, "操作员在调度前取消。");
      await loadRunDetails(run.run_id);
      await refreshRuns();
    } catch (cancelError) {
      setError(describeError(cancelError, "取消排队失败。"));
    } finally {
      setCancelling(false);
    }
  }

  async function handleSelect(runId: string) {
    try {
      setError(null);
      const loadedRun = await loadRunDetails(runId);
      setLeftView(pickWorkspaceViewForRun(loadedRun));
    } catch (selectionError) {
      setError(describeError(selectionError, "读取运行详情失败。"));
    }
  }

  async function handleRetry(runId: string) {
    try {
      setRetryingRunId(runId);
      setError(null);
      const retried = await retryRun(runId);
      setRun(retried);
      setLeftView(pickWorkspaceViewForRun(retried));
      const [events, attempts] = await Promise.all([
        listRunEvents(retried.run_id),
        listRunAttempts(retried.run_id)
      ]);
      setRunEvents(events);
      setRunAttempts(attempts);
      await refreshRuns();
    } catch (retryError) {
      setError(describeError(retryError, "重试运行失败。"));
    } finally {
      setRetryingRunId(null);
    }
  }

  function handleCreateNewTask() {
    setRun(null);
    setRunEvents([]);
    setRunAttempts([]);
    setLeftView("task");
    setError(null);
  }

  return (
    <div className="workbench-app">
      <WorkbenchHeader
        run={run}
        completionRatio={completionRatio}
        historyCount={runs.length}
        refreshing={historyLoading}
        confirming={confirming}
        cancelling={cancelling}
        retrying={retryingRunId === run?.run_id}
        onCreateNewTask={handleCreateNewTask}
        onRefresh={() => void refreshRuns()}
        onConfirm={() => void handleConfirm()}
        onCancel={() => void handleCancel()}
        onRetry={run ? () => void handleRetry(run.run_id) : undefined}
      />

      {error && <div className="workbench-banner workbench-banner--error">{error}</div>}

      <div className="workbench-main">
        <aside className="workbench-sidebar workbench-sidebar--left">
          <LeftWorkbenchSidebar
            activeView={leftView}
            run={run}
            runs={runs}
            historyLoading={historyLoading}
            retryingRunId={retryingRunId}
            submitting={submitting}
            onChangeView={setLeftView}
            onSubmit={handleSubmit}
            onSelect={handleSelect}
            onRetry={handleRetry}
          />
        </aside>

        <section className="workbench-center">
          <GraphicsWorkspace run={run} />
          <DockPanel run={run} events={runEvents} attempts={runAttempts} />
        </section>

        <aside className="workbench-sidebar workbench-sidebar--right">
          <WorkflowDraft
            run={run}
            completionRatio={completionRatio}
            confirming={confirming}
            cancelling={cancelling}
            onConfirm={handleConfirm}
            onCancel={handleCancel}
          />
        </aside>
      </div>
    </div>
  );
}
