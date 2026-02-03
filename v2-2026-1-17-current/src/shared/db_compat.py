#!/usr/bin/env python3
"""
数据库兼容层

当设置了 DATABASE_URL 环境变量时使用 PostgreSQL（通过 SQLAlchemy），
否则回退到 SQLite。提供 sqlite3 兼容的接口，让上层代码无需修改 SQL。
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

_database_url = None


def get_database_url() -> Optional[str]:
    """获取 DATABASE_URL"""
    global _database_url
    if _database_url is None:
        _database_url = os.getenv('DATABASE_URL', '')
    return _database_url if _database_url else None


def is_using_neon() -> bool:
    """是否使用 Neon PostgreSQL"""
    url = get_database_url()
    return bool(url and ('postgresql' in url or 'postgres' in url))


def _convert_sql(sql: str) -> str:
    """将 SQLite 风格 SQL 转换为 PostgreSQL 兼容格式
    - ? 占位符 -> %s
    - COALESCE 等函数保持不变
    """
    # 简单替换 ? -> %s（忽略字符串内的 ?）
    result = []
    in_string = False
    string_char = None
    for ch in sql:
        if not in_string:
            if ch in ("'", '"'):
                in_string = True
                string_char = ch
                result.append(ch)
            elif ch == '?':
                result.append('%s')
            else:
                result.append(ch)
        else:
            result.append(ch)
            if ch == string_char:
                in_string = False
    return ''.join(result)


class PgRow:
    """模拟 sqlite3.Row，支持 dict-like 和 index 访问"""

    def __init__(self, columns, values):
        self._columns = columns
        self._values = values
        self._dict = dict(zip(columns, values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._dict[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def keys(self):
        return self._columns


class PgCursor:
    """模拟 sqlite3.Cursor"""

    def __init__(self, pg_conn, use_row_factory=False):
        self._conn = pg_conn
        self._cursor = pg_conn.cursor()
        self._use_row_factory = use_row_factory
        self._description = None
        self._lastrowid = None

    @property
    def description(self):
        return self._cursor.description

    @property
    def lastrowid(self):
        return self._lastrowid

    def execute(self, sql, params=None):
        pg_sql = _convert_sql(sql)
        try:
            if params:
                self._cursor.execute(pg_sql, params)
            else:
                self._cursor.execute(pg_sql)
        except Exception:
            # 自动回滚当前事务以便后续查询
            self._conn.rollback()
            raise

        # 处理 INSERT 返回 lastrowid
        if pg_sql.strip().upper().startswith('INSERT'):
            try:
                # PostgreSQL 用 RETURNING 获取插入ID，但这里兼容不加RETURNING的情况
                if self._cursor.description:
                    row = self._cursor.fetchone()
                    if row:
                        self._lastrowid = row[0]
            except Exception:
                pass

    def executemany(self, sql, seq_of_params):
        pg_sql = _convert_sql(sql)
        for params in seq_of_params:
            self._cursor.execute(pg_sql, params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._use_row_factory and self._cursor.description:
            columns = [desc[0] for desc in self._cursor.description]
            return PgRow(columns, list(row))
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._use_row_factory and self._cursor.description:
            columns = [desc[0] for desc in self._cursor.description]
            return [PgRow(columns, list(row)) for row in rows]
        return rows

    def close(self):
        self._cursor.close()


class PgConnection:
    """模拟 sqlite3.Connection，基于 psycopg2"""

    def __init__(self, database_url: str, row_factory=None):
        import psycopg2
        self._conn = psycopg2.connect(database_url)
        self._conn.autocommit = False
        self._use_row_factory = row_factory is not None
        self.row_factory = row_factory

    def cursor(self):
        return PgCursor(self._conn, use_row_factory=self._use_row_factory)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def execute(self, sql, params=None):
        cursor = self.cursor()
        cursor.execute(sql, params)
        return cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
        return False


def get_connection(db_path: str = None, row_factory=None):
    """
    获取数据库连接。

    如果设置了 DATABASE_URL 环境变量，使用 PostgreSQL，忽略 db_path。
    否则使用 SQLite。

    Args:
        db_path: SQLite 数据库路径（PostgreSQL 模式下忽略）
        row_factory: 设为 sqlite3.Row 或任意值时启用 dict-like 行访问

    Returns:
        Connection 对象（sqlite3.Connection 或 PgConnection）
    """
    if is_using_neon():
        return PgConnection(get_database_url(), row_factory=row_factory)

    # 回退到 SQLite
    if db_path is None:
        db_path = str(Path("data/youtube_pipeline.db"))
    conn = sqlite3.connect(db_path)
    if row_factory is not None:
        conn.row_factory = row_factory
    return conn


def db_exists(db_path: str = None) -> bool:
    """检查数据库是否可用"""
    if is_using_neon():
        return True  # Neon 始终可用
    if db_path is None:
        db_path = str(Path("data/youtube_pipeline.db"))
    return Path(db_path).exists()
