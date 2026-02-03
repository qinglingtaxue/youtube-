#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速调研工具
简化版调研工具，可以快速分析单个品类的跨地区竞争情况
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import setup_logger
from utils.config import get_config
from research.real_data_collector import RealDataCollector

def quick_research(category: str, regions: List[str] = None):
    """
    快速调研单个品类的竞争情况

    Args:
        category: 调研品类
        regions: 目标地区列表
    """
    logger = setup_logger('quick_research')

    if regions is None:
        regions = ['US', 'SG', 'MY', 'TH', 'VN', 'BR', 'MX', 'IN', 'JP', 'KR']

    config = get_config()
    collector = RealDataCollector(config)

    logger.info(f"开始快速调研: {category}")
    logger.info(f"目标地区: {regions}")

    results = {}

    for region in regions:
        logger.info(f"\n🔍 调研 {category} 在 {region} 的竞争情况...")

        # 生成MCP调用命令
        commands = collector._generate_mcp_commands(category, region, 'youtube')
        logger.info("请在Claude Code中执行:")
        for cmd in commands:
            logger.info(f"  {cmd}")

        # 等待用户输入MCP返回的数据
        print(f"\n📝 请在Claude Code中执行上述命令，然后将结果输入到这里:")
        print(f"   (输入 'skip' 跳过此地区，'quit' 退出)")
        user_input = input(f"   {region} 的MCP返回数据: ").strip()

        if user_input.lower() == 'quit':
            logger.info("用户退出调研")
            break
        elif user_input.lower() == 'skip':
            logger.info(f"跳过 {region}")
            continue

        # 解析用户输入的数据（简化版，实际使用时应该解析HTML）
        # 这里只是一个占位符
        result = {
            'region': region,
            'category': category,
            'timestamp': '2025-12-09',
            'competition': 'pending'  # 待分析
        }

        results[region] = result

    # 生成简单报告
    generate_quick_report(category, results)

def generate_quick_report(category: str, results: Dict[str, Any]):
    """生成快速报告"""
    output_dir = Path('output/quick_research')
    output_dir.mkdir(parents=True, exist_ok=True)

    report = f"# {category} - 快速调研报告\n\n"
    report += f"调研时间: 2025-12-09\n\n"

    report += "## 调研结果\n\n"
    for region, result in results.items():
        report += f"### {region}\n"
        report += f"- 状态: {result.get('status', '待调研')}\n"
        report += f"- 竞争度: {result.get('competition', '待分析')}\n\n"

    report_file = output_dir / f'{category}_quick_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📁 报告已保存: {report_file}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        category = sys.argv[1]
    else:
        category = input("请输入调研品类: ").strip()

    quick_research(category)
