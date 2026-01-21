# 数据模型规约 (Data Specification)

> 定义实体结构、数据库 Schema、文件格式、数据流转
>
> **引用文档**：
> - 认知模型：`../../cog/cog.md`
> - 系统架构：`sys.spec.md`
> - 流水线规格：`../pm/pipeline.spec.md`

---

## 0. 数据分层架构

> **核心原则**：原始数据与加工数据分离，支持多目标复用和增量采集。

### 0.1 五层数据模型

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4: 分析层 (Insights)                              │
│   套利机会、推荐策略、洞察报告                          │
│   特点：按需计算、可缓存、目标相关                      │
│   存储：data/insights/                                   │
├─────────────────────────────────────────────────────────┤
│ Layer 3: 聚合层 (Aggregates)                            │
│   基线统计、话题网络、趋势数据                          │
│   特点：定期刷新、维度相关、可重建                      │
│   存储：data/cubes/                                      │
├─────────────────────────────────────────────────────────┤
│ Layer 2: 标签层 (Tags)                                  │
│   话题标签、受众标签、形式标签                          │
│   特点：依赖 NLP 模型、模型更新需重算                   │
│   存储：warehouse.db → video_tags, tag_definitions      │
├─────────────────────────────────────────────────────────┤
│ Layer 1: 清洗层 (Cleaned)                               │
│   去重、标准化字段、语言检测                            │
│   特点：幂等计算、可从原始层重建                        │
│   存储：warehouse.db → videos_cleaned                    │
├─────────────────────────────────────────────────────────┤
│ Layer 0: 原始层 (Raw)                                   │
│   yt-dlp 返回的原始 JSON                                │
│   特点：不可变、只追加、保留采集时间戳                  │
│   存储：data/raw/videos/*.jsonl                         │
└─────────────────────────────────────────────────────────┘
```

### 0.2 存储目录结构

```yaml
data/
├── raw/                        # Layer 0: 原始数据（不可变）
│   └── videos/
│       ├── 20260119_batch001.jsonl    # 每批采集一个文件
│       └── 20260119_batch002.jsonl
│
├── warehouse/                  # Layer 1-2: 清洗 + 标签
│   └── youtube.db
│       ├── videos_cleaned      # 清洗后的视频（只含原始字段）
│       ├── video_tags          # 标签关联表（多对多）
│       └── tag_definitions     # 标签定义
│
├── cubes/                      # Layer 3: 聚合数据
│   ├── baselines/
│   │   ├── global.json         # 元基线（跨领域）
│   │   └── scoped/             # 各维度基线
│   │       ├── 老年人_养生.json
│   │       └── 年轻人_健身.json
│   └── networks/
│       └── topic_cooccurrence.pkl
│
└── insights/                   # Layer 4: 分析结果
    └── arbitrage/
        └── 2026-01-19_老年人养生.json
```

### 0.3 层间依赖规则

| 规则 | 说明 |
|------|------|
| **单向依赖** | 只能依赖下游层：L4 → L3 → L2 → L1 → L0 |
| **原始不可变** | Layer 0 采集后只追加，永不修改 |
| **加工可重建** | Layer 1-4 任一层可从下层重新计算 |
| **元数据外置** | 阈值、权重、模型版本存配置文件，不存数据 |

### 0.4 多维索引设计

```yaml
# 视频的多维标签（Layer 2）
video_dimensions:
  topic:      [养生, 睡眠, 中医]      # 话题维度
  audience:   [老年人]                 # 受众维度
  format:     [科普]                   # 形式维度
  duration:   10-20min                 # 时长维度
  language:   zh                       # 语言维度

# 查询示例
query:
  # 目标：老年人健身
  audience: 老年人
  topic: 健身
  result: 返回所有匹配视频，用于建立该维度基线
```

### 0.5 增量采集流程

```python
def ensure_coverage(goal: str, threshold: float = 0.8):
    """确保某个目标的数据覆盖度"""

    # 1. 解析目标为维度组合
    dimensions = parse_goal(goal)  # e.g., {"audience": "老年人", "topic": "健身"}

    # 2. 查询已有数据
    existing = query_by_dimensions(dimensions)

    # 3. 评估覆盖度
    coverage = len(existing) / TARGET_BASELINE_SIZE

    # 4. 识别缺口
    if coverage < threshold:
        gap = int(TARGET_BASELINE_SIZE * (1 - coverage))
        # 5. 只采集缺口部分
        collect_new(dimensions, limit=gap)

    # 6. 更新/创建该维度的基线
    update_baseline(dimensions, existing + new_data)
```

### 0.6 基线分层

```yaml
baselines:
  # 元基线（跨领域，用于新领域快速启动）
  meta:
    健康类: {median: 8000, p75: 25000, common_duration: "5-15min"}
    娱乐类: {median: 30000, p75: 100000, common_duration: "1-3min"}
    教育类: {median: 5000, p75: 20000, common_duration: "10-30min"}

  # 维度基线（具体目标）
  scoped:
    "老年人×养生": {median: 8500, p75: 22000, sample_size: 1000}
    "年轻人×健身": {median: 15000, p75: 45000, sample_size: 800}

  # 基线更新策略
  refresh:
    meta: monthly          # 元基线每月更新
    scoped: on_demand      # 维度基线按需更新
```

---

## 1. 实体数据模型

### 1.1 核心实体关系图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Channel   │       │  Research   │       │ Competitor  │
│             │       │   Report    │       │   Video     │
└──────┬──────┘       └──────┬──────┘       └──────┬──────┘
       │                     │                     │
       │                     └──────────┬──────────┘
       │                                ▼
       │                     ┌─────────────────────┐
       │                     │        Spec         │
       │                     │ (视频规约)           │
       │                     └──────────┬──────────┘
       │                                │
       │                                ▼
       │                     ┌─────────────────────┐
       │                     │       Script        │
       │                     │ (创作脚本)           │
       │                     └──────────┬──────────┘
       │                                │
       ▼                                ▼
┌──────────────────────────────────────────────────┐
│                      Video                        │
│  (视频实体 - 贯穿全流程的核心载体)                  │
├──────────────────────────────────────────────────┤
│  • video_id (UUID)                               │
│  • youtube_id (发布后)                            │
│  • status: draft → scripting → producing →       │
│            ready → published/scheduled           │
└───────┬────────────────────┬─────────────────────┘
        │                    │
        ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Subtitle    │    │  Thumbnail    │    │  Analytics    │
│   (字幕)      │    │   (封面)      │    │   (数据)      │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 2. 实体 Schema 定义

### 2.1 Video (视频)

```yaml
entity: Video
description: 视频实体，内容的最终载体
table: videos

fields:
  - name: video_id
    type: UUID
    primary_key: true
    description: 内部唯一标识

  - name: youtube_id
    type: VARCHAR(11)
    nullable: true
    unique: true
    description: YouTube 视频 ID (发布后填充)

  - name: title
    type: VARCHAR(100)
    nullable: false
    constraints:
      - max_length: 100  # YouTube 限制
    description: 视频标题

  - name: description
    type: TEXT
    nullable: true
    constraints:
      - max_length: 5000  # YouTube 限制
    description: 视频描述

  - name: tags
    type: JSON  # ["tag1", "tag2", ...]
    nullable: true
    constraints:
      - max_items: 500  # YouTube 限制总字符
    description: 标签列表

  - name: file_path
    type: VARCHAR(500)
    nullable: true
    description: 本地视频文件路径

  - name: duration
    type: INTEGER
    nullable: true
    description: 视频时长 (秒)

  - name: resolution
    type: VARCHAR(10)
    nullable: true
    enum: ["720p", "1080p", "4K"]
    description: 视频分辨率

  - name: status
    type: VARCHAR(20)
    nullable: false
    default: "draft"
    enum: ["draft", "scripting", "producing", "ready", "published", "scheduled"]
    description: 视频状态

  - name: privacy
    type: VARCHAR(10)
    nullable: false
    default: "private"
    enum: ["public", "unlisted", "private"]
    description: 隐私设置

  - name: channel_id
    type: UUID
    foreign_key: channels.channel_id
    nullable: true
    description: 所属频道

  - name: spec_id
    type: UUID
    foreign_key: specs.spec_id
    nullable: true
    description: 关联的视频规约

  - name: script_id
    type: UUID
    foreign_key: scripts.script_id
    nullable: true
    description: 关联的脚本

  - name: published_at
    type: DATETIME
    nullable: true
    description: 发布时间

  - name: scheduled_at
    type: DATETIME
    nullable: true
    description: 定时发布时间

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP
    description: 创建时间

  - name: updated_at
    type: DATETIME
    default: CURRENT_TIMESTAMP
    on_update: CURRENT_TIMESTAMP
    description: 更新时间

indexes:
  - name: idx_videos_status
    fields: [status]
  - name: idx_videos_youtube_id
    fields: [youtube_id]
  - name: idx_videos_channel_id
    fields: [channel_id]
```

### 2.2 Script (脚本)

```yaml
entity: Script
description: 创作脚本，内容的文本形态
table: scripts

fields:
  - name: script_id
    type: UUID
    primary_key: true
    description: 脚本唯一标识

  - name: video_id
    type: UUID
    foreign_key: videos.video_id
    nullable: true
    description: 关联的视频

  - name: version
    type: INTEGER
    default: 1
    description: 版本号

  - name: title
    type: VARCHAR(100)
    nullable: false
    description: 脚本标题

  - name: content
    type: TEXT
    nullable: false
    description: 脚本内容 (Markdown 格式)

  - name: word_count
    type: INTEGER
    nullable: true
    description: 字数统计

  - name: estimated_duration
    type: INTEGER
    nullable: true
    description: 预估时长 (秒)

  - name: seo_score
    type: INTEGER
    nullable: true
    constraints:
      - min: 0
      - max: 100
    description: SEO 评分

  - name: status
    type: VARCHAR(20)
    default: "draft"
    enum: ["draft", "reviewing", "approved", "archived"]
    description: 脚本状态

  - name: spec_id
    type: UUID
    foreign_key: specs.spec_id
    nullable: true
    description: 关联的规约

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

  - name: updated_at
    type: DATETIME
    default: CURRENT_TIMESTAMP
    on_update: CURRENT_TIMESTAMP

indexes:
  - name: idx_scripts_video_id
    fields: [video_id]
  - name: idx_scripts_status
    fields: [status]

unique_constraints:
  - name: uq_script_version
    fields: [video_id, version]
```

### 2.3 Subtitle (字幕)

```yaml
entity: Subtitle
description: 字幕文件，内容的时间轴文本
table: subtitles

fields:
  - name: subtitle_id
    type: UUID
    primary_key: true

  - name: video_id
    type: UUID
    foreign_key: videos.video_id
    nullable: false

  - name: language
    type: VARCHAR(10)
    nullable: false
    default: "zh"
    description: 语言代码 (ISO 639-1)

  - name: type
    type: VARCHAR(20)
    default: "auto"
    enum: ["auto", "manual", "translated"]
    description: 字幕类型

  - name: format
    type: VARCHAR(10)
    default: "vtt"
    enum: ["srt", "vtt", "ass"]
    description: 字幕格式

  - name: file_path
    type: VARCHAR(500)
    nullable: false
    description: 字幕文件路径

  - name: is_synced
    type: BOOLEAN
    default: false
    description: 是否已同步校验

  - name: is_uploaded
    type: BOOLEAN
    default: false
    description: 是否已上传 YouTube

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

indexes:
  - name: idx_subtitles_video_id
    fields: [video_id]

unique_constraints:
  - name: uq_subtitle_video_language
    fields: [video_id, language, type]
```

### 2.4 Thumbnail (封面)

```yaml
entity: Thumbnail
description: 视频封面图
table: thumbnails

fields:
  - name: thumbnail_id
    type: UUID
    primary_key: true

  - name: video_id
    type: UUID
    foreign_key: videos.video_id
    nullable: false

  - name: file_path
    type: VARCHAR(500)
    nullable: false

  - name: width
    type: INTEGER
    constraints:
      - min: 1280
    description: 宽度 (像素)

  - name: height
    type: INTEGER
    constraints:
      - min: 720
    description: 高度 (像素)

  - name: file_size
    type: INTEGER
    constraints:
      - max: 2097152  # 2MB
    description: 文件大小 (字节)

  - name: is_active
    type: BOOLEAN
    default: true
    description: 是否为当前使用的封面

  - name: is_uploaded
    type: BOOLEAN
    default: false
    description: 是否已上传 YouTube

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

indexes:
  - name: idx_thumbnails_video_id
    fields: [video_id]
```

### 2.5 Spec (规约)

```yaml
entity: Spec
description: 视频规约，策划阶段的产出
table: specs

fields:
  - name: spec_id
    type: UUID
    primary_key: true

  - name: topic
    type: VARCHAR(200)
    nullable: false
    description: 视频主题

  - name: target_duration
    type: INTEGER
    nullable: false
    description: 目标时长 (秒)

  - name: style
    type: VARCHAR(50)
    enum: ["tutorial", "story", "review", "vlog", "explainer"]
    description: 内容风格

  - name: event_1
    type: TEXT
    description: 三事件结构 - 事件1 (引入问题)

  - name: event_2
    type: TEXT
    description: 三事件结构 - 事件2 (展示方案)

  - name: event_3
    type: TEXT
    description: 三事件结构 - 事件3 (总结升华)

  - name: meaning
    type: TEXT
    description: 生发意义

  - name: target_audience
    type: VARCHAR(200)
    description: 目标受众

  - name: cta
    type: VARCHAR(200)
    description: 行动号召

  - name: research_id
    type: UUID
    foreign_key: research_reports.report_id
    nullable: true
    description: 关联的调研报告

  - name: file_path
    type: VARCHAR(500)
    description: 规约文件路径 (Markdown)

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP
```

### 2.6 CompetitorVideo (竞品视频)

```yaml
entity: CompetitorVideo
description: 竞品视频元数据，调研阶段采集
table: competitor_videos

fields:
  - name: id
    type: INTEGER
    primary_key: true
    auto_increment: true

  - name: youtube_id
    type: VARCHAR(11)
    nullable: false
    unique: true

  - name: title
    type: VARCHAR(200)
    nullable: false

  - name: description
    type: TEXT

  - name: channel_name
    type: VARCHAR(100)

  - name: channel_id
    type: VARCHAR(50)

  - name: view_count
    type: BIGINT
    default: 0

  - name: like_count
    type: INTEGER
    default: 0

  - name: comment_count
    type: INTEGER
    default: 0

  - name: duration
    type: INTEGER
    description: 时长 (秒)

  - name: published_at
    type: DATETIME

  - name: tags
    type: JSON

  - name: category
    type: VARCHAR(50)

  - name: keyword_source
    type: VARCHAR(100)
    description: 来源关键词

  - name: pattern_type
    type: VARCHAR(50)
    enum: ["cognitive_impact", "storytelling", "knowledge_sharing", "interaction_guide", "unknown"]
    description: 识别的模式类型

  - name: pattern_score
    type: FLOAT
    description: 模式匹配得分

  - name: collected_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

indexes:
  - name: idx_competitor_youtube_id
    fields: [youtube_id]
  - name: idx_competitor_keyword
    fields: [keyword_source]
  - name: idx_competitor_pattern
    fields: [pattern_type]
```

### 2.7 Analytics (数据分析)

```yaml
entity: Analytics
description: 视频表现数据
table: analytics

fields:
  - name: id
    type: INTEGER
    primary_key: true
    auto_increment: true

  - name: video_id
    type: UUID
    foreign_key: videos.video_id
    nullable: false

  - name: report_date
    type: DATE
    nullable: false
    description: 报告日期

  - name: period
    type: VARCHAR(10)
    enum: ["7d", "30d", "lifetime"]
    description: 统计周期

  - name: views
    type: INTEGER
    default: 0

  - name: watch_time_minutes
    type: INTEGER
    default: 0

  - name: average_view_duration
    type: INTEGER
    description: 平均观看时长 (秒)

  - name: ctr
    type: FLOAT
    description: 点击率 (%)

  - name: likes
    type: INTEGER
    default: 0

  - name: dislikes
    type: INTEGER
    default: 0

  - name: comments
    type: INTEGER
    default: 0

  - name: shares
    type: INTEGER
    default: 0

  - name: subscribers_gained
    type: INTEGER
    default: 0

  - name: subscribers_lost
    type: INTEGER
    default: 0

  - name: impressions
    type: INTEGER
    default: 0

  - name: unique_viewers
    type: INTEGER
    default: 0

  - name: collected_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

indexes:
  - name: idx_analytics_video_date
    fields: [video_id, report_date]

unique_constraints:
  - name: uq_analytics_video_date_period
    fields: [video_id, report_date, period]
```

### 2.8 Task (任务)

```yaml
entity: Task
description: 工作流任务
table: tasks

fields:
  - name: task_id
    type: UUID
    primary_key: true

  - name: video_id
    type: UUID
    foreign_key: videos.video_id
    nullable: true

  - name: stage
    type: VARCHAR(20)
    enum: ["research", "planning", "production", "publishing", "analytics"]
    nullable: false

  - name: type
    type: VARCHAR(50)
    nullable: false
    description: 任务类型 (如 collect_videos, generate_script)

  - name: status
    type: VARCHAR(20)
    default: "pending"
    enum: ["pending", "running", "completed", "failed", "cancelled"]

  - name: input_data
    type: JSON
    description: 任务输入参数

  - name: output_data
    type: JSON
    description: 任务输出结果

  - name: error_message
    type: TEXT
    nullable: true

  - name: retry_count
    type: INTEGER
    default: 0

  - name: started_at
    type: DATETIME
    nullable: true

  - name: completed_at
    type: DATETIME
    nullable: true

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

indexes:
  - name: idx_tasks_video_id
    fields: [video_id]
  - name: idx_tasks_stage
    fields: [stage]
  - name: idx_tasks_status
    fields: [status]
```

---

## 3. 文件格式规约

### 3.1 视频文件

```yaml
format: Video
extensions: [.mp4, .mov, .mkv]
preferred: .mp4

constraints:
  codec: H.264 | H.265
  resolution:
    min: 1280x720
    preferred: 1920x1080
    max: 3840x2160
  frame_rate: 24 | 30 | 60 fps
  bitrate:
    video: 8-12 Mbps (1080p)
    audio: 192 kbps
  audio_codec: AAC
  max_file_size: 256 GB  # YouTube 限制

naming_convention:
  pattern: "{video_id}_{YYYYMMDD}_{status}.mp4"
  example: "abc123_20260118_final.mp4"

storage_path: data/videos/
```

### 3.2 字幕文件

```yaml
format: Subtitle
extensions: [.srt, .vtt]
preferred: .vtt

constraints:
  encoding: UTF-8
  max_line_length:
    zh: 42 characters
    en: 72 characters
  max_lines_per_screen: 2
  min_display_duration: 1 second
  max_display_duration: 7 seconds

srt_format:
  example: |
    1
    00:00:01,000 --> 00:00:04,000
    这是第一行字幕

    2
    00:00:04,500 --> 00:00:08,000
    这是第二行字幕

vtt_format:
  example: |
    WEBVTT

    00:00:01.000 --> 00:00:04.000
    这是第一行字幕

    00:00:04.500 --> 00:00:08.000
    这是第二行字幕

naming_convention:
  pattern: "{video_id}_{language}.{ext}"
  example: "abc123_zh.vtt"

storage_path: data/transcripts/
```

### 3.3 封面图片

```yaml
format: Thumbnail
extensions: [.jpg, .png]
preferred: .jpg

constraints:
  resolution:
    required: 1280x720
    aspect_ratio: 16:9
  file_size:
    max: 2 MB
  color_space: sRGB
  quality: >= 85% (JPEG)

naming_convention:
  pattern: "{video_id}_thumb_{variant}.jpg"
  example: "abc123_thumb_v1.jpg"

storage_path: data/thumbnails/
```

### 3.4 配置文件

```yaml
format: UploadConfig
extension: .json

schema:
  video:
    path: string (absolute path)
    title: string (max 100)
    description: string (max 5000)
    tags: string[] (max 500 chars total)
    category: string
    language: string (ISO 639-1)
    privacy: enum [public, unlisted, private]
    madeForKids: boolean

  thumbnail:
    path: string (absolute path)

  subtitles:
    path: string (absolute path)
    language: string (ISO 639-1)

  schedule:
    enabled: boolean
    publishAt: string (ISO 8601)

  playlist:
    enabled: boolean
    name: string

example: |
  {
    "video": {
      "path": "/path/to/video.mp4",
      "title": "视频标题",
      "description": "视频描述...",
      "tags": ["标签1", "标签2"],
      "category": "Education",
      "language": "zh",
      "privacy": "public",
      "madeForKids": false
    },
    "thumbnail": {
      "path": "/path/to/thumbnail.jpg"
    },
    "subtitles": {
      "path": "/path/to/subtitles.vtt",
      "language": "zh"
    },
    "schedule": {
      "enabled": false
    }
  }

storage_path: config/
```

### 3.5 报告文件

```yaml
format: Report
extensions: [.md, .json]

types:
  - name: ResearchReport
    extension: .md
    path: data/reports/research_{keyword}_{date}.md
    sections:
      - 调研概述
      - 市场分析
      - 竞品清单
      - 模式总结
      - 建议

  - name: AnalyticsReport
    extension: .md
    path: data/reports/analytics_{video_id}_{period}.md
    sections:
      - 数据概览
      - 指标详情
      - 趋势分析
      - 对比分析
      - 优化建议

  - name: SEOReport
    extension: .json
    path: scripts/seo_report_{video_id}.json
    schema:
      seo_score: integer
      title_analysis: object
      description_analysis: object
      tag_suggestions: string[]
```

---

## 4. 数据流转

### 4.1 阶段间数据流

```
┌─────────────┐
│   调研      │
│  (Research) │
└──────┬──────┘
       │ 输出:
       │ • competitor_videos (DB)
       │ • research_report.md (File)
       │ • videos.csv (File)
       ▼
┌─────────────┐
│   策划      │
│ (Planning)  │
└──────┬──────┘
       │ 输出:
       │ • spec (DB + File)
       │ • script (DB + File)
       │ • seo_report.json (File)
       ▼
┌─────────────┐
│   制作      │
│(Production) │
└──────┬──────┘
       │ 输出:
       │ • video (DB + File)
       │ • subtitle (DB + File)
       │ • thumbnail (DB + File)
       ▼
┌─────────────┐
│   发布      │
│(Publishing) │
└──────┬──────┘
       │ 输出:
       │ • youtube_id (DB update)
       │ • upload_report.json (File)
       ▼
┌─────────────┐
│   复盘      │
│ (Analytics) │
└──────┬──────┘
       │ 输出:
       │ • analytics (DB)
       │ • analytics_report.md (File)
       │ • optimization.md (File)
       ▼
┌─────────────┐
│ 下轮调研    │
│  (Loop)     │
└─────────────┘
```

### 4.2 状态流转图

```
Video 状态:

  ┌────────┐     策划完成      ┌───────────┐     制作开始     ┌───────────┐
  │ draft  │ ────────────────→ │ scripting │ ───────────────→ │ producing │
  └────────┘                   └───────────┘                   └─────┬─────┘
       ▲                                                             │
       │                                                             │
       │ 失败/取消                                           制作完成 │
       │                                                             ▼
       │                       ┌───────────┐     上传成功     ┌───────────┐
       └────────────────────── │   ready   │ ───────────────→ │ published │
                               └───────────┘                   └───────────┘
                                     │
                                     │ 定时发布
                                     ▼
                               ┌───────────┐
                               │ scheduled │
                               └───────────┘
```

---

## 5. 数据库初始化

### 5.1 SQLite DDL

```sql
-- 文件: scripts/init_db.sql

-- 视频表
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    youtube_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT,  -- JSON array
    file_path TEXT,
    duration INTEGER,
    resolution TEXT CHECK(resolution IN ('720p', '1080p', '4K')),
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK(status IN ('draft', 'scripting', 'producing', 'ready', 'published', 'scheduled')),
    privacy TEXT NOT NULL DEFAULT 'private'
        CHECK(privacy IN ('public', 'unlisted', 'private')),
    channel_id TEXT,
    spec_id TEXT,
    script_id TEXT,
    published_at DATETIME,
    scheduled_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_youtube_id ON videos(youtube_id);

-- 脚本表
CREATE TABLE IF NOT EXISTS scripts (
    script_id TEXT PRIMARY KEY,
    video_id TEXT,
    version INTEGER DEFAULT 1,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER,
    estimated_duration INTEGER,
    seo_score INTEGER CHECK(seo_score >= 0 AND seo_score <= 100),
    status TEXT DEFAULT 'draft'
        CHECK(status IN ('draft', 'reviewing', 'approved', 'archived')),
    spec_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    UNIQUE(video_id, version)
);

-- 字幕表
CREATE TABLE IF NOT EXISTS subtitles (
    subtitle_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'zh',
    type TEXT DEFAULT 'auto' CHECK(type IN ('auto', 'manual', 'translated')),
    format TEXT DEFAULT 'vtt' CHECK(format IN ('srt', 'vtt', 'ass')),
    file_path TEXT NOT NULL,
    is_synced INTEGER DEFAULT 0,
    is_uploaded INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    UNIQUE(video_id, language, type)
);

-- 封面表
CREATE TABLE IF NOT EXISTS thumbnails (
    thumbnail_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    is_active INTEGER DEFAULT 1,
    is_uploaded INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- 竞品视频表
CREATE TABLE IF NOT EXISTS competitor_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    youtube_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    channel_name TEXT,
    channel_id TEXT,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    duration INTEGER,
    published_at DATETIME,
    tags TEXT,  -- JSON array
    category TEXT,
    keyword_source TEXT,
    pattern_type TEXT CHECK(pattern_type IN
        ('cognitive_impact', 'storytelling', 'knowledge_sharing', 'interaction_guide', 'unknown')),
    pattern_score REAL,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_competitor_keyword ON competitor_videos(keyword_source);
CREATE INDEX idx_competitor_pattern ON competitor_videos(pattern_type);

-- 数据分析表
CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    report_date DATE NOT NULL,
    period TEXT CHECK(period IN ('7d', '30d', 'lifetime')),
    views INTEGER DEFAULT 0,
    watch_time_minutes INTEGER DEFAULT 0,
    average_view_duration INTEGER,
    ctr REAL,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    subscribers_gained INTEGER DEFAULT 0,
    subscribers_lost INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    UNIQUE(video_id, report_date, period)
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    video_id TEXT,
    stage TEXT NOT NULL CHECK(stage IN
        ('research', 'planning', 'production', 'publishing', 'analytics')),
    type TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN
        ('pending', 'running', 'completed', 'failed', 'cancelled')),
    input_data TEXT,  -- JSON
    output_data TEXT,  -- JSON
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE INDEX idx_tasks_stage ON tasks(stage);
CREATE INDEX idx_tasks_status ON tasks(status);

-- 套利分析结果表
CREATE TABLE IF NOT EXISTS arbitrage_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id TEXT NOT NULL UNIQUE,
    sample_size INTEGER NOT NULL,
    min_views_filter INTEGER,
    topic_arbitrage TEXT,      -- JSON: TopicArbitrageResult
    channel_arbitrage TEXT,    -- JSON: ChannelArbitrageResult
    duration_arbitrage TEXT,   -- JSON: DurationArbitrageResult
    timing_arbitrage TEXT,     -- JSON: TimingArbitrageResult
    summary TEXT,              -- JSON: ArbitrageSummary
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_arbitrage_created ON arbitrage_results(created_at);

-- 博主画像表
CREATE TABLE IF NOT EXISTS creator_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL UNIQUE,
    recommended_tier TEXT CHECK(recommended_tier IN ('beginner', 'mid_tier', 'top_tier')),
    suitable_strategies TEXT,     -- JSON array
    unsuitable_strategies TEXT,   -- JSON array
    action_items TEXT,            -- JSON array
    arbitrage_analysis_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (arbitrage_analysis_id) REFERENCES arbitrage_results(analysis_id)
);
```

### 5.2 套利分析 Schema

```yaml
# 套利分析结果 (ArbitrageResult)
entity: ArbitrageResult
description: 套利分析完整结果
table: arbitrage_results

fields:
  - name: analysis_id
    type: UUID
    primary_key: true
    description: 分析唯一标识

  - name: sample_size
    type: INTEGER
    nullable: false
    description: 分析样本量

  - name: min_views_filter
    type: INTEGER
    description: 最小播放量筛选条件

  - name: topic_arbitrage
    type: JSON
    description: 话题套利分析结果

  - name: channel_arbitrage
    type: JSON
    description: 频道套利分析结果

  - name: duration_arbitrage
    type: JSON
    description: 时长套利分析结果

  - name: timing_arbitrage
    type: JSON
    description: 趋势套利分析结果

  - name: summary
    type: JSON
    description: 综合摘要

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

# 话题套利结果 (TopicArbitrageResult)
type: TopicArbitrageResult
description: 话题套利分析结果 (JSON 内嵌)

schema:
  network_stats:
    nodes: integer          # 关键词节点数
    edges: integer          # 边数
    density: float          # 网络密度

  bridge_topics:            # 桥梁话题列表
    - keyword: string       # 关键词
      betweenness: float    # 中介中心性
      degree: integer       # 程度中心性
      interestingness: float # 有趣度 = betweenness / degree
      connected_topics: string[] # 连接的话题

  insight: string           # 分析洞察

# 频道套利结果 (ChannelArbitrageResult)
type: ChannelArbitrageResult
description: 频道套利分析结果 (JSON 内嵌)

schema:
  small_channel_opportunities:  # 小频道爆款机会
    - channel: string
      subscriber_count: integer
      max_views: integer
      max_video_title: string
      max_video_id: string
      interestingness: float    # max_views / avg_views_in_category

  large_channel_baseline:
    avg_views: integer
    median_views: integer

  insight: string

# 时长套利结果 (DurationArbitrageResult)
type: DurationArbitrageResult
description: 时长套利分析结果 (JSON 内嵌)

schema:
  buckets:                      # 时长分桶
    - duration_range: string    # 如 "3-5分钟"
      min_seconds: integer
      max_seconds: integer
      video_count: integer
      supply_ratio: float       # 供给占比 (%)
      demand_ratio: float       # 需求占比 (播放量%)
      avg_views: integer
      interestingness: float    # demand / supply
      opportunity_level: string # high/medium/low

  optimal_duration: string      # 最优时长建议
  insight: string

# 趋势套利结果 (TimingArbitrageResult)
type: TimingArbitrageResult
description: 趋势套利分析结果 (JSON 内嵌)

schema:
  rising_topics:                # 上升话题
    - keyword: string
      recent_count: integer     # 近期出现次数
      historical_count: integer # 历史出现次数
      trend_ratio: float        # recent / historical

  falling_topics:               # 下降话题
    - keyword: string
      trend_ratio: float

  insight: string

# 博主画像 (CreatorProfile)
entity: CreatorProfile
description: 博主画像定位结果
table: creator_profiles

fields:
  - name: profile_id
    type: UUID
    primary_key: true

  - name: recommended_tier
    type: VARCHAR(20)
    enum: ["beginner", "mid_tier", "top_tier"]
    description: 推荐的博主类型

  - name: suitable_strategies
    type: JSON
    description: |
      适合的套利策略列表，如:
      - beginner: ["duration", "channel", "follow_up"]
      - mid_tier: ["topic", "timing"]
      - top_tier: ["cross_language", "timing", "topic"]

  - name: unsuitable_strategies
    type: JSON
    description: 不适合的策略

  - name: action_items
    type: JSON
    description: 具体行动建议列表

  - name: arbitrage_analysis_id
    type: UUID
    foreign_key: arbitrage_results.analysis_id
    description: 关联的套利分析结果

  - name: created_at
    type: DATETIME
    default: CURRENT_TIMESTAMP

# 策略矩阵参考
strategy_matrix:
  beginner:
    description: 小白博主 (< 1000 订阅)
    suitable:
      - duration: 发现时长空白区，低竞争切入
      - channel: 复制小频道爆款内容
      - follow_up: 蹭热门视频流量
    unsuitable:
      - cross_language: 资源要求高
      - topic: 需要深度理解市场

  mid_tier:
    description: 腰部博主 (1000-100k 订阅)
    suitable:
      - topic: 发现桥梁话题，建立差异化
      - timing: 提前布局上升趋势
    unsuitable:
      - channel: 已过复制阶段

  top_tier:
    description: 头部博主 (> 100k 订阅)
    suitable:
      - cross_language: 有资源做本地化
      - timing: 能承担趋势投资风险
      - topic: 引领新话题
    unsuitable:
      - follow_up: 有损品牌形象
```

---

## 6. 数据迁移

### 6.1 版本管理

```yaml
migrations:
  - version: "001"
    name: initial_schema
    description: 初始表结构
    file: migrations/001_initial_schema.sql

  - version: "002"
    name: add_analytics
    description: 添加数据分析表
    file: migrations/002_add_analytics.sql
    depends_on: ["001"]
```

### 6.2 迁移脚本模板

```sql
-- migrations/002_add_analytics.sql

-- Migration: 002_add_analytics
-- Description: 添加数据分析表

BEGIN TRANSACTION;

-- 创建 analytics 表
CREATE TABLE IF NOT EXISTS analytics (
    -- ... 字段定义
);

-- 记录迁移版本
INSERT INTO schema_versions (version, applied_at)
VALUES ('002', CURRENT_TIMESTAMP);

COMMIT;
```

---

## 7. 数据备份

### 7.1 备份策略

```yaml
backup:
  database:
    frequency: daily
    retention: 30 days
    path: backups/db/youtube_pipeline_{YYYYMMDD}.db

  files:
    frequency: weekly
    retention: 4 weeks
    include:
      - config/
      - specs/
      - scripts/
    exclude:
      - data/videos/  # 太大
      - logs/

  method:
    - sqlite3 db.sqlite ".backup 'backup.db'"
    - tar -czf backup.tar.gz <files>
```

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-18 | 初始版本 |
| 1.1 | 2026-01-19 | 新增套利分析数据模型 (ArbitrageResult, CreatorProfile) |
| 1.2 | 2026-01-19 | 新增数据分层架构 (Section 0)：原始数据与加工数据分离，五层模型，多维索引，增量采集 |

---

*引用本规格时使用：`.42cog/spec/dev/data.spec.md`*
