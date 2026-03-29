# VibeCFD 前端全面重设计 — 设计文档

**日期**：2026-03-30
**状态**：已批准

---

## 1. 目标

重新设计 VibeCFD 前端，使其真正服务于"通过自然语言完成复杂 CFD 仿真"的核心用户场景。用户在任何时刻都能清楚地看到系统在做什么、已知道什么、下一步是什么。

当前 Codex 生成的前端令用户不满意，本次为从零开始的重设计，不限于复用现有模块。

---

## 2. 用户场景与核心流程

### 2.1 VibeCFD 仿真工作台

用户输入自然语言任务（如"算 SUBOFF 带附体 8m/s 的阻力"），系统执行完整的 8 阶段 CFD 流水线：

| 阶段 | 名称 | 性质 |
|------|------|------|
| 1 | task-intelligence | **交互式**：与用户商讨方案，检索案例库 |
| 2 | geometry-preflight | 自动执行：几何预检 |
| 3 | solver-dispatch | 自动执行：OpenFOAM 求解 |
| 4 | result-reporting | 自动执行：生成结果报告 |
| 5 | scientific-verification | 自动执行：科学验证（与基准对比） |
| 6 | scientific-study | 自动执行：深度科学分析 |
| 7 | experiment-compare | 自动执行：与实验数据对比 |
| 8 | scientific-followup | **交互式**：科学跟进问答 |

**阶段 1（任务理解）** 是最重要的交互节点：
- Claude Code 检索历史案例库，找到相似案例并展示匹配度、历史 Cd、与实验偏差
- 基于案例经验提出计算方案（湍流模型选择、网格类型、求解器、预计耗时）
- 用户审核确认或调整后，流水线才继续执行

### 2.2 Skill Studio

领域专家创建、编辑、管理 CFD 技能，并通过 SkillNet 技能图谱治理技能关系。与仿真工作台完全分离，通过 Activity Bar 切换。

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

分割线（竖向 resize handle）悬停变蓝、变粗，可左右拖动调整宽度。

### 3.2 Activity Bar

固定 48px，竖排图标，切换顶级模块：

| 图标 | 模块 | 说明 |
|------|------|------|
| 🌊 | VibeCFD 仿真 | 默认入口，有运行中任务时显示绿点 badge |
| 🧩 | Skill Studio | 技能管理工作台 |
| 💬 | 普通对话 | 通用 DeerFlow 聊天 |
| ⚙️ | 设置 | 底部固定 |

### 3.3 颜色主题

**浅色主题**，参考 Linear / Vercel Dashboard：

- 背景：`#ffffff` / `#fafaf9`（侧栏）
- 边框：`#e7e5e4`
- 文本主色：`#1c1917`
- 文本辅色：`#78716c`
- 品牌蓝（VibeCFD）：`#0ea5e9`
- 品牌紫（Skill Studio）：`#9333ea`
- 成功绿：`#22c55e`
- 警告橙：`#f59e0b`
- 数据蓝：`#3b82f6`

---

## 4. VibeCFD 仿真工作台

### 4.1 左侧边栏（140~280px）

**顶部**：VibeCFD · DeerFlow 品牌标识

**仿真任务列表**：
- 每条显示名称（SUBOFF-002）+ 状态（● 求解执行中 / ✓ 已完成）
- 当前选中的任务高亮（`#e0f2fe` 蓝色背景）
- 支持多个历史任务记录

**当前阶段快速导航**：
- 8 个阶段的迷你列表，彩色圆点状态指示（绿=完成，蓝脉冲=进行中，灰=待执行）
- 点击可快速滚动到对应阶段卡片

**底部**：`+ 新建仿真` 按钮（品牌蓝背景）

### 4.2 中央主区域（阶段流水线）

**顶部 Header**（不可滚动）：
- 任务名称 + 当前阶段 badge + 任务参数标签（Re 数、速度、构型名）

**阶段卡片列表**（可滚动）：

每个阶段是一张卡片，有三种状态：

**已完成（done）**：
- 绿色背景 header，✓ 图标
- 默认折叠，显示摘要（如"DARPA SUBOFF 裸体，5 m/s，Re=2.0M"）
- 右侧显示耗时
- 点击可展开查看详情

**进行中（active）**：
- 蓝色 header 背景 + 左侧 3px 蓝色边框
- 脉冲动画 ● 图标
- **默认展开**，显示：
  - 进度条（当前迭代 / 总迭代）
  - 指标 chip 行（Cd、Fx、耗时，`text-xl font-mono`）
  - Cd 收敛历史曲线（带面积填充，含收敛判断标记线）
  - 实时日志最后一行

**待执行（pending）**：
- 灰色 header，数字序号图标
- 折叠状态，文字变灰

#### 任务理解阶段（Stage 1）的特殊展开内容

当 stage 1 处于 active 状态时，展开内容为：

1. **检索结果**：找到的 N 个相似案例，每条显示匹配度%、案例名称、湍流模型、历史 Cd、与实验偏差
2. **建议计算方案**：琥珀色背景卡片，包含湍流模型 / 网格类型 / 求解器 / 预计耗时
3. **操作按钮**：`✓ 确认方案，开始执行` + `调整参数…`

流水线在用户点击确认前**不会自动推进**。

### 4.3 右侧 Claude Code 对话轨道（220~420px）

- Header：绿点在线指示 + "Claude Code" 标题
- 消息流：用户消息（蓝色气泡，右对齐）+ AI 消息（白色卡片，左对齐）
- AI 消息支持警告样式（琥珀色背景，⚠️ 前缀）
- 底部输入框
- 对话记录整个仿真过程，阶段切换时 AI 会自动推送状态更新

---

## 5. Skill Studio 工作台

通过 Activity Bar 🧩 切换，布局不同于仿真工作台。

### 5.1 左侧边栏

- 品牌：Skill Studio · SkillNet（紫色）
- 技能列表：每条显示技能名 + 启用/禁用彩色圆点
- 当前选中技能高亮（紫色背景）
- 底部：`+ 新建技能` 按钮（紫色背景）

### 5.2 中央区域 — 两种视图

#### 图谱视图（默认）

- 力导向 SVG 技能图谱
- 节点颜色编码：蓝=solver，绿=report，橙=geometry，灰=其他/禁用
- 节点半径：`max(12, min(28, 12 + relatedCount × 3))`（关联越多越大）
- 边颜色：`depend_on=#ef4444`，`compose_with=#a855f7`，`similar_to=#9ca3af`，`belong_to=#f59e0b`
- 悬停节点显示 tooltip（名称、类别、关联数）
- 点击节点 → 右侧打开属性检查器

**属性检查器**（图谱右侧 220px 面板）：
- 技能名称、类别、关联阶段、关系列表（带颜色标签）、状态、描述
- `✏️ 编辑此技能` 按钮（紫色）

#### 编辑器视图（点击"编辑此技能"后切换）

图谱区域整体替换为全宽技能编辑器：
- Header：`← 返回图谱` 链接 + 技能名 + "编辑中" badge（紫色）
- 左侧 Tab 导航（140px）：基本信息 / 输入参数 / 输出格式 / 技能关系 / 测试运行
- 右侧内容区：对应 Tab 的编辑表单
- 底部 Footer：`取消` + `保存技能` 按钮
- 保存后自动返回图谱视图，节点实时更新

### 5.3 右侧 Skill Creator 对话轨道

- 紫点在线指示 + "Skill Creator" 标题
- 运行 `claude-code-skill-creator` agent
- 用户可用自然语言描述修改意图，AI 直接操作编辑器字段
- 编辑器视图和图谱视图下均保持可见

---

## 6. 数据来源与状态

### 6.1 VibeCFD 状态

所有仿真状态来自 thread artifacts（`SubmarineRuntimeSnapshot`）：
- `current_stage`：当前阶段枚举值，驱动阶段卡片的 active/done/pending 状态
- `execution_plan`：8 阶段的执行计划，含每阶段描述
- `artifact_virtual_paths`：各阶段产出的 artifact 文件路径
- `simulation_requirements`：仿真参数（Re、速度、构型）
- `scientific_gate_status`：科学验证门控状态

### 6.2 Skill Studio 状态

来自 `core/skills/api.ts` 中的 SkillNet API：
- `SkillGraphNode`：`{ name, description, category, enabled, related_count, stage? }`
- `SkillGraphRelationship`：`{ source, target, relationship_type, score, reason }`
- TanStack Query 管理远程状态，技能保存后触发图谱 refetch

---

## 7. 交互细节

### 7.1 阶段卡片交互
- 已完成阶段：点击 header 展开/折叠详情（`useState` 控制）
- 进行中阶段：始终展开，不可折叠
- 任务理解阶段：确认方案按钮触发 `useSubmitThread` 提交确认消息

### 7.2 面板宽度持久化
- 用户拖动后宽度保存至 `localStorage`，刷新后恢复
- 拖动时用 `mousemove` 事件更新宽度，`mouseup` 时持久化

### 7.3 导航路由
- VibeCFD 仿真：`/workspace/submarine/[thread_id]`
- Skill Studio：`/workspace/skill-studio/[thread_id]`
- 普通对话：`/workspace/chats/[thread_id]`
- Activity Bar 切换通过 `useRouter().push()` 跳转，侧栏状态各自独立

---

## 8. 与现有代码的关系

本次重设计**替换**以下现有组件，不做修补式改造：

| 现有文件 | 处理方式 |
|----------|----------|
| `submarine-runtime-panel.tsx`（1779行） | 替换为新的 `SubmarineWorkbench` 组件树 |
| `skill-studio-dashboard.tsx` | 替换为新的 `SkillStudioWorkbench` 组件 |
| `workspace-sidebar.tsx`（shadcn Sidebar） | 仿真/Skill Studio 页面不使用原有侧边栏，改用自定义 Activity Bar + 专属侧栏 |
| `workspace-nav-menu.tsx` | 设置入口移入 Activity Bar ⚙️，原组件在新页面中弃用 |

`/workspace/chats/[thread_id]`（普通对话）页面保持原有布局不变，Activity Bar 的 💬 入口跳转至此。

---

## 9. 技术实现约束

- **框架**：Next.js 16 App Router，React 19，TypeScript 5.8，Tailwind CSS 4
- **技能图谱**：纯 SVG 力导向布局，不引入 d3（120 次迭代，Coulomb 斥力 + Hooke 引力 + 中心引力）
- **流数据**：通过现有 `useThreadStream` hook 订阅 LangGraph 流事件，不新增 WebSocket
- **组件目录**：新增文件放 `src/components/workspace/`，图谱组件 `skill-graph-canvas.tsx`
- **样式**：全用 Tailwind utility classes + `cn()` 辅助函数，不写内联 style（除动态值）
- **Server/Client 边界**：布局层 Server Component，交互组件加 `"use client"`
