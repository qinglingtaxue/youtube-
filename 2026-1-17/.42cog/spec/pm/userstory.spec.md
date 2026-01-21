# 用户故事规约 (User Story Specification)

> 定义用户角色、使用场景和验收标准
>
> **引用文档**：
> - 项目元信息：`../../meta/meta.md`
> - 认知模型：`../../cog/cog.md`
> - 现实约束：`../../real/real.md`

---

## 一、用户角色 (Personas)

### 1.1 个人创作者 (Solo Creator)

```yaml
persona_id: P001
name: 个人创作者
description: 独立运营 YouTube 频道的内容创作者
characteristics:
  - 一人身兼策划、制作、运营
  - 时间有限，需要高效工具
  - 技术能力中等，能使用命令行
  - 追求内容质量，但也关注效率
goals:
  - 减少重复性操作（调研、上传）
  - 快速了解市场趋势
  - 保持稳定的更新频率
pain_points:
  - 调研竞品耗时（手动搜索、记录）
  - 上传流程繁琐（填写元数据、设置）
  - 复盘困难（数据分散、缺乏对比）
  - 机会识别难（不知道什么内容值得做、如何定位）
```

### 1.2 运营团队成员 (Team Operator)

```yaml
persona_id: P002
name: 运营团队成员
description: 在自媒体团队中负责内容运营的成员
characteristics:
  - 团队协作，有分工
  - 需要批量处理多个视频/频道
  - 关注数据和 ROI
  - 有一定技术支持
goals:
  - 批量化内容生产
  - 可追踪的工作流程
  - 数据驱动的决策
pain_points:
  - 多频道管理复杂
  - 缺乏统一的工作流
  - 难以量化内容效果
```

---

## 二、用户故事 (User Stories)

### 阶段 1：调研 (Research)

#### US-R001: 关键词调研

```yaml
story_id: US-R001
title: 关键词调研
persona: P001 (个人创作者)
stage: research

as_a: 个人创作者
i_want: 输入关键词后自动收集 YouTube 竞品数据
so_that: 了解市场趋势，找到内容差异点

acceptance_criteria:
  - AC1: 输入关键词后 15 分钟内返回调研报告
  - AC2: 报告包含 top 10-50 竞品视频的元数据
  - AC3: 报告包含标签分布分析（高频/中频/长尾）
  - AC4: 报告包含热门话题识别
  - AC5: 数据存入本地数据库，支持历史对比

priority: P0 (MVP)
effort: M (中等)
dependencies: []
```

#### US-R002: 竞品视频分析

```yaml
story_id: US-R002
title: 竞品视频分析
persona: P001 (个人创作者)
stage: research

as_a: 个人创作者
i_want: 下载竞品视频并提取字幕/内容结构
so_that: 学习优秀内容的组织方式

acceptance_criteria:
  - AC1: 支持下载 1080p 及以下分辨率视频
  - AC2: 自动提取字幕（优先手动字幕，其次自动字幕，最后 Whisper 转录）
  - AC3: 生成内容结构分析（开头/中间/结尾）
  - AC4: 遵守版权约束，仅供分析使用

priority: P0 (MVP)
effort: M (中等)
dependencies: []
```

#### US-R003: 大规模数据采集

```yaml
story_id: US-R003
title: 大规模数据采集
persona: P001 (个人创作者)
stage: research

as_a: 个人创作者
i_want: 一次性采集 1000+ 个竞品视频的元数据
so_that: 有足够的数据样本进行市场分析

acceptance_criteria:
  - AC1: 支持按主题批量采集（如"老人养生"）
  - AC2: 自动扩展关键词（如"老人养生"→"老人健康"、"中老年保健"等）
  - AC3: 高播放量视频（>5000）自动获取详细信息
  - AC4: 支持按发布日期排序，优先获取最新视频
  - AC5: 自动去重，跳过已存在的视频

priority: P0 (MVP)
effort: M (中等)
dependencies: []
```

#### US-R004: 每日自动采集

```yaml
story_id: US-R004
title: 每日自动采集
persona: P002 (运营团队成员)
stage: research

as_a: 运营团队成员
i_want: 每天自动采集 1000 个新发布的视频
so_that: 保持数据库的时效性，及时发现新内容

acceptance_criteria:
  - AC1: 支持设置定时任务（cron/launchd）
  - AC2: 按上传日期排序，优先获取最新视频
  - AC3: 自动拍摄播放量快照（用于趋势分析）
  - AC4: 生成采集日志和结果报告

priority: P1 (增强)
effort: M (中等)
dependencies: [US-R003]
```

---

### 阶段 1.5：分析 (Analysis)

#### US-AN001: 市场分析报告

```yaml
story_id: US-AN001
title: 市场分析报告
persona: P001 (个人创作者)
stage: analysis

as_a: 个人创作者
i_want: 自动生成市场分析报告
so_that: 了解市场规模、竞争格局和进入壁垒

acceptance_criteria:
  - AC1: 报告包含市场规模（视频数、总播放量、平均播放量）
  - AC2: 报告包含频道竞争分析（集中度、规模分布）
  - AC3: 报告包含进入壁垒（播放量分层、爆款率、Top10%门槛）
  - AC4: 报告包含时间上下文（数据时间范围、时间分布）
  - AC5: 支持按时间窗口筛选（1天内、15天内、30天内、全部）

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-R003]
```

#### US-AN002: AI创作机会识别

```yaml
story_id: US-AN002
title: AI创作机会识别
persona: P001 (个人创作者)
stage: analysis

as_a: 个人创作者
i_want: 自动识别适合 AI 批量创作的内容机会
so_that: 找到小众但高价值的内容方向

acceptance_criteria:
  - AC1: 识别近期爆款（按时间窗口分类）
  - AC2: 识别高日增长视频（日增 > 500）
  - AC3: 识别小频道黑马（1-3视频的频道但播放量高）
  - AC4: 识别高互动模板（互动率 > 3%）
  - AC5: 生成机会总结和行动建议

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-R003]
```

#### US-AN003: 趋势监控

```yaml
story_id: US-AN003
title: 趋势监控
persona: P002 (运营团队成员)
stage: analysis

as_a: 运营团队成员
i_want: 追踪视频播放量的增长趋势
so_that: 识别正在上升的内容方向

acceptance_criteria:
  - AC1: 定期拍摄播放量快照
  - AC2: 计算日均增长率
  - AC3: 生成增长趋势图（1天、15天、30天）
  - AC4: 识别增长最快的视频

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-R003]
```

#### US-AN004: 综合分析报告

```yaml
story_id: US-AN004
title: 综合分析报告
persona: P001 (个人创作者)
stage: analysis

as_a: 个人创作者
i_want: 生成可视化的综合分析报告
so_that: 一目了然地了解市场全貌和创作机会

acceptance_criteria:
  - AC1: 报告为 6 个独立 HTML 页面，可在浏览器中查看
  - AC2: 页面结构：概览、套利分析、内容四象限、创作者分析、标题公式、行动建议
  - AC3: 报告包含交互式图表（播放量分布、时间分布、四象限图等）
  - AC4: 视频标题和频道名可点击跳转到 YouTube
  - AC5: 页面间通过顶部导航链接，支持快速切换

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-AN001, US-AN002, US-AN003]
```

#### US-AN005: 报告部署

```yaml
story_id: US-AN005
title: 报告部署
persona: P002 (运营团队成员)
stage: analysis

as_a: 运营团队成员
i_want: 将分析报告部署到网上
so_that: 团队成员可以随时在线查看

acceptance_criteria:
  - AC1: 支持一键部署到 Vercel
  - AC2: 报告可通过 URL 在线访问
  - AC3: 部署脚本自动生成最新报告并上传

priority: P1 (增强)
effort: S (较小)
dependencies: [US-AN004]
```

---

### 阶段 1.6：套利分析 (Arbitrage Analysis)

> **核心公式**：有趣度 = 信息价值程度 / 信息传播程度 = 中介中心性 / 程度中心性

#### US-ARB001: 话题套利分析

```yaml
story_id: US-ARB001
title: 话题套利分析
persona: P001 (个人创作者)
stage: arbitrage

as_a: 个人创作者
i_want: 通过关键词网络发现"桥梁话题"
so_that: 找到能连接多个受众群体但传播不足的高价值话题

acceptance_criteria:
  - AC1: 构建关键词共现网络（节点=关键词，边=同标题共现）
  - AC2: 计算每个关键词的中介中心性和程度中心性
  - AC3: 计算有趣度（中介中心性/程度中心性）
  - AC4: 识别有趣度 > 0.3 的桥梁话题
  - AC5: 展示每个桥梁话题连接的受众群体

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-R003]
```

#### US-ARB002: 频道套利分析

```yaml
story_id: US-ARB002
title: 频道套利分析
persona: P001 (个人创作者)
stage: arbitrage

as_a: 个人创作者
i_want: 发现小频道爆款视频
so_that: 模仿内容本身有价值但缺乏渠道的成功案例

acceptance_criteria:
  - AC1: 识别 1-3 视频的小频道
  - AC2: 找出播放量远超该频道平均的爆款视频
  - AC3: 计算有趣度（爆款播放量/频道平均播放量）
  - AC4: 生成可复制的成功模式清单
  - AC5: 提供每个爆款的内容分析

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-R003]
```

#### US-ARB003: 时长套利分析

```yaml
story_id: US-ARB003
title: 时长套利分析
persona: P001 (个人创作者)
stage: arbitrage

as_a: 个人创作者
i_want: 发现供给不足的时长区间
so_that: 在竞争较少的时长区间获得更多曝光

acceptance_criteria:
  - AC1: 将视频按时长分桶（0-1min、1-3min、3-5min...）
  - AC2: 计算每个时长区间的平均播放量和供给占比
  - AC3: 计算有趣度（平均播放量/供给占比）
  - AC4: 识别高有趣度时长区间（播放量高但供给少）
  - AC5: 给出具体的时长建议（如"建议制作 20-30 分钟的视频"）

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-R003]
```

#### US-ARB004: 趋势套利分析

```yaml
story_id: US-ARB004
title: 趋势套利分析
persona: P002 (运营团队成员)
stage: arbitrage

as_a: 运营团队成员
i_want: 识别上升和下降趋势话题
so_that: 提前布局上升话题，避开下降话题

acceptance_criteria:
  - AC1: 比较话题近期频率与历史频率
  - AC2: 计算趋势比（近期频率/历史频率）
  - AC3: 识别上升趋势话题（趋势比 > 1.5）
  - AC4: 识别下降趋势话题（趋势比 < 0.5）
  - AC5: 提供趋势话题的布局时机建议

priority: P1 (增强)
effort: M (中等)
dependencies: [US-R003]
```

#### US-ARB005: 博主定位建议

```yaml
story_id: US-ARB005
title: 博主定位建议
persona: P001 (个人创作者)
stage: arbitrage

as_a: 个人创作者
i_want: 根据我的资源情况获得定位建议
so_that: 选择适合自己的套利策略

acceptance_criteria:
  - AC1: 支持选择博主类型（小白/腰部/头部）
  - AC2: 根据类型推荐适合的套利策略
  - AC3: 小白博主：推荐话题套利、时长套利、频道套利
  - AC4: 腰部博主：推荐桥梁话题、跨品类套利
  - AC5: 头部博主：推荐趋势套利、跨语言套利

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-ARB001, US-ARB002, US-ARB003]
```

#### US-ARB006: 综合套利报告

```yaml
story_id: US-ARB006
title: 综合套利报告
persona: P001 (个人创作者)
stage: arbitrage

as_a: 个人创作者
i_want: 生成综合套利分析报告
so_that: 一目了然地了解所有套利机会和行动建议

acceptance_criteria:
  - AC1: 整合话题、频道、时长、趋势套利结果
  - AC2: 按优先级排序套利机会
  - AC3: 每个机会包含有趣度分数和行动建议
  - AC4: 生成综合摘要文本
  - AC5: 支持导出为 JSON 格式

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-ARB001, US-ARB002, US-ARB003, US-ARB004]
```

---

### 阶段 2：策划 (Planning)

#### US-P001: 脚本生成

```yaml
story_id: US-P001
title: 脚本生成
persona: P001 (个人创作者)
stage: planning

as_a: 个人创作者
i_want: 基于调研数据自动生成视频脚本大纲
so_that: 快速启动内容创作，不必从零开始

acceptance_criteria:
  - AC1: 脚本遵循三事件结构（引入-展开-总结）
  - AC2: 脚本包含时间标记（预计每段时长）
  - AC3: 脚本字数与目标时长匹配（150-180字/分钟）
  - AC4: 支持多种风格（教程/故事/评论）

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-R001]
```

#### US-P002: SEO 优化

```yaml
story_id: US-P002
title: SEO 优化
persona: P001 (个人创作者)
stage: planning

as_a: 个人创作者
i_want: 自动生成 SEO 优化的标题、描述、标签
so_that: 提高视频在 YouTube 搜索中的排名

acceptance_criteria:
  - AC1: 生成 3 个候选标题，附带评分
  - AC2: 标题长度 50-60 字符，包含目标关键词
  - AC3: 描述前 150 字符包含核心关键词
  - AC4: 推荐 5-15 个相关标签
  - AC5: SEO 评分 >= 70 分

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-P001]
```

#### US-P003: 视频规约生成

```yaml
story_id: US-P003
title: 视频规约生成
persona: P001 (个人创作者)
stage: planning

as_a: 个人创作者
i_want: 生成结构化的视频规约文档
so_that: 制作阶段有明确的执行指南

acceptance_criteria:
  - AC1: 规约包含视频概述（主题、时长、风格、受众）
  - AC2: 规约包含三事件结构详细内容
  - AC3: 规约包含 SEO 元素
  - AC4: 规约包含制作要求（配音、画面、音乐、字幕）
  - AC5: 规约格式符合 42COG 标准

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-P001, US-P002]
```

---

### 阶段 3：制作 (Production)

#### US-M001: 素材管理

```yaml
story_id: US-M001
title: 素材管理
persona: P001 (个人创作者)
stage: production

as_a: 个人创作者
i_want: 统一管理视频制作所需的素材
so_that: 素材来源可追溯，版权合规

acceptance_criteria:
  - AC1: 素材按类型分类存储（视频/图片/音频）
  - AC2: 每个素材记录来源和授权信息
  - AC3: 支持素材清单导出
  - AC4: 遵守版权约束（real.md#2）

priority: P1 (增强)
effort: M (中等)
dependencies: []
```

#### US-M002: 字幕处理

```yaml
story_id: US-M002
title: 字幕处理
persona: P001 (个人创作者)
stage: production

as_a: 个人创作者
i_want: 自动生成和优化视频字幕
so_that: 提高视频的可访问性和观看体验

acceptance_criteria:
  - AC1: 支持 Whisper 自动转录
  - AC2: 支持字幕格式转换（SRT/VTT）
  - AC3: 支持字幕校对和修复
  - AC4: 字幕符合规范（每行 ≤42 字符，每屏 ≤2 行）

priority: P0 (MVP)
effort: M (中等)
dependencies: []
```

#### US-M003: 视频合成

```yaml
story_id: US-M003
title: 视频合成
persona: P001 (个人创作者)
stage: production

as_a: 个人创作者
i_want: 使用命令行工具合成最终视频
so_that: 不依赖昂贵的视频编辑软件

acceptance_criteria:
  - AC1: 支持视频+配音+字幕+背景音乐合成
  - AC2: 输出 1080p H.264 格式
  - AC3: 提供常用 FFmpeg 命令模板
  - AC4: 支持批量合成（可选）

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-M002]
```

---

### 阶段 4：发布 (Publishing)

#### US-U001: 自动上传

```yaml
story_id: US-U001
title: 自动上传
persona: P001 (个人创作者)
stage: publishing

as_a: 个人创作者
i_want: 自动上传视频到 YouTube 并填写元数据
so_that: 省去重复的上传操作

acceptance_criteria:
  - AC1: 自动上传视频文件
  - AC2: 自动填写标题、描述、标签
  - AC3: 自动上传自定义封面
  - AC4: 自动上传字幕文件
  - AC5: 支持添加到播放列表
  - AC6: Token 消耗 < 2000（综合模式）

priority: P0 (MVP)
effort: L (较大)
dependencies: [US-M003, US-P002]
```

#### US-U002: 定时发布

```yaml
story_id: US-U002
title: 定时发布
persona: P001 (个人创作者)
stage: publishing

as_a: 个人创作者
i_want: 设置视频定时发布
so_that: 在最佳时间发布，即使我不在线

acceptance_criteria:
  - AC1: 支持选择发布日期和时间
  - AC2: 支持时区设置
  - AC3: 提供最佳发布时间建议
  - AC4: 遵守发布时间优化约束（real.md#5）

priority: P1 (增强)
effort: S (较小)
dependencies: [US-U001]
```

#### US-U003: 批量上传

```yaml
story_id: US-U003
title: 批量上传
persona: P002 (运营团队成员)
stage: publishing

as_a: 运营团队成员
i_want: 批量上传多个视频
so_that: 高效处理多频道/多视频的发布

acceptance_criteria:
  - AC1: 支持批量配置文件
  - AC2: 每个视频间隔 15 分钟（避免触发限制）
  - AC3: 单个失败不影响其他
  - AC4: 生成批量上传报告

priority: P2 (未来)
effort: L (较大)
dependencies: [US-U001]
```

#### US-U004: 上传验收

```yaml
story_id: US-U004
title: 上传验收
persona: P001 (个人创作者)
stage: publishing

as_a: 个人创作者
i_want: 自动验证上传是否成功
so_that: 确保视频正确发布，无需手动检查

acceptance_criteria:
  - AC1: 验证视频状态（已发布/已排程）
  - AC2: 验证元数据填写完整
  - AC3: 验证封面已设置
  - AC4: 验证字幕已上传
  - AC5: 生成验收报告

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-U001]
```

---

### 阶段 5：复盘 (Analytics)

#### US-A001: 数据收集

```yaml
story_id: US-A001
title: 数据收集
persona: P001 (个人创作者)
stage: analytics

as_a: 个人创作者
i_want: 自动收集视频发布后的数据
so_that: 了解视频表现，无需手动记录

acceptance_criteria:
  - AC1: 收集核心指标（观看数、时长、CTR、互动）
  - AC2: 收集流量来源分布
  - AC3: 支持多时间点收集（24h/7d/30d）
  - AC4: 数据存入数据库

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-U001]
```

#### US-A002: 效果分析

```yaml
story_id: US-A002
title: 效果分析
persona: P001 (个人创作者)
stage: analytics

as_a: 个人创作者
i_want: 生成视频效果分析报告
so_that: 了解哪些内容有效，哪些需要改进

acceptance_criteria:
  - AC1: 对比预期目标 vs 实际表现
  - AC2: 对比历史视频平均
  - AC3: 分析观众留存曲线
  - AC4: 识别高光时刻和流失点

priority: P0 (MVP)
effort: M (中等)
dependencies: [US-A001]
```

#### US-A003: 改进建议

```yaml
story_id: US-A003
title: 改进建议
persona: P001 (个人创作者)
stage: analytics

as_a: 个人创作者
i_want: 基于数据获得可执行的改进建议
so_that: 知道下一步具体做什么

acceptance_criteria:
  - AC1: 针对封面/标题/内容分别给出建议
  - AC2: 建议包含预期影响
  - AC3: 建议按优先级排序
  - AC4: 提供下期内容方向建议

priority: P0 (MVP)
effort: S (较小)
dependencies: [US-A002]
```

#### US-A004: 周期复盘

```yaml
story_id: US-A004
title: 周期复盘
persona: P002 (运营团队成员)
stage: analytics

as_a: 运营团队成员
i_want: 生成周/月度复盘报告
so_that: 从宏观视角评估内容策略效果

acceptance_criteria:
  - AC1: 汇总周期内所有视频数据
  - AC2: 识别 Top 表现和低表现视频
  - AC3: 分析趋势（上升/下降/持平）
  - AC4: 提出下周期策略建议

priority: P1 (增强)
effort: M (中等)
dependencies: [US-A002]
```

---

## 三、故事地图 (Story Map)

```
                    调研           分析          策划          制作          发布          复盘
                  (Research)    (Analysis)    (Planning)   (Production)  (Publishing)  (Analytics)
                      │             │             │             │             │             │
用户旅程 ─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────
                      │             │             │             │             │             │
MVP (P0)              │             │             │             │             │             │
                 ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
                 │ US-R001 │   │US-AN001 │   │ US-P001 │   │ US-M002 │   │ US-U001 │   │ US-A001 │
                 │ 关键词  │   │ 市场    │   │ 脚本    │   │ 字幕    │   │ 自动    │   │ 数据    │
                 │ 调研    │   │ 分析    │   │ 生成    │   │ 处理    │   │ 上传    │   │ 收集    │
                 └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
                      │             │             │             │             │             │
                 ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
                 │ US-R002 │   │US-AN002 │   │ US-P002 │   │ US-M003 │   │ US-U004 │   │ US-A002 │
                 │ 竞品    │   │ AI创作  │   │ SEO     │   │ 视频    │   │ 上传    │   │ 效果    │
                 │ 分析    │   │ 机会    │   │ 优化    │   │ 合成    │   │ 验收    │   │ 分析    │
                 └────┬────┘   └────┬────┘   └────┬────┘   └─────────┘   └─────────┘   └────┬────┘
                      │             │             │                                         │
                 ┌────┴────┐   ┌────┴────┐   ┌────┴────┐                               ┌────┴────┐
                 │ US-R003 │   │US-AN003 │   │ US-P003 │                               │ US-A003 │
                 │ 大规模  │   │ 趋势    │   │ 规约    │                               │ 改进    │
                 │ 采集    │   │ 监控    │   │ 生成    │                               │ 建议    │
                 └─────────┘   └────┬────┘   └─────────┘                               └─────────┘
                                    │
                               ┌────┴────┐
                               │US-AN004 │
                               │ 综合    │
                               │ 报告    │
                               └─────────┘
                      │             │             │             │             │             │
增强 (P1)             │             │             │             │             │             │
                 ┌────┴────┐   ┌────┴────┐   ┌─────────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
                 │ US-R004 │   │US-AN005 │   │         │   │ US-M001 │   │ US-U002 │   │ US-A004 │
                 │ 每日    │   │ 报告    │   │         │   │ 素材    │   │ 定时    │   │ 周期    │
                 │ 采集    │   │ 部署    │   │         │   │ 管理    │   │ 发布    │   │ 复盘    │
                 └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
                      │             │             │             │             │             │
未来 (P2)             │             │             │             │             │             │
                 ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────┴────┐   ┌─────────┐
                 │         │   │         │   │         │   │         │   │ US-U003 │   │         │
                 │         │   │         │   │         │   │         │   │ 批量    │   │         │
                 │         │   │         │   │         │   │         │   │ 上传    │   │         │
                 └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

---

## 四、优先级汇总

### P0 - MVP (必须有)

| 故事 ID | 标题 | 阶段 | 工作量 |
|---------|------|------|--------|
| US-R001 | 关键词调研 | 调研 | M |
| US-R002 | 竞品视频分析 | 调研 | M |
| US-R003 | 大规模数据采集 | 调研 | M |
| US-AN001 | 市场分析报告 | 分析 | S |
| US-AN002 | AI创作机会识别 | 分析 | S |
| US-AN003 | 趋势监控 | 分析 | M |
| US-AN004 | 综合分析报告 | 分析 | M |
| US-P001 | 脚本生成 | 策划 | M |
| US-P002 | SEO 优化 | 策划 | S |
| US-P003 | 视频规约生成 | 策划 | S |
| US-M002 | 字幕处理 | 制作 | M |
| US-M003 | 视频合成 | 制作 | M |
| US-U001 | 自动上传 | 发布 | L |
| US-U004 | 上传验收 | 发布 | M |
| US-A001 | 数据收集 | 复盘 | M |
| US-A002 | 效果分析 | 复盘 | M |
| US-A003 | 改进建议 | 复盘 | S |

**MVP 总计**: 17 个故事

### P1 - 增强 (应该有)

| 故事 ID | 标题 | 阶段 | 工作量 |
|---------|------|------|--------|
| US-R004 | 每日自动采集 | 调研 | M |
| US-AN005 | 报告部署 | 分析 | S |
| US-M001 | 素材管理 | 制作 | M |
| US-U002 | 定时发布 | 发布 | S |
| US-A004 | 周期复盘 | 复盘 | M |

### P2 - 未来 (可以有)

| 故事 ID | 标题 | 阶段 | 工作量 |
|---------|------|------|--------|
| US-U003 | 批量上传 | 发布 | L |

---

## 五、与其他规约的关系

```
userstory.spec.md (本文档)
    │
    │ 用户故事定义「用户要什么」
    ↓
pr.spec.md (产品需求规约)
    │
    │ 产品需求定义「产品提供什么功能」
    ↓
pipeline.spec.md (流程规约)
    │
    │ 流程规约定义「系统内部如何运作」
    ↓
prompts/ (提示词)
    │
    │ 提示词定义「具体如何执行」
    ↓
实际执行
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-18 | 初始版本，定义 2 个角色，17 个用户故事 |
| 1.1 | 2026-01-19 | 新增分析阶段用户故事(US-AN001~US-AN005)，更新调研阶段故事(US-R003、US-R004)，总计 23 个用户故事 |
| 1.2 | 2026-01-19 | 新增套利分析阶段用户故事(US-ARB001~US-ARB006)，总计 29 个用户故事 |
| 1.3 | 2026-01-19 | 更新 US-AN004 验收标准，报告结构从5个标签页改为6个独立HTML页面 |

---

*引用本规约时使用：`.42cog/spec/pm/userstory.spec.md`*
