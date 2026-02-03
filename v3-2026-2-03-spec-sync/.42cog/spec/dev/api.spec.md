# 接口规约 (API Specification)

> 定义模块间接口、CLI 接口、外部服务接口
>
> **引用文档**：
> - 系统架构：`sys.spec.md`
> - 数据模型：`data.spec.md`
> - 流水线规格：`../pm/pipeline.spec.md`

---

## 1. 接口分类

| 类型 | 描述 | 消费者 |
|------|------|--------|
| CLI | 命令行接口 | 用户 |
| Internal | 模块间接口 | 内部模块 |
| External | 外部服务接口 | YouTube, TTS 服务等 |
| MCP | Model Context Protocol | Claude Code |

---

## 2. CLI 接口

### 2.1 主命令

```yaml
command: youtube-pipeline
alias: ytp
description: YouTube 内容创作流水线 CLI

usage: |
  ytp <command> [options]
  ytp --help
  ytp --version

global_options:
  - name: --config
    short: -c
    type: string
    default: config/settings.yaml
    description: 配置文件路径

  - name: --verbose
    short: -v
    type: boolean
    default: false
    description: 详细输出

  - name: --dry-run
    type: boolean
    default: false
    description: 模拟执行，不实际操作
```

### 2.2 调研命令

```yaml
command: ytp research
description: 执行调研阶段

subcommands:
  - name: search
    description: 搜索视频
    usage: ytp research search <keyword> [options]
    arguments:
      - name: keyword
        required: true
        description: 搜索关键词
    options:
      - name: --max-results
        short: -n
        type: integer
        default: 50
        description: 最大结果数
      - name: --region
        type: string
        default: US
        description: 目标地区 (ISO 3166-1)
      - name: --time-range
        type: string
        enum: [week, month, quarter]
        default: month
        description: 时间范围
      - name: --output
        short: -o
        type: string
        description: 输出文件路径
    example: |
      ytp research search "AI 教程" --max-results 100 --region CN

  - name: analyze
    description: 分析竞品视频
    usage: ytp research analyze <input_file> [options]
    arguments:
      - name: input_file
        required: true
        description: 视频数据文件 (CSV/JSON)
    options:
      - name: --max-cases
        type: integer
        default: 10
        description: 最大案例数
      - name: --output
        short: -o
        type: string
        description: 输出报告路径
    example: |
      ytp research analyze data/videos.csv --max-cases 20

  - name: report
    description: 生成调研报告 HTML 页面
    usage: ytp research report [options]
    options:
      - name: --theme
        type: string
        default: "老人养生"
        description: 调研主题
      - name: --time-window
        type: string
        enum: [1天内, 15天内, 30天内, 全部]
        default: 全部
        description: 时间范围过滤
      - name: --output
        short: -o
        type: string
        description: 输出文件路径
      - name: --open
        type: boolean
        default: true
        description: 生成后自动在浏览器打开
      - name: --format
        type: string
        enum: [html, json]
        default: html
        description: 输出格式
    example: |
      ytp research report --theme "老人养生" --time-window 30天内
      ytp research report -o reports/research.html --open

  - name: arbitrage
    description: 套利分析 - 发现被低估的创作机会
    usage: ytp research arbitrage [options]
    options:
      - name: --type
        short: -t
        type: string
        enum: [all, topic, channel, duration, timing, cross_language, follow_up]
        default: all
        description: 套利类型
      - name: --min-views
        type: integer
        default: 1000
        description: 最小播放量筛选
      - name: --output
        short: -o
        type: string
        description: 输出文件路径
      - name: --format
        type: string
        enum: [json, markdown, html]
        default: json
        description: 输出格式
      - name: --profile
        type: string
        enum: [beginner, mid_tier, top_tier]
        description: 博主画像筛选
    example: |
      ytp research arbitrage --type topic
      ytp research arbitrage --type duration --profile beginner
      ytp research arbitrage --output reports/arbitrage.json

  - name: profile
    description: 博主画像定位分析
    usage: ytp research profile [options]
    options:
      - name: --output
        short: -o
        type: string
        description: 输出文件路径
    example: |
      ytp research profile -o reports/creator_profile.json
```

### 2.8 报告命令

```yaml
command: ytp report
description: 生成可视化报告

subcommands:
  - name: research
    description: 生成调研报告（视频列表为主）
    usage: ytp report research [options]
    options:
      - name: --theme
        type: string
        default: "老人养生"
        description: 调研主题
      - name: --time-window
        type: string
        enum: [1天内, 15天内, 30天内, 全部]
        default: 全部
        description: 时间范围
      - name: --output
        short: -o
        type: string
        description: 输出路径
      - name: --deploy
        type: boolean
        default: false
        description: 同时复制到 public/ 用于部署
    example: |
      ytp report research --theme "老人养生" --time-window 30天内
      ytp report research --deploy

  - name: comprehensive
    description: 生成综合分析报告（图表为主）
    usage: ytp report comprehensive [options]
    options:
      - name: --output
        short: -o
        type: string
        description: 输出路径
      - name: --deploy
        type: boolean
        default: false
        description: 同时复制到 public/ 用于部署
    example: |
      ytp report comprehensive
      ytp report comprehensive --deploy

  - name: deploy
    description: 部署报告到 Vercel
    usage: ytp report deploy [type]
    arguments:
      - name: type
        required: false
        default: comprehensive
        enum: [research, comprehensive, all]
        description: 要部署的报告类型
    example: |
      ytp report deploy comprehensive
      ytp report deploy all
```

### 2.3 策划命令

```yaml
command: ytp plan
description: 执行策划阶段

subcommands:
  - name: spec
    description: 生成视频规约
    usage: ytp plan spec <research_report> [options]
    arguments:
      - name: research_report
        required: true
        description: 调研报告文件
    options:
      - name: --style
        type: string
        enum: [tutorial, story, review, vlog, explainer]
        default: tutorial
        description: 内容风格
      - name: --duration
        type: integer
        default: 600
        description: 目标时长 (秒)
      - name: --output
        short: -o
        type: string
        description: 输出文件路径
    example: |
      ytp plan spec data/reports/research_AI_20260118.md --style tutorial

  - name: script
    description: 生成脚本
    usage: ytp plan script <spec_file> [options]
    arguments:
      - name: spec_file
        required: true
        description: 视频规约文件
    options:
      - name: --template
        type: string
        description: 模板文件
      - name: --ai
        type: boolean
        default: false
        description: 使用 AI 辅助生成
    example: |
      ytp plan script specs/video_spec_001.md --ai

  - name: seo
    description: SEO 优化
    usage: ytp plan seo <script_file>
    arguments:
      - name: script_file
        required: true
        description: 脚本文件
    output:
      type: SEOReport
      path: scripts/seo_report_{id}.json
```

### 2.4 制作命令

```yaml
command: ytp produce
description: 执行制作阶段

subcommands:
  - name: tts
    description: 生成配音
    usage: ytp produce tts <script_file> [options]
    arguments:
      - name: script_file
        required: true
        description: 脚本文件
    options:
      - name: --provider
        type: string
        enum: [elevenlabs, minimax, local]
        default: local
        description: TTS 服务提供商
      - name: --voice
        type: string
        description: 声音 ID
      - name: --output
        short: -o
        type: string
        description: 输出音频路径
    example: |
      ytp produce tts scripts/video_script_001.md --provider minimax

  - name: subtitle
    description: 生成字幕
    usage: ytp produce subtitle <audio_file> [options]
    arguments:
      - name: audio_file
        required: true
        description: 音频文件
    options:
      - name: --language
        type: string
        default: zh
        description: 语言代码
      - name: --model
        type: string
        enum: [base, small, medium, large]
        default: base
        description: Whisper 模型
      - name: --format
        type: string
        enum: [srt, vtt]
        default: vtt
        description: 字幕格式
    example: |
      ytp produce subtitle data/audio/voiceover.mp3 --language zh

  - name: video
    description: 合成视频
    usage: ytp produce video <config_file>
    arguments:
      - name: config_file
        required: true
        description: 制作配置文件 (JSON)
    options:
      - name: --resolution
        type: string
        enum: [720p, 1080p, 4K]
        default: 1080p
        description: 输出分辨率
      - name: --preview
        type: boolean
        default: false
        description: 生成预览 (低分辨率)
    example: |
      ytp produce video config/produce_config_001.json

  - name: thumbnail
    description: 制作封面
    usage: ytp produce thumbnail <title> [options]
    arguments:
      - name: title
        required: true
        description: 封面标题
    options:
      - name: --background
        type: string
        description: 背景图片路径
      - name: --template
        type: string
        description: 封面模板
      - name: --output
        short: -o
        type: string
        description: 输出路径
```

### 2.5 发布命令

```yaml
command: ytp publish
description: 执行发布阶段

subcommands:
  - name: upload
    description: 上传视频
    usage: ytp publish upload <video_file> [options]
    arguments:
      - name: video_file
        required: true
        description: 视频文件路径
    options:
      - name: --config
        type: string
        description: 上传配置文件 (JSON)
      - name: --title
        type: string
        description: 视频标题
      - name: --description
        type: string
        description: 视频描述
      - name: --tags
        type: string
        description: 标签 (逗号分隔)
      - name: --privacy
        type: string
        enum: [public, unlisted, private]
        default: private
        description: 隐私设置
      - name: --thumbnail
        type: string
        description: 封面文件路径
      - name: --subtitle
        type: string
        description: 字幕文件路径
    example: |
      ytp publish upload data/videos/video_001.mp4 --config config/upload_config_001.json

  - name: schedule
    description: 设置定时发布
    usage: ytp publish schedule <youtube_id> <datetime>
    arguments:
      - name: youtube_id
        required: true
        description: YouTube 视频 ID
      - name: datetime
        required: true
        description: 发布时间 (ISO 8601)
    example: |
      ytp publish schedule abc123xyz "2026-01-20T10:00:00+08:00"

  - name: verify
    description: 验证上传结果
    usage: ytp publish verify <youtube_id>
    arguments:
      - name: youtube_id
        required: true
        description: YouTube 视频 ID
    output:
      type: VerificationReport
      fields: [title, description, thumbnail, subtitle, status]
```

### 2.6 复盘命令

```yaml
command: ytp analyze
description: 执行复盘阶段

subcommands:
  - name: collect
    description: 采集数据
    usage: ytp analyze collect <youtube_id> [options]
    arguments:
      - name: youtube_id
        required: true
        description: YouTube 视频 ID
    options:
      - name: --period
        type: string
        enum: [7d, 30d, lifetime]
        default: 7d
        description: 统计周期
    example: |
      ytp analyze collect abc123xyz --period 30d

  - name: report
    description: 生成报告
    usage: ytp analyze report <youtube_id> [options]
    arguments:
      - name: youtube_id
        required: true
        description: YouTube 视频 ID
    options:
      - name: --compare
        type: string
        description: 对比视频 ID (逗号分隔)
      - name: --format
        type: string
        enum: [md, json, html]
        default: md
        description: 输出格式
    example: |
      ytp analyze report abc123xyz --compare def456,ghi789

  - name: suggest
    description: 生成优化建议
    usage: ytp analyze suggest <youtube_id>
    output:
      type: OptimizationSuggestions
      fields: [cover, title, content, next_topics]
```

### 2.7 工作流命令

```yaml
command: ytp workflow
description: 完整工作流管理

subcommands:
  - name: run
    description: 执行完整流水线
    usage: ytp workflow run <keyword> [options]
    arguments:
      - name: keyword
        required: true
        description: 调研关键词
    options:
      - name: --stages
        type: string
        default: "research,planning,production,publishing"
        description: 执行阶段 (逗号分隔)
      - name: --skip
        type: string
        description: 跳过阶段
      - name: --resume
        type: string
        description: 从指定视频 ID 恢复
    example: |
      ytp workflow run "Python 教程" --stages research,planning

  - name: status
    description: 查看工作流状态
    usage: ytp workflow status [video_id]
    arguments:
      - name: video_id
        required: false
        description: 视频 ID (不指定则显示所有)

  - name: list
    description: 列出视频
    usage: ytp workflow list [options]
    options:
      - name: --status
        type: string
        enum: [draft, scripting, producing, ready, published, scheduled]
        description: 按状态筛选
      - name: --limit
        type: integer
        default: 20
        description: 显示数量
```

### 2.9 模式分析命令

```yaml
command: ytp pattern
description: 模式洞察与学习路径
alias: ytp pt

subcommands:
  - name: analyze
    description: 多维度模式分析
    usage: ytp pattern analyze [options]
    options:
      - name: --dimension
        short: -d
        type: string
        enum: [variable, temporal, spatial, channel, user, all]
        default: all
        description: 分析维度
      - name: --pattern-id
        type: string
        description: 指定模式 ID 进行详细分析
      - name: --output
        short: -o
        type: string
        description: 输出路径
      - name: --format
        type: string
        enum: [json, markdown, html]
        default: json
        description: 输出格式
    example: |
      ytp pattern analyze --dimension variable
      ytp pattern analyze --pattern-id P023 --format markdown

  - name: learning-path
    description: 生成学习路径导航
    usage: ytp pattern learning-path [options]
    options:
      - name: --tier
        type: string
        enum: [beginner, mid_tier, top_tier]
        description: 博主层级
      - name: --goal
        type: string
        description: 学习目标（如 "提升互动率"）
      - name: --output
        short: -o
        type: string
        description: 输出路径
    example: |
      ytp pattern learning-path --tier beginner
      ytp pattern learning-path --goal "提升互动率"

  - name: detail
    description: 获取模式详情
    usage: ytp pattern detail <pattern_id> [options]
    arguments:
      - name: pattern_id
        required: true
        description: 模式 ID（如 P001, P023）
    options:
      - name: --include-examples
        type: boolean
        default: true
        description: 包含示例视频
      - name: --format
        type: string
        enum: [json, markdown]
        default: markdown
        description: 输出格式
    example: |
      ytp pattern detail P023
      ytp pattern detail P001 --format json

  - name: compare
    description: 比较多个模式
    usage: ytp pattern compare <pattern_ids> [options]
    arguments:
      - name: pattern_ids
        required: true
        description: 模式 ID 列表（逗号分隔）
    options:
      - name: --metrics
        type: string
        default: "views,engagement,difficulty"
        description: 比较指标
    example: |
      ytp pattern compare P001,P023,P042

  - name: recommend
    description: 推荐适合的模式
    usage: ytp pattern recommend [options]
    options:
      - name: --channel
        type: string
        description: 频道 ID 或 URL
      - name: --style
        type: string
        enum: [tutorial, story, review, vlog, explainer]
        description: 内容风格偏好
      - name: --top-n
        type: integer
        default: 5
        description: 推荐数量
    example: |
      ytp pattern recommend --style tutorial --top-n 3
```

### 2.10 数据流命令

```yaml
command: ytp dataflow
description: 数据分层处理与层间转换
alias: ytp df

subcommands:
  - name: ingest
    description: 写入原始层 (Layer 0)
    usage: ytp dataflow ingest <source> [options]
    arguments:
      - name: source
        required: true
        description: 数据源 (文件路径或 stdin)
    options:
      - name: --format
        type: string
        enum: [json, jsonl, csv]
        default: jsonl
        description: 输入格式
      - name: --batch-id
        type: string
        description: 批次 ID (默认自动生成)
    example: |
      ytp dataflow ingest data/raw/videos/20260119_batch001.jsonl
      cat videos.json | ytp dataflow ingest - --format json

  - name: clean
    description: 清洗数据 (Layer 0 → Layer 1)
    usage: ytp dataflow clean [options]
    options:
      - name: --since
        type: string
        description: 处理指定日期之后的原始数据 (YYYY-MM-DD)
      - name: --batch-id
        type: string
        description: 只处理指定批次
      - name: --dry-run
        type: boolean
        default: false
        description: 预览模式，不实际写入
    example: |
      ytp dataflow clean --since 2026-01-15

  - name: tag
    description: 多维度标注 (Layer 1 → Layer 2)
    usage: ytp dataflow tag [options]
    options:
      - name: --dimensions
        type: string
        default: "topic,audience,format,duration"
        description: 标注维度 (逗号分隔)
      - name: --limit
        type: integer
        description: 最大处理数量
      - name: --force
        type: boolean
        default: false
        description: 强制重新标注已有记录
    example: |
      ytp dataflow tag --dimensions topic,audience --limit 100

  - name: aggregate
    description: 构建聚合数据 (Layer 2 → Layer 3)
    usage: ytp dataflow aggregate <type> [options]
    arguments:
      - name: type
        required: true
        description: 聚合类型
        enum: [baseline, network, stats]
    options:
      - name: --scope
        type: string
        description: 聚合范围 (如 topic:健康养生)
      - name: --incremental
        type: boolean
        default: true
        description: 增量更新（默认）vs 全量重建
    example: |
      ytp dataflow aggregate baseline --scope topic:老人养生
      ytp dataflow aggregate network --incremental

  - name: coverage
    description: 检查数据覆盖度
    usage: ytp dataflow coverage [options]
    options:
      - name: --goal
        type: string
        description: 目标定义 (如 "topic:健康 AND audience:老年人")
      - name: --threshold
        type: float
        default: 0.8
        description: 覆盖度阈值
      - name: --suggest
        type: boolean
        default: true
        description: 显示补充采集建议
    output: |
      覆盖度报告:
        当前: 65% (650/1000)
        缺口: 350 条
        建议: ytp research search "老人养生" --max-results 400
    example: |
      ytp dataflow coverage --goal "topic:健康" --threshold 0.8

  - name: status
    description: 查看数据层状态
    usage: ytp dataflow status [layer]
    arguments:
      - name: layer
        required: false
        description: 指定层级 (0-4)
    output: |
      数据层状态:
        Layer 0 (Raw):       5,234 条 (2.1 GB)
        Layer 1 (Cleaned):   4,890 条
        Layer 2 (Tagged):    3,200 条 (65%)
        Layer 3 (Aggregated):
          - baselines: 12 个
          - networks: 3 个
        Layer 4 (Insights):
          - reports: 8 份
    example: |
      ytp dataflow status
      ytp dataflow status 2

  - name: rebuild
    description: 重建上层数据
    usage: ytp dataflow rebuild <from_layer> [options]
    arguments:
      - name: from_layer
        required: true
        description: 从哪一层开始重建 (1-4)
    options:
      - name: --confirm
        type: boolean
        default: false
        description: 确认重建（危险操作）
    example: |
      ytp dataflow rebuild 2 --confirm
```

---

## 3. HTTP API 服务

> 基于 FastAPI 的 HTTP 服务层，支持创作者仪表盘和异步任务管理。

### 3.1 服务配置

```yaml
service: YouTube Pipeline API
framework: FastAPI
server: uvicorn
default_port: 8000

static_files:
  mount_path: /
  directory: web/
  html: true

cors:
  allow_origins: ["*"]
  allow_methods: ["*"]
  allow_headers: ["*"]
```

### 3.2 RESTful 端点

```yaml
endpoints:
  # 健康检查
  - name: health_check
    method: GET
    path: /api/health
    description: 健康检查端点
    response:
      status: string  # "ok"
      timestamp: string  # ISO 8601

  # 创作者仪表盘页面
  - name: creator_dashboard
    method: GET
    path: /creator
    description: 创作者仪表盘入口页
    response: HTML (creator-dashboard.html)

  # 统计数据
  - name: get_statistics
    method: GET
    path: /api/statistics
    description: 获取视频统计数据
    query_params:
      - name: time_range
        type: string
        enum: [7d, 30d, 90d, all]
        default: all
      - name: category
        type: string
        description: 按分类筛选
    response:
      total_videos: integer
      total_views: integer
      total_channels: integer
      patterns_discovered: integer
      languages: array[string]
      avg_engagement_rate: float

  # 任务状态
  - name: get_task_status
    method: GET
    path: /api/task/{task_id}/status
    description: 获取异步任务状态
    path_params:
      - name: task_id
        type: string
        required: true
    response:
      task_id: string
      status: string  # pending, running, completed, failed
      progress: float  # 0.0 - 1.0
      message: string
      result: object  # 任务结果（完成时）
      error: string   # 错误信息（失败时）

  # 模式分析
  - name: get_patterns
    method: GET
    path: /api/patterns
    description: 获取已发现的模式列表
    query_params:
      - name: dimension
        type: string
        enum: [variable, temporal, spatial, channel, user]
      - name: limit
        type: integer
        default: 20
      - name: offset
        type: integer
        default: 0
    response:
      total: integer
      patterns: array[PatternSummary]

  - name: get_pattern_detail
    method: GET
    path: /api/patterns/{pattern_id}
    description: 获取模式详情（数据层）
    path_params:
      - name: pattern_id
        type: string
        required: true
    response: PatternAnalysis

  - name: get_pattern_detail_page
    method: GET
    path: /api/patterns/{pattern_id}/detail
    description: 获取模式详情页面（呈现层）
    path_params:
      - name: pattern_id
        type: string
        required: true
    response:
      pattern_id: string
      title: string
      dimension: string
      interestingness: integer
      confidence: float
      insight_card: InsightCard
      sources: array[DataSource]
      sample_videos: array[VideoExample]
      action_checklist: array[ActionItem]
      related_patterns: array[string]

  # 学习路径
  - name: get_learning_path
    method: GET
    path: /api/learning-path
    description: 获取学习路径
    query_params:
      - name: tier
        type: string
        enum: [beginner, mid_tier, top_tier]
      - name: goal
        type: string
    response:
      path_id: string
      blocks: array[LearningBlock]
      estimated_duration: string

  # 趋势追踪
  - name: get_trending_tracker
    method: GET
    path: /api/trending-tracker/{tracker_id}
    description: 获取趋势追踪数据
    path_params:
      - name: tracker_id
        type: string
        required: true
    response:
      tracker_id: string
      keyword: string
      last_update_time: string
      trend_data:
        period: string  # 24h/7d/30d
        snapshots: array[TrendSnapshot]
        total_views_delta: integer
        avg_daily_growth: float
        top_growing_videos: array[VideoExample]
      visualization: DurationDistributionChart
      alert_status: string

  # 创建分析任务
  - name: create_analysis_task
    method: POST
    path: /api/tasks/analysis
    description: 创建新的分析任务
    body:
      type: string  # arbitrage, pattern, trend
      params: object
    response:
      task_id: string
      status: string
```

### 3.3 WebSocket 端点

```yaml
websocket:
  - name: task_progress
    path: /ws/{task_id}
    description: 实时任务进度推送
    path_params:
      - name: task_id
        type: string
    messages:
      client_to_server:
        - type: subscribe
          payload: {}
        - type: unsubscribe
          payload: {}
      server_to_client:
        - type: progress
          payload:
            progress: float
            message: string
            stage: string
        - type: completed
          payload:
            result: object
        - type: error
          payload:
            error: string
            code: string
```

### 3.4 响应数据类型

```yaml
types:
  PatternSummary:
    pattern_id: string
    name: string
    dimension: string
    description: string
    sample_count: integer
    avg_views: integer
    difficulty: string  # easy, medium, hard

  PatternDetail:
    pattern_id: string
    name: string
    dimension: string
    description: string
    formula: string  # 有趣度计算公式
    metrics:
      sample_count: integer
      avg_views: integer
      avg_engagement: float
      cross_language_ratio: float
    examples: array[VideoExample]
    action_guide: ActionGuide
    related_patterns: array[string]

  LearningBlock:
    block_id: string
    title: string
    type: string  # concept, pattern, action
    content: string
    patterns: array[string]
    next_blocks: array[string]

  VideoExample:
    youtube_id: string
    title: string
    channel_name: string
    views: integer
    url: string

  ActionGuide:
    summary: string
    steps: array[string]
    prerequisites: array[string]
    expected_outcome: string

  ContentQuadrantChart:
    type: object
    description: 四象限散点图，仅用于 ContentQuadrant 可视化
    properties:
      x_axis: string  # views
      y_axis: string  # engagement_rate
      quadrants: array[Quadrant]  # [star, niche, viral, dog]

  DurationDistributionChart:
    type: object
    description: 时长分布条形图，仅用于 DurationMatrix 可视化
    properties:
      x_axis: string  # duration_bucket
      y_axis: string  # avg_views
      buckets: array[DurationBucket]
```

---

## 4. 内部模块接口

### 4.1 DataCollector

```python
class DataCollector:
    """数据收集器接口"""

    def __init__(self, config: Config) -> None:
        """
        初始化数据收集器

        Args:
            config: 配置对象
        """
        pass

    def search_videos(
        self,
        keyword: str,
        max_results: int = 50,
        region: str = "US",
        time_range: str = "month"
    ) -> List[CompetitorVideo]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            region: 目标地区 (ISO 3166-1)
            time_range: 时间范围 (week/month/quarter)

        Returns:
            竞品视频列表

        Raises:
            QuotaExceededError: API 配额超限
            NetworkError: 网络错误
        """
        pass

    def filter_quality_videos(
        self,
        videos: List[CompetitorVideo],
        min_views: int = 1000,
        min_likes: int = 50,
        max_duration: int = 3600
    ) -> List[CompetitorVideo]:
        """
        筛选高质量视频

        Args:
            videos: 视频列表
            min_views: 最小播放量
            min_likes: 最小点赞数
            max_duration: 最大时长 (秒)

        Returns:
            筛选后的视频列表
        """
        pass

    def save_videos(
        self,
        videos: List[CompetitorVideo],
        output_path: Path
    ) -> None:
        """
        保存视频数据

        Args:
            videos: 视频列表
            output_path: 输出路径
        """
        pass
```

### 4.2 ArbitrageAnalyzer

```python
class ArbitrageAnalyzer:
    """套利分析器接口 - 发现被低估的创作机会"""

    def __init__(self, db_path: str = "data/youtube_data.db") -> None:
        """
        初始化套利分析器

        Args:
            db_path: 数据库路径
        """
        pass

    def analyze_all(self, min_views: int = 1000) -> ArbitrageResult:
        """
        执行完整套利分析

        Args:
            min_views: 最小播放量筛选

        Returns:
            ArbitrageResult:
                sample_size: int
                topic_arbitrage: TopicArbitrageResult
                channel_arbitrage: ChannelArbitrageResult
                duration_arbitrage: DurationArbitrageResult
                timing_arbitrage: TimingArbitrageResult
                summary: ArbitrageSummary
        """
        pass

    def analyze_topic_arbitrage(self) -> TopicArbitrageResult:
        """
        话题套利分析 - 构建关键词网络，发现桥梁话题

        有趣度计算公式：
            信息有趣度 = 信息的价值程度 / 信息的传播程度

        利用中心性近似求解有趣度：
            在一个信息网络中，某个节点的有趣度 = 中介中心性 / 程度中心性

        Returns:
            TopicArbitrageResult:
                network_stats: Dict  # nodes, edges, density
                bridge_topics: List[Dict]  # keyword, betweenness, degree, interestingness
                insight: str
        """
        pass

    def analyze_channel_arbitrage(self) -> ChannelArbitrageResult:
        """
        频道套利分析 - 发现小频道爆款机会

        核心逻辑：
            小频道出爆款 = 内容被低估

        Returns:
            ChannelArbitrageResult:
                small_channel_opportunities: List[Dict]  # channel, max_views, interestingness
                large_channel_baseline: Dict
                insight: str
        """
        pass

    def analyze_duration_arbitrage(self) -> DurationArbitrageResult:
        """
        时长套利分析 - 发现时长空白区

        核心公式：
            有趣度 = 需求(播放量) / 供给(视频数)

        Returns:
            DurationArbitrageResult:
                buckets: List[Dict]  # duration_range, supply_ratio, demand_ratio, interestingness
                optimal_duration: str
                insight: str
        """
        pass

    def analyze_timing_arbitrage(self) -> TimingArbitrageResult:
        """
        趋势套利分析 - 发现上升话题

        核心逻辑：
            上升趋势 = 近期频率 / 历史频率

        Returns:
            TimingArbitrageResult:
                rising_topics: List[Dict]  # keyword, trend_ratio
                falling_topics: List[Dict]
                insight: str
        """
        pass

    def profile_creator(self) -> CreatorProfile:
        """
        博主画像定位

        Returns:
            CreatorProfile:
                recommended_tier: str  # beginner, mid_tier, top_tier
                suitable_strategies: List[str]
                unsuitable_strategies: List[str]
                action_items: List[str]
        """
        pass
```

### 4.3 PatternAnalyzer

```python
class PatternAnalyzer:
    """模式分析器接口"""

    def analyze_videos(
        self,
        videos: List[CompetitorVideo],
        max_cases: int = 10
    ) -> AnalysisResult:
        """
        分析视频模式

        Args:
            videos: 视频列表
            max_cases: 最大案例数

        Returns:
            AnalysisResult:
                total_videos: int
                selected_cases: List[CompetitorVideo]
                pattern_distribution: Dict[str, int]
                typical_features: Dict[str, Any]
                patterns_summary: str
        """
        pass

    def identify_pattern(
        self,
        video: CompetitorVideo
    ) -> Tuple[str, float]:
        """
        识别单个视频的模式

        Args:
            video: 视频对象

        Returns:
            (pattern_type, confidence_score)
        """
        pass
```

### 4.4 SpecGenerator

```python
class SpecGenerator:
    """规约生成器接口"""

    def generate_spec(
        self,
        research_report: ResearchReport,
        style: str = "tutorial",
        target_duration: int = 600
    ) -> Spec:
        """
        生成视频规约

        Args:
            research_report: 调研报告
            style: 内容风格
            target_duration: 目标时长 (秒)

        Returns:
            Spec:
                spec_id: str
                topic: str
                target_duration: int
                style: str
                event_1: str
                event_2: str
                event_3: str
                meaning: str
                target_audience: str
                cta: str
        """
        pass
```

### 4.5 ScriptCreator

```python
class ScriptCreator:
    """脚本创作器接口"""

    def create_script(
        self,
        spec: Spec,
        template: Optional[Template] = None,
        use_ai: bool = False
    ) -> Script:
        """
        创建脚本

        Args:
            spec: 视频规约
            template: 脚本模板 (可选)
            use_ai: 是否使用 AI 辅助

        Returns:
            Script:
                script_id: str
                title: str
                content: str
                word_count: int
                estimated_duration: int
                seo_score: int
        """
        pass

    def optimize_seo(
        self,
        script: Script
    ) -> SEOReport:
        """
        SEO 优化

        Args:
            script: 脚本对象

        Returns:
            SEOReport:
                seo_score: int
                title_analysis: Dict
                description_analysis: Dict
                tag_suggestions: List[str]
        """
        pass
```

### 4.6 VideoProducer

```python
class VideoProducer:
    """视频制作器接口"""

    def produce(
        self,
        script: Script,
        assets: List[Asset],
        config: ProductionConfig
    ) -> Video:
        """
        合成视频

        Args:
            script: 脚本
            assets: 素材列表
            config: 制作配置

        Returns:
            Video:
                video_id: str
                file_path: str
                duration: int
                resolution: str
                status: str
        """
        pass

    def generate_thumbnail(
        self,
        title: str,
        style: Dict[str, Any],
        background: Optional[Path] = None
    ) -> Thumbnail:
        """
        生成封面

        Args:
            title: 封面标题
            style: 样式配置
            background: 背景图片路径

        Returns:
            Thumbnail:
                thumbnail_id: str
                file_path: str
                width: int
                height: int
        """
        pass
```

### 4.7 UploadManager

```python
class UploadManager:
    """上传管理器接口"""

    def upload(
        self,
        video: Video,
        config: UploadConfig
    ) -> UploadResult:
        """
        上传视频到 YouTube

        Args:
            video: 视频对象
            config: 上传配置

        Returns:
            UploadResult:
                youtube_id: str
                status: str
                upload_time: datetime
                token_consumed: int

        Raises:
            AuthenticationError: 认证失败
            UploadError: 上传失败
            QuotaExceededError: 配额超限
        """
        pass

    def verify(
        self,
        youtube_id: str
    ) -> VerificationResult:
        """
        验证上传结果

        Args:
            youtube_id: YouTube 视频 ID

        Returns:
            VerificationResult:
                title_match: bool
                description_match: bool
                thumbnail_uploaded: bool
                subtitle_uploaded: bool
                overall_pass: bool
        """
        pass

    def schedule(
        self,
        youtube_id: str,
        publish_time: datetime
    ) -> bool:
        """
        设置定时发布

        Args:
            youtube_id: YouTube 视频 ID
            publish_time: 发布时间

        Returns:
            是否设置成功
        """
        pass
```

### 4.8 MetricsCollector

```python
class MetricsCollector:
    """数据采集器接口"""

    def collect(
        self,
        youtube_id: str,
        period: str = "7d"
    ) -> Metrics:
        """
        采集视频数据

        Args:
            youtube_id: YouTube 视频 ID
            period: 统计周期 (7d/30d/lifetime)

        Returns:
            Metrics:
                views: int
                watch_time_minutes: int
                average_view_duration: int
                ctr: float
                likes: int
                comments: int
                subscribers_gained: int
        """
        pass

    def generate_report(
        self,
        metrics: Metrics,
        baseline: Optional[Metrics] = None
    ) -> AnalyticsReport:
        """
        生成报告

        Args:
            metrics: 当前数据
            baseline: 基线数据 (用于对比)

        Returns:
            AnalyticsReport (Markdown 格式)
        """
        pass

    def suggest_optimizations(
        self,
        report: AnalyticsReport
    ) -> OptimizationSuggestions:
        """
        生成优化建议

        Returns:
            OptimizationSuggestions:
                cover_suggestions: List[str]
                title_suggestions: List[str]
                content_suggestions: List[str]
                next_topic_ideas: List[str]
        """
        pass
```

### 4.9 MultiDimensionPatternAnalyzer

```python
class MultiDimensionPatternAnalyzer:
    """多维度模式分析器接口 - 基于42个已发现模式"""

    def __init__(self, db_path: str = "data/youtube_data.db") -> None:
        """
        初始化模式分析器

        Args:
            db_path: 数据库路径

        数据基础：
            - 中文数据：N = 2,340 条
            - 多语言数据：N = 172 条（8种语言）
            - 已发现模式：42 个
        """
        pass

    def analyze_all_dimensions(self) -> Dict[str, DimensionAnalysisResult]:
        """
        执行全维度分析

        有趣度计算公式：
            信息有趣度 = 信息的价值程度 / 信息的传播程度

        利用中心性近似求解有趣度：
            在一个信息网络中，某个节点的有趣度 = 中介中心性 / 程度中心性

        Returns:
            Dict 包含5个维度的分析结果:
                - variable: 变量分布分析
                - temporal: 时间维度分析
                - spatial: 空间维度分析
                - channel: 频道维度分析
                - user: 用户维度分析
        """
        pass

    def analyze_variable_distribution(self) -> VariableDistributionResult:
        """
        变量分布分析 - 10个变量的分布特征

        分析变量:
            1. 播放量 (view_count)
            2. 点赞数 (like_count)
            3. 评论数 (comment_count)
            4. 时长 (duration)
            5. 频道订阅数 (subscriber_count)
            6. 发布时间 (upload_date)
            7. 互动率 (engagement_rate)
            8. 有趣度分数 (interestingness_score)
            9. 语言 (language)
            10. 频道类型 (channel_type)

        Returns:
            VariableDistributionResult:
                distributions: Dict[str, DistributionStats]
                correlations: List[CorrelationPair]
                outliers: List[OutlierInfo]
                insights: List[str]
        """
        pass

    def analyze_temporal_dimension(self) -> TemporalAnalysisResult:
        """
        时间维度分析 - 发布时间与表现的关系

        Returns:
            TemporalAnalysisResult:
                best_upload_times: List[TimeSlot]
                trend_patterns: List[TrendPattern]
                seasonality: SeasonalityInfo
                insights: List[str]
        """
        pass

    def analyze_spatial_dimension(self) -> SpatialAnalysisResult:
        """
        空间维度分析 - 跨语言/地区市场分析

        Returns:
            SpatialAnalysisResult:
                language_distribution: Dict[str, LanguageStats]
                cross_language_opportunities: List[CrossLanguageOpportunity]
                market_gaps: List[MarketGap]
                insights: List[str]
        """
        pass

    def analyze_channel_dimension(self) -> ChannelAnalysisResult:
        """
        频道维度分析 - 频道特征与表现的关系

        Returns:
            ChannelAnalysisResult:
                channel_tiers: Dict[str, TierStats]  # beginner, mid_tier, top_tier
                success_patterns: List[SuccessPattern]
                growth_trajectories: List[GrowthTrajectory]
                insights: List[str]
        """
        pass

    def analyze_user_dimension(self) -> UserAnalysisResult:
        """
        用户维度分析 - 受众特征与互动模式

        Returns:
            UserAnalysisResult:
                engagement_patterns: List[EngagementPattern]
                comment_themes: List[CommentTheme]
                audience_segments: List[AudienceSegment]
                insights: List[str]
        """
        pass

    def get_pattern_detail(self, pattern_id: str) -> PatternDetail:
        """
        获取单个模式的详细信息

        Args:
            pattern_id: 模式 ID (如 P001, P023, P042)

        Returns:
            PatternDetail:
                pattern_id: str
                name: str
                dimension: str
                description: str
                formula: str
                sample_count: int
                avg_views: int
                avg_engagement: float
                examples: List[VideoExample]
                action_guide: ActionGuide
                related_patterns: List[str]
        """
        pass

    def generate_learning_path(
        self,
        tier: str = "beginner",
        goal: Optional[str] = None
    ) -> LearningPath:
        """
        生成学习路径

        Args:
            tier: 博主层级 (beginner/mid_tier/top_tier)
            goal: 学习目标 (如 "提升互动率")

        Returns:
            LearningPath:
                path_id: str
                title: str
                description: str
                blocks: List[LearningBlock]
                patterns: List[str]
                estimated_duration: str
                prerequisites: List[str]
        """
        pass

    def generate_action_guide(
        self,
        pattern_id: str,
        context: Optional[Dict] = None
    ) -> ActionGuide:
        """
        生成行动指南

        Args:
            pattern_id: 模式 ID
            context: 用户上下文（如频道信息）

        Returns:
            ActionGuide:
                pattern_id: str
                summary: str
                steps: List[ActionStep]
                prerequisites: List[str]
                expected_outcome: str
                difficulty: str
                time_estimate: str
        """
        pass
```

---

## 5. 外部服务接口

### 5.1 YouTube Data API (可选)

```yaml
service: YouTube Data API v3
base_url: https://www.googleapis.com/youtube/v3
auth: API Key / OAuth 2.0

endpoints:
  - name: search
    method: GET
    path: /search
    params:
      q: string           # 搜索关键词
      part: "snippet"
      type: "video"
      maxResults: integer # 最大 50
      regionCode: string  # ISO 3166-1
      relevanceLanguage: string
    rate_limit: 100 queries/day (API Key)
    quota_cost: 100 units

  - name: videos.list
    method: GET
    path: /videos
    params:
      id: string          # 视频 ID (逗号分隔)
      part: "snippet,statistics,contentDetails"
    quota_cost: 1 unit per video

  - name: videos.insert
    method: POST
    path: /videos
    params:
      part: "snippet,status"
    body:
      snippet:
        title: string
        description: string
        tags: string[]
        categoryId: string
      status:
        privacyStatus: string
        publishAt: string (ISO 8601)
    quota_cost: 1600 units

notes:
  - 每日配额默认 10,000 单位
  - 上传一个视频消耗约 1600 单位
  - 建议使用综合模式 (RPA) 减少 API 依赖
```

### 5.2 ElevenLabs TTS API

```yaml
service: ElevenLabs
base_url: https://api.elevenlabs.io/v1
auth: API Key (xi-api-key header)

endpoints:
  - name: text-to-speech
    method: POST
    path: /text-to-speech/{voice_id}
    headers:
      xi-api-key: string
      Content-Type: application/json
    body:
      text: string
      model_id: string    # eleven_monolingual_v1
      voice_settings:
        stability: float
        similarity_boost: float
    response: audio/mpeg

  - name: voices
    method: GET
    path: /voices
    description: 获取可用声音列表

rate_limit:
  free: 10,000 characters/month
  starter: 30,000 characters/month

notes:
  - 主要用于英文配音
  - 中文建议使用 MiniMax
```

### 5.3 MiniMax TTS API

```yaml
service: MiniMax
base_url: https://api.minimax.chat/v1
auth: API Key

endpoints:
  - name: t2a_v2
    method: POST
    path: /t2a_v2
    body:
      model: string         # speech-01-turbo
      text: string
      voice_setting:
        voice_id: string
        speed: float
        vol: float
        pitch: integer
    response: audio stream

notes:
  - 适合中文配音
  - 详见 https://platform.minimaxi.com/document
```

---

## 6. MCP 工具接口

### 6.1 Playwright MCP

```yaml
mcp: @playwright/mcp
description: 浏览器自动化

tools:
  - name: browser_navigate
    params:
      url: string
    description: 导航到 URL

  - name: browser_snapshot
    params: {}
    description: 获取页面快照 (accessibility tree)

  - name: browser_click
    params:
      element: string     # 元素描述
      ref: string         # 元素引用
    description: 点击元素

  - name: browser_type
    params:
      element: string
      ref: string
      text: string
      submit: boolean
    description: 输入文本

  - name: browser_file_upload
    params:
      paths: string[]
    description: 上传文件

  - name: browser_select_option
    params:
      element: string
      ref: string
      values: string[]
    description: 选择下拉选项

usage_in_publishing:
  1. browser_navigate → YouTube Studio
  2. browser_click → 创建按钮
  3. browser_file_upload → 上传视频
  4. browser_type → 填写标题、描述
  5. browser_click → 发布按钮
  6. browser_snapshot → 验证结果
```

### 6.2 yt-dlp CLI (本地工具)

```yaml
tool: yt-dlp
type: CLI

commands:
  - name: 获取视频信息
    command: |
      yt-dlp --dump-json "https://www.youtube.com/watch?v={video_id}"
    output: JSON (视频元数据)

  - name: 搜索视频
    command: |
      yt-dlp --dump-json --flat-playlist "ytsearch{n}:{keyword}"
    output: JSON (搜索结果)

  - name: 下载字幕
    command: |
      yt-dlp --write-auto-sub --sub-lang zh --skip-download "{url}"
    output: 字幕文件 (.vtt)

  - name: 下载视频
    command: |
      yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" -o "{output}" "{url}"
    output: 视频文件

notes:
  - 仅用于竞品分析，不用于下载他人内容
  - 遵守 real.md#版权合规 约束
```

---

## 7. 错误码定义

### 7.1 通用错误码

```yaml
errors:
  - code: E0001
    name: ConfigurationError
    message: 配置文件错误
    http_status: 500

  - code: E0002
    name: ValidationError
    message: 参数验证失败
    http_status: 400

  - code: E0003
    name: FileNotFoundError
    message: 文件不存在
    http_status: 404

  - code: E0004
    name: DatabaseError
    message: 数据库操作失败
    http_status: 500
```

### 7.2 调研模块错误码

```yaml
errors:
  - code: E1001
    name: QuotaExceededError
    message: API 配额已用尽
    recovery: 等待配额重置或减少请求

  - code: E1002
    name: SearchError
    message: 搜索失败
    recovery: 检查关键词和网络
```

### 7.3 发布模块错误码

```yaml
errors:
  - code: E4001
    name: AuthenticationError
    message: YouTube 登录失效
    recovery: 重新登录 Chrome

  - code: E4002
    name: UploadError
    message: 视频上传失败
    recovery: 检查视频格式和网络

  - code: E4003
    name: CaptchaRequired
    message: 需要验证码
    recovery: 人工介入完成验证

  - code: E4004
    name: RateLimitError
    message: 操作过于频繁
    recovery: 等待后重试
```

---

## 8. 接口版本管理

### 8.1 版本策略

```yaml
versioning:
  strategy: semantic
  format: "v{major}.{minor}.{patch}"

  compatibility:
    major: 不兼容的 API 变更
    minor: 向后兼容的功能新增
    patch: 向后兼容的问题修复

  deprecation:
    notice_period: 2 versions
    sunset_period: 4 versions
```

### 8.2 变更日志

```yaml
changelog:
  - version: "1.0.0"
    date: "2026-01-18"
    changes:
      - 初始版本
      - 支持五阶段流水线
      - CLI 接口完整定义
```

---

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-18 | 初始版本 |
| 1.1 | 2026-01-19 | 新增套利分析 CLI 命令和 ArbitrageAnalyzer 模块接口 |
| 1.2 | 2026-01-19 | 新增 dataflow CLI 命令，支持数据分层处理与层间转换 |
| 1.3 | 2026-01-24 | 新增模式分析 CLI 命令 (ytp pattern)，支持多维度分析、学习路径、模式详情 |
| 1.4 | 2026-01-24 | 新增 HTTP API 服务 (Section 3)：FastAPI 端点、WebSocket 实时进度、创作者仪表盘 |
| 1.5 | 2026-01-24 | 新增 MultiDimensionPatternAnalyzer 模块接口 (4.9)：5维度分析、42模式详情、学习路径生成 |

---

*引用本规格时使用：`.42cog/spec/dev/api.spec.md`*
