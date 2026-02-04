import { NextResponse } from 'next/server'
import type { AnalyticsOverview } from '@/lib/types'

/**
 * GET /api/analytics/overview
 * 获取数据概览（总视频数、频道数、话题数、最后采集时间）
 */
export async function GET() {
  try {
    // TODO: 从后端 API 或数据库获取真实数据
    // const backendRes = await fetch(
    //   `${process.env.BACKEND_API_URL}/api/analytics/overview`
    // )

    // Mock 数据
    const overview: AnalyticsOverview = {
      totalVideos: Math.floor(Math.random() * 5000) + 2000,
      totalChannels: Math.floor(Math.random() * 500) + 100,
      totalTopics: Math.floor(Math.random() * 100) + 30,
      lastCollectedAt: Date.now() - Math.random() * 2 * 60 * 60 * 1000, // 2小时内
    }

    return NextResponse.json({
      success: true,
      data: overview,
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取数据概览失败',
      },
      { status: 500 }
    )
  }
}
