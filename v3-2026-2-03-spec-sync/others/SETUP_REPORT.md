# YouTube 最小化视频故事 v3 - 后端配置报告

**生成日期**: 2026-02-03
**版本**: 3.0.0
**状态**: ✅ 完成

---

## 一、数据库 Schema 生成

### 📄 生成文件

**路径**: `src/shared/schema.ts`

**特点**:
- ✅ 完整的 TypeScript 类型定义
- ✅ 基于 `.42cog/cog/cog.md` 的认知模型
- ✅ 支持 Neon PostgreSQL + SQLite 双重配置
- ✅ 包含 42 个实体模型定义

### 🔑 核心实体 (32 个)

#### 调研阶段
- `CompetitorVideo` - 竞品视频
- `Channel` - YouTube 频道
- `TrendSnapshot` - 趋势快照
- `TrendAggregate` - 趋势聚合

#### 工作流
- `Video` - 自有视频（全流程）
- `Task` - 任务管理
- `TaskState` - 任务状态

#### 分析框架
- `ContentQuadrant` - 四象限分类
- `DurationMatrix` - 时长分布
- `KeywordNetwork` - 关键词网络
- `BridgeTopic` - 桥梁话题

#### 套利分析
- `ArbitrageOpportunity` - 套利机会
- `ArbitrageReport` - 套利报告
- `CreatorProfile` - 博主画像

#### 模式分析 (42 模式)
- `PatternAnalysis` - 多维度模式
- `PatternReport` - 模式报告
- `LearningPath` - 学习路径

#### 报告
- `AnalysisReport` - 综合报告
- `MarketReport` - 市场报告
- `OpportunityReport` - 机会报告
- `DiagnoseReport` - 诊断报告

#### 可视化
- `InsightCard` - 洞察卡片
- `ReasoningChain` - 推理链
- `MonitorTask` - 监控任务
- `TrendingTracker` - 趋势追踪

#### 内容制作
- `Spec` - 视频规约
- `Script` - 脚本
- `Subtitle` - 字幕
- `Thumbnail` - 缩略图
- `Analytics` - 分析数据
- `User` - 用户账户

### 📊 枚举定义 (13 个)

| 枚举 | 用途 | 值示例 |
|------|------|--------|
| `VideoStatus` | 视频状态流转 | draft, scripting, producing, ready, published, scheduled |
| `Stage` | 工作流阶段 | research, planning, production, publishing, analytics |
| `TaskStatus` | 任务执行状态 | pending, running, completed, failed, cancelled |
| `TaskType` | 任务类型 | collect_videos, generate_script, upload_video 等 |
| `ContentStyle` | 内容风格 | tutorial, story, review, vlog, explainer |
| `QuadrantType` | 四象限类型 | star, niche, viral, dog |
| `ArbitrageType` | 套利类型 | topic, channel, duration, timing, cross_language |
| `CreatorTier` | 博主等级 | beginner, mid_tier, top_tier |
| `Privacy` | 视频可见性 | public, unlisted, private |
| `Resolution` | 视频分辨率 | 720p, 1080p, 4K |
| `ScriptStatus` | 脚本状态 | draft, reviewing, approved, archived |
| `SubtitleType` | 字幕类型 | auto, manual, translated |
| `SubtitleFormat` | 字幕格式 | srt, vtt, ass |

---

## 二、后端依赖安装

### 📦 Node.js 依赖 (package.json)

**安装状态**: ✅ 已完成
**包管理器**: Bun v1.3.4
**总包数**: 485 个

**核心依赖**:
```json
{
  "framework": "fastify@4.24.3",
  "orm": "drizzle-orm@0.30.10",
  "database": ["pg@8.18.0", "better-sqlite3@9.6.0"],
  "types": "zod@3.25.76",
  "realtime": "fastify-websocket@1.1.2",
  "logging": ["pino@8.21.0", "pino-pretty@10.3.1"],
  "visualization": ["chart.js@4.5.1", "d3@7.9.0"]
}
```

**开发工具**:
- `typescript@5.3.3` - TypeScript 编译器
- `tsx@4.7.0` - TypeScript 执行器
- `vitest@1.6.1` - 测试框架
- `eslint@8.56.0` - 代码检查
- `prettier@3.1.1` - 代码格式化

### 🐍 Python 依赖 (requirements.txt)

**安装状态**: ✅ 已完成
**虚拟环境**: `.venv/`
**Python 版本**: 3.11.4
**总包数**: 120+ 个

**核心依赖**:

| 类别 | 包 | 版本 |
|------|-----|------|
| **API** | fastapi | >= 0.109.0 |
| **服务器** | uvicorn[standard] | >= 0.27.0 |
| **ORM** | sqlalchemy | >= 2.0.0 |
| **数据库** | psycopg[binary], aiosqlite | >= 3.1.0 |
| **数据处理** | pandas, numpy, networkx | 最新 |
| **采集** | yt-dlp | >= 2025.1.0 |
| **自动化** | playwright, pyautogui | 最新 |
| **NLP** | jieba, nltk | 最新 |
| **图像** | pillow, opencv-python | 最新 |
| **安全** | pyjwt, bcrypt, cryptography | 最新 |
| **定时** | schedule, apscheduler | 最新 |

**可选依赖**:
- `openai-whisper` - 语音转文字（需单独安装）
- `sentry-sdk` - 错误追踪
- `aioredis` - Redis 缓存

---

## 三、项目配置文件

### 创建的配置文件

| 文件 | 用途 | 状态 |
|------|------|------|
| `package.json` | Node.js 项目配置 | ✅ 完成 |
| `tsconfig.json` | TypeScript 编译配置 | ✅ 完成 |
| `pyproject.toml` | Python 项目配置 | ✅ 完成 |
| `requirements.txt` | Python 依赖清单 | ✅ 完成 |
| `src/shared/schema.ts` | 数据库 Schema 定义 | ✅ 完成 |

### TypeScript 配置亮点

```json
{
  "target": "ES2022",
  "module": "ES2022",
  "strict": true,
  "paths": {
    "@/*": ["src/*"],
    "@shared/*": ["src/shared/*"],
    "@api/*": ["src/api/*"],
    "@research/*": ["src/research/*"],
    "@analysis/*": ["src/analysis/*"],
    "@pattern/*": ["src/pattern/*"]
  }
}
```

---

## 四、数据库配置

### Neon PostgreSQL (生产环境)

**配置文件**: 环境变量
**连接字符串格式**:
```
postgresql://user:password@host/dbname?sslmode=require
```

**支持特性**:
- ✅ SSL 连接
- ✅ 连接池管理
- ✅ 异步驱动 (psycopg)
- ✅ 事务管理

### SQLite (本地开发)

**数据库路径**: `./data/sqlite.db`
**配置**:
- WAL 日志模式（提升并发性能）
- 外键约束启用
- 单文件存储

---

## 五、开发环境验证

✅ **Python**: 3.11.4
✅ **Node.js**: v22.16.0
✅ **Bun**: v1.3.4

### 可用命令

#### Node.js 脚本

```bash
# 开发服务器
bun run dev

# 编译 TypeScript
bun run build

# 运行生成的代码
bun run start

# API 服务
bun run api

# CLI 工具
bun run cli

# 数据采集
bun run collect

# 套利分析
bun run analyze

# 模式分析
bun run pattern
```

#### Python 脚本

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行单元测试
pytest tests/

# 代码检查
flake8 src/

# 类型检查
mypy src/

# 代码格式化
black src/
```

---

## 六、后续步骤

### 立即可做

1. **初始化数据库**
   ```bash
   # 使用 Drizzle ORM 迁移
   bun run db:migrate

   # 推送到 PostgreSQL
   bun run db:push
   ```

2. **启动 API 服务**
   ```bash
   bun run api
   # 访问: http://localhost:3000
   ```

3. **运行测试**
   ```bash
   bun run test
   ```

### 建议实现

1. **认证模块** (`src/api/auth.ts`)
   - JWT 令牌生成和验证
   - OAuth 集成（Google、GitHub）
   - 用户会话管理

2. **数据库连接** (`src/shared/database.ts`)
   - Neon PostgreSQL 连接
   - SQLite 本地开发配置
   - 连接池管理

3. **API 路由** (`src/api/routes/`)
   - 调研 API (`research.ts`)
   - 分析 API (`analysis.ts`)
   - 模式 API (`pattern.ts`)
   - 任务 API (`task.ts`)

4. **WebSocket 实时通信** (`src/api/websocket.ts`)
   - 任务进度推送
   - 数据采集实时更新
   - 分析结果流推送

---

## 七、技术栈总结

### 后端

| 层 | 技术选型 | 特点 |
|----|---------|------|
| **框架** | Fastify + FastAPI | 高性能异步 |
| **数据库** | Neon PostgreSQL / SQLite | 云原生 + 本地开发 |
| **ORM** | Drizzle ORM (TS) + SQLAlchemy (Py) | 类型安全 |
| **认证** | JWT + OAuth | 标准方案 |
| **实时通信** | WebSocket | 任务进度推送 |
| **数据处理** | Pandas + NetworkX | 科学计算 |
| **采集** | yt-dlp + Playwright | 可靠稳定 |

### 开发工具

| 工具 | 用途 |
|-----|------|
| **TypeScript** | 类型安全的 JavaScript |
| **Drizzle Kit** | 数据库迁移和 Studio |
| **Vitest** | 单元测试 |
| **ESLint + Prettier** | 代码质量 |
| **Pytest** | Python 测试 |

---

## 八、注意事项

### 环境变量配置

创建 `.env` 文件:
```env
# 数据库
DATABASE_URL=postgresql://user:password@host/dbname

# API
API_HOST=0.0.0.0
API_PORT=3000

# JWT
JWT_SECRET=your-secret-key

# YouTube
YOUTUBE_API_KEY=your-api-key

# Neon
NEON_API_KEY=your-neon-key
```

### 依赖更新

```bash
# Node.js 依赖更新
bun update

# Python 依赖更新
source .venv/bin/activate
uv pip install --upgrade -r requirements.txt
```

### 性能优化

- 启用 SQLite WAL 日志
- 使用 PostgreSQL 连接池
- 启用 Redis 缓存（可选）
- 异步 I/O 处理长任务

---

## 九、参考文档

本配置基于以下规约文档：

- `.42cog/meta/meta.md` - 项目元信息
- `.42cog/cog/cog.md` - 认知模型 (32 个实体)
- `.42cog/real/real.md` - 现实约束
- `.42cog/spec/pm/userstory.spec.md` - 用户故事
- `.42cog/spec/pm/pr.spec.md` - 产品需求
- `.42cog/spec/dev/sys.spec.md` - 系统架构
- `.42cog/spec/dev/data.spec.md` - 数据规约

---

## 生成信息

**生成工具**: Claude Code
**生成时间**: 2026-02-03
**生成方式**: 自动化脚本 + 规约同步
**版本**: v3-2026-2-03-spec-sync

**后续维护**: 在 CLAUDE.md 中配置专有的维护任务
