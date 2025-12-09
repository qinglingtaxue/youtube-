#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量分析示例
演示如何批量分析多个关键词的YouTube视频
"""

import sys
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import setup_logger
from utils.config import get_config
from utils.file_utils import ensure_dir, write_json
from research.data_collector import DataCollector
from analysis.pattern_analyzer import PatternAnalyzer

def batch_analyze_keywords(keywords: List[str], max_videos_per_keyword: int = 20) -> Dict[str, Any]:
    """
    批量分析多个关键词

    Args:
        keywords: 关键词列表
        max_videos_per_keyword: 每个关键词最大视频数

    Returns:
        汇总分析结果
    """
    logger = setup_logger('batch_analysis')
    logger.info(f"开始批量分析 {len(keywords)} 个关键词")

    config = get_config()
    collector = DataCollector(config)
    analyzer = PatternAnalyzer(config)

    all_videos = []
    keyword_results = {}

    # 并发收集每个关键词的数据
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_keyword = {
            executor.submit(collector.search_videos, keyword, max_videos_per_keyword, 'viewCount'): keyword
            for keyword in keywords
        }

        for future in as_completed(future_to_keyword):
            keyword = future_to_keyword[future]
            try:
                videos = future.result()
                all_videos.extend(videos)
                keyword_results[keyword] = {
                    'count': len(videos),
                    'videos': videos[:5]  # 只保存前5个作为示例
                }
                logger.info(f"关键词 '{keyword}': 收集到 {len(videos)} 个视频")
            except Exception as e:
                logger.error(f"关键词 '{keyword}' 收集失败: {e}")
                keyword_results[keyword] = {'error': str(e)}

    logger.info(f"总共收集到 {len(all_videos)} 个视频")

    # 整体模式分析
    logger.info("进行整体模式分析...")
    patterns = analyzer.analyze_videos(all_videos)

    # 生成汇总报告
    summary = {
        'total_videos': len(all_videos),
        'keywords_analyzed': len(keywords),
        'successful_keywords': sum(1 for r in keyword_results.values() if 'error' not in r),
        'failed_keywords': sum(1 for r in keyword_results.values() if 'error' in r),
        'keyword_results': keyword_results,
        'overall_patterns': patterns,
        'top_patterns': patterns[:10],
        'statistics': {
            'total_views': sum(v.get('view_count', 0) for v in all_videos),
            'avg_views': sum(v.get('view_count', 0) for v in all_videos) / len(all_videos) if all_videos else 0,
            'unique_channels': len(set(v.get('channel', '') for v in all_videos))
        }
    }

    return summary

def analyze_by_category():
    """
    按类别批量分析示例
    """
    logger = setup_logger('category_analysis')
    logger.info("=" * 60)
    logger.info("YouTube视频研究工作流 - 分类批量分析")
    logger.info("=" * 60)

    # 定义不同类别的关键词
    categories = {
        '编程教学': ['Python教程', 'JavaScript教程', '编程入门', '代码教学'],
        '生活技能': ['生活技巧', '日常妙招', '实用方法', '技能分享'],
        '商业创业': ['创业经验', '商业思维', '营销策略', '副业赚钱'],
        '学习教育': ['学习方法', '知识分享', '技能提升', '读书分享']
    }

    results = {}
    output_dir = Path('output/batch_analysis')
    ensure_dir(output_dir)

    for category, keywords in categories.items():
        logger.info(f"\n📂 分析类别: {category}")
        logger.info(f"关键词: {', '.join(keywords)}")

        try:
            result = batch_analyze_keywords(keywords, max_videos_per_keyword=15)
            results[category] = result

            # 保存每个类别的详细结果
            category_file = output_dir / f'{category}_analysis.json'
            write_json(category_file, result)
            logger.info(f"结果已保存: {category_file}")

            # 显示关键统计
            stats = result['statistics']
            logger.info(f"  - 总视频数: {result['total_videos']}")
            logger.info(f"  - 总观看数: {stats['total_views']:,}")
            logger.info(f"  - 平均观看数: {stats['avg_views']:,.0f}")
            logger.info(f"  - 发现模式: {len(result['patterns'])}个")

        except Exception as e:
            logger.error(f"类别 '{category}' 分析失败: {e}")
            results[category] = {'error': str(e)}

    # 生成汇总报告
    logger.info("\n📊 生成汇总报告...")
    generate_batch_summary_report(results, output_dir)

    logger.info("\n" + "=" * 60)
    logger.info("✅ 批量分析完成！")
    logger.info("=" * 60)
    logger.info(f"\n📁 所有结果保存在: {output_dir}")

def generate_batch_summary_report(results: Dict[str, Any], output_dir: Path):
    """
    生成批量分析的汇总报告

    Args:
        results: 批量分析结果
        output_dir: 输出目录
    """
    logger = setup_logger('summary_report')

    report_lines = [
        "# YouTube视频批量分析汇总报告",
        "",
        f"**生成时间**: {Path().cwd()}",
        f"**分析类别数**: {len(results)}",
        "",
        "## 各类别分析结果",
        ""
    ]

    total_videos = 0
    total_views = 0
    all_patterns = []

    for category, result in results.items():
        if 'error' in result:
            report_lines.extend([
                f"### ❌ {category}",
                f"**状态**: 分析失败",
                f"**错误**: {result['error']}",
                ""
            ])
            continue

        stats = result['statistics']
        total_videos += result['total_videos']
        total_views += stats['total_views']
        all_patterns.extend(result['overall_patterns'])

        report_lines.extend([
            f"### ✅ {category}",
            f"- **视频数量**: {result['total_videos']}",
            f"- **总观看数**: {stats['total_views']:,}",
            f"- **平均观看数**: {stats['avg_views']:,.0f}",
            f"- **独立频道数**: {stats['unique_channels']}",
            f"- **发现模式数**: {len(result['patterns'])}",
            f"- **成功关键词**: {result['successful_keywords']}/{result['keywords_analyzed']}",
            ""
        ])

    # 整体统计
    report_lines.extend([
        "## 整体统计",
        "",
        f"- **总视频数**: {total_videos:,}",
        f"- **总观看数**: {total_views:,}",
        f"- **平均观看数**: {total_views/total_videos:,.0f}" if total_videos > 0 else "- **平均观看数**: 0",
        ""
    ])

    # 跨类别模式分析
    if all_patterns:
        # 按频率排序
        sorted_patterns = sorted(all_patterns, key=lambda x: x['frequency'], reverse=True)
        top_cross_patterns = sorted_patterns[:20]

        report_lines.extend([
            "## 跨类别热门模式 (TOP 20)",
            ""
        ])

        for i, pattern in enumerate(top_cross_patterns, 1):
            report_lines.extend([
                f"### {i}. {pattern['name']}",
                f"- **出现频率**: {pattern['frequency']}次",
                f"- **置信度**: {pattern.get('confidence', 0):.2f}",
                f"- **描述**: {pattern.get('description', 'N/A')}",
                ""
            ])

    # 保存报告
    summary_file = output_dir / 'batch_summary_report.md'
    report_content = '\n'.join(report_lines)

    from utils.file_utils import write_text
    write_text(summary_file, report_content)
    logger.info(f"汇总报告已生成: {summary_file}")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("YouTube视频研究工作流 - 批量分析")
    print("=" * 60)
    print("\n本示例将:")
    print("1. 按类别批量分析多个关键词")
    print("2. 并发收集和分析视频数据")
    print("3. 生成跨类别模式对比")
    print("4. 输出详细的分析报告")
    print("\n开始执行...\n")

    try:
        analyze_by_category()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
    except Exception as e:
        print(f"\n\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
