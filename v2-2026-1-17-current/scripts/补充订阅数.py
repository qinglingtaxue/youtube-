#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充频道订阅数数据
专门为 subscriber_count = 0 的视频补充订阅数信息
使用多线程并行采集，提高效率
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
stats = {"success": 0, "failed": 0, "processed": 0, "skipped": 0}
stats_lock = Lock()


def get_videos_without_subscribers(limit=None):
    """获取没有订阅数数据的视频（按频道去重，每个频道只取一个视频）"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 按频道去重，获取每个频道的一个视频 ID
    query = """
        SELECT youtube_id, channel_name, channel_id
        FROM competitor_videos
        WHERE has_details = 1
          AND (subscriber_count IS NULL OR subscriber_count = 0)
          AND channel_id IS NOT NULL
        GROUP BY channel_id
        ORDER BY view_count DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    c.execute(query)
    videos = c.fetchall()
    conn.close()
    return videos


def fetch_subscriber_count(video_id):
    """使用 yt-dlp 获取频道订阅数"""
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
                "channel_id": data.get("channel_id") or data.get("uploader_id"),
                "subscriber_count": data.get("channel_follower_count"),
            }
        return None
    except Exception as e:
        return None


def update_channel_subscribers(channel_id, subscriber_count):
    """更新该频道所有视频的订阅数"""
    if not channel_id or subscriber_count is None:
        return 0

    with db_lock:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        c.execute("""
            UPDATE competitor_videos
            SET subscriber_count = ?
            WHERE channel_id = ?
        """, (subscriber_count, channel_id))

        updated = c.rowcount
        conn.commit()
        conn.close()

        return updated


def process_video(args):
    """处理单个视频"""
    index, total, video_id, channel_name, channel_id = args

    # 获取订阅数
    result = fetch_subscriber_count(video_id)

    with stats_lock:
        stats["processed"] += 1

        if result and result.get("subscriber_count") is not None:
            subs = result["subscriber_count"]
            # 更新该频道所有视频
            updated = update_channel_subscribers(channel_id, subs)
            stats["success"] += 1

            # 格式化订阅数显示
            if subs >= 1000000:
                subs_str = f"{subs/1000000:.1f}M"
            elif subs >= 1000:
                subs_str = f"{subs/1000:.1f}K"
            else:
                subs_str = str(subs)

            print(f"[{stats['processed']}/{total}] ✓ {channel_name[:25]}... | 订阅:{subs_str} | 更新 {updated} 条")
            return True
        else:
            stats["failed"] += 1
            print(f"[{stats['processed']}/{total}] ✗ {channel_name[:25]}... | 获取失败")
            return False


def main():
    print("=" * 60)
    print("补充频道订阅数数据")
    print(f"并行数: {WORKERS}")
    print("=" * 60)

    # 获取需要更新的视频
    videos = get_videos_without_subscribers()
    total = len(videos)

    print(f"\n需要补充订阅数的频道: {total} 个")

    if total == 0:
        print("没有需要补充的频道")
        return

    print(f"预计耗时: {total * 3 // WORKERS // 60 + 1} 分钟\n")

    start_time = time.time()

    # 准备任务参数
    tasks = [(i, total, vid, channel, cid) for i, (vid, channel, cid) in enumerate(videos)]

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = [executor.submit(process_video, task) for task in tasks]
            for future in as_completed(futures):
                pass  # 结果已在 process_video 中打印

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")

    elapsed = time.time() - start_time

    # 验证结果
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM competitor_videos WHERE subscriber_count > 0")
    with_subs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM competitor_videos")
    total_videos = c.fetchone()[0]
    conn.close()

    print(f"\n" + "=" * 60)
    print(f"完成统计:")
    print(f"  处理: {stats['processed']} 个频道")
    print(f"  成功: {stats['success']} 个")
    print(f"  失败: {stats['failed']} 个")
    print(f"  耗时: {elapsed/60:.1f} 分钟")
    print(f"\n数据库状态:")
    print(f"  总视频数: {total_videos}")
    print(f"  有订阅数: {with_subs} ({with_subs/total_videos*100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
