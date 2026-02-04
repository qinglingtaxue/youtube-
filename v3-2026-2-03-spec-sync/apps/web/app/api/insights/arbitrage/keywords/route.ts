import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/insights/arbitrage/keywords
 * 获取关键词维度的套利分析数据
 *
 * 查询参数：
 * - timeRange: 时间范围（7d, 30d, 90d, all）
 * - rankingType: 排序类型（interestingness, betweenness, closeness）
 * - limit: 返回数量（默认 50）
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const timeRange = searchParams.get('timeRange') || '7d'
    const rankingType = searchParams.get('rankingType') || 'interestingness'
    const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 100)

    // TODO: 从后端 API 获取真实数据
    // const backendRes = await fetch(
    //   `${process.env.BACKEND_API_URL}/api/insights/arbitrage/keywords?timeRange=${timeRange}&rankingType=${rankingType}&limit=${limit}`
    // )

    // Mock 数据：生成关键词维度的有趣度排行
    const mockKeywords = Array.from({ length: limit }, (_, i) => {
      const totalVideos = Math.floor(Math.random() * 1000) + 50
      const totalViews = Math.floor(Math.random() * 100000000) + 1000000
      const degree = Math.random() * 100 + 20 // 关键词连接的视频数
      const betweenness = Math.random() * 0.4 + 0.05
      const interestingness = betweenness / (degree / 100)

      return {
        id: `keyword-arbitrage-${i + 1}`,
        keyword: generateMockKeyword(i),
        videoCount: totalVideos,
        totalViews,
        avgViewsPerVideo: Math.floor(totalViews / totalVideos),
        topVideoViews: Math.floor(totalViews * (Math.random() * 0.3 + 0.1)),

        // 中心性指标
        betweenness,
        closeness: Math.random() * 0.8 + 0.2,
        interestingness,
        degree,

        // 竞争度和机会
        competitionLevel: Math.random(), // 0-1，1 为最高竞争
        opportunityScore: (1 - Math.random() * 0.7) * interestingness, // 机会分数 = 低竞争 + 高有趣度

        // 趋势
        trendingUp: Math.random() > 0.5,
        monthlyGrowth: (Math.random() - 0.3) * 100, // -30% 到 70%
      }
    })

    // 按 rankingType 排序
    mockKeywords.sort((a, b) => {
      let aValue = 0
      let bValue = 0

      if (rankingType === 'interestingness') {
        aValue = a.interestingness || 0
        bValue = b.interestingness || 0
      } else if (rankingType === 'betweenness') {
        aValue = a.betweenness || 0
        bValue = b.betweenness || 0
      } else if (rankingType === 'closeness') {
        aValue = a.closeness || 0
        bValue = b.closeness || 0
      }

      return bValue - aValue
    })

    return NextResponse.json({
      success: true,
      data: {
        keywords: mockKeywords,
        timestamp: Date.now(),
        timeRange,
        rankingType,
        total: mockKeywords.length,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取关键词套利分析数据失败',
      },
      { status: 500 }
    )
  }
}

function generateMockKeyword(index: number): string {
  const keywords = [
    '美食教程',
    'AI 教学',
    '健身',
    '理财',
    '编程',
    '旅游',
    '养生',
    '游戏',
    '音乐',
    '电影',
    '搞笑',
    '知识',
    '体育',
    '科技',
    '生活',
    '文化',
    '艺术',
    '美妆',
    '汽车',
    '房产',
  ]

  const keyword = keywords[index % keywords.length]
  const modifier = ['新手', '入门', '教程', '指南', '技巧', '深度', '完全', '实战'][
    Math.floor(index / keywords.length) % 8
  ]

  return `${modifier}${keyword}`
}
