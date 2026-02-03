# YouTube Studio 视频下载技能

## 概述

通过 YouTube Studio 后台批量下载自己频道上传的视频。适用于备份、迁移或本地编辑场景。

## 前置条件

- 已登录 YouTube Studio 账号
- 浏览器已启用 Playwright MCP
- 视频已上传到自己的频道

## 操作流程

### 手动下载单个视频

1. **进入播放列表页面**
   ```
   https://studio.youtube.com/playlist/{PLAYLIST_ID}/videos
   ```

2. **找到目标视频行**
   - 滚动到目标视频所在位置

3. **悬停显示操作按钮**
   - 将鼠标移到视频行上
   - 等待 Options (⋮) 按钮出现

4. **点击 Options 按钮**
   - 弹出下拉菜单

5. **点击 Download**
   - 视频开始下载
   - 自动保存到 `.playwright-mcp` 目录

### 自动化批量下载 (Playwright)

```javascript
async (page) => {
  const results = [];
  const targetKeywords = ['第33集', '第34集', '第35集'];
  
  for (const keyword of targetKeywords) {
    try {
      // 1. 定位视频行
      const row = page.getByRole('row', { 
        name: new RegExp(`.*${keyword}.*`) 
      });
      
      // 2. 滚动到可见区域
      await row.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);
      
      // 3. 悬停显示按钮
      await row.hover();
      await page.waitForTimeout(800);
      
      // 4. 点击 Options 按钮
      const optionsButton = row.getByLabel('Options');
      await optionsButton.click({ force: true, timeout: 10000 });
      await page.waitForTimeout(800);
      
      // 5. 点击 Download
      const downloadButton = page.getByRole('menuitem', { name: 'Download' });
      await downloadButton.click();
      await page.waitForTimeout(3000);
      
      results.push(`${keyword}: 下载已启动`);
    } catch (err) {
      results.push(`${keyword}: 错误 - ${err.message.substring(0, 100)}`);
    }
  }
  return results.join('\n');
}
```

## 关键技术点

### 1. 悬停触发 UI
YouTube Studio 的 Options 按钮只在鼠标悬停时显示：
```javascript
await row.hover();
await page.waitForTimeout(800); // 等待按钮渲染
```

### 2. 强制点击
有时按钮被其他元素遮挡，需要强制点击：
```javascript
await optionsButton.click({ force: true, timeout: 10000 });
```

### 3. 滚动到视图
视频列表可能很长，需要先滚动：
```javascript
await row.scrollIntoViewIfNeeded();
```

### 4. 适当延时
每个操作之间需要等待 UI 响应：
- 滚动后: 300ms
- 悬停后: 800ms  
- 点击菜单后: 800ms
- 下载启动后: 3000ms

## 下载文件说明

### 保存位置
```
/Users/su/Downloads/3d_games/.playwright-mcp/
```

### 文件命名规则
YouTube Studio 下载会使用视频的完整标题作为文件名：
```
{视频标题}-{所有hashtag}.mp4
```

示例：
```
毛泽东选集-第33集-反对投降活动-纪念中国人民抗日战争暨世界反法西斯战争胜利80周年-...mp4
```

## 常见问题

### Q: Options 按钮点击超时？
A: 增加悬停等待时间，或使用 `{ force: true }` 强制点击

### Q: 视频行定位失败？
A: 检查正则表达式是否匹配视频标题，可能需要调整匹配模式

### Q: 下载没有开始？
A: 检查 Download 菜单项是否存在，某些视频可能不支持下载

## 实战案例

### 批量下载播放列表视频

**场景**: 下载"毛泽东选集"第33-43集

**步骤**:
1. 导航到播放列表: `https://studio.youtube.com/playlist/PLjDLbyA7SjEkQP6HvRznReRYSJJyQQrQk/videos`
2. 使用批量下载脚本
3. 等待所有下载完成
4. 验证文件数量和大小

**结果**: 11个视频全部下载成功

## 相关资源

- YouTube Studio: https://studio.youtube.com
- Playwright MCP 文档
- 视频文件管理最佳实践
