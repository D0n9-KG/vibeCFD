"use client";

import { MessagesSquare, WandSparklesIcon, WavesIcon } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { env } from "@/env";

export function WorkspaceNavChatList() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isMock = searchParams.get("mock") === "true";
  const skillStudioHref =
    env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isMock
      ? "/workspace/skill-studio?mock=true"
      : "/workspace/skill-studio";

  return (
    <>
      <SidebarGroup className="pt-1">
        <SidebarGroupLabel>主要功能</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              isActive={pathname.startsWith("/workspace/submarine")}
              asChild
            >
              <Link className="text-muted-foreground" href="/workspace/submarine/new">
                <WavesIcon />
                <span>VibeCFD 仿真</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              isActive={pathname.startsWith("/workspace/skill-studio")}
              asChild
            >
              <Link className="text-muted-foreground" href={skillStudioHref}>
                <WandSparklesIcon />
                <span>Skill Studio</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>

      <SidebarGroup>
        <SidebarGroupLabel>其他</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              isActive={pathname.startsWith("/workspace/chats")}
              asChild
            >
              <Link className="text-muted-foreground" href="/workspace/chats">
                <MessagesSquare />
                <span>通用对话</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>
    </>
  );
}
