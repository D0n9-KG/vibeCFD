"use client";

import {
  BotIcon,
  CompassIcon,
  MessageSquareIcon,
  PlusIcon,
  SparklesIcon,
  WavesIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useMemo } from "react";
import type { ComponentType } from "react";

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
} from "@/components/ui/sidebar";
import { useI18n } from "@/core/i18n/hooks";
import { useThreads } from "@/core/threads/hooks";
import type { AgentThread } from "@/core/threads/types";
import {
  pathOfThreadByState,
  titleOfThread,
  workbenchKindOfThread,
} from "@/core/threads/utils";
import { env } from "@/env";

import {
  getWorkspaceSurfaceById,
  getWorkspaceSurfaceHref,
  type WorkspaceSurfaceId,
  WORKSPACE_SURFACES,
} from "./workspace-surface-config";
import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";

type SurfaceQuickLink = {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
};

const RECENT_THREAD_PLACEHOLDER_COUNT = 6;

function surfaceQuickLinks(
  surfaceId: WorkspaceSurfaceId,
  {
    isMock,
    staticWebsiteOnly,
  }: {
    isMock: boolean;
    staticWebsiteOnly: boolean;
  },
): SurfaceQuickLink[] {
  switch (surfaceId) {
    case "submarine":
      return [
        {
          href: getWorkspaceSurfaceHref("submarine"),
          label: "新建仿真",
          icon: PlusIcon,
        },
      ];
    case "skill-studio":
      return [
        {
          href: getWorkspaceSurfaceHref("skill-studio", {
            isMock,
            staticWebsiteOnly,
          }),
          label: "工作台总览",
          icon: SparklesIcon,
        },
      ];
    case "chats":
      return [
        {
          href: getWorkspaceSurfaceHref("chats"),
          label: "全部对话",
          icon: MessageSquareIcon,
        },
      ];
    case "agents":
      return [
        {
          href: "/workspace/agents",
          label: "智能体总览",
          icon: CompassIcon,
        },
        {
          href: "/workspace/agents/new",
          label: "新建智能体",
          icon: BotIcon,
        },
      ];
  }
}

function filterThreadsForSurface(
  surfaceId: WorkspaceSurfaceId,
  threads: AgentThread[],
) {
  switch (surfaceId) {
    case "submarine":
      return threads.filter(
        (thread) => workbenchKindOfThread(thread) === "submarine",
      );
    case "skill-studio":
      return threads.filter(
        (thread) => workbenchKindOfThread(thread) === "skill-studio",
      );
    case "chats":
      return threads.filter((thread) => workbenchKindOfThread(thread) === "chat");
    default:
      return [];
  }
}

export function WorkspaceNavChatList({
  surfaceId,
}: {
  surfaceId: WorkspaceSurfaceId;
}) {
  const { t } = useI18n();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const chrome = getWorkspaceSidebarChrome();
  const { data: threads = [], isLoading } = useThreads();
  const isMock = searchParams.get("mock") === "true";
  const surface =
    WORKSPACE_SURFACES.find((entry) => entry.id === surfaceId) ??
    getWorkspaceSurfaceById(surfaceId);

  const quickLinks = useMemo(
    () =>
      surfaceQuickLinks(surfaceId, {
        isMock,
        staticWebsiteOnly: env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true",
      }),
    [surfaceId, isMock],
  );

  const recentThreads = useMemo(
    () => filterThreadsForSurface(surfaceId, threads).slice(0, 6),
    [surfaceId, threads],
  );

  return (
    <div className="flex flex-col gap-3">
      <SidebarGroup className={chrome.primaryGroupClassName}>
        <SidebarGroupLabel className={chrome.groupLabelClassName}>
          {surface.label}
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {quickLinks.map((link) => {
              const Icon = link.icon;
              return (
                <SidebarMenuItem key={link.href}>
                  <SidebarMenuButton
                    isActive={pathname === link.href}
                    className={chrome.menuButtonClassName}
                    asChild
                  >
                    <Link className="text-inherit" href={link.href}>
                      <Icon />
                      <span>{link.label}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      {(isLoading || recentThreads.length > 0) && (
        <SidebarGroup className={chrome.historyGroupClassName}>
          <SidebarGroupLabel className={chrome.groupLabelClassName}>
            {surfaceId === "chats" ? "最近对话" : "最近工作线程"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {isLoading
                ? Array.from({
                    length: RECENT_THREAD_PLACEHOLDER_COUNT,
                  }).map((_, index) => (
                    <SidebarMenuItem key={`placeholder-${index}`}>
                      <SidebarMenuSkeleton showIcon />
                    </SidebarMenuItem>
                  ))
                : recentThreads.map((thread) => (
                    <SidebarMenuItem key={thread.thread_id}>
                      <SidebarMenuButton
                        isActive={pathOfThreadByState(thread) === pathname}
                        className={chrome.historyButtonClassName}
                        asChild
                      >
                        <Link
                          className="text-inherit"
                          href={pathOfThreadByState(thread)}
                        >
                          {surfaceId === "submarine" ? (
                            <WavesIcon />
                          ) : (
                            <SparklesIcon />
                          )}
                          <span>{titleOfThread(thread, t.pages.untitled)}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      )}
    </div>
  );
}
