---
name: cog-context
description: 认知模型上下文 - 业务/用户/技术背景
version: 1.0
created: 2026-02-04
parent: cog.md
---

# 认知模型上下文

> 本文档记录项目的业务、用户和技术上下文，供新人入门参考。
>
> 核心实体定义见：`cog.md`

---

## 业务上下文

本系统是面向 YouTube 内容创作者的**数据洞察平台**，核心价值是帮助创作者**找到好选题、了解竞争格局、优化自己的频道**。

**与 VidIQ/TubeBuddy 的差异**：
- 不只是数据罗列，而是**有分析框架**（四象限、时长矩阵）
- **可解释的 AI 洞察**：每个结论都有推理链支撑
- **Actionable**：每个洞察对应具体行动建议

**核心功能模块**：

| 模块 | 解决的问题 | 输入 | 输出 |
|------|-----------|------|------|
| 选题发现 | "我该做什么内容？" | 关键词 | 视频榜单、机会洞察 |
| 竞品分析 | "谁做得好？怎么做的？" | 视频数据 | 四象限、频道榜 |
| 频道诊断 | "我哪里需要改进？" | 频道链接 | 评分、改进建议 |
| 监控追踪 | "市场有什么变化？" | 监控任务 | 趋势图、增长数据 |

**可视化设计的核心价值**：
1. **四象限分类**：一眼看出内容价值定位
2. **时长分布**：发现供给不足的蓝海区间
3. **推理链展示**：AI 洞察不再是黑箱
4. **置信度指示**：让用户知道结论有多可靠

**套利分析框架**：
- **话题套利**：找到能连接多个受众群体但传播不足的"桥梁话题"
- **频道套利**：发现小频道爆款，内容本身有价值，可模仿
- **时长套利**：找到供给不足的时长区间（如3-5分钟），填补空白
- **趋势套利**：提前布局上升趋势话题，吃早期红利
- **跨语言套利**：源市场火爆但目标市场空白

**数据规模**：
- 中文视频：2,340 条
- 多语言视频：172 条（英语、日语）
- 已发现模式：42 个
- 模式洞察文档：13 个（work/模式洞察*.md）

---

## 用户上下文

**目标用户画像**：
- 主要面向**中文 YouTube 创作者**
- 做养生、教程、美食、旅行等垂类内容
- 目标受众在新加坡、马来西亚、台湾、香港等华语地区
- 想通过**数据驱动**来提升内容表现

**用户的核心痛点**：
- **选题迷茫**：不知道什么内容值得做
- **竞争盲区**：不清楚领域内谁做得好、怎么做的
- **优化无方向**：知道频道有问题，但不知道问题在哪
- **趋势滞后**：等看到趋势时已经晚了

**用户旅程**：
```
发现选题 → 分析竞品 → 确定方向 → 制作内容 → 监控效果 → 迭代优化
    ↑                                              ↓
    └──────────────────────────────────────────────┘
```

---

## 技术上下文

**前端架构**：
- HTML/CSS/JS 单页应用
- Chart.js 图表库
- 暗色主题 UI（#0f172a 背景，#06b6d4 青色强调）
- WebSocket 实时通信
- Markdown 渲染
- 响应式网格布局

**后端架构**：
- Python 3.10+ + FastAPI（api_server.py）
- uvicorn ASGI 服务器
- yt-dlp 数据采集
- SQLite/JSON 数据存储
- SQLAlchemy ORM

**API 通信**：
- WebSocket：实时进度推送（/ws/{task_id}）
- REST：数据查询和操作（/api/*）
- 任务状态管理（内存存储，生产应用 Redis）

**数据处理**：
- pandas 数据分析
- networkx 网络中心性计算（有趣度公式）
- aiohttp/httpx 异步网络请求

**依赖清单**：
```
fastapi >= 0.109.0
uvicorn[standard] >= 0.27.0
websockets >= 12.0
httpx >= 0.25.0
aiohttp >= 3.9.0
pandas >= 2.0.0
yt-dlp
playwright
sqlalchemy
pyyaml
click
rich
```

详见决策文档：`.42cog/work/2026-01-09-决策-为什么放弃纯Playwright采用综合模式.md`

---

## 页面结构定义

本系统包含以下页面，每个页面对应特定的实体和交互：

| 页面 | 路径 | 核心实体 | 功能 |
|------|------|----------|------|
| 入口导航 | `web/index.html` | - | 功能入口 |
| 主控台 | `demo.html` | SearchPanel, RankingList, MonitorTask | 选题发现、频道诊断、监控中心 |
| 创作者仪表盘 | `creator-dashboard.html` | Video, Script, Spec | 内容创意生成、草稿管理、发布计划 |
| 洞察系统 | `web/insight-system.html` | PatternReport, InsightCard, ReasoningChain | 3主Tab+1外链+1隐藏Tab、模式分析、可解释AI洞察 |
| 创作者行动中心 | `web/creator-action.html` | ArbitrageOpportunity, ActionGuide | 具体行动指南、创作建议（洞察系统外链目标） |
| 模式详情 | `web/pattern-detail.html` | PatternAnalysis, InsightCard | 单个模式深度分析、置信度、数据源 |
| 竞品报告 | `public/index.html` | AnalysisReport, MarketReport | 数据概览、市场边界 |
| 套利分析 | `public/arbitrage.html` | ArbitrageReport, ArbitrageOpportunity, KeywordNetwork | 套利机会发现（2组+1外链布局） |
| 内容四象限 | `public/content-map.html` | ContentQuadrant, ContentQuadrantChart | 播放量×互动率矩阵 |
| 创作者分析 | `public/creators.html` | Channel, DiagnoseReport | 频道对比 |
| 标题公式 | `public/titles.html` | CompetitorVideo | 高播放标题特征 |
| 行动建议 | `public/actions.html` | ArbitrageOpportunity | 具体操作指引 |

**洞察系统 Tab 结构**

| Tab | 名称 | 子标签数 | 子标签内容 |
|-----|------|----------|----------|
| Tab 1 | 🌍 全局认识 | 5 | 市场规模/频道分析/内容分布/播放趋势/市场边界 |
| Tab 2 | 💰 套利分析 | 6 | 话题套利/时长套利/频道套利/趋势套利/跨语言套利/综合套利 |
| Tab 7 | 📋 信息报告 | 4 | 数据摘要/结论报告/数据导出/语言覆盖 |
| 外链 | 🎬 创作者行动中心 | - | 跳转至 creator-action.html |
| Tab 8 | 👥 用户洞察 | 5 | 用户画像/评论热词/情感分析/问题提取/需求洞察 |

**套利分析页面结构**（工作记忆 4±1 分组）

> 有趣度公式：有趣度 = 中介中心性 ÷ 程度中心性 = 价值 ÷ 传播 = 套利机会

| 组 | 名称 | Tab 内容 | 用户任务 |
|----|------|----------|---------|
| 组 1 | 📊 看数据 | 视频榜单 / 频道发现 / 赛道分析 / Google 趋势 | 了解市场现状 |
| 组 2 | 💰 找机会 | 有趣度榜 / 中介中心性榜 / 程度中心性榜 | 发现套利空间 |
| 外链 | 🎯 去行动 | → 信息报告 Tab | 获取行动建议 |

**有趣度三榜单独立展示**（必须遵守）：

| 榜单 | 公式含义 | 默认选中 |
|------|---------|---------|
| 💎 有趣度榜 | 价值高但传播少 | ✅ 是 |
| 🌉 中介中心性榜 | 能连接多群体（桥梁话题） | |
| 🔥 程度中心性榜 | 已被广泛讨论（热门话题） | |

**主控台面板结构**

| 面板 | 对应实体 | 功能 |
|------|----------|------|
| 概览 (overview) | AnalysisReport | 数据摘要、关键发现、Top3 预览 |
| 视频榜 (videos) | RankingList, CompetitorVideo | 爆款/近期爆款/长青/潜力/长视频榜 |
| 频道榜 (channels) | RankingList, Channel | 总播放/平均播放/视频数/黑马/高效榜 |
| 模式洞察 (patterns) | DurationMatrix, ContentQuadrant | 时长分布、发布趋势、标题模式 |
| 分析报告 (report) | AnalysisReport | 完整报告、导出功能 |
| 监控中心 (monitor) | MonitorTask | 关键词监控任务管理 |
| 趋势追踪 (trending) | TrendSnapshot | 增长趋势、数据变化 |

---

## 与 prompts/ 的关系

本认知模型定义了**实体和关系的稳定结构**，而 `prompts/` 目录下的提示词是**基于这些实体的操作指令**。

当提示词需要引用实体时，应参考本文档的定义：
- ContentQuadrant 的四种类型：star/niche/viral/dog
- InsightCard 的结构：title、confidence、sources、reasoning_chain
- RankingList 的分类：视频榜（hot/recentHits/evergreen/potential/longform）、频道榜（totalViews/avgViews/videoCount/darkHorse/efficiency）
- **TimeWindow 的标准定义**：1天内、15天内、30天内、全部

这样，提示词不再是孤立的指令，而是**规格的执行器**。
