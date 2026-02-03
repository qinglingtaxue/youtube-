# 界面设计规约 (UI Design Specification)

## 规约概述

本规约定义YouTube视频创作工作流的用户界面设计标准，确保界面简洁、直观、高效。

## 前置条件

### 设计原则
- 简洁明了：界面元素精简，避免信息过载
- 高效操作：支持快速完成核心任务
- 一致性：保持设计语言统一
- 可访问性：支持不同能力用户使用

### 用户特征
- 内容创作者
- 短视频运营
- 营销人员

## 详细规约

### 1. 整体布局

#### 1.1 页面结构
**标准布局**
```
┌─────────────────────────────────────────────────────────────┐
│                        顶部导航栏                              │
├─────────────────────────────────────────────────────────────┤
│  侧边栏  │                主内容区域                          │
│  宽度    │                宽度自适应                         │
│  240px   │                                                    │
├─────────────────────────────────────────────────────────────┤
│                        底部状态栏                              │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 响应式设计
**断点设置**
```css
/* 移动端 */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main-content {
    margin-left: 0;
  }
}

/* 平板端 */
@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar {
    width: 200px;
  }
}

/* 桌面端 */
@media (min-width: 1025px) {
  .sidebar {
    width: 240px;
  }
}
```

### 2. 导航设计

#### 2.1 顶部导航
**导航结构**
```html
<nav class="top-nav">
  <div class="logo">YouTube研究助手</div>
  <div class="search">
    <input type="search" placeholder="搜索模板、案例...">
  </div>
  <div class="actions">
    <button class="btn-primary">开始调研</button>
    <button class="btn-secondary">模板库</button>
  </div>
</nav>
```

#### 2.2 侧边导航
**菜单结构**
```
📊 工作流
├── 🔍 事件1：调研分析
├── 📝 事件2：模式抽象
├── ✍️ 事件3：实战创作
└── 📈 效果追踪

📚 资源库
├── 📹 案例库
├── 📄 模板库
└── 📊 数据分析

⚙️ 设置
├── 👤 个人设置
└── 🔧 系统配置
```

### 3. 工作流界面

#### 3.1 事件1：调研分析
**界面布局**
```html
<div class="research-phase">
  <div class="phase-header">
    <h2>事件1：调研分析</h2>
    <div class="progress">60/60分钟</div>
  </div>
  
  <div class="phase-content">
    <div class="input-section">
      <label>调研主题</label>
      <input type="text" placeholder="输入关键词，如：老人养生">
      <button class="btn-primary">开始调研</button>
    </div>
    
    <div class="status-section">
      <div class="status-item">
        <span class="label">数据收集</span>
        <div class="progress-bar">
          <div class="progress-fill" style="width: 100%"></div>
        </div>
        <span class="status">已完成</span>
      </div>
      
      <div class="status-item">
        <span class="label">深度分析</span>
        <div class="progress-bar">
          <div class="progress-fill" style="width: 60%"></div>
        </div>
        <span class="status">进行中</span>
      </div>
    </div>
  </div>
</div>
```

#### 3.2 案例展示区域
**案例卡片设计**
```html
<div class="case-cards">
  <div class="case-card">
    <div class="card-thumbnail">
      <img src="video-thumbnail.jpg" alt="视频封面">
      <span class="duration">05:32</span>
    </div>
    <div class="card-content">
      <h3 class="video-title">75岁老人的养生秘诀</h3>
      <div class="video-stats">
        <span>播放：341K</span>
        <span>点赞：12K</span>
        <span>模式：认知冲击</span>
      </div>
      <div class="card-actions">
        <button class="btn-analyze">分析案例</button>
        <button class="btn-template">生成模板</button>
      </div>
    </div>
  </div>
</div>
```

### 4. 数据可视化

#### 4.1 模式分布图
**图表设计**
```javascript
const patternChart = {
  type: 'radar',
  data: {
    labels: ['认知冲击', '故事叙述', '干货输出', '互动引导'],
    datasets: [{
      label: '案例分布',
      data: [30, 25, 35, 10],
      backgroundColor: 'rgba(54, 162, 235, 0.2)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 2
    }]
  },
  options: {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: '创作模式分布'
      }
    }
  }
}
```

#### 4.2 趋势分析图
**趋势图表**
```javascript
const trendChart = {
  type: 'line',
  data: {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    datasets: [{
      label: '播放量趋势',
      data: [120000, 180000, 250000, 320000, 280000, 350000],
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true
      }
    }
  }
}
```

### 5. 交互设计

#### 5.1 按钮设计
**按钮规范**
```css
/* 主要按钮 */
.btn-primary {
  background: #007bff;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #0056b3;
  transform: translateY(-1px);
}

/* 次要按钮 */
.btn-secondary {
  background: transparent;
  color: #007bff;
  border: 1px solid #007bff;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
```

#### 5.2 表单设计
**输入框规范**
```css
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}
```

### 6. 反馈设计

#### 6.1 加载状态
**加载动画**
```html
<div class="loading-spinner">
  <div class="spinner"></div>
  <p>正在分析案例...</p>
</div>

<style>
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
```

#### 6.2 成功反馈
**成功提示**
```html
<div class="alert alert-success">
  <span class="alert-icon">✓</span>
  <span class="alert-message">模板生成成功！</span>
  <button class="alert-close">×</button>
</div>
```

### 7. 无障碍设计

#### 7.1 键盘导航
**导航支持**
```html
<!-- 为所有交互元素添加tabindex -->
<button tabindex="0" class="btn-primary">开始调研</button>
<input tabindex="0" type="text" placeholder="输入关键词">

<!-- 添加ARIA标签 -->
<div role="progressbar" aria-valuenow="60" aria-valuemin="0" aria-valuemax="60">
  进度：60%
</div>
```

#### 7.2 颜色对比
**对比度要求**
- 文本与背景对比度 ≥ 4.5:1
- 大文本与背景对比度 ≥ 3:1
- 交互元素有明确的视觉反馈

## 验收标准

### 设计一致性验收
- [x] 颜色使用符合设计系统
- [x] 字体规范统一
- [x] 间距系统一致
- [x] 图标风格统一

### 可用性验收
- [x] 核心任务3步内完成
- [x] 新用户30分钟掌握
- [x] 错误率 < 5%
- [x] 任务完成率 > 90%

### 响应式验收
- [x] 移动端适配完美
- [x] 平板端显示正常
- [x] 桌面端体验优秀
- [x] 不同屏幕尺寸适配良好

### 无障碍验收
- [x] 键盘导航完整
- [x] 屏幕阅读器兼容
- [x] 颜色对比度达标
- [x] 文字可调整大小

---

**验收结论**：界面设计规约确保产品具有优秀的用户体验，降低学习成本，提升工作效率。
