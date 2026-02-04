---
name: project-cog
description: YouTube 内容创作者运营平台的认知模型
version: 3.1
last_updated: 2026-02-04
---

# 认知模型 (Cog)

## 文档索引

> 认知模型已拆分为多个文档，按需阅读：

| 文档 | 内容 | 何时阅读 |
|-----|-----|---------|
| **cog.md**（本文档） | 核心索引、工作流实体、枚举定义 | 理解全局结构 |
| [cog-collect.md](cog-collect.md) | 数据采集实体与关系（6 个实体） | 开发采集功能时 |
| [cog-process.md](cog-process.md) | 数据加工实体与关系（19 个实体，数据→图表→报告） | 开发分析/可视化时 |
| [cog-impl.md](cog-impl.md) | API/CLI/脚本/代码映射 | 开发实现时 |
| [cog-data.md](cog-data.md) | 数据生命周期与存储策略 | 处理大规模数据时 |
| [cog-context.md](cog-context.md) | 业务/用户/技术背景 | 新人入门时 |

**相关 Skill 文档**：
- [ui-layout-design.skill.md](../skills/ui-layout-design.skill.md) - UI 布局设计
- [data-visualization.skill.md](../skills/data-visualization.skill.md) - 数据可视化图表选择

---

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

**数据采集层**（详见 [cog-collect.md](cog-collect.md)）
- CompetitorVideo：竞品视频，调研阶段数据采集的核心对象
- Channel：YouTube 频道，聚合分析的维度
- TrendSnapshot：趋势快照，追踪视频增长变化
- SearchPanel：搜索面板，关键词输入和筛选条件
- MonitorTask：监控任务，定时数据采集
- TrendingTracker：趋势追踪，增长数据监控

**数据加工层**（详见 [cog-process.md](cog-process.md)）
- 分析框架：ContentQuadrant（四象限）、DurationMatrix（时长矩阵）、ArbitrageFramework（套利框架）、PatternAnalysis（模式分析）
- 可视化：InsightCard（洞察卡片）、ConfidenceBar（置信度条）、ReasoningChain（推理链）、DataSourceTag（数据源标签）、ContentQuadrantChart、DurationDistributionChart、ChartCognitionMapping（图表认知映射）
- 套利：KeywordNetwork（关键词网络）、BridgeTopic（桥梁话题）、ArbitrageOpportunity（套利机会）、CreatorProfile（博主画像）
- 报告：AnalysisReport、MarketReport、OpportunityReport、ArbitrageReport、DiagnoseReport、PatternReport
- 导航：RankingList（榜单）、PatternDetail（模式详情）、LearningPath（学习路径）、CreatorDashboard（创作者仪表盘）

**工作流层**（本文档）
- Video：自有视频，贯穿 5 阶段工作流的核心实体
- Analytics：分析数据，复盘阶段的表现指标
- Task：任务，5 阶段工作流调度的核心单元
- TaskState：任务状态，API 层任务管理（内存/Redis）
- Script：脚本，策划阶段的文稿产出
- Spec：规约，内容规约定义
- Subtitle：字幕，制作阶段资源
- Thumbnail：缩略图，制作阶段资源
- WorkflowStage：工作流阶段定义
- Agent：代理，多层级编排
- Skill：技能，可复用能力单元
</cog>

---

## 工作流实体定义

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

## 工作流关系定义

<rel>

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

**任务调度关系**

| 关系 | 基数 | 说明 |
|------|------|------|
| Task → Video | 多对一 | 多个任务服务于同一视频 |
| Task → TaskState | 一对一 | API 层状态追踪 |
| Video → Script | 一对一 | 视频对应脚本 |
| Video → Spec | 一对一 | 视频对应规约 |
| Video → Analytics | 一对多 | 视频多个周期的分析数据 |

</rel>
