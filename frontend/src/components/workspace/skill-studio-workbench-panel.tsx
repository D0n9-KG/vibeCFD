"use client";

import {
  ArrowUpRightIcon,
  BadgeCheckIcon,
  ShieldCheckIcon,
  SparklesIcon,
  TestTubeDiagonalIcon,
  WandSparklesIcon,
} from "lucide-react";
import { useMemo, useState } from "react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { urlOfArtifact } from "@/core/artifacts/utils";
import { usePublishSkill, useSkillGraph } from "@/core/skills/hooks";

import { useArtifacts } from "./artifacts";
import { useThread } from "./messages/context";
import {
  buildFocusedSkillGraphItems,
  buildSkillGraphOverview,
} from "./skill-graph.utils";
import {
  buildSkillStudioReadinessSummary,
  formatSkillStudioStatus,
  groupSkillStudioArtifacts,
} from "./skill-studio-workbench.utils";

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
  report_virtual_path?: string | null;
  package_virtual_path?: string | null;
  package_archive_virtual_path?: string | null;
  test_virtual_path?: string | null;
  publish_virtual_path?: string | null;
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
  validation_status?: string;
  test_status?: string;
  publish_status?: string;
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
  publish_gate_count?: number;
  blocking_count?: number;
  gates?: Array<{
    id?: string;
    label?: string;
    status?: string;
  }> | null;
  next_actions?: string[] | null;
};

type SkillPackagePayload = {
  assistant_mode?: string;
  assistant_label?: string;
  builtin_skills?: string[] | null;
  validation_status?: string;
  test_status?: string;
  publish_status?: string;
  package_archive_virtual_path?: string;
  archive_virtual_path?: string;
  ui_metadata_virtual_path?: string;
};

function safeJsonParse<T>(content?: string | null): T | null {
  if (!content) return null;
  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

function pickArtifact(
  artifacts: string[],
  predicate: (artifact: string) => boolean,
) {
  return artifacts.find(predicate) ?? null;
}

function getArtifactLabel(path: string) {
  if (path.endsWith("/skill-draft.json")) return "Skill draft JSON";
  if (path.endsWith("/skill-package.json")) return "Skill package";
  if (path.endsWith("/SKILL.md")) return "SKILL.md";
  if (path.endsWith("/agents/openai.yaml")) return "UI metadata";
  if (path.endsWith("/references/domain-rules.md")) return "Domain rules";
  if (path.endsWith("/test-matrix.json")) return "Test matrix";
  if (path.endsWith("/test-matrix.md")) return "Test matrix report";
  if (path.endsWith("/validation-report.json")) return "Validation JSON";
  if (path.endsWith("/validation-report.md")) return "Validation report";
  if (path.endsWith("/validation-report.html")) return "Validation HTML";
  if (path.endsWith("/publish-readiness.json")) return "Publish readiness";
  if (path.endsWith("/publish-readiness.md")) return "Publish readiness report";
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

export function SkillStudioWorkbenchPanel({
  threadId,
  className,
}: {
  threadId: string;
  className?: string;
}) {
  const { thread, isMock } = useThread();
  const { select, setOpen } = useArtifacts();
  const publishSkill = usePublishSkill();
  const [publishFeedback, setPublishFeedback] = useState<{
    variant: "default" | "destructive";
    title: string;
    message: string;
  } | null>(null);

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
    const threadArtifacts = Array.isArray(thread.values.artifacts)
      ? thread.values.artifacts
      : [];
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

  const draftJson = pickArtifact(
    studioArtifacts,
    (artifact) => artifact.endsWith("/skill-draft.json"),
  );
  const packageJson = pickArtifact(
    studioArtifacts,
    (artifact) => artifact.endsWith("/skill-package.json"),
  );
  const validationJson = pickArtifact(
    studioArtifacts,
    (artifact) => artifact.endsWith("/validation-report.json"),
  );
  const testMatrixJson = pickArtifact(
    studioArtifacts,
    (artifact) => artifact.endsWith("/test-matrix.json"),
  );
  const publishJson = pickArtifact(
    studioArtifacts,
    (artifact) => artifact.endsWith("/publish-readiness.json"),
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

  const draft = useMemo(
    () => safeJsonParse<SkillDraftPayload>(draftContent),
    [draftContent],
  );
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

  const assistantLabel =
    draft?.assistant_label ??
    studioState?.assistant_label ??
    "Claude Code · Skill Creator";
  const builtinSkills =
    draft?.builtin_skills ??
    skillPackage?.builtin_skills ??
    studioState?.builtin_skills ??
    [];
  const skillName =
    draft?.skill_name ?? studioState?.skill_name ?? "pending-skill";
  const skillTitle = draft?.skill_title ?? skillName;
  const archiveVirtualPath =
    skillPackage?.package_archive_virtual_path ??
    skillPackage?.archive_virtual_path ??
    studioState?.package_archive_virtual_path ??
    null;
  const readiness = buildSkillStudioReadinessSummary({
    errorCount: validation?.error_count ?? studioState?.error_count ?? 0,
    warningCount: validation?.warning_count ?? studioState?.warning_count ?? 0,
    validationStatus:
      validation?.status ?? studioState?.validation_status ?? "draft_only",
    testStatus: testMatrix?.status ?? studioState?.test_status ?? "draft_only",
    publishStatus:
      publishReadiness?.status ?? studioState?.publish_status ?? "draft_only",
  });
  const groupedArtifacts = groupSkillStudioArtifacts(studioArtifacts);
  const graphOverview = buildSkillGraphOverview(skillGraph);
  const focusedSkillGraphItems = buildFocusedSkillGraphItems(skillGraph);
  const publishDisabled = [
    isMock,
    !archiveVirtualPath,
    publishSkill.isPending,
    readiness.blockingCount > 0,
  ].some(Boolean);
  const overwriteDisabled = [isMock, !archiveVirtualPath, publishSkill.isPending].some(
    Boolean,
  );

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

  return (
    <div className={className}>
      <Card>
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
                  这是领域专家专用的 Skill Creator 工作台。Claude Code 会以独立的
                  Skill Creator 代理身份协助整理规则、生成 skill 包、准备测试矩阵，并在发布前给出清晰的就绪判断。
                </CardDescription>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{assistantLabel}</Badge>
              <Badge variant={getStatusTone(validation?.status ?? studioState?.validation_status)}>
                {formatSkillStudioStatus(
                  validation?.status ?? studioState?.validation_status,
                )}
              </Badge>
              <Badge variant={getStatusTone(testMatrix?.status ?? studioState?.test_status)}>
                {formatSkillStudioStatus(
                  testMatrix?.status ?? studioState?.test_status,
                )}
              </Badge>
              <Badge
                variant={getStatusTone(
                  publishReadiness?.status ?? studioState?.publish_status,
                )}
              >
                {formatSkillStudioStatus(
                  publishReadiness?.status ?? studioState?.publish_status,
                )}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6 p-5">
          <div className="grid gap-3 xl:grid-cols-4">
            <StudioStat
              icon={SparklesIcon}
              label="Current Skill"
              value={skillName}
              note="Current draft package being prepared for review."
            />
            <StudioStat
              icon={ShieldCheckIcon}
              label="Validation"
              value={readiness.validationLabel}
              note={`${validation?.error_count ?? studioState?.error_count ?? 0} error(s), ${validation?.warning_count ?? studioState?.warning_count ?? 0} warning(s)`}
            />
            <StudioStat
              icon={TestTubeDiagonalIcon}
              label="Scenario Tests"
              value={readiness.testLabel}
              note={`${testMatrix?.scenario_test_count ?? 0} prepared scenario(s)`}
            />
            <StudioStat
              icon={BadgeCheckIcon}
              label="Publish"
              value={readiness.publishLabel}
              note={`${publishReadiness?.blocking_count ?? readiness.blockingCount} blocking gate(s)`}
            />
          </div>

          <Card className="border-dashed bg-muted/10 shadow-none">
            <CardContent className="grid gap-4 p-5 xl:grid-cols-[minmax(0,1fr)_280px] xl:items-center">
              <div className="space-y-3">
                <div>
                  <div className="text-sm font-medium text-foreground">
                    Publish readiness
                  </div>
                  <div className="text-sm leading-6 text-muted-foreground">
                    The workbench treats structure, scenario testing, and publish gates as first-class signals. The right-side conversation is dedicated to the Skill Creator agent, not the main vibe CFD supervisor.
                  </div>
                </div>
                <Progress value={readiness.progress} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <MiniMetric
                  label="Progress"
                  value={`${readiness.progress}%`}
                />
                <MiniMetric
                  label="Blocking"
                  value={String(readiness.blockingCount)}
                />
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="package">
            <TabsList variant="line">
              <TabsTrigger value="package">技能包</TabsTrigger>
              <TabsTrigger value="validation">校验与测试</TabsTrigger>
              <TabsTrigger value="publish">发布就绪</TabsTrigger>
              <TabsTrigger value="artifacts">Artifacts</TabsTrigger>
              <TabsTrigger value="graph">Skill graph</TabsTrigger>
            </TabsList>

            <TabsContent value="package" className="space-y-4 pt-2">
              <div className="grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">专属 Skill Creator 代理</CardTitle>
                    <CardDescription>
                      Skill Studio 使用独立的 Claude Code 代理身份，默认围绕 skill-creator 与 writing-skills 方法论协作。
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-1">
                      <div className="text-sm font-medium">{assistantLabel}</div>
                      <div className="text-sm text-muted-foreground">
                        Agent mode:{" "}
                        {draft?.assistant_mode ??
                          skillPackage?.assistant_mode ??
                          studioState?.assistant_mode ??
                          "claude-code-skill-creator"}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {builtinSkills.map((skill) => (
                        <Badge key={skill} variant="outline">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                    <Separator />
                    <BulletList
                      items={[
                        "Experts provide domain rules, thresholds, and exceptions.",
                        "Claude Code turns those decisions into a reviewable skill package.",
                        "Validation, scenario testing, and publish gates stay visible in the workbench.",
                      ]}
                    />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Skill 包摘要</CardTitle>
                    <CardDescription>
                      这份摘要会和 SKILL.md、UI metadata、测试矩阵一起进入 artifacts，方便专家审阅和发布前复核。
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <KeyValueRow label="Skill name" value={skillName} />
                    <KeyValueRow
                      label="Purpose"
                      value={draft?.skill_purpose ?? "Pending expert purpose"}
                    />
                    <KeyValueRow
                      label="Frontmatter description"
                      value={draft?.description ?? "Pending trigger description"}
                    />
                    <KeyValueRow
                      label="UI metadata"
                      value={skillPackage?.ui_metadata_virtual_path ?? studioState?.ui_metadata_virtual_path ?? "Pending openai.yaml"}
                    />
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-4 xl:grid-cols-2">
                <StudioListCard
                  title="Trigger conditions"
                  items={draft?.trigger_conditions ?? []}
                  emptyText="No trigger conditions have been captured yet."
                />
                <StudioListCard
                  title="Acceptance criteria"
                  items={draft?.acceptance_criteria ?? []}
                  emptyText="No acceptance criteria have been captured yet."
                />
              </div>
              <StudioListCard
                title="Workflow steps"
                items={draft?.workflow_steps ?? []}
                emptyText="No workflow has been captured yet."
              />
              <div className="grid gap-4 xl:grid-cols-2">
                <StudioListCard
                  title="Expert rules"
                  items={draft?.expert_rules ?? []}
                  emptyText="No expert rules have been captured yet."
                />
                <StudioListCard
                  title="Scenario tests"
                  items={draft?.test_scenarios ?? []}
                  emptyText="No scenario tests have been captured yet."
                />
              </div>
            </TabsContent>

            <TabsContent value="validation" className="space-y-4 pt-2">
              <div className="grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Validation checks</CardTitle>
                    <CardDescription>
                      Structure validation stays strict so the expert sees what blocks review before any publish step.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <MiniMetric
                        label="Passed"
                        value={String(validation?.passed_checks?.length ?? 0)}
                      />
                      <MiniMetric
                        label="Errors"
                        value={String(validation?.error_count ?? 0)}
                      />
                      <MiniMetric
                        label="Warnings"
                        value={String(validation?.warning_count ?? 0)}
                      />
                    </div>
                    <StudioListCard
                      title="Passed checks"
                      items={validation?.passed_checks ?? []}
                      emptyText="No passed checks yet."
                      compact
                    />
                    <StudioListCard
                      title="Errors"
                      items={validation?.errors ?? []}
                      emptyText="No validation errors."
                      compact
                    />
                    <StudioListCard
                      title="Warnings"
                      items={validation?.warnings ?? []}
                      emptyText="No validation warnings."
                      compact
                    />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Scenario test matrix</CardTitle>
                    <CardDescription>
                      These scenarios are the immediate handoff for expert dry-runs and future automated skill checks.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {(testMatrix?.scenario_tests ?? []).length > 0 ? (
                      (testMatrix?.scenario_tests ?? []).map((scenario) => (
                        <div
                          key={scenario.id ?? scenario.scenario}
                          className="rounded-xl border bg-muted/10 p-4"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="text-sm font-medium text-foreground">
                              {scenario.scenario}
                            </div>
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
                        Scenario tests will appear here after the expert and Skill Creator define dry-run cases.
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="graph" className="space-y-4 pt-2">
              <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Skill graph overview</CardTitle>
                    <CardDescription>
                      Local SkillNet-lite analysis shows which skills already overlap, compose well, or should be routed together before publish.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-3 sm:grid-cols-2">
                      <MiniMetric label="Skills" value={String(graphOverview.skillCount)} />
                      <MiniMetric label="Edges" value={String(graphOverview.edgeCount)} />
                      <MiniMetric label="Enabled" value={String(graphOverview.enabledCount)} />
                      <MiniMetric label="Custom" value={String(graphOverview.customCount)} />
                    </div>
                    <StudioListCard
                      title="Top relationship types"
                      items={graphOverview.topRelationships.map((item) => `${item.label} · ${item.count}`)}
                      emptyText="Relationship analysis is not available yet."
                      compact
                    />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Current skill relationships</CardTitle>
                    <CardDescription>
                      Use this list to decide whether the new package should reuse, replace, compose with, or stay separate from existing DeerFlow skills.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {focusedSkillGraphItems.length > 0 ? (
                      focusedSkillGraphItems.map((item) => (
                        <div
                          key={item.skillName}
                          className="rounded-xl border bg-muted/10 p-4"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="text-sm font-medium text-foreground">
                              {item.skillName}
                            </div>
                            <Badge variant="outline">
                              {item.strongestScore.toFixed(2)}
                            </Badge>
                          </div>
                          <div className="mt-2 text-sm leading-6 text-muted-foreground">
                            {item.description}
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {item.relationshipLabels.map((label) => (
                              <Badge key={label} variant="outline">
                                {label}
                              </Badge>
                            ))}
                          </div>
                          <div className="mt-3 space-y-1 text-xs leading-5 text-muted-foreground">
                            {item.reasons.map((reason) => (
                              <div key={reason}>• {reason}</div>
                            ))}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-xl border border-dashed bg-background/60 p-4 text-sm text-muted-foreground">
                        Publish or install more local skills to see relationship guidance for this package.
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="publish" className="space-y-4 pt-2">
              {publishFeedback ? (
                <Alert variant={publishFeedback.variant}>
                  <ShieldCheckIcon className="size-4" />
                  <AlertTitle>{publishFeedback.title}</AlertTitle>
                  <AlertDescription>{publishFeedback.message}</AlertDescription>
                </Alert>
              ) : null}
              <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Publish gates</CardTitle>
                    <CardDescription>
                      发布前必须通过这些门槛，避免专家直接把未验证的 draft 推进到 live skills。
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {(publishReadiness?.gates ?? []).map((gate) => (
                      <div
                        key={gate.id}
                        className="flex items-center justify-between gap-3 rounded-xl border bg-muted/10 p-3"
                      >
                        <div className="text-sm text-foreground">{gate.label}</div>
                        <Badge variant={getStatusTone(gate.status)}>
                          {formatSkillStudioStatus(gate.status)}
                        </Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Next actions</CardTitle>
                    <CardDescription>
                      专家和 Skill Creator 下一步需要做的事会固定在这里，避免工作台只停留在“看草稿”。
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StudioListCard
                      title="Action queue"
                      items={publishReadiness?.next_actions ?? []}
                      emptyText="No next actions are available yet."
                      compact
                    />
                    <Separator />
                    <div className="flex flex-wrap gap-2">
                      <Button
                        disabled={publishDisabled}
                        onClick={() => void handlePublish(false)}
                      >
                        {publishSkill.isPending ? "Publishing..." : "Publish and enable"}
                      </Button>
                      <Button
                        disabled={overwriteDisabled}
                        onClick={() => void handlePublish(true)}
                        variant="outline"
                      >
                        {publishSkill.isPending ? "Publishing..." : "Overwrite publish"}
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
            </TabsContent>

            <TabsContent value="artifacts" className="space-y-4 pt-2">
              {groupedArtifacts.map((group) => (
                <Card key={group.id}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">{group.label}</CardTitle>
                    <CardDescription>
                      {group.count} artifact(s) in this stage.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {group.paths.map((artifactPath) => {
                      const externalHref = urlOfArtifact({
                        filepath: artifactPath,
                        threadId,
                        isMock: Boolean(isMock),
                      });
                      return (
                        <div
                          key={artifactPath}
                          className="flex items-center justify-between gap-3 rounded-xl border bg-background/70 p-3"
                        >
                          <div className="min-w-0">
                            <div className="truncate text-sm font-medium text-foreground">
                              {getArtifactLabel(artifactPath)}
                            </div>
                            <div className="truncate text-xs text-muted-foreground">
                              {artifactPath}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                select(artifactPath);
                                setOpen(true);
                              }}
                            >
                              查看
                            </Button>
                            <Button asChild size="icon" variant="ghost">
                              <a
                                aria-label={`Open ${getArtifactLabel(artifactPath)} in a new window`}
                                href={externalHref}
                                rel="noreferrer"
                                target="_blank"
                              >
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
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
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
      <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </div>
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
      <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-sm leading-6 text-foreground">{value}</div>
    </div>
  );
}
