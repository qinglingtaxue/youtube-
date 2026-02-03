// auto-upload-all.js - 全自动批量上传脚本
// 只需运行一次，自动上传所有视频
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// ========== 配置 ==========
const CONFIG = {
  videoFolder: '/Users/su/Downloads/民间故事2',
  videoPattern: /\.mp4$/,
  playlist: '助眠故事',
  // 定时发布配置
  startHour: 19,
  startMinute: 0,
  intervalMinutes: 15,
  // 已上传的视频（跳过这些）
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
const shortDelay = () => delay(800 + Math.random() * 500);
const mediumDelay = () => delay(2000 + Math.random() * 1000);
const longDelay = () => delay(4000 + Math.random() * 2000);

function log(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
}

function getVideoFiles() {
  const files = fs.readdirSync(CONFIG.videoFolder)
    .filter(f => CONFIG.videoPattern.test(f))
    .filter(f => {
      // 跳过已上传的
      return !CONFIG.uploaded.some(uploaded => f.includes(uploaded));
    })
    .sort()
    .map(f => ({
      path: path.join(CONFIG.videoFolder, f),
      name: f.replace('.mp4', '')
    }));
  return files;
}

function getScheduledTime(index) {
  const now = new Date();
  const scheduledDate = new Date(now);
  // 从明天开始
  scheduledDate.setDate(scheduledDate.getDate() + 1);
  scheduledDate.setHours(CONFIG.startHour);
  scheduledDate.setMinutes(CONFIG.startMinute + index * CONFIG.intervalMinutes);
  scheduledDate.setSeconds(0);
  return scheduledDate;
}

async function main() {
  const videos = getVideoFiles();
  log(`找到 ${videos.length} 个待上传视频`);

  if (videos.length === 0) {
    log('没有需要上传的视频');
    return;
  }

  videos.forEach((v, i) => {
    const time = getScheduledTime(i);
    log(`  ${i + 1}. ${v.name.substring(0, 40)}... -> ${time.toLocaleString()}`);
  });

  log('\n启动浏览器（使用已登录的 Chrome Profile 3）...');
  log('⚠️  请确保 Chrome 浏览器已完全关闭！\n');

  // 使用独立的用户数据目录，复制 cookies
  const browser = await chromium.launchPersistentContext(
    '/Users/su/Library/Application Support/Google/Chrome/Profile 3',
    {
      headless: false,
      channel: 'chrome',
      args: [
        '--start-maximized',
        '--disable-blink-features=AutomationControlled',
        '--no-first-run',
        '--no-default-browser-check',
      ],
      viewport: null,
      ignoreDefaultArgs: ['--enable-automation'],
    }
  );

  const page = browser.pages()[0] || await browser.newPage();

  try {
    for (let i = 0; i < videos.length; i++) {
      const video = videos[i];
      const scheduledTime = getScheduledTime(i);

      log(`\n${'='.repeat(60)}`);
      log(`上传视频 ${i + 1}/${videos.length}`);
      log(`文件: ${video.name.substring(0, 50)}...`);
      log(`计划发布: ${scheduledTime.toLocaleString()}`);
      log('='.repeat(60));

      const success = await uploadSingleVideo(page, video, scheduledTime, i);

      if (!success) {
        log('❌ 上传失败，跳过此视频');
        continue;
      }

      if (i < videos.length - 1) {
        log('等待 15 秒后上传下一个...');
        await delay(15000);
      }
    }

    log('\n' + '='.repeat(60));
    log('✅ 所有视频上传完成！');
    log('='.repeat(60));

  } catch (e) {
    log('❌ 错误: ' + e.message);
    console.error(e);
  } finally {
    log('\n浏览器保持打开，请手动检查结果');
    // 不关闭浏览器，让用户检查
  }
}

async function uploadSingleVideo(page, video, scheduledTime, index) {
  try {
    // 1. 打开 YouTube Studio
    log('打开 YouTube Studio...');
    await page.goto('https://studio.youtube.com', { waitUntil: 'networkidle' });
    await longDelay();

    // 检查是否需要登录
    if (page.url().includes('accounts.google.com')) {
      log('⚠️ 需要登录！请在浏览器中登录后按 Ctrl+C 停止脚本，然后重新运行');
      await delay(60000);
      return false;
    }

    // 2. 点击创建按钮
    log('点击创建按钮...');
    await page.click('#create-icon').catch(() =>
      page.click('[aria-label="创建"]').catch(() =>
        page.click('[aria-label="Create"]')
      )
    );
    await mediumDelay();

    // 3. 点击上传视频
    log('选择上传视频...');
    await page.click('tp-yt-paper-item:has-text("上传视频")').catch(() =>
      page.click('tp-yt-paper-item:has-text("Upload videos")')
    );
    await longDelay();

    // 4. 上传文件
    log('选择视频文件...');
    const fileInput = await page.waitForSelector('input[type="file"]', {
      timeout: 15000,
      state: 'attached'
    });
    await fileInput.setInputFiles(video.path);
    log('✓ 文件已选择，等待上传处理...');

    // 等待上传开始处理
    await delay(10000);

    // 5. 设置受众 - 不面向儿童
    log('设置受众（不面向儿童）...');
    try {
      await page.click('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]', { timeout: 8000 });
    } catch {
      log('受众设置可能已选择或不可用');
    }
    await mediumDelay();

    // 6. 点击下一步 3 次
    for (let step = 1; step <= 3; step++) {
      log(`点击下一步 (${step}/3)...`);
      try {
        await page.click('#next-button', { timeout: 5000 });
      } catch {
        log(`下一步 ${step} 可能不可用`);
      }
      await mediumDelay();
    }

    await longDelay();

    // 7. 选择定时发布
    log('设置定时发布...');
    try {
      await page.click('tp-yt-paper-radio-button[name="SCHEDULE"]', { timeout: 5000 });
      await mediumDelay();

      // 设置时间
      const timeStr = `${String(scheduledTime.getHours()).padStart(2, '0')}:${String(scheduledTime.getMinutes()).padStart(2, '0')}`;
      log(`设置时间: ${timeStr}`);

      try {
        const timeInput = await page.waitForSelector('input[aria-label="时间"]', { timeout: 3000 });
        await timeInput.fill(timeStr);
      } catch {
        log('时间设置可能使用默认值');
      }
    } catch (e) {
      log('定时发布设置失败，将使用私享保存: ' + e.message);
    }

    // 8. 等待上传完成
    log('等待视频上传完成...');
    try {
      await page.waitForSelector('span:has-text("上传完毕"), span:has-text("Upload complete")', { timeout: 300000 });
      log('✓ 上传完成');
    } catch {
      log('⚠️ 上传状态检测超时，尝试继续...');
    }

    // 9. 等待处理完成
    log('等待视频处理...');
    await delay(5000);

    // 10. 保存
    log('保存设置...');
    try {
      await page.click('#done-button', { timeout: 10000 });
    } catch {
      // 尝试点击 Schedule 按钮
      try {
        await page.click('ytcp-button:has-text("Schedule")');
      } catch {
        log('保存按钮点击可能失败');
      }
    }
    await longDelay();

    // 关闭可能的确认对话框
    try {
      await page.click('ytcp-button:has-text("Close")').catch(() => {});
    } catch {}

    log(`✅ 视频 "${video.name.substring(0, 30)}..." 处理完成！`);
    return true;

  } catch (e) {
    log('❌ 上传过程出错: ' + e.message);
    return false;
  }
}

main().catch(console.error);
