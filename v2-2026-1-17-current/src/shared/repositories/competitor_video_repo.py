#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CompetitorVideo Repository

提供竞品视频实体的数据库操作

引用规约：
- data.spec.md: 2.6 CompetitorVideo Schema, 5.1 SQLite DDL
"""

import json
import sqlite3
from src.shared.db_compat import get_connection as db_get_connection, is_using_neon
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.shared.logger import setup_logger
from src.shared.models import CompetitorVideo, PatternType


class CompetitorVideoRepository:
    """
    竞品视频数据库操作

    基于 data.spec.md 5.1 SQLite DDL
    """

    TABLE_NAME = "competitor_videos"

    # 建表 SQL（基于 data.spec.md）
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS competitor_videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        channel_name TEXT,
        view_count INTEGER DEFAULT 0,
        duration INTEGER,
        published_at TEXT,

        -- 第二层字段
        has_details INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        description TEXT,
        tags TEXT,
        channel_id TEXT,
        thumbnail_url TEXT,
        category TEXT,

        -- 调研相关
        theme TEXT,
        keyword_source TEXT,
        pattern_type TEXT DEFAULT 'unknown',
        pattern_score REAL,

        -- 时间
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """

    CREATE_INDEXES_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_cv_youtube_id ON competitor_videos(youtube_id)",
        "CREATE INDEX IF NOT EXISTS idx_cv_theme ON competitor_videos(theme)",
        "CREATE INDEX IF NOT EXISTS idx_cv_keyword ON competitor_videos(keyword_source)",
        "CREATE INDEX IF NOT EXISTS idx_cv_pattern ON competitor_videos(pattern_type)",
        "CREATE INDEX IF NOT EXISTS idx_cv_view_count ON competitor_videos(view_count DESC)",
    ]

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化 Repository

        Args:
            db_path: 数据库路径，默认 data/youtube_pipeline.db
        """
        self.logger = setup_logger('competitor_video_repo')

        if db_path is None:
            db_path = Path("data/youtube_pipeline.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        if is_using_neon():
            # Neon 表已由 neon_database.py 创建
            self.logger.info("使用 Neon PostgreSQL，跳过本地表初始化")
            return
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(self.CREATE_TABLE_SQL)
            for index_sql in self.CREATE_INDEXES_SQL:
                cursor.execute(index_sql)
            conn.commit()
        self.logger.info(f"数据库初始化完成: {self.db_path}")

    def _get_connection(self):
        """获取数据库连接"""
        return db_get_connection(str(self.db_path), row_factory=sqlite3.Row)

    # ============================================================
    # CRUD 操作
    # ============================================================

    def save(self, video: CompetitorVideo) -> int:
        """
        保存单个视频（插入或更新）

        Args:
            video: CompetitorVideo 实例

        Returns:
            记录 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 检查是否存在
            cursor.execute(
                "SELECT id FROM competitor_videos WHERE youtube_id = ?",
                (video.youtube_id,)
            )
            existing = cursor.fetchone()

            if existing:
                # 更新
                self._update(cursor, video, existing['id'])
                return existing['id']
            else:
                # 插入
                return self._insert(cursor, video)

    def _insert(self, cursor: sqlite3.Cursor, video: CompetitorVideo) -> int:
        """插入新记录"""
        sql = """
        INSERT INTO competitor_videos (
            youtube_id, title, channel_name, view_count, duration, published_at,
            has_details, like_count, comment_count, description, tags,
            channel_id, thumbnail_url, category,
            theme, keyword_source, pattern_type, pattern_score, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (
            video.youtube_id,
            video.title,
            video.channel_name,
            video.view_count,
            video.duration,
            video.published_at.isoformat() if video.published_at else None,
            video.has_details,  # PostgreSQL psycopg2 可以处理 Python bool
            video.like_count,
            video.comment_count,
            video.description,
            json.dumps(video.tags, ensure_ascii=False) if video.tags else None,
            video.channel_id,
            video.thumbnail_url,
            video.category,
            getattr(video, 'theme', None),
            video.keyword_source,
            video.pattern_type.value,
            video.pattern_score,
            video.collected_at.isoformat(),
        ))
        return cursor.lastrowid

    def _update(self, cursor: sqlite3.Cursor, video: CompetitorVideo, record_id: int):
        """更新现有记录"""
        sql = """
        UPDATE competitor_videos SET
            title = ?, channel_name = ?, view_count = ?, duration = ?, published_at = ?,
            has_details = ?, like_count = ?, comment_count = ?, description = ?, tags = ?,
            channel_id = ?, thumbnail_url = ?, category = ?,
            theme = COALESCE(theme, ?),
            keyword_source = COALESCE(keyword_source, ?),
            pattern_type = ?, pattern_score = ?,
            updated_at = ?
        WHERE id = ?
        """
        cursor.execute(sql, (
            video.title,
            video.channel_name,
            video.view_count,
            video.duration,
            video.published_at.isoformat() if video.published_at else None,
            video.has_details,  # PostgreSQL psycopg2 可以处理 Python bool
            video.like_count,
            video.comment_count,
            video.description,
            json.dumps(video.tags, ensure_ascii=False) if video.tags else None,
            video.channel_id,
            video.thumbnail_url,
            video.category,
            getattr(video, 'theme', None),
            video.keyword_source,
            video.pattern_type.value,
            video.pattern_score,
            datetime.now().isoformat(),
            record_id,
        ))

    def save_batch(self, videos: List[CompetitorVideo]) -> Tuple[int, int]:
        """
        批量保存视频

        Args:
            videos: CompetitorVideo 列表

        Returns:
            (inserted_count, updated_count)
        """
        inserted = 0
        updated = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for video in videos:
                cursor.execute(
                    "SELECT id FROM competitor_videos WHERE youtube_id = ?",
                    (video.youtube_id,)
                )
                existing = cursor.fetchone()

                if existing:
                    self._update(cursor, video, existing['id'])
                    updated += 1
                else:
                    self._insert(cursor, video)
                    inserted += 1

            conn.commit()

        self.logger.info(f"批量保存完成: 插入 {inserted}, 更新 {updated}")
        return inserted, updated

    def find_by_youtube_id(self, youtube_id: str) -> Optional[CompetitorVideo]:
        """
        根据 YouTube ID 查找视频

        Args:
            youtube_id: YouTube 视频 ID

        Returns:
            CompetitorVideo 或 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM competitor_videos WHERE youtube_id = ?",
                (youtube_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_model(row)
            return None

    def exists(self, youtube_id: str) -> bool:
        """检查视频是否已存在"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM competitor_videos WHERE youtube_id = ?",
                (youtube_id,)
            )
            return cursor.fetchone() is not None

    def exists_batch(self, youtube_ids: List[str]) -> set:
        """
        批量检查视频是否存在

        Args:
            youtube_ids: YouTube ID 列表

        Returns:
            已存在的 ID 集合
        """
        if not youtube_ids:
            return set()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(youtube_ids))
            cursor.execute(
                f"SELECT youtube_id FROM competitor_videos WHERE youtube_id IN ({placeholders})",
                youtube_ids
            )
            return {row['youtube_id'] for row in cursor.fetchall()}

    def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        theme: Optional[str] = None,
        keyword: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        keyword_like: Optional[str] = None,
        min_views: Optional[int] = None,
        has_details: Optional[bool] = None,
        pattern_type: Optional[PatternType] = None
    ) -> List[CompetitorVideo]:
        """
        查询视频列表

        Args:
            limit: 返回数量限制
            offset: 偏移量
            theme: 按主题精确筛选（如"养生"、"科技"）
            keyword: 按关键词精确筛选（单个）
            keywords: 按多个关键词筛选（列表，OR 关系）
            keyword_like: 按关键词模糊筛选（包含）
            min_views: 最小播放量
            has_details: 是否有详情
            pattern_type: 模式类型

        Returns:
            CompetitorVideo 列表
        """
        conditions = []
        params = []

        # 主题筛选（优先级最高）
        if theme:
            conditions.append("theme = ?")
            params.append(theme)

        # 关键词筛选（三种方式）
        if keywords and len(keywords) > 0:
            # 多关键词 OR 查询
            placeholders = ','.join('?' * len(keywords))
            conditions.append(f"keyword_source IN ({placeholders})")
            params.extend(keywords)
        elif keyword:
            # 单关键词精确匹配
            conditions.append("keyword_source = ?")
            params.append(keyword)
        elif keyword_like:
            # 模糊匹配（包含关键词）
            conditions.append("keyword_source LIKE ?")
            params.append(f"%{keyword_like}%")

        if min_views is not None:
            conditions.append("view_count >= ?")
            params.append(min_views)

        if has_details is not None:
            # PostgreSQL 使用布尔值，SQLite 兼容 true/false 作为关键字
            if has_details:
                conditions.append("has_details = true")
            else:
                conditions.append("has_details = false")

        if pattern_type:
            conditions.append("pattern_type = ?")
            params.append(pattern_type.value)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
        SELECT * FROM competitor_videos
        WHERE {where_clause}
        ORDER BY view_count DESC
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]

    def find_without_details(self, min_views: int = 0, limit: int = 100) -> List[CompetitorVideo]:
        """
        查找没有详情的高播放量视频（用于第二阶段采集）

        Args:
            min_views: 最小播放量阈值
            limit: 返回数量

        Returns:
            需要获取详情的视频列表
        """
        sql = """
        SELECT * FROM competitor_videos
        WHERE NOT has_details AND view_count >= ?
        ORDER BY view_count DESC
        LIMIT ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (min_views, limit))
            return [self._row_to_model(row) for row in cursor.fetchall()]

    def count(self, keyword: Optional[str] = None) -> int:
        """
        统计视频数量

        Args:
            keyword: 按关键词筛选

        Returns:
            数量
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if keyword:
                cursor.execute(
                    "SELECT COUNT(*) FROM competitor_videos WHERE keyword_source = ?",
                    (keyword,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM competitor_videos")
            return cursor.fetchone()[0]

    def update_pattern(
        self,
        youtube_id: str,
        pattern_type: PatternType,
        pattern_score: float
    ) -> bool:
        """
        更新模式分析结果

        Args:
            youtube_id: YouTube 视频 ID
            pattern_type: 模式类型
            pattern_score: 模式得分

        Returns:
            是否更新成功
        """
        sql = """
        UPDATE competitor_videos
        SET pattern_type = ?, pattern_score = ?, updated_at = ?
        WHERE youtube_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                pattern_type.value,
                pattern_score,
                datetime.now().isoformat(),
                youtube_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def update_details(self, video: CompetitorVideo) -> bool:
        """
        更新视频详情（第二阶段采集后调用）

        Args:
            video: 包含详情的 CompetitorVideo

        Returns:
            是否更新成功
        """
        sql = """
        UPDATE competitor_videos SET
            has_details = true,
            like_count = ?,
            comment_count = ?,
            description = ?,
            tags = ?,
            channel_id = ?,
            channel_name = COALESCE(NULLIF(channel_name, ''), ?),
            thumbnail_url = ?,
            category = ?,
            subscriber_count = ?,
            updated_at = ?
        WHERE youtube_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                video.like_count,
                video.comment_count,
                video.description,
                json.dumps(video.tags, ensure_ascii=False) if video.tags else None,
                video.channel_id,
                video.channel_name,
                video.thumbnail_url,
                video.category,
                video.subscriber_count,
                datetime.now().isoformat(),
                video.youtube_id,
            ))
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, youtube_id: str) -> bool:
        """删除视频"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM competitor_videos WHERE youtube_id = ?",
                (youtube_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_statistics(self, keyword: Optional[str] = None) -> dict:
        """
        获取统计信息

        Args:
            keyword: 按关键词筛选

        Returns:
            统计数据
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            where_clause = "WHERE keyword_source = ?" if keyword else ""
            params = (keyword,) if keyword else ()

            # 总数和详情数
            # 使用 CASE WHEN has_details THEN 1 ELSE 0 END 兼容 PostgreSQL 和 SQLite
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN has_details THEN 1 ELSE 0 END) as with_details,
                    SUM(view_count) as total_views,
                    AVG(view_count) as avg_views,
                    MAX(view_count) as max_views,
                    AVG(duration) as avg_duration
                FROM competitor_videos {where_clause}
            """, params)
            row = cursor.fetchone()

            # 模式分布
            cursor.execute(f"""
                SELECT pattern_type, COUNT(*) as count
                FROM competitor_videos {where_clause}
                GROUP BY pattern_type
            """, params)
            pattern_dist = {r['pattern_type']: r['count'] for r in cursor.fetchall()}

            return {
                'total': row['total'] or 0,
                'with_details': row['with_details'] or 0,
                'total_views': row['total_views'] or 0,
                'avg_views': int(row['avg_views'] or 0),
                'max_views': row['max_views'] or 0,
                'avg_duration': int(row['avg_duration'] or 0),
                'pattern_distribution': pattern_dist,
            }

    def _row_to_model(self, row: sqlite3.Row) -> CompetitorVideo:
        """将数据库行转换为模型"""
        data = {
            'id': row['id'],
            'youtube_id': row['youtube_id'],
            'title': row['title'],
            'channel_name': row['channel_name'],
            'view_count': row['view_count'],
            'duration': row['duration'],
            'published_at': row['published_at'],
            'has_details': bool(row['has_details']),
            'like_count': row['like_count'],
            'comment_count': row['comment_count'],
            'description': row['description'],
            'tags': row['tags'],
            'channel_id': row['channel_id'],
            'thumbnail_url': row['thumbnail_url'],
            'category': row['category'],
            'subscriber_count': row['subscriber_count'] if 'subscriber_count' in row.keys() else 0,
            'keyword_source': row['keyword_source'],
            'pattern_type': row['pattern_type'],
            'pattern_score': row['pattern_score'],
            'collected_at': row['collected_at'],
        }
        # 添加 theme 字段（兼容旧数据）
        try:
            data['theme'] = row['theme']
        except (IndexError, KeyError):
            data['theme'] = None
        return CompetitorVideo.from_dict(data)


# 便捷函数
def get_repository(db_path: Optional[str] = None) -> CompetitorVideoRepository:
    """获取 Repository 实例"""
    return CompetitorVideoRepository(db_path)
