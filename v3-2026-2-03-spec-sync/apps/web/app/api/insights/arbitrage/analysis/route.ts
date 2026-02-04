import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/insights/arbitrage/analysis
 * 获取综合分析数据（用于所有图表和洞察）
 *
 * 查询参数：
 * - videoId: 视频 ID（可选）
 * - channelId: 频道 ID（可选）
 * - timeRange: 时间范围（7d, 30d, 90d, all）
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const videoId = searchParams.get('videoId')
    const channelId = searchParams.get('channelId')
    const timeRange = searchParams.get('timeRange') || '7d'

    // 生成网络关系数据
    const generateNetworkData = () => {
      const nodeCount = Math.floor(Math.random() * 5) + 6
      const nodes = [
        { id: 'main', label: '当前项目', type: 'video', value: 300 },
      ]

      const types: Array<'video' | 'channel' | 'keyword'> = ['video', 'channel', 'keyword']
      const labels = ['视频1', '频道1', '关键词1', '视频2', '频道2', '关键词2', '视频3', '频道3', '关键词3']

      for (let i = 1; i < nodeCount; i++) {
        const type = types[i % 3]
        nodes.push({
          id: `node-${i}`,
          label: labels[i % labels.length] + Math.floor(i / 3),
          type,
          value: Math.floor(Math.random() * 200) + 50,
        })
      }

      const edges = []
      for (let i = 1; i < nodeCount; i++) {
        edges.push({
          source: 'main',
          target: `node-${i}`,
          weight: Math.floor(Math.random() * 5) + 1,
        })

        // 随机添加节点间的连接
        if (Math.random() > 0.6) {
          const target = Math.floor(Math.random() * (nodeCount - 1)) + 1
          if (target !== i) {
            edges.push({
              source: `node-${i}`,
              target: `node-${target}`,
              weight: Math.floor(Math.random() * 3) + 1,
            })
          }
        }
      }

      return { nodes, edges }
    }

    // 生成关键词数据
    const generateKeywords = () => {
      const keywords = [
        '内容营销',
        '数据分析',
        '用户增长',
        '视频创作',
        '社区运营',
        'SEO优化',
        '创意脚本',
        '后期制作',
        '频道规划',
        '粉丝互动',
        '算法推荐',
        '内容策略',
      ]

      return keywords.map(text => ({
        text,
        value: Math.floor(Math.random() * 200) + 50,
      }))
    }

    // 生成时间序列数据
    const generateTimeSeriesData = (days: number) => {
      const data = []
      let value = Math.floor(Math.random() * 50000) + 10000

      for (let i = 0; i < days; i++) {
        const date = new Date()
        date.setDate(date.getDate() - (days - i - 1))

        data.push({
          date: date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
          value: value,
        })

        // 随机游走
        value += Math.floor((Math.random() - 0.4) * 5000)
        value = Math.max(value, 5000)
      }

      return data
    }

    // 生成分类对比数据
    const generateCategoryData = () => {
      const categories = ['教程', '评论', '分享', '案例', '其他']
      return categories.map(name => ({
        name,
        value: Math.floor(Math.random() * 500) + 100,
      }))
    }

    // 生成热力图数据
    const generateHeatmapData = () => {
      const rows = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      const cols = ['上午', '中午', '下午', '晚上']
      const data: Array<{ row: string; col: string; value: number }> = []

      rows.forEach(row => {
        cols.forEach(col => {
          data.push({
            row,
            col,
            value: Math.floor(Math.random() * 1000) + 100,
          })
        })
      })

      return data
    }

    const networkData = generateNetworkData()
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365
    const timeSeriesData = generateTimeSeriesData(days)
    const categoryData = generateCategoryData()
    const heatmapData = generateHeatmapData()
    const keywords = generateKeywords()

    return NextResponse.json({
      success: true,
      data: {
        // 网络关系
        network: {
          nodes: networkData.nodes,
          edges: networkData.edges,
        },

        // 时间序列
        timeSeries: {
          views: timeSeriesData,
          engagement: timeSeriesData.map(d => ({
            ...d,
            value: Math.floor(d.value * 0.15),
          })),
        },

        // 分类对比
        categories: categoryData,

        // 热力图
        heatmap: heatmapData,

        // 关键词
        keywords,

        // 元数据
        timestamp: Date.now(),
        timeRange,
        videoId,
        channelId,
      },
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '获取分析数据失败',
      },
      { status: 500 }
    )
  }
}
