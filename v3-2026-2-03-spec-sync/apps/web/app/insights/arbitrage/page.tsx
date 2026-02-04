'use client'

import { useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SortConfig {
  timeRange: string
  field: string
  direction: 'asc' | 'desc'
}

interface Video {
  id: string
  title: string
  views: number
  likes: number
  comments: number
  betweenness?: number
  closeness?: number
  interestingness?: number
}

export default function ArbitrageAnalysisPage() {
  const [activeDataTab, setActiveDataTab] = useState<'videos' | 'channels' | 'keywords'>('videos')
  const [activeRankingTab, setActiveRankingTab] = useState<'interestingness' | 'betweenness' | 'closeness'>('interestingness')
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    timeRange: '7d',
    field: 'views',
    direction: 'desc',
  })
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [activeDataTab, activeRankingTab, sortConfig])

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        timeRange: sortConfig.timeRange,
        rankingType: activeRankingTab,
        limit: '50',
      })
      const res = await fetch(`/api/insights/arbitrage/${activeDataTab}?${params}`)
      if (res.ok) {
        const data = await res.json()
        setVideos(data.data?.[activeDataTab] || [])
      }
    } catch (error) {
      console.error('Failed to fetch arbitrage data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getSortDescription = () => {
    const timeRangeMap: Record<string, string> = {
      '7d': '过去 7 天',
      '30d': '过去 30 天',
      '90d': '过去 90 天',
      all: '全部时间',
    }
    const fieldMap: Record<string, string> = {
      views: '播放量',
      interestingness: '有趣度',
      betweenness: '中介中心性',
      closeness: '接近中心性',
    }
    return `${timeRangeMap[sortConfig.timeRange]}，按 ${fieldMap[sortConfig.field]} ${sortConfig.direction === 'desc' ? '高→低' : '低→高'}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* 页面头 */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">💰 套利分析</h1>
          <p className="text-gray-600 dark:text-gray-400">
            发现被低估的视频和频道 · 有趣度 = 中介中心性 ÷ 程度中心性
          </p>
        </div>

        {/* Tab 分组 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-4 sm:p-6 mb-6">
          {/* 看数据 Tabs */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-3">📊 看数据</h3>
            <div className="flex gap-2 flex-wrap">
              {(['videos', 'channels', 'keywords'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveDataTab(tab)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    activeDataTab === tab
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {tab === 'videos' && '📹 视频'}
                  {tab === 'channels' && '🎬 频道'}
                  {tab === 'keywords' && '🔑 关键词'}
                </button>
              ))}
            </div>
          </div>

          {/* 找机会 Tabs */}
          <div>
            <h3 className="text-sm font-semibold mb-3">💎 找机会（榜单类型）</h3>
            <div className="flex gap-2 flex-wrap">
              {(['interestingness', 'betweenness', 'closeness'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveRankingTab(tab)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    activeRankingTab === tab
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {tab === 'interestingness' && '💎 有趣度'}
                  {tab === 'betweenness' && '🌉 中介'}
                  {tab === 'closeness' && '🔥 程度'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 排序控制 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-4 sm:p-6 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            {/* 时间范围 */}
            <div>
              <label className="block text-sm font-medium mb-2">时间范围</label>
              <select
                value={sortConfig.timeRange}
                onChange={(e) => setSortConfig({ ...sortConfig, timeRange: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700"
              >
                <option value="7d">7 天内</option>
                <option value="30d">30 天内</option>
                <option value="90d">90 天内</option>
                <option value="all">全部时间</option>
              </select>
            </div>

            {/* 排序字段 */}
            <div>
              <label className="block text-sm font-medium mb-2">排序字段</label>
              <select
                value={sortConfig.field}
                onChange={(e) => setSortConfig({ ...sortConfig, field: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700"
              >
                <option value="interestingness">有趣度</option>
                <option value="betweenness">中介中心性</option>
                <option value="closeness">接近中心性</option>
                <option value="views">播放量</option>
              </select>
            </div>

            {/* 排序方向 */}
            <div>
              <label className="block text-sm font-medium mb-2">排序方向</label>
              <select
                value={sortConfig.direction}
                onChange={(e) => setSortConfig({ ...sortConfig, direction: e.target.value as 'asc' | 'desc' })}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700"
              >
                <option value="desc">高 → 低</option>
                <option value="asc">低 → 高</option>
              </select>
            </div>
          </div>

          {/* 当前排序说明 */}
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
            <p className="text-xs sm:text-sm">
              <span className="font-semibold">当前排序：</span> {getSortDescription()}
            </p>
          </div>
        </div>

        {/* 内容区域 */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">加载中...</div>
        ) : videos.length === 0 ? (
          <div className="text-center py-12 text-gray-500">暂无数据</div>
        ) : (
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg overflow-hidden">
            {/* 表格视图 */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-gray-50 dark:bg-slate-800">
                  <tr>
                    <th className="text-left font-semibold py-3 px-4">排名</th>
                    <th className="text-left font-semibold py-3 px-4">标题</th>
                    <th className="text-right font-semibold py-3 px-4">有趣度</th>
                    <th className="text-right font-semibold py-3 px-4">播放量</th>
                    <th className="text-right font-semibold py-3 px-4">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {videos.map((video, idx) => (
                    <tr key={video.id} className="border-b hover:bg-gray-50 dark:hover:bg-slate-800 transition">
                      <td className="py-3 px-4 font-bold">#{idx + 1}</td>
                      <td className="py-3 px-4">
                        <p className="line-clamp-2 text-sm">{video.title}</p>
                      </td>
                      <td className="text-right py-3 px-4 font-semibold text-purple-600">
                        {(video.interestingness || 0).toFixed(2)}
                      </td>
                      <td className="text-right py-3 px-4">{(video.views / 10000).toFixed(0)}w</td>
                      <td className="text-right py-3 px-4">
                        <Button variant="outline" size="sm">
                          查看
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
