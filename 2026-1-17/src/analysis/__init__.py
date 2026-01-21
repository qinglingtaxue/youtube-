#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析模块

提供视频数据的全面分析能力
"""

from .video_analyzer import VideoAnalyzer, AnalysisResult, analyze_videos

__all__ = [
    "VideoAnalyzer",
    "AnalysisResult",
    "analyze_videos",
]
