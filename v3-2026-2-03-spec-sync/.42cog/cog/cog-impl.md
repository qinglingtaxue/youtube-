---
name: cog-impl
description: 认知模型实现层 - API/CLI/脚本/代码映射
version: 1.0
created: 2026-02-04
parent: cog.md
---

# 认知模型实现层

> 本文档记录实体与代码实现的映射关系，供开发参考。
>
> 核心实体定义见：`cog.md`

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
