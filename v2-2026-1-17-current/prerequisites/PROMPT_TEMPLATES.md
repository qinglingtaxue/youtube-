# YouTube 内容创作流水线 - 提示词模板

> 基于 42COG 认知敏捷法的项目初始化与开发指南

---

## 1. 项目初始化

请使用 Claude Code 对我的 YouTube 内容创作流水线项目进行完整初始化，包括以下步骤：

### 第一步：创建并配置 CLAUDE.md 文件

- 将 CLAUDE.md 文件内容翻译为中文
- 在文件中添加以下个人环境信息：
  - **设备**：搭载 Apple 芯片的 Mac 电脑
  - **Python 环境**：通过 uv 配置
  - **Node.js 管理**：通过 bun 进行安装管理
  - **Git代码托管平台**：cnb.cool
- 请确保所有后续沟通和回复都使用中文

### 第二步：初始化 Git 仓库

- 初始化 Git 仓库

### 第三步：创建完整的 .gitignore 文件

需要包含以下忽略项：

#### 系统文件
- `.DS_Store`

#### Python 相关
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`
- `*.pyo`

#### Node.js 相关
- `node_modules/`
- `bun.lockb`

#### 数据文件（不提交到仓库）
- `data/videos/`
- `data/assets/`
- `data/cache/`
- `*.mp4`
- `*.mp3`
- `*.webm`
- `*.mkv`

#### 环境变量
- `.env`
- `.env.local`
- `config/secrets.yaml`

#### 日志
- `logs/`
- `*.log`

### 第四步：提供项目初始化状态报告

完成上述所有设置后，请提供一个清晰的项目初始化状态报告。

---

## 2. 检查 42plugin 插件（已通过软链接安装）

> **注意**：使用 `42plugin install` 安装的插件会自动在 `.claude/` 目录下创建软链接，无需手动注册。

请检查 `.claude/` 目录下已安装的插件软链接是否正常：

```bash
# 检查软链接状态
ls -la .claude/skills/
ls -la .claude/agents/
ls -la .claude/hooks/
ls -la .claude/commands/
```

**已安装的核心插件（69个）**：

| 类型 | 数量 | 核心插件 |
|------|------|----------|
| Skills | 45 | youtube-downloader, youtube-transcript, content-creator, ideation, spec-generator |
| Agents | 11 | orchestrator, marketing, seo-content-writer, research-planning |
| Commands | 10 | viral-automation, website-automation, review |
| Hooks | 3 | blog-workflow, smart_agent_selection, development-workflow |

**如需添加新插件**：
```bash
cd youtube-plugin-workspace
42plugin install <author>/<repo>/<plugin-name>
```

**配置 settings.local.json**（如有自定义需求）：
```json
{
  "permissions": {
    "allow": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
  }
}
```

---

## 3. 填写项目元信息

请根据下列内容，填写 `.42cog/meta/meta.md`：

**项目名称**：YouTube 内容创作流水线（YouTube Content Pipeline）

**项目描述**：一个基于 42COG 认知敏捷法的端到端 YouTube 内容创作自动化工具链。支持从市场调研、内容策划、视频制作到自动发布和效果复盘的完整工作流。采用综合模式（AI 理解 + RPA 执行 + Playwright 验收）实现高效低成本的自动化。

**核心价值**：
- 统一的 5 阶段工作流（调研→策划→制作→发布→复盘）
- 低 Token 消耗的综合执行模式
- 基于 42plugin 的模块化能力扩展
- 支持批量处理和定时发布

**作者**：[你的名字]
**仓库地址**：[你的仓库地址]

---

## 4. 生成现实约束和认知模型

请使用已经注册好的 Claude Skill：`.claude/skills/spec-generator/SKILL.md`

生成 `real.md` 与 `cog.md`，中文版。注意，如果以前有内容，直接备份在同文件夹后（加上日期后）替换。

**现实约束 (real.md) 要点**：
- YouTube API 限制（每日配额）
- 视频文件大小限制（最大 256GB）
- 上传频率限制（避免被封号）
- Token 成本控制（综合模式优先）
- 网络环境限制（可能需要代理）
- 版权合规（素材来源需合法）
- 隐私保护（不存储敏感信息）

**认知模型 (cog.md) 要点**：
参考已生成的 `DOMAIN_MODEL.md` 中的 24 个实体定义。

---

## 5. 生成产品需求规格书

请使用已经注册好的 Claude Skill：`.claude/skills/content-creator/SKILL.md`

生成产品需求规格书：`pr.spec.md`，放在：`.42cog/spec/pm/` 目录下面。

注意参考：
- `.42cog/real/real.md`
- `.42cog/cog/cog.md`
- `DOMAIN_MODEL.md`
- `YOUTUBE_CONTENT_CREATION_PIPELINE.md`

**核心功能需求**：

1. **调研模块**
   - YouTube 视频搜索和数据抓取
   - 竞品视频下载和分析
   - 标签/关键词统计

2. **策划模块**
   - 基于调研的内容规划
   - 脚本生成和 SEO 优化
   - 三事件结构规约生成

3. **制作模块**
   - 素材管理
   - 配音生成（TTS）
   - 字幕处理
   - 视频合成

4. **发布模块**
   - YouTube Studio 自动化上传
   - 元数据填写（标题/描述/标签）
   - 定时发布
   - 封面上传

5. **复盘模块**
   - 数据追踪
   - 效果分析报告
   - 策略迭代建议

---

## 6. 生成系统架构规格书

请使用已经注册好的 Claude Skill：`.claude/skills/spec-generator/SKILL.md`

生成 `sys.spec.md`，放在：`.42cog/spec/dev/` 目录下面。

注意参考：
- `.42cog/real/real.md`
- `.42cog/cog/cog.md`
- `.42cog/spec/pm/pr.spec.md`

**技术栈**：

| 层级 | 技术选型 |
|------|----------|
| 编程语言 | Python 3.10+ |
| 包管理 | uv |
| 视频下载 | yt-dlp |
| 音视频处理 | FFmpeg |
| 语音识别 | openai-whisper |
| 浏览器自动化 | Playwright / mcp-chrome |
| RPA | PyAutoGUI |
| 配置管理 | YAML |
| CLI | Click / Typer |

**目录结构**：
```
youtube-content-pipeline/
├── .claude/                # 42plugin 插件
├── .42cog/                 # 认知敏捷法文档
├── src/
│   ├── research/           # 调研模块
│   ├── planning/           # 策划模块
│   ├── production/         # 制作模块
│   ├── publishing/         # 发布模块
│   ├── analytics/          # 复盘模块
│   └── shared/             # 共享模块
├── data/                   # 数据目录
├── config/                 # 配置文件
├── scripts/                # 辅助脚本
└── cli.py                  # CLI 入口
```

---

## 7. 生成数据模型规格书

请使用已经注册好的 Claude Skill：`.claude/skills/spec-generator/SKILL.md`

生成 `db.spec.md`，放在：`.42cog/spec/dev/` 目录下面。

注意参考：
- `DOMAIN_MODEL.md`（24 个实体、26 个关系、27 个枚举）
- `.42cog/cog/cog.md`

**数据存储方案**：
- 使用 SQLite 作为本地数据库（轻量、无需服务器）
- 使用 SQLAlchemy 作为 ORM
- 视频/音频等大文件存储在本地文件系统

---

## 8. 实现调研模块

请使用已经注册好的 Claude Skill：`.claude/skills/youtube-downloader/SKILL.md` 和 `.claude/skills/youtube-transcript/SKILL.md`

实现 `src/research/` 模块，包括：

1. **youtube_fetcher.py** - YouTube 数据抓取
   - 基于关键词搜索视频
   - 获取视频元数据（标题、描述、标签、观看数等）
   - 支持分页和批量抓取

2. **competitor_analyzer.py** - 竞品分析
   - 下载竞品视频
   - 提取字幕/转录
   - 分析视频结构

3. **tag_collector.py** - 标签收集
   - 统计标签频率
   - 分类（高频/中频/长尾）
   - 生成标签矩阵

注意参考：
- `.42cog/spec/dev/sys.spec.md`
- 已有的 `youtube-content-creation-workflow/scripts/` 中的实现

---

## 9. 实现策划模块

请使用已经注册好的 Claude Skill：`.claude/skills/content-creator/SKILL.md` 和 `.claude/skills/ideation/SKILL.md`

实现 `src/planning/` 模块，包括：

1. **script_generator.py** - 脚本生成
   - 基于调研数据生成内容大纲
   - 三事件结构（引入→展开→总结）
   - 支持多种视频风格模板

2. **seo_optimizer.py** - SEO 优化
   - 标题优化
   - 描述优化
   - 标签推荐

3. **spec_builder.py** - 规约构建
   - 生成 42COG 格式的视频规约
   - 包含目标时长、风格、关键要点

注意参考：
- `.claude/skills/content-creator/references/` 下的参考文档
- `.claude/skills/content-creator/scripts/` 下的 Python 工具

---

## 10. 实现制作模块

请实现 `src/production/` 模块，包括：

1. **asset_manager.py** - 素材管理
   - 素材导入和分类
   - 元数据管理
   - 授权信息记录

2. **voiceover_generator.py** - 配音生成
   - 集成 ElevenLabs API
   - 集成 MiniMax TTS
   - 本地 Whisper TTS 备选

3. **subtitle_processor.py** - 字幕处理
   - VTT/SRT 格式转换
   - 时间轴调整
   - 使用 transcript-fixer skill 修复

4. **video_composer.py** - 视频合成
   - FFmpeg 命令封装
   - 音视频合并
   - 字幕烧录

注意参考：
- `.claude/skills/youtube-downloader/SKILL.md` 中的 FFmpeg 用法
- `.claude/skills/transcript-fixer/SKILL.md`

---

## 11. 实现发布模块

请使用已经注册好的 Claude Skill：`.claude/agents/orchestrator.md`

实现 `src/publishing/` 模块，采用**综合模式**：

1. **upload_config_generator.py** - 配置生成（AI 层）
   - 解析用户意图
   - 生成结构化上传配置 JSON
   - Token 消耗：~1,000

2. **rpa_executor.py** - RPA 执行（执行层）
   - 使用 PyAutoGUI 自动化操作
   - 按固化脚本执行上传
   - Token 消耗：0

3. **playwright_verifier.py** - Playwright 验收（验收层）
   - 检查上传状态
   - 验证元数据填写
   - 失败时触发重新探索

4. **scheduler.py** - 定时发布
   - 发布计划管理
   - 定时任务调度

注意参考：
- `youtube-minimal-video-story/2026-01-09-决策-为什么放弃纯Playwright采用综合模式.md`
- `youtube-minimal-video-story/youtube_automation/`

---

## 12. 实现复盘模块

请实现 `src/analytics/` 模块，包括：

1. **data_tracker.py** - 数据追踪
   - YouTube Analytics API 集成（可选）
   - mcp-chrome 抓取 YouTube Studio 数据
   - 关键指标：观看数、CTR、平均观看时长

2. **report_generator.py** - 报告生成
   - 7 日/30 日效果报告
   - 对比分析
   - 改进建议

注意参考：
- `.claude/hooks/blog-workflow/` 的 Hook 模式
- `info-analysis-workflow/` 中的分析模板

---

## 13. 实现 CLI 入口

请实现 `cli.py`，提供统一的命令行接口：

```bash
# 调研命令
ytpipe research --keyword "AI教程" --limit 50

# 策划命令
ytpipe plan --input research_report.json --style tutorial

# 制作命令
ytpipe produce --spec video_spec.md --output output/

# 发布命令
ytpipe publish --video output/video.mp4 --config upload_config.json

# 复盘命令
ytpipe analyze --video-id VIDEO_ID --period 7d

# 完整工作流
ytpipe workflow --keyword "AI教程" --auto
```

使用 Click 或 Typer 框架实现。

---

## 14. 质量保证

请使用已经注册好的 Claude Skill 或直接实现测试：

1. **单元测试**
   - 使用 pytest
   - 覆盖核心模块

2. **集成测试**
   - 测试完整工作流
   - 使用 mock 数据

3. **端到端测试**
   - 使用 Playwright 测试发布流程
   - 验收标准检查

---

## 15. 文档完善

请生成以下文档：

1. **README.md** - 项目说明
   - 功能介绍
   - 快速开始
   - 配置说明

2. **INSTALL.md** - 安装指南
   - 依赖安装
   - 环境配置
   - 常见问题

3. **USAGE.md** - 使用指南
   - 命令详解
   - 工作流示例
   - 最佳实践

---

## 参考文档清单

```
.42cog/
├── meta/meta.md           # 项目元信息
├── real/real.md           # 现实约束
├── cog/cog.md             # 认知模型
└── spec/
    ├── pm/
    │   ├── pr.spec.md     # 产品需求
    │   └── userstory.spec.md  # 用户故事
    └── dev/
        ├── sys.spec.md    # 系统架构
        ├── db.spec.md     # 数据模型
        └── code.spec.md   # 编码规范

YOUTUBE_CONTENT_CREATION_PIPELINE.md  # 流水线设计
DOMAIN_MODEL.md                       # 领域模型
```

---

## 快速启动模板

### 一键初始化（复制使用）

```
请帮我初始化 YouTube 内容创作流水线项目。

1. 创建项目目录结构（参考 YOUTUBE_CONTENT_CREATION_PIPELINE.md）
2. 初始化 Git 仓库和 .gitignore
3. 配置 CLAUDE.md（中文，Mac + uv + bun）
4. 创建 .42cog 目录结构
5. 安装 Python 依赖（uv）
6. 验证 42plugin 插件已注册

完成后提供初始化报告。
```

### 快速调研（复制使用）

```
请使用 youtube-downloader 和 youtube-transcript skill，
对关键词 "[你的关键词]" 进行 YouTube 市场调研。

要求：
1. 搜索前 50 个相关视频
2. 提取标签和关键词
3. 下载 Top 3 视频的字幕
4. 生成调研报告到 data/reports/
```

### 快速发布（复制使用）

```
请使用综合模式将视频上传到 YouTube。

视频文件：[视频路径]
标题：[视频标题]
描述：[视频描述]
标签：[标签1, 标签2, ...]
隐私：public
定时发布：[可选，如 2026-01-20 10:00]

请：
1. 生成上传配置 JSON
2. 启动 mcp-chrome
3. 执行 RPA 上传
4. 验收上传结果
```

---

*模板版本: 1.0*
*更新日期: 2026-01-17*
