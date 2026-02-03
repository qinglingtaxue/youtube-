/**
 * 榜单标签页功能模块
 * 提供黑马频道、热门视频、热门话题榜单展示（表格形式）
 */

// API 基础地址
var LEADERBOARD_API_BASE = window.API_BASE || window.location.origin;

/**
 * 格式化数字（播放量等）
 */
function formatLeaderboardNumber(num) {
    if (!num || num === 0) return '0';
    if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
    if (num >= 10000) return (num / 10000).toFixed(1) + '万';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
}

/**
 * 获取排名样式
 */
function getRankStyle(rank) {
    if (rank === 1) return 'background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #1f2937; font-weight: 700;';
    if (rank === 2) return 'background: linear-gradient(135deg, #94a3b8, #64748b); color: white; font-weight: 700;';
    if (rank === 3) return 'background: linear-gradient(135deg, #d97706, #b45309); color: white; font-weight: 700;';
    return 'background: #334155; color: #94a3b8;';
}

/**
 * 转义 HTML 特殊字符
 */
function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 渲染黑马频道表格
 */
function renderDarkHorseTable(channels) {
    var tbody = document.getElementById('darkHorseTableBody');
    var countEl = document.getElementById('darkHorseCount');

    if (!tbody) return;

    if (countEl) countEl.textContent = channels.length;

    if (!channels || channels.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < channels.length; i++) {
        var ch = channels[i];
        var channelUrl = ch.channel_url || '#';
        var channelName = escapeHtml(ch.channel_name) || '未知频道';

        html += '<tr class="leaderboard-row" onclick="window.open(\'' + channelUrl + '\', \'_blank\')" style="cursor: pointer;" title="点击访问频道">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getRankStyle(ch.rank) + '">' + ch.rank + '</span></td>';
        html += '<td><span class="channel-link">' + channelName + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td style="text-align: right;">' + ch.video_count + '</td>';
        html += '<td style="text-align: right; color: #f97316; font-weight: 500;">' + formatLeaderboardNumber(ch.avg_views) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatLeaderboardNumber(ch.subscriber_count) + '</td>';
        html += '<td style="text-align: right;"><span style="color: #10b981; font-weight: 600;">' + ch.dark_horse_score + 'x</span></td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染热门视频表格
 */
function renderTopVideosTable(videos) {
    var tbody = document.getElementById('topVideosTableBody');
    var countEl = document.getElementById('topVideosCount');

    if (!tbody) return;

    if (countEl) countEl.textContent = videos.length;

    if (!videos || videos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < videos.length; i++) {
        var v = videos[i];
        var videoUrl = v.video_url || '#';
        var title = escapeHtml(v.title) || '未知视频';
        var channelName = escapeHtml(v.channel_name) || '未知';
        var channelUrl = v.channel_url || '#';

        html += '<tr class="leaderboard-row" style="cursor: pointer;">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getRankStyle(v.rank) + '">' + v.rank + '</span></td>';
        html += '<td onclick="window.open(\'' + videoUrl + '\', \'_blank\')" title="点击观看视频"><span class="video-link">' + title + '</span> <span style="color: #64748b; font-size: 11px;">↗</span></td>';
        html += '<td onclick="window.open(\'' + channelUrl + '\', \'_blank\')" title="点击访问频道"><span class="channel-link" style="color: #94a3b8;">' + channelName + '</span></td>';
        html += '<td style="text-align: right; color: #f97316; font-weight: 600;">' + formatLeaderboardNumber(v.view_count) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatLeaderboardNumber(v.like_count) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatLeaderboardNumber(v.comment_count) + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 渲染热门话题表格
 */
function renderTopTopicsTable(topics) {
    var tbody = document.getElementById('topTopicsTableBody');
    var countEl = document.getElementById('topTopicsCount');

    if (!tbody) return;

    if (countEl) countEl.textContent = topics.length;

    if (!topics || topics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    var html = '';
    for (var i = 0; i < topics.length; i++) {
        var t = topics[i];
        var topicName = escapeHtml(t.topic);

        html += '<tr class="leaderboard-row">';
        html += '<td><span style="display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 6px; font-size: 12px; ' + getRankStyle(t.rank) + '">' + t.rank + '</span></td>';
        html += '<td><span style="font-weight: 500;">' + topicName + '</span></td>';
        html += '<td style="text-align: right; color: #06b6d4; font-weight: 600;">' + t.video_count + '</td>';
        html += '<td style="text-align: right; color: #f97316;">' + formatLeaderboardNumber(t.total_views) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + formatLeaderboardNumber(t.avg_views) + '</td>';
        html += '<td style="text-align: right; color: #64748b;">' + t.channel_count + '</td>';
        html += '</tr>';
    }
    tbody.innerHTML = html;
}

/**
 * 加载榜单数据
 */
function loadLeaderboardData() {
    fetch(LEADERBOARD_API_BASE + '/api/leaderboard')
        .then(function(response) {
            if (!response.ok) throw new Error('API 请求失败: ' + response.status);
            return response.json();
        })
        .then(function(result) {
            if (result.status === 'error') {
                console.error('榜单加载失败:', result.message);
                return;
            }

            var data = result.data;

            // 渲染各个榜单表格
            renderDarkHorseTable(data.dark_horse_channels || []);
            renderTopVideosTable(data.top_videos || []);
            renderTopTopicsTable(data.top_topics || []);

            console.log('✓ 榜单数据加载完成:', {
                黑马频道: (data.dark_horse_channels && data.dark_horse_channels.length) || 0,
                热门视频: (data.top_videos && data.top_videos.length) || 0,
                热门话题: (data.top_topics && data.top_topics.length) || 0
            });
        })
        .catch(function(error) {
            console.error('榜单数据加载失败:', error);
            var tbodies = ['darkHorseTableBody', 'topVideosTableBody', 'topTopicsTableBody'];
            for (var i = 0; i < tbodies.length; i++) {
                var el = document.getElementById(tbodies[i]);
                if (el) {
                    el.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #f87171; padding: 40px;">加载失败: ' + error.message + '</td></tr>';
                }
            }
        });
}

// 页面加载时自动加载榜单数据
document.addEventListener('DOMContentLoaded', function() {
    // 延迟加载榜单，避免阻塞主要内容
    setTimeout(loadLeaderboardData, 800);
});

// 如果页面已经加载完成，直接加载榜单
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(loadLeaderboardData, 800);
}
