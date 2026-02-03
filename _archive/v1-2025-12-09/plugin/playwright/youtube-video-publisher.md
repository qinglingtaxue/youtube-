# YouTube 视频自动发布 Skill

## 概述

这个 skill 用于自动化 YouTube 视频发布流程。通过 Playwright MCP 控制浏览器，完成从上传到发布的全部步骤。

## 前置条件

1. 已安装 Playwright MCP
2. 浏览器已登录 YouTube 账号
3. 准备好要上传的视频文件

## 完整工作流程

```
打开 YouTube → 点击创建 → 上传视频 → 填写详情 → ⭐设置获利(必须On) → 广告适合性 → 视频元素 → 检查 → ⭐设置定时发布 → 确认发布
```

## ⚠️ 关键步骤提醒（必须执行）

### 1. 获利设置 - 必须选择 "On"
在 Monetisation 步骤，**必须**点击 Select → 选择 "On" → 点击 Done，否则视频无法获得广告收益。

### 2. 定时发布 - 必须设置发布时间
在 Visibility 步骤，**必须**展开 "Schedule" 选项，设置具体的发布日期和时间，而不是直接选择 Public 立即发布。

---

## 第一步：导航到 YouTube

```
工具: mcp__playwright__browser_navigate
参数: url = "https://www.youtube.com"
```

---

## 第二步：点击创建按钮

```
工具: mcp__playwright__browser_click
参数:
  element = "Create button"
  ref = "button[aria-label='Create']" 或 页面快照中的 "Create" 按钮
```

然后点击 "Upload video":

```
工具: mcp__playwright__browser_click
参数:
  element = "Upload video link"
  ref = 页面快照中的 "Upload video" 链接
```

---

## 第三步：上传视频文件

### 3.1 点击选择文件按钮

```
工具: mcp__playwright__browser_click
参数:
  element = "Select files button"
  ref = 页面快照中的 "Select files" 按钮
```

### 3.2 上传文件

```
工具: mcp__playwright__browser_file_upload
参数:
  paths = ["/path/to/your/video.mp4"]
```

---

## 第四步：详情页面 (Details)

### 4.1 填写标题（必填）

```
工具: mcp__playwright__browser_type
参数:
  element = "Title textbox"
  ref = 页面快照中的标题输入框
  text = "你的视频标题"
```

### 4.2 填写描述（可选）

```
工具: mcp__playwright__browser_click
参数:
  element = "Description textbox"
  ref = 页面快照中的描述输入框
```

然后输入描述内容。

### 4.3 缩略图选项

| 选项 | 说明 |
|-----|------|
| Upload file | 上传自定义缩略图 |
| Auto-generated | 使用自动生成的缩略图 |
| A/B Testing | A/B 测试不同缩略图 |

### 4.4 播放列表（可选）

点击 "Select" 下拉菜单选择播放列表。

### 4.5 受众设置（必填）

| 选项 | ref | 说明 |
|-----|-----|------|
| Yes, it's Made for Kids | radio "Yes, it's Made for Kids" | 适合儿童的内容 |
| No, it's not 'Made for Kids' | radio "No, it's not 'Made for Kids'" | 非儿童内容 |

```
工具: mcp__playwright__browser_click
参数:
  element = "No, it's not Made for Kids radio"
  ref = 页面快照中的对应单选框
```

### 4.6 点击下一步

```
工具: mcp__playwright__browser_click
参数:
  element = "Next button"
  ref = 页面快照中的 "Next" 按钮
```

---

## 第五步：获利设置 (Monetisation) ⭐必须执行

> **重要**：此步骤必须选择 "On" 开启获利，否则视频无法获得广告收益！

### 5.1 打开获利设置

```
工具: mcp__playwright__browser_click
参数:
  element = "Monetisation select button"
  ref = 页面快照中的 "Select" 按钮（获利部分）
```

### 5.2 选择获利状态（必须选 On）

| 选项 | 说明 | 是否推荐 |
|-----|------|---------|
| On | 开启广告获利 | ✅ 推荐 |
| Off | 关闭广告获利 | ❌ 不推荐 |

```
工具: mcp__playwright__browser_click
参数:
  element = "On radio button"
  ref = 页面快照中的 "On" 单选框
```

### 5.3 完成设置

```
工具: mcp__playwright__browser_click
参数:
  element = "Done button"
  ref = 页面快照中的 "Done" 按钮
```

### 5.4 点击下一步

```
工具: mcp__playwright__browser_click
参数:
  element = "Next button"
  ref = 页面快照中的 "Next" 按钮
```

---

## 第六步：广告适合性 (Ad suitability)

### 6.1 选择内容类别

如果视频不包含敏感内容，选择 "None of the above":

```
工具: mcp__playwright__browser_click
参数:
  element = "None of the above checkbox"
  ref = 页面快照中的 "None of the above" 复选框
```

### 敏感内容类别（按需勾选）

| 类别 | 说明 |
|-----|------|
| Graphic violence or shocking content | 暴力或令人震惊的内容 |
| Harmful or dangerous acts | 有害或危险行为 |
| Sensitive social topics | 敏感社会话题 |
| Content featuring firearms | 含枪支内容 |
| Drug-related content | 毒品相关内容 |
| Sexual or suggestive content | 性暗示内容 |
| Inappropriate or offensive language | 不当或冒犯性语言 |

### 6.2 提交评级

```
工具: mcp__playwright__browser_click
参数:
  element = "Submit rating button"
  ref = 页面快照中的 "Submit rating" 按钮
```

### 6.3 点击下一步

```
工具: mcp__playwright__browser_click
参数:
  element = "Next button"
  ref = 页面快照中的 "Next" 按钮
```

---

## 第七步：视频元素 (Video elements)

此步骤为可选项：

| 元素 | 说明 |
|-----|------|
| Add subtitles | 添加字幕 |
| Add an end screen | 添加片尾画面 |
| Add cards | 添加卡片 |

### 点击下一步

```
工具: mcp__playwright__browser_click
参数:
  element = "Next button"
  ref = 页面快照中的 "Next" 按钮
```

---

## 第八步：检查 (Checks)

此页面显示版权和广告适合性检查结果。等待检查完成后：

```
工具: mcp__playwright__browser_click
参数:
  element = "Next button"
  ref = 页面快照中的 "Next" 按钮
```

---

## 第九步：可见性设置 (Visibility) ⭐必须设置定时发布

> **重要**：不要直接选择 Public 立即发布，必须使用 Schedule 设置定时发布时间！

### 可见性选项

| 选项 | 说明 | 适用场景 |
|-----|------|---------|
| Private | 私享 | 仅自己可见，测试用 |
| Unlisted | 不公开 | 有链接才能观看 |
| Members only | 仅限会员 | 频道会员专属 |
| Public | 公开 | 所有人可见（不推荐直接使用） |
| **Schedule** | **定时发布** | **✅ 推荐使用** |

### 9.1 展开定时发布选项

```
工具: mcp__playwright__browser_click
参数:
  element = "Schedule section"
  ref = 页面快照中的 "Schedule" 可展开区域
```

### 9.2 选择发布日期

```
工具: mcp__playwright__browser_click
参数:
  element = "Date picker button"
  ref = 页面快照中的日期按钮（如 "7 Jan 2026"）
```

然后在日历中选择具体日期：

```
工具: mcp__playwright__browser_click
参数:
  element = "日期"
  ref = 页面快照中对应日期的元素
```

### 9.3 选择发布时间

```
工具: mcp__playwright__browser_click
参数:
  element = "Time textbox"
  ref = 页面快照中的时间输入框
```

然后在时间列表中选择（推荐 18:00 黄金时段）：

```
工具: mcp__playwright__browser_click
参数:
  element = "18:00 option"
  ref = 页面快照中的 "18:00" 选项
```

### 9.4 首映设置（可选）

如需设置首映，勾选 "Set as Premiere"：

```
工具: mcp__playwright__browser_click
参数:
  element = "Set as Premiere checkbox"
  ref = 页面快照中的 "Set as Premiere" 复选框
```

---

## 第十步：确认发布

### 定时发布（推荐）

设置好日期和时间后，点击 Schedule 按钮：

```
工具: mcp__playwright__browser_click
参数:
  element = "Schedule button"
  ref = 页面快照中的 "Schedule" 按钮
```

如果出现检查提示对话框，点击 "Got it" 确认：

```
工具: mcp__playwright__browser_click
参数:
  element = "Got it button"
  ref = 页面快照中的 "Got it" 按钮
```

### 私享保存

```
工具: mcp__playwright__browser_click
参数:
  element = "Save button"
  ref = 页面快照中的 "Save" 按钮
```

### 立即公开发布（不推荐）

```
工具: mcp__playwright__browser_click
参数:
  element = "Publish button"
  ref = 页面快照中的 "Publish" 按钮
```

---

## 常用配置模板

### 模板1：定时发布（⭐推荐默认使用）

```yaml
visibility: Schedule
schedule_date: "明天或之后的日期"
schedule_time: "18:00"  # 推荐黄金时段
monetisation: On        # 必须开启
audience: "No, it's not Made for Kids"
ad_suitability: "None of the above"
```

### 模板2：快速私享上传（仅测试用）

```yaml
visibility: Private
monetisation: On        # 即使私享也建议开启
audience: "No, it's not Made for Kids"
ad_suitability: "None of the above"
```

### 模板3：立即公开发布（不推荐）

```yaml
visibility: Public
monetisation: On
audience: "No, it's not Made for Kids"
ad_suitability: "None of the above"
```

### 模板4：不公开分享

```yaml
visibility: Unlisted
monetisation: On
audience: "No, it's not Made for Kids"
ad_suitability: "None of the above"
```

---

## 批量发布多个视频

### 批量发布规则

1. **发布时间范围**：每天 08:00 - 24:00（早上8点到晚上12点）
2. **视频间隔**：每个视频间隔 15 分钟
3. **每天最多发布**：64 个视频（16小时 × 4个/小时）

### 批量发布时间计算

假设从明天开始发布，第一个视频 08:00：

| 视频序号 | 发布时间 |
|---------|---------|
| 视频 1 | 08:00 |
| 视频 2 | 08:15 |
| 视频 3 | 08:30 |
| 视频 4 | 08:45 |
| 视频 5 | 09:00 |
| ... | ... |
| 视频 64 | 23:45 |
| 视频 65 | 次日 08:00 |

### 批量发布工作流程

```
循环执行以下步骤，直到所有视频发布完成：

1. 上传视频
2. 填写详情
3. 开启获利 (On)
4. 广告适合性评级
5. 跳过视频元素
6. 跳过检查
7. 设置定时发布时间（根据当前视频序号计算）
8. 点击 Schedule 确认
9. 关闭成功对话框
10. 返回第1步，上传下一个视频
```

### 时间计算逻辑

```python
def calculate_publish_time(video_index, start_date, start_hour=8, end_hour=24, interval_minutes=15):
    """
    计算第 N 个视频的发布时间

    参数:
        video_index: 视频序号（从 1 开始）
        start_date: 开始日期（如 "2026-01-08"）
        start_hour: 每天开始时间（默认 8 点）
        end_hour: 每天结束时间（默认 24 点）
        interval_minutes: 视频间隔（默认 15 分钟）

    返回:
        (日期, 时间) 如 ("2026-01-08", "18:00")
    """
    # 每天可发布的视频数量
    daily_slots = (end_hour - start_hour) * 60 // interval_minutes  # 64 个

    # 计算是第几天（从 0 开始）
    day_offset = (video_index - 1) // daily_slots

    # 计算当天的第几个时间槽（从 0 开始）
    slot_in_day = (video_index - 1) % daily_slots

    # 计算具体时间
    total_minutes = start_hour * 60 + slot_in_day * interval_minutes
    hour = total_minutes // 60
    minute = total_minutes % 60

    # 计算日期
    from datetime import datetime, timedelta
    base_date = datetime.strptime(start_date, "%Y-%m-%d")
    publish_date = base_date + timedelta(days=day_offset)

    return (publish_date.strftime("%Y-%m-%d"), f"{hour:02d}:{minute:02d}")

# 示例：
# 视频 1 -> ("2026-01-08", "08:00")
# 视频 5 -> ("2026-01-08", "09:00")
# 视频 64 -> ("2026-01-08", "23:45")
# 视频 65 -> ("2026-01-09", "08:00")
```

### 批量发布示例

假设要发布 10 个视频，从 2026-01-08 开始：

| 视频 | 文件 | 发布日期 | 发布时间 |
|-----|------|---------|---------|
| 1 | video1.mp4 | 2026-01-08 | 08:00 |
| 2 | video2.mp4 | 2026-01-08 | 08:15 |
| 3 | video3.mp4 | 2026-01-08 | 08:30 |
| 4 | video4.mp4 | 2026-01-08 | 08:45 |
| 5 | video5.mp4 | 2026-01-08 | 09:00 |
| 6 | video6.mp4 | 2026-01-08 | 09:15 |
| 7 | video7.mp4 | 2026-01-08 | 09:30 |
| 8 | video8.mp4 | 2026-01-08 | 09:45 |
| 9 | video9.mp4 | 2026-01-08 | 10:00 |
| 10 | video10.mp4 | 2026-01-08 | 10:15 |

### 批量发布执行步骤

**准备工作：**
1. 确定要上传的视频文件列表
2. 确定开始发布的日期
3. 计算每个视频的发布时间

**执行流程：**

对于每个视频，执行完整的上传流程：

```
第 N 个视频：

1. 导航到 YouTube Studio
   mcp__playwright__browser_navigate -> https://studio.youtube.com

2. 点击 Upload videos 按钮

3. 选择文件并上传
   mcp__playwright__browser_file_upload -> [视频文件路径]

4. 等待上传完成（约 1-2 分钟）

5. 填写详情 -> Next

6. 获利设置：Select -> On -> Done -> Next

7. 广告适合性：None of the above -> Submit rating -> Next

8. 视频元素 -> Next

9. 检查 -> Next

10. 可见性：
    - 展开 Schedule
    - 选择日期（根据视频序号计算）
    - 选择时间（根据视频序号计算）
    - 点击 Schedule 按钮

11. 确认成功 -> Close

12. 继续上传下一个视频
```

---

## 注意事项

1. **⭐ 获利必须开启**：在 Monetisation 步骤必须选择 "On"，否则无法获得广告收益
2. **⭐ 必须定时发布**：在 Visibility 步骤必须使用 Schedule 设置发布时间，不要直接选 Public
3. **登录状态**：确保浏览器已登录 YouTube 账号
4. **视频处理**：上传后需等待视频处理完成才能发布
5. **版权检查**：如有版权问题，视频可能无法公开发布
6. **页面快照**：每次操作前先获取页面快照以获取准确的元素 ref
7. **等待加载**：页面切换后需等待元素加载完成
8. **推荐发布时间**：18:00 是黄金时段，建议设置在这个时间发布

## 调试技巧

1. 使用 `mcp__playwright__browser_snapshot` 获取当前页面状态
2. 使用 `mcp__playwright__browser_take_screenshot` 保存截图
3. 如果元素找不到，可能需要等待页面加载或滚动页面
