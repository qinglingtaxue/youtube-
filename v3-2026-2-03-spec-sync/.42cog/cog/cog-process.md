---
name: cog-process
description: 认知模型 - 数据加工层（数据怎么变成图表和报告）
version: 1.0
created: 2026-02-04
parent: cog.md
---

# 认知模型 - 数据加工层

> 本文档定义数据加工阶段的所有实体和关系。
>
> 核心问题：**什么数据，经过什么加工，变成什么图表和报告？**
>
> 总览索引见 `cog.md` | 采集实体见 `cog-collect.md` | 存储策略见 `cog-data.md`

---

## 加工管道总览

```
采集实体（cog-collect.md）
    ↓
┌───────────────────────────────────────────────────────────┐
│              分析框架层（中间加工）                          │
│  ContentQuadrant │ DurationMatrix │ KeywordNetwork │ ...  │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│              可视化层（呈现输出）                            │
│  InsightCard │ ReasoningChain │ ChartCognitionMapping      │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│              报告层（最终输出）                              │
│  AnalysisReport │ ArbitrageReport │ PatternReport │ ...   │
└───────────────────────────────────────────────────────────┘
```

## 数据→图表映射速查

| 原始数据 | 加工框架 | 输出图表 | 用途 |
|---------|---------|---------|------|
| CompetitorVideo（播放量×互动率） | ContentQuadrant | 散点图 (ContentQuadrantChart) | 内容价值定位 |
| CompetitorVideo（时长分布） | DurationMatrix | 条形图 (DurationDistributionChart) | 时长供需分析 |
| CompetitorVideo（标题关键词） | KeywordNetwork | 网络图 (vis-network) | 话题关系发现 |
| KeywordNetwork 节点 | BridgeTopic | 网络图（金色高亮） | 套利机会发现 |
| CompetitorVideo（多维度） | PatternAnalysis | InsightCard + 多种图表 | 模式洞察 |
| Channel | DiagnoseReport | 雷达图 / 评分卡 | 频道健康评估 |
| TrendSnapshot | TrendingTracker | 折线图 (LineChart) | 增长趋势追踪 |
| 任意分析结果 | InsightCard | 可折叠卡片 + 推理链 | 可解释 AI 洞察 |

---

## 分析框架实体

<ContentQuadrant>
- 唯一编码：quadrant_type (枚举：star, niche, viral, dog)
- 核心属性：
  - views_threshold：播放量阈值（区分高/低播放）
  - engagement_threshold：互动率阈值（区分高/低互动）
  - videos：该象限的视频列表
  - count：视频数量
  - percentage：占比

**四象限定义**

```
        高互动率
           ↑
    💎 Niche    ⭐ Star
    (粉丝向)     (爆款型)
           ↑
低播放 ←——————————————→ 高播放
           ↓
    ❄️ Dog      🚀 Viral
    (冷门型)     (破圈型)
           ↓
        低互动率
```

| 象限 | 播放量 | 互动率 | 策略 |
|------|--------|--------|------|
| Star | 高 | 高 | 学习标杆，分析选题/标题/封面 |
| Niche | 低 | 高 | 深耕细分，建立核心粉丝群 |
| Viral | 高 | 低 | 优化互动，增加内容深度 |
| Dog | 低 | 低 | 避免重复，分析失败原因 |
</ContentQuadrant>

<DurationMatrix>
- 唯一编码：matrix_id (auto increment)
- 核心属性：
  - buckets：时长分桶列表
    - label：分桶标签（如"0-1分钟"）
    - min_seconds：最小秒数
    - max_seconds：最大秒数
    - count：视频数量
    - supply_percentage：供给占比
    - total_views：总播放量
    - avg_views：平均播放量
  - best_bucket：最佳时长区间（平均播放最高）
  - opportunity_bucket：机会区间（高播放低供给）

**可视化形式**
```
0-1分钟   ████░░░░░░ 供给 12%
1-3分钟   ██████░░░░ 供给 28%
3-5分钟   ████████░░ 供给 15%   ← 平均播放最高
5-10分钟  ██████████ 供给 8%
```
</DurationMatrix>

---

## 可视化实体

<InsightCard>
- 唯一编码：insight_id (UUID)
- 常见分类：market（市场洞察）；opportunity（机会洞察）；warning（风险提示）
- 核心属性：
  - title：洞察标题
  - confidence：置信度 (0-100%)
  - sources：数据源列表
  - visualization：关联的可视化图表
  - reasoning_chain：推理链（步骤列表）
  - findings：关键发现列表
  - is_expanded：是否展开

**洞察卡片结构**

```
┌─────────────────────────────────────────────┐
│ 💡 洞察标题                    [展开/折叠]  │
├─────────────────────────────────────────────┤
│ [置信度条 ████████░░ 78%]                   │
│ 数据源: [视频数据] [频道数据] [趋势数据]     │
├─────────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────────────┐   │
│ │  可视化图表  │  │    推理链          │   │
│ │  (SVG/图)   │  │  📊 观察 → 权重30% │   │
│ │             │  │      ↓             │   │
│ │             │  │  📈 分析 → 权重50% │   │
│ │             │  │      ↓             │   │
│ │             │  │  ✅ 结论           │   │
│ └─────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────┘
```
</InsightCard>

<ReasoningChain>
- 唯一编码：chain_id (auto increment)
- 核心属性：
  - steps：推理步骤列表
    - icon：步骤图标
    - name：步骤名称
    - observation：观察内容
    - weight：权重百分比
  - conclusion：最终结论
  - total_confidence：综合置信度

**设计目的**
让 AI 洞察不再是黑箱，用户能看懂结论是怎么来的。
</ReasoningChain>

<ChartCognitionMapping>
- 唯一编码：chart_cognition (singleton)
- 用途：定义如何通过图表帮助用户直观理解抽象概念
- 详细实现：参见 `.42cog/skills/data-visualization.skill.md`
- 模板位置：`src/templates/charts/`

**核心映射表**

| 用户不理解的概念 | 可视化方式 | 图表类型 | 说明 |
|----------------|-----------|---------|------|
| **中介中心性** (Betweenness) | 节点大小 / 连线数量 | 网络图 | 节点越大 = 越是信息桥梁 |
| **程度中心性** (Degree) | 节点连线数 / 节点颜色 | 网络图 | 连线越多 = 传播越广 |
| **有趣度** (Interestingness) | 金色高亮 + 节点大小 | 网络图 | 金色 = 套利机会 |
| **P分位数** | 标注线 + 区域 | 直方图 | 在分布图上标注分位线 |
| **置信度** | 误差棒 | 柱状图/折线图 | 误差范围表示不确定性 |
| **互动率** | 播放量vs点赞散点 | 散点图 | 用两个用户懂的指标展示 |
| **流量来源** | 流向宽度 | 桑基图 | 越宽 = 流量越大 |
| **内容相似度** | 节点距离 | 网络图 | 越近 = 越相似 |
| **时间分布** | 颜色深浅 | 热力图 | 越深 = 越集中 |
| **关键词重要性** | 字体大小 | 词云 | 越大 = 越重要 |

**关键洞察**

> 网络图是理解中心性指标的最佳工具
>
> 用户反馈：「信息网络图可以帮助直观的理解中介中心性、程度中心性、有趣度」

**可用图表库（16 种）**

| 类别 | 图表类型 | 函数名 | 依赖 |
|------|---------|--------|------|
| 基础 | 柱状图/水平柱状图 | `createBarChart` | Chart.js |
| 基础 | 饼图/环形图 | `createPieChart` / `createDoughnutChart` | Chart.js |
| 基础 | 折线图/双轴折线图 | `createLineChart` | Chart.js |
| 基础 | 雷达图 | `createRadarChart` | Chart.js |
| 基础 | 散点图 | `createScatterChart` | Chart.js |
| 基础 | 直方图 | `createHistogram` | Chart.js |
| 高级 | 网络图 | `createNetworkGraph` | vis-network |
| 高级 | 地图 | `createMap` | Leaflet |
| 高级 | 热力图 | `createHeatmap` | ECharts |
| 高级 | 树图 | `createTreemap` | ECharts |
| 高级 | 桑基图 | `createSankeyDiagram` | ECharts |
| 高级 | 词云 | `createWordCloud` | ECharts |

**数据量级决策原则**

```
数据点 <10   → 数字卡片、环形图
数据点 10-50 → 柱状图、折线图、散点图
数据点 50-200 → 网络图、树图
数据点 200+  → 热力图、聚合网络图
关键词 20-200 → 词云
流量归因     → 桑基图
地理分布     → 地图
```

**多样性检查清单**

每页应包含以下类型图表，确保视觉多样性：
```
□ 数字展示类（卡片）      - 快速扫描
□ 比例类（饼图/树图）     - 占比理解
□ 比较类（柱状图）        - 大小对比
□ 趋势类（折线图）        - 时间变化
□ 关系类（散点图/网络图） - 相关发现
□ 分布类（直方图/热力图） - 数据分布
□ 文本类（表格/词云）     - 详细信息
```
</ChartCognitionMapping>

---

## 套利分析实体

> **核心公式**：有趣度 = 信息价值程度 / 信息传播程度 = 中介中心性 / 程度中心性
>
> 高有趣度 = 价值被低估 = 套利机会

<ArbitrageFramework>
- 唯一编码：framework_id (singleton)
- 定位：从数据发现蓝海机会的分析框架
- 核心结构：**5 维度 × 3 中心性**
  - 5 个维度：视频(Video)、搜索关键词(SearchKeyword)、频道(Channel)、标题词(TitleWord)、国家(Country)
  - 3 个中心性：有趣度(Interestingness)、中介中心性(Betweenness)、程度中心性(Degree)
  - 总计：15 个榜单（5维度 × 3指标）

**维度优先级**

| 优先级 | 维度 | 用户问题 | 作用 |
|--------|------|--------|------|
| **P1** | 视频(Video) | "什么内容最值得学习？" | 选题参考，内容价值判断 |
| **P2** | 搜索关键词(SearchKeyword) | "搜索需求 vs 内容供给？" | **内容缺口发现**（最重要） |
| **P3** | 频道(Channel) | "谁的运营值得学习？" | 频道样本学习 |
| **P4** | 标题词(TitleWord) | "热门标题怎么起？" | 标题创意参考 |
| **P5** | 国家(Country) | "有没有国际机会？" | 跨语言套利机会 |

**每个维度的 3 个中心性指标**

1. **💎 有趣度榜(Interestingness)** = 中介中心性 ÷ 程度中心性
   - 含义：价值高但传播不足 = 高有趣度 = 套利机会
   - 排序：从高到低，优先级最高

2. **🌉 中介中心性榜(Betweenness Centrality)**
   - 含义：连接多个群体的能力
   - 视频维度：能连接多个话题的综合内容
   - 搜索维度：跨域搜索热词，连接不同用户群体
   - 示例：养生 + 美容 + 运动 能共同关注的话题

3. **🔥 程度中心性榜(Degree Centrality)**
   - 含义：传播程度，竞争激烈度
   - 指标：热门程度、搜索竞争度、频道热度
   - 用途：判断内容饱和度

**榜单样例：以搜索关键词维度为例**

```
【搜索关键词 - 有趣度榜】- 内容缺口发现 ⭐⭐⭐ 最重要
排名  搜索关键词         有趣度分数  Google搜索量  YouTube视频  缺口指数
1.   穴位按摩           4.32        +76%          7条          高 ← 机会！
2.   补肾食疗           3.89        +58%          23条         中
3.   瑜伽减脂           3.56        +42%          156条        低

【搜索关键词 - 中介中心性榜】- 桥梁话题
排名  搜索关键词         中介中心性   连接的领域      应用
1.   养生保健           4.18        医学+美容+运动  跨领域合作机会
2.   食疗养生           3.94        营养+中医+健身  综合话题切入

【搜索关键词 - 程度中心性榜】- 竞争度
排名  搜索关键词         程度中心性   热度      竞争强度
1.   瑜伽减脂           4.76        🔥🔥🔥    非常激烈
2.   穴位按摩           2.15        🔥        中等（低竞争 ✅）
```

**与信息报告的数据映射**

| 信息报告结论 | 来自套利分析 | 具体榜单 | 数据维度 |
|-----------|----------|--------|--------|
| ① 市场竞争分散 | 🔥程度中心性榜 | 视频维度 | 竞争激烈度分布 |
| ② 「穴位按摩」内容缺口 | 💎有趣度榜 TOP 1 | **搜索关键词维度** ⭐ | 搜索量高+视频少 |
| ③ 最优时长 4-20min | - | - | 来自全局认识，不是套利分析 |
| ④ Tai Chi 跨语言机会 | 💎有趣度榜 | **国家维度** | 英文市场高有趣度 |
</ArbitrageFramework>

<ArbitrageReport>
- 唯一编码：arbitrage_report_id (timestamp: YYYYMMDD_HHMMSS)
- 常见分类：topic（话题套利）；channel（频道套利）；duration（时长套利）；timing（趋势套利）；cross_language（跨语言套利）
- 核心属性：
  - generated_at：生成时间
  - sample_size：样本量
  - arbitrage_types：套利类型列表
  - opportunities：发现的套利机会列表
  - summary：综合摘要

**套利类型定义**

| 套利类型 | 有趣度公式 | 含义 |
|----------|------------|------|
| 话题套利 | 中介中心性 / 程度中心性 | 能连接多群体但传播不足的话题 |
| 跨语言套利 | 源市场播放量 / 目标市场视频数 | 源市场火爆但目标市场空白 |
| 时长套利 | 平均播放量 / 供给占比 | 播放量高但供给不足的时长 |
| 频道套利 | 最高播放 / 频道平均播放 | 小频道爆款，内容本身有价值 |
| 趋势套利 | 近期频率 / 历史频率 | 上升趋势话题，提前布局 |
| 跟进套利 | 爆款播放量 / 爆款后同话题视频数 | 爆款后市场跟进程度 |
</ArbitrageReport>

<KeywordNetwork>
- 唯一编码：network_id (auto increment)
- 核心属性：
  - nodes：关键词节点列表
    - keyword：关键词
    - count：出现次数
    - total_views：关联视频总播放量
    - betweenness：中介中心性
    - degree：程度中心性
    - interestingness：有趣度（betweenness / degree）
  - edges：共现边列表
    - source：源关键词
    - target：目标关键词
    - weight：共现次数
  - network_stats：网络统计
    - density：网络密度
    - avg_clustering：平均聚类系数

**网络构建方法**
1. 节点：从视频标题中提取关键词
2. 边：两个关键词在同一视频标题中共现，即建立边
3. 边权重：共现频次
4. 使用 networkx 计算中心性指标
</KeywordNetwork>

<BridgeTopic>
- 唯一编码：keyword (关键词字符串)
- 核心属性：
  - interestingness：有趣度（> 0.3 为高有趣度）
  - betweenness：中介中心性（连接不同群体的能力）
  - degree：程度中心性（传播程度）
  - video_count：关联视频数
  - total_views：关联视频总播放量
  - connected_topics：相连的话题列表

**桥梁话题特征**
- 高中介中心性：能连接多个不同的话题群
- 低程度中心性：本身传播不充分
- 高有趣度：价值高但被低估

**示例**
「八段锦」可能同时连接「养生」「运动」「中医」三个群体，如果本身视频数不多，就是高价值套利点。
</BridgeTopic>

<CreatorProfile>
- 唯一编码：profile_id 或 creator_type
- 常见分类：beginner（小白博主）；mid_tier（腰部博主）；top_tier（头部博主）
- 核心属性：
  - type：博主类型
  - resources：资源特点
  - suitable_arbitrage：适合的套利类型
  - strategy：推荐策略

**博主定位策略**

| 博主类型 | 资源特点 | 适合的套利 | 策略 |
|----------|----------|------------|------|
| **小白博主** | 无流量、无经验 | 话题套利、时长套利、频道套利 | 找供给不足的细分，模仿小频道爆款 |
| **腰部博主** | 有基础、有粉丝 | 桥梁话题、跨品类套利 | 连接两个受众群体，跨品类迁移 |
| **头部博主** | 有流量、有资源 | 趋势套利、跨语言套利 | 早期布局新趋势，翻译套利 |
</CreatorProfile>

<ArbitrageOpportunity>
- 唯一编码：opportunity_id (UUID)
- 常见分类：topic, channel, duration, timing, cross_language, follow_up
- 核心属性：
  - type：套利类型
  - name：机会名称（话题/频道/时长区间）
  - interestingness：有趣度分数
  - value_score：价值程度
  - spread_score：传播程度
  - details：详细数据
  - recommendation：行动建议

**机会评估标准**
- 有趣度 > 1.0：高优先级机会
- 有趣度 0.5-1.0：中优先级机会
- 有趣度 < 0.5：低优先级机会
</ArbitrageOpportunity>

---

## 模式分析实体

> **数据规模**：N=2,340 中文视频 + 172 多语言视频，42 个已发现模式

<PatternAnalysis>
- 唯一编码：pattern_id (auto increment)
- 常见分类：
  - variable（变量分布）：标题长度、视频时长、话题热度
  - temporal（时间维度）：发布时机、话题周期
  - spatial（空间维度）：跨语言市场、CPM 收益
  - channel（频道维度）：黑马频道、增长案例
  - user（用户维度）：评论热词、情感分析
- 核心属性：
  - dimension：分析维度
  - finding：发现描述
  - interestingness：有趣度（1-5 分）
  - confidence：置信度（0-100%）
  - sample_size：样本量
  - data_sources：数据源列表
  - action_items：行动建议

**有趣度评估框架**
| 分数 | 含义 | 标准 |
|------|------|------|
| 5 | 极高 | 能指导多个决策，传播度极低 |
| 4 | 高 | 能指导核心决策，传播度低 |
| 3 | 中 | 能指导某些决策，传播度中等 |
| 2 | 低 | 验证已有认知，传播度较高 |
| 1 | 极低 | 已是常识，传播度极高 |
</PatternAnalysis>

<PatternReport>
- 唯一编码：report_id (timestamp: YYYYMMDD)
- 核心属性：
  - total_patterns：发现的模式总数
  - patterns_by_dimension：按维度分类的模式列表
  - top_findings：Top5 核心发现
  - action_guide：行动指南
  - data_basis：数据基础说明

**核心发现示例**
| 发现 | 有趣度 | 说明 |
|------|--------|------|
| 互动率与播放量负相关 | 5.0 | 反常识，需深入分析 |
| 长标题效果是短标题 4 倍 | 4.5 | 验证后可直接应用 |
| Tai Chi 英语市场爆发 +533% | 4.0 | 跨语言套利机会 |
| 穴位按摩内容缺口 | 4.5 | Google ↑76%，YouTube 仅 7 条 |
</PatternReport>

<PatternDetail>
- 唯一编码：pattern_id (同 PatternAnalysis 的 pattern_id)
- 页面路径：`web/pattern-detail.html`
- 用途：单个模式的深度分析页面
- 核心属性：
  - pattern_id：关联的模式 ID
  - title：模式标题（从 PatternAnalysis.finding 派生）
  - dimension：模式维度（variable/temporal/spatial/channel/user）
  - interestingness：有趣度得分（1-5）
  - confidence：置信度（0-100%）
  - insight_card：为该模式生成的洞察卡片（包含 visualization + reasoning_chain）
  - sources：详细的数据源列表和来源描述
  - sample_videos：该模式的典型视频示例列表
  - action_checklist：基于该模式的具体行动建议清单
  - related_patterns：相关/相似模式的推荐列表

**设计目的**
为每个发现的模式提供独立的详情页面，展示完整的分析过程、数据支撑和可执行建议。
</PatternDetail>

<LearningPath>
- 唯一编码：path_id (singleton)
- 用途：42 个模式的导航结构和学习路径（NOT 等同于 PatternReport）
- 关键区别：PatternReport 是静态报告，LearningPath 是动态导航交互
- **页面位置**：已集成到 `web/insight-system.html` 的导航栏和侧边栏
- 核心属性：
  - blocks：3 个主 Tab + 1 个外链 + 1 个隐藏 Tab（导航分组）
    - title：Tab 标题（分类名称）
    - description：Tab 描述（导航说明）
    - pattern_count：该分组包含的模式数
    - sub_tabs：子标签页列表（模式细分）
      - sub_title：细分标题
      - pattern_ids：该细分下的模式 ID 列表
      - deep_link：深度链接至 `pattern-detail.html?id=...`
  - stats：底部统计（视频数、频道数、总播放、天跨度、洞察数）
  - quick_search：快速搜索框（按模式名、关键词搜索）

**导航结构（3 主 Tab + 1 外链 + 1 隐藏 Tab）**

| Tab | 名称 | 子标签数 | 导航到 | 用途 |
|-----|------|----------|---------|------|
| Tab 1 | 🌍 全局认识 | 5 | 全局模式 | 整体市场认知 |
| Tab 2 | 💰 套利分析 | 6 | 套利机会模式 | 发现价值洼地 |
| Tab 7 | 📋 信息报告 | 4 | 数据报告 | 查看详细数据 |
| 外链 | 🎬 创作者行动中心 | - | `creator-action.html` | 查看具体行动计划 |
| Tab 8 | 👥 用户洞察 | 5 | 用户相关模式 | （隐藏）用户深度分析 |

**重要澄清**
- LearningPath 与 PatternReport 的关系：
  - PatternReport = 数据汇总报告（what & how many）
  - LearningPath = 用户导航体验（how to explore & learn）
  - 两者都基于相同的 42 个 PatternAnalysis，但目的不同
- 每个 sub_tab 项都链接到对应的 `pattern-detail.html` 页面

**JS 模块架构**

洞察系统由 7 个 JS 模块组成：
```
web/js/
├── insight-core.js     # 核心框架、Tab切换、状态管理
├── insight-charts.js   # Chart.js 图表封装
├── insight-report.js   # 信息报告 Tab (Tab 7)
├── insight-user.js     # 用户洞察 Tab (Tab 8，隐藏)
├── insight-global.js   # 全局认识 Tab (Tab 1)
├── insight-content.js  # 内容分析相关
└── insight.js          # 入口文件、模块协调
```

> **注**：原独立页面 `web/learning-path.html` 已归档至 `web/legacy/`
</LearningPath>

---

## 报告实体

<InformationReport>
- 唯一编码：info_report_id (singleton)
- 定位：**推理链式分析报告**，汇总跨页数据的分析结论，指导用户决策
- 职责：**洞察 + 推理链**（而非数据展示）
- 特点：单页、沉浸式、无跳转设计
- 页面路径：`web/info-report.html`

**核心结构**（4 层）

```
┌─────────────────────────────────────┐
│ 1. 全局筛选器（所有页面通用）         │
│    关键词 + 时间范围（只读显示）     │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 2. 研究假设（ResearchHypothesis）     │
│    用户的研究问题 + 分析范围         │
│    来源：全局状态，用户在上方改变时同步 │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 3. 结论链（ConclusionChain）         │
│    4 条结论卡片                     │
│    ① 默认展开，②③④ 默认折叠        │
│    ├─ 标题 + 摘要（始终可见）       │
│    ├─ 数据来源标签（点击引用）       │
│    ├─ [展开/折叠] 按钮                │
│    └─ [展开时] 推理链 + 嵌入图表    │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 4. 综合结论 + 行动入口                │
│    ├─ 综合结论文案 + 关键点列表      │
│    └─ [导出 Markdown] [去行动中心]   │
└─────────────────────────────────────┘
```

**关键组件定义**

<ResearchHypothesis>
- 来源：全局状态
- 特点：只读，用户在顶部全局筛选器改变时自动同步
- 内容：
  - 研究问题描述（1-2 句）
  - 分析范围说明：关键词 + 时间范围 + 数据源
- 示例：
  ```
  研究假设
  在「养生」赛道中，是否存在搜索需求高但内容供给不足的
  细分话题，适合新创作者切入？

  关键词: 养生 · 分析范围: 过去 3 个月 · 数据源: YouTube+GT
  ```

<ConclusionCard>
- 唯一编码：conclusion_id (1-4)
- 核心属性：
  - title：结论标题（50 字以内）
  - summary：一句话摘要（100 字以内）
  - confidence：置信度 (75-88%)
  - tags：标签列表（数据源标签 + 模式标签）
  - reasoning_steps：推理步骤列表
  - embedded_charts：嵌入图表列表
  - is_expanded：展开状态（初始值：①=true, ②③④=false）

**卡片展开/折叠规则**
- 初始状态：结论① 默认展开（占首屏），其他默认折叠
- 用户点击标题或「展开数据」按钮 → 平滑展开（transition: 0.2s）
- 展开后显示：推理步骤 → 数据来源 → 嵌入图表
- 再次点击 → 折叠回简洁视图

**卡片初始视图（始终可见）**
```
┌──────────────────────────────────────┐
│ ① 市场竞争分散，新人有机会进入        │
│                                      │
│ 摘要: Top 10 频道仅占总播放 23%，    │
│     市场未被头部垄断。45% 频道       │
│     近 6 个月新建。                  │
│                                      │
│ [标签] 全局认识·频道分布             │
│ [标签] 置信度 82%                   │
│                                      │
│ [▼ 展开数据]                         │
└──────────────────────────────────────┘
```

**卡片展开视图**
```
展开区内容：
1. 推理步骤列表（带权重）
2. 数据来源标签（可点击）
3. 嵌入图表（来自全局认识/套利分析）
```

<ReasoningStep>
- 组成：icon + text + weight
- weight 定义：
  - **百分比**（如 40%）：该步骤在结论中的数据贡献权重
  - **「结论」**（文字，非百分比）：最终结论汇总行
- 样例结构：
  ```
  📊 186 频道播放量分布呈长尾，Top 10 集中度仅 23%        | 40%
  📈 45% 频道创建于近 6 个月，市场仍在扩张               | 40%
  ✅ 结论：市场处于成长期，新进入者有生存空间             | 结论
  ```
- 设计目的：用户直观看到每个数据点的贡献度

<DataSourceTag>
- 外观：可点击 chip，浅色背景
- 格式：📊 页面名 → Tab 名 → 图表名
  - 示例：📊 全局认识 → 市场规模 → 频道集中度图
  - 示例：📈 套利分析 → 有趣度排名 → 视频有趣度榜
  - 示例：🔍 Google Trends → 穴位按摩
- 功能：点击可高亮/导航（可选，不跳转）
- 颜色编码：
  - 📊 全局认识 → 蓝色
  - 📈 套利分析 → 绿色
  - 🔍 Google Trends → 橙色

<EmbeddedChart>
- 来源：全局认识、套利分析的截图 or Chart.js 重渲染
- 特点：页面内嵌入，无需跳转
- 每条结论的嵌入图表列表：
  - 结论① 市场竞争：频道集中度柱状图 + 频道增长趋势折线图
  - 结论② 内容缺口：Google Trends vs YouTube 趋势对比表
  - 结论③ 最优时长：时长分布环形图 + 时长 vs 平均播放对比柱状图
  - 结论④ 跨语言机会：Tai Chi 搜索爆发曲线 + 英文市场空白对比

<SynthesizedConclusion>
- 唯一编码：synthetic_id (singleton)
- 核心属性：
  - main_text：综合结论主文案（1-2 句）
  - key_points：关键点列表（4 项，对应结论①②③④）
- 内容示例：
  ```
  综合结论
  「养生」赛道新创作者的首选策略：切入内容缺口话题，
  采用 4-20 分钟中视频格式，快速测试市场反应。

  → 市场竞争分散（Top 10 占 23%），新人有生存空间
  → 「穴位按摩」等话题有明确的内容缺口和需求
  → 中视频 (4-20min) 平均播放量最高（8.2 万）
  → Tai Chi 等英文热词可通过翻译内容快速变现
  ```

<ActionGateway>
- 唯一编码：gateway_id (singleton)
- 位置：综合结论下方
- 入口 1：📥 导出报告 (Markdown)
  - 功能：生成并下载 Markdown 文件
  - 内容：假设 + 4 结论（包括推理链）+ 综合结论
  - 文件名：`info-report-{date}.md`
- 入口 2：🎯 创作者行动中心 →
  - 功能：外链跳转至创作者行动中心页面
  - URL：`/creator-action-center.html` (或全局配置)

**与全局状态的同步机制**

```
用户在任何页面改变时间范围
  ↓
globalState.timeRange 更新
  ↓
全局认识、套利分析、信息报告、创作者行动中心 同时刷新
  ↓
信息报告中的：
  ├─ 假设区块显示当前参数（只读）
  ├─ 结论数据根据新时间范围重新计算
  └─ 嵌入图表同步更新
```

**与其他页面的数据映射关系**

（详见下表，与 ArbitrageFramework 对应）

| 信息报告结论 | 来自页面 | 来自 Tab/区域 | 数据来源实体 |
|-----------|---------|-----------|----------|
| ① 市场竞争分散 | 全局认识 | 市场规模 + 频道格局 | MarketReport + Channel 频道数据 |
| ② 内容缺口 | 套利分析 + Google Trends | 有趣度榜 + 搜索趋势 | ArbitrageFramework(SearchKeyword) + GoogleTrendData |
| ③ 最优时长 | 全局认识 | 内容分布 | DurationMatrix |
| ④ 跨语言机会 | 套利分析 + Google Trends | 有趣度榜(国家) + 搜索趋势 | ArbitrageFramework(Country) + GoogleTrendData |

</InformationReport>

<AnalysisReport>
- 唯一编码：report_id (timestamp: YYYYMMDD_HHMMSS)
- 常见分类：comprehensive（综合报告）；market（市场报告）；opportunity（机会报告）
- 核心属性：
  - generated_at：生成时间
  - topic：分析主题/关键词
  - sample_size：样本量
  - time_range：数据时间范围
  - tabs：报告标签页（概览、市场边界、时间分析、AI创作机会、内容分析）
  - quadrant_data：四象限分类数据
  - duration_matrix：时长分布矩阵
  - insights：洞察卡片列表

**报告目标**
1. 呈现市场全貌：多少视频、多少频道、总播放量分布
2. 四象限分类：按播放量×互动率定位内容价值
3. 时长分析：找到供给不足的时长蓝海
4. 发现创作机会：小众高价值视频，适合模仿
5. 可解释洞察：每个结论都有推理链支撑
</AnalysisReport>

<MarketReport>
- 唯一编码：market_report_id (timestamp)
- 核心属性：
  - market_size：市场规模
    - sample_videos：样本视频数
    - total_views：总播放量
    - avg_views：平均播放量
    - median_views：中位数播放量
  - channel_competition：频道竞争
    - total_channels：总频道数
    - concentration：集中度（top10_share, top20_share）
    - size_distribution：规模分布（单视频、小型、中型、大型）
  - entry_barriers：进入壁垒
    - performance_tiers：播放量分层（100万+、10-100万、1-10万...）
    - viral_rate：爆款率
    - top_10_percent_threshold：Top10%门槛
  - time_context：时间上下文
    - date_range：数据时间范围（earliest, latest, span）
    - time_distribution：时间分布（24小时内、7天内、30天内...）
</MarketReport>

<OpportunityReport>
- 唯一编码：opportunity_report_id (timestamp)
- 核心属性：
  - recent_viral_by_window：按时间窗口的近期爆款
    - 时间窗口：24小时内、7天内、30天内、90天内、6个月内
    - top_performers：每个窗口的头部视频
  - high_daily_growth：高日增长视频
    - threshold：日增阈值（默认500）
    - top_performers：高增长视频列表
  - small_channel_hits：小频道黑马
    - definition：1-3视频的频道
    - success_threshold：成功阈值（播放量 > 中位数 * 5）
  - high_engagement_templates：高互动模板
    - engagement_rate_threshold：互动率阈值（3%）
  - opportunity_summary：机会总结
    - best_time_window：最佳时间窗口
    - recommendations：建议列表
    - action_items：行动项
</OpportunityReport>

<DiagnoseReport>
- 唯一编码：diagnose_id (UUID)
- 核心属性：
  - channel_name：频道名称
  - channel_id：频道ID
  - subscriber_count：订阅数
  - video_count：视频数
  - total_views：总播放量
  - scores：评分对象
    - overall：综合评分 (A-F)
    - content_quality：内容质量评分
    - update_frequency：更新频率评分
    - engagement：互动率评分
  - strengths：优势列表
  - weaknesses：劣势列表
  - recommendations：改进建议
  - benchmark_channels：推荐对标账号
</DiagnoseReport>

---

## 交互实体

<RankingList>
- 唯一编码：list_type (枚举)
- 常见分类：
  - 视频榜：hot（爆款）、recentHits（近期爆款）、evergreen（长青）、potential（潜力）、longform（长视频）
  - 频道榜：totalViews（总播放）、avgViews（平均播放）、videoCount（视频数）、darkHorse（黑马）、efficiency（高效）
- 核心属性：
  - items：榜单项列表
  - total_count：总数
  - current_page：当前页
  - time_filter：时间筛选（0=全部、1=24小时、7=7天、30=30天、90=90天）
</RankingList>

---

## 实体关系定义

<rel>

### 数据加工管道（全流程）

```
用户输入关键词
    ↓
SearchPanel（筛选条件）                       ← cog-collect.md
    ↓
API 数据采集
    ↓
CompetitorVideo + Channel（原始数据）          ← cog-collect.md
    ↓
┌───────────────┬───────────────┬───────────────┐
│ ContentQuadrant│ DurationMatrix │ KeywordNetwork│
│   (四象限)     │   (时长分布)   │  (关键词网络) │
└───────────────┴───────────────┴───────────────┘
    ↓
AnalysisReport（分析报告）
    ↓
InsightCard + ReasoningChain（可解释洞察）
    ↓
行动建议
```

### 分析框架关系

| 关系 | 基数 | 说明 |
|------|------|------|
| CompetitorVideo → ContentQuadrant | 多对一 | 视频被分类到一个象限 |
| CompetitorVideo → DurationMatrix | 多对一 | 视频归入一个时长分桶 |
| CompetitorVideo → AnalysisReport | 多对多 | 视频参与多个报告生成 |
| Channel → RankingList | 多对多 | 频道出现在多个榜单 |

### 可视化关系

| 关系 | 基数 | 说明 |
|------|------|------|
| AnalysisReport → InsightCard | 一对多 | 报告包含多个洞察卡片 |
| InsightCard → ReasoningChain | 一对一 | 每个洞察有一个推理链 |
| InsightCard → DataSourceTag | 一对多 | 洞察关联多个数据源 |
| ContentQuadrant → ContentQuadrantChart | 一对一 | 四象限数据生成散点图 |
| DurationMatrix → DurationDistributionChart | 一对一 | 时长分布数据生成条形图 |

### 套利分析关系

| 关系 | 基数 | 说明 |
|------|------|------|
| CompetitorVideo → KeywordNetwork | 多对多 | 视频标题构建关键词网络 |
| KeywordNetwork → BridgeTopic | 一对多 | 网络包含多个桥梁话题 |
| BridgeTopic → ArbitrageOpportunity | 一对一 | 桥梁话题对应套利机会 |
| CreatorProfile → ArbitrageOpportunity | 多对多 | 不同博主适合不同套利 |
| ArbitrageOpportunity → ArbitrageReport | 多对一 | 机会汇总到报告 |

### 诊断关系

| 关系 | 基数 | 说明 |
|------|------|------|
| Channel → DiagnoseReport | 一对一 | 一个频道对应一份诊断报告 |
| DiagnoseReport → Channel | 一对多 | 报告推荐多个对标频道 |

### 模式分析关系（五层架构）

```
数据层（Data）
  CompetitorVideo → PatternAnalysis：多对多（视频贡献到多个模式发现）
                          ↓
报告层（Report）
  PatternAnalysis → PatternReport：多对一（42个模式汇总到报告）
                          ↓
呈现层（Presentation）
  PatternReport → InsightCard (type=pattern)：一对多（模式转化为洞察卡片）
  InsightCard.visualization → ContentQuadrantChart/DurationDistributionChart
  InsightCard.reasoning_chain → ReasoningChain
                          ↓
导航层（Navigation）
  LearningPath ⇌ InsightCard：多对多（导航结构链接模式洞察卡片）
                          ↓
详情层（Detail）
  PatternDetail ← InsightCard + PatternAnalysis：一对一（单个模式深度分析页面）
```

| 关系 | 基数 | 说明 |
|------|------|------|
| CompetitorVideo → PatternAnalysis | 多对多 | 视频贡献到多个模式发现 |
| PatternAnalysis → PatternReport | 多对一 | 42 个模式汇总到报告 |
| PatternReport → InsightCard | 一对多 | 模式转化为洞察卡片 |
| LearningPath → InsightCard | 多对多 | 导航结构链接洞察卡片 |
| InsightCard → PatternDetail | 一对一 | 洞察链接到详情页 |
| LearningPath → PatternDetail | 一对多 | 导航链接到详情页 |

### 跨域关系（采集→加工）

> 以下关系连接采集层实体（定义在 `cog-collect.md`）和加工层实体

| 关系 | 基数 | 说明 |
|------|------|------|
| TrendingTracker → InsightCard | 一对多 | 趋势展示生成多个洞察卡片 |
| CompetitorVideo → ContentQuadrant | 多对一 | 视频分类到象限（同"分析框架关系"） |
| CompetitorVideo → DurationMatrix | 多对一 | 视频归入时长分桶（同"分析框架关系"） |
| CompetitorVideo → KeywordNetwork | 多对多 | 视频标题构建网络（同"套利分析关系"） |
| CompetitorVideo → PatternAnalysis | 多对多 | 视频贡献到模式（同"模式分析关系"） |

</rel>
