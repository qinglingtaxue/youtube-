#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据收集模块
负责从YouTube收集视频数据并进行初步筛选
"""

import json
import time
import requests
from typing import List, Dict, Any
from pathlib import Path
from urllib.parse import quote_plus

class DataCollector:
    """数据收集器"""
    
    def __init__(self, logger):
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def collect_videos(self, theme: str, max_videos: int = 1000) -> List[Dict[str, Any]]:
        """
        收集视频数据
        
        Args:
            theme: 调研主题
            max_videos: 最大视频数量
            
        Returns:
            视频数据列表
        """
        self.logger.info(f"开始收集主题'{theme}'的视频数据，目标{max_videos}个")
        
        # 生成扩展关键词
        keywords = self._generate_keywords(theme)
        self.logger.info(f"生成了{len(keywords)}个扩展关键词")
        
        all_videos = []
        collected_per_keyword = max_videos // len(keywords)
        
        for keyword in keywords:
            self.logger.info(f"正在收集关键词：{keyword}")
            
            # 模拟数据收集（实际项目中会调用YouTube API或爬虫）
            videos = self._collect_keyword_videos(keyword, collected_per_keyword)
            all_videos.extend(videos)
            
            # 避免请求过快
            time.sleep(1)
            
        # 去重
        unique_videos = self._deduplicate_videos(all_videos)
        
        self.logger.info(f"收集完成，共获得{len(unique_videos)}个去重后的视频")
        
        return unique_videos
    
    def _generate_keywords(self, theme: str) -> List[str]:
        """生成扩展关键词"""
        base_keywords = [theme]
        
        # 根据主题生成相关关键词
        keyword_mappings = {
            '老人养生': ['中医养生', '健康科普', '长寿秘诀', '保健方法', '养生误区'],
            'AI工具': ['人工智能', 'ChatGPT', 'AI应用', '机器学习', 'AI教程'],
            '美食制作': ['家常菜', '烹饪技巧', '美食教程', '地方菜', '甜品制作'],
            '健身教程': ['减肥健身', '居家健身', '瑜伽教程', '力量训练', '有氧运动']
        }
        
        return keyword_mappings.get(theme, base_keywords + [f'{theme}技巧', f'{theme}方法', f'{theme}教程'])
    
    def _collect_keyword_videos(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """收集单个关键词的视频数据"""
        # 模拟从YouTube收集数据
        # 实际项目中这里会调用YouTube API
        
        videos = []
        for i in range(min(limit, 50)):  # 模拟每个关键词收集50个视频
            video = {
                'id': f'video_{keyword}_{i:03d}',
                'title': f'{keyword}相关视频标题_{i+1}',
                'description': f'这是关于{keyword}的详细描述...',
                'channel': f'{keyword}频道_{i%10}',
                'view_count': 10000 + i * 1000,
                'like_count': 500 + i * 50,
                'comment_count': 50 + i * 5,
                'duration': 300 + i * 60,  # 秒
                'publish_date': '2025-11-01',
                'tags': [keyword, f'{keyword}教程', f'{keyword}技巧'],
                'keyword_source': keyword
            }
            videos.append(video)
            
        return videos
    
    def _deduplicate_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复视频"""
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            video_id = video['id']
            if video_id not in seen_ids:
                seen_ids.add(video_id)
                unique_videos.append(video)
                
        return unique_videos
    
    def filter_quality_videos(self, videos: List[Dict[str, Any]], 
                            min_views: int = 1000,
                            min_likes: int = 50,
                            max_duration: int = 3600) -> List[Dict[str, Any]]:
        """筛选高质量视频"""
        filtered = []
        
        for video in videos:
            if (video.get('view_count', 0) >= min_views and
                video.get('like_count', 0) >= min_likes and
                video.get('duration', 0) <= max_duration):
                filtered.append(video)
                
        self.logger.info(f"质量筛选：从{len(videos)}个视频中筛选出{len(filtered)}个高质量视频")
        return filtered
    
    def save_videos(self, videos: List[Dict[str, Any]], output_file: Path):
        """保存视频数据"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"视频数据已保存到：{output_file}")
    
    def load_videos(self, input_file: Path) -> List[Dict[str, Any]]:
        """加载视频数据"""
        if not input_file.exists():
            return []
            
        with open(input_file, 'r', encoding='utf-8') as f:
            videos = json.load(f)
            
        self.logger.info(f"从{input_file}加载了{len(videos)}个视频数据")
        return videos
