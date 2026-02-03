// upload-manual-login.js - 支持手动登录的上传脚本
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const readline = require('readline');

// ========== 配置 ==========
const CONFIG = {
  chromeUserDataDir: '/Users/su/Library/Application Support/Google/Chrome',
  chromeProfile: 'Profile 3',
  videoFolder: '/Users/su/Downloads/民间故事2',
  videoPattern: /\.mp4$/,
  playlist: '助眠故事',
  startHour: 18,
  startMinute: 30,
  intervalMinutes: 15,
  batchSize: 5,
};

const delay = (ms) => new Promise(r => setTimeout(r, ms));
const mediumDelay = () => delay(1500 + Math.random() * 1000);
const longDelay = () => delay(3000 + Math.random() * 2000);

function log(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
}

function getVideoFiles() {
  return fs.readdirSync(CONFIG.videoFolder)
    .filter(f => CONFIG.videoPattern.test(f))
    .sort()
    .map(f => ({
      path: path.join(CONFIG.videoFolder, f),
      name: f.replace('.mp4', '')
    }));
}

function getScheduledTime(index) {
  const now = new Date();
  const scheduledDate = new Date(now);
  if (now.getHours() > CONFIG.startHour ||
      (now.getHours() === CONFIG.startHour && now.getMinutes() >= CONFIG.startMinute)) {
    scheduledDate.setDate(scheduledDate.getDate() + 1);
  }
  scheduledDate.setHours(CONFIG.startHour);
  scheduledDate.setMinutes(CONFIG.startMinute + index * CONFIG.intervalMinutes);
  scheduledDate.setSeconds(0);
  return scheduledDate;
}

async function waitForEnter(prompt) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  return new Promise(resolve => {
    rl.question(prompt, () => {
      rl.close();
      resolve();
    });
  });
}

async function main() {
  const videos = getVideoFiles();
  log(`找到 ${videos.length} 个视频文件`);

  if (videos.length === 0) {
    log('没有找到视频文件');
    return;
  }

  const batch = videos.slice(0, CONFIG.batchSize);
  log(`本批次上传 ${batch.length} 个视频`);

  log('启动浏览器...');
  log(`使用 Profile: ${CONFIG.chromeProfile}`);

  const profilePath = path.join(CONFIG.chromeUserDataDir, CONFIG.chromeProfile);

  const browser = await chromium.launchPersistentContext(profilePath, {
    headless: false,
    channel: 'chrome',
    args: ['--start-maximized', '--disable-blink-features=AutomationControlled'],
    viewport: null
  });

  const page = browser.pages()[0] || await browser.newPage();

  try {
    // 打开 YouTube Studio
    log('打开 YouTube Studio...');
    await page.goto('https://studio.youtube.com');
    await longDelay();

    // 检查是否需要登录
    const url = page.url();
    if (url.includes('accounts.google.com') || url.includes('signin')) {
      log('');
      log('⚠️  检测到需要登录！');
      log('请在浏览器中手动登录您的 Google 账号');
      log('登录完成并进入 YouTube Studio 后...');
      await waitForEnter('按 Enter 键继续...');
    }

    // 再次检查是否在 YouTube Studio
    await page.goto('https://studio.youtube.com');
    await longDelay();

    // 开始上传
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

async function uploadSingleVideo(page, video, scheduledTime, index) {
  // 确保在 YouTube Studio
  if (!page.url().includes('studio.youtube.com')) {
    await page.goto('https://studio.youtube.com');
    await longDelay();
  }

  // 点击创建按钮
  log('点击创建按钮...');
  const createClicked = await tryClickSelectors(page, [
    '#create-icon',
    'ytcp-button#create-icon',
    '[aria-label="创建"]',
    '[aria-label="Create"]',
    'button:has-text("创建")',
    'button:has-text("Create")',
  ]);

  if (!createClicked) {
    throw new Error('无法找到创建按钮');
  }
  await mediumDelay();

  // 点击上传视频
  log('选择上传视频...');
  await tryClickSelectors(page, [
    'tp-yt-paper-item:has-text("上传视频")',
    'tp-yt-paper-item:has-text("Upload videos")',
    '#text-item-0',
  ]);
  await longDelay();

  // 上传文件
  log('选择视频文件...');
  try {
    // 方法1: 直接设置文件
    const fileInput = await page.waitForSelector('input[type="file"]', { timeout: 10000, state: 'attached' });
    await fileInput.setInputFiles(video.path);
    log('✓ 文件已选择');
  } catch {
    // 方法2: 使用 fileChooser
    log('尝试 fileChooser 方式...');
    try {
      const [fileChooser] = await Promise.all([
        page.waitForEvent('filechooser', { timeout: 10000 }),
        page.click('button:has-text("选择文件")').catch(() => page.click('#select-files-button').catch(() => {}))
      ]);
      await fileChooser.setFiles(video.path);
      log('✓ 文件已通过 fileChooser 选择');
    } catch (e) {
      throw new Error('无法选择文件: ' + e.message);
    }
  }

  // 等待上传开始处理
  log('等待上传处理...');
  await delay(8000);

  // 设置受众 - 不面向儿童
  log('设置受众...');
  try {
    await page.click('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]', { timeout: 5000 });
  } catch {
    log('受众设置可能已选择');
  }

  // 点击下一步三次 (元素 -> 检查 -> 公开范围)
  for (let step = 1; step <= 3; step++) {
    log(`点击下一步 (${step}/3)...`);
    try {
      await page.click('#next-button', { timeout: 5000 });
    } catch {
      log('下一步按钮可能不可用');
    }
    await mediumDelay();
  }

  await longDelay();

  // 选择定时发布
  log('设置定时发布...');
  try {
    await page.click('tp-yt-paper-radio-button[name="SCHEDULE"]', { timeout: 5000 });
    await mediumDelay();

    // 设置日期和时间 (简化处理)
    const timeStr = `${String(scheduledTime.getHours()).padStart(2, '0')}:${String(scheduledTime.getMinutes()).padStart(2, '0')}`;
    log(`设置时间: ${timeStr}`);

    try {
      const timeInput = await page.waitForSelector('input[aria-label="时间"]', { timeout: 3000 });
      await timeInput.fill(timeStr);
    } catch {
      log('时间设置可能使用默认值');
    }
  } catch (e) {
    log('定时发布设置可能失败: ' + e.message);
  }

  // 等待上传完成
  log('等待上传完成...');
  try {
    await page.waitForSelector('span:has-text("上传完毕")', { timeout: 300000 });
    log('✓ 上传完成');
  } catch {
    log('⚠️ 上传状态检测超时，尝试继续...');
  }

  // 保存/发布
  log('保存设置...');
  try {
    await page.click('#done-button', { timeout: 10000 });
  } catch {
    log('保存按钮点击可能失败');
  }
  await longDelay();

  log(`✅ 视频 "${video.name}" 处理完成！`);
}

async function tryClickSelectors(page, selectors) {
  for (const selector of selectors) {
    try {
      await page.click(selector, { timeout: 3000 });
      log(`✓ 成功点击: ${selector}`);
      return true;
    } catch {}
  }
  return false;
}

main().catch(console.error);
