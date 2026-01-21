#!/usr/bin/env python3
"""
激活 MCP Chrome 扩展
通过自动化方式点击 Connect 按钮
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def activate_mcp_extension():
    """激活 MCP 扩展"""
    print("=" * 70)
    print("🔧 激活 MCP Chrome 扩展")
    print("=" * 70)

    async with async_playwright() as p:
        try:
            # 连接到现有的 Chrome 实例
            print("\n1️⃣ 连接到 Chrome...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 已连接到 Chrome")

            # 获取默认上下文和页面
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()

            # 导航到扩展管理页面
            print("\n2️⃣ 打开扩展管理页面...")
            await page.goto("chrome://extensions/")
            await page.wait_for_load_state("networkidle")
            print("✅ 已打开扩展管理页面")

            # 等待页面加载
            await asyncio.sleep(2)

            # 启用开发者模式（如果未启用）
            print("\n3️⃣ 检查开发者模式...")
            developer_toggle = await page.query_selector('input[id="devMode"]')
            if developer_toggle:
                is_checked = await developer_toggle.is_checked()
                if not is_checked:
                    print("   启用开发者模式...")
                    await developer_toggle.click()
                    await asyncio.sleep(1)
                    print("✅ 开发者模式已启用")
                else:
                    print("✅ 开发者模式已启用")

            # 查找 MCP Chrome Server 扩展
            print("\n4️⃣ 查找 MCP Chrome Server 扩展...")
            extensions = await page.query_selector_all('extensions-item')

            mcp_extension_found = False
            for ext in extensions:
                name = await ext.get_attribute("name")
                if name and "MCP" in name:
                    print(f"✅ 找到扩展: {name}")

                    # 点击扩展的 "Details" 按钮
                    print("\n5️⃣ 点击 Details 按钮...")
                    details_button = await ext.query_selector('a[id$="-details"]')
                    if details_button:
                        await details_button.click()
                        await asyncio.sleep(1)

                        # 在详情页面查找 "Service Worker (background)" 部分
                        print("\n6️⃣ 查找服务工作者...")
                        # 查找 "service worker" 相关的文本
                        service_worker_text = await page.query_selector('text="service worker"')
                        if service_worker_text:
                            print("✅ 找到服务工作者")

                            # 点击 "service worker" 链接
                            service_worker_link = await page.query_selector('a:has-text("service worker")')
                            if service_worker_link:
                                print("\n7️⃣ 点击服务工作者链接...")
                                await service_worker_link.click()
                                await asyncio.sleep(2)
                                print("✅ 已点击服务工作者链接")

                                # 在新的 DevTools 页面中查找 "Connect" 按钮
                                print("\n8️⃣ 查找 Connect 按钮...")
                                new_page = context.pages[-1] if context.pages else None
                                if new_page:
                                    await new_page.wait_for_load_state("networkidle")
                                    print("   已打开 DevTools")

                                    # 查找 Connect 按钮
                                    connect_button = await new_page.query_selector('text="Connect"')
                                    if connect_button:
                                        print("✅ 找到 Connect 按钮")
                                        print("\n9️⃣ 点击 Connect 按钮...")
                                        await connect_button.click()
                                        await asyncio.sleep(2)
                                        print("✅ Connect 按钮已点击")

                                        mcp_extension_found = True
                                        break
                                    else:
                                        print("⚠️  未找到 Connect 按钮")
                                        print("   请手动点击页面中的 Connect 按钮")
                        else:
                            print("⚠️  未找到服务工作者部分")

            if not mcp_extension_found:
                print("\n❌ 无法自动激活扩展")
                print("\n📋 手动激活步骤:")
                print("1. 在 Chrome 中打开: chrome://extensions/")
                print("2. 找到 'Chrome MCP Server' 扩展")
                print("3. 点击 'Details' 按钮")
                print("4. 在详情页面中找到 'Service Worker (background)' 部分")
                print("5. 点击 'service worker' 链接")
                print("6. 在打开的 DevTools 中点击 'Connect' 按钮")
                print("\n完成手动步骤后，按回车继续上传...")
                input()
            else:
                print("\n✅ MCP 扩展已成功激活")
                print("⏳ 等待服务启动...")
                await asyncio.sleep(3)

                # 检查端口 12306 是否被监听
                import subprocess
                result = subprocess.run(["lsof", "-i", ":12306"], capture_output=True)
                if result.returncode == 0:
                    print("✅ MCP 服务器已在端口 12306 上运行")
                else:
                    print("⚠️  端口 12306 仍未被监听")
                    print("   请检查扩展是否正确连接")

            await browser.close()

        except Exception as e:
            print(f"\n❌ 激活扩展时出错: {str(e)}")
            print("\n📋 请手动激活扩展:")
            print("1. 打开: chrome://extensions/")
            print("2. 启用开发者模式")
            print("3. 找到 'Chrome MCP Server' 扩展")
            print("4. 点击 'Details' → 'service worker' → 'Connect'")
            print("\n完成手动步骤后，按回车继续上传...")
            input()

if __name__ == "__main__":
    asyncio.run(activate_mcp_extension())
