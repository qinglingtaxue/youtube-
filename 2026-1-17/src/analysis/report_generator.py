#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化报告生成器

生成交互式 HTML 报告，使用 Chart.js 进行数据可视化
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .video_analyzer import AnalysisResult, VideoAnalyzer


class ReportGenerator:
    """可视化报告生成器"""

    def __init__(self):
        self.template = self._get_html_template()

    def generate(self, result: AnalysisResult, output_path: str = None) -> str:
        """
        生成 HTML 可视化报告

        Args:
            result: 分析结果
            output_path: 输出路径，默认 data/analysis/report_*.html

        Returns:
            生成的报告路径
        """
        if output_path is None:
            output_dir = Path("data/analysis")
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"report_{timestamp}.html"
        else:
            output_path = Path(output_path)

        # 准备数据
        data = self._prepare_chart_data(result)

        # 渲染 HTML
        html = self.template.replace('{{DATA}}', json.dumps(data, ensure_ascii=False))
        html = html.replace('{{GENERATED_AT}}', result.generated_at)
        html = html.replace('{{VIDEO_COUNT}}', str(result.video_count))
        html = html.replace('{{INSIGHTS}}', self._format_insights(result.insights))

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(output_path)

    def _prepare_chart_data(self, result: AnalysisResult) -> Dict[str, Any]:
        """准备图表数据"""
        data = {}

        # 基础统计卡片数据
        stats = result.basic_stats
        data['cards'] = {
            'total_videos': stats.get('total_videos', 0),
            'total_views': stats.get('view_count', {}).get('total', 0),
            'avg_views': stats.get('view_count', {}).get('mean', 0),
            'median_views': stats.get('view_count', {}).get('median', 0),
            'total_channels': result.channel_analysis.get('total_channels', 0),
            'with_details': stats.get('with_details', 0),
        }

        # 关键词分布（饼图）
        keywords = stats.get('keywords', {})
        data['keywords'] = {
            'labels': list(keywords.keys()),
            'values': list(keywords.values()),
        }

        # 时长分布（条形图）
        duration = result.duration_analysis
        if duration.get('buckets'):
            data['duration'] = {
                'labels': [b['label'] for b in duration['buckets']],
                'counts': [b['count'] for b in duration['buckets']],
                'avg_views': [b['avg_views'] for b in duration['buckets']],
            }

        # 标题模式（雷达图）
        title = result.title_analysis
        if title.get('patterns', {}).get('counts'):
            patterns = title['patterns']['counts']
            data['title_patterns'] = {
                'labels': list(patterns.keys()),
                'values': list(patterns.values()),
            }

        # 标题高频词（词云数据）
        if title.get('top_words'):
            data['top_words'] = title['top_words']

        # 内容聚类（饼图）
        clusters = result.clusters
        if clusters.get('clusters'):
            data['clusters'] = {
                'labels': [c['topic'] for c in clusters['clusters']],
                'counts': [c['count'] for c in clusters['clusters']],
                'avg_views': [c['avg_views'] for c in clusters['clusters']],
            }

        # 频道排名（条形图）
        channels = result.channel_analysis
        if channels.get('top_by_views'):
            top_channels = channels['top_by_views'][:10]
            data['channels'] = {
                'labels': [c['channel'][:15] for c in top_channels],
                'total_views': [c['total_views'] for c in top_channels],
                'video_count': [c['video_count'] for c in top_channels],
            }

        # 趋势分析（折线图）
        trends = result.trends
        if trends.get('monthly_stats'):
            data['trends'] = {
                'labels': [m['month'] for m in trends['monthly_stats']],
                'counts': [m['count'] for m in trends['monthly_stats']],
                'avg_views': [m['avg_views'] for m in trends['monthly_stats']],
            }

        # 异常值/爆款视频（表格）
        anomalies = result.anomalies
        if anomalies.get('viral_videos', {}).get('videos'):
            data['viral_videos'] = anomalies['viral_videos']['videos']

        # 播放量分布（直方图数据）
        percentiles = stats.get('view_count', {}).get('percentiles', {})
        data['view_distribution'] = {
            'percentiles': percentiles,
            'mean': stats.get('view_count', {}).get('mean', 0),
            'median': stats.get('view_count', {}).get('median', 0),
        }

        # 内容模式
        if result.content_patterns:
            data['content_patterns'] = {
                'labels': list(result.content_patterns.keys()),
                'counts': [p['count'] for p in result.content_patterns.values()],
                'avg_views': [p['avg_views'] for p in result.content_patterns.values()],
            }

        return data

    def _format_insights(self, insights: list) -> str:
        """格式化洞察列表为 HTML"""
        html_items = []
        for insight in insights:
            if insight == '---':
                html_items.append('<hr class="my-3">')
            elif insight.startswith('【'):
                html_items.append(f'<h5 class="text-primary mt-3">{insight}</h5>')
            else:
                html_items.append(f'<li>{insight}</li>')
        return '\n'.join(html_items)

    def _get_html_template(self) -> str:
        """HTML 模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube 视频分析报告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background: #f5f5f5; }
        .card { margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card { text-align: center; padding: 20px; }
        .stat-card h3 { font-size: 2rem; color: #2196F3; margin: 0; }
        .stat-card p { color: #666; margin: 5px 0 0 0; }
        .chart-container { position: relative; height: 300px; }
        .insight-list { list-style-type: none; padding-left: 0; }
        .insight-list li { padding: 8px 0; border-bottom: 1px solid #eee; }
        .insight-list li:before { content: "💡 "; }
        .viral-table { font-size: 0.9rem; }
        .word-cloud { display: flex; flex-wrap: wrap; gap: 8px; padding: 15px; }
        .word-cloud span {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 5px 12px; border-radius: 20px;
        }
        .header-banner {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header-banner">
        <div class="container">
            <h1>📊 YouTube 视频分析报告</h1>
            <p class="mb-0">生成时间: {{GENERATED_AT}} | 分析视频数: {{VIDEO_COUNT}}</p>
        </div>
    </div>

    <div class="container">
        <!-- 核心指标卡片 -->
        <div class="row" id="stat-cards">
            <div class="col-md-2">
                <div class="card stat-card">
                    <h3 id="card-videos">-</h3>
                    <p>总视频数</p>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card">
                    <h3 id="card-views">-</h3>
                    <p>总播放量</p>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card">
                    <h3 id="card-avg">-</h3>
                    <p>平均播放</p>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card">
                    <h3 id="card-median">-</h3>
                    <p>中位数</p>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card">
                    <h3 id="card-channels">-</h3>
                    <p>频道数</p>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card stat-card">
                    <h3 id="card-details">-</h3>
                    <p>有详情</p>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- 关键词分布 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">🔑 关键词分布</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="keywordChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 内容聚类 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">📂 内容主题分布</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="clusterChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- 时长分析 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">⏱️ 视频时长分析</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="durationChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 标题模式 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">📝 标题模式分析</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="patternChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- 频道排名 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">🏆 头部频道排名</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="channelChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 趋势分析 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">📈 月度趋势</div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="trendChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- 高频词 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">💬 标题高频词</div>
                    <div class="card-body word-cloud" id="wordCloud">
                    </div>
                </div>
            </div>

            <!-- 洞察与建议 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">💡 分析洞察与建议</div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        <ul class="insight-list">
                            {{INSIGHTS}}
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- 爆款视频 -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">🔥 潜在爆款视频（异常高播放量）</div>
                    <div class="card-body">
                        <table class="table table-striped viral-table" id="viralTable">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>标题</th>
                                    <th>播放量</th>
                                    <th>频道</th>
                                    <th>Z分数</th>
                                    <th>链接</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 数据
        const DATA = {{DATA}};

        // 格式化数字
        function formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toString();
        }

        // 颜色
        const COLORS = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#7CFC00', '#00CED1', '#FF69B4', '#8A2BE2'
        ];

        // 更新统计卡片
        function updateCards() {
            const cards = DATA.cards;
            document.getElementById('card-videos').textContent = formatNumber(cards.total_videos);
            document.getElementById('card-views').textContent = formatNumber(cards.total_views);
            document.getElementById('card-avg').textContent = formatNumber(cards.avg_views);
            document.getElementById('card-median').textContent = formatNumber(cards.median_views);
            document.getElementById('card-channels').textContent = formatNumber(cards.total_channels);
            document.getElementById('card-details').textContent = formatNumber(cards.with_details);
        }

        // 关键词饼图
        function renderKeywordChart() {
            if (!DATA.keywords) return;
            new Chart(document.getElementById('keywordChart'), {
                type: 'doughnut',
                data: {
                    labels: DATA.keywords.labels,
                    datasets: [{
                        data: DATA.keywords.values,
                        backgroundColor: COLORS,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right' }
                    }
                }
            });
        }

        // 内容聚类饼图
        function renderClusterChart() {
            if (!DATA.clusters) return;
            new Chart(document.getElementById('clusterChart'), {
                type: 'doughnut',
                data: {
                    labels: DATA.clusters.labels,
                    datasets: [{
                        data: DATA.clusters.counts,
                        backgroundColor: COLORS,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right' }
                    }
                }
            });
        }

        // 时长条形图
        function renderDurationChart() {
            if (!DATA.duration) return;
            new Chart(document.getElementById('durationChart'), {
                type: 'bar',
                data: {
                    labels: DATA.duration.labels,
                    datasets: [{
                        label: '视频数量',
                        data: DATA.duration.counts,
                        backgroundColor: '#36A2EB',
                        yAxisID: 'y',
                    }, {
                        label: '平均播放量',
                        data: DATA.duration.avg_views,
                        backgroundColor: '#FF6384',
                        yAxisID: 'y1',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { position: 'left', title: { display: true, text: '视频数量' }},
                        y1: { position: 'right', title: { display: true, text: '平均播放量' }, grid: { drawOnChartArea: false }}
                    }
                }
            });
        }

        // 标题模式雷达图
        function renderPatternChart() {
            if (!DATA.title_patterns) return;
            new Chart(document.getElementById('patternChart'), {
                type: 'radar',
                data: {
                    labels: DATA.title_patterns.labels,
                    datasets: [{
                        label: '使用次数',
                        data: DATA.title_patterns.values,
                        fill: true,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgb(54, 162, 235)',
                        pointBackgroundColor: 'rgb(54, 162, 235)',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        }

        // 频道条形图
        function renderChannelChart() {
            if (!DATA.channels) return;
            new Chart(document.getElementById('channelChart'), {
                type: 'bar',
                data: {
                    labels: DATA.channels.labels,
                    datasets: [{
                        label: '总播放量',
                        data: DATA.channels.total_views,
                        backgroundColor: '#4BC0C0',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        // 趋势折线图
        function renderTrendChart() {
            if (!DATA.trends) return;
            new Chart(document.getElementById('trendChart'), {
                type: 'line',
                data: {
                    labels: DATA.trends.labels,
                    datasets: [{
                        label: '视频数量',
                        data: DATA.trends.counts,
                        borderColor: '#36A2EB',
                        yAxisID: 'y',
                    }, {
                        label: '平均播放量',
                        data: DATA.trends.avg_views,
                        borderColor: '#FF6384',
                        yAxisID: 'y1',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { position: 'left' },
                        y1: { position: 'right', grid: { drawOnChartArea: false }}
                    }
                }
            });
        }

        // 词云
        function renderWordCloud() {
            if (!DATA.top_words) return;
            const container = document.getElementById('wordCloud');
            const words = Object.entries(DATA.top_words).slice(0, 20);
            const maxCount = Math.max(...words.map(w => w[1]));

            words.forEach(([word, count]) => {
                const span = document.createElement('span');
                span.textContent = word;
                const size = 0.8 + (count / maxCount) * 0.6;
                span.style.fontSize = size + 'rem';
                container.appendChild(span);
            });
        }

        // 爆款视频表格
        function renderViralTable() {
            if (!DATA.viral_videos) return;
            const tbody = document.querySelector('#viralTable tbody');
            DATA.viral_videos.forEach((video, i) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td>${video.title.substring(0, 40)}...</td>
                    <td>${video.views}</td>
                    <td>${video.channel || '-'}</td>
                    <td>${video.z_score}</td>
                    <td><a href="${video.url}" target="_blank">查看</a></td>
                `;
                tbody.appendChild(tr);
            });
        }

        // 初始化
        document.addEventListener('DOMContentLoaded', () => {
            updateCards();
            renderKeywordChart();
            renderClusterChart();
            renderDurationChart();
            renderPatternChart();
            renderChannelChart();
            renderTrendChart();
            renderWordCloud();
            renderViralTable();
        });
    </script>
</body>
</html>'''


def generate_visual_report(db_path: str = None, output_path: str = None) -> str:
    """
    生成可视化分析报告

    Args:
        db_path: 数据库路径
        output_path: 输出路径

    Returns:
        报告文件路径
    """
    # 执行分析
    analyzer = VideoAnalyzer(db_path)
    result = analyzer.analyze()

    # 生成报告
    generator = ReportGenerator()
    report_path = generator.generate(result, output_path)

    return report_path
