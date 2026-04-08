"use client";

import type { SubmarineDetailModel } from "./submarine-detail-model";

export function SubmarineOperatorBoard({
  operatorBoard,
}: {
  operatorBoard: SubmarineDetailModel["operatorBoard"];
}) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
        研究判断与后续安排
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="当前判断" value={operatorBoard.decisionStatus ?? "待判断"} />
        <Metric label="修正事项" value={String(operatorBoard.remediation.actionCount)} />
        <Metric label="研究记录" value={String(operatorBoard.timelineEntryCount)} />
        <Metric label="后续安排" value={operatorBoard.followup.latestOutcomeStatus ?? "未设置"} />
      </div>
      <div className="mt-3 space-y-2 text-sm text-slate-700">
        <p>当前问题：{operatorBoard.deliveryDecision.question ?? "尚未形成明确判断问题。"} </p>
        {operatorBoard.deliveryDecision.options.length > 0 ? (
          <p>可能路径：{operatorBoard.deliveryDecision.options.join(" ｜ ")}</p>
        ) : null}
        {operatorBoard.deliveryDecision.blockingReasons.length > 0 ? (
          <p>阻塞原因：{operatorBoard.deliveryDecision.blockingReasons.join(" ｜ ")}</p>
        ) : null}
        {operatorBoard.deliveryDecision.advisoryNotes.length > 0 ? (
          <p>主智能体建议：{operatorBoard.deliveryDecision.advisoryNotes[0]}</p>
        ) : null}
      </div>
      <div className="mt-3 rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-3 text-xs text-slate-600">
        <div>修正状态：{operatorBoard.remediation.handoffStatus ?? "暂无"}</div>
        <div>支撑工具：{operatorBoard.remediation.handoffToolName ?? "暂无"}</div>
        <div>
          待人工确认：{operatorBoard.remediation.manualActionCount}
          {operatorBoard.remediation.manualActions[0]
            ? `（${operatorBoard.remediation.manualActions[0]}）`
            : ""}
        </div>
        <div>
          后续支撑：{operatorBoard.followup.latestToolName ?? "暂无"}
          {operatorBoard.followup.latestNotes[0]
            ? ` · ${operatorBoard.followup.latestNotes[0]}`
            : ""}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/90 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
