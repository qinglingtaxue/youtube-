#!/usr/bin/env python3
"""
YouTube 内容助手 - API 服务 (简化版)
直接调用 yt-dlp 命令行，不依赖有问题的模块
"""

import asyncio
import json
import os
import subprocess
import sys
import ssl
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from contextlib import asynccontextmanager
from collections import Counter

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# 导入数据库模块
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from utils.database import get_database


# ============ Pydantic 模型 ============

class ResearchRequest(BaseModel):
    """研究请求参数"""
    topic: str = Field(..., description="研究主题/关键词")
    mode: str = Field(default="standard", description="分析模式: quick/standard/deep")
    max_results: int = Field(default=500, description="最大采集数量")

    # 筛选条件
    views_min: Optional[int] = Field(default=None, description="最小播放量")
    views_max: Optional[int] = Field(default=None, description="最大播放量")
    duration_filter: Optional[List[str]] = Field(default=None, description="时长筛选: short/medium/long")
    time_range: Optional[str] = Field(default=None, description="发布时间: 24h/7d/30d/90d/1y")
    regions: Optional[List[str]] = Field(default=None, description="目标地区")
    subscribers_filter: Optional[List[str]] = Field(default=None, description="频道粉丝数: small/medium/large/huge")
    ai_filter: Optional[str] = Field(default=None, description="AI视频筛选: ai/human")
    sort_by: str = Field(default="views", description="排序方式")


class MonitorTaskCreate(BaseModel):
    """创建监控任务"""
    keyword: str = Field(..., description="监控关键词")
    description: Optional[str] = Field(default=None, description="任务描述")
    frequency: str = Field(default="daily", description="采集频率: hourly/daily/weekly")
    max_results: int = Field(default=500, description="每次采集最大数量")


class MonitorTaskUpdate(BaseModel):
    """更新监控任务"""
    description: Optional[str] = None
    frequency: Optional[str] = None
    max_results: Optional[int] = None
    is_active: Optional[bool] = None


# ============ 任务结果缓存 ============

class TaskResultCache:
    """任务结果缓存 - 防止 WebSocket 断开后丢失结果"""

    def __init__(self, max_age_seconds: int = 3600):
        """
        Args:
            max_age_seconds: 结果最大保存时间（默认1小时）
        """
        self.results: Dict[str, Dict] = {}
        self.max_age = timedelta(seconds=max_age_seconds)

    def save(self, task_id: str, result: Dict, status: str = "complete"):
        """保存任务结果"""
        self.results[task_id] = {
            "result": result,
            "status": status,
            "timestamp": datetime.now(),
            "progress": 100 if status == "complete" else 0,
            "message": "任务完成" if status == "complete" else ""
        }
        print(f"💾 任务结果已缓存: {task_id} (状态: {status})")

    def update_progress(self, task_id: str, progress: int, message: str):
        """更新任务进度"""
        if task_id not in self.results:
            self.results[task_id] = {
                "result": None,
                "status": "running",
                "timestamp": datetime.now(),
                "progress": progress,
                "message": message
            }
        else:
            self.results[task_id]["progress"] = progress
            self.results[task_id]["message"] = message
            self.results[task_id]["timestamp"] = datetime.now()

    def get(self, task_id: str) -> Optional[Dict]:
        """获取任务结果"""
        if task_id not in self.results:
            return None

        entry = self.results[task_id]
        # 检查是否过期
        if datetime.now() - entry["timestamp"] > self.max_age:
            del self.results[task_id]
            return None

        return entry

    def cleanup(self):
        """清理过期结果"""
        now = datetime.now()
        expired = [
            task_id for task_id, entry in self.results.items()
            if now - entry["timestamp"] > self.max_age
        ]
        for task_id in expired:
            del self.results[task_id]
        if expired:
            print(f"🧹 已清理 {len(expired)} 个过期任务结果")

# 全局任务缓存
task_cache = TaskResultCache()


# ============ AI 视频检测 ============

AI_VIDEO_KEYWORDS = [
    'sora', 'runway', 'pika', 'heygen', 'synthesia', 'd-id', 'midjourney',
    'stable diffusion', 'kling', 'luma', 'gen-2', 'gen-3', 'vidu', 'cogvideo',
    'ai生成', 'ai视频', 'ai制作', 'ai创作', 'ai配音', 'ai换脸', 'ai数字人',
    '数字人', '虚拟人', '人工智能生成', 'aigc',
    'ai generated', 'ai video', 'ai-generated', 'text to video', 'ai avatar'
]

def detect_ai_video(title: str, description: str = "", tags: List[str] = None) -> tuple:
    """检测是否为AI视频"""
    text = f"{title or ''} {description or ''} {' '.join(tags or [])}".lower()
    for kw in AI_VIDEO_KEYWORDS:
        if kw.lower() in text:
            return True, kw
    return False, None


def get_duration_category(seconds: int) -> str:
    """获取时长分类"""
    if seconds < 300:
        return "short"
    elif seconds < 1200:
        return "medium"
    else:
        return "long"


# ============ yt-dlp 直接调用 ============

def search_videos_ytdlp(keyword: str, max_results: int = 50, time_range: str = None) -> List[Dict]:
    """使用 yt-dlp 搜索视频

    time_range: YouTube 时间过滤
      - 24h: 最近24小时
      - 7d: 最近7天
      - 30d: 最近30天
      - 1y: 最近1年
    """
    try:
        # 构建搜索 URL
        # YouTube 搜索时间过滤需要使用特定的 URL 参数
        search_url = f'ytsearch{max_results}:{keyword}'

        # 如果指定时间范围，使用 YouTube 搜索 URL 格式
        if time_range:
            # YouTube sp 参数编码 (base64):
            # 最近1小时: EgIIAQ, 今天: EgIIAg, 本周: EgIIAw, 本月: EgIIBA, 今年: EgIIBQ
            # 注意: YouTube 没有原生的"3个月"过滤，90d 使用本月过滤 + 后过滤实现
            sp_codes = {
                '24h': 'EgIIAg',   # 今天（24小时内）
                '7d': 'EgIIAw',    # 本周（7天内）
                '30d': 'EgIIBA',   # 本月（30天内）
                '90d': 'EgIIBA',   # 3个月（使用本月过滤，后续代码会补充过滤）
                '1y': 'EgIIBQ',    # 今年
            }
            sp = sp_codes.get(time_range)
            if sp:
                # 使用 YouTube 搜索 URL 而不是 ytsearch
                from urllib.parse import quote
                encoded_keyword = quote(keyword)
                search_url = f'https://www.youtube.com/results?search_query={encoded_keyword}&sp={sp}'
                print(f"使用时间过滤搜索: {time_range} -> sp={sp}")

        cmd = [
            'yt-dlp',
            '--dump-json',
            '--flat-playlist',
            '--no-warnings',
            '--playlist-end', str(max_results),
            search_url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 增加超时时间
        )

        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append(data)
                except json.JSONDecodeError:
                    continue

        print(f"搜索完成: 找到 {len(videos)} 个视频")
        return videos
    except subprocess.TimeoutExpired:
        print("yt-dlp 搜索超时")
        return []
    except FileNotFoundError:
        print("yt-dlp 未安装")
        return []
    except Exception as e:
        print(f"搜索错误: {e}")
        return []


def generate_search_variations(keyword: str) -> List[str]:
    """生成关键词变体，用于扩大搜索范围（基础版本）

    策略：
    1. 原始关键词
    2. 添加年份（2024, 2025）
    3. 添加常用修饰词（教程, 入门, 进阶, 实战, 技巧）
    4. 添加语言/地区变体
    """
    variations = [keyword]

    # 年份变体
    current_year = datetime.now().year
    variations.extend([
        f"{keyword} {current_year}",
        f"{keyword} {current_year - 1}",
    ])

    # 内容类型变体
    content_modifiers = ['教程', '入门', '实战', '技巧', '完整', '最新']
    for mod in content_modifiers:
        if mod not in keyword:
            variations.append(f"{keyword} {mod}")

    # 英文关键词添加英文修饰词
    if any(c.isascii() and c.isalpha() for c in keyword):
        eng_modifiers = ['tutorial', 'guide', 'beginners', 'advanced', 'tips']
        for mod in eng_modifiers:
            if mod not in keyword.lower():
                variations.append(f"{keyword} {mod}")

    return variations[:10]  # 最多返回10个变体


# ============ 高级关键词采集 ============

def get_search_suggestions(query: str, max_suggestions: int = 10, language: str = 'zh') -> List[str]:
    """获取 YouTube 搜索建议（长尾词）

    使用 YouTube 的搜索自动补全 API 获取用户真实搜索的关键词

    Args:
        query: 基础搜索词
        max_suggestions: 最大建议数
        language: 语言代码

    Returns:
        搜索建议列表
    """
    print(f"🔍 获取搜索建议: {query}")

    # YouTube 搜索建议 API
    base_url = "https://suggestqueries-clients6.youtube.com/complete/search"
    params = {
        'client': 'youtube',
        'hl': language,
        'gl': 'US',
        'gs_ri': 'youtube',
        'ds': 'yt',
        'q': query
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 创建 SSL 上下文（处理证书问题）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            # 响应是 JSONP 格式: window.google.ac.h(...)
            content = response.read().decode('utf-8')

            # 提取 JSON 部分
            start = content.find('(')
            end = content.rfind(')')
            if start != -1 and end != -1:
                json_str = content[start + 1:end]
                data = json.loads(json_str)

                # 解析建议列表
                suggestions = []
                if len(data) > 1 and isinstance(data[1], list):
                    for item in data[1]:
                        if isinstance(item, list) and len(item) > 0:
                            suggestion = item[0]
                            if suggestion != query:
                                suggestions.append(suggestion)

                print(f"   ✓ 获取到 {len(suggestions)} 个搜索建议")
                return suggestions[:max_suggestions]

    except Exception as e:
        print(f"   ⚠ 获取搜索建议失败: {e}")

    return []


def extract_tags_from_channel(channel_id: str, max_videos: int = 10, top_n: int = 15) -> List[str]:
    """从频道视频中提取高频标签

    分析竞品频道的视频标签，找出他们常用的关键词

    Args:
        channel_id: YouTube 频道 ID
        max_videos: 分析的视频数量
        top_n: 返回 top N 个高频标签

    Returns:
        高频标签列表（按频率排序）
    """
    print(f"🏷️  从频道 {channel_id} 提取标签")

    try:
        # 1. 获取频道视频列表
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--dump-single-json',
            '--playlist-end', str(max_videos),
            '--no-warnings',
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"   ⚠ 获取频道视频列表失败")
            return []

        data = json.loads(result.stdout)
        entries = data.get('entries', [])

        if not entries:
            print(f"   ⚠ 频道没有视频")
            return []

        # 2. 收集所有标签
        all_tags: List[str] = []

        for i, video in enumerate(entries[:max_videos]):
            video_id = video.get('id')
            if not video_id:
                continue

            try:
                # 获取视频详情以获取标签
                detail_cmd = [
                    'yt-dlp',
                    '--dump-json',
                    '--no-download',
                    '--no-warnings',
                    f'https://www.youtube.com/watch?v={video_id}'
                ]

                detail_result = subprocess.run(
                    detail_cmd,
                    capture_output=True,
                    text=True,
                    timeout=15
                )

                if detail_result.returncode == 0:
                    detail = json.loads(detail_result.stdout)
                    tags = detail.get('tags', [])
                    if tags:
                        all_tags.extend(tags)

            except Exception as e:
                continue

        # 3. 统计标签频率
        tag_counts = Counter(all_tags)

        # 返回高频标签
        top_tags = [tag for tag, _ in tag_counts.most_common(top_n)]

        print(f"   ✓ 从 {len(entries)} 个视频中提取了 {len(top_tags)} 个高频标签")
        return top_tags

    except Exception as e:
        print(f"   ⚠ 提取频道标签失败: {e}")
        return []


async def get_smart_search_keywords(
    keyword: str,
    competitor_channels: List[str] = None,
    max_keywords: int = 15
) -> List[str]:
    """智能获取搜索关键词

    综合多个数据源获取真实的关键词：
    1. 原始关键词
    2. YouTube 搜索建议（长尾词）
    3. 竞品频道视频标签
    4. 基础变体（年份、修饰词）

    Args:
        keyword: 主关键词
        competitor_channels: 竞品频道 ID 列表（可选）
        max_keywords: 最大关键词数

    Returns:
        综合关键词列表（已去重）
    """
    print(f"\n🧠 智能关键词采集: {keyword}")

    all_keywords: Set[str] = set()
    all_keywords.add(keyword)

    loop = asyncio.get_event_loop()

    # 1. 获取 YouTube 搜索建议
    suggestions = await loop.run_in_executor(
        None,
        lambda: get_search_suggestions(keyword, max_suggestions=10)
    )
    all_keywords.update(suggestions)
    print(f"   搜索建议: +{len(suggestions)} 个关键词")

    # 2. 从竞品频道提取标签（如果提供了频道列表）
    if competitor_channels:
        for channel_id in competitor_channels[:3]:  # 最多分析3个频道
            tags = await loop.run_in_executor(
                None,
                lambda cid=channel_id: extract_tags_from_channel(cid, max_videos=5, top_n=10)
            )
            # 只保留与主题相关的标签
            relevant_tags = [t for t in tags if is_tag_relevant(t, keyword)]
            all_keywords.update(relevant_tags)
            print(f"   频道标签 {channel_id[:8]}...: +{len(relevant_tags)} 个相关标签")
            await asyncio.sleep(0.5)  # 避免限流

    # 3. 补充基础变体（确保有足够的关键词）
    if len(all_keywords) < max_keywords:
        basic_variations = generate_search_variations(keyword)
        for v in basic_variations:
            if len(all_keywords) >= max_keywords:
                break
            all_keywords.add(v)

    keyword_list = list(all_keywords)
    print(f"   ✓ 共收集到 {len(keyword_list)} 个关键词")

    return keyword_list[:max_keywords]


def is_tag_relevant(tag: str, keyword: str) -> bool:
    """检查标签是否与关键词相关

    简单的相关性检查，过滤掉无关标签
    """
    tag_lower = tag.lower()
    keyword_lower = keyword.lower()

    # 完全包含
    if keyword_lower in tag_lower or tag_lower in keyword_lower:
        return True

    # 关键词的任何词出现在标签中
    keyword_words = keyword_lower.split()
    for word in keyword_words:
        if len(word) > 2 and word in tag_lower:
            return True

    # 标签长度过长可能是无关的
    if len(tag) > 50:
        return False

    # 标签是常见的编程/技术相关词汇
    tech_keywords = ['python', 'java', 'javascript', 'coding', 'programming', 'tutorial',
                     '教程', '编程', '开发', '学习', 'learn', 'course', '课程']
    for tk in tech_keywords:
        if tk in tag_lower and tk in keyword_lower:
            return True

    return False


# ===== 错误分类常量 =====
class ChannelErrorType:
    """频道获取错误类型"""
    SUCCESS = "success"                    # 成功
    NETWORK_TIMEOUT = "network_timeout"    # 网络超时（可重试）
    SSL_ERROR = "ssl_error"                # SSL错误（可重试）
    CONNECTION_ERROR = "connection_error"  # 连接错误（可重试）
    CHANNEL_NOT_FOUND = "channel_not_found"  # 频道不存在（永久性）
    CHANNEL_PRIVATE = "channel_private"      # 频道私有（永久性）
    RATE_LIMITED = "rate_limited"            # 被限流（可重试，需等待）
    UNKNOWN = "unknown"                      # 未知错误（可重试）

# 可重试的错误类型
RETRIABLE_ERRORS = {
    ChannelErrorType.NETWORK_TIMEOUT,
    ChannelErrorType.SSL_ERROR,
    ChannelErrorType.CONNECTION_ERROR,
    ChannelErrorType.RATE_LIMITED,
    ChannelErrorType.UNKNOWN,
}

# 永久性错误（不应重试）
PERMANENT_ERRORS = {
    ChannelErrorType.CHANNEL_NOT_FOUND,
    ChannelErrorType.CHANNEL_PRIVATE,
}


def classify_error(stderr: str) -> str:
    """根据错误信息分类错误类型"""
    if not stderr:
        return ChannelErrorType.UNKNOWN

    stderr_lower = stderr.lower()

    # 永久性错误
    if "does not exist" in stderr_lower or "not exist" in stderr_lower:
        return ChannelErrorType.CHANNEL_NOT_FOUND
    if "private" in stderr_lower:
        return ChannelErrorType.CHANNEL_PRIVATE
    if "this channel has no" in stderr_lower:
        return ChannelErrorType.CHANNEL_NOT_FOUND

    # 可重试错误
    if "ssl" in stderr_lower or "eof occurred" in stderr_lower:
        return ChannelErrorType.SSL_ERROR
    if "timed out" in stderr_lower or "timeout" in stderr_lower:
        return ChannelErrorType.NETWORK_TIMEOUT
    if "connection" in stderr_lower or "network" in stderr_lower:
        return ChannelErrorType.CONNECTION_ERROR
    if "rate" in stderr_lower or "429" in stderr_lower or "too many" in stderr_lower:
        return ChannelErrorType.RATE_LIMITED

    return ChannelErrorType.UNKNOWN


def get_channel_real_stats_with_error(channel_id: str) -> Dict:
    """获取单个频道的真实统计数据（带详细错误信息）

    返回: {
        'success': bool,
        'error_type': str,
        'error_message': str,
        'data': {...} 或 None
    }
    """
    result = {
        'success': False,
        'error_type': None,
        'error_message': None,
        'data': None
    }

    try:
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--dump-single-json',
            '--no-warnings',
            '--socket-timeout', '30',
            '--retries', '2',
            url
        ]

        proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if proc_result.returncode != 0:
            error_type = classify_error(proc_result.stderr)
            result['error_type'] = error_type
            result['error_message'] = proc_result.stderr[:200] if proc_result.stderr else "Unknown error"
            return result

        data = json.loads(proc_result.stdout)
        entries = data.get('entries', [])

        # 计算频道总播放量
        total_views = sum(entry.get('view_count') or 0 for entry in entries)
        video_count = len(entries)
        avg_views = total_views // video_count if video_count > 0 else 0

        result['success'] = True
        result['error_type'] = ChannelErrorType.SUCCESS
        result['data'] = {
            'subscriber_count': data.get('channel_follower_count') or 0,
            'real_video_count': video_count,
            'total_channel_views': total_views,
            'avg_channel_views': avg_views,
            'channel_name': data.get('channel') or data.get('uploader') or ''
        }
        return result

    except subprocess.TimeoutExpired:
        result['error_type'] = ChannelErrorType.NETWORK_TIMEOUT
        result['error_message'] = "Request timed out after 60 seconds"
        return result
    except json.JSONDecodeError as e:
        result['error_type'] = ChannelErrorType.UNKNOWN
        result['error_message'] = f"JSON parse error: {e}"
        return result
    except Exception as e:
        result['error_type'] = ChannelErrorType.UNKNOWN
        result['error_message'] = f"{type(e).__name__}: {e}"
        return result


def get_channel_real_stats(channel_id: str) -> Optional[Dict]:
    """获取单个频道的真实统计数据（兼容旧接口）"""
    result = get_channel_real_stats_with_error(channel_id)
    return result['data'] if result['success'] else None


async def fetch_channels_real_stats(
    channel_ids: List[str],
    max_retries: int = 2,
    progress_callback=None
) -> Dict[str, Dict]:
    """获取多个频道的真实统计数据（带查漏补缺机制）

    Args:
        channel_ids: 频道ID列表
        max_retries: 最大重试轮数
        progress_callback: 进度回调函数 async (current, total, stats) -> None
            stats 包含: success_count, fail_count, avg_time_per_channel, estimated_remaining_seconds, network_speed

    Returns:
        {channel_id: {subscriber_count, real_video_count, ...}}
    """
    import time

    results = {}
    total = len(channel_ids)

    # 跟踪每个频道的状态
    channel_status = {cid: {
        'success': False,
        'error_type': None,
        'error_message': None,
        'retry_count': 0,
        'skip': False  # 永久性错误标记为跳过
    } for cid in channel_ids}

    # 统计数据
    fetch_times = []  # 记录每次请求的耗时
    success_count = 0
    fail_count = 0
    processed_count = 0

    print(f"   开始获取 {total} 个频道数据（带查漏补缺机制）", flush=True)

    # ===== 第一轮采集 =====
    pending_ids = list(channel_ids)
    round_num = 1

    while pending_ids and round_num <= max_retries + 1:
        if round_num > 1:
            print(f"\n   📦 第 {round_num} 轮补采: {len(pending_ids)} 个频道", flush=True)
            await asyncio.sleep(2)  # 重试前等待

        next_pending = []

        for i, cid in enumerate(pending_ids):
            status = channel_status[cid]

            # 跳过已标记的永久性失败
            if status['skip']:
                continue

            print(f"   [{i+1}/{len(pending_ids)}] 获取频道 {cid[:15]}...", flush=True)

            # 记录请求开始时间
            start_time = time.time()

            fetch_result = get_channel_real_stats_with_error(cid)
            status['retry_count'] += 1

            # 记录请求耗时
            elapsed = time.time() - start_time
            fetch_times.append(elapsed)
            processed_count += 1

            if fetch_result['success']:
                # 成功
                results[cid] = fetch_result['data']
                status['success'] = True
                status['error_type'] = ChannelErrorType.SUCCESS
                success_count += 1
                print(f"       ✓ {fetch_result['data']['channel_name']}: 订阅={fetch_result['data']['subscriber_count']:,}", flush=True)
            else:
                # 失败 - 分类处理
                error_type = fetch_result['error_type']
                status['error_type'] = error_type
                status['error_message'] = fetch_result['error_message']
                fail_count += 1

                if error_type in PERMANENT_ERRORS:
                    # 永久性错误 - 标记跳过
                    status['skip'] = True
                    print(f"       ✗ 永久失败({error_type}): {fetch_result['error_message'][:80]}", flush=True)
                elif error_type in RETRIABLE_ERRORS:
                    # 可重试错误 - 加入下一轮
                    if round_num <= max_retries:
                        next_pending.append(cid)
                        print(f"       ⚠ 暂时失败({error_type}): 将在下一轮重试", flush=True)
                    else:
                        print(f"       ✗ 网络失败({error_type}): 已达最大重试次数", flush=True)

            # 发送进度回调
            if progress_callback and round_num == 1:  # 只在第一轮发送详细进度
                # 计算平均耗时和预估剩余时间
                avg_time = sum(fetch_times) / len(fetch_times) if fetch_times else 0.5
                remaining = total - processed_count
                estimated_remaining = remaining * (avg_time + 0.5)  # 加上间隔时间

                # 计算网络速度状态
                recent_times = fetch_times[-5:] if len(fetch_times) >= 5 else fetch_times
                recent_avg = sum(recent_times) / len(recent_times) if recent_times else 0.5

                if recent_avg < 1.0:
                    network_speed = 'fast'
                elif recent_avg < 3.0:
                    network_speed = 'normal'
                else:
                    network_speed = 'slow'

                await progress_callback(processed_count, total, {
                    'success_count': success_count,
                    'fail_count': fail_count,
                    'avg_time_per_channel': round(avg_time, 2),
                    'estimated_remaining_seconds': round(estimated_remaining),
                    'network_speed': network_speed,
                    'last_fetch_time': round(elapsed, 2),
                    'current_channel': fetch_result['data'].get('channel_name', cid[:15]) if fetch_result['success'] else cid[:15]
                })

            # 请求间隔
            if i < len(pending_ids) - 1:
                await asyncio.sleep(0.5)

        pending_ids = next_pending
        round_num += 1

    # ===== 统计结果 =====
    success_count = sum(1 for s in channel_status.values() if s['success'])
    permanent_fail = sum(1 for s in channel_status.values() if s['skip'])
    network_fail = sum(1 for s in channel_status.values()
                       if not s['success'] and not s['skip'])

    print(f"\n   📊 频道数据获取完成:", flush=True)
    print(f"      ✓ 成功: {success_count}/{total}", flush=True)
    print(f"      ✗ 永久失败(已跳过): {permanent_fail}", flush=True)
    print(f"      ⚠ 网络失败(可重试): {network_fail}", flush=True)

    # 返回结果时附加状态信息
    for cid in channel_ids:
        if cid in results:
            results[cid]['_fetch_status'] = 'success'
        else:
            status = channel_status[cid]
            # 为失败的频道也创建一个占位记录
            results[cid] = {
                'subscriber_count': 0,
                'real_video_count': 0,
                'total_channel_views': 0,
                'avg_channel_views': 0,
                'channel_name': '',
                '_fetch_status': 'permanent_failure' if status['skip'] else 'network_failure',
                '_error_type': status['error_type'],
                '_error_message': status['error_message'],
                '_retriable': not status['skip']
            }

    return results


async def search_videos_multi(
    keyword: str,
    target_count: int,
    time_range: str = None,
    progress_callback=None,
    use_smart_keywords: bool = True
) -> List[Dict]:
    """多任务搜索，通过多个搜索查询获取更多视频

    Args:
        keyword: 主关键词
        target_count: 目标视频数量
        time_range: 时间过滤
        progress_callback: 进度回调函数
        use_smart_keywords: 是否使用智能关键词采集

    Returns:
        去重后的视频列表
    """
    # 计算需要的搜索任务数
    # 每次搜索最多返回约 50-100 个有效结果
    per_search_max = 100
    num_searches = min((target_count // per_search_max) + 1, 10)  # 最多10次搜索

    # 使用智能关键词采集或基础变体
    if use_smart_keywords:
        if progress_callback:
            await progress_callback("正在获取 YouTube 搜索建议...", 5)
        search_queries = await get_smart_search_keywords(keyword, max_keywords=num_searches)
    else:
        search_queries = generate_search_variations(keyword)[:num_searches]

    print(f"\n🔍 多任务搜索策略:")
    print(f"   目标数量: {target_count}")
    print(f"   搜索任务数: {len(search_queries)}")
    print(f"   智能关键词: {'是' if use_smart_keywords else '否'}")
    print(f"   搜索关键词: {search_queries}")

    all_videos = []
    seen_ids = set()

    loop = asyncio.get_event_loop()

    for i, query in enumerate(search_queries):
        if progress_callback:
            await progress_callback(
                f"搜索任务 {i+1}/{len(search_queries)}: \"{query}\"",
                int(10 + (i / len(search_queries)) * 30)
            )

        # 在线程池中运行搜索
        results = await loop.run_in_executor(
            None,
            lambda q=query: search_videos_ytdlp(q, per_search_max, time_range)
        )

        # 去重合并
        new_count = 0
        for video in results:
            vid = video.get('id', '')
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                all_videos.append(video)
                new_count += 1

        print(f"   任务 {i+1}: 找到 {len(results)} 个，新增 {new_count} 个（去重后共 {len(all_videos)} 个）")

        # 如果已达到目标数量，提前结束
        if len(all_videos) >= target_count:
            print(f"   ✓ 已达到目标数量 {target_count}，停止搜索")
            break

        # 添加小延迟避免被限流
        await asyncio.sleep(1)

    print(f"\n📊 多任务搜索完成: 共 {len(all_videos)} 个唯一视频")
    return all_videos


def get_video_details(video_id: str) -> Optional[Dict]:
    """获取单个视频详情"""
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            f'https://www.youtube.com/watch?v={video_id}'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.stdout:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"获取详情错误: {e}")
        return None


async def fetch_videos_details_concurrent(
    video_ids: List[str],
    max_concurrent: int = 10,
    progress_callback=None
) -> Dict[str, Dict]:
    """并发获取多个视频的详细信息

    Args:
        video_ids: 视频ID列表
        max_concurrent: 最大并发数（默认10）
        progress_callback: 进度回调 async def callback(current, total, message)

    Returns:
        {video_id: video_details} 字典
    """
    results = {}
    loop = asyncio.get_event_loop()
    total = len(video_ids)

    print(f"\n🎬 并发获取 {total} 个视频详情 (并发数: {max_concurrent})")

    # 分批处理
    for i in range(0, total, max_concurrent):
        batch = video_ids[i:i + max_concurrent]
        batch_num = i // max_concurrent + 1
        total_batches = (total + max_concurrent - 1) // max_concurrent

        # 并发执行
        tasks = [
            loop.run_in_executor(None, get_video_details, vid)
            for vid in batch
        ]

        batch_results = await asyncio.gather(*tasks)

        # 收集结果
        success_count = 0
        for vid, details in zip(batch, batch_results):
            if details:
                results[vid] = details
                success_count += 1

        # 进度回调
        completed = min(i + max_concurrent, total)
        if progress_callback:
            await progress_callback(
                completed,
                total,
                f"已获取 {completed}/{total} 个视频详情 (批次 {batch_num}/{total_batches})"
            )

        print(f"   批次 {batch_num}/{total_batches}: {success_count}/{len(batch)} 成功")

        # 批次间短暂延迟，避免被限流
        if i + max_concurrent < total:
            await asyncio.sleep(0.3)

    print(f"   ✓ 完成: 成功获取 {len(results)}/{total} 个视频详情")
    return results


# ============ WebSocket 连接管理 ============

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_progress(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                print(f"WebSocket 发送失败 ({client_id}): {e}")
                self.disconnect(client_id)

    def is_connected(self, client_id: str) -> bool:
        """检查客户端是否仍然连接"""
        return client_id in self.active_connections


manager = ConnectionManager()


# ============ FastAPI 应用 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 YouTube 内容助手 API 启动中...")
    yield
    print("👋 API 服务关闭")


app = FastAPI(
    title="YouTube 内容助手 API",
    description="YouTube 视频研究与分析 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
web_dir = Path(__file__).parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# 2026-1-17 目录的静态文件服务
demo_dir = Path(__file__).parent / "2026-1-17"
if demo_dir.exists():
    app.mount("/2026-1-17", StaticFiles(directory=str(demo_dir), html=True), name="demo")


@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    index_path = web_dir / "demo.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "YouTube 内容助手 API", "docs": "/docs"}


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/suggestions")
async def get_suggestions(q: str = Query(..., description="搜索关键词")):
    """获取 YouTube 搜索建议

    返回 YouTube 自动补全的搜索建议（长尾关键词）
    """
    loop = asyncio.get_event_loop()
    suggestions = await loop.run_in_executor(
        None,
        lambda: get_search_suggestions(q, max_suggestions=10)
    )
    return {
        "query": q,
        "suggestions": suggestions,
        "count": len(suggestions)
    }


@app.get("/api/channel/{channel_id}/tags")
async def get_channel_tags(
    channel_id: str,
    max_videos: int = Query(default=10, le=20, description="分析的视频数量")
):
    """从频道视频中提取高频标签

    分析频道最新视频的标签，返回高频关键词
    """
    loop = asyncio.get_event_loop()
    tags = await loop.run_in_executor(
        None,
        lambda: extract_tags_from_channel(channel_id, max_videos=max_videos, top_n=20)
    )
    return {
        "channel_id": channel_id,
        "tags": tags,
        "count": len(tags)
    }


@app.get("/api/channel/{channel_id}")
async def get_channel_info(channel_id: str):
    """获取频道真实统计数据

    返回：
    - channel_name: 频道名称
    - subscriber_count: 订阅数
    - video_count: 视频总数
    - description: 频道描述
    """
    try:
        url = f"https://www.youtube.com/channel/{channel_id}/videos"

        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--dump-single-json',
            '--no-warnings',
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"频道不存在或无法访问: {channel_id}")

        data = json.loads(result.stdout)

        # 提取频道信息
        entries = data.get('entries', [])

        return {
            "channel_id": channel_id,
            "channel_name": data.get('channel') or data.get('uploader') or '未知',
            "subscriber_count": data.get('channel_follower_count') or 0,
            "video_count": len(entries),
            "description": data.get('description') or '',
            "channel_url": f"https://www.youtube.com/channel/{channel_id}"
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="请求超时")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="解析频道数据失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/task/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务状态和结果（用于断线重连后恢复）

    返回:
        - status: "running" | "complete" | "error" | "not_found"
        - progress: 进度百分比
        - message: 当前状态消息
        - result: 任务结果（仅当 status 为 complete 时）
    """
    cached = task_cache.get(task_id)

    if cached is None:
        return {
            "status": "not_found",
            "message": "任务不存在或已过期"
        }

    return {
        "status": cached["status"],
        "progress": cached["progress"],
        "message": cached["message"],
        "result": cached["result"] if cached["status"] == "complete" else None
    }


@app.post("/api/channels/batch")
async def get_channels_batch(channel_ids: List[str]):
    """批量获取多个频道的真实统计数据

    最多支持 10 个频道同时查询
    """
    if len(channel_ids) > 10:
        raise HTTPException(status_code=400, detail="最多支持 10 个频道同时查询")

    results = {}

    async def fetch_channel(ch_id: str):
        try:
            url = f"https://www.youtube.com/channel/{ch_id}/videos"
            cmd = [
                'yt-dlp',
                '--flat-playlist',
                '--dump-single-json',
                '--no-warnings',
                url
            ]

            # 使用 asyncio 包装同步调用
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                entries = data.get('entries', [])
                return {
                    "channel_id": ch_id,
                    "channel_name": data.get('channel') or data.get('uploader') or '未知',
                    "subscriber_count": data.get('channel_follower_count') or 0,
                    "video_count": len(entries),
                    "success": True
                }
        except Exception as e:
            pass

        return {"channel_id": ch_id, "success": False, "error": "获取失败"}

    # 并发获取所有频道
    tasks = [fetch_channel(ch_id) for ch_id in channel_ids]
    channel_results = await asyncio.gather(*tasks)

    for ch_data in channel_results:
        results[ch_data['channel_id']] = ch_data

    return {"channels": results}


@app.websocket("/ws/{task_id}")
async def websocket_research(websocket: WebSocket, task_id: str):
    """WebSocket 研究任务"""
    await manager.connect(websocket, task_id)

    try:
        # 等待第一条消息（研究请求）
        data = await websocket.receive_json()

        # 处理心跳 ping
        if data.get('type') == 'ping':
            await websocket.send_json({"type": "pong", "timestamp": data.get('timestamp')})
            # 继续等待真正的请求
            data = await websocket.receive_json()

        request = ResearchRequest(**data)

        await manager.send_progress(task_id, {
            "type": "start",
            "topic": request.topic,
            "mode": request.mode
        })

        # 创建心跳处理任务
        async def handle_heartbeat():
            """持续处理心跳消息"""
            while manager.is_connected(task_id):
                try:
                    # 使用短超时来检查是否有新消息
                    msg = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                    if msg.get('type') == 'ping':
                        await websocket.send_json({"type": "pong", "timestamp": msg.get('timestamp')})
                        print(f"💓 响应心跳 pong ({task_id})")
                except asyncio.TimeoutError:
                    # 没有新消息，继续等待
                    continue
                except WebSocketDisconnect:
                    print(f"💔 心跳检测到客户端断开 ({task_id})")
                    break
                except Exception as e:
                    # 其他错误，可能是连接问题
                    if "disconnect" in str(e).lower() or "closed" in str(e).lower():
                        break
                    continue

        # 并行运行：心跳处理 + 研究任务
        heartbeat_task = asyncio.create_task(handle_heartbeat())

        try:
            # 初始化缓存状态
            task_cache.update_progress(task_id, 0, "任务开始")

            result = await run_research_task(task_id, request)

            # 取消心跳任务
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

            # 保存结果到缓存（无论连接是否断开）
            task_cache.save(task_id, result, "complete")

            # 发送完成消息
            if manager.is_connected(task_id):
                await manager.send_progress(task_id, {
                    "type": "complete",
                    "result": result
                })
            else:
                print(f"⚠️ 任务完成但 WebSocket 已断开，结果已缓存: {task_id}")

        except Exception as e:
            heartbeat_task.cancel()
            # 保存错误状态到缓存
            task_cache.save(task_id, {"error": str(e)}, "error")
            raise e

    except WebSocketDisconnect:
        print(f"WebSocket 客户端断开连接: {task_id}")
        print(f"   💡 客户端可通过 /api/task/{task_id}/status 获取结果")
        manager.disconnect(task_id)
    except Exception as e:
        print(f"研究任务错误 ({task_id}): {e}")
        # 保存错误到缓存
        task_cache.save(task_id, {"error": str(e)}, "error")
        # 尝试发送错误消息，但如果连接已断开则忽略
        if manager.is_connected(task_id):
            try:
                await manager.send_progress(task_id, {
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass
        manager.disconnect(task_id)


async def run_research_task(task_id: str, request: ResearchRequest) -> dict:
    """执行研究任务"""

    # 打印收到的筛选参数
    print(f"\n📋 收到研究请求:")
    print(f"   主题: {request.topic}")
    print(f"   模式: {request.mode}")
    print(f"   播放量范围: {request.views_min} - {request.views_max}")
    print(f"   时长筛选: {request.duration_filter}")
    print(f"   时间范围: {request.time_range}")
    print(f"   AI筛选: {request.ai_filter}")
    print(f"   排序: {request.sort_by}")

    # 新的模式配置：支持更大数量
    mode_config = {
        "quick": 100,      # 快速扫描：100个视频
        "standard": 500,   # 标准分析：500个视频（多任务搜索）
        "deep": 1000       # 深度挖掘：1000个视频（多任务搜索）
    }
    target_count = mode_config.get(request.mode, 500)

    # 判断是否需要多任务搜索
    use_multi_search = target_count > 200

    await manager.send_progress(task_id, {
        "type": "progress",
        "stage": "search",
        "progress": 10,
        "message": f"正在搜索 \"{request.topic}\" 相关视频...（目标: {target_count}个）"
    })

    # 进度回调（带连接检查 + 缓存更新）
    async def progress_callback(message: str, progress: int):
        # 始终更新缓存（即使连接断开）
        task_cache.update_progress(task_id, progress, message)

        if not manager.is_connected(task_id):
            return
        try:
            await manager.send_progress(task_id, {
                "type": "progress",
                "stage": "search",
                "progress": progress,
                "message": message
            })
        except Exception as e:
            print(f"   ⚠ 发送搜索进度失败: {e}", flush=True)

    # 根据目标数量选择搜索策略
    if use_multi_search:
        print(f"\n🚀 使用多任务搜索策略（目标: {target_count}个视频）")
        search_results = await search_videos_multi(
            request.topic,
            target_count,
            request.time_range,
            progress_callback
        )
    else:
        # 单任务搜索
        loop = asyncio.get_event_loop()
        search_results = await loop.run_in_executor(
            None,
            lambda: search_videos_ytdlp(request.topic, target_count, request.time_range)
        )

    await manager.send_progress(task_id, {
        "type": "progress",
        "stage": "search",
        "progress": 40,
        "message": f"找到 {len(search_results)} 个视频，正在处理..."
    })

    videos = []
    channels_map = {}

    for i, video in enumerate(search_results):
        is_ai, ai_kw = detect_ai_video(
            video.get('title', ''),
            video.get('description', ''),
            video.get('tags', [])
        )

        # 计算视频年龄和日均播放量
        published_at = video.get('upload_date', '')
        video_age_days = 1  # 默认1天，避免除零
        if published_at and len(published_at) == 8:
            try:
                pub_date = datetime.strptime(published_at, '%Y%m%d')
                video_age_days = max(1, (datetime.now() - pub_date).days)
            except:
                pass

        view_count = video.get('view_count', 0) or 0
        daily_views = view_count // video_age_days if video_age_days > 0 else 0

        video_item = {
            'youtube_id': video.get('id', ''),
            'title': video.get('title', ''),
            'channel_name': video.get('channel', video.get('uploader', '')),
            'channel_id': video.get('channel_id', ''),
            'view_count': view_count,
            'like_count': video.get('like_count', 0) or 0,
            'comment_count': video.get('comment_count', 0) or 0,
            'duration': video.get('duration', 0) or 0,
            'published_at': published_at,
            'thumbnail_url': video.get('thumbnail', ''),
            'is_ai_video': is_ai,
            'ai_keyword': ai_kw,
            # 新增：视频年龄和日均播放
            'video_age_days': video_age_days,
            'daily_views': daily_views
        }

        # 应用筛选
        if not apply_filters(video_item, request):
            continue

        videos.append(video_item)

        # 统计频道
        ch_name = video_item['channel_name']
        if ch_name:
            if ch_name not in channels_map:
                channels_map[ch_name] = {
                    'channel_id': video_item['channel_id'],
                    'channel_name': ch_name,
                    'video_count': 0,
                    'total_views': 0
                }
            channels_map[ch_name]['video_count'] += 1
            channels_map[ch_name]['total_views'] += video_item['view_count']

        if i % 20 == 0:
            progress = 40 + int((i / len(search_results)) * 30)
            await manager.send_progress(task_id, {
                "type": "progress",
                "stage": "collect",
                "progress": progress,
                "message": f"已处理 {i}/{len(search_results)} 个视频..."
            })

    # 打印筛选结果统计
    filtered_count = len(search_results) - len(videos)
    print(f"\n📊 筛选结果:")
    print(f"   原始视频数: {len(search_results)}")
    print(f"   筛选后视频数: {len(videos)}")
    print(f"   被过滤掉: {filtered_count} 个")

    await manager.send_progress(task_id, {
        "type": "progress",
        "stage": "analyze",
        "progress": 70,
        "message": f"正在分析 {len(videos)} 个视频数据..."
    })

    # ===== 并发获取 Top 视频的完整详情 =====
    # 按播放量排序，取 Top N 获取详情
    videos_sorted_by_views = sorted(videos, key=lambda x: x['view_count'], reverse=True)
    top_video_count = min(200, len(videos_sorted_by_views))  # 最多获取 200 个视频详情
    top_video_ids = [v['youtube_id'] for v in videos_sorted_by_views[:top_video_count] if v.get('youtube_id')]

    if top_video_ids:
        await manager.send_progress(task_id, {
            "type": "progress",
            "stage": "details",
            "progress": 72,
            "message": f"正在获取 Top {len(top_video_ids)} 个视频的完整详情..."
        })

        async def video_progress_callback(current, total, message):
            if not manager.is_connected(task_id):
                return
            try:
                progress = 72 + int((current / total) * 10)  # 72-82%
                await manager.send_progress(task_id, {
                    "type": "progress",
                    "stage": "details",
                    "progress": progress,
                    "message": message
                })
            except Exception as e:
                print(f"   ⚠ 发送视频详情进度失败: {e}", flush=True)

        video_details = await fetch_videos_details_concurrent(
            top_video_ids,
            max_concurrent=10,
            progress_callback=video_progress_callback
        )

        # 合并详情到视频列表
        enriched_count = 0
        for v in videos:
            vid = v.get('youtube_id')
            if vid and vid in video_details:
                details = video_details[vid]
                # 补充更多字段 - 关键：更新 view_count！
                if details.get('view_count'):
                    v['view_count'] = details.get('view_count', 0) or 0
                # 更新发布日期（关键：用于时间筛选）
                if details.get('upload_date'):
                    v['published_at'] = details.get('upload_date')
                    # 重新计算视频年龄
                    try:
                        pub_date = datetime.strptime(v['published_at'], '%Y%m%d')
                        v['video_age_days'] = max(1, (datetime.now() - pub_date).days)
                        v['daily_views'] = v['view_count'] // v['video_age_days'] if v['video_age_days'] > 0 else 0
                    except:
                        pass
                v['description'] = details.get('description', '')[:500]  # 限制长度
                v['tags'] = details.get('tags', [])[:20]  # 限制标签数量
                v['like_count'] = details.get('like_count', v.get('like_count', 0)) or 0
                v['comment_count'] = details.get('comment_count', v.get('comment_count', 0)) or 0
                v['categories'] = details.get('categories', [])
                v['has_details'] = True
                enriched_count += 1
            else:
                v['has_details'] = False

        print(f"   ✓ 已补充 {enriched_count} 个视频的完整详情")

        # 重新按真实播放量排序
        videos.sort(key=lambda x: x['view_count'], reverse=True)

        # 重新计算频道的 total_views（因为视频播放量已更新）
        for ch_name in channels_map:
            channels_map[ch_name]['total_views'] = 0
        for v in videos:
            ch_name = v.get('channel_name')
            if ch_name and ch_name in channels_map:
                channels_map[ch_name]['total_views'] += v['view_count']

    # 整理频道列表（仅用于排序，不计算搜索统计）
    channels = list(channels_map.values())

    # 按搜索结果排序
    channels.sort(key=lambda x: x['total_views'], reverse=True)

    # 获取所有需要显示的频道数据（最多100个，与返回数量一致）
    max_channels_to_fetch = 100
    all_channel_ids = [ch['channel_id'] for ch in channels[:max_channels_to_fetch] if ch.get('channel_id')]

    # 获取真实频道数据
    if all_channel_ids:
        await manager.send_progress(task_id, {
            "type": "progress",
            "stage": "channels",
            "progress": 85,
            "message": f"正在获取 {len(all_channel_ids)} 个频道的真实数据...",
            "channel_fetch": {
                "total": len(all_channel_ids),
                "current": 0,
                "estimated_seconds": len(all_channel_ids) * 1.5  # 初始预估
            }
        })

        # 频道获取进度回调（带连接检查）
        async def channel_progress_callback(current, total, stats):
            # 检查 WebSocket 是否仍然连接
            if not manager.is_connected(task_id):
                print(f"   ⚠ WebSocket 已断开，停止发送进度", flush=True)
                return

            # 进度从 85% 到 94%
            progress = 85 + int((current / total) * 9)
            try:
                await manager.send_progress(task_id, {
                    "type": "progress",
                    "stage": "channels",
                    "progress": progress,
                    "message": f"获取频道数据 {current}/{total}",
                    "channel_fetch": {
                        "total": total,
                        "current": current,
                        "success_count": stats['success_count'],
                        "fail_count": stats['fail_count'],
                        "estimated_remaining_seconds": stats['estimated_remaining_seconds'],
                        "network_speed": stats['network_speed'],
                        "avg_time_per_channel": stats['avg_time_per_channel'],
                        "last_fetch_time": stats['last_fetch_time'],
                        "current_channel": stats['current_channel']
                    }
                })
            except Exception as e:
                print(f"   ⚠ 发送进度失败: {e}", flush=True)

        print(f"\n📊 获取频道真实数据: {len(all_channel_ids)} 个频道", flush=True)
        real_stats = await fetch_channels_real_stats(
            all_channel_ids,
            max_retries=2,
            progress_callback=channel_progress_callback
        )

        # 统计成功数量
        success_count = sum(1 for s in real_stats.values() if s.get('_fetch_status') == 'success')
        print(f"   ✓ 成功获取 {success_count}/{len(all_channel_ids)} 个频道的真实数据", flush=True)

        # 合并真实数据到频道统计
        for ch in channels:
            cid = ch.get('channel_id')
            if cid and cid in real_stats:
                stats = real_stats[cid]
                fetch_status = stats.get('_fetch_status', 'unknown')

                if fetch_status == 'success':
                    # 成功获取
                    ch['subscriber_count'] = stats['subscriber_count']
                    ch['real_video_count'] = stats['real_video_count']
                    ch['total_channel_views'] = stats['total_channel_views']
                    ch['avg_channel_views'] = stats['avg_channel_views']
                    ch['has_real_stats'] = True
                    ch['fetch_status'] = 'success'
                elif fetch_status == 'permanent_failure':
                    # 永久性失败（频道不存在等）
                    ch['subscriber_count'] = 0
                    ch['real_video_count'] = 0
                    ch['total_channel_views'] = 0
                    ch['avg_channel_views'] = 0
                    ch['has_real_stats'] = False
                    ch['fetch_status'] = 'permanent_failure'
                    ch['fetch_error'] = stats.get('_error_type', 'unknown')
                else:
                    # 网络失败（可重试）
                    ch['subscriber_count'] = 0
                    ch['real_video_count'] = 0
                    ch['total_channel_views'] = 0
                    ch['avg_channel_views'] = 0
                    ch['has_real_stats'] = False
                    ch['fetch_status'] = 'network_failure'
                    ch['fetch_error'] = stats.get('_error_type', 'unknown')
                    ch['retriable'] = True  # 标记可重试
            else:
                # 不在获取列表中（超出最大获取数量）
                ch['subscriber_count'] = 0
                ch['real_video_count'] = 0
                ch['total_channel_views'] = 0
                ch['avg_channel_views'] = 0
                ch['has_real_stats'] = False
                ch['fetch_status'] = 'not_fetched'

    # 重新排序（按总播放量，因为订阅数可能获取不到）
    videos = sort_videos(videos, request.sort_by)
    channels.sort(key=lambda x: x['total_views'], reverse=True)

    # 计算分布
    duration_dist = calculate_duration_distribution(videos)

    # ===== 分类视频：近期爆款 vs 长青视频 =====
    # 近期爆款：30天内发布，播放量>=1000，按播放量从高到低排序
    recent_hits = [
        v for v in videos
        if v['video_age_days'] <= 30 and v['view_count'] >= 1000
    ]
    recent_hits.sort(key=lambda x: x['view_count'], reverse=True)

    # 长青视频：发布超过180天，日均播放>=1000（说明持续有流量）
    evergreen_videos = [
        v for v in videos
        if v['video_age_days'] > 180 and v['daily_views'] >= 1000
    ]
    evergreen_videos.sort(key=lambda x: x['daily_views'], reverse=True)

    print(f"\n📊 视频分类:")
    print(f"   近期爆款(30天内,≥1000播放): {len(recent_hits)} 个")
    print(f"   长青视频(>180天,日均≥1000): {len(evergreen_videos)} 个")

    await manager.send_progress(task_id, {
        "type": "progress",
        "stage": "report",
        "progress": 95,
        "message": "正在生成分析报告..."
    })

    insights = generate_insights(videos, channels, duration_dist)

    return {
        "topic": request.topic,
        "total_videos": len(videos),
        "total_views": sum(v['view_count'] for v in videos),
        "total_channels": len(channels),
        "videos": videos[:200],
        "channels": channels[:100],
        "insights": insights,
        "duration_distribution": duration_dist,
        "ai_video_count": sum(1 for v in videos if v.get('is_ai_video')),
        # 新增：视频分类
        "recent_hits": recent_hits[:50],  # 近期爆款 Top 50
        "evergreen_videos": evergreen_videos[:50]  # 长青视频 Top 50
    }


def apply_filters(video: dict, request: ResearchRequest) -> bool:
    """应用筛选条件"""
    if request.views_min and video['view_count'] < request.views_min:
        return False
    if request.views_max and video['view_count'] > request.views_max:
        return False

    if request.duration_filter:
        duration_cat = get_duration_category(video['duration'])
        if duration_cat not in request.duration_filter:
            return False

    if request.ai_filter == 'ai' and not video.get('is_ai_video'):
        return False
    if request.ai_filter == 'human' and video.get('is_ai_video'):
        return False

    # 时间范围筛选：
    # - 24h/7d/30d/1y: YouTube sp 参数已在搜索时过滤
    # - 90d（3个月）: YouTube 没有原生支持，需要在这里补充过滤
    if request.time_range == '90d':
        if not check_time_range(video.get('published_at', ''), '90d'):
            return False

    return True


def check_time_range(published_at: str, time_range: str) -> bool:
    """检查视频发布时间是否在指定范围内"""
    if not published_at:
        return True  # 如果没有发布时间，不过滤

    try:
        # yt-dlp 返回的日期格式是 YYYYMMDD
        if len(published_at) == 8:
            pub_date = datetime.strptime(published_at, '%Y%m%d')
        else:
            pub_date = datetime.strptime(published_at[:10], '%Y-%m-%d')

        now = datetime.now()

        time_deltas = {
            '24h': 1,
            '7d': 7,
            '30d': 30,
            '90d': 90,
            '1y': 365
        }

        days = time_deltas.get(time_range)
        if days:
            cutoff = now - timedelta(days=days)
            return pub_date >= cutoff

        return True
    except Exception as e:
        print(f"日期解析错误: {e}, published_at={published_at}")
        return True  # 解析失败时不过滤


def sort_videos(videos: List[dict], sort_by: str) -> List[dict]:
    """排序视频"""
    sort_keys = {
        'views': lambda x: x['view_count'],
        'likes': lambda x: x['like_count'],
        'comments': lambda x: x['comment_count'],
        'recent': lambda x: x['published_at'] or '',
        'engagement': lambda x: (x['like_count'] + x['comment_count']) / max(x['view_count'], 1)
    }
    key_func = sort_keys.get(sort_by, sort_keys['views'])
    return sorted(videos, key=key_func, reverse=True)


def calculate_duration_distribution(videos: List[dict]) -> dict:
    """计算时长分布"""
    dist = {
        "short": {"count": 0, "total_views": 0, "label": "<5分钟"},
        "medium": {"count": 0, "total_views": 0, "label": "5-20分钟"},
        "long": {"count": 0, "total_views": 0, "label": ">20分钟"}
    }

    for v in videos:
        cat = get_duration_category(v['duration'])
        dist[cat]["count"] += 1
        dist[cat]["total_views"] += v['view_count']

    for cat in dist:
        if dist[cat]["count"] > 0:
            dist[cat]["avg_views"] = dist[cat]["total_views"] // dist[cat]["count"]
        else:
            dist[cat]["avg_views"] = 0

    return dist


def generate_insights(videos: List[dict], channels: List[dict], duration_dist: dict) -> dict:
    """生成洞察"""
    insights = {
        "opportunities": [],
        "top_performing": None,
        "market_summary": {}
    }

    if not videos:
        return insights

    total_views = sum(v['view_count'] for v in videos)
    avg_views = total_views // len(videos) if videos else 0

    insights["market_summary"] = {
        "total_videos": len(videos),
        "total_views": total_views,
        "avg_views": avg_views,
        "total_channels": len(channels)
    }

    # 最佳时长机会
    best_duration = max(duration_dist.items(), key=lambda x: x[1]["avg_views"])
    if best_duration[1]["count"] > 0:
        supply_pct = (best_duration[1]["count"] / len(videos)) * 100
        insights["opportunities"].append({
            "type": "duration",
            "title": f"{best_duration[1]['label']}视频表现最佳",
            "description": f"这个时长只占 {supply_pct:.1f}% 供给，但平均播放量达 {best_duration[1]['avg_views']:,}",
            "score": "A" if best_duration[1]["avg_views"] > avg_views * 2 else "B"
        })

    # 爆款视频
    if videos:
        top_video = videos[0]
        insights["top_performing"] = {
            "title": top_video['title'],
            "views": top_video['view_count'],
            "channel": top_video['channel_name']
        }

    # AI 视频机会
    ai_count = sum(1 for v in videos if v.get('is_ai_video'))
    if ai_count > 0:
        ai_pct = (ai_count / len(videos)) * 100
        insights["opportunities"].append({
            "type": "ai_content",
            "title": f"发现 {ai_count} 个 AI 生成视频",
            "description": f"AI 内容占比 {ai_pct:.1f}%，{'这个领域 AI 内容较多' if ai_pct > 10 else '仍以真人内容为主'}",
            "score": "B"
        })

    return insights


# ============ 监控任务 API ============

@app.post("/api/monitor/tasks")
async def create_monitor_task(task: MonitorTaskCreate):
    """创建监控任务

    设置关键词和采集频率，系统将定时采集数据
    """
    db = get_database()

    # 检查是否已存在
    existing = db.get_monitor_task_by_keyword(task.keyword)
    if existing:
        raise HTTPException(status_code=400, detail=f"关键词 '{task.keyword}' 已存在监控任务")

    task_id = db.create_monitor_task(
        keyword=task.keyword,
        description=task.description,
        frequency=task.frequency,
        max_results=task.max_results
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": f"监控任务已创建: {task.keyword}"
    }


@app.get("/api/monitor/tasks")
async def list_monitor_tasks(active_only: bool = Query(default=True)):
    """获取所有监控任务"""
    db = get_database()
    tasks = db.list_monitor_tasks(active_only=active_only)
    return {
        "tasks": tasks,
        "count": len(tasks)
    }


@app.get("/api/monitor/tasks/{task_id}")
async def get_monitor_task(task_id: int):
    """获取单个监控任务详情"""
    db = get_database()
    task = db.get_monitor_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    # 获取统计信息
    growth_summary = db.get_growth_summary(task_id, days=7)

    return {
        **task,
        "growth_summary": growth_summary
    }


@app.put("/api/monitor/tasks/{task_id}")
async def update_monitor_task(task_id: int, update: MonitorTaskUpdate):
    """更新监控任务"""
    db = get_database()

    task = db.get_monitor_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if update_data:
        db.update_monitor_task(task_id, **update_data)

    return {"success": True, "message": "监控任务已更新"}


@app.delete("/api/monitor/tasks/{task_id}")
async def delete_monitor_task(task_id: int):
    """删除监控任务"""
    db = get_database()
    result = db.delete_monitor_task(task_id)
    if result == 0:
        raise HTTPException(status_code=404, detail="监控任务不存在")
    return {"success": True, "message": "监控任务已删除"}


@app.post("/api/monitor/tasks/{task_id}/toggle")
async def toggle_monitor_task(task_id: int):
    """切换监控任务的启用/暂停状态"""
    db = get_database()
    result = db.toggle_monitor_task(task_id)
    if result == 0:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    task = db.get_monitor_task(task_id)
    status = "已启用" if task['is_active'] else "已暂停"
    return {"success": True, "is_active": task['is_active'], "message": f"监控任务{status}"}


@app.post("/api/monitor/tasks/{task_id}/run")
async def run_monitor_task_now(task_id: int, background_tasks: BackgroundTasks):
    """立即执行监控任务（手动触发）"""
    db = get_database()
    task = db.get_monitor_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    # 在后台执行采集
    background_tasks.add_task(execute_monitor_task, task_id)

    return {
        "success": True,
        "message": f"监控任务已开始执行: {task['keyword']}",
        "task_id": task_id
    }


async def execute_monitor_task(task_id: int):
    """执行单个监控任务（后台运行）"""
    db = get_database()
    task = db.get_monitor_task(task_id)

    if not task:
        print(f"❌ 监控任务 {task_id} 不存在")
        return

    keyword = task['keyword']
    max_results = task.get('max_results', 500)

    print(f"\n🔄 开始执行监控任务: {keyword}")
    print(f"   任务ID: {task_id}")
    print(f"   目标数量: {max_results}")

    try:
        # 1. 执行搜索
        loop = asyncio.get_event_loop()
        videos = await search_videos_multi(
            keyword,
            target_count=max_results,
            use_smart_keywords=True
        )

        print(f"   ✓ 搜索完成: {len(videos)} 个视频")

        # 2. 保存快照
        saved_count = 0
        for video in videos:
            video_data = {
                'video_id': video.get('id'),
                'title': video.get('title'),
                'channel_name': video.get('channel', video.get('uploader')),
                'channel_id': video.get('channel_id'),
                'view_count': video.get('view_count', 0) or 0,
                'like_count': video.get('like_count', 0) or 0,
                'comment_count': video.get('comment_count', 0) or 0,
                'duration': video.get('duration', 0) or 0,
                'published_at': video.get('upload_date')
            }
            try:
                db.save_video_snapshot(task_id, video_data)
                saved_count += 1
            except Exception as e:
                pass  # 忽略重复保存等错误

        print(f"   ✓ 保存快照: {saved_count} 个视频")

        # 3. 计算增长数据
        growth_count = db.calculate_and_save_growth(task_id)
        print(f"   ✓ 计算增长: {growth_count} 个视频")

        # 4. 更新任务状态
        db.update_monitor_task_last_run(task_id)

        print(f"   ✓ 监控任务完成: {keyword}")

    except Exception as e:
        print(f"   ❌ 监控任务失败: {e}")


@app.get("/api/monitor/tasks/{task_id}/growth")
async def get_task_growth(
    task_id: int,
    days: int = Query(default=7, le=30),
    trending_only: bool = Query(default=False)
):
    """获取监控任务的增长数据"""
    db = get_database()

    task = db.get_monitor_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    # 获取增长数据
    growth_data = db.get_video_growth(
        task_id=task_id,
        trending_only=trending_only,
        limit=100
    )

    # 获取趋势视频
    trending = db.get_trending_videos(task_id=task_id, days=days, limit=20)

    # 获取摘要
    summary = db.get_growth_summary(task_id, days=days)

    return {
        "task_id": task_id,
        "keyword": task['keyword'],
        "days": days,
        "summary": summary,
        "trending_videos": trending,
        "growth_data": growth_data[:50]
    }


@app.get("/api/monitor/tasks/{task_id}/snapshots")
async def get_task_snapshots(
    task_id: int,
    date: Optional[str] = Query(default=None, description="日期 YYYY-MM-DD"),
    limit: int = Query(default=100, le=500)
):
    """获取监控任务的视频快照"""
    db = get_database()

    task = db.get_monitor_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    snapshots = db.get_video_snapshots(task_id=task_id, date=date, limit=limit)

    return {
        "task_id": task_id,
        "keyword": task['keyword'],
        "date": date,
        "snapshots": snapshots,
        "count": len(snapshots)
    }


@app.get("/api/monitor/due")
async def get_due_tasks():
    """获取待执行的监控任务"""
    db = get_database()
    tasks = db.get_due_monitor_tasks()
    return {
        "tasks": tasks,
        "count": len(tasks)
    }


# ============ 定时任务调度器 ============

scheduler_running = False


async def scheduler_loop():
    """定时任务调度器循环"""
    global scheduler_running
    print("🕐 定时任务调度器已启动")

    while scheduler_running:
        try:
            db = get_database()
            due_tasks = db.get_due_monitor_tasks()

            if due_tasks:
                print(f"\n📋 发现 {len(due_tasks)} 个待执行任务")
                for task in due_tasks:
                    print(f"   - 执行任务: {task['keyword']}")
                    await execute_monitor_task(task['id'])
                    await asyncio.sleep(2)  # 任务间隔

        except Exception as e:
            print(f"❌ 调度器错误: {e}")

        # 每分钟检查一次
        await asyncio.sleep(60)

    print("🛑 定时任务调度器已停止")


@app.post("/api/monitor/scheduler/start")
async def start_scheduler(background_tasks: BackgroundTasks):
    """启动定时任务调度器"""
    global scheduler_running

    if scheduler_running:
        return {"success": False, "message": "调度器已在运行"}

    scheduler_running = True
    background_tasks.add_task(scheduler_loop)

    return {"success": True, "message": "定时任务调度器已启动"}


@app.post("/api/monitor/scheduler/stop")
async def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler_running

    if not scheduler_running:
        return {"success": False, "message": "调度器未运行"}

    scheduler_running = False
    return {"success": True, "message": "定时任务调度器已停止"}


@app.get("/api/monitor/scheduler/status")
async def scheduler_status():
    """获取调度器状态"""
    return {
        "running": scheduler_running,
        "message": "调度器运行中" if scheduler_running else "调度器已停止"
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    print(f"""
╔══════════════════════════════════════════╗
║     YouTube 内容助手 API 服务             ║
╠══════════════════════════════════════════╣
║  API 文档:  http://localhost:{port}/docs      ║
║  前端页面:  http://localhost:{port}/           ║
║  WebSocket: ws://localhost:{port}/ws/{{task_id}} ║
╚══════════════════════════════════════════╝
    """)

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
