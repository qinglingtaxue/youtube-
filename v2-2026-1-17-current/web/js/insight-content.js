/**
 * insight-content.js - 内容创作模块 (Tab4)
 *
 * 包含：
 * - 模式3: 最佳视频时长（renderPattern3, generatePattern3Insight）
 * - 模式4: 内容类型天花板（renderPattern4, renderContentTypeScatter）
 * - 生成内容洞察（generateContentInsight）
 */

// ========== 命名空间 ==========
window.InsightContent = window.InsightContent || {};

(function(exports) {
    'use strict';

    // ========== 依赖获取 ==========
    function getCore() { return window.InsightCore || {}; }
    function getCharts() { return window.InsightCharts || {}; }
    function getReport() { return window.InsightReport || {}; }

    function formatNumber(num) {
        if (getCore().formatNumber) return getCore().formatNumber(num);
        if (!num || num === 0) return '0';
        if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
        if (num >= 10000) return (num / 10000).toFixed(1) + '万';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    function showChartNoData(canvasId, dataType) {
        if (getCore().showChartNoData) getCore().showChartNoData(canvasId, dataType);
        else if (window.showChartNoData) window.showChartNoData(canvasId, dataType);
    }

    function hideChartNoData(canvasId) {
        if (getCore().hideChartNoData) getCore().hideChartNoData(canvasId);
        else if (window.hideChartNoData) window.hideChartNoData(canvasId);
    }

    function cacheChartImage(chart, canvasId) {
        if (getReport().cacheChartImage) getReport().cacheChartImage(chart, canvasId);
        else if (window.cacheChartImage) window.cacheChartImage(chart, canvasId);
    }

    function registerPatternConclusion(...args) {
        if (getReport().registerPatternConclusion) getReport().registerPatternConclusion(...args);
        else if (window.registerPatternConclusion) window.registerPatternConclusion(...args);
    }

    function updateInsight(insightId, content, action) {
        if (getCharts().updateInsight) getCharts().updateInsight(insightId, content, action);
        else if (window.updateInsight) window.updateInsight(insightId, content, action);
    }

    function renderScatter(canvasId, data, config) {
        if (getCharts().renderScatter) return getCharts().renderScatter(canvasId, data, config);
        else if (window.renderScatter) return window.renderScatter(canvasId, data, config);
        return null;
    }

    // ========== 图表实例 ==========
    let contentTypeScatterChart = null;

    // ========== 模式3: 最佳视频时长 ==========

    /**
     * 渲染模式3：时长与播放量关系
     */
    function renderPattern3(videos) {
        if (!videos || videos.length === 0) return;

        const maxPoints = 1500;
        let sampleVideos = videos.length > maxPoints
            ? videos.sort(() => Math.random() - 0.5).slice(0, maxPoints)
            : videos;

        const data = sampleVideos
            .map(v => ({
                x: (v.duration || 0) / 60,
                y: v.view_count || 0,
                label: v.title
            }))
            .filter(d => d.x > 0 && d.x < 120);

        renderScatter('durationScatterChart', data, {
            xLabel: '时长（分钟）',
            yLabel: '播放量',
            yScale: 'logarithmic',
            tooltipFormatter: (d) => [
                `时长: ${d.x.toFixed(1)} 分钟`,
                `播放: ${formatNumber(d.y)}`,
                d.label ? d.label.substring(0, 35) + '...' : ''
            ]
        });

        generatePattern3Insight(videos);
    }

    /**
     * 模式3：智能解读生成
     */
    function generatePattern3Insight(videos) {
        const groups = {
            '0-3分钟': [],
            '3-10分钟': [],
            '10-30分钟': [],
            '30分钟+': []
        };

        videos.forEach(v => {
            const mins = (v.duration || 0) / 60;
            if (mins < 3) groups['0-3分钟'].push(v);
            else if (mins < 10) groups['3-10分钟'].push(v);
            else if (mins < 30) groups['10-30分钟'].push(v);
            else groups['30分钟+'].push(v);
        });

        let bestGroup = null, bestMedian = 0;
        const stats = {};

        Object.entries(groups).forEach(([key, vids]) => {
            if (vids.length > 0) {
                const views = vids.map(v => v.view_count || 0).sort((a, b) => a - b);
                const median = views[Math.floor(views.length / 2)];
                stats[key] = { count: vids.length, median };
                if (median > bestMedian) {
                    bestMedian = median;
                    bestGroup = key;
                }
            }
        });

        const worstEntry = Object.entries(stats).reduce((a, b) =>
            b[1].median < a[1].median ? b : a
        );

        const ratio = (bestMedian / worstEntry[1].median).toFixed(1);

        const content = `<strong>${bestGroup}</strong> 的视频播放量中位数最高（<span class="highlight">${formatNumber(bestMedian)}</span>），是 ${worstEntry[0]} 的 <strong>${ratio}倍</strong>。共分析 <strong>${videos.length}</strong> 个视频。`;
        const action = `建议优先制作 ${bestGroup} 的内容，成功概率更高。`;

        updateInsight('durationScatterInsight', content, action);

        const conclusionEl = document.getElementById('durationConclusionText');
        if (conclusionEl) {
            conclusionEl.innerHTML = `<strong>${bestGroup}播放量最高</strong>（中位数${formatNumber(bestMedian)}），是最差时长段的${ratio}倍`;
        }

        registerPatternConclusion('tab4', '3', '最佳视频时长',
            '最佳视频时长',
            `${bestGroup}的视频播放量中位数最高（${formatNumber(bestMedian)}），是${worstEntry[0]}的${ratio}倍。建议优先制作${bestGroup}的内容。`,
            null,
            'durationScatterChart'
        );
    }

    // ========== 模式4: 内容类型天花板 ==========

    /**
     * 渲染模式4：内容类型天花板分析
     */
    function renderPattern4(videos) {
        if (!videos || videos.length === 0) {
            showChartNoData('contentTypeScatterChart', '视频');
            return;
        }
        hideChartNoData('contentTypeScatterChart');

        const keyword = new URLSearchParams(window.location.search).get('keyword') || '';

        // 养生领域专用分类
        const healthKeywords = {
            '功法养生': ['八段锦', '太极', '太極', '气功', '氣功', '站桩', '五禽戏', '易筋经', '瑜伽', '冥想', '打坐', '呼吸法', '导引', '平甩功', '保健操', '养生操', '甩手', '拉筋', '伸展'],
            '食疗养生': ['食疗', '食療', '食补', '药膳', '藥膳', '养生茶', '養生茶', '养生汤', '豆浆', '豆漿', '枸杞', '黑豆', '生姜', '蜂蜜', '红枣', '食谱', '食譜', '吃什么', '补气', '补血', '滋阴', '壮阳', '炖汤'],
            '穴位经络': ['穴位', '按摩', '艾灸', '刮痧', '经络', '經絡', '推拿', '拍打', '敲打', '疏通', '足三里', '合谷', '涌泉', '龙筋', 'spa', 'massage'],
            '器官保健': ['眼睛', '護眼', '肝', '养肝', '養肝', '肾', '腎', '补肾', '補腎', '心脏', '心臟', '肺', '脾', '胃', '血管', '血栓', '胆固醇', '膽固醇', '脊椎', '頸椎', '颈椎'],
            '中医调理': ['中医', '中醫', '阴阳', '陰陽', '五行', '脏腑', '体质', '體質', '湿气', '濕氣', '寒气', '上火', '肝火', '肾虚', '腎虛', '脾虚', '气血', '氣血', '排毒', '調理'],
            '睡眠养生': ['睡眠', '失眠', '助眠', '睡前', '入睡', '安神', '改善睡眠', '抗失智'],
            '疾病调理': ['高血压', '高血壓', '糖尿病', '便秘', '排便', '白内障', '白內障', '腎臟病', '心梗', '脑梗', '腦梗']
        };

        // 通用分类
        const genericKeywords = {
            '教程教学': ['教程', '教学', '教你', '怎么', '如何', '方法', '技巧', '入门', '学习', '新手'],
            '知识科普': ['讲解', '解说', '解析', '原理', '科普', '揭秘', '真相', '为什么', '什么是'],
            '实战演示': ['实战', '实操', '演示', '案例', '效果', '对比', '测试', '体验', '试用'],
            '故事分享': ['故事', '经历', '分享', '记录', 'vlog', '日常', '我的', '亲身'],
            '评测推荐': ['评测', '推荐', '测评', '好物', '必买', '种草', '盘点', 'top']
        };

        const isHealthTopic = ['养生', '健康', '中医', '穴位', '食疗', '气功', '太极', '八段锦', '睡眠', '失眠'].some(k => keyword.includes(k));
        const typeKeywords = isHealthTopic ? healthKeywords : genericKeywords;

        const typeStats = {};
        Object.keys(typeKeywords).forEach(type => {
            typeStats[type] = { videos: [], totalViews: 0, maxViews: 0 };
        });
        typeStats['其他'] = { videos: [], totalViews: 0, maxViews: 0 };

        videos.forEach(v => {
            const title = (v.title || '').toLowerCase();
            let matched = false;
            for (const [type, keywords] of Object.entries(typeKeywords)) {
                if (keywords.some(kw => title.includes(kw))) {
                    typeStats[type].videos.push(v);
                    typeStats[type].totalViews += v.view_count || 0;
                    typeStats[type].maxViews = Math.max(typeStats[type].maxViews, v.view_count || 0);
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                typeStats['其他'].videos.push(v);
                typeStats['其他'].totalViews += v.view_count || 0;
                typeStats['其他'].maxViews = Math.max(typeStats['其他'].maxViews, v.view_count || 0);
            }
        });

        const chartData = Object.entries(typeStats)
            .filter(([_, stats]) => stats.videos.length >= 5)
            .map(([type, stats]) => ({
                label: type,
                value: stats.videos.length > 0 ? Math.round(stats.totalViews / stats.videos.length) : 0,
                count: stats.videos.length,
                max: stats.maxViews
            }))
            .sort((a, b) => b.value - a.value);

        console.log('[Content] 模式4 - 内容类型统计:', chartData.length, '个类型');

        // 渲染散点图
        renderContentTypeScatter(videos, typeStats, chartData);

        // 更新样本量
        const sampleEl = document.getElementById('contentTypeSample');
        if (sampleEl) sampleEl.textContent = `N = ${videos.length}`;

        // 生成结论
        if (chartData.length > 0) {
            const best = chartData[0];
            const worst = chartData[chartData.length - 1];
            const ratio = worst.value > 0 ? (best.value / worst.value).toFixed(1) : '∞';

            // 更新数据解读（DOM 元素）
            const insightEl = document.getElementById('viewTrendInsight');
            if (insightEl) {
                const contentEl = insightEl.querySelector('.chart-insight-content');
                if (contentEl) {
                    const top3 = chartData.slice(0, 3);
                    contentEl.innerHTML = `
                        共分析 <strong>${videos.length}</strong> 个视频，按标题关键词分为 <strong>${chartData.length}</strong> 个内容类型。<br>
                        Top 3 类型：${top3.map(t => `<strong>${t.label}</strong>(${t.count}个，均播${formatNumber(t.value)})`).join('、')}。<br>
                        「${best.label}」均播最高，是「${worst.label}」的 ${ratio} 倍。
                    `;
                }
            }

            // 更新结论
            const conclusionEl = document.getElementById('viewTrendConclusion');
            if (conclusionEl) {
                conclusionEl.innerHTML = `「<strong>${best.label}</strong>」类内容均播最高（${formatNumber(best.value)}），天花板达 ${formatNumber(best.max)}。建议优先布局此类内容。`;
            }

            // 更新行动建议
            const actionsEl = document.getElementById('viewTrendActions');
            if (actionsEl) {
                const actions = [];
                actions.push(`<span class="pattern-action do">✅ 优先制作「${best.label}」类内容</span>`);
                if (chartData.length > 1) {
                    actions.push(`<span class="pattern-action do">✅ 次选「${chartData[1].label}」（均播${formatNumber(chartData[1].value)}）</span>`);
                }
                if (worst.value < best.value * 0.3) {
                    actions.push(`<span class="pattern-action avoid">⚠️ 避免「${worst.label}」类（均播仅${formatNumber(worst.value)}）</span>`);
                }
                actionsEl.innerHTML = actions.join('');
            }

            registerPatternConclusion('tab1', '4', '内容类型天花板',
                '内容类型天花板',
                `「${best.label}」均播最高（${formatNumber(best.value)}），天花板${formatNumber(best.max)}，是「${worst.label}」的${ratio}倍。建议优先布局${best.label}内容。`,
                null,
                'contentTypeScatterChart'
            );
        }
    }

    /**
     * 渲染内容类型散点图
     */
    function renderContentTypeScatter(videos, typeStats, chartData) {
        const canvas = document.getElementById('contentTypeScatterChart');
        if (!canvas) return;

        if (contentTypeScatterChart) {
            contentTypeScatterChart.destroy();
            contentTypeScatterChart = null;
        }

        const colorPalette = ['#06b6d4', '#f97316', '#a855f7', '#10b981', '#f43f5e', '#eab308', '#3b82f6', '#ec4899'];
        const typeColors = {};
        chartData.forEach((d, i) => typeColors[d.label] = colorPalette[i % colorPalette.length]);

        // 构建数据集
        const datasets = chartData.slice(0, 8).map((typeData, i) => {
            const stats = typeStats[typeData.label];
            if (!stats) return null;

            const points = stats.videos.slice(0, 100).map(v => ({
                x: new Date(v.published_at || Date.now()).getTime(),
                y: v.view_count || 0,
                title: v.title,
                type: typeData.label
            })).filter(p => p.y > 0);

            return {
                label: typeData.label,
                data: points,
                backgroundColor: typeColors[typeData.label] + '80',
                borderColor: typeColors[typeData.label],
                borderWidth: 1,
                pointRadius: 4,
                pointHoverRadius: 6
            };
        }).filter(Boolean);

        contentTypeScatterChart = new Chart(canvas, {
            type: 'scatter',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 8, padding: 6, usePointStyle: true }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const p = ctx.raw;
                                return [p.type, `播放: ${formatNumber(p.y)}`, p.title?.substring(0, 30) + '...'];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: { unit: 'month', displayFormats: { month: 'yy/MM' } },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b' }
                    },
                    y: {
                        type: 'logarithmic',
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b', callback: (v) => formatNumber(v) }
                    }
                }
            }
        });

        cacheChartImage(contentTypeScatterChart, 'contentTypeScatterChart');
        console.log('[Content] ✓ 内容类型散点图渲染完成');
    }

    // ========== 内容洞察生成 ==========

    function generateContentInsight(data) {
        const videos = data.videos || [];
        if (videos.length === 0) return '暂无数据';

        const durations = data.duration_distribution || {};
        const durationLabels = { short: '短视频(<5分钟)', medium: '中等(5-15分钟)', long: '长视频(>15分钟)' };

        const durationStats = Object.entries(durations)
            .filter(([k]) => k !== 'unknown')
            .map(([key, val]) => {
                if (typeof val === 'object') {
                    return { key, count: val.count || 0, avg_views: val.avg_views || 0 };
                }
                return { key, count: val || 0, avg_views: 0 };
            })
            .sort((a, b) => b.avg_views - a.avg_views);

        let durationTip = '';
        if (durationStats.length > 0) {
            const best = durationStats[0];
            const label = durationLabels[best.key] || best.key;
            const avgViews = best.avg_views > 10000 ? `${(best.avg_views / 10000).toFixed(1)}万` : best.avg_views.toLocaleString();
            durationTip = `<strong>${label}</strong>均播最高(${avgViews})`;
        }

        const combos = data.best_duration_category_combos || [];
        let comboTip = '';
        if (combos.length > 0) {
            const best = combos[0];
            const dType = durationLabels[best.duration_type] || best.duration_type;
            const avgViews = best.avg_views > 10000 ? `${(best.avg_views / 10000).toFixed(1)}万` : best.avg_views.toLocaleString();
            comboTip = `，<strong>${best.category}+${dType}</strong>是最强组合(均播${avgViews})`;
        }

        return `${durationTip}${comboTip}。`;
    }

    // ========== 导出 ==========
    exports.renderPattern3 = renderPattern3;
    exports.renderPattern4 = renderPattern4;
    exports.generatePattern3Insight = generatePattern3Insight;
    exports.generateContentInsight = generateContentInsight;
    exports.renderContentTypeScatter = renderContentTypeScatter;

    // 向后兼容
    window.renderPattern3 = renderPattern3;
    window.renderPattern4 = renderPattern4;
    window.generatePattern3Insight = generatePattern3Insight;
    window.generateContentInsight = generateContentInsight;

})(window.InsightContent);

console.log('[insight-content.js] 模块加载完成');
