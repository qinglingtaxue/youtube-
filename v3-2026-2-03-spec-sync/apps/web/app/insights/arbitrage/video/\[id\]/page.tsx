'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, Share2, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { LineChart, BarChart, InsightCard, InsightCards } from '@/components/insights'

interface VideoDetail {
  id: string
  title: string
  channelName: string
  publishedAt: string
  views: number
  likes: number
  comments: number
  interestingness: number
  betweenness: number
  closeness: number
  degree: number
}

interface GrowthData {
  date: string
  value: number
}

export default function VideoDetailPage({ params }: { params: { id: string } }) {
  const [video, setVideo] = useState<VideoDetail | null>(null)
  const [growthData, setGrowthData] = useState<GrowthData[]>([])
  const [relatedVideos, setRelatedVideos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVideoDetail()
  }, [params.id])

  const fetchVideoDetail = async () => {
    setLoading(true)
    try {
      // Mock 详情数据
      const mockVideo: VideoDetail = {
        id: params.id,
        title: '5 分钟学会 AI 视频生成 - 完整教程',
        channelName: '科技教学频道',
        publishedAt: '2024-02-01',
        views: 2500000,
        likes: 45000,
        comments: 8500,
        interestingness: 0.85,
        betweenness: 0.32,
        closeness: 0.68,
        degree: 24,
      }

      setVideo(mockVideo)

      // Mock 增长数据（过去 30 天）
      const growth: GrowthData[] = []
      let currentViews = 50000
      for (let i = 0; i < 30; i++) {
        growth.push({
          date: new Date(Date.now() - (30 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
          value: currentViews,
        })
        currentViews += Math.random() * 100000
      }
      setGrowthData(growth)

      // Mock 相关视频
      setRelatedVideos(
        Array.from({ length: 5 }, (_, i) => ({
          id: `related-${i}`,
          title: `相关视频 ${i + 1}`,
          views: Math.floor(Math.random() * 1000000),
          interestingness: Math.random() * 1,
        }))
      )
    } catch (error) {
      console.error('Failed to fetch video detail:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (!video) {
    return <div className="text-center py-12">视频不存在</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 返回按钮 */}
        <Link href="/insights/arbitrage" className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mb-6">
          <ChevronLeft className="w-4 h-4" />
          返回套利分析
        </Link>

        {/* 视频信息卡 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 sm:p-8 mb-6">
          <div className="flex gap-6 mb-6">
            {/* 视频缩略图 */}
            <div className="w-48 h-28 bg-gray-300 dark:bg-slate-700 rounded-lg flex-shrink-0" />

            <div className="flex-1">
              <h1 className="text-2xl sm:text-3xl font-bold mb-2">{video.title}</h1>
              <p className="text-gray-600 dark:text-gray-400 mb-4">频道：{video.channelName}</p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">发布时间</p>
                  <p className="font-semibold">{video.publishedAt}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">播放量</p>
                  <p className="font-semibold">{(video.views / 1000000).toFixed(1)}M</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">点赞数</p>
                  <p className="font-semibold">{(video.likes / 1000).toFixed(0)}k</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">评论数</p>
                  <p className="font-semibold">{(video.comments / 1000).toFixed(1)}k</p>
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
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{video.interestingness.toFixed(2)}</p>
            <p className="text-xs text-gray-500 mt-2">套利机会指数</p>
          </div>

          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">中介中心性</p>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{(video.betweenness * 100).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-2">传播枢纽程度</p>
          </div>

          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">接近中心性</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{(video.closeness * 100).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-2">网络距离指标</p>
          </div>

          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">程度中心性</p>
            <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{video.degree}</p>
            <p className="text-xs text-gray-500 mt-2">直接连接数</p>
          </div>
        </div>

        {/* 增长趋势 */}
        {growthData.length > 0 && (
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 mb-6">
            <LineChart data={growthData} title="📈 播放量增长趋势（过去 30 天）" label="播放量" />
          </div>
        )}

        {/* 互动分析 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 mb-6">
          <BarChart
            data={[
              { name: '点赞', value: video.likes, color: '#ef4444' },
              { name: '评论', value: video.comments, color: '#3b82f6' },
              {
                name: '分享',
                value: Math.floor(video.comments * 0.3),
                color: '#10b981',
              },
            ]}
            title="💬 互动数据对比"
            horizontal={true}
          />
        </div>

        {/* 洞察和建议 */}
        <InsightCards
          cards={[
            {
              title: '✨ 蓝海机会',
              icon: '💎',
              description: '这个视频具有高套利价值',
              insights: [
                '有趣度高达 0.85，说明内容价值大但传播力相对有限',
                '中介中心性 0.32，表明这个话题在网络中的连接程度中等',
                '可以通过优化分发策略进一步提升播放量',
              ],
              actionItems: [
                '分析标题和描述中的关键词优化机会',
                '查看类似高播放视频的发布时间模式',
                '考虑联合推广或合作创作',
              ],
              type: 'success',
            },
            {
              title: '📊 性能对标',
              icon: '🎯',
              description: '与同类视频对比',
              insights: [
                '相同话题平均视频播放量约 1.5M，该视频达到 2.5M',
                '点赞率（1.8%）高于行业平均水平（1.2%）',
                '评论率（0.34%）处于中上水平',
              ],
              actionItems: [
                '复制高互动视频的封面设计风格',
                '在标题中突出核心价值主张',
                '增加互动性问题以提升评论量',
              ],
              type: 'info',
            },
          ]}
        />

        {/* 相关视频 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">🔗 相关推荐</h3>
          <div className="space-y-3">
            {relatedVideos.map(video => (
              <div key={video.id} className="p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-slate-800 transition cursor-pointer">
                <p className="font-medium line-clamp-1">{video.title}</p>
                <div className="flex justify-between items-center mt-2 text-sm text-gray-600 dark:text-gray-400">
                  <span>{(video.views / 1000000).toFixed(1)}M 播放</span>
                  <span className="font-semibold text-purple-600">有趣度: {video.interestingness.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
