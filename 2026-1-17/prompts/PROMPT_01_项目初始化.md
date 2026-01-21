# 阶段 1：项目初始化

> 完成项目环境配置和目录结构创建

**前置条件**: 已完成 [阶段 0：前置准备](./PROMPT_00_前置准备.md)

---

## 经验索引

> 📄 `.42cog/work/EXPERIENCE_INDEX.md`

**什么时候查**：踩坑了 / 这个问题之前好像遇到过 / 要做影响范围大的改动

---

## 目标

- 创建项目目录结构
- 初始化 Git
- 配置 Python 虚拟环境
- 验证 42cog 目录结构

## 技术栈参考

📄 `前置准备/2026-01-17-技术栈与MCP清单.md`

## 检查点

- [ ] 项目目录已创建
- [ ] Git 仓库已初始化
- [ ] Python 环境就绪
- [ ] 核心工具可用（yt-dlp, ffmpeg, whisper）
- [ ] 42cog 目录结构完整

---

## 提示词模板

### 模板 1.1：一键初始化项目

```
请帮我初始化 YouTube 内容创作流水线项目。

## 环境信息
- 设备：搭载 Apple 芯片的 Mac 电脑
- Python 环境：通过 uv 配置
- Node.js 管理：通过 bun 进行安装
- Git 代码托管：cnb.cool

## 初始化步骤

### 1. 创建项目目录结构
```
youtube-content-pipeline/
├── .claude/                # Claude 配置目录
├── .42cog/                 # 认知敏捷法文档
│   ├── meta/
│   ├── real/
│   ├── cog/
│   ├── spec/
│   │   ├── pm/
│   │   └── dev/
│   └── work/
├── 前置准备/               # 调研文档（从阶段0复制）
│   ├── 技术栈与MCP清单.md
│   ├── DOMAIN_MODEL.md
│   ├── YOUTUBE_CONTENT_CREATION_PIPELINE.md
│   └── PROMPT_TEMPLATES.md
├── prompts/                # 提示词模板（从阶段0复制）
│   ├── PROMPT_00_前置准备.md
│   ├── PROMPT_01_项目初始化.md
│   ├── PROMPT_02_调研阶段.md
│   ├── PROMPT_03_策划阶段.md
│   ├── PROMPT_04_制作阶段.md
│   ├── PROMPT_05_发布阶段.md
│   └── PROMPT_06_复盘阶段.md
├── src/
│   ├── research/           # 调研模块
│   ├── planning/           # 策划模块
│   ├── production/         # 制作模块
│   ├── publishing/         # 发布模块
│   ├── analytics/          # 复盘模块
│   └── shared/             # 共享模块
│       ├── models/         # 数据模型
│       ├── database/       # 数据库操作
│       ├── utils/          # 工具函数
│       └── config/         # 配置管理
├── data/
│   ├── videos/             # 视频文件
│   ├── audio/              # 音频文件
│   ├── transcripts/        # 字幕文件
│   ├── assets/             # 素材
│   ├── reports/            # 报告
│   └── cache/              # 缓存
├── config/
│   ├── settings.yaml       # 主配置
│   └── storage.yaml        # 存储策略配置
├── scripts/                # 辅助脚本
├── logs/                   # 日志目录
├── cli.py                  # CLI 入口
├── requirements.txt        # Python 依赖
├── CLAUDE.md               # 项目级 Claude 配置
└── README.md
```

### 2. 初始化 Git 仓库
```bash
git init
```

### 3. 创建 .gitignore
包含以下忽略项：
- 系统文件：.DS_Store
- Python：.venv/, __pycache__/, *.pyc
- Node.js：node_modules/, bun.lockb
- 数据文件：data/videos/, data/audio/, data/cache/, *.mp4, *.mp3, *.webm
- 环境变量：.env, .env.local, config/secrets.yaml
- 日志：logs/, *.log

### 4. 创建 CLAUDE.md（中文版）

### 5. 安装 Python 依赖
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 6. 验证 42cog 目录结构

完成后提供初始化状态报告。
```

---

### 模板 1.2：验证环境安装

```
请帮我验证 YouTube 内容创作流水线的开发环境是否正确安装。

参考技术栈文档：前置准备/2026-01-17-技术栈与MCP清单.md

## 验证项目

### 系统工具
- [ ] yt-dlp --version (要求 ≥2025.1.0)
- [ ] ffmpeg -version (要求 ≥6.0)
- [ ] whisper --version (或全局已安装)
- [ ] git --version

### Python 环境
- [ ] python3 --version (要求 ≥3.10)
- [ ] uv --version
- [ ] 虚拟环境已激活

### Python 包
- [ ] whisper 已安装
- [ ] playwright 已安装
- [ ] pyautogui 已安装
- [ ] click 已安装
- [ ] sqlalchemy 已安装

### 42cog 目录结构
- [ ] .42cog/meta/ 目录存在
- [ ] .42cog/spec/pm/ 目录存在
- [ ] .42cog/spec/dev/ 目录存在
- [ ] .42cog/work/ 目录存在

请逐项检查并报告结果。如有缺失，提供安装命令。
```

---

### 模板 1.3：安装缺失依赖

```
请帮我安装以下缺失的依赖：

[列出缺失的依赖]

参考安装命令（来自 前置准备/2026-01-17-技术栈与MCP清单.md）：

## 系统工具
```bash
brew install yt-dlp ffmpeg imagemagick git
```

## Python 依赖
```bash
uv pip install openai-whisper playwright pyautogui click rich pyyaml sqlalchemy httpx aiohttp python-dotenv
playwright install chromium
```

安装完成后验证每个工具是否正常工作。
```

---

## 产出文档

| 文档 | 路径 | 说明 |
|------|------|------|
| CLAUDE.md | `./CLAUDE.md` | 项目级 Claude 配置 |
| .gitignore | `./.gitignore` | Git 忽略文件 |
| requirements.txt | `./requirements.txt` | Python 依赖清单 |
| settings.yaml | `./config/settings.yaml` | 主配置文件 |

---

## 需要更新的文档

| 文档 | 更新内容 |
|------|----------|
| `.42cog/meta/meta.md` | 填写项目元信息 |
| `.42cog/work/` | 记录初始化过程 |

---

## 检查清单

- [ ] 目录结构已创建
- [ ] Git 仓库已初始化
- [ ] .gitignore 已配置
- [ ] CLAUDE.md 已创建
- [ ] 系统工具已安装
- [ ] Python 环境已配置
- [ ] 42cog 目录结构完整

---

## 下一步

完成初始化后，进入 **阶段 2：调研阶段**。

---

*文档版本: 1.1*
*更新日期: 2026-01-18*
