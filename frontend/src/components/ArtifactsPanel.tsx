import type { ArtifactItem, RunSummary } from "../lib/types";

function renderArtifactPreview(artifact: ArtifactItem) {
  if (artifact.category === "image") {
    return <img src={artifact.url} alt={artifact.label} className="artifact-image" />;
  }

  return (
    <a className="artifact-link" href={artifact.url} target="_blank" rel="noreferrer">
      打开 {artifact.label}
    </a>
  );
}

interface ArtifactsPanelProps {
  run: RunSummary;
}

export function ArtifactsPanel({ run }: ArtifactsPanelProps) {
  return (
    <section className="glass-panel">
      <div className="section-heading">
        <p className="eyebrow">Artifacts & Report</p>
        <h2>产物目录与最终报告</h2>
        <p className="muted">这里集中展示当前 run 的关键图像、结构化结果、日志和交付报告。</p>
      </div>

      <div className="artifact-grid">
        {run.artifacts.length === 0 ? (
          <p className="muted">确认并执行后，这里会出现几何概览、压力图、尾流图、结果表格和最终报告。</p>
        ) : (
          run.artifacts.map((artifact) => (
            <article key={artifact.relative_path} className="artifact-card">
              <div className="artifact-card__head">
                <h3>{artifact.label}</h3>
                <span className="tag tag--dark">{artifact.category}</span>
              </div>
              <p className="muted">{artifact.relative_path}</p>
              {renderArtifactPreview(artifact)}
            </article>
          ))
        )}
      </div>

      <div className="report-panel">
        <h3>Markdown 报告</h3>
        <pre>{run.report_markdown ?? "等待执行完成后生成最终报告。"}</pre>
      </div>
    </section>
  );
}
