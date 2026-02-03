#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多领域批量采集脚本
一键采集多个领域的 YouTube 视频数据，用于跨领域规律验证

预设领域：
- 科技: AI教程、编程入门、数码评测
- 美食: 家常菜、烘焙教程、探店
- 旅行: 自驾游、穷游攻略、签证
- 理财: 基金入门、股票分析、副业
- 游戏: 游戏攻略、直播、电竞

使用方法:
    python scripts/collect_multi_domain.py                    # 采集所有预设领域
    python scripts/collect_multi_domain.py --domains 科技 美食  # 只采集指定领域
    python scripts/collect_multi_domain.py --target 300       # 每领域目标300条
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.data_collector import DataCollector

# 预设领域及关键词
DOMAIN_KEYWORDS = {
    "科技": {
        "keywords": ["AI教程", "编程入门", "Python教程", "数码评测", "手机测评", "ChatGPT", "人工智能"],
        "description": "科技/编程/AI相关",
    },
    "美食": {
        "keywords": ["家常菜", "烘焙教程", "探店", "美食制作", "食谱", "料理", "甜点"],
        "description": "美食烹饪相关",
    },
    "旅行": {
        "keywords": ["自驾游", "穷游攻略", "签证", "旅行vlog", "酒店", "机票", "旅游攻略"],
        "description": "旅行/出行相关",
    },
    "理财": {
        "keywords": ["基金入门", "股票分析", "副业", "理财", "投资", "被动收入", "财务自由"],
        "description": "理财/投资相关",
    },
    "游戏": {
        "keywords": ["游戏攻略", "直播", "电竞", "原神", "王者荣耀", "游戏解说"],
        "description": "游戏/电竞相关",
    },
    "健身": {
        "keywords": ["健身教程", "减肥", "增肌", "瑜伽", "有氧运动", "居家健身"],
        "description": "健身/运动相关",
    },
    "教育": {
        "keywords": ["英语学习", "考研", "职场", "自我提升", "学习方法", "知识分享"],
        "description": "教育/学习相关",
    },
}


def collect_domain(collector: DataCollector, domain: str, config: dict, target: int) -> dict:
    """
    采集单个领域的数据

    Args:
        collector: 数据采集器
        domain: 领域名称
        config: 领域配置（关键词等）
        target: 目标采集数量

    Returns:
        采集结果统计
    """
    print(f"\n{'='*60}")
    print(f"开始采集: {domain} ({config['description']})")
    print(f"关键词: {', '.join(config['keywords'][:5])}...")
    print(f"目标数量: {target}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        result = collector.collect_large_scale(
            theme=domain,
            target_count=target,
            detail_min_views=10000,
            detail_limit=50,
            time_range="month",
        )

        elapsed = time.time() - start_time

        return {
            "domain": domain,
            "status": "success",
            "new_videos": result.get("new_videos", 0),
            "total_found": result.get("total_found", 0),
            "details_enriched": result.get("details_enriched", 0),
            "elapsed": elapsed,
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"错误: {e}")
        return {
            "domain": domain,
            "status": "error",
            "error": str(e),
            "elapsed": elapsed,
        }


def main():
    parser = argparse.ArgumentParser(description="多领域批量采集")
    parser.add_argument("--domains", nargs="+", default=None,
                        help="指定采集的领域（默认全部）")
    parser.add_argument("--target", type=int, default=500,
                        help="每领域目标数量（默认 500）")
    parser.add_argument("--list", action="store_true",
                        help="列出所有可用领域")
    args = parser.parse_args()

    # 列出领域
    if args.list:
        print("可用领域:")
        for domain, config in DOMAIN_KEYWORDS.items():
            print(f"  {domain}: {config['description']}")
            print(f"    关键词: {', '.join(config['keywords'])}")
        return

    # 确定要采集的领域
    if args.domains:
        domains = []
        for d in args.domains:
            if d in DOMAIN_KEYWORDS:
                domains.append(d)
            else:
                print(f"警告: 未知领域 '{d}'，已跳过")
        if not domains:
            print("错误: 没有有效的领域")
            return
    else:
        domains = list(DOMAIN_KEYWORDS.keys())

    print("=" * 70)
    print("多领域批量采集")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\n待采集领域: {len(domains)} 个")
    print(f"领域列表: {', '.join(domains)}")
    print(f"每领域目标: {args.target} 条")
    print(f"预计总量: {len(domains) * args.target} 条")

    # 初始化采集器
    collector = DataCollector()

    # 为每个领域设置关键词
    for domain, config in DOMAIN_KEYWORDS.items():
        # 注册关键词映射
        if hasattr(collector, 'keyword_mappings'):
            collector.keyword_mappings[domain] = config['keywords']

    # 采集结果
    results = []
    total_start = time.time()

    for i, domain in enumerate(domains):
        print(f"\n[{i+1}/{len(domains)}] 正在采集: {domain}")

        config = DOMAIN_KEYWORDS[domain]
        result = collect_domain(collector, domain, config, args.target)
        results.append(result)

        # 领域间休息
        if i < len(domains) - 1:
            print("\n休息 10 秒...")
            time.sleep(10)

    total_elapsed = time.time() - total_start

    # 输出总结
    print("\n" + "=" * 70)
    print("采集完成汇总")
    print("=" * 70)
    print(f"\n{'领域':<10} {'状态':<8} {'新视频':<10} {'总发现':<10} {'详情':<10} {'耗时'}")
    print("-" * 70)

    total_new = 0
    total_found = 0
    total_details = 0
    success_count = 0

    for r in results:
        if r["status"] == "success":
            success_count += 1
            new = r.get("new_videos", 0)
            found = r.get("total_found", 0)
            details = r.get("details_enriched", 0)
            total_new += new
            total_found += found
            total_details += details
            print(f"{r['domain']:<10} {'✓':<8} {new:<10} {found:<10} {details:<10} {r['elapsed']/60:.1f}分钟")
        else:
            print(f"{r['domain']:<10} {'✗':<8} {'-':<10} {'-':<10} {'-':<10} {r['elapsed']/60:.1f}分钟")

    print("-" * 70)
    print(f"{'合计':<10} {success_count}/{len(domains):<6} {total_new:<10} {total_found:<10} {total_details:<10} {total_elapsed/60:.1f}分钟")
    print("=" * 70)

    # 输出下一步建议
    print("\n下一步:")
    print("  1. 查看数据: sqlite3 data/youtube_pipeline.db \"SELECT theme, COUNT(*) FROM competitor_videos GROUP BY theme\"")
    print("  2. 补全详情: python scripts/enrich_all_videos.py")
    print("  3. 更新分析: 重新运行模式洞察分析")


if __name__ == "__main__":
    main()
