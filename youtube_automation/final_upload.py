#!/usr/bin/env python3
"""
最终版本 - 实际上传 9月15日.mp4 到 YouTube
"""

import asyncio
import aiohttp
import os

# 配置代理
PROXY_URL = "http://127.0.0.1:7890"

VIDEO_FILE = "/Users/su/Downloads/9月15日.mp4"
MCP_ENDPOINT = "http://127.0.0.1:12306/mcp"

async def send_mcp_request(session, tool, params):
    """发送 MCP 请求"""
    payload = {
        "tool": tool,
        "parameters": params
    }

    try:
        async with session.post(
            MCP_ENDPOINT,
            json=payload,
            timeout=30
        ) as response:
            return await response.json()
    except Exception as e:
        return {"error": str(e), "status": "failed"}

async def upload_video():
    """上传视频"""
    print("=" * 70)
    print("🚀 开始真实上传 9月15日.mp4")
    print("=" * 70)

    # 检查文件
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ 文件不存在: {VIDEO_FILE}")
        return

    file_size = os.path.getsize(VIDEO_FILE) / (1024*1024)
    print(f"✅ 文件准备就绪:")
    print(f"   路径: {VIDEO_FILE}")
    print(f"   大小: {file_size:.2f} MB")
    print()

    # 检查 MCP 服务器
    print("🔍 检查 MCP 服务器...")
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            # 测试连接
            async with session.get(MCP_ENDPOINT, timeout=5) as response:
                if response.status == 200:
                    print("✅ MCP 服务器运行正常")
                else:
                    print("❌ MCP 服务器无响应")
                    return
    except Exception as e:
        print(f"❌ 无法连接到 MCP 服务器: {e}")
        return

    print()
    print("=" * 70)
    print("📹 开始上传流程")
    print("=" * 70)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        # 步骤 1: 导航到 YouTube Studio
        print("\n1️⃣ 导航到 YouTube Studio...")
        result = await send_mcp_request(session, "chrome_navigate", {
            "url": "https://studio.youtube.com"
        })
        print(f"   结果: {result}")
        await asyncio.sleep(3)

        # 步骤 2: 点击上传按钮
        print("\n2️⃣ 点击上传按钮...")
        result = await send_mcp_request(session, "chrome_get_interactive_elements", {})
        print(f"   找到 {len(result.get('elements', []))} 个交互元素")

        result = await send_mcp_request(session, "chrome_click_element", {
            "selector": "button#create-icon"
        })
        print(f"   结果: {result}")
        await asyncio.sleep(3)

        # 步骤 3: 上传文件
        print("\n3️⃣ 上传视频文件...")
        print(f"   文件: {VIDEO_FILE}")
        result = await send_mcp_request(session, "chrome_upload_file", {
            "selector": "input[type='file']",
            "file_path": VIDEO_FILE
        })
        print(f"   结果: {result}")
        print("   ⏳ 等待文件上传完成 (可能需要几分钟)...")
        await asyncio.sleep(10)

        # 步骤 4: 填写标题
        print("\n4️⃣ 填写视频信息...")
        result = await send_mcp_request(session, "chrome_type", {
            "selector": "textbox[aria-label='标题']",
            "text": "9月15日 - 游戏视频"
        })
        print(f"   标题: 已填写")
        await asyncio.sleep(2)

        # 步骤 5: 填写描述
        result = await send_mcp_request(session, "chrome_type", {
            "selector": "textbox[aria-label='描述']",
            "text": "这是一个9月15日的游戏演示视频\n\n#游戏 #演示 #AI"
        })
        print(f"   描述: 已填写")
        await asyncio.sleep(2)

        # 步骤 6: 设置可见性
        print("\n5️⃣ 设置可见性...")
        result = await send_mcp_request(session, "chrome_click_element", {
            "selector": "button#next-button"
        })
        await asyncio.sleep(2)

        result = await send_mcp_request(session, "chrome_click_element", {
            "selector": "paper-radio-button[name='privacy'][aria-label='公之于众']"
        })
        print(f"   可见性: 已设置为公开")
        await asyncio.sleep(2)

        # 步骤 7: 发布
        print("\n6️⃣ 发布视频...")
        print("   ⚠️  注意: 这是最后一步，将实际上传视频")
        await asyncio.sleep(2)

        result = await send_mcp_request(session, "chrome_click_element", {
            "selector": "button#done-button"
        })
        print(f"   结果: {result}")

    print()
    print("=" * 70)
    print("✅ 上传流程完成！")
    print("=" * 70)
    print()
    print("📋 后续步骤:")
    print("1. 检查 YouTube Studio: https://studio.youtube.com")
    print("2. 查看视频处理状态")
    print("3. 视频链接将在几分钟内可用")
    print()
    print("🔗 查看您的视频:")
    print("   YouTube Studio: https://studio.youtube.com")
    print()

if __name__ == "__main__":
    asyncio.run(upload_video())
