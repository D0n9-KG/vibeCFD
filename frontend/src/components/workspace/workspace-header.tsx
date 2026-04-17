"use client";

import {
  BotIcon,
  PanelsTopLeftIcon,
  SparklesIcon,
  WavesIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import type { ComponentType } from "react";

import { env } from "@/env";
import { cn } from "@/lib/utils";

import { WorkspaceActivityBar } from "./workspace-activity-bar";
import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";
import {
  getWorkspaceSurfaceHref,
  matchWorkspaceSurface,
  type WorkspaceSurfaceId,
} from "./workspace-surface-config";

const SURFACE_ACTIONS: Record<
  WorkspaceSurfaceId,
  { href: string; label: string; icon: ComponentType<{ className?: string }> }
> = {
  submarine: {
    href: "/workspace/submarine/new",
    label: "新建仿真任务",
    icon: WavesIcon,
  },
  "skill-studio": {
    href: "/workspace/skill-studio/new",
    label: "新建技能资产",
    icon: SparklesIcon,
  },
  agents: {
    href: "/workspace/agents/new",
    label: "新建智能体",
    icon: BotIcon,
  },
  "control-center": {
    href: "/workspace/control-center",
    label: "打开管理中心",
    icon: PanelsTopLeftIcon,
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
      <div className={cn("flex flex-col gap-3", chrome.headerPanelClassName)}>
        <div className="min-w-0 leading-tight">
          <span className={chrome.brandEyebrowClassName}>中文科研指挥台</span>
          <span className="text-primary mt-1 block truncate text-lg font-semibold tracking-[0.02em]">
            VibeCFD
          </span>
          <span className={cn("mt-1 block", chrome.brandMetaClassName)}>
            面向科研仿真的统一工作台 · 当前界面： {activeSurface.label}
          </span>
        </div>
        <Link
          className={cn(
            chrome.headerQuickActionClassName,
            "inline-flex w-full items-center justify-center gap-2 px-3",
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
