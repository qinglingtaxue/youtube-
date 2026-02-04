'use client'

import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  isLoading?: boolean
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  isLoading,
}: PaginationProps) {
  // 生成页码列表（最多显示 7 个页码）
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const maxVisible = 7

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1)

      if (currentPage > 4) {
        pages.push('...')
      }

      const start = Math.max(2, currentPage - 2)
      const end = Math.min(totalPages - 1, currentPage + 2)

      for (let i = start; i <= end; i++) {
        pages.push(i)
      }

      if (currentPage < totalPages - 3) {
        pages.push('...')
      }

      pages.push(totalPages)
    }

    return pages
  }

  const pages = getPageNumbers()

  // 移动端简化版本（仅显示上一页/下一页）
  const MobileView = () => (
    <div className="flex items-center justify-between gap-2 mt-8">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1 || isLoading}
        className="gap-1"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="hidden sm:inline">上一页</span>
      </Button>

      <div className="text-sm text-gray-600 dark:text-gray-400">
        {currentPage} / {totalPages}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages || isLoading}
        className="gap-1"
      >
        <span className="hidden sm:inline">下一页</span>
        <ChevronRight className="w-4 h-4" />
      </Button>
    </div>
  )

  // 桌面端完整版本
  const DesktopView = () => (
    <div className="flex items-center justify-center gap-2 mt-8 flex-wrap">
      {/* 上一页 */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1 || isLoading}
        className="gap-1"
      >
        <ChevronLeft className="w-4 h-4" />
        上一页
      </Button>

      {/* 页码 */}
      <div className="flex items-center gap-1">
        {pages.map((page, index) => {
          if (page === '...') {
            return (
              <span key={`ellipsis-${index}`} className="px-2 text-gray-500">
                ...
              </span>
            )
          }

          const pageNum = page as number
          const isActive = pageNum === currentPage

          return (
            <Button
              key={pageNum}
              variant={isActive ? 'default' : 'outline'}
              size="sm"
              onClick={() => onPageChange(pageNum)}
              disabled={isLoading}
              className="min-w-10"
            >
              {pageNum}
            </Button>
          )
        })}
      </div>

      {/* 下一页 */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages || isLoading}
        className="gap-1"
      >
        下一页
        <ChevronRight className="w-4 h-4" />
      </Button>

      {/* 页码信息 */}
      <div className="ml-4 text-sm text-gray-600 dark:text-gray-400">
        第 {currentPage} / {totalPages} 页
      </div>
    </div>
  )

  return (
    <>
      <div className="md:hidden">
        <MobileView />
      </div>
      <div className="hidden md:block">
        <DesktopView />
      </div>
    </>
  )
}
