/**
 * creator-action.js
 * 创作者行动中心页面的专用逻辑
 * 复用 insight.js 中的数据加载和图表渲染函数
 */

// 初始化创作者行动中心
async function initCreatorAction(keyword) {
    try {
        // 加载数据（复用 insight.js 的函数）
        const data = await loadAnalysisData(keyword);
        if (!data) {
            console.error('无法加载数据');
            return;
        }

        // 渲染各板块
        renderTopicDecision(data);
        renderContentCreation(data);
        renderChannelOperation(data);
        renderUserInsight(data);

    } catch (error) {
        console.error('初始化失败:', error);
    }
}

// ========== Tab 1: 选题决策 ==========

function renderTopicDecision(data) {
    // 复用 insight.js 中已有的渲染函数
    if (typeof renderLifecycleAnalysis === 'function') {
        renderLifecycleAnalysis(data);
    }
    if (typeof renderTopicMonopoly === 'function') {
        renderTopicMonopoly(data);
    }
    if (typeof renderContentTypeAnalysis === 'function') {
        renderContentTypeAnalysis(data);
    }
}

// ========== Tab 2: 创作与发布 ==========

function renderContentCreation(data) {
    // 复用 insight.js 中已有的渲染函数
    if (typeof renderDurationAnalysis === 'function') {
        renderDurationAnalysis(data);
    }
    if (typeof renderTitleFeatureAnalysis === 'function') {
        renderTitleFeatureAnalysis(data);
    }
    if (typeof renderWeekdayAnalysis === 'function') {
        renderWeekdayAnalysis(data);
    }
}

// ========== Tab 3: 频道运营 ==========

function renderChannelOperation(data) {
    // 复用 insight.js 中已有的渲染函数
    if (typeof renderStabilityAnalysis === 'function') {
        renderStabilityAnalysis(data);
    }
    if (typeof renderDarkHorseAnalysis === 'function') {
        renderDarkHorseAnalysis(data);
    }
}

// ========== Tab 4: 用户洞察 ==========

async function renderUserInsight(data) {
    const keyword = getKeywordFromURL();
    const API_BASE = window.location.origin;

    console.log('[CreatorAction] 正在从 API 加载用户洞察数据...');

    try {
        const url = `${API_BASE}/api/user-insights/${encodeURIComponent(keyword)}`;
        const response = await fetch(url);
        const result = await response.json();

        if (result.status === 'ok' && result.total_comments > 0) {
            console.log('[CreatorAction] ✓ 用户洞察数据加载成功:', result.total_comments, '条评论');

            // 更新样本量显示
            const sampleBadge = document.getElementById('hotwordsSample');
            if (sampleBadge) sampleBadge.textContent = `N = ${result.total_comments.toLocaleString()}`;

            // 渲染各模式
            renderHotwordsTableCreator(result.hotwords);
            renderWordCloudCreator(result.hotwords);
            renderHotwordsInsightCreator(result.hotwords, result.total_comments);

            // 渲染热门视频示例
            if (result.real_examples && result.real_examples.top_commented_videos) {
                renderHotVideosExamplesFromAPI(result.real_examples.top_commented_videos);
            } else if (data.videos && data.videos.length > 0) {
                renderHotVideosExamples(data.videos);
            }
        } else {
            console.warn('[CreatorAction] ⚠️ 暂无评论数据:', result.message || '');
            showNoCommentDataCreator();
        }
    } catch (error) {
        console.error('[CreatorAction] ✗ 加载用户洞察数据失败:', error);
        showNoCommentDataCreator();
    }
}

// 渲染热词表格（真实数据）
function renderHotwordsTableCreator(hotwords) {
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
}

// 渲染词云（真实数据）
function renderWordCloudCreator(hotwords) {
    const container = document.getElementById('wordCloud');
    if (!container || !hotwords?.length) return;

    const maxCount = hotwords[0]?.count || 1;
    const colors = ['#10b981', '#06b6d4', '#f59e0b', '#8b5cf6', '#ec4899'];

    container.innerHTML = hotwords.slice(0, 15).map((hw, i) => {
        const size = 12 + (hw.count / maxCount) * 24;
        return `<span style="font-size: ${size}px; color: ${colors[i % 5]}; padding: 4px 8px; display: inline-block;">${hw.word}</span>`;
    }).join('');
}

// 渲染洞察文字（真实数据）
function renderHotwordsInsightCreator(hotwords, totalComments) {
    const insightEl = document.getElementById('hotwordsInsight');
    if (!insightEl || !hotwords?.length) return;

    const contentEl = insightEl.querySelector('.chart-insight-content');
    if (!contentEl) return;

    // 分类统计
    const categoryStats = {};
    hotwords.slice(0, 10).forEach(hw => {
        categoryStats[hw.category] = (categoryStats[hw.category] || 0) + hw.count;
    });
    const topCategory = Object.entries(categoryStats).sort((a, b) => b[1] - a[1])[0];

    // 统计感谢类
    const thankWords = hotwords.filter(hw => ['感恩', '謝謝', '谢谢', '感謝', '感谢'].includes(hw.word));
    const thankTotal = thankWords.reduce((sum, hw) => sum + hw.count, 0);

    // 统计专家类
    const expertWords = hotwords.filter(hw => ['老師', '老师', '醫師', '医师'].includes(hw.word));
    const expertTotal = expertWords.reduce((sum, hw) => sum + hw.count, 0);

    contentEl.innerHTML = `
        <strong>感谢类词汇占绝对主导</strong>（共${thankTotal.toLocaleString()}次）→ 用户满意度极高<br>
        <strong>"老师/医师"高频出现</strong>（${expertTotal.toLocaleString()}次）→ 用户把创作者视为专家权威<br>
        <strong>"${hotwords[1]?.word || '分享'}"排名第二</strong>（${hotwords[1]?.count?.toLocaleString() || '-'}次）→ 内容有价值，用户愿意传播
    `;
}

// 显示无数据提示
function showNoCommentDataCreator() {
    const tbody = document.getElementById('hotwordsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#f59e0b;padding:20px;">⚠️ 暂无评论数据，请先运行: python3 scripts/fetch_comments.py</td></tr>';
    }
    const container = document.getElementById('wordCloud');
    if (container) {
        container.innerHTML = '<div style="color:#64748b;text-align:center;padding:20px;">暂无数据</div>';
    }
}

// 渲染热门视频示例（从 API 获取的真实数据）
function renderHotVideosExamplesFromAPI(videos) {
    const container = document.getElementById('hotVideosExamples');
    if (!container || !videos?.length) return;

    container.innerHTML = videos.map((v, i) => `
        <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #334155;">
            <span style="color: ${i < 3 ? '#f97316' : '#64748b'}; font-weight: 600; width: 24px;">${i + 1}</span>
            <a href="https://youtube.com/watch?v=${v.youtube_id}" target="_blank"
               style="color: #f1f5f9; text-decoration: none; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
               title="${v.title}">
                ${v.title.substring(0, 40)}${v.title.length > 40 ? '...' : ''}
            </a>
            <span style="color: #64748b; font-size: 12px;">${v.comments || 0} 评论</span>
        </div>
    `).join('');
}

// 渲染热门视频示例
function renderHotVideosExamples(videos) {
    const container = document.getElementById('hotVideosExamples');
    if (!container) return;

    // 按评论数排序，取前5
    const topVideos = [...videos]
        .filter(v => v.comment_count > 0)
        .sort((a, b) => b.comment_count - a.comment_count)
        .slice(0, 5);

    if (topVideos.length === 0) {
        container.innerHTML = '<p style="color: #64748b;">暂无评论数据</p>';
        return;
    }

    container.innerHTML = topVideos.map((v, i) => `
        <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #334155;">
            <span style="color: ${i < 3 ? '#f97316' : '#64748b'}; font-weight: 600; width: 24px;">${i + 1}</span>
            <a href="https://youtube.com/watch?v=${v.video_id}" target="_blank"
               style="color: #f1f5f9; text-decoration: none; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
               title="${v.title}">
                ${v.title.substring(0, 40)}${v.title.length > 40 ? '...' : ''}
            </a>
            <span style="color: #64748b; font-size: 12px;">${formatNumber(v.comment_count)} 评论</span>
        </div>
    `).join('');
}

// 格式化数字
function formatNumber(num) {
    if (!num) return '0';
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
}

// 标签页切换函数（如果 insight.js 中没有定义）
if (typeof switchPatternTab !== 'function') {
    function switchPatternTab(tabId) {
        // 移除所有 active
        document.querySelectorAll('.pattern-tab').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.pattern-tab-content').forEach(content => content.classList.remove('active'));

        // 添加 active
        const btn = document.querySelector(`[onclick="switchPatternTab('${tabId}')"]`);
        const content = document.getElementById(tabId);

        if (btn) btn.classList.add('active');
        if (content) content.classList.add('active');
    }
}

// 子标签页切换函数（如果 insight.js 中没有定义）
if (typeof switchSubPattern !== 'function') {
    function switchSubPattern(tabId, subId) {
        const tabContent = document.getElementById(tabId);
        if (!tabContent) return;

        // 移除该 tab 下所有 sub 的 active
        tabContent.querySelectorAll('.sub-pattern-tab').forEach(btn => btn.classList.remove('active'));
        tabContent.querySelectorAll('.sub-pattern-content').forEach(content => content.classList.remove('active'));

        // 添加 active
        const btn = tabContent.querySelector(`[onclick="switchSubPattern('${tabId}', '${subId}')"]`);
        const content = document.getElementById(`${tabId}-${subId}`);

        if (btn) btn.classList.add('active');
        if (content) content.classList.add('active');
    }
}

// 从 URL 获取关键词参数（如果 insight.js 中没有定义）
if (typeof getKeywordFromURL !== 'function') {
    function getKeywordFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('keyword') || '养生';
    }
}
