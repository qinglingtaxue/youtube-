#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP集成示例
展示如何与现有MCP服务器集成（tavily搜索、github等）
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import setup_logger
from utils.config import get_config
from utils.file_utils import ensure_dir, write_json

def mcp_tavily_search_demo():
    """
    使用MCP tavily搜索引擎进行补充搜索
    注意：此示例展示了如何与MCP集成，实际使用需要在Claude Code中调用
    """
    logger = setup_logger('mcp_tavily')
    logger.info("=" * 60)
    logger.info("MCP集成示例 - Tavily搜索引擎")
    logger.info("=" * 60)

    # 在Claude Code中，可以使用@tool调用tavily搜索：
    # @tavily 搜索 "YouTube视频优化技巧 2024"
    # @tavily 搜索 "短视频创作方法论"
    # @tavily 搜索 "内容营销趋势分析"

    logger.info("\n📝 在Claude Code中调用Tavily MCP的方法:")
    logger.info("  @tavily 搜索 'YouTube视频优化技巧 2024'")
    logger.info("  @tavily 搜索 '短视频创作方法论'")
    logger.info("  @tavily 搜索 '内容营销趋势分析'")

    logger.info("\n✅ Tavily MCP服务器已启用（通过CC-Switch管理）")
    logger.info("   位置: /Users/su/.cc-switch/cc-switch.db")
    logger.info("   状态: enabled_claude = 1")

    # 模拟搜索结果结构
    mock_search_results = {
        'query': 'YouTube视频优化技巧',
        'results': [
            {
                'title': 'YouTube视频SEO优化完整指南',
                'url': 'https://example.com/youtube-seo',
                'content': '详细介绍YouTube视频SEO优化方法...',
                'score': 0.95
            },
            {
                'title': '如何提高YouTube视频观看量',
                'url': 'https://example.com/youtube-views',
                'content': '分享提升YouTube视频观看量的实用技巧...',
                'score': 0.88
            }
        ],
        'related_queries': [
            'YouTube算法机制',
            '视频缩略图优化',
            '标题关键词布局'
        ]
    }

    # 保存模拟结果
    output_dir = Path('output/mcp_integration')
    ensure_dir(output_dir)
    write_json(output_dir / 'tavily_search_demo.json', mock_search_results)
    logger.info(f"\n📁 示例搜索结果已保存: {output_dir / 'tavily_search_demo.json'}")

def mcp_playwright_demo():
    """
    使用MCP Playwright进行浏览器自动化和数据收集
    """
    logger = setup_logger('mcp_playwright')
    logger.info("\n" + "=" * 60)
    logger.info("MCP集成示例 - Playwright浏览器自动化")
    logger.info("=" * 60)

    logger.info("\n📝 在Claude Code中调用Playwright MCP的方法:")
    logger.info("  @playwright 打开 https://www.youtube.com/results?search_query=Python教程")
    logger.info("  @playwright 滚动页面到底部")
    logger.info("  @playwright 点击第3个视频")
    logger.info("  @playwright 截图保存")

    logger.info("\n✅ Playwright MCP服务器已启用（通过CC-Switch管理）")
    logger.info("   用途: 浏览器自动化、动态内容处理、JavaScript渲染")
    logger.info("   优势: 处理YouTube等动态网站，等待内容加载")

    # 模拟Playwright操作结果
    mock_playwright_results = {
        'actions': [
            {
                'action': 'navigate',
                'url': 'https://www.youtube.com/results?search_query=Python教程',
                'status': 'success',
                'timestamp': '2025-12-09T10:00:00Z'
            },
            {
                'action': 'wait_for_selector',
                'selector': 'ytd-video-renderer',
                'status': 'success',
                'count': 20,
                'timestamp': '2025-12-09T10:00:05Z'
            },
            {
                'action': 'scroll',
                'direction': 'down',
                'pixels': 1000,
                'status': 'success',
                'timestamp': '2025-12-09T10:00:10Z'
            },
            {
                'action': 'click',
                'selector': 'ytd-video-renderer:nth-child(3) #video-title',
                'status': 'success',
                'url': 'https://www.youtube.com/watch?v=example123',
                'timestamp': '2025-12-09T10:00:15Z'
            }
        ],
        'extracted_data': {
            'videos': [
                {
                    'title': 'Python入门教程：变量和数据类型',
                    'url': 'https://www.youtube.com/watch?v=video1',
                    'view_count': '100万次观看',
                    'duration': '10:30'
                },
                {
                    'title': 'JavaScript基础教程：从零开始学习JS',
                    'url': 'https://www.youtube.com/watch?v=video2',
                    'view_count': '80万次观看',
                    'duration': '15:45'
                }
            ]
        }
    }

    # 保存模拟结果
    output_dir = Path('output/mcp_integration')
    write_json(output_dir / 'playwright_demo.json', mock_playwright_results)
    logger.info(f"\n📁 示例Playwright结果已保存: {output_dir / 'playwright_demo.json'}")

    logger.info("\n🎯 Playwright MCP适用场景:")
    logger.info("  1. YouTube搜索结果页面（动态加载）")
    logger.info("  2. 视频详情页面（评论、推荐等）")
    logger.info("  3. 频道页面（视频列表）")
    logger.info("  4. 直播页面（实时数据）")


def mcp_github_integration_demo():
    """
    使用MCP github集成进行代码搜索和分析
    """
    logger = setup_logger('mcp_github')
    logger.info("\n" + "=" * 60)
    logger.info("MCP集成示例 - GitHub代码搜索")
    logger.info("=" * 60)

    logger.info("\n📝 在Claude Code中调用GitHub MCP的方法:")
    logger.info("  @github 搜索仓库 'Python自动化脚本'")
    logger.info("  @github 搜索代码 'web scraping python'")
    logger.info("  @github 获取仓库 'https://github.com/example/automation'")

    logger.info("\n✅ GitHub MCP服务器已配置（针对Codex客户端）")
    logger.info("   状态: enabled_codex = 1")
    logger.info("   用途: 代码搜索、仓库分析、Issue查询")

    # 模拟GitHub搜索结果
    mock_github_results = {
        'repositories': [
            {
                'name': 'youtube-dl',
                'full_name': 'ytdl-org/youtube-dl',
                'description': 'Download videos from YouTube and many other sites',
                'stars': 123456,
                'language': 'Python',
                'url': 'https://github.com/ytdl-org/youtube-dl'
            },
            {
                'name': 'pytube',
                'full_name': 'pytube/pytube',
                'description': 'Python library for downloading YouTube videos',
                'stars': 8765,
                'language': 'Python',
                'url': 'https://github.com/pytube/pytube'
            }
        ],
        'code_search': [
            {
                'repository': 'youtube-scraper',
                'file': 'scraper.py',
                'content': 'def extract_video_info(): ...',
                'url': 'https://github.com/example/youtube-scraper'
            }
        ]
    }

    # 保存模拟结果
    output_dir = Path('output/mcp_integration')
    write_json(output_dir / 'github_search_demo.json', mock_github_results)
    logger.info(f"\n📁 示例GitHub结果已保存: {output_dir / 'github_search_demo.json'}")

def mcp_sequential_thinking_demo():
    """
    使用MCP sequential-thinking进行复杂问题分析
    """
    logger = setup_logger('mcp_thinking')
    logger.info("\n" + "=" * 60)
    logger.info("MCP集成示例 - 顺序思维分析")
    logger.info("=" * 60)

    logger.info("\n📝 在Claude Code中调用sequential-thinking MCP的方法:")
    logger.info("  @sequential-thinking 分析 'YouTube视频成功因素'")
    logger.info("  @sequential-thinking 分析 '短视频平台算法机制'")
    logger.info("  @sequential-thinking 分析 '内容创作与变现模式'")

    logger.info("\n✅ sequential-thinking MCP服务器已启用（针对Claude）")
    logger.info("   用途: 复杂问题的逐步分析和推理")

    # 模拟思维链分析结果
    mock_analysis = {
        'problem': 'YouTube视频成功因素分析',
        'thoughts': [
            {
                'step': 1,
                'thought': '分析YouTube视频成功的核心要素',
                'insights': ['内容质量', '标题优化', '缩略图设计', '发布时间']
            },
            {
                'step': 2,
                'thought': '深入分析每个要素的影响权重',
                'insights': ['内容质量（40%）', '标题优化（25%）', '缩略图（20%）', '其他因素（15%）']
            },
            {
                'step': 3,
                'thought': '提出可操作的优化建议',
                'insights': ['建立内容创作SOP', 'A/B测试标题和缩略图', '数据分析驱动优化']
            }
        ],
        'conclusion': '通过系统性优化关键要素，显著提升视频表现'
    }

    # 保存模拟结果
    output_dir = Path('output/mcp_integration')
    write_json(output_dir / 'sequential_thinking_demo.json', mock_analysis)
    logger.info(f"\n📁 示例思维分析已保存: {output_dir / 'sequential_thinking_demo.json'}")

def mcp_file_system_demo():
    """
    使用MCP filesystem进行文件操作集成
    """
    logger = setup_logger('mcp_filesystem')
    logger.info("\n" + "=" * 60)
    logger.info("MCP集成示例 - 文件系统操作")
    logger.info("=" * 60)

    logger.info("\n📝 在Claude Code中调用File System MCP的方法:")
    logger.info("  读取文件: '查看这个文件的内容'")
    logger.info("  搜索文件: '搜索所有 .md 文件'")
    logger.info("  列出目录: '列出当前目录结构'")
    logger.info("  创建文件: '创建新文件并写入内容'")

    logger.info("\n✅ File System MCP服务器已启用（针对Claude）")
    logger.info("   用途: 文件读写、目录管理、文件搜索")

    # 展示与工作流的集成
    integration_guide = {
        'mcp_servers': {
            'tavily': {
                'purpose': '实时搜索补充信息',
                'usage': '@tavily 搜索 "关键词"',
                'enabled_claude': True
            },
            'github': {
                'purpose': '代码和仓库搜索',
                'usage': '@github 搜索仓库 "关键词"',
                'enabled_codex': True
            },
            'sequential-thinking': {
                'purpose': '复杂问题分析',
                'usage': '@sequential-thinking 分析 "问题"',
                'enabled_claude': True
            },
            'file-system': {
                'purpose': '文件系统操作',
                'usage': '文件读写、搜索、管理',
                'enabled_claude': True
            },
            'mcp-server-fetch': {
                'purpose': '网页内容获取',
                'usage': '@fetch 获取 "URL"',
                'enabled_claude': True
            }
        },
        'workflow_integration': {
            'data_collection': '使用tavily搜索补充YouTube数据',
            'analysis': '使用sequential-thinking分析复杂模式',
            'code_search': '使用github查找相关代码和工具',
            'content_fetching': '使用mcp-server-fetch获取网页内容',
            'file_management': '使用file-system管理分析结果'
        }
    }

    # 保存集成指南
    output_dir = Path('output/mcp_integration')
    write_json(output_dir / 'mcp_integration_guide.json', integration_guide)
    logger.info(f"\n📁 MCP集成指南已保存: {output_dir / 'mcp_integration_guide.json'}")

def main():
    """
    主函数：展示所有MCP集成示例
    """
    print("\n" + "=" * 60)
    print("YouTube视频研究工作流 - MCP集成示例")
    print("=" * 60)
    print("\n本示例将展示如何与CC-Switch管理的MCP服务器集成:")
    print("1. Playwright - 浏览器自动化和动态内容处理")
    print("2. Tavily搜索引擎 - 实时信息搜索")
    print("3. GitHub集成 - 代码和仓库搜索")
    print("4. sequential-thinking - 复杂问题分析")
    print("5. File System - 文件操作")
    print("\n⚠️  注意: 实际使用需要在Claude Code中调用@tool")
    print("\n开始执行...\n")

    try:
        mcp_playwright_demo()
        mcp_tavily_search_demo()
        mcp_github_integration_demo()
        mcp_sequential_thinking_demo()
        mcp_file_system_demo()

        print("\n" + "=" * 60)
        print("✅ MCP集成示例执行完成！")
        print("=" * 60)
        print("\n📁 示例文件保存在: output/mcp_integration/")
        print("\n💡 提示:")
        print("  - 在Claude Code中直接使用 @tavily、@github 等调用MCP")
        print("  - 通过CC-Switch管理所有MCP服务器配置")
        print("  - MCP服务器状态: sqlite3 /Users/su/.cc-switch/cc-switch.db")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
    except Exception as e:
        print(f"\n\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
