'use client'

import { formatNumber } from '@/lib/utils'
import type { ChannelRow } from '@/lib/types'

interface ChannelTableProps {
  channels: ChannelRow[]
}

export function ChannelTable({ channels }: ChannelTableProps) {
  // 桌面端表格视图
  const TableView = () => (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b">
          <tr>
            <th className="text-left font-semibold py-3 px-4">频道名</th>
            <th className="text-right font-semibold py-3 px-4">订阅数</th>
            <th className="text-right font-semibold py-3 px-4">平均播放</th>
            <th className="text-right font-semibold py-3 px-4">效率分数</th>
            <th className="text-right font-semibold py-3 px-4">最近更新</th>
          </tr>
        </thead>
        <tbody>
          {channels.map((channel, index) => (
            <tr
              key={channel.id}
              className="border-b hover:bg-gray-50 dark:hover:bg-gray-800 transition"
            >
              {/* 排名 + 频道名 */}
              <td className="py-3 px-4">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-primary w-6">
                    {index + 1}
                  </span>
                  <span className="font-medium">{channel.name}</span>
                </div>
              </td>

              {/* 订阅数 */}
              <td className="text-right py-3 px-4">
                <span className="text-gray-700 dark:text-gray-300">
                  {formatNumber(channel.subscribers)}
                </span>
              </td>

              {/* 平均播放 */}
              <td className="text-right py-3 px-4">
                <span className="text-gray-700 dark:text-gray-300">
                  {formatNumber(channel.avgViews)}
                </span>
              </td>

              {/* 效率分数（中介中心性 ÷ 程度中心性） */}
              <td className="text-right py-3 px-4">
                <span className="font-semibold text-primary">
                  {channel.efficiencyScore.toFixed(1)}x
                </span>
              </td>

              {/* 最近更新 */}
              <td className="text-right py-3 px-4 text-gray-600 dark:text-gray-400">
                {channel.lastUpdated}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )

  // 移动端卡片视图
  const CardView = () => (
    <div className="space-y-3">
      {channels.map((channel, index) => (
        <div
          key={channel.id}
          className="p-4 border rounded-lg bg-white dark:bg-gray-800 hover:shadow-md dark:hover:bg-gray-750 transition"
        >
          <div className="flex items-start gap-3 mb-3">
            <span className="text-xl font-bold text-primary flex-shrink-0">
              {index + 1}
            </span>
            <span className="font-semibold line-clamp-2 flex-1">{channel.name}</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                订阅数
              </p>
              <p className="font-semibold">
                {formatNumber(channel.subscribers)}
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                平均播放
              </p>
              <p className="font-semibold">
                {formatNumber(channel.avgViews)}
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                效率分数
              </p>
              <p className="font-semibold text-primary">
                {channel.efficiencyScore.toFixed(1)}x
              </p>
            </div>

            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                最近更新
              </p>
              <p className="text-gray-600 dark:text-gray-400 text-xs">
                {channel.lastUpdated}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )

  return (
    <>
      {/* 桌面端显示表格 */}
      <div className="hidden md:block">
        <TableView />
      </div>

      {/* 移动端显示卡片 */}
      <div className="md:hidden">
        <CardView />
      </div>
    </>
  )
}
