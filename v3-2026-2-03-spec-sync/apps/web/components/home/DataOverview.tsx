'use client'

import { formatNumber, formatRelativeTime } from '@/lib/utils'
import type { AnalyticsOverview } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { RefreshCw } from 'lucide-react'
import { useState } from 'react'

interface DataOverviewProps {
  analytics: AnalyticsOverview
}

export function DataOverview({ analytics }: DataOverviewProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    useToast.addToast('数据刷新中...', 'info', 0)
    try {
      // 重新获取数据
      const res = await fetch('/api/analytics/overview')
      if (res.ok) {
        useToast.addToast('数据已更新', 'success')
      } else {
        useToast.addToast('数据刷新失败', 'error')
      }
    } catch (error) {
      console.error('刷新失败:', error)
      useToast.addToast('数据刷新失败，请稍后重试', 'error')
    } finally {
      setIsRefreshing(false)
    }
  }

  const stats = [
    {
      icon: '📹',
      label: '视频总数',
      value: formatNumber(analytics.totalVideos),
      color: 'from-blue-500 to-blue-600',
    },
    {
      icon: '🎬',
      label: '频道总数',
      value: formatNumber(analytics.totalChannels),
      color: 'from-purple-500 to-purple-600',
    },
    {
      icon: '🏷️',
      label: '话题总数',
      value: formatNumber(analytics.totalTopics),
      color: 'from-pink-500 to-pink-600',
    },
    {
      icon: '⏱️',
      label: '最后采集',
      value: formatRelativeTime(analytics.lastCollectedAt),
      color: 'from-green-500 to-green-600',
    },
  ]

  return (
    <div className="space-y-4">
      {/* 刷新按钮 */}
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? '刷新中...' : '刷新数据'}
        </Button>
      </div>

      {/* 统计卡片网格 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white dark:bg-slate-900 rounded-lg shadow p-4 hover:shadow-lg transition"
          >
            {/* 图标 */}
            <div className="text-3xl mb-2">{stat.icon}</div>

            {/* 标签 */}
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
              {stat.label}
            </p>

            {/* 数值 */}
            <p className="text-2xl font-bold">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* 信息提示 */}
      <p className="text-xs text-gray-500 dark:text-gray-500 text-center">
        数据最后更新于 {new Date(analytics.lastCollectedAt).toLocaleString('zh-CN')}
      </p>
    </div>
  )
}
