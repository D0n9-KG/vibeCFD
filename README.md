# Submarine Workflow Demo

这是一个围绕“潜艇仿真任务工作流”搭起来的本地可运行 demo。它当前的重点，不是直接把真实 CFD 全部算完，而是先把一条可解释、可追踪、可恢复、可取消、可继续扩展的工程工作流骨架搭起来。系统现在已经能够完成这样一条主链路：

`任务提交 -> 案例检索 -> 推荐流程 -> 人工确认 -> 后台入队 -> 调度器领取 -> 执行器边界 -> 产物与报告展示`

它还没有接入真实 Claude、真实 OpenFOAM 和真实 MCP 工具，但这些外部能力未来应该接在哪一层、通过什么边界接进来，仓库里现在已经有了清晰的结构。

## 当前已经实现的内容

后端使用 `FastAPI`，前端使用 `React + Vite`。后端内部已经接入轻量 `LangGraph` 编排层，并围绕 `RunStore`、案例检索、工作流生成、后台调度器和执行引擎工厂形成了完整闭环。一个任务创建之后，系统会自动为它生成独立的 `runs/<run_id>/...` 目录，把请求、候选案例、工作流草案、执行日志、后处理产物和最终报告都写进同一个 run 空间。

这套系统现在已经不是“确认后同步跑完”的一次性 demo 了。确认动作只会把 run 置为 `queued`，随后由后台调度器轮询队列、领取任务、把 run 推进到 `running`，再调用当前配置的执行引擎。前端看到的是更真实的任务生命周期，后端接口也不需要阻塞等待执行完成。

每个 run 现在同时保存三类信息：

- `run_state.json`：当前快照，包含状态、当前阶段、候选案例、工作流草案、时间线、指标、产物和报告。
- `events/events.jsonl`：追加写入的结构化事件历史，记录创建、入队、领取、完成、失败、取消、重试等关键动作。
- `attempts/attempts.json`：真实执行尝试历史，记录每次 dispatch 的开始时间、结束时间、耗时、执行引擎、结果摘要，以及失败时的失败分类和失败来源。

服务重启之后，后端会自动扫描 `runs/*/run_state.json` 恢复历史 run。对于重启前处于 `running` 的任务，系统不会假装它还在继续运行，而是会把它识别为“服务重启中断，需要手动重试”，并把这次 attempt 标记为失败，写入清晰的失败归因。

## 当前前端界面

前端这一轮已经从原来的深色卡片瀑布流，重构成了中文仿真工作台布局。页面现在由五个固定区域组成：

- 顶部操作带：放全局状态和高频动作，例如 `新建任务`、`刷新列表`、`确认执行`、`取消排队`、`重试运行`。
- 左侧工作栏：保留 `任务 / 案例 / 历史` 三个一级切换。当前默认进入 `任务输入`，需要时再切到候选案例或历史运行，避免一列里同时堆太多内容。
- 中央图形区：使用 `图形视图 / 结果对比 / 案例映射` 三种标签页，保留主视窗和副视窗结构，即使没有真实 3D 结果，也始终保留图形工作区的体验。
- 右侧检查器：集中显示 `流程确认`、`关键指标`、`工具与产物摘要`，默认只保留决策所需的短信息，不把长段文字塞进侧栏。
- 底部 Dock：统一承载 `流程详情`、`时间线`、`运行事件`、`执行尝试`、`产物目录` 和 `最终报告`，把长内容和深层细节收口到底部，不再让首页无限变长。

这一版的目标不是把网页伪装成桌面软件，而是借用仿真软件的“工作台逻辑”：第一屏先服务于操作和判断，而不是服务于阅读和营销式展示。

## 当前执行边界

为了便于本地演示和后续替换，仓库里目前有三条执行边界：

- `mock`：用于生成完整演示结果，证明日志、图表、表格、结构化结果和报告都能顺利落盘。
- `openfoam`：面向真实求解器的边界层，已经能够写请求并调用外部命令，但还没有接入真正的 OpenFOAM 运行环境。
- `claude_executor`：代表未来 Claude 接入的执行器边界。后端会把结构化任务写入 `execution/claude_executor/request.json`，再派发给独立的 `claude-executor` 服务。当前仓库自带的是一个本地 stub 版本，用来先跑通“调度层 -> 执行器 -> 结构化结果回传”这条链路。

## 目录结构

```text
backend/               FastAPI API、LangGraph 编排层、调度器与执行引擎
frontend/              React + Vite 前端
data/cases/            结构化案例库
data/skills/           skill manifest
runs/                  每次运行的持久化目录
uploads/               上传文件暂存目录
docs/                  项目文档、设计规格、实施计划、外部依赖说明
docker-compose.yml     本地多服务编排
```

## 本地启动方式

### 安装后端依赖

```powershell
cd backend
python -m pip install -r requirements.txt
```

### 安装前端依赖

```powershell
cd frontend
npm install
```

### 分别启动前后端

后端：

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

前端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

如果你想测试 `claude_executor` 这条本地执行边界，还可以额外启动 stub 执行器服务：

```powershell
cd backend
python -m uvicorn app.claude_executor_main:app --host 127.0.0.1 --port 8020 --reload
```

然后设置：

```powershell
$env:SUBMARINE_EXECUTION_ENGINE='claude_executor'
$env:SUBMARINE_EXECUTOR_BASE_URL='http://127.0.0.1:8020'
```

### 一键启动

```powershell
.\start-demo.ps1
```

## Docker Compose

当前 `docker-compose.yml` 已经包含这些服务：

- `backend`
- `frontend`
- `claude-executor`
- `openfoam-adapter`

校验配置：

```powershell
docker compose config
```

启动：

```powershell
docker compose up --build
```

需要特别说明的是，`claude-executor` 和 `openfoam-adapter` 目前都还是结构正确的边界服务，并不代表真实 Claude 和真实 OpenFOAM 已经接进来了。它们的意义，是先把服务边界和交互协议定下来，方便后续外部能力无缝接入。

## 关键环境变量

- `SUBMARINE_DEMO_ROOT`：定位 `data/`、`runs/` 和 `uploads/`
- `SUBMARINE_EXECUTION_ENGINE`：切换执行引擎，可选 `mock`、`openfoam`、`claude_executor`
- `SUBMARINE_EXECUTION_DELAY`：控制 mock 演示延时
- `SUBMARINE_DISPATCH_POLL_INTERVAL`：控制后台调度器轮询 `queued` run 的间隔
- `SUBMARINE_OPENFOAM_COMMAND`：为 `openfoam` 边界提供外部命令
- `SUBMARINE_EXECUTOR_BASE_URL`：为 `claude_executor` 引擎指定执行器服务地址
- `SUBMARINE_EXECUTOR_TIMEOUT`：设置 `claude_executor` 请求超时
- `VITE_API_BASE`：前端访问 API 的地址，默认 `http://127.0.0.1:8010`

## 验证命令

后端测试：

```powershell
cd backend
python -m pytest tests -q
```

前端测试：

```powershell
cd frontend
npm test -- --run
```

前端构建：

```powershell
cd frontend
npm run build
```

Compose 校验：

```powershell
docker compose config
```

## 仍未接入的外部能力

当前仓库已经把系统骨架搭好了，但真实 Claude、真实 OpenFOAM、真实 MCP 工具和真实 benchmark 资产仍然没有接入。这不是因为本地少写了某个模块，而是因为这些能力本来就必须由外部提供权限、资源和运行环境。

更完整的说明已经整理在：

[docs/2026-03-20-external-dependencies-checklist.md](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/2026-03-20-external-dependencies-checklist.md)

那份文档更详细地说明了当前系统已经做到哪里、在完全不依赖外部资源的前提下还能继续做什么、哪些内容必须由外部补齐，以及未来这些能力应该如何接入当前已经成型的边界。

## 下一步建议

如果继续只做当前工作区内可以完成的内容，最有价值的方向有两类。

第一类是继续强化任务系统本身，例如恢复执行、失败重试、attempt 对比、阶段级耗时分析，以及 `claude-executor` 协议里的心跳、取消和错误码。

第二类是继续打磨前端工作台，例如补更强的图形视图占位、结果对比布局、历史过滤与搜索、状态色系统和更细的运行反馈，让它从“结构正确”进一步走向“日常可用”。
