/**
 * v2 数据库验证脚本
 *
 * 用途: 迁移前验证 v2 SQLite 数据库的完整性
 * 运行: bun run scripts/validate_v2_data.ts
 */

import Database from 'better-sqlite3';
import path from 'path';
import { statSync, existsSync } from 'fs';

// ==================== 配置 ====================

const DB_PATH = './data/youtube_pipeline.db';

// ==================== 验证函数 ====================

class DataValidator {
  private db: Database.Database;

  constructor() {
    this.db = new Database(DB_PATH);
  }

  /**
   * 获取所有表名
   */
  getTables(): string[] {
    const stmt = this.db.prepare(`
      SELECT name FROM sqlite_master
      WHERE type='table' AND name NOT LIKE 'sqlite_%'
      ORDER BY name
    `);
    return stmt.all().map((row: any) => row.name);
  }

  /**
   * 验证表结构
   */
  validateTable(tableName: string): {
    name: string;
    columns: number;
    rows: number;
    status: 'OK' | 'EMPTY' | 'ERROR';
  } {
    try {
      const countStmt = this.db.prepare(`SELECT COUNT(*) as count FROM ${tableName}`);
      const rowCount = (countStmt.get() as any).count;

      const colStmt = this.db.prepare(`PRAGMA table_info(${tableName})`);
      const columns = (colStmt.all() as any[]).length;

      return {
        name: tableName,
        columns,
        rows: rowCount,
        status: rowCount > 0 ? 'OK' : 'EMPTY',
      };
    } catch (error) {
      return {
        name: tableName,
        columns: 0,
        rows: 0,
        status: 'ERROR',
      };
    }
  }

  /**
   * 验证关键表的数据质量
   */
  validateDataQuality() {
    console.log('\n📋 数据质量检查...\n');

    // 检查 CompetitorVideo
    try {
      const stmt = this.db.prepare(`
        SELECT
          COUNT(*) as total,
          COUNT(DISTINCT youtube_id) as unique_videos,
          COUNT(CASE WHEN youtube_id IS NULL THEN 1 END) as null_videos,
          COUNT(CASE WHEN title IS NULL THEN 1 END) as null_titles,
          COUNT(CASE WHEN views < 0 THEN 1 END) as negative_views
        FROM competitor_videos
      `);
      const result = stmt.get() as any;

      console.log('✅ CompetitorVideo 数据质量:');
      console.log(`   ├─ 总记录数: ${result.total}`);
      console.log(`   ├─ 唯一 youtube_id: ${result.unique_videos}`);
      console.log(`   ├─ 空 youtube_id: ${result.null_videos}`);
      console.log(`   ├─ 空 title: ${result.null_titles}`);
      console.log(`   └─ 负数 views: ${result.negative_views}`);

      if (result.total === result.unique_videos) {
        console.log('   ✅ 数据无重复（已去重）\n');
      } else {
        console.log(`   ⚠️  有 ${result.total - result.unique_videos} 条重复记录\n`);
      }
    } catch (error) {
      console.log('❌ CompetitorVideo 检查失败\n');
    }

    // 检查 Channel
    try {
      const stmt = this.db.prepare(`
        SELECT
          COUNT(*) as total,
          COUNT(DISTINCT channel_id) as unique_channels,
          COUNT(CASE WHEN channel_id IS NULL THEN 1 END) as null_channel_ids
        FROM channels
      `);
      const result = stmt.get() as any;

      console.log('✅ Channel 数据质量:');
      console.log(`   ├─ 总记录数: ${result.total}`);
      console.log(`   ├─ 唯一 channel_id: ${result.unique_channels}`);
      console.log(`   └─ 空 channel_id: ${result.null_channel_ids}\n`);
    } catch (error) {
      console.log('❌ Channel 检查失败\n');
    }

    // 检查时间戳范围
    try {
      const stmt = this.db.prepare(`
        SELECT
          MIN(published_at) as oldest_video,
          MAX(published_at) as newest_video,
          MIN(collected_at) as first_collected,
          MAX(collected_at) as last_collected
        FROM competitor_videos
      `);
      const result = stmt.get() as any;

      console.log('✅ 时间跨度:');
      console.log(`   ├─ 最早发布: ${result.oldest_video}`);
      console.log(`   ├─ 最新发布: ${result.newest_video}`);
      console.log(`   ├─ 首次采集: ${result.first_collected}`);
      console.log(`   └─ 最后采集: ${result.last_collected}\n`);
    } catch (error) {
      console.log('❌ 时间戳检查失败\n');
    }
  }

  /**
   * 运行完整验证
   */
  run() {
    console.log('🔍 v2 数据库验证\n');
    console.log(`📁 数据库路径: ${DB_PATH}\n`);
    console.log('━'.repeat(60));

    // 检查文件是否存在
    if (!existsSync(DB_PATH)) {
      console.log(`❌ 数据库文件不存在: ${DB_PATH}`);
      process.exit(1);
    }

    // 获取文件大小
    const stats = statSync(DB_PATH);
    console.log(`📊 数据库大小: ${(stats.size / 1024 / 1024).toFixed(2)} MB\n`);

    // 验证所有表
    console.log('📋 表结构验证:\n');
    const tables = this.getTables();
    console.log(`发现 ${tables.length} 个表:\n`);

    const tableStats = tables.map((table) => this.validateTable(table));

    // 按状态分类显示
    const okTables = tableStats.filter((t) => t.status === 'OK');
    const emptyTables = tableStats.filter((t) => t.status === 'EMPTY');
    const errorTables = tableStats.filter((t) => t.status === 'ERROR');

    if (okTables.length > 0) {
      console.log('✅ 有数据的表:');
      okTables.forEach((t) => {
        console.log(`   ├─ ${t.name}: ${t.rows} 条记录 (${t.columns} 列)`);
      });
      console.log();
    }

    if (emptyTables.length > 0) {
      console.log('⚪ 空表:');
      emptyTables.forEach((t) => {
        console.log(`   ├─ ${t.name}: 0 条记录`);
      });
      console.log();
    }

    if (errorTables.length > 0) {
      console.log('❌ 错误的表:');
      errorTables.forEach((t) => {
        console.log(`   ├─ ${t.name}: 无法访问`);
      });
      console.log();
    }

    // 总结统计
    const totalRecords = tableStats.reduce((sum, t) => sum + t.rows, 0);
    console.log('━'.repeat(60));
    console.log(`\n📊 总计: ${totalRecords} 条记录\n`);

    // 数据质量检查
    this.validateDataQuality();

    // 迁移检查清单
    console.log('━'.repeat(60));
    console.log('\n✅ 迁移前检查清单:\n');

    const checks = [
      { name: 'CompetitorVideo 数据完整', pass: okTables.some((t) => t.name === 'competitor_videos') },
      { name: 'Channel 数据完整', pass: okTables.some((t) => t.name === 'channels') },
      { name: '数据库文件可读取', pass: true },
      { name: '没有表结构错误', pass: errorTables.length === 0 },
    ];

    checks.forEach((check) => {
      const icon = check.pass ? '✅' : '❌';
      console.log(`${icon} ${check.name}`);
    });

    const allPassed = checks.every((c) => c.pass);
    console.log('\n' + (allPassed ? '✅ 所有检查通过！可以开始迁移' : '❌ 存在问题，请先解决'));

    this.db.close();
  }
}

// ==================== 主函数 ====================

const validator = new DataValidator();
validator.run();
