/**
 * 中心性分析模块
 * 计算网络中节点的中介中心性和接近中心性
 * 用于套利分析中的"有趣度"评分
 */

export interface NetworkNode {
  id: string
  label: string
  degree: number // 出入度
  betweenness: number // 中介中心性
  closeness: number // 接近中心性
}

export interface NetworkEdge {
  source: string
  target: string
  weight?: number
}

export interface CentralityResult {
  nodes: NetworkNode[]
  edges: NetworkEdge[]
  interestingness: Map<string, number> // 有趣度 = 中介 / 程度
}

/**
 * 中心性计算器
 * 支持计算 Betweenness 和 Closeness 中心性
 */
export class CentralityAnalyzer {
  /**
   * 构建邻接表表示的图
   */
  private buildGraph(edges: NetworkEdge[]): Map<string, Set<string>> {
    const graph = new Map<string, Set<string>>()

    for (const edge of edges) {
      if (!graph.has(edge.source)) {
        graph.set(edge.source, new Set())
      }
      graph.get(edge.source)!.add(edge.target)

      // 如果需要无向图，也添加反向边
      if (!graph.has(edge.target)) {
        graph.set(edge.target, new Set())
      }
      // 注释掉反向边以实现有向图
      // graph.get(edge.target)!.add(edge.source)
    }

    return graph
  }

  /**
   * BFS 最短路径查询
   * 返回从 source 到所有其他节点的最短路径数
   */
  private bfsShortestPaths(
    source: string,
    graph: Map<string, Set<string>>
  ): Map<string, number[]> {
    const dist = new Map<string, number>()
    const paths = new Map<string, number>()
    const queue: string[] = [source]

    // 初始化
    dist.set(source, 0)
    for (const node of graph.keys()) {
      paths.set(node, 0)
    }
    paths.set(source, 1)

    // BFS
    while (queue.length > 0) {
      const u = queue.shift()!
      const neighbors = graph.get(u) || new Set()

      for (const v of neighbors) {
        const currentDist = dist.get(u) || Infinity
        const vDist = dist.get(v) ?? Infinity

        if (vDist > currentDist + 1) {
          // 更短的路径
          dist.set(v, currentDist + 1)
          paths.set(v, paths.get(u) || 0)
          queue.push(v)
        } else if (vDist === currentDist + 1) {
          // 等长的路径，累加数量
          paths.set(v, (paths.get(v) || 0) + (paths.get(u) || 0))
        }
      }
    }

    const result = new Map<string, number[]>()
    for (const [node, d] of dist) {
      if (node !== source) {
        result.set(node, [d, paths.get(node) || 0])
      }
    }

    return result
  }

  /**
   * 计算节点的中介中心性（Betweenness Centrality）
   * BC(v) = 通过节点 v 的最短路径数 / 所有最短路径数
   */
  computeBetweenness(edges: NetworkEdge[]): Map<string, number> {
    const graph = this.buildGraph(edges)
    const nodeSet = new Set(graph.keys())
    const betweenness = new Map<string, number>()

    // 初始化
    for (const node of nodeSet) {
      betweenness.set(node, 0)
    }

    // 对每个节点对 (s, t)，计算通过 v 的最短路径
    for (const s of nodeSet) {
      const shortestPaths = this.bfsShortestPaths(s, graph)

      // 回溯计算
      const delta = new Map<string, number>()
      for (const v of nodeSet) {
        delta.set(v, 0)
      }

      for (const t of nodeSet) {
        if (s !== t) {
          const [dist, paths] = shortestPaths.get(t) || [Infinity, 0]

          // 统计通过每个中间节点的路径
          for (const v of nodeSet) {
            if (v !== s && v !== t) {
              const vPaths = shortestPaths.get(v) || [Infinity, 0]
              if (vPaths[0] === dist - 1) {
                const contribution = (vPaths[1] / paths) * (1 + (delta.get(v) || 0))
                delta.set(v, (delta.get(v) || 0) + contribution)
              }
            }
          }
        }
      }

      // 累加到总的中介中心性
      for (const [v, d] of delta) {
        betweenness.set(v, (betweenness.get(v) || 0) + d)
      }
    }

    // 标准化
    const n = nodeSet.size
    for (const [node, bc] of betweenness) {
      if (n > 2) {
        betweenness.set(node, bc / ((n - 1) * (n - 2)))
      }
    }

    return betweenness
  }

  /**
   * 计算节点的接近中心性（Closeness Centrality）
   * CC(v) = (n-1) / 到所有其他节点的距离之和
   */
  computeCloseness(edges: NetworkEdge[]): Map<string, number> {
    const graph = this.buildGraph(edges)
    const nodeSet = new Set(graph.keys())
    const closeness = new Map<string, number>()

    for (const source of nodeSet) {
      const distances = this.bfsShortestPaths(source, graph)
      let sumDistance = 0
      let reachableCount = 0

      for (const [_, [dist]] of distances) {
        if (dist !== Infinity) {
          sumDistance += dist
          reachableCount++
        }
      }

      if (reachableCount > 0 && sumDistance > 0) {
        closeness.set(source, reachableCount / sumDistance)
      } else {
        closeness.set(source, 0)
      }
    }

    return closeness
  }

  /**
   * 计算节点的程度中心性（Degree Centrality）
   */
  computeDegree(edges: NetworkEdge[]): Map<string, number> {
    const degree = new Map<string, number>()

    for (const edge of edges) {
      degree.set(edge.source, (degree.get(edge.source) || 0) + 1)
      degree.set(edge.target, (degree.get(edge.target) || 0) + 1)
    }

    return degree
  }

  /**
   * 计算有趣度 = 中介中心性 ÷ 程度中心性
   * 高有趣度 = 高价值、低传播 = 套利机会
   */
  computeInterestingness(
    betweenness: number,
    degree: number
  ): number {
    if (degree === 0) return 0
    return betweenness / degree
  }

  /**
   * 将一组值标准化到 [0, 1] 范围
   */
  normalize(values: number[]): number[] {
    if (values.length === 0) return []

    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min

    if (range === 0) {
      return values.map(() => 0.5)
    }

    return values.map((v) => (v - min) / range)
  }

  /**
   * 分析网络并返回完整结果
   */
  analyzeNetwork(nodes: string[], edges: NetworkEdge[]): CentralityResult {
    const betweenness = this.computeBetweenness(edges)
    const closeness = this.computeCloseness(edges)
    const degree = this.computeDegree(edges)
    const interestingness = new Map<string, number>()

    // 标准化中心性值
    const betweennessValues = Array.from(betweenness.values())
    const normalizedBetweenness = new Map(
      Array.from(betweenness.entries()).map(([node, val], idx) => [
        node,
        this.normalize(betweennessValues)[idx],
      ])
    )

    const closenessValues = Array.from(closeness.values())
    const normalizedCloseness = new Map(
      Array.from(closeness.entries()).map(([node, val], idx) => [
        node,
        this.normalize(closenessValues)[idx],
      ])
    )

    // 计算有趣度
    for (const node of nodes) {
      const bc = normalizedBetweenness.get(node) || 0
      const d = degree.get(node) || 0
      const normalized_d = d / Math.max(...Array.from(degree.values())) || 1
      interestingness.set(node, this.computeInterestingness(bc, normalized_d))
    }

    // 构造返回结果
    const resultNodes: NetworkNode[] = nodes.map((node) => ({
      id: node,
      label: node,
      degree: degree.get(node) || 0,
      betweenness: normalizedBetweenness.get(node) || 0,
      closeness: normalizedCloseness.get(node) || 0,
    }))

    return {
      nodes: resultNodes,
      edges,
      interestingness,
    }
  }
}
