#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle 和 Thumbnail 数据模型
媒体资源实体 - 制作阶段的核心产出

引用规约：
- data.spec.md: 2.3 Subtitle Schema, 2.4 Thumbnail Schema
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import (
    BaseModel,
    SubtitleType,
    SubtitleFormat,
    generate_uuid,
    parse_datetime,
    parse_enum,
)


@dataclass
class Subtitle(BaseModel):
    """
    字幕实体

    基于 data.spec.md 2.3 Subtitle Schema
    内容的时间轴文本
    """

    # 主键
    subtitle_id: str = field(default_factory=generate_uuid)

    # 关联
    video_id: str = ""

    # 基本信息
    language: str = "zh"  # ISO 639-1 语言代码
    type: SubtitleType = SubtitleType.AUTO
    format: SubtitleFormat = SubtitleFormat.VTT

    # 文件
    file_path: str = ""

    # 状态
    is_synced: bool = False  # 是否已同步校验
    is_uploaded: bool = False  # 是否已上传 YouTube

    # 时间
    created_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """验证字幕数据"""
        errors = []

        if not self.video_id:
            errors.append("video_id 不能为空")

        if not self.file_path:
            errors.append("file_path 不能为空")

        # 检查语言代码格式
        if len(self.language) != 2:
            errors.append(f"语言代码应为2位: {self.language}")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ============================================================
    # 文件方法
    # ============================================================

    def file_exists(self) -> bool:
        """检查文件是否存在"""
        return Path(self.file_path).exists() if self.file_path else False

    def get_file_size(self) -> Optional[int]:
        """获取文件大小（字节）"""
        if self.file_exists():
            return Path(self.file_path).stat().st_size
        return None

    @property
    def file_extension(self) -> str:
        """获取文件扩展名"""
        return self.format.value

    # ============================================================
    # 状态方法
    # ============================================================

    def mark_synced(self) -> None:
        """标记为已同步"""
        self.is_synced = True

    def mark_uploaded(self) -> None:
        """标记为已上传"""
        self.is_uploaded = True

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subtitle':
        """从字典创建实例"""
        return cls(
            subtitle_id=data.get('subtitle_id', generate_uuid()),
            video_id=data.get('video_id', ''),
            language=data.get('language', 'zh'),
            type=parse_enum(SubtitleType, data.get('type'), SubtitleType.AUTO),
            format=parse_enum(SubtitleFormat, data.get('format'), SubtitleFormat.VTT),
            file_path=data.get('file_path', ''),
            is_synced=bool(data.get('is_synced', False)),
            is_uploaded=bool(data.get('is_uploaded', False)),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
        )

    def __repr__(self) -> str:
        return f"Subtitle(id={self.subtitle_id[:8]}, lang={self.language}, synced={self.is_synced})"


@dataclass
class Thumbnail(BaseModel):
    """
    封面实体

    基于 data.spec.md 2.4 Thumbnail Schema
    视频封面图
    """

    # 主键
    thumbnail_id: str = field(default_factory=generate_uuid)

    # 关联
    video_id: str = ""

    # 文件
    file_path: str = ""

    # 尺寸 (YouTube 要求 1280x720)
    width: int = 1280
    height: int = 720
    file_size: Optional[int] = None  # 字节，最大 2MB

    # 状态
    is_active: bool = True  # 是否为当前使用的封面
    is_uploaded: bool = False  # 是否已上传 YouTube

    # 时间
    created_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 常量
    # ============================================================

    REQUIRED_WIDTH = 1280
    REQUIRED_HEIGHT = 720
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """
        验证封面数据

        基于 data.spec.md 3.3 封面图片约束
        """
        errors = []

        if not self.video_id:
            errors.append("video_id 不能为空")

        if not self.file_path:
            errors.append("file_path 不能为空")

        # 尺寸验证
        if self.width < self.REQUIRED_WIDTH:
            errors.append(f"宽度至少 {self.REQUIRED_WIDTH}px: {self.width}")

        if self.height < self.REQUIRED_HEIGHT:
            errors.append(f"高度至少 {self.REQUIRED_HEIGHT}px: {self.height}")

        # 宽高比验证 (16:9)
        expected_ratio = 16 / 9
        actual_ratio = self.width / self.height if self.height else 0
        if abs(actual_ratio - expected_ratio) > 0.01:
            errors.append(f"宽高比应为 16:9: 当前 {self.width}x{self.height}")

        # 文件大小验证
        if self.file_size and self.file_size > self.MAX_FILE_SIZE:
            errors.append(f"文件大小超过 2MB 限制: {self.file_size / 1024 / 1024:.2f}MB")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ============================================================
    # 文件方法
    # ============================================================

    def file_exists(self) -> bool:
        """检查文件是否存在"""
        return Path(self.file_path).exists() if self.file_path else False

    def update_file_info(self) -> bool:
        """
        更新文件信息（大小、尺寸）

        Returns:
            是否成功
        """
        if not self.file_exists():
            return False

        path = Path(self.file_path)
        self.file_size = path.stat().st_size

        # 尝试读取图片尺寸
        try:
            from PIL import Image
            with Image.open(path) as img:
                self.width, self.height = img.size
            return True
        except ImportError:
            # PIL 未安装，跳过尺寸更新
            return True
        except Exception:
            return False

    @property
    def file_size_mb(self) -> Optional[float]:
        """文件大小（MB）"""
        if self.file_size:
            return self.file_size / 1024 / 1024
        return None

    @property
    def resolution(self) -> str:
        """分辨率字符串"""
        return f"{self.width}x{self.height}"

    # ============================================================
    # 状态方法
    # ============================================================

    def set_active(self) -> None:
        """设为当前使用"""
        self.is_active = True

    def set_inactive(self) -> None:
        """设为不使用"""
        self.is_active = False

    def mark_uploaded(self) -> None:
        """标记为已上传"""
        self.is_uploaded = True

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Thumbnail':
        """从字典创建实例"""
        return cls(
            thumbnail_id=data.get('thumbnail_id', generate_uuid()),
            video_id=data.get('video_id', ''),
            file_path=data.get('file_path', ''),
            width=data.get('width', 1280),
            height=data.get('height', 720),
            file_size=data.get('file_size'),
            is_active=bool(data.get('is_active', True)),
            is_uploaded=bool(data.get('is_uploaded', False)),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
        )

    def __repr__(self) -> str:
        return f"Thumbnail(id={self.thumbnail_id[:8]}, {self.resolution}, active={self.is_active})"


# ============================================================
# 工厂函数
# ============================================================

def create_subtitle(
    video_id: str,
    file_path: str,
    language: str = "zh",
    subtitle_type: SubtitleType = SubtitleType.AUTO,
    **kwargs
) -> Subtitle:
    """创建新字幕"""
    return Subtitle(
        video_id=video_id,
        file_path=file_path,
        language=language,
        type=subtitle_type,
        **kwargs
    )


def create_thumbnail(
    video_id: str,
    file_path: str,
    **kwargs
) -> Thumbnail:
    """
    创建新封面

    会自动读取文件信息
    """
    thumbnail = Thumbnail(
        video_id=video_id,
        file_path=file_path,
        **kwargs
    )
    thumbnail.update_file_info()
    return thumbnail
