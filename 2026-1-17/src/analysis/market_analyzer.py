#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场规模与竞争格局分析器

分析维度：
1. 市场边界 - 总视频数、总播放量、覆盖频道数
2. 竞争强度 - 头部集中度、长尾分布
3. 发布频率 - 日均/月均发布量、活跃频道
4. 时间趋势 - 发布时间分布、增长趋势
5. 进入壁垒 - 爆款门槛、平均表现
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.logger import setup_logger
from src.shared.models import CompetitorVideo
from src.shared.repositories import CompetitorVideoRepository
from src.research.yt_dlp_client import YtDlpClient


@dataclass
class MarketReport:
    """市场分析报告"""

    # 市场规模
    market_size: Dict[str, Any] = field(default_factory=dict)

    # 频道竞争
    channel_competition: Dict[str, Any] = field(default_factory=dict)

    # 发布频率
    publishing_frequency: Dict[str, Any] = field(default_factory=dict)

    # 时间趋势
    time_trends: Dict[str, Any] = field(default_factory=dict)

    # 进入壁垒
    entry_barriers: Dict[str, Any] = field(default_factory=dict)

    # AI创作者机会分析
    ai_creator_opportunities: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    generated_at: str = ""
    sample_size: int = 0

    # 时间范围信息
    time_context: Dict[str, Any] = field(default_factory=dict)


class MarketAnalyzer:
    """市场规模与竞争格局分析器"""

    def __init__(self, db_path: Optional[str] = None):
        self.logger = setup_logger('market_analyzer')
        self.repo = CompetitorVideoRepository(db_path)
        self.client = YtDlpClient()
        self.videos: List[CompetitorVideo] = []

    def load_data(self, limit: int = 5000) -> int:
        """加载数据"""
        self.videos = self.repo.find_all(limit=limit)
        self.logger.info(f"加载了 {len(self.videos)} 个视频")
        return len(self.videos)

    def enrich_publish_dates(self, limit: int = 200) -> int:
        """
        补充发布时间（需要单独请求详情）

        Args:
            limit: 最多补充多少个

        Returns:
            成功补充的数量
        """
        # 找出没有发布时间的视频（优先高播放量）
        no_date = [v for v in self.videos if not v.published_at]
        no_date.sort(key=lambda x: x.view_count, reverse=True)
        no_date = no_date[:limit]

        self.logger.info(f"开始补充 {len(no_date)} 个视频的发布时间...")

        success = 0
        for i, v in enumerate(no_date, 1):
            try:
                info = self.client.get_video_info(v.youtube_id)
                if info and info.get('upload_date'):
                    # 更新数据库
                    upload_date = info['upload_date']
                    # 解析日期 YYYYMMDD 或 YYYY-MM-DD
                    if '-' in upload_date:
                        dt = datetime.strptime(upload_date, '%Y-%m-%d')
                    else:
                        dt = datetime.strptime(upload_date, '%Y%m%d')

                    v.published_at = dt
                    self.repo.save(v)
                    success += 1

                if i % 20 == 0:
                    self.logger.info(f"进度: {i}/{len(no_date)}, 成功: {success}")

            except Exception as e:
                self.logger.warning(f"获取 {v.youtube_id} 失败: {e}")

        self.logger.info(f"发布时间补充完成: {success}/{len(no_date)}")
        return success

    def analyze(self) -> MarketReport:
        """执行市场分析"""
        if not self.videos:
            self.load_data()

        report = MarketReport()
        report.generated_at = datetime.now().isoformat()
        report.sample_size = len(self.videos)

        self.logger.info("开始市场分析...")

        # 0. 时间范围上下文
        report.time_context = self._build_time_context()

        # 1. 市场规模
        report.market_size = self._analyze_market_size()

        # 2. 频道竞争
        report.channel_competition = self._analyze_channel_competition()

        # 3. 发布频率
        report.publishing_frequency = self._analyze_publishing_frequency()

        # 4. 时间趋势
        report.time_trends = self._analyze_time_trends()

        # 5. 进入壁垒
        report.entry_barriers = self._analyze_entry_barriers()

        # 6. AI创作者机会分析
        report.ai_creator_opportunities = self._analyze_ai_opportunities()

        self.logger.info("市场分析完成")
        return report

    def _build_time_context(self) -> Dict[str, Any]:
        """构建时间范围上下文"""
        now = datetime.now()
        videos_with_date = [v for v in self.videos if v.published_at]

        if not videos_with_date:
            return {
                'analysis_date': now.strftime('%Y-%m-%d'),
                'data_has_dates': False,
                'note': '数据缺少发布时间，时间分析受限'
            }

        dates = [v.published_at for v in videos_with_date]
        earliest = min(dates)
        latest = max(dates)

        # 统计各时间段的视频数量
        time_buckets = {
            '24小时内': len([v for v in videos_with_date if (now - v.published_at).days < 1]),
            '7天内': len([v for v in videos_with_date if (now - v.published_at).days < 7]),
            '30天内': len([v for v in videos_with_date if (now - v.published_at).days < 30]),
            '90天内': len([v for v in videos_with_date if (now - v.published_at).days < 90]),
            '6个月内': len([v for v in videos_with_date if (now - v.published_at).days < 180]),
            '1年内': len([v for v in videos_with_date if (now - v.published_at).days < 365]),
            '1年以上': len([v for v in videos_with_date if (now - v.published_at).days >= 365]),
        }

        return {
            'analysis_date': now.strftime('%Y-%m-%d'),
            'data_has_dates': True,
            'videos_with_date_count': len(videos_with_date),
            'videos_without_date_count': len(self.videos) - len(videos_with_date),
            'date_coverage_rate': round(len(videos_with_date) / len(self.videos) * 100, 1),
            'date_range': {
                'earliest': earliest.strftime('%Y-%m-%d'),
                'latest': latest.strftime('%Y-%m-%d'),
                'span_days': (latest - earliest).days,
                'span_description': self._describe_time_span((latest - earliest).days),
            },
            'time_distribution': time_buckets,
            'time_distribution_percent': {
                k: round(v / len(videos_with_date) * 100, 1)
                for k, v in time_buckets.items()
            },
        }

    def _describe_time_span(self, days: int) -> str:
        """将天数转换为可读描述"""
        if days < 7:
            return f"{days}天"
        elif days < 30:
            return f"{days // 7}周{days % 7}天" if days % 7 else f"{days // 7}周"
        elif days < 365:
            months = days // 30
            return f"约{months}个月"
        else:
            years = days // 365
            months = (days % 365) // 30
            return f"{years}年{months}个月" if months else f"{years}年"

    def _analyze_market_size(self) -> Dict[str, Any]:
        """分析市场规模"""
        view_counts = [v.view_count for v in self.videos]

        return {
            'sample_videos': len(self.videos),
            'total_views': sum(view_counts),
            'avg_views': int(sum(view_counts) / len(view_counts)) if view_counts else 0,
            'median_views': sorted(view_counts)[len(view_counts)//2] if view_counts else 0,
            'max_views': max(view_counts) if view_counts else 0,
            'estimated_market': self._estimate_total_market(),
        }

    def _estimate_total_market(self) -> Dict[str, Any]:
        """估算总市场规模"""
        # 基于搜索结果的样本，估算市场总量
        # 假设搜索结果覆盖了市场的一部分
        return {
            'note': '基于搜索样本估算，实际市场可能更大',
            'sample_coverage': '搜索结果 Top 200/关键词',
            'estimated_multiplier': '2-5x',
        }

    def _analyze_channel_competition(self) -> Dict[str, Any]:
        """分析频道竞争格局"""
        channel_videos = defaultdict(list)
        for v in self.videos:
            if v.channel_name:
                channel_videos[v.channel_name].append(v)

        total_channels = len(channel_videos)

        # 频道规模分布
        size_distribution = {
            'single_video': sum(1 for vids in channel_videos.values() if len(vids) == 1),
            'small_2_4': sum(1 for vids in channel_videos.values() if 2 <= len(vids) < 5),
            'medium_5_9': sum(1 for vids in channel_videos.values() if 5 <= len(vids) < 10),
            'large_10_plus': sum(1 for vids in channel_videos.values() if len(vids) >= 10),
        }

        # 头部集中度（Top 10 频道占比）
        channel_stats = []
        for channel, vids in channel_videos.items():
            total_views = sum(v.view_count for v in vids)
            channel_stats.append({
                'channel': channel,
                'video_count': len(vids),
                'total_views': total_views,
                'avg_views': int(total_views / len(vids)),
            })

        channel_stats.sort(key=lambda x: x['total_views'], reverse=True)

        total_market_views = sum(c['total_views'] for c in channel_stats)
        top10_views = sum(c['total_views'] for c in channel_stats[:10])
        top20_views = sum(c['total_views'] for c in channel_stats[:20])

        return {
            'total_channels': total_channels,
            'size_distribution': size_distribution,
            'concentration': {
                'top10_share': round(top10_views / total_market_views * 100, 1) if total_market_views else 0,
                'top20_share': round(top20_views / total_market_views * 100, 1) if total_market_views else 0,
                'herfindahl_index': self._calculate_hhi(channel_stats),
            },
            'top_channels': channel_stats[:15],
            'new_entrants': self._identify_new_entrants(channel_videos),
        }

    def _calculate_hhi(self, channel_stats: List[Dict]) -> float:
        """计算赫芬达尔指数（市场集中度）"""
        total = sum(c['total_views'] for c in channel_stats)
        if total == 0:
            return 0
        hhi = sum((c['total_views'] / total * 100) ** 2 for c in channel_stats)
        return round(hhi, 2)

    def _identify_new_entrants(self, channel_videos: Dict) -> Dict[str, Any]:
        """识别新进入者"""
        # 基于视频数量少但播放量不错的频道
        new_entrants = []
        for channel, vids in channel_videos.items():
            if 1 <= len(vids) <= 3:
                total_views = sum(v.view_count for v in vids)
                avg_views = total_views / len(vids)
                if avg_views > 10000:  # 平均播放量超过 1 万
                    new_entrants.append({
                        'channel': channel,
                        'video_count': len(vids),
                        'avg_views': int(avg_views),
                    })

        new_entrants.sort(key=lambda x: x['avg_views'], reverse=True)
        return {
            'count': len(new_entrants),
            'promising': new_entrants[:10],
        }

    def _analyze_publishing_frequency(self) -> Dict[str, Any]:
        """分析发布频率"""
        videos_with_date = [v for v in self.videos if v.published_at]

        if not videos_with_date:
            return {'note': '缺少发布时间数据，需要补充采集'}

        dates = [v.published_at for v in videos_with_date]
        earliest = min(dates)
        latest = max(dates)
        date_range = (latest - earliest).days

        # 日均发布
        daily_avg = len(videos_with_date) / date_range if date_range > 0 else 0

        # 按月统计
        monthly = defaultdict(int)
        for v in videos_with_date:
            key = v.published_at.strftime('%Y-%m')
            monthly[key] += 1

        # 按周统计
        weekly = defaultdict(int)
        for v in videos_with_date:
            key = v.published_at.strftime('%Y-W%W')
            weekly[key] += 1

        # 星期分布
        weekday = defaultdict(int)
        for v in videos_with_date:
            weekday[v.published_at.weekday()] += 1

        return {
            'sample_with_date': len(videos_with_date),
            'date_range': {
                'start': earliest.isoformat(),
                'end': latest.isoformat(),
                'days': date_range,
            },
            'frequency': {
                'daily_avg': round(daily_avg, 2),
                'weekly_avg': round(daily_avg * 7, 1),
                'monthly_avg': round(daily_avg * 30, 0),
            },
            'monthly_distribution': dict(sorted(monthly.items())[-12:]),
            'weekday_distribution': {
                '周一': weekday[0], '周二': weekday[1], '周三': weekday[2],
                '周四': weekday[3], '周五': weekday[4], '周六': weekday[5], '周日': weekday[6],
            },
        }

    def _analyze_time_trends(self) -> Dict[str, Any]:
        """分析时间趋势"""
        videos_with_date = [v for v in self.videos if v.published_at]

        if not videos_with_date:
            return {'note': '缺少发布时间数据'}

        # 按年统计
        yearly = defaultdict(lambda: {'count': 0, 'views': 0})
        for v in videos_with_date:
            year = v.published_at.year
            yearly[year]['count'] += 1
            yearly[year]['views'] += v.view_count

        # 计算年增长率
        years = sorted(yearly.keys())
        growth_rates = []
        for i in range(1, len(years)):
            prev = yearly[years[i-1]]['count']
            curr = yearly[years[i]]['count']
            if prev > 0:
                rate = (curr - prev) / prev * 100
                growth_rates.append({'year': years[i], 'growth': round(rate, 1)})

        # 近期趋势（最近 3 个月 vs 之前 3 个月）
        now = datetime.now()
        recent_3m = [v for v in videos_with_date if v.published_at >= now - timedelta(days=90)]
        prev_3m = [v for v in videos_with_date
                   if now - timedelta(days=180) <= v.published_at < now - timedelta(days=90)]

        return {
            'yearly_stats': {year: stats for year, stats in sorted(yearly.items())},
            'growth_rates': growth_rates,
            'recent_trend': {
                'recent_3m_count': len(recent_3m),
                'prev_3m_count': len(prev_3m),
                'trend': 'growing' if len(recent_3m) > len(prev_3m) * 1.1 else
                        ('declining' if len(recent_3m) < len(prev_3m) * 0.9 else 'stable'),
            },
        }

    def _analyze_entry_barriers(self) -> Dict[str, Any]:
        """分析进入壁垒"""
        view_counts = sorted([v.view_count for v in self.videos], reverse=True)

        # 播放量分层
        tiers = {
            'viral_1m_plus': sum(1 for v in view_counts if v >= 1000000),
            'excellent_100k': sum(1 for v in view_counts if 100000 <= v < 1000000),
            'good_10k': sum(1 for v in view_counts if 10000 <= v < 100000),
            'average_1k': sum(1 for v in view_counts if 1000 <= v < 10000),
            'low_under_1k': sum(1 for v in view_counts if v < 1000),
        }

        # 爆款门槛
        p90 = view_counts[int(len(view_counts) * 0.1)] if view_counts else 0
        p95 = view_counts[int(len(view_counts) * 0.05)] if view_counts else 0
        p99 = view_counts[int(len(view_counts) * 0.01)] if view_counts else 0

        return {
            'performance_tiers': tiers,
            'thresholds': {
                'top_10_percent': p90,
                'top_5_percent': p95,
                'top_1_percent': p99,
            },
            'success_rate': {
                'viral_rate': round(tiers['viral_1m_plus'] / len(self.videos) * 100, 2),
                'excellent_rate': round(tiers['excellent_100k'] / len(self.videos) * 100, 2),
                'above_average_rate': round(
                    (tiers['viral_1m_plus'] + tiers['excellent_100k'] + tiers['good_10k'])
                    / len(self.videos) * 100, 1),
            },
            'recommendations': self._generate_entry_recommendations(tiers, p90),
        }

    def _generate_entry_recommendations(self, tiers: Dict, p90: int) -> List[str]:
        """生成进入建议"""
        recs = []

        viral_rate = tiers['viral_1m_plus'] / sum(tiers.values()) * 100
        if viral_rate < 2:
            recs.append(f"爆款率约 {viral_rate:.1f}%，需要持续产出才能命中爆款")

        recs.append(f"进入 Top 10% 需要达到 {p90:,} 播放量")

        if tiers['low_under_1k'] > sum(tiers.values()) * 0.3:
            recs.append("约 30%+ 视频播放量不足 1000，市场存在大量低质量内容")

        return recs

    def _analyze_ai_opportunities(self) -> Dict[str, Any]:
        """
        AI 视频创作者机会分析

        专为想批量发布 AI 视频的用户设计，挖掘：
        1. 近期爆款（7天/30天/90天/6个月内）- 可模仿的成功案例
        2. 小众高增长 - 日均增长快但总量不大的蓝海
        3. 小频道黑马 - 证明新频道也能成功
        4. 高互动率模板 - 适合 AI 配音的内容类型
        """
        now = datetime.now()
        videos_with_date = [v for v in self.videos if v.published_at]

        if not videos_with_date:
            return {
                'note': '需要发布时间数据才能进行机会分析',
                'time_range': '无法确定'
            }

        # 定义时间窗口
        time_windows = {
            '7天内': timedelta(days=7),
            '30天内': timedelta(days=30),
            '90天内': timedelta(days=90),
            '6个月内': timedelta(days=180),
        }

        # 1. 各时间窗口的近期爆款
        recent_viral = {}
        for window_name, delta in time_windows.items():
            cutoff = now - delta
            recent = [v for v in videos_with_date if v.published_at >= cutoff]

            if recent:
                # 按播放量排序
                recent_sorted = sorted(recent, key=lambda x: x.view_count, reverse=True)
                top_videos = []
                for v in recent_sorted[:10]:
                    days_old = (now - v.published_at).days
                    daily_growth = v.view_count / max(days_old, 1)
                    top_videos.append({
                        'title': v.title[:50] + '...' if len(v.title) > 50 else v.title,
                        'channel': v.channel_name,
                        'views': v.view_count,
                        'published_at': v.published_at.strftime('%Y-%m-%d'),
                        'days_old': days_old,
                        'daily_growth': int(daily_growth),
                        'url': v.url,
                    })

                recent_viral[window_name] = {
                    'video_count': len(recent),
                    'total_views': sum(v.view_count for v in recent),
                    'avg_views': int(sum(v.view_count for v in recent) / len(recent)),
                    'top_performers': top_videos,
                }

        # 2. 高日均增长视频（所有时间窗口汇总）
        high_growth = []
        for v in videos_with_date:
            days_old = (now - v.published_at).days
            if days_old < 1:
                continue
            daily_growth = v.view_count / days_old
            if daily_growth > 500 and v.view_count > 5000:  # 日均 500+ 且总量 > 5000
                high_growth.append({
                    'title': v.title[:50] + '...' if len(v.title) > 50 else v.title,
                    'channel': v.channel_name,
                    'views': v.view_count,
                    'published_at': v.published_at.strftime('%Y-%m-%d'),
                    'days_old': days_old,
                    'time_bucket': self._get_time_bucket(days_old),
                    'daily_growth': int(daily_growth),
                    'url': v.url,
                })

        high_growth.sort(key=lambda x: x['daily_growth'], reverse=True)

        # 3. 小频道黑马（1-3 个视频的频道但有爆款）
        channel_videos = defaultdict(list)
        for v in self.videos:
            if v.channel_name:
                channel_videos[v.channel_name].append(v)

        small_channel_hits = []
        for channel, vids in channel_videos.items():
            if 1 <= len(vids) <= 3:
                for v in vids:
                    if v.view_count > 10000:  # 播放量 > 1 万
                        days_old = (now - v.published_at).days if v.published_at else None
                        small_channel_hits.append({
                            'title': v.title[:50] + '...' if len(v.title) > 50 else v.title,
                            'channel': channel,
                            'channel_video_count': len(vids),
                            'views': v.view_count,
                            'published_at': v.published_at.strftime('%Y-%m-%d') if v.published_at else '未知',
                            'days_old': days_old,
                            'time_bucket': self._get_time_bucket(days_old) if days_old else '未知',
                            'url': v.url,
                        })

        small_channel_hits.sort(key=lambda x: x['views'], reverse=True)

        # 4. 高互动率模板（适合 AI 配音）
        high_engagement = []
        for v in self.videos:
            if v.like_count and v.view_count > 1000:
                engagement_rate = (v.like_count + (v.comment_count or 0)) / v.view_count * 100
                if engagement_rate > 3:  # 互动率 > 3%
                    days_old = (now - v.published_at).days if v.published_at else None
                    high_engagement.append({
                        'title': v.title[:50] + '...' if len(v.title) > 50 else v.title,
                        'channel': v.channel_name,
                        'views': v.view_count,
                        'likes': v.like_count,
                        'comments': v.comment_count or 0,
                        'engagement_rate': round(engagement_rate, 2),
                        'published_at': v.published_at.strftime('%Y-%m-%d') if v.published_at else '未知',
                        'days_old': days_old,
                        'time_bucket': self._get_time_bucket(days_old) if days_old else '未知',
                        'url': v.url,
                    })

        high_engagement.sort(key=lambda x: x['engagement_rate'], reverse=True)

        # 生成机会总结
        summary = self._generate_opportunity_summary(
            recent_viral, high_growth, small_channel_hits, high_engagement
        )

        return {
            'analysis_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'data_time_range': {
                'videos_with_date': len(videos_with_date),
                'earliest': min(v.published_at for v in videos_with_date).strftime('%Y-%m-%d'),
                'latest': max(v.published_at for v in videos_with_date).strftime('%Y-%m-%d'),
            },
            'recent_viral_by_window': recent_viral,
            'high_daily_growth': {
                'count': len(high_growth),
                'description': '日均播放增长 > 500 且总播放 > 5000 的视频',
                'top_performers': high_growth[:20],
            },
            'small_channel_hits': {
                'count': len(small_channel_hits),
                'description': '1-3个视频的新频道中播放量 > 1万的爆款',
                'top_performers': small_channel_hits[:20],
            },
            'high_engagement_templates': {
                'count': len(high_engagement),
                'description': '互动率 > 3% 的高互动视频（适合 AI 配音）',
                'top_performers': high_engagement[:20],
            },
            'opportunity_summary': summary,
        }

    def _get_time_bucket(self, days: int) -> str:
        """将天数转换为时间桶标签"""
        if days < 1:
            return '24小时内'
        elif days < 7:
            return '7天内'
        elif days < 30:
            return '30天内'
        elif days < 90:
            return '90天内'
        elif days < 180:
            return '6个月内'
        elif days < 365:
            return '1年内'
        else:
            return '1年以上'

    def _generate_opportunity_summary(
        self,
        recent_viral: Dict,
        high_growth: List,
        small_channel_hits: List,
        high_engagement: List
    ) -> Dict[str, Any]:
        """生成机会总结"""

        # 统计各时间段的机会数量
        time_bucket_counts = defaultdict(int)
        for item in high_growth:
            time_bucket_counts[item['time_bucket']] += 1
        for item in small_channel_hits:
            if item['time_bucket'] != '未知':
                time_bucket_counts[item['time_bucket']] += 1

        recommendations = []

        # 基于数据给出建议
        if recent_viral.get('30天内', {}).get('video_count', 0) > 5:
            recommendations.append(f"30天内有 {recent_viral['30天内']['video_count']} 个新视频，市场活跃度较高")

        if high_growth:
            avg_daily = sum(v['daily_growth'] for v in high_growth[:10]) / min(10, len(high_growth))
            recommendations.append(f"高增长视频日均播放 {int(avg_daily):,}，存在快速起量机会")

        if small_channel_hits:
            recent_hits = [v for v in small_channel_hits if v.get('days_old') and v['days_old'] < 90]
            if recent_hits:
                recommendations.append(f"近90天有 {len(recent_hits)} 个小频道爆款，新频道有机会")

        if high_engagement:
            recommendations.append(f"发现 {len(high_engagement)} 个高互动模板，适合 AI 配音复制")

        return {
            'opportunities_by_time': dict(time_bucket_counts),
            'best_time_window': max(time_bucket_counts.items(), key=lambda x: x[1])[0] if time_bucket_counts else '未知',
            'recommendations': recommendations,
            'action_items': [
                '优先模仿 30 天内的近期爆款',
                '关注日增长 > 1000 的高速增长视频',
                '参考小频道爆款的选题和标题',
                '使用高互动率视频作为 AI 配音模板',
            ],
        }

    def save_report(self, report: MarketReport, output_path: str = None) -> str:
        """保存报告"""
        if output_path is None:
            output_dir = Path("data/analysis")
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"market_report_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': report.generated_at,
                'sample_size': report.sample_size,
                'time_context': report.time_context,
                'market_size': report.market_size,
                'channel_competition': report.channel_competition,
                'publishing_frequency': report.publishing_frequency,
                'time_trends': report.time_trends,
                'entry_barriers': report.entry_barriers,
                'ai_creator_opportunities': report.ai_creator_opportunities,
            }, f, ensure_ascii=False, indent=2)

        return str(output_path)

    def print_summary(self, report: MarketReport):
        """打印摘要"""
        print("=" * 60)
        print("📊 市场规模与竞争格局分析报告")
        print("=" * 60)
        print()

        # 市场规模
        ms = report.market_size
        print("【1. 市场规模】")
        print(f"  样本视频数: {ms['sample_videos']:,}")
        print(f"  总播放量: {ms['total_views']:,}")
        print(f"  平均播放量: {ms['avg_views']:,}")
        print(f"  中位数播放量: {ms['median_views']:,}")
        print()

        # 频道竞争
        cc = report.channel_competition
        print("【2. 频道竞争格局】")
        print(f"  总频道数: {cc['total_channels']}")
        print(f"  单视频频道: {cc['size_distribution']['single_video']} ({cc['size_distribution']['single_video']/cc['total_channels']*100:.1f}%)")
        print(f"  Top10 集中度: {cc['concentration']['top10_share']}%")
        print(f"  Top20 集中度: {cc['concentration']['top20_share']}%")
        print()
        print("  头部频道:")
        for i, ch in enumerate(cc['top_channels'][:5], 1):
            print(f"    {i}. {ch['channel'][:20]:20} | {ch['video_count']:3} 视频 | {ch['total_views']:>10,} 播放")
        print()

        # 发布频率
        pf = report.publishing_frequency
        if 'frequency' in pf:
            print("【3. 发布频率】")
            print(f"  日均发布: {pf['frequency']['daily_avg']} 视频/天")
            print(f"  月均发布: {pf['frequency']['monthly_avg']} 视频/月")
            if pf.get('weekday_distribution'):
                best_day = max(pf['weekday_distribution'].items(), key=lambda x: x[1])
                print(f"  最活跃日: {best_day[0]} ({best_day[1]} 视频)")
            print()

        # 进入壁垒
        eb = report.entry_barriers
        print("【4. 进入壁垒】")
        print(f"  爆款率(100万+): {eb['success_rate']['viral_rate']}%")
        print(f"  优秀率(10万+): {eb['success_rate']['excellent_rate']}%")
        print(f"  Top 10% 门槛: {eb['thresholds']['top_10_percent']:,} 播放")
        print()
        print("  播放量分层:")
        for tier, count in eb['performance_tiers'].items():
            pct = count / report.sample_size * 100
            bar = '█' * int(pct / 2)
            print(f"    {tier:15}: {count:4} ({pct:5.1f}%) {bar}")

        print()
        print("=" * 60)


def analyze_market(db_path: str = None, enrich_dates: bool = False) -> MarketReport:
    """便捷函数：执行市场分析"""
    analyzer = MarketAnalyzer(db_path)
    analyzer.load_data()

    if enrich_dates:
        analyzer.enrich_publish_dates(limit=200)
        analyzer.load_data()  # 重新加载

    return analyzer.analyze()
