import { Skeleton } from '@/components/ui/skeleton'

export function ChannelTableSkeleton() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="border-b">
          <tr>
            <th className="text-left py-3 px-4">
              <Skeleton className="h-4 w-24" />
            </th>
            <th className="text-right py-3 px-4">
              <Skeleton className="h-4 w-16 ml-auto" />
            </th>
            <th className="text-right py-3 px-4">
              <Skeleton className="h-4 w-16 ml-auto" />
            </th>
            <th className="text-right py-3 px-4">
              <Skeleton className="h-4 w-16 ml-auto" />
            </th>
            <th className="text-right py-3 px-4">
              <Skeleton className="h-4 w-16 ml-auto" />
            </th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 3 }).map((_, i) => (
            <tr key={i} className="border-b">
              <td className="py-3 px-4">
                <Skeleton className="h-4 w-32" />
              </td>
              <td className="text-right py-3 px-4">
                <Skeleton className="h-4 w-20 ml-auto" />
              </td>
              <td className="text-right py-3 px-4">
                <Skeleton className="h-4 w-20 ml-auto" />
              </td>
              <td className="text-right py-3 px-4">
                <Skeleton className="h-4 w-16 ml-auto" />
              </td>
              <td className="text-right py-3 px-4">
                <Skeleton className="h-4 w-20 ml-auto" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
