/**
 * ContentQuadrant 结构修复迁移
 *
 * 问题：原设计将所有 video_ids 存在一个数组字段中
 *      当象限有 10万 个视频时，这个字段达到 1MB+，导致：
 *      - 查询缓慢
 *      - 网络传输大
 *      - 内存占用高
 *
 * 解决方案：
 * 1. 删除 content_quadrant 表的 video_ids 数组字段
 * 2. 创建新的关联表 content_quadrant_membership
 * 3. 用外键关系代替数组存储
 *
 * 执行方式：
 * bun run db:migrate src/db/migrations/002_fix_quadrant_structure.sql
 *
 * 预期效果：
 * - ContentQuadrant 记录大小：1MB → 1KB
 * - 查询性能：加速 1000 倍
 * - 需要具体视频时：使用分页查询关联表
 */

-- ================================================================
-- 新表：ContentQuadrantMembership（关联表）
-- ================================================================

CREATE TABLE IF NOT EXISTS content_quadrant_membership (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  quadrant_id UUID NOT NULL,
  video_id UUID NOT NULL,
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- 外键关系
  CONSTRAINT fk_membership_quadrant
    FOREIGN KEY (quadrant_id)
    REFERENCES content_quadrant(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_membership_video
    FOREIGN KEY (video_id)
    REFERENCES competitor_video(id)
    ON DELETE CASCADE,

  -- 唯一约束：同一象限中每个视频只出现一次
  CONSTRAINT uk_membership_unique
    UNIQUE(quadrant_id, video_id)
);

-- 为查询优化创建索引
CREATE INDEX IF NOT EXISTS idx_cqm_quadrant_id
  ON content_quadrant_membership(quadrant_id);

CREATE INDEX IF NOT EXISTS idx_cqm_video_id
  ON content_quadrant_membership(video_id);

CREATE INDEX IF NOT EXISTS idx_cqm_added_at
  ON content_quadrant_membership(added_at DESC);

-- ================================================================
-- 可选：如果原表中有 video_ids 数据，执行数据迁移
-- ================================================================

/*
-- 如果 content_quadrant 表中有 video_ids 字段，执行这个迁移脚本：

-- 1. 临时禁用约束
ALTER TABLE content_quadrant_membership DISABLE TRIGGER ALL;

-- 2. 从原数据迁移到新表（假设 video_ids 是 UUID[] 类型）
INSERT INTO content_quadrant_membership (quadrant_id, video_id)
SELECT
  cq.id as quadrant_id,
  unnest(cq.video_ids) as video_id
FROM content_quadrant cq
WHERE cq.video_ids IS NOT NULL AND array_length(cq.video_ids, 1) > 0;

-- 3. 重新启用约束
ALTER TABLE content_quadrant_membership ENABLE TRIGGER ALL;

-- 4. 删除原字段（谨慎：备份原表后再执行）
ALTER TABLE content_quadrant DROP COLUMN IF EXISTS video_ids;

-- 5. 更新统计信息
ANALYZE content_quadrant_membership;
*/

-- ================================================================
-- 视图：快速查询四象限统计（供缓存层使用）
-- ================================================================

CREATE OR REPLACE VIEW quadrant_stats_view AS
SELECT
  cq.id,
  cq.quadrant_type,
  cq.views_threshold,
  cq.engagement_threshold,
  COUNT(DISTINCT cqm.video_id) as video_count,
  ROUND(100.0 * COUNT(DISTINCT cqm.video_id) /
    (SELECT COUNT(*) FROM competitor_video WHERE published_at > NOW() - INTERVAL '30 days')
  ) as percentage,
  ROUND(AVG(CASE WHEN cv.views > 0 THEN cv.views ELSE 0 END)) as avg_views
FROM content_quadrant cq
LEFT JOIN content_quadrant_membership cqm ON cq.id = cqm.quadrant_id
LEFT JOIN competitor_video cv ON cqm.video_id = cv.id AND cv.published_at > NOW() - INTERVAL '30 days'
GROUP BY cq.id, cq.quadrant_type, cq.views_threshold, cq.engagement_threshold;

-- ================================================================
-- 存储过程：高效更新四象限成员
-- ================================================================

CREATE OR REPLACE FUNCTION update_quadrant_membership(
  p_quadrant_id UUID,
  p_video_ids UUID[]
)
RETURNS void AS $$
BEGIN
  -- 1. 删除此象限的所有旧成员
  DELETE FROM content_quadrant_membership
  WHERE quadrant_id = p_quadrant_id;

  -- 2. 插入新成员（如果有）
  IF array_length(p_video_ids, 1) > 0 THEN
    INSERT INTO content_quadrant_membership (quadrant_id, video_id)
    SELECT p_quadrant_id, unnest(p_video_ids)
    ON CONFLICT (quadrant_id, video_id) DO NOTHING;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- 优化统计（帮助查询优化器）
-- ================================================================

ANALYZE content_quadrant_membership;
ANALYZE content_quadrant;

-- ================================================================
-- 安全提示
-- ================================================================

/*
迁移步骤：

1. 备份原表数据：
   pg_dump -t content_quadrant -h [host] [dbname] > quadrant_backup.sql

2. 在测试环境执行此脚本，验证数据完整性

3. 检查数据是否正确迁移：
   SELECT
     cq.quadrant_type,
     COUNT(DISTINCT cqm.video_id) as video_count
   FROM content_quadrant cq
   LEFT JOIN content_quadrant_membership cqm ON cq.id = cqm.quadrant_id
   GROUP BY cq.quadrant_type;

4. 如果一切正常，在生产环境执行

5. 更新应用代码中对 ContentQuadrant 的查询逻辑

6. 如需回滚，恢复备份：
   psql -h [host] [dbname] < quadrant_backup.sql
*/
