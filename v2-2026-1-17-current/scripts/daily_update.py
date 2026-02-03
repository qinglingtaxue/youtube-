#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日定时更新脚本

功能：
- 从 config/keywords/*.json 加载关键词配置
- 按优先级采集多个关键词
- 使用两轮采集策略（7天热门 + 60天覆盖）
- 记录更新日志

使用方法：
    # 手动运行
    python scripts/daily_update.py

    # 指定配置文件
    python scripts/daily_update.py --config yangsheng

    # macOS launchd 自动运行（每天上午 10 点）
    # ~/Library/LaunchAgents/com.youtube.daily-update.plist
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.logger import setup_logger
from src.research.data_collector import DataCollector

logger = setup_logger('daily_update')

# 配置目录
CONFIG_DIR = project_root / "config" / "keywords"

# 默认配置文件
DEFAULT_CONFIG = "yangsheng"


def load_keyword_config(config_name: str) -> Dict[str, Any]:
    """
    加载关键词配置文件

    Args:
        config_name: 配置文件名（不含 .json）

    Returns:
        配置字典
    """
    config_file = CONFIG_DIR / f"{config_name}.json"

    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    logger.info(f"加载配置: {config_file}")
    logger.info(f"主题: {config.get('topic', '未知')}")
    logger.info(f"关键词组: {len(config.get('groups', []))} 个")

    return config


def get_keywords_by_priority(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    按优先级提取所有关键词

    Returns:
        关键词列表，按优先级排序（high -> medium -> low）
    """
    priority_order = {"high": 0, "medium": 1, "low": 2}

    keywords = []
    for group in config.get("groups", []):
        priority = group.get("priority", "medium")
        weight = group.get("weight", 0.8)
        group_name = group.get("name", "未命名")

        for kw in group.get("keywords", []):
            keywords.append({
                "keyword": kw,
                "group": group_name,
                "priority": priority,
                "weight": weight,
                "priority_order": priority_order.get(priority, 1),
            })

    # 按优先级排序
    keywords.sort(key=lambda x: x["priority_order"])

    return keywords


def collect_keyword(collector: DataCollector, keyword: str, priority: str) -> Dict[str, Any]:
    """
    采集单个关键词的数据

    策略：
    - high 优先级：两轮采集（7天 + 60天）
    - medium 优先级：单轮采集（30天）
    - low 优先级：单轮采集（60天，数量少）

    Args:
        collector: DataCollector 实例
        keyword: 关键词
        priority: 优先级

    Returns:
        采集结果
    """
    logger.info(f"采集关键词: {keyword} (优先级: {priority})")
    start_time = time.time()

    total_new = 0
    total_details = 0

    try:
        if priority == "high":
            # 高优先级：两轮采集
            # 第一轮：7天内
            result1 = collector.collect_large_scale(
                theme=keyword,
                target_count=150,
                detail_min_views=5000,
                detail_limit=30,
                time_range="week",
            )
            total_new += result1.get("search_phase", {}).get("new_videos", 0)
            total_details += result1.get("detail_phase", {}).get("success", 0)

            # 第二轮：60天内
            result2 = collector.collect_large_scale(
                theme=keyword,
                target_count=300,
                detail_min_views=10000,
                detail_limit=50,
                time_range="two_months",
            )
            total_new += result2.get("search_phase", {}).get("new_videos", 0)
            total_details += result2.get("detail_phase", {}).get("success", 0)

        elif priority == "medium":
            # 中优先级：单轮采集（30天）
            result = collector.collect_large_scale(
                theme=keyword,
                target_count=200,
                detail_min_views=8000,
                detail_limit=30,
                time_range="month",
            )
            total_new += result.get("search_phase", {}).get("new_videos", 0)
            total_details += result.get("detail_phase", {}).get("success", 0)

        else:  # low
            # 低优先级：单轮采集（60天，数量少）
            result = collector.collect_large_scale(
                theme=keyword,
                target_count=100,
                detail_min_views=15000,
                detail_limit=20,
                time_range="two_months",
            )
            total_new += result.get("search_phase", {}).get("new_videos", 0)
            total_details += result.get("detail_phase", {}).get("success", 0)

        elapsed = time.time() - start_time
        logger.info(f"  完成: 新视频 {total_new}, 详情 {total_details}, 耗时 {elapsed:.1f}s")

        return {
            "keyword": keyword,
            "priority": priority,
            "status": "success",
            "new_videos": total_new,
            "details_fetched": total_details,
            "elapsed_seconds": round(elapsed, 1),
        }

    except Exception as e:
        logger.error(f"采集失败: {keyword} - {e}")
        return {
            "keyword": keyword,
            "priority": priority,
            "status": "error",
            "error": str(e),
            "elapsed_seconds": round(time.time() - start_time, 1),
        }


def daily_update(config_name: str = DEFAULT_CONFIG, max_keywords: int = None) -> Dict[str, Any]:
    """
    执行每日更新

    Args:
        config_name: 配置文件名
        max_keywords: 最大采集关键词数（用于测试）

    Returns:
        更新结果汇总
    """
    # 加载配置
    config = load_keyword_config(config_name)
    keywords = get_keywords_by_priority(config)

    if max_keywords:
        keywords = keywords[:max_keywords]

    topic = config.get("topic", "未知")

    logger.info("=" * 60)
    logger.info("每日数据更新开始")
    logger.info(f"时间: {datetime.now().isoformat()}")
    logger.info(f"主题: {topic}")
    logger.info(f"关键词数量: {len(keywords)}")
    logger.info("=" * 60)

    # 按优先级统计
    priority_counts = {}
    for kw in keywords:
        p = kw["priority"]
        priority_counts[p] = priority_counts.get(p, 0) + 1
    logger.info(f"优先级分布: {priority_counts}")

    start_time = time.time()
    collector = DataCollector()

    results = []
    success_count = 0
    fail_count = 0
    total_new = 0
    total_details = 0

    for i, kw_info in enumerate(keywords):
        keyword = kw_info["keyword"]
        priority = kw_info["priority"]
        group = kw_info["group"]

        logger.info(f"\n[{i + 1}/{len(keywords)}] {group} / {keyword}")

        result = collect_keyword(collector, keyword, priority)
        results.append(result)

        if result["status"] == "success":
            success_count += 1
            total_new += result.get("new_videos", 0)
            total_details += result.get("details_fetched", 0)
        else:
            fail_count += 1

        # 关键词之间间隔，避免请求过快
        if i < len(keywords) - 1:
            time.sleep(3)

    # 汇总
    total_elapsed = time.time() - start_time
    stats = collector.get_statistics()

    summary = {
        "update_time": datetime.now().isoformat(),
        "config": config_name,
        "topic": topic,
        "keywords_total": len(keywords),
        "keywords_success": success_count,
        "keywords_failed": fail_count,
        "total_new_videos": total_new,
        "total_details_fetched": total_details,
        "total_elapsed_seconds": round(total_elapsed, 1),
        "total_elapsed_minutes": round(total_elapsed / 60, 1),
        "database_stats": stats,
        "details": results,
    }

    logger.info("")
    logger.info("=" * 60)
    logger.info("每日更新完成")
    logger.info(f"关键词: 成功 {success_count}, 失败 {fail_count}")
    logger.info(f"新视频: {total_new}, 详情: {total_details}")
    logger.info(f"总耗时: {total_elapsed / 60:.1f} 分钟")
    logger.info(f"数据库总视频数: {stats.get('total', 0)}")
    logger.info("=" * 60)

    # 保存更新记录
    save_update_log(summary)

    return summary


def save_update_log(summary: Dict[str, Any]):
    """保存更新日志到文件"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    # 按日期保存
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"daily_update_{date_str}.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"更新日志已保存: {log_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="每日数据更新脚本")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"关键词配置文件名（默认: {DEFAULT_CONFIG}）"
    )
    parser.add_argument(
        "--max-keywords",
        type=int,
        default=None,
        help="最大采集关键词数（用于测试）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示将要执行的操作，不实际执行"
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="列出可用的配置文件"
    )

    args = parser.parse_args()

    # 列出配置文件
    if args.list_configs:
        print("可用的配置文件:")
        for f in CONFIG_DIR.glob("*.json"):
            print(f"  - {f.stem}")
        return

    # 试运行
    if args.dry_run:
        config = load_keyword_config(args.config)
        keywords = get_keywords_by_priority(config)
        if args.max_keywords:
            keywords = keywords[:args.max_keywords]

        print("=== 试运行模式 ===")
        print(f"配置文件: {args.config}")
        print(f"主题: {config.get('topic')}")
        print(f"关键词数量: {len(keywords)}")
        print("\n关键词列表:")
        for kw in keywords:
            print(f"  [{kw['priority']:6}] {kw['group']}: {kw['keyword']}")
        return

    # 确保日志目录存在
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    # 执行更新
    daily_update(config_name=args.config, max_keywords=args.max_keywords)


if __name__ == "__main__":
    main()
