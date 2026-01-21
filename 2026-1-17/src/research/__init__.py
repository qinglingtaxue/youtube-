#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调研模块 (Research Module)

提供 YouTube 视频调研功能，包括：
- 数据收集 (DataCollector)
- 模式分析 (PatternAnalyzer)
- 报告生成 (ReportGenerator)

引用规约：
- pipeline.spec.md: Stage 2 调研阶段
- api.spec.md: 2.2 调研命令, 3.1-3.2 内部接口
"""

from .yt_dlp_client import YtDlpClient, YtDlpError
from .data_collector import DataCollector, collect_and_filter
from .pattern_analyzer import PatternAnalyzer, analyze_videos
from .report_generator import ReportGenerator, generate_research_report

__all__ = [
    # 客户端
    'YtDlpClient',
    'YtDlpError',
    # 数据收集
    'DataCollector',
    'collect_and_filter',
    # 模式分析
    'PatternAnalyzer',
    'analyze_videos',
    # 报告生成
    'ReportGenerator',
    'generate_research_report',
    # 完整工作流
    'run_research',
]


def run_research(
    keyword: str,
    max_results: int = 50,
    max_cases: int = 10,
    output_format: str = 'md',
    output_dir: str = 'data/reports'
) -> dict:
    """
    执行完整调研流程

    符合 pipeline.spec.md Stage 2 调研阶段定义

    Args:
        keyword: 搜索关键词
        max_results: 最大搜索结果数
        max_cases: 最大案例数
        output_format: 输出格式 (md/json/html)
        output_dir: 输出目录

    Returns:
        {
            'videos': List[Dict],      # 收集的视频数据
            'analysis': Dict,          # 分析结果
            'report_path': Path,       # 报告文件路径
            'summary': Dict            # 摘要信息
        }
    """
    from pathlib import Path

    # 1. 收集数据
    collector = DataCollector()
    videos = collector.search_videos(keyword, max_results=max_results)

    if not videos:
        return {
            'videos': [],
            'analysis': {},
            'report_path': None,
            'summary': {'error': '未找到视频数据'}
        }

    # 2. 筛选高质量视频
    quality_videos = collector.filter_quality_videos(videos)

    # 3. 分析模式
    analyzer = PatternAnalyzer()
    analysis = analyzer.analyze_videos(quality_videos, max_cases=max_cases)

    # 4. 生成报告
    generator = ReportGenerator()
    report_path = generator.generate_and_save(
        keyword=keyword,
        videos=quality_videos,
        analysis_result=analysis,
        output_dir=Path(output_dir),
        output_format=output_format
    )

    # 5. 构建返回结果
    return {
        'videos': quality_videos,
        'analysis': analysis,
        'report_path': report_path,
        'summary': {
            'keyword': keyword,
            'total_collected': len(videos),
            'total_filtered': len(quality_videos),
            'patterns_found': len(analysis.get('pattern_distribution', {})),
            'cases_selected': len(analysis.get('selected_cases', [])),
            'report_format': output_format
        }
    }
