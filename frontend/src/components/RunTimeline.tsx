import type { ExecutionAttempt, RunEvent, RunSummary } from "../lib/types";

interface RunTimelineProps {
  run: RunSummary;
  events: RunEvent[];
  attempts: ExecutionAttempt[];
}

const attemptStatusLabels: Record<ExecutionAttempt["status"], string> = {
  running: "运行中",
  completed: "已完成",
  failed: "失败",
};

const failureCategoryLabels: Record<string, string> = {
  dispatch_launch_error: "派发启动失败",
  executor_request_failed: "执行器请求失败",
  executor_reported_failure: "执行器返回失败",
  execution_failure: "执行过程失败",
  service_restart_interruption: "服务重启中断",
};

const failureSourceLabels: Record<string, string> = {
  dispatcher: "dispatcher",
  claude_executor_client: "claude-executor client",
  claude_executor: "claude-executor",
  execution_engine: "execution engine",
  store_recovery: "store recovery",
};

function formatDetails(details: RunEvent["details"]): string | null {
  const entries = Object.entries(details).filter(([, value]) => value !== null);
  if (entries.length === 0) {
    return null;
  }
  return entries.map(([key, value]) => `${key}: ${String(value)}`).join(" · ");
}

function formatAttemptTime(startedAt: string, finishedAt?: string | null): string {
  const started = new Date(startedAt).toLocaleString();
  if (!finishedAt) {
    return `开始于 ${started}`;
  }
  return `${started} -> ${new Date(finishedAt).toLocaleString()}`;
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

function labelFailureCategory(value?: string | null): string | null {
  if (!value) {
    return null;
  }
  return failureCategoryLabels[value] ?? value;
}

function labelFailureSource(value?: string | null): string | null {
  if (!value) {
    return null;
  }
  return failureSourceLabels[value] ?? value;
}

export function RunTimeline({ run, events, attempts }: RunTimelineProps) {
  const metricEntries = Object.entries(run.metrics ?? {});

  return (
    <section className="glass-panel">
      <div className="section-heading">
        <p className="eyebrow">Execution Trace</p>
        <h2>运行时间线</h2>
        <p className="muted">
          当前状态：<strong>{run.stage_label}</strong>
        </p>
      </div>

      <div className="timeline">
        {run.timeline.length === 0 ? (
          <p className="muted">等待任务进入案例检索阶段。</p>
        ) : (
          run.timeline.map((event) => (
            <article
              key={`${event.stage}-${event.timestamp}`}
              className={`timeline-item timeline-item--${event.status}`}
            >
              <div className="timeline-item__dot" />
              <div>
                <div className="timeline-item__meta">
                  <strong>{event.stage}</strong>
                  <span>{new Date(event.timestamp).toLocaleString()}</span>
                </div>
                <p>{event.message}</p>
              </div>
            </article>
          ))
        )}
      </div>

      <div className="event-log">
        <div className="section-heading">
          <p className="eyebrow">Run Events</p>
          <h3>结构化事件历史</h3>
        </div>
        {events.length === 0 ? (
          <p className="muted">当前还没有可展示的结构化事件。</p>
        ) : (
          <div className="event-log__list">
            {events.map((event) => {
              const details = formatDetails(event.details);
              return (
                <article key={event.event_id} className="event-item">
                  <div className="event-item__meta">
                    <strong>{event.event_type}</strong>
                    <span>{new Date(event.timestamp).toLocaleString()}</span>
                  </div>
                  <p>{event.message}</p>
                  <p className="muted">
                    阶段：{event.stage} · 状态：{event.status}
                  </p>
                  {details && <p className="muted">{details}</p>}
                </article>
              );
            })}
          </div>
        )}
      </div>

      <div className="attempt-log">
        <div className="section-heading">
          <p className="eyebrow">Execution Attempts</p>
          <h3>执行尝试历史</h3>
        </div>
        {attempts.length === 0 ? (
          <p className="muted">当前还没有执行尝试记录。</p>
        ) : (
          <div className="attempt-log__list">
            {attempts.map((attempt) => {
              const failureCategory = labelFailureCategory(attempt.failure_category);
              const failureSource = labelFailureSource(attempt.failure_source);

              return (
                <article key={attempt.attempt_id} className="attempt-item">
                  <div className="attempt-item__meta">
                    <strong>Attempt #{attempt.attempt_number}</strong>
                    <span className={`tag tag--dark tag--attempt-${attempt.status}`}>
                      {attemptStatusLabels[attempt.status]}
                    </span>
                  </div>
                  <p className="muted">{formatAttemptTime(attempt.started_at, attempt.finished_at)}</p>
                  <div className="attempt-item__details">
                    <p>
                      <span>执行引擎</span>
                      <strong>{attempt.engine_name}</strong>
                    </p>
                    <p>
                      <span>耗时</span>
                      <strong>{formatDuration(attempt.duration_seconds)}</strong>
                    </p>
                    {failureCategory && (
                      <p>
                        <span>失败分类</span>
                        <strong>{failureCategory}</strong>
                      </p>
                    )}
                    {failureSource && (
                      <p>
                        <span>失败来源</span>
                        <strong>{failureSource}</strong>
                      </p>
                    )}
                  </div>
                  {attempt.summary && <p>{attempt.summary}</p>}
                  {attempt.error_message && <p className="muted">{attempt.error_message}</p>}
                </article>
              );
            })}
          </div>
        )}
      </div>

      {metricEntries.length > 0 && (
        <div className="metrics-grid">
          {metricEntries.map(([key, value]) => (
            <article key={key} className="metric-card">
              <span>{key}</span>
              <strong>{value}</strong>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
