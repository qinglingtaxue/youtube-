#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具模块
提供各种数据验证和检查功能

引用规约：
- data.spec.md: 实体约束、文件格式规约
- sys.spec.md: 共享模块 Validators 组件
"""

import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from .logger import setup_logger

logger = setup_logger('validators')


class ValidationError(Exception):
    """验证错误异常"""

    def __init__(self, message: str, field: str = None, code: str = None):
        super().__init__(message)
        self.field = field
        self.code = code or 'E0002'  # 默认验证错误码

def validate_string(value: Any, min_length: int = 0, max_length: int = None, allow_empty: bool = True) -> str:
    """
    验证字符串

    Args:
        value: 要验证的值
        min_length: 最小长度
        max_length: 最大长度
        allow_empty: 是否允许空字符串

    Returns:
        验证后的字符串

    Raises:
        ValidationError: 验证失败时抛出
    """
    if value is None:
        if allow_empty:
            return ""
        raise ValidationError("不允许为空值")

    if not isinstance(value, str):
        raise ValidationError(f"期望字符串类型，实际为{type(value).__name__}")

    if not allow_empty and not value.strip():
        raise ValidationError("不允许为空字符串")

    if len(value) < min_length:
        raise ValidationError(f"字符串长度不能小于{min_length}，实际为{len(value)}")

    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"字符串长度不能大于{max_length}，实际为{len(value)}")

    return value.strip()

def validate_number(value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    """
    验证数字

    Args:
        value: 要验证的值
        min_value: 最小值
        max_value: 最大值

    Returns:
        验证后的数字

    Raises:
        ValidationError: 验证失败时抛出
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"无法转换为数字: {value}")

    if min_value is not None and num < min_value:
        raise ValidationError(f"数字不能小于{min_value}，实际为{num}")

    if max_value is not None and num > max_value:
        raise ValidationError(f"数字不能大于{max_value}，实际为{num}")

    return num

def validate_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """
    验证整数

    Args:
        value: 要验证的值
        min_value: 最小值
        max_value: 最大值

    Returns:
        验证后的整数

    Raises:
        ValidationError: 验证失败时抛出
    """
    try:
        num = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"无法转换为整数: {value}")

    if min_value is not None and num < min_value:
        raise ValidationError(f"整数不能小于{min_value}，实际为{num}")

    if max_value is not None and num > max_value:
        raise ValidationError(f"整数不能大于{max_value}，实际为{num}")

    return num

def validate_url(url: str) -> str:
    """
    验证URL

    Args:
        url: URL字符串

    Returns:
        验证后的URL

    Raises:
        ValidationError: 验证失败时抛出
    """
    url = validate_string(url, min_length=1)

    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"无效的URL格式: {url}")
        return url
    except Exception as e:
        raise ValidationError(f"URL验证失败: {e}")

def validate_email(email: str) -> str:
    """
    验证邮箱地址

    Args:
        email: 邮箱地址

    Returns:
        验证后的邮箱地址

    Raises:
        ValidationError: 验证失败时抛出
    """
    email = validate_string(email, min_length=1)

    # 简单的邮箱正则表达式
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"无效的邮箱格式: {email}")

    return email

def validate_youtube_url(url: str) -> str:
    """
    验证YouTube URL

    Args:
        url: YouTube URL

    Returns:
        验证后的URL

    Raises:
        ValidationError: 验证失败时抛出
    """
    url = validate_url(url)

    # YouTube URL模式
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return url

    raise ValidationError(f"不是有效的YouTube URL: {url}")

def validate_list(value: Any, min_length: int = 0, max_length: Optional[int] = None,
                  item_validator: Optional[callable] = None) -> List[Any]:
    """
    验证列表

    Args:
        value: 要验证的值
        min_length: 最小长度
        max_length: 最大长度
        item_validator: 单项验证函数

    Returns:
        验证后的列表

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(value, list):
        raise ValidationError(f"期望列表类型，实际为{type(value).__name__}")

    if len(value) < min_length:
        raise ValidationError(f"列表长度不能小于{min_length}，实际为{len(value)}")

    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"列表长度不能大于{max_length}，实际为{len(value)}")

    if item_validator:
        validated_list = []
        for i, item in enumerate(value):
            try:
                validated_item = item_validator(item)
                validated_list.append(validated_item)
            except ValidationError as e:
                raise ValidationError(f"列表第{i}项验证失败: {e}")
        return validated_list

    return value

def validate_dict(value: Any, required_keys: Optional[List[str]] = None,
                  key_validator: Optional[callable] = None,
                  value_validator: Optional[callable] = None) -> Dict[str, Any]:
    """
    验证字典

    Args:
        value: 要验证的值
        required_keys: 必需键列表
        key_validator: 键验证函数
        value_validator: 值验证函数

    Returns:
        验证后的字典

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(value, dict):
        raise ValidationError(f"期望字典类型，实际为{type(value).__name__}")

    if required_keys:
        missing_keys = set(required_keys) - set(value.keys())
        if missing_keys:
            raise ValidationError(f"缺少必需键: {missing_keys}")

    validated_dict = {}
    for key, val in value.items():
        # 验证键
        if key_validator:
            try:
                key = key_validator(key)
            except ValidationError as e:
                raise ValidationError(f"字典键验证失败: {e}")

        # 验证值
        if value_validator:
            try:
                val = value_validator(val)
            except ValidationError as e:
                raise ValidationError(f"字典值验证失败: {e}")

        validated_dict[key] = val

    return validated_dict

def validate_video_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证视频数据

    Args:
        data: 视频数据字典

    Returns:
        验证后的数据

    Raises:
        ValidationError: 验证失败时抛出
    """
    required_fields = ['id', 'title', 'url']
    validated_data = validate_dict(data, required_keys=required_fields)

    # 验证各个字段
    validated_data['id'] = validate_string(validated_data['id'], min_length=1)
    validated_data['title'] = validate_string(validated_data['title'], min_length=1, max_length=200)
    validated_data['url'] = validate_youtube_url(validated_data['url'])

    # 可选字段验证
    if 'description' in validated_data:
        validated_data['description'] = validate_string(validated_data['description'], max_length=5000)

    if 'duration' in validated_data:
        validated_data['duration'] = validate_integer(validated_data['duration'], min_value=0)

    if 'view_count' in validated_data:
        validated_data['view_count'] = validate_integer(validated_data['view_count'], min_value=0)

    if 'published_at' in validated_data:
        validated_data['published_at'] = validate_string(validated_data['published_at'], min_length=1)

    if 'channel' in validated_data:
        validated_data['channel'] = validate_string(validated_data['channel'], min_length=1, max_length=100)

    if 'tags' in validated_data:
        validated_data['tags'] = validate_list(
            validated_data['tags'],
            item_validator=lambda x: validate_string(x, min_length=1, max_length=50)
        )

    return validated_data

def validate_pattern_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证模式数据

    Args:
        data: 模式数据字典

    Returns:
        验证后的数据

    Raises:
        ValidationError: 验证失败时抛出
    """
    required_fields = ['name', 'frequency']
    validated_data = validate_dict(data, required_keys=required_fields)

    # 验证各个字段
    validated_data['name'] = validate_string(validated_data['name'], min_length=1, max_length=100)
    validated_data['frequency'] = validate_integer(validated_data['frequency'], min_value=1)

    # 可选字段验证
    if 'description' in validated_data:
        validated_data['description'] = validate_string(validated_data['description'], max_length=1000)

    if 'examples' in validated_data:
        validated_data['examples'] = validate_list(
            validated_data['examples'],
            item_validator=lambda x: validate_string(x, min_length=1, max_length=500)
        )

    if 'confidence' in validated_data:
        validated_data['confidence'] = validate_number(validated_data['confidence'], min_value=0, max_value=1)

    return validated_data

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除或替换非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32)
    # 限制长度
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
    return filename.strip()


# ==================== 视频相关验证（data.spec.md） ====================

def validate_video_format(file_path: Union[str, Path]) -> bool:
    """
    验证视频文件格式

    Args:
        file_path: 视频文件路径

    Returns:
        是否为有效的视频格式

    Raises:
        ValidationError: 验证失败时抛出
    """
    path = Path(file_path)

    if not path.exists():
        raise ValidationError(f"视频文件不存在: {file_path}", field='file_path', code='E0003')

    valid_extensions = {'.mp4', '.mov', '.mkv', '.avi', '.webm'}
    if path.suffix.lower() not in valid_extensions:
        raise ValidationError(
            f"不支持的视频格式: {path.suffix}，支持的格式: {valid_extensions}",
            field='file_path'
        )

    # 检查文件大小（最大 256GB - YouTube 限制）
    max_size = 256 * 1024 * 1024 * 1024  # 256GB
    file_size = path.stat().st_size
    if file_size > max_size:
        raise ValidationError(
            f"视频文件过大: {file_size / (1024**3):.2f}GB，最大允许 256GB",
            field='file_path'
        )

    return True


def validate_thumbnail_size(file_path: Union[str, Path]) -> bool:
    """
    验证封面图尺寸

    要求：
    - 分辨率: 1280x720
    - 宽高比: 16:9
    - 文件大小: < 2MB

    Args:
        file_path: 封面文件路径

    Returns:
        是否为有效的封面

    Raises:
        ValidationError: 验证失败时抛出
    """
    path = Path(file_path)

    if not path.exists():
        raise ValidationError(f"封面文件不存在: {file_path}", field='file_path', code='E0003')

    valid_extensions = {'.jpg', '.jpeg', '.png'}
    if path.suffix.lower() not in valid_extensions:
        raise ValidationError(
            f"不支持的封面格式: {path.suffix}，支持的格式: {valid_extensions}",
            field='file_path'
        )

    # 检查文件大小（最大 2MB）
    max_size = 2 * 1024 * 1024  # 2MB
    file_size = path.stat().st_size
    if file_size > max_size:
        raise ValidationError(
            f"封面文件过大: {file_size / 1024:.2f}KB，最大允许 2MB",
            field='file_path'
        )

    # 尝试检查图片尺寸（需要 PIL）
    try:
        from PIL import Image
        with Image.open(path) as img:
            width, height = img.size
            if width < 1280 or height < 720:
                raise ValidationError(
                    f"封面分辨率过低: {width}x{height}，最小要求 1280x720",
                    field='file_path'
                )
            # 检查宽高比（允许小误差）
            ratio = width / height
            expected_ratio = 16 / 9
            if abs(ratio - expected_ratio) > 0.1:
                logger.warning(f"封面宽高比 {ratio:.2f} 不是标准的 16:9")
    except ImportError:
        logger.warning("PIL 未安装，跳过封面尺寸检查")

    return True


def validate_subtitle_sync(subtitle_path: Union[str, Path], video_duration: int = None) -> bool:
    """
    验证字幕同步

    Args:
        subtitle_path: 字幕文件路径
        video_duration: 视频时长（秒），用于检查字幕是否超出

    Returns:
        是否为有效的字幕

    Raises:
        ValidationError: 验证失败时抛出
    """
    path = Path(subtitle_path)

    if not path.exists():
        raise ValidationError(f"字幕文件不存在: {subtitle_path}", field='file_path', code='E0003')

    valid_extensions = {'.srt', '.vtt', '.ass'}
    if path.suffix.lower() not in valid_extensions:
        raise ValidationError(
            f"不支持的字幕格式: {path.suffix}，支持的格式: {valid_extensions}",
            field='file_path'
        )

    # 读取并解析字幕
    content = path.read_text(encoding='utf-8')

    if not content.strip():
        raise ValidationError("字幕文件为空", field='file_path')

    # 基本格式检查
    if path.suffix.lower() == '.srt':
        # SRT 格式检查
        if not re.search(r'\d+\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', content):
            raise ValidationError("无效的 SRT 格式", field='file_path')
    elif path.suffix.lower() == '.vtt':
        # VTT 格式检查
        if not content.strip().startswith('WEBVTT'):
            raise ValidationError("无效的 VTT 格式：缺少 WEBVTT 头", field='file_path')

    return True


def validate_youtube_id(youtube_id: str) -> str:
    """
    验证 YouTube 视频 ID

    YouTube ID 格式：11 个字符，包含字母、数字、- 和 _

    Args:
        youtube_id: YouTube 视频 ID

    Returns:
        验证后的 ID

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not youtube_id:
        raise ValidationError("YouTube ID 不能为空", field='youtube_id')

    # YouTube ID 正则
    pattern = r'^[a-zA-Z0-9_-]{11}$'
    if not re.match(pattern, youtube_id):
        raise ValidationError(
            f"无效的 YouTube ID 格式: {youtube_id}，应为 11 个字符",
            field='youtube_id'
        )

    return youtube_id


def validate_video_title(title: str) -> str:
    """
    验证视频标题

    YouTube 限制：最多 100 个字符

    Args:
        title: 视频标题

    Returns:
        验证后的标题

    Raises:
        ValidationError: 验证失败时抛出
    """
    title = validate_string(title, min_length=1, max_length=100, allow_empty=False)

    # 检查是否包含禁止字符
    forbidden_chars = ['<', '>']
    for char in forbidden_chars:
        if char in title:
            raise ValidationError(f"标题包含禁止字符: {char}", field='title')

    return title


def validate_video_description(description: str) -> str:
    """
    验证视频描述

    YouTube 限制：最多 5000 个字符

    Args:
        description: 视频描述

    Returns:
        验证后的描述

    Raises:
        ValidationError: 验证失败时抛出
    """
    return validate_string(description, max_length=5000, allow_empty=True)


def validate_video_tags(tags: List[str]) -> List[str]:
    """
    验证视频标签

    YouTube 限制：总字符数不超过 500

    Args:
        tags: 标签列表

    Returns:
        验证后的标签列表

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not tags:
        return []

    validated_tags = []
    total_length = 0

    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue

        # 单个标签长度检查
        if len(tag) > 100:
            logger.warning(f"标签过长，已截断: {tag[:50]}...")
            tag = tag[:100]

        total_length += len(tag)
        validated_tags.append(tag)

    # 总长度检查
    if total_length > 500:
        raise ValidationError(
            f"标签总字符数 {total_length} 超过限制 500",
            field='tags'
        )

    return validated_tags


def validate_video_status(status: str) -> str:
    """
    验证视频状态

    Args:
        status: 视频状态

    Returns:
        验证后的状态

    Raises:
        ValidationError: 验证失败时抛出
    """
    valid_statuses = {'draft', 'scripting', 'producing', 'ready', 'published', 'scheduled'}
    if status not in valid_statuses:
        raise ValidationError(
            f"无效的视频状态: {status}，有效状态: {valid_statuses}",
            field='status'
        )
    return status


def validate_privacy(privacy: str) -> str:
    """
    验证隐私设置

    Args:
        privacy: 隐私设置

    Returns:
        验证后的隐私设置

    Raises:
        ValidationError: 验证失败时抛出
    """
    valid_privacy = {'public', 'unlisted', 'private'}
    if privacy not in valid_privacy:
        raise ValidationError(
            f"无效的隐私设置: {privacy}，有效设置: {valid_privacy}",
            field='privacy'
        )
    return privacy


def validate_stage(stage: str) -> str:
    """
    验证工作流阶段

    Args:
        stage: 阶段名称

    Returns:
        验证后的阶段名称

    Raises:
        ValidationError: 验证失败时抛出
    """
    valid_stages = {'research', 'planning', 'production', 'publishing', 'analytics'}
    if stage not in valid_stages:
        raise ValidationError(
            f"无效的阶段: {stage}，有效阶段: {valid_stages}",
            field='stage'
        )
    return stage


def validate_upload_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证上传配置

    基于 data.spec.md 中的 UploadConfig schema

    Args:
        config: 上传配置字典

    Returns:
        验证后的配置

    Raises:
        ValidationError: 验证失败时抛出
    """
    required_keys = ['video']
    for key in required_keys:
        if key not in config:
            raise ValidationError(f"上传配置缺少必需字段: {key}", field=key)

    # 验证 video 部分
    video = config['video']
    if 'path' not in video:
        raise ValidationError("上传配置缺少 video.path", field='video.path')

    validate_video_format(video['path'])

    if 'title' in video:
        video['title'] = validate_video_title(video['title'])

    if 'description' in video:
        video['description'] = validate_video_description(video['description'])

    if 'tags' in video:
        video['tags'] = validate_video_tags(video['tags'])

    if 'privacy' in video:
        video['privacy'] = validate_privacy(video['privacy'])

    # 验证 thumbnail 部分
    if 'thumbnail' in config and config['thumbnail'].get('path'):
        validate_thumbnail_size(config['thumbnail']['path'])

    # 验证 subtitles 部分
    if 'subtitles' in config and config['subtitles'].get('path'):
        validate_subtitle_sync(config['subtitles']['path'])

    return config
