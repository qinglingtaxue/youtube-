'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface RankingItem {
  id: string
  title: string
  channelName?: string
  views: number
  likes?: number
  comments?: number
  interestingness?: number
  betweenness?: number
  closeness?: number
  subscribers?: number
}

interface RankingTableProps {
  data: RankingItem[]
  columns?: ('rank' | 'title' | 'views' | 'interestingness' | 'betweenness' | 'closeness' | 'channel' | 'subscribers')[]
  title?: string
  sortable?: boolean
  onRowClick?: (item: RankingItem) => void
}

export function RankingTable({
  data,
  columns = ['rank', 'title', 'views', 'interestingness'],
  title = '排行榜',
  sortable = true,
  onRowClick,
}: RankingTableProps) {
  const [sortConfig, setSortConfig] = useState<{
    column: string
    direction: 'asc' | 'desc'
  } | null>(null)

  const sortedData = sortConfig
    ? [...data].sort((a, b) => {
        const aValue = a[sortConfig.column as keyof RankingItem]
        const bValue = b[sortConfig.column as keyof RankingItem]

        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue
        }
        return 0
      })
    : data

  const handleSort = (column: string) => {
    if (!sortable) return

    if (sortConfig?.column === column) {
      setSortConfig({
        column,
        direction: sortConfig.direction === 'asc' ? 'desc' : 'asc',
      })
    } else {
      setSortConfig({ column, direction: 'desc' })
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 10000000) return `${(num / 10000000).toFixed(1)}千万`
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}百万`
    if (num >= 10000) return `${(num / 10000).toFixed(0)}万`
    return num.toString()
  }

  const getColumnLabel = (col: string) => {
    const labels: Record<string, string> = {
      rank: '排名',
      title: '标题',
      views: '播放量',
      likes: '点赞',
      comments: '评论',
      interestingness: '有趣度',
      betweenness: '中介中心性',
      closeness: '接近中心性',
      channel: '频道',
      subscribers: '订阅数',
    }
    return labels[col] || col
  }

  const SortIcon = ({ column }: { column: string }) => {
    if (!sortable) return null
    if (sortConfig?.column !== column) return <span className="text-gray-300 ml-1">↕</span>
    return sortConfig.direction === 'desc' ? <ChevronDown className="w-4 h-4 inline ml-1" /> : <ChevronUp className="w-4 h-4 inline ml-1" />
  }

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

      <div className="overflow-x-auto rounded-lg border dark:border-slate-700">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-slate-800 border-b dark:border-slate-700">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className={`text-left font-semibold py-3 px-4 ${
                    sortable && ['views', 'interestingness', 'betweenness', 'closeness', 'subscribers'].includes(col)
                      ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700'
                      : ''
                  }`}
                  onClick={() => handleSort(col)}
                >
                  <span className="flex items-center">
                    {getColumnLabel(col)}
                    <SortIcon column={col} />
                  </span>
                </th>
              ))}
              <th className="text-right font-semibold py-3 px-4">操作</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="text-center py-8 text-gray-500">
                  暂无数据
                </td>
              </tr>
            ) : (
              sortedData.map((item, idx) => (
                <tr
                  key={item.id}
                  className="border-b hover:bg-gray-50 dark:hover:bg-slate-800 transition dark:border-slate-700"
                >
                  {columns.map((col) => {
                    let cellContent: React.ReactNode = ''

                    if (col === 'rank') {
                      cellContent = (
                        <span className="font-bold text-primary">
                          #{idx + 1}
                        </span>
                      )
                    } else if (col === 'title') {
                      cellContent = (
                        <p className="line-clamp-2 max-w-xs">{item.title}</p>
                      )
                    } else if (col === 'channel') {
                      cellContent = item.channelName || '-'
                    } else if (col === 'views') {
                      cellContent = formatNumber(item.views)
                    } else if (col === 'likes' && item.likes !== undefined) {
                      cellContent = formatNumber(item.likes)
                    } else if (col === 'comments' && item.comments !== undefined) {
                      cellContent = formatNumber(item.comments)
                    } else if (col === 'subscribers' && item.subscribers !== undefined) {
                      cellContent = formatNumber(item.subscribers)
                    } else if (col === 'interestingness' && item.interestingness !== undefined) {
                      cellContent = (
                        <span className="font-semibold text-purple-600 dark:text-purple-400">
                          {item.interestingness.toFixed(3)}
                        </span>
                      )
                    } else if (col === 'betweenness' && item.betweenness !== undefined) {
                      cellContent = (
                        <span className="text-blue-600 dark:text-blue-400">
                          {(item.betweenness * 100).toFixed(1)}%
                        </span>
                      )
                    } else if (col === 'closeness' && item.closeness !== undefined) {
                      cellContent = (
                        <span className="text-green-600 dark:text-green-400">
                          {(item.closeness * 100).toFixed(1)}%
                        </span>
                      )
                    }

                    return (
                      <td key={`${item.id}-${col}`} className="py-3 px-4">
                        {cellContent}
                      </td>
                    )
                  })}
                  <td className="text-right py-3 px-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onRowClick?.(item)}
                    >
                      查看
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 分页提示 */}
      <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
        显示 {sortedData.length} 条记录
      </div>
    </div>
  )
}
