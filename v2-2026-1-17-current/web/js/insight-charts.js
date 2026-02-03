/**
 * insight-charts.js - 通用图表渲染器模块
 *
 * 包含：
 * - 图表实例管理（chartInstances, destroyChart）
 * - 通用散点图（renderScatter）
 * - 通用条形图（renderBar）
 * - 通用气泡图（renderBubble）
 * - 通用环形图（renderDonut）
 * - 通用折线图（renderLine）
 * - 通用直方图（renderHistogram）
 * - 通用堆叠条形图（renderStackedBar）
 * - 通用雷达图（renderRadar）
 * - 通用热力图（renderHeatmap）
 * - 通用面积图（renderArea）
 */

// ========== 命名空间 ==========
window.InsightCharts = window.InsightCharts || {};

(function(exports) {
    'use strict';

    // 图表实例存储
    const chartInstances = {};

    // 获取格式化函数（优先从 InsightCore，回退到本地实现）
    function formatNumber(num) {
        if (window.InsightCore?.formatNumber) {
            return window.InsightCore.formatNumber(num);
        }
        if (num === null || num === undefined) return '--';
        if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
        if (num >= 10000) return (num / 10000).toFixed(1) + '万';
        return num.toLocaleString();
    }

    // 获取图表缓存函数
    function cacheChartImage(chart, canvasId) {
        if (window.InsightReport?.cacheChartImage) {
            window.InsightReport.cacheChartImage(chart, canvasId);
        } else if (window.cacheChartImage) {
            window.cacheChartImage(chart, canvasId);
        }
    }

    // ========== 图表实例管理 ==========

    /**
     * 销毁指定图表
     */
    function destroyChart(chartId) {
        if (chartInstances[chartId]) {
            chartInstances[chartId].destroy();
            delete chartInstances[chartId];
        }
    }

    /**
     * 获取图表实例
     */
    function getChart(chartId) {
        return chartInstances[chartId];
    }

    /**
     * 获取所有图表实例
     */
    function getAllCharts() {
        return chartInstances;
    }

    // ========== 通用图表渲染器 ==========

    /**
     * 通用散点图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} data - 数据数组 [{x, y, label?, color?}, ...]
     * @param {Object} config - 配置 {xLabel, yLabel, xScale, yScale, title?}
     */
    function renderScatter(canvasId, data, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const chart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: config.title || '数据点',
                    data: data,
                    backgroundColor: data.map(d => d.color || 'rgba(6, 182, 212, 0.5)'),
                    borderColor: data.map(d => d.borderColor || 'rgba(6, 182, 212, 0.8)'),
                    pointRadius: config.pointRadius || 4,
                    pointHoverRadius: config.pointHoverRadius || 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const d = context.raw;
                                return config.tooltipFormatter ? config.tooltipFormatter(d) : [
                                    `${config.xLabel || 'X'}: ${d.x}`,
                                    `${config.yLabel || 'Y'}: ${formatNumber(d.y)}`,
                                    d.label ? d.label.substring(0, 40) : ''
                                ].filter(Boolean);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: config.xLabel || 'X', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' },
                        type: config.xScale || 'linear'
                    },
                    y: {
                        title: { display: true, text: config.yLabel || 'Y', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (value) => formatNumber(value)
                        },
                        type: config.yScale || 'linear'
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用条形图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} labels - 标签数组
     * @param {Array} values - 值数组
     * @param {Object} config - 配置 {horizontal, colors, yLabel, valueFormatter}
     */
    function renderBar(canvasId, labels, values, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`[Charts] renderBar: canvas '${canvasId}' 未找到!`);
            return null;
        }

        destroyChart(canvasId);

        const defaultColors = [
            'rgba(6, 182, 212, 0.7)',
            'rgba(34, 197, 94, 0.7)',
            'rgba(249, 115, 22, 0.7)',
            'rgba(139, 92, 246, 0.7)',
            'rgba(236, 72, 153, 0.7)',
            'rgba(59, 130, 246, 0.7)',
            'rgba(234, 179, 8, 0.7)',
            'rgba(239, 68, 68, 0.7)'
        ];

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: config.colors || defaultColors.slice(0, values.length),
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: config.horizontal ? 'y' : 'x',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => config.valueFormatter
                                ? config.valueFormatter(context.raw)
                                : formatNumber(context.raw)
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: config.horizontal, color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: config.horizontal ? (v) => formatNumber(v) : undefined
                        }
                    },
                    y: {
                        grid: { display: !config.horizontal, color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: !config.horizontal ? (v) => formatNumber(v) : undefined
                        },
                        title: config.yLabel ? { display: true, text: config.yLabel, color: '#94a3b8' } : undefined
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用气泡图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} data - 数据数组 [{x, y, r, label, color?}, ...]
     * @param {Object} config - 配置 {xLabel, yLabel, xScale, yScale}
     */
    function renderBubble(canvasId, data, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const chart = new Chart(ctx, {
            type: 'bubble',
            data: {
                datasets: [{
                    data: data,
                    backgroundColor: data.map((d, i) => {
                        if (d.color) return d.color;
                        if (i < 3) return 'rgba(239, 68, 68, 0.6)';
                        if (i < 10) return 'rgba(249, 115, 22, 0.6)';
                        return 'rgba(6, 182, 212, 0.5)';
                    }),
                    borderColor: data.map((d, i) => {
                        if (i < 3) return 'rgba(239, 68, 68, 0.9)';
                        if (i < 10) return 'rgba(249, 115, 22, 0.9)';
                        return 'rgba(6, 182, 212, 0.8)';
                    }),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const d = context.raw;
                                return config.tooltipFormatter ? config.tooltipFormatter(d) : [
                                    d.label || '',
                                    `${config.xLabel || 'X'}: ${formatNumber(d.x)}`,
                                    `${config.yLabel || 'Y'}: ${formatNumber(d.y)}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: config.xLabel || 'X', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' },
                        type: config.xScale || 'linear'
                    },
                    y: {
                        title: { display: true, text: config.yLabel || 'Y', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => formatNumber(v)
                        },
                        type: config.yScale || 'linear'
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用环形图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} labels - 标签数组
     * @param {Array} values - 值数组
     * @param {Object} config - 配置 {colors, centerText}
     */
    function renderDonut(canvasId, labels, values, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const defaultColors = [
            'rgba(239, 68, 68, 0.8)',
            'rgba(249, 115, 22, 0.8)',
            'rgba(234, 179, 8, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(6, 182, 212, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(139, 92, 246, 0.8)',
            'rgba(107, 114, 128, 0.6)'
        ];

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: config.colors || defaultColors.slice(0, values.length),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#94a3b8', font: { size: 11 } }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percent = ((context.raw / total) * 100).toFixed(1);
                                return `${context.label}: ${percent}%`;
                            }
                        }
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用折线图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} labels - X轴标签
     * @param {Array} datasets - 数据集 [{label, data, color}, ...]
     * @param {Object} config - 配置
     */
    function renderLine(canvasId, labels, datasets, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const defaultColors = ['#06b6d4', '#22c55e', '#f59e0b', '#ef4444'];

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets.map((ds, i) => ({
                    label: ds.label,
                    data: ds.data,
                    borderColor: ds.color || defaultColors[i % defaultColors.length],
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: datasets.length > 1,
                        labels: { color: '#94a3b8' }
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8', maxRotation: 45 }
                    },
                    y: {
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => formatNumber(v)
                        },
                        title: config.yLabel ? { display: true, text: config.yLabel, color: '#94a3b8' } : undefined
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用直方图渲染器（连续数据分布）
     * @param {string} canvasId - canvas元素ID
     * @param {Array} data - 原始数值数组
     * @param {Object} config - 配置 {bins, xLabel, yLabel, colors}
     */
    function renderHistogram(canvasId, data, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || data.length === 0) return null;

        destroyChart(canvasId);

        const bins = config.bins || [
            { label: '<1K', min: 0, max: 1000 },
            { label: '1K-5K', min: 1000, max: 5000 },
            { label: '5K-1万', min: 5000, max: 10000 },
            { label: '1万-5万', min: 10000, max: 50000 },
            { label: '5万-10万', min: 50000, max: 100000 },
            { label: '10万-50万', min: 100000, max: 500000 },
            { label: '50万-100万', min: 500000, max: 1000000 },
            { label: '100万+', min: 1000000, max: Infinity }
        ];

        const counts = bins.map(bin => ({
            label: bin.label,
            count: data.filter(v => v >= bin.min && v < bin.max).length
        }));

        const colors = config.colors || [
            'rgba(239, 68, 68, 0.7)', 'rgba(249, 115, 22, 0.7)',
            'rgba(234, 179, 8, 0.7)', 'rgba(34, 197, 94, 0.7)',
            'rgba(6, 182, 212, 0.7)', 'rgba(59, 130, 246, 0.7)',
            'rgba(139, 92, 246, 0.7)', 'rgba(236, 72, 153, 0.7)'
        ];

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: counts.map(c => c.label),
                datasets: [{
                    data: counts.map(c => c.count),
                    backgroundColor: colors.slice(0, counts.length),
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const percent = ((context.raw / data.length) * 100).toFixed(1);
                                return `${context.raw} 个 (${percent}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: config.xLabel || '区间', color: '#94a3b8' },
                        grid: { display: false },
                        ticks: { color: '#94a3b8', maxRotation: 45 }
                    },
                    y: {
                        title: { display: true, text: config.yLabel || '数量', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用堆叠条形图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} labels - 类别标签
     * @param {Array} datasets - 数据集 [{label, data, color}, ...]
     * @param {Object} config - 配置
     */
    function renderStackedBar(canvasId, labels, datasets, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const defaultColors = ['#06b6d4', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets.map((ds, i) => ({
                    label: ds.label,
                    data: ds.data,
                    backgroundColor: ds.color || defaultColors[i % defaultColors.length],
                    borderRadius: 2
                }))
            },
            options: {
                indexAxis: config.horizontal ? 'y' : 'x',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { color: '#94a3b8' }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        stacked: true,
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => formatNumber(v)
                        }
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用雷达图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} labels - 维度标签
     * @param {Array} datasets - 数据集 [{label, data, color}, ...]
     * @param {Object} config - 配置
     */
    function renderRadar(canvasId, labels, datasets, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const defaultColors = [
            { bg: 'rgba(6, 182, 212, 0.2)', border: '#06b6d4' },
            { bg: 'rgba(239, 68, 68, 0.2)', border: '#ef4444' },
            { bg: 'rgba(34, 197, 94, 0.2)', border: '#22c55e' }
        ];

        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: datasets.map((ds, i) => ({
                    label: ds.label,
                    data: ds.data,
                    backgroundColor: ds.bgColor || defaultColors[i % defaultColors.length].bg,
                    borderColor: ds.borderColor || defaultColors[i % defaultColors.length].border,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: datasets.length > 1,
                        position: 'top',
                        labels: { color: '#94a3b8' }
                    }
                },
                scales: {
                    r: {
                        angleLines: { color: '#334155' },
                        grid: { color: '#334155' },
                        pointLabels: { color: '#94a3b8' },
                        ticks: { display: false }
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用热力图渲染器（用散点图模拟）
     * @param {string} canvasId - canvas元素ID
     * @param {Array} data - 数据数组 [{x, y, value}, ...]
     * @param {Object} config - 配置 {xLabels, yLabels, xTitle, yTitle}
     */
    function renderHeatmap(canvasId, data, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const maxValue = Math.max(...data.map(d => d.value));
        const chartData = data.map(d => ({
            x: d.x,
            y: d.y,
            value: d.value,
            backgroundColor: `rgba(6, 182, 212, ${0.2 + (d.value / maxValue) * 0.8})`
        }));

        const chart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    data: chartData,
                    backgroundColor: chartData.map(d => d.backgroundColor),
                    pointRadius: 15,
                    pointStyle: 'rectRounded'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const d = context.raw;
                                const xLabel = config.xLabels ? config.xLabels[d.x] : d.x;
                                const yLabel = config.yLabels ? config.yLabels[d.y] : d.y;
                                return `${yLabel} ${xLabel}: ${formatNumber(d.value)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: config.xTitle || '', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => config.xLabels ? config.xLabels[v] : v
                        }
                    },
                    y: {
                        title: { display: true, text: config.yTitle || '', color: '#94a3b8' },
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => config.yLabels ? config.yLabels[v] : v
                        }
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用面积图渲染器
     * @param {string} canvasId - canvas元素ID
     * @param {Array} labels - X轴标签
     * @param {Array} datasets - 数据集 [{label, data, color}, ...]
     * @param {Object} config - 配置
     */
    function renderArea(canvasId, labels, datasets, config = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        destroyChart(canvasId);

        const defaultColors = [
            { bg: 'rgba(6, 182, 212, 0.3)', border: '#06b6d4' },
            { bg: 'rgba(34, 197, 94, 0.3)', border: '#22c55e' }
        ];

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets.map((ds, i) => ({
                    label: ds.label,
                    data: ds.data,
                    borderColor: ds.borderColor || defaultColors[i % defaultColors.length].border,
                    backgroundColor: ds.bgColor || defaultColors[i % defaultColors.length].bg,
                    fill: true,
                    tension: 0.3
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: datasets.length > 1,
                        labels: { color: '#94a3b8' }
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => formatNumber(v)
                        }
                    }
                }
            }
        });

        chartInstances[canvasId] = chart;
        cacheChartImage(chart, canvasId);
        return chart;
    }

    /**
     * 通用解读更新器
     * @param {string} insightId - 解读容器ID
     * @param {string} content - 解读内容HTML
     * @param {string} action - 行动建议
     */
    function updateInsight(insightId, content, action) {
        const el = document.getElementById(insightId);
        if (!el) return;

        el.innerHTML = `
            <div class="chart-insight-title">📖 数据解读</div>
            <div class="chart-insight-content">${content}</div>
            ${action ? `<div class="chart-insight-action">${action}</div>` : ''}
        `;
    }

    // ========== 导出 ==========
    exports.chartInstances = chartInstances;
    exports.destroyChart = destroyChart;
    exports.getChart = getChart;
    exports.getAllCharts = getAllCharts;

    exports.renderScatter = renderScatter;
    exports.renderBar = renderBar;
    exports.renderBubble = renderBubble;
    exports.renderDonut = renderDonut;
    exports.renderLine = renderLine;
    exports.renderHistogram = renderHistogram;
    exports.renderStackedBar = renderStackedBar;
    exports.renderRadar = renderRadar;
    exports.renderHeatmap = renderHeatmap;
    exports.renderArea = renderArea;
    exports.updateInsight = updateInsight;

    // 向后兼容：暴露到全局作用域
    window.destroyChart = destroyChart;
    window.renderScatter = renderScatter;
    window.renderBar = renderBar;
    window.renderBubble = renderBubble;
    window.renderDonut = renderDonut;
    window.renderLine = renderLine;
    window.renderHistogram = renderHistogram;
    window.renderStackedBar = renderStackedBar;
    window.renderRadar = renderRadar;
    window.renderHeatmap = renderHeatmap;
    window.renderArea = renderArea;
    window.updateInsight = updateInsight;

    // 暴露图表实例（供其他模块访问）
    window.chartInstances = chartInstances;

})(window.InsightCharts);

console.log('[insight-charts.js] 模块加载完成');
