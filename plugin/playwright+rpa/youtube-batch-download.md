# YouTube Studio 批量下载视频

## 概述

从 YouTube Studio 播放列表批量下载视频的综合自动化流程。结合意图理解、结构化参数生成、RPA 工具和 Playwright 浏览器自动化。

## 适用场景

- 从 YouTube Studio 播放列表下载指定范围的视频（如 121-130 集）
- 需要批量下载多个视频文件
- 视频数量多需要通过翻页定位

## 完整流程

### 阶段 1: 意图理解

解析用户请求，提取关键参数：
- **目标集数范围**: 如 121-130
- **播放列表 URL**: `https://studio.youtube.com/playlist/{PLAYLIST_ID}/videos`
- **下载目录**: 默认 `.playwright-mcp/`

**示例输入**:
```
下载第 121-130 集的视频
播放列表: https://studio.youtube.com/playlist/PLjDLbyA7SjEnYZW2IyqKuASGHepoA175i/videos
```

### 阶段 2: 生成结构化参数

```json
{
  "action": "download",
  "playlist_id": "PLjDLbyA7SjEnYZW2IyqKuASGHepoA175i",
  "episode_range": {
    "start": 121,
    "end": 130
  },
  "method": "playwright",
  "download_dir": ".playwright-mcp/"
}
```

### 阶段 3: 定位目标视频

#### 3.1 翻页导航

YouTube Studio 播放列表每页 30 条，按发布时间倒序：
- 第 1 页: 最新 30 条 (如 171-200)
- 第 2 页: 次新 30 条 (如 141-170)
- 第 3 页: 继续往前 (如 111-140) ← 目标 121-130 在这里

```javascript
// Playwright 翻页
await page.goto('https://studio.youtube.com/playlist/PLjDLbyA7SjEnYZW2IyqKuASGHepoA175i/videos');
// 点击下一页按钮，重复直到到达目标页
await page.getByRole('button', { name: '下一页' }).click();
```

#### 3.2 提取视频 ID

从播放列表页面提取每个视频的 ID：
```
130: aTAdQ1Wvh5k
129: BnxSLfaw7ao
128: przjlJk3HHQ
127: AZO-PLk5GpQ
126: OKp4n97h3MQ
125: S31mHtUljxU
124: XxnBYstfvAg
123: oagHjuobfqo
122: 1ENdvVBXDBQ
121: Q8lZ74edHFE
```

### 阶段 4: 执行下载

#### 方式 A: 用户浏览器 + RPA（推荐，优先使用）

**核心思路：利用用户已登录的浏览器，完全跳过登录问题**

优点：
- 零登录时间，直接使用用户现有 session
- 操作简单直观
- 有 Playwright 作为备用方案

流程：
1. **用户准备**：打开 Chrome/Safari，确保已登录 YouTube Studio
2. **打开第一页**：用户打开播放列表页面（第一页即可）
3. **Playwright 翻页**：Claude 用 Playwright 自动翻页到目标集数所在页
4. **RPA 下载**：Claude 用 pyautogui 控制屏幕执行下载操作
5. **失败回退**：如果 RPA 失败（坐标偏移等），自动回退到纯 Playwright

```python
# RPA 下载流程
import pyautogui
import time

def rpa_download_video():
    try:
        # 1. 点击视频行的选项按钮（三个点）
        pyautogui.click(options_button_x, options_button_y)
        time.sleep(0.5)

        # 2. 点击下载菜单项
        pyautogui.click(download_menu_x, download_menu_y)
        time.sleep(1)

        return True
    except Exception as e:
        print(f"RPA 失败: {e}")
        return False

# 失败则回退到 Playwright
if not rpa_download_video():
    print("RPA 失败，切换到 Playwright...")
    # 调用 Playwright 方式
```

使用前提：
- 浏览器窗口在前台可见
- 不要移动浏览器窗口位置
- 用户已登录 YouTube Studio

#### 方式 B: Playwright 直接下载（备用方案）

适用场景：RPA 失败时的回退方案，或需要后台运行时

优点：
- 可后台运行，不需要窗口在前台
- 基于 DOM 元素定位，不依赖屏幕坐标
- 更稳定可靠

缺点：
- 需要在 Playwright 的独立 profile 中登录一次

```javascript
// 对每个视频 ID 执行：
for (const videoId of videoIds) {
  // 1. 导航到详情页
  await page.goto(`https://studio.youtube.com/video/${videoId}/edit`);

  // 2. 点击选项按钮
  await page.getByRole('button', { name: '选项' }).click();

  // 3. 点击下载
  await page.getByRole('menuitem', { name: '下载' }).click();

  // 可以立即继续下一个，下载会在后台进行
}
```

#### 方式 C: 纯 RPA 工具

适用场景：简单重复任务

```bash
# RPA 工具
cd /Users/su/Downloads/3d_games/youtube-uploader
python3 youtube-tool.py
```

RPA 限制：
- 需要浏览器窗口在前台可见
- 基于屏幕坐标，移动窗口会失效
- 不能后台运行

### 阶段 5: 验收检查

```bash
# 检查下载文件
ls -lh /Users/su/Downloads/3d_games/.playwright-mcp/ | grep -E "12[0-9]|130"

# 验证文件数量
ls /Users/su/Downloads/3d_games/.playwright-mcp/*.mp4 | wc -l
```

## 工具对比

| 特性 | 用户浏览器+RPA（优先） | Playwright（备用） | 纯 RPA |
|------|------------------------|-------------------|--------|
| 登录处理 | ✅ 零登录，用现有 session | ⚠️ 需登录一次 | ⚠️ 需确保已登录 |
| 后台运行 | ❌ 需要前台 | ✅ 支持 | ❌ 需要前台 |
| 定位方式 | 屏幕坐标 | DOM 元素 | 屏幕坐标 |
| 稳定性 | 中 | 高 | 中 |
| 失败回退 | ✅ 可回退 Playwright | - | ❌ 无 |
| 推荐优先级 | 🥇 第一选择 | 🥈 第二选择 | 🥉 第三选择 |

## 常见问题

### 浏览器被占用

```bash
pkill -f "mcp-chrome-4b6d14a"
rm -f /Users/su/Library/Caches/ms-playwright/mcp-chrome-4b6d14a/SingletonLock
rm -f /Users/su/Library/Caches/ms-playwright/mcp-chrome-4b6d14a/SingletonSocket
rm -f /Users/su/Library/Caches/ms-playwright/mcp-chrome-4b6d14a/SingletonCookie
```

### 下载卡住

重新触发下载：导航到视频详情页 → 选项 → 下载

### Playwright 断开连接

**原因**：批量下载过多视频可能导致浏览器崩溃或 MCP 连接超时

**预防措施**：
1. **分批下载**：每次最多 5 个视频，避免一次性 10 个以上
2. **增加等待时间**：每个下载之间等待 3-5 秒
3. **检查下载完成**：确认前一批下载完成后再开始下一批

**补救方法**：
```bash
# 1. 清理浏览器锁文件
pkill -f "mcp-chrome"
rm -f /Users/su/Library/Caches/ms-playwright/mcp-chrome-4b6d14a/Singleton*

# 2. 重新调用 Playwright navigate（通常会自动重连）

# 3. 如果仍失败，手动在浏览器中完成剩余下载
```

**分批下载示例代码**：
```javascript
// 每批 5 个，批次之间等待 10 秒
const batchSize = 5;
for (let i = 0; i < videos.length; i += batchSize) {
  const batch = videos.slice(i, i + batchSize);
  for (const video of batch) {
    await downloadVideo(video);
    await page.waitForTimeout(3000); // 每个视频间隔 3 秒
  }
  if (i + batchSize < videos.length) {
    await page.waitForTimeout(10000); // 批次间隔 10 秒
  }
}
```

## 示例会话

```
用户: 下载 121-130 集视频
      播放列表: https://studio.youtube.com/playlist/PLjDLbyA7SjEnYZW2IyqKuASGHepoA175i/videos

Claude:
1. 解析意图: 下载 121-130 集，需要翻到第 3 页
2. 请打开浏览器，登录 YouTube Studio，打开播放列表第一页

用户: 已打开

Claude 执行:
3. [Playwright] 翻页到第 3 页 (111-140 集所在页)
4. [Playwright] 提取 10 个视频的 ID
5. [RPA] 逐个点击下载按钮
6. 如果 RPA 失败 → 回退到 Playwright 下载
7. 验证下载完成
```

## 下载记录

| 日期 | 集数范围 | 数量 | 方式 | 状态 |
|------|----------|------|------|------|
| 2026-01-08 | 107-110 | 4 | Playwright | ✅ |
| 2026-01-09 | 121-130 | 10 | Playwright | ✅ |
