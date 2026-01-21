# youtube-to-markdown

将 YouTube 视频元数据转换为 Markdown 文档。

## 触发条件

用户要获取视频信息、整理视频元数据时使用。

## 执行步骤

1. 使用 yt-dlp 获取视频元数据（JSON）
2. 解析 JSON 提取关键信息
3. **验证链接可访问性**
4. 生成 Markdown 格式文档

## 命令模板

```bash
# 获取元数据（带重试）
yt-dlp --dump-json "[URL]" --retries 3 > temp_meta.json
```

---

## ⚠️ 核心约束（基于踩坑经验）

### 1. 链接验证

```yaml
link_validation:
  required: true
  check_items:
    - video_url: "https://youtube.com/watch?v={id}"
      format: 必须是完整 URL，不能是占位符
      validation: 确保 {id} 是 11 位有效字符

    - channel_url: "https://youtube.com/channel/{channel_id}"
      format: 必须是完整 URL
      validation: 确保 channel_id 存在

  on_invalid:
    action: 标记为「链接待验证」，不要使用假链接
```

### 2. 时间过滤参数

```yaml
time_filter:
  description: 批量获取视频元数据时，支持时间范围过滤

  youtube_sp_params:
    # YouTube 搜索 URL 中的 sp 参数
    - name: 今天
      sp: "EgIIAg%3D%3D"
    - name: 本周
      sp: "EgIIAw%3D%3D"
    - name: 本月
      sp: "EgIIBA%3D%3D"
    - name: 今年
      sp: "EgIIBQ%3D%3D"

  usage_example: |
    # 搜索本周内的视频
    yt-dlp --dump-json "ytsearch50:健康养生" \
      --match-filter "upload_date>=$(date -d '7 days ago' +%Y%m%d)" \
      > videos.json

    # 或使用 YouTube 原生过滤 URL
    yt-dlp --dump-json "https://www.youtube.com/results?search_query=健康养生&sp=EgIIAw%3D%3D" \
      > videos.json
```

### 3. 发布时间验证

```yaml
time_validation:
  enabled: true
  action: 检查 upload_date 是否在预期范围内
  on_out_of_range: 标记并提示用户
```

---

## Markdown 模板

```markdown
# {title}

## 基本信息

| 属性 | 值 |
|------|-----|
| 视频 ID | {id} |
| 频道 | [{channel}]({channel_url}) |
| 发布日期 | {upload_date} |
| 时长 | {duration} |
| 观看数 | {view_count} |
| 点赞数 | {like_count} |

## 描述

{description}

## 标签

{tags}

## 链接

- 视频：[点击观看](https://youtube.com/watch?v={id})
- 频道：[访问频道]({channel_url})

---

> 数据获取时间：{fetch_timestamp}
> 链接验证状态：{link_status}
```

---

## 📋 生成后检查

```yaml
post_generation_checks:
  - name: 链接格式验证
    action: 检查所有 URL 是否为完整格式
    pattern: "^https://youtube\\.com/"
    on_failure: 修复链接格式

  - name: 必填字段检查
    required_fields:
      - title
      - id
      - channel
      - upload_date
    on_missing: 标记为数据不完整
```

## 输出

- Markdown 文件：`data/reports/video_{video_id}.md`
- 批量输出：`data/reports/videos_{date}.md`
