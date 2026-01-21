#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块
提供 SQLite 持久化层，支持 ORM 和原生 SQL

引用规约：
- data.spec.md: 实体 Schema 定义、DDL
- sys.spec.md: 共享模块 Database 组件
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager

from .logger import setup_logger
from .config import get_config, get_data_dir

logger = setup_logger('database')


class Database:
    """
    SQLite 数据库管理类

    提供：
    - 连接池管理
    - 事务支持
    - CRUD 操作
    - Schema 初始化
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，为 None 时使用配置中的路径
        """
        if db_path is None:
            config = get_config()
            db_path = config.get('database.path', 'data/youtube_pipeline.db')

        # 处理相对路径
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = get_data_dir().parent / db_path

        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection: Optional[sqlite3.Connection] = None
        self._init_db()

        logger.info(f"数据库初始化完成: {self.db_path}")

    def _init_db(self):
        """初始化数据库 Schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 启用外键约束
            cursor.execute("PRAGMA foreign_keys = ON")

            # 创建表（基于 data.spec.md 中的 DDL）
            self._create_tables(cursor)

            conn.commit()

    def _create_tables(self, cursor: sqlite3.Cursor):
        """创建数据库表"""

        # 视频表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                youtube_id TEXT UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                file_path TEXT,
                duration INTEGER,
                resolution TEXT CHECK(resolution IN ('720p', '1080p', '4K')),
                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK(status IN ('draft', 'scripting', 'producing', 'ready', 'published', 'scheduled')),
                privacy TEXT NOT NULL DEFAULT 'private'
                    CHECK(privacy IN ('public', 'unlisted', 'private')),
                channel_id TEXT,
                spec_id TEXT,
                script_id TEXT,
                published_at DATETIME,
                scheduled_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 脚本表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                script_id TEXT PRIMARY KEY,
                video_id TEXT,
                version INTEGER DEFAULT 1,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                estimated_duration INTEGER,
                seo_score INTEGER CHECK(seo_score >= 0 AND seo_score <= 100),
                status TEXT DEFAULT 'draft'
                    CHECK(status IN ('draft', 'reviewing', 'approved', 'archived')),
                spec_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id),
                UNIQUE(video_id, version)
            )
        """)

        # 字幕表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtitles (
                subtitle_id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'zh',
                type TEXT DEFAULT 'auto' CHECK(type IN ('auto', 'manual', 'translated')),
                format TEXT DEFAULT 'vtt' CHECK(format IN ('srt', 'vtt', 'ass')),
                file_path TEXT NOT NULL,
                is_synced INTEGER DEFAULT 0,
                is_uploaded INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id),
                UNIQUE(video_id, language, type)
            )
        """)

        # 封面表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thumbnails (
                thumbnail_id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                is_active INTEGER DEFAULT 1,
                is_uploaded INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        """)

        # 规约表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS specs (
                spec_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                target_duration INTEGER NOT NULL,
                style TEXT CHECK(style IN ('tutorial', 'story', 'review', 'vlog', 'explainer')),
                event_1 TEXT,
                event_2 TEXT,
                event_3 TEXT,
                meaning TEXT,
                target_audience TEXT,
                cta TEXT,
                research_id TEXT,
                file_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 竞品视频表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                channel_name TEXT,
                channel_id TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                duration INTEGER,
                published_at DATETIME,
                tags TEXT,
                category TEXT,
                keyword_source TEXT,
                pattern_type TEXT CHECK(pattern_type IN
                    ('cognitive_impact', 'storytelling', 'knowledge_sharing', 'interaction_guide', 'unknown')),
                pattern_score REAL,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 数据分析表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                report_date DATE NOT NULL,
                period TEXT CHECK(period IN ('7d', '30d', 'lifetime')),
                views INTEGER DEFAULT 0,
                watch_time_minutes INTEGER DEFAULT 0,
                average_view_duration INTEGER,
                ctr REAL,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                subscribers_gained INTEGER DEFAULT 0,
                subscribers_lost INTEGER DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                unique_viewers INTEGER DEFAULT 0,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id),
                UNIQUE(video_id, report_date, period)
            )
        """)

        # 任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                video_id TEXT,
                stage TEXT NOT NULL CHECK(stage IN
                    ('research', 'planning', 'production', 'publishing', 'analytics')),
                type TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN
                    ('pending', 'running', 'completed', 'failed', 'cancelled')),
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        """)

        # 调研报告表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_reports (
                report_id TEXT PRIMARY KEY,
                keyword TEXT NOT NULL,
                region TEXT DEFAULT 'US',
                language TEXT DEFAULT 'zh',
                video_count INTEGER DEFAULT 0,
                insights TEXT,
                file_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_youtube_id ON videos(youtube_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scripts_video_id ON scripts(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scripts_status ON scripts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtitles_video_id ON subtitles(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_thumbnails_video_id ON thumbnails(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitor_keyword ON competitor_videos(keyword_source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitor_pattern ON competitor_videos(pattern_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_stage ON tasks(stage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")

        logger.debug("数据库表创建完成")

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"事务回滚: {e}")
                raise

    # ==================== 通用 CRUD 操作 ====================

    def insert(self, table: str, data: Dict[str, Any]) -> str:
        """
        插入记录

        Args:
            table: 表名
            data: 数据字典

        Returns:
            插入记录的 ID
        """
        # 处理 JSON 字段
        processed_data = self._process_json_fields(data)

        columns = ', '.join(processed_data.keys())
        placeholders = ', '.join(['?' for _ in processed_data])
        values = list(processed_data.values())

        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            return data.get(f'{table[:-1]}_id', cursor.lastrowid)

    def update(self, table: str, data: Dict[str, Any], where: str, params: Tuple = ()) -> int:
        """
        更新记录

        Args:
            table: 表名
            data: 更新数据
            where: WHERE 条件
            params: 条件参数

        Returns:
            影响的行数
        """
        processed_data = self._process_json_fields(data)
        processed_data['updated_at'] = datetime.now().isoformat()

        set_clause = ', '.join([f"{k} = ?" for k in processed_data.keys()])
        values = list(processed_data.values()) + list(params)

        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            return cursor.rowcount

    def delete(self, table: str, where: str, params: Tuple = ()) -> int:
        """
        删除记录

        Args:
            table: 表名
            where: WHERE 条件
            params: 条件参数

        Returns:
            删除的行数
        """
        sql = f"DELETE FROM {table} WHERE {where}"

        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.rowcount

    def find_one(self, table: str, where: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        查询单条记录

        Args:
            table: 表名
            where: WHERE 条件
            params: 条件参数

        Returns:
            记录字典或 None
        """
        sql = f"SELECT * FROM {table} WHERE {where} LIMIT 1"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def find_many(
        self,
        table: str,
        where: str = "1=1",
        params: Tuple = (),
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> List[Dict[str, Any]]:
        """
        查询多条记录

        Args:
            table: 表名
            where: WHERE 条件
            params: 条件参数
            order_by: 排序
            limit: 限制数量
            offset: 偏移量

        Returns:
            记录列表
        """
        sql = f"SELECT * FROM {table} WHERE {where}"

        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def count(self, table: str, where: str = "1=1", params: Tuple = ()) -> int:
        """
        统计记录数

        Args:
            table: 表名
            where: WHERE 条件
            params: 条件参数

        Returns:
            记录数
        """
        sql = f"SELECT COUNT(*) FROM {table} WHERE {where}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()[0]

    def execute(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        执行原生 SQL

        Args:
            sql: SQL 语句
            params: 参数

        Returns:
            结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
            else:
                conn.commit()
                return []

    # ==================== 辅助方法 ====================

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将 Row 对象转换为字典"""
        result = dict(row)
        # 解析 JSON 字段
        for key, value in result.items():
            if key == 'tags' and value:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass
            elif key in ('input_data', 'output_data') and value:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass
        return result

    def _process_json_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 JSON 字段"""
        result = data.copy()
        for key in ('tags', 'input_data', 'output_data'):
            if key in result and isinstance(result[key], (list, dict)):
                result[key] = json.dumps(result[key], ensure_ascii=False)
        return result

    # ==================== 便捷方法 ====================

    def generate_id(self) -> str:
        """生成 UUID"""
        return str(uuid.uuid4())

    # ==================== Video 相关操作 ====================

    def create_video(self, title: str, **kwargs) -> str:
        """创建视频记录"""
        video_id = self.generate_id()
        data = {
            'video_id': video_id,
            'title': title,
            'status': 'draft',
            'privacy': 'private',
            **kwargs
        }
        self.insert('videos', data)
        logger.info(f"创建视频: {video_id} - {title}")
        return video_id

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """获取视频"""
        return self.find_one('videos', 'video_id = ?', (video_id,))

    def get_video_by_youtube_id(self, youtube_id: str) -> Optional[Dict[str, Any]]:
        """通过 YouTube ID 获取视频"""
        return self.find_one('videos', 'youtube_id = ?', (youtube_id,))

    def update_video_status(self, video_id: str, status: str) -> int:
        """更新视频状态"""
        return self.update('videos', {'status': status}, 'video_id = ?', (video_id,))

    def list_videos(self, status: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """列出视频"""
        if status:
            return self.find_many('videos', 'status = ?', (status,), order_by='created_at DESC', limit=limit)
        return self.find_many('videos', order_by='created_at DESC', limit=limit)

    # ==================== Task 相关操作 ====================

    def create_task(self, stage: str, task_type: str, video_id: str = None, input_data: Dict = None) -> str:
        """创建任务"""
        task_id = self.generate_id()
        data = {
            'task_id': task_id,
            'stage': stage,
            'type': task_type,
            'video_id': video_id,
            'input_data': input_data,
            'status': 'pending'
        }
        self.insert('tasks', data)
        logger.info(f"创建任务: {task_id} - {stage}/{task_type}")
        return task_id

    def update_task_status(self, task_id: str, status: str, output_data: Dict = None, error_message: str = None) -> int:
        """更新任务状态"""
        data = {'status': status}
        if status == 'running':
            data['started_at'] = datetime.now().isoformat()
        elif status in ('completed', 'failed'):
            data['completed_at'] = datetime.now().isoformat()
        if output_data:
            data['output_data'] = output_data
        if error_message:
            data['error_message'] = error_message
        return self.update('tasks', data, 'task_id = ?', (task_id,))

    def get_pending_tasks(self, stage: str = None) -> List[Dict[str, Any]]:
        """获取待处理任务"""
        if stage:
            return self.find_many('tasks', 'status = ? AND stage = ?', ('pending', stage), order_by='created_at ASC')
        return self.find_many('tasks', 'status = ?', ('pending',), order_by='created_at ASC')

    # ==================== CompetitorVideo 相关操作 ====================

    def save_competitor_video(self, youtube_id: str, title: str, **kwargs) -> int:
        """保存竞品视频（存在则更新）"""
        existing = self.find_one('competitor_videos', 'youtube_id = ?', (youtube_id,))
        if existing:
            return self.update('competitor_videos', kwargs, 'youtube_id = ?', (youtube_id,))
        else:
            data = {'youtube_id': youtube_id, 'title': title, **kwargs}
            self.insert('competitor_videos', data)
            return 1

    def get_competitor_videos(self, keyword: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取竞品视频"""
        if keyword:
            return self.find_many('competitor_videos', 'keyword_source = ?', (keyword,), order_by='view_count DESC', limit=limit)
        return self.find_many('competitor_videos', order_by='view_count DESC', limit=limit)


# ==================== 全局实例 ====================

_global_db: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _global_db
    if _global_db is None:
        _global_db = Database()
    return _global_db


def reset_database(db_path: Optional[str] = None) -> Database:
    """重置数据库实例"""
    global _global_db
    _global_db = Database(db_path)
    return _global_db
