#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调研工具主程序
统一管理数据收集、分析和报告生成
"""

from .mcp_data_collector import MCPDataCollector
from .real_data_collector import RealDataCollector
from .multi_platform_collector import MultiPlatformCollector

__all__ = ['MCPDataCollector', 'RealDataCollector', 'MultiPlatformCollector']
