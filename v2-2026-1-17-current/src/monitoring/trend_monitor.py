#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定期监控模块 - 追踪视频增长趋势

功能：
1. 记录视频播放量快照
2. 计算不同时间窗口的增长趋势
3. 生成增长趋势图数据
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TrendMonitor:
    """视频增长趋势监控器"""

    def __init__(self, db_path: str = "data/videos.db"):
        self.db_path = Path(db_path)
        self.snapshot_path = Path("data/monitoring/snapshots")
        self.snapshot_path.mkdir(parents=True, exist_ok=True)
        self._init_monitoring_tables()

    def _init_monitoring_tables(self):
        """初始化监控相关的数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 播放量快照表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS view_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                views INTEGER NOT NULL,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        ''')

        # 快照索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_snapshot_video_time
            ON view_snapshots(video_id, snapshot_time)
        ''')

        # 监控配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitor_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def take_snapshot(self, min_views: int = 1000) -> Dict[str, Any]:
        """
        拍摄当前所有视频的快照

        Args:
            min_views: 最小播放量筛选

        Returns:
            快照统计信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取符合条件的视频
        cursor.execute('''
            SELECT video_id, views, likes, comments
            FROM videos
            WHERE views >= ?
        ''', (min_views,))

        videos = cursor.fetchall()
        snapshot_time = datetime.now().isoformat()

        # 批量插入快照
        snapshot_count = 0
        for video_id, views, likes, comments in videos:
            cursor.execute('''
                INSERT INTO view_snapshots (video_id, views, likes, comments, snapshot_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (video_id, views or 0, likes or 0, comments or 0, snapshot_time))
            snapshot_count += 1

        conn.commit()
        conn.close()

        return {
            'snapshot_time': snapshot_time,
            'video_count': snapshot_count,
            'min_views_filter': min_views,
        }

    def get_growth_data(self, video_id: str, days: int = 30) -> List[Dict]:
        """
        获取单个视频的增长数据

        Args:
            video_id: 视频ID
            days: 查询天数

        Returns:
            增长数据列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT snapshot_time, views, likes, comments
            FROM view_snapshots
            WHERE video_id = ? AND snapshot_time >= ?
            ORDER BY snapshot_time ASC
        ''', (video_id, since))

        rows = cursor.fetchall()
        conn.close()

        result = []
        prev_views = None
        for snapshot_time, views, likes, comments in rows:
            growth = views - prev_views if prev_views is not None else 0
            result.append({
                'time': snapshot_time,
                'views': views,
                'likes': likes,
                'comments': comments,
                'growth': growth,
            })
            prev_views = views

        return result

    def get_trending_videos(
        self,
        time_window: str = '1天内',
        top_n: int = 10
    ) -> List[Dict]:
        """
        获取指定时间窗口内增长最快的视频

        Args:
            time_window: 时间窗口 ('1天内', '15天内', '30天内')
            top_n: 返回数量

        Returns:
            增长最快的视频列表
        """
        # 时间窗口映射
        window_days = {
            '1天内': 1,
            '15天内': 15,
            '30天内': 30,
            '7天内': 7,
            '90天内': 90,
        }
        days = window_days.get(time_window, 30)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        # 计算每个视频在时间窗口内的增长
        cursor.execute('''
            WITH first_snapshot AS (
                SELECT video_id, MIN(snapshot_time) as first_time, views as first_views
                FROM view_snapshots
                WHERE snapshot_time >= ?
                GROUP BY video_id
            ),
            last_snapshot AS (
                SELECT video_id, MAX(snapshot_time) as last_time, views as last_views
                FROM view_snapshots
                WHERE snapshot_time >= ?
                GROUP BY video_id
            )
            SELECT
                f.video_id,
                l.last_views - f.first_views as growth,
                f.first_views,
                l.last_views,
                f.first_time,
                l.last_time
            FROM first_snapshot f
            JOIN last_snapshot l ON f.video_id = l.video_id
            WHERE l.last_views > f.first_views
            ORDER BY growth DESC
            LIMIT ?
        ''', (since, since, top_n))

        rows = cursor.fetchall()

        # 获取视频详情
        result = []
        for video_id, growth, first_views, last_views, first_time, last_time in rows:
            cursor.execute('''
                SELECT title, channel, url
                FROM videos
                WHERE video_id = ?
            ''', (video_id,))
            video = cursor.fetchone()
            if video:
                title, channel, url = video
                result.append({
                    'video_id': video_id,
                    'title': title,
                    'channel': channel,
                    'url': url,
                    'growth': growth,
                    'first_views': first_views,
                    'last_views': last_views,
                    'first_time': first_time,
                    'last_time': last_time,
                    'time_window': time_window,
                })

        conn.close()
        return result

    def generate_trend_chart_data(self, time_window: str = '30天内') -> Dict[str, Any]:
        """
        生成增长趋势图数据

        Args:
            time_window: 时间窗口

        Returns:
            Chart.js 兼容的图表数据
        """
        window_days = {
            '1天内': 1,
            '15天内': 15,
            '30天内': 30,
        }
        days = window_days.get(time_window, 30)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        # 按日期聚合总播放量
        cursor.execute('''
            SELECT
                DATE(snapshot_time) as date,
                SUM(views) as total_views,
                COUNT(DISTINCT video_id) as video_count
            FROM view_snapshots
            WHERE snapshot_time >= ?
            GROUP BY DATE(snapshot_time)
            ORDER BY date ASC
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {
                'labels': [],
                'datasets': [],
                'summary': {'total_growth': 0, 'avg_daily_growth': 0},
            }

        dates = [row[0] for row in rows]
        total_views = [row[1] for row in rows]
        video_counts = [row[2] for row in rows]

        # 计算日增长
        daily_growth = []
        for i, views in enumerate(total_views):
            if i == 0:
                daily_growth.append(0)
            else:
                daily_growth.append(views - total_views[i - 1])

        total_growth = total_views[-1] - total_views[0] if len(total_views) > 1 else 0
        avg_daily = total_growth / len(dates) if dates else 0

        return {
            'labels': dates,
            'datasets': [
                {
                    'label': '累计播放量',
                    'data': total_views,
                    'borderColor': '#667eea',
                    'backgroundColor': 'rgba(102, 126, 234, 0.1)',
                    'fill': True,
                    'yAxisID': 'y',
                },
                {
                    'label': '日增长',
                    'data': daily_growth,
                    'borderColor': '#f5576c',
                    'backgroundColor': 'rgba(245, 87, 108, 0.1)',
                    'fill': True,
                    'yAxisID': 'y1',
                },
            ],
            'summary': {
                'total_growth': total_growth,
                'avg_daily_growth': int(avg_daily),
                'days': len(dates),
                'time_window': time_window,
            },
        }

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 快照总数
        cursor.execute('SELECT COUNT(*) FROM view_snapshots')
        total_snapshots = cursor.fetchone()[0]

        # 监控的视频数
        cursor.execute('SELECT COUNT(DISTINCT video_id) FROM view_snapshots')
        monitored_videos = cursor.fetchone()[0]

        # 最早和最晚快照
        cursor.execute('SELECT MIN(snapshot_time), MAX(snapshot_time) FROM view_snapshots')
        earliest, latest = cursor.fetchone()

        # 按日期统计快照数
        cursor.execute('''
            SELECT DATE(snapshot_time) as date, COUNT(*) as count
            FROM view_snapshots
            GROUP BY DATE(snapshot_time)
            ORDER BY date DESC
            LIMIT 7
        ''')
        recent_snapshots = cursor.fetchall()

        conn.close()

        return {
            'total_snapshots': total_snapshots,
            'monitored_videos': monitored_videos,
            'earliest_snapshot': earliest,
            'latest_snapshot': latest,
            'recent_daily_counts': [
                {'date': date, 'count': count}
                for date, count in recent_snapshots
            ],
        }

    def schedule_info(self) -> Dict[str, Any]:
        """返回推荐的监控调度信息"""
        return {
            'recommended_frequency': '每天一次',
            'best_time': '凌晨 2:00-4:00 (低峰期)',
            'cron_expression': '0 2 * * *',
            'commands': {
                'take_snapshot': 'python cli.py monitor snapshot',
                'view_trends': 'python cli.py monitor trends',
                'generate_report': 'python cli.py monitor report',
            },
            'notes': [
                '建议使用 cron 或 launchd 设置定时任务',
                '每次快照会记录所有视频的当前播放量',
                '积累数据后可以分析增长趋势',
            ],
        }


def take_snapshot(min_views: int = 1000) -> Dict:
    """便捷函数：拍摄快照"""
    monitor = TrendMonitor()
    return monitor.take_snapshot(min_views)


def get_trending(time_window: str = '1天内', top_n: int = 10) -> List[Dict]:
    """便捷函数：获取热门增长视频"""
    monitor = TrendMonitor()
    return monitor.get_trending_videos(time_window, top_n)


if __name__ == '__main__':
    monitor = TrendMonitor()

    print("=== 定期监控模块 ===\n")

    # 拍摄快照
    print("正在拍摄快照...")
    result = monitor.take_snapshot(min_views=1000)
    print(f"快照完成: {result['video_count']} 个视频")
    print(f"时间: {result['snapshot_time']}\n")

    # 获取统计
    stats = monitor.get_monitoring_stats()
    print("监控统计:")
    print(f"  总快照数: {stats['total_snapshots']}")
    print(f"  监控视频数: {stats['monitored_videos']}")
    print(f"  最早快照: {stats['earliest_snapshot']}")
    print(f"  最晚快照: {stats['latest_snapshot']}\n")

    # 调度信息
    schedule = monitor.schedule_info()
    print("推荐调度:")
    print(f"  频率: {schedule['recommended_frequency']}")
    print(f"  最佳时间: {schedule['best_time']}")
    print(f"  Cron: {schedule['cron_expression']}")
