#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调研报告交互页面生成器 v3 - 咨询框架升级版

融合 McKinsey/BCG 咨询分析框架的 YouTube 内容市场分析工具

核心框架：
1. BCG 矩阵 → YouTube 内容四象限（频道规模 × 内容表现）
2. 五力分析 → 创作者竞争态势雷达图
3. GE-McKinsey 9格 → 内容投资决策矩阵
4. MECE 分类 → 多维度数据切片
5. 金字塔原理 → 执行摘要结构

页面结构：
- 执行摘要：核心发现 + 行动建议（金字塔原理）
- 战略分析：BCG 矩阵 + 五力分析 + 市场集中度
- 机会识别：GE-McKinsey 9格 + 机会评分卡
- 模式洞察：标题公式、时长规律、爆款特征
- 数据浏览：完整数据表格，支持翻页浏览所有数据
"""

import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class ResearchReportGenerator:
    """调研报告生成器 - 数据洞察 + 原始数据浏览"""

    def __init__(self, db_path: str = "data/youtube_pipeline.db"):
        self.db_path = db_path

    def generate(
        self,
        theme: str = "老人养生",
        time_window: str = "全部",
        output_path: Optional[str] = None
    ) -> str:
        """生成调研报告 HTML 页面"""
        # 加载所有视频数据
        videos = self._load_videos(time_window)

        if not videos:
            raise ValueError(f"没有找到符合条件的视频数据")

        # 分析数据
        stats = self._calculate_stats(videos)
        patterns = self._analyze_patterns(videos)
        opportunities = self._find_opportunities(videos)
        trends = self._analyze_trends(videos)
        channels = self._analyze_channels(videos)

        # 咨询框架分析
        bcg_matrix = self._analyze_bcg_matrix(videos)
        five_forces = self._analyze_five_forces(videos)
        ge_matrix = self._analyze_ge_matrix(videos)
        executive_summary = self._generate_executive_summary(
            videos, patterns, bcg_matrix, five_forces, opportunities
        )

        # 组装报告数据
        report_data = {
            'meta': {
                'theme': theme,
                'generated_at': datetime.now().isoformat(),
                'sample_size': len(videos),
                'time_window': time_window,
            },
            'stats': stats,
            'patterns': patterns,
            'opportunities': opportunities,
            'trends': trends,
            'channels': channels,
            # 咨询框架数据
            'executive_summary': executive_summary,
            'bcg_matrix': bcg_matrix,
            'five_forces': five_forces,
            'ge_matrix': ge_matrix,
            'videos': videos,  # 完整数据用于前端分页
        }

        # 生成 HTML
        if output_path is None:
            output_dir = Path("data/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_theme = theme.replace(" ", "_")[:20]
            output_path = output_dir / f"research_report_{safe_theme}_{timestamp}.html"
        else:
            output_path = Path(output_path)

        html = self._render_html(report_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(output_path)

    def _load_videos(self, time_window: str = "全部") -> List[Dict]:
        """从数据库加载视频数据"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # 时间范围过滤
        time_filter = ""
        if time_window != "全部":
            days_map = {"1天内": 1, "15天内": 15, "30天内": 30}
            days = days_map.get(time_window, 30)
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            time_filter = f"AND published_at >= '{cutoff}'"

        query = f"""
        SELECT
            youtube_id as id,
            title,
            channel_name,
            'https://www.youtube.com/watch?v=' || youtube_id as url,
            view_count as views,
            like_count as likes,
            comment_count as comments,
            duration,
            published_at,
            collected_at
        FROM competitor_videos
        WHERE view_count > 0
        {time_filter}
        ORDER BY view_count DESC
        """

        cursor = conn.execute(query)
        rows = cursor.fetchall()

        videos = []
        for row in rows:
            video = dict(row)
            # 计算衍生指标
            video = self._enrich_video(video)
            videos.append(video)

        conn.close()
        return videos

    def _enrich_video(self, video: Dict) -> Dict:
        """丰富视频数据：计算日增长、时间分桶、互动率等"""
        # 日增长和时间分桶
        if video.get('published_at'):
            try:
                pub_str = video['published_at']
                if 'T' in pub_str:
                    pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                else:
                    pub_date = datetime.strptime(pub_str[:10], '%Y-%m-%d')

                days_since = max(1, (datetime.now() - pub_date.replace(tzinfo=None)).days)
                video['daily_growth'] = int(video['views'] / days_since)
                video['days_since_publish'] = days_since

                if days_since <= 1:
                    video['time_bucket'] = '24小时内'
                elif days_since <= 7:
                    video['time_bucket'] = '7天内'
                elif days_since <= 30:
                    video['time_bucket'] = '30天内'
                elif days_since <= 90:
                    video['time_bucket'] = '90天内'
                else:
                    video['time_bucket'] = '90天以上'
            except:
                video['daily_growth'] = 0
                video['days_since_publish'] = 0
                video['time_bucket'] = '未知'
        else:
            video['daily_growth'] = 0
            video['days_since_publish'] = 0
            video['time_bucket'] = '未知'

        # 互动率
        views = video.get('views', 0) or 0
        likes = video.get('likes', 0) or 0
        comments = video.get('comments', 0) or 0
        video['engagement_rate'] = round((likes + comments) / views * 100, 2) if views > 0 else 0

        # 时长分类
        dur = video.get('duration', 0) or 0
        if dur < 60:
            video['duration_bucket'] = '短视频(<1分钟)'
        elif dur < 300:
            video['duration_bucket'] = '中短(1-5分钟)'
        elif dur < 600:
            video['duration_bucket'] = '中等(5-10分钟)'
        elif dur < 1800:
            video['duration_bucket'] = '中长(10-30分钟)'
        else:
            video['duration_bucket'] = '长视频(30分钟+)'

        return video

    def _calculate_stats(self, videos: List[Dict]) -> Dict:
        """计算基础统计"""
        if not videos:
            return {}

        views = [v['views'] for v in videos]
        channels = set(v.get('channel_name', '') for v in videos)
        with_date = [v for v in videos if v.get('published_at')]

        return {
            'total_videos': len(videos),
            'total_views': sum(views),
            'avg_views': int(sum(views) / len(views)),
            'median_views': sorted(views)[len(views) // 2],
            'max_views': max(views),
            'total_channels': len(channels),
            'videos_with_date': len(with_date),
            'date_coverage': round(len(with_date) / len(videos) * 100, 1),
        }

    def _analyze_patterns(self, videos: List[Dict]) -> Dict:
        """分析内容模式 - 发现规律"""
        patterns = {}

        # 1. 标题模式分析
        title_patterns = self._analyze_title_patterns(videos)
        patterns['title'] = title_patterns

        # 2. 时长与播放量关系
        duration_performance = self._analyze_duration_performance(videos)
        patterns['duration'] = duration_performance

        # 3. 频道规模与表现
        channel_patterns = self._analyze_channel_patterns(videos)
        patterns['channel'] = channel_patterns

        # 4. 爆款特征提取
        viral_features = self._extract_viral_features(videos)
        patterns['viral'] = viral_features

        return patterns

    def _analyze_title_patterns(self, videos: List[Dict]) -> Dict:
        """分析标题模式"""
        # 常见标题关键词
        keywords = []
        for v in videos:
            title = v.get('title', '')
            # 提取中文词汇（简单分词）
            words = re.findall(r'[\u4e00-\u9fa5]+', title)
            keywords.extend(words)

        word_freq = Counter(keywords)
        top_keywords = word_freq.most_common(30)

        # 分析含特定词汇的视频表现
        trigger_words = ['秘诀', '方法', '技巧', '必看', '揭秘', '真相', '注意', '千万']
        trigger_performance = {}

        for word in trigger_words:
            with_word = [v for v in videos if word in v.get('title', '')]
            without_word = [v for v in videos if word not in v.get('title', '')]

            if with_word and without_word:
                avg_with = sum(v['views'] for v in with_word) / len(with_word)
                avg_without = sum(v['views'] for v in without_word) / len(without_word)
                multiplier = round(avg_with / avg_without, 2) if avg_without > 0 else 0

                trigger_performance[word] = {
                    'count': len(with_word),
                    'avg_views': int(avg_with),
                    'multiplier': multiplier,
                }

        # 标题长度与播放量
        title_length_buckets = {'短标题(≤15字)': [], '中标题(16-30字)': [], '长标题(>30字)': []}
        for v in videos:
            title_len = len(v.get('title', ''))
            if title_len <= 15:
                title_length_buckets['短标题(≤15字)'].append(v['views'])
            elif title_len <= 30:
                title_length_buckets['中标题(16-30字)'].append(v['views'])
            else:
                title_length_buckets['长标题(>30字)'].append(v['views'])

        title_length_performance = {}
        for bucket, views_list in title_length_buckets.items():
            if views_list:
                title_length_performance[bucket] = {
                    'count': len(views_list),
                    'avg_views': int(sum(views_list) / len(views_list)),
                }

        return {
            'top_keywords': top_keywords,
            'trigger_words': trigger_performance,
            'title_length': title_length_performance,
        }

    def _analyze_duration_performance(self, videos: List[Dict]) -> Dict:
        """分析时长与播放量关系"""
        duration_buckets = {}

        for v in videos:
            bucket = v.get('duration_bucket', '未知')
            if bucket not in duration_buckets:
                duration_buckets[bucket] = {'views': [], 'count': 0}
            duration_buckets[bucket]['views'].append(v['views'])
            duration_buckets[bucket]['count'] += 1

        result = {}
        for bucket, data in duration_buckets.items():
            if data['views']:
                result[bucket] = {
                    'count': data['count'],
                    'avg_views': int(sum(data['views']) / len(data['views'])),
                    'max_views': max(data['views']),
                    'total_views': sum(data['views']),
                }

        # 找出最佳时长
        best_bucket = max(result.items(), key=lambda x: x[1]['avg_views'])[0] if result else '未知'

        return {
            'buckets': result,
            'best_duration': best_bucket,
            'insight': f"时长为「{best_bucket}」的视频平均播放量最高",
        }

    def _analyze_channel_patterns(self, videos: List[Dict]) -> Dict:
        """分析频道模式"""
        channel_stats = {}

        for v in videos:
            ch = v.get('channel_name', '未知')
            if ch not in channel_stats:
                channel_stats[ch] = {'videos': [], 'total_views': 0}
            channel_stats[ch]['videos'].append(v)
            channel_stats[ch]['total_views'] += v['views']

        # 频道规模分布
        size_dist = {'单视频': 0, '小型(2-5)': 0, '中型(6-20)': 0, '大型(20+)': 0}
        size_performance = {'单视频': [], '小型(2-5)': [], '中型(6-20)': [], '大型(20+)': []}

        for ch, data in channel_stats.items():
            cnt = len(data['videos'])
            avg_views = data['total_views'] / cnt

            if cnt == 1:
                size_dist['单视频'] += 1
                size_performance['单视频'].append(avg_views)
            elif cnt <= 5:
                size_dist['小型(2-5)'] += 1
                size_performance['小型(2-5)'].append(avg_views)
            elif cnt <= 20:
                size_dist['中型(6-20)'] += 1
                size_performance['中型(6-20)'].append(avg_views)
            else:
                size_dist['大型(20+)'] += 1
                size_performance['大型(20+)'].append(avg_views)

        # 计算各规模频道的平均表现
        size_avg_performance = {}
        for size, views_list in size_performance.items():
            if views_list:
                size_avg_performance[size] = int(sum(views_list) / len(views_list))

        # 集中度
        total_views = sum(d['total_views'] for d in channel_stats.values())
        sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)
        top10_views = sum(d['total_views'] for _, d in sorted_channels[:10])
        top20_views = sum(d['total_views'] for _, d in sorted_channels[:20])

        return {
            'total_channels': len(channel_stats),
            'size_distribution': size_dist,
            'size_performance': size_avg_performance,
            'top10_share': round(top10_views / total_views * 100, 1) if total_views else 0,
            'top20_share': round(top20_views / total_views * 100, 1) if total_views else 0,
            'insight': f"市场集中度：Top10 频道占 {round(top10_views / total_views * 100, 1) if total_views else 0}% 播放量",
        }

    def _extract_viral_features(self, videos: List[Dict]) -> Dict:
        """提取爆款特征"""
        # 定义爆款：播放量 Top 5%
        sorted_videos = sorted(videos, key=lambda x: x['views'], reverse=True)
        viral_count = max(1, len(videos) // 20)  # Top 5%
        viral_videos = sorted_videos[:viral_count]
        normal_videos = sorted_videos[viral_count:]

        # 分析爆款特征
        features = {}

        # 标题长度
        viral_title_len = sum(len(v.get('title', '')) for v in viral_videos) / len(viral_videos)
        normal_title_len = sum(len(v.get('title', '')) for v in normal_videos) / len(normal_videos) if normal_videos else 0
        features['avg_title_length'] = {
            'viral': round(viral_title_len, 1),
            'normal': round(normal_title_len, 1),
        }

        # 时长
        viral_duration = sum(v.get('duration', 0) or 0 for v in viral_videos) / len(viral_videos)
        normal_duration = sum(v.get('duration', 0) or 0 for v in normal_videos) / len(normal_videos) if normal_videos else 0
        features['avg_duration'] = {
            'viral': int(viral_duration),
            'normal': int(normal_duration),
        }

        # 互动率
        viral_engagement = sum(v.get('engagement_rate', 0) for v in viral_videos) / len(viral_videos)
        normal_engagement = sum(v.get('engagement_rate', 0) for v in normal_videos) / len(normal_videos) if normal_videos else 0
        features['avg_engagement'] = {
            'viral': round(viral_engagement, 2),
            'normal': round(normal_engagement, 2),
        }

        # 爆款播放量门槛
        features['viral_threshold'] = viral_videos[-1]['views'] if viral_videos else 0
        features['viral_count'] = viral_count

        return features

    def _analyze_bcg_matrix(self, videos: List[Dict]) -> Dict:
        """BCG 矩阵分析 - YouTube 内容四象限

        X轴：频道规模（该频道在数据集中的视频数量作为代理）
        Y轴：内容表现（播放量/频道平均播放量 = 相对表现）

        四象限：
        - 🌟 爆款模板（大频道 + 高表现）：学习最佳实践
        - ❓ 潜力机会（小频道 + 高表现）：重点关注！可复制的成功
        - 💰 稳定流量（大频道 + 一般表现）：靠粉丝基数
        - 🐕 避免区域（小频道 + 低表现）：不要模仿
        """
        # 计算频道统计
        channel_stats = {}
        for v in videos:
            ch = v.get('channel_name', '未知')
            if ch not in channel_stats:
                channel_stats[ch] = {'videos': [], 'total_views': 0}
            channel_stats[ch]['videos'].append(v)
            channel_stats[ch]['total_views'] += v['views']

        # 计算频道规模分位数
        channel_sizes = [len(d['videos']) for d in channel_stats.values()]
        channel_size_median = sorted(channel_sizes)[len(channel_sizes) // 2] if channel_sizes else 1

        # 计算全局平均播放量
        global_avg_views = sum(v['views'] for v in videos) / len(videos) if videos else 1

        # 分类视频到四象限
        quadrants = {
            'stars': [],      # 🌟 大频道 + 高表现
            'question_marks': [],  # ❓ 小频道 + 高表现
            'cash_cows': [],  # 💰 大频道 + 一般表现
            'dogs': []        # 🐕 小频道 + 低表现
        }

        scatter_data = []  # 散点图数据

        for v in videos:
            ch = v.get('channel_name', '未知')
            ch_data = channel_stats.get(ch, {'videos': [], 'total_views': 0})
            ch_size = len(ch_data['videos'])
            ch_avg_views = ch_data['total_views'] / ch_size if ch_size > 0 else 1

            # 相对表现 = 该视频播放量 / 频道平均播放量
            relative_performance = v['views'] / ch_avg_views if ch_avg_views > 0 else 1

            # 判断象限
            is_large_channel = ch_size >= channel_size_median
            is_high_performer = v['views'] >= global_avg_views

            # 散点数据
            scatter_data.append({
                'x': ch_size,  # 频道规模
                'y': v['views'],  # 播放量
                'title': v.get('title', '')[:30],
                'channel': ch,
                'views': v['views'],
                'url': v.get('url', ''),
                'quadrant': ''
            })

            video_info = {
                'title': v.get('title', ''),
                'channel': ch,
                'views': v['views'],
                'url': v.get('url', ''),
                'relative_performance': round(relative_performance, 2),
                'channel_size': ch_size
            }

            if is_large_channel and is_high_performer:
                quadrants['stars'].append(video_info)
                scatter_data[-1]['quadrant'] = 'stars'
            elif not is_large_channel and is_high_performer:
                quadrants['question_marks'].append(video_info)
                scatter_data[-1]['quadrant'] = 'question_marks'
            elif is_large_channel and not is_high_performer:
                quadrants['cash_cows'].append(video_info)
                scatter_data[-1]['quadrant'] = 'cash_cows'
            else:
                quadrants['dogs'].append(video_info)
                scatter_data[-1]['quadrant'] = 'dogs'

        # 排序每个象限
        for q in quadrants:
            quadrants[q] = sorted(quadrants[q], key=lambda x: x['views'], reverse=True)[:20]

        return {
            'quadrants': quadrants,
            'scatter_data': scatter_data[:500],  # 限制散点数量
            'thresholds': {
                'channel_size_median': channel_size_median,
                'global_avg_views': int(global_avg_views)
            },
            'summary': {
                'stars': len([v for v in videos if channel_stats.get(v.get('channel_name', ''), {}).get('videos', []) and len(channel_stats[v.get('channel_name', '')]['videos']) >= channel_size_median and v['views'] >= global_avg_views]),
                'question_marks': len([v for v in videos if channel_stats.get(v.get('channel_name', ''), {}).get('videos', []) and len(channel_stats[v.get('channel_name', '')]['videos']) < channel_size_median and v['views'] >= global_avg_views]),
                'cash_cows': len([v for v in videos if channel_stats.get(v.get('channel_name', ''), {}).get('videos', []) and len(channel_stats[v.get('channel_name', '')]['videos']) >= channel_size_median and v['views'] < global_avg_views]),
                'dogs': len([v for v in videos if channel_stats.get(v.get('channel_name', ''), {}).get('videos', []) and len(channel_stats[v.get('channel_name', '')]['videos']) < channel_size_median and v['views'] < global_avg_views])
            }
        }

    def _analyze_five_forces(self, videos: List[Dict]) -> Dict:
        """五力分析 - YouTube 创作者竞争态势

        1. 行业竞争强度：头部频道集中度
        2. 新进入者威胁：新频道占比
        3. 替代品威胁：（外部数据，暂用占位）
        4. 买家议价能力：观众参与度/互动率
        5. 供应商议价能力：内容制作成本（用时长代理）
        """
        # 频道统计
        channel_stats = {}
        for v in videos:
            ch = v.get('channel_name', '未知')
            if ch not in channel_stats:
                channel_stats[ch] = {'total_views': 0, 'video_count': 0}
            channel_stats[ch]['total_views'] += v['views']
            channel_stats[ch]['video_count'] += 1

        total_views = sum(d['total_views'] for d in channel_stats.values())
        total_channels = len(channel_stats)

        # 1. 行业竞争强度 - CR4, CR10, HHI
        sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)

        cr4 = sum(d['total_views'] for _, d in sorted_channels[:4]) / total_views * 100 if total_views else 0
        cr10 = sum(d['total_views'] for _, d in sorted_channels[:10]) / total_views * 100 if total_views else 0

        # HHI 指数（赫芬达尔指数）
        hhi = sum((d['total_views'] / total_views * 100) ** 2 for d in channel_stats.values()) if total_views else 0

        # 竞争强度评分 (0-100)
        # HHI < 1500 = 竞争激烈, 1500-2500 = 中度集中, > 2500 = 高度集中
        if hhi < 1500:
            competition_score = 80 + (1500 - hhi) / 1500 * 20  # 80-100
        elif hhi < 2500:
            competition_score = 50 + (2500 - hhi) / 1000 * 30  # 50-80
        else:
            competition_score = max(10, 50 - (hhi - 2500) / 100)  # 10-50

        # 2. 新进入者威胁 - 单视频频道占比
        single_video_channels = sum(1 for d in channel_stats.values() if d['video_count'] == 1)
        new_entrant_ratio = single_video_channels / total_channels * 100 if total_channels else 0
        new_entrant_score = min(100, new_entrant_ratio * 2)  # 50% 单视频频道 = 100分威胁

        # 3. 替代品威胁 - 暂时固定值（需外部数据）
        substitute_score = 60  # 中等威胁

        # 4. 买家议价能力 - 平均互动率
        avg_engagement = sum(v.get('engagement_rate', 0) for v in videos) / len(videos) if videos else 0
        # 互动率越高，观众参与度越高，议价能力越强
        buyer_score = min(100, avg_engagement * 20)  # 5% 互动率 = 100分

        # 5. 供应商议价能力 - 平均时长（制作成本代理）
        avg_duration = sum(v.get('duration', 0) or 0 for v in videos) / len(videos) if videos else 0
        # 时长越长，制作成本越高，供应商议价能力越强
        supplier_score = min(100, avg_duration / 600 * 100)  # 10分钟 = 100分

        return {
            'metrics': {
                'cr4': round(cr4, 1),
                'cr10': round(cr10, 1),
                'hhi': round(hhi, 0),
                'total_channels': total_channels,
                'single_video_channels': single_video_channels,
                'avg_engagement': round(avg_engagement, 2),
                'avg_duration_min': round(avg_duration / 60, 1)
            },
            'radar_scores': {
                'competition': round(competition_score),
                'new_entrants': round(new_entrant_score),
                'substitutes': substitute_score,
                'buyers': round(buyer_score),
                'suppliers': round(supplier_score)
            },
            'interpretation': {
                'competition': '竞争激烈' if hhi < 1500 else ('中度集中' if hhi < 2500 else '高度集中'),
                'new_entrants': '高威胁' if new_entrant_ratio > 50 else ('中等威胁' if new_entrant_ratio > 25 else '低威胁'),
                'buyers': '高参与' if avg_engagement > 3 else ('中等参与' if avg_engagement > 1 else '低参与'),
                'suppliers': '高成本' if avg_duration > 600 else ('中等成本' if avg_duration > 300 else '低成本')
            },
            'top_channels': [
                {
                    'name': name,
                    'views': data['total_views'],
                    'video_count': data['video_count'],
                    'share': round(data['total_views'] / total_views * 100, 1) if total_views else 0
                }
                for name, data in sorted_channels[:10]
            ]
        }

    def _analyze_ge_matrix(self, videos: List[Dict]) -> Dict:
        """GE-McKinsey 9格矩阵 - 内容投资决策

        X轴：市场吸引力（话题热度 = 平均播放量、增长趋势）
        Y轴：竞争优势（内容差异化空间 = 小频道爆款比例）

        9格建议：
        - 重点投资：高吸引力 + 高优势
        - 选择性投资：中等组合
        - 收割/放弃：低吸引力 + 低优势
        """
        # 按时长分桶分析（作为不同"业务单元"）
        duration_buckets = {
            '短视频(<3分钟)': {'min': 0, 'max': 180},
            '中短(3-8分钟)': {'min': 180, 'max': 480},
            '中等(8-15分钟)': {'min': 480, 'max': 900},
            '中长(15-30分钟)': {'min': 900, 'max': 1800},
            '长视频(30分钟+)': {'min': 1800, 'max': float('inf')}
        }

        # 频道统计
        channel_stats = {}
        for v in videos:
            ch = v.get('channel_name', '未知')
            if ch not in channel_stats:
                channel_stats[ch] = {'video_count': 0}
            channel_stats[ch]['video_count'] += 1

        channel_size_median = sorted([d['video_count'] for d in channel_stats.values()])[len(channel_stats) // 2] if channel_stats else 1
        global_avg_views = sum(v['views'] for v in videos) / len(videos) if videos else 1

        matrix_data = []

        for bucket_name, bucket_range in duration_buckets.items():
            bucket_videos = [
                v for v in videos
                if bucket_range['min'] <= (v.get('duration', 0) or 0) < bucket_range['max']
            ]

            if not bucket_videos:
                continue

            # 市场吸引力指标
            avg_views = sum(v['views'] for v in bucket_videos) / len(bucket_videos)
            avg_daily_growth = sum(v.get('daily_growth', 0) for v in bucket_videos) / len(bucket_videos)

            # 竞争优势指标 - 小频道爆款比例
            small_channel_hits = [
                v for v in bucket_videos
                if channel_stats.get(v.get('channel_name', ''), {}).get('video_count', 0) < channel_size_median
                and v['views'] >= global_avg_views
            ]
            opportunity_ratio = len(small_channel_hits) / len(bucket_videos) * 100 if bucket_videos else 0

            # 计算矩阵位置 (1-3)
            # 市场吸引力：基于平均播放量相对于全局平均
            attractiveness_ratio = avg_views / global_avg_views if global_avg_views else 1
            if attractiveness_ratio >= 1.5:
                market_attractiveness = 3  # 高
            elif attractiveness_ratio >= 0.7:
                market_attractiveness = 2  # 中
            else:
                market_attractiveness = 1  # 低

            # 竞争优势：基于小频道爆款比例
            if opportunity_ratio >= 15:
                competitive_strength = 3  # 高
            elif opportunity_ratio >= 5:
                competitive_strength = 2  # 中
            else:
                competitive_strength = 1  # 低

            # 确定投资建议
            score = market_attractiveness + competitive_strength
            if score >= 5:
                recommendation = '重点投资'
                color = '#22c55e'  # 绿色
            elif score >= 4:
                recommendation = '选择性投资'
                color = '#eab308'  # 黄色
            elif score >= 3:
                recommendation = '维持观望'
                color = '#f97316'  # 橙色
            else:
                recommendation = '谨慎对待'
                color = '#ef4444'  # 红色

            matrix_data.append({
                'bucket': bucket_name,
                'video_count': len(bucket_videos),
                'avg_views': int(avg_views),
                'avg_daily_growth': int(avg_daily_growth),
                'opportunity_ratio': round(opportunity_ratio, 1),
                'market_attractiveness': market_attractiveness,
                'competitive_strength': competitive_strength,
                'recommendation': recommendation,
                'color': color,
                'top_videos': sorted(bucket_videos, key=lambda x: x['views'], reverse=True)[:5]
            })

        return {
            'matrix': matrix_data,
            'summary': {
                'invest': len([d for d in matrix_data if d['recommendation'] == '重点投资']),
                'selective': len([d for d in matrix_data if d['recommendation'] == '选择性投资']),
                'maintain': len([d for d in matrix_data if d['recommendation'] == '维持观望']),
                'caution': len([d for d in matrix_data if d['recommendation'] == '谨慎对待'])
            }
        }

    def _generate_executive_summary(self, videos: List[Dict], patterns: Dict,
                                    bcg: Dict, five_forces: Dict, opportunities: Dict) -> Dict:
        """金字塔原理 - 生成执行摘要

        结构：
        1. 核心结论（1句话）
        2. 三大支撑论点
        3. 关键数据
        4. 行动建议
        """
        # 分析数据生成洞察
        insights = []
        actions = []

        # 洞察1：市场集中度
        hhi = five_forces['metrics']['hhi']
        cr10 = five_forces['metrics']['cr10']
        if hhi < 1500:
            insights.append({
                'title': '市场竞争激烈，机会众多',
                'detail': f"HHI 指数 {hhi:.0f}（<1500），Top10 频道仅占 {cr10:.1f}% 播放量，小频道有突围空间",
                'icon': '🔥'
            })
            actions.append('积极进入，快速试错迭代')
        else:
            insights.append({
                'title': '市场较为集中，需差异化',
                'detail': f"HHI 指数 {hhi:.0f}，Top10 频道占 {cr10:.1f}% 播放量，需找到差异化定位",
                'icon': '⚠️'
            })
            actions.append('找准细分赛道，避开头部正面竞争')

        # 洞察2：小频道爆款机会
        question_marks_count = bcg['summary'].get('question_marks', 0)
        total = len(videos)
        qm_ratio = question_marks_count / total * 100 if total else 0
        if qm_ratio > 10:
            insights.append({
                'title': f'小频道爆款频出（{question_marks_count} 个）',
                'detail': f"占比 {qm_ratio:.1f}%，说明内容质量比频道规模更重要",
                'icon': '💡'
            })
            actions.append(f'重点研究 BCG 矩阵「潜力机会」象限的 {min(question_marks_count, 20)} 个案例')
        else:
            insights.append({
                'title': '头部效应明显',
                'detail': f"小频道爆款仅 {question_marks_count} 个（{qm_ratio:.1f}%），大频道占据主要流量",
                'icon': '📊'
            })
            actions.append('考虑与头部频道合作，或深耕长尾细分领域')

        # 洞察3：最佳内容时长
        best_duration = patterns.get('duration', {}).get('best_duration', '未知')
        insights.append({
            'title': f'最佳时长：{best_duration}',
            'detail': f"该时长区间视频平均播放量最高",
            'icon': '⏱️'
        })
        actions.append(f'新视频优先控制在「{best_duration}」区间')

        # 生成核心结论
        if hhi < 1500 and qm_ratio > 10:
            core_conclusion = "市场机会良好：竞争分散 + 小频道可突围，建议积极进入"
        elif hhi < 1500:
            core_conclusion = "市场竞争激烈但头部效应明显，需找准差异化切入点"
        elif qm_ratio > 10:
            core_conclusion = "市场集中但内容创新有空间，优质内容可以突围"
        else:
            core_conclusion = "市场成熟度高，建议谨慎评估后再决定是否进入"

        return {
            'core_conclusion': core_conclusion,
            'insights': insights,
            'actions': actions,
            'key_metrics': {
                'total_videos': len(videos),
                'total_channels': five_forces['metrics']['total_channels'],
                'hhi': hhi,
                'cr10': cr10,
                'question_marks': question_marks_count,
                'best_duration': best_duration
            }
        }

    def _find_opportunities(self, videos: List[Dict]) -> Dict:
        """发现机会"""
        opportunities = {}

        # 1. 小众高价值：高播放但来自小频道
        channel_video_count = Counter(v.get('channel_name', '') for v in videos)
        small_channel_hits = []

        median_views = sorted([v['views'] for v in videos])[len(videos) // 2]
        threshold = median_views * 3  # 播放量超过中位数3倍

        for v in videos:
            ch = v.get('channel_name', '')
            if channel_video_count[ch] <= 3 and v['views'] > threshold:
                small_channel_hits.append(v)

        opportunities['small_channel_hits'] = {
            'count': len(small_channel_hits),
            'threshold': threshold,
            'videos': sorted(small_channel_hits, key=lambda x: x['views'], reverse=True)[:20],
            'insight': f"发现 {len(small_channel_hits)} 个小频道爆款（频道视频≤3个，播放量>{threshold:,}）",
        }

        # 2. 近期爆款：7天内发布且日增长高
        recent_viral = []
        for v in videos:
            if v.get('time_bucket') in ['24小时内', '7天内'] and v.get('daily_growth', 0) > 1000:
                recent_viral.append(v)

        opportunities['recent_viral'] = {
            'count': len(recent_viral),
            'videos': sorted(recent_viral, key=lambda x: x['daily_growth'], reverse=True)[:20],
            'insight': f"近7天有 {len(recent_viral)} 个视频日增长超过 1000",
        }

        # 3. 高互动模板：互动率高的视频
        high_engagement = [v for v in videos if v.get('engagement_rate', 0) > 3]
        opportunities['high_engagement'] = {
            'count': len(high_engagement),
            'videos': sorted(high_engagement, key=lambda x: x['engagement_rate'], reverse=True)[:20],
            'insight': f"有 {len(high_engagement)} 个视频互动率超过 3%",
        }

        # 4. 潜力视频：播放量中等但增长快
        growing_videos = []
        for v in videos:
            views = v.get('views', 0)
            daily_growth = v.get('daily_growth', 0)
            # 播放量在 1万-50万 且日增长率高
            if 10000 < views < 500000 and daily_growth > 500:
                growing_videos.append(v)

        opportunities['growing'] = {
            'count': len(growing_videos),
            'videos': sorted(growing_videos, key=lambda x: x['daily_growth'], reverse=True)[:20],
            'insight': f"有 {len(growing_videos)} 个潜力视频（1万-50万播放，日增>500）",
        }

        return opportunities

    def _analyze_trends(self, videos: List[Dict]) -> Dict:
        """分析趋势"""
        trends = {}

        # 按时间分桶统计
        time_dist = Counter(v.get('time_bucket', '未知') for v in videos)
        trends['time_distribution'] = dict(time_dist)

        # 各时间段的平均播放量
        time_performance = {}
        time_buckets = ['24小时内', '7天内', '30天内', '90天内', '90天以上']

        for bucket in time_buckets:
            bucket_videos = [v for v in videos if v.get('time_bucket') == bucket]
            if bucket_videos:
                time_performance[bucket] = {
                    'count': len(bucket_videos),
                    'avg_views': int(sum(v['views'] for v in bucket_videos) / len(bucket_videos)),
                    'avg_daily_growth': int(sum(v.get('daily_growth', 0) for v in bucket_videos) / len(bucket_videos)),
                }

        trends['time_performance'] = time_performance

        # 热门关键词变化（近期 vs 全部）
        recent_videos = [v for v in videos if v.get('time_bucket') in ['24小时内', '7天内', '30天内']]
        old_videos = [v for v in videos if v.get('time_bucket') in ['90天内', '90天以上']]

        def extract_keywords(video_list):
            words = []
            for v in video_list:
                title = v.get('title', '')
                words.extend(re.findall(r'[\u4e00-\u9fa5]{2,4}', title))
            return Counter(words)

        recent_keywords = extract_keywords(recent_videos)
        old_keywords = extract_keywords(old_videos)

        # 找出上升和下降的关键词
        rising_keywords = []
        falling_keywords = []

        all_keywords = set(recent_keywords.keys()) | set(old_keywords.keys())
        for kw in all_keywords:
            recent_freq = recent_keywords.get(kw, 0) / max(len(recent_videos), 1)
            old_freq = old_keywords.get(kw, 0) / max(len(old_videos), 1)

            if recent_freq > old_freq * 1.5 and recent_keywords.get(kw, 0) >= 3:
                rising_keywords.append((kw, recent_keywords.get(kw, 0), round(recent_freq / max(old_freq, 0.001), 1)))
            elif old_freq > recent_freq * 1.5 and old_keywords.get(kw, 0) >= 3:
                falling_keywords.append((kw, old_keywords.get(kw, 0), round(old_freq / max(recent_freq, 0.001), 1)))

        trends['rising_keywords'] = sorted(rising_keywords, key=lambda x: x[2], reverse=True)[:10]
        trends['falling_keywords'] = sorted(falling_keywords, key=lambda x: x[2], reverse=True)[:10]

        return trends

    def _analyze_channels(self, videos: List[Dict]) -> List[Dict]:
        """分析频道数据"""
        channel_stats = {}

        for v in videos:
            ch = v.get('channel_name', '未知')
            if ch not in channel_stats:
                channel_stats[ch] = {
                    'name': ch,
                    'video_count': 0,
                    'total_views': 0,
                    'total_likes': 0,
                    'videos': []
                }
            channel_stats[ch]['video_count'] += 1
            channel_stats[ch]['total_views'] += v.get('views', 0)
            channel_stats[ch]['total_likes'] += v.get('likes', 0) or 0

        channels = []
        for ch in channel_stats.values():
            ch['avg_views'] = int(ch['total_views'] / ch['video_count'])
            del ch['videos']
            channels.append(ch)

        return sorted(channels, key=lambda x: x['total_views'], reverse=True)

    def _render_html(self, data: Dict) -> str:
        """渲染 HTML - v3 咨询框架可视化版"""
        meta = data['meta']
        stats = data['stats']
        patterns = data['patterns']
        opportunities = data['opportunities']
        trends = data['trends']
        channels = data['channels']
        executive_summary = data['executive_summary']
        bcg_matrix = data['bcg_matrix']
        five_forces = data['five_forces']
        ge_matrix = data['ge_matrix']

        # 转换为 JSON
        videos_json = json.dumps(data['videos'], ensure_ascii=False, default=str)
        patterns_json = json.dumps(patterns, ensure_ascii=False)
        opportunities_json = json.dumps(opportunities, ensure_ascii=False)
        trends_json = json.dumps(trends, ensure_ascii=False)
        channels_json = json.dumps(channels[:50], ensure_ascii=False)
        executive_summary_json = json.dumps(executive_summary, ensure_ascii=False)
        bcg_matrix_json = json.dumps(bcg_matrix, ensure_ascii=False)
        five_forces_json = json.dumps(five_forces, ensure_ascii=False)
        ge_matrix_json = json.dumps(ge_matrix, ensure_ascii=False)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>调研洞察 - {meta['theme']} | {meta['generated_at'][:10]}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}

        /* 头部 */
        .header {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 20px 40px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 22px; font-weight: 600; }}
        .header-meta {{ font-size: 13px; opacity: 0.9; margin-top: 4px; }}

        /* 时间过滤器 */
        .time-filter {{
            display: flex;
            gap: 8px;
        }}
        .time-btn {{
            padding: 6px 14px;
            border: 1px solid rgba(255,255,255,0.4);
            background: rgba(255,255,255,0.1);
            color: white;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}
        .time-btn:hover {{ background: rgba(255,255,255,0.2); }}
        .time-btn.active {{
            background: white;
            color: #6366f1;
            font-weight: 600;
        }}

        /* 标签页 */
        .tabs {{
            background: white;
            border-bottom: 1px solid #e5e7eb;
            padding: 0 40px;
            display: flex;
        }}
        .tab {{
            padding: 14px 24px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            font-weight: 500;
            color: #6b7280;
            transition: all 0.2s;
        }}
        .tab:hover {{ color: #6366f1; }}
        .tab.active {{
            color: #6366f1;
            border-bottom-color: #6366f1;
        }}

        /* 内容区 */
        .content {{ padding: 24px 40px; max-width: 1600px; margin: 0 auto; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* 卡片 */
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .card-label {{ font-size: 12px; color: #6b7280; margin-bottom: 4px; }}
        .card-value {{ font-size: 24px; font-weight: 700; color: #111; }}
        .card-sub {{ font-size: 11px; color: #9ca3af; margin-top: 2px; }}
        .card.primary {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
        }}
        .card.primary .card-label {{ color: rgba(255,255,255,0.8); }}
        .card.primary .card-value {{ color: white; }}
        .card.primary .card-sub {{ color: rgba(255,255,255,0.7); }}

        /* 洞察卡片 */
        .insight-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .insight-title {{
            font-size: 15px;
            font-weight: 600;
            color: #111;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .insight-title::before {{
            content: '';
            width: 4px;
            height: 18px;
            background: #6366f1;
            border-radius: 2px;
        }}
        .insight-text {{
            font-size: 14px;
            color: #4b5563;
            padding: 12px 16px;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 3px solid #6366f1;
        }}
        .insight-list {{
            list-style: none;
            padding: 0;
        }}
        .insight-list li {{
            padding: 10px 0;
            border-bottom: 1px solid #f3f4f6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .insight-list li:last-child {{ border-bottom: none; }}

        /* 图表容器 */
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
        .chart-wrapper {{ position: relative; height: 280px; }}

        /* 网格布局 */
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        @media (max-width: 1200px) {{
            .grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @media (max-width: 900px) {{
            .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
        }}

        /* 表格 */
        .table-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .table-header {{
            padding: 16px 20px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .table-title {{ font-size: 15px; font-weight: 600; }}
        .table-tools {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}

        .search-box {{
            padding: 8px 12px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 13px;
            width: 200px;
        }}
        .search-box:focus {{ outline: none; border-color: #6366f1; }}

        .sort-select {{
            padding: 8px 12px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 13px;
            background: white;
        }}

        .btn {{
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: #6366f1;
            color: white;
            border: none;
        }}
        .btn-primary:hover {{ background: #4f46e5; }}
        .btn-secondary {{
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
        }}
        .btn-secondary:hover {{ background: #f9fafb; }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .data-table th,
        .data-table td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #f3f4f6;
            font-size: 13px;
        }}
        .data-table th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
            cursor: pointer;
            white-space: nowrap;
        }}
        .data-table th:hover {{ background: #f3f4f6; }}
        .data-table tbody tr:hover {{ background: #f9fafb; }}

        .video-title {{
            max-width: 350px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .video-link {{
            color: #6366f1;
            text-decoration: none;
        }}
        .video-link:hover {{ text-decoration: underline; }}

        /* 分页 */
        .pagination {{
            padding: 16px 20px;
            border-top: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .page-info {{ font-size: 13px; color: #6b7280; }}
        .page-btns {{ display: flex; gap: 6px; }}
        .page-btn {{
            padding: 6px 12px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            background: white;
            font-size: 13px;
            cursor: pointer;
        }}
        .page-btn:hover {{ background: #f9fafb; }}
        .page-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .page-btn.active {{ background: #6366f1; color: white; border-color: #6366f1; }}

        /* 徽章 */
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 500;
        }}
        .badge-purple {{ background: #ede9fe; color: #6d28d9; }}
        .badge-green {{ background: #dcfce7; color: #16a34a; }}
        .badge-blue {{ background: #dbeafe; color: #2563eb; }}
        .badge-orange {{ background: #ffedd5; color: #ea580c; }}
        .badge-red {{ background: #fee2e2; color: #dc2626; }}

        /* 数字 */
        .num {{ font-variant-numeric: tabular-nums; }}

        /* 机会视频卡片 */
        .opportunity-video {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f3f4f6;
        }}
        .opportunity-video:last-child {{ border-bottom: none; }}
        .opportunity-video-info {{
            flex: 1;
            min-width: 0;
        }}
        .opportunity-video-title {{
            font-size: 13px;
            color: #111;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .opportunity-video-meta {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 2px;
        }}
        .opportunity-video-stats {{
            text-align: right;
            margin-left: 16px;
        }}
        .opportunity-video-views {{
            font-size: 14px;
            font-weight: 600;
            color: #111;
        }}
        .opportunity-video-growth {{
            font-size: 12px;
            color: #16a34a;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div>
                <h1>调研洞察 - {meta['theme']}</h1>
                <div class="header-meta">{stats['total_videos']:,} 个视频 · {stats['total_channels']} 个频道 · 生成于 {meta['generated_at'][:16]}</div>
            </div>
            <div class="time-filter">
                <button class="time-btn {'active' if meta['time_window'] == '1天内' else ''}" onclick="reloadWithFilter('1天内')">1天内</button>
                <button class="time-btn {'active' if meta['time_window'] == '15天内' else ''}" onclick="reloadWithFilter('15天内')">15天内</button>
                <button class="time-btn {'active' if meta['time_window'] == '30天内' else ''}" onclick="reloadWithFilter('30天内')">30天内</button>
                <button class="time-btn {'active' if meta['time_window'] == '全部' else ''}" onclick="reloadWithFilter('全部')">全部</button>
            </div>
        </div>
    </div>

    <div class="tabs">
        <div class="tab active" onclick="showTab('summary')">执行摘要</div>
        <div class="tab" onclick="showTab('strategy')">战略分析</div>
        <div class="tab" onclick="showTab('opportunities')">机会识别</div>
        <div class="tab" onclick="showTab('patterns')">模式洞察</div>
        <div class="tab" onclick="showTab('data')">数据浏览</div>
    </div>

    <div class="content">
        <!-- 执行摘要页 - 金字塔原理 -->
        <div id="summary" class="tab-content active">
            <!-- 核心结论 -->
            <div class="insight-card" style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white;">
                <div style="font-size: 13px; opacity: 0.9; margin-bottom: 8px;">核心结论</div>
                <div style="font-size: 20px; font-weight: 600;" id="coreConclusion"></div>
            </div>

            <!-- 关键指标 -->
            <div class="cards">
                <div class="card">
                    <div class="card-label">样本量</div>
                    <div class="card-value num">{stats['total_videos']:,}</div>
                </div>
                <div class="card">
                    <div class="card-label">频道数</div>
                    <div class="card-value num">{five_forces['metrics']['total_channels']}</div>
                </div>
                <div class="card">
                    <div class="card-label">HHI 指数</div>
                    <div class="card-value num">{five_forces['metrics']['hhi']:.0f}</div>
                    <div class="card-sub">{five_forces['interpretation']['competition']}</div>
                </div>
                <div class="card">
                    <div class="card-label">CR10</div>
                    <div class="card-value num">{five_forces['metrics']['cr10']}%</div>
                    <div class="card-sub">头部10频道占比</div>
                </div>
                <div class="card">
                    <div class="card-label">潜力机会</div>
                    <div class="card-value num">{bcg_matrix['summary']['question_marks']}</div>
                    <div class="card-sub">小频道爆款</div>
                </div>
                <div class="card">
                    <div class="card-label">最佳时长</div>
                    <div class="card-value" style="font-size: 18px;">{patterns['duration']['best_duration'][:8]}</div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 三大洞察 -->
                <div class="insight-card">
                    <div class="insight-title">关键发现</div>
                    <div id="insightsList" style="display: flex; flex-direction: column; gap: 12px;"></div>
                </div>

                <!-- 行动建议 -->
                <div class="insight-card">
                    <div class="insight-title">行动建议</div>
                    <div id="actionsList"></div>
                </div>
            </div>
        </div>

        <!-- 战略分析页 - BCG + 五力 + 集中度 -->
        <div id="strategy" class="tab-content">
            <div class="grid-2">
                <!-- BCG 四象限散点图 -->
                <div class="insight-card">
                    <div class="insight-title">BCG 内容矩阵</div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">
                        X轴: 频道规模 | Y轴: 播放量 | 分界线: 频道规模中位数={bcg_matrix['thresholds']['channel_size_median']}，播放量均值={self._format_number(bcg_matrix['thresholds']['global_avg_views'])}
                    </p>
                    <div class="chart-wrapper" style="height: 350px;">
                        <canvas id="bcgScatterChart"></canvas>
                    </div>
                    <div style="display: flex; gap: 16px; margin-top: 12px; font-size: 12px;">
                        <span><span style="display: inline-block; width: 12px; height: 12px; background: #22c55e; border-radius: 50%;"></span> 爆款模板 ({bcg_matrix['summary']['stars']})</span>
                        <span><span style="display: inline-block; width: 12px; height: 12px; background: #eab308; border-radius: 50%;"></span> 潜力机会 ({bcg_matrix['summary']['question_marks']})</span>
                        <span><span style="display: inline-block; width: 12px; height: 12px; background: #6366f1; border-radius: 50%;"></span> 稳定流量 ({bcg_matrix['summary']['cash_cows']})</span>
                        <span><span style="display: inline-block; width: 12px; height: 12px; background: #9ca3af; border-radius: 50%;"></span> 避免区域 ({bcg_matrix['summary']['dogs']})</span>
                    </div>
                </div>

                <!-- 五力分析雷达图 -->
                <div class="insight-card">
                    <div class="insight-title">五力分析雷达图</div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">
                        评估创作者进入该领域面临的竞争态势（分值越高，该力量越强）
                    </p>
                    <div class="chart-wrapper" style="height: 300px;">
                        <canvas id="fiveForceRadar"></canvas>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px; font-size: 12px;">
                        <div><strong>行业竞争:</strong> {five_forces['interpretation']['competition']}</div>
                        <div><strong>新进入者:</strong> {five_forces['interpretation']['new_entrants']}</div>
                        <div><strong>观众参与:</strong> {five_forces['interpretation']['buyers']}</div>
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 市场集中度仪表盘 -->
                <div class="insight-card">
                    <div class="insight-title">市场集中度</div>
                    <div style="display: flex; gap: 24px; margin-bottom: 16px;">
                        <div style="text-align: center;">
                            <div style="font-size: 36px; font-weight: 700; color: #6366f1;">{five_forces['metrics']['cr4']:.1f}%</div>
                            <div style="font-size: 12px; color: #6b7280;">CR4 (Top4占比)</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 36px; font-weight: 700; color: #8b5cf6;">{five_forces['metrics']['cr10']:.1f}%</div>
                            <div style="font-size: 12px; color: #6b7280;">CR10 (Top10占比)</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 36px; font-weight: 700; color: #a78bfa;">{five_forces['metrics']['hhi']:.0f}</div>
                            <div style="font-size: 12px; color: #6b7280;">HHI 指数</div>
                        </div>
                    </div>
                    <div class="insight-text">
                        HHI &lt; 1500 = 竞争激烈（机会多）<br>
                        HHI 1500-2500 = 中度集中<br>
                        HHI &gt; 2500 = 高度集中（头部垄断）
                    </div>
                </div>

                <!-- Top 10 频道 -->
                <div class="insight-card">
                    <div class="insight-title">Top 10 频道</div>
                    <table class="data-table">
                        <thead>
                            <tr><th>频道</th><th>视频数</th><th>播放量占比</th></tr>
                        </thead>
                        <tbody id="topChannelsList"></tbody>
                    </table>
                </div>
            </div>

            <!-- GE-McKinsey 9格矩阵 -->
            <div class="insight-card">
                <div class="insight-title">GE-McKinsey 投资决策矩阵</div>
                <p style="font-size: 13px; color: #6b7280; margin-bottom: 16px;">
                    按视频时长分析不同内容类型的投资价值（市场吸引力 × 竞争优势）
                </p>
                <div id="geMatrixGrid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;"></div>
            </div>
        </div>

        <!-- 模式洞察页 -->
        <div id="patterns" class="tab-content">
            <div class="cards">
                <div class="card primary">
                    <div class="card-label">样本量</div>
                    <div class="card-value num">{stats['total_videos']:,}</div>
                </div>
                <div class="card">
                    <div class="card-label">总播放量</div>
                    <div class="card-value num">{self._format_number(stats['total_views'])}</div>
                </div>
                <div class="card">
                    <div class="card-label">平均播放</div>
                    <div class="card-value num">{self._format_number(stats['avg_views'])}</div>
                    <div class="card-sub">中位数: {self._format_number(stats['median_views'])}</div>
                </div>
                <div class="card">
                    <div class="card-label">爆款门槛</div>
                    <div class="card-value num">{self._format_number(patterns['viral']['viral_threshold'])}</div>
                    <div class="card-sub">Top 5% ({patterns['viral']['viral_count']} 个)</div>
                </div>
                <div class="card">
                    <div class="card-label">频道数</div>
                    <div class="card-value num">{stats['total_channels']}</div>
                </div>
                <div class="card">
                    <div class="card-label">Top10 集中度</div>
                    <div class="card-value num">{patterns['channel']['top10_share']}%</div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 标题模式 -->
                <div class="insight-card">
                    <div class="insight-title">标题触发词效果</div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">含这些词的视频播放量是不含的多少倍</p>
                    <ul class="insight-list" id="triggerWordsList"></ul>
                </div>

                <!-- 时长表现 -->
                <div class="insight-card">
                    <div class="insight-title">时长与播放量关系</div>
                    <div class="insight-text">{patterns['duration']['insight']}</div>
                    <div class="chart-wrapper" style="height: 200px; margin-top: 16px;">
                        <canvas id="durationChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 爆款特征 -->
                <div class="insight-card">
                    <div class="insight-title">爆款 vs 普通视频特征对比</div>
                    <table class="data-table">
                        <thead>
                            <tr><th>特征</th><th>爆款 (Top 5%)</th><th>普通视频</th></tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>平均标题长度</td>
                                <td class="num">{patterns['viral']['avg_title_length']['viral']} 字</td>
                                <td class="num">{patterns['viral']['avg_title_length']['normal']} 字</td>
                            </tr>
                            <tr>
                                <td>平均时长</td>
                                <td class="num">{patterns['viral']['avg_duration']['viral'] // 60} 分钟</td>
                                <td class="num">{patterns['viral']['avg_duration']['normal'] // 60} 分钟</td>
                            </tr>
                            <tr>
                                <td>平均互动率</td>
                                <td class="num">{patterns['viral']['avg_engagement']['viral']}%</td>
                                <td class="num">{patterns['viral']['avg_engagement']['normal']}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- 频道格局 -->
                <div class="insight-card">
                    <div class="insight-title">频道规模分布</div>
                    <div class="insight-text">{patterns['channel']['insight']}</div>
                    <div class="chart-wrapper" style="height: 200px; margin-top: 16px;">
                        <canvas id="channelSizeChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- 标题关键词 -->
            <div class="insight-card">
                <div class="insight-title">高频标题关键词 Top 20</div>
                <div class="chart-wrapper" style="height: 250px;">
                    <canvas id="keywordsChart"></canvas>
                </div>
            </div>
        </div>

        <!-- 机会发现页 -->
        <div id="opportunities" class="tab-content">
            <div class="cards">
                <div class="card primary">
                    <div class="card-label">小频道爆款</div>
                    <div class="card-value num">{opportunities['small_channel_hits']['count']}</div>
                    <div class="card-sub">频道视频≤3 且高播放</div>
                </div>
                <div class="card">
                    <div class="card-label">近期爆款</div>
                    <div class="card-value num">{opportunities['recent_viral']['count']}</div>
                    <div class="card-sub">7天内发布，日增>1000</div>
                </div>
                <div class="card">
                    <div class="card-label">高互动视频</div>
                    <div class="card-value num">{opportunities['high_engagement']['count']}</div>
                    <div class="card-sub">互动率 > 3%</div>
                </div>
                <div class="card">
                    <div class="card-label">潜力视频</div>
                    <div class="card-value num">{opportunities['growing']['count']}</div>
                    <div class="card-sub">1万-50万播放，日增>500</div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 小频道爆款 -->
                <div class="insight-card">
                    <div class="insight-title">小频道爆款 <span class="badge badge-purple">{opportunities['small_channel_hits']['count']} 个</span></div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">{opportunities['small_channel_hits']['insight']}</p>
                    <div id="smallChannelList" style="max-height: 400px; overflow-y: auto;"></div>
                </div>

                <!-- 近期爆款 -->
                <div class="insight-card">
                    <div class="insight-title">近期爆款 <span class="badge badge-green">{opportunities['recent_viral']['count']} 个</span></div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">{opportunities['recent_viral']['insight']}</p>
                    <div id="recentViralList" style="max-height: 400px; overflow-y: auto;"></div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 高互动 -->
                <div class="insight-card">
                    <div class="insight-title">高互动视频 <span class="badge badge-blue">{opportunities['high_engagement']['count']} 个</span></div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">{opportunities['high_engagement']['insight']}</p>
                    <div id="highEngagementList" style="max-height: 400px; overflow-y: auto;"></div>
                </div>

                <!-- 潜力视频 -->
                <div class="insight-card">
                    <div class="insight-title">潜力视频 <span class="badge badge-orange">{opportunities['growing']['count']} 个</span></div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">{opportunities['growing']['insight']}</p>
                    <div id="growingList" style="max-height: 400px; overflow-y: auto;"></div>
                </div>
            </div>
        </div>

        <!-- 趋势追踪页 -->
        <div id="trends" class="tab-content">
            <div class="grid-2">
                <!-- 时间分布 -->
                <div class="insight-card">
                    <div class="insight-title">视频时间分布</div>
                    <div class="chart-wrapper">
                        <canvas id="timeDistChart"></canvas>
                    </div>
                </div>

                <!-- 各时段表现 -->
                <div class="insight-card">
                    <div class="insight-title">各时段平均表现</div>
                    <div class="chart-wrapper">
                        <canvas id="timePerformanceChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 上升关键词 -->
                <div class="insight-card">
                    <div class="insight-title">热度上升关键词 <span class="badge badge-green">近期更热</span></div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">近30天内相比更早期，这些词出现频率明显上升</p>
                    <ul class="insight-list" id="risingKeywordsList"></ul>
                </div>

                <!-- 下降关键词 -->
                <div class="insight-card">
                    <div class="insight-title">热度下降关键词 <span class="badge badge-red">关注度降低</span></div>
                    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">近30天内相比更早期，这些词出现频率明显下降</p>
                    <ul class="insight-list" id="fallingKeywordsList"></ul>
                </div>
            </div>
        </div>

        <!-- 数据浏览页 -->
        <div id="data" class="tab-content">
            <div class="table-container">
                <div class="table-header">
                    <div class="table-title">全部视频数据 <span id="filteredCount">({stats['total_videos']:,} 条)</span></div>
                    <div class="table-tools">
                        <input type="text" class="search-box" id="searchInput" placeholder="搜索标题或频道..." oninput="searchVideos()">
                        <select class="sort-select" id="sortSelect" onchange="sortVideos()">
                            <option value="views_desc">播放量 ↓</option>
                            <option value="views_asc">播放量 ↑</option>
                            <option value="daily_desc">日增长 ↓</option>
                            <option value="engagement_desc">互动率 ↓</option>
                            <option value="date_desc">最新发布</option>
                        </select>
                        <select class="sort-select" id="timeBucketFilter" onchange="filterByTimeBucket()">
                            <option value="">全部时间</option>
                            <option value="24小时内">24小时内</option>
                            <option value="7天内">7天内</option>
                            <option value="30天内">30天内</option>
                            <option value="90天内">90天内</option>
                            <option value="90天以上">90天以上</option>
                        </select>
                        <button class="btn btn-primary" onclick="exportCSV()">导出 CSV</button>
                    </div>
                </div>
                <div style="overflow-x: auto;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th style="width: 40px;">#</th>
                                <th style="min-width: 300px;">标题</th>
                                <th>频道</th>
                                <th>播放量</th>
                                <th>日增长</th>
                                <th>互动率</th>
                                <th>时长</th>
                                <th>时间段</th>
                            </tr>
                        </thead>
                        <tbody id="videoTableBody"></tbody>
                    </table>
                </div>
                <div class="pagination">
                    <div class="page-info">
                        <span id="pageInfo">第 1 页</span>，
                        共 <span id="totalPages">1</span> 页，
                        每页 <select id="pageSizeSelect" onchange="changePageSize()" style="padding: 2px 6px; border: 1px solid #e5e7eb; border-radius: 4px;">
                            <option value="20">20</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                        </select> 条
                    </div>
                    <div class="page-btns">
                        <button class="page-btn" onclick="goToPage(1)">首页</button>
                        <button class="page-btn" id="prevBtn" onclick="prevPage()">上一页</button>
                        <span id="pageNumbers"></span>
                        <button class="page-btn" id="nextBtn" onclick="nextPage()">下一页</button>
                        <button class="page-btn" onclick="goToPage(totalPagesCount)">末页</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 全局数据
        const ALL_VIDEOS = {videos_json};
        const PATTERNS = {patterns_json};
        const OPPORTUNITIES = {opportunities_json};
        const TRENDS = {trends_json};
        const CHANNELS = {channels_json};
        const EXECUTIVE_SUMMARY = {executive_summary_json};
        const BCG_MATRIX = {bcg_matrix_json};
        const FIVE_FORCES = {five_forces_json};
        const GE_MATRIX = {ge_matrix_json};

        let filteredVideos = [...ALL_VIDEOS];
        let currentPage = 1;
        let pageSize = 20;
        let totalPagesCount = Math.ceil(ALL_VIDEOS.length / pageSize);

        // 格式化数字
        function formatNumber(num) {{
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toString();
        }}

        // 格式化时长
        function formatDuration(seconds) {{
            if (!seconds) return '-';
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return mins + ':' + String(secs).padStart(2, '0');
        }}

        // 标签页切换
        function showTab(tabId) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`[onclick="showTab('${{tabId}}')"]`).classList.add('active');
            document.getElementById(tabId).classList.add('active');

            if (tabId === 'summary') initExecutiveSummary();
            if (tabId === 'strategy') initStrategyCharts();
            if (tabId === 'patterns') initPatternCharts();
            if (tabId === 'opportunities') initOpportunityLists();
            if (tabId === 'data') renderVideoTable();
        }}

        // ========== 执行摘要初始化 ==========
        function initExecutiveSummary() {{
            // 核心结论
            document.getElementById('coreConclusion').textContent = EXECUTIVE_SUMMARY.core_conclusion;

            // 洞察列表
            const insightsList = document.getElementById('insightsList');
            insightsList.innerHTML = EXECUTIVE_SUMMARY.insights.map(insight => `
                <div style="padding: 12px 16px; background: #f9fafb; border-radius: 8px; border-left: 3px solid #6366f1;">
                    <div style="font-size: 14px; font-weight: 600; color: #111; margin-bottom: 4px;">
                        ${{insight.icon}} ${{insight.title}}
                    </div>
                    <div style="font-size: 13px; color: #4b5563;">${{insight.detail}}</div>
                </div>
            `).join('');

            // 行动建议
            const actionsList = document.getElementById('actionsList');
            actionsList.innerHTML = `<ol style="padding-left: 20px; margin: 0;">` +
                EXECUTIVE_SUMMARY.actions.map(action => `
                    <li style="padding: 8px 0; border-bottom: 1px solid #f3f4f6; font-size: 14px; color: #374151;">
                        ${{action}}
                    </li>
                `).join('') + `</ol>`;
        }}

        // ========== 战略分析图表初始化 ==========
        function initStrategyCharts() {{
            initBCGScatterChart();
            initFiveForceRadar();
            initTopChannelsList();
            initGEMatrixGrid();
        }}

        // BCG 散点图
        function initBCGScatterChart() {{
            if (window.bcgChart) return;

            const ctx = document.getElementById('bcgScatterChart');
            const scatterData = BCG_MATRIX.scatter_data;

            // 按象限分组数据
            const quadrantColors = {{
                'stars': '#22c55e',
                'question_marks': '#eab308',
                'cash_cows': '#6366f1',
                'dogs': '#9ca3af'
            }};

            const datasets = Object.entries(quadrantColors).map(([quadrant, color]) => ({{
                label: quadrant,
                data: scatterData.filter(d => d.quadrant === quadrant).map(d => ({{
                    x: d.x,
                    y: d.y,
                    title: d.title,
                    channel: d.channel
                }})),
                backgroundColor: color,
                pointRadius: 5,
                pointHoverRadius: 8
            }}));

            window.bcgChart = new Chart(ctx, {{
                type: 'scatter',
                data: {{ datasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const point = context.raw;
                                    return [
                                        point.title,
                                        `频道: ${{point.channel}}`,
                                        `播放量: ${{formatNumber(point.y)}}`
                                    ];
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            title: {{ display: true, text: '频道视频数量' }},
                            type: 'logarithmic'
                        }},
                        y: {{
                            title: {{ display: true, text: '播放量' }},
                            type: 'logarithmic'
                        }}
                    }}
                }}
            }});
        }}

        // 五力分析雷达图
        function initFiveForceRadar() {{
            if (window.fiveForceChart) return;

            const ctx = document.getElementById('fiveForceRadar');
            const scores = FIVE_FORCES.radar_scores;

            window.fiveForceChart = new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: ['行业竞争', '新进入者威胁', '替代品威胁', '观众议价能力', '制作成本压力'],
                    datasets: [{{
                        label: '竞争态势评分',
                        data: [
                            scores.competition,
                            scores.new_entrants,
                            scores.substitutes,
                            scores.buyers,
                            scores.suppliers
                        ],
                        backgroundColor: 'rgba(99, 102, 241, 0.2)',
                        borderColor: '#6366f1',
                        borderWidth: 2,
                        pointBackgroundColor: '#6366f1'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        r: {{
                            beginAtZero: true,
                            max: 100,
                            ticks: {{ stepSize: 20 }}
                        }}
                    }}
                }}
            }});
        }}

        // Top 10 频道列表
        function initTopChannelsList() {{
            const tbody = document.getElementById('topChannelsList');
            tbody.innerHTML = FIVE_FORCES.top_channels.slice(0, 10).map(ch => `
                <tr>
                    <td style="max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${{ch.name}}</td>
                    <td class="num">${{ch.video_count}}</td>
                    <td><span class="badge badge-purple">${{ch.share}}%</span></td>
                </tr>
            `).join('');
        }}

        // GE 矩阵网格
        function initGEMatrixGrid() {{
            const grid = document.getElementById('geMatrixGrid');
            grid.innerHTML = GE_MATRIX.matrix.map(item => `
                <div style="background: white; border-radius: 8px; padding: 16px; border-left: 4px solid ${{item.color}};">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: #111;">${{item.bucket}}</div>
                        <span class="badge" style="background: ${{item.color}}20; color: ${{item.color}};">${{item.recommendation}}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 12px; color: #6b7280;">
                        <div>视频数: <strong>${{item.video_count}}</strong></div>
                        <div>平均播放: <strong>${{formatNumber(item.avg_views)}}</strong></div>
                        <div>市场吸引力: <strong>${{['低', '中', '高'][item.market_attractiveness - 1]}}</strong></div>
                        <div>竞争优势: <strong>${{['低', '中', '高'][item.competitive_strength - 1]}}</strong></div>
                    </div>
                </div>
            `).join('');
        }}

        // 重新加载（带时间过滤）
        function reloadWithFilter(timeWindow) {{
            alert(`请重新运行命令: python src/research/research_report.py --time-window "${{timeWindow}}"`);
        }}

        // ========== 模式洞察图表 ==========
        function initPatternCharts() {{
            // 触发词列表
            const triggerList = document.getElementById('triggerWordsList');
            const triggers = PATTERNS.title.trigger_words;
            triggerList.innerHTML = Object.entries(triggers)
                .sort((a, b) => b[1].multiplier - a[1].multiplier)
                .slice(0, 8)
                .map(([word, data]) => `
                    <li>
                        <span>"${{word}}" <span style="color: #9ca3af;">(${{data.count}} 个视频)</span></span>
                        <span class="badge ${{data.multiplier > 1.5 ? 'badge-green' : 'badge-blue'}}">${{data.multiplier}}x</span>
                    </li>
                `).join('');

            // 时长图表
            if (!window.durationChart) {{
                const ctx = document.getElementById('durationChart');
                const durData = PATTERNS.duration.buckets;
                window.durationChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: Object.keys(durData),
                        datasets: [{{
                            label: '平均播放量',
                            data: Object.values(durData).map(d => d.avg_views),
                            backgroundColor: '#6366f1'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ y: {{ beginAtZero: true }} }}
                    }}
                }});
            }}

            // 频道规模图表
            if (!window.channelSizeChart) {{
                const ctx = document.getElementById('channelSizeChart');
                const sizeData = PATTERNS.channel.size_distribution;
                window.channelSizeChart = new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: Object.keys(sizeData),
                        datasets: [{{
                            data: Object.values(sizeData),
                            backgroundColor: ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'right' }} }}
                    }}
                }});
            }}

            // 关键词图表
            if (!window.keywordsChart) {{
                const ctx = document.getElementById('keywordsChart');
                const keywords = PATTERNS.title.top_keywords.slice(0, 20);
                window.keywordsChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: keywords.map(k => k[0]),
                        datasets: [{{
                            label: '出现次数',
                            data: keywords.map(k => k[1]),
                            backgroundColor: '#6366f1'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}
        }}

        // ========== 机会发现列表 ==========
        function initOpportunityLists() {{
            renderOpportunityList('smallChannelList', OPPORTUNITIES.small_channel_hits.videos);
            renderOpportunityList('recentViralList', OPPORTUNITIES.recent_viral.videos);
            renderOpportunityList('highEngagementList', OPPORTUNITIES.high_engagement.videos);
            renderOpportunityList('growingList', OPPORTUNITIES.growing.videos);
        }}

        function renderOpportunityList(containerId, videos) {{
            const container = document.getElementById(containerId);
            container.innerHTML = videos.slice(0, 15).map(v => `
                <div class="opportunity-video">
                    <div class="opportunity-video-info">
                        <div class="opportunity-video-title">
                            <a href="${{v.url || '#'}}" target="_blank" class="video-link">${{v.title || '无标题'}}</a>
                        </div>
                        <div class="opportunity-video-meta">${{v.channel_name || '未知频道'}} · ${{v.time_bucket || ''}}</div>
                    </div>
                    <div class="opportunity-video-stats">
                        <div class="opportunity-video-views">${{formatNumber(v.views)}}</div>
                        <div class="opportunity-video-growth">日增 ${{formatNumber(v.daily_growth || 0)}}</div>
                    </div>
                </div>
            `).join('');
        }}

        // ========== 趋势图表 ==========
        function initTrendCharts() {{
            // 时间分布
            if (!window.timeDistChart) {{
                const ctx = document.getElementById('timeDistChart');
                const timeDist = TRENDS.time_distribution;
                const order = ['24小时内', '7天内', '30天内', '90天内', '90天以上', '未知'];
                const sortedLabels = order.filter(k => timeDist[k] !== undefined);
                window.timeDistChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: sortedLabels,
                        datasets: [{{
                            label: '视频数',
                            data: sortedLabels.map(k => timeDist[k]),
                            backgroundColor: '#6366f1'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}

            // 各时段表现
            if (!window.timePerformanceChart) {{
                const ctx = document.getElementById('timePerformanceChart');
                const perf = TRENDS.time_performance;
                const order = ['24小时内', '7天内', '30天内', '90天内', '90天以上'];
                const sortedLabels = order.filter(k => perf[k]);
                window.timePerformanceChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: sortedLabels,
                        datasets: [{{
                            label: '平均播放量',
                            data: sortedLabels.map(k => perf[k]?.avg_views || 0),
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.1)',
                            fill: true,
                            tension: 0.3
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false
                    }}
                }});
            }}

            // 上升关键词
            const risingList = document.getElementById('risingKeywordsList');
            risingList.innerHTML = TRENDS.rising_keywords.slice(0, 8).map(([word, count, ratio]) => `
                <li>
                    <span>"${{word}}" <span style="color: #9ca3af;">(${{count}} 次)</span></span>
                    <span class="badge badge-green">↑ ${{ratio}}x</span>
                </li>
            `).join('') || '<li style="color: #9ca3af;">暂无数据</li>';

            // 下降关键词
            const fallingList = document.getElementById('fallingKeywordsList');
            fallingList.innerHTML = TRENDS.falling_keywords.slice(0, 8).map(([word, count, ratio]) => `
                <li>
                    <span>"${{word}}" <span style="color: #9ca3af;">(${{count}} 次)</span></span>
                    <span class="badge badge-red">↓ ${{ratio}}x</span>
                </li>
            `).join('') || '<li style="color: #9ca3af;">暂无数据</li>';
        }}

        // ========== 数据浏览 ==========
        function renderVideoTable() {{
            const start = (currentPage - 1) * pageSize;
            const end = start + pageSize;
            const pageData = filteredVideos.slice(start, end);

            const tbody = document.getElementById('videoTableBody');
            tbody.innerHTML = pageData.map((v, i) => `
                <tr>
                    <td>${{start + i + 1}}</td>
                    <td class="video-title">
                        <a href="${{v.url || '#'}}" target="_blank" class="video-link">${{(v.title || '').substring(0, 60)}}</a>
                    </td>
                    <td style="white-space: nowrap;">${{(v.channel_name || '').substring(0, 15)}}</td>
                    <td class="num">${{(v.views || 0).toLocaleString()}}</td>
                    <td class="num">${{(v.daily_growth || 0).toLocaleString()}}</td>
                    <td class="num">${{v.engagement_rate || 0}}%</td>
                    <td>${{formatDuration(v.duration)}}</td>
                    <td><span class="badge badge-purple">${{v.time_bucket || '未知'}}</span></td>
                </tr>
            `).join('');

            updatePagination();
        }}

        function updatePagination() {{
            totalPagesCount = Math.ceil(filteredVideos.length / pageSize);
            document.getElementById('pageInfo').textContent = `第 ${{currentPage}} 页`;
            document.getElementById('totalPages').textContent = totalPagesCount;
            document.getElementById('filteredCount').textContent = `(${{filteredVideos.length.toLocaleString()}} 条)`;
            document.getElementById('prevBtn').disabled = currentPage <= 1;
            document.getElementById('nextBtn').disabled = currentPage >= totalPagesCount;

            // 页码按钮
            const pageNumbers = document.getElementById('pageNumbers');
            let html = '';
            const maxShow = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxShow / 2));
            let endPage = Math.min(totalPagesCount, startPage + maxShow - 1);
            if (endPage - startPage < maxShow - 1) startPage = Math.max(1, endPage - maxShow + 1);

            for (let i = startPage; i <= endPage; i++) {{
                html += `<button class="page-btn ${{i === currentPage ? 'active' : ''}}" onclick="goToPage(${{i}})">${{i}}</button>`;
            }}
            pageNumbers.innerHTML = html;
        }}

        function searchVideos() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const timeBucket = document.getElementById('timeBucketFilter').value;

            filteredVideos = ALL_VIDEOS.filter(v => {{
                const matchQuery = !query ||
                    (v.title || '').toLowerCase().includes(query) ||
                    (v.channel_name || '').toLowerCase().includes(query);
                const matchTime = !timeBucket || v.time_bucket === timeBucket;
                return matchQuery && matchTime;
            }});

            currentPage = 1;
            sortVideos();
        }}

        function filterByTimeBucket() {{
            searchVideos();
        }}

        function sortVideos() {{
            const sortBy = document.getElementById('sortSelect').value;
            filteredVideos.sort((a, b) => {{
                switch(sortBy) {{
                    case 'views_desc': return (b.views || 0) - (a.views || 0);
                    case 'views_asc': return (a.views || 0) - (b.views || 0);
                    case 'daily_desc': return (b.daily_growth || 0) - (a.daily_growth || 0);
                    case 'engagement_desc': return (b.engagement_rate || 0) - (a.engagement_rate || 0);
                    case 'date_desc': return new Date(b.published_at || 0) - new Date(a.published_at || 0);
                    default: return 0;
                }}
            }});
            renderVideoTable();
        }}

        function prevPage() {{ if (currentPage > 1) {{ currentPage--; renderVideoTable(); }} }}
        function nextPage() {{ if (currentPage < totalPagesCount) {{ currentPage++; renderVideoTable(); }} }}
        function goToPage(page) {{ currentPage = page; renderVideoTable(); }}
        function changePageSize() {{
            pageSize = parseInt(document.getElementById('pageSizeSelect').value);
            currentPage = 1;
            renderVideoTable();
        }}

        function exportCSV() {{
            const headers = ['标题', '频道', 'URL', '播放量', '点赞', '评论', '日增长', '互动率', '时长', '时间段', '发布时间'];
            const rows = filteredVideos.map(v => [
                v.title, v.channel_name, v.url, v.views, v.likes, v.comments,
                v.daily_growth, v.engagement_rate, v.duration, v.time_bucket, v.published_at
            ]);
            const csvContent = [headers.join(','), ...rows.map(r => r.map(c => `"${{c || ''}}"`).join(','))].join('\\n');
            const blob = new Blob(['\\uFEFF' + csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'research_data.csv';
            link.click();
        }}

        // 初始化
        document.addEventListener('DOMContentLoaded', function() {{
            initExecutiveSummary();  // 默认显示执行摘要
        }});
    </script>
</body>
</html>'''

    def _format_number(self, num: int) -> str:
        """格式化数字显示"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        if num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)


def generate_research_report(
    theme: str = "老人养生",
    time_window: str = "全部",
    output_path: str = None
) -> str:
    """便捷函数：生成调研报告"""
    generator = ResearchReportGenerator()
    return generator.generate(theme, time_window, output_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='生成调研洞察报告')
    parser.add_argument('--theme', default='老人养生', help='调研主题')
    parser.add_argument('--time-window', default='全部',
                       choices=['1天内', '15天内', '30天内', '全部'],
                       help='时间范围')
    parser.add_argument('--output', '-o', help='输出路径')
    parser.add_argument('--open', action='store_true', help='生成后打开')

    args = parser.parse_args()

    path = generate_research_report(
        theme=args.theme,
        time_window=args.time_window,
        output_path=args.output
    )
    print(f"报告已生成: {path}")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{Path(path).absolute()}")
