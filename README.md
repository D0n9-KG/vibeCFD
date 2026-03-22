# 潜艇仿真工作台 Demo

这是一个面向比赛展示的本地可运行系统。它已经具备完整的任务闭环：用户提交潜艇外形任务与几何文件，系统检索相似案例、生成推荐流程、等待人工确认，再由主控执行器完成几何检查、演示级求解、结果整理和报告生成，最终把日志、图像、结果表、结构化 JSON 与 Markdown 报告统一写入 `runs/<run_id>/`。

当前版本的重点不是做真实高精度 CFD 全链，而是把一套“接近可发布”的智能仿真工作台真正搭起来。前端已经是中文工作台界面，后端具备排队、调度、状态恢复、事件历史和执行尝试记录，执行层则升级成了一个项目专用主控执行器，能够真实调用兼容 OpenAI 协议的模型接口，并在受控 skill 边界内生成完整比赛展示结果。

## 当前能力

- 前端为中文仿真工作台，包含任务输入、案例查看、历史运行、图形视图、运行事件、产物目录和最终报告。
- 后端使用 `FastAPI`，支持任务创建、案例映射、流程确认、排队执行、取消、重试、事件历史和 attempt 历史。
- 每个 run 都会持久化到 `runs/<run_id>/`，包含 `run_state.json`、事件流、attempt 历史、执行日志、图表、结果 JSON 和最终报告。
- 执行器采用独立服务边界，通过 `/api/execute` 接收结构化请求，完成主控规划、几何检查、结果生成和报告回写。
- 几何检查已支持 `.x_t` Parasolid 文本头信息解析和 `.stl` 网格文件解析，能识别桌面上的 `suboff_solid.x_t`、`suboff_solid.stl` 这类真实输入，并生成几何概览图。
- 系统默认优先支持国产兼容模型接口，也兼容其它 OpenAI-compatible 服务作为本地开发测试入口。

## 目录结构

```text
backend/                FastAPI API、调度器、执行引擎与主控执行器运行时
frontend/               React + Vite 中文工作台界面
data/cases/             结构化案例库
data/skills/            skill manifest
runs/                   每次运行的持久化目录
uploads/                上传文件暂存目录
docs/                   项目文档、设计说明与外部依赖说明
scripts/                本地演示辅助脚本
docker-compose.yml      多服务本地编排
```

## 环境变量

后端与执行器最关键的环境变量如下：

- `SUBMARINE_EXECUTION_ENGINE`
  可选 `mock`、`openfoam`、`agent_executor`。当前推荐使用 `agent_executor`。
- `SUBMARINE_EXECUTOR_BASE_URL`
  后端派发执行任务时访问执行器服务的地址。
- `SUBMARINE_AGENT_BASE_URL`
  主控模型的兼容 API 地址。
- `SUBMARINE_AGENT_MODEL`
  主控模型名称。
- `SUBMARINE_AGENT_API_KEY`
  主控模型 API Key。
- `DASHSCOPE_API_KEY` / `DEEPSEEK_API_KEY` / `GLM_API_KEY` / `OPENROUTER_API_KEY`
  如果未显式设置 `SUBMARINE_AGENT_API_KEY`，执行器会按这些常见变量自动推断兼容入口。

## 本地启动

### 方式一：直接启动三个服务

执行：

```powershell
.\start-demo.ps1
```

脚本会分别启动：

- 执行器：`http://127.0.0.1:8020`
- 后端：`http://127.0.0.1:8010`
- 前端：`http://127.0.0.1:5173`

### 方式二：Docker Compose

执行：

```powershell
docker compose up --build
```

当前 Compose 默认包含：

- `backend`
- `frontend`
- `agent-executor`
- `openfoam-adapter`

在使用 Compose 前，请先在宿主机环境中准备好模型相关环境变量，尤其是 `SUBMARINE_AGENT_BASE_URL`、`SUBMARINE_AGENT_MODEL` 和对应 API Key，或者直接提供 `DASHSCOPE_API_KEY` / `DEEPSEEK_API_KEY` / `GLM_API_KEY` 等变量。

## 一键跑桌面演示

桌面已有测试几何：

- `C:\Users\D0n9\Desktop\suboff_solid.x_t`
- `C:\Users\D0n9\Desktop\suboff_solid.stl`

在后端与执行器启动后，可直接运行：

```powershell
.\scripts\run-desktop-demo.ps1
```

如需直接验证 STL，可运行：

```powershell
.\scripts\run-desktop-demo.ps1 -GeometryFilePath C:\Users\D0n9\Desktop\suboff_solid.stl
```

脚本会自动：

1. 等待后端健康检查通过
2. 上传桌面默认 `.x_t` 几何，或通过参数切换到 `.stl`
3. 创建任务并自动确认流程
4. 轮询直到 run 完成
5. 输出最终 `run_id`、run 目录和报告位置

运行完成后，重点结果会出现在：

- `runs/<run_id>/postprocess/images/geometry_overview.svg`
- `runs/<run_id>/postprocess/images/pressure_distribution.svg`
- `runs/<run_id>/postprocess/images/wake_field.svg`
- `runs/<run_id>/postprocess/tables/drag.csv`
- `runs/<run_id>/postprocess/result.json`
- `runs/<run_id>/report/final_report.md`

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

## 当前仍未接入的能力

这版已经可以用于比赛展示，但仍然有一些能力尚未真正接入：

- 真实 OpenFOAM 求解环境
- 领域专家补充的高质量 benchmark 案例资产
- 更完整的专业 skill / MCP 工具实现
- 最终比赛现场指定的部署环境与权限边界

详细说明见：

[外部依赖说明](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/2026-03-20-external-dependencies-checklist.md)
