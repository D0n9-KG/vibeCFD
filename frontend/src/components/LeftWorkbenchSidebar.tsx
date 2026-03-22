import { CandidateCases } from "./CandidateCases";
import { RunHistoryPanel } from "./RunHistoryPanel";
import { TaskForm } from "./TaskForm";
import type { TaskFormInput } from "../lib/api";
import type { RunSummary } from "../lib/types";

export type LeftWorkspaceView = "task" | "cases" | "history";

const VIEW_META: Record<
  LeftWorkspaceView,
  { label: string; description: string; countLabel?: (count: number) => string }
> = {
  task: {
    label: "任务",
    description: "创建新任务并整理输入条件。"
  },
  cases: {
    label: "案例",
    description: "查看系统映射出的候选案例与推荐复用方向。",
    countLabel: (count) => `${count}`
  },
  history: {
    label: "历史",
    description: "在已有运行之间切换、复盘或重试。",
    countLabel: (count) => `${count}`
  }
};

interface LeftWorkbenchSidebarProps {
  activeView: LeftWorkspaceView;
  run: RunSummary | null;
  runs: RunSummary[];
  historyLoading: boolean;
  retryingRunId?: string | null;
  submitting?: boolean;
  onChangeView: (view: LeftWorkspaceView) => void;
  onSubmit: (payload: TaskFormInput) => Promise<void>;
  onSelect: (runId: string) => void;
  onRetry: (runId: string) => void;
}

export function LeftWorkbenchSidebar({
  activeView,
  run,
  runs,
  historyLoading,
  retryingRunId,
  submitting = false,
  onChangeView,
  onSubmit,
  onSelect,
  onRetry
}: LeftWorkbenchSidebarProps) {
  const candidateCount = run?.candidate_cases.length ?? 0;

  return (
    <div className="left-sidebar-workspace">
      <section className="sidebar-switcher">
        <div className="sidebar-switcher__tabs" role="tablist" aria-label="左侧工作区">
          {(Object.keys(VIEW_META) as LeftWorkspaceView[]).map((view) => {
            const meta = VIEW_META[view];
            const count = view === "cases" ? candidateCount : view === "history" ? runs.length : 0;

            return (
              <button
                key={view}
                type="button"
                role="tab"
                aria-selected={activeView === view}
                className={`sidebar-view-tab ${activeView === view ? "sidebar-view-tab--active" : ""}`}
                onClick={() => onChangeView(view)}
              >
                <span>{meta.label}</span>
                {meta.countLabel && <small>{meta.countLabel(count)}</small>}
              </button>
            );
          })}
        </div>

        <div className="sidebar-switcher__summary">
          <strong>{VIEW_META[activeView].label}</strong>
          <p>{VIEW_META[activeView].description}</p>
        </div>
      </section>

      <div className="left-sidebar-workspace__content">
        {activeView === "task" && <TaskForm disabled={submitting} onSubmit={onSubmit} />}
        {activeView === "cases" && (
          <CandidateCases
            candidates={run?.candidate_cases ?? []}
            selectedCaseId={run?.selected_case?.case_id}
          />
        )}
        {activeView === "history" && (
          <RunHistoryPanel
            runs={runs}
            currentRunId={run?.run_id}
            loading={historyLoading}
            retryingRunId={retryingRunId}
            onSelect={onSelect}
            onRetry={onRetry}
          />
        )}
      </div>
    </div>
  );
}
