"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import { useRuntimeConfig } from "@/core/runtime-config/hooks";
import {
  useEnableSkill,
  useRollbackSkillRevision,
  useSkillFileContent,
  useSkillFiles,
  useSkillGraph,
  useSkillLifecycle,
  useSkillLifecycleSummaries,
  useSkills,
} from "@/core/skills/hooks";

type FileRow = {
  name: string;
  path: string;
  depth: number;
  node_type: "file" | "directory";
};

function flattenSkillFileTree(
  nodes: Array<{
    name: string;
    path: string;
    node_type: "file" | "directory";
    children?: unknown;
  }>,
  depth = 0,
): FileRow[] {
  const rows: FileRow[] = [];
  for (const node of nodes) {
    rows.push({
      name: node.name,
      path: node.path,
      depth,
      node_type: node.node_type,
    });

    if (
      node.node_type === "directory" &&
      Array.isArray(node.children) &&
      node.children.length > 0
    ) {
      rows.push(
        ...flattenSkillFileTree(
          node.children as Array<{
            name: string;
            path: string;
            node_type: "file" | "directory";
            children?: unknown;
          }>,
          depth + 1,
        ),
      );
    }
  }
  return rows;
}

function formatBindingMode(mode: string | null | undefined) {
  if (mode === "explicit") {
    return "显式绑定";
  }
  if (!mode) {
    return "未说明";
  }
  return mode;
}

function describeBindingTargetSkills(
  targetSkills: string[] | null | undefined,
  currentSkillName: string,
) {
  const skillNames = (targetSkills ?? [])
    .map((skillName) => skillName.trim())
    .filter(
      (skillName, index, allSkillNames) =>
        skillName.length > 0 && allSkillNames.indexOf(skillName) === index,
    );

  if (skillNames.length === 0) {
    return "当前技能";
  }

  return skillNames
    .map((skillName) =>
      skillName === currentSkillName ? "当前技能" : skillName,
    )
    .join("、");
}

function formatSkillCategory(category: string) {
  return category === "custom" ? "自定义" : "公共";
}

export function SkillsTab() {
  const { skills, isLoading, error } = useSkills();
  const { lifecycleSummaries } = useSkillLifecycleSummaries();
  const { runtimeConfig } = useRuntimeConfig();
  const enableSkill = useEnableSkill();
  const rollbackSkillRevision = useRollbackSkillRevision();
  const [selectedSkillName, setSelectedSkillName] = useState<string | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredSkills = useMemo(() => {
    const normalizedSearchQuery = searchQuery.trim().toLowerCase();
    if (normalizedSearchQuery.length === 0) {
      return skills;
    }

    return skills.filter((skill) =>
      skill.name.toLowerCase().includes(normalizedSearchQuery),
    );
  }, [searchQuery, skills]);

  const resolvedSkillName =
    filteredSkills.find((skill) => skill.name === selectedSkillName)?.name ??
    filteredSkills[0]?.name ??
    null;
  const selectedSkill =
    filteredSkills.find((skill) => skill.name === resolvedSkillName) ?? null;
  const selectedLifecycleSummary =
    lifecycleSummaries.find((summary) => summary.skill_name === resolvedSkillName) ??
    null;

  useEffect(() => {
    setSelectedFilePath(null);
  }, [resolvedSkillName]);

  const lifecycleDetailQuery = useSkillLifecycle({
    skillName: resolvedSkillName ?? undefined,
    enabled: Boolean(resolvedSkillName),
  });
  const skillGraphQuery = useSkillGraph({
    skillName: resolvedSkillName ?? undefined,
    enabled: Boolean(resolvedSkillName),
  });
  const skillFilesQuery = useSkillFiles({
    skillName: resolvedSkillName ?? undefined,
    enabled: Boolean(resolvedSkillName),
  });

  const fileRows = useMemo(
    () => flattenSkillFileTree(skillFilesQuery.data?.entries ?? []),
    [skillFilesQuery.data?.entries],
  );

  const resolvedFilePath =
    selectedFilePath ??
    fileRows.find((row) => row.node_type === "file")?.path ??
    null;

  const fileContentQuery = useSkillFileContent({
    skillName: resolvedSkillName ?? undefined,
    path: resolvedFilePath,
    enabled: Boolean(resolvedSkillName) && Boolean(resolvedFilePath),
  });

  const boundStageRoles = useMemo(() => {
    if (!selectedLifecycleSummary || !runtimeConfig) {
      return [];
    }

    const roleIdSet = new Set(
      (selectedLifecycleSummary.binding_targets ?? [])
        .map((binding) => binding.role_id?.trim())
        .filter((roleId): roleId is string => Boolean(roleId)),
    );

    return runtimeConfig.stage_roles.filter((role) => roleIdSet.has(role.role_id));
  }, [runtimeConfig, selectedLifecycleSummary]);

  async function handleToggleSkillEnabled() {
    if (!resolvedSkillName || !selectedSkill) {
      return;
    }

    try {
      await enableSkill.mutateAsync({
        skillName: resolvedSkillName,
        enabled: !selectedSkill.enabled,
      });
      toast.success(!selectedSkill.enabled ? "技能已启用。" : "技能已停用。");
    } catch (toggleError) {
      toast.error(
        toggleError instanceof Error
          ? toggleError.message
          : "更新技能状态失败。",
      );
    }
  }

  async function handleRollbackSkill() {
    const rollbackTargetId =
      lifecycleDetailQuery.data?.rollback_target_id ??
      selectedLifecycleSummary?.rollback_target_id;
    if (!resolvedSkillName || !rollbackTargetId) {
      return;
    }

    try {
      await rollbackSkillRevision.mutateAsync({
        skillName: resolvedSkillName,
        revision_id: rollbackTargetId,
      });
      toast.success("技能版本已回滚。");
    } catch (rollbackError) {
      toast.error(
        rollbackError instanceof Error
          ? rollbackError.message
          : "回滚技能版本失败。",
      );
    }
  }

  if (error) {
    return (
      <WorkspaceStatePanel
        state="update-failed"
        label="技能"
        title="读取技能目录失败"
        description={
          error instanceof Error
            ? error.message
            : "管理中心暂时无法读取当前技能目录。"
        }
      />
    );
  }

  if (isLoading) {
    return (
      <WorkspaceStatePanel
        state="data-interrupted"
        label="技能"
        title="正在读取技能目录"
        description="正在同步技能目录、生命周期信息、绑定关系和文件预览。"
      />
    );
  }

  if (skills.length === 0) {
    return (
      <WorkspaceStatePanel
        state="first-run"
        label="技能"
        title="当前没有可用技能"
        description="安装公共技能或发布自定义技能后，这里会显示目录、生命周期、绑定关系和文件预览。"
      />
    );
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1fr)_minmax(0,1.1fr)]">
      <section className="flex min-h-0 self-start flex-col rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
        <div className="workspace-kicker text-sky-700 dark:text-sky-300">
          技能目录
        </div>
        <div className="mt-4">
          <Input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="搜索技能名称"
            className="h-11 rounded-2xl border-slate-200/80 bg-white/90 dark:border-slate-700/70 dark:bg-slate-950/60"
          />
          <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            按技能名称过滤当前已安装 skill。
          </div>
        </div>
        <div className="mt-4 grid max-h-[calc(100vh-12rem)] overflow-y-auto gap-3 pr-1">
          {filteredSkills.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300/80 bg-slate-50/70 p-4 text-sm text-slate-600 dark:border-slate-700/70 dark:bg-slate-900/30 dark:text-slate-300">
              没有匹配到的技能，请换个名称再试。
            </div>
          ) : (
            filteredSkills.map((skill) => {
            const isSelected = skill.name === resolvedSkillName;
            const lifecycleSummary =
              lifecycleSummaries.find((item) => item.skill_name === skill.name) ??
              null;
            return (
              <button
                key={skill.name}
                type="button"
                onClick={() => {
                  setSelectedSkillName(skill.name);
                  setSelectedFilePath(null);
                }}
                className={`rounded-2xl border p-4 text-left transition ${
                  isSelected
                    ? "border-sky-300 bg-sky-50/80 dark:border-sky-700 dark:bg-sky-950/30"
                    : "border-slate-200/70 bg-slate-50/70 dark:border-slate-800/70 dark:bg-slate-900/40"
                }`}
              >
                <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                  {skill.name}
                </div>
                <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {skill.description}
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                    {formatSkillCategory(skill.category)}
                  </div>
                  <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                    {skill.enabled ? "已启用" : "已停用"}
                  </div>
                  {lifecycleSummary ? (
                    <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                      {lifecycleSummary.revision_count} 个版本
                    </div>
                  ) : null}
                </div>
              </button>
            );
            })
          )}
        </div>
      </section>

      <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
        <div className="workspace-kicker text-emerald-700 dark:text-emerald-300">
          生命周期与分配
        </div>
        {resolvedSkillName && selectedSkill ? (
          <div className="mt-4 space-y-4">
            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                    {resolvedSkillName}
                  </div>
                  <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                    草稿状态：
                    {lifecycleDetailQuery.data?.draft_status ??
                      selectedLifecycleSummary?.draft_status ??
                      "unknown"}
                  </div>
                  <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                    当前活动版本：
                    {lifecycleDetailQuery.data?.active_revision_id ??
                      selectedLifecycleSummary?.active_revision_id ??
                      "none"}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={selectedSkill.enabled ? "outline" : "default"}
                    size="sm"
                    onClick={() => void handleToggleSkillEnabled()}
                    disabled={enableSkill.isPending}
                  >
                    {enableSkill.isPending
                      ? "更新中..."
                      : selectedSkill.enabled
                        ? "停用技能"
                        : "启用技能"}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void handleRollbackSkill()}
                    disabled={
                      rollbackSkillRevision.isPending ||
                      !(
                        lifecycleDetailQuery.data?.rollback_target_id ??
                        selectedLifecycleSummary?.rollback_target_id
                      )
                    }
                  >
                    {rollbackSkillRevision.isPending ? "回滚中..." : "回滚版本"}
                  </Button>
                </div>
              </div>

              <div className="mt-4 grid gap-2 text-sm text-slate-700 dark:text-slate-300">
                <div>
                  <span className="font-medium text-slate-950 dark:text-slate-50">
                    发布路径：
                  </span>
                  {lifecycleDetailQuery.data?.published_path ??
                    selectedLifecycleSummary?.published_path ??
                    "尚未发布"}
                </div>
                <div>
                  <span className="font-medium text-slate-950 dark:text-slate-50">
                    上次发布时间：
                  </span>
                  {lifecycleDetailQuery.data?.last_published_at ??
                    selectedLifecycleSummary?.last_published_at ??
                    "未知"}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                当前分配
              </div>
              <div className="mt-3 grid gap-3">
                {(selectedLifecycleSummary?.binding_targets ?? []).length > 0 ? (
                  (selectedLifecycleSummary?.binding_targets ?? []).map((binding) => {
                    const stageRole = runtimeConfig?.stage_roles.find(
                      (role) => role.role_id === binding.role_id,
                    );
                    return (
                      <div
                        key={`${binding.role_id}-${binding.mode}`}
                        className="rounded-xl border border-slate-200/70 bg-white/80 p-3 dark:border-slate-700/70 dark:bg-slate-950/35"
                      >
                        <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                          {stageRole?.display_title ?? binding.role_id}
                        </div>
                        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          {stageRole?.subagent_name ?? "未找到对应执行子代理"} ·{" "}
                          {formatBindingMode(binding.mode)}
                        </div>
                        <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                          目标技能：{describeBindingTargetSkills(binding.target_skills, resolvedSkillName)}
                        </div>
                        {stageRole ? (
                          <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                            当前执行子代理模型：{stageRole.effective_model ?? "未配置"}
                          </div>
                        ) : null}
                      </div>
                    );
                  })
                ) : (
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    当前没有显式绑定目标。这个技能仍可被主智能体按需引用，但没有固定分配给某个执行子代理。
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                执行子代理视角
              </div>
              <div className="mt-3 grid gap-3">
                {boundStageRoles.length > 0 ? (
                  boundStageRoles.map((stageRole) => (
                    <div
                      key={stageRole.role_id}
                      className="rounded-xl border border-slate-200/70 bg-white/80 p-3 dark:border-slate-700/70 dark:bg-slate-950/35"
                    >
                      <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                        {stageRole.display_title}
                      </div>
                      <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        {stageRole.subagent_name}
                      </div>
                      <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                        当前模型：{stageRole.effective_model ?? "未配置"} · 超时 {stageRole.timeout_seconds}s
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    当前没有执行子代理被显式分配到这个技能。
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                已安装文件
              </div>
              <div className="mt-3 max-h-[26rem] overflow-auto">
                {skillFilesQuery.isLoading ? (
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    正在读取文件树...
                  </div>
                ) : (
                  <div className="grid gap-1">
                    {fileRows.map((row) => (
                      <button
                        key={row.path}
                        type="button"
                        disabled={row.node_type !== "file"}
                        onClick={() => setSelectedFilePath(row.path)}
                        className={`rounded-xl px-3 py-2 text-left text-sm ${
                          row.node_type === "file"
                            ? "hover:bg-slate-100 dark:hover:bg-slate-800/70"
                            : "cursor-default text-slate-500 dark:text-slate-400"
                        } ${
                          resolvedFilePath === row.path
                            ? "bg-sky-50 dark:bg-sky-950/30"
                            : ""
                        }`}
                        style={{ paddingLeft: `${12 + row.depth * 18}px` }}
                      >
                        {row.node_type === "directory" ? "目录" : "文件"} {row.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <WorkspaceStatePanel
            state="data-interrupted"
            label="技能"
            title="尚未选择技能"
            description="先在左侧技能目录中选择一个技能，再查看它的分配关系和文件内容。"
          />
        )}
      </section>

      <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
        <div className="workspace-kicker text-violet-700 dark:text-violet-300">
          预览
        </div>
        {resolvedSkillName ? (
          <div className="mt-4 space-y-4">
            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                图谱摘要
              </div>
              <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                相关技能：{skillGraphQuery.data?.focus?.related_skill_count ?? 0}
              </div>
              <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                当前分配到的执行子代理：{boundStageRoles.length}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                {resolvedFilePath ?? "选择一个文件以预览内容"}
              </div>
              <div className="mt-3 max-h-[34rem] overflow-auto rounded-2xl border border-slate-200/70 bg-white/90 p-4 text-sm dark:border-slate-700/70 dark:bg-slate-950/40">
                {fileContentQuery.isLoading ? (
                  <div className="text-slate-500 dark:text-slate-400">
                    正在读取文件内容...
                  </div>
                ) : fileContentQuery.data?.preview_type === "binary" ? (
                  <div className="text-slate-500 dark:text-slate-400">
                    这个文件被识别为二进制文件，因此这里只展示元信息，不直接输出原始字节内容。
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap break-words text-slate-700 dark:text-slate-200">
                    {fileContentQuery.data?.content ?? "没有可预览的文本内容。"}
                  </pre>
                )}
              </div>
            </div>
          </div>
        ) : (
          <WorkspaceStatePanel
            state="data-interrupted"
            label="技能"
            title="尚未选择技能"
            description="先选择一个技能，再查看图谱摘要和文件内容预览。"
          />
        )}
      </section>
    </div>
  );
}
