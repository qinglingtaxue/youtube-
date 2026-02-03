# 规约文档结构说明 (Spec Structure)

本目录包含基于**认知敏捷法 (42COG)** 的规约文档，围绕YouTube视频创作的"最小故事"工作流组织。

---

## 角色与技能体系

### 1. 用户角色 (/42cog:user)

**目录**：`spec/user/`

用户角色关注系统使用、操作流程和用户体验。

#### 技能列表

| 技能标识 | 文档 | 说明 |
|---------|------|------|
| `/42cog:user:usage` | `user.spec.md` | 系统使用规约（调研流程、操作指南） |
| `/42cog:user:cases` | `cases.spec.md` | 案例库规约（典型案例管理、复用） |
| `/42cog:user:workflow` | `workflow.spec.md` | 工作流规约（完整执行流程） |

---

### 2. 产品经理 (/42cog:pm)

**目录**：`spec/pm/`

产品经理角色关注需求定义、用户故事和创作模板。

#### 技能列表

| 技能标识 | 文档 | 说明 |
|---------|------|------|
| `/42cog:pm:pr` | `pr.spec.md` | 产品需求规约（Product Requirements） |
| `/42cog:pm:userstory` | `userstory.spec.md` | 用户故事规约（User Story） |
| `/42cog:pm:template` | `template.spec.md` | 创作模板规约（Template Library） |

---

### 3. 技术团队 (/42cog:tech)

**目录**：`spec/dev/`

技术团队角色关注系统架构、工具开发和自动化实现。

#### 技能列表

| 技能标识 | 文档 | 说明 |
|---------|------|------|
| `/42cog:tech:sys` | `sys.spec.md` | 系统架构规约（System Architecture） |
| `/42cog:tech:data` | `data.spec.md` | 数据处理规约（Data Processing） |
| `/42cog:tech:ai` | `ai.spec.md` | AI辅助规约（AI Assistant） |
| `/42cog:tech:automation` | `automation.spec.md` | 自动化规约（Workflow Automation） |

---

### 4. 设计团队 (/42cog:design)

**目录**：`spec/design/`

设计团队角色关注界面设计、视觉呈现和用户体验。

#### 技能列表

| 技能标识 | 文档 | 说明 |
|---------|------|------|
| `/42cog:design:ui` | `ui.spec.md` | 界面设计规约（UI Design） |
| `/42cog:design:visual` | `visual.spec.md` | 视觉设计规约（Visual Design） |

---

## 核心工作流

```
Real (现实约束) → Cog (认知模型) → Spec (规约文档) → Work (实际作品)
     ↓                 ↓                  ↓                  ↓
  real.md           cog.md            *.spec.md          实际工具
```

### 最小故事工作流

1. **事件1**：调研分析 → 产出典型案例 + 模式总结
2. **事件2**：模式抽象 → 生成创作模板
3. **事件3**：实战应用 → 输出创作文案
4. **生发意义**：积累skill文档 → 成为领域专家

### 规约生成流程

1. **输入**：
   - `real.md` - 现实约束（时间、效率、质量要求）
   - `cog.md` - 认知模型（实体、关系、框架）

2. **角色选择**：根据任务选择对应角色
   - 流程设计 → User角色 → `user:workflow`
   - 模板开发 → PM角色 → `pm:template`
   - 工具实现 → Tech角色 → `tech:automation`
   - 界面设计 → Design角色 → `design:ui`

3. **生成规约**：基于real和cog生成具体规约文档

4. **输出**：可执行的工具、模板、流程指南

---

## 核心质量标准

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

---

## 快速开始

### 1. 创建项目
```bash
mkdir youtube-minimal-story
cd youtube-minimal-story
```

### 2. 初始化42COG
```bash
# 复制本项目结构
cp -r /path/to/youtube-minimal-story-template/* .
```

### 3. 定义现实约束
```bash
# 编辑 .42cog/real/real.md
# 定义调研主题、时间限制、质量要求
```

### 4. 构建认知模型
```bash
# 编辑 .42cog/cog/cog.md
# 定义实体、关系、工作流
```

### 5. 生成规约文档
```bash
# 基于real和cog生成对应规约
# 或使用42COG命令自动生成
```

### 6. 执行工作流
```bash
# 按三事件最小故事执行
# 事件1：调研分析
# 事件2：模式抽象
# 事件3：实战创作
```

---

## 注意事项

1. **最小故事优先**：所有工作必须围绕三事件结构展开
2. **质量胜过数量**：精选10个案例，胜过收集1000条数据
3. **立即转化**：调研结果必须在30分钟内转化为可执行模板
4. **持续迭代**：每次工作流执行后都要积累skill文档

---

**认知敏捷法 (42COG)** - 从调研到创作的最短路径
