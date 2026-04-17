"use client";

import {
  BotIcon,
  CompassIcon,
  CpuIcon,
  PencilIcon,
  PlusIcon,
  RouteIcon,
  SearchIcon,
  SparklesIcon,
  Trash2Icon,
} from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  buildStageRoleSkillSummaries,
  filterAgents,
  filterStageRoleSkillSummaries,
} from "@/components/workspace/control-center/control-center-model";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import type { Agent } from "@/core/agents";
import {
  getAgentDisplayName,
  getAgentModelLabel,
  getAgentToolGroupLabel,
} from "@/core/agents/display";
import {
  useAgents,
  useCreateAgent,
  useDeleteAgent,
  useUpdateAgent,
} from "@/core/agents/hooks";
import { useModels } from "@/core/models/hooks";
import { useRuntimeConfig } from "@/core/runtime-config/hooks";
import { useSkillLifecycleSummaries } from "@/core/skills/hooks";

type AgentFormState = {
  name: string;
  displayName: string;
  description: string;
  model: string;
  toolGroups: string;
  soul: string;
};

const NO_MODEL_OVERRIDE = "__no_model_override__";

const EMPTY_AGENT_FORM: AgentFormState = {
  name: "",
  displayName: "",
  description: "",
  model: "",
  toolGroups: "",
  soul: "",
};

function buildAgentFormState(agent: Agent | null): AgentFormState {
  if (agent == null) {
    return EMPTY_AGENT_FORM;
  }

  return {
    name: agent.name,
    displayName: agent.display_name ?? "",
    description: agent.description ?? "",
    model: agent.model ?? "",
    toolGroups: (agent.tool_groups ?? []).join(", "),
    soul: agent.soul ?? "",
  };
}

function parseToolGroups(rawValue: string) {
  const groups = rawValue
    .split(",")
    .map((value) => value.trim())
    .filter(
      (value, index, allValues) =>
        value.length > 0 && allValues.indexOf(value) === index,
    );

  return groups.length > 0 ? groups : null;
}

export function AgentsTab() {
  const { agents, isLoading, error } = useAgents();
  const { models } = useModels();
  const { runtimeConfig, isLoading: isRuntimeConfigLoading, error: runtimeConfigError } =
    useRuntimeConfig();
  const {
    lifecycleSummaries,
    isLoading: areLifecycleSummariesLoading,
    error: lifecycleSummariesError,
  } = useSkillLifecycleSummaries();
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();
  const deleteAgent = useDeleteAgent();
  const [editorMode, setEditorMode] = useState<"create" | "edit" | null>(null);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null);
  const [formState, setFormState] = useState<AgentFormState>(EMPTY_AGENT_FORM);
  const [searchQuery, setSearchQuery] = useState("");

  const modelOptions = useMemo(
    () =>
      models.map((model) => ({
        name: model.name,
        label: model.display_name ?? model.name,
      })),
    [models],
  );

  const stageRoleSkillSummaries = useMemo(
    () =>
      buildStageRoleSkillSummaries(
        runtimeConfig?.stage_roles ?? [],
        lifecycleSummaries,
      ),
    [lifecycleSummaries, runtimeConfig?.stage_roles],
  );
  const filteredAgents = useMemo(
    () => filterAgents(agents, searchQuery),
    [agents, searchQuery],
  );
  const filteredStageRoleSkillSummaries = useMemo(
    () => filterStageRoleSkillSummaries(stageRoleSkillSummaries, searchQuery),
    [searchQuery, stageRoleSkillSummaries],
  );
  const hasSearchQuery = searchQuery.trim().length > 0;

  function openCreateDialog() {
    setEditingAgent(null);
    setFormState(EMPTY_AGENT_FORM);
    setEditorMode("create");
  }

  function openEditDialog(agent: Agent) {
    setEditingAgent(agent);
    setFormState(buildAgentFormState(agent));
    setEditorMode("edit");
  }

  function closeEditorDialog() {
    setEditorMode(null);
    setEditingAgent(null);
    setFormState(EMPTY_AGENT_FORM);
  }

  async function handleSaveAgent() {
    const payload = {
      description: formState.description.trim(),
      display_name: formState.displayName.trim() || null,
      model: formState.model || null,
      tool_groups: parseToolGroups(formState.toolGroups),
      soul: formState.soul,
    };

    try {
      if (editorMode === "create") {
        await createAgent.mutateAsync({
          name: formState.name.trim(),
          ...payload,
        });
        toast.success("已创建自定义智能体。");
      } else if (editorMode === "edit" && editingAgent != null) {
        await updateAgent.mutateAsync({
          name: editingAgent.name,
          request: payload,
        });
        toast.success("已更新自定义智能体。");
      }
      closeEditorDialog();
    } catch (saveError) {
      toast.error(
        saveError instanceof Error ? saveError.message : "保存智能体失败。",
      );
    }
  }

  async function handleDeleteAgent() {
    if (deleteTarget == null) {
      return;
    }

    try {
      await deleteAgent.mutateAsync(deleteTarget.name);
      toast.success("已删除自定义智能体。");
      setDeleteTarget(null);
    } catch (deleteError) {
      toast.error(
        deleteError instanceof Error ? deleteError.message : "删除智能体失败。",
      );
    }
  }

  if (error) {
    return (
      <WorkspaceStatePanel
        state="update-failed"
        label="智能体"
        title="读取智能体清单失败"
        description={
          error instanceof Error
            ? error.message
            : "管理中心暂时无法读取规范后端的智能体清单。"
        }
      />
    );
  }

  if (isLoading) {
    return (
      <WorkspaceStatePanel
        state="data-interrupted"
        label="智能体"
        title="正在读取智能体清单"
        description="正在同步规范后端中的主智能体、自定义智能体和历史迁移状态。"
      />
    );
  }

  return (
    <>
      <div className="grid gap-4">
        <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="workspace-kicker text-cyan-700 dark:text-cyan-300">
                智能体总览
              </div>
              <h3 className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                主智能体与自定义智能体
              </h3>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                这里管理真正由后端执行的智能体清单。内置智能体保持只读，自定义智能体可直接创建、编辑和删除。
              </p>
            </div>

            <Button onClick={openCreateDialog}>
              <PlusIcon className="mr-1.5 size-4" />
              新建自定义智能体
            </Button>
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
            <div className="grid gap-2">
              <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                搜索智能体
              </div>
              <div className="relative">
                <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                <Input
                  type="search"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="搜索智能体、模型、工具组、来源或子代理技能"
                  className="h-11 rounded-2xl border-slate-200/80 bg-white/90 pl-10 dark:border-slate-700/70 dark:bg-slate-950/60"
                />
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                直接按名称、职责说明、模型、工具组、历史本地来源，以及执行子代理绑定技能检索。
              </div>
            </div>

            <div className="flex flex-wrap gap-2 text-xs text-slate-600 dark:text-slate-300">
              <div className="rounded-full border border-slate-200/80 px-3 py-1.5 dark:border-slate-700/70">
                {hasSearchQuery
                  ? `匹配 ${filteredAgents.length} 个主/自定义智能体`
                  : `共 ${agents.length} 个主/自定义智能体`}
              </div>
              <div className="rounded-full border border-slate-200/80 px-3 py-1.5 dark:border-slate-700/70">
                {hasSearchQuery
                  ? `匹配 ${filteredStageRoleSkillSummaries.length} 个执行子代理`
                  : `共 ${stageRoleSkillSummaries.length} 个执行子代理`}
              </div>
            </div>
          </div>
        </section>

        {filteredAgents.length > 0 ? (
          filteredAgents.map((agent) => (
            <section
              key={agent.name}
              className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50"
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-base font-semibold text-slate-950 dark:text-slate-50">
                    <BotIcon className="size-4.5" />
                    {getAgentDisplayName(agent)}
                  </div>
                  <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                    {agent.description || "未填写职责说明。"}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                      {agent.is_builtin ? "内置" : "自定义"}
                    </div>
                    {agent.inventory_source === "legacy-local" ? (
                      <div className="rounded-full border border-amber-200/80 px-2.5 py-1 text-xs font-medium text-amber-700 dark:border-amber-800/70 dark:text-amber-300">
                        历史本地来源
                      </div>
                    ) : null}
                    {agent.model ? (
                      <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                        {getAgentModelLabel(agent.model)}
                      </div>
                    ) : (
                      <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                        继承主模型
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2">
                  <div className="flex flex-col items-end gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <CompassIcon className="size-3.5" />
                      {agent.is_editable ? "可编辑" : "只读保护"}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <SparklesIcon className="size-3.5" />
                      {agent.is_deletable ? "可删除" : "不可删除"}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {agent.is_editable ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditDialog(agent)}
                      >
                        <PencilIcon className="mr-1.5 size-4" />
                        编辑
                      </Button>
                    ) : null}
                    {agent.is_deletable ? (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => setDeleteTarget(agent)}
                      >
                        <Trash2Icon className="mr-1.5 size-4" />
                        删除
                      </Button>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                <div>
                  <div className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                    工具组
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(agent.tool_groups ?? []).length > 0 ? (
                      (agent.tool_groups ?? []).map((group) => (
                        <div
                          key={`${agent.name}-${group}`}
                          className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70"
                        >
                          {getAgentToolGroupLabel(group)}
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-slate-500 dark:text-slate-400">
                        未配置工具组。
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                    来源路径
                  </div>
                  <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                    {agent.source_path ?? "内置智能体没有独立目录。"}
                  </div>
                </div>
              </div>
            </section>
          ))
        ) : (
          <section className="rounded-[24px] border border-dashed border-slate-300/80 bg-slate-50/70 p-6 text-sm text-slate-600 dark:border-slate-700/70 dark:bg-slate-900/30 dark:text-slate-300">
            没有匹配到主智能体或自定义智能体，请换个关键词试试。
          </section>
        )}

        <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="workspace-kicker text-violet-700 dark:text-violet-300">
                执行子代理
              </div>
              <h3 className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                科研执行子代理与关联技能
              </h3>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                这些子代理负责潜艇 CFD 工作流中的案例理解、几何预检、求解调度、结果核验与报告整理。
                这里会同时显示它们当前使用的模型、超时时间和已绑定技能。
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-3">
            {runtimeConfigError || lifecycleSummariesError ? (
              <div className="rounded-2xl border border-amber-200/80 bg-amber-50/80 p-4 text-sm text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/20 dark:text-amber-200">
                未能完整读取子代理绑定摘要。
                {runtimeConfigError instanceof Error ? ` 运行配置：${runtimeConfigError.message}` : ""}
                {lifecycleSummariesError instanceof Error
                  ? ` 技能绑定：${lifecycleSummariesError.message}`
                  : ""}
              </div>
            ) : isRuntimeConfigLoading || areLifecycleSummariesLoading ? (
              <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 text-sm text-slate-600 dark:border-slate-800/70 dark:bg-slate-900/40 dark:text-slate-300">
                正在汇总执行子代理与技能绑定信息...
              </div>
            ) : filteredStageRoleSkillSummaries.length > 0 ? (
              filteredStageRoleSkillSummaries.map((stageRole) => (
                <div
                  key={stageRole.role_id}
                  className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-slate-50">
                        <RouteIcon className="size-4" />
                        {stageRole.display_title}
                      </div>
                      <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        {stageRole.subagent_name}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                        {stageRole.model_mode === "explicit" ? "显式锁定模型" : "继承主模型"}
                      </div>
                      <div className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70">
                        超时 {stageRole.timeout_seconds}s
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
                    <div>
                      <div className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                        当前模型
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                        <CpuIcon className="size-4 text-cyan-600 dark:text-cyan-300" />
                        {stageRole.effective_model ?? "未配置"}
                      </div>
                      <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                        来源：{stageRole.config_source}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                        关联技能
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {stageRole.assigned_skills.length > 0 ? (
                          stageRole.assigned_skills.map((skillName) => (
                            <div
                              key={`${stageRole.role_id}-${skillName}`}
                              className="rounded-full border border-slate-200/80 px-2.5 py-1 text-xs font-medium dark:border-slate-700/70"
                            >
                              {skillName}
                            </div>
                          ))
                        ) : (
                          <div className="text-sm text-slate-500 dark:text-slate-400">
                            当前没有显式绑定技能，将按默认工作流执行。
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 text-sm text-slate-600 dark:border-slate-800/70 dark:bg-slate-900/40 dark:text-slate-300">
                {hasSearchQuery
                  ? "当前关键词没有匹配到执行子代理或绑定技能。"
                  : "当前没有可展示的执行子代理配置。"}
              </div>
            )}
          </div>
        </section>
      </div>

      <Dialog
        open={editorMode !== null}
        onOpenChange={(open) => !open && closeEditorDialog()}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editorMode === "create" ? "新建自定义智能体" : "编辑自定义智能体"}
            </DialogTitle>
            <DialogDescription>
              在这里维护后端托管的智能体元数据、模型覆盖、工具组以及 SOUL 指令。
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4">
            <div className="grid gap-2">
              <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                智能体名称
              </div>
              <Input
                value={formState.name}
                disabled={editorMode === "edit"}
                placeholder="example-agent"
                onChange={(event) =>
                  setFormState((currentState) => ({
                    ...currentState,
                    name: event.target.value,
                  }))
                }
              />
            </div>

            <div className="grid gap-2 md:grid-cols-2">
              <div className="grid gap-2">
                <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                  展示名称
                </div>
                <Input
                  value={formState.displayName}
                  placeholder="用于前端展示的名称"
                  onChange={(event) =>
                    setFormState((currentState) => ({
                      ...currentState,
                      displayName: event.target.value,
                    }))
                  }
                />
              </div>

              <div className="grid gap-2">
                <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                  模型覆盖
                </div>
                <Select
                  value={formState.model || NO_MODEL_OVERRIDE}
                  onValueChange={(value) =>
                    setFormState((currentState) => ({
                      ...currentState,
                      model: value === NO_MODEL_OVERRIDE ? "" : value,
                    }))
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="继承主模型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NO_MODEL_OVERRIDE}>继承主模型</SelectItem>
                    {modelOptions.map((model) => (
                      <SelectItem key={model.name} value={model.name}>
                        {model.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-2">
              <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                职责说明
              </div>
              <Textarea
                value={formState.description}
                rows={3}
                placeholder="这个智能体负责解决什么问题？"
                onChange={(event) =>
                  setFormState((currentState) => ({
                    ...currentState,
                    description: event.target.value,
                  }))
                }
              />
            </div>

            <div className="grid gap-2">
              <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                工具组
              </div>
              <Input
                value={formState.toolGroups}
                placeholder="web, bash, file:read"
                onChange={(event) =>
                  setFormState((currentState) => ({
                    ...currentState,
                    toolGroups: event.target.value,
                  }))
                }
              />
            </div>

            <div className="grid gap-2">
              <div className="text-sm font-medium text-slate-950 dark:text-slate-50">
                SOUL.md
              </div>
              <Textarea
                value={formState.soul}
                rows={8}
                placeholder="填写人格、边界和操作指令。"
                onChange={(event) =>
                  setFormState((currentState) => ({
                    ...currentState,
                    soul: event.target.value,
                  }))
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeEditorDialog}>
              取消
            </Button>
            <Button
              onClick={() => void handleSaveAgent()}
              disabled={
                (editorMode === "create" && formState.name.trim().length === 0) ||
                createAgent.isPending ||
                updateAgent.isPending
              }
            >
              {createAgent.isPending || updateAgent.isPending
                ? "保存中..."
                : editorMode === "create"
                  ? "创建智能体"
                  : "保存更改"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除自定义智能体</DialogTitle>
            <DialogDescription>
              这会永久删除 {deleteTarget?.name ?? "当前选中的智能体"} 的配置、SOUL.md
              和相关后端托管文件。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => void handleDeleteAgent()}
              disabled={deleteAgent.isPending}
            >
              {deleteAgent.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
