"use client";

import {
  ActivityIcon,
  ArrowUpRightIcon,
  BoxesIcon,
  Clock3Icon,
  FileJsonIcon,
  FileTextIcon,
  GaugeIcon,
  Layers2Icon,
  RadarIcon,
  ShipWheelIcon,
  WavesIcon,
} from "lucide-react";
import { useMemo, useState, type ComponentType, type ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { urlOfArtifact } from "@/core/artifacts/utils";
import { cn } from "@/lib/utils";

import { useArtifacts } from "./artifacts";
import { useThread } from "./messages/context";
import type {
  SubmarineDesignBriefPayload,
  SubmarineDispatchPayload,
  SubmarineFinalReportPayload,
  SubmarineGeometryPayload,
  SubmarineSolverMetrics,
} from "./submarine-runtime-panel.contract";
import {
  buildSparklinePath,
  buildSubmarineTrendSeries,
  type SubmarineTrendSeries,
} from "./submarine-runtime-panel.trends";
import {
  buildSubmarineAcceptanceSummary,
  buildSubmarineExecutionOutline,
  buildSubmarineStageTrack,
  buildSubmarineDesignBriefSummary,
  buildSubmarineExperimentCompareSummary,
  buildSubmarineExperimentSummary,
  buildSubmarineFigureDeliverySummary,
  buildSubmarineResearchEvidenceSummary,
  buildSubmarineResultCards,
  buildSubmarineScientificGateSummary,
  buildSubmarineScientificFollowupSummary,
  buildSubmarineScientificRemediationHandoffSummary,
  buildSubmarineScientificRemediationSummary,
  buildSubmarineScientificStudySummary,
  buildSubmarineScientificVerificationSummary,
  filterSubmarineArtifactGroups,
  formatSubmarineRuntimeStageLabel,
  getSubmarineArtifactFilterOptions,
  getSubmarineArtifactMeta,
  groupSubmarineArtifacts,
  type SubmarineArtifactFilterId,
  type SubmarineArtifactGroup,
  type SubmarineResultCard,
  type SubmarineStageTrackItem,
} from "./submarine-runtime-panel.utils";

type RuntimeStage =
  | "task-intelligence"
  | "geometry-preflight"
  | "solver-dispatch"
  | "result-reporting"
  | "supervisor-review"
  | "user-confirmation";

type SubmarineRuntimeSnapshot = {
  current_stage?: RuntimeStage;
  task_summary?: string;
  task_type?: string;
  geometry_virtual_path?: string;
  geometry_family?: string | null;
  selected_case_id?: string | null;
  simulation_requirements?: Record<string, number | null> | null;
  stage_status?: string | null;
  review_status?: string | null;
  scientific_gate_status?: string | null;
  allowed_claim_level?: string | null;
  scientific_gate_virtual_path?: string | null;
  next_recommended_stage?: string | null;
  report_virtual_path?: string | null;
  workspace_case_dir_virtual_path?: string | null;
  run_script_virtual_path?: string | null;
  artifact_virtual_paths?: string[];
  execution_plan?: Array<{
    role_id?: string | null;
    owner?: string | null;
    goal?: string | null;
    status?: string | null;
    target_skills?: string[] | null;
  }> | null;
  activity_timeline?: RuntimeTimelineEvent[] | null;
};

type RuntimeTimelineEvent = {
  stage?: string;
  actor?: string;
  role_id?: string | null;
  title?: string;
  summary?: string;
  status?: string | null;
  skill_names?: string[] | null;
  timestamp?: string | null;
};

type WorkbenchSectionId =
  | "runtime"
  | "brief"
  | "timeline"
  | "health"
  | "metrics"
  | "trend"
  | "cases"
  | "artifacts";

const WORKBENCH_SECTIONS: Array<{ id: WorkbenchSectionId; label: string }> = [
  { id: "runtime", label: "任务上下文" },
  { id: "brief", label: "方案简报" },
  { id: "timeline", label: "执行时间线" },
  { id: "health", label: "执行状态" },
  { id: "metrics", label: "关键指标" },
  { id: "trend", label: "结果趋势" },
  { id: "cases", label: "案例匹配" },
  { id: "artifacts", label: "Artifacts" },
];

export const STAGE_ORDER: RuntimeStage[] = [
  "task-intelligence",
  "geometry-preflight",
  "solver-dispatch",
  "result-reporting",
  "supervisor-review",
];

export const STAGE_LABELS: Record<RuntimeStage, string> = {
  "task-intelligence": "任务理解",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解执行",
  "result-reporting": "结果整理",
  "supervisor-review": "Supervisor 复核",
  "user-confirmation": "用户确认",
};

const REVIEW_STATUS_LABELS: Record<string, string> = {
  ready_for_supervisor: "待复核",
  needs_user_confirmation: "待确认",
  blocked: "已阻塞",
};

function formatStage(stage?: string | null) {
  if (!stage) return "未开始";
  return formatSubmarineRuntimeStageLabel(stage);
}

function formatReviewStatus(status?: string | null) {
  if (!status) return "运行中";
  return REVIEW_STATUS_LABELS[status] ?? status;
}

function formatTimelineTimestamp(value?: string | null) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatNumeric(value?: number | null, digits = 3, suffix = "") {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return `${value.toFixed(digits)}${suffix}`;
}

function safeJsonParse<T>(content?: string | null): T | null {
  if (!content) return null;
  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

function artifactWeight(path: string) {
  if (path.endsWith("/cfd-design-brief.md")) return 0;
  if (path.endsWith("/cfd-design-brief.html")) return 1;
  if (path.endsWith("/cfd-design-brief.json")) return 2;
  if (path.endsWith("/delivery-readiness.md")) return 3;
  if (path.endsWith("/delivery-readiness.json")) return 4;
  if (path.endsWith("/final-report.md")) return 5;
  if (path.endsWith("/final-report.html")) return 6;
  if (path.endsWith("/final-report.json")) return 7;
  if (path.endsWith("/solver-results.json")) return 8;
  if (path.endsWith("/openfoam-run.log")) return 9;
  return 20;
}

function artifactIcon(path: string) {
  if (path.endsWith(".json")) return FileJsonIcon;
  if (path.endsWith(".md") || path.endsWith(".html") || path.endsWith(".log")) {
    return FileTextIcon;
  }
  return Layers2Icon;
}

function sectionElementId(id: WorkbenchSectionId) {
  return `submarine-workbench-${id}`;
}

export function SubmarineRuntimePanel({
  threadId,
  className,
}: {
  threadId: string;
  className?: string;
}) {
  const { thread, isMock } = useThread();
  const { select, setOpen } = useArtifacts();
  const [artifactFilter, setArtifactFilter] =
    useState<SubmarineArtifactFilterId>("all");

  const runtime = useMemo(() => {
    const raw = thread.values.submarine_runtime;
    return raw && typeof raw === "object" ? (raw as SubmarineRuntimeSnapshot) : null;
  }, [thread.values.submarine_runtime]);

  const submarineArtifacts = useMemo(() => {
    const runtimeArtifacts = Array.isArray(runtime?.artifact_virtual_paths)
      ? runtime.artifact_virtual_paths
      : [];
    const threadArtifacts = Array.isArray(thread.values.artifacts)
      ? thread.values.artifacts
      : [];
    return [...threadArtifacts, ...runtimeArtifacts]
      .filter(
        (path, index, list) =>
          path.includes("/submarine/") && list.indexOf(path) === index,
      )
      .sort((left, right) => artifactWeight(left) - artifactWeight(right));
  }, [runtime?.artifact_virtual_paths, thread.values.artifacts]);

  const designBriefJson = submarineArtifacts.find((path) =>
    path.endsWith("/cfd-design-brief.json"),
  );
  const finalReportJson = submarineArtifacts.find((path) =>
    path.endsWith("/final-report.json"),
  );
  const solverResultsJson = submarineArtifacts.find((path) =>
    path.endsWith("/solver-results.json"),
  );
  const dispatchJson = submarineArtifacts.find((path) =>
    path.endsWith("/openfoam-request.json"),
  );
  const geometryJson = submarineArtifacts.find((path) =>
    path.endsWith("/geometry-check.json"),
  );

  const { content: designBriefContent } = useArtifactContent({
    filepath: designBriefJson ?? "",
    threadId,
    enabled: Boolean(designBriefJson),
  });
  const { content: finalReportContent } = useArtifactContent({
    filepath: finalReportJson ?? "",
    threadId,
    enabled: Boolean(finalReportJson),
  });
  const { content: solverResultsContent } = useArtifactContent({
    filepath: solverResultsJson ?? "",
    threadId,
    enabled: Boolean(solverResultsJson),
  });
  const { content: dispatchContent } = useArtifactContent({
    filepath: dispatchJson ?? "",
    threadId,
    enabled: Boolean(dispatchJson),
  });
  const { content: geometryContent } = useArtifactContent({
    filepath: geometryJson ?? "",
    threadId,
    enabled: Boolean(geometryJson),
  });

  const designBrief = useMemo(
    () => safeJsonParse<SubmarineDesignBriefPayload>(designBriefContent),
    [designBriefContent],
  );
  const finalReport = useMemo(
    () => safeJsonParse<SubmarineFinalReportPayload>(finalReportContent),
    [finalReportContent],
  );
  const solverResults = useMemo(
    () => safeJsonParse<SubmarineSolverMetrics>(solverResultsContent),
    [solverResultsContent],
  );
  const dispatchPayload = useMemo(
    () => safeJsonParse<SubmarineDispatchPayload>(dispatchContent),
    [dispatchContent],
  );
  const geometryPayload = useMemo(
    () => safeJsonParse<SubmarineGeometryPayload>(geometryContent),
    [geometryContent],
  );

  const fallbackBrief = useMemo<SubmarineDesignBriefPayload | null>(() => {
    if (!runtime?.task_summary && !runtime?.simulation_requirements) return null;
    return {
      task_description: runtime?.task_summary,
      confirmation_status:
        runtime?.review_status === "ready_for_supervisor" ? "confirmed" : "draft",
      simulation_requirements: runtime?.simulation_requirements ?? undefined,
      open_questions:
        runtime?.review_status === "needs_user_confirmation"
          ? ["当前方案仍需要继续和 Claude Code 确认。"]
          : [],
    };
  }, [runtime]);

  const activeDesignBrief = designBrief ?? fallbackBrief;
  const designBriefSummary = useMemo(
    () => buildSubmarineDesignBriefSummary(activeDesignBrief),
    [activeDesignBrief],
  );
  const acceptanceSummary = useMemo(
    () => buildSubmarineAcceptanceSummary(finalReport),
    [finalReport],
  );
  const figureDeliverySummary = useMemo(
    () => buildSubmarineFigureDeliverySummary(finalReport),
    [finalReport],
  );
  const researchEvidenceSummary = useMemo(
    () => buildSubmarineResearchEvidenceSummary(finalReport),
    [finalReport],
  );
  const scientificGateSummary = useMemo(
    () =>
      buildSubmarineScientificGateSummary(
        finalReport?.scientific_supervisor_gate
          ? finalReport
          : runtime?.scientific_gate_status || runtime?.allowed_claim_level
            ? {
                scientific_supervisor_gate: {
                  gate_status: runtime?.scientific_gate_status,
                  allowed_claim_level: runtime?.allowed_claim_level,
                  source_readiness_status: runtime?.allowed_claim_level,
                  recommended_stage: runtime?.next_recommended_stage,
                  artifact_virtual_paths: runtime?.scientific_gate_virtual_path
                    ? [runtime.scientific_gate_virtual_path]
                    : [],
                },
              }
            : null,
      ),
    [
      finalReport,
      runtime?.allowed_claim_level,
      runtime?.next_recommended_stage,
      runtime?.scientific_gate_status,
      runtime?.scientific_gate_virtual_path,
    ],
  );
  const experimentSummary = useMemo(
    () => buildSubmarineExperimentSummary(finalReport),
    [finalReport],
  );
  const scientificRemediationSummary = useMemo(
    () => buildSubmarineScientificRemediationSummary(finalReport),
    [finalReport],
  );
  const scientificRemediationHandoffSummary = useMemo(
    () => buildSubmarineScientificRemediationHandoffSummary(finalReport),
    [finalReport],
  );
  const scientificFollowupSummary = useMemo(
    () => buildSubmarineScientificFollowupSummary(finalReport),
    [finalReport],
  );
  const experimentCompareSummary = useMemo(
    () => buildSubmarineExperimentCompareSummary(finalReport),
    [finalReport],
  );
  const scientificVerificationSummary = useMemo(
    () => buildSubmarineScientificVerificationSummary(finalReport),
    [finalReport],
  );
  const scientificStudySummary = useMemo(
    () => buildSubmarineScientificStudySummary(finalReport),
    [finalReport],
  );
  const executionOutline = useMemo(
    () =>
      buildSubmarineExecutionOutline({
        designBrief: activeDesignBrief,
        runtimePlan: runtime?.execution_plan ?? null,
      }),
    [activeDesignBrief, runtime?.execution_plan],
  );
  const stageTrack = useMemo(
    () =>
      buildSubmarineStageTrack({
        runtimePlan: runtime?.execution_plan ?? null,
        currentStage: runtime?.current_stage,
      }),
    [runtime?.current_stage, runtime?.execution_plan],
  );
  const timelineEvents = runtime?.activity_timeline ?? [];

  const solverMetrics =
    finalReport?.solver_metrics ?? dispatchPayload?.solver_results ?? solverResults;
  const candidateCases =
    dispatchPayload?.candidate_cases ?? geometryPayload?.candidate_cases ?? [];
  const selectedCase =
    dispatchPayload?.selected_case ??
    candidateCases.find((item) => item.case_id === runtime?.selected_case_id) ??
    null;
  const trendSeries = useMemo(
    () => buildSubmarineTrendSeries(solverMetrics),
    [solverMetrics],
  );
  const artifactGroups = groupSubmarineArtifacts(submarineArtifacts);
  const artifactFilterOptions = useMemo(
    () => getSubmarineArtifactFilterOptions(artifactGroups),
    [artifactGroups],
  );
  const visibleArtifactGroups = useMemo(
    () => filterSubmarineArtifactGroups(artifactGroups, artifactFilter),
    [artifactGroups, artifactFilter],
  );
  const resultCards = useMemo(
    () =>
      buildSubmarineResultCards({
        requestedOutputs: designBriefSummary?.requestedOutputs,
        outputDelivery: acceptanceSummary?.outputDelivery,
        figureDelivery: figureDeliverySummary,
        artifactPaths: submarineArtifacts,
      }),
    [
      acceptanceSummary?.outputDelivery,
      designBriefSummary?.requestedOutputs,
      figureDeliverySummary,
      submarineArtifacts,
    ],
  );

  const cd =
    solverMetrics?.latest_force_coefficients &&
    typeof solverMetrics.latest_force_coefficients.Cd === "number"
      ? solverMetrics.latest_force_coefficients.Cd
      : null;
  const dragForceX =
    solverMetrics?.latest_forces?.total_force &&
    typeof solverMetrics.latest_forces.total_force[0] === "number"
      ? solverMetrics.latest_forces.total_force[0]
      : null;

  if (!runtime && submarineArtifacts.length === 0) {
    return null;
  }

  return (
    <Card className={cn("mb-5 border shadow-sm", className)}>
      <CardHeader className="border-b bg-muted/20 py-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
              <ShipWheelIcon className="size-4" />
              Submarine CFD Workbench
            </div>
            <div>
              <CardTitle className="text-xl">潜艇任务运行面板</CardTitle>
              <CardDescription className="mt-1 max-w-3xl text-sm leading-6">
                {finalReport?.summary_zh ??
                  designBrief?.summary_zh ??
                  dispatchPayload?.summary_zh ??
                  geometryPayload?.summary_zh ??
                  runtime?.task_summary ??
                  "当前线程已经进入潜艇 CFD 专业流程。这里集中展示方案简报、运行状态和交付产物。"}
              </CardDescription>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{formatStage(runtime?.current_stage)}</Badge>
            <Badge variant="outline">
              {formatReviewStatus(runtime?.review_status)}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5 px-5 py-5">
        <StageTrack items={stageTrack} />

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <MetricTile icon={ActivityIcon} label="运行状态" value={runtime?.stage_status ?? "待命中"} note={`下一阶段：${formatStage(runtime?.next_recommended_stage)}`} />
          <MetricTile icon={BoxesIcon} label="案例模板" value={selectedCase?.title ?? runtime?.selected_case_id ?? "待匹配"} note={runtime?.geometry_family ?? designBrief?.geometry_family_hint ?? "几何家族待识别"} />
          <MetricTile icon={GaugeIcon} label="阻力系数 Cd" value={formatNumeric(cd, 6)} note={`最终时间步：${formatNumeric(solverMetrics?.final_time_seconds, 0, " s")}`} />
          <MetricTile icon={WavesIcon} label="总阻力 Fx" value={formatNumeric(dragForceX, 4, " N")} note={`Artifacts：${submarineArtifacts.length}`} />
        </div>

        <QuickAccess onJump={(id) => document.getElementById(sectionElementId(id))?.scrollIntoView({ behavior: "smooth", block: "start" })} />

        <InfoPanel id={sectionElementId("runtime")} title="任务与运行上下文" kicker="Runtime">
          <RuntimeContextGrid
            entries={[
              { label: "任务摘要", value: runtime?.task_summary ?? designBrief?.task_description ?? "待生成" },
              { label: "几何文件", value: runtime?.geometry_virtual_path ?? designBrief?.geometry_virtual_path ?? "待上传" },
              { label: "几何家族", value: runtime?.geometry_family ?? designBrief?.geometry_family_hint ?? "待识别" },
              { label: "当前报告", value: runtime?.report_virtual_path ?? designBriefJson ?? "待生成" },
              { label: "Workspace case", value: runtime?.workspace_case_dir_virtual_path ?? "待生成" },
              { label: "Run script / 后处理", value: runtime?.run_script_virtual_path ?? solverMetrics?.workspace_postprocess_virtual_path ?? "待生成" },
            ]}
          />
        </InfoPanel>

        <InfoPanel id={sectionElementId("brief")} title="CFD 设计简报" kicker="Plan">
          {designBriefSummary ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <KeyValue label="方案状态" value={designBriefSummary.confirmationStatusLabel} />
                <KeyValue label="待确认项" value={`${designBriefSummary.openQuestions.length} 项`} />
                <KeyValue label="预期交付物" value={`${designBriefSummary.expectedOutputs.length} 项`} />
                <KeyValue label="下一步" value={formatStage(runtime?.next_recommended_stage ?? designBrief?.next_recommended_stage)} />
              </div>
              {designBriefSummary.requirementPairs.length > 0 && (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {designBriefSummary.requirementPairs.map((item) => (
                    <KeyValue key={item.label} label={item.label} value={item.value} />
                  ))}
                </div>
              )}
              <div className="grid gap-4 xl:grid-cols-3">
                <LabeledList title="预期交付物" items={designBriefSummary.expectedOutputs} emptyText="Claude Code 还没有整理出明确的交付清单。" />
                <LabeledList title="用户约束" items={designBriefSummary.userConstraints} emptyText="当前还没有明确的额外约束。" />
                <LabeledList title="待确认项" items={designBriefSummary.openQuestions} emptyText="当前方案已经没有待确认项。" />
              </div>
              <div className="rounded-xl border bg-background/70 p-4">
                <div className="mb-2 text-sm font-medium text-foreground">
                  Requested Outputs
                </div>
                <LabeledList
                  title="Requested Outputs"
                  items={designBriefSummary.requestedOutputs.map((item) =>
                    item.specSummary !== "--"
                      ? `${item.label} | ${item.supportLevel} | ${item.requestedLabel} | ${item.specSummary}`
                      : `${item.label} | ${item.supportLevel} | ${item.requestedLabel}`,
                  )}
                  emptyText="Claude Code 还没有把用户需求收敛成结构化输出合同。"
                />
              </div>
              <div className="rounded-xl border bg-background/70 p-4">
                <div className="mb-2 text-sm font-medium text-foreground">
                  Scientific Verification Requirements
                </div>
                <LabeledList
                  title="Scientific Verification Requirements"
                  items={designBriefSummary.scientificVerificationRequirements.map(
                    (item) =>
                      item.detail !== "--"
                        ? `${item.label} | ${item.checkType} | ${item.detail}`
                        : `${item.label} | ${item.checkType}`,
                  )}
                  emptyText="Current design brief does not yet list research-facing verification requirements."
                />
              </div>
              <OutlineList items={executionOutline} />
            </div>
          ) : (
            <EmptyState text="Claude Code 与用户的当前讨论还没有沉淀为结构化 CFD 设计简报。生成 design brief 后，这里会展示任务目标、待确认项、交付物和执行分工。" />
          )}
        </InfoPanel>

        <InfoPanel id={sectionElementId("timeline")} title="执行时间线" kicker="Timeline">
          {timelineEvents.length > 0 ? (
            <div className="space-y-3">
              {timelineEvents.map((event, index) => (
                <TimelineEventCard
                  key={`${event.timestamp ?? "event"}-${event.stage ?? "stage"}-${index}`}
                  event={event}
                />
              ))}
            </div>
          ) : (
            <EmptyState text="当前 thread 还没有沉淀执行时间线。随着 Claude Code 修订方案、几何预检、求解派发和结果报告推进，这里会持续追加阶段记录。" />
          )}
        </InfoPanel>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
          <div className="grid gap-4">
            <InfoPanel id={sectionElementId("health")} title="求解健康状态" kicker="Health">
              <div className="grid gap-3 md:grid-cols-3">
                <StatusTile icon={ShipWheelIcon} label="几何就绪" value={dispatchPayload?.requires_geometry_conversion ? "待转换" : runtime?.geometry_virtual_path ? "可求解" : "待上传"} note={dispatchPayload?.requires_geometry_conversion ? "当前上传格式需要先转换成 STL。" : runtime?.geometry_virtual_path ? "当前线程已经具备几何输入。" : "当前线程还没有潜艇几何输入。"} />
                <StatusTile icon={RadarIcon} label="求解执行" value={solverMetrics?.solver_completed ? "已完成" : runtime?.current_stage === "solver-dispatch" ? "执行中" : "待执行"} note={solverMetrics?.solver_completed ? `最终时间步 ${formatNumeric(solverMetrics.final_time_seconds, 0, " s")}` : runtime?.current_stage === "solver-dispatch" ? runtime?.stage_status ?? "等待更多求解产物。" : "完成几何预检与案例确认后，可进入真实 OpenFOAM 求解。"} />
                <StatusTile
                  icon={Layers2Icon}
                  label="Supervisor 复核"
                  value={formatReviewStatus(runtime?.review_status)}
                  note={
                    scientificGateSummary
                      ? `Scientific gate：${scientificGateSummary.gateStatusLabel}；claim level：${scientificGateSummary.allowedClaimLevelLabel}；下一阶段：${formatStage(runtime?.next_recommended_stage)}`
                      : `下一阶段：${formatStage(runtime?.next_recommended_stage)}`
                  }
                />
              </div>
              {acceptanceSummary ? (
                <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <KeyValue label="交付评估状态" value={acceptanceSummary.statusLabel} />
                    <KeyValue label="结果可信度" value={acceptanceSummary.confidenceLabel} />
                  </div>
                  <div className="grid gap-4 xl:grid-cols-4">
                    <LabeledList
                      title="通过检查"
                      items={acceptanceSummary.passedChecks}
                      emptyText="当前还没有记录到通过检查。"
                    />
                    <LabeledList
                      title="风险提醒"
                      items={acceptanceSummary.warnings}
                      emptyText="当前没有额外风险提醒。"
                    />
                    <LabeledList
                      title="阻断问题"
                      items={acceptanceSummary.blockingIssues}
                      emptyText="当前没有阻断问题。"
                    />
                    <LabeledList
                      title="Benchmark 对比"
                      items={acceptanceSummary.benchmarkComparisons.map((item) =>
                        `${item.metricId} | ${item.status} | ${item.quantity} ${item.observedValue} / ${item.referenceValue} | ${item.relativeError}`,
                      )}
                      emptyText="当前没有命中的 benchmark 对比。"
                    />
                  </div>
                  <LabeledList
                    title="Output Delivery"
                    items={acceptanceSummary.outputDelivery.map((item) =>
                      item.specSummary !== "--"
                        ? `${item.outputId} | ${item.deliveryStatus} | ${item.specSummary} | ${item.detail}`
                        : `${item.outputId} | ${item.deliveryStatus} | ${item.detail}`,
                    )}
                    emptyText="当前还没有记录请求输出的交付状态。"
                  />
                </div>
                ) : null}
                {scientificGateSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                      <KeyValue
                        label="Scientific Gate"
                        value={scientificGateSummary.gateStatusLabel}
                      />
                      <KeyValue
                        label="Allowed Claim"
                        value={scientificGateSummary.allowedClaimLevelLabel}
                      />
                      <KeyValue
                        label="Source Readiness"
                        value={scientificGateSummary.sourceReadinessLabel}
                      />
                      <KeyValue
                        label="Recommended Stage"
                        value={scientificGateSummary.recommendedStageLabel}
                      />
                      <KeyValue
                        label="Remediation"
                        value={scientificGateSummary.remediationStageLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="Blocking Reasons"
                        items={scientificGateSummary.blockingReasons}
                        emptyText="No scientific supervisor blockers are recorded."
                      />
                      <LabeledList
                        title="Advisory Notes"
                        items={scientificGateSummary.advisoryNotes}
                        emptyText="No scientific supervisor advisory notes are recorded."
                      />
                      <LabeledList
                        title="Gate Artifacts"
                        items={scientificGateSummary.artifactPaths}
                        emptyText="No scientific supervisor gate artifacts are recorded."
                      />
                    </div>
                  </div>
                ) : null}
                {researchEvidenceSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                      <KeyValue
                        label="Research Readiness"
                        value={researchEvidenceSummary.readinessLabel}
                      />
                      <KeyValue
                        label="Verification"
                        value={researchEvidenceSummary.verificationStatusLabel}
                      />
                      <KeyValue
                        label="Validation"
                        value={researchEvidenceSummary.validationStatusLabel}
                      />
                      <KeyValue
                        label="Provenance"
                        value={researchEvidenceSummary.provenanceStatusLabel}
                      />
                      <KeyValue
                        label="Confidence"
                        value={researchEvidenceSummary.confidenceLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-2">
                      <LabeledList
                        title="Passed Evidence"
                        items={researchEvidenceSummary.passedEvidence}
                        emptyText="No passed research evidence is recorded yet."
                      />
                      <LabeledList
                        title="Evidence Gaps"
                        items={researchEvidenceSummary.evidenceGaps}
                        emptyText="No research evidence gaps are recorded."
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="Benchmark Highlights"
                        items={researchEvidenceSummary.benchmarkHighlights}
                        emptyText="No benchmark highlights are recorded."
                      />
                      <LabeledList
                        title="Provenance Highlights"
                        items={researchEvidenceSummary.provenanceHighlights}
                        emptyText="No provenance highlights are recorded."
                      />
                      <LabeledList
                        title="Evidence Artifacts"
                        items={researchEvidenceSummary.artifactPaths}
                        emptyText="No research evidence artifacts are recorded."
                      />
                    </div>
                  </div>
                ) : null}
                {experimentSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="Experiment Registry"
                        value={experimentSummary.experimentStatusLabel}
                      />
                      <KeyValue
                        label="Experiment ID"
                        value={experimentSummary.experimentId}
                      />
                      <KeyValue
                        label="Baseline Run"
                        value={experimentSummary.baselineRunId}
                      />
                      <KeyValue
                        label="Run Count"
                        value={`${experimentSummary.runCount}`}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-2">
                      <LabeledList
                        title="Experiment Artifacts"
                        items={[
                          experimentSummary.manifestPath,
                          ...(experimentSummary.comparePath !== "--"
                            ? [experimentSummary.comparePath]
                            : []),
                        ]}
                        emptyText="No experiment registry artifacts are recorded yet."
                      />
                      <LabeledList
                        title="Run Compare Notes"
                        items={experimentSummary.compareNotes}
                        emptyText="No run compare notes are recorded yet."
                      />
                    </div>
                  </div>
                ) : null}
                {scientificRemediationSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="Remediation Plan"
                        value={scientificRemediationSummary.planStatusLabel}
                      />
                      <KeyValue
                        label="Current Claim"
                        value={scientificRemediationSummary.currentClaimLevelLabel}
                      />
                      <KeyValue
                        label="Target Claim"
                        value={scientificRemediationSummary.targetClaimLevelLabel}
                      />
                      <KeyValue
                        label="Recommended Stage"
                        value={scientificRemediationSummary.recommendedStageLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-2">
                      <LabeledList
                        title="Remediation Artifacts"
                        items={scientificRemediationSummary.artifactPaths}
                        emptyText="No remediation artifacts are recorded yet."
                      />
                      <LabeledList
                        title="Remediation Actions"
                        items={scientificRemediationSummary.actions.map(
                          (item) =>
                            `${item.title} | ${item.ownerStageLabel} | ${item.executionModeLabel} | ${item.statusLabel}`,
                        )}
                        emptyText="No remediation actions are recorded."
                      />
                    </div>
                    {scientificRemediationSummary.actions.length > 0 ? (
                      <div className="space-y-3">
                        {scientificRemediationSummary.actions.map((item) => (
                          <div
                            key={item.actionId}
                            className="rounded-xl border bg-muted/20 p-4"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="outline" className="bg-background/80">
                                {item.statusLabel}
                              </Badge>
                              <span className="text-sm font-medium text-foreground">
                                {item.title}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {item.ownerStageLabel} | {item.executionModeLabel}
                              </span>
                            </div>
                            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                              <KeyValue label="Action ID" value={item.actionId} />
                              <KeyValue label="Owner Stage" value={item.ownerStageLabel} />
                              <KeyValue label="Execution Mode" value={item.executionModeLabel} />
                              <KeyValue label="Priority" value={item.priority} />
                            </div>
                            <div className="mt-3 grid gap-4 xl:grid-cols-2">
                              <LabeledList
                                title="Action Summary"
                                items={[item.summary, item.evidenceGap]}
                                emptyText="No remediation detail is recorded."
                              />
                              <LabeledList
                                title="Required Artifacts"
                                items={item.requiredArtifacts}
                                emptyText="No required remediation artifacts are recorded."
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {scientificRemediationHandoffSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="Remediation Handoff"
                        value={scientificRemediationHandoffSummary.handoffStatusLabel}
                      />
                      <KeyValue
                        label="Recommended Action"
                        value={scientificRemediationHandoffSummary.recommendedActionId}
                      />
                      <KeyValue
                        label="Suggested Tool"
                        value={scientificRemediationHandoffSummary.toolName}
                      />
                      <KeyValue
                        label="Reason"
                        value={scientificRemediationHandoffSummary.reason}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="Handoff Artifacts"
                        items={scientificRemediationHandoffSummary.artifactPaths}
                        emptyText="No remediation handoff artifacts are recorded yet."
                      />
                      <LabeledList
                        title="Suggested Tool Args"
                        items={scientificRemediationHandoffSummary.toolArgs.map(
                          (item) => `${item.key} = ${item.value}`,
                        )}
                        emptyText="No tool arguments are recorded for this handoff."
                      />
                      <LabeledList
                        title="Manual Follow-Up"
                        items={scientificRemediationHandoffSummary.manualActions.map(
                          (item) =>
                            `${item.title} | ${item.ownerStageLabel} | ${item.evidenceGap}`,
                        )}
                        emptyText="No manual follow-up actions are recorded."
                      />
                    </div>
                    {scientificRemediationHandoffSummary.toolArgs.length > 0 ? (
                      <div className="space-y-3">
                        <div className="text-sm font-medium text-foreground">
                          Suggested Tool Contract
                        </div>
                        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                          {scientificRemediationHandoffSummary.toolArgs.map((item) => (
                            <div
                              key={item.key}
                              className="rounded-xl border bg-muted/20 p-4"
                            >
                              <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                                {item.key}
                              </div>
                              <div className="mt-2 break-all text-sm text-foreground">
                                {item.value}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {scientificFollowupSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="Follow-Up Entries"
                        value={`${scientificFollowupSummary.entryCount}`}
                      />
                      <KeyValue
                        label="Latest Outcome"
                        value={scientificFollowupSummary.latestOutcomeLabel}
                      />
                      <KeyValue
                        label="Latest Handoff"
                        value={scientificFollowupSummary.latestHandoffStatusLabel}
                      />
                      <KeyValue
                        label="Report Refreshed"
                        value={scientificFollowupSummary.reportRefreshedLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="Latest Follow-Up Contract"
                        items={[
                          `action | ${scientificFollowupSummary.latestRecommendedActionId}`,
                          `tool | ${scientificFollowupSummary.latestToolName}`,
                          `dispatch | ${scientificFollowupSummary.latestDispatchStageStatusLabel}`,
                        ]}
                        emptyText="No follow-up contract details are recorded."
                      />
                      <LabeledList
                        title="Latest Follow-Up Paths"
                        items={[
                          scientificFollowupSummary.historyPath,
                          ...(scientificFollowupSummary.latestResultReportPath !== "--"
                            ? [scientificFollowupSummary.latestResultReportPath]
                            : []),
                          ...(scientificFollowupSummary.latestResultHandoffPath !== "--"
                            ? [scientificFollowupSummary.latestResultHandoffPath]
                            : []),
                        ]}
                        emptyText="No follow-up artifact paths are recorded."
                      />
                      <LabeledList
                        title="Latest Follow-Up Notes"
                        items={scientificFollowupSummary.latestNotes}
                        emptyText="No follow-up notes are recorded."
                      />
                    </div>
                    <LabeledList
                      title="Follow-Up Artifacts"
                      items={scientificFollowupSummary.artifactPaths}
                      emptyText="No follow-up artifacts are recorded."
                    />
                  </div>
                ) : null}
                {experimentCompareSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="Experiment Compare"
                        value={`${experimentCompareSummary.compareCount}`}
                      />
                      <KeyValue
                        label="Experiment ID"
                        value={experimentCompareSummary.experimentId}
                      />
                      <KeyValue
                        label="Baseline Run"
                        value={experimentCompareSummary.baselineRunId}
                      />
                      <KeyValue
                        label="Compare Artifact"
                        value={experimentCompareSummary.comparePath}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-2">
                      <LabeledList
                        title="Compare Artifacts"
                        items={experimentCompareSummary.artifactPaths}
                        emptyText="No experiment compare artifacts are recorded yet."
                      />
                      <LabeledList
                        title="Compared Runs"
                        items={experimentCompareSummary.comparisons.map(
                          (item) =>
                            `${experimentCompareSummary.baselineRunId} -> ${item.candidateRunId} | ${item.compareStatusLabel} | ${item.studyLabel}`,
                        )}
                        emptyText="No experiment comparisons are recorded yet."
                      />
                    </div>
                    {experimentCompareSummary.comparisons.length > 0 ? (
                      <div className="space-y-3">
                        {experimentCompareSummary.comparisons.map((item) => (
                          <div
                            key={`${item.candidateRunId}-${item.studyLabel}`}
                            className="rounded-xl border bg-muted/20 p-4"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="outline" className="bg-background/80">
                                {item.compareStatusLabel}
                              </Badge>
                              <span className="text-sm font-medium text-foreground">
                                {experimentCompareSummary.baselineRunId}
                                {" -> "}
                                {item.candidateRunId}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {item.studyLabel}
                              </span>
                            </div>
                            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                              <KeyValue label="Study Type" value={item.studyType} />
                              <KeyValue label="Variant" value={item.variantId} />
                              <KeyValue label="Status" value={item.compareStatusLabel} />
                              <KeyValue label="Notes" value={item.notes} />
                            </div>
                            <div className="mt-3 grid gap-4 xl:grid-cols-2">
                              <LabeledList
                                title="Metric Deltas"
                                items={
                                  item.metricDeltaLines.length > 0
                                    ? item.metricDeltaLines
                                    : [item.notes]
                                }
                                emptyText="No compare metric deltas are recorded."
                              />
                              <LabeledList
                                title="Comparison Artifacts"
                                items={item.artifactPaths}
                                emptyText="No comparison artifacts are recorded."
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {scientificStudySummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2">
                    <KeyValue
                      label="Scientific Studies"
                      value={scientificStudySummary.executionStatusLabel}
                    />
                    <KeyValue
                      label="Study Manifest"
                      value={scientificStudySummary.manifestPath}
                    />
                  </div>
                  <div className="grid gap-4 xl:grid-cols-2">
                    <LabeledList
                      title="Study Status"
                      items={scientificStudySummary.studies.map((item) =>
                        `${item.summaryLabel} | ${item.verificationStatus} | ${item.monitoredQuantity} | variants=${item.variantCount} | ${item.verificationDetail}`,
                      )}
                      emptyText="No scientific study summaries are available yet."
                    />
                    <LabeledList
                      title="Study Artifacts"
                      items={scientificStudySummary.artifactPaths}
                      emptyText="No scientific study artifacts are recorded yet."
                    />
                  </div>
                </div>
              ) : null}
              {scientificVerificationSummary ? (
                <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <KeyValue
                      label="Scientific Verification"
                      value={scientificVerificationSummary.statusLabel}
                    />
                    <KeyValue
                      label="Verification Confidence"
                      value={scientificVerificationSummary.confidenceLabel}
                    />
                  </div>
                  <div className="grid gap-4 xl:grid-cols-3">
                    <LabeledList
                      title="Passed Requirements"
                      items={scientificVerificationSummary.passedRequirements}
                      emptyText="No scientific verification checks have passed yet."
                    />
                    <LabeledList
                      title="Missing Evidence"
                      items={scientificVerificationSummary.missingEvidence}
                      emptyText="No missing scientific verification evidence is recorded."
                    />
                    <LabeledList
                      title="Blocking Issues"
                      items={scientificVerificationSummary.blockingIssues}
                      emptyText="No scientific verification blockers are recorded."
                    />
                  </div>
                  <LabeledList
                    title="Requirement Status"
                    items={scientificVerificationSummary.requirements.map(
                      (item) => `${item.label} | ${item.status} | ${item.detail}`,
                    )}
                    emptyText="No scientific verification requirement statuses are available."
                  />
                </div>
              ) : null}
            </InfoPanel>

            <InfoPanel id={sectionElementId("metrics")} title="关键 CFD 指标" kicker="Metrics">
              {solverMetrics ? (
                <div className="grid gap-3 md:grid-cols-2">
                  <KeyValue label="求解完成" value={solverMetrics.solver_completed ? "是" : "否"} />
                  <KeyValue label="最终时间步" value={formatNumeric(solverMetrics.final_time_seconds, 0, " s")} />
                  <KeyValue label="Cd" value={formatNumeric(cd, 6)} />
                  <KeyValue label="参考长度" value={formatNumeric(solverMetrics.reference_values?.reference_length_m, 3, " m")} />
                  <KeyValue label="参考面积" value={formatNumeric(solverMetrics.reference_values?.reference_area_m2, 3, " m^2")} />
                  <KeyValue label="来流速度" value={formatNumeric(solverMetrics.reference_values?.inlet_velocity_mps, 2, " m/s")} />
                </div>
              ) : (
                <EmptyState text="当前线程还没有可展示的 CFD 指标。完成几何预检和求解执行后，这里会自动展示关键系数和工况。" />
              )}
            </InfoPanel>

            <InfoPanel id={sectionElementId("trend")} title="结果趋势" kicker="Trend">
              {trendSeries.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {trendSeries.map((series) => (
                    <TrendTile key={series.id} series={series} />
                  ))}
                </div>
              ) : (
                <EmptyState text="当前还没有可展示的时间序列趋势。完成真实 OpenFOAM 求解并写出 forces 历史后，这里会显示收敛与受力变化趋势。" />
              )}
            </InfoPanel>
          </div>

          <div className="grid gap-4">
            <InfoPanel id={sectionElementId("cases")} title="案例匹配" kicker="Case Match">
              {candidateCases.length > 0 ? (
                <div className="space-y-3">
                  {candidateCases.slice(0, 3).map((candidate) => (
                    <div key={candidate.case_id} className={cn("rounded-xl border p-3", candidate.case_id === runtime?.selected_case_id ? "border-primary/30 bg-primary/5" : "border-border bg-muted/20")}>
                      <div className="mb-2 flex items-start justify-between gap-3">
                        <div>
                          <div className="font-medium text-foreground">{candidate.title}</div>
                          <div className="text-xs text-muted-foreground">{candidate.geometry_family ?? "潜艇"} · {candidate.task_type ?? "任务类型待定"}</div>
                        </div>
                        {typeof candidate.score === "number" && <Badge variant="outline">{candidate.score.toFixed(2)}</Badge>}
                      </div>
                      <div className="text-sm leading-6 text-muted-foreground">{candidate.rationale ?? "待补充说明"}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState text="当前还没有可显示的候选案例。执行几何预检后，这里会展示最匹配的潜艇案例和理由。" />
              )}
            </InfoPanel>

            <InfoPanel id={sectionElementId("artifacts")} title="Artifacts 工作台" kicker="Deliverables">
              {artifactGroups.length > 0 || resultCards.length > 0 ? (
                <div className="space-y-4">
                  {resultCards.length > 0 ? (
                    <div className="rounded-xl border bg-background/70 p-4">
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-medium text-foreground">
                            Requested Results
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Output-specific result cards with previews, delivery
                            status, and postprocess provenance.
                          </div>
                        </div>
                        <Badge variant="outline">{resultCards.length}</Badge>
                      </div>
                      <div className="grid gap-3 xl:grid-cols-2">
                        {resultCards.map((card) => (
                          <RequestedResultCard
                            key={card.outputId}
                            card={card}
                            threadId={threadId}
                            isMock={Boolean(isMock)}
                            onOpenArtifact={(artifactPath) => {
                              select(artifactPath);
                              setOpen(true);
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {artifactGroups.length > 0 ? (
                    <>
                      <div className="flex flex-wrap gap-2">
                        {artifactFilterOptions.map((option) => (
                          <Button
                            key={option.id}
                            size="sm"
                            variant={
                              artifactFilter === option.id ? "secondary" : "outline"
                            }
                            aria-pressed={artifactFilter === option.id}
                            onClick={() => setArtifactFilter(option.id)}
                          >
                            {option.label}
                            <Badge
                              variant="outline"
                              className="ml-1 rounded-full bg-background/80"
                            >
                              {option.count}
                            </Badge>
                          </Button>
                        ))}
                      </div>
                      {visibleArtifactGroups.map((group) => (
                        <ArtifactGroupSection
                          key={group.id}
                          group={group}
                          threadId={threadId}
                          isMock={Boolean(isMock)}
                          onOpenArtifact={(artifactPath) => {
                            select(artifactPath);
                            setOpen(true);
                          }}
                        />
                      ))}
                    </>
                  ) : null}
                </div>
              ) : (
                <EmptyState text="当前还没有潜艇领域产物。上传几何并触发 DeerFlow run 后，这里会集中显示阶段报告、日志和结果文件。" />
              )}
            </InfoPanel>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function QuickAccess({ onJump }: { onJump: (id: WorkbenchSectionId) => void }) {
  return (
    <div className="rounded-xl border bg-muted/20 p-4">
      <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
        <Layers2Icon className="size-4" />
        Quick Access
      </div>
      <div className="flex flex-wrap gap-2">
        {WORKBENCH_SECTIONS.map((section) => (
          <Button key={section.id} size="sm" variant="outline" onClick={() => onJump(section.id)}>
            {section.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

function formatResultToken(value: string) {
  const labels: Record<string, string> = {
    delivered: "Delivered",
    requested: "Requested",
    pending: "Pending",
    supported: "Supported",
    partially_delivered: "Partially Delivered",
    not_yet_supported: "Not Yet Supported",
  };

  return labels[value] ?? value.replaceAll("_", " ");
}

function RequestedResultCard({
  card,
  threadId,
  isMock,
  onOpenArtifact,
}: {
  card: SubmarineResultCard;
  threadId: string;
  isMock: boolean;
  onOpenArtifact: (artifactPath: string) => void;
}) {
  return (
    <div className="rounded-xl border bg-muted/20 p-3">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-foreground">
            {card.label}
          </div>
          <div className="truncate text-xs text-muted-foreground">
            {card.outputId}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Badge
            variant={card.deliveryStatus === "delivered" ? "secondary" : "outline"}
          >
            {formatResultToken(card.deliveryStatus)}
          </Badge>
          <Badge variant="outline">{formatResultToken(card.supportLevel)}</Badge>
        </div>
      </div>

      {card.previewArtifactPath ? (
        <button
          type="button"
          className="mb-3 block w-full overflow-hidden rounded-lg border bg-background/80 text-left"
          onClick={() => onOpenArtifact(card.previewArtifactPath!)}
        >
          <img
            src={urlOfArtifact({
              filepath: card.previewArtifactPath,
              threadId,
              isMock,
            })}
            alt={`${card.label} preview`}
            className="aspect-[16/10] w-full object-cover"
          />
        </button>
      ) : (
        <div className="mb-3 flex aspect-[16/10] items-center justify-center rounded-lg border border-dashed bg-background/50 px-4 text-center text-xs text-muted-foreground">
          Preview will appear here after the requested postprocess result is
          exported.
        </div>
      )}

      <div className="space-y-2 text-xs text-muted-foreground">
        <div>
          <span className="font-medium text-foreground/80">Requested:</span>{" "}
          {card.requestedLabel}
        </div>
        {card.specSummary !== "--" ? <div>Spec: {card.specSummary}</div> : null}
        {card.figureRenderStatus !== "--" ? (
          <div>
            <span className="font-medium text-foreground/80">Figure status:</span>{" "}
            {card.figureRenderStatus}
          </div>
        ) : null}
        {card.figureCaption !== "--" ? <div>Caption: {card.figureCaption}</div> : null}
        {card.selectorSummary !== "--" ? (
          <div>Selector provenance: {card.selectorSummary}</div>
        ) : null}
        {card.detail !== "--" ? <div>{card.detail}</div> : null}
      </div>

      {card.artifacts.length > 0 ? (
        <div className="mt-3 space-y-2">
          {card.artifacts.map((artifact) => (
            <div
              key={artifact.path}
              className="flex items-center justify-between gap-2 rounded-lg border bg-background/70 p-2"
            >
              <div className="min-w-0">
                <div className="truncate text-xs font-medium text-foreground">
                  {artifact.label}
                </div>
                <div className="truncate text-[11px] text-muted-foreground">
                  {artifact.path}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8"
                  onClick={() => onOpenArtifact(artifact.path)}
                >
                  Open
                </Button>
                <Button asChild size="icon-sm" variant="ghost">
                  <a
                    href={urlOfArtifact({ filepath: artifact.path, threadId, isMock })}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={artifact.externalLinkLabel}
                    title={artifact.externalLinkLabel}
                  >
                    <ArrowUpRightIcon className="size-4" />
                  </a>
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-3 rounded-lg border border-dashed bg-background/50 px-3 py-2 text-xs text-muted-foreground">
          No dedicated artifacts have been exported for this output yet.
        </div>
      )}
    </div>
  );
}

function ArtifactGroupSection({
  group,
  threadId,
  isMock,
  onOpenArtifact,
}: {
  group: SubmarineArtifactGroup;
  threadId: string;
  isMock: boolean;
  onOpenArtifact: (artifactPath: string) => void;
}) {
  return (
    <div className="rounded-xl border bg-muted/20 p-3">
      <div className="mb-3">
        <div className="text-sm font-semibold text-foreground">{group.label}</div>
        <div className="text-xs text-muted-foreground">共 {group.count} 个产物</div>
      </div>
      <div className="space-y-2">
        {group.paths.map((artifactPath) => {
          const Icon = artifactIcon(artifactPath);
          const meta = getSubmarineArtifactMeta(artifactPath);
          return (
            <div key={artifactPath} className="flex items-center justify-between gap-3 rounded-xl border bg-background/70 p-3">
              <div className="flex min-w-0 items-center gap-3">
                <div className="rounded-lg border bg-muted/40 p-2">
                  <Icon className="size-4 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-foreground">{meta.label}</div>
                  <div className="truncate text-xs text-muted-foreground">{artifactPath}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => onOpenArtifact(artifactPath)}>
                  查看
                </Button>
                <Button asChild size="icon-sm" variant="ghost">
                  <a
                    href={urlOfArtifact({ filepath: artifactPath, threadId, isMock })}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={meta.externalLinkLabel}
                    title={meta.externalLinkLabel}
                  >
                    <ArrowUpRightIcon className="size-4" />
                  </a>
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MetricTile({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-xl border bg-muted/20 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
        <Icon className="size-4" />
        {label}
      </div>
      <div className="text-lg font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{note}</div>
    </div>
  );
}

function TrendTile({ series }: { series: SubmarineTrendSeries }) {
  return (
    <div className="rounded-xl border bg-background/70 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-foreground">{series.label}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            {series.values.length} 个采样点
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold text-foreground">
            {formatNumeric(series.latestValue, series.unit ? 4 : 6, series.unit ? ` ${series.unit}` : "")}
          </div>
          <div className="text-xs text-muted-foreground">最新值</div>
        </div>
      </div>
      <div className="mt-3 overflow-hidden rounded-lg border bg-muted/30">
        <svg aria-hidden="true" viewBox="0 0 240 84" className="block h-24 w-full text-primary" preserveAspectRatio="none">
          <path
            d={buildSparklinePath(series.values, 240, 84)}
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2.5"
          />
        </svg>
      </div>
    </div>
  );
}

function InfoPanel({
  id,
  title,
  kicker,
  children,
}: {
  id?: string;
  title: string;
  kicker: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 rounded-xl border bg-muted/20 p-4">
      <div className="mb-4">
        <div className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">{kicker}</div>
        <div className="mt-1 text-base font-semibold text-foreground">{title}</div>
      </div>
      {children}
    </section>
  );
}

function RuntimeContextGrid({
  entries,
}: {
  entries: Array<{ label: string; value?: string | null }>;
}) {
  return (
    <div className="grid gap-3">
      {entries.map((entry) => (
        <div key={entry.label} className="grid gap-2 rounded-xl border bg-background/70 p-4 sm:grid-cols-[160px_minmax(0,1fr)]">
          <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{entry.label}</div>
          <div className="min-w-0 break-all text-sm leading-6 text-foreground">{entry.value ?? "--"}</div>
        </div>
      ))}
    </div>
  );
}

function KeyValue({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-xl border bg-background/70 p-3">
      <div className="mb-1 text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
      <div className="break-words text-sm leading-6 text-foreground">{value ?? "--"}</div>
    </div>
  );
}

function StatusTile({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-xl border bg-background/70 p-3">
      <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
        <Icon className="size-4" />
        {label}
      </div>
      <Badge variant="outline">{value}</Badge>
      <div className="mt-3 text-sm leading-6 text-muted-foreground">{note}</div>
    </div>
  );
}

function TimelineEventCard({ event }: { event: RuntimeTimelineEvent }) {
  const skillNames = event.skill_names?.filter(Boolean) ?? [];
  return (
    <div className="rounded-xl border bg-background/70 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{formatStage(event.stage)}</Badge>
            {event.status ? <Badge variant="secondary">{event.status}</Badge> : null}
          </div>
          <div className="text-sm font-medium text-foreground">
            {event.title ?? "阶段事件"}
          </div>
          {event.summary ? (
            <div className="text-sm leading-6 text-muted-foreground">
              {event.summary}
            </div>
          ) : null}
          {skillNames.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {skillNames.map((skillName) => (
                <Badge key={skillName} variant="outline" className="bg-background/80">
                  {skillName}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
          <Clock3Icon className="size-4" />
          <span>{event.actor ?? "DeerFlow"}</span>
          <span>·</span>
          <span>{formatTimelineTimestamp(event.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}

function LabeledList({
  title,
  items,
  emptyText,
}: {
  title: string;
  items: string[];
  emptyText: string;
}) {
  return (
    <div className="rounded-xl border bg-background/70 p-4">
      <div className="mb-3 text-sm font-medium text-foreground">{title}</div>
      {items.length > 0 ? (
        <ul className="space-y-2 text-sm leading-6 text-foreground">
          {items.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="mt-[9px] size-1.5 shrink-0 rounded-full bg-primary" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="text-sm text-muted-foreground">{emptyText}</div>
      )}
    </div>
  );
}

function OutlineList({
  items,
}: {
  items: Array<{
    roleId: string;
    roleLabel: string;
    owner: string;
    goal: string;
    status: string;
    targetSkills: string[];
  }>;
}) {
  return (
    <div className="rounded-xl border bg-background/70 p-4">
      <div className="mb-3 text-sm font-medium text-foreground">执行分工</div>
      {items.length > 0 ? (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={`${item.roleId}-${item.owner}`} className="rounded-lg border bg-muted/20 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{item.roleLabel}</Badge>
                <span className="text-sm font-medium text-foreground">{item.owner}</span>
                <Badge variant="secondary">{item.status}</Badge>
              </div>
              <div className="mt-2 text-xs text-muted-foreground">{item.roleId}</div>
              <div className="mt-2 text-sm leading-6 text-muted-foreground">{item.goal}</div>
              {item.targetSkills.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {item.targetSkills.map((skillName) => (
                    <Badge key={`${item.roleId}-${skillName}`} variant="outline" className="bg-background/80">
                      {skillName}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-muted-foreground">当前还没有明确的执行分工。</div>
      )}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed bg-background/40 p-4 text-sm text-muted-foreground">
      {text}
    </div>
  );
}

function formatStageTrackStatus(status?: string | null) {
  if (!status) {
    return "pending";
  }
  return status.replaceAll("_", " ");
}

function StageTrack({ items }: { items: SubmarineStageTrackItem[] }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
      {items.map((item, index) => {
        const isBlocked = item.status === "blocked";
        const isCurrent =
          item.status === "in_progress" || item.status === "ready";
        const isComplete = item.status === "completed";
        return (
          <div
            key={item.stageId}
            className={cn(
              "rounded-xl border px-3 py-3",
              isBlocked && "border-red-200 bg-red-50/80",
              item.status === "ready" && "border-amber-200 bg-amber-50/80",
              isCurrent && item.status !== "ready" && "border-primary/30 bg-primary/5",
              isComplete && "border-emerald-200 bg-emerald-50/80",
              !isBlocked &&
                !isCurrent &&
                !isComplete &&
                item.status !== "ready" &&
                "border-border bg-muted/30",
            )}
          >
            <div className="mb-1 text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Step {index + 1}
            </div>
            <div className="text-sm font-medium text-foreground">{item.label}</div>
            <div className="mt-2 text-xs text-muted-foreground">
              {formatStageTrackStatus(item.status)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
