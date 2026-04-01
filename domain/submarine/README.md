# 潜艇领域资产

这里存放的是从旧原型中保留下来、后续仍然需要继续利用的潜艇领域资产。

当前第一批保留内容包括：

- [cases/index.json](/C:/Users/D0n9/Desktop/颠覆性大赛/domain/submarine/cases/index.json)
  潜艇案例元数据，后续将被整理成 DeerFlow 领域 skill 可直接使用的案例库输入。
- [skills/index.json](/C:/Users/D0n9/Desktop/颠覆性大赛/domain/submarine/skills/index.json)
  旧原型中的 skill 元数据，后续会按 DeerFlow 的 skill 体系重新组织。

这个目录的目标不是继续保存旧框架实现，而是只保留真正值得进入新主线的领域资产。旧原型里的实现细节、前端页面、轻量执行器和历史脚本均已归档到 [legacy/current-prototype](/C:/Users/D0n9/Desktop/颠覆性大赛/legacy/current-prototype)。

## 当前规范与后续方向

当前主线规范见：
[2026-03-25-claude-code-supervisor-submarine-cfd-design.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/archive/superpowers/specs/2026-03-25-claude-code-supervisor-submarine-cfd-design.md)

在这套设计里，`domain/submarine/` 的职责是持续提供潜艇领域事实、案例、skill 元数据和后续模板资产；真正的运行时编排仍然留在 DeerFlow 内部，由 `thread / upload / artifact / subagent / memory / sandbox / MCP` 体系承接。

## 当前如何进入 DeerFlow 主线

`domain/submarine/` 现在已经开始作为 DeerFlow 主线的领域源数据层被消费：

- `backend/packages/harness/deerflow/domain/submarine/assets.py`
  负责从这里加载案例和 skill 源数据
- `backend/packages/harness/deerflow/domain/submarine/library.py`
  负责把 `cases/index.json` 和 `skills/index.json` 归一化为运行时可用的领域输入
- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
  负责潜艇几何检查、案例候选匹配和 artifact 结果输出
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  负责把几何与案例上下文整理为 DeerFlow-native 的 OpenFOAM 派发清单与结果摘要
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  负责基于 thread 内的 `submarine_runtime` 生成阶段报告 artifacts，并为 Claude Code Supervisor 准备 handoff
- `skills/public/submarine-*`
  是 DeerFlow prompt 层真正可读的潜艇 skill 目录

也就是说，这里继续是“潜艇领域事实与资产”的入口，但不直接承载 DeerFlow runtime 本身。

## 当前第一阶段能力

第一阶段已经接上的最小闭环是：

1. 用户上传 `.stl`
2. DeerFlow agent 调用 `submarine_geometry_check`
3. 生成结构化 `json`、中文 `md` 报告和可展示 `html`
4. 结果进入当前 thread 的 artifact 列表

当前还没有把真实求解调度、真实 OpenFOAM 执行和完整后处理接上；这些会在现有几何检查闭环之上继续扩展。

不过当前已经有第一版求解派发壳层：

1. 可以围绕 thread 内的几何文件生成 OpenFOAM 请求清单
2. 可以把派发摘要写入 DeerFlow artifact
3. 在当前 sandbox 可用时，可以执行显式提供的受控命令并把日志回写到 artifact

当前也已经补上结果报告入口：

1. `submarine_result_report` 会直接读取当前 thread 的 `submarine_runtime`
2. 生成 `final-report.json`、`final-report.md` 和 `final-report.html`
3. 把阶段结果和前置 artifacts 统一整理为 DeerFlow review handoff

## V1 Input Boundary

- v1 输入格式只支持 `STL`
- `STL` 在当前主线里是唯一可直接进入 OpenFOAM 基线求解链的格式
- `STEP / x_t / OBJ / PLY / 3MF` 等其他格式当前不进入 v1 主链
- 因此这里当前最重要的不是扩输入格式，而是把 `STL -> 几何检查 -> OpenFOAM -> 报告` 这条主链做扎实

当前求解派发也已经不只是“写一个请求 JSON”：

1. 真正的 OpenFOAM case scaffold 会落到 DeerFlow `workspace`
2. 可审阅的 `openfoam-request.json`、`dispatch-summary.*`、`supervisor-handoff.json` 会继续落到 DeerFlow `outputs`
3. 这样后续真实 OpenFOAM 执行、MCP 扩展和 Claude Code Supervisor 审阅都仍然沿着 DeerFlow 标准边界推进

后续新增的 OpenFOAM 调度、报告模板、后处理结构和案例检索规则，也应优先沉淀为这里的领域资产，而不是回退到旧原型目录中继续演化。
