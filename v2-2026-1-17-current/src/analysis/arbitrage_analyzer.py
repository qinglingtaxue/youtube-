#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
套利分析器 - 基于网络中心性发现内容机会

核心公式：
    有趣度 = 信息价值程度 / 信息传播程度
          = 中介中心性 / 程度中心性

套利类型：
1. 话题套利：发现"桥梁话题"（高中介、低程度）
2. 跨语言套利：源市场火爆但目标市场空白
3. 格式套利：A品类验证但B品类未应用
4. 频道套利：内容优质但关注不足
"""

import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import jieba

# 尝试导入 networkx，如果没有则用简化版
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


@dataclass
class ArbitrageOpportunity:
    """套利机会"""
    type: str  # topic, cross_language, format, channel
    name: str
    interestingness: float  # 有趣度
    value_score: float  # 价值程度
    spread_score: float  # 传播程度
    details: Dict[str, Any]
    recommendation: str


class ArbitrageAnalyzer:
    """套利分析器 - 发现被低估的内容机会"""

    def __init__(self, db_path: str = "data/youtube_pipeline.db"):
        self.db_path = db_path
        # 停用词
        self.stopwords = {
            '的', '是', '在', '了', '和', '与', '或', '等', '这', '那',
            '你', '我', '他', '她', '它', '们', '个', '就', '都', '也',
            '要', '会', '可以', '能', '被', '把', '让', '给', '到', '从',
            '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
            '年', '月', '日', '时', '分', '秒', '为什么', '如何', '怎么',
            '什么', '哪些', '哪个', '这个', '那个', '视频', 'youtube',
        }

    def analyze_all(self, min_videos: int = 100) -> Dict[str, Any]:
        """执行全部套利分析"""
        videos = self._load_videos()

        if len(videos) < min_videos:
            return {'error': f'视频数量不足，需要至少 {min_videos} 个'}

        results = {
            'sample_size': len(videos),
            'topic_arbitrage': self.analyze_topic_arbitrage(videos),
            'channel_arbitrage': self.analyze_channel_arbitrage(videos),
            'duration_arbitrage': self.analyze_duration_arbitrage(videos),
            'timing_arbitrage': self.analyze_timing_arbitrage(videos),
            'summary': None
        }

        # 生成摘要
        results['summary'] = self._generate_summary(results)

        return results

    def analyze_topic_arbitrage(self, videos: List[Dict]) -> Dict[str, Any]:
        """
        话题套利分析 - 基于关键词共现网络

        构建网络：
        - 节点：标题关键词
        - 边：在同一视频标题中共现

        计算有趣度：
        - 中介中心性：关键词作为"桥梁"连接不同话题群的能力
        - 程度中心性：关键词的常见程度（已被充分传播）
        - 有趣度 = 中介中心性 / 程度中心性
        """
        # 构建关键词共现网络
        network_data = self._build_keyword_network(videos)

        if not HAS_NETWORKX:
            # 简化版分析（不使用 networkx）
            return self._simplified_topic_analysis(videos, network_data)

        G = network_data['graph']

        if len(G.nodes()) < 10:
            return {'error': '关键词太少，无法分析'}

        # 计算网络中心性
        betweenness = nx.betweenness_centrality(G, weight='weight')
        degree = nx.degree_centrality(G)

        # 计算有趣度
        interestingness = {}
        for node in G.nodes():
            if degree[node] > 0.01:  # 过滤太边缘的节点
                interestingness[node] = betweenness[node] / degree[node]
            else:
                interestingness[node] = 0

        # 排序找出高有趣度话题
        sorted_topics = sorted(
            interestingness.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 取 Top 20
        top_opportunities = []
        for keyword, score in sorted_topics[:20]:
            if score > 0:
                node_data = G.nodes[keyword]
                top_opportunities.append({
                    'keyword': keyword,
                    'interestingness': round(score, 4),
                    'betweenness': round(betweenness[keyword], 4),
                    'degree': round(degree[keyword], 4),
                    'video_count': node_data.get('count', 0),
                    'total_views': node_data.get('total_views', 0),
                    'avg_views': round(node_data.get('total_views', 0) / max(node_data.get('count', 1), 1)),
                    'connected_topics': self._get_connected_topics(G, keyword, 5),
                    'interpretation': self._interpret_topic_opportunity(
                        keyword, score, betweenness[keyword], degree[keyword]
                    )
                })

        # 识别"桥梁话题"
        bridge_topics = [t for t in top_opportunities if t['betweenness'] > 0.01]

        return {
            'network_stats': {
                'nodes': len(G.nodes()),
                'edges': len(G.edges()),
                'density': round(nx.density(G), 4),
                'avg_clustering': round(nx.average_clustering(G), 4) if len(G.nodes()) > 2 else 0
            },
            'top_opportunities': top_opportunities,
            'bridge_topics': bridge_topics[:10],
            'insight': self._generate_topic_insight(top_opportunities, bridge_topics)
        }

    def analyze_channel_arbitrage(self, videos: List[Dict]) -> Dict[str, Any]:
        """
        频道套利分析 - 发现"小频道大爆款"

        有趣度 = 内容价值 / 频道传播力
              = 视频播放量 / 频道平均播放量（或订阅者估算）
        """
        # 按频道聚合
        channels = defaultdict(lambda: {'videos': [], 'total_views': 0})
        for v in videos:
            ch = v.get('channel_name', 'Unknown')
            channels[ch]['videos'].append(v)
            channels[ch]['total_views'] += v.get('views', 0)

        # 计算每个频道的统计
        channel_stats = []
        for ch_name, data in channels.items():
            video_count = len(data['videos'])
            if video_count < 2:
                continue

            total_views = data['total_views']
            avg_views = total_views / video_count

            # 找出该频道的爆款
            max_video = max(data['videos'], key=lambda x: x.get('views', 0))
            max_views = max_video.get('views', 0)

            # 频道有趣度 = 最高播放 / 平均播放
            # 高有趣度 = 有单个爆款远超平均，说明有潜力
            if avg_views > 0:
                channel_interestingness = max_views / avg_views
            else:
                channel_interestingness = 0

            # 估算频道规模（用总播放量近似）
            # 小频道高有趣度 = 套利机会
            channel_stats.append({
                'channel': ch_name,
                'video_count': video_count,
                'total_views': total_views,
                'avg_views': round(avg_views),
                'max_views': max_views,
                'max_video_title': max_video.get('title', ''),
                'interestingness': round(channel_interestingness, 2),
                'is_small_channel': total_views < 100000,
                'has_breakout': max_views > avg_views * 5
            })

        # 按有趣度排序
        channel_stats.sort(key=lambda x: x['interestingness'], reverse=True)

        # 小频道爆款机会
        small_channel_opportunities = [
            c for c in channel_stats
            if c['is_small_channel'] and c['has_breakout']
        ][:10]

        # 模式可复制的大频道
        replicable_patterns = [
            c for c in channel_stats
            if not c['is_small_channel'] and c['interestingness'] > 3
        ][:10]

        return {
            'total_channels': len(channel_stats),
            'small_channel_opportunities': small_channel_opportunities,
            'replicable_patterns': replicable_patterns,
            'insight': self._generate_channel_insight(
                small_channel_opportunities, replicable_patterns
            )
        }

    def analyze_duration_arbitrage(self, videos: List[Dict]) -> Dict[str, Any]:
        """
        时长套利分析 - 发现未被充分开发的时长区间

        有趣度 = 该时长区间的平均播放量 / 该时长区间的视频供给
        高有趣度 = 播放量高但供给少的时长区间
        """
        # 按时长分桶
        duration_buckets = {
            '0-1min': {'range': (0, 60), 'videos': [], 'total_views': 0},
            '1-3min': {'range': (60, 180), 'videos': [], 'total_views': 0},
            '3-5min': {'range': (180, 300), 'videos': [], 'total_views': 0},
            '5-10min': {'range': (300, 600), 'videos': [], 'total_views': 0},
            '10-20min': {'range': (600, 1200), 'videos': [], 'total_views': 0},
            '20-30min': {'range': (1200, 1800), 'videos': [], 'total_views': 0},
            '30min+': {'range': (1800, float('inf')), 'videos': [], 'total_views': 0},
        }

        for v in videos:
            duration = v.get('duration', 0)
            views = v.get('views', 0)
            for bucket_name, bucket_data in duration_buckets.items():
                low, high = bucket_data['range']
                if low <= duration < high:
                    bucket_data['videos'].append(v)
                    bucket_data['total_views'] += views
                    break

        # 计算每个桶的有趣度
        total_videos = len(videos)
        bucket_analysis = []

        for bucket_name, bucket_data in duration_buckets.items():
            count = len(bucket_data['videos'])
            if count == 0:
                continue

            total_views = bucket_data['total_views']
            avg_views = total_views / count
            supply_ratio = count / total_videos  # 供给占比

            # 有趣度 = 平均播放量 / 供给占比
            # 高有趣度 = 播放量高但供给少
            if supply_ratio > 0:
                interestingness = avg_views / (supply_ratio * 1000000)  # 归一化
            else:
                interestingness = 0

            bucket_analysis.append({
                'duration_range': bucket_name,
                'video_count': count,
                'supply_ratio': round(supply_ratio * 100, 1),
                'total_views': total_views,
                'avg_views': round(avg_views),
                'interestingness': round(interestingness, 2),
                'opportunity_level': 'high' if interestingness > 1 else 'medium' if interestingness > 0.5 else 'low'
            })

        # 按有趣度排序
        bucket_analysis.sort(key=lambda x: x['interestingness'], reverse=True)

        return {
            'buckets': bucket_analysis,
            'best_opportunity': bucket_analysis[0] if bucket_analysis else None,
            'insight': self._generate_duration_insight(bucket_analysis)
        }

    def analyze_timing_arbitrage(self, videos: List[Dict]) -> Dict[str, Any]:
        """
        时间套利分析 - 发现趋势拐点

        分析近期 vs 历史的话题变化，识别：
        - 上升趋势话题（早期套利机会）
        - 下降趋势话题（应避开）
        """
        from datetime import datetime, timedelta

        # 划分时间段：近期 vs 历史
        now = datetime.now()
        recent_cutoff = now - timedelta(days=30)

        recent_videos = []
        historical_videos = []

        for v in videos:
            pub_date = v.get('published_at', '')
            if not pub_date:
                historical_videos.append(v)
                continue

            try:
                if 'T' in pub_date:
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(pub_date[:10], '%Y-%m-%d')

                if dt.replace(tzinfo=None) > recent_cutoff:
                    recent_videos.append(v)
                else:
                    historical_videos.append(v)
            except (ValueError, TypeError):
                historical_videos.append(v)

        if len(recent_videos) < 10 or len(historical_videos) < 10:
            return {'error': '数据时间跨度不足'}

        # 提取关键词频率
        recent_keywords = self._extract_keyword_freq(recent_videos)
        historical_keywords = self._extract_keyword_freq(historical_videos)

        # 计算趋势变化
        trends = []
        all_keywords = set(recent_keywords.keys()) | set(historical_keywords.keys())

        for kw in all_keywords:
            recent_freq = recent_keywords.get(kw, 0) / len(recent_videos)
            historical_freq = historical_keywords.get(kw, 0) / len(historical_videos)

            if historical_freq > 0:
                trend_ratio = recent_freq / historical_freq
            elif recent_freq > 0:
                trend_ratio = 10  # 新出现的话题
            else:
                trend_ratio = 1

            # 只关注有一定频率的话题
            if recent_freq > 0.02 or historical_freq > 0.02:
                trends.append({
                    'keyword': kw,
                    'recent_freq': round(recent_freq, 4),
                    'historical_freq': round(historical_freq, 4),
                    'trend_ratio': round(trend_ratio, 2),
                    'direction': 'rising' if trend_ratio > 1.5 else 'falling' if trend_ratio < 0.7 else 'stable'
                })

        # 分类
        rising_topics = sorted(
            [t for t in trends if t['direction'] == 'rising'],
            key=lambda x: x['trend_ratio'],
            reverse=True
        )[:10]

        falling_topics = sorted(
            [t for t in trends if t['direction'] == 'falling'],
            key=lambda x: x['trend_ratio']
        )[:10]

        return {
            'recent_videos': len(recent_videos),
            'historical_videos': len(historical_videos),
            'rising_topics': rising_topics,
            'falling_topics': falling_topics,
            'insight': self._generate_timing_insight(rising_topics, falling_topics)
        }

    def analyze_cross_language_arbitrage(
        self,
        source_videos: List[Dict],
        target_videos: List[Dict],
        source_lang: str = "中文",
        target_lang: str = "越南语"
    ) -> Dict[str, Any]:
        """
        跨语言套利分析 - 发现可翻译的内容机会

        有趣度 = 源市场价值 / 目标市场供给
        高有趣度 = 源市场很火但目标市场空白
        """
        # 源市场话题分析
        source_topics = self._extract_keyword_freq(source_videos)
        source_views = defaultdict(int)
        for v in source_videos:
            for kw in self._extract_keywords(v.get('title', '')):
                source_views[kw] += v.get('views', 0)

        # 目标市场话题分析
        target_topics = self._extract_keyword_freq(target_videos)

        # 计算套利机会
        opportunities = []
        for topic, source_freq in source_topics.items():
            target_freq = target_topics.get(topic, 0)

            # 源市场价值（播放量）
            value = source_views.get(topic, 0)

            # 目标市场供给（频率，+1避免除零）
            supply = target_freq + 0.001

            # 有趣度 = 价值 / 供给
            interestingness = value / (supply * 1000000)  # 归一化

            if value > 10000:  # 只关注有一定规模的话题
                opportunities.append({
                    'topic': topic,
                    'source_value': value,
                    'source_freq': round(source_freq, 4),
                    'target_freq': round(target_freq, 4),
                    'interestingness': round(interestingness, 2),
                    'gap_ratio': round(source_freq / supply, 1),
                    'recommendation': 'high' if interestingness > 1 else 'medium' if interestingness > 0.3 else 'low'
                })

        # 按有趣度排序
        opportunities.sort(key=lambda x: x['interestingness'], reverse=True)

        return {
            'source_lang': source_lang,
            'target_lang': target_lang,
            'source_videos': len(source_videos),
            'target_videos': len(target_videos),
            'top_opportunities': opportunities[:20],
            'insight': f"发现 {len([o for o in opportunities if o['recommendation'] == 'high'])} 个高价值跨语言套利机会"
        }

    # ==================== 辅助方法 ====================

    def _load_videos(self) -> List[Dict]:
        """从数据库加载视频"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        query = """
        SELECT
            youtube_id as id,
            title,
            channel_name,
            view_count as views,
            like_count as likes,
            comment_count as comments,
            duration,
            published_at
        FROM competitor_videos
        WHERE view_count > 0
        ORDER BY view_count DESC
        """

        cursor = conn.execute(query)
        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return videos

    def _extract_keywords(self, title: str) -> List[str]:
        """从标题提取关键词"""
        if not title:
            return []

        # 分词
        words = jieba.lcut(title)

        # 过滤
        keywords = []
        for w in words:
            w = w.strip().lower()
            if (len(w) >= 2 and
                w not in self.stopwords and
                not w.isdigit() and
                not re.match(r'^[a-z]$', w)):
                keywords.append(w)

        return keywords

    def _extract_keyword_freq(self, videos: List[Dict]) -> Dict[str, float]:
        """提取关键词频率"""
        counter = Counter()
        for v in videos:
            for kw in self._extract_keywords(v.get('title', '')):
                counter[kw] += 1
        return dict(counter)

    def _build_keyword_network(self, videos: List[Dict]) -> Dict[str, Any]:
        """构建关键词共现网络"""
        if not HAS_NETWORKX:
            # 返回基础统计
            return {'graph': None, 'keyword_stats': self._extract_keyword_freq(videos)}

        G = nx.Graph()

        for v in videos:
            keywords = self._extract_keywords(v.get('title', ''))
            views = v.get('views', 0)

            # 添加/更新节点
            for kw in keywords:
                if kw in G:
                    G.nodes[kw]['count'] += 1
                    G.nodes[kw]['total_views'] += views
                else:
                    G.add_node(kw, count=1, total_views=views)

            # 添加边（共现）
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    if G.has_edge(kw1, kw2):
                        G[kw1][kw2]['weight'] += 1
                    else:
                        G.add_edge(kw1, kw2, weight=1)

        return {'graph': G}

    def _get_connected_topics(self, G, keyword: str, limit: int = 5) -> List[str]:
        """获取与关键词相连的话题"""
        if keyword not in G:
            return []

        neighbors = list(G.neighbors(keyword))
        # 按边权重排序
        neighbors.sort(key=lambda x: G[keyword][x].get('weight', 0), reverse=True)
        return neighbors[:limit]

    def _simplified_topic_analysis(self, videos: List[Dict], network_data: Dict) -> Dict[str, Any]:
        """简化版话题分析（不使用 networkx）"""
        keyword_freq = self._extract_keyword_freq(videos)

        # 按频率排序
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)

        # 计算播放量
        keyword_views = defaultdict(int)
        for v in videos:
            for kw in self._extract_keywords(v.get('title', '')):
                keyword_views[kw] += v.get('views', 0)

        # 简化版有趣度 = 平均播放量 / 频率
        opportunities = []
        for kw, freq in sorted_keywords[:50]:
            avg_views = keyword_views[kw] / freq if freq > 0 else 0
            interestingness = avg_views / (freq * 1000) if freq > 0 else 0

            opportunities.append({
                'keyword': kw,
                'frequency': freq,
                'total_views': keyword_views[kw],
                'avg_views': round(avg_views),
                'interestingness': round(interestingness, 4)
            })

        opportunities.sort(key=lambda x: x['interestingness'], reverse=True)

        return {
            'note': '简化版分析（未安装 networkx）',
            'top_opportunities': opportunities[:20]
        }

    def _interpret_topic_opportunity(
        self, keyword: str, interestingness: float,
        betweenness: float, degree: float
    ) -> str:
        """解读话题机会"""
        if interestingness > 0.5 and betweenness > 0.01:
            return f"桥梁话题：'{keyword}' 能连接多个话题群，但本身传播不足，是高价值套利点"
        elif interestingness > 0.3:
            return f"潜力话题：'{keyword}' 有一定价值但尚未充分开发"
        elif degree > 0.1:
            return f"红海话题：'{keyword}' 已被充分传播，竞争激烈"
        else:
            return f"边缘话题：'{keyword}' 价值和传播都较低"

    def _generate_topic_insight(
        self, opportunities: List[Dict], bridge_topics: List[Dict]
    ) -> str:
        """生成话题洞察"""
        insights = []

        if bridge_topics:
            top_bridges = [t['keyword'] for t in bridge_topics[:3]]
            insights.append(f"发现 {len(bridge_topics)} 个桥梁话题，最具价值的是：{', '.join(top_bridges)}")

        high_interest = [o for o in opportunities if o['interestingness'] > 0.3]
        if high_interest:
            insights.append(f"共 {len(high_interest)} 个话题有趣度高于 0.3，代表未被充分开发的机会")

        return '; '.join(insights) if insights else "暂无明显套利机会"

    def _generate_channel_insight(
        self, small_opportunities: List[Dict], replicable: List[Dict]
    ) -> str:
        """生成频道洞察"""
        insights = []

        if small_opportunities:
            best = small_opportunities[0]
            insights.append(
                f"发现 {len(small_opportunities)} 个小频道爆款机会，"
                f"最佳案例：{best['channel']} 的视频播放量达到均值的 {best['interestingness']:.0f} 倍"
            )

        if replicable:
            insights.append(f"发现 {len(replicable)} 个可复制的成功模式")

        return '; '.join(insights) if insights else "暂无明显频道套利机会"

    def _generate_duration_insight(self, buckets: List[Dict]) -> str:
        """生成时长洞察"""
        if not buckets:
            return "数据不足"

        best = buckets[0]
        high_opp = [b for b in buckets if b['opportunity_level'] == 'high']

        if high_opp:
            return (
                f"最佳时长区间：{best['duration_range']}，"
                f"平均播放量 {best['avg_views']:,} 但供给仅占 {best['supply_ratio']}%，"
                f"建议优先制作这个时长的内容"
            )
        else:
            return f"各时长区间供需相对均衡，{best['duration_range']} 略有优势"

    def _generate_timing_insight(
        self, rising: List[Dict], falling: List[Dict]
    ) -> str:
        """生成时间洞察"""
        insights = []

        if rising:
            top_rising = [t['keyword'] for t in rising[:3]]
            insights.append(f"上升趋势话题：{', '.join(top_rising)}，建议尽早布局")

        if falling:
            top_falling = [t['keyword'] for t in falling[:3]]
            insights.append(f"下降趋势话题：{', '.join(top_falling)}，建议谨慎投入")

        return '; '.join(insights) if insights else "话题趋势相对稳定"

    def _generate_summary(self, results: Dict) -> Dict[str, Any]:
        """生成综合摘要"""
        opportunities = []

        # 话题套利机会
        if 'top_opportunities' in results.get('topic_arbitrage', {}):
            for t in results['topic_arbitrage']['top_opportunities'][:3]:
                opportunities.append({
                    'type': 'topic',
                    'name': t['keyword'],
                    'score': t['interestingness'],
                    'action': f"围绕 '{t['keyword']}' 创作内容，它能连接 {', '.join(t.get('connected_topics', []))}"
                })

        # 频道套利机会
        if 'small_channel_opportunities' in results.get('channel_arbitrage', {}):
            for c in results['channel_arbitrage']['small_channel_opportunities'][:2]:
                opportunities.append({
                    'type': 'channel',
                    'name': c['channel'],
                    'score': c['interestingness'],
                    'action': f"模仿 '{c['channel']}' 的爆款：{c['max_video_title'][:30]}..."
                })

        # 时长套利机会
        if 'best_opportunity' in results.get('duration_arbitrage', {}):
            best = results['duration_arbitrage']['best_opportunity']
            if best and best['opportunity_level'] == 'high':
                opportunities.append({
                    'type': 'duration',
                    'name': best['duration_range'],
                    'score': best['interestingness'],
                    'action': f"优先制作 {best['duration_range']} 时长的视频"
                })

        # 趋势套利机会
        if 'rising_topics' in results.get('timing_arbitrage', {}):
            for t in results['timing_arbitrage']['rising_topics'][:2]:
                opportunities.append({
                    'type': 'timing',
                    'name': t['keyword'],
                    'score': t['trend_ratio'],
                    'action': f"'{t['keyword']}' 正在上升，近期频率是历史的 {t['trend_ratio']:.1f} 倍"
                })

        # 按分数排序
        opportunities.sort(key=lambda x: x['score'], reverse=True)

        return {
            'total_opportunities': len(opportunities),
            'top_actions': opportunities[:5],
            'summary_text': self._format_summary_text(opportunities[:5])
        }

    def _format_summary_text(self, opportunities: List[Dict]) -> str:
        """格式化摘要文本"""
        if not opportunities:
            return "未发现明显套利机会，市场相对饱和"

        lines = ["## 发现的套利机会\n"]
        for i, opp in enumerate(opportunities, 1):
            type_names = {
                'topic': '话题',
                'channel': '频道',
                'duration': '时长',
                'timing': '趋势'
            }
            lines.append(f"{i}. **{type_names.get(opp['type'], opp['type'])}套利**：{opp['action']}")

        return '\n'.join(lines)


def analyze_arbitrage(theme: str = None) -> Dict[str, Any]:
    """便捷函数：执行套利分析"""
    analyzer = ArbitrageAnalyzer()
    return analyzer.analyze_all()


if __name__ == '__main__':
    print("=== 套利分析 ===\n")
    results = analyze_arbitrage()

    if 'error' in results:
        print(f"错误: {results['error']}")
    else:
        print(f"样本量: {results['sample_size']} 个视频\n")

        if results['summary']:
            print(results['summary']['summary_text'])
