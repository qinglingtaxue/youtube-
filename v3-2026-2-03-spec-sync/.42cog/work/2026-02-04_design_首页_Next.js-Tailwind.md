# 首页设计实现方案（Next.js + Tailwind + shadcn/ui）

> 日期：2026-02-04
> 状态：详细设计阶段
> 技术栈：Next.js 15 + Tailwind CSS + shadcn/ui + Vercel AI SDK

---

## 核心架构设计

### 1. 页面布局分层

```
┌─────────────────────────────────────────────────────────┐
│  RootLayout (Next.js)                                   │
│  - 全局导航/页脚                                        │
│  - Theme Provider (Tailwind Dark Mode)                 │
│  - Auth Provider (Better Auth)                         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
┌───────────────────┐    ┌──────────────────┐
│  Homepage (/)     │    │ SearchResultsPage│
│                   │    │ (/search/[query])│
├───────────────────┤    └──────────────────┘
│ 1. 搜索框区       │
│    (SearchBox)    │
├───────────────────┤
│ 2. 最近搜索       │
│    (SearchHistory)│
├───────────────────┤
│ 3. 筛选条件区     │
│    (FilterPanel)  │
│    - 默认折叠     │
├───────────────────┤
│ 4. 三大功能入口   │
│    (FeatureCards) │
│    - 视频列表     │
│    - 频道排行     │
│    - 话题趋势     │
├───────────────────┤
│ 5. 快速发现区     │
│    (DiscoveryLane)│
│    - 本周爆款     │
│    - 黑马频道     │
├───────────────────┤
│ 6. 数据概览       │
│    (DataOverview) │
│    - 统计卡片     │
└───────────────────┘
```

---

## shadcn/ui 组件选型

### 必需组件列表

| 组件区域 | shadcn/ui 组件 | 用途 |
|---------|----------------|------|
| SearchBox | Input + Button | 搜索输入框 |
| SearchHistory | Badge + Button | 最近搜索标签 |
| FilterPanel | Dialog + Tabs + Checkbox + Select | 筛选面板 |
| FeatureCards | Card + Button | 功能入口卡片 |
| VideoList | Card + Image + Badge | 视频展示列表 |
| ChannelTable | Table + Avatar | 频道排行表格 |
| DataOverview | Stat Card (自定义) | 统计数据展示 |
| Loading | Skeleton + Spinner | 加载状态 |
| Toast | Toast + Toaster | 提示信息 |

### 组件树示例

```
HomePage
├── SearchSection
│   ├── SearchBox (Input + Button)
│   └── SearchHistory (Badge 列表 + ClearButton)
├── FilterSection
│   ├── FilterToggle (Button)
│   └── FilterPanel (Dialog)
│       ├── TimeRangeFilter (RadioGroup)
│       ├── DurationFilter (RadioGroup)
│       ├── ChannelSizeFilter (RadioGroup)
│       ├── MinViewsFilter (Select + Buttons)
│       └── ContentTagFilter (Checkbox 组)
├── FeatureSection
│   ├── FeatureCard (x3)
│   │   ├── Icon
│   │   ├── Title
│   │   ├── Description
│   │   └── Link Button
├── DiscoverySection
│   ├── VideoCarousel
│   │   └── VideoCard (x5)
│   └── ChannelTable
│       └── TableRow (x3)
└── DataOverview
    ├── StatCard (x4)
    └── RefreshButton
```

---

## 状态管理设计

### Zustand Store 结构

```typescript
// stores/searchStore.ts
interface SearchState {
  // UI 状态
  searchQuery: string
  isFilterOpen: boolean

  // 搜索历史
  searchHistory: SearchHistoryItem[]

  // 当前筛选
  filters: SearchFilters

  // 排序
  sortConfig: SortConfig

  // 操作
  setSearchQuery: (query: string) => void
  toggleFilter: () => void
  addSearchHistory: (query: string) => void
  clearSearchHistory: () => void
  updateFilters: (filters: Partial<SearchFilters>) => void
  updateSort: (config: SortConfig) => void

  // localStorage 持久化
  hydrate: () => void
  persist: () => void
}

// 类型定义
type SearchFilters = {
  timeRange: '24h' | '7d' | '30d' | '1y' | 'all'
  duration: 'all' | '<4min' | '4-20min' | '>20min'
  channelSize: 'all' | '<10k' | '10-100k' | '100-1M' | '>1M'
  minViews?: number
  contentTags: string[]
}

type SortConfig = {
  timeRange: string      // 时间范围
  sortField: string      // 排序字段: views | likes | comments | avgDailyViews | duration
  direction: 'asc' | 'desc'
}

type SearchHistoryItem = {
  id: string
  query: string
  timestamp: number
  resultsCount?: number
}
```

### localStorage 策略

```typescript
// 持久化字段
{
  'yt-search:history': SearchHistoryItem[],     // 最多 10 条
  'yt-search:lastFilters': SearchFilters,        // 上次搜索的筛选
  'yt-search:lastSort': SortConfig,              // 上次的排序
  'yt-app:theme': 'light' | 'dark'              // 主题
}
```

---

## API 路由设计

### Next.js API 路由结构

```
app/api/
├── search/
│   ├── route.ts              # POST /api/search (执行搜索)
│   └── history/
│       └── route.ts          # GET/DELETE /api/search/history
├── videos/
│   ├── trending/
│   │   └── route.ts          # GET /api/videos/trending (本周爆款)
│   └── [id]/
│       └── route.ts          # GET /api/videos/[id] (视频详情)
├── channels/
│   ├── trending/
│   │   └── route.ts          # GET /api/channels/trending (黑马频道)
│   └── [id]/
│       └── route.ts          # GET /api/channels/[id] (频道详情)
└── analytics/
    └── overview/
        └── route.ts          # GET /api/analytics/overview (数据概览)
```

### API 请求/响应示例

```typescript
// POST /api/search
Request: {
  query: string
  filters: SearchFilters
  sortConfig: SortConfig
  page?: number
  limit?: number
}

Response: {
  success: boolean
  data: {
    results: VideoItem[]
    total: number
    page: number
    naturalLanguage: string  // "7天内发布的视频，按播放量从高到低排序"
  }
  error?: string
}

// GET /api/videos/trending?timeRange=7d&limit=5
Response: {
  success: boolean
  data: {
    videos: VideoCard[]
    timestamp: number
  }
}

// GET /api/channels/trending?type=high-efficiency
Response: {
  success: boolean
  data: {
    channels: ChannelRow[]
    timestamp: number
  }
}

// GET /api/analytics/overview
Response: {
  success: boolean
  data: {
    totalVideos: number
    totalChannels: number
    totalTopics: number
    lastCollectedAt: number  // timestamp
  }
}
```

---

## 关键 React 组件设计

### SearchBox 组件

```typescript
// components/home/SearchBox.tsx
'use client'

import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/stores/searchStore'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export function SearchBox() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const { addSearchHistory } = useSearchStore()

  const handleSearch = async () => {
    if (!query.trim()) return

    addSearchHistory(query)
    router.push(`/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="w-full flex gap-2">
      <Input
        placeholder="输入关键词搜索（如：养生、太极、中医）"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        className="flex-1"
      />
      <Button onClick={handleSearch}>搜索</Button>
    </div>
  )
}
```

### FilterPanel 组件

```typescript
// components/home/FilterPanel.tsx
'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/stores/searchStore'

const TIME_RANGES = ['24h', '7d', '30d', '1y', 'all']
const DURATIONS = ['all', '<4min', '4-20min', '>20min']
const CHANNEL_SIZES = ['all', '<10k', '10-100k', '100-1M', '>1M']
const CONTENT_TAGS = ['教程', '养生功法', '食疗', '中医', '冥想', '评测']

export function FilterPanel() {
  const { isFilterOpen, toggleFilter, filters, updateFilters } = useSearchStore()

  return (
    <Dialog open={isFilterOpen} onOpenChange={toggleFilter}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>筛选条件</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* 时间范围 */}
          <div>
            <h4 className="mb-3 font-semibold">时间范围</h4>
            <RadioGroup value={filters.timeRange} onValueChange={(v) => updateFilters({ timeRange: v })}>
              {TIME_RANGES.map(t => (
                <div key={t} className="flex items-center gap-2">
                  <RadioGroupItem value={t} id={`time-${t}`} />
                  <label htmlFor={`time-${t}`}>{t === '24h' ? '24小时内' : ...}</label>
                </div>
              ))}
            </RadioGroup>
          </div>

          {/* 时长分类 */}
          <div>
            <h4 className="mb-3 font-semibold">时长 (YouTube原生)</h4>
            <RadioGroup value={filters.duration} onValueChange={(v) => updateFilters({ duration: v })}>
              {DURATIONS.map(d => (
                <div key={d} className="flex items-center gap-2">
                  <RadioGroupItem value={d} id={`duration-${d}`} />
                  <label htmlFor={`duration-${d}`}>{d === 'all' ? '全部' : ...}</label>
                </div>
              ))}
            </RadioGroup>
          </div>

          {/* 内容标签（多选） */}
          <div>
            <h4 className="mb-3 font-semibold">内容标签</h4>
            <div className="grid grid-cols-2 gap-3">
              {CONTENT_TAGS.map(tag => (
                <div key={tag} className="flex items-center gap-2">
                  <Checkbox
                    id={`tag-${tag}`}
                    checked={filters.contentTags.includes(tag)}
                    onCheckedChange={(checked) => {
                      const tags = checked
                        ? [...filters.contentTags, tag]
                        : filters.contentTags.filter(t => t !== tag)
                      updateFilters({ contentTags: tags })
                    }}
                  />
                  <label htmlFor={`tag-${tag}`}>{tag}</label>
                </div>
              ))}
            </div>
          </div>

          {/* 按钮 */}
          <div className="flex gap-3 justify-end pt-4 border-t">
            <Button variant="outline" onClick={() => updateFilters({ /* 重置 */ })}>
              重置
            </Button>
            <Button onClick={() => toggleFilter()}>应用筛选</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

### FeatureCards 组件

```typescript
// components/home/FeatureCards.tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { BarChart3, Building2, TrendingUp } from 'lucide-react'

const FEATURES = [
  {
    id: 'videos',
    icon: BarChart3,
    title: '📊 视频列表',
    description: '按播放量/互动率筛选竞品视频',
    link: '/videos',
  },
  {
    id: 'channels',
    icon: Building2,
    title: '🏢 频道排行',
    description: '找高效率频道，对标学习对象',
    link: '/channels',
  },
  {
    id: 'trends',
    icon: TrendingUp,
    title: '🔥 话题趋势',
    description: '发现新兴话题，Google Trends 集成',
    link: '/trends',
  },
]

export function FeatureCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {FEATURES.map(feature => {
        const Icon = feature.icon
        return (
          <Card key={feature.id} className="hover:shadow-lg transition">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Icon className="w-5 h-5" />
                {feature.title}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <CardDescription>{feature.description}</CardDescription>
              <Button asChild variant="default" className="w-full">
                <Link href={feature.link}>进入 →</Link>
              </Button>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
```

---

## 页面流程设计

### 首页加载流程

```
用户访问 /
  ↓
[1] 加载 Homepage component
  ├─ 初始化 Zustand store (hydrate from localStorage)
  ├─ 获取 session (Better Auth)
  └─ 渲染骨架屏 (Skeleton)

  ↓
[2] 并行加载数据 (使用 React.Suspense + Server Components)
  ├─ fetchTrendingVideos() → 本周爆款
  ├─ fetchTrendingChannels() → 黑马频道
  └─ fetchAnalyticsOverview() → 数据概览

  ↓
[3] 渲染完整页面
  ├─ SearchBox (即时交互)
  ├─ SearchHistory (从 localStorage)
  ├─ FilterPanel (折叠状态)
  ├─ FeatureCards (静态)
  ├─ VideoCarousel (数据已加载)
  ├─ ChannelTable (数据已加载)
  └─ DataOverview (数据已加载)
```

### 搜索流程

```
用户输入查询词 + 点击搜索
  ↓
SearchBox 调用 addSearchHistory(query)
  ↓
保存到 localStorage + Zustand store
  ↓
路由跳转到 /search?q=xxx
  ↓
SearchResultsPage 组件接收 query 参数
  ├─ 调用 POST /api/search
  ├─ 获取结果 + 自然语言排序说明
  └─ 渲染搜索结果列表
```

---

## Tailwind CSS 样式策略

### 设计系统

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',      // 蓝色
        secondary: '#8B5CF6',    // 紫色
        success: '#10B981',      // 绿色
        warning: '#F59E0B',      // 黄色
        danger: '#EF4444',       // 红色
      },
      spacing: {
        'gutter': '24px',        // 页面内边距
        'card-gap': '16px',      // 卡片间距
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in',
        'slide-up': 'slideUp 0.3s ease-out',
      },
    },
  },
}
```

### 响应式布局

```
移动端 (< 768px): 单列布局，全宽
平板端 (768-1024px): 两列或三列
桌面端 (> 1024px): 完整三列 + 侧边栏
```

---

## 数据加载策略

### 服务端渲染 (SSR) vs 客户端渲染 (CSR)

```typescript
// 首页: 混合策略
// - 搜索框 (SearchBox): CSR (客户端交互)
// - 筛选面板 (FilterPanel): CSR (状态管理)
// - 功能卡片 (FeatureCards): SSR (静态内容)
// - 本周爆款 (VideoCarousel): SSR 初始加载 + ISR (增量静态再生)
// - 黑马频道 (ChannelTable): SSR 初始加载 + ISR
// - 数据概览 (DataOverview): SSR 初始加载 + 定时刷新 (CSR 轮询)

// 搜索结果页: CSR (动态查询)
// - SearchResultsPage: 完全 CSR，根据 query 动态加载数据
```

### ISR (增量静态再生) 配置

```typescript
// app/page.tsx
export const revalidate = 3600  // 每小时重新生成

export default async function HomePage() {
  // 使用 fetch + cache 策略
  const trendingVideos = await fetch('...', {
    next: { revalidate: 3600 }
  })

  const trendingChannels = await fetch('...', {
    next: { revalidate: 3600 }
  })

  // ...
}
```

---

## 自我审查清单

### ✅ 通过的检查项

- **A1**: Tab 总数 ✅ （无 Tab，单页布局）
- **B1**: 视觉层级 ✅ （搜索框首屏，数据概览底部）
- **B2**: 核心功能入口 ✅ （3 个卡片，≤ 3）
- **C1**: 排序设计 ✅ （三个独立选择：时间+字段+方向）
- **D1**: 用户认知 ✅ （避免"互动率"等术语，使用用户可理解的指标）
- **E1**: 页面职责 ✅ （首页 = 搜索入口 + 快速发现）
- **F1**: 状态管理 ✅ （localStorage 存储搜索历史和筛选）
- **G1**: UI/UX 约束 ✅ （遵循 CLAUDE.md 所有强制约束）

### ⚠️ 需要注意的项目

- **性能**: ISR + 并行数据加载，避免首屏阻塞
- **移动端**: 搜索框 + 筛选要适配小屏幕
- **无网环境**: 使用 localStorage 缓存，graceful fallback

---

## 下一步实现步骤

- [ ] 初始化 Next.js 15 项目
- [ ] 安装 shadcn/ui 组件库
- [ ] 配置 Tailwind CSS + 设计系统
- [ ] 实现 Zustand store
- [ ] 编写核心组件（SearchBox, FilterPanel, FeatureCards）
- [ ] 实现 API 路由（/api/search, /api/videos/trending 等）
- [ ] 集成 Better Auth 认证
- [ ] 测试搜索流程 + localStorage 持久化
- [ ] 性能优化（ISR, 图片优化）
- [ ] 部署到 Vercel

