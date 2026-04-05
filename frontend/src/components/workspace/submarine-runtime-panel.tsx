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
import { localizeWorkspaceDisplayText } from "@/core/i18n/workspace-display";
import { cn } from "@/lib/utils";

import { useArtifacts } from "./artifacts";
import { useThread } from "./messages/context";
import type {
  SubmarineDesignBriefPayload,
  SubmarineDispatchPayload,
  SubmarineFinalReportPayload,
  SubmarineGeometryPayload,
  SubmarineRuntimeSnapshotPayload,
  SubmarineRuntimeTimelineEventPayload,
  SubmarineSolverMetrics,
} from "./submarine-runtime-panel.contract";
import {
  buildSparklinePath,
  buildSubmarineTrendSeries,
  type SubmarineTrendSeries,
} from "./submarine-runtime-panel.trends";
import {
  buildSubmarineAcceptanceSummary,
  buildSubmarineConclusionSectionsSummary,
  buildSubmarineDeliveryDecisionSummary,
  buildSubmarineEvidenceIndexSummary,
  buildSubmarineExecutionOutline,
  buildSubmarineStageTrack,
  buildSubmarineDesignBriefSummary,
  buildSubmarineExperimentCompareSummary,
  buildSubmarineExperimentSummary,
  buildSubmarineFigureDeliverySummary,
  buildSubmarineOutputDeliverySummary,
  buildSubmarineReportOverviewSummary,
  buildSubmarineResearchEvidenceSummary,
  buildSubmarineReproducibilitySummary,
  buildSubmarineResultCards,
  buildSubmarineScientificGateSummary,
  buildSubmarineScientificFollowupSummary,
  buildSubmarineScientificRemediationHandoffSummary,
  buildSubmarineScientificRemediationSummary,
  buildSubmarineStabilityEvidenceSummary,
  buildSubmarineScientificStudySummary,
  buildSubmarineScientificVerificationSummary,
  filterSubmarineArtifactGroups,
  formatSubmarineBenchmarkComparisonSummaryLine,
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

type SubmarineRuntimeSnapshot = SubmarineRuntimeSnapshotPayload;
type RuntimeTimelineEvent = SubmarineRuntimeTimelineEventPayload;

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
  { id: "artifacts", label: "产物" },
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
  "supervisor-review": "主管复核",
  "user-confirmation": "用户确认",
};

const REVIEW_STATUS_LABELS: Record<string, string> = {
  ready_for_supervisor: "待复核",
  needs_user_confirmation: "待确认",
  blocked: "已阻塞",
};

const RUNTIME_STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  pending: "待执行",
  ready: "就绪",
  in_progress: "进行中",
  running: "运行中",
  completed: "已完成",
  blocked: "已阻塞",
  failed: "失败",
  needs_clarification: "待澄清",
  needs_user_confirmation: "待用户确认",
};

function localizeRuntimeText(value?: string | null) {
  if (!value) {
    return "--";
  }

  return localizeWorkspaceDisplayText(value.replaceAll("_", " "));
}

function formatStage(stage?: string | null) {
  if (!stage) return "未开始";
  return formatSubmarineRuntimeStageLabel(stage);
}

function formatReviewStatus(status?: string | null) {
  if (!status) return "运行中";
  return REVIEW_STATUS_LABELS[status] ?? localizeRuntimeText(status);
}

function formatRuntimeStatus(status?: string | null) {
  if (!status) {
    return "--";
  }

  return RUNTIME_STATUS_LABELS[status] ?? localizeRuntimeText(status);
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
  const dispatchJson =
    runtime?.request_virtual_path ??
    submarineArtifacts.find((path) => path.endsWith("/openfoam-request.json"));
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
  const dispatchPayload = useMemo(
    () => safeJsonParse<SubmarineDispatchPayload>(dispatchContent),
    [dispatchContent],
  );
  const solverResultsJson =
    runtime?.solver_results_virtual_path ??
    dispatchPayload?.solver_results_virtual_path ??
    submarineArtifacts.find((path) => path.endsWith("/solver-results.json"));
  const executionLogPath =
    runtime?.execution_log_virtual_path ??
    dispatchPayload?.execution_log_virtual_path ??
    submarineArtifacts.find((path) => path.endsWith("/openfoam-run.log")) ??
    null;
  const solverResultsMarkdownPath =
    dispatchPayload?.solver_results_markdown_virtual_path ??
    submarineArtifacts.find((path) => path.endsWith("/solver-results.md")) ??
    null;
  const { content: solverResultsContent } = useArtifactContent({
    filepath: solverResultsJson ?? "",
    threadId,
    enabled: Boolean(solverResultsJson),
  });
  const solverResults = useMemo(
    () => safeJsonParse<SubmarineSolverMetrics>(solverResultsContent),
    [solverResultsContent],
  );
  const geometryPayload = useMemo(
    () => safeJsonParse<SubmarineGeometryPayload>(geometryContent),
    [geometryContent],
  );

  const fallbackBrief = useMemo<SubmarineDesignBriefPayload | null>(() => {
    if (
      !runtime?.task_summary &&
      !runtime?.simulation_requirements &&
      !(runtime?.requested_outputs?.length ?? 0)
    ) {
      return null;
    }
    return {
      task_description: runtime?.task_summary ?? undefined,
      confirmation_status:
        runtime?.review_status === "ready_for_supervisor" ? "confirmed" : "draft",
      simulation_requirements: runtime?.simulation_requirements ?? undefined,
      requested_outputs:
        runtime?.requested_outputs ??
        dispatchPayload?.requested_outputs ??
        undefined,
      open_questions:
        runtime?.review_status === "needs_user_confirmation"
          ? ["当前方案仍需要继续和 Claude Code 确认。"]
          : [],
    };
  }, [dispatchPayload?.requested_outputs, runtime]);

  const activeDesignBrief = designBrief ?? fallbackBrief;
  const designBriefSummary = useMemo(
    () => buildSubmarineDesignBriefSummary(activeDesignBrief),
    [activeDesignBrief],
  );
  const acceptanceSummary = useMemo(
    () => buildSubmarineAcceptanceSummary(finalReport),
    [finalReport],
  );
  const runtimeOutputDeliverySummary = useMemo(
    () =>
      buildSubmarineOutputDeliverySummary({
        requestedOutputs:
          runtime?.requested_outputs ??
          dispatchPayload?.requested_outputs ??
          activeDesignBrief?.requested_outputs ??
          finalReport?.requested_outputs,
        outputDeliveryPlan:
          runtime?.output_delivery_plan ??
          dispatchPayload?.output_delivery_plan ??
          finalReport?.output_delivery_plan,
      }),
    [
      activeDesignBrief?.requested_outputs,
      dispatchPayload?.output_delivery_plan,
      dispatchPayload?.requested_outputs,
      finalReport?.output_delivery_plan,
      finalReport?.requested_outputs,
      runtime?.output_delivery_plan,
      runtime?.requested_outputs,
    ],
  );
  const outputDeliverySummary =
    (acceptanceSummary?.outputDelivery?.length ?? 0) > 0
      ? acceptanceSummary!.outputDelivery
      : runtimeOutputDeliverySummary;
  const reportOverviewSummary = useMemo(
    () => buildSubmarineReportOverviewSummary(finalReport),
    [finalReport],
  );
  const deliveryHighlights = useMemo(() => {
    const summary = finalReport?.delivery_highlights;
    if (!summary) {
      return null;
    }

    return {
      metricLines: summary.metric_lines?.filter(Boolean) ?? [],
      figureTitles: summary.figure_titles?.filter(Boolean) ?? [],
      highlightArtifactPaths:
        summary.highlight_artifact_virtual_paths?.filter(Boolean) ?? [],
    };
  }, [finalReport]);
  const conclusionSectionsSummary = useMemo(
    () => buildSubmarineConclusionSectionsSummary(finalReport),
    [finalReport],
  );
  const evidenceIndexSummary = useMemo(
    () => buildSubmarineEvidenceIndexSummary(finalReport),
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
  const reproducibilitySummary = useMemo(
    () =>
      buildSubmarineReproducibilitySummary(
        finalReport?.reproducibility_summary ||
          finalReport?.environment_parity_assessment ||
          finalReport?.environment_fingerprint
          ? finalReport
          : runtime,
      ),
    [finalReport, runtime],
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
  const deliveryDecisionSummary = useMemo(
    () =>
      buildSubmarineDeliveryDecisionSummary(
        finalReport?.delivery_decision_summary
          ? finalReport
          : runtime?.delivery_decision_summary || runtime?.decision_status
            ? {
                delivery_decision_summary: runtime?.delivery_decision_summary,
                decision_status: runtime?.decision_status,
              }
            : null,
      ),
    [finalReport, runtime?.decision_status, runtime?.delivery_decision_summary],
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
  const customVariantLineageItems = useMemo(() => {
    const lines: string[] = [];
    const seen = new Set<string>();

    for (const item of experimentCompareSummary?.comparisons ?? []) {
      if (!item.isCustomVariant) {
        continue;
      }
      const line = [
        item.lineageLabel,
        item.candidateRunId,
        `compare target ${item.compareTargetRunId}`,
        item.candidateExecutionStatusLabel,
        item.compareStatusLabel,
      ].join(" | ");
      if (!seen.has(line)) {
        seen.add(line);
        lines.push(line);
      }
    }

    for (const runId of experimentSummary?.missingCustomCompareEntryIds ?? []) {
      const line = `自定义变体 | ${runId.replace(/^custom:/, "")} | ${runId} | 待对比基线目标 | 对比待完成`;
      if (!seen.has(line)) {
        seen.add(line);
        lines.push(line);
      }
    }

    return lines;
  }, [
    experimentCompareSummary?.comparisons,
    experimentSummary?.missingCustomCompareEntryIds,
  ]);
  const scientificVerificationSummary = useMemo(
    () =>
      buildSubmarineScientificVerificationSummary(
        finalReport?.scientific_verification_assessment
          ? finalReport
          : runtime?.scientific_verification_assessment
            ? {
                scientific_verification_assessment:
                  runtime.scientific_verification_assessment,
              }
            : null,
      ),
    [finalReport, runtime?.scientific_verification_assessment],
  );
  const stabilityEvidenceSummary = useMemo(
    () =>
      buildSubmarineStabilityEvidenceSummary(
        finalReport?.stability_evidence
          ? finalReport
          : runtime?.stability_evidence || runtime?.stability_evidence_virtual_path
            ? {
                stability_evidence: runtime?.stability_evidence,
                stability_evidence_virtual_path:
                  runtime?.stability_evidence_virtual_path,
              }
            : null,
      ),
    [
      finalReport,
      runtime?.stability_evidence,
      runtime?.stability_evidence_virtual_path,
    ],
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
        nextRecommendedStage: runtime?.next_recommended_stage,
      }),
    [
      runtime?.current_stage,
      runtime?.execution_plan,
      runtime?.next_recommended_stage,
    ],
  );
  const timelineEvents = runtime?.activity_timeline ?? [];
  const openArtifact = (artifactPath: string) => {
    select(artifactPath);
    setOpen(true);
  };

  const solverMetrics =
    finalReport?.solver_metrics ?? dispatchPayload?.solver_results ?? solverResults;
  const candidateCases =
    dispatchPayload?.candidate_cases ?? geometryPayload?.candidate_cases ?? [];
  const selectedCase =
    dispatchPayload?.selected_case ??
    candidateCases.find((item) => item.case_id === runtime?.selected_case_id) ??
    null;
  const geometryFindings =
    runtime?.geometry_findings ??
    dispatchPayload?.geometry_findings ??
    geometryPayload?.geometry_findings ??
    [];
  const scaleAssessment =
    runtime?.scale_assessment ??
    dispatchPayload?.scale_assessment ??
    geometryPayload?.scale_assessment ??
    null;
  const referenceValueSuggestions =
    runtime?.reference_value_suggestions ??
    dispatchPayload?.reference_value_suggestions ??
    geometryPayload?.reference_value_suggestions ??
    [];
  const calculationPlanDraft =
    runtime?.calculation_plan ??
    dispatchPayload?.calculation_plan ??
    activeDesignBrief?.calculation_plan ??
    geometryPayload?.calculation_plan ??
    [];
  const requiresImmediateConfirmation = Boolean(
    runtime?.requires_immediate_confirmation ??
      dispatchPayload?.requires_immediate_confirmation ??
      geometryPayload?.requires_immediate_confirmation,
  );
  const geometryClarificationRequired = Boolean(
    runtime?.clarification_required ??
      dispatchPayload?.clarification_required ??
      geometryPayload?.clarification_required,
  );
  const selectedCaseProvenance =
    finalReport?.selected_case_provenance_summary ??
    dispatchPayload?.selected_case_provenance_summary ??
    (selectedCase
      ? {
          case_id: selectedCase.case_id,
          title: selectedCase.title,
          source_label: selectedCase.source_label ?? null,
          source_url: selectedCase.source_url ?? null,
          source_type: selectedCase.source_type ?? null,
          applicability_conditions: selectedCase.applicability_conditions ?? [],
          confidence_note: selectedCase.confidence_note ?? null,
          is_placeholder: selectedCase.is_placeholder ?? false,
          evidence_gap_note: selectedCase.evidence_gap_note ?? null,
          acceptance_profile_summary_zh:
            selectedCase.acceptance_profile_summary_zh ?? null,
          benchmark_metric_ids: selectedCase.benchmark_metric_ids ?? [],
        }
      : null);
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
        outputDelivery: outputDeliverySummary,
        figureDelivery: figureDeliverySummary,
        artifactPaths: submarineArtifacts,
      }),
    [
      designBriefSummary?.requestedOutputs,
      figureDeliverySummary,
      outputDeliverySummary,
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
              潜艇 CFD 工作台
            </div>
            <div>
              <CardTitle className="text-xl">潜艇任务运行面板</CardTitle>
              <CardDescription className="mt-1 max-w-3xl text-sm leading-6">
                {localizeWorkspaceDisplayText(
                  finalReport?.summary_zh ??
                    designBrief?.summary_zh ??
                    dispatchPayload?.summary_zh ??
                    geometryPayload?.summary_zh ??
                    runtime?.task_summary ??
                    "当前线程已经进入潜艇 CFD 专业流程。这里集中展示方案简报、运行状态和交付产物。",
                )}
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
          <MetricTile icon={ActivityIcon} label="运行状态" value={formatRuntimeStatus(runtime?.stage_status ?? "draft")} note={`下一阶段：${formatStage(runtime?.next_recommended_stage)}`} />
          <MetricTile
            icon={BoxesIcon}
            label="案例模板"
            value={localizeWorkspaceDisplayText(
              selectedCase?.title ?? runtime?.selected_case_id ?? "待匹配",
            )}
            note={runtime?.geometry_family ?? designBrief?.geometry_family_hint ?? "几何家族待识别"}
          />
          <MetricTile icon={GaugeIcon} label="阻力系数 Cd" value={formatNumeric(cd, 6)} note={`最终时间步：${formatNumeric(solverMetrics?.final_time_seconds, 0, " s")}`} />
          <MetricTile icon={WavesIcon} label="总阻力 Fx" value={formatNumeric(dragForceX, 4, " N")} note={`产物：${submarineArtifacts.length}`} />
        </div>

        <QuickAccess onJump={(id) => document.getElementById(sectionElementId(id))?.scrollIntoView({ behavior: "smooth", block: "start" })} />

        <InfoPanel id={sectionElementId("runtime")} title="任务与运行上下文" kicker="运行面板">
          <RuntimeContextGrid
            entries={[
              {
                label: "任务摘要",
                value: localizeWorkspaceDisplayText(
                  runtime?.task_summary ?? designBrief?.task_description ?? "待生成",
                ),
              },
              { label: "几何文件", value: runtime?.geometry_virtual_path ?? designBrief?.geometry_virtual_path ?? "待上传" },
              { label: "几何家族", value: runtime?.geometry_family ?? designBrief?.geometry_family_hint ?? "待识别" },
              {
                label: "研究批准",
                value:
                  designBriefSummary?.precomputeApprovalLabel ??
                  (runtime?.review_status === "needs_user_confirmation"
                    ? "待研究人员确认"
                    : "已就绪"),
              },
              {
                label: "计算计划",
                value: `${designBriefSummary?.calculationPlan.length ?? calculationPlanDraft.length} 项`,
              },
              { label: "当前报告", value: runtime?.report_virtual_path ?? designBriefJson ?? "待生成" },
              { label: "工作区案例目录", value: runtime?.workspace_case_dir_virtual_path ?? "待生成" },
              { label: "运行脚本与后处理", value: runtime?.run_script_virtual_path ?? solverMetrics?.workspace_postprocess_virtual_path ?? "待生成" },
              { label: "派发请求", value: dispatchJson ?? "待生成" },
              {
                label: "执行日志",
                value:
                  executionLogPath ??
                  (runtime?.current_stage === "solver-dispatch" ||
                  runtime?.current_stage === "result-reporting"
                    ? "当前还没有写入执行日志"
                    : "本轮尚未执行"),
              },
              { label: "求解结果数据", value: solverResultsJson ?? "待生成" },
              {
                label: "求解结果说明文档",
                value: solverResultsMarkdownPath ?? "待生成",
              },
            ]}
          />
          <LabeledList
            title="运行时输出交付"
            items={outputDeliverySummary.map((item) =>
              item.specSummary !== "--"
                ? `${localizeWorkspaceDisplayText(item.label)} | ${localizeWorkspaceDisplayText(item.deliveryStatus)} | ${localizeWorkspaceDisplayText(item.specSummary)} | ${localizeWorkspaceDisplayText(item.detail)}`
                : `${localizeWorkspaceDisplayText(item.label)} | ${localizeWorkspaceDisplayText(item.deliveryStatus)} | ${localizeWorkspaceDisplayText(item.detail)}`,
            )}
            emptyText="当前还没有求解输出的显式交付情况。"
          />
        </InfoPanel>

        <InfoPanel id={sectionElementId("brief")} title="CFD 设计简报" kicker="方案简报">
          {designBriefSummary ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <KeyValue label="方案状态" value={designBriefSummary.confirmationStatusLabel} />
                <KeyValue label="待确认项" value={`${designBriefSummary.openQuestions.length} 项`} />
                <KeyValue label="预期交付物" value={`${designBriefSummary.expectedOutputs.length} 项`} />
                <KeyValue label="下一步" value={formatStage(runtime?.next_recommended_stage ?? designBrief?.next_recommended_stage)} />
              </div>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <KeyValue
                  label="研究批准"
                  value={designBriefSummary.precomputeApprovalLabel}
                />
                <KeyValue
                  label="计算计划"
                  value={`${designBriefSummary.calculationPlan.length} 项`}
                />
                <KeyValue
                  label="待确认计划项"
                  value={`${designBriefSummary.pendingCalculationPlanCount} 项`}
                />
                <KeyValue
                  label="立即澄清项"
                  value={`${designBriefSummary.immediateClarificationCount} 项`}
                />
                <StatusTile
                  icon={BoxesIcon}
                  label="研究批准"
                  value={
                    designBriefSummary?.precomputeApprovalLabel ??
                    (runtime?.review_status === "needs_user_confirmation"
                      ? "待研究人员确认"
                      : "已就绪")
                  }
                  note={
                    runtime?.review_status === "needs_user_confirmation"
                      ? "预计算审批仍未完成。这个关口会阻止求解执行，并且与求解后的科研结论级别判断相互独立。"
                      : "当前没有记录尚未解决的预计算审批阻断项。"
                  }
                />
              </div>
              {designBriefSummary.requirementPairs.length > 0 && (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {designBriefSummary.requirementPairs.map((item) => (
                    <KeyValue key={item.label} label={item.label} value={item.value} />
                  ))}
                </div>
              )}
              <div className="grid gap-4 xl:grid-cols-3">
                <LabeledList title="预期交付物" items={designBriefSummary.expectedOutputs.map((item) => localizeWorkspaceDisplayText(item))} emptyText="Claude Code 还没有整理出明确的交付清单。" />
                <LabeledList title="用户约束" items={designBriefSummary.userConstraints.map((item) => localizeWorkspaceDisplayText(item))} emptyText="当前还没有明确的额外约束。" />
                <LabeledList title="待确认项" items={designBriefSummary.openQuestions.map((item) => localizeWorkspaceDisplayText(item))} emptyText="当前方案已经没有待确认项。" />
              </div>
              {designBriefSummary.calculationPlan.length > 0 ? (
                <div className="rounded-xl border bg-background/70 p-4">
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-medium text-foreground">
                        计算计划审阅
                      </div>
                      <div className="text-xs text-muted-foreground">
                        这些预计算假设仍需要研究人员审阅。这个批准门槛与求解后的结论级别判断是分开的。
                      </div>
                    </div>
                    <Badge variant="outline">
                      {designBriefSummary.calculationPlan.length} 项
                    </Badge>
                  </div>
                  <div className="grid gap-3 xl:grid-cols-2">
                    {designBriefSummary.calculationPlan.map((item) => (
                      <div
                        key={item.itemId}
                        className={cn(
                          "rounded-xl border p-4",
                          item.requiresImmediateConfirmation
                            ? "border-amber-200 bg-amber-50/70"
                            : item.approvalState === "researcher_confirmed"
                              ? "border-emerald-200 bg-emerald-50/70"
                              : "border-sky-200 bg-sky-50/70",
                        )}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <div className="text-sm font-medium text-foreground">
                              {item.label}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {item.category} | {item.originLabel}
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {item.requiresImmediateConfirmation ? (
                              <Badge variant="secondary">
                                立即澄清
                              </Badge>
                            ) : null}
                            <Badge variant="outline">{item.approvalStateLabel}</Badge>
                          </div>
                        </div>
                        <div className="mt-3 grid gap-3 md:grid-cols-2">
                          <KeyValue label="建议值" value={item.proposedValue} />
                          <KeyValue label="置信度" value={item.confidenceLabel} />
                          <KeyValue label="来源" value={item.sourceLabel} />
                          <KeyValue label="来源链接" value={item.sourceUrl} />
                        </div>
                        <div className="mt-3 grid gap-3 xl:grid-cols-3">
                          <LabeledList
                            title="适用条件"
                            items={item.applicabilityConditions}
                            emptyText="当前没有记录明确的适用条件。"
                          />
                          <LabeledList
                            title="证据缺口"
                            items={
                              item.evidenceGapNote !== "--"
                                ? [item.evidenceGapNote]
                                : []
                            }
                            emptyText="当前没有记录证据缺口说明。"
                          />
                          <LabeledList
                            title="研究人员备注"
                            items={
                              item.researcherNote !== "--"
                                ? [item.researcherNote]
                                : []
                            }
                            emptyText="当前还没有研究人员备注。"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
                <div className="rounded-xl border bg-background/70 p-4">
                  <div className="mb-2 text-sm font-medium text-foreground">
                    请求输出
                  </div>
                  <LabeledList
                    title="请求输出"
                    items={designBriefSummary.requestedOutputs.map((item) =>
                      item.specSummary !== "--"
                        ? `${localizeWorkspaceDisplayText(item.label)} | ${localizeWorkspaceDisplayText(item.supportLevel)} | ${localizeWorkspaceDisplayText(item.requestedLabel)} | ${localizeWorkspaceDisplayText(item.specSummary)}`
                        : `${localizeWorkspaceDisplayText(item.label)} | ${localizeWorkspaceDisplayText(item.supportLevel)} | ${localizeWorkspaceDisplayText(item.requestedLabel)}`,
                    )}
                  emptyText="Claude Code 还没有把用户需求收敛成结构化输出合同。"
                />
              </div>
                <div className="rounded-xl border bg-background/70 p-4">
                  <div className="mb-2 text-sm font-medium text-foreground">
                    科研验证要求
                  </div>
                  <LabeledList
                    title="科研验证要求"
                    items={designBriefSummary.scientificVerificationRequirements.map(
                      (item) =>
                        item.detail !== "--"
                          ? `${localizeWorkspaceDisplayText(item.label)} | ${localizeWorkspaceDisplayText(item.checkType)} | ${localizeWorkspaceDisplayText(item.detail)}`
                          : `${localizeWorkspaceDisplayText(item.label)} | ${localizeWorkspaceDisplayText(item.checkType)}`,
                    )}
                    emptyText="当前设计简报还没有列出面向科研的验证要求。"
                  />
                </div>
              <OutlineList items={executionOutline} />
            </div>
          ) : (
            <EmptyState text="Claude Code 与用户的当前讨论还没有沉淀为结构化 CFD 设计简报。生成设计简报后，这里会展示任务目标、待确认项、交付物和执行分工。" />
          )}
        </InfoPanel>

        <InfoPanel id={sectionElementId("timeline")} title="执行时间线" kicker="时间线">
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
          <EmptyState text="当前线程还没有沉淀执行时间线。随着 Claude Code 修订方案、几何预检、求解派发和结果报告推进，这里会持续追加阶段记录。" />
          )}
        </InfoPanel>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
          <div className="grid gap-4">
            <InfoPanel id={sectionElementId("health")} title="求解健康状态" kicker="健康">
              <div className="grid gap-3 md:grid-cols-3">
                <StatusTile icon={ShipWheelIcon} label="几何就绪" value={dispatchPayload?.requires_geometry_conversion ? "待转换" : runtime?.geometry_virtual_path ? "可求解" : "待上传"} note={dispatchPayload?.requires_geometry_conversion ? "当前上传格式需要先转换成 STL。" : runtime?.geometry_virtual_path ? "当前线程已经具备几何输入。" : "当前线程还没有潜艇几何输入。"} />
                <StatusTile icon={RadarIcon} label="求解执行" value={solverMetrics?.solver_completed ? "已完成" : runtime?.current_stage === "solver-dispatch" ? "执行中" : "待执行"} note={solverMetrics?.solver_completed ? `最终时间步 ${formatNumeric(solverMetrics.final_time_seconds, 0, " s")}` : runtime?.current_stage === "solver-dispatch" ? formatRuntimeStatus(runtime?.stage_status) : "完成几何预检与案例确认后，可进入真实 OpenFOAM 求解。"} />
                <StatusTile
                  icon={Layers2Icon}
                  label="主管复核"
                  value={formatReviewStatus(runtime?.review_status)}
                  note={
                    scientificGateSummary
                        ? `科研门槛：${scientificGateSummary.gateStatusLabel}；结论级别：${scientificGateSummary.allowedClaimLevelLabel}；下一阶段：${formatStage(runtime?.next_recommended_stage)}`
                      : `下一阶段：${formatStage(runtime?.next_recommended_stage)}`
                  }
                />
              </div>
              {reportOverviewSummary ||
              deliveryHighlights ||
              conclusionSectionsSummary.length > 0 ||
              evidenceIndexSummary ? (
                <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-foreground">
                        结论优先交付
                      </div>
                      <div className="text-xs text-muted-foreground">
                        当前工作台会同步展示最终报告结构以及与产物的关联关系。
                      </div>
                    </div>
                    {reportOverviewSummary ? (
                      <Badge variant="outline" className="bg-background/80">
                        {reportOverviewSummary.reviewStatusLabel}
                      </Badge>
                    ) : null}
                  </div>
                  {reportOverviewSummary ? (
                    <>
                      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                        <KeyValue
                          label="允许结论级别"
                          value={reportOverviewSummary.allowedClaimLevelLabel}
                        />
                        <KeyValue
                          label="复核状态"
                          value={reportOverviewSummary.reviewStatusLabel}
                        />
                        <KeyValue
                          label="可复现性"
                          value={
                            reportOverviewSummary.reproducibilityStatusLabel
                          }
                        />
                        <KeyValue
                          label="证据分组"
                          value={
                            evidenceIndexSummary
                              ? `${evidenceIndexSummary.groupCount}`
                              : "--"
                          }
                        />
                      </div>
                      <div className="rounded-xl border bg-muted/20 p-4">
                        <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                          当前结论
                        </div>
                        <div className="mt-2 text-sm leading-6 text-foreground">
                          {reportOverviewSummary.currentConclusion}
                        </div>
                        <div className="mt-4 text-xs uppercase tracking-[0.16em] text-muted-foreground">
                          推荐下一步
                        </div>
                        <div className="mt-1 text-sm leading-6 text-muted-foreground">
                          {reportOverviewSummary.recommendedNextStep}
                        </div>
                      </div>
                    </>
                  ) : null}
                  {deliveryHighlights ? (
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="关键指标"
                        items={deliveryHighlights.metricLines}
                        emptyText="当前没有写入关键指标摘要。"
                      />
                      <LabeledList
                        title="代表图表"
                        items={deliveryHighlights.figureTitles}
                        emptyText="当前没有写入代表图表。"
                      />
                      <ArtifactPathList
                        title="高亮产物"
                        paths={deliveryHighlights.highlightArtifactPaths}
                        emptyText="当前没有高亮产物链接。"
                        onOpenArtifact={openArtifact}
                      />
                    </div>
                  ) : null}
                  {conclusionSectionsSummary.length > 0 ? (
                    <div className="space-y-3">
                      {conclusionSectionsSummary.map((section) => (
                        <div
                          key={section.conclusionId}
                          className="rounded-xl border bg-muted/20 p-4"
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="bg-background/80">
                              {section.claimLevelLabel}
                            </Badge>
                            <span className="text-sm font-medium text-foreground">
                              {section.title}
                            </span>
                          </div>
                          <div className="mt-3 text-sm leading-6 text-foreground">
                            {section.summary}
                          </div>
                          <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                            <KeyValue
                              label="结论级别"
                              value={section.claimLevelLabel}
                            />
                            <KeyValue
                              label="可信度"
                              value={section.confidenceLabel}
                            />
                            <KeyValue
                              label="来源数"
                              value={`${section.inlineSourceRefs.length}`}
                            />
                            <KeyValue
                              label="产物数"
                              value={`${section.artifactPaths.length}`}
                            />
                          </div>
                          <div className="mt-3 grid gap-4 xl:grid-cols-3">
                            <LabeledList
                              title="来源"
                              items={section.inlineSourceRefs}
                              emptyText="当前没有内联来源引用。"
                            />
                            <LabeledList
                              title="证据缺口"
                              items={section.evidenceGapNotes}
                              emptyText="当前没有记录证据缺口。"
                            />
                            <ArtifactPathList
                              title="关联产物"
                              paths={section.artifactPaths}
                              emptyText="当前没有关联产物。"
                              onOpenArtifact={openArtifact}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {evidenceIndexSummary ? (
                    <div className="space-y-3">
                      {evidenceIndexSummary.groups.map((group) => (
                        <div
                          key={group.groupId}
                          className="rounded-xl border bg-muted/20 p-4"
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="bg-background/80">
                              {group.groupId}
                            </Badge>
                            <span className="text-sm font-medium text-foreground">
                              {group.groupTitle}
                            </span>
                          </div>
                          <div className="mt-3 grid gap-4 xl:grid-cols-2">
                            <ArtifactPathList
                              title="证据产物"
                              paths={group.artifactPaths}
                              emptyText="当前没有证据产物链接。"
                              onOpenArtifact={openArtifact}
                            />
                            <ArtifactPathList
                              title="溯源清单"
                              paths={
                                group.provenanceManifestPath !== "--"
                                  ? [group.provenanceManifestPath]
                                  : []
                              }
                                emptyText="当前没有溯源清单链接。"
                                onOpenArtifact={openArtifact}
                              />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}
              {!acceptanceSummary && outputDeliverySummary.length > 0 ? (
                <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                  <div className="grid gap-3 md:grid-cols-3">
                    <KeyValue label="请求输出" value={`${outputDeliverySummary.length} 项`} />
                    <KeyValue
                      label="已交付"
                      value={`${outputDeliverySummary.filter((item) => item.deliveryStatus === "delivered").length} 项`}
                    />
                    <KeyValue
                      label="待交付 / 已规划"
                      value={`${outputDeliverySummary.filter((item) => item.deliveryStatus === "pending" || item.deliveryStatus === "planned").length} 项`}
                    />
                  </div>
                  <LabeledList
                    title="运行时输出交付"
                    items={outputDeliverySummary.map((item) =>
                      item.specSummary !== "--"
                        ? `${item.label} | ${item.deliveryStatus} | ${item.specSummary} | ${item.detail}`
                        : `${item.label} | ${item.deliveryStatus} | ${item.detail}`,
                    )}
                    emptyText="当前还没有记录请求输出的交付状态。"
                  />
                </div>
              ) : null}
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
                        title="基准对比"
                        items={acceptanceSummary.benchmarkComparisons.map((item) =>
                          formatSubmarineBenchmarkComparisonSummaryLine(item),
                        )}
                        emptyText="当前没有命中的基准对比。"
                      />
                  </div>
                  <LabeledList
                    title="输出交付"
                    items={acceptanceSummary.outputDelivery.map((item) =>
                      item.specSummary !== "--"
                        ? `${item.label} | ${item.deliveryStatus} | ${item.specSummary} | ${item.detail}`
                        : `${item.label} | ${item.deliveryStatus} | ${item.detail}`,
                    )}
                    emptyText="当前还没有记录请求输出的交付状态。"
                  />
                </div>
                ) : null}
                {deliveryDecisionSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border border-sky-200 bg-sky-50/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="决策状态"
                        value={deliveryDecisionSummary.decisionStatusLabel}
                      />
                      <KeyValue
                        label="推荐选项"
                        value={deliveryDecisionSummary.recommendedOptionLabel}
                      />
                      <KeyValue
                        label="决策问题"
                        value={deliveryDecisionSummary.question}
                      />
                      <KeyValue
                        label="聊天提示"
                        value={deliveryDecisionSummary.chatPrompt}
                      />
                    </div>
                    <div className="rounded-xl border border-sky-200 bg-white/80 px-4 py-3 text-sm font-medium text-sky-950">
                      请在聊天中确认下一步。
                    </div>
                    {deliveryDecisionSummary.options.length > 0 ? (
                      <div className="space-y-3">
                        {deliveryDecisionSummary.options.map((item) => (
                          <div
                            key={item.optionId}
                            className="rounded-xl border bg-background/80 p-4"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="outline" className="bg-white/80">
                                {item.followupKindLabel}
                              </Badge>
                              {item.optionId ===
                              deliveryDecisionSummary.recommendedOptionId ? (
                                <Badge variant="secondary">推荐</Badge>
                              ) : null}
                              <span className="text-sm font-medium text-foreground">
                                {item.label}
                              </span>
                            </div>
                            <div className="mt-2 text-sm leading-6 text-muted-foreground">
                              {item.summary}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="阻塞上下文"
                        items={deliveryDecisionSummary.blockingReasons}
                        emptyText="当前没有记录阻塞上下文。"
                      />
                      <LabeledList
                        title="建议备注"
                        items={deliveryDecisionSummary.advisoryNotes}
                        emptyText="当前没有记录建议备注。"
                      />
                      <ArtifactPathList
                        title="决策产物"
                        paths={deliveryDecisionSummary.artifactPaths}
                        emptyText="当前没有记录决策产物。"
                        onOpenArtifact={openArtifact}
                      />
                    </div>
                  </div>
                ) : null}
                {scientificGateSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                      <KeyValue
                        label="科研门槛"
                        value={scientificGateSummary.gateStatusLabel}
                      />
                      <KeyValue
                        label="允许结论"
                        value={scientificGateSummary.allowedClaimLevelLabel}
                      />
                      <KeyValue
                        label="证据就绪度"
                        value={scientificGateSummary.sourceReadinessLabel}
                      />
                      <KeyValue
                        label="建议阶段"
                        value={scientificGateSummary.recommendedStageLabel}
                      />
                      <KeyValue
                        label="补救阶段"
                        value={scientificGateSummary.remediationStageLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="阻塞原因"
                        items={scientificGateSummary.blockingReasons}
                        emptyText="当前没有记录科研复核阻塞项。"
                      />
                      <LabeledList
                        title="建议备注"
                        items={scientificGateSummary.advisoryNotes}
                        emptyText="当前没有记录科研复核建议。"
                      />
                      <LabeledList
                        title="门槛产物"
                        items={scientificGateSummary.artifactPaths}
                        emptyText="当前没有记录科研门槛产物。"
                      />
                    </div>
                  </div>
                ) : null}
                {reproducibilitySummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="清单文件"
                        value={reproducibilitySummary.manifestPath}
                      />
                      <KeyValue
                        label="环境配置"
                        value={reproducibilitySummary.profileLabel}
                      />
                      <KeyValue
                        label="环境一致性"
                        value={reproducibilitySummary.parityStatusLabel}
                      />
                      <KeyValue
                        label="可复现性"
                        value={
                          reproducibilitySummary.reproducibilityStatusLabel
                        }
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-2">
                      <LabeledList
                        title="漂移原因"
                        items={reproducibilitySummary.driftReasons}
                        emptyText="当前没有记录运行环境一致性漂移原因。"
                      />
                      <LabeledList
                        title="恢复建议"
                        items={reproducibilitySummary.recoveryGuidance}
                        emptyText="当前没有记录可复现性恢复建议。"
                      />
                    </div>
                  </div>
                ) : null}
                {researchEvidenceSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                      <KeyValue
                        label="科研准备度"
                        value={researchEvidenceSummary.readinessLabel}
                      />
                      <KeyValue
                        label="验证状态"
                        value={researchEvidenceSummary.verificationStatusLabel}
                      />
                      <KeyValue
                        label="校核状态"
                        value={researchEvidenceSummary.validationStatusLabel}
                      />
                      <KeyValue
                        label="溯源状态"
                        value={researchEvidenceSummary.provenanceStatusLabel}
                      />
                      <KeyValue
                        label="可信度"
                        value={researchEvidenceSummary.confidenceLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="阻断问题"
                        items={researchEvidenceSummary.blockingIssues}
                        emptyText="当前没有科研证据阻断问题。"
                      />
                      <LabeledList
                        title="已通过证据"
                        items={researchEvidenceSummary.passedEvidence}
                        emptyText="当前还没有记录已通过的科研证据。"
                      />
                      <LabeledList
                        title="证据缺口"
                        items={researchEvidenceSummary.evidenceGaps}
                        emptyText="当前没有科研证据缺口。"
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="基准亮点"
                        items={researchEvidenceSummary.benchmarkHighlights}
                        emptyText="当前没有基准亮点记录。"
                      />
                      <LabeledList
                        title="溯源亮点"
                        items={researchEvidenceSummary.provenanceHighlights}
                        emptyText="当前没有溯源亮点记录。"
                      />
                      <LabeledList
                        title="证据产物"
                        items={researchEvidenceSummary.artifactPaths}
                        emptyText="当前没有记录研究证据产物。"
                      />
                    </div>
                  </div>
                ) : null}
                {experimentSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
                      <KeyValue
                        label="实验登记"
                        value={experimentSummary.experimentStatusLabel}
                      />
                      <KeyValue
                        label="流程状态"
                        value={experimentSummary.workflowStatusLabel}
                      />
                      <KeyValue
                        label="实验 ID"
                        value={experimentSummary.experimentId}
                      />
                      <KeyValue
                        label="基线运行"
                        value={experimentSummary.baselineRunId}
                      />
                      <KeyValue
                        label="运行数量"
                        value={`${experimentSummary.runCount}`}
                      />
                      <KeyValue
                        label="对比数量"
                        value={`${experimentSummary.compareCount}`}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="实验产物"
                        items={[
                          experimentSummary.manifestPath,
                          ...(experimentSummary.studyManifestPath !== "--"
                            ? [experimentSummary.studyManifestPath]
                            : []),
                          ...(experimentSummary.comparePath !== "--"
                            ? [experimentSummary.comparePath]
                            : []),
                          ...experimentSummary.artifactPaths,
                        ]}
                        emptyText="当前还没有记录实验登记产物。"
                      />
                      <LabeledList
                        title="流程明细"
                        items={[
                          experimentSummary.workflowDetail,
                          ...experimentSummary.runStatusCountLines,
                          ...experimentSummary.compareStatusCountLines,
                        ]}
                        emptyText="当前还没有实验流程明细。"
                      />
                      <LabeledList
                        title="联动覆盖"
                        items={[
                          `status | ${experimentSummary.linkageStatus}`,
                          `issues | ${experimentSummary.linkageIssueCount}`,
                          ...experimentSummary.linkageIssues,
                          ...experimentSummary.missingVariantRunRecordIds.map(
                            (item) => `missing run-record | ${item}`,
                          ),
                          ...experimentSummary.missingCompareEntryIds.map(
                            (item) => `missing compare-entry | ${item}`,
                          ),
                        ]}
                        emptyText="当前没有实验联动问题。"
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="运行对比说明"
                        items={experimentSummary.compareNotes}
                        emptyText="当前还没有运行对比说明。"
                      />
                      <LabeledList
                        title="预期变体运行"
                        items={experimentSummary.expectedVariantRunIds}
                        emptyText="当前还没有预期科研变体运行。"
                      />
                      <LabeledList
                        title="待补齐变体缺口"
                        items={[
                          ...experimentSummary.plannedVariantRunIds.map(
                            (item) => `已规划 | ${item}`,
                          ),
                          ...experimentSummary.blockedVariantRunIds.map(
                            (item) => `已阻断 | ${item}`,
                          ),
                          ...experimentSummary.missingMetricsVariantRunIds.map(
                            (item) => `缺少指标 | ${item}`,
                          ),
                        ]}
                        emptyText="当前没有待补齐的实验流程缺口。"
                      />
                      <LabeledList
                        title="自定义变体沿袭"
                        items={customVariantLineageItems}
                        emptyText="当前没有自定义变体沿袭记录。"
                      />
                    </div>
                  </div>
                ) : null}
                {scientificRemediationSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="补救方案"
                        value={scientificRemediationSummary.planStatusLabel}
                      />
                      <KeyValue
                        label="当前结论级别"
                        value={scientificRemediationSummary.currentClaimLevelLabel}
                      />
                      <KeyValue
                        label="目标结论级别"
                        value={scientificRemediationSummary.targetClaimLevelLabel}
                      />
                      <KeyValue
                        label="推荐阶段"
                        value={scientificRemediationSummary.recommendedStageLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-2">
                      <LabeledList
                        title="补救产物"
                        items={scientificRemediationSummary.artifactPaths}
                        emptyText="当前还没有记录补救产物。"
                      />
                      <LabeledList
                        title="补救动作"
                        items={scientificRemediationSummary.actions.map(
                          (item) =>
                            `${item.title} | ${item.ownerStageLabel} | ${item.executionModeLabel} | ${item.statusLabel}`,
                        )}
                        emptyText="当前没有记录补救动作。"
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
                              <KeyValue label="动作 ID" value={item.actionId} />
                              <KeyValue label="负责阶段" value={item.ownerStageLabel} />
                              <KeyValue label="执行方式" value={item.executionModeLabel} />
                              <KeyValue label="优先级" value={item.priority} />
                            </div>
                            <div className="mt-3 grid gap-4 xl:grid-cols-2">
                              <LabeledList
                                title="动作摘要"
                                items={[item.summary, item.evidenceGap]}
                                emptyText="当前没有记录补救详情。"
                              />
                              <LabeledList
                                title="所需产物"
                                items={item.requiredArtifacts}
                                emptyText="当前没有记录所需补救产物。"
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
                        label="补救交接"
                        value={scientificRemediationHandoffSummary.handoffStatusLabel}
                      />
                      <KeyValue
                        label="建议动作"
                        value={scientificRemediationHandoffSummary.recommendedActionId}
                      />
                      <KeyValue
                        label="建议工具"
                        value={scientificRemediationHandoffSummary.toolName}
                      />
                      <KeyValue
                        label="原因"
                        value={scientificRemediationHandoffSummary.reason}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="交接产物"
                        items={scientificRemediationHandoffSummary.artifactPaths}
                        emptyText="当前还没有记录补救交接产物。"
                      />
                      <LabeledList
                        title="建议工具参数"
                        items={scientificRemediationHandoffSummary.toolArgs.map(
                          (item) => `${item.key} = ${item.value}`,
                        )}
                        emptyText="当前没有记录这次交接的工具参数。"
                      />
                      <LabeledList
                        title="人工跟进"
                        items={scientificRemediationHandoffSummary.manualActions.map(
                          (item) =>
                            `${item.title} | ${item.ownerStageLabel} | ${item.evidenceGap}`,
                        )}
                        emptyText="当前没有人工跟进行动。"
                      />
                    </div>
                    {scientificRemediationHandoffSummary.toolArgs.length > 0 ? (
                      <div className="space-y-3">
                        <div className="text-sm font-medium text-foreground">
                          建议工具契约
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
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                      <KeyValue
                        label="跟进条目"
                        value={`${scientificFollowupSummary.entryCount}`}
                      />
                      <KeyValue
                        label="最新结果"
                        value={scientificFollowupSummary.latestOutcomeLabel}
                      />
                      <KeyValue
                        label="最新交接"
                        value={scientificFollowupSummary.latestHandoffStatusLabel}
                      />
                      <KeyValue
                        label="最新类型"
                        value={scientificFollowupSummary.latestFollowupKindLabel}
                      />
                      <KeyValue
                        label="报告已刷新"
                        value={scientificFollowupSummary.reportRefreshedLabel}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="最新跟进约定"
                        items={[
                          `动作 | ${scientificFollowupSummary.latestRecommendedActionId}`,
                          `工具 | ${scientificFollowupSummary.latestToolName}`,
                          `派发 | ${scientificFollowupSummary.latestDispatchStageStatusLabel}`,
                        ]}
                        emptyText="当前没有记录跟进约定明细。"
                      />
                      <LabeledList
                        title="最新决策上下文"
                        items={[
                          `类型 | ${scientificFollowupSummary.latestFollowupKindLabel}`,
                          ...(scientificFollowupSummary.latestDecisionSummary !== "--"
                            ? [scientificFollowupSummary.latestDecisionSummary]
                            : []),
                        ]}
                        emptyText="当前没有记录跟进决策摘要。"
                      />
                      <LabeledList
                        title="触发来源 ID"
                        items={[
                          ...scientificFollowupSummary.latestSourceConclusionIds.map(
                            (item) => `结论 | ${item}`,
                          ),
                          ...scientificFollowupSummary.latestSourceEvidenceGapIds.map(
                            (item) => `证据缺口 | ${item}`,
                          ),
                        ]}
                        emptyText="当前没有记录来源结论或证据缺口 ID。"
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <ArtifactPathList
                        title="最新证据锚点"
                        paths={[
                          ...(scientificFollowupSummary.historyPath !== "--"
                            ? [scientificFollowupSummary.historyPath]
                            : []),
                          ...(scientificFollowupSummary.latestResultReportPath !== "--"
                            ? [scientificFollowupSummary.latestResultReportPath]
                            : []),
                          ...(scientificFollowupSummary.latestResultProvenanceManifestPath !==
                          "--"
                            ? [
                                scientificFollowupSummary.latestResultProvenanceManifestPath,
                              ]
                            : []),
                          ...(scientificFollowupSummary.latestResultHandoffPath !== "--"
                            ? [scientificFollowupSummary.latestResultHandoffPath]
                            : []),
                        ]}
                        emptyText="当前没有刷新后的报告或溯源锚点。"
                        onOpenArtifact={openArtifact}
                      />
                      <LabeledList
                        title="最新跟进备注"
                        items={scientificFollowupSummary.latestNotes}
                        emptyText="当前没有跟进备注。"
                      />
                      <ArtifactPathList
                        title="后续产物"
                        paths={scientificFollowupSummary.artifactPaths}
                        emptyText="当前没有记录后续产物。"
                        onOpenArtifact={openArtifact}
                      />
                    </div>
                  </div>
                ) : null}
                {experimentCompareSummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                      <KeyValue
                        label="实验对比"
                        value={`${experimentCompareSummary.compareCount}`}
                      />
                      <KeyValue
                        label="流程状态"
                        value={experimentCompareSummary.workflowStatusLabel}
                      />
                      <KeyValue
                        label="实验 ID"
                        value={experimentCompareSummary.experimentId}
                      />
                      <KeyValue
                        label="基线运行"
                        value={experimentCompareSummary.baselineRunId}
                      />
                      <KeyValue
                        label="对比产物"
                        value={experimentCompareSummary.comparePath}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-3">
                      <LabeledList
                        title="对比产物"
                        items={experimentCompareSummary.artifactPaths}
                        emptyText="当前还没有记录实验对比产物。"
                      />
                      <LabeledList
                        title="流程覆盖"
                        items={[
                          ...experimentCompareSummary.compareStatusCountLines,
                          ...experimentCompareSummary.plannedCandidateRunIds.map(
                            (item) => `已规划 | ${item}`,
                          ),
                          ...experimentCompareSummary.completedCandidateRunIds.map(
                            (item) => `已完成 | ${item}`,
                          ),
                          ...experimentCompareSummary.blockedCandidateRunIds.map(
                            (item) => `已阻塞 | ${item}`,
                          ),
                          ...experimentCompareSummary.missingMetricsCandidateRunIds.map(
                            (item) => `缺少指标 | ${item}`,
                          ),
                        ]}
                        emptyText="当前还没有记录实验对比流程详情。"
                      />
                      <LabeledList
                        title="已对比运行"
                        items={experimentCompareSummary.comparisons.map(
                          (item) =>
                            `${item.compareTargetRunId} -> ${item.candidateRunId} | ${item.compareStatusLabel} | ${item.candidateExecutionStatusLabel} | ${item.studyLabel}`,
                        )}
                        emptyText="当前还没有记录实验对比项。"
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
                                {item.compareTargetRunId}
                                {" -> "}
                                {item.candidateRunId}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {item.lineageLabel}
                              </span>
                            </div>
                            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                              <KeyValue
                                label="对比目标"
                                value={item.compareTargetRunId}
                              />
                              <KeyValue label="研究类型" value={item.studyLabel} />
                              <KeyValue label="变体" value={item.variantLabel} />
                              <KeyValue label="状态" value={item.compareStatusLabel} />
                              <KeyValue
                                 label="候选运行状态"
                                value={item.candidateExecutionStatusLabel}
                              />
                            </div>
                            <div className="mt-3 grid gap-4 xl:grid-cols-2">
                              <LabeledList
                                title="指标差值"
                                items={
                                  item.metricDeltaLines.length > 0
                                    ? item.metricDeltaLines
                                    : [item.notes]
                                }
                                emptyText="当前没有记录对比指标差值。"
                              />
                              <LabeledList
                                title="比较产物"
                                items={item.artifactPaths}
                                emptyText="当前没有记录比较产物。"
                              />
                            </div>
                            <LabeledList
                              title="比较备注"
                              items={[item.notes]}
                              emptyText="当前没有记录比较备注。"
                            />
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {scientificStudySummary ? (
                  <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="科学研究"
                        value={scientificStudySummary.executionStatusLabel}
                      />
                      <KeyValue
                        label="流程状态"
                        value={scientificStudySummary.workflowStatusLabel}
                      />
                      <KeyValue
                        label="研究数量"
                        value={`${scientificStudySummary.studies.length}`}
                      />
                      <KeyValue
                        label="研究清单"
                        value={scientificStudySummary.manifestPath}
                      />
                    </div>
                    <div className="grid gap-4 xl:grid-cols-2">
                      <LabeledList
                        title="流程概览"
                        items={[
                          ...scientificStudySummary.studyStatusCountLines,
                          ...scientificStudySummary.studies.map(
                            (item) =>
                              `${item.summaryLabel} | ${item.workflowStatusLabel} | ${item.studyExecutionStatusLabel} | ${item.verificationStatus}`,
                          ),
                        ]}
                        emptyText="当前还没有可用的科学研究流程详情。"
                      />
                      <LabeledList
                        title="研究产物"
                        items={scientificStudySummary.artifactPaths}
                        emptyText="当前还没有记录科学研究产物。"
                      />
                    </div>
                    {scientificStudySummary.studies.length > 0 ? (
                      <div className="space-y-3">
                        {scientificStudySummary.studies.map((item) => (
                          <div
                            key={item.studyType}
                            className="rounded-xl border bg-muted/20 p-4"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="outline" className="bg-background/80">
                                {item.workflowStatusLabel}
                              </Badge>
                              <span className="text-sm font-medium text-foreground">
                                {item.summaryLabel}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {item.monitoredQuantity}
                              </span>
                            </div>
                            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                              <KeyValue
                                label="执行状态"
                                value={item.studyExecutionStatusLabel}
                              />
                              <KeyValue
                                label="验证状态"
                                value={item.verificationStatus}
                              />
                              <KeyValue
                                label="变体数量"
                                value={`${item.variantCount}`}
                              />
                              <KeyValue
                                label="监测量"
                                value={item.monitoredQuantity}
                              />
                            </div>
                            <div className="mt-3 grid gap-4 xl:grid-cols-3">
                              <LabeledList
                                title="流程明细"
                                items={[
                                  item.workflowDetail,
                                  ...item.variantStatusCountLines,
                                  ...item.compareStatusCountLines,
                                  item.verificationDetail,
                                ]}
                                emptyText="当前没有研究流程明细。"
                              />
                              <LabeledList
                                title="预期 / 待处理运行"
                                items={[
                                  ...item.expectedVariantRunIds.map(
                                    (runId) => `预期 | ${runId}`,
                                  ),
                                  ...item.plannedVariantRunIds.map(
                                    (runId) => `已规划 | ${runId}`,
                                  ),
                                  ...item.inProgressVariantRunIds.map(
                                    (runId) => `运行中 | ${runId}`,
                                  ),
                                  ...item.blockedVariantRunIds.map(
                                    (runId) => `已阻断 | ${runId}`,
                                  ),
                                ]}
                                emptyText="当前没有待处理的研究运行。"
                              />
                              <LabeledList
                                title="已完成 / 对比覆盖"
                                items={[
                                  ...item.completedVariantRunIds.map(
                                    (runId) => `已完成 | ${runId}`,
                                  ),
                                  ...item.plannedCompareVariantRunIds.map(
                                    (runId) => `对比已规划 | ${runId}`,
                                  ),
                                  ...item.completedCompareVariantRunIds.map(
                                    (runId) => `对比已完成 | ${runId}`,
                                  ),
                                  ...item.blockedCompareVariantRunIds.map(
                                    (runId) => `对比已阻塞 | ${runId}`,
                                  ),
                                  ...item.missingMetricsVariantRunIds.map(
                                    (runId) => `缺少指标 | ${runId}`,
                                  ),
                                ]}
                                emptyText="暂未记录已完成运行或对比覆盖明细。"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              {stabilityEvidenceSummary ? (
                <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <KeyValue
                      label="稳定性证据"
                      value={stabilityEvidenceSummary.statusLabel}
                    />
                    <KeyValue
                      label="最终最大残差"
                      value={stabilityEvidenceSummary.residualMaxFinalValue}
                    />
                    <KeyValue
                      label="尾段系数"
                      value={stabilityEvidenceSummary.tailCoefficientLabel}
                    />
                    <KeyValue
                      label="尾段波动范围"
                      value={stabilityEvidenceSummary.tailSpreadLabel}
                    />
                  </div>
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    <KeyValue
                      label="尾段稳定性"
                      value={stabilityEvidenceSummary.tailStatusLabel}
                    />
                    <KeyValue
                      label="尾段采样数"
                      value={stabilityEvidenceSummary.tailSampleCountLabel}
                    />
                    <KeyValue
                      label="求解结果来源"
                      value={stabilityEvidenceSummary.solverResultsPath}
                    />
                  </div>
                  <LabeledList
                    title="稳定性摘要"
                    items={[
                      stabilityEvidenceSummary.summary,
                      stabilityEvidenceSummary.artifactPath,
                    ]}
                    emptyText="暂未提供结构化稳定性摘要。"
                  />
                  <div className="grid gap-4 xl:grid-cols-3">
                    <LabeledList
                      title="已通过检查"
                      items={stabilityEvidenceSummary.passedRequirements}
                      emptyText="暂未记录已通过的 SCI-01 检查项。"
                    />
                    <LabeledList
                      title="缺失的稳定性证据"
                      items={stabilityEvidenceSummary.missingEvidence}
                      emptyText="暂未记录缺失的 SCI-01 证据。"
                    />
                    <LabeledList
                      title="稳定性阻塞项"
                      items={stabilityEvidenceSummary.blockingIssues}
                      emptyText="暂未记录 SCI-01 阻塞项。"
                    />
                  </div>
                  <LabeledList
                    title="SCI-01 要求状态"
                    items={stabilityEvidenceSummary.requirementLines}
                    emptyText="暂未提供 SCI-01 要求明细。"
                  />
                </div>
              ) : null}
              {scientificVerificationSummary ? (
                <div className="mt-4 space-y-4 rounded-xl border bg-background/70 p-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <KeyValue
                      label="科研验证"
                      value={scientificVerificationSummary.statusLabel}
                    />
                    <KeyValue
                      label="验证可信度"
                      value={scientificVerificationSummary.confidenceLabel}
                    />
                  </div>
                  <div className="grid gap-4 xl:grid-cols-3">
                    <LabeledList
                      title="已通过要求"
                      items={scientificVerificationSummary.passedRequirements}
                      emptyText="当前还没有通过的科研验证检查项。"
                    />
                    <LabeledList
                      title="缺失证据"
                      items={scientificVerificationSummary.missingEvidence}
                      emptyText="当前没有记录缺失的科研验证证据。"
                    />
                    <LabeledList
                      title="阻断问题"
                      items={scientificVerificationSummary.blockingIssues}
                      emptyText="当前没有科研验证阻断问题。"
                    />
                  </div>
                  <LabeledList
                    title="要求状态"
                    items={scientificVerificationSummary.requirements.map(
                      (item) => `${item.label} | ${item.status} | ${item.detail}`,
                    )}
                    emptyText="当前没有科研验证要求状态明细。"
                  />
                </div>
              ) : null}
            </InfoPanel>

            <InfoPanel id={sectionElementId("metrics")} title="关键 CFD 指标" kicker="指标">
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

            <InfoPanel id={sectionElementId("trend")} title="结果趋势" kicker="趋势">
              {trendSeries.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {trendSeries.map((series) => (
                    <TrendTile key={series.id} series={series} />
                  ))}
                </div>
              ) : (
              <EmptyState text="当前还没有可展示的时间序列趋势。完成真实 OpenFOAM 求解并写出受力历史后，这里会显示收敛与受力变化趋势。" />
              )}
            </InfoPanel>
          </div>

          <div className="grid gap-4">
            <InfoPanel id={sectionElementId("cases")} title="案例匹配" kicker="案例">
              {geometryFindings.length > 0 ||
              scaleAssessment ||
              referenceValueSuggestions.length > 0 ||
              calculationPlanDraft.length > 0 ? (
                <div className="mb-4 space-y-4 rounded-xl border bg-background/70 p-4">
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <KeyValue
                      label="几何审阅"
                      value={
                        requiresImmediateConfirmation || geometryClarificationRequired
                          ? "需要立即澄清"
                          : calculationPlanDraft.length > 0
                            ? "待研究人员确认"
                            : "已就绪"
                      }
                    />
                    <KeyValue
                      label="尺度评估"
                      value={scaleAssessment?.summary_zh ?? "--"}
                    />
                    <KeyValue
                      label="参考建议"
                      value={`${referenceValueSuggestions.length} 项`}
                    />
                    <KeyValue
                      label="计算计划联动"
                      value={`${calculationPlanDraft.length} 项`}
                    />
                  </div>
                  <div className="grid gap-4 xl:grid-cols-3">
                    <LabeledList
                      title="几何发现"
                      items={geometryFindings.map((item) =>
                        `${item.severity ?? "提示"} | ${item.summary_zh ?? item.finding_id ?? "待补充几何发现"}`,
                      )}
                      emptyText="当前没有记录结构化几何发现。"
                    />
                    <LabeledList
                      title="参考建议"
                      items={referenceValueSuggestions.map((item) =>
                        `${item.quantity ?? "参考值"} | ${item.value ?? "--"}${item.unit ? ` ${item.unit}` : ""} | ${item.confidence ?? "--"} | ${item.source ?? "--"}`,
                      )}
                      emptyText="当前没有记录结构化参考建议。"
                    />
                    <LabeledList
                      title="计算计划延续项"
                      items={calculationPlanDraft.map((item) =>
                        `${item.label ?? item.category ?? "计算计划项"} | ${item.approval_state ?? "待处理"}${item.requires_immediate_confirmation ? " | 需要立即澄清" : ""}`,
                      )}
                      emptyText="当前还没有计算计划联动记录。"
                    />
                  </div>
                </div>
              ) : null}
              {selectedCaseProvenance ? (
                  <div className="mb-4 space-y-4 rounded-xl border bg-background/70 p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <KeyValue
                        label="选中案例"
                        value={localizeWorkspaceDisplayText(
                          selectedCaseProvenance.title ??
                            selectedCaseProvenance.case_id ??
                            "--",
                        )}
                      />
                      <KeyValue
                        label="主要来源"
                        value={localizeWorkspaceDisplayText(
                          selectedCaseProvenance.source_label ?? "--",
                        )}
                      />
                      <KeyValue
                        label="来源类型"
                        value={localizeWorkspaceDisplayText(
                          selectedCaseProvenance.source_type ?? "--",
                        )}
                      />
                    <KeyValue
                      label="基准覆盖"
                      value={`${selectedCaseProvenance.benchmark_metric_ids?.length ?? 0} 项指标`}
                    />
                  </div>
                  <div className="grid gap-4 xl:grid-cols-3">
                    <LabeledList
                      title="适用条件"
                      items={(selectedCaseProvenance.applicability_conditions ?? []).map(
                        (item) => localizeWorkspaceDisplayText(item),
                      )}
                      emptyText="当前没有记录明确的适用条件。"
                    />
                    <LabeledList
                      title="可信度 / 证据缺口"
                      items={[
                        selectedCaseProvenance.confidence_note
                          ? localizeWorkspaceDisplayText(
                              selectedCaseProvenance.confidence_note,
                            )
                          : null,
                        selectedCaseProvenance.evidence_gap_note
                          ? localizeWorkspaceDisplayText(
                              selectedCaseProvenance.evidence_gap_note,
                            )
                          : null,
                        selectedCaseProvenance.source_url,
                      ].filter((item): item is string => Boolean(item))}
                      emptyText="当前没有额外的溯源备注。"
                    />
                    <LabeledList
                      title="验收画像"
                      items={[
                        selectedCaseProvenance.acceptance_profile_summary_zh
                          ? localizeWorkspaceDisplayText(
                              selectedCaseProvenance.acceptance_profile_summary_zh,
                            )
                          : null,
                        ...(selectedCaseProvenance.benchmark_metric_ids ?? []).map(
                          (item) => `基准 | ${item}`,
                        ),
                      ].filter((item): item is string => Boolean(item))}
                      emptyText="当前没有验收画像摘要。"
                    />
                  </div>
                </div>
              ) : null}
              {candidateCases.length > 0 ? (
                <div className="space-y-3">
                  {candidateCases.slice(0, 3).map((candidate) => (
                    <div key={candidate.case_id} className={cn("rounded-xl border p-3", candidate.case_id === runtime?.selected_case_id ? "border-primary/30 bg-primary/5" : "border-border bg-muted/20")}>
                      <div className="mb-2 flex items-start justify-between gap-3">
                        <div>
                          <div className="font-medium text-foreground">
                            {localizeWorkspaceDisplayText(candidate.title)}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {localizeWorkspaceDisplayText(
                              candidate.geometry_family ?? "潜艇",
                            )}{" "}
                            ·{" "}
                            {localizeWorkspaceDisplayText(
                              candidate.task_type ?? "任务类型待定",
                            )}
                          </div>
                        </div>
                        {typeof candidate.score === "number" && <Badge variant="outline">{candidate.score.toFixed(2)}</Badge>}
                      </div>
                      <div className="text-sm leading-6 text-muted-foreground">
                        {candidate.rationale
                          ? localizeWorkspaceDisplayText(candidate.rationale)
                          : "待补充说明"}
                      </div>
                      {candidate.source_label ||
                      candidate.confidence_note ||
                      candidate.evidence_gap_note ||
                      (candidate.applicability_conditions?.length ?? 0) > 0 ? (
                        <div className="mt-3 grid gap-3 xl:grid-cols-2">
                          <LabeledList
                            title="溯源信息"
                            items={[
                              candidate.source_label
                                ? `来源 | ${localizeWorkspaceDisplayText(candidate.source_label)}`
                                : null,
                              candidate.source_url
                                ? `链接 | ${candidate.source_url}`
                                : null,
                              candidate.confidence_note
                                ? `可信度 | ${localizeWorkspaceDisplayText(candidate.confidence_note)}`
                                : null,
                              candidate.is_placeholder
                                ? "占位符支撑的建议案例"
                                : null,
                              candidate.evidence_gap_note
                                ? `缺口 | ${localizeWorkspaceDisplayText(candidate.evidence_gap_note)}`
                                : null,
                            ].filter((item): item is string => Boolean(item))}
                            emptyText="当前没有溯源备注。"
                          />
                          <LabeledList
                            title="适用条件"
                            items={(candidate.applicability_conditions ?? []).map((item) =>
                              localizeWorkspaceDisplayText(item),
                            )}
                            emptyText="当前没有适用条件记录。"
                          />
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState text="当前还没有可显示的候选案例。执行几何预检后，这里会展示最匹配的潜艇案例和理由。" />
              )}
            </InfoPanel>

            <InfoPanel id={sectionElementId("artifacts")} title="产物工作台" kicker="交付物">
              {artifactGroups.length > 0 || resultCards.length > 0 ? (
                <div className="space-y-4">
                  {resultCards.length > 0 ? (
                    <div className="rounded-xl border bg-background/70 p-4">
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-medium text-foreground">
                            目标结果
                          </div>
                          <div className="text-xs text-muted-foreground">
                            按输出项展示结果卡片，集中查看预览、交付状态和后处理来源。
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
        快速跳转
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
    delivered: "已交付",
    requested: "已请求",
    pending: "待处理",
    planned: "已规划",
    supported: "已支持",
    partially_delivered: "部分交付",
    not_yet_supported: "暂不支持",
    needs_clarification: "待澄清",
    "needs clarification": "待澄清",
    unknown: "待确认",
  };

  return labels[value] ?? localizeRuntimeText(value);
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
          {card.requestedLabel !== card.label ? (
            <div className="truncate text-xs text-muted-foreground">
              {card.requestedLabel}
            </div>
          ) : null}
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
            alt={`${card.label} 预览图`}
            className="aspect-[16/10] w-full object-cover"
          />
        </button>
      ) : (
        <div className="mb-3 flex aspect-[16/10] items-center justify-center rounded-lg border border-dashed bg-background/50 px-4 text-center text-xs text-muted-foreground">
          请求的后处理结果导出后，这里会显示对应预览。
        </div>
      )}

      <div className="space-y-2 text-xs text-muted-foreground">
        <div>
          <span className="font-medium text-foreground/80">请求项：</span>{" "}
          {card.requestedLabel}
        </div>
        {card.specSummary !== "--" ? <div>规格：{card.specSummary}</div> : null}
        {card.figureRenderStatus !== "--" ? (
          <div>
            <span className="font-medium text-foreground/80">图像状态：</span>{" "}
            {card.figureRenderStatus}
          </div>
        ) : null}
        {card.figureCaption !== "--" ? <div>图注：{card.figureCaption}</div> : null}
        {card.selectorSummary !== "--" ? (
          <div>选择器来源：{card.selectorSummary}</div>
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
                  打开
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
          当前结果还没有导出专属产物。
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
            {event.status ? (
              <Badge variant="secondary">{formatRuntimeStatus(event.status)}</Badge>
            ) : null}
          </div>
          <div className="text-sm font-medium text-foreground">
            {event.title ? localizeWorkspaceDisplayText(event.title) : "阶段事件"}
          </div>
          {event.summary ? (
            <div className="text-sm leading-6 text-muted-foreground">
              {localizeWorkspaceDisplayText(event.summary)}
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
          <span>
            {event.actor ? localizeWorkspaceDisplayText(event.actor) : "DeerFlow"}
          </span>
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

function ArtifactPathList({
  title,
  paths,
  emptyText,
  onOpenArtifact,
}: {
  title: string;
  paths: string[];
  emptyText: string;
  onOpenArtifact: (artifactPath: string) => void;
}) {
  const uniquePaths = paths.filter(
    (artifactPath, index, allPaths) =>
      Boolean(artifactPath) && allPaths.indexOf(artifactPath) === index,
  );

  return (
    <div className="rounded-xl border bg-background/70 p-4">
      <div className="mb-3 text-sm font-medium text-foreground">{title}</div>
      {uniquePaths.length > 0 ? (
        <div className="space-y-2">
          {uniquePaths.map((artifactPath) => {
            const Icon = artifactIcon(artifactPath);
            const meta = getSubmarineArtifactMeta(artifactPath);
            return (
              <button
                key={`${title}-${artifactPath}`}
                type="button"
                className="flex w-full items-center justify-between gap-3 rounded-xl border bg-muted/20 p-3 text-left transition hover:border-primary/40 hover:bg-primary/5"
                onClick={() => onOpenArtifact(artifactPath)}
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-lg border bg-background/80 p-2">
                    <Icon className="size-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-foreground">
                      {meta.label}
                    </div>
                    <div className="truncate text-xs text-muted-foreground">
                      {artifactPath}
                    </div>
                  </div>
                </div>
                <Badge variant="outline" className="shrink-0 bg-background/80">
                  打开
                </Badge>
              </button>
            );
          })}
        </div>
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
                <Badge variant="secondary">{formatRuntimeStatus(item.status)}</Badge>
              </div>
              <div className="mt-2 text-sm leading-6 text-muted-foreground">{item.goal}</div>
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
    return "待执行";
  }
  return formatRuntimeStatus(status);
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
              第 {index + 1} 步
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
