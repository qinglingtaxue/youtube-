'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/lib/stores/searchStore'
import { useToast } from '@/components/ui/toast'
import { SearchIcon, Loader2 } from 'lucide-react'

export function SearchBox() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const { searchQuery, setSearchQuery, addSearchHistory } = useSearchStore()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    useToast.addToast('搜索中...', 'info', 0)

    try {
      // 保存到历史记录
      addSearchHistory(searchQuery)

      // 跳转到搜索结果页
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`)
    } catch (error) {
      useToast.addToast('搜索出错，请稍后重试', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSearch} className="w-full">
      <div className="relative flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            placeholder="输入关键词搜索（如：养生、太极、中医）"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-3 text-base"
            disabled={loading}
            autoFocus
          />
        </div>
        <Button
          type="submit"
          disabled={!searchQuery.trim() || loading}
          className="px-4 sm:px-6"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <span className="hidden sm:inline">搜索</span>
          )}
          {!loading && <SearchIcon className="sm:hidden w-4 h-4" />}
        </Button>
      </div>
    </form>
  )
}
