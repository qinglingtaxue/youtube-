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
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │   CLI       │  │   Web UI    │  │   API       │                      │
│  │ (cli.py)    │  │ (optional)  │  │ (optional)  │                      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                      │
└─────────┼────────────────┼────────────────┼─────────────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
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
          核心公式: 有趣度 = 中介中心性 / 程度中心性
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

### 2.4 策划模块 (src/planning/)

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

### 2.5 制作模块 (src/production/)

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

### 2.6 发布模块 (src/publishing/)

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

### 2.7 复盘模块 (src/analytics/)

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

### 2.8 报告模块 (src/report/)

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

### 2.9 共享模块 (src/shared/)

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
| 视频 | FFmpeg | >= 6.0 | 音视频处理 |
| 下载 | yt-dlp | >= 2025.1.0 | YouTube 数据获取 |
| 转录 | Whisper | latest | 语音转文字 |
| 图像 | ImageMagick | >= 7.0 | 封面制作 |
| 自动化 | Playwright | latest | 浏览器控制 |
| RPA | PyAutoGUI | latest | 模拟操作 |

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

---

*引用本规格时使用：`.42cog/spec/dev/sys.spec.md`*
