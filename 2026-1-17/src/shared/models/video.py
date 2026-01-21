#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video 数据模型
视频实体 - 内容的最终载体，贯穿全流程

引用规约：
- data.spec.md: 2.1 Video Schema
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from .base import (
    BaseModel,
    VideoStatus,
    Privacy,
    Resolution,
    generate_uuid,
    parse_datetime,
    parse_enum,
    parse_json_field,
)


@dataclass
class Video(BaseModel):
    """
    视频实体

    基于 data.spec.md 2.1 Video Schema

    状态流转：
    draft → scripting → producing → ready → published/scheduled
    """

    # 主键
    video_id: str = field(default_factory=generate_uuid)

    # YouTube 相关
    youtube_id: Optional[str] = None  # 发布后填充，11位

    # 基本信息
    title: str = ""
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # 文件信息
    file_path: Optional[str] = None
    duration: Optional[int] = None  # 秒
    resolution: Optional[Resolution] = None

    # 状态
    status: VideoStatus = VideoStatus.DRAFT
    privacy: Privacy = Privacy.PRIVATE

    # 关联
    channel_id: Optional[str] = None
    spec_id: Optional[str] = None
    script_id: Optional[str] = None

    # 时间
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """
        验证视频数据

        Returns:
            错误列表，空表示验证通过
        """
        errors = []

        # 标题验证 (YouTube 限制 100 字符)
        if not self.title:
            errors.append("标题不能为空")
        elif len(self.title) > 100:
            errors.append(f"标题超过100字符限制: {len(self.title)}")

        # 描述验证 (YouTube 限制 5000 字符)
        if self.description and len(self.description) > 5000:
            errors.append(f"描述超过5000字符限制: {len(self.description)}")

        # 标签验证 (YouTube 限制总共 500 字符)
        if self.tags:
            total_tags_length = sum(len(tag) for tag in self.tags)
            if total_tags_length > 500:
                errors.append(f"标签总长度超过500字符限制: {total_tags_length}")

        # YouTube ID 验证
        if self.youtube_id and len(self.youtube_id) != 11:
            errors.append(f"YouTube ID 应为11位: {self.youtube_id}")

        return errors

    def is_valid(self) -> bool:
        """是否验证通过"""
        return len(self.validate()) == 0

    # ============================================================
    # 状态流转方法
    # ============================================================

    def can_transition_to(self, new_status: VideoStatus) -> bool:
        """
        检查是否可以转换到新状态

        状态流转规则 (data.spec.md 4.2):
        - draft → scripting
        - scripting → producing
        - producing → ready
        - ready → published | scheduled
        - scheduled → published
        - 任何状态 → draft (重置)
        """
        valid_transitions = {
            VideoStatus.DRAFT: [VideoStatus.SCRIPTING],
            VideoStatus.SCRIPTING: [VideoStatus.PRODUCING, VideoStatus.DRAFT],
            VideoStatus.PRODUCING: [VideoStatus.READY, VideoStatus.DRAFT],
            VideoStatus.READY: [VideoStatus.PUBLISHED, VideoStatus.SCHEDULED, VideoStatus.DRAFT],
            VideoStatus.SCHEDULED: [VideoStatus.PUBLISHED, VideoStatus.DRAFT],
            VideoStatus.PUBLISHED: [VideoStatus.DRAFT],  # 允许重置
        }

        allowed = valid_transitions.get(self.status, [])
        return new_status in allowed

    def transition_to(self, new_status: VideoStatus) -> bool:
        """
        转换状态

        Returns:
            是否成功
        """
        if self.can_transition_to(new_status):
            self.status = new_status
            self.updated_at = datetime.now()
            return True
        return False

    def mark_published(self, youtube_id: str) -> None:
        """标记为已发布"""
        self.youtube_id = youtube_id
        self.status = VideoStatus.PUBLISHED
        self.published_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_scheduled(self, scheduled_time: datetime) -> None:
        """标记为定时发布"""
        self.status = VideoStatus.SCHEDULED
        self.scheduled_at = scheduled_time
        self.updated_at = datetime.now()

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Video':
        """从字典创建实例"""
        return cls(
            video_id=data.get('video_id', generate_uuid()),
            youtube_id=data.get('youtube_id'),
            title=data.get('title', ''),
            description=data.get('description'),
            tags=parse_json_field(data.get('tags')) or [],
            file_path=data.get('file_path'),
            duration=data.get('duration'),
            resolution=parse_enum(Resolution, data.get('resolution')),
            status=parse_enum(VideoStatus, data.get('status'), VideoStatus.DRAFT),
            privacy=parse_enum(Privacy, data.get('privacy'), Privacy.PRIVATE),
            channel_id=data.get('channel_id'),
            spec_id=data.get('spec_id'),
            script_id=data.get('script_id'),
            published_at=parse_datetime(data.get('published_at')),
            scheduled_at=parse_datetime(data.get('scheduled_at')),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
            updated_at=parse_datetime(data.get('updated_at')) or datetime.now(),
        )

    # ============================================================
    # 便捷方法
    # ============================================================

    @property
    def is_draft(self) -> bool:
        return self.status == VideoStatus.DRAFT

    @property
    def is_published(self) -> bool:
        return self.status == VideoStatus.PUBLISHED

    @property
    def is_ready_to_publish(self) -> bool:
        return self.status == VideoStatus.READY

    @property
    def duration_formatted(self) -> str:
        """格式化时长 (MM:SS 或 HH:MM:SS)"""
        if not self.duration:
            return "00:00"

        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def youtube_url(self) -> Optional[str]:
        """YouTube 链接"""
        if self.youtube_id:
            return f"https://www.youtube.com/watch?v={self.youtube_id}"
        return None

    def __repr__(self) -> str:
        return f"Video(id={self.video_id[:8]}, title='{self.title[:20]}...', status={self.status.value})"


# ============================================================
# 工厂函数
# ============================================================

def create_video(
    title: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    **kwargs
) -> Video:
    """
    创建新视频

    Args:
        title: 标题
        description: 描述
        tags: 标签列表
        **kwargs: 其他字段

    Returns:
        Video 实例
    """
    return Video(
        title=title,
        description=description,
        tags=tags or [],
        **kwargs
    )
