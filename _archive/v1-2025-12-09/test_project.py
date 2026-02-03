#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目功能测试脚本
验证所有核心功能是否正常工作
"""

import sys
import subprocess
from pathlib import Path

def test_python_version():
    """测试Python版本"""
    print("🔍 测试Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro} (符合要求)")
        return True
    else:
        print(f"❌ Python版本: {version.major}.{version.minor}.{version.micro} (需要3.11+)")
        return False

def test_run_py():
    """测试run.py"""
    print("\n🔍 测试run.py...")
    try:
        result = subprocess.run(
            ['python3', 'run.py', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ run.py 正常工作")
            return True
        else:
            print(f"❌ run.py 错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ run.py 测试失败: {e}")
        return False

def test_research_py():
    """测试research.py"""
    print("\n🔍 测试research.py...")
    try:
        # 测试help命令
        result = subprocess.run(
            ['python3', 'research.py', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"❌ research.py help 错误: {result.stderr}")
            return False

        # 测试regions命令
        result = subprocess.run(
            ['python3', 'research.py', 'regions'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and 'US:' in result.stdout:
            print("✅ research.py 正常工作")
            return True
        else:
            print(f"❌ research.py regions 错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ research.py 测试失败: {e}")
        return False

def test_config_files():
    """测试配置文件"""
    print("\n🔍 测试配置文件...")
    config_files = [
        'config/config.yaml',
        'config/regions.yaml',
        'config/platforms.yaml',
        'config/keywords.yaml',
        'config/templates.yaml'
    ]

    all_exist = True
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False

    return all_exist

def test_source_files():
    """测试源代码文件"""
    print("\n🔍 测试源代码文件...")
    source_files = [
        'src/__init__.py',
        'src/research/__init__.py',
        'src/analysis/__init__.py',
        'src/template/__init__.py',
        'src/workflow/__init__.py',
        'src/monitoring/__init__.py',
        'src/utils/__init__.py',
        'run.py',
        'research.py'
    ]

    all_exist = True
    for file_path in source_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False

    return all_exist

def test_demo_page():
    """测试演示页面"""
    print("\n🔍 测试演示页面...")
    demo_files = [
        'web/index.html',
        'web/demo.html'
    ]

    all_exist = True
    for file_path in demo_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False

    return all_exist

def test_examples():
    """测试示例脚本"""
    print("\n🔍 测试示例脚本...")
    example_files = [
        'examples/quick_start.py',
        'examples/custom_analysis.py',
        'examples/batch_analysis.py',
        'examples/dynamic_tracking.py',
        'examples/mcp_integration.py',
        'examples/real_research.py',
        'examples/multi_platform_research.py'
    ]

    all_exist = True
    for file_path in example_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False

    return all_exist

def main():
    """主测试函数"""
    print("=" * 60)
    print("YouTube视频研究工作流 - 项目功能测试")
    print("=" * 60)

    tests = [
        ("Python版本", test_python_version),
        ("run.py", test_run_py),
        ("research.py", test_research_py),
        ("配置文件", test_config_files),
        ("源代码文件", test_source_files),
        ("演示页面", test_demo_page),
        ("示例脚本", test_examples)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有测试通过！项目可以正常使用！")
        print("\n📋 快速开始:")
        print("1. 运行示例: python3 run.py quick")
        print("2. 调研工具: python3 research.py real \"Python教程\" --regions SG MY TH")
        print("3. 查看演示: open web/demo.html")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查上述错误")

    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
