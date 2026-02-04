import { Skeleton } from '@/components/ui/skeleton'

export function VideoCarouselSkeleton() {
  return (
    <div className="flex gap-4 overflow-hidden pb-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex-shrink-0 w-40">
          {/* 缩略图骨架 */}
          <Skeleton className="w-full h-24 rounded mb-2" />

          {/* 标题骨架 */}
          <Skeleton className="w-full h-4 rounded mb-2" />
          <Skeleton className="w-3/4 h-4 rounded mb-2" />

          {/* 频道骨架 */}
          <Skeleton className="w-2/3 h-3 rounded mb-1" />

          {/* 播放量骨架 */}
          <Skeleton className="w-1/2 h-3 rounded" />
        </div>
      ))}
    </div>
  )
}
