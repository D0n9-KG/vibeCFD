"use client";

import {
  ArrowUpRightIcon,
  BadgeCheckIcon,
  ShieldCheckIcon,
  SparklesIcon,
  TestTubeDiagonalIcon,
  WandSparklesIcon,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { urlOfArtifact } from "@/core/artifacts/utils";
import { localizeWorkspaceDisplayText } from "@/core/i18n/workspace-display";
import {
  usePublishSkill,
  useRollbackSkillRevision,
  useSkillGraph,
  useSkillLifecycle,
  useSkillLifecycleSummaries,
  useUpdateSkillLifecycle,
} from "@/core/skills/hooks";
import { cn } from "@/lib/utils";

import { useArtifacts } from "./artifacts";
import { useThread } from "./messages/context";
import {
  buildFocusedSkillGraphItems,
  buildSkillGraphOverview,
  buildSkillGraphWorkbenchModel,
  type SkillGraphWorkbenchFilter,
} from "./skill-graph.utils";
import {
  buildSkillStudioBindingTargets,
  buildSkillStudioPublishPanelModel,
  buildSkillStudioReadinessSummary,
  findSkillLifecycleSummary,
  formatSkillStudioStatus,
  groupSkillStudioArtifacts,
  resolveSkillStudioAssistantIdentity,
  SKILL_STUDIO_BINDING_ROLE_IDS,
  type SkillStudioLifecycleRevision,
} from "./skill-studio-workbench.utils";

export type SkillStudioWorkbenchView =
  | "overview"
  | "build"
  | "validation"
  | "test"
  | "publish"
  | "graph";

export type SkillStudioGraphFilter = SkillGraphWorkbenchFilter;

type SkillStudioState = {
  skill_name?: string | null;
  assistant_mode?: string | null;
  assistant_label?: string | null;
  builtin_skills?: string[] | null;
  validation_status?: string | null;
  test_status?: string | null;
  publish_status?: string | null;
  error_count?: number | null;
  warning_count?: number | null;
  package_archive_virtual_path?: string | null;
  ui_metadata_virtual_path?: string | null;
  active_revision_id?: string | null;
  published_revision_id?: string | null;
  version_note?: string | null;
  bindings?:
    | Array<{
        role_id?: string | null;
        mode?: string | null;
        target_skills?: string[] | null;
      }>
    | null;
  artifact_virtual_paths?: string[] | null;
};

type SkillDraftPayload = {
  skill_name?: string;
  skill_title?: string;
  skill_purpose?: string;
  description?: string;
  assistant_mode?: string;
  assistant_label?: string;
  builtin_skills?: string[] | null;
  trigger_conditions?: string[] | null;
  workflow_steps?: string[] | null;
  expert_rules?: string[] | null;
  acceptance_criteria?: string[] | null;
  test_scenarios?: string[] | null;
};

type ValidationPayload = {
  status?: string;
  error_count?: number;
  warning_count?: number;
  passed_checks?: string[] | null;
  errors?: string[] | null;
  warnings?: string[] | null;
};

type TestMatrixPayload = {
  status?: string;
  scenario_test_count?: number;
  blocking_count?: number;
  scenario_tests?: Array<{
    id?: string;
    scenario?: string;
    status?: string;
    expected_outcome?: string;
    blocking_reasons?: string[] | null;
  }> | null;
};

type PublishReadinessPayload = {
  status?: string;
  blocking_count?: number;
  gates?: Array<{ id?: string; label?: string; status?: string }> | null;
  next_actions?: string[] | null;
};

type SkillPackagePayload = {
  assistant_mode?: string;
  assistant_label?: string;
  builtin_skills?: string[] | null;
  package_archive_virtual_path?: string;
  archive_virtual_path?: string;
  ui_metadata_virtual_path?: string;
};

type SkillStudioWorkbenchPanelProps = {
  threadId: string;
  view: SkillStudioWorkbenchView;
  graphFilter?: SkillStudioGraphFilter;
  className?: string;
};

type PublishFeedback = {
  variant: "default" | "destructive";
  title: string;
  message: string;
};

type WorkbenchData = {
  threadId: string;
  assistantLabel: string;
  assistantMode: string;
  builtinSkills: string[];
  skillName: string;
  skillTitle: string;
  archiveVirtualPath: string | null;
  draft: SkillDraftPayload | null;
  validation: ValidationPayload | null;
  testMatrix: TestMatrixPayload | null;
  publishReadiness: PublishReadinessPayload | null;
  readiness: ReturnType<typeof buildSkillStudioReadinessSummary>;
  groupedArtifacts: ReturnType<typeof groupSkillStudioArtifacts>;
  studioArtifacts: string[];
  graphOverview: ReturnType<typeof buildSkillGraphOverview>;
  focusedSkillGraphItems: ReturnType<typeof buildFocusedSkillGraphItems>;
  graphModel: ReturnType<typeof buildSkillGraphWorkbenchModel>;
  nextActionLines: string[];
};

function safeJsonParse<T>(content?: string | null): T | null {
  if (!content) return null;
  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

function pickArtifact(artifacts: string[], predicate: (artifact: string) => boolean) {
  return artifacts.find(predicate) ?? null;
}

function getArtifactLabel(path: string) {
  if (path.endsWith("/skill-draft.json")) return "技能草稿 JSON";
  if (path.endsWith("/skill-package.json")) return "技能包";
  if (path.endsWith("/SKILL.md")) return "SKILL.md";
  if (path.endsWith("/agents/openai.yaml")) return "界面元数据";
  if (path.endsWith("/references/domain-rules.md")) return "领域规则";
  if (path.endsWith("/test-matrix.json")) return "测试矩阵";
  if (path.endsWith("/validation-report.json")) return "校验报告 JSON";
  if (path.endsWith("/publish-readiness.json")) return "发布就绪报告";
  if (path.endsWith(".skill")) return "可安装 .skill 包";
  return path.split("/").at(-1) ?? path;
}

function getStatusTone(status?: string | null) {
  switch (status) {
    case "ready_for_review":
    case "ready_for_dry_run":
      return "default" as const;
    case "blocked":
    case "needs_revision":
      return "destructive" as const;
    default:
      return "outline" as const;
  }
}

const LOCALIZED_SKILL_STUDIO_LINES: Record<string, string> = {
  "Run a dry-run conversation using one of the prepared scenarios.":
    "使用已准备好的一个场景先跑一轮试运行对话。",
  "Review the generated SKILL.md, domain rules, and UI metadata together.":
    "把生成的 SKILL.md、领域规则和界面元数据一起审阅一遍。",
  "Publish only after the expert signs off on the dry-run result.":
    "只有在专家确认试运行结果后，再执行正式发布。",
};

function localizeSkillStudioLine(line: string) {
  return localizeWorkspaceDisplayText(LOCALIZED_SKILL_STUDIO_LINES[line] ?? line);
}

function deriveNextActionLines(args: {
  publishNextActions: string[];
  validationErrors: string[];
  validationWarnings: string[];
  blockingCount: number;
}) {
  if (args.publishNextActions.length > 0) {
    return args.publishNextActions.map(localizeSkillStudioLine);
  }
  if (args.validationErrors.length > 0) {
    return args.validationErrors.slice(0, 3).map(localizeSkillStudioLine);
  }
  if (args.validationWarnings.length > 0) {
    return args.validationWarnings.slice(0, 3).map(localizeSkillStudioLine);
  }
  if (args.blockingCount > 0) {
    return ["发布前先处理阻塞中的校验、测试或发布门槛。"];
  }
  return ["当前技能包已经可以进入试运行或最终发布审阅。"];
}

const LOCALIZED_PUBLISH_GATE_LABELS: Record<string, string> = {
  "Skill structure is valid": "技能结构有效",
  "Trigger description is discoverable": "触发描述可发现",
  "Scenario tests are prepared": "场景测试已准备",
  "Dry-run handoff is ready": "试运行交接已就绪",
  "UI metadata has been generated": "界面元数据已生成",
};

const GRAPH_FILTER_LABELS: Record<SkillGraphWorkbenchFilter, string> = {
  all: "全部",
  upstream: "上游",
  downstream: "下游",
  similar: "相似",
  "high-impact": "高影响",
};

function localizePublishGateLabel(label?: string | null) {
  if (!label) {
    return "未命名门槛";
  }
  return LOCALIZED_PUBLISH_GATE_LABELS[label] ?? label;
}

function formatGraphFilterLabel(filter: SkillGraphWorkbenchFilter) {
  return GRAPH_FILTER_LABELS[filter];
}

export function SkillStudioWorkbenchPanel({
  threadId,
  view,
  graphFilter = "all",
  className,
}: SkillStudioWorkbenchPanelProps) {
  const { thread, isMock } = useThread();
  const { select, setOpen } = useArtifacts();
  const publishSkill = usePublishSkill();
  const rollbackSkillRevision = useRollbackSkillRevision();
  const updateSkillLifecycle = useUpdateSkillLifecycle();
  const [publishFeedback, setPublishFeedback] = useState<PublishFeedback | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [enableOnPublish, setEnableOnPublish] = useState(true);
  const [versionNote, setVersionNote] = useState("");
  const [explicitBindingRoleIds, setExplicitBindingRoleIds] = useState<string[]>([]);

  const studioState = useMemo(() => {
    const raw = thread.values.submarine_skill_studio;
    return raw && typeof raw === "object" ? (raw as SkillStudioState) : null;
  }, [thread.values.submarine_skill_studio]);

  const currentSkillName =
    typeof studioState?.skill_name === "string" ? studioState.skill_name : undefined;
  const { lifecycleSummaries } = useSkillLifecycleSummaries({
    enabled: Boolean(currentSkillName) && !Boolean(isMock),
  });
  const { data: lifecycleDetail } = useSkillLifecycle({
    skillName: currentSkillName,
    enabled: Boolean(currentSkillName) && !Boolean(isMock),
  });
  const { data: skillGraph } = useSkillGraph({
    skillName: currentSkillName,
    isMock: Boolean(isMock),
    enabled: true,
  });

  const studioArtifacts = useMemo(() => {
    const threadArtifacts = Array.isArray(thread.values.artifacts) ? thread.values.artifacts : [];
    const stateArtifacts = Array.isArray(studioState?.artifact_virtual_paths)
      ? studioState.artifact_virtual_paths
      : [];
    return [...threadArtifacts, ...stateArtifacts].filter(
      (artifact, index, list) =>
        typeof artifact === "string" &&
        artifact.includes("/submarine/skill-studio/") &&
        list.indexOf(artifact) === index,
    );
  }, [studioState?.artifact_virtual_paths, thread.values.artifacts]);

  const draftJson = pickArtifact(studioArtifacts, (artifact) =>
    artifact.endsWith("/skill-draft.json"),
  );
  const packageJson = pickArtifact(studioArtifacts, (artifact) =>
    artifact.endsWith("/skill-package.json"),
  );
  const validationJson = pickArtifact(studioArtifacts, (artifact) =>
    artifact.endsWith("/validation-report.json"),
  );
  const testMatrixJson = pickArtifact(studioArtifacts, (artifact) =>
    artifact.endsWith("/test-matrix.json"),
  );
  const publishJson = pickArtifact(studioArtifacts, (artifact) =>
    artifact.endsWith("/publish-readiness.json"),
  );

  const { content: draftContent } = useArtifactContent({
    filepath: draftJson ?? "",
    threadId,
    enabled: Boolean(draftJson),
  });
  const { content: packageContent } = useArtifactContent({
    filepath: packageJson ?? "",
    threadId,
    enabled: Boolean(packageJson),
  });
  const { content: validationContent } = useArtifactContent({
    filepath: validationJson ?? "",
    threadId,
    enabled: Boolean(validationJson),
  });
  const { content: testMatrixContent } = useArtifactContent({
    filepath: testMatrixJson ?? "",
    threadId,
    enabled: Boolean(testMatrixJson),
  });
  const { content: publishContent } = useArtifactContent({
    filepath: publishJson ?? "",
    threadId,
    enabled: Boolean(publishJson),
  });

  const draft = useMemo(() => safeJsonParse<SkillDraftPayload>(draftContent), [draftContent]);
  const skillPackage = useMemo(
    () => safeJsonParse<SkillPackagePayload>(packageContent),
    [packageContent],
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
    () => safeJsonParse<PublishReadinessPayload>(publishContent),
    [publishContent],
  );
  const lifecycleSummary = useMemo(
    () => findSkillLifecycleSummary(lifecycleSummaries, currentSkillName),
    [currentSkillName, lifecycleSummaries],
  );

  if (!studioState && studioArtifacts.length === 0) {
    return null;
  }

  const { assistantMode, assistantLabel } = resolveSkillStudioAssistantIdentity({
    draftAssistantMode: draft?.assistant_mode,
    draftAssistantLabel: draft?.assistant_label,
    packageAssistantMode: skillPackage?.assistant_mode,
    packageAssistantLabel: skillPackage?.assistant_label,
    stateAssistantMode: studioState?.assistant_mode,
    stateAssistantLabel: studioState?.assistant_label,
  });
  const builtinSkills =
    draft?.builtin_skills ?? skillPackage?.builtin_skills ?? studioState?.builtin_skills ?? [];
  const skillName = draft?.skill_name ?? studioState?.skill_name ?? "pending-skill";
  const skillTitle = draft?.skill_title ?? skillName;
  const displayBuiltinSkills = builtinSkills.map((skill) =>
    localizeWorkspaceDisplayText(skill),
  );
  const displaySkillName = localizeWorkspaceDisplayText(skillName);
  const displaySkillTitle = localizeWorkspaceDisplayText(skillTitle);
  const archiveVirtualPath =
    skillPackage?.package_archive_virtual_path ??
    skillPackage?.archive_virtual_path ??
    studioState?.package_archive_virtual_path ??
    null;
  const publishPanelModel = useMemo(
    () =>
      buildSkillStudioPublishPanelModel({
        skillName,
        lifecycleSummary: lifecycleDetail ?? lifecycleSummary,
        stateVersionNote: studioState?.version_note,
        stateBindings: studioState?.bindings,
        stateActiveRevisionId: studioState?.active_revision_id,
        statePublishedRevisionId: studioState?.published_revision_id,
      }),
    [
      lifecycleDetail,
      lifecycleSummary,
      skillName,
      studioState?.active_revision_id,
      studioState?.bindings,
      studioState?.published_revision_id,
      studioState?.version_note,
    ],
  );
  const readiness = buildSkillStudioReadinessSummary({
    errorCount: validation?.error_count ?? studioState?.error_count ?? 0,
    warningCount: validation?.warning_count ?? studioState?.warning_count ?? 0,
    validationStatus: validation?.status ?? studioState?.validation_status ?? "draft_only",
    testStatus: testMatrix?.status ?? studioState?.test_status ?? "draft_only",
    publishStatus: publishReadiness?.status ?? studioState?.publish_status ?? "draft_only",
  });
  const groupedArtifacts = groupSkillStudioArtifacts(studioArtifacts);
  const graphOverview = buildSkillGraphOverview(skillGraph);
  const focusedSkillGraphItems = buildFocusedSkillGraphItems(skillGraph);
  const graphModel = buildSkillGraphWorkbenchModel(skillGraph, graphFilter);
  const nextActionLines = deriveNextActionLines({
    publishNextActions: publishReadiness?.next_actions ?? [],
    validationErrors: validation?.errors ?? [],
    validationWarnings: validation?.warnings ?? [],
    blockingCount: readiness.blockingCount,
  });
  const bindingTargets = useMemo(
    () => buildSkillStudioBindingTargets(skillName, explicitBindingRoleIds),
    [explicitBindingRoleIds, skillName],
  );
  const publishedRevisions = useMemo(
    () => [...(lifecycleDetail?.published_revisions ?? [])].reverse(),
    [lifecycleDetail?.published_revisions],
  );
  const publishDisabled = [
    isMock,
    !archiveVirtualPath,
    publishSkill.isPending,
    readiness.blockingCount > 0,
  ].some(Boolean);
  const overwriteDisabled = [isMock, !archiveVirtualPath, publishSkill.isPending].some(
    Boolean,
  );
  const saveLifecycleDisabled = [
    isMock,
    updateSkillLifecycle.isPending,
    !publishPanelModel.publishedPath,
  ].some(Boolean);
  const rollbackDisabled = [isMock, rollbackSkillRevision.isPending].some(Boolean);

  useEffect(() => {
    setEnableOnPublish(publishPanelModel.enabled);
    setVersionNote(publishPanelModel.versionNote);
    setExplicitBindingRoleIds(publishPanelModel.explicitBindingRoleIds);
  }, [
    publishPanelModel.enabled,
    publishPanelModel.explicitBindingRoleIds,
    publishPanelModel.versionNote,
  ]);

  useEffect(() => {
    if (graphModel.nodes.length === 0) {
      setSelectedNodeId(null);
      return;
    }
    setSelectedNodeId((current) => {
      if (current && graphModel.nodes.some((node) => node.id === current)) {
        return current;
      }
      return graphModel.focusSkillName ?? graphModel.nodes[0]?.id ?? null;
    });
  }, [graphModel]);

  const selectedNode =
    graphModel.nodes.find((node) => node.id === selectedNodeId) ??
    graphModel.nodes[0] ??
    null;

  async function handleSaveLifecycle() {
    if (!currentSkillName) {
      return;
    }

    try {
      await updateSkillLifecycle.mutateAsync({
        skillName: currentSkillName,
        enabled: enableOnPublish,
        version_note: versionNote,
        binding_targets: bindingTargets,
      });
      setPublishFeedback({
        variant: "default",
        title: "治理配置已保存",
        message:
          bindingTargets.length > 0
            ? `已为 ${bindingTargets.length} 个角色保存显式绑定，并同步当前启用状态。`
            : "已保存当前启用状态，后续线程将继续使用全局启用池自动发现。",
      });
      toast.success("技能治理配置已保存");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "保存技能治理配置失败。";
      setPublishFeedback({
        variant: "destructive",
        title: "保存失败",
        message,
      });
      toast.error(message);
    }
  }

  async function handleRollback(revisionId: string) {
    if (!currentSkillName) {
      return;
    }

    try {
      const result = await rollbackSkillRevision.mutateAsync({
        skillName: currentSkillName,
        revision_id: revisionId,
      });
      setPublishFeedback({
        variant: "default",
        title: "回滚完成",
        message: `已恢复到 ${revisionId}。当前 revision：${result.active_revision_id ?? revisionId}。`,
      });
      toast.success(`已恢复到 ${revisionId}`);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "回滚技能 revision 失败。";
      setPublishFeedback({
        variant: "destructive",
        title: "回滚失败",
        message,
      });
      toast.error(message);
    }
  }

  async function handlePublish(overwrite: boolean) {
    if (!archiveVirtualPath) {
      setPublishFeedback({
        variant: "destructive",
        title: "还没有可安装的技能包",
        message: "请先生成并校验技能包，再发布到项目中。",
      });
      return;
    }

    try {
      const result = await publishSkill.mutateAsync({
        thread_id: threadId,
        path: archiveVirtualPath,
        overwrite,
        enable: enableOnPublish,
        version_note: versionNote,
        binding_targets: bindingTargets,
      });
      setPublishFeedback({
        variant: "default",
        title: overwrite ? "技能已更新" : "技能已发布",
        message: `${result.message}。启用状态：${result.enabled ? "已启用" : "未启用"}。`,
      });
      toast.success(overwrite ? "项目中的技能已更新" : "技能已发布到项目");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "发布技能包失败。";
      setPublishFeedback({
        variant: "destructive",
        title: "发布失败",
        message,
      });
      toast.error(message);
    }
  }

  const data: WorkbenchData = {
    threadId,
    assistantLabel,
    assistantMode,
    builtinSkills: displayBuiltinSkills,
    skillName: displaySkillName,
    skillTitle: displaySkillTitle,
    archiveVirtualPath,
    draft,
    validation,
    testMatrix,
    publishReadiness,
    readiness,
    groupedArtifacts,
    studioArtifacts,
    graphOverview,
    focusedSkillGraphItems,
    graphModel,
    nextActionLines,
  };

  return (
    <div className={cn("min-h-0", className)}>
      <Card className="min-h-0 rounded-[28px] border-stone-200/80 shadow-[0_24px_64px_rgba(15,23,42,0.08)]">
        <CardHeader className="border-b bg-muted/20 pb-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                <WandSparklesIcon className="size-4" />
                专属技能工作台
              </div>
              <div className="space-y-2">
                <CardTitle className="text-2xl">{displaySkillTitle}</CardTitle>
                <CardDescription className="max-w-3xl text-sm leading-6">
                  {assistantLabel} 会把技能包审阅、校验、测试、发布就绪和图谱审阅分成独立的生命周期界面来处理。
                </CardDescription>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{assistantLabel}</Badge>
              <Badge variant={getStatusTone(validation?.status ?? studioState?.validation_status)}>
                {formatSkillStudioStatus(validation?.status ?? studioState?.validation_status)}
              </Badge>
              <Badge variant={getStatusTone(testMatrix?.status ?? studioState?.test_status)}>
                {formatSkillStudioStatus(testMatrix?.status ?? studioState?.test_status)}
              </Badge>
              <Badge variant={getStatusTone(publishReadiness?.status ?? studioState?.publish_status)}>
                {formatSkillStudioStatus(publishReadiness?.status ?? studioState?.publish_status)}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6 p-5">
          {view === "overview" ? <OverviewSection data={data} /> : null}
          {view === "build" ? (
            <BuildSection
              data={data}
              uiMetadataPath={
                skillPackage?.ui_metadata_virtual_path ??
                studioState?.ui_metadata_virtual_path ??
                 "等待生成 openai.yaml"
              }
              isMock={Boolean(isMock)}
              onOpenArtifact={(artifactPath) => {
                select(artifactPath);
                setOpen(true);
              }}
            />
          ) : null}
          {view === "validation" ? <ValidationSection validation={validation} /> : null}
          {view === "test" ? <TestSection draft={draft} testMatrix={testMatrix} /> : null}
          {view === "publish" ? (
            <PublishSection
              currentSkillName={currentSkillName ?? skillName}
              enableOnPublish={enableOnPublish}
              versionNote={versionNote}
              bindingTargets={bindingTargets}
              explicitBindingRoleIds={explicitBindingRoleIds}
              revisionCount={publishPanelModel.revisionCount}
              bindingCount={publishPanelModel.bindingCount}
              activeRevisionId={publishPanelModel.activeRevisionId}
              publishedRevisionId={publishPanelModel.publishedRevisionId}
              rollbackTargetId={publishPanelModel.rollbackTargetId}
              publishedPath={publishPanelModel.publishedPath}
              lastPublishedAt={publishPanelModel.lastPublishedAt}
              draftStatus={publishPanelModel.draftStatus}
              publishedRevisions={publishedRevisions}
              feedback={publishFeedback}
              publishDisabled={publishDisabled}
              overwriteDisabled={overwriteDisabled}
              publishPending={publishSkill.isPending}
              rollbackPending={rollbackSkillRevision.isPending}
              savePending={updateSkillLifecycle.isPending}
              saveDisabled={saveLifecycleDisabled}
              rollbackDisabled={rollbackDisabled}
              readiness={readiness}
              archiveVirtualPath={archiveVirtualPath}
              publishReadiness={publishReadiness}
              nextActionLines={nextActionLines}
              onToggleEnabled={setEnableOnPublish}
              onVersionNoteChange={setVersionNote}
              onToggleBindingRole={(roleId) => {
                setExplicitBindingRoleIds((current) => {
                  if (current.includes(roleId)) {
                    return current.filter((item) => item !== roleId);
                  }
                  return SKILL_STUDIO_BINDING_ROLE_IDS.filter(
                    (item) => item === roleId || current.includes(item),
                  );
                });
              }}
              onSaveLifecycle={handleSaveLifecycle}
              onPublish={handlePublish}
              onRollback={handleRollback}
            />
          ) : null}
          {view === "graph" ? (
            <GraphSection
              data={data}
              graphFilter={graphFilter}
              selectedNodeId={selectedNodeId}
              selectedNode={selectedNode}
              onSelectNode={setSelectedNodeId}
            />
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function OverviewSection({ data }: { data: WorkbenchData }) {
  return (
    <>
      <div className="grid gap-3 xl:grid-cols-4">
        <StudioStat
          icon={SparklesIcon}
          label="当前技能"
          value={localizeWorkspaceDisplayText(data.skillName)}
          note="当前生命周期审阅所对应的技能包标识。"
        />
        <StudioStat
          icon={ShieldCheckIcon}
          label="校验"
          value={data.readiness.validationLabel}
          note={`${data.validation?.error_count ?? 0} 个错误，${data.validation?.warning_count ?? 0} 个警告`}
        />
        <StudioStat
          icon={TestTubeDiagonalIcon}
          label="场景测试"
          value={data.readiness.testLabel}
          note={`已准备 ${data.testMatrix?.scenario_test_count ?? 0} 个场景`}
        />
        <StudioStat
          icon={BadgeCheckIcon}
          label="发布"
          value={data.readiness.publishLabel}
          note={`阻塞门槛 ${data.publishReadiness?.blocking_count ?? data.readiness.blockingCount} 个`}
        />
      </div>

      <Card className="border-dashed bg-muted/10 shadow-none">
        <CardContent className="grid gap-4 p-5 xl:grid-cols-[minmax(0,1fr)_280px] xl:items-center">
          <div className="space-y-3">
            <div>
                <div className="text-sm font-medium text-foreground">就绪度概览</div>
                <div className="text-sm leading-6 text-muted-foreground">
                  在技能正式启用到项目里之前，这个工作台会持续展示结构状态、试运行准备、发布门槛和图谱定位。
                </div>
            </div>
            <Progress value={data.readiness.progress} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <MiniMetric label="进度" value={`${data.readiness.progress}%`} />
            <MiniMetric label="阻塞" value={String(data.readiness.blockingCount)} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.95fr)]">
        <StudioListCard
          title="下一步建议"
          items={data.nextActionLines}
          emptyText="当前还没有下一步动作。"
        />
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">技能包标识</CardTitle>
            <CardDescription>
              当前草稿会绑定到唯一的技能包名称和专属代理身份上。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <KeyValueRow
              label="技能名称"
              value={localizeWorkspaceDisplayText(data.skillName)}
            />
            <KeyValueRow
              label="用途"
              value={localizeWorkspaceDisplayText(
                data.draft?.skill_purpose ?? "等待补充专家用途说明",
              )}
            />
            <KeyValueRow label="代理模式" value={data.assistantLabel} />
            <KeyValueRow label="产物" value={`共 ${data.studioArtifacts.length} 份`} />
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function BuildSection({
  data,
  uiMetadataPath,
  isMock,
  onOpenArtifact,
}: {
  data: WorkbenchData;
  uiMetadataPath: string;
  isMock: boolean;
  onOpenArtifact: (artifactPath: string) => void;
}) {
  return (
    <>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">专属技能创建器代理</CardTitle>
            <CardDescription>
              这个线程会固定一个创建代理身份，确保技能包在多轮修订中保持一致。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <div className="text-sm font-medium">{data.assistantLabel}</div>
              <div className="text-sm text-muted-foreground">
                代理模式：{data.assistantLabel}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {data.builtinSkills.map((skill) => (
                <Badge key={skill} variant="outline">
                  {localizeWorkspaceDisplayText(skill)}
                </Badge>
              ))}
            </div>
            <Separator />
            <BulletList
              items={[
                "领域专家提供规则、阈值和例外条件。",
                `${data.assistantLabel} 会把这些判断整理成可审阅的技能包。`,
                "校验、场景测试和发布门槛都会持续显示在工作台里。",
              ]}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">技能包摘要</CardTitle>
            <CardDescription>
              这里会把技能包合同、界面元数据和审阅产物放在一起查看。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <KeyValueRow
              label="技能名称"
              value={localizeWorkspaceDisplayText(data.skillName)}
            />
            <KeyValueRow
              label="用途"
              value={localizeWorkspaceDisplayText(
                data.draft?.skill_purpose ?? "等待补充专家用途说明",
              )}
            />
            <KeyValueRow
              label="描述"
              value={localizeWorkspaceDisplayText(
                data.draft?.description ?? "等待补充触发描述",
              )}
            />
            <KeyValueRow label="界面元数据" value={uiMetadataPath} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <StudioListCard
          title="触发条件"
          items={data.draft?.trigger_conditions ?? []}
          emptyText="当前还没有整理出触发条件。"
        />
        <StudioListCard
          title="验收标准"
          items={data.draft?.acceptance_criteria ?? []}
          emptyText="当前还没有整理出验收标准。"
        />
      </div>

      <StudioListCard
        title="工作流步骤"
        items={data.draft?.workflow_steps ?? []}
        emptyText="当前还没有整理出工作流步骤。"
      />

      <div className="grid gap-4 xl:grid-cols-2">
        <StudioListCard
          title="专家规则"
          items={data.draft?.expert_rules ?? []}
          emptyText="当前还没有整理出专家规则。"
        />
        <StudioListCard
          title="草稿测试场景"
          items={data.draft?.test_scenarios ?? []}
          emptyText="当前还没有整理出测试场景。"
        />
      </div>

      <ArtifactGroupsSection
        groupedArtifacts={data.groupedArtifacts}
        threadId={data.threadId}
        isMock={isMock}
        onOpenArtifact={onOpenArtifact}
      />
    </>
  );
}

function ValidationSection({ validation }: { validation: ValidationPayload | null }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">校验检查</CardTitle>
          <CardDescription>
            结构校验会保持严格，让专家在发布前就能看清楚真正阻塞审阅的地方。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <MiniMetric label="通过项" value={String(validation?.passed_checks?.length ?? 0)} />
            <MiniMetric label="错误" value={String(validation?.error_count ?? 0)} />
            <MiniMetric label="警告" value={String(validation?.warning_count ?? 0)} />
          </div>
          <StudioListCard
            title="已通过检查"
            items={validation?.passed_checks ?? []}
            emptyText="当前还没有通过项。"
            compact
          />
        </CardContent>
      </Card>

      <div className="grid gap-4">
        <StudioListCard
          title="错误"
          items={validation?.errors ?? []}
          emptyText="当前没有校验错误。"
        />
        <StudioListCard
          title="警告"
          items={validation?.warnings ?? []}
          emptyText="当前没有校验警告。"
        />
      </div>
    </div>
  );
}

function TestSection({
  draft,
  testMatrix,
}: {
  draft: SkillDraftPayload | null;
  testMatrix: TestMatrixPayload | null;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">场景测试矩阵</CardTitle>
          <CardDescription>
            这些场景就是专家试运行和后续自动化技能检查的直接交付面。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {(testMatrix?.scenario_tests ?? []).length > 0 ? (
            (testMatrix?.scenario_tests ?? []).map((scenario) => (
              <div key={scenario.id ?? scenario.scenario} className="rounded-xl border bg-muted/10 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-medium text-foreground">{scenario.scenario}</div>
                  <Badge variant={getStatusTone(scenario.status)}>
                    {formatSkillStudioStatus(scenario.status)}
                  </Badge>
                </div>
                <div className="mt-2 text-sm leading-6 text-muted-foreground">
                  {localizeWorkspaceDisplayText(scenario.expected_outcome ?? "")}
                </div>
                {(scenario.blocking_reasons ?? []).length > 0 ? (
                  <div className="mt-2 text-xs text-muted-foreground">
                    阻塞原因：
                    {localizeWorkspaceDisplayText(
                      (scenario.blocking_reasons ?? []).join(", "),
                    )}
                  </div>
                ) : null}
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
              专家和技能创建器整理出试运行场景后，这里会显示对应测试矩阵。
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">试运行准备度</CardTitle>
            <CardDescription>
              在发布前持续显示阻塞数量和测试准备状态。
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <MiniMetric label="场景数量" value={String(testMatrix?.scenario_test_count ?? 0)} />
            <MiniMetric label="阻塞" value={String(testMatrix?.blocking_count ?? 0)} />
          </CardContent>
        </Card>
        <StudioListCard
          title="草稿测试场景"
          items={draft?.test_scenarios ?? []}
          emptyText="当前还没有整理出草稿测试场景。"
        />
      </div>
    </div>
  );
}

function PublishSection({
  currentSkillName,
  enableOnPublish,
  versionNote,
  bindingTargets,
  explicitBindingRoleIds,
  revisionCount,
  bindingCount,
  activeRevisionId,
  publishedRevisionId,
  rollbackTargetId,
  publishedPath,
  lastPublishedAt,
  draftStatus,
  publishedRevisions,
  feedback,
  publishDisabled,
  overwriteDisabled,
  publishPending,
  rollbackPending,
  savePending,
  saveDisabled,
  rollbackDisabled,
  readiness,
  archiveVirtualPath,
  publishReadiness,
  nextActionLines,
  onToggleEnabled,
  onVersionNoteChange,
  onToggleBindingRole,
  onSaveLifecycle,
  onPublish,
  onRollback,
}: {
  currentSkillName: string;
  enableOnPublish: boolean;
  versionNote: string;
  bindingTargets: Array<{
    role_id: string;
    mode: string;
    target_skills: string[];
  }>;
  explicitBindingRoleIds: string[];
  revisionCount: number;
  bindingCount: number;
  activeRevisionId: string | null;
  publishedRevisionId: string | null;
  rollbackTargetId: string | null;
  publishedPath: string | null;
  lastPublishedAt: string | null;
  draftStatus: string;
  publishedRevisions: SkillStudioLifecycleRevision[];
  feedback: PublishFeedback | null;
  publishDisabled: boolean;
  overwriteDisabled: boolean;
  publishPending: boolean;
  rollbackPending: boolean;
  savePending: boolean;
  saveDisabled: boolean;
  rollbackDisabled: boolean;
  readiness: WorkbenchData["readiness"];
  archiveVirtualPath: string | null;
  publishReadiness: PublishReadinessPayload | null;
  nextActionLines: string[];
  onToggleEnabled: (enabled: boolean) => void;
  onVersionNoteChange: (value: string) => void;
  onToggleBindingRole: (roleId: string) => void;
  onSaveLifecycle: () => Promise<void>;
  onPublish: (overwrite: boolean) => Promise<void>;
  onRollback: (revisionId: string) => Promise<void>;
}) {
  return (
    <>
      {feedback ? (
        <Alert variant={feedback.variant}>
          <ShieldCheckIcon className="size-4" />
          <AlertTitle>{feedback.title}</AlertTitle>
          <AlertDescription>{feedback.message}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">发布门槛</CardTitle>
            <CardDescription>
              这些门槛必须先通过，才能避免草稿技能被误推入正式项目。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(publishReadiness?.gates ?? []).length > 0 ? (
              (publishReadiness?.gates ?? []).map((gate) => (
                <div
                  key={gate.id}
                  className="flex items-center justify-between gap-3 rounded-xl border bg-muted/10 p-3"
                >
                  <div className="text-sm text-foreground">
                    {localizePublishGateLabel(gate.label)}
                  </div>
                  <Badge variant={getStatusTone(gate.status)}>
                    {formatSkillStudioStatus(gate.status)}
                  </Badge>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
                发布就绪包生成后，这里会展示对应的发布门槛。
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">发布与治理</CardTitle>
            <CardDescription>
              在当前工作台内同时管理启用状态、版本说明和显式角色绑定。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <MiniMetric label="草稿状态" value={formatSkillStudioStatus(draftStatus)} />
              <MiniMetric label="已发布 revision" value={String(revisionCount)} />
              <MiniMetric label="当前绑定" value={String(bindingCount)} />
              <MiniMetric label="回滚目标" value={rollbackTargetId ?? "暂无"} />
            </div>
            <div className="rounded-xl border bg-muted/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-foreground">发布后启用</div>
                  <div className="text-xs text-muted-foreground">
                    关闭时仍会发布技能，但后续线程不会默认加载它。
                  </div>
                </div>
                <Switch
                  checked={enableOnPublish}
                  disabled={publishPending || savePending}
                  onCheckedChange={onToggleEnabled}
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium text-foreground">Version note</div>
              <Textarea
                className="min-h-24"
                disabled={publishPending || savePending}
                onChange={(event) => onVersionNoteChange(event.target.value)}
                placeholder="记录这次发布的目的、风险边界或上线说明。"
                value={versionNote}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm font-medium text-foreground">bindingTargets</div>
                <Badge variant="outline">
                  {explicitBindingRoleIds.length > 0
                    ? "显式角色绑定"
                    : "全局启用池自动发现"}
                </Badge>
              </div>
              <div className="space-y-2">
                {SKILL_STUDIO_BINDING_ROLE_IDS.map((roleId) => {
                  const checked = explicitBindingRoleIds.includes(roleId);
                  return (
                    <div
                      key={roleId}
                      className="flex items-center justify-between gap-3 rounded-xl border bg-background/70 p-3"
                    >
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-foreground">
                          {roleId}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {checked
                            ? `显式绑定到 ${currentSkillName}`
                            : "未设置显式绑定，保持全局启用池自动发现。"}
                        </div>
                      </div>
                      <Switch
                        checked={checked}
                        disabled={publishPending || savePending}
                        onCheckedChange={() => onToggleBindingRole(roleId)}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm font-medium text-foreground">Revision history</div>
                <Badge variant="outline">{publishedRevisions.length}</Badge>
              </div>
              {publishedRevisions.length > 0 ? (
                <div className="space-y-2">
                  {publishedRevisions.map((revision) => {
                    const isActive = revision.revision_id === activeRevisionId;
                    const isRollbackTarget =
                      revision.revision_id === rollbackTargetId;
                    return (
                      <div
                        key={revision.revision_id}
                        className="rounded-xl border bg-background/70 p-3"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="text-sm font-medium text-foreground">
                                {revision.revision_id}
                              </div>
                              {isActive ? <Badge>Active</Badge> : null}
                              {isRollbackTarget ? (
                                <Badge variant="outline">Rollback target</Badge>
                              ) : null}
                              <Badge variant="outline">
                                {revision.enabled ? "Enabled" : "Disabled"}
                              </Badge>
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">
                              {revision.published_at}
                            </div>
                            <div className="mt-2 text-sm text-muted-foreground">
                              {revision.version_note || "No version note"}
                            </div>
                            <div className="mt-2 text-xs text-muted-foreground">
                              {revision.binding_targets.length > 0
                                ? `Bindings: ${revision.binding_targets.length}`
                                : "Bindings: auto-discovery"}
                            </div>
                          </div>
                          {!isActive ? (
                            <Button
                              disabled={rollbackDisabled}
                              onClick={() => void onRollback(revision.revision_id)}
                              size="sm"
                              variant="outline"
                            >
                              {rollbackPending && isRollbackTarget
                                ? "Rolling back..."
                                : "Rollback"}
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
                  Publish the skill once to start collecting revision snapshots for rollback.
                </div>
              )}
            </div>
            <Separator />
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={saveDisabled || publishPending}
                onClick={() => void onSaveLifecycle()}
                variant="secondary"
              >
                {savePending ? "保存中..." : "保存治理配置"}
              </Button>
              <Button disabled={publishDisabled} onClick={() => void onPublish(false)}>
                {publishPending
                  ? "发布中..."
                  : enableOnPublish
                    ? "发布并启用"
                    : "发布并保持停用"}
              </Button>
              <Button
                disabled={overwriteDisabled}
                onClick={() => void onPublish(true)}
                variant="outline"
              >
                {publishPending ? "发布中..." : "覆盖发布"}
              </Button>
            </div>
            {!publishedPath ? (
              <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
                技能还没有发布到项目中。当前启用状态、Version note 和 bindingTargets
                会随下一次发布一起生效。
              </div>
            ) : null}
            <div className="space-y-2 text-sm text-muted-foreground">
              <div>校验：{readiness.validationLabel}</div>
              <div>场景测试：{readiness.testLabel}</div>
              <div>发布：{readiness.publishLabel}</div>
              <div>技能包：{archiveVirtualPath ?? "尚未生成"}</div>
              <div>当前 revision：{activeRevisionId ?? "尚未发布"}</div>
              <div>已发布 revision：{publishedRevisionId ?? "尚未发布"}</div>
              <div>项目路径：{publishedPath ?? "尚未安装到项目"}</div>
              <div>最近发布：{lastPublishedAt ?? "尚无发布记录"}</div>
            </div>
            <Separator />
            <StudioListCard
              title="动作队列"
              items={nextActionLines}
              emptyText="当前还没有下一步动作。"
              compact
            />
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function GraphSection({
  data,
  graphFilter,
  selectedNodeId,
  selectedNode,
  onSelectNode,
}: {
  data: WorkbenchData;
  graphFilter: SkillStudioGraphFilter;
  selectedNodeId: string | null;
  selectedNode: WorkbenchData["graphModel"]["nodes"][number] | null;
  onSelectNode: (nodeId: string) => void;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">技能图谱工作台</CardTitle>
          <CardDescription>
            图谱页会把关系审阅与构建、校验、发布任务分开处理。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-4">
            <MiniMetric label="技能" value={String(data.graphOverview.skillCount)} />
            <MiniMetric label="边" value={String(data.graphOverview.edgeCount)} />
            <MiniMetric label="聚焦节点" value={String(data.graphModel.nodes.length)} />
            <MiniMetric label="筛选" value={formatGraphFilterLabel(graphFilter)} />
          </div>

          {data.graphModel.nodes.length > 0 ? (
            <div className="relative overflow-hidden rounded-[28px] border border-stone-800/80 bg-[radial-gradient(circle_at_top,_rgba(250,204,21,0.20),_transparent_30%),linear-gradient(180deg,_rgba(28,25,23,0.98),_rgba(12,10,9,0.98))] p-4 text-stone-100 shadow-[0_20px_60px_rgba(12,10,9,0.45)]">
              <svg viewBox="0 0 100 100" className="h-[24rem] w-full" preserveAspectRatio="none" aria-hidden="true">
                {data.graphModel.edges.map((edge) => {
                  const source = data.graphModel.nodes.find((node) => node.id === edge.source);
                  const target = data.graphModel.nodes.find((node) => node.id === edge.target);
                  if (!source || !target) return null;
                  return (
                    <line
                      key={edge.id}
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      stroke="rgba(251,191,36,0.55)"
                      strokeWidth={Math.max(0.6, edge.score * 1.5)}
                    />
                  );
                })}
              </svg>

              {data.graphModel.nodes.map((node) => (
                <button
                  key={node.id}
                  type="button"
                  className={cn(
                    "absolute -translate-x-1/2 -translate-y-1/2 rounded-2xl border px-3 py-2 text-left transition-transform hover:scale-[1.02]",
                    node.isFocus
                      ? "border-amber-300 bg-amber-200/18 text-amber-50 shadow-[0_12px_32px_rgba(250,204,21,0.22)]"
                      : selectedNodeId === node.id
                        ? "border-sky-300 bg-sky-400/18 text-sky-50 shadow-[0_12px_28px_rgba(56,189,248,0.20)]"
                        : "border-white/12 bg-white/8 text-stone-100",
                  )}
                  style={{ left: `${node.x}%`, top: `${node.y}%` }}
                  onClick={() => onSelectNode(node.id)}
                >
                  <div className="text-xs font-semibold uppercase tracking-[0.16em] text-stone-300">
                      {node.isFocus ? "焦点" : node.category}
                  </div>
                  <div className="mt-1 text-sm font-semibold">{node.skillName}</div>
                  <div className="mt-1 text-[11px] text-stone-300">{node.strongestScore.toFixed(2)}</div>
                </button>
              ))}
            </div>
          ) : (
            <div className="rounded-[28px] border border-dashed bg-background/60 p-5 text-sm text-muted-foreground">
              当前技能有关系数据后，这里会显示聚焦图谱。
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">节点检查器</CardTitle>
          <CardDescription>
            在保留图谱筛选上下文的同时，逐个检查聚焦节点。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {selectedNode ? (
            <>
              <div>
                <div className="text-lg font-semibold text-foreground">{selectedNode.skillName}</div>
                <div className="mt-1 text-sm leading-6 text-muted-foreground">
                  {localizeWorkspaceDisplayText(selectedNode.description)}
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <MiniMetric label="分类" value={selectedNode.category} />
                <MiniMetric label="启用状态" value={selectedNode.enabled ? "是" : "否"} />
                <MiniMetric label="Revisions" value={String(selectedNode.revisionCount)} />
                <MiniMetric label="Bindings" value={String(selectedNode.bindingCount)} />
              </div>
              <MiniMetric label="最高分值" value={selectedNode.strongestScore.toFixed(2)} />
              <div className="grid gap-3 sm:grid-cols-2">
                <MiniMetric
                  label="Active revision"
                  value={selectedNode.activeRevisionId ?? "None"}
                />
                <MiniMetric
                  label="Rollback target"
                  value={selectedNode.rollbackTargetId ?? "None"}
                />
              </div>
              <MiniMetric
                label="Last published"
                value={selectedNode.lastPublishedAt ?? "No publish yet"}
              />
              <div className="flex flex-wrap gap-2">
                {selectedNode.relationshipLabels.map((label) => (
                  <Badge key={label} variant="outline">
                    {label}
                  </Badge>
                ))}
              </div>
              <StudioListCard
                title="关联原因"
                items={selectedNode.reasons}
                emptyText="当前还没有图谱关系说明。"
                compact
              />
            </>
          ) : (
            <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
              选择一个图谱节点后，这里会展示它的关系上下文。
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ArtifactGroupsSection({
  groupedArtifacts,
  threadId,
  isMock,
  onOpenArtifact,
}: {
  groupedArtifacts: ReturnType<typeof groupSkillStudioArtifacts>;
  threadId: string;
  isMock: boolean;
  onOpenArtifact: (artifactPath: string) => void;
}) {
  return (
    <div className="grid gap-4">
      {groupedArtifacts.map((group) => (
        <Card key={group.id}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{group.label}</CardTitle>
            <CardDescription>当前阶段共 {group.count} 份产物。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {group.paths.map((artifactPath) => {
              const externalHref = urlOfArtifact({ filepath: artifactPath, threadId, isMock });
              return (
                <div key={artifactPath} className="flex items-center justify-between gap-3 rounded-xl border bg-background/70 p-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-foreground">
                      {getArtifactLabel(artifactPath)}
                    </div>
                    <div className="truncate text-xs text-muted-foreground">{artifactPath}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => onOpenArtifact(artifactPath)}>
                      查看
                    </Button>
                    <Button asChild size="icon" variant="ghost">
                      <a href={externalHref} rel="noreferrer" target="_blank" aria-label={getArtifactLabel(artifactPath)}>
                        <ArrowUpRightIcon className="size-4" />
                      </a>
                    </Button>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function StudioStat({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: typeof SparklesIcon;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-xl border bg-muted/10 p-4">
      <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
        <Icon className="size-4" />
        {label}
      </div>
      <div className="text-base font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">
        {localizeWorkspaceDisplayText(note)}
      </div>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border bg-background/70 p-3">
      <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold text-foreground">{value}</div>
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2 text-sm leading-6 text-foreground">
      {items.map((item) => (
        <li key={item} className="flex gap-2">
          <span className="mt-[9px] size-1.5 shrink-0 rounded-full bg-primary" />
          <span>{localizeWorkspaceDisplayText(item)}</span>
        </li>
      ))}
    </ul>
  );
}

function StudioListCard({
  title,
  items,
  emptyText,
  compact = false,
}: {
  title: string;
  items: string[];
  emptyText: string;
  compact?: boolean;
}) {
  return (
    <Card className={compact ? "shadow-none" : undefined}>
      <CardHeader className={compact ? "pb-2" : "pb-3"}>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length > 0 ? (
          <BulletList items={items} />
        ) : (
          <div className="text-sm text-muted-foreground">{emptyText}</div>
        )}
      </CardContent>
    </Card>
  );
}

function KeyValueRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border bg-muted/10 px-4 py-3">
      <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm leading-6 text-foreground">{value}</div>
    </div>
  );
}
