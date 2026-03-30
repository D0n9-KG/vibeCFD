# VibeCFD Submarine Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `SubmarineRuntimePanel` with a new 4-pane workbench (`SubmarinePipeline`) that shows an Activity Bar, resizable sidebar with run list + stage nav, a stage pipeline in the center, and a Claude Code chat rail on the right.

**Architecture:** `SubmarinePipeline` owns the full-height layout via `react-resizable-panels`. It reads runtime state through `useThread()` (same as the current panel) and accepts chat-rail props from page.tsx. Five stage cards render in order; the active card is auto-expanded and non-collapsible.

**Tech Stack:** Next.js 16, React 19, TypeScript 5.8, Tailwind CSS 4, react-resizable-panels, node:test (utility tests only)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `src/app/workspace/submarine/submarine-pipeline-layout.ts` | Create | Panel size defaults, min/max constants, localStorage storage keys |
| `src/app/workspace/submarine/submarine-pipeline-layout.test.ts` | Create | node:test unit tests for layout constants |
| `src/components/workspace/submarine-stage-card.tsx` | Create | Shared collapsible card shell (done/active/pending states) |
| `src/components/workspace/submarine-pipeline-sidebar.tsx` | Create | Left sidebar: run list + stage nav mini-list + new simulation button |
| `src/components/workspace/submarine-convergence-chart.tsx` | Create | SVG Cd convergence sparkline with area fill + convergence marker |
| `src/components/workspace/submarine-stage-cards.tsx` | Create | Five stage-specific card components (one per RuntimeStage in STAGE_ORDER) |
| `src/components/workspace/submarine-pipeline.tsx` | Create | Main container: Activity Bar + ResizablePanelGroup (sidebar + center + chat) |
| `src/app/workspace/submarine/[thread_id]/page.tsx` | Modify | Replace CSS-grid layout with `<SubmarinePipeline>` |

---

## Task 1: Layout Constants Utility

**Files:**
- Create: `src/app/workspace/submarine/submarine-pipeline-layout.ts`
- Create: `src/app/workspace/submarine/submarine-pipeline-layout.test.ts`

- [ ] **Step 1: Create `submarine-pipeline-layout.ts`**

```typescript
// src/app/workspace/submarine/submarine-pipeline-layout.ts

export const PIPELINE_SIDEBAR_MIN_PCT = 10;   // ~140px at 1400px wide
export const PIPELINE_SIDEBAR_DEFAULT_PCT = 14; // ~192px
export const PIPELINE_SIDEBAR_MAX_PCT = 22;   // ~308px

export const PIPELINE_CHAT_MIN_PCT = 16;   // ~220px
export const PIPELINE_CHAT_DEFAULT_PCT = 22; // ~300px
export const PIPELINE_CHAT_MAX_PCT = 32;   // ~448px

export const PIPELINE_STORAGE_KEY_SIDEBAR = "submarine-pipeline-sidebar-size";
export const PIPELINE_STORAGE_KEY_CHAT = "submarine-pipeline-chat-size";

export type PipelineLayoutConfig = {
  sidebarDefaultPct: number;
  sidebarMinPct: number;
  sidebarMaxPct: number;
  chatDefaultPct: number;
  chatMinPct: number;
  chatMaxPct: number;
  sidebarStorageKey: string;
  chatStorageKey: string;
};

export function getPipelineLayoutConfig(): PipelineLayoutConfig {
  return {
    sidebarDefaultPct: PIPELINE_SIDEBAR_DEFAULT_PCT,
    sidebarMinPct: PIPELINE_SIDEBAR_MIN_PCT,
    sidebarMaxPct: PIPELINE_SIDEBAR_MAX_PCT,
    chatDefaultPct: PIPELINE_CHAT_DEFAULT_PCT,
    chatMinPct: PIPELINE_CHAT_MIN_PCT,
    chatMaxPct: PIPELINE_CHAT_MAX_PCT,
    sidebarStorageKey: PIPELINE_STORAGE_KEY_SIDEBAR,
    chatStorageKey: PIPELINE_STORAGE_KEY_CHAT,
  };
}
```

- [ ] **Step 2: Create `submarine-pipeline-layout.test.ts`**

```typescript
// src/app/workspace/submarine/submarine-pipeline-layout.test.ts
import assert from "node:assert/strict";
import test from "node:test";

const {
  getPipelineLayoutConfig,
  PIPELINE_SIDEBAR_MIN_PCT,
  PIPELINE_SIDEBAR_DEFAULT_PCT,
  PIPELINE_SIDEBAR_MAX_PCT,
  PIPELINE_CHAT_MIN_PCT,
  PIPELINE_CHAT_DEFAULT_PCT,
  PIPELINE_CHAT_MAX_PCT,
  PIPELINE_STORAGE_KEY_SIDEBAR,
  PIPELINE_STORAGE_KEY_CHAT,
} = await import(
  new URL("./submarine-pipeline-layout.ts", import.meta.url).href
);

void test("getPipelineLayoutConfig returns complete config", () => {
  const config = getPipelineLayoutConfig();
  assert.equal(config.sidebarDefaultPct, PIPELINE_SIDEBAR_DEFAULT_PCT);
  assert.equal(config.sidebarMinPct, PIPELINE_SIDEBAR_MIN_PCT);
  assert.equal(config.sidebarMaxPct, PIPELINE_SIDEBAR_MAX_PCT);
  assert.equal(config.chatDefaultPct, PIPELINE_CHAT_DEFAULT_PCT);
  assert.equal(config.chatMinPct, PIPELINE_CHAT_MIN_PCT);
  assert.equal(config.chatMaxPct, PIPELINE_CHAT_MAX_PCT);
  assert.equal(config.sidebarStorageKey, PIPELINE_STORAGE_KEY_SIDEBAR);
  assert.equal(config.chatStorageKey, PIPELINE_STORAGE_KEY_CHAT);
});

void test("sidebar default is within min-max range", () => {
  assert.ok(PIPELINE_SIDEBAR_DEFAULT_PCT > PIPELINE_SIDEBAR_MIN_PCT);
  assert.ok(PIPELINE_SIDEBAR_DEFAULT_PCT < PIPELINE_SIDEBAR_MAX_PCT);
});

void test("chat default is within min-max range", () => {
  assert.ok(PIPELINE_CHAT_DEFAULT_PCT > PIPELINE_CHAT_MIN_PCT);
  assert.ok(PIPELINE_CHAT_DEFAULT_PCT < PIPELINE_CHAT_MAX_PCT);
});

void test("storage keys are distinct strings", () => {
  assert.notEqual(PIPELINE_STORAGE_KEY_SIDEBAR, PIPELINE_STORAGE_KEY_CHAT);
  assert.equal(typeof PIPELINE_STORAGE_KEY_SIDEBAR, "string");
  assert.equal(typeof PIPELINE_STORAGE_KEY_CHAT, "string");
});
```

- [ ] **Step 3: Run tests**

```powershell
cd C:\Users\D0n9\Desktop\颠覆性大赛\frontend
node --experimental-strip-types src/app/workspace/submarine/submarine-pipeline-layout.test.ts
```

Expected: all 4 tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/app/workspace/submarine/submarine-pipeline-layout.ts src/app/workspace/submarine/submarine-pipeline-layout.test.ts
git commit -m "feat: add submarine pipeline layout constants"
```

---

## Task 2: StageCard Shell Component

**Files:**
- Create: `src/components/workspace/submarine-stage-card.tsx`

- [ ] **Step 1: Write `submarine-stage-card.tsx`**

```tsx
// src/components/workspace/submarine-stage-card.tsx
"use client";

import { ChevronDownIcon, ChevronUpIcon } from "lucide-react";
import { useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export type StageCardState = "done" | "active" | "pending";

export interface StageCardProps {
  state: StageCardState;
  index: number;
  name: string;
  description?: string;
  timeLabel?: string;
  rightLabel?: ReactNode;
  children?: ReactNode;
  defaultExpanded?: boolean;
  className?: string;
}

export function StageCard({
  state,
  index,
  name,
  description,
  timeLabel,
  rightLabel,
  children,
  defaultExpanded,
  className,
}: StageCardProps) {
  const [expanded, setExpanded] = useState(
    defaultExpanded ?? state === "active",
  );

  const canToggle = state !== "active" && children != null;
  const showBody = (state === "active" || expanded) && children != null;

  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-stone-200",
        className,
      )}
    >
      {/* Header */}
      <div
        className={cn(
          "flex items-center gap-3 px-3.5 py-2.5",
          state === "done" && "bg-green-50",
          state === "active" &&
            "border-l-[3px] border-l-blue-500 bg-blue-50",
          state === "pending" && "bg-stone-50",
          canToggle && "cursor-pointer select-none",
        )}
        onClick={canToggle ? () => setExpanded((v) => !v) : undefined}
      >
        {/* Icon */}
        <StageIcon state={state} index={index} />

        {/* Info */}
        <div className="min-w-0 flex-1">
          <div
            className={cn(
              "text-[13px] font-semibold",
              state === "pending" && "text-stone-400",
              state === "active" && "text-stone-900",
              state === "done" && "text-stone-900",
            )}
          >
            {name}
          </div>
          {description && (
            <div className="mt-0.5 truncate text-[11px] text-stone-500">
              {description}
            </div>
          )}
        </div>

        {/* Right area */}
        <div className="flex shrink-0 items-center gap-2">
          {rightLabel}
          {timeLabel && (
            <span className="text-[11px] text-stone-400">{timeLabel}</span>
          )}
          {canToggle && (
            <span className="text-stone-400">
              {expanded ? (
                <ChevronUpIcon className="size-3.5" />
              ) : (
                <ChevronDownIcon className="size-3.5" />
              )}
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      {showBody && (
        <div className="border-t border-stone-200 bg-white px-3.5 py-3">
          {children}
        </div>
      )}
    </div>
  );
}

function StageIcon({
  state,
  index,
}: {
  state: StageCardState;
  index: number;
}) {
  if (state === "done") {
    return (
      <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-green-500 text-[10px] font-bold text-white">
        ✓
      </div>
    );
  }
  if (state === "active") {
    return (
      <div className="flex size-5 shrink-0 animate-pulse items-center justify-center rounded-full bg-blue-500 text-[10px] font-bold text-white">
        ●
      </div>
    );
  }
  return (
    <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-stone-200 text-[10px] font-bold text-stone-400">
      {index}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/workspace/submarine-stage-card.tsx
git commit -m "feat: add StageCard shell for submarine pipeline"
```

---

## Task 3: SubmarinePipelineSidebar

**Files:**
- Create: `src/components/workspace/submarine-pipeline-sidebar.tsx`

The sidebar receives the run list (from parent via `useThreads()`) and the current stage index. It renders:
1. Brand header: VibeCFD · DeerFlow
2. Run list (current thread highlighted)
3. Stage mini-nav (5 stages with colored dots)
4. Footer: "＋ 新建仿真"

- [ ] **Step 1: Write `submarine-pipeline-sidebar.tsx`**

```tsx
// src/components/workspace/submarine-pipeline-sidebar.tsx
"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { cn } from "@/lib/utils";

// RuntimeStage values in order
const STAGE_ORDER = [
  "task-intelligence",
  "geometry-preflight",
  "solver-dispatch",
  "result-reporting",
  "supervisor-review",
] as const;

const STAGE_LABELS: Record<string, string> = {
  "task-intelligence": "任务理解",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解执行",
  "result-reporting": "结果整理",
  "supervisor-review": "Supervisor 复核",
};

export interface SidebarRunItem {
  threadId: string;
  title: string;
  isRunning: boolean;
  isComplete: boolean;
}

interface SubmarinePipelineSidebarProps {
  currentThreadId: string;
  currentStage?: string | null;
  runs: SidebarRunItem[];
  onStageClick: (stageId: string) => void;
  onNewSimulation: () => void;
}

export function SubmarinePipelineSidebar({
  currentThreadId,
  currentStage,
  runs,
  onStageClick,
  onNewSimulation,
}: SubmarinePipelineSidebarProps) {
  const router = useRouter();

  const handleRunClick = useCallback(
    (threadId: string) => {
      router.push(`/workspace/submarine/${threadId}`);
    },
    [router],
  );

  const currentStageIndex = currentStage
    ? STAGE_ORDER.indexOf(currentStage as (typeof STAGE_ORDER)[number])
    : -1;

  return (
    <div className="flex h-full flex-col overflow-hidden bg-stone-50">
      {/* Brand header */}
      <div className="border-b border-stone-200 px-3 py-3">
        <div className="text-[14px] font-extrabold tracking-tight text-sky-500">
          VibeCFD{" "}
          <span className="text-[10px] font-normal text-stone-400">
            · DeerFlow
          </span>
        </div>
      </div>

      {/* Run list */}
      <div className="px-2.5 pb-1 pt-2">
        <div className="mb-1 px-1.5 text-[10px] font-semibold uppercase tracking-widest text-stone-400">
          仿真任务
        </div>
        {runs.length === 0 && (
          <div className="px-1.5 py-2 text-[11px] text-stone-400">
            暂无仿真任务
          </div>
        )}
        {runs.map((run) => (
          <div
            key={run.threadId}
            className={cn(
              "mx-0.5 my-0.5 cursor-pointer rounded-md px-2 py-1.5 text-[12px]",
              run.threadId === currentThreadId
                ? "bg-sky-100 font-semibold text-sky-700"
                : "text-stone-500 hover:bg-stone-100",
            )}
            onClick={() => handleRunClick(run.threadId)}
          >
            <div className="truncate">{run.title || run.threadId.slice(0, 8)}</div>
            <div
              className={cn(
                "mt-0.5 text-[10px]",
                run.threadId === currentThreadId
                  ? "text-sky-400"
                  : "text-stone-400",
              )}
            >
              {run.isRunning ? "● 运行中" : run.isComplete ? "✓ 已完成" : "○ 待运行"}
            </div>
          </div>
        ))}
      </div>

      {/* Stage mini-nav */}
      <div className="flex-1 overflow-y-auto px-2.5 pb-1 pt-2">
        <div className="mb-1 px-1.5 text-[10px] font-semibold uppercase tracking-widest text-stone-400">
          当前阶段
        </div>
        <div className="space-y-0.5 px-1">
          {STAGE_ORDER.map((stageId, idx) => {
            const isDone = currentStageIndex > idx;
            const isActive = currentStageIndex === idx;
            return (
              <button
                key={stageId}
                type="button"
                className={cn(
                  "flex w-full items-center gap-1.5 rounded px-1.5 py-1 text-[11px] text-left hover:bg-stone-100",
                  isActive && "bg-sky-100 font-semibold text-sky-700",
                )}
                onClick={() => onStageClick(stageId)}
              >
                <span
                  className={cn(
                    "inline-block size-[7px] shrink-0 rounded-full",
                    isDone && "bg-green-500",
                    isActive && "animate-pulse bg-sky-500",
                    !isDone && !isActive && "bg-stone-300",
                  )}
                />
                {STAGE_LABELS[stageId]}
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-stone-200 p-2.5">
        <button
          type="button"
          className="w-full rounded-md bg-sky-500 py-1.5 text-[12px] font-semibold text-white hover:bg-sky-600"
          onClick={onNewSimulation}
        >
          ＋ 新建仿真
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/workspace/submarine-pipeline-sidebar.tsx
git commit -m "feat: add SubmarinePipelineSidebar with run list and stage nav"
```

---

## Task 4: SubmarineConvergenceChart

**Files:**
- Create: `src/components/workspace/submarine-convergence-chart.tsx`

Pure SVG chart; no external libraries.

- [ ] **Step 1: Write `submarine-convergence-chart.tsx`**

```tsx
// src/components/workspace/submarine-convergence-chart.tsx
"use client";

interface SubmarineConvergenceChartProps {
  /** Array of Cd values; index 0 = first iteration */
  values: number[];
  /** Width of the SVG (CSS, default "100%") */
  width?: string | number;
  /** Height of the SVG in px (default 56) */
  height?: number;
  /** Index at which convergence was detected (-1 = none) */
  convergenceIndex?: number;
}

const VIEW_W = 300;
const VIEW_H = 56;
const PAD_TOP = 4;
const PAD_BTM = 6;
const PLOT_H = VIEW_H - PAD_TOP - PAD_BTM;

function normalize(values: number[]): number[] {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;
  if (range === 0) return values.map(() => 0.5);
  return values.map((v) => (v - min) / range);
}

export function SubmarineConvergenceChart({
  values,
  width = "100%",
  height = 56,
  convergenceIndex = -1,
}: SubmarineConvergenceChartProps) {
  if (values.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-[10px] text-stone-400"
        style={{ height }}
      >
        暂无收敛数据
      </div>
    );
  }

  const norm = normalize(values);
  const n = norm.length;

  // Build polyline points (inverted Y so high value = tall)
  const points = norm
    .map((v, i) => {
      const x = (i / (n - 1)) * VIEW_W;
      const y = PAD_TOP + (1 - v) * PLOT_H;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  // Area path: polyline + bottom-right + bottom-left
  const areaPoints = `${points} ${VIEW_W},${VIEW_H - PAD_BTM} 0,${VIEW_H - PAD_BTM}`;

  // Convergence marker
  const convX =
    convergenceIndex >= 0 && convergenceIndex < n
      ? ((convergenceIndex / (n - 1)) * VIEW_W).toFixed(1)
      : null;

  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      style={{ width, height, display: "block" }}
      aria-hidden
    >
      {/* Area fill */}
      <polygon
        points={areaPoints}
        fill="rgba(59,130,246,0.07)"
        stroke="none"
      />
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke="#3b82f6"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      {/* Baseline */}
      <line
        x1={0}
        y1={VIEW_H - PAD_BTM}
        x2={VIEW_W}
        y2={VIEW_H - PAD_BTM}
        stroke="#e7e5e4"
        strokeWidth="0.5"
      />
      {/* Convergence marker */}
      {convX != null && (
        <>
          <line
            x1={convX}
            y1={0}
            x2={convX}
            y2={VIEW_H - PAD_BTM}
            stroke="#22c55e"
            strokeWidth="0.8"
            strokeDasharray="3,3"
          />
          <text
            x={Number(convX) + 3}
            y={10}
            fill="#22c55e"
            fontSize={7}
            fontFamily="sans-serif"
          >
            收敛
          </text>
        </>
      )}
    </svg>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/workspace/submarine-convergence-chart.tsx
git commit -m "feat: add SubmarineConvergenceChart SVG component"
```

---

## Task 5: Stage-Specific Card Components

**Files:**
- Create: `src/components/workspace/submarine-stage-cards.tsx`

Five cards: `TaskIntelligenceCard`, `GeometryPreflightCard`, `SolverDispatchCard`, `ResultReportingCard`, `SupervisorReviewCard`.

Each card receives the `SubmarineRuntimeSnapshot`, relevant artifact payloads, and the `sendMessage` callback for interactive stages.

- [ ] **Step 1: Write `submarine-stage-cards.tsx`**

```tsx
// src/components/workspace/submarine-stage-cards.tsx
"use client";

import { useCallback, useState } from "react";

import { cn } from "@/lib/utils";

import { SubmarineConvergenceChart } from "./submarine-convergence-chart";
import { type StageCardState, StageCard } from "./submarine-stage-card";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineSolverMetrics,
  SubmarineDispatchPayload,
  SubmarineGeometryPayload,
} from "./submarine-runtime-panel.contract";

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
  const simReq = brief?.simulation_requirements ?? snapshot?.simulation_requirements;
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

  // Metrics — SubmarineSolverMetrics exposes latest_force_coefficients["Cd"]
  const cd = solverMetrics?.latest_force_coefficients?.["Cd"] ?? null;
  const fx = solverMetrics?.latest_force_coefficients?.["Fx"] ?? null;

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
  const cd = reportSolverMetrics?.latest_force_coefficients?.["Cd"] ?? null;
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
          {(finalReport as Record<string, unknown>).summary_zh as string ?? ""}
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

function InfoRow({
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
```

- [ ] **Step 2: Run type check**

```powershell
cd C:\Users\D0n9\Desktop\颠覆性大赛\frontend
pnpm typecheck 2>&1 | Select-Object -First 40
```

Fix any type errors before continuing.

- [ ] **Step 3: Commit**

```bash
git add src/components/workspace/submarine-stage-cards.tsx
git commit -m "feat: add submarine stage card components (5 stages)"
```

---

## Task 6: (Removed — Activity Bar is already in WorkspaceLayout)

The existing `WorkspaceSidebar` (rendered by `WorkspaceLayout`) already handles workbench switching between VibeCFD / Skill Studio / 通用对话 via `WorkspaceNavChatList`. Adding a duplicate Activity Bar inside `SubmarinePipeline` would create a nested navigation shell that conflicts with the existing `SidebarProvider`.

**Decision:** No Activity Bar in `SubmarinePipeline`. The submarine-specific sidebar (run list + stage nav) is sufficient. Workbench navigation remains in the existing `WorkspaceSidebar`.

---

## Task 7: SubmarinePipeline Main Container

**Files:**
- Create: `src/components/workspace/submarine-pipeline.tsx`

This is the main component that replaces `SubmarineRuntimePanel`. It contains:
- `ResizablePanelGroup` (orientation="horizontal") with: submarine sidebar, center (stage pipeline), and chat rail panels
- `chatOpen` state for < xl responsive collapse (same pattern as the existing workbench)
- `useThreads()` for the sidebar run list (filtered to submarine threads)
- `onLayoutChanged` on the Group for panel size persistence to localStorage
- Reads runtime data from `useThread()` just like the existing panel

- [ ] **Step 1: Write `submarine-pipeline.tsx`**

```tsx
// src/components/workspace/submarine-pipeline.tsx
"use client";

import { useCallback, useMemo, useRef, useState } from "react";

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
} from "./submarine-runtime-panel.contract";
import {
  buildSubmarineTrendSeries,
} from "./submarine-runtime-panel.trends";
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
  type PipelineLayoutConfig,
} from "../../app/workspace/submarine/submarine-pipeline-layout";

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
  simulation_requirements?: Record<string, number | null> | null;
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
  sendMessage,
  onStop,
}: SubmarinePipelineProps) {
  const { thread } = useThread();
  const [settings, setSettings] = useLocalSettings();
  const layoutConfig = useMemo(() => getPipelineLayoutConfig(), []);
  const centerRef = useRef<HTMLDivElement>(null);

  // ── Responsive chat toggle (mirrors existing workbench pattern) ────────────
  const [chatOpen, setChatOpen] = useState(true);

  // ── Run list from useThreads (filter submarine threads) ───────────────────
  const { data: allThreads = [] } = useThreads({ limit: 30 }, isMock);
  const runs = useMemo<SidebarRunItem[]>(() => {
    return allThreads
      .filter((t) =>
        Array.isArray(t.values?.artifacts)
          ? (t.values.artifacts as string[]).some((p) =>
              p.includes("/submarine/") && !p.includes("/submarine/skill-studio/"),
            )
          : t.values?.submarine_runtime != null,
      )
      .map((t) => ({
        threadId: t.thread_id,
        title: (t.values?.title as string | undefined) ?? "",
        isRunning: t.values?.submarine_runtime != null && !t.values?.is_complete,
        isComplete: Boolean(t.values?.is_complete),
      }));
  }, [allThreads]);

  // ── Layout persistence ────────────────────────────────────────────────────
  const defaultLayout = useMemo(
    () => ({
      sidebar: loadStoredPct(PIPELINE_STORAGE_KEY_SIDEBAR, layoutConfig.sidebarDefaultPct),
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
      execution_plan: runtime.execution_plan,
      activity_timeline: runtime.activity_timeline,
    };
  }, [runtime]);

  // ── Callbacks ─────────────────────────────────────────────────────────────
  const handleSend = useCallback(
    (tid: string, message: { role: "human"; content: string }) => {
      void sendMessage(tid, message as PromptInputMessage);
    },
    [sendMessage],
  );

  const handleSubmit = useCallback(
    (message: PromptInputMessage) => {
      void sendMessage(threadId, message);
    },
    [sendMessage, threadId],
  );

  const handleStageClick = useCallback((stageId: string) => {
    const el = document.getElementById(`submarine-stage-${stageId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const handleNewSimulation = useCallback(() => {
    history.pushState(null, "", "/workspace/submarine/new");
    window.location.href = "/workspace/submarine/new";
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────
  // xl+ : 3 panes (sidebar + center + chat)
  // < xl : single column — center only, chat toggle button in header
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      {/* < xl header with chat toggle */}
      <div className="flex shrink-0 items-center gap-2 border-b border-stone-200 px-4 py-2 xl:hidden">
        <span className="flex-1 truncate text-[13px] font-semibold text-stone-900">
          {thread.title ?? "仿真任务"}
        </span>
        <button
          type="button"
          className="rounded-md border border-stone-200 px-3 py-1 text-[12px] text-stone-600 hover:bg-stone-50"
          onClick={() => setChatOpen((v) => !v)}
        >
          {chatOpen ? "收起聊天" : "展开聊天"}
        </button>
      </div>

      {/* 3-pane resizable layout — full height on xl, flex column on mobile */}
      <div className="min-h-0 flex-1 xl:hidden">
        {/* Mobile: center always visible, chat rail below toggle */}
        <div className="flex h-full flex-col overflow-hidden">
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
  handleSend: (tid: string, message: { role: "human"; content: string }) => void;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Center header — xl only (mobile header is in parent) */}
      <div className="hidden shrink-0 items-center gap-2.5 border-b border-stone-200 px-4 py-2.5 xl:flex">
        <span className="text-[14px] font-bold text-stone-900">
          {thread.title ?? "仿真任务"}
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
        <div id="submarine-stage-task-intelligence">
          <TaskIntelligenceCard
            threadId={threadId}
            snapshot={stageSnapshot}
            designBrief={designBrief}
            onConfirm={handleSend}
          />
        </div>
        <div id="submarine-stage-geometry-preflight">
          <GeometryPreflightCard snapshot={stageSnapshot} geometry={geometry} />
        </div>
        <div id="submarine-stage-solver-dispatch">
          <SolverDispatchCard
            snapshot={stageSnapshot}
            solverMetrics={solverMetrics}
            trendValues={trendValues}
          />
        </div>
        <div id="submarine-stage-result-reporting">
          <ResultReportingCard
            snapshot={stageSnapshot}
            finalReport={finalReport}
            solverMetrics={solverMetrics}
            reportVirtualPath={runtime?.report_virtual_path}
          />
        </div>
        <div id="submarine-stage-supervisor-review">
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

function SimReqTags({
  reqs,
}: {
  reqs: Record<string, number | null>;
}) {
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
```

- [ ] **Step 2: Run type check**

```powershell
cd C:\Users\D0n9\Desktop\颠覆性大赛\frontend
pnpm typecheck 2>&1 | Select-Object -First 60
```

Fix any type errors before continuing.

- [ ] **Step 3: Commit**

```bash
git add src/components/workspace/submarine-pipeline.tsx
git commit -m "feat: add SubmarinePipeline 4-pane workbench container"
```

---

## Task 8: Export from barrel (if applicable)

**Files:**
- Modify: `src/components/workspace/index.ts` (if it exists and exports workspace components)

- [ ] **Step 1: Check if barrel file exists**

```powershell
Get-Content "C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\workspace\index.ts" -ErrorAction SilentlyContinue | Select-Object -First 5
```

If the file doesn't exist or doesn't export workspace components, skip this task. If it does export them, add:

```typescript
export { SubmarinePipeline } from "./submarine-pipeline";
```

- [ ] **Step 2: Commit (only if barrel was modified)**

```bash
git add src/components/workspace/index.ts
git commit -m "feat: export SubmarinePipeline from workspace barrel"
```

---

## Task 9: Wire Up in page.tsx

**Files:**
- Modify: `src/app/workspace/submarine/[thread_id]/page.tsx`

Replace the CSS-grid layout with `SubmarinePipeline`. The existing `<header>` bar, `ThreadContext.Provider`, `ChatBox`, and all hook calls in the page component are preserved. The `<main>` section's inner grid is replaced.

- [ ] **Step 1: Read current page.tsx to find exact replacement boundaries**

Read lines 143–254 of page.tsx to identify the exact `return` block structure before editing.

- [ ] **Step 2: Add import for SubmarinePipeline**

In `src/app/workspace/submarine/[thread_id]/page.tsx`, replace:
```typescript
import { SubmarineRuntimePanel } from "@/components/workspace/submarine-runtime-panel";
```
with:
```typescript
import { SubmarinePipeline } from "@/components/workspace/submarine-pipeline";
```

Also remove the import of `getSubmarineWorkbenchLayout`:
```typescript
import { getSubmarineWorkbenchLayout } from "../submarine-workbench-layout";
```

- [ ] **Step 3: Remove the layout useMemo**

Remove:
```typescript
  const layout = useMemo(
    () => getSubmarineWorkbenchLayout({ chatOpen }),
    [chatOpen],
  );
```

**Keep** `chatOpen` / `setChatOpen` / `focusChatRail` — `SubmarinePipeline` accepts `chatOpen`/`onChatOpenChange` props so the existing page-level toggle button in the header can still drive it (see Step 4).

**Important:** Keep `handleSubmit`, `handleStop`, `isUploading`, `isNewThread`, `thread`, `sendMessage`, `settings`, `setSettings`, `showNotification`, `setArtifactsOpen`.

- [ ] **Step 4: Replace the return block's main content**

Replace the entire `<main className="min-h-0 flex-1 overflow-hidden pt-14">` block with:

```tsx
          <main className="min-h-0 flex-1 overflow-hidden">
            <SubmarinePipeline
              threadId={threadId}
              isNewThread={isNewThread}
              isUploading={isUploading}
              isMock={isMock}
              chatOpen={chatOpen}
              onChatOpenChange={setChatOpen}
              sendMessage={sendMessage}
              onStop={handleStop}
            />
          </main>
```

The existing header `<Button>` that calls `setChatOpen` stays. It now drives `SubmarinePipeline`'s responsive chat toggle via the `chatOpen`/`onChatOpenChange` props.

**Also update `SubmarinePipelineProps` in `submarine-pipeline.tsx`** to accept these two new props and thread them down to the internal state initializer:

```tsx
interface SubmarinePipelineProps {
  threadId: string;
  isNewThread: boolean;
  isUploading: boolean;
  isMock?: boolean;
  chatOpen?: boolean;             // controlled from page
  onChatOpenChange?: (v: boolean) => void;
  sendMessage: ...;
  onStop: ...;
}
```

And change the `chatOpen` state line in the component body:
```tsx
  const [chatOpenInternal, setChatOpenInternal] = useState(true);
  const chatOpen = props.chatOpen ?? chatOpenInternal;
  const setChatOpen = props.onChatOpenChange ?? setChatOpenInternal;
```

**Note:** `SubmarineLaunchpad` in page.tsx is no longer needed — its "start a conversation" prompt is replaced by the inline chat rail's `isNewThread` autoFocus. Remove it and its helper components (`RuntimePlaceholder`, `CollaborationStep`) from page.tsx.

- [ ] **Step 5: Run type check and lint**

```powershell
cd C:\Users\D0n9\Desktop\颠覆性大赛\frontend
pnpm check 2>&1 | Select-Object -First 80
```

Fix all errors and warnings.

- [ ] **Step 6: Quick visual check in dev server**

```powershell
# In a separate terminal
pnpm dev
```

Navigate to `http://localhost:3000/workspace/submarine/new` and verify:
- Existing WorkspaceSidebar still shows on the left (no duplicate shell)
- Submarine sidebar shows "VibeCFD · DeerFlow" brand + stage nav + new simulation button
- Center shows 5 stage cards
- Right shows Claude Code chat rail
- Resizing any panel persists after page reload (check localStorage for `submarine-pipeline-sidebar-size`)
- On viewport < 1280px: sidebar hidden, chat rail hidden by default, toggle button visible
- Page is not broken

- [ ] **Step 7: Commit**

```bash
git add src/app/workspace/submarine/[thread_id]/page.tsx
git commit -m "feat: wire SubmarinePipeline into submarine workbench page"
```

---

## Task 10: Codex Review + Final Verification

- [ ] **Step 1: Run typecheck (must be clean)**

```powershell
cd C:\Users\D0n9\Desktop\颠覆性大赛\frontend
pnpm typecheck 2>&1
```

Expected: 0 errors. Fix any before proceeding.

- [ ] **Step 2: Run layout utility tests**

```powershell
node --experimental-strip-types src/app/workspace/submarine/submarine-pipeline-layout.test.ts
```

Expected: 4 tests pass.

- [ ] **Step 3: Run linter**

```powershell
pnpm lint 2>&1 | Select-Object -First 40
```

Fix any lint errors.

- [ ] **Step 4: Submit to Codex for review**

Use the Codex MCP tool (`sandbox="read-only"`) with this prompt:

```
Please review the VibeCFD submarine workbench redesign implementation. The following files were created or modified:

New files:
- src/app/workspace/submarine/submarine-pipeline-layout.ts
- src/app/workspace/submarine/submarine-pipeline-layout.test.ts
- src/components/workspace/submarine-stage-card.tsx
- src/components/workspace/submarine-pipeline-sidebar.tsx
- src/components/workspace/submarine-convergence-chart.tsx
- src/components/workspace/submarine-stage-cards.tsx
- src/components/workspace/submarine-pipeline.tsx

Modified:
- src/app/workspace/submarine/[thread_id]/page.tsx

The design spec is at: docs/superpowers/specs/2026-03-30-vibecfd-frontend-redesign-design.md

Please evaluate:
1. Correctness: Does the implementation match spec section 4 (VibeCFD Workbench layout)?
2. Data pipeline: Are runtime snapshot fields accessed correctly (matching submarine-runtime-panel.tsx patterns)?
3. Interactive stages: Does TaskIntelligenceCard correctly gate pipeline progress via sendMessage?
4. ResizablePanel: Are panel ids, defaultSize, minSize, maxSize consistent with spec section 7.2?
5. TypeScript: Are there any obvious type mismatches or missing imports?
6. Any regressions introduced in page.tsx?
```

- [ ] **Step 5: Address any blocking issues found by Codex**

- [ ] **Step 6: Final commit if any fixes were made**

```bash
git add -A
git commit -m "fix: address Codex review findings for submarine pipeline"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Covered by |
|-------------|-----------|
| 3.1 Shell structure (3 panes inside workbench) | SubmarinePipeline ResizablePanelGroup (Task 7) |
| 3.2 Activity Bar / workbench navigation | 已有 WorkspaceSidebar + WorkspaceNavChatList，不重复建；Task 6 已移除 |
| 3.3 Color theme (light, stone/sky) | Tailwind classes throughout |
| 4.1 Left sidebar | SubmarinePipelineSidebar (Task 3)；run list 由 useThreads() 在 Task 7 内部查询 |
| 4.2 Center stage cards (5 stages) | submarine-stage-cards.tsx (Task 5) |
| 4.2 task-intelligence interactive | TaskIntelligenceCard + sendMessage (Task 5) |
| 4.2 solver-dispatch Cd chart | SubmarineConvergenceChart + SolverDispatchCard (Tasks 4, 5) |
| 4.2 result-reporting Cd display | ResultReportingCard (Task 5) |
| 4.2 supervisor-review user confirm | SupervisorReviewCard (Task 5) |
| 4.3 Chat rail (220-420px resizable) | ResizablePanel in SubmarinePipeline (Task 7) |
| 6.1 Data sources (useThread, artifacts) | SubmarinePipeline data pipeline (Task 7) |
| 7.1 Navigation rules | chatOpen/onChatOpenChange 桥接 page.tsx 现有 toggle；thread 创建用 history.replaceState（page.tsx 不变） |
| 7.2 Panel width persistence | onLayoutChanged → localStorage；loadStoredPct → defaultLayout（Task 7） |
| 8. Migration boundary (providers preserved) | layout.tsx / WorkspaceLayout 不动；page.tsx 保留 ThreadContext、ChatBox |
| 9. Responsive (xl breakpoint) | < xl 单列 + chatOpen toggle；≥ xl ResizablePanelGroup |

**No placeholders:** 每个 task 的代码均完整，无 TBD。

**Type consistency:** `StageRuntimeSnapshot`（submarine-stage-cards.tsx）是 `SubmarineRuntimeSnapshot`（submarine-pipeline.tsx）的子集，通过 `stageSnapshot` useMemo 映射。`buildSubmarineTrendSeries` 返回 `SubmarineTrendSeries[]`，每条有 `id` + `values: TrendValue[]`，取 `id==="cd"` 的 `.values.map(v => v.value)` 得 `number[]`（已验证 trends.ts 类型）。
