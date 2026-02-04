import { NextRequest, NextResponse } from 'next/server'
import type { VideoCard } from '@/lib/types'

/**
 * GET /api/videos/trending
 * 获取本周爆款视频（播放量 Top N）
 *
 * 查询参数：
 * - limit: 返回数量（默认 5）
 * - timeRange: 时间范围（默认 7d）
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const limit = Math.min(parseInt(searchParams.get('limit') || '5'), 50)
    const timeRange = searchParams.get('timeRange') || '7d'

    // TODO: 从后端 API 或数据库获取真实数据
    // const backendRes = await fetch(
    //   `${process.env.BACKEND_API_URL}/api/videos/trending?limit=${limit}&timeRange=${timeRange}`
    // )

    // Mock 数据
    const mockVideos: VideoCard[] = Array.from({ length: limit }, (_, i) => ({
      id: `video-trending-${i + 1}`,
      title: generateMockTitle(i),
      thumbnail: `https://i.ytimg.com/vi/${generateYouTubeId()}/mqdefault.jpg`,
      views: Math.floor(Math.random() * 10000000) + 100000,
      channelName: `频道 ${i + 1}`,
    }))

    // 按播放量排序
    mockVideos.sort((a, b) => b.views - a.views)

    return NextResponse.json({
      success: true,
      data: {
        videos: mockVideos,
        timestamp: Date.now(),
        timeRange,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取爆款视频失败',
      },
      { status: 500 }
    )
  }
}

function generateMockTitle(index: number): string {
  const titles = [
    '如何高效学习编程',
    '10分钟学会 React Hooks',
    '前端性能优化完整指南',
    '深入理解 JavaScript 闭包',
    'CSS Grid 布局实战教程',
    'TypeScript 进阶技巧',
    '构建可扩展的 Web 应用',
    '现代 JavaScript 必知必会',
    'Web 安全防护全攻略',
    '算法面试题详解',
  ]
  return titles[index % titles.length]
}

function generateYouTubeId(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
  let id = ''
  for (let i = 0; i < 11; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return id
}
