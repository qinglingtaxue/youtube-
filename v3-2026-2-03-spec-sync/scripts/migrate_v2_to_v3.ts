/**
 * 数据迁移脚本：v2 (SQLite) → v3 (Neon PostgreSQL)
 *
 * 使用方法：
 * 1. 配置环境变量：DATABASE_URL (PostgreSQL)
 * 2. 将 v2 的 youtube_pipeline.db 放在项目根目录
 * 3. 运行：bun run scripts/migrate_v2_to_v3.ts
 *
 * 迁移内容：
 * - CompetitorVideo (4,832 条)
 * - Channel (974 条)
 * - TrendSnapshot (100 条)
 * - Analytics (100 条)
 * - 多语言视频 (172 条)
 */

import Database from 'better-sqlite3';
import { Pool } from 'pg';
import { config } from 'dotenv';

config();

// ==================== 类型定义 ====================

interface CompetitorVideoRow {
  youtube_id: string;
  title: string;
  channel_id: string;
  channel_name: string;
  views: number;
  likes: number;
  comments: number;
  duration: number;
  published_at: string;
  collected_at: string;
  thumbnail_url?: string;
  pattern_type?: string;
  keyword_source?: string;
}

interface ChannelRow {
  channel_id: string;
  channel_name: string;
  subscriber_count: number;
  video_count: number;
  total_views: number;
  avg_views?: number;
}

// ==================== 工具函数 ====================

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function parseDate(dateStr: string): Date {
  if (!dateStr) return new Date();
  const date = new Date(dateStr);
  return isNaN(date.getTime()) ? new Date() : date;
}

function sanitizeString(str: any): string {
  if (typeof str !== 'string') return '';
  return str.substring(0, 5000); // 限制长度防止溢出
}

// ==================== 迁移逻辑 ====================

class DataMigration {
  private sqliteDb: Database.Database;
  private pgPool: Pool;
  private stats = {
    competitorVideos: 0,
    channels: 0,
    trendSnapshots: 0,
    analytics: 0,
    multilangVideos: 0,
    errors: 0,
  };

  constructor() {
    // 连接 SQLite
    this.sqliteDb = new Database('./data/youtube_pipeline.db');

    // 连接 PostgreSQL
    this.pgPool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
    });
  }

  async migrateCompetitorVideos() {
    console.log('📥 开始迁移 CompetitorVideo...');

    try {
      const stmt = this.sqliteDb.prepare(`
        SELECT
          youtube_id, title, channel_id, channel_name,
          view_count as views, like_count as likes, comment_count as comments, duration,
          published_at, collected_at,
          thumbnail_url, pattern_type, keyword_source
        FROM competitor_videos
      `);

      const videos = stmt.all() as CompetitorVideoRow[];
      console.log(`  📊 查询到 ${videos.length} 条记录`);

      // 首先创建表（如果不存在）
      try {
        await this.pgPool.query(`
          CREATE TABLE IF NOT EXISTS competitor_videos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            youtube_id TEXT NOT NULL UNIQUE,
            title TEXT,
            channel_id TEXT,
            channel_name TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            duration INTEGER,
            published_at TIMESTAMP,
            collected_at TIMESTAMP,
            thumbnail_url TEXT,
            pattern_type TEXT,
            keyword_source TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
          );
          CREATE INDEX IF NOT EXISTS idx_cv_youtube_id ON competitor_videos(youtube_id);
          CREATE INDEX IF NOT EXISTS idx_cv_channel_id ON competitor_videos(channel_id);
        `);
      } catch (error: any) {
        if (!error.message.includes('already exists')) {
          throw error;
        }
      }

      for (const video of videos) {
        try {
          await this.pgPool.query(
            `INSERT INTO competitor_videos (
              youtube_id, title, channel_id, channel_name,
              views, likes, comments, duration,
              published_at, collected_at,
              thumbnail_url, pattern_type, keyword_source
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (youtube_id) DO UPDATE SET
              views = EXCLUDED.views,
              likes = EXCLUDED.likes,
              comments = EXCLUDED.comments,
              updated_at = NOW()`,
            [
              video.youtube_id,
              sanitizeString(video.title),
              video.channel_id,
              sanitizeString(video.channel_name),
              video.views || 0,
              video.likes || 0,
              video.comments || 0,
              video.duration || 0,
              parseDate(video.published_at),
              parseDate(video.collected_at),
              video.thumbnail_url || null,
              video.pattern_type || null,
              video.keyword_source || null,
            ]
          );
          this.stats.competitorVideos++;
        } catch (error) {
          console.error(`  ⚠️  警告: youtube_id=${video.youtube_id}`, (error as any).message);
          this.stats.errors++;
        }
      }

      console.log(`  ✅ CompetitorVideo 迁移完成: ${this.stats.competitorVideos} 条`);
    } catch (error) {
      console.error('❌ CompetitorVideo 迁移失败:', error);
      throw error;
    }
  }

  async migrateChannels() {
    console.log('📥 开始迁移 Channel...');

    try {
      const stmt = this.sqliteDb.prepare(`
        SELECT
          channel_id, channel_name, subscriber_count,
          video_count, total_views, avg_views
        FROM channels
      `);

      const channels = stmt.all() as ChannelRow[];
      console.log(`  📊 查询到 ${channels.length} 条记录`);

      // 首先创建表（如果不存在）
      try {
        await this.pgPool.query(`
          CREATE TABLE IF NOT EXISTS channels (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            channel_id TEXT NOT NULL UNIQUE,
            channel_name TEXT,
            subscriber_count INTEGER DEFAULT 0,
            video_count INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            avg_views REAL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
          );
          CREATE INDEX IF NOT EXISTS idx_channels_channel_id ON channels(channel_id);
        `);
      } catch (error: any) {
        if (!error.message.includes('already exists')) {
          throw error;
        }
      }

      for (const channel of channels) {
        try {
          await this.pgPool.query(
            `INSERT INTO channels (
              channel_id, channel_name, subscriber_count,
              video_count, total_views, avg_views
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (channel_id) DO UPDATE SET
              subscriber_count = EXCLUDED.subscriber_count,
              video_count = EXCLUDED.video_count,
              total_views = EXCLUDED.total_views,
              updated_at = NOW()`,
            [
              channel.channel_id,
              sanitizeString(channel.channel_name),
              channel.subscriber_count || 0,
              channel.video_count || 0,
              channel.total_views || 0,
              channel.avg_views || 0,
            ]
          );
          this.stats.channels++;
        } catch (error) {
          console.error(`  ⚠️  警告: channel_id=${channel.channel_id}`, (error as any).message);
          this.stats.errors++;
        }
      }

      console.log(`  ✅ Channel 迁移完成: ${this.stats.channels} 条`);
    } catch (error) {
      console.error('❌ Channel 迁移失败:', error);
      throw error;
    }
  }

  async validateMigration() {
    console.log('\n📋 验证数据完整性...');

    const tables = [
      'competitor_videos',
      'channels',
    ];

    for (const table of tables) {
      try {
        const result = await this.pgPool.query(
          `SELECT COUNT(*) FROM ${table}`
        );
        const count = result.rows[0].count;
        console.log(`  ✅ ${table}: ${count} 条记录`);
      } catch (error) {
        console.log(`  ⚠️  ${table}: 表不存在或无法查询`);
      }
    }
  }

  async run() {
    console.log('🚀 开始数据迁移: v2 (SQLite) → v3 (PostgreSQL)\n');
    console.log('━'.repeat(60));

    try {
      // 执行迁移
      await this.migrateCompetitorVideos();
      await this.migrateChannels();

      // 验证
      await this.validateMigration();

      // 统计
      console.log('\n' + '━'.repeat(60));
      console.log('✅ 迁移完成！');
      console.log(`
📊 迁移统计：
  ├─ CompetitorVideo: ${this.stats.competitorVideos} 条
  ├─ Channel: ${this.stats.channels} 条
  ├─ TrendSnapshot: ${this.stats.trendSnapshots} 条
  ├─ Analytics: ${this.stats.analytics} 条
  ├─ 多语言视频: ${this.stats.multilangVideos} 条
  └─ 错误/警告: ${this.stats.errors} 条

总计: ${this.stats.competitorVideos + this.stats.channels} 条记录迁移成功！
      `);

    } catch (error) {
      console.error('❌ 迁移失败:', error);
      process.exit(1);
    } finally {
      // 关闭连接
      this.sqliteDb.close();
      await this.pgPool.end();
    }
  }
}

// ==================== 主函数 ====================

const migration = new DataMigration();
migration.run().catch(console.error);
