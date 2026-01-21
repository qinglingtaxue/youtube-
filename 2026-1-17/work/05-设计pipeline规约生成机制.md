# TD-05: Pipeline 规约生成机制 / Pipeline Specification Mechanism

> 声明式数据处理流程定义与执行框架
> Declarative data processing workflow definition and execution framework

---

## 决策概要 / Decision Summary

| 属性 / Attribute | 值 / Value |
|------------------|------------|
| 决策编号 / ID | TD-05 |
| 决策类型 / Type | 系统架构 / System Architecture |
| 决策日期 / Date | 2026-01-18 |
| 来源对话 / Source | cbe9596b |
| 状态 / Status | 已执行 / Implemented |

---

## 架构结构 / Architecture Structure

```
pipeline/
├── specs/                  # 规约定义 / Spec Definitions
│   ├── video-collection.yaml
│   ├── channel-analysis.yaml
│   └── trend-report.yaml
├── stages/                 # 阶段实现 / Stage Implementations
│   ├── collect/            # 采集阶段
│   ├── transform/          # 转换阶段
│   ├── analyze/            # 分析阶段
│   └── export/             # 导出阶段
├── engine/                 # 执行引擎 / Execution Engine
│   ├── parser.ts           # 规约解析器
│   ├── executor.ts         # 阶段执行器
│   └── monitor.ts          # 执行监控
├── plugins/                # 插件扩展 / Plugins
│   └── custom-stage.ts
└── README.md
```

---

## 核心组件索引 / Core Component Index

| # | 组件 / Component | 中文说明 | English Description | 职责 / Responsibility |
|---|------------------|---------|---------------------|----------------------|
| 1 | Spec Parser | 规约解析器 | Parses YAML/JSON specs | 验证并解析规约文件 |
| 2 | Stage Executor | 阶段执行器 | Executes pipeline stages | 按顺序执行各阶段 |
| 3 | Data Connector | 数据连接器 | Connects stages | 阶段间数据传递 |
| 4 | Monitor | 执行监控 | Monitors execution | 进度、错误、日志 |
| 5 | Plugin System | 插件系统 | Extends functionality | 自定义阶段扩展 |

---

## 规约详解 / Specification Details

### 1. 规约结构 / Spec Structure

```yaml
# specs/video-collection.yaml
pipeline:
  name: youtube-video-collection
  version: "1.0.0"
  description: "YouTube 视频数据采集与分析流水线"

  # 全局配置
  config:
    timeout: 3600000        # 1小时超时
    retryOnFailure: true
    maxRetries: 3

  # 阶段定义
  stages:
    - name: collect
      type: rpa
      description: "采集 YouTube 视频数据"
      input:
        source: config
        path: keywords.json
      output:
        type: file
        path: data/raw/videos-{{timestamp}}.json
      config:
        maxVideos: 1000
        timeRange: 7d
        sortBy: views

    - name: transform
      type: process
      description: "数据清洗与转换"
      input:
        source: stage
        stage: collect
      output:
        type: file
        path: data/processed/videos-clean.json
      operations:
        - dedup:
            key: id
        - normalize:
            fields: [views, likes, comments]
        - enrich:
            addFields: [engagement_rate, growth_score]
        - filter:
            condition: "views >= 1000"

    - name: analyze
      type: compute
      description: "数据分析与指标计算"
      input:
        source: stage
        stage: transform
      output:
        type: file
        path: data/analyzed/videos-metrics.json
      metrics:
        - name: top_videos
          type: ranking
          by: views
          limit: 50
        - name: category_distribution
          type: groupBy
          field: category
        - name: trend_analysis
          type: timeSeries
          field: publishedAt
          interval: day

    - name: export
      type: output
      description: "导出多种格式"
      input:
        source: stage
        stage: analyze
      formats:
        - type: json
          path: output/videos.json
        - type: csv
          path: output/videos.csv
        - type: html
          path: output/report.html
          template: templates/report.html
```

---

### 2. 阶段类型 / Stage Types

| 类型 / Type | 中文说明 | English Description | 典型操作 / Operations |
|-------------|---------|---------------------|----------------------|
| `rpa` | RPA 采集 | RPA collection | 浏览器自动化采集 |
| `process` | 数据处理 | Data processing | 清洗、转换、过滤 |
| `compute` | 计算分析 | Computation | 聚合、统计、排名 |
| `output` | 结果导出 | Export output | JSON、CSV、HTML |
| `custom` | 自定义 | Custom stage | 插件扩展 |

**处理操作详解 / Process Operations:**

```yaml
operations:
  # 去重
  - dedup:
      key: id                    # 去重字段
      keepFirst: true            # 保留第一条

  # 字段标准化
  - normalize:
      fields:
        - name: views
          type: number
          default: 0
        - name: publishedAt
          type: date
          format: ISO8601

  # 数据增强
  - enrich:
      addFields:
        - name: engagement_rate
          formula: "(likes + comments) / views"
        - name: days_since_publish
          formula: "daysDiff(now, publishedAt)"

  # 条件过滤
  - filter:
      condition: "views >= 1000 AND duration >= 60"

  # 字段映射
  - map:
      from: channelTitle
      to: channel_name

  # 排序
  - sort:
      by: views
      order: desc
```

---

### 3. 执行引擎 / Execution Engine

```typescript
// engine/executor.ts
interface PipelineSpec {
  name: string
  version: string
  stages: StageSpec[]
}

interface StageSpec {
  name: string
  type: 'rpa' | 'process' | 'compute' | 'output' | 'custom'
  input: InputConfig
  output: OutputConfig
  config?: Record<string, any>
}

interface ExecutionContext {
  pipelineId: string
  startTime: Date
  currentStage: string
  data: Record<string, any>
  errors: Error[]
}

class PipelineExecutor {
  private stages: Map<string, StageHandler> = new Map()

  constructor() {
    this.registerBuiltinStages()
  }

  async execute(spec: PipelineSpec): Promise<ExecutionResult> {
    const context: ExecutionContext = {
      pipelineId: generateId(),
      startTime: new Date(),
      currentStage: '',
      data: {},
      errors: [],
    }

    console.log(`[Pipeline] Starting: ${spec.name} v${spec.version}`)

    for (const stageSpec of spec.stages) {
      context.currentStage = stageSpec.name
      console.log(`[Stage] Running: ${stageSpec.name}`)

      try {
        const handler = this.stages.get(stageSpec.type)
        if (!handler) {
          throw new Error(`Unknown stage type: ${stageSpec.type}`)
        }

        const input = await this.resolveInput(stageSpec.input, context)
        const output = await handler.execute(input, stageSpec.config)
        await this.writeOutput(stageSpec.output, output)

        context.data[stageSpec.name] = output
        console.log(`[Stage] Completed: ${stageSpec.name}`)

      } catch (error) {
        context.errors.push(error as Error)
        console.error(`[Stage] Failed: ${stageSpec.name}`, error)

        if (!spec.config?.retryOnFailure) {
          throw error
        }
      }
    }

    return {
      pipelineId: context.pipelineId,
      duration: Date.now() - context.startTime.getTime(),
      stages: spec.stages.map(s => s.name),
      errors: context.errors,
    }
  }

  private registerBuiltinStages(): void {
    this.stages.set('rpa', new RpaStageHandler())
    this.stages.set('process', new ProcessStageHandler())
    this.stages.set('compute', new ComputeStageHandler())
    this.stages.set('output', new OutputStageHandler())
  }
}
```

---

### 4. 数据流示意 / Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Pipeline Executor                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│   Stage 1     │         │   Stage 2     │         │   Stage 3     │
│   collect     │ ──────▶ │   transform   │ ──────▶ │   analyze     │
│               │  JSON   │               │  JSON   │               │
│  (RPA采集)    │         │  (数据清洗)    │         │  (指标计算)   │
└───────────────┘         └───────────────┘         └───────────────┘
        │                                                   │
        │                                                   ▼
        │                                           ┌───────────────┐
        │                                           │   Stage 4     │
        │                                           │   export      │
        │                                           │               │
        │                                           │  (多格式导出)  │
        │                                           └───────────────┘
        │                                                   │
        ▼                                                   ▼
   raw/*.json                                    output/{json,csv,html}
```

---

## 规约验证 / Spec Validation

```typescript
// engine/parser.ts
import Ajv from 'ajv'

const pipelineSchema = {
  type: 'object',
  required: ['name', 'version', 'stages'],
  properties: {
    name: { type: 'string', minLength: 1 },
    version: { type: 'string', pattern: '^\\d+\\.\\d+\\.\\d+$' },
    stages: {
      type: 'array',
      minItems: 1,
      items: {
        type: 'object',
        required: ['name', 'type'],
        properties: {
          name: { type: 'string' },
          type: { enum: ['rpa', 'process', 'compute', 'output', 'custom'] },
        },
      },
    },
  },
}

function validateSpec(spec: unknown): PipelineSpec {
  const ajv = new Ajv()
  const validate = ajv.compile(pipelineSchema)

  if (!validate(spec)) {
    throw new Error(`Invalid spec: ${JSON.stringify(validate.errors)}`)
  }

  return spec as PipelineSpec
}
```

---

## 快速导航 / Quick Navigation

### 想创建新的流水线？ / Want to create a new pipeline?
→ 复制 `specs/video-collection.yaml` 并修改

### 想添加自定义阶段？ / Want to add custom stage?
→ 在 `plugins/` 目录创建并注册

### 想了解上游数据来源？ / Want upstream data source?
→ 阅读 [TD-04: RPA 矩阵架构](./04-采用RPA固化脚本矩阵架构.md)

### 想了解数据展示？ / Want data presentation?
→ 阅读 [TD-07: 多页面交互架构](./07-确定多页面交互系统架构.md)

---

## 设计原则 / Design Principles

1. **声明式优于命令式 / Declarative over Imperative**
   - 描述"做什么"而非"怎么做"
   - 配置而非代码

2. **阶段解耦 / Stage Decoupling**
   - 各阶段独立可替换
   - 通过标准接口通信

3. **可扩展性 / Extensibility**
   - 插件机制支持自定义阶段
   - 不修改核心代码即可扩展

4. **可观测性 / Observability**
   - 执行日志完整记录
   - 进度和错误实时监控

---

## 注意事项 / Notes

1. **版本管理 / Versioning**：规约文件纳入版本控制
2. **向后兼容 / Compatibility**：新版本保持向后兼容
3. **错误恢复 / Recovery**：支持从失败阶段重试
4. **资源清理 / Cleanup**：执行完成后清理临时文件
5. **性能监控 / Performance**：记录各阶段执行耗时

---

## 相关决策 / Related Decisions

| 决策 / Decision | 关系 / Relation |
|-----------------|-----------------|
| [TD-04](./04-采用RPA固化脚本矩阵架构.md) | 上游：数据采集 |
| [TD-07](./07-确定多页面交互系统架构.md) | 下游：数据展示 |

---

*最后更新 / Last Updated: 2026-01-20*
