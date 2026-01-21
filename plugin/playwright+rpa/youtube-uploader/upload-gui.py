#!/usr/bin/env python3
"""
upload-gui.py - 带 GUI 界面的 YouTube 上传工具
"""

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

# 进度保存文件
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), '.upload_progress.json')

class YouTubeUploaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 视频上传工具")
        self.root.geometry("950x750")

        self.uploading = False
        self.stop_flag = False
        self.video_list = []  # 存储视频信息 [{path, name, cover}, ...]
        self.cover_list = []  # 封面文件列表
        self.cover_image = None  # 保持封面图片引用
        self.cover_photo = None  # PhotoImage 引用

        self.create_widgets()

    def create_widgets(self):
        # 配置区域
        config_frame = ttk.LabelFrame(self.root, text="配置", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # 视频文件夹
        ttk.Label(config_frame, text="视频文件夹:").grid(row=0, column=0, sticky="w")
        self.folder_var = tk.StringVar(value="/Users/su/Downloads/民间故事2")
        folder_entry = ttk.Entry(config_frame, textvariable=self.folder_var, width=45)
        folder_entry.grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="浏览", command=self.browse_folder).grid(row=0, column=2)

        # 封面文件夹
        ttk.Label(config_frame, text="封面文件夹:").grid(row=1, column=0, sticky="w", pady=5)
        self.cover_folder_var = tk.StringVar(value="")
        cover_entry = ttk.Entry(config_frame, textvariable=self.cover_folder_var, width=45)
        cover_entry.grid(row=1, column=1, padx=5)
        ttk.Button(config_frame, text="浏览", command=self.browse_cover_folder).grid(row=1, column=2)
        ttk.Label(config_frame, text="(封面文件名需与视频同名，如 video.jpg)", foreground="gray").grid(row=2, column=1, sticky="w")

        # 延迟设置
        delay_frame = ttk.Frame(config_frame)
        delay_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)

        ttk.Label(delay_frame, text="操作延迟:").pack(side="left")
        self.delay_var = tk.DoubleVar(value=0.3)
        ttk.Spinbox(delay_frame, from_=0.1, to=2.0, increment=0.1,
                   textvariable=self.delay_var, width=5).pack(side="left", padx=5)
        ttk.Label(delay_frame, text="秒").pack(side="left")

        # 上传间隔设置
        interval_frame = ttk.LabelFrame(config_frame, text="上传间隔", padding=5)
        interval_frame.grid(row=4, column=0, columnspan=3, sticky="w", pady=5)

        # 间隔模式选择
        self.interval_mode = tk.StringVar(value="fixed")
        ttk.Radiobutton(interval_frame, text="固定时间", variable=self.interval_mode,
                       value="fixed", command=self.update_interval_ui).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(interval_frame, text="随机时间", variable=self.interval_mode,
                       value="random", command=self.update_interval_ui).grid(row=0, column=1, padx=5)

        # 固定时间设置 (mm:ss 格式)
        self.fixed_frame = ttk.Frame(interval_frame)
        self.fixed_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=5)
        ttk.Label(self.fixed_frame, text="间隔:").pack(side="left")
        self.interval_min_fixed = tk.IntVar(value=5)
        ttk.Spinbox(self.fixed_frame, from_=0, to=60, increment=1,
                   textvariable=self.interval_min_fixed, width=3).pack(side="left", padx=2)
        ttk.Label(self.fixed_frame, text=":").pack(side="left")
        self.interval_sec_fixed = tk.IntVar(value=0)
        ttk.Spinbox(self.fixed_frame, from_=0, to=59, increment=5,
                   textvariable=self.interval_sec_fixed, width=3).pack(side="left", padx=2)
        ttk.Label(self.fixed_frame, text="(分:秒)").pack(side="left", padx=5)

        # 随机时间设置 (mm:ss 格式)
        self.random_frame = ttk.Frame(interval_frame)
        self.random_frame.grid(row=2, column=0, columnspan=4, sticky="w", pady=5)
        ttk.Label(self.random_frame, text="最小:").pack(side="left")
        self.interval_min_rand_min = tk.IntVar(value=3)
        ttk.Spinbox(self.random_frame, from_=0, to=60, increment=1,
                   textvariable=self.interval_min_rand_min, width=3).pack(side="left", padx=2)
        ttk.Label(self.random_frame, text=":").pack(side="left")
        self.interval_sec_rand_min = tk.IntVar(value=0)
        ttk.Spinbox(self.random_frame, from_=0, to=59, increment=5,
                   textvariable=self.interval_sec_rand_min, width=3).pack(side="left", padx=2)

        ttk.Label(self.random_frame, text="  最大:").pack(side="left")
        self.interval_min_rand_max = tk.IntVar(value=10)
        ttk.Spinbox(self.random_frame, from_=0, to=60, increment=1,
                   textvariable=self.interval_min_rand_max, width=3).pack(side="left", padx=2)
        ttk.Label(self.random_frame, text=":").pack(side="left")
        self.interval_sec_rand_max = tk.IntVar(value=0)
        ttk.Spinbox(self.random_frame, from_=0, to=59, increment=5,
                   textvariable=self.interval_sec_rand_max, width=3).pack(side="left", padx=2)
        ttk.Label(self.random_frame, text="(分:秒)").pack(side="left", padx=5)

        # 初始隐藏随机设置
        self.random_frame.grid_remove()

        # 其他选项
        options_frame = ttk.LabelFrame(config_frame, text="上传选项", padding=5)
        options_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=5)

        # 播放列表选项
        ttk.Label(options_frame, text="播放列表:").grid(row=0, column=0, sticky="w")
        self.playlist_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="添加到播放列表", variable=self.playlist_enabled,
                       command=self.toggle_playlist).grid(row=0, column=1, sticky="w")
        self.playlist_var = tk.StringVar(value="")
        self.playlist_entry = ttk.Entry(options_frame, textvariable=self.playlist_var, width=20, state="disabled")
        self.playlist_entry.grid(row=0, column=2, padx=5)

        # 盈利选项
        ttk.Label(options_frame, text="盈利模式:").grid(row=1, column=0, sticky="w", pady=5)
        self.monetization_var = tk.StringVar(value="none")
        ttk.Radiobutton(options_frame, text="不设置", variable=self.monetization_var, value="none").grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(options_frame, text="开启盈利", variable=self.monetization_var, value="on").grid(row=1, column=2, sticky="w")
        ttk.Radiobutton(options_frame, text="关闭盈利", variable=self.monetization_var, value="off").grid(row=1, column=3, sticky="w")

        # 视频列表和预览区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 左侧：视频列表
        list_frame = ttk.LabelFrame(main_frame, text="待上传视频", padding=10)
        list_frame.pack(side="left", fill="both", expand=True)

        # 视频列表 - 使用 Treeview 显示更多信息
        columns = ("name", "cover", "status")
        self.video_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.video_tree.heading("name", text="视频名称")
        self.video_tree.heading("cover", text="封面")
        self.video_tree.heading("status", text="状态")
        self.video_tree.column("name", width=300)
        self.video_tree.column("cover", width=80)
        self.video_tree.column("status", width=80)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        self.video_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        # 绑定选择事件以预览封面
        self.video_tree.bind("<<TreeviewSelect>>", self.on_video_select)

        # 列表操作按钮
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side="right", padx=5, fill="y")

        ttk.Button(btn_frame, text="添加视频", command=self.add_videos, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="删除选中", command=self.remove_selected, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_videos, width=10).pack(pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="⬆ 上移", command=self.move_up, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="⬇ 下移", command=self.move_down, width=10).pack(pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="从文件夹加载", command=self.refresh_videos, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="全选", command=self.select_all, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="取消选择", command=self.deselect_all, width=10).pack(pady=2)

        # 右侧：封面管理
        preview_frame = ttk.LabelFrame(main_frame, text="封面管理", padding=10)
        preview_frame.pack(side="right", fill="both", padx=(5, 0))

        # 封面列表
        ttk.Label(preview_frame, text="封面列表 (按顺序匹配视频):").pack(anchor="w")
        self.cover_tree = ttk.Treeview(preview_frame, columns=("name",), show="headings", height=6)
        self.cover_tree.heading("name", text="封面文件")
        self.cover_tree.column("name", width=180)
        cover_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.cover_tree.yview)
        self.cover_tree.configure(yscrollcommand=cover_scroll.set)
        self.cover_tree.pack(side="left", fill="both", expand=True)
        cover_scroll.pack(side="left", fill="y")
        self.cover_tree.bind("<<TreeviewSelect>>", self.on_cover_select)

        # 封面操作按钮
        cover_btn_frame = ttk.Frame(preview_frame)
        cover_btn_frame.pack(side="right", fill="y", padx=5)
        ttk.Button(cover_btn_frame, text="⬆", command=self.move_cover_up, width=3).pack(pady=2)
        ttk.Button(cover_btn_frame, text="⬇", command=self.move_cover_down, width=3).pack(pady=2)

        # 封面预览区
        preview_img_frame = ttk.Frame(self.root)
        preview_img_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(preview_img_frame, text="预览:").pack(side="left")
        self.cover_label = ttk.Label(preview_img_frame, text="[选择封面查看]", anchor="center")
        self.cover_label.pack(side="left", padx=10)
        self.cover_info = ttk.Label(preview_img_frame, text="", wraplength=300)
        self.cover_info.pack(side="left", padx=10)

        # 匹配说明
        self.match_info = ttk.Label(preview_img_frame, text="", foreground="blue")
        self.match_info.pack(side="right", padx=10)

        # 进度区域
        progress_frame = ttk.LabelFrame(self.root, text="进度", padding=10)
        progress_frame.pack(fill="x", padx=10, pady=5)

        # 进度信息行
        progress_info = ttk.Frame(progress_frame)
        progress_info.pack(fill="x")

        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(progress_info, textvariable=self.progress_var).pack(side="left")

        # 当前步骤
        self.step_var = tk.StringVar(value="")
        ttk.Label(progress_info, textvariable=self.step_var, foreground="green").pack(side="right")

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)

        # 当前视频
        self.current_var = tk.StringVar(value="")
        ttk.Label(progress_frame, textvariable=self.current_var, foreground="blue").pack(anchor="w")

        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="日志", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True)

        # 控制按钮
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ttk.Button(control_frame, text="▶ 开始上传", command=self.start_upload)
        self.start_btn.pack(side="left", padx=5)

        self.resume_btn = ttk.Button(control_frame, text="▶ 继续未完成", command=self.resume_upload, state="disabled")
        self.resume_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(control_frame, text="⏹ 停止", command=self.stop_upload, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        ttk.Button(control_frame, text="清除进度", command=self.clear_progress).pack(side="right", padx=5)
        ttk.Button(control_frame, text="清空日志", command=self.clear_log).pack(side="right", padx=5)

        # 初始加载视频列表
        self.refresh_videos()

        # 检查是否有未完成的进度
        self.check_saved_progress()

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

    def browse_cover_folder(self):
        folder = filedialog.askdirectory(initialdir=self.cover_folder_var.get() or self.folder_var.get())
        if folder:
            self.cover_folder_var.set(folder)
            self.load_covers_from_folder(folder)

    def load_covers_from_folder(self, folder):
        """从文件夹加载所有封面"""
        self.cover_list = []
        if not os.path.exists(folder):
            return

        # 获取所有图片文件并排序
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                self.cover_list.append(os.path.join(folder, f))

        self.refresh_cover_tree()
        self.assign_covers_to_videos()
        self.log(f"加载了 {len(self.cover_list)} 个封面")

    def refresh_cover_tree(self):
        """刷新封面列表显示"""
        self.cover_tree.delete(*self.cover_tree.get_children())
        for i, cover_path in enumerate(self.cover_list):
            name = os.path.basename(cover_path)
            self.cover_tree.insert("", "end", values=(f"{i+1}. {name}",))

        # 更新匹配信息
        if len(self.cover_list) == 0:
            self.match_info.configure(text="无封面")
        elif len(self.cover_list) == 1:
            self.match_info.configure(text="单封面模式: 所有视频使用同一封面")
        else:
            self.match_info.configure(text=f"多封面模式: {len(self.cover_list)} 封面按顺序匹配视频")

    def assign_covers_to_videos(self):
        """将封面分配给视频"""
        if not self.cover_list:
            # 无封面
            for video in self.video_list:
                video['cover'] = None
        elif len(self.cover_list) == 1:
            # 单封面：所有视频用同一个
            for video in self.video_list:
                video['cover'] = self.cover_list[0]
        else:
            # 多封面：按顺序匹配
            for i, video in enumerate(self.video_list):
                if i < len(self.cover_list):
                    video['cover'] = self.cover_list[i]
                else:
                    video['cover'] = None  # 超出封面数量的视频无封面

        self.refresh_tree()

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
            img.thumbnail((120, 90), Image.Resampling.LANCZOS)
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

    def toggle_playlist(self):
        """切换播放列表输入框状态"""
        if self.playlist_enabled.get():
            self.playlist_entry.configure(state="normal")
        else:
            self.playlist_entry.configure(state="disabled")

    def update_step(self, step_text):
        """更新当前步骤显示"""
        self.root.after(0, lambda: self.step_var.set(step_text))

    def update_interval_ui(self):
        """切换固定/随机间隔显示"""
        if self.interval_mode.get() == "fixed":
            self.fixed_frame.grid()
            self.random_frame.grid_remove()
        else:
            self.fixed_frame.grid_remove()
            self.random_frame.grid()

    def get_interval(self):
        """获取间隔时间（秒）"""
        if self.interval_mode.get() == "fixed":
            # 固定时间：分钟 * 60 + 秒
            return self.interval_min_fixed.get() * 60 + self.interval_sec_fixed.get()
        else:
            # 随机时间
            min_seconds = self.interval_min_rand_min.get() * 60 + self.interval_sec_rand_min.get()
            max_seconds = self.interval_min_rand_max.get() * 60 + self.interval_sec_rand_max.get()
            if min_seconds > max_seconds:
                min_seconds, max_seconds = max_seconds, min_seconds
            return random.randint(min_seconds, max_seconds)

    def format_interval(self, seconds):
        """格式化间隔时间显示 (mm:ss)"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def add_videos(self):
        """手动添加视频文件"""
        files = filedialog.askopenfilenames(
            title="选择视频文件",
            initialdir=self.folder_var.get(),
            filetypes=[("MP4 文件", "*.mp4"), ("所有视频", "*.mp4 *.mov *.avi *.mkv"), ("所有文件", "*.*")]
        )
        added = 0
        for f in files:
            if f not in [v['path'] for v in self.video_list]:
                video_info = {
                    'path': f,
                    'name': os.path.basename(f).rsplit('.', 1)[0],
                    'cover': None,
                    'status': '待上传'
                }
                self.video_list.append(video_info)
                added += 1
        # 重新分配封面
        self.assign_covers_to_videos()
        self.log(f"添加了 {added} 个视频")

    def remove_selected(self):
        """删除选中的视频"""
        selected = self.video_tree.selection()
        if not selected:
            return
        # 获取选中项的索引并删除
        indices_to_remove = []
        for item in selected:
            idx = self.video_tree.index(item)
            indices_to_remove.append(idx)
        # 从后往前删除，避免索引变化
        for idx in sorted(indices_to_remove, reverse=True):
            del self.video_list[idx]
        self.refresh_tree()
        self.log(f"删除了 {len(selected)} 个视频")

    def clear_videos(self):
        """清空视频列表"""
        if self.video_list and messagebox.askyesno("确认", "确定要清空所有视频吗？"):
            self.video_list.clear()
            self.refresh_tree()
            self.log("已清空视频列表")

    def refresh_videos(self):
        """从文件夹加载视频"""
        folder = self.folder_var.get()
        if not os.path.exists(folder):
            messagebox.showerror("错误", f"文件夹不存在: {folder}")
            return

        videos = sorted([f for f in os.listdir(folder) if f.lower().endswith('.mp4')])
        self.video_list.clear()

        for v in videos:
            video_path = os.path.join(folder, v)
            video_info = {
                'path': video_path,
                'name': v.rsplit('.', 1)[0],
                'cover': None,  # 由 assign_covers_to_videos 分配
                'status': '待上传'
            }
            self.video_list.append(video_info)

        # 分配封面
        self.assign_covers_to_videos()
        self.log(f"从文件夹加载了 {len(videos)} 个视频")

    def refresh_tree(self):
        """刷新 Treeview 显示"""
        self.video_tree.delete(*self.video_tree.get_children())
        for i, video in enumerate(self.video_list):
            cover_status = "✓ 有" if video['cover'] else "✗ 无"
            # 添加序号到视频名称
            name_display = f"{i+1}. {video['name'][:45]}" + ('...' if len(video['name']) > 45 else '')
            self.video_tree.insert("", "end", values=(
                name_display,
                cover_status,
                video['status']
            ))

    def select_all(self):
        for item in self.video_tree.get_children():
            self.video_tree.selection_add(item)

    def deselect_all(self):
        self.video_tree.selection_remove(*self.video_tree.get_children())

    def on_video_select(self, event):
        """当选择视频时，同步选中对应的封面"""
        selected = self.video_tree.selection()
        if not selected:
            return

        idx = self.video_tree.index(selected[0])

        # 同步选中封面列表中对应位置的封面
        cover_items = self.cover_tree.get_children()
        if len(self.cover_list) == 1 and cover_items:
            # 单封面模式：选中唯一封面
            self.cover_tree.selection_set(cover_items[0])
            self.on_cover_select(None)
        elif idx < len(cover_items):
            # 多封面模式：选中对应封面
            self.cover_tree.selection_set(cover_items[idx])
            self.on_cover_select(None)

    def move_up(self):
        """上移选中的视频"""
        selected = self.video_tree.selection()
        if not selected:
            return

        idx = self.video_tree.index(selected[0])
        if idx == 0:
            return

        # 交换位置
        self.video_list[idx], self.video_list[idx-1] = self.video_list[idx-1], self.video_list[idx]
        self.refresh_tree()

        # 重新选中
        items = self.video_tree.get_children()
        if idx-1 < len(items):
            self.video_tree.selection_set(items[idx-1])

    def move_down(self):
        """下移选中的视频"""
        selected = self.video_tree.selection()
        if not selected:
            return

        idx = self.video_tree.index(selected[0])
        if idx >= len(self.video_list) - 1:
            return

        # 交换位置
        self.video_list[idx], self.video_list[idx+1] = self.video_list[idx+1], self.video_list[idx]
        self.refresh_tree()

        # 重新选中
        items = self.video_tree.get_children()
        if idx+1 < len(items):
            self.video_tree.selection_set(items[idx+1])


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

    def start_upload(self):
        selected = self.video_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要上传的视频")
            return

        self.uploading = True
        self.stop_flag = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # 获取选中的视频索引
        selected_indices = [self.video_tree.index(item) for item in selected]

        # 在新线程中运行上传
        thread = threading.Thread(target=self.upload_thread, args=(selected_indices,))
        thread.daemon = True
        thread.start()

    def stop_upload(self):
        self.stop_flag = True
        self.log("正在停止...")

    def upload_thread(self, selected_indices):
        videos = [self.video_list[i] for i in selected_indices]
        total = len(videos)
        video_paths = [v['path'] for v in videos]

        pyautogui.PAUSE = self.delay_var.get()

        self.log(f"开始上传 {total} 个视频")
        self.log("3 秒后开始，将鼠标移到左上角可中止")
        time.sleep(3)

        # 保存初始进度
        self.save_progress(video_paths, 0)

        for i, video in enumerate(videos):
            if self.stop_flag:
                # 保存当前进度（从当前视频继续）
                self.save_progress(video_paths, i)
                self.log("已停止，进度已保存")
                self.root.after(0, lambda: self.resume_btn.configure(state="normal"))
                break

            # 更新状态
            video['status'] = '上传中'
            self.root.after(0, self.refresh_tree)
            self.root.after(0, lambda v=video['name'], idx=i, t=total: self.update_progress(v, idx, t))

            try:
                self.upload_single(video)
                video['status'] = '✓ 完成'
                self.log(f"✓ 完成: {video['name'][:40]}...")
                # 更新进度（标记当前视频已完成，下次从 i+1 开始）
                self.save_progress(video_paths, i + 1)
            except Exception as e:
                video['status'] = '✗ 失败'
                self.log(f"✗ 失败: {e}")
                # 失败时保存进度，下次可以从这个视频重试
                self.save_progress(video_paths, i)

            self.root.after(0, self.refresh_tree)

            if i < total - 1 and not self.stop_flag:
                interval = self.get_interval()
                mode_str = "随机" if self.interval_mode.get() == "random" else "固定"
                self.log(f"等待 {self.format_interval(interval)} ({mode_str})...")
                time.sleep(interval)

        if not self.stop_flag:
            self.root.after(0, self.upload_finished)
        else:
            self.root.after(0, self.upload_stopped)

    def update_progress(self, video_name, current, total):
        self.progress_var.set(f"进度: {current + 1}/{total}")
        self.progress_bar["value"] = (current + 1) / total * 100
        self.current_var.set(f"当前: {video_name[:50]}...")

    def upload_finished(self):
        self.uploading = False
        self.start_btn.configure(state="normal")
        self.resume_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.progress_var.set("完成")
        self.current_var.set("")
        self.step_var.set("")
        self.log("✅ 上传任务结束")
        # 清除进度文件
        self.clear_progress_file()

    def upload_stopped(self):
        """上传被停止时的处理"""
        self.uploading = False
        self.start_btn.configure(state="normal")
        self.resume_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_var.set("已暂停")
        self.step_var.set("")
        self.log("⏸ 上传已暂停，可点击\"继续未完成\"按钮恢复")

    def save_progress(self, video_paths, current_index):
        """保存当前进度"""
        progress = {
            'video_paths': video_paths,
            'current_index': current_index,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'folder': self.folder_var.get(),
            'cover_folder': self.cover_folder_var.get(),
            'playlist_enabled': self.playlist_enabled.get(),
            'playlist_name': self.playlist_var.get(),
            'monetization': self.monetization_var.get()
        }
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存进度失败: {e}")

    def load_progress(self):
        """加载保存的进度"""
        try:
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"加载进度失败: {e}")
        return None

    def check_saved_progress(self):
        """检查是否有未完成的进度"""
        progress = self.load_progress()
        if progress:
            remaining = len(progress['video_paths']) - progress['current_index']
            if remaining > 0:
                self.resume_btn.configure(state="normal")
                self.log(f"发现未完成任务: 还有 {remaining} 个视频待上传 (保存于 {progress['timestamp']})")

    def clear_progress_file(self):
        """清除进度文件"""
        try:
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
        except Exception:
            pass

    def clear_progress(self):
        """手动清除进度"""
        self.clear_progress_file()
        self.resume_btn.configure(state="disabled")
        self.log("已清除保存的进度")

    def resume_upload(self):
        """继续未完成的上传"""
        progress = self.load_progress()
        if not progress:
            messagebox.showwarning("提示", "没有找到未完成的任务")
            return

        remaining_paths = progress['video_paths'][progress['current_index']:]
        if not remaining_paths:
            messagebox.showinfo("提示", "所有任务已完成")
            self.clear_progress_file()
            self.resume_btn.configure(state="disabled")
            return

        # 恢复设置
        if progress.get('playlist_enabled'):
            self.playlist_enabled.set(True)
            self.playlist_var.set(progress.get('playlist_name', ''))
            self.toggle_playlist()
        if progress.get('monetization'):
            self.monetization_var.set(progress['monetization'])

        # 构建待上传视频列表
        resume_videos = []
        for path in remaining_paths:
            if os.path.exists(path):
                name = os.path.basename(path).rsplit('.', 1)[0]
                # 查找对应的封面
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

        self.uploading = True
        self.stop_flag = False
        self.start_btn.configure(state="disabled")
        self.resume_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # 在新线程中运行上传
        thread = threading.Thread(target=self.resume_upload_thread, args=(resume_videos, remaining_paths))
        thread.daemon = True
        thread.start()

    def resume_upload_thread(self, videos, all_paths):
        """继续上传的线程"""
        total = len(videos)
        pyautogui.PAUSE = self.delay_var.get()

        self.log("3 秒后开始，将鼠标移到左上角可中止")
        time.sleep(3)

        for i, video in enumerate(videos):
            if self.stop_flag:
                # 保存当前进度
                self.save_progress(all_paths, i)
                self.log("已停止，进度已保存")
                break

            # 更新状态
            video['status'] = '上传中'
            self.root.after(0, lambda v=video['name'], idx=i, t=total: self.update_progress(v, idx, t))

            try:
                self.upload_single(video)
                video['status'] = '✓ 完成'
                self.log(f"✓ 完成: {video['name'][:40]}...")
                # 更新进度（标记当前视频已完成）
                self.save_progress(all_paths, i + 1)
            except Exception as e:
                video['status'] = '✗ 失败'
                self.log(f"✗ 失败: {e}")
                # 失败时也保存进度，下次可以从这个视频重试
                self.save_progress(all_paths, i)

            if i < total - 1 and not self.stop_flag:
                interval = self.get_interval()
                mode_str = "随机" if self.interval_mode.get() == "random" else "固定"
                self.log(f"等待 {self.format_interval(interval)} ({mode_str})...")
                time.sleep(interval)

        self.root.after(0, self.upload_finished)

    def upload_single(self, video):
        """上传单个视频"""
        video_path = video['path']
        title = video['name']
        cover_path = video.get('cover')

        # 获取播放列表和盈利设置
        playlist_name = self.playlist_var.get() if self.playlist_enabled.get() else None
        monetization = self.monetization_var.get()  # "none", "on", "off"

        # 激活 Chrome
        self.update_step("激活浏览器...")
        os.system('open -a "Google Chrome"')
        time.sleep(1)

        # 打开 YouTube Studio
        self.update_step("打开 YouTube Studio...")
        self.log("打开 YouTube Studio...")
        pyautogui.hotkey('command', 'l')
        time.sleep(0.5)
        pyautogui.hotkey('command', 'a')
        pyperclip.copy('https://studio.youtube.com')
        pyautogui.hotkey('command', 'v')
        time.sleep(0.3)
        pyautogui.press('return')
        time.sleep(5)

        # 点击创建
        self.update_step("点击创建按钮...")
        self.log("点击创建...")
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width - 150, 80)
        time.sleep(2)

        # 上传视频
        self.update_step("选择上传视频...")
        self.log("选择上传视频...")
        pyautogui.press('down')
        time.sleep(0.3)
        pyautogui.press('return')
        time.sleep(3)

        # 选择文件
        self.update_step("选择视频文件...")
        self.log("选择视频文件...")
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

        # 上传封面（如果有）
        if cover_path and os.path.exists(cover_path):
            self.update_step("上传封面...")
            self.log("上传封面...")
            try:
                # 点击上传缩略图按钮
                # 通常在视频详情页面的右侧
                pyautogui.press('tab')
                time.sleep(0.3)
                pyautogui.press('tab')
                time.sleep(0.3)
                pyautogui.press('return')  # 点击上传缩略图
                time.sleep(2)

                # 选择封面文件
                pyautogui.hotkey('shift', 'command', 'g')
                time.sleep(1)
                pyperclip.copy(cover_path)
                pyautogui.hotkey('command', 'v')
                time.sleep(0.5)
                pyautogui.press('return')
                time.sleep(1)
                pyautogui.press('return')
                time.sleep(3)
                self.log("✓ 封面已上传")
            except Exception as e:
                self.log(f"封面上传失败: {e}")

        # 设置受众
        self.update_step("设置受众...")
        self.log("设置受众...")
        for _ in range(10):
            pyautogui.press('tab')
            time.sleep(0.1)
        pyautogui.press('space')
        time.sleep(1)

        # 盈利设置 (如果需要)
        if monetization != "none":
            self.update_step("设置盈利模式...")
            self.log(f"设置盈利: {'开启' if monetization == 'on' else '关闭'}")
            try:
                # 展开更多选项 - 点击"显示更多选项"
                pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.press('space')  # 展开更多选项
                time.sleep(1)

                # 找到盈利选项并设置
                for _ in range(5):
                    pyautogui.press('tab')
                    time.sleep(0.1)

                if monetization == "on":
                    pyautogui.press('space')  # 开启盈利
                else:
                    # 如果是关闭盈利，可能需要取消选中
                    pass
                time.sleep(1)
            except Exception as e:
                self.log(f"盈利设置失败: {e}")

        # 下一步 x3
        for i in range(3):
            self.update_step(f"下一步 {i+1}/3...")
            self.log(f"下一步 {i+1}/3...")
            pyautogui.press('tab')
            pyautogui.press('return')
            time.sleep(2)
        time.sleep(2)

        # 播放列表设置 (如果需要)
        if playlist_name:
            self.update_step("添加到播放列表...")
            self.log(f"添加到播放列表: {playlist_name}")
            try:
                # 在发布页面，找到播放列表选项
                # 通常需要点击"添加到播放列表"下拉菜单
                for _ in range(3):
                    pyautogui.press('tab')
                    time.sleep(0.1)
                pyautogui.press('return')  # 打开播放列表选择
                time.sleep(1)

                # 搜索或选择播放列表
                pyperclip.copy(playlist_name)
                pyautogui.hotkey('command', 'v')
                time.sleep(1)
                pyautogui.press('return')  # 选择
                time.sleep(1)
                pyautogui.press('escape')  # 关闭下拉菜单
                time.sleep(0.5)
            except Exception as e:
                self.log(f"播放列表设置失败: {e}")

        # 保存
        self.update_step("保存视频...")
        self.log("保存...")
        for _ in range(5):
            pyautogui.press('tab')
            time.sleep(0.1)
        pyautogui.press('return')
        time.sleep(3)

        self.update_step("完成")


def main():
    root = tk.Tk()
    app = YouTubeUploaderGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
