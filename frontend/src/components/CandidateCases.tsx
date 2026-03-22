import type { CaseCandidate } from "../lib/types";
import { formatTaskType } from "../lib/display";

interface CandidateCasesProps {
  candidates: CaseCandidate[];
  selectedCaseId?: string | null;
}

function shorten(text: string, maxLength = 56): string {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength)}...`;
}

export function CandidateCases({ candidates, selectedCaseId }: CandidateCasesProps) {
  return (
    <section className="sidebar-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">检索</p>
          <h2>候选案例</h2>
        </div>
        <span className="panel-tag">{candidates.length} 条</span>
      </div>

      {candidates.length === 0 ? (
        <p className="panel-empty">提交任务后，这里会显示结构化匹配出的候选案例。</p>
      ) : (
        <div className="sidebar-list">
          {candidates.slice(0, 5).map((candidate, index) => {
            const selected = candidate.case_id === selectedCaseId;
            return (
              <article
                key={candidate.case_id}
                className={`sidebar-row ${selected ? "sidebar-row--selected" : ""}`}
              >
                <div className="sidebar-row__head">
                  <strong>{candidate.title}</strong>
                  <span className="score-badge">{candidate.score.toFixed(2)}</span>
                </div>
                <p className="sidebar-row__meta">
                  候选 {index + 1} · {candidate.geometry_family} · {formatTaskType(candidate.task_type)}
                </p>
                <p className="sidebar-row__text">{shorten(candidate.rationale)}</p>
                <div className="sidebar-chip-row">
                  {candidate.expected_outputs.slice(0, 3).map((output) => (
                    <span key={output} className="info-chip">
                      {output}
                    </span>
                  ))}
                  {selected && <span className="info-chip info-chip--selected">当前采用</span>}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
