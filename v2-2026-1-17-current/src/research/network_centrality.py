#!/usr/bin/env python3
"""
网络中心性分析模块

基于视频-话题网络计算中介中心性和程度中心性，
用于发现被低估的套利机会。

网络定义：
- 节点：视频、频道、话题（keyword_source）
- 边：
  - 视频-话题：视频属于某话题
  - 频道-话题：频道发布过该话题的视频
  - 话题-话题：在同一频道下共现
"""

import sqlite3
from src.shared.db_compat import get_connection as db_get_connection, is_using_neon
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import math

# 尝试导入 networkx，如果不可用则使用简化版算法
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class NetworkCentralityAnalyzer:
    """网络中心性分析器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None:
            self._conn = db_get_connection(self.db_path, row_factory=sqlite3.Row)
        return self._conn

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _load_video_topic_data(self) -> Tuple[List[Dict], Dict[str, List[str]]]:
        """
        加载视频-话题数据

        返回:
        - videos: 视频列表（含视频信息）
        - channel_topics: 频道 -> 话题列表的映射
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取所有视频及其话题
        cursor.execute("""
            SELECT
                youtube_id,
                title,
                channel_id,
                channel_name,
                keyword_source,
                view_count,
                subscriber_count,
                like_count,
                comment_count
            FROM competitor_videos
            WHERE keyword_source IS NOT NULL
              AND keyword_source != ''
              AND youtube_id IS NOT NULL
        """)

        videos = []
        channel_topics = defaultdict(set)

        for row in cursor.fetchall():
            video = dict(row)
            videos.append(video)

            # 记录频道涉及的话题
            if video['channel_id']:
                channel_topics[video['channel_id']].add(video['keyword_source'])

        # 转换 set 为 list
        channel_topics = {k: list(v) for k, v in channel_topics.items()}

        return videos, channel_topics

    def _build_topic_cooccurrence_graph(self, channel_topics: Dict[str, List[str]]) -> Dict[str, Dict[str, int]]:
        """
        构建话题共现图

        如果两个话题在同一个频道下出现，则它们之间有一条边。
        边的权重 = 共现的频道数量

        返回: adjacency list 格式的图 {topic: {neighbor_topic: weight}}
        """
        graph = defaultdict(lambda: defaultdict(int))

        for channel_id, topics in channel_topics.items():
            # 为该频道下的所有话题对创建边
            for i, t1 in enumerate(topics):
                for t2 in topics[i+1:]:
                    graph[t1][t2] += 1
                    graph[t2][t1] += 1

        return dict(graph)

    def _build_channel_topic_graph(self, videos: List[Dict]) -> Dict[str, Dict[str, int]]:
        """
        构建频道-话题二分图

        边的权重 = 频道在该话题下发布的视频数量
        """
        graph = defaultdict(lambda: defaultdict(int))

        for video in videos:
            channel_id = video.get('channel_id')
            topic = video.get('keyword_source')
            if channel_id and topic:
                graph[f"channel:{channel_id}"][f"topic:{topic}"] += 1
                graph[f"topic:{topic}"][f"channel:{channel_id}"] += 1

        return dict(graph)

    def _calculate_degree_centrality_simple(self, graph: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        计算程度中心性（简化版，不依赖 networkx）

        程度中心性 = 节点的邻居数 / (总节点数 - 1)
        """
        n = len(graph)
        if n <= 1:
            return {node: 0.0 for node in graph}

        centrality = {}
        for node in graph:
            degree = len(graph[node])
            centrality[node] = degree / (n - 1)

        return centrality

    def _calculate_betweenness_centrality_simple(self, graph: Dict[str, Dict[str, Any]], k: int = 100) -> Dict[str, float]:
        """
        计算中介中心性（简化版，采样算法）

        使用 BFS 近似算法，从 k 个随机节点出发计算最短路径
        """
        import random

        nodes = list(graph.keys())
        n = len(nodes)

        if n <= 2:
            return {node: 0.0 for node in nodes}

        betweenness = {node: 0.0 for node in nodes}

        # 采样 k 个源节点
        sample_nodes = random.sample(nodes, min(k, n))

        for source in sample_nodes:
            # BFS 计算从 source 到所有节点的最短路径
            distances = {source: 0}
            predecessors = {node: [] for node in nodes}
            sigma = {node: 0 for node in nodes}  # 最短路径数量
            sigma[source] = 1

            queue = [source]
            stack = []

            while queue:
                current = queue.pop(0)
                stack.append(current)

                for neighbor in graph.get(current, {}):
                    # 发现新节点
                    if neighbor not in distances:
                        distances[neighbor] = distances[current] + 1
                        queue.append(neighbor)

                    # 最短路径
                    if distances[neighbor] == distances[current] + 1:
                        sigma[neighbor] += sigma[current]
                        predecessors[neighbor].append(current)

            # 反向累积贡献
            delta = {node: 0.0 for node in nodes}
            while stack:
                w = stack.pop()
                for v in predecessors[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != source:
                    betweenness[w] += delta[w]

        # 归一化
        scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
        scale *= n / len(sample_nodes)  # 补偿采样

        for node in betweenness:
            betweenness[node] *= scale

        return betweenness

    def calculate_topic_centrality(self) -> List[Dict[str, Any]]:
        """
        计算话题的中心性

        返回按中介中心性排序的话题列表
        """
        videos, channel_topics = self._load_video_topic_data()

        # 构建话题共现图
        graph = self._build_topic_cooccurrence_graph(channel_topics)

        if not graph:
            return []

        # 计算中心性
        if HAS_NETWORKX:
            G = nx.Graph()
            for t1, neighbors in graph.items():
                for t2, weight in neighbors.items():
                    G.add_edge(t1, t2, weight=weight)

            betweenness = nx.betweenness_centrality(G, weight='weight')
            degree = nx.degree_centrality(G)
        else:
            betweenness = self._calculate_betweenness_centrality_simple(graph)
            degree = self._calculate_degree_centrality_simple(graph)

        # 统计每个话题的视频数和播放量
        topic_stats = defaultdict(lambda: {'video_count': 0, 'total_views': 0, 'channels': set()})
        for video in videos:
            topic = video.get('keyword_source')
            if topic:
                topic_stats[topic]['video_count'] += 1
                topic_stats[topic]['total_views'] += video.get('view_count', 0) or 0
                if video.get('channel_id'):
                    topic_stats[topic]['channels'].add(video['channel_id'])

        # 组装结果
        results = []
        for topic in graph.keys():
            stats = topic_stats[topic]
            b = betweenness.get(topic, 0)
            d = degree.get(topic, 0)

            # 有趣度 = 中介中心性 / max(程度中心性, 0.01)
            interestingness = b / max(d, 0.01)

            results.append({
                'topic': topic,
                'betweenness': round(b, 6),
                'degree': round(d, 6),
                'interestingness': round(interestingness, 4),
                'video_count': stats['video_count'],
                'total_views': stats['total_views'],
                'avg_views': round(stats['total_views'] / stats['video_count']) if stats['video_count'] > 0 else 0,
                'channel_count': len(stats['channels'])
            })

        # 按中介中心性排序
        results.sort(key=lambda x: x['betweenness'], reverse=True)

        return results

    def calculate_channel_centrality(self) -> List[Dict[str, Any]]:
        """
        计算频道的中心性

        基于频道-话题二分图的投影
        """
        videos, channel_topics = self._load_video_topic_data()

        # 构建频道-频道网络（通过共同话题连接）
        # 如果两个频道都发布过同一话题的视频，则它们之间有边
        graph = defaultdict(lambda: defaultdict(int))

        # 构建话题 -> 频道列表的映射
        topic_channels = defaultdict(set)
        for channel_id, topics in channel_topics.items():
            for topic in topics:
                topic_channels[topic].add(channel_id)

        # 为共同话题的频道对创建边
        for topic, channels in topic_channels.items():
            channels_list = list(channels)
            for i, c1 in enumerate(channels_list):
                for c2 in channels_list[i+1:]:
                    graph[c1][c2] += 1
                    graph[c2][c1] += 1

        graph = dict(graph)

        if not graph:
            return []

        # 计算中心性
        if HAS_NETWORKX:
            G = nx.Graph()
            for c1, neighbors in graph.items():
                for c2, weight in neighbors.items():
                    G.add_edge(c1, c2, weight=weight)

            betweenness = nx.betweenness_centrality(G, weight='weight', k=min(100, len(G.nodes())))
            degree = nx.degree_centrality(G)
        else:
            betweenness = self._calculate_betweenness_centrality_simple(graph, k=50)
            degree = self._calculate_degree_centrality_simple(graph)

        # 统计频道信息
        channel_stats = defaultdict(lambda: {
            'channel_name': '',
            'video_count': 0,
            'total_views': 0,
            'subscriber_count': 0,
            'topics': set()
        })

        for video in videos:
            channel_id = video.get('channel_id')
            if channel_id:
                stats = channel_stats[channel_id]
                stats['channel_name'] = video.get('channel_name', '')
                stats['video_count'] += 1
                stats['total_views'] += video.get('view_count', 0) or 0
                stats['subscriber_count'] = max(stats['subscriber_count'], video.get('subscriber_count', 0) or 0)
                stats['topics'].add(video.get('keyword_source'))

        # 组装结果
        results = []
        for channel_id in graph.keys():
            stats = channel_stats[channel_id]
            b = betweenness.get(channel_id, 0)
            d = degree.get(channel_id, 0)

            # 有趣度 = 中介中心性 / max(程度中心性, 0.01)
            interestingness = b / max(d, 0.01)

            results.append({
                'channel_id': channel_id,
                'channel_name': stats['channel_name'],
                'channel_url': f"https://www.youtube.com/channel/{channel_id}" if channel_id else '',
                'betweenness': round(b, 6),
                'degree': round(d, 6),
                'interestingness': round(interestingness, 4),
                'video_count': stats['video_count'],
                'total_views': stats['total_views'],
                'avg_views': round(stats['total_views'] / stats['video_count']) if stats['video_count'] > 0 else 0,
                'subscriber_count': stats['subscriber_count'],
                'topic_count': len(stats['topics'])
            })

        # 按中介中心性排序
        results.sort(key=lambda x: x['betweenness'], reverse=True)

        return results

    def calculate_video_centrality(self) -> List[Dict[str, Any]]:
        """
        计算视频的中心性

        基于视频-话题二分图，视频通过共同话题连接
        """
        videos, _ = self._load_video_topic_data()

        # 构建话题 -> 视频列表的映射
        topic_videos = defaultdict(list)
        video_info = {}

        for video in videos:
            vid = video.get('youtube_id')
            topic = video.get('keyword_source')
            if vid and topic:
                topic_videos[topic].append(vid)
                video_info[vid] = video

        # 由于视频数量较多，我们采用简化策略：
        # 每个视频的程度中心性 = 与它同话题的视频数 / (总视频数 - 1)
        # 中介中心性 = 该视频所属话题的"桥梁"程度（话题的中介中心性）

        # 先计算话题的中介中心性
        topic_centrality = {t['topic']: t['betweenness'] for t in self.calculate_topic_centrality()}

        n = len(videos)
        results = []

        for video in videos:
            vid = video.get('youtube_id')
            topic = video.get('keyword_source')

            if not vid or not topic:
                continue

            # 程度中心性：同话题视频数
            same_topic_count = len(topic_videos.get(topic, [])) - 1
            degree = same_topic_count / (n - 1) if n > 1 else 0

            # 中介中心性：继承话题的中介中心性
            betweenness = topic_centrality.get(topic, 0)

            # 有趣度
            interestingness = betweenness / max(degree, 0.01)

            results.append({
                'youtube_id': vid,
                'title': video.get('title', ''),
                'video_url': f"https://www.youtube.com/watch?v={vid}",
                'channel_id': video.get('channel_id', ''),
                'channel_name': video.get('channel_name', ''),
                'channel_url': f"https://www.youtube.com/channel/{video.get('channel_id')}" if video.get('channel_id') else '',
                'topic': topic,
                'betweenness': round(betweenness, 6),
                'degree': round(degree, 6),
                'interestingness': round(interestingness, 4),
                'view_count': video.get('view_count', 0) or 0,
                'like_count': video.get('like_count', 0) or 0,
                'comment_count': video.get('comment_count', 0) or 0,
                'subscriber_count': video.get('subscriber_count', 0) or 0
            })

        # 按中介中心性排序
        results.sort(key=lambda x: x['betweenness'], reverse=True)

        return results

    def calculate_title_word_centrality(self) -> List[Dict[str, Any]]:
        """
        计算标题关键词的中心性

        基于词共现网络
        """
        import re

        videos, _ = self._load_video_topic_data()

        # 提取标题中的关键词
        def extract_keywords(title: str) -> List[str]:
            if not title:
                return []
            # 移除特殊字符，保留中文、英文、数字
            words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', title)
            # 过滤太短的词
            words = [w for w in words if len(w) >= 2]
            return words

        # 构建词共现图
        word_cooccurrence = defaultdict(lambda: defaultdict(int))
        word_stats = defaultdict(lambda: {'count': 0, 'total_views': 0, 'videos': []})

        for video in videos:
            title = video.get('title', '')
            keywords = extract_keywords(title)

            # 统计词频和播放量
            seen_words = set()
            for word in keywords:
                if word not in seen_words:
                    word_stats[word]['count'] += 1
                    word_stats[word]['total_views'] += video.get('view_count', 0) or 0
                    word_stats[word]['videos'].append(video.get('youtube_id'))
                    seen_words.add(word)

            # 构建共现边
            unique_keywords = list(seen_words)
            for i, w1 in enumerate(unique_keywords):
                for w2 in unique_keywords[i+1:]:
                    word_cooccurrence[w1][w2] += 1
                    word_cooccurrence[w2][w1] += 1

        graph = dict(word_cooccurrence)

        if not graph:
            return []

        # 只分析出现频率较高的词（减少计算量）
        min_count = 3
        filtered_graph = {
            w: {nw: wt for nw, wt in neighbors.items() if word_stats[nw]['count'] >= min_count}
            for w, neighbors in graph.items()
            if word_stats[w]['count'] >= min_count
        }
        filtered_graph = {k: v for k, v in filtered_graph.items() if v}

        if not filtered_graph:
            return []

        # 计算中心性
        if HAS_NETWORKX:
            G = nx.Graph()
            for w1, neighbors in filtered_graph.items():
                for w2, weight in neighbors.items():
                    G.add_edge(w1, w2, weight=weight)

            betweenness = nx.betweenness_centrality(G, weight='weight', k=min(50, len(G.nodes())))
            degree = nx.degree_centrality(G)
        else:
            betweenness = self._calculate_betweenness_centrality_simple(filtered_graph, k=30)
            degree = self._calculate_degree_centrality_simple(filtered_graph)

        # 组装结果
        results = []
        for word in filtered_graph.keys():
            stats = word_stats[word]
            b = betweenness.get(word, 0)
            d = degree.get(word, 0)

            interestingness = b / max(d, 0.01)

            results.append({
                'word': word,
                'betweenness': round(b, 6),
                'degree': round(d, 6),
                'interestingness': round(interestingness, 4),
                'count': stats['count'],
                'total_views': stats['total_views'],
                'avg_views': round(stats['total_views'] / stats['count']) if stats['count'] > 0 else 0
            })

        # 按中介中心性排序
        results.sort(key=lambda x: x['betweenness'], reverse=True)

        return results

    def get_arbitrage_opportunities(self, top_n: int = 50) -> Dict[str, Any]:
        """
        获取套利机会榜单

        返回各类中心性排名和套利机会
        """
        # 计算各类中心性
        topic_centrality = self.calculate_topic_centrality()
        channel_centrality = self.calculate_channel_centrality()
        video_centrality = self.calculate_video_centrality()
        title_word_centrality = self.calculate_title_word_centrality()

        # 按中介中心性排序的 Top N
        betweenness_topics = topic_centrality[:top_n]
        betweenness_channels = channel_centrality[:top_n]
        betweenness_videos = video_centrality[:top_n]
        betweenness_words = title_word_centrality[:top_n]

        # 按程度中心性排序的 Top N
        degree_topics = sorted(topic_centrality, key=lambda x: x['degree'], reverse=True)[:top_n]
        degree_channels = sorted(channel_centrality, key=lambda x: x['degree'], reverse=True)[:top_n]
        degree_videos = sorted(video_centrality, key=lambda x: x['degree'], reverse=True)[:top_n]
        degree_words = sorted(title_word_centrality, key=lambda x: x['degree'], reverse=True)[:top_n]

        # 套利机会：高中介 + 低播放量
        # 找出中介中心性高但播放量低于平均的内容
        avg_video_views = sum(v.get('view_count', 0) for v in video_centrality) / len(video_centrality) if video_centrality else 0

        arbitrage_videos = [
            v for v in video_centrality
            if v['betweenness'] > 0 and v['view_count'] < avg_video_views
        ]
        arbitrage_videos.sort(key=lambda x: x['betweenness'], reverse=True)

        # 高潜力频道：高中介 + 低粉丝
        avg_subs = sum(c.get('subscriber_count', 0) for c in channel_centrality) / len(channel_centrality) if channel_centrality else 0

        arbitrage_channels = [
            c for c in channel_centrality
            if c['betweenness'] > 0 and c['subscriber_count'] < avg_subs
        ]
        arbitrage_channels.sort(key=lambda x: x['betweenness'], reverse=True)

        # 套利话题：高中介 + 低视频数（桥梁话题但未被充分利用）
        avg_topic_videos = sum(t.get('video_count', 0) for t in topic_centrality) / len(topic_centrality) if topic_centrality else 0

        arbitrage_topics = [
            t for t in topic_centrality
            if t['betweenness'] > 0 and t['video_count'] < avg_topic_videos
        ]
        arbitrage_topics.sort(key=lambda x: x['betweenness'], reverse=True)

        # 套利标题词：高中介 + 低使用频率（桥梁词汇但未被充分使用）
        avg_word_count = sum(w.get('count', 0) for w in title_word_centrality) / len(title_word_centrality) if title_word_centrality else 0

        arbitrage_words = [
            w for w in title_word_centrality
            if w['betweenness'] > 0 and w['count'] < avg_word_count
        ]
        arbitrage_words.sort(key=lambda x: x['betweenness'], reverse=True)

        return {
            'betweenness': {
                'topics': betweenness_topics,
                'channels': betweenness_channels,
                'videos': betweenness_videos,
                'words': betweenness_words
            },
            'degree': {
                'topics': degree_topics,
                'channels': degree_channels,
                'videos': degree_videos,
                'words': degree_words
            },
            'arbitrage': {
                'high_betweenness_low_views_videos': arbitrage_videos[:top_n],
                'high_betweenness_low_subs_channels': arbitrage_channels[:top_n],
                'high_betweenness_low_videos_topics': arbitrage_topics[:top_n],
                'high_betweenness_low_count_words': arbitrage_words[:top_n]
            },
            'stats': {
                'total_topics': len(topic_centrality),
                'total_channels': len(channel_centrality),
                'total_videos': len(video_centrality),
                'total_words': len(title_word_centrality),
                'avg_video_views': round(avg_video_views),
                'avg_channel_subs': round(avg_subs),
                'avg_topic_videos': round(avg_topic_videos, 1),
                'avg_word_count': round(avg_word_count, 1)
            }
        }


def get_centrality_data(db_path: str) -> Dict[str, Any]:
    """
    便捷函数：获取中心性分析数据
    """
    analyzer = NetworkCentralityAnalyzer(db_path)
    try:
        return analyzer.get_arbitrage_opportunities()
    finally:
        analyzer.close()


def get_network_graph_data(db_path: str, graph_type: str = 'topic', max_nodes: int = 50) -> Dict[str, Any]:
    """
    获取网络图可视化数据（节点 + 边）

    参数:
    - db_path: 数据库路径
    - graph_type: 'topic' (话题共现网络) 或 'channel' (频道-频道网络)
    - max_nodes: 最大节点数量

    返回:
    - nodes: 节点列表，包含 id, label, betweenness, degree, size, color 等
    - edges: 边列表，包含 from, to, weight
    """
    analyzer = NetworkCentralityAnalyzer(db_path)
    try:
        videos, channel_topics = analyzer._load_video_topic_data()

        if graph_type == 'topic':
            # 构建话题共现图
            graph = analyzer._build_topic_cooccurrence_graph(channel_topics)

            # 统计话题信息
            topic_stats = defaultdict(lambda: {'video_count': 0, 'total_views': 0, 'channels': set()})
            for video in videos:
                topic = video.get('keyword_source')
                if topic:
                    topic_stats[topic]['video_count'] += 1
                    topic_stats[topic]['total_views'] += video.get('view_count', 0) or 0
                    if video.get('channel_id'):
                        topic_stats[topic]['channels'].add(video['channel_id'])

            # 计算中心性
            if HAS_NETWORKX:
                import networkx as nx
                G = nx.Graph()
                for t1, neighbors in graph.items():
                    for t2, weight in neighbors.items():
                        G.add_edge(t1, t2, weight=weight)
                betweenness = nx.betweenness_centrality(G, weight='weight')
                degree = nx.degree_centrality(G)
            else:
                betweenness = analyzer._calculate_betweenness_centrality_simple(graph)
                degree = analyzer._calculate_degree_centrality_simple(graph)

            # 按中介中心性排序，取 top N 节点
            sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            selected_nodes = set(n[0] for n in sorted_nodes)

            # 构建节点数据
            nodes = []
            max_betweenness = max(betweenness.values()) if betweenness else 1
            max_degree = max(degree.values()) if degree else 1

            for node_id in selected_nodes:
                stats = topic_stats[node_id]
                b = betweenness.get(node_id, 0)
                d = degree.get(node_id, 0)
                interestingness = b / max(d, 0.01)

                # 节点大小基于程度中心性
                size = 10 + (d / max_degree) * 40

                # 节点颜色基于中介中心性（0-1 映射到颜色）
                color_intensity = b / max_betweenness if max_betweenness > 0 else 0

                nodes.append({
                    'id': node_id,
                    'label': node_id,
                    'betweenness': round(b, 6),
                    'degree': round(d, 6),
                    'interestingness': round(interestingness, 4),
                    'video_count': stats['video_count'],
                    'total_views': stats['total_views'],
                    'channel_count': len(stats['channels']),
                    'size': round(size, 1),
                    'color_intensity': round(color_intensity, 3)
                })

            # 构建边数据（只包含选中节点之间的边）
            edges = []
            max_weight = 1
            for t1 in selected_nodes:
                for t2, weight in graph.get(t1, {}).items():
                    if t2 in selected_nodes and t1 < t2:  # 避免重复边
                        edges.append({
                            'from': t1,
                            'to': t2,
                            'weight': weight
                        })
                        max_weight = max(max_weight, weight)

            # 归一化边的权重
            for edge in edges:
                edge['width'] = 1 + (edge['weight'] / max_weight) * 4

            return {
                'status': 'ok',
                'graph_type': 'topic',
                'nodes': nodes,
                'edges': edges,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'max_betweenness': round(max_betweenness, 6),
                    'max_degree': round(max_degree, 6)
                }
            }

        elif graph_type == 'channel':
            # 构建频道-频道网络（通过共同话题连接）
            topic_channels = defaultdict(set)
            for channel_id, topics in channel_topics.items():
                for topic in topics:
                    topic_channels[topic].add(channel_id)

            graph = defaultdict(lambda: defaultdict(int))
            for topic, channels in topic_channels.items():
                channels_list = list(channels)
                for i, c1 in enumerate(channels_list):
                    for c2 in channels_list[i+1:]:
                        graph[c1][c2] += 1
                        graph[c2][c1] += 1
            graph = dict(graph)

            # 频道信息
            channel_stats = defaultdict(lambda: {
                'channel_name': '',
                'video_count': 0,
                'total_views': 0,
                'subscriber_count': 0,
                'topics': set()
            })
            for video in videos:
                channel_id = video.get('channel_id')
                if channel_id:
                    stats = channel_stats[channel_id]
                    stats['channel_name'] = video.get('channel_name', '')
                    stats['video_count'] += 1
                    stats['total_views'] += video.get('view_count', 0) or 0
                    stats['subscriber_count'] = max(stats['subscriber_count'], video.get('subscriber_count', 0) or 0)
                    stats['topics'].add(video.get('keyword_source'))

            # 计算中心性
            if HAS_NETWORKX:
                import networkx as nx
                G = nx.Graph()
                for c1, neighbors in graph.items():
                    for c2, weight in neighbors.items():
                        G.add_edge(c1, c2, weight=weight)
                betweenness = nx.betweenness_centrality(G, weight='weight', k=min(100, len(G.nodes())))
                degree = nx.degree_centrality(G)
            else:
                betweenness = analyzer._calculate_betweenness_centrality_simple(graph, k=50)
                degree = analyzer._calculate_degree_centrality_simple(graph)

            # 按中介中心性排序，取 top N
            sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            selected_nodes = set(n[0] for n in sorted_nodes)

            # 构建节点
            nodes = []
            max_betweenness = max(betweenness.values()) if betweenness else 1
            max_degree = max(degree.values()) if degree else 1

            for node_id in selected_nodes:
                stats = channel_stats[node_id]
                b = betweenness.get(node_id, 0)
                d = degree.get(node_id, 0)
                interestingness = b / max(d, 0.01)

                size = 10 + (d / max_degree) * 40
                color_intensity = b / max_betweenness if max_betweenness > 0 else 0

                nodes.append({
                    'id': node_id,
                    'label': stats['channel_name'][:15] if stats['channel_name'] else node_id[:8],
                    'full_name': stats['channel_name'],
                    'betweenness': round(b, 6),
                    'degree': round(d, 6),
                    'interestingness': round(interestingness, 4),
                    'video_count': stats['video_count'],
                    'total_views': stats['total_views'],
                    'subscriber_count': stats['subscriber_count'],
                    'topic_count': len(stats['topics']),
                    'size': round(size, 1),
                    'color_intensity': round(color_intensity, 3)
                })

            # 构建边
            edges = []
            max_weight = 1
            for c1 in selected_nodes:
                for c2, weight in graph.get(c1, {}).items():
                    if c2 in selected_nodes and c1 < c2:
                        edges.append({
                            'from': c1,
                            'to': c2,
                            'weight': weight
                        })
                        max_weight = max(max_weight, weight)

            for edge in edges:
                edge['width'] = 1 + (edge['weight'] / max_weight) * 4

            return {
                'status': 'ok',
                'graph_type': 'channel',
                'nodes': nodes,
                'edges': edges,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'max_betweenness': round(max_betweenness, 6),
                    'max_degree': round(max_degree, 6)
                }
            }

        else:
            return {'status': 'error', 'message': f'Unknown graph type: {graph_type}'}

    finally:
        analyzer.close()


if __name__ == "__main__":
    import json

    # 测试
    db_path = Path(__file__).parent.parent.parent / "data" / "youtube_pipeline.db"

    if db_path.exists():
        print(f"分析数据库: {db_path}")
        data = get_centrality_data(str(db_path))

        print("\n=== 统计信息 ===")
        print(json.dumps(data['stats'], indent=2, ensure_ascii=False))

        print("\n=== 中介中心性 Top 10 话题 ===")
        for i, t in enumerate(data['betweenness']['topics'][:10], 1):
            print(f"{i}. {t['topic']}: betweenness={t['betweenness']:.4f}, videos={t['video_count']}")

        print("\n=== 中介中心性 Top 10 频道 ===")
        for i, c in enumerate(data['betweenness']['channels'][:10], 1):
            print(f"{i}. {c['channel_name']}: betweenness={c['betweenness']:.4f}, topics={c['topic_count']}")

        print("\n=== 套利机会 Top 10 视频 ===")
        for i, v in enumerate(data['arbitrage']['high_betweenness_low_views_videos'][:10], 1):
            print(f"{i}. {v['title'][:30]}...: betweenness={v['betweenness']:.4f}, views={v['view_count']}")
    else:
        print(f"数据库不存在: {db_path}")
