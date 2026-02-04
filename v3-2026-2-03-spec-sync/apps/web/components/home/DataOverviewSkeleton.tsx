import { Skeleton } from '@/components/ui/skeleton'

export function DataOverviewSkeleton() {
  return (
    <div className="space-y-4">
      {/* 刷新按钮骨架 */}
      <div className="flex justify-end">
        <Skeleton className="h-10 w-24 rounded" />
      </div>

      {/* 统计卡片骨架 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white dark:bg-slate-900 rounded-lg p-4">
            <Skeleton className="h-8 w-8 rounded mb-2" />
            <Skeleton className="h-3 w-16 rounded mb-2" />
            <Skeleton className="h-6 w-24 rounded" />
          </div>
        ))}
      </div>

      {/* 信息提示骨架 */}
      <Skeleton className="h-3 w-48 rounded mx-auto" />
    </div>
  )
}
