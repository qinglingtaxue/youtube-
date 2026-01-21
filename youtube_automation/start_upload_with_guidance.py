#!/usr/bin/env python3
"""
引导用户完成 MCP 扩展激活并开始真实视频上传
"""

import asyncio
import os
import subprocess
import webbrowser
import time

async def main():
    print("=" * 70)
    print("🚀 YouTube 视频上传 - MCP 自动化系统")
    print("=" * 70)

    # 检查视频文件
    video_file = "/Users/su/Downloads/9月15日.mp4"
    print(f"\n📹 视频文件: {video_file}")

    if not os.path.exists(video_file):
        print(f"❌ 视频文件不存在: {video_file}")
        return

    file_size = os.path.getsize(video_file) / (1024*1024)
    print(f"✅ 文件大小: {file_size:.2f} MB")

    # 步骤 1: 打开扩展管理页面
    print("\n" + "=" * 70)
    print("步骤 1/5: 激活 MCP Chrome 扩展")
    print("=" * 70)

    print("\n正在打开扩展管理页面...")
    webbrowser.open("chrome://extensions/")

    print("""
📋 请按顺序完成以下操作:

1️⃣  在 Chrome 扩展页面中启用"开发者模式" (右上角开关)
2️⃣  找到 "Chrome MCP Server" 扩展
3️⃣  点击该扩展的 "Details" 按钮
4️⃣  在详情页面中找到 "Service Worker (background)" 部分
5️⃣  点击 "service worker" 链接
6️⃣  在打开的 DevTools 窗口中点击 "Connect" 按钮
7️⃣  确认连接成功后关闭窗口

⚠️  重要: 必须完成所有步骤，否则上传无法进行

完成所有步骤后，按回车键继续...
""")
    input()

    # 验证 MCP 服务器
    print("\n" + "=" * 70)
    print("步骤 2/5: 验证 MCP 服务器")
    print("=" * 70)

    print("正在检查 MCP 服务器状态...")
    result = subprocess.run(["lsof", "-i", ":12306"], capture_output=True)
    if result.returncode == 0:
        print("✅ MCP 服务器已在端口 12306 上运行")
    else:
        print("❌ MCP 服务器未运行")
        print("请检查扩展是否正确连接")
        return

    # 步骤 3: 打开 YouTube Studio
    print("\n" + "=" * 70)
    print("步骤 3/5: 打开 YouTube Studio")
    print("=" * 70)

    print("\n正在打开 YouTube Studio...")
    webbrowser.open("https://studio.youtube.com")

    print("""
📋 请确认登录状态:

1️⃣  确认您已登录 Google 账户
2️⃣  确认可以访问 YouTube Studio
3️⃣  确认可以看到"创建"按钮

登录完成后，按回车键继续...
""")
    input()

    # 步骤 4: 开始上传
    print("\n" + "=" * 70)
    print("步骤 4/5: 准备上传")
    print("=" * 70)

    print(f"""
📹 上传信息:
   文件: {video_file}
   大小: {file_size:.2f} MB
   标题: 9月15日 - 游戏视频
   描述: 这是一个9月15日的游戏演示视频
   可见性: 公开

⚠️  即将开始真实上传到您的 YouTube 账户
   视频将出现在您的 YouTube Studio 中
   YouTube 需要几分钟处理时间

确认开始上传？输入 'YES' 确认: """, end="")
    confirm = input().strip()

    if confirm != "YES":
        print("\n❌ 已取消上传")
        return

    # 步骤 5: 执行上传
    print("\n" + "=" * 70)
    print("步骤 5/5: 执行上传")
    print("=" * 70)

    print("\n🚀 正在启动上传流程...")
    print("⏳ 这可能需要几分钟时间，请耐心等待...")

    # 运行上传脚本
    os.chdir("/Users/su/Downloads/3d_games/youtube_automation")
    result = subprocess.run(["python3", "final_upload.py"])

    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ 上传完成!")
        print("=" * 70)
        print("""
📋 后续步骤:
1. 检查 YouTube Studio: https://studio.youtube.com
2. 视频处理可能需要 5-15 分钟
3. 处理完成后会收到邮件通知
4. 视频链接将在处理完成后可用

🔗 快速链接:
   YouTube Studio: https://studio.youtube.com
   我的频道: https://www.youtube.com/@
        """)
    else:
        print("\n" + "=" * 70)
        print("❌ 上传失败")
        print("=" * 70)
        print("请检查错误信息并重试")

if __name__ == "__main__":
    asyncio.run(main())
