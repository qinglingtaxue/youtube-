# post-collect - 采集完成后自动触发

当数据采集完成后自动执行的操作。

## 触发条件

- `daily_collect.py` 执行完成
- `data_collector.collect_large_scale()` 执行完成
- 数据库有新增视频

## 自动执行

1. 更新数据库统计信息
2. 生成调研报告快照
3. 检查是否有新的爆款视频
4. 发送通知（如果配置）

## 配置

在 `config/hooks.yaml` 中配置：

```yaml
post_collect:
  enabled: true
  auto_report: true
  notify: false
  report_type: research
```

## 执行脚本

```python
# hooks/post_collect.py
import sys
sys.path.insert(0, '.')

from src.research.data_collector import DataCollector
from src.research.research_report import generate_research_report

def on_collect_complete():
    # 获取统计
    collector = DataCollector()
    stats = collector.get_statistics()

    print(f"采集完成统计:")
    print(f"  总视频数: {stats['total']}")
    print(f"  有详情的: {stats['with_details']}")

    # 自动生成报告（可选）
    # path = generate_research_report()
    # print(f"报告已生成: {path}")

if __name__ == '__main__':
    on_collect_complete()
```
