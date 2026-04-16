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
        <Metric
          label="后续安排"
          value={operatorBoard.followup.latestOutcomeStatus ?? "未设置"}
        />
      </div>

      <div className="mt-3 rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-3 text-xs text-slate-600">
        <div>
          合同状态：{operatorBoard.contract.revisionLabel ?? "待同步"} /{" "}
          {operatorBoard.contract.iterationModeLabel ?? "待同步"}
        </div>
        {operatorBoard.contract.revisionSummary ? (
          <div>修订摘要：{operatorBoard.contract.revisionSummary}</div>
        ) : null}
        <div>
          未决研究项：{operatorBoard.contract.unresolvedDecisionCount} / 能力缺口：
          {operatorBoard.contract.capabilityGapCount} / 证据期望：
          {operatorBoard.contract.evidenceExpectationCount}
        </div>
        <div>
          交付计划：已交付 {operatorBoard.contract.deliveryDeliveredCount} 项，待完成{" "}
          {operatorBoard.contract.deliveryPlannedCount} 项，受阻{" "}
          {operatorBoard.contract.deliveryBlockedCount} 项
        </div>
      </div>

      {operatorBoard.contract.capabilityGapLabels.length > 0 ? (
        <article className="mt-3 rounded-xl border border-amber-200/80 bg-amber-50/70 px-3 py-3 text-sm text-slate-700">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-700">
            能力缺口
          </div>
          <ul className="mt-2 space-y-1">
            {operatorBoard.contract.capabilityGapLabels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </article>
      ) : null}

      {operatorBoard.contract.unresolvedDecisionLabels.length > 0 ? (
        <article className="mt-3 rounded-xl border border-sky-200/80 bg-sky-50/70 px-3 py-3 text-sm text-slate-700">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-700">
            未决研究事项
          </div>
          <ul className="mt-2 space-y-1">
            {operatorBoard.contract.unresolvedDecisionLabels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </article>
      ) : null}

      {operatorBoard.contract.deliveryItems.length > 0 ? (
        <article className="mt-3 rounded-xl border border-slate-200/80 bg-white px-3 py-3 text-sm text-slate-700">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            交付计划明细
          </div>
          <ul className="mt-2 space-y-2">
            {operatorBoard.contract.deliveryItems.map((item) => (
              <li
                key={`${item.outputId ?? item.label}-${item.statusLabel}`}
                className="rounded-lg border border-slate-200/80 bg-slate-50/80 px-3 py-2"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-slate-900">{item.label}</span>
                  <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[11px] font-semibold text-slate-700">
                    {item.statusLabel}
                  </span>
                </div>
                {item.detail ? (
                  <p className="mt-1 text-xs leading-5 text-slate-600">{item.detail}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </article>
      ) : null}

      {operatorBoard.remediation.actions.length > 0 ||
      operatorBoard.remediation.manualActions.length > 0 ? (
        <article className="mt-3 rounded-xl border border-slate-200/80 bg-white px-3 py-3 text-sm text-slate-700">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            修正清单
          </div>
          {operatorBoard.remediation.actions.length > 0 ? (
            <ul className="mt-2 space-y-2">
              {operatorBoard.remediation.actions.map((action) => (
                <li
                  key={action}
                  className="rounded-lg border border-slate-200/80 bg-slate-50/80 px-3 py-2"
                >
                  {action}
                </li>
              ))}
            </ul>
          ) : null}
          {operatorBoard.remediation.manualActions.length > 0 ? (
            <>
              <div className="mt-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-700">
                待人工确认清单
              </div>
              <ul className="mt-2 space-y-2">
                {operatorBoard.remediation.manualActions.map((action) => (
                  <li
                    key={action}
                    className="rounded-lg border border-amber-200/80 bg-amber-50/70 px-3 py-2"
                  >
                    {action}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </article>
      ) : null}

      <div className="mt-3 space-y-2 text-sm text-slate-700">
        <p>
          当前问题：
          {operatorBoard.deliveryDecision.question ?? "尚未形成明确的交付判断问题。"}
        </p>
        {operatorBoard.deliveryDecision.options.length > 0 ? (
          <p>可选路径：{operatorBoard.deliveryDecision.options.join(" / ")}</p>
        ) : null}
        {operatorBoard.deliveryDecision.blockingReasons.length > 0 ? (
          <p>阻塞原因：{operatorBoard.deliveryDecision.blockingReasons.join(" / ")}</p>
        ) : null}
        {operatorBoard.deliveryDecision.advisoryNotes.length > 0 ? (
          <p>主智能体建议：{operatorBoard.deliveryDecision.advisoryNotes[0]}</p>
        ) : null}
      </div>

      <div className="mt-3 rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-3 text-xs text-slate-600">
        <div>修正状态：{operatorBoard.remediation.handoffStatus ?? "暂无"}</div>
        <div>执行工具：{operatorBoard.remediation.handoffToolName ?? "暂无"}</div>
        {operatorBoard.remediation.sourceRunId ? (
          <div>
            当前数据链：{operatorBoard.remediation.sourceRunId}
            {operatorBoard.remediation.compareTargetRunId
              ? ` -> ${operatorBoard.remediation.compareTargetRunId}`
              : ""}
          </div>
        ) : null}
        {operatorBoard.remediation.derivedRunIds[0] ? (
          <div>派生链：{operatorBoard.remediation.derivedRunIds.join(" / ")}</div>
        ) : null}
        <div>
          待人工确认：{operatorBoard.remediation.manualActionCount}
          {operatorBoard.remediation.manualActions[0]
            ? `（${operatorBoard.remediation.manualActions[0]}）`
            : ""}
        </div>
        <div>
          后续执行：{operatorBoard.followup.latestToolName ?? "暂无"}
          {operatorBoard.followup.latestNotes[0]
            ? ` / ${operatorBoard.followup.latestNotes[0]}`
            : ""}
        </div>
        {operatorBoard.followup.latestSourceRunId ? (
          <div>
            最新后续来源：{operatorBoard.followup.latestSourceRunId}
            {operatorBoard.followup.latestCompareTargetRunId
              ? ` -> ${operatorBoard.followup.latestCompareTargetRunId}`
              : ""}
          </div>
        ) : null}
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
