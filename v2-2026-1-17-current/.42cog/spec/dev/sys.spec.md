# 系统架构规约 (System Specification)

> 定义系统组件、模块边界、技术选型、部署架构
>
> **引用文档**：
> - 认知模型：`../../cog/cog.md`
> - 现实约束：`../../real/real.md`
> - 流水线规格：`../pm/pipeline.spec.md`

---

## 1. 系统概览

### 1.1 架构风格

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户层 (User Layer)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │   CLI       │  │   Web UI    │  │  HTTP API   │  │  WebSocket    │  │
│  │ (cli.py)    │  │ (dashboard) │  │  (FastAPI)  │  │  (realtime)   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────┬───────┘  │
└─────────┼────────────────┼────────────────┼─────────────────┼──────────┘
          │                │                │                 │
          └────────────────┴────────────────┴─────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                          API 服务层 (API Layer)                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                            │  │
│  │  • /api/health - 健康检查                                         │  │
│  │  • /api/statistics - 统计数据                                     │  │
│  │  • /api/patterns - 模式分析                                       │  │
│  │  • /api/learning-path - 学习路径                                  │  │
│  │  • /ws/{task_id} - 实时进度推送                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        编排层 (Orchestration Layer)                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  WorkflowManager                                  │   │
│  │  • 五阶段流水线编排                                                │   │
│  │  • 状态管理与持久化                                                │   │
│  │  • 错误恢复与重试                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   调研模块      │   │   策划模块      │   │   制作模块      │
│   (research/)   │   │   (planning/)   │   │  (production/)  │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ DataCollector   │   │ SpecGenerator   │   │ VideoProducer   │
│ PatternAnalyzer │   │ ScriptCreator   │   │ SubtitleMaker   │
│ CompetitorScan  │   │ SEOOptimizer    │   │ ThumbnailMaker  │
└─────────────────┘   └─────────────────┘   └─────────────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   发布模块      │   │   复盘模块      │   │   共享模块      │
│  (publishing/)  │   │  (analytics/)   │   │   (shared/)     │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ UploadManager   │   │ MetricsCollect  │   │ Config          │
│ MetadataFiller  │   │ ReportGenerator │   │ Logger          │
│ ScheduleManager │   │ Optimizer       │   │ Database        │
└─────────────────┘   └─────────────────┘   └─────────────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        基础设施层 (Infrastructure Layer)                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│  │  SQLite   │  │  yt-dlp   │  │  FFmpeg   │  │ Playwright │           │
│  │ (storage) │  │ (download)│  │  (video)  │  │   (RPA)    │           │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 设计原则

| 原则 | 描述 | 实现方式 |
|------|------|----------|
| 单一职责 | 每个模块只负责一个阶段 | 模块按 pipeline stage 划分 |
| 依赖倒置 | 高层不依赖低层实现 | 通过接口/协议定义依赖 |
| 开闭原则 | 对扩展开放，对修改关闭 | 插件式 Skill/Agent 架构 |
| 综合模式 | AI 理解 + RPA 执行 + 验收检查 | 见 real.md 技术上下文 |

---

## 2. 模块规约

### 2.1 数据层处理模块 (src/dataflow/)

```yaml
module:
  name: dataflow
  path: src/dataflow/
  responsibility: 数据分层处理与层间转换

components:
  - name: RawIngester
    file: raw_ingester.py
    class: RawIngester
    description: Layer 0 原始数据采集与存储
    methods:
      - name: ingest
        input: [source: str, data: List[Dict]]
        output: str  # batch_id
        description: 将原始数据写入 JSONL 文件（不可变）
      - name: get_batch
        input: [batch_id: str]
        output: List[Dict]
        description: 读取原始批次数据

  - name: DataCleaner
    file: data_cleaner.py
    class: DataCleaner
    description: Layer 1 数据清洗与标准化
    methods:
      - name: clean_batch
        input: [batch_id: str]
        output: int  # 清洗后的记录数
        description: 去重、字段标准化、语言检测
      - name: rebuild_all
        input: []
        output: int
        description: 从 Layer 0 重建整个 Layer 1

  - name: DimensionTagger
    file: dimension_tagger.py
    class: DimensionTagger
    description: Layer 2 多维标签标注
    methods:
      - name: tag_videos
        input: [video_ids: List[str]]
        output: Dict[str, List[str]]  # {video_id: [tags]}
        description: 为视频添加多维标签（话题、受众、形式）
      - name: retag_all
        input: [dimension: str]
        output: int
        description: 重新标注某个维度（模型更新时）

  - name: AggregateBuilder
    file: aggregate_builder.py
    class: AggregateBuilder
    description: Layer 3 聚合数据构建
    methods:
      - name: build_baseline
        input: [dimensions: Dict]
        output: BaselineStats
        description: 构建指定维度组合的基线
      - name: build_topic_network
        input: [min_cooccurrence: int]
        output: str  # network file path
        description: 构建话题共现网络
      - name: update_meta_baseline
        input: []
        output: None
        description: 更新元基线（跨领域）

  - name: CoverageChecker
    file: coverage_checker.py
    class: CoverageChecker
    description: 覆盖度评估与增量采集决策
    methods:
      - name: check_coverage
        input: [goal: str]
        output: CoverageReport
        description: 评估某个目标的数据覆盖度
      - name: identify_gaps
        input: [goal: str, threshold: float]
        output: List[CollectionTask]
        description: 识别缺口，生成采集任务

dependencies:
  external:
    - jieba           # 中文分词
  internal:
    - shared.database
    - shared.config

storage_paths:
  layer0: data/raw/videos/*.jsonl
  layer1: data/warehouse/youtube.db#videos_cleaned
  layer2: data/warehouse/youtube.db#video_tags
  layer3: data/cubes/
  layer4: data/insights/
```

### 2.2 调研模块 (src/research/)

```yaml
module:
  name: research
  path: src/research/
  responsibility: 数据采集与竞品分析

components:
  - name: DataCollector
    file: data_collector.py
    class: DataCollector
    methods:
      - name: collect_videos
        input: [keyword: str, max_videos: int]
        output: List[Dict]
        description: 根据关键词采集视频元数据
      - name: filter_quality_videos
        input: [videos: List, min_views: int]
        output: List[Dict]
        description: 按质量指标筛选视频
      - name: ensure_coverage
        input: [goal: str, threshold: float]
        output: CoverageResult
        description: 确保目标覆盖度，自动补充缺口

  - name: PatternAnalyzer
    file: pattern_analyzer.py
    class: PatternAnalyzer
    methods:
      - name: analyze_videos
        input: [videos: List, max_cases: int]
        output: Dict[str, Any]
        description: 分析视频模式，输出典型案例

  - name: YtDlpClient
    file: yt_dlp_client.py
    class: YtDlpClient
    description: yt-dlp 封装客户端，遵守版权合规约束
    methods:
      - name: search_videos
        input: [keyword: str, max_results: int, sort_by: str, time_range: str]
        output: List[Dict]
        description: 搜索视频，支持时间过滤和播放量排序
      - name: get_video_info
        input: [video_id: str]
        output: Dict
        description: 获取单个视频详细信息
    constants:
      - TIME_FILTER_PARAMS: 时间过滤参数 (hour/today/week/month/year)
      - SORT_PARAMS: 排序参数 (relevance/date/view_count/rating)
      - TIME_AND_VIEW_SORT_PARAMS: 组合参数 (时间+播放量排序)

  - name: NetworkCentralityAnalyzer
    file: network_centrality.py
    class: NetworkCentralityAnalyzer
    description: 网络中心性分析，发现套利机会
    methods:
      - name: calculate_topic_centrality
        output: Dict
        description: 计算话题中心性
      - name: calculate_channel_centrality
        output: Dict
        description: 计算频道中心性
      - name: get_arbitrage_opportunities
        input: [top_n: int]
        output: List[Dict]
        description: 获取套利机会榜单
    algorithms:
      - 程度中心性: 节点邻居数 / (总节点数 - 1)
      - 中介中心性: BFS 采样算法近似
      - 有趣度: 中介中心性 / max(程度中心性, 0.01)

dependencies:
  external:
    - yt-dlp          # 视频元数据获取
    - requests        # HTTP 请求
  internal:
    - shared.logger
    - shared.config
    - dataflow.RawIngester      # 写入原始层
    - dataflow.CoverageChecker  # 覆盖度检查

output_artifacts:
  - data/raw/videos/{batch_id}.jsonl    # 原始数据
  - data/reports/research_{keyword}_{date}.md
  - data/reports/videos_{keyword}_{date}.csv
```

### 2.3 分析模块 (src/analysis/)

```yaml
module:
  name: analysis
  path: src/analysis/
  responsibility: 套利分析与机会发现

components:
  - name: ArbitrageAnalyzer
    file: arbitrage_analyzer.py
    class: ArbitrageAnalyzer
    description: 套利分析器 - 发现被低估的创作机会
    methods:
      - name: analyze_all
        input: [min_views: int]
        output: ArbitrageResult
        description: 执行完整套利分析
      - name: analyze_topic_arbitrage
        input: []
        output: TopicArbitrageResult
        description: |
          话题套利分析
          有趣度计算公式: 信息有趣度 = 信息的价值程度 / 信息的传播程度
          利用中心性近似求解: 某个节点的有趣度 = 中介中心性 / 程度中心性
          输出: 桥梁话题列表
      - name: analyze_channel_arbitrage
        input: []
        output: ChannelArbitrageResult
        description: |
          频道套利分析
          发现小频道爆款机会
      - name: analyze_duration_arbitrage
        input: []
        output: DurationArbitrageResult
        description: |
          时长套利分析
          核心公式: 有趣度 = 需求(播放量) / 供给(视频数)
      - name: analyze_timing_arbitrage
        input: []
        output: TimingArbitrageResult
        description: |
          趋势套利分析
          发现上升/下降话题
      - name: profile_creator
        input: []
        output: CreatorProfile
        description: 博主画像定位，匹配适合的套利策略

  - name: VideoAnalyzer
    file: video_analyzer.py
    class: VideoAnalyzer
    methods:
      - name: analyze_video
        input: [video_id: str]
        output: VideoAnalysisResult
        description: 分析单个视频

  - name: MarketAnalyzer
    file: market_analyzer.py
    class: MarketAnalyzer
    methods:
      - name: analyze_market
        input: [theme: str]
        output: MarketReport
        description: 市场规模和竞争分析

dependencies:
  external:
    - networkx        # 关键词网络分析
    - numpy           # 数值计算
  internal:
    - shared.database
    - research.data_collector

output_artifacts:
  - data/reports/arbitrage_{date}.json
  - data/reports/creator_profile_{date}.json

strategy_matrix:
  # 策略与博主类型匹配
  beginner:
    suitable: [duration, channel, follow_up]
    unsuitable: [cross_language, topic]
  mid_tier:
    suitable: [topic, timing]
    unsuitable: [channel]
  top_tier:
    suitable: [cross_language, timing, topic]
    unsuitable: [follow_up]
```

### 2.4 模式分析模块 (src/pattern/)

```yaml
module:
  name: pattern
  path: src/pattern/
  responsibility: 多维度模式分析与学习路径生成

components:
  - name: MultiDimensionPatternAnalyzer
    file: pattern_analyzer.py
    class: MultiDimensionPatternAnalyzer
    description: |
      多维度模式分析器
      数据基础: 中文 N=2,340 条 + 多语言 N=172 条
      已发现模式: 42 个
    methods:
      - name: analyze_all_dimensions
        input: []
        output: Dict[str, DimensionAnalysisResult]
        description: |
          执行全维度分析
          有趣度计算公式: 信息有趣度 = 信息的价值程度 / 信息的传播程度
          利用中心性近似求解有趣度: 某个节点的有趣度 = 中介中心性 / 程度中心性
      - name: analyze_variable_distribution
        input: []
        output: VariableDistributionResult
        description: 变量分布分析 - 10个变量的分布特征
      - name: analyze_temporal_dimension
        input: []
        output: TemporalAnalysisResult
        description: 时间维度分析 - 发布时间与表现的关系
      - name: analyze_spatial_dimension
        input: []
        output: SpatialAnalysisResult
        description: 空间维度分析 - 跨语言/地区市场分析
      - name: analyze_channel_dimension
        input: []
        output: ChannelAnalysisResult
        description: 频道维度分析 - 频道特征与表现的关系
      - name: analyze_user_dimension
        input: []
        output: UserAnalysisResult
        description: 用户维度分析 - 受众特征与互动模式

  - name: PatternDetailService
    file: pattern_detail.py
    class: PatternDetailService
    description: 模式详情服务
    methods:
      - name: get_pattern_detail
        input: [pattern_id: str]
        output: PatternDetail
        description: 获取单个模式详情 (P001-P042)
      - name: list_patterns
        input: [dimension: str, limit: int]
        output: List[PatternSummary]
        description: 按维度列出模式
      - name: compare_patterns
        input: [pattern_ids: List[str]]
        output: PatternComparison
        description: 比较多个模式

  - name: LearningPathGenerator
    file: learning_path.py
    class: LearningPathGenerator
    description: 学习路径生成器
    methods:
      - name: generate_learning_path
        input: [tier: str, goal: str]
        output: LearningPath
        description: 根据博主层级和目标生成学习路径
      - name: get_recommended_patterns
        input: [channel_info: Dict]
        output: List[PatternRecommendation]
        description: 推荐适合的模式

  - name: ActionGuideGenerator
    file: action_guide.py
    class: ActionGuideGenerator
    description: 行动指南生成器
    methods:
      - name: generate_action_guide
        input: [pattern_id: str, context: Dict]
        output: ActionGuide
        description: 为特定模式生成行动指南
      - name: batch_generate
        input: [pattern_ids: List[str]]
        output: List[ActionGuide]
        description: 批量生成行动指南

dependencies:
  external:
    - networkx        # 网络分析
    - numpy           # 数值计算
    - pandas          # 数据处理
  internal:
    - shared.database
    - analysis.arbitrage_analyzer
    - dataflow.aggregate_builder

output_artifacts:
  - data/insights/patterns/{pattern_id}.json
  - data/insights/learning_paths/{tier}_{goal}.json
  - data/insights/reports/pattern_report_{date}.json
  - web/pattern-detail.html
  - web/learning-path.html
```

### 2.5 API 服务模块 (src/api/)

```yaml
module:
  name: api
  path: src/api/
  responsibility: HTTP API 服务与 WebSocket 实时通信

components:
  - name: APIServer
    file: server.py
    class: APIServer
    description: FastAPI 应用服务器
    methods:
      - name: start
        input: [host: str, port: int]
        output: None
        description: 启动 API 服务器
      - name: stop
        input: []
        output: None
        description: 停止服务器

  - name: PatternRouter
    file: routers/pattern.py
    description: 模式分析 API 路由
    endpoints:
      - path: /api/patterns
        method: GET
        description: 获取模式列表
      - path: /api/patterns/{pattern_id}
        method: GET
        description: 获取模式详情
      - path: /api/learning-path
        method: GET
        description: 获取学习路径

  - name: StatisticsRouter
    file: routers/statistics.py
    description: 统计数据 API 路由
    endpoints:
      - path: /api/statistics
        method: GET
        description: 获取统计概览
      - path: /api/health
        method: GET
        description: 健康检查

  - name: TaskRouter
    file: routers/task.py
    description: 任务管理 API 路由
    endpoints:
      - path: /api/tasks/analysis
        method: POST
        description: 创建分析任务
      - path: /api/task/{task_id}/status
        method: GET
        description: 获取任务状态

  - name: WebSocketManager
    file: websocket.py
    class: WebSocketManager
    description: WebSocket 连接管理
    methods:
      - name: connect
        input: [websocket: WebSocket, task_id: str]
        output: None
        description: 建立 WebSocket 连接
      - name: broadcast_progress
        input: [task_id: str, progress: float, message: str]
        output: None
        description: 广播任务进度

dependencies:
  external:
    - fastapi         # Web 框架
    - uvicorn         # ASGI 服务器
    - websockets      # WebSocket 支持
  internal:
    - shared.database
    - pattern.MultiDimensionPatternAnalyzer
    - analysis.arbitrage_analyzer

output_artifacts:
  - api_server.py     # 服务入口
  - web/creator-dashboard.html  # 创作者仪表盘
```

### 2.6 策划模块 (src/planning/)

```yaml
module:
  name: planning
  path: src/planning/
  responsibility: 规约生成与脚本创作

components:
  - name: SpecGenerator
    file: spec_generator.py
    class: SpecGenerator
    methods:
      - name: generate_spec
        input: [research_report: ResearchReport, style: str]
        output: Spec
        description: 根据调研报告生成视频规约

  - name: ScriptCreator
    file: script_creator.py
    class: ScriptCreator
    methods:
      - name: create_script
        input: [spec: Spec, template: Template]
        output: Script
        description: 根据规约和模板创作脚本

  - name: SEOOptimizer
    file: seo_optimizer.py
    class: SEOOptimizer
    methods:
      - name: optimize
        input: [script: Script]
        output: SEOReport
        description: 优化标题/描述/标签

dependencies:
  external:
    - anthropic       # Claude API (可选)
  internal:
    - shared.config
    - research.PatternAnalyzer

output_artifacts:
  - specs/video_spec_{id}.md
  - scripts/video_script_{id}.md
  - scripts/seo_report_{id}.json
```

### 2.7 制作模块 (src/production/)

```yaml
module:
  name: production
  path: src/production/
  responsibility: 视频合成与字幕处理

components:
  - name: VideoProducer
    file: video_producer.py
    class: VideoProducer
    methods:
      - name: produce
        input: [script: Script, assets: List[Asset]]
        output: Video
        description: 合成最终视频

  - name: SubtitleMaker
    file: subtitle_maker.py
    class: SubtitleMaker
    methods:
      - name: generate
        input: [audio: Path, language: str]
        output: Subtitle
        description: 生成字幕文件 (Whisper)
      - name: sync
        input: [subtitle: Subtitle, video: Video]
        output: Subtitle
        description: 同步字幕时间轴

  - name: ThumbnailMaker
    file: thumbnail_maker.py
    class: ThumbnailMaker
    methods:
      - name: create
        input: [title: str, style: dict]
        output: Thumbnail
        description: 生成视频封面

dependencies:
  external:
    - ffmpeg          # 视频处理
    - whisper         # 语音转文字
    - imagemagick     # 图像处理
  internal:
    - shared.config

output_artifacts:
  - data/videos/{id}.mp4
  - data/transcripts/{id}.vtt
  - data/thumbnails/{id}.jpg
```

### 2.8 发布模块 (src/publishing/)

```yaml
module:
  name: publishing
  path: src/publishing/
  responsibility: 视频上传与元数据填写

components:
  - name: UploadManager
    file: upload_manager.py
    class: UploadManager
    methods:
      - name: upload
        input: [video: Video, config: UploadConfig]
        output: UploadResult
        description: 上传视频到 YouTube
        execution_mode: hybrid  # AI理解 + RPA执行

  - name: MetadataFiller
    file: metadata_filler.py
    class: MetadataFiller
    methods:
      - name: fill
        input: [youtube_id: str, metadata: dict]
        output: bool
        description: 填写视频元数据

  - name: ScheduleManager
    file: schedule_manager.py
    class: ScheduleManager
    methods:
      - name: schedule
        input: [youtube_id: str, publish_time: datetime]
        output: bool
        description: 设置定时发布

dependencies:
  external:
    - playwright      # 浏览器自动化
    - pyautogui       # RPA 操作
  internal:
    - shared.config

output_artifacts:
  - logs/upload_report_{date}.json
  - config/upload_config_{id}.json
```

### 2.9 复盘模块 (src/analytics/)

```yaml
module:
  name: analytics
  path: src/analytics/
  responsibility: 数据采集与效果分析

components:
  - name: MetricsCollector
    file: metrics_collector.py
    class: MetricsCollector
    methods:
      - name: collect
        input: [youtube_id: str, period: str]
        output: Metrics
        description: 采集视频表现数据

  - name: ReportGenerator
    file: report_generator.py
    class: ReportGenerator
    methods:
      - name: generate
        input: [metrics: Metrics, baseline: Metrics]
        output: AnalyticsReport
        description: 生成复盘报告

  - name: Optimizer
    file: optimizer.py
    class: Optimizer
    methods:
      - name: suggest
        input: [report: AnalyticsReport]
        output: OptimizationSuggestions
        description: 生成优化建议

dependencies:
  external:
    - playwright      # 抓取 YouTube Studio
  internal:
    - shared.database

output_artifacts:
  - data/reports/analytics_{id}_{period}.md
  - data/reports/optimization_{id}.md
```

### 2.10 报告模块 (src/report/)

```yaml
module:
  name: report
  path: src/report/
  responsibility: 可视化报告生成（6个独立HTML页面）

components:
  - name: ReportGenerator
    file: report_generator.py
    class: ReportGenerator
    description: 综合报告生成器，输出6个独立HTML页面
    methods:
      - name: generate_all
        input: [output_dir: str]
        output: List[str]
        description: 生成全部6个HTML页面
      - name: generate_overview
        input: [output_path: str]
        output: str
        description: 生成概览页面 (index.html)
      - name: generate_arbitrage
        input: [output_path: str]
        output: str
        description: 生成套利分析页面 (arbitrage.html)
      - name: generate_content_map
        input: [output_path: str]
        output: str
        description: 生成内容四象限页面 (content-map.html)
      - name: generate_creators
        input: [output_path: str]
        output: str
        description: 生成创作者分析页面 (creators.html)
      - name: generate_titles
        input: [output_path: str]
        output: str
        description: 生成标题公式页面 (titles.html)
      - name: generate_actions
        input: [output_path: str]
        output: str
        description: 生成行动建议页面 (actions.html)

  - name: PageRenderer
    file: page_renderer.py
    class: PageRenderer
    description: HTML页面渲染器
    methods:
      - name: render
        input: [template: str, data: Dict]
        output: str
        description: 渲染HTML模板
      - name: _generate_nav
        input: [active_page: str]
        output: str
        description: 生成顶部导航（6页面链接）

dependencies:
  external:
    - sqlite3         # 数据库访问
    - json            # JSON 处理
  internal:
    - research.data_collector
    - analysis.video_analyzer
    - analysis.market_analyzer
    - analysis.arbitrage_analyzer

output_artifacts:
  pages:
    - public/index.html        # 概览页面
    - public/arbitrage.html    # 套利分析页面
    - public/content-map.html  # 内容四象限页面
    - public/creators.html     # 创作者分析页面
    - public/titles.html       # 标题公式页面
    - public/actions.html      # 行动建议页面

  deployment:
    platform: Vercel
    url: https://youtube-analysis-report.vercel.app
```

### 2.11 共享模块 (src/shared/)

```yaml
module:
  name: shared
  path: src/shared/
  responsibility: 公共组件与基础设施

components:
  - name: Config
    file: config.py
    class: Config
    description: 配置管理 (YAML + 环境变量)

  - name: Logger
    file: logger.py
    class: Logger
    description: 统一日志 (结构化输出)

  - name: Database
    file: database.py
    class: Database
    description: SQLite 持久化层

  - name: Validators
    file: validators.py
    functions:
      - validate_video_format
      - validate_thumbnail_size
      - validate_subtitle_sync

  - name: FileUtils
    file: file_utils.py
    functions:
      - ensure_dir
      - safe_filename
      - cleanup_old_files
```

---

## 3. 技术选型

### 3.1 核心依赖

| 类别 | 工具 | 版本 | 用途 |
|------|------|------|------|
| 运行时 | Python | >= 3.10 | 主语言 |
| 包管理 | uv | latest | 依赖管理 |
| 数据库 | SQLite | 3.x | 本地持久化 |
| Web 框架 | FastAPI | >= 0.100 | HTTP API 服务 |
| ASGI 服务器 | uvicorn | latest | API 服务运行 |
| 视频 | FFmpeg | >= 6.0 | 音视频处理 |
| 下载 | yt-dlp | >= 2025.1.0 | YouTube 数据获取 |
| 转录 | Whisper | latest | 语音转文字 |
| 图像 | ImageMagick | >= 7.0 | 封面制作 |
| 自动化 | Playwright | latest | 浏览器控制 |
| RPA | PyAutoGUI | latest | 模拟操作 |
| 网络分析 | networkx | >= 3.0 | 关键词网络、中心性计算 |
| 数据处理 | pandas | >= 2.0 | 数据分析 |

### 3.2 可选依赖

| 类别 | 工具 | 用途 | 启用条件 |
|------|------|------|----------|
| AI | anthropic | Claude API | 需要 AI 生成脚本 |
| TTS | elevenlabs | 英文配音 | 需要配音功能 |
| TTS | minimax | 中文配音 | 需要中文配音 |

### 3.3 MCP 服务

| MCP | 用途 | 阶段 |
|-----|------|------|
| @anthropic/claude-mcp | AI 能力 | 策划 |
| @playwright/mcp | 浏览器自动化 | 发布、复盘 |
| mcp-chrome | 保持登录状态 | 发布（备选） |

---

## 4. 目录结构

```
youtube-minimal-video-story/
├── .42cog/                     # 42cog 规约系统
│   ├── meta/meta.md            # 项目元信息
│   ├── cog/cog.md              # 认知模型
│   ├── real/real.md            # 现实约束
│   └── spec/
│       ├── pm/                 # 产品规约
│       │   ├── pipeline.spec.md
│       │   ├── userstory.spec.md
│       │   └── pr.spec.md
│       └── dev/                # 开发规约
│           ├── sys.spec.md     # 本文档
│           ├── data.spec.md
│           └── api.spec.md
│
├── src/                        # 源代码
│   ├── __init__.py
│   ├── main.py                 # 入口
│   ├── dataflow/               # 数据层处理模块
│   │   ├── __init__.py
│   │   ├── raw_ingester.py     # Layer 0 原始数据
│   │   ├── data_cleaner.py     # Layer 1 清洗
│   │   ├── dimension_tagger.py # Layer 2 标签
│   │   ├── aggregate_builder.py # Layer 3 聚合
│   │   └── coverage_checker.py # 覆盖度评估
│   ├── research/               # 调研模块
│   │   ├── __init__.py
│   │   ├── data_collector.py
│   │   └── pattern_analyzer.py
│   ├── analysis/               # 分析模块
│   │   ├── __init__.py
│   │   ├── arbitrage_analyzer.py   # 套利分析器
│   │   ├── video_analyzer.py
│   │   └── market_analyzer.py
│   ├── pattern/                # 模式分析模块
│   │   ├── __init__.py
│   │   ├── pattern_analyzer.py     # 多维度模式分析
│   │   ├── pattern_detail.py       # 模式详情服务
│   │   ├── learning_path.py        # 学习路径生成
│   │   └── action_guide.py         # 行动指南生成
│   ├── api/                    # API 服务模块
│   │   ├── __init__.py
│   │   ├── server.py               # FastAPI 应用
│   │   ├── websocket.py            # WebSocket 管理
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── pattern.py          # 模式分析路由
│   │       ├── statistics.py       # 统计数据路由
│   │       └── task.py             # 任务管理路由
│   ├── planning/               # 策划模块 (待实现)
│   ├── production/             # 制作模块 (待实现)
│   ├── publishing/             # 发布模块 (待实现)
│   ├── analytics/              # 复盘模块 (待实现)
│   └── shared/                 # 共享模块
│       ├── __init__.py
│       ├── config.py
│       ├── logger.py
│       └── database.py
│
├── prompts/                    # 阶段提示词
│   ├── PROMPT_02_调研阶段.md
│   ├── PROMPT_03_策划阶段.md
│   ├── PROMPT_04_制作阶段.md
│   ├── PROMPT_05_发布阶段.md
│   └── PROMPT_06_复盘阶段.md
│
├── data/                       # 数据目录 (gitignore)
│   ├── raw/                    # Layer 0: 原始数据
│   │   └── videos/*.jsonl
│   ├── warehouse/              # Layer 1-2: 清洗 + 标签
│   │   └── youtube.db
│   ├── cubes/                  # Layer 3: 聚合数据
│   │   ├── baselines/
│   │   └── networks/
│   ├── insights/               # Layer 4: 分析结果
│   ├── assets/                 # 素材
│   ├── videos/                 # 视频文件
│   ├── transcripts/            # 字幕文件
│   ├── thumbnails/             # 封面图
│   └── reports/                # 报告
│
├── config/                     # 配置文件
│   ├── settings.yaml           # 主配置
│   ├── secrets.yaml            # 敏感信息 (gitignore)
│   └── upload_config_*.json    # 上传配置
│
├── logs/                       # 日志 (gitignore)
│
├── tests/                      # 测试
│   ├── unit/
│   └── integration/
│
├── scripts/                    # 辅助脚本
│
├── web/                        # Web 前端页面
│   ├── index.html              # 概览页面
│   ├── demo.html               # 演示页面
│   ├── creator-dashboard.html  # 创作者仪表盘
│   ├── creator-action.html     # 创作者行动中心（洞察系统外链目标）
│   ├── learning-path.html      # 学习路径页面
│   ├── pattern-detail.html     # 模式详情页面
│   ├── insight-system.html     # 洞察系统页面（3主Tab+1外链+1隐藏Tab）
│   ├── js/                     # JavaScript 模块
│   │   ├── insight.js          # 洞察系统入口
│   │   ├── insight-core.js     # 核心框架、Tab切换
│   │   ├── insight-charts.js   # Chart.js 图表封装
│   │   ├── insight-report.js   # 信息报告 Tab
│   │   ├── insight-user.js     # 用户洞察 Tab（隐藏）
│   │   ├── insight-global.js   # 全局认识 Tab
│   │   └── insight-content.js  # 内容分析相关
│   └── open_demo.sh            # 演示启动脚本
│
├── api_server.py               # API 服务入口
├── cli.py                      # CLI 入口
├── pyproject.toml              # 项目配置
└── requirements.txt            # 依赖清单
```

---

## 5. 部署架构

### 5.1 本地开发环境

```yaml
environment: local-dev

requirements:
  os: macOS / Linux / Windows (WSL)
  python: 3.10+
  storage: >= 50GB free space
  memory: >= 8GB RAM

setup:
  1. git clone <repo>
  2. uv venv && source .venv/bin/activate
  3. uv pip install -r requirements.txt
  4. cp config/secrets.yaml.example config/secrets.yaml
  5. # 配置 API keys

verification:
  - python cli.py --help
  - ffmpeg -version
  - yt-dlp --version
```

### 5.2 生产环境

```yaml
environment: production

deployment_options:
  - name: 单机部署
    description: 适合个人创作者
    requirements:
      - 本地机器或 VPS
      - Chrome 已登录 YouTube
    notes:
      - 使用 systemd 管理进程
      - 定时任务触发复盘

  - name: 容器部署
    description: 适合团队使用
    requirements:
      - Docker / Podman
      - 持久化卷挂载 data/
    notes:
      - 需要 VNC 或远程桌面支持发布
      - 或使用 YouTube Data API
```

---

## 6. 安全规约

### 6.1 敏感信息管理

```yaml
secrets:
  storage: config/secrets.yaml
  gitignore: true

  required:
    - youtube_cookies      # 发布模块需要

  optional:
    - anthropic_api_key    # AI 生成脚本
    - elevenlabs_api_key   # TTS 配音
    - minimax_api_key      # 中文 TTS

access_control:
  - 文件权限 600 (仅 owner 可读写)
  - 不记录到日志
  - 不包含在错误报告中
```

### 6.2 约束检查

```yaml
constraints:
  - ref: real.md#YouTube 社区准则红线
    enforcement: pre-publish content review

  - ref: real.md#API/自动化限制
    enforcement: rate limiter + quota counter

  - ref: real.md#版权合规
    enforcement: asset source tracking
```

---

## 7. 扩展点

### 7.1 插件接口

```python
# 新增 Skill 的接口
class SkillBase(ABC):
    @abstractmethod
    def execute(self, input: dict) -> dict:
        """执行技能"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass

# 注册方式
# .claude/skills/<skill-name>/skill.md + skill.py
```

### 7.2 自定义阶段

```yaml
# 在 pipeline.spec.md 中扩展
custom_stages:
  - name: localization
    after: production
    before: publishing
    description: 多语言本地化
    input: [Video, Subtitle]
    output: [Video[], Subtitle[]]
```

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-18 | 初始版本 |
| 1.1 | 2026-01-19 | 新增分析模块 (ArbitrageAnalyzer, VideoAnalyzer, MarketAnalyzer) |
| 1.2 | 2026-01-19 | 新增数据层处理模块 (dataflow/)：RawIngester, DataCleaner, DimensionTagger, AggregateBuilder, CoverageChecker |
| 1.3 | 2026-01-19 | 更新报告模块：输出改为6个独立HTML页面（概览/套利分析/内容四象限/创作者分析/标题公式/行动建议）|
| 1.4 | 2026-01-24 | 新增模式分析模块 (pattern/)：MultiDimensionPatternAnalyzer, PatternDetailService, LearningPathGenerator, ActionGuideGenerator |
| 1.5 | 2026-01-24 | 新增 API 服务模块 (api/)：FastAPI 应用、WebSocket 实时通信、REST 端点 |
| 1.6 | 2026-01-24 | 更新系统架构图：添加 API 服务层；更新技术选型：添加 FastAPI、uvicorn、networkx、pandas |
| 1.7 | 2026-01-24 | 更新目录结构：添加 pattern/、api/、web/ 目录和新页面文件 |
| 1.8 | 2026-02-01 | 新增调研模块组件：YtDlpClient（yt-dlp封装）、NetworkCentralityAnalyzer（网络中心性分析） |
| 1.9 | 2026-02-01 | 更正洞察系统页面结构文档：3个主Tab + 1个外链 + 1个隐藏Tab；添加7模块JS架构说明 |

---

*引用本规格时使用：`.42cog/spec/dev/sys.spec.md`*
