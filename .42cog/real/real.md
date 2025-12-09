---
name: youtube-research-real
description: Real-world constraints for YouTube video creation workflow using MCP fetch instead of YouTube API
---

# YouTube视频研究工作流 - 现实约束 (Real)

<real>
- 必须使用MCP工具进行真实网页浏览（推荐playwright MCP处理动态内容，mcp-server-fetch处理静态页面），不得依赖YouTube API（避免配额限制）
- 单次调研时间不超过2小时，必须产出可执行的洞察
- 收集的数据必须能在30分钟内完成分析并抽象出模式
- 调研结果必须能直接指导创作，无需二次转化
- 整个工作流必须比手工方式快5倍以上
- 分析报告必须用"三事件最小故事"结构呈现
- 工具链使用门槛不能超过30分钟学习成本
- 必须支持从1000个样本中快速筛选出10个高质量案例
- 最终产出是具体的创作模板，而非泛泛的数据报表
- 所有数据收集必须通过CC-Switch管理的MCP服务器进行
</real>
