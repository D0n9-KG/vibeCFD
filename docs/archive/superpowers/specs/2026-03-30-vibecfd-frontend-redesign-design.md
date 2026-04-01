# VibeCFD 前端全面重设计 — 设计文档

**日期**：2026-03-30
**状态**：已批准（v2 — Codex 审查后修订）

---

## 1. 目标

重新设计 VibeCFD 前端，使其真正服务于"通过自然语言完成复杂 CFD 仿真"的核心用户场景。用户在任何时刻都能清楚地看到系统在做什么、已知道什么、下一步是什么。

本次重设计的范围是**替换 workbench 层内部组件**，外层 Provider 树和路由结构保持不变（见第 8 节迁移边界）。

---

## 2. 用户场景与核心流程

### 2.1 VibeCFD 仿真工作台

用户输入自然语言任务（如"算 SUBOFF 带附体 8m/s 的阻力"），系统执行 5 个顶层阶段的 CFD 流水线：

| 阶段 | RuntimeStage 值 | 性质 |
|------|----------------|------|
| 1 | `task-intelligence` | **交互式**：与用户商讨方案，检索案例库，用户确认后流水线才推进 |
| 2 | `geometry-preflight` | 自动：几何预检 |
| 3 | `solver-dispatch` | 自动：OpenFOAM 求解，实时 Cd 收敛 |
| 4 | `result-reporting` | 自动：结果整理，含科学验证证据链、实验对比、深度分析 |
| 5 | `supervisor-review` | **交互式**：Supervisor 复核，可能触发 `user-confirmation` |

> **说明**：scientific-verification / scientific-study / experiment-compare / scientific-followup 是 `result-reporting` 和 `supervisor-review` 阶段产出的内容区段（`SubmarineResultCard`、`SubmarineScientificVerificationSummary` 等），**不是独立的顶层阶段卡片**，在 UI 中展示为 `result-reporting` / `supervisor-review` 阶段卡片的展开详情区。

**阶段 1（task-intelligence）** 是最重要的交互节点：
- Claude Code 检索历史案例库，展示相似案例（匹配度、历史 Cd、与实验偏差）
- 提出计算方案建议（湍流模型、网格类型、求解器、预计耗时）
- 用户确认（或调整）后，通过 `sendMessage` 发送 human message，流水线继续执行

阶段 `user-confirmation` 是 `supervisor-review` 的子状态（`review_status === "needs_user_confirmation"`），不独立显示为阶段卡片。

### 2.2 Skill Studio

领域专家创建、编辑、管理 CFD 技能，并通过 SkillNet 技能图谱治理技能关系。与仿真工作台通过 Activity Bar 切换，路由独立。

---

## 3. 整体布局架构

### 3.1 Shell 结构（从左到右）

```
┌──────────────────────────────────────────────────────────────────────┐
│ Activity Bar │  Left Sidebar  │  Center Main  │  Right Chat Rail     │
│   48px固定   │  140~280px可拖  │  flex剩余空间  │   220~420px可拖      │
│              │               │  min 400px    │                      │
└──────────────────────────────────────────────────────────────────────┘
```

面板宽度拖拽使用 `react-resizable-panels`（项目已引入，`chat-box.tsx` 在用）。

**响应式**：`xl`（1280px）以下退化为单列，Chat Rail 折叠为切换按钮，遵循现有 `submarine-workbench-layout.ts` 的 `xl:` breakpoint 模式。

### 3.2 Activity Bar

固定 48px，竖排图标，切换顶级工作台入口：

| 图标 | 模块 | 路由 |
|------|------|------|
| 🌊 | VibeCFD 仿真 | `/workspace/submarine/[thread_id]` |
| 🧩 | Skill Studio | `/workspace/skill-studio/[thread_id]` |
| 💬 | 普通对话 | `/workspace/chats/[thread_id]` |
| ⚙️ | 设置（底部固定） | 打开 Settings Dialog |

Activity Bar 渲染在现有 `WorkspaceLayout` 内，替换现有 shadcn `SidebarMenu` 的导航区域，不破坏外层 `SidebarProvider`。

### 3.3 颜色主题

**浅色主题**，参考 Linear / Vercel Dashboard：

- 背景：`#ffffff` / `#fafaf9`（侧栏）
- 边框：`#e7e5e4`（→ Tailwind `stone-200`）
- 文本主色：`#1c1917`（→ `stone-900`）
- 文本辅色：`#78716c`（→ `stone-500`）
- 品牌蓝（VibeCFD）：`#0ea5e9`（→ `sky-500`）
- 品牌紫（Skill Studio）：`#9333ea`（→ `purple-600`）
- 成功绿：`#22c55e`（→ `green-500`）
- 警告橙：`#f59e0b`（→ `amber-500`）
- 数据蓝：`#3b82f6`（→ `blue-500`）

---

## 4. VibeCFD 仿真工作台

### 4.1 左侧边栏（140~280px，`ResizablePanel`）

**顶部**：VibeCFD · DeerFlow 品牌标识

**仿真任务列表**：
- 每条显示名称 + 状态（● 运行中 / ✓ 已完成）
- 数据来源：`useThreads()` 筛选 submarine 类型 threads
- 当前选中高亮（`sky-100` 背景）

**当前阶段快速导航**：
- `STAGE_ORDER`（5 个）的迷你列表，彩色圆点状态指示
- 绿=已完成（`current_stage` 在此之后），蓝脉冲=当前，灰=待执行
- 点击滚动到对应阶段卡片

**底部**：`+ 新建仿真` 按钮

### 4.2 中央主区域（阶段流水线，`ResizablePanel flex:1`）

**顶部 Header**（sticky，不随列表滚动）：
- 任务名称 + 当前阶段 badge + 参数标签（来自 `snapshot.simulation_requirements`）

**阶段卡片列表**（overflow-y: auto）：

每个阶段卡片三种状态：

**已完成（done）**：
- 绿色 header，✓ 图标，右侧耗时
- 默认折叠，显示单行摘要（来自 `snapshot.task_summary` / artifact 标题）
- 点击展开查看详情

**进行中（active）**：
- 蓝色 header + 左侧 3px 蓝色边框，脉冲 ● 图标
- 默认展开，不可折叠

**待执行（pending）**：
- 灰色 header，数字序号，文字变灰，折叠

#### task-intelligence 阶段展开内容

1. **案例检索结果**：N 条相似案例卡片，各含匹配度%、案例名、湍流模型、历史 Cd、与实验偏差（数据来自 `snapshot` 的 `selected_case_id` / case library artifact）
2. **建议计算方案**：琥珀色卡片，含湍流模型 / 网格类型 / 求解器 / 预计耗时
3. **操作按钮**：`✓ 确认方案，开始执行`（调用 `sendMessage`）+ `调整参数…`

流水线在用户点击确认前不自动推进（backend 等待 human message）。

#### solver-dispatch 阶段展开内容

- 进度条（来自 `execution_plan` 中的 status 字段）
- 指标 chip 行：Cd、Fx、耗时（来自 result artifacts）
- Cd 收敛历史曲线（SVG，带面积填充）
- 实时日志最后一行（来自 `activity_timeline` 最新事件）

#### result-reporting 阶段展开内容

- 关键结果数字（Cd 大字展示，`text-4xl font-mono`）
- 科学验证证据摘要（`buildSubmarineScientificVerificationSummary` 产出）
- 实验对比结果（若有）
- 深度分析结论段落
- 下载报告按钮（`report_virtual_path`）

#### supervisor-review 阶段展开内容

- 复核状态 badge（`review_status` → `REVIEW_STATUS_LABELS`）
- 若 `review_status === "needs_user_confirmation"`：展示确认/拒绝按钮，`sendMessage` 驱动
- 科学门控状态（`scientific_gate_status`）

### 4.3 右侧 Claude Code 对话轨道（220~420px，`ResizablePanel`）

- Header：绿点在线指示 + "Claude Code" 标题
- 消息流：与现有 chat rail 相同的渲染逻辑，复用 `MessageList` 组件
- AI 消息支持警告样式（琥珀色，⚠️ 前缀）
- 底部：`PromptInput`（复用现有 `PromptInputProvider` 下的 input 组件）

---

## 5. Skill Studio 工作台

通过 Activity Bar 🧩 切换。

### 5.1 左侧边栏

- 品牌：Skill Studio · SkillNet（紫色）
- 技能列表：来自 `loadSkillGraph()` 返回的 `skills` 数组
- 每条显示技能名 + 启用/禁用彩色圆点（`node.enabled`）
- 底部：`+ 新建技能`（触发 `sendMessage` 启动 skill-creator）

### 5.2 中央区域 — 两种视图

#### 图谱视图（默认）

力导向 SVG 技能图谱（纯前端计算，120 次迭代，不引入 d3）：

- 节点：`SkillGraphNode`，半径 = `max(12, min(28, 12 + related_count × 3))`
- 节点颜色：solver=`#3b82f6`，report=`#22c55e`，geometry=`#f97316`，其他/禁用=`#94a3b8`
- 边：`SkillGraphRelationship`，颜色：`depend_on=#ef4444`，`compose_with=#a855f7`，`similar_to=#9ca3af`，`belong_to=#f59e0b`
- 悬停 tooltip（名称、类别、关联数）
- 点击节点 → 调用 `loadSkillGraph({ skillName })` 更新 focus，右侧显示属性检查器

**降级规则**：
- 节点数 > 30 或 API 返回失败 → 退化为分组列表视图（按 category 分组）
- 加载中：骨架占位
- 空图谱：显示"暂无技能，点击 + 新建"

**属性检查器**（图谱右侧 220px）：
- 技能名、类别、关联阶段（`node.stage`）、关系标签、状态
- `✏️ 编辑此技能` 按钮

#### 编辑器视图（点击"编辑"后）

图谱区域整体替换为全宽技能编辑器（`view` 状态切换，不导航）：
- Header：`← 返回图谱` + 技能名 + "编辑中" badge
- Tab 导航（140px）：基本信息 / 输入参数 / 输出格式 / 技能关系 / 测试运行
- 底部：`取消` + `保存技能`
- 保存：`sendMessage` 提交修改，等待 agent 更新 artifact，refetch 图谱

### 5.3 右侧 Skill Creator 对话轨道

- 紫点在线指示 + "Skill Creator" 标题
- 运行 `claude-code-skill-creator` agent（`SKILL_STUDIO_BUILTIN_SKILLS = ["skill-creator", "writing-skills"]`）
- 底部 `PromptInput`，复用 `PromptInputProvider`

---

## 6. 数据来源与状态 API

### 6.1 VibeCFD 状态 source of truth

| UI 区域 | Source | Hook / 函数 |
|---------|--------|------------|
| 阶段卡片状态（done/active/pending） | `snapshot.current_stage` | `useThreadStream()` → `thread.values` |
| 任务参数标签 | `snapshot.simulation_requirements` | 同上 |
| Cd/Fx/收敛曲线 | result artifacts | `useArtifacts()` + `artifact_virtual_paths` |
| 案例检索结果 | case library artifact | `artifact_virtual_paths` 中 case artifact |
| 实时日志 | `snapshot.activity_timeline` | `useThreadStream()` → `thread.values` |
| 执行进度 | `snapshot.execution_plan[].status` | 同上 |
| 确认/拒绝操作 | human message | `sendMessage(text)` |

### 6.2 Skill Studio 状态 source of truth

| UI 区域 | Source | Hook / 函数 |
|---------|--------|------------|
| 技能列表 | `SkillGraphResponse.skills` | `loadSkillGraph()` via TanStack Query |
| 图谱节点/边 | `SkillGraphResponse.relationships` | 同上 |
| 选中节点详情 | `SkillGraphResponse.focus` | `loadSkillGraph({ skillName })` |
| 技能保存 | human message → agent → artifact | `sendMessage(text)` |

---

## 7. 导航与线程保活规则

### 7.1 Activity Bar 切换规则

```
同一 workbench 内的模式切换（如 graph ↔ editor）:
  → React state 切换，不触发任何路由操作

切换到另一个 workbench（submarine → skill-studio）:
  → 有已有 thread: router.push(`/workspace/skill-studio/${lastSkillStudioThreadId}`)
  → 无 thread: router.push(`/workspace/skill-studio/new`) 触发新建

新 thread 在当前 workbench 中创建时:
  → history.replaceState(null, "", `/workspace/submarine/${newThreadId}`)
  → （与现有 page.tsx:64 保持一致，避免 thread remount）
```

### 7.2 面板宽度持久化

使用 `react-resizable-panels` 的 `storage` prop，key 分别为 `submarine-sidebar-size`、`submarine-chat-rail-size`，`localStorage` 持久化。

### 7.3 现有 URL 参数语义（保持不变）

- `/workspace/submarine/new`：path segment `new` 触发新建 thread（`threadIdFromPath === "new"` 时生成 uuid）
- `?mock=true`：mock 模式（query param）
- `?mode=skill`：Skill Studio skill 创建模式，Welcome 页面特殊文案（query param）

---

## 8. 迁移边界（保留 vs 替换）

```
WorkspaceLayout（SidebarProvider）          ← 保留，Activity Bar 嵌入其中
  └── /workspace/submarine/[thread_id]/
      layout.tsx（SubtasksProvider、ArtifactsProvider、PromptInputProvider）  ← 保留
      page.tsx（useThreadStream、sendMessage）                                 ← 保留 hook 调用
        └── SubmarineRuntimePanel（1779 行）   ← 替换为新组件树
              ↓ 替换为
            SubmarineWorkbench
              ├── SubmarineSidebar
              ├── SubmarineStageList（阶段卡片列表）
              │     ├── TaskIntelligenceCard
              │     ├── SolverDispatchCard
              │     ├── ResultReportingCard（含 scientific 内容区段）
              │     └── SupervisorReviewCard
              └── （Chat Rail 复用现有 chat 组件）
```

```
/workspace/skill-studio/[thread_id]/
  layout.tsx（providers）                   ← 保留
  page.tsx（useThreadStream、sendMessage）   ← 保留 hook 调用
    └── SkillStudioWorkbenchPanel           ← 替换为新组件树
          ↓ 替换为
        SkillStudioWorkbench
          ├── SkillStudioSidebar
          ├── SkillGraphCanvas（图谱视图）或 SkillEditorView（编辑视图）
          │     └── SkillInspectorPanel（图谱右侧）
          └── （Chat Rail 复用）
```

`submarine-runtime-panel.utils.ts`、`skill-graph.utils.ts` 中的工具函数**保留复用**，不重写。

---

## 9. 非功能性要求

- **响应式**：`xl`（1280px）以下单列，Chat Rail 折叠为切换按钮，Activity Bar 保持。遵循现有 `submarine-workbench-layout.ts` 的 `xl:` breakpoint 模式。
- **空态**：无仿真任务时展示"点击 + 新建仿真开始"占位。图谱无数据时展示列表降级视图。
- **错态**：stream 断连时展示重连 banner；artifact 加载失败展示错误 inline。
- **测试**：工具函数（布局计算、力导向算法）用 `node:test` 单测，遵循已有 `skill-graph.utils.test.ts` 和 `submarine-workbench-layout.test.ts` 模式。

---

## 10. 技术实现约束

- **框架**：Next.js 16 App Router，React 19，TypeScript 5.8，Tailwind CSS 4
- **面板拖拽**：`react-resizable-panels`（已引入，`chat-box.tsx` 在用），不自写 `mousemove` 实现
- **技能图谱**：纯 SVG 力导向布局，不引入 d3；120 次迭代，Coulomb 斥力 + Hooke 引力 + 中心引力；节点数 > 30 时降级为列表
- **流数据**：通过现有 `useThreadStream` hook 订阅 LangGraph 流事件，确认操作通过 `sendMessage(text)` 发送 human message
- **样式**：Tailwind utility classes + `cn()`，动态宽度用 CSS 变量（`react-resizable-panels` 管理）
- **Server/Client 边界**：布局层 Server Component，交互组件 `"use client"`
