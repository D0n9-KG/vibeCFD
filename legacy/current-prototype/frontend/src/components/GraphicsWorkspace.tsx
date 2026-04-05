import { useMemo, useState } from "react";

import { resolveArtifactUrl } from "../lib/api";
import { formatMetricLabel, formatMetricValue } from "../lib/display";
import type { ArtifactItem, RunSummary } from "../lib/types";
import { ModelViewport } from "./ModelViewport";

type GraphicsTab = "graphics" | "compare" | "mapping";

const VIEW_LABELS: Record<GraphicsTab, string> = {
  graphics: "图形视图",
  compare: "结果对比",
  mapping: "案例映射"
};

function pickImageArtifacts(run: RunSummary | null): ArtifactItem[] {
  const priority = new Map<string, number>([
    ["pressure_distribution.svg", 0],
    ["wake_field.svg", 1],
    ["geometry_overview.svg", 2]
  ]);

  return [...(run?.artifacts ?? [])]
    .filter((artifact) => artifact.category === "image")
    .sort((left, right) => {
      const leftPriority = [...priority.entries()].find(([needle]) =>
        left.relative_path.includes(needle)
      )?.[1] ?? 99;
      const rightPriority = [...priority.entries()].find(([needle]) =>
        right.relative_path.includes(needle)
      )?.[1] ?? 99;
      return leftPriority - rightPriority;
    });
}

function pickModelArtifact(run: RunSummary | null): ArtifactItem | undefined {
  return (run?.artifacts ?? []).find((artifact) => artifact.category === "model");
}

function renderViewportContent(
  artifact: ArtifactItem | undefined,
  placeholderTitle: string,
  placeholderText: string
) {
  if (artifact) {
    return <img className="viewport-image" src={resolveArtifactUrl(artifact.url)} alt={artifact.label} />;
  }

  return (
    <div className="viewport-placeholder">
      <p className="viewport-placeholder__title">{placeholderTitle}</p>
      <p>{placeholderText}</p>
    </div>
  );
}

interface GraphicsWorkspaceProps {
  run: RunSummary | null;
}

export function GraphicsWorkspace({ run }: GraphicsWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<GraphicsTab>("graphics");
  const imageArtifacts = useMemo(() => pickImageArtifacts(run), [run]);
  const modelArtifact = useMemo(() => pickModelArtifact(run), [run]);
  const primaryImage = modelArtifact ? imageArtifacts[0] : imageArtifacts[0];
  const secondaryImage = modelArtifact ? imageArtifacts[0] : imageArtifacts[1];
  const metricEntries = Object.entries(run?.metrics ?? {});

  return (
    <section className="workspace-panel">
      <div className="workspace-topbar">
        <div className="workspace-tabs">
          {(Object.keys(VIEW_LABELS) as GraphicsTab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              className={`workspace-tab ${activeTab === tab ? "workspace-tab--active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {VIEW_LABELS[tab]}
            </button>
          ))}
        </div>
        <div className="workspace-meta">
          <span>{run?.selected_case?.title ?? "等待选择案例"}</span>
          <strong>{run?.stage_label ?? "未开始"}</strong>
        </div>
      </div>

      {activeTab === "graphics" && (
        <div className="workspace-grid">
          <article className="viewport viewport--primary">
            <header className="viewport__header">
              <span>主视窗</span>
              <strong>{modelArtifact?.label ?? primaryImage?.label ?? "几何 / 结果主图"}</strong>
            </header>
            {modelArtifact ? (
              <ModelViewport artifact={modelArtifact} />
            ) : (
              renderViewportContent(
                primaryImage,
                "等待主图",
                run
                  ? "当前运行尚未生成主图时，这里会优先显示几何概览或核心结果图。"
                  : "提交新任务或载入历史运行后，这里会显示最重要的几何预览与结果图。"
              )
            )}
          </article>

          <div className="workspace-side">
            <article className="viewport viewport--secondary">
              <header className="viewport__header">
                <span>副视窗</span>
                <strong>{secondaryImage?.label ?? "压力 / 尾流对照"}</strong>
              </header>
              {renderViewportContent(
                secondaryImage,
                "等待对照图",
                run
                  ? "这里用于展示第二张关键图、截面对比或当前阶段的辅助结果。"
                  : "载入运行后，这里会显示压力分布、尾流切片或结果对照图。"
              )}
            </article>

            <article className="workspace-summary-card">
              <header className="viewport__header">
                <span>当前摘要</span>
                <strong>{run?.run_id ?? "未载入 Run"}</strong>
              </header>
              <dl className="workspace-summary">
                <div>
                  <dt>任务</dt>
                  <dd>{run?.request.task_description ?? "请在左侧创建任务或载入历史运行。"}</dd>
                </div>
                <div>
                  <dt>案例</dt>
                  <dd>{run?.selected_case?.geometry_family ?? "尚未映射"}</dd>
                </div>
                <div>
                  <dt>产物</dt>
                  <dd>{run?.artifacts.length ?? 0} 项</dd>
                </div>
              </dl>
            </article>
          </div>
        </div>
      )}

      {activeTab === "compare" && (
        <div className="workspace-grid workspace-grid--compare">
          <article className="viewport viewport--primary">
            <header className="viewport__header">
              <span>结果对比</span>
              <strong>关键指标</strong>
            </header>
            {metricEntries.length === 0 ? (
              <div className="viewport-placeholder">
                <p className="viewport-placeholder__title">暂无指标</p>
                <p>运行完成后，这里会集中显示阻力、压力和其他关键结果，方便快速判断。</p>
              </div>
            ) : (
              <div className="metric-grid">
                {metricEntries.map(([key, value]) => (
                  <article key={key} className="metric-tile">
                    <span>{formatMetricLabel(key)}</span>
                    <strong>{formatMetricValue(key, value)}</strong>
                  </article>
                ))}
              </div>
            )}
          </article>

          <article className="viewport viewport--secondary">
            <header className="viewport__header">
              <span>对照信息</span>
              <strong>预期输出</strong>
            </header>
            <div className="workspace-note-list">
              {(run?.selected_case?.expected_outputs ?? []).length > 0 ? (
                (run?.selected_case?.expected_outputs ?? []).map((output) => <p key={output}>{output}</p>)
              ) : (
                <p>当前还没有可对照的结果输出。</p>
              )}
            </div>
          </article>
        </div>
      )}

      {activeTab === "mapping" && (
        <div className="workspace-grid workspace-grid--compare">
          <article className="viewport viewport--primary">
            <header className="viewport__header">
              <span>案例映射</span>
              <strong>{run?.selected_case?.title ?? "等待案例"}</strong>
            </header>
            <div className="workspace-note-list">
              <p>{run?.geometry_check ?? "当前尚未执行几何检查。"}</p>
              <p>{run?.workflow_draft?.summary ?? "生成案例后，这里会显示推荐流程与映射摘要。"}</p>
            </div>
          </article>

          <article className="viewport viewport--secondary">
            <header className="viewport__header">
              <span>允许工具</span>
              <strong>{run?.workflow_draft?.allowed_tools.length ?? 0} 项</strong>
            </header>
            <div className="chip-grid">
              {(run?.workflow_draft?.allowed_tools ?? []).length > 0 ? (
                run?.workflow_draft?.allowed_tools.map((tool) => (
                  <span key={tool} className="info-chip">
                    {tool}
                  </span>
                ))
              ) : (
                <p className="workspace-empty-line">当前没有可展示的工具约束。</p>
              )}
            </div>
          </article>
        </div>
      )}
    </section>
  );
}
