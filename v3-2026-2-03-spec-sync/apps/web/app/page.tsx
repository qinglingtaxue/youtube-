import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-20">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">🎥 YouTube 内容分析工具</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
            帮助创作者发现市场机会、了解频道表现、制定增长策略
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-12">
          <Link href="/insights" className="w-full">
            <Button className="w-full h-32 text-lg flex flex-col items-center justify-center gap-3 bg-blue-600 hover:bg-blue-700">
              <span className="text-3xl">🔍</span>
              <span>全局认识</span>
              <span className="text-sm font-normal">看懂市场全景</span>
            </Button>
          </Link>

          <Link href="/insights/arbitrage" className="w-full">
            <Button className="w-full h-32 text-lg flex flex-col items-center justify-center gap-3 bg-purple-600 hover:bg-purple-700">
              <span className="text-3xl">💰</span>
              <span>套利分析</span>
              <span className="text-sm font-normal">发现市场机会</span>
            </Button>
          </Link>

          <Link href="/insights/report" className="w-full">
            <Button className="w-full h-32 text-lg flex flex-col items-center justify-center gap-3 bg-green-600 hover:bg-green-700">
              <span className="text-3xl">📊</span>
              <span>信息报告</span>
              <span className="text-sm font-normal">策略建议与洞察</span>
            </Button>
          </Link>

          <Link href="/insights/creator-center" className="w-full">
            <Button className="w-full h-32 text-lg flex flex-col items-center justify-center gap-3 bg-orange-600 hover:bg-orange-700">
              <span className="text-3xl">🎬</span>
              <span>创作者中心</span>
              <span className="text-sm font-normal">频道诊断与改进</span>
            </Button>
          </Link>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-lg p-8 shadow-lg">
          <h2 className="text-2xl font-bold mb-4">✨ 功能概览</h2>
          <ul className="space-y-3 text-gray-700 dark:text-gray-300">
            <li className="flex items-start gap-3">
              <span className="text-2xl">📈</span>
              <div>
                <strong>全局认识</strong> - 8 种图表类型覆盖市场全景，理解行业现状
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-2xl">🔬</span>
              <div>
                <strong>套利分析</strong> - 使用网络分析算法发现被低估的内容和频道
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-2xl">💡</span>
              <div>
                <strong>信息报告</strong> - 推理链式报告，清晰的论证和可执行建议
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-2xl">🎯</span>
              <div>
                <strong>创作者中心</strong> - 频道诊断报告，对标市场基线，了解改进方向
              </div>
            </li>
          </ul>
        </div>

        <div className="mt-12 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>Phase 4-8 已完成 | 版本 v3</p>
        </div>
      </div>
    </div>
  )
}
