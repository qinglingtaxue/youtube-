// upload.js - YouTube 自动上传脚本
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// ========== 配置 ==========
const CONFIG = {
  // 使用 Chrome 的用户数据目录（选择已登录 YouTube 的 Profile）
  // 注意: 运行此脚本时需要关闭 Chrome 浏览器，否则会冲突
  chromeUserDataDir: '/Users/su/Library/Application Support/Google/Chrome',
  // 选择 Profile: Default, Profile 1, Profile 3 等
  chromeProfile: 'Profile 3',

  // 视频文件夹
  videoFolder: '/Users/su/Downloads/3d_games/上传',

  // 视频文件名匹配
  videoPattern: /^毛泽东选集.*\.mp4$/,

  // 封面图片
  coverImage: '/Users/su/Downloads/视频封面/毛泽东选集.jpg',

  // 播放列表
  playlist: '毛泽东选集',
  selectFirstPlaylist: true,

  // 盈利设置
  enableMonetization: true,

  // 定时发布
  startTime: '17:20',
  intervalMin: 13,
  intervalMax: 16,
};

// ========== 人类化延迟 ==========
function randomDelay(min, max) {
  const delay = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise(r => setTimeout(r, delay));
}

const shortDelay = () => randomDelay(300, 800);
const mediumDelay = () => randomDelay(1000, 2500);
const thinkingDelay = () => randomDelay(2000, 4000);


// ========== 日志 ==========
function log(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
}


// ========== 获取视频文件列表 ==========
function getVideoFiles() {
  const files = fs.readdirSync(CONFIG.videoFolder)
    .filter(f => CONFIG.videoPattern.test(f))
    .sort()
    .map(f => path.join(CONFIG.videoFolder, f));
  log(`找到 ${files.length} 个视频文件`);
  return files;
}


// ========== 主函数 ==========
async function main() {
  const videos = getVideoFiles();
  if (videos.length === 0) {
    log('没有找到视频文件');
    return;
  }

  log('启动浏览器（使用已登录的 Chrome Profile）...');
  log(`使用 Profile: ${CONFIG.chromeProfile}`);
  log('⚠️  请确保 Chrome 浏览器已关闭，否则会冲突！');

  // 构建完整的 Profile 路径
  const profilePath = path.join(CONFIG.chromeUserDataDir, CONFIG.chromeProfile);

  // 使用 launchPersistentContext 加载已有的 Profile
  const browser = await chromium.launchPersistentContext(profilePath, {
    headless: false,
    channel: 'chrome',
    args: [
      '--start-maximized',
      '--disable-blink-features=AutomationControlled'  // 隐藏自动化标记
    ],
    viewport: null  // 使用全屏
  });

  const page = browser.pages()[0] || await browser.newPage();

  try {
    await uploadVideos(page, videos);
  } catch (e) {
    log('错误: ' + e.message);
    console.error(e);
  }

  log('完成！浏览器保持打开，请手动检查');
  // 不关闭浏览器，让用户手动检查
  // await browser.close();
}


// ========== 上传视频 ==========
async function uploadVideos(page, videos) {
  log('打开 YouTube Studio...');
  await page.goto('https://studio.youtube.com');
  await thinkingDelay();
  
  // 截图查看页面状态
  await page.screenshot({ path: '/tmp/yt-studio-screenshot.png' });
  log('已截图保存到 /tmp/yt-studio-screenshot.png');
  
  log('点击上传按钮...');
  // 尝试多个可能的选择器
  const uploadSelectors = [
    '#upload-icon',
    'ytcp-button#upload-button',
    '[aria-label="Upload videos"]',
    'button:has-text("Upload")',
    'button:has-text("上传")'
  ];
  
  for (const selector of uploadSelectors) {
    try {
      await page.click(selector, { timeout: 5000 });
      log('✓ 找到上传按钮');
      break;
    } catch (e) {
      log(`尝试 ${selector} 失败`);
    }
  }
  await mediumDelay();

  log('选择视频文件...');
  const fileInput = await page.waitForSelector('input[type="file"]');
  await fileInput.setInputFiles(videos);
  log(`已选择 ${videos.length} 个视频`);
  
  await thinkingDelay();
}


// 启动
main().catch(console.error);
