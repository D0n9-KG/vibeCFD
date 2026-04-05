# 潜艇仿真智能体系统（DeerFlow 重建基线）

这个仓库已经从原来的轻量原型，切换为 **以 DeerFlow 为新底座** 的重建基线。当前目标不是把系统做成固定阶段的 CFD 工作流，而是做成一个 `lead-agent-first` 的 VibeCFD 系统：由 `Codex` 或 `Claude Code` 主智能体与用户协商目标、约束和交付物，再动态调用 `skills`、`sub-agents`、`tools` 和 `sandbox` 完成任务。

## VibeCFD Direction

- 主智能体是唯一面向用户的协作者
- `skills` 负责提供专业判断与护栏，而不是强制固定顺序
- `tools` 负责确定性动作，例如几何检查、求解派发、结果报告
- `sub-agents` 只承担边界清晰的专项任务
- `sandbox` 和 `artifacts` 是高风险执行与可追溯证据的硬边界

## 当前仓库结构

- [backend](/C:/Users/D0n9/Desktop/颠覆性大赛/backend)
  DeerFlow 后端与 harness 主线，后续主控智能体、sub-agent、memory、Claude Code 集成等都以这里为基础。
- [frontend](/C:/Users/D0n9/Desktop/颠覆性大赛/frontend)
  DeerFlow 前端主线。后续会在这个基础上重构出潜艇仿真工作台，而不是继续使用旧原型的页面结构。
- [domain/submarine](/C:/Users/D0n9/Desktop/颠覆性大赛/domain/submarine)
  当前保留下来的潜艇领域资产入口，包括案例与 skill 元数据。
- [docs/archive/superpowers/specs/2026-03-25-claude-code-supervisor-submarine-cfd-design.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/archive/superpowers/specs/2026-03-25-claude-code-supervisor-submarine-cfd-design.md)
  当前主线的正式系统设计，明确了 `Claude Code Supervisor + DeerFlow CFD Runtime + 专业 subagents + OpenFOAM` 的目标形态。
- [docs/archive/superpowers/specs/2026-03-25-deerflow-replatform-design.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/archive/superpowers/specs/2026-03-25-deerflow-replatform-design.md)
  DeerFlow 重平台切换的背景设计说明，作为当前主线的上游背景文档保留。
- [legacy/current-prototype](/C:/Users/D0n9/Desktop/颠覆性大赛/legacy/current-prototype)
  旧的轻量原型整体归档，只保留为参考资料，不再作为主线继续演化。

## 为什么切换到底座重建

当前项目的核心诉求不是继续维护一套较轻的自建 agent runtime，而是尽可能充分利用：

- DeerFlow 的 `sub-agents`
- DeerFlow 的 `memory`
- DeerFlow 的 `sandbox`
- DeerFlow 的 `skills` 与 MCP 扩展能力
- DeerFlow 的 artifact / thread 管理
- DeerFlow 对 Claude Code 和兼容模型接入的支持

这些能力比旧原型当前拥有的通用框架层更强，也更系统。由于现阶段领域层仍然较浅，现在切换到底座重建的成本低于未来继续叠加后再回头替换。

## 当前保留了什么

这次没有把旧工作全部删除，而是只保留了真正值得继续利用的内容：

- 潜艇案例数据：[domain/submarine/cases/index.json](/C:/Users/D0n9/Desktop/颠覆性大赛/domain/submarine/cases/index.json)
- skill 元数据：[domain/submarine/skills/index.json](/C:/Users/D0n9/Desktop/颠覆性大赛/domain/submarine/skills/index.json)
- 旧原型中的几何处理、结果组织、前端工作台和报告经验，整体保留在 [legacy/current-prototype](/C:/Users/D0n9/Desktop/颠覆性大赛/legacy/current-prototype)

## 当前已经接上的最小潜艇闭环

当前主线已经开始把潜艇领域真正接到 DeerFlow 上，而不是停留在方案层：

- 领域源数据仍然以 [domain/submarine](/C:/Users/D0n9/Desktop/颠覆性大赛/domain/submarine) 为入口
- DeerFlow 运行时已经增加 `backend/packages/harness/deerflow/domain/submarine/`
- DeerFlow skills 已增加：
  - `skills/public/submarine-case-search`
  - `skills/public/submarine-geometry-check`
  - `skills/public/submarine-solver-dispatch`
  - `skills/public/submarine-report`
  - `skills/public/submarine-orchestrator`
- DeerFlow 内置工具已增加 `submarine_geometry_check`
- DeerFlow 内置工具已增加 `submarine_solver_dispatch`
- DeerFlow 内置工具已增加 `submarine_result_report`
- DeerFlow 专业 subagents 已注册：
  - `submarine-task-intelligence`
  - `submarine-geometry-preflight`
  - `submarine-solver-dispatch`
  - `submarine-result-reporting`

现在最小闭环已经可以围绕现有 thread / upload / artifact 机制工作，但这些能力应该被视为主智能体可动态调用的能力边界，而不是唯一固定流程：

1. 用户把 `.stl` 上传到当前 thread
2. agent 通过 `submarine-geometry-check` skill 调用 `submarine_geometry_check`
3. 系统输出中文摘要，并把结果写入 thread outputs
4. 产物进入 DeerFlow artifact 面板，可在前端直接打开
5. thread state 会同步写入 `submarine_runtime`，供后续 `solver dispatch / report / Supervisor` 继续接力

此外，当前主线已经补上了第一版 `submarine_solver_dispatch`：

1. 基于当前 thread 中的几何与案例候选生成 OpenFOAM 派发清单
2. 产出 `openfoam-request.json`、中文 `dispatch-summary.md` 和 `dispatch-summary.html`
3. 当提供命令并允许执行时，可通过当前 DeerFlow sandbox 执行受控命令，并把 `openfoam-run.log` 回写为 artifact

当前 geometry-check 产物默认落在：

- `backend/.deer-flow/threads/{thread_id}/user-data/outputs/submarine/geometry-check/{geometry_slug}/geometry-check.json`
- `backend/.deer-flow/threads/{thread_id}/user-data/outputs/submarine/geometry-check/{geometry_slug}/geometry-check.md`
- `backend/.deer-flow/threads/{thread_id}/user-data/outputs/submarine/geometry-check/{geometry_slug}/geometry-check.html`

这一步还没有恢复旧执行器、旧调度器或旧前端，而是严格复用 DeerFlow 的原生上传、thread、artifact 与 skill 注入机制。

## 当前目标架构

当前推荐的系统形态已经进一步明确为：

- `Claude Code` 作为外层 `Supervisor`
- `DeerFlow` 作为唯一 `CFD Runtime`
- 潜艇领域能力通过 `skills + domain runtime + subagents + artifacts` 进入 DeerFlow
- 真实 OpenFOAM 与其他专业服务通过 `sandbox / MCP` 受控接入

这意味着后续不是继续做一个“通用聊天 agent”，而是做一个围绕潜艇 CFD run 组织的专业智能体系统。

## 下一阶段开发原则

后续开发默认遵循以下原则：

- 不再继续扩展 `legacy/current-prototype` 中的旧主线代码
- 新增的潜艇场景能力，优先做成 DeerFlow 兼容的领域 skill、prompt、artifact 和前端工作台组件
- 需要参考旧实现时，从 `legacy/current-prototype` 抽取思路，而不是继续在旧框架上补丁式迭代
- Claude Code、sub-agent、memory、sandbox 等能力优先按 DeerFlow 原生方式接入，而不是自建平行执行层

## 上游参考

- DeerFlow 上游仓库：[bytedance/deer-flow](https://github.com/bytedance/deer-flow)
- DeerFlow 中文说明：[README_zh.md](/C:/Users/D0n9/Desktop/颠覆性大赛/README_zh.md)

如果后续要继续推进，请先阅读：
[2026-03-25-claude-code-supervisor-submarine-cfd-design.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/archive/superpowers/specs/2026-03-25-claude-code-supervisor-submarine-cfd-design.md)

背景设计说明见：
[2026-03-25-deerflow-replatform-design.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/archive/superpowers/specs/2026-03-25-deerflow-replatform-design.md)

## Runtime Status Update

- Current DeerFlow-native submarine runtime stages now include `submarine_geometry_check`, `submarine_solver_dispatch`, and `submarine_result_report`
- Current thread state now persists a structured `submarine_runtime` snapshot so geometry preflight, solver dispatch, reporting, and Claude Code Supervisor handoff can continue across the same run
- Current public submarine skills now include `submarine-solver-dispatch` in addition to case search, geometry check, report, and orchestrator
- Real OpenFOAM case scaffolds now live under DeerFlow `workspace`, while reviewable manifests and reports stay under DeerFlow `outputs/artifacts`
- Solver dispatch now emits a `supervisor-handoff.json` artifact so Claude Code Supervisor can review the same structured contract that DeerFlow runtime is using

## OpenFOAM Sandbox Status

- The project now defines a DeerFlow-compatible OpenFOAM sandbox image at [docker/openfoam-sandbox/Dockerfile](/C:/Users/D0n9/Desktop/颠覆性大赛/docker/openfoam-sandbox/Dockerfile)
- Build and verification instructions live in [docker/openfoam-sandbox/README.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docker/openfoam-sandbox/README.md)
- Recommended image tag is `deer-flow-openfoam-sandbox:latest`
- `make setup-sandbox` and `make docker-init` now resolve the sandbox image from `config.yaml`, so DeerFlow can use a project-specific CFD sandbox instead of a generic image

## V1 STL-only Boundary

- v1 只接受 `clean watertight STL` 作为几何输入。
- `.stl` 上传后可以继续进入 DeerFlow `geometry check -> solver dispatch -> OpenFOAM` 基线链路。
- `STEP / x_t / OBJ / PLY / 3MF` 等其他格式当前都不进入 v1 主链，系统会直接提示改用 STL。
- v1 仍然会在 OpenFOAM 内生成体网格；当前暂不做复杂的通用网格自动生成平台，而是采用固定模板化 meshing 路径。
