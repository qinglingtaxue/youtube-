#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML解析工具
解析MCP返回的HTML内容，提取视频信息
"""

import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from utils.logger import setup_logger

logger = setup_logger('html_parser')

def parse_youtube_search_results(html_content: str) -> List[Dict[str, Any]]:
    """
    解析YouTube搜索结果页面HTML

    Args:
        html_content: 页面HTML内容

    Returns:
        视频信息列表
    """
    videos = []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找视频容器
        video_containers = soup.find_all('div', {'id': 'video-title'})

        for container in video_containers:
            try:
                # 提取标题
                title = container.get('title', '').strip()

                # 查找观看量
                views_text = ''
                view_container = container.find_parent().find('span', string=re.compile(r'次观看'))
                if view_container:
                    views_text = view_container.text.strip()

                # 查找频道名
                channel_name = ''
                channel_container = container.find_parent().find('a', {'href': re.compile(r'/channel/')})
                if channel_container:
                    channel_name = channel_container.text.strip()

                # 查找发布时间
                published_text = ''
                published_container = container.find_parent().find('span', string=re.compile(r'\d+.*前'))
                if published_container:
                    published_text = published_container.text.strip()

                video_info = {
                    'title': title,
                    'channel': channel_name,
                    'views': views_text,
                    'published': published_text,
                    'url': ''
                }

                if video_info['title']:  # 只添加有标题的视频
                    videos.append(video_info)

            except Exception as e:
                logger.warning(f"解析单个视频失败: {e}")
                continue

    except Exception as e:
        logger.error(f"解析HTML失败: {e}")

    logger.info(f"解析到 {len(videos)} 个视频")
    return videos

def parse_tiktok_search_results(html_content: str) -> List[Dict[str, Any]]:
    """
    解析TikTok搜索结果页面HTML

    Args:
        html_content: 页面HTML内容

    Returns:
        视频信息列表
    """
    videos = []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # TikTok的HTML结构比较复杂，需要根据实际情况调整
        # 这里只是一个示例

        # 查找视频标题
        title_containers = soup.find_all('div', {'data-e2e': 'search-video-card'})

        for container in title_containers:
            try:
                title = container.find('div', {'data-e2e': 'search-video-card-title'})
                if title:
                    title = title.text.strip()

                # 提取其他信息
                video_info = {
                    'title': title,
                    'creator': '',
                    'views': '',
                    'likes': '',
                    'url': ''
                }

                if video_info['title']:
                    videos.append(video_info)

            except Exception as e:
                logger.warning(f"解析TikTok视频失败: {e}")
                continue

    except Exception as e:
        logger.error(f"解析TikTok HTML失败: {e}")

    logger.info(f"解析到 {len(videos)} 个TikTok视频")
    return videos

def parse_facebook_search_results(html_content: str) -> List[Dict[str, Any]]:
    """
    解析Facebook搜索结果页面HTML

    Args:
        html_content: 页面HTML内容

    Returns:
        帖子信息列表
    """
    posts = []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Facebook的HTML结构
        post_containers = soup.find_all('div', {'role': 'article'})

        for container in post_containers:
            try:
                # 提取帖子内容
                content = container.get_text(strip=True)

                # 提取互动数据
                likes = 0
                like_containers = container.find_all('span', string=re.compile(r'\d+.*赞'))
                if like_containers:
                    likes = extract_number(like_containers[0].text)

                post_info = {
                    'content': content[:100],  # 截取前100字符
                    'likes': likes,
                    'comments': 0,
                    'shares': 0,
                    'url': ''
                }

                if post_info['content']:
                    posts.append(post_info)

            except Exception as e:
                logger.warning(f"解析Facebook帖子失败: {e}")
                continue

    except Exception as e:
        logger.error(f"解析Facebook HTML失败: {e}")

    logger.info(f"解析到 {len(posts)} 个Facebook帖子")
    return posts

def parse_instagram_search_results(html_content: str) -> List[Dict[str, Any]]:
    """
    解析Instagram搜索结果页面HTML

    Args:
        html_content: 页面HTML内容

    Returns:
        帖子信息列表
    """
    posts = []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Instagram的HTML结构
        post_containers = soup.find_all('div', {'class': '_aagv'})

        for container in post_containers:
            try:
                # 提取图片alt文本作为内容
                img = container.find('img')
                content = img.get('alt', '') if img else ''

                # 提取互动数据
                likes = 0
                like_containers = container.find_all('span', string=re.compile(r'\d+'))
                if like_containers:
                    likes = extract_number(like_containers[0].text)

                post_info = {
                    'content': content[:100],
                    'likes': likes,
                    'comments': 0,
                    'url': ''
                }

                if post_info['content']:
                    posts.append(post_info)

            except Exception as e:
                logger.warning(f"解析Instagram帖子失败: {e}")
                continue

    except Exception as e:
        logger.error(f"解析Instagram HTML失败: {e}")

    logger.info(f"解析到 {len(posts)} 个Instagram帖子")
    return posts

def extract_number(text: str) -> int:
    """从文本中提取数字"""
    if not text:
        return 0

    # 移除非数字字符，保留数字
    numbers = re.findall(r'\d+', text.replace(',', ''))
    if numbers:
        return int(numbers[0])

    return 0
