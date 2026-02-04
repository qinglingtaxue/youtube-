/**
 * 信息报告数据接口定义
 *
 * 定义 info-report-template.html 中 REPORT_DATA 的 TypeScript 类型。
 * 报告生成器负责将数据库实体转换为此接口格式，模板直接消费。
 *
 * 数据流向:
 *   MarketReport + OpportunityReport + PatternReport + ArbitrageReport
 *     → InfoReportDataBuilder.build()
 *       → InfoReportData (JSON)
 *         → info-report-template.html 渲染
 *
 * 参考:
 * - src/shared/schema.ts (实体定义)
 * - src/templates/charts/info-report-template.html (模板)
 * - .42cog/work/2026-02-04_design_信息报告页面.md (设计文档)
 */

import type {
  CreatorTier,
  PatternAnalysis,
  ArbitrageOpportunity,
  MarketReport,
  OpportunityReport,
  PatternReport,
} from "../shared/schema.ts";

// ============================================
// 信息报告顶层数据结构
// ============================================

/**
 * 信息报告完整数据
 * 对应模板中的 REPORT_DATA 对象
 */
export interface InfoReportData {
  // 数据基础
  sample_videos: number;
  sample_channels: number;
  time_span: string; // 如 "9年5月"
  insight_count: number;
  report_date: string; // ISO date "YYYY-MM-DD"

  // 市场健康度 (各维度 0-100)
  health: MarketHealthScores;
  health_grade: string; // "A+" | "A" | "B+" | "B" | "C+" | "C" | "D" | "F"
  health_desc: string;

  // 核心发现 (Top 5)
  insights: InsightItem[];

  // 机会排名 (Top 10, 按有趣度排序)
  opportunities: OpportunityItem[];

  // 创作者推荐 (分阶段)
  creator_recs: CreatorRecommendations;

  // 行动清单 (按优先级分组)
  actions: ActionGroups;

  // Google Trends 数据
  trends: TrendData;
}

// ============================================
// 子标签 1: 分析摘要
// ============================================

/**
 * 市场健康度 5 维评分
 *
 * 评分标准 (来自设计文档):
 * - competition: 竞争度，越低越好（意味着不被垄断）
 * - opportunity: 机会度，越高越好
 * - growth: 增长势，越高越好（市场还在增长）
 * - concentration: 集中度，越低越好（市场分散有利新人）
 * - freshness: 新鲜度，越高越好（活跃市场）
 */
export interface MarketHealthScores {
  competition: number; // 0-100, 低=好（取反后展示为"低竞争"）
  opportunity: number; // 0-100, 高=好
  growth: number; // 0-100, 高=好
  concentration: number; // 0-100, 低=好（取反后展示为"低集中"）
  freshness: number; // 0-100, 高=好
}

/**
 * 核心发现条目
 * 对应 InsightCard + ReasoningChain 实体
 */
export interface InsightItem {
  title: string;
  confidence: number; // 0-100
  badge: string; // 如 "反常识" | "可直接应用" | "跨语言套利" | "高优先级"
  steps: ReasoningStepItem[];
}

/**
 * 推理链步骤
 */
export interface ReasoningStepItem {
  icon: string; // emoji
  text: string;
  weight: string; // 如 "30%" | "结论"
}

// ============================================
// 子标签 2: 机会评估
// ============================================

/**
 * 机会排名条目
 */
export interface OpportunityItem {
  name: string;
  score: number; // 有趣度分数
  competition: "低" | "中" | "高";
  duration: "<4min" | "4-20min" | ">20min"; // YouTube 原生分档
  tag: string; // 如 "新手推荐" | ""
}

/**
 * 创作者推荐 (三阶段)
 */
export interface CreatorRecommendations {
  beginner: CreatorRecGroup;
  mid_tier: CreatorRecGroup;
  top_tier: CreatorRecGroup;
}

/**
 * 单阶段创作者推荐
 */
export interface CreatorRecGroup {
  title: string;
  items: CreatorRecItem[];
}

/**
 * 创作者推荐条目
 */
export interface CreatorRecItem {
  icon: string; // emoji
  name: string;
  desc: string;
}

// ============================================
// 子标签 3: 行动清单
// ============================================

/**
 * 行动清单分组 (P0/P1/P2)
 */
export interface ActionGroups {
  p0: ActionItem[]; // 立即行动（本周）
  p1: ActionItem[]; // 短期计划（两周内）
  p2: ActionItem[]; // 中期规划（一个月内）
}

/**
 * 行动项
 */
export interface ActionItem {
  text: string;
  meta: string; // 附加信息，如 "有趣度: 4.00 | 预估竞争: 低"
}

// ============================================
// 子标签 4: 趋势预警
// ============================================

/**
 * Google Trends 数据
 */
export interface TrendData {
  // 关键词时间序列
  keywords: Record<string, KeywordTrendSeries>;

  // 上升趋势话题
  rising: RisingTopic[];

  // 内容缺口
  content_gaps: ContentGap[];

  // 下降趋势
  declining: DecliningTopic[];
}

/**
 * 关键词趋势时间序列
 */
export interface KeywordTrendSeries {
  months: string[]; // ISO month "YYYY-MM"
  search_volume: number[]; // Google 搜索热度 (0-100)
  youtube_count: number[]; // YouTube 视频数量
}

/**
 * 上升趋势话题
 */
export interface RisingTopic {
  topic: string;
  trend_ratio: string; // 如 "+76%"
  status: "rising" | "exploding";
}

/**
 * 内容缺口
 * Google 上涨但 YouTube 还少 = 套利机会
 */
export interface ContentGap {
  topic: string;
  google_trend: string; // 如 "+76%"
  youtube_count: number;
}

/**
 * 下降趋势话题
 */
export interface DecliningTopic {
  topic: string;
  trend_ratio: string; // 如 "-32%"
  status: "declining";
  advice: string;
}

// ============================================
// 数据转换输入（从数据库实体来）
// ============================================

/**
 * 报告生成器的输入参数
 * 汇集各分析模块的输出
 */
export interface InfoReportInput {
  market_report: MarketReport;
  opportunity_report: OpportunityReport;
  pattern_report: PatternReport;
  arbitrage_opportunities: ArbitrageOpportunity[];
  trend_data?: TrendData;
  creator_tier?: CreatorTier;
}
