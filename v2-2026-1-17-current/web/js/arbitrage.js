/**
 * 套利分析模块
 * 整合榜单 + 中心性分析 + 套利机会发现
 */

// API 基础地址
var ARBITRAGE_API_BASE = window.API_BASE || window.location.origin;

// 缓存数据
var arbitrageData = null;

/**
 * 格式化数字
 */
function formatArbitrageNumber(num) {
    if (!num || num === 0) return '0';
    if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
    if (num >= 10000) return (num / 10000).toFixed(1) + '万';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
}

/**
 * 获取排名样式
 */
function getArbitrageRankStyle(rank) {
    if (rank === 1) return 'background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #1f2937; font-weight: 700;';
    if (rank === 2) return 'background: linear-gradient(135deg, #94a3b8, #64748b); color: white; font-weight: 700;';
    if (rank === 3) return 'background: linear-gradient(135deg, #d97706, #b45309); color: white; font-weight: 700;';
    return 'background: #334155; color: #94a3b8;';
}

/**
 * 转义 HTML
 */
function escapeArbitrageHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 加载套利分析数据
 */
function loadArbitrageData() {
    return fetch(ARBITRAGE_API_BASE + '/api/arbitrage')
        .then(function(response) {
            if (!response.ok) throw new Error('API 请求失败: ' + response.status);
            return response.json();
        })
        .then(function(result) {
            if (result.status === 'error') {
                throw new Error(result.message);
            }
            arbitrageData = result.data;
            console.log('✓ 套利分析数据加载完成:', arbitrageData.stats);
            return arbitrageData;
        });
}

/**
 * 渲染中介中心性话题榜单
 */
function renderBetweennessTopics(topics) {
    var tbody = document.getElementById('betweennessTopicsTableBody');
    var countEl = document.getElementById('betweennessTopicsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = topics.length;

    if (!topics || topics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(topics.length, 50); i++) {
        var t = topics[i];
        var interestingnessStyle = t.interestingness > 1 ? 'color: #10b981; font-weight: 600;' :
                                   t.interestingness > 0.3 ? 'color: #f59e0b;' : 'color: #94a3b8;';

        html += '<tr class="leaderboard-row">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(t.rank) + '">' + t.rank + '</span></td>';
        html += '<td><span style="font-weight: 500;">' + escapeArbitrageHtml(t.topic) + '</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + t.betweenness.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + t.degree.toFixed(4) + '</td>';
        html += '<td style="text-align: right; ' + interestingnessStyle + '">' + t.interestingness.toFixed(2) + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(t.avg_views) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染中介中心性频道榜单
 */
function renderBetweennessChannels(channels) {
    var tbody = document.getElementById('betweennessChannelsTableBody');
    var countEl = document.getElementById('betweennessChannelsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = channels.length;

    if (!channels || channels.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(channels.length, 50); i++) {
        var c = channels[i];
        var channelUrl = c.channel_url || '#';
        var channelName = escapeArbitrageHtml(c.channel_name) || '未知频道';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + channelUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击访问频道">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(c.rank) + '">' + c.rank + '</span></td>';
        html += '<td><span class="channel-link">' + channelName + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + c.betweenness.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + c.degree.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #10b981;">' + c.topic_count + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(c.avg_views) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatArbitrageNumber(c.subscriber_count) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染中介中心性视频榜单
 */
function renderBetweennessVideos(videos) {
    var tbody = document.getElementById('betweennessVideosTableBody');
    var countEl = document.getElementById('betweennessVideosCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = videos.length;

    if (!videos || videos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(videos.length, 50); i++) {
        var v = videos[i];
        var videoUrl = v.video_url || '#';
        var title = escapeArbitrageHtml(v.title);
        if (title && title.length > 40) title = title.substring(0, 40) + '...';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + videoUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击观看视频">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(v.rank) + '">' + v.rank + '</span></td>';
        html += '<td><span class="video-link">' + title + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + v.betweenness.toFixed(4) + '</td>';
        html += '<td style="color: #94a3b8; font-size: 12px;">' + escapeArbitrageHtml(v.topic) + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(v.view_count) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatArbitrageNumber(v.subscriber_count) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染程度中心性话题榜单
 */
function renderDegreeTopics(topics) {
    var tbody = document.getElementById('degreeTopicsTableBody');
    var countEl = document.getElementById('degreeTopicsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = topics.length;

    if (!topics || topics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(topics.length, 50); i++) {
        var t = topics[i];

        html += '<tr class="leaderboard-row">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(t.rank) + '">' + t.rank + '</span></td>';
        html += '<td><span style="font-weight: 500;">' + escapeArbitrageHtml(t.topic) + '</span></td>';
        html += '<td style="text-align: right; color: #a855f7; font-weight: 600;">' + t.degree.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + t.betweenness.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #06b6d4;">' + t.video_count + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(t.avg_views) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染程度中心性频道榜单
 */
function renderDegreeChannels(channels) {
    var tbody = document.getElementById('degreeChannelsTableBody');
    var countEl = document.getElementById('degreeChannelsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = channels.length;

    if (!channels || channels.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(channels.length, 50); i++) {
        var c = channels[i];
        var channelUrl = c.channel_url || '#';
        var channelName = escapeArbitrageHtml(c.channel_name) || '未知频道';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + channelUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击访问频道">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(c.rank) + '">' + c.rank + '</span></td>';
        html += '<td><span class="channel-link">' + channelName + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right; color: #a855f7; font-weight: 600;">' + c.degree.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + c.betweenness.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #10b981;">' + c.topic_count + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(c.avg_views) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatArbitrageNumber(c.subscriber_count) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染程度中心性视频榜单
 */
function renderDegreeVideos(videos) {
    var tbody = document.getElementById('degreeVideosTableBody');
    var countEl = document.getElementById('degreeVideosCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = videos.length;

    if (!videos || videos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(videos.length, 50); i++) {
        var v = videos[i];
        var videoUrl = v.video_url || '#';
        var title = escapeArbitrageHtml(v.title);
        if (title && title.length > 40) title = title.substring(0, 40) + '...';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + videoUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击观看视频">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(v.rank) + '">' + v.rank + '</span></td>';
        html += '<td><span class="video-link">' + title + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right; color: #a855f7; font-weight: 600;">' + v.degree.toFixed(4) + '</td>';
        html += '<td style="color: #94a3b8; font-size: 12px;">' + escapeArbitrageHtml(v.topic) + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(v.view_count) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatArbitrageNumber(v.subscriber_count) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染套利机会视频榜单（高中介+低播放）
 */
function renderArbitrageVideos(videos) {
    var tbody = document.getElementById('arbitrageVideosTableBody');
    var countEl = document.getElementById('arbitrageVideosCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = videos.length;

    if (!videos || videos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(videos.length, 50); i++) {
        var v = videos[i];
        var videoUrl = v.video_url || '#';
        var title = escapeArbitrageHtml(v.title);
        if (title && title.length > 35) title = title.substring(0, 35) + '...';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + videoUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击观看视频">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(v.rank) + '">' + v.rank + '</span></td>';
        html += '<td><span class="video-link">' + title + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + v.betweenness.toFixed(4) + '</td>';
        html += '<td style="color: #94a3b8; font-size: 12px;">' + escapeArbitrageHtml(v.topic) + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(v.view_count) + '</td>';
        html += '<td style="text-align: center;"><span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">套利</span></td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染套利机会频道榜单（高中介+低粉丝）
 */
function renderArbitrageChannels(channels) {
    var tbody = document.getElementById('arbitrageChannelsTableBody');
    var countEl = document.getElementById('arbitrageChannelsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = channels.length;

    if (!channels || channels.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(channels.length, 50); i++) {
        var c = channels[i];
        var channelUrl = c.channel_url || '#';
        var channelName = escapeArbitrageHtml(c.channel_name) || '未知频道';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + channelUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击访问频道">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(c.rank) + '">' + c.rank + '</span></td>';
        html += '<td><span class="channel-link">' + channelName + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + c.betweenness.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #10b981;">' + c.topic_count + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatArbitrageNumber(c.subscriber_count) + '</td>';
        html += '<td style="text-align: center;"><span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">潜力</span></td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染套利机会话题榜单（高中介+低视频数）
 */
function renderArbitrageTopics(topics) {
    var tbody = document.getElementById('arbitrageTopicsTableBody');
    var countEl = document.getElementById('arbitrageTopicsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = topics.length;

    if (!topics || topics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(topics.length, 50); i++) {
        var t = topics[i];

        html += '<tr class="leaderboard-row">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(t.rank) + '">' + t.rank + '</span></td>';
        html += '<td><span style="font-weight: 500;">' + escapeArbitrageHtml(t.topic) + '</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + t.betweenness.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + t.video_count + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(t.avg_views) + '</td>';
        html += '<td style="text-align: center;"><span style="background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">蓝海</span></td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染套利机会标题词榜单（高中介+低使用频率）
 */
function renderArbitrageWords(words) {
    var tbody = document.getElementById('arbitrageWordsTableBody');
    var countEl = document.getElementById('arbitrageWordsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = words.length;

    if (!words || words.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(words.length, 50); i++) {
        var w = words[i];

        html += '<tr class="leaderboard-row">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(w.rank) + '">' + w.rank + '</span></td>';
        html += '<td><span style="font-weight: 500; color: #a855f7;">' + escapeArbitrageHtml(w.word) + '</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + w.betweenness.toFixed(4) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + w.count + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(w.avg_views) + '</td>';
        html += '<td style="text-align: center;"><span style="background: #8b5cf6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">关键词</span></td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染传统榜单 - 黑马频道
 */
function renderDarkHorseChannels(channels) {
    var tbody = document.getElementById('darkHorseChannelsTableBody');
    var countEl = document.getElementById('darkHorseChannelsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = channels.length;

    if (!channels || channels.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(channels.length, 50); i++) {
        var c = channels[i];
        var channelUrl = c.channel_url || '#';
        var channelName = escapeArbitrageHtml(c.channel_name) || '未知频道';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + channelUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击访问频道">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(c.rank) + '">' + c.rank + '</span></td>';
        html += '<td><span class="channel-link">' + channelName + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right;">' + c.video_count + '</td>';
        html += '<td style="text-align: right; color: #f97316; font-weight: 500;">' + formatArbitrageNumber(c.avg_views) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatArbitrageNumber(c.subscriber_count) + '</td>';
        html += '<td style="text-align: right;"><span style="color: #10b981; font-weight: 600;">' + c.dark_horse_score + 'x</span></td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染传统榜单 - 热门视频（按播放量）
 */
function renderTopVideosByViews(videos) {
    var tbody = document.getElementById('topVideosByViewsTableBody');
    var countEl = document.getElementById('topVideosByViewsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = videos.length;

    if (!videos || videos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(videos.length, 50); i++) {
        var v = videos[i];
        var videoUrl = v.video_url || '#';
        var title = escapeArbitrageHtml(v.title);

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + videoUrl + '\', \'_blank\')" style="cursor: pointer;">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(v.rank) + '">' + v.rank + '</span></td>';
        html += '<td><span class="video-link">' + title + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="color: #94a3b8; font-size: 12px;">' + escapeArbitrageHtml(v.channel_name) + '</td>';
        html += '<td style="text-align: right; color: #f97316; font-weight: 600;">' + formatArbitrageNumber(v.view_count) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatArbitrageNumber(v.like_count) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染传统榜单 - 频道（按粉丝数）
 */
function renderTopChannelsBySubs(channels) {
    var tbody = document.getElementById('topChannelsBySubsTableBody');
    var countEl = document.getElementById('topChannelsBySubsCount');

    if (!tbody) return;
    if (countEl) countEl.textContent = channels.length;

    if (!channels || channels.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(channels.length, 50); i++) {
        var c = channels[i];
        var channelUrl = c.channel_url || '#';
        var channelName = escapeArbitrageHtml(c.channel_name) || '未知频道';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + channelUrl + '\', \'_blank\')" style="cursor: pointer;">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getArbitrageRankStyle(c.rank) + '">' + c.rank + '</span></td>';
        html += '<td><span class="channel-link">' + channelName + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right; color: #a855f7; font-weight: 600;">' + formatArbitrageNumber(c.subscriber_count) + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatArbitrageNumber(c.avg_views) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + c.video_count + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 初始化套利分析模块
 */
function initArbitrageModule() {
    loadArbitrageData()
        .then(function(data) {
            // 渲染中介中心性榜单
            var betweenness = data.centrality_leaderboard.betweenness || {};
            renderBetweennessTopics(betweenness.topics || []);
            renderBetweennessChannels(betweenness.channels || []);
            renderBetweennessVideos(betweenness.videos || []);

            // 渲染程度中心性榜单
            var degree = data.centrality_leaderboard.degree || {};
            renderDegreeTopics(degree.topics || []);
            renderDegreeChannels(degree.channels || []);
            renderDegreeVideos(degree.videos || []);

            // 渲染套利机会榜单
            var arbitrage = data.arbitrage_opportunities || {};
            renderArbitrageVideos(arbitrage.high_betweenness_low_views_videos || []);
            renderArbitrageChannels(arbitrage.high_betweenness_low_subs_channels || []);
            renderArbitrageTopics(arbitrage.high_betweenness_low_videos_topics || []);
            renderArbitrageWords(arbitrage.high_betweenness_low_count_words || []);

            // 渲染传统榜单
            var traditional = data.traditional_leaderboard || {};
            renderDarkHorseChannels(traditional.dark_horse_channels || []);
            renderTopVideosByViews(traditional.top_videos_by_views || []);
            renderTopChannelsBySubs(traditional.top_channels_by_subs || []);

            // 更新统计信息
            var stats = data.stats || {};
            var statsEl = document.getElementById('arbitrageStats');
            if (statsEl) {
                statsEl.innerHTML = '话题 <span style="color: #06b6d4; font-weight: 600;">' + (stats.total_topics || 0) + '</span> · ' +
                    '频道 <span style="color: #f97316; font-weight: 600;">' + (stats.total_channels || 0) + '</span> · ' +
                    '视频 <span style="color: #a855f7; font-weight: 600;">' + (stats.total_videos || 0) + '</span>';
            }

            // 自动加载网络图（默认中介中心性视角）
            initNetworkGraph();

            // ========== 注册套利分析结论到信息报告 ==========
            if (typeof registerPatternConclusion === 'function') {
                // 子Tab1: 套利机会
                var arbVideos = arbitrage.high_betweenness_low_views_videos || [];
                var arbChannels = arbitrage.high_betweenness_low_subs_channels || [];
                var arbTopics = arbitrage.high_betweenness_low_videos_topics || [];
                var arbWords = arbitrage.high_betweenness_low_count_words || [];
                var arbParts = [];
                if (arbVideos.length > 0) arbParts.push('套利视频' + arbVideos.length + '个（Top1：' + escapeArbitrageHtml(arbVideos[0].title || '未知') + '，中介中心性' + arbVideos[0].betweenness.toFixed(4) + '）');
                if (arbChannels.length > 0) arbParts.push('高潜力频道' + arbChannels.length + '个（Top1：' + escapeArbitrageHtml(arbChannels[0].channel_name || '未知') + '）');
                if (arbTopics.length > 0) arbParts.push('蓝海话题' + arbTopics.length + '个（Top1：' + escapeArbitrageHtml(arbTopics[0].topic || '未知') + '）');
                if (arbWords.length > 0) arbParts.push('价值关键词' + arbWords.length + '个（Top1：' + escapeArbitrageHtml(arbWords[0].word || '未知') + '）');
                if (arbParts.length > 0) {
                    registerPatternConclusion('tab2', 'arb-opportunity', '套利机会发现',
                        '套利机会',
                        arbParts.join('；') + '。'
                    );
                }

                // 子Tab2: 中介中心性 Top50
                var betTopics = betweenness.topics || [];
                var betChannels = betweenness.channels || [];
                var betVideos = betweenness.videos || [];
                if (betTopics.length > 0) {
                    var topTopic = betTopics[0];
                    registerPatternConclusion('tab2', 'arb-betweenness', '中介中心性分析',
                        '中介中心性 Top50',
                        '话题Top1「' + escapeArbitrageHtml(topTopic.topic) + '」（中介' + topTopic.betweenness.toFixed(4) + '），频道Top1「' + escapeArbitrageHtml((betChannels[0] || {}).channel_name || '未知') + '」，视频Top1「' + escapeArbitrageHtml((betVideos[0] || {}).title || '未知') + '」。高中介节点是连接不同内容社群的桥梁。'
                    );
                }

                // 子Tab3: 程度中心性 Top50
                var degTopics = degree.topics || [];
                var degChannels = degree.channels || [];
                var degVideos = degree.videos || [];
                if (degTopics.length > 0) {
                    var topDegTopic = degTopics[0];
                    registerPatternConclusion('tab2', 'arb-degree', '程度中心性分析',
                        '程度中心性 Top50',
                        '话题Top1「' + escapeArbitrageHtml(topDegTopic.topic) + '」（程度' + topDegTopic.degree.toFixed(4) + '），频道Top1「' + escapeArbitrageHtml((degChannels[0] || {}).channel_name || '未知') + '」，视频Top1「' + escapeArbitrageHtml((degVideos[0] || {}).title || '未知') + '」。高程度节点是领域内最活跃的核心。'
                    );
                }

                // 子Tab4: 黑马频道
                var darkHorseList = traditional.dark_horse_channels || [];
                if (darkHorseList.length > 0) {
                    var topHorse = darkHorseList[0];
                    registerPatternConclusion('tab2', 'arb-darkhorse', '黑马频道发现',
                        '黑马频道',
                        '共' + darkHorseList.length + '个黑马频道。Top1「' + escapeArbitrageHtml(topHorse.channel_name || '未知') + '」订阅' + formatArbitrageNumber(topHorse.subscriber_count || 0) + '，黑马指数' + (topHorse.dark_horse_index || 0).toFixed(1) + '。低粉高播的频道值得研究其内容策略。'
                    );
                }

                // 子Tab5: 热门视频
                var topVideos = traditional.top_videos_by_views || [];
                if (topVideos.length > 0) {
                    var topV = topVideos[0];
                    registerPatternConclusion('tab2', 'arb-hotvideo', '热门视频排行',
                        '热门视频',
                        '共' + topVideos.length + '个热门视频。Top1「' + escapeArbitrageHtml(topV.title || '未知') + '」播放' + formatArbitrageNumber(topV.view_count || 0) + '，来自频道「' + escapeArbitrageHtml(topV.channel_name || '未知') + '」。'
                    );
                }

                // 子Tab6: 头部频道
                var topChannels = traditional.top_channels_by_subs || [];
                if (topChannels.length > 0) {
                    var topC = topChannels[0];
                    registerPatternConclusion('tab2', 'arb-topchannel', '头部频道排行',
                        '头部频道',
                        '共' + topChannels.length + '个头部频道。Top1「' + escapeArbitrageHtml(topC.channel_name || '未知') + '」粉丝' + formatArbitrageNumber(topC.subscriber_count || 0) + '，视频' + (topC.video_count || 0) + '个。'
                    );
                }

                // 刷新信息报告以包含新注册的结论
                if (typeof renderInfoReportFromConclusions === 'function') {
                    console.log('[套利分析] 结论注册完成，刷新信息报告');
                    renderInfoReportFromConclusions();
                }
            }
        })
        .catch(function(error) {
            console.error('套利分析数据加载失败:', error);
            // 显示错误信息到各个表格
            var tables = [
                'betweennessTopicsTableBody', 'betweennessChannelsTableBody', 'betweennessVideosTableBody',
                'degreeTopicsTableBody', 'degreeChannelsTableBody', 'degreeVideosTableBody',
                'arbitrageVideosTableBody', 'arbitrageChannelsTableBody',
                'darkHorseChannelsTableBody', 'topVideosByViewsTableBody', 'topChannelsBySubsTableBody'
            ];
            for (var i = 0; i < tables.length; i++) {
                var el = document.getElementById(tables[i]);
                if (el) {
                    el.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #f87171; padding: 40px;">加载失败: ' + error.message + '</td></tr>';
                }
            }
        });
}

// ==================== 网络图可视化部分 ====================

// 网络图状态管理
var NetworkViz = {
    // 当前展开的着色模式
    currentColorMode: null,  // 'betweenness' | 'degree' | 'arbitrage'

    // 当前网络类型
    currentNetworkType: 'topic',  // 'topic' | 'channel'

    // vis.js 网络图实例
    network: null,

    // 网络图数据缓存
    networkData: null,

    // 原始节点数据（用于重新着色）
    nodesDataset: null,
    edgesDataset: null
};

/**
 * 切换着色模式（点击三个卡片时触发）
 */
function toggleCentralityChart(colorMode) {
    var allCards = document.querySelectorAll('.centrality-card');

    // 更新卡片样式
    allCards.forEach(function(c) {
        var cardType = c.id.replace('Card', '');
        var checkMark = c.querySelector('.card-check');
        if (cardType === colorMode) {
            c.classList.add('active');
            c.style.borderWidth = '2px';
            c.style.borderColor = cardType === 'betweenness' ? 'rgba(6, 182, 212, 0.5)' :
                                  cardType === 'degree' ? 'rgba(59, 130, 246, 0.5)' :
                                  'rgba(249, 115, 22, 0.5)';
            c.style.background = cardType === 'betweenness' ? 'rgba(6, 182, 212, 0.15)' :
                                 cardType === 'degree' ? 'rgba(59, 130, 246, 0.15)' :
                                 'rgba(249, 115, 22, 0.15)';
            if (checkMark) checkMark.style.opacity = '1';
        } else {
            c.classList.remove('active');
            c.style.borderWidth = '1px';
            c.style.borderColor = cardType === 'betweenness' ? 'rgba(6, 182, 212, 0.3)' :
                                  cardType === 'degree' ? 'rgba(59, 130, 246, 0.3)' :
                                  'rgba(249, 115, 22, 0.3)';
            c.style.background = cardType === 'betweenness' ? 'rgba(6, 182, 212, 0.1)' :
                                 cardType === 'degree' ? 'rgba(59, 130, 246, 0.1)' :
                                 'rgba(249, 115, 22, 0.1)';
            if (checkMark) checkMark.style.opacity = '0';
        }
    });

    NetworkViz.currentColorMode = colorMode;

    // 更新图例
    updateNetworkLegend(colorMode);

    // 如果网络图数据已加载，重新着色；否则加载数据
    if (NetworkViz.networkData) {
        applyColorMode(colorMode);
        updateCardTop3();
    } else {
        loadNetworkGraph();
    }
}

/**
 * 初始化网络图（页面加载时自动调用）
 */
function initNetworkGraph() {
    NetworkViz.currentColorMode = 'betweenness';
    loadNetworkGraph();
}

/**
 * 更新图例显示
 */
function updateNetworkLegend(colorMode) {
    document.getElementById('legendBetweenness').style.display = colorMode === 'betweenness' ? 'flex' : 'none';
    document.getElementById('legendDegree').style.display = colorMode === 'degree' ? 'flex' : 'none';
    document.getElementById('legendArbitrage').style.display = colorMode === 'arbitrage' ? 'flex' : 'none';
}

/**
 * 切换网络类型（话题/频道）
 */
function switchNetworkType(type) {
    if (NetworkViz.currentNetworkType === type) return;

    NetworkViz.currentNetworkType = type;

    // 更新按钮状态
    var buttons = document.querySelectorAll('.chart-view-btn[data-view]');
    buttons.forEach(function(btn) {
        if (btn.getAttribute('data-view') === type) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // 重新加载网络图
    NetworkViz.networkData = null;
    loadNetworkGraph();
}

/**
 * 更新网络图（节点数变化时）
 */
function updateNetworkGraph() {
    NetworkViz.networkData = null;
    loadNetworkGraph();
}

/**
 * 重置网络图视图
 */
function resetNetworkView() {
    if (NetworkViz.network) {
        NetworkViz.network.fit({
            animation: {
                duration: 500,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

/**
 * 加载网络图数据
 */
function loadNetworkGraph() {
    var loadingEl = document.getElementById('networkLoading');
    if (loadingEl) loadingEl.style.display = 'block';

    var nodeCount = document.getElementById('networkNodeCount');
    var maxNodes = nodeCount ? parseInt(nodeCount.value) : 50;

    fetch(ARBITRAGE_API_BASE + '/api/network-graph?graph_type=' + NetworkViz.currentNetworkType + '&max_nodes=' + maxNodes)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (loadingEl) loadingEl.style.display = 'none';

            if (data.status !== 'ok') {
                console.error('加载网络图失败:', data.message);
                return;
            }

            NetworkViz.networkData = data;
            renderNetworkGraph(data);

            if (NetworkViz.currentColorMode) {
                applyColorMode(NetworkViz.currentColorMode);
                updateCardTop3();
            }
        })
        .catch(function(error) {
            if (loadingEl) loadingEl.style.display = 'none';
            console.error('网络图请求失败:', error);
        });
}

/**
 * 渲染网络图
 */
function renderNetworkGraph(data) {
    var container = document.getElementById('networkGraphContainer');
    if (!container) return;

    // 准备节点数据
    var nodes = data.nodes.map(function(node) {
        return {
            id: node.id,
            label: node.label,
            title: createNodeTooltip(node),
            // 初始样式（后续通过 applyColorMode 覆盖）
            size: node.size,
            font: { color: '#e2e8f0', size: 11 },
            // 保存原始数据
            raw: node
        };
    });

    // 准备边数据
    var edges = data.edges.map(function(edge) {
        return {
            from: edge.from,
            to: edge.to,
            width: edge.width,
            color: { color: 'rgba(71, 85, 105, 0.5)', highlight: 'rgba(6, 182, 212, 0.8)' },
            smooth: { type: 'continuous' }
        };
    });

    // 创建 DataSet
    NetworkViz.nodesDataset = new vis.DataSet(nodes);
    NetworkViz.edgesDataset = new vis.DataSet(edges);

    // vis.js 配置
    var options = {
        nodes: {
            shape: 'dot',
            borderWidth: 2,
            shadow: true,
            font: {
                color: '#e2e8f0',
                size: 11,
                face: 'system-ui, -apple-system, sans-serif'
            }
        },
        edges: {
            smooth: {
                type: 'continuous',
                forceDirection: 'none'
            }
        },
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 100,
                springConstant: 0.08,
                damping: 0.4,
                avoidOverlap: 0.5
            },
            stabilization: {
                enabled: true,
                iterations: 200,
                updateInterval: 25
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 300,
            hideEdgesOnDrag: false,
            hideEdgesOnZoom: false,
            zoomView: true,           // 允许滚轮缩放
            dragView: true,           // 允许拖拽画布
            dragNodes: true,          // 允许拖拽节点
            navigationButtons: false,
            keyboard: false,
            zoomSpeed: 0.3            // 降低缩放速度，更平滑
        }
    };

    // 销毁旧的网络图
    if (NetworkViz.network) {
        NetworkViz.network.destroy();
    }

    // 创建网络图
    NetworkViz.network = new vis.Network(
        container,
        { nodes: NetworkViz.nodesDataset, edges: NetworkViz.edgesDataset },
        options
    );

    // 稳定后停止物理模拟
    NetworkViz.network.on('stabilizationIterationsDone', function() {
        NetworkViz.network.setOptions({ physics: { enabled: false } });
    });

    // 点击节点高亮相关边
    NetworkViz.network.on('selectNode', function(params) {
        var nodeId = params.nodes[0];
        highlightConnectedEdges(nodeId);
    });

    NetworkViz.network.on('deselectNode', function() {
        resetEdgeColors();
    });
}

/**
 * 创建节点的 tooltip 内容（返回 DOM 元素，vis.js 会正确渲染）
 */
function createNodeTooltip(node) {
    // 创建 DOM 元素，vis.js 会正确渲染 DOM 元素作为 tooltip
    var container = document.createElement('div');
    container.style.cssText = 'background: #1e293b; padding: 10px; border-radius: 6px; color: #e2e8f0; font-size: 12px; max-width: 250px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);';

    // 标题
    var title = document.createElement('div');
    title.style.cssText = 'font-weight: bold; margin-bottom: 6px; color: #f1f5f9;';
    title.textContent = node.label;
    container.appendChild(title);

    // 完整名称（如果有）
    if (node.full_name && node.full_name !== node.label) {
        var fullName = document.createElement('div');
        fullName.style.cssText = 'color: #94a3b8; margin-bottom: 6px; font-size: 11px;';
        fullName.textContent = node.full_name;
        container.appendChild(fullName);
    }

    // 数据网格
    var grid = document.createElement('div');
    grid.style.cssText = 'display: grid; grid-template-columns: 1fr 1fr; gap: 4px;';

    // 添加数据行的辅助函数
    function addRow(label, value, color) {
        var labelDiv = document.createElement('div');
        labelDiv.textContent = label;
        grid.appendChild(labelDiv);

        var valueDiv = document.createElement('div');
        valueDiv.style.color = color || '#e2e8f0';
        valueDiv.textContent = value;
        grid.appendChild(valueDiv);
    }

    addRow('桥梁指数:', node.betweenness.toFixed(4), '#06b6d4');
    addRow('热门指数:', node.degree.toFixed(4), '#a855f7');
    addRow('有趣度:', node.interestingness.toFixed(4), '#f97316');

    if (node.video_count) {
        addRow('视频数:', node.video_count);
    }
    if (node.total_views) {
        addRow('总播放:', formatArbitrageNumber(node.total_views));
    }
    if (node.channel_count) {
        addRow('频道数:', node.channel_count);
    }
    if (node.subscriber_count) {
        addRow('订阅数:', formatArbitrageNumber(node.subscriber_count));
    }

    container.appendChild(grid);
    return container;
}

/**
 * 应用着色模式
 */
function applyColorMode(colorMode) {
    if (!NetworkViz.nodesDataset || !NetworkViz.networkData) return;

    var nodes = NetworkViz.networkData.nodes;
    var maxBetweenness = NetworkViz.networkData.stats.max_betweenness || 1;
    var maxDegree = NetworkViz.networkData.stats.max_degree || 1;

    // 计算平均值用于套利模式
    var avgViews = 0;
    nodes.forEach(function(n) { avgViews += n.total_views || 0; });
    avgViews = avgViews / nodes.length;

    var updates = nodes.map(function(node) {
        var color, borderColor, size;

        if (colorMode === 'betweenness') {
            // 中介中心性着色：热力图 红-橙-黄-灰
            var intensity = node.betweenness / maxBetweenness;
            if (intensity > 0.7) {
                // TOP 桥梁 - 深红
                color = 'rgba(239, 68, 68, 0.95)';
                borderColor = 'rgba(220, 38, 38, 1)';
                size = 22 + intensity * 15;
            } else if (intensity > 0.4) {
                // 重要桥梁 - 橙色
                color = 'rgba(249, 115, 22, 0.9)';
                borderColor = 'rgba(234, 88, 12, 1)';
                size = 16 + intensity * 12;
            } else if (intensity > 0.15) {
                // 中等桥梁 - 黄色
                color = 'rgba(234, 179, 8, 0.85)';
                borderColor = 'rgba(202, 138, 4, 1)';
                size = 12 + intensity * 10;
            } else {
                // 边缘节点 - 灰色
                color = 'rgba(100, 116, 139, 0.6)';
                borderColor = 'rgba(71, 85, 105, 0.8)';
                size = 8 + intensity * 8;
            }

        } else if (colorMode === 'degree') {
            // 程度中心性着色：多色渐变 紫色-蓝色-青色-灰色
            var intensity = node.degree / maxDegree;
            if (intensity > 0.7) {
                // 超级枢纽 - 紫色
                color = 'rgba(147, 51, 234, 0.95)';
                borderColor = 'rgba(126, 34, 206, 1)';
                size = 22 + intensity * 15;
            } else if (intensity > 0.4) {
                // 热门枢纽 - 蓝色
                color = 'rgba(59, 130, 246, 0.9)';
                borderColor = 'rgba(37, 99, 235, 1)';
                size = 16 + intensity * 12;
            } else if (intensity > 0.15) {
                // 活跃节点 - 青色
                color = 'rgba(34, 211, 238, 0.85)';
                borderColor = 'rgba(6, 182, 212, 1)';
                size = 12 + intensity * 10;
            } else {
                // 边缘节点 - 灰色
                color = 'rgba(100, 116, 139, 0.6)';
                borderColor = 'rgba(71, 85, 105, 0.8)';
                size = 8 + intensity * 8;
            }

        } else if (colorMode === 'arbitrage') {
            // 套利着色：红色 = 高中介+低热度，绿色 = 已饱和
            var normalizedBetweenness = node.betweenness / maxBetweenness;
            var normalizedPopularity = Math.min(1, (node.total_views || 0) / Math.max(avgViews, 1));

            // 套利得分 = 高桥梁 + 低热度
            var arbitrageScore = normalizedBetweenness * (1 - normalizedPopularity * 0.7);

            if (arbitrageScore > 0.5) {
                // 高套利机会 - 红色
                color = 'rgba(239, 68, 68, 0.9)';
                borderColor = 'rgba(239, 68, 68, 1)';
            } else if (arbitrageScore > 0.25) {
                // 中等机会 - 橙色
                color = 'rgba(249, 115, 22, 0.8)';
                borderColor = 'rgba(249, 115, 22, 1)';
            } else if (normalizedPopularity > 0.5) {
                // 已充分利用 - 绿色
                color = 'rgba(34, 197, 94, 0.7)';
                borderColor = 'rgba(34, 197, 94, 0.9)';
            } else {
                // 一般 - 灰色
                color = 'rgba(100, 116, 139, 0.6)';
                borderColor = 'rgba(100, 116, 139, 0.8)';
            }
            size = 10 + arbitrageScore * 25;  // 套利得分越高，节点越大
        }

        return {
            id: node.id,
            color: {
                background: color,
                border: borderColor,
                highlight: {
                    background: color,
                    border: '#fff'
                },
                hover: {
                    background: color,
                    border: '#fff'
                }
            },
            size: size
        };
    });

    NetworkViz.nodesDataset.update(updates);
}

/**
 * 高亮连接的边
 */
function highlightConnectedEdges(nodeId) {
    if (!NetworkViz.edgesDataset) return;

    var edges = NetworkViz.edgesDataset.get();
    var updates = edges.map(function(edge) {
        var isConnected = edge.from === nodeId || edge.to === nodeId;
        return {
            id: edge.id,
            color: {
                color: isConnected ? 'rgba(6, 182, 212, 0.8)' : 'rgba(71, 85, 105, 0.2)',
                highlight: 'rgba(6, 182, 212, 0.9)'
            },
            width: isConnected ? edge.width * 1.5 : edge.width * 0.5
        };
    });
    NetworkViz.edgesDataset.update(updates);
}

/**
 * 重置边的颜色
 */
function resetEdgeColors() {
    if (!NetworkViz.edgesDataset || !NetworkViz.networkData) return;

    var updates = NetworkViz.networkData.edges.map(function(edge) {
        return {
            id: edge.from + '-' + edge.to,  // vis.js 的边 id 可能不同，这里需要注意
            color: { color: 'rgba(71, 85, 105, 0.5)', highlight: 'rgba(6, 182, 212, 0.8)' },
            width: edge.width
        };
    });

    // 由于边的 id 可能不匹配，我们重新获取所有边并更新
    var existingEdges = NetworkViz.edgesDataset.get();
    var resetUpdates = existingEdges.map(function(edge, index) {
        var originalEdge = NetworkViz.networkData.edges[index] || { width: 1 };
        return {
            id: edge.id,
            color: { color: 'rgba(71, 85, 105, 0.5)', highlight: 'rgba(6, 182, 212, 0.8)' },
            width: originalEdge.width || 1
        };
    });
    NetworkViz.edgesDataset.update(resetUpdates);
}

/**
 * 更新网络图 TOP 5 列表
 */
function updateNetworkTopList(colorMode) {
    var container = document.getElementById('networkTopItems');
    var titleEl = document.getElementById('topListTitle');
    if (!container || !NetworkViz.networkData) return;

    var nodes = NetworkViz.networkData.nodes.slice();  // 复制数组

    // 根据着色模式排序
    var sortKey, title;
    if (colorMode === 'betweenness') {
        sortKey = 'betweenness';
        title = 'TOP 5 桥梁' + (NetworkViz.currentNetworkType === 'topic' ? '话题' : '频道');
    } else if (colorMode === 'degree') {
        sortKey = 'degree';
        title = 'TOP 5 热门' + (NetworkViz.currentNetworkType === 'topic' ? '话题' : '频道');
    } else {
        sortKey = 'interestingness';
        title = 'TOP 5 套利机会';
    }

    if (titleEl) titleEl.textContent = title;

    nodes.sort(function(a, b) { return b[sortKey] - a[sortKey]; });
    var top5 = nodes.slice(0, 5);

    var html = '';
    top5.forEach(function(node, index) {
        var rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        var name = node.label || node.id;
        var value = node[sortKey].toFixed(4);

        // 点击时聚焦到该节点
        html += '<div class="top-item" onclick="focusNode(\'' + node.id + '\')" style="cursor: pointer;">';
        html += '<span class="rank ' + rankClass + '">' + (index + 1) + '</span>';
        html += '<span class="name">' + escapeArbitrageHtml(name) + '</span>';
        html += '<span class="value">' + value + '</span>';
        html += '</div>';
    });

    container.innerHTML = html || '<span style="color: #64748b;">暂无数据</span>';
}

/**
 * 更新三个卡片中的 TOP3 列表
 */
function updateCardTop3() {
    if (!NetworkViz.networkData) return;

    var nodes = NetworkViz.networkData.nodes;

    // 中介中心性 TOP3
    var byBetweenness = nodes.slice().sort(function(a, b) { return b.betweenness - a.betweenness; }).slice(0, 3);
    var betweennessEl = document.getElementById('betweennessTop3');
    if (betweennessEl) {
        betweennessEl.innerHTML = byBetweenness.map(function(n, i) {
            return '<span style="color: ' + (i === 0 ? '#ef4444' : i === 1 ? '#f97316' : '#eab308') + ';">' + (i + 1) + '.' + n.label + '</span>';
        }).join(' ');
    }

    // 程度中心性 TOP3
    var byDegree = nodes.slice().sort(function(a, b) { return b.degree - a.degree; }).slice(0, 3);
    var degreeEl = document.getElementById('degreeTop3');
    if (degreeEl) {
        degreeEl.innerHTML = byDegree.map(function(n, i) {
            return '<span style="color: ' + (i === 0 ? '#7c3aed' : i === 1 ? '#a855f7' : '#c084fc') + ';">' + (i + 1) + '.' + n.label + '</span>';
        }).join(' ');
    }

    // 套利机会 TOP3（高中介 + 低热度）
    var avgViews = 0;
    nodes.forEach(function(n) { avgViews += n.total_views || 0; });
    avgViews = avgViews / nodes.length;
    var maxBetweenness = NetworkViz.networkData.stats.max_betweenness || 1;

    var withScore = nodes.map(function(n) {
        var normalizedBetweenness = n.betweenness / maxBetweenness;
        var normalizedPopularity = Math.min(1, (n.total_views || 0) / Math.max(avgViews, 1));
        n.arbitrageScore = normalizedBetweenness * (1 - normalizedPopularity * 0.7);
        return n;
    });
    var byArbitrage = withScore.sort(function(a, b) { return b.arbitrageScore - a.arbitrageScore; }).slice(0, 3);
    var arbitrageEl = document.getElementById('arbitrageTop3');
    if (arbitrageEl) {
        arbitrageEl.innerHTML = byArbitrage.map(function(n, i) {
            return '<span style="color: ' + (i === 0 ? '#ef4444' : i === 1 ? '#f97316' : '#fbbf24') + ';">' + (i + 1) + '.' + n.label + '</span>';
        }).join(' ');
    }
}

/**
 * 聚焦到指定节点
 */
function focusNode(nodeId) {
    if (!NetworkViz.network) return;

    NetworkViz.network.focus(nodeId, {
        scale: 1.5,
        animation: {
            duration: 500,
            easingFunction: 'easeInOutQuad'
        }
    });

    NetworkViz.network.selectNodes([nodeId]);
    highlightConnectedEdges(nodeId);
}

// 页面加载时自动初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟加载，避免阻塞主要内容
    setTimeout(initArbitrageModule, 1000);
});

// 如果页面已经加载完成，直接初始化
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initArbitrageModule, 1000);
}
