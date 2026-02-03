# /deploy - 部署报告到 Vercel

将最新报告部署到 Vercel。

## 使用方法

```
/deploy [报告类型]
```

## 参数

- `报告类型`：research / comprehensive / all，默认 comprehensive

## 执行步骤

1. 生成最新报告
2. 复制到 public/ 目录
3. 执行 Vercel 部署
4. 返回部署 URL

## 示例

```
/deploy comprehensive
/deploy all
/deploy
```

---

请执行以下命令进行部署：

```bash
cd /Users/su/Downloads/3d_games/5-content-creation-tools/youtube-minimal-video-story/2026-1-17

# 生成最新报告
source .venv/bin/activate
python -c "
import sys
sys.path.insert(0, '.')
from src.analysis.comprehensive_report import generate_comprehensive_report
path = generate_comprehensive_report()
print(f'报告已生成: {path}')
"

# 复制到 public 目录
latest_report=$(ls -t data/analysis/comprehensive_report_*.html 2>/dev/null | head -1)
if [ -n "$latest_report" ]; then
    cp "$latest_report" public/index.html
    echo "已复制: $latest_report -> public/index.html"
fi

# 部署到 Vercel
vercel --prod --yes
```

部署完成后访问: https://youtube-analysis-report.vercel.app
