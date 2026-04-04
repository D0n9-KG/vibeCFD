"use client";

import { BotIcon, PlusIcon } from "lucide-react";
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
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="min-w-0 flex-1">
              <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
                {resolvedSurfaceLabel}
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-stone-900">
                {t.agents.title}
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-stone-600">
                {t.agents.description}
              </p>
            </div>

            <Button onClick={handleNewAgent}>
              <PlusIcon className="mr-1.5 size-4" />
              {t.agents.newAgent}
            </Button>
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
            <div className="flex min-h-[18rem] items-center justify-center text-sm text-stone-500">
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
                <div className="text-sm font-medium text-stone-900">
                  {t.common.agentCount(agents.length)}
                </div>
                <div className="mt-1 text-sm text-stone-500">
                  {t.agents.listDescription}
                </div>
              </div>
              <div className="hidden rounded-full border border-stone-200/80 bg-stone-50 px-3 py-1 text-xs font-medium text-stone-500 md:flex md:items-center md:gap-2">
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
