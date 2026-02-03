# workflow-agent - 工作流编排智能体

编排和管理完整内容创作流水线的智能代理。

## 能力

- 理解用户意图
- 拆解任务步骤
- 调度其他 Agent
- 追踪流程进度
- 处理异常情况

## 触发条件

- 用户请求完成端到端任务
- 需要协调多个阶段的工作
- 复杂任务需要拆解执行

## 工作流程

```
用户请求
    ↓
意图理解 → 确定目标和约束
    ↓
任务拆解 → 分解为子任务
    ↓
调度执行：
    ├── research-agent（调研）
    ├── content-agent（策划）
    ├── production-agent（制作）
    └── publish-agent（发布）
    ↓
进度追踪 → 监控各阶段状态
    ↓
结果汇总 → 输出最终报告
```

## 支持的工作流

### 1. 完整流水线
```
调研 → 分析 → 策划 → 制作 → 发布 → 复盘
```

### 2. 快速调研
```
采集 → 分析 → 报告
```

### 3. 内容策划
```
加载数据 → 分析模式 → 生成选题 → 输出规约
```

### 4. 批量发布
```
检查视频 → 上传 → 设置元数据 → 验证
```

## 使用示例

**用户**：帮我完成一个"老人养生"主题的视频，从调研到策划

**Agent 执行**：
```
[workflow-agent] 理解任务：完成调研到策划的流程
[workflow-agent] 调度 research-agent...
    [research-agent] 采集 1000 个视频
    [research-agent] 分析市场数据
    [research-agent] 生成调研报告 ✓
[workflow-agent] 调度 content-agent...
    [content-agent] 分析爆款特征
    [content-agent] 生成 5 个选题
    [content-agent] 输出视频规约 ✓
[workflow-agent] 流程完成，输出：
    - 调研报告：data/reports/research_xxx.html
    - 选题列表：5 个
    - 视频规约：specs/video_xxx.md
```

## 状态管理

```yaml
workflow_state:
  id: "wf_20260119_001"
  status: "running"
  current_stage: "planning"
  stages:
    research:
      status: "completed"
      output: "data/reports/research_xxx.html"
    analysis:
      status: "completed"
      output: "data/analysis/market_xxx.json"
    planning:
      status: "running"
      progress: 60%
    production:
      status: "pending"
    publishing:
      status: "pending"
```

## 调用方式

```python
from agents.workflow_agent import WorkflowAgent

agent = WorkflowAgent()
result = agent.run(
    intent="完成老人养生主题的视频，从调研到策划",
    stages=["research", "analysis", "planning"],
    auto_proceed=True
)
```
