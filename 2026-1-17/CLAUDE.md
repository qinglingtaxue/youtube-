# YouTube 内容创作流水线

## 经验索引

| 文档 | 内容 | 什么时候查 |
|------|------|------------|
| `.42cog/work/EXPERIENCE_INDEX.md` | 踩过的坑、积累的经验 | 踩坑了 / 似曾相识 / 大改动前 |
| `.42cog/work/tech-decisions.md` | 技术选型决策 | 集成第三方库时 |
| `.42cog/work/关键决策参考.md` | 架构决策 | 项目结构调整时 |

**踩坑后**：更新对应文档，把新经验加进去。

---

## Skill 调用规则

遇到以下场景时，自动使用对应 skill：

### 核心 Skill（基于踩坑经验，优先级高）

| 用户意图 | 调用 Skill | 路径 | 说明 |
|----------|------------|------|------|
| **采集 YouTube 数据** | data-collector | `.claude/skills/data-collector.md` | 包含时间过滤、重试机制、关键词来源规约 |
| **验证数据质量** | data-validator | `.claude/skills/data-validator.md` | 链接验证、完整性检查、真实性验证 |
| **生成可视化图表** | visualization | `.claude/skills/visualization.md` | 防溢出规约、极端数据测试、交互设计 |
| 生成调研报告 | research-report | `.claude/skills/research-report.md` | 包含指标计算公式、链接验证 |

### 常规 Skill

| 用户意图 | 调用 Skill | 路径 |
|----------|------------|------|
| 下载 YouTube 视频 | youtube-downloader | `.claude/skills/youtube-downloader.md` |
| 提取字幕/获取文稿 | youtube-transcript | `.claude/skills/youtube-transcript.md` |
| 获取视频元数据 | youtube-to-markdown | `.claude/skills/youtube-to-markdown.md` |
| 提取网页文章 | article-extractor | `.claude/skills/article-extractor.md` |
| 分析品牌声音/SEO优化 | content-creator | `.claude/skills/content-creator.md` |
| 头脑风暴/创意构思 | ideation | `.claude/skills/ideation.md` |
| 生成视频规约 | spec-generator | `.claude/skills/spec-generator.md` |
| 修复/优化字幕 | transcript-fixer | `.claude/skills/transcript-fixer.md` |
| 处理音视频/合成视频 | media-processing | `.claude/skills/media-processing.md` |

**使用方式**：读取 skill 文件，按其中的步骤和约束执行。

### ⚠️ 踩坑经验速查（2026-01-17 ~ 2026-01-20 总结）

| 问题类型 | 关键约束 | 相关 Skill |
|----------|----------|-----------|
| 时间过滤失效 | 必须使用 YouTube 原生 sp 参数 | data-collector |
| 模拟数据问题 | 禁止用模拟数据，无数据显示 0 | research-report |
| 链接点不开 | 必须验证链接可访问性 | data-validator |
| 气泡图溢出 | 设置 max-width/max-height | visualization |
| 排序无差别 | 每个指标必须有不同计算公式 | research-report |
| 关键词随意 | 必须来自用户行为数据 | data-collector |
| 进度不明 | 长操作必须显示进度 | youtube-downloader |

---

## 项目概述

YouTube 内容创作全流程自动化工具，五个阶段：调研 → 策划 → 制作 → 发布 → 复盘

## 技术栈

| 类型 | 工具 |
|------|------|
| 语言 | Python 3.10+ |
| 包管理 | uv |
| Node.js | bun |
| 视频下载 | yt-dlp |
| 音视频处理 | ffmpeg |
| 图像处理 | imagemagick |
| 语音转文字 | whisper |
| 浏览器自动化 | playwright |

## 目录结构

```
├── src/                    # 代码
│   ├── research/           # 调研
│   ├── planning/           # 策划
│   ├── production/         # 制作
│   ├── publishing/         # 发布
│   ├── analytics/          # 复盘
│   └── shared/             # 共享
├── data/                   # 数据（gitignore）
├── config/                 # 配置
├── prompts/                # 提示词模板
├── .42cog/                 # 认知敏捷法文档
│   ├── work/               # 工作文档、经验索引
│   ├── spec/               # 规约
│   └── ...
└── logs/                   # 日志
```

## 开发规范

- 代码风格：PEP 8
- 类型注解：必须
- 命名：文件 snake_case，类 PascalCase
- 提交：feat/fix/docs/refactor/test/chore

## 常用命令

```bash
source .venv/bin/activate    # 激活环境
python cli.py --help         # CLI
uv pip install -r requirements.txt  # 安装依赖
```

## 注意事项

- 敏感信息：`config/secrets.yaml`（不提交）
- 大文件：`data/`（gitignore）
- 日志：`logs/`
