# 🚀 Claude Code 项目配置目录

## 目录概述

`.claude` 目录是 Claude Code 在此项目中的配置和 skills 管理目录。

```
.claude/
├── README.md                   # 本文件 - 配置说明
├── settings.local.json         # Claude Code 本地配置
└── skills/                     # 注册的 Claude Skills
    └── check-naming-violations.skill.md (软连接)
```

---

## 📋 配置说明

### settings.local.json

**作用**: Claude Code 的项目级配置文件

**主要配置项**:

#### 1. 项目信息
```json
"project": {
  "name": "youtube-minimal-video-story-v3",
  "displayName": "YouTube 最小化视频故事创建工具 (v3)",
  "version": "3.0.0"
}
```

#### 2. Claude Skills 管理
```json
"skills": {
  "enabled": true,
  "autoLoad": true,
  "directory": ".claude/skills",
  "skills": [
    {
      "id": "check-naming-violations",
      "name": "命名规约检查工具",
      "enabled": true
    }
  ]
}
```

#### 3. 开发环境配置
```json
"environment": {
  "os": "macOS",
  "arch": "arm64",
  "nodeManager": "bun",
  "pythonManager": "uv",
  "gitPlatform": "cnb.cool",
  "language": "zh-CN"
}
```

#### 4. 工具链配置
- **Node.js**: 通过 bun 管理
- **Python**: 通过 uv 管理
- **Git**: cnb.cool 平台

#### 5. 文件忽略规则
```json
"ignorePatterns": {
  "gitignore": ".gitignore",
  "claudeignore": ".claudeignore"
}
```

---

## 🔗 Claude Skills 管理

### Skills 来源

所有 Claude Skills 通过**软连接**从 `.42cog/skills` 目录链接到 `.claude/skills` 目录。

**好处**:
- ✅ 源文件保持单一位置
- ✅ 便于版本管理
- ✅ 自动同步更新
- ✅ 节省存储空间

### 当前注册的 Skills

#### 1. 命名规约检查工具 (check-naming-violations)

**来源**: `.42cog/skills/check-naming-violations.skill.md`

**功能**:
- 检查项目中的文件命名冲突
- 审计违反编码规约的文件
- 验证文件元数据完整性
- 检查文件关系映射

**类型**: audit（审计工具）

**触发方式**: 手动触发

**使用方式**:
```
在 Claude Code 中输入:
- "检查我的文件名"
- "审计命名冲突"
- "验证编码规约"
- "生成文件清单"
```

---

## 📁 文件忽略规则

### .gitignore

Git 版本控制的忽略规则
- 位置: 项目根目录
- 管理: 依赖、编译产物、敏感文件等

### .claudeignore

Claude Code 代码分析的忽略规则
- 位置: 项目根目录
- 管理: 大文件、缓存、非源代码等

---

## 🔧 配置修改指南

### 添加新的 Claude Skill

#### 步骤 1: 创建 Skill 文件

在 `.42cog/skills/` 目录下创建新的 skill 文件:
```bash
# 文件命名规则: {skill-name}.skill.md
touch .42cog/skills/my-skill.skill.md
```

#### 步骤 2: 创建软连接

```bash
ln -s /absolute/path/to/.42cog/skills/my-skill.skill.md .claude/skills/my-skill.skill.md
```

#### 步骤 3: 更新配置

编辑 `settings.local.json`，在 `skills.skills` 数组中添加:
```json
{
  "id": "my-skill",
  "name": "我的 Skill 名称",
  "description": "Skill 描述",
  "type": "tool|audit|generator",
  "path": ".claude/skills/my-skill.skill.md",
  "enabled": true
}
```

### 禁用某个 Skill

编辑 `settings.local.json`，将对应 skill 的 `enabled` 设为 `false`:
```json
{
  "id": "check-naming-violations",
  "enabled": false
}
```

---

## 🛠️ 常用命令

### 列出所有 Skills

```bash
# 查看 .claude/skills 目录
ls -la .claude/skills/

# 查看 settings.local.json 中的 skills 列表
cat .claude/settings.local.json | jq .skills
```

### 验证软连接

```bash
# 检查软连接是否正确
ls -lL .claude/skills/

# 测试软连接指向的文件是否存在
file .claude/skills/*.skill.md
```

### 清理断裂的软连接

```bash
# 找出断裂的软连接
find .claude/skills -type l ! -exec test -e {} \; -print

# 删除断裂的软连接
find .claude/skills -type l ! -exec test -e {} \; -delete
```

---

## 📊 配置检查清单

- [x] `.claude/` 目录已创建
- [x] `.claude/skills/` 子目录已创建
- [x] 软连接已创建: `check-naming-violations.skill.md`
- [x] `settings.local.json` 已配置
- [x] 项目信息已填写
- [x] 环境配置已设置
- [x] 工具链已配置
- [x] Skills 已注册
- [x] 文件忽略规则已配置
- [x] README 文档已完成

---

## 🎯 使用 Claude Skills

### 在项目中使用 Skill

Claude Code 会自动加载 `settings.local.json` 中启用的 skills。

### 调用 Skill

使用斜杠命令或自然语言触发:
```
/check-naming-violations
或
"帮我检查项目中的命名冲突"
```

### 参考文档

- Claude Code 官方文档: https://claude.com/claude-code
- Skill 开发指南: 参考 `.42cog/skills/` 中的示例

---

## 📝 维护建议

### 定期检查

1. **每月检查一次** 软连接的完整性
2. **新增 Skill 时** 及时更新 `settings.local.json`
3. **项目更新时** 验证配置的一致性

### 备份建议

保持 `settings.local.json` 的备份:
```bash
cp .claude/settings.local.json .claude/settings.local.json.bak
```

---

## 🚨 故障排除

### 软连接不生效

**症状**: 软连接存在但无法访问

**解决**:
```bash
# 验证源文件是否存在
test -f /absolute/path/to/source && echo "源文件存在" || echo "源文件不存在"

# 重新创建软连接
rm .claude/skills/broken-link.skill.md
ln -s /absolute/path/to/source .claude/skills/broken-link.skill.md
```

### 导入 Skill 时出错

**症状**: 加载 Skill 时报错

**解决**:
1. 检查 `settings.local.json` 的 JSON 格式是否正确
2. 检查 `path` 字段是否正确
3. 验证 skill 文件头的 YAML 格式

---

## 📚 相关文件

- **CLAUDE.md**: 项目级 Claude Code 配置
- **.gitignore**: Git 忽略规则
- **.claudeignore**: Claude Code 分析忽略规则
- **.42cog/skills/**: Skill 源文件位置

---

## ℹ️ 更多信息

- 项目初始化报告: `PROJECT_INIT_REPORT.md`
- 项目配置文档: `CLAUDE.md`
- 项目结构规范: `.42cog/spec/`

---

**最后更新**: 2026-02-03
**配置版本**: 1.0.0
**状态**: ✅ 已激活

*由 Claude Code 生成和维护*
