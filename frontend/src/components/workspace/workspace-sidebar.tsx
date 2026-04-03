"use client";

import type { CSSProperties } from "react";
import { usePathname } from "next/navigation";

import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

import { WorkspaceActivityBar } from "./workspace-activity-bar";
import { WorkspaceHeader } from "./workspace-header";
import { WorkspaceNavChatList } from "./workspace-nav-chat-list";
import { matchWorkspaceSurface } from "./workspace-surface-config";
import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";

const WORKSPACE_SIDEBAR_STYLE = {
  "--sidebar-width": "18.5rem",
} as CSSProperties;

export function WorkspaceSidebar({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();
  const chrome = getWorkspaceSidebarChrome();
  const activeSurface = matchWorkspaceSurface(pathname);

  return (
    <Sidebar
      variant="sidebar"
      collapsible="icon"
      className={chrome.sidebarClassName}
      style={WORKSPACE_SIDEBAR_STYLE}
      {...props}
    >
      <div className="flex h-full min-h-0">
        <WorkspaceActivityBar className="hidden md:flex" />
        <div className={cn("workspace-context-sidebar", chrome.contextSidebarClassName)}>
          <SidebarHeader className={chrome.headerClassName}>
            <WorkspaceHeader />
          </SidebarHeader>
          <SidebarContent className={chrome.contentClassName}>
            <WorkspaceNavChatList surfaceId={activeSurface.id} />
          </SidebarContent>
        </div>
      </div>
      <SidebarRail />
    </Sidebar>
  );
}
