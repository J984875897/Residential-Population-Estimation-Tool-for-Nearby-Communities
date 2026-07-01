"""诊断脚本：测试这台 Mac 上 tkinter 各控件渲染情况"""
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.geometry("460x420")
root.title("Tkinter 渲染诊断")
root.configure(bg="#eef2f7")

tk.Label(root, text="===== 渲染诊断 =====",
         font=("Helvetica", 13, "bold"), fg="#2B579A").pack(pady=(12, 4))

# 1. Canvas（已知最可靠）
c = tk.Canvas(root, height=36, bg="#2B579A", highlightthickness=0)
c.pack(fill=tk.X, padx=20)
c.create_text(230, 18, text="1. Canvas 蓝底白字（应可见）", fill="white",
              font=("Helvetica", 11, "bold"))

# 2. Frame with bg
f = tk.Frame(root, bg="#eef2f7")
f.pack(fill=tk.X, padx=20, pady=6)

# 3. tk.Label no bg
tk.Label(f, text="2. tk.Label 无bg，fg=深蓝（应可见深蓝字）",
         fg="#1a2a4a", font=("Helvetica", 11), bg="#eef2f7").pack(anchor="w")

# 4. tk.Label with bg matching parent
tk.Label(f, text="3. tk.Label bg=父背景色（应可见）",
         fg="#c0392b", bg="#eef2f7", font=("Helvetica", 11)).pack(anchor="w", pady=2)

# 5. tk.Label with different bg
tk.Label(f, text="4. tk.Label bg=黄色（应有黄色背景）",
         fg="black", bg="yellow", font=("Helvetica", 11)).pack(anchor="w", pady=2)

# 6. ttk.Label plain
ttk.Label(f, text="5. ttk.Label 无样式（应可见系统默认样式）").pack(anchor="w", pady=2)

# 7. ttk.Label with style
style = ttk.Style()
style.configure("Test.TLabel", foreground="blue", font=("Helvetica", 11))
ttk.Label(f, text="6. ttk.Label 带style foreground=blue（应为蓝字）",
          style="Test.TLabel").pack(anchor="w", pady=2)

# 8. tk.Entry
ent_frame = tk.Frame(root, bg="#eef2f7")
ent_frame.pack(fill=tk.X, padx=20, pady=4)
tk.Label(ent_frame, text="7. tk.Entry white bg:", fg="#1a2a4a",
         bg="#eef2f7", font=("Helvetica", 11)).pack(side=tk.LEFT)
tk.Entry(ent_frame, bg="white", fg="black", font=("Helvetica", 11),
         highlightthickness=1, highlightbackground="#aaaaaa").pack(side=tk.LEFT, padx=8)

# 9. tk.Button
tk.Button(root, text="8. tk.Button（应为蓝底白字）",
          bg="#2B579A", fg="white", font=("Helvetica", 11),
          relief=tk.FLAT, padx=10, pady=5).pack(pady=8)

tk.Label(root, text="（把截图发给我，我就能知道哪些控件能用）",
         fg="#888888", font=("Helvetica", 9), bg="#eef2f7").pack()

root.mainloop()
