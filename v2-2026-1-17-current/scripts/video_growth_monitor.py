#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频增长监控脚本
定时采集视频播放量，计算增长率，检测病毒式增长

使用方法:
    # 单次运行
    python scripts/video_growth_monitor.py

    # 定时任务 (crontab)
    # 每6小时执行一次
    0 */6 * * * cd /path/to/project && .venv/bin/python scripts/video_growth_monitor.py
"""

import json
import sqlite3
import subprocess
import sys
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Optional

# 路径配置
DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"

# 并发配置
WORKERS = 5  # 采集并发数

# 监控配置
TIERS = {
    "high": {"interval_hours": 6, "description": "高频监控 - 新视频/潜力视频"},
    "medium": {"interval_hours": 12, "description": "中频监控 - 中期视频"},
    "normal": {"interval_hours": 24, "description": "常规监控 - 一般视频"},
    "low": {"interval_hours": 72, "description": "低频监控 - 老视频"},
}

# 病毒式增长判定阈值
VIRAL_THRESHOLDS = {
    "growth_rate_min": 0.3,       # 最低增长率 30%
    "acceleration_min": 0.1,      # 最低加速度
    "min_data_points": 3,         # 最少数据点数
}

# 锁
db_lock = Lock()

# 统计
stats = {
    "checked": 0,
    "updated": 0,
    "new_viral": 0,
    "errors": 0,
}


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(str(DB_PATH), timeout=30)


def get_videos_to_monitor() -> list:
    """
    获取需要监控的视频列表
    优先级：
    1. 新视频（<7天）
    2. 已标记为潜力视频
    3. 上次检查时间超过间隔的视频
    """
    conn = get_connection()
    c = conn.cursor()

    now = datetime.now()

    # 获取需要检查的视频
    # 优先选择：新视频、潜力视频、超过检查间隔的视频
    c.execute("""
        SELECT
            cv.youtube_id,
            cv.title,
            cv.view_count,
            cv.published_at,
            COALESCE(vm.monitoring_tier, 'normal') as tier,
            COALESCE(vm.is_potential, 0) as is_potential,
            vm.last_checked_at
        FROM competitor_videos cv
        LEFT JOIN video_monitoring vm ON cv.youtube_id = vm.youtube_id
        WHERE cv.has_details = 1
          AND cv.view_count > 0
          AND cv.published_at IS NOT NULL
        ORDER BY
            -- 优先级排序：潜力视频 > 新视频 > 上次检查时间
            COALESCE(vm.is_potential, 0) DESC,
            cv.published_at DESC,
            vm.last_checked_at ASC
        LIMIT 100
    """)

    videos = []
    for row in c.fetchall():
        youtube_id, title, view_count, published_at, tier, is_potential, last_checked = row

        # 计算视频年龄
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            video_age_days = (now - pub_date.replace(tzinfo=None)).days
        except:
            video_age_days = 999

        # 判断是否需要检查
        needs_check = False

        if last_checked is None:
            needs_check = True  # 从未检查过
        else:
            try:
                last_check_time = datetime.fromisoformat(last_checked)
                interval = TIERS.get(tier, TIERS["normal"])["interval_hours"]
                if (now - last_check_time).total_seconds() > interval * 3600:
                    needs_check = True
            except:
                needs_check = True

        # 新视频总是检查
        if video_age_days <= 7:
            needs_check = True

        # 潜力视频总是检查
        if is_potential:
            needs_check = True

        if needs_check:
            videos.append({
                "youtube_id": youtube_id,
                "title": title,
                "current_views": view_count,
                "video_age_days": video_age_days,
                "tier": tier,
                "is_potential": is_potential,
            })

    conn.close()
    return videos


def fetch_video_stats(video_id: str) -> Optional[dict]:
    """使用 yt-dlp 获取视频当前统计"""
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
                "view_count": data.get("view_count", 0),
                "like_count": data.get("like_count", 0),
                "comment_count": data.get("comment_count", 0),
            }
        return None
    except:
        return None


def get_last_stats(conn, youtube_id: str) -> Optional[dict]:
    """获取上一次记录的统计"""
    c = conn.cursor()
    c.execute("""
        SELECT view_count, like_count, comment_count, recorded_at
        FROM video_stats_history
        WHERE youtube_id = ?
        ORDER BY recorded_at DESC
        LIMIT 1
    """, (youtube_id,))
    row = c.fetchone()

    if row:
        return {
            "view_count": row[0],
            "like_count": row[1],
            "comment_count": row[2],
            "recorded_at": row[3],
        }
    return None


def calculate_growth_metrics(current: dict, previous: Optional[dict]) -> dict:
    """计算增长指标"""
    if not previous:
        return {
            "view_count_delta": 0,
            "hours_since_last": 0,
            "growth_rate": 0,
        }

    view_delta = current["view_count"] - previous["view_count"]

    try:
        last_time = datetime.fromisoformat(previous["recorded_at"])
        hours = (datetime.now() - last_time).total_seconds() / 3600
    except:
        hours = 24

    # 增长率 = 增量 / 原值
    if previous["view_count"] > 0:
        growth_rate = view_delta / previous["view_count"]
    else:
        growth_rate = 0

    return {
        "view_count_delta": view_delta,
        "hours_since_last": round(hours, 1),
        "growth_rate": round(growth_rate, 4),
    }


def save_stats(conn, youtube_id: str, stats: dict, growth: dict):
    """保存统计数据到历史表"""
    c = conn.cursor()
    c.execute("""
        INSERT INTO video_stats_history
        (youtube_id, view_count, like_count, comment_count,
         view_count_delta, hours_since_last, growth_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        youtube_id,
        stats["view_count"],
        stats["like_count"],
        stats["comment_count"],
        growth["view_count_delta"],
        growth["hours_since_last"],
        growth["growth_rate"],
    ))
    conn.commit()


def update_monitoring_status(conn, youtube_id: str, growth_rate: float,
                            acceleration: float, video_age_days: int):
    """更新视频监控状态"""
    c = conn.cursor()

    # 判断监控等级
    if video_age_days <= 3:
        tier = "high"
    elif video_age_days <= 14:
        tier = "medium"
    elif video_age_days <= 30:
        tier = "normal"
    else:
        tier = "low"

    # 判断是否为潜力视频
    is_potential = 1 if growth_rate > VIRAL_THRESHOLDS["growth_rate_min"] else 0

    # 计算病毒指数
    viral_score = growth_rate * (1 + acceleration) * 100 if acceleration > 0 else 0

    # 更新或插入
    c.execute("""
        INSERT INTO video_monitoring
        (youtube_id, monitoring_tier, is_potential, last_growth_rate,
         growth_acceleration, viral_score, last_checked_at, check_count, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(youtube_id) DO UPDATE SET
            monitoring_tier = ?,
            is_potential = ?,
            last_growth_rate = ?,
            growth_acceleration = ?,
            viral_score = ?,
            last_checked_at = ?,
            check_count = check_count + 1,
            updated_at = ?
    """, (
        youtube_id, tier, is_potential, growth_rate, acceleration, viral_score,
        datetime.now().isoformat(), datetime.now().isoformat(),
        tier, is_potential, growth_rate, acceleration, viral_score,
        datetime.now().isoformat(), datetime.now().isoformat(),
    ))
    conn.commit()

    return is_potential, viral_score


def calculate_acceleration(conn, youtube_id: str) -> float:
    """计算增长加速度（需要至少3个数据点）"""
    c = conn.cursor()
    c.execute("""
        SELECT growth_rate, recorded_at
        FROM video_stats_history
        WHERE youtube_id = ?
        ORDER BY recorded_at DESC
        LIMIT 5
    """, (youtube_id,))

    rows = c.fetchall()
    if len(rows) < 3:
        return 0

    # 增长率序列（从旧到新）
    growth_rates = [r[0] for r in reversed(rows) if r[0] is not None]

    if len(growth_rates) < 2:
        return 0

    # 加速度 = 最近增长率 - 上次增长率
    accelerations = [growth_rates[i] - growth_rates[i-1]
                     for i in range(1, len(growth_rates))]

    return sum(accelerations) / len(accelerations) if accelerations else 0


def detect_viral_growth(conn, youtube_id: str) -> bool:
    """检测是否为病毒式增长"""
    c = conn.cursor()
    c.execute("""
        SELECT growth_rate
        FROM video_stats_history
        WHERE youtube_id = ?
        ORDER BY recorded_at DESC
        LIMIT 5
    """, (youtube_id,))

    rows = c.fetchall()
    if len(rows) < VIRAL_THRESHOLDS["min_data_points"]:
        return False

    growth_rates = [r[0] for r in rows if r[0] is not None]

    # 条件1: 所有增长率都为正
    if not all(r > 0 for r in growth_rates):
        return False

    # 条件2: 最近增长率超过阈值
    if growth_rates[0] < VIRAL_THRESHOLDS["growth_rate_min"]:
        return False

    # 条件3: 增长在加速
    if len(growth_rates) >= 2:
        acceleration = growth_rates[0] - growth_rates[1]
        if acceleration < VIRAL_THRESHOLDS["acceleration_min"]:
            return False

    return True


def process_video(video: dict) -> dict:
    """处理单个视频"""
    youtube_id = video["youtube_id"]

    # 获取当前统计
    current_stats = fetch_video_stats(youtube_id)
    if not current_stats:
        return {"status": "error", "youtube_id": youtube_id}

    with db_lock:
        conn = get_connection()

        # 获取上次统计
        last_stats = get_last_stats(conn, youtube_id)

        # 计算增长指标
        growth = calculate_growth_metrics(current_stats, last_stats)

        # 保存历史
        save_stats(conn, youtube_id, current_stats, growth)

        # 计算加速度
        acceleration = calculate_acceleration(conn, youtube_id)

        # 更新监控状态
        is_potential, viral_score = update_monitoring_status(
            conn, youtube_id, growth["growth_rate"],
            acceleration, video["video_age_days"]
        )

        # 检测病毒式增长
        is_viral = detect_viral_growth(conn, youtube_id)

        conn.close()

    return {
        "status": "success",
        "youtube_id": youtube_id,
        "title": video["title"][:30],
        "current_views": current_stats["view_count"],
        "delta": growth["view_count_delta"],
        "growth_rate": growth["growth_rate"],
        "acceleration": acceleration,
        "is_potential": is_potential,
        "is_viral": is_viral,
        "viral_score": viral_score,
    }


def main():
    print("=" * 60)
    print("视频增长监控")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 获取需要监控的视频
    videos = get_videos_to_monitor()
    total = len(videos)

    print(f"\n待检查视频: {total} 个")

    if total == 0:
        print("没有需要检查的视频")
        return

    print(f"并发数: {WORKERS}")
    print(f"预计耗时: {total * 3 // WORKERS // 60 + 1} 分钟\n")

    start_time = time.time()
    viral_videos = []

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = {executor.submit(process_video, v): v for v in videos}

            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                stats["checked"] += 1

                if result["status"] == "success":
                    stats["updated"] += 1

                    # 输出进度
                    delta_str = f"+{result['delta']:,}" if result['delta'] >= 0 else f"{result['delta']:,}"
                    rate_str = f"{result['growth_rate']*100:.1f}%"

                    status_icon = "✓"
                    if result["is_viral"]:
                        status_icon = "🔥"
                        stats["new_viral"] += 1
                        viral_videos.append(result)
                    elif result["is_potential"]:
                        status_icon = "⬆"

                    print(f"[{stats['checked']}/{total}] {status_icon} {result['title']}... | "
                          f"播放:{result['current_views']:,} ({delta_str}) | 增长:{rate_str}")
                else:
                    stats["errors"] += 1
                    print(f"[{stats['checked']}/{total}] ✗ {result['youtube_id']}")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")

    elapsed = time.time() - start_time

    # 输出总结
    print(f"\n" + "=" * 60)
    print("监控完成")
    print(f"  检查: {stats['checked']} 个")
    print(f"  成功: {stats['updated']} 个")
    print(f"  失败: {stats['errors']} 个")
    print(f"  耗时: {elapsed/60:.1f} 分钟")

    if viral_videos:
        print(f"\n🔥 发现 {len(viral_videos)} 个快速增长视频:")
        for v in viral_videos[:5]:
            print(f"  - {v['title']}... (增长率:{v['growth_rate']*100:.1f}%)")

    print("=" * 60)


if __name__ == "__main__":
    main()
