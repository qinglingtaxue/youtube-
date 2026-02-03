#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行补全视频详情数据
使用多进程加速，5个并行任务
"""

import json
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"

# 并行数量
WORKERS = 10

# 数据库锁
db_lock = Lock()

# 统计
stats = {"success": 0, "failed": 0, "processed": 0}
stats_lock = Lock()


def get_videos_to_update():
    """获取需要更新的视频列表"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
        SELECT youtube_id, title
        FROM competitor_videos
        WHERE theme='养生' AND (published_at IS NULL OR channel_id IS NULL)
    """)
    videos = c.fetchall()
    conn.close()
    return videos


def fetch_video_details(video_id):
    """使用 yt-dlp 获取视频详情"""
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-warnings",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "youtube_id": video_id,
                "channel_id": data.get("channel_id") or data.get("uploader_id"),
                "published_at": parse_upload_date(data.get("upload_date")),
                "view_count": data.get("view_count"),
                "like_count": data.get("like_count"),
                "comment_count": data.get("comment_count"),
                "duration": data.get("duration"),
                "description": data.get("description", "")[:500] if data.get("description") else None,
                "tags": data.get("tags", [])[:10],
                "thumbnail_url": data.get("thumbnail"),
                "subscriber_count": data.get("channel_follower_count"),  # 频道订阅数
            }
        return None
    except:
        return None


def parse_upload_date(date_str):
    """解析日期"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d").isoformat()
    except:
        return None


def update_video(details):
    """更新视频详情到数据库"""
    if not details:
        return False

    with db_lock:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        updates = []
        values = []

        if details.get("channel_id"):
            updates.append("channel_id = ?")
            values.append(details["channel_id"])

        if details.get("published_at"):
            updates.append("published_at = ?")
            values.append(details["published_at"])

        if details.get("view_count") is not None:
            updates.append("view_count = ?")
            values.append(details["view_count"])

        if details.get("like_count") is not None:
            updates.append("like_count = ?")
            values.append(details["like_count"])

        if details.get("comment_count") is not None:
            updates.append("comment_count = ?")
            values.append(details["comment_count"])

        if details.get("duration") is not None:
            updates.append("duration = ?")
            values.append(details["duration"])

        if details.get("description"):
            updates.append("description = ?")
            values.append(details["description"])

        if details.get("tags"):
            updates.append("tags = ?")
            values.append(json.dumps(details["tags"]))

        if details.get("thumbnail_url"):
            updates.append("thumbnail_url = ?")
            values.append(details["thumbnail_url"])

        if details.get("subscriber_count") is not None:
            updates.append("subscriber_count = ?")
            values.append(details["subscriber_count"])

        updates.append("has_details = 1")

        if not updates:
            conn.close()
            return False

        values.append(details["youtube_id"])
        query = f"UPDATE competitor_videos SET {', '.join(updates)} WHERE youtube_id = ?"
        c.execute(query, values)
        conn.commit()
        conn.close()
        return True


def process_video(args):
    """处理单个视频"""
    index, total, video_id, title = args

    details = fetch_video_details(video_id)

    with stats_lock:
        stats["processed"] += 1
        if details and update_video(details):
            stats["success"] += 1
            pub = details.get("published_at", "")[:10] if details.get("published_at") else "无"
            print(f"[{stats['processed']}/{total}] ✓ {title[:30]}... (发布: {pub})")
            return True
        else:
            stats["failed"] += 1
            print(f"[{stats['processed']}/{total}] ✗ {title[:30]}...")
            return False


def main():
    print("=" * 60)
    print("并行补全视频详情数据")
    print(f"并行数: {WORKERS}")
    print("=" * 60)

    videos = get_videos_to_update()
    total = len(videos)

    print(f"\n需要补全的视频: {total} 个")
    print(f"预计耗时: {total * 2 // WORKERS // 60} 分钟\n")

    if total == 0:
        print("没有需要补全的视频")
        return

    start_time = time.time()

    # 准备任务参数
    tasks = [(i, total, vid, title) for i, (vid, title) in enumerate(videos)]

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = [executor.submit(process_video, task) for task in tasks]
            for future in as_completed(futures):
                pass  # 结果已在 process_video 中打印

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")

    elapsed = time.time() - start_time
    print(f"\n" + "=" * 60)
    print(f"完成统计:")
    print(f"  处理: {stats['processed']} 个")
    print(f"  成功: {stats['success']} 个")
    print(f"  失败: {stats['failed']} 个")
    print(f"  耗时: {elapsed/60:.1f} 分钟")
    print("=" * 60)


if __name__ == "__main__":
    main()
