# 阶段 4：制作阶段 (Production)

**前置条件**: 已完成 [阶段 3：策划阶段](./PROMPT_03_策划阶段.md)

> 根据脚本和规约制作视频

---

## 经验索引

> 📄 `.42cog/work/EXPERIENCE_INDEX.md`

**什么时候查**：踩坑了 / 这个问题之前好像遇到过 / 要做影响范围大的改动

---

## 规格引用

> ⚠️ **本提示词是规格的执行器，执行前请确认符合以下规格：**

| 规格文档 | 引用章节 | 用途 |
|----------|----------|------|
| `.42cog/spec/pm/pipeline.spec.md` | Stage 3: Production | 输入输出契约、前置后置条件 |
| `.42cog/cog/cog.md` | Video, Subtitle, Thumbnail | 实体定义和状态 |
| `.42cog/real/real.md` | #2 版权合规, #4 存储与成本控制 | 约束检查 |

### 执行前检查 (来自 pipeline.spec.md)

```yaml
preconditions:
  dependencies:
    - stage: planning
      status: completed
      outputs: [Spec, Script]
  tools:
    - name: ffmpeg
      check: "ffmpeg -version"
      min_version: "6.0"
  constraints:
    - ref: "real.md#版权合规"
      check: "所有素材来源已记录"
    - ref: "real.md#存储与成本控制"
      check: "磁盘剩余空间 > 20GB"
```

### 输入契约

```yaml
input:
  required:
    - spec: Spec               # 来自策划阶段
    - script: Script           # 来自策划阶段
  optional:
    - assets: Asset[]          # 预备素材
    - voiceover_provider: enum # "elevenlabs" | "minimax" | "recorded"
    - resolution: enum         # "1080p" | "4K"
```

---

## 阶段目标

- 准备和管理视频素材
- 生成配音音频（TTS 或录制）
- 处理和优化字幕
- 合成最终视频
- 制作视频封面

---

## 技术栈参考

📄 **参考文档**：`.42cog/work/2026-01-17-技术栈与MCP清单.md`

### 本阶段需要的工具

| 工具 | 用途 | 验证命令 |
|------|------|----------|
| FFmpeg | 音视频合成 | `ffmpeg -version` |
| ImageMagick | 封面制作 | `magick --version` |
| Whisper | 字幕生成 | `whisper --help` |

### TTS 服务（可选）

| 服务 | 用途 | 文档 |
|------|------|------|
| ElevenLabs | 英文高质量配音 | https://elevenlabs.io/docs |
| MiniMax | 中文配音 | https://platform.minimaxi.com/document |

### 本阶段不需要 MCP

制作阶段主要使用本地工具（FFmpeg、ImageMagick），不需要启用 MCP。

---

## Skill

> 查阅 `CLAUDE.md`「Skill 调用规则」，按用户意图自动调用对应 skill。

本阶段常用：`transcript-fixer`、`media-processing`

---

## 提示词模板

### 模板 3.1：素材准备

```
请帮我为视频准备素材。

## 视频规约
- 规约文件：`.42cog/spec/pm/video_spec_YYYYMMDD.md`
- 脚本文件：`scripts/video_script_YYYYMMDD.md`

## 素材需求清单

### 1. 视频片段
- [ ] 录屏演示（如有）
- [ ] Stock footage（如需要）
- [ ] 动画/过渡效果

### 2. 图片素材
- [ ] 配图/截图
- [ ] 图表/数据可视化
- [ ] Logo/品牌元素

### 3. 音频素材
- [ ] 配音音频
- [ ] 背景音乐（免版税）
- [ ] 音效（如有）

## 素材来源建议
- Stock footage: Pexels, Pixabay
- 音乐: YouTube Audio Library, Uppbeat
- 音效: freesound.org

## 输出
- 素材清单：`data/assets/asset_list_YYYYMMDD.json`
- 素材目录结构：
  ```
  data/assets/YYYYMMDD/
  ├── video/
  ├── image/
  ├── audio/
  └── metadata.json
  ```

素材清单格式：
```json
{
  "project_id": "video_YYYYMMDD",
  "assets": [
    {
      "id": "asset_001",
      "type": "video",
      "name": "intro_clip.mp4",
      "source": "Pexels",
      "license": "CC0",
      "path": "data/assets/YYYYMMDD/video/intro_clip.mp4"
    }
  ]
}
```
```

---

### 模板 3.2：配音生成

```
请根据脚本生成配音音频。

## 脚本文件
`scripts/video_script_YYYYMMDD.md`

## 配音要求
- 语言：中文 / 英文
- 语速：正常（150-180 字/分钟）
- 风格：专业 / 亲切 / 活泼

## 方案选择

### 方案 A：ElevenLabs（英文高质量）
```bash
# API 调用示例
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}" \
  -H "xi-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your script text here...",
    "model_id": "eleven_monolingual_v1"
  }'
```

### 方案 B：MiniMax（中文）
```bash
# 参考 MiniMax API 文档
# https://platform.minimaxi.com/document
```

### 方案 C：自己录制
- 使用安静环境
- 推荐麦克风：Blue Yeti / Rode
- 录制软件：Audacity / GarageBand

## 输出
- 配音文件：`data/audio/voiceover_YYYYMMDD.mp3`
- 音频参数：44.1kHz, 16bit, 立体声

## 后处理
```bash
# 降噪（使用 FFmpeg）
ffmpeg -i voiceover_raw.mp3 -af "afftdn=nf=-25" voiceover_clean.mp3

# 音量标准化
ffmpeg -i voiceover_clean.mp3 -af "loudnorm=I=-16:LRA=11:TP=-1.5" voiceover_final.mp3
```
```

---

### 模板 3.3：字幕处理

```
请处理和优化视频字幕。

## 输入
- 配音音频：`data/audio/voiceover_YYYYMMDD.mp3`
- 或：现有字幕文件

## 任务

### 1. 字幕生成（如无现有字幕）
```bash
# 使用 Whisper 生成字幕
whisper "data/audio/voiceover_YYYYMMDD.mp3" \
  --model base \
  --language zh \
  --output_format srt \
  --output_dir data/transcripts/
```

### 2. 字幕修复
使用 transcript-fixer skill 进行：
- 修正错别字
- 优化断句
- 调整时间轴

### 3. 字幕格式转换
```bash
# SRT 转 VTT
ffmpeg -i subtitles.srt subtitles.vtt

# VTT 转 SRT
ffmpeg -i subtitles.vtt subtitles.srt
```

## 字幕规范
- 每行不超过 42 个字符（中文）/ 72 个字符（英文）
- 每屏不超过 2 行
- 最短显示时间：1 秒
- 最长显示时间：7 秒

## 输出
- 字幕文件：`data/transcripts/subtitles_YYYYMMDD.srt`
- 字幕文件：`data/transcripts/subtitles_YYYYMMDD.vtt`
```

---

### 模板 3.4：视频合成

```
请合成最终视频。

## 输入文件
- 视频片段：`data/assets/YYYYMMDD/video/*.mp4`
- 配音音频：`data/audio/voiceover_YYYYMMDD.mp3`
- 背景音乐：`data/audio/bgm_YYYYMMDD.mp3`
- 字幕文件：`data/transcripts/subtitles_YYYYMMDD.srt`

## 合成步骤

### 1. 视频拼接（如有多个片段）
```bash
# 创建文件列表
echo "file 'clip1.mp4'" > filelist.txt
echo "file 'clip2.mp4'" >> filelist.txt

# 拼接
ffmpeg -f concat -safe 0 -i filelist.txt -c copy merged.mp4
```

### 2. 添加配音
```bash
ffmpeg -i video.mp4 -i voiceover.mp3 \
  -c:v copy -c:a aac \
  -map 0:v:0 -map 1:a:0 \
  video_with_voice.mp4
```

### 3. 混合背景音乐
```bash
ffmpeg -i video_with_voice.mp4 -i bgm.mp3 \
  -filter_complex "[0:a][1:a]amerge=inputs=2,pan=stereo|c0<c0+c2|c1<c1+c3[a]" \
  -c:v copy -map 0:v -map "[a]" \
  video_with_bgm.mp4
```

### 4. 烧录字幕
```bash
ffmpeg -i video_with_bgm.mp4 \
  -vf "subtitles=subtitles.srt:force_style='FontSize=24,FontName=PingFang SC'" \
  -c:a copy \
  output_final.mp4
```

### 5. 一键合成命令
```bash
ffmpeg -i video.mp4 -i voiceover.mp3 -i bgm.mp3 \
  -filter_complex "[1:a]volume=1.0[voice];[2:a]volume=0.3[bgm];[voice][bgm]amix=inputs=2:duration=first[a]" \
  -vf "subtitles=subtitles.srt" \
  -c:v libx264 -preset slow -crf 18 \
  -c:a aac -b:a 192k \
  -map 0:v -map "[a]" \
  output/video_final.mp4
```

## 输出参数建议
- 分辨率：1920x1080（1080p）
- 帧率：30fps
- 视频编码：H.264
- 视频码率：8-12 Mbps
- 音频编码：AAC
- 音频码率：192 kbps

## 输出
- 最终视频：`output/video_YYYYMMDD_final.mp4`
```

---

### 模板 3.5：封面制作

```
请为视频制作封面。

## 封面要求
- 尺寸：1280x720 像素（16:9）
- 格式：JPG 或 PNG
- 文件大小：< 2MB

## 设计原则
1. **醒目的标题**：大字、高对比度
2. **人脸/表情**：增加点击率
3. **品牌一致性**：使用统一的颜色和字体
4. **简洁**：不超过 5 个元素

## 使用 ImageMagick 制作
```bash
# 基础封面（纯色背景+文字）
magick -size 1280x720 xc:"#1a1a2e" \
  -font "PingFang-SC-Bold" -pointsize 72 \
  -fill white -gravity center \
  -annotate +0-100 "视频标题" \
  -pointsize 36 -annotate +0+100 "副标题" \
  thumbnail.jpg

# 添加图片叠加
magick background.jpg \
  \( overlay.png -resize 400x400 \) -gravity east -geometry +50+0 -composite \
  -font "PingFang-SC-Bold" -pointsize 72 -fill white \
  -gravity west -annotate +50+0 "标题" \
  thumbnail.jpg
```

## 输出
- 封面文件：`output/thumbnail_YYYYMMDD.jpg`
- 备选封面：`output/thumbnail_YYYYMMDD_alt.jpg`

## 建议
- 制作 3 个备选封面用于 A/B 测试
- 预览在小尺寸下的可读性
```

---

## 产出文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 素材清单 | `data/assets/asset_list_*.json` | 素材元数据 |
| 配音音频 | `data/audio/voiceover_*.mp3` | 配音文件 |
| 字幕文件 | `data/transcripts/subtitles_*.srt` | 字幕文件 |
| 最终视频 | `output/video_*_final.mp4` | 合成视频 |
| 封面图 | `output/thumbnail_*.jpg` | 视频封面 |

---

## 需要更新的文档

| 文档 | 更新内容 |
|------|----------|
| `data/assets/` | 新增素材文件 |
| `data/audio/` | 新增音频文件 |
| `data/transcripts/` | 新增字幕文件 |
| `output/` | 新增视频和封面 |
| `.42cog/work/` | 记录制作过程 |

---

## 质量检查

### 视频检查
- [ ] 视频画质清晰（1080p）
- [ ] 音画同步
- [ ] 配音清晰可听
- [ ] 背景音乐音量适中
- [ ] 字幕无错误
- [ ] 时长符合预期

### 封面检查
- [ ] 尺寸正确（1280x720）
- [ ] 文字清晰可读
- [ ] 小尺寸预览效果好

---

## 检查清单

- [ ] 素材已准备完毕
- [ ] 配音已生成/录制
- [ ] 字幕已处理优化
- [ ] 视频已合成
- [ ] 封面已制作
- [ ] 质量检查通过

---

## 后置检查 (来自 pipeline.spec.md)

```yaml
postconditions:
  validation:
    - "Video 文件存在且可播放"
    - "Video 时长与 spec.target_duration 误差 < 10%"
    - "Subtitle 时间轴与 Video 同步"
    - "Thumbnail 分辨率 >= 1280x720"
  quality:
    - "视频无明显画质问题"
    - "音频清晰，无杂音"
    - "字幕无错别字 (AI 检测)"
```

### 输出契约

```yaml
output:
  files:
    - path: "data/videos/{video_id}.mp4"
      type: Video
      constraints:
        - format: mp4
        - resolution: >= 1080p
    - path: "data/transcripts/{video_id}.vtt"
      type: Subtitle
      constraints:
        - format: vtt | srt
    - path: "data/thumbnails/{video_id}.jpg"
      type: Thumbnail
      constraints:
        - resolution: >= 1280x720
        - file_size: < 2MB
  database:
    - entity: Video
      status_update: "draft → producing → ready"
```

---

## 下一步

完成制作后，进入 **阶段 5：发布阶段**，将视频上传到 YouTube。

---

*文档版本: 1.0*
*更新日期: 2026-01-17*
