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
  shouldLoadSkillLifecycleDetail,
  type SkillStudioLifecycleBindingTarget,
} from "@/components/workspace/skill-studio-workbench.utils";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { buildProgressPreviewFromMessage } from "@/core/messages/utils";
import type {
  SkillGraphResponse,
  SkillLifecycleRecord,
  SkillLifecycleSummary,
} from "@/core/skills/api";
import {
  usePublishSkill,
  useRecordDryRunEvidence,
  useRollbackSkillRevision,
  useSkillGraph,
  useSkillLifecycle,
  useSkillLifecycleSummaries,
  useUpdateSkillLifecycle,
} from "@/core/skills/hooks";
import type { AgentThreadContext } from "@/core/threads";
import { isMissingThreadError } from "@/core/threads/error";
import { resolveThreadDisplayTitle } from "@/core/threads/utils";
import { env } from "@/env";

import {
  buildSkillStudioDetailModel,
  type DryRunEvidencePayload,
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
  const dryRunEvidenceMessageIds = useMemo(
    () =>
      thread.messages
        .filter((message) => message.type === "ai" || message.type === "human")
        .slice(-6)
        .map((message) => {
          const messageId = (message as { id?: unknown }).id;
          return typeof messageId === "string" && messageId ? messageId : null;
        })
        .filter((messageId): messageId is string => Boolean(messageId)),
    [thread.messages],
  );
  const threadErrorMessage =
    thread.error instanceof Error
      ? thread.error.message
      : typeof thread.error === "string"
        ? thread.error
        : null;
  const hasMissingRuntimeThread = isMissingThreadError(thread.error);

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
  const dryRunEvidencePath =
    studioState?.dry_run_evidence_virtual_path ??
    pickArtifact(studioArtifacts, "/dry-run-evidence.json");
  const lifecyclePath = pickArtifact(studioArtifacts, "/skill-lifecycle.json");
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
  const { content: dryRunEvidenceContent } = useArtifactContent({
    filepath: dryRunEvidencePath ?? "",
    threadId,
    enabled: Boolean(dryRunEvidencePath),
  });
  const { content: lifecycleContent, isLoading: isLifecycleArtifactLoading } =
    useArtifactContent({
      filepath: lifecyclePath ?? "",
      threadId,
      enabled: Boolean(lifecyclePath),
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
  const dryRunEvidence = useMemo(
    () => safeJsonParse<DryRunEvidencePayload>(dryRunEvidenceContent),
    [dryRunEvidenceContent],
  );
  const lifecycleRecord = useMemo(
    () => safeJsonParse<SkillLifecycleRecord>(lifecycleContent),
    [lifecycleContent],
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
  const {
    lifecycleSummaries,
    isLoading: areLifecycleSummariesLoading,
  } = useSkillLifecycleSummaries({ enabled: !isMock });
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
    enabled:
      shouldLoadSkillLifecycleDetail({
        skillName,
        lifecycleSummary,
        areLifecycleSummariesLoading,
        isThreadLoading: thread.isLoading,
        hasLifecycleArtifactPath: Boolean(lifecyclePath),
        isLifecycleArtifactLoading,
        lifecycleRecord,
      }) && !isMock,
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
        dryRunEvidence,
        publishReadiness,
        lifecycleSummary,
        lifecycleDetail,
        skillGraph,
        studioArtifacts,
      }),
    [
      draft,
      dryRunEvidence,
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
  const recordDryRunEvidenceMutation = useRecordDryRunEvidence();
  const rollbackSkillRevision = useRollbackSkillRevision();
  const busy =
    updateLifecycle.isPending ||
    recordDryRunEvidenceMutation.isPending ||
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
  const canSaveLifecycle = Boolean(
    skillName &&
      (lifecyclePath || draftPath || lifecycleSummary || lifecycleDetail),
  );

  const saveLifecycle = useCallback(async () => {
    if (!skillName || !canSaveLifecycle) return;
    try {
      await updateLifecycle.mutateAsync({
        skillName,
        enabled: publishEnabled,
        version_note: versionNote,
        binding_targets: bindingTargets,
        thread_id: threadId,
        path: lifecyclePath ?? draftPath ?? undefined,
      });
      toast.success("技能生命周期设置已保存。");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "保存技能生命周期设置失败。");
    }
  }, [
    bindingTargets,
    canSaveLifecycle,
    draftPath,
    lifecyclePath,
    publishEnabled,
    skillName,
    threadId,
    updateLifecycle,
    versionNote,
  ]);

  const recordDryRun = useCallback(
    async (status: "passed" | "failed") => {
      if (!draftPath) return;
      try {
        await recordDryRunEvidenceMutation.mutateAsync({
          thread_id: threadId,
          path: draftPath,
          status,
          scenario_id: detail.evaluate.scenarioMatrix.scenarios[0]?.id,
          message_ids: dryRunEvidenceMessageIds,
          reviewer_note: versionNote,
          publishReadinessPath,
          dryRunEvidencePath,
          isMock: Boolean(isMock),
        });
        toast.success(status === "passed" ? "已记录试跑通过。" : "已记录试跑失败。");
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "记录试跑证据失败。");
      }
    },
    [
      detail.evaluate.scenarioMatrix.scenarios,
      draftPath,
      dryRunEvidencePath,
      dryRunEvidenceMessageIds,
      isMock,
      publishReadinessPath,
      recordDryRunEvidenceMutation,
      threadId,
      versionNote,
    ],
  );

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
    thread.values.messages,
  );
  const showAssistantSelector = agentSelectorEnabled && !agentSelectionLocked;
  const recoveryHref = useMemo(() => {
    const params = new URLSearchParams();
    if (activeAgentName) {
      params.set("agent", activeAgentName);
    }
    if (isMock) {
      params.set("mock", "true");
    }

    return `/workspace/skill-studio/new${
      params.size > 0 ? `?${params.toString()}` : ""
    }`;
  }, [activeAgentName, isMock]);

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
      {threadErrorMessage ? (
        <WorkspaceStatePanel
          state="data-interrupted"
          title={
            hasMissingRuntimeThread
              ? "原技能线程已失效"
              : "技能线程暂时中断"
          }
          description={
            hasMissingRuntimeThread
              ? `${threadErrorMessage}。当前页面上的技能产物仍可查看，但要继续协商或补做验证，需要新建技能线程。`
              : threadErrorMessage
          }
          actions={[
            {
              label: "重试当前线程",
              onClick: () => window.location.reload(),
            },
            {
              label: hasMissingRuntimeThread ? "新建技能线程" : "返回技能总览",
              href: recoveryHref,
              variant: "default",
            },
          ]}
        />
      ) : null}
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        <SkillStudioLifecycleCanvas
          session={session}
          detail={detail}
          isMock={Boolean(isMock)}
          enabled={publishEnabled}
          versionNote={versionNote}
          explicitBindingRoleIds={explicitBindingRoleIds}
          busy={busy}
          canSaveLifecycle={canSaveLifecycle}
          canPublish={
            Boolean(packageArchivePath) &&
            detail.evaluate.dryRun.status === "passed" &&
            detail.publish.blockedGateCount === 0
          }
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
          onRecordDryRunPassed={() => void recordDryRun("passed")}
          onRecordDryRunFailed={() => void recordDryRun("failed")}
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
              disabled={
                env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ||
                isUploading ||
                hasMissingRuntimeThread
              }
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
