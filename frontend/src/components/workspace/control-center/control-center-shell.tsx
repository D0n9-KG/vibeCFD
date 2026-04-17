"use client";

import {
  DatabaseZapIcon,
  FolderCogIcon,
  Settings2Icon,
  ShieldCheckIcon,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AgentsTab } from "@/components/workspace/control-center/agents-tab";
import { RuntimeConfigTab } from "@/components/workspace/control-center/runtime-config-tab";
import { SkillsTab } from "@/components/workspace/control-center/skills-tab";
import { ThreadsTab } from "@/components/workspace/control-center/threads-tab";
import {
  WorkspaceSurfaceCard,
  WorkspaceSurfaceMain,
  WorkspaceSurfacePage,
} from "@/components/workspace/workspace-container";

const CONTROL_CENTER_TABS = [
  {
    value: "runtime-config",
    label: "模型与路由",
    description: "管理内置模型、自定义运行时模型、主代理默认模型与执行阶段路由。",
    icon: Settings2Icon,
  },
  {
    value: "agents",
    label: "智能体与子代理",
    description: "管理主智能体、自定义智能体，以及科研执行子代理的职责与绑定关系。",
    icon: ShieldCheckIcon,
  },
  {
    value: "skills",
    label: "技能资产",
    description: "浏览已安装技能，查看生命周期、绑定关系、文件结构与内容预览。",
    icon: FolderCogIcon,
  },
  {
    value: "threads",
    label: "线程与历史",
    description: "查看规范线程、预览删除影响，并直接管理用户仍在使用的会话历史。",
    icon: DatabaseZapIcon,
  },
] as const;

function renderTabContent(
  tabValue: (typeof CONTROL_CENTER_TABS)[number]["value"],
) {
  switch (tabValue) {
    case "runtime-config":
      return <RuntimeConfigTab />;
    case "agents":
      return <AgentsTab />;
    case "skills":
      return <SkillsTab />;
    case "threads":
      return <ThreadsTab />;
    default:
      return null;
  }
}

export function ControlCenterShell() {
  const searchParams = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const defaultTab: (typeof CONTROL_CENTER_TABS)[number]["value"] =
    CONTROL_CENTER_TABS.some((tab) => tab.value === requestedTab) &&
    requestedTab != null
      ? (requestedTab as (typeof CONTROL_CENTER_TABS)[number]["value"])
      : "runtime-config";

  useEffect(() => {
    document.title = "管理中心 - VibeCFD";
  }, []);

  return (
    <WorkspaceSurfacePage data-surface-label="管理中心">
      <WorkspaceSurfaceMain className="max-w-[1840px]">
        <WorkspaceSurfaceCard className="overflow-hidden">
          <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]">
            <div className="min-w-0">
              <div className="workspace-kicker text-emerald-700 dark:text-emerald-300">
                管理中枢
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
                管理中心
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700 dark:text-slate-300">
                把运行配置、智能体、技能资产和线程历史统一放进同一个规范工作台，
                避免用户为了确认系统状态而在不同页面和隐蔽目录之间来回跳转。
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                <div className="metric-chip">4 个管理域</div>
                <div className="metric-chip">以后端规范状态为准</div>
                <div className="metric-chip">支持删除预览与规范清理</div>
              </div>
            </div>

            <div className="control-panel self-start rounded-2xl border border-slate-200/70 bg-slate-50/80 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div>
                <div className="workspace-kicker text-slate-500 dark:text-slate-400">
                  当前目标
                </div>
                <div className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                  把后台真实状态清晰地暴露给前端用户
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  每个分页都直接读取规范后端接口，让用户看到的配置、技能、线程和
                  子代理状态，与系统真正执行时使用的状态保持一致。
                </p>
              </div>
            </div>
          </div>
        </WorkspaceSurfaceCard>

        <WorkspaceSurfaceCard className="min-h-0 overflow-hidden">
          <Tabs key={defaultTab} defaultValue={defaultTab} className="gap-5">
            <TabsList variant="line" className="w-full justify-start overflow-x-auto">
              {CONTROL_CENTER_TABS.map((tab) => {
                const Icon = tab.icon;
                return (
                  <TabsTrigger key={tab.value} value={tab.value}>
                    <Icon className="size-4" />
                    {tab.label}
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {CONTROL_CENTER_TABS.map((tab) => (
              <TabsContent key={tab.value} value={tab.value}>
                <div className="mb-4 text-sm text-slate-600 dark:text-slate-300">
                  {tab.description}
                </div>
                {renderTabContent(tab.value)}
              </TabsContent>
            ))}
          </Tabs>
        </WorkspaceSurfaceCard>
      </WorkspaceSurfaceMain>
    </WorkspaceSurfacePage>
  );
}
