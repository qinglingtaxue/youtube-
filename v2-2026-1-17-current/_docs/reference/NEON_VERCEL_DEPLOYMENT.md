# Neon 数据库 + Vercel 部署指南

## 概述

本项目支持从本地 SQLite 迁移到 Neon PostgreSQL 云数据库，并部署到 Vercel。

## 前置条件

1. [Neon](https://neon.tech/) 账号
2. [Vercel](https://vercel.com/) 账号
3. 本地已有 SQLite 数据库 (`data/youtube_pipeline.db`)

## 步骤 1: 创建 Neon 数据库

1. 登录 [Neon Console](https://console.neon.tech/)
2. 创建新项目 (Create Project)
3. 选择区域（建议选择 `US East (N. Virginia)` 与 Vercel 一致）
4. 复制连接字符串，格式如下：
   ```
   postgresql://username:password@ep-xxx-xxx-123456.us-east-2.aws.neon.tech/dbname?sslmode=require
   ```

## 步骤 2: 配置环境变量

### 本地开发

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env`，填入 Neon 连接字符串：
   ```
   DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
   ```

### Vercel 部署

1. 在 Vercel 项目设置中，添加环境变量：
   - 变量名: `DATABASE_URL`
   - 值: Neon 连接字符串

2. 或使用 Vercel CLI：
   ```bash
   vercel env add DATABASE_URL
   ```

## 步骤 3: 迁移数据

运行迁移脚本，将本地 SQLite 数据迁移到 Neon：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量（或从 .env 加载）
export DATABASE_URL="postgresql://..."

# 运行迁移
python scripts/migrate_to_neon.py
```

迁移脚本会：
- 自动检测本地 `data/youtube_pipeline.db`
- 在 Neon 创建表结构
- 批量迁移所有数据
- 验证迁移结果

## 步骤 4: 部署到 Vercel

### 方式 1: 通过 GitHub 集成

1. 将代码推送到 GitHub
2. 在 Vercel 导入项目
3. 配置环境变量 `DATABASE_URL`
4. 点击 Deploy

### 方式 2: 通过 Vercel CLI

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录
vercel login

# 部署（首次会创建项目）
vercel

# 生产部署
vercel --prod
```

## 项目结构

```
├── api/
│   └── index.py          # Vercel 入口文件
├── src/
│   └── shared/
│       ├── database.py       # 原 SQLite 数据库（本地开发兼容）
│       └── neon_database.py  # Neon PostgreSQL ORM
├── scripts/
│   └── migrate_to_neon.py    # 数据迁移脚本
├── web/                      # 前端静态文件
├── vercel.json               # Vercel 配置
└── .env.example              # 环境变量模板
```

## 数据库模型

| 表名 | 描述 |
|------|------|
| `videos` | 视频基本信息 |
| `scripts` | 视频脚本 |
| `subtitles` | 字幕文件 |
| `thumbnails` | 封面图片 |
| `specs` | 视频规约 |
| `competitor_videos` | 竞品视频数据 |
| `analytics` | 数据分析记录 |
| `tasks` | 任务队列 |
| `research_reports` | 调研报告 |

## 本地开发

如果未设置 `DATABASE_URL`，系统会自动回退到本地 SQLite：

```bash
# 启动本地服务（使用 SQLite）
python api_server.py

# 启动本地服务（使用 Neon）
DATABASE_URL="postgresql://..." python api_server.py
```

## 注意事项

1. **WebSocket 限制**: Vercel Serverless Functions 不支持长连接 WebSocket。实时数据采集功能在 Vercel 上可能受限，建议：
   - 使用 HTTP 轮询替代 WebSocket
   - 或部署到支持 WebSocket 的平台（如 Railway, Render）

2. **冷启动**: Serverless 函数首次请求可能有 1-3 秒延迟

3. **数据库连接**: 使用 `NullPool` 避免 Serverless 环境的连接泄露

4. **大文件处理**: Vercel Lambda 有 50MB 大小限制，已在 `vercel.json` 中配置

## 故障排查

### 数据库连接失败

```bash
# 检查连接字符串格式
echo $DATABASE_URL

# 测试连接
python -c "from src.shared.neon_database import get_neon_database; db = get_neon_database(); print('Connected:', db.is_neon)"
```

### 迁移失败

```bash
# 检查 SQLite 数据库
ls -la data/*.db

# 查看详细错误
python scripts/migrate_to_neon.py 2>&1
```

### Vercel 部署失败

```bash
# 查看构建日志
vercel logs

# 本地测试构建
vercel build
```
