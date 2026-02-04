'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { DynamicPagination } from '@/lib/dynamic-imports'
import { useSearchStore } from '@/lib/stores/searchStore'
import { useToast } from '@/components/ui/toast'
import { formatNumber } from '@/lib/utils'
import type { SearchResponse, Video } from '@/lib/types'
import { Loader2, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

const PAGE_SIZE = 20

export default function SearchResultsPage() {
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''
  const pageParam = parseInt(searchParams.get('page') || '1')
  const { filters, sortConfig } = useSearchStore()
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [currentPage, setCurrentPage] = useState(pageParam)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!query) return

    const fetchResults = async () => {
      try {
        setLoading(true)
        setError(null)
        useToast.addToast('搜索中...', 'info', 0)

        const res = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query,
            filters,
            sortConfig,
            page: currentPage,
            limit: PAGE_SIZE,
          }),
        })

        if (!res.ok) {
          throw new Error('搜索失败')
        }

        const data = await res.json()
        setResults(data.data)
        useToast.addToast(`找到 ${data.data.total} 条结果`, 'success')

        // 滚动到页面顶部
        window.scrollTo({ top: 0, behavior: 'smooth' })
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : '搜索失败'
        setError(errorMsg)
        useToast.addToast(errorMsg, 'error')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [query, currentPage, filters, sortConfig])

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p>搜索中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Button asChild>
            <Link href="/">返回首页</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 返回按钮 */}
        <Button variant="ghost" asChild className="mb-6">
          <Link href="/" className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            返回首页
          </Link>
        </Button>

        {/* 搜索信息 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            搜索结果: "<span className="text-primary">{query}</span>"
          </h1>
          {results && (
            <p className="text-gray-600 dark:text-gray-400">
              共 {results.total} 条结果
            </p>
          )}
        </div>

        {/* 排序控制面板 */}
        {results && (
          <SortPanel />
        )}

        {/* 结果列表 */}
        {results && results.results.length > 0 ? (
          <>
            <div className="space-y-4">
              {results.results.map((video, index) => (
                <VideoResultItem
                  key={video.id}
                  video={video}
                  rank={(currentPage - 1) * PAGE_SIZE + index + 1}
                />
              ))}
            </div>

            {/* 分页 */}
            <DynamicPagination
              currentPage={currentPage}
              totalPages={Math.ceil(results.total / PAGE_SIZE)}
              onPageChange={handlePageChange}
              isLoading={loading}
            />
          </>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              未找到相关视频
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function SortPanel() {
  const { sortConfig, updateSort, getSortDescription } = useSearchStore()

  const TIME_RANGES = [
    { value: '24h', label: '24小时内' },
    { value: '7d', label: '7天内' },
    { value: '30d', label: '30天内' },
    { value: '1y', label: '1年内' },
    { value: 'all', label: '不限' },
  ]

  const SORT_FIELDS = [
    { value: 'views', label: '播放量' },
    { value: 'likes', label: '点赞数' },
    { value: 'comments', label: '评论数' },
    { value: 'avgDailyViews', label: '日均播放' },
    { value: 'duration', label: '时长' },
  ]

  const DIRECTIONS = [
    { value: 'desc', label: '高→低' },
    { value: 'asc', label: '低→高' },
  ]

  return (
    <div className="mb-6 p-4 sm:p-6 bg-white dark:bg-slate-900 rounded-lg border border-gray-200 dark:border-gray-800">
      <div className="mb-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* 时间范围 */}
          <div>
            <label className="text-xs font-semibold text-gray-600 dark:text-gray-400 block mb-2">
              时间范围
            </label>
            <select
              value={sortConfig.timeRange}
              onChange={(e) => updateSort({ timeRange: e.target.value as any })}
              className="w-full px-3 py-2 text-sm border rounded-md bg-white dark:bg-slate-800 border-gray-300 dark:border-gray-700"
            >
              {TIME_RANGES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {/* 排序字段 */}
          <div>
            <label className="text-xs font-semibold text-gray-600 dark:text-gray-400 block mb-2">
              排序字段
            </label>
            <select
              value={sortConfig.sortField}
              onChange={(e) => updateSort({ sortField: e.target.value as any })}
              className="w-full px-3 py-2 text-sm border rounded-md bg-white dark:bg-slate-800 border-gray-300 dark:border-gray-700"
            >
              {SORT_FIELDS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {/* 排序方向 */}
          <div>
            <label className="text-xs font-semibold text-gray-600 dark:text-gray-400 block mb-2">
              排序方向
            </label>
            <select
              value={sortConfig.direction}
              onChange={(e) => updateSort({ direction: e.target.value as any })}
              className="w-full px-3 py-2 text-sm border rounded-md bg-white dark:bg-slate-800 border-gray-300 dark:border-gray-700"
            >
              {DIRECTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 当前排序说明 */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-900">
        <p className="text-xs sm:text-sm text-blue-900 dark:text-blue-100">
          <span className="font-semibold">当前：</span>
          {getSortDescription()}
        </p>
      </div>
    </div>
  )
}

function VideoResultItem({ video, rank }: { video: Video; rank: number }) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg shadow overflow-hidden hover:shadow-lg transition">
      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 p-3 sm:p-4">
        {/* 排名 */}
        <div className="flex-shrink-0 flex items-center justify-center sm:w-12">
          <div className="text-xl sm:text-2xl font-bold text-primary">#{rank}</div>
        </div>

        {/* 缩略图 */}
        <div className="flex-shrink-0 w-full sm:w-40 h-24 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden">
          <img
            src={video.thumbnail}
            alt={video.title}
            className="w-full h-full object-cover"
          />
        </div>

        {/* 内容 */}
        <div className="flex-1">
          <h3 className="font-semibold mb-2 line-clamp-2 text-sm sm:text-base hover:text-primary transition">
            {video.title}
          </h3>

          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-2 sm:mb-3 line-clamp-1">
            {video.channelName} · {formatNumber(video.channelSubscribers)} 订阅
          </p>

          {/* 统计数据 */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 text-xs mb-2">
            <div>
              <p className="text-gray-500 dark:text-gray-400">播放</p>
              <p className="font-semibold">{formatNumber(video.views)}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">点赞</p>
              <p className="font-semibold">{formatNumber(video.likes)}</p>
            </div>
            <div className="hidden sm:block">
              <p className="text-gray-500 dark:text-gray-400">评论</p>
              <p className="font-semibold">{formatNumber(video.comments)}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">时长</p>
              <p className="font-semibold">
                {Math.floor(video.duration / 60)}:{String(video.duration % 60).padStart(2, '0')}
              </p>
            </div>
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400">
            {new Date(video.publishedAt).toLocaleDateString('zh-CN')}
          </p>
        </div>
      </div>
    </div>
  )
}
