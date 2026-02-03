# 阶段 3：策划阶段 (Planning)

**前置条件**: 已完成 [阶段 2：调研阶段](./PROMPT_02_调研阶段.md)

> 基于调研数据，规划内容策略和脚本

---

## 经验索引

> 📄 `.42cog/work/EXPERIENCE_INDEX.md`

**什么时候查**：踩坑了 / 这个问题之前好像遇到过 / 要做影响范围大的改动

---

## 规格引用

> ⚠️ **本提示词是规格的执行器，执行前请确认符合以下规格：**

| 规格文档 | 引用章节 | 用途 |
|----------|----------|------|
| `.42cog/spec/pm/pipeline.spec.md` | Stage 2: Planning | 输入输出契约、前置后置条件 |
| `.42cog/cog/cog.md` | Script, Spec | 实体定义和状态 |
| `.42cog/real/real.md` | #1 YouTube 社区准则红线, #6 SEO 最佳实践 | 约束检查 |

### 执行前检查 (来自 pipeline.spec.md)

```yaml
preconditions:
  dependencies:
    - stage: research
      status: completed
      outputs: [ResearchReport]
  constraints:
    - "内容主题不违反 YouTube 社区准则"
```

### 输入契约

```yaml
input:
  required:
    - research_report: ResearchReport   # 来自调研阶段
  optional:
    - brand_voice: BrandVoiceConfig     # 品牌声音配置
    - target_duration: integer          # 目标时长 (秒)
    - style: enum                       # 风格: "tutorial" | "story" | "review"
```

---

## 阶段目标

- 分析调研数据，确定内容方向
- 生成视频脚本和大纲
- 优化 SEO（标题、描述、标签）
- 生成 42COG 格式的视频规约

---

## 技术栈参考

📄 **参考文档**：`.42cog/work/2026-01-17-技术栈与MCP清单.md`

### 本阶段需要的工具

| 工具 | 用途 | 说明 |
|------|------|------|
| Claude API | 内容生成 | 通过 Claude Code 调用 |
| Python | 脚本处理 | SEO 分析脚本 |
| YAML | 配置管理 | 视频规约配置 |

### 本阶段不需要 MCP

策划阶段主要是 AI 生成和文档编写，不需要启用 MCP。如需查阅最新文档，可选用 Context7。

---

## Skill

> 查阅 `CLAUDE.md`「Skill 调用规则」，按用户意图自动调用对应 skill。

本阶段常用：`content-creator`、`ideation`、`spec-generator`

---

## 提示词模板

### 模板 2.1：内容策划（基于调研）

```
请基于以下调研数据，规划一个 YouTube 视频的内容策略。

## 调研数据来源
- 调研报告：`data/reports/research_[关键词]_YYYYMMDD.md`
- 标签矩阵：`data/reports/tags_[关键词]_YYYYMMDD.json`

## 目标受众
- 年龄段：[如 25-35 岁]
- 痛点：[如 想学习 AI 但不知从何开始]
- 期望：[如 快速入门、实用技巧]

## 策划要求

### 1. 主题选择
- 基于调研中观看量最高的 3 个话题
- 找出差异化切入点

### 2. 内容结构（三事件结构）
- **事件 1（引入）**：建立问题/痛点（0:00-1:00）
- **事件 2（展开）**：展示解决方案（1:00-6:00）
- **事件 3（总结）**：升华+行动号召（6:00-8:00）

### 3. 视频参数
- 目标时长：8-12 分钟
- 风格：教程型 / 故事型 / 评论型（选一）
- 语言：中文 / 英文

## 输出要求
- 内容策划文档：`.42cog/spec/pm/content_plan_YYYYMMDD.md`

使用 orchestrator agent 协调 marketing 和 seo-content-writer 代理。
```

---

### 模板 2.2：脚本生成

```
请为以下视频主题生成完整脚本。

## 视频信息
- 主题：[视频主题]
- 时长：[如 8-10 分钟]
- 风格：[教程型/故事型/评论型]

## 参考内容
- 内容策划：`.42cog/spec/pm/content_plan_YYYYMMDD.md`
- 竞品分析：`data/reports/competitor_*.md`

## 脚本要求

### 格式
```markdown
## [视频标题]

### 开场（0:00-1:00）
[开场白，建立话题...]

### 第一部分：[小标题]（1:00-3:00）
[内容...]

### 第二部分：[小标题]（3:00-6:00）
[内容...]

### 第三部分：[小标题]（6:00-8:00）
[内容...]

### 结尾（8:00-8:30）
[总结 + CTA...]
```

### 要点
- 每分钟约 150-180 字（口语速度）
- 包含过渡语句
- 标注重点强调部分
- 标注需要画面配合的地方

## 输出
- 脚本文件：`scripts/video_script_YYYYMMDD.md`
- 分镜大纲：`scripts/storyboard_YYYYMMDD.md`（可选）

使用 content-creator skill 进行品牌声音一致性检查。
```

---

### 模板 2.3：SEO 优化

```
请为以下视频优化 SEO 元素。

## 视频信息
- 脚本：`scripts/video_script_YYYYMMDD.md`
- 目标关键词：[主关键词]
- 次要关键词：[关键词1, 关键词2, ...]

## 参考数据
- 标签矩阵：`data/reports/tags_*.json`
- 竞品标题分析：`data/reports/research_*.md`

## 优化项目

### 1. 标题优化
- 长度：50-70 字符
- 包含主关键词
- 引发好奇/解决痛点
- 提供 3 个标题选项

### 2. 描述优化
- 前 150 字符包含关键词（搜索结果显示）
- 总长度：300-500 字
- 包含章节时间戳
- 包含相关链接（如有）

### 3. 标签推荐
- 5-15 个标签
- 混合使用：高频标签 + 长尾标签
- 按优先级排序

## 输出
- SEO 优化报告：`scripts/seo_report_YYYYMMDD.json`

格式示例：
```json
{
  "titles": [
    {"title": "...", "score": 85},
    {"title": "...", "score": 82},
    {"title": "...", "score": 78}
  ],
  "description": "...",
  "tags": ["标签1", "标签2", ...],
  "seo_score": 85,
  "suggestions": [...]
}
```

使用 seo-content-writer agent 进行优化。
```

---

### 模板 2.4：视频规约生成

```
请使用 spec-generator skill 生成 42COG 格式的视频规约。

## 输入文档
- 内容策划：`.42cog/spec/pm/content_plan_YYYYMMDD.md`
- 视频脚本：`scripts/video_script_YYYYMMDD.md`
- SEO 报告：`scripts/seo_report_YYYYMMDD.json`

## 规约格式

```xml
<spec>
  <section name="视频概述">
    <topic>主题描述</topic>
    <duration>目标时长: 8-12分钟</duration>
    <style>风格: 教程型</style>
    <target_audience>目标受众描述</target_audience>
  </section>

  <section name="三事件结构">
    <event1>
      <title>事件1标题</title>
      <time>0:00-1:00</time>
      <content>引入问题/痛点</content>
    </event1>
    <event2>
      <title>事件2标题</title>
      <time>1:00-6:00</time>
      <content>展示解决方案</content>
    </event2>
    <event3>
      <title>事件3标题</title>
      <time>6:00-8:00</time>
      <content>总结升华</content>
    </event3>
    <meaning>生发意义: 观众收获</meaning>
  </section>

  <section name="SEO优化">
    <title>标题(含关键词)</title>
    <description>描述(前150字含关键词)</description>
    <tags>标签列表</tags>
    <seo_score>85</seo_score>
  </section>

  <section name="制作要求">
    <voiceover>配音要求</voiceover>
    <visuals>画面要求</visuals>
    <music>背景音乐要求</music>
    <subtitles>字幕要求</subtitles>
  </section>
</spec>
```

## 输出
- 视频规约：`.42cog/spec/pm/video_spec_YYYYMMDD.md`
```

---

### 模板 2.5：创意构思（头脑风暴）

```
请使用 ideation skill 为 "[主题]" 进行创意头脑风暴。

## 构思维度

### 1. 话题角度
- 常规角度 vs 新奇角度
- 正面 vs 反面
- 专业 vs 入门

### 2. 内容形式
- 教程演示
- 对比测评
- 问答解惑
- 故事叙述
- 挑战实验

### 3. 差异化
- 竞品未覆盖的角度
- 独特的表达方式
- 创新的结构设计

## 输出
- 创意清单（10+ 个点子）
- 每个点子的可行性评分
- Top 3 推荐及理由

保存到：`data/reports/ideation_YYYYMMDD.md`
```

---

## 产出文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 内容策划 | `.42cog/spec/pm/content_plan_*.md` | 内容方向和策略 |
| 视频脚本 | `scripts/video_script_*.md` | 完整逐字稿 |
| SEO 报告 | `scripts/seo_report_*.json` | SEO 优化建议 |
| 视频规约 | `.42cog/spec/pm/video_spec_*.md` | 42COG 格式规约 |
| 创意清单 | `data/reports/ideation_*.md` | 头脑风暴结果 |

---

## 需要更新的文档

| 文档 | 更新内容 |
|------|----------|
| `.42cog/spec/pm/` | 新增策划文档 |
| `scripts/` | 新增脚本文件 |
| `.42cog/work/` | 记录策划过程 |

---

## 质量检查

在进入制作阶段前，确保：

1. **内容完整性**
   - [ ] 脚本覆盖所有要点
   - [ ] 三事件结构清晰
   - [ ] 时长预估合理

2. **SEO 就绪**
   - [ ] 标题优化完成
   - [ ] 描述包含关键词
   - [ ] 标签列表准备好

3. **规约验证**
   - [ ] 视频规约格式正确
   - [ ] 制作要求明确

---

## 检查清单

- [ ] 调研数据已分析
- [ ] 内容策划已完成
- [ ] 视频脚本已生成
- [ ] SEO 优化已完成
- [ ] 视频规约已生成

---

## 后置检查 (来自 pipeline.spec.md)

```yaml
postconditions:
  validation:
    - "Spec 文件符合三事件结构"
    - "Script word_count > 500"
    - "Script estimated_duration 在 target_duration ±20% 范围内"
  quality:
    - "SEO 评分 >= 70"
    - "标题长度 50-60 字符"
    - ref: "real.md#SEO 最佳实践"
```

### 输出契约

```yaml
output:
  files:
    - path: "specs/video_spec_{video_id}.md"
      type: Spec
      required: true
    - path: "scripts/video_script_{video_id}.md"
      type: Script
      required: true
    - path: "scripts/seo_report_{video_id}.json"
      type: SEOReport
      required: false
```

---

## 下一步

完成策划后，进入 **阶段 4：制作阶段**，根据脚本和规约制作视频。

---

*文档版本: 1.0*
*更新日期: 2026-01-17*
