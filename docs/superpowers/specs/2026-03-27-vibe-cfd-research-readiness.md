# 面向科研工作的 Vibe CFD 差距、外部补录要求与仓库推进记录

## 1. 文档目的

这份文档服务于当前 DeerFlow 主线下的 `vibe CFD` 项目，目标不是再讨论是否回到旧原型，而是回答三个更实际的问题：

1. 要把当前系统推进到“真正可用于科研工作”的级别，还缺什么。
2. 这些缺口里，哪些必须由仓库外部补录，补录内容要具体到什么粒度。
3. 在不等待全部外部条件就绪的前提下，当前仓库内还能继续推进哪些能力，以及当前真实状态是什么。

本文档刻意先写外部必须补录的内容，因为这决定了仓库内很多能力的上限。没有 benchmark、专业验收规则和领域专家共创内容，系统最多只能做到“结构化、可追踪、可展示”，还做不到“可以支撑科研判断”。

## 2. 外部必须补录的内容与具体要求

### 2.1 CFD 基准案例与验收规则包

这是最关键的外部补录项。当前仓库已经有 `domain/submarine/cases/index.json` 里的案例库，但它更像 workflow template，不是科研验收数据包。真正面向科研工作，至少要为每个主用案例补入以下信息：

- 案例身份：
  - 标准案例名称
  - 案例来源文献或公开报告
  - 几何版本说明
  - 工况适用范围
- 参考真值或容差：
  - `Cd / Cl / Cm` 的参考值、参考区间或容许误差
  - 压力分布、尾迹速度亏损、典型截面数据
  - 允许采用的比较方式，是点值、曲线趋势还是区间判定
- 计算可信度门槛：
  - 最大可接受残差
  - 最少求解时间或收敛判据
  - 网格质量和网格独立性最小要求
  - 域尺寸、边界条件、湍流模型约束
- 报告必交项：
  - 必须出现的图表
  - 必须出现的对比表
  - 必须记录的求解参数
  - 必须归档的中间 artifacts

具体要求：

- 每个重点案例都应形成结构化 JSON/YAML，而不是只给一段文字说明。
- 每条验收规则都要明确：
  - 数据来源
  - 适用条件
  - 阈值或比较方法
  - 不满足时应判定为 `warning` 还是 `blocked`
- 第一批至少应覆盖：
  - `DARPA SUBOFF bare hull resistance`
  - `DARPA SUBOFF pressure distribution`
  - `Joubert BB2 wake / pressure`
  - `Type 209 engineering drag`

如果这一包不补齐，系统只能做“结果整理”和“工程启发式提示”，不能做“科研验收”。

### 2.2 专业 CFD Skills 内容包

当前仓库内已经有 DeerFlow 技能体系、Skill Studio、graph、publish/install 流程，但“科研可用”的难点在 skill 内容，而不是 skill 外壳。

外部需要补录的 skill 内容至少包括：

- 几何预检 skill：
  - STL 拓扑/尺度/闭合性检查规则
  - 潜艇几何族识别经验
  - 常见问题分类与处理建议
- 网格准备 skill：
  - 不同任务类型的网格策略
  - 局部加密建议
  - 壁面处理、边界层层数、首层高度建议
- OpenFOAM 求解 skill：
  - 求解器选择规则
  - 湍流模型选择规则
  - 稳态/瞬态切换条件
  - 控制参数默认值和调整策略
- 后处理 skill：
  - 力系数提取
  - 压力图、流线、切片、尾迹图生成
  - 典型科研图表格式
- 验收与报告 skill：
  - benchmark 对比
  - 风险说明
  - 中文结论模板
  - “可继续做科研判断 / 只能作演示参考”的边界说明

具体要求：

- 每个 skill 不应只是一段 prompt，至少要包含：
  - 触发条件
  - 输入 contract
  - 输出 contract
  - 验收标准
  - 至少 2-3 个测试场景
- Skill 需要由领域专家和 Claude Code 共创，而不是只靠通用模型生成初稿后直接发布。
- Skill Studio 最终要支持这些专业 skill 的测试记录与发布追踪。

### 2.3 更成熟的 OpenFOAM 模板与后处理模板

当前仓库的 OpenFOAM 路径已经通了基线，但还不是成熟科研模板库。

外部需要补录：

- 分任务类型的 case 模板：
  - resistance
  - pressure distribution
  - wake field
  - 未来扩展的 free-surface
- 模板应包含：
  - 几何导入规范
  - blockMesh / snappyHexMesh 策略
  - turbulenceProperties
  - fvSchemes / fvSolution
  - controlDict 推荐配置
  - forces / forceCoeffs / probes / slices 等 function objects
- 后处理模板应包含：
  - 图像输出标准
  - CSV/JSON 表格字段
  - 中文报告引用格式

具体要求：

- 模板要能对应到具体案例，不要只给“一个万能模板”。
- 每个模板要注明适用边界，不允许超出边界时仍被系统误用为“科研结果”。
- 模板必须能在容器化 sandbox 中复现。

### 2.4 远程算力与生产化运行环境

科研工作不能长期停留在本地 demo sandbox。

外部需要补录：

- 远程计算节点或集群
- 任务队列与资源配额规则
- 长任务运行、失败恢复和归档策略
- 结果回传与 artifact 同步方案

具体要求：

- 需要明确本地 smoke run 与远程正式 run 的边界。
- 正式科研 run 必须记录：
  - 运行环境
  - 镜像版本
  - OpenFOAM 版本
  - skill 版本
  - 关键参数快照

### 2.5 领域专家参与机制

这是决定系统是否真正“科研可用”的组织性条件。

外部必须补录：

- 谁负责案例基准与验收规则
- 谁负责 OpenFOAM 模板审查
- 谁负责 skill 内容审查
- 谁负责结果可信度判定

具体要求：

- 至少形成一个轻量 review 机制：
  - `AI 起草`
  - `专家审阅`
  - `修订发布`
- 没有专家审阅通过的内容，只能算草稿，不应作为正式科研规范。

### 2.6 MCP 与外部知识/工具接入

为进一步提升科研工作流，外部应补录可接入能力：

- 文献检索
- benchmark 数据库
- 远程文件系统/HPC
- 专业后处理工具
- 团队知识库

具体要求：

- 这些接入要通过 DeerFlow 的标准扩展边界完成，不再另造平行执行层。
- 每个接入要明确：
  - 访问权限
  - 可用范围
  - 是否影响科研结论可信度

## 3. 外部补录项的验收标准

外部内容不是“收集到一些材料”就算完成，至少要达到以下验收标准：

### 3.1 案例与规则

- 能以结构化格式进入仓库
- 能被运行时直接读取
- 能被报告和 acceptance 逻辑引用
- 能说明来源、边界和阈值

### 3.2 Skills

- 能在 Skill Studio 中生成、验证、打包、发布
- 至少有最小测试场景
- 输出可追踪到 thread/artifact/run

### 3.3 模板

- 能在 sandbox 里复现
- 能稳定生成 artifacts
- 能和案例规则一一对应

### 3.4 专家参与

- 有明确审阅责任人
- 有版本记录
- 有发布或拒绝结论

## 4. 仓库内可以继续推进的主线

即使外部内容尚未全部补齐，当前仓库内仍然可以继续推进以下方向：

### 4.1 Supervisor 强闭环

- 多轮聊天收敛 design brief
- 执行前确认
- 执行中状态回写
- 执行后结果回收与再决策

### 4.2 案例级验收框架

- 把案例库从“描述型 metadata”提升为“可执行验收 contract”
- 允许先接入占位规则，再逐步替换成专家给出的正式阈值
- 让 acceptance 逻辑支持 `warning / blocked / ready_for_review`

### 4.3 工作台过程控制

- rerun
- stop
- continue
- compare
- 阶段性 review 操作

### 4.4 Skill Studio 治理能力

- 删除
- 版本化
- provenance
- 回滚

### 4.5 中文科研报告与后处理展示

- 图表占位结构
- benchmark 对比表
- 风险解释
- 结论边界说明

## 5. 当前已验证的基础状态

以下状态已通过真实仓库代码和测试核实：

- DeerFlow 主线已接上潜艇 CFD 最小闭环：
  - `submarine_design_brief`
  - `submarine_geometry_check`
  - `submarine_solver_dispatch`
  - `submarine_result_report`
- `task_tool` 的 `target_skills` 逻辑符合既定边界：
  - Claude 显式传才会收窄
  - 不传则 subagent 看到普通 enabled skill 池
- 独立的 `vibe CFD` 工作台与 `Skill Studio` 工作台都已存在
- Skill graph 已接入本地治理层，并有 graph API 与前端展示
- DeerFlow sandbox + OpenFOAM 路径已具备基线链路
- v1 已收口到 `STL-only`

对应代码锚点包括但不限于：

- `backend/packages/harness/deerflow/domain/submarine/`
- `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- `backend/app/gateway/routers/skills.py`

进一步拆开后的真实状态如下：

### 5.1 DeerFlow 主线闭环

- 设计简报：
  - `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- 几何预检：
  - `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- 求解派发：
  - `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- 结果报告：
  - `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`

### 5.2 Skill 路由边界

- `target_skills` 只有 Claude Code 显式传入时才收窄。
- 如果 Claude 不传，subagent 仍使用普通 enabled skill 池。
- 相关逻辑位于：
  - `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
  - `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`

### 5.3 工作台与治理层

- 潜艇工作台：
  - `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`
  - `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Skill Studio：
  - `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`
  - `frontend/src/components/workspace/skill-studio-dashboard.tsx`
  - `frontend/src/components/workspace/skill-studio-workbench-panel.tsx`
- Skills graph API：
  - `backend/app/gateway/routers/skills.py`

### 5.4 当前已落地的结果验收能力

截至本轮，系统已经不是只有“最终报告”，还具备：

- `delivery-readiness.json`
- `delivery-readiness.md`
- `final-report.json` 中的 `acceptance_assessment`

并且 acceptance 逻辑已经支持：

- 通用 gate
  - solver completed
  - mesh quality
  - residual summary
  - planned end time
  - force coefficients
  - STL runtime contract
- 案例级 gate
  - case required artifacts
  - case completed fraction
  - case max final residual

## 6. 当前仍未完成的关键差距

当前系统距离“真正可用于科研工作”的差距，按严重度排序如下：

1. 缺少案例级 benchmark 和验收规则，导致结果可信度无法提升到科研等级。
2. Supervisor 仍偏 prompt/tool 约定，缺少更硬的运行状态机。
3. 工作台缺少过程控制能力，更像展示面板而不是研究工作台。
4. Skill Studio 的治理层还不完整，无法满足长期科研资产沉淀。
5. OpenFOAM 模板和后处理模板仍偏基线演示。

## 7. 本轮仓库内推进目标

本轮优先推进一个最关键、且当前仓库内立刻能做的方向：

- 把当前结果验收从“通用交付门控”推进到“案例级科研验收框架”的第一步。

本轮不试图凭空创造 benchmark 真值，而是先把仓库内的案例 contract 结构搭起来，使系统可以：

- 从案例库读取验收 profile
- 在结果报告中引用案例级阈值
- 给出更清晰的 case-aware acceptance gate

这一步完成后，后续外部专家补录的规则才能自然接入，不需要重写整条运行时。

## 8. 本轮推进记录与当前详细状态

### 8.1 本轮新增的仓库内能力

本轮已完成两类推进：

1. 文档化梳理：
   - 明确外部必须补录项
   - 明确外部内容的具体验收要求
   - 明确仓库内可继续推进方向
2. 代码推进：
   - 把案例库从“描述型 metadata”向“案例级验收 contract”推进了一步
   - 让结果报告开始读取 case-specific acceptance profile
   - 让 acceptance assessment 能根据案例规则给出更严格的判定

### 8.2 本轮真实修改的文件

#### 文档

- `docs/superpowers/specs/2026-03-27-vibe-cfd-research-readiness.md`

#### 仓库内实现

- `backend/packages/harness/deerflow/domain/submarine/models.py`
  - 新增 `SubmarineCaseAcceptanceProfile`
  - `SubmarineCase` 增加 `acceptance_profile`
- `domain/submarine/cases/index.json`
  - 为首批关键案例补入案例级 acceptance profile
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - 新增 selected case 解析
  - 新增 case-aware acceptance gates
  - `final-report.json` 新增 `selected_case_acceptance_profile`

#### 测试

- `backend/tests/test_submarine_domain_assets.py`
- `backend/tests/test_submarine_result_report_tool.py`

### 8.3 本轮已验证的行为

以下行为已通过真实测试验证：

- 案例库能加载 `acceptance_profile`
- `darpa_suboff_bare_hull_resistance` 已带有结构化 case profile
- 结果报告会把案例 profile 写入 `final-report.json`
- 当案例阈值被突破时，`acceptance_assessment` 会转为 `blocked`
- 之前已存在的通用 delivery readiness 流程仍然保持可用

### 8.4 本轮执行的验证

后端：

- `uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_geometry_check_tool.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_task_tool_core_logic.py tests/test_lead_agent_prompt_skill_routing.py tests/test_skill_relationships.py tests/test_skills_graph_router.py tests/test_skills_publish_router.py tests/test_submarine_subagents.py tests/test_submarine_skill_studio_tool.py tests/test_submarine_domain_assets.py tests/test_submarine_skills_presence.py -q`
- 结果：`55 passed`

前端：

- `node --experimental-strip-types --test src/app/workspace/submarine/submarine-workbench-layout.test.ts src/app/workspace/skill-studio/skill-studio-workbench-layout.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts`
- 结果：`24 passed`

类型检查：

- `frontend/node_modules/.bin/tsc.cmd --noEmit`
- 结果：通过

### 8.5 当前项目的详细状态判断

#### 已经做到的

- DeerFlow 主线潜艇 CFD 最小闭环已成型。
- `vibe CFD` 与 `Skill Studio` 两个工作台都已落在同一 DeerFlow thread/artifact/chat 体系下。
- `target_skills` 边界与 skill graph 定位符合既定决策。
- `STL-only` 边界已在运行时、公开 skill 和案例库层面收口。
- 结果报告已经不只是“生成一份 md/html”，还具备结构化 acceptance layer。
- acceptance layer 已开始支持案例级科研验收 skeleton。

#### 仍然只是半成品的

- 案例级 acceptance profile 现在还是第一版 skeleton，只覆盖当前系统能直接读取的指标。
- benchmark 真值、文献容差、网格独立性规则还没有真正接入。
- Supervisor 的多轮收敛和阶段门控还偏 prompt 驱动，不是完整状态机。
- 工作台目前仍偏展示面，过程控制还不足。
- Skill Studio 治理层还不够完整。

#### 当前主要风险

1. 没有外部 benchmark 和专家规则时，case-aware acceptance 仍然只是“科研框架”，还不是正式科研判定。
2. 本地 sandbox 基线可用不等于远程生产算力可用。
3. 结果可视化和后处理模板仍不足以支撑高质量科研汇报。
4. 当前案例级规则主要覆盖数值门槛，尚未覆盖图表、对比曲线和研究结论边界。

### 8.6 下一阶段最值得继续推进的仓库内事项

按优先级建议继续推进：

1. 把案例级 acceptance profile 从 skeleton 扩展为更完整的 case contract：
   - benchmark comparison
   - mesh independence
   - report-required sections
2. 强化 Supervisor 闭环：
   - design brief 多轮收敛
   - 执行前确认
   - 执行后 review gate
3. 给工作台补过程控制：
   - rerun
   - stop
   - continue
   - compare
4. 给 Skill Studio 补治理层：
   - delete
   - version history
   - rollback

## 9. 2026-03-27 Benchmark-Aware 推进补记

### 9.1 本轮继续推进的目标

本轮没有去扩新的界面壳子，而是继续补“科研可信度”这一层。原因是当前仓库虽然已经具备 DeerFlow 主线下的潜艇 CFD 基线闭环，但结果层仍然缺少真正可执行的 benchmark-aware 判断。

这一轮的推进目标被收敛为三件事：

1. 用真实 STL 文件 `C:\Users\D0n9\Desktop\suboff_solid.stl` 复核当前几何识别和 case 匹配是否正确。
2. 给 `darpa_suboff_bare_hull_resistance` 补入第一条可执行 benchmark target。
3. 让 `submarine_result_report` 在工况匹配时自动生成 benchmark comparison，并把结果写入 `acceptance_assessment`。

### 9.2 基于真实 STL 的复核结果

使用仓库中的几何识别与 case ranking 逻辑处理 `C:\Users\D0n9\Desktop\suboff_solid.stl` 后，得到如下结果：

- file_name: `suboff_solid.stl`
- input_format: `stl`
- geometry_family: `DARPA SUBOFF`
- estimated_length_m: `4.356`
- triangle_count: `32760`
- top_case_id: `darpa_suboff_bare_hull_resistance`
- top_case_score: `8.9`

这说明当前主链中的：

- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- `backend/packages/harness/deerflow/domain/submarine/library.py`

已经能把该 STL 稳定识别进 SUBOFF 家族，并把第一推荐案例落到阻力基线 case，而不是错误分流到别的模板。

### 9.3 本轮接入的 benchmark 来源与边界

本轮使用了可公开访问、可追踪的资料做第一版 benchmark 接入：

- 几何与实验计划元数据：
  - `https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA210642.xhtml`
  - `https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA359226.xhtml`
- 当前直接接入的阻力系数参考值来源：
  - `https://pure.port.ac.uk/ws/portalfiles/portal/110702250/Hydrodynamic_parameter_estimation_of_DARPA_SUBOFF.pdf`

本轮落到代码里的 benchmark target 为：

- case: `darpa_suboff_bare_hull_resistance`
- metric_id: `cd_at_3_05_mps`
- quantity: `Cd`
- reference_value: `0.00314`
- inlet_velocity_mps: `3.05`
- relative_tolerance: `0.1`
- on_miss_status: `blocked`

需要明确的是：

- 这不是完整的 DARPA SUBOFF 科研验收包。
- 它只是第一条真正接进 DeerFlow 主链的 benchmark rule。
- 后续仍然需要领域专家补入更多 benchmark、容差依据、网格独立性规则和图表级验收规则。

### 9.4 本轮真实代码改动

#### 1. 扩展案例验收 schema

文件：

- `backend/packages/harness/deerflow/domain/submarine/models.py`

改动：

- 新增 `SubmarineBenchmarkTarget`
- 在 `SubmarineCaseAcceptanceProfile` 中新增 `benchmark_targets`

#### 2. 把 benchmark target 接入案例库

文件：

- `domain/submarine/cases/index.json`

改动：

- 为 `darpa_suboff_bare_hull_resistance` 补入结构化 benchmark target
- 将该 case 的参考来源从占位链接收敛到真实公开来源
- 同时把该文件中原先存在的中文乱码型 summary 一并收口为正常可读文本

#### 3. 让结果报告生成 benchmark comparisons

文件：

- `backend/packages/harness/deerflow/domain/submarine/reporting.py`

改动：

- 新增 benchmark observed value 解析逻辑
- 新增 benchmark target 评估逻辑
- 在 `acceptance_assessment` 中新增 `benchmark_comparisons`
- 对命中的 benchmark target 自动生成对应 gate，例如：
  - `benchmark_cd_at_3_05_mps`
- benchmark miss 会按照 profile 配置进入 `warning` 或 `blocked`
- delivery readiness 的 markdown/html 产物也会带出 benchmark comparison 摘要

### 9.5 本轮新增和扩展的测试

文件：

- `backend/tests/test_submarine_domain_assets.py`
- `backend/tests/test_submarine_result_report_tool.py`

关键覆盖包括：

- `SubmarineCaseAcceptanceProfile` 能否加载 `benchmark_targets`
- `darpa_suboff_bare_hull_resistance` 是否暴露 `cd_at_3_05_mps`
- 当 `inlet_velocity_mps = 3.05` 且 `Cd` 接近 `0.00314` 时，是否生成 `passed` 的 benchmark comparison
- 当同一工况下 `Cd` 偏离过大时，是否生成 `blocked` 的 benchmark gate，并把 run 标为 `blocked`

### 9.6 本轮验证结果

#### 定向 TDD 验证

- `uv run pytest tests/test_submarine_domain_assets.py::test_submarine_case_library_exposes_case_acceptance_profiles -q`
- `uv run pytest tests/test_submarine_result_report_tool.py::test_submarine_result_report_adds_benchmark_comparison_for_matching_case -q`
- `uv run pytest tests/test_submarine_result_report_tool.py::test_submarine_result_report_blocks_when_benchmark_miss_exceeds_tolerance -q`

结果：

- 先红后绿，符合 TDD 预期

#### 潜艇域回归

- `uv run pytest tests -q -k submarine`

结果：

- `36 passed, 730 deselected, 1 warning`

说明：

- warning 仍来自 `backend/packages/harness/deerflow/agents/memory/updater.py` 中既有的 `datetime.utcnow()` deprecation，与本轮改动无关。

#### 前端工作台验证

- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- `node_modules/.bin/tsc.cmd --noEmit`

结果：

- `submarine-runtime-panel.utils.test.ts` 通过
- `frontend` TypeScript 类型检查通过

说明：

- benchmark comparison 现在已经能从 `acceptance_assessment.benchmark_comparisons` 进入前端 summary，并显示在 `submarine-runtime-panel` 的健康面板里。

### 9.7 当前项目状态的新增判断

在本轮 benchmark-aware 推进之后，可以把项目状态更新为：

- 当前系统已经不仅有“结构化 delivery readiness”，还具备“第一条真正可执行的 case benchmark comparison”。
- 这意味着仓库已经迈出了从“工程 gate”走向“科研 gate”的第一步。
- 但当前仍然只是一条示范性 benchmark rule，不足以单独支撑科研结论。

更具体地说：

- 已做到：
  - DeerFlow 主线下的潜艇 CFD 结果报告可以读取案例 benchmark rule 并执行比较。
  - benchmark 结果会进入 `acceptance_assessment`、delivery readiness markdown/html 和最终 JSON 报告。
  - 真实 SUBOFF STL 已能对上 SUBOFF 阻力基线 case。
- 仍未做到：
  - 多 benchmark 联合验收
  - 网格独立性验收
  - 图表级 benchmark 对比
  - 远程正式算力与长任务治理
  - 领域专家审核后的正式验收包

### 9.8 下一步最值得继续推进的仓库内事项

按优先级，下一步建议继续推进：

1. 将 benchmark-aware acceptance 从单条规则扩成可复用 contract
   - 支持多个 benchmark target
   - 支持图表/曲线类 required outputs
   - 支持 mesh-independence 占位规则
2. 扩展工作台中的 benchmark 展示深度
   - 当前已经能在 `submarine-runtime-panel` 中直接看到 benchmark pass/block 状态
   - 下一步应补 benchmark 来源、误差百分比和参考值说明
3. 继续强化 Supervisor 闭环
   - 在 design brief 收敛、执行许可、结果回收之间补更硬的运行状态
4. 为 Skill Studio 补版本与回滚治理
   - 让后续专家共创的专业 CFD skills 能被安全发布和回滚
