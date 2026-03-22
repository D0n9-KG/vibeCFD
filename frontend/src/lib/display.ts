import type { RunStatus, TaskType } from "./types";

export const TASK_TYPE_LABELS: Record<TaskType, string> = {
  pressure_distribution: "压力分布",
  resistance: "阻力分析",
  wake_field: "尾流切片",
  drift_angle_force: "斜航受力",
  near_free_surface: "自由液面",
  self_propulsion: "自航分析"
};

export const RUN_STATUS_LABELS: Record<RunStatus, string> = {
  draft: "草稿",
  awaiting_confirmation: "待确认",
  queued: "排队中",
  running: "运行中",
  completed: "已完成",
  cancelled: "已取消",
  failed: "失败"
};

export function formatTaskType(taskType: string): string {
  return TASK_TYPE_LABELS[taskType as TaskType] ?? taskType;
}

export function formatRunStatus(status: RunStatus): string {
  return RUN_STATUS_LABELS[status];
}
