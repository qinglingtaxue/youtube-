#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据收集模块
负责从 YouTube 收集视频数据并进行初步筛选

引用规约：
- api.spec.md: 3.1 DataCollector 接口
- data.spec.md: CompetitorVideo 实体
- real.md: #3 版权合规, #4 存储与成本控制

功能：
- 搜索视频 (通过 yt-dlp)
- 筛选高质量视频
- 保存和加载视频数据
"""

import json
import time
import urllib.parse
import urllib.request
import ssl
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from datetime import datetime
from collections import Counter
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config import get_config, Config
from src.research.yt_dlp_client import YtDlpClient, YtDlpError


class DataCollector:
    """
    数据收集器

    基于 api.spec.md 3.1 DataCollector 接口实现
    """

    def __init__(self, config: Optional[Config] = None):
        """
        初始化数据收集器

        Args:
            config: 配置对象 (可选)
        """
        self.config = config or get_config()
        self.logger = setup_logger('data_collector')

        # 从配置获取参数
        self.max_results = self.config.get('research.max_videos', 100)
        self.min_views = self.config.get('research.min_views', 1000)
        self.min_likes = self.config.get('research.min_likes', 50)
        self.max_duration = self.config.get('research.max_duration', 3600)

        # 初始化 yt-dlp 客户端
        try:
            self.ytdlp = YtDlpClient(self.config)
            self.use_ytdlp = True
            self.logger.info("使用 yt-dlp 进行数据收集")
        except YtDlpError as e:
            self.logger.warning(f"yt-dlp 不可用 ({e})，将使用模拟数据")
            self.ytdlp = None
            self.use_ytdlp = False

    def search_videos(
        self,
        keyword: str,
        max_results: int = 50,
        region: str = "US",
        time_range: str = "month",
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索视频

        符合 api.spec.md 3.1 DataCollector.search_videos 接口

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            region: 目标地区 (ISO 3166-1)
            time_range: 时间范围 (week/month/quarter/year)
            days: 最近多少天内的视频（优先级高于 time_range）

        Returns:
            竞品视频列表

        Raises:
            Exception: 搜索失败
        """
        # 计算日期范围
        if days is not None:
            date_limit = days
        else:
            date_limit = {
                'week': 7,
                'month': 30,
                'quarter': 90,
                'year': 365
            }.get(time_range, 30)

        self.logger.info(f"搜索视频: keyword={keyword}, max_results={max_results}, 时间范围={date_limit}天内")

        if self.use_ytdlp:
            return self._search_with_ytdlp(keyword, max_results, date_limit)
        else:
            return self._search_mock(keyword, max_results)

    def _search_with_ytdlp(
        self,
        keyword: str,
        max_results: int,
        date_limit: int = 30
    ) -> List[Dict[str, Any]]:
        """使用 yt-dlp 搜索视频（带时间筛选）"""
        from datetime import timedelta

        # 计算截止日期（使用相对时间，避免系统时间问题）
        # 获取当前真实时间点作为基准
        today = datetime.now()

        try:
            # 搜索时多获取一些，因为后面要过滤
            fetch_count = max_results * 3
            search_results = self.ytdlp.search_videos(keyword, fetch_count)

            if not search_results:
                self.logger.warning("搜索未返回结果")
                return []

            self.logger.info(f"搜索到 {len(search_results)} 个候选视频，开始获取详情并筛选...")

            # 获取详细信息并按日期筛选
            videos_with_details = []
            processed = 0
            skipped_old = 0

            for result in search_results:
                # 已经收集够了就停止
                if len(videos_with_details) >= max_results:
                    break

                try:
                    video_id = result.get('id')
                    if not video_id:
                        continue

                    processed += 1

                    # 获取详细信息
                    detail = self.ytdlp.get_video_info(video_id)

                    # 检查日期（date_limit <= 0 表示不限制时间）
                    video_date_str = detail.get('upload_date', '')
                    if video_date_str and date_limit > 0 and date_limit < 3650:
                        # 解析视频上传日期
                        try:
                            date_str = video_date_str.replace('-', '')
                            if len(date_str) >= 8:
                                video_date = datetime.strptime(date_str[:8], '%Y%m%d')
                                days_ago = (today - video_date).days

                                if days_ago > date_limit:
                                    skipped_old += 1
                                    self.logger.debug(f"跳过旧视频 {video_id}，上传于 {days_ago} 天前")
                                    time.sleep(0.5)
                                    continue
                        except ValueError:
                            pass  # 日期解析失败，保留视频

                    # 转换为标准格式
                    video = self._convert_to_standard_format(detail, keyword)
                    videos_with_details.append(video)

                    # 进度日志
                    if processed % 5 == 0:
                        self.logger.info(f"已处理 {processed} 个，有效 {len(videos_with_details)} 个，跳过旧视频 {skipped_old} 个")

                    # 速率限制
                    time.sleep(1)

                except YtDlpError as e:
                    self.logger.warning(f"获取视频 {result.get('id')} 详情失败: {e}")
                    continue

            self.logger.info(f"搜索完成: 处理 {processed} 个，有效 {len(videos_with_details)} 个，跳过旧视频 {skipped_old} 个")
            return videos_with_details

        except YtDlpError as e:
            self.logger.error(f"yt-dlp 搜索失败: {e}")
            raise

    def _convert_to_standard_format(
        self,
        ytdlp_data: Dict[str, Any],
        keyword: str
    ) -> Dict[str, Any]:
        """
        转换 yt-dlp 数据为标准 CompetitorVideo 格式

        符合 data.spec.md CompetitorVideo 实体
        """
        return {
            'id': ytdlp_data.get('youtube_id', ''),
            'youtube_id': ytdlp_data.get('youtube_id', ''),
            'title': ytdlp_data.get('title', ''),
            'description': ytdlp_data.get('description', ''),
            'channel': ytdlp_data.get('channel_name', ''),
            'channel_id': ytdlp_data.get('channel_id', ''),
            'view_count': ytdlp_data.get('view_count', 0),
            'like_count': ytdlp_data.get('like_count', 0),
            'comment_count': ytdlp_data.get('comment_count', 0),
            'duration': ytdlp_data.get('duration', 0),
            'upload_date': ytdlp_data.get('upload_date'),
            'publish_date': ytdlp_data.get('upload_date'),
            'tags': ytdlp_data.get('tags', []),
            'thumbnail_url': ytdlp_data.get('thumbnail_url', ''),
            'url': ytdlp_data.get('url', ''),
            'keyword_source': keyword,
            'collected_at': ytdlp_data.get('collected_at', datetime.now().isoformat())
        }

    def _search_mock(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """生成模拟视频数据（当 yt-dlp 不可用时使用）"""
        self.logger.warning("使用模拟数据（yt-dlp 不可用）")

        videos = []
        for i in range(min(max_results, 20)):
            video = {
                'id': f'mock_{keyword[:5]}_{i:03d}',
                'youtube_id': f'mock_{i:06d}',
                'title': f'{keyword}相关视频标题_{i+1}',
                'description': f'这是关于{keyword}的详细描述...',
                'channel': f'{keyword}频道_{i % 5}',
                'channel_id': f'UC_mock_{i % 5}',
                'view_count': 10000 + i * 1000,
                'like_count': 500 + i * 50,
                'comment_count': 50 + i * 5,
                'duration': 300 + i * 60,
                'upload_date': '2025-11-01',
                'publish_date': '2025-11-01',
                'tags': [keyword, f'{keyword}教程', f'{keyword}技巧'],
                'keyword_source': keyword,
                'collected_at': datetime.now().isoformat()
            }
            videos.append(video)
        return videos

    def collect_videos(
        self,
        theme: str,
        max_videos: int = 100,
        time_range: str = "month",
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        收集视频数据（支持多关键词扩展和时间筛选）

        Args:
            theme: 调研主题
            max_videos: 最大视频数量
            time_range: 时间范围 (week/month/quarter/year)
            days: 最近多少天内的视频（优先级高于 time_range）

        Returns:
            视频数据列表
        """
        # 计算时间范围描述
        if days is not None:
            time_desc = f"{days}天内"
        else:
            time_desc = {'week': '一周内', 'month': '一个月内', 'quarter': '三个月内', 'year': '一年内'}.get(time_range, '一个月内')

        self.logger.info(f"开始收集主题'{theme}'的视频数据，目标{max_videos}个，时间范围：{time_desc}")

        # 生成扩展关键词
        keywords = self._generate_keywords(theme)
        self.logger.info(f"生成了{len(keywords)}个扩展关键词: {keywords}")

        all_videos = []
        collected_per_keyword = max(max_videos // len(keywords), 10)

        for keyword in keywords:
            self.logger.info(f"正在收集关键词：{keyword}")

            try:
                videos = self.search_videos(
                    keyword,
                    collected_per_keyword,
                    time_range=time_range,
                    days=days
                )
                all_videos.extend(videos)
            except Exception as e:
                self.logger.error(f"收集关键词 {keyword} 失败: {e}")
                continue

            # 避免请求过快
            time.sleep(2)

        # 去重
        unique_videos = self._deduplicate_videos(all_videos)

        self.logger.info(f"收集完成，共获得{len(unique_videos)}个去重后的视频")

        return unique_videos[:max_videos]

    def _generate_keywords(self, theme: str) -> List[str]:
        """
        生成扩展关键词（基于真实数据源）

        优先级：
        1. YouTube 搜索建议（长尾词）
        2. 频道视频标签
        3. 默认扩展
        """
        keywords = [theme]

        # 1. 获取 YouTube 搜索建议
        try:
            suggestions = self.get_search_suggestions(theme, max_suggestions=10)
            if suggestions:
                keywords.extend(suggestions[:5])
                self.logger.info(f"从搜索建议获取 {len(suggestions[:5])} 个关键词")
        except Exception as e:
            self.logger.warning(f"获取搜索建议失败: {e}")

        # 去重
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)

        return unique_keywords[:8]  # 最多返回 8 个关键词

    def get_search_suggestions(
        self,
        query: str,
        max_suggestions: int = 10,
        language: str = 'zh'
    ) -> List[str]:
        """
        获取 YouTube 搜索建议（长尾词）

        使用 YouTube 的搜索自动补全 API 获取用户真实搜索的关键词

        Args:
            query: 基础搜索词
            max_suggestions: 最大建议数
            language: 语言代码

        Returns:
            搜索建议列表
        """
        self.logger.info(f"获取搜索建议: {query}")

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

                    self.logger.info(f"获取到 {len(suggestions)} 个搜索建议")
                    return suggestions[:max_suggestions]

        except Exception as e:
            self.logger.warning(f"获取搜索建议失败: {e}")

        return []

    def extract_tags_from_channel(
        self,
        channel_id: str,
        max_videos: int = 20,
        top_n: int = 20
    ) -> List[str]:
        """
        从频道视频中提取高频标签

        分析竞品频道的视频标签，找出他们常用的关键词

        Args:
            channel_id: YouTube 频道 ID
            max_videos: 分析的视频数量
            top_n: 返回 top N 个高频标签

        Returns:
            高频标签列表（按频率排序）
        """
        if not self.use_ytdlp:
            self.logger.warning("yt-dlp 不可用，无法提取标签")
            return []

        self.logger.info(f"从频道 {channel_id} 提取标签")

        try:
            # 获取频道视频列表
            videos = self.ytdlp.get_channel_videos(channel_id, max_videos)

            if not videos:
                self.logger.warning("未获取到频道视频")
                return []

            # 收集所有标签
            all_tags: List[str] = []

            for video in videos[:max_videos]:
                video_id = video.get('id')
                if not video_id:
                    continue

                try:
                    # 获取视频详情以获取标签
                    detail = self.ytdlp.get_video_info(video_id)
                    tags = detail.get('tags', [])
                    if tags:
                        all_tags.extend(tags)

                    # 速率限制
                    time.sleep(1)

                except Exception as e:
                    self.logger.debug(f"获取视频 {video_id} 标签失败: {e}")
                    continue

            # 统计标签频率
            tag_counts = Counter(all_tags)

            # 返回高频标签
            top_tags = [tag for tag, _ in tag_counts.most_common(top_n)]

            self.logger.info(f"从 {len(videos)} 个视频中提取了 {len(top_tags)} 个高频标签")
            return top_tags

        except Exception as e:
            self.logger.error(f"提取频道标签失败: {e}")
            return []

    def collect_keywords_from_competitors(
        self,
        channel_ids: List[str],
        theme: str,
        max_keywords: int = 30
    ) -> List[str]:
        """
        从多个竞品频道收集关键词

        综合多个数据源获取真实的关键词：
        1. 搜索建议长尾词
        2. 竞品频道视频标签

        Args:
            channel_ids: 竞品频道 ID 列表
            theme: 主题（用于获取搜索建议）
            max_keywords: 最大关键词数

        Returns:
            综合关键词列表（已去重）
        """
        self.logger.info(f"从 {len(channel_ids)} 个竞品频道收集关键词")

        all_keywords: Set[str] = set()
        all_keywords.add(theme)

        # 1. 获取搜索建议
        suggestions = self.get_search_suggestions(theme, max_suggestions=15)
        all_keywords.update(suggestions)

        # 2. 从每个频道提取标签
        for channel_id in channel_ids:
            try:
                tags = self.extract_tags_from_channel(channel_id, max_videos=10, top_n=10)
                all_keywords.update(tags)
            except Exception as e:
                self.logger.warning(f"从频道 {channel_id} 提取标签失败: {e}")
                continue

            # 频道间速率限制
            time.sleep(2)

        # 转为列表并限制数量
        keyword_list = list(all_keywords)

        self.logger.info(f"共收集到 {len(keyword_list)} 个关键词")
        return keyword_list[:max_keywords]

    def _deduplicate_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复视频"""
        seen_ids = set()
        unique_videos = []

        for video in videos:
            video_id = video.get('id') or video.get('youtube_id')
            if video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                unique_videos.append(video)

        return unique_videos

    def filter_quality_videos(
        self,
        videos: List[Dict[str, Any]],
        min_views: Optional[int] = None,
        min_likes: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        筛选高质量视频

        符合 api.spec.md 3.1 DataCollector.filter_quality_videos 接口

        Args:
            videos: 视频列表
            min_views: 最小播放量 (默认从配置读取)
            min_likes: 最小点赞数 (默认从配置读取)
            max_duration: 最大时长秒数 (默认从配置读取)

        Returns:
            筛选后的视频列表
        """
        min_views = min_views or self.min_views
        min_likes = min_likes or self.min_likes
        max_duration = max_duration or self.max_duration

        filtered = []

        for video in videos:
            view_count = video.get('view_count') or 0
            like_count = video.get('like_count') or 0
            duration = video.get('duration') or 0

            # 应用筛选条件
            if view_count >= min_views and like_count >= min_likes:
                if max_duration == 0 or duration <= max_duration:
                    filtered.append(video)

        self.logger.info(
            f"质量筛选：从{len(videos)}个视频中筛选出{len(filtered)}个高质量视频 "
            f"(播放>={min_views}, 点赞>={min_likes}, 时长<={max_duration}秒)"
        )
        return filtered

    def save_videos(
        self,
        videos: List[Dict[str, Any]],
        output_path: Path
    ) -> None:
        """
        保存视频数据

        符合 api.spec.md 3.1 DataCollector.save_videos 接口

        Args:
            videos: 视频列表
            output_path: 输出路径 (支持 .json 和 .csv)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix.lower() == '.csv':
            self._save_as_csv(videos, output_path)
        else:
            self._save_as_json(videos, output_path)

        self.logger.info(f"视频数据已保存到：{output_path}")

    def _save_as_json(self, videos: List[Dict[str, Any]], output_path: Path):
        """保存为 JSON 格式"""
        data = {
            'collected_at': datetime.now().isoformat(),
            'count': len(videos),
            'videos': videos
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_as_csv(self, videos: List[Dict[str, Any]], output_path: Path):
        """保存为 CSV 格式"""
        import csv

        if not videos:
            return

        # 确定字段
        fields = [
            'id', 'youtube_id', 'title', 'channel', 'view_count',
            'like_count', 'comment_count', 'duration', 'upload_date',
            'tags', 'keyword_source', 'url'
        ]

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()

            for video in videos:
                # 处理列表字段
                row = video.copy()
                if isinstance(row.get('tags'), list):
                    row['tags'] = ','.join(row['tags'])
                writer.writerow(row)

    def load_videos(self, input_path: Path) -> List[Dict[str, Any]]:
        """
        加载视频数据

        Args:
            input_path: 输入文件路径

        Returns:
            视频列表
        """
        input_path = Path(input_path)

        if not input_path.exists():
            self.logger.warning(f"文件不存在: {input_path}")
            return []

        if input_path.suffix.lower() == '.csv':
            return self._load_from_csv(input_path)
        else:
            return self._load_from_json(input_path)

    def _load_from_json(self, input_path: Path) -> List[Dict[str, Any]]:
        """从 JSON 加载"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 支持两种格式：纯列表或带元数据的对象
        if isinstance(data, list):
            videos = data
        else:
            videos = data.get('videos', [])

        self.logger.info(f"从 {input_path} 加载了 {len(videos)} 个视频数据")
        return videos

    def _load_from_csv(self, input_path: Path) -> List[Dict[str, Any]]:
        """从 CSV 加载"""
        import csv

        videos = []
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 处理数值字段
                for field in ['view_count', 'like_count', 'comment_count', 'duration']:
                    if row.get(field):
                        try:
                            row[field] = int(row[field])
                        except ValueError:
                            row[field] = 0

                # 处理标签字段
                if row.get('tags') and isinstance(row['tags'], str):
                    row['tags'] = row['tags'].split(',')

                videos.append(row)

        self.logger.info(f"从 {input_path} 加载了 {len(videos)} 个视频数据")
        return videos

    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个视频详细信息

        Args:
            video_id: YouTube 视频 ID

        Returns:
            视频详细信息
        """
        if not self.use_ytdlp:
            self.logger.warning("yt-dlp 不可用")
            return None

        try:
            return self.ytdlp.get_video_info(video_id)
        except YtDlpError as e:
            self.logger.error(f"获取视频 {video_id} 详情失败: {e}")
            return None


# 便捷函数
def collect_and_filter(
    keyword: str,
    max_results: int = 50,
    min_views: int = 1000
) -> List[Dict[str, Any]]:
    """
    便捷函数：收集并筛选视频

    Args:
        keyword: 搜索关键词
        max_results: 最大结果数
        min_views: 最小播放量

    Returns:
        筛选后的视频列表
    """
    collector = DataCollector()
    videos = collector.search_videos(keyword, max_results)
    return collector.filter_quality_videos(videos, min_views=min_views)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10

        print(f"搜索: {keyword}, 最大结果: {max_results}")

        collector = DataCollector()
        videos = collector.search_videos(keyword, max_results)

        print(f"\n找到 {len(videos)} 个视频:")
        for i, v in enumerate(videos[:10], 1):
            print(f"  {i}. {v.get('title', 'N/A')}")
            print(f"     播放: {v.get('view_count', 'N/A')}, 时长: {v.get('duration', 'N/A')}秒")
            print()

        # 筛选
        filtered = collector.filter_quality_videos(videos)
        print(f"筛选后: {len(filtered)} 个高质量视频")
    else:
        print("用法: python data_collector.py <搜索关键词> [最大结果数]")
