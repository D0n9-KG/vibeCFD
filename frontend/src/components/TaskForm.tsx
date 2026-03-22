import { useState } from "react";

import type { TaskFormInput } from "../lib/api";
import type { TaskType } from "../lib/types";

const TASK_TYPE_OPTIONS: Array<{ value: TaskType; label: string; hint: string }> = [
  { value: "pressure_distribution", label: "压力分布", hint: "输出表面压力云图与关键部位特征。" },
  { value: "resistance", label: "阻力分析", hint: "关注阻力数值、阻力系数和基础对照。" },
  { value: "wake_field", label: "尾流切片", hint: "关注尾流截面与主流场的切片结果。" },
  { value: "near_free_surface", label: "自由液面", hint: "保留为扩展项，适合演示未来能力。" }
];

const GEOMETRY_OPTIONS = ["DARPA SUBOFF", "Joubert BB2", "Type 209", "未指定"];

interface TaskFormProps {
  disabled?: boolean;
  onSubmit: (payload: TaskFormInput) => Promise<void>;
}

export function TaskForm({ disabled = false, onSubmit }: TaskFormProps) {
  const [taskDescription, setTaskDescription] = useState("分析这个潜艇外形在深潜工况下的压力分布和阻力结果。");
  const [taskType, setTaskType] = useState<TaskType>("pressure_distribution");
  const [geometryFamilyHint, setGeometryFamilyHint] = useState("DARPA SUBOFF");
  const [operatingNotes, setOperatingNotes] = useState("深潜稳态工况，默认使用不可压稳态流动假设。");
  const [geometryFile, setGeometryFile] = useState<File | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      taskDescription,
      taskType,
      geometryFamilyHint: geometryFamilyHint === "未指定" ? "" : geometryFamilyHint,
      operatingNotes,
      geometryFile
    });
  }

  const selectedType = TASK_TYPE_OPTIONS.find((option) => option.value === taskType);

  return (
    <form className="sidebar-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <div>
          <p className="section-kicker">输入</p>
          <h2>任务输入</h2>
        </div>
        <span className="panel-tag">新建</span>
      </div>

      <p className="panel-description">提交新 run 后，系统会先检索案例，再生成推荐流程。</p>

      <label className="form-field">
        <span>任务说明</span>
        <textarea
          aria-label="任务说明"
          value={taskDescription}
          onChange={(event) => setTaskDescription(event.target.value)}
          rows={3}
          disabled={disabled}
        />
      </label>

      <div className="compact-grid">
        <label className="form-field">
          <span>任务类型</span>
          <select
            aria-label="任务类型"
            value={taskType}
            onChange={(event) => setTaskType(event.target.value as TaskType)}
            disabled={disabled}
          >
            {TASK_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <small>{selectedType?.hint}</small>
        </label>

        <label className="form-field">
          <span>几何家族</span>
          <select
            aria-label="几何家族"
            value={geometryFamilyHint}
            onChange={(event) => setGeometryFamilyHint(event.target.value)}
            disabled={disabled}
          >
            {GEOMETRY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="form-field">
        <span>工况说明</span>
        <textarea
          aria-label="工况说明"
          value={operatingNotes}
          onChange={(event) => setOperatingNotes(event.target.value)}
          rows={3}
          disabled={disabled}
        />
      </label>

      <label className="form-field">
        <span>几何文件</span>
        <input
          aria-label="几何文件"
          type="file"
          accept=".stl,.x_t,.step,.stp"
          onChange={(event) => setGeometryFile(event.target.files?.[0] ?? null)}
          disabled={disabled}
        />
        <small>{geometryFile ? geometryFile.name : "支持 STL / x_t / STEP。"}</small>
      </label>

      <button className="primary-action" type="submit" disabled={disabled}>
        {disabled ? "检索中" : "检索案例"}
      </button>
    </form>
  );
}
