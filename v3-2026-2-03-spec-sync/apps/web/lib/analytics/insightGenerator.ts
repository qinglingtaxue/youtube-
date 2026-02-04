/**
 * 洞察生成模块
 * 基于中心性数据生成套利分析的洞察文案
 */

export interface VideoWithMetrics {
  id: string
  title: string
  views: number
  likes: number
  comments: number
  channelName: string
  channelSubscribers: number
  publishedAt: string

  // 中心性指标
  betweenness?: number
  closeness?: number
  interestingness?: number
}

export interface ArbitrageInsight {
  trend: string // 趋势描述
  topInterestingVideos: VideoWithMetrics[] // Top 3 有趣度视频
  conclusion: string // 结论
  recommendation: string // 推荐行动
}

/**
 * 洞察生成器
 */
export class InsightGenerator {
  /**
   * 生成蓝海市场识别
   */
  generateBlueSeaInsight(topVideos: VideoWithMetrics[]): ArbitrageInsight {
    if (topVideos.length === 0) {
      return {
        trend: '数据不足',
        topInterestingVideos: [],
        conclusion: '无法生成洞察',
        recommendation: '请增加数据采集',
      }
    }

    const smallChannelVideos = topVideos.filter(
      (v) => (v.channelSubscribers || 0) < 100000
    )
    const avgChannelSize =
      topVideos.reduce((sum, v) => sum + (v.channelSubscribers || 0), 0) /
      topVideos.length

    const trend =
      smallChannelVideos.length > topVideos.length * 0.5
        ? '蓝海市场确认'
        : '竞争市场'

    const conclusion =
      smallChannelVideos.length > 0
        ? `Top ${topVideos.length} 高有趣度视频中有 ${smallChannelVideos.length} 条来自小频道（<10w 订阅者），这表明该话题存在 **低订阅高价值的蓝海机会**。这些小频道通过优质内容突破了大号的垄断。`
        : `当前市场竞争格局由大号主导。小频道需要通过创新角度和更高质量的内容才能突破。`

    const recommendation =
      smallChannelVideos.length > 0
        ? `
1. **学习蓝海视频策略**：分析这些高有趣度小频道视频的标题、时长、制作工艺
2. **找准细分角度**：这些视频覆盖了什么"未被充分开发"的子话题？
3. **快速迭代**：小频道的成功往往靠"快、精、新"，而非大投入
        `.trim()
        : `
1. **等待市场洗牌**：观察大号是否有内容空白
2. **专业化定位**：找一个非常细的垂直领域，大号不会深入
3. **质量为王**：在制作工艺上超越现有视频
        `.trim()

    return {
      trend,
      topInterestingVideos: topVideos.slice(0, 3),
      conclusion,
      recommendation,
    }
  }

  /**
   * 生成增长机会分析
   */
  generateGrowthOpportunity(videos: VideoWithMetrics[]): ArbitrageInsight {
    const lastWeekVideos = videos.slice(0, Math.ceil(videos.length * 0.25))
    const avgViewsRecent =
      lastWeekVideos.reduce((sum, v) => sum + v.views, 0) /
      (lastWeekVideos.length || 1)
    const avgViewsAll =
      videos.reduce((sum, v) => sum + v.views, 0) / (videos.length || 1)

    const growthTrend =
      avgViewsRecent > avgViewsAll ? '上升趋势' : '下降趋势'

    const conclusion =
      avgViewsRecent > avgViewsAll
        ? `最近新发布的内容播放量 **${Math.round(avgViewsRecent / 10000) * 10000}** 次，相比历史平均 **${Math.round(avgViewsAll / 10000) * 10000}** 次，显示该话题正处于 **增长期**。`
        : `最近新发布的内容播放量 **${Math.round(avgViewsRecent / 10000) * 10000}** 次，相比历史平均 **${Math.round(avgViewsAll / 10000) * 10000}** 次，显示该话题可能进入 **成熟或衰退期**。`

    return {
      trend: growthTrend,
      topInterestingVideos: lastWeekVideos.slice(0, 3),
      conclusion,
      recommendation:
        growthTrend === '上升趋势'
          ? '赶上增长潮，现在进入此领域的窗口期还在开放'
          : '谨慎进入，考虑创新角度或等待下一波热点',
    }
  }

  /**
   * 生成竞争对标分析
   */
  generateCompetitionAnalysis(
    topChannels: Array<{ name: string; views: number; subscribers: number }>
  ): ArbitrageInsight {
    if (topChannels.length === 0) {
      return {
        trend: '数据不足',
        topInterestingVideos: [],
        conclusion: '无法进行竞争分析',
        recommendation: '请先获取频道数据',
      }
    }

    const totalViews = topChannels.reduce((sum, c) => sum + c.views, 0)
    const top3Concentration =
      (topChannels
        .slice(0, 3)
        .reduce((sum, c) => sum + c.views, 0) /
        totalViews) *
      100

    const concentration =
      top3Concentration > 60 ? '高度集中' : top3Concentration > 40 ? '中等集中' : '相对分散'

    return {
      trend: concentration,
      topInterestingVideos: [],
      conclusion: `该话题的内容生产呈现 **${concentration}** 格局。Top 3 频道占总播放量的 **${Math.round(top3Concentration)}%**。${
        top3Concentration > 60
          ? '大号垄断显著，小号破局困难。'
          : '市场竞争相对均匀，机会相对平等。'
      }`,
      recommendation: `${
        top3Concentration > 60
          ? '需要找到大号忽视的细分领域'
          : '只要质量足够好，就有机会获得曝光'
      }`,
    }
  }

  /**
   * 生成内容多样性分析
   */
  generateDiversityAnalysis(videos: VideoWithMetrics[]): string {
    const uniqueChannels = new Set(videos.map((v) => v.channelName)).size
    const avgViewsPerChannel =
      videos.reduce((sum, v) => sum + v.views, 0) / (uniqueChannels || 1)

    if (uniqueChannels < 5) {
      return `内容高度集中：仅 ${uniqueChannels} 个频道。建议寻找被忽视的视角。`
    } else if (uniqueChannels < 15) {
      return `内容相对多元：来自 ${uniqueChannels} 个频道。仍有专业细分机会。`
    } else {
      return `内容充分多元：来自 ${uniqueChannels} 个频道。强调创新和差异化很关键。`
    }
  }

  /**
   * 生成时间窗口分析
   */
  generateTimeWindowInsight(
    videos: VideoWithMetrics[]
  ): {
    window: string
    reason: string
  } {
    if (videos.length === 0) {
      return {
        window: '无数据',
        reason: '请增加数据采集',
      }
    }

    // 简化：基于视频发布时间分布
    const now = Date.now()
    const videoAges = videos.map(
      (v) => (now - new Date(v.publishedAt).getTime()) / (1000 * 60 * 60 * 24)
    )
    const avgAge = videoAges.reduce((sum, a) => sum + a, 0) / videoAges.length

    let window = '观察期'
    let reason = '数据收集中，请稍候'

    if (avgAge < 3) {
      window = '黄金期'
      reason = '新鲜内容，处于算法推荐的最佳时段'
    } else if (avgAge < 7) {
      window = '活跃期'
      reason = '1 周内的内容仍在获得主要流量'
    } else if (avgAge < 30) {
      window = '衰退期'
      reason = '超过 1 周的内容逐渐失去推荐优先级'
    } else {
      window = '长尾期'
      reason = '需要打造常青内容才能持续获得搜索流量'
    }

    return { window, reason }
  }
}
