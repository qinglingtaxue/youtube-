# 流水线规格 (Pipeline Specification)

> 定义五阶段工作流的输入、输出、前置条件、后置检查
>
> **引用文档**：
> - 认知模型：`../.42cog/cog/cog.md`
> - 现实约束：`../.42cog/real/real.md`
> - 领域模型：`./前置准备/DOMAIN_MODEL.md`

---

## 概览

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ 调研    │ → │ 分析    │ → │ 模式    │ → │ 策划    │ → │ 制作    │ → │ 发布    │ → │ 复盘    │
│Research │   │Analysis │   │Pattern  │   │Planning │   │Production│  │Publishing│  │Analytics│
└────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
     │             │             │             │             │             │             │
     ▼             ▼             ▼             ▼             ▼             ▼             ▼
  视频数据     市场报告     42个模式       规约+脚本      视频文件     YouTube ID    数据报告
  1000+条      机会报告     学习路径       SEO策略       字幕+封面     发布状态     优化建议
              趋势快照      行动指南                                                    │
                                                                                       ▼
                                                                                 ┌──────────┐
                                                                                 │ 下轮迭代 │
                                                                                 └──────────┘
```

### 核心价值

> **四维矩阵：广度 × 深度 × 效能 × 洞察**
>
> | 维度 | 价值主张 | 具体体现 |
> |------|---------|---------|
> | **广度** | 五阶段端到端 | 调研→策划→制作→发布→复盘，全流程自动化 |
> | **深度** | 42plugin 生态 | 开箱即用 69 个组件 |
> | **效能** | 分层执行架构 | AI 理解 → RPA 执行 → Playwright 验收 |
> | **洞察** | 套利分析框架 | 有趣度公式发现被低估的创作机会 |
>
> **有趣度计算公式**：`信息有趣度 = 信息的价值程度 / 信息的传播程度`
>
> 利用中心性近似求解有趣度：在一个信息网络中，`某个节点的有趣度 = 中介中心性 / 程度中心性`

---

## Stage 1: 调研 (Research)

### 1.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `research` |
| display_name | 调研阶段 |
| order | 1 |
| 预计时长 | 1-4 小时 |
| 核心产出 | CompetitorVideo 列表 |

### 1.2 输入契约

```yaml
input:
  required:
    - theme: string            # 调研主题（如"老人养生"）
  optional:
    - target_count: integer    # 目标采集数量 (默认 1000)
    - sort_by: enum            # 排序方式: "date" | "relevance" | "view_count"
    - detail_min_views: integer # 获取详情的最小播放量阈值 (默认 5000)
    - detail_limit: integer    # 获取详情的数量上限 (默认 100)
```

### 1.3 输出契约

```yaml
output:
  database:
    - table: competitor_videos
      fields:
        - youtube_id: 视频ID
        - title: 标题
        - channel_name: 频道名
        - channel_id: 频道ID
        - view_count: 播放量
        - like_count: 点赞数
        - comment_count: 评论数
        - duration: 时长(秒)
        - published_at: 发布时间
        - collected_at: 采集时间
        - has_details: 是否有详情
      computed_fields:
        - days_since_publish: 发布天数
        - daily_growth: 日均增长
        - time_bucket: 时间分桶
        - engagement_rate: 互动率

  files:
    - path: "data/daily_reports/collect_{YYYYMMDD_HHMMSS}.json"
      type: CollectionReport
      required: true
```

### 1.4 前置条件

```yaml
preconditions:
  tools:
    - name: yt-dlp
      check: "yt-dlp --version"
      min_version: "2025.1.0"
    - name: sqlite3
      check: "sqlite3 --version"

  constraints:
    - ref: "real.md#存储与成本控制"
      check: "磁盘剩余空间 > 10GB"
```

### 1.5 后置检查

```yaml
postconditions:
  validation:
    - "新增视频数 > 0 或 数据库已有足够视频"
    - "视频元数据完整（title, view_count, published_at）"

  quality:
    - "高播放量视频（>5000）已获取详情"
    - "采集日志已记录"
```

### 1.6 CLI 命令

```bash
# 大规模采集
python cli.py research collect --theme "老人养生" --count 1000

# 查看统计
python cli.py research stats
```

### 1.7 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| youtube-downloader | Skill | 下载竞品视频 |
| youtube-transcript | Skill | 提取字幕 |
| youtube-to-markdown | Skill | 视频元数据转 MD |
| data-collector | Module | 数据采集器 |

---

## Stage 1.5: 分析 (Analysis)

### 1.5.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `analysis` |
| display_name | 分析阶段 |
| order | 1.5 |
| 预计时长 | 5-30 秒（自动化） |
| 核心产出 | MarketReport, OpportunityReport, TrendSnapshot |

### 1.5.2 输入契约

```yaml
input:
  required:
    - competitor_videos: CompetitorVideo[]  # 来自 Stage 1 数据库
  optional:
    - time_window: enum      # 时间窗口: "1d" | "15d" | "30d" | "all"
    - min_views: integer     # 最小播放量筛选 (默认 0)
```

### 1.5.3 输出契约

```yaml
output:
  reports:
    - type: MarketReport
      content:
        market_size:
          - sample_videos: 样本视频数
          - total_views: 总播放量
          - avg_views: 平均播放量
          - median_views: 中位数播放量
        channel_competition:
          - total_channels: 总频道数
          - concentration: 集中度(top10_share, top20_share)
          - size_distribution: 规模分布(单视频、小型、中型、大型)
        entry_barriers:
          - performance_tiers: 播放量分层(100万+、10-100万、1-10万...)
          - viral_rate: 爆款率
          - top_10_percent_threshold: Top10%门槛
        time_context:
          - date_range: 数据时间范围(earliest, latest, span)
          - time_distribution: 时间分布(24小时内、7天内、30天内...)

    - type: OpportunityReport
      content:
        recent_viral_by_window:
          - 时间窗口: 24小时内、7天内、30天内、90天内、6个月内
          - top_performers: 每个窗口的头部视频
        high_daily_growth:
          - threshold: 日增阈值(默认500)
          - top_performers: 高增长视频列表
        small_channel_hits:
          - definition: 1-3视频的频道
          - success_threshold: 成功阈值(播放量 > 中位数 * 5)
        high_engagement_templates:
          - engagement_rate_threshold: 互动率阈值(3%)
        opportunity_summary:
          - best_time_window: 最佳时间窗口
          - recommendations: 建议列表
          - action_items: 行动项

  files:
    - path: "public/index.html"
      type: OverviewReport
      required: true
      description: "概览页面：核心数据卡片、播放量分布、市场边界、时间分析"
    - path: "public/arbitrage.html"
      type: ArbitrageReport
      required: true
      description: "套利分析页面：6种套利类型分析、有趣度公式"
    - path: "public/content-map.html"
      type: ContentMapReport
      required: true
      description: "内容四象限页面：播放量×互动率分析"
    - path: "public/creators.html"
      type: CreatorsReport
      required: true
      description: "创作者分析页面：频道排行、规模分布"
    - path: "public/titles.html"
      type: TitlesReport
      required: true
      description: "标题公式页面：词频分析、标题模式"
    - path: "public/actions.html"
      type: ActionsReport
      required: true
      description: "行动建议页面：具体行动项、优先级"

  database:
    - table: trend_snapshots
      fields:
        - video_id: 关联视频ID
        - snapshot_time: 快照时间
        - views: 播放量
        - likes: 点赞数
        - comments: 评论数
        - growth: 与上次快照的增长差值
```

### 1.5.4 报告页面结构

> 报告输出为 6 个独立 HTML 页面，通过顶部导航链接

```yaml
pages:
  1_overview:
    file: "index.html"
    name: "概览"
    content:
      - 核心数据卡片（总视频、总播放、平均播放、发布窗口）
      - 视频播放量分布图（直方图）
      - 标签页内容：市场边界、时间分析、创作机会

  2_arbitrage:
    file: "arbitrage.html"
    name: "套利分析"
    content:
      - 6种套利类型分析（话题、频道、时长、趋势、跨语言、跟进）
      - 有趣度公式可视化
      - 套利机会表格

  3_content_map:
    file: "content-map.html"
    name: "内容四象限"
    content:
      - 播放量×互动率四象限图
      - 各象限视频分布
      - 象限策略建议

  4_creators:
    file: "creators.html"
    name: "创作者分析"
    content:
      - 头部创作者排行
      - 频道规模分布
      - 频道成功率分析

  5_titles:
    file: "titles.html"
    name: "标题公式"
    content:
      - 高播放标题词频分析
      - 标题长度与播放量关系
      - 标题模式提取

  6_actions:
    file: "actions.html"
    name: "行动建议"
    content:
      - 基于分析的具体行动项
      - 优先级排序
      - 快速启动指南
```

### 1.5.5 时间窗口定义

```yaml
user_facing_windows:
  - name: "1天内"
    days: 1
    use: "实时热点追踪"
  - name: "15天内"
    days: 15
    use: "短期趋势分析"
  - name: "30天内"
    days: 30
    use: "月度表现评估"
  - name: "全部"
    days: null
    use: "全量数据分析"

internal_time_buckets:
  - name: "24小时内"
    range: "0-1天"
  - name: "7天内"
    range: "1-7天"
  - name: "30天内"
    range: "7-30天"
  - name: "90天内"
    range: "30-90天"
  - name: "6个月内"
    range: "90-180天"
  - name: "1年内"
    range: "180-365天"
  - name: "1年以上"
    range: "365+天"
```

### 1.5.6 前置条件

```yaml
preconditions:
  dependencies:
    - stage: research
      status: completed
      min_videos: 100  # 至少需要100个视频才能生成有意义的分析

  constraints:
    - "数据库中有足够的视频数据"
```

### 1.5.7 后置检查

```yaml
postconditions:
  validation:
    - "6个 HTML 报告文件存在且可打开"
    - "页面间导航链接正常工作"
    - "所有图表正确渲染"

  quality:
    - "机会识别至少返回1条有效建议"
    - "套利分析包含可执行建议"
    - "行动建议页面有具体行动项"
```

### 1.5.8 CLI 命令

```bash
# 生成市场分析报告
python cli.py analytics market --time-window 30d

# 生成机会识别报告
python cli.py analytics opportunities --time-window 15d

# 生成综合HTML报告
python cli.py analytics report

# 拍摄播放量快照（用于趋势追踪）
python cli.py monitor snapshot --min-views 1000

# 查看增长趋势
python cli.py monitor trends --window 15d
```

### 1.5.9 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| pattern-analyzer | Module | 市场模式分析 |
| comprehensive-report | Module | HTML报告生成 |
| trend-monitor | Module | 趋势监控与快照 |

### 1.5.10 部署

```yaml
deployment:
  platform: Vercel
  url: "https://youtube-analysis-report.vercel.app"

  files:
    - source: "public/*.html"
      destination: "/"
      description: "6个报告页面直接部署到根目录"

  config: "vercel.json"

  structure:
    - "/ → index.html (概览)"
    - "/arbitrage.html (套利分析)"
    - "/content-map.html (内容四象限)"
    - "/creators.html (创作者分析)"
    - "/titles.html (标题公式)"
    - "/actions.html (行动建议)"
```

---

## Stage 1.6: 套利分析 (Arbitrage Analysis)

> **有趣度计算公式**：`信息有趣度 = 信息的价值程度 / 信息的传播程度`
>
> 利用中心性近似求解有趣度：在一个信息网络中，`某个节点的有趣度 = 中介中心性 / 程度中心性`
>
> 高有趣度 = 价值被低估 = 套利机会

### 1.6.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `arbitrage` |
| display_name | 套利分析阶段 |
| order | 1.6 |
| 预计时长 | 10-60 秒（自动化） |
| 核心产出 | ArbitrageReport, BridgeTopic, CreatorProfile |

### 1.6.2 输入契约

```yaml
input:
  required:
    - competitor_videos: CompetitorVideo[]  # 来自 Stage 1 数据库
  optional:
    - min_videos: integer       # 最小样本量 (默认 100)
    - creator_type: enum        # 博主类型: "beginner" | "mid_tier" | "top_tier"
```

### 1.6.3 输出契约

```yaml
output:
  reports:
    - type: ArbitrageReport
      content:
        topic_arbitrage:
          - network_stats: 关键词网络统计（节点数、边数、密度）
          - bridge_topics: 桥梁话题列表（高中介中心性）
          - insight: 话题套利洞察
        channel_arbitrage:
          - small_channel_opportunities: 小频道爆款机会
          - replicable_patterns: 可复制的成功模式
          - insight: 频道套利洞察
        duration_arbitrage:
          - buckets: 时长分桶分析（供需不平衡）
          - best_duration: 最佳时长区间
          - insight: 时长套利洞察
        timing_arbitrage:
          - rising_topics: 上升趋势话题
          - falling_topics: 下降趋势话题
          - insight: 趋势套利洞察
        summary:
          - opportunities: 发现的套利机会列表
          - summary_text: 综合摘要

    - type: CreatorProfile
      content:
        type: 博主类型
        suitable_arbitrage: 适合的套利类型列表
        strategy: 推荐策略
        action_items: 具体行动项

  files:
    - path: "data/analysis/arbitrage_report_{YYYYMMDD_HHMMSS}.json"
      type: ArbitrageReport
      required: true
```

### 1.6.4 套利类型定义

```yaml
arbitrage_types:
  topic:
    name: 话题套利
    formula: "中介中心性 / 程度中心性"
    meaning: "能连接多群体但传播不足的话题"
    suitable_for: ["beginner", "mid_tier"]

  channel:
    name: 频道套利
    formula: "最高播放 / 频道平均播放"
    meaning: "小频道爆款，内容本身有价值"
    suitable_for: ["beginner"]

  duration:
    name: 时长套利
    formula: "平均播放量 / 供给占比"
    meaning: "播放量高但供给不足的时长"
    suitable_for: ["beginner", "mid_tier"]

  timing:
    name: 趋势套利
    formula: "近期频率 / 历史频率"
    meaning: "上升趋势话题，提前布局"
    suitable_for: ["top_tier"]

  cross_language:
    name: 跨语言套利
    formula: "源市场播放量 / 目标市场视频数"
    meaning: "源市场火爆但目标市场空白"
    suitable_for: ["top_tier"]

  follow_up:
    name: 跟进套利
    formula: "爆款播放量 / 爆款后同话题视频数"
    meaning: "爆款后市场跟进程度"
    suitable_for: ["mid_tier", "top_tier"]
```

### 1.6.5 博主定位策略

```yaml
creator_profiles:
  beginner:
    name: 小白博主
    resources: "无流量、无经验"
    suitable_arbitrage: ["topic", "duration", "channel"]
    strategy: "找供给不足的细分，模仿小频道爆款"

  mid_tier:
    name: 腰部博主
    resources: "有基础、有粉丝"
    suitable_arbitrage: ["topic", "duration", "follow_up"]
    strategy: "连接两个受众群体，跨品类迁移"

  top_tier:
    name: 头部博主
    resources: "有流量、有资源"
    suitable_arbitrage: ["timing", "cross_language", "follow_up"]
    strategy: "早期布局新趋势，翻译套利"
```

### 1.6.6 前置条件

```yaml
preconditions:
  dependencies:
    - stage: research
      status: completed
      min_videos: 100  # 至少需要100个视频

  tools:
    - name: networkx
      check: "python -c 'import networkx'"
    - name: jieba
      check: "python -c 'import jieba'"

  constraints:
    - "数据库中有足够的视频数据（≥100）"
```

### 1.6.7 后置检查

```yaml
postconditions:
  validation:
    - "套利报告包含至少一种套利类型的分析结果"
    - "桥梁话题有趣度计算正确"
    - "博主定位建议与资源匹配"

  quality:
    - "至少发现 3 个套利机会"
    - "每个套利机会包含可执行的行动建议"
```

### 1.6.8 CLI 命令

```bash
# 综合套利分析
python cli.py arbitrage analyze

# 话题套利分析（关键词网络）
python cli.py arbitrage topic

# 频道套利分析（小频道爆款）
python cli.py arbitrage channel

# 时长套利分析（供需不平衡）
python cli.py arbitrage duration

# 趋势套利分析（上升/下降话题）
python cli.py arbitrage timing

# 博主定位建议
python cli.py arbitrage profile --type beginner
```

### 1.6.9 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| arbitrage-analyzer | Module | 套利分析核心逻辑 |
| keyword-network | Module | 关键词共现网络构建 |
| creator-profiler | Module | 博主定位匹配 |

---

## Stage 1.7: 模式分析 (Pattern Analysis)

> **数据规模**：N=2,340 中文视频 + 172 多语言视频，42 个已发现模式

### 1.7.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `pattern_analysis` |
| display_name | 模式分析阶段 |
| order | 1.7 |
| 预计时长 | 10-30 秒（自动化） |
| 核心产出 | PatternReport, LearningPath |

### 1.7.2 输入契约

```yaml
input:
  required:
    - competitor_videos: CompetitorVideo[]  # 来自 Stage 1 数据库
  optional:
    - dimensions: string[]    # 分析维度: ["variable", "temporal", "spatial", "channel", "user"]
    - min_sample_size: integer  # 最小样本量 (默认 100)
```

### 1.7.3 输出契约

```yaml
output:
  reports:
    - type: PatternReport
      content:
        variable_dimension:
          - title_length_analysis: 标题长度与播放量关系
          - duration_distribution: 视频时长分布分析
          - topic_heat_distribution: 话题热度分布
        temporal_dimension:
          - publish_timing: 发布时机分析
          - topic_cycle: 话题热度周期规律
        spatial_dimension:
          - cross_language_comparison: 跨语言市场对比
          - cpm_revenue_analysis: CPM 收益分析
          - cross_market_arbitrage: 跨市场套利机会
        channel_dimension:
          - dark_horse_channels: 黑马频道特征
          - fast_growth_cases: 快速增长案例
          - subscriber_efficiency: 订阅与效率关系
        user_dimension:
          - comment_hotwords: 评论热词分析
          - user_questions: 用户问题提取
          - sentiment_analysis: 情感分析
        action_guide:
          - content_gaps: 内容缺口机会
          - top5_actions: Top5 行动清单
          - final_decision: 终极决策建议

    - type: LearningPath
      content:
        blocks: 3 个主 Tab + 1 个外链 + 1 个隐藏 Tab（集成在 insight-system.html）
        patterns_count: 42
        stats: 视频数、频道数、总播放、天跨度、洞察数

  files:
    - path: "work/模式洞察-索引.md"
      type: PatternReport
      required: true
      description: "42 个模式的完整索引"
    - path: "web/insight-system.html"
      type: InsightSystem
      required: true
      description: "洞察系统页面（3个主Tab：全局认识/套利分析/信息报告 + 创作者行动中心外链 + 隐藏的用户洞察Tab）"
      tab_structure:
        - tab1_global: "🌍 全局认识（5个子标签：数据概览/频道分析/内容类型分析/播放趋势/市场边界）"
        - tab2_arbitrage: "💰 套利分析（6个子标签：话题套利/时长套利/频道套利/趋势套利/跨语言套利/综合套利）"
        - tab7_report: "📋 信息报告（4个子标签：数据报告/结论摘要/数据导出/语言分布）"
        - external_link: "🎬 创作者行动中心 → creator-action.html"
        - tab8_user: "👥 用户洞察（隐藏，5个子标签：用户画像/评论热词/情感分析/问题提取/需求洞察）"
      js_modules:
        - insight-core.js: "核心框架、Tab切换、状态管理"
        - insight-charts.js: "Chart.js 图表封装"
        - insight-report.js: "信息报告 Tab (Tab 7)"
        - insight-user.js: "用户洞察 Tab (Tab 8，隐藏)"
        - insight-global.js: "全局认识 Tab (Tab 1)"
        - insight-content.js: "内容分析相关"
        - insight.js: "入口文件、模块协调"
    - path: "web/pattern-detail.html"
      type: PatternDetail
      required: true
      description: "单个模式详情页面"
    - path: "web/legacy/learning-path.html"
      type: LearningPath
      required: false
      description: "[已归档] 原独立学习路径页面"
```

### 1.7.4 分析维度定义

```yaml
dimensions:
  variable:
    name: 变量分布
    patterns:
      - 标题长度效果（长标题 4 倍于短标题）
      - 视频时长最优区间（10-30 分钟）
      - 话题热度分布
    output_files: ["模式洞察-变量分布-*.md"]

  temporal:
    name: 时间维度
    patterns:
      - 发布时机（周末效果更好）
      - 话题热度周期规律
    output_files: ["模式洞察-时间维度-*.md"]

  spatial:
    name: 空间维度
    patterns:
      - 英语市场均播分析
      - CPM 收益对比
      - Tai Chi 英语市场爆发（+533%）
    output_files: ["模式洞察-空间维度-*.md"]

  channel:
    name: 频道维度
    patterns:
      - 黑马频道特征
      - 快速增长案例
      - 订阅与效率关系
    output_files: ["模式洞察-频道维度-*.md"]

  user:
    name: 用户维度
    patterns:
      - 评论热词
      - 用户问题
      - 情感分析
      - 用户画像
    output_files: ["模式洞察-用户维度-*.md"]
```

### 1.7.5 核心发现示例

| 发现 | 有趣度 | 说明 |
|------|--------|------|
| 互动率与播放量负相关 | 5.0 | 反常识，需深入分析 |
| 长标题效果是短标题 4 倍 | 4.5 | 验证后可直接应用 |
| Tai Chi 英语市场爆发 +533% | 4.0 | 跨语言套利机会 |
| 穴位按摩内容缺口 | 4.5 | Google ↑76%，YouTube 仅 7 条 |

### 1.7.6 前置条件

```yaml
preconditions:
  dependencies:
    - stage: research
      status: completed
      min_videos: 100

  constraints:
    - "数据库中有足够的视频数据（≥100）"
```

### 1.7.7 后置检查

```yaml
postconditions:
  validation:
    - "模式报告包含至少 5 个维度的分析"
    - "每个模式包含有趣度评分和置信度"
    - "学习路径页面可正常访问"

  quality:
    - "至少发现 10 个有趣度 ≥ 3.0 的模式"
    - "行动指南包含可执行的建议"
```

### 1.7.8 CLI 命令

```bash
# 生成模式分析报告
python cli.py pattern analyze

# 按维度分析
python cli.py pattern analyze --dimension variable
python cli.py pattern analyze --dimension temporal
python cli.py pattern analyze --dimension spatial

# 生成学习路径页面
python cli.py pattern learning-path

# 查看单个模式详情
python cli.py pattern detail --id 23
```

### 1.7.9 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| pattern-analyzer | Module | 模式识别核心逻辑 |
| interestingness-calculator | Module | 有趣度计算 |
| learning-path-generator | Module | 学习路径生成 |

---

## Stage 2: 策划 (Planning)

### 2.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `planning` |
| display_name | 策划阶段 |
| order | 2 |
| 预计时长 | 2-4 小时 |
| 核心产出 | Spec, Script |

### 2.2 输入契约

```yaml
input:
  required:
    - research_report: ResearchReport   # 来自 Stage 1
  optional:
    - brand_voice: BrandVoiceConfig     # 品牌声音配置
    - target_duration: integer          # 目标时长 (秒)
    - style: enum                       # 风格: "tutorial" | "story" | "review"
```

### 2.3 输出契约

```yaml
output:
  files:
    - path: "specs/video_spec_{video_id}.md"
      type: Spec
      required: true
      schema:
        - topic: string
        - target_duration: integer
        - style: enum
        - event_1: string        # 引入问题
        - event_2: string        # 展示方案
        - event_3: string        # 总结升华
        - meaning: string        # 生发意义
        - target_audience: string
        - cta: string            # 行动号召

    - path: "scripts/video_script_{video_id}.md"
      type: Script
      required: true
      schema:
        - title: string
        - content: text (Markdown)
        - word_count: integer
        - estimated_duration: integer

    - path: "scripts/seo_report_{video_id}.json"
      type: SEOReport
      required: false
      schema:
        - seo_score: integer (0-100)
        - title_keywords: string[]
        - description_keywords: string[]
        - suggested_tags: string[]
```

### 2.4 前置条件

```yaml
preconditions:
  dependencies:
    - stage: research
      status: completed
      outputs: [ResearchReport]

  constraints:
    - ref: "real.md#YouTube 社区准则红线"
      check: "内容主题不违反社区准则"
```

### 2.5 后置检查

```yaml
postconditions:
  validation:
    - "Spec 文件符合三事件结构"
    - "Script word_count > 500"
    - "Script estimated_duration 在 target_duration ±20% 范围内"

  quality:
    - "SEO 评分 >= 70"
    - "标题长度 50-60 字符"
    - ref: "real.md#SEO 最佳实践"
```

### 2.6 关联 Prompts

- `prompts/PROMPT_03_策划阶段.md`

### 2.7 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| content-creator | Skill | 品牌声音 + SEO 优化 |
| ideation | Skill | 创意构思 |
| spec-generator | Skill | 规约文档生成 |
| marketing | Agent | 品牌营销策略 |
| seo-content-writer | Agent | SEO 内容创作 |

---

## Stage 3: 制作 (Production)

### 3.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `production` |
| display_name | 制作阶段 |
| order | 3 |
| 预计时长 | 4-8 小时 |
| 核心产出 | Video, Subtitle, Thumbnail |

### 3.2 输入契约

```yaml
input:
  required:
    - spec: Spec               # 来自 Stage 2
    - script: Script           # 来自 Stage 2
  optional:
    - assets: Asset[]          # 预备素材
    - voiceover_provider: enum # "elevenlabs" | "minimax" | "recorded"
    - resolution: enum         # "1080p" | "4K"
```

### 3.3 输出契约

```yaml
output:
  files:
    - path: "data/videos/{video_id}.mp4"
      type: Video
      required: true
      constraints:
        - format: mp4
        - resolution: >= 1080p
        - duration: spec.target_duration ±10%

    - path: "data/transcripts/{video_id}.vtt"
      type: Subtitle
      required: true
      constraints:
        - format: vtt | srt
        - language: script.language

    - path: "data/thumbnails/{video_id}.jpg"
      type: Thumbnail
      required: true
      constraints:
        - resolution: >= 1280x720
        - format: jpg | png
        - file_size: < 2MB

  database:
    - table: video
      fields: [video_id, title, file_path, duration, resolution, status]
      status_update: "draft → producing → ready"
    - table: subtitle
      fields: [subtitle_id, video_id, language, type, file_path]
    - table: thumbnail
      fields: [thumbnail_id, video_id, file_path, is_active]
```

### 3.4 前置条件

```yaml
preconditions:
  dependencies:
    - stage: planning
      status: completed
      outputs: [Spec, Script]

  tools:
    - name: ffmpeg
      check: "ffmpeg -version"
      min_version: "6.0"
    - name: whisper
      check: "whisper --help"
      note: "仅在需要转录时必需"

  constraints:
    - ref: "real.md#版权合规"
      check: "所有素材来源已记录"
    - ref: "real.md#存储与成本控制"
      check: "磁盘剩余空间 > 20GB"
```

### 3.5 后置检查

```yaml
postconditions:
  validation:
    - "Video 文件存在且可播放"
    - "Video 时长与 spec.target_duration 误差 < 10%"
    - "Subtitle 时间轴与 Video 同步"
    - "Thumbnail 分辨率 >= 1280x720"

  quality:
    - "视频无明显画质问题"
    - "音频清晰，无杂音"
    - "字幕无错别字 (AI 检测)"
```

### 3.6 关联 Prompts

- `prompts/PROMPT_04_制作阶段.md`

### 3.7 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| transcript-fixer | Skill | 字幕修复优化 |
| video-comparer | Skill | 视频对比分析 |

---

## Stage 4: 发布 (Publishing)

### 4.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `publishing` |
| display_name | 发布阶段 |
| order | 4 |
| 预计时长 | 0.5-1 小时 |
| 核心产出 | UploadTask (completed), youtube_id |

### 4.2 输入契约

```yaml
input:
  required:
    - video: Video             # 来自 Stage 3, status = "ready"
    - subtitle: Subtitle       # 来自 Stage 3
    - thumbnail: Thumbnail     # 来自 Stage 3
    - script: Script           # 用于填写元数据
  optional:
    - schedule_time: datetime  # 定时发布时间
    - privacy: enum            # "public" | "unlisted" | "private"
    - playlist: string         # 播放列表名称
```

### 4.3 输出契约

```yaml
output:
  updates:
    - entity: Video
      field: youtube_id
      value: "发布后获得的 YouTube 视频 ID"
    - entity: Video
      field: status
      value: "published" | "scheduled"
    - entity: UploadTask
      field: status
      value: "completed"

  files:
    - path: "logs/upload_report_{YYYYMMDD}.json"
      type: UploadReport
      schema:
        - video_id: string
        - youtube_id: string
        - upload_time: datetime
        - status: enum
        - token_consumed: integer
```

### 4.4 前置条件

```yaml
preconditions:
  dependencies:
    - stage: production
      status: completed
      outputs: [Video, Subtitle, Thumbnail]

  tools:
    - name: mcp-chrome
      check: "curl http://127.0.0.1:12306/health"
      note: "需要 Chrome 已登录 YouTube"

  constraints:
    - ref: "real.md#YouTube 社区准则红线"
      check: "内容已通过人工/AI 审核"
    - ref: "real.md#API/自动化限制"
      check: "当日上传次数未超限"
    - ref: "real.md#发布时间优化"
      check: "发布时间在目标受众活跃时段 (可选)"
```

### 4.5 后置检查

```yaml
postconditions:
  validation:
    - "youtube_id 格式正确 (11 字符)"
    - "视频在 YouTube Studio 中可见"
    - "元数据填写完整 (标题、描述、标签)"
    - "字幕已上传并启用"
    - "封面已设置"

  quality:
    - "视频状态为 '已发布' 或 '已排程'"
    - "Token 消耗 < 2000 (综合模式)"
```

### 4.6 关联 Prompts

- `prompts/PROMPT_05_发布阶段.md`

### 4.7 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| viral-automation | Command | 病毒式传播自动化 |
| website-automation | Command | 网站自动化操作 |

### 4.8 执行模式

```yaml
execution_mode: hybrid  # 综合模式

workflow:
  1_understand:
    executor: AI
    token_budget: ~1000
    action: "解析上传参数，生成结构化配置"

  2_execute:
    executor: RPA (youtube-tool.py)
    token_budget: 0
    action: "执行上传、填写元数据"

  3_verify:
    executor: Playwright / DOM 检查
    token_budget: ~500 (仅失败时)
    action: "验证上传状态，失败则重新探索"
```

---

## Stage 5: 复盘 (Analytics)

### 5.1 阶段定义

| 属性 | 值 |
|------|-----|
| stage_name | `analytics` |
| display_name | 复盘阶段 |
| order | 5 |
| 预计时长 | 1-2 小时 |
| 核心产出 | Analytics, 优化建议 |
| 触发时机 | 发布后 7 天 / 30 天 |

### 5.2 输入契约

```yaml
input:
  required:
    - youtube_id: string       # 来自 Stage 4
    - published_at: datetime   # 发布时间
  optional:
    - period: enum             # 分析周期: "7d" | "30d" | "lifetime"
    - compare_videos: string[] # 对比视频 ID 列表
```

### 5.3 输出契约

```yaml
output:
  files:
    - path: "data/reports/analytics_{video_id}_{period}.md"
      type: AnalyticsReport
      schema:
        - views: integer
        - watch_time_minutes: integer
        - average_view_duration: integer
        - ctr: float
        - likes: integer
        - comments: integer
        - subscribers_gained: integer

    - path: "data/reports/optimization_{video_id}.md"
      type: OptimizationSuggestions
      schema:
        - cover_suggestions: string[]
        - title_suggestions: string[]
        - content_suggestions: string[]
        - next_topic_ideas: string[]

  database:
    - table: analytics
      fields: [video_id, report_date, period, views, ctr, ...]
```

### 5.4 前置条件

```yaml
preconditions:
  dependencies:
    - stage: publishing
      status: completed
      min_elapsed_time: "7 days"  # 至少发布 7 天后

  tools:
    - name: mcp-chrome
      check: "curl http://127.0.0.1:12306/health"
      note: "用于抓取 YouTube Studio 数据"
```

### 5.5 后置检查

```yaml
postconditions:
  validation:
    - "AnalyticsReport 包含核心指标"
    - "数据已存入 analytics 表"

  quality:
    - "报告包含与预期对比分析"
    - "报告包含可执行的优化建议"
    - "报告包含下期内容方向"
```

### 5.6 关联 Prompts

- `prompts/PROMPT_06_复盘阶段.md`

### 5.7 关联 Skills/Agents

| 组件 | 类型 | 用途 |
|------|------|------|
| blog-workflow | Hook | 内容质量检查 |

### 5.8 反馈闭环

```yaml
feedback_loop:
  source: OptimizationSuggestions
  target: Stage 1 (Research)

  actions:
    - "将 next_topic_ideas 作为下轮调研关键词"
    - "将 content_suggestions 纳入 brand_voice 配置"
    - "更新标签策略 (基于 CTR 分析)"
```

---

## 阶段流转规则

### 状态机

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Video 状态流转                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [draft] ──策划完成──→ [scripting] ──制作开始──→ [producing]        │
│                                                                     │
│  [producing] ──制作完成──→ [ready] ──上传成功──→ [published]        │
│                                       │                             │
│                                       └──定时发布──→ [scheduled]    │
│                                                                     │
│  任何状态 ──失败/取消──→ [draft] (回退)                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 阶段依赖

```yaml
dependencies:
  analysis:
    requires: [research]
    can_skip: false
    min_videos: 100  # 至少需要100个视频

  planning:
    requires: [analysis]  # 策划依赖分析报告
    can_skip: false

  production:
    requires: [planning]
    can_skip: false

  publishing:
    requires: [production]
    can_skip: false

  analytics:
    requires: [publishing]
    can_skip: true  # 可跳过复盘直接进入下轮
    delay: "7d"     # 至少等待 7 天
```

### 并行执行

```yaml
parallelization:
  allowed:
    - "多个视频可同时处于不同阶段"
    - "同一阶段的多个任务可并行 (如批量调研)"

  forbidden:
    - "同一视频不能同时在多个阶段执行"
    - "发布阶段不允许并行 (避免账号风控)"
```

---

## 约束检查点

| 检查点 | 阶段 | 约束引用 | 检查方式 |
|--------|------|----------|----------|
| API 配额 | research, publishing | real.md#3 | 配额计数器 |
| 存储空间 | research, production | real.md#4 | `df -h` |
| 社区准则 | planning, publishing | real.md#1 | 人工/AI 审核 |
| 版权合规 | production | real.md#2 | 素材来源记录 |
| SEO 规范 | planning | real.md#6 | seo_optimizer.py |
| 发布时间 | publishing | real.md#5 | 定时发布配置 |
| 数据充足 | analysis | - | 至少100个视频 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-18 | 初始版本，定义五阶段规格 |
| 1.1 | 2026-01-19 | 新增分析阶段(Stage 1.5)，包含市场报告、机会报告、趋势监控 |
| 1.2 | 2026-01-19 | 新增套利分析阶段(Stage 1.6)，包含有趣度公式、6种套利类型、博主定位策略 |
| 1.3 | 2026-01-19 | 更新报告输出结构为6个独立HTML页面（概览、套利分析、内容四象限、创作者分析、标题公式、行动建议）|
| 1.4 | 2026-01-24 | 新增模式分析阶段(Stage 1.7)，包含 5 个分析维度、42 个已发现模式、学习路径页面 |
| 1.5 | 2026-01-24 | 更新有趣度公式表述，区分原理层和求解层 |
| 1.6 | 2026-01-24 | 学习路径集成到 insight-system.html（7标签页），原 learning-path.html 归档至 web/legacy/ |
| 1.7 | 2026-02-01 | 更正洞察系统页面结构：3个主Tab（全局认识/套利分析/信息报告）+ 创作者行动中心外链 + 隐藏的用户洞察Tab；记录7模块JS架构 |

---

*引用本规格时使用：`.42cog/spec/pm/pipeline.spec.md`*
