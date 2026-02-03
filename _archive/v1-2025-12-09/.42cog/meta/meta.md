# 项目元信息

**项目名称**: YouTube视频研究工作流
**项目标语**: 基于42COG框架和MCP技术的YouTube视频模式研究与内容创作工作流
**版本**: 0.1.0
**创建日期**: 2025-12-09
**负责人**: Claude Code

## 版本历史

### v0.1.0 (2025-12-09)
**初始版本** - 项目框架搭建

**主要功能**:
- ✅ 完整的42COG框架实现（Real→Cog→Spec→Work）
- ✅ 基于MCP fetch的数据收集方案（替代YouTube API）
- ✅ 三事件最小故事工作流（数据收集→模式分析→内容创作）
- ✅ 动态追踪模块（长期模式+短期趋势）
- ✅ 完整的工具模块（logger、config、validators等）
- ✅ 5个示例脚本（quick_start、custom_analysis、batch_analysis、dynamic_tracking、mcp_integration）
- ✅ 统一启动脚本（run.py）
- ✅ 完整文档体系（README、快速开始、使用指南等）

**技术栈**:
- Python 3.11+
- MCP Protocol (mcp-server-fetch, tavily, sequential-thinking等)
- CC-Switch MCP管理
- 42COG Framework

**数据方案**:
- 原计划：YouTube Data API v3
- 实际采用：MCP fetch真实网页浏览
- 优势：无需API配额限制，直接获取真实数据

**核心创新**:
1. 双轨研究系统：长期模式（每3天）+ 短期动态（每小时）
2. MCP生态集成：避免重复造轮子，直接使用现有MCP服务器
3. 模式驱动研究：从搜索驱动转向模式驱动，提高效率
4. 最小故事框架：事件1→事件2→事件3的简化工作流

**文件统计**:
- 42COG框架文档: 18个
- 源代码模块: 11个
- 示例脚本: 5个
- 配置文件: 3个
- 项目文档: 9个
- 总计: 46个文件
