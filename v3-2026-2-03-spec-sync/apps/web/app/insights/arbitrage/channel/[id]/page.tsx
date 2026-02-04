'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, Share2, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { LineChart, BarChart, InsightCard, InsightCards } from '@/components/insights'
import { useParams } from 'next/navigation'

interface ChannelDetail {
  id: string
  name: string
  subscribers: number
  totalViews: number
  videoCount: number
  avgViews: number
  interestingness: number
  betweenness: number
  closeness: number
  degree: number
  recentGrowthRate: number
  category: string
}

interface MonthlyData {
  date: string
  value: number
}

export default function ChannelDetailPage() {
  const params = useParams()
  const id = params?.id as string

  const [channel, setChannel] = useState<ChannelDetail | null>(null)
  const [monthlyGrowth, setMonthlyGrowth] = useState<MonthlyData[]>([])
  const [topVideos, setTopVideos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return

    try {
      // Mock 频道详情数据
      const mockChannel: ChannelDetail = {
        id: id,
        name: '@科技教学频道',
        subscribers: 450000,
        totalViews: 125000000,
        videoCount: 287,
        avgViews: 435000,
        interestingness: 0.72,
        betweenness: 0.28,
        closeness: 0.65,
        degree: 35,
        recentGrowthRate: 12.5,
        category: '教育',
      }

      setChannel(mockChannel)

      // Mock 12 个月增长数据
      const growth: MonthlyData[] = []
      let currentSubs = 350000
      for (let i = 11; i >= 0; i--) {
        const date = new Date()
        date.setMonth(date.getMonth() - i)
        growth.push({
          date: date.toLocaleDateString('zh-CN', { month: 'short', year: '2-digit' }),
          value: currentSubs,
        })
        currentSubs += Math.random() * 20000
      }
      setMonthlyGrowth(growth)

      // Mock 热门视频
      setTopVideos(
        Array.from({ length: 5 }, (_, i) => ({
          id: `video-${i}`,
          title: `热门视频 ${i + 1}`,
          views: Math.floor(Math.random() * 1000000) + 500000,
          uploadDate: new Date(Date.now() - Math.random() * 180 * 24 * 60 * 60 * 1000).toLocaleDateString(),
        }))
      )
    } catch (error) {
      console.error('Failed to fetch channel detail:', error)
    } finally {
      setLoading(false)
    }
  }, [id])

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (!channel) {
    return <div className="text-center py-12">频道不存在</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 返回按钮 */}
        <Link href="/insights/arbitrage" className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mb-6">
          <ChevronLeft className="w-4 h-4" />
          返回套利分析
        </Link>

        {/* 频道信息卡 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 sm:p-8 mb-6">
          <div className="flex gap-6 mb-6">
            {/* 频道头像 */}
            <div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-purple-600 rounded-full flex-shrink-0 flex items-center justify-center text-white text-2xl font-bold">
              {channel.name.charAt(1)}
            </div>

            <div className="flex-1">
              <h1 className="text-2xl sm:text-3xl font-bold mb-2">{channel.name}</h1>
              <p className="text-gray-600 dark:text-gray-400 mb-4">{channel.category} · {channel.videoCount} 个视频</p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">订阅者</p>
                  <p className="font-semibold">{(channel.subscribers / 1000).toFixed(0)}k</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">总播放量</p>
                  <p className="font-semibold">{(channel.totalViews / 1000000).toFixed(0)}M</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">平均视频播放</p>
                  <p className="font-semibold">{(channel.avgViews / 10000).toFixed(0)}w</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">最近增长率</p>
                  <p className="font-semibold text-green-600">{channel.recentGrowthRate.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex flex-col gap-2">
              <Button variant="outline" size="sm" className="gap-2">
                <Share2 className="w-4 h-4" />
                分享
              </Button>
              <Button variant="outline" size="sm" className="gap-2">
                <Download className="w-4 h-4" />
                导出
              </Button>
            </div>
          </div>
        </div>

        {/* 中心性指标 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">有趣度</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{channel.interestingness.toFixed(2)}</p>
            <p className="text-xs text-gray-500 mt-2">内容价值指数</p>
          </div>

          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">中介中心性</p>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{(channel.betweenness * 100).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-2">内容影响力</p>
          </div>

          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">接近中心性</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{(channel.closeness * 100).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-2">传播便利度</p>
          </div>

          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">程度中心性</p>
            <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{channel.degree}</p>
            <p className="text-xs text-gray-500 mt-2">协作频率</p>
          </div>
        </div>

        {/* 订阅增长趋势 */}
        {monthlyGrowth.length > 0 && (
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 mb-6">
            <LineChart data={monthlyGrowth} title="📈 订阅增长趋势（过去 12 个月）" label="订阅者数" />
          </div>
        )}

        {/* 内容分布 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 mb-6">
          <BarChart
            data={[
              { name: '教程', value: Math.floor(channel.videoCount * 0.35), color: '#3b82f6' },
              { name: '评论', value: Math.floor(channel.videoCount * 0.25), color: '#10b981' },
              { name: '动态', value: Math.floor(channel.videoCount * 0.2), color: '#f59e0b' },
              { name: '其他', value: Math.floor(channel.videoCount * 0.2), color: '#8b5cf6' },
            ]}
            title="📊 视频类型分布"
          />
        </div>

        {/* 频道洞察 */}
        <InsightCards
          cards={[
            {
              title: '🎯 增长机会',
              icon: '📈',
              description: '频道发展建议',
              insights: [
                `最近三个月增长率 ${channel.recentGrowthRate.toFixed(1)}%，显示稳定增长趋势`,
                '平均视频播放量 43.5w，说明内容有一定吸引力',
                '有趣度 0.72，介于中高水平，仍有优化空间',
              ],
              actionItems: [
                '分析高播放视频特征，复制成功经验',
                '增加互动环节，提升评论和分享率',
                '考虑与相邻领域频道合作，拓展受众',
              ],
              type: 'success',
            },
            {
              title: '💡 市场洞察',
              icon: '🔍',
              description: '竞争态势分析',
              insights: [
                `${channel.category}类频道中，订阅者排名中等偏上`,
                '内容类型多样化，有助于吸引不同受众',
                '与主流内容创作者联系度中等，有跨界机会',
              ],
              actionItems: [
                '研究同领域排名前 5 的频道策略',
                '定期发布热点相关内容，抓住流量机会',
                '建立粉丝互动社群，提高用户粘性',
              ],
              type: 'info',
            },
          ]}
        />

        {/* 热门视频 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">🎬 热门视频</h3>
          <div className="space-y-3">
            {topVideos.map((video, idx) => (
              <div key={video.id} className="p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 transition">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-sm">#{idx + 1} {video.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{video.uploadDate} 上传</p>
                  </div>
                  <span className="text-sm font-bold text-purple-600">{(video.views / 10000).toFixed(0)}w</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
