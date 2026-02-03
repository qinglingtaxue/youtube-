# YouTube 视频上传 - 手动完成指南

## 概述

您已经准备好了所有必要的组件：
- ✅ 视频文件: `/Users/su/Downloads/9月15日.mp4` (167.37 MB)
- ✅ MCP Chrome 扩展已加载到 Chrome
- ✅ 上传脚本已准备就绪

## 需要完成的步骤

### 步骤 1: 激活 MCP 扩展 (关键步骤)

1. **打开 Chrome 并导航到扩展管理页面**
   ```
   在地址栏输入: chrome://extensions/
   ```

2. **启用开发者模式**
   - 在页面右上角找到"开发者模式"开关
   - 点击开关启用开发者模式

3. **找到 Chrome MCP Server 扩展**
   - 在扩展列表中找到 "Chrome MCP Server"
   - 确认该扩展已启用（开关为蓝色/绿色）

4. **点击 Details 按钮**
   - 在 "Chrome MCP Server" 扩展右侧点击 "Details" 按钮

5. **打开 Service Worker**
   - 在详情页面中找到 "Service Worker (background)" 部分
   - 点击 "service worker" 链接

6. **点击 Connect 按钮**
   - 在打开的 DevTools 窗口中
   - 找到并点击 "Connect" 按钮

7. **确认连接成功**
   - DevTools 应该显示连接成功的消息
   - 关闭窗口

### 步骤 2: 确认 YouTube 登录

1. **打开 YouTube Studio**
   ```
   https://studio.youtube.com
   ```

2. **确认登录状态**
   - 确认您已登录 Google 账户
   - 确认可以访问 YouTube Studio
   - 确认可以看到"创建"按钮

### 步骤 3: 运行上传脚本

完成步骤 1 和 2 后，运行以下命令：

```bash
cd /Users/su/Downloads/3d_games/youtube_automation
python3 final_upload.py
```

## 故障排除

### 问题: 找不到 Chrome MCP Server 扩展

**解决方案:**
```bash
# 重新加载扩展
bash /Users/su/Downloads/3d_games/mcp/load_mcp_chrome.sh
```

### 问题: 端口 12306 没有被监听

**解决方案:**
1. 检查扩展是否已正确加载
2. 确认已点击 "Connect" 按钮
3. 重新启动 Chrome

### 问题: YouTube Studio 无法访问

**解决方案:**
1. 清除浏览器缓存
2. 重新登录 Google 账户
3. 检查网络连接（可能需要代理）

## 验证步骤

在运行上传脚本前，验证以下内容：

```bash
# 检查端口 12306 是否被监听
lsof -i :12306

# 应该显示类似输出：
# COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF    NODE NAME
# node    12345 user   14u  IPv4 0x12345678      0t0    TCP localhost:12306 (LISTEN)
```

## 上传流程说明

当您运行 `final_upload.py` 时，脚本将：

1. ✅ 检查视频文件存在
2. ✅ 检查 MCP 服务器连接
3. ✅ 导航到 YouTube Studio
4. ✅ 点击上传按钮
5. ✅ 选择视频文件
6. ✅ 填写视频信息（标题、描述、可见性）
7. ✅ 发布视频

## 预期结果

- 视频将出现在您的 YouTube Studio 中
- 视频状态显示为"正在处理"
- 处理通常需要 5-15 分钟
- 处理完成后会收到邮件通知

## 联系信息

如果遇到问题，请检查：
1. Chrome 扩展是否正确加载
2. MCP 服务器是否在端口 12306 运行
3. YouTube 账户是否已登录
4. 网络连接是否稳定

---

**注意:** 这是真实的 YouTube 上传，视频将出现在您的频道中。
