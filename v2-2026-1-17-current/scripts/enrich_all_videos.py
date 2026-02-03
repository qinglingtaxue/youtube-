#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台批量补充视频详情脚本

功能：
- 遍历数据库中所有没有详情的视频
- 调用 yt-dlp 获取完整详情（点赞、评论、描述、标签等）
- 更新到数据库
- 支持断点续传（已处理的不会重复处理）
- 后台运行，不影响前端使用

使用方法：
    # 后台运行（推荐）
    nohup python scripts/enrich_all_videos.py > logs/enrich_videos.log 2>&1 &

    # 或前台运行查看进度
    python scripts/enrich_all_videos.py

    # 指定参数
    python scripts/enrich_all_videos.py --batch-size 100 --delay 2
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.logger import setup_logger
from src.shared.config import get_config
from src.shared.models import CompetitorVideo
from src.shared.repositories import CompetitorVideoRepository
from src.research.yt_dlp_client import YtDlpClient, YtDlpError

logger = setup_logger('enrich_videos')


def enrich_all_videos(
    batch_size: int = 500,
    delay: float = 1.5,
    min_views: int = 0,
    db_path: str = None
):
    """
    批量补充所有视频的详情

    Args:
        batch_size: 每批处理数量
        delay: 每个视频之间的延迟（秒）
        min_views: 最小播放量阈值（0 表示所有视频）
        db_path: 数据库路径
    """
    logger.info("=" * 60)
    logger.info("开始批量补充视频详情")
    logger.info("=" * 60)

    # 初始化
    config = get_config()
    repo = CompetitorVideoRepository(db_path)

    try:
        ytdlp = YtDlpClient(config)
    except YtDlpError as e:
        logger.error(f"yt-dlp 初始化失败: {e}")
        return

    # 获取统计信息
    stats = repo.get_statistics()
    total_videos = stats['total']
    with_details = stats['with_details']
    need_details = total_videos - with_details

    logger.info(f"数据库统计:")
    logger.info(f"  - 总视频数: {total_videos}")
    logger.info(f"  - 已有详情: {with_details}")
    logger.info(f"  - 需要补充: {need_details}")
    logger.info(f"")
    logger.info(f"参数配置:")
    logger.info(f"  - 每批数量: {batch_size}")
    logger.info(f"  - 请求延迟: {delay} 秒")
    logger.info(f"  - 最小播放量: {min_views}")
    logger.info("")

    if need_details == 0:
        logger.info("所有视频都已有详情，无需处理")
        return

    # 预估时间
    estimated_seconds = need_details * (delay + 3)  # 假设每个视频 3 秒处理 + 延迟
    estimated_minutes = estimated_seconds / 60
    logger.info(f"预计耗时: {estimated_minutes:.1f} 分钟")
    logger.info("")

    # 开始处理
    start_time = time.time()
    success_count = 0
    fail_count = 0
    processed = 0

    while True:
        # 获取一批需要处理的视频
        videos = repo.find_without_details(min_views=min_views, limit=batch_size)

        if not videos:
            logger.info("没有更多需要处理的视频")
            break

        logger.info(f"本批次处理 {len(videos)} 个视频...")

        for i, video in enumerate(videos):
            processed += 1

            try:
                # 获取详情
                logger.info(f"[{processed}/{need_details}] 获取详情: {video.youtube_id} - {video.title[:40]}...")

                details = ytdlp.get_video_info(video.youtube_id)

                # 转换为模型
                enriched = CompetitorVideo.from_ytdlp_details(details, video.keyword_source)

                # 更新数据库
                repo.update_details(enriched)
                success_count += 1

                # 进度日志
                if processed % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = (need_details - processed) / rate if rate > 0 else 0
                    logger.info(f"进度: {processed}/{need_details} ({processed*100//need_details}%), "
                               f"成功: {success_count}, 失败: {fail_count}, "
                               f"剩余约 {remaining/60:.1f} 分钟")

                # 延迟
                time.sleep(delay)

            except YtDlpError as e:
                logger.warning(f"获取视频 {video.youtube_id} 详情失败: {e}")
                fail_count += 1
                # 失败后稍微多等一会
                time.sleep(delay * 2)

            except Exception as e:
                logger.error(f"处理视频 {video.youtube_id} 时出错: {e}")
                fail_count += 1
                time.sleep(delay)

    # 完成统计
    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 60)
    logger.info("批量补充完成!")
    logger.info("=" * 60)
    logger.info(f"总处理: {processed}")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {fail_count}")
    logger.info(f"耗时: {elapsed/60:.1f} 分钟")

    # 最终统计
    final_stats = repo.get_statistics()
    logger.info("")
    logger.info(f"数据库最终状态:")
    logger.info(f"  - 总视频数: {final_stats['total']}")
    logger.info(f"  - 已有详情: {final_stats['with_details']}")
    logger.info(f"  - 详情覆盖率: {final_stats['with_details']*100//final_stats['total'] if final_stats['total'] > 0 else 0}%")


def main():
    parser = argparse.ArgumentParser(description='后台批量补充视频详情')
    parser.add_argument('--batch-size', type=int, default=500, help='每批处理数量')
    parser.add_argument('--delay', type=float, default=1.5, help='每个视频之间的延迟（秒）')
    parser.add_argument('--min-views', type=int, default=0, help='最小播放量阈值')
    parser.add_argument('--db-path', type=str, default=None, help='数据库路径')

    args = parser.parse_args()

    # 确保日志目录存在
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    enrich_all_videos(
        batch_size=args.batch_size,
        delay=args.delay,
        min_views=args.min_views,
        db_path=args.db_path
    )


if __name__ == '__main__':
    main()
