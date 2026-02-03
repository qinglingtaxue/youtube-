# 模块组合规范

> 让独立的高品味模块能自由组合，产生涌现效应。

## 1. 全局唯一编码体系

### 1.1 Skill 编码

| 编码 | Skill | 职责 |
|------|-------|------|
| SK-01 | data-collector | 数据采集 |
| SK-02 | data-validator | 数据验证 |
| SK-03 | visualization | 可视化图表 |
| SK-04 | research-report | 调研报告 |
| SK-05 | youtube-downloader | 视频下载 |
| SK-06 | youtube-transcript | 字幕提取 |
| SK-07 | youtube-to-markdown | 元数据转 MD |
| SK-08 | article-extractor | 网页提取 |
| SK-09 | content-creator | 内容创作 |
| SK-10 | ideation | 创意构思 |
| SK-11 | spec-generator | 规约生成 |
| SK-12 | transcript-fixer | 字幕修复 |
| SK-13 | media-processing | 音视频处理 |

### 1.2 模式编码

| 编码 | 维度 | 说明 |
|------|------|------|
| PT-VAR-xx | 变量分布 | 标题长度、视频时长等 |
| PT-TMP-xx | 时间维度 | 发布时机、周期规律 |
| PT-SPA-xx | 空间维度 | 跨语言、地区分布 |
| PT-CHA-xx | 频道维度 | 黑马频道、增长案例 |
| PT-USR-xx | 用户维度 | 评论热词、情感分析 |

### 1.3 知识单元类型编码

| 编码 | 类型 | 说明 | 产出自 |
|------|------|------|--------|
| KU-VIDEO | 视频单元 | 包含 youtube_id, title, view_count 等 | SK-01 |
| KU-CHANNEL | 频道单元 | 包含 channel_id, subscriber_count 等 | SK-01 |
| KU-PATTERN | 模式单元 | 包含 pattern_id, confidence, finding 等 | 分析脚本 |
| KU-INSIGHT | 洞察单元 | 包含 insight_id, title, sources 等 | SK-04 |
| KU-TRANSCRIPT | 字幕单元 | 包含 video_id, segments, text 等 | SK-06 |
| KU-ARTICLE | 文章单元 | 包含 url, title, content 等 | SK-08 |

### 1.4 文档编码

| 编码 | 类型 | 说明 |
|------|------|------|
| TD-xx | 技术决策 | work/01-xxx.md ~ work/20-xxx.md |
| SP-xxx | 规约 | .42cog/spec/dev/*.spec.md |
| EXP-xx | 经验 | 踩坑经验索引 |

---

## 2. 模块组合矩阵

### 2.1 典型任务的模块组合

```yaml
task_compositions:

  # 任务：采集 + 验证 + 分析
  full_research:
    id: TC-01
    name: 完整调研流程
    skills:
      - SK-01  # data-collector（必选）
      - SK-02  # data-validator（必选）
      - SK-03  # visualization（可选）
      - SK-04  # research-report（可选）
    sequence: SK-01 → SK-02 → SK-03 → SK-04
    dependency: |
      SK-02 依赖 SK-01 的输出
      SK-03 依赖 SK-02 通过后的数据
      SK-04 依赖 SK-03 的图表

  # 任务：快速采集
  quick_collect:
    id: TC-02
    name: 快速采集（不验证）
    skills:
      - SK-01  # data-collector
    use_case: 探索性采集，后续再验证

  # 任务：内容创作
  content_creation:
    id: TC-03
    name: 内容创作流程
    skills:
      - SK-10  # ideation（先构思）
      - SK-11  # spec-generator（生成规约）
      - SK-09  # content-creator（创作内容）
    sequence: SK-10 → SK-11 → SK-09

  # 任务：视频处理
  video_processing:
    id: TC-04
    name: 视频处理流程
    skills:
      - SK-05  # youtube-downloader
      - SK-06  # youtube-transcript
      - SK-12  # transcript-fixer（可选）
      - SK-13  # media-processing（可选）
    sequence: SK-05 → SK-06 → SK-12 → SK-13
```

### 2.2 模块兼容性矩阵

```
        SK-01  SK-02  SK-03  SK-04  SK-05  SK-06
SK-01     -      →      →      →      ○      ○
SK-02     ×      -      →      →      ○      ○
SK-03     ×      ×      -      →      ○      ○
SK-04     ×      ×      ×      -      ○      ○
SK-05     ○      ○      ○      ○      -      →
SK-06     ○      ○      ○      ○      ×      -

图例：
  → : 前者输出是后者输入
  × : 不兼容/无关
  ○ : 可并行，无依赖
```

---

## 3. 分组与优先级

### 3.1 任务优先级标记

```yaml
priority_levels:
  P0_critical:
    description: 阻塞其他任务，必须立即处理
    examples:
      - 数据库连接失败
      - 采集 API 被封
    response_time: < 1 小时

  P1_high:
    description: 影响核心功能，当天处理
    examples:
      - 数据验证失败率 > 30%
      - 图表显示异常
    response_time: < 8 小时

  P2_medium:
    description: 影响用户体验，本周处理
    examples:
      - 缺少可选字段
      - 报告格式优化
    response_time: < 1 周

  P3_low:
    description: 优化项，有空处理
    examples:
      - 代码重构
      - 文档补充
    response_time: 无限制
```

### 3.2 时间窗口分组

```yaml
time_windows:
  realtime:
    description: 需要立即响应
    data_freshness: < 1 小时
    skills: [SK-01]  # 实时采集

  daily:
    description: 每日更新
    data_freshness: < 24 小时
    skills: [SK-01, SK-02]  # 日常采集 + 验证

  weekly:
    description: 周报/周分析
    data_freshness: < 7 天
    skills: [SK-01, SK-02, SK-03, SK-04]  # 完整流程

  archive:
    description: 归档数据
    data_freshness: > 30 天
    action: 压缩存储，不再更新
```

---

## 4. 组合检查清单

### 4.1 组合前检查

```yaml
pre_composition_checks:
  - name: 输入输出匹配
    check: 前一个 skill 的输出格式是否匹配后一个的输入
    fail_action: 查看 skill 文档的"输出"和"触发条件"

  - name: 依赖完整
    check: 所有依赖的 skill 是否都在组合中
    fail_action: 补充缺失的 skill

  - name: 顺序正确
    check: 是否按依赖顺序排列
    fail_action: 参考组合矩阵调整顺序

  - name: 优先级一致
    check: 组合中的 skill 优先级是否兼容
    fail_action: 高优先级任务不应依赖低优先级 skill
```

### 4.2 组合后验证

```yaml
post_composition_checks:
  - name: 数据流通
    check: 数据是否从第一个 skill 流到最后一个
    method: 检查中间产物是否存在

  - name: 无数据丢失
    check: 输入记录数 ≈ 输出记录数（允许过滤）
    method: 比较各阶段的 count

  - name: 质量不降级
    check: 后续 skill 不应降低数据质量
    method: 比较各阶段的 quality_score
```

---

## 5. 使用示例

### 示例1：执行完整调研

```python
# 组合 TC-01：完整调研流程
from skills import (
    DataCollector,    # SK-01
    DataValidator,    # SK-02
    Visualization,    # SK-03
    ResearchReport,   # SK-04
)

# 按顺序执行
raw_data = DataCollector.run(keyword="养生", max_results=500)
validated_data = DataValidator.run(raw_data, phase="accuracy")
charts = Visualization.run(validated_data)
report = ResearchReport.run(validated_data, charts)
```

### 示例2：查找可用组合

```python
# 我有 SK-01 的输出，可以接哪些 skill？
next_skills = get_compatible_skills("SK-01", direction="downstream")
# 返回：["SK-02", "SK-03", "SK-04"]

# 我要执行 SK-04，需要先执行哪些 skill？
required_skills = get_required_skills("SK-04")
# 返回：["SK-01", "SK-02"]（必选） + ["SK-03"]（可选）
```

---

## 6. 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-01 | 初始版本，定义编码体系和组合矩阵 |
| v1.1 | 2026-02-01 | 添加知识单元类型编码（KU-xxx），skill 文件落地编码 |
