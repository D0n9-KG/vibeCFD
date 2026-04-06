"use client";

import {
  GitBranchPlusIcon,
  MessageSquareIcon,
  ShieldAlertIcon,
  SparklesIcon,
  UploadCloudIcon,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  InterruptActionBar,
  NegotiationRail,
  SecondaryLayerHost,
  SessionSummaryBar,
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
import type {
  SkillGraphResponse,
  SkillLifecycleRecord,
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

import { SkillStudioDefineStage } from "./skill-studio-define-stage";
import {
  buildSkillStudioDetailModel,
  type PublishReadinessPayload,
  type SkillDraftPayload,
  type SkillPackagePayload,
  type SkillStudioThreadState,
  type TestMatrixPayload,
  type ValidationPayload,
} from "./skill-studio-detail-model";
import { SkillStudioEvaluateStage } from "./skill-studio-evaluate-stage";
import { SkillStudioGraphStage } from "./skill-studio-graph-stage";
import { SkillStudioPublishStage } from "./skill-studio-publish-stage";
import {
  buildSkillStudioSessionModel,
  type SkillStudioPrimaryStage,
} from "./skill-studio-session-model";

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

const STAGE_META: Record<
  SkillStudioPrimaryStage,
  { label: string; note: string; icon: typeof SparklesIcon }
> = {
  define: {
    label: "Define",
    note: "Goal, triggers, constraints, acceptance, and package intent.",
    icon: SparklesIcon,
  },
  evaluate: {
    label: "Evaluate",
    note: "Validation blockers, warnings, scenarios, and dry-run evidence.",
    icon: ShieldAlertIcon,
  },
  publish: {
    label: "Publish",
    note: "Readiness, bindings, revisions, rollback, and enable state.",
    icon: UploadCloudIcon,
  },
  graph: {
    label: "Graph",
    note: "Upstream, downstream, similar, and high-impact relationships.",
    icon: GitBranchPlusIcon,
  },
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
  const lifecycleSummary = useMemo(
    () => findSkillLifecycleSummary(lifecycleSummaries, skillName),
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
  const [activeStage, setActiveStage] = useState<SkillStudioPrimaryStage>(
    session.primaryStage,
  );
  const [publishEnabled, setPublishEnabled] = useState(detail.publish.enabled);
  const [versionNote, setVersionNote] = useState(detail.publish.versionNote);
  const [explicitBindingRoleIds, setExplicitBindingRoleIds] = useState<string[]>(
    detail.publish.explicitBindingRoleIds,
  );

  useEffect(() => {
    setActiveStage(session.primaryStage);
  }, [session.primaryStage]);

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
      toast.success("Lifecycle settings updated.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update lifecycle.");
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
      toast.success("Skill published.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to publish skill.");
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
      toast.success("Rollback applied.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to roll back.");
    }
  }, [detail.publish.rollbackTargetId, rollbackSkillRevision, skillName]);

  const secondaryLayers = [
    {
      id: "define",
      label: "Package Brief",
      content:
        detail.define.acceptanceCriteria[0] ??
        detail.define.constraints[0] ??
        "Define the brief and acceptance boundary first.",
    },
    {
      id: "evaluate",
      label: "Evaluation Blockers",
      content:
        detail.evaluate.validationErrors[0] ??
        detail.evaluate.dryRun.nextActions[0] ??
        "Validation and dry-run blockers will surface here.",
    },
    {
      id: "publish",
      label: "Publish State",
      content:
        detail.publish.nextActions[0] ??
        detail.publish.rollbackTargetId ??
        "Publish readiness and rollback state stay visible here.",
    },
    {
      id: "graph",
      label: "Graph Context",
      content:
        detail.graph.relatedSkills[0]?.reasons[0] ??
        "Relationship context appears here once graph links are available.",
    },
  ];
  const secondaryLayerId =
    activeStage === "evaluate"
      ? "evaluate"
      : activeStage === "publish"
        ? "publish"
        : activeStage === "graph"
          ? "graph"
          : "define";
  const threadTitle =
    typeof thread.values.title === "string" && thread.values.title.length > 0
      ? thread.values.title
      : detail.define.skillTitle;

  return (
    <WorkbenchShell
      mobileNegotiationRailVisible={mobileNegotiationRailVisible}
      nav={
        <div className="flex h-full min-h-0 flex-col">
          <div className="flex items-center gap-2 text-orange-700">
            <SparklesIcon className="size-4" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.2em]">
              Skill Studio
            </span>
          </div>
          <div className="mt-4 space-y-2">
            {(Object.keys(STAGE_META) as SkillStudioPrimaryStage[]).map((stage) => {
              const meta = STAGE_META[stage];
              const Icon = meta.icon;
              return (
                <button
                  key={stage}
                  type="button"
                  className={cn(
                    "w-full rounded-2xl border px-3 py-3 text-left transition-colors",
                    activeStage === stage
                      ? "border-orange-200 bg-orange-50"
                      : "border-slate-200 bg-white",
                  )}
                  onClick={() => setActiveStage(stage)}
                >
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
                    <Icon className="size-4" />
                    {meta.label}
                  </div>
                  <div className="mt-2 text-xs leading-5 text-slate-600">
                    {meta.note}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      }
      main={
        <div className="flex h-full min-h-0 flex-col gap-3">
          <ThreadHeader
            title={threadTitle}
            subtitle={`${activeAssistantLabel} · agentic skill lifecycle`}
            statusLabel={session.summary.publishStatus}
            actions={
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={onToggleChatRail}>
                  <MessageSquareIcon className="size-4" />
                  {mobileNegotiationRailVisible ? "Hide rail" : "Show rail"}
                </Button>
              </div>
            }
          />
          <SessionSummaryBar
            pendingApprovals={session.negotiation.pendingApprovalCount}
            interruptionVisible={session.negotiation.interruptionVisible}
            summary={
              session.negotiation.question ??
              "The right rail stays available for negotiation and live edits."
            }
          />
          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            {activeStage === "define" ? (
              <SkillStudioDefineStage detail={detail} onOpenChat={onToggleChatRail} />
            ) : null}
            {activeStage === "evaluate" ? (
              <SkillStudioEvaluateStage detail={detail} />
            ) : null}
            {activeStage === "publish" ? (
              <SkillStudioPublishStage
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
              />
            ) : null}
            {activeStage === "graph" ? <SkillStudioGraphStage detail={detail} /> : null}
          </div>
        </div>
      }
      negotiation={
        <NegotiationRail
          title={<div className="text-base font-semibold text-slate-950">Assistant Rail</div>}
          question={
            <p className="rounded-xl border border-amber-200/80 bg-amber-50/70 px-3 py-2 text-sm text-amber-900">
              {session.negotiation.question ?? "No blocking negotiation right now."}
            </p>
          }
          actions={
            <Select
              value={activeAgentName}
              onValueChange={onAgentChange}
              disabled={agentSelectionLocked || !agentSelectorEnabled}
            >
              <SelectTrigger className="w-full bg-white/90">
                <SelectValue placeholder="Choose skill creator" />
              </SelectTrigger>
              <SelectContent>
                {agentOptions.map((option) => (
                  <SelectItem key={option.name} value={option.name}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          }
          body={
            <div className="flex h-full min-h-0 flex-col gap-3">
              <InterruptActionBar
                interruptionVisible={session.negotiation.interruptionVisible}
                onPause={() => setActiveStage("define")}
                onResolve={onToggleChatRail}
              />
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">{activeAssistantLabel}</CardTitle>
                  <CardDescription>{assistantDescription}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2 pt-0">
                  <Badge variant="outline">{session.summary.validationStatus}</Badge>
                  <Badge variant="outline">{session.summary.testStatus}</Badge>
                  <Badge variant="outline">{session.summary.publishStatus}</Badge>
                </CardContent>
              </Card>
              <div className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-slate-200/80 bg-white/84">
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
                Open Artifacts
              </Button>
            </div>
          }
        />
      }
      secondary={
        <SecondaryLayerHost layers={secondaryLayers} activeLayerId={secondaryLayerId} />
      }
    />
  );
}
