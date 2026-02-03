#!/bin/bash
# Cog 每日同步检查脚本
# 添加到 ~/.zshrc 或 ~/.bashrc 中

# 配置
COG_PROJECT_ROOT="/Users/su/Downloads/3d_games/5-content-creation-tools/youtube-minimal-video-story/2026-1-17"
COG_SYNC_MARKER="$HOME/.cog_last_sync"

cog_daily_check() {
    local today=$(date +%Y-%m-%d)

    # 检查今天是否已经运行过
    if [ -f "$COG_SYNC_MARKER" ]; then
        local last_check=$(cat "$COG_SYNC_MARKER")
        if [ "$last_check" = "$today" ]; then
            return 0  # 今天已检查，跳过
        fi
    fi

    # 检查项目目录是否存在
    if [ ! -d "$COG_PROJECT_ROOT" ]; then
        return 0
    fi

    # 运行同步检查
    echo ""
    echo "🔄 每日 Cog 同步检查..."
    python3 "$COG_PROJECT_ROOT/scripts/sync_cog_from_code.py" --mode=check --quiet

    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        echo ""
        echo "💡 运行以下命令查看详情："
        echo "   python3 $COG_PROJECT_ROOT/scripts/sync_cog_from_code.py --mode=suggest"
        echo ""
    fi

    # 记录今天已检查
    echo "$today" > "$COG_SYNC_MARKER"
}

# 在终端启动时自动运行
cog_daily_check
