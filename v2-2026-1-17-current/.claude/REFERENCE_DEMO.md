# 参考实例（Reference Demo）

> 对齐的本质：找到一个更好的实例（70分），让当前（60分）向它学习。
>
> 本文档是"70分实例"，新开发的功能应向它对齐。

## 1. 最佳实践 Skill 文件示例

以 `data-collector.md` 为参考，所有 skill 文件应包含：

```markdown
# {skill-name}

> **编码**: SK-{编号}
> **类型**: {类型}
> **输入**: {输入的知识单元类型}
> **输出**: {输出的知识单元类型}
> **前置**: {依赖的 skill}（如有）
> **可接**: {可连接的下游 skill}

{一句话描述}

## 触发条件

- 条件1
- 条件2

## 核心约束（基于踩坑经验）

### 1. {约束名称}

```yaml
{约束内容，用 YAML 格式}
```

### 2. {约束名称}
...

## 输出

- 输出物1：`路径/文件名`
- 输出物2：`路径/文件名`
```

**对齐检查**：新 skill 文件是否包含以上所有部分？缺哪个补哪个。

---

## 2. 最佳实践知识单元示例

### 2.1 视频知识单元 (KU-VIDEO)

```json
{
  "ku_id": "dQw4w9WgXcQ",
  "ku_type": "video",
  "source": "yt-dlp",
  "source_id": "dQw4w9WgXcQ",
  "metadata": {
    "youtube_id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "channel_name": "Rick Astley",
    "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
    "view_count": 1500000000,
    "like_count": 15000000,
    "comment_count": 3000000,
    "duration": 213,
    "published_at": "2009-10-25T00:00:00Z",
    "engagement_rate": 1.2
  },
  "quality_score": 0.95,
  "status": "validated"
}
```

**对齐检查**：
- [ ] 有 `ku_id`（全局唯一）？
- [ ] 有 `ku_type`？
- [ ] 有 `source` 和 `source_id`（可溯源）？
- [ ] `metadata` 包含所有必填字段？
- [ ] 有 `quality_score`（0-1）？
- [ ] 有 `status`（pending/validated/failed）？

### 2.2 模式知识单元 (KU-PATTERN)

```json
{
  "ku_id": "PT-TMP-01",
  "ku_type": "pattern",
  "metadata": {
    "pattern_id": "PT-TMP-01",
    "dimension": "temporal",
    "finding": "周一发布的视频平均播放量比其他日期高 23%",
    "sample_size": 1500,
    "confidence": 0.82,
    "data_sources": ["competitor_videos"],
    "time_range": "2026-01-01 ~ 2026-01-31",
    "action_items": [
      "优先选择周一 10:00-14:00 发布",
      "避开周末发布"
    ]
  },
  "quality_score": 0.85,
  "status": "validated"
}
```

**对齐检查**：
- [ ] `pattern_id` 符合编码规范（PT-{维度}-{序号}）？
- [ ] 有 `dimension`（temporal/spatial/variable/channel/user）？
- [ ] `finding` 是一句完整的结论？
- [ ] `sample_size` >= 该维度最小要求？
- [ ] `confidence` 与 `sample_size` 匹配？
- [ ] 有可执行的 `action_items`？

---

## 3. 最佳实践对齐流程

### 3.1 规约 vs Demo 对齐（12问法）

当你有一个规约和一个 demo 时：

```
提示词模板：

请对比以下两个文档：
- 规约：{规约文档路径}
- Demo：{demo 路径或截图}

请列出：
1. 规约有但 demo 没有的功能（共 N 个）
2. Demo 有但规约没有的功能（共 M 个）
3. 两者都有但实现不一致的地方（共 K 个）

对于每个差异，请说明：
- 哪个更好？
- 如果规约更好，demo 需要改什么？
- 如果 demo 更好，规约需要改什么？

注意：只列出差异，不要自动修改。由我来决定改哪个。
```

**核心原则**：AI 只列出差异，人来决定改什么。

### 3.2 唯一编码对齐

当代码中使用了编码时：

```
检查项：
1. 编码是否全局唯一？（不能有两个 SK-01）
2. 编码是否有意义？（看编码就知道是什么）
3. 编码是否连续？（不能 SK-01, SK-02, SK-05 跳过 03/04）
4. 引用是否正确？（SK-01 的输出被 SK-02 引用）
```

---

## 4. 分组最佳实践

### 4.1 数据迁移分组

```
第一轮：快速跑通原型
  - 目标：验证流程可行
  - 允许：数据丢失、功能不全
  - 时间：1 天

第二轮：冻结旧数据，处理增量
  - 目标：最小化停机时间
  - 冻结：24小时前的数据
  - 单独处理：最近的增量数据
  - 时间：半天
```

### 4.2 功能分组

```
P0 必须有：
  - 核心功能 A
  - 核心功能 B

P1 应该有：
  - 增强功能 C
  - 增强功能 D

P2 可以没有（先放一放）：
  - 锦上添花功能 E
  - 新功能 F
```

### 4.3 Bug 修复分组

```
不要这样做：
  一次性扔 10 条 bug 给 AI

应该这样做：
  1. 让 AI 按优先级排序、合并同类项
  2. 分成 3-4 组
  3. 一组一组处理
```

---

## 5. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-02-02 | 初始版本，提供 skill/KU/对齐/分组 的参考实例 |
