'use client'

import { formatNumber } from '@/lib/utils'
import type { VideoCard } from '@/lib/types'
import Image from 'next/image'

interface VideoCarouselProps {
  videos: VideoCard[]
}

export function VideoCarousel({ videos }: VideoCarouselProps) {
  return (
    <div className="flex gap-3 sm:gap-4 overflow-x-auto pb-4 snap-x snap-mandatory">
      {videos.map((video) => (
        <div
          key={video.id}
          className="flex-shrink-0 w-32 sm:w-40 snap-start group cursor-pointer"
        >
          {/* 缩略图 */}
          <div className="relative w-full h-24 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden mb-2">
            <img
              src={video.thumbnail}
              alt={video.title}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
            />
            {/* 播放量浮层 */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>

          {/* 标题 */}
          <h4 className="text-sm font-semibold line-clamp-2 mb-1 group-hover:text-primary transition">
            {video.title}
          </h4>

          {/* 频道和播放量 */}
          <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
            <p className="line-clamp-1">{video.channelName}</p>
            <p className="font-semibold text-gray-900 dark:text-gray-100">
              {formatNumber(video.views)}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
