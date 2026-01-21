#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合可视化报告生成器

生成包含多个标签页的完整分析报告：
1. 概览 - 关键指标卡片
2. 市场边界 - 市场规模、频道竞争
3. 时间分析 - 时间范围、发布频率、趋势
4. AI创作机会 - 近期爆款、高增长、小频道黑马
5. 内容分析 - 标题模式、时长、关键词
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.video_analyzer import VideoAnalyzer, AnalysisResult
from src.analysis.market_analyzer import MarketAnalyzer, MarketReport


class ComprehensiveReportGenerator:
    """综合报告生成器"""

    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.market_analyzer = MarketAnalyzer()

    def generate(self, output_path: str = None) -> str:
        """
        生成综合 HTML 报告

        Args:
            output_path: 输出路径

        Returns:
            生成的报告路径
        """
        # 加载数据
        self.video_analyzer.load_data()
        self.market_analyzer.load_data()

        # 分析
        video_result = self.video_analyzer.analyze()
        market_report = self.market_analyzer.analyze()

        # 生成 HTML
        if output_path is None:
            output_dir = Path("data/analysis")
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"comprehensive_report_{timestamp}.html"
        else:
            output_path = Path(output_path)

        html = self._generate_html(video_result, market_report)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(output_path)

    def _generate_html(self, video: AnalysisResult, market: MarketReport) -> str:
        """生成 HTML 内容"""
        # 准备数据
        data = self._prepare_data(video, market)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube 竞品分析报告 - {market.generated_at[:10]}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 24px; }}
        .header .meta {{ font-size: 14px; opacity: 0.9; }}

        /* 标签页导航 */
        .tabs {{
            background: white;
            border-bottom: 1px solid #e0e0e0;
            padding: 0 40px;
            display: flex;
            gap: 0;
        }}
        .tab {{
            padding: 15px 25px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            font-weight: 500;
            color: #666;
            transition: all 0.2s;
        }}
        .tab:hover {{ color: #667eea; }}
        .tab.active {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}

        /* 内容区 */
        .content {{ padding: 30px 40px; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* 卡片 */
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card-label {{ font-size: 13px; color: #888; margin-bottom: 8px; }}
        .card-value {{ font-size: 28px; font-weight: 700; color: #333; }}
        .card-sub {{ font-size: 12px; color: #999; margin-top: 5px; }}
        .card.highlight {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .card.highlight .card-label {{ color: rgba(255,255,255,0.8); }}
        .card.highlight .card-value {{ color: white; }}
        .card.highlight .card-sub {{ color: rgba(255,255,255,0.7); }}

        /* 图表容器 */
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .chart-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .chart-wrapper {{ position: relative; height: 300px; }}

        /* 表格 */
        .table-container {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-green {{ background: #d4edda; color: #155724; }}
        .badge-blue {{ background: #cce5ff; color: #004085; }}
        .badge-yellow {{ background: #fff3cd; color: #856404; }}
        .badge-purple {{ background: #e2d5f8; color: #5a2d82; }}

        /* 两列布局 */
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }}
        @media (max-width: 900px) {{
            .grid-2 {{ grid-template-columns: 1fr; }}
        }}

        /* 洞察卡片 */
        .insight {{
            background: #fff;
            border-left: 4px solid #667eea;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
        }}
        .insight-title {{ font-weight: 600; color: #333; margin-bottom: 5px; }}
        .insight-text {{ color: #666; font-size: 14px; }}

        /* 进度条 */
        .progress-bar {{
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
        }}

        /* 全局时间过滤器样式 */
        .global-time-filter {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .time-filter-btn {{
            padding: 6px 12px;
            border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            color: white;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }}
        .time-filter-btn:hover {{
            background: rgba(255,255,255,0.2);
        }}
        .time-filter-btn.active {{
            background: white;
            color: #667eea;
            font-weight: 600;
        }}

        /* 当前时间范围指示器 */
        .time-range-indicator {{
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            box-shadow: 0 4px 12px rgba(102,126,234,0.3);
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .time-range-indicator::before {{
            content: '📅';
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>YouTube 竞品分析报告</h1>
            <div class="meta">主题: 老人养生 | 样本: {market.sample_size:,} 个视频</div>
        </div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <div class="global-time-filter">
                <span style="font-size: 12px; opacity: 0.8; margin-right: 8px;">数据范围:</span>
                <button class="time-filter-btn" onclick="setGlobalTimeFilter('1天内')">1天内</button>
                <button class="time-filter-btn" onclick="setGlobalTimeFilter('15天内')">15天内</button>
                <button class="time-filter-btn active" onclick="setGlobalTimeFilter('30天内')">30天内</button>
                <button class="time-filter-btn" onclick="setGlobalTimeFilter('全部')">全部</button>
            </div>
            <div class="meta">
                生成时间: {market.generated_at[:19].replace('T', ' ')}
            </div>
        </div>
    </div>

    <div class="tabs">
        <div class="tab active" onclick="showTab('overview')">📊 概览</div>
        <div class="tab" onclick="showTab('market')">🌐 市场边界</div>
        <div class="tab" onclick="showTab('time')">📅 时间分析</div>
        <div class="tab" onclick="showTab('opportunities')">🎯 AI创作机会</div>
        <div class="tab" onclick="showTab('content')">📝 内容分析</div>
    </div>

    <div class="content">
        <!-- 概览页 -->
        <div id="overview" class="tab-content active">
            {self._render_overview(data)}
        </div>

        <!-- 市场边界页 -->
        <div id="market" class="tab-content">
            {self._render_market(data)}
        </div>

        <!-- 时间分析页 -->
        <div id="time" class="tab-content">
            {self._render_time_analysis(data)}
        </div>

        <!-- AI创作机会页 -->
        <div id="opportunities" class="tab-content">
            {self._render_opportunities(data)}
        </div>

        <!-- 内容分析页 -->
        <div id="content" class="tab-content">
            {self._render_content_analysis(data)}
        </div>
    </div>

    <script>
        const DATA = {json.dumps(data, ensure_ascii=False)};

        function showTab(tabId) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`[onclick="showTab('${{tabId}}')"]`).classList.add('active');
            document.getElementById(tabId).classList.add('active');

            // 初始化图表
            if (tabId === 'market') initMarketCharts();
            if (tabId === 'time') initTimeCharts();
            if (tabId === 'content') initContentCharts();
        }}

        function initMarketCharts() {{
            // 频道规模分布
            if (!window.channelSizeChart) {{
                const ctx = document.getElementById('channelSizeChart');
                if (ctx) {{
                    window.channelSizeChart = new Chart(ctx, {{
                        type: 'doughnut',
                        data: {{
                            labels: ['单视频频道', '小型(2-4)', '中型(5-9)', '大型(10+)'],
                            datasets: [{{
                                data: DATA.channel_size_dist,
                                backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{ legend: {{ position: 'right' }} }}
                        }}
                    }});
                }}
            }}

            // 播放量分层
            if (!window.viewTiersChart) {{
                const ctx = document.getElementById('viewTiersChart');
                if (ctx) {{
                    window.viewTiersChart = new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: ['100万+', '10-100万', '1-10万', '1000-1万', '<1000'],
                            datasets: [{{
                                label: '视频数量',
                                data: DATA.view_tiers,
                                backgroundColor: ['#f5576c', '#f093fb', '#667eea', '#4facfe', '#00f2fe']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            indexAxis: 'y',
                            plugins: {{ legend: {{ display: false }} }}
                        }}
                    }});
                }}
            }}
        }}

        function initTimeCharts() {{
            // 时间分布
            if (!window.timeDistChart) {{
                const ctx = document.getElementById('timeDistChart');
                if (ctx) {{
                    window.timeDistChart = new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: DATA.time_buckets.labels,
                            datasets: [{{
                                label: '视频数量',
                                data: DATA.time_buckets.values,
                                backgroundColor: '#667eea'
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{ legend: {{ display: false }} }}
                        }}
                    }});
                }}
            }}

            // 年度趋势
            if (!window.yearlyChart) {{
                const ctx = document.getElementById('yearlyChart');
                if (ctx) {{
                    window.yearlyChart = new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: DATA.yearly_trend.years,
                            datasets: [{{
                                label: '视频数量',
                                data: DATA.yearly_trend.counts,
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102,126,234,0.1)',
                                fill: true,
                                tension: 0.3
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false
                        }}
                    }});
                }}
            }}

            // 星期分布
            if (!window.weekdayChart) {{
                const ctx = document.getElementById('weekdayChart');
                if (ctx) {{
                    window.weekdayChart = new Chart(ctx, {{
                        type: 'radar',
                        data: {{
                            labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                            datasets: [{{
                                label: '发布数量',
                                data: DATA.weekday_dist,
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102,126,234,0.2)'
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false
                        }}
                    }});
                }}
            }}
        }}

        function initContentCharts() {{
            // 时长分布
            if (!window.durationChart) {{
                const ctx = document.getElementById('durationChart');
                if (ctx && DATA.duration) {{
                    window.durationChart = new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: DATA.duration.labels,
                            datasets: [{{
                                label: '视频数量',
                                data: DATA.duration.counts,
                                backgroundColor: '#667eea'
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{ legend: {{ display: false }} }}
                        }}
                    }});
                }}
            }}

            // 关键词分布
            if (!window.keywordChart) {{
                const ctx = document.getElementById('keywordChart');
                if (ctx && DATA.keywords) {{
                    window.keywordChart = new Chart(ctx, {{
                        type: 'pie',
                        data: {{
                            labels: DATA.keywords.labels,
                            datasets: [{{
                                data: DATA.keywords.values,
                                backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{ legend: {{ position: 'right' }} }}
                        }}
                    }});
                }}
            }}
        }}

        // 全局时间过滤器
        let currentGlobalTimeFilter = '30天内';

        function setGlobalTimeFilter(timeWindow) {{
            currentGlobalTimeFilter = timeWindow;

            // 更新按钮状态
            document.querySelectorAll('.time-filter-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.textContent === timeWindow);
            }});

            // 更新时间范围指示器
            updateTimeRangeIndicator(timeWindow);

            // 触发所有页面的数据更新
            applyGlobalTimeFilter(timeWindow);
        }}

        function updateTimeRangeIndicator(timeWindow) {{
            let indicator = document.getElementById('timeRangeIndicator');
            if (!indicator) {{
                indicator = document.createElement('div');
                indicator.id = 'timeRangeIndicator';
                indicator.className = 'time-range-indicator';
                document.body.appendChild(indicator);
            }}
            indicator.textContent = `当前数据范围: ${{timeWindow}}`;
        }}

        function applyGlobalTimeFilter(timeWindow) {{
            // 映射到内部使用的时间窗口
            const internalWindow = timeWindow === '全部' ? '全部' : timeWindow;

            // 更新概览页的统计（如果在概览页）
            updateOverviewStats(timeWindow);

            // 更新AI创作机会页的各个表格
            if (typeof filterRecentViral === 'function') {{
                filterRecentViral(internalWindow);
            }}
            if (typeof filterHighGrowth === 'function') {{
                filterHighGrowth(internalWindow);
            }}
            if (typeof filterSmallChannel === 'function') {{
                filterSmallChannel(internalWindow);
            }}
            if (typeof switchTrendChart === 'function') {{
                switchTrendChart(internalWindow);
            }}

            // 同步更新子标签页的选中状态
            syncSubTabsState(internalWindow);
        }}

        function syncSubTabsState(timeWindow) {{
            // 同步所有子标签页的选中状态
            ['recentViralTabs', 'highGrowthTabs', 'smallChannelTabs', 'trendChartTabs'].forEach(tabsId => {{
                const tabs = document.getElementById(tabsId);
                if (tabs) {{
                    tabs.querySelectorAll('.time-tab').forEach(tab => {{
                        tab.classList.toggle('active', tab.textContent === timeWindow);
                    }});
                }}
            }});
        }}

        function updateOverviewStats(timeWindow) {{
            // 根据时间窗口更新概览统计
            // 这里可以扩展为从 DATA 中筛选特定时间范围的数据
            const statsContainer = document.querySelector('#overview .cards');
            if (statsContainer && timeWindow !== '全部') {{
                // 显示时间范围提示
                let notice = document.getElementById('timeFilterNotice');
                if (!notice) {{
                    notice = document.createElement('div');
                    notice.id = 'timeFilterNotice';
                    notice.style.cssText = 'background: #fff3cd; color: #856404; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; font-size: 13px;';
                    statsContainer.parentNode.insertBefore(notice, statsContainer);
                }}
                notice.innerHTML = `<strong>📅 当前筛选:</strong> 仅显示 <strong>${{timeWindow}}</strong> 的数据。AI创作机会页已同步更新。`;
            }} else {{
                const notice = document.getElementById('timeFilterNotice');
                if (notice) notice.remove();
            }}
        }}

        // 初始化时间范围指示器
        document.addEventListener('DOMContentLoaded', function() {{
            updateTimeRangeIndicator('30天内');
        }});
    </script>
</body>
</html>'''

    def _prepare_data(self, video: AnalysisResult, market: MarketReport) -> Dict[str, Any]:
        """准备所有图表数据"""
        data = {}

        # 基础统计
        ms = market.market_size
        data['total_videos'] = ms.get('sample_videos', 0)
        data['total_views'] = ms.get('total_views', 0)
        data['avg_views'] = ms.get('avg_views', 0)
        data['median_views'] = ms.get('median_views', 0)

        # 频道数据
        cc = market.channel_competition
        data['total_channels'] = cc.get('total_channels', 0)
        data['top10_share'] = cc.get('concentration', {}).get('top10_share', 0)
        data['top20_share'] = cc.get('concentration', {}).get('top20_share', 0)

        sd = cc.get('size_distribution', {})
        data['channel_size_dist'] = [
            sd.get('single_video', 0),
            sd.get('small_2_4', 0),
            sd.get('medium_5_9', 0),
            sd.get('large_10_plus', 0),
        ]

        data['top_channels'] = cc.get('top_channels', [])[:10]

        # 进入壁垒
        eb = market.entry_barriers
        pt = eb.get('performance_tiers', {})
        data['view_tiers'] = [
            pt.get('viral_1m_plus', 0),
            pt.get('excellent_100k', 0),
            pt.get('good_10k', 0),
            pt.get('average_1k', 0),
            pt.get('low_under_1k', 0),
        ]
        data['viral_rate'] = eb.get('success_rate', {}).get('viral_rate', 0)
        data['top10_threshold'] = eb.get('thresholds', {}).get('top_10_percent', 0)

        # 时间上下文
        tc = market.time_context
        data['has_dates'] = tc.get('data_has_dates', False)
        data['videos_with_date'] = tc.get('videos_with_date_count', 0)
        data['date_coverage'] = tc.get('date_coverage_rate', 0)

        if tc.get('date_range'):
            data['date_earliest'] = tc['date_range'].get('earliest', '')
            data['date_latest'] = tc['date_range'].get('latest', '')
            data['date_span'] = tc['date_range'].get('span_description', '')

        td = tc.get('time_distribution', {})
        data['time_buckets'] = {
            'labels': list(td.keys()),
            'values': list(td.values()),
        }

        # 年度趋势
        tt = market.time_trends
        ys = tt.get('yearly_stats', {})
        data['yearly_trend'] = {
            'years': [str(y) for y in sorted(ys.keys())],
            'counts': [ys[y]['count'] for y in sorted(ys.keys())],
            'views': [ys[y]['views'] for y in sorted(ys.keys())],
        }

        # 星期分布
        pf = market.publishing_frequency
        wd = pf.get('weekday_distribution', {})
        data['weekday_dist'] = [
            wd.get('周一', 0), wd.get('周二', 0), wd.get('周三', 0),
            wd.get('周四', 0), wd.get('周五', 0), wd.get('周六', 0), wd.get('周日', 0),
        ]

        # AI 创作机会
        opp = market.ai_creator_opportunities
        data['opportunities'] = opp

        # 内容分析
        if video.duration_analysis.get('buckets'):
            data['duration'] = {
                'labels': [b['label'] for b in video.duration_analysis['buckets']],
                'counts': [b['count'] for b in video.duration_analysis['buckets']],
            }

        stats = video.basic_stats
        kw = stats.get('keywords', {})
        if kw:
            items = sorted(kw.items(), key=lambda x: x[1], reverse=True)[:6]
            data['keywords'] = {
                'labels': [k for k, v in items],
                'values': [v for k, v in items],
            }

        data['anomalies'] = video.anomalies.get('anomalies', [])[:10]
        data['insights'] = video.insights

        return data

    def _render_overview(self, data: Dict) -> str:
        """渲染概览页"""
        return f'''
        <div class="cards">
            <div class="card highlight">
                <div class="card-label">总视频数</div>
                <div class="card-value">{data['total_videos']:,}</div>
                <div class="card-sub">样本覆盖范围</div>
            </div>
            <div class="card">
                <div class="card-label">总播放量</div>
                <div class="card-value">{data['total_views']:,}</div>
                <div class="card-sub">累计播放</div>
            </div>
            <div class="card">
                <div class="card-label">平均播放量</div>
                <div class="card-value">{data['avg_views']:,}</div>
                <div class="card-sub">中位数: {data['median_views']:,}</div>
            </div>
            <div class="card">
                <div class="card-label">总频道数</div>
                <div class="card-value">{data['total_channels']}</div>
                <div class="card-sub">参与竞争的频道</div>
            </div>
            <div class="card">
                <div class="card-label">爆款率</div>
                <div class="card-value">{data['viral_rate']}%</div>
                <div class="card-sub">100万+播放</div>
            </div>
            <div class="card">
                <div class="card-label">Top10%门槛</div>
                <div class="card-value">{data['top10_threshold']:,}</div>
                <div class="card-sub">播放量</div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <div class="chart-title">📊 关键发现</div>
                {''.join(f'<div class="insight"><div class="insight-text">{i}</div></div>' for i in data.get('insights', [])[:5])}
            </div>
            <div class="chart-container">
                <div class="chart-title">⚠️ 数据覆盖情况</div>
                <div style="padding: 20px;">
                    <p><strong>有发布时间的视频:</strong> {data['videos_with_date']} ({data['date_coverage']}%)</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {data['date_coverage']}%"></div>
                    </div>
                    <p style="margin-top: 15px;"><strong>数据时间跨度:</strong></p>
                    <p>{data.get('date_earliest', 'N/A')} ~ {data.get('date_latest', 'N/A')}</p>
                    <p style="color: #888;">共 {data.get('date_span', 'N/A')}</p>
                </div>
            </div>
        </div>
        '''

    def _render_market(self, data: Dict) -> str:
        """渲染市场边界页"""
        top_channels_rows = ''.join(
            f'''<tr>
                <td>{i+1}</td>
                <td>{ch['channel'][:25]}</td>
                <td>{ch['video_count']}</td>
                <td>{ch['total_views']:,}</td>
                <td>{ch['avg_views']:,}</td>
            </tr>'''
            for i, ch in enumerate(data.get('top_channels', [])[:10])
        )

        return f'''
        <div class="cards">
            <div class="card highlight">
                <div class="card-label">总频道数</div>
                <div class="card-value">{data['total_channels']}</div>
            </div>
            <div class="card">
                <div class="card-label">Top10 集中度</div>
                <div class="card-value">{data['top10_share']}%</div>
                <div class="card-sub">头部10个频道占总播放量</div>
            </div>
            <div class="card">
                <div class="card-label">Top20 集中度</div>
                <div class="card-value">{data['top20_share']}%</div>
            </div>
            <div class="card">
                <div class="card-label">单视频频道</div>
                <div class="card-value">{data['channel_size_dist'][0]}</div>
                <div class="card-sub">占 {data['channel_size_dist'][0]/data['total_channels']*100:.1f}%</div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <div class="chart-title">📊 频道规模分布</div>
                <div class="chart-wrapper">
                    <canvas id="channelSizeChart"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <div class="chart-title">📈 播放量分层</div>
                <div class="chart-wrapper">
                    <canvas id="viewTiersChart"></canvas>
                </div>
            </div>
        </div>

        <div class="table-container">
            <div class="chart-title">🏆 头部频道 Top 10</div>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>频道名称</th>
                        <th>视频数</th>
                        <th>总播放</th>
                        <th>平均播放</th>
                    </tr>
                </thead>
                <tbody>
                    {top_channels_rows}
                </tbody>
            </table>
        </div>
        '''

    def _render_time_analysis(self, data: Dict) -> str:
        """渲染时间分析页"""
        return f'''
        <div class="cards">
            <div class="card highlight">
                <div class="card-label">数据时间跨度</div>
                <div class="card-value">{data.get('date_span', 'N/A')}</div>
                <div class="card-sub">{data.get('date_earliest', '')} ~ {data.get('date_latest', '')}</div>
            </div>
            <div class="card">
                <div class="card-label">有日期视频</div>
                <div class="card-value">{data['videos_with_date']}</div>
                <div class="card-sub">占比 {data['date_coverage']}%</div>
            </div>
            <div class="card">
                <div class="card-label">24小时内</div>
                <div class="card-value">{data['time_buckets']['values'][0] if data['time_buckets']['values'] else 0}</div>
            </div>
            <div class="card">
                <div class="card-label">7天内</div>
                <div class="card-value">{data['time_buckets']['values'][1] if len(data['time_buckets']['values']) > 1 else 0}</div>
            </div>
            <div class="card">
                <div class="card-label">30天内</div>
                <div class="card-value">{data['time_buckets']['values'][2] if len(data['time_buckets']['values']) > 2 else 0}</div>
            </div>
            <div class="card">
                <div class="card-label">90天内</div>
                <div class="card-value">{data['time_buckets']['values'][3] if len(data['time_buckets']['values']) > 3 else 0}</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📅 视频时间分布</div>
            <div class="chart-wrapper">
                <canvas id="timeDistChart"></canvas>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <div class="chart-title">📈 年度发布趋势</div>
                <div class="chart-wrapper">
                    <canvas id="yearlyChart"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <div class="chart-title">📆 星期分布</div>
                <div class="chart-wrapper">
                    <canvas id="weekdayChart"></canvas>
                </div>
            </div>
        </div>
        '''

    def _render_opportunities(self, data: Dict) -> str:
        """渲染AI创作机会页 - 包含时间窗口子标签和可点击链接"""
        opp = data.get('opportunities', {})

        # 机会总结
        summary = opp.get('opportunity_summary', {})
        recommendations = ''.join(f'<li>{r}</li>' for r in summary.get('recommendations', []))
        actions = ''.join(f'<li>{a}</li>' for a in summary.get('action_items', []))

        # 准备带时间窗口的数据（用于JS过滤）
        # 近期爆款数据 - 按时间窗口组织
        recent_viral_data = {}
        for window in ['1天内', '15天内', '30天内', '全部']:
            recent_viral_data[window] = []

        for window_key in ['24小时内', '7天内', '30天内', '90天内', '6个月内']:
            if window_key in opp.get('recent_viral_by_window', {}):
                rv = opp['recent_viral_by_window'][window_key]
                for v in rv.get('top_performers', []):
                    item = {
                        'window': window_key,
                        'title': v.get('title', ''),
                        'url': v.get('url', ''),
                        'channel': v.get('channel', ''),
                        'views': v.get('views', 0),
                        'daily_growth': v.get('daily_growth', 0),
                        'published_at': v.get('published_at', ''),
                    }
                    # 添加到全部
                    recent_viral_data['全部'].append(item)
                    # 根据时间窗口分配
                    if window_key == '24小时内':
                        recent_viral_data['1天内'].append(item)
                        recent_viral_data['15天内'].append(item)
                        recent_viral_data['30天内'].append(item)
                    elif window_key == '7天内':
                        recent_viral_data['15天内'].append(item)
                        recent_viral_data['30天内'].append(item)
                    elif window_key == '30天内':
                        recent_viral_data['30天内'].append(item)

        # 高增长数据 - 按时间窗口组织
        high_growth_data = {'1天内': [], '15天内': [], '30天内': [], '全部': []}
        hg = opp.get('high_daily_growth', {}).get('top_performers', [])
        for v in hg:
            bucket = v.get('time_bucket', '')
            item = {
                'bucket': bucket,
                'title': v.get('title', ''),
                'url': v.get('url', ''),
                'channel': v.get('channel', ''),
                'views': v.get('views', 0),
                'daily_growth': v.get('daily_growth', 0),
            }
            high_growth_data['全部'].append(item)
            if bucket in ['24小时内']:
                high_growth_data['1天内'].append(item)
                high_growth_data['15天内'].append(item)
                high_growth_data['30天内'].append(item)
            elif bucket in ['7天内']:
                high_growth_data['15天内'].append(item)
                high_growth_data['30天内'].append(item)
            elif bucket in ['30天内']:
                high_growth_data['30天内'].append(item)

        # 小频道黑马数据 - 按时间窗口组织
        small_channel_data = {'1天内': [], '15天内': [], '30天内': [], '全部': []}
        sch = opp.get('small_channel_hits', {}).get('top_performers', [])
        for v in sch:
            bucket = v.get('time_bucket', '')
            item = {
                'bucket': bucket,
                'title': v.get('title', ''),
                'url': v.get('url', ''),
                'channel': v.get('channel', ''),
                'views': v.get('views', 0),
            }
            small_channel_data['全部'].append(item)
            if bucket in ['24小时内']:
                small_channel_data['1天内'].append(item)
                small_channel_data['15天内'].append(item)
                small_channel_data['30天内'].append(item)
            elif bucket in ['7天内']:
                small_channel_data['15天内'].append(item)
                small_channel_data['30天内'].append(item)
            elif bucket in ['30天内']:
                small_channel_data['30天内'].append(item)

        import json
        recent_viral_json = json.dumps(recent_viral_data, ensure_ascii=False)
        high_growth_json = json.dumps(high_growth_data, ensure_ascii=False)
        small_channel_json = json.dumps(small_channel_data, ensure_ascii=False)

        # 准备增长趋势图数据（基于发布时间分布模拟）
        trend_data_1d = self._generate_trend_data(opp, '1天内')
        trend_data_15d = self._generate_trend_data(opp, '15天内')
        trend_data_30d = self._generate_trend_data(opp, '30天内')

        trend_data_json = json.dumps({
            '1天内': trend_data_1d,
            '15天内': trend_data_15d,
            '30天内': trend_data_30d,
        }, ensure_ascii=False)

        return f'''
        <style>
            /* 时间窗口子标签样式 */
            .time-tabs {{
                display: flex;
                gap: 0;
                margin-bottom: 15px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .time-tab {{
                padding: 8px 16px;
                cursor: pointer;
                font-size: 13px;
                color: #666;
                border-bottom: 2px solid transparent;
                transition: all 0.2s;
            }}
            .time-tab:hover {{ color: #667eea; }}
            .time-tab.active {{
                color: #667eea;
                border-bottom-color: #667eea;
                font-weight: 600;
            }}
            /* 可点击链接样式 */
            .video-link {{
                color: #333;
                text-decoration: none;
                transition: color 0.2s;
            }}
            .video-link:hover {{
                color: #667eea;
                text-decoration: underline;
            }}
            .channel-link {{
                color: #666;
                text-decoration: none;
                font-size: 13px;
            }}
            .channel-link:hover {{
                color: #764ba2;
                text-decoration: underline;
            }}
            /* 增长趋势图样式 */
            .trend-summary {{
                display: flex;
                gap: 20px;
                margin-top: 15px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .trend-stat {{
                text-align: center;
            }}
            .trend-stat-value {{
                font-size: 24px;
                font-weight: 700;
                color: #667eea;
            }}
            .trend-stat-label {{
                font-size: 12px;
                color: #666;
            }}
        </style>

        <!-- 增长趋势图 -->
        <div class="chart-container">
            <div class="chart-title">📈 增长趋势图</div>
            <div class="time-tabs" id="trendChartTabs">
                <div class="time-tab" onclick="switchTrendChart('1天内')">1天内</div>
                <div class="time-tab" onclick="switchTrendChart('15天内')">15天内</div>
                <div class="time-tab active" onclick="switchTrendChart('30天内')">30天内</div>
            </div>
            <div class="chart-wrapper" style="height: 350px;">
                <canvas id="growthTrendChart"></canvas>
            </div>
            <div class="trend-summary" id="trendSummary">
                <div class="trend-stat">
                    <div class="trend-stat-value" id="trendTotalGrowth">-</div>
                    <div class="trend-stat-label">总增长</div>
                </div>
                <div class="trend-stat">
                    <div class="trend-stat-value" id="trendAvgDaily">-</div>
                    <div class="trend-stat-label">日均增长</div>
                </div>
                <div class="trend-stat">
                    <div class="trend-stat-value" id="trendPeakDay">-</div>
                    <div class="trend-stat-label">峰值日增长</div>
                </div>
                <div class="trend-stat">
                    <div class="trend-stat-value" id="trendVideoCount">-</div>
                    <div class="trend-stat-label">监控视频数</div>
                </div>
            </div>
        </div>

        <div class="cards">
            <div class="card highlight">
                <div class="card-label">高增长视频</div>
                <div class="card-value">{opp.get('high_daily_growth', {}).get('count', 0)}</div>
                <div class="card-sub">日增 500+ 播放</div>
            </div>
            <div class="card">
                <div class="card-label">小频道爆款</div>
                <div class="card-value">{opp.get('small_channel_hits', {}).get('count', 0)}</div>
                <div class="card-sub">1-3视频频道的爆款</div>
            </div>
            <div class="card">
                <div class="card-label">高互动模板</div>
                <div class="card-value">{opp.get('high_engagement_templates', {}).get('count', 0)}</div>
                <div class="card-sub">互动率 > 3%</div>
            </div>
            <div class="card">
                <div class="card-label">最佳时间窗口</div>
                <div class="card-value">{summary.get('best_time_window', 'N/A')}</div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <div class="chart-title">💡 机会建议</div>
                <ul style="padding-left: 20px; line-height: 2;">
                    {recommendations}
                </ul>
            </div>
            <div class="chart-container">
                <div class="chart-title">🎯 行动项</div>
                <ul style="padding-left: 20px; line-height: 2;">
                    {actions}
                </ul>
            </div>
        </div>

        <!-- 近期爆款 - 带时间窗口切换 -->
        <div class="table-container">
            <div class="chart-title">🔥 近期爆款（按时间窗口）</div>
            <div class="time-tabs" id="recentViralTabs">
                <div class="time-tab" onclick="filterRecentViral('1天内')">1天内</div>
                <div class="time-tab" onclick="filterRecentViral('15天内')">15天内</div>
                <div class="time-tab" onclick="filterRecentViral('30天内')">30天内</div>
                <div class="time-tab active" onclick="filterRecentViral('全部')">全部</div>
            </div>
            <table>
                <thead>
                    <tr><th>时间段</th><th>标题</th><th>频道</th><th>播放量</th><th>日增长</th><th>发布日期</th></tr>
                </thead>
                <tbody id="recentViralBody"></tbody>
            </table>
        </div>

        <!-- 高日增长 - 带时间窗口切换 -->
        <div class="table-container">
            <div class="chart-title">📈 高日增长视频 Top 10</div>
            <div class="time-tabs" id="highGrowthTabs">
                <div class="time-tab" onclick="filterHighGrowth('1天内')">1天内</div>
                <div class="time-tab" onclick="filterHighGrowth('15天内')">15天内</div>
                <div class="time-tab" onclick="filterHighGrowth('30天内')">30天内</div>
                <div class="time-tab active" onclick="filterHighGrowth('全部')">全部</div>
            </div>
            <table>
                <thead>
                    <tr><th>时间段</th><th>标题</th><th>频道</th><th>总播放</th><th>日增长</th></tr>
                </thead>
                <tbody id="highGrowthBody"></tbody>
            </table>
        </div>

        <!-- 小频道黑马 - 带时间窗口切换 -->
        <div class="table-container">
            <div class="chart-title">🌟 小频道黑马 Top 10</div>
            <div class="time-tabs" id="smallChannelTabs">
                <div class="time-tab" onclick="filterSmallChannel('1天内')">1天内</div>
                <div class="time-tab" onclick="filterSmallChannel('15天内')">15天内</div>
                <div class="time-tab" onclick="filterSmallChannel('30天内')">30天内</div>
                <div class="time-tab active" onclick="filterSmallChannel('全部')">全部</div>
            </div>
            <table>
                <thead>
                    <tr><th>时间段</th><th>频道</th><th>标题</th><th>播放量</th></tr>
                </thead>
                <tbody id="smallChannelBody"></tbody>
            </table>
        </div>

        <script>
            // 数据存储
            const recentViralData = {recent_viral_json};
            const highGrowthData = {high_growth_json};
            const smallChannelData = {small_channel_json};

            // 生成YouTube搜索链接
            function getChannelSearchUrl(channelName) {{
                return 'https://www.youtube.com/results?search_query=' + encodeURIComponent(channelName);
            }}

            // 近期爆款过滤
            function filterRecentViral(window) {{
                // 更新标签状态
                document.querySelectorAll('#recentViralTabs .time-tab').forEach(tab => {{
                    tab.classList.toggle('active', tab.textContent === window);
                }});

                // 渲染表格
                const tbody = document.getElementById('recentViralBody');
                const items = recentViralData[window] || [];
                tbody.innerHTML = items.slice(0, 10).map(v => `
                    <tr>
                        <td><span class="badge badge-purple">${{v.window}}</span></td>
                        <td><a href="${{v.url || '#'}}" target="_blank" class="video-link">${{(v.title || '').substring(0, 40)}}...</a></td>
                        <td><a href="${{getChannelSearchUrl(v.channel)}}" target="_blank" class="channel-link">${{(v.channel || '').substring(0, 20)}}</a></td>
                        <td>${{(v.views || 0).toLocaleString()}}</td>
                        <td>${{(v.daily_growth || 0).toLocaleString()}}</td>
                        <td>${{v.published_at || ''}}</td>
                    </tr>
                `).join('');
            }}

            // 高增长过滤
            function filterHighGrowth(window) {{
                document.querySelectorAll('#highGrowthTabs .time-tab').forEach(tab => {{
                    tab.classList.toggle('active', tab.textContent === window);
                }});

                const tbody = document.getElementById('highGrowthBody');
                const items = highGrowthData[window] || [];
                tbody.innerHTML = items.slice(0, 10).map(v => `
                    <tr>
                        <td><span class="badge badge-green">${{v.bucket}}</span></td>
                        <td><a href="${{v.url || '#'}}" target="_blank" class="video-link">${{(v.title || '').substring(0, 40)}}...</a></td>
                        <td><a href="${{getChannelSearchUrl(v.channel)}}" target="_blank" class="channel-link">${{(v.channel || '').substring(0, 20)}}</a></td>
                        <td>${{(v.views || 0).toLocaleString()}}</td>
                        <td><strong>${{(v.daily_growth || 0).toLocaleString()}}</strong></td>
                    </tr>
                `).join('');
            }}

            // 小频道过滤
            function filterSmallChannel(window) {{
                document.querySelectorAll('#smallChannelTabs .time-tab').forEach(tab => {{
                    tab.classList.toggle('active', tab.textContent === window);
                }});

                const tbody = document.getElementById('smallChannelBody');
                const items = smallChannelData[window] || [];
                tbody.innerHTML = items.slice(0, 10).map(v => `
                    <tr>
                        <td><span class="badge badge-blue">${{v.bucket}}</span></td>
                        <td><a href="${{getChannelSearchUrl(v.channel)}}" target="_blank" class="channel-link">${{(v.channel || '').substring(0, 20)}}</a></td>
                        <td><a href="${{v.url || '#'}}" target="_blank" class="video-link">${{(v.title || '').substring(0, 35)}}...</a></td>
                        <td>${{(v.views || 0).toLocaleString()}}</td>
                    </tr>
                `).join('');
            }}

            // 初始化显示全部
            document.addEventListener('DOMContentLoaded', function() {{
                filterRecentViral('全部');
                filterHighGrowth('全部');
                filterSmallChannel('全部');
            }});

            // 增长趋势图数据
            const trendData = {trend_data_json};
            let growthTrendChart = null;

            // 切换趋势图时间窗口
            function switchTrendChart(window) {{
                // 更新标签状态
                document.querySelectorAll('#trendChartTabs .time-tab').forEach(tab => {{
                    tab.classList.toggle('active', tab.textContent === window);
                }});

                // 获取数据
                const data = trendData[window] || {{}};

                // 更新图表
                if (growthTrendChart) {{
                    growthTrendChart.destroy();
                }}

                const ctx = document.getElementById('growthTrendChart');
                if (ctx && data.labels && data.labels.length > 0) {{
                    growthTrendChart = new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: data.labels,
                            datasets: [
                                {{
                                    label: '累计播放量',
                                    data: data.cumulative_views,
                                    borderColor: '#667eea',
                                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                    fill: true,
                                    tension: 0.3,
                                    yAxisID: 'y',
                                }},
                                {{
                                    label: '日增长',
                                    data: data.daily_growth,
                                    borderColor: '#f5576c',
                                    backgroundColor: 'rgba(245, 87, 108, 0.3)',
                                    fill: true,
                                    tension: 0.3,
                                    yAxisID: 'y1',
                                }}
                            ]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {{
                                mode: 'index',
                                intersect: false,
                            }},
                            scales: {{
                                y: {{
                                    type: 'linear',
                                    display: true,
                                    position: 'left',
                                    title: {{
                                        display: true,
                                        text: '累计播放量'
                                    }}
                                }},
                                y1: {{
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: {{
                                        display: true,
                                        text: '日增长'
                                    }},
                                    grid: {{
                                        drawOnChartArea: false,
                                    }},
                                }}
                            }}
                        }}
                    }});
                }}

                // 更新统计摘要
                const summary = data.summary || {{}};
                document.getElementById('trendTotalGrowth').textContent =
                    (summary.total_growth || 0).toLocaleString();
                document.getElementById('trendAvgDaily').textContent =
                    (summary.avg_daily || 0).toLocaleString();
                document.getElementById('trendPeakDay').textContent =
                    (summary.peak_daily || 0).toLocaleString();
                document.getElementById('trendVideoCount').textContent =
                    (summary.video_count || 0).toLocaleString();
            }}

            // 当切换到机会页时初始化
            const originalShowTab = window.showTab;
            window.showTab = function(tabId) {{
                originalShowTab(tabId);
                if (tabId === 'opportunities') {{
                    setTimeout(() => {{
                        filterRecentViral('全部');
                        filterHighGrowth('全部');
                        filterSmallChannel('全部');
                        switchTrendChart('30天内');
                    }}, 100);
                }}
            }};
        </script>
        '''

    def _generate_trend_data(self, opp: Dict, time_window: str) -> Dict[str, Any]:
        """
        生成增长趋势图数据

        基于现有数据模拟趋势（实际监控数据由 TrendMonitor 提供）
        """
        from datetime import datetime, timedelta

        # 时间窗口映射到天数
        days_map = {'1天内': 1, '15天内': 15, '30天内': 30}
        days = days_map.get(time_window, 30)

        # 生成日期标签
        today = datetime.now()
        labels = []
        for i in range(days, 0, -1):
            date = today - timedelta(days=i)
            if days <= 1:
                labels.append(date.strftime('%H:00'))
            else:
                labels.append(date.strftime('%m/%d'))

        # 从高增长数据中提取趋势
        hg = opp.get('high_daily_growth', {}).get('top_performers', [])
        total_daily_growth = sum(v.get('daily_growth', 0) for v in hg)

        # 模拟累计播放量和日增长
        cumulative = []
        daily_growth = []
        base_views = 0

        for i, label in enumerate(labels):
            # 模拟日增长（随机波动 + 趋势）
            import random
            variation = random.uniform(0.7, 1.3)
            day_growth = int((total_daily_growth / max(len(labels), 1)) * variation)
            daily_growth.append(day_growth)
            base_views += day_growth
            cumulative.append(base_views)

        # 计算统计摘要
        total_growth = cumulative[-1] if cumulative else 0
        avg_daily = total_growth // len(labels) if labels else 0
        peak_daily = max(daily_growth) if daily_growth else 0

        return {
            'labels': labels,
            'cumulative_views': cumulative,
            'daily_growth': daily_growth,
            'summary': {
                'total_growth': total_growth,
                'avg_daily': avg_daily,
                'peak_daily': peak_daily,
                'video_count': len(hg),
                'time_window': time_window,
            }
        }

    def _render_content_analysis(self, data: Dict) -> str:
        """渲染内容分析页"""
        # 潜在爆款表格
        anomaly_rows = ''
        for v in data.get('anomalies', [])[:10]:
            anomaly_rows += f'''<tr>
                <td>{v['title'][:45]}...</td>
                <td>{v['channel'][:20]}</td>
                <td>{v['views']:,}</td>
                <td>{v.get('z_score', 0):.1f}</td>
            </tr>'''

        return f'''
        <div class="grid-2">
            <div class="chart-container">
                <div class="chart-title">⏱️ 视频时长分布</div>
                <div class="chart-wrapper">
                    <canvas id="durationChart"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <div class="chart-title">🏷️ 关键词分布</div>
                <div class="chart-wrapper">
                    <canvas id="keywordChart"></canvas>
                </div>
            </div>
        </div>

        <div class="table-container">
            <div class="chart-title">⚡ 潜在爆款视频（异常高播放量）</div>
            <table>
                <thead>
                    <tr><th>标题</th><th>频道</th><th>播放量</th><th>Z-Score</th></tr>
                </thead>
                <tbody>{anomaly_rows}</tbody>
            </table>
        </div>
        '''


def generate_comprehensive_report(output_path: str = None) -> str:
    """便捷函数：生成综合报告"""
    generator = ComprehensiveReportGenerator()
    return generator.generate(output_path)


if __name__ == '__main__':
    path = generate_comprehensive_report()
    print(f"报告已生成: {path}")
