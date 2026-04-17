import type { Agent } from "@/core/agents/types";
import type { RuntimeConfigStageRoleSummary } from "@/core/runtime-config/api";
import type { SkillLifecycleSummary } from "@/core/skills/api";
import type { ThreadOrphanSummary } from "@/core/thread-management/api";

export type StageRoleSkillSummary = RuntimeConfigStageRoleSummary & {
  assigned_skills: string[];
};

export type OrphanAuditSummary = {
  orphan_count: number;
  occupied_orphan_count: number;
  zero_byte_orphan_count: number;
  total_files: number;
  total_bytes: number;
  largest_orphan_bytes: number;
};

function normalizeSkillName(value: string | null | undefined) {
  return typeof value === "string" ? value.trim() : "";
}

function uniqueSorted(values: Iterable<string>) {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right));
}

export function buildStageRoleSkillSummaries(
  stageRoles: RuntimeConfigStageRoleSummary[],
  lifecycleSummaries: Array<
    Pick<SkillLifecycleSummary, "skill_name" | "enabled" | "binding_targets">
  >,
): StageRoleSkillSummary[] {
  const skillsByRoleId = new Map<string, Set<string>>();

  for (const lifecycleSummary of lifecycleSummaries) {
    if (lifecycleSummary.enabled === false) {
      continue;
    }

    for (const bindingTarget of lifecycleSummary.binding_targets ?? []) {
      const roleId =
        typeof bindingTarget?.role_id === "string"
          ? bindingTarget.role_id.trim()
          : "";
      if (!roleId) {
        continue;
      }

      const targetSkillNames = (bindingTarget.target_skills ?? [])
        .map((skillName) => normalizeSkillName(skillName))
        .filter((skillName) => skillName.length > 0);
      const resolvedSkillNames =
        targetSkillNames.length > 0
          ? targetSkillNames
          : [normalizeSkillName(lifecycleSummary.skill_name)];

      if (!skillsByRoleId.has(roleId)) {
        skillsByRoleId.set(roleId, new Set<string>());
      }

      const roleSkillNames = skillsByRoleId.get(roleId)!;
      for (const skillName of resolvedSkillNames) {
        if (skillName.length > 0) {
          roleSkillNames.add(skillName);
        }
      }
    }
  }

  return stageRoles.map((stageRole) => ({
    ...stageRole,
    assigned_skills: uniqueSorted(skillsByRoleId.get(stageRole.role_id) ?? []),
  }));
}

function normalizeSearchQuery(value: string) {
  return value.trim().toLowerCase();
}

export function filterAgents(agents: Agent[], search: string) {
  const searchQuery = normalizeSearchQuery(search);
  if (!searchQuery) {
    return agents;
  }

  return agents.filter((agent) => {
    const keywords = [
      agent.name,
      agent.display_name ?? "",
      agent.description ?? "",
      agent.model ?? "",
      agent.inventory_source ?? "",
      agent.source_path ?? "",
      ...(agent.tool_groups ?? []),
      agent.is_builtin ? "内置" : "自定义",
      agent.inventory_source === "legacy-local" ? "历史本地" : "规范后端",
    ]
      .join(" ")
      .toLowerCase();

    return keywords.includes(searchQuery);
  });
}

export function filterStageRoleSkillSummaries(
  stageRoles: StageRoleSkillSummary[],
  search: string,
) {
  const searchQuery = normalizeSearchQuery(search);
  if (!searchQuery) {
    return stageRoles;
  }

  return stageRoles.filter((stageRole) => {
    const keywords = [
      stageRole.role_id,
      stageRole.subagent_name,
      stageRole.display_title,
      stageRole.effective_model ?? "",
      stageRole.config_source,
      stageRole.model_mode === "explicit" ? "显式模型" : "继承主模型",
      ...stageRole.assigned_skills,
    ]
      .join(" ")
      .toLowerCase();

    return keywords.includes(searchQuery);
  });
}

export function buildOrphanAuditSummary(
  orphans: ThreadOrphanSummary[],
): OrphanAuditSummary {
  return orphans.reduce<OrphanAuditSummary>(
    (summary, orphan) => ({
      orphan_count: summary.orphan_count + 1,
      occupied_orphan_count:
        summary.occupied_orphan_count + (orphan.total_bytes > 0 ? 1 : 0),
      zero_byte_orphan_count:
        summary.zero_byte_orphan_count + (orphan.total_bytes === 0 ? 1 : 0),
      total_files: summary.total_files + orphan.total_files,
      total_bytes: summary.total_bytes + orphan.total_bytes,
      largest_orphan_bytes: Math.max(
        summary.largest_orphan_bytes,
        orphan.total_bytes,
      ),
    }),
    {
      orphan_count: 0,
      occupied_orphan_count: 0,
      zero_byte_orphan_count: 0,
      total_files: 0,
      total_bytes: 0,
      largest_orphan_bytes: 0,
    },
  );
}

export function filterAndSortOrphans(
  orphans: ThreadOrphanSummary[],
  options: {
    search?: string;
    includeZeroByte?: boolean;
  } = {},
) {
  const searchQuery = options.search?.trim().toLowerCase() ?? "";
  const includeZeroByte = options.includeZeroByte ?? true;

  return orphans
    .filter((orphan) => {
      if (!includeZeroByte && orphan.total_bytes === 0) {
        return false;
      }

      if (!searchQuery) {
        return true;
      }

      return (
        orphan.thread_id.toLowerCase().includes(searchQuery) ||
        orphan.thread_dir.toLowerCase().includes(searchQuery)
      );
    })
    .sort((left, right) => {
      if (left.total_bytes !== right.total_bytes) {
        return right.total_bytes - left.total_bytes;
      }
      if (left.total_files !== right.total_files) {
        return right.total_files - left.total_files;
      }
      return left.thread_id.localeCompare(right.thread_id);
    });
}
