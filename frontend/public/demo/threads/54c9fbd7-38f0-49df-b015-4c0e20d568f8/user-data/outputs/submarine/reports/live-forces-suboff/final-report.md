# 潜艇 CFD 阶段报告

## 中文摘要
已生成《潜艇 CFD 阶段报告》，来源阶段为 `result-reporting`。几何家族识别为 `DARPA SUBOFF`。选定案例 `darpa_suboff_bare_hull_resistance`。当前结果已经进入报告整理阶段，可直接交由 Supervisor 做质量复核。 已提取 CFD 指标，最终时间步 `200.0`，Cd `0.00329517365`。

## 运行上下文
- 来源阶段: `result-reporting`
- 任务类型: `resistance`
- 几何文件: `/mnt/user-data/uploads/live-forces-suboff.stl`
- 几何家族: `DARPA SUBOFF`
- 选定案例: `darpa_suboff_bare_hull_resistance`
- Workspace case: `/mnt/user-data/workspace/submarine/solver-dispatch/live-forces-suboff/openfoam-case`
- Run script: `/mnt/user-data/workspace/submarine/solver-dispatch/live-forces-suboff/openfoam-case/Allrun`

## 当前阶段判断
- review_status: `ready_for_supervisor`
- next_recommended_stage: `supervisor-review`
- source_report_virtual_path: `/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.md`
- supervisor_handoff_virtual_path: `当前阶段无`

## 来源证据
- `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/dispatch-summary.md`
- `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/dispatch-summary.html`
- `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/openfoam-request.json`
- `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/supervisor-handoff.json`
- `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/openfoam-run.log`
- `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/solver-results.json`
- `/mnt/user-data/outputs/submarine/solver-dispatch/live-forces-suboff/solver-results.md`
- `/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.md`
- `/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.html`
- `/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.json`

## CFD 结果指标
- 求解完成: `True`
- 最终时间步: `200.0`
- 后处理目录: `/mnt/user-data/workspace/submarine/solver-dispatch/live-forces-suboff/openfoam-case/postProcessing`
- Cd: `0.00329517365`
- Cl: `5.08813363e-06`
- Cs: `None`
- CmPitch: `None`
- 总阻力向量 (N): `[6.59034731, -6.51951e-07, 0.010176267241]`
- 总力矩向量 (N·m): `[0.005095659653, -0.011087214137, -3.29517521]`

## 参考量
- 参考长度: `4.0` m
- 参考面积: `0.16` m^2
- 来流速度: `5.0` m/s
- 流体密度: `1000.0` kg/m^3

## 本阶段产物
- `/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.md`
- `/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.html`
- `/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.json`

## 建议
- 由 Claude Code Supervisor 审阅当前阶段结论，再决定是否进入下一次 DeerFlow run。
- 若当前仅完成几何预检，请在继续前补全工况、案例和求解参数确认。
- 若当前已完成求解派发或执行，请继续补齐结果整理与后处理展示。
