#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CompetitorVideo 数据模型
竞品视频实体 - 调研阶段的核心数据

引用规约：
- data.spec.md: 2.6 CompetitorVideo Schema

数据分层策略（参考 VidIQ/TubeBuddy 最佳实践）：
- 第一层：搜索即可获得（快速采集）
- 第二层：需要详情请求（按需采集）
- 第三层：不存储（实时获取）
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import (
    BaseModel,
    PatternType,
    parse_datetime,
    parse_enum,
    parse_json_field,
)


# 字段截断常量
MAX_DESCRIPTION_LENGTH = 500  # 描述截断长度
MAX_TAGS_COUNT = 10           # 最多保留标签数


@dataclass
class CompetitorVideo(BaseModel):
    """
    竞品视频实体

    基于 data.spec.md 2.6 CompetitorVideo Schema
    调研阶段采集的竞品视频元数据

    数据分层：
    - 第一层（搜索获得）：youtube_id, title, channel_name, view_count, duration, published_at
    - 第二层（详情获得）：like_count, comment_count, description, tags, channel_id, thumbnail_url
    """

    # 主键 (自增，可选)
    id: Optional[int] = None

    # ============================================================
    # 第一层：搜索即可获得（快速采集，0.5秒/个）
    # ============================================================
    youtube_id: str = ""  # 11位，唯一标识
    title: str = ""       # 完整保留（YouTube 限制 100 字符）
    channel_name: Optional[str] = None
    view_count: int = 0   # 质量筛选核心指标
    duration: Optional[int] = None  # 秒
    published_at: Optional[datetime] = None

    # ============================================================
    # 第二层：需要详情请求（按需采集，4秒/个）
    # ============================================================
    has_details: bool = False  # 标记是否已获取详情
    like_count: int = 0
    comment_count: int = 0
    description: Optional[str] = None  # 截断为 MAX_DESCRIPTION_LENGTH
    tags: List[str] = field(default_factory=list)  # 只存前 MAX_TAGS_COUNT 个
    channel_id: Optional[str] = None
    thumbnail_url: Optional[str] = None  # 只存 1 个（非多尺寸列表）
    category: Optional[str] = None
    subscriber_count: int = 0  # 频道订阅数

    # ============================================================
    # 调研相关
    # ============================================================
    theme: Optional[str] = None  # 主题分类（如"养生"、"科技"）
    keyword_source: Optional[str] = None  # 来源关键词
    pattern_type: PatternType = PatternType.UNKNOWN  # 识别的模式
    pattern_score: Optional[float] = None  # 模式匹配得分

    # 时间
    collected_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 计算属性
    # ============================================================

    @property
    def url(self) -> str:
        """YouTube 链接"""
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def channel_url(self) -> Optional[str]:
        """频道链接"""
        if self.channel_id:
            return f"https://www.youtube.com/channel/{self.channel_id}"
        return None

    @property
    def engagement_rate(self) -> float:
        """
        互动率 (点赞+评论 / 播放)

        Returns:
            互动率，0-1 之间
        """
        if self.view_count <= 0:
            return 0.0
        return (self.like_count + self.comment_count) / self.view_count

    @property
    def like_rate(self) -> float:
        """点赞率"""
        if self.view_count <= 0:
            return 0.0
        return self.like_count / self.view_count

    @property
    def duration_formatted(self) -> str:
        """格式化时长"""
        if not self.duration:
            return "N/A"

        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def view_count_formatted(self) -> str:
        """格式化播放量"""
        if self.view_count >= 1_000_000:
            return f"{self.view_count / 1_000_000:.1f}M"
        elif self.view_count >= 1_000:
            return f"{self.view_count / 1_000:.1f}K"
        return str(self.view_count)

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """验证数据"""
        errors = []

        if not self.youtube_id:
            errors.append("youtube_id 不能为空")
        elif len(self.youtube_id) != 11:
            errors.append(f"youtube_id 应为11位: {len(self.youtube_id)}")

        if not self.title:
            errors.append("title 不能为空")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ============================================================
    # 质量评估
    # ============================================================

    def is_high_quality(
        self,
        min_views: int = 1000,
        min_likes: int = 50,
        max_duration: int = 3600
    ) -> bool:
        """
        判断是否为高质量视频

        Args:
            min_views: 最小播放量
            min_likes: 最小点赞数
            max_duration: 最大时长（秒）
        """
        if self.view_count < min_views:
            return False
        if self.like_count < min_likes:
            return False
        if self.duration and self.duration > max_duration:
            return False
        return True

    def quality_score(self) -> float:
        """
        计算质量分数

        综合考虑播放量、互动率、模式匹配度

        Returns:
            0-1 之间的分数
        """
        # 播放量分数 (10万为满分)
        view_score = min(self.view_count / 100000, 1.0)

        # 互动率分数 (5%为满分)
        engagement_score = min(self.engagement_rate * 20, 1.0)

        # 模式分数
        pattern_score = self.pattern_score or 0.0

        # 加权平均
        return view_score * 0.4 + engagement_score * 0.3 + pattern_score * 0.3

    # ============================================================
    # 模式相关
    # ============================================================

    def set_pattern(self, pattern_type: PatternType, score: float) -> None:
        """设置识别的模式"""
        self.pattern_type = pattern_type
        self.pattern_score = score

    @property
    def pattern_name(self) -> str:
        """模式中文名"""
        names = {
            PatternType.COGNITIVE_IMPACT: "认知冲击型",
            PatternType.STORYTELLING: "故事叙述型",
            PatternType.KNOWLEDGE_SHARING: "干货输出型",
            PatternType.INTERACTION_GUIDE: "互动引导型",
            PatternType.UNKNOWN: "未知",
        }
        return names.get(self.pattern_type, "未知")

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompetitorVideo':
        """从字典创建实例"""
        # 截断处理
        description = data.get('description')
        if description and len(description) > MAX_DESCRIPTION_LENGTH:
            description = description[:MAX_DESCRIPTION_LENGTH]

        tags = parse_json_field(data.get('tags')) or []
        if len(tags) > MAX_TAGS_COUNT:
            tags = tags[:MAX_TAGS_COUNT]

        return cls(
            id=data.get('id'),
            youtube_id=data.get('youtube_id', ''),
            title=data.get('title', ''),
            channel_name=data.get('channel_name') or data.get('channel'),
            view_count=data.get('view_count', 0) or 0,
            duration=data.get('duration'),
            published_at=parse_datetime(data.get('published_at') or data.get('upload_date')),
            # 第二层字段
            has_details=data.get('has_details', False),
            like_count=data.get('like_count', 0) or 0,
            comment_count=data.get('comment_count', 0) or 0,
            description=description,
            tags=tags,
            channel_id=data.get('channel_id'),
            thumbnail_url=data.get('thumbnail_url'),
            category=data.get('category'),
            subscriber_count=data.get('subscriber_count', 0) or 0,
            # 调研相关
            theme=data.get('theme'),
            keyword_source=data.get('keyword_source'),
            pattern_type=parse_enum(PatternType, data.get('pattern_type'), PatternType.UNKNOWN),
            pattern_score=data.get('pattern_score'),
            collected_at=parse_datetime(data.get('collected_at')) or datetime.now(),
        )

    @classmethod
    def from_ytdlp_search(cls, data: Dict[str, Any], keyword: str = "", theme: str = None) -> 'CompetitorVideo':
        """
        从 yt-dlp 搜索结果创建实例（第一层数据，快速）

        Args:
            data: yt-dlp --flat-playlist 的输出
            keyword: 来源关键词
            theme: 主题分类（如"养生"、"科技"）
        """
        # 优先使用精确时间戳，回退到日期
        published_time = (
            data.get('release_timestamp') or  # 首播时间（精确到秒）
            data.get('timestamp') or          # 上传时间（精确到秒）
            data.get('upload_date')           # 仅日期 YYYYMMDD
        )
        return cls(
            youtube_id=data.get('id', ''),
            title=data.get('title', ''),
            channel_name=data.get('channel') or data.get('uploader'),
            view_count=data.get('view_count', 0) or 0,
            duration=data.get('duration'),
            published_at=parse_datetime(published_time),
            theme=theme,
            keyword_source=keyword,
            has_details=False,  # 标记：未获取详情
        )

    @classmethod
    def from_ytdlp_details(cls, data: Dict[str, Any], keyword: str = "", theme: str = None) -> 'CompetitorVideo':
        """
        从 yt-dlp 详情结果创建实例（第二层数据，完整）

        Args:
            data: yt-dlp --dump-json 的输出
            keyword: 来源关键词
            theme: 主题分类（如"养生"、"科技"）
        """
        # 截断描述
        description = data.get('description', '')
        if description and len(description) > MAX_DESCRIPTION_LENGTH:
            description = description[:MAX_DESCRIPTION_LENGTH]

        # 截断标签
        tags = data.get('tags') or []
        if len(tags) > MAX_TAGS_COUNT:
            tags = tags[:MAX_TAGS_COUNT]

        # 提取单个缩略图 URL（不存储多尺寸列表）
        thumbnail_url = data.get('thumbnail', '')

        # 优先使用精确时间戳，回退到日期
        published_time = (
            data.get('release_timestamp') or  # 首播时间（精确到秒）
            data.get('timestamp') or          # 上传时间（精确到秒）
            data.get('upload_date')           # 仅日期 YYYYMMDD
        )

        return cls(
            youtube_id=data.get('id', ''),
            title=data.get('title', ''),
            channel_name=data.get('channel') or data.get('uploader'),
            view_count=data.get('view_count', 0) or 0,
            duration=data.get('duration'),
            published_at=parse_datetime(published_time),
            # 第二层字段
            has_details=True,  # 标记：已获取详情
            like_count=data.get('like_count', 0) or 0,
            comment_count=data.get('comment_count', 0) or 0,
            description=description,
            tags=tags,
            channel_id=data.get('channel_id') or data.get('uploader_id'),
            thumbnail_url=thumbnail_url,
            category=data.get('categories', [None])[0] if data.get('categories') else None,
            subscriber_count=data.get('channel_follower_count', 0) or 0,
            theme=theme,
            keyword_source=keyword,
        )

    @classmethod
    def from_ytdlp(cls, data: Dict[str, Any], keyword: str = "") -> 'CompetitorVideo':
        """
        从 yt-dlp 输出创建实例（兼容旧接口）

        Args:
            data: yt-dlp --dump-json 的输出
            keyword: 来源关键词
        """
        return cls.from_ytdlp_details(data, keyword)

    def __repr__(self) -> str:
        return f"CompetitorVideo(id={self.youtube_id}, title='{self.title[:20]}...', views={self.view_count_formatted})"


# ============================================================
# 工厂函数
# ============================================================

def create_competitor_video(
    youtube_id: str,
    title: str,
    view_count: int = 0,
    **kwargs
) -> CompetitorVideo:
    """创建竞品视频"""
    return CompetitorVideo(
        youtube_id=youtube_id,
        title=title,
        view_count=view_count,
        **kwargs
    )
