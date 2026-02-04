/**
 * 信息报告生成器
 *
 * 职责:
 * 1. 将分析模块输出的数据库实体转换为 InfoReportData
 * 2. 读取 HTML 模板，注入真实数据
 * 3. 输出可直接在浏览器中打开的 HTML 文件
 *
 * CLI 命令: bun run report:info
 * API 端点: GET /api/report/info
 *
 * 参考:
 * - src/report/info-report-data.ts (数据接口)
 * - src/templates/charts/info-report-template.html (HTML 模板)
 * - .42cog/cog/cog-impl.md (CLI/API 映射)
 */

import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import type {
  MarketReport,
  OpportunityReport,
  PatternReport,
  PatternAnalysis,
  ArbitrageOpportunity,
} from "../shared/schema.ts";

import type {
  InfoReportData,
  InfoReportInput,
  MarketHealthScores,
  InsightItem,
  OpportunityItem,
  ActionGroups,
  CreatorRecommendations,
  TrendData,
} from "./info-report-data.ts";

// ============================================
// 报告生成器
// ============================================

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const TEMPLATE_PATH = resolve(
  __dirname,
  "../templates/charts/info-report-template.html",
);

/**
 * 信息报告生成器
 *
 * 使用方法:
 * ```ts
 * const generator = new InfoReportGenerator();
 * const data = generator.buildReportData(input);
 * const html = generator.renderHTML(data);
 * generator.saveToFile(html, "./output/info-report.html");
 * ```
 */
export class InfoReportGenerator {
  private templateHTML: string;

  constructor() {
    this.templateHTML = readFileSync(TEMPLATE_PATH, "utf-8");
  }

  /**
   * 从分析模块输出构建报告数据
   */
  buildReportData(input: InfoReportInput): InfoReportData {
    const health = this.calculateHealthScores(
      input.market_report,
      input.opportunity_report,
    );
    const grade = this.calculateHealthGrade(health);

    return {
      // 数据基础
      sample_videos: input.market_report.market_size?.sample_videos ?? 0,
      sample_channels:
        input.market_report.channel_competition?.total_channels ?? 0,
      time_span: this.calculateTimeSpan(input.market_report),
      insight_count: input.pattern_report.total_patterns,
      report_date: new Date().toISOString().split("T")[0],

      // 市场健康度
      health,
      health_grade: grade.grade,
      health_desc: grade.desc,

      // 核心发现
      insights: this.transformInsights(input.pattern_report),

      // 机会排名
      opportunities: this.transformOpportunities(
        input.arbitrage_opportunities,
      ),

      // 创作者推荐
      creator_recs: this.buildCreatorRecommendations(
        input.arbitrage_opportunities,
      ),

      // 行动清单
      actions: this.buildActionItems(input.arbitrage_opportunities),

      // Google Trends
      trends: input.trend_data ?? this.getEmptyTrendData(),
    };
  }

  /**
   * 将数据注入 HTML 模板，生成完整报告
   */
  renderHTML(data: InfoReportData): string {
    // 替换模板中的 REPORT_DATA 示例数据
    const dataJSON = JSON.stringify(data, null, 8);
    const rendered = this.templateHTML.replace(
      /const REPORT_DATA = \{[\s\S]*?\n        \};/,
      `const REPORT_DATA = ${dataJSON};`,
    );
    return rendered;
  }

  /**
   * 保存 HTML 到文件
   */
  saveToFile(html: string, outputPath: string): void {
    writeFileSync(outputPath, html, "utf-8");
  }

  /**
   * 一键生成: 构建数据 → 渲染 HTML → 保存文件
   */
  generate(input: InfoReportInput, outputPath: string): InfoReportData {
    const data = this.buildReportData(input);
    const html = this.renderHTML(data);
    this.saveToFile(html, outputPath);
    return data;
  }

  // ============================================
  // 数据转换: 市场健康度
  // ============================================

  /**
   * 从 MarketReport + OpportunityReport 计算 5 维健康评分
   *
   * 评分维度 (0-100):
   * - competition: Top10 集中度 → 越低越好
   * - opportunity: 套利机会密度 → 越高越好
   * - growth: 近期视频增长率 → 越高越好
   * - concentration: 频道集中度 → 越低越好
   * - freshness: 近期视频占比 → 越高越好
   */
  private calculateHealthScores(
    market: MarketReport,
    opportunity: OpportunityReport,
  ): MarketHealthScores {
    const top10Share =
      market.channel_competition?.concentration?.top10_share ?? 50;
    const totalChannels =
      market.channel_competition?.total_channels ?? 1;
    const viralRate = market.entry_barriers?.viral_rate ?? 5;

    // 竞争度: Top10 播放量占比，直接作为竞争分数
    const competition = Math.min(100, Math.round(top10Share));

    // 机会度: 基于爆款率和小频道黑马数
    const smallChannelCount =
      opportunity.small_channel_hits?.count ?? 0;
    const opportunityScore = Math.min(
      100,
      Math.round(viralRate * 5 + smallChannelCount * 2),
    );

    // 增长势: 基于近期高增长视频数
    const highGrowthCount =
      opportunity.high_daily_growth?.length ?? 0;
    const growthScore = Math.min(100, Math.round(highGrowthCount * 5 + 30));

    // 集中度: 频道数量的倒数（频道越多越分散）
    const concentrationScore = Math.min(
      100,
      Math.round((1 - Math.min(totalChannels, 500) / 500) * 100),
    );

    // 新鲜度: 基于最近时间窗口的爆款数
    const recentViral = opportunity.recent_viral ?? [];
    const recentCount = recentViral.reduce(
      (sum, w) => sum + (w.top_performers?.length ?? 0),
      0,
    );
    const freshnessScore = Math.min(100, Math.round(recentCount * 3 + 40));

    return {
      competition,
      opportunity: opportunityScore,
      growth: growthScore,
      concentration: concentrationScore,
      freshness: freshnessScore,
    };
  }

  /**
   * 从健康评分计算综合评级
   */
  private calculateHealthGrade(
    scores: MarketHealthScores,
  ): { grade: string; desc: string } {
    // 综合分 = 正面指标平均 - 负面指标影响
    const positiveAvg =
      (scores.opportunity + scores.growth + scores.freshness) / 3;
    const negativeAvg = (scores.competition + scores.concentration) / 2;
    const composite = positiveAvg - negativeAvg * 0.3;

    const gradeTable: Array<{
      min: number;
      grade: string;
      desc: string;
    }> = [
      { min: 80, grade: "A+", desc: "极佳市场，机会丰富竞争温和" },
      { min: 70, grade: "A", desc: "优质市场，多个套利空间" },
      { min: 60, grade: "B+", desc: "机会充足但竞争加剧" },
      { min: 50, grade: "B", desc: "中等市场，需精准定位" },
      { min: 40, grade: "C+", desc: "竞争激烈，寻找细分" },
      { min: 30, grade: "C", desc: "红海市场，门槛较高" },
      { min: 20, grade: "D", desc: "饱和市场，谨慎进入" },
      { min: 0, grade: "F", desc: "不建议进入" },
    ];

    const result = gradeTable.find((g) => composite >= g.min) ?? gradeTable[gradeTable.length - 1];
    return { grade: result.grade, desc: result.desc };
  }

  // ============================================
  // 数据转换: 核心发现
  // ============================================

  /**
   * 将 PatternReport 的 top_findings 转换为 InsightItem[]
   */
  private transformInsights(report: PatternReport): InsightItem[] {
    const findings = report.top_findings ?? [];

    return findings.slice(0, 5).map((pattern) => ({
      title: pattern.finding,
      confidence: pattern.confidence,
      badge: this.getInsightBadge(pattern),
      steps: this.buildReasoningSteps(pattern),
    }));
  }

  /**
   * 根据模式特征生成 badge
   */
  private getInsightBadge(pattern: PatternAnalysis): string {
    if (pattern.interestingness >= 4.5) return "高优先级";
    if (pattern.dimension === "spatial") return "跨语言套利";
    if (pattern.interestingness >= 4.0) return "可直接应用";
    if (pattern.confidence >= 85) return "高置信度";
    return "反常识";
  }

  /**
   * 从模式数据构建推理链步骤
   */
  private buildReasoningSteps(
    pattern: PatternAnalysis,
  ): InsightItem["steps"] {
    const sources = pattern.data_sources ?? [];
    const actions = pattern.action_items ?? [];

    const steps: InsightItem["steps"] = [];

    // 数据观察步骤
    if (sources.length > 0) {
      steps.push({
        icon: "📊",
        text: `${pattern.sample_size} 条数据样本分析（${sources.join("、")}）`,
        weight: "40%",
      });
    }

    // 分析发现步骤
    steps.push({
      icon: "📈",
      text: pattern.finding,
      weight: sources.length > 0 ? "40%" : "60%",
    });

    // 结论/建议步骤
    if (actions.length > 0) {
      steps.push({
        icon: "✅",
        text: actions[0],
        weight: "结论",
      });
    }

    return steps;
  }

  // ============================================
  // 数据转换: 机会排名
  // ============================================

  /**
   * 将 ArbitrageOpportunity[] 转换为 OpportunityItem[]
   */
  private transformOpportunities(
    opportunities: ArbitrageOpportunity[],
  ): OpportunityItem[] {
    return opportunities
      .sort((a, b) => b.interestingness - a.interestingness)
      .slice(0, 10)
      .map((opp) => ({
        name: opp.name,
        score: Number(opp.interestingness.toFixed(2)),
        competition: this.getCompetitionLevel(opp.spread_score),
        duration: this.inferDuration(opp),
        tag: this.getOpportunityTag(opp),
      }));
  }

  private getCompetitionLevel(
    spreadScore: number,
  ): "低" | "中" | "高" {
    if (spreadScore < 0.3) return "低";
    if (spreadScore < 0.6) return "中";
    return "高";
  }

  private inferDuration(opp: ArbitrageOpportunity): OpportunityItem["duration"] {
    const details = opp.details as Record<string, unknown> | undefined;
    const duration = details?.recommended_duration as string | undefined;
    if (duration === "<4min" || duration === "4-20min" || duration === ">20min") {
      return duration;
    }
    return "4-20min"; // 默认推荐中视频
  }

  private getOpportunityTag(opp: ArbitrageOpportunity): string {
    // 低竞争 + 高有趣度 = 新手推荐
    if (opp.spread_score < 0.3 && opp.interestingness > 1.0) {
      return "新手推荐";
    }
    return "";
  }

  // ============================================
  // 数据转换: 创作者推荐
  // ============================================

  /**
   * 基于套利机会生成分阶段创作者推荐
   * 推荐策略来自 cog-process.md CreatorProfile 定义
   */
  private buildCreatorRecommendations(
    opportunities: ArbitrageOpportunity[],
  ): CreatorRecommendations {
    const topTopic = opportunities
      .filter((o) => o.type === "topic")
      .sort((a, b) => b.interestingness - a.interestingness)[0];

    const topChannel = opportunities
      .filter((o) => o.type === "channel")
      .sort((a, b) => b.interestingness - a.interestingness)[0];

    return {
      beginner: {
        title: "🌱 新手创作者策略",
        items: [
          {
            icon: "🦄",
            name: "话题套利",
            desc: topTopic
              ? `找供给不足的细分话题，如「${topTopic.name}」`
              : "找供给不足的细分话题",
          },
          {
            icon: "🦄",
            name: "频道套利",
            desc: topChannel
              ? `模仿「${topChannel.name}」等小频道的爆款结构`
              : "模仿小频道爆款视频的选题和结构",
          },
          {
            icon: "⏱️",
            name: "时长套利",
            desc: "优先做 4-20 分钟中视频",
          },
        ],
      },
      mid_tier: {
        title: "🚀 成长期创作者策略",
        items: [
          {
            icon: "🌉",
            name: "桥梁话题",
            desc: "连接两个受众群体，如「养生+运动」",
          },
          {
            icon: "📈",
            name: "趋势套利",
            desc: "跟进上升趋势话题，如 Google Trends 上升词",
          },
          {
            icon: "🔄",
            name: "跟进套利",
            desc: "在爆款视频后 72 小时内快速跟进",
          },
        ],
      },
      top_tier: {
        title: "👑 成熟期创作者策略",
        items: [
          {
            icon: "🌍",
            name: "跨语言套利",
            desc: "将热门中文内容翻译到英文市场",
          },
          {
            icon: "📈",
            name: "趋势套利",
            desc: "早期布局新趋势，建立先发优势",
          },
          {
            icon: "📢",
            name: "品牌合作",
            desc: "利用频道影响力获取品牌赞助",
          },
        ],
      },
    };
  }

  // ============================================
  // 数据转换: 行动清单
  // ============================================

  /**
   * 从套利机会生成分优先级行动清单
   */
  private buildActionItems(
    opportunities: ArbitrageOpportunity[],
  ): ActionGroups {
    const sorted = opportunities
      .sort((a, b) => b.interestingness - a.interestingness);

    const top3 = sorted.slice(0, 3);
    const mid3 = sorted.slice(3, 6);

    return {
      p0: top3.map((opp) => ({
        text: `搜索「${opp.name}」，分析 Top 10 视频的标题和封面`,
        meta: `有趣度: ${opp.interestingness.toFixed(2)} | 预估竞争: ${this.getCompetitionLevel(opp.spread_score)} | 推荐时长: ${this.inferDuration(opp)}`,
      })),
      p1: [
        ...mid3.map((opp) => ({
          text: `对比「${opp.name}」领域的 3 个标杆频道内容策略`,
          meta: `有趣度: ${opp.interestingness.toFixed(2)} | 预估竞争: ${this.getCompetitionLevel(opp.spread_score)}`,
        })),
        {
          text: "建立 YouTube 搜索建议关键词库（≥20 个关键词）",
          meta: "方法: 从 Google Trends 上升话题中筛选",
        },
      ],
      p2: [
        {
          text: "完成 5 个视频的制作和发布",
          meta: "按机会优先级从高到低选题",
        },
        {
          text: "分析自有频道数据，与基线对比",
          meta: "指标: 播放量、点赞率、评论数",
        },
        {
          text: "识别个人最佳内容类型和时长",
          meta: "基于发布后 7 天的数据",
        },
        {
          text: "建立定期采集和分析流程",
          meta: "建议: 每周采集 500 条新数据",
        },
      ],
    };
  }

  // ============================================
  // 辅助方法
  // ============================================

  private calculateTimeSpan(_market: MarketReport): string {
    // 从 market_report 的时间范围计算跨度
    // 实际实现时从 time_range 字段计算
    return "数据待计算";
  }

  private getEmptyTrendData(): TrendData {
    return {
      keywords: {},
      rising: [],
      content_gaps: [],
      declining: [],
    };
  }
}

// ============================================
// 便捷函数
// ============================================

/**
 * 一键生成信息报告
 *
 * @param input 分析模块输出数据
 * @param outputPath 输出 HTML 文件路径
 * @returns 报告数据对象
 */
export function generateInfoReport(
  input: InfoReportInput,
  outputPath: string,
): InfoReportData {
  const generator = new InfoReportGenerator();
  return generator.generate(input, outputPath);
}

/**
 * 仅构建报告数据（不渲染 HTML）
 * 用于 API 返回 JSON
 */
export function buildInfoReportData(
  input: InfoReportInput,
): InfoReportData {
  const generator = new InfoReportGenerator();
  return generator.buildReportData(input);
}
