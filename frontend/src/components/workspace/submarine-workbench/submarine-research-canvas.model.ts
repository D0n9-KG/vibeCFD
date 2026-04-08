import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
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

const INTERNAL_TOKEN_LABELS: Readonly<Record<string, string>> = {
  darpa_suboff_bare_hull_resistance: "DARPA SUBOFF 裸艇阻力基线",
};

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

  value = value.replace(/\b[a-z0-9]+(?:_[a-z0-9]+){2,}\b/gi, (token) => {
    const lowered = token.toLowerCase();
    return INTERNAL_TOKEN_LABELS[lowered] ?? token.replace(/_/g, " ");
  });

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
    case "solver-dispatch":
      return "求解准备与分发";
    case "result-reporting":
      return "结果整理中";
    case "supervisor-review":
      return "研究审阅中";
    default:
      return stage ?? null;
  }
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
  const runtimeStageLabel = localizeRuntimeStageLabel(runtime?.current_stage);

  const badges = [
    geometryName ? `几何: ${geometryName}` : null,
    runtime?.runtime_status ? `运行: ${runtime.runtime_status}` : null,
    runtimeStageLabel ? `阶段: ${runtimeStageLabel}` : null,
    ...requestedOutputs.slice(0, 2).map((label) => `输出: ${label}`),
    artifactPaths.length > 0 ? `${artifactPaths.length} 项产物` : null,
    finalReport?.provenance_manifest_virtual_path ? "含 provenance 记录" : null,
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
      if (skillNames.length > 0) {
        notes.push(`当前切片会参考 ${skillNames.join("、")} 等技能信号。`);
      }
      if (verificationRequirements.length > 0) {
        notes.push(`验证要求包括 ${verificationRequirements.slice(0, 2).join("、")}。`);
      }
      break;
    case "simulation-execution":
      if (runtime?.runtime_status) {
        notes.push(`运行状态目前为 ${runtime.runtime_status}。`);
      }
      if (runtime?.current_stage) {
        notes.push(`执行阶段位于 ${runtime.current_stage}。`);
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
