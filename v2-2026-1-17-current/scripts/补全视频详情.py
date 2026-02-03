#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补全视频详情数据
使用 yt-dlp 获取缺失的 published_at 和 channel_id 字段
"""

import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"

# 批次大小
BATCH_SIZE = 50


def get_videos_to_update(conn, limit=None):
    """获取需要更新的视频列表"""
    c = conn.cursor()
    query = """
        SELECT youtube_id, title, channel_name
        FROM competitor_videos
        WHERE theme='养生' AND (published_at IS NULL OR channel_id IS NULL)
    """
    if limit:
        query += f" LIMIT {limit}"
    c.execute(query)
    return c.fetchall()


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
        else:
            print(f"  ⚠️ yt-dlp 错误: {result.stderr[:100]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ 超时")
        return None
    except Exception as e:
        print(f"  ⚠️ 异常: {e}")
        return None


def parse_upload_date(date_str):
    """解析 yt-dlp 返回的日期格式 (YYYYMMDD)"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d").isoformat()
    except:
        return None


def update_video(conn, details):
    """更新视频详情到数据库"""
    if not details:
        return False

    c = conn.cursor()

    # 构建更新语句（只更新非空字段）
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

    # 标记已获取详情
    updates.append("has_details = 1")

    if not updates:
        return False

    values.append(details["youtube_id"])

    query = f"UPDATE competitor_videos SET {', '.join(updates)} WHERE youtube_id = ?"
    c.execute(query, values)
    conn.commit()
    return True


def main():
    print("=" * 60)
    print("补全视频详情数据")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))

    # 获取需要更新的视频
    videos = get_videos_to_update(conn)
    total = len(videos)

    print(f"\n需要补全的视频: {total} 个")

    if total == 0:
        print("没有需要补全的视频")
        conn.close()
        return

    # 确认开始
    print(f"\n预计耗时: {total * 2 // 60} 分钟（每个视频约2秒）")
    print("按 Ctrl+C 可随时中断\n")

    success = 0
    failed = 0
    start_time = time.time()

    try:
        for i, (video_id, title, channel) in enumerate(videos):
            progress = f"[{i+1}/{total}]"
            print(f"{progress} 处理: {title[:40]}...")

            # 获取详情
            details = fetch_video_details(video_id)

            if details:
                if update_video(conn, details):
                    success += 1
                    pub = details.get("published_at", "无")[:10] if details.get("published_at") else "无"
                    print(f"  ✓ 已更新 (发布: {pub}, 频道ID: {details.get('channel_id', '无')[:15]}...)")
                else:
                    failed += 1
                    print(f"  ✗ 更新失败")
            else:
                failed += 1

            # 速率限制
            time.sleep(1)

            # 每50个显示进度
            if (i + 1) % BATCH_SIZE == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (total - i - 1) / rate
                print(f"\n--- 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%) ---")
                print(f"成功: {success}, 失败: {failed}")
                print(f"剩余时间: {remaining/60:.1f} 分钟\n")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")

    finally:
        conn.close()
        elapsed = time.time() - start_time
        print(f"\n" + "=" * 60)
        print(f"完成统计:")
        print(f"  处理: {success + failed} 个")
        print(f"  成功: {success} 个")
        print(f"  失败: {failed} 个")
        print(f"  耗时: {elapsed/60:.1f} 分钟")
        print("=" * 60)


if __name__ == "__main__":
    main()
