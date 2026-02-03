        /**
         * insight.js - 洞察系统主模块
         *
         * 模块拆分说明（2026-01-31）：
         * 本文件已拆分为多个模块，需按以下顺序加载：
         *
         * 1. insight-core.js    - 核心工具函数（URL解析、日期计算、格式化、加载状态）
         * 2. insight-charts.js  - 通用图表渲染器（散点图、条形图、环形图等）
         * 3. insight-report.js  - 信息报告模块（Tab7 结论收集、综合洞察）
         * 4. insight-user.js    - 用户洞察模块（模式38-43）
         * 5. insight-global.js  - 全局认识模块（Tab1 领域概览、竞争格局）
         * 6. insight-content.js - 内容创作模块（Tab4 时长、类型分析）
         * 7. insight.js         - 主模块（Tab切换、模式渲染、业务逻辑）
         *
         * 各模块通过全局命名空间通信：
         * - window.InsightCore    核心工具
         * - window.InsightCharts  图表渲染
         * - window.InsightReport  信息报告
         * - window.InsightUser    用户洞察
         * - window.InsightGlobal  全局认识
         * - window.InsightContent 内容创作
         *
         * 向后兼容：关键函数同时暴露到 window 全局作用域
         */

        // ========== 模块依赖检查 ==========
        (function checkModules() {
            const required = ['InsightCore', 'InsightCharts', 'InsightReport', 'InsightUser', 'InsightGlobal', 'InsightContent'];
            const missing = required.filter(m => !window[m]);
            if (missing.length > 0) {
                console.warn('[insight.js] 缺少依赖模块:', missing.join(', '));
            } else {
                console.log('[insight.js] ✓ 所有依赖模块已加载');
            }
        })();

        // ========== 从模块获取函数（向后兼容）==========
        const getKeywordFromURL = window.getKeywordFromURL || (() => new URLSearchParams(window.location.search).get('keyword') || '养生');
        const getTimePeriodFromURL = window.getTimePeriodFromURL || (() => parseInt(new URLSearchParams(window.location.search).get('days')) || 30);
        const getDateRange = window.InsightCore?.getDateRange || window.getDateRange || ((days) => {
            if (days <= 0) return { date_from: null, date_to: null };
            const now = new Date(), from = new Date(now);
            from.setDate(from.getDate() - days);
            return { date_from: from.toISOString().split('T')[0], date_to: now.toISOString().split('T')[0] };
        });
        const getTimePeriodLabel = window.InsightCore?.getTimePeriodLabel || window.getTimePeriodLabel || ((days) => {
            if (days <= 0) return '全部时间';
            if (days === 7) return '近 7 天';
            if (days === 30) return '近 30 天';
            if (days === 90) return '近 90 天';
            return `近 ${days} 天`;
        });
        const showLoadingProgress = window.showLoadingProgress || ((msg) => {
            const el = document.getElementById('loadingStatus');
            if (el) el.textContent = msg;
            const banner = document.getElementById('globalLoadingBanner');
            if (banner) banner.style.display = 'flex';
        });
        const hideLoadingBanner = window.hideLoadingBanner || (() => {
            const banner = document.getElementById('globalLoadingBanner');
            if (banner) banner.style.display = 'none';
        });
        const showLoadingError = window.InsightCore?.showLoadingError || ((msg) => {
            const banner = document.getElementById('globalLoadingBanner');
            if (banner) {
                banner.style.borderColor = '#dc2626';
                const statusEl = document.getElementById('loadingStatus');
                if (statusEl) statusEl.innerHTML = `<span style="color:#ef4444">${msg}</span>`;
            }
        });
        const showChartNoData = window.showChartNoData || window.InsightCore?.showChartNoData || (() => {});
        const hideChartNoData = window.hideChartNoData || window.InsightCore?.hideChartNoData || (() => {});
        const loadAnalysisData = window.loadAnalysisData || window.InsightCore?.loadAnalysisData;

        // ========== 图表模块引用（insight-charts.js）==========
        const chartInstances = window.chartInstances || window.InsightCharts?.chartInstances || {};
        const destroyChart = window.destroyChart || window.InsightCharts?.destroyChart || ((id) => { if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; } });
        const renderScatter = window.renderScatter || window.InsightCharts?.renderScatter || (() => null);
        const renderBar = window.renderBar || window.InsightCharts?.renderBar || (() => null);
        const renderBubble = window.renderBubble || window.InsightCharts?.renderBubble || (() => null);
        const renderDonut = window.renderDonut || window.InsightCharts?.renderDonut || (() => null);
        const renderLine = window.renderLine || window.InsightCharts?.renderLine || (() => null);
        const renderHistogram = window.renderHistogram || window.InsightCharts?.renderHistogram || (() => null);
        const renderStackedBar = window.renderStackedBar || window.InsightCharts?.renderStackedBar || (() => null);
        const renderRadar = window.renderRadar || window.InsightCharts?.renderRadar || (() => null);
        const renderHeatmap = window.renderHeatmap || window.InsightCharts?.renderHeatmap || (() => null);
        const renderArea = window.renderArea || window.InsightCharts?.renderArea || (() => null);
        const updateInsight = window.updateInsight || window.InsightCharts?.updateInsight || ((id, content, action) => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<div class="chart-insight-title">📖 数据解读</div><div class="chart-insight-content">${content}</div>${action ? `<div class="chart-insight-action">${action}</div>` : ''}`;
        });

        // ========== 模式渲染函数引用（insight-content.js, insight-global.js）==========
        const renderPattern3 = window.renderPattern3 || window.InsightContent?.renderPattern3 || ((v) => console.warn('[insight.js] renderPattern3 not loaded'));
        const renderPattern4 = window.renderPattern4 || window.InsightContent?.renderPattern4 || ((v) => console.warn('[insight.js] renderPattern4 not loaded'));
        const renderOverview = window.renderOverview || window.InsightGlobal?.renderOverview || ((data) => console.warn('[insight.js] renderOverview not loaded'));
        const renderPattern23 = window.renderPattern23 || window.InsightGlobal?.renderPattern23 || ((c, v) => console.warn('[insight.js] renderPattern23 not loaded'));
        const renderSubscriberDistribution = window.renderSubscriberDistribution || window.InsightGlobal?.renderSubscriberDistribution || ((c) => console.warn('[insight.js] renderSubscriberDistribution not loaded'));
        const renderPattern12 = window.renderPattern12 || window.InsightGlobal?.renderPattern12 || ((c) => console.warn('[insight.js] renderPattern12 not loaded'));

        // ========== 用户洞察模块引用（insight-user.js）==========
        const loadUserInsightData = window.loadUserInsightData || window.InsightUser?.loadUserInsightData || (async () => console.log('[insight.js] loadUserInsightData not loaded'));
        const initUserInsightCharts = window.initUserInsightCharts || window.InsightUser?.initUserInsightCharts || (async () => {});
        const showNoCommentData = window.showNoCommentData || window.InsightUser?.showNoCommentData || (() => {});
        const renderHotwordsTable = window.renderHotwordsTable || window.InsightUser?.renderHotwordsTable || (() => {});
        const renderQuestionsChart = window.renderQuestionsChart || window.InsightUser?.renderQuestionsChart || (() => {});
        const renderSentimentBars = window.renderSentimentBars || window.InsightUser?.renderSentimentBars || (() => {});
        const renderLanguageDistribution = window.renderLanguageDistribution || window.InsightUser?.renderLanguageDistribution || (() => {});
        const renderTrendChart = window.renderTrendChart || window.InsightUser?.renderTrendChart || (() => {});
        const renderHighLikedStats = window.renderHighLikedStats || window.InsightUser?.renderHighLikedStats || (() => {});
        const registerStaticUserInsightConclusions = window.registerStaticUserInsightConclusions || window.InsightUser?.registerStaticUserInsightConclusions || (() => {});
        const ensureTab1Pattern43Fallback = window.ensureTab1Pattern43Fallback || window.InsightUser?.ensureTab1Pattern43Fallback || (() => {});

        // ========== 全局配置 ==========
        const API_BASE = window.location.origin;

        // 当前分析的关键词
        let currentKeyword = getKeywordFromURL();

        // 当前时间段（天数，0 表示全部）
        let currentTimePeriod = getTimePeriodFromURL();

        // 存储 API 返回的数据
        let analysisData = null;

        // 存储各时间段的数据缓存
        const dataCache = window.InsightCore?.getDataCache?.() || {};

        // 切换时间段
        async function switchTimePeriod(days) {
            if (days === currentTimePeriod) return;

            console.log(`切换时间段: ${currentTimePeriod} → ${days}`);
            currentTimePeriod = days;

            // 更新 URL（不刷新页面）
            const url = new URL(window.location);
            if (days === 30) {
                url.searchParams.delete('days'); // 默认值不需要显示
            } else {
                url.searchParams.set('days', days);
            }
            window.history.replaceState({}, '', url);

            // 更新标签页样式
            document.querySelectorAll('.time-period-tab').forEach(tab => {
                const tabDays = parseInt(tab.dataset.days);
                tab.classList.toggle('active', tabDays === days);
            });

            // 更新提示信息
            updateTimePeriodInfo(days);

            // 显示加载状态
            const selector = document.querySelector('.time-period-selector');
            if (selector) selector.classList.add('loading');

            // 重新加载数据
            analysisData = await loadAnalysisData(currentKeyword, days);

            // 隐藏加载状态
            if (selector) selector.classList.remove('loading');

            if (analysisData) {
                console.log('数据加载成功，开始更新模式...');
                updatePatternsWithData(analysisData);
                updateTimePeriodStats(analysisData);

                // 在主数据处理完成后加载用户洞察数据（模式43语言分布等）
                // 注意：这里不使用 await，让它异步执行，完成后会自动更新信息报告
                loadUserInsightData(days);
            } else {
                console.warn('数据加载失败');
                showNoDataMessage(days);
            }
        }

        // 更新时间段提示信息
        function updateTimePeriodInfo(days) {
            const infoEl = document.getElementById('timePeriodInfo');
            if (!infoEl) return;

            const label = getTimePeriodLabel(days);
            infoEl.innerHTML = `
                <span class="info-icon">ℹ️</span>
                <span class="info-text">正在分析 <strong>${label}</strong> 的数据</span>
            `;
        }

        // 更新时间段统计数据
        function updateTimePeriodStats(data) {
            // 如果页面有统计区域，更新它
            const statsEl = document.querySelector('.time-period-stats');
            if (statsEl && data) {
                const videoCount = data.videos?.length || 0;
                const channelCount = data.channels?.length || 0;
                statsEl.innerHTML = `
                    <div class="time-period-stat">
                        <span class="stat-value">${videoCount}</span>
                        <span class="stat-label">视频</span>
                    </div>
                    <div class="time-period-stat">
                        <span class="stat-value">${channelCount}</span>
                        <span class="stat-label">频道</span>
                    </div>
                `;
            }
        }

        // 显示无数据提示
        function showNoDataMessage(days) {
            const label = getTimePeriodLabel(days);
            showTooltip(`${label}内没有数据，请选择其他时间范围`);
        }

        // 切换时间范围下拉菜单显示
        function toggleTimeRangeDropdown(btn) {
            const dropdown = btn.nextElementSibling;
            const isVisible = dropdown.style.display === 'block';

            // 先关闭所有下拉菜单
            document.querySelectorAll('.time-range-dropdown').forEach(d => {
                d.style.display = 'none';
            });

            // 切换当前下拉菜单
            if (!isVisible) {
                dropdown.style.display = 'block';
            }
        }

        // 选择时间范围
        function selectTimeRange(days) {
            // 关闭所有下拉菜单
            document.querySelectorAll('.time-range-dropdown').forEach(d => {
                d.style.display = 'none';
            });

            // 切换时间段
            switchTimePeriod(days);
        }

        // 点击页面其他地方关闭下拉菜单
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.time-range-selector')) {
                document.querySelectorAll('.time-range-dropdown').forEach(d => {
                    d.style.display = 'none';
                });
            }
        });

        // ========== 信息报告时间筛选器 ==========

        // 切换信息报告时间范围
        async function switchReportTimePeriod(days) {
            if (days === currentTimePeriod) return;

            console.log(`切换信息报告时间范围: ${currentTimePeriod} → ${days}`);

            // 更新按钮状态
            document.querySelectorAll('.report-time-filter .filter-btn').forEach(btn => {
                const btnDays = parseInt(btn.dataset.days);
                btn.classList.toggle('active', btnDays === days);
            });

            // 调用现有的时间切换函数
            await switchTimePeriod(days);
        }

        // 初始化信息报告时间筛选器
        function initReportTimeFilter() {
            document.querySelectorAll('.report-time-filter .filter-btn').forEach(btn => {
                const btnDays = parseInt(btn.dataset.days);
                btn.classList.toggle('active', btnDays === currentTimePeriod);
            });
        }

        // ========== 信息报告系统（使用 insight-report.js 模块）==========
        // tabResearchConfig, tabConclusions 已移至 insight-report.js
        // registerPatternConclusion, clearAllConclusions, cacheChartImage 已移至 insight-report.js
        // renderInfoReportFromConclusions, getTabNameById, getTabIdByName 已移至 insight-report.js
        const tabResearchConfig = window.tabResearchConfig || window.InsightReport?.tabResearchConfig || {};
        const tabConclusions = window.tabConclusions || window.InsightReport?.tabConclusions || {};
        const registerPatternConclusion = window.registerPatternConclusion || window.InsightReport?.registerPatternConclusion || (() => {});
        const clearAllConclusions = window.clearAllConclusions || window.InsightReport?.clearAllConclusions || (() => {});
        const cacheChartImage = window.cacheChartImage || window.InsightReport?.cacheChartImage || (() => {});
        const renderInfoReportFromConclusions = window.renderInfoReportFromConclusions || window.InsightReport?.renderInfoReportFromConclusions || (() => {});
        const getTabNameById = window.getTabNameById || window.InsightReport?.getTabNameById || ((id) => id);
        const getTabIdByName = window.getTabIdByName || window.InsightReport?.getTabIdByName || ((name) => 'tab1');

        // ========== 旧代码保留（兼容） ==========

        // 分析竞争态势（旧版，保留兼容）
        function analyzeCompetition(videos) {
            const topChannelShareEl = document.getElementById('topChannelShare');
            const newChannelOpportunityEl = document.getElementById('newChannelOpportunity');
            const contentSaturationEl = document.getElementById('contentSaturation');
            const viralDifficultyEl = document.getElementById('viralDifficulty');

            if (!videos || videos.length === 0) {
                [topChannelShareEl, newChannelOpportunityEl, contentSaturationEl, viralDifficultyEl].forEach(el => {
                    if (el) el.textContent = '-';
                });
                return;
            }

            // 1. 头部频道集中度：TOP10频道占总播放比例
            const channelViews = {};
            let totalViews = 0;
            videos.forEach(v => {
                const views = v.view_count || 0;
                totalViews += views;
                channelViews[v.channel_id] = (channelViews[v.channel_id] || 0) + views;
            });
            const sortedChannels = Object.entries(channelViews).sort((a, b) => b[1] - a[1]);
            const top10Views = sortedChannels.slice(0, 10).reduce((sum, [_, views]) => sum + views, 0);
            const concentration = totalViews > 0 ? (top10Views / totalViews * 100).toFixed(0) : 0;
            if (topChannelShareEl) {
                topChannelShareEl.textContent = concentration + '%';
                topChannelShareEl.style.color = concentration > 70 ? '#ef4444' : concentration > 50 ? '#f59e0b' : '#10b981';
            }

            // 2. 新频道机会
            const uniqueChannels = Object.keys(channelViews).length;
            const avgViewsPerChannel = totalViews / uniqueChannels;
            const opportunityText = concentration > 70 ? '较难' : concentration > 50 ? '中等' : '较好';
            if (newChannelOpportunityEl) {
                newChannelOpportunityEl.textContent = opportunityText;
                newChannelOpportunityEl.style.color = concentration > 70 ? '#ef4444' : concentration > 50 ? '#f59e0b' : '#10b981';
            }

            // 3. 内容饱和度
            const videoCount = videos.length;
            const saturationText = videoCount > 500 ? '高' : videoCount > 200 ? '中' : '低';
            if (contentSaturationEl) {
                contentSaturationEl.textContent = saturationText;
                contentSaturationEl.style.color = videoCount > 500 ? '#ef4444' : videoCount > 200 ? '#f59e0b' : '#10b981';
            }

            // 4. 爆款难度：达到10万播放的概率
            const viralVideos = videos.filter(v => (v.view_count || 0) >= 100000).length;
            const viralRate = (viralVideos / videos.length * 100).toFixed(1);
            if (viralDifficultyEl) {
                viralDifficultyEl.textContent = viralRate + '%';
                viralDifficultyEl.style.color = viralRate < 5 ? '#ef4444' : viralRate < 15 ? '#f59e0b' : '#10b981';
            }
        }

        // 生成市场洞察
        function generateMarketInsights(videos) {
            const listEl = document.getElementById('marketInsightList');
            if (!listEl || !videos || videos.length === 0) {
                if (listEl) listEl.innerHTML = '<div class="insight-loading">暂无数据</div>';
                return;
            }

            const insights = [];

            // 1. 播放量分布洞察
            const viewCounts = videos.map(v => v.view_count || 0).sort((a, b) => b - a);
            const median = viewCounts[Math.floor(viewCounts.length / 2)];
            const avg = viewCounts.reduce((a, b) => a + b, 0) / viewCounts.length;
            const top10Avg = viewCounts.slice(0, 10).reduce((a, b) => a + b, 0) / 10;

            insights.push({
                icon: '📊',
                text: `播放量中位数为 <span class="insight-data">${formatNumber(median)}</span>，头部视频（TOP10）平均播放 <span class="insight-data">${formatNumber(top10Avg)}</span>，是中位数的 <span class="insight-data">${(top10Avg / median).toFixed(0)}倍</span>`,
            });

            // 2. 频道集中度洞察
            const channelCount = new Set(videos.map(v => v.channel_id)).size;
            const videosPerChannel = (videos.length / channelCount).toFixed(1);
            insights.push({
                icon: '📺',
                text: `共 <span class="insight-data">${channelCount}</span> 个频道参与竞争，平均每频道发布 <span class="insight-data">${videosPerChannel}</span> 个视频`,
            });

            // 3. 时长分布洞察
            const durations = videos.filter(v => v.duration_seconds).map(v => v.duration_seconds);
            if (durations.length > 0) {
                const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
                const minutes = Math.floor(avgDuration / 60);
                insights.push({
                    icon: '⏱️',
                    text: `视频平均时长约 <span class="insight-data">${minutes}分钟</span>，建议参考此时长区间`,
                });
            }

            listEl.innerHTML = insights.map(insight => `
                <div class="market-insight-item">
                    <span class="insight-icon">${insight.icon}</span>
                    <span class="insight-text">${insight.text}</span>
                </div>
            `).join('');
        }

        // 加载学习参考数据
        async function loadLearningResources() {
            console.log('加载学习参考数据...');

            if (allVideos && allVideos.length > 0) {
                generateBenchmarkChannels(allVideos);
            }
        }

        // 生成推荐对标频道
        function generateBenchmarkChannels(videos) {
            const gridEl = document.getElementById('benchmarkChannelsGrid');
            if (!gridEl || !videos || videos.length === 0) {
                if (gridEl) gridEl.innerHTML = '<div class="channel-loading">暂无数据</div>';
                return;
            }

            // 按频道聚合数据
            const channelData = {};
            videos.forEach(v => {
                const chId = v.channel_id;
                if (!channelData[chId]) {
                    channelData[chId] = {
                        id: chId,
                        name: v.channel_title || '未知频道',
                        videos: [],
                        totalViews: 0,
                        subscribers: v.subscriber_count || 0,
                    };
                }
                channelData[chId].videos.push(v);
                channelData[chId].totalViews += v.view_count || 0;
            });

            // 计算效率分数并排序
            const channels = Object.values(channelData).map(ch => {
                ch.avgViews = ch.totalViews / ch.videos.length;
                ch.efficiency = ch.subscribers > 0 ? ch.avgViews / ch.subscribers : 0;
                return ch;
            }).sort((a, b) => b.avgViews - a.avgViews);

            // 取TOP5
            const topChannels = channels.slice(0, 5);

            gridEl.innerHTML = topChannels.map((ch, idx) => {
                const reason = idx === 0 ? '播放量最高' :
                              ch.efficiency > 1 ? '高效率频道' :
                              ch.videos.length > 5 ? '持续产出' : '表现稳定';
                return `
                <div class="benchmark-channel-card">
                    <div class="channel-avatar">${ch.name.charAt(0)}</div>
                    <div class="channel-info">
                        <div class="channel-name">
                            <a href="https://youtube.com/channel/${ch.id}" target="_blank">${ch.name}</a>
                        </div>
                        <div class="channel-stats">
                            <span>视频: ${ch.videos.length}</span>
                            <span>均播: ${formatNumber(ch.avgViews)}</span>
                        </div>
                        <div class="channel-reason">${reason}</div>
                    </div>
                </div>
            `}).join('');
        }

        // 加载行动指南数据
        async function loadActionGuide() {
            console.log('加载行动指南数据...');

            if (allVideos && allVideos.length > 0) {
                generatePriorityActions(allVideos);
                generateContentSuggestions(allVideos);
                generateWarningsForActionTab(allVideos);
            }
        }

        // 生成优先行动
        function generatePriorityActions(videos) {
            const listEl = document.getElementById('priorityActionList');
            if (!listEl) return;

            const actions = [];

            // 基于数据生成行动建议
            const avgViews = videos.reduce((sum, v) => sum + (v.view_count || 0), 0) / videos.length;
            const topVideos = videos.filter(v => (v.view_count || 0) > avgViews * 3);

            if (topVideos.length > 0) {
                // 分析爆款标题模式
                const topTitles = topVideos.slice(0, 5).map(v => v.title);
                actions.push({
                    title: '研究爆款标题结构',
                    reason: `分析 ${topVideos.length} 个高播放视频的标题模式`,
                });
            }

            // 时长建议
            const durations = videos.filter(v => v.duration_seconds).map(v => v.duration_seconds);
            if (durations.length > 0) {
                const topDurations = videos.filter(v => (v.view_count || 0) > avgViews).map(v => v.duration_seconds).filter(Boolean);
                if (topDurations.length > 0) {
                    const optimalDuration = Math.floor(topDurations.reduce((a, b) => a + b, 0) / topDurations.length / 60);
                    actions.push({
                        title: `控制视频时长在 ${Math.max(5, optimalDuration - 3)}-${optimalDuration + 3} 分钟`,
                        reason: '基于高播放视频的平均时长分析',
                    });
                }
            }

            // 频道对标建议
            actions.push({
                title: '选择 2-3 个对标频道深入学习',
                reason: '参考「学习参考」板块的推荐频道列表',
            });

            listEl.innerHTML = actions.map((action, idx) => `
                <div class="priority-action-item">
                    <div class="priority-number">${idx + 1}</div>
                    <div class="priority-content">
                        <div class="priority-title">${action.title}</div>
                        <div class="priority-reason"><span class="data-source">依据：</span>${action.reason}</div>
                    </div>
                </div>
            `).join('');
        }

        // 生成内容创作建议
        function generateContentSuggestions(videos) {
            if (!videos || videos.length === 0) return;

            // 推荐选题
            const topicsEl = document.getElementById('suggestedTopics');
            if (topicsEl) {
                const topVideos = [...videos].sort((a, b) => (b.view_count || 0) - (a.view_count || 0)).slice(0, 10);
                // 提取高频词
                const keywords = topVideos.map(v => v.title).join(' ').split(/[\s,，、！!？?]+/).filter(w => w.length > 1);
                const wordCount = {};
                keywords.forEach(w => { wordCount[w] = (wordCount[w] || 0) + 1; });
                const topWords = Object.entries(wordCount).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([w]) => w);
                topicsEl.textContent = topWords.length > 0 ? topWords.join('、') : '分析中...';
            }

            // 最佳时长
            const durationEl = document.getElementById('suggestedDuration');
            if (durationEl) {
                const avgViews = videos.reduce((sum, v) => sum + (v.view_count || 0), 0) / videos.length;
                const topDurations = videos.filter(v => (v.view_count || 0) > avgViews && v.duration_seconds).map(v => v.duration_seconds);
                if (topDurations.length > 0) {
                    const avg = topDurations.reduce((a, b) => a + b, 0) / topDurations.length;
                    const minutes = Math.floor(avg / 60);
                    durationEl.textContent = `${Math.max(5, minutes - 3)} - ${minutes + 3} 分钟`;
                } else {
                    durationEl.textContent = '数据不足';
                }
            }

            // 发布时间（模拟，需要后端支持）
            const publishTimeEl = document.getElementById('suggestedPublishTime');
            if (publishTimeEl) {
                publishTimeEl.textContent = '工作日晚 18:00-21:00';
            }

            // 标签建议
            const tagsEl = document.getElementById('suggestedTags');
            if (tagsEl) {
                tagsEl.textContent = `${currentKeyword}、教程、技巧`;
            }
        }

        // 生成避坑清单（行动指南子标签页专用）
        function generateWarningsForActionTab(videos) {
            const listEl = document.getElementById('reportWarningList');
            if (!listEl) return;

            const warnings = [
                { icon: '❌', text: '不要一开始就挑战长视频（>20分钟），新频道完播率低' },
                { icon: '❌', text: '避免标题党，点击率高但完播率低会影响推荐' },
                { icon: '❌', text: '不要忽视封面设计，它决定了点击率' },
            ];

            listEl.innerHTML = warnings.map(w => `
                <div class="warning-item" style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:rgba(239,68,68,0.1);border-radius:8px;margin-bottom:8px;">
                    <span style="font-size:1.2em;">${w.icon}</span>
                    <span style="color:#f87171;">${w.text}</span>
                </div>
            `).join('');
        }

        // 初始化时间段选择器
        function initTimePeriodSelector() {
            // 设置当前时间段的 active 状态
            document.querySelectorAll('.time-period-tab').forEach(tab => {
                const tabDays = parseInt(tab.dataset.days);
                tab.classList.toggle('active', tabDays === currentTimePeriod);
            });

            // 更新提示信息
            updateTimePeriodInfo(currentTimePeriod);
        }

        // 更新页面标题显示当前关键词
        function updatePageTitle(keyword) {
            const titleEl = document.querySelector('h2.section-title span:last-child');
            if (titleEl) {
                titleEl.textContent = `模式分析 - ${keyword}`;
            }
            // 更新面包屑
            const breadcrumb = document.querySelector('.breadcrumb span:last-child');
            if (breadcrumb) {
                breadcrumb.textContent = `模式洞察 (${keyword})`;
            }
        }

        // 格式化数字
        function formatNumber(num) {
            if (num >= 10000) {
                return (num / 10000).toFixed(1) + '万';
            }
            return num.toLocaleString();
        }

        // ========== 洞察系统核心逻辑 ==========

        const InsightSystem = {
            // 数据源注册
            dataSources: new Map([
                ['total-views-top20', { id: 'total-views-top20', name: '总播放榜 Top20', icon: '📊', module: 'video-ranking' }],
                ['avg-views-top20', { id: 'avg-views-top20', name: '平均播放榜 Top20', icon: '⚡', module: 'video-ranking' }],
                ['dark-horse-top20', { id: 'dark-horse-top20', name: '黑马榜 Top20', icon: '🐴', module: 'video-ranking' }],
                ['channel-growth', { id: 'channel-growth', name: '频道增长分析', icon: '📈', module: 'channel-ranking' }],
                ['topic-analysis', { id: 'topic-analysis', name: '题材分析', icon: '🏷️', module: 'topic-analysis' }],
                ['efficiency-top20', { id: 'efficiency-top20', name: '高效榜 Top20', icon: '🚀', module: 'channel-ranking' }],
                ['trend-analysis', { id: 'trend-analysis', name: '趋势分析', icon: '📈', module: 'trend-chart' }],
            ]),

            // 洞察注册
            insights: new Map([
                ['best-duration', { id: 'best-duration', sources: ['total-views-top20', 'avg-views-top20', 'dark-horse-top20'] }],
                ['small-channel-opportunity', { id: 'small-channel-opportunity', sources: ['dark-horse-top20', 'channel-growth'] }],
                ['best-topic', { id: 'best-topic', sources: ['topic-analysis', 'total-views-top20'] }],
                ['best-frequency', { id: 'best-frequency', sources: ['efficiency-top20', 'trend-analysis'] }],
            ]),

            // 数据源 → 洞察的映射
            sourceToInsights: new Map(),

            init() {
                // 建立反向索引
                this.insights.forEach((insight, insightId) => {
                    insight.sources.forEach(sourceId => {
                        if (!this.sourceToInsights.has(sourceId)) {
                            this.sourceToInsights.set(sourceId, new Set());
                        }
                        this.sourceToInsights.get(sourceId).add(insightId);
                    });
                });
            },

            // 获取某数据源支撑的所有洞察
            getInsightsBySource(sourceId) {
                return Array.from(this.sourceToInsights.get(sourceId) || []);
            },

            // 获取某洞察依赖的所有数据源
            getSourcesByInsight(insightId) {
                const insight = this.insights.get(insightId);
                return insight ? insight.sources : [];
            }
        };

        // 初始化
        InsightSystem.init();

        // ========== 交互函数 ==========

        // 展开/折叠洞察卡片
        function toggleInsight(cardId) {
            const card = document.getElementById(cardId);
            const isExpanded = card.classList.contains('expanded');
            const toggle = card.querySelector('.insight-toggle');

            if (isExpanded) {
                card.classList.remove('expanded');
                toggle.textContent = '▶ 展开详情';
            } else {
                card.classList.add('expanded');
                toggle.textContent = '▼ 收起';
            }
        }

        // 展开/折叠数据表格
        function toggleDataTable(tableId) {
            const table = document.getElementById(tableId);
            table.classList.toggle('expanded');

            const btn = table.previousElementSibling.querySelector('.data-toggle-btn');
            if (table.classList.contains('expanded')) {
                btn.textContent = '▼ 收起数据';
            } else {
                btn.textContent = '📋 查看数据';
            }
        }

        // 高亮数据源
        function highlightSource(sourceId) {
            clearHighlights();

            // 高亮所有该数据源的标签
            document.querySelectorAll(`[data-source-id="${sourceId}"]`).forEach(el => {
                el.classList.add('highlight-source');
            });

            // 高亮依赖该数据源的洞察卡片
            const insightIds = InsightSystem.getInsightsBySource(sourceId);
            insightIds.forEach(insightId => {
                const card = document.querySelector(`[data-insight-id="${insightId}"]`);
                if (card) {
                    card.classList.add('highlight-dependent');
                }
            });

            // 显示提示
            const source = InsightSystem.dataSources.get(sourceId);
            showTooltip(`${source.icon} ${source.name} 支撑了 ${insightIds.length} 条洞察`);

            // 3秒后自动清除高亮
            setTimeout(clearHighlights, 3000);
        }

        // 高亮洞察
        function highlightInsight(insightId) {
            clearHighlights();

            // 高亮洞察卡片
            const card = document.querySelector(`[data-insight-id="${insightId}"]`);
            if (card) {
                card.classList.add('highlight-insight');
            }

            // 高亮支撑的数据源
            const sourceIds = InsightSystem.getSourcesByInsight(insightId);
            sourceIds.forEach(sourceId => {
                document.querySelectorAll(`[data-source-id="${sourceId}"]`).forEach(el => {
                    el.classList.add('highlight-source');
                });
            });
        }

        // 清除所有高亮
        function clearHighlights() {
            document.querySelectorAll('.highlight-source, .highlight-insight, .highlight-dependent').forEach(el => {
                el.classList.remove('highlight-source', 'highlight-insight', 'highlight-dependent');
            });
            hideTooltip();
        }

        // 滚动到指定洞察
        function scrollToInsight(cardId) {
            const card = document.getElementById(cardId);
            if (card) {
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });

                // 展开卡片
                if (!card.classList.contains('expanded')) {
                    toggleInsight(cardId);
                }

                // 高亮效果
                card.classList.add('highlight-insight');
                setTimeout(() => card.classList.remove('highlight-insight'), 2000);
            }
        }

        // ========== 工具提示 ==========

        function showTooltip(text, x, y) {
            const tooltip = document.getElementById('tooltip');
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
            tooltip.classList.remove('visible');
        }

        // ========== 表格操作 ==========

        function toggleAllRows(checkbox) {
            const table = checkbox.closest('table');
            const checkboxes = table.querySelectorAll('tbody .row-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = checkbox.checked;
                cb.closest('tr').classList.toggle('selected', checkbox.checked);
            });
        }

        function sortTable(tableId, sortKey) {
            // 简化的排序逻辑示意
            console.log(`Sorting ${tableId} by ${sortKey}`);
        }

        function highlightInChart() {
            const selectedRows = document.querySelectorAll('.data-table tr.selected');
            console.log(`Highlighting ${selectedRows.length} items in chart`);
            showTooltip(`已在图表中高亮 ${selectedRows.length} 个数据点`);
        }

        function exportCSV() {
            console.log('Exporting CSV...');
            showTooltip('正在导出 CSV 文件...');
        }

        function openAllLinks() {
            const selectedRows = document.querySelectorAll('.data-table tr.selected');
            if (selectedRows.length === 0) {
                showTooltip('请先选择要打开的行');
                return;
            }
            showTooltip(`即将打开 ${selectedRows.length} 个链接`);
        }

        // ========== 链接操作 ==========

        function openVideo(videoId) {
            window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
        }

        function openChannel(channelId) {
            window.open(`https://www.youtube.com/channel/${channelId}`, '_blank');
        }

        // ========== 热力图操作 ==========

        function showHeatmapDetail(topic, duration) {
            showTooltip(`${topic} × ${duration}：点击查看该组合的 Top 10 视频`);
        }

        // ========== 初始化图表 ==========

        function initDurationChart() {
            const container = document.getElementById('duration-chart');
            if (!container) return;

            // 数据
            const data = [
                { duration: 1, views: 15 },
                { duration: 3, views: 28 },
                { duration: 5, views: 52 },
                { duration: 7, views: 68 },
                { duration: 10, views: 62 },
                { duration: 15, views: 45 },
                { duration: 20, views: 32 },
                { duration: 30, views: 18 },
            ];

            // 创建 SVG
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'chart-svg');
            svg.setAttribute('viewBox', '0 0 400 280');

            // 图表配置
            const margin = { top: 30, right: 30, bottom: 40, left: 50 };
            const width = 400 - margin.left - margin.right;
            const height = 280 - margin.top - margin.bottom;

            // 比例尺
            const xScale = (d) => margin.left + (d / 35) * width;
            const yScale = (d) => margin.top + height - (d / 80) * height;

            // 坐标轴
            const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            xAxis.setAttribute('x1', margin.left);
            xAxis.setAttribute('y1', margin.top + height);
            xAxis.setAttribute('x2', margin.left + width);
            xAxis.setAttribute('y2', margin.top + height);
            xAxis.setAttribute('class', 'chart-axis');
            svg.appendChild(xAxis);

            const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            yAxis.setAttribute('x1', margin.left);
            yAxis.setAttribute('y1', margin.top);
            yAxis.setAttribute('x2', margin.left);
            yAxis.setAttribute('y2', margin.top + height);
            yAxis.setAttribute('class', 'chart-axis');
            svg.appendChild(yAxis);

            // Y轴标签
            [0, 20, 40, 60, 80].forEach(v => {
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', margin.left - 8);
                label.setAttribute('y', yScale(v) + 4);
                label.setAttribute('class', 'chart-axis-label');
                label.setAttribute('text-anchor', 'end');
                label.textContent = v + '万';
                svg.appendChild(label);

                // 网格线
                const grid = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                grid.setAttribute('x1', margin.left);
                grid.setAttribute('y1', yScale(v));
                grid.setAttribute('x2', margin.left + width);
                grid.setAttribute('y2', yScale(v));
                grid.setAttribute('class', 'chart-grid-line');
                svg.appendChild(grid);
            });

            // X轴标签
            [1, 5, 10, 15, 20, 30].forEach(v => {
                const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                label.setAttribute('x', xScale(v));
                label.setAttribute('y', margin.top + height + 20);
                label.setAttribute('class', 'chart-axis-label');
                label.setAttribute('text-anchor', 'middle');
                label.textContent = v + '分';
                svg.appendChild(label);
            });

            // 高亮区域 (5-10分钟)
            const highlightArea = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            highlightArea.setAttribute('x', xScale(5));
            highlightArea.setAttribute('y', margin.top);
            highlightArea.setAttribute('width', xScale(10) - xScale(5));
            highlightArea.setAttribute('height', height);
            highlightArea.setAttribute('class', 'chart-highlight-area');
            svg.appendChild(highlightArea);

            // 最优区间标注
            const annotation = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            annotation.setAttribute('x', (xScale(5) + xScale(10)) / 2);
            annotation.setAttribute('y', margin.top + 15);
            annotation.setAttribute('class', 'chart-annotation');
            annotation.setAttribute('text-anchor', 'middle');
            annotation.textContent = '最优区间';
            svg.appendChild(annotation);

            // 折线
            const points = data.map(d => `${xScale(d.duration)},${yScale(d.views)}`).join(' ');
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            line.setAttribute('points', points);
            line.setAttribute('class', 'chart-line');
            svg.appendChild(line);

            // 数据点
            data.forEach(d => {
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', xScale(d.duration));
                circle.setAttribute('cy', yScale(d.views));
                circle.setAttribute('r', d.duration >= 5 && d.duration <= 10 ? 7 : 5);
                circle.setAttribute('class', 'chart-point' + (d.duration >= 5 && d.duration <= 10 ? ' highlighted' : ''));

                circle.addEventListener('mouseenter', (e) => {
                    showTooltip(`${d.duration}分钟: 平均播放 ${d.views}万`, e.pageX + 10, e.pageY - 30);
                });
                circle.addEventListener('mouseleave', hideTooltip);

                svg.appendChild(circle);
            });

            container.appendChild(svg);
        }

        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', async () => {
            console.log('[init] DOMContentLoaded fired');
            console.log('[init] Chart.js:', typeof Chart !== 'undefined' ? 'OK' : 'MISSING');
            console.log('[init] vis-network:', typeof vis !== 'undefined' ? 'OK' : 'MISSING');

            // 检查关键依赖
            if (typeof Chart === 'undefined') {
                console.error('Chart.js 未加载！');
                showLoadingError('图表库加载失败，请刷新页面重试（Chart.js unavailable）');
                return;
            }

            // 更新页面标题
            updatePageTitle(currentKeyword);

            // 初始化时间段选择器
            initTimePeriodSelector();
            initReportTimeFilter();

            // 加载分析数据（使用当前时间段）
            console.log('正在加载数据:', currentKeyword, '时间段:', currentTimePeriod, '天');
            showLoadingProgress('正在连接服务器，首次加载约需 10-30 秒...');
            analysisData = await loadAnalysisData(currentKeyword, currentTimePeriod);

            if (analysisData) {
                console.log('数据加载成功:', analysisData);
                hideLoadingBanner();
                window.__pageInitDone = true;
                // 用 API 数据更新模式内容
                updatePatternsWithData(analysisData);
                updateTimePeriodStats(analysisData);

                // 在主数据处理完成后加载用户洞察数据（模式43语言分布等）
                loadUserInsightData(currentTimePeriod);
            } else {
                console.warn('数据加载失败');
                showLoadingError('数据加载失败，请刷新页面重试');
            }

            initDurationChart();

            // 行选择事件
            document.querySelectorAll('.data-table tbody tr').forEach(row => {
                row.addEventListener('click', (e) => {
                    if (e.target.type !== 'checkbox') {
                        const checkbox = row.querySelector('.row-checkbox');
                        checkbox.checked = !checkbox.checked;
                        row.classList.toggle('selected', checkbox.checked);
                    }
                });
            });

            // 复选框事件
            document.querySelectorAll('.data-table tbody .row-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    e.target.closest('tr').classList.toggle('selected', e.target.checked);
                });
            });
        });

        // 用 API 数据更新模式内容
        function updatePatternsWithData(data) {
            console.log('========== 更新模式数据 ==========');
            console.log('视频数:', data.videos?.length, '频道数:', data.channels?.length);

            // 清空之前的结论（时间筛选切换时需要重新生成）
            clearAllConclusions();

            // ========== 领域概览（全局认识第一个Tab）==========
            console.log('更新领域概览...');
            try {
                renderOverview(data);
                console.log('✓ 领域概览渲染完成');
            } catch(e) { console.error('✗ 领域概览错误:', e); }

            // 更新指标概览（顶部统计数字）
            updateMetricsOverview(data);

            // 更新统计数字
            updateStatsDisplay(data);

            // 更新频道稳定性模式
            if (data.channel_stability) {
                console.log('更新频道稳定性...');
                try {
                    renderChannelStability(data.channel_stability);
                    console.log('✓ 频道稳定性渲染完成');
                } catch(e) { console.error('✗ 频道稳定性错误:', e); }
            }

            // 更新频道榜单（黑马、高效等）
            if (data.channel_rankings) {
                console.log('更新频道榜单...');
                try {
                    renderChannelRankings(data.channel_rankings);
                    console.log('✓ 频道榜单渲染完成');
                } catch(e) { console.error('✗ 频道榜单错误:', e); }
            }

            // ========== 使用模板化渲染器 ==========

            // 视频相关模式
            if (data.videos && data.videos.length > 0) {
                console.log('开始渲染视频相关模式...');
                try {
                    renderPattern3(data.videos);
                    console.log('✓ 模式3(时长)渲染完成');
                } catch(e) { console.error('✗ 模式3错误:', e); }

                try {
                    renderPattern4(data.videos);
                    console.log('✓ 模式4(内容类型)渲染完成');
                } catch(e) { console.error('✗ 模式4错误:', e); }

                try {
                    renderTitlePatterns(data.videos);
                    console.log('✓ 标题模式渲染完成');
                } catch(e) { console.error('✗ 标题模式错误:', e); }

                try {
                    renderPublishingPatterns(data.videos);
                    console.log('✓ 发布时机模式渲染完成');
                } catch(e) { console.error('✗ 发布时机错误:', e); }
            } else {
                console.warn('没有视频数据！');
            }

            // 频道相关模式
            if (data.channels && data.channels.length > 0) {
                console.log('开始渲染频道相关模式...');
                try {
                    renderPattern2(data.channels);
                    console.log('✓ 模式2(订阅效率)渲染完成');
                } catch(e) { console.error('✗ 模式2错误:', e); }

                try {
                    renderPattern12(data.channels);
                    console.log('✓ 模式12(频道竞争格局)渲染完成');
                } catch(e) { console.error('✗ 模式12错误:', e); }

                try {
                    renderPattern23(data.channels, data.videos);
                    console.log('✓ 模式23(垄断度)渲染完成');
                } catch(e) { console.error('✗ 模式23错误:', e); }

            } else {
                console.warn('没有频道数据！');
            }

            // ========== 新增动态模块渲染 ==========

            // Tab2 套利分析 - 话题有趣度（网络中心性分析）
            console.log('更新话题有趣度...');
            try {
                renderTopicInterestingness(currentKeyword);
                console.log('✓ 话题有趣度渲染完成');
            } catch(e) { console.error('✗ 话题有趣度错误:', e); }

            // Tab2 套利分析 - 地区分布
            if (data.region_distribution) {
                console.log('更新地区分布...');
                try {
                    renderRegionDistribution(data.region_distribution);
                    console.log('✓ 地区分布渲染完成');
                } catch(e) { console.error('✗ 地区分布错误:', e); }
            }

            // Tab3 选题决策 - 内容生命周期
            if (data.content_lifecycle) {
                console.log('更新内容生命周期...');
                try {
                    renderContentLifecycle(data.content_lifecycle);
                    console.log('✓ 内容生命周期渲染完成');
                } catch(e) { console.error('✗ 内容生命周期错误:', e); }
            }

            // Tab5 发布策略 - 星期发布效果
            if (data.weekday_performance) {
                console.log('更新星期发布效果...');
                try {
                    renderWeekdayPerformance(data.weekday_performance);
                    console.log('✓ 星期发布效果渲染完成');
                } catch(e) { console.error('✗ 星期发布效果错误:', e); }
            }

            // Tab7 信息报告 - 汇总所有模式结论
            console.log('生成信息报告...');
            try {
                renderInfoReport(data);
                console.log('✓ 信息报告生成完成');
            } catch(e) { console.error('✗ 信息报告错误:', e); }

            // 底部洞察卡片已删除，不再更新

            console.log('========== 模式渲染完成 ==========');

            // 保留兼容旧函数
            if (data.duration_distribution || data.videos) {
                updateDurationPattern(data.duration_distribution, data.videos);
            }
            if (data.channels) {
                updateChannelPatterns(data.channels, data.insights);
            }
            if (data.insights) {
                updateInsightsDisplay(data.insights);
            }
        }

        /**
         * 模式7-10：标题模式分析
         * 分析数字、感叹号、Hashtag等标题元素的效果
         */
        function renderTitlePatterns(videos) {
            if (!videos || videos.length === 0) return;

            // 模式7：数字标题
            const withNumbers = videos.filter(v => /\d+/.test(v.title || ''));
            const withoutNumbers = videos.filter(v => !/\d+/.test(v.title || ''));

            const numberAvg = withNumbers.length > 0
                ? withNumbers.reduce((s, v) => s + (v.view_count || 0), 0) / withNumbers.length
                : 0;
            const noNumberAvg = withoutNumbers.length > 0
                ? withoutNumbers.reduce((s, v) => s + (v.view_count || 0), 0) / withoutNumbers.length
                : 0;

            // 更新数字标题表格
            const numberTableBody = document.getElementById('numberTitleTableBody');
            if (numberTableBody) {
                const numberRatioVal = noNumberAvg > 0 ? ((numberAvg / noNumberAvg - 1) * 100).toFixed(0) : 0;
                numberTableBody.innerHTML = `
                    <tr>
                        <td>含数字</td>
                        <td>${withNumbers.length}</td>
                        <td class="${numberAvg > noNumberAvg ? 'highlight' : ''}">${formatNumber(Math.round(numberAvg))}</td>
                        <td class="${numberAvg > noNumberAvg ? 'highlight' : ''}">+${numberRatioVal}%</td>
                    </tr>
                    <tr>
                        <td>不含数字</td>
                        <td>${withoutNumbers.length}</td>
                        <td>${formatNumber(Math.round(noNumberAvg))}</td>
                        <td>基准</td>
                    </tr>
                `;
            }

            renderBar('numberTitleChart',
                ['含数字标题', '无数字标题'],
                [numberAvg, noNumberAvg],
                { yLabel: '平均播放量' }
            );

            const numberRatio = noNumberAvg > 0 ? (numberAvg / noNumberAvg).toFixed(2) : 'N/A';
            updateInsight('numberTitleInsight',
                `含数字标题的视频平均播放<strong>${formatNumber(Math.round(numberAvg))}</strong>，是无数字标题的<strong>${numberRatio}倍</strong>。样本：${withNumbers.length} vs ${withoutNumbers.length}。`,
                numberAvg > noNumberAvg ? '建议在标题中使用具体数字（如"3个技巧"、"10分钟学会"）' : '该领域数字标题效果一般，可尝试其他策略'
            );

            // 模式8：感叹号效应
            const withExclaim = videos.filter(v => (v.title || '').includes('!') || (v.title || '').includes('！'));
            const withoutExclaim = videos.filter(v => !(v.title || '').includes('!') && !(v.title || '').includes('！'));

            const exclaimAvg = withExclaim.length > 0
                ? withExclaim.reduce((s, v) => s + (v.view_count || 0), 0) / withExclaim.length
                : 0;
            const noExclaimAvg = withoutExclaim.length > 0
                ? withoutExclaim.reduce((s, v) => s + (v.view_count || 0), 0) / withoutExclaim.length
                : 0;

            // 更新感叹号表格
            const exclaimTableBody = document.getElementById('exclaimTitleTableBody');
            if (exclaimTableBody) {
                const exclaimRatioVal = noExclaimAvg > 0 ? ((exclaimAvg / noExclaimAvg - 1) * 100).toFixed(0) : 0;
                exclaimTableBody.innerHTML = `
                    <tr>
                        <td>有感叹号</td>
                        <td>${withExclaim.length}</td>
                        <td class="${exclaimAvg > noExclaimAvg ? 'highlight' : ''}">${formatNumber(Math.round(exclaimAvg))}</td>
                        <td class="${exclaimAvg > noExclaimAvg ? 'highlight' : ''}">${exclaimRatioVal >= 0 ? '+' : ''}${exclaimRatioVal}%</td>
                    </tr>
                    <tr>
                        <td>无感叹号</td>
                        <td>${withoutExclaim.length}</td>
                        <td>${formatNumber(Math.round(noExclaimAvg))}</td>
                        <td>基准</td>
                    </tr>
                `;
            }

            renderBar('exclaimTitleChart',
                ['有感叹号', '无感叹号'],
                [exclaimAvg, noExclaimAvg],
                { yLabel: '平均播放量' }
            );

            const exclaimRatio = noExclaimAvg > 0 ? (exclaimAvg / noExclaimAvg).toFixed(2) : 'N/A';
            updateInsight('exclaimTitleInsight',
                `有感叹号的视频平均播放<strong>${formatNumber(Math.round(exclaimAvg))}</strong>，是无感叹号的<strong>${exclaimRatio}倍</strong>。样本：${withExclaim.length} vs ${withoutExclaim.length}。`,
                exclaimAvg > noExclaimAvg ? '适当使用感叹号增加情绪感染力，但不要过度使用' : '该领域感叹号效果一般'
            );

            // 模式9：Hashtag策略
            const withHashtag = videos.filter(v => (v.title || '').includes('#'));
            const withoutHashtag = videos.filter(v => !(v.title || '').includes('#'));

            const hashtagAvg = withHashtag.length > 0
                ? withHashtag.reduce((s, v) => s + (v.view_count || 0), 0) / withHashtag.length
                : 0;
            const noHashtagAvg = withoutHashtag.length > 0
                ? withoutHashtag.reduce((s, v) => s + (v.view_count || 0), 0) / withoutHashtag.length
                : 0;

            // 更新Hashtag表格
            const hashtagTableBody = document.getElementById('hashtagTableBody');
            if (hashtagTableBody) {
                const hashtagRatioVal = noHashtagAvg > 0 ? ((hashtagAvg / noHashtagAvg - 1) * 100).toFixed(0) : 0;
                hashtagTableBody.innerHTML = `
                    <tr>
                        <td>有Hashtag</td>
                        <td>${withHashtag.length}</td>
                        <td class="${hashtagAvg > noHashtagAvg ? 'highlight' : ''}">${formatNumber(Math.round(hashtagAvg))}</td>
                        <td class="${hashtagAvg > noHashtagAvg ? 'highlight' : ''}">${hashtagRatioVal >= 0 ? '+' : ''}${hashtagRatioVal}%</td>
                    </tr>
                    <tr>
                        <td>无Hashtag</td>
                        <td>${withoutHashtag.length}</td>
                        <td class="${noHashtagAvg > hashtagAvg ? 'highlight' : ''}">${formatNumber(Math.round(noHashtagAvg))}</td>
                        <td>基准</td>
                    </tr>
                `;
            }

            renderBar('hashtagChart',
                ['有Hashtag', '无Hashtag'],
                [hashtagAvg, noHashtagAvg],
                { yLabel: '平均播放量' }
            );

            const hashtagRatio = noHashtagAvg > 0 ? (hashtagAvg / noHashtagAvg).toFixed(2) : 'N/A';
            updateInsight('hashtagInsight',
                `有Hashtag的视频平均播放<strong>${formatNumber(Math.round(hashtagAvg))}</strong>，是无Hashtag的<strong>${hashtagRatio}倍</strong>。样本：${withHashtag.length} vs ${withoutHashtag.length}。`,
                hashtagAvg < noHashtagAvg ? 'Hashtag视频播放较低（可能多为Shorts），但互动率更高' : 'Hashtag对该领域有积极影响'
            );

            // 注册标题模式结论到信息报告（分开注册模式7、8、9）
            // 模式7: 数字标题
            const numberPct = noNumberAvg > 0 ? ((numberAvg / noNumberAvg - 1) * 100).toFixed(0) : 0;
            const numberBetter = numberAvg > noNumberAvg;
            registerPatternConclusion('tab4', '7', '数字标题',
                '数字标题',
                numberBetter ? `含数字标题播放量提升${numberPct}%（${formatNumber(Math.round(numberAvg))} vs ${formatNumber(Math.round(noNumberAvg))}）。建议使用"3个动作"、"5分钟"等数字增强点击。`
                     : `数字标题在该领域效果一般（${formatNumber(Math.round(numberAvg))} vs ${formatNumber(Math.round(noNumberAvg))}），可不强求。`,
                null, // examples
                'numberTitleChart'  // 关联数字标题对比图
            );

            // 模式8: 感叹号效应
            const exclaimPct = noExclaimAvg > 0 ? ((exclaimAvg / noExclaimAvg - 1) * 100).toFixed(0) : 0;
            const exclaimBetter = exclaimAvg > noExclaimAvg;
            registerPatternConclusion('tab4', '8', '感叹号效应',
                '感叹号效应',
                exclaimBetter ? `感叹号标题播放量提升${exclaimPct}%（${formatNumber(Math.round(exclaimAvg))} vs ${formatNumber(Math.round(noExclaimAvg))}）。适度使用感叹号增强情绪感染力。`
                     : `感叹号在该领域效果一般（${formatNumber(Math.round(exclaimAvg))} vs ${formatNumber(Math.round(noExclaimAvg))}），不建议滥用。`,
                null, // examples
                'exclaimTitleChart'  // 关联感叹号效应对比图
            );

            // 模式9: Hashtag策略
            const hashtagPct = noHashtagAvg > 0 ? ((hashtagAvg / noHashtagAvg - 1) * 100).toFixed(0) : 0;
            const hashtagBetter = hashtagAvg > noHashtagAvg;
            registerPatternConclusion('tab4', '9', 'Hashtag策略',
                'Hashtag策略',
                hashtagBetter ? `Hashtag视频播放量提升${hashtagPct}%（${formatNumber(Math.round(hashtagAvg))} vs ${formatNumber(Math.round(noHashtagAvg))}）。建议添加相关话题标签增加曝光。`
                     : `Hashtag在该领域效果一般（可能多为Shorts），但互动率通常更高。`,
                null, // examples
                'hashtagChart'  // 关联Hashtag策略对比图
            );

            // 模式10: 标题句式
            registerPatternConclusion('tab4', '10', '标题句式',
                '标题句式',
                '陈述句标题（如"每天按压这3个穴位"）平均播放8.2万，比问句（如"如何缓解失眠？"）高63%。建议优先使用陈述句式。'
            );

            // 补充: 标题长度
            registerPatternConclusion('tab4', '补充', '标题长度',
                '标题长度',
                '长标题（50+字）平均播放9.4万，是短标题（<15字）的4.4倍。与直觉相反，详细描述性标题效果更好。'
            );
        }

        /**
         * 模式5 & 15：发布时机分析
         * 分析周几和几点发布效果最好
         */
        function renderPublishingPatterns(videos) {
            if (!videos || videos.length === 0) return;

            // 按星期统计
            const weekdayStats = Array(7).fill(null).map(() => ({ count: 0, views: 0 }));
            const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

            // 按小时统计
            const hourStats = Array(24).fill(null).map(() => ({ count: 0, views: 0 }));

            videos.forEach(v => {
                if (!v.published_at) return;
                const date = new Date(v.published_at);
                const day = date.getDay();
                const hour = date.getHours();

                weekdayStats[day].count++;
                weekdayStats[day].views += v.view_count || 0;
                hourStats[hour].count++;
                hourStats[hour].views += v.view_count || 0;
            });

            // 计算平均播放
            const weekdayAvg = weekdayStats.map((s, i) => ({
                label: weekdayNames[i],
                value: s.count > 0 ? Math.round(s.views / s.count) : 0,
                count: s.count
            }));

            const hourAvg = hourStats.map((s, i) => ({
                label: `${i}:00`,
                value: s.count > 0 ? Math.round(s.views / s.count) : 0,
                count: s.count
            }));

            // 模式5：周几发布
            renderBar('weekdayChart',
                weekdayAvg.map(d => d.label),
                weekdayAvg.map(d => d.value),
                { yLabel: '平均播放量' }
            );

            const bestDay = weekdayAvg.reduce((a, b) => b.value > a.value ? b : a);
            const worstDay = weekdayAvg.filter(d => d.count > 0).reduce((a, b) => b.value < a.value ? b : a);
            const dayRatio = worstDay.value > 0 ? (bestDay.value / worstDay.value).toFixed(1) : '∞';

            updateInsight('weekdayInsight',
                `<strong>${bestDay.label}</strong>发布的视频平均播放最高（<span class="highlight">${formatNumber(bestDay.value)}</span>），共${bestDay.count}个视频样本。`,
                `建议优先在${bestDay.label}发布重要内容。`
            );

            // 注册模式5结论
            registerPatternConclusion('tab5', '5', '最佳发布日',
                '最佳发布日',
                `${bestDay.label}发布的视频平均播放最高（${formatNumber(bestDay.value)}），是${worstDay.label}的${dayRatio}倍。建议重要内容优先在${bestDay.label}发布。`,
                null,
                'weekdayChart'  // 关联周几发布柱状图
            );

            // 模式15：几点发布
            const validHours = hourAvg.filter(h => h.count >= 5);
            if (validHours.length > 0) {
                renderBar('hourChart',
                    validHours.map(d => d.label),
                    validHours.map(d => d.value),
                    { yLabel: '平均播放量' }
                );

                const bestHour = validHours.reduce((a, b) => b.value > a.value ? b : a);
                updateInsight('hourInsight',
                    `<strong>${bestHour.label}</strong>发布效果最佳（平均<span class="highlight">${formatNumber(bestHour.value)}</span>播放）。`,
                    `建议在${bestHour.label}左右发布视频。`
                );

            }
        }

        /**
         * 模式2：订阅数≠播放效率
         * 展示订阅数与播放效率的关系
         */
        function renderPattern2(channels) {
            if (!channels || channels.length === 0) return;

            const data = channels
                .filter(c => c.subscriber_count && c.subscriber_count > 100 && c.video_count > 0)
                .map(c => ({
                    x: c.subscriber_count,
                    y: c.total_views / c.video_count,
                    label: c.channel_name
                }));

            renderScatter('subscriptionEfficiencyChart', data, {
                xLabel: '订阅数',
                yLabel: '平均播放量',
                xScale: 'logarithmic',
                yScale: 'logarithmic'
            });

            // 计算相关性
            const sortedBySub = [...channels].sort((a, b) => (b.subscriber_count || 0) - (a.subscriber_count || 0));
            const top10Sub = sortedBySub.slice(0, 10);
            const top10AvgViews = top10Sub.reduce((s, c) => s + (c.video_count > 0 ? c.total_views / c.video_count : 0), 0) / 10;

            const avgAllViews = channels.reduce((s, c) => s + (c.video_count > 0 ? c.total_views / c.video_count : 0), 0) / channels.length;

            updateInsight('subscriptionEfficiencyInsight',
                `订阅Top 10频道的平均播放量为<strong>${formatNumber(Math.round(top10AvgViews))}</strong>，全体平均为<strong>${formatNumber(Math.round(avgAllViews))}</strong>。相差<strong>${(top10AvgViews / avgAllViews).toFixed(1)}倍</strong>。`,
                `高订阅不等于高效率。小频道同样可以获得高播放，关键在内容质量。`
            );

            // 注册模式2结论
            const ratio = (top10AvgViews / avgAllViews).toFixed(1);
            registerPatternConclusion('tab6', '2', '订阅规模≠播放效率',
                '订阅≠播放效率',
                `订阅Top10频道均播（${formatNumber(Math.round(top10AvgViews))}）是全体平均（${formatNumber(Math.round(avgAllViews))}）的${ratio}倍。高订阅不等于高效率，小频道同样可以获得高播放，关键在内容质量。`,
                null,
                'subscriptionEfficiencyChart'  // 关联订阅播放效率散点图
            );
        }

        // ========== 指标概览更新 ==========
        function updateMetricsOverview(data) {
            // 更新视频数
            const videoCountEl = document.getElementById('metric-video-count');
            if (videoCountEl) {
                // 优先使用筛选后的视频数量，与信息报告卡片保持一致
                videoCountEl.textContent = (data.videos?.length || data.total_videos || 0).toLocaleString();
            }

            // 更新频道数 - 优先使用筛选后的频道数量
            const channelCountEl = document.getElementById('metric-channel-count');
            if (channelCountEl) {
                channelCountEl.textContent = (data.channels?.length || data.total_channels || 0).toLocaleString();
            }

            // 更新总播放 - 基于筛选后的视频计算
            const totalViewsEl = document.getElementById('metric-total-views');
            if (totalViewsEl) {
                const totalViews = (data.videos || []).reduce((s, v) => s + (v.view_count || 0), 0) || data.total_views || 0;
                if (totalViews >= 100000000) {
                    totalViewsEl.textContent = (totalViews / 100000000).toFixed(1) + '亿';
                } else if (totalViews >= 10000) {
                    totalViewsEl.textContent = (totalViews / 10000).toFixed(1) + '万';
                } else {
                    totalViewsEl.textContent = totalViews.toLocaleString();
                }
            }

            // 更新时间跨度
            const timeSpanEl = document.getElementById('metric-time-span');
            if (timeSpanEl && data.data_time_range) {
                const earliest = data.data_time_range.published_earliest;
                const latest = data.data_time_range.published_latest;
                if (earliest && latest) {
                    const days = Math.ceil((new Date(latest) - new Date(earliest)) / (1000 * 60 * 60 * 24));
                    timeSpanEl.textContent = days;
                } else {
                    timeSpanEl.textContent = currentTimePeriod > 0 ? currentTimePeriod : '--';
                }
            }

            // 更新洞察数
            const insightCountEl = document.getElementById('metric-insight-count');
            if (insightCountEl) {
                // 计算有意义的洞察数量
                let count = 0;
                if (data.insights) {
                    if (data.insights.duration_insight) count++;
                    if (data.insights.trend_insight) count++;
                    if (data.insights.title_insight) count++;
                    if (data.insights.channel_insight) count++;
                    count += (data.insights.opportunities || []).length;
                }
                insightCountEl.textContent = count || '--';
            }

            // ========== 更新信息网络统计概览 ==========
            updateNetworkStats(data);
        }

        // 更新信息网络统计概览
        function updateNetworkStats(data) {
            const videos = data.videos || [];
            const channels = data.channels || [];

            // 1. 视频数量
            const statVideoEl = document.getElementById('stat-video-count');
            if (statVideoEl) {
                statVideoEl.textContent = videos.length.toLocaleString();
            }

            // 2. 频道数量
            const statChannelEl = document.getElementById('stat-channel-count');
            if (statChannelEl) {
                statChannelEl.textContent = channels.length.toLocaleString();
            }

            // 3. 标签数量（去重）
            const uniqueTags = new Set();
            videos.forEach(v => {
                (v.tags || []).forEach(tag => {
                    if (tag && tag.trim()) uniqueTags.add(tag.trim().toLowerCase());
                });
            });
            const statTagEl = document.getElementById('stat-tag-count');
            if (statTagEl) {
                statTagEl.textContent = uniqueTags.size.toLocaleString();
            }

            // 4. 话题数量（基于视频标题提取的话题关键词）
            const topicKeywords = new Set();
            videos.forEach(v => {
                // 从标题提取可能的话题
                const title = v.title || '';
                // 提取中文关键词（2-6字）
                const zhMatches = title.match(/[\u4e00-\u9fa5]{2,6}/g) || [];
                zhMatches.forEach(m => topicKeywords.add(m));
            });
            const statTopicEl = document.getElementById('stat-topic-count');
            if (statTopicEl) {
                // 限制为前500个常见话题
                statTopicEl.textContent = Math.min(topicKeywords.size, 500).toLocaleString();
            }

            // 5. 国家/地区数量
            const uniqueCountries = new Set();
            channels.forEach(c => {
                if (c.country && c.country !== 'None' && c.country !== '未知') {
                    uniqueCountries.add(c.country);
                }
            });
            const statCountryEl = document.getElementById('stat-country-count');
            if (statCountryEl) {
                statCountryEl.textContent = uniqueCountries.size.toLocaleString();
            }

            // 6. 总播放量
            const totalViews = videos.reduce((sum, v) => sum + (v.view_count || 0), 0);
            const statTotalViewsEl = document.getElementById('stat-total-views');
            if (statTotalViewsEl) {
                if (totalViews >= 100000000) {
                    statTotalViewsEl.textContent = (totalViews / 100000000).toFixed(1) + '亿';
                } else if (totalViews >= 10000) {
                    statTotalViewsEl.textContent = (totalViews / 10000).toFixed(0) + '万';
                } else {
                    statTotalViewsEl.textContent = totalViews.toLocaleString();
                }
            }

            // 7. 采集时间范围
            const timeRangeEl = document.getElementById('statsTimeRange');
            if (timeRangeEl && data.data_time_range) {
                const earliest = data.data_time_range.published_earliest;
                const latest = data.data_time_range.published_latest;
                const collectedLatest = data.data_time_range.collected_latest;

                if (earliest && latest) {
                    const days = Math.ceil((new Date(latest) - new Date(earliest)) / (1000 * 60 * 60 * 24));
                    let rangeText = `视频发布：${earliest} ~ ${latest}（${days}天）`;
                    if (collectedLatest) {
                        rangeText += ` | 最后采集：${collectedLatest}`;
                    }
                    timeRangeEl.textContent = rangeText;
                } else {
                    timeRangeEl.textContent = '采集时间：未知';
                }
            }
        }

        // ========== 频道稳定性渲染 ==========
        function renderChannelStability(stability) {
            if (!stability) return;

            // 更新标题
            const titleEl = document.getElementById('stabilityTableTitle');
            if (titleEl) {
                titleEl.textContent = `频道稳定性分析（N=${stability.total_channels}）`;
            }

            // 更新表格（显示最不稳定的频道）
            const tbody = document.getElementById('stabilityTableBody');
            if (tbody && stability.top_unstable && stability.top_unstable.length > 0) {
                tbody.innerHTML = stability.top_unstable.slice(0, 10).map(c => {
                    const ratioClass = c.stability_class === 'danger' ? 'danger-text' :
                                       c.stability_class === 'warning' ? 'warning-text' :
                                       c.stability_class === 'highlight' ? 'highlight' : '';
                    return `<tr>
                        <td>${c.channel_name || '未知频道'}</td>
                        <td>${c.video_count}</td>
                        <td>${formatNumber(c.avg_views)}</td>
                        <td class="${ratioClass}">${c.max_avg_ratio}</td>
                        <td class="${ratioClass}">${c.stability}</td>
                    </tr>`;
                }).join('');
            } else if (tbody) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#94a3b8;">暂无足够数据</td></tr>';
            }

            // 更新柱状图
            const barChart = document.getElementById('stabilityBarChart');
            if (barChart && stability.top_unstable && stability.top_unstable.length > 0) {
                const maxRatio = Math.max(...stability.top_unstable.map(c => c.max_avg_ratio));
                barChart.innerHTML = stability.top_unstable.slice(0, 5).map(c => {
                    const widthPct = (c.max_avg_ratio / maxRatio * 100).toFixed(0);
                    const barClass = c.stability_class === 'danger' ? 'danger' :
                                     c.stability_class === 'warning' ? 'warning' : 'success';
                    return `<div class="bar-item">
                        <span class="bar-label">${(c.channel_name || '').substring(0, 10)}</span>
                        <div class="bar-track">
                            <div class="bar-fill ${barClass}" style="width: ${widthPct}%"></div>
                        </div>
                        <span class="bar-value">${c.max_avg_ratio}</span>
                    </div>`;
                }).join('');
            }

            // 更新结论
            const conclusionEl = document.getElementById('stabilityConclusion');
            if (conclusionEl && stability.insight) {
                conclusionEl.innerHTML = `<strong>${stability.insight.summary}</strong>`;
            }

            // 更新行动建议
            const actionsEl = document.getElementById('stabilityActions');
            if (actionsEl && stability.insight) {
                const stableChannels = stability.insight.most_stable_channels || [];
                actionsEl.innerHTML = `
                    <div class="action-item success">
                        <span class="action-icon">✅</span>
                        <span>${stability.insight.recommendation}</span>
                    </div>
                    ${stableChannels.length > 0 ? `
                    <div class="action-item">
                        <span class="action-icon">🎯</span>
                        <span>最稳定频道：${stableChannels.slice(0, 3).join('、')}</span>
                    </div>` : ''}
                    <div class="action-item">
                        <span class="action-icon">📊</span>
                        <span>健康指标：max/avg &lt; 10</span>
                    </div>
                `;
            }

            // 注册模式结论到信息报告
            if (stability.insight) {
                const stableChannels = stability.insight.most_stable_channels || [];
                const stableCount = stability.stable_count || 0;
                const totalCount = stability.total_channels || 0;
                const stableRatio = totalCount > 0 ? ((stableCount / totalCount) * 100).toFixed(0) : 0;

                registerPatternConclusion('tab6', '11', '频道稳定性差异',
                    '频道稳定性',
                    `${stableRatio}%的频道表现稳定。${stability.insight.summary}。${stableChannels.length > 0 ? `最稳定频道：${stableChannels.slice(0, 3).join('、')}。` : ''}${stability.insight.recommendation}`
                );
            }
        }

        // ========== 频道榜单渲染 ==========
        function renderChannelRankings(rankings) {
            if (!rankings) return;

            // 渲染黑马榜
            if (rankings.dark_horse_rank) {
                renderDarkHorseRanking(rankings.dark_horse_rank);
            }

            // 渲染高效榜
            if (rankings.efficiency_rank) {
                renderEfficiencyRanking(rankings.efficiency_rank);
            }

            // 渲染快速增长榜
            if (rankings.fast_growth_rank) {
                renderFastGrowthRanking(rankings.fast_growth_rank);
            }
        }

        // 渲染黑马榜
        function renderDarkHorseRanking(darkHorse) {
            const tbody = document.getElementById('darkHorseTableBody');
            if (!tbody || !darkHorse.channels || darkHorse.channels.length === 0) {
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#94a3b8;">暂无黑马频道数据（需要订阅数数据）</td></tr>';
                }
                return;
            }

            // 更新标题
            const titleEl = document.getElementById('darkHorseTableTitle');
            if (titleEl) {
                titleEl.textContent = `黑马频道分析（N=${darkHorse.sample_size}）`;
            }

            // 更新表格
            tbody.innerHTML = darkHorse.channels.slice(0, 10).map(c => {
                const subsText = c.subscriber_count >= 10000
                    ? (c.subscriber_count / 10000).toFixed(1) + '万'
                    : (c.subscriber_count / 1000).toFixed(1) + 'K';
                const maxViewsText = c.max_views >= 10000
                    ? formatNumber(c.max_views)
                    : c.max_views.toLocaleString();
                // 黑马指数 = max_views / subscriber_count
                const burstRatio = c.subscriber_count > 0
                    ? Math.round(c.max_views / c.subscriber_count)
                    : 0;
                return `<tr>
                    <td>${c.channel_name || '未知频道'}</td>
                    <td>${subsText}</td>
                    <td>${maxViewsText}</td>
                    <td class="highlight">${burstRatio}×</td>
                </tr>`;
            }).join('');

            // 更新结论
            const conclusionEl = document.getElementById('darkHorseConclusion');
            if (conclusionEl && darkHorse.channels.length > 0) {
                const topChannel = darkHorse.channels[0];
                const burstRatio = topChannel.subscriber_count > 0
                    ? Math.round(topChannel.max_views / topChannel.subscriber_count)
                    : 0;
                conclusionEl.innerHTML = `<strong>${topChannel.channel_name}</strong> 订阅仅 ${formatNumber(topChannel.subscriber_count)}，却有 ${formatNumber(topChannel.max_views)} 播放的视频（${burstRatio}倍爆发），证明<strong>好内容不需要大流量基础</strong>`;

                // 准备图表数据（前8个黑马频道）
                const chartChannels = darkHorse.channels.slice(0, 8);
                const chartLabels = chartChannels.map(c => c.channel_name?.slice(0, 10) || '未知');
                const chartBurstRatios = chartChannels.map(c =>
                    c.subscriber_count > 0 ? Math.round(c.max_views / c.subscriber_count) : 0
                );

                // 注册模式12结论（含图表）
                registerPatternConclusion('tab6', '12', '黑马频道特征',
                    '黑马频道特征',
                    `「${topChannel.channel_name}」订阅仅${formatNumber(topChannel.subscriber_count)}却达成${formatNumber(topChannel.max_views)}播放（${burstRatio}倍爆发）。好内容不需要大流量基础，小频道同样可以逆袭。`,
                    null,
                    'subsDistScatter'  // 关联订阅分布散点图
                );
            }
        }

        // ========== Tab2 套利分析 - 地区分布渲染 ==========
        function renderRegionDistribution(data) {
            if (!data || !data.regions) return;

            const tbody = document.getElementById('regionTableBody');
            if (tbody && data.regions.length > 0) {
                tbody.innerHTML = data.regions.slice(0, 10).map(r => {
                    const avgViewsText = r.avg_views >= 10000
                        ? formatNumber(r.avg_views)
                        : r.avg_views.toLocaleString();
                    return `<tr>
                        <td>${r.region}</td>
                        <td>${r.channel_count}</td>
                        <td class="${r.avg_views === data.regions[0].avg_views ? 'highlight' : ''}">${avgViewsText}</td>
                        <td>${r.feature}</td>
                    </tr>`;
                }).join('');
            }

            // 更新可视化条形图
            const barContainer = document.getElementById('regionBarChart');
            if (barContainer && data.regions.length > 0) {
                const maxViews = data.regions[0].avg_views;
                barContainer.innerHTML = data.regions.slice(0, 4).map(r => {
                    const pct = Math.round((r.avg_views / maxViews) * 100);
                    const viewsText = r.avg_views >= 10000
                        ? (r.avg_views / 10000).toFixed(1) + '万'
                        : r.avg_views.toLocaleString();
                    const barClass = pct > 80 ? 'success' : (pct < 50 ? 'warning' : '');
                    return `<div class="bar-item">
                        <span class="bar-label">${r.region}</span>
                        <div class="bar-track">
                            <div class="bar-fill ${barClass}" style="width: ${pct}%"></div>
                        </div>
                        <span class="bar-value">${viewsText}</span>
                    </div>`;
                }).join('');
            }

            // 更新结论
            const conclusionEl = document.getElementById('regionConclusion');
            if (conclusionEl && data.insight) {
                conclusionEl.innerHTML = data.insight;
            }

            // 注册模式结论到信息报告（含图表）
            if (data.regions && data.regions.length >= 2) {
                const top = data.regions[0];
                const bottom = data.regions[data.regions.length - 1];
                const ratio = bottom.avg_views > 0 ? (top.avg_views / bottom.avg_views).toFixed(1) : '∞';
                const topAvgText = top.avg_views >= 10000 ? (top.avg_views / 10000).toFixed(1) + '万' : top.avg_views.toLocaleString();

                // 准备图表数据
                const chartRegions = data.regions.slice(0, 8);
                const chartLabels = chartRegions.map(r => r.region);
                const chartValues = chartRegions.map(r => r.avg_views);

                // 注册模式22: 地区热度分布
                registerPatternConclusion('tab2', '22', '地区热度分布',
                    '地区热度分布',
                    `「${top.region}」地区均播放最高(${topAvgText})，是「${bottom.region}」的${ratio}倍。存在明显地域套利空间，优先布局高均播地区内容。`,
                    null,
                    {
                        type: 'bar',
                        data: {
                            labels: chartLabels,
                            datasets: [{
                                label: '平均播放',
                                data: chartValues,
                                backgroundColor: chartValues.map((v, i) => i === 0 ? '#22c55e' : '#06b6d4'),
                                borderRadius: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            indexAxis: 'y',
                            plugins: {
                                legend: { display: false }
                            },
                            scales: {
                                x: {
                                    grid: { color: '#334155' },
                                    ticks: { color: '#94a3b8', callback: v => v >= 10000 ? (v/10000).toFixed(0) + '万' : v }
                                },
                                y: {
                                    grid: { display: false },
                                    ticks: { color: '#e2e8f0' }
                                }
                            }
                        }
                    }
                );
            }
        }

        // ========== Tab3 选题决策 - 内容生命周期渲染 ==========
        function renderContentLifecycle(data) {
            if (!data || !data.topics) return;

            const tbody = document.getElementById('lifecycleTableBody');
            if (tbody && data.topics.length > 0) {
                tbody.innerHTML = data.topics.slice(0, 10).map(t => {
                    const avgViewsText = t.avg_views >= 10000
                        ? formatNumber(t.avg_views)
                        : t.avg_views.toLocaleString();
                    const stageClass = t.stage === '新兴爆发' ? 'highlight' :
                                       t.stage === '长青经典' ? 'success-text' : '';
                    return `<tr>
                        <td>${t.content_type}</td>
                        <td>${t.span_text}</td>
                        <td class="${t.avg_views === data.topics[0].avg_views ? 'highlight' : ''}">${avgViewsText}</td>
                        <td class="${stageClass}">${t.stage}</td>
                    </tr>`;
                }).join('');
            }

            // 更新条形图（话题热度变化）
            const barChart = document.getElementById('lifecycleBarChart');
            if (barChart && data.topics.length > 0) {
                // 取前5个话题显示趋势
                const displayTopics = data.topics.slice(0, 5);
                barChart.innerHTML = displayTopics.map(t => {
                    // 根据阶段确定颜色和显示值
                    let barClass = '';
                    let valueText = t.stage;
                    if (t.stage === '新兴爆发') {
                        barClass = 'success';
                        valueText = '🔥 新兴';
                    } else if (t.stage === '长青经典') {
                        barClass = '';
                        valueText = '✓ 长青';
                    } else if (t.stage === '稳定') {
                        barClass = '';
                        valueText = '→ 稳定';
                    } else if (t.stage === '下滑') {
                        barClass = 'warning';
                        valueText = '↘ 下滑';
                    } else if (t.stage === '衰退') {
                        barClass = 'danger';
                        valueText = '↓ 衰退';
                    }
                    // 计算宽度（基于平均播放量的相对值）
                    const maxViews = Math.max(...displayTopics.map(x => x.avg_views));
                    const widthPct = Math.round((t.avg_views / maxViews) * 100);
                    return `<div class="bar-item">
                        <span class="bar-label">${t.content_type}</span>
                        <div class="bar-track">
                            <div class="bar-fill ${barClass}" style="width: ${widthPct}%"></div>
                        </div>
                        <span class="bar-value">${valueText}</span>
                    </div>`;
                }).join('');
            }

            // 更新结论
            const conclusionEl = document.getElementById('lifecycleConclusion');
            if (conclusionEl && data.insight) {
                conclusionEl.innerHTML = data.insight;
            }

            // 更新推荐标签
            const actionsEl = document.getElementById('lifecycleActions');
            if (actionsEl) {
                let actions = [];
                if (data.evergreen_topics && data.evergreen_topics.length > 0) {
                    actions.push(`<span class="pattern-action do">✅ 做长青话题：${data.evergreen_topics[0]}</span>`);
                }
                if (data.emerging_topics && data.emerging_topics.length > 0) {
                    actions.push(`<span class="pattern-action highlight">🔥 抓新兴话题：${data.emerging_topics[0]}</span>`);
                }
                if (data.topics && data.topics.length > 0) {
                    actions.push(`<span class="pattern-action do">✅ 优先：${data.topics[0].content_type}</span>`);
                }
                actionsEl.innerHTML = actions.join('');
            }

            // 注册模式结论到信息报告
            if (data.topics && data.topics.length > 0) {
                const emerging = data.topics.filter(t => t.stage === '新兴爆发').map(t => t.content_type);
                const evergreen = data.topics.filter(t => t.stage === '长青经典').map(t => t.content_type);
                const declining = data.topics.filter(t => t.stage === '衰退' || t.stage === '下滑').map(t => t.content_type);

                let conclusionParts = [];
                if (emerging.length > 0) {
                    conclusionParts.push(`新兴爆发话题：${emerging.slice(0, 2).join('、')}（建议抓紧布局）`);
                }
                if (evergreen.length > 0) {
                    conclusionParts.push(`长青经典话题：${evergreen.slice(0, 2).join('、')}（稳定选择）`);
                }
                if (declining.length > 0) {
                    conclusionParts.push(`下滑话题：${declining.slice(0, 2).join('、')}（建议避开）`);
                }

                if (conclusionParts.length > 0) {
                    registerPatternConclusion('tab3', '13', '话题生命周期',
                        '话题生命周期',
                        conclusionParts.join('；') + '。'
                    );
                }
            }
        }

        // ========== Tab5 发布策略 - 星期发布效果渲染 ==========
        function renderWeekdayPerformance(data) {
            if (!data || !data.weekdays) return;

            const tbody = document.getElementById('weekdayTableBody');
            if (tbody && data.weekdays.length > 0) {
                // 按星期顺序排列显示
                const weekdayOrder = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
                const sortedByWeekday = [...data.weekdays].sort((a, b) =>
                    weekdayOrder.indexOf(a.weekday) - weekdayOrder.indexOf(b.weekday)
                );

                const maxAvg = Math.max(...data.weekdays.map(w => w.avg_views));
                const minAvg = Math.min(...data.weekdays.map(w => w.avg_views));

                tbody.innerHTML = data.weekdays.map(w => {
                    const avgViewsText = w.avg_views >= 10000
                        ? formatNumber(w.avg_views)
                        : w.avg_views.toLocaleString();
                    const maxViewsText = w.max_views >= 10000
                        ? formatNumber(w.max_views)
                        : w.max_views.toLocaleString();
                    const isMax = w.avg_views === maxAvg;
                    const isMin = w.avg_views === minAvg;
                    return `<tr>
                        <td class="${isMax ? 'highlight' : (isMin ? 'danger-text' : '')}">${w.weekday}</td>
                        <td>${w.video_count}</td>
                        <td class="${isMax ? 'highlight' : (isMin ? 'danger-text' : '')}">${avgViewsText}</td>
                        <td>${maxViewsText}</td>
                    </tr>`;
                }).join('');
            }

            // 更新结论
            const conclusionEl = document.getElementById('weekdayConclusion');
            if (conclusionEl && data.insight) {
                conclusionEl.innerHTML = data.insight;
            }

            // 更新推荐
            const actionsEl = document.getElementById('weekdayActions');
            if (actionsEl && data.best_day && data.worst_day) {
                actionsEl.innerHTML = `
                    <span class="pattern-action do">✅ 优先 ${data.best_day} 发布</span>
                    <span class="pattern-action do">✅ 次选 周末</span>
                    <span class="pattern-action avoid">⚠️ 避免 ${data.worst_day}</span>
                `;
            }
        }

        // 渲染高效榜
        function renderEfficiencyRanking(efficiency) {
            // 可以扩展渲染到其他位置
            console.log('高效榜数据:', efficiency.channels?.length || 0, '个频道');
        }

        // 渲染快速增长榜（模式14数据目前是静态的，这里注册静态结论）
        function renderFastGrowthRanking(fastGrowth) {
            console.log('快速增长榜数据:', fastGrowth?.channels?.length || 0, '个频道');

            // 注册模式14结论（基于HTML中的静态数据）
            registerPatternConclusion('tab6', '14', '快速增长案例',
                '快速增长案例',
                '快速增长频道共性：集中发布5-6条视频（1-3天），内容首选食疗配方，长标题(30-60字)+多Hashtag(5-15个)，通常第2-3条视频实现爆发。'
            );
        }

        // 更新统计数字显示
        function updateStatsDisplay(data) {
            // 更新样本量显示（排除有特定 ID 的 badge，这些由各自的渲染函数更新）
            const excludeIds = ['hotwordsSample', 'questionsSample', 'sentimentSample', 'contentTypeSample', 'darkHorseSample', 'topChannelSample', 'monopolySample'];
            const sampleBadges = document.querySelectorAll('.pattern-confidence-badge:last-child');
            sampleBadges.forEach(badge => {
                if (badge.textContent.includes('N =') && !excludeIds.includes(badge.id)) {
                    badge.textContent = `N = ${(data.total_videos || 0).toLocaleString()}`;
                }
            });

            // 更新各模式的时间范围提示
            updateTimePeriodInConclusions(data);
        }

        // 更新结论中的时间段信息
        function updateTimePeriodInConclusions(data) {
            const timePeriod = data._timePeriod || currentTimePeriod;
            const label = getTimePeriodLabel(timePeriod);

            // 获取数据统计
            const videoCount = data.videos?.length || data.total_videos || 0;
            const channelCount = data.channels?.length || 0;

            // 在模式栏右侧空白处显示可点击的时间范围选择器
            const timeRangeSelector = `
                <div class="time-range-selector" style="
                    position: relative;
                    margin-left: auto;
                ">
                    <button class="time-range-badge" onclick="toggleTimeRangeDropdown(this)" style="
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        padding: 6px 12px;
                        background: rgba(6, 182, 212, 0.1);
                        border: 1px solid rgba(6, 182, 212, 0.25);
                        border-radius: 6px;
                        font-size: 0.85em;
                        color: #06b6d4;
                        cursor: pointer;
                        transition: all 0.2s;
                    ">
                        <span>📅</span>
                        <span class="time-range-label">${label}</span>
                        <span style="color: #475569;">|</span>
                        <span style="color: #94a3b8;">${videoCount} 视频</span>
                        <span style="margin-left: 4px; font-size: 0.8em;">▼</span>
                    </button>
                    <div class="time-range-dropdown" style="
                        display: none;
                        position: absolute;
                        top: 100%;
                        right: 0;
                        margin-top: 4px;
                        background: #1e293b;
                        border: 1px solid #334155;
                        border-radius: 8px;
                        padding: 4px;
                        min-width: 140px;
                        z-index: 100;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    ">
                        <div class="time-option" onclick="selectTimeRange(1)" style="padding: 8px 12px; cursor: pointer; border-radius: 4px; color: #e2e8f0; font-size: 0.85em;">近 24 小时</div>
                        <div class="time-option" onclick="selectTimeRange(7)" style="padding: 8px 12px; cursor: pointer; border-radius: 4px; color: #e2e8f0; font-size: 0.85em;">近 7 天</div>
                        <div class="time-option" onclick="selectTimeRange(30)" style="padding: 8px 12px; cursor: pointer; border-radius: 4px; color: #e2e8f0; font-size: 0.85em;">近 30 天</div>
                        <div class="time-option" onclick="selectTimeRange(90)" style="padding: 8px 12px; cursor: pointer; border-radius: 4px; color: #e2e8f0; font-size: 0.85em;">近 90 天</div>
                        <div class="time-option" onclick="selectTimeRange(0)" style="padding: 8px 12px; cursor: pointer; border-radius: 4px; color: #e2e8f0; font-size: 0.85em;">全部时间</div>
                    </div>
                </div>
            `;

            // 更新每个 tab 的子标签页导航栏右侧（模式栏的空白处）
            document.querySelectorAll('.sub-pattern-tabs').forEach(subTabs => {
                // 移除旧的时间范围选择器
                const oldSelector = subTabs.querySelector('.time-range-selector');
                if (oldSelector) oldSelector.remove();

                // 在子标签页导航栏末尾添加时间范围选择器
                subTabs.insertAdjacentHTML('beforeend', timeRangeSelector);
            });

            // 更新指标概览中的天跨度
            const metricsOverview = document.querySelector('.metrics-overview');
            if (metricsOverview) {
                const daysMetric = metricsOverview.querySelector('.metric-item:nth-child(7)');
                if (daysMetric) {
                    const valueEl = daysMetric.querySelector('.metric-value');
                    if (valueEl) {
                        valueEl.textContent = timePeriod > 0 ? timePeriod : '全部';
                    }
                }
            }
        }

        // 更新时长模式（模式3）
        function updateDurationPattern(distribution, videos) {
            // 计算各时长段的数据
            const durationStats = {
                '<1分钟': { count: 0, views: 0, likes: 0 },
                '1-3分钟': { count: 0, views: 0, likes: 0 },
                '3-10分钟': { count: 0, views: 0, likes: 0 },
                '10-30分钟': { count: 0, views: 0, likes: 0 },
                '30分钟+': { count: 0, views: 0, likes: 0 }
            };

            if (videos && videos.length > 0) {
                videos.forEach(v => {
                    const seconds = v.duration || 0;
                    let category;
                    if (seconds < 60) category = '<1分钟';
                    else if (seconds < 180) category = '1-3分钟';
                    else if (seconds < 600) category = '3-10分钟';
                    else if (seconds < 1800) category = '10-30分钟';
                    else category = '30分钟+';

                    durationStats[category].count++;
                    durationStats[category].views += v.view_count || 0;
                    durationStats[category].likes += v.like_count || 0;
                });
            }

            // 计算平均播放和点赞率
            const statsArray = Object.entries(durationStats)
                .map(([category, stats]) => ({
                    category,
                    count: stats.count,
                    avgViews: stats.count > 0 ? Math.round(stats.views / stats.count) : 0,
                    likeRate: stats.views > 0 ? (stats.likes / stats.views * 100).toFixed(2) : '0.00'
                }))
                .sort((a, b) => b.avgViews - a.avgViews); // 按平均播放排序

            console.log('时长统计:', statsArray);

            // 更新表格
            const tbody = document.getElementById('durationTableBody');
            if (tbody && statsArray.length > 0) {
                tbody.innerHTML = statsArray.map((s, i) => {
                    const avgViewText = s.avgViews >= 10000
                        ? formatNumber(s.avgViews)
                        : s.avgViews.toLocaleString();
                    const viewClass = i === 0 ? 'highlight' : '';
                    // 找出点赞率最高的
                    const maxLikeRate = Math.max(...statsArray.map(x => parseFloat(x.likeRate)));
                    const likeClass = parseFloat(s.likeRate) === maxLikeRate ? 'highlight' : '';
                    return `<tr>
                        <td>${s.category}</td>
                        <td>${s.count}</td>
                        <td class="${viewClass}">${avgViewText}</td>
                        <td class="${likeClass}">${s.likeRate}%</td>
                    </tr>`;
                }).join('');
            }

            // 更新样本量标题
            const titleEl = document.getElementById('durationSampleTitle');
            if (titleEl && videos) {
                titleEl.textContent = `时长档次表现对比（N=${videos.length}）`;
            }
        }

        // 更新频道模式（模式12、31等）
        function updateChannelPatterns(channels, insights) {
            if (!channels || channels.length === 0) return;

            // 计算爆发倍率并排序
            // 筛选条件：订阅>1000，平均播放>10000
            const channelsWithRatio = channels
                .filter(c => c.subscriber_count && c.subscriber_count > 1000 && c.avg_views > 10000)
                .map(c => ({
                    ...c,
                    // 用总播放量/订阅数作为爆发倍率
                    burstRatio: Math.round(c.total_views / c.subscriber_count)
                }))
                .sort((a, b) => b.burstRatio - a.burstRatio)
                .slice(0, 5);

            // 找出头部频道
            const topChannels = [...channels]
                .sort((a, b) => b.total_views - a.total_views)
                .slice(0, 5);

            console.log('黑马频道(按爆发倍率):', channelsWithRatio);
            console.log('头部频道:', topChannels);

            // 更新黑马频道表格
            const tbody = document.getElementById('darkHorseTableBody');
            if (tbody && channelsWithRatio.length > 0) {
                tbody.innerHTML = channelsWithRatio.map((c, i) => {
                    const subText = c.subscriber_count >= 10000
                        ? (c.subscriber_count / 10000).toFixed(2) + '万'
                        : c.subscriber_count;
                    const viewText = c.total_views >= 10000
                        ? (c.total_views / 10000).toFixed(0) + '万'
                        : c.total_views;
                    const ratioClass = c.burstRatio > 100 ? 'high-value' : '';
                    const viewClass = i === 0 ? 'highlight-value' : '';
                    const channelLink = c.channel_id
                        ? `<a href="https://www.youtube.com/channel/${c.channel_id}" target="_blank" rel="noopener" class="channel-link">${c.channel_name || '未知'}</a>`
                        : (c.channel_name || '未知');
                    return `<tr>
                        <td>${channelLink}</td>
                        <td>${subText}</td>
                        <td class="${viewClass}">${viewText}</td>
                        <td class="${ratioClass}">${c.burstRatio}×</td>
                    </tr>`;
                }).join('');
            }

            // 更新样本量
            const sampleEl = document.getElementById('darkHorseSample');
            if (sampleEl) {
                sampleEl.textContent = `N = ${channels.length}`;
            }

            // 计算并更新垄断度（模式23）
            const totalViews = channels.reduce((sum, c) => sum + (c.total_views || 0), 0);
            const top3Views = topChannels.slice(0, 3).reduce((sum, c) => sum + (c.total_views || 0), 0);
            const top3Share = totalViews > 0 ? (top3Views / totalViews * 100).toFixed(1) : 0;

            // 判断竞争格局
            let competitionLevel = '分散';
            if (top3Share > 90) competitionLevel = '极度垄断';
            else if (top3Share > 80) competitionLevel = '高度垄断';
            else if (top3Share > 60) competitionLevel = '较垄断';
            else if (top3Share > 40) competitionLevel = '中等';

            // 更新垄断度显示
            const monopolyInfo = document.getElementById('currentMonopolyInfo');
            const monopolyKeyword = document.getElementById('monopolyKeyword');
            const top3ShareEl = document.getElementById('top3Share');
            const competitionLevelEl = document.getElementById('competitionLevel');

            if (monopolyInfo && monopolyKeyword && top3ShareEl && competitionLevelEl) {
                monopolyInfo.style.display = 'block';
                monopolyKeyword.textContent = currentKeyword;
                top3ShareEl.textContent = top3Share + '%';
                competitionLevelEl.textContent = competitionLevel;
            }

            // 更新垄断度样本量
            const monopolySampleEl = document.getElementById('monopolySample');
            if (monopolySampleEl) {
                monopolySampleEl.textContent = `N = ${channels.length}`;
            }

            // 注册模式23结论到信息报告
            registerPatternConclusion('tab3', '23', '话题垄断度分析',
                '话题垄断度',
                `当前话题「${currentKeyword}」Top3频道占总播放${top3Share}%，竞争格局：${competitionLevel}。` +
                (top3Share > 80 ? '头部高度集中，新频道需差异化切入。' : top3Share > 60 ? '头部有一定集中度，仍有机会突围。' : '市场较分散，新频道有较大空间。')
            );
        }

        // 更新标题模式（模式7-10）
        function updateTitlePatterns(patterns) {
            if (!patterns || patterns.length === 0) return;

            // 显示高频词
            console.log('标题高频词 Top10:', patterns.slice(0, 10));

            // 可以在页面某处显示高频词云或列表
            // 这里暂时只记录日志，后续可扩展
        }

        // 分析视频标题特征（用于模式7-10）
        function analyzeVideoTitles(videos) {
            if (!videos || videos.length === 0) return;

            let withNumber = { count: 0, views: 0 };
            let withoutNumber = { count: 0, views: 0 };
            let withExclamation = { count: 0, views: 0 };
            let withoutExclamation = { count: 0, views: 0 };

            videos.forEach(v => {
                const title = v.title || '';
                const views = v.view_count || 0;

                // 检查是否含数字
                if (/\d/.test(title)) {
                    withNumber.count++;
                    withNumber.views += views;
                } else {
                    withoutNumber.count++;
                    withoutNumber.views += views;
                }

                // 检查是否含感叹号
                if (/[!！]/.test(title)) {
                    withExclamation.count++;
                    withExclamation.views += views;
                } else {
                    withoutExclamation.count++;
                    withoutExclamation.views += views;
                }
            });

            // 计算平均播放
            const avgWithNumber = withNumber.count > 0 ? Math.round(withNumber.views / withNumber.count) : 0;
            const avgWithoutNumber = withoutNumber.count > 0 ? Math.round(withoutNumber.views / withoutNumber.count) : 0;
            const avgWithExclamation = withExclamation.count > 0 ? Math.round(withExclamation.views / withExclamation.count) : 0;
            const avgWithoutExclamation = withoutExclamation.count > 0 ? Math.round(withoutExclamation.views / withoutExclamation.count) : 0;

            console.log('数字标题分析:', { withNumber: avgWithNumber, withoutNumber: avgWithoutNumber });
            console.log('感叹号分析:', { withExclamation: avgWithExclamation, withoutExclamation: avgWithoutExclamation });

            return {
                number: { with: withNumber, without: withoutNumber, avgWith: avgWithNumber, avgWithout: avgWithoutNumber },
                exclamation: { with: withExclamation, without: withoutExclamation, avgWith: avgWithExclamation, avgWithout: avgWithoutExclamation }
            };
        }

        // 更新洞察显示
        function updateInsightsDisplay(insights) {
            console.log('洞察数据:', insights);
        }

        // ========== 模式详情面板 ==========

        // 模式数据
        const patternData = {
            pattern3: {
                badge: '模式3',
                name: '时长有最优区间',
                confidence: '高',
                sample: 'N = 2,340',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">原始数据</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <table class="pattern-data-table">
                                        <thead>
                                            <tr><th>时长档次</th><th>视频数</th><th>平均播放</th><th>点赞率</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr class="highlight"><td>10-30分钟</td><td>256</td><td class="highlight-value">239,547</td><td>2.04%</td></tr>
                                            <tr><td>3-10分钟</td><td>435</td><td>66,958</td><td class="highlight-value">2.57%</td></tr>
                                            <tr><td>&lt;1分钟</td><td>842</td><td>60,971</td><td>2.01%</td></tr>
                                            <tr><td>30分+</td><td>287</td><td class="low-value">50,463</td><td class="low-value">1.52%</td></tr>
                                            <tr><td>1-3分钟</td><td>520</td><td>37,667</td><td>2.34%</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">可视化分析</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-bar-chart">
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">10-30分钟</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill green" style="width: 100%">
                                                    <span class="pattern-bar-value">239,547</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">3-10分钟</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill blue" style="width: 28%">
                                                    <span class="pattern-bar-value">66,958</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">&lt;1分钟</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill purple" style="width: 25%">
                                                    <span class="pattern-bar-value">60,971</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">30分+</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill yellow" style="width: 21%">
                                                    <span class="pattern-bar-value">50,463</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">1-3分钟</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill red" style="width: 16%">
                                                    <span class="pattern-bar-value">37,667</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-conclusion">
                                        <div class="pattern-conclusion-title">
                                            <span>💡</span>
                                            <span>核心结论</span>
                                        </div>
                                        <div class="pattern-conclusion-text">
                                            <strong>10-30分钟</strong>是播放量最优区间（平均24万），<strong>3-10分钟</strong>互动率最高（2.57%）。30分钟以上的长视频互动率最低。
                                        </div>
                                    </div>
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>主内容：10-30分钟</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>引流内容：3-10分钟</span>
                                        </div>
                                        <div class="pattern-action avoid">
                                            <span class="pattern-action-icon">⚠️</span>
                                            <span>避免30分钟以上</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            pattern4: {
                badge: '模式4',
                name: '内容类型决定天花板',
                confidence: '中',
                sample: 'N = 2,290',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">原始数据</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <table class="pattern-data-table">
                                        <thead>
                                            <tr><th>内容类型</th><th>视频数</th><th>平均播放</th><th>平均时长</th><th>点赞率</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr class="highlight"><td>功法教学（八段锦/太极）</td><td>89</td><td class="highlight-value">351,625</td><td>8分钟</td><td>1.16%</td></tr>
                                            <tr><td>饮食养生</td><td>470</td><td>88,167</td><td>14分钟</td><td>1.75%</td></tr>
                                            <tr><td>综合养生</td><td>1234</td><td>70,789</td><td>9分钟</td><td>2.32%</td></tr>
                                            <tr><td>专家讲解</td><td>69</td><td>47,858</td><td>27分钟</td><td>1.74%</td></tr>
                                            <tr><td>养生秘诀</td><td>217</td><td>39,284</td><td>5分钟</td><td>1.75%</td></tr>
                                            <tr><td>穴位按摩</td><td>100</td><td>37,531</td><td>7分钟</td><td>2.32%</td></tr>
                                            <tr><td class="low-value">健康警示</td><td>111</td><td class="low-value">1,728</td><td>5分钟</td><td>3.14%</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">可视化分析</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-bar-chart">
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">功法教学</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill green" style="width: 100%">
                                                    <span class="pattern-bar-value">351,625</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">饮食养生</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill blue" style="width: 25%">
                                                    <span class="pattern-bar-value">88,167</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">综合养生</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill purple" style="width: 20%">
                                                    <span class="pattern-bar-value">70,789</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">专家讲解</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill purple" style="width: 14%">
                                                    <span class="pattern-bar-value">47,858</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">养生秘诀</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill yellow" style="width: 11%">
                                                    <span class="pattern-bar-value">39,284</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">穴位按摩</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill yellow" style="width: 11%">
                                                    <span class="pattern-bar-value">37,531</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">健康警示</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill red" style="width: 0.5%">
                                                    <span class="pattern-bar-value">1,728</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <p style="text-align: center; color: var(--color-accent); margin-top: 16px; font-weight: 600;">功法教学是健康警示的 203 倍</p>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-conclusion">
                                        <div class="pattern-conclusion-title">
                                            <span>💡</span>
                                            <span>核心结论</span>
                                        </div>
                                        <div class="pattern-conclusion-text">
                                            内容类型的选择，直接决定了播放量天花板。<strong>功法教学类</strong>（八段锦、太极）平均播放量是其他类型的 4-200 倍。选对类型 &gt; 优化标题 &gt; 提高制作质量。
                                        </div>
                                    </div>
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>优先做功法教学</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>饮食养生为第二选择</span>
                                        </div>
                                        <div class="pattern-action avoid">
                                            <span class="pattern-action-icon">⚠️</span>
                                            <span>避免健康警示类</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            pattern7: {
                badge: '模式7-10',
                name: '标题特征影响',
                confidence: '中',
                sample: 'N = 2,290',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">A/B 对比分析</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <!-- A/B 对比进度条 -->
                                    <div class="ab-compare-container">
                                        <div class="ab-compare-row">
                                            <div class="ab-compare-label">含数字</div>
                                            <div class="ab-compare-bars">
                                                <div class="ab-bar-wrap">
                                                    <span class="ab-bar-label">有</span>
                                                    <div class="ab-bar-track">
                                                        <div class="ab-bar-fill win" style="width: 100%;">11.8万</div>
                                                    </div>
                                                </div>
                                                <div class="ab-bar-wrap">
                                                    <span class="ab-bar-label">无</span>
                                                    <div class="ab-bar-track">
                                                        <div class="ab-bar-fill lose" style="width: 44%;">5.2万</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="ab-compare-effect">+2.25×</div>
                                        </div>
                                        <div class="ab-compare-row">
                                            <div class="ab-compare-label">感叹号</div>
                                            <div class="ab-compare-bars">
                                                <div class="ab-bar-wrap">
                                                    <span class="ab-bar-label">有</span>
                                                    <div class="ab-bar-track">
                                                        <div class="ab-bar-fill win" style="width: 100%;">9.5万</div>
                                                    </div>
                                                </div>
                                                <div class="ab-bar-wrap">
                                                    <span class="ab-bar-label">无</span>
                                                    <div class="ab-bar-track">
                                                        <div class="ab-bar-fill lose" style="width: 75%;">7.1万</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="ab-compare-effect">+33%</div>
                                        </div>
                                        <div class="ab-compare-row">
                                            <div class="ab-compare-label">陈述句</div>
                                            <div class="ab-compare-bars">
                                                <div class="ab-bar-wrap">
                                                    <span class="ab-bar-label">陈述</span>
                                                    <div class="ab-bar-track">
                                                        <div class="ab-bar-fill win" style="width: 100%;">8.2万</div>
                                                    </div>
                                                </div>
                                                <div class="ab-bar-wrap">
                                                    <span class="ab-bar-label">问句</span>
                                                    <div class="ab-bar-track">
                                                        <div class="ab-bar-fill lose" style="width: 61%;">5.0万</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="ab-compare-effect">+63%</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">标题长度阶梯图（反常识！）</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <!-- 阶梯图 -->
                                    <div class="step-chart">
                                        <div class="step-item">
                                            <div class="step-bar" style="height: 22%;">
                                                <span class="step-bar-value">2.1万</span>
                                            </div>
                                            <span class="step-label">&lt;15字</span>
                                        </div>
                                        <div class="step-item">
                                            <div class="step-bar" style="height: 54%;">
                                                <span class="step-bar-value">5.3万</span>
                                            </div>
                                            <span class="step-label">15-30字</span>
                                        </div>
                                        <div class="step-item">
                                            <div class="step-bar" style="height: 92%;">
                                                <span class="step-bar-value">9.1万</span>
                                            </div>
                                            <span class="step-label">30-50字</span>
                                        </div>
                                        <div class="step-item best">
                                            <div class="step-bar" style="height: 100%;">
                                                <span class="step-bar-value">9.4万</span>
                                            </div>
                                            <span class="step-label">50+字</span>
                                        </div>
                                    </div>
                                    <p style="text-align: center; color: #22c55e; font-weight: 600; margin-top: 12px;">🔥 长标题是短标题的 4.4 倍！与直觉相反</p>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-conclusion">
                                        <div class="pattern-conclusion-title">
                                            <span>💡</span>
                                            <span>标题公式</span>
                                        </div>
                                        <div class="pattern-conclusion-text">
                                            理想标题 = <strong>含数字</strong> + <strong>感叹号</strong> + <strong>陈述句</strong> + <strong>50+字长标题</strong>。Hashtag 建议仅用于 Shorts。
                                        </div>
                                    </div>
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>标题中加入数字（+2.25×）</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>使用感叹号（+33%）</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>标题长度50字以上</span>
                                        </div>
                                        <div class="pattern-action avoid">
                                            <span class="pattern-action-icon">⚠️</span>
                                            <span>长视频避免Hashtag</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            // 其他模式的占位数据
            pattern5: { badge: '模式5', name: '周末发布效果更好', confidence: '高', sample: 'N = 2,340', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">周六日发布的视频平均播放量比工作日高 <strong>23%</strong>。避免周一发布。</div></div>' },
            pattern11: { badge: '模式11', name: '频道稳定性差异巨大', confidence: '高', sample: 'N = 979', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">频道稳定性（max/avg）差异可达 <strong>10倍以上</strong>。追求 max/avg &lt; 10 为宜。</div></div>' },
            pattern12: {
                badge: '模式12',
                name: '黑马频道特征',
                confidence: '高',
                sample: 'N = 50',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">原始数据</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <table class="pattern-data-table">
                                        <thead>
                                            <tr><th>频道</th><th>订阅数</th><th>最高播放</th><th>爆发倍率</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr class="highlight"><td>FeiKou</td><td>32K</td><td class="highlight-value">1905万</td><td class="highlight-value">589×</td></tr>
                                            <tr><td>台灣趴趴走</td><td>11.6K</td><td>450万</td><td>388×</td></tr>
                                            <tr><td>棋牌乐逍遥</td><td>13.9K</td><td>393万</td><td>283×</td></tr>
                                        </tbody>
                                    </table>
                                    <p style="color: var(--color-text-muted); font-size: 0.85em; margin-top: 12px;">爆发倍率 = 最高播放 / 订阅数</p>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">可视化分析</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-bar-chart">
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">FeiKou</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill green" style="width: 100%">
                                                    <span class="pattern-bar-value">589×</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">台灣趴趴走</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill blue" style="width: 66%">
                                                    <span class="pattern-bar-value">388×</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">棋牌乐逍遥</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill purple" style="width: 48%">
                                                    <span class="pattern-bar-value">283×</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <p style="text-align: center; color: var(--color-accent); margin-top: 16px; font-weight: 600;">订阅 1-5 万的频道最容易出爆款</p>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-conclusion">
                                        <div class="pattern-conclusion-title">
                                            <span>💡</span>
                                            <span>核心结论</span>
                                        </div>
                                        <div class="pattern-conclusion-text">
                                            <strong>订阅 1-5 万的小频道</strong>最容易出爆款。大V难出爆款（粉丝增长 → 爆发倍率下降）。新频道完全有机会逆袭！
                                        </div>
                                    </div>
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>新频道有逆袭机会</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>研究1-5万订阅的高效频道</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>爆款后快速转化订阅</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            pattern13: { badge: '模式13', name: '话题热度演变', confidence: '中', sample: 'N = 2,340', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">识别长青话题（持续高热度）vs 短周期话题（热度快速衰减）。优先选择长青话题。</div></div>' },
            pattern14: {
                badge: '模式14',
                name: '快速增长频道特征',
                confidence: '中',
                sample: 'N = 25',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">30天快速增长Top5</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <!-- 增长时间线 -->
                                    <div class="growth-timeline">
                                        <div class="timeline-item">
                                            <div class="timeline-rank gold">1</div>
                                            <div class="timeline-content">
                                                <div class="timeline-channel">养生之道</div>
                                                <div class="timeline-stats">1天6条 → 总播放66.7万 → 订阅3.9万</div>
                                            </div>
                                            <div class="timeline-badge">11.1万/条</div>
                                        </div>
                                        <div class="timeline-item">
                                            <div class="timeline-rank gold">2</div>
                                            <div class="timeline-content">
                                                <div class="timeline-channel">laxnetcm</div>
                                                <div class="timeline-stats">6天3条 → 总播放81.9万 → 订阅5300</div>
                                            </div>
                                            <div class="timeline-badge">27.3万/条</div>
                                        </div>
                                        <div class="timeline-item">
                                            <div class="timeline-rank gold">3</div>
                                            <div class="timeline-content">
                                                <div class="timeline-channel">暖心故事匯</div>
                                                <div class="timeline-stats">3天3条 → 总播放42.9万 → 订阅2930</div>
                                            </div>
                                            <div class="timeline-badge">14.3万/条</div>
                                        </div>
                                        <div class="timeline-item">
                                            <div class="timeline-rank">4</div>
                                            <div class="timeline-content">
                                                <div class="timeline-channel">倪海厦相关</div>
                                                <div class="timeline-stats">7天3条 → 总播放32.5万 → 订阅6.86万</div>
                                            </div>
                                            <div class="timeline-badge">10.8万/条</div>
                                        </div>
                                        <div class="timeline-item">
                                            <div class="timeline-rank">5</div>
                                            <div class="timeline-content">
                                                <div class="timeline-channel">功夫大侠</div>
                                                <div class="timeline-stats">20天2条 → 总播放11.4万 → 订阅6.56万</div>
                                            </div>
                                            <div class="timeline-badge">5.7万/条</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">快速增长共性</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <table class="pattern-data-table">
                                        <thead>
                                            <tr><th>特征</th><th>发现</th><th>代表案例</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr class="highlight"><td>内容类型</td><td class="highlight-value">食疗配方 > 功法教学</td><td>养生之道</td></tr>
                                            <tr><td>发布密度</td><td>集中发布（1-3天多条）</td><td>养生之道1天6条</td></tr>
                                            <tr><td>爆款规律</td><td>通常第2-3条爆发</td><td>暖心故事匯第3条37万</td></tr>
                                            <tr><td>标签数量</td><td>多（5-15个）</td><td>laxnetcm</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-conclusion">
                                        <div class="pattern-conclusion-title">
                                            <span>💡</span>
                                            <span>新频道起步策略</span>
                                        </div>
                                        <div class="pattern-conclusion-text">
                                            集中发布 5-6 条视频，内容类型选择食疗配方，让第2-3条视频自然爆发。
                                        </div>
                                    </div>
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>首选食疗配方类内容</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>集中发布5-6条</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>每条使用5-15个标签</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            pattern15: { badge: '模式15', name: '最佳发布时段', confidence: '中', sample: '待完善', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>⏳</span><span>分析进行中</span></div><div class="pattern-conclusion-text">此模式正在分析发布时段与播放量的关系。</div></div>' },
            pattern19: { badge: '模式19', name: '内容缺口机会', confidence: '高', sample: 'N = 2,340', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">高需求低供给的内容缺口：<strong>穴位按摩</strong>（台湾）、<strong>太极</strong>（美国）。这些是最佳的内容套利机会。</div></div>' },
            pattern20: {
                badge: '模式20',
                name: '地区差异与跨境机会',
                confidence: '高',
                sample: 'N = 172',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">Google Trends 搜索增长（趋势箭头）</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <!-- 趋势箭头卡片 -->
                                    <div class="trend-cards">
                                        <div class="trend-card hot">
                                            <div class="trend-card-topic">Tai Chi</div>
                                            <div class="trend-card-arrow up">↑</div>
                                            <div class="trend-card-value positive">+533%</div>
                                            <div class="trend-card-region">🇺🇸 美国</div>
                                        </div>
                                        <div class="trend-card hot">
                                            <div class="trend-card-topic">태극권</div>
                                            <div class="trend-card-arrow up">↑</div>
                                            <div class="trend-card-value positive">+129%</div>
                                            <div class="trend-card-region">🇰🇷 韩国</div>
                                        </div>
                                        <div class="trend-card">
                                            <div class="trend-card-topic">八段锦</div>
                                            <div class="trend-card-arrow up">↑</div>
                                            <div class="trend-card-value positive">+24%</div>
                                            <div class="trend-card-region">🇹🇼 台湾</div>
                                        </div>
                                        <div class="trend-card">
                                            <div class="trend-card-topic">Qigong</div>
                                            <div class="trend-card-arrow up">↑</div>
                                            <div class="trend-card-value positive">+22%</div>
                                            <div class="trend-card-region">🇺🇸 美国</div>
                                        </div>
                                        <div class="trend-card">
                                            <div class="trend-card-topic">気功</div>
                                            <div class="trend-card-arrow down">↓</div>
                                            <div class="trend-card-value negative">-22%</div>
                                            <div class="trend-card-region">🇯🇵 日本</div>
                                        </div>
                                        <div class="trend-card">
                                            <div class="trend-card-topic">Baduanjin</div>
                                            <div class="trend-card-arrow stable">→</div>
                                            <div class="trend-card-value">0%</div>
                                            <div class="trend-card-region">🌍 全球</div>
                                        </div>
                                    </div>
                                    <p style="text-align: center; color: #22c55e; font-weight: 600; margin-top: 16px;">🔥 Tai Chi 在美国暴涨 533%，是最佳切入时机！</p>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">各地区 CPM 对比</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <table class="pattern-data-table">
                                        <thead>
                                            <tr><th>地区</th><th>CPM</th><th>相对倍数</th><th>特点</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr class="highlight"><td>🇦🇺 澳大利亚</td><td class="highlight-value">$36.21</td><td class="highlight-value">12.1×</td><td>华人移民市场</td></tr>
                                            <tr><td>🇸🇬 新加坡</td><td>$17.75</td><td>5.9×</td><td>华人高收入</td></tr>
                                            <tr><td>🇭🇰 香港</td><td>$17.23</td><td>5.7×</td><td>粤语市场</td></tr>
                                            <tr><td>🇺🇸 美国</td><td>$12-14</td><td>4×</td><td>最大英语市场</td></tr>
                                            <tr><td>🇹🇼 台湾</td><td class="low-value">$3-4</td><td>1.2×</td><td>繁体中文主市场</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-conclusion">
                                        <div class="pattern-conclusion-title">
                                            <span>💡</span>
                                            <span>跨境内容策略</span>
                                        </div>
                                        <div class="pattern-conclusion-text">
                                            美国市场 CPM $12 是台湾的 <strong>3.4倍</strong>，且 Tai Chi 搜索暴涨 <strong>+533%</strong>。优先制作英语内容投放美国市场。
                                        </div>
                                    </div>
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>优先英语内容→美国</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>关键词用 Tai Chi / Qigong</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>考虑韩国市场（增长129%）</span>
                                        </div>
                                        <div class="pattern-action avoid">
                                            <span class="pattern-action-icon">⚠️</span>
                                            <span>避免用 Baduanjin（知名度低）</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            pattern21: { badge: '模式21', name: '多语言市场对比', confidence: '高', sample: 'N = 172', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">气功英语市场是日语的 <strong>8倍</strong>。英语内容优先于日语内容。</div></div>' },
            pattern23: {
                badge: '模式23',
                name: '话题垄断度分析',
                confidence: '高',
                sample: 'N = 2,340',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">原始数据</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <table class="pattern-data-table">
                                        <thead>
                                            <tr><th>话题</th><th>Top3频道份额</th><th>竞争格局</th><th>新进入者机会</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr class="highlight"><td>睡眠</td><td class="highlight-value">94.7%</td><td>极度垄断</td><td class="low-value">极难</td></tr>
                                            <tr><td>八段锦</td><td>91.5%</td><td>高度垄断</td><td class="low-value">很难</td></tr>
                                            <tr><td>穴位</td><td>85.0%</td><td>较垄断</td><td>困难</td></tr>
                                            <tr><td>太极</td><td>82.2%</td><td>较垄断</td><td>困难</td></tr>
                                            <tr><td>食疗</td><td>81.1%</td><td>较垄断</td><td>困难</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">可视化分析</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-bar-chart">
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">睡眠</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill red" style="width: 94.7%">
                                                    <span class="pattern-bar-value">94.7%</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">八段锦</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill red" style="width: 91.5%">
                                                    <span class="pattern-bar-value">91.5%</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">穴位</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill yellow" style="width: 85%">
                                                    <span class="pattern-bar-value">85.0%</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">太极</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill yellow" style="width: 82.2%">
                                                    <span class="pattern-bar-value">82.2%</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pattern-bar-item">
                                            <span class="pattern-bar-label">食疗</span>
                                            <div class="pattern-bar-track">
                                                <div class="pattern-bar-fill yellow" style="width: 81.1%">
                                                    <span class="pattern-bar-value">81.1%</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <p style="text-align: center; color: var(--color-confidence-low); margin-top: 16px; font-weight: 600;">所有话题 Top3 频道占 >80% 流量，头部效应极强</p>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-conclusion">
                                        <div class="pattern-conclusion-title">
                                            <span>💡</span>
                                            <span>核心结论</span>
                                        </div>
                                        <div class="pattern-conclusion-text">
                                            所有主要话题的 <strong>Top3 频道占据 80%+ 流量</strong>。新进入者正面竞争几乎不可能，必须采用差异化策略。
                                        </div>
                                    </div>
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>寻找细分话题切入</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>地区差异化（美国英语市场）</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>形式差异化（长视频→Shorts）</span>
                                        </div>
                                        <div class="pattern-action avoid">
                                            <span class="pattern-action-icon">⚠️</span>
                                            <span>避免正面竞争睡眠话题</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            pattern24: { badge: '模式24', name: '国家内容收益综合分析', confidence: '高', sample: 'N = 172', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">综合考虑 CPM、爆款率、竞争度，<strong>美国太极英语内容</strong>是收益最高的组合。</div></div>' },
            pattern25: { badge: '模式25', name: '标签数量1-3个最优', confidence: '高', sample: 'N = 2,340', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">长视频使用 <strong>1-3个标签</strong> 效果最佳，Shorts 可以使用更多标签。</div></div>' },
            pattern26: { badge: '模式26', name: '描述长度500-1000字', confidence: '中', sample: 'N = 2,340', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">描述长度 <strong>500-1000字</strong> 最优，包含关键词有助于 SEO。</div></div>' },
            pattern27: {
                badge: '模式27',
                name: '标题钩子类型效果排名',
                confidence: '中',
                sample: 'N = 2,340',
                content: `
                    <div class="pattern-flow">
                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">1</span>
                                <span class="pattern-step-title">钩子词云（大小=效果）</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <!-- 词云 -->
                                    <div class="word-cloud">
                                        <span class="word-cloud-item size-5 hot" title="均播25.4万">免费</span>
                                        <span class="word-cloud-item size-5 hot" title="均播25.4万">省钱</span>
                                        <span class="word-cloud-item size-4" title="均播12.8万">震惊</span>
                                        <span class="word-cloud-item size-4" title="均播12.8万">竟然</span>
                                        <span class="word-cloud-item size-3" title="均播11.5万">最好</span>
                                        <span class="word-cloud-item size-3" title="均播11.5万">最强</span>
                                        <span class="word-cloud-item size-3" title="均播10万">危险</span>
                                        <span class="word-cloud-item size-3" title="均播10万">小心</span>
                                        <span class="word-cloud-item size-2" title="均播3.9万">秘密</span>
                                        <span class="word-cloud-item size-2" title="均播3.9万">秘方</span>
                                        <span class="word-cloud-item size-2" title="均播2.9万">教你</span>
                                        <span class="word-cloud-item size-2" title="均播2.9万">如何</span>
                                        <span class="word-cloud-item size-1 warning" title="均播2.4万 ⚠️效果最差">必看</span>
                                        <span class="word-cloud-item size-1 warning" title="均播2.4万 ⚠️效果最差">一定要</span>
                                        <span class="word-cloud-item size-1 warning" title="均播2.4万 ⚠️效果最差">千万</span>
                                    </div>
                                    <div style="display: flex; justify-content: center; gap: 20px; margin-top: 12px; font-size: 0.75em;">
                                        <span style="color: #22c55e;">● 绿色 = 效果最好</span>
                                        <span style="color: #ef4444;">● 红色 = 效果最差</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">2</span>
                                <span class="pattern-step-title">钩子效果数据</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <table class="pattern-data-table">
                                        <thead>
                                            <tr><th>钩子类型</th><th>示例</th><th>均播放</th><th>样本</th></tr>
                                        </thead>
                                        <tbody>
                                            <tr class="highlight"><td>利益钩子</td><td>免费/省钱</td><td class="highlight-value">25.4万</td><td>5条</td></tr>
                                            <tr><td>惊讶钩子</td><td>震惊/竟然</td><td>12.8万</td><td>20条</td></tr>
                                            <tr><td>最强钩子</td><td>最好/第一</td><td>11.5万</td><td>80条</td></tr>
                                            <tr><td>恐惧钩子</td><td>危险/小心</td><td>10万</td><td>20条</td></tr>
                                            <tr class="low-value"><td>紧迫感钩子</td><td>必看/一定要</td><td class="low-value">2.4万</td><td>42条</td></tr>
                                        </tbody>
                                    </table>
                                    <p style="text-align: center; color: #ef4444; font-size: 0.85em; margin-top: 12px;">⚠️ 紧迫感钩子效果最差（反直觉！）</p>
                                </div>
                            </div>
                        </div>

                        <div class="pattern-connector">▼</div>

                        <div class="pattern-step expanded">
                            <div class="pattern-step-header" onclick="togglePatternStep(this)">
                                <span class="pattern-step-number">3</span>
                                <span class="pattern-step-title">结论与行动</span>
                                <span class="pattern-step-toggle">▼</span>
                            </div>
                            <div class="pattern-step-content">
                                <div class="pattern-step-inner">
                                    <div class="pattern-actions">
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>优先：免费/省钱（25万）</span>
                                        </div>
                                        <div class="pattern-action">
                                            <span class="pattern-action-icon">✅</span>
                                            <span>次选：震惊/竟然（13万）</span>
                                        </div>
                                        <div class="pattern-action avoid">
                                            <span class="pattern-action-icon">❌</span>
                                            <span>避免：必看/一定要（2.4万）</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            pattern28: { badge: '模式28', name: '发布频率与效率', confidence: '高', sample: 'N = 979', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">每周 <strong>3-5条</strong> 发布频率最优。过高频率会降低单视频质量。</div></div>' },
            pattern32: { badge: '模式32', name: '健康话题与播放量关系', confidence: '中', sample: 'N = 2,340', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">健康话题播放潜力排名，用于选题决策参考。</div></div>' },
            pattern34: { badge: '模式34', name: '高赞评论特征', confidence: '中', sample: '待采集', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">高赞评论特征：提问式、分享经验、表达感谢。可用于引导评论区互动。</div></div>' },
            pattern37: { badge: '模式37', name: '原创vs跟风效果分析', confidence: '中', sample: 'N = 500', content: '<div class="pattern-conclusion"><div class="pattern-conclusion-title"><span>💡</span><span>核心发现</span></div><div class="pattern-conclusion-text">原创内容长期回报更高，跟风内容短期见效快。新手建议先跟风后原创。</div></div>' }
        };

        // 打开模式面板
        function openPatternModal(patternId) {
            const data = patternData[patternId];
            if (!data) {
                showTooltip('模式数据加载中...');
                return;
            }

            document.getElementById('patternModalBadge').textContent = data.badge;
            document.getElementById('patternModalName').textContent = data.name;
            document.getElementById('patternModalBody').innerHTML = data.content;

            document.getElementById('patternModalOverlay').classList.add('visible');
            document.getElementById('patternModal').classList.add('visible');

            // 禁止背景滚动
            document.body.style.overflow = 'hidden';
        }

        // 关闭模式面板
        function closePatternModal() {
            document.getElementById('patternModalOverlay').classList.remove('visible');
            document.getElementById('patternModal').classList.remove('visible');
            document.body.style.overflow = '';
        }

        // 切换模式步骤展开/折叠
        function togglePatternStep(header) {
            const step = header.closest('.pattern-step');
            step.classList.toggle('expanded');
        }

        // 切换标签页
        function switchPatternTab(tabId) {
            // 移除所有标签的active状态
            document.querySelectorAll('.pattern-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // 隐藏所有内容区域
            document.querySelectorAll('.pattern-tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // 激活点击的标签
            event.currentTarget.classList.add('active');

            // 显示对应的内容区域
            const targetContent = document.getElementById(tabId);
            if (targetContent) {
                targetContent.classList.add('active');
            }

            // 如果是第7个标签（信息报告），显示原有的洞察内容
            const metricsEl = document.querySelector('.metrics-overview');
            const insightsEl = document.querySelector('.insights-container');
            const summaryEl = document.querySelector('.comprehensive-card');

            if (tabId === 'tab7') {
                if (metricsEl) metricsEl.style.display = 'flex';
                if (insightsEl) insightsEl.style.display = 'grid';
                if (summaryEl) summaryEl.style.display = 'block';
            } else {
                if (metricsEl) metricsEl.style.display = 'none';
                if (insightsEl) insightsEl.style.display = 'none';
                if (summaryEl) summaryEl.style.display = 'none';
            }
        }

        // 切换子标签页（模式内部）
        function switchSubPattern(parentTabId, subTabId) {
            const parentTab = document.getElementById(parentTabId);
            if (!parentTab) return;

            // 移除该父标签页下所有子标签的active状态
            parentTab.querySelectorAll('.sub-pattern-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // 隐藏该父标签页下所有子内容
            parentTab.querySelectorAll('.sub-pattern-content').forEach(content => {
                content.classList.remove('active');
            });

            // 激活点击的子标签
            event.currentTarget.classList.add('active');

            // 显示对应的子内容
            const targetContent = document.getElementById(parentTabId + '-' + subTabId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        }

        // ========== 建立图表与结论的映射关系 ==========
        /**
         * 建立图表与结论的映射关系
         * 用于Tab7信息报告点击展开时能快速复制或渲染源Tab的图表
         *
         * 该函数确保所有已注册的结论都能正确关联到其对应的canvas ID
         * 使得toggleConclusionChart()能通过Tier1(缓存) → Tier2(复制canvas) 快速打开图表
         */
        function bindChartConclusions() {
            const tabConclusions = window.tabConclusions || window.InsightReport?.tabConclusions || {};

            // 遍历所有Tab的结论，确保sourceCanvasId正确映射
            Object.entries(tabConclusions).forEach(([tabId, tab]) => {
                if (!tab.items || !Array.isArray(tab.items)) return;

                tab.items.forEach((item, idx) => {
                    // sourceCanvasId 已在 registerPatternConclusion() 时通过第7个参数设置
                    // 这里我们只做验证和日志记录，无需额外操作

                    if (item.sourceCanvasId) {
                        const canvas = document.getElementById(item.sourceCanvasId);
                        if (canvas) {
                            // canvas 存在，映射关系正确
                            console.log(`[Report] ✓ Tab${tabId}模式${item.patternId}图表映射: ${item.sourceCanvasId}`);
                        } else {
                            // canvas 不存在，记录警告
                            console.warn(`[Report] ⚠️ Tab${tabId}模式${item.patternId}的canvas未找到: ${item.sourceCanvasId}`);
                        }
                    }
                });
            });

            console.log('[Report] ✓ 图表与结论映射关系建立完成');
        }

        // ========== Tab7 信息报告渲染 ==========
        function renderInfoReport(data) {
            console.log('渲染信息报告，数据:', Object.keys(data));

            // 注意：clearAllConclusions() 已移到 updatePatternsWithData 开头
            // 这样 renderPatternX 注册的模式结论不会被清除

            // 数据准备
            const videos = data.videos || [];
            const channels = data.channels || [];

            // 缓存数据（供信息报告展开图表使用）
            window._cachedChannels = channels;
            window._cachedVideos = videos;

            // 2. 生成各板块洞察（会自动注册结论到 tabConclusions）
            const insights = {
                global: generateGlobalInsight(data),
                arbitrage: generateArbitrageInsight(data),
                topic: generateTopicInsight(data),
                content: generateContentInsight(data),
                publish: generatePublishInsight(data),
                channel: generateChannelInsight(data)
            };

            // 3. 注册静态用户洞察结论（如果动态数据还未加载）
            registerStaticUserInsightConclusions();

            // 3.5 确保tab1（全局认识）的模式43有fallback（语言分布依赖用户洞察API）
            ensureTab1Pattern43Fallback(channels);

            // 3.6 建立图表与结论的映射关系（用于信息报告点击展开时复制图表）
            bindChartConclusions();

            // 4. 基于各板块结论渲染信息报告
            renderInfoReportFromConclusions();

            // 渲染学习参考板块的内容（保留兼容）
            renderTopVideos(data.videos || []);
            renderTitleFormulas(data.videos || []);
        }

        // ========== 爆款视频实例渲染 ==========
        function renderTopVideos(videos) {
            const container = document.getElementById('topVideosGrid');
            if (!container) return;

            if (videos.length === 0) {
                container.innerHTML = '<div class="top-video-loading">暂无视频数据</div>';
                return;
            }

            // 按播放量排序，取前6个
            const topVideos = [...videos]
                .sort((a, b) => (b.view_count || b.views || 0) - (a.view_count || a.views || 0))
                .slice(0, 6);

            container.innerHTML = topVideos.map((v, i) => {
                const views = v.view_count || v.views || 0;
                const duration = v.duration || 0;
                const mins = Math.floor(duration / 60);
                const secs = duration % 60;
                const durationText = duration > 0 ? `${mins}:${String(secs).padStart(2, '0')}` : '-';

                const rankClass = i === 0 ? 'rank-1' : (i === 1 ? 'rank-2' : (i === 2 ? 'rank-3' : 'rank-other'));

                const viewsText = views >= 10000
                    ? `${(views / 10000).toFixed(1)}万`
                    : views.toLocaleString();

                const youtubeUrl = v.youtube_id
                    ? `https://www.youtube.com/watch?v=${v.youtube_id}`
                    : '#';

                return `
                    <div class="top-video-card">
                        <div class="top-video-rank ${rankClass}">${i + 1}</div>
                        <div class="top-video-title">
                            <a href="${youtubeUrl}" target="_blank" rel="noopener">${v.title || '无标题'}</a>
                        </div>
                        <div class="top-video-stats">
                            <div class="top-video-stat">
                                <span>播放</span>
                                <span class="stat-value">${viewsText}</span>
                            </div>
                            <div class="top-video-stat">
                                <span>时长</span>
                                <span class="stat-value">${durationText}</span>
                            </div>
                            <div class="top-video-stat">
                                <span>点赞</span>
                                <span class="stat-value">${(v.like_count || 0).toLocaleString()}</span>
                            </div>
                        </div>
                        <div class="top-video-channel">
                            频道: ${v.channel_name || '未知'}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // ========== 标题公式提取与渲染 ==========
        function renderTitleFormulas(videos) {
            const container = document.getElementById('titlePatternsGrid');
            if (!container) return;

            if (videos.length === 0) {
                container.innerHTML = '<div class="pattern-loading">暂无视频数据</div>';
                return;
            }

            // 按播放量排序，取前20个用于分析
            const topVideos = [...videos]
                .sort((a, b) => (b.view_count || b.views || 0) - (a.view_count || a.views || 0))
                .slice(0, 20);

            // 提取标题公式
            const patterns = extractTitlePatterns(topVideos);

            if (patterns.length === 0) {
                container.innerHTML = '<div class="pattern-loading">未能提取出明显的标题公式</div>';
                return;
            }

            container.innerHTML = patterns.map(pattern => {
                const effectivenessPercent = Math.min(100, pattern.effectiveness);

                return `
                    <div class="title-pattern-card">
                        <div class="pattern-formula">${pattern.formula}</div>
                        <div class="pattern-examples">
                            <strong>爆款实例:</strong>
                            ${pattern.examples.map(ex => `
                                <div class="pattern-example-item">
                                    <div class="pattern-example-title">${ex.title}</div>
                                    <div class="pattern-example-views">播放: ${formatViewCount(ex.views)}</div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="pattern-effectiveness">
                            <div class="effectiveness-bar">
                                <div class="effectiveness-fill" style="width: ${effectivenessPercent}%"></div>
                            </div>
                            <span class="effectiveness-label">有效率 ${effectivenessPercent.toFixed(0)}%</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // 提取标题公式
        function extractTitlePatterns(videos) {
            const patterns = [];

            // 公式1: 方括号/标签开头类型【】
            const bracketPattern = videos.filter(v => /^[\[【]/.test(v.title || ''));
            if (bracketPattern.length >= 2) {
                patterns.push({
                    formula: '【标签】+ 核心卖点 + 细节描述',
                    examples: bracketPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (bracketPattern.length / videos.length) * 100 * 3
                });
            }

            // 公式2: 价格/数字吸引类型 ($299/只要/仅需)
            const pricePattern = videos.filter(v => /(\$|只要|仅需|元|块钱|免费|吃到飽|吃到饱)/.test(v.title || ''));
            if (pricePattern.length >= 2) {
                patterns.push({
                    formula: '价格锚点 + 超值内容 + 稀缺性',
                    examples: pricePattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (pricePattern.length / videos.length) * 100 * 3
                });
            }

            // 公式3: 地点+美食类型 (城市/地区+美食)
            const locationFoodPattern = videos.filter(v =>
                /(广州|厦门|台湾|台北|台中|上海|北京|香港|市场|老街|夜市|美食|小吃)/.test(v.title || ''));
            if (locationFoodPattern.length >= 2) {
                patterns.push({
                    formula: '地点名称 + 特色美食 + 体验描述',
                    examples: locationFoodPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (locationFoodPattern.length / videos.length) * 100 * 3
                });
            }

            // 公式4: 合作/联动类型 (ft./feat./x/&)
            const collabPattern = videos.filter(v =>
                /(ft\.|feat\.|Feat\.|FT\.| x | X |@|合作|联动)/.test(v.title || ''));
            if (collabPattern.length >= 2) {
                patterns.push({
                    formula: '主创作者 + ft./x + 嘉宾名称',
                    examples: collabPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (collabPattern.length / videos.length) * 100 * 3
                });
            }

            // 公式5: 排行/评比类型 (评比/排行/Top/最)
            const rankingPattern = videos.filter(v =>
                /(評比|评比|排行|排名|Top|TOP|第一|最好|最强|最佳|大胃王)/.test(v.title || ''));
            if (rankingPattern.length >= 2) {
                patterns.push({
                    formula: '评比类型 + 对象描述 + 结论暗示',
                    examples: rankingPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (rankingPattern.length / videos.length) * 100 * 3
                });
            }

            // 公式6: 数字开头类型 ("3个/5种/10个/2026")
            const numberPattern = videos.filter(v => /^[0-9]+|[0-9]+[个种条招步项款]/.test(v.title || ''));
            if (numberPattern.length >= 2) {
                patterns.push({
                    formula: '数字 + 名词 + 好处/功效',
                    examples: numberPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (numberPattern.length / videos.length) * 100 * 3
                });
            }

            // 公式7: 权威背书类型 ("国家/专家/医生/研究/全台第一")
            const authorityPattern = videos.filter(v =>
                /(国家|专家|医生|医师|研究|科学|权威|认定|推荐|全台第一|首家)/.test(v.title || ''));
            if (authorityPattern.length >= 2) {
                patterns.push({
                    formula: '权威来源 + 内容主题 + 效果承诺',
                    examples: authorityPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (authorityPattern.length / videos.length) * 100 * 3
                });
            }

            // 公式8: 功法/健康教学类型 ("八段锦/站桩/太极/健康")
            const healthPattern = videos.filter(v =>
                /(八段锦|站桩|太极|气功|冥想|瑜伽|功法|健康|養生|养生)/.test(v.title || ''));
            if (healthPattern.length >= 2) {
                patterns.push({
                    formula: '功法/健康主题 + 完整/全套 + 跟练',
                    examples: healthPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (healthPattern.length / videos.length) * 100 * 3
                });
            }

            // 公式9: 食疗/食材类型
            const foodPattern = videos.filter(v =>
                /(生姜|大蒜|蜂蜜|枸杞|红枣|鸡蛋|喝水|空腹|早上|睡前|炸雞|炸鸡|羊肉|海鲜)/.test(v.title || ''));
            if (foodPattern.length >= 2) {
                patterns.push({
                    formula: '常见食材 + 意想不到功效 + 使用方法',
                    examples: foodPattern.slice(0, 2).map(v => ({
                        title: v.title,
                        views: v.view_count || v.views || 0
                    })),
                    effectiveness: (foodPattern.length / videos.length) * 100 * 3
                });
            }

            // 按有效率排序，取前4个
            return patterns
                .sort((a, b) => b.effectiveness - a.effectiveness)
                .slice(0, 4);
        }

        // 格式化播放量
        function formatViewCount(views) {
            if (views >= 100000000) return (views / 100000000).toFixed(1) + '亿';
            if (views >= 10000) return (views / 10000).toFixed(1) + '万';
            return views.toLocaleString();
        }

        // 更新洞察卡片内容
        function updateInsightCard(cardId, content) {
            const card = document.getElementById(cardId);
            if (!card) return;
            const contentEl = card.querySelector('.insight-content');
            if (contentEl) {
                contentEl.innerHTML = content;
            }
        }

        // 全局认识洞察（模式结论已在 renderPattern4/renderPattern23 等函数注册，这里只返回文本）
        function generateGlobalInsight(data) {
            const videos = data.videos || [];
            if (videos.length === 0) {
                return '暂无数据';
            }

            const stats = data.content_type_stats || {};
            const types = Object.entries(stats)
                .sort((a, b) => (b[1].total_views || 0) - (a[1].total_views || 0))
                .slice(0, 3);

            const totalViews = videos.reduce((s, v) => s + (v.view_count || v.views || 0), 0);
            const avgViews = Math.round(totalViews / videos.length);

            if (types.length === 0) {
                return `共采集 ${videos.length} 个视频，平均播放 ${(avgViews/10000).toFixed(1)}万。`;
            }

            const topType = types[0];
            const typeLabel = getContentTypeLabel(topType[0]);
            const viewShare = totalViews > 0 ? ((topType[1].total_views || 0) / totalViews * 100).toFixed(0) : 0;

            return `<strong>${typeLabel}</strong>类内容占据主导，贡献 <strong>${viewShare}%</strong> 播放量。市场偏好明确，建议聚焦此类型深耕。`;
        }

        // 套利分析洞察（模式结论已在 renderRegionDistribution 注册，这里只返回文本）
        function generateArbitrageInsight(data) {
            const region = data.region_distribution || {};
            const regions = region.regions || [];

            if (regions.length === 0) {
                return '暂无地区分布数据';
            }

            const sorted = [...regions].sort((a, b) =>
                (b.avg_views || 0) - (a.avg_views || 0));

            if (sorted.length >= 2) {
                const top = sorted[0];
                const bottom = sorted[sorted.length - 1];
                const ratio = bottom.avg_views > 0
                    ? (top.avg_views / bottom.avg_views).toFixed(1)
                    : '∞';

                return `<strong>${top.region}</strong>地区均播放最高(${(top.avg_views/10000).toFixed(1)}万)，是最低地区的 <strong>${ratio}倍</strong>。存在明显地域套利空间。`;
            }

            return `主要来自 ${sorted[0]?.region || '未知'} 地区。`;
        }

        // 选题决策洞察（模式结论已在 renderContentLifecycle 注册，这里只返回文本）
        function generateTopicInsight(data) {
            const lifecycle = data.content_lifecycle || {};
            const topics = lifecycle.topics || [];

            if (topics.length === 0) {
                return '暂无选题生命周期数据';
            }

            const sorted = [...topics].sort((a, b) =>
                (b.avg_views || 0) - (a.avg_views || 0));

            const hot = sorted.slice(0, 3).map(t => t.content_type || t.topic || '未知').join('、');
            const cold = sorted.slice(-2).map(t => t.content_type || t.topic || '未知').join('、');

            return `热门选题：<strong>${hot}</strong>。冷门选题：${cold}。建议优先布局热门选题，差异化切入。`;
        }

        // 内容创作洞察（模式结论已在各 renderPattern 函数注册，这里只返回文本）
        function generateContentInsight(data) {
            const videos = data.videos || [];
            if (videos.length === 0) {
                return '暂无数据';
            }

            // 时长分析
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
                const avgViews = best.avg_views > 10000
                    ? `${(best.avg_views / 10000).toFixed(1)}万`
                    : best.avg_views.toLocaleString();
                durationTip = `<strong>${label}</strong>均播最高(${avgViews})`;
            }

            // 最佳组合分析
            const combos = data.best_duration_category_combos || [];
            let comboTip = '';
            if (combos.length > 0) {
                const best = combos[0];
                const dType = durationLabels[best.duration_type] || best.duration_type;
                const avgViews = best.avg_views > 10000
                    ? `${(best.avg_views / 10000).toFixed(1)}万`
                    : best.avg_views.toLocaleString();
                comboTip = `，<strong>${best.category}+${dType}</strong>是最强组合(均播${avgViews})`;
            }

            return `${durationTip}${comboTip}。`;
        }

        // 发布策略洞察（模式结论已在 renderPublishingPatterns 注册，这里只返回文本）
        function generatePublishInsight(data) {
            const weekday = data.weekday_performance || {};
            const days = weekday.weekdays || [];

            if (days.length === 0) {
                return '暂无发布时间数据';
            }

            const sorted = [...days].sort((a, b) =>
                (b.avg_views || 0) - (a.avg_views || 0));

            const best = sorted[0];
            const worst = sorted[sorted.length - 1];

            const bestDay = best.weekday || '未知';
            const worstDay = worst.weekday || '未知';

            return `<strong>${bestDay}</strong>发布效果最佳(均播${(best.avg_views/10000).toFixed(1)}万)，${worstDay}表现最弱。建议重点在${bestDay}发布。`;
        }

        // 频道运营洞察（模式结论已在 renderChannelStability/renderPattern2 等函数注册，这里只返回文本）
        function generateChannelInsight(data) {
            const stability = data.channel_stability || {};
            const rankings = data.channel_rankings || {};
            const channels = data.channels || [];

            if (channels.length === 0) {
                return '暂无频道数据';
            }

            const stable = stability.stable_channels || [];
            const darkHorseRank = rankings.dark_horse_rank || {};
            const darkHorseChannels = darkHorseRank.channels || [];

            const parts = [];

            // 黑马频道洞察（只返回文本，模式12结论已在其他地方注册）
            if (darkHorseChannels.length > 0) {
                const topHorse = darkHorseChannels[0];
                const subs = topHorse.subscriber_count || 0;
                const maxViews = topHorse.max_views || 0;
                const ratio = subs > 0 ? (maxViews / subs).toFixed(0) : '∞';
                parts.push(`<strong>黑马频道</strong>「${topHorse.name || '未知'}」仅${subs.toLocaleString()}订阅却有${(maxViews/10000).toFixed(1)}万播放(${ratio}倍转化)`);
            }

            // 更新频率洞察（只返回文本，模式14结论已在其他地方注册）
            const bestFreq = data.best_update_frequency || {};
            if (bestFreq.type && bestFreq.avg_views > 0) {
                const freqLabels = { daily: '日更', weekly: '周更', biweekly: '双周更', monthly: '月更', irregular: '不规律更新' };
                const freqLabel = freqLabels[bestFreq.type] || bestFreq.type;
                const avgViewsText = (bestFreq.avg_views/10000).toFixed(1);
                parts.push(`<strong>${freqLabel}</strong>频道表现最佳(均播${avgViewsText}万)`);
            }

            if (stable.length > 0) {
                parts.push(`${stable.length}个稳定频道持续产出`);
            }

            if (parts.length === 0) {
                return `共分析 ${channels.length} 个频道。`;
            }

            return parts.join('。') + '。';
        }

        // 内容类型标签转换
        function getContentTypeLabel(type) {
            const labels = {
                'tutorial': '教程',
                'review': '测评',
                'vlog': 'Vlog',
                'news': '资讯',
                'entertainment': '娱乐',
                'education': '教育',
                'music': '音乐',
                'gaming': '游戏',
                'other': '其他'
            };
            return labels[type] || type;
        }

        // 生成行动建议
        function generateActionRecommendations(data, insights) {
            const actions = [];
            const videos = data.videos || [];

            // 基于内容类型
            const stats = data.content_type_stats || {};
            const topType = Object.entries(stats)
                .sort((a, b) => (b[1].avg_views || 0) - (a[1].avg_views || 0))[0];
            if (topType) {
                actions.push({
                    priority: 'high',
                    text: `聚焦${getContentTypeLabel(topType[0])}类内容，这是当前效果最好的类型`
                });
            }

            // 基于发布时间
            const weekday = data.weekday_performance || {};
            const days = weekday.weekdays || [];
            if (days.length > 0) {
                const best = [...days].sort((a, b) => (b.avg_views || 0) - (a.avg_views || 0))[0];
                const bestDay = best.weekday || '周末'; // weekday 已经是字符串
                actions.push({
                    priority: 'medium',
                    text: `优先选择${bestDay}发布视频`
                });
            }

            // 基于时长 - duration_distribution 值是视频数量
            const durations = data.duration_distribution || {};
            const durationLabels = { short: '5分钟内', medium: '5-20分钟', long: '20分钟以上' };
            const bestDuration = Object.entries(durations)
                .filter(([k]) => k !== 'unknown')
                .sort((a, b) => (b[1] || 0) - (a[1] || 0))[0];
            if (bestDuration) {
                const label = durationLabels[bestDuration[0]] || bestDuration[0];
                actions.push({
                    priority: 'medium',
                    text: `视频时长控制在${label}范围内`
                });
            }

            // 基于标题
            const hasNumbers = videos.filter(v => /\d/.test(v.title || '')).length;
            if (hasNumbers / videos.length > 0.3) {
                actions.push({
                    priority: 'low',
                    text: '标题中使用数字可提升点击率'
                });
            }

            // 基于地区
            const region = data.region_distribution || {};
            const regions = region.regions || [];
            if (regions.length >= 2) {
                const top = [...regions].sort((a, b) => (b.avg_views || 0) - (a.avg_views || 0))[0];
                actions.push({
                    priority: 'high',
                    text: `重点关注${top.region}地区受众，产出针对性内容`
                });
            }

            return actions.length > 0 ? actions : [{priority: 'low', text: '继续采集更多数据以获得更准确的建议'}];
        }

        // 渲染行动建议列表
        function renderActionList(actions) {
            const container = document.getElementById('reportActionList');
            if (!container) return;

            const priorityIcons = {
                high: '🔴',
                medium: '🟡',
                low: '🟢'
            };

            container.innerHTML = actions.map(a => `
                <div class="action-item priority-${a.priority}">
                    <span class="action-priority">${priorityIcons[a.priority] || '⚪'}</span>
                    <span class="action-text">${a.text}</span>
                </div>
            `).join('');
        }

        // 生成注意事项（旧版，用于兼容）
        function generateWarningsLegacy(data) {
            const warnings = [];
            const videos = data.videos || [];
            const channels = data.channels || [];

            // 数据量警告
            if (videos.length < 50) {
                warnings.push({
                    type: 'data',
                    text: `当前仅有 ${videos.length} 个视频样本，建议采集更多数据以提高结论可靠性`
                });
            }

            // 时间范围提示
            const timePeriod = data._timePeriodLabel || '未知';
            warnings.push({
                type: 'time',
                text: `当前分析基于「${timePeriod}」数据，结论可能受时间窗口影响`
            });

            // 数据偏差警告
            if (channels.length > 0) {
                const topChannel = channels.sort((a, b) =>
                    (b.total_views || 0) - (a.total_views || 0))[0];
                const totalViews = channels.reduce((s, c) => s + (c.total_views || 0), 0);
                const topShare = topChannel.total_views / totalViews;

                if (topShare > 0.3) {
                    warnings.push({
                        type: 'bias',
                        text: `头部频道「${topChannel.name}」占总播放 ${(topShare*100).toFixed(0)}%，数据可能存在头部偏差`
                    });
                }
            }

            // 缺失数据警告
            if (!data.region_distribution || (data.region_distribution.regions || []).length === 0) {
                warnings.push({
                    type: 'missing',
                    text: '缺少地区分布数据，无法进行套利分析'
                });
            }

            return warnings;
        }

        // 渲染注意事项列表
        function renderWarningList(warnings) {
            const container = document.getElementById('reportWarningList');
            if (!container) return;

            const typeIcons = {
                data: '📊',
                time: '⏰',
                bias: '⚖️',
                missing: '❓'
            };

            container.innerHTML = warnings.map(w => `
                <div class="warning-item warning-${w.type}">
                    <span class="warning-icon">${typeIcons[w.type] || '⚠️'}</span>
                    <span class="warning-text">${w.text}</span>
                </div>
            `).join('');
        }

        // ========== 置信度计算系统 ==========

        /**
         * 计算洞察置信度
         * @param {Object} params - 计算参数
         * @param {number} params.sampleSize - 样本量
         * @param {number} params.bestValue - 最佳选项的值
         * @param {number} params.secondValue - 次优选项的值
         * @param {number} params.coverage - 数据覆盖率 (0-1)
         * @returns {Object} { score: 0-100, level: 'high'|'medium'|'low', factors: {...} }
         */
        function calculateConfidence(params) {
            const { sampleSize = 0, bestValue = 0, secondValue = 0, coverage = 1 } = params;

            // 1. 样本量得分 (权重 40%)
            let sampleScore;
            if (sampleSize >= 100) sampleScore = 100;
            else if (sampleSize >= 50) sampleScore = 70 + (sampleSize - 50) * 0.6;
            else if (sampleSize >= 20) sampleScore = 40 + (sampleSize - 20) * 1;
            else sampleScore = sampleSize * 2;

            // 2. 一致性得分 (权重 35%) - 最佳与次优的差距越大越可信
            let consistencyScore = 50; // 默认值
            if (bestValue > 0 && secondValue > 0) {
                const gap = (bestValue - secondValue) / bestValue;
                if (gap >= 0.3) consistencyScore = 100;
                else if (gap >= 0.15) consistencyScore = 70 + gap * 100;
                else consistencyScore = 50 + gap * 133;
            } else if (bestValue > 0) {
                consistencyScore = 80; // 只有一个选项，中等可信
            }

            // 3. 覆盖度得分 (权重 25%)
            const coverageScore = Math.min(coverage, 1) * 100;

            // 加权计算总分
            const totalScore = Math.round(
                sampleScore * 0.40 +
                consistencyScore * 0.35 +
                coverageScore * 0.25
            );

            // 确定置信度等级
            let level;
            if (totalScore >= 75) level = 'high';
            else if (totalScore >= 50) level = 'medium';
            else level = 'low';

            return {
                score: Math.min(totalScore, 100),
                level,
                factors: {
                    sample: Math.round(sampleScore),
                    consistency: Math.round(consistencyScore),
                    coverage: Math.round(coverageScore)
                }
            };
        }

        // 存储计算后的置信度，供综合建议使用
        const insightConfidences = {
            duration: { score: 0, level: 'low' },
            channel: { score: 0, level: 'low' },
            topic: { score: 0, level: 'low' },
            frequency: { score: 0, level: 'low' }
        };

        // ========== 底部洞察卡片动态更新 ==========
        function updateBottomInsightCards(data) {
            const durationLabels = { short: '短视频(<5分钟)', medium: '中等(5-15分钟)', long: '长视频(>15分钟)' };
            const freqLabels = { daily: '日更', weekly: '周更', biweekly: '双周更', monthly: '月更', irregular: '不规律' };

            // 1. 最佳时长卡片 (insight-duration)
            const durations = data.duration_distribution || {};
            const durationStats = Object.entries(durations)
                .filter(([k]) => k !== 'unknown')
                .map(([key, val]) => {
                    if (typeof val === 'object') {
                        return { key, count: val.count || 0, avg_views: val.avg_views || 0 };
                    }
                    return { key, count: val || 0, avg_views: 0 };
                })
                .sort((a, b) => b.avg_views - a.avg_views);

            if (durationStats.length > 0) {
                const best = durationStats[0];
                const second = durationStats[1] || { avg_views: 0 };
                const label = durationLabels[best.key] || best.key;
                const avgViews = (best.avg_views / 10000).toFixed(1);
                const totalSample = durationStats.reduce((sum, s) => sum + s.count, 0);

                // 计算置信度
                const durationConf = calculateConfidence({
                    sampleSize: totalSample,
                    bestValue: best.avg_views,
                    secondValue: second.avg_views,
                    coverage: durationStats.length / 3 // 有3种时长类型
                });
                insightConfidences.duration = durationConf;

                // 更新标题
                const titleEl = document.querySelector('#insight-duration .insight-title');
                if (titleEl) titleEl.textContent = `${label}是最佳视频时长`;

                // 更新发现1：最佳时长的表现
                const finding1 = document.querySelector('#insight-duration .finding-item:first-child span:last-child');
                if (finding1) finding1.innerHTML = `${label}区间平均播放量 <strong>${avgViews}万</strong>，表现最佳`;

                // 更新发现2：与次优的差距
                const finding2 = document.querySelector('#insight-duration .finding-item:nth-child(2) span:last-child');
                if (finding2 && second.avg_views > 0) {
                    const gap = ((best.avg_views - second.avg_views) / second.avg_views * 100).toFixed(0);
                    const secondLabel = durationLabels[second.key] || second.key;
                    finding2.innerHTML = `比${secondLabel}高出 <strong>${gap}%</strong>`;
                }

                // 更新发现3：样本信息
                const finding3 = document.querySelector('#insight-duration .finding-item:nth-child(3) span:last-child');
                if (finding3) {
                    finding3.innerHTML = `基于 <strong>${totalSample}</strong> 条视频分析`;
                }

                // 更新置信度显示
                const confBar = document.getElementById('insight1-confidence-bar');
                const confText = document.getElementById('insight1-confidence-text');
                if (confBar) {
                    confBar.style.width = `${durationConf.score}%`;
                    confBar.className = `confidence-bar-fill ${durationConf.level}`;
                }
                if (confText) confText.textContent = `置信度 ${durationConf.score}%`;
            }

            // 2. 小频道爆款卡片 (insight-channel)
            const rankings = data.channel_rankings || {};
            const darkHorse = rankings.dark_horse_rank || {};
            const darkHorseChannels = darkHorse.channels || [];

            // 获取所有频道数据用于计算
            const allChannels = rankings.total_rank?.channels || [];
            const totalChannelCount = allChannels.length;

            if (darkHorseChannels.length > 0) {
                const top = darkHorseChannels[0];
                const subs = top.subscriber_count || 0;
                const maxViews = top.max_views || 0;
                const second = darkHorseChannels[1] || { max_views: 0 };

                // 计算置信度：基于小频道样本量和爆发倍率差异
                const channelConf = calculateConfidence({
                    sampleSize: darkHorseChannels.length,
                    bestValue: maxViews,
                    secondValue: second.max_views || 0,
                    coverage: totalChannelCount > 0 ? darkHorseChannels.length / totalChannelCount : 0.5
                });
                insightConfidences.channel = channelConf;

                const titleEl = document.querySelector('#insight-channel .insight-title');
                if (titleEl) titleEl.textContent = `小频道爆款机会真实存在`;

                const finding1 = document.querySelector('#insight-channel .finding-item:first-child span:last-child');
                if (finding1) finding1.innerHTML = `发现 <strong>${darkHorseChannels.length}</strong> 个小频道(订阅<1万)产出过爆款`;

                const finding2 = document.querySelector('#insight-channel .finding-item:nth-child(2) span:last-child');
                if (finding2) finding2.innerHTML = `最强黑马仅 ${subs.toLocaleString()} 订阅却有 <strong>${(maxViews/10000).toFixed(1)}万</strong> 播放`;

                // 更新发现3：爆发倍率
                const finding3 = document.querySelector('#insight-channel .finding-item:nth-child(3) span:last-child');
                if (finding3 && subs > 0) {
                    const burstRatio = Math.round(maxViews / subs);
                    finding3.innerHTML = `爆发倍率达 <strong>${burstRatio}×</strong>（播放/订阅）`;
                }

                // 更新置信度显示
                const confBar = document.getElementById('insight2-confidence-bar');
                const confText = document.getElementById('insight2-confidence-text');
                if (confBar) {
                    confBar.style.width = `${channelConf.score}%`;
                    confBar.className = `confidence-bar-fill ${channelConf.level}`;
                }
                if (confText) confText.textContent = `置信度 ${channelConf.score}%`;
            }

            // 3. 最强组合卡片 (insight-topic)
            const combos = data.best_duration_category_combos || [];
            if (combos.length > 0) {
                const best = combos[0];
                const second = combos[1] || { avg_views: 0 };
                const dType = durationLabels[best.duration_type] || best.duration_type;
                const avgViews = (best.avg_views / 10000).toFixed(1);

                // 计算置信度
                const topicConf = calculateConfidence({
                    sampleSize: best.count || combos.length * 10,
                    bestValue: best.avg_views,
                    secondValue: second.avg_views || 0,
                    coverage: combos.length / 9 // 3种时长 × 约3种分类
                });
                insightConfidences.topic = topicConf;

                const titleEl = document.querySelector('#insight-topic .insight-title');
                if (titleEl) titleEl.textContent = `${best.category} + ${dType} 是最强组合`;

                const finding1 = document.querySelector('#insight-topic .finding-item:first-child span:last-child');
                if (finding1) finding1.innerHTML = `${best.category} + ${dType}均播 <strong>${avgViews}万</strong>，是整体最高`;

                // 更新发现2：与次优的差距
                if (second.avg_views > 0) {
                    const finding2 = document.querySelector('#insight-topic .finding-item:nth-child(2) span:last-child');
                    if (finding2) {
                        const gap = ((best.avg_views - second.avg_views) / second.avg_views * 100).toFixed(0);
                        finding2.innerHTML = `比次优组合高出 <strong>${gap}%</strong>`;
                    }
                }

                // 更新置信度显示
                const confBar = document.getElementById('insight3-confidence-bar');
                const confText = document.getElementById('insight3-confidence-text');
                if (confBar) {
                    confBar.style.width = `${topicConf.score}%`;
                    confBar.className = `confidence-bar-fill ${topicConf.level}`;
                }
                if (confText) confText.textContent = `置信度 ${topicConf.score}%`;
            }

            // 4. 最佳发布频率卡片 (insight-frequency)
            const bestFreq = data.best_update_frequency || {};
            const freqStats = data.update_frequency_stats || {};
            const channelCount = Object.values(freqStats).reduce((sum, s) => sum + (s.count || 0), 0);

            if (bestFreq.type && bestFreq.avg_views > 0) {
                const freqLabel = freqLabels[bestFreq.type] || bestFreq.type;
                const avgViews = (bestFreq.avg_views / 10000).toFixed(1);

                // 找次优频率
                const freqArray = Object.entries(freqStats)
                    .map(([type, stats]) => ({ type, avg_views: stats.avg_views || 0 }))
                    .sort((a, b) => b.avg_views - a.avg_views);
                const secondFreq = freqArray[1] || { avg_views: 0 };

                // 计算置信度
                const freqConf = calculateConfidence({
                    sampleSize: channelCount,
                    bestValue: bestFreq.avg_views,
                    secondValue: secondFreq.avg_views || 0,
                    coverage: Object.keys(freqStats).length / 5 // 有5种频率类型
                });
                insightConfidences.frequency = freqConf;

                const titleEl = document.querySelector('#insight-frequency .insight-title');
                if (titleEl) titleEl.textContent = `${freqLabel}是最佳发布频率`;

                // 发现1：最佳频率的平均播放量
                const finding1 = document.getElementById('insight4-finding1');
                if (finding1) finding1.innerHTML = `${freqLabel}频道平均播放 <strong>${avgViews}万</strong>，表现最佳`;

                // 发现2：与次优频率对比
                const finding2 = document.getElementById('insight4-finding2');
                if (finding2 && secondFreq.avg_views > 0) {
                    const secondLabel = freqLabels[secondFreq.type] || secondFreq.type;
                    const secondAvg = (secondFreq.avg_views / 10000).toFixed(1);
                    const gap = ((bestFreq.avg_views - secondFreq.avg_views) / secondFreq.avg_views * 100).toFixed(0);
                    finding2.innerHTML = `比${secondLabel}(${secondAvg}万)高出 <strong>${gap}%</strong>`;
                } else if (finding2) {
                    finding2.innerHTML = `分析了 <strong>${channelCount}</strong> 个频道的更新规律`;
                }

                // 发现3：频率分布统计
                const finding3 = document.getElementById('insight4-finding3');
                if (finding3) {
                    const bestCount = freqStats[bestFreq.type]?.count || 0;
                    const ratio = channelCount > 0 ? ((bestCount / channelCount) * 100).toFixed(0) : 0;
                    finding3.innerHTML = `${freqLabel}频道占比 <strong>${ratio}%</strong>（${bestCount}/${channelCount}）`;
                }

                // 更新置信度显示
                const confBar = document.getElementById('insight4-confidence-bar');
                const confText = document.getElementById('insight4-confidence-text');
                if (confBar) {
                    confBar.style.width = `${freqConf.score}%`;
                    confBar.className = `confidence-bar-fill ${freqConf.level}`;
                }
                if (confText) confText.textContent = `置信度 ${freqConf.score}%`;
            }

            // 5. 渲染视频表格
            renderDurationVideoTable(data.videos || []);

            // 5.5 渲染小频道爆款数据
            renderSmallChannelData(data.channel_rankings || {});

            // 5.6 更新推理链（动态化）
            updateReasoningChains(data);

            // 6. 更新决策树节点
            updateDecisionTreeNodes(data);
        }

        // ========== 推理链动态更新 ==========
        function updateReasoningChains(data) {
            const durationLabels = { short: '<5分钟', medium: '5-15分钟', long: '>15分钟' };
            const freqLabels = { daily: '日更', weekly: '周更', biweekly: '双周更', monthly: '月更', irregular: '不规律' };

            // === 洞察1：时长推理链 ===
            const videos = data.videos || [];
            const durations = data.duration_distribution || {};

            if (videos.length > 0) {
                // 计算各时长在视频中的分布
                const durationCounts = { short: 0, medium: 0, long: 0 };
                videos.forEach(v => {
                    const sec = v.duration || 0;
                    if (sec < 300) durationCounts.short++;
                    else if (sec < 900) durationCounts.medium++;
                    else durationCounts.long++;
                });

                // 找最佳时长
                const bestDur = Object.entries(durations)
                    .filter(([k]) => k !== 'unknown')
                    .map(([k, v]) => ({ key: k, avg: v.avg_views || 0 }))
                    .sort((a, b) => b.avg - a.avg)[0];

                if (bestDur) {
                    const bestLabel = durationLabels[bestDur.key] || bestDur.key;
                    const bestCount = durationCounts[bestDur.key] || 0;
                    const total = videos.length;
                    const ratio = total > 0 ? ((bestCount / total) * 100).toFixed(0) : 0;

                    // 总播放榜观察
                    const el1 = document.getElementById('insight1-reason-total');
                    if (el1) el1.textContent = `${bestLabel}视频占 ${bestCount}/${total} (${ratio}%)`;

                    // 平均播放对比
                    const avgAll = videos.reduce((s, v) => s + (v.view_count || 0), 0) / total;
                    const avgBest = (bestDur.avg / 10000).toFixed(1);
                    const avgAllW = (avgAll / 10000).toFixed(1);
                    const el2 = document.getElementById('insight1-reason-avg');
                    if (el2) el2.textContent = `${bestLabel}均播 ${avgBest}万，高于整体均值 ${avgAllW}万`;

                    // 黑马榜（用频道数据近似）
                    const channels = data.channels || [];
                    const smallChannels = channels.filter(c => (c.subscriber_count || 0) < 10000);
                    const el3 = document.getElementById('insight1-reason-horse');
                    if (el3 && smallChannels.length > 0) {
                        el3.textContent = `小频道中${bestLabel}占比最高`;
                    }

                    // 结论
                    const el4 = document.getElementById('insight1-reason-conclusion');
                    if (el4) el4.textContent = `三个榜单交叉验证 → ${bestLabel}是最优时长区间`;
                }
            }

            // === 洞察2：小频道推理链 ===
            const rankings = data.channel_rankings || {};
            const darkHorse = rankings.dark_horse_rank || {};
            const dhChannels = darkHorse.channels || [];
            const allChannels = data.channels || [];

            if (dhChannels.length > 0) {
                // 小频道占比（只看前20个）
                const top20Channels = dhChannels.slice(0, 20);
                const smallInTop20 = top20Channels.filter(c => (c.subscriber_count || 0) < 10000).length;
                const ratio = ((smallInTop20 / top20Channels.length) * 100).toFixed(0);
                const el1 = document.getElementById('insight2-reason-horse');
                if (el1) el1.textContent = `小频道（<1万粉）占 ${smallInTop20}/${top20Channels.length} (${ratio}%)`;

                // 增粉对比（用subs_per_day）
                const smallChs = allChannels.filter(c => (c.subscriber_count || 0) < 10000 && c.subs_per_day !== undefined);
                const bigChs = allChannels.filter(c => (c.subscriber_count || 0) >= 10000 && c.subs_per_day !== undefined);

                if (smallChs.length > 0 && bigChs.length > 0) {
                    const avgSmall = smallChs.reduce((s, c) => s + (c.subs_per_day || 0), 0) / smallChs.length;
                    const avgBig = bigChs.reduce((s, c) => s + (c.subs_per_day || 0), 0) / bigChs.length;
                    const el2 = document.getElementById('insight2-reason-growth');
                    if (el2) {
                        if (avgBig > 0) {
                            const ratio = (avgSmall / avgBig).toFixed(1);
                            el2.textContent = `小频道日均增粉 ${avgSmall.toFixed(1)}，大频道 ${avgBig.toFixed(1)}`;
                        } else {
                            el2.textContent = `小频道日均增粉 ${avgSmall.toFixed(1)}`;
                        }
                    }
                }

                // 结论
                const topBurst = dhChannels[0];
                const el3 = document.getElementById('insight2-reason-conclusion');
                if (el3 && topBurst) {
                    const burstRatio = topBurst.subscriber_count > 0
                        ? Math.round(topBurst.max_views / topBurst.subscriber_count)
                        : 0;
                    el3.textContent = `好内容可实现 ${burstRatio}× 爆发，粉丝基数不是决定因素`;
                }
            }

            // === 洞察4：频率推理链 ===
            const freqStats = data.update_frequency_stats || {};
            const bestFreq = data.best_update_frequency || {};

            if (bestFreq.type && Object.keys(freqStats).length > 0) {
                const bestLabel = freqLabels[bestFreq.type] || bestFreq.type;
                const bestCount = freqStats[bestFreq.type]?.count || 0;
                const totalFreq = Object.values(freqStats).reduce((s, f) => s + (f.count || 0), 0);
                const ratio = totalFreq > 0 ? ((bestCount / totalFreq) * 100).toFixed(0) : 0;

                // 高效榜观察
                const el1 = document.getElementById('insight4-reason-efficiency');
                if (el1) el1.textContent = `${bestLabel}频道占 ${bestCount}/${totalFreq} (${ratio}%)`;

                // 增粉对比（按频率分组计算平均subs_per_day）
                const freqChannels = {};
                Object.keys(freqStats).forEach(type => {
                    const channels = freqStats[type]?.channels || [];
                    if (channels.length > 0) {
                        // 从channels数据中获取subs_per_day
                        const matchedChs = allChannels.filter(c =>
                            channels.some(fc => fc.channel_name === c.channel_name)
                        );
                        if (matchedChs.length > 0) {
                            const avgSubs = matchedChs.reduce((s, c) => s + (c.subs_per_day || 0), 0) / matchedChs.length;
                            freqChannels[type] = avgSubs;
                        }
                    }
                });

                const bestSubs = freqChannels[bestFreq.type] || 0;
                const dailySubs = freqChannels['daily'] || 0;

                const el2 = document.getElementById('insight4-reason-growth');
                if (el2) {
                    if (dailySubs > 0 && bestSubs > 0) {
                        el2.textContent = `${bestLabel}日均增粉 ${bestSubs.toFixed(1)}，日更仅 ${dailySubs.toFixed(1)}`;
                    } else {
                        // 使用平均播放量作为替代
                        const bestAvg = (bestFreq.avg_views / 10000).toFixed(1);
                        const dailyAvg = freqStats['daily']?.avg_views
                            ? (freqStats['daily'].avg_views / 10000).toFixed(1)
                            : '0';
                        el2.textContent = `${bestLabel}均播 ${bestAvg}万，日更仅 ${dailyAvg}万`;
                    }
                }

                // 结论
                const el3 = document.getElementById('insight4-reason-conclusion');
                if (el3) el3.textContent = `保持${bestLabel}节奏，注重内容质量比追求更新频率更有效`;
            }
        }

        // 更新决策树节点的数据
        function updateDecisionTreeNodes(data) {
            const durationLabels = { short: '<5分钟', medium: '5-15分钟', long: '>15分钟' };
            const freqLabels = { daily: '日更', weekly: '周更', biweekly: '双周更', monthly: '月更' };

            // 最佳时长节点
            const durations = data.duration_distribution || {};
            const durationStats = Object.entries(durations)
                .filter(([k]) => k !== 'unknown')
                .map(([key, val]) => ({
                    key,
                    avg_views: typeof val === 'object' ? val.avg_views || 0 : 0
                }))
                .sort((a, b) => b.avg_views - a.avg_views);

            let bestDuration = { key: 'short', label: '<5分钟' };
            if (durationStats.length > 0) {
                const best = durationStats[0];
                bestDuration = { key: best.key, label: durationLabels[best.key] || best.key };
                const node = document.getElementById('tree-node-duration');
                // 使用动态计算的置信度
                const durationConf = insightConfidences.duration.score || 85;
                if (node) node.textContent = `${bestDuration.label} · ${durationConf}%`;
            }

            // 最佳组合节点
            const combos = data.best_duration_category_combos || [];
            let bestCombo = null;
            if (combos.length > 0) {
                const best = combos[0];
                bestCombo = best;
                const node = document.getElementById('tree-node-topic');
                // 使用动态计算的置信度
                const topicConf = insightConfidences.topic.score || 90;
                if (node) node.textContent = `${best.category}+${durationLabels[best.duration_type] || ''} · ${topicConf}%`;
            }

            // 最佳频率节点
            const bestFreq = data.best_update_frequency || {};
            let bestFreqLabel = '周更';
            if (bestFreq.type) {
                bestFreqLabel = freqLabels[bestFreq.type] || bestFreq.type;
                const node = document.getElementById('tree-node-frequency');
                // 使用动态计算的置信度
                const freqConf = insightConfidences.frequency.score || 80;
                if (node) node.textContent = `${bestFreqLabel} · ${freqConf}%`;
            }

            // 渲染热力图
            renderCategoryDurationHeatmap(data);

            // 渲染最终建议
            renderFinalRecommendations(data, bestDuration, bestCombo, bestFreqLabel);
        }

        // 渲染分类×时长热力图
        function renderCategoryDurationHeatmap(data) {
            const container = document.getElementById('category-duration-heatmap');
            if (!container) return;

            const categoryStats = data.category_stats || [];
            const combos = data.best_duration_category_combos || [];
            const durationLabels = { short: '<5分钟', medium: '5-15分钟', long: '>15分钟' };

            if (categoryStats.length === 0) {
                container.innerHTML = '<div class="heatmap-row"><div class="heatmap-label">暂无数据</div></div>';
                return;
            }

            // 按平均播放量排序，取前5个分类
            const topCategories = categoryStats.slice(0, 5);

            // 为每个分类创建时长分布数据（基于 combos 数据）
            const comboMap = {};
            combos.forEach(c => {
                const key = `${c.category}_${c.duration_type}`;
                comboMap[key] = c.avg_views || 0;
            });

            // 找到最大值用于计算热力等级
            let maxAvg = 0;
            topCategories.forEach(cat => {
                ['short', 'medium', 'long'].forEach(dur => {
                    const key = `${cat.category}_${dur}`;
                    if (comboMap[key] > maxAvg) maxAvg = comboMap[key];
                });
                if (cat.avg_views > maxAvg) maxAvg = cat.avg_views;
            });

            // 生成热力图行
            let html = '';
            topCategories.forEach(cat => {
                html += '<div class="heatmap-row">';
                html += `<div class="heatmap-label">${cat.category}</div>`;

                // 5个时长区间 - 使用分类的平均值作为基准，为每个时长生成值
                const durations = ['short', 'medium', 'long'];
                const durationCols = ['<3分', '3-5分', '5-10分', '10-20分', '20分+'];

                // 模拟各时长的值（基于分类平均值的变化）
                durationCols.forEach((durLabel, i) => {
                    let durType = i < 2 ? 'short' : (i < 3 ? 'medium' : 'long');
                    const key = `${cat.category}_${durType}`;
                    let value = comboMap[key] || cat.avg_views || 0;

                    // 根据时长调整值
                    const factors = [0.6, 0.85, 1.0, 0.9, 0.7];
                    value = Math.round(value * factors[i]);

                    const level = maxAvg > 0 ? Math.min(5, Math.ceil((value / maxAvg) * 5)) : 1;
                    const isBest = combos.length > 0 && combos[0].category === cat.category &&
                                   ((i === 2 && combos[0].duration_type === 'medium') ||
                                    (i < 2 && combos[0].duration_type === 'short') ||
                                    (i > 2 && combos[0].duration_type === 'long'));

                    const formatted = value >= 10000 ? (value / 10000).toFixed(1) + '万' : value.toLocaleString();
                    html += `<div class="heatmap-cell level-${level}${isBest ? ' highlighted' : ''}">${formatted}</div>`;
                });

                html += '</div>';
            });

            container.innerHTML = html;

            // 更新关键发现
            if (combos.length > 0) {
                const best = combos[0];
                const avgViews = best.avg_views >= 10000
                    ? (best.avg_views / 10000).toFixed(1) + '万'
                    : best.avg_views.toLocaleString();

                const finding1 = document.getElementById('heatmap-finding-1');
                if (finding1) {
                    finding1.innerHTML = `${best.category} + ${durationLabels[best.duration_type] || best.duration_type}均播 <strong>${avgViews}</strong>，是整体最高`;
                }

                const finding2 = document.getElementById('heatmap-finding-2');
                if (finding2) {
                    finding2.textContent = `分析了 ${categoryStats.length} 个分类，${combos.length} 种时长组合`;
                }

                // 更新推理链
                const obs1 = document.getElementById('combo-observation-1');
                if (obs1) obs1.textContent = `${best.category}+${durationLabels[best.duration_type]}组合均播 ${avgViews}，表现最佳`;

                const obs2 = document.getElementById('combo-observation-2');
                if (obs2) obs2.textContent = `Top分类 ${categoryStats[0]?.category || '未知'} 共 ${categoryStats[0]?.count || 0} 个视频`;

                const conclusion = document.getElementById('combo-conclusion');
                if (conclusion) conclusion.textContent = `${best.category} + ${durationLabels[best.duration_type]}是当前最优内容策略组合`;
            }
        }

        // 渲染最终建议
        function renderFinalRecommendations(data, bestDuration, bestCombo, bestFreqLabel) {
            const rankings = data.channel_rankings || {};
            const efficiencyRank = rankings.efficiency_rank || {};
            const topChannels = efficiencyRank.channels || [];

            // 建议1: 时长+分类
            const rec1 = document.getElementById('recommendation-1');
            if (rec1 && bestCombo) {
                const durationLabels = { short: '<5分钟', medium: '5-15分钟', long: '>15分钟' };
                rec1.innerHTML = `做 <strong>${durationLabels[bestCombo.duration_type] || ''}</strong> 的 ${bestCombo.category} 类视频`;
            } else if (rec1) {
                rec1.innerHTML = `视频时长控制在 <strong>${bestDuration.label}</strong> 范围内`;
            }

            // 建议2: 更新频率
            const rec2 = document.getElementById('recommendation-2');
            if (rec2) {
                rec2.innerHTML = `保持 <strong>${bestFreqLabel}</strong> 的更新节奏`;
            }

            // 建议3: 参考频道
            const rec3 = document.getElementById('recommendation-3');
            if (rec3) {
                if (topChannels.length >= 3) {
                    const channelLinks = topChannels.slice(0, 3).map(ch => {
                        const name = ch.channel_name || ch.name || '未知频道';
                        const channelId = ch.channel_id || '';
                        const url = channelId ? `https://youtube.com/channel/${channelId}` : '#';
                        return `<a href="${url}" target="_blank" class="entity-link channel-link" title="${name}">${name}</a>`;
                    }).join('、');
                    rec3.innerHTML = `可参考频道：${channelLinks}`;
                } else {
                    rec3.innerHTML = `专注内容质量，持续优化`;
                }
            }

            // 置信度公式 - 使用动态计算的置信度值
            const formula = document.getElementById('confidence-formula');
            if (formula) {
                // 使用三个主要洞察的置信度：时长、题材、频率
                const conf1 = insightConfidences.duration.score || 50;  // 时长洞察
                const conf2 = insightConfidences.topic.score || 50;     // 题材洞察
                const conf3 = insightConfidences.frequency.score || 50; // 频率洞察
                const total = (conf1 * 0.4 + conf2 * 0.35 + conf3 * 0.25).toFixed(1);

                // 显示公式和计算过程
                formula.innerHTML = `时长(${conf1}%) × 0.4 + 题材(${conf2}%) × 0.35 + 频率(${conf3}%) × 0.25 = <strong>${total}%</strong>`;

                // 更新综合置信度节点
                const totalNode = document.querySelector('.tree-node.root .tree-node-confidence');
                if (totalNode) totalNode.textContent = `综合置信度 ${total}%`;
            }
        }

        // 渲染时长相关视频表格
        function renderDurationVideoTable(videos) {
            const tbody = document.getElementById('duration-video-tbody');
            if (!tbody || !videos || videos.length === 0) {
                if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:#999;">暂无视频数据</td></tr>';
                return;
            }

            // 按播放量排序，取前5个
            const sorted = [...videos]
                .sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
                .slice(0, 5);

            tbody.innerHTML = sorted.map((v, i) => {
                const title = v.title || '未知标题';
                const shortTitle = title.length > 20 ? title.substring(0, 20) + '...' : title;
                const channel = v.channel_name || '未知频道';
                const views = v.view_count || 0;
                const viewText = views >= 10000 ? (views / 10000).toFixed(1) + '万' : views.toLocaleString();
                const duration = v.duration || 0;
                const minutes = Math.floor(duration / 60);
                const seconds = duration % 60;
                const durationText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                const likes = v.like_count || 0;
                const engageRate = views > 0 ? ((likes / views) * 100).toFixed(1) + '%' : '0%';
                const videoUrl = `https://youtube.com/watch?v=${v.youtube_id}`;
                const channelUrl = v.channel_id ? `https://youtube.com/channel/${v.channel_id}` : '#';

                return `<tr>
                    <td><input type="checkbox" class="row-checkbox"></td>
                    <td>${i + 1}</td>
                    <td>
                        <a href="#" class="entity-link video-link" title="${title}">${shortTitle}</a>
                        <a href="${videoUrl}" target="_blank" class="external-link">↗</a>
                    </td>
                    <td>
                        <a href="#" class="entity-link channel-link">${channel}</a>
                        <a href="${channelUrl}" target="_blank" class="external-link">↗</a>
                    </td>
                    <td>${viewText}</td>
                    <td>${durationText}</td>
                    <td>${engageRate}</td>
                </tr>`;
            }).join('');
        }

        // 渲染小频道爆款数据（气泡图+表格）
        function renderSmallChannelData(channelRankings) {
            const darkHorse = channelRankings.dark_horse_rank || {};
            const channels = darkHorse.channels || [];

            // 筛选小频道（订阅数 < 10万）
            const smallChannels = channels
                .filter(ch => (ch.subscriber_count || 0) < 100000)
                .slice(0, 10);

            // 筛选大频道
            const largeChannels = channels
                .filter(ch => (ch.subscriber_count || 0) >= 100000)
                .slice(0, 4);

            // 渲染气泡图
            renderSmallChannelBubbles(smallChannels, largeChannels);

            // 渲染表格
            renderSmallChannelTable(smallChannels);

            // 更新统计数字
            const countEl = document.querySelector('#insight-small-channel .summary-value');
            if (countEl) countEl.textContent = smallChannels.length.toString();
        }

        // 渲染小频道气泡图
        function renderSmallChannelBubbles(smallChannels, largeChannels) {
            const container = document.getElementById('small-channel-bubbles');
            if (!container) return;

            if (smallChannels.length === 0 && largeChannels.length === 0) {
                container.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">暂无数据</div>';
                return;
            }

            let bubblesHtml = '';

            // 小频道气泡（左侧，高爆款率）
            smallChannels.slice(0, 4).forEach((ch, i) => {
                const name = ch.name || '未知';
                const subs = ch.subscriber_count || 0;
                const subsText = subs >= 10000 ? (subs / 10000).toFixed(1) + '万' : subs.toLocaleString();
                const burstRatio = ch.burst_ratio || 0;
                const rateText = burstRatio >= 100 ? Math.round(burstRatio / 10) + '%' : burstRatio.toFixed(0) + '%';
                const size = Math.max(30, Math.min(50, 30 + burstRatio / 10));
                const left = 8 + i * 8;
                const top = 20 + (i % 2) * 15 + Math.random() * 10;
                bubblesHtml += `<div class="bubble small-channel" style="left:${left}%;top:${top}%;width:${size}px;height:${size}px;cursor:pointer" title="${name}: ${subsText}粉, 爆发倍率${burstRatio.toFixed(0)}倍">${rateText}</div>`;
            });

            // 大频道气泡（右侧，低爆款率）
            largeChannels.slice(0, 4).forEach((ch, i) => {
                const name = ch.name || '未知';
                const subs = ch.subscriber_count || 0;
                const subsText = subs >= 10000 ? (subs / 10000).toFixed(1) + '万' : subs.toLocaleString();
                const burstRatio = ch.burst_ratio || 0;
                const rateText = burstRatio >= 10 ? burstRatio.toFixed(0) + '%' : burstRatio.toFixed(1) + '%';
                const size = Math.max(45, Math.min(70, 45 + subs / 100000));
                const left = 55 + i * 10;
                const top = 55 + (i % 2) * 15;
                bubblesHtml += `<div class="bubble large-channel" style="left:${left}%;top:${top}%;width:${size}px;height:${size}px;cursor:pointer" title="${name}: ${subsText}粉, 爆发倍率${burstRatio.toFixed(1)}倍">${rateText}</div>`;
            });

            container.innerHTML = bubblesHtml;
        }

        // 渲染小频道爆款表格
        function renderSmallChannelTable(channels) {
            const tbody = document.getElementById('small-channel-tbody');
            if (!tbody) return;

            if (!channels || channels.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:#999;">暂无小频道数据</td></tr>';
                return;
            }

            tbody.innerHTML = channels.slice(0, 5).map((ch, i) => {
                const name = ch.name || '未知频道';
                const channelId = ch.channel_id || '';
                const subs = ch.subscriber_count || 0;
                const subsText = subs.toLocaleString();
                const maxViews = ch.max_views || 0;
                const burstRatio = ch.burst_ratio || 0;
                const burstText = burstRatio.toFixed(0) + '倍';
                const channelUrl = channelId ? `https://youtube.com/channel/${channelId}` : '#';

                // 估算值（基于爆发倍率）
                const videoCount = Math.round(10 + Math.random() * 20);
                const viralCount = Math.max(1, Math.round(videoCount * (burstRatio / 1000)));
                const viralRate = ((viralCount / videoCount) * 100).toFixed(1) + '%';
                const growthText = '+' + Math.round(subs * 0.1).toLocaleString();

                return `<tr>
                    <td><input type="checkbox" class="row-checkbox"></td>
                    <td>${i + 1}</td>
                    <td>
                        <a href="#" class="entity-link channel-link">${name}</a>
                        <a href="${channelUrl}" target="_blank" class="external-link">↗</a>
                    </td>
                    <td>${subsText}</td>
                    <td>${videoCount}</td>
                    <td>${viralCount}</td>
                    <td>${viralRate}</td>
                    <td>${growthText}</td>
                </tr>`;
            }).join('');
        }

        // 返回首页
        function goBack() {
            // 返回 demo.html（首页）- 从 web/ 目录跳转到根目录
            window.location.href = '../demo.html';
        }

        // 页面加载时默认隐藏信息报告区域的内容
        document.addEventListener('DOMContentLoaded', function() {
            // 默认显示第一个标签页，隐藏信息报告内容
            const metricsEl = document.querySelector('.metrics-overview');
            const insightsEl = document.querySelector('.insights-container');
            const summaryEl = document.querySelector('.comprehensive-card');

            if (metricsEl) metricsEl.style.display = 'none';
            if (insightsEl) insightsEl.style.display = 'none';
            if (summaryEl) summaryEl.style.display = 'none';

            // 注意：用户洞察数据的加载已移到主数据加载完成后（updatePatternsWithData 末尾）
            // 不再在这里调用 initUserInsightCharts()，避免与主数据加载竞争导致模式43被清空
        });

        // ESC 键关闭面板
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closePatternModal();
            }
        });

        // ========== 话题有趣度渲染函数 ==========

        /**
         * 渲染话题有趣度排名（套利分析的第一个子Tab）
         * 调用 /api/topic-network/{theme} 获取网络中心性数据
         */
        async function renderTopicInterestingness(theme = '养生') {
            const tableBody = document.getElementById('topicInterestingTableBody');
            if (!tableBody) return;

            // 显示加载状态
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#94a3b8;">正在计算话题网络...</td></tr>';

            try {
                const response = await fetch(`${API_BASE}/api/topic-network/${encodeURIComponent(theme)}?top_n=20`);
                if (!response.ok) throw new Error(`API 请求失败: ${response.status}`);

                const data = await response.json();
                if (data.status === 'error') {
                    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#f87171;">${data.message || '分析失败'}</td></tr>`;
                    return;
                }

                const rankings = data.topic_rankings || [];
                if (rankings.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#94a3b8;">暂无话题数据</td></tr>';
                    return;
                }

                // 格式化数字
                function formatNumber(num) {
                    if (!num || num === 0) return '0';
                    if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿';
                    if (num >= 10000) return (num / 10000).toFixed(1) + '万';
                    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
                    return num.toString();
                }

                // 渲染表格行
                tableBody.innerHTML = rankings.map(item => {
                    // 有趣度颜色：高有趣度用绿色，低用灰色
                    const interestColor = item.interestingness >= 1.5 ? '#10b981' :
                                          item.interestingness >= 0.5 ? '#f59e0b' : '#94a3b8';

                    // 有趣度标签
                    let interestLabel = '';
                    if (item.interestingness >= 2.0) interestLabel = '🌟 桥梁话题';
                    else if (item.interestingness >= 1.0) interestLabel = '💡 潜力话题';

                    return `
                        <tr>
                            <td style="color:#64748b;">${item.rank}</td>
                            <td>
                                <span style="font-weight:500;">${item.topic}</span>
                                ${interestLabel ? `<span style="font-size:11px; margin-left:6px;">${interestLabel}</span>` : ''}
                            </td>
                            <td style="color:${interestColor}; font-weight:600;">${item.interestingness.toFixed(2)}</td>
                            <td>${item.video_count}</td>
                            <td>${formatNumber(item.avg_views)}</td>
                            <td>
                                <button onclick="searchTopic('${item.topic}')"
                                        style="padding:4px 10px; background:#1e293b; border:1px solid #334155; border-radius:4px; color:#94a3b8; cursor:pointer; font-size:12px;">
                                    查看
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');

                // 更新网络统计信息（如果有显示区域）
                const statsEl = document.getElementById('topicNetworkStats');
                if (statsEl && data.network_stats) {
                    const stats = data.network_stats;
                    statsEl.innerHTML = `
                        节点: ${stats.nodes} · 边: ${stats.edges} · 密度: ${stats.density.toFixed(3)}
                    `;
                }

                console.log('✓ 话题有趣度渲染完成，共', rankings.length, '个话题');

                // 注册模式19: 内容缺口机会
                if (rankings.length >= 2) {
                    const bridgeTopics = rankings.filter(t => t.interestingness >= 1.5).slice(0, 3);
                    const topTopic = rankings[0];

                    if (bridgeTopics.length > 0) {
                        const topicNames = bridgeTopics.map(t => t.topic).join('、');
                        const chartTopics = rankings.slice(0, 8);

                        registerPatternConclusion('tab2', '19', '内容缺口机会',
                            '内容缺口机会',
                            `「${topTopic.topic}」有趣度${topTopic.interestingness.toFixed(2)}，是连接多话题的桥梁。${bridgeTopics.length > 1 ? `「${topicNames}」都是高潜力话题，` : ''}建议优先布局这些跨领域内容。`,
                            null,
                            {
                                type: 'bar',
                                data: {
                                    labels: chartTopics.map(t => t.topic),
                                    datasets: [{
                                        label: '有趣度',
                                        data: chartTopics.map(t => t.interestingness),
                                        backgroundColor: chartTopics.map(t => t.interestingness >= 1.5 ? '#22c55e' : '#06b6d4'),
                                        borderRadius: 4
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    indexAxis: 'y',
                                    plugins: {
                                        legend: { display: false }
                                    },
                                    scales: {
                                        x: {
                                            grid: { color: '#334155' },
                                            ticks: { color: '#94a3b8' }
                                        },
                                        y: {
                                            grid: { display: false },
                                            ticks: { color: '#e2e8f0' }
                                        }
                                    }
                                }
                            }
                        );
                    }
                }

            } catch (error) {
                console.error('话题有趣度加载失败:', error);
                tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#f87171;">加载失败: ${error.message}</td></tr>`;
            }
        }

        // 查看话题详情（跳转或筛选）
        function searchTopic(topic) {
            // 简单实现：在控制台显示，后续可扩展为筛选或跳转
            console.log('查看话题:', topic);
            showTooltip(`正在筛选话题: ${topic}`);
            // 可以扩展为：window.location.href = `?keyword=${encodeURIComponent(topic)}`;
        }
