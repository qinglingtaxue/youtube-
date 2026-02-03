# YouTube 自动上传技能

## 概述

通过 Playwright MCP 自动化上传视频到 YouTube Studio。

## 首次使用：登录问题解决方案

### 问题说明

Playwright MCP 使用独立的浏览器实例，**不会**复用系统中已登录的 Chrome 浏览器。首次打开 YouTube Studio 时会显示未登录状态。

### 解决方案：首次手动登录

1. **首次运行时**，导航到 YouTube Studio 后会看到 Google 登录页面
2. **手动点击账号登录**（在 Playwright 浏览器窗口中操作）
3. **完成登录后**，Playwright MCP 会保存登录状态到其缓存目录
4. **后续使用**时会自动保持登录状态，无需再次登录

### 备选方案：使用已登录的 Chrome Profile（需关闭 Chrome）

如果需要使用 Node.js 脚本而非 Playwright MCP，可以复用系统 Chrome 的登录状态。

#### 如果已知哪个 Profile 登录了 YouTube

直接使用该 Profile 名称（如 `Default`、`Profile 1`、`Profile 3` 等）。

**当前使用的 Profile**：`Profile 3`

#### 如果不确定哪个 Profile 登录了 YouTube

```bash
# macOS - 列出所有 Profile
ls -la "/Users/$USER/Library/Application Support/Google/Chrome/" | grep -E "Profile|Default"

# 查看某个 Profile 的账号邮箱
cat "/Users/$USER/Library/Application Support/Google/Chrome/Profile 3/Preferences" | grep -o '"email":"[^"]*"'
```

或者直接查看 Chrome 浏览器右上角的头像，点击可以看到 Profile 名称。

#### 重要提示

- **必须关闭 Chrome 浏览器**：Chrome 会锁定 Profile 目录，同时运行会冲突
- **Cookie 安全保护**：复制 Profile 到其他位置后，Google 登录状态可能失效
- **推荐**：直接使用 Playwright MCP 并首次手动登录，更简单可靠

### 关于自动化检测

**实际经验**：目前使用 Playwright MCP 操作 YouTube Studio 未遇到机器人检测问题。

**可能的原因**：
- YouTube Studio 是创作者后台工具，不像前台那样严格检测
- Playwright MCP 的操作间隔本身就不固定（等待页面加载、网络延迟等）
- 每次操作都有人工确认和干预的机会

#### 操作约束（必须遵守）

| 约束项 | 标准值 | 说明 |
|--------|--------|------|
| 单次上传视频数量 | ≤ 15 个 | 避免一次性上传过多视频 |
| 每个视频操作间隔 | ≥ 30 秒 | 完成一个视频设置到开始下一个的间隔 |
| 定时发布间隔 | ≥ 13 分钟 | 相邻视频的发布时间间隔 |
| 每日上传总量 | ≤ 50 个 | 单日上传视频数量上限 |

#### 验收标准

每个视频上传完成后，需确认以下状态：

- [ ] 视频状态显示为 "Scheduled"（已定时）而非 "Draft"（草稿）
- [ ] 封面图片已上传成功（显示自定义封面）
- [ ] 播放列表已正确选择
- [ ] 盈利状态显示为 "On"
- [ ] 广告适宜性显示 "Rating saved"
- [ ] 定时发布时间正确（日期、时间）
- [ ] 未出现任何错误提示或警告

**整体验收**：
- 所有视频状态为 "Scheduled"
- 未触发验证码或安全警告
- 账号状态正常（未被限制）

**目前未观察到的问题**：
- 未触发验证码
- 未被要求重新登录
- 未收到账号异常警告

### 登录状态存储位置

Playwright MCP 的浏览器数据存储在：
```
~/Library/Caches/ms-playwright/mcp-chrome-*/
```

### 常见登录问题

#### Q: 每次都要重新登录？
A: 检查 Playwright MCP 的缓存目录是否被清理。如果使用 `--isolated` 模式启动会每次创建新的 Profile。

#### Q: 登录后仍然显示未登录？
A: Google 账号可能启用了额外的安全验证，需要：
1. 在 Playwright 浏览器中完成所有安全验证步骤
2. 可能需要在手机上确认登录请求

#### Q: 出现"浏览器已被占用"错误？
A: 错误信息："Browser is already in use for ..."
解决方案：
1. 关闭其他正在运行的 Playwright MCP 会话
2. 或者在启动时使用 `--isolated` 参数（但会丢失登录状态）

---

## 重要提示

1. **建议单个视频逐一上传完成**：批量上传多个视频容易导致视频变成草稿状态，因为每个视频都需要完成所有设置步骤才能发布
2. **必须完成广告适宜性问卷**：开启盈利后必须填写 Ad suitability 问卷，否则 Schedule 按钮会被禁用
3. **时间过期处理**：如果选择的定时发布时间已过期（显示"Select a time in the future"），应将时间往后推几分钟，而非改到第二天

## 使用前必须确认的参数

**重要**：每批视频的设置可能不同，必须在上传前向用户确认以下参数：

### 运行模式差异

| 运行模式 | 参数获取方式 |
|----------|--------------|
| **终端模式** (Claude Code) | 每次上传前**必须主动询问**用户，不能假设默认值 |
| **UI 模式** (App/小程序) | 用户在界面中填写，提交后执行 |

### 终端模式询问模板

```
在开始上传前，请确认以下设置：

1. 视频文件：[已提供的路径]

2. 标题设置：
   □ 使用文件名作为标题（默认）
   □ 自定义标题 → 请提供标题列表
   □ 使用模板 → 请提供模板格式

3. 封面设置：
   □ 情况1: 不需要封面（使用 YouTube 自动生成）
   □ 情况2: 系列视频用同一个封面 → 请提供封面路径
   □ 情况3: 每个视频用不同封面 → 请提供封面文件夹

4. A/B 测试（可选）：
   □ 不启用
   □ 启用 → 每个视频最多 3 个备选标题 + 3 张备选封面

5. 播放列表：添加到哪个播放列表？

6. 盈利：是否开启？

7. 可见性/发布方式：
   □ Public（公开）
   □ Unlisted（不公开）
   □ Private（私有）
   □ Scheduled（定时发布）→ 开始时间？间隔？
```

---

在执行上传前，需要向用户确认以下信息：

### 1. 视频文件来源
```
请提供视频文件路径：
- 单个文件: /path/to/video.mp4
- 文件夹: /path/to/videos/
- 多个文件: 列出所有文件路径
```

### 2. 封面图片来源

封面上传分为三种情况：

| 情况 | 适用场景 | 操作 |
|------|----------|------|
| 1. 不需要封面 | 使用 YouTube 自动生成 | 跳过封面设置 |
| 2. 系列视频同封面 | 同一系列的多个视频 | 所有视频使用同一张封面 |
| 3. 独立视频各配封面 | 每个视频是独立内容 | 每个视频配不同封面 |

```
请选择封面设置方式：

□ 情况1: 不需要封面
  → 使用 YouTube 自动生成的封面（从视频中截取3张供选择）

□ 情况2: 系列视频用同一个封面
  → 提供封面路径: /path/to/cover.jpg
  → 示例: 民间故事系列、电视剧合集等

□ 情况3: 每个视频用不同封面
  → 提供封面文件夹: /path/to/covers/
  → 文件名需与视频匹配（如 video1.mp4 对应 video1.jpg）

封面图片要求：
- 推荐尺寸: 1280x720 像素
- 宽高比: 16:9
- 格式: JPG, PNG, GIF
- 大小: 不超过 2MB
```

### 3. 视频标题设置
```
请选择标题设置方式：
□ 使用文件名作为标题（去除扩展名）
□ 自定义标题模板，例如：
  - "毛泽东选集 第{集数}集 {章节名}"
  - 需要提供标题列表
□ 手动为每个视频设置标题
```

### 4. 视频描述设置
```
请提供视频描述：
□ 所有视频使用相同描述
□ 每个视频使用不同描述（提供描述列表）
□ 不设置描述
```

### 5. 播放列表设置
```
是否添加到播放列表？
□ 否
□ 是，添加到现有播放列表: ____________
□ 是，创建新播放列表: ____________
```

### 6. 盈利设置 (Monetization)
```
是否开启盈利？
□ 是，开启广告盈利
□ 否，不开启盈利
```

### 7. 可见性设置
```
请选择发布可见性：
□ Public (公开)
□ Unlisted (不公开，有链接可观看)
□ Private (私有，仅自己可见)
□ Scheduled (定时发布)
```

### 8. 定时发布设置（如选择 Scheduled）
```
请设置定时发布参数：
- 开始日期: ____________ (例如: 2026-01-07)
- 开始时间: ____________ (例如: 09:00)
- 时区: ____________ (例如: Asia/Shanghai)
- 发布间隔: ____________ 分钟 (默认: 13-16分钟)
```

### 9. 其他设置
```
□ 是否允许评论
□ 是否显示点赞数
□ 视频分类: ____________ (例如: Education, Entertainment)
□ 标签/Tags: ____________
```

---

## 操作流程

### 步骤 1: 导航到 YouTube Studio

```javascript
mcp__playwright__browser_navigate({
  url: "https://studio.youtube.com"
})
```

### 步骤 2: 点击上传按钮

```javascript
mcp__playwright__browser_click({
  element: "Upload videos button",
  ref: "上传按钮的ref"
})
```

### 步骤 3: 选择视频文件

```javascript
// 点击 Select files 按钮
mcp__playwright__browser_click({
  element: "Select files button",
  ref: "选择文件按钮的ref"
})

// 上传视频文件
mcp__playwright__browser_file_upload({
  paths: ["用户提供的视频路径列表"]
})
```

### 步骤 4: 编辑视频详情

对每个上传的视频：

#### 4.1 设置标题
```javascript
// 如果需要修改标题
mcp__playwright__browser_type({
  element: "Title input",
  ref: "标题输入框的ref",
  text: "用户指定的标题"
})
```

#### 4.2 设置描述
```javascript
mcp__playwright__browser_type({
  element: "Description input",
  ref: "描述输入框的ref",
  text: "用户提供的描述"
})
```

#### 4.3 上传封面（如果选择自定义封面）
```javascript
// 点击上传缩略图按钮
mcp__playwright__browser_click({
  element: "Upload thumbnail button",
  ref: "上传缩略图按钮的ref"
})

// 选择封面图片
mcp__playwright__browser_file_upload({
  paths: ["用户提供的封面路径"]
})
```

#### 4.4 选择播放列表
```javascript
// 点击播放列表下拉
mcp__playwright__browser_click({
  element: "Playlist dropdown",
  ref: "播放列表下拉的ref"
})

// 选择目标播放列表
mcp__playwright__browser_click({
  element: "用户指定的播放列表",
  ref: "播放列表选项的ref"
})
```

### 步骤 5: 设置盈利（如果开启）

```javascript
// 导航到 Monetisation 标签
mcp__playwright__browser_click({
  element: "Monetisation tab",
  ref: "盈利标签的ref"
})

// 点击编辑盈利状态按钮
mcp__playwright__browser_click({
  element: "Edit video monetisation status button",
  ref: "编辑盈利状态按钮的ref"
})

// 选择 "On" 开启盈利
mcp__playwright__browser_click({
  element: "On radio button",
  ref: "On选项的ref"
})

// 点击 Done 确认
mcp__playwright__browser_click({
  element: "Done button",
  ref: "Done按钮的ref"
})
```

### 步骤 5.5: 设置广告适宜性 (Ad suitability) - 重要！

**说明**：开启盈利后必须完成此步骤，否则 Schedule 按钮会被禁用。对于一般内容，默认选择 "None of the above"。

```javascript
// 导航到 Ad suitability 标签
mcp__playwright__browser_click({
  element: "Ad suitability tab",
  ref: "广告适宜性标签的ref"
})

// 选择 "None of the above"（以上都没有）- 默认选择
mcp__playwright__browser_click({
  element: "None of the above checkbox",
  ref: "以上都没有复选框的ref"
})

// 点击 Submit rating 提交评级
mcp__playwright__browser_click({
  element: "Submit rating button",
  ref: "提交评级按钮的ref"
})

// 等待显示 "Rating saved" 确认
```

**注意**：如果视频内容确实包含敏感内容，应如实勾选相应选项。

### 步骤 6: 设置可见性

```javascript
// 导航到 Visibility 标签
mcp__playwright__browser_click({
  element: "Visibility tab",
  ref: "可见性标签的ref"
})

// 选择可见性选项
// Public / Unlisted / Private / Schedule
mcp__playwright__browser_click({
  element: "用户选择的可见性",
  ref: "可见性选项的ref"
})
```

### 步骤 7: 设置定时发布（如果选择 Schedule）

#### 时间计算规则（重要！）

| 规则 | 说明 |
|------|------|
| **第一个视频时间** | 当前时间 + 5-10 分钟（程序运行需要时间，预留缓冲） |
| **日期选择** | 使用当前日期，不要设置到未来日期 |
| **后续视频间隔** | 比前一个视频晚 13-16 分钟 |
| **时间选择器精度** | YouTube 以 15 分钟为间隔（如 21:00, 21:15, 21:30） |

**计算示例**：
- 当前时间: 20:32
- 第一个视频: 20:45（最近的 15 分钟间隔时间）
- 第二个视频: 21:00（+15 分钟）
- 第三个视频: 21:15（+15 分钟）
- ...

**为什么不设置到未来日期？**
- 视频发布后观众能立即看到，设置到当天可以尽早获得观看量
- 如果程序运行时间长导致时间过期，往后推几分钟即可，不需要改日期

**时间过期处理**：
- 如果运行到某个视频时，原定的发布时间已过期（显示 "Select a time in the future"）
- **正确做法**：将当前及后续所有视频的发布时间都往后推，保持间隔不变
- 例如：原定 21:00 的视频过期了，改为 21:15，后续视频也依次后推（21:30, 21:45...）

```javascript
// 点击 Schedule 选项展开
mcp__playwright__browser_click({
  element: "Schedule section",
  ref: "定时发布选项的ref"
})

// 点击日期选择器
mcp__playwright__browser_click({
  element: "Date picker button",
  ref: "日期按钮的ref"
})

// 在日历中选择日期
mcp__playwright__browser_click({
  element: "目标日期",
  ref: "日期的ref"
})

// 点击时间输入框
mcp__playwright__browser_click({
  element: "Time textbox",
  ref: "时间输入框的ref"
})

// 从下拉列表选择时间（15分钟间隔）
mcp__playwright__browser_click({
  element: "目标时间选项",
  ref: "时间选项的ref"
})
```

**时间过期处理**：
- 如果出现 "Select a time in the future" 警告，说明选择的时间已过期
- **正确做法**：
  1. 将当前视频的时间往后推到最近的可用时间（如当前是 20:30，选择 20:45）
  2. **后续所有视频的时间也要相应后推**，保持间隔不变
- **错误做法**：将日期改到第二天（这会打乱整体发布计划）
- 例如：原计划 21:00, 21:15, 21:30，如果 21:00 过期，改为 21:15, 21:30, 21:45

**等待系统检查**：
- 设置完成后，Schedule 按钮可能暂时处于禁用状态
- 原因：系统正在进行版权检查和内容检查（显示"Checking"）
- 通常需要等待 10-30 秒
- 如果等待超过 1 分钟仍然禁用，检查是否完成了 Ad suitability 问卷

### 步骤 8: 保存/发布

```javascript
// 点击 Save / Publish / Schedule 按钮
mcp__playwright__browser_click({
  element: "Save button",
  ref: "保存按钮的ref"
})
```

---

## 推荐上传流程（单视频逐一完成）

### 完整流程（每个视频）

对于每个视频，按以下顺序完成所有设置后再进行下一个：

1. **上传视频文件** → 等待上传完成
2. **设置标题**（如需修改）
3. **上传封面图片**
4. **选择播放列表**
5. **开启盈利**（Monetisation → Edit → On → Done）
6. **完成广告适宜性问卷**（Ad suitability → None of the above → Submit rating）
7. **设置定时发布**（Visibility → Schedule → 选择日期时间）
8. **点击 Schedule 按钮**
9. **关闭确认对话框**，继续下一个视频

### 时间计算规则

| 规则 | 说明 |
|------|------|
| **第一个视频时间** | 当前时间 + 5-10 分钟（预留程序运行缓冲） |
| **日期选择** | 使用当前日期 |
| **后续视频间隔** | 比前一个视频晚 13-16 分钟（推荐 15 分钟） |

### 时间安排示例

假设当前时间 20:32，程序准备好后约 20:40：
- 视频1: 20:45（当前时间 + 约 5-10 分钟，选最近的 15 分钟间隔）
- 视频2: 21:00（+15 分钟）
- 视频3: 21:15（+15 分钟）
- 视频4: 21:30（+15 分钟）
- 视频5: 21:45（+15 分钟）
- ...

---

## 批量上传示例

### 示例：上传毛泽东选集第33-43集

**用户确认的参数：**
- 视频来源: `/Users/su/Downloads/3d_games/上传/毛泽东选集-第33集-*.mp4` 等11个文件
- 封面: `/Users/su/Downloads/视频封面/毛泽东选集.jpg`（所有视频使用相同封面）
- 标题: 使用文件名（已包含完整标题）
- 描述: 统一使用相同描述
- 播放列表: 毛泽东全集
- 盈利: 开启
- 广告适宜性: None of the above（默认）
- 可见性: 定时发布
- 发布日期: 2026-01-06
- 发布间隔: 每15分钟发布一个（21:00, 21:15, 21:30...）

---

## 常见问题

### Q: 上传速度慢？
A: 取决于网络带宽和视频文件大小。

### Q: 如何批量设置封面？
A: 准备与视频同名的封面图片文件夹，程序会自动匹配。

### Q: 定时发布的时间间隔如何计算？
A: 例如间隔15分钟，第1个视频21:00，第2个21:15，第3个21:30...

### Q: Schedule 按钮一直是禁用状态？
A: 可能的原因：
1. **时间已过期**：检查是否显示"Select a time in the future"，需要选择未来的时间
2. **未完成广告适宜性问卷**：开启盈利后必须完成 Ad suitability 问卷
3. **系统检查中**：等待10-30秒让系统完成版权和内容检查

### Q: 批量上传后视频变成草稿了？
A: 这是因为没有逐一完成每个视频的设置。建议单个视频完成所有步骤（包括点击 Schedule）后再处理下一个。

### Q: 时间选择器没有我想要的精确时间？
A: YouTube 时间选择器以15分钟为间隔（如 21:00, 21:15, 21:30），无法选择如 21:05 这样的时间。

### Q: 出现"We're still checking your video"提示？
A: 这是正常的，系统在进行版权检查。可以选择：
1. 等待检查完成后再点击 Schedule
2. 直接点击 Schedule，会弹出提示框，点击"Got it"确认即可

---

## 中断恢复流程

上传过程可能因为网络问题、程序崩溃、用户中断等原因中断。根据中断情况分为两种恢复场景：

### 场景一：在原 Claude 会话中重启

**情况描述**：用户在同一个 Claude Code 会话中说"继续"或重新开始操作。

**特点**：
- ✅ 浏览器可能仍然打开着
- ✅ 当前页面状态可能保持
- ✅ 可以直接获取页面快照查看状态

**恢复步骤**：
1. **获取浏览器快照** (`browser_snapshot`)
2. **判断当前状态**：
   - 如果在上传对话框中 → 继续完成当前视频设置
   - 如果在 Dashboard 页面 → 检查已上传视频列表
   - 如果浏览器已关闭 → 按场景二处理
3. **继续操作**

**示例**：
```
用户: 继续
助手: [获取浏览器快照]
     → 发现当前在视频上传对话框，标题已填写，正在 Monetisation 标签
     → 继续完成盈利设置 → Ad suitability → Schedule
```

---

### 场景二：在新 Claude 会话中恢复

**情况描述**：用户开启了新的 Claude Code 会话，上一个会话已结束。

**特点**：
- ❌ 浏览器已关闭（会话结束时自动关闭）
- ✅ 登录状态保留（存储在 `~/Library/Caches/ms-playwright/mcp-chrome-*/`）
- ❌ 需要重新打开浏览器并导航

**恢复步骤**：
1. **导航到 YouTube Studio** (`browser_navigate` → `https://studio.youtube.com`)
2. **检查登录状态**（通常会自动保持登录）
3. **导航到 Content 页面**（查看所有视频列表）
4. **识别视频状态**：对比源文件夹和 YouTube Studio 中的视频
5. **处理草稿视频**（优先完成）
6. **继续上传剩余视频**

**示例**：
```
用户: 继续上传 /Users/su/Downloads/民间故事2 中的视频
助手: [导航到 YouTube Studio]
     [获取已上传视频列表]
     → 发现：2 个 Scheduled，1 个 Draft，7 个未上传
     → 先完成草稿视频的设置
     → 然后继续上传剩余 7 个视频
```

---

### 两种场景对比

| 对比项 | 场景一（��会话） | 场景二（新会话） |
|--------|-----------------|-----------------|
| 浏览器状态 | 可能仍打开 | 已关闭 |
| 登录状态 | 保持 | 保持 |
| 页面状态 | 可能保持 | 需重新导航 |
| 恢复速度 | 快（直接继续） | 较慢（需重新打开） |
| 首要操作 | 获取快照判断状态 | 导航到 YouTube Studio |

---

### 恢复步骤（通用）

| 步骤 | 操作 | 说明 |
|------|------|------|
| **1** | 打开 YouTube Studio Content 页面 | `https://studio.youtube.com/channel/xxx/videos/upload` |
| **2** | 识别已上传的视频 | 查看 Scheduled/Draft/Processing 状态的视频 |
| **3** | 对比源文件夹 | 确定哪些视频已上传、哪些是草稿、哪些未上传 |
| **4** | 优先处理草稿 | 先完成草稿视频的设置（盈利、播放列表、定时发布） |
| **5** | 继续上传剩余视频 | 从未上传的视频继续 |
| **6** | 重新计算发布时间 | 根据当前时间重新规划发布时间表 |

### 识别视频状态

在 YouTube Studio Content 页面，视频可能有以下状态：

| 状态 | 含义 | 恢复操作 |
|------|------|----------|
| **Scheduled** | ✅ 已完成定时发布设置 | 无需操作，跳过 |
| **Draft** | ⚠️ 上传完成但未完成设置 | 点击编辑，完成设置后 Schedule |
| **Processing** | ⏳ 正在处理中 | 等待处理完成后继续设置 |
| **不在列表中** | ❌ 未上传 | 需要上传 |

### 草稿视频快速完成设置

对于 Draft 状态的视频，需要完成以下设置：

```
1. 点击视频 → Edit draft
2. 检查标题是否正确
3. 切换到 Monetisation 标签 → Edit → On → Done
4. 完成 Ad suitability 问卷 → None of the above → Submit rating
5. 选择播放列表（如需要）
6. 切换到 Visibility 标签 → Schedule → 设置日期时间
7. 点击 Schedule 按钮
```

### 恢复时的时间计算

中断恢复时，需要重新计算发布时间：

1. **获取当前时间**：恢复操作的实际时间
2. **检查已设置的视频时间**：查看已 Scheduled 的视频最晚发布时间
3. **计算新的开始时间**：
   - 如果有已 Scheduled 的视频：���一个视频 = 最晚时间 + 15分钟
   - 如果没有已 Scheduled 的视频：第一个视频 = 当前时间 + 10分钟

### 恢复操作示例

**场景**：上传5个视频时在第3个视频中断，现在恢复

```
中断前状态：
- 视频1: Scheduled 15:15 ✅
- 视频2: Scheduled 15:30 ✅
- 视频3: Draft (标题已填，其他未设置) ⚠️
- 视频4: 未上传 ❌
- 视频5: 未上传 ❌

恢复操作（当前时间 16:20）：
1. 完成视频3的设置 → Schedule 16:30
2. 上传视频4 → Schedule 16:45
3. 上传视频5 → Schedule 17:00
```

### 终端模式恢复询问模板

```
检测到上次上传可能中断，正在检查状态...

源文件夹: /path/to/videos/ (共 10 个视频)

YouTube Studio 状态:
- ✅ Scheduled: 视频1, 视频2 (2个)
- ⚠️ Draft: 视频3 (1个)
- ❌ 未上传: 视频4-10 (7个)

是否继续上传？
□ 是，从草稿视频3开始继续
□ 是，跳过草稿，从视频4开始上传
□ 否，取消操作

发布时间设置：
- 已有最晚发布时间: 15:30
- 建议下一个视频时间: 16:30（当前时间 + 10分钟）
- 后续视频间隔: 15分钟
```

---

## 相关技能

- [YouTube Studio 下载技能](youtube_studio_download_skill.md)
