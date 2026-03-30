// src/components/workspace/submarine-pipeline.tsx
"use client";

import { useRouter } from "next/navigation";
import { useCallback, useMemo, useRef } from "react";

import { type PromptInputMessage } from "@/components/ai-elements/prompt-input";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { useLocalSettings } from "@/core/settings";
import { useThreads } from "@/core/threads/hooks";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import { InputBox } from "./input-box";
import { MessageList } from "./messages";
import { useThread } from "./messages/context";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineSolverMetrics,
  SubmarineGeometryPayload,
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
import {
  type SidebarRunItem,
  SubmarinePipelineSidebar,
} from "./submarine-pipeline-sidebar";
import {
  getPipelineLayoutConfig,
  PIPELINE_STORAGE_KEY_SIDEBAR,
  PIPELINE_STORAGE_KEY_CHAT,
} from "@/app/workspace/submarine/submarine-pipeline-layout";

// ── Persistence helpers ───────────────────────────────────────────────────────

function loadStoredPct(key: string, fallback: number): number {
  if (typeof window === "undefined") return fallback;
  const raw = window.localStorage.getItem(key);
  if (!raw) return fallback;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 && n < 100 ? n : fallback;
}

// ── Runtime snapshot type (mirrors SubmarineRuntimePanel) ────────────────────
type SubmarineRuntimeSnapshot = {
  current_stage?: string | null;
  task_summary?: string | null;
  task_type?: string | null;
  geometry_virtual_path?: string | null;
  geometry_family?: string | null;
  selected_case_id?: string | null;
  simulation_requirements?: SubmarineSimulationRequirements | null;
  stage_status?: string | null;
  review_status?: string | null;
  scientific_gate_status?: string | null;
  allowed_claim_level?: string | null;
  scientific_gate_virtual_path?: string | null;
  next_recommended_stage?: string | null;
  report_virtual_path?: string | null;
  artifact_virtual_paths?: string[];
  execution_plan?: Array<{
    role_id?: string | null;
    owner?: string | null;
    goal?: string | null;
    status?: string | null;
    target_skills?: string[] | null;
  }> | null;
  activity_timeline?: Array<{
    stage?: string;
    actor?: string;
    role_id?: string | null;
    title?: string;
    summary?: string;
    status?: string | null;
    skill_names?: string[] | null;
    timestamp?: string | null;
  }> | null;
};

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
  chatOpen = false,
  sendMessage,
  onStop,
}: SubmarinePipelineProps) {
  const router = useRouter();
  const { thread } = useThread();
  const [settings, setSettings] = useLocalSettings();
  const layoutConfig = useMemo(() => getPipelineLayoutConfig(), []);
  // centerRef scopes the xl desktop pane for stage-nav scroll
  const centerRef = useRef<HTMLDivElement>(null);
  // mobileCenterRef scopes the mobile pane separately to avoid duplicate-id querySelector conflicts
  const mobileCenterRef = useRef<HTMLDivElement>(null);

  // ── Run list from useThreads (filter submarine threads) ───────────────────
  const { data: allThreads = [] } = useThreads({ limit: 30 }, isMock);
  const runs = useMemo<SidebarRunItem[]>(() => {
    return allThreads
      .filter((t) =>
        Array.isArray(t.values?.artifacts)
          ? (t.values.artifacts as string[]).some(
              (p) =>
                p.includes("/submarine/") &&
                !p.includes("/submarine/skill-studio/"),
            )
          : t.values?.submarine_runtime != null,
      )
      .map((t) => ({
        threadId: t.thread_id,
        title: (t.values?.title as string | undefined) ?? "",
        isRunning:
          t.values?.submarine_runtime != null && !t.values?.is_complete,
        isComplete: Boolean(t.values?.is_complete),
      }));
  }, [allThreads]);

  // ── Layout persistence ────────────────────────────────────────────────────
  const defaultLayout = useMemo(
    () => ({
      sidebar: loadStoredPct(
        PIPELINE_STORAGE_KEY_SIDEBAR,
        layoutConfig.sidebarDefaultPct,
      ),
      chat: loadStoredPct(PIPELINE_STORAGE_KEY_CHAT, layoutConfig.chatDefaultPct),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on mount
    [],
  );

  const handleLayoutChanged = useCallback(
    (layout: Record<string, number>) => {
      if (typeof layout.sidebar === "number") {
        window.localStorage.setItem(
          PIPELINE_STORAGE_KEY_SIDEBAR,
          String(layout.sidebar),
        );
      }
      if (typeof layout.chat === "number") {
        window.localStorage.setItem(
          PIPELINE_STORAGE_KEY_CHAT,
          String(layout.chat),
        );
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
      ? (thread.values.artifacts as string[])
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
  const solverResultsJson = submarineArtifacts.find((p) =>
    p.endsWith("/solver-results.json"),
  );
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
      current_stage: runtime.current_stage,
      task_summary: runtime.task_summary,
      simulation_requirements: runtime.simulation_requirements,
      stage_status: runtime.stage_status,
      review_status: runtime.review_status,
      scientific_gate_status: runtime.scientific_gate_status,
      allowed_claim_level: runtime.allowed_claim_level,
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
        stage: item.stage,
        actor: item.actor,
        title: item.title,
        summary: item.summary,
        status: item.status,
        timestamp: item.timestamp,
      })) ?? null,
    };
  }, [runtime]);

  // ── Callbacks ─────────────────────────────────────────────────────────────
  // Bridge from stage card { role, content } to PromptInputMessage { text, files }
  const handleSend = useCallback(
    (tid: string, message: { role: "human"; content: string }) => {
      void sendMessage(tid, { text: message.content, files: [] });
    },
    [sendMessage],
  );

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      void sendMessage(threadId, message);
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

  // ── Render ────────────────────────────────────────────────────────────────
  // xl+ : 3 panes (sidebar + center + chat)
  // < xl : single column — center only; chat toggle owned by page.tsx header button
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      {/* 3-pane resizable layout — full height on xl, flex column on mobile */}
      <div className="min-h-0 flex-1 xl:hidden">
        {/* Mobile: center always visible, chat rail below toggle */}
        <div className="flex h-full flex-col overflow-hidden">
          <PipelineCenterPane
            thread={thread}
            runtime={runtime}
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
          {chatOpen && (
            <PipelineChatRail
              thread={thread}
              threadId={threadId}
              isNewThread={isNewThread}
              isUploading={isUploading}
              settings={settings}
              setSettings={setSettings}
              handleSubmit={handleSubmit}
              onStop={onStop}
            />
          )}
        </div>
      </div>

      <ResizablePanelGroup
        orientation="horizontal"
        className="hidden min-h-0 flex-1 xl:flex"
        onLayoutChanged={handleLayoutChanged}
      >
        {/* Sidebar */}
        <ResizablePanel
          id="submarine-pipeline-sidebar"
          defaultSize={defaultLayout.sidebar}
          minSize={layoutConfig.sidebarMinPct}
          maxSize={layoutConfig.sidebarMaxPct}
        >
          <SubmarinePipelineSidebar
            currentThreadId={threadId}
            currentStage={runtime?.current_stage}
            runs={runs}
            onStageClick={handleStageClick}
            onNewSimulation={handleNewSimulation}
          />
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Center — stage pipeline */}
        <ResizablePanel id="submarine-pipeline-center">
          <PipelineCenterPane
            thread={thread}
            runtime={runtime}
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

        <ResizableHandle withHandle />

        {/* Chat rail */}
        <ResizablePanel
          id="submarine-pipeline-chat"
          defaultSize={defaultLayout.chat}
          minSize={layoutConfig.chatMinPct}
          maxSize={layoutConfig.chatMaxPct}
        >
          <PipelineChatRail
            thread={thread}
            threadId={threadId}
            isNewThread={isNewThread}
            isUploading={isUploading}
            settings={settings}
            setSettings={setSettings}
            handleSubmit={handleSubmit}
            onStop={onStop}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

// ── PipelineCenterPane (extracted to avoid JSX duplication between mobile/xl) ─

function PipelineCenterPane({
  thread,
  runtime,
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
  runtime: SubmarineRuntimeSnapshot | null;
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
  ) => void;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Center header — xl only (mobile header is in parent) */}
      <div className="hidden shrink-0 items-center gap-2.5 border-b border-stone-200 px-4 py-2.5 xl:flex">
        <span className="text-[14px] font-bold text-stone-900">
          {thread.values.title ?? "仿真任务"}
        </span>
        {runtime?.current_stage && (
          <StageBadge stage={runtime.current_stage} />
        )}
        {runtime?.simulation_requirements && (
          <SimReqTags reqs={runtime.simulation_requirements} />
        )}
      </div>

      {/* Stage list */}
      <div
        ref={centerRef}
        className="min-h-0 flex-1 space-y-2.5 overflow-y-auto p-3"
      >
        {/* data-stage-id instead of id to avoid duplicate-id issues when both
            mobile and desktop panes are mounted simultaneously */}
        <div data-stage-id="submarine-stage-task-intelligence">
          <TaskIntelligenceCard
            threadId={threadId}
            snapshot={stageSnapshot}
            designBrief={designBrief}
            onConfirm={handleSend}
          />
        </div>
        <div data-stage-id="submarine-stage-geometry-preflight">
          <GeometryPreflightCard snapshot={stageSnapshot} geometry={geometry} />
        </div>
        <div data-stage-id="submarine-stage-solver-dispatch">
          <SolverDispatchCard
            snapshot={stageSnapshot}
            solverMetrics={solverMetrics}
            trendValues={trendValues}
          />
        </div>
        <div data-stage-id="submarine-stage-result-reporting">
          <ResultReportingCard
            snapshot={stageSnapshot}
            finalReport={finalReport}
            solverMetrics={solverMetrics}
            reportVirtualPath={runtime?.report_virtual_path}
          />
        </div>
        <div data-stage-id="submarine-stage-supervisor-review">
          <SupervisorReviewCard
            threadId={threadId}
            snapshot={stageSnapshot}
            onConfirm={handleSend}
          />
        </div>
      </div>
    </div>
  );
}

// ── PipelineChatRail ──────────────────────────────────────────────────────────

function PipelineChatRail({
  thread,
  threadId,
  isNewThread,
  isUploading,
  settings,
  setSettings,
  handleSubmit,
  onStop,
}: {
  thread: ReturnType<typeof useThread>["thread"];
  threadId: string;
  isNewThread: boolean;
  isUploading: boolean;
  settings: ReturnType<typeof useLocalSettings>[0];
  setSettings: ReturnType<typeof useLocalSettings>[1];
  handleSubmit: (message: PromptInputMessage) => void;
  onStop: () => Promise<void>;
}) {
  return (
    <div className="flex min-h-0 flex-col border-l border-stone-200 bg-stone-50 xl:h-full">
      {/* Chat header */}
      <div className="flex shrink-0 items-center gap-2 border-b border-stone-200 px-3.5 py-2.5">
        <span className="inline-block size-[6px] shrink-0 rounded-full bg-green-500" />
        <span className="text-[12px] font-semibold text-stone-800">
          Claude Code
        </span>
      </div>

      {/* Messages */}
      <div className="min-h-0 flex-1 overflow-hidden">
        <MessageList
          className="flex-1 justify-start"
          paddingBottom={32}
          threadId={threadId}
          thread={thread}
        />
      </div>

      {/* Input */}
      <div className="shrink-0 border-t border-stone-200 bg-white p-2.5">
        <InputBox
          className="w-full bg-white"
          isNewThread={isNewThread}
          threadId={threadId}
          autoFocus={isNewThread}
          status={
            thread.error ? "error" : thread.isLoading ? "streaming" : "ready"
          }
          context={settings.context}
          disabled={
            env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isUploading
          }
          onContextChange={(context) => setSettings("context", context)}
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
  "supervisor-review": "Supervisor 复核",
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
    <div className="ml-auto flex gap-2">
      {tags.map((t) => (
        <span key={t} className="text-[11px] text-stone-400">
          {t}
        </span>
      ))}
    </div>
  );
}
