# YouTube视频的最小故事 - 项目说明

## 项目概述

基于**认知敏捷法 (42COG)** 构建的YouTube视频创作工作流项目。通过"事件1→事件2→事件3"的三事件最小故事框架，将复杂的调研工作简化为高效的三步走策略。

## 核心框架

### 最小故事工作流

```
事件1：调研x个视频 → 找到领域高手 + 总结创作模式
    ↓
事件2：逆向工程 → 将模式应用到文案创作
    ↓
事件3：实战创作 → 写出解决领域难题的创作文案
    ↓
生发意义：积累skill文档 → 成为领域高手
```

### 核心优势

- **高效性**：2小时内完成从调研到模板的全流程
- **实用性**：输出可直接执行的创作指导
- **可复用性**：积累的skill文档形成知识资产
- **低门槛**：30分钟学习成本，工具链简单易用

## 项目结构

```
youtube 视频的最小故事/
├── .42cog/                      # 42COG框架目录
│   ├── README.md                # 框架说明
│   ├── real/                    # 现实约束
│   │   └── real.md
│   ├── cog/                     # 认知模型
│   │   └── cog.md
│   ├── spec/                    # 规约文档
│   │   ├── README.md
│   │   ├── spec.md
│   │   ├── user/                # 用户角色规约
│   │   │   ├── user.spec.md
│   │   │   ├── cases.spec.md
│   │   │   └── workflow.spec.md
│   │   ├── pm/                  # 产品经理规约
│   │   │   ├── pr.spec.md
│   │   │   ├── userstory.spec.md
│   │   │   └── template.spec.md
│   │   ├── dev/                 # 技术团队规约
│   │   │   ├── sys.spec.md
│   │   │   ├── data.spec.md
│   │   │   ├── ai.spec.md
│   │   │   └── automation.spec.md
│   │   └── design/              # 设计团队规约
│   │       ├── ui.spec.md
│   │       └── visual.spec.md
│   └── work/                    # 实际作品
│       └── work.md
├── src/                         # 源代码实现
│   ├── research/                # 数据收集模块
│   │   └── data_collector.py
│   ├── analysis/                # 模式分析模块
│   │   └── pattern_analyzer.py
│   ├── template/                # 模板生成模块
│   │   └── template_generator.py
│   ├── creator/                 # 内容创建模块
│   │   └── script_creator.py
│   ├── workflow/                # 工作流管理模块
│   │   └── workflow_manager.py
│   └── utils/                   # 工具模块
│       ├── logger.py
│       ├── config.py
│       ├── file_utils.py
│       └── validators.py
├── config/                      # 配置文件
│   ├── config.yaml
│   ├── keywords.yaml
│   └── templates.yaml
├── examples/                    # 示例脚本
│   ├── quick_start.py
│   ├── custom_analysis.py
│   ├── batch_analysis.py
│   └── mcp_integration.py
├── .env.example                # 环境变量模板
├── requirements.txt            # 依赖包列表
├── run.py                      # 统一启动脚本
├── .gitignore                 # Git忽略规则
├── README.md                   # 本文档
├── 快速开始.md                 # 快速开始指南
├── 使用指南.md                 # 详细使用说明
└── PROJECT_SUMMARY.md          # 项目总结
```

## 核心实体

### 1. Researcher（调研员）
负责整个工作流的执行，从数据收集到模式抽象，再到创作转化。

### 2. Sample（视频样本）
被调研的视频对象，从1000个候选中筛选出10个高质量案例。

### 3. Pattern（创作模式）
从样本中抽象出的规律，如"认知冲击型"、"故事叙述型"等。

### 4. Template（创作模板）
可复用的创作框架，直接指导视频创作。

### 5. Workflow（工作流）
完整的三事件流程，确保调研工作高效有序。

## 质量标准

### 数据质量标准
- **精选案例**：10个高质量案例 > 1000个浅层数据
- **模式深度**：必须抽象出可复用的创作规律
- **实用性**：调研结果必须直接指导创作

### 时间效率标准
- **调研时间**：单次不超过2小时
- **分析时间**：30分钟内完成模式抽象
- **学习成本**：30分钟掌握工具使用

### 产出质量标准
- **可执行性**：模板必须能直接用于创作
- **可复用性**：形成的skill文档可反复使用
- **可迭代性**：支持持续优化和扩展

## 快速开始

### 1. 环境准备
```bash
# 检查Python版本（需要3.11+）
python3 --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置MCP环境
```bash
# 检查CC-Switch MCP服务器状态
ps aux | grep cc-switch

# 检查启用的MCP服务器
sqlite3 /Users/su/.cc-switch/cc-switch.db "SELECT name FROM mcp_servers WHERE enabled_claude = 1;"

# 如果需要可选AI服务，可配置环境变量
cp .env.example .env
vim .env
```

### 3. 运行示例
```bash
# 方式1：使用统一启动脚本（推荐）
python3 run.py quick

# 方式2：直接运行示例
python3 examples/quick_start.py

# 方式3：执行完整工作流
python3 run.py workflow --keywords "教程,教学,学习" --max-videos 30
```

### 4. 跨平台跨地区调研（重点功能）⭐

**找出竞争少的领域**：

```bash
# 查看可用地区
python3 research.py regions

# 查看低竞争地区
python3 research.py regions --group low_competition

# 执行真实数据调研（基于实际MCP调用）
python3 research.py real "Python教程"

# 执行多平台调研（模拟数据，演示流程）
python3 research.py multi "数据分析"
```

**核心价值**：
- ✅ 实际调用MCP工具收集YouTube、TikTok、Facebook、Instagram数据
- ✅ 基于真实观看量、频道数、发布时间分析竞争度
- ✅ 对比20个国家/地区，找出信息差和机会点
- ✅ 生成详细的竞争分析和机会推荐报告

**使用步骤**：
1. 在Claude Code中执行MCP命令收集数据
2. 系统自动分析竞争度
3. 查看基于实际数据的分析报告

详细说明请参考 [RESEARCH_TOOL.md](RESEARCH_TOOL.md)

### 5. 查看结果
```bash
# 查看输出文件
ls -la output/quick_start/

# 查看研究报告
cat output/quick_start/research_report.md
```

### 5. 深入理解（可选）
- 阅读 `.42cog/README.md` 了解42COG方法论
- 查看 `.42cog/cog/cog.md` 理解认知模型
- 研究 `src/` 目录中的源代码实现

## 适用人群

- **内容创作者**：快速找到创作灵感
- **短视频运营**：批量生产高质量内容
- **营销人员**：掌握行业创作规律
- **品牌方**：制定有效的内容策略

## 应用场景

- 新领域调研
- 竞品分析
- 爆款内容复盘
- 创作模板构建

## 关键优势

### 相比传统调研方法
- **效率提升5倍以上**
- **分析深度显著提升**
- **输出可直接应用**
- **积累形成知识资产**

### 相比手工分析方式
- **自动化程度高**
- **数据处理能力强**
- **模式识别准确**
- **模板复用性好**

## 发展路线图

### 第一阶段：MVP（最小可行产品）
- 基础工作流引擎
- 案例分析工具
- 模板生成功能
- Web界面原型

### 第二阶段：功能完善
- 完整案例库系统
- AI辅助分析
- 数据可视化
- 移动端适配

### 第三阶段：生产就绪
- 自动化流水线
- 监控系统
- 性能优化
- 安全加固

## 文档导航

### 核心文档
- [框架说明](./.42cog/README.md) - 42COG方法论介绍
- [现实约束](./.42cog/real/real.md) - 项目约束条件
- [认知模型](./.42cog/cog/cog.md) - 核心实体和关系
- [快速开始](./快速开始.md) - 5分钟快速上手指南
- [使用指南](./使用指南.md) - 详细操作说明
- [项目总结](./PROJECT_SUMMARY.md) - 完整项目概述

### 源代码文档
- [MCP数据收集器](./src/research/mcp_data_collector.py) - MCP fetch网页浏览
- [模式分析器](./src/analysis/pattern_analyzer.py) - 数据分析算法
- [模板生成器](./src/template/template_generator.py) - 报告生成系统
- [工作流管理器](./src/workflow/workflow_manager.py) - 三事件流程控制

### 示例文档
- [快速开始示例](./examples/quick_start.py) - 基础三事件工作流
- [自定义分析示例](./examples/custom_analysis.py) - 高级分析功能
- [批量分析示例](./examples/batch_analysis.py) - 多类别并发分析
- [MCP集成示例](./examples/mcp_integration.py) - 与CC-Switch MCP集成

### 配置文档
- [主配置](./config/config.yaml) - 系统配置参数
- [关键词配置](./config/keywords.yaml) - 研究领域关键词
- [模板配置](./config/templates.yaml) - 输出模板定义

### 42COG规范文档
#### 用户视角
- [系统使用规约](./.42cog/spec/user/user.spec.md) - 操作流程指南
- [案例库规约](./.42cog/spec/user/cases.spec.md) - 案例管理机制
- [工作流规约](./.42cog/spec/user/workflow.spec.md) - 三事件执行流程

#### 产品视角
- [产品需求规约](./.42cog/spec/pm/pr.spec.md) - 核心需求定义
- [用户故事规约](./.42cog/spec/pm/userstory.spec.md) - 使用场景描述
- [创作模板规约](./.42cog/spec/pm/template.spec.md) - 模板库管理

#### 技术视角
- [系统架构规约](./.42cog/spec/dev/sys.spec.md) - 技术架构设计
- [数据处理规约](./.42cog/spec/dev/data.spec.md) - 数据处理流程
- [AI辅助规约](./.42cog/spec/dev/ai.spec.md) - AI功能设计
- [自动化规约](./.42cog/spec/dev/automation.spec.md) - 自动化机制

#### 设计视角
- [界面设计规约](./.42cog/spec/design/ui.spec.md) - UI/UX设计规范
- [视觉设计规约](./.42cog/spec/design/visual.spec.md) - 视觉设计标准

## 社区与支持

### 学习资源
- 42COG方法论文档
- 视频教程和案例
- 最佳实践分享
- 常见问题解答

### 反馈渠道
- 工具使用反馈
- 模板质量评价
- 功能改进建议
- 成功案例分享

---

**认知敏捷法 (42COG)** - 让调研工作回归本质：发现模式，创作价值

通过本项目，您将掌握一种全新的调研方法，能够在短时间内从海量数据中提炼出有价值的创作模式，并直接转化为可执行的内容创作方案。
