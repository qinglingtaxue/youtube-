# 阶段 0：前置准备

> 在初始化项目之前，准备好所需的调研文档和模板文件

---

## 经验索引

> 📄 `.42cog/work/EXPERIENCE_INDEX.md`

**什么时候查**：踩坑了 / 这个问题之前好像遇到过 / 要做影响范围大的改动

---

## 目标

- 确认调研文档已完成
- 复制项目模板到工作目录
- 确认系统工具已安装

---

## 需要的调研文档

在初始化之前，确保以下调研文档已准备好：

| 文档 | 路径 | 说明 | 状态 |
|------|------|------|------|
| 技术栈清单 | `前置准备/2026-01-17-技术栈与MCP清单.md` | 工具版本要求、MCP 配置 | [ ] |
| 领域模型 | `前置准备/DOMAIN_MODEL.md` | 业务实体和流程定义 | [ ] |
| 流水线设计 | `前置准备/YOUTUBE_CONTENT_CREATION_PIPELINE.md` | 五阶段工作流设计 | [ ] |
| 提示词模板 | `前置准备/PROMPT_TEMPLATES.md` | 提示词设计参考 | [ ] |

---

## 需要复制的模板

从模板库复制以下文件到项目目录：

```bash
# 创建项目目录
mkdir youtube-content-pipeline
cd youtube-content-pipeline

# 42cog 目录结构模板
cp -r /path/to/template/.42cog ./

# 提示词模板目录
cp -r /path/to/template/prompts ./

# 前置准备文档
mkdir 前置准备
cp /path/to/template/DOMAIN_MODEL.md ./前置准备/
cp /path/to/template/YOUTUBE_CONTENT_CREATION_PIPELINE.md ./前置准备/
cp /path/to/template/PROMPT_TEMPLATES.md ./前置准备/
cp /path/to/template/技术栈与MCP清单.md ./前置准备/

# 42plugin 插件模板（Claude skills/agents/hooks）
cp -r /path/to/template/youtube-plugin-workspace ./
```

| 模板 | 来源 | 用途 |
|------|------|------|
| `.42cog/` | 认知敏捷法模板 | 项目文档结构 |
| `prompts/` | 提示词模板库 | 各阶段提示词 |
| `前置准备/` | 调研文档 | 技术栈、领域模型、流水线设计 |
| `youtube-plugin-workspace/` | 42plugin 插件模板 | Claude skills/agents/hooks |

---

## youtube-plugin-workspace 目录结构

```
youtube-plugin-workspace/
└── .claude/
    ├── agents/      # Claude 代理定义
    ├── commands/    # 自定义命令
    ├── hooks/       # 钩子脚本
    └── skills/      # 技能模块
```

---

## prompts 目录结构

```
prompts/
├── PROMPT_00_前置准备.md      # 本文档
├── PROMPT_01_项目初始化.md    # 环境配置、目录创建
├── PROMPT_02_调研阶段.md      # 竞品分析、热点追踪
├── PROMPT_03_策划阶段.md      # 选题策划、脚本生成
├── PROMPT_04_制作阶段.md      # 视频剪辑、字幕生成
├── PROMPT_05_发布阶段.md      # 自动上传、SEO优化
└── PROMPT_06_复盘阶段.md      # 数据分析、优化建议
```

---

## 系统工具检查

确认以下工具已全局安装：

```bash
# 检查命令
yt-dlp --version      # 要求 ≥2025.1.0
ffmpeg -version       # 要求 ≥6.0
whisper --version     # 语音识别
git --version
python3 --version     # 要求 ≥3.10
uv --version          # Python 包管理
```

如未安装，运行：

```bash
brew install yt-dlp ffmpeg git
```

---

## 检查清单

- [ ] 调研文档已准备（前置准备/）
- [ ] 模板文件已复制（.42cog/, prompts/）
- [ ] 42plugin 插件已复制（youtube-plugin-workspace/）
- [ ] 系统工具已安装
- [ ] 工作目录已创建

---

## 下一步

完成前置准备后，进入 **阶段 1：项目初始化**。

---

*文档版本: 1.0*
*更新日期: 2026-01-18*
