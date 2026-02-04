import { NextRequest, NextResponse } from 'next/server'
import type { ChannelRow } from '@/lib/types'

/**
 * GET /api/channels/trending
 * 获取黑马频道（低订阅高播放）
 *
 * 查询参数：
 * - limit: 返回数量（默认 3）
 * - type: 频道类型，可选 'high-efficiency' 或 'all'（默认 all）
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const limit = Math.min(parseInt(searchParams.get('limit') || '3'), 50)
    const type = searchParams.get('type') || 'all'

    // TODO: 从后端 API 或数据库获取真实数据
    // const backendRes = await fetch(
    //   `${process.env.BACKEND_API_URL}/api/channels/trending?limit=${limit}&type=${type}`
    // )

    // Mock 数据：黑马频道（低订阅高播放）
    const mockChannels: ChannelRow[] = Array.from({ length: limit }, (_, i) => {
      const subscribers = Math.floor(Math.random() * 100000) + 1000
      const avgViews = Math.floor(Math.random() * 500000) + 50000
      const efficiencyScore = (avgViews / subscribers).toFixed(1)

      return {
        id: `channel-trending-${i + 1}`,
        name: generateMockChannelName(i),
        subscribers,
        avgViews,
        efficiencyScore: parseFloat(efficiencyScore),
        lastUpdated: formatRelativeTime(
          Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000
        ),
      }
    })

    // 按效率分数排序（高到低）
    mockChannels.sort((a, b) => b.efficiencyScore - a.efficiencyScore)

    return NextResponse.json({
      success: true,
      data: {
        channels: mockChannels,
        timestamp: Date.now(),
        type,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取频道数据失败',
      },
      { status: 500 }
    )
  }
}

function generateMockChannelName(index: number): string {
  const names = [
    '编程思维养成',
    '技术工坊',
    '代码手工坊',
    '前端密码',
    '后端秘籍',
    '全栈之路',
    '编程乐园',
    '代码艺术馆',
    '技术探险队',
    '开发者笔记',
  ]
  return names[index % names.length]
}

function formatRelativeTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const days = Math.floor(diff / (24 * 60 * 60 * 1000))

  if (days === 0) return '今天'
  if (days === 1) return '1 天前'
  if (days < 7) return `${days} 天前`
  if (days < 30) return `${Math.floor(days / 7)} 周前`
  return `${Math.floor(days / 30)} 月前`
}
