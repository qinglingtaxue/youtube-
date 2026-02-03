# 🚀 数据迁移快速参考卡片

**v2 → v3 Neon PostgreSQL 迁移**

---

## 一键迁移命令速查

### 1️⃣ 验证 v2 数据库
```bash
bun run migration:validate-v2
```
**预期**: 显示 4,834 条竞品视频、974 个频道等

### 2️⃣ 准备 Neon 连接
```bash
# 复制环境配置
cp .env.example .env

# 编辑 .env，替换为真实的 DATABASE_URL
# DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

### 3️⃣ 创建 PostgreSQL Schema
```bash
bun run db:push
```
**预期**: 创建 32 个表

### 4️⃣ 执行数据迁移
```bash
bun run migration:execute
```
**预期**: 6,180 条记录迁移成功

### 5️⃣ 验证迁移结果
```bash
bun run migration:validate
```
**预期**: 各表数据行数匹配

### 6️⃣ 启动 v3 应用
```bash
bun run api
```
**预期**: 应用运行在 http://localhost:3000

---

## 环境变量配置

### 开发环境（SQLite）
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/youtube.db
API_ENV=development
LOG_LEVEL=DEBUG
```

### 生产环境（PostgreSQL）
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
API_ENV=production
LOG_LEVEL=WARN
```

---

## 数据迁移检查列表

| 步骤 | 命令 | 检查项 |
|-----|------|-------|
| 1 | `bun run migration:validate-v2` | v2 数据完整性 ✅ |
| 2 | 手动配置 .env | DATABASE_URL 正确 ✅ |
| 3 | `bun run db:push` | PostgreSQL Schema 创建 ✅ |
| 4 | `bun run migration:execute` | 数据迁移完成 ✅ |
| 5 | `bun run migration:validate` | 数据行数匹配 ✅ |
| 6 | `bun run api` | 应用正常启动 ✅ |

---

## SQL 快速查询

### 查看迁移数据量
```sql
psql $DATABASE_URL

-- 查看各表记录数
SELECT 'competitor_videos' as table_name, COUNT(*) FROM competitor_videos
UNION ALL SELECT 'channels', COUNT(*) FROM channels
UNION ALL SELECT 'trend_snapshots', COUNT(*) FROM trend_snapshots
UNION ALL SELECT 'analytics', COUNT(*) FROM analytics;
```

### 查看数据样本
```sql
-- 竞品视频样本
SELECT youtube_id, title, views FROM competitor_videos LIMIT 5;

-- 频道样本
SELECT channel_id, channel_name, subscriber_count FROM channels LIMIT 5;

-- 趋势数据样本
SELECT video_id, snapshot_time, views FROM trend_snapshots LIMIT 5;
```

### 验证外键关系
```sql
-- 检查孤立的趋势数据
SELECT COUNT(*) FROM trend_snapshots ts
LEFT JOIN competitor_videos cv ON ts.video_id = cv.id
WHERE cv.id IS NULL;
-- 应该返回 0
```

---

## API 测试

### 获取竞品视频
```bash
curl "http://localhost:3000/api/videos?limit=5"
```

### 获取频道列表
```bash
curl "http://localhost:3000/api/channels?limit=5"
```

### 获取四象限分析
```bash
curl "http://localhost:3000/api/analysis/quadrant"
```

### 按关键词搜索
```bash
curl "http://localhost:3000/api/videos?keyword=养生&limit=10"
```

---

## 故障排除速查

### 连接失败: "connection refused"
```bash
# 检查 DATABASE_URL 格式
echo $DATABASE_URL

# 验证 Neon 项目状态
# 访问 https://console.neon.tech/ 确认项目为 Available
```

### 表不存在: "relation does not exist"
```bash
# 重新推送 Schema
bun run db:push

# 如需强制重置（会删除所有数据）
bun run db:push --force
```

### 迁移失败: 部分记录错误
```bash
# 查看具体错误信息（在日志中找出有问题的 youtube_id）
# 通常是数据类型或约束问题

# 手动清空 PostgreSQL 并重试
bun run db:push --force
bun run migration:execute
```

### 性能缓慢
```bash
# 启用 Redis 缓存
export ENABLE_REDIS_CACHE=true

# 或在 Neon 控制台查看 Database Monitor
# https://console.neon.tech/
```

---

## 文件速查表

| 文件 | 用途 |
|-----|------|
| `.env.example` | 环境变量模板 |
| `MIGRATION_EXECUTION_GUIDE.md` | 完整迁移指南（详细步骤） |
| `MIGRATION_CHECKLIST.md` | 迁移检查清单（进度跟踪） |
| `DATA_MIGRATION_PLAN.md` | 迁移方案分析（背景和策略） |
| `scripts/validate_v2_data.ts` | v2 数据验证脚本 |
| `scripts/migrate_v2_to_v3.ts` | 数据迁移脚本 |
| `scripts/validate_migration.ts` | 迁移结果验证脚本 |

---

## 时间估计

| 任务 | 时间 |
|-----|------|
| 准备 Neon 项目 | 15 分钟 |
| 创建 PostgreSQL Schema | 5 分钟 |
| 执行数据迁移 | 10-15 分钟 |
| 数据验证 | 10 分钟 |
| 应用测试 | 15 分钟 |
| **总计** | **50-60 分钟** |

---

## 成功标志

✅ 迁移完成后您应该看到:

- ✅ `bun run api` 启动成功
- ✅ API 能查询到 4,834 条竞品视频
- ✅ API 能查询到 974 个频道
- ✅ 查询响应时间 < 200ms
- ✅ Drizzle Studio 显示所有数据
- ✅ 没有数据库错误日志

---

## 紧急回滚

如果遇到问题需要回滚到 SQLite:

```bash
# 停止当前应用
# (Ctrl+C)

# 编辑 .env
# DATABASE_TYPE=sqlite
# DATABASE_URL=sqlite:///./data/youtube.db

# 重启应用
bun run api

# 数据完好无损，v2 SQLite 未被修改
```

---

## 下一步

迁移完成后:

1. **启用监控** - 配置 Sentry 或其他监控工具
2. **设置备份** - 启用 Neon 自动备份功能
3. **持续采集** - 配置定时任务采集新视频数据
4. **性能优化** - 根据实际使用情况调整连接池和缓存
5. **文档更新** - 在 CLAUDE.md 中更新数据库配置文档

---

## 相关链接

- 📖 Neon 官方文档: https://neon.tech/docs
- 🐘 PostgreSQL 文档: https://www.postgresql.org/docs
- 🛢️ Drizzle ORM 文档: https://orm.drizzle.team
- 🚀 Fastify 文档: https://www.fastify.io

---

**最后更新**: 2026-02-03
**版本**: v1.0

💡 **提示**: 打印此卡片或保存为 PDF 便于快速参考！
