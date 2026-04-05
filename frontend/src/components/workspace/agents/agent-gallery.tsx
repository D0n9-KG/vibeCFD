"use client";

import { BotIcon, Link2Icon, PlusIcon, RadarIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import {
  WorkspaceSurfaceCard,
  WorkspaceSurfaceMain,
  WorkspaceSurfacePage,
} from "@/components/workspace/workspace-container";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { useAgents } from "@/core/agents";
import { useI18n } from "@/core/i18n/hooks";

import { AgentCard } from "./agent-card";

type AgentGalleryProps = {
  surfaceLabel?: string;
};

export function AgentGallery({ surfaceLabel }: AgentGalleryProps) {
  const { t } = useI18n();
  const { agents, isLoading, error } = useAgents();
  const router = useRouter();
  const resolvedSurfaceLabel = surfaceLabel ?? t.agents.title;

  useEffect(() => {
    document.title = `${t.agents.title} - ${t.pages.appName}`;
  }, [t.agents.title, t.pages.appName]);

  const handleNewAgent = () => {
    router.push("/workspace/agents/new");
  };

  return (
    <WorkspaceSurfacePage
      className="workspace-agent-gallery"
      data-surface-label={resolvedSurfaceLabel}
    >
      <WorkspaceSurfaceMain className="max-w-[1840px]">
        <WorkspaceSurfaceCard className="overflow-hidden">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
            <div className="min-w-0">
              <div className="workspace-kicker text-cyan-700 dark:text-cyan-300">
                Agent Catalog
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
                {t.agents.title}
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700 dark:text-slate-300">
                {t.agents.description}
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                <div className="metric-chip">
                  <BotIcon className="size-3.5" />
                  {t.common.agentCount(agents.length)}
                </div>
                <div className="metric-chip">
                  <Link2Icon className="size-3.5" />
                  {
                    agents.filter((agent) => (agent.tool_groups?.length ?? 0) > 0)
                      .length
                  }{" "}
                  个具备工具域
                </div>
                <div className="metric-chip">
                  <RadarIcon className="size-3.5" />
                  {resolvedSurfaceLabel}
                </div>
              </div>
            </div>

            <div className="control-panel flex flex-col justify-between gap-4">
              <div>
                <div className="workspace-kicker text-slate-500 dark:text-slate-400">
                  Assembly
                </div>
                <div className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                  建立可复用的智能体目录
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  统一管理模型、工具组和领域职责，让不同 surface 共享同一套
                  VibeCFD 协作能力。
                </p>
              </div>

              <Button onClick={handleNewAgent}>
                <PlusIcon className="mr-1.5 size-4" />
                {t.agents.newAgent}
              </Button>
            </div>
          </div>
        </WorkspaceSurfaceCard>

        {error ? (
          <WorkspaceStatePanel
            state="update-failed"
            actions={[
              {
                label: t.workspace.retryUpdate,
                onClick: () => window.location.reload(),
              },
            ]}
          />
        ) : isLoading ? (
          <WorkspaceSurfaceCard>
            <div className="flex min-h-[18rem] items-center justify-center text-sm text-slate-500 dark:text-slate-400">
              {t.common.loading}
            </div>
          </WorkspaceSurfaceCard>
        ) : agents.length === 0 ? (
          <WorkspaceStatePanel
            state="first-run"
            title={t.agents.emptyTitle}
            description={t.agents.emptyDescription}
            actions={[
              {
                label: t.agents.newAgent,
                onClick: handleNewAgent,
              },
            ]}
          />
        ) : (
          <WorkspaceSurfaceCard className="min-h-0">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                  {t.common.agentCount(agents.length)}
                </div>
                <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {t.agents.listDescription}
                </div>
              </div>
              <div className="hidden rounded-full border border-cyan-200/70 bg-cyan-50/80 px-3 py-1 text-xs font-medium text-cyan-700 md:flex md:items-center md:gap-2 dark:border-cyan-900/70 dark:bg-cyan-950/30 dark:text-cyan-300">
                <BotIcon className="size-3.5" />
                {t.agents.catalogLabel}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {agents.map((agent) => (
                <AgentCard key={agent.name} agent={agent} />
              ))}
            </div>
          </WorkspaceSurfaceCard>
        )}
      </WorkspaceSurfaceMain>
    </WorkspaceSurfacePage>
  );
}
