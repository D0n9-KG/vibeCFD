"use client";

import {
  BugIcon,
  ChevronsUpDown,
  InfoIcon,
  Settings2Icon,
  SettingsIcon,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { useI18n } from "@/core/i18n/hooks";

import { SettingsDialog } from "./settings";
import { getWorkspaceSidebarChrome } from "./workspace-sidebar-shell";

function NavMenuButtonContent({
  isSidebarOpen,
  t,
  iconOnly = false,
}: {
  isSidebarOpen: boolean;
  t: ReturnType<typeof useI18n>["t"];
  iconOnly?: boolean;
}) {
  if (iconOnly) {
    return (
      <div className="flex size-full items-center justify-center">
        <SettingsIcon className="size-4" />
        <span className="sr-only">{t.workspace.settingsAndMore}</span>
      </div>
    );
  }

  return isSidebarOpen ? (
    <div className="text-muted-foreground flex w-full items-center gap-2 text-left text-sm">
      <SettingsIcon className="size-4" />
      <span>{t.workspace.settingsAndMore}</span>
      <ChevronsUpDown className="text-muted-foreground ml-auto size-4" />
    </div>
  ) : (
    <div className="flex size-full items-center justify-center">
      <SettingsIcon className="text-muted-foreground size-4" />
    </div>
  );
}

export function WorkspaceNavMenu({
  mode = "sidebar",
}: {
  mode?: "sidebar" | "activity-bar";
}) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsDefaultSection, setSettingsDefaultSection] = useState<
    "appearance" | "memory" | "tools" | "skills" | "notification" | "about"
  >("appearance");
  const [mounted, setMounted] = useState(false);
  const { open: isSidebarOpen } = useSidebar();
  const { t } = useI18n();
  const chrome = getWorkspaceSidebarChrome();
  const iconOnly = mode === "activity-bar";

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        defaultSection={settingsDefaultSection}
      />
      <SidebarMenu className="w-full">
        <SidebarMenuItem>
          {mounted ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size={iconOnly ? "default" : "lg"}
                  className={
                    iconOnly
                      ? chrome.activityBarSettingsButtonClassName
                      : chrome.footerMenuButtonClassName
                  }
                >
                  <NavMenuButtonContent
                    isSidebarOpen={isSidebarOpen}
                    t={t}
                    iconOnly={iconOnly}
                  />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                align="end"
                sideOffset={4}
              >
                <DropdownMenuGroup>
                  <DropdownMenuItem
                    onClick={() => {
                      setSettingsDefaultSection("appearance");
                      setSettingsOpen(true);
                    }}
                  >
                    <Settings2Icon />
                    {t.common.settings}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <a
                    href="https://github.com/zjunlp/SkillNet"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <DropdownMenuItem>
                      <BugIcon />
                      SkillNet
                    </DropdownMenuItem>
                  </a>
                  <a href="https://github.com/bytedance/deer-flow/issues" target="_blank" rel="noopener noreferrer">
                    <DropdownMenuItem>
                      <BugIcon />
                      {t.workspace.reportIssue}
                    </DropdownMenuItem>
                  </a>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => {
                    setSettingsDefaultSection("about");
                    setSettingsOpen(true);
                  }}
                >
                  <InfoIcon />
                  {t.workspace.about}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <SidebarMenuButton
              size={iconOnly ? "default" : "lg"}
              className={`${iconOnly ? chrome.activityBarSettingsButtonClassName : chrome.footerMenuButtonClassName} pointer-events-none`}
            >
              <NavMenuButtonContent
                isSidebarOpen={isSidebarOpen}
                t={t}
                iconOnly={iconOnly}
              />
            </SidebarMenuButton>
          )}
        </SidebarMenuItem>
      </SidebarMenu>
    </>
  );
}
