# 阶段 2：调研阶段 (Research)

**前置条件**: 已完成 [阶段 1：项目初始化](./PROMPT_01_项目初始化.md)

> 收集目标领域的 YouTube 内容数据，了解市场趋势和竞品

---

## 经验索引

> 📄 `.42cog/work/EXPERIENCE_INDEX.md`

**什么时候查**：踩坑了 / 这个问题之前好像遇到过 / 要做影响范围大的改动

---

## 规格引用

> ⚠️ **本提示词是规格的执行器，执行前请确认符合以下规格：**

| 规格文档 | 引用章节 | 用途 |
|----------|----------|------|
| `.42cog/spec/pm/pipeline.spec.md` | Stage 1: Research | 输入输出契约、前置后置条件 |
| `.42cog/cog/cog.md` | WorkflowStage, CompetitorVideo | 实体定义和状态 |
| `.42cog/real/real.md` | #3 API/自动化限制, #4 存储与成本控制 | 约束检查 |

### 执行前检查 (来自 pipeline.spec.md)

```yaml
preconditions:
  - yt-dlp --version >= 2025.1.0
  - YouTube API 配额充足 (剩余 > 1000 单位)
  - 磁盘剩余空间 > 10GB
```

---

## 阶段目标

- 基于关键词搜索和收集 YouTube 视频数据
- 下载并分析竞品视频
- 提取字幕/转录内容
- 统计标签和关键词
- 生成市场调研报告

---

## 技术栈参考

📄 **参考文档**：`.42cog/work/2026-01-17-技术栈与MCP清单.md`

### 本阶段需要的工具

| 工具 | 用途 | 验证命令 |
|------|------|----------|
| yt-dlp | 视频/字幕下载 | `yt-dlp --version` |
| Whisper | 语音转文字 | `whisper --help` |
| SQLite | 元数据存储 | `sqlite3 --version` |
| FFmpeg | 音频提取 | `ffmpeg -version` |

### 本阶段需要的 MCP

| MCP | 必要性 | 用途 |
|-----|--------|------|
| mcp-server-fetch | ✅ 推荐 | 抓取网页内容（频道信息、评论等） |
| tavily | ⚠️ 可选 | 实时搜索热门话题 |

---

## Skill

> 查阅 `CLAUDE.md`「Skill 调用规则」，按用户意图自动调用对应 skill。

本阶段常用：`youtube-downloader`、`youtube-transcript`、`youtube-to-markdown`、`article-extractor`

---

## 提示词模板

### 模板 1.1：关键词调研

```
请帮我对 "[关键词]" 进行 YouTube 市场调研。

## 调研范围
- 搜索前 50 个相关视频
- 时间范围：最近 3 个月

## 收集数据
- 视频标题、描述、标签
- 观看数、点赞数、评论数
- 频道名称、订阅数
- 发布日期、视频时长

## 分析维度
1. 热门话题：哪些主题观看量最高？
2. 标签分析：高频标签有哪些？
3. 时长分布：热门视频的时长集中在哪个区间？
4. 发布频率：头部创作者的更新频率是？

## 输出要求
- 调研报告：`data/reports/research_[关键词]_YYYYMMDD.md`
- 视频清单：`data/reports/videos_[关键词]_YYYYMMDD.csv`
- 标签矩阵：`data/reports/tags_[关键词]_YYYYMMDD.json`

注意：使用 yt-dlp 命令行工具，参考技术栈文档中的配置。
```

---

### 模板 1.2：竞品视频分析

```
请帮我分析这个竞品视频：[VIDEO_URL]

## 分析任务

### 1. 下载视频（可选）
- 使用 youtube-downloader skill
- 格式：1080p 或最高可用
- 保存到：`data/videos/`

### 2. 提取字幕
- 使用 youtube-transcript skill
- 优先顺序：手动字幕 > 自动字幕 > Whisper 转录
- 保存到：`data/transcripts/`

### 3. 内容分析
- 视频结构（开头/中间/结尾）
- 核心论点
- 引用来源
- CTA（行动号召）

### 4. 技术分析
- 封面设计特点
- 视频时长和节奏
- 剪辑风格

## 输出要求
- 分析报告：`data/reports/competitor_[VIDEO_ID]_YYYYMMDD.md`
- 字幕文件：`data/transcripts/[VIDEO_ID].vtt`

## 参考命令
```bash
# 下载视频
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" "[VIDEO_URL]" -o "data/videos/%(id)s.%(ext)s"

# 下载字幕
yt-dlp --write-auto-sub --sub-lang zh,en --skip-download "[VIDEO_URL]" -o "data/transcripts/%(id)s"

# Whisper 转录（无字幕时）
whisper "data/videos/[VIDEO_ID].mp4" --model base --output_format vtt --output_dir data/transcripts/
```
```

---

### 模板 1.3：批量标签收集

```
请帮我收集和分析 "[关键词]" 领域的 YouTube 标签。

## 数据来源
1. 搜索 "[关键词]" 获取前 100 个视频
2. 提取每个视频的标签

## 分析要求
- 高频标签（出现 >10 次）
- 中频标签（5-10 次）
- 长尾标签（<5 次）
- 标签共现关系

## 输出
- 标签统计：`data/reports/tags_analysis_YYYYMMDD.json`
- 标签词云数据：`data/reports/tags_wordcloud_YYYYMMDD.json`

## 格式示例
```json
{
  "high_frequency": [
    {"tag": "AI教程", "count": 45},
    {"tag": "人工智能", "count": 38}
  ],
  "medium_frequency": [...],
  "long_tail": [...],
  "cooccurrence": {
    "AI教程": ["机器学习", "深度学习", "Python"],
    ...
  }
}
```
```

---

### 模板 1.4：趋势追踪（需要 tavily MCP）

```
请帮我追踪 "[领域]" 在 YouTube 上的最新趋势。

## 使用工具
- tavily MCP（实时搜索）
- mcp-server-fetch（抓取详情）

## 追踪内容
1. 最近一周的热门视频
2. 新兴话题和关键词
3. 行业新闻和事件
4. 算法推荐趋势

## 输出
- 趋势报告：`data/reports/trend_[领域]_YYYYMMDD.md`
```

---

## 产出文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 市场调研报告 | `data/reports/research_*.md` | 调研结果汇总 |
| 视频清单 | `data/reports/videos_*.csv` | 视频元数据列表 |
| 标签矩阵 | `data/reports/tags_*.json` | 标签分类和统计 |
| 竞品分析 | `data/reports/competitor_*.md` | 单个视频深度分析 |
| 字幕文件 | `data/transcripts/*.vtt` | 提取的字幕 |

---

## 需要更新的文档

| 文档 | 更新内容 |
|------|----------|
| `.42cog/work/` | 记录调研过程和发现 |
| `data/` 目录 | 存储调研数据 |

---

## 数据库操作

调研数据应存入 SQLite 数据库：

```sql
-- 视频元数据
INSERT INTO video (
  video_id, title, description, channel_name,
  view_count, like_count, comment_count,
  duration, published_at
) VALUES (...);

-- 标签关联
INSERT INTO video_tag (video_id, tag_name) VALUES (...);

-- 调研记录
INSERT INTO research (keyword, search_date, video_count) VALUES (...);
```

---

## 检查清单

- [ ] yt-dlp 可正常下载视频和字幕
- [ ] Whisper 可正常转录音频
- [ ] 调研报告已生成
- [ ] 标签矩阵已生成
- [ ] 数据已存入数据库

---

## 后置检查 (来自 pipeline.spec.md)

```yaml
postconditions:
  validation:
    - "ResearchReport 文件存在且非空"
    - "video_count > 0"
    - "至少采集 10 个有效视频元数据"
  quality:
    - "报告包含热门话题分析"
    - "报告包含标签分布统计"
    - "报告包含竞品清单 (top 10)"
```

---

## 下一步

完成调研后，进入 **阶段 3：策划阶段**，基于调研数据规划内容。

---

*文档版本: 1.0*
*更新日期: 2026-01-17*
