'use client'

/**
 * 套利分析散点图组件
 * X 轴：程度中心性（Degree Centrality）
 * Y 轴：中介中心性（Betweenness Centrality）
 * 颜色：有趣度（蓝 → 红）
 * 大小：播放量
 */

interface ScatterPlotProps {
  data: Array<{
    id: string
    title: string
    degree: number
    betweenness: number
    interestingness: number
    views: number
  }>
  width?: number
  height?: number
}

export function ScatterPlot({ data, width = 600, height = 400 }: ScatterPlotProps) {
  if (data.length === 0) {
    return (
      <div className="w-full h-96 flex items-center justify-center text-gray-500">
        暂无数据
      </div>
    )
  }

  // 计算坐标范围
  const degrees = data.map(d => d.degree)
  const betweennesses = data.map(d => d.betweenness)
  const interestingnesses = data.map(d => d.interestingness)
  const views = data.map(d => d.views)

  const minDegree = Math.min(...degrees)
  const maxDegree = Math.max(...degrees)
  const minBetweenness = Math.min(...betweennesses)
  const maxBetweenness = Math.max(...betweennesses)
  const minInterestingness = Math.min(...interestingnesses)
  const maxInterestingness = Math.max(...interestingnesses)
  const minViews = Math.min(...views)
  const maxViews = Math.max(...views)

  // 坐标映射函数
  const mapX = (degree: number) => {
    const range = maxDegree - minDegree || 1
    return ((degree - minDegree) / range) * (width - 80) + 40
  }

  const mapY = (betweenness: number) => {
    const range = maxBetweenness - minBetweenness || 1
    return height - ((betweenness - minBetweenness) / range) * (height - 80) - 40
  }

  // 颜色映射函数：有趣度（蓝 → 红）
  const getColor = (interestingness: number) => {
    const normalized = (interestingness - minInterestingness) / (maxInterestingness - minInterestingness || 1)
    // 蓝色 (0) 到 红色 (1)
    const hue = (1 - normalized) * 240 // 蓝色 240° 到 红色 0°
    return `hsl(${hue}, 100%, 50%)`
  }

  // 大小映射函数：播放量
  const getRadius = (viewCount: number) => {
    const normalized = (viewCount - minViews) / (maxViews - minViews || 1)
    return 4 + normalized * 12 // 4 到 16
  }

  return (
    <div className="w-full">
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="border rounded bg-white dark:bg-slate-800"
      >
        {/* 背景网格 */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(200,200,200,0.1)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={width} height={height} fill="url(#grid)" />

        {/* 坐标轴 */}
        {/* X 轴 */}
        <line x1="40" y1={height - 40} x2={width - 40} y2={height - 40} stroke="currentColor" strokeWidth="2" />
        {/* Y 轴 */}
        <line x1="40" y1="40" x2="40" y2={height - 40} stroke="currentColor" strokeWidth="2" />

        {/* X 轴标签 */}
        <text x={width / 2} y={height - 5} textAnchor="middle" className="text-xs fill-gray-600 dark:fill-gray-400">
          程度中心性（Degree）
        </text>

        {/* Y 轴标签 */}
        <text
          x="10"
          y={height / 2}
          textAnchor="middle"
          transform={`rotate(-90 10 ${height / 2})`}
          className="text-xs fill-gray-600 dark:fill-gray-400"
        >
          中介中心性（Betweenness）
        </text>

        {/* 刻度线和标签 */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const x = 40 + (width - 80) * ratio
          const y = height - 40 - (height - 80) * ratio
          return (
            <g key={`tick-${ratio}`}>
              {/* X 轴刻度 */}
              <line x1={x} y1={height - 35} x2={x} y2={height - 40} stroke="currentColor" strokeWidth="1" />
              <text
                x={x}
                y={height - 20}
                textAnchor="middle"
                className="text-xs fill-gray-500 dark:fill-gray-500"
              >
                {(minDegree + (maxDegree - minDegree) * ratio).toFixed(1)}
              </text>

              {/* Y 轴刻度 */}
              <line x1="35" y1={y} x2="40" y2={y} stroke="currentColor" strokeWidth="1" />
              <text
                x="30"
                y={y + 3}
                textAnchor="end"
                className="text-xs fill-gray-500 dark:fill-gray-500"
              >
                {(minBetweenness + (maxBetweenness - minBetweenness) * ratio).toFixed(2)}
              </text>
            </g>
          )
        })}

        {/* 数据点 */}
        {data.map((point) => {
          const cx = mapX(point.degree)
          const cy = mapY(point.betweenness)
          const r = getRadius(point.views)
          const color = getColor(point.interestingness)

          return (
            <g key={point.id}>
              {/* 数据点 */}
              <circle
                cx={cx}
                cy={cy}
                r={r}
                fill={color}
                opacity="0.7"
                className="hover:opacity-100 transition-opacity cursor-pointer"
              >
                <title>{point.title}</title>
              </circle>

              {/* 外圈 */}
              <circle
                cx={cx}
                cy={cy}
                r={r + 1}
                fill="none"
                stroke={color}
                strokeWidth="1"
                opacity="0.5"
              />
            </g>
          )
        })}
      </svg>

      {/* 图例 */}
      <div className="mt-4 flex justify-center gap-8 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-500" />
          <span>低有趣度（高传播）</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-yellow-500" />
          <span>中等有趣度</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-red-500" />
          <span>高有趣度（套利机会）</span>
        </div>
      </div>

      {/* 说明 */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded text-sm text-gray-700 dark:text-gray-300">
        <p className="font-semibold mb-1">📊 如何解读：</p>
        <ul className="space-y-1 text-xs">
          <li>• <strong>左上角</strong>（红色）：高价值、低传播 = 蓝海机会</li>
          <li>• <strong>右下角</strong>（蓝色）：高传播、低价值 = 饱和市场</li>
          <li>• <strong>点的大小</strong>：播放量越大，点越大</li>
        </ul>
      </div>
    </div>
  )
}
