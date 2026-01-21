# TD-04: RPA 固化脚本矩阵架构 / RPA Script Matrix Architecture

> 基于浏览器自动化的多维度并行数据采集架构
> Browser automation-based multi-dimensional parallel data collection architecture

---

## 决策概要 / Decision Summary

| 属性 / Attribute | 值 / Value |
|------------------|------------|
| 决策编号 / ID | TD-04 |
| 决策类型 / Type | 系统架构 / System Architecture |
| 决策日期 / Date | 2026-01-18 |
| 来源对话 / Source | 5909f148 |
| 状态 / Status | 已执行 / Implemented |

---

## 架构结构 / Architecture Structure

```
rpa-matrix/
├── scheduler/              # 任务调度器 / Task Scheduler
│   ├── queue.ts            # 任务队列管理
│   ├── priority.ts         # 优先级调度
│   └── retry.ts            # 重试策略
├── executor/               # RPA 执行器 / RPA Executor
│   ├── browser.ts          # 浏览器实例管理
│   ├── page.ts             # 页面操作封装
│   └── extractor.ts        # 数据提取器
├── matrix/                 # 矩阵配置 / Matrix Config
│   ├── keywords.json       # 关键词维度
│   ├── timeRange.json      # 时间维度
│   └── sortBy.json         # 排序维度
├── storage/                # 数据存储 / Data Storage
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后数据
└── config.yaml             # 全局配置
```

---

## 核心组件索引 / Core Component Index

| # | 组件 / Component | 中文说明 | English Description | 技术 / Tech |
|---|------------------|---------|---------------------|-------------|
| 1 | Task Scheduler | 任务调度器，管理采集任务队列 | Manages collection task queue | Node.js |
| 2 | RPA Executor | RPA 执行器，浏览器自动化操作 | Browser automation operations | Playwright |
| 3 | Data Extractor | 数据提取器，解析页面数据 | Parses page data | Cheerio |
| 4 | Matrix Config | 矩阵配置，定义采集维度 | Defines collection dimensions | JSON/YAML |
| 5 | Data Storage | 数据存储，持久化采集结果 | Persists collection results | JSON/SQLite |

---

## 架构详解 / Architecture Details

### 1. 矩阵采集策略 / Matrix Collection Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    矩阵调度器 / Matrix Scheduler             │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ 关键词维度     │   │ 时间维度      │   │ 排序维度      │
│ Keywords      │   │ Time Range   │   │ Sort By      │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ • 游戏        │   │ • 24小时      │   │ • 播放量      │
│ • 教程        │   │ • 7天         │   │ • 上传时间    │
│ • Vlog        │   │ • 30天        │   │ • 相关度      │
│ • ...         │   │ • 90天        │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │ 任务总数 = K × T × S    │
              │ 示例: 10 × 4 × 3 = 120  │
              └─────────────────────────┘
```

**维度配置 / Dimension Config:**

| 维度 / Dimension | 选项数 / Options | 示例 / Example |
|------------------|-----------------|----------------|
| 关键词 / Keywords | 10+ | 游戏, 教程, Vlog, 科技... |
| 时间 / Time Range | 4 | 24h, 7d, 30d, 90d |
| 排序 / Sort By | 3 | views, date, relevance |

---

### 2. RPA 执行器 / RPA Executor

| 文件 / File | 中文说明 | English Description |
|-------------|---------|---------------------|
| `browser.ts` | 浏览器实例池管理，支持多实例并行 | Browser instance pool, supports parallel |
| `page.ts` | 页面导航、等待、滚动操作封装 | Page navigation, wait, scroll operations |
| `extractor.ts` | DOM 选择器、数据解析、字段映射 | DOM selectors, parsing, field mapping |

**核心代码 / Key Code:**

```typescript
// executor/browser.ts
import { chromium, Browser, Page } from 'playwright'

class BrowserPool {
  private browsers: Browser[] = []
  private maxInstances = 3

  async acquire(): Promise<Page> {
    if (this.browsers.length < this.maxInstances) {
      const browser = await chromium.launch({ headless: true })
      this.browsers.push(browser)
    }
    const browser = this.browsers[this.browsers.length - 1]
    return browser.newPage()
  }

  async release(page: Page): Promise<void> {
    await page.close()
  }
}
```

```typescript
// executor/extractor.ts
interface VideoData {
  id: string
  title: string
  channel: string
  views: number
  duration: string
  publishedAt: string
  thumbnail: string
}

async function extractVideos(page: Page): Promise<VideoData[]> {
  await page.waitForSelector('ytd-video-renderer')

  return page.$$eval('ytd-video-renderer', (nodes) =>
    nodes.map((node) => ({
      id: node.querySelector('a#thumbnail')?.href?.split('v=')[1] || '',
      title: node.querySelector('#video-title')?.textContent?.trim() || '',
      channel: node.querySelector('#channel-name a')?.textContent?.trim() || '',
      views: parseViews(node.querySelector('#metadata-line span')?.textContent),
      duration: node.querySelector('ytd-thumbnail-overlay-time-status-renderer')?.textContent?.trim() || '',
      publishedAt: node.querySelectorAll('#metadata-line span')[1]?.textContent || '',
      thumbnail: node.querySelector('img')?.src || '',
    }))
  )
}
```

---

### 3. 任务调度器 / Task Scheduler

```typescript
// scheduler/queue.ts
interface Task {
  id: string
  keyword: string
  timeRange: string
  sortBy: string
  priority: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  retryCount: number
}

class TaskQueue {
  private tasks: Task[] = []
  private maxConcurrent = 3
  private running = 0

  async add(task: Omit<Task, 'status' | 'retryCount'>): Promise<void> {
    this.tasks.push({
      ...task,
      status: 'pending',
      retryCount: 0,
    })
    this.tasks.sort((a, b) => b.priority - a.priority)
  }

  async next(): Promise<Task | null> {
    if (this.running >= this.maxConcurrent) return null
    const task = this.tasks.find(t => t.status === 'pending')
    if (task) {
      task.status = 'running'
      this.running++
    }
    return task || null
  }

  async complete(taskId: string): Promise<void> {
    const task = this.tasks.find(t => t.id === taskId)
    if (task) {
      task.status = 'completed'
      this.running--
    }
  }
}
```

---

### 4. 数据流 / Data Flow

```
输入 / Input                    处理 / Process                   输出 / Output
─────────────────────────────────────────────────────────────────────────────────

keywords.json  ───┐
                  │
timeRange.json ───┼──▶ [矩阵生成] ──▶ [任务队列] ──▶ [RPA执行] ──▶ raw/*.json
                  │                                      │
sortBy.json   ───┘                                      │
                                                        ▼
                                              [数据清洗/去重/合并]
                                                        │
                                                        ▼
                                              processed/videos.json
```

---

## 技术选型对比 / Technology Comparison

| 方案 / Option | 优点 / Pros | 缺点 / Cons | 选择 / Choice |
|---------------|-------------|-------------|---------------|
| YouTube Data API | 官方支持、稳定 | 配额限制、成本高 | ✗ |
| 第三方数据服务 | 开箱即用 | 成本极高、依赖第三方 | ✗ |
| **RPA 自动化** | **灵活、无配额限制** | **维护成本、反爬风险** | **✓** |

---

## 配置示例 / Configuration Example

```yaml
# config.yaml
rpa:
  browser:
    headless: true
    timeout: 30000
    userAgent: "Mozilla/5.0 ..."

  scheduler:
    maxConcurrent: 3
    retryLimit: 3
    retryDelay: 5000

  matrix:
    keywords:
      - group: core
        words: [游戏, 教程, Vlog]
        priority: high
      - group: extended
        words: [科技, 美食, 旅行]
        priority: medium

    timeRange: [24h, 7d, 30d, 90d]
    sortBy: [views, date, relevance]

  storage:
    type: json  # json | sqlite
    path: ./data
    compress: true
```

---

## 快速导航 / Quick Navigation

### 想了解任务调度？ / Want task scheduling?
→ 查看 `scheduler/` 目录

### 想了解数据提取？ / Want data extraction?
→ 查看 `executor/extractor.ts`

### 想修改采集维度？ / Want to modify dimensions?
→ 编辑 `matrix/*.json` 配置文件

### 想了解下游处理？ / Want downstream processing?
→ 阅读 [TD-05: Pipeline 规约机制](./05-设计pipeline规约生成机制.md)

---

## 注意事项 / Notes

1. **反爬策略 / Anti-Bot**：控制请求频率，使用随机延迟
2. **选择器维护 / Selectors**：YouTube 页面更新时需及时调整
3. **错误处理 / Error Handling**：网络超时、元素未找到等异常
4. **资源管理 / Resources**：及时关闭浏览器实例避免内存泄漏
5. **数据验证 / Validation**：提取数据后验证完整性
6. **日志记录 / Logging**：记录采集过程便于问题排查

---

## 相关决策 / Related Decisions

| 决策 / Decision | 关系 / Relation |
|-----------------|-----------------|
| [TD-05](./05-设计pipeline规约生成机制.md) | 下游：数据处理流程 |
| [TD-13](./13-确定采集关键词逻辑与近期视频筛选规则.md) | 细化：采集逻辑 |
| [TD-14](./14-增加进度预估与网络速度显示功能.md) | 增强：进度监控 |
| [TD-15](./15-采用YouTube原生搜索过滤机制.md) | 优化：过滤机制 |

---

*最后更新 / Last Updated: 2026-01-20*
