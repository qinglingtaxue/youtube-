#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt-dlp 封装层
提供 YouTube 视频信息获取功能

引用规约：
- api.spec.md: 5.2 yt-dlp CLI
- data.spec.md: CompetitorVideo 实体
- real.md: #3 版权合规

功能：
- 搜索视频
- 获取视频详细信息
- 下载字幕（仅用于竞品分析）
"""

import json
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.logger import setup_logger
from src.shared.config import get_config

logger = setup_logger('yt_dlp_client')


class YtDlpError(Exception):
    """yt-dlp 相关错误"""
    pass


class YtDlpClient:
    """
    yt-dlp 封装客户端

    用于获取 YouTube 视频元数据，仅用于竞品分析。
    遵守 real.md#3 版权合规约束：
    - 不下载他人视频内容
    - 仅获取公开元数据
    """

    # YouTube 搜索时间过滤参数（sp 参数）
    # 这些是 YouTube 原生搜索 URL 的过滤器编码
    TIME_FILTER_PARAMS = {
        'hour': 'EgQIARAB',       # 过去 1 小时
        'today': 'EgQIAhAB',      # 今天（24小时内）
        'day': 'EgQIAhAB',        # 同 today
        'week': 'EgQIAxAB',       # 本周（7天内）
        'month': 'EgQIBBAB',      # 本月（30天内）
        'two_months': 'EgQIBRAB', # 60天（使用 year 过滤，后续代码补充过滤）
        'quarter': 'EgQIBRAB',    # 季度（使用 year 过滤，后续代码补充过滤）
        'year': 'EgQIBRAB',       # 今年
    }

    # YouTube 搜索排序参数（sp 参数）
    # 这些参数可以让 YouTube 按特定方式排序返回结果
    SORT_PARAMS = {
        'relevance': '',           # 按相关性（默认）
        'date': 'CAISAhAB',        # 按上传日期（最新优先）
        'view_count': 'CAMSAhAB',  # 按播放量（最高优先）★ 关键！
        'rating': 'CAESAhAB',      # 按评分
    }

    # 组合参数：时间过滤 + 按播放量排序
    # 确保搜索结果是指定时间范围内播放量最高的视频
    TIME_AND_VIEW_SORT_PARAMS = {
        'hour': 'EgQIARABGAI%3D',       # 过去1小时 + 按播放量
        'today': 'EgQIAhABGAI%3D',      # 今天 + 按播放量
        'day': 'EgQIAhABGAI%3D',        # 同 today
        'week': 'EgQIAxABGAI%3D',       # 本周 + 按播放量
        'month': 'EgQIBBABGAI%3D',      # 本月 + 按播放量
        'two_months': 'EgQIBRABGAI%3D', # 60天 + 按播放量（使用 year，后过滤）
        'year': 'EgQIBRABGAI%3D',       # 今年 + 按播放量
    }

    def __init__(self, config: Optional[Any] = None):
        """
        初始化客户端

        Args:
            config: 配置对象 (可选)
        """
        self.config = config or get_config()
        self.timeout = self.config.get('youtube.timeout', 30)
        self.rate_limit_delay = self.config.get('youtube.rate_limit_delay', 2)

        # 验证 yt-dlp 是否可用
        self._verify_ytdlp()

    def _verify_ytdlp(self):
        """验证 yt-dlp 是否已安装"""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"yt-dlp 版本: {result.stdout.strip()}")
            else:
                raise YtDlpError("yt-dlp 不可用")
        except FileNotFoundError:
            raise YtDlpError("yt-dlp 未安装，请运行: pip install yt-dlp")
        except subprocess.TimeoutExpired:
            raise YtDlpError("yt-dlp 响应超时")

    def _run_ytdlp(self, args: List[str], timeout: Optional[int] = None) -> str:
        """
        执行 yt-dlp 命令

        Args:
            args: 命令参数列表
            timeout: 超时时间（秒）

        Returns:
            命令输出

        Raises:
            YtDlpError: 执行失败
        """
        cmd = ['yt-dlp'] + args
        timeout = timeout or self.timeout

        logger.debug(f"执行命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                # 检查常见错误
                if 'Video unavailable' in error_msg:
                    raise YtDlpError(f"视频不可用: {error_msg}")
                elif 'Sign in' in error_msg:
                    raise YtDlpError(f"需要登录: {error_msg}")
                elif 'rate' in error_msg.lower():
                    raise YtDlpError(f"请求过于频繁: {error_msg}")
                else:
                    raise YtDlpError(f"yt-dlp 执行失败: {error_msg}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise YtDlpError(f"命令执行超时 ({timeout}秒)")
        except Exception as e:
            if isinstance(e, YtDlpError):
                raise
            raise YtDlpError(f"执行错误: {str(e)}")

    def search_videos(
        self,
        keyword: str,
        max_results: int = 50,
        sort_by: str = "relevance",
        time_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索 YouTube 视频

        支持时间过滤，使用 YouTube 原生搜索 URL 参数

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数（建议不超过 100）
            sort_by: 排序方式 (relevance/date/view_count/rating)
            time_range: 时间范围过滤
                - 'hour': 过去1小时
                - 'today'/'day': 24小时内
                - 'week': 7天内
                - 'month': 30天内
                - 'two_months': 60天内 ★ 新增
                - 'quarter': 3个月内（90天）
                - 'year': 今年
                - None: 不过滤（默认）

        Returns:
            视频信息列表，每项包含：
            - id: 视频 ID
            - title: 标题
            - channel: 频道名
            - channel_id: 频道 ID
            - duration: 时长（秒）
            - view_count: 播放量
            - upload_date: 上传日期
        """
        logger.info(f"搜索视频: keyword={keyword}, max_results={max_results}, sort_by={sort_by}, time_range={time_range}")

        # 使用 YouTube 原生搜索 URL（支持时间过滤和排序）
        return self._search_with_filters(keyword, max_results, time_range, sort_by)

    def _search_with_filters(
        self,
        keyword: str,
        max_results: int,
        time_range: Optional[str] = None,
        sort_by: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        使用 YouTube 原生搜索 URL 进行搜索 - 支持时间过滤和排序组合

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            time_range: 时间范围 (hour/today/week/month/year/None)
            sort_by: 排序方式 (relevance/date/view_count/rating)

        Returns:
            视频信息列表
        """
        from urllib.parse import quote

        encoded_keyword = quote(keyword)

        # 构建 sp 参数（时间过滤 + 排序）
        sp = self._build_sp_param(time_range, sort_by)

        # 构建搜索 URL
        if sp:
            search_url = f"https://www.youtube.com/results?search_query={encoded_keyword}&sp={sp}"
        else:
            search_url = f"https://www.youtube.com/results?search_query={encoded_keyword}"

        logger.info(f"搜索: time_range={time_range}, sort_by={sort_by}, sp={sp}")

        # 移除 --flat-playlist，获取完整视频信息（包括发布日期、频道ID等）
        args = [
            '--dump-json',
            '--no-download',
            '--playlist-end', str(max_results),
            '--no-warnings',
            '--ignore-errors',  # 跳过无法访问的视频
            search_url
        ]

        videos = self._execute_search(args, full_info=True)

        # 对于 two_months（60天）和 quarter（90天），YouTube 没有原生支持，需要后过滤
        if time_range == 'two_months':
            videos = self._filter_by_date_range(videos, days=60)
        elif time_range == 'quarter':
            videos = self._filter_by_date_range(videos, days=90)

        return videos

    def _execute_search(self, args: List[str], full_info: bool = False) -> List[Dict[str, Any]]:
        """
        执行搜索命令并解析结果

        Args:
            args: yt-dlp 命令参数
            full_info: 是否获取完整视频信息（包括发布日期、点赞数等）
        """
        try:
            # 完整信息模式需要更长超时（每个视频约3-5秒）
            timeout = 300 if full_info else 60
            output = self._run_ytdlp(args, timeout=timeout)

            videos = []
            for line in output.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # 根据模式选择解析方法
                    if full_info:
                        video = self._parse_video_info(data)
                    else:
                        video = self._parse_search_result(data)
                    if video:
                        videos.append(video)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败: {e}")
                    continue

            logger.info(f"搜索完成，获取 {len(videos)} 个结果 (full_info={full_info})")
            return videos

        except YtDlpError as e:
            logger.error(f"搜索失败: {e}")
            raise

    def _build_sp_param(
        self,
        time_range: Optional[str] = None,
        sort_by: str = "relevance"
    ) -> str:
        """
        构建 YouTube 搜索的 sp 参数

        YouTube sp 参数是 base64 编码的 protobuf，用于控制搜索过滤和排序。

        Args:
            time_range: 时间范围 (hour/today/week/month/year/None)
            sort_by: 排序方式 (relevance/date/view_count/rating)

        Returns:
            sp 参数字符串
        """
        # 如果同时需要时间过滤和按播放量排序，使用预定义的组合参数
        if time_range and sort_by == 'view_count':
            if time_range in self.TIME_AND_VIEW_SORT_PARAMS:
                return self.TIME_AND_VIEW_SORT_PARAMS[time_range]
            # quarter 没有原生支持，使用 year + view_count，后续代码会补充过滤
            elif time_range == 'quarter':
                return self.TIME_AND_VIEW_SORT_PARAMS.get('year', '')

        # 只需要时间过滤
        if time_range and time_range in self.TIME_FILTER_PARAMS:
            return self.TIME_FILTER_PARAMS[time_range]

        # 只需要排序（无时间过滤）
        if sort_by in self.SORT_PARAMS and sort_by != 'relevance':
            return self.SORT_PARAMS[sort_by]

        # 默认（相关性排序，无时间过滤）
        return ''

    def _filter_by_date_range(
        self,
        videos: List[Dict[str, Any]],
        days: int
    ) -> List[Dict[str, Any]]:
        """按日期范围后过滤视频"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = []

        for video in videos:
            upload_date_str = video.get('upload_date')
            if not upload_date_str:
                # 没有日期信息的视频保留（宁可多不可漏）
                filtered.append(video)
                continue

            try:
                # 解析日期 (格式: YYYY-MM-DD)
                upload_date = datetime.strptime(upload_date_str, '%Y-%m-%d')
                if upload_date >= cutoff_date:
                    filtered.append(video)
            except ValueError:
                # 日期解析失败，保留
                filtered.append(video)

        logger.info(f"日期过滤: {len(videos)} -> {len(filtered)} (保留 {days} 天内)")
        return filtered

    def _parse_search_result(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析搜索结果"""
        if data.get('_type') == 'playlist':
            return None

        return {
            'id': data.get('id', ''),
            'title': data.get('title', ''),
            'channel': data.get('channel', '') or data.get('uploader', ''),
            'channel_id': data.get('channel_id', '') or data.get('uploader_id', ''),
            'duration': data.get('duration'),
            'view_count': data.get('view_count'),
            'upload_date': self._parse_date(data.get('upload_date')),
            'url': f"https://www.youtube.com/watch?v={data.get('id', '')}"
        }

    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        获取视频详细信息

        基于 api.spec.md 5.2 定义:
        yt-dlp --dump-json "https://www.youtube.com/watch?v={video_id}"

        Args:
            video_id: YouTube 视频 ID (11 位字符)

        Returns:
            视频详细信息，符合 data.spec.md CompetitorVideo 实体
        """
        logger.info(f"获取视频信息: {video_id}")

        # 验证视频 ID 格式
        if not self._validate_video_id(video_id):
            raise YtDlpError(f"无效的视频 ID: {video_id}")

        url = f"https://www.youtube.com/watch?v={video_id}"

        args = [
            '--dump-json',
            '--no-download',
            '--no-warnings',
            url
        ]

        try:
            output = self._run_ytdlp(args, timeout=30)
            data = json.loads(output)
            return self._parse_video_info(data)

        except json.JSONDecodeError as e:
            raise YtDlpError(f"视频信息解析失败: {e}")

    def _parse_video_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析视频信息为 CompetitorVideo 格式

        符合 data.spec.md 实体定义
        """
        video_id = data.get('id', '')
        return {
            # 基础信息（同时提供 id 和 youtube_id 以兼容不同调用方）
            'id': video_id,
            'youtube_id': video_id,
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'channel_name': data.get('channel', '') or data.get('uploader', ''),
            'channel_id': data.get('channel_id', '') or data.get('uploader_id', ''),

            # 统计数据
            'view_count': data.get('view_count', 0),
            'like_count': data.get('like_count', 0),
            'comment_count': data.get('comment_count', 0),

            # 时间信息
            'duration': data.get('duration', 0),
            'upload_date': self._parse_date(data.get('upload_date')),

            # 内容信息
            'tags': data.get('tags', []),
            'categories': data.get('categories', []),
            'language': data.get('language', ''),

            # 缩略图
            'thumbnail_url': data.get('thumbnail', ''),
            'thumbnails': self._extract_thumbnails(data.get('thumbnails', [])),

            # 字幕信息
            'has_subtitles': bool(data.get('subtitles') or data.get('automatic_captions')),
            'available_subtitles': list(data.get('subtitles', {}).keys()),

            # 元数据
            'url': f"https://www.youtube.com/watch?v={data.get('id', '')}",
            'collected_at': datetime.now().isoformat()
        }

    def _extract_thumbnails(self, thumbnails: List[Dict]) -> Dict[str, str]:
        """提取缩略图 URL"""
        result = {}
        for thumb in thumbnails:
            if thumb.get('id'):
                result[thumb['id']] = thumb.get('url', '')
            elif thumb.get('resolution'):
                result[thumb['resolution']] = thumb.get('url', '')
        return result

    def get_videos_batch(
        self,
        video_ids: List[str],
        on_progress: Optional[callable] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        批量获取视频信息

        Args:
            video_ids: 视频 ID 列表
            on_progress: 进度回调函数 (current, total, video_id)

        Returns:
            (成功列表, 失败列表)
        """
        import time

        logger.info(f"批量获取 {len(video_ids)} 个视频信息")

        successful = []
        failed = []

        for i, video_id in enumerate(video_ids):
            try:
                if on_progress:
                    on_progress(i + 1, len(video_ids), video_id)

                info = self.get_video_info(video_id)
                successful.append(info)

                # 速率限制
                if i < len(video_ids) - 1:
                    time.sleep(self.rate_limit_delay)

            except YtDlpError as e:
                logger.warning(f"获取视频 {video_id} 失败: {e}")
                failed.append(video_id)

        logger.info(f"批量获取完成: 成功 {len(successful)}, 失败 {len(failed)}")
        return successful, failed

    def download_subtitles(
        self,
        video_id: str,
        language: str = 'zh',
        output_dir: Optional[Path] = None,
        auto_generated: bool = True
    ) -> Optional[Path]:
        """
        下载视频字幕（仅用于竞品分析）

        遵守 real.md#3 版权合规：仅下载字幕用于分析

        Args:
            video_id: 视频 ID
            language: 字幕语言代码
            output_dir: 输出目录
            auto_generated: 是否包含自动生成字幕

        Returns:
            字幕文件路径（如果成功）
        """
        logger.info(f"下载字幕: video_id={video_id}, language={language}")

        if not self._validate_video_id(video_id):
            raise YtDlpError(f"无效的视频 ID: {video_id}")

        output_dir = output_dir or Path('data/subtitles')
        output_dir.mkdir(parents=True, exist_ok=True)

        url = f"https://www.youtube.com/watch?v={video_id}"
        output_template = str(output_dir / f"{video_id}.%(ext)s")

        args = [
            '--skip-download',
            '--write-sub',
            '--sub-lang', language,
            '--sub-format', 'vtt',
            '-o', output_template,
            '--no-warnings',
        ]

        if auto_generated:
            args.append('--write-auto-sub')

        args.append(url)

        try:
            self._run_ytdlp(args, timeout=60)

            # 查找生成的字幕文件
            patterns = [
                output_dir / f"{video_id}.{language}.vtt",
                output_dir / f"{video_id}.vtt",
            ]

            for pattern in patterns:
                if pattern.exists():
                    logger.info(f"字幕下载成功: {pattern}")
                    return pattern

            # 尝试模糊匹配
            for f in output_dir.glob(f"{video_id}*.vtt"):
                logger.info(f"字幕下载成功: {f}")
                return f

            logger.warning(f"未找到字幕文件")
            return None

        except YtDlpError as e:
            logger.error(f"字幕下载失败: {e}")
            return None

    def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取频道视频列表

        Args:
            channel_id: 频道 ID
            max_results: 最大结果数

        Returns:
            视频列表
        """
        logger.info(f"获取频道视频: channel_id={channel_id}")

        url = f"https://www.youtube.com/channel/{channel_id}/videos"

        args = [
            '--dump-json',
            '--flat-playlist',
            '--playlist-end', str(max_results),
            '--no-warnings',
            url
        ]

        try:
            output = self._run_ytdlp(args, timeout=60)

            videos = []
            for line in output.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    video = self._parse_search_result(data)
                    if video:
                        videos.append(video)
                except json.JSONDecodeError:
                    continue

            logger.info(f"获取频道视频完成，共 {len(videos)} 个")
            return videos

        except YtDlpError as e:
            logger.error(f"获取频道视频失败: {e}")
            raise

    def _validate_video_id(self, video_id: str) -> bool:
        """验证视频 ID 格式"""
        # YouTube 视频 ID 为 11 位字符
        if not video_id or len(video_id) != 11:
            return False
        # 允许字母、数字、下划线、连字符
        return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None

        # yt-dlp 返回格式：YYYYMMDD
        if len(date_str) == 8 and date_str.isdigit():
            try:
                dt = datetime.strptime(date_str, '%Y%m%d')
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass

        return date_str

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        从 URL 提取视频 ID

        支持格式：
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None


# ============================================================
# YouTube 搜索建议（用于关键词扩展）
# ============================================================

def get_youtube_suggestions(keyword: str, limit: int = 10) -> List[str]:
    """
    获取 YouTube 搜索建议

    使用 YouTube 的搜索建议 API 获取相关关键词
    这是获取真实用户搜索行为的最佳方式

    Args:
        keyword: 种子关键词
        limit: 返回数量限制

    Returns:
        相关关键词列表
    """
    import urllib.request
    import urllib.parse
    import ssl

    try:
        # YouTube 搜索建议 API
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={encoded_keyword}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # 创建 SSL 上下文，跳过证书验证（macOS 常见问题）
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            # 响应格式: window.google.ac.h(["keyword",[["suggestion1",0],["suggestion2",0],...]])
            data = response.read().decode('utf-8')

            # 解析 JSONP 响应
            # 格式: window.google.ac.h(["query",[["sug1",0,[512,433]],["sug2",0,[512,433]],...]])
            import re
            match = re.search(r'\[.*\]', data)
            if match:
                parsed = json.loads(match.group())
                if len(parsed) > 1 and isinstance(parsed[1], list):
                    suggestions = []
                    for item in parsed[1]:
                        if isinstance(item, list) and len(item) > 0:
                            suggestions.append(item[0])
                    logger.info(f"获取 YouTube 搜索建议: {keyword} -> {len(suggestions)} 个")
                    return suggestions[:limit]

        return []
    except Exception as e:
        logger.warning(f"获取 YouTube 搜索建议失败: {e}")
        return []


def expand_keywords_from_youtube(seed_keyword: str, max_keywords: int = 15) -> List[str]:
    """
    基于 YouTube 搜索建议扩展关键词

    策略：
    1. 直接搜索种子关键词获取建议
    2. 添加常见后缀（教程、入门、技巧等）搜索
    3. 去重并返回

    Args:
        seed_keyword: 种子关键词
        max_keywords: 最大关键词数量

    Returns:
        扩展后的关键词列表（包含种子关键词）
    """
    keywords = set()
    keywords.add(seed_keyword)

    # 1. 直接获取建议
    suggestions = get_youtube_suggestions(seed_keyword)
    for s in suggestions:
        keywords.add(s)

    # 2. 常见后缀扩展
    suffixes = ['教程', '入门', '技巧', '方法', '推荐', '2025', '2024']
    for suffix in suffixes:
        query = f"{seed_keyword}{suffix}"
        more_suggestions = get_youtube_suggestions(query, limit=5)
        for s in more_suggestions:
            keywords.add(s)
            if len(keywords) >= max_keywords:
                break
        if len(keywords) >= max_keywords:
            break

    result = list(keywords)[:max_keywords]
    logger.info(f"关键词扩展: {seed_keyword} -> {len(result)} 个关键词")
    return result


# 便捷函数
def search_videos(keyword: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """便捷搜索函数"""
    client = YtDlpClient()
    return client.search_videos(keyword, max_results)


def get_video_info(video_id: str) -> Dict[str, Any]:
    """便捷获取视频信息函数"""
    client = YtDlpClient()
    return client.get_video_info(video_id)


if __name__ == '__main__':
    # 简单测试
    import sys

    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        print(f"搜索: {keyword}")

        client = YtDlpClient()
        videos = client.search_videos(keyword, max_results=5)

        for v in videos:
            print(f"  - {v['title']} ({v['id']})")
            print(f"    播放: {v.get('view_count', 'N/A')}, 时长: {v.get('duration', 'N/A')}秒")
    else:
        print("用法: python yt_dlp_client.py <搜索关键词>")
