'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/lib/stores/searchStore'
import { X } from 'lucide-react'

export function SearchHistory() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const { searchHistory, setSearchQuery, removeHistoryItem, clearSearchHistory } =
    useSearchStore()

  // 避免 hydration mismatch
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  if (searchHistory.length === 0) {
    return null
  }

  const handleClickHistory = (query: string) => {
    setSearchQuery(query)
    router.push(`/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-sm text-gray-600 dark:text-gray-400">最近搜索：</span>

      {searchHistory.map((item) => (
        <div key={item.id} className="relative group">
          <Badge
            variant="outline"
            className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition"
            onClick={() => handleClickHistory(item.query)}
          >
            {item.query}
          </Badge>
          <button
            onClick={(e) => {
              e.stopPropagation()
              removeHistoryItem(item.id)
            }}
            className="absolute -top-2 -right-2 hidden group-hover:block bg-white dark:bg-gray-900 rounded-full p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label={`删除 ${item.query} 搜索记录`}
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      ))}

      <Button
        variant="ghost"
        size="sm"
        onClick={clearSearchHistory}
        className="ml-2 text-xs"
      >
        清空历史
      </Button>
    </div>
  )
}
