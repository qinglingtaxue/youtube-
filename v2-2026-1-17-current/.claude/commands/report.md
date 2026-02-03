# /report - 一键生成报告

生成调研洞察报告或综合分析报告。

## 使用方法

```
/report [类型] [时间范围]
```

## 参数

- `类型`：research（调研报告）或 comprehensive（综合报告），默认 research
- `时间范围`：1天内 / 15天内 / 30天内 / 全部，默认 全部

## 执行步骤

1. 从数据库加载视频数据
2. 执行数据分析
3. 生成 HTML 报告
4. 在浏览器中打开

## 示例

```
/report research 30天内
/report comprehensive
/report
```

---

请执行以下命令生成报告：

**调研报告**：
```bash
cd /Users/su/Downloads/3d_games/5-content-creation-tools/youtube-minimal-video-story/2026-1-17
source .venv/bin/activate
python src/research/research_report.py --time-window "${2:-全部}" --open
```

**综合报告**：
```bash
cd /Users/su/Downloads/3d_games/5-content-creation-tools/youtube-minimal-video-story/2026-1-17
source .venv/bin/activate
python -c "
import sys
sys.path.insert(0, '.')
from src.analysis.comprehensive_report import generate_comprehensive_report
import webbrowser
from pathlib import Path

path = generate_comprehensive_report()
print(f'报告已生成: {path}')
webbrowser.open(f'file://{Path(path).absolute()}')
"
```

报告生成后会自动在浏览器中打开。
