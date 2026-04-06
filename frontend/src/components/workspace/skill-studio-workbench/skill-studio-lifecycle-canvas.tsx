"use client";

import { type ReactNode, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  SecondaryLayerHost,
  WorkbenchFlow,
} from "@/components/workspace/agentic-workbench";
import {
  SKILL_STUDIO_BINDING_ROLE_IDS,
  labelOfSkillStudioBindingRoleId,
  type SkillStudioLifecycleBindingTarget,
} from "@/components/workspace/skill-studio-workbench.utils";

import type { SkillStudioDetailModel } from "./skill-studio-detail-model";
import type { SkillStudioSessionModel } from "./skill-studio-session-model";
import { SkillStudioTestingEvidence } from "./skill-studio-testing-evidence";

type DrawerId = "testing" | "publish" | "graph";

const DEFAULT_DRAWER_BY_MODULE: Record<string, DrawerId> = {
  intent: "publish",
  draft: "publish",
  evaluation: "testing",
  "release-prep": "publish",
  lifecycle: "publish",
  graph: "graph",
};

function resolveDefaultDrawerId(moduleId: string): DrawerId {
  return DEFAULT_DRAWER_BY_MODULE[moduleId] ?? "publish";
}

type SkillStudioLifecycleCanvasProps = {
  session: SkillStudioSessionModel;
  detail: SkillStudioDetailModel;
  isMock: boolean;
  enabled: boolean;
  versionNote: string;
  explicitBindingRoleIds: string[];
  busy: boolean;
  canPublish: boolean;
  canRollback: boolean;
  onEnabledChange: (nextValue: boolean) => void;
  onVersionNoteChange: (nextValue: string) => void;
  onToggleBindingRole: (roleId: string) => void;
  onSaveLifecycle: () => void;
  onPublish: () => void;
  onRollback: () => void;
};

export function SkillStudioLifecycleCanvas({
  session,
  detail,
  isMock,
  enabled,
  versionNote,
  explicitBindingRoleIds,
  busy,
  canPublish,
  canRollback,
  onEnabledChange,
  onVersionNoteChange,
  onToggleBindingRole,
  onSaveLifecycle,
  onPublish,
  onRollback,
}: SkillStudioLifecycleCanvasProps) {
  const [activeDrawerId, setActiveDrawerId] = useState<DrawerId>(() =>
    resolveDefaultDrawerId(session.activeModuleId),
  );
  const activeModule =
    session.modules.find((module) => module.expanded) ?? session.modules[0];
  const pendingSummary =
    session.negotiation.pendingApprovalCount > 0
      ? `${session.negotiation.pendingApprovalCount} 项待修正`
      : "当前无阻塞项";
  const relationshipSummary =
    detail.graph.relationshipCount > 0
      ? `${detail.graph.relationshipCount} 条技能关系`
      : "关系网络待建立";

  useEffect(() => {
    setActiveDrawerId(resolveDefaultDrawerId(session.activeModuleId));
  }, [session.activeModuleId]);

  const drawerLayers = useMemo(
    () => [
      {
        id: "testing",
        label: "验证与试跑证据",
        content: <SkillStudioTestingEvidence evaluate={detail.evaluate} />,
      },
      {
        id: "publish",
        label: "发布状态与版本信息",
        content: <PublishDrawer detail={detail} />,
      },
      {
        id: "graph",
        label: "关系网络",
        content: <GraphDrawer detail={detail} />,
      },
    ],
    [detail],
  );

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <section className="rounded-[24px] border border-orange-200/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(252,246,241,0.96))] px-4 py-4 shadow-[0_18px_40px_rgba(249,115,22,0.08)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-orange-700">
              技能总览
            </div>
            <h3 className="mt-2 text-lg font-semibold text-slate-950">
              围绕定义、验证、发布与挂载维护整条技能生命周期。
            </h3>
          </div>

          <div className="grid min-w-[280px] flex-1 gap-3 md:grid-cols-3">
            <OverviewMetric
              label="当前焦点"
              value={activeModule?.title ?? "等待开始"}
            />
            <OverviewMetric label="待确认事项" value={pendingSummary} />
            <OverviewMetric label="技能关系" value={relationshipSummary} />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {session.modules.map((module, index) => (
            <FlowIndexChip
              key={module.id}
              index={index + 1}
              title={module.title}
              status={module.status}
              active={module.expanded}
            />
          ))}
        </div>
      </section>

      <WorkbenchFlow
        items={session.modules.map((module) => ({
          id: module.id,
          title: module.title,
          status: module.status,
          summary: module.summary,
          expanded: module.expanded,
          content: renderLifecycleContent({
            moduleId: module.id,
            detail,
            isMock,
            enabled,
            versionNote,
            explicitBindingRoleIds,
            busy,
            canPublish,
            canRollback,
            onEnabledChange,
            onVersionNoteChange,
            onToggleBindingRole,
            onSaveLifecycle,
            onPublish,
            onRollback,
          }),
        }))}
      />

      <SecondaryLayerHost
        layers={drawerLayers}
        activeLayerId={activeDrawerId}
        className="border-slate-200/70 bg-transparent"
      />
    </div>
  );
}

function OverviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-white/90 bg-white/88 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold leading-6 text-slate-900">
        {value}
      </div>
    </article>
  );
}

function FlowIndexChip({
  index,
  title,
  status,
  active,
}: {
  index: number;
  title: string;
  status: string;
  active: boolean;
}) {
  return (
    <article
      className={[
        "inline-flex items-center gap-2 rounded-full border px-3 py-2 transition-colors",
        active
          ? "border-orange-200/80 bg-orange-50/80"
          : "border-slate-200/80 bg-white/88",
      ].join(" ")}
    >
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {String(index).padStart(2, "0")}
      </div>
      <div className="text-sm font-semibold text-slate-950">{title}</div>
      <div className="text-xs text-slate-600">{status}</div>
    </article>
  );
}

function localizeGateStatus(status: string | undefined) {
  switch (status) {
    case "passed":
      return "已通过";
    case "blocked":
      return "已阻塞";
    case "pending":
      return "待处理";
    default:
      return status ?? "待处理";
  }
}

function renderLifecycleContent({
  moduleId,
  detail,
  isMock,
  enabled,
  versionNote,
  explicitBindingRoleIds,
  busy,
  canPublish,
  canRollback,
  onEnabledChange,
  onVersionNoteChange,
  onToggleBindingRole,
  onSaveLifecycle,
  onPublish,
  onRollback,
}: {
  moduleId: string;
  detail: SkillStudioDetailModel;
  isMock: boolean;
  enabled: boolean;
  versionNote: string;
  explicitBindingRoleIds: string[];
  busy: boolean;
  canPublish: boolean;
  canRollback: boolean;
  onEnabledChange: (nextValue: boolean) => void;
  onVersionNoteChange: (nextValue: string) => void;
  onToggleBindingRole: (roleId: string) => void;
  onSaveLifecycle: () => void;
  onPublish: () => void;
  onRollback: () => void;
}): ReactNode {
  switch (moduleId) {
    case "intent":
      return (
        <KeyValueGrid
          items={[
            { label: "技能名称", value: detail.define.skillName },
            { label: "主要目标", value: detail.define.skillGoal },
            { label: "创建助手", value: detail.assistant.label },
          ]}
        />
      );
    case "draft":
      return (
        <div className="space-y-4">
          <TokenList
            title="触发条件"
            items={detail.define.triggerConditions}
            emptyLabel="尚未补充触发条件。"
          />
          <TokenList
            title="专家约束"
            items={detail.define.constraints}
            emptyLabel="尚未补充专家约束。"
          />
          <TokenList
            title="成功标准"
            items={detail.define.acceptanceCriteria}
            emptyLabel="尚未补充成功标准。"
          />
        </div>
      );
    case "evaluation":
      return (
        <KeyValueGrid
          items={[
            { label: "验证状态", value: detail.evaluate.status },
            { label: "错误数量", value: String(detail.evaluate.errorCount) },
            { label: "警告数量", value: String(detail.evaluate.warningCount) },
          ]}
        />
      );
    case "release-prep":
      return (
        <div className="space-y-4">
          <KeyValueGrid
            items={[
              { label: "发布门禁", value: String(detail.publish.gateCount) },
              { label: "阻塞门禁", value: String(detail.publish.blockedGateCount) },
              { label: "产物分组", value: String(detail.artifactGroups.length) },
            ]}
          />
          <CompactList
            title="下一步动作"
            items={detail.publish.nextActions.map((item) => ({
              title: item,
            }))}
            emptyLabel="当前没有额外的发布准备动作。"
          />
        </div>
      );
    case "lifecycle":
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-3">
            <div className="text-sm font-semibold text-slate-950">启用状态</div>
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <span>{enabled ? "已启用" : "未启用"}</span>
              <Switch
                checked={enabled}
                onCheckedChange={onEnabledChange}
                disabled={isMock}
              />
            </div>
          </div>

          <KeyValueGrid
            items={[
              {
                label: "活动版本",
                value: detail.publish.activeRevisionId ?? "草稿中",
              },
              {
                label: "已发布版本",
                value: detail.publish.publishedRevisionId ?? "尚未发布",
              },
              {
                label: "回退目标",
                value: detail.publish.rollbackTargetId ?? "暂无",
              },
            ]}
          />

          <section className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-950">版本说明</h4>
            <Textarea
              className="min-h-28"
              value={versionNote}
              onChange={(event) => onVersionNoteChange(event.target.value)}
              placeholder="记录这一版解决了什么问题，还保留了哪些边界。"
            />
          </section>

          <section className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-950">显式挂载角色</h4>
            <div className="grid gap-2 md:grid-cols-2">
              {SKILL_STUDIO_BINDING_ROLE_IDS.map((roleId) => {
                const selected = explicitBindingRoleIds.includes(roleId);

                return (
                  <button
                    key={roleId}
                    type="button"
                    disabled={isMock}
                    className={`rounded-2xl border px-3 py-3 text-left text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${
                      selected
                        ? "border-orange-200 bg-orange-50 text-orange-900"
                        : "border-slate-200 bg-slate-50 text-slate-700"
                    }`}
                    onClick={() => onToggleBindingRole(roleId)}
                  >
                    {labelOfSkillStudioBindingRoleId(roleId)}
                  </button>
                );
              })}
            </div>
          </section>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" disabled={busy || isMock} onClick={onSaveLifecycle}>
              保存生命周期设置
            </Button>
            <Button disabled={busy || isMock || !canPublish} onClick={onPublish}>
              发布当前草案
            </Button>
            <Button
              variant="outline"
              disabled={busy || isMock || !canRollback}
              onClick={onRollback}
            >
              回退到上一版本
            </Button>
          </div>
        </div>
      );
    case "graph":
      return (
        <div className="space-y-4">
          <KeyValueGrid
            items={[
              { label: "关联技能", value: String(detail.graph.relationshipCount) },
              { label: "高影响连接", value: String(detail.graph.highImpactCount) },
              { label: "上游技能", value: String(detail.graph.upstreamCount) },
            ]}
          />
          <CompactList
            title="关系摘要"
            items={detail.graph.relatedSkills.slice(0, 3).map((item) => ({
              title: item.skillName,
              meta: `${item.category} · score ${item.strongestScore.toFixed(2)}`,
              description: item.reasons[0] ?? item.description,
            }))}
            emptyLabel="当前还没有建立技能关系。"
          />
        </div>
      );
    default:
      return null;
  }
}

function PublishDrawer({ detail }: { detail: SkillStudioDetailModel }) {
  return (
    <section className="space-y-3 rounded-[24px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
      <KeyValueGrid
        items={[
          { label: "版本数量", value: String(detail.publish.revisionCount) },
          { label: "绑定数量", value: String(detail.publish.bindingCount) },
          { label: "回退目标", value: detail.publish.rollbackTargetId ?? "暂无" },
        ]}
      />
      <CompactList
        title="发布门禁"
        items={detail.publish.gates.map((gate) => ({
          title: gate.label,
          meta: localizeGateStatus(gate.status),
        }))}
        emptyLabel="当前没有发布门禁信息。"
      />
      <CompactList
        title="绑定目标"
        items={detail.publish.bindingTargets.map(
          (target: SkillStudioLifecycleBindingTarget) => ({
            title: labelOfSkillStudioBindingRoleId(target.role_id),
            meta: target.mode,
            description: target.target_skills.join("、"),
          }),
        )}
        emptyLabel="当前没有显式绑定目标。"
      />
    </section>
  );
}

function GraphDrawer({ detail }: { detail: SkillStudioDetailModel }) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
      <CompactList
        title="相关技能"
        items={detail.graph.relatedSkills.map((item) => ({
          title: item.skillName,
          meta: `${item.category} · score ${item.strongestScore.toFixed(2)}`,
          description: item.reasons[0] ?? item.description,
        }))}
        emptyLabel="当前还没有图谱关联。"
      />
    </section>
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
          <div className="mt-2 text-sm leading-6 text-slate-800">
            {item.value}
          </div>
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
              <div className="text-sm font-semibold text-slate-900">
                {item.title}
              </div>
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
