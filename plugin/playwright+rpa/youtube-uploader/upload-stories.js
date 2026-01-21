// upload-stories.js - 民间故事视频上传脚本
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// ========== 配置 ==========
const CONFIG = {
  chromeUserDataDir: '/Users/su/Library/Application Support/Google/Chrome',
  chromeProfile: 'Default',
  videoFolder: '/Users/su/Downloads/民间故事2',
  videoPattern: /\.mp4$/,
  playlist: '助眠故事',
  enableMonetization: true,
  // 定时发布配置
  startHour: 18,
  startMinute: 30,
  intervalMinutes: 15,
  // 每批上传数量
  batchSize: 5,
};

// ========== 延迟函数 ==========
const delay = (ms) => new Promise(r => setTimeout(r, ms));
const shortDelay = () => delay(500 + Math.random() * 500);
const mediumDelay = () => delay(1500 + Math.random() * 1000);
const longDelay = () => delay(3000 + Math.random() * 2000);

function log(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
}

// ========== 获取视频文件 ==========
function getVideoFiles() {
  const files = fs.readdirSync(CONFIG.videoFolder)
    .filter(f => CONFIG.videoPattern.test(f))
    .sort()
    .map(f => ({
      path: path.join(CONFIG.videoFolder, f),
      name: f.replace('.mp4', '')
    }));
  log(`找到 ${files.length} 个视频文件`);
  return files;
}

// ========== 计算发布时间 ==========
function getScheduledTime(index) {
  const now = new Date();
  const scheduledDate = new Date(now);

  // 如果当前时间已过今天的开始时间，从明天开始
  if (now.getHours() > CONFIG.startHour ||
      (now.getHours() === CONFIG.startHour && now.getMinutes() >= CONFIG.startMinute)) {
    scheduledDate.setDate(scheduledDate.getDate() + 1);
  }

  scheduledDate.setHours(CONFIG.startHour);
  scheduledDate.setMinutes(CONFIG.startMinute + index * CONFIG.intervalMinutes);
  scheduledDate.setSeconds(0);

  return scheduledDate;
}

// ========== 主函数 ==========
async function main() {
  const videos = getVideoFiles();
  if (videos.length === 0) {
    log('没有找到视频文件');
    return;
  }

  // 只取前 batchSize 个
  const batch = videos.slice(0, CONFIG.batchSize);
  log(`本批次上传 ${batch.length} 个视频`);

  log('启动浏览器...');
  log(`使用 Profile: ${CONFIG.chromeProfile}`);
  log('⚠️  请确保 Chrome 浏览器已关闭！');

  const profilePath = path.join(CONFIG.chromeUserDataDir, CONFIG.chromeProfile);

  const browser = await chromium.launchPersistentContext(profilePath, {
    headless: false,
    channel: 'chrome',
    args: ['--start-maximized', '--disable-blink-features=AutomationControlled'],
    viewport: null
  });

  const page = browser.pages()[0] || await browser.newPage();

  try {
    for (let i = 0; i < batch.length; i++) {
      const video = batch[i];
      const scheduledTime = getScheduledTime(i);
      log(`\n========== 上传视频 ${i + 1}/${batch.length} ==========`);
      log(`文件: ${video.name}`);
      log(`计划发布: ${scheduledTime.toLocaleString()}`);

      await uploadSingleVideo(page, video, scheduledTime, i);

      if (i < batch.length - 1) {
        log('等待 10 秒后上传下一个...');
        await delay(10000);
      }
    }

    log('\n✅ 本批次上传完成！');
    log(`已上传 ${batch.length} 个视频`);
    log(`剩余 ${videos.length - batch.length} 个视频待上传`);

  } catch (e) {
    log('❌ 错误: ' + e.message);
    console.error(e);
  }

  log('浏览器保持打开，请手动检查');
}

// ========== 上传单个视频 ==========
async function uploadSingleVideo(page, video, scheduledTime, index) {
  log('打开 YouTube Studio...');
  await page.goto('https://studio.youtube.com');
  await longDelay();

  // 截图调试
  await page.screenshot({ path: `/tmp/yt-studio-${index}.png` });
  log(`截图保存到 /tmp/yt-studio-${index}.png`);

  // 点击创建按钮 - 尝试多个选择器
  log('点击创建按钮...');
  const createSelectors = [
    '#create-icon',
    'ytcp-button#create-icon',
    'button#create-icon',
    '[aria-label="创建"]',
    '[aria-label="Create"]',
    'ytcp-icon-button#create-icon',
    'ytcp-button:has-text("创建")',
    'button:has-text("创建")',
    'button:has-text("Create")',
    '#upload-icon'
  ];

  let clicked = false;
  for (const selector of createSelectors) {
    try {
      await page.click(selector, { timeout: 3000 });
      log(`✓ 成功点击: ${selector}`);
      clicked = true;
      break;
    } catch {
      // 继续尝试下一个
    }
  }

  if (!clicked) {
    // 如果所有选择器都失败，尝试用文本定位
    log('尝试通过文本定位...');
    try {
      await page.locator('text=创建').first().click({ timeout: 5000 });
      clicked = true;
    } catch {
      await page.locator('text=Create').first().click({ timeout: 5000 });
      clicked = true;
    }
  }

  if (!clicked) {
    throw new Error('无法找到创建按钮');
  }

  await mediumDelay();

  // 点击上传视频
  log('选择上传视频...');
  const uploadSelectors = [
    'tp-yt-paper-item:has-text("上传视频")',
    'tp-yt-paper-item:has-text("Upload videos")',
    'tp-yt-paper-item:has-text("上傳影片")',
    '#text-item-0',
    'ytcp-text-menu tp-yt-paper-item:first-child'
  ];

  for (const selector of uploadSelectors) {
    try {
      await page.click(selector, { timeout: 3000 });
      log(`✓ 成功点击上传视频: ${selector}`);
      break;
    } catch {
      // 继续尝试
    }
  }
  await mediumDelay();

  // 上传文件
  log('选择视频文件...');
  const fileInput = await page.waitForSelector('input[type="file"]', { timeout: 10000 });
  await fileInput.setInputFiles(video.path);

  // 等待上传开始
  log('等待上传处理...');
  await delay(5000);

  // 设置标题（通常自动填充，但可能需要确认）
  try {
    const titleInput = await page.waitForSelector('#textbox[aria-label="添加标题"]', { timeout: 5000 });
    await titleInput.fill(video.name);
  } catch {
    log('标题已自动填充');
  }

  // 选择"不，这不是面向儿童的内容"
  log('设置受众...');
  await delay(2000);
  try {
    await page.click('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]', { timeout: 5000 });
  } catch {
    log('受众设置可能已选择');
  }

  // 点击下一步（元素）
  log('点击下一步（元素）...');
  await page.click('#next-button');
  await mediumDelay();

  // 点击下一步（检查）
  log('点击下一步（检查）...');
  await page.click('#next-button');
  await mediumDelay();

  // 点击下一步（公开范围）
  log('点击下一步（公开范围）...');
  await page.click('#next-button');
  await longDelay();

  // 选择定时发布
  log('设置定时发布...');
  await page.click('tp-yt-paper-radio-button[name="SCHEDULE"]');
  await mediumDelay();

  // 设置日期
  const dateStr = `${scheduledTime.getMonth() + 1}月${scheduledTime.getDate()}日`;
  log(`设置日期: ${dateStr}`);

  try {
    await page.click('#datepicker-trigger');
    await shortDelay();

    // 输入日期
    const dateInput = await page.waitForSelector('input.tp-yt-paper-input', { timeout: 5000 });
    await dateInput.fill(`${scheduledTime.getFullYear()}/${scheduledTime.getMonth() + 1}/${scheduledTime.getDate()}`);
    await shortDelay();
  } catch (e) {
    log('日期设置方式可能不同: ' + e.message);
  }

  // 设置时间
  const timeStr = `${String(scheduledTime.getHours()).padStart(2, '0')}:${String(scheduledTime.getMinutes()).padStart(2, '0')}`;
  log(`设置时间: ${timeStr}`);

  try {
    const timeInput = await page.waitForSelector('input[aria-label="时间"]', { timeout: 5000 });
    await timeInput.fill(timeStr);
  } catch (e) {
    log('时间设置方式可能不同: ' + e.message);
  }

  // 等待上传完成
  log('等待上传完成...');
  await page.waitForSelector('span:has-text("上传完毕")', { timeout: 300000 });

  // 点击安排时间/发布
  log('保存设置...');
  await page.click('#done-button');
  await longDelay();

  log(`✅ 视频 "${video.name}" 上传完成！`);
}

// 启动
main().catch(console.error);
