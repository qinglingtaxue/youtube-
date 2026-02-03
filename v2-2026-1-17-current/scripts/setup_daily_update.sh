#!/bin/bash
# 设置每日定时更新脚本
# 用法: ./scripts/setup_daily_update.sh

echo "=== YouTube 数据每日更新设置 ==="

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$PROJECT_DIR/scripts/com.youtube.daily-update.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.youtube.daily-update.plist"

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

echo "项目目录: $PROJECT_DIR"

# 检查是否已存在
if [ -f "$PLIST_DST" ]; then
    echo "已存在定时任务配置，是否更新？(y/n)"
    read -r answer
    if [ "$answer" != "y" ]; then
        echo "取消操作"
        exit 0
    fi
    # 卸载旧任务
    launchctl unload "$PLIST_DST" 2>/dev/null
fi

# 复制配置文件
cp "$PLIST_SRC" "$PLIST_DST"
echo "配置文件已复制到: $PLIST_DST"

# 加载任务
launchctl load "$PLIST_DST"
echo "定时任务已加载"

# 显示状态
echo ""
echo "=== 设置完成 ==="
echo "定时任务将在每天凌晨 3:00 自动运行"
echo ""
echo "常用命令："
echo "  查看状态:  launchctl list | grep youtube"
echo "  手动运行:  python $PROJECT_DIR/scripts/daily_update.py"
echo "  卸载任务:  launchctl unload $PLIST_DST"
echo "  查看日志:  cat $PROJECT_DIR/logs/daily_update_$(date +%Y-%m-%d).json"
echo ""
