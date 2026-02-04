/**
 * 数据库 Schema 定义
 * YouTube 端到端内容创作流水线数据模型
 *
 * 参考文档：
 * - .42cog/cog/cog.md (认知模型)
 * - .42cog/spec/dev/sys.spec.md (系统架构)
 * - .42cog/spec/dev/data.spec.md (数据规约)
 *
 * 数据库选择：Neon PostgreSQL (Cloud) / SQLite (Local)
 * ORM: Prisma / Drizzle ORM
 */

// ==================== 基础类型定义 ====================

/**
 * 视频状态枚举
 * draft → scripting → producing → ready → published
 *            ↓
 *         scheduled
 */
export enum VideoStatus {
  DRAFT = "draft",
  SCRIPTING = "scripting",
  PRODUCING = "producing",
  READY = "ready",
  PUBLISHED = "published",
  SCHEDULED = "scheduled",
}

/**
 * 可见性枚举
 */
export enum Privacy {
  PUBLIC = "public",
  UNLISTED = "unlisted",
  PRIVATE = "private",
}

/**
 * 分辨率枚举
 */
export enum Resolution {
  RESOLUTION_720P = "720p",
  RESOLUTION_1080P = "1080p",
  RESOLUTION_4K = "4K",
}

/**
 * 工作流阶段枚举
 * research → planning → production → publishing → analytics
 */
export enum Stage {
  RESEARCH = "research",
  PLANNING = "planning",
  PRODUCTION = "production",
  PUBLISHING = "publishing",
  ANALYTICS = "analytics",
}

/**
 * 任务状态枚举
 * pending → running → completed
 *    ↓
 *  failed → (重试 ≤3 次)
 *    ↓
 * cancelled
 */
export enum TaskStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

/**
 * 任务类型枚举
 */
export enum TaskType {
  // 调研阶段
  COLLECT_VIDEOS = "collect_videos",
  ANALYZE_PATTERNS = "analyze_patterns",
  GENERATE_REPORT = "generate_report",

  // 策划阶段
  CREATE_SPEC = "create_spec",
  GENERATE_SCRIPT = "generate_script",
  SEO_ANALYSIS = "seo_analysis",

  // 制作阶段
  GENERATE_AUDIO = "generate_audio",
  CREATE_VIDEO = "create_video",
  GENERATE_SUBTITLE = "generate_subtitle",
  CREATE_THUMBNAIL = "create_thumbnail",

  // 发布阶段
  UPLOAD_VIDEO = "upload_video",
  UPLOAD_THUMBNAIL = "upload_thumbnail",
  UPLOAD_SUBTITLE = "upload_subtitle",
  SCHEDULE_PUBLISH = "schedule_publish",

  // 复盘阶段
  COLLECT_ANALYTICS = "collect_analytics",
  GENERATE_ANALYTICS_REPORT = "generate_analytics_report",
}

/**
 * 分析周期枚举
 */
export enum AnalyticsPeriod {
  PERIOD_7D = "7d",
  PERIOD_30D = "30d",
  LIFETIME = "lifetime",
}

/**
 * 内容风格枚举
 */
export enum ContentStyle {
  TUTORIAL = "tutorial",
  STORY = "story",
  REVIEW = "review",
  VLOG = "vlog",
  EXPLAINER = "explainer",
}

/**
 * 脚本状态枚举
 */
export enum ScriptStatus {
  DRAFT = "draft",
  REVIEWING = "reviewing",
  APPROVED = "approved",
  ARCHIVED = "archived",
}

/**
 * 字幕类型枚举
 */
export enum SubtitleType {
  AUTO = "auto",
  MANUAL = "manual",
  TRANSLATED = "translated",
}

/**
 * 字幕格式枚举
 */
export enum SubtitleFormat {
  SRT = "srt",
  VTT = "vtt",
  ASS = "ass",
}

/**
 * 四象限类型枚举
 * Star（爆款型）、Niche（粉丝向）、Viral（破圈型）、Dog（冷门型）
 */
export enum QuadrantType {
  STAR = "star",
  NICHE = "niche",
  VIRAL = "viral",
  DOG = "dog",
}

/**
 * 模式类型枚举
 */
export enum PatternType {
  COGNITIVE_IMPACT = "cognitive_impact",
  STORYTELLING = "storytelling",
  KNOWLEDGE_SHARING = "knowledge_sharing",
  INTERACTION_GUIDE = "interaction_guide",
  UNKNOWN = "unknown",
}

/**
 * 套利类型枚举
 */
export enum ArbitrageType {
  TOPIC = "topic",
  CHANNEL = "channel",
  DURATION = "duration",
  TIMING = "timing",
  CROSS_LANGUAGE = "cross_language",
  FOLLOW_UP = "follow_up",
}

/**
 * 博主类型枚举
 */
export enum CreatorTier {
  BEGINNER = "beginner",
  MID_TIER = "mid_tier",
  TOP_TIER = "top_tier",
}

// ==================== 主要实体 ====================

/**
 * 竞品视频
 * 调研阶段数据采集的核心对象
 */
export interface CompetitorVideo {
  id: string; // UUID
  youtube_id: string; // YouTube Video ID (unique)
  title: string;
  channel_id: string;
  channel_name: string;
  url: string;
  views: number;
  likes: number;
  comments: number;
  duration: number; // 秒
  published_at: Date;
  collected_at: Date;
  thumbnail_url?: string;

  // AI 检测
  is_ai_video?: boolean;
  ai_keyword?: string;

  // 计算属性（可选）
  days_since_publish?: number;
  daily_views?: number;
  time_bucket?: string;
  engagement_rate?: number; // (likes + comments) / views * 100
  quadrant?: QuadrantType;
  score?: string; // S/A/B/C
}

/**
 * YouTube 频道
 * 聚合分析的维度
 */
export interface Channel {
  id: string; // UUID
  channel_id: string; // YouTube Channel ID (unique)
  channel_name: string;
  subscriber_count: number;
  video_count: number;
  total_views: number;
  avg_views?: number;
  search_hit_count?: number; // 搜索命中的视频数
  has_real_stats?: boolean;

  // 计算属性（可选）
  efficiency_score?: number; // avg_views / subscriber_count
  is_dark_horse?: boolean; // 低粉高播放
}

/**
 * 用户
 * 存储用户账户和认证信息
 */
export interface User {
  id: string; // UUID
  email: string; // unique
  password_hash?: string; // OAuth 时可为空
  name?: string;
  avatar_url?: string;

  // OAuth
  provider?: string; // "google", "github", "email"
  provider_id?: string;

  created_at: Date;
  updated_at: Date;
  last_login?: Date;
}

/**
 * 自有视频
 * 贯穿 5 阶段工作流的核心实体
 */
export interface Video {
  id: string; // UUID
  user_id: string; // Foreign Key to User
  title: string;
  description?: string;

  // 状态管理
  status: VideoStatus;
  privacy: Privacy;
  duration?: number; // 秒
  resolution?: Resolution;

  // 关联 ID
  spec_id?: string; // Foreign Key to Spec
  script_id?: string; // Foreign Key to Script

  // 文件路径
  file_path?: string;

  // YouTube
  youtube_id?: string; // 发布后填充
  youtube_url?: string; // 计算属性

  // 发布时间
  created_at: Date;
  updated_at: Date;
  scheduled_at?: Date;
  published_at?: Date;

  // 计算属性（可选）
  engagement_rate?: number;
  is_ready_to_publish?: boolean;
}

/**
 * 规约 (Spec)
 * 视频制作的指导文档
 */
export interface Spec {
  id: string; // UUID
  video_id: string; // Foreign Key to Video
  title: string;
  target_audience?: string;
  content_style?: ContentStyle;
  key_points?: string[]; // JSON array
  reference_videos?: string[]; // YouTube IDs
  constraints?: Record<string, unknown>; // JSON object

  created_at: Date;
  updated_at: Date;
}

/**
 * 脚本 (Script)
 * 视频制作的文稿
 */
export interface Script {
  id: string; // UUID
  video_id: string; // Foreign Key to Video
  version: number;
  content: string; // Markdown
  word_count: number;
  estimated_duration?: number; // 秒
  status: ScriptStatus;

  created_at: Date;
  updated_at: Date;
}

/**
 * 字幕 (Subtitle)
 * 视频字幕文件
 */
export interface Subtitle {
  id: string; // UUID
  video_id: string; // Foreign Key to Video
  type: SubtitleType;
  format: SubtitleFormat;
  language: string; // ISO 639-1 code
  content: string; // 字幕内容
  file_path?: string;

  created_at: Date;
  updated_at: Date;
}

/**
 * 缩略图 (Thumbnail)
 * 视频封面
 */
export interface Thumbnail {
  id: string; // UUID
  video_id: string; // Foreign Key to Video
  file_path: string;
  width: number;
  height: number;
  created_at: Date;
}

/**
 * 分析数据 (Analytics)
 * 复盘阶段的表现指标
 */
export interface Analytics {
  id: string; // UUID
  video_id: string; // Foreign Key to Video
  period: AnalyticsPeriod;
  collected_at: Date;

  // 观看指标
  views: number;
  watch_time_minutes?: number;
  average_view_duration?: number; // 秒
  unique_viewers?: number;

  // 互动指标
  likes: number;
  dislikes?: number;
  comments: number;
  shares?: number;

  // 频道指标
  subscribers_gained?: number;
  subscribers_lost?: number;

  // 曝光指标
  impressions?: number;
  ctr?: number; // 点击率 (%)

  // 计算属性（可选）
  engagement_rate?: number;
  like_ratio?: number;
  subscriber_delta?: number;
  ctr_formatted?: string;
}

/**
 * 趋势快照 (TrendSnapshot)
 * 追踪视频增长变化
 */
export interface TrendSnapshot {
  id: string; // UUID
  video_id: string; // Foreign Key to CompetitorVideo
  snapshot_time: Date;
  views: number;
  likes?: number;
  comments?: number;
  growth?: number; // 与上次快照的增长差值
}

/**
 * 趋势聚合 (TrendAggregate)
 * 分层存储策略：压缩后的趋势数据
 */
export interface TrendAggregate {
  id: string; // UUID
  video_id: string; // Foreign Key to CompetitorVideo
  period_type: "daily" | "weekly" | "monthly";
  period_start: Date;
  period_end: Date;
  views_start: number;
  views_end: number;
  growth_total: number;
  growth_rate: number; // %
  snapshot_count: number;
}

/**
 * 任务 (Task)
 * 5 阶段工作流调度的核心单元
 */
export interface Task {
  id: string; // UUID
  stage: Stage;
  task_type: TaskType;
  status: TaskStatus;
  input_data?: Record<string, unknown>; // JSON
  output_data?: Record<string, unknown>; // JSON
  error_message?: string;
  max_retries: number;
  retry_count: number;
  started_at?: Date;
  completed_at?: Date;
  created_at: Date;
  updated_at: Date;

  // 计算属性（可选）
  duration_seconds?: number;
  can_retry?: boolean;
}

/**
 * 任务状态 (TaskState)
 * API 层任务状态管理（内存/Redis，生产应用）
 */
export interface TaskState {
  task_id: string; // Foreign Key to Task
  status: TaskStatus;
  progress: number; // 0-100
  message?: string;
  result?: Record<string, unknown>;
  error?: string;
  created_at: Date;
  updated_at: Date;
}

/**
 * 内容四象限 (ContentQuadrant)
 * 播放量×互动率的二维分类
 *
 * 说明：
 * - 不再在此表中存储 video_ids 数组（会导致 1MB+ 单条记录）
 * - 改用关联表 content_quadrant_membership 支持分页查询
 * - 使用 QuadrantOperations.getQuadrantVideos(quadrantId, {page, limit}) 分页获取视频
 *
 * 参考：src/db/migrations/002_fix_quadrant_structure.sql
 * 参考：src/db/quadrant-operations.ts
 */
export interface ContentQuadrant {
  id: string; // UUID
  quadrant_type: QuadrantType;
  views_threshold: number;
  engagement_threshold: number;
  // ❌ 已删除：video_ids?: string[];
  // ✅ 改用关联表 content_quadrant_membership（见迁移脚本）
  count?: number; // 该象限的视频总数（从关联表统计）
  percentage?: number; // 占比
}

/**
 * 内容四象限成员关联表 (ContentQuadrantMembership)
 * 用于存储象限与视频的多对多关系
 *
 * 替代 ContentQuadrant.video_ids 数组字段
 * 支持高效分页查询和灵活的成员管理
 */
export interface ContentQuadrantMembership {
  id: string; // UUID
  quadrant_id: string; // Foreign Key to ContentQuadrant
  video_id: string; // Foreign Key to CompetitorVideo
  created_at: Date;

  // 计算属性（可选）
  rank?: number; // 在象限中的排序位置（按播放量）
}

/**
 * 时长分布矩阵 (DurationMatrix)
 * 时长×平均播放的供需分析
 */
export interface DurationMatrix {
  id: string; // UUID
  label: string; // "0-1分钟", "1-3分钟" 等
  min_seconds: number;
  max_seconds: number;
  count: number;
  supply_percentage: number;
  total_views: number;
  avg_views: number;
  best_bucket?: boolean;
  opportunity_bucket?: boolean;
}

/**
 * 关键词网络 (KeywordNetwork)
 * 话题共现关系图
 */
export interface KeywordNetwork {
  id: string; // UUID
  nodes: KeywordNode[];
  edges: KeywordEdge[];
  network_stats?: {
    density: number;
    avg_clustering: number;
  };
}

/**
 * 关键词节点
 */
export interface KeywordNode {
  keyword: string;
  count: number;
  total_views: number;
  betweenness: number; // 中介中心性
  degree: number; // 程度中心性
  interestingness: number; // 有趣度
}

/**
 * 关键词边
 */
export interface KeywordEdge {
  source: string;
  target: string;
  weight: number; // 共现次数
}

/**
 * 桥梁话题 (BridgeTopic)
 * 能连接多个受众群体但传播不足的话题
 */
export interface BridgeTopic {
  keyword: string; // unique
  interestingness: number;
  betweenness: number;
  degree: number;
  video_count: number;
  total_views: number;
  connected_topics?: string[]; // 相连话题列表
}

/**
 * 博主画像 (CreatorProfile)
 * 博主类型和适合的套利策略
 */
export interface CreatorProfile {
  id: string; // UUID
  user_id: string; // Foreign Key to User
  creator_tier: CreatorTier;
  resources?: Record<string, unknown>;
  suitable_arbitrage?: ArbitrageType[];
  strategy?: string;
  created_at: Date;
  updated_at: Date;
}

/**
 * 套利机会 (ArbitrageOpportunity)
 * 具体可执行的创作方向
 */
export interface ArbitrageOpportunity {
  id: string; // UUID
  type: ArbitrageType;
  name: string;
  interestingness: number;
  value_score: number;
  spread_score: number;
  details?: Record<string, unknown>;
  recommendation?: string;
}

/**
 * 套利报告 (ArbitrageReport)
 * 综合套利分析结果
 */
export interface ArbitrageReport {
  id: string; // UUID
  generated_at: Date;
  sample_size: number;
  arbitrage_types: ArbitrageType[];
  opportunities: ArbitrageOpportunity[];
  summary?: string;
}

/**
 * 模式分析 (PatternAnalysis)
 * 多维度模式发现
 */
export interface PatternAnalysis {
  id: string; // UUID (P001-P042)
  dimension: string; // variable|temporal|spatial|channel|user
  finding: string;
  interestingness: number; // 1-5
  confidence: number; // 0-100
  sample_size: number;
  data_sources?: string[];
  action_items?: string[];
}

/**
 * 模式报告 (PatternReport)
 * 42 个模式的汇总报告
 */
export interface PatternReport {
  id: string; // UUID
  generated_at: Date;
  total_patterns: number;
  patterns_by_dimension?: Record<string, PatternAnalysis[]>;
  top_findings?: PatternAnalysis[];
  action_guide?: string;
  data_basis?: string;
}

/**
 * 学习路径 (LearningPath)
 * 42 个模式的导航结构
 */
export interface LearningPath {
  id: string; // UUID (singleton)
  blocks: LearningPathBlock[];
  stats?: {
    video_count: number;
    channel_count: number;
    total_views: number;
    time_span_days: number;
    insight_count: number;
  };
  quick_search?: boolean;
}

/**
 * 学习路径块
 */
export interface LearningPathBlock {
  title: string;
  description: string;
  pattern_count: number;
  sub_tabs: LearningPathSubTab[];
}

/**
 * 学习路径子标签
 */
export interface LearningPathSubTab {
  sub_title: string;
  pattern_ids: string[];
  deep_link: string;
}

/**
 * 分析报告 (AnalysisReport)
 * 综合数据洞察报告
 */
export interface AnalysisReport {
  id: string; // UUID
  generated_at: Date;
  topic: string;
  sample_size: number;
  time_range?: {
    start: Date;
    end: Date;
  };
  tabs?: string[];
  quadrant_data?: ContentQuadrant;
  duration_matrix?: DurationMatrix[];
  insights?: InsightCard[];
}

/**
 * 市场报告 (MarketReport)
 * 市场规模和竞争格局
 */
export interface MarketReport {
  id: string; // UUID
  generated_at: Date;
  market_size?: {
    sample_videos: number;
    total_views: number;
    avg_views: number;
    median_views: number;
  };
  channel_competition?: {
    total_channels: number;
    concentration?: {
      top10_share: number;
      top20_share: number;
    };
  };
  entry_barriers?: {
    performance_tiers: Record<string, number>;
    viral_rate: number;
    top_10_percent_threshold: number;
  };
}

/**
 * 机会报告 (OpportunityReport)
 * 创作机会识别
 */
export interface OpportunityReport {
  id: string; // UUID
  generated_at: Date;
  recent_viral?: {
    window: string;
    top_performers: CompetitorVideo[];
  }[];
  high_daily_growth?: CompetitorVideo[];
  small_channel_hits?: {
    count: number;
    videos: CompetitorVideo[];
  };
  opportunity_summary?: string;
}

/**
 * 诊断报告 (DiagnoseReport)
 * 频道健康度评估
 */
export interface DiagnoseReport {
  id: string; // UUID
  channel_name: string;
  channel_id: string;
  subscriber_count: number;
  video_count: number;
  total_views: number;
  scores?: {
    overall: string; // A-F
    content_quality: number;
    update_frequency: number;
    engagement: number;
  };
  strengths?: string[];
  weaknesses?: string[];
  recommendations?: string[];
  benchmark_channels?: Channel[];
}

/**
 * 洞察卡片 (InsightCard)
 * 可折叠展开的分析单元
 */
export interface InsightCard {
  id: string; // UUID
  category: "market" | "opportunity" | "warning";
  title: string;
  confidence: number; // 0-100
  sources?: string[];
  visualization?: string; // chart reference
  reasoning_chain?: ReasoningChain;
  findings?: string[];
  is_expanded?: boolean;
}

/**
 * 推理链 (ReasoningChain)
 * 展示 AI 得出结论的过程
 */
export interface ReasoningChain {
  id: string; // UUID
  steps: ReasoningStep[];
  conclusion: string;
  total_confidence: number;
}

/**
 * 推理步骤
 */
export interface ReasoningStep {
  icon: string;
  name: string;
  observation: string;
  weight: number; // 权重百分比
}

/**
 * 信息报告 (InformationReport)
 * 推理链式分析报告，汇总跨页数据的分析结论，指导用户决策
 *
 * 结构：
 * 1. 研究假设（来自全局筛选器）
 * 2. 结论链（4 张结论卡片）
 * 3. 综合结论（4 个关键点）
 * 4. 行动入口（导出 + 创作者行动中心）
 *
 * 参考：cog-process.md L536-720
 */
export interface InformationReport {
  id: string; // singleton UUID
  generated_at: Date;
  keyword: string; // 关键词（用于唯一标识）
  time_range: string; // "过去 3 个月"、"过去 7 天" 等

  // 四层结构
  hypothesis: ResearchHypothesis;
  conclusions: ConclusionCard[]; // 4 张卡片
  synthesized_conclusion: SynthesizedConclusion;
  action_gateway: ActionGateway;

  // 元数据
  sample_size: number; // 分析样本量（视频数）
  data_sources: string[]; // ["YouTube", "Google Trends"] 等
  confidence: number; // 整体置信度（0-100%）
}

/**
 * 研究假设
 * 来源：全局状态（用户在顶部全局筛选器改变时自动同步）
 */
export interface ResearchHypothesis {
  question: string; // 研究问题描述（1-2 句）
  keyword: string; // "养生"
  time_range: string; // "过去 3 个月"
  data_sources: string[]; // ["YouTube", "Google Trends"]
}

/**
 * 结论卡片
 * 每条报告包含 4 张卡片，对应：
 * ① 市场竞争分析
 * ② 内容缺口发现
 * ③ 最优时长分析
 * ④ 跨语言机会
 */
export interface ConclusionCard {
  id: string; // "1" | "2" | "3" | "4"
  title: string; // "市场竞争分散，新人有机会进入"（50 字以内）
  summary: string; // 一句话摘要（100 字以内）
  confidence: number; // 置信度 (75-88%)
  tags: string[]; // 数据源标签 + 模式标签
  reasoning_steps: ReasoningStep[]; // 推理步骤列表
  embedded_charts?: {
    chart_type: string; // "bar" | "line" | "scatter" | "network" 等
    chart_name: string; // "频道集中度" | "时长分布" 等
    data_source: string; // 页面和 Tab 来源
  }[];
  is_expanded: boolean; // 初始：①=true, ②③④=false
}

/**
 * 综合结论
 */
export interface SynthesizedConclusion {
  main_text: string; // 综合结论主文案（1-2 句）
  // 例：「养生」赛道新创作者的首选策略：切入内容缺口话题，
  //   采用 4-20 分钟中视频格式，快速测试市场反应。

  key_points: string[]; // 关键点列表（4 项，对应 ①②③④）
  // 例：[
  //   "市场竞争分散（Top 10 占 23%），新人有生存空间",
  //   "「穴位按摩」等话题有明确的内容缺口和需求",
  //   "中视频 (4-20min) 平均播放量最高（8.2 万）",
  //   "Tai Chi 等英文热词可通过翻译内容快速变现"
  // ]
}

/**
 * 行动入口
 */
export interface ActionGateway {
  export_enabled: boolean; // 是否可导出
  export_format?: "markdown" | "pdf"; // 导出格式（默认 markdown）
  action_center_link?: string; // 创作者行动中心链接
  // 例："/creator-action-center.html?keyword=养生"
}

/**
 * 数据源标签
 * 用于追踪结论的数据来源
 */
export interface DataSourceTag {
  icon: string; // "📊" | "📈" | "🔍" 等
  source_page: string; // "全局认识" | "套利分析" | "Google Trends"
  source_tab?: string; // "市场规模" | "有趣度排名"
  source_chart?: string; // "频道集中度图" | "视频有趣度榜"
  color?: string; // "blue" | "green" | "orange" 等
}

/**
 * 监控任务 (MonitorTask)
 * 定时数据采集任务
 */
export interface MonitorTask {
  id: string; // UUID
  user_id: string; // Foreign Key to User
  keyword: string;
  interval: number; // 分钟
  last_run?: Date;
  next_run?: Date;
  status: TaskStatus;
  video_count?: number;
  created_at: Date;
  updated_at: Date;
}

/**
 * 趋势追踪 (TrendingTracker)
 * 监控任务的结果呈现
 */
export interface TrendingTracker {
  id: string; // UUID
  task_id: string; // Foreign Key to MonitorTask
  keyword: string;
  last_update_time: Date;
  trend_data?: {
    period: "24h" | "7d" | "30d";
    snapshots: TrendSnapshot[];
    total_views_delta: number;
    avg_daily_growth: number;
    top_growing_videos?: CompetitorVideo[];
  };
  alert_status?: boolean;
}

/**
 * 搜索面板 (SearchPanel)
 * 关键词输入和筛选条件
 */
export interface SearchPanel {
  topic: string;
  filters?: {
    views_min?: number;
    views_max?: number;
    regions?: string[];
    duration?: string;
    subscribers?: {
      min: number;
      max: number;
    };
    time_range?: string;
    sort_by?: string;
    ai_filter?: boolean;
  };
  presets?: string[];
}

/**
 * 排行榜列表 (RankingList)
 * 视频/频道排行
 */
export interface RankingList {
  list_type: string; // hot|recentHits|evergreen|potential|longform
  items: (CompetitorVideo | Channel)[];
  total_count: number;
  current_page: number;
  time_filter?: number;
}

// ==================== 数据库配置 ====================

/**
 * Neon PostgreSQL 连接配置
 * 适用于生产环境
 */
export interface NeonConfig {
  connection_string: string;
  pool_size?: number;
  ssl?: boolean;
  application_name?: string;
}

/**
 * SQLite 本地配置
 * 适用于开发环境
 */
export interface SQLiteConfig {
  database_path: string;
  journal_mode?: "WAL" | "DELETE";
  foreign_keys?: boolean;
}

/**
 * 数据库配置
 */
export interface DatabaseConfig {
  type: "postgresql" | "sqlite";
  neon?: NeonConfig;
  sqlite?: SQLiteConfig;
}

// ==================== 导出类型 ====================

export type {
  CompetitorVideo,
  Channel,
  User,
  Video,
  Spec,
  Script,
  Subtitle,
  Thumbnail,
  Analytics,
  TrendSnapshot,
  TrendAggregate,
  Task,
  TaskState,
  ContentQuadrant,
  ContentQuadrantMembership,
  DurationMatrix,
  KeywordNetwork,
  KeywordNode,
  KeywordEdge,
  BridgeTopic,
  CreatorProfile,
  ArbitrageOpportunity,
  ArbitrageReport,
  PatternAnalysis,
  PatternReport,
  LearningPath,
  LearningPathBlock,
  LearningPathSubTab,
  AnalysisReport,
  MarketReport,
  OpportunityReport,
  DiagnoseReport,
  InsightCard,
  ReasoningChain,
  ReasoningStep,
  InformationReport,
  ResearchHypothesis,
  ConclusionCard,
  SynthesizedConclusion,
  ActionGateway,
  DataSourceTag,
  MonitorTask,
  TrendingTracker,
  SearchPanel,
  RankingList,
};
