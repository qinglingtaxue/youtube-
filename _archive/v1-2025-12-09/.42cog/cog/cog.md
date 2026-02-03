---
name: youtube-research-cog
description: Cognitive model for YouTube video creation workflow with three-event minimum story framework
---

# YouTube视频创作工作流 - 认知模型 (Cog)

<cog>
本系统包括以下关键实体：
- researcher：调研员（内容创作者）
- sample：视频样本（被调研的对象）
- pattern：创作模式（从样本中抽象出的规律）
- template：创作模板（可复用的创作框架）
- workflow：工作流（调研到创作的完整流程）
- datasource：数据源（YouTube等平台）
</cog>

<researcher>
- 唯一编码：调研任务的唯一标识符
- 常见分类：新手指南型、深度分析型、快速筛选型
- 核心能力：模式识别、抽象总结、创作转化
</researcher>

<sample>
- 唯一编码：视频ID或频道ID
- 常见分类：高播放量型、新兴赛道型、技巧创新型
- 筛选标准：1000个候选中筛选出10个典型案例
</sample>

<pattern>
- 唯一编码：模式名称（如"认知冲击型"）
- 常见分类：内容结构模式、互动策略模式、视觉呈现模式
- 抽象层级：从具体案例到通用规律的转化
</pattern>

<template>
- 唯一编码：模板ID（如"认知冲击_开头3秒"）
- 常见分类：标题模板、脚本模板、视觉模板
- 应用场景：直接指导视频创作的具体框架
</template>

<workflow>
- 唯一编码：工作流实例ID
- 常见分类：单轮调研型、多轮迭代型、对比分析型
- 核心流程：事件1→事件2→事件3的最小故事
</workflow>

<datasource>
- 唯一编码：平台标识（YouTube、抖音等）
- 常见分类：视频平台、音频平台、图文平台
- 数据特征：实时性、规模性、多样性
</datasource>

<rel>
- researcher-sample：一对多（一个调研员分析多个样本）
- sample-pattern：一对多（一个样本可体现多个模式）
- pattern-template：一对一（一个模式对应一个模板）
- workflow-datasource：多对多（一个工作流可调用多个数据源）
- template-researcher：一对多（一个模板可被多个创作者使用）
</rel>

<events>
- 事件1：调研x个视频 → 找到领域高手 + 总结创作模式
- 事件2：逆向工程 → 将模式应用到文案创作
- 事件3：实战创作 → 写出解决领域难题的创作文案
- 生发意义：积累skill文档 → 成为领域高手
</events>

<framework>
- 最小故事：任何调研都必须遵循三事件结构
- 停止条件：完成事件3即停止，不做无效扩展
- 质量标准：10个高质量案例 > 1000个浅层数据
</framework>
