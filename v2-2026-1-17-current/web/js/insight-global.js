/**
 * insight-global.js - 全局认识模块 (Tab1)
 *
 * 包含：
 * - 领域概览（renderOverview）
 * - 模式4: 内容类型天花板（renderPattern4）
 * - 模式12: 频道竞争格局（renderPattern12, renderSubscriberDistribution）
 * - 模式23: 频道国家分布（renderPattern23）
 * - 生成全局洞察（generateGlobalInsight）
 */

// ========== 命名空间 ==========
window.InsightGlobal = window.InsightGlobal || {};

(function(exports) {
    'use strict';

    // ========== 依赖获取 ==========
    function getCore() { return window.InsightCore || {}; }
    function getCharts() { return window.InsightCharts || {}; }
    function getReport() { return window.InsightReport || {}; }

    // 向后兼容工具函数
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

    // ========== 图表实例 ==========
    let overviewScatterChart = null;
    let countryBarChart = null;
    let subsDistScatter = null;

    // ========== 国家名称映射 ==========
    const countryShortNames = {
        'Hong Kong': '香港', 'Taiwan': '台湾', 'United States': '美国',
        'Singapore': '新加坡', 'Malaysia': '马来西亚', 'Japan': '日本',
        'South Korea': '韩国', 'China': '中国', 'Australia': '澳大利亚',
        'Canada': '加拿大', 'United Kingdom': '英国', 'Germany': '德国',
        'France': '法国', 'Indonesia': '印尼', 'Thailand': '泰国',
        'Vietnam': '越南', 'Philippines': '菲律宾', 'India': '印度',
        'Brazil': '巴西', 'Mexico': '墨西哥', 'Russia': '俄罗斯'
    };

    // ========== 领域概览 ==========

    /**
     * 渲染领域概览（全局认识的第一个子Tab）
     */
    function renderOverview(data) {
        // 1. 更新数字卡片
        const totalVideos = data.total_videos || data.videos?.length || 0;
        const totalChannels = data.total_channels || data.channels?.length || 0;
        const totalViews = data.videos?.reduce((sum, v) => sum + (v.view_count || 0), 0) || 0;
        const avgViews = totalVideos > 0 ? Math.round(totalViews / totalVideos) : 0;

        const videosEl = document.getElementById('overviewTotalVideos');
        if (videosEl) videosEl.textContent = formatNumber(totalVideos);

        const growthEl = document.getElementById('overviewVideoGrowth');
        if (growthEl && data.publishing_trend && data.publishing_trend.length >= 6) {
            const trend = data.publishing_trend;
            const recent = trend.slice(-3).reduce((sum, m) => sum + (m.count || 0), 0);
            const older = trend.slice(-6, -3).reduce((sum, m) => sum + (m.count || 0), 0);
            if (older > 0) {
                const rate = ((recent - older) / older * 100).toFixed(0);
                growthEl.textContent = `近3月${rate >= 0 ? '+' : ''}${rate}%`;
                growthEl.style.color = rate >= 0 ? '#10b981' : '#ef4444';
            }
        }

        const channelsEl = document.getElementById('overviewTotalChannels');
        if (channelsEl) channelsEl.textContent = formatNumber(totalChannels);

        const viewsEl = document.getElementById('overviewTotalViews');
        if (viewsEl) viewsEl.textContent = formatNumber(totalViews);

        const avgViewsEl = document.getElementById('overviewAvgViews');
        if (avgViewsEl) avgViewsEl.textContent = `(均播${formatNumber(avgViews)})`;

        // 国家统计
        if (data.channels) {
            const countryCounts = {};
            data.channels.forEach(c => {
                if (c.country && c.country !== 'Unknown') {
                    countryCounts[c.country] = (countryCounts[c.country] || 0) + 1;
                }
            });
            const countryCount = Object.keys(countryCounts).length;
            const countriesEl = document.getElementById('overviewCountries');
            const topCountryEl = document.getElementById('overviewTopCountry');
            if (countriesEl) countriesEl.textContent = countryCount || '--';
            if (topCountryEl && countryCount > 0) {
                const top = Object.entries(countryCounts).sort((a, b) => b[1] - a[1])[0];
                const shortName = countryShortNames[top[0]] || top[0];
                topCountryEl.textContent = `(${shortName})`;
            }
        }

        // 2. 渲染散点图
        renderOverviewScatterChart(data);

        // 3. 更新数据说明
        const dataRangeEl = document.getElementById('overviewDataRange');
        if (dataRangeEl) {
            const timeRange = data.data_time_range || {};
            dataRangeEl.textContent = `${timeRange.published_earliest || '?'} ~ ${timeRange.published_latest || '?'}`;
        }

        // 4. 生成洞察和结论
        generateOverviewInsight(data);
    }

    /**
     * 渲染领域概览散点图
     */
    function renderOverviewScatterChart(data) {
        const scatterCanvas = document.getElementById('overviewScatterChart');
        if (!scatterCanvas || !data.videos || data.videos.length === 0) {
            showChartNoData('overviewScatterChart', '视频');
            return;
        }

        // 关键检查：Chart 库必须已加载
        if (typeof Chart === 'undefined') {
            console.error('[renderOverviewScatterChart] Chart.js 库未加载，请检查 chart.min.js 脚本');
            showChartNoData('overviewScatterChart', '图表库');
            return;
        }

        hideChartNoData('overviewScatterChart');

        if (overviewScatterChart) {
            overviewScatterChart.destroy();
            overviewScatterChart = null;
        }

        // 统计话题频率
        const tagFreq = {};
        const titleKeywords = ['八段锦', '太极', '气功', '穴位', '食疗', '养生', '中医', '经络', '按摩', '冥想', '健康', '长寿', '減肥', '瑜伽'];

        data.videos.forEach(v => {
            if (v.tags && Array.isArray(v.tags)) {
                v.tags.forEach(tag => {
                    if (tag && tag.length > 1 && tag.length < 10) {
                        tagFreq[tag] = (tagFreq[tag] || 0) + 1;
                    }
                });
            }
            titleKeywords.forEach(kw => {
                if (v.title && v.title.includes(kw)) {
                    tagFreq[kw] = (tagFreq[kw] || 0) + 1;
                }
            });
        });

        const topTopics = Object.entries(tagFreq)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([tag]) => tag);

        const colorPalette = ['#06b6d4', '#f97316', '#a855f7', '#10b981', '#f43f5e', '#eab308', '#3b82f6', '#ec4899', '#14b8a6', '#64748b'];
        const topicColors = {};
        topTopics.forEach((t, i) => topicColors[t] = colorPalette[i % colorPalette.length]);

        // 动态选择聚合粒度
        const dates = data.videos.map(v => v.published_at).filter(Boolean).sort();
        const firstDate = new Date(dates[0]);
        const lastDate = new Date(dates[dates.length - 1]);
        const daySpan = Math.ceil((lastDate - firstDate) / (1000 * 60 * 60 * 24));

        let getTimeKey, formatLabel;
        if (daySpan < 45) {
            getTimeKey = (d) => d.slice(0, 10);
            formatLabel = (k) => k.slice(5).replace('-', '/');
        } else if (daySpan < 120) {
            getTimeKey = (d) => {
                const date = new Date(d);
                const year = date.getFullYear();
                const week = Math.ceil((date - new Date(year, 0, 1)) / (7 * 24 * 60 * 60 * 1000));
                return `${year}W${String(week).padStart(2, '0')}`;
            };
            formatLabel = (k) => k.replace('20', '').replace('W', '周');
        } else {
            getTimeKey = (d) => d.slice(0, 7);
            formatLabel = (k) => k.slice(2).replace('-', '/');
        }

        // 聚合数据
        const timeTopicData = {};
        data.videos.forEach(v => {
            if (!v.published_at) return;
            const timeKey = getTimeKey(v.published_at);
            let topics = [];
            if (v.tags && Array.isArray(v.tags)) {
                topics = v.tags.filter(t => topTopics.includes(t));
            }
            if (topics.length === 0) {
                for (const kw of topTopics) {
                    if (v.title && v.title.includes(kw)) {
                        topics.push(kw);
                        break;
                    }
                }
            }
            if (topics.length === 0) topics = ['其他'];

            if (!timeTopicData[timeKey]) timeTopicData[timeKey] = {};
            topics.forEach(topic => {
                if (!timeTopicData[timeKey][topic]) {
                    timeTopicData[timeKey][topic] = { views: 0, count: 0 };
                }
                timeTopicData[timeKey][topic].views += v.view_count || 0;
                timeTopicData[timeKey][topic].count += 1;
            });
        });

        const timePoints = Object.keys(timeTopicData).sort().slice(-30);
        const timeLabels = timePoints.map(formatLabel);
        const datasets = [];

        topTopics.forEach(topic => {
            const points = [];
            const pointSizes = [];
            timePoints.forEach((t) => {
                const topicData = timeTopicData[t]?.[topic];
                if (topicData && topicData.count > 0) {
                    const size = Math.min(Math.sqrt(topicData.count) * 2 + 3, 18);
                    points.push({
                        x: formatLabel(t),
                        y: topicData.views,
                        timeKey: t,
                        timeLabel: formatLabel(t),
                        topic: topic,
                        count: topicData.count,
                        avgViews: Math.round(topicData.views / topicData.count)
                    });
                    pointSizes.push(size);
                }
            });
            if (points.length > 0) {
                datasets.push({
                    label: topic,
                    data: points,
                    backgroundColor: topicColors[topic] + '99',
                    borderColor: topicColors[topic],
                    borderWidth: 1.5,
                    showLine: true,
                    tension: 0.3,
                    fill: false,
                    pointRadius: pointSizes,
                    pointHoverRadius: pointSizes.map(s => s + 3)
                });
            }
        });

        const chartTimeLabels = [...timeLabels];

        overviewScatterChart = new Chart(scatterCanvas, {
            type: 'scatter',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 10, padding: 8, usePointStyle: true }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const p = ctx.raw;
                                return [`${p.topic} (${p.timeLabel})`, `播放量: ${formatNumber(p.y)}`, `视频数: ${p.count}`, `均播: ${formatNumber(p.avgViews)}`];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: chartTimeLabels,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b', autoSkip: true, maxTicksLimit: 12, maxRotation: 45 }
                    },
                    y: {
                        type: 'logarithmic',
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b', callback: (v) => formatNumber(v) }
                    }
                }
            }
        });

        cacheChartImage(overviewScatterChart, 'overviewScatterChart');
        console.log('[Global] ✓ 领域概览散点图渲染完成');
    }

    /**
     * 生成领域概览洞察
     */
    function generateOverviewInsight(data) {
        const videos = data.videos || [];
        const channels = data.channels || [];
        const sumViews = videos.reduce((s, v) => s + (v.view_count || 0), 0);
        const avgViewsForInsight = videos.length > 0 ? Math.round(sumViews / videos.length) : 0;

        const sortedVideos = [...videos].sort((a, b) => (b.view_count || 0) - (a.view_count || 0));
        const maxViews = sortedVideos[0] ? sortedVideos[0].view_count : 0;

        const viewsArray = videos.map(v => v.view_count || 0).filter(v => v > 0);
        const medianViews = viewsArray.length > 0 ?
            viewsArray.sort((a, b) => a - b)[Math.floor(viewsArray.length / 2)] : 0;

        let marketSize = '中等规模';
        let marketColor = '#eab308';
        if (avgViewsForInsight >= 100000) {
            marketSize = '大市场';
            marketColor = '#10b981';
        } else if (avgViewsForInsight < 10000) {
            marketSize = '小众市场';
            marketColor = '#f97316';
        }

        updateInsight('overviewInsight',
            `共<strong>${videos.length}</strong>个视频、<strong>${channels.length}</strong>个频道。总播放<strong>${formatNumber(sumViews)}</strong>，均播<strong>${formatNumber(avgViewsForInsight)}</strong>，中位数<strong>${formatNumber(medianViews)}</strong>。最高播放<strong>${formatNumber(maxViews)}</strong>。`,
            `散点图展示不同话题在不同时间段的播放量分布。点越大表示该时段该话题的总播放量越高。`
        );

        const conclusionEl = document.getElementById('overviewConclusion');
        const actionsEl = document.getElementById('overviewActions');

        if (conclusionEl) {
            const top10Views = sortedVideos.slice(0, 10).reduce((s, v) => s + (v.view_count || 0), 0);
            const top10Percent = sumViews > 0 ? ((top10Views / sumViews) * 100).toFixed(0) : 0;

            let conclusion = `该领域属于<strong style="color:${marketColor}">${marketSize}</strong>。`;
            conclusion += `均播<strong>${formatNumber(avgViewsForInsight)}</strong>，最高播放可达<strong>${formatNumber(maxViews)}</strong>。`;
            conclusion += top10Percent > 50 ? `头部集中度高（Top10占${top10Percent}%），需要爆款策略。` : `流量分布较均匀，持续产出有机会积累。`;
            conclusionEl.innerHTML = conclusion;
        }

        if (actionsEl) {
            let actions = '';
            if (marketSize === '大市场') {
                actions = `<span class="pattern-action do">✅ 市场空间大，值得投入</span><span class="pattern-action do">✅ 分析头部视频的成功要素</span><span class="pattern-action avoid">⚠️ 注意竞争激烈，需差异化</span>`;
            } else if (marketSize === '小众市场') {
                actions = `<span class="pattern-action do">✅ 竞争较小，容易出头</span><span class="pattern-action do">✅ 深耕垂直领域建立壁垒</span><span class="pattern-action avoid">⚠️ 天花板有限，管理预期</span>`;
            } else {
                actions = `<span class="pattern-action do">✅ 市场适中，平衡机会与竞争</span><span class="pattern-action do">✅ 找准细分定位持续产出</span><span class="pattern-action avoid">⚠️ 关注头部动态，学习借鉴</span>`;
            }
            actionsEl.innerHTML = actions;
        }

        // 注册结论
        const top10Views = sortedVideos.slice(0, 10).reduce((s, v) => s + (v.view_count || 0), 0);
        const top10Percent = sumViews > 0 ? ((top10Views / sumViews) * 100).toFixed(0) : 0;

        registerPatternConclusion('tab1', '0', '领域概览',
            '话题播放量分布',
            `该领域属于${marketSize}。共${videos.length}个视频、${channels.length}个频道，总播放${formatNumber(sumViews)}，均播${formatNumber(avgViewsForInsight)}。头部集中度${top10Percent > 50 ? '较高' : '较低'}（Top10占${top10Percent}%）。`,
            null,
            'overviewScatterChart'
        );
    }

    // ========== 模式23: 频道国家分布 ==========

    function renderPattern23(channels, videos) {
        if (!channels || channels.length === 0) {
            showChartNoData('countryBarChart', '频道');
            return;
        }
        hideChartNoData('countryBarChart');

        // 去重
        const seenIds = new Set();
        const uniqueChannels = channels.filter(c => {
            const id = c.channel_id || c.channel_name || c.title;
            if (seenIds.has(id)) return false;
            seenIds.add(id);
            return true;
        });

        // 统计各国家
        const countryStats = {};
        uniqueChannels.forEach(c => {
            const country = c.country && c.country !== 'Unknown' ? c.country : '未知';
            if (!countryStats[country]) {
                countryStats[country] = { channels: [], totalViews: 0, totalSubs: 0 };
            }
            countryStats[country].channels.push(c);
            countryStats[country].totalViews += c.total_views || 0;
            countryStats[country].totalSubs += c.subscriber_count || 0;
        });

        const sortedCountries = Object.entries(countryStats)
            .filter(([country]) => country !== '未知')
            .sort((a, b) => b[1].channels.length - a[1].channels.length);

        const displayCountries = sortedCountries.slice(0, 12);
        const colorPalette = ['#06b6d4', '#f97316', '#a855f7', '#10b981', '#f43f5e', '#eab308', '#3b82f6', '#ec4899', '#14b8a6', '#8b5cf6', '#ef4444', '#84cc16'];

        // 更新统计
        const validCountries = sortedCountries.length;
        const totalChannels = uniqueChannels.filter(c => c.country && c.country !== 'Unknown').length;
        const topCountry = sortedCountries[0] ? sortedCountries[0][0] : '--';
        const shortTopCountry = countryShortNames[topCountry] || topCountry;

        const countryCountEl = document.getElementById('countryCount');
        const channelCountEl = document.getElementById('countryChannelCount');
        const topCountryEl = document.getElementById('topCountryName');
        const sampleEl = document.getElementById('countrySample');

        if (countryCountEl) countryCountEl.textContent = validCountries;
        if (channelCountEl) channelCountEl.textContent = totalChannels;
        if (topCountryEl) topCountryEl.textContent = shortTopCountry;
        if (sampleEl) sampleEl.textContent = `N = ${uniqueChannels.length}`;

        // 渲染条形图
        const barCanvas = document.getElementById('countryBarChart');
        if (barCanvas) {
            // 关键检查：Chart 库必须已加载
            if (typeof Chart === 'undefined') {
                console.error('[renderPattern23] Chart.js 库未加载');
                return;
            }

            if (countryBarChart) {
                countryBarChart.destroy();
                countryBarChart = null;
            }

            const labels = displayCountries.map(([country]) => countryShortNames[country] || country);
            const values = displayCountries.map(([_, stats]) => stats.channels.length);
            const colors = displayCountries.map((_, i) => colorPalette[i % colorPalette.length]);

            countryBarChart = new Chart(barCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors.map(c => c + 'cc'),
                        borderColor: colors,
                        borderWidth: 1, borderRadius: 4, barPercentage: 0.7, categoryPercentage: 0.85
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
                                label: (ctx) => {
                                    const count = ctx.raw;
                                    const percent = ((count / totalChannels) * 100).toFixed(1);
                                    return `${count} 个频道 (${percent}%)`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' }, title: { display: true, text: '频道数量', color: '#64748b' } },
                        y: { grid: { display: false }, ticks: { color: '#e2e8f0', font: { size: 12 } } }
                    }
                },
                plugins: [{
                    afterDatasetsDraw: (chart) => {
                        const ctx = chart.ctx;
                        ctx.save();
                        ctx.font = '11px sans-serif';
                        ctx.fillStyle = '#94a3b8';
                        ctx.textAlign = 'left';
                        ctx.textBaseline = 'middle';
                        chart.data.datasets[0].data.forEach((value, index) => {
                            const meta = chart.getDatasetMeta(0);
                            const bar = meta.data[index];
                            const percent = ((value / totalChannels) * 100).toFixed(0);
                            ctx.fillText(`${value} (${percent}%)`, bar.x + 6, bar.y);
                        });
                        ctx.restore();
                    }
                }]
            });

            cacheChartImage(countryBarChart, 'countryBarChart');
        }

        // 生成洞察
        if (sortedCountries.length > 0) {
            const [topName, topData] = sortedCountries[0];
            const topShort = countryShortNames[topName] || topName;
            const topPercent = (topData.channels.length / totalChannels * 100).toFixed(0);

            // 生成 Top 3 国家描述
            const top3Desc = sortedCountries.slice(0, 3).map(([name, stats]) => {
                const shortName = countryShortNames[name] || name;
                return `${shortName}(${stats.channels.length}个)`;
            }).join('、');

            const insightText = `覆盖 <strong>${validCountries}</strong> 个国家/地区，共 <strong>${totalChannels}</strong> 个频道。${topShort}占比最高（${topPercent}%），Top 3 为：${top3Desc}。`;

            // 更新页面元素
            const insightEl = document.getElementById('countryDistInsight');
            if (insightEl) {
                const contentEl = insightEl.querySelector('.chart-insight-content');
                if (contentEl) contentEl.innerHTML = insightText;
            }

            registerPatternConclusion('tab1', '23', '频道国家分布',
                '频道国家分布',
                `${validCountries}个国家/地区的${totalChannels}个频道中，${topShort}占比最高（${topPercent}%，${topData.channels.length}个频道）。了解地区分布有助于发现跨区域内容机会。`,
                null,
                { sourceCanvasId: 'countryBarChart' }
            );
        }

        console.log('[Global] ✓ 频道国家分布渲染完成');
    }

    // ========== 模式12: 频道竞争格局 ==========

    function renderSubscriberDistribution(channels) {
        if (!channels || channels.length === 0) {
            showChartNoData('subsDistScatter', '频道');
            return;
        }
        hideChartNoData('subsDistScatter');

        // 去重
        const seenIds = new Set();
        const validChannels = channels.filter(c => {
            if (c.subscriber_count == null || c.subscriber_count <= 0) return false;
            const id = c.channel_id || c.channel_name || c.title;
            if (seenIds.has(id)) return false;
            seenIds.add(id);
            return true;
        });

        const allSubs = validChannels.map(c => c.subscriber_count).sort((a, b) => a - b);
        const median = allSubs.length > 0 ? allSubs[Math.floor(allSubs.length / 2)] : 0;
        const maxSubs = allSubs.length > 0 ? allSubs[allSubs.length - 1] : 0;

        // 更新统计
        const channelCountEl = document.getElementById('subsDistChannelCount');
        const medianEl = document.getElementById('subsDistMedian');
        const maxEl = document.getElementById('subsDistMax');

        if (channelCountEl) channelCountEl.textContent = validChannels.length;
        if (medianEl) medianEl.textContent = formatNumber(median);
        if (maxEl) maxEl.textContent = formatNumber(maxSubs);

        function getColor(subs) {
            if (subs >= 1000000) return '#ef4444';
            if (subs >= 100000) return '#f97316';
            if (subs >= 10000) return '#10b981';
            return '#06b6d4';
        }

        const scatterData = validChannels.map((c, idx) => ({
            x: idx + 1,
            y: c.subscriber_count,
            channelName: c.channel_name || c.title || '未知频道',
            channelId: c.channel_id
        }));

        const canvas = document.getElementById('subsDistScatter');
        if (canvas) {
            // 关键检查：Chart 库必须已加载
            if (typeof Chart === 'undefined') {
                console.error('[renderSubscriberDistribution] Chart.js 库未加载');
                return;
            }

            if (subsDistScatter) {
                subsDistScatter.destroy();
                subsDistScatter = null;
            }

            subsDistScatter = new Chart(canvas, {
                type: 'scatter',
                data: {
                    datasets: [{
                        data: scatterData,
                        backgroundColor: scatterData.map(d => getColor(d.y) + '99'),
                        borderColor: scatterData.map(d => getColor(d.y)),
                        borderWidth: 1, pointRadius: 5, pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    const d = ctx.raw;
                                    return [`${d.channelName}`, `订阅: ${formatNumber(d.y)}`];
                                }
                            }
                        }
                    },
                    scales: {
                        x: { display: false },
                        y: {
                            type: 'logarithmic',
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#64748b', callback: (v) => formatNumber(v) },
                            title: { display: true, text: '订阅数', color: '#64748b' }
                        }
                    }
                }
            });

            cacheChartImage(subsDistScatter, 'subsDistScatter');
        }

        console.log('[Global] ✓ 频道竞争格局渲染完成');
    }

    function renderPattern12(channels) {
        renderSubscriberDistribution(channels);

        if (!channels || channels.length === 0) return;

        // 去重
        const seenIds = new Set();
        const validChannels = channels.filter(c => {
            if (c.subscriber_count == null || c.subscriber_count <= 0) return false;
            const id = c.channel_id || c.channel_name || c.title;
            if (seenIds.has(id)) return false;
            seenIds.add(id);
            return true;
        });

        const allSubs = validChannels.map(c => c.subscriber_count).sort((a, b) => a - b);
        const median = allSubs.length > 0 ? allSubs[Math.floor(allSubs.length / 2)] : 0;
        const maxSubs = allSubs.length > 0 ? allSubs[allSubs.length - 1] : 0;

        // 分层统计
        const tiers = {
            '100万+': validChannels.filter(c => c.subscriber_count >= 1000000).length,
            '10-100万': validChannels.filter(c => c.subscriber_count >= 100000 && c.subscriber_count < 1000000).length,
            '1-10万': validChannels.filter(c => c.subscriber_count >= 10000 && c.subscriber_count < 100000).length,
            '<1万': validChannels.filter(c => c.subscriber_count < 10000).length
        };

        const topTier = Object.entries(tiers).sort((a, b) => b[1] - a[1])[0];

        registerPatternConclusion('tab1', '12', '频道竞争格局',
            '频道竞争格局',
            `${validChannels.length}个频道中，${topTier[0]}订阅的最多（${topTier[1]}个，${(topTier[1]/validChannels.length*100).toFixed(0)}%）。中位数${formatNumber(median)}，最高${formatNumber(maxSubs)}。${median < 10000 ? '多数是小频道，新人入局机会大。' : '头部频道较多，需要差异化竞争。'}`,
            null,
            'subsDistScatter'
        );
    }

    // ========== 全局洞察生成 ==========

    function generateGlobalInsight(data) {
        const videos = data.videos || [];
        const channels = data.channels || [];

        const totalViews = videos.reduce((s, v) => s + (v.view_count || 0), 0);
        const avgViews = videos.length > 0 ? Math.round(totalViews / videos.length) : 0;

        let insight = `该领域共有${videos.length}个视频、${channels.length}个频道，`;
        insight += `总播放${formatNumber(totalViews)}，均播${formatNumber(avgViews)}。`;

        if (avgViews >= 100000) {
            insight += '属于大市场，值得深耕。';
        } else if (avgViews < 10000) {
            insight += '属于小众市场，竞争相对较小。';
        } else {
            insight += '属于中等规模市场，机会与挑战并存。';
        }

        return insight;
    }

    // ========== 导出 ==========
    exports.renderOverview = renderOverview;
    exports.renderPattern12 = renderPattern12;
    exports.renderPattern23 = renderPattern23;
    exports.renderSubscriberDistribution = renderSubscriberDistribution;
    exports.generateGlobalInsight = generateGlobalInsight;
    exports.countryShortNames = countryShortNames;

    // 向后兼容
    window.renderOverview = renderOverview;
    window.renderPattern12 = renderPattern12;
    window.renderPattern23 = renderPattern23;
    window.renderSubscriberDistribution = renderSubscriberDistribution;
    window.generateGlobalInsight = generateGlobalInsight;

})(window.InsightGlobal);

console.log('[insight-global.js] 模块加载完成');
