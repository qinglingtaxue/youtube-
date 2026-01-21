# 技术决策索引 / Technical Decisions Index

> YouTube 内容创作流水线项目的 7 个核心技术决策
> 7 Core Technical Decisions for YouTube Content Creation Pipeline Project

---

## 目录结构 / Directory Structure

```
work/
├── TECHNICAL-DECISIONS.md           # 技术决策索引（本文档）/ This index
├── 04-采用RPA固化脚本矩阵架构.md      # 数据采集架构 / Data collection architecture
├── 05-设计pipeline规约生成机制.md     # 流程编排 / Pipeline orchestration
├── 06-选择NextJS作为前端技术栈.md     # 前端技术栈 / Frontend stack
├── 07-确定多页面交互系统架构.md       # 应用架构 / Application architecture
├── 13-确定采集关键词逻辑与近期视频筛选规则.md  # 采集逻辑 / Collection logic
├── 14-增加进度预估与网络速度显示功能.md      # UX 增强 / UX enhancement
└── 15-采用YouTube原生搜索过滤机制.md        # 过滤机制 / Filter mechanism
```

---

## 技术决策索引（按架构层级） / Decision Index (By Architecture Layer)

| # | 文件路径 / File Path | 中文名称 | English Name | 决策类型 / Type |
|---|---------------------|---------|--------------|----------------|
| 1 | `06-选择NextJS作为前端技术栈.md` | Next.js 技术栈选型 | Next.js Stack Selection | 技术栈选型 / Stack Selection |
| 2 | `04-采用RPA固化脚本矩阵架构.md` | RPA 矩阵架构 | RPA Matrix Architecture | 系统架构 / System Architecture |
| 3 | `05-设计pipeline规约生成机制.md` | Pipeline 规约机制 | Pipeline Specification | 系统架构 / System Architecture |
| 4 | `07-确定多页面交互系统架构.md` | 多页面交互架构 | Multi-page Architecture | 应用架构 / Application Architecture |
| 5 | `13-确定采集关键词逻辑与近期视频筛选规则.md` | 采集逻辑设计 | Collection Logic Design | 实现方案 / Implementation |
| 6 | `14-增加进度预估与网络速度显示功能.md` | 进度监控功能 | Progress Monitoring | 实现方案 / Implementation |
| 7 | `15-采用YouTube原生搜索过滤机制.md` | YouTube 原生过滤 | YouTube Native Filters | 实现方案 / Implementation |

---

## 技术架构总览 / Technical Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        技术栈选型 / Stack Selection                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  [TD-06] Next.js + React + TypeScript + Tailwind CSS          │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        系统架构 / System Architecture                │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐    │
│  │  [TD-04] RPA 矩阵架构    │    │  [TD-05] Pipeline 规约机制  │    │
│  │  • 浏览器自动化          │    │  • 声明式流程定义           │    │
│  │  • 多关键词并行采集      │───▶│  • 阶段解耦可替换           │    │
│  │  • 矩阵调度策略          │    │  • 配置驱动执行             │    │
│  └─────────────────────────┘    └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        应用架构 / Application Architecture           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  [TD-07] 多页面交互系统                                        │  │
│  │  /videos (榜单) → /channels (频道) → /analysis (分析)          │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        实现方案 / Implementation                     │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │ [TD-13]       │  │ [TD-14]       │  │ [TD-15]               │   │
│  │ 采集逻辑      │  │ 进度监控      │  │ YouTube 原生过滤      │   │
│  │ • 关键词分组  │  │ • 完成百分比  │  │ • sp 参数构建         │   │
│  │ • 优先级排序  │  │ • 剩余时间    │  │ • 时间/时长/类型      │   │
│  │ • 去重过滤    │  │ • 网速监控    │  │ • 减少无效采集        │   │
│  └───────────────┘  └───────────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 技术决策详解 / Decision Details

### 1. 技术栈选型 (TD-06) / Stack Selection

| 技术 / Tech | 选择 / Choice | 理由 / Rationale |
|-------------|---------------|------------------|
| 框架 / Framework | Next.js 14+ | 文件路由、SSR/SSG、API Routes |
| 语言 / Language | TypeScript | 类型安全、IDE 支持 |
| 样式 / Styling | Tailwind CSS | 原子化、快速开发 |
| 状态 / State | React Hooks | 轻量、足够场景 |

**核心优势 / Key Advantages:**
- 全栈能力，前后端统一代码库
- 社区活跃，生态丰富
- 部署简单（Vercel 一键部署）

```typescript
// Next.js App Router 示例
// app/videos/page.tsx
export default async function VideosPage() {
  const videos = await fetchVideos()
  return <VideoList videos={videos} />
}
```

---

### 2. 系统架构 (TD-04, TD-05) / System Architecture

#### 2.1 RPA 矩阵架构 (TD-04)

| 组件 / Component | 职责 / Responsibility | 技术 / Tech |
|------------------|----------------------|-------------|
| 任务调度器 | 管理采集任务队列 | Node.js |
| RPA 执行器 | 浏览器自动化操作 | Playwright |
| 数据解析器 | 提取页面数据 | Cheerio |
| 数据存储 | 持久化采集结果 | JSON/SQLite |

```
矩阵采集策略 / Matrix Collection Strategy
──────────────────────────────────────────
关键词维度: [游戏, 教程, Vlog, ...]
时间维度:   [24h, 7d, 30d, 90d]
排序维度:   [播放量, 上传时间, 相关度]

任务总数 = 关键词数 × 时间维度 × 排序维度
示例: 10 × 4 × 3 = 120 个采集任务
```

#### 2.2 Pipeline 规约机制 (TD-05)

```yaml
# pipeline.spec.yaml
pipeline:
  name: youtube-video-collection
  version: "1.0"

  stages:
    - name: collect
      type: rpa
      input: keywords.json
      output: raw_videos.json

    - name: transform
      type: process
      operations: [dedup, normalize, enrich]
      output: clean_videos.json

    - name: analyze
      type: compute
      metrics: [views, engagement, growth]
      output: analyzed_videos.json

    - name: present
      type: export
      formats: [json, csv, html]
```

---

### 3. 应用架构 (TD-07) / Application Architecture

| 页面 / Page | 路由 / Route | 功能 / Function |
|-------------|--------------|-----------------|
| 首页 | `/` | 数据概览仪表盘 |
| 视频榜单 | `/videos` | 爆款/潜力/热门视频 |
| 频道榜单 | `/channels` | 频道排行榜 |
| 数据分析 | `/analysis` | 趋势图表、洞察 |
| 采集管理 | `/collect` | 任务配置、执行 |

```
Next.js App Router 结构
──────────────────────────────────
src/
├── app/
│   ├── layout.tsx          # 全局布局
│   ├── page.tsx            # 首页 /
│   ├── videos/
│   │   ├── page.tsx        # /videos
│   │   ├── [id]/page.tsx   # /videos/:id
│   │   └── trending/page.tsx
│   ├── channels/
│   │   └── page.tsx        # /channels
│   └── api/
│       └── videos/route.ts # API 路由
├── components/
│   ├── ui/                 # 通用组件
│   ├── video/              # 视频相关
│   └── chart/              # 图表组件
└── lib/
    ├── data.ts             # 数据获取
    └── utils.ts            # 工具函数
```

---

### 4. 实现方案 (TD-13, TD-14, TD-15) / Implementation

#### 4.1 采集逻辑设计 (TD-13)

```typescript
// 关键词配置结构
interface KeywordConfig {
  group: string       // 分组名称
  words: string[]     // 关键词列表
  priority: 'high' | 'medium' | 'low'
}

// 采集过滤规则
function shouldCollect(video: Video): boolean {
  if (video.duration < 10) return false      // 时长 < 10秒
  if (video.views < 1000) return false       // 播放 < 1000
  if (existingIds.has(video.id)) return false // 已存在
  return true
}
```

#### 4.2 进度监控功能 (TD-14)

```typescript
interface ProgressState {
  total: number           // 总任务数
  completed: number       // 已完成数
  current: string         // 当前任务
  estimatedTime: number   // 预估剩余时间(秒)
  networkSpeed: number    // 网速 (bytes/s)
  successRate: number     // 成功率 (0-1)
}

// 进度计算
const progress = (completed / total) * 100
const eta = (total - completed) * avgTimePerTask
```

#### 4.3 YouTube 原生过滤 (TD-15)

| 过滤项 / Filter | 参数值 / Value | URL 编码 / Encoded |
|-----------------|----------------|-------------------|
| 最近1小时 | EgIIAQ== | EgIIAQ%3D%3D |
| 今天 | EgIIAg== | EgIIAg%3D%3D |
| 本周 | EgIIAw== | EgIIAw%3D%3D |
| 本月 | EgIIBA== | EgIIBA%3D%3D |
| 按播放量排序 | CAM= | CAM%3D |

```typescript
// URL 构建示例
function buildSearchUrl(keyword: string, options: SearchOptions) {
  const params = new URLSearchParams()
  params.set('search_query', keyword)

  let sp = ''
  if (options.sortBy === 'views') sp += 'CAM'
  if (options.uploadDate === 'week') sp += 'SBAgDEAE'

  if (sp) params.set('sp', sp)
  return `https://www.youtube.com/results?${params}`
}
```

---

## 技术要点 / Technical Notes

### Next.js API Route 示例

```typescript
// app/api/videos/route.ts
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const filter = searchParams.get('filter') || 'all'

  const videos = await getVideos({ filter })
  return NextResponse.json(videos)
}
```

### RPA 采集脚本示例

```typescript
// scripts/collect.ts
import { chromium } from 'playwright'

async function collectVideos(keyword: string) {
  const browser = await chromium.launch()
  const page = await browser.newPage()

  await page.goto(buildSearchUrl(keyword, { sortBy: 'views' }))
  await page.waitForSelector('ytd-video-renderer')

  const videos = await page.$$eval('ytd-video-renderer', nodes =>
    nodes.map(extractVideoData)
  )

  await browser.close()
  return videos
}
```

---

## 快速导航 / Quick Navigation

### 想了解前端技术选型？ / Want frontend stack?
→ 阅读 `06-选择NextJS作为前端技术栈.md`

### 想了解数据采集架构？ / Want collection architecture?
→ 阅读 `04-采用RPA固化脚本矩阵架构.md`

### 想了解流程编排设计？ / Want pipeline design?
→ 阅读 `05-设计pipeline规约生成机制.md`

### 想了解页面结构设计？ / Want page structure?
→ 阅读 `07-确定多页面交互系统架构.md`

### 想了解采集实现细节？ / Want collection details?
→ 阅读 `13-确定采集关键词逻辑与近期视频筛选规则.md`

---

## 决策依赖关系 / Decision Dependencies

```
TD-06 (Next.js)
    │
    └──▶ TD-07 (多页面架构)
              │
              └──▶ TD-14 (进度监控 UI)

TD-04 (RPA 架构)
    │
    ├──▶ TD-05 (Pipeline 规约)
    │
    ├──▶ TD-13 (采集逻辑)
    │         │
    │         └──▶ TD-15 (YouTube 过滤)
    │
    └──▶ TD-14 (进度监控)
```

---

## 注意事项 / Notes

1. **类型安全 / Type Safety**：所有数据结构使用 TypeScript 接口定义
2. **错误处理 / Error Handling**：RPA 采集需要完善的重试和降级机制
3. **性能优化 / Performance**：使用增量采集避免重复数据
4. **合规性 / Compliance**：遵守 YouTube TOS，控制采集频率
5. **可维护性 / Maintainability**：页面选择器变化时需要及时更新
6. **监控告警 / Monitoring**：网络异常和采集失败需要及时告警

---

*最后更新 / Last Updated: 2026-01-20*
