'use client'

/**
 * 柱状图组件
 * 用于展示分类数据对比（如不同话题的视频数、频道数等）
 */

interface BarChartProps {
  data: Array<{
    name: string
    value: number
    color?: string
  }>
  title?: string
  label?: string
  width?: number
  height?: number
  horizontal?: boolean
}

export function BarChart({
  data,
  title = '数据对比',
  label = '数值',
  width = 600,
  height = 300,
  horizontal = false,
}: BarChartProps) {
  if (data.length === 0) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-gray-500">
        暂无数据
      </div>
    )
  }

  // 计算最大值
  const maxValue = Math.max(...data.map(d => d.value))

  // 默认颜色
  const defaultColors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']

  // 格式化数字
  const formatNumber = (num: number) => {
    if (num >= 10000000) return `${(num / 10000000).toFixed(1)}千万`
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}百万`
    if (num >= 10000) return `${(num / 10000).toFixed(0)}万`
    return num.toString()
  }

  if (horizontal) {
    return (
      <div className="w-full">
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

        <div className="space-y-4">
          {data.map((item, idx) => {
            const percentage = (item.value / maxValue) * 100
            const color = item.color || defaultColors[idx % defaultColors.length]

            return (
              <div key={item.name}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium">{item.name}</span>
                  <span className="text-sm font-bold">{formatNumber(item.value)}</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-6 overflow-hidden">
                  <div
                    className="h-full flex items-center justify-end px-2 text-white text-xs font-bold transition-all"
                    style={{ width: `${percentage}%`, backgroundColor: color }}
                  >
                    {percentage > 10 && `${percentage.toFixed(0)}%`}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* 统计信息 */}
        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
            <p className="text-xs text-gray-500 dark:text-gray-400">最高</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white">{formatNumber(maxValue)}</p>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
            <p className="text-xs text-gray-500 dark:text-gray-400">总计</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white">
              {formatNumber(data.reduce((sum, item) => sum + item.value, 0))}
            </p>
          </div>
        </div>
      </div>
    )
  }

  // 竖直柱状图
  const barWidth = (width - 100) / data.length
  const chartHeight = height - 100

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="border rounded bg-white dark:bg-slate-800"
      >
        {/* 背景网格 */}
        <defs>
          <pattern id="grid-vertical" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(200,200,200,0.1)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={width} height={height} fill="url(#grid-vertical)" />

        {/* 坐标轴 */}
        <line x1="50" y1={height - 50} x2={width - 30} y2={height - 50} stroke="currentColor" strokeWidth="2" />
        <line x1="50" y1="40" x2="50" y2={height - 50} stroke="currentColor" strokeWidth="2" />

        {/* Y 轴刻度和标签 */}
        {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
          const y = height - 50 - ratio * chartHeight
          const value = maxValue * ratio

          return (
            <g key={`y-tick-${ratio}`}>
              <line x1="45" y1={y} x2="50" y2={y} stroke="currentColor" strokeWidth="1" />
              <text x="40" y={y + 3} textAnchor="end" className="text-xs fill-gray-500 dark:fill-gray-500">
                {formatNumber(value)}
              </text>
            </g>
          )
        })}

        {/* Y 轴标签 */}
        <text
          x="15"
          y={height / 2}
          textAnchor="middle"
          transform={`rotate(-90 15 ${height / 2})`}
          className="text-xs fill-gray-600 dark:fill-gray-400"
        >
          {label}
        </text>

        {/* 柱子和 X 轴标签 */}
        {data.map((item, idx) => {
          const barHeight = (item.value / maxValue) * chartHeight
          const x = 50 + idx * barWidth + barWidth / 2
          const y = height - 50 - barHeight
          const color = item.color || defaultColors[idx % defaultColors.length]

          return (
            <g key={item.name}>
              {/* 柱子 */}
              <rect
                x={x - barWidth * 0.35}
                y={y}
                width={barWidth * 0.7}
                height={barHeight}
                fill={color}
                opacity="0.8"
                className="hover:opacity-100 transition-opacity cursor-pointer"
              >
                <title>{`${item.name}: ${formatNumber(item.value)}`}</title>
              </rect>

              {/* 数值标签 */}
              <text
                x={x}
                y={y - 5}
                textAnchor="middle"
                className="text-xs font-bold fill-gray-900 dark:fill-white"
              >
                {formatNumber(item.value)}
              </text>

              {/* X 轴标签 */}
              <text
                x={x}
                y={height - 25}
                textAnchor="middle"
                className="text-xs fill-gray-600 dark:fill-gray-400"
              >
                {item.name}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
