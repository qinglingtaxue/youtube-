# data-collector

YouTube 数据采集 - 核心 skill，包含大量踩坑经验。

## 触发条件

- 用户要采集 YouTube 视频数据
- 用户要搜索特定主题的视频
- 用户要获取频道信息
- 用户要批量采集数据

---

## ⚠️ 核心约束（基于踩坑经验）

### 1. 搜索逻辑规约（核心）

```yaml
search_logic:
  description: YouTube 搜索的完整参数和策略

  # ============ 时间过滤 ============
  time_filter:
    rule: 必须使用 YouTube 原生搜索过滤，不能只靠本地过滤
    reason: 本地过滤会导致搜到多年前的数据，违背用户预期

    sp_params:
      今天: "EgIIAg%3D%3D"
      本周: "EgIIAw%3D%3D"
      本月: "EgIIBA%3D%3D"
      今年: "EgIIBQ%3D%3D"

  # ============ 排序方式 ============
  sort_order:
    相关性: ""  # 默认，不需要额外参数
    上传日期: "CAI%3D"
    观看次数: "CAM%3D"
    评分: "CAE%3D"

    # 组合示例：本周 + 按播放量排序
    combined_example: "EgIIAw%3D%3D&sp=CAM%3D"

  # ============ 内容类型 ============
  content_type:
    视频: "EgIQAQ%3D%3D"
    频道: "EgIQAg%3D%3D"
    播放列表: "EgIQAw%3D%3D"
    电影: "EgIQBA%3D%3D"

  # ============ 时长过滤 ============
  duration_filter:
    短视频_4分钟以下: "EgIYAQ%3D%3D"
    中等_4到20分钟: "EgIYAw%3D%3D"
    长视频_20分钟以上: "EgIYAg%3D%3D"

  # ============ URL 构建 ============
  url_template: |
    https://www.youtube.com/results?search_query={keyword}&sp={sp_param}

  # 正确做法
  correct_usage: |
    # 搜索本周内、按播放量排序的视频
    url = f"https://www.youtube.com/results?search_query=健康养生&sp=EgIIAw%253D%253D"
    yt-dlp --flat-playlist --dump-json "{url}"

  # 错误做法
  wrong_usage: |
    # ❌ 先搜索全部再本地过滤（会搜到多年前的数据）
    yt-dlp "ytsearch100:健康养生" | filter by date

    # ❌ 不指定时间范围（结果混乱）
    yt-dlp "ytsearch100:健康养生"
```

### 2. 搜索数量限制与分批策略

```yaml
search_quantity:
  description: 处理 YouTube 单次搜索数量限制

  limitations:
    - YouTube 单次搜索最多返回约 500 个结果
    - ytsearch{N} 最多支持 N=100 左右
    - API 有频率限制

  # ============ 分批搜索策略 ============
  batch_strategy:
    rule: 用户要 1000 个视频时，拆解成多个任务

    methods:
      - name: 关键词拓展法
        description: 使用 YouTube 搜索建议获取真实用户高频词

        # ⚠️ 关键词必须来自用户行为数据，不能硬编码！

        correct_example: |
          # ✅ 正确：从 YouTube 搜索建议获取关键词
          seed = "健康"
          keywords = get_youtube_suggestions(seed)
          # 返回：["健康养生操", "健康饮食食谱", "健康减肥方法", ...]
          # 这些是真实用户在搜索框输入的高频词

          for kw in keywords[:5]:  # 取前 5 个
              search(kw, limit=200)  # 5 * 200 = 1000

        wrong_example: |
          # ❌ 错误：硬编码关键词（AI 随意设定）
          keywords = ["健康养生", "健康饮食", "健康生活"]  # 不要这样做！

        how_to_get_suggestions: |
          # 方法 1：YouTube 搜索建议 API（已验证可用）
          url = f"https://clients1.google.com/complete/search?client=youtube&gs_ri=youtube&ds=yt&q={seed}"
          # 返回 JSONP 格式，需解析：window.google.ac.h([...])

          # Python 解析示例：
          import requests, json, re
          resp = requests.get(url).text
          match = re.search(r'window\.google\.ac\.h\((\[.*\])\)', resp)
          data = json.loads(match.group(1))
          keywords = [item[0] for item in data[1]]  # 提取关键词列表

          # 方法 2：yt-dlp 获取相关视频标签
          yt-dlp --dump-json "https://youtube.com/watch?v={video_id}" | jq '.tags'

          # 方法 3：从热门视频的标题中提取关键词
          # 先搜索种子词，获取 Top 100 视频，提取标题高频词

      - name: 时间切片法
        description: 按不同时间段分别搜索
        example: |
          # 分别搜索不同时间段
          time_ranges = ["今天", "本周", "本月"]
          for tr in time_ranges:
              search(keyword, time_range=tr, limit=300)

      - name: 排序切换法
        description: 使用不同排序方式获取不同视频
        example: |
          # 同一关键词，不同排序
          sort_methods = ["相关性", "上传日期", "观看次数"]
          for sort in sort_methods:
              search(keyword, sort=sort, limit=300)

  # ============ 去重策略 ============
  deduplication:
    rule: 多次搜索结果必须去重
    method: 按 video_id 去重
    implementation: |
      seen_ids = set()
      unique_videos = []
      for video in all_results:
          if video['id'] not in seen_ids:
              seen_ids.add(video['id'])
              unique_videos.append(video)

  # ============ 合并策略 ============
  merge_strategy:
    rule: 多批次结果合并时保留来源标记
    fields_to_preserve:
      - search_keyword: 搜索关键词
      - search_time_range: 时间范围
      - search_sort: 排序方式
      - batch_id: 批次 ID
```

### 3. 搜索结果验证

```yaml
search_validation:
  description: 验证搜索结果是否符合预期

  checks:
    - name: 数量验证
      action: 检查实际获取数量是否达到目标
      pass_criteria: actual >= target * 0.8
      on_failure: |
        可能原因：
        1. 搜索条件过于严格
        2. 该主题视频本身就少
        3. 网络问题导致部分失败

    - name: 时间范围验证
      action: 抽样检查 upload_date 是否在指定范围内
      pass_criteria: 100% 在范围内
      on_failure: 检查 sp 参数是否正确

    - name: 去重率统计
      action: 计算 (原始数量 - 去重后数量) / 原始数量
      threshold: < 30%
      on_exceed: 搜索策略可能有重叠，需要调整关键词
```

### 2. 关键词来源规约

```yaml
keyword_source:
  rule: 关键词必须来自用户行为数据，不能 AI 随意生成

  valid_sources:
    - name: 搜索框长尾词建议
      method: get_search_suggestions(seed_keyword)
      example: "健康" → ["健康养生", "健康饮食", "健康生活方式"]

    - name: 视频标签
      method: extract_tags_from_video(video_id)
      example: 从热门视频中提取 tags 字段

    - name: 频道视频标签
      method: extract_tags_from_channel(channel_id)
      example: 从频道所有视频中提取高频标签

    - name: 用户手动输入
      method: user_input
      example: 用户直接指定关键词

  invalid_sources:
    - AI 随意生成  # ❌
    - 硬编码的关键词列表  # ❌

  logging:
    required: true
    format: "{keyword}: {source_type} | {source_detail}"
```

### 3. 数据分层设计

```yaml
data_layers:
  rule: 原始数据与加工数据必须分离

  raw_layer:
    path: "data/raw/"
    description: 保存所有采集的原始数据，不做任何处理
    retention: 永久保留
    format: JSON

  processed_layer:
    path: "data/processed/"
    description: 根据需求过滤和计算后的数据
    retention: 可重新生成
    format: JSON / SQLite

  presentation_layer:
    path: "data/reports/"
    description: 最终展示用的数据
    retention: 可重新生成
    format: HTML / Markdown

  reason: |
    如果目标变化需要重新分析，原始数据不需要重新采集
```

### 4. 提高采集成功率（核心策略）

```yaml
success_rate_optimization:
  description: 从多个维度提高采集成功率

  # ============ 1. 请求间隔控制 ============
  rate_limiting:
    rule: 必须控制请求频率，避免被 YouTube 限流

    recommended_delays:
      - type: 视频列表搜索
        delay: 1-2 秒/请求
      - type: 视频详情获取
        delay: 0.5-1 秒/请求
      - type: 频道信息获取
        delay: 1-2 秒/请求

    implementation: |
      import time
      import random

      def request_with_delay(url, min_delay=1, max_delay=2):
          response = fetch(url)
          time.sleep(random.uniform(min_delay, max_delay))
          return response

    anti_patterns:
      - ❌ 无间隔连续请求
      - ❌ 固定间隔（容易被检测）

  # ============ 2. 并发控制 ============
  concurrency:
    rule: 控制并发数量，避免触发限流

    recommended:
      - 视频详情采集：最多 3 并发
      - 频道信息采集：最多 2 并发
      - 搜索请求：串行执行（1 并发）

    implementation: |
      import asyncio
      from asyncio import Semaphore

      semaphore = Semaphore(3)  # 最多 3 并发

      async def fetch_with_limit(url):
          async with semaphore:
              return await fetch(url)

  # ============ 3. 错误分类处理 ============
  error_handling:
    categories:
      - type: 可重试错误
        errors: [network_timeout, connection_reset, 429_rate_limit, 503_service_unavailable]
        action: 指数退避重试
        max_retries: 3

      - type: 不可重试错误
        errors: [404_not_found, video_unavailable, private_video, age_restricted]
        action: 标记并跳过，不重试
        log_reason: true

      - type: 需要人工干预
        errors: [captcha_required, account_blocked]
        action: 暂停采集，提示用户

    implementation: |
      def handle_error(error, url):
          if error.code in [429, 503]:
              return "retry_with_backoff"
          elif error.code == 404 or "unavailable" in error.message:
              log_skip(url, reason=error.message)
              return "skip"
          elif "captcha" in error.message:
              return "pause_and_notify"

  # ============ 4. 智能退避策略 ============
  backoff_strategy:
    type: 指数退避 + 抖动

    delays: [5, 15, 45, 120]  # 秒
    jitter: 0.3  # 30% 随机抖动

    implementation: |
      import random

      def get_backoff_delay(retry_count, base_delays=[5, 15, 45, 120], jitter=0.3):
          if retry_count >= len(base_delays):
              base = base_delays[-1]
          else:
              base = base_delays[retry_count]
          return base * (1 + random.uniform(-jitter, jitter))

  # ============ 5. 批量采集优化 ============
  batch_optimization:
    rule: 大批量采集时的优化策略

    strategies:
      - name: 分时段采集
        description: 避开高峰期，选择凌晨采集
        recommended_time: "02:00 - 06:00"

      - name: 分批次采集
        description: 每批 100-200 个，批次间休息 5 分钟
        implementation: |
          batch_size = 100
          for i in range(0, total, batch_size):
              batch = items[i:i+batch_size]
              collect_batch(batch)
              if i + batch_size < total:
                  time.sleep(300)  # 休息 5 分钟

      - name: 优先级排序
        description: 先采集高价值数据，确保核心数据成功
        priority_order:
          - 1: Top 100 高播放量视频详情
          - 2: 热门频道信息
          - 3: 其他视频详情

  # ============ 6. 不可采集项识别 ============
  uncollectable_detection:
    rule: 识别并标记即使网络正常也无法采集的项

    types:
      - type: 私有视频
        detection: "Private video" in error
        action: 标记为 uncollectable，跳过

      - type: 已删除视频
        detection: "Video unavailable" in error
        action: 标记为 deleted，跳过

      - type: 年龄限制
        detection: "age-restricted" in error
        action: 标记为 age_restricted，可选登录后重试

      - type: 地区限制
        detection: "not available in your country" in error
        action: 标记为 geo_blocked，可选代理重试

    logging:
      file: "logs/uncollectable_items.json"
      fields:
        - url
        - type
        - reason
        - detected_at

  # ============ 7. 成功率监控 ============
  success_rate_monitoring:
    metrics:
      - name: 实时成功率
        formula: (成功数) / (尝试数) * 100
        alert_threshold: < 70%
        action_on_alert: 暂停采集，检查网络

      - name: 最终成功率
        formula: (成功数 + 补采成功数) / (总需求数) * 100
        target: >= 95%

    display: |
      📊 采集成功率
      - 实时成功率：{realtime_rate}%
      - 重试成功：{retry_success} 条
      - 不可采集：{uncollectable} 条
      - 待补采：{pending_backfill} 条
```

### 5. 网络重试机制

```yaml
retry_policy:
  max_retries: 3
  retry_delay: [5, 15, 45]  # 秒，指数退避 + 抖动

  retry_on:
    - network_error
    - timeout
    - rate_limit (429)
    - 503_service_unavailable

  not_retry_on:
    - 404_not_found
    - video_unavailable
    - private_video

  failure_logging:
    file: "logs/collection_failures.json"
    fields:
      - url
      - error_type
      - error_message
      - timestamp
      - retry_count
      - is_retriable

  backfill_strategy:
    description: 网络恢复后自动重试失败项
    trigger: 手动执行 `ytp collect --backfill`

    steps:
      - 1: 读取 logs/collection_failures.json
      - 2: 过滤出 is_retriable=true 的项
      - 3: 按优先级排序（高播放量视频优先）
      - 4: 重新采集
      - 5: 更新成功率统计
```

### 5. 缺失率统计与阈值

```yaml
completeness_check:
  metrics:
    - name: 视频数据完整率
      formula: (有完整元数据的视频数) / (总采集视频数) * 100
      threshold: 90%
      on_below_threshold: 触发重试

    - name: 频道数据完整率
      formula: (有频道详情的频道数) / (总频道数) * 100
      threshold: 80%
      on_below_threshold: 标记为「频道数据待补充」

  report:
    display: 采集完成后显示完整率报告
    format: |
      📊 数据完整率报告
      - 视频数据：{video_rate}% ({complete_videos}/{total_videos})
      - 频道数据：{channel_rate}% ({complete_channels}/{total_channels})
      - 失败项：{failure_count} 条（详见 logs/collection_failures.json）
```

---

## 📋 采集流程

```yaml
collection_flow:
  - step: 1
    name: 参数验证
    actions:
      - 验证关键词来源
      - 验证时间范围参数
      - 检查 sp 参数是否正确

  - step: 2
    name: 搜索视频
    actions:
      - 使用 YouTube 原生时间过滤
      - 记录搜索 URL
      - 显示进度（已获取 X / 目标 Y）

  - step: 3
    name: 获取详情
    actions:
      - 批量获取视频元数据
      - 批量获取频道信息
      - 失败项记录并重试

  - step: 4
    name: 数据存储
    actions:
      - 保存原始数据到 raw 层
      - 生成加工数据到 processed 层
      - 更新数据库索引

  - step: 5
    name: 完整率检查
    actions:
      - 计算各项完整率
      - 生成完整率报告
      - 低于阈值时提示用户
```

---

## ⏱️ 进度反馈

```yaml
progress_feedback:
  enabled: true

  display_items:
    - 当前阶段名称
    - 进度百分比
    - 已采集数量 / 目标数量
    - 预估剩余时间
    - 网络速度（可选）

  format: |
    🔄 {stage_name}
    进度：{current}/{total} ({percent}%)
    预估剩余：{eta}
    速度：{speed}/s

  estimated_time:
    - target: 100
      time: "约 2 分钟"
    - target: 500
      time: "约 10 分钟"
    - target: 1000
      time: "约 20 分钟"
```

---

## 📊 命令模板

```bash
# 搜索本周内的视频（使用 YouTube 原生过滤）
yt-dlp --flat-playlist --dump-json \
  "https://www.youtube.com/results?search_query=健康养生&sp=EgIIAw%3D%3D" \
  > data/raw/search_results.json

# 获取视频详情
yt-dlp --dump-json "https://youtube.com/watch?v={video_id}" \
  --retries 3 \
  > data/raw/video_{video_id}.json

# 获取频道信息
yt-dlp --dump-json "https://youtube.com/channel/{channel_id}" \
  --retries 3 \
  > data/raw/channel_{channel_id}.json
```

---

## 📋 采集后验证

```yaml
post_collection_checks:
  - name: 时间范围验证
    action: 抽样 10 条数据，检查 upload_date 是否在指定范围内
    pass_criteria: 100% 在范围内
    on_failure: 检查 sp 参数是否正确

  - name: 数据量验证
    action: 检查采集数量是否达到目标
    pass_criteria: actual >= target * 0.9
    on_failure: 检查搜索条件是否过于严格

  - name: 字段完整性
    required_fields:
      - id
      - title
      - view_count
      - upload_date
      - channel
    on_missing: 记录到缺失日志
```

---

## 输出

- 原始数据：`data/raw/{date}_{keyword}.json`
- 加工数据：`data/processed/{date}_{keyword}.json`
- 数据库：`data/videos.db`
- 采集日志：`logs/collection_log.json`
- 失败记录：`logs/collection_failures.json`
- 完整率报告：`logs/completeness_report.json`
