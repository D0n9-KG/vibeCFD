import { formatRunStatus } from "../lib/display";
import type { RunSummary } from "../lib/types";

interface WorkbenchHeaderProps {
  run: RunSummary | null;
  completionRatio: number;
  historyCount: number;
  refreshing: boolean;
  confirming: boolean;
  cancelling: boolean;
  retrying: boolean;
  onCreateNewTask: () => void;
  onRefresh: () => void;
  onConfirm: () => void;
  onCancel: () => void;
  onRetry?: (() => void) | undefined;
}

function formatStatus(run: RunSummary | null): string {
  if (!run) {
    return "等待载入";
  }
  return formatRunStatus(run.status);
}

export function WorkbenchHeader({
  run,
  completionRatio,
  historyCount,
  refreshing,
  confirming,
  cancelling,
  retrying,
  onCreateNewTask,
  onRefresh,
  onConfirm,
  onCancel,
  onRetry
}: WorkbenchHeaderProps) {
  const canConfirm = run?.status === "awaiting_confirmation";
  const canCancel = run?.status === "queued";
  const canRetry = Boolean(run && run.status !== "queued" && run.status !== "running" && onRetry);

  return (
    <header className="workbench-header">
      <div className="workbench-brand">
        <div className="workbench-brand__mark" aria-hidden="true">
          CFD
        </div>
        <div>
          <p className="section-kicker">Submarine CFD</p>
          <h1>潜艇仿真工作台</h1>
          <p className="section-caption">案例检索、流程确认、运行追踪与结果复盘集中在同一工作界面。</p>
        </div>
      </div>

      <div className="workbench-toolbar">
        <div className="command-group">
          <button type="button" className="command-button command-button--primary" onClick={onCreateNewTask}>
            新建任务
          </button>
          <button type="button" className="command-button" onClick={onRefresh} disabled={refreshing}>
            {refreshing ? "刷新中" : "刷新列表"}
          </button>
        </div>

        <div className="command-group">
          <button type="button" className="command-button" onClick={onConfirm} disabled={!canConfirm || confirming}>
            {confirming ? "确认中" : "确认执行"}
          </button>
          <button type="button" className="command-button" onClick={onCancel} disabled={!canCancel || cancelling}>
            {cancelling ? "取消中" : "取消排队"}
          </button>
          <button type="button" className="command-button" onClick={onRetry} disabled={!canRetry || retrying}>
            {retrying ? "重试中" : "重试运行"}
          </button>
        </div>
      </div>

      <div className="workbench-statusbar">
        <div className="status-card">
          <span>当前 Run</span>
          <strong>{run?.run_id ?? "未载入"}</strong>
        </div>
        <div className="status-card">
          <span>状态</span>
          <strong>{formatStatus(run)}</strong>
        </div>
        <div className="status-card">
          <span>流程进度</span>
          <strong>{completionRatio}%</strong>
        </div>
        <div className="status-card">
          <span>历史记录</span>
          <strong>{historyCount} 条</strong>
        </div>
      </div>
    </header>
  );
}
