import { Suspense } from 'react'
import { SearchBox } from '@/components/home/SearchBox'
import { SearchHistory } from '@/components/home/SearchHistory'
import { FilterPanel } from '@/components/home/FilterPanel'
import { VideoCarousel } from '@/components/home/VideoCarousel'
import { VideoCarouselSkeleton } from '@/components/home/VideoCarouselSkeleton'
import { ChannelTable } from '@/components/home/ChannelTable'
import { ChannelTableSkeleton } from '@/components/home/ChannelTableSkeleton'
import { DataOverview } from '@/components/home/DataOverview'
import { DataOverviewSkeleton } from '@/components/home/DataOverviewSkeleton'
import { Button } from '@/components/ui/button'
import { BarChart3, Building2, TrendingUp } from 'lucide-react'
import Link from 'next/link'
import {
  fetchTrendingVideos,
  fetchTrendingChannels,
  fetchAnalyticsOverview,
} from '@/lib/api'

// ISR: 每小时重新生成
export const revalidate = 3600

// 异步数据获取函数（服务端）
async function TrendingVideosSection() {
  try {
    const res = await fetchTrendingVideos(5, '7d')
    return <VideoCarousel videos={res.data.videos} />
  } catch (error) {
    return <div className="text-center py-8 text-red-600">加载失败，请刷新页面</div>
  }
}

async function TrendingChannelsSection() {
  try {
    const res = await fetchTrendingChannels(3)
    return <ChannelTable channels={res.data.channels} />
  } catch (error) {
    return <div className="text-center py-8 text-red-600">加载失败，请刷新页面</div>
  }
}

async function AnalyticsSection() {
  try {
    const res = await fetchAnalyticsOverview()
    return <DataOverview analytics={res.data} />
  } catch (error) {
    return <div className="text-center py-8 text-red-600">加载失败，请刷新页面</div>
  }
}

const FEATURES = [
  {
    id: 'videos',
    icon: BarChart3,
    title: '📊 视频列表',
    description: '按播放量/互动率筛选竞品视频',
    link: '/videos',
  },
  {
    id: 'channels',
    icon: Building2,
    title: '🏢 频道排行',
    description: '找高效率频道，对标学习对象',
    link: '/channels',
  },
  {
    id: 'trends',
    icon: TrendingUp,
    title: '🔥 话题趋势',
    description: '发现新兴话题，Google Trends 集成',
    link: '/trends',
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-3 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* 标题 */}
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-3xl sm:text-5xl font-bold mb-3 sm:mb-4">
            YouTube 竞品分析工具
          </h1>
          <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400">
            数据驱动选题发现，市场洞察与套利机会
          </p>
        </div>

        {/* 搜索区 */}
        <section className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-4 sm:p-6 mb-6 sm:mb-8 animate-fade-in">
          <SearchBox />

          <div className="mt-4">
            <SearchHistory />
          </div>

          <div className="mt-4">
            <FilterPanel />
          </div>
        </section>

        {/* 三大功能入口 */}
        <section className="mb-8 sm:mb-12">
          <h2 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6">核心功能</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FEATURES.map((feature) => {
              const Icon = feature.icon
              return (
                <div
                  key={feature.id}
                  className="bg-white dark:bg-slate-900 rounded-lg shadow-md p-6 hover:shadow-lg transition hover:-translate-y-1"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <Icon className="w-6 h-6 text-primary" />
                    <h3 className="text-lg font-semibold">{feature.title}</h3>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {feature.description}
                  </p>
                  <Button asChild variant="outline" className="w-full">
                    <Link href={feature.link}>进入 →</Link>
                  </Button>
                </div>
              )
            })}
          </div>
        </section>

        {/* 快速发现区 */}
        <section className="mb-8 sm:mb-12">
          <h2 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6">快速发现</h2>

          {/* 本周爆款 */}
          <div className="mb-8 sm:mb-12">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">🔥 本周爆款 (播放量 Top 5)</h3>
              <Link href="/videos?sort=views&time=7d" className="text-sm text-blue-600 hover:underline">
                查看全部 →
              </Link>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-lg shadow p-4 sm:p-6">
              <Suspense fallback={<VideoCarouselSkeleton />}>
                <TrendingVideosSection />
              </Suspense>
            </div>
          </div>

          {/* 黑马频道 */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">🏆 黑马频道 (低订阅高播放)</h3>
              <Link href="/channels?type=high-efficiency" className="text-sm text-blue-600 hover:underline">
                查看全部 →
              </Link>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-lg shadow p-4 sm:p-6">
              <Suspense fallback={<ChannelTableSkeleton />}>
                <TrendingChannelsSection />
              </Suspense>
            </div>
          </div>
        </section>

        {/* 数据概览 */}
        <section className="border-t pt-6 sm:pt-8">
          <h2 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6">📈 数据概览</h2>
          <Suspense fallback={<DataOverviewSkeleton />}>
            <AnalyticsSection />
          </Suspense>
        </section>
      </div>
    </div>
  )
}
