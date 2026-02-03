#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化监控相关的数据库表
- video_stats_history: 视频播放量历史记录
- watched_channels: 关注的博主列表
- channel_publications: 博主发布记录
- channel_alerts: 告警记录
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"


def init_tables():
    """创建监控相关的表"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 1. 视频统计历史表 - 用于追踪视频增长
    c.execute("""
        CREATE TABLE IF NOT EXISTS video_stats_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT NOT NULL,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- 计算字段（采集时计算）
            view_count_delta INTEGER,        -- 与上次记录的差值
            hours_since_last INTEGER,        -- 距上次记录的小时数
            growth_rate REAL,                -- 增长率

            FOREIGN KEY (youtube_id) REFERENCES competitor_videos(youtube_id)
        )
    """)

    # 索引优化
    c.execute("CREATE INDEX IF NOT EXISTS idx_stats_youtube_id ON video_stats_history(youtube_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_stats_recorded_at ON video_stats_history(recorded_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_stats_composite ON video_stats_history(youtube_id, recorded_at)")

    # 2. 视频监控状态表 - 记录每个视频的监控等级和增长状态
    c.execute("""
        CREATE TABLE IF NOT EXISTS video_monitoring (
            youtube_id TEXT PRIMARY KEY,
            monitoring_tier TEXT DEFAULT 'normal',  -- 'high', 'medium', 'normal', 'low'
            is_potential INTEGER DEFAULT 0,         -- 标记为潜力视频

            -- 增长指标
            last_growth_rate REAL,                  -- 最近一次增长率
            avg_growth_rate REAL,                   -- 平均增长率
            growth_acceleration REAL,              -- 增长加速度
            viral_score REAL,                       -- 病毒指数

            -- 监控状态
            last_checked_at TIMESTAMP,
            next_check_at TIMESTAMP,
            check_count INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (youtube_id) REFERENCES competitor_videos(youtube_id)
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_monitoring_tier ON video_monitoring(monitoring_tier)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_monitoring_next_check ON video_monitoring(next_check_at)")

    # 3. 关注的博主列表
    c.execute("""
        CREATE TABLE IF NOT EXISTS watched_channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            channel_url TEXT,

            -- 监控配置
            priority TEXT DEFAULT 'normal',         -- 'critical', 'high', 'normal', 'low'
            watch_reason TEXT,                      -- 'competitor', 'influential', 'underrated', 'manual'
            check_interval_minutes INTEGER DEFAULT 120,

            -- 状态跟踪
            last_video_id TEXT,                     -- 最新视频ID
            last_video_at TIMESTAMP,                -- 最后发视频时间
            last_checked_at TIMESTAMP,              -- 最后检查时间
            avg_videos_per_week REAL,               -- 平均每周发布数

            -- 关注的话题
            interested_topics TEXT,                 -- JSON数组 ["养生", "中医"]

            -- 统计
            total_videos_tracked INTEGER DEFAULT 0,

            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_watched_priority ON watched_channels(priority, is_active)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_watched_next_check ON watched_channels(last_checked_at)")

    # 4. 博主发布记录
    c.execute("""
        CREATE TABLE IF NOT EXISTS channel_publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            youtube_id TEXT UNIQUE NOT NULL,

            -- 基础信息
            title TEXT,
            description TEXT,
            published_at TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration INTEGER,
            thumbnail_url TEXT,

            -- 内容分析
            extracted_keywords TEXT,                -- JSON数组
            content_type TEXT,                      -- 'tutorial', 'review', 'vlog', etc.
            topic_match_score REAL,                 -- 与关注话题的匹配度

            -- 初始数据
            initial_view_count INTEGER,
            initial_like_count INTEGER,

            FOREIGN KEY (channel_id) REFERENCES watched_channels(channel_id)
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_publications_channel ON channel_publications(channel_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_publications_time ON channel_publications(published_at)")

    # 5. 告警记录
    c.execute("""
        CREATE TABLE IF NOT EXISTS channel_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT,
            youtube_id TEXT,

            alert_type TEXT,                        -- 'new_video', 'topic_match', 'competitor_move', 'viral_growth'
            alert_level TEXT,                       -- 'urgent', 'important', 'info'
            alert_message TEXT,
            alert_data TEXT,                        -- JSON 额外数据

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            read_at TIMESTAMP
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_unread ON channel_alerts(is_read, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON channel_alerts(alert_type)")

    conn.commit()
    conn.close()

    print("✓ 监控相关表已创建完成")
    print("  - video_stats_history: 视频播放量历史")
    print("  - video_monitoring: 视频监控状态")
    print("  - watched_channels: 关注的博主")
    print("  - channel_publications: 博主发布记录")
    print("  - channel_alerts: 告警记录")


def verify_tables():
    """验证表是否创建成功"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    tables = [
        "video_stats_history",
        "video_monitoring",
        "watched_channels",
        "channel_publications",
        "channel_alerts"
    ]

    print("\n验证表结构:")
    for table in tables:
        c.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
        exists = c.fetchone()[0] > 0
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")

    conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("初始化监控数据库表")
    print("=" * 50)
    init_tables()
    verify_tables()
