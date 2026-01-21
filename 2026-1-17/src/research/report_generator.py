#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调研报告生成器
基于视频数据和分析结果生成调研报告

引用规约：
- api.spec.md: 2.2 调研命令 (ytp research report)
- data.spec.md: ResearchReport 输出格式
- pipeline.spec.md: Stage 2 输出契约

功能：
- 生成 Markdown 格式调研报告
- 支持 JSON 和 HTML 格式
- 包含统计数据、模式分析、案例详情
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.logger import setup_logger
from src.shared.config import get_config, Config


class ReportGenerator:
    """
    调研报告生成器

    生成符合 data.spec.md 规格的调研报告
    """

    def __init__(self, config: Optional[Config] = None):
        """
        初始化报告生成器

        Args:
            config: 配置对象 (可选)
        """
        self.config = config or get_config()
        self.logger = setup_logger('report_generator')

    def generate_report(
        self,
        keyword: str,
        videos: List[Dict[str, Any]],
        analysis_result: Dict[str, Any],
        output_format: str = 'md'
    ) -> str:
        """
        生成调研报告

        Args:
            keyword: 调研关键词
            videos: 视频数据列表
            analysis_result: 模式分析结果
            output_format: 输出格式 (md/json/html)

        Returns:
            报告内容
        """
        self.logger.info(f"生成调研报告: keyword={keyword}, format={output_format}")

        report_data = self._build_report_data(keyword, videos, analysis_result)

        if output_format == 'json':
            return self._render_json(report_data)
        elif output_format == 'html':
            return self._render_html(report_data)
        else:
            return self._render_markdown(report_data)

    def _build_report_data(
        self,
        keyword: str,
        videos: List[Dict[str, Any]],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建报告数据结构"""
        return {
            'metadata': {
                'keyword': keyword,
                'generated_at': datetime.now().isoformat(),
                'total_videos': len(videos),
                'report_version': '1.0'
            },
            'summary': self._generate_summary(videos, analysis_result),
            'statistics': analysis_result.get('statistics', {}),
            'pattern_analysis': {
                'distribution': analysis_result.get('pattern_distribution', {}),
                'summary': analysis_result.get('patterns_summary', ''),
                'features': analysis_result.get('typical_features', {})
            },
            'selected_cases': self._format_cases(
                analysis_result.get('selected_cases', [])
            ),
            'recommendations': self._generate_recommendations(analysis_result),
            'raw_videos': videos[:20]  # 保留前 20 个原始数据
        }

    def _generate_summary(
        self,
        videos: List[Dict[str, Any]],
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成摘要"""
        stats = analysis_result.get('statistics', {})
        view_stats = stats.get('view_stats', {})
        duration_stats = stats.get('duration_stats', {})

        return {
            'total_videos_analyzed': len(videos),
            'total_views': view_stats.get('total', 0),
            'avg_views': int(view_stats.get('avg', 0)),
            'avg_duration_minutes': round(duration_stats.get('avg', 0) / 60, 1),
            'patterns_found': len(analysis_result.get('pattern_distribution', {})),
            'top_pattern': self._get_top_pattern(analysis_result)
        }

    def _get_top_pattern(self, analysis_result: Dict[str, Any]) -> str:
        """获取最常见模式"""
        distribution = analysis_result.get('pattern_distribution', {})
        if not distribution:
            return '未识别'

        top = max(distribution.items(), key=lambda x: x[1])
        features = analysis_result.get('typical_features', {})
        pattern_info = features.get(top[0], {})

        return pattern_info.get('name', top[0])

    def _format_cases(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化案例数据"""
        formatted = []

        for case in cases:
            formatted.append({
                'title': case.get('title', ''),
                'channel': case.get('channel', ''),
                'youtube_id': case.get('youtube_id') or case.get('id', ''),
                'url': case.get('url', ''),
                'view_count': case.get('view_count', 0),
                'like_count': case.get('like_count', 0),
                'duration': case.get('duration', 0),
                'duration_formatted': self._format_duration(case.get('duration', 0)),
                'pattern': case.get('pattern_name', ''),
                'pattern_key': case.get('primary_pattern', ''),
                'confidence': case.get('pattern_confidence', 0)
            })

        return formatted

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if not seconds:
            return 'N/A'

        minutes = seconds // 60
        secs = seconds % 60

        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def _generate_recommendations(
        self,
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成创作建议"""
        recommendations = []
        features = analysis_result.get('typical_features', {})

        for pattern_key, feature in features.items():
            rec = {
                'pattern': feature.get('name', pattern_key),
                'description': feature.get('description', ''),
                'avg_views': feature.get('avg_views', 0),
                'avg_engagement': round(feature.get('avg_engagement', 0) * 100, 1),
                'suggested_duration': self._format_duration(
                    int(feature.get('duration_analysis', {}).get('avg', 0))
                ),
                'title_tips': self._generate_title_tips(feature),
                'content_tips': self._generate_content_tips(feature),
                'example_titles': feature.get('typical_titles', [])[:3]
            }
            recommendations.append(rec)

        # 按播放量排序
        recommendations.sort(key=lambda x: x['avg_views'], reverse=True)
        return recommendations

    def _generate_title_tips(self, feature: Dict[str, Any]) -> List[str]:
        """生成标题建议"""
        tips = []
        title_analysis = feature.get('title_analysis', {})

        if title_analysis.get('has_numbers_ratio', 0) > 0.3:
            tips.append("标题中使用数字可以提升点击率")

        if title_analysis.get('has_questions_ratio', 0) > 0.2:
            tips.append("使用问句标题吸引好奇心")

        avg_length = title_analysis.get('avg_length', 0)
        if avg_length:
            tips.append(f"建议标题长度约 {int(avg_length)} 字符")

        common_words = title_analysis.get('common_words', {})
        if common_words:
            top_words = list(common_words.keys())[:5]
            tips.append(f"常用关键词: {', '.join(top_words)}")

        return tips

    def _generate_content_tips(self, feature: Dict[str, Any]) -> List[str]:
        """生成内容建议"""
        tips = []
        content_analysis = feature.get('content_analysis', {})

        if content_analysis.get('has_timestamps_ratio', 0) > 0.3:
            tips.append("在描述中添加时间戳可以提升用户体验")

        if content_analysis.get('has_hashtags_ratio', 0) > 0.2:
            tips.append("使用相关话题标签增加曝光")

        avg_length = content_analysis.get('avg_length', 0)
        if avg_length:
            tips.append(f"建议描述长度约 {int(avg_length)} 字符")

        return tips

    def _render_markdown(self, report_data: Dict[str, Any]) -> str:
        """渲染 Markdown 格式报告"""
        metadata = report_data['metadata']
        summary = report_data['summary']
        pattern_analysis = report_data['pattern_analysis']
        cases = report_data['selected_cases']
        recommendations = report_data['recommendations']

        lines = [
            f"# YouTube 调研报告: {metadata['keyword']}",
            "",
            f"> 生成时间: {metadata['generated_at'][:10]}",
            f"> 分析视频数: {metadata['total_videos']}",
            "",
            "---",
            "",
            "## 1. 摘要",
            "",
            f"- **分析视频数**: {summary['total_videos_analyzed']}",
            f"- **总播放量**: {summary['total_views']:,}",
            f"- **平均播放量**: {summary['avg_views']:,}",
            f"- **平均时长**: {summary['avg_duration_minutes']} 分钟",
            f"- **识别模式数**: {summary['patterns_found']}",
            f"- **最常见模式**: {summary['top_pattern']}",
            "",
            "---",
            "",
            "## 2. 模式分析",
            "",
            "### 2.1 模式分布",
            "",
        ]

        # 模式分布
        distribution = pattern_analysis.get('distribution', {})
        for pattern_key, count in sorted(
            distribution.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            feature = pattern_analysis.get('features', {}).get(pattern_key, {})
            name = feature.get('name', pattern_key)
            lines.append(f"- **{name}**: {count} 个案例")

        lines.extend([
            "",
            "### 2.2 各模式特征",
            ""
        ])

        # 模式特征
        for pattern_key, feature in pattern_analysis.get('features', {}).items():
            lines.extend([
                f"#### {feature.get('name', pattern_key)}",
                "",
                f"- 案例数量: {feature.get('case_count', 0)}",
                f"- 平均播放量: {feature.get('avg_views', 0):,}",
                f"- 平均互动率: {feature.get('avg_engagement', 0) * 100:.1f}%",
                ""
            ])

        lines.extend([
            "---",
            "",
            "## 3. 精选案例",
            ""
        ])

        # 精选案例
        for i, case in enumerate(cases[:10], 1):
            lines.extend([
                f"### 案例 {i}: {case['title'][:50]}{'...' if len(case['title']) > 50 else ''}",
                "",
                f"- **频道**: {case['channel']}",
                f"- **播放量**: {case['view_count']:,}",
                f"- **点赞数**: {case['like_count']:,}",
                f"- **时长**: {case['duration_formatted']}",
                f"- **模式**: {case['pattern']}",
                f"- **链接**: {case['url']}",
                ""
            ])

        lines.extend([
            "---",
            "",
            "## 4. 创作建议",
            ""
        ])

        # 创作建议
        for i, rec in enumerate(recommendations[:3], 1):
            lines.extend([
                f"### 建议 {i}: {rec['pattern']}",
                "",
                f"**模式描述**: {rec.get('description', '')}",
                "",
                f"- 平均播放量: {rec['avg_views']:,}",
                f"- 平均互动率: {rec['avg_engagement']}%",
                f"- 建议时长: {rec['suggested_duration']}",
                "",
                "**标题技巧**:",
                ""
            ])

            for tip in rec.get('title_tips', []):
                lines.append(f"- {tip}")

            lines.extend([
                "",
                "**内容技巧**:",
                ""
            ])

            for tip in rec.get('content_tips', []):
                lines.append(f"- {tip}")

            if rec.get('example_titles'):
                lines.extend([
                    "",
                    "**参考标题**:",
                    ""
                ])
                for title in rec['example_titles']:
                    lines.append(f"- {title}")

            lines.append("")

        lines.extend([
            "---",
            "",
            "*报告由 YouTube Pipeline 自动生成*"
        ])

        return '\n'.join(lines)

    def _render_json(self, report_data: Dict[str, Any]) -> str:
        """渲染 JSON 格式报告"""
        return json.dumps(report_data, ensure_ascii=False, indent=2, default=str)

    def _render_html(self, report_data: Dict[str, Any]) -> str:
        """渲染 HTML 格式报告"""
        metadata = report_data['metadata']
        summary = report_data['summary']
        cases = report_data['selected_cases']

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>调研报告: {metadata['keyword']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        h2 {{ color: #202124; margin-top: 30px; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .summary-item {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .summary-value {{ font-size: 24px; font-weight: bold; color: #1a73e8; }}
        .summary-label {{ font-size: 12px; color: #666; }}
        .case {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .case-title {{ font-weight: bold; color: #202124; }}
        .case-meta {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .tag {{ display: inline-block; background: #e8f0fe; color: #1a73e8; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
        footer {{ text-align: center; color: #999; margin-top: 40px; padding: 20px; }}
    </style>
</head>
<body>
    <h1>📊 YouTube 调研报告: {metadata['keyword']}</h1>
    <p style="color: #666;">生成时间: {metadata['generated_at'][:10]}</p>

    <div class="summary">
        <h2>摘要</h2>
        <div class="summary-item">
            <div class="summary-value">{summary['total_videos_analyzed']}</div>
            <div class="summary-label">分析视频数</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">{summary['avg_views']:,}</div>
            <div class="summary-label">平均播放量</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">{summary['avg_duration_minutes']}</div>
            <div class="summary-label">平均时长(分钟)</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">{summary['top_pattern']}</div>
            <div class="summary-label">最常见模式</div>
        </div>
    </div>

    <h2>精选案例</h2>
"""

        for case in cases[:10]:
            html += f"""
    <div class="case">
        <div class="case-title">{case['title']}</div>
        <div class="case-meta">
            频道: {case['channel']} |
            播放: {case['view_count']:,} |
            时长: {case['duration_formatted']}
            <span class="tag">{case['pattern']}</span>
        </div>
    </div>
"""

        html += """
    <footer>
        报告由 YouTube Pipeline 自动生成
    </footer>
</body>
</html>
"""

        return html

    def save_report(
        self,
        report_content: str,
        output_path: Path,
        output_format: str = 'md'
    ) -> None:
        """
        保存报告到文件

        Args:
            report_content: 报告内容
            output_path: 输出路径
            output_format: 输出格式
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 确保扩展名正确
        expected_ext = {'md': '.md', 'json': '.json', 'html': '.html'}
        ext = expected_ext.get(output_format, '.md')

        if output_path.suffix != ext:
            output_path = output_path.with_suffix(ext)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        self.logger.info(f"报告已保存到: {output_path}")

    def generate_and_save(
        self,
        keyword: str,
        videos: List[Dict[str, Any]],
        analysis_result: Dict[str, Any],
        output_dir: Optional[Path] = None,
        output_format: str = 'md'
    ) -> Path:
        """
        生成并保存报告

        Args:
            keyword: 关键词
            videos: 视频数据
            analysis_result: 分析结果
            output_dir: 输出目录
            output_format: 输出格式

        Returns:
            输出文件路径
        """
        # 默认输出目录
        if output_dir is None:
            output_dir = Path('data/reports')

        output_dir = Path(output_dir)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_keyword = keyword.replace(' ', '_').replace('/', '_')[:20]
        filename = f"research_{safe_keyword}_{timestamp}"

        output_path = output_dir / filename

        # 生成报告
        report_content = self.generate_report(
            keyword, videos, analysis_result, output_format
        )

        # 保存报告
        self.save_report(report_content, output_path, output_format)

        # 返回实际保存路径
        ext = {'md': '.md', 'json': '.json', 'html': '.html'}.get(output_format, '.md')
        return output_path.with_suffix(ext)


# 便捷函数
def generate_research_report(
    keyword: str,
    videos: List[Dict[str, Any]],
    analysis_result: Dict[str, Any],
    output_format: str = 'md'
) -> str:
    """便捷生成报告函数"""
    generator = ReportGenerator()
    return generator.generate_report(keyword, videos, analysis_result, output_format)


if __name__ == '__main__':
    # 测试
    print("报告生成器测试")

    generator = ReportGenerator()

    # 模拟数据
    test_videos = [
        {
            'title': '3个方法提升效率',
            'channel': '效率频道',
            'youtube_id': 'abc123xyz00',
            'url': 'https://youtube.com/watch?v=abc123xyz00',
            'view_count': 50000,
            'like_count': 2000,
            'duration': 600
        }
    ]

    test_analysis = {
        'statistics': {
            'view_stats': {'total': 50000, 'avg': 50000},
            'duration_stats': {'avg': 600}
        },
        'pattern_distribution': {'knowledge_sharing': 1},
        'patterns_summary': '- 干货输出型: 1 个案例',
        'typical_features': {
            'knowledge_sharing': {
                'name': '干货输出型',
                'description': '提供实用信息和方法论',
                'case_count': 1,
                'avg_views': 50000,
                'avg_engagement': 0.044,
                'duration_analysis': {'avg': 600},
                'title_analysis': {'avg_length': 10, 'common_words': {'方法': 1}},
                'content_analysis': {'avg_length': 100},
                'typical_titles': ['3个方法提升效率']
            }
        },
        'selected_cases': test_videos
    }

    # 生成报告
    report = generator.generate_report('效率提升', test_videos, test_analysis)
    print("\n生成的 Markdown 报告预览:")
    print(report[:500] + "...")
