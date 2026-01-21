# TD-06: Next.js 前端技术栈 / Next.js Frontend Stack

> 基于 Next.js 的现代化全栈开发技术选型
> Modern full-stack development technology selection based on Next.js

---

## 决策概要 / Decision Summary

| 属性 / Attribute | 值 / Value |
|------------------|------------|
| 决策编号 / ID | TD-06 |
| 决策类型 / Type | 技术栈选型 / Stack Selection |
| 决策日期 / Date | 2026-01-19 |
| 来源对话 / Source | fbd8379a |
| 状态 / Status | 已执行 / Implemented |

---

## 技术栈结构 / Stack Structure

```
tech-stack/
├── framework/              # 框架层 / Framework Layer
│   └── Next.js 14+         # React 全栈框架
├── language/               # 语言层 / Language Layer
│   └── TypeScript 5+       # 类型安全
├── styling/                # 样式层 / Styling Layer
│   └── Tailwind CSS 3+     # 原子化 CSS
├── state/                  # 状态层 / State Layer
│   └── React Hooks         # 内置状态管理
├── data/                   # 数据层 / Data Layer
│   ├── Server Actions      # 服务端操作
│   └── API Routes          # REST API
└── deploy/                 # 部署层 / Deploy Layer
    └── Vercel              # 一键部署
```

---

## 技术选型索引 / Technology Selection Index

| # | 层级 / Layer | 技术 / Tech | 版本 / Version | 选择理由 / Rationale |
|---|--------------|-------------|----------------|---------------------|
| 1 | Framework | Next.js | 14+ | App Router、RSC、全栈能力 |
| 2 | Language | TypeScript | 5+ | 类型安全、IDE 支持、重构友好 |
| 3 | Styling | Tailwind CSS | 3+ | 原子化、快速开发、一致性 |
| 4 | State | React Hooks | - | 轻量、足够场景、无额外依赖 |
| 5 | UI Components | shadcn/ui | - | 可定制、无黑盒、复制粘贴 |
| 6 | Icons | Lucide React | - | 轻量、风格统一、tree-shaking |
| 7 | Charts | Recharts | - | React 原生、声明式、响应式 |
| 8 | Deploy | Vercel | - | Next.js 原生支持、自动 CI/CD |

---

## 技术详解 / Technology Details

### 1. Next.js 14+ 特性 / Next.js 14+ Features

| 特性 / Feature | 中文说明 | English Description |
|----------------|---------|---------------------|
| App Router | 基于文件系统的路由 | File-system based routing |
| Server Components | 服务端组件，减少客户端 JS | Server-side rendering |
| Server Actions | 服务端操作，表单处理 | Server-side form handling |
| API Routes | 内置 API 路由 | Built-in API endpoints |
| Streaming | 流式渲染 | Progressive rendering |
| Caching | 多层缓存策略 | Multi-layer caching |

**核心优势 / Key Advantages:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Next.js 14+ 架构                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Pages     │  │    API      │  │   Server    │                 │
│  │  (Routes)   │  │   Routes    │  │   Actions   │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         │                │                │                         │
│         └────────────────┼────────────────┘                         │
│                          │                                          │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │    React Server       │                              │
│              │    Components (RSC)   │                              │
│              └───────────────────────┘                              │
│                          │                                          │
│         ┌────────────────┼────────────────┐                         │
│         ▼                ▼                ▼                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Static    │  │   Dynamic   │  │  Streaming  │                 │
│  │   Render    │  │   Render    │  │   Render    │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2. 项目配置 / Project Configuration

```typescript
// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // 实验性功能
  experimental: {
    typedRoutes: true,        // 类型安全路由
  },

  // 图片优化
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'i.ytimg.com',  // YouTube 缩略图
      },
    ],
  },

  // 重定向
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ]
  },
}

export default nextConfig
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "noEmit": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#10B981',
        accent: '#F59E0B',
      },
    },
  },
  plugins: [],
}
```

---

### 3. 代码示例 / Code Examples

**页面组件 / Page Component:**

```tsx
// app/videos/page.tsx
import { Suspense } from 'react'
import { VideoList } from '@/components/video/VideoList'
import { VideoFilters } from '@/components/video/VideoFilters'
import { getVideos } from '@/lib/data'

interface SearchParams {
  filter?: string
  sort?: string
  page?: string
}

export default async function VideosPage({
  searchParams,
}: {
  searchParams: SearchParams
}) {
  const { filter = 'all', sort = 'views', page = '1' } = searchParams

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">视频榜单</h1>

      <VideoFilters
        currentFilter={filter}
        currentSort={sort}
      />

      <Suspense fallback={<VideoListSkeleton />}>
        <VideoListWrapper
          filter={filter}
          sort={sort}
          page={parseInt(page)}
        />
      </Suspense>
    </div>
  )
}

async function VideoListWrapper({
  filter,
  sort,
  page,
}: {
  filter: string
  sort: string
  page: number
}) {
  const videos = await getVideos({ filter, sort, page })
  return <VideoList videos={videos} />
}
```

**API 路由 / API Route:**

```typescript
// app/api/videos/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getVideos, VideoFilter } from '@/lib/data'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const filter = searchParams.get('filter') as VideoFilter || 'all'
  const sort = searchParams.get('sort') || 'views'
  const page = parseInt(searchParams.get('page') || '1')
  const limit = parseInt(searchParams.get('limit') || '20')

  try {
    const { videos, total } = await getVideos({
      filter,
      sort,
      page,
      limit,
    })

    return NextResponse.json({
      data: videos,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch videos' },
      { status: 500 }
    )
  }
}
```

**Server Action:**

```typescript
// app/actions/videos.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function refreshVideos() {
  // 触发数据重新采集
  await fetch(`${process.env.API_URL}/collect`, {
    method: 'POST',
  })

  // 重新验证页面缓存
  revalidatePath('/videos')

  return { success: true }
}
```

---

### 4. 备选方案对比 / Alternative Comparison

| 方案 / Option | 优点 / Pros | 缺点 / Cons | 评分 / Score |
|---------------|-------------|-------------|--------------|
| **Next.js** | 全栈、生态丰富、部署简单 | 学习曲线、版本迭代快 | **⭐⭐⭐⭐⭐** |
| Remix | 数据加载优雅、表单处理好 | 生态较小、市场份额低 | ⭐⭐⭐⭐ |
| Nuxt (Vue) | 上手简单、文档好 | Vue 生态、组件库少 | ⭐⭐⭐⭐ |
| SvelteKit | 性能最优、包体积小 | 生态不成熟、人才少 | ⭐⭐⭐ |
| Astro | 静态优先、多框架 | 交互性弱、动态场景差 | ⭐⭐⭐ |

---

## 快速导航 / Quick Navigation

### 想了解项目结构？ / Want project structure?
→ 阅读 [TD-07: 多页面交互架构](./07-确定多页面交互系统架构.md)

### 想了解数据获取？ / Want data fetching?
→ 查看 `app/api/` 和 `lib/data.ts`

### 想了解组件开发？ / Want component development?
→ 查看 `components/` 目录

### 想了解部署配置？ / Want deployment config?
→ 查看 `vercel.json` 和 `next.config.ts`

---

## 开发规范 / Development Standards

### 文件命名 / File Naming

| 类型 / Type | 规范 / Convention | 示例 / Example |
|-------------|-------------------|----------------|
| 页面文件 | `page.tsx` | `app/videos/page.tsx` |
| 布局文件 | `layout.tsx` | `app/layout.tsx` |
| 组件文件 | PascalCase | `VideoCard.tsx` |
| 工具文件 | camelCase | `formatDate.ts` |
| 类型文件 | camelCase | `video.ts` |
| API 路由 | `route.ts` | `app/api/videos/route.ts` |

### 目录组织 / Directory Organization

```
src/
├── app/                    # Next.js App Router
│   ├── (dashboard)/        # 路由分组
│   ├── api/                # API 路由
│   └── globals.css         # 全局样式
├── components/
│   ├── ui/                 # 通用 UI 组件
│   └── [feature]/          # 业务组件
├── lib/
│   ├── data.ts             # 数据获取
│   ├── utils.ts            # 工具函数
│   └── constants.ts        # 常量定义
└── types/
    └── index.ts            # 类型定义
```

---

## 注意事项 / Notes

1. **类型安全 / Type Safety**：充分利用 TypeScript，避免 `any`
2. **服务端优先 / Server First**：优先使用 Server Components
3. **按需加载 / Lazy Loading**：大组件使用 `dynamic` 导入
4. **图片优化 / Image Optimization**：使用 `next/image`
5. **缓存策略 / Caching**：合理配置 `revalidate`
6. **错误处理 / Error Handling**：使用 `error.tsx` 边界

---

## 相关决策 / Related Decisions

| 决策 / Decision | 关系 / Relation |
|-----------------|-----------------|
| [TD-07](./07-确定多页面交互系统架构.md) | 下游：页面结构设计 |
| [TD-14](./14-增加进度预估与网络速度显示功能.md) | 应用：进度 UI 实现 |

---

*最后更新 / Last Updated: 2026-01-20*
