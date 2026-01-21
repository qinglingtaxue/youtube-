#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository 层

提供实体的数据库 CRUD 操作，连接 Model 和 Database
"""

from .competitor_video_repo import CompetitorVideoRepository

__all__ = [
    "CompetitorVideoRepository",
]
