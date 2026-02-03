# YouTube 内容创作流水线

## 经验索引

| 文档 | 内容 | 什么时候查 |
|------|------|------------|
| `.42cog/work/EXPERIENCE_INDEX.md` | 踩过的坑、积累的经验 | 踩坑了 / 似曾相识 / 大改动前 |
| `.42cog/work/tech-decisions.md` | 技术选型决策 | 集成第三方库时 |
| `.42cog/work/关键决策参考.md` | 架构决策 | 项目结构调整时 |

**踩坑后**：更新对应文档，把新经验加进去。

---

## Cog 同步检查规则

### 重大任务前必须同步检查

当准备执行以下任务时，**先运行 cog 同步检查**：
- 设计新功能
- 编写新的 spec 文档
- 创建新的数据模型/类
- 重构现有代码架构

执行命令：
```bash
python scripts/sync_cog_from_code.py --mode=check
```

如果发现不一致，先更新 cog 再继续任务。

### 新实体发现规则

当工作中发现满足以下条件的概念时，应建议更新 cog：
1. 有独立的唯一编码（可作为主键）
2. 有明确的输入/输出
3. 在多个地方被引用
4. 不是已有实体的属性变体

发现后，在任务末尾输出：
> 🆕 发现潜在新实体：[名称]
> - 来源：[文件:行号]
> - 理由：[为什么是新实体而非属性]
> - 建议：运行 `python scripts/sync_cog_from_code.py --mode=suggest`

### 同步命令速查

| 命令 | 作用 |
|------|------|
| `--mode=check` | 只检查，报告差异 |
| `--mode=suggest` | 检查并生成更新建议 |
| `--mode=full` | 完整同步，更新 cog.md |
| `--quiet` | 静默模式，只在有差异时输出 |

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

### ⚠️ 踩坑经验速查（2026-01-17 ~ 2026-01-28 总结）

| 问题类型 | 关键约束 | 相关 Skill |
|----------|----------|-----------|
| 时间过滤失效 | 必须使用 YouTube 原生 sp 参数 | data-collector |
| **数据阶段混淆** | 先判断阶段：设计验证→模拟数据OK，准确性校验→必须真实数据，压力测试→生成数据 | data-validator |
| 链接点不开 | 必须验证链接可访问性 | data-validator |
| 气泡图溢出 | 设置 max-width/max-height | visualization |
| 排序无差别 | 每个指标必须有不同计算公式 | research-report |
| 关键词随意 | 必须来自用户行为数据 | data-collector |
| 进度不明 | 长操作必须显示进度 | youtube-downloader |
| **频道数据重复** | 渲染前必须按 channel_id 去重 | visualization |
| **图表XY轴搞反** | 先确认：X轴是什么？Y轴是什么？ | visualization |
| **图表类型选错** | 散点图≠折线图≠柱状图，先问用户要哪种 | visualization |
| **数据字段选错** | 先用 `SELECT DISTINCT field, COUNT(*)` 检查数据分布 | data-validator |
| **位置理解偏差** | "右侧"有歧义，先确认：页面右侧 or 某元素右侧？ | - |

### 📊 数据阶段判断（写代码前必做）

| 阶段 | 信号词 | 数据来源 | 规则 |
|------|--------|----------|------|
| 设计验证 | 效果、布局、UI、原型 | 模拟数据 | 值可假，结构必须真 |
| 准确性校验 | 验证、检查、真实、数据对不对 | 真实数据库 | 禁止任何硬编码 |
| 压力测试 | 性能、扩展、大量、未来 | 生成数据 | 基于真实分布放大 |

**默认阶段**：准确性校验（不确定时问用户）

### 📚 工作文档索引

#### 技术决策文档（TD-xx）

| 编号 | 文档 | 内容 | 什么时候查 |
|------|------|------|------------|
| TD-01 | `work/01-启动YouTube内容创作流水线项目.md` | 项目启动背景 | 了解项目初衷 |
| TD-02 | `work/02-确定软件设计理念与迭代方向.md` | 设计理念 | 架构决策时 |
| TD-03 | `work/03-采用cog-real文档规范体系.md` | 文档规范 | 写文档时 |
| TD-04 | `work/04-采用RPA固化脚本矩阵架构.md` | RPA架构选型 | 自动化决策时 |
| TD-05 | `work/05-设计pipeline规约生成机制.md` | Pipeline设计 | 流水线开发时 |
| TD-06 | `work/06-选择NextJS作为前端技术栈.md` | 前端选型 | 前端开发时 |
| TD-07 | `work/07-确定多页面交互系统架构.md` | 页面架构 | UI设计时 |
| TD-08 | `work/08-定义爆款潜力热门视频标签体系.md` | 标签体系 | 视频分类时 |
| TD-09 | `work/09-设计视频频道榜单筛选维度.md` | 榜单维度 | 榜单功能开发时 |
| TD-10 | `work/10-确定信息采集分组与指标图示化方案.md` | 指标可视化 | 图表开发时 |
| TD-11 | `work/11-调整爆款Top50判定标准.md` | 爆款标准 | 排名算法时 |
| TD-12 | `work/12-确定时间维度采集范围.md` | 时间范围 | 数据采集时 |
| TD-13 | `work/13-确定采集关键词逻辑与近期视频筛选规则.md` | 关键词逻辑 | 采集策略调整时 |
| TD-14 | `work/14-增加进度预估与网络速度显示功能.md` | 进度显示 | 长操作UX时 |
| TD-15 | `work/15-采用YouTube原生搜索过滤机制.md` | 时间过滤 | 搜索功能开发时 |
| TD-16 | `work/16-有趣度评估框架设计.md` | 有趣度公式 | 评估模式价值时 |
| TD-17 | `work/17-跨语言套利空间计算方法.md` | 跨境价值 | 多语言分析时 |
| TD-18 | `work/18-外部CPM数据引入.md` | CPM数据源 | 收益估算时 |
| TD-19 | `work/19-Chart.js散点图X轴标签不显示问题.md` | Chart.js踩坑 | 图表显示异常时 |
| TD-20 | `work/20-榜单功能开发经验总结.md` | 榜单开发经验 | 榜单功能开发时 |

#### 模式洞察文档

| 文档 | 内容 | 什么时候查 |
|------|------|------------|
| `work/模式洞察.md` | 模式洞察主文档 | 理解模式分析体系 |
| `work/模式洞察-索引.md` | 23个模式的索引 | 快速定位模式 |
| `work/模式洞察-数据基础.md` | 数据源和字段说明 | 开发模式功能时 |
| `work/模式洞察-评估方法.md` | 模式评估标准 | 评估模式价值时 |
| `work/模式洞察-行动指南.md` | 可操作的建议 | 指导用户行动时 |
| `work/模式洞察-候补模式.md` | 待开发的模式 | 规划新功能时 |

**按维度分组**：

| 维度 | 数据文档 | 方法文档 | 输出文档 |
|------|----------|----------|----------|
| 时间 | `模式洞察-时间维度-数据.md` | `模式洞察-时间维度-方法.md` | `模式洞察-时间维度-输出.md` |
| 空间 | `模式洞察-空间维度-数据.md` | `模式洞察-空间维度-方法.md` | `模式洞察-空间维度-输出.md` |
| 频道 | `模式洞察-频道维度-数据.md` | `模式洞察-频道维度-方法.md` | `模式洞察-频道维度-输出.md` |
| 用户 | `模式洞察-用户维度-数据.md` | `模式洞察-用户维度-方法.md` | `模式洞察-用户维度-输出.md` |
| 变量 | `模式洞察-变量分布-数据.md` | `模式洞察-变量分布-方法.md` | `模式洞察-变量分布-输出.md` |

#### 操作指南

| 文档 | 内容 | 什么时候查 |
|------|------|------------|
| `work/采集指令.md` | 数据采集命令 | 手动采集时 |
| `work/采集逻辑.md` | 采集策略说明 | 理解采集机制时 |
| `work/可视化图表设计方案.md` | 图表设计规范 | 图表开发时 |
| `work/信息报告ui 设计提示词优化.md` | UI设计提示词 | 优化UI时 |

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
