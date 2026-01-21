# 阶段 5：发布阶段 (Publishing)

**前置条件**: 已完成 [阶段 4：制作阶段](./PROMPT_04_制作阶段.md)

> 自动上传视频并优化元数据

---

## 经验索引

> 📄 `.42cog/work/EXPERIENCE_INDEX.md`

**什么时候查**：踩坑了 / 这个问题之前好像遇到过 / 要做影响范围大的改动

---

## 规格引用

> ⚠️ **本提示词是规格的执行器，执行前请确认符合以下规格：**

| 规格文档 | 引用章节 | 用途 |
|----------|----------|------|
| `.42cog/spec/pm/pipeline.spec.md` | Stage 4: Publishing | 输入输出契约、执行模式、前置后置条件 |
| `.42cog/cog/cog.md` | Video, UploadTask | 实体定义和状态流转 |
| `.42cog/real/real.md` | #1 YouTube 社区准则红线, #3 API/自动化限制, #5 发布时间优化 | 约束检查 |

### 执行前检查 (来自 pipeline.spec.md)

```yaml
preconditions:
  dependencies:
    - stage: production
      status: completed
      outputs: [Video, Subtitle, Thumbnail]
  tools:
    - name: mcp-chrome
      check: "curl http://127.0.0.1:12306/health"
      note: "需要 Chrome 已登录 YouTube"
  constraints:
    - ref: "real.md#YouTube 社区准则红线"
      check: "内容已通过人工/AI 审核"
    - ref: "real.md#API/自动化限制"
      check: "当日上传次数未超限"
```

### 执行模式 (来自 pipeline.spec.md)

```yaml
execution_mode: hybrid  # 综合模式

workflow:
  1_understand:
    executor: AI
    token_budget: ~1000
    action: "解析上传参数，生成结构化配置"
  2_execute:
    executor: RPA (youtube-tool.py)
    token_budget: 0
    action: "执行上传、填写元数据"
  3_verify:
    executor: Playwright / DOM 检查
    token_budget: ~500 (仅失败时)
    action: "验证上传状态，失败则重新探索"
```

---

## 阶段目标

- 生成上传配置
- 自动化上传视频到 YouTube
- 填写元数据（标题、描述、标签）
- 上传封面和字幕
- 设置定时发布（可选）

---

## 技术栈参考

📄 **参考文档**：`.42cog/work/2026-01-17-技术栈与MCP清单.md`

### 本阶段需要的工具

| 工具 | 用途 | 说明 |
|------|------|------|
| Playwright | 浏览器自动化 | 操作 YouTube Studio |
| PyAutoGUI | RPA 执行 | 模拟鼠标键盘 |

### 本阶段需要的 MCP

| MCP | 必要性 | 用途 |
|-----|--------|------|
| @playwright/mcp | ✅ 必须 | YouTube Studio 自动化 |
| mcp-chrome | ⚠️ 备选 | 保持登录状态的浏览器控制 |

### MCP 配置

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

---

## 综合模式架构

📄 **参考文档**：`youtube-minimal-video-story/2026-01-09-决策-为什么放弃纯Playwright采用综合模式.md`

```
用户意图（自然语言）
       ↓
┌─────────────────────────────────┐
│ AI 理解需求（~1,000 tokens）    │
│ • 解析上传参数                   │
│ • 生成结构化配置                 │
└─────────────────────────────────┘
       ↓
┌─────────────────────────────────┐
│ RPA 执行（0 tokens）            │
│ • PyAutoGUI 自动化操作          │
│ • 按固化脚本执行上传            │
└─────────────────────────────────┘
       ↓
┌─────────────────────────────────┐
│ 验收检测（文件系统/DOM检查）     │
│ • 检查上传状态                   │
│ • 验证元数据填写                 │
└─────────────────────────────────┘
       ↓ 失败？
┌─────────────────────────────────┐
│ Playwright 重新探索             │
│ • 发现页面变化                   │
│ • 更新 RPA 脚本                 │
└─────────────────────────────────┘
```

---

## 42plugin 插件

### 核心插件

| 插件 | 类型 | 路径 | 功能 |
|------|------|------|------|
| viral-automation | Command | `.claude/commands/viral-automation.md` | 病毒式传播自动化 |
| website-automation | Command | `.claude/commands/website-automation.md` | 网站自动化操作 |
| orchestrator | Agent | `.claude/agents/orchestrator.md` | 代理编排 |

### 使用方式

```
请使用 viral-automation command 发布视频
请使用 website-automation command 操作 YouTube Studio
请使用 orchestrator agent 协调发布任务
```

---

## 提示词模板

### 模板 4.1：生成上传配置（AI 层）

```
请根据以下信息生成 YouTube 上传配置。

## 视频信息
- 视频文件：`output/video_YYYYMMDD_final.mp4`
- 封面文件：`output/thumbnail_YYYYMMDD.jpg`
- 字幕文件：`data/transcripts/subtitles_YYYYMMDD.srt`

## 元数据来源
- SEO 报告：`scripts/seo_report_YYYYMMDD.json`
- 视频规约：`.42cog/spec/pm/video_spec_YYYYMMDD.md`

## 配置生成

生成 JSON 格式的上传配置：

```json
{
  "video": {
    "path": "/absolute/path/to/video.mp4",
    "title": "视频标题（含关键词）",
    "description": "描述文本...\n\n章节：\n0:00 开场\n1:00 第一部分\n...",
    "tags": ["标签1", "标签2", "标签3"],
    "category": "Education",  // 或其他类别
    "language": "zh",
    "privacy": "public",  // public/unlisted/private
    "madeForKids": false
  },
  "thumbnail": {
    "path": "/absolute/path/to/thumbnail.jpg"
  },
  "subtitles": {
    "path": "/absolute/path/to/subtitles.srt",
    "language": "zh"
  },
  "schedule": {
    "enabled": false,
    "publishAt": "2026-01-20T10:00:00+08:00"  // ISO 8601 格式
  },
  "playlist": {
    "enabled": true,
    "name": "播放列表名称"
  }
}
```

## 输出
- 配置文件：`config/upload_config_YYYYMMDD.json`

## 验证清单
- [ ] 视频文件路径正确
- [ ] 标题长度 ≤ 100 字符
- [ ] 描述长度 ≤ 5000 字符
- [ ] 标签数量 5-15 个
- [ ] 封面尺寸 1280x720
```

---

### 模板 4.2：执行上传（RPA 层）

```
请使用综合模式上传视频到 YouTube。

## 配置文件
`config/upload_config_YYYYMMDD.json`

## 执行步骤

### 步骤 1：启动浏览器
使用 @playwright/mcp 或 mcp-chrome

### 步骤 2：导航到 YouTube Studio
```
URL: https://studio.youtube.com
```

### 步骤 3：点击上传按钮
- 查找「创建」或「上传视频」按钮
- 点击打开上传对话框

### 步骤 4：上传视频文件
使用 browser_file_upload 工具上传视频

### 步骤 5：填写元数据
- 标题
- 描述
- 标签（在「显示更多」中）
- 播放列表

### 步骤 6：上传封面
- 点击「上传缩略图」
- 选择封面文件

### 步骤 7：设置隐私
- 选择：公开/不公开/私享
- 如需定时发布，选择「排定时间」

### 步骤 8：发布
- 点击「发布」或「排定时间」

## 日志记录
每个步骤记录到：`logs/upload_YYYYMMDD.log`

## 错误处理
- 如遇到验证码，暂停并提示用户
- 如上传失败，记录错误并重试（最多 3 次）
```

---

### 模板 4.3：验收检查（验收层）

```
请验证视频是否成功上传到 YouTube。

## 验收检查清单

### 1. 上传状态
- [ ] 视频状态显示「已发布」或「已排程」
- [ ] 无处理错误

### 2. 元数据验证
- [ ] 标题正确
- [ ] 描述完整
- [ ] 标签已添加（在 YouTube Studio 中检查）

### 3. 封面验证
- [ ] 自定义封面已应用
- [ ] 不是自动生成的封面

### 4. 字幕验证
- [ ] 字幕已上传
- [ ] 字幕语言正确

### 5. 播放列表
- [ ] 已添加到指定播放列表

## 验收方式

使用 @playwright/mcp 的 browser_snapshot 获取页面状态：

```
1. 导航到 YouTube Studio > 内容
2. 找到刚上传的视频
3. 检查各项状态
```

## 输出
- 验收报告：`logs/upload_verification_YYYYMMDD.json`

```json
{
  "video_id": "abc123",
  "video_url": "https://youtube.com/watch?v=abc123",
  "upload_time": "2026-01-17T10:30:00+08:00",
  "status": "published",
  "verification": {
    "title": {"expected": "...", "actual": "...", "pass": true},
    "description": {"pass": true},
    "thumbnail": {"pass": true},
    "subtitles": {"pass": true},
    "playlist": {"pass": true}
  },
  "overall_pass": true
}
```
```

---

### 模板 4.4：定时发布

```
请设置视频定时发布。

## 发布计划
- 视频：`output/video_YYYYMMDD_final.mp4`
- 发布时间：YYYY-MM-DD HH:MM（时区：Asia/Shanghai）

## 最佳发布时间建议
根据目标受众选择：

| 目标受众 | 推荐时间（北京时间） |
|----------|----------------------|
| 上班族 | 周中 12:00-13:00, 20:00-22:00 |
| 学生 | 周末 10:00-12:00, 15:00-17:00 |
| 全球受众 | UTC 14:00 (北京 22:00) |

## 设置步骤
1. 上传视频时选择「排定时间」
2. 设置发布日期和时间
3. 确认时区正确
4. 点击「排定时间」

## 注意事项
- 定时发布的视频无法预览
- 发布前可以修改元数据
- 发布后 48 小时内可更换封面

## 输出
更新配置文件中的 schedule 部分
```

---

### 模板 4.5：批量发布

```
请批量上传多个视频到 YouTube。

## 视频列表
```json
[
  {
    "video": "output/video_001.mp4",
    "config": "config/upload_config_001.json"
  },
  {
    "video": "output/video_002.mp4",
    "config": "config/upload_config_002.json"
  }
]
```

## 批量发布策略
- 每个视频间隔：15 分钟（避免触发限制）
- 发布时间：每个视频定时不同时间
- 错误处理：单个失败不影响其他

## 执行流程
```
for each video in list:
    1. 读取配置
    2. 执行上传
    3. 验收检查
    4. 记录结果
    5. 等待 15 分钟
    6. 继续下一个
```

## 输出
- 批量发布报告：`logs/batch_upload_YYYYMMDD.json`
```

---

## 产出文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 上传配置 | `config/upload_config_*.json` | 上传参数 |
| 上传日志 | `logs/upload_*.log` | 执行日志 |
| 验收报告 | `logs/upload_verification_*.json` | 验收结果 |

---

## 需要更新的文档

| 文档 | 更新内容 |
|------|----------|
| `config/` | 新增上传配置 |
| `logs/` | 新增上传日志 |
| `.42cog/work/` | 记录发布过程 |

---

## 发布检查清单

| 检查项 | 验收标准 |
|--------|----------|
| 视频上传 | 状态显示「已发布」或「已排程」 |
| 标题 | 包含目标关键词，长度 ≤ 100 字符 |
| 描述 | 前 150 字符含关键词，包含章节 |
| 标签 | 5-15 个相关标签 |
| 封面 | 自定义封面，1280x720 |
| 字幕 | 已上传并启用 |
| 播放列表 | 已添加到目标列表 |

---

## 常见问题

### Q: 上传失败怎么办？
1. 检查网络连接
2. 检查视频格式是否支持
3. 检查文件大小（最大 256GB）
4. 重试上传

### Q: 如何保持登录状态？
使用 mcp-chrome 连接已登录的浏览器，或在 Playwright 中使用持久化 context。

### Q: 如何避免被封号？
- 不要频繁上传（建议每天 ≤ 5 个）
- 不要使用违规内容
- 保持正常的操作节奏

---

## 检查清单

- [ ] 上传配置已生成
- [ ] MCP 已启动
- [ ] 视频已上传
- [ ] 元数据已填写
- [ ] 封面已上传
- [ ] 验收检查通过

---

## 后置检查 (来自 pipeline.spec.md)

```yaml
postconditions:
  validation:
    - "youtube_id 格式正确 (11 字符)"
    - "视频在 YouTube Studio 中可见"
    - "元数据填写完整 (标题、描述、标签)"
    - "字幕已上传并启用"
    - "封面已设置"
  quality:
    - "视频状态为 '已发布' 或 '已排程'"
    - "Token 消耗 < 2000 (综合模式)"
```

### 输出契约

```yaml
output:
  updates:
    - entity: Video
      field: youtube_id
      value: "发布后获得的 YouTube 视频 ID"
    - entity: Video
      field: status
      value: "published" | "scheduled"
  files:
    - path: "logs/upload_report_{YYYYMMDD}.json"
      type: UploadReport
```

---

## 下一步

完成发布后，进入 **阶段 6：复盘阶段**，追踪视频效果。

---

*文档版本: 1.0*
*更新日期: 2026-01-17*
