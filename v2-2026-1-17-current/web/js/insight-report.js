/**
 * insight-report.js - 信息报告模块 (Tab7)
 *
 * 包含：
 * - 结论收集系统（tabConclusions, registerPatternConclusion）
 * - 信息报告渲染（renderInfoReportFromConclusions, renderTabReviewGrid）
 * - 综合洞察（renderSynthesis）
 * - 图表展开/复制（toggleConclusionChart, copyChartToCanvas）
 * - 延迟图表渲染（_renderChartDirectly, _renderFallbackChart）
 */

// ========== 命名空间 ==========
window.InsightReport = window.InsightReport || {};

(function(exports) {
    'use strict';

    // ========== 板块配置 ==========
    const tabResearchConfig = {
        tab1: {
            name: '全局认识',
            icon: '🌍',
            hypothesis: '了解市场全貌能帮助我找到竞争格局和机会',
            dataDescription: '视频播放量、频道订阅数、国家分布、语言分布等基础数据',
            synthesisTemplate: (items) => {
                const countries = items.find(i => i.patternId === '23');
                const subs = items.find(i => i.patternId === '12');
                if (countries && subs) {
                    return `市场以${countries.conclusion.match(/(\S+)占比最高/)?.[1] || '特定地区'}为主，${subs.conclusion.split('。')[0]}。`;
                }
                return '市场格局已初步分析，详见各模式结论。';
            }
        },
        tab2: {
            name: '套利分析',
            icon: '💰',
            hypothesis: '存在被低估的内容机会（高桥梁价值 + 低竞争）',
            dataDescription: '话题共现网络、频道关联网络、中心性指标',
            synthesisTemplate: (items) => {
                const arb = items.find(i => i.patternId === 'arb-opportunity');
                if (arb) return arb.conclusion;
                return '套利机会分析完成，详见各子榜单。';
            }
        },
        tab3: {
            name: '选题决策',
            icon: '🎯',
            hypothesis: '不同话题/内容类型有不同的播放天花板和竞争程度',
            dataDescription: '话题分类、内容类型、播放量上限、垄断度',
            synthesisTemplate: (items) => {
                const p4 = items.find(i => i.patternId === '4');
                const p13 = items.find(i => i.patternId === '13');
                if (p4) return p4.conclusion.split('。')[0] + '。';
                if (p13) return p13.conclusion.split('。')[0] + '。';
                return '选题分析完成，建议优先选择高天花板、低垄断的话题。';
            }
        },
        tab4: {
            name: '内容创作',
            icon: '✍️',
            hypothesis: '视频时长、标题写法等创作要素会影响播放量',
            dataDescription: '视频时长、标题长度、标题特征（数字/感叹号/hashtag）、句式',
            synthesisTemplate: (items) => {
                const p3 = items.find(i => i.patternId === '3');
                const p7 = items.find(i => i.patternId === '7');
                let result = '';
                if (p3) result += p3.conclusion.split('。')[0] + '；';
                if (p7) result += p7.conclusion.split('。')[0] + '。';
                return result || '创作要素分析完成，详见各模式结论。';
            }
        },
        tab5: {
            name: '发布策略',
            icon: '🚀',
            hypothesis: '发布时间会影响视频初始表现',
            dataDescription: '发布日期、发布时段、播放量分布',
            synthesisTemplate: (items) => {
                const p5 = items.find(i => i.patternId === '5');
                if (p5) return p5.conclusion;
                return '发布时间分析完成，建议选择观众活跃时段发布。';
            }
        },
        tab6: {
            name: '频道运营',
            icon: '📈',
            hypothesis: '频道规模和稳定性有规律可循',
            dataDescription: '频道订阅数、视频数量、播放稳定性、增长轨迹',
            synthesisTemplate: (items) => {
                const p11 = items.find(i => i.patternId === '11');
                const p12 = items.find(i => i.patternId === '12');
                if (p11) return p11.conclusion.split('。')[0] + '。';
                if (p12) return p12.conclusion.split('。')[0] + '。';
                return '频道运营分析完成，详见各模式结论。';
            }
        },
        tab8: {
            name: '用户洞察',
            icon: '👥',
            hypothesis: '评论能反映用户真实需求和内容缺口',
            dataDescription: '评论文本、热词、情感、问题类型、高赞特征',
            synthesisTemplate: (items) => {
                const p38 = items.find(i => i.patternId === '38');
                const p40 = items.find(i => i.patternId === '40');
                if (p38 && p40) {
                    return `用户${p40.conclusion.includes('正面') ? '满意度高' : '反馈多元'}，${p38.conclusion.split('。')[0]}。`;
                }
                return '用户洞察分析完成，详见各模式结论。';
            }
        }
    };

    // ========== 全局结论存储 ==========
    const tabConclusions = {
        tab1: { name: '全局认识', icon: '🌍', items: [] },
        tab2: { name: '套利分析', icon: '💰', items: [] },
        tab3: { name: '选题决策', icon: '🎯', items: [] },
        tab4: { name: '内容创作', icon: '✍️', items: [] },
        tab5: { name: '发布策略', icon: '🚀', items: [] },
        tab6: { name: '频道运营', icon: '📈', items: [] },
        tab8: { name: '用户洞察', icon: '👥', items: [] }
    };

    // 图表图片缓存
    const chartImageCache = {};

    // 结论图表实例
    const conclusionChartInstances = {};

    // ========== 图表缓存 ==========

    // 缓存图表图片（在图表创建后调用）
    // 优化：支持同步缓存 + 异步备份，提高Tab7快速打开的概率
    function cacheChartImage(chart, canvasId) {
        if (!chart || !canvasId) return;
        try {
            // 方案1: 尝试同步转换（大多数情况下会成功）
            try {
                const base64 = chart.toBase64Image('image/png', 1);
                if (base64 && base64.length > 100) {
                    chartImageCache[canvasId] = base64;
                    console.log(`[Report] 图表缓存(同步) ${canvasId} (${Math.round(base64.length/1024)}KB)`);
                    return; // 同步缓存成功，不需要异步备份
                }
            } catch (syncError) {
                // 同步失败，进行异步备份
                console.warn(`[Report] 缓存同步失败 ${canvasId}，使用异步备份`);
            }

            // 方案2: 异步备份（requestAnimationFrame作为降级方案）
            requestAnimationFrame(() => {
                try {
                    const base64 = chart.toBase64Image('image/png', 1);
                    if (base64 && base64.length > 100) {
                        chartImageCache[canvasId] = base64;
                        console.log(`[Report] 图表缓存(异步) ${canvasId} (${Math.round(base64.length/1024)}KB)`);
                    }
                } catch (e) {
                    console.warn(`[Report] 缓存失败 ${canvasId}:`, e.message);
                }
            });
        } catch (e) {
            console.warn(`[Report] 缓存初始化失败 ${canvasId}:`, e.message);
        }
    }

    // ========== 结论注册 ==========

    // 注册模式结论到对应板块
    function registerPatternConclusion(tabId, patternId, patternName, dataSource, conclusion, examples = null, chartConfig = null) {
        if (tabConclusions[tabId]) {
            const existingIndex = tabConclusions[tabId].items.findIndex(item => item.patternId === patternId);

            let sourceCanvasId = null;
            let fallbackConfig = null;
            if (typeof chartConfig === 'string') {
                sourceCanvasId = chartConfig;
                chartConfig = null;
            } else if (chartConfig && typeof chartConfig === 'object' && chartConfig.sourceCanvasId) {
                sourceCanvasId = chartConfig.sourceCanvasId;
                fallbackConfig = chartConfig.fallbackConfig || null;
                chartConfig = fallbackConfig;
            }

            const newItem = {
                patternId,
                patternName,
                dataSource,
                conclusion,
                examples: examples || [],
                chartConfig: chartConfig,
                sourceCanvasId: sourceCanvasId
            };

            if (existingIndex !== -1) {
                if (!newItem.sourceCanvasId && tabConclusions[tabId].items[existingIndex].sourceCanvasId) {
                    newItem.sourceCanvasId = tabConclusions[tabId].items[existingIndex].sourceCanvasId;
                }
                tabConclusions[tabId].items[existingIndex] = newItem;
                console.log(`[Report] 模式${patternId}：${patternName} (已更新)`);
            } else {
                tabConclusions[tabId].items.push(newItem);
                console.log(`[Report] 模式${patternId}：${patternName}`);
            }
        }
    }

    // 清空所有结论
    function clearAllConclusions() {
        Object.keys(tabConclusions).forEach(key => {
            tabConclusions[key].items = [];
        });
    }

    // ========== 图表复制 ==========

    // 从源 canvas 复制图表到目标 canvas
    function copyChartToCanvas(sourceCanvasId, targetCanvasId) {
        const sourceCanvas = document.getElementById(sourceCanvasId);
        const targetCanvas = document.getElementById(targetCanvasId);

        if (!sourceCanvas || !targetCanvas) {
            console.warn(`[Report] canvas 不存在: source=${sourceCanvasId}, target=${targetCanvasId}`);
            return false;
        }

        // 检查源 canvas 尺寸（关键！）
        if (sourceCanvas.width === 0 || sourceCanvas.height === 0) {
            console.warn(`[Report] 源 canvas 尺寸为0，无法复制: ${sourceCanvasId}`);
            return false;
        }

        try {
            targetCanvas.width = sourceCanvas.width;
            targetCanvas.height = sourceCanvas.height;

            const ctx = targetCanvas.getContext('2d');
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(0, 0, targetCanvas.width, targetCanvas.height);
            ctx.drawImage(sourceCanvas, 0, 0);

            console.log(`[Report] 复制成功: ${sourceCanvasId} → ${targetCanvasId}`);
            return true;
        } catch (e) {
            console.warn(`[Report] 复制失败: ${sourceCanvasId}`, e);
            return false;
        }
    }

    // ========== 延迟图表渲染 ==========

    // 直接在展开区域渲染图表
    function _renderChartDirectly(sourceCanvasId, targetCanvasId) {
        const chartRenderMap = {
            // 策略1：优先尝试从原始canvas复制（适用于所有图表类型）
            '_tryDirectCopy': () => {
                const originalCanvas = document.getElementById(sourceCanvasId);
                if (originalCanvas && originalCanvas.width > 0 && originalCanvas.height > 0) {
                    const targetCanvas = document.getElementById(targetCanvasId);
                    if (targetCanvas) {
                        try {
                            targetCanvas.width = originalCanvas.width;
                            targetCanvas.height = originalCanvas.height;
                            const ctx = targetCanvas.getContext('2d');
                            ctx.drawImage(originalCanvas, 0, 0);
                            console.log(`[Report] ✓ 直接复制原始图表: ${sourceCanvasId}`);
                            return true;
                        } catch (e) {
                            console.warn(`[Report] 直接复制失败 ${sourceCanvasId}:`, e.message);
                            return false;
                        }
                    }
                }
                return false;
            },

            // 策略2：根据图表类型重新渲染（后备方案）
            'overviewScatterChart': () => {
                // 优先复制，失败则不提供重新渲染（这个图表必须来自Tab1）
                return chartRenderMap._tryDirectCopy();
            },
            'languageDistChart': () => {
                if (!chartRenderMap._tryDirectCopy()) {
                    if (window._cachedUserInsights?.language) {
                        return _renderLanguageChartToCanvas(targetCanvasId, window._cachedUserInsights.language);
                    }
                }
                return false;
            },
            'countryBarChart': () => {
                if (!chartRenderMap._tryDirectCopy()) {
                    if (window._cachedChannels) {
                        return _renderCountryChartToCanvas(targetCanvasId, window._cachedChannels);
                    }
                }
                return false;
            },
            'contentTypeScatterChart': () => {
                if (!chartRenderMap._tryDirectCopy()) {
                    if (window._cachedVideos) {
                        return _renderViewsTrendChartToCanvas(targetCanvasId, window._cachedVideos);
                    }
                }
                return false;
            },
            'subsDistScatter': () => {
                if (!chartRenderMap._tryDirectCopy()) {
                    if (window._cachedChannels) {
                        return _renderSubsDistChartToCanvas(targetCanvasId, window._cachedChannels);
                    }
                }
                return false;
            }
        };

        const renderFn = chartRenderMap[sourceCanvasId];
        if (renderFn) {
            return renderFn();
        }
        return false;
    }

    // 渲染语言分布图到指定 canvas
    function _renderLanguageChartToCanvas(canvasId, language) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !language?.distribution?.length) return false;

        const data = language.distribution.filter(d =>
            d.percentage > 0.5 && d.code !== 'emoji' && d.code !== 'unknown'
        );
        if (!data.length) return false;

        const colors = {
            'zh-CN': '#06b6d4', 'zh-TW': '#f97316', 'en': '#10b981',
            'ja': '#ec4899', 'ko': '#8b5cf6', 'emoji': '#fbbf24', 'unknown': '#475569'
        };

        if (conclusionChartInstances[canvasId]) {
            conclusionChartInstances[canvasId].destroy();
        }

        conclusionChartInstances[canvasId] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: data.map(d => (colors[d.code] || '#64748b') + 'cc'),
                    borderColor: data.map(d => colors[d.code] || '#64748b'),
                    borderWidth: 1, borderRadius: 4
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
                            label: ctx => `${data[ctx.dataIndex].count.toLocaleString()} 条评论 (${data[ctx.dataIndex].percentage}%)`
                        }
                    }
                },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                    y: { grid: { display: false }, ticks: { color: '#e2e8f0', font: { size: 12 } } }
                }
            }
        });
        return true;
    }

    // 渲染国家分布图到指定 canvas
    function _renderCountryChartToCanvas(canvasId, channels) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !channels?.length) return false;

        const countryStats = {};
        channels.forEach(ch => {
            const country = ch.country || '未知';
            if (!countryStats[country]) countryStats[country] = { count: 0, views: 0 };
            countryStats[country].count++;
            countryStats[country].views += ch.total_views || 0;
        });

        const sorted = Object.entries(countryStats)
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 10);

        if (!sorted.length) return false;

        if (conclusionChartInstances[canvasId]) {
            conclusionChartInstances[canvasId].destroy();
        }

        conclusionChartInstances[canvasId] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: sorted.map(([c]) => c),
                datasets: [{
                    label: '频道数',
                    data: sorted.map(([, s]) => s.count),
                    backgroundColor: 'rgba(6, 182, 212, 0.7)',
                    borderColor: 'rgba(6, 182, 212, 1)',
                    borderWidth: 1, borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                    y: { grid: { display: false }, ticks: { color: '#e2e8f0' } }
                }
            }
        });
        return true;
    }

    // 渲染播放量趋势图到指定 canvas
    function _renderViewsTrendChartToCanvas(canvasId, videos) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !videos?.length) return false;

        const formatNum = (v) => v >= 10000 ? (v/10000).toFixed(0) + '万' : v.toLocaleString();

        const data = videos
            .filter(v => v.published_at && v.view_count)
            .map(v => ({
                x: new Date(v.published_at).getTime(),
                y: v.view_count,
                title: v.title
            }))
            .sort((a, b) => a.x - b.x);

        if (!data.length) return false;

        if (conclusionChartInstances[canvasId]) {
            conclusionChartInstances[canvasId].destroy();
        }

        conclusionChartInstances[canvasId] = new Chart(canvas, {
            type: 'scatter',
            data: {
                datasets: [{
                    data: data,
                    backgroundColor: 'rgba(6, 182, 212, 0.6)',
                    borderColor: 'rgba(6, 182, 212, 1)',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => [
                                ctx.raw.title?.substring(0, 30) + '...',
                                `播放: ${formatNum(ctx.raw.y)}`
                            ]
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: { unit: 'day', displayFormats: { day: 'MM-dd' } },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b' }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b', callback: v => formatNum(v) }
                    }
                }
            }
        });
        return true;
    }

    // 渲染订阅分布图到指定 canvas
    function _renderSubsDistChartToCanvas(canvasId, channels) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !channels?.length) return false;

        const formatNum = (v) => v >= 10000 ? (v/10000).toFixed(0) + '万' : v.toLocaleString();

        const getColor = (subs) => {
            if (subs >= 1000000) return '#ef4444';
            if (subs >= 100000) return '#f97316';
            if (subs >= 10000) return '#10b981';
            return '#06b6d4';
        };

        const data = channels
            .filter(c => c.subscriber_count)
            .map((c, i) => ({
                x: i,
                y: c.subscriber_count,
                name: c.channel_name
            }));

        if (!data.length) return false;

        if (conclusionChartInstances[canvasId]) {
            conclusionChartInstances[canvasId].destroy();
        }

        conclusionChartInstances[canvasId] = new Chart(canvas, {
            type: 'scatter',
            data: {
                datasets: [{
                    data: data,
                    backgroundColor: data.map(d => getColor(d.y) + '99'),
                    borderColor: data.map(d => getColor(d.y)),
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => [`${ctx.raw.name}`, `订阅: ${formatNum(ctx.raw.y)}`]
                        }
                    }
                },
                scales: {
                    x: { display: false },
                    y: {
                        type: 'logarithmic',
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#64748b', callback: v => formatNum(v) }
                    }
                }
            }
        });
        return true;
    }

    // 回退图表渲染
    function _renderFallbackChart(chartId, tabId, itemIdx, targetCanvasId, item) {
        if (item.sourceCanvasId) {
            const copied = copyChartToCanvas(item.sourceCanvasId, targetCanvasId);
            if (copied) return;
        }
        if (item.chartConfig) {
            renderConclusionChart(chartId, tabId, itemIdx);
            return;
        }
        if (item.sourceCanvasId) {
            _renderChartDirectly(item.sourceCanvasId, targetCanvasId);
        }
    }

    // ========== 图表展开/关闭 ==========

    // 切换结论图表显示
    function toggleConclusionChart(chartId, tabId, itemIdx) {
        const container = document.getElementById(chartId);
        if (!container) return;

        const isVisible = container.classList.contains('visible');
        const conclusionItem = container.previousElementSibling;

        if (isVisible) {
            container.classList.remove('visible');
            conclusionItem.classList.remove('expanded');
            if (conclusionChartInstances[chartId]) {
                conclusionChartInstances[chartId].destroy();
                delete conclusionChartInstances[chartId];
            }
        } else {
            container.classList.add('visible');
            conclusionItem.classList.add('expanded');

            const tab = tabConclusions[tabId];
            const item = tab?.items?.[itemIdx];

            if (item) {
                const targetCanvasId = `${chartId}-canvas`;
                let renderSuccess = false;

                // 方案1：优先使用缓存的 base64 图片（最快，通常 < 10ms）
                if (item.sourceCanvasId && chartImageCache[item.sourceCanvasId]) {
                    const cachedImage = chartImageCache[item.sourceCanvasId];
                    if (cachedImage && cachedImage.length > 1000) {
                        const targetCanvas = document.getElementById(targetCanvasId);
                        if (targetCanvas) {
                            const img = new Image();
                            img.onload = () => {
                                if (img.width > 0 && img.height > 0) {
                                    targetCanvas.width = img.width;
                                    targetCanvas.height = img.height;
                                    const ctx = targetCanvas.getContext('2d');
                                    ctx.drawImage(img, 0, 0);
                                    console.log(`[Report] ✓ Tier1 使用缓存图片: ${item.sourceCanvasId}`);
                                } else {
                                    console.warn(`[Report] 缓存图片尺寸无效，降级到Tier2`);
                                    _renderFallbackChart(chartId, tabId, itemIdx, targetCanvasId, item);
                                }
                            };
                            img.onerror = () => {
                                console.warn(`[Report] 缓存图片加载失败，降级到Tier2`);
                                _renderFallbackChart(chartId, tabId, itemIdx, targetCanvasId, item);
                            };
                            img.src = cachedImage;
                            renderSuccess = true;
                        }
                    }
                }

                // 方案2：尝试直接复制 canvas（~10-50ms）
                if (!renderSuccess && item.sourceCanvasId) {
                    if (copyChartToCanvas(item.sourceCanvasId, targetCanvasId)) {
                        console.log(`[Report] ✓ Tier2 直接复制canvas: ${item.sourceCanvasId}`);
                        renderSuccess = true;
                    } else {
                        console.warn(`[Report] Tier2 复制失败，继续降级`);
                    }
                }

                // 方案3：使用 chartConfig 动态渲染（~100-300ms）
                if (!renderSuccess && item.chartConfig) {
                    console.log(`[Report] → Tier3 动态渲染图表: ${item.patternId}`);
                    renderConclusionChart(chartId, tabId, itemIdx);
                    renderSuccess = true;
                }

                // 方案4：直接在展开区域重新渲染（~200-500ms）
                if (!renderSuccess && item.sourceCanvasId) {
                    console.log(`[Report] → Tier4 重新渲染图表: ${item.sourceCanvasId}`);
                    renderSuccess = _renderChartDirectly(item.sourceCanvasId, targetCanvasId);
                }

                // 所有方案都失败，显示提示
                if (!renderSuccess) {
                    const targetCanvas = document.getElementById(targetCanvasId);
                    if (targetCanvas) {
                        targetCanvas.width = 400;
                        targetCanvas.height = 200;
                        const ctx = targetCanvas.getContext('2d');
                        ctx.fillStyle = '#1e293b';
                        ctx.fillRect(0, 0, 400, 200);
                        ctx.fillStyle = '#64748b';
                        ctx.font = '14px sans-serif';
                        ctx.textAlign = 'center';
                        ctx.fillText('请先查看「全局认识」标签页加载图表数据', 200, 100);
                    }
                }
            }
        }
    }

    // 关闭结论图表
    function closeConclusionChart(chartId) {
        const container = document.getElementById(chartId);
        if (!container) return;

        container.classList.remove('visible');
        const conclusionItem = container.previousElementSibling;
        if (conclusionItem) {
            conclusionItem.classList.remove('expanded');
        }

        if (conclusionChartInstances[chartId]) {
            conclusionChartInstances[chartId].destroy();
            delete conclusionChartInstances[chartId];
        }
    }

    // 渲染结论对应的图表
    function renderConclusionChart(chartId, tabId, itemIdx) {
        const tab = tabConclusions[tabId];
        if (!tab || !tab.items[itemIdx]) return;

        const item = tab.items[itemIdx];
        if (item.chartImage) return;

        const chartConfig = item.chartConfig;
        if (!chartConfig) return;

        const canvasId = `${chartId}-canvas`;
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        if (conclusionChartInstances[chartId]) {
            conclusionChartInstances[chartId].destroy();
        }

        const chart = new Chart(ctx, {
            type: chartConfig.type || 'bar',
            data: chartConfig.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: chartConfig.showLegend !== false,
                        position: 'top',
                        labels: { color: '#94a3b8', font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(100, 116, 139, 0.3)',
                        borderWidth: 1
                    }
                },
                scales: chartConfig.type !== 'pie' && chartConfig.type !== 'doughnut' ? {
                    x: {
                        grid: { color: 'rgba(100, 116, 139, 0.15)' },
                        ticks: { color: '#94a3b8', font: { size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(100, 116, 139, 0.15)' },
                        ticks: { color: '#94a3b8', font: { size: 10 } }
                    }
                } : undefined,
                ...chartConfig.options
            }
        });

        conclusionChartInstances[chartId] = chart;
        console.log(`[Report] 渲染图表 ${chartId}`);
    }

    // ========== 信息报告渲染 ==========

    // 渲染信息报告 - 基于各板块结论
    function renderInfoReportFromConclusions() {
        console.log('[Report] 渲染信息报告...');
        renderTabReviewGrid();
        renderSynthesis();
    }

    // 渲染六大板块回顾网格
    function renderTabReviewGrid() {
        const gridEl = document.getElementById('tabReviewGrid');
        if (!gridEl) return;

        const tabConfig = [
            { id: 'tab1', name: '全局认识', icon: '🌍' },
            { id: 'tab2', name: '套利分析', icon: '💰' },
            { id: 'tab3', name: '选题决策', icon: '🎯' },
            { id: 'tab4', name: '内容创作', icon: '✍️' },
            { id: 'tab5', name: '发布策略', icon: '🚀' },
            { id: 'tab6', name: '频道运营', icon: '📈' },
            { id: 'tab8', name: '用户洞察', icon: '👥' }
        ];

        let html = '';
        tabConfig.forEach(config => {
            const tab = tabConclusions[config.id];
            const items = tab?.items || [];
            const count = items.length;
            const researchConfig = tabResearchConfig[config.id] || {};

            let conclusionsHtml = '';
            if (count === 0) {
                conclusionsHtml = '<div class="pattern-conclusion-item no-data">暂无数据，请先查看该板块</div>';
            } else {
                items.forEach((item, idx) => {
                    const patternLabel = item.patternId && item.patternName
                        ? `「模式${item.patternId}：${item.patternName}」`
                        : '';
                    const hasSourceCanvas = item.sourceCanvasId != null;
                    const hasChart = item.chartConfig != null;
                    const expandable = hasSourceCanvas || hasChart;
                    const expandableClass = expandable ? 'expandable' : '';
                    const chartId = `chart-${config.id}-${item.patternId || idx}`;

                    conclusionsHtml += `
                        <div class="pattern-conclusion-wrapper">
                            <div class="pattern-conclusion-item ${expandableClass}"
                                 ${expandable ? `onclick="InsightReport.toggleConclusionChart('${chartId}', '${config.id}', ${idx})"` : ''}>
                                <span class="conclusion-number">${idx + 1}.</span>
                                <span class="conclusion-text">
                                    基于「${item.dataSource}」得出${patternLabel}：${item.conclusion}
                                </span>
                                ${expandable ? '<span class="expand-icon">📊</span>' : ''}
                            </div>
                            ${expandable ? `
                            <div class="conclusion-chart-container" id="${chartId}">
                                <div class="chart-title">
                                    <span>📊 ${item.patternName || item.dataSource}</span>
                                    <button class="chart-close" onclick="event.stopPropagation(); InsightReport.closeConclusionChart('${chartId}')">收起 ▲</button>
                                </div>
                                <div class="chart-wrapper">
                                    <canvas id="${chartId}-canvas" style="width:100%; height:280px;"></canvas>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    `;
                });
            }

            const synthesis = researchConfig.synthesisTemplate
                ? researchConfig.synthesisTemplate(items)
                : (count > 0 ? '详见上方各模式结论。' : '暂无综合结论。');

            html += `
                <div class="tab-review-card">
                    <div class="tab-review-header">
                        <div class="tab-review-title">
                            <span class="tab-icon">${config.icon}</span>
                            <span>${config.name}</span>
                        </div>
                        <span class="tab-review-badge">${count} 条结论</span>
                    </div>
                    <div class="research-context">
                        <div class="hypothesis-section">
                            <span class="hypothesis-label">🎯 问题意识：</span>
                            <span class="hypothesis-text">因为我想验证假设「${researchConfig.hypothesis || '待配置'}」</span>
                        </div>
                        <div class="data-source-section">
                            <span class="data-label">📊 我收集了：</span>
                            <span class="data-text">${researchConfig.dataDescription || '相关数据'}</span>
                        </div>
                    </div>
                    <div class="tab-conclusions-list">
                        ${conclusionsHtml}
                    </div>
                    <div class="synthesis-section">
                        <div class="synthesis-label">💡 综合结论：</div>
                        <div class="synthesis-text">${synthesis}</div>
                    </div>
                </div>
            `;
        });

        gridEl.innerHTML = html;
    }

    // 渲染综合洞察
    function renderSynthesis() {
        const contentEl = document.getElementById('synthesisContent');
        if (!contentEl) return;

        const allItems = [];
        Object.entries(tabConclusions).forEach(([tabId, tab]) => {
            (tab.items || []).forEach(item => {
                allItems.push({ ...item, source: tab.name, tabId, icon: tab.icon });
            });
        });

        if (allItems.length === 0) {
            contentEl.innerHTML = '<div class="synthesis-loading">请先查看其他板块的分析，结论将自动汇总到这里</div>';
            return;
        }

        const patternItems = allItems.filter(i => i.patternId && i.patternName);
        const totalPatterns = patternItems.length;

        const getPattern = (tabId, patternId) => {
            return patternItems.find(i => i.tabId === tabId && i.patternId === patternId);
        };

        let html = `<div class="synthesis-header-main">🔍 深度洞察（基于 ${totalPatterns} 个模式交叉分析）</div>`;

        html += `<div class="cross-insights-grid">`;

        // 1. 最佳赛道
        const p4 = getPattern('tab1', '4');
        const p23 = getPattern('tab1', '23');
        const p13 = getPattern('tab3', '13');
        if (p4 || p23 || p13) {
            html += `<div class="cross-card">
                <div class="cross-card-title">📌 最佳赛道判断</div>
                <div class="cross-card-sources">
                    ${p4 ? `<div class="source-row"><span class="source-tag">模式4</span>${p4.conclusion.split('。')[0]}</div>` : ''}
                    ${p23 ? `<div class="source-row"><span class="source-tag">模式23</span>${p23.conclusion.split('。')[0]}</div>` : ''}
                    ${p13 ? `<div class="source-row"><span class="source-tag">模式13</span>${p13.conclusion.split('。')[0]}</div>` : ''}
                </div>
                <div class="cross-card-conclusion">
                    ∴ 综合三个维度的数据，找出高天花板 + 低垄断 + 长青的最佳赛道
                </div>
            </div>`;
        }

        // 2. 效率悖论
        const p12 = getPattern('tab1', '12');
        const p2 = getPattern('tab6', '2');
        if (p12 || p2) {
            html += `<div class="cross-card">
                <div class="cross-card-title">📌 频道规模悖论</div>
                <div class="cross-card-sources">
                    ${p12 ? `<div class="source-row"><span class="source-tag">模式12</span>${p12.conclusion.split('。')[0]}</div>` : ''}
                    ${p2 ? `<div class="source-row"><span class="source-tag">模式2</span>${p2.conclusion.split('。')[0]}</div>` : ''}
                </div>
                <div class="cross-card-conclusion">
                    ∴ 新人起步无劣势，内容质量比粉丝数更重要
                </div>
            </div>`;
        }

        // 3. 内容公式
        const p3 = getPattern('tab4', '3');
        const p7 = getPattern('tab4', '7');
        const p10 = getPattern('tab4', '10');
        if (p3 || p7 || p10) {
            html += `<div class="cross-card">
                <div class="cross-card-title">📌 爆款内容公式</div>
                <div class="cross-card-sources">
                    ${p3 ? `<div class="source-row"><span class="source-tag">模式3</span>${p3.conclusion.split('。')[0]}</div>` : ''}
                    ${p7 ? `<div class="source-row"><span class="source-tag">模式7</span>${p7.conclusion.split('。')[0]}</div>` : ''}
                    ${p10 ? `<div class="source-row"><span class="source-tag">模式10</span>${p10.conclusion.split('。')[0]}</div>` : ''}
                </div>
                <div class="cross-card-conclusion">
                    ∴ 综合最佳时长 + 标题特征，形成可复用的内容公式
                </div>
            </div>`;
        }

        html += `</div>`;

        // 行动清单
        const actionItems = patternItems
            .filter(item => item.conclusion.includes('建议') || item.conclusion.includes('优先'))
            .slice(0, 5);

        if (actionItems.length > 0) {
            html += `<div class="action-section">
                <div class="action-section-title">📋 行动清单</div>
                <div class="action-items">`;

            actionItems.forEach((item, idx) => {
                const sentences = item.conclusion.split('。');
                const actionText = sentences.find(s => s.includes('建议') || s.includes('优先')) || sentences[0];
                html += `<div class="action-row">
                    <span class="action-num">${idx + 1}</span>
                    <span class="action-text">${actionText}</span>
                    <span class="action-from">模式${item.patternId}</span>
                </div>`;
            });

            html += `</div></div>`;
        }

        // 风险提示
        const riskItems = patternItems
            .filter(item => item.conclusion.includes('避免') || item.conclusion.includes('避开'))
            .slice(0, 3);

        if (riskItems.length > 0) {
            html += `<div class="risk-section">
                <div class="risk-section-title">⚠️ 避坑指南</div>
                <div class="risk-items">`;

            riskItems.forEach(item => {
                const sentences = item.conclusion.split('。');
                const riskText = sentences.find(s => s.includes('避免') || s.includes('避开')) || '';
                if (riskText) {
                    html += `<div class="risk-row">
                        <span class="risk-icon">🚫</span>
                        <span class="risk-text">${riskText}</span>
                        <span class="risk-from">模式${item.patternId}</span>
                    </div>`;
                }
            });

            html += `</div></div>`;
        }

        contentEl.innerHTML = html;
    }

    // 跳转到指定Tab
    function jumpToTab(tabId) {
        const tabBtn = document.querySelector(`.pattern-tab[data-tab="${tabId}"]`);
        if (tabBtn) {
            tabBtn.click();
            const tabContent = document.getElementById(tabId);
            if (tabContent) {
                tabContent.classList.add('highlight-jump');
                setTimeout(() => tabContent.classList.remove('highlight-jump'), 2000);
            }
        }
    }

    // ========== 导出 ==========
    exports.tabResearchConfig = tabResearchConfig;
    exports.tabConclusions = tabConclusions;
    exports.chartImageCache = chartImageCache;
    exports.conclusionChartInstances = conclusionChartInstances;

    exports.cacheChartImage = cacheChartImage;
    exports.registerPatternConclusion = registerPatternConclusion;
    exports.clearAllConclusions = clearAllConclusions;
    exports.copyChartToCanvas = copyChartToCanvas;
    exports.toggleConclusionChart = toggleConclusionChart;
    exports.closeConclusionChart = closeConclusionChart;
    exports.renderConclusionChart = renderConclusionChart;
    exports.renderInfoReportFromConclusions = renderInfoReportFromConclusions;
    exports.renderTabReviewGrid = renderTabReviewGrid;
    exports.renderSynthesis = renderSynthesis;
    exports.jumpToTab = jumpToTab;

    // 向后兼容：暴露到全局作用域
    window.registerPatternConclusion = registerPatternConclusion;
    window.clearAllConclusions = clearAllConclusions;
    window.cacheChartImage = cacheChartImage;
    window.copyChartToCanvas = copyChartToCanvas;
    window.toggleConclusionChart = toggleConclusionChart;
    window.closeConclusionChart = closeConclusionChart;
    window.renderInfoReportFromConclusions = renderInfoReportFromConclusions;
    window.jumpToTab = jumpToTab;

    // 暴露内部变量（供其他模块访问）
    window.tabConclusions = tabConclusions;
    window.chartImageCache = chartImageCache;

})(window.InsightReport);

console.log('[insight-report.js] 模块加载完成');
