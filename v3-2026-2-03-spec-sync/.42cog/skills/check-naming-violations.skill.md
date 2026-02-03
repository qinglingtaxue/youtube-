---
name: check-naming-violations
description: 检查项目中的文件命名冲突和违反规约的文件
type: audit
trigger: manual
created: 2026-02-03
version: 1.0
---

# Skill: 命名规约检查工具 (Check Naming Violations)

## 功能概述

这个 skill 用于**审计项目中的所有文件**，检测：
1. 同目录重名文件
2. 违反编码规约的文件名
3. 缺少必要元数据的卡片
4. 同主题文件的关系是否在映射表中标注

## 触发条件

用户执行以下任何操作时触发：
- "检查我的文件名"
- "审计命名冲突"
- "验证编码规约"
- "生成文件清单"

## 执行步骤

### Step 1: 扫描项目结构

遍历项目的所有文件（排除 `.git`, `node_modules`, `.42cog/cache` 等）：

```python
def scan_files():
    """
    扫描项目结构，返回所有需要检查的文件
    """
    excluded_dirs = ['.git', 'node_modules', '.42cog/cache', '__pycache__']
    files = []

    for root, dirs, filenames in os.walk('.'):
        # 过滤排除目录
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for filename in filenames:
            if filename.endswith(('.md', '.yaml', '.yml', '.json')):
                filepath = os.path.join(root, filename)
                files.append({
                    'path': filepath,
                    'name': filename,
                    'dir': root,
                    'ext': os.path.splitext(filename)[1]
                })

    return files
```

### Step 2: 检测命名规约违反

对每个文件检查以下规则：

#### Rule 1: 同目录重名检查
```python
def check_duplicate_in_dir(files):
    """检查同目录中是否有重名文件"""
    violations = []

    for dir_path, dir_files in group_by_directory(files):
        # 按文件名（不含扩展）分组
        by_name = {}
        for f in dir_files:
            name_without_ext = os.path.splitext(f['name'])[0]
            if name_without_ext not in by_name:
                by_name[name_without_ext] = []
            by_name[name_without_ext].append(f)

        # 查找重复
        for name, file_list in by_name.items():
            if len(file_list) > 1:
                violations.append({
                    'type': 'DUPLICATE_IN_DIR',
                    'directory': dir_path,
                    'files': [f['path'] for f in file_list],
                    'severity': 'CRITICAL'
                })

    return violations
```

#### Rule 2: 格式检查

对文档级文件检查格式：`YYYYMMDD_type_topic.md`

```python
def validate_document_name(filename):
    """检查文档级文件名是否符合规约"""
    pattern = r'^(\d{8})_(spec|log|insight|template|guide|report|note)_([a-z0-9-]+)\.md$'
    match = re.match(pattern, filename)

    if not match:
        return {
            'valid': False,
            'reason': f'文件名不符合规约格式: {filename}',
            'expected_format': 'YYYYMMDD_type_topic.md'
        }

    date_str, file_type, topic = match.groups()

    # 检查日期有效性
    try:
        date = datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        return {
            'valid': False,
            'reason': f'日期无效: {date_str}',
            'expected_format': 'YYYYMMDD (如: 20260203)'
        }

    return {'valid': True, 'date': date, 'type': file_type, 'topic': topic}
```

#### Rule 3: 卡片元数据检查

检查 `.md` 文件是否有有效的 YAML 前置元数据和 id：

```python
def validate_card_metadata(file_path):
    """检查卡片是否有必要的元数据"""
    with open(file_path, 'r') as f:
        content = f.read()

    # 检查 YAML 前置
    if not content.startswith('---'):
        return {
            'valid': False,
            'reason': '缺少 YAML 前置元数据'
        }

    # 提取 YAML
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {
            'valid': False,
            'reason': 'YAML 前置格式不正确'
        }

    try:
        yaml_content = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return {
            'valid': False,
            'reason': f'YAML 解析错误: {e}'
        }

    # 检查必要字段
    required_fields = ['id', 'type', 'title']
    missing = [f for f in required_fields if f not in yaml_content]

    if missing:
        return {
            'valid': False,
            'reason': f'缺少必要字段: {missing}'
        }

    return {'valid': True, 'metadata': yaml_content}
```

### Step 3: 检测同主题文件

```python
def find_same_topic_files(files):
    """查找同主题的文件"""
    by_topic = {}

    for f in files:
        # 提取主题（文件名中 type 之后的部分）
        match = re.match(r'^(\d{8})_(.*?)_(.+)\.md$', f['name'])
        if match:
            topic = match.group(3)  # 主题部分
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(f)

    # 筛选出有多个版本的主题
    same_topic = {topic: files for topic, files in by_topic.items() if len(files) > 1}

    return same_topic
```

### Step 4: 检查映射表

```python
def validate_mapping_table(cog_path, same_topic_files):
    """检查 cog.md 中的同主题映射表是否完整"""
    with open(cog_path, 'r') as f:
        cog_content = f.read()

    # 提取映射表
    mapping_section = re.search(
        r'## 同主题文件关系映射.*?\n(.*?)(?=\n---|\n##|\Z)',
        cog_content,
        re.DOTALL
    )

    violations = []

    for topic, files in same_topic_files.items():
        mapped_files = set()

        if mapping_section:
            table_content = mapping_section.group(1)
            # 检查每个文件是否在映射表中
            for f in files:
                if f['name'] not in table_content:
                    violations.append({
                        'type': 'UNMAPPED_FILE',
                        'topic': topic,
                        'file': f['path'],
                        'severity': 'WARNING',
                        'action': f'请在 cog.md#同主题文件关系映射 中添加该文件'
                    })
        else:
            violations.append({
                'type': 'MISSING_MAPPING_TABLE',
                'severity': 'WARNING',
                'action': '请在 cog.md 中补充 "## 同主题文件关系映射" 章节'
            })

    return violations
```

### Step 5: 生成报告

```python
def generate_report(violations, same_topic_files, scanned_file_count):
    """
    生成审计报告
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'scanned_files': scanned_file_count,
        'critical_violations': [],
        'warnings': [],
        'statistics': {
            'total_violations': len(violations),
            'by_severity': {},
            'same_topic_groups': len(same_topic_files)
        },
        'recommendations': []
    }

    # 分类统计
    for v in violations:
        severity = v.get('severity', 'INFO')
        if severity not in report['statistics']['by_severity']:
            report['statistics']['by_severity'][severity] = 0
        report['statistics']['by_severity'][severity] += 1

        if severity == 'CRITICAL':
            report['critical_violations'].append(v)
        else:
            report['warnings'].append(v)

    # 生成建议
    if report['critical_violations']:
        report['recommendations'].append({
            'priority': 1,
            'action': '立即修复所有 CRITICAL 级别的重名文件',
            'steps': [
                '1. 手动审查冲突的文件，确认哪个是最新版本',
                '2. 删除旧版本文件',
                '3. 重新运行此检查确认问题已解决'
            ]
        })

    if len(same_topic_files) > 0:
        report['recommendations'].append({
            'priority': 2,
            'action': f'更新 cog.md 中的同主题映射表（当前 {len(same_topic_files)} 个主题）',
            'steps': [
                '1. 在 cog.md 的 "## 同主题文件关系映射" 章节添加表格行',
                '2. 记录文件的关系、状态和说明',
                '3. 用 "active" 标记活跃文件，"deprecated" 标记过期文件'
            ]
        })

    return report
```

## 输出格式

### 标准输出（终端显示）

```
╔════════════════════════════════════════════════════════════════╗
║         命名规约审计报告 (Naming Convention Audit Report)      ║
╠════════════════════════════════════════════════════════════════╣
║ 扫描时间: 2026-02-03 18:30:45                                   ║
║ 扫描文件数: 248                                                  ║
║ 发现违反数: 3                                                    ║
║   ├─ CRITICAL: 1 个                                             ║
║   ├─ WARNING: 2 个                                              ║
║   └─ INFO: 0 个                                                 ║
╠════════════════════════════════════════════════════════════════╣

【严重问题 (CRITICAL)】

1. 同目录重名文件
   📂 .42cog/spec/dev/
   └─ 冲突文件:
      - sys.spec.md
      - sys.spec.md (2)  ← ❌ 重复！
   💡 建议: 检查这两个文件的内容，删除较旧的版本

【警告 (WARNING)】

2. 文件名格式不符合规约
   📄 src/data_collector.py (非 .md 文件，跳过检查)

3. 未映射的同主题文件
   📂 cog.md#同主题文件关系映射
   ├─ 主题: naming-convention
   ├─ 已映射: 2026-02-03_spec_naming-convention.md
   └─ 未映射: ❌ meta.md#编码规约, real.md#文件名冲突禁区
   💡 建议: 在 cog.md 中补充这两个文件的映射记录

╠════════════════════════════════════════════════════════════════╣

【同主题文件组统计】

| 主题 | 文件数 | 状态 |
|------|--------|------|
| naming-convention | 3 | ⚠️  未全部映射 |
| video-script | 2 | ✓ 已映射 |
| arbitrage-analysis | 4 | ⚠️  未全部映射 |

╠════════════════════════════════════════════════════════════════╣

【建议行动】

Priority 1 (立即执行):
  □ 删除 .42cog/spec/dev/ 中的重复文件

Priority 2 (本周执行):
  □ 更新 cog.md 中的映射表（3 个主题待处理）

Priority 3 (下周执行):
  □ 审计更新日期序号是否连续

═════════════════════════════════════════════════════════════════
✓ 检查完成。详细报告已保存至: reports/naming-audit-2026-02-03.json
```

### JSON 输出（存储为报告文件）

```json
{
  "report_id": "audit-20260203-183045",
  "timestamp": "2026-02-03T18:30:45Z",
  "scanned_files": 248,
  "violations": [
    {
      "type": "DUPLICATE_IN_DIR",
      "severity": "CRITICAL",
      "directory": ".42cog/spec/dev",
      "files": [
        ".42cog/spec/dev/sys.spec.md",
        ".42cog/spec/dev/sys.spec.md (2)"
      ],
      "action": "manual_review_and_delete"
    },
    {
      "type": "UNMAPPED_FILE",
      "severity": "WARNING",
      "topic": "naming-convention",
      "file": "meta.md#编码规约",
      "action": "add_to_mapping_table"
    }
  ],
  "statistics": {
    "total_violations": 3,
    "by_severity": {
      "CRITICAL": 1,
      "WARNING": 2,
      "INFO": 0
    },
    "same_topic_groups": 3,
    "files_by_type": {
      "md": 156,
      "yaml": 45,
      "json": 47
    }
  },
  "recommendations": [
    {
      "priority": 1,
      "action": "Fix duplicate files in .42cog/spec/dev/",
      "steps": [...]
    }
  ]
}
```

## 使用示例

### 示例 1：基础检查

```
用户: "检查我的文件名"

Claude:
我来为你的项目执行命名规约审计...

✓ 扫描完成 (248 文件)
⚠️  发现 3 处违反

最严重的问题:
  1. [CRITICAL] .42cog/spec/dev/ 中有重复文件
  2. [WARNING] cog.md 中有 3 个文件未在映射表中标注

详细报告已保存: reports/naming-audit-2026-02-03.json
```

### 示例 2：针对特定目录

```
用户: "检查 .42cog/spec/ 目录的文件名"

Claude:
正在检查 .42cog/spec/ ...

总计: 45 个文件，发现 0 处违反 ✓

子目录统计:
  ├─ pm/ (15 文件) ✓
  └─ dev/ (12 文件) ⚠️  有 1 处重复

全部符合编码规约！
```

## 集成到工作流中

在以下场景自动触发此 skill：

1. **新项目初始化**
   ```
   后创建时运行: check-naming-violations --report
   ```

2. **定期审计**（每周）
   ```
   cron: "0 9 * * 1" → /check-naming-violations --strict
   ```

3. **文件冲突检测**
   ```
   创建新文件时：先运行 /check-naming-violations --quiet
   确认无冲突后，才创建文件
   ```

4. **提交前检查**（与 git hook 集成）
   ```bash
   pre-commit hook:
   if ! /check-naming-violations --exit-code; then
       echo "❌ 命名规约检查失败，请修复后再提交"
       exit 1
   fi
   ```

---

**最后更新**：2026-02-03
**维护者**：Claude Code
**下一版本计划**：v2.0（支持更多文件类型和自动修复）
