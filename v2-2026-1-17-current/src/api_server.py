#!/usr/bin/env python3
"""
YouTube 内容助手 API 服务器

提供 WebSocket 和 HTTP 接口，支持：
- WebSocket 实时数据采集和进度推送
- HTTP 任务状态查询（作为 WebSocket 断开后的补救机制）
- 趋势热词获取
"""

import asyncio
import json
import queue
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import sqlite3
from src.shared.db_compat import get_connection as db_get_connection, db_exists, is_using_neon

# 预加载 jieba（避免每次请求冷启动）
try:
    import jieba
    jieba.initialize()
except Exception:
    pass

# 分析结果缓存（Vercel 函数实例级别，同一实例复用）
_analyze_cache = {}
_CACHE_TTL = 600  # 10 分钟缓存

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 惰性导入：避免在 Vercel 环境中因 yt-dlp 不可用而失败
# DataCollector 和 CompetitorVideoRepository 只在需要时才导入
DataCollector = None
CompetitorVideoRepository = None


def _get_data_collector():
    """惰性加载 DataCollector"""
    global DataCollector
    if DataCollector is None:
        from src.research.data_collector import DataCollector as DC
        DataCollector = DC
    return DataCollector()


def _get_repository(db_path=None):
    """惰性加载 CompetitorVideoRepository"""
    global CompetitorVideoRepository
    if CompetitorVideoRepository is None:
        from src.shared.repositories import CompetitorVideoRepository as Repo
        CompetitorVideoRepository = Repo
    return CompetitorVideoRepository(db_path)


# ============================================================
# 任务状态管理
# ============================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"
    NOT_FOUND = "not_found"


@dataclass
class TaskState:
    """任务状态"""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# 任务存储（内存中，生产环境应使用 Redis）
task_store: Dict[str, TaskState] = {}

# 任务过期时间（秒）
TASK_EXPIRY = 3600  # 1小时


def cleanup_expired_tasks():
    """清理过期任务"""
    now = time.time()
    expired = [
        task_id for task_id, task in task_store.items()
        if now - task.updated_at > TASK_EXPIRY
    ]
    for task_id in expired:
        del task_store[task_id]


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title="YouTube Content Assistant API",
    description="YouTube 内容助手 API 服务器",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务 - 提供 web 目录下的可视化页面
web_dir = Path(__file__).parent / "web"
if web_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(web_dir), html=True), name="dashboard")

# 静态文件服务 - 提供 public 目录下的分析报告页面
public_dir = Path(__file__).parent / "public"
if public_dir.exists():
    app.mount("/report", StaticFiles(directory=str(public_dir), html=True), name="report")


# ============================================================
# HTTP 端点
# ============================================================

@app.get("/")
async def root():
    """返回前端页面"""
    demo_path = Path(__file__).parent / "demo.html"
    if demo_path.exists():
        return FileResponse(demo_path, media_type="text/html")
    return {"status": "ok", "message": "YouTube Content Assistant API"}


@app.get("/creator")
async def creator_dashboard():
    """返回创作者友好版界面"""
    creator_path = Path(__file__).parent / "creator-dashboard.html"
    if creator_path.exists():
        return FileResponse(creator_path, media_type="text/html")
    return {"status": "error", "message": "创作者仪表盘页面不存在"}


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok", "message": "YouTube Content Assistant API"}


@app.get("/api/task/{task_id}/status")
async def get_task_status(task_id: str):
    """
    获取任务状态

    这是 WebSocket 断开后的补救机制，前端可以轮询此接口获取结果
    """
    cleanup_expired_tasks()

    if task_id not in task_store:
        return JSONResponse(
            status_code=404,
            content={"status": "not_found", "message": "任务不存在或已过期"}
        )

    task = task_store[task_id]
    return task.to_dict()


@app.get("/api/statistics")
async def get_statistics():
    """获取数据库统计信息"""
    try:
        repo = _get_repository()
        stats = repo.get_statistics()
        return {"status": "ok", "data": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# WebSocket 端点
# ============================================================

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 连接端点

    协议：
    1. 客户端连接后发送研究参数
    2. 服务器推送进度更新
    3. 服务器推送最终结果
    4. 持续响应心跳保持连接
    """
    await websocket.accept()

    # 创建任务状态
    task_store[task_id] = TaskState(task_id=task_id)

    # 服务器主动心跳任务（保持连接活跃）
    heartbeat_task = None
    stop_heartbeat = False

    async def server_heartbeat():
        """服务器主动发送心跳，保持连接活跃"""
        nonlocal stop_heartbeat
        while not stop_heartbeat:
            try:
                await asyncio.sleep(15)  # 每 15 秒发送一次
                if not stop_heartbeat:
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time(),
                        "server_ping": True
                    })
            except Exception as e:
                if not stop_heartbeat:
                    print(f"服务器心跳发送失败: {e}")
                break

    try:
        # 等待客户端发送参数
        data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
        params = json.loads(data)

        # 处理心跳（首次连接时可能先收到心跳）
        while params.get("type") == "ping":
            await websocket.send_json({"type": "pong", "timestamp": time.time()})
            print(f"💓 响应初始心跳: {task_id}")
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            params = json.loads(data)

        # 提取参数
        topic = params.get("topic", "")
        video_count = params.get("video_count", 100)
        time_range = params.get("time_range", "month")
        sort_by = params.get("sort_by", "views")

        if not topic:
            await websocket.send_json({
                "type": "error",
                "message": "缺少主题参数"
            })
            return

        # 更新任务状态
        task = task_store[task_id]
        task.status = TaskStatus.RUNNING
        task.message = f"正在分析: {topic}"
        task.updated_at = time.time()

        # 发送开始消息
        await websocket.send_json({
            "type": "status",
            "message": f"正在分析: {topic}",
            "progress": 0
        })

        # 启动服务器心跳任务（与数据采集并行运行，保持连接活跃）
        heartbeat_task = asyncio.create_task(server_heartbeat())

        # 执行数据采集（在后台线程中运行以避免阻塞）
        result = await run_data_collection(
            websocket, task_id, topic, video_count, time_range, sort_by
        )

        # 停止心跳响应
        stop_heartbeat = True
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        # 更新任务状态（无论 WebSocket 是否断开，都保存结果）
        task.status = TaskStatus.COMPLETE
        task.result = result
        task.progress = 100
        task.message = "采集完成"
        task.updated_at = time.time()

        # 尝试发送最终结果（WebSocket 可能已断开）
        try:
            await websocket.send_json({
                "type": "complete",
                "result": result
            })
        except Exception as send_err:
            print(f"发送完成消息失败（WebSocket 可能已断开）: {send_err}")
            # 结果已保存到 task_store，前端可通过 HTTP 轮询获取

    except WebSocketDisconnect:
        print(f"WebSocket 断开: {task_id}")
        stop_heartbeat = True
        # 任务状态保持，让 HTTP 轮询可以获取结果

    except asyncio.TimeoutError:
        try:
            await websocket.send_json({
                "type": "error",
                "message": "等待参数超时"
            })
        except:
            pass
        task_store[task_id].status = TaskStatus.ERROR
        task_store[task_id].error = "等待参数超时"

    except Exception as e:
        error_msg = str(e)
        print(f"WebSocket 错误: {error_msg}")
        traceback.print_exc()

        # 只有在任务未完成时才设置为错误状态
        task = task_store.get(task_id)
        if task and task.status != TaskStatus.COMPLETE:
            task.status = TaskStatus.ERROR
            task.error = error_msg

        try:
            await websocket.send_json({
                "type": "error",
                "message": error_msg
            })
        except:
            pass


async def run_data_collection(
    websocket: WebSocket,
    task_id: str,
    topic: str,
    video_count: int,
    time_range: str,
    sort_by: str
) -> Dict[str, Any]:
    """
    执行数据采集

    使用 asyncio.to_thread 在后台线程运行 DataCollector
    """
    # 使用线程安全的队列（queue.Queue 是线程安全的）
    progress_queue = queue.Queue()

    # 停止标志
    stop_consumer = False

    # 时间估算状态
    stage_start_times: Dict[str, float] = {}
    stage_item_times: Dict[str, list] = {}

    async def send_progress(stage: str, current: int, total: int, message: str = "", extra: dict = None):
        """发送进度更新"""
        progress = int((current / total) * 100) if total > 0 else 0
        now = time.time()

        # 计算预计剩余时间
        estimated_remaining = None
        if stage not in stage_start_times:
            stage_start_times[stage] = now
            stage_item_times[stage] = []

        if current > 0:
            # 记录每个项目的处理时间
            if len(stage_item_times[stage]) < current:
                elapsed = now - stage_start_times[stage]
                avg_time_per_item = elapsed / current
                remaining_items = total - current
                estimated_remaining = avg_time_per_item * remaining_items
                stage_item_times[stage].append(avg_time_per_item)

        # 更新任务状态
        task = task_store.get(task_id)
        if task:
            task.progress = progress
            task.message = message or f"{stage}: {current}/{total}"
            task.updated_at = now

        # 构建进度消息
        progress_data = {
            "type": "progress",
            "stage": stage,
            "current": current,
            "total": total,
            "progress": progress,
            "message": message or f"{stage}: {current}/{total}"
        }

        # 添加时间估算（前端期望的格式）
        if estimated_remaining is not None and estimated_remaining > 0:
            if stage == "detail":
                progress_data["channel_fetch"] = {
                    "estimated_remaining_seconds": estimated_remaining
                }
            else:
                progress_data["estimated_remaining_seconds"] = estimated_remaining

        # 添加实时统计（视频数、频道数）
        if extra:
            progress_data.update(extra)

        try:
            await websocket.send_json(progress_data)
        except:
            pass  # WebSocket 可能已断开

    def sync_progress_callback(stage: str, current: int, total: int, extra: dict = None):
        """同步进度回调（在后台线程中调用）"""
        try:
            # 使用线程安全的 queue.Queue
            progress_queue.put((stage, current, total, extra or {}))
        except:
            pass

    # 启动进度消费者
    async def progress_consumer():
        nonlocal stop_consumer
        while not stop_consumer:
            try:
                # 非阻塞方式检查队列
                try:
                    item = progress_queue.get_nowait()
                    if len(item) == 4:
                        stage, current, total, extra = item
                    else:
                        stage, current, total = item
                        extra = {}
                    await send_progress(stage, current, total, extra=extra)
                except queue.Empty:
                    # 队列为空，等待一小段时间
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"进度消费者错误: {e}")
                await asyncio.sleep(0.1)

    progress_task = asyncio.create_task(progress_consumer())

    try:
        # 发送开始状态
        await send_progress("初始化", 0, 1, "正在初始化数据收集器...")

        # 在后台线程执行数据采集
        def collect_data():
            collector = _get_data_collector()

            # 计算参数
            detail_limit = min(video_count // 2, 100)
            detail_min_views = 5000

            # 创建带实时统计的进度回调
            def progress_with_stats(stage: str, current: int, total: int):
                """带实时统计的进度回调"""
                # 查询当前主题相关的视频数和频道数
                try:
                    videos = collector.get_videos_from_db(
                        keyword_like=topic,
                        min_views=0,
                        limit=10000
                    )
                    video_count_now = len(videos)

                    # 统计频道（去重）
                    channels = set()
                    for v in videos:
                        if v.channel_id and v.channel_id != 'None':
                            channels.add(v.channel_id)
                        elif v.channel_name:
                            channels.add(v.channel_name)
                    channel_count_now = len(channels)

                    # 调用原始回调，附带实时统计
                    sync_progress_callback(stage, current, total, {
                        "realtime_stats": {
                            "videos": video_count_now,
                            "channels": channel_count_now
                        }
                    })
                except Exception as e:
                    # 即使统计失败也继续
                    sync_progress_callback(stage, current, total, {})

            # 执行大规模采集
            result = collector.collect_large_scale(
                theme=topic,
                target_count=video_count,
                detail_min_views=detail_min_views,
                detail_limit=detail_limit,
                time_range=time_range,
                on_progress=progress_with_stats
            )

            # 获取视频列表（使用模糊匹配，包含所有扩展关键词的视频）
            # 例如搜索 "养生"，会匹配 "养生"、"中医养生"、"健康养生" 等所有相关关键词

            # 先获取实际搜索到的全部视频（不受筛选条件限制）用于统计
            all_matched_videos = collector.get_videos_from_db(
                keyword_like=topic,  # 模糊匹配，包含主题词的所有视频
                min_views=0,  # 不限制播放量
                limit=10000   # 足够大的数量
            )

            # 统计频道数量（去重，优先使用 channel_id，否则用 channel_name）
            channels = set()
            for v in all_matched_videos:
                # 优先用 channel_id，如果没有或者是 'None' 字符串，则用 channel_name
                if v.channel_id and v.channel_id != 'None':
                    channels.add(v.channel_id)
                elif v.channel_name:
                    channels.add(v.channel_name)

            actual_total_videos = len(all_matched_videos)
            actual_total_channels = len(channels)

            # 获取筛选后的视频（用于展示）
            videos = collector.get_videos_from_db(
                keyword_like=topic,
                min_views=1000,
                limit=video_count * 2  # 多取一些，后面会去重排序
            )

            # 按排序方式排序
            if sort_by == "views":
                videos.sort(key=lambda v: v.view_count or 0, reverse=True)
            elif sort_by == "likes":
                videos.sort(key=lambda v: v.like_count or 0, reverse=True)
            elif sort_by == "date":
                videos.sort(key=lambda v: v.published_at or "", reverse=True)
            elif sort_by == "engagement":
                videos.sort(
                    key=lambda v: ((v.like_count or 0) + (v.comment_count or 0)) / max(v.view_count or 1, 1),
                    reverse=True
                )

            # 转换为字典格式
            video_list = []
            for v in videos[:video_count]:
                video_list.append({
                    "youtube_id": v.youtube_id,
                    "title": v.title,
                    "channel_name": v.channel_name,
                    "channel_id": v.channel_id,
                    "view_count": v.view_count or 0,
                    "like_count": v.like_count or 0,
                    "comment_count": v.comment_count or 0,
                    "duration": v.duration or 0,
                    "published_at": v.published_at.isoformat() if v.published_at else None,
                    "thumbnail_url": v.thumbnail_url,
                    "description": v.description[:200] if v.description else None,
                    "tags": v.tags or [],
                })

            # 计算统计信息
            total_views = sum(v["view_count"] for v in video_list)
            total_likes = sum(v["like_count"] for v in video_list)
            total_comments = sum(v["comment_count"] for v in video_list)

            # 获取数据库中该主题的最后更新时间
            db_stats = collector.get_statistics()

            return {
                "topic": topic,
                "total_videos": actual_total_videos,  # 实际搜索到的视频总数（不受筛选限制）
                "total_channels": actual_total_channels,  # 实际搜索到的频道总数
                "displayed_videos": len(video_list),  # 当前展示的视频数量
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "avg_views": total_views // len(video_list) if video_list else 0,
                "avg_likes": total_likes // len(video_list) if video_list else 0,
                "videos": video_list,
                "collection_stats": result,
                "collected_at": datetime.now().isoformat(),

                # 数据基数信息（用户新需求）
                "data_basis": {
                    "total_videos_in_db": db_stats.get('total', 0),  # 数据库总视频数
                    "videos_for_this_topic": actual_total_videos,     # 本主题视频数
                    "ranking_basis": len(video_list),                 # 排名依据的视频数
                    "description": f"本排名基于 {actual_total_videos} 个视频数据筛选"
                },
                "last_updated": datetime.now().isoformat(),  # 数据更新时间
            }

        # 执行采集
        result = await asyncio.to_thread(collect_data)

        return result

    finally:
        stop_consumer = True
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass


# ============================================================
# 主题数据查询（直接查看已有数据）
# ============================================================

@app.get("/api/themes")
async def get_themes():
    """获取数据库中的主题列表"""
    try:
        repo = _get_repository()
        conn = repo._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT theme, COUNT(*) as count
            FROM competitor_videos
            WHERE theme IS NOT NULL
            GROUP BY theme
            ORDER BY count DESC
        ''')
        themes = [{"theme": row[0], "count": row[1]} for row in cursor.fetchall()]
        conn.close()
        return {"status": "ok", "themes": themes}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/analyze/{theme}")
async def analyze_theme(
    theme: str,
    limit: int = 100,
    sort_by: str = "views",
    min_views: int = 1000,
    date_from: str = None,
    date_to: str = None
):
    """
    直接分析已有数据（不触发新搜索）

    Args:
        theme: 主题名称（如"养生"、"科技"）
        limit: 返回视频数量
        sort_by: 排序方式 (views/likes/date/engagement)
        min_views: 最小播放量筛选
        date_from: 发布时间起始（YYYY-MM-DD）
        date_to: 发布时间截止（YYYY-MM-DD）
    """
    try:
        # 缓存检查（同一函数实例内复用结果）
        cache_key = f"{theme}_{limit}_{sort_by}_{min_views}_{date_from}_{date_to}"
        if cache_key in _analyze_cache:
            cached_time, cached_result = _analyze_cache[cache_key]
            if time.time() - cached_time < _CACHE_TTL:
                return cached_result

        collector = _get_data_collector()

        # 使用 theme 精确匹配（新的查询方式）
        all_videos = collector.get_videos_from_db(
            theme=theme,
            min_views=0,
            limit=10000
        )

        if not all_videos:
            # 如果没有精确匹配，尝试模糊匹配（兼容旧数据）
            all_videos = collector.get_videos_from_db(
                keyword_like=theme,
                min_views=0,
                limit=10000
            )

        if not all_videos:
            return {
                "status": "error",
                "message": f"没有找到主题 '{theme}' 的数据，请先搜索收集数据"
            }

        # 计算数据的时间范围（视频发布时间）
        published_dates = [v.published_at for v in all_videos if v.published_at]
        collected_dates = [v.collected_at for v in all_videos if v.collected_at]

        data_time_range = {
            "published_earliest": min(published_dates).strftime("%Y-%m-%d") if published_dates else None,
            "published_latest": max(published_dates).strftime("%Y-%m-%d") if published_dates else None,
            "collected_earliest": min(collected_dates).strftime("%Y-%m-%d %H:%M") if collected_dates else None,
            "collected_latest": max(collected_dates).strftime("%Y-%m-%d %H:%M") if collected_dates else None,
        }

        # 统计频道
        channels = set()
        for v in all_videos:
            if v.channel_id and v.channel_id != 'None':
                channels.add(v.channel_id)
            elif v.channel_name:
                channels.add(v.channel_name)

        actual_total_videos = len(all_videos)
        actual_total_channels = len(channels)

        # 筛选视频
        valid_videos = all_videos

        # 播放量筛选
        if min_views > 0:
            valid_videos = [v for v in valid_videos if (v.view_count or 0) >= min_views]

        # 日期筛选
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                valid_videos = [v for v in valid_videos if v.published_at and v.published_at >= from_date]
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
                # 包含当天结束
                to_date = to_date.replace(hour=23, minute=59, second=59)
                valid_videos = [v for v in valid_videos if v.published_at and v.published_at <= to_date]
            except ValueError:
                pass

        filtered_count = len(valid_videos)

        # 排序
        if sort_by == "views":
            valid_videos.sort(key=lambda v: v.view_count or 0, reverse=True)
        elif sort_by == "likes":
            valid_videos.sort(key=lambda v: v.like_count or 0, reverse=True)
        elif sort_by == "date":
            valid_videos.sort(key=lambda v: str(v.published_at or ""), reverse=True)
        elif sort_by == "engagement":
            valid_videos.sort(
                key=lambda v: ((v.like_count or 0) + (v.comment_count or 0)) / max(v.view_count or 1, 1),
                reverse=True
            )

        # 取前 N 个
        display_videos = valid_videos[:limit]

        # 转换格式（大量视频时省略 description 和 tags 以减小响应体积）
        compact = len(display_videos) > 500
        video_list = []
        for v in display_videos:
            item = {
                "youtube_id": v.youtube_id,
                "title": v.title,
                "channel_name": v.channel_name,
                "channel_id": v.channel_id,
                "view_count": v.view_count or 0,
                "like_count": v.like_count or 0,
                "comment_count": v.comment_count or 0,
                "duration": v.duration or 0,
                "published_at": v.published_at.isoformat() if v.published_at else None,
                "thumbnail_url": v.thumbnail_url,
            }
            if not compact:
                item["description"] = v.description[:200] if v.description else None
                item["tags"] = v.tags or []
            video_list.append(item)

        # 计算统计
        total_views = sum(v["view_count"] for v in video_list)
        total_likes = sum(v["like_count"] for v in video_list)
        total_comments = sum(v["comment_count"] for v in video_list)

        db_stats = collector.get_statistics()

        # 构建筛选条件描述
        filter_description_parts = []
        if min_views > 0:
            filter_description_parts.append(f"播放量≥{min_views:,}")
        if date_from:
            filter_description_parts.append(f"从 {date_from}")
        if date_to:
            filter_description_parts.append(f"到 {date_to}")
        filter_description = "，".join(filter_description_parts) if filter_description_parts else "无筛选"

        # 计算时长分布（用于模式洞察）- 增强版，包含平均播放量
        duration_stats = {
            "short": {"count": 0, "total_views": 0, "videos": []},  # < 5分钟
            "medium": {"count": 0, "total_views": 0, "videos": []},  # 5-15分钟
            "long": {"count": 0, "total_views": 0, "videos": []},  # > 15分钟
        }
        for v in valid_videos:
            d = v.duration or 0
            views = v.view_count or 0
            if d < 300:  # < 5分钟
                duration_stats["short"]["count"] += 1
                duration_stats["short"]["total_views"] += views
                duration_stats["short"]["videos"].append(views)
            elif d < 900:  # 5-15分钟
                duration_stats["medium"]["count"] += 1
                duration_stats["medium"]["total_views"] += views
                duration_stats["medium"]["videos"].append(views)
            else:  # > 15分钟
                duration_stats["long"]["count"] += 1
                duration_stats["long"]["total_views"] += views
                duration_stats["long"]["videos"].append(views)

        # 构建增强版时长分布
        duration_distribution = {}
        for key, stats in duration_stats.items():
            count = stats["count"]
            total_views = stats["total_views"]
            videos = stats["videos"]
            duration_distribution[key] = {
                "count": count,
                "total_views": total_views,
                "avg_views": int(total_views / count) if count > 0 else 0,
                "max_views": max(videos) if videos else 0,
                "min_views": min(videos) if videos else 0,
            }

        # 计算标题模式（提取高频关键词）- jieba 已在顶部预加载
        title_word_count = {}
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她', '它', '们', '我们', '你们', '他们', '什么', '怎么', '这个', '那个', '还', '能', '可以', '让', '被', '把', '给', '与', '及', '之', '来', '为', '以', '于', '所', '如', '或', '而', '但', '并', '且', '因', '则', '只', '从', '如何', '如果', '就是', '什麼', '這個', '那個', '如何', '什么', '怎样', '哪些', '為什麼', '為何', '如何', '怎麼', '怎麽', '#', '｜', '|', '/', '\\', '!', '！', '?', '？', '...', '。', '，', '、', '：', '；', '"', '"', ''', ''', '「', '」', '【', '】', '《', '》', '（', '）', '(', ')', '[', ']', '{', '}', ' ', '\n', '\t'}
        for v in valid_videos:
            if v.title:
                words = jieba.cut(v.title)
                for word in words:
                    word = word.strip()
                    if len(word) >= 2 and word not in stopwords and not word.isdigit():
                        title_word_count[word] = title_word_count.get(word, 0) + 1

        # 排序并取前20个高频词
        title_patterns = [
            {"word": word, "count": count}
            for word, count in sorted(title_word_count.items(), key=lambda x: x[1], reverse=True)[:20]
        ]

        # 计算发布趋势（按月统计）
        publishing_trend = {}
        for v in valid_videos:
            if v.published_at:
                month_key = v.published_at.strftime("%Y-%m")
                publishing_trend[month_key] = publishing_trend.get(month_key, 0) + 1

        # 转换为列表并按月份排序
        publishing_trend_list = [
            {"month": month, "count": count}
            for month, count in sorted(publishing_trend.items())
        ]

        # 计算近期爆款（30天内发布，高播放量）
        now = datetime.now()
        recent_hits = []
        evergreen_videos = []
        for v in valid_videos:
            if v.published_at:
                days_old = (now - v.published_at).days
                daily_views = (v.view_count or 0) / max(days_old, 1)
                if days_old <= 30 and (v.view_count or 0) >= 10000:
                    recent_hits.append({
                        "youtube_id": v.youtube_id,
                        "title": v.title,
                        "channel_name": v.channel_name,
                        "channel_id": v.channel_id,
                        "view_count": v.view_count or 0,
                        "video_age_days": days_old,
                        "daily_views": int(daily_views),
                        "published_at": v.published_at.isoformat() if v.published_at else None,
                    })
                elif days_old > 180 and daily_views > 100:  # 半年以上，日均播放>100
                    evergreen_videos.append({
                        "youtube_id": v.youtube_id,
                        "title": v.title,
                        "channel_name": v.channel_name,
                        "channel_id": v.channel_id,
                        "view_count": v.view_count or 0,
                        "video_age_days": days_old,
                        "daily_views": int(daily_views),
                        "published_at": v.published_at.isoformat() if v.published_at else None,
                    })

        # 按日均播放排序
        recent_hits.sort(key=lambda x: x["daily_views"], reverse=True)
        evergreen_videos.sort(key=lambda x: x["daily_views"], reverse=True)

        # 计算内容类型（category）统计
        category_stats = {}
        for v in valid_videos:
            cat = getattr(v, 'category', None) or '未分类'
            if cat not in category_stats:
                category_stats[cat] = {
                    "count": 0,
                    "total_views": 0,
                    "videos": [],
                }
            category_stats[cat]["count"] += 1
            category_stats[cat]["total_views"] += v.view_count or 0
            category_stats[cat]["videos"].append(v.view_count or 0)

        # 计算各分类的平均播放量，并排序
        category_list = []
        for cat, stats in category_stats.items():
            count = stats["count"]
            total_views = stats["total_views"]
            videos = stats["videos"]
            category_list.append({
                "category": cat,
                "count": count,
                "total_views": total_views,
                "avg_views": int(total_views / count) if count > 0 else 0,
                "max_views": max(videos) if videos else 0,
            })
        category_list.sort(key=lambda x: x["count"], reverse=True)

        # 计算时长+分类的组合统计（用于发现最佳组合）
        duration_category_combo = {}
        for v in valid_videos:
            cat = getattr(v, 'category', None) or '未分类'
            d = v.duration or 0
            if d < 300:
                duration_key = "short"
            elif d < 900:
                duration_key = "medium"
            else:
                duration_key = "long"
            combo_key = f"{duration_key}_{cat}"
            if combo_key not in duration_category_combo:
                duration_category_combo[combo_key] = {
                    "duration_type": duration_key,
                    "category": cat,
                    "count": 0,
                    "total_views": 0,
                }
            duration_category_combo[combo_key]["count"] += 1
            duration_category_combo[combo_key]["total_views"] += v.view_count or 0

        # 计算每个组合的平均播放量
        for combo in duration_category_combo.values():
            combo["avg_views"] = int(combo["total_views"] / combo["count"]) if combo["count"] > 0 else 0

        # 按平均播放量排序找出最佳组合
        best_combos = sorted(
            [c for c in duration_category_combo.values() if c["count"] >= 3],  # 至少3个视频才有参考价值
            key=lambda x: x["avg_views"],
            reverse=True
        )[:5]  # 取Top5

        # 计算频道更新频率分析
        channel_update_freq = {}
        for v in valid_videos:
            channel_key = v.channel_id if (v.channel_id and v.channel_id != 'None') else v.channel_name
            if not channel_key or not v.published_at:
                continue
            if channel_key not in channel_update_freq:
                channel_update_freq[channel_key] = {
                    "channel_name": v.channel_name,
                    "videos": [],
                    "total_views": 0,
                }
            channel_update_freq[channel_key]["videos"].append({
                "published_at": v.published_at,
                "views": v.view_count or 0,
            })
            channel_update_freq[channel_key]["total_views"] += v.view_count or 0

        # 计算每个频道的更新频率
        update_frequency_stats = {
            "daily": {"count": 0, "total_views": 0, "channels": []},     # 每天更新
            "weekly": {"count": 0, "total_views": 0, "channels": []},    # 每周1-2次
            "biweekly": {"count": 0, "total_views": 0, "channels": []},  # 每两周一次
            "monthly": {"count": 0, "total_views": 0, "channels": []},   # 每月一次
            "irregular": {"count": 0, "total_views": 0, "channels": []}, # 不规律
        }

        for channel_key, data in channel_update_freq.items():
            videos = data["videos"]
            if len(videos) < 2:
                continue  # 至少2个视频才能计算频率

            # 按发布时间排序
            videos.sort(key=lambda x: x["published_at"])

            # 计算平均间隔天数
            total_days = 0
            for i in range(1, len(videos)):
                delta = (videos[i]["published_at"] - videos[i-1]["published_at"]).days
                total_days += delta
            avg_interval = total_days / (len(videos) - 1) if len(videos) > 1 else 0

            # 分类更新频率
            if avg_interval <= 2:
                freq_type = "daily"
            elif avg_interval <= 7:
                freq_type = "weekly"
            elif avg_interval <= 14:
                freq_type = "biweekly"
            elif avg_interval <= 30:
                freq_type = "monthly"
            else:
                freq_type = "irregular"

            update_frequency_stats[freq_type]["count"] += 1
            update_frequency_stats[freq_type]["total_views"] += data["total_views"]
            if len(update_frequency_stats[freq_type]["channels"]) < 5:  # 每类最多记录5个频道
                update_frequency_stats[freq_type]["channels"].append({
                    "channel_name": data["channel_name"],
                    "video_count": len(videos),
                    "avg_interval_days": round(avg_interval, 1),
                    "total_views": data["total_views"],
                    "avg_views": data["total_views"] // len(videos) if videos else 0,
                })

        # 计算每个频率类型的平均播放量
        for freq_type, stats in update_frequency_stats.items():
            stats["avg_views"] = stats["total_views"] // stats["count"] if stats["count"] > 0 else 0

        # 找出最佳更新频率
        best_frequency = max(
            [(k, v) for k, v in update_frequency_stats.items() if v["count"] > 0],
            key=lambda x: x[1]["avg_views"],
            default=("unknown", {"avg_views": 0})
        )

        # ========== 智能分析结论 ==========
        insights = _generate_insights(
            theme=theme,
            duration_distribution=duration_distribution,
            title_patterns=title_patterns,
            publishing_trend=publishing_trend_list,
            recent_hits=recent_hits,
            evergreen_videos=evergreen_videos,
            channels=_extract_channel_stats(valid_videos),  # 使用时间过滤后的视频
            total_videos=actual_total_videos,
            filtered_videos=filtered_count,
            avg_views=total_views // len(video_list) if video_list else 0,
        )

        result = {
            "status": "ok",
            "result": {
                "topic": theme,
                "total_videos": actual_total_videos,
                "total_channels": actual_total_channels,
                "filtered_videos": filtered_count,
                "displayed_videos": len(video_list),
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "avg_views": total_views // len(video_list) if video_list else 0,
                "avg_likes": total_likes // len(video_list) if video_list else 0,
                "videos": video_list,
                "data_basis": {
                    "total_videos_in_db": db_stats.get('total', 0),
                    "videos_for_this_topic": actual_total_videos,
                    "filtered_count": filtered_count,
                    "ranking_basis": len(video_list),
                    "description": f"本排名基于 {actual_total_videos} 个视频中筛选出的 {filtered_count} 个视频"
                },
                "data_time_range": data_time_range,
                "filter_applied": {
                    "min_views": min_views,
                    "date_from": date_from,
                    "date_to": date_to,
                    "description": filter_description
                },
                "last_updated": datetime.now().isoformat(),
                "channels": _extract_channel_stats(valid_videos),  # 使用时间过滤后的视频
                # 模式洞察数据
                "duration_distribution": duration_distribution,
                "title_patterns": title_patterns,  # 标题高频词
                "publishing_trend": publishing_trend_list,  # 发布趋势
                "recent_hits": recent_hits[:20],  # 近期爆款 Top 20
                "evergreen_videos": evergreen_videos[:20],  # 长青视频 Top 20
                "category_stats": category_list,  # 内容类型统计
                "best_duration_category_combos": best_combos,  # 最佳时长+类型组合
                "update_frequency_stats": update_frequency_stats,  # 更新频率统计
                "best_update_frequency": {
                    "type": best_frequency[0],
                    "avg_views": best_frequency[1]["avg_views"],
                    "channel_count": best_frequency[1]["count"],
                },
                # 智能分析结论
                "insights": insights,
                # 频道榜单（用于频道运营模块的动态渲染）- 使用过滤后的视频
                "channel_rankings": _generate_channel_rankings(valid_videos),
                # 频道稳定性分析 - 使用过滤后的视频
                "channel_stability": _calculate_channel_stability(valid_videos),
                # 地区分布分析（Tab2 套利挖掘）
                "region_distribution": _analyze_region_distribution(_extract_channel_stats(valid_videos)),
                # 星期发布效果分析（Tab5 发布策略）
                "weekday_performance": _analyze_weekday_performance(valid_videos),
                # 内容生命周期分析（Tab3 选题决策）
                "content_lifecycle": _analyze_content_lifecycle(valid_videos),
            }
        }

        # 缓存结果
        _analyze_cache[cache_key] = (time.time(), result)

        return result
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def _generate_insights(
    theme: str,
    duration_distribution: dict,
    title_patterns: list,
    publishing_trend: list,
    recent_hits: list,
    evergreen_videos: list,
    channels: list,
    total_videos: int,
    filtered_videos: int,
    avg_views: int,
    duration_arbitrage: list = None,  # 时长套利数据
    channel_arbitrage: list = None,   # 频道套利数据
    topic_arbitrage: list = None,     # 话题套利数据
) -> dict:
    """
    生成智能分析结论
    包括：单项分析结论 + 综合分析结论
    """
    insights = {
        "duration_insight": None,  # 时长分布结论
        "trend_insight": None,     # 发布趋势结论
        "title_insight": None,     # 标题模式结论
        "channel_insight": None,   # 频道分布结论
        "comprehensive": None,     # 综合结论
        "opportunities": [],       # 机会点
        "recommendations": [],     # 建议
        # === 有趣度分析（套利分析）===
        "arbitrage_analysis": {
            "duration_arbitrage": [],   # 时长套利：需求/供给
            "channel_arbitrage": [],    # 频道套利：小频道爆款
            "topic_arbitrage": [],      # 话题套利：中介中心性/度中心性
        },
        # === 博主分类分析 ===
        "creator_classification": {
            "most_influential": [],     # 最有影响力的博主（播放量+订阅量最高）
            "underrated": [],           # 被低估的博主（订阅少但播放高）
            "high_value_niche": [],     # 高价值但小众的博主（有趣度高）
        },
        # === 视频生命力分析 ===
        "video_vitality": {
            "evergreen_content": [],    # 长青内容（发布超180天仍有高日均）
            "recent_hot": [],           # 近期高热度（发布早期表现突出，需持续监控确认增长趋势）
        },
    }

    # ===== 1. 时长分布结论 =====
    # 兼容新旧格式：新格式是 {"short": {"count": N, "avg_views": M}, ...}
    def get_duration_count(key):
        val = duration_distribution.get(key, 0)
        if isinstance(val, dict):
            return val.get("count", 0)
        return val

    total_duration = get_duration_count("short") + get_duration_count("medium") + get_duration_count("long")
    if total_duration > 0:
        short_pct = get_duration_count("short") / total_duration * 100
        medium_pct = get_duration_count("medium") / total_duration * 100
        long_pct = get_duration_count("long") / total_duration * 100

        if short_pct > 60:
            insights["duration_insight"] = {
                "type": "short_dominated",
                "title": "短视频主导",
                "description": f"该领域以短视频为主（{short_pct:.0f}%），5分钟以内的内容更易获得关注。",
                "recommendation": "建议制作3-5分钟的精炼内容，快速传递核心价值。"
            }
        elif long_pct > 40:
            insights["duration_insight"] = {
                "type": "long_content",
                "title": "深度内容受欢迎",
                "description": f"长视频占比较高（{long_pct:.0f}%），观众愿意投入时间学习深度内容。",
                "recommendation": "可以制作15-30分钟的系统性教程或深度解析。"
            }
        else:
            insights["duration_insight"] = {
                "type": "mixed",
                "title": "时长多元化",
                "description": f"短({short_pct:.0f}%)/中({medium_pct:.0f}%)/长({long_pct:.0f}%)视频均有市场。",
                "recommendation": "可根据内容复杂度灵活选择时长，短视频引流，长视频变现。"
            }

    # ===== 2. 发布趋势结论 =====
    if len(publishing_trend) >= 3:
        recent_months = publishing_trend[-3:]
        older_months = publishing_trend[-6:-3] if len(publishing_trend) >= 6 else publishing_trend[:3]

        recent_avg = sum(m["count"] for m in recent_months) / len(recent_months)
        older_avg = sum(m["count"] for m in older_months) / len(older_months) if older_months else recent_avg

        if older_avg > 0:
            growth_rate = (recent_avg - older_avg) / older_avg * 100
        else:
            growth_rate = 0

        if growth_rate > 30:
            insights["trend_insight"] = {
                "type": "rapid_growth",
                "title": "快速增长期",
                "description": f"近期内容发布量增长{growth_rate:.0f}%，市场热度持续上升。",
                "recommendation": "建议尽快入场，抢占先发优势。"
            }
        elif growth_rate < -20:
            insights["trend_insight"] = {
                "type": "declining",
                "title": "热度下降",
                "description": f"近期发布量下降{abs(growth_rate):.0f}%，市场可能趋于饱和或转移。",
                "recommendation": "需要寻找差异化角度或新的细分方向。"
            }
        else:
            insights["trend_insight"] = {
                "type": "stable",
                "title": "稳定发展",
                "description": f"发布量保持稳定，市场成熟度较高。",
                "recommendation": "适合持续深耕，注重内容质量提升。"
            }

    # ===== 3. 标题模式结论 =====
    if title_patterns and len(title_patterns) >= 5:
        top_words = [p["word"] for p in title_patterns[:5]]
        insights["title_insight"] = {
            "type": "keyword_pattern",
            "title": "高频关键词",
            "description": f"「{top_words[0]}」「{top_words[1]}」「{top_words[2]}」等词汇频繁出现。",
            "keywords": top_words,
            "recommendation": f"标题中包含「{top_words[0]}」等关键词可提高搜索曝光。"
        }

    # ===== 4. 频道分布结论 =====
    if channels and len(channels) >= 3:
        top_channel = channels[0]
        top3_share = sum(c.get("total_views", 0) for c in channels[:3])
        total_channel_views = sum(c.get("total_views", 0) for c in channels)
        concentration = top3_share / total_channel_views * 100 if total_channel_views > 0 else 0

        if concentration > 50:
            insights["channel_insight"] = {
                "type": "concentrated",
                "title": "头部集中",
                "description": f"Top 3 频道占据 {concentration:.0f}% 的播放量，头部效应明显。",
                "top_channel": top_channel.get("channel_name", "未知"),
                "recommendation": "需要差异化竞争，避免与头部正面竞争。"
            }
        else:
            insights["channel_insight"] = {
                "type": "dispersed",
                "title": "竞争分散",
                "description": f"播放量分布较为分散，新频道仍有机会。",
                "top_channel": top_channel.get("channel_name", "未知"),
                "recommendation": "市场机会较多，专注垂直细分领域可快速突围。"
            }

    # ===== 5. 综合分析结论 =====
    comprehensive_parts = []
    opportunities = []

    # 市场概览
    market_size = "大" if total_videos > 1000 else "中等" if total_videos > 200 else "小众"
    comprehensive_parts.append(f"「{theme}」领域共有 {total_videos} 个视频，市场规模{market_size}。")

    # 基于各维度生成机会点
    if insights.get("duration_insight"):
        di = insights["duration_insight"]
        if di["type"] == "short_dominated":
            opportunities.append({
                "title": "长视频蓝海",
                "description": "市场以短视频为主，深度长视频内容较少，可能存在差异化机会。",
                "score": "B"
            })
        elif di["type"] == "long_content":
            opportunities.append({
                "title": "短视频引流",
                "description": "可制作精华短视频吸引用户，再导流至长视频。",
                "score": "A"
            })

    if insights.get("trend_insight"):
        ti = insights["trend_insight"]
        if ti["type"] == "rapid_growth":
            opportunities.append({
                "title": "增长红利",
                "description": "市场快速增长中，新进入者容易获得关注。",
                "score": "A"
            })
        elif ti["type"] == "stable":
            opportunities.append({
                "title": "精品化机会",
                "description": "市场成熟但内容同质化严重，高质量差异化内容有机会脱颖而出。",
                "score": "B"
            })

    if len(evergreen_videos) > 5:
        opportunities.append({
            "title": "长青内容",
            "description": f"存在 {len(evergreen_videos)} 个长期获得流量的视频，说明该领域适合做常青内容。",
            "score": "A"
        })

    if len(recent_hits) > 3:
        opportunities.append({
            "title": "近期热点",
            "description": f"近30天有 {len(recent_hits)} 个爆款视频，市场活跃度高。",
            "score": "A"
        })

    insights["opportunities"] = opportunities

    # 生成综合建议
    recommendations = []
    if insights.get("title_insight"):
        recommendations.append(f"标题策略：使用「{insights['title_insight']['keywords'][0]}」「{insights['title_insight']['keywords'][1]}」等关键词")
    if insights.get("duration_insight"):
        recommendations.append(f"时长策略：{insights['duration_insight']['recommendation']}")
    if insights.get("channel_insight"):
        recommendations.append(f"竞争策略：{insights['channel_insight']['recommendation']}")

    insights["recommendations"] = recommendations

    # ===== 6. 有趣度分析（套利分析）=====
    arbitrage = insights["arbitrage_analysis"]

    # 6.1 时长套利：有趣度 = 平均播放量 / 供给比例
    # 找出需求大（播放量高）但供给少（视频数少）的时长区间
    if duration_arbitrage:
        arbitrage["duration_arbitrage"] = duration_arbitrage
    else:
        # 使用传入的 duration_distribution 计算（兼容新旧格式）
        total_videos_duration = sum(
            v.get("count", 0) if isinstance(v, dict) else v
            for v in duration_distribution.values()
        )
        if total_videos_duration > 0:
            duration_arb = []
            duration_labels = {
                "short": "短视频(<5分钟)",
                "medium": "中等(5-15分钟)",
                "long": "长视频(>15分钟)"
            }
            for key, label in duration_labels.items():
                val = duration_distribution.get(key, 0)
                if isinstance(val, dict):
                    count = val.get("count", 0)
                    actual_avg_views = val.get("avg_views", 0)
                else:
                    count = val
                    actual_avg_views = avg_views if avg_views > 0 else 10000

                supply_ratio = count / total_videos_duration if total_videos_duration > 0 else 0
                # 使用真实平均播放量（如果有），否则估算
                if actual_avg_views > 0:
                    estimated_demand = actual_avg_views
                else:
                    base_avg = avg_views if avg_views > 0 else 10000
                    if key == "short":
                        estimated_demand = base_avg * 0.8
                    elif key == "medium":
                        estimated_demand = base_avg * 1.0
                    else:
                        estimated_demand = base_avg * 1.5

                interestingness = estimated_demand / (supply_ratio * 100) if supply_ratio > 0 else 0
                duration_arb.append({
                    "bucket": label,
                    "supply_count": count,
                    "supply_ratio": round(supply_ratio * 100, 1),
                    "avg_views": int(actual_avg_views),  # 真实平均播放量
                    "estimated_avg_views": int(estimated_demand),
                    "interestingness": round(interestingness, 2),
                    "insight": "蓝海机会" if interestingness > (avg_views or 10000) else "红海竞争" if interestingness < (avg_views or 10000) * 0.5 else "中等竞争"
                })
            duration_arb.sort(key=lambda x: x["interestingness"], reverse=True)
            arbitrage["duration_arbitrage"] = duration_arb

    # 6.2 频道套利：有趣度 = 最高播放量 / 频道平均播放量
    # 找出小频道的爆款视频（证明内容而非流量决定播放）
    if channel_arbitrage:
        arbitrage["channel_arbitrage"] = channel_arbitrage
    elif channels:
        channel_arb = []
        for ch in channels[:20]:  # 分析 Top 20 频道
            max_views = ch.get("total_views", 0)  # 这里应该是单视频最高播放
            avg_ch_views = ch.get("avg_views", 0)
            video_count = ch.get("video_count", 0)

            if avg_ch_views > 0 and video_count >= 2:
                # 计算爆款系数：最高播放 vs 平均播放
                # 如果某个视频播放远超频道平均，说明内容本身有吸引力
                viral_ratio = max_views / avg_ch_views if avg_ch_views > 0 else 0

                # 小频道爆款更有价值（订阅少但播放高）
                subscriber_count = ch.get("subscriber_count", 0) or ch.get("subscriberCount", 0)
                if subscriber_count > 0:
                    views_per_sub = max_views / subscriber_count
                else:
                    views_per_sub = 0

                channel_arb.append({
                    "channel_name": ch.get("channel_name", "未知"),
                    "channel_id": ch.get("channel_id"),
                    "video_count": video_count,
                    "total_views": ch.get("total_views", 0),
                    "avg_views": avg_ch_views,
                    "subscriber_count": subscriber_count,
                    "viral_ratio": round(viral_ratio, 2),
                    "views_per_subscriber": round(views_per_sub, 2),
                    "interestingness": round(viral_ratio * (1 + views_per_sub / 10), 2) if views_per_sub > 0 else round(viral_ratio, 2),
                    "insight": "高潜力" if viral_ratio > 3 and views_per_sub > 5 else "内容驱动" if viral_ratio > 2 else "流量稳定"
                })

        channel_arb.sort(key=lambda x: x["interestingness"], reverse=True)
        arbitrage["channel_arbitrage"] = channel_arb[:10]  # 返回 Top 10

    # 6.3 话题套利：基于关键词共现分析
    # 有趣度 = 中介中心性 / 度中心性（连接不同话题群的关键词更有价值）
    if topic_arbitrage:
        arbitrage["topic_arbitrage"] = topic_arbitrage
    elif title_patterns and len(title_patterns) >= 5:
        # 简化版：使用词频和共现频率估算
        # 高频但独特（与其他词共现少）的词更有"套利"价值
        topic_arb = []
        top_words = title_patterns[:15]  # 分析前15个高频词
        total_word_count = sum(w["count"] for w in top_words)

        for i, word_data in enumerate(top_words):
            word = word_data["word"]
            count = word_data["count"]

            # 频率占比
            frequency_ratio = count / total_word_count if total_word_count > 0 else 0

            # 排名系数（排名越靠后但频率不低，说明是"隐藏宝藏"）
            rank_score = (len(top_words) - i) / len(top_words)

            # 简化的有趣度计算：频率适中但排名靠前的词可能过于泛化
            # 频率适中且排名靠后的词可能是差异化机会
            if frequency_ratio > 0.15:
                insight = "泛化关键词（竞争激烈）"
                interestingness = frequency_ratio * 0.5
            elif frequency_ratio > 0.08:
                insight = "主流关键词（适度竞争）"
                interestingness = frequency_ratio * 1.0
            else:
                insight = "差异化关键词（蓝海机会）"
                interestingness = frequency_ratio * 2.0  # 给予更高权重

            topic_arb.append({
                "keyword": word,
                "frequency": count,
                "frequency_ratio": round(frequency_ratio * 100, 2),
                "interestingness": round(interestingness * 100, 2),
                "insight": insight
            })

        # 按有趣度排序，突出蓝海机会
        topic_arb.sort(key=lambda x: x["interestingness"], reverse=True)
        arbitrage["topic_arbitrage"] = topic_arb

    # ===== 7. 博主分类分析 =====
    creator_class = insights["creator_classification"]

    if channels and len(channels) >= 3:
        # 7.1 最有影响力的博主（播放量+订阅量最高）
        # 计算影响力分数 = 总播放量 × log10(订阅数+1)
        import math
        influential_list = []
        for ch in channels[:30]:
            total_views = ch.get("total_views", 0)
            subscriber_count = ch.get("subscriber_count", 0) or ch.get("subscriberCount", 0)
            video_count = ch.get("video_count", 0)

            # 影响力分数：综合考虑播放量和订阅
            influence_score = total_views * math.log10(max(subscriber_count, 1) + 1) / 1000
            influential_list.append({
                "channel_name": ch.get("channel_name", "未知"),
                "channel_id": ch.get("channel_id"),
                "total_views": total_views,
                "subscriber_count": subscriber_count,
                "video_count": video_count,
                "avg_views": ch.get("avg_views", 0),
                "influence_score": round(influence_score, 2),
            })
        influential_list.sort(key=lambda x: x["influence_score"], reverse=True)
        creator_class["most_influential"] = influential_list[:10]

        # 7.2 被低估的博主（订阅少但播放高）
        # 有趣度 = 总播放量 / (订阅数 + 1)
        underrated_list = []
        for ch in channels:
            total_views = ch.get("total_views", 0)
            subscriber_count = ch.get("subscriber_count", 0) or ch.get("subscriberCount", 0)
            avg_views = ch.get("avg_views", 0)

            if total_views > 5000:  # 至少有一定播放量
                # 被低估指数 = 播放量 / 订阅数（订阅越少但播放越高越被低估）
                underrated_score = total_views / (subscriber_count + 1) if subscriber_count < 10000 else 0
                if underrated_score > 0:
                    underrated_list.append({
                        "channel_name": ch.get("channel_name", "未知"),
                        "channel_id": ch.get("channel_id"),
                        "total_views": total_views,
                        "subscriber_count": subscriber_count,
                        "video_count": ch.get("video_count", 0),
                        "avg_views": avg_views,
                        "underrated_score": round(underrated_score, 2),
                        "insight": "高度被低估" if underrated_score > 100 else "中度被低估" if underrated_score > 10 else "轻度被低估"
                    })
        underrated_list.sort(key=lambda x: x["underrated_score"], reverse=True)
        creator_class["underrated"] = underrated_list[:10]

        # 7.3 高价值但小众的博主（有趣度高 = 内容质量高但渠道小）
        # 有趣度 = 平均播放量 / (订阅数 / 视频数 + 1)
        high_value_niche = []
        for ch in channels:
            avg_views = ch.get("avg_views", 0)
            subscriber_count = ch.get("subscriber_count", 0) or ch.get("subscriberCount", 0)
            video_count = ch.get("video_count", 0)

            if avg_views > 1000 and video_count >= 2:  # 有一定质量
                # 高价值指数 = 平均播放量 / 每视频预期订阅转化
                expected_subs_per_video = subscriber_count / (video_count + 1)
                niche_score = avg_views / (expected_subs_per_video + 100)
                if niche_score > 1:
                    high_value_niche.append({
                        "channel_name": ch.get("channel_name", "未知"),
                        "channel_id": ch.get("channel_id"),
                        "total_views": ch.get("total_views", 0),
                        "subscriber_count": subscriber_count,
                        "video_count": video_count,
                        "avg_views": avg_views,
                        "niche_score": round(niche_score, 2),
                        "insight": "高价值小众" if niche_score > 50 else "潜力小众" if niche_score > 10 else "值得关注"
                    })
        high_value_niche.sort(key=lambda x: x["niche_score"], reverse=True)
        creator_class["high_value_niche"] = high_value_niche[:10]

    # ===== 8. 视频生命力分析 =====
    video_vitality = insights["video_vitality"]

    # 8.1 长青内容（使用传入的 evergreen_videos）
    if evergreen_videos:
        evergreen_with_vitality = []
        for v in evergreen_videos[:20]:
            days_old = v.get("video_age_days", 0)
            daily_views = v.get("daily_views", 0)
            total_views = v.get("view_count", 0)

            # 生命力指数 = 日均播放 × sqrt(视频天数)
            vitality_score = daily_views * math.sqrt(days_old) if days_old > 0 else 0
            evergreen_with_vitality.append({
                **v,
                "vitality_score": round(vitality_score, 2),
                "vitality_level": "超级长青" if vitality_score > 5000 else "优质长青" if vitality_score > 1000 else "稳定长青"
            })
        evergreen_with_vitality.sort(key=lambda x: x["vitality_score"], reverse=True)
        video_vitality["evergreen_content"] = evergreen_with_vitality[:10]

    # 8.2 近期高热度（使用传入的 recent_hits，仅表示发布早期表现突出，需持续监控确认增长趋势）
    if recent_hits:
        recent_hot = []
        for v in recent_hits[:20]:
            days_old = v.get("video_age_days", 1)
            daily_views = v.get("daily_views", 0)
            total_views = v.get("view_count", 0)

            # 热度指数 = 日均播放 / sqrt(视频天数+1)（越新的高播放视频热度越高）
            hot_score = daily_views / math.sqrt(days_old + 1)
            recent_hot.append({
                **v,
                "hot_score": round(hot_score, 2),
                "hot_level": "爆款潜力" if hot_score > 10000 else "热门" if hot_score > 3000 else "上升中"
            })
        recent_hot.sort(key=lambda x: x["hot_score"], reverse=True)
        video_vitality["recent_hot"] = recent_hot[:10]

    # 综合结论
    insights["comprehensive"] = {
        "market_summary": " ".join(comprehensive_parts),
        "opportunity_count": len(opportunities),
        "key_finding": opportunities[0]["description"] if opportunities else "需要更多数据进行深入分析",
        "top_performing": recent_hits[0] if recent_hits else None,
    }

    return insights


def _get_channels_info_from_db() -> dict:
    """从 channels 表获取频道详细信息"""
    if not db_exists():
        return {}

    channels_info = {}
    try:
        conn = db_get_connection(row_factory=sqlite3.Row)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT channel_id, channel_name, handle, subscriber_count,
                   video_count, total_views, country, description,
                   created_at, canonical_url
            FROM channels
        """)
        for row in cursor.fetchall():
            channels_info[row['channel_id']] = {
                'handle': row['handle'],
                'channel_subscriber_count': row['subscriber_count'],  # channels 表的订阅数
                'channel_video_count': row['video_count'],  # 频道总视频数
                'channel_total_views': row['total_views'],  # 频道总观看数
                'country': row['country'],
                'description': row['description'],
                'created_at': row['created_at'],
                'canonical_url': row['canonical_url'],
            }
        conn.close()
    except Exception as e:
        print(f"查询 channels 表失败: {e}")

    return channels_info


def _extract_channel_stats(videos) -> list:
    """提取频道统计信息（合并 channels 表数据）"""
    # 先从 channels 表获取额外信息
    channels_extra_info = _get_channels_info_from_db()

    channel_data = {}
    for v in videos:
        channel_key = v.channel_id if (v.channel_id and v.channel_id != 'None') else v.channel_name
        if not channel_key:
            continue

        if channel_key not in channel_data:
            channel_data[channel_key] = {
                "channel_id": v.channel_id,
                "channel_name": v.channel_name,
                "video_count": 0,  # 该主题下的视频数
                "total_views": 0,  # 该主题下的总播放
                "total_likes": 0,
                "subscriber_count": 0,  # 订阅数（取最大值）
            }

        channel_data[channel_key]["video_count"] += 1
        channel_data[channel_key]["total_views"] += v.view_count or 0
        channel_data[channel_key]["total_likes"] += v.like_count or 0
        # 取该频道视频中最大的订阅数（因为不同视频采集时间可能不同）
        video_subscriber = getattr(v, 'subscriber_count', 0) or 0
        if video_subscriber > channel_data[channel_key]["subscriber_count"]:
            channel_data[channel_key]["subscriber_count"] = video_subscriber

    # 计算平均值、合并 channels 表数据并排序
    channels = list(channel_data.values())
    for c in channels:
        c["avg_views"] = c["total_views"] // c["video_count"] if c["video_count"] > 0 else 0
        c["subscriberCount"] = c["subscriber_count"]  # 前端期望的字段名

        # 合并 channels 表的额外信息
        channel_id = c.get("channel_id")
        if channel_id and channel_id in channels_extra_info:
            extra = channels_extra_info[channel_id]
            c["handle"] = extra.get("handle")  # @用户名
            c["country"] = extra.get("country")  # 国家/地区
            c["description"] = extra.get("description")  # 频道描述
            c["channel_video_count"] = extra.get("channel_video_count")  # 频道总视频数
            c["channel_total_views"] = extra.get("channel_total_views")  # 频道总观看数
            c["created_at"] = extra.get("created_at")  # 频道创建时间
            c["canonical_url"] = extra.get("canonical_url")  # 频道 URL
            # 如果 channels 表有订阅数且比视频表的大，使用 channels 表的
            channel_subs = extra.get("channel_subscriber_count") or 0
            if channel_subs > c["subscriber_count"]:
                c["subscriber_count"] = channel_subs
                c["subscriberCount"] = channel_subs

            # 计算频道年龄和日均涨粉
            created_at = extra.get("created_at")
            if created_at and c["subscriber_count"] > 0:
                try:
                    from datetime import datetime
                    created = datetime.strptime(created_at, "%Y-%m-%d")
                    days = (datetime.now() - created).days
                    if days > 0:
                        c["days_since_creation"] = days
                        c["subs_per_day"] = round(c["subscriber_count"] / days, 1)
                except:
                    pass

    channels.sort(key=lambda c: c["total_views"], reverse=True)
    return channels  # 返回全部频道


# ============================================================
# 趋势热词
# ============================================================

@app.get("/api/trending")
async def get_trending_keywords():
    """获取趋势热词"""
    # 这里可以集成真实的趋势数据源
    # 目前返回预设热词
    keywords = [
        {"keyword": "AI工具", "heat": 98},
        {"keyword": "健康养生", "heat": 95},
        {"keyword": "Python教程", "heat": 92},
        {"keyword": "副业赚钱", "heat": 90},
        {"keyword": "投资理财", "heat": 88},
        {"keyword": "效率工具", "heat": 85},
        {"keyword": "自媒体运营", "heat": 82},
        {"keyword": "英语学习", "heat": 80},
    ]
    return {"status": "ok", "keywords": keywords}


# ============================================================
# 创作者助手 API（创作者友好版）
# ============================================================

@app.get("/api/creator-helper/{theme}")
async def get_creator_helper(theme: str):
    """
    创作者助手 API - 直接给出可用的建议

    返回 5 个核心模块：
    1. 选题助手 - 今日推荐选题 + 理由 + 标题参考
    2. 爆款学习 - 值得学习的爆款视频 + 学习点
    3. 标题助手 - 高效关键词 + 标题公式模板
    4. 学习对象 - 频道榜单（总播放榜/平均播放榜/视频数榜/黑马榜/高效榜）
    5. 避坑提醒 - 3 个最重要的警告
    """
    try:
        collector = _get_data_collector()

        # 获取所有视频数据
        all_videos = collector.get_videos_from_db(
            theme=theme,
            min_views=0,
            limit=10000
        )

        if not all_videos:
            all_videos = collector.get_videos_from_db(
                keyword_like=theme,
                min_views=0,
                limit=10000
            )

        if not all_videos:
            return {
                "status": "error",
                "message": f"没有找到主题 '{theme}' 的数据"
            }

        now = datetime.now()
        import math

        # ========== 1. 选题助手 ==========
        topic_recommendations = _generate_topic_recommendations(all_videos, theme, now)

        # ========== 2. 爆款学习 ==========
        viral_learning = _generate_viral_learning(all_videos, now)

        # ========== 3. 标题助手 ==========
        title_helper = _generate_title_helper(all_videos)

        # ========== 4. 学习对象（频道榜单）==========
        channel_rankings = _generate_channel_rankings(all_videos)

        # ========== 5. 避坑提醒 ==========
        warnings = _generate_warnings(all_videos, now)

        return {
            "status": "ok",
            "theme": theme,
            "data_basis": len(all_videos),
            "modules": {
                "topic_recommendations": topic_recommendations,
                "viral_learning": viral_learning,
                "title_helper": title_helper,
                "channel_rankings": channel_rankings,
                "warnings": warnings,
            }
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def _generate_topic_recommendations(videos, theme: str, now) -> dict:
    """生成选题推荐"""
    import jieba
    from collections import Counter

    # 分析近期爆款的关键词
    recent_viral = []
    evergreen = []

    for v in videos:
        if not v.published_at:
            continue
        days_old = (now - v.published_at).days
        daily_views = (v.view_count or 0) / max(days_old, 1)

        if days_old <= 30 and (v.view_count or 0) >= 10000:
            recent_viral.append({
                "title": v.title,
                "views": v.view_count,
                "daily_views": daily_views,
                "days_old": days_old,
            })
        elif days_old > 180 and daily_views > 100:
            evergreen.append({
                "title": v.title,
                "views": v.view_count,
                "daily_views": daily_views,
                "days_old": days_old,
            })

    # 提取爆款视频中的关键词
    stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '什么', '怎么', '这个', '那个', '还', '能', '可以', '让', '被', '把', '给', '如何'}
    keyword_counter = Counter()

    for v in recent_viral[:20]:
        words = jieba.cut(v["title"])
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stopwords and not word.isdigit():
                keyword_counter[word] += 1

    hot_keywords = [k for k, _ in keyword_counter.most_common(10)]

    # 生成 3 个选题推荐
    recommendations = []

    if recent_viral:
        # 推荐 1: 基于近期爆款
        top_viral = recent_viral[0]
        recommendations.append({
            "topic": f"{theme} + {hot_keywords[0] if hot_keywords else '实用技巧'}",
            "reason": f"近期「{top_viral['title'][:20]}...」日均 {int(top_viral['daily_views'])} 播放，说明这个角度有热度",
            "title_reference": top_viral["title"],
            "confidence": "高",
        })

    if len(hot_keywords) >= 2:
        # 推荐 2: 关键词组合
        recommendations.append({
            "topic": f"「{hot_keywords[0]}」+「{hot_keywords[1]}」组合",
            "reason": f"这两个词在爆款标题中频繁出现，组合使用可提高搜索曝光",
            "title_reference": f"【{hot_keywords[0]}】{theme}必看的{hot_keywords[1]}指南",
            "confidence": "中",
        })

    if evergreen:
        # 推荐 3: 基于长青内容
        top_evergreen = evergreen[0]
        recommendations.append({
            "topic": "制作系统性教程（长青内容）",
            "reason": f"「{top_evergreen['title'][:20]}...」发布 {top_evergreen['days_old']} 天仍有日均 {int(top_evergreen['daily_views'])} 播放",
            "title_reference": top_evergreen["title"],
            "confidence": "高",
        })

    return {
        "today_picks": recommendations[:3],
        "hot_keywords": hot_keywords[:5],
        "data_source": f"基于 {len(recent_viral)} 个近期爆款和 {len(evergreen)} 个长青视频分析",
    }


def _generate_viral_learning(videos, now) -> dict:
    """生成爆款学习内容"""
    viral_videos = []

    for v in videos:
        if not v.published_at or not v.view_count:
            continue
        days_old = (now - v.published_at).days
        if days_old <= 0:
            days_old = 1

        daily_views = v.view_count / days_old
        engagement_rate = ((v.like_count or 0) + (v.comment_count or 0)) / max(v.view_count, 1)

        # 筛选爆款：播放量高或日均高
        if v.view_count >= 50000 or (daily_views > 1000 and v.view_count >= 10000):
            # 分析学习点
            learning_points = []

            # 时长分析
            duration = v.duration or 0
            if duration < 300:
                learning_points.append("短视频策略：5分钟内快速传递价值")
            elif duration > 900:
                learning_points.append("深度内容：长视频满足深度学习需求")

            # 互动率分析
            if engagement_rate > 0.05:
                learning_points.append("高互动率：标题/内容引发共鸣")

            # 日均分析
            if daily_views > 5000:
                learning_points.append("病毒传播：具有分享属性")
            elif days_old > 180 and daily_views > 200:
                learning_points.append("长青内容：持续获得搜索流量")

            viral_videos.append({
                "youtube_id": v.youtube_id,
                "title": v.title,
                "channel_name": v.channel_name,
                "view_count": v.view_count,
                "daily_views": int(daily_views),
                "days_old": days_old,
                "duration": duration,
                "learning_points": learning_points or ["值得深入分析其成功因素"],
                "thumbnail_url": v.thumbnail_url,
            })

    # 排序并取前 10 个
    viral_videos.sort(key=lambda x: x["daily_views"], reverse=True)

    return {
        "videos": viral_videos[:10],
        "summary": f"共发现 {len(viral_videos)} 个值得学习的爆款视频",
    }


def _generate_title_helper(videos) -> dict:
    """生成标题助手内容"""
    import jieba
    from collections import Counter

    # 提取所有标题的关键词
    stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '什么', '怎么', '这个', '那个', '还', '能', '可以', '让', '被', '把', '给', '如何', '如果', '为什么', '怎样', '哪些'}

    # 按播放量加权统计关键词
    keyword_scores = Counter()
    keyword_video_count = Counter()

    for v in videos:
        if not v.title or not v.view_count:
            continue
        words = jieba.cut(v.title)
        seen_words = set()
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stopwords and not word.isdigit() and word not in seen_words:
                seen_words.add(word)
                keyword_scores[word] += v.view_count
                keyword_video_count[word] += 1

    # 计算高效关键词：总播放量 / 出现次数
    efficient_keywords = []
    for word, total_views in keyword_scores.most_common(50):
        count = keyword_video_count[word]
        if count >= 3:  # 至少出现 3 次
            avg_views = total_views / count
            efficient_keywords.append({
                "keyword": word,
                "avg_views": int(avg_views),
                "video_count": count,
                "total_views": total_views,
            })

    efficient_keywords.sort(key=lambda x: x["avg_views"], reverse=True)

    # 提取标题模板
    title_templates = [
        {"template": "【数字】+ 主题 + 结果", "example": "【3个方法】让你的XXX提升200%"},
        {"template": "如何 + 动作 + 获得好处", "example": "如何在7天内掌握XXX"},
        {"template": "主题 + 避坑指南", "example": "新手必看！XXX常见的5个错误"},
        {"template": "为什么 + 问题 + （答案预告）", "example": "为什么你的XXX总是失败？"},
        {"template": "主题 + 完整教程/攻略", "example": "2025年最新XXX完整攻略"},
    ]

    return {
        "efficient_keywords": efficient_keywords[:10],
        "title_templates": title_templates,
        "tip": "在标题中使用高效关键词，平均能获得更高播放量",
    }


def _generate_channel_rankings(videos) -> dict:
    """生成频道榜单（总播放榜/平均播放榜/视频数榜/黑马榜/高效榜/快速增长榜）"""
    import math
    from datetime import datetime

    # 从 channels 表获取频道订阅数和创建时间
    channel_info = {}  # channel_id/channel_name -> {subscriber_count, created_at, days_since_creation, subs_per_day}
    if db_exists():
        try:
            conn = db_get_connection()
            cursor = conn.cursor()
            # 获取所有频道的订阅数（不限制 created_at）
            cursor.execute("""
                SELECT channel_id, channel_name, subscriber_count, created_at
                FROM channels
                WHERE subscriber_count > 0
            """)
            now = datetime.now()
            for row in cursor.fetchall():
                ch_id, ch_name, subs, created_at = row
                info = {
                    "subscriber_count": subs or 0,
                    "created_at": None,
                    "days_since_creation": None,
                    "subs_per_day": 0,
                }
                # 如果有创建时间，计算增长速度
                if created_at and created_at.strip():
                    try:
                        created = datetime.strptime(created_at, "%Y-%m-%d")
                        days = (now - created).days
                        if days > 0:
                            info["created_at"] = created_at
                            info["days_since_creation"] = days
                            info["subs_per_day"] = round(subs / days, 1) if subs else 0
                    except:
                        pass
                # 用 channel_id 和 channel_name 都作为 key
                if ch_id:
                    channel_info[ch_id] = info
                if ch_name:
                    channel_info[ch_name] = info
            conn.close()
        except Exception as e:
            print(f"获取频道数据失败: {e}")

    # 统计每个频道的数据
    channel_data = {}
    channel_videos = {}  # 存储每个频道的视频列表，用于详细分析

    for v in videos:
        channel_key = v.channel_id if (v.channel_id and v.channel_id != 'None') else v.channel_name
        if not channel_key:
            continue

        if channel_key not in channel_data:
            channel_data[channel_key] = {
                "channel_id": v.channel_id,
                "channel_name": v.channel_name,
                "video_count": 0,
                "total_views": 0,
                "total_likes": 0,
                "subscriber_count": 0,
                "max_views": 0,
                "min_views": float('inf'),
                "total_duration": 0,
                "videos": [],  # 用于分析优缺点
            }
            channel_videos[channel_key] = []

        channel_data[channel_key]["video_count"] += 1
        channel_data[channel_key]["total_views"] += v.view_count or 0
        channel_data[channel_key]["total_likes"] += v.like_count or 0
        channel_data[channel_key]["total_duration"] += v.duration or 0

        if (v.view_count or 0) > channel_data[channel_key]["max_views"]:
            channel_data[channel_key]["max_views"] = v.view_count or 0
        if (v.view_count or 0) < channel_data[channel_key]["min_views"]:
            channel_data[channel_key]["min_views"] = v.view_count or 0

        channel_data[channel_key]["videos"].append({
            "title": v.title,
            "views": v.view_count or 0,
            "likes": v.like_count or 0,
            "duration": v.duration or 0,
        })

        video_subscriber = getattr(v, 'subscriber_count', 0) or 0
        if video_subscriber > channel_data[channel_key]["subscriber_count"]:
            channel_data[channel_key]["subscriber_count"] = video_subscriber

    # 计算派生指标
    channels = list(channel_data.values())
    for c in channels:
        c["avg_views"] = c["total_views"] // c["video_count"] if c["video_count"] > 0 else 0
        c["avg_duration"] = c["total_duration"] // c["video_count"] if c["video_count"] > 0 else 0
        c["engagement_rate"] = c["total_likes"] / c["total_views"] if c["total_views"] > 0 else 0
        c["views_variance"] = c["max_views"] - c["min_views"] if c["min_views"] != float('inf') else 0

        # 【重要】先从 channels 表获取订阅数（更准确），再计算黑马指数
        channel_key = c["channel_id"] or c["channel_name"]
        if channel_key in channel_info:
            info = channel_info[channel_key]
            # 使用 channels 表的订阅数（更准确）
            if info["subscriber_count"] > c["subscriber_count"]:
                c["subscriber_count"] = info["subscriber_count"]
            c["created_at"] = info["created_at"]
            c["days_since_creation"] = info["days_since_creation"]
            c["subs_per_day"] = info["subs_per_day"]
        else:
            c["created_at"] = None
            c["days_since_creation"] = None
            c["subs_per_day"] = 0

        # 黑马指数（在获取订阅数之后计算）
        if c["subscriber_count"] > 0 and c["subscriber_count"] < 10000:
            c["dark_horse_score"] = c["max_views"] / (c["subscriber_count"] + 1)
        else:
            c["dark_horse_score"] = 0

        # 高效指数
        if c["subscriber_count"] > 0:
            c["efficiency_score"] = c["avg_views"] / c["subscriber_count"]
        else:
            c["efficiency_score"] = 0

    def format_channel_with_analysis(c, rank_type: str) -> dict:
        """格式化频道信息，包含详细分析"""
        # 分析优点
        strengths = []
        weaknesses = []

        # 基于数据分析优点
        if c["avg_views"] > 50000:
            strengths.append({
                "point": "内容吸引力强",
                "data": f"平均播放 {c['avg_views']:,}",
                "reasoning": "远高于该领域平均水平，说明内容有较强吸引力"
            })
        elif c["avg_views"] > 10000:
            strengths.append({
                "point": "稳定表现",
                "data": f"平均播放 {c['avg_views']:,}",
                "reasoning": "高于行业中位数，说明内容质量稳定"
            })

        if c["engagement_rate"] > 0.05:
            strengths.append({
                "point": "高互动率",
                "data": f"点赞率 {c['engagement_rate']*100:.1f}%",
                "reasoning": "说明内容能引发用户共鸣，值得学习其互动技巧"
            })

        if c["video_count"] >= 10:
            strengths.append({
                "point": "持续输出",
                "data": f"发布了 {c['video_count']} 个视频",
                "reasoning": "说明该频道深耕该领域，有系统化的内容策略"
            })

        avg_duration_min = c["avg_duration"] / 60
        if 5 <= avg_duration_min <= 15:
            strengths.append({
                "point": "时长适中",
                "data": f"平均时长 {avg_duration_min:.0f} 分钟",
                "reasoning": "符合观众注意力曲线，既有深度又不冗长"
            })

        # 分析缺点
        if c["views_variance"] > c["avg_views"] * 3:
            weaknesses.append({
                "point": "表现不稳定",
                "data": f"播放量波动: {c['min_views']:,} ~ {c['max_views']:,}",
                "reasoning": "视频质量不稳定，部分内容未能获得足够关注"
            })

        if c["engagement_rate"] < 0.02:
            weaknesses.append({
                "point": "互动率偏低",
                "data": f"点赞率仅 {c['engagement_rate']*100:.1f}%",
                "reasoning": "可能内容偏信息性，缺乏情感共鸣点"
            })

        if avg_duration_min > 30:
            weaknesses.append({
                "point": "视频过长",
                "data": f"平均时长 {avg_duration_min:.0f} 分钟",
                "reasoning": "可能导致完播率下降，建议学习其内容但缩短时长"
            })

        # 计算推荐理由
        why_learn = _get_learning_reason_detailed(c, rank_type)

        return {
            "channel_name": c["channel_name"],
            "channel_id": c["channel_id"],
            "total_views": c["total_views"],
            "avg_views": c["avg_views"],
            "video_count": c["video_count"],
            "subscriber_count": c["subscriber_count"],
            "max_views": c["max_views"],
            "engagement_rate": round(c["engagement_rate"] * 100, 2),
            "avg_duration": c["avg_duration"],
            # 频道年龄相关
            "created_at": c.get("created_at"),
            "days_since_creation": c.get("days_since_creation"),
            "subs_per_day": c.get("subs_per_day", 0),
            "why_learn": why_learn["summary"],
            "analysis": {
                "conclusion": why_learn["conclusion"],
                "data_basis": why_learn["data_basis"],
                "calculation": why_learn["calculation"],
                "strengths": strengths[:3],  # 最多3个优点
                "weaknesses": weaknesses[:2],  # 最多2个缺点
            }
        }

    def _get_learning_reason_detailed(c, rank_type: str) -> dict:
        """根据榜单类型给出详细的学习理由"""
        if rank_type == "total_views":
            return {
                "summary": f"总播放 {c['total_views']:,}，是该领域的头部频道",
                "conclusion": "头部频道，值得作为标杆学习",
                "data_basis": [
                    f"总播放量: {c['total_views']:,}",
                    f"视频数量: {c['video_count']}",
                    f"平均播放: {c['avg_views']:,}",
                ],
                "calculation": "按总播放量降序排列",
            }
        elif rank_type == "avg_views":
            return {
                "summary": f"平均每个视频 {c['avg_views']:,} 播放，内容质量稳定",
                "conclusion": "内容质量标杆，每个视频都值得学习",
                "data_basis": [
                    f"平均播放: {c['avg_views']:,}",
                    f"总播放: {c['total_views']:,}",
                    f"视频数: {c['video_count']}",
                ],
                "calculation": "平均播放 = 总播放 / 视频数（筛选至少3个视频）",
            }
        elif rank_type == "video_count":
            return {
                "summary": f"发布了 {c['video_count']} 个视频，深耕该领域",
                "conclusion": "可学习其选题策略和内容体系",
                "data_basis": [
                    f"视频数量: {c['video_count']}",
                    f"总播放: {c['total_views']:,}",
                    f"平均播放: {c['avg_views']:,}",
                ],
                "calculation": "按视频发布数量降序排列",
            }
        elif rank_type == "dark_horse":
            return {
                "summary": f"订阅仅 {c['subscriber_count']:,} 却有 {c['max_views']:,} 播放的视频",
                "conclusion": "内容驱动型，证明好内容不需要大流量基础",
                "data_basis": [
                    f"订阅数: {c['subscriber_count']:,}",
                    f"最高播放: {c['max_views']:,}",
                    f"黑马指数: {c['dark_horse_score']:.1f}",
                ],
                "calculation": "黑马指数 = 最高播放 / (订阅数+1)，仅限订阅<1万的频道",
            }
        elif rank_type == "efficiency":
            return {
                "summary": f"每个订阅贡献 {c['efficiency_score']:.1f} 播放，转化效率高",
                "conclusion": "转化效率标杆，可学习其用户运营方式",
                "data_basis": [
                    f"平均播放: {c['avg_views']:,}",
                    f"订阅数: {c['subscriber_count']:,}",
                    f"效率指数: {c['efficiency_score']:.2f}",
                ],
                "calculation": "效率指数 = 平均播放 / 订阅数",
            }
        elif rank_type == "fast_growth":
            days = c.get('days_since_creation', 0)
            subs = c.get('subscriber_count', 0)
            subs_per_day = c.get('subs_per_day', 0)
            created_at = c.get('created_at', '未知')
            return {
                "summary": f"创建 {days} 天涨到 {subs:,} 粉丝，日均涨粉 {subs_per_day:.1f}",
                "conclusion": "快速增长标杆，可研究其冷启动策略",
                "data_basis": [
                    f"频道创建: {created_at}",
                    f"频道年龄: {days} 天",
                    f"当前订阅: {subs:,}",
                    f"日均涨粉: {subs_per_day:.1f}",
                ],
                "calculation": "日均涨粉 = 订阅数 / 频道天数",
            }
        return {
            "summary": "",
            "conclusion": "",
            "data_basis": [],
            "calculation": "",
        }

    # 生成各榜单（样本量提升到100+，确保统计意义）
    # 前端可根据需要选择展示数量
    RANKING_LIMIT = 100

    total_views_rank = sorted(channels, key=lambda x: x["total_views"], reverse=True)[:RANKING_LIMIT]
    avg_views_rank = sorted([c for c in channels if c["video_count"] >= 3], key=lambda x: x["avg_views"], reverse=True)[:RANKING_LIMIT]
    video_count_rank = sorted(channels, key=lambda x: x["video_count"], reverse=True)[:RANKING_LIMIT]
    dark_horse_rank = sorted([c for c in channels if c["dark_horse_score"] > 0], key=lambda x: x["dark_horse_score"], reverse=True)[:RANKING_LIMIT]
    efficiency_rank = sorted([c for c in channels if c["subscriber_count"] > 0], key=lambda x: x["efficiency_score"], reverse=True)[:RANKING_LIMIT]

    # 快速增长榜：30天内达到1000粉丝，或日均涨粉最快的频道
    fast_growth_rank = sorted(
        [c for c in channels if c.get("subs_per_day", 0) > 0 and c.get("days_since_creation")],
        key=lambda x: x["subs_per_day"],
        reverse=True
    )[:RANKING_LIMIT]

    # 统计信息（用于前端显示样本量）
    total_channels = len(channels)
    channels_with_subs = len([c for c in channels if c["subscriber_count"] > 0])

    return {
        # 统计元信息 - 用于前端显示样本量说明
        "stats": {
            "total_channels": total_channels,
            "channels_with_subs": channels_with_subs,
            "ranking_limit": RANKING_LIMIT,
            "sample_description": f"基于 {total_channels} 个频道的数据，展示 Top {RANKING_LIMIT}",
        },
        "total_views_rank": {
            "title": "总播放榜",
            "emoji": "📊",
            "description": "累计播放量最高的频道",
            "ranking_formula": "按总播放量降序排列",
            "sample_size": len(total_views_rank),
            "channels": [format_channel_with_analysis(c, "total_views") for c in total_views_rank],
        },
        "avg_views_rank": {
            "title": "平均播放榜",
            "emoji": "⚡",
            "description": "单视频平均播放量最高",
            "ranking_formula": "平均播放 = 总播放 / 视频数（至少3个视频）",
            "sample_size": len(avg_views_rank),
            "channels": [format_channel_with_analysis(c, "avg_views") for c in avg_views_rank],
        },
        "video_count_rank": {
            "title": "视频数榜",
            "emoji": "📹",
            "description": "发布视频数量最多",
            "ranking_formula": "按视频数量降序排列",
            "sample_size": len(video_count_rank),
            "channels": [format_channel_with_analysis(c, "video_count") for c in video_count_rank],
        },
        "dark_horse_rank": {
            "title": "黑马榜",
            "emoji": "🐴",
            "description": "小频道大爆款，内容驱动型",
            "ranking_formula": "黑马指数 = 最高播放 / (订阅数+1)，仅限订阅<1万",
            "sample_size": len(dark_horse_rank),
            "note": "需要订阅数据" if len(dark_horse_rank) == 0 else None,
            "channels": [format_channel_with_analysis(c, "dark_horse") for c in dark_horse_rank],
        },
        "efficiency_rank": {
            "title": "高效榜",
            "emoji": "🚀",
            "description": "订阅转化效率最高",
            "ranking_formula": "效率指数 = 平均播放 / 订阅数",
            "sample_size": len(efficiency_rank),
            "note": "需要订阅数据" if len(efficiency_rank) == 0 else None,
            "channels": [format_channel_with_analysis(c, "efficiency") for c in efficiency_rank],
        },
        "fast_growth_rank": {
            "title": "快速增长榜",
            "emoji": "📈",
            "description": "从0到1000粉丝最快的频道",
            "ranking_formula": "日均涨粉 = 订阅数 / 频道天数",
            "sample_size": len(fast_growth_rank),
            "note": "需要频道创建时间数据" if len(fast_growth_rank) == 0 else None,
            "channels": [format_channel_with_analysis(c, "fast_growth") for c in fast_growth_rank],
        },
    }


def _calculate_channel_stability(videos) -> dict:
    """
    计算频道稳定性分析

    稳定性指标：max/avg 比值
    - < 3: 极稳定（每个视频表现接近）
    - 3-10: 较稳定（偶有波动）
    - 10-20: 不稳定（靠爆款拉动）
    - > 20: 极不稳定（高度依赖单一爆款）
    """
    # 统计每个频道的数据
    channel_data = {}
    for v in videos:
        channel_key = v.channel_id if (v.channel_id and v.channel_id != 'None') else v.channel_name
        if not channel_key:
            continue

        if channel_key not in channel_data:
            channel_data[channel_key] = {
                "channel_id": v.channel_id,
                "channel_name": v.channel_name,
                "views": [],
                "total_views": 0,
                "video_count": 0,
            }

        channel_data[channel_key]["views"].append(v.view_count or 0)
        channel_data[channel_key]["total_views"] += v.view_count or 0
        channel_data[channel_key]["video_count"] += 1

    # 计算稳定性指标（只分析至少有3个视频的频道）
    stability_results = []
    for key, data in channel_data.items():
        if data["video_count"] < 3:
            continue

        views = data["views"]
        avg_views = data["total_views"] / data["video_count"]
        max_views = max(views)
        min_views = min(views)

        # max/avg 比值
        max_avg_ratio = max_views / avg_views if avg_views > 0 else 0

        # 判断稳定性等级
        if max_avg_ratio < 3:
            stability = "极稳定"
            stability_class = "success"
        elif max_avg_ratio < 10:
            stability = "较稳定"
            stability_class = "highlight"
        elif max_avg_ratio < 20:
            stability = "不稳定"
            stability_class = "warning"
        else:
            stability = "极不稳定"
            stability_class = "danger"

        stability_results.append({
            "channel_name": data["channel_name"],
            "channel_id": data["channel_id"],
            "video_count": data["video_count"],
            "avg_views": int(avg_views),
            "max_views": max_views,
            "min_views": min_views,
            "max_avg_ratio": round(max_avg_ratio, 2),
            "stability": stability,
            "stability_class": stability_class,
        })

    # 按 max/avg 比值排序（从高到低，不稳定的在前）
    stability_results.sort(key=lambda x: x["max_avg_ratio"], reverse=True)

    # 统计各稳定性等级的频道数量
    stability_distribution = {
        "极稳定": len([s for s in stability_results if s["stability"] == "极稳定"]),
        "较稳定": len([s for s in stability_results if s["stability"] == "较稳定"]),
        "不稳定": len([s for s in stability_results if s["stability"] == "不稳定"]),
        "极不稳定": len([s for s in stability_results if s["stability"] == "极不稳定"]),
    }

    return {
        "total_channels": len(stability_results),
        "distribution": stability_distribution,
        "top_unstable": stability_results[:10],  # 最不稳定的 Top 10
        "top_stable": sorted(stability_results, key=lambda x: x["max_avg_ratio"])[:10],  # 最稳定的 Top 10
        "insight": _generate_stability_insight(stability_distribution, stability_results),
    }


def _generate_stability_insight(distribution: dict, results: list) -> dict:
    """生成稳定性分析洞察"""
    total = sum(distribution.values())
    if total == 0:
        return {"summary": "暂无足够数据", "recommendation": ""}

    stable_pct = (distribution["极稳定"] + distribution["较稳定"]) / total * 100
    unstable_pct = (distribution["不稳定"] + distribution["极不稳定"]) / total * 100

    # 找出最稳定和最不稳定的频道
    most_stable = sorted(results, key=lambda x: x["max_avg_ratio"])[:3] if results else []
    most_unstable = sorted(results, key=lambda x: x["max_avg_ratio"], reverse=True)[:3] if results else []

    summary = f"{stable_pct:.0f}% 的频道表现稳定（max/avg < 10），{unstable_pct:.0f}% 的频道高度依赖爆款"

    recommendation = "建议学习稳定频道的内容策略，而非追求一次性爆款"
    if stable_pct > 70:
        recommendation = "该领域频道普遍稳定，建议追求持续输出而非等待爆款"
    elif unstable_pct > 50:
        recommendation = "该领域高度依赖爆款，需要找到可复制的爆款公式"

    return {
        "summary": summary,
        "recommendation": recommendation,
        "stable_pct": round(stable_pct, 1),
        "unstable_pct": round(unstable_pct, 1),
        "most_stable_channels": [c["channel_name"] for c in most_stable],
        "most_unstable_channels": [c["channel_name"] for c in most_unstable],
    }


def _analyze_region_distribution(channels: list) -> dict:
    """
    分析频道地区分布（Tab2 套利挖掘）
    """
    region_stats = {}

    for ch in channels:
        country = ch.get("country") or "未知"
        if country not in region_stats:
            region_stats[country] = {
                "channel_count": 0,
                "total_views": 0,
                "total_videos": 0,
            }
        region_stats[country]["channel_count"] += 1
        region_stats[country]["total_views"] += ch.get("total_views", 0)
        region_stats[country]["total_videos"] += ch.get("video_count", 0)

    # 计算均播放
    results = []
    for region, stats in region_stats.items():
        if stats["channel_count"] > 0:
            avg_views = stats["total_views"] // max(stats["total_videos"], 1)
            results.append({
                "region": region,
                "channel_count": stats["channel_count"],
                "avg_views": avg_views,
                "total_views": stats["total_views"],
                "feature": _get_region_feature(region, avg_views, stats["channel_count"]),
            })

    # 按均播放排序
    results.sort(key=lambda x: x["avg_views"], reverse=True)

    # 生成洞察
    if len(results) >= 2:
        top = results[0]
        second = results[1] if len(results) > 1 else None
        ratio = top["avg_views"] / max(results[-1]["avg_views"], 1) if results else 1
        insight = f"{top['region']}市场均播最高（{top['avg_views']:,}），是最低的 {ratio:.1f} 倍"
    else:
        insight = "数据量不足，无法分析地区差异"

    return {
        "regions": results[:10],  # Top 10 地区
        "insight": insight,
        "total_regions": len(results),
    }


def _get_region_feature(region: str, avg_views: int, channel_count: int) -> str:
    """根据地区特征返回描述"""
    features = {
        "Taiwan": "繁体主市场",
        "Hong Kong": "粤语市场",
        "United States": "海外华人",
        "Singapore": "高质量",
        "Malaysia": "东南亚",
        "Canada": "北美华人",
        "Australia": "澳洲华人",
        "China": "简体市场",
    }
    if region in features:
        return features[region]
    if avg_views > 100000:
        return "均播最高"
    if channel_count > 50:
        return "频道最多"
    return "新兴市场"


def _analyze_weekday_performance(videos: list) -> dict:
    """
    分析不同星期的发布效果（Tab5 发布策略）
    """
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_stats = {i: {"count": 0, "total_views": 0, "max_views": 0} for i in range(7)}

    for v in videos:
        if v.published_at:
            weekday = v.published_at.weekday()  # 0=周一, 6=周日
            views = v.view_count or 0
            weekday_stats[weekday]["count"] += 1
            weekday_stats[weekday]["total_views"] += views
            weekday_stats[weekday]["max_views"] = max(weekday_stats[weekday]["max_views"], views)

    results = []
    for i, stats in weekday_stats.items():
        if stats["count"] > 0:
            avg_views = stats["total_views"] // stats["count"]
            results.append({
                "weekday": weekday_names[i],
                "weekday_index": i,
                "video_count": stats["count"],
                "avg_views": avg_views,
                "max_views": stats["max_views"],
            })

    # 按均播放排序
    results.sort(key=lambda x: x["avg_views"], reverse=True)

    # 找出最佳和最差
    best = results[0] if results else None
    worst = results[-1] if results else None

    insight = ""
    if best and worst and best["avg_views"] > 0:
        ratio = best["avg_views"] / max(worst["avg_views"], 1)
        insight = f"{best['weekday']}发布效果最佳（均播{best['avg_views']:,}），是{worst['weekday']}的 {ratio:.1f} 倍"

    return {
        "weekdays": results,
        "best_day": best["weekday"] if best else None,
        "worst_day": worst["weekday"] if worst else None,
        "insight": insight,
    }


def _analyze_content_lifecycle(videos: list) -> dict:
    """
    分析内容类型生命周期（Tab3 选题决策）
    """
    from datetime import datetime
    now = datetime.now()

    # 按内容类型分组
    type_stats = {}
    for v in videos:
        content_type = _classify_content_type(v.title or "")
        if content_type not in type_stats:
            type_stats[content_type] = {
                "videos": [],
                "total_views": 0,
                "earliest": None,
                "latest": None,
            }

        type_stats[content_type]["videos"].append(v)
        type_stats[content_type]["total_views"] += v.view_count or 0

        if v.published_at:
            if type_stats[content_type]["earliest"] is None or v.published_at < type_stats[content_type]["earliest"]:
                type_stats[content_type]["earliest"] = v.published_at
            if type_stats[content_type]["latest"] is None or v.published_at > type_stats[content_type]["latest"]:
                type_stats[content_type]["latest"] = v.published_at

    results = []
    for content_type, stats in type_stats.items():
        video_count = len(stats["videos"])
        if video_count < 3:  # 至少3个视频才分析
            continue

        avg_views = stats["total_views"] // video_count

        # 计算活跃跨度
        if stats["earliest"] and stats["latest"]:
            span_days = (stats["latest"] - stats["earliest"]).days
            if span_days > 365:
                span_text = f"{span_days // 365}年"
            elif span_days > 30:
                span_text = f"{span_days // 30}个月"
            else:
                span_text = f"{span_days}天"
        else:
            span_days = 0
            span_text = "未知"

        # 判断阶段
        if span_days > 365 * 3 and avg_views > 50000:
            stage = "长青经典"
        elif span_days > 365 and avg_views > 30000:
            stage = "持续增长"
        elif span_days < 180 and avg_views > 50000:
            stage = "新兴爆发"
        elif avg_views > 80000:
            stage = "高热期"
        else:
            stage = "稳定期"

        results.append({
            "content_type": content_type,
            "video_count": video_count,
            "avg_views": avg_views,
            "span_text": span_text,
            "span_days": span_days,
            "stage": stage,
        })

    # 按均播放排序
    results.sort(key=lambda x: x["avg_views"], reverse=True)

    # 生成洞察
    evergreen = [r for r in results if r["stage"] == "长青经典"]
    emerging = [r for r in results if r["stage"] == "新兴爆发"]

    insight = ""
    if evergreen:
        insight += f"长青话题：{', '.join([e['content_type'] for e in evergreen[:3]])}。"
    if emerging:
        insight += f"新兴话题：{', '.join([e['content_type'] for e in emerging[:3]])}。"
    if not insight:
        insight = "各话题发展均衡，建议关注高均播话题。"

    return {
        "topics": results[:10],
        "insight": insight,
        "evergreen_topics": [e["content_type"] for e in evergreen],
        "emerging_topics": [e["content_type"] for e in emerging],
    }


def _classify_content_type(title: str) -> str:
    """根据标题分类内容类型"""
    title_lower = title.lower()

    if any(kw in title_lower for kw in ["八段锦", "太极", "气功", "功法", "站桩"]):
        return "功法养生"
    elif any(kw in title_lower for kw in ["穴位", "按摩", "经络", "推拿", "针灸"]):
        return "穴位经络"
    elif any(kw in title_lower for kw in ["食疗", "食物", "吃", "喝", "饮食", "营养"]):
        return "食疗养生"
    elif any(kw in title_lower for kw in ["中医", "中药", "调理", "体质"]):
        return "中医调理"
    elif any(kw in title_lower for kw in ["肝", "肾", "脾", "胃", "心", "肺", "血管", "血压"]):
        return "器官保健"
    else:
        return "其他"


def _generate_warnings(videos, now) -> list:
    """生成避坑提醒（最多 3 条）"""
    warnings = []

    # 分析数据
    durations = [v.duration for v in videos if v.duration]
    views = [v.view_count for v in videos if v.view_count]
    recent_videos = [v for v in videos if v.published_at and (now - v.published_at).days <= 90]

    # 警告 1: 时长陷阱
    if durations:
        avg_duration = sum(durations) / len(durations)
        short_count = len([d for d in durations if d < 60])
        if short_count > len(durations) * 0.3:
            warnings.append({
                "icon": "⏱️",
                "title": "避免过短视频",
                "content": f"该领域 {short_count} 个视频时长不足 1 分钟，平均播放量偏低。建议至少 3-5 分钟。",
                "severity": "high",
            })

    # 警告 2: 竞争激烈
    if views:
        median_views = sorted(views)[len(views) // 2]
        if median_views < 1000:
            warnings.append({
                "icon": "⚠️",
                "title": "竞争激烈，注意差异化",
                "content": f"该领域中位数播放量仅 {median_views}，说明大部分视频表现一般。必须找到差异化角度。",
                "severity": "medium",
            })

    # 警告 3: 发布时机
    if recent_videos:
        recent_success = [v for v in recent_videos if (v.view_count or 0) >= 10000]
        success_rate = len(recent_success) / len(recent_videos) if recent_videos else 0
        if success_rate < 0.1:
            warnings.append({
                "icon": "📅",
                "title": "近期爆款率较低",
                "content": f"近 90 天仅 {len(recent_success)}/{len(recent_videos)} 个视频突破万播，市场可能趋于饱和。",
                "severity": "medium",
            })

    # 如果没有警告，给一个通用提醒
    if not warnings:
        warnings.append({
            "icon": "💡",
            "title": "坚持原创内容",
            "content": "数据显示该领域整体表现良好，建议专注内容质量和持续输出。",
            "severity": "low",
        })

    return warnings[:3]


# ============================================================
# 用户洞察 API（评论分析）
# ============================================================

@app.get("/api/user-insights/{keyword}")
async def get_user_insights(
    keyword: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    用户洞察 API - 分析评论数据

    参数：
    - keyword: 关键词
    - date_from: 开始日期 (YYYY-MM-DD)
    - date_to: 结束日期 (YYYY-MM-DD)

    返回：
    1. 热词分析（模式38）
    2. 问题类型分布（模式39）
    3. 情感分布（模式40）
    4. 话题趋势（模式41）
    5. 高赞评论特征（模式42）
    6. 用户语言分布（模式43）
    """
    import re
    from collections import Counter, defaultdict

    # 检查数据库是否可用（Neon 或本地 SQLite）
    if not db_exists():
        return {"status": "error", "message": "数据库不存在"}

    conn = db_get_connection()
    cursor = conn.cursor()

    # 构建时间过滤条件
    date_conditions = []
    params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]

    if date_from:
        date_conditions.append("cv.published_at >= ?")
        params.append(date_from)
    if date_to:
        date_conditions.append("cv.published_at <= ?")
        params.append(date_to + " 23:59:59")

    date_filter = " AND " + " AND ".join(date_conditions) if date_conditions else ""

    # 获取与关键词相关视频的评论（支持时间过滤）
    cursor.execute(f"""
        SELECT vc.text, vc.like_count, vc.published_at
        FROM video_comments vc
        JOIN competitor_videos cv ON vc.youtube_id = cv.youtube_id
        WHERE (cv.title LIKE ? OR cv.keyword_source LIKE ? OR cv.theme LIKE ?)
        AND vc.text IS NOT NULL
        {date_filter}
    """, params)

    comments = cursor.fetchall()

    # 如果没有匹配，获取所有评论（保持时间过滤）
    if len(comments) < 100:
        fallback_params = []
        fallback_conditions = ["text IS NOT NULL"]
        if date_from:
            fallback_conditions.append("published_at >= ?")
            fallback_params.append(date_from)
        if date_to:
            fallback_conditions.append("published_at <= ?")
            fallback_params.append(date_to + " 23:59:59")

        cursor.execute(f"""
            SELECT text, like_count, published_at
            FROM video_comments
            WHERE {' AND '.join(fallback_conditions)}
        """, fallback_params)
        comments = cursor.fetchall()

    if not comments:
        conn.close()
        return {
            "status": "ok",
            "total_comments": 0,
            "message": "暂无评论数据，请先运行 python3 scripts/fetch_comments.py 采集评论"
        }

    total_comments = len(comments)

    # ========== 模式38：热词分析 ==========
    try:
        import jieba
        all_text = ' '.join([c[0] for c in comments if c[0]])
        words = jieba.lcut(all_text)
        stopwords = {'的', '是', '在', '了', '和', '我', '有', '也', '不', '就', '都', '这', '你', '他', '她', '它', '很', '会', '要', '可以', '能', '到', '说', '去', '对', '被', '让', '把', '给', '从', '但', '还', '为', '与', '着', '得', '上', '下', '来', '出', '个', '们', '么', '那', '这个', '一', '一个', '\n', ' ', '', '可以', '觉得', '这样', '自己', '现在', '知道', '没有', '真的', '什么', '怎么', '因为', '所以', '如果', '虽然', '但是', '而且', '或者', '只是', '这么', '那么', '非常', '已经', '以后', '之前', '一些', '一样', '希望', '大家'}
        words = [w.strip() for w in words if len(w.strip()) >= 2 and w.strip() not in stopwords and not any(c in w for c in '\n\r\t')]
        word_counts = Counter(words).most_common(20)

        # 归类热词
        hotwords = []
        category_map = {
            '感恩': '互动', '謝謝': '互动', '谢谢': '互动', '感謝': '互动', '感谢': '互动',
            '老師': '互动', '老师': '互动', '醫師': '互动', '医师': '互动', '醫生': '互动', '医生': '互动',
            '分享': '互动', '健康': '效果', '身體': '效果', '身体': '效果', '有效': '效果',
            '請問': '疑问', '请问': '疑问', '每天': '行动', '運動': '功法', '运动': '功法'
        }
        for i, (word, count) in enumerate(word_counts, 1):
            category = category_map.get(word, '其他')
            hotwords.append({
                "rank": i,
                "word": word,
                "count": count,
                "category": category
            })
    except ImportError:
        hotwords = []

    # ========== 模式39：问题类型分析 ==========
    question_patterns = {
        'YES_NO': r'[可以嗎|可以吗|行嗎|行吗|好嗎|好吗|對嗎|对吗|是嗎|是吗|會嗎|会吗|能嗎|能吗|嗎\?|吗\?]',
        'HOW': r'[怎麼|怎么|如何|怎樣|怎样|咋]',
        'WHY': r'[為什麼|为什么|為何|为何|何故]',
        'WHAT': r'[什麼是|什么是|是什麼|是什么|啥是]',
        'WHERE': r'[哪裡|哪里|哪兒|哪儿|何處|何处|在哪]'
    }

    question_counts = {k: 0 for k in question_patterns}
    question_counts['OTHER'] = 0
    total_questions = 0

    for text, _, _ in comments:
        if not text:
            continue
        if '?' in text or '？' in text or '嗎' in text or '吗' in text:
            total_questions += 1
            matched = False
            for qtype, pattern in question_patterns.items():
                if re.search(pattern, text):
                    question_counts[qtype] += 1
                    matched = True
                    break
            if not matched:
                question_counts['OTHER'] += 1

    questions_data = {
        "total": total_questions,
        "percentage": round(total_questions / total_comments * 100, 1) if total_comments > 0 else 0,
        "types": [
            {"type": "YES_NO", "count": question_counts['YES_NO'], "label": "确认类「可以吗？」"},
            {"type": "HOW", "count": question_counts['HOW'], "label": "方法类「怎么做？」"},
            {"type": "WHERE", "count": question_counts['WHERE'], "label": "资源类「哪里找？」"},
            {"type": "WHAT", "count": question_counts['WHAT'], "label": "定义类「是什么？」"},
            {"type": "WHY", "count": question_counts['WHY'], "label": "原因类「为什么？」"},
            {"type": "OTHER", "count": question_counts['OTHER'], "label": "其他问句"}
        ]
    }

    # ========== 模式40：情感分析 ==========
    positive_words = ['謝謝', '谢谢', '感恩', '感謝', '感谢', '棒', '好', '讚', '赞', '喜歡', '喜欢', '有效', '厲害', '厉害', '清楚', '實用', '实用', '受益', '幫助', '帮助']
    negative_words = ['爛', '烂', '差', '廢', '废', '沒用', '没用', '騙', '骗', '假', '垃圾', '無聊', '无聊', '失望']

    pos_count = 0
    neg_count = 0
    neu_count = 0

    for text, _, _ in comments:
        if not text:
            continue
        has_pos = any(w in text for w in positive_words)
        has_neg = any(w in text for w in negative_words)
        if has_pos and not has_neg:
            pos_count += 1
        elif has_neg and not has_pos:
            neg_count += 1
        else:
            neu_count += 1

    sentiment_data = {
        "positive": {"count": pos_count, "percentage": round(pos_count / total_comments * 100, 1)},
        "neutral": {"count": neu_count, "percentage": round(neu_count / total_comments * 100, 1)},
        "negative": {"count": neg_count, "percentage": round(neg_count / total_comments * 100, 1)},
        "score": round((pos_count - neg_count) / total_comments, 3) if total_comments > 0 else 0
    }

    # ========== 模式43：用户语言分布 ==========
    def detect_language(text):
        """
        检测评论语言（基于字符集分析）

        逻辑：
        1. 如果有日文假名 → 日语
        2. 如果有韩文字符 → 韩语
        3. 如果有CJK汉字 → 中文（再区分简繁体）
        4. 如果有英文字母 → 英语
        5. 纯表情/纯数字/纯标点 → 根据内容长度判断
        """
        if not text or not text.strip():
            return 'unknown'

        # 统计各类字符
        cjk_count = 0       # 中日韩汉字总数
        english = 0         # 英文字母
        japanese_kana = 0   # 日文假名（平假名+片假名）
        korean = 0          # 韩文

        # 简体特征字（大陆简化字）
        simplified_chars = set(
            '国为学这来说时会开关门问东车长马风见让认识语读写画图电视听爱钱银'
            '团组织员决设计从达进远连运还边过华众参办处备复头发现实应该条级纸'
            '编练习务确验证谈护转轻较农讲获数响弹劳卫规则总结构节约专业压医药'
            '厂广产业单报导头号张机杨档极标权汇汉沟济点热营环线细终经网结获'
        )
        # 繁体特征字（台港澳繁体字）
        traditional_chars = set(
            '國為學這來說時會開關門問東車長馬風見讓認識語讀寫畫圖電視聽愛錢銀'
            '團組織員決設計從達進遠連運還邊過華眾參辦處備復頭發現實應該條級紙'
            '編練習務確驗證談護轉輕較農講獲數響彈勞衛規則總結構節約專業壓醫藥'
            '廠廣產業單報導頭號張機楊檔極標權匯漢溝濟點熱營環線細終經網結獲'
        )

        zh_simplified_score = 0
        zh_traditional_score = 0

        for char in text:
            code = ord(char)
            # 英文字母 (A-Z, a-z)
            if (0x0041 <= code <= 0x005A) or (0x0061 <= code <= 0x007A):
                english += 1
            # 日文平假名 (3040-309F) 和片假名 (30A0-30FF)
            elif 0x3040 <= code <= 0x30FF:
                japanese_kana += 1
            # 韩文 (AC00-D7AF)
            elif 0xAC00 <= code <= 0xD7AF:
                korean += 1
            # 中日韩汉字 (4E00-9FFF) - 包含所有汉字
            elif 0x4E00 <= code <= 0x9FFF:
                cjk_count += 1
                if char in simplified_chars:
                    zh_simplified_score += 1
                elif char in traditional_chars:
                    zh_traditional_score += 1

        # 判断语言优先级：日语 > 韩语 > 中文 > 英语

        # 1. 有日文假名 → 日语（日语特有，即使混有汉字也是日语）
        if japanese_kana >= 2:
            return 'ja'

        # 2. 有韩文 → 韩语
        if korean >= 2:
            return 'ko'

        # 3. 有汉字 → 中文（区分简繁体）
        if cjk_count > 0:
            # 根据特征字分数区分简繁体
            if zh_traditional_score > zh_simplified_score:
                return 'zh-TW'  # 繁体中文
            else:
                return 'zh-CN'  # 简体中文（默认，因为大部分汉字是通用的）

        # 4. 有英文字母 → 英语
        if english > 0:
            return 'en'

        # 5. 纯表情/数字/标点 → 归入"表情"类别（这是真正的"无法判断文字语言"）
        return 'emoji'

    # 统计语言分布
    language_counts = defaultdict(int)
    for text, _, _ in comments:
        if text:
            lang = detect_language(text)
            language_counts[lang] += 1

    # 语言名称映射
    lang_names = {
        'zh-CN': '简体中文',
        'zh-TW': '繁体中文',
        'en': '英语',
        'ja': '日语',
        'ko': '韩语',
        'emoji': '纯表情/符号',  # 没有文字内容，只有表情或符号
        'unknown': '未知'
    }

    language_data = {
        "total": total_comments,
        "distribution": [
            {
                "code": code,
                "name": lang_names.get(code, code),
                "count": count,
                "percentage": round(count / total_comments * 100, 1) if total_comments > 0 else 0
            }
            for code, count in sorted(language_counts.items(), key=lambda x: -x[1])
        ]
    }

    # ========== 模式41：话题趋势 ==========
    topics = {
        '养生': r'養生|养生|保健|健康',
        '睡眠': r'睡眠|失眠|睡不著|睡不着|入睡',
        '穴位': r'穴位|穴道|按摩',
        '八段锦': r'八段錦|八段锦',
        '太极': r'太極|太极|太極拳|太极拳',
        '气功': r'氣功|气功'
    }

    monthly_topics = defaultdict(lambda: defaultdict(int))

    for text, _, pub_time in comments:
        if not text or not pub_time:
            continue
        month_match = re.search(r'(\d{4})-(\d{2})', str(pub_time))
        if month_match:
            month_key = f"{month_match.group(1)}-{month_match.group(2)}"
            for topic, pattern in topics.items():
                if re.search(pattern, text):
                    monthly_topics[month_key][topic] += 1

    sorted_months = sorted(monthly_topics.keys())[-6:] if monthly_topics else []

    trend_data = {
        "months": sorted_months,
        "topics": {}
    }
    for topic in topics:
        trend_data["topics"][topic] = [monthly_topics[m].get(topic, 0) for m in sorted_months]

    # ========== 模式42：高赞评论特征 ==========
    cursor.execute("""
        SELECT text, like_count FROM video_comments
        WHERE like_count > 0 AND text IS NOT NULL
        ORDER BY like_count DESC LIMIT 100
    """)
    top_comments = cursor.fetchall()

    if top_comments:
        avg_len = sum(len(t[0]) for t in top_comments) / len(top_comments)
        experience_words = ['我', '自己', '親身', '亲身', '試過', '试过', '經歷', '经历', '實踐', '实践']
        has_experience = sum(1 for t in top_comments if any(w in t[0] for w in experience_words))
        has_question = sum(1 for t in top_comments if '?' in t[0] or '？' in t[0])

        high_liked_data = {
            "avg_length": round(avg_len),
            "has_experience_pct": has_experience,
            "has_question_pct": has_question,
            "max_likes": top_comments[0][1] if top_comments else 0
        }
    else:
        high_liked_data = {
            "avg_length": 0,
            "has_experience_pct": 0,
            "has_question_pct": 0,
            "max_likes": 0,
            "examples": []
        }

    # ========== 真实案例数据 ==========

    # 评论最多的视频（互动热门）
    # PostgreSQL 要求 GROUP BY 包含所有非聚合列
    cursor.execute("""
        SELECT cv.title, cv.channel_name, cv.view_count, cv.youtube_id, COUNT(vc.id) as comment_count
        FROM competitor_videos cv
        JOIN video_comments vc ON cv.youtube_id = vc.youtube_id
        GROUP BY cv.youtube_id, cv.title, cv.channel_name, cv.view_count
        ORDER BY comment_count DESC
        LIMIT 5
    """)
    top_commented_videos = [
        {"title": r[0][:50] + "..." if len(r[0]) > 50 else r[0], "channel": r[1], "views": r[2], "youtube_id": r[3], "comments": r[4]}
        for r in cursor.fetchall()
    ]

    # 高赞评论案例（带视频来源）
    cursor.execute("""
        SELECT vc.text, vc.like_count, cv.title, cv.channel_name, cv.youtube_id
        FROM video_comments vc
        JOIN competitor_videos cv ON vc.youtube_id = cv.youtube_id
        WHERE vc.like_count > 50 AND length(vc.text) > 20 AND length(vc.text) < 200
        ORDER BY vc.like_count DESC
        LIMIT 5
    """)
    top_liked_comments = [
        {"text": r[0][:100] + "..." if len(r[0]) > 100 else r[0], "likes": r[1], "video_title": r[2][:40] + "..." if len(r[2]) > 40 else r[2], "channel": r[3], "youtube_id": r[4]}
        for r in cursor.fetchall()
    ]

    # 用户问题案例（带视频来源）
    cursor.execute("""
        SELECT vc.text, cv.title, cv.channel_name, cv.youtube_id
        FROM video_comments vc
        JOIN competitor_videos cv ON vc.youtube_id = cv.youtube_id
        WHERE (vc.text LIKE '%可以嗎%' OR vc.text LIKE '%可以吗%' OR vc.text LIKE '%怎麼%' OR vc.text LIKE '%怎么%' OR vc.text LIKE '%如何%')
        AND length(vc.text) > 10 AND length(vc.text) < 100
        LIMIT 5
    """)
    question_examples = [
        {"text": r[0], "video_title": r[1][:40] + "..." if len(r[1]) > 40 else r[1], "channel": r[2], "youtube_id": r[3]}
        for r in cursor.fetchall()
    ]

    # 更新高赞数据添加案例
    if top_comments:
        high_liked_data["examples"] = [
            {"text": t[0][:150] + "..." if len(t[0]) > 150 else t[0], "likes": t[1]}
            for t in top_comments[:3]
        ]

    conn.close()

    return {
        "status": "ok",
        "keyword": keyword,
        "total_comments": total_comments,
        "hotwords": hotwords,
        "questions": questions_data,
        "sentiment": sentiment_data,
        "language": language_data,  # 模式43：语言分布
        "trends": trend_data,
        "high_liked": high_liked_data,
        "real_examples": {
            "top_commented_videos": top_commented_videos,
            "top_liked_comments": top_liked_comments,
            "question_examples": question_examples
        }
    }


# ============================================================
# 话题网络分析 API（有趣度计算）
# ============================================================

@app.get("/api/topic-network/{theme}")
async def analyze_topic_network(theme: str, min_cooccurrence: int = 2, top_n: int = 30):
    """
    话题网络分析 - 计算话题有趣度

    有趣度 = 中介中心性 / 程度中心性
    高有趣度 = 高桥梁价值 + 低传播饱和度 = 被低估的高价值节点
    """
    try:
        import networkx as nx
        from collections import defaultdict, Counter

        collector = _get_data_collector()
        all_videos = collector.get_videos_from_db(theme=theme, min_views=0, limit=10000)

        if not all_videos:
            all_videos = collector.get_videos_from_db(keyword_like=theme, min_views=0, limit=10000)

        if not all_videos:
            return {"status": "error", "message": f"没有找到主题 '{theme}' 的数据"}

        # 1. 提取标签并统计
        tag_counter = Counter()
        tag_views = defaultdict(int)

        for video in all_videos:
            tags = video.tags or []
            for tag in tags:
                tag = tag.strip().lower()
                if 2 <= len(tag) <= 50:
                    tag_counter[tag] += 1
                    tag_views[tag] += video.view_count or 0

        if len(tag_counter) < 10:
            return {"status": "error", "message": f"标签数据不足（仅 {len(tag_counter)} 个）"}

        # 2. 构建共现网络
        G = nx.Graph()
        cooccurrence = defaultdict(int)

        for video in all_videos:
            tags = [t.strip().lower() for t in (video.tags or []) if 2 <= len(t.strip()) <= 50]
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    if tag1 != tag2:
                        key = tuple(sorted([tag1, tag2]))
                        cooccurrence[key] += 1

        # 添加节点和边
        for (tag1, tag2), count in cooccurrence.items():
            if count >= min_cooccurrence:
                if not G.has_node(tag1):
                    G.add_node(tag1, video_count=tag_counter[tag1], total_views=tag_views[tag1])
                if not G.has_node(tag2):
                    G.add_node(tag2, video_count=tag_counter[tag2], total_views=tag_views[tag2])
                G.add_edge(tag1, tag2, weight=count)

        if G.number_of_nodes() < 5:
            return {"status": "error", "message": "网络节点不足，请降低 min_cooccurrence"}

        # 3. 计算中心性
        k = min(300, G.number_of_nodes())
        betweenness = nx.betweenness_centrality(G, k=k, normalized=True)
        degree = nx.degree_centrality(G)

        # 4. 计算有趣度
        epsilon = 0.001
        interestingness = {node: betweenness.get(node, 0) / (degree.get(node, 0) + epsilon) for node in G.nodes()}

        # 5. 排序 Top N
        sorted_topics = sorted(interestingness.items(), key=lambda x: x[1], reverse=True)[:top_n]

        # 6. 构建结果
        topic_rankings = []
        for rank, (topic, score) in enumerate(sorted_topics, 1):
            node_data = G.nodes[topic]
            video_count = node_data.get("video_count", 0)
            total_views = node_data.get("total_views", 0)

            # 行动建议
            if score > 1.0:
                action = {"level": "high", "emoji": "🔥", "text": "立即创作"}
            elif score > 0.3:
                action = {"level": "medium", "emoji": "💡", "text": "值得尝试"}
            else:
                action = {"level": "low", "emoji": "⚪", "text": "需差异化"}

            topic_rankings.append({
                "rank": rank,
                "topic": topic,
                "interestingness": round(score, 3),
                "betweenness": round(betweenness.get(topic, 0), 4),
                "degree": round(degree.get(topic, 0), 4),
                "video_count": video_count,
                "total_views": total_views,
                "avg_views": total_views // max(video_count, 1),
                "action": action
            })

        return {
            "status": "ok",
            "theme": theme,
            "topic_rankings": topic_rankings,
            "network_stats": {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "density": round(nx.density(G), 4),
            },
            "formula": "有趣度 = 中介中心性 / 程度中心性"
        }

    except ImportError:
        return {"status": "error", "message": "需要安装 networkx: pip install networkx"}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# ============================================================
# 全局榜单 API
# ============================================================

@app.get("/api/leaderboard")
async def get_leaderboard():
    """
    获取全局榜单数据

    返回：
    - Top 50 黑马频道（订阅少但播放好的频道）
    - Top 50 热门视频（按播放量）
    - Top 10 热门话题（按视频数/播放量）
    """
    try:
        db_path = Path(__file__).parent / "data" / "youtube_pipeline.db"
        conn = db_get_connection(str(db_path))
        cursor = conn.cursor()

        # ========== Top 50 黑马频道 ==========
        # 黑马指数 = 平均播放量 / max(订阅数, 1000)
        # 只选择至少有2个视频的频道，且有订阅数据
        cursor.execute("""
            SELECT
                channel_name,
                channel_id,
                COUNT(*) as video_count,
                AVG(view_count) as avg_views,
                MAX(view_count) as max_views,
                SUM(view_count) as total_views,
                MAX(subscriber_count) as subscriber_count,
                AVG(view_count) * 1.0 / GREATEST(MAX(subscriber_count), 1000) as dark_horse_score
            FROM competitor_videos
            WHERE channel_name IS NOT NULL
              AND channel_name != ''
              AND view_count > 0
            GROUP BY channel_id, channel_name
            HAVING COUNT(*) >= 2 AND MAX(subscriber_count) > 0
            ORDER BY dark_horse_score DESC
            LIMIT 50
        """)

        dark_horse_channels = []
        for row in cursor.fetchall():
            channel_name, channel_id, video_count, avg_views, max_views, total_views, subscriber_count, score = row
            dark_horse_channels.append({
                "rank": len(dark_horse_channels) + 1,
                "channel_name": channel_name,
                "channel_id": channel_id,
                "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                "video_count": video_count,
                "avg_views": int(avg_views or 0),
                "max_views": int(max_views or 0),
                "total_views": int(total_views or 0),
                "subscriber_count": int(subscriber_count or 0),
                "dark_horse_score": round(score or 0, 2)
            })

        # ========== Top 50 热门视频 ==========
        cursor.execute("""
            SELECT
                youtube_id,
                title,
                channel_name,
                channel_id,
                view_count,
                like_count,
                comment_count,
                subscriber_count,
                published_at,
                duration
            FROM competitor_videos
            WHERE view_count > 0
            ORDER BY view_count DESC
            LIMIT 50
        """)

        top_videos = []
        for row in cursor.fetchall():
            youtube_id, title, channel_name, channel_id, view_count, like_count, comment_count, subscriber_count, published_at, duration = row
            top_videos.append({
                "rank": len(top_videos) + 1,
                "youtube_id": youtube_id,
                "title": title[:60] + "..." if title and len(title) > 60 else title,
                "full_title": title,
                "video_url": f"https://www.youtube.com/watch?v={youtube_id}",
                "channel_name": channel_name,
                "channel_id": channel_id,
                "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                "view_count": int(view_count or 0),
                "like_count": int(like_count or 0),
                "comment_count": int(comment_count or 0),
                "subscriber_count": int(subscriber_count or 0),
                "published_at": published_at,
                "duration": int(duration or 0)
            })

        # ========== Top 10 热门话题 ==========
        # 使用 keyword_source 作为话题来源（比 theme 更丰富）
        cursor.execute("""
            SELECT
                keyword_source,
                COUNT(*) as video_count,
                SUM(view_count) as total_views,
                AVG(view_count) as avg_views,
                COUNT(DISTINCT COALESCE(channel_id, channel_name)) as channel_count
            FROM competitor_videos
            WHERE keyword_source IS NOT NULL AND keyword_source != ''
            GROUP BY keyword_source
            ORDER BY video_count DESC, total_views DESC
            LIMIT 10
        """)

        top_topics = []
        for row in cursor.fetchall():
            keyword_source, video_count, total_views, avg_views, channel_count = row
            top_topics.append({
                "rank": len(top_topics) + 1,
                "topic": keyword_source,
                "video_count": int(video_count or 0),
                "total_views": int(total_views or 0),
                "avg_views": int(avg_views or 0),
                "channel_count": int(channel_count or 0)
            })

        # ========== 统计概览 ==========
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT COALESCE(channel_id, channel_name)), SUM(view_count) FROM competitor_videos")
        stats = cursor.fetchone()

        conn.close()

        return {
            "status": "ok",
            "data": {
                "dark_horse_channels": dark_horse_channels,
                "top_videos": top_videos,
                "top_topics": top_topics,
                "stats": {
                    "total_videos": stats[0] or 0,
                    "total_channels": stats[1] or 0,
                    "total_views": stats[2] or 0
                }
            }
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# ============================================================
# 中心性分析 API（套利分析）
# ============================================================

@app.get("/api/centrality")
async def get_centrality_analysis():
    """
    获取网络中心性分析数据

    返回：
    - 中介中心性 Top 50（话题、频道、视频、标题词）
    - 程度中心性 Top 50（话题、频道、视频、标题词）
    - 套利机会（高中介+低播放/低粉丝）
    """
    try:
        from src.research.network_centrality import get_centrality_data

        db_path = Path(__file__).parent / "data" / "youtube_pipeline.db"

        if not db_exists(str(db_path)):
            return {"status": "error", "message": "数据库不存在"}

        data = get_centrality_data(str(db_path))

        # 为每个列表添加 rank
        for category in ['betweenness', 'degree']:
            for list_name in ['topics', 'channels', 'videos', 'words']:
                items = data.get(category, {}).get(list_name, [])
                for i, item in enumerate(items):
                    item['rank'] = i + 1

        for list_name in ['high_betweenness_low_views_videos', 'high_betweenness_low_subs_channels']:
            items = data.get('arbitrage', {}).get(list_name, [])
            for i, item in enumerate(items):
                item['rank'] = i + 1

        return {
            "status": "ok",
            "data": data
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# 中心性数据缓存（避免每次请求都重新计算）
_centrality_cache = {"data": None, "timestamp": 0, "ttl": 300}  # 5分钟缓存


@app.get("/api/arbitrage")
async def get_arbitrage_combined():
    """
    获取整合后的套利分析数据（包含榜单 + 中心性分析）

    返回：
    - 原有榜单数据（黑马频道、热门视频、热门话题）
    - 中心性榜单（中介中心性、程度中心性 Top 50）
    - 套利机会榜单

    使用 5 分钟缓存加速响应
    """
    try:
        from src.research.network_centrality import get_centrality_data

        db_path = Path(__file__).parent / "data" / "youtube_pipeline.db"

        if not db_exists(str(db_path)):
            return {"status": "error", "message": "数据库不存在"}

        # 检查缓存是否有效
        current_time = time.time()
        if _centrality_cache["data"] and (current_time - _centrality_cache["timestamp"]) < _centrality_cache["ttl"]:
            centrality_data = _centrality_cache["data"]
        else:
            # 重新计算并缓存
            centrality_data = get_centrality_data(str(db_path))
            _centrality_cache["data"] = centrality_data
            _centrality_cache["timestamp"] = current_time

        # 获取原有榜单数据
        conn = db_get_connection(str(db_path))
        cursor = conn.cursor()

        # ========== Top 50 黑马频道 ==========
        cursor.execute("""
            SELECT
                channel_name,
                channel_id,
                COUNT(*) as video_count,
                AVG(view_count) as avg_views,
                MAX(view_count) as max_views,
                SUM(view_count) as total_views,
                MAX(subscriber_count) as subscriber_count,
                AVG(view_count) * 1.0 / GREATEST(MAX(subscriber_count), 1000) as dark_horse_score
            FROM competitor_videos
            WHERE channel_name IS NOT NULL
              AND channel_name != ''
              AND view_count > 0
            GROUP BY channel_id, channel_name
            HAVING COUNT(*) >= 2 AND MAX(subscriber_count) > 0
            ORDER BY dark_horse_score DESC
            LIMIT 50
        """)

        dark_horse_channels = []
        for row in cursor.fetchall():
            channel_name, channel_id, video_count, avg_views, max_views, total_views, subscriber_count, score = row
            dark_horse_channels.append({
                "rank": len(dark_horse_channels) + 1,
                "channel_name": channel_name,
                "channel_id": channel_id,
                "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                "video_count": video_count,
                "avg_views": int(avg_views or 0),
                "max_views": int(max_views or 0),
                "total_views": int(total_views or 0),
                "subscriber_count": int(subscriber_count or 0),
                "dark_horse_score": round(score or 0, 2)
            })

        # ========== Top 50 热门视频（按播放量）==========
        cursor.execute("""
            SELECT
                youtube_id,
                title,
                channel_name,
                channel_id,
                view_count,
                like_count,
                comment_count,
                subscriber_count,
                published_at,
                duration
            FROM competitor_videos
            WHERE view_count > 0
            ORDER BY view_count DESC
            LIMIT 50
        """)

        top_videos_by_views = []
        for row in cursor.fetchall():
            youtube_id, title, channel_name, channel_id, view_count, like_count, comment_count, subscriber_count, published_at, duration = row
            top_videos_by_views.append({
                "rank": len(top_videos_by_views) + 1,
                "youtube_id": youtube_id,
                "title": title[:60] + "..." if title and len(title) > 60 else title,
                "full_title": title,
                "video_url": f"https://www.youtube.com/watch?v={youtube_id}",
                "channel_name": channel_name,
                "channel_id": channel_id,
                "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                "view_count": int(view_count or 0),
                "like_count": int(like_count or 0),
                "comment_count": int(comment_count or 0),
                "subscriber_count": int(subscriber_count or 0),
            })

        # ========== Top 50 频道（按粉丝数）==========
        cursor.execute("""
            SELECT
                channel_name,
                channel_id,
                COUNT(*) as video_count,
                AVG(view_count) as avg_views,
                SUM(view_count) as total_views,
                MAX(subscriber_count) as subscriber_count
            FROM competitor_videos
            WHERE channel_name IS NOT NULL
              AND channel_name != ''
              AND subscriber_count > 0
            GROUP BY channel_id, channel_name
            ORDER BY subscriber_count DESC
            LIMIT 50
        """)

        top_channels_by_subs = []
        for row in cursor.fetchall():
            channel_name, channel_id, video_count, avg_views, total_views, subscriber_count = row
            top_channels_by_subs.append({
                "rank": len(top_channels_by_subs) + 1,
                "channel_name": channel_name,
                "channel_id": channel_id,
                "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                "video_count": video_count,
                "avg_views": int(avg_views or 0),
                "total_views": int(total_views or 0),
                "subscriber_count": int(subscriber_count or 0),
            })

        # ========== Top 10 热门话题 ==========
        cursor.execute("""
            SELECT
                keyword_source,
                COUNT(*) as video_count,
                SUM(view_count) as total_views,
                AVG(view_count) as avg_views,
                COUNT(DISTINCT COALESCE(channel_id, channel_name)) as channel_count
            FROM competitor_videos
            WHERE keyword_source IS NOT NULL AND keyword_source != ''
            GROUP BY keyword_source
            ORDER BY video_count DESC, total_views DESC
            LIMIT 50
        """)

        top_topics = []
        for row in cursor.fetchall():
            keyword_source, video_count, total_views, avg_views, channel_count = row
            top_topics.append({
                "rank": len(top_topics) + 1,
                "topic": keyword_source,
                "video_count": int(video_count or 0),
                "total_views": int(total_views or 0),
                "avg_views": int(avg_views or 0),
                "channel_count": int(channel_count or 0)
            })

        conn.close()

        # 为中心性数据添加 rank
        for category in ['betweenness', 'degree']:
            for list_name in ['topics', 'channels', 'videos', 'words']:
                items = centrality_data.get(category, {}).get(list_name, [])
                for i, item in enumerate(items):
                    item['rank'] = i + 1

        for list_name in ['high_betweenness_low_views_videos', 'high_betweenness_low_subs_channels']:
            items = centrality_data.get('arbitrage', {}).get(list_name, [])
            for i, item in enumerate(items):
                item['rank'] = i + 1

        return {
            "status": "ok",
            "data": {
                # 原有榜单
                "traditional_leaderboard": {
                    "dark_horse_channels": dark_horse_channels,
                    "top_videos_by_views": top_videos_by_views,
                    "top_channels_by_subs": top_channels_by_subs,
                    "top_topics": top_topics
                },
                # 中心性榜单
                "centrality_leaderboard": {
                    "betweenness": centrality_data.get('betweenness', {}),
                    "degree": centrality_data.get('degree', {})
                },
                # 套利机会
                "arbitrage_opportunities": centrality_data.get('arbitrage', {}),
                # 统计信息
                "stats": centrality_data.get('stats', {})
            }
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# ============================================================
# 频道详情 API（向高手学习模块）
# ============================================================

@app.get("/api/channel-detail/{channel_id}")
async def get_channel_detail(channel_id: str):
    """
    获取频道详情数据（用于"向高手学习"模块）

    返回：
    - 频道基本信息（订阅数、总播放等）
    - 视频列表（按播放量排序）
    - 话题分布（按 keyword_source 分组统计）
    - 时长分布
    - 成长轨迹（基于频道创建时间）
    """
    try:
        db_path = Path(__file__).parent / "data" / "youtube_pipeline.db"

        if not db_exists(str(db_path)):
            return {"status": "error", "message": "数据库不存在"}

        conn = db_get_connection(str(db_path), row_factory=sqlite3.Row)
        cursor = conn.cursor()

        # 1. 获取频道的所有视频
        cursor.execute("""
            SELECT
                youtube_id,
                title,
                channel_name,
                view_count,
                like_count,
                comment_count,
                duration,
                published_at,
                keyword_source,
                thumbnail_url
            FROM competitor_videos
            WHERE channel_id = ? OR channel_name = (
                SELECT channel_name FROM competitor_videos WHERE channel_id = ? LIMIT 1
            )
            ORDER BY view_count DESC
        """, (channel_id, channel_id))

        videos = cursor.fetchall()

        if not videos:
            conn.close()
            return {"status": "error", "message": f"未找到频道 {channel_id} 的数据"}

        # 2. 获取频道信息（从 channels 表）
        cursor.execute("""
            SELECT channel_name, subscriber_count, video_count, total_views,
                   country, description, created_at, canonical_url
            FROM channels
            WHERE channel_id = ?
        """, (channel_id,))
        channel_row = cursor.fetchone()

        # 基本统计
        channel_name = videos[0]['channel_name'] if videos else '未知频道'
        total_videos = len(videos)
        total_views = sum(v['view_count'] or 0 for v in videos)
        total_likes = sum(v['like_count'] or 0 for v in videos)
        avg_views = total_views // total_videos if total_videos > 0 else 0

        # 从 channels 表获取订阅数，如果没有则从视频表估算
        if channel_row:
            subscriber_count = channel_row['subscriber_count'] or 0
            created_at = channel_row['created_at']
            country = channel_row['country']
            description = channel_row['description']
        else:
            # 从视频表获取最大订阅数
            cursor.execute("""
                SELECT MAX(subscriber_count) FROM competitor_videos WHERE channel_id = ?
            """, (channel_id,))
            sub_row = cursor.fetchone()
            subscriber_count = sub_row[0] if sub_row and sub_row[0] else 0
            created_at = None
            country = None
            description = None

        # 3. 视频列表（Top 20）
        video_list = []
        for v in videos[:20]:
            video_list.append({
                "youtube_id": v['youtube_id'],
                "title": v['title'],
                "view_count": v['view_count'] or 0,
                "like_count": v['like_count'] or 0,
                "duration": v['duration'] or 0,
                "published_at": v['published_at'],
                "keyword_source": v['keyword_source'],
                "thumbnail_url": v['thumbnail_url'],
                "video_url": f"https://www.youtube.com/watch?v={v['youtube_id']}"
            })

        # 4. 话题分布（按 keyword_source 分组）
        topic_stats = {}
        for v in videos:
            topic = v['keyword_source'] or '其他'
            if topic not in topic_stats:
                topic_stats[topic] = {
                    "count": 0,
                    "total_views": 0,
                    "videos": []
                }
            topic_stats[topic]["count"] += 1
            topic_stats[topic]["total_views"] += v['view_count'] or 0
            topic_stats[topic]["videos"].append(v['view_count'] or 0)

        # 计算每个话题的统计
        topic_distribution = []
        for topic, stats in topic_stats.items():
            count = stats["count"]
            total_topic_views = stats["total_views"]
            topic_distribution.append({
                "topic": topic,
                "count": count,
                "percentage": round(count / total_videos * 100, 1) if total_videos > 0 else 0,
                "total_views": total_topic_views,
                "avg_views": total_topic_views // count if count > 0 else 0,
                "contribution": round(total_topic_views / total_views * 100, 1) if total_views > 0 else 0
            })

        # 按视频数排序
        topic_distribution.sort(key=lambda x: x["count"], reverse=True)

        # 标记主力话题和高效话题
        if topic_distribution:
            topic_distribution[0]["badge"] = "主力"
            # 找出效率最高的（平均播放最高）
            best_efficiency = max(topic_distribution, key=lambda x: x["avg_views"])
            if best_efficiency != topic_distribution[0]:
                for t in topic_distribution:
                    if t["topic"] == best_efficiency["topic"]:
                        t["badge"] = "高效"
                        break

        # 5. 时长分布
        duration_stats = {
            "short": {"count": 0, "total_views": 0, "label": "短视频(<5分钟)"},
            "medium": {"count": 0, "total_views": 0, "label": "中等(5-15分钟)"},
            "long": {"count": 0, "total_views": 0, "label": "长视频(>15分钟)"}
        }
        for v in videos:
            d = v['duration'] or 0
            views = v['view_count'] or 0
            if d < 300:
                duration_stats["short"]["count"] += 1
                duration_stats["short"]["total_views"] += views
            elif d < 900:
                duration_stats["medium"]["count"] += 1
                duration_stats["medium"]["total_views"] += views
            else:
                duration_stats["long"]["count"] += 1
                duration_stats["long"]["total_views"] += views

        duration_distribution = []
        for key, stats in duration_stats.items():
            count = stats["count"]
            if count > 0:
                duration_distribution.append({
                    "type": key,
                    "label": stats["label"],
                    "count": count,
                    "percentage": round(count / total_videos * 100, 1) if total_videos > 0 else 0,
                    "avg_views": stats["total_views"] // count
                })

        # 6. 成长轨迹（基于频道创建时间）
        growth_trajectory = []
        if created_at:
            try:
                from datetime import datetime
                created = datetime.strptime(created_at, "%Y-%m-%d")
                days = (datetime.now() - created).days
                years = days // 365

                growth_trajectory.append({
                    "phase": "创建",
                    "date": created_at,
                    "milestone": "频道创建",
                    "data": f"开始于 {created_at}"
                })

                if subscriber_count > 0:
                    subs_per_day = subscriber_count / days if days > 0 else 0
                    growth_trajectory.append({
                        "phase": "当前",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "milestone": f"累计 {subscriber_count:,} 订阅",
                        "data": f"日均涨粉 {subs_per_day:.1f}"
                    })
            except:
                pass

        # 7. 计算播放效率
        efficiency = (avg_views / subscriber_count * 100) if subscriber_count > 0 else 0

        conn.close()

        return {
            "status": "ok",
            "data": {
                "channel_info": {
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "subscriber_count": subscriber_count,
                    "total_views": total_views,
                    "total_videos": total_videos,
                    "avg_views": avg_views,
                    "efficiency": round(efficiency, 1),
                    "country": country,
                    "description": description,
                    "created_at": created_at,
                    "channel_url": f"https://www.youtube.com/channel/{channel_id}"
                },
                "videos": video_list,
                "topic_distribution": topic_distribution,
                "duration_distribution": duration_distribution,
                "growth_trajectory": growth_trajectory,
                # 生成学习建议
                "learning_insights": _generate_channel_learning_insights(
                    channel_name, subscriber_count, avg_views, efficiency,
                    topic_distribution, duration_distribution, video_list
                )
            }
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def _generate_channel_learning_insights(
    channel_name: str,
    subscriber_count: int,
    avg_views: int,
    efficiency: float,
    topic_distribution: list,
    duration_distribution: list,
    videos: list
) -> dict:
    """
    根据频道数据生成学习洞察
    """
    # 为什么值得研究
    why_study = []
    if subscriber_count > 100000:
        why_study.append(f"拥有 {subscriber_count:,} 订阅，是该领域的头部玩家")
    elif subscriber_count > 10000:
        why_study.append(f"拥有 {subscriber_count:,} 订阅，正在快速增长")

    if efficiency > 20:
        why_study.append(f"播放效率达 {efficiency:.1f}%（高于行业平均），内容吸引力强")
    elif efficiency > 10:
        why_study.append(f"播放效率 {efficiency:.1f}%，用户粘性良好")

    if avg_views > 100000:
        why_study.append(f"均播 {avg_views:,}，内容有较强的传播力")

    if not why_study:
        why_study.append("研究其内容策略和增长路径，可以为新人提供参考经验")

    # 成功模式
    success_patterns = []

    # 分析话题策略
    if topic_distribution:
        main_topic = topic_distribution[0]
        if main_topic["percentage"] > 50:
            success_patterns.append({
                "title": "垂直深耕",
                "desc": f"主力话题「{main_topic['topic']}」占比 {main_topic['percentage']}%，专注单一领域",
                "evidence": f"{main_topic['count']} 个视频聚焦该方向"
            })
        else:
            success_patterns.append({
                "title": "多元布局",
                "desc": "内容覆盖多个话题，降低单一话题风险",
                "evidence": f"涉及 {len(topic_distribution)} 个不同话题"
            })

    # 分析时长策略
    if duration_distribution:
        main_duration = max(duration_distribution, key=lambda x: x["count"])
        success_patterns.append({
            "title": f"{main_duration['label']}策略",
            "desc": f"主要发布{main_duration['label']}，占比 {main_duration['percentage']}%",
            "evidence": f"这类视频均播 {main_duration['avg_views']:,}"
        })

    # 分析爆款规律
    if videos and len(videos) >= 3:
        top_video = videos[0]
        avg_top3 = sum(v['view_count'] for v in videos[:3]) / 3
        success_patterns.append({
            "title": "爆款能力",
            "desc": f"最高播放 {top_video['view_count']:,}，前3视频均播 {int(avg_top3):,}",
            "evidence": f"爆款标题参考：「{top_video['title'][:30]}...」"
        })

    # 学习路径
    learning_path = [
        f"研究「{topic_distribution[0]['topic'] if topic_distribution else '主力话题'}」方向的选题规律",
        "学习该频道的标题写法和封面风格",
        f"保持稳定更新，参考其{main_duration['label'] if duration_distribution else '中等时长'}策略" if duration_distribution else "保持稳定更新频率",
        "分析高播放视频的内容结构",
        "找到差异化角度，避免完全模仿"
    ]

    # 行动建议
    actions = {
        "do": [
            f"从「{topic_distribution[0]['topic'] if topic_distribution else '验证过的话题'}」切入",
            "保持稳定更新频率",
            "学习标题和封面风格"
        ],
        "avoid": [
            "不要一开始就分散精力",
            "不要完全复制，要有差异化"
        ]
    }

    return {
        "why_study": why_study,
        "success_patterns": success_patterns,
        "learning_path": learning_path,
        "actions": actions
    }


# ============================================================
# 网络图可视化 API
# ============================================================

@app.get("/api/network-graph")
async def get_network_graph(graph_type: str = "topic", max_nodes: int = 50):
    """
    获取网络图可视化数据（节点 + 边）

    参数:
    - graph_type: 'topic' (话题共现网络) 或 'channel' (频道-频道网络)
    - max_nodes: 最大节点数量 (10-100)

    返回:
    - nodes: 节点列表，包含 id, label, betweenness, degree, size, color_intensity 等
    - edges: 边列表，包含 from, to, weight, width
    - stats: 统计信息

    用于前端 vis.js 网络图可视化，支持三种着色模式：
    1. 中介中心性着色 - 桥梁节点高亮
    2. 程度中心性着色 - 枢纽节点高亮
    3. 套利机会着色 - 高中介+低热度节点高亮
    """
    try:
        from src.research.network_centrality import get_network_graph_data

        db_path = Path(__file__).parent / "data" / "youtube_pipeline.db"

        if not db_exists(str(db_path)):
            return {"status": "error", "message": "数据库不存在"}

        # 限制节点数量范围
        max_nodes = max(10, min(100, max_nodes))

        data = get_network_graph_data(str(db_path), graph_type=graph_type, max_nodes=max_nodes)

        return data

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("YouTube Content Assistant API Server")
    print("=" * 50)
    print("启动服务器: http://localhost:8000")
    print("WebSocket: ws://localhost:8000/ws/{task_id}")
    print("API 文档: http://localhost:8000/docs")
    print("=" * 50)

    import os
    # 开发时设置 DEV=1 启用热重载，生产环境默认关闭
    dev_mode = os.environ.get("DEV", "0") == "1"

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=dev_mode,  # 默认关闭热重载，避免中断 WebSocket 连接
        log_level="info"
    )
