# youtube-transcript

提取 YouTube 视频字幕。

## 触发条件

用户要提取字幕、获取视频文稿时使用。

## 执行步骤

1. 尝试下载手动字幕
2. 如果没有，尝试自动生成的字幕
3. 如果都没有，使用 Whisper 转录
4. 验证字幕文件完整性

## 命令模板

```bash
# 下载字幕（优先手动，其次自动）- 带重试
yt-dlp --write-sub --write-auto-sub \
  --sub-lang zh,en \
  --skip-download \
  --retries 3 \
  "[URL]" \
  -o "data/transcripts/%(id)s"

# 如果没有字幕，先下载音频再用 Whisper
yt-dlp -f "bestaudio" "[URL]" -x --audio-format mp3 -o "temp_audio.mp3" --retries 3
whisper temp_audio.mp3 --model base --language zh --output_format vtt --output_dir data/transcripts/
rm temp_audio.mp3
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
    - no_subtitle_found

  fallback_chain:
    - step: 1
      action: 下载手动字幕
      on_failure: 尝试步骤 2

    - step: 2
      action: 下载自动生成字幕
      on_failure: 尝试步骤 3

    - step: 3
      action: 使用 Whisper 转录
      on_failure: 记录失败，提示用户
```

### 2. 进度反馈

```yaml
progress_feedback:
  stages:
    - name: 检查字幕可用性
      display: "正在检查视频是否有字幕..."
      weight: 10%

    - name: 下载字幕
      display: "正在下载字幕文件..."
      weight: 30%

    - name: Whisper 转录（如需要）
      display: "正在使用 Whisper 转录音频（预计 {duration} 分钟）..."
      weight: 50%
      estimated_time:
        - audio_length: 5min
          time: "约 1 分钟"
        - audio_length: 10min
          time: "约 2 分钟"
        - audio_length: 30min
          time: "约 5 分钟"

    - name: 格式转换
      display: "正在转换字幕格式..."
      weight: 10%
```

### 3. 失败项记录

```yaml
failure_logging:
  log_file: "logs/transcript_failures.json"
  record_fields:
    - video_id
    - url
    - subtitle_type_tried  # manual / auto / whisper
    - error_message
    - timestamp
```

---

## 📋 提取后验证

```yaml
post_extraction_checks:
  - name: 文件存在性
    action: ls data/transcripts/{video_id}.*
    on_failure: 标记为提取失败

  - name: 文件非空
    min_size: 100 bytes
    on_failure: 字幕文件可能损坏

  - name: 格式有效性
    action: 检查 VTT/SRT 格式是否正确
    on_failure: 尝试格式修复
```

## 输出

- 字幕文件：`data/transcripts/{video_id}.vtt` 或 `.srt`
- 提取日志：`logs/transcript_log.json`
- 失败记录：`logs/transcript_failures.json`
