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
import { useArtifactContent } from "@/core/artifacts/hooks";
import { urlOfArtifact } from "@/core/artifacts/utils";
import { usePublishSkill, useSkillGraph } from "@/core/skills/hooks";
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
  buildSkillStudioReadinessSummary,
  formatSkillStudioStatus,
  groupSkillStudioArtifacts,
  resolveSkillStudioAssistantIdentity,
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
  if (path.endsWith("/skill-draft.json")) return "Skill draft JSON";
  if (path.endsWith("/skill-package.json")) return "Skill package";
  if (path.endsWith("/SKILL.md")) return "SKILL.md";
  if (path.endsWith("/agents/openai.yaml")) return "UI metadata";
  if (path.endsWith("/references/domain-rules.md")) return "Domain rules";
  if (path.endsWith("/test-matrix.json")) return "Test matrix";
  if (path.endsWith("/validation-report.json")) return "Validation JSON";
  if (path.endsWith("/publish-readiness.json")) return "Publish readiness";
  if (path.endsWith(".skill")) return "Installable .skill package";
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

function deriveNextActionLines(args: {
  publishNextActions: string[];
  validationErrors: string[];
  validationWarnings: string[];
  blockingCount: number;
}) {
  if (args.publishNextActions.length > 0) return args.publishNextActions;
  if (args.validationErrors.length > 0) return args.validationErrors.slice(0, 3);
  if (args.validationWarnings.length > 0) return args.validationWarnings.slice(0, 3);
  if (args.blockingCount > 0) {
    return ["Resolve blocking validation, testing, or publish gates before release."];
  }
  return ["The package is ready for a dry-run or final publish review."];
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
  const [publishFeedback, setPublishFeedback] = useState<PublishFeedback | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const studioState = useMemo(() => {
    const raw = thread.values.submarine_skill_studio;
    return raw && typeof raw === "object" ? (raw as SkillStudioState) : null;
  }, [thread.values.submarine_skill_studio]);

  const currentSkillName =
    typeof studioState?.skill_name === "string" ? studioState.skill_name : undefined;
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
  const archiveVirtualPath =
    skillPackage?.package_archive_virtual_path ??
    skillPackage?.archive_virtual_path ??
    studioState?.package_archive_virtual_path ??
    null;
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
  const publishDisabled = [
    isMock,
    !archiveVirtualPath,
    publishSkill.isPending,
    readiness.blockingCount > 0,
  ].some(Boolean);
  const overwriteDisabled = [isMock, !archiveVirtualPath, publishSkill.isPending].some(
    Boolean,
  );

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

  async function handlePublish(overwrite: boolean) {
    if (!archiveVirtualPath) {
      setPublishFeedback({
        variant: "destructive",
        title: "No installable package yet",
        message:
          "Generate and validate the skill package before publishing it to the project.",
      });
      return;
    }

    try {
      const result = await publishSkill.mutateAsync({
        thread_id: threadId,
        path: archiveVirtualPath,
        overwrite,
        enable: true,
      });
      setPublishFeedback({
        variant: "default",
        title: overwrite ? "Skill updated" : "Skill published",
        message: `${result.message}. Enabled: ${result.enabled ? "yes" : "no"}.`,
      });
      toast.success(overwrite ? "Skill updated in project" : "Skill published to project");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to publish the skill package.";
      setPublishFeedback({
        variant: "destructive",
        title: "Publish failed",
        message,
      });
      toast.error(message);
    }
  }

  const data: WorkbenchData = {
    threadId,
    assistantLabel,
    assistantMode,
    builtinSkills,
    skillName,
    skillTitle,
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
                Dedicated Skill Studio
              </div>
              <div className="space-y-2">
                <CardTitle className="text-2xl">{skillTitle}</CardTitle>
                <CardDescription className="max-w-3xl text-sm leading-6">
                  {assistantLabel} keeps package review, validation, testing,
                  publish readiness, and graph review visible as separate
                  lifecycle surfaces.
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
                "Pending openai.yaml"
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
              feedback={publishFeedback}
              publishDisabled={publishDisabled}
              overwriteDisabled={overwriteDisabled}
              publishPending={publishSkill.isPending}
              readiness={readiness}
              archiveVirtualPath={archiveVirtualPath}
              publishReadiness={publishReadiness}
              nextActionLines={nextActionLines}
              onPublish={handlePublish}
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
          label="Current Skill"
          value={data.skillName}
          note="Current package identity for this lifecycle review."
        />
        <StudioStat
          icon={ShieldCheckIcon}
          label="Validation"
          value={data.readiness.validationLabel}
          note={`${data.validation?.error_count ?? 0} error(s), ${data.validation?.warning_count ?? 0} warning(s)`}
        />
        <StudioStat
          icon={TestTubeDiagonalIcon}
          label="Scenario Tests"
          value={data.readiness.testLabel}
          note={`${data.testMatrix?.scenario_test_count ?? 0} prepared scenario(s)`}
        />
        <StudioStat
          icon={BadgeCheckIcon}
          label="Publish"
          value={data.readiness.publishLabel}
          note={`${data.publishReadiness?.blocking_count ?? data.readiness.blockingCount} blocking gate(s)`}
        />
      </div>

      <Card className="border-dashed bg-muted/10 shadow-none">
        <CardContent className="grid gap-4 p-5 xl:grid-cols-[minmax(0,1fr)_280px] xl:items-center">
          <div className="space-y-3">
            <div>
              <div className="text-sm font-medium text-foreground">Readiness summary</div>
              <div className="text-sm leading-6 text-muted-foreground">
                The workbench keeps structure, dry-run preparation, publish
                gates, and graph positioning visible before the package is
                enabled in the project.
              </div>
            </div>
            <Progress value={data.readiness.progress} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <MiniMetric label="Progress" value={`${data.readiness.progress}%`} />
            <MiniMetric label="Blocking" value={String(data.readiness.blockingCount)} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.95fr)]">
        <StudioListCard
          title="Next action guidance"
          items={data.nextActionLines}
          emptyText="No next actions are available yet."
        />
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Package identity</CardTitle>
            <CardDescription>
              The current draft stays tied to one package name and one dedicated
              assistant identity.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <KeyValueRow label="Skill name" value={data.skillName} />
            <KeyValueRow
              label="Purpose"
              value={data.draft?.skill_purpose ?? "Pending expert purpose"}
            />
            <KeyValueRow label="Agent mode" value={data.assistantMode} />
            <KeyValueRow label="Artifacts" value={`${data.studioArtifacts.length} total artifact(s)`} />
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
            <CardTitle className="text-base">Dedicated Skill Creator agent</CardTitle>
            <CardDescription>
              This thread keeps one dedicated creator identity so the package
              remains consistent across revisions.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <div className="text-sm font-medium">{data.assistantLabel}</div>
              <div className="text-sm text-muted-foreground">
                Agent mode: {data.assistantMode}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {data.builtinSkills.map((skill) => (
                <Badge key={skill} variant="outline">
                  {skill}
                </Badge>
              ))}
            </div>
            <Separator />
            <BulletList
              items={[
                "Experts provide domain rules, thresholds, and exceptions.",
                `${data.assistantLabel} turns those decisions into a reviewable skill package.`,
                "Validation, scenario testing, and publish gates stay visible in the workbench.",
              ]}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Skill package summary</CardTitle>
            <CardDescription>
              The package contract stays alongside UI metadata and review
              artifacts for this skill.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <KeyValueRow label="Skill name" value={data.skillName} />
            <KeyValueRow
              label="Purpose"
              value={data.draft?.skill_purpose ?? "Pending expert purpose"}
            />
            <KeyValueRow
              label="Frontmatter description"
              value={data.draft?.description ?? "Pending trigger description"}
            />
            <KeyValueRow label="UI metadata" value={uiMetadataPath} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <StudioListCard
          title="Trigger conditions"
          items={data.draft?.trigger_conditions ?? []}
          emptyText="No trigger conditions have been captured yet."
        />
        <StudioListCard
          title="Acceptance criteria"
          items={data.draft?.acceptance_criteria ?? []}
          emptyText="No acceptance criteria have been captured yet."
        />
      </div>

      <StudioListCard
        title="Workflow steps"
        items={data.draft?.workflow_steps ?? []}
        emptyText="No workflow has been captured yet."
      />

      <div className="grid gap-4 xl:grid-cols-2">
        <StudioListCard
          title="Expert rules"
          items={data.draft?.expert_rules ?? []}
          emptyText="No expert rules have been captured yet."
        />
        <StudioListCard
          title="Draft scenario tests"
          items={data.draft?.test_scenarios ?? []}
          emptyText="No scenario tests have been captured yet."
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
          <CardTitle className="text-base">Validation checks</CardTitle>
          <CardDescription>
            Structural validation stays strict so the expert can see what blocks
            review before any publish step.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <MiniMetric label="Passed" value={String(validation?.passed_checks?.length ?? 0)} />
            <MiniMetric label="Errors" value={String(validation?.error_count ?? 0)} />
            <MiniMetric label="Warnings" value={String(validation?.warning_count ?? 0)} />
          </div>
          <StudioListCard
            title="Passed checks"
            items={validation?.passed_checks ?? []}
            emptyText="No passed checks yet."
            compact
          />
        </CardContent>
      </Card>

      <div className="grid gap-4">
        <StudioListCard
          title="Errors"
          items={validation?.errors ?? []}
          emptyText="No validation errors."
        />
        <StudioListCard
          title="Warnings"
          items={validation?.warnings ?? []}
          emptyText="No validation warnings."
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
          <CardTitle className="text-base">Scenario test matrix</CardTitle>
          <CardDescription>
            These scenarios are the immediate handoff for expert dry-runs and
            future automated skill checks.
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
                  {scenario.expected_outcome}
                </div>
                {(scenario.blocking_reasons ?? []).length > 0 ? (
                  <div className="mt-2 text-xs text-muted-foreground">
                    Blocking: {(scenario.blocking_reasons ?? []).join(", ")}
                  </div>
                ) : null}
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
              Scenario tests will appear here after the expert and Skill Creator
              define dry-run cases.
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Dry-run readiness</CardTitle>
            <CardDescription>
              Keep blocking counts and test preparation visible before publish.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <MiniMetric label="Scenario count" value={String(testMatrix?.scenario_test_count ?? 0)} />
            <MiniMetric label="Blocking" value={String(testMatrix?.blocking_count ?? 0)} />
          </CardContent>
        </Card>
        <StudioListCard
          title="Draft test scenarios"
          items={draft?.test_scenarios ?? []}
          emptyText="No draft test scenarios have been captured yet."
        />
      </div>
    </div>
  );
}

function PublishSection({
  feedback,
  publishDisabled,
  overwriteDisabled,
  publishPending,
  readiness,
  archiveVirtualPath,
  publishReadiness,
  nextActionLines,
  onPublish,
}: {
  feedback: PublishFeedback | null;
  publishDisabled: boolean;
  overwriteDisabled: boolean;
  publishPending: boolean;
  readiness: WorkbenchData["readiness"];
  archiveVirtualPath: string | null;
  publishReadiness: PublishReadinessPayload | null;
  nextActionLines: string[];
  onPublish: (overwrite: boolean) => Promise<void>;
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
            <CardTitle className="text-base">Publish gates</CardTitle>
            <CardDescription>
              These gates must pass before publish so a draft skill does not get
              pushed into the live project by accident.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(publishReadiness?.gates ?? []).length > 0 ? (
              (publishReadiness?.gates ?? []).map((gate) => (
                <div
                  key={gate.id}
                  className="flex items-center justify-between gap-3 rounded-xl border bg-muted/10 p-3"
                >
                  <div className="text-sm text-foreground">{gate.label}</div>
                  <Badge variant={getStatusTone(gate.status)}>
                    {formatSkillStudioStatus(gate.status)}
                  </Badge>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
                Publish gates will appear here once the readiness bundle is
                available.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Next actions</CardTitle>
            <CardDescription>
              Keep the final review queue explicit before release.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StudioListCard
              title="Action queue"
              items={nextActionLines}
              emptyText="No next actions are available yet."
              compact
            />
            <Separator />
            <div className="flex flex-wrap gap-2">
              <Button disabled={publishDisabled} onClick={() => void onPublish(false)}>
                {publishPending ? "Publishing..." : "Publish and enable"}
              </Button>
              <Button
                disabled={overwriteDisabled}
                onClick={() => void onPublish(true)}
                variant="outline"
              >
                {publishPending ? "Publishing..." : "Overwrite publish"}
              </Button>
            </div>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div>Validation: {readiness.validationLabel}</div>
              <div>Scenario tests: {readiness.testLabel}</div>
              <div>Publish: {readiness.publishLabel}</div>
              <div>Package: {archiveVirtualPath ?? "Not generated yet"}</div>
            </div>
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
          <CardTitle className="text-base">Skill graph workbench</CardTitle>
          <CardDescription>
            The graph page keeps focused relationship review separate from build,
            validation, and publish tasks.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-4">
            <MiniMetric label="Skills" value={String(data.graphOverview.skillCount)} />
            <MiniMetric label="Edges" value={String(data.graphOverview.edgeCount)} />
            <MiniMetric label="Focused" value={String(data.graphModel.nodes.length)} />
            <MiniMetric label="Filter" value={graphFilter.replaceAll("-", " ")} />
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
                    {node.isFocus ? "Focus" : node.category}
                  </div>
                  <div className="mt-1 text-sm font-semibold">{node.skillName}</div>
                  <div className="mt-1 text-[11px] text-stone-300">{node.strongestScore.toFixed(2)}</div>
                </button>
              ))}
            </div>
          ) : (
            <div className="rounded-[28px] border border-dashed bg-background/60 p-5 text-sm text-muted-foreground">
              The focused graph will appear here after relationship data is
              available for the current skill.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Node inspector</CardTitle>
          <CardDescription>
            Inspect one focused node at a time while keeping filter context on
            the graph canvas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {selectedNode ? (
            <>
              <div>
                <div className="text-lg font-semibold text-foreground">{selectedNode.skillName}</div>
                <div className="mt-1 text-sm leading-6 text-muted-foreground">
                  {selectedNode.description}
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <MiniMetric label="Category" value={selectedNode.category} />
                <MiniMetric label="Enabled" value={selectedNode.enabled ? "yes" : "no"} />
              </div>
              <MiniMetric label="Strongest score" value={selectedNode.strongestScore.toFixed(2)} />
              <div className="flex flex-wrap gap-2">
                {selectedNode.relationshipLabels.map((label) => (
                  <Badge key={label} variant="outline">
                    {label}
                  </Badge>
                ))}
              </div>
              <StudioListCard
                title="Reasons"
                items={selectedNode.reasons}
                emptyText="No graph rationale is available yet."
                compact
              />
            </>
          ) : (
            <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
              Select a graph node to inspect its relationship context.
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
            <CardDescription>{group.count} artifact(s) in this stage.</CardDescription>
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
                      鏌ョ湅
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
      <div className="mt-1 text-sm text-muted-foreground">{note}</div>
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
          <span>{item}</span>
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
