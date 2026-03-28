import { formatRunStatus, formatTaskType } from "../lib/display";
import type { RunSummary } from "../lib/types";

interface RunHistoryPanelProps {
  runs: RunSummary[];
  currentRunId?: string | null;
  loading: boolean;
  retryingRunId?: string | null;
  onSelect: (runId: string) => void;
  onRetry: (runId: string) => void;
}

function formatDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export function RunHistoryPanel({
  runs,
  currentRunId,
  loading,
  retryingRunId,
  onSelect,
  onRetry
}: RunHistoryPanelProps) {
  return (
    <section className="sidebar-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">运行</p>
          <h2>历史运行</h2>
        </div>
        <span className="panel-tag">最近 {runs.length} 条</span>
      </div>

      {loading ? (
        <p className="panel-empty">正在读取历史运行记录。</p>
      ) : runs.length === 0 ? (
        <p className="panel-empty">还没有可显示的历史 run。</p>
      ) : (
        <div className="sidebar-list">
          {runs.map((item) => {
            const isCurrent = item.run_id === currentRunId;
            const canRetry = item.status !== "queued" && item.status !== "running";

            return (
              <article key={item.run_id} className={`history-row ${isCurrent ? "history-row--current" : ""}`}>
                <div className="sidebar-row__head">
                  <strong>{item.run_id}</strong>
                  <span className="state-badge">{formatRunStatus(item.status)}</span>
                </div>
                <p className="sidebar-row__text">{item.request.task_description}</p>
                <p className="sidebar-row__meta">
                  {formatTaskType(item.request.task_type)} · {item.request.geometry_family_hint || "未指定"}
                </p>
                <p className="sidebar-row__meta">更新时间：{formatDate(item.updated_at)}</p>
                <div className="sidebar-actions">
                  <button type="button" className="secondary-action" onClick={() => onSelect(item.run_id)}>
                    载入
                  </button>
                  {canRetry && (
                    <button
                      type="button"
                      className="secondary-action secondary-action--accent"
                      disabled={retryingRunId === item.run_id}
                      onClick={() => onRetry(item.run_id)}
                    >
                      {retryingRunId === item.run_id ? "重试中" : "重试"}
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
