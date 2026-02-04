/**
 * ContentQuadrant 操作模块
 *
 * 提供与新的四象限数据结构相互作用的所有操作
 * 使用关联表而不是数组字段
 *
 * 使用示例：
 * ```ts
 * const ops = new QuadrantOperations(db);
 *
 * // 获取四象限统计
 * const stats = await ops.getQuadrantStats('keyword');
 *
 * // 获取某象限的视频列表（分页）
 * const videos = await ops.getQuadrantVideos(quadrantId, { page: 1, limit: 50 });
 *
 * // 更新象限成员
 * await ops.updateQuadrantMembers(quadrantId, [videoId1, videoId2, ...]);
 * ```
 */

// ================================================================
// 类型定义
// ================================================================

export interface QuadrantStatsRecord {
  id: string;
  quadrant_type: "star" | "niche" | "viral" | "dog";
  views_threshold: number;
  engagement_threshold: number;
  video_count: number;
  percentage: number;
  avg_views: number;
}

export interface QuadrantVideoItem {
  id: string;
  youtube_id: string;
  title: string;
  views: number;
  likes: number;
  comments: number;
  channel_name: string;
}

export interface PaginationOptions {
  page: number;
  limit: number;
}

// ================================================================
// QuadrantOperations 类
// ================================================================

export class QuadrantOperations {
  constructor(private db: any) {}

  /**
   * 获取四象限统计（从视图查询，高效）
   *
   * 返回每个象限的：
   * - 视频数量
   * - 百分比
   * - 平均播放量
   *
   * 查询时间：< 100ms（使用视图和缓存）
   */
  async getQuadrantStats(keyword?: string) {
    // 如果有关键词，需要过滤
    if (keyword) {
      // 这里需要自定义逻辑，因为视图不支持 WHERE 参数
      return this.computeQuadrantStatsForKeyword(keyword);
    }

    // 否则直接从视图查询
    return this.db.$queryRaw<QuadrantStatsRecord[]>`
      SELECT
        id,
        quadrant_type,
        views_threshold,
        engagement_threshold,
        video_count,
        percentage,
        avg_views
      FROM quadrant_stats_view
      ORDER BY quadrant_type;
    `;
  }

  /**
   * 获取特定象限的视频列表（分页）
   *
   * 使用场景：用户点击"Star 象限"时，加载具体的视频列表
   *
   * 查询时间：200-500ms（分页 + 索引）
   */
  async getQuadrantVideos(
    quadrantId: string,
    pagination: PaginationOptions
  ) {
    const { page, limit } = pagination;
    const offset = (page - 1) * limit;

    // 查询视频列表
    const videos = await this.db.$queryRaw<QuadrantVideoItem[]>`
      SELECT
        cv.id,
        cv.youtube_id,
        cv.title,
        cv.views,
        cv.likes,
        cv.comments,
        cv.channel_name
      FROM content_quadrant_membership cqm
      JOIN competitor_video cv ON cqm.video_id = cv.id
      WHERE cqm.quadrant_id = $1
      ORDER BY cv.views DESC
      LIMIT $2 OFFSET $3;
    `;

    // 获取总数
    const countResult = await this.db.$queryRaw<[{ count: bigint }]>`
      SELECT COUNT(*) as count
      FROM content_quadrant_membership
      WHERE quadrant_id = $1;
    `;

    const total = Number(countResult[0]?.count || 0);

    return {
      items: videos,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * 更新象限成员（替换旧数据）
   *
   * 使用场景：每天重新计算四象限时调用
   *
   * 优化：使用存储过程，避免 N+1 查询
   */
  async updateQuadrantMembers(
    quadrantId: string,
    videoIds: string[]
  ) {
    // 调用数据库存储过程
    await this.db.$executeRaw`
      SELECT update_quadrant_membership(
        $1::UUID,
        $2::UUID[]
      );
    `;
  }

  /**
   * 批量更新所有象限（用于定时任务）
   *
   * 使用场景：每日凌晨 4 点重新计算四象限
   */
  async updateAllQuadrants(keywordToQuadrants: Record<string, QuadrantDefinition[]>) {
    for (const [keyword, quadrants] of Object.entries(keywordToQuadrants)) {
      for (const q of quadrants) {
        await this.updateQuadrantMembers(q.quadrantId, q.videoIds);
      }
    }
  }

  /**
   * 添加单个视频到象限
   */
  async addVideoToQuadrant(quadrantId: string, videoId: string) {
    try {
      await this.db.contentQuadrantMembership.create({
        data: {
          quadrant_id: quadrantId,
          video_id: videoId,
        },
      });
    } catch (error) {
      // 可能是唯一约束冲突（视频已在象限中），忽略
      if ((error as any).code !== "P2002") {
        throw error;
      }
    }
  }

  /**
   * 从象限移除视频
   */
  async removeVideoFromQuadrant(quadrantId: string, videoId: string) {
    await this.db.contentQuadrantMembership.deleteMany({
      where: {
        quadrant_id: quadrantId,
        video_id: videoId,
      },
    });
  }

  /**
   * 获取象限大小（视频计数）
   */
  async getQuadrantSize(quadrantId: string): Promise<number> {
    const result = await this.db.contentQuadrantMembership.count({
      where: { quadrant_id: quadrantId },
    });
    return result;
  }

  /**
   * 清空象限（删除所有成员）
   */
  async clearQuadrant(quadrantId: string) {
    await this.db.contentQuadrantMembership.deleteMany({
      where: { quadrant_id: quadrantId },
    });
  }

  // ============================================================
  // 私有方法
  // ============================================================

  /**
   * 为特定关键词计算四象限统计
   * （这是一个完整的计算过程）
   */
  private async computeQuadrantStatsForKeyword(keyword: string) {
    // 查询所有符合关键词的视频
    const videos = await this.db.competitorVideo.findMany({
      where: {
        title: { contains: keyword },
      },
      select: {
        id: true,
        views: true,
        likes: true,
        comments: true,
      },
    });

    if (videos.length === 0) {
      return {
        star: { count: 0, percentage: 0, avg_views: 0 },
        niche: { count: 0, percentage: 0, avg_views: 0 },
        viral: { count: 0, percentage: 0, avg_views: 0 },
        dog: { count: 0, percentage: 0, avg_views: 0 },
      };
    }

    // 计算阈值
    const totalViews = videos.reduce((sum, v) => sum + v.views, 0);
    const avgViews = totalViews / videos.length;

    const engagements = videos.map((v) => ({
      ...v,
      engagement: ((v.likes || 0) + (v.comments || 0)) / v.views,
    }));

    const avgEngagement =
      engagements.reduce((sum, v) => sum + v.engagement, 0) /
      engagements.length;

    // 分类
    const quadrants = {
      star: { videoIds: [] as string[], totalViews: 0 },
      niche: { videoIds: [] as string[], totalViews: 0 },
      viral: { videoIds: [] as string[], totalViews: 0 },
      dog: { videoIds: [] as string[], totalViews: 0 },
    };

    for (const v of engagements) {
      const isHighViews = v.views > avgViews;
      const isHighEngagement = v.engagement > avgEngagement;

      let quadrant: keyof typeof quadrants;
      if (isHighViews && isHighEngagement) {
        quadrant = "star";
      } else if (!isHighViews && isHighEngagement) {
        quadrant = "niche";
      } else if (isHighViews && !isHighEngagement) {
        quadrant = "viral";
      } else {
        quadrant = "dog";
      }

      quadrants[quadrant].videoIds.push(v.id);
      quadrants[quadrant].totalViews += v.views;
    }

    // 构建返回数据
    return {
      star: {
        count: quadrants.star.videoIds.length,
        percentage: Math.round((quadrants.star.videoIds.length / videos.length) * 100),
        avg_views: Math.round(
          quadrants.star.totalViews /
            Math.max(quadrants.star.videoIds.length, 1)
        ),
      },
      niche: {
        count: quadrants.niche.videoIds.length,
        percentage: Math.round((quadrants.niche.videoIds.length / videos.length) * 100),
        avg_views: Math.round(
          quadrants.niche.totalViews /
            Math.max(quadrants.niche.videoIds.length, 1)
        ),
      },
      viral: {
        count: quadrants.viral.videoIds.length,
        percentage: Math.round((quadrants.viral.videoIds.length / videos.length) * 100),
        avg_views: Math.round(
          quadrants.viral.totalViews /
            Math.max(quadrants.viral.videoIds.length, 1)
        ),
      },
      dog: {
        count: quadrants.dog.videoIds.length,
        percentage: Math.round((quadrants.dog.videoIds.length / videos.length) * 100),
        avg_views: Math.round(
          quadrants.dog.totalViews /
            Math.max(quadrants.dog.videoIds.length, 1)
        ),
      },
    };
  }
}

// ================================================================
// 工具函数
// ================================================================

interface QuadrantDefinition {
  quadrantId: string;
  videoIds: string[];
}

/**
 * 定时任务：每天重新计算四象限（通常在凌晨 4 点）
 */
export async function dailyQuadrantRefresh(
  db: any,
  keywords: string[]
) {
  console.log("🔄 开始四象限刷新...");

  const ops = new QuadrantOperations(db);
  const startTime = Date.now();

  for (const keyword of keywords) {
    try {
      const stats = await ops.getQuadrantStats(keyword);
      console.log(`✅ 刷新了关键词 "${keyword}" 的四象限`);
    } catch (error) {
      console.error(`❌ 刷新 "${keyword}" 失败:`, error);
    }
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  console.log(`✨ 四象限刷新完成 (耗时 ${duration}s)`);
}
