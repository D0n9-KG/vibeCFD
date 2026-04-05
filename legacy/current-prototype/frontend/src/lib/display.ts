import type { RunStatus, TaskType } from "./types";

export const TASK_TYPE_LABELS: Record<TaskType, string> = {
  pressure_distribution: "压力分布",
  resistance: "阻力分析",
  wake_field: "尾流切片",
  drift_angle_force: "斜航受力",
  near_free_surface: "近自由液面",
  self_propulsion: "自航分析"
};

export const RUN_STATUS_LABELS: Record<RunStatus, string> = {
  draft: "草稿",
  awaiting_confirmation: "待确认",
  queued: "等待执行",
  running: "执行中",
  completed: "已完成",
  cancelled: "已取消",
  failed: "失败"
};

const METRIC_LABELS: Record<string, string> = {
  drag_coefficient: "阻力系数",
  drag_newtons: "总阻力",
  pressure_peak_kpa: "峰值压力",
  pressure_mean_kpa: "平均压力",
  wake_uniformity: "尾流均匀性",
  reference_speed_ms: "参考来流速度",
  wetted_area_m2: "湿表面积",
  estimated_length_m: "估计尺度"
};

export function formatTaskType(taskType: string): string {
  return TASK_TYPE_LABELS[taskType as TaskType] ?? taskType;
}

export function formatRunStatus(status: RunStatus): string {
  return RUN_STATUS_LABELS[status];
}

export function formatMetricLabel(metricKey: string): string {
  return METRIC_LABELS[metricKey] ?? metricKey;
}

export function formatMetricValue(metricKey: string, metricValue: string | number): string {
  if (typeof metricValue !== "number") {
    return String(metricValue);
  }

  switch (metricKey) {
    case "drag_coefficient":
      return metricValue.toFixed(5);
    case "drag_newtons":
      return `${metricValue.toFixed(1)} N`;
    case "pressure_peak_kpa":
    case "pressure_mean_kpa":
      return `${metricValue.toFixed(2)} kPa`;
    case "wake_uniformity":
      return metricValue.toFixed(3);
    case "reference_speed_ms":
      return `${metricValue.toFixed(2)} m/s`;
    case "wetted_area_m2":
      return `${metricValue.toFixed(2)} m²`;
    case "estimated_length_m":
      return `${metricValue.toFixed(3)} m`;
    default:
      return metricValue.toFixed(3);
  }
}
