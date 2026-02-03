#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动采集脚本

功能：
1. 自动采集 1000 个新发布的视频
2. 按上传日期排序，优先获取最新视频
3. 记录采集日志和结果
4. 可配置为 cron/launchd 定时任务

使用方法：
    # 手动运行
    python scripts/daily_collect.py

    # 设置 cron 定时任务（每天凌晨 2 点）
    0 2 * * * cd /path/to/project && python scripts/daily_collect.py

    # macOS launchd 定时任务
    # 创建 ~/Library/LaunchAgents/com.youtube.daily-collect.plist
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.research.data_collector import DataCollector
from src.monitoring.trend_monitor import TrendMonitor


def setup_logging():
    """设置日志"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"daily_collect_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def daily_collect(
    theme: str = "老人养生",
    target_count: int = 1000,
    detail_min_views: int = 5000,
    detail_limit: int = 100,
    take_snapshot: bool = True
):
    """
    执行每日采集任务

    Args:
        theme: 采集主题
        target_count: 目标采集数量
        detail_min_views: 获取详情的最小播放量
        detail_limit: 获取详情的数量上限
        take_snapshot: 是否拍摄播放量快照
    """
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info(f"每日采集任务开始 - 主题: {theme}")
    logger.info("=" * 50)

    start_time = datetime.now()
    result = {
        'date': start_time.strftime('%Y-%m-%d'),
        'theme': theme,
        'target_count': target_count,
        'status': 'running',
    }

    try:
        # 1. 执行数据采集
        logger.info(f"目标: 采集 {target_count} 个新视频")
        collector = DataCollector()

        collect_result = collector.collect_large_scale(
            theme=theme,
            target_count=target_count,
            detail_min_views=detail_min_views,
            detail_limit=detail_limit,
            sort_by='date'  # 按日期排序，优先最新
        )

        result['collection'] = {
            'new_videos': collect_result['phase1']['new_videos'],
            'skipped': collect_result['phase1']['skipped'],
            'details_success': collect_result['phase2']['success'],
            'details_failed': collect_result['phase2']['failed'],
        }

        result['database'] = collect_result['database']

        logger.info(f"采集完成:")
        logger.info(f"  - 新增视频: {result['collection']['new_videos']}")
        logger.info(f"  - 跳过已存在: {result['collection']['skipped']}")
        logger.info(f"  - 详情获取成功: {result['collection']['details_success']}")
        logger.info(f"  - 详情获取失败: {result['collection']['details_failed']}")

        # 2. 拍摄播放量快照（用于趋势分析）
        if take_snapshot:
            logger.info("拍摄播放量快照...")
            monitor = TrendMonitor()
            snapshot_result = monitor.take_snapshot(min_views=1000)
            result['snapshot'] = snapshot_result
            logger.info(f"快照完成: {snapshot_result['video_count']} 个视频")

        # 3. 统计信息
        result['status'] = 'success'
        result['elapsed_seconds'] = (datetime.now() - start_time).total_seconds()

        logger.info(f"总耗时: {result['elapsed_seconds']:.1f} 秒")

    except Exception as e:
        logger.error(f"采集失败: {e}", exc_info=True)
        result['status'] = 'failed'
        result['error'] = str(e)
        result['elapsed_seconds'] = (datetime.now() - start_time).total_seconds()

    # 保存采集结果
    result_dir = project_root / "data" / "daily_reports"
    result_dir.mkdir(parents=True, exist_ok=True)

    result_file = result_dir / f"collect_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"结果已保存: {result_file}")
    logger.info("=" * 50)

    return result


def generate_launchd_plist():
    """生成 macOS launchd 配置文件"""
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.youtube.daily-collect</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{Path(__file__).absolute()}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{project_root}/logs/launchd_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{project_root}/logs/launchd_stderr.log</string>
    <key>WorkingDirectory</key>
    <string>{project_root}</string>
</dict>
</plist>'''

    plist_path = Path.home() / "Library/LaunchAgents/com.youtube.daily-collect.plist"
    print(f"将以下内容保存到: {plist_path}")
    print("-" * 50)
    print(plist_content)
    print("-" * 50)
    print("\n然后运行:")
    print(f"  launchctl load {plist_path}")
    print(f"  launchctl start com.youtube.daily-collect")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='每日自动采集脚本')
    parser.add_argument('--theme', default='老人养生', help='采集主题')
    parser.add_argument('--count', type=int, default=1000, help='目标采集数量')
    parser.add_argument('--detail-min-views', type=int, default=5000, help='获取详情的最小播放量')
    parser.add_argument('--detail-limit', type=int, default=100, help='获取详情的数量上限')
    parser.add_argument('--no-snapshot', action='store_true', help='不拍摄快照')
    parser.add_argument('--show-launchd', action='store_true', help='显示 launchd 配置')

    args = parser.parse_args()

    if args.show_launchd:
        generate_launchd_plist()
    else:
        daily_collect(
            theme=args.theme,
            target_count=args.count,
            detail_min_views=args.detail_min_views,
            detail_limit=args.detail_limit,
            take_snapshot=not args.no_snapshot,
        )
