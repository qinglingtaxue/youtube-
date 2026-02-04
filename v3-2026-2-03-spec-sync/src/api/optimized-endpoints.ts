/**
 * 优化的 API 端点集合
 *
 * 本文件提供与性能优化相关的所有 API 端点实现
 * 包括分页、缓存、索引等优化
 *
 * 集成方式：
 * 1. 复制这些函数到你的现有 API 路由中
 * 2. 确保使用了优化后的数据库查询
 * 3. 启用缓存管理器
 *
 * 示例（如果使用 Express）：
 * ```ts
 * import { getVideosPaginated, getVideoStats } from './api/optimized-endpoints';
 *
 * app.get('/api/videos', async (req, res) => {
 *   const data = await getVideosPaginated(req.query, db);
 *   res.json(data);
 * });
 * ```
 */

import { getCached, invalidateCache } from "../lib/cache.ts";

// ================================================================
// 类型定义
// ================================================================

export interface PaginationQuery {
  page?: string | number;
  limit?: string | number;
  keyword?: string;
  sortBy?: "views" | "published_at" | "engagement_rate";
  timeRange?: "24h" | "7d" | "30d" | "90d" | "all";
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    hasMore: boolean;
  };
}

export interface VideoStatsResponse {
  total_videos: number;
  avg_views: number;
  median_views: number;
  min_views: number;
  max_views: number;
  total_views: number;
  engagement_distribution: {
    high: number; // > 5%
    medium: number; // 2-5%
    low: number; // < 2%
  };
}

export interface QuadrantSummaryResponse {
  total_videos: number;
  star: { count: number; percentage: number; avg_views: number };
  niche: { count: number; percentage: number; avg_views: number };
  viral: { count: number; percentage: number; avg_views: number };
  dog: { count: number; percentage: number; avg_views: number };
}

// ================================================================
// Quick Wins：立即可用的优化（不需要改数据库）
// ================================================================

/**
 * Quick Win 1：添加时间范围限制
 * 问题：无限制查询导致全表扫描
 * 解决：总是限制查询范围
 */
function getTimeRangeFilter(timeRange?: string) {
  const now = new Date();
  const rangeMap: Record<string, Date> = {
    "24h": new Date(now.getTime() - 24 * 60 * 60 * 1000),
    "7d": new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
    "30d": new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
    "90d": new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000),
  };

  return rangeMap[timeRange || "30d"] || new Date(0); // 默认 30 天
}

/**
 * Quick Win 2：参数验证和范围限制
 * 问题：前端要求加载 100万 条数据
 * 解决：强制限制最大返回数量
 */
function validatePaginationParams(query: PaginationQuery) {
  let page = parseInt(String(query.page || "1"), 10);
  let limit = parseInt(String(query.limit || "50"), 10);

  // 防止无效参数
  if (page < 1) page = 1;
  if (limit < 1) limit = 1;
  if (limit > 100) limit = 100; // ✅ 最多返回 100 条

  // 防止深分页（offset > 100000）
  const maxPage = Math.ceil(100000 / limit);
  if (page > maxPage) page = maxPage;

  return { page, limit };
}

// ================================================================
// 优化 1：视频列表分页查询
// ================================================================

/**
 * 获取视频列表（分页）
 *
 * API：GET /api/videos?page=1&limit=50&keyword=养生&sortBy=views&timeRange=30d
 *
 * 优化点：
 * 1. 分页返回，不一次性加载全量
 * 2. 时间范围限制，避免扫描 90+ 天数据
 * 3. 按需选择返回字段（select），减少网络传输
 * 4. 使用数据库索引加速排序
 *
 * 预期响应时间：100-200ms（vs 原来的 10-30s）
 */
export async function getVideosPaginated(
  query: PaginationQuery,
  db: any
): Promise<PaginatedResponse<any>> {
  const { page, limit } = validatePaginationParams(query);
  const offset = (page - 1) * limit;
  const timeRangeStart = getTimeRangeFilter(query.timeRange);
  const sortBy = query.sortBy || "views";

  // 构建查询条件
  const where: any = {
    published_at: { gte: timeRangeStart },
  };

  if (query.keyword) {
    where.title = { contains: query.keyword };
  }

  // 计算总数（缓存此结果，避免重复计算）
  const cacheKey = `count:videos:${JSON.stringify(where)}`;
  const total = await getCached({
    key: cacheKey,
    ttl: 600, // 缓存 10 分钟
    fetch: async () => {
      return db.competitorVideo.count({ where });
    },
  });

  // 查询分页数据
  const items = await db.competitorVideo.findMany({
    where,
    select: {
      // ✅ 只返回必要字段（减少数据传输）
      id: true,
      youtube_id: true,
      title: true,
      views: true,
      likes: true,
      comments: true,
      channel_name: true,
      duration: true,
      published_at: true,
      // ❌ 不返回：description, ai_keyword（这些字段大且不常用）
    },
    orderBy: { [sortBy]: "desc" },
    skip: offset,
    take: limit,
  });

  return {
    items,
    pagination: {
      page,
      limit,
      total,
      pages: Math.ceil(total / limit),
      hasMore: page < Math.ceil(total / limit),
    },
  };
}

// ================================================================
// 优化 2：视频统计（预计算 + 缓存）
// ================================================================

/**
 * 获取视频统计数据
 *
 * API：GET /api/videos/stats?keyword=养生&timeRange=30d
 *
 * 优化点：
 * 1. 缓存计算结果（1 小时过期）
 * 2. 避免重复计算同一关键词的统计
 * 3. 返回聚合数据，不返回原始列表
 *
 * 预期响应时间：10-50ms（从缓存）vs 2-5s（计算）
 */
export async function getVideoStats(
  query: PaginationQuery,
  db: any
): Promise<VideoStatsResponse> {
  const timeRangeStart = getTimeRangeFilter(query.timeRange);
  const cacheKey = `stats:${query.keyword}:${query.timeRange || "30d"}`;

  return getCached({
    key: cacheKey,
    ttl: 3600, // 缓存 1 小时
    fetch: async () => {
      const where: any = { published_at: { gte: timeRangeStart } };
      if (query.keyword) {
        where.title = { contains: query.keyword };
      }

      const videos = await db.competitorVideo.findMany({
        where,
        select: {
          views: true,
          likes: true,
          comments: true,
        },
      });

      if (videos.length === 0) {
        return {
          total_videos: 0,
          avg_views: 0,
          median_views: 0,
          min_views: 0,
          max_views: 0,
          total_views: 0,
          engagement_distribution: { high: 0, medium: 0, low: 0 },
        };
      }

      // 计算统计数据
      const views = videos.map((v) => v.views).sort((a, b) => a - b);
      const totalViews = views.reduce((sum, v) => sum + v, 0);
      const avgViews = Math.round(totalViews / videos.length);
      const medianViews =
        views.length % 2 === 0
          ? (views[views.length / 2 - 1] + views[views.length / 2]) / 2
          : views[Math.floor(views.length / 2)];

      // 互动率分布
      const engagementRates = videos.map((v) => {
        const totalEngagement = (v.likes || 0) + (v.comments || 0);
        return totalEngagement / (v.views || 1);
      });

      const engagementHigh = engagementRates.filter((r) => r > 0.05).length;
      const engagementMedium = engagementRates.filter((r) => r >= 0.02 && r <= 0.05).length;
      const engagementLow = engagementRates.filter((r) => r < 0.02).length;

      return {
        total_videos: videos.length,
        avg_views: avgViews,
        median_views: Math.round(medianViews),
        min_views: views[0],
        max_views: views[views.length - 1],
        total_views: totalViews,
        engagement_distribution: {
          high: engagementHigh,
          medium: engagementMedium,
          low: engagementLow,
        },
      };
    },
  });
}

// ================================================================
// 优化 3：四象限聚合（缓存 + 只返回统计）
// ================================================================

/**
 * 获取四象限汇总数据
 *
 * API：GET /api/quadrant/summary?keyword=养生
 *
 * 优化点：
 * 1. 缓存四象限统计（不是视频列表）
 * 2. ✅ 只返回计数和百分比，不返回 video_ids
 * 3. 前端需要具体视频时，使用分页 API
 *
 * 预期响应体积：< 1KB（vs 原来的 1MB+）
 */
export async function getQuadrantSummary(
  query: PaginationQuery,
  db: any
): Promise<QuadrantSummaryResponse> {
  const timeRangeStart = getTimeRangeFilter(query.timeRange);
  const cacheKey = `quadrant:summary:${query.keyword}:${query.timeRange || "30d"}`;

  return getCached({
    key: cacheKey,
    ttl: 3600,
    fetch: async () => {
      const where: any = { published_at: { gte: timeRangeStart } };
      if (query.keyword) {
        where.title = { contains: query.keyword };
      }

      // 获取所有视频的基本数据
      const videos = await db.competitorVideo.findMany({
        where,
        select: {
          id: true,
          views: true,
          likes: true,
          comments: true,
        },
      });

      if (videos.length === 0) {
        return {
          total_videos: 0,
          star: { count: 0, percentage: 0, avg_views: 0 },
          niche: { count: 0, percentage: 0, avg_views: 0 },
          viral: { count: 0, percentage: 0, avg_views: 0 },
          dog: { count: 0, percentage: 0, avg_views: 0 },
        };
      }

      // 计算阈值
      const totalViews = videos.reduce((sum, v) => sum + v.views, 0);
      const avgViews = totalViews / videos.length;
      const avgEngagement =
        videos.reduce((sum, v) => sum + ((v.likes || 0) + (v.comments || 0)) / v.views, 0) /
        videos.length;

      // 分类视频
      const quadrants: Record<
        string,
        { count: number; totalViews: number }
      > = {
        star: { count: 0, totalViews: 0 },
        niche: { count: 0, totalViews: 0 },
        viral: { count: 0, totalViews: 0 },
        dog: { count: 0, totalViews: 0 },
      };

      for (const video of videos) {
        const engagement = ((video.likes || 0) + (video.comments || 0)) / video.views;
        const isHighViews = video.views > avgViews;
        const isHighEngagement = engagement > avgEngagement;

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

        quadrants[quadrant].count++;
        quadrants[quadrant].totalViews += video.views;
      }

      // 构建响应
      return {
        total_videos: videos.length,
        star: {
          count: quadrants.star.count,
          percentage: Math.round((quadrants.star.count / videos.length) * 100),
          avg_views: Math.round(
            quadrants.star.totalViews / Math.max(quadrants.star.count, 1)
          ),
        },
        niche: {
          count: quadrants.niche.count,
          percentage: Math.round((quadrants.niche.count / videos.length) * 100),
          avg_views: Math.round(
            quadrants.niche.totalViews / Math.max(quadrants.niche.count, 1)
          ),
        },
        viral: {
          count: quadrants.viral.count,
          percentage: Math.round((quadrants.viral.count / videos.length) * 100),
          avg_views: Math.round(
            quadrants.viral.totalViews / Math.max(quadrants.viral.count, 1)
          ),
        },
        dog: {
          count: quadrants.dog.count,
          percentage: Math.round((quadrants.dog.count / videos.length) * 100),
          avg_views: Math.round(
            quadrants.dog.totalViews / Math.max(quadrants.dog.count, 1)
          ),
        },
      };
    },
  });
}

// ================================================================
// 优化 4：时长分布（预计算 + 缓存）
// ================================================================

export interface DurationBucket {
  label: string;
  min_seconds: number;
  max_seconds: number;
  count: number;
  percentage: number;
  avg_views: number;
}

/**
 * 获取时长分布数据
 *
 * API：GET /api/duration/distribution?keyword=养生
 */
export async function getDurationDistribution(
  query: PaginationQuery,
  db: any
): Promise<DurationBucket[]> {
  const timeRangeStart = getTimeRangeFilter(query.timeRange);
  const cacheKey = `duration:${query.keyword}:${query.timeRange || "30d"}`;

  return getCached({
    key: cacheKey,
    ttl: 3600,
    fetch: async () => {
      const where: any = { published_at: { gte: timeRangeStart } };
      if (query.keyword) {
        where.title = { contains: query.keyword };
      }

      const videos = await db.competitorVideo.findMany({
        where,
        select: { duration: true, views: true },
      });

      if (videos.length === 0) return [];

      // 定义时长分桶（YouTube 标准）
      const buckets = [
        { label: "< 4 分钟", min: 0, max: 240 },
        { label: "4-20 分钟", min: 240, max: 1200 },
        { label: "> 20 分钟", min: 1200, max: Infinity },
      ];

      const result: DurationBucket[] = [];

      for (const bucket of buckets) {
        const bucketsVideos = videos.filter(
          (v) =>
            (v.duration || 0) >= bucket.min &&
            (v.duration || 0) < bucket.max
        );

        const totalViews = bucketsVideos.reduce((sum, v) => sum + v.views, 0);
        const avgViews =
          bucketsVideos.length > 0 ? Math.round(totalViews / bucketsVideos.length) : 0;

        result.push({
          label: bucket.label,
          min_seconds: bucket.min,
          max_seconds: bucket.max,
          count: bucketsVideos.length,
          percentage: Math.round((bucketsVideos.length / videos.length) * 100),
          avg_views: avgViews,
        });
      }

      return result;
    },
  });
}

// ================================================================
// 缓存失效管理
// ================================================================

/**
 * 当新数据被采集时，清除相关缓存
 * 在数据采集模块中调用此函数
 *
 * 使用示例：
 * ```ts
 * await saveNewVideos(videos, db);
 * invalidateStatsCache('养生');
 * ```
 */
export async function invalidateStatsCache(keyword?: string) {
  if (keyword) {
    // 清除特定关键词的缓存
    await invalidateCache(`stats:${keyword}:*`);
    await invalidateCache(`quadrant:summary:${keyword}:*`);
    await invalidateCache(`duration:${keyword}:*`);
    await invalidateCache(`count:videos:*title*${keyword}*`);
  } else {
    // 清除所有缓存
    await invalidateCache("stats:*");
    await invalidateCache("quadrant:*");
    await invalidateCache("duration:*");
    await invalidateCache("count:*");
  }
}

// ================================================================
// 实用工具
// ================================================================

/**
 * 批量预热缓存（应用启动时执行）
 */
export async function warmupCache(
  keywords: string[],
  db: any
): Promise<void> {
  console.log(`🔥 预热 ${keywords.length} 个关键词的缓存...`);

  for (const keyword of keywords) {
    try {
      await Promise.all([
        getVideoStats({ keyword }, db),
        getQuadrantSummary({ keyword }, db),
        getDurationDistribution({ keyword }, db),
      ]);
    } catch (error) {
      console.warn(`⚠️ 预热 "${keyword}" 缓存失败:`, error);
    }
  }

  console.log("✅ 缓存预热完成");
}
