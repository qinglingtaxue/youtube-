# cog.md 文档拆分决策记录

> 日期：2026-02-04
> 状态：已完成（二次拆分）
> 关联文档：cog.md, cog-collect.md, cog-process.md, cog-impl.md, cog-data.md, cog-context.md

---

## 决策背景

cog.md 作为认知模型的核心文档，随着项目迭代不断膨胀，从最初的几百行增长到 **1887 行**。这导致了以下问题：

| 问题 | 影响 |
|------|------|
| 文档过长 | AI 上下文窗口占用大，查找困难 |
| 职责混杂 | 核心实体、实现细节、上下文混在一起 |
| 维护困难 | 修改一处需要滚动很久找位置 |
| 阅读负担 | 新人入门不知道从哪里开始读 |

---

## 拆分历程

### 第一轮拆分：按阅读场景

**目标**：将 1887 行的单一大文件按「阅读场景」拆成 4 个文件

| 文档 | 职责 | 行数 |
|------|------|------|
| cog.md | 核心实体 + 关系定义 | 1108 |
| cog-impl.md | API/CLI/脚本/代码映射 | 189 |
| cog-data.md | 数据生命周期与存储策略 | 165 |
| cog-context.md | 业务/用户/技术背景 | 198 |

**核心文件压缩效果**：41% 减少（1887 → 1108）

### 第二轮拆分：按领域边界

**问题**：第一轮拆分后，cog.md 仍有 1108 行，包含三类不同领域的实体混杂在一起：
- 数据采集实体（CompetitorVideo, Channel 等）
- 数据加工实体（ContentQuadrant, InsightCard, ArbitrageReport 等）
- 工作流实体（Video, Task, Script 等）

**决策**：将核心实体按「数据流方向」进一步拆分

```
采集（从哪来）→ 加工（怎么变）→ 工作流（怎么用）
```

| 新文档 | 职责 | 实体数 | 行数 |
|--------|------|--------|------|
| **cog-collect.md** | 数据采集层：数据从哪来 | 6 | 177 |
| **cog-process.md** | 数据加工层：数据→图表→报告 | 19 | 676 |
| cog.md（精简后） | 核心索引 + 工作流实体 + 枚举 | 9 | 362 |

---

## 核心设计原则

### 原则 1：按数据流方向拆分

**问题**：原 cog.md 包含了 5 种不同类型的内容
- 实体定义（CompetitorVideo, Channel, Task...）
- 实现映射（API、CLI、脚本）
- 数据策略（生命周期、存储）
- 上下文信息（业务、用户、技术背景）
- UI 设计原则（用户认知、页面结构）

**决策**：第一轮按「阅读场景」拆分，第二轮按「数据流方向」再拆

| 文档 | 职责 | 阅读场景 |
|------|------|----------|
| **cog.md** | 核心索引 + 工作流实体 + 枚举 | 理解全局结构 |
| **cog-collect.md** | 数据采集实体与关系（6 个实体） | 开发采集功能时 |
| **cog-process.md** | 数据加工实体与关系（19 个实体） | 开发分析/可视化时 |
| **cog-impl.md** | API/CLI/脚本/代码映射 | 开发实现时 |
| **cog-data.md** | 数据生命周期与存储策略 | 处理大规模数据时 |
| **cog-context.md** | 业务/用户/技术背景 | 新人入门时 |

---

### 原则 2：核心文档极致精简

**问题**：AI 每次对话都需要加载 cog.md，行数越少 token 消耗越低

**决策**：核心 cog.md 只保留索引 + 工作流 + 枚举，领域实体全部外迁

```
第一轮拆分：1887 → 1108 行（压缩 41%）
第二轮拆分：1108 →  362 行（压缩 67%）
总压缩效果：1887 →  362 行（压缩 81%）
```

**cog.md 保留的内容**（必须在核心文件中）：
- 文档索引（6 个子文档 + 2 个 Skill 文档的导航）
- 核心认知摘要（有趣度公式、用户旅程）
- 实体总览清单（三层分类：采集层、加工层、工作流层）
- 工作流实体定义（Video, Task, TaskState, Analytics, Script, Spec）
- 流程实体定义（WorkflowStage, Agent, Skill）
- 枚举类型定义（VideoStatus, Privacy, Stage, TaskStatus 等）
- 工作流关系定义

**移出到 cog-collect.md 的内容**：
- CompetitorVideo 实体
- Channel 实体
- TrendSnapshot 实体
- SearchPanel 实体
- MonitorTask 实体
- TrendingTracker 实体
- 采集关系定义

**移出到 cog-process.md 的内容**：
- 分析框架实体（ContentQuadrant, DurationMatrix）
- 可视化实体（InsightCard, ReasoningChain, ChartCognitionMapping）
- 套利分析实体（ArbitrageReport, KeywordNetwork, BridgeTopic, CreatorProfile, ArbitrageOpportunity）
- 模式分析实体（PatternAnalysis, PatternReport, PatternDetail, LearningPath）
- 报告实体（AnalysisReport, MarketReport, OpportunityReport, DiagnoseReport）
- 交互实体（RankingList）
- 所有加工层关系定义

---

### 原则 3：索引优先

**问题**：6 个文件拆分后，用户不知道内容在哪个文件

**决策**：在 cog.md 顶部添加文档索引 + 实体总览

```markdown
## 文档索引

| 文档 | 内容 | 何时阅读 |
|-----|-----|---------|
| **cog.md**（本文档） | 核心索引、工作流实体、枚举定义 | 理解全局结构 |
| cog-collect.md | 数据采集实体与关系（6 个实体） | 开发采集功能时 |
| cog-process.md | 数据加工实体与关系（19 个实体） | 开发分析/可视化时 |
| cog-impl.md | API/CLI/脚本/代码映射 | 开发实现时 |
| cog-data.md | 数据生命周期与存储策略 | 处理大规模数据时 |
| cog-context.md | 业务/用户/技术背景 | 新人入门时 |
```

**实体总览清单**（cog.md 中保留三层分类汇总）：

```markdown
**数据采集层**（详见 cog-collect.md）
- CompetitorVideo, Channel, TrendSnapshot, SearchPanel, MonitorTask, TrendingTracker

**数据加工层**（详见 cog-process.md）
- 分析框架：ContentQuadrant, DurationMatrix, ArbitrageFramework, PatternAnalysis
- 可视化：InsightCard, ReasoningChain, ChartCognitionMapping...
- 套利：KeywordNetwork, BridgeTopic, ArbitrageOpportunity, CreatorProfile
- 报告：AnalysisReport, MarketReport, OpportunityReport, ArbitrageReport...
- 导航：RankingList, PatternDetail, LearningPath, CreatorDashboard

**工作流层**（本文档）
- Video, Analytics, Task, TaskState, Script, Spec, WorkflowStage, Agent, Skill
```

**好处**：
- 用户第一眼看到文档全景
- 通过三层分类知道实体属于哪个领域
- 快速决定读哪个子文档

---

### 原则 4：保持内聚

**问题**：拆分后可能导致相关内容分散

**决策**：每个子文档自成体系，有完整的 YAML 前置元数据和交叉引用

```yaml
---
name: cog-collect
description: 认知模型 - 数据采集层（数据从哪来）
version: 1.0
created: 2026-02-04
parent: cog.md
---
```

**每个子文档的导航头**：
```markdown
> 总览索引见 `cog.md` | 数据加工见 `cog-process.md` | 存储策略见 `cog-data.md`
```

---

### 原则 5：cog-process.md 包含完整的加工管道

**问题**：数据加工涉及 19 个实体，分析框架→可视化→报告→交互的管道关系复杂

**决策**：cog-process.md 包含「数据→图表映射速查表」和完整的实体关系定义

```markdown
## 数据→图表映射速查

| 原始数据 | 加工框架 | 输出图表 | 用途 |
|---------|---------|---------|------|
| CompetitorVideo（播放量×互动率） | ContentQuadrant | 散点图 | 内容价值定位 |
| CompetitorVideo（时长分布） | DurationMatrix | 条形图 | 时长供需分析 |
| CompetitorVideo（标题关键词） | KeywordNetwork | 网络图 | 话题关系发现 |
| ...
```

**好处**：
- 开发者一目了然：什么数据经过什么加工变成什么图表
- 减少在多个文件间来回查找

---

### 原则 6：UI 设计原则独立

**问题**：用户认知模型和 UI 设计原则已经在 Skill 文档中有完整定义

**决策**：cog.md 只保留 Skill 文档引用，详细内容由 Skill 文档提供

```markdown
**相关 Skill 文档**：
- ui-layout-design.skill.md - UI 布局设计
- data-visualization.skill.md - 数据可视化图表选择
```

---

## 最终文档结构

```
.42cog/cog/
├── cog.md            # 核心索引 + 工作流实体 + 枚举（362 行）
├── cog-collect.md    # 数据采集层：6 个实体（177 行）
├── cog-process.md    # 数据加工层：19 个实体（676 行）
├── cog-impl.md       # 实现映射（189 行）
├── cog-data.md       # 数据策略（165 行）
└── cog-context.md    # 上下文信息（198 行）
```

**总行数对比**：

| 方案 | 行数 | 说明 |
|------|------|------|
| 拆分前 | 1887 | 单一大文件 |
| 第一轮拆分后（总计） | 1660 | 4 个文件合计 |
| 第二轮拆分后（总计） | 1767 | 6 个文件合计 |
| 核心文件（第一轮） | 1108 | AI 默认加载 |
| 核心文件（第二轮） | 362 | AI 默认加载 |

**核心文件压缩效果**：

| 阶段 | 核心文件行数 | 压缩比 |
|------|-------------|--------|
| 拆分前 | 1887 | - |
| 第一轮 | 1108 | 41% 减少 |
| 第二轮 | 362 | **81% 减少** |

> 总行数略有增加（1660 → 1767），因为每个子文档增加了导航头、管道总览和速查表等辅助内容。这是合理的代价——子文档自成体系比单纯压缩行数更重要。

---

## 拆分后的内容分布

### cog.md（362 行）— 核心索引

```
✅ 文档索引（6 个子文档 + 2 个 Skill 文档）
✅ 核心认知摘要（有趣度公式、用户旅程、核心价值）
✅ 实体总览清单（三层分类：采集/加工/工作流）
✅ 工作流实体定义
  - Video（状态流转：draft→scripting→producing→ready→published）
  - Task（状态转移：pending→running→completed/failed/cancelled）
  - TaskState（API 层状态管理）
  - Analytics（观看/互动/频道/曝光指标）
  - Script（脚本版本管理）
  - Spec（内容规约）
✅ 流程实体定义
  - WorkflowStage（5 阶段 I/O 定义）
  - Agent（三层编排）
  - Skill（可复用能力）
✅ 枚举类型定义
  - VideoStatus, Privacy, Resolution
  - PatternType, Stage, TaskStatus
  - AnalyticsPeriod, ContentStyle
✅ 工作流关系定义
  - 内容创作流（调研→策划→制作→发布→复盘）
  - 任务调度关系
```

### cog-collect.md（177 行）— 数据采集层

```
✅ 核心问题：数据从哪来？怎么采集？采集得到什么？
✅ 采集核心实体
  - CompetitorVideo（竞品视频，含计算属性：daily_views, quadrant, score）
  - Channel（频道，含计算属性：efficiency_score, is_dark_horse）
  - TrendSnapshot（趋势快照，追踪增长变化）
✅ 采集交互实体
  - SearchPanel（搜索面板，6 个筛选维度）
  - MonitorTask（监控任务，调度层）
  - TrendingTracker（趋势展示，呈现层）
✅ 采集关系定义
  - 采集流程图（关键词→SearchPanel→API→数据入库→可选监控/快照）
  - 6 条关系映射表
```

### cog-process.md（676 行）— 数据加工层

```
✅ 核心问题：什么数据，经过什么加工，变成什么图表和报告？
✅ 加工管道总览（三层架构图：分析框架→可视化→报告）
✅ 数据→图表映射速查表（7 条映射）
✅ 分析框架实体
  - ContentQuadrant（四象限：star/niche/viral/dog）
  - DurationMatrix（时长分桶：供给占比+平均播放）
✅ 可视化实体
  - InsightCard（洞察卡片：置信度+推理链+数据源）
  - ReasoningChain（推理链：步骤+权重+结论）
  - ChartCognitionMapping（图表认知映射：10 种概念→可视化方式，16 种图表库）
✅ 套利分析实体
  - ArbitrageReport（6 种套利类型）
  - KeywordNetwork（关键词网络：节点+边+中心性）
  - BridgeTopic（桥梁话题：高有趣度 > 0.3）
  - CreatorProfile（博主画像：小白/腰部/头部）
  - ArbitrageOpportunity（套利机会：优先级评估）
✅ 模式分析实体
  - PatternAnalysis（5 维模式：variable/temporal/spatial/channel/user）
  - PatternReport（42 个模式汇总）
  - PatternDetail（单个模式深度分析页）
  - LearningPath（导航结构：3 主 Tab+1 外链+1 隐藏 Tab）
✅ 报告实体
  - AnalysisReport（综合报告）
  - MarketReport（市场规模+频道竞争+进入壁垒）
  - OpportunityReport（时间窗口爆款+高增长+小频道黑马）
  - DiagnoseReport（频道诊断评分 A-F）
✅ 交互实体
  - RankingList（视频榜 5 种 + 频道榜 5 种）
✅ 实体关系定义
  - 数据加工管道（全流程）
  - 分析框架关系
  - 可视化关系
  - 套利分析关系
  - 诊断关系
  - 模式分析关系（五层架构：数据→报告→呈现→导航→详情）
  - 跨域关系（采集→加工）
```

### cog-impl.md（189 行）— 实现映射

```
✅ API 与实体映射（13 个端点 + WebSocket 协议）
✅ CLI 命令与实体映射（16 个命令）
✅ 脚本与实体映射（12 个脚本 + 数据分层策略）
✅ 代码实现层实体定义
  - DataCollector（两阶段采集）
  - YtDlpClient（YouTube 数据采集封装）
  - YtDlpError（自定义异常）
  - NetworkCentralityAnalyzer（中心性算法）
  - BaseModel（数据模型基类）
  - TaskTypes（任务类型常量）
✅ 便捷函数索引（7 个函数）
```

### cog-data.md（165 行）— 数据策略

```
✅ 时间窗口定义（报告窗口 4 级 + 存储时间桶 7 级）
✅ 数据生命周期与存储策略
  - 核心问题（TrendSnapshot 爆炸、查询性能、存储成本）
  - 分层存储策略（热/温/冷/归档 四层）
  - TrendAggregate 实体（压缩后的趋势数据）
  - 数据压缩规则（4 个年龄段 → 4 种粒度）
  - 压缩效果估算（1 年 16:1 压缩比）
  - 视频数据去重策略（主表去重 + VideoKeywordHit 关联表）
  - 分页查询策略（后端分页 + 统计预计算）
  - 定时任务（凌晨压缩+归档+缓存刷新）
```

### cog-context.md（198 行）— 上下文信息

```
✅ 业务上下文
  - 系统定位（数据洞察平台）
  - 与竞品差异（vs VidIQ/TubeBuddy）
  - 核心功能模块（4 个模块）
  - 套利分析框架（5 种套利）
  - 数据规模（2340 + 172 视频，42 个模式）
✅ 用户上下文
  - 目标用户画像（中文 YouTube 创作者）
  - 核心痛点（4 个）
  - 用户旅程
✅ 技术上下文
  - 前端架构（HTML/CSS/JS + Chart.js + WebSocket）
  - 后端架构（Python + FastAPI + yt-dlp + SQLite）
  - API 通信（WebSocket + REST）
  - 数据处理（pandas + networkx）
  - 依赖清单
✅ 页面结构定义
  - 页面列表（11 个页面）
  - 洞察系统 Tab 结构（3 主 Tab + 1 外链 + 1 隐藏 Tab）
  - 套利分析页面结构（2 组 + 1 外链，含有趣度三榜单）
  - 主控台面板结构（7 个面板）
✅ 与 prompts/ 的关系
```

---

## 决策总结

| 决策 | 原因 |
|------|------|
| 两轮拆分策略 | 第一轮按场景拆，第二轮按领域拆 |
| 核心文件压缩到 362 行 | AI token 消耗减少 81% |
| 按数据流方向拆分核心实体 | 采集→加工→工作流，职责清晰 |
| cog-process.md 包含完整管道 | 一个文件解答「数据怎么变成图表」 |
| 添加文档索引和实体总览 | 用户快速定位内容 |
| 保持内聚 | 每个文档自成体系 |
| UI 原则引用 Skill | 避免重复，职责分明 |
| YAML 元数据标注关系 | 明确文档层级 |

---

## 后续维护指南

### 何时修改哪个文件？

| 场景 | 修改文件 |
|------|----------|
| 新增采集相关实体 | cog-collect.md |
| 新增分析/可视化/报告实体 | cog-process.md |
| 新增工作流实体 | cog.md |
| 新增枚举类型 | cog.md |
| 新增 API 端点 | cog-impl.md |
| 新增 CLI 命令 | cog-impl.md |
| 新增数据表/存储策略 | cog-data.md |
| 更新技术栈 | cog-context.md |
| 新增页面 | cog-context.md |

### 文档版本管理

每个文档独立版本：
- cog.md: version 3.1
- cog-collect.md: version 1.0
- cog-process.md: version 1.0
- cog-impl.md: version 1.0
- cog-data.md: version 1.0
- cog-context.md: version 1.0

### 拆分的可逆性

如果未来需要合并回单文件（例如 AI 上下文窗口足够大），只需：
1. 将 cog-collect.md 的实体定义和关系合并回 cog.md
2. 将 cog-process.md 的实体定义和关系合并回 cog.md
3. 删除子文档索引

---

## 迭代记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-02-04 | 初版：记录第一轮拆分（1 → 4 文件），cog.md 1887 → 1108 行 |
| v2.0 | 2026-02-04 | 更新：记录第二轮拆分（4 → 6 文件），cog.md 1108 → 362 行 |

### v2.0 变更明细

**结构变更**：
- 新增「拆分历程」章节，区分第一轮和第二轮拆分
- 原「原则 1：单一职责」改为「原则 1：按数据流方向拆分」
- 原「原则 2：核心文档精简」改为「原则 2：核心文档极致精简」
- 新增「原则 5：cog-process.md 包含完整的加工管道」
- 原「原则 5：UI 设计原则独立」移为「原则 6」
- 删除原「原则 3：索引优先」中的旧索引示例，替换为 6 文件版本
- 新增「拆分的可逆性」章节

**数据变更**：

| 指标 | v1.0 记录值 | v2.0 记录值 |
|------|------------|------------|
| 文件数 | 4 | 6 |
| cog.md 行数 | 1108 | 362 |
| 核心文件压缩比 | 41% | 81% |
| 总行数 | 1660 | 1767 |
| 关联文档 | 4 个 | 6 个 |
| cog.md 职责 | 核心实体 + 关系定义 | 核心索引 + 工作流实体 + 枚举 |
| cog.md version | 3.0 | 3.1 |

**新增文件记录**：
- cog-collect.md（177 行）：从 cog.md 拆出的采集层实体（6 个）
- cog-process.md（676 行）：从 cog.md 拆出的加工层实体（19 个）

**维护指南变更**：
- 新增「采集相关实体 → cog-collect.md」
- 新增「分析/可视化/报告实体 → cog-process.md」
- 原「新增业务实体 → cog.md」改为「新增工作流实体 → cog.md」

---

## 参考文档

- `.42cog/skills/ui-layout-design.skill.md` - UI 布局设计技能
- `.42cog/skills/data-visualization.skill.md` - 数据可视化技能
- `.42cog/real/real.md` - 现实约束
- `CLAUDE.md` - 项目配置
