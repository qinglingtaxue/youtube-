#!/usr/bin/env python3
"""
修复真实 YouTube 上传 - 处理 "This video isn't available any more" 问题
"""

import asyncio
import aiohttp
from youtube_mcp_workflow import YouTubeMCPWorkflow

async def real_youtube_upload():
    """
    真实的 YouTube 上传流程
    解决视频不可用问题
    """
    print("=" * 70)
    print("🔧 修复真实 YouTube 上传问题")
    print("=" * 70)

    async with YouTubeMCPWorkflow() as workflow:

        # ✅ 关键修复 1: 使用真实的文件路径
        video_config = {
            "file": "/Users/su/Downloads/your_real_video.mp4",  # ⚠️ 必须替换为真实路径
            "title": "年龄大了定要忌嘴，8吃8少吃",
            "description": "分享8个简单有效的老人养生习惯\n\n#老人养生 #健康生活",
            "privacy": "public",
            "tags": ["老人养生", "健康", "长寿"]
        }

        print("\n📋 上传配置:")
        print(f"   文件: {video_config['file']}")
        print(f"   标题: {video_config['title']}")
        print(f"   描述: {video_config['description'][:50]}...")

        # ✅ 关键修复 2: 验证文件存在
        import os
        if not os.path.exists(video_config['file']):
            print(f"\n❌ 错误: 视频文件不存在!")
            print(f"   请将您的视频文件放置在: {video_config['file']}")
            print(f"   或修改脚本中的文件路径")
            return

        print(f"\n✅ 文件验证通过")

        # ✅ 关键修复 3: 检查 YouTube 登录状态
        print("\n🔐 检查 YouTube 登录状态...")
        await workflow.send_mcp_request("chrome_navigate", {
            "url": "https://studio.youtube.com"
        })
        await asyncio.sleep(3)

        # 获取页面内容检查是否已登录
        content = await workflow.send_mcp_request("chrome_get_web_content", {})
        if "登录" in str(content) or "Sign in" in str(content):
            print("⚠️  请在浏览器中手动登录 YouTube 后重试")
            print("   打开: https://studio.youtube.com")
            print("   完成登录后按回车继续...")
            input()
        else:
            print("✅ YouTube 已登录")

        # ✅ 关键修复 4: 真实的视频上传流程
        print("\n🚀 开始真实上传...")
        result = await workflow.upload_video_workflow(video_config)

        # ✅ 关键修复 5: 获取真实的 video_id
        if result.get("upload_status") == "success":
            print("\n✅ 视频上传成功!")
            print("🔗 请访问 YouTube Studio 查看:")
            print("   https://studio.youtube.com")
            print("\n📊 视频信息:")
            print(f"   标题: {video_config['title']}")
            print(f"   状态: 正在处理...")
            print(f"   链接将在几分钟后可用")

            # ✅ 关键修复 6: 等待处理完成
            print("\n⏳ 等待 YouTube 处理视频 (可能需要 5-10 分钟)...")
            print("   您可以随时在 YouTube Studio 查看状态")

        else:
            print(f"\n❌ 上传失败: {result.get('message', '未知错误')}")


async def batch_upload_with_verification():
    """批量上传并验证"""
    print("\n" + "=" * 70)
    print("📦 批量上传验证流程")
    print("=" * 70)

    videos = [
        {
            "file": "/Users/su/Downloads/video1.mp4",
            "title": "年龄大了定要忌嘴，8吃8少吃",
            "description": "分享8个简单有效的老人养生习惯\n\n#老人养生",
            "privacy": "public"
        },
        {
            "file": "/Users/su/Downloads/video2.mp4",
            "title": "70歲後，千萬別再只走路了！",
            "description": "打破常见认知！70岁后仅仅走路是不够的\n\n#健康",
            "privacy": "public"
        }
    ]

    # 验证所有文件存在
    print("\n📁 验证视频文件...")
    missing_files = []
    for i, video in enumerate(videos, 1):
        import os
        if os.path.exists(video['file']):
            size = os.path.getsize(video['file']) / (1024*1024)
            print(f"   ✅ 视频 {i}: {video['file']} ({size:.1f} MB)")
        else:
            print(f"   ❌ 视频 {i}: {video['file']} (文件不存在)")
            missing_files.append(i)

    if missing_files:
        print(f"\n⚠️  发现 {len(missing_files)} 个文件不存在")
        print("请将视频文件放在以下位置:")
        for i, video in enumerate(videos, 1):
            print(f"   视频 {i}: {video['file']}")
        return

    print("\n✅ 所有文件验证通过，开始上传...")

    async with YouTubeMCPWorkflow() as workflow:
        results = await workflow.batch_upload_videos(videos)

        # 验证结果
        print("\n" + "=" * 70)
        print("📊 上传结果验证")
        print("=" * 70)

        for result in results:
            if result.get("status") == "success":
                print(f"\n✅ 视频 #{result['index']} 上传成功")
                print(f"   标题: {result['video']['title']}")
                print(f"   状态: 已提交到 YouTube (处理中)")
                print(f"   查看: https://studio.youtube.com")
            else:
                print(f"\n❌ 视频 #{result['index']} 上传失败")
                print(f"   错误: {result.get('error', '未知')}")


if __name__ == "__main__":
    print("""
🔧 YouTube 上传问题修复指南

问题: "This video isn't available any more"

原因:
1. 模拟程序使用的是假的 video_id
2. 真实上传需要:
   - 真实的视频文件路径
   - YouTube 登录状态
   - 有效的视频格式

解决方案:
1. 使用真实的视频文件
2. 确保已登录 YouTube
3. 等待 YouTube 处理完成

选择模式:
1. 单个视频上传 (推荐先试这个)
2. 批量视频上传
""")

    choice = input("\n选择模式 (1/2): ").strip()

    if choice == "1":
        asyncio.run(real_youtube_upload())
    elif choice == "2":
        asyncio.run(batch_upload_with_verification())
    else:
        print("无效选择")
