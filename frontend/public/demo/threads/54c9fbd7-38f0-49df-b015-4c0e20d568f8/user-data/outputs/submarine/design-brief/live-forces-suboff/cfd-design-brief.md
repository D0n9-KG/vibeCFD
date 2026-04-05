# 潜艇 CFD 设计简报

## 中文摘要
Claude Code 已将当前对话整理为第一版潜艇 CFD 方案：先基于 DARPA SUBOFF 裸艇进行阻力基线计算，确认单工况稳健跑通后，再决定是否扩展更多工况。

## 任务定义
- 任务目标：`基于上传的 DARPA SUBOFF 几何完成裸艇阻力基线计算，并交付可审阅的结果报告。`
- 任务类型：`resistance`
- 确认状态：`draft`
- 几何路径：`/mnt/user-data/uploads/live-forces-suboff.stl`
- 几何家族线索：`DARPA SUBOFF`
- 选定案例：`darpa_suboff_bare_hull_resistance`

## 计算要求
- inlet_velocity_mps: `5.0`
- fluid_density_kg_m3: `1000.0`
- kinematic_viscosity_m2ps: `1e-06`
- end_time_seconds: `200.0`
- delta_t_seconds: `1.0`
- write_interval_steps: `50`

## 预期交付物
- 阻力系数 Cd
- 总阻力与力矩摘要
- 中文结果报告

## 用户约束
- 先做单工况稳健基线，不做参数扫描
- 输出结果必须进入 DeerFlow artifact 体系

## 待确认项
- 是否需要追加 3 m/s 和 7 m/s 对比工况

## 执行分工
- `claude-code-supervisor` / Claude Code：与用户持续确认任务目标、交付物和边界条件。
- `task-intelligence` / DeerFlow：确定潜艇案例模板和执行路径。
- `geometry-preflight` / DeerFlow：完成几何检查与前处理就绪性判断。
- `solver-dispatch` / DeerFlow：准备并执行 OpenFOAM 基线求解。
- `result-reporting` / DeerFlow：整理结果数据与中文报告。
