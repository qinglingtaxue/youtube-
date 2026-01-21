#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式分析模块
从视频数据中识别创作模式

引用规约：
- api.spec.md: 3.2 PatternAnalyzer 接口
- data.spec.md: CompetitorVideo 实体
- pipeline.spec.md: Stage 2 调研阶段

功能：
- 分析视频创作模式
- 识别高效模式
- 提取典型特征
- 生成分析报告
"""

import json
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.logger import setup_logger
from src.shared.config import get_config, Config


class PatternAnalyzer:
    """
    模式分析器

    基于 api.spec.md 3.2 PatternAnalyzer 接口实现
    """

    def __init__(self, config: Optional[Config] = None):
        """
        初始化模式分析器

        Args:
            config: 配置对象 (可选)
        """
        self.config = config or get_config()
        self.logger = setup_logger('pattern_analyzer')

        # 从配置读取参数
        self.min_pattern_frequency = self.config.get('analysis.min_pattern_frequency', 3)
        self.similarity_threshold = self.config.get('analysis.similarity_threshold', 0.8)

        # 加载模式模板
        self.pattern_templates = self._load_pattern_templates()

    def _load_pattern_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        加载预定义的创作模式模板

        基于 pipeline.spec.md 中定义的四种模式
        """
        return {
            'cognitive_impact': {
                'name': '认知冲击型',
                'description': '通过颠覆认知或提供新视角吸引观众',
                'keywords': [
                    '颠覆', '真相', '你以为', '其实', '90%', '研究显示',
                    '专家', '震惊', '真没想到', '原来', '秘密', '内幕'
                ],
                'title_patterns': [
                    r'.*你不知道.*',
                    r'.*\d+%.*',
                    r'.*真相.*',
                    r'.*颠覆.*',
                    r'.*专家.*',
                ],
                'structures': ['冲击观点', '数据支撑', '权威背书', '行动引导'],
                'score_weight': 0.8,
                'typical_duration': (300, 900),  # 5-15分钟
            },
            'storytelling': {
                'name': '故事叙述型',
                'description': '通过故事引发情感共鸣',
                'keywords': [
                    '故事', '经历', '去年', '朋友', '后来', '终于',
                    '明白', '那时候', '从前', '记得', '发生', '遇到'
                ],
                'title_patterns': [
                    r'.*我.*故事.*',
                    r'.*经历.*',
                    r'.*从.*到.*',
                    r'.*之后.*',
                ],
                'structures': ['故事背景', '冲突发展', '解决升华'],
                'score_weight': 0.7,
                'typical_duration': (600, 1200),  # 10-20分钟
            },
            'knowledge_sharing': {
                'name': '干货输出型',
                'description': '提供实用信息和方法论',
                'keywords': [
                    '方法', '技巧', '步骤', '如何', '教程', '干货',
                    '指南', '秘诀', '攻略', '要点', '诀窍', '必看'
                ],
                'title_patterns': [
                    r'.*\d+个?[种方技].*',
                    r'.*如何.*',
                    r'.*教程.*',
                    r'.*指南.*',
                    r'.*完全.*',
                ],
                'structures': ['问题提出', '方法拆解', '案例验证'],
                'score_weight': 0.9,
                'typical_duration': (480, 900),  # 8-15分钟
            },
            'interaction_guide': {
                'name': '互动引导型',
                'description': '通过互动提升参与度',
                'keywords': [
                    '你觉得', '评论', '关注', '分享', '投票', '问答',
                    '留言', '讨论', '选择', '告诉我', '你会', '你是'
                ],
                'title_patterns': [
                    r'.*你.*吗.*',
                    r'.*哪个.*',
                    r'.*选.*',
                    r'.*pk.*',
                ],
                'structures': ['悬念设置', '互动提问', '引导关注'],
                'score_weight': 0.6,
                'typical_duration': (180, 600),  # 3-10分钟
            }
        }

    def analyze_videos(
        self,
        videos: List[Dict[str, Any]],
        max_cases: int = 10
    ) -> Dict[str, Any]:
        """
        分析视频模式

        符合 api.spec.md 3.2 PatternAnalyzer.analyze_videos 接口

        Args:
            videos: 视频列表
            max_cases: 最大案例数

        Returns:
            AnalysisResult:
                total_videos: int
                selected_cases: List[CompetitorVideo]
                pattern_distribution: Dict[str, int]
                typical_features: Dict[str, Any]
                patterns_summary: str
        """
        self.logger.info(f"开始分析 {len(videos)} 个视频，识别创作模式")

        if not videos:
            return self._empty_result()

        # 1. 为每个视频计算模式得分
        video_patterns = []
        for video in videos:
            pattern_scores = self._calculate_pattern_scores(video)
            video['pattern_scores'] = pattern_scores
            video_patterns.append(video)

        # 2. 筛选最佳案例
        selected_cases = self._select_best_cases(video_patterns, max_cases)

        # 3. 分析模式分布
        pattern_distribution = self._analyze_pattern_distribution(selected_cases)

        # 4. 提取典型特征
        typical_features = self._extract_typical_features(selected_cases)

        # 5. 计算统计数据
        statistics = self._calculate_statistics(videos, selected_cases)

        result = {
            'total_videos': len(videos),
            'selected_cases': selected_cases,
            'pattern_distribution': pattern_distribution,
            'typical_features': typical_features,
            'patterns_summary': self._generate_patterns_summary(selected_cases),
            'statistics': statistics,
            'analyzed_at': datetime.now().isoformat()
        }

        self.logger.info(
            f"模式分析完成：识别出 {len(selected_cases)} 个典型案例，"
            f"{len(pattern_distribution)} 种模式"
        )
        return result

    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'total_videos': 0,
            'selected_cases': [],
            'pattern_distribution': {},
            'typical_features': {},
            'patterns_summary': '无数据',
            'statistics': {},
            'analyzed_at': datetime.now().isoformat()
        }

    def identify_pattern(
        self,
        video: Dict[str, Any]
    ) -> Tuple[str, float]:
        """
        识别单个视频的模式

        符合 api.spec.md 3.2 PatternAnalyzer.identify_pattern 接口

        Args:
            video: 视频对象

        Returns:
            (pattern_type, confidence_score)
        """
        scores = self._calculate_pattern_scores(video)

        if not scores:
            return ('unknown', 0.0)

        best_pattern = max(scores.items(), key=lambda x: x[1])
        return (best_pattern[0], best_pattern[1])

    def _calculate_pattern_scores(self, video: Dict[str, Any]) -> Dict[str, float]:
        """计算视频与各模式的匹配度"""
        scores = {}
        title = video.get('title', '')
        description = video.get('description', '')
        text_content = f"{title} {description}".lower()
        duration = video.get('duration', 0)

        for pattern_key, pattern_info in self.pattern_templates.items():
            score = 0.0

            # 1. 关键词匹配 (40%)
            keyword_matches = sum(
                1 for keyword in pattern_info['keywords']
                if keyword.lower() in text_content
            )
            keyword_score = min(keyword_matches / max(len(pattern_info['keywords']), 1), 1.0)

            # 2. 标题模式匹配 (20%)
            title_pattern_score = 0.0
            for pattern in pattern_info.get('title_patterns', []):
                if re.match(pattern, title, re.IGNORECASE):
                    title_pattern_score = 1.0
                    break

            # 3. 时长匹配 (10%)
            duration_score = 0.0
            typical_duration = pattern_info.get('typical_duration', (0, 3600))
            if typical_duration[0] <= duration <= typical_duration[1]:
                duration_score = 1.0
            elif duration > 0:
                # 部分匹配
                if duration < typical_duration[0]:
                    duration_score = duration / typical_duration[0]
                else:
                    duration_score = typical_duration[1] / duration

            # 4. 数据指标匹配 (30%)
            view_score = min(video.get('view_count', 0) / 100000, 1.0)
            engagement_score = self._calculate_engagement_score(video)
            data_score = view_score * 0.5 + engagement_score * 0.5

            # 综合得分
            score = (
                keyword_score * 0.4 +
                title_pattern_score * 0.2 +
                duration_score * 0.1 +
                data_score * 0.3
            ) * pattern_info['score_weight']

            scores[pattern_key] = round(score, 4)

        return scores

    def _calculate_engagement_score(self, video: Dict[str, Any]) -> float:
        """计算互动得分"""
        views = video.get('view_count', 0)
        likes = video.get('like_count', 0)
        comments = video.get('comment_count', 0)

        if views == 0:
            return 0.0

        # 点赞率 + 评论率
        like_rate = likes / views
        comment_rate = comments / views

        # 合理范围内的互动率 (1-10% 为优秀)
        engagement_rate = like_rate + comment_rate
        return min(engagement_rate * 20, 1.0)

    def _select_best_cases(
        self,
        videos: List[Dict[str, Any]],
        max_cases: int
    ) -> List[Dict[str, Any]]:
        """筛选最佳案例，确保模式多样性"""

        def calculate_comprehensive_score(video):
            pattern_scores = video.get('pattern_scores', {})
            best_pattern_score = max(pattern_scores.values()) if pattern_scores else 0
            view_score = min(video.get('view_count', 0) / 50000, 1.0)
            engagement_score = self._calculate_engagement_score(video)

            return best_pattern_score * 0.5 + view_score * 0.3 + engagement_score * 0.2

        # 按综合得分排序
        videos.sort(key=calculate_comprehensive_score, reverse=True)

        # 确保模式多样性
        selected = []
        pattern_counts = defaultdict(int)
        max_per_pattern = max(max_cases // 3, 2)

        for video in videos:
            if len(selected) >= max_cases:
                break

            # 找到最佳匹配模式
            pattern_scores = video.get('pattern_scores', {})
            if not pattern_scores:
                continue

            best_pattern = max(pattern_scores.items(), key=lambda x: x[1])
            pattern_key, pattern_score = best_pattern

            # 如果该模式案例过多，跳过
            if pattern_counts[pattern_key] >= max_per_pattern:
                continue

            # 添加模式信息
            video['primary_pattern'] = pattern_key
            video['pattern_name'] = self.pattern_templates[pattern_key]['name']
            video['pattern_confidence'] = pattern_score

            selected.append(video)
            pattern_counts[pattern_key] += 1

        return selected

    def _analyze_pattern_distribution(self, cases: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析模式分布"""
        pattern_counts = Counter()
        for case in cases:
            pattern = case.get('primary_pattern', 'unknown')
            pattern_counts[pattern] += 1

        return dict(pattern_counts)

    def _extract_typical_features(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取各模式的典型特征"""
        features = {}

        for pattern_key in self.pattern_templates.keys():
            pattern_cases = [
                c for c in cases
                if c.get('primary_pattern') == pattern_key
            ]

            if not pattern_cases:
                continue

            # 标题特征
            titles = [c.get('title', '') for c in pattern_cases]
            title_analysis = self._analyze_titles(titles)

            # 内容特征
            descriptions = [c.get('description', '') for c in pattern_cases]
            content_analysis = self._analyze_content(descriptions)

            # 时长特征
            durations = [c.get('duration', 0) for c in pattern_cases if c.get('duration')]
            duration_analysis = {
                'avg': sum(durations) / len(durations) if durations else 0,
                'min': min(durations) if durations else 0,
                'max': max(durations) if durations else 0
            }

            # 数据特征
            views = [c.get('view_count', 0) for c in pattern_cases]
            likes = [c.get('like_count', 0) for c in pattern_cases]

            features[pattern_key] = {
                'name': self.pattern_templates[pattern_key]['name'],
                'description': self.pattern_templates[pattern_key]['description'],
                'case_count': len(pattern_cases),
                'title_analysis': title_analysis,
                'content_analysis': content_analysis,
                'duration_analysis': duration_analysis,
                'avg_views': sum(views) // len(views) if views else 0,
                'avg_likes': sum(likes) // len(likes) if likes else 0,
                'avg_engagement': sum(
                    self._calculate_engagement_score(c)
                    for c in pattern_cases
                ) / len(pattern_cases),
                'typical_titles': titles[:3]  # 示例标题
            }

        return features

    def _analyze_titles(self, titles: List[str]) -> Dict[str, Any]:
        """分析标题特征"""
        if not titles:
            return {}

        # 提取常见关键词
        all_words = []
        for title in titles:
            words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', title)
            all_words.extend([w for w in words if len(w) > 1])

        word_freq = Counter(all_words).most_common(15)

        # 标题长度分析
        lengths = [len(t) for t in titles]

        # 检测标题模式
        has_numbers = sum(1 for t in titles if re.search(r'\d', t))
        has_questions = sum(1 for t in titles if '?' in t or '？' in t)
        has_emoji = sum(1 for t in titles if re.search(r'[\U0001F600-\U0001F64F]', t))

        return {
            'common_words': dict(word_freq),
            'avg_length': sum(lengths) / len(lengths),
            'has_numbers_ratio': has_numbers / len(titles),
            'has_questions_ratio': has_questions / len(titles),
            'has_emoji_ratio': has_emoji / len(titles)
        }

    def _analyze_content(self, descriptions: List[str]) -> Dict[str, Any]:
        """分析内容特征"""
        if not descriptions:
            return {}

        lengths = [len(d) for d in descriptions if d]

        # 检测常见元素
        has_links = sum(1 for d in descriptions if 'http' in d.lower())
        has_timestamps = sum(1 for d in descriptions if re.search(r'\d+:\d+', d))
        has_hashtags = sum(1 for d in descriptions if '#' in d)

        return {
            'avg_length': sum(lengths) / len(lengths) if lengths else 0,
            'min_length': min(lengths) if lengths else 0,
            'max_length': max(lengths) if lengths else 0,
            'has_links_ratio': has_links / len(descriptions) if descriptions else 0,
            'has_timestamps_ratio': has_timestamps / len(descriptions) if descriptions else 0,
            'has_hashtags_ratio': has_hashtags / len(descriptions) if descriptions else 0
        }

    def _calculate_statistics(
        self,
        all_videos: List[Dict[str, Any]],
        selected_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算统计数据"""
        if not all_videos:
            return {}

        all_views = [v.get('view_count', 0) for v in all_videos if v.get('view_count')]
        all_likes = [v.get('like_count', 0) for v in all_videos if v.get('like_count')]
        all_durations = [v.get('duration', 0) for v in all_videos if v.get('duration')]

        return {
            'total_videos': len(all_videos),
            'selected_cases': len(selected_cases),
            'view_stats': {
                'total': sum(all_views),
                'avg': sum(all_views) / len(all_views) if all_views else 0,
                'max': max(all_views) if all_views else 0,
                'min': min(all_views) if all_views else 0
            },
            'like_stats': {
                'total': sum(all_likes),
                'avg': sum(all_likes) / len(all_likes) if all_likes else 0
            },
            'duration_stats': {
                'avg': sum(all_durations) / len(all_durations) if all_durations else 0,
                'max': max(all_durations) if all_durations else 0,
                'min': min(all_durations) if all_durations else 0
            }
        }

    def _generate_patterns_summary(self, cases: List[Dict[str, Any]]) -> str:
        """生成模式总结文本"""
        if not cases:
            return "无数据"

        summary_parts = []
        pattern_groups = defaultdict(list)

        for case in cases:
            pattern = case.get('primary_pattern', 'unknown')
            pattern_groups[pattern].append(case)

        for pattern_key, pattern_cases in sorted(
            pattern_groups.items(),
            key=lambda x: len(x[1]),
            reverse=True
        ):
            if not pattern_cases:
                continue

            pattern_info = self.pattern_templates.get(pattern_key, {})
            pattern_name = pattern_info.get('name', pattern_key)
            count = len(pattern_cases)
            avg_views = sum(c.get('view_count', 0) for c in pattern_cases) // count

            summary_parts.append(
                f"- **{pattern_name}**：{count}个案例，平均播放量 {avg_views:,}"
            )

        return '\n'.join(summary_parts)

    def save_analysis_result(
        self,
        result: Dict[str, Any],
        output_path: Path
    ) -> None:
        """保存分析结果"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)

        self.logger.info(f"分析结果已保存到：{output_path}")

    def load_analysis_result(self, input_path: Path) -> Optional[Dict[str, Any]]:
        """加载分析结果"""
        input_path = Path(input_path)

        if not input_path.exists():
            self.logger.warning(f"文件不存在: {input_path}")
            return None

        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_pattern_recommendations(
        self,
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        根据分析结果生成模式推荐

        Args:
            analysis_result: 分析结果

        Returns:
            推荐列表，按效果排序
        """
        recommendations = []
        typical_features = analysis_result.get('typical_features', {})

        for pattern_key, features in typical_features.items():
            pattern_info = self.pattern_templates.get(pattern_key, {})

            # 计算推荐分数
            score = (
                features.get('avg_views', 0) / 100000 * 0.4 +
                features.get('avg_engagement', 0) * 0.4 +
                features.get('case_count', 0) / 10 * 0.2
            )

            recommendations.append({
                'pattern': pattern_key,
                'name': pattern_info.get('name', pattern_key),
                'description': pattern_info.get('description', ''),
                'score': round(score, 4),
                'avg_views': features.get('avg_views', 0),
                'avg_engagement': features.get('avg_engagement', 0),
                'case_count': features.get('case_count', 0),
                'structures': pattern_info.get('structures', []),
                'typical_titles': features.get('typical_titles', [])
            })

        # 按分数排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations


# 便捷函数
def analyze_videos(
    videos: List[Dict[str, Any]],
    max_cases: int = 10
) -> Dict[str, Any]:
    """便捷分析函数"""
    analyzer = PatternAnalyzer()
    return analyzer.analyze_videos(videos, max_cases)


if __name__ == '__main__':
    import sys

    # 测试
    print("模式分析器测试")

    analyzer = PatternAnalyzer()

    # 测试单个视频识别
    test_video = {
        'title': '3个方法帮你快速提升效率，90%的人都不知道！',
        'description': '这是一个关于效率提升的教程，包含详细的步骤说明...',
        'view_count': 50000,
        'like_count': 2000,
        'comment_count': 100,
        'duration': 600
    }

    pattern, confidence = analyzer.identify_pattern(test_video)
    print(f"\n测试视频模式识别:")
    print(f"  模式: {pattern}")
    print(f"  置信度: {confidence:.4f}")
    print(f"  模式名称: {analyzer.pattern_templates[pattern]['name']}")
