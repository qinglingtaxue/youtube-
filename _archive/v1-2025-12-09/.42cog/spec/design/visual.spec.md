# 视觉设计规约 (Visual Design Specification)

## 规约概述

本规约定义YouTube视频创作工作流的视觉设计标准，包括色彩、字体、图标、数据可视化等视觉元素。

## 前置条件

### 设计理念
- 专业简洁
- 数据驱动
- 高效直观
- 品牌一致

### 应用场景
- 界面视觉
- 数据可视化
- 报告设计
- 品牌传播

## 详细规约

### 1. 色彩系统

#### 1.1 主色调
**品牌色彩**
```css
:root {
  /* 主色 */
  --primary-color: #007bff;      /* 专业蓝 */
  --primary-light: #4dabf7;      /* 浅蓝 */
  --primary-dark: #0056b3;       /* 深蓝 */
  
  /* 辅助色 */
  --secondary-color: #6c757d;    /* 中性灰 */
  --accent-color: #28a745;       /* 成功绿 */
  --warning-color: #ffc107;      /* 警告黄 */
  --danger-color: #dc3545;       /* 危险红 */
}
```

#### 1.2 功能色彩
**状态色彩**
```css
/* 数据可视化色彩 */
--chart-blue: #4dabf7;
--chart-green: #51cf66;
--chart-yellow: #ffd43b;
--chart-red: #ff6b6b;
--chart-purple: #845ef7;
--chart-orange: #ff922b;

/* 模式色彩 */
--pattern-cognitive: #007bff;     /* 认知冲击 */
--pattern-storytelling: #28a745;  /* 故事叙述 */
--pattern-knowledge: #ffc107;     /* 干货输出 */
--pattern-interaction: #6f42c1;   /* 互动引导 */
```

### 2. 字体系统

#### 2.1 字体族
**字体规范**
```css
/* 主字体 */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", 
             "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", 
             "Helvetica Neue", Helvetica, Arial, sans-serif;

/* 数字字体 */
font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", 
             Consolas, "Courier New", monospace;
```

#### 2.2 字号层级
**字号规范**
```css
/* 标题层级 */
.text-h1 { font-size: 32px; font-weight: 700; line-height: 1.2; }
.text-h2 { font-size: 28px; font-weight: 600; line-height: 1.3; }
.text-h3 { font-size: 24px; font-weight: 600; line-height: 1.3; }
.text-h4 { font-size: 20px; font-weight: 500; line-height: 1.4; }

/* 正文字体 */
.text-body { font-size: 14px; font-weight: 400; line-height: 1.6; }
.text-small { font-size: 12px; font-weight: 400; line-height: 1.5; }
.text-caption { font-size: 11px; font-weight: 400; line-height: 1.4; }
```

### 3. 图标系统

#### 3.1 图标风格
**设计原则**
- 线性图标，2px描边
- 圆角处理，4px半径
- 统一视角，正面呈现
- 简洁明了，避免细节

#### 3.2 常用图标
**功能图标**
```
工作流图标
🔍 调研分析 - 搜索图标
📝 模式抽象 - 文档图标
✍️ 实战创作 - 编辑图标
📈 效果追踪 - 图表图标

数据图标
📊 数据分析 - 柱状图
📹 视频案例 - 播放图标
📄 模板库 - 文档集合
🎯 精准定位 - 目标图标
```

### 4. 数据可视化

#### 4.1 图表配色方案
**配色规范**
```javascript
const chartColors = {
  // 模式分析图表
  patterns: [
    '#007bff', // 认知冲击
    '#28a745', // 故事叙述
    '#ffc107', // 干货输出
    '#6f42c1', // 互动引导
    '#fd7e14'  // 其他
  ],
  
  // 趋势分析图表
  trends: [
    '#4dabf7', // 播放量
    '#51cf66', // 点赞量
    '#ffd43b', // 评论量
    '#ff6b6b'  // 分享量
  ],
  
  // 对比分析图表
  comparison: [
    '#007bff',
    '#28a745',
    '#6c757d',
    '#ffc107'
  ]
}
```

#### 4.2 图表样式
**柱状图样式**
```css
.chart-bar {
  fill: var(--chart-blue);
  transition: fill 0.3s;
}

.chart-bar:hover {
  fill: var(--primary-dark);
}

.chart-axis {
  stroke: #dee2e6;
  stroke-width: 1;
}

.chart-label {
  font-size: 12px;
  fill: #6c757d;
}
```

#### 4.3 数据卡片设计
**卡片样式**
```html
<div class="data-card">
  <div class="card-header">
    <h3 class="card-title">播放量趋势</h3>
    <span class="card-trend up">+15.3%</span>
  </div>
  <div class="card-content">
    <div class="metric-value">2.3M</div>
    <div class="metric-label">平均播放量</div>
  </div>
  <div class="card-chart">
    <!-- 迷你图表 -->
  </div>
</div>
```

### 5. 插画系统

#### 5.1 插画风格
**设计特点**
- 扁平化插画
- 统一的色彩体系
- 简洁的几何形状
- 温暖的人性化元素

#### 5.2 插画应用
**使用场景**
- 空状态页面
- 引导页设计
- 成功/错误页面
- 功能介绍

### 6. 动效设计

#### 6.1 基础动效
**动效规范**
```css
/* 淡入淡出 */
.fade-enter {
  opacity: 0;
}

.fade-enter-active {
  opacity: 1;
  transition: opacity 300ms;
}

/* 滑动 */
.slide-enter {
  transform: translateX(-100%);
}

.slide-enter-active {
  transform: translateX(0);
  transition: transform 300ms;
}

/* 缩放 */
.scale-enter {
  transform: scale(0.9);
}

.scale-enter-active {
  transform: scale(1);
  transition: transform 200ms;
}
```

#### 6.2 数据动效
**数字递增**
```javascript
function animateNumber(element, start, end, duration) {
  const startTime = performance.now();
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    const current = Math.floor(start + (end - start) * progress);
    element.textContent = current.toLocaleString();
    
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  
  requestAnimationFrame(update);
}
```

### 7. 响应式视觉

#### 7.1 移动端适配
**视觉调整**
```css
@media (max-width: 768px) {
  .data-card {
    padding: 16px;
  }
  
  .chart-container {
    height: 200px;
  }
  
  .text-h2 {
    font-size: 24px;
  }
}
```

#### 7.2 暗色主题
**暗色配色**
```css
[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --border-color: #404040;
}
```

## 验收标准

### 视觉一致性验收
- [x] 色彩使用符合设计系统
- [x] 字体层级清晰统一
- [x] 图标风格一致
- [x] 间距使用8px基础单位

### 可读性验收
- [x] 文字对比度 ≥ 4.5:1
- [x] 重要信息视觉权重突出
- [x] 数据可视化清晰直观
- [x] 状态反馈及时明确

### 品牌一致性验收
- [x] 视觉风格符合品牌调性
- [x] 设计元素可复用
- [x] 不同页面风格统一
- [x] 品牌识别度高

### 响应式验收
- [x] 不同屏幕尺寸适配良好
- [x] 移动端体验优秀
- [x] 暗色主题完整
- [x] 动效流畅自然

---

**验收结论**：视觉设计规约确保产品具有专业、现代的视觉呈现，提升用户体验和品牌价值。
