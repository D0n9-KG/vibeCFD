"use client";

import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";

import { RecentChatList } from "./recent-chat-list";
import { WorkspaceHeader } from "./workspace-header";
import { WorkspaceNavChatList } from "./workspace-nav-chat-list";
import { WorkspaceNavMenu } from "./workspace-nav-menu";
import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";

export function WorkspaceSidebar({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  const { open: isSidebarOpen } = useSidebar();
  const chrome = getWorkspaceSidebarChrome();
  return (
    <>
      <Sidebar
        variant="sidebar"
        collapsible="icon"
        className={chrome.sidebarClassName}
        {...props}
      >
        <SidebarHeader className={chrome.headerClassName}>
          <WorkspaceHeader />
        </SidebarHeader>
        <SidebarContent className={chrome.contentClassName}>
          <WorkspaceNavChatList />
          {isSidebarOpen && <RecentChatList />}
        </SidebarContent>
        <SidebarFooter className={chrome.footerClassName}>
          <WorkspaceNavMenu />
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>
    </>
  );
}
