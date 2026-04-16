import { localizeWorkspaceDisplayText } from "../../../core/i18n/workspace-display.ts";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineOutputDeliveryPlanItem,
  SubmarineRuntimeSnapshotPayload,
} from "../submarine-runtime-panel.contract.ts";

import type { SubmarineResearchSliceId } from "./submarine-session-model";

export type SubmarineResearchSliceFact = {
  label: string;
  value: string;
};

type BuildSliceFactsModelInput = {
  sliceId: SubmarineResearchSliceId;
  pendingApprovalCount: number;
  runtimeStatus: string | null;
  artifactCount: number;
  executionPlanCount: number;
  skillNames: readonly string[];
  requestedOutputs: readonly string[];
};

type BuildSliceContextNotesModelInput = {
  sliceId: SubmarineResearchSliceId;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  requestedOutputs: readonly string[];
  verificationRequirements: readonly string[];
  skillNames: readonly string[];
  executionPlanCount: number;
  artifactPaths: readonly string[];
};

type OutputDeliveryPlanLike =
  | readonly SubmarineOutputDeliveryPlanItem[]
  | null
  | undefined;

const INTERNAL_TOKEN_LABELS: Readonly<Record<string, string>> = {
  darpa_suboff_bare_hull_resistance: "DARPA SUBOFF 裸艇阻力基线",
  "task-intelligence": "研究判断整理中",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解准备与分发",
  "scientific-verification": "科研校验",
  "result-reporting": "结果整理阶段",
  "scientific-followup": "后续研究",
  "supervisor-review": "研究审阅",
};

const RUNTIME_STATUS_LABELS: Readonly<Record<string, string>> = {
  ready: "就绪",
  running: "运行中",
  completed: "已完成",
  blocked: "已阻塞",
  failed: "失败",
};

function looksLikeInternalCode(value: string) {
  return /^[a-z0-9]+(?:[-_][a-z0-9]+)+$/.test(value.trim());
}

function shouldGenericizeUnknownResearchToken(token: string) {
  const normalized = token.trim().toLowerCase();
  if (!looksLikeInternalCode(normalized)) {
    return false;
  }

  const separatorCount = (normalized.match(/[-_]/g) ?? []).length;
  return separatorCount >= 2;
}

export function basenameOfVirtualPath(path?: string | null): string | null {
  if (!path) {
    return null;
  }

  const normalized = path.replace(/\\/g, "/");
  const segments = normalized.split("/");
  return segments.at(-1) ?? normalized;
}

export function sanitizeSubmarineResearchCopy(text?: string | null): string | null {
  if (!text) {
    return null;
  }

  let value = text.trim();
  if (!value) {
    return null;
  }

  value = value.replace(/\/mnt\/user-data\/[^\s，。；,;）)\]]+/g, (matched) => {
    return basenameOfVirtualPath(matched) ?? "";
  });

  value = value.replace(/\b[a-z0-9]+(?:[-_][a-z0-9]+)+\b/gi, (token) => {
    const lowered = token.toLowerCase();
    if (INTERNAL_TOKEN_LABELS[lowered]) {
      return INTERNAL_TOKEN_LABELS[lowered];
    }

    return shouldGenericizeUnknownResearchToken(token) ? "相关研究项" : token;
  });

  value = localizeWorkspaceDisplayText(value);
  value = value.replace(/\s+/g, " ").trim();
  return value || null;
}

export function summarizeSubmarineResearchCopy(
  text?: string | null,
  maxLength = 96,
): string | null {
  const sanitized = sanitizeSubmarineResearchCopy(text);
  if (!sanitized) {
    return null;
  }

  if (sanitized.length <= maxLength) {
    return sanitized;
  }

  return `${sanitized.slice(0, Math.max(1, maxLength - 1)).trimEnd()}…`;
}

function ensureSentenceEnding(text: string) {
  return /[。！？…]$/.test(text) ? text : `${text}。`;
}

export function buildSubmarineResearchSnapshotSummary(
  text?: string | null,
  maxLength = 72,
): string | null {
  const sanitized = sanitizeSubmarineResearchCopy(text);
  if (!sanitized) {
    return null;
  }

  const value = sanitized
    .replace(/，确认[^。；]*?(，并(?:给出|形成)[^。；]*)/g, "$1")
    .replace(/[，；]当前先?不启动求解。?$/g, "")
    .replace(/\s+/g, " ")
    .replace(/，并并/g, "，并")
    .trim();

  const primarySentence =
    value
      .split(/[；。]/)
      .map((part) => part.trim())
      .find(Boolean) ?? value;

  const preferred = primarySentence.length <= maxLength ? primarySentence : value;
  if (preferred.length <= maxLength) {
    return ensureSentenceEnding(preferred);
  }

  return `${preferred.slice(0, Math.max(1, maxLength - 1)).trimEnd()}…`;
}

function localizeRuntimeStageLabel(stage?: string | null): string | null {
  switch (stage) {
    case "task-intelligence":
      return "研究判断整理中";
    case "geometry-preflight":
      return "几何预检";
    case "solver-dispatch":
      return "求解准备与分发";
    case "result-reporting":
      return "结果整理中";
    case "supervisor-review":
      return "研究审阅中";
    default:
      if (!stage) {
        return null;
      }

      return looksLikeInternalCode(stage) ? "阶段待同步" : stage;
  }
}

function localizeIterationModeLabel(mode?: string | null): string | null {
  switch (mode) {
    case "baseline":
      return "基线";
    case "revise_baseline":
      return "修订基线";
    case "derive_variant":
      return "派生变体";
    case "followup":
      return "后续跟进";
    default:
      if (!mode) {
        return null;
      }

      return looksLikeInternalCode(mode)
        ? "迭代模式待同步"
        : localizeWorkspaceDisplayText(mode);
  }
}

function localizeRuntimeStatusLabel(status?: string | null): string | null {
  if (!status) {
    return null;
  }

  return (
    RUNTIME_STATUS_LABELS[status] ??
    (looksLikeInternalCode(status)
      ? "状态待同步"
      : localizeWorkspaceDisplayText(status))
  );
}

function localizeRevisionSummary(value?: string | null) {
  if (!value) {
    return null;
  }

  return value.trim() === "Updated the structured CFD design brief."
    ? "已更新结构化 CFD 设计简报。"
    : value.trim();
}

function resolveDisplayedRuntimeStage(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  finalReport: SubmarineFinalReportPayload | null,
): string | null {
  if (
    typeof finalReport?.source_runtime_stage === "string" &&
    finalReport.source_runtime_stage.trim().length > 0
  ) {
    return finalReport.source_runtime_stage.trim();
  }

  return runtime?.current_stage ?? null;
}

function summarizeOutputDeliveryPlan(
  outputDeliveryPlan: OutputDeliveryPlanLike,
): string | null {
  const deliveryPlan = outputDeliveryPlan ?? [];
  if (deliveryPlan.length === 0) {
    return null;
  }

  const deliveredCount = deliveryPlan.filter(
    (item) => item?.delivery_status === "delivered",
  ).length;
  const plannedCount = deliveryPlan.filter(
    (item) =>
      item?.delivery_status === "planned" || item?.delivery_status === "pending",
  ).length;
  const blockedCount = deliveryPlan.filter(
    (item) =>
      item?.delivery_status === "not_yet_supported" ||
      item?.delivery_status === "not_available_for_this_run",
  ).length;

  return `交付计划中已交付 ${deliveredCount} 项，待完成 ${plannedCount} 项，受阻 ${blockedCount} 项。`;
}

export function buildSliceEvidenceBadgesModel({
  runtime,
  designBrief,
  finalReport,
  artifactPaths,
  requestedOutputs,
}: {
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  artifactPaths: readonly string[];
  requestedOutputs: readonly string[];
}): readonly string[] {
  const geometryName = basenameOfVirtualPath(
    runtime?.geometry_virtual_path ?? designBrief?.geometry_virtual_path,
  );
  const runtimeStageLabel = localizeRuntimeStageLabel(
    resolveDisplayedRuntimeStage(runtime, finalReport),
  );
  const contractRevision =
    finalReport?.contract_revision ??
    runtime?.contract_revision ??
    designBrief?.contract_revision ??
    null;
  const iterationModeLabel = localizeIterationModeLabel(
    finalReport?.iteration_mode ??
      runtime?.iteration_mode ??
      designBrief?.iteration_mode ??
      null,
  );
  const outputDeliveryPlan =
    finalReport?.output_delivery_plan ??
    runtime?.output_delivery_plan ??
    designBrief?.output_delivery_plan ??
    [];
  const deliveredOutputCount = outputDeliveryPlan.filter(
    (item) => item?.delivery_status === "delivered",
  ).length;
  const outputDeliveryBadge =
    outputDeliveryPlan.length > 0
      ? `交付: ${deliveredOutputCount}/${outputDeliveryPlan.length} 已交付`
      : null;

  const badges = [
    geometryName ? `几何: ${geometryName}` : null,
    localizeRuntimeStatusLabel(runtime?.runtime_status)
      ? `运行: ${localizeRuntimeStatusLabel(runtime?.runtime_status)}`
      : null,
    runtimeStageLabel ? `阶段: ${runtimeStageLabel}` : null,
    typeof contractRevision === "number" ? `合同: r${contractRevision}` : null,
    iterationModeLabel ? `迭代: ${iterationModeLabel}` : null,
    outputDeliveryBadge,
    ...requestedOutputs.slice(0, 2).map((label) => `输出: ${label}`),
    artifactPaths.length > 0 ? `${artifactPaths.length} 项产物` : null,
    finalReport?.provenance_manifest_virtual_path ? "含溯源记录" : null,
  ].filter((badge): badge is string => Boolean(badge));

  return badges.filter((badge, index, all) => all.indexOf(badge) === index);
}

function resolveProgressValue({
  pendingApprovalCount,
  runtimeStatus,
}: Pick<BuildSliceFactsModelInput, "pendingApprovalCount" | "runtimeStatus">): string {
  if (pendingApprovalCount > 0) {
    return `${pendingApprovalCount} 项待确认`;
  }
  if (runtimeStatus === "blocked") {
    return "运行已阻塞";
  }
  if (runtimeStatus === "failed") {
    return "运行已失败";
  }
  if (runtimeStatus === "running") {
    return "求解执行中";
  }
  if (runtimeStatus === "completed") {
    return "已完成本轮执行";
  }

  return "当前无阻塞项";
}

function resolveCollaborationValue({
  sliceId,
  pendingApprovalCount,
  executionPlanCount,
  skillNames,
  requestedOutputs,
}: Pick<
  BuildSliceFactsModelInput,
  "sliceId" | "pendingApprovalCount" | "executionPlanCount" | "skillNames" | "requestedOutputs"
>): string {
  switch (sliceId) {
    case "geometry-preflight":
      if (pendingApprovalCount > 0) {
        return "优先确认工况与约束";
      }
      if (requestedOutputs.length > 0) {
        return requestedOutputs.slice(0, 2).join("、");
      }
      if (skillNames.length > 0) {
        return "几何预检与工况判断";
      }
      return "按需协商推进";
    case "simulation-plan":
      if (executionPlanCount > 0) {
        return `${executionPlanCount} 项求解准备`;
      }
      if (pendingApprovalCount > 0) {
        return "待确认的求解准备";
      }
      if (skillNames.length > 0) {
        return `${skillNames.length} 个技能线索`;
      }
      if (requestedOutputs.length > 0) {
        return requestedOutputs.slice(0, 2).join("、");
      }
      return "按需协商推进";
    case "simulation-execution":
      if (skillNames.length > 0) {
        return `${skillNames.length} 个运行线索`;
      }
      return "求解与监测协同";
    case "results-and-delivery":
      if (requestedOutputs.length > 0) {
        return requestedOutputs.slice(0, 2).join("、");
      }
      return "结果审阅与交付判断";
    case "task-establishment":
    default:
      if (requestedOutputs.length > 0) {
        return requestedOutputs.slice(0, 2).join("、");
      }
      if (skillNames.length > 0) {
        return `${skillNames.length} 个技能线索`;
      }
      return "按需协商推进";
  }
}

export function buildSliceFactsModel({
  sliceId,
  pendingApprovalCount,
  runtimeStatus,
  artifactCount,
  executionPlanCount,
  skillNames,
  requestedOutputs,
}: BuildSliceFactsModelInput): readonly SubmarineResearchSliceFact[] {
  return [
    {
      label: "当前进度",
      value: resolveProgressValue({
        pendingApprovalCount,
        runtimeStatus,
      }),
    },
    {
      label: "研究产物",
      value: artifactCount > 0 ? `${artifactCount} 项研究产物` : "尚未产出研究文件",
    },
    {
      label: "协作线索",
      value: resolveCollaborationValue({
        sliceId,
        pendingApprovalCount,
        executionPlanCount,
        skillNames,
        requestedOutputs,
      }),
    },
  ];
}

export function buildSliceContextNotesModel({
  sliceId,
  runtime,
  designBrief,
  finalReport,
  requestedOutputs,
  verificationRequirements,
  skillNames,
  executionPlanCount,
  artifactPaths,
}: BuildSliceContextNotesModelInput): readonly string[] {
  const notes: string[] = [];
  const geometryName = basenameOfVirtualPath(
    runtime?.geometry_virtual_path ?? designBrief?.geometry_virtual_path,
  );
  const conciseTaskSummary = buildSubmarineResearchSnapshotSummary(
    runtime?.task_summary ?? designBrief?.summary_zh,
    72,
  );
  const contractRevision =
    finalReport?.contract_revision ??
    runtime?.contract_revision ??
    designBrief?.contract_revision ??
    null;
  const iterationModeLabel = localizeIterationModeLabel(
    finalReport?.iteration_mode ??
      runtime?.iteration_mode ??
      designBrief?.iteration_mode ??
      null,
  );
  const revisionSummary =
    localizeRevisionSummary(
      finalReport?.revision_summary ??
        runtime?.revision_summary ??
        designBrief?.revision_summary ??
        null,
    );
  const unresolvedDecisionCount =
    finalReport?.unresolved_decisions?.length ??
    runtime?.unresolved_decisions?.length ??
    designBrief?.unresolved_decisions?.length ??
    0;
  const outputDeliveryPlanSummary = summarizeOutputDeliveryPlan(
    finalReport?.output_delivery_plan ??
      runtime?.output_delivery_plan ??
      designBrief?.output_delivery_plan ??
      null,
  );

  switch (sliceId) {
    case "task-establishment":
      if (conciseTaskSummary) {
        notes.push(`当前研究目标已收敛为：${conciseTaskSummary}`);
      }
      if (geometryName) {
        notes.push(`当前研究对象已经锁定为 ${geometryName}。`);
      }
      if (requestedOutputs.length > 0) {
        notes.push(`当前最关注 ${requestedOutputs.length} 项交付输出。`);
        notes.push(`当前优先确认 ${requestedOutputs.slice(0, 2).join("、")}。`);
      }
      break;
    case "geometry-preflight":
      if (geometryName) {
        notes.push(`几何预检围绕 ${geometryName} 的可计算性和前置判断展开。`);
      }
      if ((designBrief?.open_questions?.length ?? 0) > 0) {
        notes.push(`仍有 ${designBrief?.open_questions?.length ?? 0} 个开放问题等待研究者确认。`);
      }
      if ((designBrief?.requested_outputs?.length ?? 0) > 0) {
        notes.push(`当前预检也在为 ${designBrief?.requested_outputs?.length ?? 0} 项目标输出做准备。`);
      }
      break;
    case "simulation-plan":
      if (executionPlanCount > 0) {
        notes.push(`主智能体已经整理出 ${executionPlanCount} 项求解准备。`);
      }
      if (typeof contractRevision === "number" || iterationModeLabel) {
        notes.push(
          `当前任务合同已更新到 ${typeof contractRevision === "number" ? `r${contractRevision}` : "最新版本"}${iterationModeLabel ? `（${iterationModeLabel}）` : ""}。`,
        );
      }
      if (revisionSummary) {
        notes.push(
          summarizeSubmarineResearchCopy(revisionSummary, 88) ?? revisionSummary,
        );
      }
      if (unresolvedDecisionCount > 0) {
        notes.push(`当前仍有 ${unresolvedDecisionCount} 项未决研究决策需要跟进。`);
      }
      if (outputDeliveryPlanSummary) {
        notes.push(outputDeliveryPlanSummary);
      }
      if (skillNames.length > 0) {
        const localizedSkillNames = skillNames
          .map((skill) => localizeWorkspaceDisplayText(skill))
          .map((skill) => (looksLikeInternalCode(skill) ? "相关技能" : skill))
          .filter((skill, index, all) => skill.length > 0 && all.indexOf(skill) === index);
        notes.push(`当前切片会参考 ${localizedSkillNames.join("、")} 等技能信号。`);
      }
      if (verificationRequirements.length > 0) {
        notes.push(`验证要求包括 ${verificationRequirements.slice(0, 2).join("、")}。`);
      }
      break;
    case "simulation-execution":
      if (runtime?.runtime_status) {
        notes.push(
          `运行状态目前为 ${localizeRuntimeStatusLabel(runtime.runtime_status) ?? runtime.runtime_status}。`,
        );
      }
      if (runtime?.current_stage) {
        notes.push(
          `执行阶段位于 ${localizeRuntimeStageLabel(runtime.current_stage) ?? runtime.current_stage}。`,
        );
      }
      const timelineEntries = runtime?.activity_timeline ?? [];
      if (timelineEntries.length > 0) {
        notes.push(
          timelineEntries
            .slice(0, 2)
            .map(
              (entry) =>
                summarizeSubmarineResearchCopy(
                  entry.summary ?? entry.title ?? entry.actor ?? "",
                  72,
                ) ?? "",
            )
            .filter(Boolean)
            .join("；"),
        );
      }
      break;
    case "results-and-delivery":
      if (finalReport?.summary_zh) {
        notes.push(
          summarizeSubmarineResearchCopy(finalReport.summary_zh, 96) ?? finalReport.summary_zh,
        );
      }
      const conclusionSections = finalReport?.conclusion_sections ?? [];
      if (conclusionSections.length > 0) {
        notes.push(
          conclusionSections
            .slice(0, 2)
            .map(
              (section) =>
                summarizeSubmarineResearchCopy(
                  section.summary_zh ?? section.title_zh ?? "",
                  64,
                ) ?? "",
            )
            .filter(Boolean)
            .join("；"),
        );
      }
      if (artifactPaths.length > 0) {
        notes.push(`当前已经沉淀 ${artifactPaths.length} 项与该阶段相关的研究产物。`);
      }
      break;
  }

  return notes.filter((note, index, all) => Boolean(note) && all.indexOf(note) === index);
}
