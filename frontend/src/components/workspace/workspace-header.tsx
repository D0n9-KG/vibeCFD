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

export function WorkspaceHeader({ className }: { className?: string }) {
  const { state } = useSidebar();
  const pathname = usePathname();
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
          <div className="flex items-center justify-between gap-2">
            {env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ? (
              <Link href="/" className="ml-2 flex flex-col leading-none">
                <span className="text-primary font-serif text-base font-semibold">VibeCFD</span>
                <span className="text-[10px] text-muted-foreground">Powered by DeerFlow</span>
              </Link>
            ) : (
              <div className="ml-2 flex cursor-default flex-col leading-none">
                <span className="text-primary font-serif text-base font-semibold">VibeCFD</span>
                <span className="text-[10px] text-muted-foreground">Powered by DeerFlow</span>
              </div>
            )}
            <SidebarTrigger />
          </div>
        )}
      </div>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            isActive={pathname === "/workspace/submarine/new"}
            asChild
          >
            <Link className="text-muted-foreground" href="/workspace/submarine/new">
              <WavesIcon size={16} />
              <span>新建仿真</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </>
  );
}
