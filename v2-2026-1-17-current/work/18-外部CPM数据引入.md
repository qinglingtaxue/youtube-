# TD-18: 外部CPM数据引入 / External CPM Data Integration

> YouTube 各国广告收益数据的引入与应用
> Integration and application of YouTube advertising revenue data by country

---

## 决策概要 / Decision Summary

| 属性 / Attribute | 值 / Value |
|------------------|------------|
| 决策编号 / ID | TD-18 |
| 决策类型 / Type | 数据源决策 / Data Source Decision |
| 决策日期 / Date | 2026-01-24 |
| 来源 | 模式洞察文档拆分过程中补充 |
| 状态 / Status | 已执行 / Implemented |

---

## 决策背景 / Decision Background

### 问题识别

1. 模式24需要计算「国家×内容」的收益潜力
2. CPM（每千次展示成本）是关键变量
3. YouTube 不公开 CPM 数据，需要从外部来源获取

### 触发因素

- 发现美国市场均播高，但收益如何？
- 需要量化「进入美国市场」vs「进入日本市场」的收益差异

---

## 决策内容 / Decision Content

### 数据来源选择

| 来源 | URL | 数据时效 | 可信度 | 采用 |
|------|-----|----------|--------|------|
| isthischannelmonetized.com | [链接](https://isthischannelmonetized.com/data/youtube-cpm/) | 2025 | 高 | ✅ |
| awisee.com | [链接](https://awisee.com/blog/cpm-rates-by-country/) | 2025 | 高 | ✅ |
| lenostube.com | [链接](https://www.lenostube.com/en/youtube-cpm-rpm-rates/) | 2025 | 中 | ✅ |
| milx.app | [链接](https://milx.app/en/trends/which-countries-have-the-best-youtube-cpm-rates-in-2025) | 2025 | 中 | ✅ |
| telepromptero.com | [链接](https://telepromptero.com/blog/youtube-rpm/) | 2025 | 中 | ✅ |

### 选择标准

1. **时效性**：优先选择 2025 年数据
2. **交叉验证**：多源数据对比，取中位值
3. **覆盖范围**：需覆盖目标市场（美国/日本/台湾/香港/新加坡）

### CPM 数据汇总（2025）

| 国家 | CPM(美元) | 相对全球平均 | 数据来源 |
|------|-----------|--------------|----------|
| 🥇 挪威 | $43.15 | 14.4x | isthischannelmonetized |
| 🥈 澳大利亚 | $36.21 | 12.1x | isthischannelmonetized |
| 🥉 美国 | $12-14 | 4x | 多源交叉验证 |
| 4 新加坡 | $17.75 | 5.9x | awisee |
| 5 香港 | $17.23 | 5.7x | awisee |
| 6 英国 | $6.43 | 2.1x | lenostube |
| 7 日本 | $5.68 | 1.9x | lenostube |
| 8 德国 | $5.53 | 1.8x | lenostube |
| 9 台湾 | $3-4 | 1.2x | 多源估算 |
| 10 印度 | $0.74 | 0.25x | 多源交叉验证 |

**全球平均**: $2.80-3.50

---

## 数据验证 / Data Validation

### 交叉验证方法

1. 对同一国家，收集 3+ 来源的数据
2. 剔除明显异常值（>3σ）
3. 取剩余值的中位数

### 验证结果

| 国家 | 来源1 | 来源2 | 来源3 | 采用值 |
|------|-------|-------|-------|--------|
| 美国 | $12 | $14 | $13 | **$12-14** |
| 日本 | $5.68 | $5.5 | $6.0 | **$5.68** |
| 台湾 | $3.5 | $3.0 | $4.0 | **$3-4** |

### 数据局限性

1. **平均值偏差**：不同内容类别 CPM 差异大（科技>娱乐>养生）
2. **时间波动**：CPM 受季节、广告主预算影响
3. **算法变化**：YouTube 可能调整分成比例

---

## 应用公式 / Application Formula

### 收益估算公式

```
预估收益(美元) = 播放量 × (CPM / 1000)

示例：
- 10万播放 @ 美国市场：100,000 × ($12/1000) = $1,200
- 10万播放 @ 台湾市场：100,000 × ($3.5/1000) = $350
```

### 综合收益潜力公式

```
收益潜力 = 预期播放量 × CPM × 爆款率 / 竞争度

示例（太极@美国）：
= 2,170,000 × $12 × 0.40 / 20
= $520,800 / 20
= $26,040 (调整后收益潜力指数)
```

---

## 使用场景 / When to Use

### 应该查阅本文档的时机

| 场景 | 原因 |
|------|------|
| 决定目标市场 | 对比各市场 CPM |
| 估算视频收益 | 使用公式计算 |
| 制定内容策略 | 平衡播放量和 CPM |
| 评估跨境价值 | 结合 TD-17 套利公式 |

### 更新频率

- **年度更新**：每年初更新 CPM 数据
- **事件触发**：YouTube 政策变化时更新

---

## 与其他决策的关系 / Related Decisions

| 决策 | 关系 |
|------|------|
| [TD-17](./17-跨语言套利空间计算方法.md) | TD-18 提供 CPM，TD-17 计算套利 |
| [模式洞察-空间维度](./模式洞察-空间维度.md) | 使用本文档的 CPM 数据 |

---

## 行动建议（基于CPM分析）

### 🔴 高优先级市场

| 市场 | CPM | 理由 |
|------|-----|------|
| 美国 | $12-14 | 规模最大 + CPM 较高 |
| 澳大利亚 | $36.21 | CPM 极高，华人移民市场 |
| 新加坡 | $17.75 | 华人高收入市场 |

### 🟡 中优先级市场

| 市场 | CPM | 理由 |
|------|-----|------|
| 香港 | $17.23 | 粤语市场，CPM 不错 |
| 日本 | $5.68 | 稳定市场，需本地化 |

### ⚪ 低优先级市场

| 市场 | CPM | 理由 |
|------|-----|------|
| 台湾 | $3-4 | 中文主市场，但 CPM 低 |
| 印度 | $0.74 | 量大但收益极低 |

---

## 决策状态 / Decision Status

| 属性 | 值 |
|------|-----|
| 状态 | 已执行 |
| 决策日期 | 2026-01-24 |
| 应用位置 | 模式洞察-空间维度.md 模式24 |
| 数据更新频率 | 年度 |
| 负责人 | - |

---

## 数据来源完整列表

1. [YouTube CPM in 2025 Full Data Analysis - isthischannelmonetized](https://isthischannelmonetized.com/data/youtube-cpm/)
2. [CPM Rates by Country 2025 - awisee](https://awisee.com/blog/cpm-rates-by-country/)
3. [YouTube CPM & RPM Rates 2025 - Lenos](https://www.lenostube.com/en/youtube-cpm-rpm-rates/)
4. [Top YouTube CPM Countries 2025 - MilX](https://milx.app/en/trends/which-countries-have-the-best-youtube-cpm-rates-in-2025)
5. [YouTube RPM Rates by Category and Country - Telepromptero](https://telepromptero.com/blog/youtube-rpm/)

---

*最后更新 / Last Updated: 2026-01-24*
