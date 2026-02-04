# 快速启动指南 - YouTube 竞品分析工具

## 项目结构

```
apps/web/                              # Next.js 前端应用
├── app/
│   ├── layout.tsx                     # 根布局
│   ├── page.tsx                       # 首页 (/
│   ├── search/page.tsx                # 搜索结果页 (/search?q=...)
│   ├── videos/page.tsx                # 视频列表页 (/videos)
│   ├── channels/page.tsx              # 频道排行页 (/channels)
│   ├── trends/page.tsx                # 话题趋势页 (/trends)
│   ├── api/
│   │   └── search/route.ts            # 搜索 API
│   └── globals.css                    # 全局样式
│
├── components/
│   ├── home/
│   │   ├── SearchBox.tsx              # 搜索框
│   │   ├── SearchHistory.tsx          # 搜索历史
│   │   └── FilterPanel.tsx            # 筛选面板
│   └── ui/
│       ├── button.tsx
│       ├── input.tsx
│       └── badge.tsx
│
├── lib/
│   ├── types.ts                       # TypeScript 类型定义
│   ├── utils.ts                       # 工具函数
│   └── stores/
│       └── searchStore.ts             # Zustand 状态管理
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .env.example
```

## 安装和运行

### 1. 安装依赖

```bash
cd apps/web

# 使用 bun（推荐）
bun install

# 或使用 npm
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.local
```

编辑 `.env.local`：
```env
NEXT_PUBLIC_API_URL=http://localhost:3000
BACKEND_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
# 使用 bun
bun run dev

# 或使用 npm
npm run dev
```

访问 http://localhost:3000

## 核心功能演示

### 1. 搜索框
- 输入关键词（如："养生"、"太极"）
- 点击"搜索"或按 Enter 键
- 自动保存到搜索历史

### 2. 搜索历史
- 显示最近 10 条搜索记录
- 点击历史标签可快速重新搜索
- 支持逐条删除或"清空历史"

### 3. 筛选条件
- 时间范围：24小时、7天、30天、1年、不限
- 时长分类：全部、<4分钟、4-20分钟、>20分钟（YouTube原生）
- 频道规模：不限、小频道、中频道、大频道、超大
- 内容标签：多选支持

### 4. 搜索结果
- 自动跳转到 `/search?q=xxx` 页面
- 显示"自然语言排序说明"（如：7天内发布的视频，按播放量从高→低排序）
- 展示视频卡片列表

## 数据流

```
用户输入搜索词
    ↓
SearchBox 组件 (useSearchStore)
    ↓
将查询词保存到 localStorage (Zustand persist)
    ↓
路由跳转到 /search?q=xxx
    ↓
SearchResultsPage 发起 POST /api/search 请求
    ↓
API 路由返回 mock 数据（Phase 2 会连接真实后端）
    ↓
渲染搜索结果列表
```

## localStorage 存储

Zustand store 自动将以下数据持久化到 localStorage（`yt-search-store`）：
- `searchHistory`: 最近 10 条搜索记录
- `filters`: 当前筛选条件
- `sortConfig`: 排序配置

页面刷新后会自动恢复状态。

## 开发命令

```bash
# 开发模式（热重载）
bun run dev

# 类型检查
bun run type-check

# 代码格式化
bun run format

# Linting
bun run lint

# 构建生产版本
bun run build

# 生产模式运行
bun run start

# 单元测试（Phase 3）
bun run test

# E2E 测试（Phase 3）
bun run test:e2e
```

## 常见问题

### Q1: 为什么搜索没有返回数据？
A: Phase 1 使用 mock 数据。Phase 2 会连接真实的后端 API。

### Q2: 如何清空搜索历史？
A: 在首页 SearchHistory 组件中点击"清空历史"按钮。

### Q3: 搜索历史会永久保存吗？
A: 是的，存储在浏览器的 localStorage 中（在用户清空浏览数据前）。

### Q4: 支持暗色模式吗？
A: 已配置 Tailwind dark mode 支持，Phase 3 会添加 toggle 切换。

### Q5: 如何集成真实后端 API？
A: 编辑 `app/api/search/route.ts`，取消注释 BACKEND_API_URL 部分，删除 mock 数据。

## 下一步（Phase 2-4）

### Phase 2：数据加载
- [ ] 实现 /api/videos/trending
- [ ] 实现 /api/channels/trending
- [ ] 实现 /api/analytics/overview
- [ ] 集成 ISR + Suspense
- [ ] 搜索结果分页

### Phase 3：交互优化
- [ ] 响应式布局微调
- [ ] Dark mode toggle
- [ ] Loading 和 Error states
- [ ] 性能优化（Code splitting）

### Phase 4：认证 + 部署
- [ ] Better Auth 集成
- [ ] Vercel 部署配置
- [ ] CI/CD pipeline

## 调试技巧

### 1. 检查 localStorage
在浏览器开发者工具中：
```javascript
// 查看 Zustand store 数据
JSON.parse(localStorage.getItem('yt-search-store'))
```

### 2. 网络请求调试
- 打开 DevTools → Network
- 搜索任意词
- 查看 POST /api/search 的请求和响应

### 3. React 组件调试
```bash
# 安装 React DevTools 浏览器扩展
# 然后在 DevTools 中查看组件树和 props
```

## 性能指标目标

- **首屏加载时间**：< 2s
- **搜索响应**：< 500ms（含 mock 数据）
- **Lighthouse 分数**：> 90

## 支持的浏览器

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- 移动端浏览器（iOS Safari, Chrome Mobile）

## 疑问或问题？

查看相关文档：
- 设计方案：`.42cog/work/2026-02-04_design_首页_Next.js-Tailwind.md`
- 实现指南：`.42cog/work/2026-02-04_guide_首页实现_代码框架.md`
- 决策总结：`.42cog/work/2026-02-04_decision_首页-技术栈与设计总结.md`
