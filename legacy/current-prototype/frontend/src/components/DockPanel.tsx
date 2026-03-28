import { useEffect, useMemo, useState } from "react";

import type { ExecutionAttempt, RunEvent, RunSummary } from "../lib/types";

type DockTab = "workflow" | "timeline" | "events" | "attempts" | "artifacts" | "report";

const DOCK_TABS: Array<{ id: DockTab; label: string }> = [
  { id: "workflow", label: "流程详情" },
  { id: "timeline", label: "时间线" },
  { id: "events", label: "运行事件" },
  { id: "attempts", label: "执行尝试" },
  { id: "artifacts", label: "产物目录" },
  { id: "report", label: "最终报告" }
];

const ATTEMPT_STATUS_COPY: Record<ExecutionAttempt["status"], string> = {
  running: "运行中",
  completed: "已完成",
  failed: "失败"
};

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

function formatDetails(details: RunEvent["details"]): string | null {
  const entries = Object.entries(details).filter(([, value]) => value !== null);
  if (entries.length === 0) {
    return null;
  }
  return entries.map(([key, value]) => `${key}: ${String(value)}`).join(" · ");
}

function formatDuration(durationSeconds?: number | null): string {
  if (durationSeconds === null || durationSeconds === undefined) {
    return "记录中";
  }
  if (durationSeconds < 1) {
    return `${Math.round(durationSeconds * 1000)} ms`;
  }
  return `${durationSeconds.toFixed(durationSeconds >= 10 ? 1 : 3)} s`;
}

function getPreferredDockTab(
  run: RunSummary | null,
  events: RunEvent[],
  attempts: ExecutionAttempt[]
): DockTab {
  if (!run) {
    return "timeline";
  }

  if (run.status === "draft" || run.status === "awaiting_confirmation") {
    return run.workflow_draft ? "workflow" : "timeline";
  }

  if (run.status === "queued" || run.status === "running") {
    return "timeline";
  }

  if (run.status === "completed") {
    if (run.artifacts.length > 0) {
      return "artifacts";
    }
    if (run.report_markdown) {
      return "report";
    }
    return "timeline";
  }

  if (run.status === "failed") {
    if (attempts.length > 0) {
      return "attempts";
    }
    if (events.length > 0) {
      return "events";
    }
    return "timeline";
  }

  if (run.status === "cancelled") {
    return events.length > 0 ? "events" : "timeline";
  }

  return "timeline";
}

interface DockPanelProps {
  run: RunSummary | null;
  events: RunEvent[];
  attempts: ExecutionAttempt[];
}

export function DockPanel({ run, events, attempts }: DockPanelProps) {
  const preferredTab = useMemo(
    () => getPreferredDockTab(run, events, attempts),
    [run, events, attempts]
  );
  const [activeTab, setActiveTab] = useState<DockTab>(preferredTab);

  useEffect(() => {
    setActiveTab(preferredTab);
  }, [preferredTab, run?.run_id, run?.status]);

  return (
    <section className="dock-panel">
      <div className="dock-tabs" role="tablist" aria-label="运行详情标签页">
        {DOCK_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`dock-tab ${activeTab === tab.id ? "dock-tab--active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="dock-content">
        {!run && (
          <div className="dock-empty">
            <p className="dock-empty__title">等待任务或历史运行</p>
            <p>左侧提交新任务后，这里会集中显示流程详情、时间线、运行事件、产物和最终报告。</p>
          </div>
        )}

        {run && activeTab === "workflow" && (
          <div className="dock-section-grid">
            <article className="dock-card">
              <h3>推荐摘要</h3>
              <p>{run.workflow_draft?.summary ?? "当前运行还没有生成流程摘要。"}</p>
            </article>
            <article className="dock-card">
              <h3>默认假设</h3>
              <ul className="dock-list">
                {(run.workflow_draft?.assumptions ?? []).length > 0 ? (
                  run.workflow_draft?.assumptions.map((item) => <li key={item}>{item}</li>)
                ) : (
                  <li>当前还没有补充默认假设。</li>
                )}
              </ul>
            </article>
            <article className="dock-card dock-card--wide">
              <h3>阶段说明</h3>
              <div className="dock-stage-list">
                {(run.workflow_draft?.stages ?? []).length > 0 ? (
                  run.workflow_draft?.stages.map((stage, index) => (
                    <article key={stage.stage_id} className="dock-stage-item">
                      <span>{index + 1}</span>
                      <div>
                        <strong>{stage.title}</strong>
                        <p>{stage.description}</p>
                      </div>
                    </article>
                  ))
                ) : (
                  <p>当前还没有阶段说明。</p>
                )}
              </div>
            </article>
          </div>
        )}

        {run && activeTab === "timeline" && (
          <div className="dock-list-panel">
            {run.timeline.length === 0 ? (
              <p className="dock-empty-line">当前还没有时间线记录。</p>
            ) : (
              run.timeline.map((item) => (
                <article key={`${item.stage}-${item.timestamp}`} className="dock-log-item">
                  <div className="dock-log-item__meta">
                    <strong>{item.stage}</strong>
                    <span>{formatDateTime(item.timestamp)}</span>
                  </div>
                  <p>{item.message}</p>
                </article>
              ))
            )}
          </div>
        )}

        {run && activeTab === "events" && (
          <div className="dock-list-panel">
            {events.length === 0 ? (
              <p className="dock-empty-line">当前还没有结构化运行事件。</p>
            ) : (
              events.map((event) => {
                const details = formatDetails(event.details);
                return (
                  <article key={event.event_id} className="dock-log-item">
                    <div className="dock-log-item__meta">
                      <strong>{event.event_type}</strong>
                      <span>{formatDateTime(event.timestamp)}</span>
                    </div>
                    <p>{event.message}</p>
                    <p className="dock-subtle">
                      阶段：{event.stage} · 状态：{event.status}
                    </p>
                    {details && <p className="dock-subtle">{details}</p>}
                  </article>
                );
              })
            )}
          </div>
        )}

        {run && activeTab === "attempts" && (
          <div className="dock-list-panel">
            {attempts.length === 0 ? (
              <p className="dock-empty-line">当前还没有执行尝试记录。</p>
            ) : (
              attempts.map((attempt) => (
                <article key={attempt.attempt_id} className="dock-log-item">
                  <div className="dock-log-item__meta">
                    <strong>Attempt #{attempt.attempt_number}</strong>
                    <span>{ATTEMPT_STATUS_COPY[attempt.status]}</span>
                  </div>
                  <p className="dock-subtle">
                    {formatDateTime(attempt.started_at)}
                    {attempt.finished_at ? ` -> ${formatDateTime(attempt.finished_at)}` : ""}
                  </p>
                  <div className="dock-detail-grid">
                    <p>
                      <span>执行引擎</span>
                      <strong>{attempt.engine_name}</strong>
                    </p>
                    <p>
                      <span>耗时</span>
                      <strong>{formatDuration(attempt.duration_seconds)}</strong>
                    </p>
                    {attempt.failure_category && (
                      <p>
                        <span>失败分类</span>
                        <strong>{attempt.failure_category}</strong>
                      </p>
                    )}
                    {attempt.failure_source && (
                      <p>
                        <span>失败来源</span>
                        <strong>{attempt.failure_source}</strong>
                      </p>
                    )}
                  </div>
                  {attempt.summary && <p>{attempt.summary}</p>}
                  {attempt.error_message && <p className="dock-subtle">{attempt.error_message}</p>}
                </article>
              ))
            )}
          </div>
        )}

        {run && activeTab === "artifacts" && (
          <div className="dock-artifact-grid">
            {run.artifacts.length === 0 ? (
              <p className="dock-empty-line">运行完成后，这里会显示日志、图像、表格和结构化结果。</p>
            ) : (
              run.artifacts.map((artifact) => (
                <article key={artifact.relative_path} className="dock-artifact-card">
                  <div className="dock-log-item__meta">
                    <strong>{artifact.label}</strong>
                    <span>{artifact.category}</span>
                  </div>
                  <p className="dock-subtle">{artifact.relative_path}</p>
                  {artifact.category === "image" ? (
                    <img className="dock-artifact-image" src={artifact.url} alt={artifact.label} />
                  ) : (
                    <a href={artifact.url} target="_blank" rel="noreferrer">
                      打开产物
                    </a>
                  )}
                </article>
              ))
            )}
          </div>
        )}

        {run && activeTab === "report" && (
          <article className="dock-report">
            <h3>最终报告</h3>
            <pre>{run.report_markdown ?? "当前还没有生成最终报告。"}</pre>
          </article>
        )}
      </div>
    </section>
  );
}
