import type { AgentThread } from "@/core/threads/types";
import {
  localizeThreadDisplayTitle,
  localizeWorkspaceDisplayText,
} from "../../core/i18n/workspace-display.ts";

import {
  DEFAULT_SKILL_STUDIO_AGENT,
  labelOfSkillStudioAgentName,
  normalizeSkillStudioAgentLabel,
} from "./skill-studio-agent-options.ts";
import type { SkillStudioLifecycleSummary } from "./skill-studio-workbench.utils.ts";

type SkillStudioThreadState = {
  skill_name?: string | null;
  skill_asset_id?: string | null;
  assistant_mode?: string | null;
  assistant_label?: string | null;
  validation_status?: string | null;
  test_status?: string | null;
  publish_status?: string | null;
  error_count?: number | null;
  warning_count?: number | null;
  lifecycle_virtual_path?: string | null;
  active_revision_id?: string | null;
  published_revision_id?: string | null;
  version_note?: string | null;
  bindings?: Array<{
    role_id?: string | null;
    mode?: string | null;
    target_skills?: string[] | null;
  }> | null;
  report_virtual_path?: string | null;
  artifact_virtual_paths?: string[] | null;
};

export type SkillStudioLifecycleBinding = {
  roleId: string;
  mode: string;
  targetSkills: string[];
};

export type SkillStudioDashboardEntry = {
  threadId: string;
  title: string;
  skillName: string;
  skillAssetId: string;
  assistantMode: string;
  assistantLabel: string;
  validationStatus: string;
  testStatus: string;
  publishStatus: string;
  errorCount: number;
  warningCount: number;
  artifactCount: number;
  lifecycleVirtualPath: string | null;
  activeRevisionId: string | null;
  publishedRevisionId: string | null;
  versionNote: string;
  bindings: SkillStudioLifecycleBinding[];
  reportVirtualPath: string | null;
  updatedAt: string | null;
};

function extractSkillSlugFromArtifacts(artifacts: string[]) {
  const matched = artifacts.find((artifact) =>
    artifact.includes("/submarine/skill-studio/"),
  );
  if (!matched) {
    return "draft-only";
  }

  const parts = matched.split("/submarine/skill-studio/")[1]?.split("/") ?? [];
  return parts[0] ?? "draft-only";
}

function normalizeSkillStudioBindings(
  bindings: SkillStudioThreadState["bindings"],
): SkillStudioLifecycleBinding[] {
  if (!Array.isArray(bindings)) {
    return [];
  }

  return bindings
    .map((binding) => {
      const roleId =
        typeof binding?.role_id === "string" ? binding.role_id : null;
      const mode = typeof binding?.mode === "string" ? binding.mode : null;
      if (!roleId || !mode) {
        return null;
      }

      return {
        roleId,
        mode,
        targetSkills: Array.isArray(binding?.target_skills)
          ? binding.target_skills.filter(
              (skill): skill is string => typeof skill === "string",
            )
          : [],
      };
    })
    .filter((binding): binding is SkillStudioLifecycleBinding => binding !== null);
}

function normalizeLifecycleSummaryBindings(
  bindings: SkillStudioLifecycleSummary["binding_targets"] | undefined,
): SkillStudioLifecycleBinding[] {
  if (!Array.isArray(bindings)) {
    return [];
  }

  return bindings
    .map((binding) => {
      const roleId =
        typeof binding?.role_id === "string" ? binding.role_id : null;
      const mode = typeof binding?.mode === "string" ? binding.mode : null;
      if (!roleId || !mode) {
        return null;
      }

      return {
        roleId,
        mode,
        targetSkills: Array.isArray(binding?.target_skills)
          ? binding.target_skills.filter(
              (skill): skill is string => typeof skill === "string",
            )
          : [],
      };
    })
    .filter((binding): binding is SkillStudioLifecycleBinding => binding !== null);
}

export function buildSkillStudioEntries(
  threads: AgentThread[],
  untitledLabel = "未命名技能工作台",
  lifecycleSummaries: SkillStudioLifecycleSummary[] = [],
): SkillStudioDashboardEntry[] {
  const entries: SkillStudioDashboardEntry[] = [];
  const lifecycleBySkillName = new Map(
    lifecycleSummaries.map((summary) => [summary.skill_name, summary]),
  );

  for (const thread of threads) {
    const threadArtifacts = Array.isArray(thread.values?.artifacts)
      ? thread.values.artifacts.filter(
          (artifact): artifact is string =>
            typeof artifact === "string" &&
            artifact.includes("/submarine/skill-studio/"),
        )
      : [];
    const studioState = thread.values?.submarine_skill_studio as
      | SkillStudioThreadState
      | undefined;
    const stateArtifacts = Array.isArray(studioState?.artifact_virtual_paths)
      ? studioState.artifact_virtual_paths.filter(
          (artifact): artifact is string => typeof artifact === "string",
        )
      : [];
    const artifactSet = [...threadArtifacts, ...stateArtifacts].filter(
      (artifact, index, list) => list.indexOf(artifact) === index,
    );

    if (!studioState && artifactSet.length === 0) {
      continue;
    }

    const assistantMode =
      studioState?.assistant_mode ?? DEFAULT_SKILL_STUDIO_AGENT;
    const fallbackSkillAssetId =
      studioState?.skill_name ?? extractSkillSlugFromArtifacts(artifactSet);
    const lifecycleSummary = lifecycleBySkillName.get(fallbackSkillAssetId);

    entries.push({
      threadId: thread.thread_id,
      title:
        typeof thread.values?.title === "string" && thread.values.title
          ? thread.values.title === "Untitled"
            ? untitledLabel
            : localizeThreadDisplayTitle(thread.values.title)
          : untitledLabel,
      skillName: localizeWorkspaceDisplayText(
        studioState?.skill_name ?? extractSkillSlugFromArtifacts(artifactSet),
      ),
      skillAssetId: studioState?.skill_asset_id ?? fallbackSkillAssetId,
      assistantMode,
      assistantLabel: normalizeSkillStudioAgentLabel(
        studioState?.assistant_label ??
          labelOfSkillStudioAgentName(assistantMode),
        assistantMode,
      ),
      validationStatus: studioState?.validation_status ?? "draft_only",
      testStatus: studioState?.test_status ?? "draft_only",
      publishStatus: studioState?.publish_status ?? "draft_only",
      errorCount: studioState?.error_count ?? 0,
      warningCount: studioState?.warning_count ?? 0,
      artifactCount: artifactSet.length,
      lifecycleVirtualPath: studioState?.lifecycle_virtual_path ?? null,
      activeRevisionId:
        lifecycleSummary?.active_revision_id ??
        studioState?.active_revision_id ??
        null,
      publishedRevisionId:
        lifecycleSummary?.published_revision_id ??
        studioState?.published_revision_id ??
        null,
      versionNote:
        lifecycleSummary?.version_note ?? studioState?.version_note ?? "",
      bindings:
        lifecycleSummary && lifecycleSummary.binding_targets.length > 0
          ? normalizeLifecycleSummaryBindings(lifecycleSummary.binding_targets)
          : normalizeSkillStudioBindings(studioState?.bindings),
      reportVirtualPath: studioState?.report_virtual_path ?? null,
      updatedAt: thread.updated_at ?? null,
    });
  }

  return entries.sort((left, right) => {
    const leftTime = left.updatedAt ? new Date(left.updatedAt).getTime() : 0;
    const rightTime = right.updatedAt ? new Date(right.updatedAt).getTime() : 0;
    return rightTime - leftTime;
  });
}
