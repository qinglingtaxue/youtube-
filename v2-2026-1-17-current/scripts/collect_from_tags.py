#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于已有视频标签进行二次采集
从数据库中提取高频标签，作为新关键词搜索更多视频

使用方法:
    python scripts/collect_from_tags.py --theme 养生
    python scripts/collect_from_tags.py --theme 养生 --top 20  # 只用前20个标签
    python scripts/collect_from_tags.py --theme 养生 --dry-run  # 预览不执行
"""

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.logger import setup_logger
from src.research.data_collector import DataCollector
import sqlite3

logger = setup_logger('collect_from_tags')

DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"


def get_high_freq_tags(theme: str, min_count: int = 10, top_n: int = 30) -> list:
    """
    从数据库提取高频标签

    Args:
        theme: 主题
        min_count: 最小出现次数
        top_n: 返回前N个

    Returns:
        [(tag, count), ...]
    """
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 获取已有关键词
    c.execute('''
        SELECT DISTINCT keyword_source FROM competitor_videos
        WHERE theme = ? AND keyword_source IS NOT NULL
    ''', (theme,))
    existing_keywords = set(row[0] for row in c.fetchall())

    # 获取标签
    c.execute('''
        SELECT tags FROM competitor_videos
        WHERE theme = ? AND tags IS NOT NULL AND tags != ""
    ''', (theme,))

    tag_counter = Counter()
    for row in c.fetchall():
        tags_str = row[0]
        if tags_str:
            try:
                tags = json.loads(tags_str)
                if isinstance(tags, list):
                    for tag in tags:
                        if tag and 2 <= len(tag) <= 10:
                            tag_counter[tag] += 1
            except:
                for tag in tags_str.split(','):
                    tag = tag.strip()
                    if tag and 2 <= len(tag) <= 10:
                        tag_counter[tag] += 1

    conn.close()

    # 过滤
    exclude_patterns = [
        'health', 'good health', 'advice', 'tips', 'care',  # 英文
        theme,  # 主题本身
    ]

    # 太通用的词
    generic_words = {
        '健康', '中医', '养生', '疾病', '保健', '视频', '频道',
        '中国', '台湾', '生活', '日常', '分享', '推荐',
    }

    result = []
    for tag, count in tag_counter.most_common(200):
        # 跳过已有关键词
        if tag in existing_keywords:
            continue
        # 跳过英文
        if any(p in tag.lower() for p in exclude_patterns):
            continue
        # 跳过太通用的
        if tag in generic_words:
            continue
        # 最小次数
        if count < min_count:
            continue

        result.append((tag, count))
        if len(result) >= top_n:
            break

    return result


def collect_by_tags(theme: str, tags: list, target_per_tag: int = 50) -> dict:
    """
    使用标签作为关键词采集

    Args:
        theme: 主题（用于分类存储）
        tags: [(tag, count), ...]
        target_per_tag: 每个标签目标数量

    Returns:
        采集统计
    """
    collector = DataCollector()

    total_new = 0
    total_skip = 0
    results = []

    for i, (tag, freq) in enumerate(tags):
        logger.info(f"[{i+1}/{len(tags)}] 采集关键词: {tag} (原频次: {freq})")

        try:
            # 使用 search_videos_parallel，传入 theme 确保正确分类
            new_count, skip_count = collector.search_videos_parallel(
                keyword=tag,
                max_per_strategy=target_per_tag,
                time_range="month",
                theme=theme,  # 传入 theme 确保正确分类
            )

            total_new += new_count
            total_skip += skip_count

            results.append({
                "tag": tag,
                "freq": freq,
                "new": new_count,
                "skip": skip_count,
            })

            logger.info(f"  → 新增 {new_count}, 跳过 {skip_count}")

            # 请求间隔
            time.sleep(2)

        except Exception as e:
            logger.error(f"  采集失败: {e}")
            results.append({
                "tag": tag,
                "freq": freq,
                "error": str(e),
            })

    return {
        "theme": theme,
        "tags_used": len(tags),
        "total_new": total_new,
        "total_skip": total_skip,
        "details": results,
    }


def main():
    parser = argparse.ArgumentParser(description="基于标签的二次采集")
    parser.add_argument("--theme", required=True, help="主题名称")
    parser.add_argument("--top", type=int, default=20, help="使用前N个高频标签 (默认20)")
    parser.add_argument("--min-count", type=int, default=10, help="标签最小出现次数 (默认10)")
    parser.add_argument("--target", type=int, default=50, help="每标签目标数量 (默认50)")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际采集")
    args = parser.parse_args()

    print("=" * 70)
    print("基于标签的二次采集")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 获取高频标签
    print(f"\n从 [{args.theme}] 主题提取高频标签...")
    tags = get_high_freq_tags(args.theme, args.min_count, args.top)

    if not tags:
        print("未找到合适的标签")
        return

    print(f"\n找到 {len(tags)} 个新关键词：")
    print("-" * 40)
    for tag, count in tags:
        print(f"  {count:4d}次  {tag}")
    print("-" * 40)

    if args.dry_run:
        print("\n[预览模式] 不执行采集")
        return

    # 确认执行
    print(f"\n将使用这 {len(tags)} 个关键词采集，每个目标 {args.target} 条")

    # 执行采集
    start_time = time.time()
    result = collect_by_tags(args.theme, tags, args.target)
    elapsed = time.time() - start_time

    # 输出结果
    print("\n" + "=" * 70)
    print("采集完成")
    print("=" * 70)
    print(f"使用标签数: {result['tags_used']}")
    print(f"新增视频: {result['total_new']}")
    print(f"跳过(已存在): {result['total_skip']}")
    print(f"耗时: {elapsed/60:.1f} 分钟")

    # 详细结果
    print("\n各标签采集情况：")
    for d in result['details']:
        if 'error' in d:
            print(f"  {d['tag']}: 错误 - {d['error']}")
        else:
            print(f"  {d['tag']}: +{d['new']} (跳过{d['skip']})")


if __name__ == "__main__":
    main()
