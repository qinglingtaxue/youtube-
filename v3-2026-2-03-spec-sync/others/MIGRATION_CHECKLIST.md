# ✅ 数据迁移检查清单

**项目**: YouTube 最小化视频故事 v3
**迁移计划**: v2 (SQLite) → v3 (Neon PostgreSQL)
**日期**: 2026-02-03
**状态**: 🟡 准备中

---

## 📋 前置条件检查

### 环境准备
- [ ] Node.js v22+ 已安装
- [ ] Bun v1.3.4+ 已安装
- [ ] Git 已配置
- [ ] 项目依赖已安装 (`bun install` 完成)

### 账户和权限
- [ ] 拥有 Neon 账户 (https://console.neon.tech/)
- [ ] 拥有 v2 数据库访问权限
- [ ] 拥有本项目的写权限

### 数据备份
- [ ] v2 SQLite 数据库备份已保存
- [ ] 备份路径记录: `_________________`
- [ ] 备份验证成功 (能恢复)

---

## 🔍 第一阶段：数据验证

### v2 数据库检查
```bash
bun run migration:validate-v2
```

**检查项目**:
- [ ] 数据库文件存在 (./data/youtube_pipeline.db)
- [ ] 数据库大小在 8-10 MB
- [ ] 能成功连接到 SQLite
- [ ] CompetitorVideo 表: 4,834 条 ± 10%
- [ ] Channel 表: 974 条 ± 10%
- [ ] TrendSnapshot 表: 100 条 ± 10%
- [ ] Analytics 表: 100 条 ± 10%
- [ ] 多语言视频表: 172 条 ± 10%
- [ ] 数据无重复 (youtube_id 唯一)
- [ ] 时间戳格式一致

**问题发现**:
- [ ] 无问题，继续
- [ ] 有问题，记录: `_________________`

---

## 🌐 第二阶段：Neon PostgreSQL 设置

### 创建 Neon 项目
- [ ] 已登录 Neon 控制台
- [ ] 已创建新项目: `youtube-v3-prod` (或 `_________________`)
- [ ] 项目状态: Available
- [ ] PostgreSQL 版本: 15+

### 获取连接信息
- [ ] 已获取连接字符串
- [ ] 格式验证: `postgresql://user:password@host/dbname?sslmode=require`
- [ ] 连接字符串已保存到安全位置

### .env 配置
- [ ] `.env` 文件已创建 (从 `.env.example` 复制)
- [ ] `DATABASE_TYPE=postgresql`
- [ ] `DATABASE_URL=postgresql://...` (已替换实际值)
- [ ] 其他必要的环境变量已配置

### 连接测试
```bash
# 测试连接
bun run db:studio
```

- [ ] 能成功连接到 PostgreSQL
- [ ] Drizzle Studio 页面可访问

---

## 📊 第三阶段：数据库 Schema 创建

### 推送 Schema
```bash
bun run db:push
```

**检查项目**:
- [ ] Schema 推送成功
- [ ] 没有错误信息
- [ ] 能在 Drizzle Studio 看到 32 个表

### 表结构验证

在 Drizzle Studio 中验证:

**核心表**:
- [ ] `competitor_videos` 表
  - 字段数: >= 15
  - 主键: id (UUID)
  - 索引: youtube_id (UNIQUE)

- [ ] `channels` 表
  - 字段数: >= 7
  - 主键: id (UUID)
  - 索引: channel_id (UNIQUE)

- [ ] `trend_snapshots` 表
  - 字段数: >= 7
  - 主键: id (UUID)
  - 外键: video_id 指向 competitor_videos

- [ ] `analytics` 表
  - 字段数: >= 8
  - 主键: id (UUID)
  - 外键: video_id 指向 competitor_videos

**工作流表**:
- [ ] `videos` 表存在
- [ ] `tasks` 表存在
- [ ] `task_states` 表存在

**分析表**:
- [ ] `content_quadrants` 表存在
- [ ] `arbitrage_opportunities` 表存在
- [ ] `pattern_analysis` 表存在

---

## 🔄 第四阶段：数据迁移执行

### 迁移前最后检查
- [ ] v2 数据库完整备份已保存
- [ ] PostgreSQL 空数据库已准备
- [ ] 网络连接稳定
- [ ] 没有其他进程在修改 v2 数据库

### 执行迁移
```bash
bun run migration:execute
```

**预期结果**:
```
✅ CompetitorVideo: 4834 条
✅ Channel: 974 条
✅ TrendSnapshot: 100 条
✅ Analytics: 100 条
✅ 多语言视频: 172 条
总计: 6180 条记录迁移成功
```

**监控指标**:
- [ ] 迁移耗时: __________ 分钟
- [ ] 错误条数: 0
- [ ] 警告条数: __________ (可接受)

### 迁移问题处理

如果迁移失败:
- [ ] 记录完整的错误信息
- [ ] 检查 PostgreSQL 日志: `psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements LIMIT 10;"`
- [ ] 清空 PostgreSQL 数据: `bun run db:push --force`
- [ ] 重新运行迁移: `bun run migration:execute`

---

## ✅ 第五阶段：数据验证

### 数据完整性验证
```bash
bun run migration:validate
```

**检查项目**:
- [ ] CompetitorVideo 行数: >= 4,734 (95% 的 4,834)
- [ ] Channel 行数: >= 925 (95% 的 974)
- [ ] TrendSnapshot 行数: >= 95 (95% 的 100)
- [ ] Analytics 行数: >= 95 (95% 的 100)

### SQL 手动验证
```sql
psql $DATABASE_URL

-- 查看总记录数
SELECT 'competitor_videos' as table_name, COUNT(*) FROM competitor_videos
UNION ALL
SELECT 'channels', COUNT(*) FROM channels
UNION ALL
SELECT 'trend_snapshots', COUNT(*) FROM trend_snapshots
UNION ALL
SELECT 'analytics', COUNT(*) FROM analytics;

-- 查看数据样本
SELECT youtube_id, title, views FROM competitor_videos LIMIT 3;
SELECT channel_id, channel_name FROM channels LIMIT 3;
```

- [ ] 所有查询成功执行
- [ ] 返回的数据合理
- [ ] 没有重复的 youtube_id
- [ ] 时间戳正确格式化

### 外键关系验证
```sql
-- 验证 trend_snapshots 的 video_id 指向有效的 competitor_videos
SELECT COUNT(*) FROM trend_snapshots ts
LEFT JOIN competitor_videos cv ON ts.video_id = cv.id
WHERE cv.id IS NULL;
-- 应该返回 0

-- 验证 analytics 的 video_id 指向有效的 competitor_videos
SELECT COUNT(*) FROM analytics a
LEFT JOIN competitor_videos cv ON a.video_id = cv.id
WHERE cv.id IS NULL;
-- 应该返回 0
```

- [ ] 没有孤立的外键记录

---

## 🌐 第六阶段：应用测试

### 启动 v3 应用
```bash
# 使用 PostgreSQL 连接启动
export DATABASE_TYPE=postgresql
bun run api
```

**检查项目**:
- [ ] 服务器成功启动
- [ ] 日志显示 "✅ 数据库连接成功"
- [ ] API 监听在 http://localhost:3000
- [ ] WebSocket 连接正常

### API 端点测试

#### 1. 查询竞品视频
```bash
curl http://localhost:3000/api/videos?limit=5
```

**预期**:
- [ ] HTTP 200 OK
- [ ] 返回 5 条视频记录
- [ ] 字段包含: youtube_id, title, views, likes, comments
- [ ] 总记录数 ~4,834

#### 2. 查询频道
```bash
curl http://localhost:3000/api/channels?limit=5
```

**预期**:
- [ ] HTTP 200 OK
- [ ] 返回 5 条频道记录
- [ ] 字段包含: channel_id, channel_name, subscriber_count
- [ ] 总记录数 ~974

#### 3. 查询趋势数据
```bash
curl http://localhost:3000/api/trends?video_id=<youtube_id>
```

**预期**:
- [ ] HTTP 200 OK
- [ ] 返回该视频的趋势快照
- [ ] 字段包含: views, likes, comments, snapshot_time

#### 4. 分析 API
```bash
curl http://localhost:3000/api/analysis/quadrant
```

**预期**:
- [ ] HTTP 200 OK
- [ ] 返回四象限分析结果
- [ ] 各象限包含视频数据

#### 5. 性能测试
```bash
# 测试查询响应时间
time curl http://localhost:3000/api/videos?limit=100
```

**预期**:
- [ ] 响应时间 < 200ms
- [ ] 不出现超时

### 功能测试

- [ ] 搜索功能正常 (关键词搜索视频)
- [ ] 排序功能正常 (按 views、likes 排序)
- [ ] 分页功能正常 (limit/offset)
- [ ] 筛选功能正常 (按 channel_id 筛选)

### WebSocket 测试 (可选)

```javascript
// 在浏览器控制台测试
const ws = new WebSocket('ws://localhost:3000/ws');
ws.onmessage = (e) => console.log('收到:', e.data);
ws.send(JSON.stringify({ type: 'subscribe', table: 'competitor_videos' }));
```

- [ ] WebSocket 连接成功
- [ ] 能接收实时数据推送

---

## 🚀 第七阶段：上线切换

### 停止旧服务
- [ ] 停止任何旧的 SQLite 连接应用
- [ ] 确认 v2 应用已停止

### 环境切换
- [ ] `.env` 文件已配置为生产环境
- [ ] `DATABASE_TYPE=postgresql`
- [ ] `API_ENV=production`
- [ ] `LOG_LEVEL=WARN` (减少日志)
- [ ] `JWT_SECRET` 已更新为安全值

### 生产启动
```bash
export DATABASE_TYPE=postgresql
export API_ENV=production
bun run build
bun run start
```

- [ ] 应用正常启动
- [ ] 没有启动错误
- [ ] 日志显示正常

### 监控告警设置
- [ ] 启用 Sentry 错误追踪 (可选)
- [ ] 启用应用日志收集
- [ ] 配置告警通知
- [ ] 监控 PostgreSQL 连接池状态

---

## 📈 第八阶段：性能优化 (可选)

### 添加数据库索引
```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_competitor_videos_channel_id ON competitor_videos(channel_id);
CREATE INDEX idx_competitor_videos_published_at ON competitor_videos(published_at DESC);
CREATE INDEX idx_channels_subscriber_count ON channels(subscriber_count DESC);
```

- [ ] 索引已创建
- [ ] 查询性能改善验证

### 启用缓存
- [ ] Redis 已安装和运行
- [ ] `ENABLE_REDIS_CACHE=true`
- [ ] 缓存策略已配置

### 连接池优化
- [ ] 连接池参数已调整
- [ ] 并发连接数满足需求

---

## 🔄 第九阶段：回滚计划 (紧急)

如果迁移失败或出现严重问题:

### 回滚到 SQLite
```bash
# 1. 停止 v3 应用
# (ctrl+c)

# 2. 重新配置 .env
export DATABASE_TYPE=sqlite
export DATABASE_URL=sqlite:///./data/youtube.db

# 3. 启动应用
bun run api
```

- [ ] SQLite 应用成功启动
- [ ] 旧数据完好无损

### 数据库备份恢复 (PostgreSQL)
```bash
# 如需恢复 PostgreSQL
psql $DATABASE_URL < backups/youtube_v3_backup.sql
```

- [ ] 备份文件确认有效

---

## 📝 迁移记录

### 执行信息

| 项目 | 值 |
|-----|-----|
| 迁移日期 | __________________ |
| 迁移开始时间 | __________________ |
| 迁移结束时间 | __________________ |
| 总耗时 | __________________ |
| 参与人员 | __________________ |

### 数据统计

| 表名 | 预期行数 | 实际行数 | 状态 |
|------|---------|--------|------|
| CompetitorVideo | 4,834 | __________ | __ |
| Channel | 974 | __________ | __ |
| TrendSnapshot | 100 | __________ | __ |
| Analytics | 100 | __________ | __ |
| 多语言视频 | 172 | __________ | __ |

### 遇到的问题

```
1. 问题: ________________________________________________
   解决: ________________________________________________

2. 问题: ________________________________________________
   解决: ________________________________________________

3. 问题: ________________________________________________
   解决: ________________________________________________
```

### 备注

```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

## ✅ 最终确认

迁移完成标志:

- [ ] 所有检查项已完成
- [ ] 数据完整性已验证
- [ ] 应用功能正常
- [ ] 性能达到预期
- [ ] 备份已保存
- [ ] 团队已知晓
- [ ] 文档已更新

**迁移状态**: 🟢 完成 / 🟡 进行中 / 🔴 失败

**签名**: __________________ **日期**: __________________

---

## 📞 支持

- 📖 完整指南: MIGRATION_EXECUTION_GUIDE.md
- 📊 迁移方案: DATA_MIGRATION_PLAN.md
- 🐛 遇到问题: 参考 MIGRATION_EXECUTION_GUIDE.md 的故障排除章节
- 🔗 Neon 文档: https://neon.tech/docs

---

**生成时间**: 2026-02-03
**文档版本**: v1.0
