# Claude Code Supervisor + DeerFlow 潜艇 CFD 智能体系统设计

## 1. 文档目的

这份文档定义当前仓库接下来的唯一主线：在 DeerFlow 之上构建面向潜艇 CFD 任务的专业智能体系统，并把 `Claude Code` 放在 DeerFlow 官方推荐的位置上，作为外层总控入口使用。

它不是对 [2026-03-25-deerflow-replatform-design.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/superpowers/specs/2026-03-25-deerflow-replatform-design.md) 的替代，而是该重构决策之后的正式系统设计。前一份文档回答“为什么切到 DeerFlow”；这一份回答“切过去之后系统应该长成什么样，以及如何充分使用 DeerFlow 的能力”。

## 2. 核心决策

当前系统采用三层结构：

1. `Claude Code Supervisor`
   负责用户意图理解、方案确认、阶段门控、质量审阅、与用户的高层交互。
2. `DeerFlow CFD Runtime`
   负责 thread、upload、artifact、memory、sandbox、skills、MCP、subagents 和运行态编排。
3. `专业执行能力层`
   负责几何检查、案例匹配、OpenFOAM 任务准备、求解调度、结果整理与报告生成。

关键约束如下：

- 不再恢复旧的轻量执行器、旧调度器、旧前端主线。
- `legacy/current-prototype/` 只作为领域经验参考。
- 潜艇系统的核心交付物是可追踪的 run、artifact、报告和结构化结果，而不是一段聊天回复。
- `Claude Code` 的官方推荐接入位是 DeerFlow 外层，通过 `claude-to-deerflow` 与 DeerFlow HTTP API 交互；本项目遵循这个位置。

## 3. 目标

系统应支持如下任务形态：

1. 用户上传潜艇几何文件，例如 `.x_t` 或 `.stl`。
2. 系统完成任务理解、案例匹配、几何检查、求解准备、求解调度、结果整理和报告生成。
3. 每次执行都形成一个可展示、可追踪、可归档的 DeerFlow thread/run。
4. 后续可以自然接入真实 OpenFOAM、真实专业 skill、真实 MCP 服务和真实 Claude Code 协作链。

同时，系统要充分使用 DeerFlow 的原生能力，而不是只把 DeerFlow 当成一个聊天壳子：

- `sub-agents`
- `memory`
- `sandbox`
- `skills`
- `MCP`
- `artifacts / threads / uploads`
- `Claude Code integration`

## 4. 非目标

当前阶段不做以下事情：

- 不恢复旧原型执行链路。
- 不先追求通用问答 agent。
- 不先做“外观优先”的前端翻新。
- 不在 Claude Code 侧堆一套平行的执行框架。
- 不把 OpenFOAM 先做成脱离 DeerFlow artifact/thread 体系的黑盒脚本。

## 5. 备选方案与取舍

### 方案 A：Claude Code 只做外部调用器

Claude Code 只负责发 HTTP 请求给 DeerFlow，DeerFlow 内部仍保持通用 lead agent，不做深度领域化。

优点：

- 接入速度快
- 与官方 `claude-to-deerflow` skill 最接近

缺点：

- 潜艇领域语义会停留在外层
- DeerFlow 内部无法形成稳定的专业能力边界
- artifact、memory、subagent 很难真正围绕 CFD 工作流组织

### 方案 B：DeerFlow 自己总控，Claude 只做模型提供者

把 Claude 只当 DeerFlow 的模型，在 `models` 层接入 `ClaudeChatModel`。

优点：

- 架构简单
- DeerFlow 内部统一

缺点：

- 不符合“Claude Code 做总控”的目标
- 失去官方 `claude-to-deerflow` 这条外层协作链的价值

### 方案 C：Claude Code Supervisor + DeerFlow Runtime

Claude Code 在外层做总控与质量门控，DeerFlow 在内层做运行时与专业执行编排。

优点：

- 同时符合 DeerFlow 官方推荐接入位和项目当前诉求
- DeerFlow 原生能力可以完整承接专业 run
- Claude Code 负责上层沟通、判断与验收，职责清晰

缺点：

- 需要明确 Supervisor 和 Runtime 之间的协议面
- 需要对 subagent 边界做更严格设计

本项目采用方案 C。

## 6. 总体架构

### 6.1 Claude Code Supervisor

Supervisor 位于 DeerFlow 外层，优先通过 `skills/public/claude-to-deerflow/` 与 DeerFlow 的 Gateway/LangGraph API 交互。

职责：

- 理解用户任务与目标工况
- 做必要的澄清和方案确认
- 决定什么时候启动 DeerFlow run
- 读取 DeerFlow 返回的 artifact、日志和结构化结果
- 做阶段门控与最终质量判断
- 与用户持续交互

不负责：

- 直接执行 OpenFOAM
- 直接承担几何解析或后处理细节
- 自己维护一套独立的 artifact/run 体系

### 6.2 DeerFlow CFD Runtime

DeerFlow 是真正的运行时内核，负责所有与“执行一次专业 CFD 任务”有关的状态与产物管理。

它承接：

- `thread`
- `upload`
- `artifact`
- `memory`
- `sandbox`
- `skills`
- `MCP`
- `subagents`
- `LangGraph run / stream`

当前仓库中的主要挂点如下：

- 上传入口：`backend/app/gateway/routers/uploads.py`
- artifact 服务：`backend/app/gateway/routers/artifacts.py`
- 线程数据目录：`backend/packages/harness/deerflow/agents/middlewares/thread_data_middleware.py`
- upload 注入：`backend/packages/harness/deerflow/agents/middlewares/uploads_middleware.py`
- skill 注入：`backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- DeerFlow 内置几何检查工具：`backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- 潜艇运行时领域层：`backend/packages/harness/deerflow/domain/submarine/`

### 6.3 专业执行能力层

这一层围绕潜艇 CFD 任务做拆分，不再走“单 agent 大包大揽”的路线。

第一批角色边界定义为：

1. `task-intelligence`
   任务理解、案例检索、案例推荐、流程建议。
2. `geometry-preflight`
   几何识别、格式检查、尺度估计、风险提示、前处理产物生成。
3. `solver-dispatch`
   OpenFOAM case 组装、求解参数映射、执行调度、运行日志与失败恢复。
4. `result-reporting`
   汇总日志、图表、数值结果、形成中文摘要、正式报告与 artifact 清单。

这些边界已经在 `backend/packages/harness/deerflow/domain/submarine/roles.py` 中有了第一版定义，后续需要进一步演化为真正可注册的 DeerFlow 专业 subagents。

## 7. DeerFlow 能力映射

| DeerFlow 能力 | 在潜艇 CFD 系统中的作用 |
|---|---|
| `threads` | 每个潜艇任务对应一个可追踪的工作线程，承载上传、消息、产物和状态 |
| `uploads` | 承载 `.x_t`、`.stl`、配置表、补充资料等输入 |
| `artifacts` | 承载几何检查结果、OpenFOAM 日志、后处理图片、最终报告 |
| `sub-agents` | 承载案例理解、几何预检、求解调度、结果整理等角色分工 |
| `memory` | 保留案例经验、用户偏好、任务上下文、常见失败模式与最佳实践 |
| `sandbox` | 承载几何预处理、OpenFOAM 本地或容器内执行、后处理脚本运行 |
| `skills` | 把潜艇领域工作流显式注入 lead agent 与专业 subagent |
| `MCP` | 接入 CAD/网格/存储/检索/远程集群/报告服务等外部能力 |
| `Claude Code integration` | 让外层 Supervisor 官方方式接入 DeerFlow，而不是自造协议 |

## 8. 关键对象模型

### 8.1 Thread 即任务容器

每个任务 thread 至少要包含：

- 用户输入消息
- 上传文件列表
- 当前阶段状态
- 中间与最终 artifact
- 结构化结果摘要
- 失败原因与重试记录

这意味着 thread 不是普通聊天记录，而是一次潜艇 CFD run 的主容器。

### 8.2 Artifact 即一等公民

artifact 需要被设计成面向展示与归档，而不是临时输出文件。第一阶段最低要求：

- `geometry-check.json`
- `geometry-check.md`
- `geometry-check.html`

后续要扩展为：

- `case-selection.json`
- `solver-plan.md`
- `openfoam-run.log`
- `postprocess-summary.json`
- `report.md`
- `report.html`
- 关键图片、表格、曲线图

### 8.3 Memory 即任务知识沉淀

Memory 不应只记录泛用聊天事实，而应沉淀以下内容：

- 常用潜艇几何家族与对应案例
- 常见输入问题与修复建议
- 用户或团队偏好的工况设置
- OpenFOAM 求解过程中的常见失败模式
- 报告口径与展示偏好

## 9. End-to-End 运行流

标准任务流如下：

1. 用户在 Claude Code 中提出任务并提供输入。
2. Claude Code Supervisor 完成高层意图理解和方案澄清。
3. Supervisor 通过 `claude-to-deerflow` 创建 thread，并上传几何文件到 DeerFlow。
4. DeerFlow lead agent 加载潜艇技能，进入 `submarine-orchestrator` 工作流。
5. `task-intelligence` 完成案例匹配与流程建议。
6. `geometry-preflight` 执行 `.x_t` / `.stl` 检查并写入 artifact。
7. 若检查通过，`solver-dispatch` 组装 OpenFOAM case 并通过 sandbox / MCP 执行。
8. `result-reporting` 汇总结果、产物与报告。
9. DeerFlow thread 返回可展示 artifact、结构化结果和中文摘要。
10. Claude Code Supervisor 读取结果，进行质量审查，并向用户汇报。

## 10. OpenFOAM 接入原则

OpenFOAM 不应该作为一条游离在系统外部的脚本链，而应作为 DeerFlow 运行时中的受控执行能力接入。

推荐接法：

1. DeerFlow `solver-dispatch` 负责把潜艇任务映射为受控的 OpenFOAM 执行计划。
2. 执行计划在 DeerFlow sandbox 中落地，或通过 DeerFlow MCP 转发到远端计算资源。
3. 所有执行日志、配置、输入映射和输出结果都回写到 thread artifact。
4. Claude Code Supervisor 永远不直接操作 OpenFOAM 目录，而是只看 DeerFlow 返回的结构化状态与产物。

这保证了：

- OpenFOAM 被纳入统一运行时治理
- 失败可以追踪
- 结果可以归档
- 后续可以从本地执行切到容器执行或远程集群，而不改 Supervisor 侧接口

## 11. 技能与 Subagent 设计原则

潜艇系统不能只靠一个通用 prompt。领域能力必须固化为 DeerFlow 可读、可组合、可替换的 skill 与 subagent 结构。

推荐保留并扩展以下 skill：

- `submarine-orchestrator`
- `submarine-case-search`
- `submarine-geometry-check`
- `submarine-report`
- `submarine-solver-dispatch`
- `submarine-postprocess`

其中：

- `skills/public/submarine-*` 负责提示与工作流约束
- `backend/packages/harness/deerflow/domain/submarine/*` 负责结构化领域逻辑
- 专业 subagent 配置负责明确执行边界与工具权限

## 12. MCP 与外部能力扩展

为了真正“充分利用 DeerFlow”，MCP 需要成为潜艇系统的长期标准扩展位，而不是可有可无的补充。

优先考虑的 MCP 类型：

- 远程 OpenFOAM 或 HPC 作业提交
- CAD/几何检查服务
- 网格生成或质量评估服务
- 对象存储与结果归档
- 专业知识库与案例检索
- 报告导出与企业内部分发

原则是：

- DeerFlow 通过 MCP 接入外部能力
- Claude Code Supervisor 不直接绕开 DeerFlow 调这些服务
- 所有外部能力调用结果最终回到 DeerFlow thread/artifact

## 13. 当前文档清理决策

为避免继续被迁移期残留文档误导，以下文档在本轮清理中移除：

- `docs/CODE_CHANGE_SUMMARY_BY_FILE.md`
- `docs/SKILL_NAME_CONFLICT_FIX.md`
- `docs/superpowers/plans/2026-03-25-submarine-deerflow-minimum-loop.md`

清理原因：

- 它们属于临时迁移说明或已经被新主线覆盖
- 不能作为当前架构决策依据
- 会把注意力拉回旧问题或窄范围阶段性方案

## 14. 分阶段实施建议

### Phase 1：Supervisor/Runtime 契约定型

- 明确 Claude Code Supervisor 调用 DeerFlow 的任务协议
- 统一 thread、upload、artifact 的 run 语义
- 保持已有几何检查最小闭环可用

### Phase 2：专业 Subagent 结构落地

- 把 `roles.py` 中的角色边界变成真正可调用的 DeerFlow 专业 subagents
- 让 `submarine-orchestrator` 优先调度专业 subagents，而不是只依赖通用代理

### Phase 3：OpenFOAM 受控接入

- 定义 `solver-dispatch` 的输入输出契约
- 在 sandbox 或 MCP 上接入真实 OpenFOAM 运行链
- 让日志、配置和结果都进入 artifact

### Phase 4：结果与报告产品化

- 完成结果汇总、中文报告、图表与结果面板
- 让 DeerFlow 前端逐步演化成潜艇仿真工作台

## 15. 成功标准

满足以下条件时，可认为系统进入正确主线：

1. Claude Code 负责高层总控，但不直接承担底层执行。
2. DeerFlow 成为唯一运行时内核，完整承载 thread、upload、artifact、memory、sandbox、skills、MCP 和 subagents。
3. 潜艇任务可以形成从上传到结果报告的完整 run。
4. OpenFOAM、专业服务和后续团队协作能力都能在 DeerFlow 体系内自然接入。
5. 仓库中不再保留会让开发者误判主线的旧计划或迁移残留文档。
