# pre-deploy - 部署前检查

在执行 Vercel 部署前自动运行的检查。

## 触发条件

- 执行 `/deploy` 命令
- 执行 `scripts/deploy.sh`
- 手动运行 `vercel` 命令

## 检查项目

1. 确保 public/ 目录存在
2. 确保有最新的报告文件
3. 验证 HTML 文件完整性
4. 检查文件大小是否合理

## 配置

在 `config/hooks.yaml` 中配置：

```yaml
pre_deploy:
  enabled: true
  check_report_age: 24h  # 报告超过24小时则重新生成
  max_file_size: 10MB
  required_files:
    - public/index.html
```

## 执行脚本

```python
# hooks/pre_deploy.py
import os
from pathlib import Path
from datetime import datetime, timedelta

def pre_deploy_check():
    public_dir = Path("public")
    index_file = public_dir / "index.html"

    # 检查目录
    if not public_dir.exists():
        print("错误: public/ 目录不存在")
        return False

    # 检查文件
    if not index_file.exists():
        print("错误: public/index.html 不存在")
        return False

    # 检查文件时间
    mtime = datetime.fromtimestamp(index_file.stat().st_mtime)
    age = datetime.now() - mtime
    if age > timedelta(hours=24):
        print(f"警告: 报告已过期 ({age.days} 天前)")
        print("建议重新生成报告")

    # 检查文件大小
    size_mb = index_file.stat().st_size / 1024 / 1024
    if size_mb > 10:
        print(f"警告: 文件过大 ({size_mb:.1f} MB)")

    print("部署前检查通过")
    return True

if __name__ == '__main__':
    pre_deploy_check()
```
