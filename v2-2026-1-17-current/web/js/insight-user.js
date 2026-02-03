/**
 * insight-user.js - 用户洞察模块 (Tab8)
 *
 * 包含：
 * - 用户洞察数据加载（loadUserInsightData, initUserInsightCharts）
 * - 模式38: 评论热词（renderHotwordsTable）
 * - 模式39: 用户问题（renderQuestionsChart）
 * - 模式40: 情感分布（renderSentimentBars）
 * - 模式41: 话题趋势（renderTrendChart）
 * - 模式42: 高赞特征（renderHighLikedStats）
 * - 模式43: 语言分布（renderLanguageDistribution）
 * - 真实案例渲染（renderRealExamples）
 * - 静态结论注册（registerStaticUserInsightConclusions）
 */

// ========== 命名空间 ==========
window.InsightUser = window.InsightUser || {};

(function(exports) {
    'use strict';

    // ========== 依赖检查 ==========
    function getCore() {
        return window.InsightCore || {};
    }

    function getReport() {
        return window.InsightReport || {};
    }

    function getCharts() {
        return window.InsightCharts || {};
    }

    // 向后兼容的工具函数
    function getDateRange(days) {
        return getCore().getDateRange ? getCore().getDateRange(days) : { date_from: null, date_to: null };
    }

    function getCurrentKeyword() {
        return getCore().getCurrentKeyword ? getCore().getCurrentKeyword() : (window.currentKeyword || '养生');
    }

    function getCurrentTimePeriod() {
        return getCore().getCurrentTimePeriod ? getCore().getCurrentTimePeriod() : (window.currentTimePeriod || 30);
    }

    function getAPIBase() {
        return getCore().getAPIBase ? getCore().getAPIBase() : window.location.origin;
    }

    function registerPatternConclusion(...args) {
        if (getReport().registerPatternConclusion) {
            getReport().registerPatternConclusion(...args);
        } else if (window.registerPatternConclusion) {
            window.registerPatternConclusion(...args);
        }
    }

    function renderInfoReportFromConclusions() {
        if (getReport().renderInfoReportFromConclusions) {
            getReport().renderInfoReportFromConclusions();
        } else if (window.renderInfoReportFromConclusions) {
            window.renderInfoReportFromConclusions();
        }
    }

    function cacheChartImage(chart, canvasId) {
        if (getReport().cacheChartImage) {
            getReport().cacheChartImage(chart, canvasId);
        } else if (window.cacheChartImage) {
            window.cacheChartImage(chart, canvasId);
        }
    }

    function destroyChart(chartId) {
        if (getCharts().destroyChart) {
            getCharts().destroyChart(chartId);
        } else if (window.destroyChart) {
            window.destroyChart(chartId);
        }
    }

    function showChartNoData(canvasId, dataType) {
        if (getCore().showChartNoData) {
            getCore().showChartNoData(canvasId, dataType);
        } else if (window.showChartNoData) {
            window.showChartNoData(canvasId, dataType);
        }
    }

    function hideChartNoData(canvasId) {
        if (getCore().hideChartNoData) {
            getCore().hideChartNoData(canvasId);
        } else if (window.hideChartNoData) {
            window.hideChartNoData(canvasId);
        }
    }

    // ========== 用户洞察数据缓存 ==========
    let userInsightData = null;
    let languageDistChart = null;

    // ========== 数据加载 ==========

    /**
     * 加载用户洞察数据 - 从 API 获取真实数据（支持时间筛选）
     */
    async function loadUserInsightData(days = null) {
        const timePeriod = days !== null ? days : getCurrentTimePeriod();
        const keyword = getCurrentKeyword();
        const API_BASE = getAPIBase();

        console.log('[User] 正在从 API 加载用户洞察数据... 时间段:', timePeriod, '天');

        try {
            let url = `${API_BASE}/api/user-insights/${encodeURIComponent(keyword)}`;
            if (timePeriod > 0) {
                const { date_from, date_to } = getDateRange(timePeriod);
                if (date_from) url += `?date_from=${date_from}`;
                if (date_to) url += `&date_to=${date_to}`;
            }

            const response = await fetch(url);
            const result = await response.json();

            if (result.status === 'ok' && result.total_comments > 0) {
                userInsightData = result;
                console.log('[User] ✓ 数据加载成功:', result.total_comments, '条评论');
                renderUserInsightData(result);
                renderInfoReportFromConclusions();
            } else {
                console.warn('[User] ⚠️ 暂无评论数据:', result.message || '');
                showNoCommentData();
            }
        } catch (error) {
            console.error('[User] ✗ 加载用户洞察数据失败:', error);
            showNoCommentData();
        }
    }

    /**
     * 初始化用户洞察（向后兼容）
     */
    async function initUserInsightCharts() {
        return loadUserInsightData();
    }

    /**
     * 显示无数据提示
     */
    function showNoCommentData() {
        const tbody = document.getElementById('hotwordsTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#f59e0b;padding:20px;">⚠️ 暂无评论数据，请先运行: python3 scripts/fetch_comments.py</td></tr>';
        }
    }

    // ========== 数据渲染 ==========

    /**
     * 渲染用户洞察数据
     */
    function renderUserInsightData(data) {
        // 更新样本量显示
        const sampleBadge = document.getElementById('hotwordsSample');
        if (sampleBadge) sampleBadge.textContent = `N = ${data.total_comments.toLocaleString()}`;

        // 缓存用户洞察数据（供信息报告展开图表使用）
        window._cachedUserInsights = data;

        // 渲染各模式
        renderHotwordsTable(data.hotwords);
        renderQuestionsChart(data.questions);
        renderSentimentBars(data.sentiment);
        renderLanguageDistribution(data.language);
        renderTrendChart(data.trends);
        renderHighLikedStats(data.high_liked);

        // 渲染真实案例
        if (data.real_examples) {
            renderRealExamples(data.real_examples);
        }

        // 注册用户洞察模式结论
        registerUserInsightConclusions(data);

        console.log('[User] ✓ 用户洞察渲染完成');
    }

    /**
     * 注册用户洞察模式结论
     */
    function registerUserInsightConclusions(data) {
        // 模式38: 评论热词
        if (data.hotwords && data.hotwords.length > 0) {
            const top3Words = data.hotwords.slice(0, 3).map(hw => `"${hw.word}"`).join('、');
            const categories = [...new Set(data.hotwords.slice(0, 5).map(hw => hw.category))];
            registerPatternConclusion('tab8', '38', '评论热词',
                '评论热词',
                `高频词：${top3Words}。主要类别：${categories.join('、')}。用户反馈以${data.hotwords[0]?.category || '互动'}类为主，说明内容获得认可。`
            );
        }

        // 模式39: 用户问题
        if (data.questions && data.questions.types && data.questions.types.length > 0) {
            const sortedTypes = [...data.questions.types].sort((a, b) => b.count - a.count);
            const topType = sortedTypes[0];
            const pct = ((topType.count / data.questions.total) * 100).toFixed(1);
            registerPatternConclusion('tab8', '39', '用户问题',
                '用户问题',
                `${pct}%的问题是"${topType.label}"类（${topType.count}条）。用户最关心${topType.label}相关内容，可针对性创作解答视频。`,
                null,
                'questionsChart'
            );
        }

        // 模式40: 情感分布
        if (data.sentiment) {
            const posRatio = data.sentiment.positive.percentage;
            const score = data.sentiment.score;
            const scoreSign = score >= 0 ? '+' : '';
            registerPatternConclusion('tab8', '40', '情感分布',
                '情感分布',
                `正面情感占${posRatio}%，情感分数${scoreSign}${score.toFixed(3)}。${score > 0.3 ? '整体反馈非常积极，内容受到用户认可。' : score > 0 ? '整体反馈正面，但仍有提升空间。' : '存在较多负面反馈，需关注用户不满点。'}`
            );
        }

        // 模式41: 话题趋势
        if (data.trends && data.trends.topics) {
            const topics = Object.keys(data.trends.topics);
            if (topics.length > 0) {
                const recentTrends = topics.map(topic => {
                    const values = data.trends.topics[topic];
                    const recent = values.slice(-3);
                    const earlier = values.slice(-6, -3);
                    const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
                    const earlierAvg = earlier.length > 0 ? earlier.reduce((a, b) => a + b, 0) / earlier.length : recentAvg;
                    const growth = earlierAvg > 0 ? ((recentAvg - earlierAvg) / earlierAvg * 100).toFixed(0) : 0;
                    return { topic, growth: parseInt(growth), recentAvg };
                }).sort((a, b) => b.growth - a.growth);

                const rising = recentTrends.filter(t => t.growth > 10);
                const falling = recentTrends.filter(t => t.growth < -10);
                let trendText = '';
                if (rising.length > 0) {
                    trendText += `上升趋势：${rising.slice(0, 2).map(t => `${t.topic}(+${t.growth}%)`).join('、')}。`;
                }
                if (falling.length > 0) {
                    trendText += `下降趋势：${falling.slice(0, 2).map(t => `${t.topic}(${t.growth}%)`).join('、')}。`;
                }
                if (!trendText) {
                    trendText = `各话题热度相对稳定，${recentTrends[0]?.topic || '养生'}关注度最高。`;
                }

                registerPatternConclusion('tab8', '41', '话题趋势',
                    '话题趋势',
                    trendText,
                    null,
                    'trendChart'
                );
            }
        }

        // 模式42: 高赞特征
        if (data.high_liked) {
            registerPatternConclusion('tab8', '42', '高赞特征',
                '高赞特征',
                `高赞评论平均${data.high_liked.avg_length}字，${data.high_liked.has_experience_pct}%分享个人经历，${data.high_liked.has_question_pct}%包含问题。最高赞${data.high_liked.max_likes.toLocaleString()}。建议引导用户分享真实体验。`
            );
        }

        // 模式43: 用户语言分布 - 注册到全局认知板块(tab1)
        if (data.language && data.language.distribution && data.language.distribution.length > 0) {
            const topLang = data.language.distribution[0];
            const secondLang = data.language.distribution[1];
            let langText = `主要用户语言：${topLang.name}（${topLang.percentage}%，${topLang.count.toLocaleString()}条）`;
            if (secondLang && secondLang.percentage > 5) {
                langText += `，其次是${secondLang.name}（${secondLang.percentage}%）`;
            }
            langText += '。';
            if (topLang.code === 'zh-TW' || (secondLang && secondLang.code === 'zh-TW' && secondLang.percentage > 20)) {
                langText += '繁体用户占比高，建议同时提供繁体字幕。';
            } else if (topLang.code === 'en' || (secondLang && secondLang.code === 'en' && secondLang.percentage > 10)) {
                langText += '有英语用户群，可考虑添加英文字幕扩大受众。';
            }
            registerPatternConclusion('tab1', '43', '语言分布',
                '语言分布',
                langText,
                null,
                'languageDistChart'
            );
        }

        console.log('[User] ✓ 模式结论注册完成');
    }

    // ========== 模式38: 评论热词 ==========

    function renderHotwordsTable(hotwords) {
        const tbody = document.getElementById('hotwordsTableBody');
        if (!tbody || !hotwords?.length) return;

        const categoryColors = {
            '互动': '#10b981', '效果': '#06b6d4', '疑问': '#f59e0b',
            '行动': '#8b5cf6', '功法': '#ec4899', '其他': '#94a3b8'
        };
        const insights = {
            '感恩': '用户认可度高', '謝謝': '感谢类占主导', '谢谢': '简体用户群',
            '感謝': '繁体用户群', '分享': '内容有价值', '老師': '视创作者为专家',
            '老师': '用户信任度高', '醫師': '医疗权威认可', '健康': '核心关注点',
            '請問': '用户有大量问题'
        };

        tbody.innerHTML = hotwords.slice(0, 10).map(hw => `
            <tr>
                <td>${hw.rank}</td>
                <td><strong style="color:${categoryColors[hw.category] || '#94a3b8'}">${hw.word}</strong></td>
                <td>${hw.count.toLocaleString()}</td>
                <td>${hw.category}</td>
                <td>${insights[hw.word] || '-'}</td>
            </tr>
        `).join('');

        // 渲染词云
        const cloud = document.getElementById('wordCloud');
        if (cloud) {
            const maxCount = hotwords[0]?.count || 1;
            cloud.innerHTML = hotwords.slice(0, 15).map((hw, i) => {
                const size = 0.8 + (hw.count / maxCount) * 1.2;
                const colors = ['#10b981', '#06b6d4', '#f59e0b', '#8b5cf6', '#ec4899'];
                return `<span style="font-size:${size}em;color:${colors[i % 5]};margin:4px;display:inline-block;">${hw.word}</span>`;
            }).join('');
        }
    }

    // ========== 模式39: 用户问题 ==========

    function renderQuestionsChart(questions) {
        const ctx = document.getElementById('questionsChart');
        if (!ctx || !questions) return;

        destroyChart('questionsChart');

        const sortedTypes = questions.types.sort((a, b) => b.count - a.count);
        const colors = ['rgba(249,115,22,0.8)', 'rgba(34,197,94,0.7)', 'rgba(236,72,153,0.7)',
                       'rgba(6,182,212,0.7)', 'rgba(139,92,246,0.7)', 'rgba(148,163,184,0.5)'];

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sortedTypes.map(t => `${t.type} ${t.label}`),
                datasets: [{ data: sortedTypes.map(t => t.count), backgroundColor: colors, borderWidth: 0 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '55%',
                plugins: {
                    legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 10 }, padding: 6 } },
                    tooltip: { callbacks: { label: c => `${c.raw}条 (${((c.raw/questions.total)*100).toFixed(1)}%)` } }
                }
            }
        });

        // 存储到全局图表实例
        if (window.chartInstances) {
            window.chartInstances['questionsChart'] = chart;
        }
        cacheChartImage(chart, 'questionsChart');

        // 更新洞察文字
        const insight = document.getElementById('questionsInsight');
        if (insight) {
            const top = sortedTypes[0];
            const contentEl = insight.querySelector('.chart-insight-content');
            if (contentEl) {
                contentEl.innerHTML = `
                    <strong>${((top.count/questions.total)*100).toFixed(1)}% 是 ${top.type} ${top.label}</strong><br><br>
                    总问句: <strong>${questions.total}</strong> 条 (占评论 ${questions.percentage}%)
                `;
            }
        }

        // 更新样本量 badge
        const sampleEl = document.getElementById('questionsSample');
        if (sampleEl) {
            sampleEl.textContent = `N = ${questions.total.toLocaleString()} 条问句`;
        }
    }

    // ========== 模式40: 情感分布 ==========

    function renderSentimentBars(sentiment) {
        if (!sentiment) return;

        // 正面
        const posText = document.getElementById('sentiment-positive-text');
        const posBar = document.getElementById('sentiment-positive-bar');
        if (posText) posText.textContent = `${sentiment.positive.percentage}% (${sentiment.positive.count.toLocaleString()}条)`;
        if (posBar) posBar.style.width = `${sentiment.positive.percentage}%`;

        // 中性
        const neuText = document.getElementById('sentiment-neutral-text');
        const neuBar = document.getElementById('sentiment-neutral-bar');
        if (neuText) neuText.textContent = `${sentiment.neutral.percentage}% (${sentiment.neutral.count.toLocaleString()}条)`;
        if (neuBar) neuBar.style.width = `${sentiment.neutral.percentage}%`;

        // 负面
        const negText = document.getElementById('sentiment-negative-text');
        const negBar = document.getElementById('sentiment-negative-bar');
        if (negText) negText.textContent = `${sentiment.negative.percentage}% (${sentiment.negative.count.toLocaleString()}条)`;
        if (negBar) negBar.style.width = `${sentiment.negative.percentage}%`;

        // 情感分数
        const scoreEl = document.getElementById('sentiment-score');
        if (scoreEl && sentiment.score !== undefined) {
            const score = sentiment.score;
            const sign = score >= 0 ? '+' : '';
            scoreEl.textContent = `${sign}${score.toFixed(3)}`;
            scoreEl.style.color = score >= 0.3 ? '#10b981' : (score >= 0 ? '#06b6d4' : '#ef4444');
        }

        // 更新样本量 badge
        const total = sentiment.positive.count + sentiment.neutral.count + sentiment.negative.count;
        const sampleEl = document.getElementById('sentimentSample');
        if (sampleEl) {
            sampleEl.textContent = `N = ${total.toLocaleString()}`;
        }
    }

    // ========== 模式41: 话题趋势 ==========

    function renderTrendChart(trends) {
        const ctx = document.getElementById('trendChart');
        if (!ctx || !trends?.months?.length) return;

        destroyChart('trendChart');

        const colors = {
            '养生': { border: 'rgba(6,182,212,1)', bg: 'rgba(6,182,212,0.15)' },
            '睡眠': { border: 'rgba(249,115,22,1)', bg: 'rgba(249,115,22,0.1)' },
            '太极': { border: 'rgba(239,68,68,0.8)', bg: 'transparent' },
            '八段锦': { border: 'rgba(34,197,94,0.8)', bg: 'transparent' },
            '穴位': { border: 'rgba(148,163,184,0.6)', bg: 'transparent' },
            '气功': { border: 'rgba(139,92,246,0.6)', bg: 'transparent' }
        };

        const monthLabels = trends.months.map(m => `${parseInt(m.split('-')[1])}月`);
        const datasets = Object.entries(trends.topics).map(([topic, data], i) => ({
            label: topic, data,
            borderColor: colors[topic]?.border || `hsl(${i*60},70%,50%)`,
            backgroundColor: colors[topic]?.bg || 'transparent',
            tension: 0.3, fill: topic === '养生' || topic === '睡眠',
            pointRadius: 3, pointHoverRadius: 5,
            borderDash: ['太极', '穴位', '气功'].includes(topic) ? [5,5] : []
        }));

        const chart = new Chart(ctx, {
            type: 'line',
            data: { labels: monthLabels, datasets },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { position: 'top', labels: { color: '#94a3b8', font: { size: 11 }, usePointStyle: true, padding: 15 } },
                    tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.raw}次提及` } }
                },
                scales: {
                    x: { grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#94a3b8' } },
                    y: { grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#94a3b8' }, beginAtZero: true }
                }
            }
        });

        if (window.chartInstances) {
            window.chartInstances['trendChart'] = chart;
        }
        cacheChartImage(chart, 'trendChart');
    }

    // ========== 模式42: 高赞特征 ==========

    function renderHighLikedStats(stats) {
        if (!stats) return;
        const cards = document.querySelectorAll('#tab8-sub5 .pattern-data-section > div > div');
        if (cards.length >= 4) {
            const firstChild0 = cards[0].querySelector('div:first-child');
            const firstChild1 = cards[1].querySelector('div:first-child');
            const firstChild2 = cards[2].querySelector('div:first-child');
            const firstChild3 = cards[3].querySelector('div:first-child');
            if (firstChild0) firstChild0.textContent = `${stats.avg_length}字`;
            if (firstChild1) firstChild1.textContent = `${stats.has_experience_pct}%`;
            if (firstChild2) firstChild2.textContent = `${stats.has_question_pct}%`;
            if (firstChild3) firstChild3.textContent = stats.max_likes.toLocaleString();
        }
    }

    // ========== 模式43: 语言分布 ==========

    function renderLanguageDistribution(language) {
        if (!language || !language.distribution || language.distribution.length === 0) {
            showChartNoData('languageDistChart', '语言分布');
            return;
        }
        hideChartNoData('languageDistChart');

        const canvas = document.getElementById('languageDistChart');
        if (!canvas) {
            console.log('[User] 语言分布图 canvas 未找到');
            return;
        }

        // 销毁旧图表
        if (languageDistChart) {
            languageDistChart.destroy();
            languageDistChart = null;
        }

        // 过滤掉占比太小的和无意义的类别
        const data = language.distribution.filter(d =>
            d.percentage > 0.5 && d.code !== 'emoji' && d.code !== 'unknown'
        );

        const colors = {
            'zh-CN': '#06b6d4', 'zh-TW': '#f97316', 'en': '#10b981',
            'ja': '#ec4899', 'ko': '#8b5cf6', 'emoji': '#fbbf24', 'unknown': '#475569'
        };

        const bgColors = data.map(d => (colors[d.code] || '#64748b') + 'cc');
        const borderColors = data.map(d => colors[d.code] || '#64748b');

        languageDistChart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                const item = data[ctx.dataIndex];
                                return `${item.count.toLocaleString()} 条评论 (${item.percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b' },
                        title: { display: true, text: '评论数', color: '#64748b' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#e2e8f0', font: { size: 12 } }
                    }
                }
            },
            plugins: [{
                afterDatasetsDraw: function(chart) {
                    const ctx = chart.ctx;
                    ctx.save();
                    ctx.font = '11px sans-serif';
                    ctx.fillStyle = '#94a3b8';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'middle';

                    chart.data.datasets[0].data.forEach((value, index) => {
                        const meta = chart.getDatasetMeta(0);
                        const bar = meta.data[index];
                        const item = data[index];
                        ctx.fillText(`${item.percentage}%`, bar.x + 6, bar.y);
                    });
                    ctx.restore();
                }
            }]
        });

        cacheChartImage(languageDistChart, 'languageDistChart');

        // 更新统计信息
        const sampleEl = document.getElementById('languageSample');
        if (sampleEl) {
            sampleEl.textContent = `N = ${language.total.toLocaleString()}`;
        }

        console.log('[User] ✓ 语言分布图渲染完成，共', data.length, '种语言');
    }

    // ========== 真实案例渲染 ==========

    function renderRealExamples(examples) {
        // 渲染互动热门视频（模式38区域）
        const hotVideosContainer = document.getElementById('hotVideosExamples');
        if (hotVideosContainer && examples.top_commented_videos?.length) {
            hotVideosContainer.innerHTML = examples.top_commented_videos.map(v => `
                <div style="padding:10px;background:#0f172a;border-radius:6px;margin-bottom:8px;">
                    <div style="color:#e2e8f0;font-size:0.9em;margin-bottom:4px;">
                        <a href="https://youtube.com/watch?v=${v.youtube_id}" target="_blank" style="color:#06b6d4;text-decoration:none;">${v.title}</a>
                    </div>
                    <div style="color:#64748b;font-size:0.8em;">
                        📺 ${v.channel} · 👁 ${(v.views/10000).toFixed(1)}万 · 💬 ${v.comments}条评论
                    </div>
                </div>
            `).join('');
        }

        // 渲染用户问题案例（模式39区域）
        const questionExamplesContainer = document.getElementById('questionExamples');
        if (questionExamplesContainer && examples.question_examples?.length) {
            questionExamplesContainer.innerHTML = examples.question_examples.map(q => `
                <div style="padding:10px;background:#0f172a;border-radius:6px;margin-bottom:8px;">
                    <div style="color:#f59e0b;font-size:0.9em;margin-bottom:4px;">❓ "${q.text}"</div>
                    <div style="color:#64748b;font-size:0.8em;">
                        来自: <a href="https://youtube.com/watch?v=${q.youtube_id}" target="_blank" style="color:#06b6d4;text-decoration:none;">${q.video_title}</a> (${q.channel})
                    </div>
                </div>
            `).join('');
        }

        // 渲染高赞评论案例（模式42区域）
        const highLikedExamplesContainer = document.getElementById('highLikedExamples');
        if (highLikedExamplesContainer && examples.top_liked_comments?.length) {
            highLikedExamplesContainer.innerHTML = examples.top_liked_comments.map(c => `
                <div style="padding:12px;background:#0f172a;border-radius:6px;margin-bottom:10px;border-left:3px solid #10b981;">
                    <div style="color:#e2e8f0;font-size:0.9em;margin-bottom:6px;line-height:1.5;">"${c.text}"</div>
                    <div style="display:flex;justify-content:space-between;color:#64748b;font-size:0.8em;">
                        <span>👍 ${c.likes}赞</span>
                        <span>来自: <a href="https://youtube.com/watch?v=${c.youtube_id}" target="_blank" style="color:#06b6d4;text-decoration:none;">${c.channel}</a></span>
                    </div>
                </div>
            `).join('');
        }
    }

    // ========== 静态结论注册（Fallback） ==========

    function registerStaticUserInsightConclusions() {
        const tabConclusions = window.tabConclusions || getReport().tabConclusions;
        if (!tabConclusions) return;

        // 如果已有动态数据注册的结论，则跳过
        if (tabConclusions.tab8 && tabConclusions.tab8.items.length > 0) {
            console.log('[User] 已有动态结论，跳过静态注册');
            return;
        }

        console.log('[User] 注册静态用户洞察结论...');

        registerPatternConclusion('tab8', '38', '评论热词', '评论热词',
            '高频词：感恩(1,406)、分享(1,319)、謝謝(1,314)。感谢类词汇占主导，说明用户满意度极高。'
        );
        registerPatternConclusion('tab8', '39', '用户问题', '用户问题',
            '用户常见问题集中在"如何操作"、"适用人群"、"效果时长"三类。可针对性创作解答视频满足用户需求。'
        );
        registerPatternConclusion('tab8', '40', '情感分布', '情感分布',
            '正面情感占比超过85%，整体用户反馈非常积极。负面评论主要集中在"效果不明显"，可通过强调正确方法来改善。'
        );
        registerPatternConclusion('tab8', '41', '话题趋势', '话题趋势',
            '养生话题热度持续上升，穴位经络类内容关注度稳定增长。建议持续深耕这些领域。'
        );
        registerPatternConclusion('tab8', '42', '高赞特征', '高赞特征',
            '高赞评论特征：分享个人经历、表达感谢、提出具体问题。建议在视频结尾引导用户分享真实体验。'
        );
    }

    /**
     * 确保 tab1（全局认识）的模式43有fallback
     */
    function ensureTab1Pattern43Fallback(channels) {
        const tabConclusions = window.tabConclusions || getReport().tabConclusions;
        if (!tabConclusions) return;

        const hasPattern43 = tabConclusions.tab1 && tabConclusions.tab1.items.some(item => item.patternId === '43');
        if (hasPattern43) {
            console.log('[User] 模式43已存在于tab1，跳过fallback');
            return;
        }

        console.log('[User] 模式43未注册，使用频道数据推断语言分布...');

        if (channels && channels.length > 0) {
            const countryLangMap = {
                'TW': { name: '繁体中文', code: 'zh-TW' },
                'HK': { name: '繁体中文', code: 'zh-TW' },
                'CN': { name: '简体中文', code: 'zh-CN' },
                'US': { name: '英语', code: 'en' },
                'UK': { name: '英语', code: 'en' },
                'MY': { name: '马来语/中文', code: 'ms' },
                'SG': { name: '英语/中文', code: 'en' }
            };

            const countryCount = {};
            channels.forEach(ch => {
                const country = ch.country || 'Unknown';
                countryCount[country] = (countryCount[country] || 0) + 1;
            });

            const langCount = {};
            Object.entries(countryCount).forEach(([country, count]) => {
                const lang = countryLangMap[country] || { name: '其他', code: 'other' };
                langCount[lang.name] = (langCount[lang.name] || 0) + count;
            });

            const total = channels.length;
            const sortedLangs = Object.entries(langCount)
                .sort((a, b) => b[1] - a[1])
                .map(([name, count]) => ({
                    name,
                    count,
                    percentage: ((count / total) * 100).toFixed(1)
                }));

            if (sortedLangs.length > 0) {
                const topLang = sortedLangs[0];
                const secondLang = sortedLangs[1];
                let langText = `主要用户语言：${topLang.name}（约${topLang.percentage}%）`;
                if (secondLang && parseFloat(secondLang.percentage) > 10) {
                    langText += `，其次是${secondLang.name}（约${secondLang.percentage}%）`;
                }
                langText += '。（基于频道国家分布推断）';

                registerPatternConclusion('tab1', '43', '语言分布', '语言分布', langText, null, 'languageDistChart');
                console.log('[User] ✓ 模式43 fallback注册完成');
                return;
            }
        }

        // 通用 fallback
        registerPatternConclusion('tab1', '43', '语言分布', '语言分布',
            '语言分布数据加载中，请查看「全局认识」→「语言分布」子Tab获取详细信息。',
            null, 'languageDistChart'
        );
        console.log('[User] ✓ 模式43 通用fallback注册完成');
    }

    // ========== 导出 ==========
    exports.userInsightData = userInsightData;
    exports.loadUserInsightData = loadUserInsightData;
    exports.initUserInsightCharts = initUserInsightCharts;
    exports.showNoCommentData = showNoCommentData;
    exports.renderUserInsightData = renderUserInsightData;
    exports.renderHotwordsTable = renderHotwordsTable;
    exports.renderQuestionsChart = renderQuestionsChart;
    exports.renderSentimentBars = renderSentimentBars;
    exports.renderLanguageDistribution = renderLanguageDistribution;
    exports.renderTrendChart = renderTrendChart;
    exports.renderHighLikedStats = renderHighLikedStats;
    exports.renderRealExamples = renderRealExamples;
    exports.registerStaticUserInsightConclusions = registerStaticUserInsightConclusions;
    exports.ensureTab1Pattern43Fallback = ensureTab1Pattern43Fallback;

    // 向后兼容：暴露到全局作用域
    window.loadUserInsightData = loadUserInsightData;
    window.initUserInsightCharts = initUserInsightCharts;
    window.showNoCommentData = showNoCommentData;
    window.renderUserInsightData = renderUserInsightData;
    window.renderHotwordsTable = renderHotwordsTable;
    window.renderQuestionsChart = renderQuestionsChart;
    window.renderSentimentBars = renderSentimentBars;
    window.renderLanguageDistribution = renderLanguageDistribution;
    window.renderTrendChart = renderTrendChart;
    window.renderHighLikedStats = renderHighLikedStats;
    window.renderRealExamples = renderRealExamples;
    window.registerStaticUserInsightConclusions = registerStaticUserInsightConclusions;
    window.ensureTab1Pattern43Fallback = ensureTab1Pattern43Fallback;

})(window.InsightUser);

console.log('[insight-user.js] 模块加载完成');
