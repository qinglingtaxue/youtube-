#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube视频研究工作流 - 统一启动脚本
提供简单的命令行界面来执行各种功能
"""

import sys
import argparse
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.logger import setup_logger, get_default_log_file
from utils.config import get_config
from workflow.workflow_manager import WorkflowManager

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description='YouTube视频研究工作流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python3 run.py quick          # 运行快速开始示例
  python3 run.py custom         # 运行自定义分析示例
  python3 run.py batch          # 运行批量分析示例
  python3 run.py mcp            # 运行MCP集成示例
  python3 run.py workflow --keywords "教程,教学,学习"  # 执行完整工作流
        """
    )

    parser.add_argument(
        'command',
        choices=['quick', 'custom', 'batch', 'mcp', 'workflow', 'help'],
        help='要执行的命令'
    )

    parser.add_argument(
        '--keywords',
        type=str,
        help='工作流关键词（用逗号分隔）'
    )

    parser.add_argument(
        '--max-videos',
        type=int,
        default=20,
        help='每个关键词最大视频数（默认: 20）'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/custom_run',
        help='输出目录（默认: output/custom_run）'
    )

    args = parser.parse_args()

    # 显示帮助
    if args.command == 'help':
        parser.print_help()
        return

    print("\n" + "=" * 60)
    print("YouTube视频研究工作流 - 启动器")
    print("=" * 60)

    # 初始化日志
    logger = setup_logger('runner')
    log_file = get_default_log_file()
    print(f"\n📝 日志文件: {log_file}")

    # 初始化配置
    config = get_config()
    print(f"⚙️  配置文件: {config.config_path or '默认配置'}")

    try:
        if args.command == 'quick':
            print("\n🚀 运行快速开始示例...")
            from examples.quick_start import quick_start_example
            quick_start_example()

        elif args.command == 'custom':
            print("\n🔧 运行自定义分析示例...")
            from examples.custom_analysis import custom_analysis_example
            custom_analysis_example()

        elif args.command == 'batch':
            print("\n📦 运行批量分析示例...")
            from examples.batch_analysis import analyze_by_category
            analyze_by_category()

        elif args.command == 'mcp':
            print("\n🔌 运行MCP集成示例...")
            from examples.mcp_integration import main as mcp_main
            mcp_main()

        elif args.command == 'workflow':
            if not args.keywords:
                print("\n❌ 错误: 工作流模式需要指定 --keywords 参数")
                print("   示例: python3 run.py workflow --keywords '教程,教学,学习'")
                return

            keywords = [k.strip() for k in args.keywords.split(',')]
            print(f"\n⚡ 执行完整工作流...")
            print(f"   关键词: {', '.join(keywords)}")
            print(f"   最大视频数: {args.max_videos}")

            # 初始化工作流管理器
            workflow = WorkflowManager(config)

            # 执行完整工作流
            result = workflow.execute_full_workflow(
                keywords=keywords,
                max_videos_per_keyword=args.max_videos,
                output_dir=args.output_dir
            )

            print(f"\n✅ 工作流执行完成!")
            print(f"   输出目录: {args.output_dir}")

        print("\n" + "=" * 60)
        print("✅ 执行完成!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
    except Exception as e:
        print(f"\n\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"执行失败: {e}", exc_info=True)

if __name__ == '__main__':
    main()
