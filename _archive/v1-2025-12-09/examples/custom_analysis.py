#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义分析示例
展示如何自定义分析参数和流程
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import setup_logger
from utils.config import Config, get_config
from utils.file_utils import ensure_dir
from analysis.pattern_analyzer import PatternAnalyzer
from template.template_generator import TemplateGenerator

def custom_analysis_example():
    """
    自定义分析示例
    展示如何使用自定义配置进行分析
    """
    logger = setup_logger('custom_analysis')
    logger.info("=" * 60)
    logger.info("YouTube视频研究工作流 - 自定义分析示例")
    logger.info("=" * 60)

    # 创建自定义配置
    logger.info("\n📋 创建自定义配置")
    custom_config = Config()
    custom_config.set('analysis.min_pattern_frequency', 2)  # 降低模式频率阈值
    custom_config.set('analysis.similarity_threshold', 0.7)  # 调整相似度阈值
    custom_config.set('analysis.max_keywords', 30)  # 增加关键词数量
    logger.info("自定义配置已应用")

    # 模拟视频数据（实际使用时应从数据收集器获取）
    logger.info("\n📹 准备模拟视频数据")
    sample_videos = [
        {
            'id': 'video1',
            'title': 'Python入门教程：变量和数据类型',
            'description': '学习Python编程的基础知识',
            'view_count': 10000,
            'duration': 600,
            'tags': ['Python', '编程', '教程', '入门'],
            'channel': '编程教学频道',
            'published_at': '2024-01-15'
        },
        {
            'id': 'video2',
            'title': 'JavaScript基础教程：从零开始学习JS',
            'description': '前端开发必学JavaScript',
            'view_count': 15000,
            'duration': 900,
            'tags': ['JavaScript', '前端', '编程', '教程'],
            'channel': 'Web开发课堂',
            'published_at': '2024-01-20'
        },
        {
            'id': 'video3',
            'title': '数据科学入门：使用Python进行数据分析',
            'description': '学习数据分析的基本方法',
            'view_count': 8000,
            'duration': 1200,
            'tags': ['数据科学', 'Python', '数据分析', '教程'],
            'channel': '数据科学频道',
            'published_at': '2024-01-25'
        },
        {
            'id': 'video4',
            'title': '机器学习实战：线性回归算法详解',
            'description': '深入理解机器学习算法',
            'view_count': 12000,
            'duration': 1500,
            'tags': ['机器学习', '算法', 'Python', '实战'],
            'channel': 'AI学习室',
            'published_at': '2024-02-01'
        },
        {
            'id': 'video5',
            'title': '深度学习入门：神经网络基础',
            'description': '神经网络基本原理和实现',
            'view_count': 18000,
            'duration': 1800,
            'tags': ['深度学习', '神经网络', 'AI', 'Python'],
            'channel': 'AI学习室',
            'published_at': '2024-02-05'
        }
    ]
    logger.info(f"准备了 {len(sample_videos)} 个模拟视频")

    # 步骤1：关键词分析
    logger.info("\n🔍 步骤1：关键词分析")
    analyzer = PatternAnalyzer(custom_config)

    # 提取和分析关键词
    keyword_analysis = analyzer.extract_keywords(sample_videos)
    logger.info(f"提取到 {len(keyword_analysis['keywords'])} 个关键词")
    logger.info("前10个高频关键词:")
    for i, (keyword, count) in enumerate(keyword_analysis['keywords'][:10], 1):
        logger.info(f"  {i}. {keyword} (出现{count}次)")

    # 步骤2：标题模式分析
    logger.info("\n📝 步骤2：标题模式分析")
    title_patterns = analyzer.analyze_title_patterns(sample_videos)
    logger.info(f"发现 {len(title_patterns)} 种标题模式")

    for pattern in title_patterns:
        logger.info(f"  - {pattern['pattern']} (匹配{pattern['count']}个视频)")
        logger.info(f"    示例: {pattern['examples'][0]}")

    # 步骤3：标签共现分析
    logger.info("\n🏷️ 步骤3：标签共现分析")
    tag_analysis = analyzer.analyze_tag_cooccurrence(sample_videos)
    logger.info("标签共现网络:")
    for tag_pair, freq in tag_analysis['cooccurrence'][:5]:
        logger.info(f"  - {tag_pair[0]} + {tag_pair[1]} (共现{freq}次)")

    # 步骤4：观看数据分析
    logger.info("\n📊 步骤4：观看数据分析")
    view_analysis = analyzer.analyze_view_patterns(sample_videos)
    logger.info(f"平均观看次数: {view_analysis['average_views']:,.0f}")
    logger.info(f"观看次数中位数: {view_analysis['median_views']:,.0f}")
    logger.info(f"最高观看次数: {view_analysis['max_views']:,.0f}")

    # 找出表现最好的视频
    top_videos = sorted(sample_videos, key=lambda x: x['view_count'], reverse=True)
    logger.info("观看次数TOP3视频:")
    for i, video in enumerate(top_videos[:3], 1):
        logger.info(f"  {i}. {video['title']} ({video['view_count']:,}次观看)")

    # 步骤5：生成可视化报告
    logger.info("\n📈 步骤5：生成可视化报告")
    generator = TemplateGenerator(custom_config)

    report = generator.generate_custom_report({
        'video_count': len(sample_videos),
        'keyword_analysis': keyword_analysis,
        'title_patterns': title_patterns,
        'tag_analysis': tag_analysis,
        'view_analysis': view_analysis,
        'top_videos': top_videos[:3]
    })

    # 保存报告
    output_dir = Path('output/custom_analysis')
    ensure_dir(output_dir)
    report_file = output_dir / 'custom_analysis_report.md'

    from utils.file_utils import write_text
    write_text(report_file, report)
    logger.info(f"自定义分析报告已生成: {report_file}")

    # 步骤6：生成改进建议
    logger.info("\n💡 步骤6：生成内容改进建议")
    suggestions = analyzer.generate_content_suggestions(sample_videos)
    logger.info("基于分析的内容创作建议:")

    for category, items in suggestions.items():
        logger.info(f"\n{category}:")
        for item in items:
            logger.info(f"  - {item}")

    # 保存建议
    suggestions_file = output_dir / 'content_suggestions.md'
    suggestions_text = "\n".join([f"- {item}" for category, items in suggestions.items() for item in items])
    write_text(suggestions_file, f"# 内容创作建议\n\n{suggestions_text}")
    logger.info(f"内容建议已保存: {suggestions_file}")

    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("✅ 自定义分析示例执行完成！")
    logger.info("=" * 60)
    logger.info("\n📁 输出文件:")
    logger.info(f"  - 自定义分析报告: {report_file}")
    logger.info(f"  - 内容创作建议: {suggestions_file}")
    logger.info("\n🎯 本次分析亮点:")
    logger.info(f"  - 自定义了 {custom_config.get('analysis.min_pattern_frequency')} 次的最低模式频率")
    logger.info(f"  - 调整相似度阈值为 {custom_config.get('analysis.similarity_threshold')}")
    logger.info(f"  - 提取了 {len(keyword_analysis['keywords'])} 个关键词")
    logger.info(f"  - 识别了 {len(title_patterns)} 种标题模式")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("YouTube视频研究工作流 - 自定义分析示例")
    print("=" * 60)
    print("\n本示例将展示:")
    print("1. 自定义分析参数配置")
    print("2. 多维度视频数据分析")
    print("3. 生成可视化报告")
    print("4. 提供内容创作建议")
    print("\n开始执行...\n")

    try:
        custom_analysis_example()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
    except Exception as e:
        print(f"\n\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
