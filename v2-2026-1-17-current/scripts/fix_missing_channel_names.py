#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复缺失的 channel_name

针对有 channel_id 但没有 channel_name 的视频，
从 YouTube 重新获取频道名称
"""

import sqlite3
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.yt_dlp_client import YtDlpClient, YtDlpError


def fix_missing_channel_names(db_path: str = "data/youtube_pipeline.db", limit: int = 200):
    """
    修复缺失的 channel_name

    对于有 channel_id 但没有 channel_name 的视频，
    重新从 YouTube 获取视频信息来获取频道名称
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 找出需要修复的视频
    cursor.execute("""
        SELECT youtube_id, channel_id, title
        FROM competitor_videos
        WHERE (channel_name IS NULL OR channel_name = '')
          AND channel_id IS NOT NULL AND channel_id != ''
          AND has_details = 1
        LIMIT ?
    """, (limit,))

    videos = cursor.fetchall()

    if not videos:
        print("没有需要修复的视频")
        return

    print(f"找到 {len(videos)} 个需要修复的视频")

    # 初始化 yt-dlp
    try:
        ytdlp = YtDlpClient()
    except YtDlpError as e:
        print(f"yt-dlp 初始化失败: {e}")
        return

    fixed_count = 0
    fail_count = 0

    for i, video in enumerate(videos):
        youtube_id = video['youtube_id']
        print(f"[{i+1}/{len(videos)}] 处理 {youtube_id}...", end=" ")

        try:
            # 获取视频信息
            info = ytdlp.get_video_info(youtube_id)
            channel_name = info.get('channel_name', '')
            subscriber_count = info.get('subscriber_count', 0)

            if channel_name:
                # 更新数据库
                cursor.execute("""
                    UPDATE competitor_videos
                    SET channel_name = ?, subscriber_count = ?
                    WHERE youtube_id = ?
                """, (channel_name, subscriber_count, youtube_id))
                conn.commit()
                print(f"✓ {channel_name}")
                fixed_count += 1
            else:
                print("✗ 仍然获取不到 channel_name")
                fail_count += 1

            # 速率限制
            time.sleep(1)

        except YtDlpError as e:
            print(f"✗ 错误: {e}")
            fail_count += 1
        except Exception as e:
            print(f"✗ 异常: {e}")
            fail_count += 1

    conn.close()

    print(f"\n完成: 修复 {fixed_count} 个, 失败 {fail_count} 个")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="修复缺失的 channel_name")
    parser.add_argument("--limit", type=int, default=200, help="最大处理数量")
    parser.add_argument("--db", type=str, default="data/youtube_pipeline.db", help="数据库路径")

    args = parser.parse_args()
    fix_missing_channel_names(args.db, args.limit)
