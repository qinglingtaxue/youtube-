# media-processing

音视频媒体处理。

## 触发条件

- 用户要处理视频/音频
- 用户要合成视频
- 用户要转换格式

## 功能

### 1. 视频合成

```bash
# 拼接多个视频
echo "file 'clip1.mp4'" > filelist.txt
echo "file 'clip2.mp4'" >> filelist.txt
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4

# 添加音轨
ffmpeg -i video.mp4 -i audio.mp3 \
  -c:v copy -c:a aac \
  -map 0:v:0 -map 1:a:0 \
  output.mp4

# 混合背景音乐
ffmpeg -i video.mp4 -i bgm.mp3 \
  -filter_complex "[0:a][1:a]amix=inputs=2:duration=first[a]" \
  -c:v copy -map 0:v -map "[a]" \
  output.mp4
```

### 2. 字幕烧录

```bash
ffmpeg -i video.mp4 \
  -vf "subtitles=subs.srt:force_style='FontSize=24'" \
  -c:a copy \
  output.mp4
```

### 3. 音频处理

```bash
# 降噪
ffmpeg -i input.mp3 -af "afftdn=nf=-25" output.mp3

# 音量标准化
ffmpeg -i input.mp3 -af "loudnorm=I=-16:LRA=11:TP=-1.5" output.mp3
```

### 4. 格式转换

```bash
# 视频转 MP4
ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4

# 提取音频
ffmpeg -i video.mp4 -vn -c:a mp3 audio.mp3
```

### 5. 封面制作

```bash
# 纯色背景 + 文字
magick -size 1280x720 xc:"#1a1a2e" \
  -font "PingFang-SC-Bold" -pointsize 72 \
  -fill white -gravity center \
  -annotate +0+0 "标题" \
  thumbnail.jpg
```

## 输出参数建议

| 参数 | 值 |
|------|-----|
| 分辨率 | 1920x1080 |
| 帧率 | 30fps |
| 视频编码 | H.264 |
| 视频码率 | 8-12 Mbps |
| 音频编码 | AAC |
| 音频码率 | 192 kbps |

## 输出

- 视频：`output/video_{date}.mp4`
- 音频：`data/audio/{name}.mp3`
- 封面：`output/thumbnail_{date}.jpg`
