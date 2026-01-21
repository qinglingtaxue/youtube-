// upload-connect.js - 连接到已登录的 Chrome 上传视频
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

// ========== 配置 ==========
const CONFIG = {
  videoFolder: '/Users/su/Downloads/民间故事2',
  videoPattern: /\.mp4$/,
  playlist: '助眠故事',
  startHour: 18,
  startMinute: 30,
  intervalMinutes: 15,
  batchSize: 5,
  debugPort: 9222,
};

const delay = (ms) => new Promise(r => setTimeout(r, ms));
const shortDelay = () => delay(500 + Math.random() * 500);
const mediumDelay = () => delay(1500 + Math.random() * 1000);
const longDelay = () => delay(3000 + Math.random() * 2000);

function log(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
}

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

// 启动带远程调试的 Chrome
async function launchChromeWithDebug() {
  return new Promise((resolve, reject) => {
    const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    const profilePath = '/Users/su/Library/Application Support/Google/Chrome/Profile 3';
    const cmd = `"${chromePath}" --remote-debugging-port=${CONFIG.debugPort} --user-data-dir="/Users/su/Library/Application Support/Google/Chrome" --profile-directory="Profile 3" "https://studio.youtube.com"`;

    log('启动 Chrome (带远程调试)...');
    log(`Profile: Profile 3`);

    exec(cmd, (error) => {
      if (error && !error.killed) {
        // Chrome might still be launching, ignore non-fatal errors
      }
    });

    // 等待 Chrome 启动
    setTimeout(() => resolve(), 5000);
  });
}

async function main() {
  const videos = getVideoFiles();
  if (videos.length === 0) {
    log('没有找到视频文件');
    return;
  }

  const batch = videos.slice(0, CONFIG.batchSize);
  log(`本批次上传 ${batch.length} 个视频`);

  // 启动 Chrome
  await launchChromeWithDebug();

  log('连接到 Chrome...');
  let browser;
  try {
    browser = await chromium.connectOverCDP(`http://localhost:${CONFIG.debugPort}`);
    log('✓ 成功连接到 Chrome');
  } catch (e) {
    log('❌ 无法连接到 Chrome: ' + e.message);
    log('请确保没有其他 Chrome 实例在运行');
    return;
  }

  const contexts = browser.contexts();
  if (contexts.length === 0) {
    log('❌ 没有找到浏览器上下文');
    return;
  }

  const context = contexts[0];
  const pages = context.pages();
  let page = pages.length > 0 ? pages[0] : await context.newPage();

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

async function uploadSingleVideo(page, video, scheduledTime, index) {
  log('打开 YouTube Studio...');
  await page.goto('https://studio.youtube.com');
  await longDelay();

  // 截图
  await page.screenshot({ path: `/tmp/yt-studio-${index}.png` });
  log(`截图保存到 /tmp/yt-studio-${index}.png`);

  // 检查是否在登录页面
  const isLoginPage = await page.locator('text=登录').count() > 0 ||
                      await page.locator('text=Sign in').count() > 0;
  if (isLoginPage) {
    log('⚠️ 检测到登录页面，请手动登录后重新运行脚本');
    return;
  }

  // 点击创建按钮
  log('点击创建按钮...');
  const createSelectors = [
    '#create-icon',
    'ytcp-button#create-icon',
    'button#create-icon',
    '[aria-label="创建"]',
    '[aria-label="Create"]',
    'button:has-text("创建")',
    'button:has-text("Create")',
  ];

  let clicked = false;
  for (const selector of createSelectors) {
    try {
      await page.click(selector, { timeout: 3000 });
      log(`✓ 成功点击: ${selector}`);
      clicked = true;
      break;
    } catch {}
  }

  if (!clicked) {
    try {
      await page.locator('text=创建').first().click({ timeout: 5000 });
      clicked = true;
    } catch {
      try {
        await page.locator('text=Create').first().click({ timeout: 5000 });
        clicked = true;
      } catch {}
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
    '#text-item-0',
  ];

  for (const selector of uploadSelectors) {
    try {
      await page.click(selector, { timeout: 3000 });
      log(`✓ 成功点击上传视频`);
      break;
    } catch {}
  }
  await longDelay();

  // 等待文件输入出现
  log('选择视频文件...');
  try {
    const fileInput = await page.waitForSelector('input[type="file"]', { timeout: 15000, state: 'attached' });
    await fileInput.setInputFiles(video.path);
    log('✓ 文件已选择');
  } catch (e) {
    log('尝试另一种方式上传...');
    // 尝试通过 fileChooser
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 5000 }),
      page.click('button:has-text("选择文件")').catch(() => {})
    ]);
    if (fileChooser) {
      await fileChooser.setFiles(video.path);
      log('✓ 文件已通过 fileChooser 选择');
    } else {
      throw new Error('无法上传文件');
    }
  }

  // 等待上传开始
  log('等待上传处理...');
  await delay(8000);

  // 设置受众
  log('设置受众...');
  try {
    await page.click('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]', { timeout: 5000 });
  } catch {
    log('受众设置可能已选择');
  }

  // 点击下一步三次
  for (let step = 1; step <= 3; step++) {
    log(`点击下一步 (${step}/3)...`);
    await page.click('#next-button');
    await mediumDelay();
  }

  await longDelay();

  // 选择定时发布
  log('设置定时发布...');
  try {
    await page.click('tp-yt-paper-radio-button[name="SCHEDULE"]');
    await mediumDelay();
  } catch (e) {
    log('定时发布选择可能失败: ' + e.message);
  }

  // 等待上传完成
  log('等待上传完成...');
  try {
    await page.waitForSelector('span:has-text("上传完毕")', { timeout: 300000 });
    log('✓ 上传完成');
  } catch {
    log('⚠️ 上传状态检测超时，继续...');
  }

  // 保存
  log('保存设置...');
  await page.click('#done-button');
  await longDelay();

  log(`✅ 视频 "${video.name}" 上传完成！`);
}

main().catch(console.error);
