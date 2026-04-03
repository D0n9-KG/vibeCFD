"use client";

import { BotIcon, MessageSquareIcon, SparklesIcon, WavesIcon } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import type { ComponentType } from "react";

import { env } from "@/env";
import { cn } from "@/lib/utils";

import { WorkspaceActivityBar } from "./workspace-activity-bar";
import {
  getWorkspaceSurfaceHref,
  matchWorkspaceSurface,
  type WorkspaceSurfaceId,
} from "./workspace-surface-config";
import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";

const SURFACE_ACTIONS: Record<
  WorkspaceSurfaceId,
  { href: string; label: string; icon: ComponentType<{ className?: string }> }
> = {
  submarine: {
    href: "/workspace/submarine/new",
    label: "新建仿真",
    icon: WavesIcon,
  },
  "skill-studio": {
    href: "/workspace/skill-studio",
    label: "进入 Skill Studio",
    icon: SparklesIcon,
  },
  chats: {
    href: "/workspace/chats",
    label: "查看对话",
    icon: MessageSquareIcon,
  },
  agents: {
    href: "/workspace/agents/new",
    label: "新建智能体",
    icon: BotIcon,
  },
};

export function WorkspaceHeader({ className }: { className?: string }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const chrome = getWorkspaceSidebarChrome();
  const activeSurface = matchWorkspaceSurface(pathname);
  const isMock = searchParams.get("mock") === "true";
  const surfaceAction = SURFACE_ACTIONS[activeSurface.id];
  const ActionIcon = surfaceAction.icon;

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <WorkspaceActivityBar orientation="horizontal" className="md:hidden" />
      <div className={cn("flex items-center gap-3", chrome.headerPanelClassName)}>
        <div className="min-w-0 flex-1 leading-none">
          <span className={chrome.brandEyebrowClassName}>统一工作区</span>
          <span className="text-primary mt-1 block truncate font-serif text-base font-semibold">
            VibeCFD
          </span>
          <span className={chrome.brandMetaClassName}>
            当前上下文: {activeSurface.label}
          </span>
        </div>
        <Link
          className={cn(
            chrome.headerQuickActionClassName,
            "inline-flex items-center gap-2 px-3",
          )}
          href={
            activeSurface.id === "skill-studio"
              ? getWorkspaceSurfaceHref("skill-studio", {
                  isMock,
                  staticWebsiteOnly:
                    env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true",
                })
              : surfaceAction.href
          }
        >
          <ActionIcon className="size-4" />
          <span>{surfaceAction.label}</span>
        </Link>
      </div>
    </div>
  );
}
