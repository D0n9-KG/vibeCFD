import type {
  SkillGraphResponse,
  SkillLifecycleRecord,
  SkillLifecycleSummary,
} from "@/core/skills/api";

import {
  buildFocusedSkillGraphItems,
  buildSkillGraphOverview,
} from "../skill-graph.utils.ts";
import {
  buildSkillStudioPublishPanelModel,
  buildSkillStudioReadinessSummary,
  groupSkillStudioArtifacts,
  resolveSkillStudioAssistantIdentity,
  type SkillStudioArtifactGroup,
} from "../skill-studio-workbench.utils.ts";

export type SkillStudioThreadState = {
  skill_name?: string | null;
  skill_asset_id?: string | null;
  assistant_mode?: string | null;
  assistant_label?: string | null;
  builtin_skills?: string[] | null;
  validation_status?: string | null;
  test_status?: string | null;
  publish_status?: string | null;
  error_count?: number | null;
  warning_count?: number | null;
  package_virtual_path?: string | null;
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

export type SkillDraftPayload = {
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

export type ValidationPayload = {
  status?: string;
  error_count?: number;
  warning_count?: number;
  passed_checks?: string[] | null;
  errors?: string[] | null;
  warnings?: string[] | null;
};

export type TestMatrixPayload = {
  status?: string;
  scenario_test_count?: number;
  blocking_count?: number;
  scenario_tests?:
    | Array<{
        id?: string;
        scenario?: string;
        status?: string;
        expected_outcome?: string;
        blocking_reasons?: string[] | null;
      }>
    | null;
};

export type PublishReadinessPayload = {
  status?: string;
  blocking_count?: number;
  gates?: Array<{ id?: string; label?: string; status?: string }> | null;
  next_actions?: string[] | null;
};

export type SkillPackagePayload = {
  assistant_mode?: string;
  assistant_label?: string;
  builtin_skills?: string[] | null;
  package_archive_virtual_path?: string;
  archive_virtual_path?: string;
  ui_metadata_virtual_path?: string;
};

export type SkillStudioDetailModel = {
  assistant: {
    mode: string;
    label: string;
    builtinSkills: string[];
  };
  artifactGroups: SkillStudioArtifactGroup[];
  readiness: ReturnType<typeof buildSkillStudioReadinessSummary>;
  define: {
    skillName: string;
    skillTitle: string;
    skillGoal: string;
    triggerCount: number;
    triggerConditions: string[];
    constraintCount: number;
    constraints: string[];
    acceptanceCriteria: string[];
    builtinSkills: string[];
  };
  evaluate: {
    status: string;
    errorCount: number;
    warningCount: number;
    passedChecks: string[];
    validationErrors: string[];
    validationWarnings: string[];
    scenarioMatrix: {
      scenarioCount: number;
      blockedCount: number;
      scenarios: Array<{
        id: string;
        scenario: string;
        status: string;
        expectedOutcome: string;
        blockingReasons: string[];
      }>;
    };
    dryRun: {
      ready: boolean;
      nextActions: string[];
    };
  };
  publish: ReturnType<typeof buildSkillStudioPublishPanelModel> & {
    gateCount: number;
    blockedGateCount: number;
    gates: Array<{ id: string; label: string; status: string }>;
    nextActions: string[];
  };
  graph: {
    relationshipCount: number;
    highImpactCount: number;
    upstreamCount: number;
    downstreamCount: number;
    overview: ReturnType<typeof buildSkillGraphOverview>;
    relatedSkills: ReturnType<typeof buildFocusedSkillGraphItems>;
  };
};

export type BuildSkillStudioDetailModelInput = {
  studioState: SkillStudioThreadState | null;
  draft: SkillDraftPayload | null;
  skillPackage: SkillPackagePayload | null;
  validation: ValidationPayload | null;
  testMatrix: TestMatrixPayload | null;
  publishReadiness: PublishReadinessPayload | null;
  lifecycleSummary: SkillLifecycleSummary | null;
  lifecycleDetail: SkillLifecycleRecord | null;
  skillGraph: SkillGraphResponse | null;
  studioArtifacts: string[];
};

const SKILL_STUDIO_COPY_MAP: Record<string, string> = {
  "Skill structure is valid": "技能结构校验通过",
  "Trigger description is discoverable": "触发描述可被发现",
  "Scenario tests are prepared": "场景测试已准备",
  "Dry-run handoff is ready": "试跑交接已就绪",
  "UI metadata has been generated": "界面元数据已生成",
  "Run a dry-run conversation using one of the prepared scenarios.":
    "使用已准备的场景执行一次试跑对话。",
  "Review the generated SKILL.md, domain rules, and UI metadata together.":
    "一并复核生成的 SKILL.md、领域规则与界面元数据。",
  "Publish only after the expert signs off on the dry-run result.":
    "仅在专家确认试跑结果后再执行发布。",
};

function localizeSkillStudioCopy(value: string | null | undefined) {
  if (!value) {
    return value ?? "";
  }

  return SKILL_STUDIO_COPY_MAP[value] ?? value;
}

export function buildSkillStudioDetailModel(
  input: BuildSkillStudioDetailModelInput,
): SkillStudioDetailModel {
  const assistant = resolveSkillStudioAssistantIdentity({
    draftAssistantMode: input.draft?.assistant_mode,
    draftAssistantLabel: input.draft?.assistant_label,
    packageAssistantMode: input.skillPackage?.assistant_mode,
    packageAssistantLabel: input.skillPackage?.assistant_label,
    stateAssistantMode: input.studioState?.assistant_mode,
    stateAssistantLabel: input.studioState?.assistant_label,
  });
  const builtinSkills = [
    ...(input.draft?.builtin_skills ?? []),
    ...(input.skillPackage?.builtin_skills ?? []),
    ...(input.studioState?.builtin_skills ?? []),
  ].filter((skill, index, all): skill is string => Boolean(skill) && all.indexOf(skill) === index);
  const readiness = buildSkillStudioReadinessSummary({
    errorCount: input.validation?.error_count ?? input.studioState?.error_count ?? 0,
    warningCount:
      input.validation?.warning_count ?? input.studioState?.warning_count ?? 0,
    validationStatus: input.validation?.status ?? input.studioState?.validation_status,
    testStatus: input.testMatrix?.status ?? input.studioState?.test_status,
    publishStatus:
      input.publishReadiness?.status ?? input.studioState?.publish_status,
  });
  const artifactGroups = groupSkillStudioArtifacts(input.studioArtifacts);
  const publishPanel = buildSkillStudioPublishPanelModel({
    skillName:
      input.studioState?.skill_name ??
      input.draft?.skill_name ??
      input.lifecycleDetail?.skill_name ??
      "draft-skill",
    lifecycleSummary: input.lifecycleDetail ?? input.lifecycleSummary,
    stateVersionNote: input.studioState?.version_note,
    stateBindings: input.studioState?.bindings,
    stateActiveRevisionId: input.studioState?.active_revision_id,
    statePublishedRevisionId: input.studioState?.published_revision_id,
  });
  const relatedSkills = buildFocusedSkillGraphItems(input.skillGraph);
  const graphOverview = buildSkillGraphOverview(input.skillGraph);
  const scenarios =
    input.testMatrix?.scenario_tests?.map((scenario) => ({
      id: scenario?.id ?? "scenario",
      scenario: scenario?.scenario ?? "Scenario",
      status: scenario?.status ?? "pending",
      expectedOutcome: scenario?.expected_outcome ?? "Outcome not declared.",
      blockingReasons: scenario?.blocking_reasons ?? [],
    })) ?? [];
  const blockedGateCount =
    input.publishReadiness?.gates?.filter((gate) => gate?.status === "blocked")
      .length ?? 0;

  return {
    assistant: {
      mode: assistant.assistantMode,
      label: assistant.assistantLabel,
      builtinSkills,
    },
    artifactGroups,
    readiness,
    define: {
      skillName:
        input.draft?.skill_name ??
        input.studioState?.skill_name ??
        input.lifecycleDetail?.skill_name ??
        "未命名技能",
      skillTitle:
        input.draft?.skill_title ??
        input.draft?.skill_name ??
        input.studioState?.skill_name ??
        "未命名技能",
      skillGoal:
        input.draft?.skill_purpose ??
        input.draft?.description ??
        "请先定义技能目标、触发条件与评审边界。",
      triggerCount: input.draft?.trigger_conditions?.length ?? 0,
      triggerConditions: input.draft?.trigger_conditions ?? [],
      constraintCount: input.draft?.expert_rules?.length ?? 0,
      constraints: input.draft?.expert_rules ?? [],
      acceptanceCriteria: input.draft?.acceptance_criteria ?? [],
      builtinSkills,
    },
    evaluate: {
      status: input.validation?.status ?? input.studioState?.validation_status ?? "draft_only",
      errorCount: input.validation?.error_count ?? input.studioState?.error_count ?? 0,
      warningCount:
        input.validation?.warning_count ?? input.studioState?.warning_count ?? 0,
      passedChecks:
        input.validation?.passed_checks?.map((item) => localizeSkillStudioCopy(item)) ??
        [],
      validationErrors: input.validation?.errors ?? [],
      validationWarnings: input.validation?.warnings ?? [],
      scenarioMatrix: {
        scenarioCount:
          input.testMatrix?.scenario_test_count ??
          input.testMatrix?.scenario_tests?.length ??
          0,
        blockedCount: input.testMatrix?.blocking_count ?? 0,
        scenarios,
      },
      dryRun: {
        ready:
          (input.testMatrix?.blocking_count ?? 0) === 0 &&
          (input.publishReadiness?.blocking_count ?? 0) === 0 &&
          readiness.blockingCount === 0,
        nextActions: input.publishReadiness?.next_actions ?? [],
      },
    },
    publish: {
      ...publishPanel,
      gateCount: input.publishReadiness?.gates?.length ?? 0,
      blockedGateCount,
      gates:
        input.publishReadiness?.gates?.map((gate) => ({
          id: gate?.id ?? "gate",
          label: localizeSkillStudioCopy(gate?.label) || "未命名门禁",
          status: gate?.status ?? "pending",
        })) ?? [],
      nextActions:
        input.publishReadiness?.next_actions?.map((item) =>
          localizeSkillStudioCopy(item),
        ) ?? [],
    },
    graph: {
      relationshipCount: relatedSkills.length,
      highImpactCount: relatedSkills.filter((item) => item.strongestScore >= 0.75)
        .length,
      upstreamCount: relatedSkills.filter((item) => item.category === "upstream")
        .length,
      downstreamCount: relatedSkills.filter((item) => item.category === "downstream")
        .length,
      overview: graphOverview,
      relatedSkills,
    },
  };
}
