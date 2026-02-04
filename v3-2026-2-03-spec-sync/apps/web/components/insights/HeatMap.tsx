'use client'

/**
 * 热力图组件
 * 用于展示二维数据分布（如不同话题在不同时间的热度）
 */

interface HeatMapProps {
  data: Array<{
    row: string
    col: string
    value: number
  }>
  rows?: string[]
  cols?: string[]
  title?: string
  width?: number
  height?: number
  colorScheme?: 'blue-red' | 'green-yellow-red'
}

export function HeatMap({
  data,
  rows,
  cols,
  title = '热力分布',
  width = 600,
  height = 400,
  colorScheme = 'blue-red',
}: HeatMapProps) {
  if (data.length === 0) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-gray-500">
        暂无数据
      </div>
    )
  }

  // 自动推导行列标签
  const allRows = rows || Array.from(new Set(data.map(d => d.row))).sort()
  const allCols = cols || Array.from(new Set(data.map(d => d.col))).sort()

  // 构建矩阵
  const matrix: Record<string, Record<string, number>> = {}
  for (const row of allRows) {
    matrix[row] = {}
    for (const col of allCols) {
      const item = data.find(d => d.row === row && d.col === col)
      matrix[row][col] = item?.value || 0
    }
  }

  // 计算值范围
  const values = data.map(d => d.value)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const range = maxValue - minValue || 1

  // 颜色映射函数
  const getColor = (value: number) => {
    const normalized = (value - minValue) / range

    if (colorScheme === 'green-yellow-red') {
      // 绿 → 黄 → 红
      if (normalized < 0.5) {
        // 绿 到 黄
        const ratio = normalized * 2
        const r = Math.floor(255 * ratio)
        const g = 255
        const b = 0
        return `rgb(${r}, ${g}, ${b})`
      } else {
        // 黄 到 红
        const ratio = (normalized - 0.5) * 2
        const r = 255
        const g = Math.floor(255 * (1 - ratio))
        const b = 0
        return `rgb(${r}, ${g}, ${b})`
      }
    } else {
      // 蓝 → 红（默认）
      const hue = (1 - normalized) * 240 // 蓝色 240° 到 红色 0°
      return `hsl(${hue}, 100%, 50%)`
    }
  }

  // 布局参数
  const cellWidth = (width - 150) / allCols.length
  const cellHeight = (height - 80) / allRows.length
  const startX = 150
  const startY = 40

  // 格式化数字
  const formatNumber = (num: number) => {
    if (num >= 10000000) return `${(num / 10000000).toFixed(1)}千万`
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}百万`
    if (num >= 10000) return `${(num / 10000).toFixed(0)}万`
    return num.toString()
  }

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="border rounded bg-white dark:bg-slate-800"
      >
        {/* 列标题 */}
        {allCols.map((col, colIdx) => (
          <text
            key={`col-${colIdx}`}
            x={startX + colIdx * cellWidth + cellWidth / 2}
            y="30"
            textAnchor="middle"
            className="text-xs font-semibold fill-gray-700 dark:fill-gray-300"
          >
            {col}
          </text>
        ))}

        {/* 行标题和热力单元格 */}
        {allRows.map((row, rowIdx) => (
          <g key={`row-${rowIdx}`}>
            {/* 行标题 */}
            <text
              x="140"
              y={startY + rowIdx * cellHeight + cellHeight / 2 + 4}
              textAnchor="end"
              className="text-xs font-semibold fill-gray-700 dark:fill-gray-300"
            >
              {row}
            </text>

            {/* 热力单元格 */}
            {allCols.map((col, colIdx) => {
              const value = matrix[row][col]
              const color = getColor(value)
              const x = startX + colIdx * cellWidth
              const y = startY + rowIdx * cellHeight

              return (
                <g key={`cell-${rowIdx}-${colIdx}`}>
                  <rect
                    x={x}
                    y={y}
                    width={cellWidth}
                    height={cellHeight}
                    fill={color}
                    stroke="rgba(255,255,255,0.2)"
                    strokeWidth="1"
                    className="hover:opacity-80 transition-opacity cursor-pointer"
                  >
                    <title>{`${row} - ${col}: ${formatNumber(value)}`}</title>
                  </rect>

                  {/* 数值标签（仅当单元格足够大时显示） */}
                  {cellWidth > 50 && cellHeight > 30 && (
                    <text
                      x={x + cellWidth / 2}
                      y={y + cellHeight / 2 + 4}
                      textAnchor="middle"
                      className="text-xs font-bold fill-white"
                    >
                      {formatNumber(value)}
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        ))}
      </svg>

      {/* 颜色条图例 */}
      <div className="mt-4 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">低</span>
          <div className="flex h-6 w-32 rounded overflow-hidden border border-gray-300">
            {Array.from({ length: 10 }, (_, i) => {
              const value = minValue + (range * i) / 10
              const color = getColor(value)
              return <div key={i} style={{ flex: 1, backgroundColor: color }} />
            })}
          </div>
          <span className="text-xs text-gray-500">高</span>
        </div>
        <div className="text-sm font-semibold">
          {formatNumber(minValue)} - {formatNumber(maxValue)}
        </div>
      </div>
    </div>
  )
}
