"use client";

import { MessageSquareIcon, SparklesIcon } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  NegotiationRail,
  SessionSummaryBar,
  ThreadHeader,
  WORKBENCH_COPY,
  WorkbenchShell,
} from "@/components/workspace/agentic-workbench";
import { useArtifacts } from "@/components/workspace/artifacts";
import { InputBox } from "@/components/workspace/input-box";
import { MessageList } from "@/components/workspace/messages";
import { useThread } from "@/components/workspace/messages/context";
import type { SkillStudioAgentOption } from "@/components/workspace/skill-studio-agent-options";
import {
  buildSkillStudioBindingTargets,
  findSkillLifecycleSummary,
  type SkillStudioLifecycleBindingTarget,
} from "@/components/workspace/skill-studio-workbench.utils";
import { useArtifactContent } from "@/core/artifacts/hooks";
import type {
  SkillGraphResponse,
  SkillLifecycleRecord,
  SkillLifecycleSummary,
} from "@/core/skills/api";
import {
  usePublishSkill,
  useRollbackSkillRevision,
  useSkillGraph,
  useSkillLifecycle,
  useSkillLifecycleSummaries,
  useUpdateSkillLifecycle,
} from "@/core/skills/hooks";
import type { AgentThreadContext } from "@/core/threads";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import {
  buildSkillStudioDetailModel,
  type PublishReadinessPayload,
  type SkillDraftPayload,
  type SkillPackagePayload,
  type SkillStudioThreadState,
  type TestMatrixPayload,
  type ValidationPayload,
} from "./skill-studio-detail-model";
import { SkillStudioLifecycleCanvas } from "./skill-studio-lifecycle-canvas";
import { buildSkillStudioSessionModel } from "./skill-studio-session-model";

type SkillStudioAgenticWorkbenchProps = {
  threadId: string;
  isNewThread: boolean;
  activeAgentName: string;
  activeAssistantLabel: string;
  assistantDescription: string;
  agentOptions: SkillStudioAgentOption[];
  agentSelectionLocked: boolean;
  agentSelectorEnabled: boolean;
  onAgentChange: (value: string) => void;
  mobileNegotiationRailVisible: boolean;
  onToggleChatRail: () => void;
  isUploading: boolean;
  context: Omit<
    AgentThreadContext,
    "thread_id" | "is_plan_mode" | "thinking_enabled" | "subagent_enabled"
  > & {
    mode: "flash" | "thinking" | "pro" | "ultra" | undefined;
    reasoning_effort?: "minimal" | "low" | "medium" | "high";
  };
  onContextChange: (
    context: Omit<
      AgentThreadContext,
      "thread_id" | "is_plan_mode" | "thinking_enabled" | "subagent_enabled"
    > & {
      mode: "flash" | "thinking" | "pro" | "ultra" | undefined;
      reasoning_effort?: "minimal" | "low" | "medium" | "high";
    },
  ) => void;
  onSubmit: (message: PromptInputMessage) => void;
  onStop: () => Promise<void>;
};

function safeJsonParse<T>(content?: string | null) {
  if (!content) return null;
  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

function pickArtifact(artifacts: string[], suffix: string) {
  return artifacts.find((artifact) => artifact.endsWith(suffix)) ?? null;
}

function collectSkillStudioArtifacts(
  threadArtifacts: unknown,
  studioArtifacts: SkillStudioThreadState["artifact_virtual_paths"],
) {
  return [
    ...(Array.isArray(threadArtifacts) ? threadArtifacts : []),
    ...(Array.isArray(studioArtifacts) ? studioArtifacts : []),
  ].filter((artifact, index, all): artifact is string => {
    return (
      typeof artifact === "string" &&
      artifact.includes("/submarine/skill-studio/") &&
      all.indexOf(artifact) === index
    );
  });
}

function toChineseStatus(status: string | null | undefined) {
  switch (status) {
    case "ready_for_review":
      return "待评审";
    case "needs_revision":
      return "待修订";
    case "draft_only":
      return "仅有草案";
    case "ready_for_dry_run":
      return "待试跑";
    case "draft_ready":
      return "草案就绪";
    case "published":
      return "已发布";
    case "rollback_available":
      return "可回退";
    case "blocked":
      return "已阻塞";
    case "passed":
      return "已通过";
    case "failed":
      return "未通过";
    default:
      return status ?? "待处理";
  }
}

export function SkillStudioAgenticWorkbench({
  threadId,
  isNewThread,
  activeAgentName,
  activeAssistantLabel,
  assistantDescription,
  agentOptions,
  agentSelectionLocked,
  agentSelectorEnabled,
  onAgentChange,
  mobileNegotiationRailVisible,
  onToggleChatRail,
  isUploading,
  context,
  onContextChange,
  onSubmit,
  onStop,
}: SkillStudioAgenticWorkbenchProps) {
  const { thread, isMock } = useThread();
  const { setOpen: setArtifactsOpen } = useArtifacts();
  const studioState =
    thread.values.submarine_skill_studio != null &&
    typeof thread.values.submarine_skill_studio === "object"
      ? (thread.values.submarine_skill_studio as SkillStudioThreadState)
      : null;
  const studioArtifacts = useMemo(
    () =>
      collectSkillStudioArtifacts(
        thread.values.artifacts,
        studioState?.artifact_virtual_paths,
      ),
    [studioState?.artifact_virtual_paths, thread.values.artifacts],
  );
  const draftPath = pickArtifact(studioArtifacts, "/skill-draft.json");
  const validationPath = studioArtifacts.find((item) =>
    item.includes("/validation-report."),
  );
  const testMatrixPath = studioArtifacts.find((item) =>
    item.includes("/test-matrix."),
  );
  const publishReadinessPath = studioArtifacts.find((item) =>
    item.includes("/publish-readiness."),
  );
  const skillPackagePath =
    studioState?.package_virtual_path ??
    pickArtifact(studioArtifacts, "/skill-package.json") ??
    "";

  const { content: draftContent } = useArtifactContent({
    filepath: draftPath ?? "",
    threadId,
    enabled: Boolean(draftPath),
  });
  const { content: validationContent } = useArtifactContent({
    filepath: validationPath ?? "",
    threadId,
    enabled: Boolean(validationPath),
  });
  const { content: testMatrixContent } = useArtifactContent({
    filepath: testMatrixPath ?? "",
    threadId,
    enabled: Boolean(testMatrixPath),
  });
  const { content: publishReadinessContent } = useArtifactContent({
    filepath: publishReadinessPath ?? "",
    threadId,
    enabled: Boolean(publishReadinessPath),
  });
  const { content: skillPackageContent } = useArtifactContent({
    filepath: skillPackagePath,
    threadId,
    enabled: Boolean(skillPackagePath),
  });

  const draft = useMemo(
    () => safeJsonParse<SkillDraftPayload>(draftContent),
    [draftContent],
  );
  const validation = useMemo(
    () => safeJsonParse<ValidationPayload>(validationContent),
    [validationContent],
  );
  const testMatrix = useMemo(
    () => safeJsonParse<TestMatrixPayload>(testMatrixContent),
    [testMatrixContent],
  );
  const publishReadiness = useMemo(
    () => safeJsonParse<PublishReadinessPayload>(publishReadinessContent),
    [publishReadinessContent],
  );
  const skillPackage = useMemo(
    () => safeJsonParse<SkillPackagePayload>(skillPackageContent),
    [skillPackageContent],
  );
  const skillName = draft?.skill_name ?? studioState?.skill_name ?? null;
  const { lifecycleSummaries } = useSkillLifecycleSummaries({ enabled: !isMock });
  const lifecycleSummary = useMemo<SkillLifecycleSummary | null>(
    () => {
      const summary = findSkillLifecycleSummary(lifecycleSummaries, skillName);
      return summary
        ? {
            ...summary,
            version_note: summary.version_note ?? undefined,
          }
        : null;
    },
    [lifecycleSummaries, skillName],
  );
  const lifecycleQuery = useSkillLifecycle({
    skillName: skillName ?? undefined,
    enabled: Boolean(skillName) && !isMock,
  });
  const lifecycleDetail: SkillLifecycleRecord | null = lifecycleQuery.data ?? null;
  const skillGraphQuery = useSkillGraph({
    skillName: skillName ?? undefined,
    isMock: isMock === true,
    enabled: Boolean(skillName),
  });
  const skillGraph: SkillGraphResponse | null = skillGraphQuery.data ?? null;
  const detail = useMemo(
    () =>
      buildSkillStudioDetailModel({
        studioState,
        draft,
        skillPackage,
        validation,
        testMatrix,
        publishReadiness,
        lifecycleSummary,
        lifecycleDetail,
        skillGraph,
        studioArtifacts,
      }),
    [
      draft,
      lifecycleDetail,
      lifecycleSummary,
      publishReadiness,
      skillGraph,
      skillPackage,
      studioArtifacts,
      studioState,
      testMatrix,
      validation,
    ],
  );
  const session = useMemo(
    () =>
      buildSkillStudioSessionModel({
        isNewThread,
        persistedAssistantMode: studioState?.assistant_mode ?? null,
        hasDraftArtifact: Boolean(draftPath),
        validationStatus:
          validation?.status ?? studioState?.validation_status ?? "draft_only",
        testStatus: testMatrix?.status ?? studioState?.test_status ?? "draft_only",
        publishStatus:
          publishReadiness?.status ?? studioState?.publish_status ?? "draft_only",
        errorCount: validation?.error_count ?? studioState?.error_count ?? 0,
        warningCount: validation?.warning_count ?? studioState?.warning_count ?? 0,
        blockingCount:
          (publishReadiness?.blocking_count ?? 0) +
          (testMatrix?.blocking_count ?? 0) +
          (validation?.error_count ?? 0),
        graphRelationshipCount: detail.graph.relationshipCount,
      }),
    [
      detail.graph.relationshipCount,
      draftPath,
      isNewThread,
      publishReadiness?.blocking_count,
      publishReadiness?.status,
      studioState?.assistant_mode,
      studioState?.error_count,
      studioState?.publish_status,
      studioState?.test_status,
      studioState?.validation_status,
      studioState?.warning_count,
      testMatrix?.blocking_count,
      testMatrix?.status,
      validation?.error_count,
      validation?.status,
      validation?.warning_count,
    ],
  );
  const [publishEnabled, setPublishEnabled] = useState(detail.publish.enabled);
  const [versionNote, setVersionNote] = useState(detail.publish.versionNote);
  const [explicitBindingRoleIds, setExplicitBindingRoleIds] = useState<string[]>(
    detail.publish.explicitBindingRoleIds,
  );

  useEffect(() => {
    setPublishEnabled(detail.publish.enabled);
    setVersionNote(detail.publish.versionNote);
    setExplicitBindingRoleIds(detail.publish.explicitBindingRoleIds);
  }, [
    detail.publish.enabled,
    detail.publish.explicitBindingRoleIds,
    detail.publish.versionNote,
  ]);

  const updateLifecycle = useUpdateSkillLifecycle();
  const publishSkillMutation = usePublishSkill();
  const rollbackSkillRevision = useRollbackSkillRevision();
  const busy =
    updateLifecycle.isPending ||
    publishSkillMutation.isPending ||
    rollbackSkillRevision.isPending;
  const bindingTargets = useMemo<SkillStudioLifecycleBindingTarget[]>(
    () =>
      skillName
        ? buildSkillStudioBindingTargets(skillName, explicitBindingRoleIds)
        : [],
    [explicitBindingRoleIds, skillName],
  );
  const packageArchivePath =
    studioState?.package_archive_virtual_path ??
    skillPackage?.package_archive_virtual_path ??
    skillPackage?.archive_virtual_path ??
    null;

  const saveLifecycle = useCallback(async () => {
    if (!skillName) return;
    try {
      await updateLifecycle.mutateAsync({
        skillName,
        enabled: publishEnabled,
        version_note: versionNote,
        binding_targets: bindingTargets,
      });
      toast.success("生命周期设置已保存。");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "保存生命周期设置失败。");
    }
  }, [bindingTargets, publishEnabled, skillName, updateLifecycle, versionNote]);

  const publish = useCallback(async () => {
    if (!packageArchivePath) return;
    try {
      await publishSkillMutation.mutateAsync({
        thread_id: threadId,
        path: packageArchivePath,
        enable: publishEnabled,
        version_note: versionNote,
        binding_targets: bindingTargets,
      });
      toast.success("技能已发布。");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "发布技能失败。");
    }
  }, [
    bindingTargets,
    packageArchivePath,
    publishEnabled,
    publishSkillMutation,
    threadId,
    versionNote,
  ]);

  const rollback = useCallback(async () => {
    if (!skillName || !detail.publish.rollbackTargetId) return;
    try {
      await rollbackSkillRevision.mutateAsync({
        skillName,
        revision_id: detail.publish.rollbackTargetId,
      });
      toast.success("已回退到指定版本。");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "回退失败。");
    }
  }, [detail.publish.rollbackTargetId, rollbackSkillRevision, skillName]);

  const openNegotiation = useCallback(() => {
    if (!mobileNegotiationRailVisible) {
      onToggleChatRail();
      window.setTimeout(() => {
        const rail = document.getElementById("skill-studio-chat-rail");
        rail?.scrollIntoView({ behavior: "smooth", block: "start" });
        const input = rail?.querySelector("textarea");
        if (input instanceof HTMLTextAreaElement) {
          input.focus();
        }
      }, 50);
      return;
    }

    const rail = document.getElementById("skill-studio-chat-rail");
    rail?.scrollIntoView({ behavior: "smooth", block: "start" });
    const input = rail?.querySelector("textarea");
    if (input instanceof HTMLTextAreaElement) {
      input.focus();
    }
  }, [mobileNegotiationRailVisible, onToggleChatRail]);

  const activeModule = session.modules.find((module) => module.expanded) ?? session.modules[0];
  const threadTitle =
    typeof thread.values.title === "string" && thread.values.title.length > 0
      ? thread.values.title
      : detail.define.skillTitle;

  const nav = (
    <div className="flex h-full min-h-0 flex-col gap-5">
      <section className="rounded-[26px] border border-orange-200/70 bg-[radial-gradient(circle_at_top_right,rgba(249,115,22,0.16),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(252,246,241,0.96))] p-4 shadow-[0_22px_60px_rgba(249,115,22,0.10)]">
        <div className="flex items-center gap-2 text-orange-700">
          <SparklesIcon className="size-4" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.22em]">
            技能生命周期工作台
          </span>
        </div>
        <h2 className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
          {threadTitle}
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          从技能意图到发布版本，所有定义、验证、试跑、发布和关系网络都集中在这一张主画布里。
        </p>
        <div className="mt-4 grid gap-2">
          <NavMetric label="当前焦点" value={activeModule?.title ?? "等待开始"} />
          <NavMetric
            label="待确认事项"
            value={
              session.negotiation.pendingApprovalCount > 0
                ? `${session.negotiation.pendingApprovalCount} 项`
                : "当前无阻塞项"
            }
          />
          <NavMetric label="技能关系" value={`${detail.graph.relationshipCount} 条`} />
        </div>
      </section>

      <section className="min-h-0 rounded-[24px] border border-slate-200/80 bg-white/92 p-4">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
          生命周期推进流
        </div>
        <div className="mt-3 space-y-2">
          {session.modules.map((module, index) => (
            <article
              key={module.id}
              className={cn(
                "rounded-2xl border px-3 py-3 transition-colors",
                module.expanded
                  ? "border-orange-200/80 bg-orange-50/70"
                  : "border-slate-200/80 bg-slate-50/70",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold text-slate-500">
                    {String(index + 1).padStart(2, "0")}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-slate-950">
                    {module.title}
                  </div>
                </div>
                <span className="rounded-full border border-slate-200/80 bg-white px-2.5 py-1 text-xs text-slate-600">
                  {module.status}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );

  const main = (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <ThreadHeader
        title={threadTitle}
        subtitle={`${activeAssistantLabel} 负责这条技能生命周期线程的定义、验证与发布协商。`}
        statusLabel={activeModule?.status ?? "处理中"}
        actions={
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={onToggleChatRail}>
              <MessageSquareIcon className="size-4" />
              {mobileNegotiationRailVisible ? "收起协商区" : "展开协商区"}
            </Button>
          </div>
        }
      />
      <SessionSummaryBar
        pendingApprovals={session.negotiation.pendingApprovalCount}
        interruptionVisible={session.negotiation.interruptionVisible}
        summary={session.negotiation.question ?? WORKBENCH_COPY.common.negotiationHint}
      />
      <div className="min-h-0 flex-1">
        <SkillStudioLifecycleCanvas
          session={session}
          detail={detail}
          enabled={publishEnabled}
          versionNote={versionNote}
          explicitBindingRoleIds={explicitBindingRoleIds}
          busy={busy}
          canPublish={Boolean(packageArchivePath)}
          canRollback={Boolean(detail.publish.rollbackTargetId)}
          onEnabledChange={setPublishEnabled}
          onVersionNoteChange={setVersionNote}
          onToggleBindingRole={(roleId) =>
            setExplicitBindingRoleIds((current) =>
              current.includes(roleId)
                ? current.filter((item) => item !== roleId)
                : [...current, roleId],
            )
          }
          onSaveLifecycle={saveLifecycle}
          onPublish={publish}
          onRollback={rollback}
          onOpenNegotiation={openNegotiation}
        />
      </div>
    </div>
  );

  const negotiation = (
    <NegotiationRail
      title={
        <div className="space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            {WORKBENCH_COPY.common.negotiationRailTitle}
          </div>
          <h3 className="text-base font-semibold text-slate-950">
            在这里直接补充技能规则、修改验证口径或调整发布策略。
          </h3>
        </div>
      }
      question={
        <p className="rounded-xl border border-amber-200/80 bg-amber-50/70 px-3 py-2 text-sm text-amber-900">
          {session.negotiation.question ?? "当前没有阻塞项，可继续推进技能生命周期。"}
        </p>
      }
      actions={
        <div className="space-y-2">
          <div className="text-xs leading-5 text-slate-500">
            开始创建后会锁定创建助手，但你仍然可以随时在这里协商修改技能方案。
          </div>
          <Select
            value={activeAgentName}
            onValueChange={onAgentChange}
            disabled={agentSelectionLocked || !agentSelectorEnabled}
          >
            <SelectTrigger className="w-full bg-white/90">
              <SelectValue placeholder="选择技能创建助手" />
            </SelectTrigger>
            <SelectContent>
              {agentOptions.map((option) => (
                <SelectItem key={option.name} value={option.name}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      }
      body={
        <div className="flex h-full min-h-0 flex-col gap-3">
          <section className="rounded-2xl border border-slate-200/80 bg-white/90 px-4 py-3">
            <div className="text-sm font-semibold text-slate-950">{activeAssistantLabel}</div>
            <p className="mt-1 text-sm leading-6 text-slate-600">{assistantDescription}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
              <span className="rounded-full border border-slate-200/80 bg-slate-50 px-2.5 py-1">
                验证：{toChineseStatus(session.summary.validationStatus)}
              </span>
              <span className="rounded-full border border-slate-200/80 bg-slate-50 px-2.5 py-1">
                试跑：{toChineseStatus(session.summary.testStatus)}
              </span>
              <span className="rounded-full border border-slate-200/80 bg-slate-50 px-2.5 py-1">
                发布：{toChineseStatus(session.summary.publishStatus)}
              </span>
            </div>
          </section>

          <div
            id="skill-studio-chat-rail"
            className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-slate-200/80 bg-white/84"
          >
            <MessageList
              className="flex-1 justify-start"
              paddingBottom={32}
              threadId={threadId}
              thread={thread}
            />
          </div>

          <InputBox
            className="w-full bg-transparent"
            isNewThread={isNewThread}
            showNewThreadSuggestions={false}
            threadId={threadId}
            autoFocus={isNewThread}
            status={thread.error ? "error" : thread.isLoading ? "streaming" : "ready"}
            context={context}
            disabled={env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isUploading}
            onContextChange={onContextChange}
            onSubmit={onSubmit}
            onStop={onStop}
          />

          <Button variant="outline" onClick={() => setArtifactsOpen(true)}>
            打开技能产物
          </Button>
        </div>
      }
      footer={
        <p className="text-xs leading-5 text-slate-600">
          不需要额外的暂停或恢复按钮，直接在聊天框里告诉主智能体“先停一下，修改技能方案”即可。
        </p>
      }
    />
  );

  return (
    <WorkbenchShell
      mobileNegotiationRailVisible={mobileNegotiationRailVisible}
      nav={nav}
      main={main}
      negotiation={negotiation}
    />
  );
}

function NavMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/80 bg-white/88 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
