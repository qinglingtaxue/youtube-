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
- 两阶段采集（快速搜索 + 按需详情）
- 数据库持久化和去重
- 筛选高质量视频
- 支持大规模采集（1000+视频）

采集策略（参考 VidIQ/TubeBuddy 最佳实践）：
- 阶段1：快速搜索，获取基础信息（0.5秒/个）
- 阶段2：对高质量视频获取详情（4秒/个）
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.logger import setup_logger
from src.shared.config import get_config, Config
from src.shared.models import CompetitorVideo
from src.shared.repositories import CompetitorVideoRepository
from .yt_dlp_client import YtDlpClient, YtDlpError, expand_keywords_from_youtube


class DataCollector:
    """
    数据收集器

    基于 api.spec.md 3.1 DataCollector 接口实现

    支持两阶段采集：
    - 阶段1：快速搜索（search_videos_fast）
    - 阶段2：详情获取（enrich_video_details）
    """

    def __init__(self, config: Optional[Config] = None, db_path: Optional[str] = None):
        """
        初始化数据收集器

        Args:
            config: 配置对象 (可选)
            db_path: 数据库路径 (可选)
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

        # 初始化 Repository（数据库）
        self.repository = CompetitorVideoRepository(db_path)

    def search_videos(
        self,
        keyword: str,
        max_results: int = 50,
        region: str = "US",
        time_range: str = "month"
    ) -> List[Dict[str, Any]]:
        """
        搜索视频

        符合 api.spec.md 3.1 DataCollector.search_videos 接口

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            region: 目标地区 (ISO 3166-1)
            time_range: 时间范围
                - 'hour': 过去1小时
                - 'today'/'day': 24小时内
                - 'week': 7天内
                - 'month': 30天内
                - 'two_months': 60天内 ★ 推荐
                - 'quarter': 3个月内（90天）
                - 'year': 今年

        Returns:
            竞品视频列表

        Raises:
            Exception: 搜索失败
        """
        self.logger.info(f"搜索视频: keyword={keyword}, max_results={max_results}, region={region}, time_range={time_range}")

        if self.use_ytdlp:
            return self._search_with_ytdlp(keyword, max_results, time_range)
        else:
            return self._search_mock(keyword, max_results)

    def _search_with_ytdlp(
        self,
        keyword: str,
        max_results: int,
        time_range: str = "month"
    ) -> List[Dict[str, Any]]:
        """使用 yt-dlp 搜索视频"""
        try:
            # 搜索获取视频列表（带时间过滤）
            search_results = self.ytdlp.search_videos(keyword, max_results, time_range=time_range)

            if not search_results:
                self.logger.warning("搜索未返回结果")
                return []

            # 获取详细信息（仅获取部分以避免请求过多）
            videos_with_details = []
            detail_limit = min(len(search_results), 20)  # 最多获取20个详情

            self.logger.info(f"获取 {detail_limit} 个视频的详细信息...")

            for i, result in enumerate(search_results[:detail_limit]):
                try:
                    video_id = result.get('id')
                    if not video_id:
                        continue

                    # 获取详细信息
                    detail = self.ytdlp.get_video_info(video_id)

                    # 转换为标准格式
                    video = self._convert_to_standard_format(detail, keyword)
                    videos_with_details.append(video)

                    # 进度日志
                    if (i + 1) % 5 == 0:
                        self.logger.info(f"已获取 {i + 1}/{detail_limit} 个视频详情")

                    # 速率限制
                    time.sleep(1)

                except YtDlpError as e:
                    self.logger.warning(f"获取视频 {result.get('id')} 详情失败: {e}")
                    continue

            # 对于超出详情获取限制的视频，使用搜索结果基本信息
            for result in search_results[detail_limit:]:
                video = {
                    'id': result.get('id', ''),
                    'youtube_id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'channel': result.get('channel', ''),
                    'view_count': result.get('view_count'),
                    'duration': result.get('duration'),
                    'upload_date': result.get('upload_date'),
                    'keyword_source': keyword,
                    'collected_at': datetime.now().isoformat()
                }
                videos_with_details.append(video)

            self.logger.info(f"搜索完成，共获取 {len(videos_with_details)} 个视频")
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
        max_videos: int = 100
    ) -> List[Dict[str, Any]]:
        """
        收集视频数据（支持多关键词扩展）

        Args:
            theme: 调研主题
            max_videos: 最大视频数量

        Returns:
            视频数据列表
        """
        self.logger.info(f"开始收集主题'{theme}'的视频数据，目标{max_videos}个")

        # 生成扩展关键词
        keywords = self._generate_keywords(theme)
        self.logger.info(f"生成了{len(keywords)}个扩展关键词: {keywords}")

        all_videos = []
        collected_per_keyword = max(max_videos // len(keywords), 10)

        for keyword in keywords:
            self.logger.info(f"正在收集关键词：{keyword}")

            try:
                videos = self.search_videos(keyword, collected_per_keyword)
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

    def _generate_keywords(self, theme: str, max_keywords: int = 15) -> List[str]:
        """
        生成扩展关键词

        策略（按优先级）：
        1. 首先尝试从 YouTube 搜索建议获取真实用户搜索的关键词
        2. 如果失败，使用预定义映射
        3. 最后使用默认扩展

        Args:
            theme: 主题关键词
            max_keywords: 最大关键词数量

        Returns:
            扩展后的关键词列表
        """
        self.logger.info(f"开始扩展关键词: {theme}")

        # 1. 首选：从 YouTube 搜索建议获取真实关键词
        try:
            youtube_keywords = expand_keywords_from_youtube(theme, max_keywords)
            if len(youtube_keywords) >= 5:
                self.logger.info(f"使用 YouTube 搜索建议: {youtube_keywords}")
                return youtube_keywords
        except Exception as e:
            self.logger.warning(f"获取 YouTube 搜索建议失败: {e}")

        # 2. 备选：预定义关键词映射（更丰富的映射）
        keyword_mappings = {
            # 养生相关（更全面的映射）
            '养生': ['养生', '中医养生', '健康养生', '养生堂', '养生食谱', '老年养生',
                    '养生功法', '养生茶', '四季养生', '经络养生', '养生之道'],
            '老人养生': ['中医养生', '健康科普', '长寿秘诀', '保健方法', '养生误区',
                       '老年健康', '养生堂', '经络养生'],
            '健康': ['健康养生', '健康饮食', '健康科普', '健康生活', '亚健康调理',
                    '健康小知识', '养生保健'],

            # AI 相关
            'AI工具': ['AI工具', '人工智能', 'ChatGPT', 'AI应用', '机器学习', 'AI教程',
                      'AI绘画', 'AI写作', 'AI助手', 'Claude', 'Midjourney'],
            'AI': ['AI工具', 'AI教程', 'AI应用', '人工智能', 'ChatGPT', 'AI绘画'],

            # 美食相关
            '美食': ['美食制作', '家常菜', '烹饪技巧', '美食教程', '地方菜', '甜品制作',
                    '美食探店', '美食vlog', '快手菜', '减脂餐'],
            '美食制作': ['家常菜', '烹饪技巧', '美食教程', '地方菜', '甜品制作'],

            # 健身相关
            '健身': ['健身教程', '减肥健身', '居家健身', '瑜伽教程', '力量训练',
                    '有氧运动', '减脂塑形', '健身入门', '帕梅拉'],
            '健身教程': ['减肥健身', '居家健身', '瑜伽教程', '力量训练', '有氧运动'],

            # 编程相关
            'Python': ['Python教程', 'Python入门', 'Python项目', 'Python编程',
                      'Python爬虫', 'Python数据分析', 'Python自动化'],
            '编程': ['编程入门', 'Python教程', 'JavaScript', '前端开发', '后端开发'],

            # 自媒体相关
            'YouTube': ['YouTube运营', 'YouTube涨粉', 'YouTube变现', 'YouTube教程',
                       'YouTube SEO', 'YouTube算法', '油管运营'],
            '自媒体': ['自媒体运营', '短视频', '涨粉技巧', '内容创作', '自媒体变现'],

            # 旅游相关
            '旅游': ['旅游vlog', '旅行攻略', '自驾游', '穷游', '背包客', '旅游推荐',
                    '国内旅游', '出境游', '旅行日记'],
            '旅游vlog': ['旅游vlog', '旅行攻略', '自驾游', '旅行日记', '城市探索'],

            # 理财相关
            '理财': ['投资理财', '基金入门', '股票教程', '理财知识', '财务自由',
                    '被动收入', '副业赚钱'],
            '投资': ['投资理财', '股票分析', '基金定投', '价值投资', '投资入门'],

            # 学习相关
            '英语': ['英语学习', '英语口语', '英语听力', '英语语法', '雅思托福',
                    '英语词汇', '英语发音'],
            '学习': ['学习方法', '高效学习', '考试技巧', '读书笔记', '知识管理'],
        }

        # 匹配预定义关键词（精确匹配优先，然后模糊匹配）
        theme_lower = theme.lower()

        # 精确匹配
        if theme in keyword_mappings:
            return keyword_mappings[theme][:max_keywords]

        # 模糊匹配
        for key, values in keyword_mappings.items():
            if key.lower() in theme_lower or theme_lower in key.lower():
                self.logger.info(f"使用预定义映射 ({key}): {values[:max_keywords]}")
                return values[:max_keywords]

        # 3. 最后：默认扩展（更丰富）
        default_suffixes = ['教程', '入门', '技巧', '方法', '推荐', '攻略',
                           '2025', '怎么', '如何', '最新']
        default_keywords = [theme]
        for suffix in default_suffixes:
            default_keywords.append(f'{theme}{suffix}')
            if len(default_keywords) >= max_keywords:
                break

        self.logger.info(f"使用默认扩展: {default_keywords}")
        return default_keywords

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

    # ============================================================
    # 两阶段采集（大规模采集优化）
    # ============================================================

    def search_videos_parallel(
        self,
        keyword: str,
        max_per_strategy: int = 50,
        time_range: str = "month",
        save_to_db: bool = True,
        theme: str = None
    ) -> Tuple[int, int]:
        """
        并行搜索：使用多种排序策略同时搜索同一关键词

        策略组合（确保不遗漏高质量视频）：
        1. view_count: 按播放量排序（确保 Top 100）★ 最重要
        2. relevance: 按相关性排序（默认，覆盖最全）
        3. date: 按发布日期排序（发现新视频）

        Args:
            keyword: 搜索关键词
            max_per_strategy: 每种策略的最大结果数
            time_range: 时间范围
            save_to_db: 是否保存到数据库
            theme: 主题分类（如"养生"、"科技"）

        Returns:
            (new_count, skip_count) 新增数量和跳过数量
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        self.logger.info(f"[并行搜索] keyword={keyword}, 每策略={max_per_strategy}, time_range={time_range}")

        if not self.use_ytdlp:
            self.logger.warning("yt-dlp 不可用")
            return 0, 0

        # 搜索策略：按播放量 > 相关性 > 日期
        strategies = [
            ('view_count', '按播放量'),
            ('relevance', '按相关性'),
            ('date', '按日期'),
        ]

        all_results = []

        def search_with_strategy(sort_by: str, desc: str):
            """执行单个策略的搜索"""
            try:
                self.logger.info(f"  [{desc}] 开始搜索...")
                results = self.ytdlp.search_videos(
                    keyword,
                    max_per_strategy,
                    sort_by=sort_by,
                    time_range=time_range
                )
                self.logger.info(f"  [{desc}] 获得 {len(results)} 个结果")
                return results
            except YtDlpError as e:
                self.logger.warning(f"  [{desc}] 搜索失败: {e}")
                return []

        # 并行执行搜索
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(search_with_strategy, sort_by, desc): (sort_by, desc)
                for sort_by, desc in strategies
            }

            for future in as_completed(futures):
                sort_by, desc = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    self.logger.error(f"  [{desc}] 异常: {e}")

        if not all_results:
            self.logger.warning("[并行搜索] 所有策略均无结果")
            return 0, 0

        # 去重（同一视频可能被多种策略搜到）
        seen_ids = set()
        unique_videos = []
        for result in all_results:
            video_id = result.get('id')
            if video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                video = CompetitorVideo.from_ytdlp_search(result, keyword, theme=theme)
                if video.youtube_id:
                    unique_videos.append(video)

        self.logger.info(f"[并行搜索] 去重后: {len(unique_videos)} 个唯一视频 (原始 {len(all_results)})")

        if not save_to_db:
            return len(unique_videos), 0

        # 批量去重检查（与数据库）
        youtube_ids = [v.youtube_id for v in unique_videos]
        existing_ids = self.repository.exists_batch(youtube_ids)

        # 过滤已存在的视频
        new_videos = [v for v in unique_videos if v.youtube_id not in existing_ids]
        skip_count = len(unique_videos) - len(new_videos)

        if new_videos:
            inserted, updated = self.repository.save_batch(new_videos)
            self.logger.info(f"[并行搜索] 完成: 新增 {inserted}, 跳过 {skip_count}")
            return inserted, skip_count
        else:
            self.logger.info(f"[并行搜索] 完成: 全部已存在，跳过 {skip_count}")
            return 0, skip_count

    def search_videos_fast(
        self,
        keyword: str,
        max_results: int = 100,
        save_to_db: bool = True,
        time_range: str = "month"
    ) -> Tuple[int, int]:
        """
        阶段1：快速搜索（仅获取基础信息）

        使用 --flat-playlist 模式，不获取详情，速度快
        自动去重并保存到数据库

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            save_to_db: 是否保存到数据库
            time_range: 时间范围 (hour/today/week/month/quarter/year)

        Returns:
            (new_count, skip_count) 新增数量和跳过数量
        """
        self.logger.info(f"[阶段1] 快速搜索: keyword={keyword}, max_results={max_results}, time_range={time_range}")

        if not self.use_ytdlp:
            self.logger.warning("yt-dlp 不可用")
            return 0, 0

        try:
            # 搜索获取基础信息（带时间过滤）
            search_results = self.ytdlp.search_videos(keyword, max_results, time_range=time_range)

            if not search_results:
                self.logger.warning("搜索未返回结果")
                return 0, 0

            # 转换为 CompetitorVideo 模型
            videos = []
            for result in search_results:
                video = CompetitorVideo.from_ytdlp_search(result, keyword)
                if video.youtube_id:
                    videos.append(video)

            self.logger.info(f"搜索获得 {len(videos)} 个视频")

            if not save_to_db:
                return len(videos), 0

            # 批量去重检查
            youtube_ids = [v.youtube_id for v in videos]
            existing_ids = self.repository.exists_batch(youtube_ids)

            # 过滤已存在的视频
            new_videos = [v for v in videos if v.youtube_id not in existing_ids]
            skip_count = len(videos) - len(new_videos)

            if new_videos:
                inserted, updated = self.repository.save_batch(new_videos)
                self.logger.info(f"[阶段1] 完成: 新增 {inserted}, 跳过 {skip_count}")
                return inserted, skip_count
            else:
                self.logger.info(f"[阶段1] 完成: 全部已存在，跳过 {skip_count}")
                return 0, skip_count

        except YtDlpError as e:
            self.logger.error(f"快速搜索失败: {e}")
            return 0, 0

    def enrich_video_details(
        self,
        min_views: int = 10000,
        limit: int = 100,
        on_progress: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[int, int]:
        """
        阶段2：获取高质量视频的详情

        从数据库中找出没有详情的高播放量视频，获取详情

        Args:
            min_views: 最小播放量阈值（只对高播放量视频获取详情）
            limit: 最大获取数量
            on_progress: 进度回调 (current, total, youtube_id)

        Returns:
            (success_count, fail_count)
        """
        self.logger.info(f"[阶段2] 获取详情: min_views={min_views}, limit={limit}")

        if not self.use_ytdlp:
            self.logger.warning("yt-dlp 不可用")
            return 0, 0

        # 查找需要获取详情的视频
        videos_need_details = self.repository.find_without_details(min_views, limit)

        if not videos_need_details:
            self.logger.info("[阶段2] 没有需要获取详情的视频")
            return 0, 0

        self.logger.info(f"[阶段2] 找到 {len(videos_need_details)} 个视频需要获取详情")

        success_count = 0
        fail_count = 0

        for i, video in enumerate(videos_need_details):
            try:
                if on_progress:
                    on_progress(i + 1, len(videos_need_details), video.youtube_id)

                # 获取详情
                details = self.ytdlp.get_video_info(video.youtube_id)

                # 转换为模型（保留原有的 theme）
                enriched = CompetitorVideo.from_ytdlp_details(details, video.keyword_source, theme=getattr(video, 'theme', None))

                # 更新数据库
                self.repository.update_details(enriched)
                success_count += 1

                # 进度日志
                if (i + 1) % 10 == 0:
                    self.logger.info(f"[阶段2] 进度: {i + 1}/{len(videos_need_details)}")

                # 速率限制
                time.sleep(1)

            except YtDlpError as e:
                self.logger.warning(f"获取视频 {video.youtube_id} 详情失败: {e}")
                fail_count += 1

        self.logger.info(f"[阶段2] 完成: 成功 {success_count}, 失败 {fail_count}")
        return success_count, fail_count

    def collect_large_scale(
        self,
        theme: str,
        target_count: int = 500,
        detail_min_views: int = 10000,
        detail_limit: int = 200,
        time_range: str = "month",
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        大规模采集（优化策略：先搜索再筛选 Top 100 获取详情）

        采集策略：
        1. 阶段1（快速搜索）：大量搜索获取基础信息（200-500个）
        2. 阶段2（筛选 Top 100）：按播放量排序，对 Top 100 获取完整详情
        3. 阶段3（扩展数据）：100 以后的视频保存基础信息，后台慢慢补充

        Args:
            theme: 调研主题
            target_count: 目标视频数量
            detail_min_views: 获取详情的最小播放量
            detail_limit: 获取详情的数量上限
            time_range: 时间范围 (hour/today/week/month/quarter/year)
            on_progress: 进度回调 (stage, current, total)

        Returns:
            采集统计信息
        """
        self.logger.info(f"=== 大规模采集开始（先搜索再筛选 Top 100）===")
        self.logger.info(f"主题: {theme}, 目标: {target_count}, 时间范围: {time_range}")

        start_time = time.time()

        # 生成扩展关键词
        max_keywords = min(15, max(5, target_count // 30))
        keywords = self._generate_keywords(theme, max_keywords=max_keywords)

        # 每个关键词每种策略搜索数量
        # 并行搜索会使用 3 种策略，总数约为 per_keyword * 3
        per_keyword = max(target_count // len(keywords) // 2, 30)

        self.logger.info(f"关键词: {keywords}")
        self.logger.info(f"每关键词每策略搜索: {per_keyword} 个（3种策略并行）")

        # ============================================================
        # 阶段1：并行搜索所有关键词（多策略 + 多关键词并行）
        # ============================================================
        if on_progress:
            on_progress("search", 0, len(keywords))

        self.logger.info(f"[阶段1-并行搜索] 对 {len(keywords)} 个关键词并行采集...")

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from threading import Lock

        total_new = 0
        total_skip = 0
        completed_count = 0
        result_lock = Lock()

        # 关键词并行数（10个任务同时进行）
        KEYWORD_WORKERS = min(10, len(keywords))

        def search_keyword(idx_keyword):
            """搜索单个关键词"""
            idx, kw = idx_keyword
            try:
                new, skip = self.search_videos_parallel(
                    kw,
                    max_per_strategy=per_keyword,
                    time_range=time_range,
                    theme=theme
                )
                return (idx, kw, new, skip, None)
            except Exception as e:
                return (idx, kw, 0, 0, str(e))

        with ThreadPoolExecutor(max_workers=KEYWORD_WORKERS) as executor:
            futures = {
                executor.submit(search_keyword, (i, kw)): (i, kw)
                for i, kw in enumerate(keywords)
            }

            for future in as_completed(futures):
                idx, kw, new, skip, error = future.result()

                with result_lock:
                    completed_count += 1
                    total_new += new
                    total_skip += skip

                    if error:
                        self.logger.warning(f"[{completed_count}/{len(keywords)}] ✗ {kw}: {error}")
                    else:
                        self.logger.info(f"[{completed_count}/{len(keywords)}] ✓ {kw}: +{new} 新, {skip} 跳过")

                    if on_progress:
                        on_progress("search", completed_count, len(keywords))

        self.logger.info(f"[阶段1-并行搜索] 完成: 新增 {total_new}, 跳过 {total_skip}")

        # ============================================================
        # 阶段2：筛选 Top 100 并获取完整详情
        # ============================================================
        RANKING_COUNT = 100  # 榜单需要的 Top 100 数据

        if on_progress:
            on_progress("detail", 0, RANKING_COUNT)

        self.logger.info(f"[阶段2-详情] 对 Top {RANKING_COUNT} 高播放量视频获取完整详情...")

        # 获取高播放量但没有详情的视频
        success, fail = self.enrich_video_details(
            min_views=detail_min_views,
            limit=RANKING_COUNT,
            on_progress=lambda c, t, vid: on_progress("detail", c, t) if on_progress else None
        )

        self.logger.info(f"[阶段2-详情] 完成: 成功 {success}, 失败 {fail}")

        total_ranking = success

        # 统计信息
        elapsed = time.time() - start_time
        stats = self.repository.get_statistics()

        result = {
            'theme': theme,
            'keywords': keywords,
            'search_phase': {
                'new_videos': total_new,
                'skipped': total_skip,
                'description': '快速搜索（获取基础信息：标题、播放量、频道名）'
            },
            'detail_phase': {
                'success': total_ranking,
                'failed': fail,
                'description': f'Top {RANKING_COUNT} 高播放量视频获取完整详情（发布日期、点赞数、评论数等）'
            },
            'database': stats,
            'elapsed_seconds': round(elapsed, 1),
        }

        self.logger.info(f"=== 大规模采集完成 ===")
        self.logger.info(f"搜索阶段: {total_new} 个新增, {total_skip} 个跳过")
        self.logger.info(f"详情阶段: Top {RANKING_COUNT} 中 {total_ranking} 个成功, {fail} 个失败")
        self.logger.info(f"总耗时: {elapsed:.1f} 秒")
        self.logger.info(f"数据库总量: {stats['total']}")

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return self.repository.get_statistics()

    def get_videos_from_db(
        self,
        theme: Optional[str] = None,
        keyword: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        keyword_like: Optional[str] = None,
        min_views: Optional[int] = None,
        has_details: Optional[bool] = None,
        limit: int = 100
    ) -> List[CompetitorVideo]:
        """
        从数据库获取视频

        Args:
            theme: 按主题精确筛选（如"养生"、"科技"）
            keyword: 按关键词精确筛选（单个）
            keywords: 按多个关键词筛选（列表，OR 关系）
            keyword_like: 按关键词模糊筛选（包含主题词的所有关键词）
            min_views: 最小播放量
            has_details: 是否有详情
            limit: 返回数量

        Returns:
            CompetitorVideo 列表
        """
        return self.repository.find_all(
            limit=limit,
            theme=theme,
            keyword=keyword,
            keywords=keywords,
            keyword_like=keyword_like,
            min_views=min_views,
            has_details=has_details
        )


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
