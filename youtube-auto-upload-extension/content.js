// content.js - YouTube Studio 自动化脚本（人类化版本）

let uploadConfig = null;
let statusPanel = null;

// ========== 人类化随机延迟 ==========

// 随机延迟：模拟人类反应时间
function humanDelay(min = 800, max = 2000) {
  const delay = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise(resolve => setTimeout(resolve, delay));
}

// 短延迟：点击后的反应
function shortDelay() {
  return humanDelay(300, 800);
}

// 中等延迟：切换页面/等待加载
function mediumDelay() {
  return humanDelay(1000, 2500);
}

// 长延迟：思考时间
function thinkingDelay() {
  return humanDelay(2000, 4000);
}


// 模拟人类打字（逐字输入）
async function humanType(element, text) {
  element.focus();
  for (const char of text) {
    element.value += char;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    await humanDelay(50, 150); // 每个字符间隔50-150ms
  }
}

// ========== 状态面板 ==========

function createStatusPanel() {
  if (statusPanel) return;
  
  statusPanel = document.createElement('div');
  statusPanel.id = 'yt-upload-status-panel';
  statusPanel.innerHTML = `
    <div class="panel-header">
      <span>🎬 YouTube 自动上传</span>
      <button id="panel-close">×</button>
    </div>
    <div class="panel-body">
      <div class="status-item">
        <span class="status-label">状态：</span>
        <span id="upload-status" class="status-value">等待中</span>
      </div>
      <div class="status-item">
        <span class="status-label">当前步骤：</span>
        <span id="current-step" class="status-value">-</span>
      </div>
      <div id="log-container"></div>
    </div>
  `;
  document.body.appendChild(statusPanel);
  
  document.getElementById('panel-close').onclick = () => {
    statusPanel.style.display = 'none';
  };
}


function updateStatus(status, step) {
  if (!statusPanel) createStatusPanel();
  statusPanel.style.display = 'block';
  document.getElementById('upload-status').textContent = status;
  document.getElementById('current-step').textContent = step;
}

function addLog(message) {
  if (!statusPanel) createStatusPanel();
  const container = document.getElementById('log-container');
  const time = new Date().toLocaleTimeString();
  container.innerHTML += `<div class="log-item">[${time}] ${message}</div>`;
  container.scrollTop = container.scrollHeight;
}


// ========== 消息监听 ==========

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'startUpload') {
    uploadConfig = message.config;
    createStatusPanel();
    updateStatus('🟢 运行中', '初始化');
    addLog('收到上传指令，开始执行...');
    startUploadProcess();
  }
});


// ========== 工具函数 ==========

function waitForElement(selector, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const element = document.querySelector(selector);
    if (element) return resolve(element);

    const observer = new MutationObserver(() => {
      const el = document.querySelector(selector);
      if (el) {
        observer.disconnect();
        resolve(el);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found`));
    }, timeout);
  });
}


// ========== 上传流程 ==========

async function startUploadProcess() {
  try {
    updateStatus('🟢 运行中', '点击上传按钮');
    addLog('正在点击上传按钮...');
    
    await thinkingDelay(); // 人类思考时间
    
    const uploadBtn = document.querySelector('#upload-icon') || 
                      document.querySelector('ytcp-button#upload-button');
    if (uploadBtn) {
      uploadBtn.click();
      addLog('✓ 已点击上传按钮');
    }
    
    await mediumDelay();
    updateStatus('🟢 运行中', '等待选择文件');
    addLog('请选择要上传的视频文件...');
    
  } catch (e) {
    updateStatus('🔴 出错', e.message);
    addLog('❌ 错误: ' + e.message);
  }
}


// 监听文件上传
function setupFileUploadListener() {
  const observer = new MutationObserver(async () => {
    const progress = document.querySelector('ytcp-video-upload-progress');
    if (progress) {
      observer.disconnect();
      addLog('✓ 检测到视频上传');
      await handleVideoUploaded();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}


// 视频上传后处理
async function handleVideoUploaded() {
  updateStatus('🟢 运行中', '设置视频详情');
  await thinkingDelay();
  
  if (uploadConfig.selectFirstPlaylist) {
    await setPlaylist();
    await mediumDelay();
  }
  
  if (uploadConfig.enableMonetization) {
    await setMonetization();
    await mediumDelay();
  }
  
  await setSchedule();
  
  updateStatus('🟢 完成', '等待发布');
  addLog('✓ 所有设置完成，请点击发布');
}


// 设置播放列表
async function setPlaylist() {
  updateStatus('🟢 运行中', '设置播放列表');
  addLog('正在设置播放列表...');
  
  await shortDelay();
  
  const playlistBtn = document.querySelector('ytcp-video-metadata-playlists');
  if (playlistBtn) {
    playlistBtn.click();
    await mediumDelay();
    
    const checkboxes = document.querySelectorAll('ytcp-checkbox-lit');
    if (checkboxes.length > 0) {
      await shortDelay();
      checkboxes[0].click();
      addLog('✓ 已选择第一个播放列表');
    }
    
    await shortDelay();
    const saveBtn = document.querySelector('ytcp-button#save-button');
    if (saveBtn) saveBtn.click();
  }
}


// 设置盈利
async function setMonetization() {
  updateStatus('🟢 运行中', '设置盈利');
  addLog('正在设置盈利...');
  
  await shortDelay();
  
  const tabs = document.querySelectorAll('tp-yt-paper-tab');
  for (const tab of tabs) {
    if (tab.textContent.includes('Monetization') || tab.textContent.includes('盈利')) {
      tab.click();
      await mediumDelay();
      addLog('✓ 已进入盈利设置');
      break;
    }
  }
  
  await shortDelay();
  const monetizeRadio = document.querySelector('tp-yt-paper-radio-button[name="VIDEO_MONETIZE_ON"]');
  if (monetizeRadio) {
    monetizeRadio.click();
    addLog('✓ 已开启盈利');
  }
}


// 设置定时发布
async function setSchedule() {
  updateStatus('🟢 运行中', '设置定时发布');
  addLog('正在设置定时发布...');
  
  await shortDelay();
  
  const tabs = document.querySelectorAll('tp-yt-paper-tab');
  for (const tab of tabs) {
    if (tab.textContent.includes('Visibility') || tab.textContent.includes('可见')) {
      tab.click();
      await mediumDelay();
      addLog('✓ 已进入可见性设置');
      break;
    }
  }


  await shortDelay();
  
  // 选择定时发布
  const scheduleRadio = document.querySelector('tp-yt-paper-radio-button[name="SCHEDULE"]');
  if (scheduleRadio) {
    scheduleRadio.click();
    await shortDelay();
    addLog('✓ 已选择定时发布');
  }


  // 设置时间
  if (uploadConfig.startTime) {
    await shortDelay();
    const timeInput = document.querySelector('input[type="time"]');
    if (timeInput) {
      timeInput.value = uploadConfig.startTime;
      timeInput.dispatchEvent(new Event('input', { bubbles: true }));
      addLog('✓ 已设置发布时间: ' + uploadConfig.startTime);
    }
  }
}

// 初始化
setupFileUploadListener();
console.log('[YT上传] 人类化插件已加载');
