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

from src.utils.logger import setup_logger
from src.utils.config import get_config

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
        'hour': 'EgQIARAB',     # 过去 1 小时
        'today': 'EgQIAhAB',    # 今天（24小时内）
        'day': 'EgQIAhAB',      # 同 today
        'week': 'EgQIAxAB',     # 本周（7天内）
        'month': 'EgQIBBAB',    # 本月（30天内）
        'quarter': 'EgQIBBAB',  # 季度（使用月过滤，后续代码补充过滤）
        'year': 'EgQIBRAB',     # 今年
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
                - 'quarter': 3个月内
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
        logger.info(f"搜索视频: keyword={keyword}, max_results={max_results}, time_range={time_range}")

        # 根据是否有时间过滤选择不同的搜索方式
        if time_range and time_range in self.TIME_FILTER_PARAMS:
            # 使用 YouTube 原生搜索 URL（支持时间过滤）
            return self._search_with_time_filter(keyword, max_results, time_range)
        else:
            # 传统搜索方式（无时间过滤）
            return self._search_basic(keyword, max_results)

    def _search_basic(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """基础搜索（无时间过滤）"""
        search_query = f"ytsearch{max_results}:{keyword}"

        args = [
            '--dump-json',
            '--flat-playlist',
            '--no-warnings',
            search_query
        ]

        return self._execute_search(args)

    def _search_with_time_filter(
        self,
        keyword: str,
        max_results: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """
        使用 YouTube 原生搜索 URL 进行时间过滤搜索

        原理：YouTube 搜索页面 URL 的 sp 参数控制过滤器
        例如: https://www.youtube.com/results?search_query=python&sp=EgQIBBAB
        """
        from urllib.parse import quote

        sp = self.TIME_FILTER_PARAMS.get(time_range, '')
        encoded_keyword = quote(keyword)

        # 构建 YouTube 原生搜索 URL
        search_url = f"https://www.youtube.com/results?search_query={encoded_keyword}&sp={sp}"

        logger.info(f"使用时间过滤搜索: {time_range} -> sp={sp}")

        args = [
            '--dump-json',
            '--flat-playlist',
            '--playlist-end', str(max_results),
            '--no-warnings',
            search_url
        ]

        videos = self._execute_search(args)

        # 对于 quarter（3个月），YouTube 没有原生支持，需要后过滤
        if time_range == 'quarter':
            videos = self._filter_by_date_range(videos, days=90)

        return videos

    def _execute_search(self, args: List[str]) -> List[Dict[str, Any]]:
        """执行搜索命令并解析结果"""
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
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败: {e}")
                    continue

            logger.info(f"搜索完成，获取 {len(videos)} 个结果")
            return videos

        except YtDlpError as e:
            logger.error(f"搜索失败: {e}")
            raise

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
        return {
            # 基础信息
            'youtube_id': data.get('id', ''),
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
