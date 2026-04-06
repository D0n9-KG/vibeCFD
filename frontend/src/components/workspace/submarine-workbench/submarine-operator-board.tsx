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
        交付判断与后续动作
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="交付状态" value={operatorBoard.decisionStatus ?? "待判断"} />
        <Metric label="修正动作" value={String(operatorBoard.remediation.actionCount)} />
        <Metric label="流程事件" value={String(operatorBoard.timelineEntryCount)} />
        <Metric label="后续研究" value={operatorBoard.followup.latestOutcomeStatus ?? "未设置"} />
      </div>
      <div className="mt-3 space-y-2 text-sm text-slate-700">
        <p>交付问题：{operatorBoard.deliveryDecision.question ?? "尚未形成交付问题。"} </p>
        {operatorBoard.deliveryDecision.options.length > 0 ? (
          <p>候选选项：{operatorBoard.deliveryDecision.options.join(" ｜ ")}</p>
        ) : null}
        {operatorBoard.deliveryDecision.blockingReasons.length > 0 ? (
          <p>阻塞原因：{operatorBoard.deliveryDecision.blockingReasons.join(" ｜ ")}</p>
        ) : null}
        {operatorBoard.deliveryDecision.advisoryNotes.length > 0 ? (
          <p>建议说明：{operatorBoard.deliveryDecision.advisoryNotes[0]}</p>
        ) : null}
      </div>
      <div className="mt-3 rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-3 text-xs text-slate-600">
        <div>修正交接：{operatorBoard.remediation.handoffStatus ?? "暂无"}</div>
        <div>交接工具：{operatorBoard.remediation.handoffToolName ?? "暂无"}</div>
        <div>
          人工动作：{operatorBoard.remediation.manualActionCount}
          {operatorBoard.remediation.manualActions[0]
            ? `（${operatorBoard.remediation.manualActions[0]}）`
            : ""}
        </div>
        <div>
          后续工具：{operatorBoard.followup.latestToolName ?? "暂无"}
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
