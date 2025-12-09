#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube视频创作工作流 - 主程序
实现三事件最小故事框架：
事件1：调研分析 → 产出典型案例 + 模式总结
事件2：模式抽象 → 生成创作模板
事件3：实战应用 → 输出创作文案
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from research.data_collector import DataCollector
from analysis.pattern_analyzer import PatternAnalyzer
from template.template_generator import TemplateGenerator
from workflow.workflow_manager import WorkflowManager
from utils.logger import setup_logger

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='YouTube视频创作工作流')
    parser.add_argument('--theme', type=str, required=True, 
                       help='调研主题，例如：老人养生')
    parser.add_argument('--output-dir', type=str, default='./output',
                       help='输出目录')
    parser.add_argument('--max-videos', type=int, default=1000,
                       help='最大视频数量')
    parser.add_argument('--max-cases', type=int, default=10,
                       help='精选案例数量')
    parser.add_argument('--time-limit', type=int, default=120,
                       help='时间限制（分钟）')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger()
    logger.info(f"开始执行YouTube视频创作工作流，主题：{args.theme}")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 执行三事件最小故事工作流
    workflow = WorkflowManager(
        theme=args.theme,
        output_dir=output_dir,
        max_videos=args.max_videos,
        max_cases=args.max_cases,
        time_limit=args.time_limit,
        logger=logger
    )
    
    try:
        result = workflow.execute()
        
        # 输出结果摘要
        print("\n" + "="*60)
        print(f"🎉 工作流执行完成！")
        print(f"📊 调研主题：{args.theme}")
        print(f"📁 输出目录：{output_dir}")
        print(f"⏱️  总耗时：{result['total_time']:.1f}分钟")
        print(f"📹 收集视频：{result['videos_collected']}个")
        print(f"🎯 精选案例：{result['cases_selected']}个")
        print(f"📝 识别模式：{result['patterns_found']}个")
        print(f"📄 生成模板：{result['templates_generated']}个")
        print(f"✍️ 创作文案：{result['scripts_created']}个")
        print("="*60 + "\n")
        
        return result
        
    except Exception as e:
        logger.error(f"工作流执行失败：{str(e)}")
        print(f"❌ 执行失败：{str(e)}")
        return None

if __name__ == '__main__':
    result = main()
    sys.exit(0 if result else 1)
