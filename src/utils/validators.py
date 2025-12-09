#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具模块
提供各种数据验证和检查功能
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from .logger import setup_logger

logger = setup_logger('validators')

class ValidationError(Exception):
    """验证错误异常"""
    pass

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
