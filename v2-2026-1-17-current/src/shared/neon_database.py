#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neon PostgreSQL 数据库模块

提供连接 Neon 云数据库的能力，支持 Vercel 无服务器部署。
使用 SQLAlchemy ORM + asyncpg 异步驱动。

配置方式:
1. 环境变量: DATABASE_URL
2. .env 文件: DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
"""

import os
from datetime import datetime
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import NullPool

from dotenv import load_dotenv

from .logger import setup_logger

# 加载环境变量
load_dotenv()

logger = setup_logger('neon_database')

# SQLAlchemy 基类
Base = declarative_base()


# ==================== ORM 模型定义 ====================

class Video(Base):
    """视频表"""
    __tablename__ = 'videos'

    video_id = Column(String(36), primary_key=True)
    youtube_id = Column(String(20), unique=True, nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON 字符串
    file_path = Column(String(500), nullable=True)
    duration = Column(Integer, nullable=True)
    resolution = Column(String(10), nullable=True)  # 720p, 1080p, 4K
    status = Column(String(20), nullable=False, default='draft')
    privacy = Column(String(20), nullable=False, default='private')
    channel_id = Column(String(50), nullable=True)
    spec_id = Column(String(36), nullable=True)
    script_id = Column(String(36), nullable=True)
    published_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    scripts = relationship("Script", back_populates="video")
    subtitles = relationship("Subtitle", back_populates="video")
    thumbnails = relationship("Thumbnail", back_populates="video")


class Script(Base):
    """脚本表"""
    __tablename__ = 'scripts'

    script_id = Column(String(36), primary_key=True)
    video_id = Column(String(36), ForeignKey('videos.video_id'), nullable=True)
    version = Column(Integer, default=1)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=True)
    estimated_duration = Column(Integer, nullable=True)
    seo_score = Column(Integer, nullable=True)
    status = Column(String(20), default='draft')
    spec_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    video = relationship("Video", back_populates="scripts")


class Subtitle(Base):
    """字幕表"""
    __tablename__ = 'subtitles'

    subtitle_id = Column(String(36), primary_key=True)
    video_id = Column(String(36), ForeignKey('videos.video_id'), nullable=False)
    language = Column(String(10), nullable=False, default='zh')
    type = Column(String(20), default='auto')  # auto, manual, translated
    format = Column(String(10), default='vtt')  # srt, vtt, ass
    file_path = Column(String(500), nullable=False)
    is_synced = Column(Boolean, default=False)
    is_uploaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="subtitles")


class Thumbnail(Base):
    """封面表"""
    __tablename__ = 'thumbnails'

    thumbnail_id = Column(String(36), primary_key=True)
    video_id = Column(String(36), ForeignKey('videos.video_id'), nullable=False)
    file_path = Column(String(500), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    is_uploaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="thumbnails")


class Spec(Base):
    """规约表"""
    __tablename__ = 'specs'

    spec_id = Column(String(36), primary_key=True)
    topic = Column(String(500), nullable=False)
    target_duration = Column(Integer, nullable=False)
    style = Column(String(20), nullable=True)  # tutorial, story, review, vlog, explainer
    event_1 = Column(Text, nullable=True)
    event_2 = Column(Text, nullable=True)
    event_3 = Column(Text, nullable=True)
    meaning = Column(Text, nullable=True)
    target_audience = Column(String(200), nullable=True)
    cta = Column(String(200), nullable=True)
    research_id = Column(String(36), nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompetitorVideo(Base):
    """竞品视频表 - 核心数据表"""
    __tablename__ = 'competitor_videos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_id = Column(String(20), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    channel_name = Column(String(200), nullable=True)
    channel_id = Column(String(50), nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    duration = Column(Integer, nullable=True)  # 秒
    published_at = Column(DateTime, nullable=True)
    tags = Column(Text, nullable=True)  # JSON 字符串
    category = Column(String(100), nullable=True)
    keyword_source = Column(String(200), nullable=True)
    pattern_type = Column(String(50), nullable=True)
    pattern_score = Column(Float, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    theme = Column(String(200), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    has_details = Column(Boolean, default=False)

    # 扩展字段（用于洞察分析）
    subscriber_count = Column(Integer, nullable=True)
    region = Column(String(50), nullable=True)
    language = Column(String(10), nullable=True)
    is_ai_generated = Column(Boolean, nullable=True)
    engagement_rate = Column(Float, nullable=True)


class Analytics(Base):
    """数据分析表"""
    __tablename__ = 'analytics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(36), ForeignKey('videos.video_id'), nullable=False)
    report_date = Column(DateTime, nullable=False)
    period = Column(String(20), nullable=True)  # 7d, 30d, lifetime
    views = Column(Integer, default=0)
    watch_time_minutes = Column(Integer, default=0)
    average_view_duration = Column(Integer, nullable=True)
    ctr = Column(Float, nullable=True)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    subscribers_gained = Column(Integer, default=0)
    subscribers_lost = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)
    collected_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    """任务表"""
    __tablename__ = 'tasks'

    task_id = Column(String(36), primary_key=True)
    video_id = Column(String(36), ForeignKey('videos.video_id'), nullable=True)
    stage = Column(String(20), nullable=False)  # research, planning, production, publishing, analytics
    type = Column(String(50), nullable=False)
    status = Column(String(20), default='pending')  # pending, running, completed, failed, cancelled
    input_data = Column(Text, nullable=True)  # JSON
    output_data = Column(Text, nullable=True)  # JSON
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ResearchReport(Base):
    """调研报告表"""
    __tablename__ = 'research_reports'

    report_id = Column(String(36), primary_key=True)
    keyword = Column(String(200), nullable=False)
    region = Column(String(10), default='US')
    language = Column(String(10), default='zh')
    video_count = Column(Integer, default=0)
    insights = Column(Text, nullable=True)  # JSON
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Channel(Base):
    """频道表"""
    __tablename__ = 'channels'

    channel_id = Column(String(50), primary_key=True)
    channel_name = Column(String(200), nullable=True)
    handle = Column(String(100), nullable=True)
    subscriber_count = Column(BigInteger, nullable=True)  # 订阅数可能很大
    video_count = Column(Integer, nullable=True)
    total_views = Column(BigInteger, nullable=True)  # 总播放量可能超过21亿
    country = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(String(20), nullable=True)
    canonical_url = Column(String(500), nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class VideoComment(Base):
    """视频评论表"""
    __tablename__ = 'video_comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_id = Column(String(20), nullable=False)
    comment_id = Column(String(50), nullable=True)
    text = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    author_id = Column(String(50), nullable=True)
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_favorited = Column(Boolean, default=False)
    published_at = Column(String(50), nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)


class VideoStatsHistory(Base):
    """视频统计历史表"""
    __tablename__ = 'video_stats_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_id = Column(String(20), nullable=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    view_count_delta = Column(Integer, nullable=True)
    hours_since_last = Column(Integer, nullable=True)
    growth_rate = Column(Float, nullable=True)


class VideoMonitoring(Base):
    """视频监控表"""
    __tablename__ = 'video_monitoring'

    youtube_id = Column(String(20), primary_key=True)
    monitoring_tier = Column(String(20), nullable=True)
    is_potential = Column(Boolean, default=False)
    last_growth_rate = Column(Float, nullable=True)
    avg_growth_rate = Column(Float, nullable=True)
    growth_acceleration = Column(Float, nullable=True)
    viral_score = Column(Float, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    next_check_at = Column(DateTime, nullable=True)
    check_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class WatchedChannel(Base):
    """关注频道表"""
    __tablename__ = 'watched_channels'

    channel_id = Column(String(50), primary_key=True)
    channel_name = Column(String(200), nullable=True)
    channel_url = Column(String(500), nullable=True)
    priority = Column(String(20), nullable=True)
    watch_reason = Column(Text, nullable=True)
    check_interval_minutes = Column(Integer, default=60)
    last_video_id = Column(String(20), nullable=True)
    last_video_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    avg_videos_per_week = Column(Float, nullable=True)
    interested_topics = Column(Text, nullable=True)
    total_videos_tracked = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class ChannelPublication(Base):
    """频道发布表"""
    __tablename__ = 'channel_publications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(50), nullable=False)
    youtube_id = Column(String(20), nullable=False)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    duration = Column(Integer, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    extracted_keywords = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=True)
    topic_match_score = Column(Float, nullable=True)
    initial_view_count = Column(Integer, nullable=True)
    initial_like_count = Column(Integer, nullable=True)


class ChannelAlert(Base):
    """频道预警表"""
    __tablename__ = 'channel_alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(50), nullable=False)
    youtube_id = Column(String(20), nullable=True)
    alert_type = Column(String(50), nullable=True)
    alert_level = Column(String(20), nullable=True)
    alert_message = Column(Text, nullable=True)
    alert_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)


class SearchTrend(Base):
    """搜索趋势表"""
    __tablename__ = 'search_trends'

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False)
    geo = Column(String(10), nullable=True)
    date = Column(String(20), nullable=True)
    interest = Column(Integer, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)


class TrendAnalysis(Base):
    """趋势分析表"""
    __tablename__ = 'trend_analysis'

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False)
    geo = Column(String(10), nullable=True)
    avg_interest = Column(Float, nullable=True)
    trend_direction = Column(String(20), nullable=True)
    trend_change_pct = Column(Float, nullable=True)
    yt_video_count = Column(Integer, nullable=True)
    yt_total_views = Column(Integer, nullable=True)
    yt_avg_views = Column(Integer, nullable=True)
    opportunity_score = Column(Float, nullable=True)
    opportunity_reason = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)


class MultilangVideo(Base):
    """多语言视频表"""
    __tablename__ = 'multilang_videos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_id = Column(String(20), nullable=False)
    title = Column(String(500), nullable=True)
    channel_name = Column(String(200), nullable=True)
    channel_id = Column(String(50), nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    duration = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)
    geo = Column(String(10), nullable=True)
    topic = Column(String(200), nullable=True)
    search_keyword = Column(String(200), nullable=True)
    published_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)


# ==================== 数据库连接管理 ====================

class NeonDatabase:
    """
    Neon PostgreSQL 数据库管理类

    支持:
    - 同步连接 (用于迁移、CLI)
    - 异步连接 (用于 FastAPI)
    - 连接池管理 (Vercel 无服务器兼容)
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        初始化 Neon 数据库连接

        Args:
            database_url: PostgreSQL 连接字符串，格式:
                postgresql://user:password@host/dbname?sslmode=require
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')

        if not self.database_url:
            logger.warning("未配置 DATABASE_URL，将使用本地 SQLite")
            self.database_url = "sqlite:///data/youtube_pipeline.db"
            self.is_neon = False
        else:
            self.is_neon = 'neon' in self.database_url or 'postgresql' in self.database_url

        # 同步引擎
        self._sync_engine = None
        self._sync_session_factory = None

        # 异步引擎
        self._async_engine = None
        self._async_session_factory = None

        logger.info(f"数据库类型: {'Neon PostgreSQL' if self.is_neon else 'SQLite'}")

    def _get_async_url(self) -> str:
        """转换为异步连接 URL"""
        if self.database_url.startswith('postgresql://'):
            return self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        elif self.database_url.startswith('postgres://'):
            return self.database_url.replace('postgres://', 'postgresql+asyncpg://')
        return self.database_url

    @property
    def sync_engine(self):
        """获取同步引擎"""
        if self._sync_engine is None:
            # Vercel 无服务器环境使用 NullPool
            self._sync_engine = create_engine(
                self.database_url,
                poolclass=NullPool if self.is_neon else None,
                echo=False
            )
        return self._sync_engine

    @property
    def async_engine(self):
        """获取异步引擎"""
        if self._async_engine is None:
            async_url = self._get_async_url()
            self._async_engine = create_async_engine(
                async_url,
                poolclass=NullPool if self.is_neon else None,
                echo=False
            )
        return self._async_engine

    @property
    def sync_session_factory(self):
        """获取同步会话工厂"""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                expire_on_commit=False
            )
        return self._sync_session_factory

    @property
    def async_session_factory(self):
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                expire_on_commit=False
            )
        return self._async_session_factory

    def create_tables(self):
        """创建所有表（同步）"""
        Base.metadata.create_all(self.sync_engine)
        logger.info("数据库表创建完成")

    async def create_tables_async(self):
        """创建所有表（异步）"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成（异步）")

    def get_session(self):
        """获取同步会话（上下文管理器）"""
        return self.sync_session_factory()

    @asynccontextmanager
    async def get_async_session(self):
        """获取异步会话（上下文管理器）"""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"数据库事务失败: {e}")
                raise

    def close(self):
        """关闭连接"""
        if self._sync_engine:
            self._sync_engine.dispose()
        if self._async_engine:
            # 异步引擎需要在事件循环中关闭
            pass


# ==================== 全局实例 ====================

_neon_db: Optional[NeonDatabase] = None


def get_neon_database() -> NeonDatabase:
    """获取全局 Neon 数据库实例"""
    global _neon_db
    if _neon_db is None:
        _neon_db = NeonDatabase()
    return _neon_db


def init_neon_database(database_url: Optional[str] = None) -> NeonDatabase:
    """初始化 Neon 数据库（创建表）"""
    global _neon_db
    _neon_db = NeonDatabase(database_url)
    _neon_db.create_tables()
    return _neon_db


# ==================== FastAPI 依赖注入 ====================

async def get_db_session():
    """FastAPI 依赖：获取数据库会话"""
    db = get_neon_database()
    async with db.get_async_session() as session:
        yield session
