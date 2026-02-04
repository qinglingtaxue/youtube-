'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface InsightCardProps {
  title: string
  icon?: string
  description: string
  insights: string[]
  actionItems?: string[]
  type?: 'info' | 'success' | 'warning' | 'error'
  expandable?: boolean
}

export function InsightCard({
  title,
  icon = '💡',
  description,
  insights,
  actionItems = [],
  type = 'info',
  expandable = true,
}: InsightCardProps) {
  const [expanded, setExpanded] = useState(true)

  const typeStyles = {
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    warning: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    error: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
  }

  const typeTextStyles = {
    info: 'text-blue-900 dark:text-blue-300',
    success: 'text-green-900 dark:text-green-300',
    warning: 'text-yellow-900 dark:text-yellow-300',
    error: 'text-red-900 dark:text-red-300',
  }

  return (
    <div className={`${typeStyles[type]} border rounded-lg p-4 sm:p-6`}>
      {/* 标题 */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-xl flex-shrink-0">{icon}</span>
          <div>
            <h3 className={`font-bold text-lg ${typeTextStyles[type]}`}>{title}</h3>
            <p className={`text-sm mt-1 ${typeTextStyles[type]}`}>{description}</p>
          </div>
        </div>

        {expandable && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-shrink-0 p-1 hover:bg-white/20 rounded transition"
            aria-label={expanded ? '收起' : '展开'}
          >
            {expanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        )}
      </div>

      {/* 展开内容 */}
      {expanded && (
        <>
          {/* 洞察要点 */}
          {insights.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className={`font-semibold text-sm ${typeTextStyles[type]}`}>📊 关键洞察</h4>
              <ul className="space-y-1">
                {insights.map((insight, idx) => (
                  <li key={idx} className={`text-sm flex gap-2 ${typeTextStyles[type]}`}>
                    <span className="flex-shrink-0">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 行动建议 */}
          {actionItems.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className={`font-semibold text-sm ${typeTextStyles[type]}`}>🎯 建议行动</h4>
              <ul className="space-y-1">
                {actionItems.map((action, idx) => (
                  <li key={idx} className={`text-sm flex gap-2 ${typeTextStyles[type]}`}>
                    <span className="flex-shrink-0">→</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}

/**
 * 洞察卡片群组
 */
interface InsightCardsProps {
  cards: InsightCardProps[]
}

export function InsightCards({ cards }: InsightCardsProps) {
  return (
    <div className="space-y-4">
      {cards.map((card, idx) => (
        <InsightCard key={idx} {...card} />
      ))}
    </div>
  )
}
