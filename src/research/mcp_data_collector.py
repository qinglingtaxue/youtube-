#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于MCP Fetch的数据收集器
使用mcp-server-fetch进行真实的网页浏览和数据收集
替代YouTube API方案
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger
from utils.config import get_config
from utils.file_utils import ensure_dir, write_json
from utils.validators import validate_string, sanitize_filename

logger = setup_logger('mcp_data_collector')

class MCPDataCollector:
    """基于MCP Fetch的数据收集器"""

    def __init__(self, config):
        """
        初始化MCP数据收集器

        Args:
            config: 配置对象
        """
        self.config = config
        self.cache_dir = Path('cache/mcp_data')
        ensure_dir(self.cache_dir)
        logger.info("MCP数据收集器初始化完成")

    def search_youtube_videos(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        使用MCP Fetch搜索YouTube视频

        Args:
            query: 搜索关键词
            max_results: 最大结果数

        Returns:
            视频数据列表
        """
        logger.info(f"使用MCP Fetch搜索YouTube视频: {query}")

        # 构建YouTube搜索URL
        search_url = f"https://www.youtube.com/results?search_query={query}&sp=CAI%253D"

        try:
            # 使用MCP Fetch获取搜索结果页面
            html_content = self._fetch_with_mcp(search_url)

            # 解析HTML提取视频信息
            videos = self._parse_youtube_search_results(html_content, query)

            # 限制结果数量
            videos = videos[:max_results]

            logger.info(f"成功获取 {len(videos)} 个视频")

            # 保存原始数据
            cache_file = self.cache_dir / f"search_{sanitize_filename(query)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            write_json(cache_file, {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'videos': videos
            })

            return videos

        except Exception as e:
            logger.error(f"搜索YouTube视频失败: {e}")
            raise

    def get_video_details(self, video_url: str) -> Dict[str, Any]:
        """
        使用MCP Fetch获取视频详细信息

        Args:
            video_url: 视频URL

        Returns:
            视频详细信息
        """
        logger.debug(f"获取视频详情: {video_url}")

        try:
            # 使用MCP Fetch获取视频页面
            html_content = self._fetch_with_mcp(video_url)

            # 解析视频信息
            video_info = self._parse_video_details(html_content, video_url)

            # 保存视频详情
            cache_file = self.cache_dir / f"video_{video_info['id']}.json"
            write_json(cache_file, video_info)

            return video_info

        except Exception as e:
            logger.error(f"获取视频详情失败 {video_url}: {e}")
            raise

    def get_trending_videos(self, category: str = "", max_results: int = 50) -> List[Dict[str, Any]]:
        """
        获取热门视频

        Args:
            category: 视频分类
            max_results: 最大结果数

        Returns:
            热门视频列表
        """
        logger.info(f"获取热门视频: {category or '全部'}")

        try:
            # 构建热门视频URL
            if category:
                trending_url = f"https://www.youtube.com/feed/trending"
            else:
                trending_url = "https://www.youtube.com/feed/trending"

            # 使用MCP Fetch获取热门页面
            html_content = self._fetch_with_mcp(trending_url)

            # 解析热门视频
            videos = self._parse_trending_videos(html_content)

            # 限制结果数量
            videos = videos[:max_results]

            logger.info(f"成功获取 {len(videos)} 个热门视频")

            return videos

        except Exception as e:
            logger.error(f"获取热门视频失败: {e}")
            raise

    def get_channel_videos(self, channel_url: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        获取频道视频

        Args:
            channel_url: 频道URL
            max_results: 最大结果数

        Returns:
            频道视频列表
        """
        logger.info(f"获取频道视频: {channel_url}")

        try:
            # 使用MCP Fetch获取频道页面
            html_content = self._fetch_with_mcp(channel_url)

            # 解析频道视频
            videos = self._parse_channel_videos(html_content, channel_url)

            # 限制结果数量
            videos = videos[:max_results]

            logger.info(f"成功获取 {len(videos)} 个频道视频")

            return videos

        except Exception as e:
            logger.error(f"获取频道视频失败 {channel_url}: {e}")
            raise

    def batch_collect_videos(self, urls: List[str], max_workers: int = 3) -> List[Dict[str, Any]]:
        """
        批量收集视频详情

        Args:
            urls: 视频URL列表
            max_workers: 并发数

        Returns:
            视频详情列表
        """
        logger.info(f"批量收集 {len(urls)} 个视频详情")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        videos = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.get_video_details, url): url
                for url in urls
            }

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    video_info = future.result()
                    videos.append(video_info)
                    logger.debug(f"已收集: {video_info.get('title', url)}")
                except Exception as e:
                    logger.error(f"收集视频失败 {url}: {e}")

        logger.info(f"批量收集完成，成功 {len(videos)}/{len(urls)} 个")
        return videos

    def _fetch_with_mcp(self, url: str) -> str:
        """
        使用MCP Fetch获取网页内容

        Args:
            url: 目标URL

        Returns:
            HTML内容
        """
        logger.debug(f"MCP Fetch获取: {url}")

        # 注意：实际使用中需要通过Claude Code调用MCP fetch
        # 这里返回模拟数据用于演示
        # 实际实现中应该是：
        # @fetch 获取 {url}

        # 模拟返回的HTML内容
        # 实际项目中应该在Claude Code中调用MCP工具
        mock_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Mock YouTube Page</title></head>
        <body>
            <script>
                // 模拟YouTube数据结构
                var ytInitialData = {{
                    "contents": {{
                        "twoColumnSearchResultsRenderer": {{
                            "primaryContents": {{
                                "sectionListRenderer": {{
                                    "contents": [
                                        {{
                                            "searchResultRenderer": {{
                                                "contents": [
                                                    {{
                                                        "videoRenderer": {{
                                                            "videoId": "mock123",
                                                            "title": {{"runs": [{{"text": "Mock Video for {url}"}}]}},
                                                            "viewCountText": {{"simpleText": "1,000,000次观看"}},
                                                            "lengthText": {{"simpleText": "10:30"}},
                                                            "ownerText": {{"runs": [{{"text": "Mock Channel"}}]}}
                                                        }}
                                                    }}
                                                ]
                                            }}
                                        }}
                                    ]
                                }}
                            }}
                        }}
                    }}
                }};
            </script>
        </body>
        </html>
        """

        logger.warning("当前使用模拟数据，实际使用需要通过Claude Code调用MCP fetch")
        return mock_html

    def _parse_youtube_search_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """
        解析YouTube搜索结果

        Args:
            html_content: HTML内容
            query: 搜索关键词

        Returns:
            视频列表
        """
        videos = []

        # 实际实现中需要解析HTML提取视频信息
        # 这里提供解析逻辑示例

        # 使用正则表达式提取视频信息（实际中应使用更强大的HTML解析器）
        video_patterns = re.findall(
            r'"videoRenderer":\s*{"videoId":\s*"([^"]+)"[^}]*"title":\s*{"runs":\s*\[{"text":\s*"([^"]+)"}]',
            html_content
        )

        for video_id, title in video_patterns:
            video_info = {
                'id': video_id,
                'title': title,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'search_query': query,
                'collected_at': datetime.now().isoformat()
            }
            videos.append(video_info)

        return videos

    def _parse_video_details(self, html_content: str, video_url: str) -> Dict[str, Any]:
        """
        解析视频详情页面

        Args:
            html_content: HTML内容
            video_url: 视频URL

        Returns:
            视频详细信息
        """
        # 提取视频ID
        video_id_match = re.search(r'v=([^&]+)', video_url)
        video_id = video_id_match.group(1) if video_id_match else 'unknown'

        # 实际实现中需要解析HTML提取详细信息
        video_info = {
            'id': video_id,
            'url': video_url,
            'title': '解析的标题',
            'description': '解析的描述',
            'view_count': 0,
            'like_count': 0,
            'duration': 0,
            'published_at': datetime.now().isoformat(),
            'channel': '解析的频道',
            'tags': [],
            'collected_at': datetime.now().isoformat()
        }

        return video_info

    def _parse_trending_videos(self, html_content: str) -> List[Dict[str, Any]]:
        """
        解析热门视频

        Args:
            html_content: HTML内容

        Returns:
            热门视频列表
        """
        # 类似搜索结果解析，但专门处理热门视频
        return []

    def _parse_channel_videos(self, html_content: str, channel_url: str) -> List[Dict[str, Any]]:
        """
        解析频道视频

        Args:
            html_content: HTML内容
            channel_url: 频道URL

        Returns:
            频道视频列表
        """
        # 解析频道页面的视频列表
        return []

    def save_collected_data(self, videos: List[Dict[str, Any]], filename: str):
        """
        保存收集的数据

        Args:
            videos: 视频数据列表
            filename: 文件名
        """
        output_file = self.cache_dir / f"{sanitize_filename(filename)}.json"

        data = {
            'collection_info': {
                'timestamp': datetime.now().isoformat(),
                'video_count': len(videos),
                'source': 'mcp_fetch'
            },
            'videos': videos
        }

        write_json(output_file, data)
        logger.info(f"数据已保存到: {output_file}")


def main():
    """主函数 - 演示MCP数据收集器使用"""
    config = get_config()
    collector = MCPDataCollector(config)

    print("\n" + "=" * 60)
    print("MCP数据收集器 - 演示模式")
    print("=" * 60)
    print("\n注意: 当前运行在演示模式，使用模拟数据")
    print("实际使用需要在Claude Code中调用MCP fetch工具\n")

    try:
        # 演示搜索
        print("🔍 演示: 搜索YouTube视频")
        videos = collector.search_youtube_videos("Python教程", max_results=5)
        print(f"获取到 {len(videos)} 个视频")

        # 演示获取视频详情
        if videos:
            print("\n📹 演示: 获取视频详情")
            first_video = videos[0]
            details = collector.get_video_details(first_video['url'])
            print(f"视频标题: {details['title']}")

        print("\n✅ 演示完成")
        print("\n💡 提示: 实际使用需要在Claude Code中执行:")
        print("  @fetch 获取 https://www.youtube.com/results?search_query=Python教程")

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
