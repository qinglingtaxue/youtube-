# data-validator

数据验证 - 确保数据质量和完整性。

## 触发条件

- 数据采集完成后
- 报告生成前
- 用户质疑数据真实性时
- 定期数据质量检查

---

## ⚠️ 核心约束（基于踩坑经验）

### 1. 链接可访问性验证

```yaml
link_validation:
  description: 验证所有链接是否可点击跳转

  check_types:
    - name: 视频链接
      pattern: "^https://youtube\\.com/watch\\?v=[a-zA-Z0-9_-]{11}$"
      sample_size: 10  # 抽样验证数量
      method: HEAD 请求或 yt-dlp --dump-json

    - name: 频道链接
      pattern: "^https://youtube\\.com/(channel/|@)[a-zA-Z0-9_-]+$"
      sample_size: 10
      method: HEAD 请求

  on_invalid:
    action: 标记为「链接失效」
    log_file: "logs/invalid_links.json"

  report_format: |
    🔗 链接验证报告
    - 视频链接有效率：{video_rate}% ({valid_videos}/{total_videos})
    - 频道链接有效率：{channel_rate}% ({valid_channels}/{total_channels})
    - 失效链接详见：logs/invalid_links.json
```

### 2. 数据真实性验证

```yaml
authenticity_check:
  description: 验证数据是否为真实数据而非模拟数据

  indicators:
    - name: video_id 格式
      valid_pattern: "^[a-zA-Z0-9_-]{11}$"
      invalid_examples: ["test123", "sample", "xxx"]

    - name: 播放量合理性
      range: [0, 10000000000]  # 100亿以内
      suspicious: [0, 123456, 1000000]  # 整数可能是模拟数据

    - name: 发布日期合理性
      range: ["2005-04-23", "today"]  # YouTube 成立日期至今
      suspicious: ["2000-01-01", "1970-01-01"]  # 明显错误的日期

    - name: 频道名称
      invalid_patterns: ["测试频道", "Test Channel", "Sample"]

  on_suspicious:
    action: 标记为「数据待验证」
    require_manual_check: true
```

### 3. 时间范围验证

```yaml
time_range_validation:
  description: 验证数据是否在用户指定的时间范围内

  method: |
    1. 读取采集时指定的时间范围参数
    2. 抽样检查 10 条数据的 upload_date
    3. 计算在范围内的比例

  pass_criteria: 100%  # 必须全部在范围内
  on_failure:
    action: 提示时间过滤可能失效
    suggestion: 检查 YouTube sp 参数是否正确使用

  report_format: |
    📅 时间范围验证
    - 指定范围：{start_date} ~ {end_date}
    - 抽样数量：{sample_size}
    - 在范围内：{in_range_count} ({rate}%)
    - 超出范围的数据：{out_of_range_list}
```

### 4. 数据完整性验证

```yaml
completeness_check:
  description: 检查必填字段是否完整

  required_fields:
    video:
      - id: "视频ID"
      - title: "标题"
      - view_count: "播放量"
      - upload_date: "发布日期"
      - channel: "频道名"
      - channel_id: "频道ID"

    channel:
      - id: "频道ID"
      - name: "频道名"
      - subscriber_count: "订阅数"
      - video_count: "视频数"

  optional_fields:
    video:
      - like_count: "点赞数"
      - comment_count: "评论数"
      - description: "描述"
      - tags: "标签"

  report_format: |
    📊 数据完整性报告

    必填字段完整率：
    {required_fields_report}

    可选字段覆盖率：
    {optional_fields_report}

    缺失详情：logs/missing_fields.json
```

### 5. 计算逻辑验证

```yaml
calculation_validation:
  description: 验证指标计算结果是否合理

  checks:
    - name: 排序差异检查
      action: 比较「爆款榜」「潜力榜」「热门榜」的 Top10
      pass_criteria: 至少 50% 的视频不重复
      on_failure: 计算逻辑可能相同，需检查公式

    - name: 数值范围检查
      metrics:
        - name: 日均播放量
          range: [0, 10000000]  # 1000万以内合理
        - name: 互动率
          range: [0, 100]  # 百分比
      on_out_of_range: 标记为异常值

    - name: 排序顺序检查
      action: 验证榜单是否按指定指标降序排列
      pass_criteria: 100% 正确排序
```

---

## 📋 验证流程

```yaml
validation_flow:
  - step: 1
    name: 格式验证
    actions:
      - 检查 video_id 格式
      - 检查 URL 格式
      - 检查日期格式

  - step: 2
    name: 完整性验证
    actions:
      - 检查必填字段
      - 统计缺失率
      - 生成缺失报告

  - step: 3
    name: 真实性验证
    actions:
      - 抽样验证链接可访问性
      - 检查数值合理性
      - 标记可疑数据

  - step: 4
    name: 时间范围验证
    actions:
      - 抽样检查发布日期
      - 计算范围内比例

  - step: 5
    name: 计算验证
    actions:
      - 检查排序差异
      - 检查数值范围
      - 验证排序顺序

  - step: 6
    name: 生成报告
    actions:
      - 汇总所有验证结果
      - 生成综合验证报告
      - 标记需要人工检查的项
```

---

## 📊 命令模板

```bash
# 验证视频链接（使用 yt-dlp 快速检查）
yt-dlp --dump-json "https://youtube.com/watch?v={video_id}" \
  --no-download \
  --skip-download \
  2>/dev/null && echo "VALID" || echo "INVALID"

# 批量验证（Python 脚本）
python -c "
from src.shared.validators import DataValidator
validator = DataValidator()
report = validator.validate_all('data/videos.db')
print(report.summary())
"
```

---

## 📋 验证报告模板

```yaml
validation_report:
  summary:
    total_records: int
    valid_records: int
    invalid_records: int
    overall_quality_score: float  # 0-100

  details:
    link_validation:
      video_link_valid_rate: float
      channel_link_valid_rate: float
      invalid_links: list

    completeness:
      required_field_rate: float
      optional_field_rate: float
      missing_fields: dict

    authenticity:
      suspicious_records: list
      reason: str

    time_range:
      in_range_rate: float
      out_of_range_records: list

    calculation:
      ranking_diversity: float
      value_anomalies: list

  recommendations:
    - action: str
      priority: high/medium/low
      affected_records: int
```

---

## 输出

- 验证报告：`logs/validation_report_{date}.json`
- 失效链接：`logs/invalid_links.json`
- 缺失字段：`logs/missing_fields.json`
- 可疑数据：`logs/suspicious_records.json`
