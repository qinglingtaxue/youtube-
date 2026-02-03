#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评论采集脚本
从 Top 视频获取评论内容，用于用户反馈分析

采集字段：
- youtube_id: 视频ID
- comment_id: 评论ID
- text: 评论内容
- author: 作者
- author_id: 作者ID
- like_count: 点赞数
- reply_count: 回复数
- is_pinned: 是否置顶
- timestamp: 发布时间

使用方法:
    python scripts/fetch_comments.py                    # 采集 Top 100 视频的评论
    python scripts/fetch_comments.py --limit 50        # 采集 Top 50 视频
    python scripts/fetch_comments.py --max-comments 20 # 每视频最多20条评论
"""

import argparse
import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# 路径配置
DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"

# 默认配置
DEFAULT_VIDEO_LIMIT = 100      # 默认采集 Top 100 视频
DEFAULT_MAX_COMMENTS = 50      # 每视频最多评论数
REQUEST_DELAY = 3              # 请求间隔（秒）


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_comments_table():
    """创建评论表"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS video_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT NOT NULL,           -- 视频ID
            comment_id TEXT UNIQUE,             -- 评论ID
            text TEXT,                          -- 评论内容
            author TEXT,                        -- 作者昵称
            author_id TEXT,                     -- 作者ID (@xxx)
            like_count INTEGER DEFAULT 0,       -- 点赞数
            reply_count INTEGER DEFAULT 0,      -- 回复数
            is_pinned INTEGER DEFAULT 0,        -- 是否置顶
            is_favorited INTEGER DEFAULT 0,     -- 是否被频道主喜欢
            published_at TEXT,                  -- 发布时间

            -- 采集元数据
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (youtube_id) REFERENCES competitor_videos(youtube_id)
        )
    """)

    # 索引
    c.execute("CREATE INDEX IF NOT EXISTS idx_comments_video ON video_comments(youtube_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_comments_likes ON video_comments(like_count DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_comments_time ON video_comments(published_at)")

    conn.commit()
    conn.close()
    print("✓ video_comments 表已初始化")


def get_top_videos(limit: int) -> List[Dict]:
    """获取播放量 Top N 的视频"""
    conn = get_connection()
    c = conn.cursor()

    # 排除已采集评论的视频
    c.execute("""
        SELECT cv.youtube_id, cv.title, cv.view_count, cv.comment_count
        FROM competitor_videos cv
        LEFT JOIN (
            SELECT youtube_id, COUNT(*) as collected_count
            FROM video_comments
            GROUP BY youtube_id
        ) vc ON cv.youtube_id = vc.youtube_id
        WHERE cv.comment_count > 0
          AND (vc.collected_count IS NULL OR vc.collected_count < 5)
        ORDER BY cv.view_count DESC
        LIMIT ?
    """, (limit,))

    videos = [
        {
            "youtube_id": row[0],
            "title": row[1],
            "view_count": row[2],
            "comment_count": row[3],
        }
        for row in c.fetchall()
    ]

    conn.close()
    return videos


def fetch_comments(youtube_id: str, max_comments: int = 50) -> Optional[List[Dict]]:
    """
    使用 yt-dlp 获取视频评论

    Args:
        youtube_id: 视频ID
        max_comments: 最大评论数

    Returns:
        评论列表
    """
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-warnings",
            "--write-comments",
            "--extractor-args", f"youtube:comment_sort=top;max_comments={max_comments}",
            f"https://www.youtube.com/watch?v={youtube_id}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        comments = data.get("comments", [])

        # 解析评论
        parsed = []
        for c in comments:
            parsed.append({
                "youtube_id": youtube_id,
                "comment_id": c.get("id"),
                "text": c.get("text", ""),
                "author": c.get("author"),
                "author_id": c.get("author_id"),
                "like_count": c.get("like_count", 0) or 0,
                "reply_count": c.get("reply_count", 0) or 0,
                "is_pinned": 1 if c.get("is_pinned") else 0,
                "is_favorited": 1 if c.get("is_favorited") else 0,
                "published_at": datetime.fromtimestamp(c["timestamp"]).isoformat() if c.get("timestamp") else None,
            })

        return parsed

    except subprocess.TimeoutExpired:
        return None
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"  错误: {e}")
        return None


def save_comments(comments: List[Dict]):
    """保存评论到数据库"""
    if not comments:
        return

    conn = get_connection()
    c = conn.cursor()

    for comment in comments:
        try:
            c.execute("""
                INSERT INTO video_comments
                (youtube_id, comment_id, text, author, author_id, like_count,
                 reply_count, is_pinned, is_favorited, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(comment_id) DO UPDATE SET
                    like_count = excluded.like_count,
                    reply_count = excluded.reply_count
            """, (
                comment["youtube_id"],
                comment["comment_id"],
                comment["text"],
                comment["author"],
                comment["author_id"],
                comment["like_count"],
                comment["reply_count"],
                comment["is_pinned"],
                comment["is_favorited"],
                comment["published_at"],
            ))
        except sqlite3.Error:
            continue

    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="采集 YouTube 视频评论")
    parser.add_argument("--limit", type=int, default=DEFAULT_VIDEO_LIMIT,
                        help=f"采集 Top N 视频 (默认 {DEFAULT_VIDEO_LIMIT})")
    parser.add_argument("--max-comments", type=int, default=DEFAULT_MAX_COMMENTS,
                        help=f"每视频最多评论数 (默认 {DEFAULT_MAX_COMMENTS})")
    args = parser.parse_args()

    print("=" * 70)
    print("YouTube 评论采集")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 初始化表
    init_comments_table()

    # 获取 Top 视频
    videos = get_top_videos(args.limit)
    total = len(videos)

    print(f"\n待采集视频: {total} 个")
    print(f"每视频最多: {args.max_comments} 条评论")
    print(f"预计耗时: {total * (REQUEST_DELAY + 5) / 60:.1f} 分钟")
    print("\n" + "-" * 70)
    print(f"{'#':<5} {'状态':<4} {'标题':<30} {'播放':<10} {'评论':<8} {'采集'}")
    print("-" * 70)

    # 统计
    stats = {"success": 0, "error": 0, "total_comments": 0}
    start_time = time.time()

    for i, video in enumerate(videos):
        youtube_id = video["youtube_id"]
        title = video["title"][:28]
        view_count = video["view_count"]
        comment_count = video["comment_count"]

        # 采集评论
        comments = fetch_comments(youtube_id, args.max_comments)

        if comments:
            save_comments(comments)
            stats["success"] += 1
            stats["total_comments"] += len(comments)
            print(f"{i+1:<5} {'✓':<4} {title:<30} {view_count:<10,} {comment_count:<8} {len(comments)}条")
        else:
            stats["error"] += 1
            print(f"{i+1:<5} {'✗':<4} {title:<30} {view_count:<10,} {comment_count:<8} 失败")

        # 请求间隔
        if i < total - 1:
            time.sleep(REQUEST_DELAY)

    elapsed = time.time() - start_time

    # 输出总结
    print("\n" + "=" * 70)
    print("采集完成")
    print(f"  成功: {stats['success']} 个视频")
    print(f"  失败: {stats['error']} 个视频")
    print(f"  总评论: {stats['total_comments']} 条")
    print(f"  耗时: {elapsed/60:.1f} 分钟")
    print("=" * 70)


if __name__ == "__main__":
    main()
