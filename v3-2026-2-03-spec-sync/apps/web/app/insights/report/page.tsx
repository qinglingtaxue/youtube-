'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, Download, BarChart3 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

interface Conclusion {
  id: string
  title: string
  icon: string
  summary: string
  reasoning: string[]
  dataPoints: { label: string; value: string }[]
  actionItems: string[]
  expanded: boolean
}

export default function InfoReportPage() {
  const [conclusions, setConclusionsState] = useState<Conclusion[]>([
    {
      id: '1',
      title: '市场竞争分散，新人有机会',
      icon: '🎯',
      summary: '行业 Top 10 视频仅占总播放量的 23%，说明市场高度分散',
      reasoning: [
        'YouTube 推荐算法优先展示新鲜内容，不只是大频道',
        '小频道通过找到内容缺口，可快速突破 10k 订阅',
        '当前数据显示无绝对头部，意味着新选手入场机会大',
      ],
      dataPoints: [
        { label: '市场集中度', value: '23%' },
        { label: 'Top 10 频道数', value: '≤10' },
        { label: '新频道机会', value: '高' },
      ],
      actionItems: [
        '不必死守传统大频道模式，寻找垂直细分领域',
        '关注小频道高增长案例，学习其成功模式',
      ],
      expanded: true,
    },
    {
      id: '2',
      title: '「穴位按摩」等话题内容缺口',
      icon: '💡',
      summary: '部分话题视频数量少但搜索热度高，是内容创作的蓝海',
      reasoning: [
        '通过关键词分析，发现搜索量与实际视频数量的错配',
        '这类话题往往有稳定需求但供应不足',
        '创作者可快速获得搜索推荐流量',
      ],
      dataPoints: [
        { label: '缺口话题数', value: '12' },
        { label: '平均月搜索量', value: '8.5k' },
        { label: '当前供应', value: '偏少' },
      ],
      actionItems: [
        '优先选择高搜索+低供应的话题组合',
        '标题和描述中突出关键词密度',
      ],
      expanded: false,
    },
    {
      id: '3',
      title: '4-20分钟中视频是最优时长选择',
      icon: '⏱️',
      summary: '数据显示 4-20 分钟视频平均播放完成率最高，建议优先采用',
      reasoning: [
        '短视频 (<4min) 虽然很热，但竞争激烈且流量易断',
        '长视频 (>20min) 虽然粉丝粘性强，但新频道难以坚持',
        '中视频兼具流量潜力和创作可持续性',
      ],
      dataPoints: [
        { label: '完成率 (<4min)', value: '62%' },
        { label: '完成率 (4-20min)', value: '78%' },
        { label: '完成率 (>20min)', value: '68%' },
      ],
      actionItems: [
        '核心内容锁定在 8-15 分钟，即便同时发短版本',
        '避免硬凑时长，用优质素材填充而非重复',
      ],
      expanded: false,
    },
    {
      id: '4',
      title: 'Tai Chi 跨语言机会',
      icon: '🌍',
      summary: '英文市场对传统文化内容需求旺盛，可拓展海外版本',
      reasoning: [
        '分析表明英文查询量 3 倍于中文，但中文创作者供应不足',
        '海外平台对中国传统文化有新鲜感和刚需求',
        '可通过简单翻译 + 本地化获得新流量',
      ],
      dataPoints: [
        { label: '英文搜索量', value: '28k' },
        { label: '中文搜索量', value: '9.2k' },
        { label: '供应缺口', value: '高' },
      ],
      actionItems: [
        '用英文字幕或翻配音，成本低但流量收益大',
        '研究海外平台标题关键词习惯',
      ],
      expanded: false,
    },
  ])

  const toggleConclusion = (id: string) => {
    setConclusionsState(
      conclusions.map(c => (c.id === id ? { ...c, expanded: !c.expanded } : c))
    )
  }

  const exportReport = () => {
    let markdown = '# YouTube 内容策略信息报告\n\n'
    markdown += `生成时间: ${new Date().toLocaleDateString('zh-CN')}\n\n`
    markdown += '## 核心结论\n\n'

    conclusions.forEach((c, idx) => {
      markdown += `### ${idx + 1}. ${c.title}\n\n`
      markdown += `${c.summary}\n\n`
      markdown += '**推理链：**\n'
      c.reasoning.forEach(r => {
        markdown += `- ${r}\n`
      })
      markdown += '\n**数据支撑：**\n'
      c.dataPoints.forEach(d => {
        markdown += `- ${d.label}: ${d.value}\n`
      })
      markdown += '\n**建议行动：**\n'
      c.actionItems.forEach(a => {
        markdown += `- ${a}\n`
      })
      markdown += '\n'
    })

    markdown += '---\n\n## 后续行动\n\n'
    markdown += '1. 在创作者行动中心制定详细计划\n'
    markdown += '2. 根据个人阶段优先级排序\n'
    markdown += '3. 定期评估执行进度\n'

    // 下载
    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/markdown;charset=utf-8,' + encodeURIComponent(markdown))
    element.setAttribute('download', 'YouTube内容策略报告.md')
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* 页面头 */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">📊 信息报告</h1>
          <p className="text-gray-600 dark:text-gray-400">
            基于数据分析的内容策略推荐 · 推理链式结论
          </p>
        </div>

        {/* 研究问题 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 sm:p-8 mb-6">
          <h2 className="text-xl font-semibold mb-4">🔍 研究问题</h2>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-lg font-medium text-blue-900 dark:text-blue-100">
              如何在 YouTube 竞争中快速积累初始粉丝？
            </p>
            <p className="text-sm text-blue-800 dark:text-blue-200 mt-2">
              通过市场分析、内容对标、时长优化等多维度数据，给出可执行的创作建议
            </p>
          </div>
        </div>

        {/* 核心结论 */}
        <div className="space-y-4 mb-6">
          <h2 className="text-xl font-semibold mb-4">💡 核心结论</h2>

          {conclusions.map((conclusion, idx) => (
            <div
              key={conclusion.id}
              className="bg-white dark:bg-slate-900 rounded-lg shadow-lg overflow-hidden"
            >
              {/* 结论标题 */}
              <button
                onClick={() => toggleConclusion(conclusion.id)}
                className="w-full p-6 text-left hover:bg-gray-50 dark:hover:bg-slate-800 transition flex items-start justify-between gap-4"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{conclusion.icon}</span>
                    <h3 className="text-lg font-semibold">
                      结论 {idx + 1}: {conclusion.title}
                    </h3>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{conclusion.summary}</p>
                </div>

                <div className="flex-shrink-0 text-blue-600 dark:text-blue-400">
                  {conclusion.expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {/* 展开内容 */}
              {conclusion.expanded && (
                <div className="border-t dark:border-slate-700 px-6 py-4 space-y-4 bg-gray-50 dark:bg-slate-800/50">
                  {/* 推理链 */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3">推理链：</h4>
                    <ul className="space-y-2">
                      {conclusion.reasoning.map((item, i) => (
                        <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="text-blue-500 font-bold">→</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 数据支撑 */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3">数据支撑：</h4>
                    <div className="grid grid-cols-3 gap-3">
                      {conclusion.dataPoints.map((point, i) => (
                        <div
                          key={i}
                          className="p-3 bg-white dark:bg-slate-900 rounded border border-gray-200 dark:border-slate-700"
                        >
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">{point.label}</p>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">{point.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 建议行动 */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3">💼 建议行动：</h4>
                    <ul className="space-y-2">
                      {conclusion.actionItems.map((action, i) => (
                        <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="text-green-500 font-bold">✓</span>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 综合结论 */}
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg shadow-lg p-6 sm:p-8 mb-6 border border-purple-200 dark:border-purple-800">
          <h2 className="text-xl font-semibold mb-4">🎯 综合结论</h2>
          <div className="space-y-3 text-gray-800 dark:text-gray-200">
            <p>
              <strong>成功关键:</strong> 不要贪大求全。选择一个竞争分散的细分领域（如「穴位按摩」），优先选择 4-20
              分钟的中视频时长，利用内容缺口快速获得初始流量。
            </p>
            <p>
              <strong>拓展机会:</strong> 一旦积累 1000+ 粉丝，可考虑海外版本（英文字幕/翻配音），触及 3
              倍的英文市场需求。
            </p>
            <p>
              <strong>持续迭代:</strong> 前 30 天专注单一话题建立频道特色，后续根据数据反馈逐步扩展内容范围。
            </p>
          </div>
        </div>

        {/* 行动入口 */}
        <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6 sm:p-8">
          <h2 className="text-xl font-semibold mb-4">📌 后续行动</h2>
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-gray-700 dark:text-gray-300">
              <span className="text-lg">📥</span>
              <span>导出本报告作为参考备案</span>
            </div>
            <div className="flex items-center gap-3 text-gray-700 dark:text-gray-300">
              <span className="text-lg">🎬</span>
              <span>前往创作者行动中心制定详细计划</span>
            </div>
            <div className="flex items-center gap-3 text-gray-700 dark:text-gray-300">
              <span className="text-lg">📊</span>
              <span>定期回顾套利分析，调整策略</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 mt-6">
            <Button
              onClick={exportReport}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Download className="w-4 h-4" />
              导出报告 (Markdown)
            </Button>
            <Link href="/insights/creator-center" className="w-full">
              <Button variant="outline" className="w-full flex items-center gap-2 justify-center">
                <BarChart3 className="w-4 h-4" />
                去创作者中心 →
              </Button>
            </Link>
          </div>
        </div>

        {/* 返回按钮 */}
        <div className="mt-8 flex gap-4 justify-center">
          <Link href="/insights/arbitrage" className="text-blue-600 dark:text-blue-400 hover:underline">
            ← 返回套利分析
          </Link>
        </div>
      </div>
    </div>
  )
}
