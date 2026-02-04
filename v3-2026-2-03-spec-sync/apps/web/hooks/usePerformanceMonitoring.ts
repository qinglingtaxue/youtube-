import { useEffect } from 'react'
import { monitorWebVitals, type WebVitals } from '@/lib/web-vitals'

interface PerformanceMonitoringOptions {
  onVitalsMeasured?: (vital: WebVitals) => void
  logToConsole?: boolean
  sendToAnalytics?: boolean
}

/**
 * Hook for monitoring Core Web Vitals
 * 监控 Web 性能指标的 React Hook
 */
export function usePerformanceMonitoring({
  onVitalsMeasured,
  logToConsole = false,
  sendToAnalytics = false,
}: PerformanceMonitoringOptions = {}) {
  useEffect(() => {
    const handleVitalsMeasured = (vital: WebVitals) => {
      // 执行回调函数
      onVitalsMeasured?.(vital)

      // 可选：打印到控制台
      if (logToConsole) {
        const ratingColor = {
          good: 'color: green',
          'needs-improvement': 'color: orange',
          poor: 'color: red',
        }[vital.rating || 'poor']

        console.log(
          `%c${vital.name}: ${vital.value.toFixed(2)}ms (${vital.rating})`,
          ratingColor
        )
      }

      // 可选：发送到分析服务
      if (sendToAnalytics && typeof fetch !== 'undefined') {
        fetch('/api/analytics/performance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(vital),
          keepalive: true, // 即使页面卸载也会发送
        }).catch(() => {
          // 忽略分析发送错误
        })
      }
    }

    monitorWebVitals(handleVitalsMeasured)
  }, [onVitalsMeasured, logToConsole, sendToAnalytics])
}
