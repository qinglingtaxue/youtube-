#!/bin/bash
# 启动带远程调试端口的 Chrome

echo "关闭现有 Chrome..."
pkill -f "Google Chrome" 2>/dev/null
sleep 2

echo "启动 Chrome (端口 9222, Profile 3)..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="/Users/su/Library/Application Support/Google/Chrome" \
  --profile-directory="Profile 3" \
  "https://studio.youtube.com" &

echo ""
echo "Chrome 已启动！"
echo "请在浏览器中确认已登录 YouTube Studio"
echo "然后运行: node upload-cdp.js"
