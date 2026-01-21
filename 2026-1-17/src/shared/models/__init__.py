#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块

基于 data.spec.md 定义的实体 Schema

实体关系:
- Video: 核心实体，贯穿全流程
- Script/Spec: 策划阶段产出
- Subtitle/Thumbnail: 制作阶段产出
- CompetitorVideo: 调研阶段采集
- Analytics: 复盘阶段数据
- Task: 任务调度
"""

# ============================================================
# 枚举类型
# ============================================================

from .base import (
    # 视频相关
    VideoStatus,
    Privacy,
    Resolution,
    # 脚本相关
    ScriptStatus,
    ContentStyle,
    # 字幕相关
    SubtitleType,
    SubtitleFormat,
    # 调研相关
    PatternType,
    # 复盘相关
    AnalyticsPeriod,
    # 任务相关
    Stage,
    TaskStatus,
)

# ============================================================
# 基类
# ============================================================

from .base import BaseModel

# ============================================================
# 实体模型
# ============================================================

# 视频 - 核心实体
from .video import Video, create_video

# 脚本和规约 - 策划阶段
from .script import Script, Spec, create_script, create_spec

# 媒体资源 - 制作阶段
from .media import Subtitle, Thumbnail, create_subtitle, create_thumbnail

# 竞品视频 - 调研阶段
from .research import CompetitorVideo, create_competitor_video

# 数据分析 - 复盘阶段
from .analytics import Analytics, create_analytics

# 任务 - 工作流调度
from .task import Task, TaskTypes, create_task

# ============================================================
# 工具函数
# ============================================================

from .base import (
    generate_uuid,
    generate_short_id,
    now_iso,
    parse_datetime,
    parse_enum,
    parse_json_field,
)


# ============================================================
# 导出列表
# ============================================================

__all__ = [
    # 枚举
    "VideoStatus",
    "Privacy",
    "Resolution",
    "ScriptStatus",
    "ContentStyle",
    "SubtitleType",
    "SubtitleFormat",
    "PatternType",
    "AnalyticsPeriod",
    "Stage",
    "TaskStatus",
    # 基类
    "BaseModel",
    # 实体
    "Video",
    "Script",
    "Spec",
    "Subtitle",
    "Thumbnail",
    "CompetitorVideo",
    "Analytics",
    "Task",
    "TaskTypes",
    # 工厂函数
    "create_video",
    "create_script",
    "create_spec",
    "create_subtitle",
    "create_thumbnail",
    "create_competitor_video",
    "create_analytics",
    "create_task",
    # 工具函数
    "generate_uuid",
    "generate_short_id",
    "now_iso",
    "parse_datetime",
    "parse_enum",
    "parse_json_field",
]
