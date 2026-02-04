# Phase 6 - 信息报告页面实现计划

> 日期：2026-02-04
> 状态：计划中
> 优先级：🟡 中
> 预估工时：4-5 天
> 前置条件：Phase 4 完成（Phase 5 可并行）

---

## 页面概览

信息报告页面是一个**推理链式分析报告**，展示 4 条关键洞察和支撑数据。

### 核心特点

- **推理链展示**：数据 → 步骤 → 结论
- **置信度标注**：每条推理步骤都标注置信度（如 60%、88%）
- **嵌入式图表**：结论卡片内嵌对应的数据图表
- **可展开详情**：点击"展开数据"查看推理细节
- **自然语言生成**：AI 生成的洞察文案

### 示例结论

> **结论 1：市场竞争分散**
>
> 摘要：养生话题前 10 名视频仅占总播放量的 23%，市场竞争格局分散。
>
> 推理：
> - Top 1 视频播放量：245 万 (置信度：99%)
> - Top 10 占比：23% (置信度：88%)
> - 推断：蓝海市场，分散竞争 (置信度：76%)

---

## 页面布局设计

```
┌────────────────────────────────────────────────────────┐
│  ← 返回首页        📊 信息报告                          │
└────────────────────────────────────────────────────────┘

┌─ 全局筛选器 ───────────────────────────────────────────┐
│  关键词: [养生 ▼]  时间范围: [7天 ▼]                  │
│  当前报告：养生话题，过去 7 天采集 156 条视频         │
└────────────────────────────────────────────────────────┘

┌─ 报告头 ───────────────────────────────────────────────┐
│  📄 信息报告 - 推理链式分析                            │
│  基于 156 条视频、24 个频道的自动化洞察                │
│  报告生成时间：2026-02-04 09:30 UTC                    │
└────────────────────────────────────────────────────────┘

┌─ 结论卡片 1 ───────────────────────────────────────────┐
│  💡 结论 1：市场竞争分散                              │
│  ────────────────────────────────────────────────────  │
│  摘要：养生话题前 10 名视频仅占总播放量的 23%，       │
│        市场竞争格局分散。                               │
│                                                         │
│  [▼ 展开推理链]                                        │
│                                                         │
│  ┌─ 推理过程 ────────────────────────────────────────┐│
│  │ Step 1: 统计 Top 10 视频                         ││
│  │   - Top 1: 245 万 浏览        (99% 置信度)      ││
│  │   - Top 2: 189 万 浏览                            ││
│  │   - ...                                             ││
│  │   - Top 10: 45 万 浏览                            ││
│  │   - 小计：1,234 万 浏览                           ││
│  │                                                    ││
│  │ Step 2: 计算占比                                  ││
│  │   - Top 10 占比 = 1,234 万 ÷ 5,340 万 = 23%    ││
│  │   (88% 置信度)                                    ││
│  │                                                    ││
│  │ Step 3: 推断市场格局                              ││
│  │   - CR10 < 50% → 竞争分散 (76% 置信度)          ││
│  │   - 机会：相对容易进入市场                         ││
│  │                                                    ││
│  └────────────────────────────────────────────────────┘│
│                                                         │
│  📊 支撑数据：                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [柱状图：Top 10 视频播放量对比]                 │  │
│  │ ... 嵌入 recharts 柱状图 ...                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  🎯 行动建议：                                          │
│  → 创作更新的内容（竞品更新频率分析）                   │
│  → 找准细分角度（未被充分覆盖的子话题）                 │
│  → 学习 Top 3 频道的内容策略（创作者中心）             │
│                                                         │
└────────────────────────────────────────────────────────┘

┌─ 结论卡片 2-4：... (同上) ──────────────────────────────┐
│  （卡片 2：视频质量梯度、卡片 3：频道增长趋势、        │
│   卡片 4：关键词热度变化）                             │
└────────────────────────────────────────────────────────┘

┌─ 页脚 ──────────────────────────────────────────────────┐
│  最后更新：2 小时前 | [📥 导出报告 PDF] [🔄 重新生成]  │
└────────────────────────────────────────────────────────┘
```

---

## 核心数据结构

### 1. 结论卡片（ConclusionCard）

```typescript
interface ConclusionCard {
  id: string                    // 1-4
  title: string                 // 结论标题（如"市场竞争分散"）
  summary: string               // 摘要文案（2-3 句）
  reasoning: ReasoningChain     // 推理链
  supportingChart: ChartConfig  // 支撑图表
  actionItems: string[]         // 行动建议（3-5 条）
  generatedAt: string           // 生成时间
  confidence: number            // 整体置信度 (0-1)
}
```

### 2. 推理链（ReasoningChain）

```typescript
interface ReasoningChain {
  steps: ReasoningStep[]
  conclusion: string
}

interface ReasoningStep {
  sequence: number              // 步骤序号 (1, 2, 3...)
  title: string                 // 步骤标题
  data: {
    label: string
    value: any
  }[]
  inference: string             // 推理结果
  confidence: number            // 该步骤的置信度 (0-1)
  note?: string                 // 补充说明
}
```

### 3. 图表配置（ChartConfig）

```typescript
interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'histogram'
  title: string
  data: any[]
  xAxis?: AxisConfig
  yAxis?: AxisConfig
  config?: Record<string, any>  // Recharts 特定配置
}
```

### 4. 信息报告页面状态

```typescript
interface InfoReportState {
  keyword: string                      // 当前关键词
  timeRange: '7d' | '30d' | '90d'     // 时间范围
  conclusions: ConclusionCard[]        // 4 条结论
  metadata: {
    videoCount: number
    channelCount: number
    generatedAt: string
  }
  expanded: Map<string, boolean>       // 哪些卡片展开
}
```

---

## 实现任务清单

### 第 1 步：创建页面框架（2 小时）

**文件**：`app/insights/info-report/page.tsx`

**功能**：
1. [ ] 导航栏（返回按钮）
2. [ ] 全局筛选器（关键词 + 时间范围）
3. [ ] 报告头信息
4. [ ] 结论卡片列表容器
5. [ ] 数据加载状态
6. [ ] 错误处理

**代码框架**：
```typescript
'use client'

export default function InfoReportPage() {
  const [keyword, setKeyword] = useState('养生')
  const [timeRange, setTimeRange] = useState('7d')
  const [conclusions, setConclusions] = useState<ConclusionCard[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 加载报告数据
    fetchInfoReport(keyword, timeRange)
  }, [keyword, timeRange])

  return (
    <div>
      {/* 导航 */}
      {/* 筛选器 */}
      {/* 报告头 */}
      {/* 结论卡片列表 */}
      {/* 页脚 */}
    </div>
  )
}
```

---

### 第 2 步：实现结论卡片组件（3 小时）

**文件**：`components/insights/ConclusionCard.tsx`

**功能**：
1. [ ] 卡片头（序号 + 标题 + 摘要）
2. [ ] 展开/收起按钮
3. [ ] 推理链显示（条件渲染）
4. [ ] 嵌入式图表
5. [ ] 行动建议列表

**代码框架**：
```typescript
export function ConclusionCard({ card, expanded, onToggle }: Props) {
  return (
    <div className="bg-white border rounded-lg p-6 mb-6">
      {/* 卡片头 */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold">
            💡 结论 {card.id}：{card.title}
          </h3>
          <p className="text-gray-600 mt-2">{card.summary}</p>
        </div>
        <button onClick={() => onToggle(card.id)}>
          {expanded ? '▼' : '▶'} 展开推理链
        </button>
      </div>

      {/* 推理链（展开时显示） */}
      {expanded && (
        <div className="bg-gray-50 rounded p-4 mb-4">
          <ReasoningChain chain={card.reasoning} />
        </div>
      )}

      {/* 图表 */}
      <div className="mb-4">
        <ChartRenderer config={card.supportingChart} />
      </div>

      {/* 行动建议 */}
      <div className="border-t pt-4">
        <h4 className="font-semibold mb-3">🎯 行动建议：</h4>
        <ul className="space-y-2">
          {card.actionItems.map(item => (
            <li key={item} className="text-sm flex gap-2">
              <span>→</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
```

---

### 第 3 步：实现推理链组件（2 小时）

**文件**：`components/insights/ReasoningChain.tsx`

**功能**：
1. [ ] 步骤列表显示
2. [ ] 置信度进度条/百分比
3. [ ] 步骤间的连接线（可选视觉效果）

**代码框架**：
```typescript
export function ReasoningChain({ chain }: Props) {
  return (
    <div className="space-y-4">
      {chain.steps.map((step, idx) => (
        <div key={idx} className="relative pl-8">
          {/* 步骤序号圆圈 */}
          <div className="absolute left-0 top-1 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
            {step.sequence}
          </div>

          {/* 步骤内容 */}
          <div className="bg-white border-l-2 border-blue-500 pl-4">
            <h5 className="font-semibold">{step.title}</h5>

            {/* 数据点 */}
            <div className="mt-2 space-y-1">
              {step.data.map(d => (
                <div key={d.label} className="text-sm">
                  <span className="text-gray-600">- {d.label}：</span>
                  <span className="font-semibold">{d.value}</span>
                </div>
              ))}
            </div>

            {/* 推理结果 + 置信度 */}
            <div className="mt-3">
              <p className="text-sm text-gray-700">{step.inference}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs text-gray-500">置信度：</span>
                <div className="w-24 h-1.5 bg-gray-200 rounded overflow-hidden">
                  <div
                    className="h-full bg-green-500"
                    style={{ width: `${step.confidence * 100}%` }}
                  />
                </div>
                <span className="text-xs font-semibold">
                  {Math.round(step.confidence * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* 步骤间连接线 */}
          {idx < chain.steps.length - 1 && (
            <div className="absolute left-2 top-10 w-0.5 h-8 bg-blue-300" />
          )}
        </div>
      ))}
    </div>
  )
}
```

---

### 第 4 步：实现数据获取 API（3 小时）

**文件**：`app/api/insights/info-report/route.ts`

**功能**：生成信息报告

**请求参数**：
```typescript
{
  keyword: string
  timeRange: '7d' | '30d' | '90d'
}
```

**响应**：
```typescript
{
  success: boolean
  data: {
    keyword: string
    timeRange: string
    conclusions: ConclusionCard[]
    metadata: {
      videoCount: number
      channelCount: number
      generatedAt: string
    }
  }
}
```

**实现步骤**：
1. [ ] 查询指定关键词和时间范围的数据
2. [ ] 调用推理引擎生成 4 条结论
3. [ ] 计算每条结论的置信度
4. [ ] 准备支撑数据和图表配置
5. [ ] 生成行动建议

**推理引擎逻辑**：
```typescript
class InsightGenerator {
  // 结论 1：市场竞争分散度
  generateCompetitionInsight(videos: Video[]): ConclusionCard {
    const top10Videos = videos.slice(0, 10)
    const top10Views = top10Videos.reduce((sum, v) => sum + v.views, 0)
    const totalViews = videos.reduce((sum, v) => sum + v.views, 0)
    const cr10 = top10Views / totalViews

    return {
      title: cr10 < 0.3 ? '市场竞争分散' : '市场集中度高',
      summary: `前 10 名视频占比 ${(cr10 * 100).toFixed(1)}%，${
        cr10 < 0.3 ? '竞争格局分散' : '少数大号垄断'
      }`,
      // ... 其他字段
    }
  }

  // 结论 2：视频质量梯度
  generateQualityGradient(videos: Video[]): ConclusionCard {
    // 比较 Top 10 和 Bottom 10 的质量指标
  }

  // 结论 3：频道增长趋势
  generateChannelGrowth(channels: Channel[]): ConclusionCard {
    // 分析频道的平均增速
  }

  // 结论 4：关键词热度变化
  generateKeywordTrend(data: TimeSeriesData[]): ConclusionCard {
    // 对比不同时间段的热度
  }
}
```

---

### 第 5 步：实现图表渲染组件（2 小时）

**文件**：`components/insights/ChartRenderer.tsx`

**功能**：根据配置类型渲染不同的图表

```typescript
export function ChartRenderer({ config }: Props) {
  switch (config.type) {
    case 'bar':
      return <BarChart data={config.data} {...config.config} />
    case 'line':
      return <LineChart data={config.data} {...config.config} />
    case 'pie':
      return <PieChart data={config.data} {...config.config} />
    case 'scatter':
      return <ScatterChart data={config.data} {...config.config} />
    default:
      return null
  }
}
```

---

### 第 6 步：集成到应用（1 小时）

**文件修改**：
1. [ ] `lib/types.ts` - 添加 ConclusionCard 等类型
2. [ ] `lib/stores/` - 创建 infoReportStore（可选）
3. [ ] 导航菜单 - 添加"信息报告"链接

---

## 验收标准

### 功能验收

- [ ] 页面加载正常，显示筛选器和 4 条结论卡片
- [ ] 筛选器切换生效，报告重新加载
- [ ] 结论卡片可展开/收起
- [ ] 推理链正确显示步骤和置信度
- [ ] 嵌入式图表正确渲染
- [ ] 行动建议清晰易懂

### 内容验收

- [ ] 4 条结论的逻辑清晰
- [ ] 推理步骤的置信度合理（40%-99%）
- [ ] 行动建议可操作性强
- [ ] 文案自然通顺

### 性能验收

- [ ] 页面加载 < 2s
- [ ] 卡片展开/收起 < 100ms
- [ ] 图表渲染 < 1s

---

## 参考文件

- 设计文档：`.42cog/work/2026-02-04_v3_decision_信息报告设计.md`
- 布局草稿：`.42cog/work/2026-02-04_v3_design_信息报告-4结论布局草稿.md`

---

## 后续依赖

- ✅ Phase 4 需完成
- ℹ️ Phase 5 可并行或完成后进行
- ⏭️ Phase 7 可并行进行

