"""
GUI 界面，使用内置 tkinter，无需额外安装。
运行方式：python main.py（默认启动 GUI）
          python main.py --cli（命令行模式，保留原有交互）
"""

import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import queue

import config
import runtime_state


class ScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LJJ住户爬虫小程序")
        self.root.resizable(False, False)

        self._log_queue = queue.Queue()
        self._choice_event = threading.Event()
        self._choice_result = None
        self._scraper_main_fn = None

        saved_state = runtime_state.load_state()
        if saved_state:
            runtime_state.apply_state_to_config(config, saved_state)

        # ── config 绑定变量 ──
        self._var_city_code = tk.StringVar(value=config.CITY_CODE)
        self._var_city_name = tk.StringVar(value=config.CITY_NAME)
        self._var_name = tk.StringVar(value=config.TARGET_NAME)
        self._var_lng = tk.StringVar(value=str(config.TARGET_LNG))
        self._var_lat = tk.StringVar(value=str(config.TARGET_LAT))
        self._var_radius = tk.StringVar(value=str(config.RADIUS_KM))
        self._var_districts = tk.StringVar(value=", ".join(config.SEARCH_DISTRICTS))
        self._var_limit = tk.StringVar(value=str(saved_state.get("max_communities") or ""))
        self._var_data_dir = tk.StringVar(
            value=runtime_state.get_saved_data_dir(runtime_state.DEFAULT_DATA_DIR)
        )
        self._max_communities = None
        self._data_dir = self._var_data_dir.get()

        self._build_config_window()

    # ══════════════════════════════════════════
    #  阶段一：配置窗口
    # ══════════════════════════════════════════

    def _build_config_window(self):
        self.root.geometry("620x660")

        # ── 标题栏：create_rectangle 绘制蓝色背景（绕过 Aqua 主题颜色限制）──
        tc = tk.Canvas(self.root, height=50, highlightthickness=0, bd=0)
        tc.pack(fill=tk.X)
        tc.create_rectangle(0, 0, 2000, 100, fill="#2B579A", outline="")
        tc.create_text(280, 25, text="LJJ住户爬虫小程序",
                       fill="white", font=("Helvetica", 15, "bold"))

        # ── 表单画布（标签用 create_text 绘制，输入框用 create_window 嵌入）──
        # Tk 9.0 / macOS Aqua 不响应 Label/Frame 的颜色设置，
        # 但 Canvas 的绘图指令（create_text/create_rectangle）始终可靠。
        fc = tk.Canvas(self.root, highlightthickness=0, bd=0)
        fc.pack(fill=tk.BOTH, expand=True)

        LX = 22   # 标签起始 x
        EX = 190  # 输入框起始 x（anchor="w"）
        EW = 25   # 输入框字符宽度

        # (y坐标, 标签文字, 变量, 提示文字)
        fields = [
            (22,  "城市代码 (City Code)",  self._var_city_code,
                  "如 lz（兰州）、bj（北京）、sh（上海）"),
            (74,  "城市名称（中文）",       self._var_city_name,  ""),
            (112, "目标地点名称",           self._var_name,       ""),
            (150, "经度 (Longitude)",       self._var_lng,        ""),
            (188, "纬度 (Latitude)",        self._var_lat,        ""),
            (226, "搜索半径 (km)",          self._var_radius,     ""),
            (264, "行政区（逗号分隔）",     self._var_districts,  ""),
        ]

        for y, label, var, hint in fields:
            fc.create_text(LX, y + 9, text=label, fill="#1a2a4a",
                           font=("Helvetica", 11), anchor="w")
            e = tk.Entry(fc, textvariable=var, width=EW,
                         font=("Helvetica", 10))
            fc.create_window(EX, y + 9, window=e, anchor="w", height=26)
            if hint:
                fc.create_text(EX, y + 27, text=hint,
                               fill="#888888", font=("Helvetica", 9), anchor="w")

        # 行政区行旁边的「自动获取」按钮
        self._fetch_btn = tk.Button(
            fc, text="自动获取行政区",
            command=self._on_fetch_districts,
            bg="#5a7db5", fg="#1a2a4a",
            font=("Helvetica", 9),
            relief=tk.FLAT, padx=6, pady=2,
        )
        fc.create_window(EX + 232, 273, window=self._fetch_btn, anchor="w")

        # 分隔线
        fc.create_line(LX, 302, 538, 302, fill="#cccccc", width=1)

        # 爬取数量上限
        fc.create_text(LX, 326, text="爬取数量上限（条）",
                       fill="#1a2a4a", font=("Helvetica", 11), anchor="w")
        le = tk.Entry(fc, textvariable=self._var_limit, width=EW,
                      font=("Helvetica", 10))
        fc.create_window(EX, 326, window=le, anchor="w", height=26)
        fc.create_text(EX, 346, text="留空则爬取全部；仅从头爬取（Step 1/2）时生效",
                       fill="#888888", font=("Helvetica", 9), anchor="w")

        # 数据保存文件夹
        fc.create_text(LX, 382, text="数据保存文件夹",
                       fill="#1a2a4a", font=("Helvetica", 11), anchor="w")
        de = tk.Entry(fc, textvariable=self._var_data_dir, width=EW,
                      font=("Helvetica", 10))
        fc.create_window(EX, 382, window=de, anchor="w", height=26)
        pick_btn = tk.Button(
            fc, text="选择...",
            command=self._on_select_data_dir,
            bg="#5a7db5", fg="#1a2a4a",
            font=("Helvetica", 9),
            relief=tk.FLAT, padx=6, pady=2,
        )
        fc.create_window(EX + 232, 382, window=pick_btn, anchor="w")
        fc.create_text(EX, 402, text="断点和中间数据会保存在这里；重启后默认使用上次选择",
                       fill="#888888", font=("Helvetica", 9), anchor="w")

        # 底部提示
        fc.create_text(310, 438,
                       text="开始运行后会保存本次输入；小区坐标来自贝壳，目标坐标请尽量使用同一坐标体系",
                       fill="#888888", font=("Helvetica", 9))

        # 开始按钮（嵌入 Canvas，形状和文字始终可见）
        start_btn = tk.Button(
            fc, text="  开始运行  ",
            command=self._on_start,
            bg="#2B579A", fg="#1a2a4a",
            font=("Helvetica", 12, "bold"),
            relief=tk.FLAT, padx=14, pady=7,
        )
        fc.create_window(310, 480, window=start_btn)

    def _on_start(self):
        # 验证并写入 config（仅内存）
        city_code = re.sub(r'\.ke\.com$', '', self._var_city_code.get().strip().lower())
        if not city_code:
            messagebox.showerror("输入错误", "城市代码不能为空（如 lz、bj、sh）")
            return
        config.CITY_CODE = city_code
        config.CITY_NAME = self._var_city_name.get().strip() or city_code
        config.BASE_URL = f"https://{city_code}.ke.com"
        config.TARGET_NAME = self._var_name.get().strip()
        try:
            config.TARGET_LNG = float(self._var_lng.get())
            config.TARGET_LAT = float(self._var_lat.get())
            config.RADIUS_KM = float(self._var_radius.get())
        except ValueError:
            messagebox.showerror("输入错误", "经度、纬度、搜索半径必须为数字")
            return
        raw_districts = self._var_districts.get()
        config.SEARCH_DISTRICTS = [d.strip() for d in raw_districts.split(",") if d.strip()]
        if not config.SEARCH_DISTRICTS:
            messagebox.showerror("输入错误", "至少需要输入一个行政区")
            return

        self._data_dir = self._var_data_dir.get().strip()
        if not self._data_dir:
            messagebox.showerror("输入错误", "数据保存文件夹不能为空")
            return

        limit_raw = self._var_limit.get().strip()
        if limit_raw:
            try:
                self._max_communities = int(limit_raw)
                if self._max_communities <= 0:
                    messagebox.showerror("输入错误", "爬取数量上限必须为正整数")
                    return
            except ValueError:
                messagebox.showerror("输入错误", "爬取数量上限必须为整数（如 50）")
                return
        else:
            self._max_communities = None

        runtime_state.save_state(
            runtime_state.state_from_config(config, self._data_dir, self._max_communities)
        )

        # 切换到主运行窗口
        for w in self.root.winfo_children():
            w.destroy()
        self._build_main_window()

        # 启动后台线程
        t = threading.Thread(target=self._run_scraper, daemon=True)
        t.start()

        # 启动队列轮询
        self.root.after(100, self._poll_queue)

    def _on_fetch_districts(self):
        city_code = re.sub(r'\.ke\.com$', '', self._var_city_code.get().strip().lower())
        if not city_code:
            messagebox.showerror("错误", "请先填写城市代码（如 lz、bj、sh）")
            return
        config.CITY_CODE = city_code
        config.BASE_URL = f"https://{city_code}.ke.com"
        self._fetch_btn.config(state=tk.DISABLED, text="获取中…")
        threading.Thread(target=self._fetch_districts_thread, daemon=True).start()

    def _on_select_data_dir(self):
        selected = filedialog.askdirectory(
            title="选择数据保存文件夹",
            initialdir=self._var_data_dir.get() or runtime_state.DEFAULT_DATA_DIR,
        )
        if selected:
            self._var_data_dir.set(selected)

    def _fetch_districts_thread(self):
        from scraper import get_district_links
        districts = get_district_links()
        if districts:
            slugs = ", ".join(d["slug"] for d in districts)
            names = "\n".join(f'  {d["name"]} = {d["slug"]}' for d in districts)
            self._var_districts.set(slugs)
            self.root.after(0, lambda: self._fetch_btn.config(state=tk.NORMAL, text="自动获取行政区"))
            self.root.after(0, lambda: messagebox.showinfo(
                "行政区已填入",
                f"找到 {len(districts)} 个行政区：\n{names}\n\n已自动填入，请按需删减。",
            ))
        else:
            self.root.after(0, lambda: self._fetch_btn.config(state=tk.NORMAL, text="自动获取行政区"))
            self.root.after(0, lambda: messagebox.showwarning(
                "未找到行政区", "未能从首页提取行政区链接，请手动填写。"
            ))

    # ══════════════════════════════════════════
    #  阶段二：主运行窗口
    # ══════════════════════════════════════════

    def _build_main_window(self):
        self.root.geometry("720x520")
        self.root.resizable(True, True)

        # 顶部标题
        top = tk.Frame(self.root, bg="#2B579A")
        top.pack(fill=tk.X)
        tk.Label(
            top,
            text=f"正在运行 — {config.TARGET_NAME}",
            bg="#2B579A", fg="white",
            font=("Microsoft YaHei", 11, "bold"),
            pady=8, padx=10,
        ).pack(side=tk.LEFT)

        # 日志区域
        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._log_text = scrolledtext.ScrolledText(
            log_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white",
        )
        self._log_text.pack(fill=tk.BOTH, expand=True)

        # 底部按钮区（动态填充）
        self._btn_frame = tk.Frame(self.root, pady=6)
        self._btn_frame.pack(fill=tk.X, padx=10)

        # 状态栏
        self._status_label = tk.Label(
            self.root, text="运行中…",
            bg="#1e1e1e", fg="#aaaaaa",
            font=("Microsoft YaHei", 9),
            pady=3,
        )
        self._status_label.pack(fill=tk.X)

    def _append_log(self, msg: str):
        self._log_text.config(state=tk.NORMAL)
        self._log_text.insert(tk.END, msg + "\n")
        self._log_text.see(tk.END)
        self._log_text.config(state=tk.DISABLED)

    # ══════════════════════════════════════════
    #  队列轮询（主线程）
    # ══════════════════════════════════════════

    def _poll_queue(self):
        try:
            while True:
                item = self._log_queue.get_nowait()
                kind = item[0]
                if kind == "log":
                    self._append_log(item[1])
                elif kind == "ask_continue":
                    # 显示确认弹窗（弹窗关闭后自动恢复轮询）
                    self._show_continue_dialog(item[1], item[2])
                    return
                elif kind == "ask_checkpoint":
                    self._show_checkpoint_dialog(item[1])
                    return
                elif kind == "ask_verify":
                    self._show_verify_dialog()
                    return
                elif kind == "done":
                    self._on_scraper_done()
                    return
                elif kind == "stopped":
                    self._on_scraper_stopped()
                    return
                elif kind == "error":
                    self._append_log(item[1])
                    self._on_scraper_error()
                    return
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    # ══════════════════════════════════════════
    #  弹窗：浏览器验证
    # ══════════════════════════════════════════

    def _show_verify_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("需要浏览器验证")
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.geometry("420x240")
        self._center_dialog(dialog)

        tk.Label(
            dialog,
            text="⚠️  浏览器需要验证",
            font=("Microsoft YaHei", 12, "bold"),
            fg="#c0392b",
            pady=12,
        ).pack()

        steps_frame = tk.Frame(dialog, padx=24)
        steps_frame.pack(fill=tk.X)
        for step in [
            "1. 在弹出的 Chrome 窗口中完成验证码",
            "2. 确认已登录贝壳账号",
            "3. 手动导航到小区列表页，确认页面正常",
        ]:
            tk.Label(
                steps_frame, text=step,
                font=("Microsoft YaHei", 10), anchor="w", fg="#1a2a4a",
            ).pack(fill=tk.X, pady=2)

        def on_done():
            dialog.destroy()

        tk.Button(
            dialog,
            text="  已完成验证，继续运行  ",
            command=on_done,
            bg="#27ae60", fg="#1a2a4a",
            font=("Microsoft YaHei", 10, "bold"),
            relief=tk.FLAT, padx=12, pady=6,
            cursor="hand2",
        ).pack(pady=16)

        dialog.wait_window()
        self._choice_event.set()
        self.root.after(100, self._poll_queue)

    # ══════════════════════════════════════════
    #  弹窗：步骤确认
    # ══════════════════════════════════════════

    def _show_continue_dialog(self, next_step_desc: str, preview_lines):
        dialog = tk.Toplevel(self.root)
        dialog.title("确认继续")
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.geometry("440x260")
        self._center_dialog(dialog)

        tk.Label(
            dialog,
            text=f"→ 继续 {next_step_desc}？",
            fg="#1a2a4a",
            font=("Microsoft YaHei", 11, "bold"),
            pady=12,
        ).pack()

        if preview_lines:
            preview_frame = tk.Frame(dialog, bd=1, relief=tk.SOLID, bg="#e8eef5")
            preview_frame.pack(padx=20, fill=tk.X)
            tk.Label(
                preview_frame, text="预览（前3条）：",
                fg="#4a6080", bg="#e8eef5",
                font=("Microsoft YaHei", 9), anchor="w",
            ).pack(fill=tk.X, padx=6, pady=(4, 0))
            for line in preview_lines[:3]:
                tk.Label(
                    preview_frame, text=line,
                    bg="#e8eef5",
                    font=("Consolas", 9), anchor="w", fg="#1a2a4a",
                ).pack(fill=tk.X, padx=14, pady=1)

        result = [None]

        def choose(r):
            result[0] = r
            dialog.destroy()

        btn_row = tk.Frame(dialog, pady=15)
        btn_row.pack()

        tk.Button(
            btn_row, text="继续", command=lambda: choose("y"),
            bg="#2B579A", fg="#1a2a4a",
            font=("Microsoft YaHei", 10), relief=tk.FLAT,
            padx=16, pady=5, cursor="hand2",
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_row, text="保存并退出", command=lambda: choose("n"),
            bg="#888888", fg="#1a2a4a",
            font=("Microsoft YaHei", 10), relief=tk.FLAT,
            padx=10, pady=5, cursor="hand2",
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_row, text="退出", command=lambda: choose("q"),
            bg="#c0392b", fg="#1a2a4a",
            font=("Microsoft YaHei", 10), relief=tk.FLAT,
            padx=16, pady=5, cursor="hand2",
        ).pack(side=tk.LEFT, padx=8)

        dialog.wait_window()

        self._choice_result = result[0] or "q"
        self._choice_event.set()
        self.root.after(100, self._poll_queue)

    # ══════════════════════════════════════════
    #  弹窗：断点选择
    # ══════════════════════════════════════════

    def _show_checkpoint_dialog(self, existing_files):
        dialog = tk.Toplevel(self.root)
        dialog.title("发现未完成的进度")
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.geometry("500x360")
        self._center_dialog(dialog)

        tk.Label(
            dialog,
            text="发现上次未完成的进度",
            fg="#1a2a4a",
            font=("Microsoft YaHei", 12, "bold"),
            pady=10,
        ).pack()
        tk.Label(
            dialog,
            text=f"断点文件：{', '.join(existing_files)}",
            fg="#4a6080",
            font=("Microsoft YaHei", 9),
        ).pack()

        result = [None]

        def choose(r):
            result[0] = r
            dialog.destroy()

        opts_frame = tk.Frame(dialog, padx=20, pady=8)
        opts_frame.pack(fill=tk.BOTH, expand=True)

        options = [
            ("c", "继续上次进度", "自动跳过已完成步骤", "#2B579A"),
            ("1", "Step 1 重新开始", "清除全部断点，重新爬取小区列表（耗时最长）", "#c0392b"),
            ("2", "Step 2 重新开始", "保留 URL 列表，重新抓取小区详情（需联网）", "#e67e22"),
            ("3", "Step 3 重新计算", f"保留爬取数据，按当前 {config.RADIUS_KM}km 重新生成 Excel（秒级）", "#27ae60"),
            ("r", "完全重置", "等同于 Step 1，清除全部断点", "#c0392b"),
            ("q", "退出", "", "#888888"),
        ]

        for key, label, desc, color in options:
            row = tk.Frame(opts_frame)
            row.pack(fill=tk.X, pady=3)
            tk.Button(
                row, text=label,
                command=lambda k=key: choose(k),
                bg=color, fg="#1a2a4a",
                font=("Microsoft YaHei", 9),
                relief=tk.FLAT, padx=8, pady=4,
                width=16, cursor="hand2",
            ).pack(side=tk.LEFT)
            if desc:
                tk.Label(
                    row, text=desc, fg="#1a2a4a",
                    font=("Microsoft YaHei", 9), anchor="w",
                ).pack(side=tk.LEFT, padx=10)

        dialog.wait_window()

        self._choice_result = result[0] or "q"
        self._choice_event.set()
        self.root.after(100, self._poll_queue)

    # ══════════════════════════════════════════
    #  完成 / 停止 处理
    # ══════════════════════════════════════════

    def _on_scraper_done(self):
        self._status_label.config(text="运行完成 ✓", fg="#27ae60")
        tk.Button(
            self._btn_frame, text="关闭窗口",
            command=self.root.destroy,
            bg="#888888", fg="#1a2a4a",
            font=("Microsoft YaHei", 10), relief=tk.FLAT,
            padx=14, pady=4, cursor="hand2",
        ).pack(side=tk.RIGHT)

    def _on_scraper_stopped(self):
        self._status_label.config(text="已停止", fg="#888888")
        tk.Button(
            self._btn_frame, text="关闭窗口",
            command=self.root.destroy,
            bg="#888888", fg="#1a2a4a",
            font=("Microsoft YaHei", 10), relief=tk.FLAT,
            padx=14, pady=4, cursor="hand2",
        ).pack(side=tk.RIGHT)

    def _on_scraper_error(self):
        self._status_label.config(text="运行出错", fg="#c0392b")
        tk.Button(
            self._btn_frame, text="关闭窗口",
            command=self.root.destroy,
            bg="#888888", fg="#1a2a4a",
            font=("Microsoft YaHei", 10), relief=tk.FLAT,
            padx=14, pady=4, cursor="hand2",
        ).pack(side=tk.RIGHT)

    # ══════════════════════════════════════════
    #  后台线程
    # ══════════════════════════════════════════

    def _run_scraper(self):
        try:
            self._scraper_main_fn(
                log_fn=self.log,
                ask_continue_fn=self.ask_continue,
                ask_checkpoint_fn=self.ask_checkpoint,
                verify_fn=self.ask_verify,
                max_communities=self._max_communities,
                data_dir=self._data_dir,
            )
            self._log_queue.put(("done",))
        except SystemExit:
            self._log_queue.put(("stopped",))
        except Exception as e:
            self._log_queue.put(("error", f"\n❌ 运行出错: {e}"))

    # ══════════════════════════════════════════
    #  公共 API（由工作线程调用）
    # ══════════════════════════════════════════

    def log(self, msg: str):
        """线程安全：将日志消息放入队列，由主线程写入控件。"""
        self._log_queue.put(("log", msg))

    def ask_continue(self, next_step_desc: str, preview_lines=None) -> str:
        """线程安全：阻塞工作线程直到用户在弹窗中做出选择，返回 'y'/'n'/'q'。"""
        self._choice_event.clear()
        self._log_queue.put(("ask_continue", next_step_desc, preview_lines))
        self._choice_event.wait()
        return self._choice_result

    def ask_checkpoint(self, existing_files: list) -> str:
        """线程安全：阻塞工作线程直到用户选择断点选项，返回 'c'/'1'/'2'/'3'/'r'/'q'。"""
        self._choice_event.clear()
        self._log_queue.put(("ask_checkpoint", existing_files))
        self._choice_event.wait()
        return self._choice_result

    def ask_verify(self):
        """线程安全：显示验证弹窗，阻塞工作线程直到用户确认完成验证。"""
        self._choice_event.clear()
        self._log_queue.put(("ask_verify",))
        self._choice_event.wait()

    # ══════════════════════════════════════════
    #  工具
    # ══════════════════════════════════════════

    def _center_dialog(self, dialog: tk.Toplevel):
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width() // 2
        ry = self.root.winfo_y() + self.root.winfo_height() // 2
        w = int(dialog.geometry().split("x")[0])
        h = int(dialog.geometry().split("x")[1].split("+")[0])
        dialog.geometry(f"+{rx - w // 2}+{ry - h // 2}")

    def run(self, scraper_main_fn):
        """启动 GUI 主循环，scraper_main_fn 为爬虫入口函数。"""
        self._scraper_main_fn = scraper_main_fn
        self.root.mainloop()
