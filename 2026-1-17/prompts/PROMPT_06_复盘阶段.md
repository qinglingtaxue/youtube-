# 阶段 6：复盘阶段 (Analytics)

**前置条件**: 已完成 [阶段 5：发布阶段](./PROMPT_05_发布阶段.md)

> 追踪效果，迭代优化策略

---

## 经验索引

> 📄 `.42cog/work/EXPERIENCE_INDEX.md`

**什么时候查**：踩坑了 / 这个问题之前好像遇到过 / 要做影响范围大的改动

---

## 规格引用

> ⚠️ **本提示词是规格的执行器，执行前请确认符合以下规格：**

| 规格文档 | 引用章节 | 用途 |
|----------|----------|------|
| `.42cog/spec/pm/pipeline.spec.md` | Stage 5: Analytics | 输入输出契约、反馈闭环、前置后置条件 |
| `.42cog/cog/cog.md` | Analytics, WorkflowStage | 实体定义和信息流向 |
| `.42cog/real/real.md` | #3 API/自动化限制 | 约束检查 |

### 执行前检查 (来自 pipeline.spec.md)

```yaml
preconditions:
  dependencies:
    - stage: publishing
      status: completed
      min_elapsed_time: "7 days"  # 至少发布 7 天后
  tools:
    - name: mcp-chrome
      check: "curl http://127.0.0.1:12306/health"
      note: "用于抓取 YouTube Studio 数据"
```

### 反馈闭环 (来自 pipeline.spec.md)

```yaml
feedback_loop:
  source: OptimizationSuggestions
  target: Stage 1 (Research)
  actions:
    - "将 next_topic_ideas 作为下轮调研关键词"
    - "将 content_suggestions 纳入 brand_voice 配置"
    - "更新标签策略 (基于 CTR 分析)"
```

---

## 阶段目标

- 收集视频发布后的数据
- 分析关键指标（观看数、CTR、留存率）
- 生成效果分析报告
- 提出改进建议
- 迭代优化下一期内容

---

## 技术栈参考

📄 **参考文档**：`.42cog/work/2026-01-17-技术栈与MCP清单.md`

### 本阶段需要的工具

| 工具 | 用途 | 说明 |
|------|------|------|
| SQLite | 存储历史数据 | 长期数据追踪 |
| Python | 数据分析 | 生成报告 |

### 本阶段需要的 MCP

| MCP | 必要性 | 用途 |
|-----|--------|------|
| @playwright/mcp | ✅ 推荐 | 抓取 YouTube Studio 数据 |
| mcp-chrome | ⚠️ 备选 | 保持登录状态 |

### 数据来源

| 来源 | 获取方式 | 数据类型 |
|------|----------|----------|
| YouTube Studio | Playwright 抓取 | 实时数据 |
| YouTube Analytics API | API 调用（需配额）| 详细数据 |
| 手动记录 | 用户输入 | 补充数据 |

---

## 42plugin 插件

### 核心插件

| 插件 | 类型 | 路径 | 功能 |
|------|------|------|------|
| blog-workflow | Hook | `.claude/hooks/blog-workflow` | 内容质量检查 |
| smart_agent_selection | Hook | `.claude/hooks/smart_agent_selection` | 智能代理选择 |

### 使用方式

```
blog-workflow Hook 会在提交内容规划时自动触发质量检查
```

---

## 提示词模板

### 模板 5.1：数据收集

```
请帮我收集视频发布后的数据。

## 视频信息
- 视频 ID：[VIDEO_ID]
- 视频 URL：https://youtube.com/watch?v=[VIDEO_ID]
- 发布日期：YYYY-MM-DD

## 数据收集时间点
- 24 小时后
- 7 天后
- 30 天后

## 需要收集的指标

### 核心指标
| 指标 | 说明 |
|------|------|
| 观看次数 | 总观看量 |
| 观看时长 | 总观看时长（小时） |
| 平均观看时长 | 每次观看的平均时长 |
| 平均观看百分比 | 观众平均看了多少 |

### 互动指标
| 指标 | 说明 |
|------|------|
| 点赞数 | 👍 数量 |
| 不喜欢数 | 👎 数量 |
| 评论数 | 评论总数 |
| 分享数 | 分享次数 |

### 点击指标
| 指标 | 说明 |
|------|------|
| 展示次数 | 缩略图展示次数 |
| 点击率 (CTR) | 展示→点击的转化率 |

### 流量来源
| 来源 | 占比 |
|------|------|
| YouTube 搜索 | % |
| 推荐视频 | % |
| 浏览功能 | % |
| 外部来源 | % |

## 数据收集方式

### 方式 A：Playwright 抓取
使用 @playwright/mcp 导航到 YouTube Studio Analytics

```
1. 导航到 https://studio.youtube.com
2. 点击「内容」
3. 找到目标视频
4. 点击「数据分析」
5. 获取页面快照，提取数据
```

### 方式 B：YouTube Analytics API（需 API Key）
```bash
# 需要 YouTube Data API v3 配额
```

## 输出
- 原始数据：`data/analytics/raw_[VIDEO_ID]_YYYYMMDD.json`

```json
{
  "video_id": "abc123",
  "collected_at": "2026-01-24T10:00:00+08:00",
  "period": "7d",
  "metrics": {
    "views": 1234,
    "watch_time_hours": 56.7,
    "avg_view_duration": "4:32",
    "avg_view_percentage": 45.2,
    "likes": 89,
    "dislikes": 3,
    "comments": 12,
    "shares": 5,
    "impressions": 5678,
    "ctr": 2.8
  },
  "traffic_sources": {
    "search": 35.2,
    "suggested": 42.1,
    "browse": 15.3,
    "external": 7.4
  }
}
```
```

---

### 模板 5.2：效果分析

```
请分析视频的表现并生成报告。

## 数据来源
- 原始数据：`data/analytics/raw_[VIDEO_ID]_*.json`
- 历史数据：数据库中的历史记录

## 分析维度

### 1. 与预期对比
- 观看数：目标 vs 实际
- CTR：目标 vs 实际
- 平均观看时长：目标 vs 实际

### 2. 与历史对比
- 对比上一期视频
- 对比同类型视频平均
- 趋势分析（上升/下降/持平）

### 3. 观众留存分析
- 开头 30 秒留存率
- 中段留存率
- 结尾留存率
- 找出流失点

### 4. 流量来源分析
- 主要流量来源
- 搜索关键词排名
- 推荐算法表现

## 报告模板

```markdown
# 视频效果分析报告

## 基本信息
- 视频标题：[标题]
- 视频 ID：[VIDEO_ID]
- 发布日期：YYYY-MM-DD
- 分析周期：7 天

## 核心指标摘要

| 指标 | 数值 | 对比上期 | 评价 |
|------|------|----------|------|
| 观看次数 | 1,234 | +15% | 良好 |
| CTR | 2.8% | -0.5% | 待改进 |
| 平均观看时长 | 4:32 | +0:23 | 优秀 |
| 互动率 | 7.2% | +1.1% | 良好 |

## 详细分析

### 观众留存
[留存曲线分析...]

### 流量来源
[流量来源分析...]

### 高光时刻
[观众反复观看的片段...]

## 结论
[整体评价...]

## 改进建议
1. ...
2. ...
3. ...
```

## 输出
- 分析报告：`data/reports/analysis_[VIDEO_ID]_YYYYMMDD.md`
```

---

### 模板 5.3：改进建议

```
请基于视频分析报告提出改进建议。

## 分析报告
`data/reports/analysis_[VIDEO_ID]_YYYYMMDD.md`

## 改进方向

### 1. 封面优化
如果 CTR 低于预期（<4%）：
- 分析点击率高的竞品封面
- 测试不同的封面设计
- A/B 测试（YouTube 付费功能）

### 2. 标题优化
如果搜索流量低：
- 检查关键词是否匹配
- 参考热门视频标题
- 调整标题结构

### 3. 内容节奏
如果留存率低：
- 分析流失点
- 缩短开头引入
- 增加节奏变化
- 添加更多视觉元素

### 4. 发布时间
如果初期流量低：
- 分析观众活跃时段
- 调整发布时间
- 测试不同时段

### 5. SEO 优化
如果搜索排名低：
- 更新描述关键词
- 添加更多相关标签
- 在评论区添加关键词

## 输出格式

```json
{
  "video_id": "abc123",
  "improvements": [
    {
      "area": "封面",
      "issue": "CTR 仅 2.8%，低于平均",
      "suggestion": "尝试添加人脸表情，使用更醒目的颜色",
      "priority": "high",
      "expected_impact": "+1% CTR"
    },
    {
      "area": "内容节奏",
      "issue": "1:30 处出现明显流失",
      "suggestion": "缩短开场白，更快进入主题",
      "priority": "medium",
      "expected_impact": "+10% 留存"
    }
  ],
  "next_video_recommendations": [
    "话题建议...",
    "结构建议...",
    "发布时间建议..."
  ]
}
```

## 输出
- 改进建议：`data/reports/improvements_[VIDEO_ID]_YYYYMMDD.json`
```

---

### 模板 5.4：周期性复盘

```
请进行 [周/月] 度内容复盘。

## 复盘周期
- 开始日期：YYYY-MM-DD
- 结束日期：YYYY-MM-DD

## 复盘内容

### 1. 发布概况
- 本期发布视频数：X 个
- 总观看次数：X 次
- 总观看时长：X 小时
- 新增订阅：X 人

### 2. Top 表现视频
| 排名 | 视频 | 观看数 | CTR | 互动率 |
|------|------|--------|-----|--------|
| 1 | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... |

### 3. 低表现视频
[分析原因...]

### 4. 趋势分析
- 哪类内容表现好？
- 哪个时段发布效果好？
- 观众互动有何特点？

### 5. 下期计划
基于本期数据，下期应该：
- 内容方向：...
- 发布频率：...
- 重点优化：...

## 输出
- 周期复盘报告：`data/reports/periodic_review_YYYYMMDD.md`
```

---

### 模板 5.5：数据库更新

```
请将分析数据存入数据库以便长期追踪。

## 数据表结构

### video_analytics 表
```sql
CREATE TABLE video_analytics (
    id INTEGER PRIMARY KEY,
    video_id TEXT NOT NULL,
    collected_at DATETIME NOT NULL,
    period TEXT NOT NULL,  -- '24h', '7d', '30d'

    -- 核心指标
    views INTEGER,
    watch_time_hours REAL,
    avg_view_duration TEXT,
    avg_view_percentage REAL,

    -- 互动指标
    likes INTEGER,
    dislikes INTEGER,
    comments INTEGER,
    shares INTEGER,

    -- 点击指标
    impressions INTEGER,
    ctr REAL,

    -- 流量来源 (JSON)
    traffic_sources TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 插入数据
```sql
INSERT INTO video_analytics (
    video_id, collected_at, period,
    views, watch_time_hours, avg_view_duration, avg_view_percentage,
    likes, dislikes, comments, shares,
    impressions, ctr, traffic_sources
) VALUES (
    'abc123', '2026-01-24 10:00:00', '7d',
    1234, 56.7, '4:32', 45.2,
    89, 3, 12, 5,
    5678, 2.8, '{"search": 35.2, "suggested": 42.1}'
);
```

## 查询示例

### 视频历史数据
```sql
SELECT * FROM video_analytics
WHERE video_id = 'abc123'
ORDER BY collected_at;
```

### 频道整体表现
```sql
SELECT
    strftime('%Y-%m', collected_at) as month,
    SUM(views) as total_views,
    AVG(ctr) as avg_ctr
FROM video_analytics
WHERE period = '30d'
GROUP BY month
ORDER BY month;
```
```

---

## 产出文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 原始数据 | `data/analytics/raw_*.json` | 采集的原始数据 |
| 分析报告 | `data/reports/analysis_*.md` | 单视频分析 |
| 改进建议 | `data/reports/improvements_*.json` | 优化建议 |
| 周期复盘 | `data/reports/periodic_review_*.md` | 周/月度复盘 |

---

## 需要更新的文档

| 文档 | 更新内容 |
|------|----------|
| `data/analytics/` | 新增数据文件 |
| `data/reports/` | 新增分析报告 |
| 数据库 | 更新 video_analytics 表 |
| `.42cog/work/` | 记录复盘过程和发现 |

---

## 复盘时间表

| 时间点 | 复盘内容 |
|--------|----------|
| 发布后 24 小时 | 初步数据检查 |
| 发布后 7 天 | 详细效果分析 |
| 发布后 30 天 | 长期表现评估 |
| 每周末 | 周度复盘 |
| 每月初 | 月度复盘 |

---

## 关键指标基准

| 指标 | 差 | 一般 | 良好 | 优秀 |
|------|-----|------|------|------|
| CTR | <2% | 2-4% | 4-10% | >10% |
| 平均观看百分比 | <30% | 30-50% | 50-70% | >70% |
| 互动率 | <2% | 2-5% | 5-10% | >10% |

---

## Hook 触发

blog-workflow Hook 会在以下情况触发：
- 提交新的内容规划时
- 提交视频脚本时

自动检查：
- 内容质量
- SEO 优化状态
- 与历史表现的对比

---

## 检查清单

- [ ] 24 小时数据已收集
- [ ] 7 天数据已收集
- [ ] 分析报告已生成
- [ ] 改进建议已提出
- [ ] 数据已存入数据库

---

## 后置检查 (来自 pipeline.spec.md)

```yaml
postconditions:
  validation:
    - "AnalyticsReport 包含核心指标"
    - "数据已存入 analytics 表"
  quality:
    - "报告包含与预期对比分析"
    - "报告包含可执行的优化建议"
    - "报告包含下期内容方向"
```

### 输出契约

```yaml
output:
  files:
    - path: "data/reports/analytics_{video_id}_{period}.md"
      type: AnalyticsReport
    - path: "data/reports/optimization_{video_id}.md"
      type: OptimizationSuggestions
  database:
    - table: analytics
      fields: [video_id, report_date, period, views, ctr, ...]
```

---

## 下一步

完成复盘后，回到 **阶段 2：调研阶段**，开始下一期内容的创作循环。

```
完整工作流循环（来自 cog.md 信息流向）：
CompetitorVideo → ResearchReport → Spec → Script → Video → Analytics
                                                              ↓
                                                     OptimizationSuggestions
                                                              ↓
                                                    下轮调研关键词 → ...
```

---

*文档版本: 1.0*
*更新日期: 2026-01-17*
