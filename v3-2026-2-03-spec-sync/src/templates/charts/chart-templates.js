/**
 * Chart.js 图表模板库
 * 基于 v1 报告系统提取，用于全局认识和套利分析页面
 *
 * 依赖: Chart.js v4+
 * CDN: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
 */

// ============================================
// 1. 数字卡片模板 (非图表，但常用)
// ============================================

/**
 * 生成数字卡片 HTML
 * @param {Object} config - { label, value, sub, highlight }
 */
function createStatCard({ label, value, sub = '', highlight = false }) {
  const highlightClass = highlight ? 'card highlight' : 'card';
  return `
    <div class="${highlightClass}">
      <div class="card-label">${label}</div>
      <div class="card-value">${typeof value === 'number' ? value.toLocaleString() : value}</div>
      ${sub ? `<div class="card-sub">${sub}</div>` : ''}
    </div>
  `;
}

/**
 * 生成多个卡片的容器
 * @param {Array} cards - 卡片配置数组
 */
function createStatCardsRow(cards) {
  return `
    <div class="cards">
      ${cards.map(card => createStatCard(card)).join('')}
    </div>
  `;
}


// ============================================
// 2. 柱状图模板 (Bar Chart)
// ============================================

/**
 * 创建垂直柱状图
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { labels, data, label, color }
 */
function createBarChart(canvasId, { labels, data, label = '数量', color = '#667eea' }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        backgroundColor: color
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } }
    }
  });
}

/**
 * 创建水平柱状图
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { labels, data, label, colors }
 */
function createHorizontalBarChart(canvasId, { labels, data, label = '数量', colors = null }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const defaultColors = ['#f5576c', '#f093fb', '#667eea', '#4facfe', '#00f2fe'];

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        backgroundColor: colors || defaultColors.slice(0, data.length)
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } }
    }
  });
}


// ============================================
// 3. 饼图/环形图模板 (Pie/Doughnut Chart)
// ============================================

/**
 * 创建饼图
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { labels, data, colors }
 */
function createPieChart(canvasId, { labels, data, colors = null }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const defaultColors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

  return new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors || defaultColors.slice(0, data.length)
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right' } }
    }
  });
}

/**
 * 创建环形图 (Doughnut)
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { labels, data, colors }
 */
function createDoughnutChart(canvasId, { labels, data, colors = null }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const defaultColors = ['#667eea', '#764ba2', '#f093fb', '#f5576c'];

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors || defaultColors.slice(0, data.length)
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'right' } }
    }
  });
}


// ============================================
// 4. 折线图模板 (Line Chart)
// ============================================

/**
 * 创建基础折线图
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { labels, data, label, color, fill }
 */
function createLineChart(canvasId, { labels, data, label = '趋势', color = '#667eea', fill = true }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        borderColor: color,
        backgroundColor: fill ? `${color}1a` : 'transparent', // 10% opacity
        fill: fill,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
}

/**
 * 创建双轴折线图 (用于增长趋势)
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { labels, cumulativeData, dailyData }
 */
function createDualAxisLineChart(canvasId, { labels, cumulativeData, dailyData }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: '累计播放量',
          data: cumulativeData,
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          fill: true,
          tension: 0.3,
          yAxisID: 'y',
        },
        {
          label: '日增长',
          data: dailyData,
          borderColor: '#f5576c',
          backgroundColor: 'rgba(245, 87, 108, 0.3)',
          fill: true,
          tension: 0.3,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: '累计播放量' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: '日增长' },
          grid: { drawOnChartArea: false },
        }
      }
    }
  });
}


// ============================================
// 5. 雷达图模板 (Radar Chart)
// ============================================

/**
 * 创建雷达图 (用于星期分布等)
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { labels, data, label, color }
 */
function createRadarChart(canvasId, { labels, data, label = '分布', color = '#667eea' }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        borderColor: color,
        backgroundColor: `${color}33` // 20% opacity
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
}


// ============================================
// 6. 散点图模板 (Scatter Chart)
// ============================================

/**
 * 创建四象限散点图 (播放量×互动率)
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { data, xLabel, yLabel }
 */
function createScatterChart(canvasId, { data, xLabel = 'X轴', yLabel = 'Y轴' }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [{
        label: '数据点',
        data: data, // [{ x: value, y: value }, ...]
        backgroundColor: 'rgba(102, 126, 234, 0.6)',
        borderColor: '#667eea',
        pointRadius: 5,
        pointHoverRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: xLabel }
        },
        y: {
          title: { display: true, text: yLabel }
        }
      }
    }
  });
}


// ============================================
// 7. 直方图模板 (Histogram - 用柱状图模拟)
// ============================================

/**
 * 创建播放量分布直方图
 * @param {string} canvasId - canvas 元素 ID
 * @param {Object} config - { bins, counts }
 */
function createHistogram(canvasId, { bins, counts }) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: bins,
      datasets: [{
        label: '视频数量',
        data: counts,
        backgroundColor: '#667eea',
        borderColor: '#5a6fd6',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          title: { display: true, text: '播放量区间' }
        },
        y: {
          title: { display: true, text: '视频数量' },
          beginAtZero: true
        }
      }
    }
  });
}


// ============================================
// 8. 进度条模板 (非 Chart.js)
// ============================================

/**
 * 生成进度条 HTML
 * @param {Object} config - { value, max, label }
 */
function createProgressBar({ value, max = 100, label = '' }) {
  const percentage = Math.min(100, (value / max) * 100);
  return `
    <div style="margin-bottom: 15px;">
      ${label ? `<p style="margin-bottom: 5px;"><strong>${label}:</strong> ${value}/${max} (${percentage.toFixed(1)}%)</p>` : ''}
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${percentage}%"></div>
      </div>
    </div>
  `;
}


// ============================================
// 9. 图表容器模板
// ============================================

/**
 * 生成图表容器 HTML
 * @param {Object} config - { id, title, height }
 */
function createChartContainer({ id, title, height = 300 }) {
  return `
    <div class="chart-container">
      <div class="chart-title">${title}</div>
      <div class="chart-wrapper" style="height: ${height}px;">
        <canvas id="${id}"></canvas>
      </div>
    </div>
  `;
}

/**
 * 生成两列图表布局
 * @param {string} leftHtml - 左侧 HTML
 * @param {string} rightHtml - 右侧 HTML
 */
function createTwoColumnLayout(leftHtml, rightHtml) {
  return `
    <div class="grid-2">
      ${leftHtml}
      ${rightHtml}
    </div>
  `;
}


// ============================================
// 10. 洞察卡片模板
// ============================================

/**
 * 生成洞察卡片 HTML
 * @param {Object} config - { title, text }
 */
function createInsightCard({ title = '', text }) {
  return `
    <div class="insight">
      ${title ? `<div class="insight-title">${title}</div>` : ''}
      <div class="insight-text">${text}</div>
    </div>
  `;
}

/**
 * 生成多个洞察卡片
 * @param {Array} insights - 洞察文本数组
 */
function createInsightsList(insights) {
  return insights.map(text => createInsightCard({ text })).join('');
}


// ============================================
// 11. 网络图模板 (Force-Directed Graph)
// 依赖: vis-network
// CDN: <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
// ============================================

/**
 * 创建力导向网络图 (用于套利分析的信息网络)
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { nodes, edges, options }
 *
 * nodes 格式: [{ id: 1, label: '视频A', value: 100, group: 'hot' }, ...]
 * edges 格式: [{ from: 1, to: 2, value: 5 }, ...]
 */
function createNetworkGraph(containerId, { nodes, edges, options = {} }) {
  const container = document.getElementById(containerId);
  if (!container) return null;

  const defaultOptions = {
    nodes: {
      shape: 'dot',
      scaling: {
        min: 10,
        max: 50,
        label: { enabled: true, min: 14, max: 30 }
      },
      font: { size: 12, face: 'Arial' }
    },
    edges: {
      width: 0.5,
      color: { inherit: 'from' },
      smooth: { type: 'continuous' }
    },
    physics: {
      stabilization: { iterations: 100 },
      barnesHut: {
        gravitationalConstant: -2000,
        springConstant: 0.04,
        springLength: 95
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      hideEdgesOnDrag: true
    },
    groups: {
      hot: { color: { background: '#f5576c', border: '#d9534f' } },
      medium: { color: { background: '#667eea', border: '#5a6fd6' } },
      cold: { color: { background: '#4facfe', border: '#3d8bd4' } },
      interesting: { color: { background: '#ffd700', border: '#daa520' } }
    }
  };

  const mergedOptions = { ...defaultOptions, ...options };
  const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };

  return new vis.Network(container, data, mergedOptions);
}

/**
 * 创建有趣度网络图 (中介中心性 / 程度中心性)
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { videos, links, metric }
 *
 * metric: 'interestingness' | 'betweenness' | 'degree'
 */
function createInterestingnessNetwork(containerId, { videos, links, metric = 'interestingness' }) {
  // 根据指标计算节点大小和颜色
  const nodes = videos.map(v => {
    let value, group;
    switch(metric) {
      case 'betweenness':
        value = v.betweenness_centrality * 100;
        group = value > 50 ? 'hot' : value > 20 ? 'medium' : 'cold';
        break;
      case 'degree':
        value = v.degree_centrality * 100;
        group = value > 50 ? 'hot' : value > 20 ? 'medium' : 'cold';
        break;
      case 'interestingness':
      default:
        value = v.interestingness * 100;
        group = value > 1 ? 'interesting' : value > 0.5 ? 'hot' : 'medium';
        break;
    }
    return {
      id: v.id,
      label: v.title.substring(0, 20) + '...',
      value: value,
      group: group,
      title: `${v.title}\n播放量: ${v.views.toLocaleString()}\n${metric}: ${value.toFixed(2)}`
    };
  });

  const edges = links.map(l => ({
    from: l.source,
    to: l.target,
    value: l.weight || 1
  }));

  return createNetworkGraph(containerId, { nodes, edges });
}


// ============================================
// 12. 地图模板 (Geographic Map)
// 依赖: Leaflet
// CDN: <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
//      <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
// ============================================

/**
 * 创建基础地图
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { center, zoom, markers }
 *
 * markers 格式: [{ lat, lng, title, popup, size }, ...]
 */
function createMap(containerId, { center = [35.8617, 104.1954], zoom = 4, markers = [] }) {
  const container = document.getElementById(containerId);
  if (!container) return null;

  const map = L.map(containerId).setView(center, zoom);

  // 使用 OpenStreetMap 瓦片
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  // 添加标记点
  markers.forEach(m => {
    const marker = L.circleMarker([m.lat, m.lng], {
      radius: m.size || 8,
      fillColor: m.color || '#667eea',
      color: '#fff',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(map);

    if (m.popup) {
      marker.bindPopup(m.popup);
    }
    if (m.title) {
      marker.bindTooltip(m.title);
    }
  });

  return map;
}

/**
 * 创建频道地理分布地图
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { channels }
 *
 * channels 格式: [{ name, lat, lng, subscribers, videos }, ...]
 */
function createChannelDistributionMap(containerId, { channels }) {
  const maxSubs = Math.max(...channels.map(c => c.subscribers));

  const markers = channels.map(c => ({
    lat: c.lat,
    lng: c.lng,
    title: c.name,
    size: 5 + (c.subscribers / maxSubs) * 20,
    color: c.subscribers > 100000 ? '#f5576c' : c.subscribers > 10000 ? '#667eea' : '#4facfe',
    popup: `<b>${c.name}</b><br>订阅: ${c.subscribers.toLocaleString()}<br>视频: ${c.videos}`
  }));

  return createMap(containerId, { markers });
}


// ============================================
// 13. 热力图模板 (Heatmap)
// 依赖: Chart.js + chartjs-chart-matrix 插件
// 或使用 ECharts
// ============================================

/**
 * 创建时间热力图 (发布时间 × 星期)
 * 使用 ECharts 实现
 * 依赖: <script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
 *
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { data, xLabels, yLabels }
 *
 * data 格式: [[x, y, value], ...] 例如 [[0, 0, 5], [0, 1, 10], ...]
 */
function createHeatmap(containerId, { data, xLabels, yLabels, title = '' }) {
  const container = document.getElementById(containerId);
  if (!container || typeof echarts === 'undefined') return null;

  const chart = echarts.init(container);

  const option = {
    title: { text: title, left: 'center' },
    tooltip: {
      position: 'top',
      formatter: function(params) {
        return `${yLabels[params.data[1]]} ${xLabels[params.data[0]]}<br>数量: ${params.data[2]}`;
      }
    },
    grid: {
      top: '15%',
      left: '15%',
      right: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: xLabels,
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: yLabels,
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: Math.max(...data.map(d => d[2])),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#f5f7fa', '#667eea', '#764ba2', '#f5576c']
      }
    },
    series: [{
      name: '数量',
      type: 'heatmap',
      data: data,
      label: { show: true },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      }
    }]
  };

  chart.setOption(option);
  return chart;
}

/**
 * 创建发布时间热力图 (小时 × 星期)
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { publishTimes }
 *
 * publishTimes 格式: [{ dayOfWeek: 0-6, hour: 0-23, count: number }, ...]
 */
function createPublishTimeHeatmap(containerId, { publishTimes }) {
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

  // 转换数据格式
  const data = publishTimes.map(pt => [pt.hour, pt.dayOfWeek, pt.count]);

  return createHeatmap(containerId, {
    data,
    xLabels: hours,
    yLabels: days,
    title: '发布时间分布'
  });
}


// ============================================
// 14. 树图模板 (Treemap)
// 依赖: ECharts
// ============================================

/**
 * 创建树图 (用于分类/标签分布)
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { data, title }
 *
 * data 格式: [{ name: '分类A', value: 100, children: [...] }, ...]
 */
function createTreemap(containerId, { data, title = '' }) {
  const container = document.getElementById(containerId);
  if (!container || typeof echarts === 'undefined') return null;

  const chart = echarts.init(container);

  const option = {
    title: { text: title, left: 'center' },
    tooltip: {
      formatter: function(info) {
        return `${info.name}<br>数量: ${info.value.toLocaleString()}`;
      }
    },
    series: [{
      type: 'treemap',
      data: data,
      leafDepth: 1,
      label: {
        show: true,
        formatter: '{b}'
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2,
        gapWidth: 2
      },
      levels: [
        {
          itemStyle: {
            borderColor: '#555',
            borderWidth: 4,
            gapWidth: 4
          }
        },
        {
          colorSaturation: [0.3, 0.6],
          itemStyle: {
            borderColorSaturation: 0.7,
            gapWidth: 2,
            borderWidth: 2
          }
        }
      ]
    }]
  };

  chart.setOption(option);
  return chart;
}


// ============================================
// 15. 桑基图模板 (Sankey Diagram)
// 依赖: ECharts
// ============================================

/**
 * 创建桑基图 (用于流量流向分析)
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { nodes, links, title }
 *
 * nodes 格式: [{ name: '节点A' }, ...]
 * links 格式: [{ source: '节点A', target: '节点B', value: 100 }, ...]
 */
function createSankeyDiagram(containerId, { nodes, links, title = '' }) {
  const container = document.getElementById(containerId);
  if (!container || typeof echarts === 'undefined') return null;

  const chart = echarts.init(container);

  const option = {
    title: { text: title, left: 'center' },
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove'
    },
    series: [{
      type: 'sankey',
      data: nodes,
      links: links,
      emphasis: { focus: 'adjacency' },
      lineStyle: {
        color: 'gradient',
        curveness: 0.5
      }
    }]
  };

  chart.setOption(option);
  return chart;
}


// ============================================
// 16. 词云模板 (Word Cloud)
// 依赖: ECharts + echarts-wordcloud
// CDN: <script src="https://cdn.jsdelivr.net/npm/echarts-wordcloud/dist/echarts-wordcloud.min.js"></script>
// ============================================

/**
 * 创建词云图 (用于关键词/标签分析)
 * @param {string} containerId - 容器元素 ID
 * @param {Object} config - { words, title }
 *
 * words 格式: [{ name: '关键词', value: 100 }, ...]
 */
function createWordCloud(containerId, { words, title = '' }) {
  const container = document.getElementById(containerId);
  if (!container || typeof echarts === 'undefined') return null;

  const chart = echarts.init(container);

  const option = {
    title: { text: title, left: 'center' },
    tooltip: { show: true },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '90%',
      height: '90%',
      rotationRange: [-45, 45],
      rotationStep: 45,
      gridSize: 8,
      sizeRange: [12, 60],
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: function() {
          const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'];
          return colors[Math.floor(Math.random() * colors.length)];
        }
      },
      data: words
    }]
  };

  chart.setOption(option);
  return chart;
}


// ============================================
// 导出 (ES Modules)
// ============================================

export {
  // 卡片
  createStatCard,
  createStatCardsRow,
  // 柱状图
  createBarChart,
  createHorizontalBarChart,
  // 饼图
  createPieChart,
  createDoughnutChart,
  // 折线图
  createLineChart,
  createDualAxisLineChart,
  // 雷达图
  createRadarChart,
  // 散点图
  createScatterChart,
  // 直方图
  createHistogram,
  // 进度条
  createProgressBar,
  // 容器
  createChartContainer,
  createTwoColumnLayout,
  // 洞察
  createInsightCard,
  createInsightsList,
  // 网络图 (vis.js)
  createNetworkGraph,
  createInterestingnessNetwork,
  // 地图 (Leaflet)
  createMap,
  createChannelDistributionMap,
  // 热力图 (ECharts)
  createHeatmap,
  createPublishTimeHeatmap,
  // 树图 (ECharts)
  createTreemap,
  // 桑基图 (ECharts)
  createSankeyDiagram,
  // 词云 (ECharts)
  createWordCloud
};
