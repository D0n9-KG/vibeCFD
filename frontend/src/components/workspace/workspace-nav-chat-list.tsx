"use client";

import { BotIcon, MessagesSquare, WandSparklesIcon } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useI18n } from "@/core/i18n/hooks";
import { env } from "@/env";

export function WorkspaceNavChatList() {
  const { t } = useI18n();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isMock = searchParams.get("mock") === "true";
  const skillStudioHref =
    env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isMock
      ? "/workspace/skill-studio?mock=true"
      : "/workspace/skill-studio";
  return (
    <SidebarGroup className="pt-1">
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton isActive={pathname === "/workspace/chats"} asChild>
            <Link className="text-muted-foreground" href="/workspace/chats">
              <MessagesSquare />
              <span>{t.sidebar.chats}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <SidebarMenuButton
            isActive={pathname.startsWith("/workspace/agents")}
            asChild
          >
            <Link className="text-muted-foreground" href="/workspace/agents">
              <BotIcon />
              <span>{t.sidebar.agents}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <SidebarMenuButton
            isActive={pathname.startsWith("/workspace/skill-studio")}
            asChild
          >
            <Link
              className="text-muted-foreground"
              href={skillStudioHref}
            >
              <WandSparklesIcon />
              <span>{t.sidebar.skillStudio}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  );
}
