// upload-cdp.js - 使用 CDP 连接已登录的 Chrome
//
// 使用方法:
// 1. 先关闭所有 Chrome 窗口
// 2. 运行: ./start-chrome.sh  (启动带调试端口的 Chrome)
// 3. 在 Chrome 中登录 YouTube Studio
// 4. 运行: node upload-cdp.js

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const CONFIG = {
  videoFolder: '/Users/su/Downloads/民间故事2',
  videoPattern: /\.mp4$/,
  debugPort: 9222,
  startHour: 19,
  startMinute: 0,
  intervalMinutes: 15,
  // 已上传的视频关键词（用于跳过）
  uploaded: [
    '供妹创业的哥哥',
    '岳父母带着小舅子',
    '夏夜灵堂忽起风',
    '火电站河道捞起断腿',
    '山村和尚突然还俗',
    '傻小子刘二圈刚和哑女秋月拜完堂',
    '传家金镯失窃疑马力',
    '李生焚画时',
    '穷张家除夕摸到狗屎被地主误当宝，地主为套秘宝把女儿嫁来。地主女儿敲灶坑发现藏金',
    '镇上丢了三幅古画后',
    '孝子扎纸人替母尽孝',
  ],
};

const delay = (ms) => new Promise(r => setTimeout(r, ms));
const mediumDelay = () => delay(2000 + Math.random() * 1000);
const longDelay = () => delay(4000 + Math.random() * 2000);

function log(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
}

function getVideoFiles() {
  return fs.readdirSync(CONFIG.videoFolder)
    .filter(f => CONFIG.videoPattern.test(f))
    .filter(f => !CONFIG.uploaded.some(u => f.includes(u)))
    .sort()
    .map(f => ({
      path: path.join(CONFIG.videoFolder, f),
      name: f.replace('.mp4', '')
    }));
}

function getScheduledTime(index) {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(CONFIG.startHour);
  d.setMinutes(CONFIG.startMinute + index * CONFIG.intervalMinutes);
  d.setSeconds(0);
  return d;
}

async function main() {
  const videos = getVideoFiles();
  log(`找到 ${videos.length} 个待上传视频\n`);

  if (videos.length === 0) {
    log('没有需要上传的视频');
    return;
  }

  videos.forEach((v, i) => {
    log(`  ${i + 1}. ${v.name.substring(0, 50)}...`);
  });

  log('\n连接到 Chrome (端口 9222)...');

  let browser;
  try {
    browser = await chromium.connectOverCDP(`http://localhost:${CONFIG.debugPort}`);
    log('✓ 成功连接到 Chrome');
  } catch (e) {
    log('❌ 无法连接到 Chrome');
    log('请先运行: ./start-chrome.sh');
    log('然后在浏览器中登录 YouTube Studio');
    return;
  }

  const contexts = browser.contexts();
  const context = contexts[0];
  const pages = context.pages();
  let page = pages[0] || await context.newPage();

  try {
    for (let i = 0; i < videos.length; i++) {
      const video = videos[i];
      const scheduledTime = getScheduledTime(i);

      log(`\n${'='.repeat(50)}`);
      log(`上传视频 ${i + 1}/${videos.length}`);
      log(`文件: ${video.name.substring(0, 40)}...`);
      log(`计划: ${scheduledTime.toLocaleString()}`);
      log('='.repeat(50));

      await uploadVideo(page, video, scheduledTime);

      if (i < videos.length - 1) {
        log('等待 15 秒...');
        await delay(15000);
      }
    }

    log('\n✅ 所有视频上传完成！');
  } catch (e) {
    log('❌ 错误: ' + e.message);
  }
}

async function uploadVideo(page, video, scheduledTime) {
  // 1. 打开 YouTube Studio
  log('打开 YouTube Studio...');
  await page.goto('https://studio.youtube.com');
  await longDelay();

  // 检查登录
  if (page.url().includes('accounts.google.com')) {
    log('⚠️ 需要登录！请在浏览器中登录');
    return;
  }

  // 2. 点击创建
  log('点击创建...');
  await page.click('#create-icon').catch(() =>
    page.click('[aria-label="创建"]').catch(() =>
      page.click('[aria-label="Create"]')
    )
  );
  await mediumDelay();

  // 3. 上传视频
  log('选择上传视频...');
  await page.click('tp-yt-paper-item:has-text("上传视频")').catch(() =>
    page.click('tp-yt-paper-item:has-text("Upload videos")')
  );
  await longDelay();

  // 4. 选择文件
  log('选择文件...');
  const fileInput = await page.waitForSelector('input[type="file"]', { timeout: 15000, state: 'attached' });
  await fileInput.setInputFiles(video.path);
  log('✓ 文件已选择');
  await delay(10000);

  // 5. 设置受众
  log('设置受众...');
  try {
    await page.click('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]', { timeout: 8000 });
  } catch {}
  await mediumDelay();

  // 6. 下一步 x3
  for (let i = 1; i <= 3; i++) {
    log(`下一步 ${i}/3...`);
    try { await page.click('#next-button', { timeout: 5000 }); } catch {}
    await mediumDelay();
  }
  await longDelay();

  // 7. 定时发布
  log('设置定时发布...');
  try {
    await page.click('tp-yt-paper-radio-button[name="SCHEDULE"]', { timeout: 5000 });
    await mediumDelay();

    const timeStr = `${String(scheduledTime.getHours()).padStart(2, '0')}:${String(scheduledTime.getMinutes()).padStart(2, '0')}`;
    log(`设置时间: ${timeStr}`);
    try {
      const timeInput = await page.waitForSelector('input[aria-label="时间"]', { timeout: 3000 });
      await timeInput.fill(timeStr);
    } catch {}
  } catch {}

  // 8. 等待上传
  log('等待上传完成...');
  try {
    await page.waitForSelector('span:has-text("上传完毕"), span:has-text("Upload complete")', { timeout: 300000 });
    log('✓ 上传完成');
  } catch {
    log('⚠️ 上传超时，继续...');
  }

  // 9. 保存
  log('保存...');
  try { await page.click('#done-button', { timeout: 10000 }); } catch {}
  await longDelay();

  log(`✅ "${video.name.substring(0, 30)}..." 完成！`);
}

main().catch(console.error);
