/**
 * 向高手学习模块
 * 提供高手排行榜展示和高手详情分析
 */

// API 基础地址
var MASTER_API_BASE = window.API_BASE || window.location.origin;

// 当前选中的高手数据
var selectedMaster = null;

// 高手列表数据缓存
var mastersData = null;

/**
 * 格式化数字
 */
function formatMasterNumber(num) {
    if (!num || num === 0) return '0';
    if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
    if (num >= 10000) return (num / 10000).toFixed(1) + '万';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
}

/**
 * 转义 HTML
 */
function escapeMasterHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 获取排名样式
 */
function getMasterRankStyle(rank) {
    if (rank === 1) return 'background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #1f2937;';
    if (rank === 2) return 'background: linear-gradient(135deg, #94a3b8, #64748b); color: white;';
    if (rank === 3) return 'background: linear-gradient(135deg, #d97706, #b45309); color: white;';
    return 'background: #334155; color: #94a3b8;';
}

/**
 * 加载高手数据（复用套利分析中的头部频道数据）
 */
function loadMastersData() {
    return fetch(MASTER_API_BASE + '/api/arbitrage')
        .then(function(response) {
            if (!response.ok) throw new Error('API 请求失败: ' + response.status);
            return response.json();
        })
        .then(function(result) {
            if (result.status === 'error') {
                throw new Error(result.message);
            }
            // 使用头部频道数据作为高手列表
            var traditional = result.data.traditional_leaderboard || {};
            mastersData = traditional.top_channels_by_subs || [];
            console.log('✓ 高手数据加载完成:', mastersData.length + '个频道');
            return mastersData;
        });
}

/**
 * 渲染高手排行榜
 */
function renderMastersList(masters) {
    var container = document.getElementById('mastersList');
    var countEl = document.getElementById('mastersCount');

    if (!container) return;
    if (countEl) countEl.textContent = masters.length;

    if (!masters || masters.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 40px;">暂无数据</div>';
        return;
    }

    var html = '';
    for (var i = 0; i < Math.min(masters.length, 50); i++) {
        var m = masters[i];
        var channelName = escapeMasterHtml(m.channel_name) || '未知频道';
        var isSelected = selectedMaster && selectedMaster.channel_id === m.channel_id;

        html += '<div class="master-item' + (isSelected ? ' selected' : '') + '" onclick="selectMaster(' + i + ')">';
        html += '<div class="master-rank" style="' + getMasterRankStyle(m.rank) + '">' + m.rank + '</div>';
        html += '<div class="master-info">';
        html += '<div class="master-name">' + channelName + '</div>';
        html += '<div class="master-stats">';
        html += '<span>' + formatMasterNumber(m.subscriber_count) + ' 订阅</span>';
        html += '<span>均播 ' + formatMasterNumber(m.avg_views) + '</span>';
        html += '</div>';
        html += '</div>';
        html += '</div>';
    }

    container.innerHTML = html;
}

/**
 * 选择高手并展示详情
 */
function selectMaster(index) {
    if (!mastersData || index >= mastersData.length) return;

    selectedMaster = mastersData[index];

    // 更新列表选中状态
    var items = document.querySelectorAll('.master-item');
    items.forEach(function(item, i) {
        if (i === index) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });

    // 显示加载状态
    var panel = document.getElementById('masterDetailPanel');
    if (panel) {
        panel.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 60px;">加载中...</div>';
    }

    // 调用 API 获取频道详情（真实数据）
    var channelId = selectedMaster.channel_id;
    if (channelId) {
        loadChannelDetail(channelId);
    } else {
        // 如果没有 channel_id，显示基本信息
        renderMasterDetailBasic(selectedMaster);
    }

    // 在移动端自动滚动到详情区域
    var detailPanel = document.getElementById('masterDetailPanel');
    if (detailPanel && window.innerWidth < 1024) {
        detailPanel.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * 加载频道详情（从 API 获取真实数据）
 */
function loadChannelDetail(channelId) {
    fetch(MASTER_API_BASE + '/api/channel-detail/' + encodeURIComponent(channelId))
        .then(function(response) {
            if (!response.ok) throw new Error('API 请求失败: ' + response.status);
            return response.json();
        })
        .then(function(result) {
            if (result.status === 'error') {
                throw new Error(result.message);
            }
            // 使用真实数据渲染详情
            renderMasterDetailReal(result.data);
        })
        .catch(function(error) {
            console.error('频道详情加载失败:', error);
            // 降级使用基本数据
            renderMasterDetailBasic(selectedMaster);
        });
}

/**
 * 渲染高手详情（基本数据，无 API）
 */
function renderMasterDetailBasic(master) {
    var panel = document.getElementById('masterDetailPanel');
    if (!panel) return;

    var channelName = escapeMasterHtml(master.channel_name) || '未知频道';
    var channelUrl = master.channel_url || '#';
    var efficiency = master.subscriber_count > 0 ? (master.avg_views / master.subscriber_count * 100).toFixed(1) : 0;

    var html = '<div class="detail-card">';
    html += '<div class="detail-header">';
    html += '<div><div class="detail-title">' + channelName + '</div>';
    html += '<div class="detail-subtitle">排名 #' + master.rank + ' · ' + formatMasterNumber(master.subscriber_count) + ' 订阅</div></div>';
    html += '<a href="' + channelUrl + '" target="_blank" class="channel-link-btn">访问频道 ↗</a>';
    html += '</div>';
    html += '<div class="detail-body">';
    html += '<div class="stats-grid">';
    html += '<div class="stat-item"><div class="stat-value highlight">' + formatMasterNumber(master.subscriber_count) + '</div><div class="stat-label">订阅数</div></div>';
    html += '<div class="stat-item"><div class="stat-value">' + formatMasterNumber(master.avg_views) + '</div><div class="stat-label">均播</div></div>';
    html += '<div class="stat-item"><div class="stat-value">' + (master.video_count || '--') + '</div><div class="stat-label">视频数</div></div>';
    html += '<div class="stat-item"><div class="stat-value">' + efficiency + '%</div><div class="stat-label">播放效率</div></div>';
    html += '</div>';
    html += '<div class="why-study-box"><div class="why-study-title">提示</div>';
    html += '<div class="why-study-text">暂无详细数据，请确保数据库中有该频道的视频信息。</div></div>';
    html += '</div></div>';

    panel.innerHTML = html;
}

/**
 * 渲染高手详情（使用 API 真实数据）
 */
function renderMasterDetailReal(data) {
    var panel = document.getElementById('masterDetailPanel');
    if (!panel) return;

    var info = data.channel_info || {};
    var videos = data.videos || [];
    var topicDist = data.topic_distribution || [];
    var durationDist = data.duration_distribution || [];
    var growthTrajectory = data.growth_trajectory || [];
    var insights = data.learning_insights || {};

    var channelName = escapeMasterHtml(info.channel_name) || '未知频道';
    var channelUrl = info.channel_url || '#';
    var efficiency = info.efficiency || 0;
    var subscriberFormatted = formatMasterNumber(info.subscriber_count);
    var avgViewsFormatted = formatMasterNumber(info.avg_views);

    var html = '';

    // ========== 基本信息卡片 ==========
    html += '<div class="detail-card">';
    html += '<div class="detail-header">';
    html += '<div><div class="detail-title">' + channelName + '</div>';
    html += '<div class="detail-subtitle">' + subscriberFormatted + ' 订阅 · ' + (info.total_videos || 0) + ' 个视频</div></div>';
    html += '<a href="' + channelUrl + '" target="_blank" class="channel-link-btn">访问频道 ↗</a>';
    html += '</div>';
    html += '<div class="detail-body">';

    // 核心数据网格
    html += '<div class="stats-grid">';
    html += '<div class="stat-item"><div class="stat-value highlight">' + subscriberFormatted + '</div><div class="stat-label">订阅数</div></div>';
    html += '<div class="stat-item"><div class="stat-value">' + avgViewsFormatted + '</div><div class="stat-label">均播</div></div>';
    html += '<div class="stat-item"><div class="stat-value">' + (info.total_videos || 0) + '</div><div class="stat-label">视频数</div></div>';
    html += '<div class="stat-item"><div class="stat-value">' + efficiency + '%</div><div class="stat-label">播放效率</div></div>';
    html += '</div>';

    // 为什么值得研究（使用 API 返回的洞察）
    var whyStudy = insights.why_study || [];
    html += '<div class="why-study-box">';
    html += '<div class="why-study-title">为什么值得研究？</div>';
    html += '<div class="why-study-text">';
    if (whyStudy.length > 0) {
        for (var w = 0; w < whyStudy.length; w++) {
            html += '<p style="margin: 4px 0;">' + escapeMasterHtml(whyStudy[w]) + '</p>';
        }
    } else {
        html += '研究其内容策略和增长路径，可以为新人提供可复制的经验。';
    }
    html += '</div></div>';
    html += '</div></div>';

    // ========== 成长轨迹（真实数据） ==========
    if (growthTrajectory.length > 0) {
        html += '<div class="detail-card">';
        html += '<div class="detail-header"><div class="detail-title">成长轨迹</div></div>';
        html += '<div class="detail-body"><div class="timeline">';
        for (var g = 0; g < growthTrajectory.length; g++) {
            var phase = growthTrajectory[g];
            html += '<div class="timeline-item">';
            html += '<div class="timeline-dot ' + (g === growthTrajectory.length - 1 ? 'current' : 'milestone') + '"></div>';
            html += '<div class="timeline-date">' + escapeMasterHtml(phase.phase || phase.date) + '</div>';
            html += '<div class="timeline-content">';
            html += '<div class="timeline-title">' + escapeMasterHtml(phase.milestone || phase.title) + '</div>';
            html += '<div class="timeline-desc">' + escapeMasterHtml(phase.data || phase.desc || '') + '</div>';
            html += '</div></div>';
        }
        html += '</div></div></div>';
    }

    // ========== 内容结构分析（真实话题分布） ==========
    if (topicDist.length > 0) {
        html += '<div class="detail-card">';
        html += '<div class="detail-header"><div class="detail-title">内容结构分析</div><div class="detail-subtitle">基于 ' + (info.total_videos || 0) + ' 个视频的真实数据</div></div>';
        html += '<div class="detail-body">';
        html += '<div class="content-structure"><div class="structure-body"><div class="topic-list">';

        var maxCount = topicDist[0] ? topicDist[0].count : 1;
        for (var t = 0; t < Math.min(topicDist.length, 6); t++) {
            var topic = topicDist[t];
            var barWidth = Math.max(10, (topic.count / maxCount) * 100);
            var badge = topic.badge || '';

            html += '<div class="topic-item ' + badge.toLowerCase() + '">';
            html += '<div class="topic-bar" style="width: ' + barWidth + '%"></div>';
            html += '<div class="topic-info">';
            html += '<span class="topic-name">' + escapeMasterHtml(topic.topic) + '</span>';
            if (badge) {
                html += '<span class="topic-badge ' + badge.toLowerCase() + '">' + badge + '</span>';
            }
            html += '</div>';
            html += '<div class="topic-stats">';
            html += '<span class="topic-count">' + topic.count + '个视频</span>';
            html += '<span class="topic-ratio">' + topic.percentage + '%</span>';
            html += '<span class="topic-views">贡献 ' + topic.contribution + '% 播放量</span>';
            html += '</div></div>';
        }
        html += '</div>';

        // 洞察提示
        if (topicDist.length > 0) {
            var mainTopic = topicDist[0];
            html += '<div class="topic-insight"><div class="insight-icon">💡</div>';
            html += '<div class="insight-text">主力话题「' + escapeMasterHtml(mainTopic.topic) + '」贡献了 ' + mainTopic.contribution + '% 的播放量，建议新人从这个验证过的方向切入。</div></div>';
        }
        html += '</div></div></div></div>';
    }

    // ========== 成功模式总结（API 返回） ==========
    var patterns = insights.success_patterns || [];
    if (patterns.length > 0) {
        html += '<div class="detail-card">';
        html += '<div class="detail-header"><div class="detail-title">成功模式总结</div></div>';
        html += '<div class="detail-body"><div class="pattern-summary">';
        for (var p = 0; p < patterns.length; p++) {
            var pattern = patterns[p];
            html += '<div class="pattern-item">';
            html += '<div class="pattern-number">' + (p + 1) + '</div>';
            html += '<div class="pattern-content">';
            html += '<div class="pattern-title">' + escapeMasterHtml(pattern.title) + '</div>';
            html += '<div class="pattern-desc">' + escapeMasterHtml(pattern.desc) + '</div>';
            html += '<div class="pattern-evidence">证据：' + escapeMasterHtml(pattern.evidence) + '</div>';
            html += '</div></div>';
        }
        html += '</div></div></div>';
    }

    // ========== 新人可学习的路径（API 返回） ==========
    var learningPath = insights.learning_path || [];
    var actions = insights.actions || {};
    if (learningPath.length > 0) {
        html += '<div class="detail-card">';
        html += '<div class="detail-header"><div class="detail-title">新人可学习的路径</div></div>';
        html += '<div class="detail-body"><div class="learning-path">';
        for (var l = 0; l < learningPath.length; l++) {
            html += '<div class="learning-step">';
            html += '<div class="step-number">第' + (l + 1) + '步</div>';
            html += '<div class="step-content">' + escapeMasterHtml(learningPath[l]) + '</div>';
            html += '</div>';
        }
        html += '</div>';

        // 行动建议
        html += '<div class="action-list">';
        var doActions = actions.do || [];
        var avoidActions = actions.avoid || [];
        for (var d = 0; d < doActions.length; d++) {
            html += '<span class="action-item do">' + escapeMasterHtml(doActions[d]) + '</span>';
        }
        for (var a = 0; a < avoidActions.length; a++) {
            html += '<span class="action-item avoid">' + escapeMasterHtml(avoidActions[a]) + '</span>';
        }
        html += '</div></div></div>';
    }

    // ========== 代表作品分析（真实视频列表） ==========
    if (videos.length > 0) {
        html += '<div class="detail-card">';
        html += '<div class="detail-header"><div class="detail-title">代表作品分析</div><div class="detail-subtitle">Top ' + Math.min(videos.length, 10) + ' 高播放视频</div></div>';
        html += '<div class="detail-body"><div class="video-list">';

        for (var v = 0; v < Math.min(videos.length, 10); v++) {
            var video = videos[v];
            html += '<div class="video-item">';
            html += '<div class="video-rank">' + (v + 1) + '</div>';
            html += '<div class="video-content">';
            html += '<a href="' + (video.video_url || 'https://www.youtube.com/watch?v=' + video.youtube_id) + '" target="_blank" class="video-title">' + escapeMasterHtml(video.title) + '</a>';
            html += '<div class="video-meta">';
            html += '<span class="video-views">' + formatMasterNumber(video.view_count) + ' 播放</span>';
            if (video.keyword_source) {
                html += '<span class="video-topic">' + escapeMasterHtml(video.keyword_source) + '</span>';
            }
            if (video.duration) {
                html += '<span class="video-duration">' + formatDuration(video.duration) + '</span>';
            }
            html += '</div></div></div>';
        }
        html += '</div>';

        // 标题规律提示
        html += '<div class="topic-insight" style="margin-top: 16px;">';
        html += '<div class="insight-icon">📝</div>';
        html += '<div class="insight-text"><strong>标题规律：</strong>观察高播放视频的标题特征，提炼可复用的模板。点击视频标题可直接观看学习。</div>';
        html += '</div></div></div>';
    }

    // ========== 时长分布（真实数据） ==========
    if (durationDist.length > 0) {
        html += '<div class="detail-card">';
        html += '<div class="detail-header"><div class="detail-title">时长分布</div></div>';
        html += '<div class="detail-body"><div class="duration-dist">';
        for (var du = 0; du < durationDist.length; du++) {
            var dur = durationDist[du];
            html += '<div class="duration-item">';
            html += '<span class="duration-label">' + escapeMasterHtml(dur.label) + '</span>';
            html += '<span class="duration-count">' + dur.count + '个 (' + dur.percentage + '%)</span>';
            html += '<span class="duration-avg">均播 ' + formatMasterNumber(dur.avg_views) + '</span>';
            html += '</div>';
        }
        html += '</div></div></div>';
    }

    panel.innerHTML = html;
}

/**
 * 格式化时长（秒 → 分:秒）
 */
function formatDuration(seconds) {
    if (!seconds) return '--';
    var mins = Math.floor(seconds / 60);
    var secs = seconds % 60;
    return mins + ':' + (secs < 10 ? '0' : '') + secs;
}

/**
 * 初始化向高手学习模块
 */
function initMasterModule() {
    loadMastersData()
        .then(function(data) {
            renderMastersList(data);
            // 默认选中第一个
            if (data && data.length > 0) {
                selectMaster(0);
            }
        })
        .catch(function(error) {
            console.error('高手数据加载失败:', error);
            var container = document.getElementById('mastersList');
            if (container) {
                container.innerHTML = '<div style="text-align: center; color: #f87171; padding: 40px;">加载失败: ' + error.message + '</div>';
            }
        });
}

// 页面加载完成后检查是否需要初始化
document.addEventListener('DOMContentLoaded', function() {
    // 如果当前显示的是向高手学习 tab，则初始化
    var masterTab = document.getElementById('tabMaster');
    if (masterTab && masterTab.classList.contains('active')) {
        setTimeout(initMasterModule, 500);
    }
});
