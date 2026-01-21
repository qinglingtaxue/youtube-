---
name: project-cog
description: YouTube 内容创作者运营平台的认知模型
---

# 认知模型 (Cog)

> 本系统的核心认知：**数据驱动选题发现，可视化呈现市场格局，可解释 AI 辅助决策**
>
> 用户旅程：`输入关键词 → 数据采集 → 多维分析 → 可视化呈现 → 洞察生成 → 行动建议`
>
> **核心价值**：不是简单的数据罗列，而是**有框架的分析 + 可解释的洞察 + 可执行的建议**

<cog>
本系统包括以下关键实体：

**核心数据流（信息源）**
- CompetitorVideo：竞品视频，数据采集的核心对象
- Channel：YouTube 频道，聚合分析的维度
- TrendSnapshot：趋势快照，追踪视频增长变化

**分析框架（认知模型）**
- ContentQuadrant：内容四象限，播放量×互动率的二维分类
  - Star（爆款型）：高播放+高互动，学习标杆
  - Niche（粉丝向）：低播放+高互动，深耕细分
  - Viral（破圈型）：高播放+低互动，优化互动
  - Dog（冷门型）：低播放+低互动，避免重复
- DurationMatrix：时长分布矩阵，时长×平均播放的供需分析
- ArbitrageFramework：套利分析框架，有趣度公式发现价值洼地

**可视化层（呈现系统）**
- InsightCard：洞察卡片，可折叠展开的分析单元
- ConfidenceBar：置信度条，表示洞察可靠性
- ReasoningChain：推理链，展示 AI 得出结论的过程
- DataSourceTag：数据源标签，关联原始数据
- ScatterChart：散点图，四象限可视化
- BarChart：条形图，分布可视化

**报告实体（输出物）**
- AnalysisReport：分析报告，综合数据洞察
- MarketReport：市场报告，定义市场边界和竞争格局
- OpportunityReport：机会报告，识别创作者切入点
- ArbitrageReport：套利报告，发现价值被低估的机会
- DiagnoseReport：诊断报告，频道健康度评估

**交互实体（用户界面）**
- SearchPanel：搜索面板，关键词输入和筛选条件
- FilterChip：筛选标签，多维度数据过滤
- RankingList：榜单列表，视频/频道排行
- MonitorTask：监控任务，定时数据采集
- TrendingTracker：趋势追踪，增长数据监控

**套利实体（价值发现）**
- ArbitrageOpportunity：套利机会，具体可执行的创作方向
- BridgeTopic：桥梁话题，连接多受众群体的关键词
- CreatorProfile：博主画像，匹配适合的套利策略
- KeywordNetwork：关键词网络，话题共现关系图
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
- 核心属性：
  - keyword：监控关键词
  - interval：采集间隔
  - last_run：上次运行时间
  - next_run：下次运行时间
  - status：状态（pending、running、completed、failed）
  - video_count：已采集视频数
</MonitorTask>

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
- ContentQuadrant → ScatterChart：一对一（四象限生成散点图）
- DurationMatrix → BarChart：一对一（时长分布生成条形图）

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
- 暗色主题 UI（#0f172a 背景）
- WebSocket 实时通信

**后端架构**：
- Python FastAPI
- yt-dlp 数据采集
- SQLite/JSON 数据存储

**API 通信**：
- WebSocket：实时进度推送
- REST：数据查询和操作

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
| 竞品报告 | `public/index.html` | AnalysisReport, MarketReport | 数据概览、市场边界 |
| 套利分析 | `public/arbitrage.html` | ArbitrageReport, ArbitrageOpportunity | 套利机会发现 |
| 内容四象限 | `public/content-map.html` | ContentQuadrant, ScatterChart | 播放量×互动率矩阵 |
| 创作者分析 | `public/creators.html` | Channel, DiagnoseReport | 频道对比 |
| 标题公式 | `public/titles.html` | CompetitorVideo | 高播放标题特征 |
| 行动建议 | `public/actions.html` | ArbitrageOpportunity | 具体操作指引 |
| 洞察系统 | `web/insight-system.html` | InsightCard, ReasoningChain | 可解释 AI 洞察 |

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

## API 与实体映射

| API 端点 | 操作实体 | 功能 |
|----------|----------|------|
| `GET /ws/{task_id}` | CompetitorVideo | WebSocket 数据采集 |
| `GET /api/channel/{id}` | Channel | 获取频道详情 |
| `POST /api/channels/batch` | Channel | 批量获取频道数据 |
| `GET /api/videos` | CompetitorVideo | 视频列表查询 |
| `POST /api/monitor` | MonitorTask | 创建监控任务 |
| `GET /api/trends/{keyword}` | TrendSnapshot | 获取趋势数据 |

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
