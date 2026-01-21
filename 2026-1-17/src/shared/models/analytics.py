#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics 数据模型
视频表现数据 - 复盘阶段的核心数据

引用规约：
- data.spec.md: 2.7 Analytics Schema
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from .base import (
    BaseModel,
    AnalyticsPeriod,
    parse_datetime,
    parse_enum,
)


@dataclass
class Analytics(BaseModel):
    """
    视频表现数据实体

    基于 data.spec.md 2.7 Analytics Schema
    复盘阶段采集的视频表现指标
    """

    # 主键 (自增，可选)
    id: Optional[int] = None

    # 关联
    video_id: str = ""

    # 报告信息
    report_date: date = field(default_factory=date.today)
    period: AnalyticsPeriod = AnalyticsPeriod.DAYS_7

    # 观看数据
    views: int = 0
    watch_time_minutes: int = 0
    average_view_duration: Optional[int] = None  # 秒
    unique_viewers: int = 0

    # 互动数据
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    shares: int = 0

    # 频道数据
    subscribers_gained: int = 0
    subscribers_lost: int = 0

    # 曝光数据
    impressions: int = 0
    ctr: Optional[float] = None  # 点击率 (%)

    # 时间
    collected_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 计算属性
    # ============================================================

    @property
    def engagement_rate(self) -> float:
        """
        互动率 (点赞+评论+分享 / 播放)

        Returns:
            互动率，0-1 之间
        """
        if self.views <= 0:
            return 0.0
        return (self.likes + self.comments + self.shares) / self.views

    @property
    def like_ratio(self) -> float:
        """
        好评率 (点赞 / (点赞+踩))

        Returns:
            好评率，0-1 之间
        """
        total = self.likes + self.dislikes
        if total <= 0:
            return 0.0
        return self.likes / total

    @property
    def subscriber_delta(self) -> int:
        """订阅净增"""
        return self.subscribers_gained - self.subscribers_lost

    @property
    def average_watch_percentage(self) -> Optional[float]:
        """
        平均观看百分比

        需要视频时长信息，这里仅返回平均观看时长
        """
        return None  # 需要视频时长才能计算

    @property
    def watch_time_hours(self) -> float:
        """观看时长 (小时)"""
        return self.watch_time_minutes / 60

    @property
    def ctr_formatted(self) -> str:
        """格式化点击率"""
        if self.ctr is None:
            return "N/A"
        return f"{self.ctr:.2f}%"

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """验证数据"""
        errors = []

        if not self.video_id:
            errors.append("video_id 不能为空")

        if self.ctr is not None:
            if self.ctr < 0 or self.ctr > 100:
                errors.append(f"点击率应在0-100之间: {self.ctr}")

        if self.views < 0:
            errors.append("播放量不能为负数")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ============================================================
    # 分析方法
    # ============================================================

    def is_performing_well(
        self,
        min_views: int = 100,
        min_ctr: float = 2.0,
        min_engagement: float = 0.02
    ) -> bool:
        """
        判断视频表现是否良好

        Args:
            min_views: 最小播放量
            min_ctr: 最小点击率 (%)
            min_engagement: 最小互动率
        """
        if self.views < min_views:
            return False
        if self.ctr is not None and self.ctr < min_ctr:
            return False
        if self.engagement_rate < min_engagement:
            return False
        return True

    def performance_score(self) -> float:
        """
        计算综合表现分数

        Returns:
            0-100 之间的分数
        """
        # 播放量分数 (1万为满分)
        view_score = min(self.views / 10000, 1.0) * 30

        # 点击率分数 (5%为满分)
        ctr_score = min((self.ctr or 0) / 5, 1.0) * 25

        # 互动率分数 (5%为满分)
        engagement_score = min(self.engagement_rate * 20, 1.0) * 25

        # 好评率分数
        like_score = self.like_ratio * 20

        return view_score + ctr_score + engagement_score + like_score

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Analytics':
        """从字典创建实例"""
        # 处理 report_date
        report_date_val = data.get('report_date')
        if isinstance(report_date_val, str):
            try:
                report_date = datetime.strptime(report_date_val, '%Y-%m-%d').date()
            except ValueError:
                report_date = date.today()
        elif isinstance(report_date_val, date):
            report_date = report_date_val
        else:
            report_date = date.today()

        return cls(
            id=data.get('id'),
            video_id=data.get('video_id', ''),
            report_date=report_date,
            period=parse_enum(AnalyticsPeriod, data.get('period'), AnalyticsPeriod.DAYS_7),
            views=data.get('views', 0) or 0,
            watch_time_minutes=data.get('watch_time_minutes', 0) or 0,
            average_view_duration=data.get('average_view_duration'),
            unique_viewers=data.get('unique_viewers', 0) or 0,
            likes=data.get('likes', 0) or 0,
            dislikes=data.get('dislikes', 0) or 0,
            comments=data.get('comments', 0) or 0,
            shares=data.get('shares', 0) or 0,
            subscribers_gained=data.get('subscribers_gained', 0) or 0,
            subscribers_lost=data.get('subscribers_lost', 0) or 0,
            impressions=data.get('impressions', 0) or 0,
            ctr=data.get('ctr'),
            collected_at=parse_datetime(data.get('collected_at')) or datetime.now(),
        )

    @classmethod
    def from_youtube_analytics(cls, data: Dict[str, Any], video_id: str) -> 'Analytics':
        """
        从 YouTube Analytics API 响应创建实例

        Args:
            data: YouTube Analytics API 返回的数据
            video_id: 视频 ID
        """
        return cls(
            video_id=video_id,
            views=data.get('views', 0),
            watch_time_minutes=data.get('estimatedMinutesWatched', 0),
            average_view_duration=data.get('averageViewDuration'),
            likes=data.get('likes', 0),
            dislikes=data.get('dislikes', 0),
            comments=data.get('comments', 0),
            shares=data.get('shares', 0),
            subscribers_gained=data.get('subscribersGained', 0),
            subscribers_lost=data.get('subscribersLost', 0),
            impressions=data.get('impressions', 0),
            ctr=data.get('impressionsClickThroughRate'),
        )

    def __repr__(self) -> str:
        return f"Analytics(video={self.video_id[:8] if self.video_id else 'N/A'}, date={self.report_date}, views={self.views})"


# ============================================================
# 工厂函数
# ============================================================

def create_analytics(
    video_id: str,
    views: int = 0,
    period: AnalyticsPeriod = AnalyticsPeriod.DAYS_7,
    **kwargs
) -> Analytics:
    """创建分析数据"""
    return Analytics(
        video_id=video_id,
        views=views,
        period=period,
        **kwargs
    )
