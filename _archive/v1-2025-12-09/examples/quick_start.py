#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速开始示例
演示如何使用YouTube视频研究工作流的基本功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import setup_logger, get_default_log_file
from utils.config import get_config
from utils.file_utils import ensure_dir, write_text
from research.data_collector import DataCollector
from analysis.pattern_analyzer import PatternAnalyzer
from workflow.workflow_manager import WorkflowManager

def quick_start_example():
    """
    快速开始示例
    演示三事件工作流的完整流程
    """
    logger = setup_logger('quick_start')
    logger.info("=" * 60)
    logger.info("YouTube视频研究工作流 - 快速开始示例")
    logger.info("=" * 60)

    # 步骤1：配置初始化
    logger.info("\n📋 步骤1：配置初始化")
    config = get_config()
    logger.info(f"配置文件加载完成: {config.config_path or '默认配置'}")

    # 设置日志文件
    log_file = get_default_log_file()
    ensure_dir(Path(log_file).parent)
    logger.info(f"日志文件: {log_file}")

    # 步骤2：事件1 - 数据收集
    logger.info("\n🔍 步骤2：事件1 - 数据收集")
    logger.info("正在收集YouTube视频数据...")

    try:
        # 初始化数据收集器
        collector = DataCollector(config)

        # 搜索关键词
        keywords = ['教程', '教学', '学习']
        video_data = []

        for keyword in keywords:
            logger.info(f"搜索关键词: {keyword}")
            videos = collector.search_videos(
                query=keyword,
                max_results=10,  # 限制数量以便快速演示
                order='viewCount'
            )
            video_data.extend(videos)
            logger.info(f"找到 {len(videos)} 个视频")

        logger.info(f"总共收集到 {len(video_data)} 个视频")

        # 保存原始数据
        output_dir = Path('output/quick_start')
        ensure_dir(output_dir)

        raw_data_file = output_dir / 'raw_videos.json'
        import json
        with open(raw_data_file, 'w', encoding='utf-8') as f:
            json.dump(video_data, f, ensure_ascii=False, indent=2)
        logger.info(f"原始数据已保存到: {raw_data_file}")

    except Exception as e:
        logger.error(f"数据收集失败: {e}")
        logger.info("请检查MCP服务器配置和网络连接")
        return

    # 步骤3：事件2 - 模式分析
    logger.info("\n🔬 步骤3：事件2 - 模式分析")
    logger.info("正在分析视频数据中的模式...")

    try:
        # 初始化模式分析器
        analyzer = PatternAnalyzer(config)

        # 分析视频模式
        result = analyzer.analyze_videos(video_data)
        cases = result['selected_cases']

        logger.info(f"发现 {len(cases)} 个典型案例")

        # 保存分析结果
        patterns_file = output_dir / 'patterns.json'
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"模式分析结果已保存到: {patterns_file}")

        # 显示前5个案例
        logger.info("\n📊 前5个典型案例:")
        for i, case in enumerate(cases[:5], 1):
            pattern_name = case.get('pattern_name', '未知模式')
            title = case.get('title', '')[:30]
            views = case.get('view_count', 0)
            logger.info(f"{i}. {pattern_name} - {title}... ({views:,}次观看)")

    except Exception as e:
        logger.error(f"模式分析失败: {e}")
        return

    # 步骤4：事件3 - 模板生成
    logger.info("\n📝 步骤4：事件3 - 模板生成")
    logger.info("基于分析结果生成内容模板...")

    try:
        # 初始化工作流管理器
        workflow = WorkflowManager(config)

        # 生成研究报告
        report = workflow.generate_report(
            video_data=video_data,
            patterns=cases,
            template_type='report'
        )

        # 保存报告
        report_file = output_dir / 'research_report.md'
        write_text(report_file, report)
        logger.info(f"研究报告已生成: {report_file}")

        # 生成内容创作指南
        guide = workflow.generate_content_guide(
            patterns=cases,
            target_audience='初学者'
        )

        guide_file = output_dir / 'content_guide.md'
        write_text(guide_file, guide)
        logger.info(f"内容创作指南已生成: {guide_file}")

    except Exception as e:
        logger.error(f"模板生成失败: {e}")
        return

    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("✅ 快速开始示例执行完成！")
    logger.info("=" * 60)
    logger.info("\n📁 输出文件:")
    logger.info(f"  - 原始视频数据: {raw_data_file}")
    logger.info(f"  - 模式分析结果: {patterns_file}")
    logger.info(f"  - 研究报告: {report_file}")
    logger.info(f"  - 内容创作指南: {guide_file}")
    logger.info(f"  - 运行日志: {log_file}")
    logger.info("\n💡 提示:")
    logger.info("  - 查看output目录下的文件了解详细结果")
    logger.info("  - 可以修改config/config.yaml自定义配置")
    logger.info("  - 使用更多关键词可以获得更好的分析结果")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("YouTube视频研究工作流 - 快速开始示例")
    print("=" * 60)
    print("\n本示例将演示完整的三事件工作流程：")
    print("1. 事件1：收集YouTube视频数据")
    print("2. 事件2：分析视频模式")
    print("3. 事件3：生成内容模板和报告")
    print("\n开始执行...\n")

    try:
        quick_start_example()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
    except Exception as e:
        print(f"\n\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
