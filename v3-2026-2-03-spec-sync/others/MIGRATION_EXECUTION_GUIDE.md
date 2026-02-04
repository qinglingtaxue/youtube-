# 🚀 数据迁移执行指南 - v2 → v3 (Neon PostgreSQL)

**创建时间**: 2026-02-03
**方案**: Hybrid Mode (推荐) - 混合模式
**预计时间**: 3-4 小时

---

## 快速检查清单

### ✅ 前置条件

在开始迁移前，请确保：

- [ ] v2 数据库完整备份已保存
- [ ] Neon PostgreSQL 账户已创建（https://console.neon.tech/）
- [ ] Node.js v22+ 已安装
- [ ] Bun v1.3.4+ 已安装
- [ ] 本项目依赖已安装 (`bun install` 完成)
- [ ] .env 文件已配置

---

## 第一阶段：准备环境

### Step 1: 验证 v2 数据库

```bash
# 运行数据库验证脚本
bun run scripts/validate_v2_data.ts
```

**预期输出**:
```
✅ 数据库大小: 8.1 MB

✅ 有数据的表:
   ├─ competitor_videos: 4834 条记录
   ├─ channels: 974 条记录
   ├─ multilang_videos: 172 条记录
   ├─ video_monitoring: 100 条记录
   └─ video_stats_history: 100 条记录
```

**如果出现❌**: 检查 v2 数据库路径和文件完整性

### Step 2: 创建 Neon PostgreSQL 数据库

1. **访问 Neon 控制台**
   - 打开: https://console.neon.tech/
   - 登录账户（或创建新账户）

2. **创建新项目**
   - 点击 "New Project"
   - 输入项目名: `youtube-v3-prod` (或自定义)
   - 选择 PostgreSQL 版本: 15+
   - 选择区域: 靠近您的位置（美国东部优先）
   - 点击 "Create project"

3. **获取连接字符串**
   - 项目创建后，点击 "Connect"
   - 选择连接方式: "Connection string"
   - 复制完整的连接字符串，格式如下:
   ```
   postgresql://user:password@host/dbname?sslmode=require
   ```

4. **配置 .env 文件**
   ```bash
   cp .env.example .env
   ```

   编辑 `.env`，替换数据库连接字符串:
   ```env
   DATABASE_TYPE=postgresql
   DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
   ```

### Step 3: 验证数据库连接

```bash
# 测试 PostgreSQL 连接
bun run db:studio
```

**预期结果**: 浏览器打开 Drizzle Studio，显示空数据库

如果连接失败，检查:
- [ ] DATABASE_URL 格式正确
- [ ] 网络连接正常
- [ ] Neon 项目状态为 "Available"

---

## 第二阶段：创建数据库 Schema

### Step 4: 推送 Schema 到 PostgreSQL

```bash
# 创建所有 v3 表和索引
bun run db:push
```

**预期输出**:
```
✅ Drizzle ORM 已推送 schema
✅ 创建了以下表:
   - competitor_videos
   - channels
   - trend_snapshots
   - analytics
   - videos
   - tasks
   - ... (共 32 个实体)
```

### Step 5: 验证 Schema 创建

```bash
# 打开 Drizzle Studio 查看表结构
bun run db:studio
```

**检查清单**:
- [ ] competitor_videos 表存在（包含 youtube_id, title, views 等字段）
- [ ] channels 表存在
- [ ] trend_snapshots 表存在
- [ ] analytics 表存在
- [ ] 所有表的主键和索引正确

---

## 第三阶段：执行数据迁移

### Step 6: 备份数据

```bash
# 可选：备份当前 PostgreSQL 状态
psql $DATABASE_URL -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';"
```

### Step 7: 运行迁移脚本

```bash
# 执行完整迁移（包括所有数据表）
bun run scripts/migrate_v2_to_v3.ts
```

**预期输出**:
```
🚀 开始数据迁移: v2 (SQLite) → v3 (PostgreSQL)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 开始迁移 CompetitorVideo...
  📊 查询到 4834 条记录
  ✅ CompetitorVideo 迁移完成: 4834 条

📥 开始迁移 Channel...
  📊 查询到 974 条记录
  ✅ Channel 迁移完成: 974 条

📥 开始迁移 TrendSnapshot...
  📊 查询到 100 条记录
  ✅ TrendSnapshot 迁移完成: 100 条

📥 开始迁移 Analytics...
  📊 查询到 100 条记录
  ✅ Analytics 迁移完成: 100 条

📥 开始迁移多语言视频...
  📊 查询到 172 条记录
  ✅ 多语言视频迁移完成: 172 条

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 迁移完成！

📊 迁移统计：
  ├─ CompetitorVideo: 4834 条
  ├─ Channel: 974 条
  ├─ TrendSnapshot: 100 条
  ├─ Analytics: 100 条
  ├─ 多语言视频: 172 条
  └─ 错误: 0 条

总计: 6180 条记录迁移成功！
```

**错误处理**:
- 如果看到 ❌ 错误，检查错误日志
- 常见错误: 连接超时、外键约束失败
- 重试前先手动清空 PostgreSQL 中的数据表

---

## 第四阶段：数据验证

### Step 8: 验证迁移数据完整性

创建验证脚本 `scripts/validate_migration.ts`:

```typescript
import { db } from '@/shared/database';
import { competitorVideos, channels, trendSnapshots, analytics } from '@/shared/schema';
import { count } from 'drizzle-orm';

async function validateMigration() {
  console.log('📋 验证迁移数据...\n');

  const tables = [
    { name: 'competitor_videos', expected: 4834 },
    { name: 'channels', expected: 974 },
    { name: 'trend_snapshots', expected: 100 },
    { name: 'analytics', expected: 100 },
  ];

  for (const table of tables) {
    const result = await db
      .select({ count: count() })
      .from(table as any)
      .then((r) => r[0]);

    const actual = result.count;
    const status = actual >= table.expected * 0.95 ? '✅' : '❌';

    console.log(`${status} ${table.name}: ${actual} 条 (预期 ${table.expected})`);
  }

  console.log('\n✅ 验证完成');
}

validateMigration().catch(console.error);
```

运行验证:
```bash
bun run scripts/validate_migration.ts
```

### Step 9: 执行 SQL 查询验证

```sql
-- 连接到 PostgreSQL
psql $DATABASE_URL

-- 查询各表记录数
SELECT 'competitor_videos' as table_name, COUNT(*) as count FROM competitor_videos
UNION ALL
SELECT 'channels', COUNT(*) FROM channels
UNION ALL
SELECT 'trend_snapshots', COUNT(*) FROM trend_snapshots
UNION ALL
SELECT 'analytics', COUNT(*) FROM analytics;

-- 检查数据样本
SELECT youtube_id, title, views FROM competitor_videos LIMIT 5;
SELECT channel_id, channel_name, subscriber_count FROM channels LIMIT 5;
```

**预期结果**:
```
    table_name     | count
─────────────────────────────
 competitor_videos |  4834
 channels          |   974
 trend_snapshots   |   100
 analytics         |   100
```

---

## 第五阶段：应用测试

### Step 10: 启动 v3 应用

```bash
# 使用 PostgreSQL 启动
export DATABASE_TYPE=postgresql
bun run api
```

**预期输出**:
```
🚀 Fastify 服务器启动
📡 API 服务运行在 http://localhost:3000
✅ 数据库连接成功
```

### Step 11: 测试 API 端点

```bash
# 查询竞品视频
curl http://localhost:3000/api/videos?limit=5

# 预期返回:
{
  "data": [
    {
      "id": "uuid",
      "youtube_id": "dQw4w9WgXcQ",
      "title": "视频标题",
      "views": 1000000,
      ...
    }
  ],
  "total": 4834
}
```

```bash
# 查询频道
curl http://localhost:3000/api/channels?limit=5

# 预期返回:
{
  "data": [
    {
      "id": "uuid",
      "channel_id": "UCxxxxxx",
      "channel_name": "频道名称",
      "subscriber_count": 1000000,
      ...
    }
  ],
  "total": 974
}
```

### Step 12: 测试分析功能

```bash
# 测试竞品分析 API
curl http://localhost:3000/api/analysis/quadrant

# 预期返回包含四象限分析结果
{
  "star": [...],
  "niche": [...],
  "viral": [...],
  "dog": [...]
}
```

---

## 第六阶段：上线切换

### Step 13: 环境切换

```bash
# 1. 验证生产环境配置
cat .env | grep DATABASE

# 2. 停止本地 SQLite 开发模式
# (ctrl+c)

# 3. 启动生产环境 PostgreSQL 模式
export API_ENV=production
export LOG_LEVEL=WARN
bun run api
```

### Step 14: 监控和告警

```bash
# 1. 启用 Sentry 错误追踪
export ENABLE_SENTRY=true
export SENTRY_DSN=your-sentry-dsn

# 2. 启用 Redis 缓存（可选）
export ENABLE_REDIS_CACHE=true
export REDIS_URL=redis://localhost:6379

# 3. 监控日志
tail -f logs/app.log | grep -i error
```

---

## 故障排除

### 问题 1: 迁移失败 - "table does not exist"

**原因**: PostgreSQL schema 还未创建

**解决**:
```bash
# 重新推送 schema
bun run db:push

# 如果需要重置，使用 --force 标记
bun run db:push --force
```

### 问题 2: 迁移失败 - "connection refused"

**原因**: 无法连接到 PostgreSQL

**检查**:
```bash
# 验证 DATABASE_URL
echo $DATABASE_URL

# 测试连接
psql $DATABASE_URL -c "SELECT 1"

# 如果失败，检查:
# 1. Neon 项目状态
# 2. 网络连接
# 3. 防火墙设置
```

### 问题 3: 迁移部分失败

**原因**: 某些记录有数据问题

**解决**:
```bash
# 查看错误日志
# 错误信息会打印出具体的 youtube_id 和错误原因

# 手动修复数据后重试
bun run scripts/migrate_v2_to_v3.ts
```

### 问题 4: 性能缓慢

**原因**: 网络延迟或 Neon 配置不当

**优化**:
```bash
# 1. 启用连接池
# src/shared/database.ts 中调整 pool 参数

# 2. 添加查询缓存
export ENABLE_REDIS_CACHE=true

# 3. 添加数据库索引
# 在 src/shared/schema.ts 中添加索引定义
```

---

## 成功标志

迁移完成后，您应该能看到:

- ✅ 4,834 条竞品视频已迁移到 PostgreSQL
- ✅ 974 个频道信息已迁移
- ✅ API 能够正常查询所有数据
- ✅ 分析功能（四象限、套利分析等）正常工作
- ✅ 性能达到预期（查询响应 < 200ms）
- ✅ 没有数据损坏或丢失

---

## 后续维护

### 定期备份

```bash
# 每日备份 PostgreSQL
pg_dump $DATABASE_URL > backups/youtube_v3_$(date +%Y%m%d).sql
```

### 性能监控

```bash
# 在 Neon 控制台查看:
# 1. Database Monitor - 实时查询和性能
# 2. Query Performance - 慢查询分析
# 3. Storage - 存储使用情况
```

### 增量采集

```bash
# v3 新增数据会自动写入 PostgreSQL
# 配置定时任务持续采集新视频数据
bun run collect -- --keyword "关键词" --max 100
```

---

## 需要帮助？

- 📧 检查 Neon 文档: https://neon.tech/docs
- 🐛 遇到 bug: 查看项目 issue
- 💬 需要支持: 提交问题和日志

---

**迁移估计时间**: 3-4 小时
**建议**: 在非业务高峰期进行迁移
**风险等级**: 🟢 低 (已备份 v2 数据)

祝迁移顺利！🎉
