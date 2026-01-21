# youtube-downloader

下载 YouTube 视频。

## 触发条件

用户要下载 YouTube 视频时使用。

## 执行步骤

1. 解析视频 URL，提取 video_id
2. 检查本地是否已存在（避免重复下载）
3. 使用 yt-dlp 下载视频（带进度显示）
4. 验证下载完整性
5. 保存到 `data/videos/` 目录
6. 记录下载日志

## 命令模板

```bash
# 下载最高质量（最高 1080p）- 带进度条
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" "[URL]" \
  -o "data/videos/%(id)s.%(ext)s" \
  --progress \
  --newline

# 下载 4K（如果可用）
yt-dlp -f "bestvideo[height<=2160]+bestaudio/best" "[URL]" \
  -o "data/videos/%(id)s.%(ext)s" \
  --progress

# 只下载音频
yt-dlp -f "bestaudio" "[URL]" \
  -x --audio-format mp3 \
  -o "data/audio/%(id)s.%(ext)s" \
  --progress
```

---

## ⚠️ 核心约束（基于踩坑经验）

### 1. 网络重试机制

```yaml
retry_policy:
  max_retries: 3
  retry_delay: [5, 10, 30]  # 秒，指数退避
  retry_on:
    - network_error
    - timeout
    - rate_limit

  command_with_retry: |
    yt-dlp "[URL]" \
      --retries 3 \
      --fragment-retries 5 \
      --retry-sleep 5 \
      -o "data/videos/%(id)s.%(ext)s"
```

### 2. 失败项记录

```yaml
failure_logging:
  log_file: "logs/download_failures.json"
  record_fields:
    - video_id
    - url
    - error_type
    - error_message
    - timestamp
    - retry_count

  example: |
    {
      "video_id": "abc123",
      "url": "https://youtube.com/watch?v=abc123",
      "error_type": "network_error",
      "error_message": "Connection timed out",
      "timestamp": "2026-01-20T15:30:00",
      "retry_count": 3
    }
```

### 3. 进度反馈

```yaml
progress_feedback:
  display_items:
    - 当前下载进度（百分比）
    - 下载速度（MB/s）
    - 预估剩余时间
    - 已下载大小 / 总大小

  command: |
    yt-dlp "[URL]" \
      --progress-template "%(progress._percent_str)s | %(progress._speed_str)s | ETA: %(progress._eta_str)s" \
      -o "data/videos/%(id)s.%(ext)s"
```

---

## 📋 下载前检查

```yaml
pre_download_checks:
  - name: 检查本地是否已存在
    action: ls data/videos/{video_id}.*
    on_exists: 跳过下载，提示用户

  - name: 检查磁盘空间
    action: df -h data/videos/
    min_space: 1GB
    on_failure: 提示用户清理空间

  - name: 验证 URL 格式
    pattern: "^https?://(www\\.)?youtube\\.com/watch\\?v=[a-zA-Z0-9_-]{11}"
    on_failure: 提示 URL 格式错误
```

---

## 📋 下载后验证

```yaml
post_download_checks:
  - name: 文件完整性
    action: ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file}"
    pass_criteria: 返回有效时长
    on_failure: 标记为下载不完整，加入重试队列

  - name: 文件大小
    min_size: 1MB  # 视频至少 1MB
    on_failure: 可能下载失败，建议重试
```

## 输出

- 视频文件：`data/videos/{video_id}.mp4`
- 或音频文件：`data/audio/{video_id}.mp3`
- 下载日志：`logs/download_log.json`
- 失败记录：`logs/download_failures.json`
