// popup.js - 弹出窗口逻辑

document.addEventListener('DOMContentLoaded', async () => {
  // 加载保存的配置
  const config = await chrome.storage.local.get([
    'videoPath', 'coverPath', 'playlist', 'startTime',
    'minInterval', 'maxInterval', 'enableMonetization', 'selectFirstPlaylist'
  ]);

  if (config.videoPath) document.getElementById('videoPath').value = config.videoPath;
  if (config.coverPath) document.getElementById('coverPath').value = config.coverPath;
  if (config.playlist) document.getElementById('playlist').value = config.playlist;
  if (config.startTime) document.getElementById('startTime').value = config.startTime;
  if (config.minInterval) document.getElementById('minInterval').value = config.minInterval;
  if (config.maxInterval) document.getElementById('maxInterval').value = config.maxInterval;
  if (config.enableMonetization !== undefined) {
    document.getElementById('enableMonetization').checked = config.enableMonetization;
  }
  if (config.selectFirstPlaylist !== undefined) {
    document.getElementById('selectFirstPlaylist').checked = config.selectFirstPlaylist;
  }


  // 保存配置
  document.getElementById('saveConfig').addEventListener('click', async () => {
    const config = {
      videoPath: document.getElementById('videoPath').value,
      coverPath: document.getElementById('coverPath').value,
      playlist: document.getElementById('playlist').value,
      startTime: document.getElementById('startTime').value,
      minInterval: parseInt(document.getElementById('minInterval').value),
      maxInterval: parseInt(document.getElementById('maxInterval').value),
      enableMonetization: document.getElementById('enableMonetization').checked,
      selectFirstPlaylist: document.getElementById('selectFirstPlaylist').checked
    };

    await chrome.storage.local.set(config);
    showStatus('配置已保存！', 'success');
  });


  // 开始上传
  document.getElementById('startUpload').addEventListener('click', async () => {
    const config = {
      videoPath: document.getElementById('videoPath').value,
      coverPath: document.getElementById('coverPath').value,
      playlist: document.getElementById('playlist').value,
      startTime: document.getElementById('startTime').value,
      minInterval: parseInt(document.getElementById('minInterval').value),
      maxInterval: parseInt(document.getElementById('maxInterval').value),
      enableMonetization: document.getElementById('enableMonetization').checked,
      selectFirstPlaylist: document.getElementById('selectFirstPlaylist').checked
    };

    if (!config.videoPath) {
      showStatus('请输入视频文件夹路径！', 'error');
      return;
    }

    await chrome.storage.local.set(config);


    // 检查是否在 YouTube Studio 页面
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes('studio.youtube.com')) {
      showStatus('请先打开 YouTube Studio！', 'error');
      chrome.tabs.create({ url: 'https://studio.youtube.com' });
      return;
    }

    // 发送消息给 content script
    chrome.tabs.sendMessage(tab.id, { action: 'startUpload', config });
    showStatus('正在启动上传...', 'info');
  });


  function showStatus(message, type) {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = 'status show';
    status.style.color = type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#74c0fc';
  }
});
