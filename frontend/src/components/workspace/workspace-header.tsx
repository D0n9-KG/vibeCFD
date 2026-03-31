"use client";

import { WavesIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";

export function WorkspaceHeader({ className }: { className?: string }) {
  const { state } = useSidebar();
  const pathname = usePathname();
  const chrome = getWorkspaceSidebarChrome();

  return (
    <>
      <div
        className={cn(
          "group/workspace-header flex h-12 flex-col justify-center",
          className,
        )}
      >
        {state === "collapsed" ? (
          <div className="group-has-data-[collapsible=icon]/sidebar-wrapper:-translate-y flex w-full cursor-pointer items-center justify-center">
            <div className="text-primary block pt-1 font-serif text-sm font-semibold group-hover/workspace-header:hidden">
              VC
            </div>
            <SidebarTrigger className="hidden pl-2 group-hover/workspace-header:block" />
          </div>
        ) : (
          <div className={cn("flex items-center gap-2", chrome.headerPanelClassName)}>
            {env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ? (
              <Link href="/" className="min-w-0 flex-1 leading-none">
                <span className={chrome.brandEyebrowClassName}>Studio Rail</span>
                <span className="text-primary mt-1 block truncate font-serif text-base font-semibold">
                  VibeCFD
                </span>
                <span className={chrome.brandMetaClassName}>
                  Powered by DeerFlow
                </span>
              </Link>
            ) : (
              <div className="min-w-0 flex-1 cursor-default leading-none">
                <span className={chrome.brandEyebrowClassName}>Studio Rail</span>
                <span className="text-primary mt-1 block truncate font-serif text-base font-semibold">
                  VibeCFD
                </span>
                <span className={chrome.brandMetaClassName}>
                  Powered by DeerFlow
                </span>
              </div>
            )}
            <SidebarTrigger className="shrink-0 rounded-lg bg-white/70" />
          </div>
        )}
      </div>

      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            isActive={pathname === "/workspace/submarine/new"}
            className={chrome.headerQuickActionClassName}
            asChild
          >
            <Link className="text-inherit" href="/workspace/submarine/new">
              <WavesIcon size={16} />
              <span>新建仿真</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </>
  );
}
