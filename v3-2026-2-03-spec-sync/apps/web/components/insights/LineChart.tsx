'use client'

/**
 * 线性趋势图组件
 * 用于展示视频/频道的增长趋势（播放量、订阅数等）
 */

interface LineChartProps {
  data: Array<{
    date: string
    value: number
  }>
  title?: string
  label?: string
  width?: number
  height?: number
  color?: string
}

export function LineChart({
  data,
  title = '增长趋势',
  label = '数值',
  width = 600,
  height = 300,
  color = '#3b82f6',
}: LineChartProps) {
  if (data.length === 0) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-gray-500">
        暂无数据
      </div>
    )
  }

  // 计算数据范围
  const values = data.map(d => d.value)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const range = maxValue - minValue || 1

  // 坐标映射
  const mapY = (value: number) => {
    const normalized = (value - minValue) / range
    return height - 60 - normalized * (height - 100)
  }

  const mapX = (index: number) => {
    return 50 + (index / (data.length - 1)) * (width - 100)
  }

  // 生成路径
  const pathData = data
    .map((point, idx) => {
      const x = mapX(idx)
      const y = mapY(point.value)
      return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')

  // 格式化 Y 轴标签
  const formatNumber = (num: number) => {
    if (num >= 10000000) return `${(num / 10000000).toFixed(1)}千万`
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}百万`
    if (num >= 10000) return `${(num / 10000).toFixed(0)}万`
    return num.toString()
  }

  // Y 轴刻度线
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map(ratio => ({
    ratio,
    value: minValue + range * ratio,
    y: height - 60 - ratio * (height - 100),
  }))

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
          <pattern id="grid-lines" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(200,200,200,0.1)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={width} height={height} fill="url(#grid-lines)" />

        {/* 坐标轴 */}
        <line x1="50" y1={height - 60} x2={width - 50} y2={height - 60} stroke="currentColor" strokeWidth="2" />
        <line x1="50" y1="40" x2="50" y2={height - 60} stroke="currentColor" strokeWidth="2" />

        {/* Y 轴标签 */}
        <text
          x="25"
          y={height / 2}
          textAnchor="middle"
          transform={`rotate(-90 25 ${height / 2})`}
          className="text-xs fill-gray-600 dark:fill-gray-400"
        >
          {label}
        </text>

        {/* X 轴标签 */}
        <text x={width / 2} y={height - 10} textAnchor="middle" className="text-xs fill-gray-600 dark:fill-gray-400">
          时间
        </text>

        {/* Y 轴刻度和标签 */}
        {yTicks.map(tick => (
          <g key={`y-tick-${tick.ratio}`}>
            <line x1="45" y1={tick.y} x2="50" y2={tick.y} stroke="currentColor" strokeWidth="1" />
            <text
              x="40"
              y={tick.y + 3}
              textAnchor="end"
              className="text-xs fill-gray-500 dark:fill-gray-500"
            >
              {formatNumber(tick.value)}
            </text>
          </g>
        ))}

        {/* X 轴刻度和日期标签 */}
        {data.map((point, idx) => {
          // 只显示第一个、最后一个和中间的日期
          if (data.length > 10 && idx !== 0 && idx !== data.length - 1 && idx % Math.floor(data.length / 3) !== 0) {
            return null
          }

          const x = mapX(idx)
          return (
            <g key={`x-tick-${idx}`}>
              <line x1={x} y1={height - 55} x2={x} y2={height - 60} stroke="currentColor" strokeWidth="1" />
              <text x={x} y={height - 40} textAnchor="middle" className="text-xs fill-gray-500 dark:fill-gray-500">
                {point.date}
              </text>
            </g>
          )
        })}

        {/* 趋势线 */}
        <path d={pathData} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />

        {/* 数据点 */}
        {data.map((point, idx) => (
          <circle
            key={`point-${idx}`}
            cx={mapX(idx)}
            cy={mapY(point.value)}
            r="3"
            fill={color}
            className="hover:r-5 transition-all cursor-pointer"
          >
            <title>{`${point.date}: ${formatNumber(point.value)}`}</title>
          </circle>
        ))}
      </svg>

      {/* 统计信息 */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
          <p className="text-xs text-gray-500 dark:text-gray-400">最高值</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">{formatNumber(maxValue)}</p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
          <p className="text-xs text-gray-500 dark:text-gray-400">最低值</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">{formatNumber(minValue)}</p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
          <p className="text-xs text-gray-500 dark:text-gray-400">增长率</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">
            {((((maxValue - minValue) / minValue) * 100) || 0).toFixed(1)}%
          </p>
        </div>
      </div>
    </div>
  )
}
