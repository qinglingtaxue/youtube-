'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

interface DiagnosisCard {
  id: number
  title: string
  icon: string
  metric: string
  current: string
  baseline: string
  difference: string
  isPositive: boolean
  marketFinding: string[]
  suggestions: string[]
  dataLink: string
  dataLinkText: string
  expanded: boolean
}

export default function CreatorCenterPage() {
  const [diagnoses, setDiagnoses] = useState<DiagnosisCard[]>([
    {
      id: 1,
      title: '视频时长',
      icon: '⏱️',
      metric: '平均时长',
      current: '11 分钟',
      baseline: '8 分钟',
      difference: '+3 分钟（偏长）',
      isPositive: false,
      marketFinding: [
        '4-20min 中视频均播 8.2 万（最高）',
        '你当前在中视频范围内 ✓',
        '但相对市场均值 8 分钟仍偏长 -1.5%',
      ],
      suggestions: [
        '改进方向：下降到 8-10 分钟范围',
        '预期改进：播放完成率 +3~5%',
        '执行难度：中等（需调整脚本和素材使用）',
      ],
      dataLink: '/insights/arbitrage',
      dataLinkText: '查看信息报告 · 结论③',
      expanded: true,
    },
    {
      id: 2,
      title: '互动率',
      icon: '💬',
      metric: '点赞 + 评论 ÷ 播放',
      current: '1.2%',
      baseline: '2.8%',
      difference: '-1.6% （偏低）',
      isPositive: false,
      marketFinding: [
        '市场平均互动率：2.8%',
        '你的频道互动率：1.2%',
        '差异原因可能：缺乏互动环节 / 评论激励',
      ],
      suggestions: [
        '改进方向：在视频中段增加互动问题',
        '预期改进：互动率 +0.8~1.2%',
        '执行难度：低（无需改变内容结构）',
      ],
      dataLink: '/insights',
      dataLinkText: '查看全局认识',
      expanded: false,
    },
    {
      id: 3,
      title: '发布频率',
      icon: '📅',
      metric: '每周发布次数',
      current: '1.5 次/周',
      baseline: '2.5 次/周',
      difference: '-1 次/周（低于标准）',
      isPositive: false,
      marketFinding: [
        '市场增长型频道：2.5 次/周',
        '你的频道：1.5 次/周',
        '算法偏好：定期发布信号强于单个视频质量',
      ],
      suggestions: [
        '改进方向：增加到 2 次/周',
        '预期改进：月订阅增长 +8~12%',
        '执行难度：高（需提前规划和素材储备）',
      ],
      dataLink: '/insights/report',
      dataLinkText: '查看信息报告',
      expanded: false,
    },
    {
      id: 4,
      title: '选题方向',
      icon: '🎯',
      metric: '内容话题多样性',
      current: '8 个话题',
      baseline: '集中于 2-3 个缺口话题',
      difference: '机会：聚焦缺口话题',
      isPositive: true,
      marketFinding: [
        '穴位按摩 / 太极养生 搜索量高但供应少',
        '你目前话题太分散，容易被算法视为"什么都做"',
        '建议：前 90 天专注 2-3 个缺口话题建立特色',
      ],
      suggestions: [
        '改进方向：在穴位按摩 + 太极养生 两个话题深度',
        '预期改进：这两个话题的视频播放 +30~50%',
        '执行难度：中等（需调整选题方向和脚本库）',
      ],
      dataLink: '/insights/arbitrage',
      dataLinkText: '查看套利分析 · 结论②',
      expanded: false,
    },
  ])

  const toggleDiagnosis = (id: number) => {
    setDiagnoses(diagnoses.map(d => (d.id === id ? { ...d, expanded: !d.expanded } : d)))
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* 页面头 */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">🎬 创作者中心</h1>
          <p className="text-gray-600 dark:text-gray-400">基于市场分析的频道诊断 · 了解改进方向</p>
        </div>

        {/* 频道现状卡片 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 sm:p-8 mb-6">
          <h2 className="text-xl font-semibold mb-4">📊 频道现状</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">频道名</p>
              <p className="font-semibold">穴位养生馆</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">创建时间</p>
              <p className="font-semibold">6 个月前</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">订阅数</p>
              <p className="font-semibold text-lg">2.4 万</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">发布视频</p>
              <p className="font-semibold">24 个</p>
            </div>
          </div>
        </div>

        {/* 核心指标概览 */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg shadow-lg p-6 sm:p-8 mb-6 border border-blue-200 dark:border-blue-800">
          <h2 className="text-lg font-semibold mb-4">🎯 核心指标对标</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span>平均播放量</span>
              <div className="flex items-center gap-2">
                <span className="font-bold">8.5 万</span>
                <span className="text-xs text-gray-600 dark:text-gray-400">vs 市场 12 万 (-29%)</span>
                <TrendingDown className="w-4 h-4 text-red-500" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span>互动率</span>
              <div className="flex items-center gap-2">
                <span className="font-bold">1.2%</span>
                <span className="text-xs text-gray-600 dark:text-gray-400">vs 市场 2.8% (-57%)</span>
                <TrendingDown className="w-4 h-4 text-red-500" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span>发布频率</span>
              <div className="flex items-center gap-2">
                <span className="font-bold">1.5 次/周</span>
                <span className="text-xs text-gray-600 dark:text-gray-400">vs 市场 2.5 次 (-40%)</span>
                <TrendingDown className="w-4 h-4 text-red-500" />
              </div>
            </div>
          </div>
        </div>

        {/* 诊断卡片 */}
        <div className="space-y-4 mb-6">
          <h2 className="text-xl font-semibold">🔍 详细诊断</h2>

          {diagnoses.map(diagnosis => (
            <div
              key={diagnosis.id}
              className="bg-white dark:bg-slate-900 rounded-lg shadow-lg overflow-hidden"
            >
              {/* 诊断标题 */}
              <button
                onClick={() => toggleDiagnosis(diagnosis.id)}
                className="w-full p-6 text-left hover:bg-gray-50 dark:hover:bg-slate-800 transition"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-2xl">{diagnosis.icon}</span>
                      <div>
                        <h3 className="text-lg font-semibold">诊断 {diagnosis.id}：{diagnosis.title}</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {diagnosis.metric}：{diagnosis.current} | 市场基线：{diagnosis.baseline}
                        </p>
                      </div>
                    </div>
                    <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                      diagnosis.isPositive
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                        : 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200'
                    }`}>
                      {diagnosis.difference}
                    </div>
                  </div>

                  <div className="flex-shrink-0 text-blue-600 dark:text-blue-400">
                    {diagnosis.expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </div>
                </div>
              </button>

              {/* 展开内容 */}
              {diagnosis.expanded && (
                <div className="border-t dark:border-slate-700 px-6 py-4 space-y-4 bg-gray-50 dark:bg-slate-800/50">
                  {/* 市场发现 */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3">📈 市场发现：</h4>
                    <ul className="space-y-2">
                      {diagnosis.marketFinding.map((finding, i) => (
                        <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="text-blue-500 font-bold">•</span>
                          <span>{finding}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 建议 */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3">💡 改进建议：</h4>
                    <ul className="space-y-2">
                      {diagnosis.suggestions.map((suggestion, i) => (
                        <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="text-green-500 font-bold">✓</span>
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 数据链接 */}
                  <div className="pt-2 border-t dark:border-slate-600">
                    <Link href={diagnosis.dataLink} className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium">
                      📊 {diagnosis.dataLinkText} →
                    </Link>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 改进目标与追踪 */}
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg shadow-lg p-6 sm:p-8 border border-green-200 dark:border-green-800">
          <h2 className="text-xl font-semibold mb-4">🎯 下个月改进目标</h2>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">互动率改进</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">1.2% → 2.0%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '43%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">发布频率改进</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">1.5 次/周 → 2 次/周</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '60%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">选题聚焦</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">8 个话题 → 3 个话题</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '75%' }} />
              </div>
            </div>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 mt-4">
            💡 系统会在下月自动对比你的实际指标，检验改进效果
          </p>
        </div>

        {/* 返回导航 */}
        <div className="mt-8 flex gap-4 justify-center flex-wrap">
          <Link href="/insights/report" className="text-blue-600 dark:text-blue-400 hover:underline">
            ← 返回信息报告
          </Link>
          <span className="text-gray-400">|</span>
          <Link href="/insights/arbitrage" className="text-blue-600 dark:text-blue-400 hover:underline">
            ← 返回套利分析
          </Link>
        </div>
      </div>
    </div>
  )
}
