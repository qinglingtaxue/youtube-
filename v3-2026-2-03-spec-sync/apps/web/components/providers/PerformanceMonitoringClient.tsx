'use client'

import { usePerformanceMonitoring } from '@/hooks/usePerformanceMonitoring'
import type { WebVitals } from '@/lib/web-vitals'

/**
 * 性能监控客户端组件
 * 在应用根级别监控 Core Web Vitals 指标
 */
export function PerformanceMonitoringClient() {
  usePerformanceMonitoring({
    onVitalsMeasured: (vital: WebVitals) => {
      // 在开发环境中打印性能数据
      if (process.env.NODE_ENV === 'development') {
        const ratingEmoji = {
          good: '✅',
          'needs-improvement': '⚠️',
          poor: '❌',
        }[vital.rating || 'poor']

        console.log(
          `${ratingEmoji} [Core Web Vitals] ${vital.name}: ${vital.value.toFixed(2)}ms (${vital.rating})`
        )
      }
    },
    // 在生产环境中发送性能数据到分析服务
    sendToAnalytics: process.env.NODE_ENV === 'production',
    // 在开发环境中打印日志
    logToConsole: process.env.NODE_ENV === 'development',
  })

  return null
}
