# Git工作流指南

## 🚀 初始化Git仓库

```bash
# 进入项目目录
cd "/Users/su/Downloads/3d_games/youtube 视频的最小故事"

# 初始化Git仓库
git init

# 配置用户信息
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 添加所有文件
git add .

# 创建初始提交
git commit -m "feat: 初始化YouTube视频研究工作流项目

主要功能:
- 完整的42COG框架实现
- 基于MCP fetch的数据收集方案
- 三事件最小故事工作流
- 动态追踪模块
- 5个示例脚本
- 完整文档体系

技术栈:
- Python 3.11+
- MCP Protocol
- CC-Switch MCP管理
- 42COG Framework"
```

## 📋 版本管理规则

### 版本号规则

采用[语义化版本控制](https://semver.org/lang/zh-CN/)：

- **主版本号 (MAJOR)**：不兼容的API修改
- **次版本号 (MINOR)**：向下兼容的功能性新增
- **修订号 (PATCH)**：向下兼容的问题修正

当前版本：**v0.1.0**

### 提交信息规范

使用[约定式提交](https://www.conventionalcommits.org/zh-hans/)格式：

```
<类型>[可选范围]: <描述>

[可选正文]

[可选脚注]
```

**类型说明**：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链相关

**示例**：
```bash
# 添加新功能
git commit -m "feat: 添加动态追踪模块

- 新增动态追踪器
- 实现趋势监控
- 添加调度器功能
- 集成MCP服务器"

# 修复bug
git commit -m "fix: 修复logger.py语法错误

- 将setLevel和setFormatter拆分为两行
- 确保文件处理器正确配置"

# 更新文档
git commit -m "docs: 更新快速开始指南

- 参考w1_gobang项目QUICKSTART.md
- 添加5分钟快速上手流程
- 完善目录结构说明"
```

## 🏷️ 版本标签管理

### 创建版本标签

```bash
# 获取当前最新版本
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

# 自动计算新版本号（PATCH +1）
NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{$NF = $NF + 1;} 1' | sed 's/ /./g')

# 创建标签
git tag -a $NEW_VERSION -m "Release $NEW_VERSION

主要变更:
- 添加基于MCP fetch的数据收集方案
- 实现动态追踪模块
- 完善Git工作流程
- 更新文档体系"

# 推送提交和标签
git push origin main
git push origin $NEW_VERSION
```

### 版本标签说明格式

每个版本标签应包含：

```
Release v0.1.0 - 项目框架搭建完成

主要功能:
- ✅ 完整的42COG框架实现
- ✅ 基于MCP fetch的数据收集
- ✅ 三事件工作流
- ✅ 动态追踪模块
- ✅ 示例脚本和文档

技术栈:
- Python 3.11+
- MCP Protocol
- CC-Switch
- 42COG Framework

文件统计:
- 46个文件
- 11个源代码模块
- 5个示例脚本
- 9个文档文件

下一版本计划:
- v0.1.1: 优化MCP数据解析
- v0.2.0: 添加Web界面
```

### 查看版本历史

```bash
# 查看所有标签
git tag -l -n9

# 查看最新版本
git describe --tags --abbrev=0

# 查看版本详情
git show v0.1.0

# 查看版本差异
git diff v0.1.0..HEAD
```

## 🌐 GitHub推送流程

### 第一步：创建GitHub仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角 "+" 号
3. 选择 "New repository"
4. 填写仓库信息：
   - Repository name: `youtube-video-research-workflow`
   - Description: `基于42COG框架和MCP技术的YouTube视频模式研究工作流`
   - 设置为 Public 或 Private
   - **不要**初始化README（已存在）
5. 点击 "Create repository"

### 第二步：推送代码

```bash
# 添加远程仓库（替换为您的GitHub仓库URL）
git remote add origin https://github.com/your-username/youtube-video-research-workflow.git

# 推送到GitHub
git push -u origin main

# 推送标签
git push origin --tags
```

### 第三步：创建Release

```bash
# 在GitHub上创建Release
# 访问: https://github.com/your-username/youtube-video-research-workflow/releases
# 点击 "Create a new release"
# 选择标签: v0.1.0
# 标题: v0.1.0 - 项目框架搭建完成
# 描述: 复制标签说明内容
```

## 🔄 持续开发流程

### 日常开发

```bash
# 1. 创建功能分支
git checkout -b feature/dynamic-tracking

# 2. 开发功能
# ... 修改代码 ...

# 3. 提交变更
git add .
git commit -m "feat: 实现动态追踪功能"

# 4. 推送分支
git push origin feature/dynamic-tracking

# 5. 创建Pull Request
# 在GitHub上创建PR并请求审查

# 6. 合并到主分支
# 通过GitHub界面合并PR
```

### 发布新版本

```bash
# 1. 确保在main分支
git checkout main

# 2. 拉取最新代码
git pull origin main

# 3. 更新版本号
# 编辑 .42cog/meta/meta.md

# 4. 创建版本标签
git tag -a v0.1.1 -m "Release v0.1.1

主要变更:
- 优化MCP数据解析
- 修复已知bug
- 改进文档"

# 5. 推送
git push origin main
git push origin v0.1.1
```

## 📊 项目统计

### 文件统计脚本

创建 `scripts/project-stats.sh`：

```bash
#!/bin/bash

echo "YouTube视频研究工作流 - 项目统计"
echo "================================"
echo ""

echo "📁 文件统计:"
echo "  Python文件: $(find . -name "*.py" | wc -l)"
echo "  Markdown文件: $(find . -name "*.md" | wc -l)"
echo "  配置文件: $(find . -name "*.yaml" -o -name "*.yml" | wc -l)"
echo "  总文件数: $(find . -type f | wc -l)"
echo ""

echo "📦 模块统计:"
echo "  核心模块: $(find src -name "*.py" | wc -l)"
echo "  示例脚本: $(find examples -name "*.py" | wc -l)"
echo "  工具模块: $(find src/utils -name "*.py" | wc -l)"
echo ""

echo "📚 文档统计:"
echo "  42COG文档: $(find .42cog -name "*.md" | wc -l)"
echo "  项目文档: $(ls *.md 2>/dev/null | wc -l)"
echo ""

echo "🔗 Git信息:"
echo "  当前分支: $(git branch --show-current)"
echo "  最新标签: $(git describe --tags --abbrev=0 2>/dev/null || echo '无标签')"
echo "  提交次数: $(git rev-list --count HEAD)"
echo "  最后更新: $(git log -1 --format=%cd)"
```

## ❗ 注意事项

1. **不要提交敏感信息**：
   - `.env` 文件（已添加到 `.gitignore`）
   - API密钥
   - 密码等

2. **保持提交原子性**：
   - 每次提交只包含相关变更
   - 避免在一个提交中混合多个功能

3. **编写清晰的提交信息**：
   - 第一行不超过50字符
   - 详细说明在正文中

4. **定期更新文档**：
   - 修改代码后更新相关文档
   - 在提交信息中提及文档更新

5. **遵循语义化版本**：
   - 破坏性变更 → 主版本号+1
   - 新功能 → 次版本号+1
   - 修复 → 修订号+1

## 🔗 相关资源

- [Git官方文档](https://git-scm.com/doc)
- [GitHub官方指南](https://guides.github.com/)
- [约定式提交](https://www.conventionalcommits.org/)
- [语义化版本](https://semver.org/)
- [42COG框架](https://42cog.com)

---

**遵循此工作流程，确保项目可维护、可追溯、可协作！** 🚀
