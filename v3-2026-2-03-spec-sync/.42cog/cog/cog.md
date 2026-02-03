---
name: project-cog
description: YouTube 内容创作者运营平台的认知模型
version: 2.0
last_updated: 2026-02-03
---

# 认知模型 (Cog)

> 本系统的核心认知：**数据驱动选题发现，可视化呈现市场格局，可解释 AI 辅助决策**
>
> 用户旅程：`输入关键词 → 数据采集 → 多维分析 → 可视化呈现 → 洞察生成 → 行动建议`
>
> **核心价值**：不是简单的数据罗列，而是**有框架的分析 + 可解释的洞察 + 可执行的建议**
>
> **有趣度计算公式**：`信息有趣度 = 信息的价值程度 / 信息的传播程度`
>
> 利用中心性近似求解有趣度：在一个信息网络中，`某个节点的有趣度 = 中介中心性 / 程度中心性`
>
> 高有趣度 = 价值被低估 = 套利机会

<cog>
本系统包括以下关键实体：

**核心数据流（信息源）**
- CompetitorVideo：竞品视频，调研阶段数据采集的核心对象
- Channel：YouTube 频道，聚合分析的维度
- TrendSnapshot：趋势快照，追踪视频增长变化
- Video：自有视频，贯穿 5 阶段工作流的核心实体
- Analytics：分析数据，复盘阶段的表现指标

**分析框架（认知模型）**
- ContentQuadrant：内容四象限，播放量×互动率的二维分类
  - Star（爆款型）：高播放+高互动，学习标杆
  - Niche（粉丝向）：低播放+高互动，深耕细分
  - Viral（破圈型）：高播放+低互动，优化互动
  - Dog（冷门型）：低播放+低互动，避免重复
- DurationMatrix：时长分布矩阵，时长×平均播放的供需分析
- ArbitrageFramework：套利分析框架，有趣度公式发现价值洼地
- PatternAnalysis：模式分析框架，多维度识别高效创作模式
  - 变量分布：标题长度、视频时长、话题热度分布
  - 时间维度：发布时机、话题热度周期规律
  - 空间维度：跨语言市场对比、CPM 收益分析
  - 频道维度：黑马频道特征、快速增长案例
  - 用户维度：评论热词、用户问题、情感分析

**可视化层（呈现系统）**
- InsightCard：洞察卡片，可折叠展开的分析单元
- ConfidenceBar：置信度条，表示洞察可靠性
- ReasoningChain：推理链，展示 AI 得出结论的过程
- DataSourceTag：数据源标签，关联原始数据
- ContentQuadrantChart：四象限散点图，仅用于 ContentQuadrant 可视化
- DurationDistributionChart：时长分布条形图，仅用于 DurationMatrix 可视化

**报告实体（输出物）**
- AnalysisReport：分析报告，综合数据洞察
- MarketReport：市场报告，定义市场边界和竞争格局
- OpportunityReport：机会报告，识别创作者切入点
- ArbitrageReport：套利报告，发现价值被低估的机会
- DiagnoseReport：诊断报告，频道健康度评估
- PatternReport：模式洞察报告，42 个已发现模式索引（N=2,340 中文 + 172 多语言）

**交互实体（用户界面）**
- SearchPanel：搜索面板，关键词输入和筛选条件
- FilterChip：筛选标签，多维度数据过滤
- RankingList：榜单列表，视频/频道排行
- MonitorTask：监控任务，定时数据采集
- TrendingTracker：趋势追踪，增长数据监控
- LearningPath：学习路径数据结构（已集成到 insight-system.html 的模式分析标签页）
- PatternDetail：模式详情，单个模式深度分析页面
- CreatorDashboard：创作者仪表盘，内容创意生成和发布计划

**套利实体（价值发现）**
- ArbitrageOpportunity：套利机会，具体可执行的创作方向
- BridgeTopic：桥梁话题，连接多受众群体的关键词
- CreatorProfile：博主画像，匹配适合的套利策略
- KeywordNetwork：关键词网络，话题共现关系图

**工作流实体（任务调度）**
- Task：任务，5 阶段工作流调度的核心单元
- TaskState：任务状态，API 层任务管理（内存/Redis）
- Script：脚本，策划阶段的文稿产出
- Spec：规约，内容规约定义
- Subtitle：字幕，制作阶段资源
- Thumbnail：缩略图，制作阶段资源
</cog>

---

## 可视化实体定义

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

## 分析报告实体定义

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

<TrendSnapshot>
- 唯一编码：snapshot_id (auto increment)
- 核心属性：
  - video_id：关联视频ID
  - snapshot_time：快照时间
  - views：播放量
  - likes：点赞数
  - comments：评论数
  - growth：与上次快照的增长差值

**快照用途**
1. 追踪单个视频的播放量变化曲线
2. 识别增长最快的视频（按时间窗口）
3. 生成增长趋势图（1天、15天、30天）
</TrendSnapshot>

---

## 套利分析实体定义

> **核心公式**：有趣度 = 信息价值程度 / 信息传播程度 = 中介中心性 / 程度中心性
>
> 高有趣度 = 价值被低估 = 套利机会

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

## 模式分析实体定义

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

## 交互实体定义

<SearchPanel>
- 唯一编码：panel_id (singleton)
- 核心属性：
  - topic：搜索关键词
  - filters：筛选条件对象
    - views_min/views_max：播放量范围
    - regions：目标地区列表
    - duration：视频时长类型
    - subscribers：频道粉丝数范围
    - time_range：发布时间范围
    - sort_by：排序方式
    - ai_filter：AI视频筛选
  - presets：预设热门关键词

**筛选维度**
| 维度 | 选项 |
|------|------|
| 播放量 | 1万以下、1-10万、10万+ |
| 地区 | 新加坡、马来西亚、台湾、香港、美国、大陆 |
| 时长 | 短视频(<5分钟)、中等(5-20分钟)、长视频(20分钟+) |
| 粉丝数 | 小频道(<1万)、中频道(1-10万)、大频道(10-100万)、超大(100万+) |
| 发布时间 | 24小时、近7天、近30天、近3个月、近1年 |
| 排序 | 播放量、点赞、评论、互动率、最新、增长 |
</SearchPanel>

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

<MonitorTask>
- 唯一编码：task_id (UUID)
- 用途：定时监控任务的管理单元（调度层）
- 核心属性：
  - keyword：监控关键词
  - interval：采集间隔（分钟）
  - last_run：上次运行时间
  - next_run：下次运行时间
  - status：状态（pending、running、completed、failed）
  - video_count：已采集视频数

**与 TrendingTracker 的区别**：
- MonitorTask = 监控任务配置和执行（调度层）
- TrendingTracker = 监控结果的呈现（展示层）
</MonitorTask>

<TrendingTracker>
- 唯一编码：tracker_id (关联的 MonitorTask.task_id)
- 用途：MonitorTask 执行结果的展示和可视化（呈现层）
- 关键区别：NOT 是独立实体，而是 MonitorTask 执行结果的包装视图
- 核心属性：
  - task_id：关联的监控任务 ID
  - keyword：监控的关键词
  - last_update_time：最后更新时间
  - trend_data：趋势数据对象
    - period：时间段（24h/7d/30d）
    - snapshots：时间序列的快照数据（从 TrendSnapshot 聚合）
    - total_views_delta：总播放量变化
    - avg_daily_growth：平均日增长
    - top_growing_videos：增长最快的视频列表
  - visualization：趋势图表（LineChart 显示播放量增长曲线）
  - alert_status：是否触发预警（高增长/突跌）

**设计目的**
为 MonitorTask 的执行结果提供直观的可视化展示，用户无需关心任务配置，只需查看实时趋势数据。
</TrendingTracker>

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

## 工作流核心实体定义

<Video>
- 唯一编码：video_id (UUID) / youtube_id (发布后)
- 常见分类：draft（草稿）；scripting（脚本中）；producing（制作中）；ready（待发）；published（已发）；scheduled（定时）
- 核心属性：
  - title：视频标题
  - status：状态枚举（VideoStatus）
  - privacy：可见性（public/unlisted/private）
  - duration：视频时长（秒）
  - resolution：分辨率（720p/1080p/4K）
  - spec_id：关联的规约 ID
  - script_id：关联的脚本 ID
  - file_path：视频文件路径
  - youtube_id：YouTube 视频 ID（发布后）
  - scheduled_at：定时发布时间
- 计算属性：
  - engagement_rate：互动率
  - is_ready_to_publish：是否可发布
  - youtube_url：YouTube 链接

**状态流转**
```
draft → scripting → producing → ready → published
                                  ↓
                             scheduled
```

**状态转移规则**
- draft → scripting：开始写脚本
- scripting → producing：脚本完成，开始制作
- producing → ready：视频制作完成
- ready → published：直接发布
- ready → scheduled：设置定时发布
</Video>

<Task>
- 唯一编码：task_id (UUID)
- 常见分类：按阶段划分（research/planning/production/publishing/analytics）
- 核心属性：
  - stage：所属阶段枚举（Stage）
  - task_type：任务类型（collect_videos/generate_script/upload_video 等）
  - status：状态枚举（TaskStatus）
  - input_data：输入数据（JSON）
  - output_data：输出数据（JSON）
  - error_message：错误信息
  - max_retries：最大重试次数（默认 3）
  - retry_count：当前重试次数
  - started_at：开始时间
  - completed_at：完成时间
- 计算属性：
  - duration_seconds：执行耗时
  - can_retry：是否可重试

**状态转移**
```
pending → running → completed
            ↓
          failed → (重试 ≤3 次)
            ↓
        cancelled
```

**支持的方法**
- start()：开始执行
- complete(result)：成功完成
- fail(error)：执行失败
- cancel()：取消任务
- retry()：重试任务
- reset()：重置状态
</Task>

<TaskState>
- 唯一编码：task_id (UUID)
- 用途：API 层任务状态管理（内存存储，生产应用 Redis）
- 核心属性：
  - task_id：任务 ID
  - status：当前状态
  - progress：进度百分比（0-100）
  - message：进度消息
  - result：执行结果
  - error：错误信息
  - created_at：创建时间
- 过期策略：1 小时自动清理
</TaskState>

<Analytics>
- 唯一编码：analytics_id (UUID)
- 常见分类：按周期划分（7d/30d/lifetime）
- 核心属性：
  - video_id：关联的视频 ID
  - period：统计周期枚举（AnalyticsPeriod）
  - collected_at：采集时间
  - **观看指标**：
    - views：播放量
    - watch_time_minutes：总观看时长（分钟）
    - average_view_duration：平均观看时长（秒）
    - unique_viewers：独立观众数
  - **互动指标**：
    - likes：点赞数
    - dislikes：踩数
    - comments：评论数
    - shares：分享数
  - **频道指标**：
    - subscribers_gained：新增订阅
    - subscribers_lost：流失订阅
  - **曝光指标**：
    - impressions：曝光次数
    - ctr：点击率（%）
- 计算属性：
  - engagement_rate：互动率
  - like_ratio：点赞比（likes / (likes + dislikes)）
  - subscriber_delta：净增订阅
  - ctr_formatted：格式化 CTR
  - performance_score()：综合表现评分
</Analytics>

<Script>
- 唯一编码：script_id (UUID)
- 核心属性：
  - video_id：关联的视频 ID
  - version：版本号
  - content：脚本内容（Markdown）
  - word_count：字数
  - estimated_duration：预估时长（秒）
  - status：状态（draft/reviewed/approved）
  - created_at：创建时间
  - updated_at：更新时间
</Script>

<Spec>
- 唯一编码：spec_id (UUID)
- 核心属性：
  - title：规约标题
  - target_audience：目标受众
  - content_style：内容风格枚举（ContentStyle）
  - key_points：核心要点列表
  - reference_videos：参考视频列表
  - constraints：约束条件
  - created_at：创建时间
</Spec>

---

## 枚举类型定义

<Enumerations>
**视频状态（VideoStatus）**
| 值 | 说明 |
|---|---|
| draft | 草稿 |
| scripting | 脚本编写中 |
| producing | 制作中 |
| ready | 待发布 |
| published | 已发布 |
| scheduled | 定时发布 |

**可见性（Privacy）**
| 值 | 说明 |
|---|---|
| public | 公开 |
| unlisted | 不公开 |
| private | 私密 |

**分辨率（Resolution）**
| 值 | 说明 |
|---|---|
| 720p | 高清 |
| 1080p | 全高清 |
| 4K | 超高清 |

**模式类型（PatternType）**
| 值 | 说明 |
|---|---|
| cognitive_impact | 认知冲击 |
| storytelling | 故事叙述 |
| knowledge_sharing | 知识分享 |
| interaction_guide | 互动引导 |
| unknown | 未知 |

**工作流阶段（Stage）**
| 值 | 说明 |
|---|---|
| research | 调研 |
| planning | 策划 |
| production | 制作 |
| publishing | 发布 |
| analytics | 复盘 |

**任务状态（TaskStatus）**
| 值 | 说明 |
|---|---|
| pending | 待执行 |
| running | 执行中 |
| completed | 已完成 |
| failed | 失败 |
| cancelled | 已取消 |

**分析周期（AnalyticsPeriod）**
| 值 | 说明 |
|---|---|
| 7d | 近 7 天 |
| 30d | 近 30 天 |
| lifetime | 全周期 |

**内容风格（ContentStyle）**
| 值 | 说明 |
|---|---|
| tutorial | 教程 |
| story | 故事 |
| review | 评测 |
| vlog | 日常 |
| explainer | 解说 |
</Enumerations>

---

## 视频与频道实体定义

<CompetitorVideo>
- 唯一编码：video_id (YouTube ID)
- 核心属性：
  - title：视频标题
  - channel_name：频道名称
  - channel_id：频道ID
  - url：视频链接
  - views：播放量
  - likes：点赞数
  - comments：评论数
  - duration：时长（秒）
  - published_at：发布时间
  - collected_at：采集时间
  - thumbnail_url：缩略图URL
  - is_ai_video：是否为AI生成视频
  - ai_keyword：AI识别关键词
- 计算属性：
  - days_since_publish：发布天数
  - daily_views：日均播放（views / days_since_publish）
  - time_bucket：时间分桶（24小时内、7天内、30天内...）
  - engagement_rate：互动率（(likes + comments) / views * 100）
  - quadrant：所属四象限（star/niche/viral/dog）
  - score：评分等级（S/A/B/C）
</CompetitorVideo>

<Channel>
- 唯一编码：channel_id (YouTube Channel ID)
- 核心属性：
  - channel_name：频道名称
  - subscriber_count：订阅数
  - video_count：视频总数（频道真实数据）
  - total_views：频道总播放量
  - avg_views：频道平均播放量
  - search_hit_count：搜索命中视频数
  - has_real_stats：是否有真实统计数据
- 计算属性：
  - efficiency_score：效率得分（avg_views / subscriber_count）
  - is_dark_horse：是否为黑马频道（低粉高播放）
</Channel>

---

## 流程实体定义

<WorkflowStage>
- 唯一编码：stage_name (枚举：research, planning, production, publishing, analytics)
- 阶段顺序：调研(1) → 策划(2) → 制作(3) → 发布(4) → 复盘(5)
- 每阶段输入输出：
  - research: 关键词 → 竞品视频 + 市场数据
  - analysis: 市场数据 → 市场报告 + 机会报告 + 趋势快照
  - planning: 报告 → 规约(Spec) + 脚本(Script)
  - production: 脚本 → 视频 + 字幕 + 封面
  - publishing: 视频 → 上传确认 + YouTube ID
  - analytics: YouTube ID → 数据报告 → 下轮调研输入
</WorkflowStage>

<Agent>
- 唯一编码：agent_id (UUID) 或 agent_name (slug)
- 常见分类：specialized（专业代理）；integrated（集成代理）；elite（精英代理）
- 层级关系：elite 编排 integrated，integrated 调用 specialized
</Agent>

<Skill>
- 唯一编码：skill_name (slug，如 youtube-downloader)
- 常见分类：
  - youtube：平台交互（下载、上传、搜索）
  - content：内容处理（转写、剪辑、配音）
  - analysis：数据分析（市场分析、机会识别、趋势监控）
  - report：报告生成（HTML报告、PDF导出）
- 使用方式：被 Agent 调用，或被用户直接触发
</Skill>

---

## 关系定义

<rel>
**数据采集关系**
- SearchPanel → CompetitorVideo：搜索产生视频数据
- CompetitorVideo → Channel：多对一（多个视频属于一个频道）
- MonitorTask → CompetitorVideo：定时采集产生新数据
- CompetitorVideo → TrendSnapshot：一对多（一个视频多个时间点快照）

**分析框架关系**
- CompetitorVideo → ContentQuadrant：多对一（视频被分类到四象限）
- CompetitorVideo → DurationMatrix：多对一（视频归入时长分桶）
- CompetitorVideo → AnalysisReport：多对多（视频参与报告生成）
- Channel → RankingList：多对多（频道出现在多个榜单）

**可视化关系**
- AnalysisReport → InsightCard：一对多（报告包含多个洞察卡片）
- InsightCard → ReasoningChain：一对一（每个洞察有推理链）
- InsightCard → DataSourceTag：一对多（洞察关联多个数据源）
- ContentQuadrant → ContentQuadrantChart：一对一（四象限数据生成散点图表示）
- DurationMatrix → DurationDistributionChart：一对一（时长分布数据生成条形图表示）
- InsightCard.visualization：可关联任何图表类型（ContentQuadrantChart / DurationDistributionChart / 其他）

**套利分析关系**
- CompetitorVideo → KeywordNetwork：多对多（视频标题构建关键词网络）
- KeywordNetwork → BridgeTopic：一对多（网络包含多个桥梁话题）
- BridgeTopic → ArbitrageOpportunity：一对一（桥梁话题对应套利机会）
- CreatorProfile → ArbitrageOpportunity：多对多（不同博主适合不同套利）
- ArbitrageOpportunity → ArbitrageReport：多对一（机会汇总到报告）

**诊断关系**
- Channel → DiagnoseReport：一对一（频道对应诊断报告）
- DiagnoseReport → Channel：多对多（报告推荐多个对标频道）

**用户交互流**
```
用户输入关键词
    ↓
SearchPanel（筛选条件）
    ↓
API 数据采集
    ↓
CompetitorVideo + Channel（原始数据）
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

**内容创作流**
```
调研阶段（Research）
    ↓
CompetitorVideo → PatternAnalysis → ArbitrageOpportunity
    ↓
策划阶段（Planning）
    ↓
Spec → Script
    ↓
制作阶段（Production）
    ↓
Video + Subtitle + Thumbnail
    ↓
发布阶段（Publishing）
    ↓
Video.youtube_id（发布成功）
    ↓
复盘阶段（Analytics）
    ↓
Analytics → 下一轮调研输入
```

**监控追踪关系**
- MonitorTask → CompetitorVideo：一对多（监控任务产生新采集视频）
- MonitorTask → TrendingTracker：一对一（任务配置对应结果展示）
- TrendingTracker → TrendSnapshot：多对多（展示包含多个快照）
- TrendingTracker → InsightCard：一对多（可生成多个趋势洞察卡片）

**任务调度关系**
- Task → Video：多对一（多个任务服务于同一视频）
- Task → TaskState：一对一（API 层状态追踪）
- Video → Script：一对一（视频对应脚本）
- Video → Spec：一对一（视频对应规约）
- Video → Analytics：一对多（视频多个周期的分析数据）

**模式分析关系（四层架构）**
```
数据层（Data）
  CompetitorVideo → PatternAnalysis：多对多（视频贡献到多个模式发现）
                          ↓
报告层（Report）
  PatternAnalysis → PatternReport：多对一（42个模式汇总到报告）
                          ↓
呈现层（Presentation）
  PatternReport → InsightCard (type=pattern)：多对一（模式转化为洞察卡片）
  InsightCard.visualization → ContentQuadrantChart/DurationDistributionChart：关联图表
  InsightCard.reasoning_chain → ReasoningChain：推理过程
                          ↓
导航层（Navigation）
  LearningPath ⇌ InsightCard：导航结构链接模式洞察卡片
                          ↓
详情层（Detail）
  PatternDetail ← InsightCard + PatternAnalysis：单个模式深度分析页面
```

- CompetitorVideo → PatternAnalysis：多对多（视频贡献到多个模式发现）
- PatternAnalysis → PatternReport：多对一（42 个模式汇总到报告）
- PatternReport ≠ LearningPath（前者是数据报告，后者是导航体验）
- InsightCard (type=pattern) ← PatternAnalysis：洞察卡片呈现模式
- InsightCard → PatternDetail：导航至详情页
- LearningPath → PatternDetail：通过导航结构链接到详情页
</rel>

---

## 时间窗口定义

<TimeWindow>
报告中使用的时间窗口标准定义：

| 窗口名称 | 天数范围 | 用途 |
|---------|---------|-----|
| 1天内 | 0-1 | 实时热点追踪 |
| 15天内 | 0-15 | 短期趋势分析 |
| 30天内 | 0-30 | 月度表现评估 |
| 全部 | 不限 | 全量数据分析 |

**内部存储时间桶**
| 桶名称 | 天数范围 | 说明 |
|-------|---------|-----|
| 24小时内 | 0-1 | 最新内容 |
| 7天内 | 1-7 | 近一周 |
| 30天内 | 7-30 | 近一月 |
| 90天内 | 30-90 | 近一季 |
| 6个月内 | 90-180 | 近半年 |
| 1年内 | 180-365 | 近一年 |
| 1年以上 | 365+ | 历史内容 |
</TimeWindow>

---

## 数据生命周期与存储策略

<DataLifecycle>

### 核心问题

当数据量达到十几万甚至更多时，需要解决：
1. **TrendSnapshot 爆炸**：N个视频 × M天 = N×M 条记录
2. **查询性能下降**：无索引/分区导致全表扫描
3. **存储成本增长**：冗余数据无限膨胀

### 分层存储策略

```
┌─────────────────────────────────────────────────────────────┐
│                    数据温度分层                              │
├─────────────────────────────────────────────────────────────┤
│ 🔴 热数据（近7天）  │ 完整快照，日粒度，支持实时查询          │
│ 🟡 温数据（7-30天） │ 周聚合快照，保留关键指标                │
│ 🔵 冷数据（30-90天）│ 月聚合快照，只保留统计数据              │
│ ⚪ 归档（90天+）    │ 只保留视频元数据，删除详细快照           │
└─────────────────────────────────────────────────────────────┘
```

### 新增实体：TrendAggregate

用于存储压缩后的趋势数据：

```
TrendAggregate:
  - video_id：视频ID
  - period_type：周期类型 ('daily' | 'weekly' | 'monthly')
  - period_start：周期开始时间
  - period_end：周期结束时间
  - views_start：周期开始播放量
  - views_end：周期结束播放量
  - growth_total：周期内总增长
  - growth_rate：增长率 (%)
  - snapshot_count：聚合的快照数量
```

### 数据压缩规则

| 数据年龄 | 存储粒度 | 保留时长 | 压缩操作 |
|----------|----------|----------|----------|
| 0-7天 | 日快照 | 7天 | 不压缩 |
| 7-30天 | 周聚合 | 30天 | 日快照 → 周聚合 |
| 30-90天 | 月聚合 | 90天 | 周聚合 → 月聚合 |
| 90天+ | 仅元数据 | 永久 | 删除所有快照 |

### 压缩效果估算

假设监控 5000 个视频：

| 时间范围 | 无压缩（条数） | 压缩后（条数） | 压缩比 |
|----------|---------------|---------------|--------|
| 1周 | 35,000 | 35,000 | 1:1 |
| 1个月 | 150,000 | 55,000 | 2.7:1 |
| 6个月 | 900,000 | 85,000 | **10:1** |
| 1年 | 1,825,000 | 115,000 | **16:1** |

### 视频数据去重策略

```
问题：同一视频被多个关键词采集 → 重复存储

解决方案：主表去重 + 关联表记录命中

CompetitorVideo（主表，以 youtube_id 为主键）
├─ youtube_id (PK)    # 唯一，不重复
├─ title, channel     # 基础信息
├─ first_seen_at      # 首次采集时间
├─ last_updated_at    # 最后更新时间
├─ current_views      # 当前播放量（覆盖更新）
└─ current_likes      # 当前点赞数（覆盖更新）

VideoKeywordHit（关联表）
├─ youtube_id         # 视频ID
├─ keyword            # 命中的关键词
├─ hit_at             # 命中时间
└─ rank_position      # 搜索排名位置
```

### 分页查询策略

```
问题：前端一次性加载10万条数据 → 浏览器崩溃

解决方案：后端分页 + 统计预计算

API 设计：
├─ GET /api/videos?page=1&limit=50     # 分页返回视频列表
├─ GET /api/stats                       # 返回预计算的统计数据
├─ GET /api/quadrant/summary            # 返回四象限聚合数据
└─ GET /api/duration/distribution       # 返回时长分布聚合

前端只存：
├─ 当前页数据（50条）
├─ 统计摘要数据
└─ 图表聚合数据
```

### 定时任务

```python
# 每日凌晨运行
@scheduled(cron="0 3 * * *")
def daily_data_maintenance():
    # 1. 压缩7天前的日快照为周聚合
    compress_to_weekly(older_than=7)

    # 2. 压缩30天前的周聚合为月聚合
    compress_to_monthly(older_than=30)

    # 3. 删除90天前的详细快照（保留元数据）
    archive_old_snapshots(older_than=90)

    # 4. 更新统计缓存
    refresh_stats_cache()
```

</DataLifecycle>

---

## 上下文信息

<context>

### 业务上下文

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

### 用户上下文

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

### 技术上下文

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

</context>

---

## 页面结构定义

<PageStructure>
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
| 套利分析 | `public/arbitrage.html` | ArbitrageReport, ArbitrageOpportunity | 套利机会发现 |
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
</PageStructure>

---

## 与 prompts/ 的关系

本认知模型定义了**实体和关系的稳定结构**，而 `prompts/` 目录下的提示词是**基于这些实体的操作指令**。

当提示词需要引用实体时，应参考本文档的定义：
- ContentQuadrant 的四种类型：star/niche/viral/dog
- InsightCard 的结构：title、confidence、sources、reasoning_chain
- RankingList 的分类：视频榜（hot/recentHits/evergreen/potential/longform）、频道榜（totalViews/avgViews/videoCount/darkHorse/efficiency）
- **TimeWindow 的标准定义**：1天内、15天内、30天内、全部

这样，提示词不再是孤立的指令，而是**规格的执行器**。

---

## 全局文件索引与编码系统

本系统采用**三层唯一编码体系**来避免文件名冲突和混淆：

### 编码层级结构

```
卡片级（Card Level）
├─ id: card-<YYYYMMDD>-<序号>
├─ 位置：任何卡片的 YAML 前置元数据中
└─ 用途：单个想法/洞察的身份证号

文档级（Document Level）
├─ 格式：<YYYYMMDD>_<type>_<topic>.md
├─ 类型：insight|log|spec|template|guide|report
└─ 用途：中等粒度的知识单元（几千字的文档）

项目级（Project Level）
├─ 格式：<project-name>-<module>-<phase>
└─ 用途：超大粒度的工作单元（整个项目文件夹）
```

### 约定俗成文件名的保护

**特殊地位的文件**（不遵循编码规约，因为它们是 AI 和工具的约定俗成）：

必须保持原名：
- `.42cog/` 下所有文件：`meta.md`, `cog.md`, `real.md`, `spec/`, `work.md`, `skills/`
- 工具链文件：`.gitignore`, `.claudeignore`, `package.json`, `README.md`
- Skill 文件后缀：`*.skill.md`

这些文件如果改名，AI 和工具生态会识别失败。因此编码规约**只适用于项目自创的文档**。

### 冲突预防机制

**全局约束**（适用于整个项目）：
1. 同一目录内不允许**完全重名**的文件（如两个 naming.md）
2. 避免同一主题有多个扩展名的文件（如 naming.md 和 naming.txt 都是说明文档）
3. 同一主题的不同版本通过日期区分
4. 子文件夹中的同名文件建议在文件名中包含父上下文（避免混淆）
5. **约定俗成文件不改名**（.42cog/*, .gitignore, .claudeignore 等）

**实际考虑**：
- AI 可以区分不同扩展名（如 .md 和 .txt）
- 问题在于**人眼容易混淆**（"我应该用 naming.md 还是 naming.txt？"）
- 所以规约的目的是减少选择困惑，而不是限制 AI 能力

**检查流程**（创建新文件时）：
```
检查编码规约
    ↓
用 Grep 全局搜索同名文件
    ↓
如发现冲突，列出所有候选名字
    ↓
用户选择 → 确认创建 ✓
```

**异常处理**：
- 如需多版本同名文件：`<name>_v<version>.md`
- 如需多个相同编码：`<name>_<序号>.md`
- 必须在 cog.md 的同主题关系映射中注明版本和用途

### 同主题文件关系映射

当同一主题下有多个文件时，必须在此清单中标注它们的关系：

| 主题 | 文件 | 创建日期 | 状态 | 关系说明 |
|------|------|----------|------|----------|
| 编码规约 | 2026-02-03_spec_naming-convention.md | 2026-02-03 | active | 详细的全局编码规约 |
| 编码规约 | meta.md#编码规约 | 2026-02-03 | active | meta.md 中的简化版规约 |
| 编码规约 | real.md#文件名冲突禁区 | 2026-02-03 | active | 禁区清单，作为 real 约束 |
| - | - | - | - | - |

（此表持续更新，每当新增同主题文件时添加一行）

### 编码规约版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-02-03 | 初始化三层编码体系 |
| 2.0 | 2026-02-03 | 补充全局索引和冲突预防机制 |

---

## API 与实体映射

| API 端点 | 方法 | 操作实体 | 功能 |
|----------|------|----------|------|
| `/` | GET | - | 返回主控台页面 (demo.html) |
| `/creator` | GET | Video, Script | 返回创作者仪表盘 (creator-dashboard.html) |
| `/api/health` | GET | - | 健康检查 |
| `/api/statistics` | GET | CompetitorVideo, Channel | 数据库统计（视频总数、频道数等） |
| `/api/task/{task_id}/status` | GET | TaskState | 任务状态查询（WebSocket 备用） |
| `/ws/{task_id}` | WebSocket | CompetitorVideo, TaskState | 实时数据采集和进度推送 |
| `/api/channel/{id}` | GET | Channel | 获取频道详情 |
| `/api/channels/batch` | POST | Channel | 批量获取频道数据 |
| `/api/videos` | GET | CompetitorVideo | 视频列表查询（分页） |
| `/api/monitor` | POST | MonitorTask | 创建监控任务 |
| `/api/trends/{keyword}` | GET | TrendSnapshot | 获取趋势数据 |
| `/api/stats` | GET | AnalysisReport | 预计算统计数据 |
| `/api/quadrant/summary` | GET | ContentQuadrant | 四象限聚合数据 |
| `/api/duration/distribution` | GET | DurationMatrix | 时长分布聚合 |

**WebSocket 协议**：
```
1. 客户端连接 /ws/{task_id}
2. 发送研究参数 JSON
3. 服务器推送进度更新 { progress: 0-100, message: "..." }
4. 最终推送完整结果 { status: "completed", result: {...} }
5. 心跳保活连接
```

---

## CLI 命令与实体映射

| 命令 | 操作实体 | 输出 |
|-----|---------|-----|
| `research collect` | CompetitorVideo | 新增视频到数据库 |
| `research stats` | CompetitorVideo | 数据库统计信息 |
| `analytics market` | MarketReport | 市场分析报告 |
| `analytics opportunities` | OpportunityReport | AI创作机会报告 |
| `analytics report` | AnalysisReport | 综合HTML报告 |
| `analytics quadrant` | ContentQuadrant | 四象限分析 |
| `monitor snapshot` | TrendSnapshot | 播放量快照 |
| `monitor trends` | TrendSnapshot | 增长趋势分析 |
| `arbitrage analyze` | ArbitrageReport | 综合套利分析报告 |
| `arbitrage topic` | KeywordNetwork, BridgeTopic | 话题套利分析（桥梁话题） |
| `arbitrage channel` | ArbitrageOpportunity | 频道套利分析（小频道爆款） |
| `arbitrage duration` | ArbitrageOpportunity, DurationMatrix | 时长套利分析（供需不平衡） |
| `arbitrage timing` | ArbitrageOpportunity | 趋势套利分析（上升/下降话题） |
| `arbitrage profile` | CreatorProfile | 博主定位建议 |
| `diagnose channel` | DiagnoseReport | 频道诊断报告 |

---

## 脚本与实体映射

| 脚本 | 操作实体 | 功能 |
|-----|---------|-----|
| `scripts/daily_update.py` | CompetitorVideo, TrendSnapshot | 定时更新，每日采集热门话题视频 |
| `scripts/enrich_all_videos.py` | CompetitorVideo | 批量补充详情（点赞/评论/描述/标签） |
| `scripts/video_growth_monitor.py` | TrendSnapshot | 追踪视频表现变化 |
| `scripts/fetch_channel_info.py` | Channel | 批量采集频道数据 |
| `scripts/fetch_comments.py` | CompetitorVideo | 视频评论提取 |
| `scripts/fetch_trends.py` | TrendSnapshot | Google Trends 热词获取 |
| `scripts/collect_multi_domain.py` | CompetitorVideo | 跨品类采集策略 |
| `scripts/collect_multilang.py` | CompetitorVideo | 多语言采集（英语、日语） |
| `scripts/init_monitoring_tables.py` | TrendSnapshot | 初始化监控表结构 |
| `scripts/并行补全视频详情.py` | CompetitorVideo | 多进程加速详情获取 |
| `scripts/补全视频详情.py` | CompetitorVideo | 逐条补充详情 |
| `scripts/补充订阅数.py` | Channel | 频道订阅数更新 |

**数据分层策略**（CompetitorVideo 采集效率优化）：
```
第一层（快速采集 0.5秒/个）：
  - youtube_id, title, channel_name, view_count, duration, published_at

第二层（详情采集 4秒/个）：
  - like_count, comment_count, description, tags, channel_id, subscriber_count

has_details 标记：快速判断是否需要补充详情
```

---

## 代码实现层实体定义

> 本章节记录核心模块的实现类，为开发参考。

<DataCollector>
- 文件位置：`src/research/data_collector.py:40`
- 职责：数据收集器，两阶段采集（快速搜索 + 详情获取）
- 核心方法：
  - `search_videos(keyword, max_results, region, time_range)` → 搜索视频
  - `search_videos_fast(keyword, max_results, save_to_db, time_range)` → 阶段1快速搜索
  - `enrich_video_details(min_views, limit)` → 阶段2详情获取
  - `search_videos_parallel(keyword, max_per_strategy, time_range)` → 并行多策略搜索
  - `collect_large_scale(theme, target_count)` → 大规模采集
  - `filter_quality_videos(videos, min_views)` → 质量筛选
  - `get_statistics()` → 数据库统计
- 依赖：YtDlpClient, CompetitorVideoRepository
</DataCollector>

<YtDlpClient>
- 文件位置：`src/research/yt_dlp_client.py:40`
- 职责：yt-dlp 封装客户端，YouTube 数据采集
- 核心属性：
  - TIME_FILTER_PARAMS：时间过滤参数（hour/today/week/month/year）
  - SORT_PARAMS：排序参数（relevance/date/view_count/rating）
  - TIME_AND_VIEW_SORT_PARAMS：组合参数（时间+播放量排序）
- 核心方法：
  - `search_videos(keyword, max_results, sort_by, time_range)` → 搜索视频
  - `get_video_info(video_id)` → 获取视频详情
- 约束：遵守 real.md#3 版权合规（仅获取公开元数据）
</YtDlpClient>

<YtDlpError>
- 文件位置：`src/research/yt_dlp_client.py:35`
- 职责：yt-dlp 相关错误的自定义异常类
- 继承：Exception
</YtDlpError>

<NetworkCentralityAnalyzer>
- 文件位置：`src/research/network_centrality.py:31`
- 职责：网络中心性分析，发现套利机会
- 网络定义：
  - 节点：视频、频道、话题
  - 边：视频-话题、频道-话题、话题共现
- 核心方法：
  - `calculate_topic_centrality()` → 话题中心性
  - `calculate_channel_centrality()` → 频道中心性
  - `calculate_video_centrality()` → 视频中心性
  - `calculate_title_word_centrality()` → 标题词中心性
  - `get_arbitrage_opportunities(top_n)` → 套利机会榜单
- 中心性算法：
  - 程度中心性 = 节点的邻居数 / (总节点数 - 1)
  - 中介中心性 = BFS 采样算法近似
  - 有趣度 = 中介中心性 / max(程度中心性, 0.01)
- 依赖：networkx（可选，有则使用；无则使用简化算法）
</NetworkCentralityAnalyzer>

<BaseModel>
- 文件位置：`src/shared/models/base.py:120`
- 职责：数据模型基类，提供序列化/反序列化
- 核心方法：
  - `to_dict()` → 转为字典（处理 Enum、datetime）
  - `from_dict(data)` → 从字典创建实例
  - `to_json()` / `from_json()` → JSON 序列化
- 子类：CompetitorVideo, Video, Script, Analytics 等
</BaseModel>

<TaskTypes>
- 文件位置：`src/shared/models/task.py:320`
- 职责：任务类型常量定义
- 常量分组：
  - 调研阶段：COLLECT_VIDEOS, ANALYZE_PATTERNS, GENERATE_REPORT
  - 策划阶段：CREATE_SPEC, GENERATE_SCRIPT, SEO_ANALYSIS
  - 制作阶段：GENERATE_AUDIO, CREATE_VIDEO, GENERATE_SUBTITLE, CREATE_THUMBNAIL
  - 发布阶段：UPLOAD_VIDEO, UPLOAD_THUMBNAIL, UPLOAD_SUBTITLE, SCHEDULE_PUBLISH
  - 复盘阶段：COLLECT_ANALYTICS, GENERATE_ANALYTICS_REPORT
</TaskTypes>

---

## 补充枚举定义

<AdditionalEnumerations>
以下枚举已在代码中定义，补充文档：

**脚本状态（ScriptStatus）**
| 值 | 说明 |
|---|---|
| draft | 草稿 |
| reviewing | 审阅中 |
| approved | 已通过 |
| archived | 已归档 |

**字幕类型（SubtitleType）**
| 值 | 说明 |
|---|---|
| auto | 自动生成 |
| manual | 手动创建 |
| translated | 翻译 |

**字幕格式（SubtitleFormat）**
| 值 | 说明 |
|---|---|
| srt | SRT 格式 |
| vtt | VTT 格式 |
| ass | ASS 格式 |
</AdditionalEnumerations>

---

## 便捷函数索引

| 函数 | 位置 | 功能 |
|------|------|------|
| `collect_and_filter(keyword, max_results, min_views)` | `data_collector.py` | 一键收集并筛选视频 |
| `expand_keywords_from_youtube(theme, max_keywords)` | `yt_dlp_client.py` | 从 YouTube 搜索建议扩展关键词 |
| `get_centrality_data(db_path)` | `network_centrality.py` | 获取中心性分析数据 |
| `get_network_graph_data(db_path, graph_type, max_nodes)` | `network_centrality.py` | 获取网络图可视化数据 |
| `parse_datetime(value)` | `base.py` | 解析多种格式的日期时间 |
| `parse_enum(enum_class, value, default)` | `base.py` | 安全解析枚举值 |
| `generate_uuid()` / `generate_short_id()` | `base.py` | 生成唯一标识符 |
