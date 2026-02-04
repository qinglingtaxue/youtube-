'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface TabItem {
  id: string
  label: string
  emoji: string
  question: string
}

interface OverviewData {
  metrics: Record<string, number | string>
  viewsDistribution: Array<{ range: string; count: number }>
  publishTrend: Array<{ month: string; videos: number; avgViews: number }>
  timeWindowDistribution: Array<{ window: string; count: number }>
  weekDayDistribution: Array<{ day: string; count: number }>
  durationDistribution: Array<{ label: string; value: number; percentage: number }>
  viewsSegmentation: Array<{ label: string; value: number; percentage: number }>
  languageDistribution: Array<{ language: string; count: number; percentage: number }>
  channelSizeDistribution: Array<{ label: string; value: number; percentage: number }>
  channelConcentration: Array<{ rank: string; views: number }>
  topChannels: Array<{ rank: number; name: string; subscribers: string; videos: number; avgViews: number }>
  countryDistribution: Array<{ country: string; count: number; percentage: number }>
}

interface TabGroup {
  name: string
  tabs: TabItem[]
}

export default function GlobalOverviewPage() {
  const [activeTab, setActiveTab] = useState<string>('market-size')
  const [timeRange, setTimeRange] = useState<string>('7d')
  const [data, setData] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)

  const tabGroups: TabGroup[] = [
    {
      name: '宏观概览',
      tabs: [
        { id: 'market-size', label: '市场规模', emoji: '📊', question: '有多大？' },
        { id: 'time-distribution', label: '时间分布', emoji: '📅', question: '什么时候发？' },
      ],
    },
    {
      name: '内容与参与者',
      tabs: [
        { id: 'content-distribution', label: '内容分布', emoji: '📝', question: '什么样？' },
        { id: 'language-distribution', label: '语言分布', emoji: '🌐', question: '什么语言？' },
        { id: 'channel-landscape', label: '频道格局', emoji: '👥', question: '谁在做？' },
        { id: 'country-distribution', label: '国家分布', emoji: '🌍', question: '哪里的？' },
      ],
    },
  ]

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/insights/overview?timeRange=${timeRange}`)
        if (res.ok) {
          const result = await res.json()
          setData(result.data)
        }
      } catch (error) {
        console.error('Failed to fetch overview data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [timeRange])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* 页面头 */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">🔍 全局认识</h1>
          <p className="text-gray-600 dark:text-gray-400">看懂市场数据分布 · 建立对行业的整体认知</p>
        </div>

        {/* 时间范围筛选 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-4 sm:p-6 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">时间范围：</label>
            <div className="flex gap-2 flex-wrap">
              {['7d', '30d', '90d', 'all'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    timeRange === range
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {range === '7d' && '7 天内'}
                  {range === '30d' && '30 天内'}
                  {range === '90d' && '90 天内'}
                  {range === 'all' && '全部时间'}
                </button>
              ))}
            </div>
          </div>
          {data && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
              当前显示：{timeRange === '7d' && '过去 7 天'}{timeRange === '30d' && '过去 30 天'}
              {timeRange === '90d' && '过去 90 天'}
              {timeRange === 'all' && '全部时间'}的数据（共 {data.metrics.totalVideos} 条视频）
            </p>
          )}
        </div>

        {/* Tab 分组 */}
        <div className="space-y-6">
          {tabGroups.map((group) => (
            <div key={group.name}>
              {/* 分组标题 */}
              <h2 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">{group.name}</h2>

              {/* 该分组的 Tabs */}
              <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-4 sm:p-6 mb-6">
                <div className="flex gap-2 flex-wrap mb-6">
                  {group.tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
                        activeTab === tab.id
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200'
                      }`}
                    >
                      <span>{tab.emoji}</span>
                      <span>{tab.label}</span>
                    </button>
                  ))}
                </div>

                {/* 活跃 Tab 的问题说明 */}
                {tabGroups
                  .flatMap((g) => g.tabs)
                  .find((t) => t.id === activeTab) && (
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800 mb-6">
                    <p className="text-sm text-blue-900 dark:text-blue-100">
                      <span className="font-semibold">用户问题：</span>{' '}
                      {tabGroups.flatMap((g) => g.tabs).find((t) => t.id === activeTab)?.question}
                    </p>
                  </div>
                )}

                {/* Tab 内容 */}
                <div className="space-y-6">
                  {activeTab === 'market-size' && data && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">关键指标</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">总视频数</p>
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">{data.metrics.totalVideos}</p>
                        </div>
                        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">总频道数</p>
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">{data.metrics.totalChannels}</p>
                        </div>
                        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">总播放量</p>
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {typeof data.metrics.totalViews === 'number'
                              ? (data.metrics.totalViews / 1000000).toFixed(1) + 'M'
                              : data.metrics.totalViews}
                          </p>
                        </div>
                        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">人均播放</p>
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {typeof data.metrics.avgViewsPerVideo === 'number'
                              ? (data.metrics.avgViewsPerVideo / 1000).toFixed(1) + 'k'
                              : data.metrics.avgViewsPerVideo}
                          </p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-4">播放量分布</h4>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          {data.viewsDistribution.map((item, idx) => (
                            <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">{item.range}</p>
                              <p className="text-lg font-bold text-gray-900 dark:text-white">{item.count}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-4">发布趋势（过去 12 个月）</h4>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          {data.publishTrend.slice(0, 4).map((item, idx) => (
                            <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">{item.month}</p>
                              <p className="text-lg font-bold text-gray-900 dark:text-white">{item.videos} 个</p>
                              <p className="text-xs text-gray-500 mt-1">{(item.avgViews / 1000).toFixed(0)}k 播放</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'time-distribution' && data && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">时间分布分析</h3>

                      <div>
                        <h4 className="font-semibold mb-4">按时间窗口分布</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          {data.timeWindowDistribution.map((item, idx) => (
                            <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium">{item.window}</span>
                                <span className="font-bold text-blue-600 dark:text-blue-400">{item.count}</span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                                <div
                                  className="bg-blue-500 h-2 rounded-full"
                                  style={{ width: `${(item.count / 1000) * 100}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-4">按周日分布</h4>
                        <div className="grid grid-cols-2 sm:grid-cols-7 gap-2">
                          {data.weekDayDistribution.map((item, idx) => (
                            <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center">
                              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">{item.day}</p>
                              <p className="text-lg font-bold text-gray-900 dark:text-white">{item.count}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'content-distribution' && data && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">内容特征分析</h3>

                      <div>
                        <h4 className="font-semibold mb-4">视频时长分布</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                          {data.durationDistribution.map((item, idx) => (
                            <div key={idx} className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium">{item.label}</span>
                                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{item.percentage}%</span>
                              </div>
                              <p className="text-2xl font-bold text-gray-900 dark:text-white">{item.value}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-4">播放量分层</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                          {data.viewsSegmentation.map((item, idx) => (
                            <div key={idx} className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium">{item.label}</span>
                                <span className="text-sm font-bold text-green-600 dark:text-green-400">{item.percentage}%</span>
                              </div>
                              <p className="text-2xl font-bold text-gray-900 dark:text-white">{item.value}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'language-distribution' && data && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">语言分布分析</h3>
                      <div className="space-y-3">
                        {data.languageDistribution.map((item, idx) => (
                          <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{item.language}</span>
                              <span className="font-bold text-blue-600 dark:text-blue-400">{item.percentage}%</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
                              <div
                                className="bg-gradient-to-r from-blue-400 to-blue-600 h-3 rounded-full"
                                style={{ width: `${item.percentage}%` }}
                              />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.count} 个视频</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeTab === 'channel-landscape' && data && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">频道生态分析</h3>

                      <div>
                        <h4 className="font-semibold mb-4">频道规模分布</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          {data.channelSizeDistribution.map((item, idx) => (
                            <div key={idx} className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium">{item.label}</span>
                                <span className="text-sm font-bold text-purple-600 dark:text-purple-400">{item.percentage}%</span>
                              </div>
                              <p className="text-2xl font-bold text-gray-900 dark:text-white">{item.value}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-4">播放量集中度</h4>
                        <div className="space-y-3">
                          {data.channelConcentration.map((item, idx) => (
                            <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium">{item.rank}</span>
                                <span className="font-bold text-orange-600 dark:text-orange-400">
                                  {(item.views / 1000000).toFixed(1)}M
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                                <div
                                  className="bg-orange-500 h-2 rounded-full"
                                  style={{ width: `${(item.views / 8200000) * 100}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-4">Top 10 频道排名</h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="border-b bg-gray-50 dark:bg-slate-800">
                              <tr>
                                <th className="text-left font-semibold py-3 px-4">排名</th>
                                <th className="text-left font-semibold py-3 px-4">频道名</th>
                                <th className="text-right font-semibold py-3 px-4">订阅</th>
                                <th className="text-right font-semibold py-3 px-4">视频数</th>
                                <th className="text-right font-semibold py-3 px-4">人均播放</th>
                              </tr>
                            </thead>
                            <tbody>
                              {data.topChannels.map((channel) => (
                                <tr key={channel.rank} className="border-b hover:bg-gray-50 dark:hover:bg-slate-800">
                                  <td className="py-3 px-4 font-bold">#{channel.rank}</td>
                                  <td className="py-3 px-4">{channel.name}</td>
                                  <td className="text-right py-3 px-4">{channel.subscribers}</td>
                                  <td className="text-right py-3 px-4">{channel.videos}</td>
                                  <td className="text-right py-3 px-4 font-semibold text-blue-600 dark:text-blue-400">
                                    {(channel.avgViews / 1000).toFixed(0)}k
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'country-distribution' && data && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold">国家/地区分布</h3>
                      <div className="space-y-3">
                        {data.countryDistribution.map((item, idx) => (
                          <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">{item.country}</span>
                              <span className="font-bold text-green-600 dark:text-green-400">{item.percentage}%</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
                              <div
                                className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full"
                                style={{ width: `${item.percentage}%` }}
                              />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.count} 个视频</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 行动入口 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 sm:p-8 mb-6">
          <h2 className="text-xl font-semibold mb-4">📊 下一步行动</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Link href="/insights/arbitrage" className="w-full">
              <Button variant="outline" className="w-full justify-center">
                💰 查看套利分析
              </Button>
            </Link>
            <Link href="/insights/report" className="w-full">
              <Button variant="outline" className="w-full justify-center">
                📋 查看信息报告
              </Button>
            </Link>
            <Link href="/insights/creator-center" className="w-full">
              <Button variant="outline" className="w-full justify-center">
                🎬 创作者诊断中心
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
