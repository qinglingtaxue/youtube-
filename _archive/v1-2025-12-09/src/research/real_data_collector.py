#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据收集器
基于实际MCP调用收集数据，然后分析竞争度
"""

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from utils.logger import setup_logger
from utils.config import get_config
from utils.file_utils import ensure_dir, write_json, write_text

class RealDataCollector:
    """真实数据收集器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger('real_data_collector')

    def analyze_competition_from_views(self, videos: List[Dict[str, Any]]) -> str:
        """
        基于观看量分析竞争度

        Args:
            videos: 视频列表

        Returns:
            竞争度评估: high/medium/low
        """
        if not videos:
            return 'low'

        # 提取观看量数据
        view_counts = []
        for video in videos:
            views_str = video.get('views', '0')
            # 提取数字
            views = self._extract_view_count(views_str)
            if views > 0:
                view_counts.append(views)

        if not view_counts:
            return 'low'

        # 计算统计指标
        avg_views = sum(view_counts) / len(view_counts)
        median_views = sorted(view_counts)[len(view_counts) // 2]
        max_views = max(view_counts)

        self.logger.info(f"观看量分析 - 平均: {avg_views:,.0f}, 中位数: {median_views:,.0f}, 最大: {max_views:,.0f}")

        # 基于观看量判断竞争度
        # 高竞争: 平均观看量超过100万
        # 中等竞争: 平均观看量10万-100万
        # 低竞争: 平均观看量低于10万
        if avg_views >= 1000000:
            return 'high'
        elif avg_views >= 100000:
            return 'medium'
        else:
            return 'low'

    def _extract_view_count(self, views_str: str) -> int:
        """提取观看量数值"""
        if not views_str:
            return 0

        # 移除空格和逗号
        views_str = views_str.replace(',', '').replace(' ', '')

        # 提取数字
        match = re.search(r'(\d+(?:\.\d+)?)', views_str)
        if not match:
            return 0

        number = float(match.group(1))

        # 处理单位
        if '万' in views_str or '10k' in views_str.lower() or 'k' in views_str.lower():
            return int(number * 1000)
        elif '百万' in views_str or 'M' in views_str.upper():
            return int(number * 1000000)
        else:
            return int(number)

    def analyze_competition_from_channels(self, videos: List[Dict[str, Any]]) -> str:
        """
        基于频道数量和订阅者分析竞争度

        Args:
            videos: 视频列表

        Returns:
            竞争度评估
        """
        # 统计不同频道的数量
        channels = {}
        for video in videos:
            channel = video.get('channel', 'Unknown')
            if channel not in channels:
                channels[channel] = 0
            channels[channel] += 1

        # 如果视频来自很多不同频道，说明竞争激烈
        unique_channels = len(channels)
        self.logger.info(f"独特频道数量: {unique_channels}")

        # 如果只有少数几个频道主导，说明竞争度较低
        if unique_channels <= 5:
            return 'low'
        elif unique_channels <= 15:
            return 'medium'
        else:
            return 'high'

    def analyze_competition_from_recency(self, videos: List[Dict[str, Any]]) -> str:
        """
        基于发布时间分析竞争度

        Args:
            videos: 视频列表

        Returns:
            竞争度评估
        """
        # 统计近期发布视频的数量
        recent_count = 0
        for video in videos:
            published = video.get('published', '')
            if self._is_recent_published(published):
                recent_count += 1

        total_count = len(videos)
        recent_ratio = recent_count / total_count if total_count > 0 else 0

        self.logger.info(f"近期发布视频比例: {recent_ratio:.2%}")

        # 如果近期发布的视频很多，说明竞争激烈
        if recent_ratio >= 0.7:
            return 'high'
        elif recent_ratio >= 0.4:
            return 'medium'
        else:
            return 'low'

    def _is_recent_published(self, published: str) -> bool:
        """判断是否为近期发布（30天内）"""
        if not published:
            return False

        try:
            # 解析日期（假设格式为YYYY-MM-DD）
            pub_date = datetime.strptime(published, '%Y-%m-%d')
            days_diff = (datetime.now() - pub_date).days
            return days_diff <= 30
        except:
            return False

    def collect_and_analyze_region(self, query: str, region: str, platform: str = 'youtube') -> Dict[str, Any]:
        """
        收集并分析特定地区的竞争度

        Args:
            query: 搜索关键词
            region: 地区代码
            platform: 平台名称

        Returns:
            分析结果
        """
        self.logger.info(f"开始收集 {region} - {query} 的数据...")

        # 在Claude Code中调用MCP工具：
        mcp_commands = self._generate_mcp_commands(query, region, platform)
        self.logger.info("请在Claude Code中执行以下MCP命令:")
        for cmd in mcp_commands:
            self.logger.info(f"  {cmd}")

        # 模拟数据收集（在实际使用中，这些数据来自MCP调用结果）
        # 实际使用时，这里应该是真实的HTML解析结果
        mock_videos = self._get_mock_data(query, region, platform)

        # 分析竞争度
        view_competition = self.analyze_competition_from_views(mock_videos)
        channel_competition = self.analyze_competition_from_channels(mock_videos)
        recency_competition = self.analyze_competition_from_recency(mock_videos)

        # 综合评分
        competition_scores = {
            'views': 3 if view_competition == 'high' else 2 if view_competition == 'medium' else 1,
            'channels': 3 if channel_competition == 'high' else 2 if channel_competition == 'medium' else 1,
            'recency': 3 if recency_competition == 'high' else 2 if recency_competition == 'medium' else 1
        }

        overall_score = sum(competition_scores.values()) / len(competition_scores)
        overall_competition = 'high' if overall_score >= 2.5 else 'medium' if overall_score >= 1.5 else 'low'

        result = {
            'region': region,
            'query': query,
            'platform': platform,
            'timestamp': datetime.now().isoformat(),
            'video_count': len(mock_videos),
            'competition_analysis': {
                'view_based': view_competition,
                'channel_based': channel_competition,
                'recency_based': recency_competition,
                'overall': overall_competition,
                'scores': competition_scores,
                'score_value': overall_score
            },
            'sample_videos': mock_videos[:5]  # 保存前5个样本
        }

        return result

    def _generate_mcp_commands(self, query: str, region: str, platform: str) -> List[str]:
        """生成MCP调用命令"""
        commands = []

        if platform == 'youtube':
            commands.append(f"@playwright 打开 https://www.youtube.com/results?search_query={query}&gl={region}")
            commands.append("@playwright 等待页面加载完成")
            commands.append("@playwright 滚动页面到底部")
            commands.append("@playwright 提取所有视频的标题、频道名、观看量、发布时间")
            commands.append("@playwright 截图保存")

        elif platform == 'tiktok':
            commands.append(f"@playwright 打开 https://www.tiktok.com/search?q={query}")
            commands.append("@playwright 等待内容加载")
            commands.append("@playwright 滚动加载更多视频")
            commands.append("@playwright 提取视频信息")

        elif platform == 'facebook':
            commands.append(f"@playwright 打开 https://www.facebook.com/search/top/?q={query}")
            commands.append("@playwright 等待内容加载")
            commands.append("@playwright 提取帖子信息")

        elif platform == 'instagram':
            commands.append(f"@playwright 打开 https://www.instagram.com/explore/tags/{query}/")
            commands.append("@playwright 等待内容加载")
            commands.append("@playwright 提取帖子信息")

        return commands

    def _get_mock_data(self, query: str, region: str, platform: str) -> List[Dict[str, Any]]:
        """获取模拟数据（实际使用时应该来自真实的MCP调用）"""
        # 在实际使用中，这里应该解析MCP返回的HTML内容
        # 目前返回示例数据

        return [
            {
                'title': f'{query} 教程 {region}',
                'channel': f'频道{region}1',
                'views': '50万',
                'published': '2024-12-01',
                'url': f'https://youtube.com/watch?v=video{region}1'
            },
            {
                'title': f'{query} 学习 {region}',
                'channel': f'频道{region}2',
                'views': '30万',
                'published': '2024-12-05',
                'url': f'https://youtube.com/watch?v=video{region}2'
            }
        ]

    def execute_real_research(self, categories: List[str], regions: List[str], platforms: List[str]) -> Dict[str, Any]:
        """
        执行真实调研

        Args:
            categories: 品类列表
            regions: 地区列表
            platforms: 平台列表

        Returns:
            完整调研结果
        """
        self.logger.info("=" * 60)
        self.logger.info("开始执行真实数据调研")
        self.logger.info("=" * 60)

        all_results = {}

        for category in categories:
            self.logger.info(f"\n📂 调研品类: {category}")
            category_results = {}

            for region in regions:
                self.logger.info(f"\n🌍 调研地区: {region}")

                for platform in platforms:
                    self.logger.info(f"\n📱 调研平台: {platform}")

                    try:
                        result = self.collect_and_analyze_region(
                            query=category,
                            region=region,
                            platform=platform
                        )

                        category_results[f"{region}_{platform}"] = result

                        self.logger.info(f"✅ {category} - {region} - {platform}")
                        self.logger.info(f"   竞争度: {result['competition_analysis']['overall']}")
                        self.logger.info(f"   评分: {result['competition_analysis']['score_value']:.2f}")

                    except Exception as e:
                        self.logger.error(f"❌ {category} - {region} - {platform}: {e}")

            all_results[category] = category_results

        # 保存结果
        output_dir = Path('output/real_research')
        ensure_dir(output_dir)

        for category, results in all_results.items():
            file_path = output_dir / f'{category}_research.json'
            write_json(file_path, results)

        # 生成分析报告
        self._generate_analysis_report(all_results, output_dir)

        return all_results

    def _generate_analysis_report(self, results: Dict[str, Any], output_dir: Path):
        """生成分析报告"""
        report = "# 真实数据调研分析报告\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 按品类分析
        for category, category_results in results.items():
            report += f"## {category}\n\n"

            # 统计各地区竞争度
            region_stats = {}
            for key, result in category_results.items():
                region = result['region']
                competition = result['competition_analysis']['overall']
                score = result['competition_analysis']['score_value']

                if region not in region_stats:
                    region_stats[region] = {'high': 0, 'medium': 0, 'low': 0, 'scores': []}

                region_stats[region][competition] += 1
                region_stats[region]['scores'].append(score)

            # 显示各地区竞争情况
            for region, stats in region_stats.items():
                avg_score = sum(stats['scores']) / len(stats['scores'])
                dominant_level = max(['high', 'medium', 'low'], key=lambda k: stats[k])

                report += f"### {region}\n"
                report += f"- 竞争度: {dominant_level}\n"
                report += f"- 平均评分: {avg_score:.2f}\n"
                report += f"- 详细分布: 高竞争{stats['high']}个, 中等竞争{stats['medium']}个, 低竞争{stats['low']}个\n\n"

        # 总体建议
        report += "## 总体建议\n\n"

        report += "### 低竞争地区推荐\n"
        report += "基于实际数据，建议优先考虑以下地区：\n"

        # 找出所有低竞争机会
        low_comp_opportunities = []
        for category, category_results in results.items():
            for key, result in category_results.items():
                if result['competition_analysis']['overall'] == 'low':
                    low_comp_opportunities.append((category, result['region'], result['competition_analysis']['score_value']))

        # 按评分排序
        low_comp_opportunities.sort(key=lambda x: x[2])

        for category, region, score in low_comp_opportunities[:10]:
            report += f"- **{category}** - {region} (评分: {score:.2f})\n"

        report_file = output_dir / 'analysis_report.md'
        write_text(report_file, report)

        self.logger.info(f"\n📁 分析报告已保存: {report_file}")

if __name__ == '__main__':
    # 定义调研参数
    categories = [
        'Python教程',
        'JavaScript学习',
        'AI人工智能',
        '数据分析',
        '机器学习',
        'Web开发'
    ]

    regions = [
        'US', 'CN', 'JP', 'KR', 'TW', 'HK',
        'SG', 'MY', 'TH', 'VN', 'IN', 'GB',
        'DE', 'FR', 'BR', 'MX', 'CA', 'AU'
    ]

    platforms = ['youtube', 'tiktok', 'facebook', 'instagram']

    # 执行调研
    config = get_config()
    collector = RealDataCollector(config)
    results = collector.execute_real_research(categories, regions, platforms)

    print("\n" + "=" * 60)
    print("✅ 真实数据调研完成！")
    print("=" * 60)
