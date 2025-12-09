#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据调研示例
基于实际MCP调用收集数据，分析真实竞争度
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import setup_logger
from utils.config import get_config
from research.real_data_collector import RealDataCollector

def main():
    """
    演示真实数据调研功能
    """
    logger = setup_logger('real_research')
    logger.info("=" * 60)
    logger.info("YouTube视频研究工作流 - 真实数据调研示例")
    logger.info("=" * 60)

    print("\n⚠️  重要说明：")
    print("本工具需要您在Claude Code中实际调用MCP工具来收集数据")
    print("以下是实际调研步骤：\n")

    # 初始化配置和收集器
    config = get_config()
    collector = RealDataCollector(config)

    # 定义调研品类
    categories = [
        'Python教程',
        'JavaScript学习',
        'AI人工智能',
        '数据分析',
        '机器学习',
        'Web开发',
        '游戏开发',
        '摄影教程',
        '烹饪教学',
        '健身指导'
    ]

    # 定义目标地区
    regions = [
        'US',    # 美国
        'CN',    # 中国大陆
        'JP',    # 日本
        'KR',    # 韩国
        'TW',    # 台湾
        'SG',    # 新加坡
        'MY',    # 马来西亚
        'TH',    # 泰国
        'VN',    # 越南
        'IN',    # 印度
        'GB',    # 英国
        'DE',    # 德国
        'BR',    # 巴西
        'MX',    # 墨西哥
        'CA',    # 加拿大
        'AU'     # 澳大利亚
    ]

    # 定义目标平台
    platforms = ['youtube', 'tiktok', 'facebook', 'instagram']

    print(f"📋 调研计划:")
    print(f"  品类数量: {len(categories)}")
    print(f"  地区数量: {len(regions)}")
    print(f"  平台数量: {len(platforms)}")
    print(f"  总调研组合: {len(categories) * len(regions) * len(platforms)}")

    print("\n" + "=" * 60)
    print("实际调研步骤（需要在Claude Code中执行）")
    print("=" * 60)

    # 演示一个完整的调研流程
    example_category = "Python教程"
    example_regions = ['US', 'SG', 'MY', 'TH', 'BR']

    print(f"\n🔍 以 '{example_category}' 为例，调研地区: {', '.join(example_regions)}")
    print("\n📝 步骤1: 在Claude Code中执行以下MCP命令:\n")

    for region in example_regions:
        print(f"🌍 地区 {region}:")
        commands = collector._generate_mcp_commands(example_category, region, 'youtube')
        for cmd in commands:
            print(f"  {cmd}")
        print()

    print("\n📊 步骤2: 分析收集到的数据")
    print("  系统将基于以下指标分析竞争度:")
    print("  - 观看量分析（平均观看量）")
    print("  - 频道分析（独特频道数量）")
    print("  - 时效性分析（近期发布比例）")
    print("  - 综合评分（1-3分，3分最高）")

    print("\n📈 步骤3: 查看分析结果")
    print("  结果将保存在 output/real_research/ 目录下")

    print("\n" + "=" * 60)
    print("如何判断竞争度？")
    print("=" * 60)

    print("\n🎯 观看量分析:")
    print("  - 高竞争: 平均观看量 ≥ 100万")
    print("  - 中等竞争: 平均观看量 10万-100万")
    print("  - 低竞争: 平均观看量 < 10万")

    print("\n👥 频道分析:")
    print("  - 高竞争: 独特频道数量 > 15")
    print("  - 中等竞争: 独特频道数量 5-15")
    print("  - 低竞争: 独特频道数量 < 5")

    print("\n⏰ 时效性分析:")
    print("  - 高竞争: 近期发布视频比例 ≥ 70%")
    print("  - 中等竞争: 近期发布视频比例 40-70%")
    print("  - 低竞争: 近期发布视频比例 < 40%")

    print("\n" + "=" * 60)
    print("实际执行调研")
    print("=" * 60)

    print("\n💡 如果您已经在Claude Code中收集了数据，可以运行:")
    print("  python3 src/research/real_data_collector.py")

    print("\n💡 或者修改categories、regions列表，然后运行:")
    print("  python3 examples/real_research.py")

    print("\n📝 示例代码:")
    print("""
# 修改 categories 列表，添加您的研究品类
categories = [
    '您的品类1',
    '您的品类2',
    '您的品类3'
]

# 修改 regions 列表，选择您关注的地区
regions = [
    'SG',    # 新加坡
    'MY',    # 马来西亚
    'TH',    # 泰国
    'VN',    # 越南
    'BR'     # 巴西
]

# 执行调研
collector = RealDataCollector(config)
results = collector.execute_real_research(categories, regions, ['youtube'])
""")

    print("\n" + "=" * 60)
    print("✅ 真实数据调研指南完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
