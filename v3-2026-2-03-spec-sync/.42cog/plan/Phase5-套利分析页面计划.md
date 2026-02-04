# Phase 5 - 套利分析页面实现计划

> 日期：2026-02-04
> 状态：计划中
> 优先级：🔴 高
> 预估工时：5-7 天
> 前置条件：Phase 4 完成

---

## 页面概览

套利分析页面是一个多维度数据分析工具，展示视频/频道/赛道等的**有趣度**排名。

### 核心概念

**有趣度公式**：`有趣度 = 中介中心性 ÷ 程度中心性 = 价值 ÷ 传播力 = 套利机会`

- **高有趣度** = 高价值、低传播 = 蓝海市场（套利机会）
- **低有趣度** = 高传播、低价值 = 饱和市场

### 页面链接

路由：`/insights/arbitrage` 或 `/analytics/arbitrage`

---

## 页面布局设计

```
┌─────────────────────────────────────────────────────┐
│  ← 返回首页      💰 套利分析                        │
└─────────────────────────────────────────────────────┘

┌─ Tab 分组控制 ──────────────────────────────────────┐
│  📊 看数据:  [视频]  [频道]  [赛道]  [Google Trends]│
│  💰 找机会:  [有趣度] [中介] [程度]               │
└─────────────────────────────────────────────────────┘

┌─ 排序控制 ──────────────────────────────────────────┐
│  时间: [7天内 ▼]  字段: [有趣度 ▼]  方向: [高→低 ▼]│
│  当前: 7天内，按有趣度从高到低排序                  │
└─────────────────────────────────────────────────────┘

┌─ 图表区域 ──────────────────────────────────────────┐
│  根据选中 Tab 动态渲染：                            │
│                                                      │
│  [视频] Tab:                                        │
│  ├─ 左: 榜单类型选择 (黑马/爆款/增长最快)         │
│  ├─ 右: 力导向网络图 + 散点图 + 表格               │
│  └─ 底: 结论卡片 (如"蓝海市场")                    │
│                                                      │
│  [频道] Tab:                                        │
│  ├─ 类似布局                                       │
│  └─ 示例：新兴频道识别                             │
│                                                      │
│  [赛道] Tab:                                        │
│  └─ 话题/关键词的中心性分析                        │
│                                                      │
│  [有趣度/中介/程度] 榜单:                          │
│  └─ 简单的排序表格 (Top 20)                        │
└─────────────────────────────────────────────────────┘
```

---

## 核心数据结构

### 1. 视频数据（Video）

```typescript
interface Video {
  id: string
  title: string
  views: number
  likes: number
  comments: number
  duration: number
  publishedAt: string
  channelId: string
  channelName: string
  channelSubscribers: number

  // 中心性计算字段
  inDegree?: number      // 入度（被链接次数）
  outDegree?: number     // 出度（链接他人次数）
  betweenness?: number   // 中介中心性
  closeness?: number     // 接近中心性

  // 派生指标
  betweennessNorm?: number  // 标准化中介中心性 (0-1)
  interestingness?: number  // 有趣度 = 中介 / 程度
}
```

### 2. 中心性计算器（CentralityAnalyzer）

```typescript
interface NetworkNode {
  id: string
  label: string
  degree: number        // 出入度
  betweenness: number
  closeness: number
}

interface NetworkEdge {
  source: string
  target: string
  weight?: number
}

class CentralityAnalyzer {
  computeBetweenness(edges: NetworkEdge[]): Map<string, number>
  computeCloseness(edges: NetworkEdge[]): Map<string, number>
  normalize(values: number[]): number[]
  computeInterestingness(betweenness: number, degree: number): number
}
```

### 3. 榜单类型（RankingType）

```typescript
type RankingType =
  | 'interestingness'  // 有趣度 = 中介 / 程度
  | 'betweenness'      // 中介中心性（连接力）
  | 'closeness'        // 接近中心性（影响范围）

type DataDimension =
  | 'videos'           // 视频维度
  | 'channels'         // 频道维度
  | 'keywords'         // 关键词维度
  | 'topics'           // 话题维度
```

---

## 实现任务清单

### 第 1 步：创建页面框架（3 小时）

**文件**：`app/insights/arbitrage/page.tsx`

**功能**：
1. [ ] 导航栏（返回首页按钮）
2. [ ] Tab 分组控制（6 个 Tab）
3. [ ] 排序控制面板（时间范围 + 排序字段 + 方向）
4. [ ] 动态内容区域（根据 Tab 切换）
5. [ ] 加载状态和错误处理

**代码框架**：
```typescript
'use client'

export default function ArbitrageAnalysisPage() {
  const [activeDataTab, setActiveDataTab] = useState<'videos' | 'channels' | 'keywords'>('videos')
  const [activeRankingTab, setActiveRankingTab] = useState<'interestingness' | 'betweenness' | 'closeness'>('interestingness')
  const [sortConfig, setSortConfig] = useState({
    timeRange: '7d',
    field: 'interestingness',
    direction: 'desc'
  })

  return (
    <div>
      {/* 导航 */}
      {/* Tab 分组 */}
      {/* 排序控制 */}
      {/* 内容区域 */}
    </div>
  )
}
```

---

### 第 2 步：实现中心性计算模块（4 小时）

**文件**：`lib/analytics/centralityAnalyzer.ts`

**核心算法**：

```typescript
// 中介中心性（Betweenness Centrality）
// 衡量节点"在两个其他节点之间充当桥梁"的程度
computeBetweenness(edges: NetworkEdge[]): Map<string, number> {
  const nodeSet = new Set<string>()
  const graph = new Map<string, Set<string>>()

  // 构建图
  for (const edge of edges) {
    nodeSet.add(edge.source)
    nodeSet.add(edge.target)

    if (!graph.has(edge.source)) {
      graph.set(edge.source, new Set())
    }
    graph.get(edge.source)!.add(edge.target)
  }

  const betweenness = new Map<string, number>()

  // 对每个节点计算其中介中心性
  for (const node of nodeSet) {
    let count = 0
    // 使用 BFS 找最短路径...
    betweenness.set(node, count)
  }

  return betweenness
}

// 接近中心性（Closeness Centrality）
// 衡量节点"到其他节点的平均距离"
computeCloseness(edges: NetworkEdge[]): Map<string, number> {
  // 实现 Floyd-Warshall 或 BFS...
}

// 有趣度 = 中介 / 程度
computeInterestingness(betweenness: number, degree: number): number {
  return degree === 0 ? 0 : betweenness / degree
}
```

**关键函数**：
- `buildGraph(edges)` - 构建邻接表
- `shortestPath(graph, source, target)` - 最短路径（BFS）
- `computeAllPairsShortestPaths(edges)` - 全对最短路径
- `normalize(values)` - 标准化到 [0, 1]

---

### 第 3 步：实现数据获取 API（4 小时）

#### 3.1 GET /api/insights/arbitrage/videos

**功能**：获取视频维度的中心性数据

**请求参数**：
```typescript
{
  timeRange: '7d' | '30d' | '90d' | 'all'
  rankingType: 'interestingness' | 'betweenness' | 'closeness'
  limit?: 50
}
```

**响应**：
```typescript
{
  success: boolean
  data: {
    videos: Video[]
    network?: {
      nodes: NetworkNode[]
      edges: NetworkEdge[]
    }
    insights: {
      trend: string
      topInterestingVideos: Video[]
      conclusion: string
    }
  }
}
```

**实现步骤**：
1. [ ] 查询时间范围内的所有视频
2. [ ] 构建视频间的引用/相似网络
3. [ ] 计算中心性指标
4. [ ] 排序和分页
5. [ ] 生成洞察文案

#### 3.2 GET /api/insights/arbitrage/channels

类似 videos API，但数据维度是频道

#### 3.3 GET /api/insights/arbitrage/keywords

关键词维度的中心性分析

---

### 第 4 步：实现图表组件（6 小时）

#### 4.1 力导向网络图（NetworkGraph）

**文件**：`components/insights/NetworkGraph.tsx`

**库**：`react-force-graph`

**功能**：
- 显示网络节点和边
- 节点颜色按有趣度填充（蓝←→红）
- 节点大小按程度中心性（点击可高亮）
- 交互：拖拽、缩放、悬停显示详情

```typescript
import ForceGraph2D from 'react-force-graph-2d'

export function NetworkGraph({ nodes, edges, onNodeClick }: Props) {
  return (
    <ForceGraph2D
      graphData={{ nodes, links: edges }}
      nodeColor={node => {
        const hue = (1 - node.interestingness / maxInterestingness) * 240
        return `hsl(${hue}, 100%, 50%)`
      }}
      nodeVal={node => Math.sqrt(node.degree) * 5}
      onNodeClick={onNodeClick}
      {...config}
    />
  )
}
```

#### 4.2 散点图（ScatterPlot）

**文件**：`components/insights/ScatterPlot.tsx`

**库**：`recharts`

**坐标轴**：
- X 轴：程度中心性（degree）
- Y 轴：中介中心性（betweenness）
- 颜色：有趣度（蓝→红）
- 大小：播放量

```typescript
<ScatterChart width={600} height={400} margin={{ top: 20, right: 20 }}>
  <XAxis dataKey="degree" name="程度中心性" />
  <YAxis dataKey="betweenness" name="中介中心性" />
  <Scatter
    name="视频"
    data={videos}
    fill="#8884d8"
  />
</ScatterChart>
```

#### 4.3 表格（RankingTable）

**文件**：`components/insights/RankingTable.tsx`

**功能**：
- 显示 Top 20 排名
- 列：排名、标题、有趣度、中介、程度、播放量
- 可排序列
- 可点击展开详情

```typescript
<table>
  <thead>
    <tr>
      <th>排名</th>
      <th>标题</th>
      <th>有趣度</th>
      <th>中介中心性</th>
      <th>程度中心性</th>
      <th>播放量</th>
    </tr>
  </thead>
  <tbody>
    {videos.map((video, i) => (
      <tr key={video.id}>
        <td>#{i + 1}</td>
        <td>{video.title}</td>
        <td>{video.interestingness.toFixed(2)}</td>
        <td>{video.betweenness.toFixed(2)}</td>
        <td>{video.closeness.toFixed(2)}</td>
        <td>{formatNumber(video.views)}</td>
      </tr>
    ))}
  </tbody>
</table>
```

---

### 第 5 步：实现榜单切换逻辑（3 小时）

**文件**：`components/insights/ArbitrageTabPanels.tsx`

**功能**：
1. [ ] 内容标签页切换（Videos/Channels/Keywords）
2. [ ] 榜单类型切换（有趣度/中介/程度）
3. [ ] 排序控制（时间范围 + 方向）
4. [ ] 图表和表格的条件渲染
5. [ ] 数据加载状态

**交互流程**：
```
用户选择 Tab → 更新 URL 参数 → 触发 API 请求 → 重新计算中心性 → 渲染图表
```

---

### 第 6 步：添加结论卡片和洞察（2 小时）

**文件**：`components/insights/InsightCard.tsx`

**内容**：
- 蓝海市场识别："前 3 名有趣度视频都来自小频道"
- 增长趋势："过去 7 天新兴关键词"
- 竞争对标："Top 10 频道的视频覆盖率"

```typescript
<div className="bg-blue-50 border-l-4 border-blue-500 p-4">
  <h3 className="font-bold text-blue-900">💎 蓝海机会发现</h3>
  <p className="text-sm text-blue-800 mt-2">
    "养生"话题有趣度最高的 3 个视频都来自订阅数 &lt; 10k 的小频道，
    存在通过优质内容快速增长的机会。
  </p>
</div>
```

---

### 第 7 步：集成到应用（2 小时）

**文件修改**：
1. [ ] `lib/dynamic-imports.ts` - 添加 ArbitrageAnalysisPage 动态导入
2. [ ] `components/shared/Navbar.tsx` - 添加导航链接（或在首页功能卡片中）
3. [ ] `lib/types.ts` - 补充 ArbitrageAnalysis 相关类型
4. [ ] `lib/stores/` - 创建 arbitrageStore（可选）

---

## 依赖库安装

```bash
bun add recharts visx react-force-graph
bun add simple-statistics  # 统计计算
```

---

## 验收标准

### 功能验收

- [ ] 页面加载正常，显示 6 个 Tab
- [ ] Tab 切换不卡顿，API 请求正确
- [ ] 力导向网络图正常渲染（50-200 节点）
- [ ] 散点图显示正确的坐标轴和数据点
- [ ] 表格可排序，显示 Top 20
- [ ] 排序控制生效，图表实时更新
- [ ] 移动端响应式正确

### 性能验收

- [ ] 网络图加载 < 1s（< 200 节点）
- [ ] 表格排序 < 100ms
- [ ] 没有内存泄漏（长时间运行）

### 数据验收

- [ ] 有趣度计算正确（中介 / 程度）
- [ ] 中心性指标标准化到 [0, 1]
- [ ] 排序顺序正确
- [ ] API 错误处理完善

---

## 参考文件

- 设计文档：`.42cog/work/2026-02-04_v3_decision_套利页面布局.md`
- 图表策略：`.42cog/work/2026-02-04_v3_decision_图表选择策略.md`
- 现有类型：`lib/types.ts`

---

## 后续依赖

- ✅ Phase 4 需完成
- ⏭️ Phase 6 等待本阶段完成
- ⏭️ Phase 7 可并行进行

