'use client'

/**
 * 网络关系图组件
 * 展示视频/频道/关键词之间的关系网络
 * 基于 SVG 的力引导布局实现
 */

import { useEffect, useRef, useState } from 'react'

interface Node {
  id: string
  label: string
  type: 'video' | 'channel' | 'keyword'
  value: number
  color?: string
}

interface Edge {
  source: string
  target: string
  weight?: number
}

interface NetworkGraphProps {
  nodes: Node[]
  edges: Edge[]
  title?: string
  width?: number
  height?: number
  onNodeClick?: (nodeId: string) => void
}

export function NetworkGraph({
  nodes,
  edges,
  title = '关系网络',
  width = 800,
  height = 600,
  onNodeClick,
}: NetworkGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map())
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  // 简化版力引导算法（迭代 50 次）
  useEffect(() => {
    if (nodes.length === 0 || !canvasRef.current) return

    // 初始化位置
    const initialPositions = new Map<string, { x: number; y: number }>()
    nodes.forEach((node, index) => {
      const angle = (index / nodes.length) * Math.PI * 2
      const radius = Math.min(width, height) / 3
      initialPositions.set(node.id, {
        x: width / 2 + radius * Math.cos(angle),
        y: height / 2 + radius * Math.sin(angle),
      })
    })

    let currentPositions = initialPositions
    const velocities = new Map<string, { x: number; y: number }>()
    nodes.forEach(node => {
      velocities.set(node.id, { x: 0, y: 0 })
    })

    // 力引导算法迭代
    for (let iteration = 0; iteration < 50; iteration++) {
      const forces = new Map<string, { x: number; y: number }>()
      nodes.forEach(node => {
        forces.set(node.id, { x: 0, y: 0 })
      })

      // 斥力（节点之间）
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const nodeA = nodes[i]
          const nodeB = nodes[j]
          const posA = currentPositions.get(nodeA.id)!
          const posB = currentPositions.get(nodeB.id)!

          const dx = posB.x - posA.x
          const dy = posB.y - posA.y
          const distance = Math.sqrt(dx * dx + dy * dy) || 1
          const repulsion = 100 / (distance + 1)

          const fx = (dx / distance) * repulsion
          const fy = (dy / distance) * repulsion

          const forceA = forces.get(nodeA.id)!
          forceA.x -= fx
          forceA.y -= fy

          const forceB = forces.get(nodeB.id)!
          forceB.x += fx
          forceB.y += fy
        }
      }

      // 引力（边连接的节点）
      edges.forEach(edge => {
        const nodeA = currentPositions.get(edge.source)
        const nodeB = currentPositions.get(edge.target)

        if (!nodeA || !nodeB) return

        const dx = nodeB.x - nodeA.x
        const dy = nodeB.y - nodeA.y
        const distance = Math.sqrt(dx * dx + dy * dy) || 1
        const attraction = distance * 0.1

        const fx = (dx / distance) * attraction
        const fy = (dy / distance) * attraction

        const forceA = forces.get(edge.source)!
        forceA.x += fx
        forceA.y += fy

        const forceB = forces.get(edge.target)!
        forceB.x -= fx
        forceB.y -= fy
      })

      // 更新位置和速度
      const damping = 0.85
      const newPositions = new Map(currentPositions)

      nodes.forEach(node => {
        const force = forces.get(node.id)!
        const velocity = velocities.get(node.id)!

        velocity.x = (velocity.x + force.x) * damping
        velocity.y = (velocity.y + force.y) * damping

        let pos = newPositions.get(node.id)!
        pos.x += velocity.x
        pos.y += velocity.y

        // 边界约束
        pos.x = Math.max(40, Math.min(width - 40, pos.x))
        pos.y = Math.max(40, Math.min(height - 40, pos.y))
      })

      currentPositions = newPositions
    }

    setPositions(currentPositions)
  }, [nodes, edges, width, height])

  // 获取节点颜色
  const getNodeColor = (node: Node): string => {
    if (node.color) return node.color
    switch (node.type) {
      case 'video':
        return '#3b82f6' // 蓝色
      case 'channel':
        return '#10b981' // 绿色
      case 'keyword':
        return '#f59e0b' // 橙色
      default:
        return '#6b7280'
    }
  }

  // 渲染
  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="border rounded bg-white dark:bg-slate-800"
        onMouseMove={e => {
          // 简化的悬停检测
          const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect()
          const x = (e.clientX - rect.left) * (width / rect.width)
          const y = (e.clientY - rect.top) * (height / rect.height)

          let hovering = null
          for (const node of nodes) {
            const pos = positions.get(node.id)
            if (!pos) continue

            const radius = 20 + (node.value / 100) * 10
            const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2)

            if (distance < radius) {
              hovering = node.id
              break
            }
          }

          setHoveredNode(hovering)
        }}
        onMouseLeave={() => setHoveredNode(null)}
      >
        {/* 边（连接线） */}
        {edges.map((edge, idx) => {
          const posA = positions.get(edge.source)
          const posB = positions.get(edge.target)

          if (!posA || !posB) return null

          return (
            <line
              key={`edge-${idx}`}
              x1={posA.x}
              y1={posA.y}
              x2={posB.x}
              y2={posB.y}
              stroke="rgba(200, 200, 200, 0.3)"
              strokeWidth="1"
            />
          )
        })}

        {/* 节点 */}
        {nodes.map(node => {
          const pos = positions.get(node.id)
          if (!pos) return null

          const radius = 20 + (node.value / 100) * 10
          const color = getNodeColor(node)
          const isHovered = hoveredNode === node.id

          return (
            <g
              key={node.id}
              onClick={() => onNodeClick?.(node.id)}
              style={{ cursor: 'pointer' }}
            >
              {/* 外圈（悬停时显示） */}
              {isHovered && (
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={radius + 8}
                  fill="none"
                  stroke={color}
                  strokeWidth="2"
                  opacity="0.5"
                />
              )}

              {/* 节点圆形 */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={radius}
                fill={color}
                opacity={isHovered ? 1 : 0.8}
                className="transition-all"
              >
                <title>{node.label}</title>
              </circle>

              {/* 节点标签 */}
              {radius > 20 && (
                <text
                  x={pos.x}
                  y={pos.y}
                  textAnchor="middle"
                  dy="0.3em"
                  className="text-xs font-bold fill-white pointer-events-none"
                  style={{
                    textShadow: '0 1px 3px rgba(0,0,0,0.5)',
                  }}
                >
                  {node.label.length > 8 ? node.label.substring(0, 8) + '...' : node.label}
                </text>
              )}
            </g>
          )
        })}
      </svg>

      {/* 图例 */}
      <div className="mt-4 flex justify-center gap-6 text-sm flex-wrap">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-500" />
          <span>视频</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-500" />
          <span>频道</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-amber-500" />
          <span>关键词</span>
        </div>
      </div>

      {/* 说明 */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded text-sm text-gray-700 dark:text-gray-300">
        <p className="font-semibold mb-1">💡 如何解读：</p>
        <ul className="space-y-1 text-xs">
          <li>• 节点大小：数据量越大，节点越大</li>
          <li>• 连线：表示节点之间存在关联</li>
          <li>• 距离：距离越近，关联度越强</li>
        </ul>
      </div>
    </div>
  )
}
