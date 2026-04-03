"use client";

import {
  ClipboardCheckIcon,
  GitBranchPlusIcon,
  LayoutPanelLeftIcon,
  PackageCheckIcon,
  ShieldCheckIcon,
  TestTubeDiagonalIcon,
  WaypointsIcon,
  WandSparklesIcon,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import {
  SkillStudioWorkbenchPanel,
  type SkillStudioGraphFilter,
  type SkillStudioWorkbenchView,
} from "./skill-studio-workbench-panel";

type SkillStudioWorkbenchShellProps = {
  threadId: string;
  assistantLabel: string;
  hasWorkbenchSurface: boolean;
  isNewThread: boolean;
  className?: string;
  onOpenChat: () => void;
};

const SKILL_STUDIO_VIEWS: Array<{
  id: SkillStudioWorkbenchView;
  label: string;
  icon: typeof WandSparklesIcon;
  note: string;
}> = [
  {
    id: "overview",
    label: "鎬昏",
    icon: WandSparklesIcon,
    note: "Readiness, blockers, and next action guidance.",
  },
  {
    id: "build",
    label: "鏋勫缓",
    icon: PackageCheckIcon,
    note: "Package structure, rules, and draft contract.",
  },
  {
    id: "validation",
    label: "鏍￠獙",
    icon: ShieldCheckIcon,
    note: "Validation status, errors, and warnings.",
  },
  {
    id: "test",
    label: "娴嬭瘯",
    icon: TestTubeDiagonalIcon,
    note: "Scenario test matrix and blocking cases.",
  },
  {
    id: "publish",
    label: "鍙戝竷",
    icon: ClipboardCheckIcon,
    note: "Publish gates and enablement actions.",
  },
  {
    id: "graph",
    label: "鍥捐氨",
    icon: GitBranchPlusIcon,
    note: "Focused graph surface and node inspector.",
  },
];

const SKILL_STUDIO_GRAPH_FILTERS: Array<{
  id: SkillStudioGraphFilter;
  label: string;
}> = [
  { id: "all", label: "鍏ㄩ儴" },
  { id: "upstream", label: "涓婃父" },
  { id: "downstream", label: "涓嬫父" },
  { id: "similar", label: "鐩镐技" },
  { id: "high-impact", label: "楂樺奖鍝峘" },
];

export function SkillStudioWorkbenchShell({
  threadId,
  assistantLabel,
  hasWorkbenchSurface,
  isNewThread,
  className,
  onOpenChat,
}: SkillStudioWorkbenchShellProps) {
  const [activeView, setActiveView] =
    useState<SkillStudioWorkbenchView>("overview");
  const [graphFilter, setGraphFilter] =
    useState<SkillStudioGraphFilter>("all");
  const [navOpen, setNavOpen] = useState(false);

  const shouldShowPlaceholder =
    !hasWorkbenchSurface && activeView !== "overview";

  return (
    <div className={cn("min-h-0", className)}>
      <aside className="hidden min-h-0 flex-col overflow-hidden rounded-[28px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,251,235,0.92),rgba(255,255,255,0.96))] p-4 shadow-[0_18px_44px_rgba(120,53,15,0.08)] xl:flex">
        <div className="rounded-2xl border border-amber-100/80 bg-white/92 p-4 shadow-[0_14px_34px_rgba(120,53,15,0.08)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-700">
            Skill Studio
          </div>
          <div className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
            Lifecycle workbench
          </div>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            {assistantLabel} stays dedicated to authoring, validation, dry-run
            preparation, and publish readiness for this thread.
          </p>
        </div>

        <div className="mt-4 rounded-2xl border border-stone-200/80 bg-white/88 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.05)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-stone-400">
            Current agent
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="outline">{assistantLabel}</Badge>
            <Badge variant="outline">
              {hasWorkbenchSurface ? "Artifacts loaded" : "Draft thread"}
            </Badge>
          </div>
        </div>

        <nav className="mt-4 flex-1 space-y-2">
          {SKILL_STUDIO_VIEWS.map((view) => {
            const Icon = view.icon;
            const isActive = activeView === view.id;
            return (
              <button
                key={view.id}
                type="button"
                className={cn(
                  "flex w-full items-start gap-3 rounded-2xl border px-3 py-3 text-left transition-colors",
                  isActive
                    ? "border-amber-200 bg-amber-50 text-stone-950 shadow-[0_10px_24px_rgba(217,119,6,0.12)]"
                    : "border-stone-200/80 bg-white/86 text-stone-700 hover:border-stone-300 hover:bg-white",
                )}
                onClick={() => setActiveView(view.id)}
              >
                <span
                  className={cn(
                    "mt-0.5 rounded-xl border p-2",
                    isActive
                      ? "border-amber-200 bg-white text-amber-700"
                      : "border-stone-200 bg-stone-50 text-stone-500",
                  )}
                >
                  <Icon className="size-4" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold">{view.label}</span>
                  <span className="mt-1 block text-xs leading-5 text-stone-500">
                    {view.note}
                  </span>
                </span>
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="xl:hidden">
        <div className="mb-4 flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={() => setNavOpen((open) => !open)}
          >
            <LayoutPanelLeftIcon className="size-4" />
            {navOpen ? "鏀惰捣鍒嗘爮" : "灞曞紑鍒嗘爮"}
          </Button>
          <Button variant="outline" onClick={onOpenChat}>
            <WaypointsIcon className="size-4" />
            鎵撳紑 Skill Creator 鑱婂ぉ
          </Button>
        </div>

        {navOpen ? (
          <div className="mb-4 rounded-[28px] border border-stone-200/80 bg-white/96 p-4 shadow-[0_18px_44px_rgba(15,23,42,0.07)]">
            <div className="grid gap-3 sm:grid-cols-2">
              {SKILL_STUDIO_VIEWS.map((view) => {
                const Icon = view.icon;
                const isActive = activeView === view.id;
                return (
                  <button
                    key={view.id}
                    type="button"
                    className={cn(
                      "rounded-2xl border px-3 py-3 text-left",
                      isActive
                        ? "border-amber-200 bg-amber-50 text-stone-950"
                        : "border-stone-200 bg-stone-50 text-stone-700",
                    )}
                    onClick={() => {
                      setActiveView(view.id);
                      setNavOpen(false);
                    }}
                  >
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <Icon className="size-4" />
                      {view.label}
                    </div>
                    <div className="mt-1 text-xs leading-5 text-stone-500">
                      {view.note}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>

      <section className="min-h-0 min-w-0 overflow-hidden">
        <div className="mb-4 rounded-[28px] border border-stone-200/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.92),rgba(255,255,255,0.96))] p-5 shadow-[0_18px_44px_rgba(120,53,15,0.08)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
            Skill authoring surface
          </div>
          <div className="mt-3 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0 flex-1">
              <h2 className="text-2xl font-semibold tracking-tight text-stone-900">
                Keep build, validation, testing, publish, and graph review on
                their own dedicated surfaces.
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
                The workbench keeps the chat rail dedicated to {assistantLabel},
                while this center surface stays focused on reviewable skill
                artifacts instead of mixing every panel into one viewport.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{assistantLabel}</Badge>
              <Badge variant="outline">
                {isNewThread ? "New thread" : "Existing thread"}
              </Badge>
              <Badge variant="outline">
                {hasWorkbenchSurface ? "Workbench ready" : "Waiting for first draft"}
              </Badge>
            </div>
          </div>
        </div>

        {activeView === "graph" ? (
          <div className="mb-4 flex flex-wrap gap-2">
            {SKILL_STUDIO_GRAPH_FILTERS.map((filter) => (
              <Button
                key={filter.id}
                variant={graphFilter === filter.id ? "default" : "outline"}
                onClick={() => setGraphFilter(filter.id)}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        ) : null}

        {activeView === "overview" ? (
          <SkillStudioLaunchpad
            assistantLabel={assistantLabel}
            hasWorkbenchSurface={hasWorkbenchSurface}
            isNewThread={isNewThread}
            onOpenChat={onOpenChat}
          />
        ) : null}

        <div className="min-h-0 overflow-hidden">
          {hasWorkbenchSurface ? (
            <SkillStudioWorkbenchPanel
              threadId={threadId}
              view={activeView}
              graphFilter={graphFilter}
            />
          ) : shouldShowPlaceholder ? (
            <SkillStudioPlaceholder assistantLabel={assistantLabel} />
          ) : activeView === "overview" ? (
            <SkillStudioPlaceholder assistantLabel={assistantLabel} />
          ) : null}
        </div>
      </section>
    </div>
  );
}

function SkillStudioLaunchpad({
  assistantLabel,
  hasWorkbenchSurface,
  isNewThread,
  onOpenChat,
}: {
  assistantLabel: string;
  hasWorkbenchSurface: boolean;
  isNewThread: boolean;
  onOpenChat: () => void;
}) {
  return (
    <section className="mb-4 rounded-[28px] border border-stone-200/80 bg-white/94 p-5 shadow-[0_18px_44px_rgba(15,23,42,0.06)]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
        Dedicated collaboration
      </div>
      <div className="mt-3 grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.7fr)]">
        <div>
          <h3 className="text-xl font-semibold tracking-tight text-stone-900">
            Build with a dedicated Skill Creator instead of a generic thread.
          </h3>
          <p className="mt-2 text-sm leading-7 text-stone-600">
            The right rail is reserved for {assistantLabel}, while this
            workbench tracks package structure, validation, scenario tests,
            publish gates, and graph positioning for the current skill.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={onOpenChat}>
              {isNewThread ? "寮€濮嬪叡鍒?Skill" : "缁х画涓?Skill Creator 鍗忎綔"}
            </Button>
          </div>
        </div>

        <div className="rounded-2xl border border-stone-200/80 bg-stone-50/90 p-4">
          <div className="text-sm font-semibold text-stone-900">Workflow</div>
          <div className="mt-3 space-y-3 text-sm leading-6 text-stone-600">
            <div>1. Capture domain rules, triggers, and acceptance criteria.</div>
            <div>2. Review the generated package, validation, and tests.</div>
            <div>3. Publish only after the gates and graph position are clear.</div>
            {hasWorkbenchSurface ? (
              <div>This thread already has workbench artifacts ready for review.</div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function SkillStudioPlaceholder({
  assistantLabel,
}: {
  assistantLabel: string;
}) {
  return (
    <section className="rounded-[28px] border border-dashed border-stone-300 bg-white/80 p-8 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="max-w-3xl">
        <h3 className="text-lg font-semibold text-stone-900">
          Waiting for the first skill package draft
        </h3>
        <p className="mt-3 text-sm leading-7 text-stone-600">
          Start on the right with {assistantLabel}. Once the first draft,
          validation bundle, or publish-readiness artifact lands, this surface
          will switch into the focused lifecycle workbench automatically.
        </p>
      </div>
    </section>
  );
}
