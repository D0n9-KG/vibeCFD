"use client";

import { MessageSquareIcon } from "lucide-react";
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
  ThreadHeader,
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
import { buildProgressPreviewFromMessage } from "@/core/messages/utils";
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
import { resolveThreadDisplayTitle } from "@/core/threads/utils";
import { env } from "@/env";

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

const DEFAULT_ENGLISH_SKILL_GOAL = [
  "De",
  "fine how Claude Code and reporting subagents should decide whether a submarine CFD run is trustworthy, needs review, or should be rerun.",
].join("");

function localizeSkillStudioGoal(goal: string) {
  if (goal === DEFAULT_ENGLISH_SKILL_GOAL) {
    return "定义 Claude Code 与报告子代理如何判断一次潜艇 CFD 任务是否可信、是否需要复核，或者是否应当重新计算。";
  }

  return goal;
}

function resolveSkillStudioHeaderStatusLabel(status: string) {
  switch (status) {
    case "published":
      return "已发布";
    case "ready_for_review":
      return "待评审";
    case "draft_ready":
      return "待发布";
    case "rollback_available":
      return "可回退";
    default:
      return "处理中";
  }
}

export function SkillStudioAgenticWorkbench({
  threadId,
  isNewThread,
  activeAgentName,
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
  const latestVisiblePreview = useMemo(() => {
    const latestVisibleMessage = [...thread.messages]
      .reverse()
      .find((message) => message.type === "ai" || message.type === "human");

    return latestVisibleMessage
      ? buildProgressPreviewFromMessage(latestVisibleMessage)
      : null;
  }, [thread.messages]);
  const threadErrorMessage =
    thread.error instanceof Error
      ? thread.error.message
      : typeof thread.error === "string"
        ? thread.error
        : null;

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
  const lifecycleSummary = useMemo<SkillLifecycleSummary | null>(() => {
    const summary = findSkillLifecycleSummary(lifecycleSummaries, skillName);
    return summary
      ? {
          ...summary,
          version_note: summary.version_note ?? undefined,
        }
      : null;
  }, [lifecycleSummaries, skillName]);

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
        isLoading: thread.isLoading,
        errorMessage: threadErrorMessage,
        latestVisiblePreview,
      }),
    [
      detail.graph.relationshipCount,
      draftPath,
      latestVisiblePreview,
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
      thread.isLoading,
      validation?.error_count,
      validation?.status,
      validation?.warning_count,
      threadErrorMessage,
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
      toast.success("技能生命周期设置已保存。");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "保存技能生命周期设置失败。");
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

  const threadTitle = resolveThreadDisplayTitle(
    thread.values.title,
    detail.define.skillTitle,
  );
  const showAssistantSelector = agentSelectorEnabled && !agentSelectionLocked;

  const main = (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <ThreadHeader
        title={threadTitle}
        subtitle={localizeSkillStudioGoal(detail.define.skillGoal)}
        statusLabel={resolveSkillStudioHeaderStatusLabel(session.summary.publishStatus)}
        actions={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="xl:hidden"
              onClick={onToggleChatRail}
            >
              <MessageSquareIcon className="size-4" />
              {mobileNegotiationRailVisible ? "收起协商区" : "展开协商区"}
            </Button>
            {showAssistantSelector ? (
              <Select
                value={activeAgentName}
                onValueChange={onAgentChange}
                disabled={agentSelectionLocked || !agentSelectorEnabled}
              >
                <SelectTrigger className="w-[220px] bg-white/90">
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
            ) : null}
            <Button size="sm" variant="outline" onClick={() => setArtifactsOpen(true)}>
              打开技能产物
            </Button>
          </div>
        }
      />
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        <SkillStudioLifecycleCanvas
          session={session}
          detail={detail}
          isMock={Boolean(isMock)}
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
        />
      </div>
    </div>
  );

  const negotiation = (
    <NegotiationRail
      className="gap-2 p-2.5"
      title={<div className="px-1 text-sm font-semibold text-slate-900">协商区</div>}
      question={null}
      actions={null}
      body={
        <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white/84">
          <div id="skill-studio-chat-rail" className="min-h-0 flex-1 overflow-hidden">
            <MessageList
              className="flex-1 justify-start"
              paddingBottom={192}
              threadId={threadId}
              thread={thread}
            />
          </div>

          <div className="border-t border-slate-200/80 p-2.5">
            <InputBox
              className="w-full bg-transparent"
              textareaClassName="min-h-36"
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
          </div>
        </div>
      }
    />
  );

  return (
    <WorkbenchShell
      mobileNegotiationRailVisible={mobileNegotiationRailVisible}
      main={main}
      negotiation={negotiation}
    />
  );
}
