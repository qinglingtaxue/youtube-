#!/bin/bash
# 部署报告到 Vercel

set -e

echo "=== 部署 YouTube 分析报告到 Vercel ==="

# 进入项目目录
cd "$(dirname "$0")/.."

# 激活虚拟环境
source .venv/bin/activate

# 生成最新报告
echo "1. 生成最新报告..."
python -c "
import sys
sys.path.insert(0, '.')
from src.analysis.comprehensive_report import generate_comprehensive_report
path = generate_comprehensive_report()
print(f'报告已生成: {path}')
"

# 复制最新报告到 public 目录
echo "2. 复制到 public 目录..."
latest_report=$(ls -t data/analysis/comprehensive_report_*.html | head -1)
cp "$latest_report" public/index.html
echo "已复制: $latest_report -> public/index.html"

# 部署到 Vercel
echo "3. 部署到 Vercel..."
vercel --prod --yes

echo ""
echo "=== 部署完成 ==="
echo "访问: https://youtube-analysis-report.vercel.app"
