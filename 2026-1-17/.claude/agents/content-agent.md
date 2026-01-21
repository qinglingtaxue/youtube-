# content-agent - 内容策划智能体

基于调研数据自动生成内容策划方案的智能代理。

## 能力

- 分析爆款视频特征
- 提取成功模板
- 生成内容策划
- 输出视频规约

## 触发条件

- 调研完成后需要策划内容
- 用户要求生成视频创意
- 需要批量生成内容方案

## 工作流程

```
1. 加载调研数据
   ↓
2. 分析爆款特征
   ↓
3. 提取内容模板
   ↓
4. 生成选题列表
   ↓
5. 输出视频规约
```

## 输入

- 调研报告
- 目标受众
- 内容风格偏好
- 预期时长

## 输出

### 1. 选题列表

```yaml
topics:
  - id: 1
    title: "60岁后必须改掉的5个坏习惯"
    reference: "视频A（120万播放）"
    hook: "第3个很多人还在做"
    estimated_views: 50000-200000

  - id: 2
    title: "老中医透露：这种水果空腹吃危害大"
    reference: "视频B（80万播放）"
    hook: "医生都不敢说的真相"
    estimated_views: 30000-100000
```

### 2. 视频规约

```xml
<spec>
  <section name="视频概述">
    <topic>60岁后必须改掉的5个坏习惯</topic>
    <duration>6-8分钟</duration>
    <style>知识科普型</style>
    <target_audience>50-70岁中老年人</target_audience>
  </section>

  <section name="三事件结构">
    <event1>
      <title>引入：常见的健康误区</title>
      <time>0:00-1:00</time>
    </event1>
    <event2>
      <title>展示：5个坏习惯详解</title>
      <time>1:00-6:00</time>
    </event2>
    <event3>
      <title>总结：正确做法</title>
      <time>6:00-8:00</time>
    </event3>
  </section>
</spec>
```

## 使用示例

**用户**：基于刚才的调研，帮我策划 5 个视频选题

**Agent 执行**：
1. 分析调研报告中的爆款特征
2. 提取高播放量视频的标题模式
3. 生成 5 个选题方案
4. 为每个选题生成简要规约

## 调用方式

```python
from agents.content_agent import ContentAgent

agent = ContentAgent()
result = agent.run(
    research_data=research_result,
    topic_count=5,
    target_duration=480,  # 8分钟
    style="知识科普"
)
```
