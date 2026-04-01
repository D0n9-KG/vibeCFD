// src/components/workspace/submarine-stage-cards.tsx
"use client";

import { useCallback, useState } from "react";

import { cn } from "@/lib/utils";

import {
  buildClarificationRequestMessage,
  buildConfirmExecutionMessage,
} from "./submarine-confirmation-actions";
import { SubmarineConvergenceChart } from "./submarine-convergence-chart";
import {
  buildSubmarineAcceptanceSummary,
  buildSubmarineExperimentCompareSummary,
  buildSubmarineExperimentSummary,
  buildSubmarineResearchEvidenceSummary,
  buildSubmarineScientificGateSummary,
  buildSubmarineScientificStudySummary,
  formatSubmarineBenchmarkComparisonSummaryLine,
} from "./submarine-runtime-panel.utils";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineSolverMetrics,
  SubmarineGeometryPayload,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";
import { type StageCardState, StageCard } from "./submarine-stage-card";
import { buildTaskIntelligenceViewModel } from "./submarine-task-intelligence-view";

// ── Shared runtime snapshot type (re-declared locally to avoid coupling) ──────
export type StageRuntimeSnapshot = {
  current_stage?: string | null;
  next_recommended_stage?: string | null;
  task_summary?: string | null;
  simulation_requirements?: SubmarineSimulationRequirements | null;
  stage_status?: string | null;
  runtime_status?: string | null;
  runtime_summary?: string | null;
  recovery_guidance?: string | null;
  blocker_detail?: string | null;
  review_status?: string | null;
  scientific_gate_status?: string | null;
  allowed_claim_level?: string | null;
  report_virtual_path?: string | null;
  execution_plan?: Array<{
    role_id?: string | null;
    owner?: string | null;
    goal?: string | null;
    status?: string | null;
  }> | null;
  activity_timeline?: Array<{
    stage?: string;
    actor?: string;
    title?: string;
    summary?: string;
    status?: string | null;
    timestamp?: string | null;
  }> | null;
};

export type StageTrendValues = number[];

const STAGE_ORDER = [
  "task-intelligence",
  "geometry-preflight",
  "solver-dispatch",
  "result-reporting",
  "supervisor-review",
] as const;

type RuntimeStage = (typeof STAGE_ORDER)[number];
type RuntimeStatus =
  | "ready"
  | "running"
  | "blocked"
  | "failed"
  | "completed";

function normalizeStage(value?: string | null): RuntimeStage | null {
  return STAGE_ORDER.includes(value as RuntimeStage)
    ? (value as RuntimeStage)
    : null;
}

function normalizeRuntimeStatus(value?: string | null): RuntimeStatus | null {
  switch (value) {
    case "ready":
    case "running":
    case "blocked":
    case "failed":
    case "completed":
      return value;
    default:
      return null;
  }
}

function resolveStageState(
  stageId: RuntimeStage,
  snapshot: StageRuntimeSnapshot | null,
): StageCardState {
  const currentStage = normalizeStage(snapshot?.current_stage);
  const nextStage = normalizeStage(snapshot?.next_recommended_stage);
  const runtimeStatus = normalizeRuntimeStatus(snapshot?.runtime_status);
  const stageIdx = STAGE_ORDER.indexOf(stageId);
  const currentIdx = currentStage ? STAGE_ORDER.indexOf(currentStage) : -1;
  const nextIdx = nextStage ? STAGE_ORDER.indexOf(nextStage) : -1;

  if (runtimeStatus === "blocked" && currentIdx >= 0) {
    if (stageIdx < currentIdx) return "done";
    if (stageIdx === currentIdx) return "blocked";
    return "pending";
  }

  if (runtimeStatus === "failed" && currentIdx >= 0) {
    if (stageIdx < currentIdx) return "done";
    if (stageIdx === currentIdx) return "failed";
    return "pending";
  }

  if (runtimeStatus === "completed") {
    if (nextIdx >= 0) {
      if (stageIdx < nextIdx) return "done";
      if (stageIdx === nextIdx) return "active";
      return "pending";
    }
    if (currentIdx >= 0) {
      return stageIdx <= currentIdx ? "done" : "pending";
    }
    return "pending";
  }

  if (currentIdx < 0) return "pending";
  if (stageIdx < currentIdx) return "done";
  if (stageIdx === currentIdx) return "active";
  return "pending";
}

function RuntimeStateNotice({
  snapshot,
  state,
}: {
  snapshot: StageRuntimeSnapshot | null;
  state: StageCardState;
}) {
  if (state !== "blocked" && state !== "failed") {
    return null;
  }

  const title = state === "blocked" ? "恢复提示" : "失败提示";
  const borderClassName =
    state === "blocked"
      ? "border-amber-200 bg-amber-50 text-amber-900"
      : "border-red-200 bg-red-50 text-red-900";
  const detailClassName =
    state === "blocked" ? "text-amber-800" : "text-red-800";
  const summary =
    snapshot?.runtime_summary ??
    (state === "blocked" ? "当前运行已阻塞。" : "当前运行已失败。");

  return (
    <div className={cn("mb-3 rounded-xl border px-3.5 py-3", borderClassName)}>
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em]">
        {title}
      </div>
      <div className="mt-1 text-[11px] leading-5">{summary}</div>
      {snapshot?.blocker_detail && (
        <div className={cn("mt-2 text-[11px] leading-5", detailClassName)}>
          {snapshot.blocker_detail}
        </div>
      )}
      {snapshot?.recovery_guidance && (
        <div className={cn("mt-2 text-[11px] leading-5", detailClassName)}>
          {snapshot.recovery_guidance}
        </div>
      )}
    </div>
  );
}

// ── TaskIntelligenceCard ──────────────────────────────────────────────────────

interface TaskIntelligenceCardProps {
  threadId: string;
  snapshot: StageRuntimeSnapshot | null;
  designBrief: SubmarineDesignBriefPayload | null;
  onConfirm: (
    threadId: string,
    message: { role: "human"; content: string },
  ) => Promise<void> | void;
}

function LegacyTaskIntelligenceCard({
  threadId,
  snapshot,
  designBrief,
  onConfirm,
}: TaskIntelligenceCardProps) {
  const state = resolveStageState("task-intelligence", snapshot);
  const [confirming, setConfirming] = useState(false);

  const handleConfirm = useCallback(() => {
    setConfirming(true);
    onConfirm(threadId, { role: "human", content: "确认方案，开始执行" });
  }, [threadId, onConfirm]);

  const handleModify = useCallback(() => {
    onConfirm(threadId, {
      role: "human",
      content: "我需要调整计算方案，请稍等",
    });
  }, [threadId, onConfirm]);

  const brief = designBrief;
  const simReq = brief?.simulation_requirements ?? snapshot?.simulation_requirements;
  const caseId = brief?.selected_case_id ?? null;
  const openQuestions = brief?.open_questions ?? [];

  const descriptionText =
    state === "done"
      ? brief?.task_description?.slice(0, 60) ?? "已确认方案"
      : state === "active"
        ? brief?.confirmation_status !== "confirmed" ||
            openQuestions.length > 0 ||
            snapshot?.review_status === "needs_user_confirmation" ||
            snapshot?.stage_status === "waiting_user"
          ? "方案待确认"
          : "正在分析任务…"
        : "等待开始";

  return (
    <StageCard
      state={state}
      index={1}
      name="任务理解"
      description={descriptionText}
      defaultExpanded={state !== "done"}
    >
      {/* Case retrieval */}
      {caseId && (
        <div className="mb-3">
          <SectionLabel color="sky">检索到相似案例</SectionLabel>
          <div className="space-y-1.5">
            <div className="flex items-start gap-2.5 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-2">
              <span className="shrink-0 rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-bold text-blue-700">
                案例
              </span>
              <div>
                <div className="text-[12px] font-semibold text-stone-800">
                  {caseId}
                </div>
                {simReq?.inlet_velocity_mps != null && (
                  <div className="mt-0.5 text-[10px] text-stone-500">
                    入口速度 {simReq.inlet_velocity_mps} m/s
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Proposed plan */}
      {simReq && (
        <div className="mb-3">
          <SectionLabel color="amber">建议计算方案</SectionLabel>
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5">
            <div className="flex flex-wrap gap-x-4 gap-y-2">
              {simReq.inlet_velocity_mps != null && (
                <PlanItem label="入口速度" value={`${simReq.inlet_velocity_mps} m/s`} />
              )}
              {simReq.fluid_density_kg_m3 != null && (
                <PlanItem label="流体密度" value={`${simReq.fluid_density_kg_m3} kg/m³`} />
              )}
              {simReq.kinematic_viscosity_m2ps != null && (
                <PlanItem
                  label="运动黏度"
                  value={`${simReq.kinematic_viscosity_m2ps.toExponential(2)} m²/s`}
                />
              )}
              {simReq.end_time_seconds != null && (
                <PlanItem label="模拟时长" value={`${simReq.end_time_seconds} s`} />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Open questions */}
      {openQuestions.length > 0 && (
        <div className="mb-3">
          <SectionLabel color="red">待确认问题</SectionLabel>
          <ul className="space-y-1">
            {openQuestions.map((q, i) => (
              <li key={i} className="flex gap-1.5 text-[11px] text-stone-600">
                <span className="shrink-0 text-amber-500">⚠</span>
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!caseId && !simReq && openQuestions.length === 0 && (
        <StageHintList
          title="这一步会先形成可确认的研究 brief"
          items={[
            "抽取研究目标、关键工况、对比对象和交付要求",
            "整理 baseline 与后续 scientific study 的切入点",
            "如果信息不足，会在聊天区追问缺失条件而不是硬编码推进",
          ]}
        />
      )}

      {/* Confirm actions — only when active and waiting for user */}
      {state === "active" && (
        <div className="mt-2 flex gap-2">
          <button
            type="button"
            disabled={confirming}
            className="rounded-md bg-green-500 px-4 py-1.5 text-[12px] font-semibold text-white hover:bg-green-600 disabled:opacity-60"
            onClick={handleConfirm}
          >
            {confirming ? "发送中…" : "✓ 确认方案，开始执行"}
          </button>
          <button
            type="button"
            className="rounded-md border border-stone-200 bg-white px-4 py-1.5 text-[12px] text-stone-700 hover:bg-stone-50"
            onClick={handleModify}
          >
            调整参数…
          </button>
        </div>
      )}
    </StageCard>
  );
}

// ── GeometryPreflightCard ─────────────────────────────────────────────────────

void LegacyTaskIntelligenceCard;

export function TaskIntelligenceCard({
  threadId,
  snapshot,
  designBrief,
  onConfirm,
}: TaskIntelligenceCardProps) {
  const state = resolveStageState("task-intelligence", snapshot);
  const [confirming, setConfirming] = useState(false);

  const handleConfirm = useCallback(() => {
    setConfirming(true);
    onConfirm(threadId, {
      role: "human",
      content: buildConfirmExecutionMessage(designBrief),
    });
  }, [designBrief, threadId, onConfirm]);

  const handleModify = useCallback(() => {
    onConfirm(threadId, {
      role: "human",
      content: buildClarificationRequestMessage(designBrief),
    });
  }, [designBrief, threadId, onConfirm]);

  const brief = designBrief;
  const simReq = brief?.simulation_requirements ?? snapshot?.simulation_requirements;
  const caseId = brief?.selected_case_id ?? null;
  const viewModel = buildTaskIntelligenceViewModel({
    designBrief,
    snapshot,
  });

  const descriptionText =
    state === "blocked"
      ? snapshot?.runtime_summary ?? "任务理解暂时受阻"
      : state === "failed"
        ? snapshot?.runtime_summary ?? "任务理解失败"
        : state === "done"
      ? brief?.task_description?.slice(0, 60) ?? "方案已确认"
      : state === "active"
        ? viewModel.confirmationState === "needs_clarification"
          ? "仍有关键工况待确认"
          : viewModel.confirmationState === "ready_to_confirm"
            ? "详细方案已生成，等待用户确认"
            : viewModel.confirmationState === "confirmed"
              ? "方案已确认，等待进入预检或执行"
              : "正在分析任务..."
        : "等待开始";

  return (
    <StageCard
      state={state}
      index={1}
      name="任务理解"
      description={descriptionText}
      defaultExpanded={state !== "done"}
    >
      <RuntimeStateNotice snapshot={snapshot} state={state} />
      {caseId && (
        <div className="mb-4">
          <SectionLabel color="sky">匹配案例</SectionLabel>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">
                baseline
              </span>
              <div className="text-[12px] font-semibold text-stone-800">
                {caseId}
              </div>
            </div>
            {simReq?.inlet_velocity_mps != null && (
              <div className="mt-1 text-[11px] text-stone-500">
                入口速度 {simReq.inlet_velocity_mps} m/s
              </div>
            )}
          </div>
        </div>
      )}

      {viewModel.confirmationState !== "idle" && (
        <div
          className={cn(
            "mb-4 rounded-xl border px-3.5 py-3 text-[11px] leading-5 shadow-sm",
            viewModel.confirmationState === "confirmed"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : viewModel.confirmationState === "needs_clarification"
                ? "border-amber-200 bg-amber-50 text-amber-900"
                : "border-sky-200 bg-sky-50 text-sky-900",
          )}
        >
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em]">
            {viewModel.confirmationState === "confirmed"
              ? "Plan Locked"
              : viewModel.confirmationState === "needs_clarification"
                ? "Needs Clarification"
                : "Awaiting Confirmation"}
          </div>
          <div className="mt-1">
            {viewModel.confirmationState === "confirmed"
              ? "当前计算方案已经确认，后续预检与求解应严格沿用这一版 brief 中的工况、输出和验证要求。"
              : viewModel.confirmationState === "needs_clarification"
                ? "当前 brief 仍有待确认条件，主智能体应先和用户协商补齐，再进入执行。"
                : "当前已经形成可审阅的计算方案，请先确认方案，再启动后续预检与求解。"}
          </div>
        </div>
      )}

      {viewModel.planItems.length > 0 && (
        <div className="mb-4">
          <SectionLabel color="amber">计算方案</SectionLabel>
          <div className="grid gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-3 sm:grid-cols-2 xl:grid-cols-3">
            {viewModel.planItems.map((item) => (
              <PlanItem key={item.label} label={item.label} value={item.value} />
            ))}
          </div>
        </div>
      )}

      {viewModel.requestedOutputs.length > 0 && (
        <div className="mb-4">
          <SectionLabel color="sky">预期输出</SectionLabel>
          <div className="space-y-2">
            {viewModel.requestedOutputs.map((output) => (
              <div
                key={output.outputId}
                className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <div className="text-[12px] font-semibold text-stone-800">
                    {output.label}
                  </div>
                  <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-stone-600">
                    {output.supportLevel}
                  </span>
                </div>
                <div className="mt-1 text-[11px] text-stone-600">
                  用户请求: {output.requestedLabel}
                </div>
                {output.selectorSummary && (
                  <div className="mt-1 text-[10px] font-mono text-stone-500">
                    selector={output.selectorSummary}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {viewModel.verificationRequirements.length > 0 && (
        <div className="mb-4">
          <SectionLabel color="sky">科研验证要求</SectionLabel>
          <div className="space-y-2">
            {viewModel.verificationRequirements.map((requirement) => (
              <div
                key={requirement.requirementId}
                className="rounded-xl border border-slate-200 bg-white px-3.5 py-3"
              >
                <div className="text-[12px] font-semibold text-stone-800">
                  {requirement.label}
                </div>
                <div className="mt-1 font-mono text-[10px] text-stone-500">
                  {requirement.checkType}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {viewModel.userConstraints.length > 0 && (
        <div className="mb-4">
          <SectionLabel color="sky">用户约束</SectionLabel>
          <div className="rounded-xl border border-stone-200 bg-white px-3.5 py-3">
            <ul className="space-y-1.5">
              {viewModel.userConstraints.map((constraint) => (
                <li
                  key={constraint}
                  className="flex gap-1.5 text-[11px] text-stone-600"
                >
                  <span className="shrink-0 text-sky-500">•</span>
                  {constraint}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {viewModel.openQuestions.length > 0 && (
        <div className="mb-4">
          <SectionLabel color="red">待确认问题</SectionLabel>
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-3">
            <ul className="space-y-1.5">
              {viewModel.openQuestions.map((question) => (
                <li
                  key={question}
                  className="flex gap-1.5 text-[11px] text-stone-700"
                >
                  <span className="shrink-0 text-amber-500">?</span>
                  {question}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {viewModel.executionSteps.length > 0 && (
        <div className="mb-4">
          <SectionLabel color="sky">执行分工</SectionLabel>
          <div className="space-y-2">
            {viewModel.executionSteps.map((step) => (
              <div
                key={step.roleId}
                className="rounded-xl border border-stone-200 bg-white px-3.5 py-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <div className="text-[12px] font-semibold text-stone-800">
                    {step.owner}
                  </div>
                  <span className="rounded-full bg-stone-100 px-2 py-0.5 text-[10px] font-medium text-stone-600">
                    {step.status}
                  </span>
                </div>
                <div className="mt-1 text-[10px] font-mono text-stone-500">
                  {step.roleId}
                </div>
                <div className="mt-1 text-[11px] text-stone-600">{step.goal}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!caseId &&
        !simReq &&
        viewModel.openQuestions.length === 0 &&
        viewModel.requestedOutputs.length === 0 && (
          <StageHintList
            title="这一步会先形成可确认的研究 brief"
            items={[
              "抽取研究目标、关键工况、对比对象和交付要求",
              "整理 baseline 与后续 scientific study 的切入点",
              "如果信息不足，会在聊天区继续协商缺失条件，而不是硬编码推进",
            ]}
          />
        )}

      {state === "active" && (
        <div className="mt-3 flex flex-wrap gap-2">
          {viewModel.canConfirmExecution && (
            <button
              type="button"
              disabled={confirming}
              className="rounded-xl bg-emerald-600 px-4 py-2 text-[12px] font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:opacity-60"
              onClick={handleConfirm}
            >
              {confirming ? "发送中..." : "确认方案，开始执行"}
            </button>
          )}
          <button
            type="button"
            className="rounded-xl border border-stone-200 bg-white px-4 py-2 text-[12px] text-stone-700 transition hover:bg-stone-50"
            onClick={handleModify}
          >
            {viewModel.openQuestions.length > 0 ? "补充待确认条件" : "调整参数"}
          </button>
        </div>
      )}
    </StageCard>
  );
}

interface GeometryPreflightCardProps {
  snapshot: StageRuntimeSnapshot | null;
  geometry: SubmarineGeometryPayload | null;
}

export function GeometryPreflightCard({
  snapshot,
  geometry,
}: GeometryPreflightCardProps) {
  const state = resolveStageState("geometry-preflight", snapshot);

  // SubmarineGeometryPayload has: summary_zh, candidate_cases (no geometry_family_hint)
  const description =
    state === "done"
      ? geometry?.summary_zh?.slice(0, 60) ?? "几何预检通过"
      : state === "active"
        ? "正在检查几何…"
        : "等待任务理解完成";

  const resolvedDescription =
    state === "blocked"
      ? snapshot?.runtime_summary ?? "鍑犱綍棰勬鍙楅樆"
      : state === "failed"
        ? snapshot?.runtime_summary ?? "鍑犱綍棰勬澶辫触"
        : description;

  return (
    <StageCard
      state={state}
      index={2}
      name="几何预检"
      description={resolvedDescription}
      defaultExpanded={state !== "done"}
    >
      <RuntimeStateNotice snapshot={snapshot} state={state} />
      {geometry?.summary_zh && (
        <div className="text-[11px] text-stone-600">{geometry.summary_zh}</div>
      )}
      {!geometry && state === "active" && (
        <div className="text-[11px] text-stone-400">几何检查运行中…</div>
      )}
      {!geometry && state !== "done" && (
        <StageHintList
          title="预检会收敛几何与网格可用性"
          items={[
            "检查几何来源是否完整、是否需要转换或清理",
            "确认边界命名、候选案例与求解设定是否匹配",
            "为后续 solver dispatch 提供可追溯的几何依据",
          ]}
        />
      )}
    </StageCard>
  );
}

// ── SolverDispatchCard ────────────────────────────────────────────────────────

interface SolverDispatchCardProps {
  snapshot: StageRuntimeSnapshot | null;
  solverMetrics: SubmarineSolverMetrics | null;
  trendValues: StageTrendValues;
}

export function SolverDispatchCard({
  snapshot,
  solverMetrics,
  trendValues,
}: SolverDispatchCardProps) {
  const state = resolveStageState("solver-dispatch", snapshot);

  // Compute progress from execution_plan
  const plan = snapshot?.execution_plan ?? [];
  const totalSteps = plan.length;
  const completedSteps = plan.filter((s) => s.status === "completed").length;
  const progressPct = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  // Latest log line from activity_timeline
  const lastEvent = snapshot?.activity_timeline?.at(-1);

  // Metrics — SubmarineSolverMetrics exposes latest_force_coefficients.Cd
  const cd = solverMetrics?.latest_force_coefficients?.Cd ?? null;
  const fx = solverMetrics?.latest_force_coefficients?.Fx ?? null;
  const runtimeStateDescription =
    state === "blocked"
      ? snapshot?.runtime_summary ?? "Solver dispatch blocked"
      : state === "failed"
        ? snapshot?.runtime_summary ?? "Solver dispatch failed"
        : null;

  const description =
    state === "done"
      ? cd != null ? `Cd=${cd.toFixed(5)} · 求解完成` : "求解完成"
      : state === "active"
        ? "simpleFoam 运行中"
        : "等待几何预检完成";

  return (
    <StageCard
      state={state}
      index={3}
      name="求解执行"
      description={runtimeStateDescription ?? description}
      rightLabel={
        state === "active" ? (
          <span className="text-[11px] font-medium text-blue-500">运行中</span>
        ) : undefined
      }
      defaultExpanded={state !== "done"}
    >
      <RuntimeStateNotice snapshot={snapshot} state={state} />
      {/* Progress */}
      {totalSteps > 0 && (
        <div className="mb-2.5 flex items-center gap-2.5">
          <div className="h-1 flex-1 overflow-hidden rounded-full bg-stone-200">
            <div
              className="h-1 rounded-full bg-blue-500 transition-all"
              style={{ width: `${progressPct.toFixed(0)}%` }}
            />
          </div>
          <span className="text-[11px] font-semibold text-blue-500">
            {completedSteps}/{totalSteps}
          </span>
        </div>
      )}

      {/* Metric chips */}
      <div className="mb-2.5 flex gap-2">
        <MetricChip label="Cd" value={cd != null ? cd.toFixed(5) : "--"} color="green" />
        <MetricChip
          label="Fx"
          value={fx != null ? `${fx.toFixed(2)} N` : "--"}
          color="blue"
        />
      </div>

      {/* Convergence chart */}
      {trendValues.length >= 2 && (
        <div className="mb-2 overflow-hidden rounded-md border border-slate-200 bg-slate-50 p-2">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
            Cd 收敛历史
          </div>
          <SubmarineConvergenceChart values={trendValues} height={48} />
        </div>
      )}

      {/* Latest log */}
      {lastEvent && (
        <div className="rounded bg-stone-100 px-2 py-1 font-mono text-[10px] text-stone-500">
          <span className="text-green-500">▶</span>{" "}
          {lastEvent.actor ? `[${lastEvent.actor}] ` : ""}
          {lastEvent.title ?? lastEvent.summary ?? "…"}
        </div>
      )}
      {!solverMetrics && totalSteps === 0 && trendValues.length < 2 && (
        <StageHintList
          title="求解阶段会保留完整的 dispatch 与数值证据"
          items={[
            "生成可审计的执行计划，而不是直接跳到硬编码求解",
            "记录 solver 产物、关键系数和收敛历史",
            "为后续比较研究、报告和 scientific followup 提供基础数据",
          ]}
        />
      )}
    </StageCard>
  );
}

// ── ResultReportingCard ───────────────────────────────────────────────────────

interface ResultReportingCardProps {
  snapshot: StageRuntimeSnapshot | null;
  finalReport: SubmarineFinalReportPayload | null;
  solverMetrics: SubmarineSolverMetrics | null;
  reportVirtualPath?: string | null;
}

export function ResultReportingCard({
  snapshot,
  finalReport,
  solverMetrics,
  reportVirtualPath,
}: ResultReportingCardProps) {
  const state = resolveStageState("result-reporting", snapshot);

  // Cd from solver metrics (latest_force_coefficients["Cd"]) or final report solver_metrics
  const reportSolverMetrics = finalReport?.solver_metrics ?? solverMetrics;
  const cd = reportSolverMetrics?.latest_force_coefficients?.Cd ?? null;
  const runtimeStateDescription =
    state === "blocked"
      ? snapshot?.runtime_summary ?? "Result reporting blocked"
      : state === "failed"
        ? snapshot?.runtime_summary ?? "Result reporting failed"
        : null;
  const description =
    state === "done"
      ? cd != null ? `Cd = ${cd.toFixed(5)}` : "报告已生成"
      : state === "active"
        ? "结果整理中…"
        : "等待求解完成";
  const experimentSummary = buildSubmarineExperimentSummary(finalReport);
  const experimentCompareSummary =
    buildSubmarineExperimentCompareSummary(finalReport);
  const scientificStudySummary =
    buildSubmarineScientificStudySummary(finalReport);
  const acceptanceSummary = buildSubmarineAcceptanceSummary(finalReport);
  const researchEvidenceSummary =
    buildSubmarineResearchEvidenceSummary(finalReport);
  const scientificGateSummary = buildSubmarineScientificGateSummary(
    finalReport?.scientific_supervisor_gate
      ? finalReport
      : snapshot?.scientific_gate_status || snapshot?.allowed_claim_level
        ? {
            scientific_supervisor_gate: {
              gate_status: snapshot?.scientific_gate_status,
              allowed_claim_level: snapshot?.allowed_claim_level,
              source_readiness_status: snapshot?.allowed_claim_level,
              recommended_stage: snapshot?.next_recommended_stage,
            },
          }
        : null,
  );

  return (
    <StageCard
      state={state}
      index={4}
      name="结果整理"
      description={runtimeStateDescription ?? description}
      defaultExpanded={state !== "done"}
    >
      <RuntimeStateNotice snapshot={snapshot} state={state} />
      {/* Big Cd display */}
      {cd != null && (
        <div className="mb-3">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-stone-400">
            阻力系数 Cd
          </div>
          <div className="font-mono text-4xl font-extrabold text-stone-900">
            {cd.toFixed(5)}
          </div>
        </div>
      )}

      {/* Report summary */}
      {finalReport && (
        <div className="mb-2 text-[12px] text-stone-600">
          {finalReport.summary_zh ?? ""}
        </div>
      )}

      {(scientificGateSummary ||
        researchEvidenceSummary ||
        (acceptanceSummary?.benchmarkComparisons.length ?? 0) > 0) && (
        <div className="mt-4 space-y-3">
          <SectionLabel color="amber">Scientific Claim Gate</SectionLabel>
          <div className="grid gap-3 xl:grid-cols-3">
            {scientificGateSummary && (
              <WorkflowSummaryCard
                title="Scientific Claim Gate"
                badge={scientificGateSummary.gateStatusLabel}
                stats={[
                  {
                    label: "Claim Level",
                    value: scientificGateSummary.allowedClaimLevelLabel,
                  },
                  {
                    label: "Next Stage",
                    value: scientificGateSummary.recommendedStageLabel,
                  },
                  {
                    label: "Remediation",
                    value: scientificGateSummary.remediationStageLabel,
                  },
                ]}
                sections={[
                  {
                    title: "Decision Basis",
                    items: compactTextItems([
                      `readiness | ${scientificGateSummary.sourceReadinessLabel}`,
                    ]),
                    emptyText: "No scientific claim basis is recorded yet.",
                  },
                  {
                    title: "Blocking Reasons",
                    items: compactTextItems(scientificGateSummary.blockingReasons),
                    emptyText: "No claim blockers are recorded.",
                  },
                  {
                    title: "Advisory Notes",
                    items: compactTextItems(scientificGateSummary.advisoryNotes),
                    emptyText: "No claim advisory notes are recorded.",
                  },
                ]}
              />
            )}

            {researchEvidenceSummary && (
              <WorkflowSummaryCard
                title="Research Evidence"
                badge={researchEvidenceSummary.readinessLabel}
                stats={[
                  {
                    label: "Validation",
                    value: researchEvidenceSummary.validationStatusLabel,
                  },
                  {
                    label: "Verification",
                    value: researchEvidenceSummary.verificationStatusLabel,
                  },
                  {
                    label: "Confidence",
                    value: researchEvidenceSummary.confidenceLabel,
                  },
                ]}
                sections={[
                  {
                    title: "Benchmark Highlights",
                    items: compactTextItems(
                      researchEvidenceSummary.benchmarkHighlights,
                    ),
                    emptyText: "No benchmark highlights are recorded yet.",
                  },
                  {
                    title: "Blocking Issues",
                    items: compactTextItems(
                      researchEvidenceSummary.blockingIssues,
                    ),
                    emptyText: "No research evidence blockers are recorded.",
                  },
                  {
                    title: "Evidence Gaps",
                    items: compactTextItems(researchEvidenceSummary.evidenceGaps),
                    emptyText: "No research evidence gaps are recorded.",
                  },
                ]}
              />
            )}

            {acceptanceSummary &&
              acceptanceSummary.benchmarkComparisons.length > 0 && (
                <WorkflowSummaryCard
                  title="Benchmark Comparisons"
                  badge={`${acceptanceSummary.benchmarkComparisons.length} recorded`}
                  stats={[
                    {
                      label: "Acceptance",
                      value: acceptanceSummary.statusLabel,
                    },
                    {
                      label: "Confidence",
                      value: acceptanceSummary.confidenceLabel,
                    },
                    {
                      label: "Warnings",
                      value: `${acceptanceSummary.warnings.length}`,
                    },
                  ]}
                  sections={[
                    {
                      title: "Reference Checks",
                      items: compactTextItems(
                        acceptanceSummary.benchmarkComparisons.map((item) =>
                          formatSubmarineBenchmarkComparisonSummaryLine(item),
                        ),
                      ),
                      emptyText: "No benchmark comparisons are recorded yet.",
                    },
                    {
                      title: "Detailed Findings",
                      items: compactTextItems(
                        acceptanceSummary.benchmarkComparisons.map(
                          (item) => item.detail,
                        ),
                      ),
                      emptyText: "No benchmark detail is recorded yet.",
                    },
                    {
                      title: "Reference Sources",
                      items: compactTextItems(
                        acceptanceSummary.benchmarkComparisons.flatMap((item) =>
                          [item.sourceLabel, item.sourceUrl].filter(Boolean),
                        ),
                      ),
                      emptyText: "No benchmark source metadata is recorded.",
                    },
                  ]}
                />
              )}
          </div>
        </div>
      )}

      {(experimentSummary || experimentCompareSummary || scientificStudySummary) && (
        <div className="mt-4 space-y-3">
          <SectionLabel color="sky">Verification Workflow</SectionLabel>
          <div className="grid gap-3 xl:grid-cols-3">
            {experimentSummary && (
              <WorkflowSummaryCard
                title="Experiment Registry"
                badge={experimentSummary.workflowStatusLabel}
                stats={[
                  {
                    label: "Registry",
                    value: experimentSummary.experimentStatusLabel,
                  },
                  {
                    label: "Runs",
                    value: `${experimentSummary.runCount}`,
                  },
                  {
                    label: "Compares",
                    value: `${experimentSummary.compareCount}`,
                  },
                ]}
                sections={[
                  {
                    title: "Workflow Detail",
                    items: compactTextItems([
                      experimentSummary.workflowDetail,
                      ...experimentSummary.runStatusCountLines,
                      ...experimentSummary.compareStatusCountLines,
                    ]),
                    emptyText: "No experiment workflow detail is recorded yet.",
                  },
                  {
                    title: "Linkage Coverage",
                    items: compactTextItems([
                      `status | ${experimentSummary.linkageStatus}`,
                      `issues | ${experimentSummary.linkageIssueCount}`,
                      ...experimentSummary.linkageIssues,
                      ...experimentSummary.missingVariantRunRecordIds.map(
                        (item) => `missing run-record | ${item}`,
                      ),
                      ...experimentSummary.missingCompareEntryIds.map(
                        (item) => `missing compare-entry | ${item}`,
                      ),
                    ]),
                    emptyText: "No experiment linkage issues are recorded.",
                  },
                  {
                    title: "Outstanding Gaps",
                    items: compactTextItems([
                      ...experimentSummary.plannedVariantRunIds.map(
                        (item) => `planned | ${item}`,
                      ),
                      ...experimentSummary.blockedVariantRunIds.map(
                        (item) => `blocked | ${item}`,
                      ),
                      ...experimentSummary.missingMetricsVariantRunIds.map(
                        (item) => `missing metrics | ${item}`,
                      ),
                      ...experimentSummary.compareNotes,
                    ]),
                    emptyText: "No outstanding experiment workflow gaps are recorded.",
                  },
                ]}
              />
            )}

            {experimentCompareSummary && (
              <WorkflowSummaryCard
                title="Experiment Compare"
                badge={experimentCompareSummary.workflowStatusLabel}
                stats={[
                  {
                    label: "Baseline",
                    value: experimentCompareSummary.baselineRunId,
                  },
                  {
                    label: "Compare Count",
                    value: `${experimentCompareSummary.compareCount}`,
                  },
                  {
                    label: "Artifact",
                    value: experimentCompareSummary.comparePath,
                  },
                ]}
                sections={[
                  {
                    title: "Workflow Coverage",
                    items: compactTextItems([
                      ...experimentCompareSummary.compareStatusCountLines,
                      ...experimentCompareSummary.plannedCandidateRunIds.map(
                        (item) => `planned | ${item}`,
                      ),
                      ...experimentCompareSummary.completedCandidateRunIds.map(
                        (item) => `completed | ${item}`,
                      ),
                      ...experimentCompareSummary.blockedCandidateRunIds.map(
                        (item) => `blocked | ${item}`,
                      ),
                      ...experimentCompareSummary.missingMetricsCandidateRunIds.map(
                        (item) => `missing metrics | ${item}`,
                      ),
                    ]),
                    emptyText: "No experiment compare workflow detail is recorded yet.",
                  },
                  {
                    title: "Compared Runs",
                    items: compactTextItems(
                      experimentCompareSummary.comparisons.map(
                        (item) =>
                          `${experimentCompareSummary.baselineRunId} -> ${item.candidateRunId} | ${item.compareStatusLabel} | ${item.candidateExecutionStatusLabel}`,
                      ),
                    ),
                    emptyText: "No experiment comparisons are recorded yet.",
                  },
                  {
                    title: "Comparison Notes",
                    items: compactTextItems(
                      experimentCompareSummary.comparisons.flatMap((item) => [
                        item.notes,
                        ...item.metricDeltaLines,
                      ]),
                    ),
                    emptyText: "No comparison notes are recorded.",
                  },
                ]}
              />
            )}

            {scientificStudySummary && (
              <WorkflowSummaryCard
                title="Scientific Studies"
                badge={scientificStudySummary.workflowStatusLabel}
                stats={[
                  {
                    label: "Execution",
                    value: scientificStudySummary.executionStatusLabel,
                  },
                  {
                    label: "Study Count",
                    value: `${scientificStudySummary.studies.length}`,
                  },
                  {
                    label: "Manifest",
                    value: scientificStudySummary.manifestPath,
                  },
                ]}
                sections={[
                  {
                    title: "Workflow Overview",
                    items: compactTextItems([
                      ...scientificStudySummary.studyStatusCountLines,
                      ...scientificStudySummary.studies.map(
                        (item) =>
                          `${item.summaryLabel} | ${item.workflowStatusLabel} | ${item.studyExecutionStatusLabel} | ${item.verificationStatus}`,
                      ),
                    ]),
                    emptyText: "No scientific study workflow detail is available yet.",
                  },
                  {
                    title: "Follow-Up Runs",
                    items: compactTextItems(
                      scientificStudySummary.studies.flatMap((item) => [
                        item.workflowDetail,
                        ...item.expectedVariantRunIds.map(
                          (runId) => `expected | ${runId}`,
                        ),
                        ...item.plannedVariantRunIds.map(
                          (runId) => `planned | ${runId}`,
                        ),
                        ...item.inProgressVariantRunIds.map(
                          (runId) => `running | ${runId}`,
                        ),
                        ...item.blockedVariantRunIds.map(
                          (runId) => `blocked | ${runId}`,
                        ),
                      ]),
                    ),
                    emptyText: "No outstanding study runs are recorded.",
                  },
                  {
                    title: "Compare Coverage",
                    items: compactTextItems(
                      scientificStudySummary.studies.flatMap((item) => [
                        item.verificationDetail,
                        ...item.completedVariantRunIds.map(
                          (runId) => `completed | ${runId}`,
                        ),
                        ...item.plannedCompareVariantRunIds.map(
                          (runId) => `compare planned | ${runId}`,
                        ),
                        ...item.completedCompareVariantRunIds.map(
                          (runId) => `compare completed | ${runId}`,
                        ),
                        ...item.blockedCompareVariantRunIds.map(
                          (runId) => `compare blocked | ${runId}`,
                        ),
                        ...item.missingMetricsVariantRunIds.map(
                          (runId) => `metrics missing | ${runId}`,
                        ),
                      ]),
                    ),
                    emptyText: "No completed or compare-coverage detail is recorded.",
                  },
                ]}
              />
            )}
          </div>
        </div>
      )}

      {/* Download report */}
      {reportVirtualPath && (
        <div className="mt-2">
          <span className="inline-block rounded-md border border-stone-200 bg-white px-3 py-1.5 text-[11px] font-medium text-stone-700 hover:bg-stone-50 cursor-pointer">
            ⬇ 下载报告
          </span>
        </div>
      )}

      {state === "active" && !cd && (
        <div className="text-[11px] text-stone-400">正在整理计算结果…</div>
      )}
      {!finalReport && cd == null && (
        <StageHintList
          title="报告阶段会把数值结果转成科研交付物"
          items={[
            "汇总关键系数、验证结论与 claim level",
            "沉淀对比、图表、报告路径和 followup 入口",
            "确保结果不是只有终值，而是带证据链的可复查结论",
          ]}
        />
      )}
    </StageCard>
  );
}

// ── SupervisorReviewCard ──────────────────────────────────────────────────────

const REVIEW_STATUS_LABELS: Record<string, string> = {
  ready_for_supervisor: "待复核",
  needs_user_confirmation: "待用户确认",
  blocked: "已阻塞",
};

const REVIEW_STATUS_COLORS: Record<string, string> = {
  ready_for_supervisor: "bg-amber-100 text-amber-700",
  needs_user_confirmation: "bg-blue-100 text-blue-700",
  blocked: "bg-red-100 text-red-700",
};

interface SupervisorReviewCardProps {
  threadId: string;
  snapshot: StageRuntimeSnapshot | null;
  finalReport?: SubmarineFinalReportPayload | null;
  onConfirm: (
    threadId: string,
    message: { role: "human"; content: string },
  ) => Promise<void> | void;
}

export function SupervisorReviewCard({
  threadId,
  snapshot,
  finalReport,
  onConfirm,
}: SupervisorReviewCardProps) {
  const state = resolveStageState("supervisor-review", snapshot);
  const reviewStatus = snapshot?.review_status ?? null;
  const gateStatus = snapshot?.scientific_gate_status ?? null;
  const needsUserConfirmation = reviewStatus === "needs_user_confirmation";
  const scientificGateSummary = buildSubmarineScientificGateSummary(
    finalReport?.scientific_supervisor_gate
      ? finalReport
      : snapshot?.scientific_gate_status || snapshot?.allowed_claim_level
        ? {
            scientific_supervisor_gate: {
              gate_status: snapshot?.scientific_gate_status,
              allowed_claim_level: snapshot?.allowed_claim_level,
              source_readiness_status: snapshot?.allowed_claim_level,
              recommended_stage: snapshot?.next_recommended_stage,
            },
          }
        : null,
  );
  const researchEvidenceSummary = buildSubmarineResearchEvidenceSummary(finalReport);

  const description =
    state === "done"
      ? "复核已完成"
      : state === "active"
        ? reviewStatus
          ? REVIEW_STATUS_LABELS[reviewStatus] ?? reviewStatus
          : "复核中…"
        : "等待结果整理";

  const runtimeStateDescription =
    state === "blocked"
      ? snapshot?.runtime_summary ?? "Supervisor review blocked"
      : state === "failed"
        ? snapshot?.runtime_summary ?? "Supervisor review failed"
        : null;

  const handleAccept = useCallback(() => {
    onConfirm(threadId, {
      role: "human",
      content: "确认通过，批准当前结果",
    });
  }, [threadId, onConfirm]);

  const handleReject = useCallback(() => {
    onConfirm(threadId, {
      role: "human",
      content: "需要重新计算，请说明修改意见",
    });
  }, [threadId, onConfirm]);

  return (
    <StageCard
      state={state}
      index={5}
      name="Supervisor 复核"
      description={runtimeStateDescription ?? description}
      defaultExpanded={state !== "done"}
    >
      <RuntimeStateNotice snapshot={snapshot} state={state} />
      {/* Review status badge */}
      {reviewStatus && (
        <div className="mb-2">
          <span
            className={cn(
              "inline-block rounded-full px-2.5 py-0.5 text-[11px] font-semibold",
              REVIEW_STATUS_COLORS[reviewStatus] ?? "bg-stone-100 text-stone-600",
            )}
          >
            {REVIEW_STATUS_LABELS[reviewStatus] ?? reviewStatus}
          </span>
        </div>
      )}

      {/* Scientific gate */}
      {gateStatus && (
        <div className="mb-2 text-[11px] text-stone-500">
          科学门控：{gateStatus}
        </div>
      )}

      {scientificGateSummary && (
        <div className="mt-4 grid gap-3 xl:grid-cols-3">
          <WorkflowSummaryCard
            title="Supervisor Claim Gate"
            badge={scientificGateSummary.gateStatusLabel}
            stats={[
              {
                label: "Claim Level",
                value: scientificGateSummary.allowedClaimLevelLabel,
              },
              {
                label: "Recommended",
                value: scientificGateSummary.recommendedStageLabel,
              },
              {
                label: "Remediation",
                value: scientificGateSummary.remediationStageLabel,
              },
            ]}
            sections={[
              {
                title: "Blocking Reasons",
                items: compactTextItems(scientificGateSummary.blockingReasons),
                emptyText: "No supervisor claim blockers are recorded.",
              },
              {
                title: "Advisory Notes",
                items: compactTextItems(scientificGateSummary.advisoryNotes),
                emptyText: "No supervisor advisory notes are recorded.",
              },
              {
                title: "Claim Basis",
                items: compactTextItems([
                  `readiness | ${scientificGateSummary.sourceReadinessLabel}`,
                ]),
                emptyText: "No claim basis is recorded yet.",
              },
            ]}
          />

          {researchEvidenceSummary && (
            <WorkflowSummaryCard
              title="Research Evidence Snapshot"
              badge={researchEvidenceSummary.validationStatusLabel}
              stats={[
                {
                  label: "Readiness",
                  value: researchEvidenceSummary.readinessLabel,
                },
                {
                  label: "Verification",
                  value: researchEvidenceSummary.verificationStatusLabel,
                },
                {
                  label: "Provenance",
                  value: researchEvidenceSummary.provenanceStatusLabel,
                },
              ]}
              sections={[
                {
                  title: "Blocking Issues",
                  items: compactTextItems(researchEvidenceSummary.blockingIssues),
                  emptyText: "No research evidence blockers are recorded.",
                },
                {
                  title: "Evidence Gaps",
                  items: compactTextItems(researchEvidenceSummary.evidenceGaps),
                  emptyText: "No research evidence gaps are recorded.",
                },
                {
                  title: "Benchmark Highlights",
                  items: compactTextItems(
                    researchEvidenceSummary.benchmarkHighlights,
                  ),
                  emptyText: "No benchmark highlights are recorded.",
                },
              ]}
            />
          )}
        </div>
      )}

      {/* User confirmation buttons */}
      {needsUserConfirmation && (
        <div className="mt-2 flex gap-2">
          <button
            type="button"
            className="rounded-md bg-green-500 px-4 py-1.5 text-[12px] font-semibold text-white hover:bg-green-600"
            onClick={handleAccept}
          >
            ✓ 确认通过
          </button>
          <button
            type="button"
            className="rounded-md border border-stone-200 bg-white px-4 py-1.5 text-[12px] text-stone-700 hover:bg-stone-50"
            onClick={handleReject}
          >
            需要重算
          </button>
        </div>
      )}

      {state === "active" && !reviewStatus && (
        <div className="text-[11px] text-stone-400">Supervisor 正在复核…</div>
      )}
      {!reviewStatus && !gateStatus && (
        <StageHintList
          title="复核阶段负责收口科研闭环"
          items={[
            "检查 claim level、验证状态与证据缺口",
            "决定是否接受当前结果、要求重算或触发 followup",
            "把用户确认与 scientific gate 串成完整交付闭环",
          ]}
        />
      )}
    </StageCard>
  );
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function SectionLabel({
  color,
  children,
}: {
  color: "sky" | "amber" | "red";
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "mb-1.5 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.5px]",
        color === "sky" && "text-stone-500",
        color === "amber" && "text-amber-800",
        color === "red" && "text-red-600",
      )}
    >
      <span
        className={cn(
          "inline-block h-3 w-[3px] shrink-0 rounded-sm",
          color === "sky" && "bg-stone-400",
          color === "amber" && "bg-amber-500",
          color === "red" && "bg-red-500",
        )}
      />
      {children}
    </div>
  );
}

function StageHintList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <div className="mt-auto rounded-xl border border-dashed border-stone-200 bg-stone-50/80 p-3">
      <div className="text-[11px] font-semibold text-stone-700">{title}</div>
      <ul className="mt-2 space-y-1.5">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-[11px] leading-5 text-stone-500">
            <span className="mt-[5px] inline-block size-1.5 shrink-0 rounded-full bg-sky-500" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function compactTextItems(items: Array<string | null | undefined>): string[] {
  const deduped: string[] = [];
  for (const item of items) {
    const value = item?.trim();
    if (!value || value === "--" || deduped.includes(value)) {
      continue;
    }
    deduped.push(value);
  }
  return deduped;
}

function WorkflowSummaryCard({
  title,
  badge,
  stats,
  sections,
}: {
  title: string;
  badge: string;
  stats: Array<{ label: string; value: string }>;
  sections: Array<{ title: string; items: string[]; emptyText: string }>;
}) {
  return (
    <div className="rounded-xl border border-stone-200 bg-stone-50/80 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-400">
          {title}
        </div>
        <span className="rounded-full border border-stone-200 bg-white px-2.5 py-1 text-[10px] font-semibold text-stone-700">
          {badge}
        </span>
      </div>

      <div className="mt-3 grid gap-2">
        {stats.map((item) => (
          <div
            key={`${title}-${item.label}`}
            className="rounded-lg border border-white/90 bg-white/90 px-2.5 py-2 shadow-[0_6px_18px_rgba(15,23,42,0.04)]"
          >
            <div className="text-[9px] font-semibold uppercase tracking-[0.18em] text-stone-400">
              {item.label}
            </div>
            <div className="mt-1 break-all text-[11px] font-medium leading-5 text-stone-700">
              {item.value}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 space-y-3">
        {sections.map((section) => (
          <div key={`${title}-${section.title}`}>
            <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-400">
              {section.title}
            </div>
            {section.items.length > 0 ? (
              <ul className="mt-2 space-y-1.5">
                {section.items.map((item) => (
                  <li
                    key={`${title}-${section.title}-${item}`}
                    className="flex gap-2 text-[11px] leading-5 text-stone-600"
                  >
                    <span className="mt-[6px] inline-block size-1.5 shrink-0 rounded-full bg-sky-500" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="mt-2 text-[11px] leading-5 text-stone-400">
                {section.emptyText}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function PlanItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-[110px] flex-1">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-amber-700">
        {label}
      </div>
      <div className="text-[12px] font-bold text-stone-900">{value}</div>
    </div>
  );
}

function MetricChip({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "green" | "blue" | "neutral";
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5">
      <div className="text-[9px] font-semibold uppercase tracking-[0.5px] text-slate-400">
        {label}
      </div>
      <div
        className={cn(
          "font-mono text-[18px] font-extrabold leading-tight tracking-tight",
          color === "green" && "text-green-500",
          color === "blue" && "text-blue-500",
          color === "neutral" && "text-stone-800",
        )}
      >
        {value}
      </div>
    </div>
  );
}
