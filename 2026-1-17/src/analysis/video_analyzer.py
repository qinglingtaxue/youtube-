#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频数据分析引擎

参考业界实践（VidIQ、TubeBuddy、Social Blade）设计的全面分析框架：
1. 描述性统计 - 基础数据概览
2. 标题模式分析 - NLP分析标题特征
3. 内容模式分类 - 识别视频类型
4. 频道分析 - 头部频道、内容定位
5. 时长分析 - 最佳时长区间
6. 聚类分析 - 发现内容类别
7. 异常值检测 - 识别爆款和异常
8. 趋势分析 - 时间维度分析
9. 洞察生成 - 自动生成建议
"""

import re
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.logger import setup_logger
from src.shared.models import CompetitorVideo, PatternType
from src.shared.repositories import CompetitorVideoRepository


@dataclass
class AnalysisResult:
    """分析结果容器"""

    # 基础统计
    basic_stats: Dict[str, Any] = field(default_factory=dict)

    # 标题分析
    title_analysis: Dict[str, Any] = field(default_factory=dict)

    # 内容模式
    content_patterns: Dict[str, Any] = field(default_factory=dict)

    # 频道分析
    channel_analysis: Dict[str, Any] = field(default_factory=dict)

    # 时长分析
    duration_analysis: Dict[str, Any] = field(default_factory=dict)

    # 聚类结果
    clusters: Dict[str, Any] = field(default_factory=dict)

    # 异常值
    anomalies: Dict[str, Any] = field(default_factory=dict)

    # 趋势分析
    trends: Dict[str, Any] = field(default_factory=dict)

    # 洞察和建议
    insights: List[str] = field(default_factory=list)

    # 元数据
    generated_at: str = ""
    video_count: int = 0


class VideoAnalyzer:
    """
    视频数据分析引擎

    提供全面的竞品视频分析能力，包括：
    - 描述性统计
    - 标题模式识别
    - 内容分类
    - 频道分析
    - 异常检测
    - 趋势分析
    """

    # 标题模式关键词（参考 VidIQ 爆款标题研究）
    TITLE_PATTERNS = {
        'question': ['为什么', '如何', '怎么', '怎样', '什么', '哪些', '哪个', '是否', '能不能', '可以吗', '？'],
        'number': [r'\d+个', r'\d+种', r'\d+大', r'\d+招', r'\d+步', r'\d+天', r'\d+分钟', r'第\d+'],
        'emotion': ['震惊', '惊人', '神奇', '太厉害', '绝了', '必看', '必须', '一定要', '千万别', '后悔'],
        'authority': ['医生', '专家', '教授', '名医', '研究', '科学', '证明', '发现', '揭秘', '真相'],
        'urgency': ['立刻', '马上', '现在', '今天', '赶紧', '别等', '错过', '最后'],
        'contrast': ['vs', '对比', '区别', '不同', '比较', '更好', '最好', '最差'],
        'list': ['清单', '大全', '合集', '盘点', '总结', '整理'],
        'personal': ['我的', '亲身', '经历', '分享', '经验', '故事'],
    }

    # 内容模式关键词（基于 data.spec.md PatternType）
    CONTENT_PATTERNS = {
        PatternType.COGNITIVE_IMPACT: {
            'keywords': ['震惊', '惊人', '颠覆', '真相', '揭秘', '99%', '90%', '不知道', '想不到', '万万没想到'],
            'weight': 1.5,
        },
        PatternType.STORYTELLING: {
            'keywords': ['故事', '经历', '案例', '分享', '亲身', '我的', '记录', '一个人', '从此'],
            'weight': 1.3,
        },
        PatternType.KNOWLEDGE_SHARING: {
            'keywords': ['方法', '技巧', '教程', '步骤', '指南', '攻略', '干货', '详解', '科普', '讲解'],
            'weight': 1.2,
        },
        PatternType.INTERACTION_GUIDE: {
            'keywords': ['评论', '留言', '点赞', '关注', '订阅', '告诉我', '你觉得', '选哪个', '投票'],
            'weight': 1.1,
        },
    }

    # 时长区间定义（秒）
    DURATION_BUCKETS = [
        (0, 60, '< 1分钟'),
        (60, 180, '1-3分钟'),
        (180, 300, '3-5分钟'),
        (300, 600, '5-10分钟'),
        (600, 1200, '10-20分钟'),
        (1200, 3600, '20-60分钟'),
        (3600, float('inf'), '> 1小时'),
    ]

    def __init__(self, db_path: Optional[str] = None):
        """初始化分析器"""
        self.logger = setup_logger('video_analyzer')
        self.repo = CompetitorVideoRepository(db_path)
        self.videos: List[CompetitorVideo] = []

    def load_data(self, limit: int = 5000) -> int:
        """加载视频数据"""
        self.videos = self.repo.find_all(limit=limit)
        self.logger.info(f"加载了 {len(self.videos)} 个视频")
        return len(self.videos)

    def analyze(self) -> AnalysisResult:
        """执行完整分析"""
        if not self.videos:
            self.load_data()

        self.logger.info("开始全面分析...")
        result = AnalysisResult()
        result.video_count = len(self.videos)
        result.generated_at = datetime.now().isoformat()

        # 1. 基础统计
        self.logger.info("[1/8] 基础统计分析...")
        result.basic_stats = self._analyze_basic_stats()

        # 2. 标题分析
        self.logger.info("[2/8] 标题模式分析...")
        result.title_analysis = self._analyze_titles()

        # 3. 内容模式分类
        self.logger.info("[3/8] 内容模式分类...")
        result.content_patterns = self._classify_content_patterns()

        # 4. 频道分析
        self.logger.info("[4/8] 频道分析...")
        result.channel_analysis = self._analyze_channels()

        # 5. 时长分析
        self.logger.info("[5/8] 时长分析...")
        result.duration_analysis = self._analyze_duration()

        # 6. 聚类分析
        self.logger.info("[6/8] 聚类分析...")
        result.clusters = self._cluster_videos()

        # 7. 异常值检测
        self.logger.info("[7/8] 异常值检测...")
        result.anomalies = self._detect_anomalies()

        # 8. 趋势分析
        self.logger.info("[8/8] 趋势分析...")
        result.trends = self._analyze_trends()

        # 生成洞察
        self.logger.info("生成分析洞察...")
        result.insights = self._generate_insights(result)

        self.logger.info("分析完成！")
        return result

    # ============================================================
    # 1. 基础统计分析
    # ============================================================

    def _analyze_basic_stats(self) -> Dict[str, Any]:
        """基础统计分析"""
        view_counts = [v.view_count for v in self.videos]
        like_counts = [v.like_count for v in self.videos if v.has_details]
        comment_counts = [v.comment_count for v in self.videos if v.has_details]

        return {
            'total_videos': len(self.videos),
            'with_details': sum(1 for v in self.videos if v.has_details),
            'view_count': {
                'total': sum(view_counts),
                'mean': int(sum(view_counts) / len(view_counts)) if view_counts else 0,
                'median': self._median(view_counts),
                'max': max(view_counts) if view_counts else 0,
                'min': min(view_counts) if view_counts else 0,
                'std': self._std(view_counts),
                'percentiles': {
                    '25': self._percentile(view_counts, 25),
                    '50': self._percentile(view_counts, 50),
                    '75': self._percentile(view_counts, 75),
                    '90': self._percentile(view_counts, 90),
                    '95': self._percentile(view_counts, 95),
                    '99': self._percentile(view_counts, 99),
                },
            },
            'like_count': {
                'total': sum(like_counts),
                'mean': int(sum(like_counts) / len(like_counts)) if like_counts else 0,
                'median': self._median(like_counts),
            } if like_counts else {},
            'comment_count': {
                'total': sum(comment_counts),
                'mean': int(sum(comment_counts) / len(comment_counts)) if comment_counts else 0,
                'median': self._median(comment_counts),
            } if comment_counts else {},
            'engagement': self._analyze_engagement(),
            'keywords': self._count_keywords(),
        }

    def _analyze_engagement(self) -> Dict[str, Any]:
        """分析互动率"""
        detailed = [v for v in self.videos if v.has_details and v.view_count > 0]
        if not detailed:
            return {}

        engagement_rates = [v.engagement_rate for v in detailed]
        like_rates = [v.like_rate for v in detailed]

        return {
            'avg_engagement_rate': round(sum(engagement_rates) / len(engagement_rates) * 100, 3),
            'avg_like_rate': round(sum(like_rates) / len(like_rates) * 100, 3),
            'high_engagement_count': sum(1 for r in engagement_rates if r > 0.05),  # > 5%
        }

    def _count_keywords(self) -> Dict[str, int]:
        """统计来源关键词分布"""
        counter = Counter(v.keyword_source for v in self.videos if v.keyword_source)
        return dict(counter.most_common())

    # ============================================================
    # 2. 标题模式分析
    # ============================================================

    def _analyze_titles(self) -> Dict[str, Any]:
        """分析标题模式"""
        titles = [v.title for v in self.videos]

        # 标题长度统计
        lengths = [len(t) for t in titles]

        # 模式检测
        pattern_counts = {}
        pattern_examples = {}
        for pattern_name, keywords in self.TITLE_PATTERNS.items():
            matches = []
            for v in self.videos:
                for kw in keywords:
                    if isinstance(kw, str) and kw in v.title:
                        matches.append(v)
                        break
                    elif kw.startswith(r'\\') or '\\d' in kw:  # 正则
                        if re.search(kw, v.title):
                            matches.append(v)
                            break

            pattern_counts[pattern_name] = len(matches)
            # 取播放量最高的3个作为示例
            top_matches = sorted(matches, key=lambda x: x.view_count, reverse=True)[:3]
            pattern_examples[pattern_name] = [
                {'title': v.title, 'views': v.view_count_formatted, 'url': v.url}
                for v in top_matches
            ]

        # 高频词统计（简单分词）
        word_counter = Counter()
        for title in titles:
            # 简单的中文分词（按标点和空格分割 + 滑动窗口提取短语）
            words = re.findall(r'[\u4e00-\u9fa5]{2,6}', title)
            word_counter.update(words)

        return {
            'length': {
                'mean': int(sum(lengths) / len(lengths)) if lengths else 0,
                'median': self._median(lengths),
                'max': max(lengths) if lengths else 0,
                'min': min(lengths) if lengths else 0,
            },
            'patterns': {
                'counts': pattern_counts,
                'examples': pattern_examples,
            },
            'top_words': dict(word_counter.most_common(30)),
            'title_structures': self._analyze_title_structures(),
        }

    def _analyze_title_structures(self) -> Dict[str, Any]:
        """分析标题结构"""
        structures = {
            'starts_with_emoji': 0,
            'contains_emoji': 0,
            'contains_hashtag': 0,
            'contains_bracket': 0,  # 【】
            'ends_with_question': 0,
            'contains_number': 0,
            'contains_english': 0,
        }

        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]')

        for v in self.videos:
            title = v.title
            if emoji_pattern.match(title):
                structures['starts_with_emoji'] += 1
            if emoji_pattern.search(title):
                structures['contains_emoji'] += 1
            if '#' in title:
                structures['contains_hashtag'] += 1
            if '【' in title or '】' in title:
                structures['contains_bracket'] += 1
            if title.endswith('？') or title.endswith('?'):
                structures['ends_with_question'] += 1
            if re.search(r'\d', title):
                structures['contains_number'] += 1
            if re.search(r'[a-zA-Z]', title):
                structures['contains_english'] += 1

        # 转换为百分比
        total = len(self.videos)
        return {k: round(v / total * 100, 1) for k, v in structures.items()}

    # ============================================================
    # 3. 内容模式分类
    # ============================================================

    def _classify_content_patterns(self) -> Dict[str, Any]:
        """分类内容模式"""
        pattern_videos = {p: [] for p in PatternType}

        for v in self.videos:
            scores = {}
            for pattern_type, config in self.CONTENT_PATTERNS.items():
                score = 0
                for kw in config['keywords']:
                    if kw in v.title:
                        score += 1
                    if v.description and kw in v.description:
                        score += 0.5
                scores[pattern_type] = score * config['weight']

            # 分配到得分最高的模式
            if scores:
                best_pattern = max(scores, key=scores.get)
                if scores[best_pattern] > 0:
                    pattern_videos[best_pattern].append(v)
                else:
                    pattern_videos[PatternType.UNKNOWN].append(v)
            else:
                pattern_videos[PatternType.UNKNOWN].append(v)

        # 计算每个模式的统计
        result = {}
        for pattern_type, videos in pattern_videos.items():
            if not videos:
                continue

            view_counts = [v.view_count for v in videos]
            result[pattern_type.value] = {
                'count': len(videos),
                'percentage': round(len(videos) / len(self.videos) * 100, 1),
                'avg_views': int(sum(view_counts) / len(view_counts)),
                'total_views': sum(view_counts),
                'top_videos': [
                    {'title': v.title, 'views': v.view_count_formatted, 'url': v.url}
                    for v in sorted(videos, key=lambda x: x.view_count, reverse=True)[:5]
                ],
            }

        return result

    # ============================================================
    # 4. 频道分析
    # ============================================================

    def _analyze_channels(self) -> Dict[str, Any]:
        """分析频道"""
        channel_videos = defaultdict(list)
        for v in self.videos:
            if v.channel_name:
                channel_videos[v.channel_name].append(v)

        # 计算频道统计
        channel_stats = []
        for channel, videos in channel_videos.items():
            view_counts = [v.view_count for v in videos]
            channel_stats.append({
                'channel': channel,
                'video_count': len(videos),
                'total_views': sum(view_counts),
                'avg_views': int(sum(view_counts) / len(view_counts)),
                'max_views': max(view_counts),
                'top_video': max(videos, key=lambda x: x.view_count).title,
            })

        # 按总播放量排序
        channel_stats.sort(key=lambda x: x['total_views'], reverse=True)

        return {
            'total_channels': len(channel_videos),
            'top_by_views': channel_stats[:20],
            'top_by_count': sorted(channel_stats, key=lambda x: x['video_count'], reverse=True)[:20],
            'single_video_channels': sum(1 for c in channel_stats if c['video_count'] == 1),
            'prolific_channels': sum(1 for c in channel_stats if c['video_count'] >= 5),
        }

    # ============================================================
    # 5. 时长分析
    # ============================================================

    def _analyze_duration(self) -> Dict[str, Any]:
        """分析视频时长"""
        videos_with_duration = [v for v in self.videos if v.duration]
        if not videos_with_duration:
            return {}

        durations = [v.duration for v in videos_with_duration]

        # 时长区间统计
        bucket_stats = []
        for min_dur, max_dur, label in self.DURATION_BUCKETS:
            bucket_videos = [v for v in videos_with_duration
                          if min_dur <= v.duration < max_dur]
            if bucket_videos:
                view_counts = [v.view_count for v in bucket_videos]
                bucket_stats.append({
                    'label': label,
                    'count': len(bucket_videos),
                    'percentage': round(len(bucket_videos) / len(videos_with_duration) * 100, 1),
                    'avg_views': int(sum(view_counts) / len(view_counts)),
                    'total_views': sum(view_counts),
                })

        # 找最佳时长区间（平均播放量最高）
        best_bucket = max(bucket_stats, key=lambda x: x['avg_views']) if bucket_stats else None

        return {
            'total_with_duration': len(videos_with_duration),
            'stats': {
                'mean': int(sum(durations) / len(durations)),
                'median': self._median(durations),
                'max': max(durations),
                'min': min(durations),
            },
            'buckets': bucket_stats,
            'best_duration_range': best_bucket['label'] if best_bucket else None,
            'short_form_ratio': round(
                sum(1 for d in durations if d < 60) / len(durations) * 100, 1
            ),  # < 1分钟
        }

    # ============================================================
    # 6. 聚类分析
    # ============================================================

    def _cluster_videos(self) -> Dict[str, Any]:
        """基于标题相似度聚类（简化版，无需ML库）"""
        # 基于关键词的简单聚类
        topic_clusters = defaultdict(list)

        # 定义主题关键词
        topics = {
            '穴位按摩': ['穴位', '按摩', '按压', '推拿'],
            '饮食调理': ['吃什么', '食物', '饮食', '食疗', '水果', '蔬菜', '喝水'],
            '中药养生': ['中药', '中医', '草药', '药材', '汤', '茶'],
            '运动健身': ['运动', '锻炼', '走路', '散步', '健身', '太极'],
            '疾病防治': ['病', '症', '治疗', '预防', '改善', '调理'],
            '生活习惯': ['习惯', '作息', '睡眠', '早起', '熬夜'],
            '器官保健': ['肝', '肾', '心', '肺', '胃', '脾', '血管', '血压'],
            '长寿秘诀': ['长寿', '百岁', '老人', '长命', '秘诀'],
        }

        for v in self.videos:
            assigned = False
            for topic, keywords in topics.items():
                for kw in keywords:
                    if kw in v.title:
                        topic_clusters[topic].append(v)
                        assigned = True
                        break
                if assigned:
                    break
            if not assigned:
                topic_clusters['其他'].append(v)

        # 计算每个聚类的统计
        cluster_stats = []
        for topic, videos in topic_clusters.items():
            if not videos:
                continue
            view_counts = [v.view_count for v in videos]
            cluster_stats.append({
                'topic': topic,
                'count': len(videos),
                'percentage': round(len(videos) / len(self.videos) * 100, 1),
                'avg_views': int(sum(view_counts) / len(view_counts)),
                'total_views': sum(view_counts),
                'top_videos': [
                    {'title': v.title[:50], 'views': v.view_count_formatted}
                    for v in sorted(videos, key=lambda x: x.view_count, reverse=True)[:3]
                ],
            })

        cluster_stats.sort(key=lambda x: x['total_views'], reverse=True)

        return {
            'method': 'keyword_based',
            'cluster_count': len(cluster_stats),
            'clusters': cluster_stats,
            'dominant_topic': cluster_stats[0]['topic'] if cluster_stats else None,
        }

    # ============================================================
    # 7. 异常值检测
    # ============================================================

    def _detect_anomalies(self) -> Dict[str, Any]:
        """检测异常值"""
        view_counts = [v.view_count for v in self.videos]
        mean = sum(view_counts) / len(view_counts)
        std = self._std(view_counts)

        # 使用 IQR 方法检测异常值
        q1 = self._percentile(view_counts, 25)
        q3 = self._percentile(view_counts, 75)
        iqr = q3 - q1

        upper_bound = q3 + 1.5 * iqr
        lower_bound = max(0, q1 - 1.5 * iqr)

        # 极端高播放量（潜在爆款）
        outliers_high = [v for v in self.videos if v.view_count > upper_bound]
        outliers_high.sort(key=lambda x: x.view_count, reverse=True)

        # 极端低播放量
        outliers_low = [v for v in self.videos if v.view_count < lower_bound and v.view_count > 0]

        # 互动率异常
        detailed = [v for v in self.videos if v.has_details and v.view_count > 1000]
        if detailed:
            engagement_rates = [v.engagement_rate for v in detailed]
            eng_mean = sum(engagement_rates) / len(engagement_rates)
            eng_std = self._std(engagement_rates)

            high_engagement = [v for v in detailed if v.engagement_rate > eng_mean + 2 * eng_std]
            high_engagement.sort(key=lambda x: x.engagement_rate, reverse=True)
        else:
            high_engagement = []

        return {
            'method': 'IQR',
            'thresholds': {
                'upper_bound': int(upper_bound),
                'lower_bound': int(lower_bound),
                'mean': int(mean),
                'std': int(std),
            },
            'viral_videos': {
                'count': len(outliers_high),
                'videos': [
                    {
                        'title': v.title,
                        'views': v.view_count_formatted,
                        'channel': v.channel_name,
                        'url': v.url,
                        'z_score': round((v.view_count - mean) / std, 2) if std > 0 else 0,
                    }
                    for v in outliers_high[:10]
                ],
            },
            'underperforming': {
                'count': len(outliers_low),
            },
            'high_engagement': {
                'count': len(high_engagement),
                'videos': [
                    {
                        'title': v.title,
                        'views': v.view_count_formatted,
                        'engagement_rate': f"{v.engagement_rate * 100:.2f}%",
                        'url': v.url,
                    }
                    for v in high_engagement[:5]
                ],
            },
        }

    # ============================================================
    # 8. 趋势分析
    # ============================================================

    def _analyze_trends(self) -> Dict[str, Any]:
        """分析时间趋势"""
        # 按发布时间分组
        videos_with_date = [v for v in self.videos if v.published_at]
        if not videos_with_date:
            return {}

        # 按年月分组
        monthly = defaultdict(list)
        for v in videos_with_date:
            key = v.published_at.strftime('%Y-%m')
            monthly[key].append(v)

        # 计算每月统计
        monthly_stats = []
        for month, videos in sorted(monthly.items()):
            view_counts = [v.view_count for v in videos]
            monthly_stats.append({
                'month': month,
                'count': len(videos),
                'total_views': sum(view_counts),
                'avg_views': int(sum(view_counts) / len(view_counts)),
            })

        # 识别近期热门话题（最近3个月的高播放量视频的标题关键词）
        recent_cutoff = datetime.now().replace(day=1)
        recent_videos = [v for v in videos_with_date
                        if v.published_at and v.published_at.year >= recent_cutoff.year - 1]
        recent_videos.sort(key=lambda x: x.view_count, reverse=True)

        # 提取热门话题关键词
        hot_keywords = Counter()
        for v in recent_videos[:50]:
            words = re.findall(r'[\u4e00-\u9fa5]{2,4}', v.title)
            hot_keywords.update(words)

        return {
            'date_range': {
                'earliest': min(v.published_at for v in videos_with_date).isoformat(),
                'latest': max(v.published_at for v in videos_with_date).isoformat(),
            },
            'monthly_stats': monthly_stats[-12:],  # 最近12个月
            'trend_direction': self._calculate_trend_direction(monthly_stats),
            'hot_topics': dict(hot_keywords.most_common(15)),
            'recent_viral': [
                {'title': v.title, 'views': v.view_count_formatted, 'date': v.published_at.strftime('%Y-%m-%d')}
                for v in recent_videos[:5]
            ],
        }

    def _calculate_trend_direction(self, monthly_stats: List[Dict]) -> str:
        """计算趋势方向"""
        if len(monthly_stats) < 3:
            return 'insufficient_data'

        recent = monthly_stats[-3:]
        earlier = monthly_stats[-6:-3] if len(monthly_stats) >= 6 else monthly_stats[:3]

        recent_avg = sum(m['avg_views'] for m in recent) / len(recent)
        earlier_avg = sum(m['avg_views'] for m in earlier) / len(earlier)

        change = (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0

        if change > 0.2:
            return 'strongly_growing'
        elif change > 0.05:
            return 'growing'
        elif change < -0.2:
            return 'declining'
        elif change < -0.05:
            return 'slightly_declining'
        return 'stable'

    # ============================================================
    # 9. 洞察生成
    # ============================================================

    def _generate_insights(self, result: AnalysisResult) -> List[str]:
        """生成分析洞察和建议"""
        insights = []

        # 基础洞察
        stats = result.basic_stats
        insights.append(f"数据集包含 {stats['total_videos']} 个视频，总播放量 {stats['view_count']['total']:,}")

        # 播放量分布洞察
        median = stats['view_count']['median']
        mean = stats['view_count']['mean']
        if mean > median * 2:
            insights.append(f"播放量分布呈明显右偏（均值 {mean:,} >> 中位数 {median:,}），存在头部效应")

        # 标题模式洞察
        title = result.title_analysis
        if title.get('patterns', {}).get('counts'):
            top_pattern = max(title['patterns']['counts'].items(), key=lambda x: x[1])
            insights.append(f"最常见的标题模式是「{top_pattern[0]}」类型，占比 {top_pattern[1] / stats['total_videos'] * 100:.1f}%")

        # 时长洞察
        duration = result.duration_analysis
        if duration.get('best_duration_range'):
            insights.append(f"最佳视频时长区间为「{duration['best_duration_range']}」，该区间视频平均播放量最高")

        # 频道洞察
        channels = result.channel_analysis
        if channels.get('top_by_views'):
            top_channel = channels['top_by_views'][0]
            insights.append(f"头部频道「{top_channel['channel']}」贡献了最多播放量（{top_channel['total_views']:,}）")

        # 聚类洞察
        clusters = result.clusters
        if clusters.get('clusters'):
            top_cluster = clusters['clusters'][0]
            insights.append(f"主导内容类型是「{top_cluster['topic']}」，占总播放量的较大比例")

        # 异常值洞察
        anomalies = result.anomalies
        if anomalies.get('viral_videos', {}).get('count', 0) > 0:
            viral_count = anomalies['viral_videos']['count']
            insights.append(f"识别出 {viral_count} 个异常高播放量视频（潜在爆款），值得深入分析其特征")

        # 趋势洞察
        trends = result.trends
        if trends.get('trend_direction'):
            direction_map = {
                'strongly_growing': '强劲增长',
                'growing': '稳步增长',
                'stable': '基本稳定',
                'slightly_declining': '略有下降',
                'declining': '明显下降',
            }
            direction = direction_map.get(trends['trend_direction'], '未知')
            insights.append(f"整体趋势呈「{direction}」态势")

        # 内容建议
        insights.append("---")
        insights.append("【内容创作建议】")

        # 基于聚类的建议
        if clusters.get('clusters'):
            high_view_clusters = [c for c in clusters['clusters'] if c['avg_views'] > stats['view_count']['mean']]
            if high_view_clusters:
                topics = [c['topic'] for c in high_view_clusters[:3]]
                insights.append(f"推荐选题方向：{', '.join(topics)}")

        # 基于标题模式的建议
        if title.get('patterns', {}).get('counts'):
            pattern_performance = []
            for pattern_name, count in title['patterns']['counts'].items():
                if count > 0 and title['patterns']['examples'].get(pattern_name):
                    examples = title['patterns']['examples'][pattern_name]
                    if examples:
                        avg_views = sum(int(e['views'].replace('M', '000000').replace('K', '000').replace('.', ''))
                                       for e in examples if e['views']) / len(examples)
                        pattern_performance.append((pattern_name, avg_views))

            if pattern_performance:
                best_pattern = max(pattern_performance, key=lambda x: x[1])
                insights.append(f"建议采用「{best_pattern[0]}」类型的标题模式，表现相对较好")

        # 时长建议
        if duration.get('best_duration_range'):
            insights.append(f"建议视频时长控制在「{duration['best_duration_range']}」区间")

        return insights

    # ============================================================
    # 辅助方法
    # ============================================================

    def _median(self, data: List[float]) -> float:
        """计算中位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        n = len(sorted_data)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_data[mid - 1] + sorted_data[mid]) / 2
        return sorted_data[mid]

    def _std(self, data: List[float]) -> float:
        """计算标准差"""
        if not data or len(data) < 2:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return math.sqrt(variance)

    def _percentile(self, data: List[float], p: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        return sorted_data[int(f)] * (c - k) + sorted_data[int(c)] * (k - f)

    def save_report(self, result: AnalysisResult, output_dir: str = "data/analysis") -> str:
        """保存分析报告"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存完整 JSON 报告
        json_path = output_path / f"analysis_report_{timestamp}.json"
        report_data = {
            'generated_at': result.generated_at,
            'video_count': result.video_count,
            'basic_stats': result.basic_stats,
            'title_analysis': result.title_analysis,
            'content_patterns': result.content_patterns,
            'channel_analysis': result.channel_analysis,
            'duration_analysis': result.duration_analysis,
            'clusters': result.clusters,
            'anomalies': result.anomalies,
            'trends': result.trends,
            'insights': result.insights,
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"分析报告已保存: {json_path}")
        return str(json_path)


def analyze_videos(db_path: Optional[str] = None) -> AnalysisResult:
    """便捷函数：执行视频分析"""
    analyzer = VideoAnalyzer(db_path)
    return analyzer.analyze()
