# YouTube 内容创作流水线

YouTube 内容创作全流程自动化工具，覆盖调研、策划、制作、发布、复盘五个阶段。

## 快速开始

```bash
# 激活虚拟环境
source .venv/bin/activate

# 查看可用命令
python cli.py --help

# 查看项目状态
python cli.py status
```

## 项目结构

```
├── src/
│   ├── research/      # 调研模块 - 竞品分析、热点追踪
│   ├── planning/      # 策划模块 - 选题策划、脚本生成
│   ├── production/    # 制作模块 - 视频剪辑、字幕生成
│   ├── publishing/    # 发布模块 - 自动上传、SEO优化
│   ├── analytics/     # 复盘模块 - 数据分析、报告生成
│   └── shared/        # 共享模块 - 通用工具和模型
├── data/              # 数据文件目录
├── config/            # 配置文件
├── scripts/           # 辅助脚本
└── logs/              # 日志文件
```

## 核心功能

### 调研阶段
- YouTube 频道分析
- 竞品视频下载与分析
- 热门话题追踪

### 策划阶段
- 选题生成与评估
- 脚本大纲生成
- 素材规划

### 制作阶段
- 视频剪辑自动化
- 语音转字幕 (Whisper)
- 封面生成

### 发布阶段
- 自动上传至 YouTube
- 元数据优化
- 发布时间调度

### 复盘阶段
- 观看数据采集
- 表现分析报告
- 优化建议生成

## 依赖工具

- Python 3.10+
- yt-dlp - 视频下载
- ffmpeg - 音视频处理
- whisper - 语音识别
- playwright - 浏览器自动化

## 配置

主配置文件: `config/settings.yaml`
存储策略: `config/storage.yaml`

## 许可证

Private
