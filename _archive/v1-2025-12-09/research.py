#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台跨地区调研工具主程序
统一的数据收集、分析和报告生成工具
"""

import argparse
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.config import get_config
from research.real_data_collector import RealDataCollector
from research.multi_platform_collector import MultiPlatformCollector
from utils.logger import setup_logger

def load_config():
    """加载配置文件"""
    config_dict = {}

    # 加载地区配置
    regions_file = Path(__file__).parent / 'config' / 'regions.yaml'
    if regions_file.exists():
        with open(regions_file, 'r', encoding='utf-8') as f:
            config_dict['regions'] = yaml.safe_load(f)

    # 加载平台配置
    platforms_file = Path(__file__).parent / 'config' / 'platforms.yaml'
    if platforms_file.exists():
        with open(platforms_file, 'r', encoding='utf-8') as f:
            config_dict['platforms'] = yaml.safe_load(f)

    return config_dict

def real_research(args):
    """执行真实数据调研"""
    logger = setup_logger('real_research')

    config = load_config()
    collector = RealDataCollector(config)

    logger.info(f"开始真实数据调研: {args.category}")

    # 使用指定的地区或配置文件中的低竞争地区
    if args.regions:
        regions = args.regions
    else:
        regions = config['regions']['groups']['low_competition']

    results = collector.execute_real_research(
        categories=[args.category],
        regions=regions,
        platforms=args.platforms or ['youtube']
    )

    logger.info("真实数据调研完成")
    return results

def multi_platform_research(args):
    """执行多平台调研"""
    logger = setup_logger('multi_platform_research')

    config = load_config()
    collector = MultiPlatformCollector(config)

    logger.info(f"开始多平台调研: {args.category}")

    # 使用指定的地区或配置文件中的所有地区
    if args.regions:
        regions = args.regions
    else:
        regions = list(config['regions']['regions'].keys())[:10]  # 默认前10个地区

    results = collector.execute_full_research(
        query=args.category,
        regions=regions,
        platforms=args.platforms or ['youtube', 'tiktok']
    )

    logger.info("多平台调研完成")
    return results

def main():
    parser = argparse.ArgumentParser(description='跨平台跨地区调研工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 真实数据调研命令
    real_parser = subparsers.add_parser('real', help='真实数据调研')
    real_parser.add_argument('category', help='调研品类')
    real_parser.add_argument('--regions', nargs='+', help='目标地区列表')
    real_parser.add_argument('--platforms', nargs='+', default=['youtube'],
                            help='目标平台列表')
    real_parser.add_argument('--output', default='output/real_research',
                            help='输出目录')

    # 多平台调研命令
    multi_parser = subparsers.add_parser('multi', help='多平台调研')
    multi_parser.add_argument('category', help='调研品类')
    multi_parser.add_argument('--regions', nargs='+', help='目标地区列表')
    multi_parser.add_argument('--platforms', nargs='+',
                            default=['youtube', 'tiktok'], help='目标平台列表')
    multi_parser.add_argument('--output', default='output/multi_platform',
                            help='输出目录')

    # 列出可用地区
    regions_parser = subparsers.add_parser('regions', help='列出可用地区')
    regions_parser.add_argument('--group', help='地区分组')

    # 列出可用平台
    platforms_parser = subparsers.add_parser('platforms', help='列出可用平台')
    platforms_parser.add_argument('--group', help='平台分组')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'regions':
        config = load_config()
        if args.group:
            regions = config['regions']['groups'].get(args.group, [])
            print(f"地区分组 {args.group}:")
            for region in regions:
                region_info = config['regions']['regions'].get(region, {})
                print(f"  {region}: {region_info.get('name', '')}")
        else:
            print("所有地区:")
            for region, info in config['regions']['regions'].items():
                print(f"  {region}: {info.get('name', '')} ({info.get('competition_level', 'unknown')})")

    elif args.command == 'platforms':
        config = load_config()
        if args.group:
            platforms = config['platforms']['groups'].get(args.group, [])
            print(f"平台分组 {args.group}:")
            for platform in platforms:
                platform_info = config['platforms']['platforms'].get(platform, {})
                print(f"  {platform}: {platform_info.get('name', '')}")
        else:
            print("所有平台:")
            for platform, info in config['platforms']['platforms'].items():
                print(f"  {platform}: {info.get('name', '')}")

    elif args.command == 'real':
        results = real_research(args)
        print(f"\n调研完成！结果保存在: {args.output}")

    elif args.command == 'multi':
        results = multi_platform_research(args)
        print(f"\n调研完成！结果保存在: {args.output}")

if __name__ == '__main__':
    main()
