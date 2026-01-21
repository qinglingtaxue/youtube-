#!/usr/bin/env python3
"""
youtube-tool.py - YouTube 视频管理工具（上传 + 下载）
支持标签页切换

CLI 用法:
  下载: python youtube-tool.py download --url "播放列表URL" --keywords "101-110"
  上传: python youtube-tool.py upload --folder "/path/to/videos" --range "1-10"
"""

import argparse
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import pyautogui
import pyperclip
import time
import os
import random
import json
from PIL import Image, ImageTk

# 进度保存文件和配置文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_PROGRESS_FILE = os.path.join(SCRIPT_DIR, '.upload_progress.json')
DOWNLOAD_PROGRESS_FILE = os.path.join(SCRIPT_DIR, '.download_progress.json')
CONFIG_FILE = os.path.join(SCRIPT_DIR, '.youtube_tool_config.json')
BATCH_FILE = os.path.join(SCRIPT_DIR, '.batch_workflows.json')


class YouTubeToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 视频管理工具")
        self.root.geometry("1000x800")

        # 共享状态
        self.running = False
        self.stop_flag = False

        # 上传相关
        self.video_list = []
        self.cover_list = []
        self.cover_photo = None

        # 下载相关
        self.download_list = []

        # 删除相关
        self.delete_list = []

        # 批次工作流
        self.batch_list = []

        # 加载配置
        self.config = self.load_config()

        self.create_widgets()

        # 窗口关闭时保存配置
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        """加载保存的配置"""
        default = {
            'video_folder': '/Users/su/Downloads/民间故事2',
            'cover_folder': '',
            'download_folder': os.path.expanduser("~/Downloads"),
            'cover_mode': 'single',
            'group_pattern': '3,1,2'
        }
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    default.update(saved)
        except:
            pass
        return default

    def save_config(self):
        """保存配置"""
        config = {
            'video_folder': self.upload_folder_var.get(),
            'cover_folder': self.cover_folder_var.get(),
            'download_folder': self.download_folder_var.get(),
            'cover_mode': self.cover_mode.get(),
            'group_pattern': self.group_var.get()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass

    def on_close(self):
        """窗口关闭时的处理"""
        self.save_config()
        self.save_batch_workflows_silent()
        self.root.destroy()

    def create_widgets(self):
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # 下载标签页（第一个）
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text="📥 下载视频")

        # 上传标签页
        self.upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.upload_frame, text="📤 上传视频")

        # 删除标签页
        self.delete_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.delete_frame, text="🗑️ 删除视频")

        # 工作流标签页
        self.batch_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_frame, text="📋 批次工作流")

        # 日志标签页
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="📝 日志")

        # 日志区域内容
        self.log_text = scrolledtext.ScrolledText(self.log_frame, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        bottom_frame = ttk.Frame(self.log_frame)
        bottom_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(bottom_frame, text="清空日志", command=self.clear_log).pack(side="right")

        # 构建所有标签页内容
        self.create_upload_tab()
        self.create_download_tab()
        self.create_delete_tab()
        self.create_batch_tab()

    # ==================== 上传标签页 ====================
    def create_upload_tab(self):
        frame = self.upload_frame

        # 配置区域
        config_frame = ttk.LabelFrame(frame, text="上传配置", padding=5)
        config_frame.pack(fill="x", padx=5, pady=5)

        # 视频文件夹
        row1 = ttk.Frame(config_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="视频文件夹:", width=12).pack(side="left")
        self.upload_folder_var = tk.StringVar(value=self.config.get('video_folder', ''))
        ttk.Entry(row1, textvariable=self.upload_folder_var, width=50).pack(side="left", padx=5)
        ttk.Button(row1, text="浏览", command=self.browse_upload_folder).pack(side="left")

        # 封面文件夹
        row2 = ttk.Frame(config_frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="封面文件夹:", width=12).pack(side="left")
        self.cover_folder_var = tk.StringVar(value=self.config.get('cover_folder', ''))
        ttk.Entry(row2, textvariable=self.cover_folder_var, width=50).pack(side="left", padx=5)
        ttk.Button(row2, text="浏览", command=self.browse_cover_folder).pack(side="left")

        # 间隔设置
        row3 = ttk.Frame(config_frame)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="上传间隔:", width=12).pack(side="left")
        self.interval_min = tk.IntVar(value=5)
        ttk.Spinbox(row3, from_=0, to=60, textvariable=self.interval_min, width=3).pack(side="left")
        ttk.Label(row3, text=":").pack(side="left")
        self.interval_sec = tk.IntVar(value=0)
        ttk.Spinbox(row3, from_=0, to=59, textvariable=self.interval_sec, width=3).pack(side="left")
        ttk.Label(row3, text="(分:秒)").pack(side="left", padx=5)

        # 选项
        row4 = ttk.Frame(config_frame)
        row4.pack(fill="x", pady=2)
        self.playlist_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(row4, text="添加到播放列表", variable=self.playlist_enabled).pack(side="left")
        self.playlist_var = tk.StringVar(value="")
        ttk.Entry(row4, textvariable=self.playlist_var, width=20).pack(side="left", padx=5)

        # 主区域：视频列表 + 封面管理
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 左侧：视频列表
        list_frame = ttk.LabelFrame(main_frame, text="待上传视频", padding=5)
        list_frame.pack(side="left", fill="both", expand=True)

        # Treeview
        columns = ("idx", "name", "cover", "status")
        self.upload_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        self.upload_tree.heading("idx", text="#")
        self.upload_tree.heading("name", text="视频名称")
        self.upload_tree.heading("cover", text="封面")
        self.upload_tree.heading("status", text="状态")
        self.upload_tree.column("idx", width=40)
        self.upload_tree.column("name", width=300)
        self.upload_tree.column("cover", width=50)
        self.upload_tree.column("status", width=70)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.upload_tree.yview)
        self.upload_tree.configure(yscrollcommand=scroll.set)
        self.upload_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        # 绑定选择事件以预览封面
        self.upload_tree.bind("<<TreeviewSelect>>", self.on_video_select)

        # 视频列表按钮
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side="right", fill="y", padx=5)
        ttk.Button(btn_frame, text="加载视频", command=self.load_upload_videos, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="追加视频", command=self.append_upload_videos, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_video_list, width=10).pack(pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="全选", command=self.upload_select_all, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="取消选择", command=self.upload_deselect_all, width=10).pack(pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="⬆ 上移", command=self.move_video_up, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="⬇ 下移", command=self.move_video_down, width=10).pack(pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="📋 保存批次", command=self.save_upload_as_batch, width=10).pack(pady=2)

        # 右侧：封面管理
        cover_frame = ttk.LabelFrame(main_frame, text="封面管理", padding=5)
        cover_frame.pack(side="right", fill="y", padx=(5, 0))

        # 封面分配模式
        mode_frame = ttk.Frame(cover_frame)
        mode_frame.pack(fill="x", pady=(0, 3))
        ttk.Label(mode_frame, text="模式:").pack(side="left")
        self.cover_mode = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="单封面", variable=self.cover_mode,
                       value="single", command=self.on_mode_change).pack(side="left")
        ttk.Radiobutton(mode_frame, text="顺序", variable=self.cover_mode,
                       value="order", command=self.on_mode_change).pack(side="left")
        ttk.Radiobutton(mode_frame, text="分组", variable=self.cover_mode,
                       value="group", command=self.on_mode_change).pack(side="left")

        # 分组设置（如 "3,1,2" 表示封面1用于3个视频，封面2用于1个，封面3用于2个）
        self.group_frame = ttk.Frame(cover_frame)
        self.group_frame.pack(fill="x", pady=(0, 3))
        ttk.Label(self.group_frame, text="分组:").pack(side="left")
        self.group_var = tk.StringVar(value="3,1,2")
        self.group_entry = ttk.Entry(self.group_frame, textvariable=self.group_var, width=15)
        self.group_entry.pack(side="left", padx=2)
        self.group_entry.bind('<Return>', lambda e: self.assign_covers_to_videos())
        ttk.Button(self.group_frame, text="应用", command=self.assign_covers_to_videos, width=4).pack(side="left")
        self.group_frame.pack_forget()  # 初始隐藏

        # 匹配说明
        self.match_info = ttk.Label(cover_frame, text="无封面", foreground="blue", wraplength=220)
        self.match_info.pack(anchor="w", pady=(0, 5))

        # 封面列表
        ttk.Label(cover_frame, text="封面列表:").pack(anchor="w")
        cover_list_frame = ttk.Frame(cover_frame)
        cover_list_frame.pack(fill="x")

        self.cover_tree = ttk.Treeview(cover_list_frame, columns=("name",), show="headings", height=4)
        self.cover_tree.heading("name", text="封面文件")
        self.cover_tree.column("name", width=180)
        cover_scroll = ttk.Scrollbar(cover_list_frame, orient="vertical", command=self.cover_tree.yview)
        self.cover_tree.configure(yscrollcommand=cover_scroll.set)
        self.cover_tree.pack(side="left", fill="x")
        cover_scroll.pack(side="left", fill="y")
        self.cover_tree.bind("<<TreeviewSelect>>", self.on_cover_select)

        # 封面操作按钮
        cover_btn_frame = ttk.Frame(cover_list_frame)
        cover_btn_frame.pack(side="right", fill="y", padx=2)
        ttk.Button(cover_btn_frame, text="⬆", command=self.move_cover_up, width=3).pack(pady=2)
        ttk.Button(cover_btn_frame, text="⬇", command=self.move_cover_down, width=3).pack(pady=2)

        # 封面预览区（更大的预览）
        preview_frame = ttk.LabelFrame(cover_frame, text="预览", padding=5)
        preview_frame.pack(fill="both", expand=True, pady=5)

        self.cover_label = ttk.Label(preview_frame, text="[选择封面查看]", anchor="center")
        self.cover_label.pack(expand=True)
        self.cover_info = ttk.Label(preview_frame, text="", wraplength=200)
        self.cover_info.pack(pady=5)

        # 进度和控制
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        self.upload_progress_var = tk.StringVar(value="就绪")
        ttk.Label(ctrl_frame, textvariable=self.upload_progress_var).pack(side="left")

        self.upload_step_var = tk.StringVar(value="")
        ttk.Label(ctrl_frame, textvariable=self.upload_step_var, foreground="green").pack(side="left", padx=20)

        # 左侧按钮
        ttk.Button(ctrl_frame, text="📋 保存为批次", command=self.save_upload_as_batch).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="清除进度", command=self.clear_upload_progress).pack(side="left", padx=5)

        # 右侧按钮
        self.upload_stop_btn = ttk.Button(ctrl_frame, text="⏹ 停止", command=self.stop_task, state="disabled")
        self.upload_stop_btn.pack(side="right", padx=5)

        self.upload_resume_btn = ttk.Button(ctrl_frame, text="▶ 继续未完成", command=self.resume_upload, state="disabled")
        self.upload_resume_btn.pack(side="right", padx=5)

        self.upload_start_btn = ttk.Button(ctrl_frame, text="▶ 开始上传", command=self.start_upload)
        self.upload_start_btn.pack(side="right", padx=5)

        # 初始加载
        self.load_upload_videos()
        self.check_saved_progress()

    # ==================== 下载标签页 ====================
    def create_download_tab(self):
        frame = self.download_frame

        # 配置区域
        config_frame = ttk.LabelFrame(frame, text="下载配置", padding=5)
        config_frame.pack(fill="x", padx=5, pady=5)

        # 播放列表 URL
        row1 = ttk.Frame(config_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="播放列表URL:", width=12).pack(side="left")
        self.playlist_url_var = tk.StringVar(value="https://studio.youtube.com/playlist/")
        ttk.Entry(row1, textvariable=self.playlist_url_var, width=60).pack(side="left", padx=5)
        ttk.Button(row1, text="打开", command=self.open_playlist_url).pack(side="left")

        # 保存目录
        row2 = ttk.Frame(config_frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="保存目录:", width=12).pack(side="left")
        self.download_folder_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        ttk.Entry(row2, textvariable=self.download_folder_var, width=50).pack(side="left", padx=5)
        ttk.Button(row2, text="浏览", command=self.browse_download_folder).pack(side="left")
        ttk.Button(row2, text="打开文件夹", command=self.open_download_folder).pack(side="left", padx=5)

        # 自动创建子文件夹
        row2b = ttk.Frame(config_frame)
        row2b.pack(fill="x", pady=2)
        ttk.Label(row2b, text="", width=12).pack(side="left")
        self.create_subfolder = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2b, text="自动创建子文件夹", variable=self.create_subfolder).pack(side="left")
        self.subfolder_name_var = tk.StringVar(value="YouTube下载_{date}")
        ttk.Entry(row2b, textvariable=self.subfolder_name_var, width=25).pack(side="left", padx=5)
        ttk.Label(row2b, text="({date}=日期)", foreground="gray").pack(side="left")

        # 关键词筛选
        row3 = ttk.Frame(config_frame)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="关键词筛选:", width=12).pack(side="left")
        self.download_keywords_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=self.download_keywords_var, width=40).pack(side="left", padx=5)
        ttk.Label(row3, text="(支持范围: 101-110 或逗号分隔: 1,2,3)", foreground="gray").pack(side="left")

        # 下载间隔
        row4 = ttk.Frame(config_frame)
        row4.pack(fill="x", pady=2)
        ttk.Label(row4, text="下载间隔:", width=12).pack(side="left")
        self.download_interval = tk.IntVar(value=3)
        ttk.Spinbox(row4, from_=1, to=30, textvariable=self.download_interval, width=5).pack(side="left")
        ttk.Label(row4, text="秒").pack(side="left", padx=5)

        # 待下载列表
        list_frame = ttk.LabelFrame(frame, text="待下载视频", padding=5)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Treeview
        columns = ("idx", "name", "status")
        self.download_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.download_tree.heading("idx", text="#")
        self.download_tree.heading("name", text="视频名称/关键词")
        self.download_tree.heading("status", text="状态")
        self.download_tree.column("idx", width=40)
        self.download_tree.column("name", width=500)
        self.download_tree.column("status", width=80)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.download_tree.yview)
        self.download_tree.configure(yscrollcommand=scroll.set)
        self.download_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        # 按钮
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side="right", fill="y", padx=5)
        ttk.Button(btn_frame, text="添加关键词", command=self.add_download_keywords, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="删除选中", command=self.remove_download_selected, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_download_list, width=12).pack(pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="全选", command=self.download_select_all, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="取消选择", command=self.download_deselect_all, width=12).pack(pady=2)

        # 进度和控制
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        self.download_progress_var = tk.StringVar(value="就绪")
        ttk.Label(ctrl_frame, textvariable=self.download_progress_var).pack(side="left")

        self.download_step_var = tk.StringVar(value="")
        ttk.Label(ctrl_frame, textvariable=self.download_step_var, foreground="green").pack(side="left", padx=20)

        self.download_stop_btn = ttk.Button(ctrl_frame, text="⏹ 停止", command=self.stop_task, state="disabled")
        self.download_stop_btn.pack(side="right", padx=5)

        self.download_start_btn = ttk.Button(ctrl_frame, text="▶ 开始下载", command=self.start_download)
        self.download_start_btn.pack(side="right", padx=5)

        ttk.Button(ctrl_frame, text="📋 保存为批次", command=self.save_download_as_batch).pack(side="right", padx=5)

        # 说明
        info_frame = ttk.LabelFrame(frame, text="使用说明", padding=5)
        info_frame.pack(fill="x", padx=5, pady=5)
        info_text = """1. 在浏览器中登录 YouTube Studio
2. 输入播放列表 URL 并点击"打开"（在浏览器中打开播放列表页面）
3. 输入要下载的视频关键词（用逗号分隔，用于匹配视频标题）
4. 设置保存目录（默认自动创建带日期的子文件夹）
5. 点击"开始下载"
6. 下载完成后会弹出提示，可直接打开下载文件夹

注意: YouTube Studio 下载的视频会保存到浏览器的默认下载目录"""
        ttk.Label(info_frame, text=info_text, justify="left").pack(anchor="w")

    # ==================== 上传功能 ====================
    def browse_upload_folder(self):
        folder = filedialog.askdirectory(initialdir=self.upload_folder_var.get())
        if folder:
            self.upload_folder_var.set(folder)
            self.load_upload_videos()

    def browse_cover_folder(self):
        folder = filedialog.askdirectory(initialdir=self.cover_folder_var.get() or self.upload_folder_var.get())
        if folder:
            self.cover_folder_var.set(folder)
            self.load_covers()

    def load_upload_videos(self):
        """从文件夹加载视频（清空现有列表）"""
        folder = self.upload_folder_var.get()
        if not os.path.exists(folder):
            self.log(f"文件夹不存在: {folder}")
            return

        self.video_list.clear()
        videos = sorted([f for f in os.listdir(folder) if f.lower().endswith('.mp4')])

        for v in videos:
            self.video_list.append({
                'path': os.path.join(folder, v),
                'name': v.rsplit('.', 1)[0],
                'cover': None,
                'status': '待上传'
            })

        self.load_covers()
        self.refresh_upload_tree()
        self.log(f"加载了 {len(videos)} 个视频")

    def append_upload_videos(self):
        """追加视频（不清空现有列表）"""
        folder = filedialog.askdirectory(initialdir=self.upload_folder_var.get(), title="选择要追加的视频文件夹")
        if not folder:
            return

        existing_paths = {v['path'] for v in self.video_list}
        videos = sorted([f for f in os.listdir(folder) if f.lower().endswith('.mp4')])
        added = 0

        for v in videos:
            path = os.path.join(folder, v)
            if path not in existing_paths:
                self.video_list.append({
                    'path': path,
                    'name': v.rsplit('.', 1)[0],
                    'cover': None,
                    'status': '待上传'
                })
                added += 1

        self.assign_covers_to_videos()
        self.log(f"追加了 {added} 个视频，共 {len(self.video_list)} 个")

    def clear_video_list(self):
        """清空视频列表"""
        if self.video_list and messagebox.askyesno("确认", "确定清空视频列表？"):
            self.video_list.clear()
            self.refresh_upload_tree()
            self.log("已清空视频列表")

    def load_covers(self):
        folder = self.cover_folder_var.get()
        self.cover_list.clear()

        if folder and os.path.exists(folder):
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    self.cover_list.append(os.path.join(folder, f))

        self.refresh_cover_tree()
        self.assign_covers_to_videos()

    def refresh_cover_tree(self):
        """刷新封面列表显示"""
        self.cover_tree.delete(*self.cover_tree.get_children())
        for i, cover_path in enumerate(self.cover_list):
            name = os.path.basename(cover_path)
            self.cover_tree.insert("", "end", values=(f"{i+1}. {name}",))

    def on_mode_change(self):
        """模式切换时的处理"""
        mode = self.cover_mode.get()
        if mode == "group":
            self.group_frame.pack(fill="x", pady=(0, 3), after=self.group_frame.master.winfo_children()[0])
        else:
            self.group_frame.pack_forget()
        self.assign_covers_to_videos()

    def assign_covers_to_videos(self):
        """将封面分配给视频"""
        if not self.cover_list:
            for video in self.video_list:
                video['cover'] = None
            self.match_info.configure(text="无封面")
        else:
            mode = self.cover_mode.get()
            if mode == "single":
                # 单封面模式：所有视频使用第一个封面
                for video in self.video_list:
                    video['cover'] = self.cover_list[0]
                self.match_info.configure(text=f"单封面: 所有 {len(self.video_list)} 个视频用同一封面")
            elif mode == "order":
                # 顺序模式：第n个封面匹配第n个视频
                for i, video in enumerate(self.video_list):
                    if i < len(self.cover_list):
                        video['cover'] = self.cover_list[i]
                    else:
                        video['cover'] = None
                self.match_info.configure(text=f"顺序: {len(self.cover_list)} 封面对应 {len(self.video_list)} 视频")
            elif mode == "group":
                # 分组模式：根据分组数分配
                try:
                    groups = [int(x.strip()) for x in self.group_var.get().split(',') if x.strip()]
                    video_idx = 0
                    for cover_idx, count in enumerate(groups):
                        if cover_idx >= len(self.cover_list):
                            break
                        for _ in range(count):
                            if video_idx < len(self.video_list):
                                self.video_list[video_idx]['cover'] = self.cover_list[cover_idx]
                                video_idx += 1
                    # 剩余视频无封面
                    for i in range(video_idx, len(self.video_list)):
                        self.video_list[i]['cover'] = None
                    self.match_info.configure(text=f"分组: {groups}")
                except:
                    self.match_info.configure(text="分组格式错误，如: 3,1,2")
        self.refresh_upload_tree()

    def on_cover_select(self, event):
        """选择封面时预览"""
        selected = self.cover_tree.selection()
        if not selected:
            return

        idx = self.cover_tree.index(selected[0])
        if idx >= len(self.cover_list):
            return

        cover_path = self.cover_list[idx]
        try:
            img = Image.open(cover_path)
            img.thumbnail((240, 135), Image.Resampling.LANCZOS)  # 更大的预览
            self.cover_photo = ImageTk.PhotoImage(img)
            self.cover_label.configure(image=self.cover_photo, text="")

            # 显示匹配的视频
            if len(self.cover_list) == 1:
                self.cover_info.configure(text=f"此封面用于所有 {len(self.video_list)} 个视频")
            elif idx < len(self.video_list):
                video_name = self.video_list[idx]['name'][:30]
                self.cover_info.configure(text=f"匹配视频: {video_name}...")
            else:
                self.cover_info.configure(text="(无匹配视频)")
        except Exception as e:
            self.cover_label.configure(image="", text="加载失败")
            self.cover_info.configure(text=str(e))

    def on_video_select(self, event):
        """选择视频时同步选中对应封面"""
        selected = self.upload_tree.selection()
        if not selected:
            return

        idx = self.upload_tree.index(selected[0])
        cover_items = self.cover_tree.get_children()

        if len(self.cover_list) == 1 and cover_items:
            self.cover_tree.selection_set(cover_items[0])
            self.on_cover_select(None)
        elif idx < len(cover_items):
            self.cover_tree.selection_set(cover_items[idx])
            self.on_cover_select(None)

    def move_cover_up(self):
        """上移封面"""
        selected = self.cover_tree.selection()
        if not selected:
            return
        idx = self.cover_tree.index(selected[0])
        if idx == 0:
            return
        self.cover_list[idx], self.cover_list[idx-1] = self.cover_list[idx-1], self.cover_list[idx]
        self.refresh_cover_tree()
        self.assign_covers_to_videos()
        items = self.cover_tree.get_children()
        if idx-1 < len(items):
            self.cover_tree.selection_set(items[idx-1])

    def move_cover_down(self):
        """下移封面"""
        selected = self.cover_tree.selection()
        if not selected:
            return
        idx = self.cover_tree.index(selected[0])
        if idx >= len(self.cover_list) - 1:
            return
        self.cover_list[idx], self.cover_list[idx+1] = self.cover_list[idx+1], self.cover_list[idx]
        self.refresh_cover_tree()
        self.assign_covers_to_videos()
        items = self.cover_tree.get_children()
        if idx+1 < len(items):
            self.cover_tree.selection_set(items[idx+1])

    def move_video_up(self):
        """上移视频"""
        selected = self.upload_tree.selection()
        if not selected:
            return
        idx = self.upload_tree.index(selected[0])
        if idx == 0:
            return
        self.video_list[idx], self.video_list[idx-1] = self.video_list[idx-1], self.video_list[idx]
        self.assign_covers_to_videos()
        items = self.upload_tree.get_children()
        if idx-1 < len(items):
            self.upload_tree.selection_set(items[idx-1])

    def move_video_down(self):
        """下移视频"""
        selected = self.upload_tree.selection()
        if not selected:
            return
        idx = self.upload_tree.index(selected[0])
        if idx >= len(self.video_list) - 1:
            return
        self.video_list[idx], self.video_list[idx+1] = self.video_list[idx+1], self.video_list[idx]
        self.assign_covers_to_videos()
        items = self.upload_tree.get_children()
        if idx+1 < len(items):
            self.upload_tree.selection_set(items[idx+1])

    def refresh_upload_tree(self):
        self.upload_tree.delete(*self.upload_tree.get_children())
        for i, v in enumerate(self.video_list):
            cover_status = "✓" if v['cover'] else "✗"
            self.upload_tree.insert("", "end", values=(i+1, v['name'][:40], cover_status, v['status']))

    def upload_select_all(self):
        for item in self.upload_tree.get_children():
            self.upload_tree.selection_add(item)

    def upload_deselect_all(self):
        self.upload_tree.selection_remove(*self.upload_tree.get_children())

    # 进度保存/恢复
    def save_upload_progress(self, video_paths, current_index):
        """保存当前进度"""
        progress = {
            'video_paths': video_paths,
            'current_index': current_index,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'folder': self.upload_folder_var.get(),
            'cover_folder': self.cover_folder_var.get()
        }
        try:
            with open(UPLOAD_PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存进度失败: {e}")

    def load_upload_progress(self):
        """加载保存的进度"""
        try:
            if os.path.exists(UPLOAD_PROGRESS_FILE):
                with open(UPLOAD_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"加载进度失败: {e}")
        return None

    def check_saved_progress(self):
        """检查是否有未完成的进度"""
        progress = self.load_upload_progress()
        if progress:
            remaining = len(progress['video_paths']) - progress['current_index']
            if remaining > 0:
                self.upload_resume_btn.configure(state="normal")
                self.log(f"发现未完成任务: 还有 {remaining} 个视频待上传 (保存于 {progress['timestamp']})")

    def clear_upload_progress(self):
        """清除进度"""
        try:
            if os.path.exists(UPLOAD_PROGRESS_FILE):
                os.remove(UPLOAD_PROGRESS_FILE)
        except Exception:
            pass
        self.upload_resume_btn.configure(state="disabled")
        self.log("已清除保存的进度")

    def save_upload_as_batch(self):
        """将当前上传配置保存为批次"""
        selected = self.upload_tree.selection()
        if not selected:
            # 如果没有选择，使用全部视频
            videos_to_save = self.video_list.copy()
        else:
            indices = [self.upload_tree.index(item) for item in selected]
            videos_to_save = [self.video_list[i].copy() for i in indices]

        if not videos_to_save:
            messagebox.showwarning("警告", "没有可保存的视频")
            return

        # 创建批次，保存完整的视频和封面信息
        batch_name = f"上传批次_{len(self.batch_list)+1}"
        batch = {
            'name': batch_name,
            'type': 'upload',
            'videos': videos_to_save,  # 保存完整的视频列表（包含路径和封面）
            'interval': self.interval_min.get() * 60 + self.interval_sec.get(),
            'status': '待执行',
            'video_count': len(videos_to_save)
        }

        self.batch_list.append(batch)
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()

        # 显示保存的内容
        video_names = [v['name'][:20] + '...' if len(v['name']) > 20 else v['name'] for v in videos_to_save[:3]]
        if len(videos_to_save) > 3:
            video_names.append(f"...等 {len(videos_to_save)} 个")
        self.log(f"✓ 已保存上传批次: {batch_name}")
        self.log(f"  视频: {', '.join(video_names)}")
        messagebox.showinfo("成功", f"已保存批次: {batch_name}\n包含 {len(videos_to_save)} 个视频")

    def save_download_as_batch(self):
        """将当前下载配置保存为批次"""
        if not self.download_list:
            messagebox.showwarning("警告", "下载列表为空")
            return

        keywords = [d['keyword'] for d in self.download_list]
        batch_name = f"下载批次_{len(self.batch_list)+1}"
        batch = {
            'name': batch_name,
            'type': 'download',
            'keywords_list': keywords,  # 保存完整的关键词列表
            'keywords': ','.join(keywords),  # 兼容旧格式
            'url': self.playlist_url_var.get(),
            'folder': self.download_folder_var.get(),
            'interval': self.download_interval.get(),
            'status': '待执行',
            'keyword_count': len(keywords)
        }

        self.batch_list.append(batch)
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()

        self.log(f"✓ 已保存下载批次: {batch_name}")
        self.log(f"  关键词: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
        messagebox.showinfo("成功", f"已保存批次: {batch_name}\n包含 {len(keywords)} 个关键词")

    def save_delete_as_batch(self):
        """将当前删除配置保存为批次"""
        if not self.delete_list:
            messagebox.showwarning("警告", "删除列表为空")
            return

        keywords = [d['keyword'] for d in self.delete_list]
        batch_name = f"删除批次_{len(self.batch_list)+1}"
        batch = {
            'name': batch_name,
            'type': 'delete',
            'keywords_list': keywords,  # 保存完整的关键词列表
            'keywords': ','.join(keywords),  # 兼容旧格式
            'url': self.delete_url_var.get(),
            'interval': self.delete_interval.get(),
            'status': '待执行',
            'keyword_count': len(keywords)
        }

        self.batch_list.append(batch)
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()

        self.log(f"✓ 已保存删除批次: {batch_name}")
        self.log(f"  关键词: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
        messagebox.showinfo("成功", f"已保存批次: {batch_name}\n包含 {len(keywords)} 个关键词")

    def resume_upload(self):
        """继续未完成的上传"""
        progress = self.load_upload_progress()
        if not progress:
            messagebox.showwarning("提示", "没有找到未完成的任务")
            return

        remaining_paths = progress['video_paths'][progress['current_index']:]
        if not remaining_paths:
            messagebox.showinfo("提示", "所有任务已完成")
            self.clear_upload_progress()
            return

        resume_videos = []
        for path in remaining_paths:
            if os.path.exists(path):
                name = os.path.basename(path).rsplit('.', 1)[0]
                cover = None
                for v in self.video_list:
                    if v['path'] == path:
                        cover = v.get('cover')
                        break
                resume_videos.append({
                    'path': path,
                    'name': name,
                    'cover': cover,
                    'status': '待上传'
                })

        if not resume_videos:
            messagebox.showwarning("提示", "找不到待上传的视频文件")
            return

        self.log(f"继续上传 {len(resume_videos)} 个视频...")

        self.running = True
        self.stop_flag = False
        self.upload_start_btn.configure(state="disabled")
        self.upload_resume_btn.configure(state="disabled")
        self.upload_stop_btn.configure(state="normal")

        thread = threading.Thread(target=self.resume_upload_thread, args=(resume_videos, remaining_paths))
        thread.daemon = True
        thread.start()

    def resume_upload_thread(self, videos, all_paths):
        """继续上传的线程"""
        total = len(videos)
        pyautogui.PAUSE = 0.3

        self.log("3 秒后开始，将鼠标移到左上角可中止")
        time.sleep(3)

        for i, video in enumerate(videos):
            if self.stop_flag:
                self.save_upload_progress(all_paths, i)
                self.log("已停止，进度已保存")
                break

            video['status'] = '上传中'
            self.root.after(0, lambda: self.upload_progress_var.set(f"进度: {i+1}/{total}"))

            try:
                self.upload_single(video)
                video['status'] = '✓ 完成'
                self.log(f"✓ 完成: {video['name'][:40]}...")
                self.save_upload_progress(all_paths, i + 1)
            except Exception as e:
                video['status'] = '✗ 失败'
                self.log(f"✗ 失败: {e}")
                self.save_upload_progress(all_paths, i)

            if i < total - 1 and not self.stop_flag:
                interval = self.interval_min.get() * 60 + self.interval_sec.get()
                self.log(f"等待 {interval} 秒...")
                time.sleep(interval)

        self.root.after(0, lambda: self.upload_start_btn.configure(state="normal"))
        self.root.after(0, lambda: self.upload_stop_btn.configure(state="disabled"))
        self.root.after(0, lambda: self.upload_progress_var.set("完成"))

        if not self.stop_flag:
            self.clear_upload_progress()

        self.running = False

    def start_upload(self):
        selected = self.upload_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要上传的视频")
            return

        self.running = True
        self.stop_flag = False
        self.upload_start_btn.configure(state="disabled")
        self.upload_resume_btn.configure(state="disabled")
        self.upload_stop_btn.configure(state="normal")

        indices = [self.upload_tree.index(item) for item in selected]
        thread = threading.Thread(target=self.upload_thread, args=(indices,))
        thread.daemon = True
        thread.start()

    def upload_thread(self, indices):
        videos = [self.video_list[i] for i in indices]
        total = len(videos)
        video_paths = [v['path'] for v in videos]

        pyautogui.PAUSE = 0.3
        self.log(f"开始上传 {total} 个视频")
        self.log("3 秒后开始，鼠标移到左上角可中止")
        time.sleep(3)

        # 保存初始进度
        self.save_upload_progress(video_paths, 0)

        for i, video in enumerate(videos):
            if self.stop_flag:
                self.save_upload_progress(video_paths, i)
                self.log("已停止，进度已保存")
                self.root.after(0, lambda: self.upload_resume_btn.configure(state="normal"))
                break

            video['status'] = '上传中'
            self.root.after(0, self.refresh_upload_tree)
            self.root.after(0, lambda: self.upload_progress_var.set(f"进度: {i+1}/{total}"))

            try:
                self.upload_single(video)
                video['status'] = '✓ 完成'
                self.log(f"✓ 完成: {video['name'][:40]}...")
                self.save_upload_progress(video_paths, i + 1)
            except Exception as e:
                video['status'] = '✗ 失败'
                self.log(f"✗ 失败: {e}")
                self.save_upload_progress(video_paths, i)

            self.root.after(0, self.refresh_upload_tree)

            if i < total - 1 and not self.stop_flag:
                interval = self.interval_min.get() * 60 + self.interval_sec.get()
                self.log(f"等待 {interval} 秒...")
                time.sleep(interval)

        self.root.after(0, lambda: self.upload_start_btn.configure(state="normal"))
        self.root.after(0, lambda: self.upload_stop_btn.configure(state="disabled"))
        self.root.after(0, lambda: self.upload_progress_var.set("完成"))

        if not self.stop_flag:
            self.clear_upload_progress()
            self.log("✅ 上传任务结束")

        self.running = False

    def upload_single(self, video):
        """上传单个视频 (RPA)"""
        video_path = video['path']
        cover_path = video.get('cover')

        # 激活 Chrome
        self.update_upload_step("激活浏览器...")
        os.system('open -a "Google Chrome"')
        time.sleep(1)

        # 打开 YouTube Studio
        self.update_upload_step("打开 YouTube Studio...")
        pyautogui.hotkey('command', 'l')
        time.sleep(0.5)
        pyautogui.hotkey('command', 'a')
        pyperclip.copy('https://studio.youtube.com')
        pyautogui.hotkey('command', 'v')
        time.sleep(0.3)
        pyautogui.press('return')
        time.sleep(5)

        # 点击创建
        self.update_upload_step("点击创建...")
        screen_width, _ = pyautogui.size()
        pyautogui.click(screen_width - 150, 80)
        time.sleep(2)

        # 选择上传
        self.update_upload_step("选择上传视频...")
        pyautogui.press('down')
        time.sleep(0.3)
        pyautogui.press('return')
        time.sleep(3)

        # 选择文件
        self.update_upload_step("选择文件...")
        time.sleep(1)
        pyautogui.hotkey('shift', 'command', 'g')
        time.sleep(1)
        pyperclip.copy(video_path)
        pyautogui.hotkey('command', 'v')
        time.sleep(0.5)
        pyautogui.press('return')
        time.sleep(1)
        pyautogui.press('return')
        time.sleep(10)

        # 上传封面
        if cover_path and os.path.exists(cover_path):
            self.update_upload_step("上传封面...")
            try:
                pyautogui.press('tab')
                time.sleep(0.3)
                pyautogui.press('tab')
                time.sleep(0.3)
                pyautogui.press('return')
                time.sleep(2)
                pyautogui.hotkey('shift', 'command', 'g')
                time.sleep(1)
                pyperclip.copy(cover_path)
                pyautogui.hotkey('command', 'v')
                time.sleep(0.5)
                pyautogui.press('return')
                time.sleep(1)
                pyautogui.press('return')
                time.sleep(3)
            except:
                pass

        # 设置受众
        self.update_upload_step("设置受众...")
        for _ in range(10):
            pyautogui.press('tab')
            time.sleep(0.1)
        pyautogui.press('space')
        time.sleep(1)

        # 下一步 x3
        for i in range(3):
            self.update_upload_step(f"下一步 {i+1}/3...")
            pyautogui.press('tab')
            pyautogui.press('return')
            time.sleep(2)
        time.sleep(2)

        # 保存
        self.update_upload_step("保存...")
        for _ in range(5):
            pyautogui.press('tab')
            time.sleep(0.1)
        pyautogui.press('return')
        time.sleep(3)

        self.update_upload_step("完成")

    def update_upload_step(self, text):
        self.root.after(0, lambda: self.upload_step_var.set(text))

    # ==================== 下载功能 ====================
    def browse_download_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder_var.get())
        if folder:
            self.download_folder_var.set(folder)

    def open_download_folder(self):
        """打开下载文件夹"""
        folder = self.get_download_folder()
        if os.path.exists(folder):
            os.system(f'open "{folder}"')
        else:
            messagebox.showinfo("提示", f"文件夹不存在: {folder}")

    def get_download_folder(self):
        """获取实际的下载文件夹路径"""
        base_folder = self.download_folder_var.get()
        if self.create_subfolder.get():
            subfolder_name = self.subfolder_name_var.get()
            subfolder_name = subfolder_name.replace("{date}", time.strftime("%Y%m%d"))
            return os.path.join(base_folder, subfolder_name)
        return base_folder

    def ensure_download_folder(self):
        """确保下载文件夹存在"""
        folder = self.get_download_folder()
        if not os.path.exists(folder):
            os.makedirs(folder)
            self.log(f"创建下载文件夹: {folder}")
        return folder

    def open_playlist_url(self):
        url = self.playlist_url_var.get()
        os.system(f'open -a "Google Chrome" "{url}"')
        self.log(f"打开播放列表: {url}")

    def parse_keywords(self, keywords_str):
        """解析关键词，支持范围表达式如 101-110"""
        result = []
        for part in keywords_str.split(','):
            part = part.strip()
            if not part:
                continue
            # 检查是否是范围表达式 (如 101-110)
            if '-' in part:
                parts = part.split('-')
                if len(parts) == 2:
                    try:
                        start = int(parts[0].strip())
                        end = int(parts[1].strip())
                        if start <= end:
                            for i in range(start, end + 1):
                                result.append(str(i))
                            continue
                    except ValueError:
                        pass
            # 不是范围表达式，直接添加
            result.append(part)
        return result

    def add_download_keywords(self):
        keywords = self.download_keywords_var.get().strip()
        if not keywords:
            messagebox.showwarning("警告", "请输入关键词")
            return

        parsed = self.parse_keywords(keywords)
        added = 0
        for kw in parsed:
            if kw and kw not in [d['keyword'] for d in self.download_list]:
                self.download_list.append({
                    'keyword': kw,
                    'status': '待下载'
                })
                added += 1

        self.refresh_download_tree()
        self.log(f"添加了 {added} 个下载任务")

    def remove_download_selected(self):
        selected = self.download_tree.selection()
        if not selected:
            return
        indices = sorted([self.download_tree.index(item) for item in selected], reverse=True)
        for idx in indices:
            del self.download_list[idx]
        self.refresh_download_tree()

    def clear_download_list(self):
        if self.download_list and messagebox.askyesno("确认", "确定清空下载列表？"):
            self.download_list.clear()
            self.refresh_download_tree()

    def refresh_download_tree(self):
        self.download_tree.delete(*self.download_tree.get_children())
        for i, d in enumerate(self.download_list):
            self.download_tree.insert("", "end", values=(i+1, d['keyword'], d['status']))

    def download_select_all(self):
        for item in self.download_tree.get_children():
            self.download_tree.selection_add(item)

    def download_deselect_all(self):
        self.download_tree.selection_remove(*self.download_tree.get_children())

    def start_download(self):
        selected = self.download_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要下载的视频")
            return

        self.running = True
        self.stop_flag = False
        self.download_start_btn.configure(state="disabled")
        self.download_stop_btn.configure(state="normal")

        indices = [self.download_tree.index(item) for item in selected]
        thread = threading.Thread(target=self.download_thread, args=(indices,))
        thread.daemon = True
        thread.start()

    def download_thread(self, indices):
        items = [self.download_list[i] for i in indices]
        total = len(items)
        interval = self.download_interval.get()
        success_count = 0

        pyautogui.PAUSE = 0.3

        # 创建下载文件夹
        download_folder = self.ensure_download_folder()
        self.log(f"下载目录: {download_folder}")
        self.log(f"开始下载 {total} 个视频")
        self.log("3 秒后开始，鼠标移到左上角可中止")
        time.sleep(3)

        for i, item in enumerate(items):
            if self.stop_flag:
                self.log("已停止")
                break

            item['status'] = '下载中'
            self.root.after(0, self.refresh_download_tree)
            self.root.after(0, lambda: self.download_progress_var.set(f"进度: {i+1}/{total}"))

            try:
                self.download_single(item['keyword'])
                item['status'] = '✓ 已启动'
                success_count += 1
                self.log(f"✓ 下载已启动: {item['keyword']}")
            except Exception as e:
                item['status'] = '✗ 失败'
                self.log(f"✗ 失败: {e}")

            self.root.after(0, self.refresh_download_tree)

            if i < total - 1 and not self.stop_flag:
                self.log(f"等待 {interval} 秒...")
                time.sleep(interval)

        # 完成后显示总结
        self.log("=" * 50)
        self.log(f"✅ 下载任务完成!")
        self.log(f"   成功启动: {success_count}/{total} 个")
        self.log(f"   保存位置: {download_folder}")
        self.log("=" * 50)

        # 显示完成对话框
        self.root.after(0, lambda: self.show_download_complete(download_folder, success_count, total))

        self.root.after(0, lambda: self.download_start_btn.configure(state="normal"))
        self.root.after(0, lambda: self.download_stop_btn.configure(state="disabled"))
        self.root.after(0, lambda: self.download_progress_var.set("完成"))
        self.running = False

    def show_download_complete(self, folder, success, total):
        """显示下载完成对话框"""
        msg = f"下载任务完成!\n\n成功启动: {success}/{total} 个\n保存位置: {folder}\n\n是否打开下载文件夹？"
        if messagebox.askyesno("下载完成", msg):
            os.system(f'open "{folder}"')

    def get_download_files(self):
        """获取下载文件夹中的所有 mp4 文件"""
        import glob
        download_dir = os.path.expanduser("~/Downloads")
        return set(glob.glob(os.path.join(download_dir, "*.mp4")))

    def verify_download(self, keyword, before_files, timeout=30):
        """验收标准：检查是否有包含关键词的新文件出现"""
        self.update_download_step(f"验证下载: {keyword}...")
        for i in range(timeout):
            time.sleep(1)
            after_files = self.get_download_files()
            new_files = after_files - before_files
            # 检查新文件中是否有包含关键词的
            for f in new_files:
                if keyword in os.path.basename(f):
                    self.update_download_step(f"✓ 验收通过: {os.path.basename(f)}")
                    return True
            # 检查是否有正在下载的文件（.crdownload）
            downloading = glob.glob(os.path.join(os.path.expanduser("~/Downloads"), "*.crdownload"))
            if downloading and i < timeout - 1:
                self.update_download_step(f"下载中... ({i+1}s)")
                continue
        self.update_download_step(f"✗ 验收失败: 未找到 {keyword} 的下载文件")
        return False

    def download_single(self, keyword):
        """下载单个视频 (RPA) - 使用 hover 显示选项按钮的正确工作流"""
        self.update_download_step(f"查找: {keyword}...")

        # ========== 验收标准：记录下载前的文件 ==========
        before_files = self.get_download_files()

        # 激活 Chrome
        os.system('open -a "Google Chrome"')
        time.sleep(1)

        # 使用 Cmd+F 搜索关键词（高亮显示）
        self.update_download_step("搜索视频...")
        pyautogui.hotkey('command', 'f')
        time.sleep(0.5)
        pyperclip.copy(keyword)
        pyautogui.hotkey('command', 'v')
        time.sleep(1)

        # 获取当前高亮位置（搜索结果会高亮）
        # 按 Escape 关闭搜索框但保持高亮
        pyautogui.press('escape')
        time.sleep(0.5)

        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()

        # ========== 关键修改：正确的 hover 工作流 ==========
        # 1. 先移动到视频行的左侧（缩略图区域），触发 hover
        self.update_download_step("悬停到视频行...")

        # YouTube Studio 视频列表：缩略图通常在左侧约 300px 位置
        # 搜索后高亮的行大约在屏幕中间
        row_x = 400  # 视频行的 X 坐标（缩略图附近）
        row_y = screen_height // 2  # 大约在屏幕中间

        pyautogui.moveTo(row_x, row_y)
        time.sleep(1)  # 等待 hover 效果显示

        # 2. 保持在同一行，移动到右侧找"选项"按钮
        self.update_download_step("移动到选项按钮...")
        # 选项按钮在行的右侧，大约在屏幕宽度的 85% 位置
        options_x = int(screen_width * 0.85)

        # 缓慢移动到选项按钮位置（保持 hover 状态）
        pyautogui.moveTo(options_x, row_y, duration=0.3)
        time.sleep(0.8)

        # 3. 点击选项按钮
        self.update_download_step("点击选项按钮...")
        pyautogui.click()
        time.sleep(1)

        # 4. 在弹出菜单中找到"下载"并点击
        self.update_download_step("点击下载...")
        # 下载选项通常是菜单中的第5项（修改标题、在YouTube观看、获取链接、宣传、下载）
        # 使用键盘导航更可靠
        for _ in range(4):  # 按 4 次 down 到达"下载"
            pyautogui.press('down')
            time.sleep(0.2)
        pyautogui.press('return')
        time.sleep(3)

        # ========== 验收标准：验证下载是否成功 ==========
        return self.verify_download(keyword, before_files, timeout=60)

    def update_download_step(self, text):
        self.root.after(0, lambda: self.download_step_var.set(text))

    # ==================== 删除标签页 ====================
    def create_delete_tab(self):
        frame = self.delete_frame

        # 配置区域
        config_frame = ttk.LabelFrame(frame, text="删除配置", padding=5)
        config_frame.pack(fill="x", padx=5, pady=5)

        # 使用下载页面相同的播放列表 URL
        row1 = ttk.Frame(config_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="播放列表URL:", width=12).pack(side="left")
        self.delete_url_var = tk.StringVar(value="https://studio.youtube.com/playlist/")
        ttk.Entry(row1, textvariable=self.delete_url_var, width=60).pack(side="left", padx=5)
        ttk.Button(row1, text="打开", command=self.open_delete_url).pack(side="left")
        ttk.Button(row1, text="同步下载URL", command=self.sync_delete_url).pack(side="left", padx=5)

        # 删除间隔
        row2 = ttk.Frame(config_frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="删除间隔:", width=12).pack(side="left")
        self.delete_interval = tk.IntVar(value=3)
        ttk.Spinbox(row2, from_=1, to=30, textvariable=self.delete_interval, width=5).pack(side="left")
        ttk.Label(row2, text="秒").pack(side="left", padx=5)

        # 关键词筛选
        row3 = ttk.Frame(config_frame)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="关键词筛选:", width=12).pack(side="left")
        self.delete_keywords_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=self.delete_keywords_var, width=40).pack(side="left", padx=5)
        ttk.Label(row3, text="(多个用逗号分隔)", foreground="gray").pack(side="left")

        # 待删除列表
        list_frame = ttk.LabelFrame(frame, text="待删除视频", padding=5)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Treeview
        columns = ("idx", "name", "status")
        self.delete_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.delete_tree.heading("idx", text="#")
        self.delete_tree.heading("name", text="视频名称/关键词")
        self.delete_tree.heading("status", text="状态")
        self.delete_tree.column("idx", width=40)
        self.delete_tree.column("name", width=500)
        self.delete_tree.column("status", width=80)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.delete_tree.yview)
        self.delete_tree.configure(yscrollcommand=scroll.set)
        self.delete_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        # 按钮
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side="right", fill="y", padx=5)
        ttk.Button(btn_frame, text="添加关键词", command=self.add_delete_keywords, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="从下载复制", command=self.copy_from_download, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="删除选中", command=self.remove_delete_selected, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_delete_list, width=12).pack(pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="全选", command=self.delete_select_all, width=12).pack(pady=2)
        ttk.Button(btn_frame, text="取消选择", command=self.delete_deselect_all, width=12).pack(pady=2)

        # 进度和控制
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        self.delete_progress_var = tk.StringVar(value="就绪")
        ttk.Label(ctrl_frame, textvariable=self.delete_progress_var).pack(side="left")

        self.delete_step_var = tk.StringVar(value="")
        ttk.Label(ctrl_frame, textvariable=self.delete_step_var, foreground="red").pack(side="left", padx=20)

        self.delete_stop_btn = ttk.Button(ctrl_frame, text="⏹ 停止", command=self.stop_task, state="disabled")
        self.delete_stop_btn.pack(side="right", padx=5)

        self.delete_start_btn = ttk.Button(ctrl_frame, text="🗑️ 开始删除", command=self.start_delete)
        self.delete_start_btn.pack(side="right", padx=5)

        ttk.Button(ctrl_frame, text="📋 保存为批次", command=self.save_delete_as_batch).pack(side="right", padx=5)

        # 警告说明
        warn_frame = ttk.LabelFrame(frame, text="警告", padding=5)
        warn_frame.pack(fill="x", padx=5, pady=5)
        warn_text = """⚠️ 删除操作不可恢复！请谨慎操作！

使用流程:
1. 在浏览器中登录 YouTube Studio 并打开播放列表页面
2. 输入要删除的视频关键词（用于匹配视频标题）
3. 可从"下载视频"页面复制已下载的视频列表
4. 点击"开始删除"执行删除操作"""
        ttk.Label(warn_frame, text=warn_text, justify="left", foreground="red").pack(anchor="w")

    # 删除功能方法
    def open_delete_url(self):
        url = self.delete_url_var.get()
        os.system(f'open -a "Google Chrome" "{url}"')
        self.log(f"打开删除页面: {url}")

    def sync_delete_url(self):
        """同步下载页面的 URL"""
        self.delete_url_var.set(self.playlist_url_var.get())
        self.log("已同步下载页面的 URL")

    def add_delete_keywords(self):
        keywords = self.delete_keywords_var.get().strip()
        if not keywords:
            messagebox.showwarning("警告", "请输入关键词")
            return

        for kw in keywords.split(','):
            kw = kw.strip()
            if kw and kw not in [d['keyword'] for d in self.delete_list]:
                self.delete_list.append({
                    'keyword': kw,
                    'status': '待删除'
                })

        self.refresh_delete_tree()
        self.log(f"添加了 {len(keywords.split(','))} 个删除任务")

    def copy_from_download(self):
        """从下载列表复制"""
        if not self.download_list:
            messagebox.showinfo("提示", "下载列表为空")
            return

        added = 0
        for item in self.download_list:
            kw = item['keyword']
            if kw not in [d['keyword'] for d in self.delete_list]:
                self.delete_list.append({
                    'keyword': kw,
                    'status': '待删除'
                })
                added += 1

        self.refresh_delete_tree()
        self.log(f"从下载列表复制了 {added} 个任务")

    def remove_delete_selected(self):
        selected = self.delete_tree.selection()
        if not selected:
            return
        indices = sorted([self.delete_tree.index(item) for item in selected], reverse=True)
        for idx in indices:
            del self.delete_list[idx]
        self.refresh_delete_tree()

    def clear_delete_list(self):
        if self.delete_list and messagebox.askyesno("确认", "确定清空删除列表？"):
            self.delete_list.clear()
            self.refresh_delete_tree()

    def refresh_delete_tree(self):
        self.delete_tree.delete(*self.delete_tree.get_children())
        for i, d in enumerate(self.delete_list):
            self.delete_tree.insert("", "end", values=(i+1, d['keyword'], d['status']))

    def delete_select_all(self):
        for item in self.delete_tree.get_children():
            self.delete_tree.selection_add(item)

    def delete_deselect_all(self):
        self.delete_tree.selection_remove(*self.delete_tree.get_children())

    def start_delete(self):
        selected = self.delete_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的视频")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected)} 个视频吗？\n\n⚠️ 此操作不可恢复！"):
            return

        self.running = True
        self.stop_flag = False
        self.delete_start_btn.configure(state="disabled")
        self.delete_stop_btn.configure(state="normal")

        indices = [self.delete_tree.index(item) for item in selected]
        thread = threading.Thread(target=self.delete_thread, args=(indices,))
        thread.daemon = True
        thread.start()

    def delete_thread(self, indices):
        items = [self.delete_list[i] for i in indices]
        total = len(items)
        interval = self.delete_interval.get()
        success_count = 0

        pyautogui.PAUSE = 0.3

        self.log(f"开始删除 {total} 个视频")
        self.log("3 秒后开始，鼠标移到左上角可中止")
        time.sleep(3)

        for i, item in enumerate(items):
            if self.stop_flag:
                self.log("已停止")
                break

            item['status'] = '删除中'
            self.root.after(0, self.refresh_delete_tree)
            self.root.after(0, lambda: self.delete_progress_var.set(f"进度: {i+1}/{total}"))

            try:
                self.delete_single(item['keyword'])
                item['status'] = '✓ 已删除'
                success_count += 1
                self.log(f"✓ 已删除: {item['keyword']}")
            except Exception as e:
                item['status'] = '✗ 失败'
                self.log(f"✗ 失败: {e}")

            self.root.after(0, self.refresh_delete_tree)

            if i < total - 1 and not self.stop_flag:
                self.log(f"等待 {interval} 秒...")
                time.sleep(interval)

        self.log("=" * 50)
        self.log(f"🗑️ 删除任务完成! 成功: {success_count}/{total}")
        self.log("=" * 50)

        self.root.after(0, lambda: self.delete_start_btn.configure(state="normal"))
        self.root.after(0, lambda: self.delete_stop_btn.configure(state="disabled"))
        self.root.after(0, lambda: self.delete_progress_var.set("完成"))
        self.running = False

    def delete_single(self, keyword):
        """删除单个视频 (RPA)"""
        self.update_delete_step(f"查找: {keyword}...")

        # 激活 Chrome
        os.system('open -a "Google Chrome"')
        time.sleep(1)

        # 使用 Cmd+F 搜索
        self.update_delete_step("搜索视频...")
        pyautogui.hotkey('command', 'f')
        time.sleep(0.5)
        pyperclip.copy(keyword)
        pyautogui.hotkey('command', 'v')
        time.sleep(1)
        pyautogui.press('escape')
        time.sleep(0.5)

        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()

        # 移动到页面中间偏左的位置（视频列表区域）
        self.update_delete_step("定位视频...")
        target_x = screen_width // 3
        target_y = screen_height // 2
        pyautogui.moveTo(target_x, target_y)
        time.sleep(0.8)

        # 移动到右侧查找 Options 按钮 (⋮)
        self.update_delete_step("点击 Options...")
        pyautogui.moveTo(screen_width - 200, target_y)
        time.sleep(0.8)
        pyautogui.click()
        time.sleep(0.8)

        # 点击删除选项 (通常是菜单中的某一项)
        self.update_delete_step("选择删除...")
        # 在 YouTube Studio 中，删除通常在菜单下方
        for _ in range(5):  # 向下移动到删除选项
            pyautogui.press('down')
            time.sleep(0.2)
        pyautogui.press('return')
        time.sleep(1)

        # 确认删除对话框
        self.update_delete_step("确认删除...")
        time.sleep(1)
        pyautogui.press('tab')
        time.sleep(0.3)
        pyautogui.press('return')
        time.sleep(2)

        self.update_delete_step("已删除")

    def update_delete_step(self, text):
        self.root.after(0, lambda: self.delete_step_var.set(text))

    # ==================== 批次工作流标签页 ====================
    def create_batch_tab(self):
        frame = self.batch_frame

        # 顶部说明
        info_label = ttk.Label(frame, text="批次工作流：可以保存多个不同参数的工作流配置，按顺序执行", foreground="blue")
        info_label.pack(pady=5)

        # 主区域分为两部分：左边批次列表，右边参数编辑
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 左侧：批次列表
        list_frame = ttk.LabelFrame(main_frame, text="工作流列表", padding=5)
        list_frame.pack(side="left", fill="both", expand=True)

        columns = ("idx", "name", "type", "folder", "status")
        self.batch_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.batch_tree.heading("idx", text="#")
        self.batch_tree.heading("name", text="批次名称")
        self.batch_tree.heading("type", text="类型")
        self.batch_tree.heading("folder", text="文件夹")
        self.batch_tree.heading("status", text="状态")
        self.batch_tree.column("idx", width=30)
        self.batch_tree.column("name", width=120)
        self.batch_tree.column("type", width=60)
        self.batch_tree.column("folder", width=200)
        self.batch_tree.column("status", width=60)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.batch_tree.yview)
        self.batch_tree.configure(yscrollcommand=scroll.set)
        self.batch_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.batch_tree.bind("<<TreeviewSelect>>", self.on_batch_select)

        # 列表按钮
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(side="right", fill="y", padx=5)
        ttk.Button(list_btn_frame, text="⬆ 上移", command=self.move_batch_up, width=10).pack(pady=2)
        ttk.Button(list_btn_frame, text="⬇ 下移", command=self.move_batch_down, width=10).pack(pady=2)
        ttk.Separator(list_btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(list_btn_frame, text="删除批次", command=self.remove_batch, width=10).pack(pady=2)
        ttk.Button(list_btn_frame, text="清空全部", command=self.clear_batches, width=10).pack(pady=2)

        # 右侧：批次参数编辑
        edit_frame = ttk.LabelFrame(main_frame, text="批次参数", padding=5)
        edit_frame.pack(side="right", fill="y", padx=(5, 0))

        # 批次名称
        row1 = ttk.Frame(edit_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="批次名称:", width=10).pack(side="left")
        self.batch_name_var = tk.StringVar(value="批次1")
        ttk.Entry(row1, textvariable=self.batch_name_var, width=20).pack(side="left", padx=5)

        # 类型选择
        row2 = ttk.Frame(edit_frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="操作类型:", width=10).pack(side="left")
        self.batch_type_var = tk.StringVar(value="upload")
        ttk.Radiobutton(row2, text="上传", variable=self.batch_type_var, value="upload").pack(side="left")
        ttk.Radiobutton(row2, text="下载", variable=self.batch_type_var, value="download").pack(side="left")
        ttk.Radiobutton(row2, text="删除", variable=self.batch_type_var, value="delete").pack(side="left")

        # 视频文件夹
        row3 = ttk.Frame(edit_frame)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="视频文件夹:", width=10).pack(side="left")
        self.batch_video_folder_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=self.batch_video_folder_var, width=25).pack(side="left", padx=5)
        ttk.Button(row3, text="浏览", command=self.browse_batch_video_folder, width=5).pack(side="left")

        # 封面文件夹
        row4 = ttk.Frame(edit_frame)
        row4.pack(fill="x", pady=2)
        ttk.Label(row4, text="封面文件夹:", width=10).pack(side="left")
        self.batch_cover_folder_var = tk.StringVar(value="")
        ttk.Entry(row4, textvariable=self.batch_cover_folder_var, width=25).pack(side="left", padx=5)
        ttk.Button(row4, text="浏览", command=self.browse_batch_cover_folder, width=5).pack(side="left")

        # 封面模式
        row5 = ttk.Frame(edit_frame)
        row5.pack(fill="x", pady=2)
        ttk.Label(row5, text="封面模式:", width=10).pack(side="left")
        self.batch_cover_mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(row5, text="单封面", variable=self.batch_cover_mode_var, value="single").pack(side="left")
        ttk.Radiobutton(row5, text="顺序", variable=self.batch_cover_mode_var, value="order").pack(side="left")
        ttk.Radiobutton(row5, text="分组", variable=self.batch_cover_mode_var, value="group").pack(side="left")

        # 分组设置
        row6 = ttk.Frame(edit_frame)
        row6.pack(fill="x", pady=2)
        ttk.Label(row6, text="分组设置:", width=10).pack(side="left")
        self.batch_group_var = tk.StringVar(value="3,1,2")
        ttk.Entry(row6, textvariable=self.batch_group_var, width=20).pack(side="left", padx=5)
        ttk.Label(row6, text="(如: 3,1,2)", foreground="gray").pack(side="left")

        # 关键词（用于下载/删除）
        row7 = ttk.Frame(edit_frame)
        row7.pack(fill="x", pady=2)
        ttk.Label(row7, text="关键词:", width=10).pack(side="left")
        self.batch_keywords_var = tk.StringVar(value="")
        ttk.Entry(row7, textvariable=self.batch_keywords_var, width=30).pack(side="left", padx=5)

        # 间隔
        row8 = ttk.Frame(edit_frame)
        row8.pack(fill="x", pady=2)
        ttk.Label(row8, text="间隔(秒):", width=10).pack(side="left")
        self.batch_interval_var = tk.IntVar(value=5)
        ttk.Spinbox(row8, from_=1, to=600, textvariable=self.batch_interval_var, width=10).pack(side="left", padx=5)

        # 添加/更新按钮
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="添加批次", command=self.add_batch).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="更新选中", command=self.update_batch).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="从当前复制", command=self.copy_current_settings).pack(side="left", padx=5)

        # 底部控制
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        self.batch_progress_var = tk.StringVar(value="就绪")
        ttk.Label(ctrl_frame, textvariable=self.batch_progress_var).pack(side="left")

        self.batch_step_var = tk.StringVar(value="")
        ttk.Label(ctrl_frame, textvariable=self.batch_step_var, foreground="green").pack(side="left", padx=20)

        self.batch_stop_btn = ttk.Button(ctrl_frame, text="⏹ 停止", command=self.stop_task, state="disabled")
        self.batch_stop_btn.pack(side="right", padx=5)

        self.batch_start_btn = ttk.Button(ctrl_frame, text="▶ 执行全部批次", command=self.start_batch_workflow)
        self.batch_start_btn.pack(side="right", padx=5)

        ttk.Button(ctrl_frame, text="保存工作流", command=self.save_batch_workflows).pack(side="right", padx=5)
        ttk.Button(ctrl_frame, text="加载工作流", command=self.load_batch_workflows).pack(side="right", padx=5)

        # 加载已保存的工作流
        self.load_batch_workflows_silent()

    # 批次工作流方法
    def browse_batch_video_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.batch_video_folder_var.set(folder)

    def browse_batch_cover_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.batch_cover_folder_var.set(folder)

    def copy_current_settings(self):
        """从当前上传页面复制设置"""
        self.batch_video_folder_var.set(self.upload_folder_var.get())
        self.batch_cover_folder_var.set(self.cover_folder_var.get())
        self.batch_cover_mode_var.set(self.cover_mode.get())
        self.batch_group_var.set(self.group_var.get())
        interval = self.interval_min.get() * 60 + self.interval_sec.get()
        self.batch_interval_var.set(interval)
        self.log("已从上传页面复制设置")

    def add_batch(self):
        """添加新批次"""
        batch = {
            'name': self.batch_name_var.get(),
            'type': self.batch_type_var.get(),
            'video_folder': self.batch_video_folder_var.get(),
            'cover_folder': self.batch_cover_folder_var.get(),
            'cover_mode': self.batch_cover_mode_var.get(),
            'group_pattern': self.batch_group_var.get(),
            'keywords': self.batch_keywords_var.get(),
            'interval': self.batch_interval_var.get(),
            'status': '待执行'
        }
        self.batch_list.append(batch)
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()  # 自动保存
        self.log(f"添加批次: {batch['name']} (已自动保存)")

    def update_batch(self):
        """更新选中的批次"""
        selected = self.batch_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要更新的批次")
            return

        idx = self.batch_tree.index(selected[0])
        self.batch_list[idx] = {
            'name': self.batch_name_var.get(),
            'type': self.batch_type_var.get(),
            'video_folder': self.batch_video_folder_var.get(),
            'cover_folder': self.batch_cover_folder_var.get(),
            'cover_mode': self.batch_cover_mode_var.get(),
            'group_pattern': self.batch_group_var.get(),
            'keywords': self.batch_keywords_var.get(),
            'interval': self.batch_interval_var.get(),
            'status': '待执行'
        }
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()  # 自动保存
        self.log(f"更新批次: {self.batch_name_var.get()} (已自动保存)")

    def on_batch_select(self, event):
        """选择批次时加载参数"""
        selected = self.batch_tree.selection()
        if not selected:
            return

        idx = self.batch_tree.index(selected[0])
        batch = self.batch_list[idx]

        self.batch_name_var.set(batch['name'])
        self.batch_type_var.set(batch['type'])
        self.batch_video_folder_var.set(batch.get('video_folder', ''))
        self.batch_cover_folder_var.set(batch.get('cover_folder', ''))
        self.batch_cover_mode_var.set(batch.get('cover_mode', 'single'))
        self.batch_group_var.set(batch.get('group_pattern', ''))
        self.batch_keywords_var.set(batch.get('keywords', ''))
        self.batch_interval_var.set(batch.get('interval', 5))

    def move_batch_up(self):
        selected = self.batch_tree.selection()
        if not selected:
            return
        idx = self.batch_tree.index(selected[0])
        if idx == 0:
            return
        self.batch_list[idx], self.batch_list[idx-1] = self.batch_list[idx-1], self.batch_list[idx]
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()  # 自动保存
        items = self.batch_tree.get_children()
        if idx-1 < len(items):
            self.batch_tree.selection_set(items[idx-1])

    def move_batch_down(self):
        selected = self.batch_tree.selection()
        if not selected:
            return
        idx = self.batch_tree.index(selected[0])
        if idx >= len(self.batch_list) - 1:
            return
        self.batch_list[idx], self.batch_list[idx+1] = self.batch_list[idx+1], self.batch_list[idx]
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()  # 自动保存
        items = self.batch_tree.get_children()
        if idx+1 < len(items):
            self.batch_tree.selection_set(items[idx+1])

    def remove_batch(self):
        selected = self.batch_tree.selection()
        if not selected:
            return
        idx = self.batch_tree.index(selected[0])
        del self.batch_list[idx]
        self.refresh_batch_tree()
        self.save_batch_workflows_silent()  # 自动保存

    def clear_batches(self):
        if self.batch_list and messagebox.askyesno("确认", "确定清空所有批次？"):
            self.batch_list.clear()
            self.refresh_batch_tree()
            self.save_batch_workflows_silent()  # 自动保存

    def refresh_batch_tree(self):
        self.batch_tree.delete(*self.batch_tree.get_children())
        type_names = {'upload': '上传', 'download': '下载', 'delete': '删除'}
        for i, b in enumerate(self.batch_list):
            # 显示具体内容
            if b['type'] == 'upload':
                if 'videos' in b:
                    count = len(b['videos'])
                    content = f"{count} 个视频"
                else:
                    content = b.get('video_folder', '')[:25]
            else:
                if 'keywords_list' in b:
                    count = len(b['keywords_list'])
                    content = f"{count} 个关键词"
                else:
                    content = b.get('keywords', '')[:25]

            self.batch_tree.insert("", "end", values=(
                i+1,
                b['name'],
                type_names.get(b['type'], b['type']),
                content,
                b.get('status', '待执行')
            ))

    def save_batch_workflows(self):
        """保存工作流到文件"""
        try:
            with open(BATCH_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.batch_list, f, ensure_ascii=False, indent=2)
            self.log(f"已保存 {len(self.batch_list)} 个批次工作流")
        except Exception as e:
            self.log(f"保存失败: {e}")

    def load_batch_workflows(self):
        """从文件加载工作流"""
        if not os.path.exists(BATCH_FILE):
            messagebox.showinfo("提示", "没有保存的工作流")
            return

        try:
            with open(BATCH_FILE, 'r', encoding='utf-8') as f:
                self.batch_list = json.load(f)
            self.refresh_batch_tree()
            self.log(f"已加载 {len(self.batch_list)} 个批次工作流")
        except Exception as e:
            self.log(f"加载失败: {e}")

    def load_batch_workflows_silent(self):
        """静默加载工作流（启动时）"""
        if os.path.exists(BATCH_FILE):
            try:
                with open(BATCH_FILE, 'r', encoding='utf-8') as f:
                    self.batch_list = json.load(f)
                self.refresh_batch_tree()
            except:
                pass

    def save_batch_workflows_silent(self):
        """静默保存工作流（自动保存）"""
        try:
            with open(BATCH_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.batch_list, f, ensure_ascii=False, indent=2)
        except:
            pass

    def start_batch_workflow(self):
        """执行所有批次工作流"""
        if not self.batch_list:
            messagebox.showwarning("警告", "没有要执行的批次")
            return

        if not messagebox.askyesno("确认", f"确定要执行 {len(self.batch_list)} 个批次工作流吗？"):
            return

        self.running = True
        self.stop_flag = False
        self.batch_start_btn.configure(state="disabled")
        self.batch_stop_btn.configure(state="normal")

        thread = threading.Thread(target=self.batch_workflow_thread)
        thread.daemon = True
        thread.start()

    def batch_workflow_thread(self):
        """批次工作流执行线程"""
        total = len(self.batch_list)

        for i, batch in enumerate(self.batch_list):
            if self.stop_flag:
                self.log("批次工作流已停止")
                break

            batch['status'] = '执行中'
            self.root.after(0, self.refresh_batch_tree)
            self.root.after(0, lambda b=batch: self.batch_progress_var.set(f"执行批次 {i+1}/{total}: {b['name']}"))
            self.root.after(0, lambda b=batch: self.batch_step_var.set(f"类型: {b['type']}"))

            self.log(f"=" * 50)
            self.log(f"执行批次 {i+1}/{total}: {batch['name']} ({batch['type']})")

            try:
                if batch['type'] == 'upload':
                    self.execute_upload_batch(batch)
                elif batch['type'] == 'download':
                    self.execute_download_batch(batch)
                elif batch['type'] == 'delete':
                    self.execute_delete_batch(batch)

                batch['status'] = '✓ 完成'
                self.log(f"✓ 批次完成: {batch['name']}")
            except Exception as e:
                batch['status'] = '✗ 失败'
                self.log(f"✗ 批次失败: {e}")

            self.root.after(0, self.refresh_batch_tree)

            # 批次间等待
            if i < total - 1 and not self.stop_flag:
                self.log("批次间等待 10 秒...")
                time.sleep(10)

        self.log("=" * 50)
        self.log("✅ 所有批次工作流执行完成")

        self.root.after(0, lambda: self.batch_start_btn.configure(state="normal"))
        self.root.after(0, lambda: self.batch_stop_btn.configure(state="disabled"))
        self.root.after(0, lambda: self.batch_progress_var.set("完成"))
        self.root.after(0, lambda: self.batch_step_var.set(""))
        self.running = False

    def execute_upload_batch(self, batch):
        """执行上传批次"""
        # 优先使用保存的视频列表
        if 'videos' in batch and batch['videos']:
            video_list = batch['videos']
        else:
            # 兼容旧格式：从文件夹加载
            folder = batch.get('video_folder', '')
            if not folder or not os.path.exists(folder):
                raise Exception(f"视频文件夹不存在: {folder}")

            videos = sorted([f for f in os.listdir(folder) if f.lower().endswith('.mp4')])
            if not videos:
                raise Exception("文件夹中没有视频")

            # 加载封面
            cover_folder = batch.get('cover_folder', '')
            covers = []
            if cover_folder and os.path.exists(cover_folder):
                covers = sorted([os.path.join(cover_folder, f) for f in os.listdir(cover_folder)
                               if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])

            # 构建视频列表
            video_list = []
            for v in videos:
                video_list.append({
                    'path': os.path.join(folder, v),
                    'name': v.rsplit('.', 1)[0],
                    'cover': None,
                    'status': '待上传'
                })

            # 分配封面
            cover_mode = batch.get('cover_mode', 'single')
            if covers:
                if cover_mode == 'single':
                    for video in video_list:
                        video['cover'] = covers[0]
                elif cover_mode == 'order':
                    for i, video in enumerate(video_list):
                        if i < len(covers):
                            video['cover'] = covers[i]
                elif cover_mode == 'group':
                    try:
                        groups = [int(x.strip()) for x in batch.get('group_pattern', '').split(',') if x.strip()]
                        video_idx = 0
                        for cover_idx, count in enumerate(groups):
                            if cover_idx >= len(covers):
                                break
                            for _ in range(count):
                                if video_idx < len(video_list):
                                    video_list[video_idx]['cover'] = covers[cover_idx]
                                    video_idx += 1
                    except:
                        pass

        # 上传视频
        interval = batch.get('interval', 5)
        for i, video in enumerate(video_list):
            if self.stop_flag:
                break

            self.log(f"  上传 {i+1}/{len(video_list)}: {video['name'][:40]}...")
            try:
                self.upload_single(video)
                self.log(f"  ✓ 完成")
            except Exception as e:
                self.log(f"  ✗ 失败: {e}")

            if i < len(video_list) - 1:
                time.sleep(interval)

    def execute_download_batch(self, batch):
        """执行下载批次"""
        # 优先使用保存的关键词列表
        if 'keywords_list' in batch and batch['keywords_list']:
            keyword_list = batch['keywords_list']
        else:
            # 兼容旧格式：从逗号分隔的字符串解析
            keywords = batch.get('keywords', '')
            if not keywords:
                raise Exception("没有指定下载关键词")
            keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        if not keyword_list:
            raise Exception("没有指定下载关键词")

        interval = batch.get('interval', 3)

        for i, kw in enumerate(keyword_list):
            if self.stop_flag:
                break

            self.log(f"  下载 {i+1}/{len(keyword_list)}: {kw}...")
            try:
                self.download_single(kw)
                self.log(f"  ✓ 下载已启动")
            except Exception as e:
                self.log(f"  ✗ 失败: {e}")

            if i < len(keyword_list) - 1:
                time.sleep(interval)

    def execute_delete_batch(self, batch):
        """执行删除批次"""
        # 优先使用保存的关键词列表
        if 'keywords_list' in batch and batch['keywords_list']:
            keyword_list = batch['keywords_list']
        else:
            # 兼容旧格式：从逗号分隔的字符串解析
            keywords = batch.get('keywords', '')
            if not keywords:
                raise Exception("没有指定删除关键词")
            keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]

        if not keyword_list:
            raise Exception("没有指定删除关键词")

        interval = batch.get('interval', 3)

        for i, kw in enumerate(keyword_list):
            if self.stop_flag:
                break

            self.log(f"  删除 {i+1}/{len(keyword_list)}: {kw}...")
            try:
                self.delete_single(kw)
                self.log(f"  ✓ 已删除")
            except Exception as e:
                self.log(f"  ✗ 失败: {e}")

            if i < len(keyword_list) - 1:
                time.sleep(interval)

    # ==================== 共享功能 ====================
    def stop_task(self):
        self.stop_flag = True
        self.log("正在停止...")

    def log(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")


def parse_range(range_str):
    """解析范围字符串，如 '101-110' -> ['101', '102', ..., '110']"""
    result = []
    for part in range_str.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            parts = part.split('-')
            if len(parts) == 2:
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    for i in range(start, end + 1):
                        result.append(str(i))
                    continue
                except ValueError:
                    pass
        result.append(part)
    return result


def get_download_files_cli():
    """获取下载文件夹中的所有 mp4 文件"""
    import glob
    download_dir = os.path.expanduser("~/Downloads")
    return set(glob.glob(os.path.join(download_dir, "*.mp4")))


def verify_download_cli(keyword, before_files, timeout=60):
    """验收标准：检查是否有包含关键词的新文件出现"""
    import glob
    print(f"  验证下载中...")
    for i in range(timeout):
        time.sleep(1)
        after_files = get_download_files_cli()
        new_files = after_files - before_files
        # 检查新文件中是否有包含关键词的
        for f in new_files:
            if keyword in os.path.basename(f):
                print(f"  ✓ 验收通过: {os.path.basename(f)}")
                return True
        # 检查是否有正在下载的文件（.crdownload）
        downloading = glob.glob(os.path.join(os.path.expanduser("~/Downloads"), "*.crdownload"))
        if downloading:
            if i % 5 == 0:  # 每5秒报告一次
                print(f"  下载中... ({i+1}s)")
            continue
    print(f"  ✗ 验收失败: 未找到 {keyword} 的下载文件")
    return False


def cli_download(url, keywords, interval=3):
    """CLI 模式下载 - 带验收标准"""
    print(f"=" * 50)
    print(f"YouTube 下载工具 (CLI 模式) - 带验收")
    print(f"=" * 50)
    print(f"播放列表: {url}")
    print(f"关键词: {keywords}")
    print(f"间隔: {interval} 秒")
    print(f"=" * 50)

    keyword_list = parse_range(keywords)
    print(f"待下载: {len(keyword_list)} 个视频")
    print(f"  {', '.join(keyword_list[:5])}{'...' if len(keyword_list) > 5 else ''}")
    print(f"=" * 50)

    # 打开播放列表
    print("打开播放列表...")
    os.system(f'open -a "Google Chrome" "{url}"')
    time.sleep(5)

    pyautogui.PAUSE = 0.3
    pyautogui.FAILSAFE = True

    print("3 秒后开始，鼠标移到左上角可中止")
    time.sleep(3)

    success_count = 0
    failed_list = []

    for i, keyword in enumerate(keyword_list):
        print(f"\n[{i+1}/{len(keyword_list)}] 下载: {keyword}")

        # ========== 验收标准：记录下载前的文件 ==========
        before_files = get_download_files_cli()

        try:
            # 激活 Chrome
            os.system('open -a "Google Chrome"')
            time.sleep(1)

            # Cmd+F 搜索
            print(f"  搜索中...")
            pyautogui.hotkey('command', 'f')
            time.sleep(0.5)
            pyperclip.copy(keyword)
            pyautogui.hotkey('command', 'v')
            time.sleep(1)
            pyautogui.press('escape')
            time.sleep(0.5)

            # ========== 正确的 hover 工作流 ==========
            screen_width, screen_height = pyautogui.size()

            # 1. 先 hover 到视频行左侧（缩略图区域）
            print(f"  悬停到视频行...")
            row_x = 400
            row_y = screen_height // 2
            pyautogui.moveTo(row_x, row_y)
            time.sleep(1)

            # 2. 缓慢移动到右侧的选项按钮（保持 hover 状态）
            print(f"  移动到选项按钮...")
            options_x = int(screen_width * 0.85)
            pyautogui.moveTo(options_x, row_y, duration=0.3)
            time.sleep(0.8)

            # 3. 点击选项按钮
            print(f"  点击选项...")
            pyautogui.click()
            time.sleep(1)

            # 4. 在菜单中导航到"下载"（第5项）
            print(f"  点击下载...")
            for _ in range(4):
                pyautogui.press('down')
                time.sleep(0.2)
            pyautogui.press('return')
            time.sleep(3)

            # ========== 验收标准：验证下载是否成功 ==========
            if verify_download_cli(keyword, before_files, timeout=60):
                success_count += 1
            else:
                failed_list.append(keyword)

        except Exception as e:
            print(f"  ✗ 异常: {e}")
            failed_list.append(keyword)

        if i < len(keyword_list) - 1:
            print(f"  等待 {interval} 秒...")
            time.sleep(interval)

    # ========== 最终报告 ==========
    print(f"\n" + "=" * 50)
    print(f"下载任务完成!")
    print(f"成功: {success_count}/{len(keyword_list)}")
    if failed_list:
        print(f"失败: {', '.join(failed_list)}")
    print(f"=" * 50)


def main():
    parser = argparse.ArgumentParser(description='YouTube 视频管理工具')
    subparsers = parser.add_subparsers(dest='command', help='操作类型')

    # 下载命令
    download_parser = subparsers.add_parser('download', help='下载视频')
    download_parser.add_argument('--url', required=True, help='播放列表 URL')
    download_parser.add_argument('--keywords', required=True, help='关键词 (如: 101-110 或 1,2,3)')
    download_parser.add_argument('--interval', type=int, default=3, help='下载间隔(秒)')

    # 上传命令 (预留)
    upload_parser = subparsers.add_parser('upload', help='上传视频')
    upload_parser.add_argument('--folder', required=True, help='视频文件夹')
    upload_parser.add_argument('--range', help='上传范围 (如: 1-10)')
    upload_parser.add_argument('--interval', type=int, default=300, help='上传间隔(秒)')

    args = parser.parse_args()

    if args.command == 'download':
        cli_download(args.url, args.keywords, args.interval)
    elif args.command == 'upload':
        print("上传功能 CLI 模式开发中...")
    else:
        # 无参数时启动 GUI
        root = tk.Tk()
        app = YouTubeToolGUI(root)
        root.mainloop()


if __name__ == '__main__':
    main()
