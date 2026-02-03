#!/usr/bin/env python3
"""
使用真实视频文件进行 YouTube 上传测试
"""

import asyncio
import os
from youtube_mcp_workflow import YouTubeMCPWorkflow

async def upload_real_video():
    """上传真实视频文件"""
    print("=" * 70)
    print("🎬 使用真实视频文件上传测试")
    print("=" * 70)

    # 使用用户提供的真实视频文件
    video_file = "/Users/su/Downloads/3d_games/w1_gobang_project/11月30日.mp4"

    # 检查文件是否存在
    if not os.path.exists(video_file):
        print(f"\n❌ 错误: 视频文件不存在!")
        print(f"   文件路径: {video_file}")
        print(f"\n请确认文件存在后重试")
        return

    # 获取文件信息
    file_size = os.path.getsize(video_file) / (1024*1024)  # MB
    print(f"\n✅ 找到视频文件:")
    print(f"   路径: {video_file}")
    print(f"   大小: {file_size:.2f} MB")

    # 视频配置
    video_config = {
        "file": video_file,
        "title": "11月30日 - 五子棋游戏视频",
        "description": "这是一个五子棋游戏的演示视频\n\n#五子棋 #游戏 #AI",
        "privacy": "public",
        "tags": ["五子棋", "游戏", "AI", "演示"]
    }

    print(f"\n📋 上传配置:")
    print(f"   标题: {video_config['title']}")
    print(f"   描述: {video_config['description']}")
    print(f"   可见性: {video_config['privacy']}")

    # 检查 MCP 服务器状态
    print("\n🔍 检查 MCP Chrome 服务器...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:12306/health", timeout=5) as response:
                if response.status == 200:
                    print("✅ MCP 服务器运行正常")
                else:
                    print("⚠️  MCP 服务器无响应")
                    print("   请运行: bash /Users/su/Downloads/3d_games/mcp/load_mcp_chrome.sh")
                    return
    except:
        print("⚠️  无法连接到 MCP 服务器")
        print("   请运行: bash /Users/su/Downloads/3d_games/mcp/load_mcp_chrome.sh")
        return

    # 检查 YouTube 登录状态
    print("\n🔐 检查 YouTube 登录状态...")
    print("   正在导航到 YouTube Studio...")

    async with YouTubeMCPWorkflow() as workflow:
        # 导航到 YouTube Studio
        result = await workflow.send_mcp_request("chrome_navigate", {
            "url": "https://studio.youtube.com"
        })
        await asyncio.sleep(5)

        # 检查是否需要登录
        content = await workflow.send_mcp_request("chrome_get_web_content", {})

        if "登录" in str(content) or "Sign in" in str(content) or "登录您的 Google 账户" in str(content):
            print("\n⚠️  检测到需要登录 YouTube")
            print("=" * 60)
            print("📝 手动登录步骤:")
            print("1. 请在浏览器中打开: https://studio.youtube.com")
            print("2. 完成 Google 账户登录")
            print("3. 确保可以访问 YouTube Studio")
            print("4. 登录完成后回到这里按回车继续...")
            print("=" * 60)
            input("按回车键继续...")
        else:
            print("✅ YouTube 已登录")

        # 开始上传
        print("\n" + "=" * 70)
        print("🚀 开始真实视频上传")
        print("=" * 70)

        try:
            result = await workflow.upload_video_workflow(video_config)

            if result.get("upload_status") == "success":
                print("\n" + "=" * 70)
                print("✅ 上传成功!")
                print("=" * 70)
                print("\n📊 视频信息:")
                print(f"   标题: {video_config['title']}")
                print(f"   文件: {video_file}")
                print(f"   大小: {file_size:.2f} MB")
                print(f"\n⏳ 状态: 视频已提交到 YouTube")
                print("   YouTube 正在处理您的视频 (通常需要 5-15 分钟)")
                print(f"\n🔗 查看地址:")
                print(f"   YouTube Studio: https://studio.youtube.com")
                print(f"   我的频道: https://www.youtube.com/@")

                print("\n📋 后续步骤:")
                print("1. 在 YouTube Studio 查看视频状态")
                print("2. 处理完成后会收到邮件通知")
                print("3. 视频链接将发送到您的邮箱")

            else:
                print("\n" + "=" * 70)
                print("❌ 上传失败")
                print("=" * 70)
                print(f"错误信息: {result.get('message', '未知错误')}")
                print(f"\n🔧 故障排除:")
                print("1. 检查文件格式 (推荐 MP4)")
                print("2. 检查网络连接")
                print("3. 确认 YouTube 账户状态")
                print("4. 尝试重新上传")

        except Exception as e:
            print("\n" + "=" * 70)
            print("❌ 上传过程出错")
            print("=" * 70)
            print(f"错误: {str(e)}")
            print(f"\n请检查:")
            print("1. MCP 服务器是否运行")
            print("2. Chrome 扩展是否已连接")
            print("3. YouTube 账户是否已登录")


if __name__ == "__main__":
    print("""
🎬 真实视频上传测试

使用文件: /Users/su/Downloads/3d_games/w1_gobang_project/11月30日.mp4

⚠️  注意事项:
- 这将尝试真实上传到您的 YouTube 账户
- 上传的视频会出现在您的 YouTube Studio 中
- YouTube 需要几分钟到几十分钟来处理视频

准备就绪后按回车开始...
""")
    input()
    asyncio.run(upload_real_video())
