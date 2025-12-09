#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调研工具命令行界面
提供简单的命令行接口进行调研
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.config import get_config
from research.real_data_collector import RealDataCollector

def main():
    parser = argparse.ArgumentParser(description='跨平台跨地区调研工具')
    parser.add_argument('category', help='调研品类')
    parser.add_argument('--regions', nargs='+', default=['US', 'SG', 'MY', 'TH', 'BR'],
                        help='目标地区列表')
    parser.add_argument('--platforms', nargs='+', default=['youtube'],
                        help='目标平台列表')
    parser.add_argument('--output', default='output/research',
                        help='输出目录')

    args = parser.parse_args()

    config = get_config()
    collector = RealDataCollector(config)

    print(f"开始调研: {args.category}")
    print(f"地区: {args.regions}")
    print(f"平台: {args.platforms}")

    # 执行调研
    results = collector.execute_real_research(
        categories=[args.category],
        regions=args.regions,
        platforms=args.platforms
    )

    print("\n调研完成！")
    print(f"结果保存在: {args.output}")

if __name__ == '__main__':
    main()
