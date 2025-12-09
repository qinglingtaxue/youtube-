#!/bin/bash

# 打开功能演示页面

echo "🎯 打开YouTube视频研究工作流功能演示..."
echo ""

# 检查是否在正确的目录
if [ ! -f "demo.html" ]; then
    echo "❌ 错误: 请在 web/ 目录下运行此脚本"
    exit 1
fi

# 启动Web服务器
echo "🚀 启动Web服务器..."
python3 -m http.server 8080 --bind 127.0.0.1 > /dev/null 2>&1 &
SERVER_PID=$!

# 等待服务器启动
sleep 2

echo "✅ 服务器已启动 (PID: $SERVER_PID)"
echo ""
echo "📱 演示页面地址:"
echo "   http://localhost:8080/demo.html"
echo ""
echo "💡 按 Ctrl+C 停止服务器"
echo ""

# 在浏览器中打开
if command -v open > /dev/null; then
    # macOS
    open http://localhost:8080/demo.html
elif command -v xdg-open > /dev/null; then
    # Linux
    xdg-open http://localhost:8080/demo.html
else
    echo "请手动在浏览器中打开: http://localhost:8080/demo.html"
fi

# 等待用户中断
echo ""
read -p "按 Enter 键停止服务器..."

# 停止服务器
kill $SERVER_PID 2>/dev/null
echo "✅ 服务器已停止"
