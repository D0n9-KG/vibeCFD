---
phase: 7
slug: workspace-ux-and-navigation-system
status: approved
shadcn_initialized: true
preset: new-york / neutral / workspace-custom
created: 2026-04-03
---

# Phase 7 - UI Design Contract

> Workspace UX and Navigation System 的视觉与交互合同。用于在进入 `gsd-plan-phase 7` 之前锁定 IA、页面壳层、响应式行为、中文文案与设计系统边界。

---

## Design System

| Property | Value |
|----------|-------|
| Tool | shadcn/ui |
| Preset | `new-york`，基于 `neutral`，叠加 VibeCFD 工作区自定义 token |
| Component library | Radix primitives + 项目内 `workspace/*` 领域壳层组件 |
| Icon library | `lucide-react` |
| Font | `IBM Plex Sans`, `Noto Sans SC`, `PingFang SC`, `Microsoft YaHei`, sans-serif |

### Design System Rules

- 不新造平行 UI 框架，继续以现有 `shadcn + Radix + Tailwind v4` 为底座。
- Phase 7 的新增 UI 优先抽成共享 shell / layout / nav / status 组件，不允许把视觉逻辑继续塞进单页大组件。
- 所有工作区页面共享同一组壳层 token、容器节奏、状态样式和焦点样式。
- `submarine` 保持研究操作主面，不被“通用聊天页”替代。

---

## Information Architecture Contract

### Top-Level Navigation

- 工作区采用 `Activity Bar + 二级侧栏 + 主工作区 + 右侧聊天轨` 的统一架构。
- Activity Bar 固定包含 4 个一级入口：
  - `仿真`
  - `Skill Studio`
  - `对话`
  - `智能体`
- `设置` 固定在 Activity Bar 底部，不与一级业务入口混排。

### Secondary Sidebar Role

- 二级侧栏只展示“当前工作台相关对象”，不再混放全局导航与局部导航。
- 二级侧栏是“当前上下文目录”，不是第二个 Activity Bar。
- 对象分布规则：
  - `仿真`: 运行中的/已完成的仿真任务、阶段定位、主操作入口
  - `Skill Studio`: 最近 skill 线程、工作台入口、图谱/工作台视图入口
  - `对话`: 最近对话列表
  - `智能体`: 智能体列表、创建入口、最近 agent 线程

### Default Entry

- `/workspace` 默认进入“上次活跃工作台 + 上次活跃线程”。
- 若没有历史上下文，fallback 到 `/workspace/submarine/new`。

### Orientation Rules

- 一级定位靠 Activity Bar 完成。
- 二级定位靠侧栏标题 + 当前对象高亮完成。
- 页面头部只做当前对象标题、状态、关键操作，不承担全局导航职责。
- Breadcrumb 仅作为辅助方向提示，不应比对象标题更强。

---

## Shell Layout Contract

| Region | Default | Range / Behavior | Contract |
|--------|---------|------------------|----------|
| Activity Bar | 56px | 固定宽度 | 只放一级入口与设置，图标优先，文字通过 tooltip / active label 辅助 |
| Secondary Sidebar | 272px | 240px - 320px | 当前工作台局部导航，支持拖拽调整 |
| Main Workspace | auto | 最小 720px | 核心任务、证据、产物、状态都应在这里可读 |
| Chat Rail | 360px | 320px - 440px | 与主工作流相关的 lead-agent 对话，不得吞掉主任务区 |
| Page Header | 64px | 紧凑态 56px | 标题、状态、关键 CTA、产物入口 |

### Surface-Specific Layout Rules

#### 仿真工作台

- 左侧二级栏展示：
  - 当前/历史仿真任务
  - 当前阶段列表
  - `新建仿真` 主 CTA
- 主区展示：
  - 任务摘要
  - 当前阶段
  - 证据状态
  - 阶段卡片流
  - 关键产物入口
- 右侧聊天轨保留为专用协作轨道，桌面端默认可见。

#### Skill Studio

- 左侧二级栏展示：
  - 最近 skill 线程
  - `仪表盘 / 当前工作台` 两级视图
  - `新建 Skill 线程` CTA
- 主区展示：
  - package / validation / tests / publish readiness / graph 等工作台模块
- 右侧聊天轨为专属 Skill Creator 对话，不出现 CFD 运行信息。

#### 通用对话

- 左侧二级栏展示最近对话。
- 主区优先保证消息流与输入区稳定，不引入额外复杂分栏。
- 若线程带有 `submarine_runtime` 上下文，可出现“进入仿真工作台”跳转，但不把对话页变成仿真页。

#### 智能体

- 左侧二级栏展示智能体列表、筛选与 `新建智能体`。
- 主区为 gallery / detail / create shell，不与 Skill Studio 的工作台语言混用。

---

## Responsive Behavior

### Desktop Wide `>= 1440px`

- 使用完整四区布局：`Activity Bar / Secondary Sidebar / Main / Chat Rail`。
- `仿真` 与 `Skill Studio` 的聊天轨默认展开。
- 阶段卡片和工作台模块允许双列。

### Laptop `1280px - 1439px`

- 保留 `Activity Bar / Secondary Sidebar / Main`。
- 聊天轨默认折叠为右侧抽屉或显式切换按钮，不长期挤压主区。
- `仿真` 阶段卡片回落为单列优先，避免主区信息断裂。

### Compact Desktop `1024px - 1279px`

- Activity Bar 保留。
- 二级侧栏改为抽屉 / sheet。
- 聊天轨不常驻，只通过按钮召回。
- 页面头部必须仍能保留标题、当前状态和主 CTA。

### Mobile `< 1024px`

- 允许单列堆叠，但必须可用。
- 聊天轨、二级侧栏全部改为 sheet。
- 输入区与主 CTA 维持 sticky。
- 不为 mobile 额外发明新工作流，只做桌面壳层的顺序重排。

---

## Spacing Scale

Declared values (all multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | 图标与文字微间距、状态点、紧凑分隔 |
| sm | 8px | chip、按钮内边距、微型卡片间距 |
| md | 12px | 卡片内分组、列表项内部节奏 |
| lg | 16px | 默认控件间距、表单区块、标题下留白 |
| xl | 24px | 页面 section 内边距、双栏块间距 |
| 2xl | 32px | 工作台模块之间的主级间距 |
| 3xl | 48px | 页面首屏留白、主要版块分隔 |

Exceptions: `56px` Activity Bar, `64px` Page Header, `72px` 首屏 hero / launchpad 垂直起始留白

### Spacing Rules

- 一级页面不允许同时出现 `px-4 / px-6 / px-8` 的随意混搭；同一页只保留一组主容器横向节奏。
- 卡片内部优先使用 `12 / 16 / 24` 三档，不使用 14、18、22 这类游离值。
- 可拖拽分栏之间的视觉间距固定，不因页面类型漂移。

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14px | 400 | 1.7 |
| Label | 12px | 600 | 1.45 |
| Heading | 20px | 600 | 1.3 |
| Display | 32px | 600 | 1.15 |

### Typography Rules

- 中文为第一阅读语言，正文优先保证连续阅读与扫描效率，不追求过强展示感。
- 所有数值密集区域使用 tabular numerals。
- 页面标题、阶段标题、模块标题统一使用 `Heading` 系列，不允许单页自定义另一套“大标题美术字”。
- 说明文字默认 14px，不再出现大段 12px 正文。

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#F7F4EE` | 工作区背景、空白面、页面基底 |
| Secondary (30%) | `#FFFFFF` | 卡片、侧栏面板、浮层、聊天轨 |
| Accent (10%) | `#0E8ACF` | 当前导航、高亮状态、焦点环、主 CTA、关键数据强调 |
| Destructive | `#C94F4F` | 删除、清理、不可逆确认 |

Accent reserved for: 当前工作台激活态、当前阶段、主按钮、焦点环、主图表主序列、关键状态提示；不得用于所有链接、所有按钮、所有 badge

### Support Colors

- Success: `#2F8F5B`
- Warning: `#C58A1D`
- Info: `#3C6FE1`
- Neutral text secondary: `#6B7280`
- Neutral border: `#DDD6C8`

### Color Rules

- 工作区整体采用“暖中性色 + 冷蓝强调”，不让每个页面各自发明主色。
- `Skill Studio` 可以有轻微的表面身份差异，但只允许出现在 eyebrow、微徽标、辅助 badge，不重新定义整套品牌色。
- 背景与卡片层级依赖明度和边框，不依赖重阴影堆叠。

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | `动词 + 对象`，如 `新建仿真` / `新建 Skill 线程` / `新建智能体` |
| Empty state heading | `还没有开始` / `还没有内容` 这类直接状态句，不使用营销式标题 |
| Empty state body | 必须说明当前缺什么，以及下一步怎么开始 |
| Error state | `当前问题 + 建议下一步`，例如“当前步骤未完成，请先处理几何预检中的阻塞项。” |
| Destructive confirmation | `删除 {对象名} 后，将同时清理相关对话、上传文件和产物，此操作不可撤销。` |

### Copy Rules

- 中文优先，品牌名和明确产品名词可保留英文，如 `Skill Studio`、`OpenFOAM`、`Agent`。
- 页面标题不使用口号式文案，只使用“对象名 + 当前状态 / 用途”。
- 按钮标签最多 8 个汉字；超过时改成标题 + 说明，不把长句塞进按钮。
- 所有长期存在的 UI 文案必须走 i18n key，不允许把核心导航、标题、dialog 文案继续硬编码在组件里。

### Locked Surface Labels

- 一级入口：`仿真` / `Skill Studio` / `对话` / `智能体`
- 仿真主面标题语义：`任务名 + 当前研究状态`
- Skill Studio 主面标题语义：`技能名 + 当前准备度`
- 阶段类标签使用直接名词：`任务理解` / `几何预检` / `求解执行` / `结果整理` / `主管复核`

---

## Interaction and State Contract

### Focus and Accessibility

- 所有可键盘聚焦元素必须有 2px 可见焦点环，颜色使用 accent，不可透明。
- 主按钮、拖拽手柄、侧栏激活项、tab、dialog confirm action 都必须可键盘操作。
- 颜色不是唯一状态来源；运行中、错误、完成都必须同时有文字标签。

### Loading / Empty / Error

- Loading 优先使用 skeleton，不只给 spinner。
- Empty state 必须给下一步 CTA。
- Error state 必须解释“问题发生在哪一层”，至少区分：
  - 页面加载失败
  - 数据为空
  - 当前流程被阻塞
  - 不可逆操作确认

### Motion

- 页面壳层和面板切换使用 `120ms - 180ms` 过渡。
- 禁止长时浮夸动画；运动只用于强化方向感和层级切换。
- Activity Bar、二级侧栏、聊天轨切换使用同一条 easing 曲线。

### Stage and Workbench Behavior

- 仿真阶段流中，`当前阶段` 默认展开，已完成阶段默认折叠，未开始阶段默认折叠。
- 证据状态、产物入口、下一步建议必须在首屏摘要可见，不藏进二级 tab。
- Skill Studio 的 `validation / tests / publish` 不得只在聊天消息里体现，必须在工作台主区可见。

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | `button`, `card`, `badge`, `tabs`, `dialog`, `sheet`, `sidebar`, `resizable`, `tooltip`, `select`, `progress`, `alert`, `input`, `textarea`, `breadcrumb`, `scroll-area`, `separator` | not required |
| `@ai-elements` | prompt input related blocks | shadcn view + diff required |
| `@magicui` | decorative / presentational blocks only | shadcn view + diff required |
| `@react-bits` | non-core visual enhancement blocks only | shadcn view + diff required |

### Registry Rules

- 第三方 registry 组件不能直接进入 shell、nav、dialog、sidebar、stage card 这类核心结构层。
- 所有第三方块进入 workspace 前，必须先过：
  - 视觉 token 对齐
  - keyboard / focus 检查
  - 暗色模式与浅色模式检查
  - 中文文案密度检查

---

## Implementation Notes for Planner

- 优先产出共享壳层 primitives：
  - `WorkspaceActivityBar`
  - `WorkspaceSecondarySidebar`
  - `WorkspacePageHeader`
  - `WorkspaceSurfaceShell`
  - `WorkspaceChatRail`
  - `WorkspaceStatePanel`
- `submarine` 与 `skill-studio` 的聊天轨行为应复用同一套 rail contract，不再各写一套开关和宽度规则。
- `workspace-container.tsx` 的 breadcrumb/header contract 需要降级为辅助结构，由新的 page-shell 接管主导语义。
- 现有硬编码中文文案是 Phase 7 的显式清理目标，不视为“以后再说”的小问题。

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-04-03
