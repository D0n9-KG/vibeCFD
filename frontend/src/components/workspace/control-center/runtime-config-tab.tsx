"use client";

import {
  BotIcon,
  PencilLineIcon,
  PlusIcon,
  RouteIcon,
  SaveIcon,
  SearchIcon,
  Trash2Icon,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
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
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { WorkspaceStatePanel } from "@/components/workspace/workspace-state-panel";
import type {
  RuntimeConfigSummary,
  RuntimeModelCreateRequest,
  RuntimeModelSummary,
  RuntimeModelUpdateRequest,
} from "@/core/runtime-config/api";
import {
  useCreateRuntimeModel,
  useDeleteRuntimeModel,
  useRuntimeConfig,
  useRuntimeModels,
  useUpdateRuntimeConfig,
  useUpdateRuntimeModel,
} from "@/core/runtime-config/hooks";

type ProviderKey = RuntimeModelCreateRequest["provider_key"];

type StageRoleDraft = {
  model_mode: "inherit" | "explicit";
  model_name: string | null;
};

type RoutingDraft = {
  leadDefaultModel: string | null;
  stageRoles: Record<string, StageRoleDraft>;
};

type EditorMode = "inspect" | "create" | "edit";

type ModelFormState = {
  name: string;
  display_name: string;
  description: string;
  provider_key: ProviderKey;
  model: string;
  base_url: string;
  api_key: string;
  clear_api_key: boolean;
  supports_thinking: boolean;
  supports_reasoning_effort: boolean;
  supports_vision: boolean;
};

const CONFIG_DEFAULT_SENTINEL = "__config_default__";
const MODEL_SELECT_SENTINEL = "__select_model__";

const PROVIDER_OPTIONS: Array<{ value: ProviderKey; label: string }> = [
  { value: "openai", label: "OpenAI API" },
  { value: "openai-compatible", label: "OpenAI-Compatible API" },
  { value: "anthropic", label: "Anthropic API" },
];

const EMPTY_MODEL_FORM: ModelFormState = {
  name: "",
  display_name: "",
  description: "",
  provider_key: "openai",
  model: "",
  base_url: "",
  api_key: "",
  clear_api_key: false,
  supports_thinking: false,
  supports_reasoning_effort: false,
  supports_vision: false,
};

function buildRoutingDraft(runtimeConfig: RuntimeConfigSummary): RoutingDraft {
  return {
    leadDefaultModel: runtimeConfig.lead_agent.is_overridden
      ? runtimeConfig.lead_agent.default_model
      : null,
    stageRoles: Object.fromEntries(
      runtimeConfig.stage_roles.map((role) => [
        role.role_id,
        {
          model_mode: role.model_mode,
          model_name:
            role.model_mode === "explicit" ? role.effective_model ?? null : null,
        },
      ]),
    ),
  };
}

function buildModelFormState(model: RuntimeModelSummary | null): ModelFormState {
  if (model == null) {
    return EMPTY_MODEL_FORM;
  }

  return {
    name: model.name,
    display_name: model.display_name ?? "",
    description: model.description ?? "",
    provider_key: model.provider_key,
    model: model.model,
    base_url: model.base_url ?? "",
    api_key: "",
    clear_api_key: false,
    supports_thinking: model.supports_thinking,
    supports_reasoning_effort: model.supports_reasoning_effort,
    supports_vision: model.supports_vision,
  };
}

function normalizeOptionalText(value: string) {
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}

function resolveModelLabel(
  models: RuntimeModelSummary[],
  modelName: string | null | undefined,
) {
  if (!modelName) {
    return "未配置";
  }

  const matched = models.find((model) => model.name === modelName);
  return matched?.display_name ?? matched?.name ?? modelName;
}

function filterRuntimeModels(models: RuntimeModelSummary[], query: string) {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return models;
  }

  return models.filter((model) =>
    [
      model.name,
      model.display_name ?? "",
      model.description ?? "",
      model.model,
      model.provider_label,
      model.provider_key,
      model.base_url ?? "",
      model.source,
    ]
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuery),
  );
}

function routeOptionLabel(model: RuntimeModelSummary) {
  const label = model.display_name ?? model.name;
  return `${label} · ${model.source === "runtime" ? "自定义" : "内置"}`;
}

export function RuntimeConfigTab() {
  const { runtimeConfig, isLoading, error } = useRuntimeConfig();
  const {
    runtimeModels,
    isLoading: areRuntimeModelsLoading,
    error: runtimeModelsError,
  } = useRuntimeModels();
  const updateRuntimeConfig = useUpdateRuntimeConfig();
  const createRuntimeModel = useCreateRuntimeModel();
  const updateRuntimeModel = useUpdateRuntimeModel();
  const deleteRuntimeModel = useDeleteRuntimeModel();

  const [routingDraft, setRoutingDraft] = useState<RoutingDraft | null>(null);
  const [selectedModelName, setSelectedModelName] = useState<string | null>(null);
  const [editorMode, setEditorMode] = useState<EditorMode>("inspect");
  const [modelForm, setModelForm] = useState<ModelFormState>(EMPTY_MODEL_FORM);
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    if (runtimeConfig) {
      setRoutingDraft(buildRoutingDraft(runtimeConfig));
    }
  }, [runtimeConfig]);

  const filteredModels = useMemo(
    () => filterRuntimeModels(runtimeModels, searchQuery),
    [runtimeModels, searchQuery],
  );
  const selectedModel = useMemo(
    () =>
      selectedModelName == null
        ? null
        : runtimeModels.find((model) => model.name === selectedModelName) ?? null,
    [runtimeModels, selectedModelName],
  );
  const routingBaselineDraft = useMemo(
    () => (runtimeConfig ? buildRoutingDraft(runtimeConfig) : null),
    [runtimeConfig],
  );
  const routingDirty = useMemo(() => {
    if (routingDraft == null || routingBaselineDraft == null) {
      return false;
    }

    return JSON.stringify(routingDraft) !== JSON.stringify(routingBaselineDraft);
  }, [routingBaselineDraft, routingDraft]);

  useEffect(() => {
    if (editorMode === "create") {
      return;
    }

    if (runtimeModels.length === 0) {
      setSelectedModelName(null);
      setEditorMode("inspect");
      setModelForm(EMPTY_MODEL_FORM);
      return;
    }

    if (selectedModelName == null) {
      setSelectedModelName(runtimeModels[0]?.name ?? null);
    }
  }, [editorMode, runtimeModels, selectedModelName]);

  useEffect(() => {
    if (editorMode === "create") {
      return;
    }

    if (selectedModel == null) {
      setEditorMode("inspect");
      setModelForm(EMPTY_MODEL_FORM);
      return;
    }

    setEditorMode(selectedModel.is_editable ? "edit" : "inspect");
    setModelForm(buildModelFormState(selectedModel));
  }, [editorMode, selectedModel]);

  function beginCreateModel() {
    setEditorMode("create");
    setSelectedModelName(null);
    setModelForm(EMPTY_MODEL_FORM);
  }

  async function handleSaveRouting() {
    if (runtimeConfig == null || routingDraft == null) {
      return;
    }

    try {
      await updateRuntimeConfig.mutateAsync({
        lead_agent: {
          default_model: routingDraft.leadDefaultModel,
        },
        stage_roles: runtimeConfig.stage_roles.map((role) => {
          const roleDraft = routingDraft.stageRoles[role.role_id] ?? {
            model_mode: "inherit" as const,
            model_name: null,
          };

          return {
            role_id: role.role_id,
            model_mode: roleDraft.model_mode,
            model_name:
              roleDraft.model_mode === "explicit" ? roleDraft.model_name : null,
          };
        }),
      });
      toast.success("已保存模型路由规则。");
    } catch (saveError) {
      toast.error(
        saveError instanceof Error ? saveError.message : "保存模型路由失败。",
      );
    }
  }

  async function handleSaveModel() {
    if (!modelForm.model.trim()) {
      toast.error("请先填写底层模型标识。");
      return;
    }

    if (editorMode === "create" && !modelForm.name.trim()) {
      toast.error("请先填写模型名称。");
      return;
    }

    const createPayload: RuntimeModelCreateRequest = {
      name: modelForm.name.trim(),
      display_name: normalizeOptionalText(modelForm.display_name),
      description: normalizeOptionalText(modelForm.description),
      provider_key: modelForm.provider_key,
      model: modelForm.model.trim(),
      base_url: normalizeOptionalText(modelForm.base_url),
      api_key: normalizeOptionalText(modelForm.api_key),
      supports_thinking: modelForm.supports_thinking,
      supports_reasoning_effort: modelForm.supports_reasoning_effort,
      supports_vision: modelForm.supports_vision,
    };

    try {
      if (editorMode === "create") {
        const createdModel = await createRuntimeModel.mutateAsync(createPayload);
        setSelectedModelName(createdModel.name);
        setEditorMode("edit");
        setModelForm(buildModelFormState(createdModel));
        toast.success("已新增运行时模型。");
        return;
      }

      if (!selectedModel?.is_editable) {
        return;
      }

      const updatedModel = await updateRuntimeModel.mutateAsync({
        modelName: selectedModel.name,
        request: {
          display_name: createPayload.display_name,
          description: createPayload.description,
          provider_key: createPayload.provider_key,
          model: createPayload.model,
          base_url: createPayload.base_url,
          api_key: normalizeOptionalText(modelForm.api_key),
          clear_api_key: modelForm.clear_api_key,
          supports_thinking: createPayload.supports_thinking,
          supports_reasoning_effort: createPayload.supports_reasoning_effort,
          supports_vision: createPayload.supports_vision,
        } satisfies RuntimeModelUpdateRequest,
      });
      setSelectedModelName(updatedModel.name);
      setModelForm(buildModelFormState(updatedModel));
      toast.success("已更新运行时模型。");
    } catch (saveError) {
      toast.error(
        saveError instanceof Error ? saveError.message : "保存运行时模型失败。",
      );
    }
  }

  async function handleDeleteModel() {
    if (!selectedModel?.is_editable) {
      return;
    }

    try {
      await deleteRuntimeModel.mutateAsync(selectedModel.name);
      setDeleteDialogOpen(false);
      setSelectedModelName(null);
      setEditorMode("inspect");
      setModelForm(EMPTY_MODEL_FORM);
      toast.success("已删除运行时模型。");
    } catch (deleteError) {
      toast.error(
        deleteError instanceof Error ? deleteError.message : "删除运行时模型失败。",
      );
    }
  }

  if (error || runtimeModelsError) {
    const resolvedError = error ?? runtimeModelsError;
    return (
      <WorkspaceStatePanel
        state="update-failed"
        label="模型中心"
        title="读取模型中心失败"
        description={
          resolvedError instanceof Error
            ? resolvedError.message
            : "管理中心暂时无法读取模型注册表或模型路由。"
        }
      />
    );
  }

  if (
    isLoading ||
    areRuntimeModelsLoading ||
    runtimeConfig == null ||
    routingDraft == null
  ) {
    return (
      <WorkspaceStatePanel
        state="data-interrupted"
        label="模型中心"
        title="正在读取模型中心"
        description="正在同步内置模型、自定义模型、主代理默认模型与阶段子代理路由。"
      />
    );
  }

  const configFileDefaultModel = runtimeModels.find(
    (model) => model.name === runtimeConfig.models[0]?.name,
  );
  const routingOptions = runtimeModels.map((model) => ({
    value: model.name,
    label: routeOptionLabel(model),
    isAvailable: model.is_available,
  }));
  const currentModelSavePending =
    createRuntimeModel.isPending || updateRuntimeModel.isPending;

  return (
    <>
      <div className="grid gap-5 2xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="workspace-kicker text-cyan-700 dark:text-cyan-300">
                模型注册表
              </div>
              <h3 className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                模型目录与密钥
              </h3>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                内置模型保持只读；新增运行时模型后，你可以直接在前端填写
                `base_url`、`api_key` 和能力标签。
              </p>
            </div>
            <Button onClick={beginCreateModel}>
              <PlusIcon className="mr-1.5 size-4" />
              新建运行时模型
            </Button>
          </div>

          <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(280px,0.78fr)_minmax(0,1.22fr)]">
            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
              <div className="relative">
                <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                <Input
                  type="search"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="搜索模型名、provider、底层 model"
                  className="h-11 rounded-2xl border-slate-200/80 bg-white/90 pl-10 dark:border-slate-700/70 dark:bg-slate-950/60"
                />
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <div className="metric-chip">共 {runtimeModels.length} 个模型</div>
                <div className="metric-chip">
                  {runtimeModels.filter((model) => model.source === "runtime").length} 个自定义
                </div>
              </div>

              <div className="mt-4 grid max-h-[calc(100vh-16rem)] gap-3 overflow-y-auto pr-1">
                {filteredModels.map((model) => (
                  <button
                    key={model.name}
                    type="button"
                    onClick={() => {
                      setSelectedModelName(model.name);
                      setEditorMode(model.is_editable ? "edit" : "inspect");
                    }}
                    className={`rounded-2xl border p-4 text-left transition ${
                      editorMode !== "create" && selectedModel?.name === model.name
                        ? "border-cyan-300 bg-cyan-50/80 dark:border-cyan-700 dark:bg-cyan-950/30"
                        : "border-slate-200/70 bg-white/85 dark:border-slate-700/70 dark:bg-slate-950/35"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-slate-950 dark:text-slate-50">
                          {model.display_name ?? model.name}
                        </div>
                        <div className="mt-1 truncate text-xs text-slate-500 dark:text-slate-400">
                          {model.name}
                        </div>
                      </div>
                      <Badge variant={model.is_available ? "secondary" : "outline"}>
                        {model.is_available ? "可用" : "未就绪"}
                      </Badge>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant="outline">
                        {model.source === "runtime" ? "自定义" : "内置"}
                      </Badge>
                      <Badge variant="outline">{model.provider_label}</Badge>
                      {model.has_api_key ? (
                        <Badge variant="outline">已保存密钥</Badge>
                      ) : null}
                    </div>
                    <div className="mt-3 text-sm text-slate-600 dark:text-slate-300">
                      {model.model}
                    </div>
                  </button>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-5 dark:border-slate-800/70 dark:bg-slate-900/40">
              {editorMode === "inspect" && selectedModel != null ? (
                <div className="space-y-4">
                  <div>
                    <div className="workspace-kicker text-emerald-700 dark:text-emerald-300">
                      当前模型
                    </div>
                    <h4 className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                      {selectedModel.display_name ?? selectedModel.name}
                    </h4>
                    <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      这是来自 `config.yaml` 的内置模型，前端不会直接改写。如果你需要自定义 endpoint 或独立密钥，请新建一个运行时模型。
                    </p>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-slate-200/70 bg-white/85 p-4 dark:border-slate-700/70 dark:bg-slate-950/35">
                      <div className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                        Provider
                      </div>
                      <div className="mt-2 text-sm font-semibold text-slate-950 dark:text-slate-50">
                        {selectedModel.provider_label}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-slate-200/70 bg-white/85 p-4 dark:border-slate-700/70 dark:bg-slate-950/35">
                      <div className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                        底层模型
                      </div>
                      <div className="mt-2 text-sm font-semibold text-slate-950 dark:text-slate-50">
                        {selectedModel.model}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">
                      {selectedModel.supports_thinking ? "支持 thinking" : "不支持 thinking"}
                    </Badge>
                    <Badge variant="outline">
                      {selectedModel.supports_reasoning_effort
                        ? "支持 reasoning effort"
                        : "不支持 reasoning effort"}
                    </Badge>
                    <Badge variant="outline">
                      {selectedModel.supports_vision ? "支持视觉输入" : "纯文本"}
                    </Badge>
                  </div>

                  <Button variant="outline" onClick={beginCreateModel}>
                    <PlusIcon className="mr-1.5 size-4" />
                    新建运行时模型
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="workspace-kicker text-emerald-700 dark:text-emerald-300">
                        {editorMode === "create" ? "新建模型" : "编辑模型"}
                      </div>
                      <h4 className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                        {editorMode === "create"
                          ? "新增运行时模型"
                          : selectedModel?.display_name ?? selectedModel?.name ?? "运行时模型"}
                      </h4>
                    </div>
                    {editorMode === "edit" && selectedModel?.is_editable ? (
                      <Button
                        variant="outline"
                        onClick={() => setDeleteDialogOpen(true)}
                      >
                        <Trash2Icon className="mr-1.5 size-4" />
                        删除模型
                      </Button>
                    ) : null}
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <Input
                      value={modelForm.name}
                      onChange={(event) =>
                        setModelForm((currentForm) => ({
                          ...currentForm,
                          name: event.target.value,
                        }))
                      }
                      placeholder="模型名称，例如 lab-openai"
                      disabled={editorMode !== "create"}
                    />
                    <Input
                      value={modelForm.display_name}
                      onChange={(event) =>
                        setModelForm((currentForm) => ({
                          ...currentForm,
                          display_name: event.target.value,
                        }))
                      }
                      placeholder="显示名称"
                    />
                    <Select
                      value={modelForm.provider_key}
                      onValueChange={(value: ProviderKey) =>
                        setModelForm((currentForm) => ({
                          ...currentForm,
                          provider_key: value,
                        }))
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="选择 provider" />
                      </SelectTrigger>
                      <SelectContent>
                        {PROVIDER_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Input
                      value={modelForm.model}
                      onChange={(event) =>
                        setModelForm((currentForm) => ({
                          ...currentForm,
                          model: event.target.value,
                        }))
                      }
                      placeholder="底层模型标识"
                    />
                    <div className="md:col-span-2">
                      <Input
                        value={modelForm.base_url}
                        onChange={(event) =>
                          setModelForm((currentForm) => ({
                            ...currentForm,
                            base_url: event.target.value,
                          }))
                        }
                        placeholder="base_url，留空则使用 provider 默认地址"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Input
                        type="password"
                        value={modelForm.api_key}
                        onChange={(event) =>
                          setModelForm((currentForm) => ({
                            ...currentForm,
                            api_key: event.target.value,
                            clear_api_key: false,
                          }))
                        }
                        placeholder={
                          editorMode === "edit"
                            ? "留空表示保持现有 api_key 不变"
                            : "可选：创建时直接保存 api_key"
                        }
                        disabled={modelForm.clear_api_key}
                      />
                    </div>
                    {editorMode === "edit" ? (
                      <label className="md:col-span-2 flex items-center justify-between gap-4 rounded-2xl border border-slate-200/70 bg-white/85 px-4 py-3 text-sm dark:border-slate-700/70 dark:bg-slate-950/35">
                        <div>
                          <div className="font-medium text-slate-950 dark:text-slate-50">
                            clear_api_key
                          </div>
                          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            打开后会在保存时清除后端已存的密钥。
                          </div>
                        </div>
                        <Switch
                          checked={modelForm.clear_api_key}
                          onCheckedChange={(checked) =>
                            setModelForm((currentForm) => ({
                              ...currentForm,
                              clear_api_key: checked,
                              api_key: checked ? "" : currentForm.api_key,
                            }))
                          }
                        />
                      </label>
                    ) : null}
                    <div className="md:col-span-2">
                      <Textarea
                        value={modelForm.description}
                        onChange={(event) =>
                          setModelForm((currentForm) => ({
                            ...currentForm,
                            description: event.target.value,
                          }))
                        }
                        placeholder="备注说明"
                        rows={4}
                      />
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-3">
                    <label className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200/70 bg-white/85 px-4 py-3 text-sm dark:border-slate-700/70 dark:bg-slate-950/35">
                      <span>supports_thinking</span>
                      <Switch
                        checked={modelForm.supports_thinking}
                        onCheckedChange={(checked) =>
                          setModelForm((currentForm) => ({
                            ...currentForm,
                            supports_thinking: checked,
                          }))
                        }
                      />
                    </label>
                    <label className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200/70 bg-white/85 px-4 py-3 text-sm dark:border-slate-700/70 dark:bg-slate-950/35">
                      <span>supports_reasoning_effort</span>
                      <Switch
                        checked={modelForm.supports_reasoning_effort}
                        onCheckedChange={(checked) =>
                          setModelForm((currentForm) => ({
                            ...currentForm,
                            supports_reasoning_effort: checked,
                          }))
                        }
                      />
                    </label>
                    <label className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200/70 bg-white/85 px-4 py-3 text-sm dark:border-slate-700/70 dark:bg-slate-950/35">
                      <span>supports_vision</span>
                      <Switch
                        checked={modelForm.supports_vision}
                        onCheckedChange={(checked) =>
                          setModelForm((currentForm) => ({
                            ...currentForm,
                            supports_vision: checked,
                          }))
                        }
                      />
                    </label>
                  </div>

                  <div className="flex flex-wrap justify-end gap-2">
                    {editorMode === "edit" ? (
                      <Button variant="outline" onClick={beginCreateModel}>
                        <PencilLineIcon className="mr-1.5 size-4" />
                        改为新建
                      </Button>
                    ) : null}
                    <Button
                      onClick={() => void handleSaveModel()}
                      disabled={currentModelSavePending}
                    >
                      <SaveIcon className="mr-1.5 size-4" />
                      {currentModelSavePending
                        ? "保存中..."
                        : editorMode === "create"
                          ? "创建模型"
                          : "保存修改"}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm shadow-slate-950/5 dark:border-slate-800/80 dark:bg-slate-950/50">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="workspace-kicker text-emerald-700 dark:text-emerald-300">
                路由规则
              </div>
              <h3 className="mt-2 text-lg font-semibold text-slate-950 dark:text-slate-50">
                主代理默认模型与阶段路由
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                线程若未显式切模，就会回落到这里的规则。
              </p>
            </div>
            <Button
              onClick={() => void handleSaveRouting()}
              disabled={!routingDirty || updateRuntimeConfig.isPending}
            >
              <SaveIcon className="mr-1.5 size-4" />
              {updateRuntimeConfig.isPending ? "保存中..." : "保存路由"}
            </Button>
          </div>

          <div className="mt-5 rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-slate-50">
              <BotIcon className="size-4" />
              主代理默认模型
            </div>
            <div className="mt-3">
              <Select
                value={routingDraft.leadDefaultModel ?? CONFIG_DEFAULT_SENTINEL}
                onValueChange={(value) =>
                  setRoutingDraft((currentDraft) =>
                    currentDraft == null
                      ? currentDraft
                      : {
                          ...currentDraft,
                          leadDefaultModel:
                            value === CONFIG_DEFAULT_SENTINEL ? null : value,
                        },
                  )
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="主代理默认模型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={CONFIG_DEFAULT_SENTINEL}>
                    跟随 config.yaml 基线（
                    {configFileDefaultModel
                      ? routeOptionLabel(configFileDefaultModel)
                      : "未配置"}
                    ）
                  </SelectItem>
                  {routingOptions.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                      {model.isAvailable ? "" : " (未就绪)"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="mt-4 grid gap-4">
            {runtimeConfig.stage_roles.map((role) => {
              const roleDraft = routingDraft.stageRoles[role.role_id] ?? {
                model_mode: "inherit" as const,
                model_name: null,
              };

              return (
                <div
                  key={role.role_id}
                  className="rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4 dark:border-slate-800/70 dark:bg-slate-900/40"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-slate-50">
                        <RouteIcon className="size-4" />
                        {role.display_title || role.role_id}
                      </div>
                      <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        当前生效：{resolveModelLabel(runtimeModels, role.effective_model)}
                      </div>
                    </div>
                    <Badge variant="outline">
                      {roleDraft.model_mode === "inherit" ? "继承主代理" : "显式锁定"}
                    </Badge>
                  </div>

                  <div className="mt-4 grid gap-3 lg:grid-cols-[220px_minmax(0,1fr)]">
                    <Select
                      value={roleDraft.model_mode}
                      onValueChange={(value: "inherit" | "explicit") =>
                        setRoutingDraft((currentDraft) =>
                          currentDraft == null
                            ? currentDraft
                            : {
                                ...currentDraft,
                                stageRoles: {
                                  ...currentDraft.stageRoles,
                                  [role.role_id]: {
                                    model_mode: value,
                                    model_name:
                                      value === "explicit"
                                        ? currentDraft.stageRoles[role.role_id]
                                            ?.model_name ??
                                          runtimeModels[0]?.name ??
                                          null
                                        : null,
                                  },
                                },
                              },
                        )
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="路由模式" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="inherit">继承主代理</SelectItem>
                        <SelectItem value="explicit">显式模型</SelectItem>
                      </SelectContent>
                    </Select>

                    <Select
                      value={roleDraft.model_name ?? MODEL_SELECT_SENTINEL}
                      disabled={roleDraft.model_mode !== "explicit"}
                      onValueChange={(value) =>
                        setRoutingDraft((currentDraft) =>
                          currentDraft == null
                            ? currentDraft
                            : {
                                ...currentDraft,
                                stageRoles: {
                                  ...currentDraft.stageRoles,
                                  [role.role_id]: {
                                    model_mode: "explicit",
                                    model_name: value,
                                  },
                                },
                              },
                        )
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="选择显式模型" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={MODEL_SELECT_SENTINEL} disabled>
                          请选择模型
                        </SelectItem>
                        {routingOptions.map((model) => (
                          <SelectItem key={model.value} value={model.value}>
                            {model.label}
                            {model.isAvailable ? "" : " (未就绪)"}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除运行时模型</DialogTitle>
            <DialogDescription>
              {selectedModel?.display_name ?? selectedModel?.name ?? "该模型"}
              会从运行时注册表移除，保存的 api_key 也会一并删除。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => void handleDeleteModel()}
              disabled={deleteRuntimeModel.isPending}
            >
              {deleteRuntimeModel.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
