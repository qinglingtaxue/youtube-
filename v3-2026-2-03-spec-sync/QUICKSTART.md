# 🚀 快速开始指南 - v3

## 环境配置

### 1️⃣ 激活虚拟环境

```bash
# Python
source .venv/bin/activate

# 验证安装
python --version    # Python 3.11.4
bun --version      # v1.3.4
node --version     # v22+
```

### 2️⃣ 数据库连接

#### 本地开发（SQLite）
```bash
# 无需额外配置，自动使用 ./data/sqlite.db
```

#### 云端生产（Neon PostgreSQL）
```bash
# .env 文件配置
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

---

## 启动服务

### API 服务器

```bash
# Node.js (Fastify)
bun run api
# 访问: http://localhost:3000

# Python (FastAPI)
source .venv/bin/activate
python -m uvicorn src.api.server:app --reload
# 访问: http://localhost:8000
```

### CLI 工具

```bash
# 数据采集
bun run collect -- --keyword "养生" --max 1000

# 套利分析
bun run analyze

# 模式分析
bun run pattern
```

---

## 核心文件速览

| 文件 | 说明 |
|------|------|
| `src/shared/schema.ts` | 📄 数据库 Schema（32 个实体） |
| `src/api/server.ts` | 🌐 API 服务入口 |
| `src/research/data_collector.ts` | 📊 数据采集模块 |
| `src/analysis/arbitrage_analyzer.ts` | 💰 套利分析模块 |
| `src/pattern/pattern_analyzer.ts` | 🔍 模式分析模块（42 个） |
| `SETUP_REPORT.md` | 📋 详细配置报告 |

---

## 关键实体

### 调研阶段
- `CompetitorVideo` - 竞品视频数据
- `Channel` - YouTube 频道
- `TrendSnapshot` - 趋势快照

### 分析框架
- `ContentQuadrant` - 四象限分析
- `ArbitrageOpportunity` - 套利机会
- `PatternAnalysis` - 42 个模式

### 工作流
- `Video` - 自有视频（draft → published）
- `Task` - 任务管理
- `Analytics` - 复盘数据

---

## 常用命令

### Node.js

```bash
# 开发
bun run dev              # 热重载

# 构建
bun run build            # 编译 TypeScript
bun run start            # 运行生成的代码

# 测试
bun run test             # 运行单元测试

# 代码质量
bun run lint             # ESLint 检查
bun run format           # Prettier 格式化
```

### Python

```bash
# 测试
pytest tests/

# 代码质量
flake8 src/              # 代码检查
mypy src/               # 类型检查
black src/              # 代码格式化

# 数据库
python -m alembic revision --autogenerate -m "message"
python -m alembic upgrade head
```

---

## 环境变量模板

创建 `.env` 文件:

```env
# ==================== 数据库 ====================
DATABASE_TYPE=sqlite  # 或 postgresql
DATABASE_URL=sqlite:///./data/youtube.db

# PostgreSQL (Neon)
# DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# ==================== API ====================
API_HOST=0.0.0.0
API_PORT=3000
API_ENV=development  # 或 production

# ==================== 认证 ====================
JWT_SECRET=your-secret-key-here
JWT_EXPIRE_HOURS=24

# ==================== YouTube ====================
YOUTUBE_API_KEY=your-api-key
YOUTUBE_MAX_RESULTS=50

# ==================== 日志 ====================
LOG_LEVEL=INFO
LOG_FORMAT=json

# ==================== 特性开关 ====================
ENABLE_WEBSOCKET=true
ENABLE_REDIS_CACHE=false
ENABLE_SENTRY=false
```

---

## 项目结构

```
src/
├── shared/
│   ├── schema.ts      # 📄 数据库 Schema
│   ├── database.ts    # 🔌 数据库连接
│   └── logger.ts      # 📝 日志系统
├── api/
│   ├── server.ts      # 🌐 API 入口
│   ├── auth.ts        # 🔐 认证
│   └── routes/
│       ├── research.ts    # 调研 API
│       ├── analysis.ts    # 分析 API
│       └── pattern.ts     # 模式 API
├── research/          # 📊 数据采集
├── analysis/          # 💰 套利分析
├── pattern/           # 🔍 模式分析 (42个)
├── planning/          # 📝 策划模块
├── production/        # 🎬 制作模块
├── publishing/        # 📤 发布模块
└── analytics/         # 📈 复盘模块

data/
├── sqlite.db         # SQLite 数据库
├── raw/              # Layer 0 原始数据
├── warehouse/        # Layer 1-2 清洗和标签
└── insights/         # Layer 3-4 分析结果

config/
├── settings.yaml     # 主配置
└── secrets.yaml      # 敏感信息 (gitignore)
```

---

## 数据流向

```
输入关键词
    ↓
CompetitorVideo 采集
    ↓
+─────────────┬──────────────┬──────────────┐
│             │              │              │
↓             ↓              ↓              ↓
四象限    时长分布      关键词网络     套利分析
│             │              │              │
└─────────────┼──────────────┼──────────────┘
              ↓
       AnalysisReport
              ↓
       InsightCard 洞察
              ↓
         行动建议
```

---

## 调试技巧

### 查看数据库

```bash
# Drizzle Studio (可视化)
bun run db:studio

# SQL 查询
psql $DATABASE_URL
sqlite3 data/sqlite.db
```

### 查看 API 文档

```bash
# Fastify (Node.js)
# 访问: http://localhost:3000/docs

# FastAPI (Python)
# 访问: http://localhost:8000/docs
```

### 查看日志

```bash
# 开发模式（彩色日志）
LOG_LEVEL=DEBUG bun run api

# 生产模式（JSON 日志）
LOG_FORMAT=json bun run api
```

---

## 常见问题

### Q: 如何切换数据库？
```bash
# 编辑 .env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://...
```

### Q: 如何重置数据库？
```bash
# SQLite
rm data/sqlite.db

# PostgreSQL
bun run db:push --force
```

### Q: 如何添加新的依赖？
```bash
# Node.js
bun add package-name

# Python
source .venv/bin/activate
uv pip install package-name
```

### Q: 如何运行测试？
```bash
# Node.js
bun run test

# Python
pytest tests/ -v --cov=src
```

---

## 性能优化

### 启用 Redis 缓存

```env
ENABLE_REDIS_CACHE=true
REDIS_URL=redis://localhost:6379
```

### 启用 Sentry 错误追踪

```env
ENABLE_SENTRY=true
SENTRY_DSN=https://...
```

### 连接池优化

```typescript
// src/shared/database.ts
pool: {
  min: 2,
  max: 10,
}
```

---

## 生产部署

### Vercel（推荐）

```bash
# 连接 GitHub
git push origin main

# Vercel 自动部署
```

### Docker

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY . .
RUN bun install
RUN bun run build
CMD ["bun", "run", "start"]
```

---

## 相关文档

- 📄 [完整设置报告](./SETUP_REPORT.md)
- 📋 [系统架构规约](./​.42cog/spec/dev/sys.spec.md)
- 🔑 [数据库 Schema](./src/shared/schema.ts)
- 📊 [认知模型](./​.42cog/cog/cog.md)

---

**祝开发愉快！** 🎉
