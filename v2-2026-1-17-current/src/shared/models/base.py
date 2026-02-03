#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型基础定义
包含枚举、基类、工具函数

引用规约：
- data.spec.md: 实体 Schema 定义
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional, List, TypeVar, Type
import uuid
import json


# ============================================================
# 枚举定义 (基于 data.spec.md)
# ============================================================

class VideoStatus(str, Enum):
    """视频状态枚举 - data.spec.md 2.1"""
    DRAFT = "draft"
    SCRIPTING = "scripting"
    PRODUCING = "producing"
    READY = "ready"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"


class Privacy(str, Enum):
    """隐私设置枚举 - data.spec.md 2.1"""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class Resolution(str, Enum):
    """视频分辨率枚举 - data.spec.md 2.1"""
    HD_720P = "720p"
    FHD_1080P = "1080p"
    UHD_4K = "4K"


class ScriptStatus(str, Enum):
    """脚本状态枚举 - data.spec.md 2.2"""
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    ARCHIVED = "archived"


class SubtitleType(str, Enum):
    """字幕类型枚举 - data.spec.md 2.3"""
    AUTO = "auto"
    MANUAL = "manual"
    TRANSLATED = "translated"


class SubtitleFormat(str, Enum):
    """字幕格式枚举 - data.spec.md 2.3"""
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"


class ContentStyle(str, Enum):
    """内容风格枚举 - data.spec.md 2.5"""
    TUTORIAL = "tutorial"
    STORY = "story"
    REVIEW = "review"
    VLOG = "vlog"
    EXPLAINER = "explainer"


class PatternType(str, Enum):
    """模式类型枚举 - data.spec.md 2.6"""
    COGNITIVE_IMPACT = "cognitive_impact"
    STORYTELLING = "storytelling"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    INTERACTION_GUIDE = "interaction_guide"
    UNKNOWN = "unknown"


class AnalyticsPeriod(str, Enum):
    """统计周期枚举 - data.spec.md 2.7"""
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    LIFETIME = "lifetime"


class Stage(str, Enum):
    """流水线阶段枚举 - data.spec.md 2.8"""
    RESEARCH = "research"
    PLANNING = "planning"
    PRODUCTION = "production"
    PUBLISHING = "publishing"
    ANALYTICS = "analytics"


class TaskStatus(str, Enum):
    """任务状态枚举 - data.spec.md 2.8"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================
# 基类定义
# ============================================================

T = TypeVar('T', bound='BaseModel')


@dataclass
class BaseModel:
    """
    数据模型基类

    提供通用的序列化/反序列化方法
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        处理：
        - Enum 转为 value
        - datetime 转为 ISO 格式字符串
        - 嵌套对象递归转换
        """
        result = {}
        for key, value in asdict(self).items():
            result[key] = self._serialize_value(value)
        return result

    def _serialize_value(self, value: Any) -> Any:
        """序列化单个值"""
        if isinstance(value, Enum):
            return value.value
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, list):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, 'to_dict'):
            return value.to_dict()
        return value

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建实例

        子类应重写此方法以处理特殊字段转换
        """
        # 过滤掉不在字段中的键
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """从 JSON 字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ============================================================
# 工具函数
# ============================================================

def generate_uuid() -> str:
    """生成 UUID"""
    return str(uuid.uuid4())


def generate_short_id() -> str:
    """生成短 ID (8位)"""
    return uuid.uuid4().hex[:8]


def now_iso() -> str:
    """获取当前时间 ISO 格式"""
    return datetime.now().isoformat()


def parse_datetime(value: Any) -> Optional[datetime]:
    """
    解析日期时间

    支持：
    - datetime 对象
    - Unix 时间戳（int/float）
    - ISO 格式字符串
    - YYYYMMDD 格式字符串（yt-dlp upload_date）
    - None
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Unix 时间戳（yt-dlp 的 timestamp/release_timestamp 字段）
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except (ValueError, OSError):
            pass
    if isinstance(value, str):
        try:
            # 尝试 ISO 格式
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            pass
        try:
            # 尝试常见格式
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        try:
            # 仅日期
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            pass
        try:
            # YYYYMMDD 格式（yt-dlp upload_date）
            return datetime.strptime(value, '%Y%m%d')
        except ValueError:
            pass
    return None


def parse_enum(enum_class: Type[Enum], value: Any, default: Any = None) -> Optional[Enum]:
    """
    解析枚举值

    Args:
        enum_class: 枚举类
        value: 值（可以是枚举实例或字符串）
        default: 默认值
    """
    if value is None:
        return default
    if isinstance(value, enum_class):
        return value
    if isinstance(value, str):
        try:
            return enum_class(value)
        except ValueError:
            return default
    return default


def parse_json_field(value: Any) -> Any:
    """
    解析可能是 JSON 字符串的字段

    用于处理数据库中存储为 TEXT 的 JSON 字段
    """
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value
