#!/usr/bin/env python3
"""
Cog 同步脚本 - 保持 cog.md 与代码实现同步

触发时机：
1. 每天开工时（终端启动）
2. git commit 涉及 models/ 或 .spec.md 时
3. AI 执行重大任务前

使用方式：
    python scripts/sync_cog_from_code.py --mode=check    # 只检查，报告差异
    python scripts/sync_cog_from_code.py --mode=suggest  # 检查并生成建议
    python scripts/sync_cog_from_code.py --mode=full     # 完整同步，更新 cog.md
    python scripts/sync_cog_from_code.py --quiet         # 静默模式，只在有差异时输出
"""

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class EntityInfo:
    """实体信息"""
    name: str
    source: str  # 'code' or 'cog'
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    attributes: list = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = []


@dataclass
class SyncReport:
    """同步报告"""
    code_entities: dict  # name -> EntityInfo
    cog_entities: dict   # name -> EntityInfo
    new_in_code: list    # 代码有，cog 没有
    missing_in_code: list  # cog 有，代码没有
    timestamp: str


class CogSyncer:
    """Cog 同步器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cog_path = project_root / ".42cog" / "cog" / "cog.md"
        self.models_paths = [
            project_root / "src" / "shared" / "models",
            project_root / "src" / "research",
            project_root / "src" / "analytics",
        ]
        self.spec_path = project_root / ".42cog" / "spec"

    def scan_code_entities(self) -> dict:
        """扫描代码中的实体定义"""
        entities = {}

        # 扫描 Python 类定义
        for models_dir in self.models_paths:
            if not models_dir.exists():
                continue
            for py_file in models_dir.rglob("*.py"):
                self._scan_python_file(py_file, entities)

        # 扫描 spec 文件中定义的实体
        if self.spec_path.exists():
            for spec_file in self.spec_path.rglob("*.spec.md"):
                self._scan_spec_file(spec_file, entities)

        return entities

    def _scan_python_file(self, file_path: Path, entities: dict):
        """扫描单个 Python 文件"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 跳过私有类和测试类
                    if node.name.startswith('_') or node.name.startswith('Test'):
                        continue
                    # 跳过 Mixin 和 Base 类
                    if 'Mixin' in node.name or node.name == 'Base':
                        continue

                    # 提取属性
                    attributes = []
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            attributes.append(item.target.id)

                    entities[node.name] = EntityInfo(
                        name=node.name,
                        source='code',
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno,
                        attributes=attributes
                    )
        except Exception as e:
            print(f"⚠️ 解析 {file_path} 失败: {e}", file=sys.stderr)

    def _scan_spec_file(self, file_path: Path, entities: dict):
        """扫描 spec 文件中的实体定义"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # 查找 <EntityName> 形式的定义
            pattern = r'<(\w+)>\s*\n-\s*唯一编码'
            matches = re.finditer(pattern, content)

            for match in matches:
                entity_name = match.group(1)
                if entity_name not in entities:
                    entities[entity_name] = EntityInfo(
                        name=entity_name,
                        source='code',  # spec 也算代码侧
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=content[:match.start()].count('\n') + 1
                    )
        except Exception as e:
            print(f"⚠️ 解析 {file_path} 失败: {e}", file=sys.stderr)

    def parse_cog_entities(self) -> dict:
        """解析 cog.md 中记录的实体"""
        entities = {}

        if not self.cog_path.exists():
            print(f"⚠️ cog.md 不存在: {self.cog_path}", file=sys.stderr)
            return entities

        content = self.cog_path.read_text(encoding='utf-8')

        # 方式1: 查找 <EntityName> 形式的定义块
        pattern = r'<(\w+)>\s*\n-\s*唯一编码'
        matches = re.finditer(pattern, content)

        for match in matches:
            entity_name = match.group(1)
            entities[entity_name] = EntityInfo(
                name=entity_name,
                source='cog',
                file_path=str(self.cog_path.relative_to(self.project_root)),
                line_number=content[:match.start()].count('\n') + 1
            )

        # 方式2: 查找 "- EntityName：" 形式的列表项
        list_pattern = r'^-\s+(\w+)：'
        for i, line in enumerate(content.split('\n'), 1):
            match = re.match(list_pattern, line)
            if match:
                entity_name = match.group(1)
                if entity_name not in entities:
                    entities[entity_name] = EntityInfo(
                        name=entity_name,
                        source='cog',
                        file_path=str(self.cog_path.relative_to(self.project_root)),
                        line_number=i
                    )

        return entities

    def generate_report(self) -> SyncReport:
        """生成同步报告"""
        code_entities = self.scan_code_entities()
        cog_entities = self.parse_cog_entities()

        code_names = set(code_entities.keys())
        cog_names = set(cog_entities.keys())

        new_in_code = sorted(code_names - cog_names)
        missing_in_code = sorted(cog_names - code_names)

        return SyncReport(
            code_entities=code_entities,
            cog_entities=cog_entities,
            new_in_code=new_in_code,
            missing_in_code=missing_in_code,
            timestamp=datetime.now().isoformat()
        )

    def print_report(self, report: SyncReport, quiet: bool = False):
        """打印同步报告"""
        has_diff = report.new_in_code or report.missing_in_code

        if quiet and not has_diff:
            return

        print("=" * 60)
        print("🔍 Cog 同步检查报告")
        print(f"📅 时间: {report.timestamp}")
        print("=" * 60)
        print()

        print(f"📋 代码中发现：{len(report.code_entities)} 个实体")
        print(f"📋 cog.md 记录：{len(report.cog_entities)} 个实体")
        print()

        if report.new_in_code:
            print("🆕 新增实体（代码有，cog 没有）：")
            for name in report.new_in_code:
                info = report.code_entities[name]
                loc = f"{info.file_path}:{info.line_number}" if info.file_path else "未知位置"
                print(f"   - {name} ({loc})")
            print()

        if report.missing_in_code:
            print("⚠️ 可能过时（cog 有，代码未找到实现）：")
            for name in report.missing_in_code:
                info = report.cog_entities[name]
                print(f"   - {name} (cog.md:{info.line_number})")
            print()

        if not has_diff:
            print("✅ cog.md 与代码同步，无差异")
        else:
            print("-" * 60)
            print(f"📊 差异统计：+{len(report.new_in_code)} 新增，-{len(report.missing_in_code)} 可能过时")

    def generate_suggestion(self, report: SyncReport) -> str:
        """生成更新建议"""
        if not report.new_in_code:
            return ""

        lines = [
            "",
            "## 建议添加到 cog.md 的实体",
            "",
        ]

        for name in report.new_in_code:
            info = report.code_entities[name]
            lines.append(f"<{name}>")
            lines.append(f"- 唯一编码：{name.lower()}_id (待定义)")
            lines.append(f"- 来源：{info.file_path}:{info.line_number}")
            if info.attributes:
                lines.append("- 核心属性：")
                for attr in info.attributes[:5]:  # 最多显示5个
                    lines.append(f"  - {attr}")
            lines.append(f"</{name}>")
            lines.append("")

        return "\n".join(lines)

    def update_cog(self, report: SyncReport):
        """更新 cog.md（追加新实体）"""
        if not report.new_in_code:
            print("✅ 无需更新")
            return

        suggestion = self.generate_suggestion(report)

        # 备份原文件
        backup_path = self.cog_path.with_suffix('.md.bak')
        content = self.cog_path.read_text(encoding='utf-8')
        backup_path.write_text(content, encoding='utf-8')
        print(f"📦 已备份: {backup_path}")

        # 追加到文件末尾
        with open(self.cog_path, 'a', encoding='utf-8') as f:
            f.write("\n\n---\n")
            f.write(f"\n## 自动同步添加 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
            f.write(suggestion)

        print(f"✅ 已更新 cog.md，添加了 {len(report.new_in_code)} 个实体")


def main():
    parser = argparse.ArgumentParser(description='Cog 同步脚本')
    parser.add_argument('--mode', choices=['check', 'suggest', 'full'],
                        default='check', help='运行模式')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='静默模式，只在有差异时输出')
    parser.add_argument('--project', type=Path, default=None,
                        help='项目根目录')

    args = parser.parse_args()

    # 确定项目根目录
    if args.project:
        project_root = args.project
    else:
        # 从脚本位置向上找
        project_root = Path(__file__).parent.parent

    syncer = CogSyncer(project_root)
    report = syncer.generate_report()

    if args.mode == 'check':
        syncer.print_report(report, quiet=args.quiet)
        # 有差异返回非0
        sys.exit(1 if (report.new_in_code or report.missing_in_code) else 0)

    elif args.mode == 'suggest':
        syncer.print_report(report, quiet=args.quiet)
        if report.new_in_code:
            print("\n" + "=" * 60)
            print("📝 更新建议")
            print("=" * 60)
            print(syncer.generate_suggestion(report))

    elif args.mode == 'full':
        syncer.print_report(report, quiet=args.quiet)
        if report.new_in_code:
            confirm = input("\n确认更新 cog.md？(y/n) ")
            if confirm.lower() == 'y':
                syncer.update_cog(report)
            else:
                print("❌ 已取消")


if __name__ == '__main__':
    main()
