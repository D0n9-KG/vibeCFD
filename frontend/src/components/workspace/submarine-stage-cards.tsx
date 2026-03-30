// src/components/workspace/submarine-stage-cards.tsx
"use client";

import { useCallback, useState } from "react";

import { cn } from "@/lib/utils";

import { SubmarineConvergenceChart } from "./submarine-convergence-chart";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineSolverMetrics,
  SubmarineDispatchPayload,
  SubmarineGeometryPayload,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";
import { type StageCardState, StageCard } from "./submarine-stage-card";

// ── Shared runtime snapshot type (re-declared locally to avoid coupling) ──────
export type StageRuntimeSnapshot = {
  current_stage?: string | null;
  task_summary?: string | null;
  simulation_requirements?: Record<string, number | null> | null;
  stage_status?: string | null;
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

function resolveStageState(
  stageId: RuntimeStage,
  currentStage?: string | null,
): StageCardState {
  if (!currentStage) return "pending";
  const currentIdx = STAGE_ORDER.indexOf(currentStage as RuntimeStage);
  const stageIdx = STAGE_ORDER.indexOf(stageId);
  if (stageIdx < currentIdx) return "done";
  if (stageIdx === currentIdx) return "active";
  return "pending";
}

// ── TaskIntelligenceCard ──────────────────────────────────────────────────────

interface TaskIntelligenceCardProps {
  threadId: string;
  snapshot: StageRuntimeSnapshot | null;
  designBrief: SubmarineDesignBriefPayload | null;
  onConfirm: (threadId: string, message: { role: "human"; content: string }) => void;
}

export function TaskIntelligenceCard({
  threadId,
  snapshot,
  designBrief,
  onConfirm,
}: TaskIntelligenceCardProps) {
  const state = resolveStageState("task-intelligence", snapshot?.current_stage);
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
  const simReq: SubmarineSimulationRequirements | null | undefined =
    brief?.simulation_requirements ??
    (snapshot?.simulation_requirements as SubmarineSimulationRequirements | null | undefined);
  const caseId = brief?.selected_case_id ?? null;
  const openQuestions = brief?.open_questions ?? [];

  const descriptionText =
    state === "done"
      ? brief?.task_description?.slice(0, 60) ?? "已确认方案"
      : state === "active"
        ? snapshot?.stage_status === "waiting_user"
          ? "方案待确认"
          : "正在分析任务…"
        : "等待开始";

  return (
    <StageCard
      state={state}
      index={1}
      name="任务理解"
      description={descriptionText}
      defaultExpanded={state === "active"}
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

interface GeometryPreflightCardProps {
  snapshot: StageRuntimeSnapshot | null;
  geometry: SubmarineGeometryPayload | null;
}

export function GeometryPreflightCard({
  snapshot,
  geometry,
}: GeometryPreflightCardProps) {
  const state = resolveStageState("geometry-preflight", snapshot?.current_stage);

  // SubmarineGeometryPayload has: summary_zh, candidate_cases (no geometry_family_hint)
  const description =
    state === "done"
      ? geometry?.summary_zh?.slice(0, 60) ?? "几何预检通过"
      : state === "active"
        ? "正在检查几何…"
        : "等待任务理解完成";

  return (
    <StageCard
      state={state}
      index={2}
      name="几何预检"
      description={description}
      defaultExpanded={state === "active"}
    >
      {geometry?.summary_zh && (
        <div className="text-[11px] text-stone-600">{geometry.summary_zh}</div>
      )}
      {!geometry && state === "active" && (
        <div className="text-[11px] text-stone-400">几何检查运行中…</div>
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
  const state = resolveStageState("solver-dispatch", snapshot?.current_stage);

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
      description={description}
      rightLabel={
        state === "active" ? (
          <span className="text-[11px] font-medium text-blue-500">运行中</span>
        ) : undefined
      }
      defaultExpanded={state === "active"}
    >
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
  const state = resolveStageState("result-reporting", snapshot?.current_stage);

  // Cd from solver metrics (latest_force_coefficients["Cd"]) or final report solver_metrics
  const reportSolverMetrics = finalReport?.solver_metrics ?? solverMetrics;
  const cd = reportSolverMetrics?.latest_force_coefficients?.Cd ?? null;
  const description =
    state === "done"
      ? cd != null ? `Cd = ${cd.toFixed(5)}` : "报告已生成"
      : state === "active"
        ? "结果整理中…"
        : "等待求解完成";

  return (
    <StageCard
      state={state}
      index={4}
      name="结果整理"
      description={description}
      defaultExpanded={state === "active"}
    >
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
  onConfirm: (threadId: string, message: { role: "human"; content: string }) => void;
}

export function SupervisorReviewCard({
  threadId,
  snapshot,
  onConfirm,
}: SupervisorReviewCardProps) {
  const state = resolveStageState("supervisor-review", snapshot?.current_stage);
  const reviewStatus = snapshot?.review_status ?? null;
  const gateStatus = snapshot?.scientific_gate_status ?? null;
  const needsUserConfirmation = reviewStatus === "needs_user_confirmation";

  const description =
    state === "done"
      ? "复核已完成"
      : state === "active"
        ? reviewStatus
          ? REVIEW_STATUS_LABELS[reviewStatus] ?? reviewStatus
          : "复核中…"
        : "等待结果整理";

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
      description={description}
      defaultExpanded={state === "active"}
    >
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

function _InfoRow({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-stone-400">{label}</span>
      <span className={cn("font-medium text-stone-800", valueClass)}>
        {value}
      </span>
    </div>
  );
}
