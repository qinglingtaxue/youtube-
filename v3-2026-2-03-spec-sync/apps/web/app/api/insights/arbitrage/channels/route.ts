import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/insights/arbitrage/channels
 * 获取频道维度的套利分析数据
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
    //   `${process.env.BACKEND_API_URL}/api/insights/arbitrage/channels?timeRange=${timeRange}&rankingType=${rankingType}&limit=${limit}`
    // )

    // Mock 数据：生成频道维度的有趣度排行
    const mockChannels = Array.from({ length: limit }, (_, i) => {
      const subscribers = Math.floor(Math.random() * 10000000) + 10000
      const totalViews = Math.floor(Math.random() * 500000000) + 1000000
      const degree = Math.random() * 50 + 10 // 频道连接数
      const betweenness = Math.random() * 0.3 + 0.05
      const interestingness = betweenness / (degree / 100)

      return {
        id: `channel-arbitrage-${i + 1}`,
        name: generateMockChannelName(i),
        subscribers,
        totalViews,
        videoCount: Math.floor(Math.random() * 500) + 50,
        avgViews: Math.floor(totalViews / (Math.random() * 300 + 50)),
        avgLikes: Math.floor(totalViews * (Math.random() * 0.1 + 0.01)),
        avgComments: Math.floor(totalViews * (Math.random() * 0.02 + 0.001)),

        // 中心性指标
        betweenness,
        closeness: Math.random() * 0.8 + 0.2,
        interestingness,
        degree,

        // 增长趋势
        recentGrowthRate: (Math.random() - 0.5) * 100, // -50% 到 +50%
        category: generateMockCategory(i),
      }
    })

    // 按 rankingType 排序
    mockChannels.sort((a, b) => {
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
        channels: mockChannels,
        timestamp: Date.now(),
        timeRange,
        rankingType,
        total: mockChannels.length,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取频道套利分析数据失败',
      },
      { status: 500 }
    )
  }
}

function generateMockChannelName(index: number): string {
  const prefixes = ['@', '频道', '官方', '新媒体']
  const topics = ['养生大师', '编程宝典', '美食天地', '旅游日记', '健身房', '学习中心', '财务分析', '科技前沿']

  const prefix = prefixes[index % prefixes.length]
  const topic = topics[Math.floor(index / prefixes.length) % topics.length]

  return `${prefix}${topic}${index + 1}`
}

function generateMockCategory(index: number): string {
  const categories = ['教育', '娱乐', '生活', '科技', '体育', '美食', '旅游', '财经', '音乐', '游戏']
  return categories[index % categories.length]
}
