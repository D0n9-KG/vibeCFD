// src/components/workspace/submarine-pipeline.tsx
"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { type GroupImperativeHandle } from "react-resizable-panels";
import { toast } from "sonner";

import {
  getPipelineDefaultLayout,
  getPipelineLayoutConfig,
  getPipelineStoredLayout,
  PIPELINE_STORAGE_KEY_CHAT,
  PIPELINE_STORAGE_KEY_SIDEBAR,
} from "@/app/workspace/submarine/submarine-pipeline-layout";
import { type PromptInputMessage } from "@/components/ai-elements/prompt-input";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { localizeWorkspaceDisplayText } from "@/core/i18n/workspace-display";
import { useLocalSettings } from "@/core/settings";
import { useDeleteThread, useThreads } from "@/core/threads/hooks";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import { InputBox } from "./input-box";
import { MessageList } from "./messages";
import { useThread } from "./messages/context";
import {
  deriveCompletedSubmarineRunIds,
  deriveSubmarineRunDeletionPath,
  deriveSubmarineSidebarRuns,
  getSubmarineDisplayedNextStage,
  getSubmarineDisplayedStage,
} from "./submarine-pipeline-runs";
import {
  getSubmarinePipelineCenterPaneConfig,
  getSubmarinePipelineChatRailClassName,
  getSubmarinePipelineChatViewportClassName,
  getSubmarinePipelineDesktopShellConfig,
} from "./submarine-pipeline-shell";
import {
  type SidebarRunItem,
  SubmarinePipelineSidebar,
} from "./submarine-pipeline-sidebar";
import {
  getSubmarinePipelineStatus,
  type SubmarinePipelineStatus,
} from "./submarine-pipeline-status";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineGeometryPayload,
  SubmarineRuntimeSnapshotPayload,
  SubmarineSolverMetrics,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";
import { buildSubmarineTrendSeries } from "./submarine-runtime-panel.trends";
import {
  GeometryPreflightCard,
  ResultReportingCard,
  SolverDispatchCard,
  SupervisorReviewCard,
  TaskIntelligenceCard,
  type StageRuntimeSnapshot,
} from "./submarine-stage-cards";
import { WORKSPACE_RESIZABLE_IDS } from "./workspace-resizable-ids";

// ── Persistence helpers ───────────────────────────────────────────────────────


// ── Runtime snapshot type (mirrors SubmarineRuntimePanel) ────────────────────
type SubmarineRuntimeSnapshot = SubmarineRuntimeSnapshotPayload;
type SubmarineInputContext = ReturnType<typeof useLocalSettings>[0]["context"];

function safeJsonParse<T>(content?: string | null): T | null {
  if (!content) return null;
  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

function artifactWeight(path: string): number {
  if (path.endsWith("/cfd-design-brief.json")) return 2;
  if (path.endsWith("/final-report.json")) return 7;
  if (path.endsWith("/solver-results.json")) return 8;
  if (path.endsWith("/openfoam-request.json")) return 9;
  if (path.endsWith("/geometry-check.json")) return 10;
  return 20;
}

// ── Props ────────────────────────────────────────────────────────────────────

interface SubmarinePipelineProps {
  threadId: string;
  isNewThread: boolean;
  isUploading: boolean;
  isMock?: boolean;
  showChatRail?: boolean;
  showSidebar?: boolean;
  /** Controlled from parent page header button; toggles mobile chat rail */
  chatOpen?: boolean;
  sendMessage: (
    threadId: string,
    message: PromptInputMessage,
  ) => Promise<void> | void;
  onStop: () => Promise<void>;
}

// ── Main component ────────────────────────────────────────────────────────────

export function SubmarinePipeline({
  threadId,
  isNewThread,
  isUploading,
  isMock = false,
  showChatRail = true,
  showSidebar = true,
  chatOpen: chatOpenProp,
  sendMessage,
  onStop,
}: SubmarinePipelineProps) {
  const chatOpen = chatOpenProp ?? false;
  const router = useRouter();
  const { thread } = useThread();
  const [settings, setSettings] = useLocalSettings();
  const [isCleaningRuns, setIsCleaningRuns] = useState(false);
  const layoutConfig = useMemo(() => getPipelineLayoutConfig(), []);
  const desktopShell = useMemo(
    () => getSubmarinePipelineDesktopShellConfig(),
    [],
  );
  const pipelineGroupRef = useRef<GroupImperativeHandle | null>(null);
  // centerRef scopes the xl desktop pane for stage-nav scroll
  const centerRef = useRef<HTMLDivElement>(null);
  // mobileCenterRef scopes the mobile pane separately to avoid duplicate-id querySelector conflicts
  const mobileCenterRef = useRef<HTMLDivElement>(null);

  // ── Run list from useThreads (filter submarine threads) ───────────────────
  const { data: allThreads = [] } = useThreads({ limit: 30 }, isMock);
  const { mutateAsync: deleteThread } = useDeleteThread();
  const runs = useMemo<SidebarRunItem[]>(() => {
    return deriveSubmarineSidebarRuns(allThreads);
  }, [allThreads]);
  const completedRunIds = useMemo(
    () => deriveCompletedSubmarineRunIds(runs),
    [runs],
  );

  // ── Layout persistence ────────────────────────────────────────────────────
  const defaultLayout = useMemo(() => getPipelineDefaultLayout(), []);

  useEffect(() => {
    if (typeof window === "undefined" || !pipelineGroupRef.current) {
      return;
    }

    pipelineGroupRef.current.setLayout(
      getPipelineStoredLayout({
        viewportWidth: window.innerWidth,
        sidebarRaw: window.localStorage.getItem(PIPELINE_STORAGE_KEY_SIDEBAR),
        chatRaw: window.localStorage.getItem(PIPELINE_STORAGE_KEY_CHAT),
      }),
    );
  }, []);

  const handleLayoutChanged = useCallback(
    (layout: Record<string, number>) => {
      const sidebarSize = layout["submarine-pipeline-sidebar"];
      const chatSize = layout["submarine-pipeline-chat"];
      if (typeof sidebarSize === "number") {
        window.localStorage.setItem(PIPELINE_STORAGE_KEY_SIDEBAR, String(sidebarSize));
      }
      if (typeof chatSize === "number") {
        window.localStorage.setItem(PIPELINE_STORAGE_KEY_CHAT, String(chatSize));
      }
    },
    [],
  );

  // ── Runtime state ──────────────────────────────────────────────────────────
  const runtime = useMemo<SubmarineRuntimeSnapshot | null>(() => {
    const raw = thread.values.submarine_runtime;
    return raw && typeof raw === "object"
      ? (raw as SubmarineRuntimeSnapshot)
      : null;
  }, [thread.values.submarine_runtime]);

  const submarineArtifacts = useMemo(() => {
    const runtimePaths = Array.isArray(runtime?.artifact_virtual_paths)
      ? runtime.artifact_virtual_paths
      : [];
    const threadPaths = Array.isArray(thread.values.artifacts)
      ? thread.values.artifacts
      : [];
    return [...threadPaths, ...runtimePaths]
      .filter(
        (path, idx, arr) =>
          path.includes("/submarine/") && arr.indexOf(path) === idx,
      )
      .sort((a, b) => artifactWeight(a) - artifactWeight(b));
  }, [runtime?.artifact_virtual_paths, thread.values.artifacts]);

  const designBriefJson = submarineArtifacts.find((p) =>
    p.endsWith("/cfd-design-brief.json"),
  );
  const finalReportJson = submarineArtifacts.find((p) =>
    p.endsWith("/final-report.json"),
  );
  const solverResultsJson =
    runtime?.solver_results_virtual_path ??
    submarineArtifacts.find((p) => p.endsWith("/solver-results.json"));
  const geometryJson = submarineArtifacts.find((p) =>
    p.endsWith("/geometry-check.json"),
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
  const solverResultsParsed = useMemo(
    () => safeJsonParse<SubmarineSolverMetrics>(solverResultsContent),
    [solverResultsContent],
  );
  // Mirror existing panel: prefer finalReport.solver_metrics, fallback to solver-results.json
  const solverMetrics = useMemo(
    () => finalReport?.solver_metrics ?? solverResultsParsed,
    [finalReport, solverResultsParsed],
  );
  const geometry = useMemo(
    () => safeJsonParse<SubmarineGeometryPayload>(geometryContent),
    [geometryContent],
  );

  // buildSubmarineTrendSeries returns SubmarineTrendSeries[] where each series has id + values: TrendValue[]
  const trendValues = useMemo(() => {
    const seriesList = buildSubmarineTrendSeries(solverMetrics);
    const cdSeries = seriesList.find((s) => s.id === "cd");
    return cdSeries?.values.map((v) => v.value) ?? [];
  }, [solverMetrics]);

  // ── Snapshot for stage cards ───────────────────────────────────────────────
  const stageSnapshot = useMemo<StageRuntimeSnapshot | null>(() => {
    if (!runtime) return null;
    return {
      current_stage: runtime.current_stage ?? undefined,
      next_recommended_stage: runtime.next_recommended_stage ?? undefined,
      task_summary: runtime.task_summary ?? undefined,
      simulation_requirements: runtime.simulation_requirements,
      geometry_findings: runtime.geometry_findings ?? null,
      scale_assessment: runtime.scale_assessment ?? null,
      reference_value_suggestions: runtime.reference_value_suggestions ?? null,
      clarification_required: runtime.clarification_required ?? null,
      calculation_plan: runtime.calculation_plan ?? null,
      requires_immediate_confirmation:
        runtime.requires_immediate_confirmation ?? null,
      stage_status: runtime.stage_status,
      runtime_status: runtime.runtime_status,
      runtime_summary: runtime.runtime_summary,
      recovery_guidance: runtime.recovery_guidance,
      blocker_detail: runtime.blocker_detail,
      review_status: runtime.review_status,
      scientific_gate_status: runtime.scientific_gate_status,
      allowed_claim_level: runtime.allowed_claim_level,
      decision_status: runtime.decision_status,
      delivery_decision_summary: runtime.delivery_decision_summary ?? null,
      report_virtual_path: runtime.report_virtual_path,
      // Strip fields not in StageRuntimeSnapshot (target_skills)
      execution_plan: runtime.execution_plan?.map((item) => ({
        role_id: item.role_id,
        owner: item.owner,
        goal: item.goal,
        status: item.status,
      })) ?? null,
      // Strip fields not in StageRuntimeSnapshot (role_id, skill_names)
      activity_timeline: runtime.activity_timeline?.map((item) => ({
        stage: item.stage ?? undefined,
        actor: item.actor ?? undefined,
        title: item.title ?? undefined,
        summary: item.summary ?? undefined,
        status: item.status,
        timestamp: item.timestamp,
      })) ?? null,
    };
  }, [runtime]);

  const displayedCurrentStage = useMemo(
    () => getSubmarineDisplayedStage(runtime, designBrief),
    [designBrief, runtime],
  );
  const displayedNextStage = useMemo(
    () => getSubmarineDisplayedNextStage(runtime, designBrief),
    [designBrief, runtime],
  );

  const pipelineStatus = useMemo(
    () =>
      getSubmarinePipelineStatus({
        threadError: thread.error,
        threadIsLoading: thread.isLoading,
        isNewThread,
        hasMessages: thread.messages.length > 0,
        hasDesignBrief: Boolean(designBrief),
        hasFinalReport: Boolean(finalReport),
        designBriefSummary: designBrief?.summary_zh,
        runtimeTaskSummary: runtime?.task_summary,
        runtimeStatus: runtime?.runtime_status,
        runtimeSummary: runtime?.runtime_summary,
        recoveryGuidance: runtime?.recovery_guidance,
        blockerDetail: runtime?.blocker_detail,
        reviewStatus: runtime?.review_status ?? designBrief?.review_status,
        nextRecommendedStage:
          runtime?.next_recommended_stage ?? designBrief?.next_recommended_stage,
        requiresImmediateConfirmation:
          runtime?.requires_immediate_confirmation ??
          designBrief?.requires_immediate_confirmation,
        pendingCalculationPlanCount: (
          runtime?.calculation_plan ??
          designBrief?.calculation_plan ??
          []
        ).filter((item) => item?.approval_state !== "researcher_confirmed").length,
        scientificGateStatus: runtime?.scientific_gate_status,
        allowedClaimLevel: runtime?.allowed_claim_level,
        decisionStatus: runtime?.decision_status ?? finalReport?.decision_status,
        scientificVerificationStatus:
          runtime?.scientific_verification_assessment?.status,
        environmentParityStatus:
          finalReport?.reproducibility_summary?.parity_status ??
          finalReport?.environment_parity_assessment?.parity_status ??
          runtime?.environment_parity_assessment?.parity_status,
        reproducibilityStatus:
          finalReport?.reproducibility_summary?.reproducibility_status ??
          finalReport?.environment_parity_assessment?.parity_status ??
          runtime?.environment_parity_assessment?.parity_status,
        environmentProfileLabel:
          finalReport?.environment_parity_assessment?.profile_label ??
          runtime?.environment_parity_assessment?.profile_label,
      }),
    [
      designBrief,
      finalReport,
      isNewThread,
      runtime?.calculation_plan,
      runtime?.allowed_claim_level,
      runtime?.blocker_detail,
      runtime?.decision_status,
      runtime?.environment_parity_assessment?.parity_status,
      runtime?.environment_parity_assessment?.profile_label,
      runtime?.recovery_guidance,
      runtime?.requires_immediate_confirmation,
      runtime?.review_status,
      runtime?.next_recommended_stage,
      runtime?.scientific_gate_status,
      runtime?.scientific_verification_assessment,
      runtime?.runtime_status,
      runtime?.runtime_summary,
      runtime?.task_summary,
      thread.error,
      thread.isLoading,
      thread.messages.length,
    ],
  );

  // ── Callbacks ─────────────────────────────────────────────────────────────
  // Bridge from stage card { role, content } to PromptInputMessage { text, files }
  const handleSend = useCallback(
    (tid: string, message: { role: "human"; content: string }) => {
      return sendMessage(tid, { text: message.content, files: [] });
    },
    [sendMessage],
  );

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      return sendMessage(threadId, message);
    },
    [sendMessage, threadId],
  );

  // Use scoped querySelector so stage navigation targets the visible pane,
  // not the CSS-hidden duplicate (both panes are mounted simultaneously).
  const handleStageClick = useCallback((stageId: string) => {
    // On xl the desktop center pane is visible; on mobile use the mobile pane.
    const container =
      window.innerWidth >= 1280 ? centerRef.current : mobileCenterRef.current;
    const el = container?.querySelector<HTMLElement>(
      `[data-stage-id="submarine-stage-${stageId}"]`,
    );
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const handleNewSimulation = useCallback(() => {
    router.push("/workspace/submarine/new");
  }, [router]);
  const renderCenterOnly = !showSidebar && !showChatRail;

  const handleDeleteRun = useCallback(
    async (runThreadId: string) => {
      setIsCleaningRuns(true);
      try {
        await deleteThread({ threadId: runThreadId });
        const nextPath = deriveSubmarineRunDeletionPath(
          allThreads,
          [runThreadId],
          threadId,
        );
        if (nextPath) {
          router.replace(nextPath);
        }
        toast.success("已删除该仿真任务，并同步清理关联对话、上传与产物。");
      } catch (error) {
        toast.error(
          error instanceof Error ? error.message : "删除仿真任务失败，请稍后重试。",
        );
      } finally {
        setIsCleaningRuns(false);
      }
    },
    [allThreads, deleteThread, router, threadId],
  );

  const handleCleanupCompletedRuns = useCallback(async () => {
    if (completedRunIds.length === 0) {
      toast.info("当前没有可清理的已完成仿真任务。");
      return;
    }

    setIsCleaningRuns(true);
    const deletedRunIds: string[] = [];
    const failedRunIds: string[] = [];

    try {
      for (const runThreadId of completedRunIds) {
        try {
          await deleteThread({ threadId: runThreadId });
          deletedRunIds.push(runThreadId);
        } catch {
          failedRunIds.push(runThreadId);
        }
      }

      const nextPath = deriveSubmarineRunDeletionPath(
        allThreads,
        deletedRunIds,
        threadId,
      );
      if (nextPath) {
        router.replace(nextPath);
      }

      if (failedRunIds.length > 0) {
        toast.error(
          deletedRunIds.length > 0
            ? `已清理 ${deletedRunIds.length} 个已完成任务，但还有 ${failedRunIds.length} 个删除失败，请重试。`
            : "清理已完成任务失败，请稍后重试。",
        );
        return;
      }

      toast.success(
        `已清理 ${deletedRunIds.length} 个已完成仿真任务，对话、上传与产物已同步删除。`,
      );
    } finally {
      setIsCleaningRuns(false);
    }
  }, [allThreads, completedRunIds, deleteThread, router, threadId]);

  // ── Render ────────────────────────────────────────────────────────────────
  // xl+ : 3 panes (sidebar + center + chat)
  // < xl : single column — center only; chat toggle owned by page.tsx header button
  if (renderCenterOnly) {
    return (
      <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-[28px] border border-stone-200/80 bg-white shadow-[0_24px_64px_rgba(15,23,42,0.08)]">
        <div className="min-h-0 flex-1 overflow-hidden">
          <PipelineCenterPane
            thread={thread}
            isNewThread={isNewThread}
            runtime={runtime}
            displayedCurrentStage={displayedCurrentStage}
            displayedNextStage={displayedNextStage}
            pipelineStatus={pipelineStatus}
            centerRef={centerRef}
            threadId={threadId}
            stageSnapshot={stageSnapshot}
            designBrief={designBrief}
            geometry={geometry}
            solverMetrics={solverMetrics}
            trendValues={trendValues}
            finalReport={finalReport}
            handleSend={handleSend}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      {/* 3-pane resizable layout — full height on xl, flex column on mobile */}
      <div className="min-h-0 flex-1 xl:hidden">
        {/* Mobile: center always visible, chat rail below toggle */}
        <div className="flex h-full flex-col overflow-hidden">
          <PipelineCenterPane
            thread={thread}
            isNewThread={isNewThread}
            runtime={runtime}
            displayedCurrentStage={displayedCurrentStage}
            displayedNextStage={displayedNextStage}
            pipelineStatus={pipelineStatus}
            centerRef={mobileCenterRef}
            threadId={threadId}
            stageSnapshot={stageSnapshot}
            designBrief={designBrief}
            geometry={geometry}
            solverMetrics={solverMetrics}
            trendValues={trendValues}
            finalReport={finalReport}
            handleSend={handleSend}
          />
          {showChatRail && chatOpen && (
            <SubmarinePipelineChatRail
              thread={thread}
              pipelineStatus={pipelineStatus}
              threadId={threadId}
              isNewThread={isNewThread}
              isUploading={isUploading}
              context={settings.context}
              onContextChange={(context) => setSettings("context", context)}
              handleSubmit={handleSubmit}
              onStop={onStop}
            />
          )}
        </div>
      </div>

      <div className={desktopShell.containerClassName}>
        <ResizablePanelGroup
          orientation="horizontal"
          className={desktopShell.groupClassName}
          onLayoutChanged={handleLayoutChanged}
          defaultLayout={defaultLayout}
          groupRef={pipelineGroupRef}
          id={WORKSPACE_RESIZABLE_IDS.submarinePipelineGroup}
        >
        {showSidebar ? (
          <>
            {/* Sidebar */}
            <ResizablePanel
              id="submarine-pipeline-sidebar"
              defaultSize={layoutConfig.sidebarDefaultSize}
              minSize={layoutConfig.sidebarMinSize}
              maxSize={layoutConfig.sidebarMaxSize}
            >
              <SubmarinePipelineSidebar
                currentThreadId={threadId}
                currentStage={displayedCurrentStage}
                currentThreadRunLabel={pipelineStatus.runLabel}
                currentThreadTone={pipelineStatus.tone}
                runs={runs}
                completedRunCount={completedRunIds.length}
                isCleanupPending={isCleaningRuns}
                onStageClick={handleStageClick}
                onDeleteRun={handleDeleteRun}
                onCleanupCompletedRuns={handleCleanupCompletedRuns}
                onNewSimulation={handleNewSimulation}
              />
            </ResizablePanel>

            <ResizableHandle
              id={WORKSPACE_RESIZABLE_IDS.submarinePipelineSidebarHandle}
              withHandle
            />
          </>
        ) : null}

        {/* Center — stage pipeline */}
        <ResizablePanel id="submarine-pipeline-center">
          <PipelineCenterPane
            thread={thread}
            isNewThread={isNewThread}
            runtime={runtime}
            displayedCurrentStage={displayedCurrentStage}
            displayedNextStage={displayedNextStage}
            pipelineStatus={pipelineStatus}
            centerRef={centerRef}
            threadId={threadId}
            stageSnapshot={stageSnapshot}
            designBrief={designBrief}
            geometry={geometry}
            solverMetrics={solverMetrics}
            trendValues={trendValues}
            finalReport={finalReport}
            handleSend={handleSend}
          />
        </ResizablePanel>

        {showChatRail ? (
          <>
            <ResizableHandle
              id={WORKSPACE_RESIZABLE_IDS.submarinePipelineChatHandle}
              withHandle
            />

            {/* Chat rail */}
            <ResizablePanel
              id="submarine-pipeline-chat"
              defaultSize={layoutConfig.chatDefaultSize}
              minSize={layoutConfig.chatMinSize}
              maxSize={layoutConfig.chatMaxSize}
            >
              <SubmarinePipelineChatRail
                thread={thread}
                pipelineStatus={pipelineStatus}
                threadId={threadId}
                isNewThread={isNewThread}
                isUploading={isUploading}
                context={settings.context}
                onContextChange={(context) => setSettings("context", context)}
                handleSubmit={handleSubmit}
                onStop={onStop}
              />
            </ResizablePanel>
          </>
        ) : null}
        </ResizablePanelGroup>
      </div>
    </div>
  );
}

// ── PipelineCenterPane (extracted to avoid JSX duplication between mobile/xl) ─

function PipelineCenterPane({
  thread,
  isNewThread,
  runtime,
  displayedCurrentStage,
  displayedNextStage,
  pipelineStatus,
  centerRef,
  threadId,
  stageSnapshot,
  designBrief,
  geometry,
  solverMetrics,
  trendValues,
  finalReport,
  handleSend,
}: {
  thread: ReturnType<typeof useThread>["thread"];
  isNewThread: boolean;
  runtime: SubmarineRuntimeSnapshot | null;
  displayedCurrentStage: string | null;
  displayedNextStage: string | null;
  pipelineStatus: SubmarinePipelineStatus;
  centerRef: React.RefObject<HTMLDivElement | null>;
  threadId: string;
  stageSnapshot: StageRuntimeSnapshot | null;
  designBrief: SubmarineDesignBriefPayload | null;
  geometry: SubmarineGeometryPayload | null;
  solverMetrics: SubmarineSolverMetrics | null;
  trendValues: number[];
  finalReport: SubmarineFinalReportPayload | null;
  handleSend: (
    tid: string,
    message: { role: "human"; content: string },
  ) => Promise<void> | void;
}) {
  const centerPaneConfig = getSubmarinePipelineCenterPaneConfig();
  const currentStageLabel = localizeWorkspaceDisplayText(
    displayedCurrentStage
      ? (STAGE_LABELS[displayedCurrentStage] ?? displayedCurrentStage)
      : "等待建立研究简报",
  );
  const nextStageLabel = localizeWorkspaceDisplayText(
    displayedNextStage
      ? (STAGE_LABELS[displayedNextStage] ?? displayedNextStage)
      : "补充目标与基线条件",
  );
  const calculationPlanDraft =
    runtime?.calculation_plan ?? designBrief?.calculation_plan ?? [];
  const pendingCalculationPlanCount = calculationPlanDraft.filter(
    (item) => item?.approval_state !== "researcher_confirmed",
  ).length;
  const hasImmediateCalculationPlanClarification =
    Boolean(
      runtime?.requires_immediate_confirmation ??
        designBrief?.requires_immediate_confirmation,
    ) ||
    calculationPlanDraft.some(
      (item) =>
        Boolean(item?.requires_immediate_confirmation) &&
        item?.approval_state !== "researcher_confirmed",
    );
  const hasPendingBriefConfirmation = Boolean(
    pendingCalculationPlanCount > 0 ||
      hasImmediateCalculationPlanClarification ||
      runtime?.review_status === "needs_user_confirmation" ||
      runtime?.next_recommended_stage === "user-confirmation" ||
      (designBrief &&
        (designBrief.confirmation_status !== "confirmed" ||
          (designBrief.open_questions?.filter(Boolean).length ?? 0) > 0)),
  );
  const submarineArtifactCount = Array.isArray(thread.values.artifacts)
    ? thread.values.artifacts.filter((path) => path.includes("/submarine/")).length
    : 0;
  const isRehydratingExistingThread =
    !isNewThread &&
    thread.isLoading &&
    thread.messages.length === 0 &&
    !designBrief &&
    !finalReport &&
    !runtime;
  const evidenceStatusLabel = localizeWorkspaceDisplayText(
    finalReport
      ? "已有报告与评估结论"
      : hasPendingBriefConfirmation
        ? hasImmediateCalculationPlanClarification
          ? "计算计划需要立即确认"
          : pendingCalculationPlanCount > 0
            ? `计算计划待确认（${pendingCalculationPlanCount} 项）`
            : "研究简报待确认，确认后才会进入求解派发"
        : designBrief
          ? "简报已确认，待生成数值证据"
          : "等待建立可确认的研究简报",
  );
  return (
    <div className="flex h-full min-h-0 flex-col bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.10),_transparent_32%),linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.96))]">
      {/* Center header — xl only (mobile header is in parent) */}
      <div className="hidden shrink-0 items-center gap-2.5 border-b border-stone-200 px-4 py-2.5 xl:flex">
        <span className="text-[14px] font-bold text-stone-900">
          {thread.values.title ?? "仿真任务"}
        </span>
        {runtime?.current_stage && (
          <StageBadge stage={displayedCurrentStage ?? runtime.current_stage} />
        )}
        {runtime?.simulation_requirements && (
          <SimReqTags reqs={runtime.simulation_requirements} />
        )}
      </div>

      {/* Stage list */}
      <div
        ref={centerRef}
        className={centerPaneConfig.scrollClassName}
      >
        <div className={centerPaneConfig.overviewClassName}>
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0 flex-1 space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-600">
                  研究驾驶舱
                </span>
                {runtime?.current_stage ? (
                  <StageBadge
                    stage={displayedCurrentStage ?? runtime.current_stage}
                  />
                ) : (
                  <span className="rounded-full bg-stone-100 px-2.5 py-1 text-[11px] font-semibold text-stone-600">
                    待启动
                  </span>
                )}
                <span
                  className={cn(
                    "rounded-full px-2.5 py-1 text-[11px] font-semibold text-white",
                    pipelineStatus.tone === "error"
                      ? "bg-red-600"
                      : "bg-stone-900",
                  )}
                >
                  {pipelineStatus.outputStatus}
                </span>
              </div>

              <div className="space-y-2">
                <h2 className="text-xl font-semibold tracking-tight text-stone-900 xl:text-2xl">
                  {thread.values.title ?? "准备新的仿真研究"}
                </h2>
                <p className="max-w-3xl text-sm leading-6 text-stone-600">
                  {pipelineStatus.summaryText}
                </p>
              </div>

              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                <WorkbenchFocusTile
                  label="当前阶段"
                  value={currentStageLabel}
                />
                <WorkbenchFocusTile
                  label="下一步"
                  value={nextStageLabel}
                />
                <WorkbenchFocusTile
                  label="证据链"
                  value={evidenceStatusLabel}
                />
              </div>

              {runtime?.simulation_requirements && (
                <div className="flex flex-wrap gap-2">
                  <SimReqTags reqs={runtime.simulation_requirements} />
                </div>
              )}

              {pipelineStatus.errorBanner && (
                <div className="rounded-2xl border border-red-200 bg-red-50/90 p-4 shadow-sm">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-red-600">
                    Failure surfaced
                  </div>
                  <div className="mt-2 text-base font-semibold text-red-900">
                    {pipelineStatus.errorBanner.title}
                  </div>
                  <p className="mt-1 text-sm leading-6 text-red-800">
                    {pipelineStatus.errorBanner.guidance}
                  </p>
                  <div className="mt-3 rounded-xl border border-red-200 bg-white/80 px-3 py-2 text-xs leading-5 text-red-900">
                    {pipelineStatus.errorBanner.message}
                  </div>
                </div>
              )}
            </div>

            <div className="grid w-full gap-2 sm:grid-cols-3 xl:w-[22rem] xl:grid-cols-1">
              <WorkbenchStatCard
                label="子流程"
                value={String(stageSnapshot?.execution_plan?.length ?? 0)}
                meta="当前计划项"
              />
              <WorkbenchStatCard
                label="对话消息"
                value={String(thread.messages.length)}
                meta="已纳入上下文"
              />
              <WorkbenchStatCard
                label="产物"
                value={String(submarineArtifactCount)}
                meta="研究产物"
              />
            </div>
          </div>
        </div>

        {isRehydratingExistingThread ? (
          <div className="grid gap-4">
            <div className="rounded-[28px] border border-sky-100 bg-white/90 p-6 shadow-[0_18px_60px_rgba(14,165,233,0.10)]">
              <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-600">
                Rehydrating Thread
              </div>
              <h3 className="mt-3 text-xl font-semibold text-stone-900">
                正在恢复已有仿真任务
              </h3>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">
                已进入创建完成的潜艇线程，当前正在重新加载首条消息、上传附件和研究产物。恢复完成后，工作台会自动回到对应阶段，而不是回退成新的空白任务。
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <WorkbenchFocusTile
                  label="线程身份"
                  value={thread.values.title ?? threadId}
                />
                <WorkbenchFocusTile
                  label="恢复内容"
                  value="消息、附件与产物"
                />
                <WorkbenchFocusTile
                  label="当前状态"
                  value="正在重新水合页面状态"
                />
              </div>
            </div>
          </div>
        ) : (
          <div className={centerPaneConfig.stageGridClassName}>
            {/* data-stage-id instead of id to avoid duplicate-id issues when both
                mobile and desktop panes are mounted simultaneously */}
            <div
              className={centerPaneConfig.stageSectionClassName}
              data-stage-id="submarine-stage-task-intelligence"
            >
              <TaskIntelligenceCard
                threadId={threadId}
                snapshot={stageSnapshot}
                designBrief={designBrief}
                onConfirm={handleSend}
              />
            </div>
            <div
              className={centerPaneConfig.stageSectionClassName}
              data-stage-id="submarine-stage-geometry-preflight"
            >
              <GeometryPreflightCard snapshot={stageSnapshot} geometry={geometry} />
            </div>
            <div
              className={centerPaneConfig.stageSectionClassName}
              data-stage-id="submarine-stage-solver-dispatch"
            >
              <SolverDispatchCard
                snapshot={stageSnapshot}
                solverMetrics={solverMetrics}
                trendValues={trendValues}
              />
            </div>
            <div
              className={centerPaneConfig.stageSectionClassName}
              data-stage-id="submarine-stage-result-reporting"
            >
              <ResultReportingCard
                snapshot={stageSnapshot}
                finalReport={finalReport}
                solverMetrics={solverMetrics}
                reportVirtualPath={runtime?.report_virtual_path}
              />
            </div>
            <div
              className={cn(centerPaneConfig.stageSectionClassName, "xl:col-span-2")}
              data-stage-id="submarine-stage-supervisor-review"
            >
              <SupervisorReviewCard
                threadId={threadId}
                snapshot={stageSnapshot}
                finalReport={finalReport}
                onConfirm={handleSend}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── PipelineChatRail ──────────────────────────────────────────────────────────

type SubmarinePipelineChatRailProps = {
  thread: ReturnType<typeof useThread>["thread"];
  pipelineStatus: SubmarinePipelineStatus;
  threadId: string;
  isNewThread: boolean;
  isUploading: boolean;
  context: SubmarineInputContext;
  onContextChange: (context: SubmarineInputContext) => void;
  className?: string;
  handleSubmit: (message: PromptInputMessage) => Promise<void> | void;
  onStop: () => Promise<void>;
};

export function SubmarinePipelineChatRail({
  thread,
  pipelineStatus,
  threadId,
  isNewThread,
  isUploading,
  context,
  onContextChange,
  className,
  handleSubmit,
  onStop,
}: SubmarinePipelineChatRailProps) {
  return (
    <div className={cn(getSubmarinePipelineChatRailClassName(), className)}>
      {/* Chat header */}
      <div className="flex shrink-0 items-center gap-2 border-b border-stone-200 px-3.5 py-2.5">
        <span
          className={cn(
            "inline-block size-[6px] shrink-0 rounded-full",
            pipelineStatus.tone === "error"
              ? "bg-red-500"
              : pipelineStatus.tone === "streaming"
                ? "bg-green-500"
                : "bg-amber-500",
          )}
        />
        <span className="text-[12px] font-semibold text-stone-800">
          {pipelineStatus.agentLabel}
        </span>
      </div>

      {pipelineStatus.errorBanner && (
        <div className="border-b border-red-200 bg-red-50 px-3.5 py-2 text-xs leading-5 text-red-800">
          {pipelineStatus.errorBanner.message}
        </div>
      )}

      {/* Messages */}
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <MessageList
          className={getSubmarinePipelineChatViewportClassName()}
          paddingBottom={160}
          threadId={threadId}
          thread={thread}
        />
      </div>

      {/* Input */}
      <div className="shrink-0 border-t border-stone-200 bg-white p-2.5">
        <InputBox
          className="w-full bg-white"
          textareaClassName="min-h-28"
          isNewThread={isNewThread}
          showNewThreadSuggestions={false}
          threadId={threadId}
          autoFocus={isNewThread}
          status={
            pipelineStatus.tone === "error"
              ? "error"
              : pipelineStatus.tone === "streaming"
                ? "streaming"
                : "ready"
          }
          context={context}
          disabled={
            env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isUploading
          }
          onContextChange={onContextChange}
          onSubmit={handleSubmit}
          onStop={onStop}
        />
      </div>
    </div>
  );
}

// ── Small presentational helpers ─────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  "task-intelligence": "任务理解",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解执行",
  "result-reporting": "结果整理",
  "supervisor-review": "主管复核",
  "user-confirmation": "用户确认",
};

const STAGE_BADGE_COLORS: Record<string, string> = {
  "task-intelligence": "bg-amber-100 text-amber-700",
  "geometry-preflight": "bg-blue-100 text-blue-700",
  "solver-dispatch": "bg-blue-100 text-blue-700",
  "result-reporting": "bg-green-100 text-green-700",
  "supervisor-review": "bg-purple-100 text-purple-700",
  "user-confirmation": "bg-orange-100 text-orange-700",
};

function StageBadge({ stage }: { stage: string }) {
  return (
    <span
      className={cn(
        "rounded-full px-2.5 py-0.5 text-[11px] font-semibold",
        STAGE_BADGE_COLORS[stage] ?? "bg-stone-100 text-stone-600",
      )}
    >
      ● {STAGE_LABELS[stage] ?? stage}
    </span>
  );
}

function SimReqTags({ reqs }: { reqs: SubmarineSimulationRequirements }) {
  const tags: string[] = [];
  if (reqs.inlet_velocity_mps != null)
    tags.push(`${reqs.inlet_velocity_mps} m/s`);
  if (tags.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((t) => (
        <span
          key={t}
          className="rounded-full bg-stone-100 px-2.5 py-1 text-[11px] font-medium text-stone-500"
        >
          {t}
        </span>
      ))}
    </div>
  );
}

function WorkbenchFocusTile({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-stone-200/80 bg-stone-50/80 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-400">
        {label}
      </div>
      <div className="mt-1 text-sm font-medium leading-6 text-stone-700">
        {value}
      </div>
    </div>
  );
}

function WorkbenchStatCard({
  label,
  value,
  meta,
}: {
  label: string;
  value: string;
  meta: string;
}) {
  return (
    <div className="rounded-xl border border-stone-200/80 bg-white px-3.5 py-3 shadow-[0_8px_24px_rgba(15,23,42,0.05)]">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-400">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-tight text-stone-900">
        {value}
      </div>
      <div className="mt-1 text-xs text-stone-500">{meta}</div>
    </div>
  );
}
