import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/insights/report
 * 获取信息报告数据（推理链式结论）
 *
 * 查询参数：
 * - videoId: 视频 ID（可选）
 * - channelId: 频道 ID（可选）
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const videoId = searchParams.get('videoId')
    const channelId = searchParams.get('channelId')

    // Mock 结论数据
    const conclusions = [
      {
        id: '1',
        title: '市场竞争分散，新人有机会',
        icon: '🎯',
        summary: '行业 Top 10 视频仅占总播放量的 23%，说明市场高度分散',
        reasoning: [
          'YouTube 推荐算法优先展示新鲜内容，不只是大频道',
          '小频道通过找到内容缺口，可快速突破 10k 订阅',
          '当前数据显示无绝对头部，意味着新选手入场机会大',
        ],
        dataPoints: [
          { label: '市场集中度', value: '23%' },
          { label: 'Top 10 频道数', value: '≤10' },
          { label: '新频道机会', value: '高' },
        ],
        actionItems: [
          '不必死守传统大频道模式，寻找垂直细分领域',
          '关注小频道高增长案例，学习其成功模式',
        ],
        priority: 1,
        confidence: 0.95,
      },
      {
        id: '2',
        title: '「穴位按摩」等话题内容缺口',
        icon: '💡',
        summary: '部分话题视频数量少但搜索热度高，是内容创作的蓝海',
        reasoning: [
          '通过关键词分析，发现搜索量与实际视频数量的错配',
          '这类话题往往有稳定需求但供应不足',
          '创作者可快速获得搜索推荐流量',
        ],
        dataPoints: [
          { label: '缺口话题数', value: '12' },
          { label: '平均月搜索量', value: '8.5k' },
          { label: '当前供应', value: '偏少' },
        ],
        actionItems: [
          '优先选择高搜索+低供应的话题组合',
          '标题和描述中突出关键词密度',
        ],
        priority: 1,
        confidence: 0.88,
      },
      {
        id: '3',
        title: '4-20分钟中视频是最优时长选择',
        icon: '⏱️',
        summary: '数据显示 4-20 分钟视频平均播放完成率最高，建议优先采用',
        reasoning: [
          '短视频 (<4min) 虽然很热，但竞争激烈且流量易断',
          '长视频 (>20min) 虽然粉丝粘性强，但新频道难以坚持',
          '中视频兼具流量潜力和创作可持续性',
        ],
        dataPoints: [
          { label: '完成率 (<4min)', value: '62%' },
          { label: '完成率 (4-20min)', value: '78%' },
          { label: '完成率 (>20min)', value: '68%' },
        ],
        actionItems: [
          '核心内容锁定在 8-15 分钟，即便同时发短版本',
          '避免硬凑时长，用优质素材填充而非重复',
        ],
        priority: 1,
        confidence: 0.92,
      },
      {
        id: '4',
        title: 'Tai Chi 跨语言机会',
        icon: '🌍',
        summary: '英文市场对传统文化内容需求旺盛，可拓展海外版本',
        reasoning: [
          '分析表明英文查询量 3 倍于中文，但中文创作者供应不足',
          '海外平台对中国传统文化有新鲜感和刚需求',
          '可通过简单翻译 + 本地化获得新流量',
        ],
        dataPoints: [
          { label: '英文搜索量', value: '28k' },
          { label: '中文搜索量', value: '9.2k' },
          { label: '供应缺口', value: '高' },
        ],
        actionItems: [
          '用英文字幕或翻配音，成本低但流量收益大',
          '研究海外平台标题关键词习惯',
        ],
        priority: 2,
        confidence: 0.82,
      },
    ]

    // 综合结论
    const synthesis = {
      keyMessage: '不要贪大求全。选择一个竞争分散的细分领域（如「穴位按摩」），优先选择 4-20 分钟的中视频时长，利用内容缺口快速获得初始流量。',
      expansion: '一旦积累 1000+ 粉丝，可考虑海外版本（英文字幕/翻配音），触及 3 倍的英文市场需求。',
      continuousImprovement: '前 30 天专注单一话题建立频道特色，后续根据数据反馈逐步扩展内容范围。',
    }

    // 研究问题
    const research = {
      question: '如何在 YouTube 竞争中快速积累初始粉丝？',
      description: '通过市场分析、内容对标、时长优化等多维度数据，给出可执行的创作建议',
    }

    return NextResponse.json({
      success: true,
      data: {
        research,
        conclusions: conclusions.sort((a, b) => a.priority - b.priority),
        synthesis,
        timestamp: Date.now(),
        videoId,
        channelId,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取信息报告失败',
      },
      { status: 500 }
    )
  }
}
