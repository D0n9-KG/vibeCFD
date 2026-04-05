import { formatRunStatus } from "../lib/display";
import type { RunSummary } from "../lib/types";

interface WorkflowDraftProps {
  run: RunSummary | null;
  completionRatio: number;
  confirming: boolean;
  cancelling: boolean;
  onConfirm: () => Promise<void>;
  onCancel: () => Promise<void>;
}

export function WorkflowDraft({
  run,
  completionRatio,
  confirming,
  cancelling,
  onConfirm,
  onCancel
}: WorkflowDraftProps) {
  const canConfirm = run?.status === "awaiting_confirmation";
  const canCancel = run?.status === "queued";
  const metricEntries = Object.entries(run?.metrics ?? {});
  const tools = run?.workflow_draft?.allowed_tools ?? [];
  const artifacts = run?.workflow_draft?.required_artifacts ?? [];
  const stages = run?.workflow_draft?.stages ?? [];

  return (
    <section className="inspector-stack">
      <article className="inspector-panel">
        <div className="panel-heading">
          <div>
            <p className="section-kicker">检查器</p>
            <h2>流程确认</h2>
          </div>
          <span className="state-badge">{run ? formatRunStatus(run.status) : "未载入"}</span>
        </div>

        <p className="panel-description">
          {run?.workflow_draft?.summary ??
            "左侧提交任务或载入历史运行后，这里会显示推荐流程、当前阶段和确认动作。"}
        </p>

        <div className="inspector-metric-strip">
          <div>
            <span>进度</span>
            <strong>{run ? `${completionRatio}%` : "--"}</strong>
          </div>
          <div>
            <span>当前阶段</span>
            <strong>{run?.stage_label ?? "未开始"}</strong>
          </div>
        </div>

        <p className="inspector-note">
          {run?.geometry_check ??
            "尚未执行几何检查。创建任务后，这里会先给出几何检查和案例映射结论。"}
        </p>

        {stages.length > 0 ? (
          <div className="inspector-stage-list">
            {stages.slice(0, 4).map((stage, index) => (
              <article key={stage.stage_id} className="inspector-stage-item">
                <span>{index + 1}</span>
                <div>
                  <strong>{stage.title}</strong>
                  <p>{stage.description}</p>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="inspector-placeholder-list">
            <p>1. 检索案例并生成推荐流程</p>
            <p>2. 人工确认后进入排队和调度</p>
            <p>3. 结果、事件和报告统一回写到 run 目录</p>
          </div>
        )}

        <div className="inspector-actions">
          <button
            className="primary-action"
            type="button"
            onClick={() => void onConfirm()}
            disabled={!canConfirm || confirming}
          >
            {confirming ? "确认中" : "确认执行"}
          </button>
          <button
            className="secondary-action secondary-action--danger"
            type="button"
            onClick={() => void onCancel()}
            disabled={!canCancel || cancelling}
          >
            {cancelling ? "取消中" : "取消排队"}
          </button>
        </div>
      </article>

      <article className="inspector-panel">
        <div className="panel-heading">
          <div>
            <p className="section-kicker">指标</p>
            <h2>关键指标</h2>
          </div>
        </div>

        {metricEntries.length > 0 ? (
          <div className="inspector-metric-grid">
            {metricEntries.map(([key, value]) => (
              <article key={key} className="metric-tile">
                <span>{key}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>
        ) : (
          <div className="inspector-metric-grid inspector-metric-grid--placeholder">
            <article className="metric-tile">
              <span>阻力</span>
              <strong>待计算</strong>
            </article>
            <article className="metric-tile">
              <span>压力峰值</span>
              <strong>待计算</strong>
            </article>
          </div>
        )}
      </article>

      <article className="inspector-panel">
        <div className="panel-heading">
          <div>
            <p className="section-kicker">摘要</p>
            <h2>工具与产物</h2>
          </div>
        </div>

        {tools.length > 0 ? (
          <div className="chip-grid">
            {tools.map((tool) => (
              <span key={tool} className="info-chip">
                {tool}
              </span>
            ))}
          </div>
        ) : (
          <div className="chip-grid">
            <span className="info-chip">案例工具待生成</span>
            <span className="info-chip">执行约束待生成</span>
          </div>
        )}

        {artifacts.length > 0 ? (
          <ul className="inspector-list">
            {artifacts.map((artifact) => (
              <li key={artifact}>{artifact}</li>
            ))}
          </ul>
        ) : (
          <ul className="inspector-list">
            <li>运行日志</li>
            <li>结果图像</li>
            <li>最终报告</li>
          </ul>
        )}
      </article>
    </section>
  );
}
