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
from datetime import datetime, timedelta
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

        # ========== 监控相关表 ==========

        # 监控任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitor_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                description TEXT,
                frequency TEXT DEFAULT 'daily',
                max_results INTEGER DEFAULT 500,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_run_at DATETIME,
                next_run_at DATETIME
            )
        """)

        # 视频快照表（每次采集的数据）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                video_id TEXT NOT NULL,
                title TEXT,
                channel_name TEXT,
                channel_id TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                duration INTEGER DEFAULT 0,
                published_at TEXT,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES monitor_tasks(id)
            )
        """)

        # 视频增长记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_growth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                task_id INTEGER,
                date TEXT NOT NULL,
                views_today INTEGER DEFAULT 0,
                views_yesterday INTEGER DEFAULT 0,
                views_growth INTEGER DEFAULT 0,
                growth_rate REAL DEFAULT 0,
                is_trending BOOLEAN DEFAULT 0,
                UNIQUE(video_id, date)
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
        # 监控表索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_snapshots_video_id ON video_snapshots(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_snapshots_collected_at ON video_snapshots(collected_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_growth_date ON video_growth(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_growth_trending ON video_growth(is_trending)")

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

    # ==================== 监控任务相关操作 ====================

    def create_monitor_task(self, keyword: str, description: str = None,
                           frequency: str = 'daily', max_results: int = 500) -> int:
        """
        创建监控任务

        Args:
            keyword: 搜索关键词
            description: 任务描述
            frequency: 采集频率 (hourly/daily/weekly)
            max_results: 最大采集数量

        Returns:
            任务ID
        """
        from datetime import timedelta

        # 计算下次运行时间
        now = datetime.now()
        if frequency == 'hourly':
            next_run = now + timedelta(hours=1)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        else:  # daily
            next_run = now + timedelta(days=1)

        data = {
            'keyword': keyword,
            'description': description or f'监控关键词: {keyword}',
            'frequency': frequency,
            'max_results': max_results,
            'is_active': 1,
            'next_run_at': next_run.isoformat()
        }

        result = self.insert('monitor_tasks', data)
        logger.info(f"创建监控任务: {keyword} (频率: {frequency})")
        return result

    def get_monitor_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取单个监控任务"""
        return self.find_one('monitor_tasks', 'id = ?', (task_id,))

    def get_monitor_task_by_keyword(self, keyword: str) -> Optional[Dict[str, Any]]:
        """通过关键词获取监控任务"""
        return self.find_one('monitor_tasks', 'keyword = ?', (keyword,))

    def list_monitor_tasks(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """列出所有监控任务"""
        if active_only:
            return self.find_many('monitor_tasks', 'is_active = 1', order_by='created_at DESC')
        return self.find_many('monitor_tasks', order_by='created_at DESC')

    def update_monitor_task(self, task_id: int, **kwargs) -> int:
        """更新监控任务（不自动添加 updated_at）"""
        if not kwargs:
            return 0

        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [task_id]

        sql = f"UPDATE monitor_tasks SET {set_clause} WHERE id = ?"

        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            return cursor.rowcount

    def update_monitor_task_last_run(self, task_id: int) -> int:
        """更新监控任务的最后运行时间"""
        task = self.get_monitor_task(task_id)
        if not task:
            return 0

        now = datetime.now()
        frequency = task.get('frequency', 'daily')

        if frequency == 'hourly':
            next_run = now + timedelta(hours=1)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        else:
            next_run = now + timedelta(days=1)

        sql = """
            UPDATE monitor_tasks
            SET last_run_at = ?, next_run_at = ?
            WHERE id = ?
        """

        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (now.isoformat(), next_run.isoformat(), task_id))
            return cursor.rowcount

    def delete_monitor_task(self, task_id: int) -> int:
        """删除监控任务"""
        return self.delete('monitor_tasks', 'id = ?', (task_id,))

    def toggle_monitor_task(self, task_id: int) -> int:
        """切换监控任务的激活状态"""
        task = self.get_monitor_task(task_id)
        if not task:
            return 0
        new_status = 0 if task['is_active'] else 1
        return self.update_monitor_task(task_id, is_active=new_status)

    def get_due_monitor_tasks(self) -> List[Dict[str, Any]]:
        """获取需要运行的监控任务（已到执行时间）"""
        now = datetime.now().isoformat()
        return self.find_many(
            'monitor_tasks',
            'is_active = 1 AND (next_run_at IS NULL OR next_run_at <= ?)',
            (now,),
            order_by='next_run_at ASC'
        )

    # ==================== 视频快照相关操作 ====================

    def save_video_snapshot(self, task_id: int, video_data: Dict[str, Any]) -> int:
        """
        保存视频快照

        Args:
            task_id: 监控任务ID
            video_data: 视频数据

        Returns:
            快照ID
        """
        data = {
            'task_id': task_id,
            'video_id': video_data.get('video_id') or video_data.get('id'),
            'title': video_data.get('title'),
            'channel_name': video_data.get('channel_name') or video_data.get('uploader'),
            'channel_id': video_data.get('channel_id'),
            'view_count': video_data.get('view_count', 0),
            'like_count': video_data.get('like_count', 0),
            'comment_count': video_data.get('comment_count', 0),
            'duration': video_data.get('duration', 0),
            'published_at': video_data.get('published_at') or video_data.get('upload_date')
        }
        return self.insert('video_snapshots', data)

    def save_video_snapshots_batch(self, task_id: int, videos: List[Dict[str, Any]]) -> int:
        """批量保存视频快照"""
        count = 0
        for video in videos:
            try:
                self.save_video_snapshot(task_id, video)
                count += 1
            except Exception as e:
                logger.error(f"保存视频快照失败: {video.get('video_id')} - {e}")
        logger.info(f"批量保存视频快照: {count}/{len(videos)}")
        return count

    def get_video_snapshots(self, task_id: int = None, video_id: str = None,
                           date: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取视频快照"""
        conditions = []
        params = []

        if task_id:
            conditions.append('task_id = ?')
            params.append(task_id)
        if video_id:
            conditions.append('video_id = ?')
            params.append(video_id)
        if date:
            conditions.append('DATE(collected_at) = ?')
            params.append(date)

        where = ' AND '.join(conditions) if conditions else '1=1'
        return self.find_many('video_snapshots', where, tuple(params),
                             order_by='collected_at DESC', limit=limit)

    def get_latest_snapshot(self, video_id: str) -> Optional[Dict[str, Any]]:
        """获取视频的最新快照"""
        snapshots = self.get_video_snapshots(video_id=video_id, limit=1)
        return snapshots[0] if snapshots else None

    def get_previous_snapshot(self, video_id: str, before_date: str = None) -> Optional[Dict[str, Any]]:
        """获取视频的前一个快照"""
        if before_date is None:
            before_date = datetime.now().strftime('%Y-%m-%d')

        sql = """
            SELECT * FROM video_snapshots
            WHERE video_id = ? AND DATE(collected_at) < ?
            ORDER BY collected_at DESC LIMIT 1
        """
        results = self.execute(sql, (video_id, before_date))
        return results[0] if results else None

    # ==================== 视频增长相关操作 ====================

    def save_video_growth(self, video_id: str, task_id: int,
                         views_today: int, views_yesterday: int) -> int:
        """
        保存视频增长数据

        Args:
            video_id: 视频ID
            task_id: 监控任务ID
            views_today: 今日播放量
            views_yesterday: 昨日播放量
        """
        today = datetime.now().strftime('%Y-%m-%d')
        views_growth = views_today - views_yesterday
        growth_rate = (views_growth / views_yesterday * 100) if views_yesterday > 0 else 0

        # 判断是否趋势上升（增长>1000 或 增长率>10%）
        is_trending = views_growth > 1000 or growth_rate > 10

        data = {
            'video_id': video_id,
            'task_id': task_id,
            'date': today,
            'views_today': views_today,
            'views_yesterday': views_yesterday,
            'views_growth': views_growth,
            'growth_rate': round(growth_rate, 2),
            'is_trending': 1 if is_trending else 0
        }

        # 使用 INSERT OR REPLACE 来处理唯一约束
        sql = """
            INSERT OR REPLACE INTO video_growth
            (video_id, task_id, date, views_today, views_yesterday, views_growth, growth_rate, is_trending)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                video_id, task_id, today, views_today, views_yesterday,
                views_growth, round(growth_rate, 2), 1 if is_trending else 0
            ))
            return cursor.lastrowid

    def get_video_growth(self, video_id: str = None, task_id: int = None,
                        date: str = None, trending_only: bool = False,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """获取视频增长数据"""
        conditions = []
        params = []

        if video_id:
            conditions.append('video_id = ?')
            params.append(video_id)
        if task_id:
            conditions.append('task_id = ?')
            params.append(task_id)
        if date:
            conditions.append('date = ?')
            params.append(date)
        if trending_only:
            conditions.append('is_trending = 1')

        where = ' AND '.join(conditions) if conditions else '1=1'
        return self.find_many('video_growth', where, tuple(params),
                             order_by='views_growth DESC', limit=limit)

    def get_trending_videos(self, task_id: int = None, days: int = 7,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取趋势视频（近N天内增长明显的视频）
        """
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        conditions = ['is_trending = 1', 'date >= ?']
        params = [start_date]

        if task_id:
            conditions.append('task_id = ?')
            params.append(task_id)

        where = ' AND '.join(conditions)

        # 按总增长量排序
        sql = f"""
            SELECT video_id,
                   SUM(views_growth) as total_growth,
                   AVG(growth_rate) as avg_growth_rate,
                   COUNT(*) as trending_days
            FROM video_growth
            WHERE {where}
            GROUP BY video_id
            ORDER BY total_growth DESC
            LIMIT ?
        """
        params.append(limit)
        return self.execute(sql, tuple(params))

    def calculate_and_save_growth(self, task_id: int) -> int:
        """
        计算并保存所有视频的增长数据

        对比今天和昨天的快照，计算增长
        """
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # 获取今天的快照
        today_snapshots = self.get_video_snapshots(task_id=task_id, date=today)

        count = 0
        for snapshot in today_snapshots:
            video_id = snapshot['video_id']
            views_today = snapshot['view_count']

            # 获取昨天的快照
            prev = self.get_previous_snapshot(video_id, today)
            views_yesterday = prev['view_count'] if prev else 0

            self.save_video_growth(video_id, task_id, views_today, views_yesterday)
            count += 1

        logger.info(f"计算增长数据完成: {count} 个视频")
        return count

    def get_growth_summary(self, task_id: int, days: int = 7) -> Dict[str, Any]:
        """
        获取增长摘要统计
        """
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        sql = """
            SELECT
                COUNT(DISTINCT video_id) as total_videos,
                SUM(views_growth) as total_growth,
                AVG(views_growth) as avg_growth,
                SUM(CASE WHEN is_trending = 1 THEN 1 ELSE 0 END) as trending_count
            FROM video_growth
            WHERE task_id = ? AND date >= ?
        """
        results = self.execute(sql, (task_id, start_date))
        return results[0] if results else {}


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
