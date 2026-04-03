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
| Component library | Radix primitives + 项目内 `workspace/*` 壳层组件 |
| Icon library | `lucide-react` |
| Font | `IBM Plex Sans`, `Noto Sans SC`, `PingFang SC`, `Microsoft YaHei`, sans-serif |

### Design System Rules

- 不新造平行 UI 框架，继续以现有 `shadcn + Radix + Tailwind v4` 为底座。
- Phase 7 的新增 UI 优先抽成共享 shell / layout / nav / state 组件，不允许继续把视觉逻辑塞进单页大组件。
- 所有工作区页面共享同一组壳层 token、容器节奏、状态样式和焦点样式。
- 在保证过程展示完整的前提下，默认视图必须简洁清爽；优先分层展示，不把全部过程模块一次性摊开。
- 运行中的工作流必须能在工作台内被实时监控，不能把实时状态只藏在聊天消息或外部终端里。
- `submarine` 保持研究操作主界面，不被“通用聊天页”替代。

---

## Information Architecture Contract

### Unified Sidebar

- 工作区采用 `整合侧栏 + 主工作区 + 可选聊天轨` 的统一结构，不再保留 `Activity Bar + 二级侧栏` 的双左栏形式。
- 左侧整合侧栏内部只分区，不分栏：
  - 顶部：工作台切换 `仿真 / Skill Studio / 对话 / 智能体`
  - 中部：当前工作台上下文对象列表
  - 下部：当前工作台局部页面导航与主 CTA
  - 底部：设置与次级入口
- 整合侧栏必须同时承担“一级入口”和“当前上下文目录”，但视觉上仍然是一块连续面板。

### Workspace Decomposition

- 主工作区默认进入 `总览`，只展示当前状态、关键指标、风险、下一步和核心产物入口。
- 高密度领域必须拆为可跳转子页或子视图，不把所有模块堆在同一屏：
  - `仿真`：`总览 / 运行时 / 产物 / 报告`
  - `Skill Studio`：`总览 / 构建 / 校验 / 测试 / 发布 / 图谱`
  - `对话`：`会话列表 / 会话内容`，不引入与聊天无关的工作台模块
  - `智能体`：`总览 / 详情 / 创建`，避免与 Skill Studio 共用工作流语义
- 总览页负责“看清现在”，子页负责“深入处理”，抽屉负责“临时协作或辅助信息”。
- 运行中的对象必须同时满足：
  - `总览` 可看到实时状态摘要
  - `运行时` 子页可看到完整过程监控
  - 聊天轨只做协作补充，不承担主监控职责

### Default Entry

- `/workspace` 默认进入“上次活跃工作台 + 上次活跃对象 + 上次活跃页面”。
- 若没有历史上下文，fallback 到 `/workspace/submarine/new`。

### Orientation Rules

- 一级定位通过整合侧栏顶部工作台切换完成。
- 二级定位通过侧栏中的对象高亮与页面导航高亮完成。
- 页面头部只承担对象标题、状态和关键操作，不承担全局导航职责。
- Breadcrumb 仅作辅助，不应比页面标题更强。

---

## Shell Layout Contract

| Region | Default | Range / Behavior | Contract |
|--------|---------|------------------|----------|
| Unified Sidebar | 296px | 272px - 320px | 单一整合侧栏，包含一级工作台切换、对象列表、页面导航、主 CTA |
| Main Workspace | auto | 最小 840px | 核心任务、证据、产物、状态必须在这里可读 |
| Chat Rail | 340px | 320px - 400px | 与当前工作流相关的协作轨道；不是解释页面用途的说明区 |
| Page Header | 64px | 紧凑态 56px | 标题、状态、关键 CTA、少量跳转 |
| Subpage Tabs | 44px | 溢出时可横向滚动 | 承担“总览与子页切换”，不再在首屏堆满所有模块 |
| Runtime Summary Strip | 72px - 96px | 仅在运行中对象出现 | 位于总览首屏顶部，显示阶段、最近更新时间、健康度、快捷跳转 |

### Surface-Specific Layout Rules

#### 仿真工作台

- 左侧整合侧栏展示：
  - 当前/历史仿真任务
  - 当前页面导航 `总览 / 运行时 / 产物 / 报告`
  - `新建仿真` 主 CTA
- `总览` 只展示：
  - 当前阶段
  - 关键指标摘要
  - 风险与阻塞
  - 主要产物入口
  - 下一步动作
- `总览` 必须额外提供一条紧凑的实时监控摘要，至少包含：
  - 当前运行阶段
  - 最近更新时间
  - 健康度或告警状态
  - 进入 `运行时` 页的快捷入口
- 详细日志、实时曲线、产物清单、报告内容进入对应子页，而不是全部堆在总览。
- `运行时` 子页专门承载：
  - 阶段流 / 时间线
  - 实时日志或关键事件流
  - 关键指标曲线与最新数值
  - 阻塞、重试、人工接管入口
- `产物` 子页专门承载：
  - 最新产物列表
  - 快照 / 指标 / 日志 / 导出物分类
  - 数据新鲜度与生成时间
  - 对比、打开、导出入口
- `产物` 页不重复承载完整运行时过程，只负责把“已经产出了什么、哪个可用、哪个需要重跑”讲清楚。
- `报告` 子页专门承载：
  - 报告骨架与章节完成度
  - 已绑定证据与待补证据
  - 审阅状态
  - 导出与交付动作
- `报告` 页不重新展示完整产物矩阵；它负责把证据组织成可交付叙事，而不是再做一层文件浏览器。

#### Skill Studio

- 左侧整合侧栏展示：
  - 最近 skill 线程
  - 当前页面导航 `总览 / 构建 / 校验 / 测试 / 发布 / 图谱`
  - `新建 Skill 线程` 主 CTA
- `总览` 只展示：
  - 当前准备度
  - blocking items
  - 最近验证结果
  - 发布门槛
- `构建` 子页专门承载：
  - skill 包结构与关键文件完整度
  - 依赖与 registry 引入状态
  - 模板 / 片段 / 入口配置
  - 下一步进入校验的准备度
- `构建` 页不提前给出“是否可发布”的最终判断，只负责把构成是否齐全讲清楚。
- `校验` 子页专门承载：
  - 当前验证结论
  - 阻塞项与风险等级
  - 证据与覆盖情况
  - 修复后下一步动作
- `校验` 页不展示完整图谱、不承接发布动作，只负责把“能不能继续往下走”讲清楚。
- `测试` 子页专门承载：
  - 测试矩阵
  - 通过 / 失败 / 缺失用例
  - 重跑与补测动作
  - 回归风险提示
- `测试` 页不重复解释构建细节，也不承担发布确认职责。
- `发布` 子页专门承载：
  - 发布准备度
  - 影响范围
  - 干跑 / 回滚 / 确认动作
  - 发布后监控入口
- `发布` 页必须把高影响节点、受影响对象和确认门槛放在首屏，而不是把这些信息埋在按钮之后。
- `图谱` 明确定义为 `Skill 图谱` 页面，用于展示：
  - skill 之间的依赖关系
  - 触发条件与调用链
  - 上游 / 下游影响面
  - 发布后可能影响的对象
- `图谱` 视觉上应采用真正的网络图表达，而不是静态方块列表：
  - 当前 skill 作为主节点高亮
  - 上游 / 下游 / 相似 / 归属节点围绕主节点分层排布
  - 连线或边标签用于表达 `depend_on / compose_with / belong_to / similar_to`
- `总览` 只保留 `Skill 图谱入口` 或极小型预览，不在首屏常驻大图谱。
- `构建 / 校验 / 测试 / 发布 / 图谱` 各自承载深层信息，避免单屏堆满 package、graph、tests、publish gate。

#### 通用对话

- 左侧整合侧栏展示最近会话和必要筛选。
- 主区优先保证消息流、输入区和上下文跳转稳定，不引入多余说明块。
- 若线程带有 `submarine_runtime` 等上下文，只提供简洁跳转入口，不把聊天页改造成工作台页。
- 紧凑态下，对话工作台优先保留：
  - 消息流
  - 当前会话标题
  - 已挂载上下文 chips
  - 输入区
- 会话列表与上下文轨在紧凑态下都退化为抽屉，不与消息主区并列挤压。

#### 智能体

- 左侧整合侧栏展示智能体列表、筛选和创建入口。
- 主区分为 `总览 / 详情 / 创建`，不复用 Skill Studio 的任务语义。
- `详情` 子页专门承载：
  - 当前运行状态与最近执行轨迹
  - 权限 / 资源 / 边界
  - 关联工作台与线程
  - 人工接管与审计入口
- `创建` 子页专门承载：
  - 模板选择
  - 能力范围与权限
  - 关联工作台 / 数据源
  - 创建前预览与确认
- 智能体紧凑态下，详情与创建都应退化为单列主区 + 抽屉式辅助区，不再保留持续展开聊天轨。

---

## Responsive Behavior

### Desktop Wide `>= 1440px`

- 使用 `整合侧栏 / 主工作区 / 聊天轨` 三段式布局。
- `仿真` 与 `Skill Studio` 的聊天轨可默认展开，但不得压缩主区到不可读。
- 总览页允许双列摘要卡，但详细模块仍通过子页承载。

### Laptop `1280px - 1439px`

- 保留 `整合侧栏 / 主工作区`。
- 聊天轨默认折叠为右侧抽屉或显式切换按钮。
- 总览页回落为单列优先，避免信息断裂。
- 实时监控摘要仍保留在首屏，不能因为宽度收紧而完全折叠消失。

### Compact Desktop `1024px - 1279px`

- 左侧整合侧栏改为抽屉或可折叠窄态，不长期占位。
- 页面头部必须保留标题、当前状态、`导航` 触发器和 `聊天` 触发器。
- 继续坚持“总览 + 子页”，不因为空间变小而把所有模块重新堆回单页。

### Mobile `< 1024px`

- 允许单列堆叠，但必须可用。
- 侧栏与聊天轨均改为 sheet / drawer。
- 输入区与主 CTA 保持 sticky。
- 不为 mobile 额外发明新工作流，只做顺序重排。
- 实时监控摘要优先级高于辅助说明块，移动端也必须保留。

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
| 3xl | 48px | 页面首屏留白、主要板块分隔 |

Exceptions: `64px` Page Header, `72px` 首屏 hero / launchpad 垂直起始留白

### Spacing Rules

- 一级页面不允许同时出现 `px-4 / px-6 / px-8` 的随意混搭；同一页只保留一组主容器横向节奏。
- 总览页首屏优先使用 `12 / 16 / 24` 的紧凑节奏，不用大段说明把卡片拉长。
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

- 中文为第一阅读语言，正文优先保证连续阅读与扫描效率。
- 所有数值密集区域使用 tabular numerals。
- 页面标题、阶段标题、模块标题统一使用 `Heading` 系列，不单独再发明“大标题艺术字”。
- 说明文字默认 14px，不再出现大段 12px 正文。

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#F7F4EE` | 工作区背景、空白面、页面基底 |
| Secondary (30%) | `#FFFFFF` | 卡片、侧栏面板、浮层、聊天轨 |
| Accent (10%) | `#0E8ACF` | 当前导航、高亮状态、焦点环、主 CTA、关键数据强调 |
| Destructive | `#C94F4F` | 删除、清理、不可逆确认 |

Accent reserved for: 当前工作台激活态、当前阶段、主按钮、焦点环、主图表主序列、关键状态提示；不得用于所有链接、所有按钮、所有 badge。

### Support Colors

- Success: `#2F8F5B`
- Warning: `#C58A1D`
- Info: `#3C6FE1`
- Neutral text secondary: `#6B7280`
- Neutral border: `#DDD6C8`

### Color Rules

- 工作区整体采用“暖中性色 + 冷蓝强调”，不让每个页面各自发明主色。
- `Skill Studio` 可以有轻微的表面身份差异，但只允许出现在 eyebrow、微徽标、辅助 badge。
- 背景与卡片层级依赖明度和边框，不依赖重阴影堆叠。

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Page title | `对象名 + 当前状态 / 页面用途` |
| Primary CTA | `动词 + 对象`，如 `新建仿真` / `发布 Skill` |
| Tabs / nav labels | 名词或短语，优先 2-6 个汉字 |
| Empty state heading | 直接说明状态，如 `还没有仿真任务` |
| Empty state body | 一句话说明缺什么，以及下一步 |
| Destructive confirmation | 必须写清影响范围与不可撤销性 |

### Copy Rules

- 中文优先，品牌名和明确产品名词可保留英文，如 `Skill Studio`、`OpenFOAM`、`Agent`。
- 不解释显而易见的控件功能，不写“这里可以聊天”“这里可以切换标签”“这里可以输入内容”这类说明。
- 辅助文案只在以下场景出现：状态、风险、前置条件、不可逆影响、下一步动作。
- 侧栏列表项默认只保留对象名、状态、时间，不写完整说明句。
- 聊天轨标题区只保留对象名、角色名、在线状态，不附带用途介绍。
- 一个首屏最多只允许一个解释性段落；若能用标签、badge、状态卡表达，就不要再写段落。
- 所有长期存在的 UI 文案必须走 i18n key，不允许把核心导航、标题、dialog 文案继续硬编码在组件里。

### Locked Surface Labels

- 一级入口：`仿真` / `Skill Studio` / `对话` / `智能体`
- 仿真子页：`总览` / `运行时` / `产物` / `报告`
- Skill Studio 子页：`总览` / `构建` / `校验` / `测试` / `发布` / `图谱`
- 阶段类标签使用直接名词：`任务理解` / `几何预检` / `求解执行` / `结果整理` / `主管复核`

---

## Interaction and State Contract

### Focus and Accessibility

- 所有可键盘聚焦元素必须有 `2px` 可见焦点环，颜色使用 accent。
- 主按钮、侧栏激活项、Tab、Dialog confirm action 都必须可键盘操作。
- 颜色不是唯一状态来源；运行中、错误、完成都必须同时有文字标签。

### Loading / Empty / Error

- Loading 优先使用 skeleton，不只给 spinner。
- Empty state 必须给下一步 CTA，但文案保持简洁。
- Error state 必须解释问题发生在哪一层，并给出一条明确下一步。

### Live Monitoring

- 运行中的对象必须在工作台内自动刷新状态，不依赖用户手动刷新才能看到进展。
- `总览` 只展示紧凑监控摘要；完整监控细节进入 `运行时` 子页。
- `运行时` 子页必须同时提供：
  - 阶段流向
  - 最新事件
  - 指标变化
  - 数据新鲜度时间戳
- 当数据停止更新或运行异常时，界面必须明确显示 `更新中断`、`等待人工确认` 或同等级别状态，而不是静默停住。
- 聊天轨里的 agent 回复可以解释上下文，但不能替代主工作区的运行监控。

### Skill Graph Interaction

- `图谱` 页必须支持至少一组轻量筛选：
  - `全部`
  - `上游`
  - `下游`
  - `相似`
  - `高影响`
- 连线样式应具备稳定语义，不同关系不能只靠节点文字区分：
  - `depend_on`: 实线、冷色强调
  - `compose_with`: 实线、次级强调
  - `belong_to`: 虚线、中性语义
  - `similar_to`: 点线或弱虚线、弱强调
- 点击节点后，主画布必须同步高亮该节点及其直接边，非关联节点降噪。
- 右侧详情区必须响应当前选中节点，至少显示：
  - 节点名与类型
  - 直接上游 / 下游
  - 关系类型汇总
  - 影响面或发布提示
- 图谱页的默认状态应选中当前 skill 主节点，而不是让用户先面对一张无焦点的大网。
- 图谱画布必须支持桌面端拖拽平移；触控板或滚轮缩放不能破坏节点可读性。
- 图谱页必须提供显式视图控制：`适应画布`、`重置视图`、`- / 当前缩放比例 / +`。
- 首次进入图谱页时，当前 skill 主节点默认位于主视口中心附近；当用户从列表或详情区跳转到屏外节点时，可自动居中一次。
- 宽桌面默认显示小地图与当前视口框；较窄笔记本宽度可以折叠小地图，但不能移除“当前所见区域”这一能力。
- 右侧详情区应明确显示当前选中节点，避免用户在缩放或拖拽后失去焦点对象。
- 图谱默认只展开当前选中节点的一跳关系；二跳关系必须按需展开，不能默认把整张图一次性铺满。
- 二跳展开应以“当前分支”为单位，而不是全图同时展开；从 `report-writer` 展开二跳时，不应顺带把无关支路全部展开。
- 当选中节点存在可扩展的二跳关系时，界面应提供轻量入口，例如节点旁的 `+2`、详情区计数或工具栏按钮，而不是直接塞入更多节点。
- 切换 `上游 / 下游 / 相似 / 高影响` 筛选时，当前选中节点必须保持可见并尽量保持原位置，避免用户每切一次都重新找焦点。
- 筛选切换优先使用“弱化非命中关系 -> 收起非命中关系”的方式，避免整张图突然重排造成空间跳变。
- 如果当前筛选下没有匹配关系，主节点仍需保留在画布中，右侧说明明确显示“无匹配关系”，而不是给用户一个空白画布。
- 点击非主节点后，图谱焦点应切换到该节点；原主节点若与其直接相关，应保留为上下文锚点，而不是完全消失。
- 节点切换时，右侧详情区只更新当前节点相关信息，不应因为字段长度差异导致整块面板明显跳高或跳宽。
- 当前选中节点若在筛选态下“无更多命中关系”，界面应同时保留：
  - 当前选中节点
  - 至少一个上下文锚点
  - 一条简洁空状态提示
- 空状态提示必须短，不解释基础控件；只说明“当前筛选下无更多关系”以及提供下一步动作，例如：
  - `返回全部`
  - `切换到上游 / 下游`
  - `查看当前节点详情`
- 空状态不能替换整个图谱页，只能作为当前筛选态下的局部反馈；用户仍应知道自己在图谱中的位置。

### Graph Accessibility

- 图谱页必须支持键盘导航，且不能只对工具栏可达：
  - `Tab` 在工具栏、筛选、图谱画布、详情区之间移动
  - 进入画布后，使用方向键在当前可见节点之间移动焦点
  - `Enter / Space` 选中当前焦点节点
- 当节点存在可展开二跳时，键盘可直接触发该动作；优先使用当前节点旁的展开入口或详情区按钮，不引入额外隐藏快捷键依赖。
- 节点焦点态、选中态、筛选态必须同时具备非颜色信号，例如：
  - 焦点环
  - 边框变化
  - 状态标签
- 右侧详情区或底部详情抽屉更新时，标题区必须立即反映当前选中节点，避免键盘用户失去上下文。
- 小地图若折叠，必须有可聚焦入口；若展开，不要求成为主要键盘导航路径。

### Graph Responsive Behavior

- 宽桌面保持 `图谱画布 + 右侧详情` 双列；图谱画布优先级高于详情区。
- 笔记本宽度下，图谱页应退化为：
  - 图谱画布仍作为主区
  - 详情区下移为主区下方卡片或底部抽屉
  - 小地图折叠为轻量入口，不持续占画布角落
- 窄宽度下，筛选行和图谱工具栏允许分两行，但第一行必须优先保留：
  - 当前选中节点
  - 当前筛选
  - 返回主视图的动作
- 紧凑态下，空状态反馈优先嵌入详情卡片或底部抽屉，而不是覆盖图谱画布中央。
- 紧凑态下若聊天轨存在，默认折叠；图谱页不能与聊天轨并列挤压主画布。

### Wireframe Coverage

- 当前已完成可视化草图的一级工作台 / 关键页面：
  - `仿真总览`
  - `仿真运行时`
  - `仿真产物`
  - `仿真报告`
  - `Skill Studio 总览`
  - `Skill Studio 构建`
  - `Skill Studio 校验`
  - `Skill Studio 测试`
  - `Skill Studio 发布`
  - `Skill 图谱桌面版`
  - `Skill 图谱笔记本态`
  - `对话工作台桌面版`
  - `对话工作台紧凑态`
  - `智能体工作台桌面版`
  - `智能体详情`
  - `智能体创建`
  - `智能体紧凑态`
  - `紧凑版总览`
- 当前已补齐的跨页状态：
  - 工作区首次进入 / 无历史上下文
  - 权限不足
  - 数据中断
  - 更新失败
- 当前 Phase 7 UI 设计覆盖已闭环，可直接进入 planning / implementation。

### Motion

- 页面壳层和面板切换使用 `120ms - 180ms` 过渡。
- 禁止长时间浮夸动画；运动只用于强化方向感和层级切换。
- 侧栏、抽屉、聊天轨切换使用同一套 easing 曲线。

### Overview and Subpage Behavior

- 总览首屏只显示摘要，不展示完整日志流、完整产物列表、完整图关系、完整测试矩阵。
- 深层内容必须进入子页、抽屉或可展开区，而不是默认铺满首屏。
- 聊天轨只在协作有价值时出现，不承担教学说明职责。
- 当前阶段、风险和下一步必须在总览首屏直接可见。

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | `button`, `card`, `badge`, `tabs`, `dialog`, `sheet`, `sidebar`, `resizable`, `tooltip`, `select`, `progress`, `alert`, `input`, `textarea`, `breadcrumb`, `scroll-area`, `separator` | not required |
| `@ai-elements` | prompt input related blocks | shadcn view + diff required |
| `@magicui` | decorative / presentational blocks only | shadcn view + diff required |
| `@react-bits` | non-core visual enhancement blocks only | shadcn view + diff required |

### Registry Rules

- 第三方 registry 组件不能直接进入 shell、nav、dialog、sidebar 这类核心结构层。
- 所有第三方块进入 workspace 前，必须先过：
  - 视觉 token 对齐
  - keyboard / focus 检查
  - 中英文案密度检查

---

## Implementation Notes for Planner

- 优先产出共享壳层 primitives：
  - `WorkspaceSidebar`
  - `WorkspaceNavSwitcher`
  - `WorkspaceObjectList`
  - `WorkspaceSubpageTabs`
  - `WorkspacePageHeader`
  - `WorkspaceSurfaceShell`
  - `WorkspaceRuntimeSummaryStrip`
  - `WorkspaceRuntimeTimeline`
  - `WorkspaceLiveMetricCard`
  - `WorkspaceChatRail`
  - `WorkspaceDrawerTrigger`
- 图谱页建议拆出独立 primitives：
  - `WorkspaceGraphCanvas`
  - `WorkspaceGraphToolbar`
  - `WorkspaceGraphMinimap`
  - `WorkspaceGraphDetailPanel`
  - `WorkspaceGraphEmptyState`
  - `WorkspaceGraphDetailSheet`
- 图谱状态建议显式建模为：
  - `selectedNodeId`
  - `activeRelationFilter`
  - `expansionDepth`
  - `viewportTransform`
- `submarine` 与 `skill-studio` 需要从“单页堆模块”改造成“总览 + 子页 / 子视图”的结构。
- `workspace-container.tsx` 的 breadcrumb/header contract 需要降级为辅助结构，由新的 page-shell 接管主导航语义。
- 现有解释型硬编码文案是 Phase 7 的显式清理目标，尤其是聊天框、标签、输入区这类显而易见控件周围的说明句。

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-04-03
