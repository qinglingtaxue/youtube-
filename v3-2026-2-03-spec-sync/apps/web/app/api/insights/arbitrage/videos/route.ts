import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/insights/arbitrage/videos
 * 获取视频维度的套利分析数据
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
    //   `${process.env.BACKEND_API_URL}/api/insights/arbitrage/videos?timeRange=${timeRange}&rankingType=${rankingType}&limit=${limit}`
    // )

    // Mock 数据：生成有趣度排行
    const mockVideos = Array.from({ length: limit }, (_, i) => {
      const views = Math.floor(Math.random() * 10000000) + 100000
      const degree = Math.random() * 10 + 1
      const betweenness = Math.random() * 0.5 + 0.1
      const interestingness = betweenness / degree

      return {
        id: `video-arbitrage-${i + 1}`,
        title: generateMockTitle(i),
        views,
        likes: Math.floor(views * (Math.random() * 0.1 + 0.01)),
        comments: Math.floor(views * (Math.random() * 0.02 + 0.001)),
        channelName: `频道 ${Math.floor(Math.random() * 100) + 1}`,
        channelSubscribers: Math.floor(Math.random() * 10000000) + 1000,
        publishedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),

        // 中心性指标
        betweenness,
        closeness: Math.random() * 0.8 + 0.2,
        interestingness,
        degree,
      }
    })

    // 按 rankingType 排序
    mockVideos.sort((a, b) => {
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
        videos: mockVideos,
        timestamp: Date.now(),
        timeRange,
        rankingType,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取套利分析数据失败',
      },
      { status: 500 }
    )
  }
}

function generateMockTitle(index: number): string {
  const topics = ['养生', '编程', '美食', '旅游', '健身', '学习', '投资', '科技']
  const actions = ['5 分钟学会', '完整指南', '终极教程', '深度分析', '实战演示', '对比评测']

  const topic = topics[index % topics.length]
  const action = actions[Math.floor(index / topics.length) % actions.length]

  return `${action} - ${topic}`
}
