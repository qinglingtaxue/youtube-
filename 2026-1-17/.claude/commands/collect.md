# /collect - 快速采集视频数据

执行视频数据采集任务。

## 使用方法

```
/collect [主题] [数量]
```

## 参数

- `主题`：采集的关键词主题，默认 "老人养生"
- `数量`：目标采集数量，默认 500

## 执行步骤

1. 运行数据采集脚本
2. 显示采集进度
3. 输出采集结果摘要

## 示例

```
/collect 老人养生 1000
/collect 健康饮食
/collect
```

---

请执行以下命令进行数据采集：

```bash
cd /Users/su/Downloads/3d_games/5-content-creation-tools/youtube-minimal-video-story/2026-1-17
source .venv/bin/activate
python scripts/daily_collect.py --theme "$1" --count ${2:-500}
```

采集完成后，显示数据库统计信息。
