import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/insights/overview
 * 获取全局认识数据（市场概览）
 *
 * 查询参数：
 * - timeRange: 时间范围（7d, 30d, 90d, all） - 默认 7d
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const timeRange = searchParams.get('timeRange') || '7d'

    // Mock 关键指标
    const metrics = {
      totalVideos: 2340,
      totalChannels: 487,
      totalViews: 18500000,
      avgViewsPerVideo: 7905,
      totalLikes: 245000,
      totalComments: 89000,
    }

    // Mock 播放量分布（用于直方图）
    const viewsDistribution = [
      { range: '<1k', count: 234 },
      { range: '1k-5k', count: 456 },
      { range: '5k-10k', count: 389 },
      { range: '10k-50k', count: 678 },
      { range: '50k-100k', count: 345 },
      { range: '100k-500k', count: 178 },
      { range: '500k-1M', count: 56 },
      { range: '>1M', count: 8 },
    ]

    // Mock 视频发布趋势（12个月）
    const publishTrend = Array.from({ length: 12 }, (_, i) => ({
      month: `${i + 1}月`,
      videos: Math.floor(Math.random() * 300) + 150,
      avgViews: Math.floor(Math.random() * 15000) + 5000,
    }))

    // Mock 时间窗口分布（什么时候发？）
    const timeWindowDistribution = [
      { window: '早晨 (6-12点)', count: 285 },
      { window: '下午 (12-18点)', count: 672 },
      { window: '晚上 (18-24点)', count: 945 },
      { window: '夜晚 (0-6点)', count: 438 },
    ]

    // Mock 发布星期分布（雷达图）
    const weekDayDistribution = [
      { day: '周一', count: 312 },
      { day: '周二', count: 289 },
      { day: '周三', count: 356 },
      { day: '周四', count: 401 },
      { day: '周五', count: 478 },
      { day: '周六', count: 324 },
      { day: '周日', count: 280 },
    ]

    // Mock 发布时间热力图（7x24）
    const publishHeatmap = Array.from({ length: 7 }, (_, day) =>
      Array.from({ length: 24 }, (_, hour) => ({
        day,
        hour,
        count: Math.floor(Math.random() * 30) + 2,
      }))
    ).flat()

    // Mock 时长分布（环形图）
    const durationDistribution = [
      { label: '<4 分钟', value: 234, percentage: 10 },
      { label: '4-20 分钟', value: 1567, percentage: 67 },
      { label: '>20 分钟', value: 539, percentage: 23 },
    ]

    // Mock 播放量分层（饼图）
    const viewsSegmentation = [
      { label: '低播放 (<10k)', value: 1079, percentage: 46 },
      { label: '中等播放 (10k-100k)', value: 1023, percentage: 44 },
      { label: '高播放 (>100k)', value: 238, percentage: 10 },
    ]

    // Mock 四象限散点（时长 vs 完成率）
    const quadrantData = Array.from({ length: 120 }, (_, i) => ({
      duration: Math.floor(Math.random() * 60) + 2,
      completionRate: Math.floor(Math.random() * 100) + 30,
      views: Math.floor(Math.random() * 500000) + 10000,
    }))

    // Mock 语言分布
    const languageDistribution = [
      { language: '中文', count: 1850, percentage: 79 },
      { language: '英文', count: 312, percentage: 13 },
      { language: '日文', count: 89, percentage: 4 },
      { language: '韩文', count: 56, percentage: 2 },
      { language: '西班牙文', count: 33, percentage: 1.5 },
      { language: '其他', count: 20, percentage: 0.5 },
    ]

    // Mock 频道规模分布（环形图）
    const channelSizeDistribution = [
      { label: '微频道 (<1k 订阅)', value: 234, percentage: 48 },
      { label: '小频道 (1k-10k)', value: 156, percentage: 32 },
      { label: '中频道 (10k-100k)', value: 67, percentage: 14 },
      { label: '大频道 (>100k)', value: 30, percentage: 6 },
    ]

    // Mock 频道集中度（柱状图）
    const channelConcentration = [
      { rank: 'Top 1', views: 2500000 },
      { rank: 'Top 2-5', views: 1800000 },
      { rank: 'Top 6-10', views: 950000 },
      { rank: 'Top 11-50', views: 8200000 },
      { rank: '其他', views: 5050000 },
    ]

    // Mock Top 10 频道
    const topChannels = [
      { rank: 1, name: '健康养生宝典', subscribers: '125k', videos: 456, avgViews: 125000 },
      { rank: 2, name: '穴位按摩大师', subscribers: '98k', videos: 234, avgViews: 95000 },
      { rank: 3, name: '太极养生馆', subscribers: '87k', videos: 189, avgViews: 78000 },
      { rank: 4, name: '中医保健频道', subscribers: '76k', videos: 201, avgViews: 72000 },
      { rank: 5, name: '养生从这开始', subscribers: '65k', videos: 167, avgViews: 65000 },
      { rank: 6, name: '健身养生合一', subscribers: '54k', videos: 145, avgViews: 58000 },
      { rank: 7, name: '瑜伽养生生活', subscribers: '48k', videos: 129, avgViews: 52000 },
      { rank: 8, name: '老中医说养生', subscribers: '42k', videos: 115, avgViews: 48000 },
      { rank: 9, name: '现代养生智慧', subscribers: '38k', videos: 98, avgViews: 44000 },
      { rank: 10, name: '养生方法大全', subscribers: '34k', videos: 87, avgViews: 39000 },
    ]

    // Mock 国家分布
    const countryDistribution = [
      { country: '中国', count: 1890, percentage: 81 },
      { country: '美国', count: 198, percentage: 8.5 },
      { country: '新加坡', count: 89, percentage: 3.8 },
      { country: '台湾', count: 78, percentage: 3.3 },
      { country: '加拿大', count: 45, percentage: 1.9 },
      { country: '澳大利亚', count: 29, percentage: 1.2 },
      { country: '其他', count: 12, percentage: 0.3 },
    ]

    return NextResponse.json({
      success: true,
      data: {
        timeRange,
        metrics,
        viewsDistribution,
        publishTrend,
        timeWindowDistribution,
        weekDayDistribution,
        publishHeatmap,
        durationDistribution,
        viewsSegmentation,
        quadrantData,
        languageDistribution,
        channelSizeDistribution,
        channelConcentration,
        topChannels,
        countryDistribution,
        timestamp: Date.now(),
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取全局认识数据失败',
      },
      { status: 500 }
    )
  }
}
