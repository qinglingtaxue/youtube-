# visualization

可视化设计规约 - 确保图表和 UI 正确显示。

## 触发条件

- 生成可视化图表时
- 设计洞察系统 UI 时
- 创建数据报告页面时

---

## ⚠️ 核心约束（基于踩坑经验）

### 1. 布局防溢出规约

```yaml
layout_constraints:
  description: 防止图表和内容溢出容器

  rules:
    - name: 容器边界
      rule: 所有可视化组件必须设置 max-width 和 max-height
      css: |
        .chart-container {
          max-width: 100%;
          max-height: 500px;
          overflow: auto;
        }

    - name: 响应式设计
      rule: 图表必须支持容器宽度变化
      implementation: 使用百分比宽度或 resize observer

    - name: 文本截断
      rule: 长文本必须有截断策略
      css: |
        .label-text {
          max-width: 150px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

    - name: 气泡图边界
      rule: 气泡不能超出绘图区域
      implementation: |
        // 确保气泡在边界内
        const clampedX = Math.max(radius, Math.min(width - radius, x));
        const clampedY = Math.max(radius, Math.min(height - radius, y));

  extreme_data_tests:
    - 数据量为 0 时：显示「暂无数据」占位符
    - 数据量 > 1000 时：启用虚拟滚动或分页
    - 单条数据值极大时：使用对数刻度或截断显示
    - 文本超长时：截断 + tooltip 显示完整内容
```

### 2. 图表类型规范

```yaml
chart_specifications:

  气泡图:
    use_case: 展示三维数据关系（x, y, 大小）
    constraints:
      - 最大气泡数量：100（超过则聚合或分页）
      - 气泡最小半径：10px（确保可点击）
      - 气泡最大半径：50px（防止遮挡）
      - 必须有图例说明气泡代表什么
      - 必须有 tooltip 显示详细信息

    anti_patterns:
      - ❌ 气泡重叠严重无法分辨
      - ❌ 文字标签被遮挡
      - ❌ 气泡超出容器边界

    implementation: |
      // 防止气泡重叠的力导向布局
      const simulation = d3.forceSimulation(data)
        .force('x', d3.forceX(d => xScale(d.x)).strength(0.5))
        .force('y', d3.forceY(d => yScale(d.y)).strength(0.5))
        .force('collide', d3.forceCollide(d => radiusScale(d.value) + 2));

  热力图:
    use_case: 展示二维数据密度分布
    constraints:
      - 单元格最小尺寸：20x20px
      - 必须有颜色图例
      - 颜色对比度满足 WCAG AA 标准

  柱状图:
    use_case: 比较不同类别的数值
    constraints:
      - 最大柱子数量：20（超过则显示 Top N + 其他）
      - 柱子最小宽度：20px
      - 必须有 y 轴标签和刻度

  折线图:
    use_case: 展示趋势变化
    constraints:
      - 数据点过多时自动采样
      - 必须有 x 轴时间刻度
      - 支持缩放和平移

  饼图:
    use_case: 展示占比关系
    constraints:
      - 最大分片数量：7（超过则合并为「其他」）
      - 每个分片必须有标签或图例
      - 小于 5% 的分片合并或特殊处理
```

### 3. 交互设计规范

```yaml
interaction_design:

  tooltip:
    description: 鼠标悬停显示详细信息
    constraints:
      - 显示延迟：200ms
      - 消失延迟：100ms
      - 位置：自动避免超出视口
      - 内容：关键指标 + 可点击链接

  click_action:
    description: 点击图表元素的行为
    constraints:
      - 点击气泡/柱子：显示详情面板或跳转
      - 点击图例：切换显示/隐藏
      - 点击背景：清除选中状态

  drill_down:
    description: 从汇总到详情的下钻
    constraints:
      - 必须有「返回」按钮
      - 层级不超过 3 层
      - 每层都有面包屑导航
```

### 4. 数据展示规范

```yaml
data_display:

  空数据处理:
    rule: 数据为空时必须有友好提示
    implementation: |
      {data.length === 0 ? (
        <div class="empty-state">
          <icon>📊</icon>
          <p>暂无数据</p>
          <p class="hint">请先采集数据或调整筛选条件</p>
        </div>
      ) : (
        <Chart data={data} />
      )}

  加载状态:
    rule: 数据加载时必须有加载指示器
    implementation: |
      {loading ? (
        <div class="loading">
          <spinner />
          <p>正在加载数据...</p>
        </div>
      ) : null}

  错误状态:
    rule: 加载失败时必须有错误提示和重试按钮
    implementation: |
      {error ? (
        <div class="error-state">
          <icon>⚠️</icon>
          <p>加载失败：{error.message}</p>
          <button onClick={retry}>重试</button>
        </div>
      ) : null}

  数据来源标注:
    rule: 必须显示数据来源和更新时间
    format: "数据来源：{source} | 更新时间：{timestamp}"
```

### 5. 洞察系统设计

```yaml
insight_system:
  description: 从数据中提取洞察并可视化展示

  structure:
    - level: 结论
      display: 卡片标题
      example: "5-20分钟视频表现最佳"

    - level: 证据
      display: 展开查看
      components:
        - 支撑数据表格
        - 可视化图表
        - 推理链说明

    - level: 行动建议
      display: 底部按钮
      example: "查看 Top10 视频详情"

  interaction:
    - 点击卡片：展开/折叠详情
    - 点击「查看数据」：显示原始数据表格
    - 点击链接：跳转到视频/频道页面

  anti_patterns:
    - ❌ 只有结论没有证据
    - ❌ 数据表格没有链接
    - ❌ 图表没有图例说明
```

---

## 📋 开发前检查清单

```yaml
pre_development_checklist:
  - [ ] 确定图表类型
  - [ ] 确定数据结构
  - [ ] 设计空数据/加载/错误状态
  - [ ] 设计交互行为（hover/click/drill-down）
  - [ ] 确定响应式断点
  - [ ] 准备极端数据测试用例
```

---

## 📋 开发后测试清单

```yaml
post_development_checklist:
  - name: 空数据测试
    action: 传入空数组，检查是否显示「暂无数据」
    pass_criteria: 有友好提示，无报错

  - name: 极端数据测试
    action: 传入 1000+ 条数据，检查性能和布局
    pass_criteria: 无溢出，响应时间 < 1秒

  - name: 长文本测试
    action: 传入超长标题/频道名，检查截断
    pass_criteria: 文本截断，hover 显示完整内容

  - name: 链接验证
    action: 点击所有可点击元素
    pass_criteria: 链接正确跳转

  - name: 响应式测试
    action: 调整窗口宽度 320px ~ 1920px
    pass_criteria: 布局不崩溃，内容可读

  - name: 图例验证
    action: 检查所有图表是否有图例
    pass_criteria: 用户能理解图表含义
```

---

## 📊 常用图表库推荐

```yaml
chart_libraries:
  - name: Chart.js
    use_case: 简单图表（柱状图、折线图、饼图）
    pros: 轻量、易用
    cons: 复杂交互支持有限

  - name: ECharts
    use_case: 复杂图表、地图、大数据量
    pros: 功能丰富、性能好
    cons: 体积较大

  - name: D3.js
    use_case: 自定义可视化、力导向图
    pros: 灵活度高
    cons: 学习曲线陡峭

  recommendation: |
    - 简单报告：Chart.js
    - 复杂分析页面：ECharts
    - 自定义可视化：D3.js
```

---

## 输出

- 图表组件：`src/components/charts/`
- 样式文件：`src/styles/charts.css`
- 测试用例：`tests/charts/`
