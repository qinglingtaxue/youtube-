#!/bin/bash
# YouTube MCP 自动化发布完整流程脚本

echo "========================================="
echo "🚀 MCP Chrome YouTube 自动化发布系统"
echo "========================================="
echo ""

# 步骤 1：启动 MCP Chrome 服务器
echo "📋 步骤 1/4: 启动 MCP Chrome 服务器..."
bash /Users/su/Downloads/3d_games/mcp/load_mcp_chrome.sh

# 等待服务器启动
echo ""
echo "⏳ 等待 MCP 服务器启动 (10秒)..."
sleep 10

# 步骤 2：检查服务器状态
echo ""
echo "📋 步骤 2/4: 检查服务器状态..."
if curl -s http://127.0.0.1:12306/health > /dev/null 2>&1; then
    echo "✅ MCP Chrome 服务器运行正常"
else
    echo "❌ MCP Chrome 服务器未响应，请检查扩展是否正确加载"
    echo ""
    echo "🔧 故障排除步骤："
    echo "1. 打开 Chrome: chrome://extensions/"
    echo "2. 启用 '开发者模式'"
    echo "3. 确保 'Chrome MCP Server' 扩展已加载"
    echo "4. 点击扩展图标并连接"
    exit 1
fi

# 步骤 3：运行 Python 自动化脚本
echo ""
echo "📋 步骤 3/4: 执行 YouTube 自动上传..."
cd /Users/su/Downloads/3d_games/youtube_automation

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -q aiohttp selenium beautifulsoup4 > /dev/null 2>&1

# 运行上传脚本
echo "▶️  开始自动化上传..."
python3 mcp_youtube_upload.py

# 步骤 4：生成报告
echo ""
echo "📋 步骤 4/4: 生成上传报告..."
REPORT_FILE="upload_report_$(date +%Y%m%d_%H%M%S).json"
echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"status\": \"completed\"}" > "$REPORT_FILE"
echo "📄 报告已保存到: $REPORT_FILE"

echo ""
echo "========================================="
echo "✅ 自动化流程完成！"
echo "========================================="
echo ""
echo "📌 查看更多选项："
echo "   - 单个视频上传: python3 upload_single.py"
echo "   - 批量视频上传: python3 batch_upload.py"
echo "   - 视频管理: python3 video_manager.py"
echo ""
echo "🔗 有用的链接："
echo "   - YouTube Studio: https://studio.youtube.com"
echo "   - MCP 状态: http://127.0.0.1:12306/health"
