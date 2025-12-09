#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台跨地区调研示例
演示如何收集YouTube、TikTok、Facebook、Instagram等多平台数据
以及如何找出信息差和竞争少的领域
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import setup_logger
from utils.config import get_config
from research.multi_platform_collector import MultiPlatformCollector

def main():
    """
    演示多平台跨地区调研功能
    """
    logger = setup_logger('multi_platform_research')
    logger.info("=" * 60)
    logger.info("YouTube视频研究工作流 - 多平台跨地区调研示例")
    logger.info("=" * 60)

    # 初始化配置和收集器
    config = get_config()
    collector = MultiPlatformCollector(config)

    # 定义研究关键词
    keywords = [
        'Python教程',
        'JavaScript学习',
        'AI人工智能',
        'ChatGPT使用',
        '数据分析',
        '机器学习',
        '编程入门',
        'Web开发'
    ]

    # 定义目标地区
    target_regions = [
        'US',    # 美国 - 竞争激烈
        'CN',    # 中国大陆 - 竞争激烈
        'JP',    # 日本 - 中等竞争
        'KR',    # 韩国 - 中等竞争
        'TW',    # 台湾 - 中等竞争
        'HK',    # 香港 - 中等竞争
        'SG',    # 新加坡 - 低竞争
        'MY',    # 马来西亚 - 低竞争
        'TH',    # 泰国 - 低竞争
        'VN',    # 越南 - 低竞争
        'IN',    # 印度 - 中等竞争
        'GB',    # 英国 - 中等竞争
        'DE',    # 德国 - 中等竞争
        'FR',    # 法国 - 中等竞争
        'BR',    # 巴西 - 低竞争
        'MX',    # 墨西哥 - 低竞争
        'CA',    # 加拿大 - 中等竞争
        'AU'     # 澳大利亚 - 中等竞争
    ]

    # 定义目标平台
    target_platforms = [
        'youtube',
        'tiktok',
        'facebook',
        'instagram'
    ]

    logger.info(f"\n📋 研究计划:")
    logger.info(f"  关键词数量: {len(keywords)}")
    logger.info(f"  目标地区: {len(target_regions)}个")
    logger.info(f"  目标平台: {len(target_platforms)}个")

    # 执行调研
    all_results = {}
    for keyword in keywords:
        logger.info(f"\n🔍 开始调研关键词: {keyword}")

        try:
            result = collector.execute_full_research(
                query=keyword,
                regions=target_regions,
                platforms=target_platforms
            )

            all_results[keyword] = result

            logger.info(f"✅ {keyword} 调研完成")
            logger.info(f"   发现 {len(result['gap_analysis']['low_competition_regions'])} 个低竞争机会")
            logger.info(f"   发现 {len(result['gap_analysis']['cross_platform_gaps'])} 个跨平台空白")

        except Exception as e:
            logger.error(f"❌ {keyword} 调研失败: {e}")
            continue

    # 生成综合报告
    logger.info(f"\n📊 生成综合分析报告...")
    generate_comprehensive_report(all_results)

    logger.info("\n" + "=" * 60)
    logger.info("✅ 多平台跨地区调研示例执行完成！")
    logger.info("=" * 60)

def generate_comprehensive_report(results: dict):
    """生成综合分析报告"""
    from utils.file_utils import ensure_dir, write_text
    from datetime import datetime

    output_dir = Path('output/multi_platform_research')
    ensure_dir(output_dir)

    report = "# 多平台跨地区机会分析 - 综合报告\n\n"
    report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # 汇总所有低竞争机会
    report += "## 🎯 汇总低竞争机会\n\n"

    all_low_comp = []
    all_cross_gaps = []

    for keyword, result in results.items():
        gap_analysis = result['gap_analysis']
        all_low_comp.extend(gap_analysis['low_competition_regions'])
        all_cross_gaps.extend(gap_analysis['cross_platform_gaps'])

    # 按平台分组低竞争机会
    by_platform = {}
    for gap in all_low_comp:
        platform = gap['platform']
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(gap)

    for platform, gaps in by_platform.items():
        report += f"### {platform.title()}\n"
        report += f"发现 {len(gaps)} 个低竞争机会:\n\n"

        # 排序并显示前10个
        sorted_gaps = sorted(gaps, key=lambda x: x['opportunity_score'], reverse=True)[:10]
        for gap in sorted_gaps:
            report += f"- **{', '.join(gap['regions'])}** (机会评分: {gap['opportunity_score']:.2f})\n"
        report += "\n"

    # 跨平台空白汇总
    report += "## 🔍 汇总跨平台空白\n\n"
    report += f"共发现 {len(all_cross_gaps)} 个跨平台空白机会:\n\n"

    # 按地区分组
    by_region = {}
    for gap in all_cross_gaps:
        region = gap['region']
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(gap)

    for region, gaps in by_region.items():
        report += f"### {region}\n"
        missing_platforms = set()
        for gap in gaps:
            missing_platforms.update(gap['missing_platforms'])
        report += f"- **缺失平台**: {', '.join(missing_platforms)}\n"
        report += f"- **机会**: 该地区在某些平台存在空白，建议优先布局\n\n"

    # 最佳机会推荐
    report += "## 🏆 最佳机会推荐\n\n"

    # 找出评分最高的低竞争地区
    best_opportunities = []
    for gap in all_low_comp:
        if gap['opportunity_score'] > 1.0:  # 评分大于1认为是好机会
            best_opportunities.append(gap)

    best_opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)

    report += "### Top 10 低竞争地区机会\n"
    for i, opp in enumerate(best_opportunities[:10], 1):
        report += f"{i}. **{opp['platform'].title()}** - {', '.join(opp['regions'])} "
        report += f"(评分: {opp['opportunity_score']:.2f})\n"

    # 跨平台最佳机会
    cross_platform_best = []
    for region, gaps in by_region.items():
        if len(gaps) >= 2:  # 至少缺失2个平台
            cross_platform_best.append((region, len(gaps)))

    cross_platform_best.sort(key=lambda x: x[1], reverse=True)

    report += "\n### Top 10 跨平台空白机会\n"
    for i, (region, count) in enumerate(cross_platform_best[:10], 1):
        report += f"{i}. **{region}** (缺失 {count} 个平台)\n"

    # 行动建议
    report += "\n## 🚀 行动建议\n\n"

    report += "### 优先级排序\n"
    report += "1. **第一阶段** (1-2个月): 专注于2-3个低竞争地区的YouTube和TikTok\n"
    report += "2. **第二阶段** (3-4个月): 扩展到Facebook和Instagram\n"
    report += "3. **第三阶段** (5-6个月): 进入中高竞争地区，提升内容质量\n\n"

    report += "### 具体执行步骤\n"
    report += "1. **选定目标**: 从Top 10中选择2-3个最匹配你能力的机会\n"
    report += "2. **本地化策略**: 为选定地区制定本地化内容策略\n"
    report += "3. **多平台布局**: 优先在竞争较少的平台发布\n"
    report += "4. **监控调整**: 持续监控竞争对手，适时调整策略\n\n"

    report += "### 注意事项\n"
    report += "- 重视内容质量和本地化\n"
    report += "- 遵守各平台规则和政策\n"
    report += "- 关注文化差异和用户习惯\n"
    report += "- 准备多语言内容支持\n\n"

    # 保存报告
    report_file = output_dir / 'comprehensive_opportunity_report.md'
    write_text(report_file, report)

    print(f"\n📁 综合报告已生成: {report_file}")

if __name__ == '__main__':
    main()
