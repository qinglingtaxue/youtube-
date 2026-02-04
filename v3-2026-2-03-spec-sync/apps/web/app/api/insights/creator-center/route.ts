import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/insights/creator-center
 * 获取创作者中心诊断数据
 *
 * 查询参数：
 * - channelId: 频道 ID（可选）
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const channelId = searchParams.get('channelId')

    // Mock 频道数据
    const channelInfo = {
      name: '穴位养生馆',
      createdAt: '6 个月前',
      subscribers: '2.4 万',
      videoCount: 24,
      avgDuration: 11, // 分钟
      publishFrequency: 1.5, // 次/周
      avgViews: 85000,
      engagementRate: 0.012, // 1.2%
      topicCount: 8,
    }

    // Mock 诊断数据
    const diagnoses = [
      {
        id: 1,
        title: '视频时长',
        metric: '平均时长',
        current: '11 分钟',
        baseline: '8 分钟',
        difference: '+3 分钟（偏长）',
        isPositive: false,
        marketFinding: [
          '4-20min 中视频均播 8.2 万（最高）',
          '你当前在中视频范围内 ✓',
          '但相对市场均值 8 分钟仍偏长 -1.5%',
        ],
        suggestions: [
          '改进方向：下降到 8-10 分钟范围',
          '预期改进：播放完成率 +3~5%',
          '执行难度：中等（需调整脚本和素材使用）',
        ],
        referenceLink: '/insights/report#conclusion-3',
      },
      {
        id: 2,
        title: '互动率',
        metric: '点赞 + 评论 ÷ 播放',
        current: '1.2%',
        baseline: '2.8%',
        difference: '-1.6% （偏低）',
        isPositive: false,
        marketFinding: [
          '市场平均互动率：2.8%',
          '你的频道互动率：1.2%',
          '差异原因可能：缺乏互动环节 / 评论激励',
        ],
        suggestions: [
          '改进方向：在视频中段增加互动问题',
          '预期改进：互动率 +0.8~1.2%',
          '执行难度：低（无需改变内容结构）',
        ],
        referenceLink: '/insights',
      },
      {
        id: 3,
        title: '发布频率',
        metric: '每周发布次数',
        current: '1.5 次/周',
        baseline: '2.5 次/周',
        difference: '-1 次/周（低于标准）',
        isPositive: false,
        marketFinding: [
          '市场增长型频道：2.5 次/周',
          '你的频道：1.5 次/周',
          '算法偏好：定期发布信号强于单个视频质量',
        ],
        suggestions: [
          '改进方向：增加到 2 次/周',
          '预期改进：月订阅增长 +8~12%',
          '执行难度：高（需提前规划和素材储备）',
        ],
        referenceLink: '/insights/report',
      },
      {
        id: 4,
        title: '选题方向',
        metric: '内容话题多样性',
        current: '8 个话题',
        baseline: '集中于 2-3 个缺口话题',
        difference: '机会：聚焦缺口话题',
        isPositive: true,
        marketFinding: [
          '穴位按摩 / 太极养生 搜索量高但供应少',
          '你目前话题太分散，容易被算法视为"什么都做"',
          '建议：前 90 天专注 2-3 个缺口话题建立特色',
        ],
        suggestions: [
          '改进方向：在穴位按摩 + 太极养生 两个话题深度',
          '预期改进：这两个话题的视频播放 +30~50%',
          '执行难度：中等（需调整选题方向和脚本库）',
        ],
        referenceLink: '/insights/arbitrage#conclusion-2',
      },
    ]

    // Mock 改进目标
    const improvementGoals = [
      {
        metric: '互动率改进',
        current: '1.2%',
        target: '2.0%',
        progress: 43,
        dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        metric: '发布频率改进',
        current: '1.5 次/周',
        target: '2 次/周',
        progress: 60,
        dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        metric: '选题聚焦',
        current: '8 个话题',
        target: '3 个话题',
        progress: 75,
        dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ]

    // Mock 核心指标
    const coreMetrics = [
      {
        name: '平均播放量',
        current: 85000,
        baseline: 120000,
        diff: -29,
      },
      {
        name: '互动率',
        current: 1.2,
        baseline: 2.8,
        diff: -57,
      },
      {
        name: '发布频率',
        current: 1.5,
        baseline: 2.5,
        diff: -40,
      },
    ]

    return NextResponse.json({
      success: true,
      data: {
        channelInfo,
        coreMetrics,
        diagnoses,
        improvementGoals,
        timestamp: Date.now(),
        channelId,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取创作者中心数据失败',
      },
      { status: 500 }
    )
  }
}
