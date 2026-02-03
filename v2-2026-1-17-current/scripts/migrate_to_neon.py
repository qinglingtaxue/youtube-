#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 到 Neon PostgreSQL 数据迁移脚本

用法:
1. 设置环境变量: export DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
2. 运行迁移: python scripts/migrate_to_neon.py

功能:
- 自动检测本地 SQLite 数据库
- 创建 Neon 表结构
- 迁移所有数据（批量插入）
- 显示迁移进度
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()


def get_sqlite_connection(db_path: str) -> sqlite3.Connection:
    """获取 SQLite 连接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    """获取 SQLite 中的所有表"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]


def get_table_data(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    """获取表中所有数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # 转换为字典列表
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_table_count(conn: sqlite3.Connection, table_name: str) -> int:
    """获取表记录数"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def migrate_to_neon(sqlite_path: str, neon_url: str):
    """
    执行迁移

    Args:
        sqlite_path: SQLite 数据库路径
        neon_url: Neon PostgreSQL 连接字符串
    """
    from src.shared.neon_database import NeonDatabase, Base

    console.print(f"\n[bold cyan]📦 开始迁移数据库[/bold cyan]")
    console.print(f"源: {sqlite_path}")
    console.print(f"目标: {neon_url[:50]}...")

    # 连接 SQLite
    sqlite_conn = get_sqlite_connection(sqlite_path)
    tables = get_sqlite_tables(sqlite_conn)

    # 统计信息
    stats_table = Table(title="📊 源数据库统计")
    stats_table.add_column("表名", style="cyan")
    stats_table.add_column("记录数", justify="right", style="green")

    total_records = 0
    table_counts = {}
    for table in tables:
        count = get_table_count(sqlite_conn, table)
        table_counts[table] = count
        total_records += count
        stats_table.add_row(table, str(count))

    stats_table.add_row("[bold]总计[/bold]", f"[bold]{total_records}[/bold]")
    console.print(stats_table)

    # 初始化 Neon 数据库
    console.print("\n[yellow]🔧 创建 Neon 表结构...[/yellow]")
    neon_db = NeonDatabase(neon_url)
    neon_db.create_tables()
    console.print("[green]✓ 表结构创建完成[/green]")

    # SQLite 表名到 ORM 模型的映射
    from src.shared.neon_database import (
        Video, Script, Subtitle, Thumbnail, Spec,
        CompetitorVideo, Analytics, Task, ResearchReport,
        Channel, VideoComment, VideoStatsHistory, VideoMonitoring,
        WatchedChannel, ChannelPublication, ChannelAlert,
        SearchTrend, TrendAnalysis, MultilangVideo
    )

    table_model_map = {
        'videos': Video,
        'scripts': Script,
        'subtitles': Subtitle,
        'thumbnails': Thumbnail,
        'specs': Spec,
        'competitor_videos': CompetitorVideo,
        'analytics': Analytics,
        'tasks': Task,
        'research_reports': ResearchReport,
        'channels': Channel,
        'video_comments': VideoComment,
        'video_stats_history': VideoStatsHistory,
        'video_monitoring': VideoMonitoring,
        'watched_channels': WatchedChannel,
        'channel_publications': ChannelPublication,
        'channel_alerts': ChannelAlert,
        'search_trends': SearchTrend,
        'trend_analysis': TrendAnalysis,
        'multilang_videos': MultilangVideo,
    }

    # 迁移数据
    console.print("\n[yellow]📤 迁移数据中...[/yellow]")

    migrated_tables = []
    skipped_tables = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:

        for table_name in tables:
            if table_name not in table_model_map:
                skipped_tables.append(table_name)
                continue

            count = table_counts[table_name]
            if count == 0:
                continue

            task = progress.add_task(f"迁移 {table_name}", total=count)

            # 获取数据
            data = get_table_data(sqlite_conn, table_name)
            model_class = table_model_map[table_name]

            # 批量插入
            session = neon_db.get_session()
            try:
                batch_size = 100
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]

                    for row in batch:
                        # 清理数据：移除 None 键，转换类型
                        cleaned_row = {}
                        for key, value in row.items():
                            if value is not None:
                                # 清理字符串中的 NUL 字节（PostgreSQL 不接受）
                                if isinstance(value, str):
                                    value = value.replace('\x00', '')
                                # 处理日期时间字段
                                if isinstance(value, str) and key.endswith('_at'):
                                    try:
                                        cleaned_row[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                    except:
                                        cleaned_row[key] = None
                                # 处理布尔字段
                                elif key in ('is_synced', 'is_uploaded', 'is_active', 'is_ai_generated',
                                             'is_pinned', 'is_favorited', 'is_potential', 'is_read'):
                                    cleaned_row[key] = bool(value)
                                else:
                                    cleaned_row[key] = value

                        # 创建模型实例
                        try:
                            instance = model_class(**cleaned_row)
                            session.merge(instance)  # merge 而不是 add，避免重复键冲突
                        except Exception as e:
                            session.rollback()
                            console.print(f"[red]跳过记录: {e}[/red]")

                        progress.update(task, advance=1)

                    # 每批次提交
                    try:
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        console.print(f"[red]批次提交失败，逐条重试: {e}[/red]")
                        # 逐条重试
                        for row in batch:
                            cleaned_row = {}
                            for key, value in row.items():
                                if value is not None:
                                    if isinstance(value, str):
                                        value = value.replace('\x00', '')
                                    if isinstance(value, str) and key.endswith('_at'):
                                        try:
                                            cleaned_row[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                        except:
                                            cleaned_row[key] = None
                                    elif key in ('is_synced', 'is_uploaded', 'is_active', 'is_ai_generated',
                                                 'is_pinned', 'is_favorited', 'is_potential', 'is_read'):
                                        cleaned_row[key] = bool(value)
                                    else:
                                        cleaned_row[key] = value
                            try:
                                instance = model_class(**cleaned_row)
                                session.merge(instance)
                                session.commit()
                            except Exception as e2:
                                session.rollback()

                migrated_tables.append(table_name)

            except Exception as e:
                session.rollback()
                console.print(f"[red]迁移 {table_name} 失败: {e}[/red]")
            finally:
                session.close()

    # 迁移结果
    console.print("\n[bold green]✅ 迁移完成！[/bold green]")

    result_table = Table(title="📋 迁移结果")
    result_table.add_column("状态", style="cyan")
    result_table.add_column("表名")

    for table in migrated_tables:
        result_table.add_row("✓ 已迁移", table)
    for table in skipped_tables:
        result_table.add_row("⏭ 跳过（无对应模型）", table)

    console.print(result_table)

    # 验证迁移
    console.print("\n[yellow]🔍 验证迁移数据...[/yellow]")
    session = neon_db.get_session()

    verify_table = Table(title="验证结果")
    verify_table.add_column("表名", style="cyan")
    verify_table.add_column("SQLite", justify="right")
    verify_table.add_column("Neon", justify="right")
    verify_table.add_column("状态", justify="center")

    for table_name, model_class in table_model_map.items():
        sqlite_count = table_counts.get(table_name, 0)
        neon_count = session.query(model_class).count()
        status = "✓" if sqlite_count == neon_count else "⚠"
        verify_table.add_row(table_name, str(sqlite_count), str(neon_count), status)

    session.close()
    console.print(verify_table)


def main():
    """主函数"""
    # 获取 Neon 连接字符串
    neon_url = os.getenv('DATABASE_URL')

    if not neon_url:
        console.print("[red]错误: 未设置 DATABASE_URL 环境变量[/red]")
        console.print("\n请设置 Neon 数据库连接字符串:")
        console.print("  export DATABASE_URL='postgresql://user:password@host/dbname?sslmode=require'")
        sys.exit(1)

    # 查找 SQLite 数据库
    data_dir = project_root / 'data'
    sqlite_files = list(data_dir.glob('*.db'))

    if not sqlite_files:
        console.print("[red]错误: data/ 目录下没有找到 SQLite 数据库文件[/red]")
        sys.exit(1)

    # 显示可用的数据库
    console.print("\n[bold]可用的 SQLite 数据库:[/bold]")
    for i, db_file in enumerate(sqlite_files, 1):
        console.print(f"  {i}. {db_file.name}")

    # 默认选择主数据库
    main_db = data_dir / 'youtube_pipeline.db'
    if main_db.exists():
        db_path = main_db
    else:
        db_path = sqlite_files[0]

    console.print(f"\n使用数据库: [cyan]{db_path}[/cyan]")

    # 确认迁移
    confirm = input("\n确认开始迁移? (y/N): ")
    if confirm.lower() != 'y':
        console.print("[yellow]已取消迁移[/yellow]")
        sys.exit(0)

    # 执行迁移
    migrate_to_neon(str(db_path), neon_url)


if __name__ == '__main__':
    main()
