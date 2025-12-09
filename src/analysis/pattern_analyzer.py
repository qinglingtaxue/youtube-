#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式分析模块
从视频数据中识别创作模式
"""

import json
import re
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from pathlib import Path

class PatternAnalyzer:
    """模式分析器"""
    
    def __init__(self, logger):
        self.logger = logger
        # 预定义的创作模式
        self.pattern_templates = {
            'cognitive_impact': {
                'name': '认知冲击型',
                'keywords': ['颠覆', '真相', '你以为', '其实', '90%', '研究显示', '专家'],
                'structures': ['冲击观点', '数据支撑', '权威背书', '行动引导'],
                'score_weight': 0.8
            },
            'storytelling': {
                'name': '故事叙述型',
                'keywords': ['故事', '经历', '去年', '朋友', '后来', '终于', '明白'],
                'structures': ['故事背景', '冲突发展', '解决升华'],
                'score_weight': 0.7
            },
            'knowledge_sharing': {
                'name': '干货输出型',
                'keywords': ['方法', '技巧', '3个步骤', '如何', '教程', '干货'],
                'structures': ['问题提出', '方法拆解', '案例验证'],
                'score_weight': 0.9
            },
            'interaction_guide': {
                'name': '互动引导型',
                'keywords': ['你觉得', '评论', '关注', '分享', '投票', '问答'],
                'structures': ['悬念设置', '互动提问', '引导关注'],
                'score_weight': 0.6
            }
        }
        
    def analyze_videos(self, videos: List[Dict[str, Any]], max_cases: int = 10) -> Dict[str, Any]:
        """
        分析视频数据，识别模式和精选案例
        
        Args:
            videos: 视频数据列表
            max_cases: 最大案例数量
            
        Returns:
            分析结果
        """
        self.logger.info(f"开始分析{len(videos)}个视频，识别创作模式")
        
        # 1. 计算每个视频的模式匹配度
        video_patterns = []
        for video in videos:
            pattern_scores = self._calculate_pattern_scores(video)
            video['pattern_scores'] = pattern_scores
            video_patterns.append(video)
            
        # 2. 根据模式和播放量筛选最佳案例
        selected_cases = self._select_best_cases(video_patterns, max_cases)
        
        # 3. 分析模式分布
        pattern_distribution = self._analyze_pattern_distribution(selected_cases)
        
        # 4. 提取典型特征
        typical_features = self._extract_typical_features(selected_cases)
        
        result = {
            'total_videos': len(videos),
            'selected_cases': selected_cases,
            'pattern_distribution': pattern_distribution,
            'typical_features': typical_features,
            'patterns_summary': self._generate_patterns_summary(selected_cases)
        }
        
        self.logger.info(f"模式分析完成：识别出{len(selected_cases)}个典型案例，{len(pattern_distribution)}种模式")
        return result
    
    def _calculate_pattern_scores(self, video: Dict[str, Any]) -> Dict[str, float]:
        """计算视频与各模式的匹配度"""
        scores = {}
        text_content = f"{video.get('title', '')} {video.get('description', '')}"
        
        for pattern_key, pattern_info in self.pattern_templates.items():
            score = 0.0
            
            # 关键词匹配
            keyword_matches = sum(1 for keyword in pattern_info['keywords'] 
                                if keyword in text_content)
            keyword_score = min(keyword_matches / len(pattern_info['keywords']), 1.0)
            
            # 数据指标匹配
            view_score = min(video.get('view_count', 0) / 100000, 1.0)  # 10万播放为满分
            engagement_score = self._calculate_engagement_score(video)
            
            # 综合得分
            score = (keyword_score * 0.4 + view_score * 0.3 + engagement_score * 0.3)
            scores[pattern_key] = score * pattern_info['score_weight']
            
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
        
        return min((like_rate + comment_rate) * 100, 1.0)
    
    def _select_best_cases(self, videos: List[Dict[str, Any]], max_cases: int) -> List[Dict[str, Any]]:
        """筛选最佳案例"""
        # 按综合得分排序
        def calculate_comprehensive_score(video):
            pattern_score = max(video['pattern_scores'].values())
            view_score = min(video.get('view_count', 0) / 50000, 1.0)
            engagement_score = self._calculate_engagement_score(video)
            
            return pattern_score * 0.5 + view_score * 0.3 + engagement_score * 0.2
        
        videos.sort(key=calculate_comprehensive_score, reverse=True)
        
        # 确保模式多样性
        selected = []
        pattern_counts = defaultdict(int)
        
        for video in videos:
            if len(selected) >= max_cases:
                break
                
            # 找到最佳匹配模式
            best_pattern = max(video['pattern_scores'].items(), key=lambda x: x[1])[0]
            
            # 如果该模式案例过多，跳过
            if pattern_counts[best_pattern] >= max_cases // 3:
                continue
                
            video['primary_pattern'] = best_pattern
            video['pattern_name'] = self.pattern_templates[best_pattern]['name']
            selected.append(video)
            pattern_counts[best_pattern] += 1
            
        return selected
    
    def _analyze_pattern_distribution(self, cases: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析模式分布"""
        pattern_counts = Counter()
        for case in cases:
            pattern = case.get('primary_pattern', 'unknown')
            pattern_counts[pattern] += 1
            
        return dict(pattern_counts)
    
    def _extract_typical_features(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取典型特征"""
        features = {}
        
        for pattern_key in self.pattern_templates.keys():
            pattern_cases = [c for c in cases if c.get('primary_pattern') == pattern_key]
            
            if not pattern_cases:
                continue
                
            # 分析标题特征
            titles = [c.get('title', '') for c in pattern_cases]
            title_patterns = self._analyze_title_patterns(titles)
            
            # 分析内容特征
            descriptions = [c.get('description', '') for c in pattern_cases]
            content_patterns = self._analyze_content_patterns(descriptions)
            
            features[pattern_key] = {
                'name': self.pattern_templates[pattern_key]['name'],
                'case_count': len(pattern_cases),
                'title_patterns': title_patterns,
                'content_patterns': content_patterns,
                'avg_views': sum(c.get('view_count', 0) for c in pattern_cases) // len(pattern_cases),
                'avg_engagement': sum(self._calculate_engagement_score(c) for c in pattern_cases) / len(pattern_cases)
            }
            
        return features
    
    def _analyze_title_patterns(self, titles: List[str]) -> Dict[str, Any]:
        """分析标题模式"""
        # 提取常见开头
        opening_patterns = Counter()
        for title in titles:
            if len(title) > 10:
                opening = title[:10]
                opening_patterns[opening] += 1
                
        # 提取常见关键词
        all_words = []
        for title in titles:
            words = re.findall(r'[\w]+', title)
            all_words.extend(words)
            
        common_words = Counter(all_words).most_common(10)
        
        return {
            'common_openings': dict(opening_patterns.most_common(5)),
            'common_words': dict(common_words)
        }
    
    def _analyze_content_patterns(self, descriptions: List[str]) -> Dict[str, Any]:
        """分析内容模式"""
        # 统计描述长度
        lengths = [len(desc) for desc in descriptions]
        
        return {
            'avg_length': sum(lengths) / len(lengths) if lengths else 0,
            'min_length': min(lengths) if lengths else 0,
            'max_length': max(lengths) if lengths else 0
        }
    
    def _generate_patterns_summary(self, cases: List[Dict[str, Any]]) -> str:
        """生成模式总结"""
        summary_parts = []
        
        pattern_groups = defaultdict(list)
        for case in cases:
            pattern = case.get('primary_pattern', 'unknown')
            pattern_groups[pattern].append(case)
            
        for pattern_key, pattern_cases in pattern_groups.items():
            if not pattern_cases:
                continue
                
            pattern_name = self.pattern_templates.get(pattern_key, {}).get('name', pattern_key)
            count = len(pattern_cases)
            avg_views = sum(c.get('view_count', 0) for c in pattern_cases) // count
            
            summary_parts.append(f"- {pattern_name}：{count}个案例，平均播放量{avg_views:,}")
            
        return '\n'.join(summary_parts)
    
    def save_analysis_result(self, result: Dict[str, Any], output_file: Path):
        """保存分析结果"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"分析结果已保存到：{output_file}")
