// upload-api.js - 使用 YouTube Data API 上传视频（推荐方案）
//
// 设置步骤:
// 1. 去 https://console.cloud.google.com/
// 2. 创建项目 -> 启用 YouTube Data API v3
// 3. 创建 OAuth 2.0 凭据 (桌面应用)
// 4. 下载 client_secret.json 到此目录
// 5. 运行: npm install googleapis
// 6. 运行: node upload-api.js (首次运行需授权)

const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');
const readline = require('readline');

const CONFIG = {
  videoFolder: '/Users/su/Downloads/民间故事2',
  videoPattern: /\.mp4$/,
  clientSecretPath: './client_secret.json',
  tokenPath: './token.json',
  // 定时发布配置
  startHour: 19,
  startMinute: 0,
  intervalMinutes: 15,
  // 已上传的视频（跳过）
  uploaded: [
    '供妹创业的哥哥', '岳父母带着小舅子', '夏夜灵堂忽起风',
    '火电站河道捞起断腿', '山村和尚突然还俗', '傻小子刘二圈刚和哑女秋月拜完堂',
    '传家金镯失窃疑马力', '李生焚画时', '孝子扎纸人替母尽孝',
    '穷张家除夕摸到狗屎被地主误当宝，地主为套秘宝把女儿嫁来。地主女儿敲灶坑发现藏金',
    '镇上丢了三幅古画后',
  ],
};

const SCOPES = ['https://www.googleapis.com/auth/youtube.upload'];

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

async function authorize() {
  // 读取凭据
  if (!fs.existsSync(CONFIG.clientSecretPath)) {
    log('❌ 找不到 client_secret.json');
    log('请从 Google Cloud Console 下载 OAuth 2.0 凭据');
    process.exit(1);
  }

  const credentials = JSON.parse(fs.readFileSync(CONFIG.clientSecretPath));
  const { client_id, client_secret, redirect_uris } = credentials.installed || credentials.web;

  const oauth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

  // 检查已有 token
  if (fs.existsSync(CONFIG.tokenPath)) {
    const token = JSON.parse(fs.readFileSync(CONFIG.tokenPath));
    oauth2Client.setCredentials(token);
    log('✓ 使用已保存的授权');
    return oauth2Client;
  }

  // 新授权
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
  });

  log('请在浏览器中打开以下链接进行授权:');
  console.log('\n' + authUrl + '\n');

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const code = await new Promise(resolve => {
    rl.question('输入授权码: ', answer => {
      rl.close();
      resolve(answer);
    });
  });

  const { tokens } = await oauth2Client.getToken(code);
  oauth2Client.setCredentials(tokens);
  fs.writeFileSync(CONFIG.tokenPath, JSON.stringify(tokens));
  log('✓ 授权成功，token 已保存');

  return oauth2Client;
}

async function uploadVideo(youtube, video, scheduledTime) {
  log(`上传: ${video.name.substring(0, 50)}...`);

  const fileSize = fs.statSync(video.path).size;
  log(`文件大小: ${(fileSize / 1024 / 1024).toFixed(2)} MB`);

  const res = await youtube.videos.insert({
    part: 'snippet,status',
    requestBody: {
      snippet: {
        title: video.name,
        description: '【民间故事】助眠系列',
        tags: ['民间故事', '助眠', '故事'],
        categoryId: '22', // People & Blogs
      },
      status: {
        privacyStatus: 'private', // 先设为私享
        publishAt: scheduledTime.toISOString(), // 定时发布
        selfDeclaredMadeForKids: false,
      },
    },
    media: {
      body: fs.createReadStream(video.path),
    },
  }, {
    onUploadProgress: evt => {
      const progress = (evt.bytesRead / fileSize * 100).toFixed(1);
      process.stdout.write(`\r  上传进度: ${progress}%`);
    },
  });

  console.log(''); // 换行
  log(`✓ 上传完成! Video ID: ${res.data.id}`);
  return res.data.id;
}

async function main() {
  const videos = getVideoFiles();
  log(`找到 ${videos.length} 个待上传视频\n`);

  if (videos.length === 0) {
    log('没有需要上传的视频');
    return;
  }

  videos.forEach((v, i) => {
    const time = getScheduledTime(i);
    log(`  ${i + 1}. ${v.name.substring(0, 40)}... -> ${time.toLocaleString()}`);
  });

  log('\n正在授权...');
  const auth = await authorize();
  const youtube = google.youtube({ version: 'v3', auth });

  log('\n开始上传...\n');

  for (let i = 0; i < videos.length; i++) {
    const video = videos[i];
    const scheduledTime = getScheduledTime(i);

    log(`\n[${ i + 1}/${videos.length}] ===============`);
    try {
      await uploadVideo(youtube, video, scheduledTime);
    } catch (e) {
      log(`❌ 上传失败: ${e.message}`);
    }

    if (i < videos.length - 1) {
      log('等待 5 秒...');
      await new Promise(r => setTimeout(r, 5000));
    }
  }

  log('\n✅ 所有视频上传完成！');
}

main().catch(console.error);
