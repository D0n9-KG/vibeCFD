import type { AgentThread } from "@/core/threads/types";

type SkillStudioThreadState = {
  skill_name?: string | null;
  assistant_mode?: string | null;
  validation_status?: string | null;
  test_status?: string | null;
  publish_status?: string | null;
  error_count?: number | null;
  warning_count?: number | null;
  report_virtual_path?: string | null;
  artifact_virtual_paths?: string[] | null;
};

export type SkillStudioDashboardEntry = {
  threadId: string;
  title: string;
  skillName: string;
  assistantMode: string;
  validationStatus: string;
  testStatus: string;
  publishStatus: string;
  errorCount: number;
  warningCount: number;
  artifactCount: number;
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

export function buildSkillStudioEntries(
  threads: AgentThread[],
): SkillStudioDashboardEntry[] {
  const entries: SkillStudioDashboardEntry[] = [];

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

      entries.push({
        threadId: thread.thread_id,
        title:
          typeof thread.values?.title === "string" && thread.values.title
            ? thread.values.title
            : "Untitled Skill Studio",
        skillName:
          studioState?.skill_name ??
          extractSkillSlugFromArtifacts(artifactSet),
        assistantMode:
          studioState?.assistant_mode ?? "claude-code-skill-creator",
        validationStatus: studioState?.validation_status ?? "draft_only",
        testStatus: studioState?.test_status ?? "draft_only",
        publishStatus: studioState?.publish_status ?? "draft_only",
        errorCount: studioState?.error_count ?? 0,
        warningCount: studioState?.warning_count ?? 0,
        artifactCount: artifactSet.length,
        reportVirtualPath: studioState?.report_virtual_path ?? null,
        updatedAt: thread.updated_at ?? null,
      });
  }

  return entries.sort((left, right) => {
    const leftTime = left.updatedAt ? new Date(left.updatedAt).getTime() : 0;
    const rightTime = right.updatedAt
      ? new Date(right.updatedAt).getTime()
      : 0;
    return rightTime - leftTime;
  });
}
