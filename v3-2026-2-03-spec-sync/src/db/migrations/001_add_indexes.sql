/**
 * 数据库索引迁移
 * 目的：为大数据量查询优化性能
 *
 * 执行方式：
 * bun run db:migrate src/db/migrations/001_add_indexes.sql
 * 或在 Neon Dashboard 中手动执行
 *
 * 预期效果：
 * - YouTube ID 查询：O(N) → O(1)
 * - 时间范围查询：10-30s → 200-500ms
 * - 频道聚合：加速 10-100倍
 */

-- ================================================================
-- CompetitorVideo 表索引
-- ================================================================

-- 1. 主键唯一索引（用于 youtube_id 去重）
CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_youtube_id
  ON competitor_video(youtube_id);

-- 2. 发布时间索引（最常见查询：过滤时间范围）
CREATE INDEX IF NOT EXISTS idx_cv_published_at
  ON competitor_video(published_at DESC);

-- 3. 频道 ID 索引（聚合分析）
CREATE INDEX IF NOT EXISTS idx_cv_channel_id
  ON competitor_video(channel_id);

-- 4. 复合索引（标题搜索 + 时间范围）
-- 用于查询：keyword + 时间范围 时的加速
CREATE INDEX IF NOT EXISTS idx_cv_title_published
  ON competitor_video(published_at DESC, title);

-- 5. 播放量索引（排序查询）
CREATE INDEX IF NOT EXISTS idx_cv_views
  ON competitor_video(views DESC);

-- ================================================================
-- TrendAggregate 表索引
-- ================================================================

-- 1. 视频 + 周期类型复合索引（最常见查询）
-- 场景：查询某视频的周趋势
CREATE INDEX IF NOT EXISTS idx_ta_video_period
  ON trend_aggregate(video_id, period_type, period_start DESC);

-- 2. 时间范围索引（查询最近 N 天的聚合）
CREATE INDEX IF NOT EXISTS idx_ta_period_start
  ON trend_aggregate(period_start DESC);

-- ================================================================
-- TrendSnapshot 表索引（注意：此表需要定期清理）
-- ================================================================

-- 1. 部分索引：仅保留 7 天内的快照
-- 这样可以减小索引大小，加快查询
CREATE INDEX IF NOT EXISTS idx_ts_video_recent
  ON trend_snapshot(video_id, snapshot_time DESC)
  WHERE snapshot_time > CURRENT_TIMESTAMP - INTERVAL '7 days';

-- 2. 时间范围索引（用于压缩任务查询旧数据）
CREATE INDEX IF NOT EXISTS idx_ts_snapshot_time
  ON trend_snapshot(snapshot_time DESC);

-- ================================================================
-- Analytics 表索引
-- ================================================================

-- 1. 视频 + 周期复合索引
CREATE INDEX IF NOT EXISTS idx_analytics_video_period
  ON analytics(video_id, period, collected_at DESC);

-- 2. 收集时间索引
CREATE INDEX IF NOT EXISTS idx_analytics_collected_at
  ON analytics(collected_at DESC);

-- ================================================================
-- ContentQuadrant 表索引
-- ================================================================

-- 1. 象限类型索引
CREATE INDEX IF NOT EXISTS idx_cq_quadrant_type
  ON content_quadrant(quadrant_type);

-- ================================================================
-- Channel 表索引
-- ================================================================

-- 1. YouTube Channel ID 唯一索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_ch_channel_id
  ON channel(channel_id);

-- 2. 订阅数索引（排序查询）
CREATE INDEX IF NOT EXISTS idx_ch_subscriber_count
  ON channel(subscriber_count DESC);

-- ================================================================
-- 统计信息更新（帮助查询优化器）
-- ================================================================

-- 更新表统计，让数据库优化器做出更好的决策
ANALYZE competitor_video;
ANALYZE trend_aggregate;
ANALYZE trend_snapshot;
ANALYZE analytics;
ANALYZE content_quadrant;
ANALYZE channel;
