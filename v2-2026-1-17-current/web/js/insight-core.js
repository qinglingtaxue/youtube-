/**
 * insight-core.js - 核心工具函数模块
 *
 * 包含：
 * - 全局配置和状态
 * - URL 参数处理
 * - 日期计算
 * - 数据加载
 * - 格式化工具
 * - 加载状态管理
 * - 工具提示
 */

// ========== 命名空间 ==========
window.InsightCore = window.InsightCore || {};

(function(exports) {
    'use strict';

    // ========== 全局配置 ==========
    const API_BASE = window.location.origin;

    // 从 URL 获取关键词参数
    function getKeywordFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('keyword') || '养生';
    }

    // 从 URL 获取时间段参数
    function getTimePeriodFromURL() {
        const params = new URLSearchParams(window.location.search);
        const days = params.get('days');
        return days ? parseInt(days) : 30; // 默认 30 天
    }

    // 当前分析的关键词
    let currentKeyword = getKeywordFromURL();

    // 当前时间段（天数，0 表示全部）
    let currentTimePeriod = getTimePeriodFromURL();

    // 存储 API 返回的数据
    let analysisData = null;

    // 存储各时间段的数据缓存
    const dataCache = {};

    // ========== 日期计算 ==========

    // 计算日期范围
    function getDateRange(days) {
        if (days <= 0) return { date_from: null, date_to: null };

        const now = new Date();
        const from = new Date(now);
        from.setDate(from.getDate() - days);

        return {
            date_from: from.toISOString().split('T')[0],
            date_to: now.toISOString().split('T')[0]
        };
    }

    // 获取时间段描述
    function getTimePeriodLabel(days) {
        if (days <= 0) return '全部时间';
        if (days === 1) return '近 24 小时';
        if (days === 7) return '近 7 天';
        if (days === 30) return '近 30 天';
        if (days === 90) return '近 90 天';
        return `近 ${days} 天`;
    }

    // ========== 格式化工具 ==========

    // 格式化数字
    function formatNumber(num) {
        if (num === null || num === undefined) return '--';
        if (num >= 100000000) {
            return (num / 100000000).toFixed(1) + '亿';
        }
        if (num >= 10000) {
            return (num / 10000).toFixed(1) + '万';
        }
        return num.toLocaleString();
    }

    // 格式化百分比
    function formatPercent(num, decimals = 1) {
        if (num === null || num === undefined) return '--';
        return num.toFixed(decimals) + '%';
    }

    // 格式化日期
    function formatDate(dateStr) {
        if (!dateStr) return '--';
        const date = new Date(dateStr);
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    }

    // ========== 加载状态管理 ==========

    // 显示加载进度提示
    function showLoadingProgress(msg) {
        const el = document.getElementById('loadingStatus');
        if (el) el.textContent = msg;
        const banner = document.getElementById('globalLoadingBanner');
        if (banner) banner.style.display = 'flex';
    }

    // 隐藏加载进度（数据加载完成后调用）
    function hideLoadingBanner() {
        const banner = document.getElementById('globalLoadingBanner');
        if (banner) banner.style.display = 'none';
    }

    // 显示加载错误
    function showLoadingError(msg) {
        const banner = document.getElementById('globalLoadingBanner');
        const spinner = document.getElementById('loadingSpinner');
        const statusEl = document.getElementById('loadingStatus');
        if (banner) {
            banner.style.borderColor = '#dc2626';
            if (spinner) spinner.style.display = 'none';
            if (statusEl) statusEl.innerHTML = `<span style="color:#ef4444">${msg}</span> <button onclick="location.reload()" style="margin-left:12px;padding:4px 16px;border-radius:6px;border:1px solid #334155;background:#1e293b;color:#94a3b8;cursor:pointer">重试</button>`;
        }
    }

    // ========== 图表无数据提示 ==========

    // 显示图表无数据提示
    function showChartNoData(canvasId, dataType) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const container = canvas.parentElement;
        if (!container) return;

        // 隐藏 canvas
        canvas.style.display = 'none';

        // 检查是否已有提示
        let msgEl = container.querySelector('.no-data-message');
        if (!msgEl) {
            msgEl = document.createElement('div');
            msgEl.className = 'no-data-message';
            msgEl.style.cssText = 'display:flex;align-items:center;justify-content:center;height:100%;color:#64748b;font-size:14px;text-align:center;padding:40px;';
            container.appendChild(msgEl);
        }
        msgEl.innerHTML = `<span>⚠️ 缺少${dataType}数据，无法生成图表</span>`;
        msgEl.style.display = 'flex';
    }

    // 隐藏图表无数据提示（恢复显示 canvas）
    function hideChartNoData(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        canvas.style.display = 'block';
        const container = canvas.parentElement;
        if (container) {
            const msgEl = container.querySelector('.no-data-message');
            if (msgEl) msgEl.style.display = 'none';
        }
    }

    // ========== 工具提示 ==========

    function showTooltip(text, x, y) {
        const tooltip = document.getElementById('tooltip');
        if (!tooltip) return;

        tooltip.textContent = text;
        tooltip.classList.add('visible');

        if (x && y) {
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        } else {
            tooltip.style.left = '50%';
            tooltip.style.top = '20px';
            tooltip.style.transform = 'translateX(-50%)';
        }
    }

    function hideTooltip() {
        const tooltip = document.getElementById('tooltip');
        if (tooltip) {
            tooltip.classList.remove('visible');
        }
    }

    // ========== 数据加载 ==========

    // 加载分析数据
    async function loadAnalysisData(keyword, days = 30) {
        const cacheKey = `${keyword}_${days}`;

        // 检查缓存
        if (dataCache[cacheKey]) {
            console.log(`[Core] 使用缓存数据: ${cacheKey}`);
            return dataCache[cacheKey];
        }

        try {
            // 构建 URL 参数
            let url = `${API_BASE}/api/analyze/${encodeURIComponent(keyword)}?limit=10000&min_views=0`;

            // 添加日期过滤
            if (days > 0) {
                const { date_from, date_to } = getDateRange(days);
                if (date_from) url += `&date_from=${date_from}`;
                if (date_to) url += `&date_to=${date_to}`;
            }

            console.log(`[Core] 正在加载数据: ${url}`);

            // 显示加载进度提示
            showLoadingProgress('正在连接服务器...');

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 120s 超时

            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);

            showLoadingProgress('正在解析数据...');

            if (!response.ok) {
                throw new Error(`API 请求失败: ${response.status}`);
            }
            const data = await response.json();
            if (data.status === 'error') {
                console.warn('[Core] API 返回错误:', data.message);
                showLoadingError(data.message || '数据加载失败');
                return null;
            }

            // 缓存结果
            const result = data.result || data;
            result._timePeriod = days; // 标记时间段
            result._timePeriodLabel = getTimePeriodLabel(days);
            dataCache[cacheKey] = result;

            return result;
        } catch (error) {
            console.error('[Core] 加载分析数据失败:', error);
            if (error.name === 'AbortError') {
                showLoadingError('请求超时，服务器响应过慢，请稍后重试');
            } else {
                showLoadingError(`数据加载失败: ${error.message}`);
            }
            return null;
        }
    }

    // ========== 状态访问器 ==========

    function getCurrentKeyword() {
        return currentKeyword;
    }

    function setCurrentKeyword(keyword) {
        currentKeyword = keyword;
    }

    function getCurrentTimePeriod() {
        return currentTimePeriod;
    }

    function setCurrentTimePeriod(days) {
        currentTimePeriod = days;
    }

    function getAnalysisData() {
        return analysisData;
    }

    function setAnalysisData(data) {
        analysisData = data;
    }

    function getDataCache() {
        return dataCache;
    }

    function getAPIBase() {
        return API_BASE;
    }

    // ========== 导出 ==========
    exports.API_BASE = API_BASE;
    exports.getKeywordFromURL = getKeywordFromURL;
    exports.getTimePeriodFromURL = getTimePeriodFromURL;
    exports.getDateRange = getDateRange;
    exports.getTimePeriodLabel = getTimePeriodLabel;
    exports.formatNumber = formatNumber;
    exports.formatPercent = formatPercent;
    exports.formatDate = formatDate;
    exports.showLoadingProgress = showLoadingProgress;
    exports.hideLoadingBanner = hideLoadingBanner;
    exports.showLoadingError = showLoadingError;
    exports.showChartNoData = showChartNoData;
    exports.hideChartNoData = hideChartNoData;
    exports.showTooltip = showTooltip;
    exports.hideTooltip = hideTooltip;
    exports.loadAnalysisData = loadAnalysisData;

    // 状态访问器
    exports.getCurrentKeyword = getCurrentKeyword;
    exports.setCurrentKeyword = setCurrentKeyword;
    exports.getCurrentTimePeriod = getCurrentTimePeriod;
    exports.setCurrentTimePeriod = setCurrentTimePeriod;
    exports.getAnalysisData = getAnalysisData;
    exports.setAnalysisData = setAnalysisData;
    exports.getDataCache = getDataCache;
    exports.getAPIBase = getAPIBase;

    // 向后兼容：暴露到全局作用域
    window.getKeywordFromURL = getKeywordFromURL;
    window.getTimePeriodFromURL = getTimePeriodFromURL;
    window.formatNumber = formatNumber;
    window.showTooltip = showTooltip;
    window.hideTooltip = hideTooltip;
    window.showLoadingProgress = showLoadingProgress;
    window.hideLoadingBanner = hideLoadingBanner;
    window.showLoadingError = showLoadingError;
    window.showChartNoData = showChartNoData;
    window.hideChartNoData = hideChartNoData;

})(window.InsightCore);

console.log('[insight-core.js] 模块加载完成');
