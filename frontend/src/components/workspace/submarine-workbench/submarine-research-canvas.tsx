"use client";

import { Layers3Icon, MicroscopeIcon, ScrollTextIcon } from "lucide-react";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  SecondaryLayerHost,
  WorkbenchFlow,
} from "@/components/workspace/agentic-workbench";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

import type { SubmarineDetailModel } from "./submarine-detail-model";
import { SubmarineExperimentBoard } from "./submarine-experiment-board";
import { SubmarineOperatorBoard } from "./submarine-operator-board";
import type { SubmarineSessionModel } from "./submarine-session-model";
import { SubmarineTrustPanels } from "./submarine-trust-panels";

type SubmarineResearchCanvasProps = {
  session: SubmarineSessionModel;
  detail: SubmarineDetailModel;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  artifactPaths: readonly string[];
  onOpenNegotiation: () => void;
};

type DrawerId = "trust" | "studies" | "operator";

const DEFAULT_DRAWER_BY_MODULE: Record<string, DrawerId> = {
  proposal: "operator",
  decision: "operator",
  delegation: "operator",
  skills: "operator",
  execution: "operator",
  "postprocess-method": "trust",
  "postprocess-result": "studies",
  report: "trust",
};

export function SubmarineResearchCanvas({
  session,
  detail,
  runtime,
  designBrief,
  finalReport,
  artifactPaths,
  onOpenNegotiation,
}: SubmarineResearchCanvasProps) {
  const [activeDrawerId, setActiveDrawerId] = useState<DrawerId>(
    DEFAULT_DRAWER_BY_MODULE[session.activeModuleId],
  );

  useEffect(() => {
    setActiveDrawerId(DEFAULT_DRAWER_BY_MODULE[session.activeModuleId]);
  }, [session.activeModuleId]);

  const executionPlan = runtime?.execution_plan ?? designBrief?.execution_outline ?? [];
  const skillNames = [
    ...(runtime?.execution_plan?.flatMap((item) => item.target_skills ?? []) ?? []),
    ...(runtime?.activity_timeline?.flatMap((item) => item.skill_names ?? []) ?? []),
  ].filter((skill, index, all): skill is string => Boolean(skill) && all.indexOf(skill) === index);
  const requestedOutputs =
    runtime?.requested_outputs?.map((item) => item?.label ?? item?.requested_label ?? "").filter(Boolean) ??
    designBrief?.requested_outputs
      ?.map((item) => item?.label ?? item?.requested_label ?? "")
      .filter(Boolean) ??
    [];
  const verificationRequirements =
    designBrief?.scientific_verification_requirements
      ?.map((item) => item?.summary_zh ?? item?.label ?? "")
      .filter(Boolean) ?? [];
  const timelineEntries = runtime?.activity_timeline ?? [];
  const conclusionSections = finalReport?.conclusion_sections ?? [];

  const drawerLayers = useMemo(
    () => [
      {
        id: "trust",
        label: "证据与可信度",
        content: <SubmarineTrustPanels panels={detail.trustPanels} />,
      },
      {
        id: "studies",
        label: "对比试验与后处理结果",
        content: <SubmarineExperimentBoard experimentBoard={detail.experimentBoard} />,
      },
      {
        id: "operator",
        label: "交付判断与后续动作",
        content: <SubmarineOperatorBoard operatorBoard={detail.operatorBoard} />,
      },
    ],
    [detail.experimentBoard, detail.operatorBoard, detail.trustPanels],
  );

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <WorkbenchFlow
        items={session.modules.map((module) => ({
          id: module.id,
          title: module.title,
          status: module.status,
          summary: module.summary,
          expanded: module.expanded,
          content: renderModuleContent({
            moduleId: module.id,
            runtime,
            designBrief,
            finalReport,
            executionPlan,
            skillNames,
            requestedOutputs,
            verificationRequirements,
            timelineEntries,
            artifactPaths,
            conclusionSections,
            detail,
            onOpenNegotiation,
            onOpenDrawer: setActiveDrawerId,
          }),
        }))}
      />

      <SecondaryLayerHost
        layers={drawerLayers}
        activeLayerId={activeDrawerId}
        className="border-slate-200/70 bg-slate-50/70"
      />
    </div>
  );
}

function renderModuleContent({
  moduleId,
  runtime,
  designBrief,
  finalReport,
  executionPlan,
  skillNames,
  requestedOutputs,
  verificationRequirements,
  timelineEntries,
  artifactPaths,
  conclusionSections,
  detail,
  onOpenNegotiation,
  onOpenDrawer,
}: {
  moduleId: string;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  executionPlan: readonly {
    role_id?: string | null;
    owner?: string | null;
    goal?: string | null;
    status?: string | null;
  }[];
  skillNames: readonly string[];
  requestedOutputs: readonly string[];
  verificationRequirements: readonly string[];
  timelineEntries: readonly {
    actor?: string | null;
    title?: string | null;
    summary?: string | null;
    status?: string | null;
  }[];
  artifactPaths: readonly string[];
  conclusionSections: readonly {
    title_zh?: string | null;
    summary_zh?: string | null;
  }[];
  detail: SubmarineDetailModel;
  onOpenNegotiation: () => void;
  onOpenDrawer: (id: DrawerId) => void;
}): ReactNode {
  switch (moduleId) {
    case "proposal":
      return (
        <div className="space-y-4">
          <KeyValueGrid
            items={[
              {
                label: "研究目标",
                value:
                  runtime?.task_summary ??
                  designBrief?.summary_zh ??
                  "等待主智能体整理本轮潜艇仿真的目标与边界。",
              },
              {
                label: "几何对象",
                value:
                  designBrief?.geometry_virtual_path ??
                  runtime?.geometry_virtual_path ??
                  "尚未绑定几何文件",
              },
              {
                label: "交付预期",
                value: requestedOutputs[0] ?? "尚未定义具体交付物",
              },
            ]}
          />
          <TokenList
            title="用户约束"
            emptyLabel="尚未补充显式约束。"
            items={designBrief?.user_constraints ?? []}
          />
        </div>
      );
    case "decision":
      return (
        <div className="space-y-4">
          <TokenList
            title="待确认问题"
            emptyLabel="当前没有待确认问题。"
            items={designBrief?.open_questions ?? []}
          />
          <TokenList
            title="待确认参数"
            emptyLabel="当前没有待确认参数。"
            items={
              runtime?.calculation_plan
                ?.filter((item) => item?.approval_state !== "researcher_confirmed")
                .map((item) => item?.label ?? item?.item_id ?? "待确认项") ?? []
            }
          />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={onOpenNegotiation}>
              去协商区补充修改意见
            </Button>
          </div>
        </div>
      );
    case "delegation":
      return (
        <CompactList
          title="子代理任务分配"
          emptyLabel="方案敲定后，这里会展示主智能体拆分出的子任务。"
          items={executionPlan.map((item) => ({
            title: item.goal ?? item.role_id ?? "未命名任务",
            meta: [item.owner ?? "待分配", item.status ?? "待启动"].join(" · "),
          }))}
        />
      );
    case "skills":
      return (
        <div className="space-y-4">
          <TokenList
            title="已调用技能"
            emptyLabel="当前尚未触发显式技能调用。"
            items={skillNames}
          />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => onOpenDrawer("operator")}>
              查看主智能体编排说明
            </Button>
          </div>
        </div>
      );
    case "execution":
      return (
        <div className="space-y-4">
          <KeyValueGrid
            items={[
              { label: "运行状态", value: runtime?.runtime_status ?? "尚未执行" },
              {
                label: "当前阶段",
                value: runtime?.current_stage ?? "等待进入计算流程",
              },
              {
                label: "运行产物",
                value: artifactPaths.length > 0 ? `${artifactPaths.length} 项` : "暂无",
              },
            ]}
          />
          <CompactList
            title="最新运行轨迹"
            emptyLabel="暂无运行轨迹。"
            items={timelineEntries.slice(0, 4).map((entry) => ({
              title: entry.title ?? "未命名事件",
              meta: [entry.actor ?? "主智能体", entry.status ?? "进行中"]
                .filter(Boolean)
                .join(" · "),
              description: entry.summary ?? undefined,
            }))}
          />
        </div>
      );
    case "postprocess-method":
      return (
        <div className="space-y-4">
          <TokenList
            title="后处理输出"
            emptyLabel="尚未定义后处理输出。"
            items={requestedOutputs}
          />
          <TokenList
            title="科学验证要求"
            emptyLabel="尚未定义科学验证要求。"
            items={verificationRequirements}
          />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => onOpenDrawer("trust")}>
              查看证据与可信度
            </Button>
          </div>
        </div>
      );
    case "postprocess-result":
      return (
        <div className="space-y-4">
          <KeyValueGrid
            items={[
              {
                label: "对比试验",
                value: `${detail.experimentBoard.compareCount} 组`,
              },
              {
                label: "研究批次",
                value: `${detail.experimentBoard.studyCount} 组`,
              },
              {
                label: "已完成对比",
                value: `${detail.experimentBoard.compareCompletedCount} 组`,
              },
            ]}
          />
          <div className="flex flex-wrap gap-2">
            <DrawerShortcut
              icon={<MicroscopeIcon className="size-4" />}
              label="查看对比试验"
              onClick={() => onOpenDrawer("studies")}
            />
            <DrawerShortcut
              icon={<Layers3Icon className="size-4" />}
              label="查看证据链"
              onClick={() => onOpenDrawer("trust")}
            />
          </div>
        </div>
      );
    case "report":
      return (
        <div className="space-y-4">
          <KeyValueGrid
            items={[
              {
                label: "最终结论",
                value:
                  finalReport?.summary_zh ?? "尚未形成最终结论，请继续推进研究与复核。",
              },
              {
                label: "结论边界",
                value:
                  finalReport?.report_overview?.allowed_claim_level ??
                  runtime?.allowed_claim_level ??
                  "尚未明确",
              },
              {
                label: "下一步建议",
                value:
                  finalReport?.report_overview?.recommended_next_step_zh ??
                  "等待主智能体给出交付判断与后续动作。",
              },
            ]}
          />
          <CompactList
            title="结论片段"
            emptyLabel="最终报告生成后，这里会显示结论片段。"
            items={conclusionSections.slice(0, 3).map((section) => ({
              title: section.title_zh ?? "结论片段",
              description: section.summary_zh ?? undefined,
            }))}
          />
          <div className="flex flex-wrap gap-2">
            <DrawerShortcut
              icon={<Layers3Icon className="size-4" />}
              label="查看证据与可信度"
              onClick={() => onOpenDrawer("trust")}
            />
            <DrawerShortcut
              icon={<ScrollTextIcon className="size-4" />}
              label="查看交付判断"
              onClick={() => onOpenDrawer("operator")}
            />
          </div>
        </div>
      );
    default:
      return null;
  }
}

function DrawerShortcut({
  icon,
  label,
  onClick,
}: {
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <Button size="sm" variant="outline" onClick={onClick}>
      {icon}
      {label}
    </Button>
  );
}

function KeyValueGrid({
  items,
}: {
  items: readonly { label: string; value: string }[];
}) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {items.map((item) => (
        <article
          key={item.label}
          className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-3"
        >
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            {item.label}
          </div>
          <div className="mt-2 text-sm leading-6 text-slate-800">{item.value}</div>
        </article>
      ))}
    </div>
  );
}

function TokenList({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: readonly string[];
  emptyLabel: string;
}) {
  return (
    <section className="space-y-2">
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      {items.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <span
              key={item}
              className="rounded-full border border-slate-200/80 bg-white px-3 py-1.5 text-sm text-slate-700"
            >
              {item}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-sm leading-6 text-slate-600">{emptyLabel}</p>
      )}
    </section>
  );
}

function CompactList({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: readonly {
    title: string;
    meta?: string;
    description?: string;
  }[];
  emptyLabel: string;
}) {
  return (
    <section className="space-y-3">
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      {items.length > 0 ? (
        <div className="space-y-2">
          {items.map((item) => (
            <article
              key={[item.title, item.meta, item.description].join("-")}
              className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-3"
            >
              <div className="text-sm font-semibold text-slate-900">{item.title}</div>
              {item.meta ? (
                <div className="mt-1 text-xs text-slate-500">{item.meta}</div>
              ) : null}
              {item.description ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  {item.description}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <p className="text-sm leading-6 text-slate-600">{emptyLabel}</p>
      )}
    </section>
  );
}
