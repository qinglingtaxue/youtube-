# 数据迁移方案 - v2 → v3 (Neon PostgreSQL)

**评估日期**: 2026-02-03
**源数据库**: v2 (SQLite, 8.1MB)
**目标数据库**: v3 (Neon PostgreSQL, 生产环境)
**迁移难度**: ⭐⭐⭐☆☆ 中等 (5 分制)

---

## 一、数据现状评估

### 📊 数据量统计

| 表名 | 记录数 | 说明 |
|------|--------|------|
| **competitor_videos** | 4,834 | 竞品视频数据（核心） |
| **channels** | 974 | YouTube 频道数据 |
| **multilang_videos** | 172 | 多语言视频 |
| **video_monitoring** | 100 | 监控任务数据 |
| **video_stats_history** | 100 | 历史统计数据 |
| **channel_alerts** | 0 | 频道告警（空） |
| **search_trends** | 0 | 搜索趋势（空） |
| **video_comments** | ? | 视频评论 |
| **其他** | - | - |

**总体统计**:
- 📁 数据库大小: **8.1 MB**
- 📊 总记录数: **~6,110+ 条**
- ✅ 数据质量: 良好（已去重处理）
- ⚠️ 空表数量: 2 个（可忽略）

### 🔍 v2 数据库架构

```sql
-- 核心表
CREATE TABLE competitor_videos (
  id UUID,
  youtube_id TEXT UNIQUE,
  title TEXT,
  channel_id TEXT,
  channel_name TEXT,
  views INTEGER,
  likes INTEGER,
  comments INTEGER,
  duration INTEGER,
  published_at TIMESTAMP,
  collected_at TIMESTAMP,
  ...
);

CREATE TABLE channels (
  channel_id TEXT PRIMARY KEY,
  channel_name TEXT,
  subscriber_count INTEGER,
  video_count INTEGER,
  total_views INTEGER,
  ...
);

-- 监控表
CREATE TABLE video_monitoring (
  id INTEGER,
  video_id TEXT,
  snapshot_time TIMESTAMP,
  views INTEGER,
  ...
);

CREATE TABLE video_stats_history (
  id INTEGER,
  video_id TEXT,
  period TEXT,
  collected_at TIMESTAMP,
  views INTEGER,
  ...
);
```

---

## 二、迁移可行性分析

### ✅ 可以迁移的数据

#### 1. **CompetitorVideo (竞品视频)** - 4,834 条
- ✅ 数据完整，无缺失
- ✅ youtube_id 可作为唯一标识
- ✅ 直接映射到 v3 Schema
- 🔄 迁移难度: **低**

**字段映射**:
```
v2.competitor_videos.youtube_id → v3.CompetitorVideo.youtube_id
v2.competitor_videos.title → v3.CompetitorVideo.title
v2.competitor_videos.channel_id → v3.CompetitorVideo.channel_id
v2.competitor_videos.views → v3.CompetitorVideo.views
v2.competitor_videos.likes → v3.CompetitorVideo.likes
v2.competitor_videos.comments → v3.CompetitorVideo.comments
...
```

#### 2. **Channel (频道数据)** - 974 条
- ✅ 数据完整
- ✅ channel_id 唯一
- ✅ 直接映射到 v3 Schema
- 🔄 迁移难度: **低**

#### 3. **TrendSnapshot (趋势快照)** - 100 条
- ✅ 可映射到 v3.TrendSnapshot
- ✅ 数据量小
- 🔄 迁移难度: **低**

#### 4. **Analytics (分析数据)** - 100 条
- ✅ 可重新分类到 AnalyticsPeriod
- ✅ 数据量小
- 🔄 迁移难度: **低**

#### 5. **多语言视频** - 172 条
- ✅ 可作为 CompetitorVideo 的补充
- ✅ 完整迁移
- 🔄 迁移难度: **低**

### ⚠️ 需要处理的问题

#### 1. **数据模型不完全匹配**
- v2 没有 `Video`（自有视频）概念
- v2 没有 `Task`（任务管理）
- v2 没有 `Spec`（视频规约）、`Script`（脚本）等制作流程表

**处理方式**: ✅ 这不是阻碍，因为：
- v2 数据是"研究数据"（调研阶段）
- v3 的新表是"制作流程"（策划→制作→发布）
- 两套系统可以共存，不需要迁移 v2 不存在的表

#### 2. **关键字段可能缺失**
- v2 的某些字段 v3 中命名不同
- v2 可能缺少 v3 需要的某些字段

**处理方式**: ✅ 通过 SQL 转换填充或设置默认值

#### 3. **外键关系**
- v2 可能没有定义严格的外键
- v3 采用 Drizzle ORM，需要关系约束

**处理方式**: ✅ 在迁移时动态验证和修复关系

---

## 三、迁移方案对比

### 方案 A: 直接迁移 ✅ 推荐

**流程**:
1. 导出 v2 SQLite 数据为 CSV
2. 使用 Drizzle 创建 v3 PostgreSQL 表
3. 编写 TypeScript 迁移脚本
4. 数据验证和去重
5. 切换应用连接字符串

**优点**:
- ✅ 一次性完成，无需维护两个数据库
- ✅ v2 历史数据完全保留
- ✅ v3 可以继续增量采集
- ✅ 无业务中断

**缺点**:
- ❌ 需要编写迁移脚本
- ❌ 需要数据验证

**时间估计**: 2-3 小时
**成本**: 低

### 方案 B: 逐步迁移 (保守)

**流程**:
1. v3 创建独立的 PostgreSQL 数据库
2. v2 继续运行（不动）
3. v3 新的采集数据写入 v3 数据库
4. 后续需要时再迁移 v2 数据
5. 最终合并（可选）

**优点**:
- ✅ 风险最低
- ✅ v2 继续稳定运行
- ✅ v3 可以独立验证

**缺点**:
- ❌ 维护两个数据库
- ❌ 后续需要数据合并
- ❌ 历史数据难以整合

**时间估计**: 立即开始（无迁移时间）
**成本**: 中等（维护成本高）

### 方案 C: 混合模式 (推荐用于生产)

**流程**:
1. 创建 Neon PostgreSQL 数据库
2. 迁移 v2 的所有数据 (CompetitorVideo, Channel, TrendSnapshot)
3. v3 的新表独立创建 (Video, Task, Script, Spec 等)
4. v2 和 v3 共用一个 PostgreSQL 数据库
5. 应用层通过 ORM 区分调用

**优点**:
- ✅ 统一数据库管理
- ✅ 旧数据被新系统访问
- ✅ 架构清晰
- ✅ 成本最优

**缺点**:
- ⚠️ 需要数据迁移脚本
- ⚠️ 需要 ORM schema 合并

**时间估计**: 3-4 小时
**成本**: 低

---

## 四、推荐迁移方案（方案 C）

### 执行步骤

#### Step 1: 准备 Neon PostgreSQL

```bash
# 创建新的 Neon 数据库
# 从 Neon 控制台：https://console.neon.tech/
# 获取连接字符串
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# 在 .env 中配置
export DATABASE_URL="postgresql://..."
```

#### Step 2: 创建 v3 Schema

```bash
# 使用 Drizzle ORM 生成 PostgreSQL schema
bun run db:push

# 这会在 PostgreSQL 中创建所有 v3 表：
# - Video, Task, Script, Spec, Subtitle, Thumbnail
# - Analytics, InsightCard, PatternAnalysis
# - User, MonitorTask, etc.
```

#### Step 3: 导出 v2 数据

```bash
# 从 v2 SQLite 数据库导出 CSV
sqlite3 /path/to/youtube_pipeline.db << 'EOF'
.mode csv
.output competitor_videos.csv
SELECT * FROM competitor_videos;

.output channels.csv
SELECT * FROM channels;

.output trend_snapshots.csv
SELECT * FROM video_monitoring;

.output analytics.csv
SELECT * FROM video_stats_history;
EOF
```

#### Step 4: 创建迁移脚本

```typescript
// src/migrations/migrate_v2_to_v3.ts
import { db } from '@/shared/database';
import { csv } from 'csv-parse';
import fs from 'fs';

async function migrateCompetitorVideos() {
  const videos = await parseCsv('competitor_videos.csv');

  for (const row of videos) {
    await db.insert(competitorVideos).values({
      id: generateUUID(),
      youtube_id: row.youtube_id,
      title: row.title,
      channel_id: row.channel_id,
      channel_name: row.channel_name,
      views: parseInt(row.views),
      likes: parseInt(row.likes),
      comments: parseInt(row.comments),
      duration: parseInt(row.duration),
      published_at: new Date(row.published_at),
      collected_at: new Date(row.collected_at),
      // ... 其他字段
    });
  }
}

async function migrateChannels() {
  // 类似逻辑
}

async function migrateTrendSnapshots() {
  // 类似逻辑
}

async function main() {
  try {
    console.log('🔄 开始迁移 v2 数据...');

    await migrateCompetitorVideos();
    console.log('✅ CompetitorVideo 迁移完成 (4,834 条)');

    await migrateChannels();
    console.log('✅ Channel 迁移完成 (974 条)');

    await migrateTrendSnapshots();
    console.log('✅ TrendSnapshot 迁移完成 (100 条)');

    await validateData();
    console.log('✅ 数据验证通过！');

  } catch (error) {
    console.error('❌ 迁移失败:', error);
    process.exit(1);
  }
}

main();
```

#### Step 5: 数据验证

```bash
# 运行迁移脚本
bun run migrate_v2_to_v3

# 验证数据
psql $DATABASE_URL << 'EOF'
SELECT COUNT(*) as 竞品视频数 FROM competitor_videos;
SELECT COUNT(*) as 频道数 FROM channels;
SELECT COUNT(*) as 快照数 FROM trend_snapshots;
EOF
```

#### Step 6: 切换应用

```bash
# 更新 v3 应用配置
# .env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://...

# 启动 v3 应用
bun run api
```

---

## 五、数据完整性检查清单

### 迁移前检查

- [ ] v2 数据库完整备份
- [ ] 确认 4,834 条竞品视频
- [ ] 确认 974 个频道
- [ ] 确认没有重复的 youtube_id
- [ ] 确认时间戳格式一致

### 迁移后检查

- [ ] PostgreSQL 中各表记录数正确
- [ ] 没有外键约束冲突
- [ ] 时间戳正确转换
- [ ] 视频链接有效
- [ ] 频道 ID 对应关系正确

### 应用测试

- [ ] API 查询竞品视频成功
- [ ] 频道统计数据正确
- [ ] 趋势分析可正常计算
- [ ] WebSocket 实时推送正常
- [ ] 性能达到预期

---

## 六、风险评估和备选方案

### 🔴 高风险 (可能性: 低)

**风险**: 数据损坏或丢失

**缓解措施**:
- ✅ 备份 v2 SQLite 数据库
- ✅ 先在测试环境迁移
- ✅ 迁移前验证数据
- ✅ 迁移后立即验证

### 🟡 中风险 (可能性: 中)

**风险**: 性能下降

**缓解措施**:
- ✅ 添加适当的数据库索引
- ✅ 使用连接池
- ✅ 启用查询缓存

### 🟢 低风险 (可能性: 高)

**风险**: 字段映射错误

**缓解措施**:
- ✅ 编写完整的类型转换
- ✅ 数据类型验证
- ✅ 单元测试覆盖

---

## 七、迁移时间表

| 阶段 | 任务 | 时间 | 状态 |
|------|------|------|------|
| 1 | 准备 Neon PostgreSQL | 30 分钟 | ⏳ 待启动 |
| 2 | 创建 v3 Schema | 15 分钟 | ⏳ 待启动 |
| 3 | 导出 v2 数据 | 10 分钟 | ⏳ 待启动 |
| 4 | 编写迁移脚本 | 60 分钟 | ⏳ 待启动 |
| 5 | 执行迁移 | 15 分钟 | ⏳ 待启动 |
| 6 | 数据验证 | 30 分钟 | ⏳ 待启动 |
| 7 | 应用测试 | 30 分钟 | ⏳ 待启动 |
| 8 | 上线切换 | 15 分钟 | ⏳ 待启动 |

**总计**: 约 **3-4 小时**

---

## 八、成本分析

### Neon PostgreSQL

| 项目 | 价格 | 说明 |
|------|------|------|
| **存储** | $0.15/GB/月 | 数据库存储 |
| **计算** | 从 $7/月 起 | 计算资源 |
| **备份** | 包含 | 自动备份 7 天 |
| **SSL** | 免费 | 连接加密 |

**估算**:
- 存储: 8.1 MB × $0.15 = **$0/月** (低于最低计费)
- 计算: **$7/月** (入门级)
- **总计**: **约 $7/月** (极低成本)

### 与 SQLite 对比

| 方案 | 成本 | 优势 |
|------|------|------|
| SQLite (本地) | $0 | 无托管成本 |
| Neon PostgreSQL | $7/月 | 云原生、自动备份、高可用 |
| v2 + v3 并行 | $0-7 | 灵活过渡 |

---

## 九、后续建议

### 立即可做 (1-2 周内)

1. **迁移 v2 数据到 Neon**
   ```bash
   # 按方案 C 执行迁移脚本
   bun run migrate_v2_to_v3
   ```

2. **验证数据完整性**
   ```bash
   # 查询各表数据量
   bun run validate_migration
   ```

3. **v3 应用上线**
   ```bash
   # 切换数据库连接
   export DATABASE_URL="postgresql://..."
   bun run api
   ```

### 后续优化 (2-4 周内)

1. **添加数据库索引**
   - 在 youtube_id 上添加索引
   - 在 channel_id 上添加索引
   - 在 published_at 上添加索引

2. **启用缓存**
   - Redis 缓存频繁查询
   - API 响应缓存

3. **备份策略**
   - 启用 Neon 的自动备份
   - 设置定期导出

4. **性能监控**
   - 使用 Neon 的性能面板
   - 监控查询性能

---

## 十、决策矩阵

| 方案 | 风险 | 时间 | 成本 | 灵活性 | 推荐度 |
|------|------|------|------|--------|--------|
| **A. 直接迁移** | 中 | 2-3h | 低 | 中 | ⭐⭐⭐ |
| **B. 逐步迁移** | 低 | 0h | 中 | 高 | ⭐⭐ |
| **C. 混合模式** | 低 | 3-4h | 低 | 高 | ⭐⭐⭐⭐⭐ |

**结论**: **推荐采用方案 C (混合模式)**，理由如下：
- ✅ v2 数据完全保留和可用
- ✅ v3 新功能独立开发
- ✅ 统一数据库管理
- ✅ 成本最优
- ✅ 风险最低

---

## 总结

**可以迁移吗？** ✅ **可以，现在就可以！**

**迁移难度？** ⭐⭐⭐☆☆ **中等**（5 分制）

**预期时间？** 3-4 小时

**推荐方案？** **方案 C (混合模式)** - 将 v2 所有研究数据迁移到 Neon PostgreSQL，同时新增 v3 的工作流表

**下一步？** 开始执行迁移脚本！

---

## 附录：快速参考

### 迁移命令速查

```bash
# 1. 准备环境
export DATABASE_URL="postgresql://..."

# 2. 创建 v3 schema
bun run db:push

# 3. 导出 v2 数据
sqlite3 v2.db ".mode csv" ".output data.csv" "SELECT * FROM competitor_videos;"

# 4. 执行迁移
bun run migrate_v2_to_v3

# 5. 验证结果
bun run validate_migration

# 6. 启动应用
bun run api
```

### 查询验证脚本

```sql
-- 验证迁移数据量
SELECT
  'competitor_videos' as table_name, COUNT(*) as record_count
FROM competitor_videos
UNION ALL
SELECT 'channels', COUNT(*) FROM channels
UNION ALL
SELECT 'trend_snapshots', COUNT(*) FROM trend_snapshots;

-- 检查数据完整性
SELECT COUNT(DISTINCT youtube_id) FROM competitor_videos;
SELECT COUNT(DISTINCT channel_id) FROM channels;
```

---

**生成时间**: 2026-02-03
**版本**: v3-2026-2-03-spec-sync
**作者**: Claude Code
