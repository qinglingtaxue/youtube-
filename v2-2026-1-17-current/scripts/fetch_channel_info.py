#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
频道信息采集脚本
从 YouTube 频道 About 页面获取完整信息

采集字段：
- channel_id: 频道ID
- channel_name: 频道名称
- handle: @用户名
- subscriber_count: 订阅数
- video_count: 视频数
- total_views: 总观看数
- country: 国家/地区
- description: 频道描述
- created_at: 加入时间

使用方法:
    python scripts/fetch_channel_info.py              # 采集所有
    python scripts/fetch_channel_info.py --limit 100  # 只采集100个
    python scripts/fetch_channel_info.py --workers 5  # 5并发
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 路径配置
DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"

# 并发配置
DEFAULT_WORKERS = 3
REQUEST_DELAY = 1.5  # 请求间隔（秒）


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_channel_table():
    """创建/更新 channels 表结构"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            handle TEXT,                    -- @用户名
            subscriber_count INTEGER,
            video_count INTEGER,
            total_views INTEGER,            -- 总观看数
            country TEXT,                   -- 国家/地区
            description TEXT,               -- 频道描述
            created_at TEXT,                -- 频道创建时间 (YYYY-MM-DD)
            canonical_url TEXT,             -- 频道URL

            -- 采集元数据
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 索引
    c.execute("CREATE INDEX IF NOT EXISTS idx_channels_created ON channels(created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_channels_subs ON channels(subscriber_count DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_channels_country ON channels(country)")

    conn.commit()
    conn.close()
    print("✓ channels 表已初始化")


def get_channels_to_fetch(limit: Optional[int] = None) -> list:
    """
    获取需要采集的频道列表
    优先采集有视频但缺少频道信息的频道
    """
    conn = get_connection()
    c = conn.cursor()

    # 从 competitor_videos 表获取所有独立的 channel_id
    # 排除已经在 channels 表中的
    query = """
        SELECT
            cv.channel_id,
            cv.channel_name,
            MAX(cv.subscriber_count) as max_subs
        FROM competitor_videos cv
        LEFT JOIN channels ch ON cv.channel_id = ch.channel_id
        WHERE cv.channel_id IS NOT NULL
          AND cv.channel_id != ''
          AND ch.channel_id IS NULL
        GROUP BY cv.channel_id
        ORDER BY max_subs DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    c.execute(query)
    channels = [
        {
            "channel_id": row[0],
            "channel_name": row[1],
            "subscriber_count": row[2] or 0,
        }
        for row in c.fetchall()
    ]

    conn.close()
    return channels


def parse_joined_date(joined_str: str) -> Optional[str]:
    """
    解析 YouTube 频道创建时间字符串

    输入格式示例:
    - "Joined 12 Nov 2019"
    - "Joined Nov 12, 2019"
    - "2019年11月12日加入"

    返回: ISO 格式日期 "2019-11-12"
    """
    if not joined_str:
        return None

    # 英文格式1: "Joined 12 Nov 2019"
    match = re.search(r'Joined\s+(\d{1,2})\s+(\w+)\s+(\d{4})', joined_str, re.IGNORECASE)
    if match:
        day, month_str, year = match.groups()
        month = parse_month(month_str)
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"

    # 英文格式2: "Joined Nov 12, 2019"
    match = re.search(r'Joined\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})', joined_str, re.IGNORECASE)
    if match:
        month_str, day, year = match.groups()
        month = parse_month(month_str)
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"

    # 中文格式: "2019年11月12日"
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', joined_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return None


def parse_month(month_str: str) -> Optional[int]:
    """解析月份字符串"""
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10,
        'november': 11, 'december': 12
    }
    return months.get(month_str.lower()[:3])


def parse_count(count_str: str) -> int:
    """
    解析数量字符串

    输入: "776k subscribers", "211,765,003 views", "494 videos"
    返回: 整数
    """
    if not count_str:
        return 0

    # 移除逗号和非数字字符（保留K/M/B）
    clean = count_str.replace(',', '').strip()

    # 提取数字部分
    match = re.search(r'([\d.]+)\s*([KMBkmb])?', clean)
    if not match:
        return 0

    num_str, suffix = match.groups()
    try:
        num = float(num_str)
    except ValueError:
        return 0

    # 处理 K/M/B 后缀
    multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
    if suffix:
        num *= multipliers.get(suffix.lower(), 1)

    return int(num)


def fetch_channel_about(channel_id: str) -> Optional[Dict[str, Any]]:
    """
    从 YouTube 频道 About 页面获取完整信息

    直接解析页面内嵌的 ytInitialData JSON
    """
    try:
        url = f"https://www.youtube.com/channel/{channel_id}/about"

        cmd = ["curl", "-s", "-L", "--max-time", "15",
               "-H", "Accept-Language: en-US,en;q=0.9",  # 强制英文以统一日期格式
               url]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

        if result.returncode != 0 or not result.stdout:
            return None

        html = result.stdout

        # 提取 ytInitialData JSON
        match = re.search(r'var ytInitialData = ({.*?});', html)
        if not match:
            return None

        data = json.loads(match.group(1))

        # 查找 aboutChannelViewModel
        about_data = find_about_channel_data(data)
        if not about_data:
            return None

        # 解析各字段
        channel_info = {
            "channel_id": about_data.get("channelId") or channel_id,
            "channel_name": None,
            "handle": None,
            "subscriber_count": 0,
            "video_count": 0,
            "total_views": 0,
            "country": about_data.get("country"),
            "description": about_data.get("description"),
            "created_at": None,
            "canonical_url": about_data.get("canonicalChannelUrl"),
        }

        # 解析订阅数: "776k subscribers"
        if about_data.get("subscriberCountText"):
            channel_info["subscriber_count"] = parse_count(about_data["subscriberCountText"])

        # 解析视频数: "494 videos"
        if about_data.get("videoCountText"):
            channel_info["video_count"] = parse_count(about_data["videoCountText"])

        # 解析总观看: "211,765,003 views"
        if about_data.get("viewCountText"):
            channel_info["total_views"] = parse_count(about_data["viewCountText"])

        # 解析加入时间: {"content": "Joined 12 Nov 2019"}
        joined_text = about_data.get("joinedDateText")
        if isinstance(joined_text, dict):
            joined_text = joined_text.get("content", "")
        if joined_text:
            channel_info["created_at"] = parse_joined_date(joined_text)

        # 解析 handle: "www.youtube.com/@windstory" -> "@windstory"
        display_url = about_data.get("displayCanonicalChannelUrl", "")
        if "@" in display_url:
            match = re.search(r'@[\w.-]+', display_url)
            if match:
                channel_info["handle"] = match.group(0)

        # 从页面获取频道名称（aboutChannelViewModel 不包含）
        channel_name = extract_channel_name(data)
        if channel_name:
            channel_info["channel_name"] = channel_name

        return channel_info

    except subprocess.TimeoutExpired:
        return None
    except json.JSONDecodeError:
        return None
    except Exception as e:
        return None


def find_about_channel_data(data: dict) -> Optional[dict]:
    """递归查找 aboutChannelViewModel 数据"""
    if isinstance(data, dict):
        if "aboutChannelViewModel" in data:
            return data["aboutChannelViewModel"]
        for value in data.values():
            result = find_about_channel_data(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_about_channel_data(item)
            if result:
                return result
    return None


def extract_channel_name(data: dict) -> Optional[str]:
    """从 ytInitialData 中提取频道名称"""
    try:
        # 尝试从 metadata 中获取
        if isinstance(data, dict):
            # 路径1: metadata.channelMetadataRenderer.title
            metadata = data.get("metadata", {})
            if "channelMetadataRenderer" in metadata:
                return metadata["channelMetadataRenderer"].get("title")

            # 路径2: header.c4TabbedHeaderRenderer.title
            header = data.get("header", {})
            if "c4TabbedHeaderRenderer" in header:
                return header["c4TabbedHeaderRenderer"].get("title")

            # 递归查找
            for value in data.values():
                result = extract_channel_name(value)
                if result:
                    return result
    except:
        pass
    return None


def save_channel_info(channel_info: Dict[str, Any]):
    """保存频道信息到数据库"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO channels
        (channel_id, channel_name, handle, subscriber_count, video_count,
         total_views, country, description, created_at, canonical_url,
         collected_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(channel_id) DO UPDATE SET
            channel_name = COALESCE(excluded.channel_name, channels.channel_name),
            handle = COALESCE(excluded.handle, channels.handle),
            subscriber_count = excluded.subscriber_count,
            video_count = excluded.video_count,
            total_views = excluded.total_views,
            country = COALESCE(excluded.country, channels.country),
            description = COALESCE(excluded.description, channels.description),
            created_at = COALESCE(excluded.created_at, channels.created_at),
            canonical_url = COALESCE(excluded.canonical_url, channels.canonical_url),
            updated_at = CURRENT_TIMESTAMP
    """, (
        channel_info["channel_id"],
        channel_info["channel_name"],
        channel_info["handle"],
        channel_info["subscriber_count"],
        channel_info["video_count"],
        channel_info["total_views"],
        channel_info["country"],
        channel_info["description"],
        channel_info["created_at"],
        channel_info["canonical_url"],
        datetime.now().isoformat(),
        datetime.now().isoformat(),
    ))

    conn.commit()
    conn.close()


def process_channel(channel: dict) -> dict:
    """处理单个频道"""
    channel_id = channel["channel_id"]

    info = fetch_channel_about(channel_id)
    time.sleep(REQUEST_DELAY)

    if info and (info["subscriber_count"] > 0 or info["created_at"]):
        save_channel_info(info)
        return {
            "status": "success",
            "channel_id": channel_id,
            "channel_name": info["channel_name"],
            "handle": info["handle"],
            "subscriber_count": info["subscriber_count"],
            "video_count": info["video_count"],
            "total_views": info["total_views"],
            "country": info["country"],
            "created_at": info["created_at"],
        }
    else:
        return {
            "status": "error",
            "channel_id": channel_id,
            "channel_name": channel.get("channel_name"),
        }


def format_number(n: int) -> str:
    """格式化数字显示"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def main():
    parser = argparse.ArgumentParser(description="采集 YouTube 频道完整信息")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"并发数 (默认 {DEFAULT_WORKERS})")
    parser.add_argument("--limit", type=int, default=None,
                        help="最多采集 N 个频道")
    args = parser.parse_args()

    print("=" * 70)
    print("YouTube 频道信息采集")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 初始化表
    init_channel_table()

    # 获取待采集频道
    channels = get_channels_to_fetch(args.limit)
    total = len(channels)

    print(f"\n待采集频道: {total} 个")

    if total == 0:
        print("没有需要采集的频道")
        return

    print(f"并发数: {args.workers}")
    print(f"预计耗时: {total * REQUEST_DELAY / args.workers / 60:.1f} 分钟")
    print("\n" + "-" * 70)
    print(f"{'#':<5} {'状态':<4} {'频道名':<20} {'订阅':<10} {'视频':<8} {'创建时间':<12} {'地区'}")
    print("-" * 70)

    # 统计
    stats = {"success": 0, "error": 0, "with_date": 0}
    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process_channel, ch): ch for ch in channels}

            for i, future in enumerate(as_completed(futures)):
                result = future.result()

                if result["status"] == "success":
                    stats["success"] += 1

                    name = (result["channel_name"] or result["handle"] or result["channel_id"])[:18]
                    subs = format_number(result["subscriber_count"])
                    videos = result["video_count"] or 0
                    created = result["created_at"] or "-"
                    country = (result["country"] or "-")[:8]

                    if result["created_at"]:
                        stats["with_date"] += 1
                        icon = "✓"
                    else:
                        icon = "○"

                    print(f"{i+1:<5} {icon:<4} {name:<20} {subs:<10} {videos:<8} {created:<12} {country}")
                else:
                    stats["error"] += 1
                    name = result.get("channel_name") or result.get("channel_id", "unknown")
                    print(f"{i+1:<5} {'✗':<4} {name[:20]:<20} {'失败'}")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")

    elapsed = time.time() - start_time

    # 输出总结
    print("\n" + "=" * 70)
    print("采集完成")
    print(f"  成功: {stats['success']} 个")
    print(f"  失败: {stats['error']} 个")
    print(f"  获取到创建时间: {stats['with_date']} 个 ({stats['with_date']*100//max(stats['success'],1)}%)")
    print(f"  耗时: {elapsed/60:.1f} 分钟")
    print("=" * 70)


if __name__ == "__main__":
    main()
