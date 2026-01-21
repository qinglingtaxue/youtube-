# research-report

生成调研报告交互页面 - 用于展示竞品调研数据和市场分析结果。

## 触发条件

- 用户要生成调研报告
- 用户要查看竞品分析结果
- 完成数据采集后需要可视化展示
- 用户要求生成 HTML 报告

## 输入

- 竞品视频数据库 (`data/videos.db`)
- 采集主题关键词
- 时间范围筛选条件（可选）
- 报告类型：research（调研报告）/ comprehensive（综合报告）

---

## ⚠️ 核心约束（基于踩坑经验）

### 1. 真实数据强制要求

```yaml
data_policy:
  rule: 禁止使用模拟数据作为最终展示
  fallback: 没有真实数据时显示 0 或空白，不要回退到模拟数据
  validation: 报告生成前必须验证数据来源
```

### 2. 链接验证检查

```yaml
link_validation:
  required: true
  check_items:
    - 视频链接必须包含完整 URL（https://youtube.com/watch?v=xxx）
    - 频道链接必须可点击跳转
    - 生成后抽样验证 10 条链接的可访问性
  on_failure: 标记为「链接待验证」，不要使用占位符
```

### 3. 数据来源标注

```yaml
data_source_label:
  display: true
  format: "数据来源：{source} | 更新时间：{timestamp}"
  source_types:
    - local_db: 本地数据库（缓存）
    - live_api: YouTube 实时 API
    - mixed: 混合来源
```

---

## 📊 指标计算公式（必须遵守）

```yaml
metrics:
  爆款指标:
    formula: 播放量 / max(发布天数, 1)
    unit: 播放量/天
    description: 日均播放量，发布天数至少为1避免除零

  潜力指标:
    formula: (点赞数 + 评论数) / max(播放量, 1) * 1000
    unit: 千次播放互动数
    description: 互动率，衡量观众参与度

  热门指标:
    formula: 近7天播放增量
    unit: 播放量
    description: 短期增长势头

  长青指标:
    formula: 总播放量 / max(发布月数, 1)
    unit: 播放量/月
    description: 月均播放量，衡量长期价值

  黑马指标:
    formula: 近30天新增订阅 / max(原订阅数, 100) * 100
    unit: 百分比
    description: 订阅增长率，原订阅数至少100避免极端值

note: 不同指标必须产生不同排序结果，如果排序相同说明计算逻辑有问题
```

## 报告架构

```yaml
report:
  name: research_report
  type: HTML 单文件应用
  framework: vanilla JS + Chart.js

  layout:
    header:
      - 标题
      - 主题信息
      - 样本量统计
      - 时间范围选择器（1天内/15天内/30天内/全部）
      - 生成时间

    tabs:
      - name: 数据概览
        id: overview
        components:
          - 关键指标卡片（6个）
          - 数据覆盖情况
          - 关键发现列表

      - name: 视频列表
        id: videos
        components:
          - 搜索过滤器
          - 排序选项（播放量/日增/发布时间）
          - 分页表格
          - 视频预览弹窗

      - name: 频道分析
        id: channels
        components:
          - 头部频道排行
          - 频道规模分布饼图
          - 频道集中度分析

      - name: 内容模式
        id: patterns
        components:
          - 标题模式词云
          - 时长分布直方图
          - 关键词频率图
          - 典型案例展示

  interactions:
    - 全局时间过滤器
    - 表格排序和筛选
    - 图表交互（点击钻取）
    - 视频链接跳转
    - 数据导出（CSV）
```

## 模块规约

```yaml
module:
  name: research_report
  path: src/research/
  file: research_report.py
  class: ResearchReportGenerator

  methods:
    - name: generate
      input:
        - theme: str（调研主题）
        - time_window: str（时间窗口，默认"全部"）
        - output_path: str（可选，输出路径）
      output: str（生成的报告路径）

    - name: _load_videos
      description: 从数据库加载视频数据
      output: List[Dict]

    - name: _calculate_stats
      description: 计算统计指标
      output: Dict

    - name: _analyze_channels
      description: 分析频道数据
      output: Dict

    - name: _extract_patterns
      description: 提取内容模式
      output: Dict

    - name: _render_html
      description: 渲染 HTML 模板
      output: str

  dependencies:
    internal:
      - src.research.data_collector.DataCollector
      - src.analysis.pattern_analyzer.PatternAnalyzer
    external:
      - sqlite3
      - json
      - datetime
```

## API 接口

```yaml
cli:
  command: ytp research report
  usage: ytp research report [options]

  options:
    - name: --theme
      type: string
      default: "老人养生"
      description: 调研主题

    - name: --time-window
      type: string
      enum: [1天内, 15天内, 30天内, 全部]
      default: 全部
      description: 时间范围过滤

    - name: --output
      short: -o
      type: string
      description: 输出文件路径

    - name: --open
      type: boolean
      default: true
      description: 生成后自动打开

  example: |
    ytp research report --theme "老人养生" --time-window 30天内
    ytp research report -o reports/research_report.html
```

## 数据结构

```yaml
report_data:
  meta:
    theme: string
    generated_at: datetime
    sample_size: int
    time_window: string

  overview:
    total_videos: int
    total_views: int
    avg_views: int
    median_views: int
    total_channels: int
    date_coverage: float

  videos:
    - video_id: string
      title: string
      channel: string
      url: string
      views: int
      likes: int
      comments: int
      duration: int
      published_at: datetime
      daily_growth: int
      time_bucket: string

  channels:
    - name: string
      video_count: int
      total_views: int
      avg_views: int

  patterns:
    title_keywords: Dict[str, int]
    duration_distribution: List[Dict]
    category_distribution: Dict[str, int]
```

## 交互设计

```yaml
interactions:
  # 全局时间过滤
  time_filter:
    type: button_group
    position: header
    options: [1天内, 15天内, 30天内, 全部]
    on_change:
      - 更新所有统计数据
      - 重绘所有图表
      - 过滤视频列表
      - 显示时间范围指示器

  # 视频列表
  video_table:
    features:
      - 列排序（点击表头）
      - 搜索过滤（标题/频道）
      - 分页（每页20条）
      - 行点击（打开视频链接）

  # 图表交互
  charts:
    - 饼图点击：过滤到该分类
    - 柱状图悬停：显示详细数据
    - 折线图缩放：时间范围调整

  # 数据导出
  export:
    formats: [CSV, JSON]
    content:
      - 当前筛选的视频列表
      - 统计摘要
```

## 输出

- 报告文件：`data/reports/research_report_{theme}_{date}.html`
- 部署目录：`public/research.html`（用于 Vercel 部署）

## 与综合报告的区别

| 特性 | 调研报告 (research) | 综合报告 (comprehensive) |
|------|---------------------|-------------------------|
| 重点 | 视频列表和搜索 | 市场分析和机会识别 |
| 主要用户 | 调研阶段的创作者 | 策划阶段的决策者 |
| 核心功能 | 浏览/筛选/导出视频 | 图表可视化/机会发现 |
| 数据深度 | 单个视频详情 | 聚合统计和趋势 |
| 交互重点 | 表格操作 | 图表交互 |

## 使用示例

```python
# Python API
from src.research.research_report import ResearchReportGenerator

generator = ResearchReportGenerator()
path = generator.generate(
    theme="老人养生",
    time_window="30天内",
    output_path="data/reports/research_report.html"
)
print(f"报告已生成: {path}")

# CLI
# ytp research report --theme "老人养生" --time-window 30天内
```

---

## 📋 生成后检查清单（必须执行）

```yaml
post_generation_checks:
  - name: 链接可访问性
    action: 随机抽取 10 条视频/频道链接，验证是否可点击跳转
    pass_criteria: 90% 以上链接可访问
    on_failure: 标记失效链接，提示用户

  - name: 排序差异验证
    action: 检查「爆款榜」「潜力榜」「热门榜」的 Top10 是否有差异
    pass_criteria: 至少 50% 的视频不重复
    on_failure: 排查计算逻辑是否写错

  - name: 时间范围验证
    action: 抽样 10 条数据，检查发布时间是否在指定范围内
    pass_criteria: 100% 在范围内
    on_failure: 检查时间过滤参数是否生效

  - name: 数据完整性
    action: 检查关键字段（标题、播放量、频道）是否有空值
    pass_criteria: 空值率 < 5%
    on_failure: 重新采集缺失数据
```

---

## ⏱️ 进度反馈机制

```yaml
progress_feedback:
  enabled: true
  stages:
    - name: 加载数据
      weight: 10%
      display: "正在从数据库加载视频数据..."

    - name: 计算指标
      weight: 30%
      display: "正在计算 {current}/{total} 个视频的指标..."

    - name: 生成图表
      weight: 40%
      display: "正在生成 {chart_name} 图表..."

    - name: 渲染报告
      weight: 20%
      display: "正在渲染 HTML 报告..."

  estimated_time:
    - sample_size: 100
      time: "约 10 秒"
    - sample_size: 500
      time: "约 30 秒"
    - sample_size: 1000
      time: "约 1 分钟"
```
