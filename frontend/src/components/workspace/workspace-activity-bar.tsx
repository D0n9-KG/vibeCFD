"use client";

import {
  BotIcon,
  MessageSquareIcon,
  SparklesIcon,
  WavesIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import type { ComponentType } from "react";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import { WorkspaceNavMenu } from "./workspace-nav-menu";
import {
  getWorkspaceSurfaceHref,
  isWorkspaceSurfaceActive,
  type WorkspaceSurface,
  WORKSPACE_SURFACES,
} from "./workspace-surface-config";
import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";

const SURFACE_ICONS: Record<
  WorkspaceSurface["id"],
  ComponentType<{ className?: string }>
> = {
  submarine: WavesIcon,
  "skill-studio": SparklesIcon,
  chats: MessageSquareIcon,
  agents: BotIcon,
};

export function WorkspaceActivityBar({
  className,
  orientation = "vertical",
}: {
  className?: string;
  orientation?: "vertical" | "horizontal";
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const chrome = getWorkspaceSidebarChrome();
  const isMock = searchParams.get("mock") === "true";
  const isVertical = orientation === "vertical";

  return (
    <div
      className={cn(
        "workspace-surfaces-activity-bar",
        isVertical
          ? chrome.activityBarClassName
          : chrome.activityBarCompactClassName,
        className,
      )}
    >
      <div
        className={cn(
          "flex min-h-0 w-full",
          isVertical
            ? "h-full flex-col items-center gap-3"
            : "items-center gap-2 overflow-x-auto",
        )}
      >
        <SidebarTrigger className={chrome.activityBarTriggerClassName} />
        <nav
          aria-label="Workspace surfaces"
          className={cn(
            "flex min-h-0",
            isVertical
              ? "flex-1 flex-col items-center gap-2"
              : "min-w-0 flex-1 items-center gap-2",
          )}
        >
          {WORKSPACE_SURFACES.map((surface) => {
            const Icon = SURFACE_ICONS[surface.id];
            const isActive = isWorkspaceSurfaceActive(surface, pathname);
            return (
              <Link
                key={surface.id}
                aria-label={surface.label}
                title={surface.label}
                href={getWorkspaceSurfaceHref(surface.id, {
                  isMock,
                  staticWebsiteOnly:
                    env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true",
                })}
                className={cn(
                  chrome.activityBarButtonClassName,
                  isActive && chrome.activityBarButtonActiveClassName,
                  !isVertical &&
                    "h-auto min-w-max gap-2 px-3 py-2 text-[13px] font-medium",
                )}
              >
                <Icon className="size-4" />
                {!isVertical && <span>{surface.label}</span>}
              </Link>
            );
          })}
        </nav>
        <div className={cn(!isVertical && "ml-auto")}>
          <WorkspaceNavMenu mode="activity-bar" />
        </div>
      </div>
    </div>
  );
}
