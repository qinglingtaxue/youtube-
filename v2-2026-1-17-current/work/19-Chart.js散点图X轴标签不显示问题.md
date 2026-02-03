# Chart.js 散点图 X 轴标签不显示问题

> **问题日期**: 2026-01-25
>
> **场景**: "领域概览"视频分布气泡图，X轴应显示时间（日/周/月），实际为空白

---

## 一、问题现象

气泡图（bubble chart）的 X 轴完全空白，不显示任何时间标签。

## 二、原始代码（失败）

```javascript
// 数据点使用数字索引
points.push({
    x: idx,  // 0, 1, 2, 3...
    y: topicData.views,
    ...
});

// X 轴配置
scales: {
    x: {
        type: 'linear',
        min: -0.5,
        max: timePoints.length - 0.5,
        ticks: {
            callback: function(value) {
                if (!Number.isInteger(value)) return '';
                return timeLabels[value] || '';  // 通过索引查标签
            }
        }
    }
}
```

### 失败原因

1. **`linear` 类型轴的 callback 行为不可靠**：Chart.js 的 linear 轴主要用于连续数值，callback 的调用时机和参数不一定符合预期
2. **闭包变量可能无法正确访问**：`timeLabels` 在 callback 执行时可能已经超出作用域
3. **本质问题**：用数值轴模拟分类轴是反模式

## 三、解决方案

改用 `category` 类型轴 + 字符串 x 值：

```javascript
// 预先生成标签数组
const chartTimeLabels = [...timeLabels];  // ['26/01', '25/12', '25/11', ...]

// 数据点使用字符串标签
points.push({
    x: formatLabel(t),  // '26/01', '25/12'... 与 labels 匹配
    y: topicData.views,
    ...
});

// X 轴配置
scales: {
    x: {
        type: 'category',
        labels: chartTimeLabels,  // 直接提供标签数组
        ticks: {
            color: '#64748b',
            autoSkip: true,
            maxTicksLimit: 12,
            maxRotation: 45
        }
    }
}
```

## 四、关键改动对比

| 项目 | 原方案 | 新方案 |
|------|--------|--------|
| X轴类型 | `linear` | `category` |
| 数据点 x 值 | 数字索引 `idx` | 字符串标签 `formatLabel(t)` |
| 标签显示方式 | `callback` 转换 | `labels` 数组直接指定 |
| 可靠性 | ❌ 不显示 | ✅ 正常显示 |

## 五、核心原理

Chart.js 的轴类型决定了数据解析方式：

- **`linear`**：连续数值轴，适合 `x: 100, 200, 300`
- **`category`**：分类轴，适合 `x: '1月', '2月', '3月'`
- **`time`**：时间轴，适合 `x: '2026-01-15'`（需额外配置）

对于气泡图按时间分组的场景，`category` 是最简单可靠的选择：
1. 不需要日期解析库（如 date-fns）
2. 不需要 callback 转换
3. 数据点 x 值直接对应标签文字

## 六、经验总结

| 场景 | 推荐方案 |
|------|----------|
| X轴是离散分类（日/周/月） | `type: 'category'` + `labels` 数组 |
| X轴是连续数值 | `type: 'linear'` |
| X轴是精确时间戳 | `type: 'time'` + adapter |

**避免**：用 `linear` 轴 + `callback` 模拟分类轴，行为不可预测。

---

## 文档更新日志

| 日期 | 内容 |
|------|------|
| 2026-01-25 | 初始记录 |
