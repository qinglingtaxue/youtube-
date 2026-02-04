---
name: cog-collect
description: 认知模型 - 数据采集层（数据从哪来）
version: 1.0
created: 2026-02-04
parent: cog.md
---

# 认知模型 - 数据采集层

> 本文档定义数据采集阶段的所有实体和关系。
>
> 核心问题：**数据从哪来？怎么采集？采集得到什么？**
>
> 总览索引见 `cog.md` | 数据加工见 `cog-process.md` | 存储策略见 `cog-data.md`

---

## 采集核心实体

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

## 采集交互实体

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

---

## 采集关系定义

<rel>

| 关系 | 基数 | 说明 |
|------|------|------|
| SearchPanel → CompetitorVideo | 一对多 | 一次搜索产生多条视频数据 |
| CompetitorVideo → Channel | 多对一 | 多个视频属于同一频道 |
| CompetitorVideo → TrendSnapshot | 一对多 | 一个视频有多个时间点快照 |
| MonitorTask → CompetitorVideo | 一对多 | 一个监控任务采集多条视频 |
| MonitorTask → TrendingTracker | 一对一 | 一个任务配置对应一个结果展示 |
| TrendingTracker → TrendSnapshot | 多对多 | 一个趋势展示聚合多个视频的多个快照 |

**采集流程**

```
用户输入关键词
    ↓
SearchPanel（筛选条件）
    ↓
API 数据采集（yt-dlp）
    ↓
CompetitorVideo + Channel（原始数据入库）
    ↓
MonitorTask（可选：定时持续采集）
    ↓
TrendSnapshot（可选：增长快照）
    ↓
TrendingTracker（可选：趋势展示）
```

</rel>
