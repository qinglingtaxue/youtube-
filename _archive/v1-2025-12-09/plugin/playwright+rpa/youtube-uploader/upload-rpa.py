#!/usr/bin/env python3
"""
upload-rpa.py - RPA 风格的 YouTube 上传脚本
直接操作已打开的 Chrome 浏览器

使用: python3 upload-rpa.py
"""

import pyautogui
import pyperclip
import time
import os
import subprocess

# 配置
VIDEO_FOLDER = '/Users/su/Downloads/民间故事2'

# 已上传的视频（跳过）
UPLOADED = [
    '供妹创业的哥哥', '岳父母带着小舅子', '夏夜灵堂忽起风',
    '火电站河道捞起断腿', '山村和尚突然还俗', '傻小子刘二圈刚和哑女秋月拜完堂',
    '传家金镯失窃疑马力', '李生焚画时', '孝子扎纸人替母尽孝',
    '穷张家除夕摸到狗屎被地主误当宝，地主为套秘宝把女儿嫁来。地主女儿敲灶坑发现藏金',
    '镇上丢了三幅古画后',
]

pyautogui.PAUSE = 0.3
pyautogui.FAILSAFE = True


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def get_videos():
    videos = []
    for f in sorted(os.listdir(VIDEO_FOLDER)):
        if not f.endswith('.mp4'):
            continue
        if any(u in f for u in UPLOADED):
            continue
        videos.append({
            'path': os.path.join(VIDEO_FOLDER, f),
            'name': f.replace('.mp4', '')
        })
    return videos


def activate_chrome():
    """激活 Chrome"""
    os.system('open -a "Google Chrome"')
    time.sleep(1)


def goto_youtube_studio():
    """打开 YouTube Studio"""
    log("打开 YouTube Studio...")
    pyautogui.hotkey('command', 'l')
    time.sleep(0.5)
    pyautogui.hotkey('command', 'a')
    pyperclip.copy('https://studio.youtube.com')
    pyautogui.hotkey('command', 'v')
    time.sleep(0.3)
    pyautogui.press('return')
    time.sleep(5)


def click_create():
    """点击创建按钮 - 使用键盘快捷键"""
    log("查找创建按钮...")
    # YouTube Studio 没有键盘快捷键，用 Tab 导航到创建按钮
    # 或者直接点击屏幕右上角区域
    # 先用简单方法：直接点击固定位置（需要根据屏幕分辨率调整）

    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    log(f"屏幕尺寸: {screen_width}x{screen_height}")

    # 创建按钮通常在右上角
    # 在 1920x1080 分辨率下大约在 (1770, 80)
    create_x = screen_width - 150
    create_y = 80

    log(f"点击创建按钮位置: ({create_x}, {create_y})")
    pyautogui.click(create_x, create_y)
    time.sleep(2)


def click_upload_videos():
    """点击上传视频"""
    log("选择上传视频...")
    # 菜单弹出后，上传视频是第一项
    pyautogui.press('down')
    time.sleep(0.3)
    pyautogui.press('return')
    time.sleep(3)


def select_file(file_path):
    """选择文件上传"""
    log(f"选择文件: {os.path.basename(file_path)[:40]}...")
    time.sleep(1)

    # 使用 Shift+Cmd+G 打开"前往文件夹"
    pyautogui.hotkey('shift', 'command', 'g')
    time.sleep(1)

    # 粘贴文件路径
    pyperclip.copy(file_path)
    pyautogui.hotkey('command', 'v')
    time.sleep(0.5)
    pyautogui.press('return')
    time.sleep(1)
    pyautogui.press('return')

    log("等待上传开始...")
    time.sleep(10)


def configure_video():
    """配置视频设置"""
    log("设置受众（不面向儿童）...")
    # 多次 Tab 到受众选项
    for _ in range(10):
        pyautogui.press('tab')
        time.sleep(0.1)
    pyautogui.press('space')
    time.sleep(1)

    # 点击下一步 3 次
    for i in range(3):
        log(f"下一步 {i+1}/3...")
        pyautogui.press('tab')
        pyautogui.press('return')
        time.sleep(2)

    time.sleep(2)


def save_video():
    """保存视频"""
    log("保存...")
    # Tab 到保存按钮
    for _ in range(5):
        pyautogui.press('tab')
        time.sleep(0.1)
    pyautogui.press('return')
    time.sleep(3)


def upload_one_video(video):
    """上传单个视频"""
    log(f"\n{'='*50}")
    log(f"上传: {video['name'][:40]}...")
    log('='*50)

    try:
        activate_chrome()
        goto_youtube_studio()
        click_create()
        click_upload_videos()
        select_file(video['path'])
        configure_video()
        save_video()
        log("✓ 完成!")
        return True
    except Exception as e:
        log(f"✗ 失败: {e}")
        return False


def main():
    videos = get_videos()
    log(f"找到 {len(videos)} 个待上传视频\n")

    if not videos:
        log("没有需要上传的视频")
        return

    for i, v in enumerate(videos):
        log(f"  {i+1}. {v['name'][:50]}...")

    log("\n" + "="*50)
    log("3 秒后开始...")
    log("鼠标移到左上角可中止")
    log("="*50)
    time.sleep(3)

    for i, video in enumerate(videos):
        upload_one_video(video)
        if i < len(videos) - 1:
            log("等待 15 秒...")
            time.sleep(15)

    log("\n✅ 所有视频处理完成！")


if __name__ == '__main__':
    main()
