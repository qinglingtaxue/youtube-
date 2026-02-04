'use client'

/**
 * 词云组件
 * 展示关键词频率分布，字号大小表示频率高低
 */

interface WordItem {
  text: string
  value: number
  color?: string
}

interface WordCloudProps {
  words: WordItem[]
  title?: string
  width?: number
  height?: number
  onWordClick?: (word: string) => void
}

export function WordCloud({
  words,
  title = '关键词分布',
  width = 600,
  height = 300,
  onWordClick,
}: WordCloudProps) {
  if (words.length === 0) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-gray-500">
        暂无数据
      </div>
    )
  }

  // 计算字号范围
  const values = words.map(w => w.value)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const range = maxValue - minValue || 1

  // 字号映射函数（16px - 48px）
  const getFontSize = (value: number) => {
    const normalized = (value - minValue) / range
    return 16 + normalized * 32
  }

  // 颜色映射（默认蓝→红渐变）
  const getColor = (index: number, value: number) => {
    if (words[index].color) return words[index].color

    const normalized = (value - minValue) / range
    const hue = (1 - normalized) * 240 // 蓝色 → 红色
    return `hsl(${hue}, 70%, 50%)`
  }

  // 简单的词云布局（网格排列）
  const cols = Math.ceil(Math.sqrt(words.length))
  const cellWidth = width / cols
  const cellHeight = height / Math.ceil(words.length / cols)

  // 生成位置
  const positions = words.map((word, idx) => {
    const row = Math.floor(idx / cols)
    const col = idx % cols

    return {
      x: col * cellWidth + cellWidth / 2,
      y: row * cellHeight + cellHeight / 2,
      fontSize: getFontSize(word.value),
      color: getColor(idx, word.value),
    }
  })

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="border rounded bg-white dark:bg-slate-800"
      >
        {/* 背景 */}
        <rect width={width} height={height} fill="none" />

        {/* 词 */}
        {words.map((word, idx) => {
          const pos = positions[idx]

          return (
            <g
              key={word.text}
              onClick={() => onWordClick?.(word.text)}
              style={{ cursor: 'pointer' }}
            >
              <text
                x={pos.x}
                y={pos.y}
                textAnchor="middle"
                dy="0.3em"
                fontSize={pos.fontSize}
                fontWeight="bold"
                fill={pos.color}
                opacity="0.8"
                className="hover:opacity-100 transition-opacity select-none"
              >
                {word.text}
              </text>
            </g>
          )
        })}
      </svg>

      {/* 频率说明 */}
      <div className="mt-4 flex justify-between items-center text-xs text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold" style={{ color: getColor(0, minValue) }}>
            字较小
          </span>
          <span>= 频率低</span>
        </div>
        <div className="flex items-center gap-2">
          <span>频率高 =</span>
          <span className="text-sm font-bold" style={{ color: getColor(0, maxValue) }}>
            字较大
          </span>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
          <p className="text-xs text-gray-500 dark:text-gray-400">关键词总数</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">{words.length}</p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
          <p className="text-xs text-gray-500 dark:text-gray-400">最高频</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">{maxValue}</p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-slate-700 rounded">
          <p className="text-xs text-gray-500 dark:text-gray-400">平均频</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">
            {(values.reduce((a, b) => a + b, 0) / values.length).toFixed(0)}
          </p>
        </div>
      </div>
    </div>
  )
}
