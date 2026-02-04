import type { Metadata } from 'next'
import Script from 'next/script'
import { ThemeProvider } from '@/components/providers/ThemeProvider'
import { ErrorBoundary } from '@/components/providers/ErrorBoundary'
import { Navbar } from '@/components/shared/Navbar'
import { ToastContainer } from '@/components/ui/toast'
import { PerformanceMonitoringClient } from '@/components/providers/PerformanceMonitoringClient'
import { cn } from '@/lib/utils'
import './globals.css'

export const metadata: Metadata = {
  title: 'YouTube 竞品分析工具',
  description: '视频选题数据驱动，发现市场洞察和套利机会',
  keywords: ['YouTube', '视频分析', '竞品研究', '内容创作'],
  authors: [{ name: 'YouTube Analyzer Team' }],
}

export const viewport = 'width=device-width, initial-scale=1, maximum-scale=5'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        {/* 性能监控脚本 */}
        <Script
          src="https://unpkg.com/web-vitals@3/dist/web-vitals.iife.js"
          strategy="lazyOnload"
        />
      </head>
      <body className={cn(
        'min-h-screen bg-background text-foreground',
        'antialiased'
      )}>
        <ThemeProvider>
          <ErrorBoundary>
            {/* 性能监控客户端组件 */}
            <PerformanceMonitoringClient />

            <div className="flex flex-col min-h-screen">
              {/* 导航栏 */}
              <Navbar />

              {/* 主内容 */}
              <main className="flex-1">
                {children}
              </main>

              {/* 页脚 */}
              <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 py-8 mt-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className="text-center text-sm text-gray-600 dark:text-gray-400">
                    <p>
                      © 2026 YouTube 竞品分析工具 ·
                      <a href="https://github.com" className="hover:text-primary ml-1">GitHub</a>
                    </p>
                    <p className="mt-2 text-xs">
                      Built with Next.js · Tailwind CSS · shadcn/ui
                    </p>
                  </div>
                </div>
              </footer>
            </div>

            {/* Toast 通知容器 */}
            <ToastContainer />
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  )
}
