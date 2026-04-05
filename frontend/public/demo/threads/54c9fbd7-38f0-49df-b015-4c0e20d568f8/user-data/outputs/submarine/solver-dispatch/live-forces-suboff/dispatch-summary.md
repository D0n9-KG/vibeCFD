# 潜艇求解派发摘要

## 中文摘要
已为 `live-forces-suboff.stl` 生成 OpenFOAM 派发方案，几何家族识别为 `DARPA SUBOFF`。当前优先采用案例模板“DARPA SUBOFF Bare Hull Resistance Baseline”。已执行 sandbox 内求解派发命令。本轮请求要求立即执行。

## 求解派发状态
- 状态: `executed`
- 任务类型: `resistance`
- 几何文件: `live-forces-suboff.stl`
- 几何家族: `DARPA SUBOFF`

## 选定案例
- `darpa_suboff_bare_hull_resistance` | DARPA SUBOFF Bare Hull Resistance Baseline
- 推荐求解器: `OpenFOAM simpleFoam`
- 依据: 任务类型完全匹配；几何家族高度接近；任务描述关键词重合 3 项；输入格式可复用现有模板

## 审核契约
- review_status: `ready_for_supervisor`
- next_recommended_stage: `result-reporting`
- report_virtual_path: `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/dispatch-summary.md`

## 运行产物
- 请求清单: `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/openfoam-request.json`
- 摘要报告: `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/dispatch-summary.md`
- 执行日志: `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/openfoam-run.log`

## 命令
```bash
bash /mnt/user-data/workspace/submarine/solver-dispatch/live-forces-suboff/openfoam-case/Allrun
```

## 下一步建议
- 由 Supervisor 审核案例、命令和运行风险。
- 如果命令已执行，继续进入结果整理与报告生成。
- 如果尚未执行，可在 DeerFlow runtime 内继续补全求解参数。
