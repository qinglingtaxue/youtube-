'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/lib/stores/searchStore'
import { ChevronDown, ChevronUp } from 'lucide-react'

const TIME_RANGES = [
  { value: '24h', label: '24小时内' },
  { value: '7d', label: '7天内' },
  { value: '30d', label: '30天内' },
  { value: '1y', label: '1年内' },
  { value: 'all', label: '不限' },
]

const DURATIONS = [
  { value: 'all', label: '全部' },
  { value: '<4min', label: '短视频 (<4分钟)' },
  { value: '4-20min', label: '中视频 (4-20分钟)' },
  { value: '>20min', label: '长视频 (>20分钟)' },
]

const CHANNEL_SIZES = [
  { value: 'all', label: '不限' },
  { value: '<10k', label: '小频道 (<1万)' },
  { value: '10-100k', label: '中频道 (1-100万)' },
  { value: '100-1M', label: '大频道 (100万-1000万)' },
  { value: '>1M', label: '超大 (>1000万)' },
]

const CONTENT_TAGS = ['教程', '养生功法', '食疗', '中医', '冥想', '评测']

export function FilterPanel() {
  const { isFilterOpen, toggleFilter, filters, updateFilters, resetFilters } =
    useSearchStore()

  return (
    <div className="space-y-2">
      {/* 展开/折叠按钮 */}
      <button
        onClick={toggleFilter}
        className="flex items-center gap-2 text-sm text-primary hover:opacity-80 transition"
      >
        {isFilterOpen ? (
          <>
            <ChevronUp className="w-4 h-4" />
            收起筛选条件
          </>
        ) : (
          <>
            <ChevronDown className="w-4 h-4" />
            展开筛选条件
          </>
        )}
      </button>

      {/* 筛选面板 */}
      {isFilterOpen && (
        <div className="mt-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-900 space-y-6 animate-slide-up">
          {/* 时间范围 */}
          <div>
            <h4 className="text-sm font-semibold mb-3">时间范围</h4>
            <div className="space-y-2">
              {TIME_RANGES.map((range) => (
                <label key={range.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="timeRange"
                    value={range.value}
                    checked={filters.timeRange === range.value}
                    onChange={(e) => updateFilters({ timeRange: e.target.value as any })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">{range.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 时长 */}
          <div>
            <h4 className="text-sm font-semibold mb-3">时长 (YouTube原生)</h4>
            <div className="space-y-2">
              {DURATIONS.map((duration) => (
                <label key={duration.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="duration"
                    value={duration.value}
                    checked={filters.duration === duration.value}
                    onChange={(e) => updateFilters({ duration: e.target.value as any })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">{duration.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 频道规模 */}
          <div>
            <h4 className="text-sm font-semibold mb-3">频道规模</h4>
            <div className="space-y-2">
              {CHANNEL_SIZES.map((size) => (
                <label key={size.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="channelSize"
                    value={size.value}
                    checked={filters.channelSize === size.value}
                    onChange={(e) => updateFilters({ channelSize: e.target.value as any })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">{size.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 内容标签 */}
          <div>
            <h4 className="text-sm font-semibold mb-3">内容标签 (可多选)</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {CONTENT_TAGS.map((tag) => (
                <label key={tag} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.contentTags.includes(tag)}
                    onChange={(e) => {
                      const tags = e.target.checked
                        ? [...filters.contentTags, tag]
                        : filters.contentTags.filter((t) => t !== tag)
                      updateFilters({ contentTags: tags })
                    }}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-sm">{tag}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 pt-4 border-t justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={resetFilters}
            >
              重置
            </Button>
            <Button
              size="sm"
              onClick={toggleFilter}
            >
              应用筛选
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
