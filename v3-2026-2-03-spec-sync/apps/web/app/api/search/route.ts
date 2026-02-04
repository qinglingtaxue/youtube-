import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import type { SearchFilters, SortConfig } from '@/lib/types'

// 请求验证 Schema
const SearchRequestSchema = z.object({
  query: z.string().min(1, '搜索词不能为空').max(100),
  filters: z.object({
    timeRange: z.enum(['24h', '7d', '30d', '1y', 'all']),
    duration: z.enum(['all', '<4min', '4-20min', '>20min']),
    channelSize: z.enum(['all', '<10k', '10-100k', '100-1M', '>1M']),
    minViews: z.number().optional(),
    contentTags: z.array(z.string()),
  }),
  sortConfig: z.object({
    timeRange: z.string(),
    sortField: z.enum(['views', 'likes', 'comments', 'avgDailyViews', 'duration']),
    direction: z.enum(['asc', 'desc']),
  }),
  page: z.number().optional().default(1),
  limit: z.number().optional().default(20),
})

/**
 * 生成自然语言排序说明
 */
function generateSortDescription(sortConfig: SortConfig): string {
  const timeRangeText: Record<string, string> = {
    '24h': '24小时内',
    '7d': '过去7天',
    '30d': '过去30天',
    '1y': '过去1年',
    'all': '全部时间',
  }

  const fieldText: Record<string, string> = {
    views: '播放量',
    likes: '点赞数',
    comments: '评论数',
    avgDailyViews: '日均播放',
    duration: '时长',
  }

  const direction = sortConfig.direction === 'desc' ? '高→低' : '低→高'

  return `${timeRangeText[sortConfig.timeRange]}发布的视频，按${fieldText[sortConfig.sortField]}从${direction}排序`
}

/**
 * POST /api/search
 * 搜索视频
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    // 验证请求数据
    const validated = SearchRequestSchema.parse(body)

    // TODO: 调用后端 API (Fastify)
    // const backendRes = await fetch(
    //   `${process.env.BACKEND_API_URL}/api/search`,
    //   {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(validated),
    //   }
    // )

    // 临时 mock 数据
    const mockResults = Array.from({ length: validated.limit }, (_, i) => ({
      id: `video-${i + 1}`,
      youtubeId: `dQw4w9WgXcQ`,
      title: `${validated.query} - 视频 ${i + 1}`,
      channelName: `频道 ${i + 1}`,
      channelId: `channel-${i + 1}`,
      thumbnail: `https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg`,
      views: Math.floor(Math.random() * 10000000),
      likes: Math.floor(Math.random() * 500000),
      comments: Math.floor(Math.random() * 100000),
      duration: Math.floor(Math.random() * 3600),
      publishedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      channelSubscribers: Math.floor(Math.random() * 10000000),
    }))

    const naturalLanguage = generateSortDescription(validated.sortConfig)

    return NextResponse.json({
      success: true,
      data: {
        results: mockResults,
        total: 156,
        page: validated.page,
        naturalLanguage,
      },
    })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          success: false,
          error: '请求数据验证失败',
          details: error.errors,
        },
        { status: 400 }
      )
    }

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '未知错误',
      },
      { status: 500 }
    )
  }
}
